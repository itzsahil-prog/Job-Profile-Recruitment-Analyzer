#!/usr/bin/env python3
"""
validate_dataset.py — Dataset validation and quality reporting for the
Big Data Job Profile Recruitment Analyzer.

Reads a job postings CSV file using pandas chunked streaming (chunksize=50000),
performs quality checks, and writes a JSON report. Handles UTF-8 and latin-1
encodings, quoted commas, duplicate job_ids, and missing values.

Usage:
    python analytics/validate_dataset.py --input data/job_descriptions.csv
    python analytics/validate_dataset.py --input data/job_descriptions.csv \\
        --output outputs/data_quality_report.json

Output JSON keys:
    source_path, encoding_detected, total_rows_raw, columns, schema_mapping,
    missing_values, duplicate_rows, rows_after_dedup, rejected_rows,
    rows_retained, validation_timestamp
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

CHUNKSIZE = 50_000

# ---------------------------------------------------------------------------
# Explicit schema mapping: actual CSV column -> logical field name
# ---------------------------------------------------------------------------
SCHEMA_MAPPING = {
    # Real dataset column names
    'Job Id':           'job_id',
    'Job Title':        'job_title',
    'Job Description':  'description',
    'skills':           'skills_required',
    'Experience':       'experience_required',
    'Company':          'company',
    'Salary Range':     'salary_range',
    'Job Posting Date': 'post_date',
    # Logical names (used by test fixtures and local sim outputs)
    'job_id':           'job_id',
    'job_title':        'job_title',
    'description':      'description',
    'skills_required':  'skills_required',
    'experience_required': 'experience_required',
    'company':          'company',
    'salary_range':     'salary_range',
    'post_date':        'post_date',
}

# Required columns — a row is rejected if ANY of these is null/empty
REQUIRED_COLS = ['Job Id', 'Job Title', 'Job Description']


def detect_encoding(filepath):
    """Try UTF-8, fall back to latin-1."""
    for enc in ('utf-8', 'latin-1'):
        try:
            with open(filepath, encoding=enc) as f:
                for _ in zip(range(200), f):
                    pass
            return enc
        except UnicodeDecodeError:
            continue
    return 'utf-8'


def _is_empty(series):
    """Return boolean Series: True where value is NaN or empty/whitespace string."""
    return series.isna() | (series.fillna('').str.strip() == '')


def load_csv(filepath, encoding):
    """
    Stream through the CSV in pandas chunks of CHUNKSIZE.

    Single-pass algorithm:
      1. Accumulate missing-value counts per column (on raw rows).
      2. Deduplicate by 'Job Id' across chunks (seen_ids set).
      3. On the deduped subset, count rows where REQUIRED_COLS are empty (rejected).

    Returns
    -------
    tuple:
        columns          list[str]
        total_rows_raw   int
        missing          dict[str, int]
        duplicate_rows   int
        rows_after_dedup int
        rejected_rows    int
        rows_retained    int
    """
    columns = None
    total_rows_raw = 0
    missing = {}
    seen_ids = set()
    duplicate_rows = 0
    rows_after_dedup = 0
    rejected_rows = 0

    chunk_iter = pd.read_csv(
        filepath,
        encoding=encoding,
        encoding_errors='replace',
        chunksize=CHUNKSIZE,
        low_memory=False,
        dtype=str,          # keep everything as strings; avoids mixed-type issues
    )

    for chunk in chunk_iter:
        if columns is None:
            columns = list(chunk.columns)
            missing = {col: 0 for col in columns}

        total_rows_raw += len(chunk)

        # --- 1. Missing value counts (on raw rows) ---
        for col in columns:
            if col in chunk.columns:
                missing[col] += int(_is_empty(chunk[col]).sum())

        # Progress every ~500k rows
        if (total_rows_raw // 500_000) > ((total_rows_raw - len(chunk)) // 500_000):
            print(f"  Progress: {total_rows_raw:,} rows read...", flush=True)

        # --- 2. Deduplication by job_id column (handles both 'Job Id' and 'job_id') ---
        id_col_name = None
        for candidate in ('Job Id', 'job_id'):
            if candidate in chunk.columns:
                id_col_name = candidate
                break
        if id_col_name is not None:
            id_col = chunk[id_col_name].fillna('').str.strip()
            has_id = id_col != ''

            # A row is a duplicate if its non-empty id was already seen
            is_dup = has_id & id_col.isin(seen_ids)

            # For rows that are NOT duplicates and have a valid id,
            # we still need to handle within-chunk duplicates:
            # process row by row to respect first-occurrence rule.
            is_dup_list = is_dup.tolist()
            id_list = id_col.tolist()
            for i, (jid, already_dup) in enumerate(zip(id_list, is_dup_list)):
                if already_dup:
                    continue  # already marked
                if jid == '':
                    continue  # no id, can't dedup
                if jid in seen_ids:
                    # became a dup due to a row earlier in this same chunk
                    is_dup_list[i] = True
                else:
                    seen_ids.add(jid)

            is_dup = pd.Series(is_dup_list, index=chunk.index)

            dup_count = int(is_dup.sum())
            duplicate_rows += dup_count

            deduped_chunk = chunk[~is_dup].copy()
        else:
            deduped_chunk = chunk.copy()

        rows_after_dedup += len(deduped_chunk)

        # --- 3. Rejection check on deduped rows ---
        # Support both raw column names ('Job Id', 'Job Title', 'Job Description')
        # and logical names ('job_id', 'job_title', 'description') written by test fixtures
        REQUIRED_CANDIDATES = [
            ('Job Id',          'job_id'),
            ('Job Title',       'job_title'),
            ('Job Description', 'description'),
        ]
        reject_mask = pd.Series([False] * len(deduped_chunk), index=deduped_chunk.index)
        for raw_name, logical_name in REQUIRED_CANDIDATES:
            for col in (raw_name, logical_name):
                if col in deduped_chunk.columns:
                    reject_mask = reject_mask | _is_empty(deduped_chunk[col])
                    break

        rejected_rows += int(reject_mask.sum())

    rows_retained = rows_after_dedup - rejected_rows
    return (
        columns or [],
        total_rows_raw,
        missing,
        duplicate_rows,
        rows_after_dedup,
        rejected_rows,
        rows_retained,
    )


def validate(input_path, output_path):
    """Run full validation pipeline and write a JSON quality report."""
    if not os.path.isfile(input_path):
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Validating: {input_path}")
    print(f"Streaming in chunks of {CHUNKSIZE:,} rows...")

    # Step 1: detect encoding
    encoding = detect_encoding(input_path)
    print(f"Encoding detected: {encoding}")

    # Step 2: stream CSV
    (columns, total_rows_raw, missing_values,
     duplicate_rows, rows_after_dedup,
     rejected_rows, rows_retained) = load_csv(input_path, encoding)

    # Step 3: schema mapping (only columns present in the file)
    schema_mapping = {col: SCHEMA_MAPPING[col] for col in columns if col in SCHEMA_MAPPING}

    # Step 4: build report
    report = {
        'source_path':          os.path.abspath(input_path),
        'encoding_detected':    encoding,
        'total_rows_raw':       total_rows_raw,
        'columns':              columns,
        'schema_mapping':       schema_mapping,
        'missing_values':       missing_values,
        'duplicate_rows':       duplicate_rows,
        'rows_after_dedup':     rows_after_dedup,
        'rejected_rows':        rejected_rows,
        'rows_retained':        rows_retained,
        'validation_timestamp': datetime.now(timezone.utc).isoformat(),
    }

    # Step 5: write output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\nValidation complete.")
    print(f"  Total rows (raw):   {total_rows_raw:,}")
    print(f"  Duplicates removed: {duplicate_rows:,}")
    print(f"  Rows after dedup:   {rows_after_dedup:,}")
    print(f"  Rejected rows:      {rejected_rows:,}")
    print(f"  Rows retained:      {rows_retained:,}")
    print(f"  Report written to:  {output_path}")

    return report


def main():
    parser = argparse.ArgumentParser(
        description='Validate a job postings CSV and produce a quality report.'
    )
    parser.add_argument(
        '--input', required=True,
        help='Path to input CSV file (e.g. data/job_descriptions.csv)'
    )
    parser.add_argument(
        '--output', default='outputs/data_quality_report.json',
        help='Path to output JSON report (default: outputs/data_quality_report.json)'
    )
    args = parser.parse_args()
    validate(args.input, args.output)


if __name__ == '__main__':
    main()
