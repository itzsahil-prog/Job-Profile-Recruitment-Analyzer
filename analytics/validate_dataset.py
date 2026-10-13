#!/usr/bin/env python3
"""
validate_dataset.py — Dataset validation and quality reporting for the
Big Data Job Profile Recruitment Analyzer.

Reads a job postings CSV file, performs quality checks, and writes a JSON
report to the specified output path. Handles UTF-8 and latin-1 encodings,
quoted commas, duplicate job_ids, and missing values.

Usage:
    python analytics/validate_dataset.py --input data/job_postings.csv
    python analytics/validate_dataset.py --input data/job_postings.csv \\
        --output outputs/my_report.json

Output JSON keys:
    source_path, encoding_detected, total_rows_raw, columns, schema_mapping,
    missing_values, duplicate_rows, rows_after_dedup, rejected_rows,
    rows_retained, validation_timestamp
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Logical field names we try to map input columns to
# ---------------------------------------------------------------------------
LOGICAL_FIELDS = [
    'job_id', 'job_title', 'company', 'location',
    'salary_range', 'experience_required', 'skills_required',
    'description', 'post_date',
]


def detect_encoding(filepath):
    """
    Try to open the file with UTF-8; fall back to latin-1 if that fails.

    Parameters
    ----------
    filepath : str
        Path to the CSV file.

    Returns
    -------
    str
        'utf-8' or 'latin-1'
    """
    for encoding in ('utf-8', 'latin-1'):
        try:
            with open(filepath, newline='', encoding=encoding) as f:
                # Read a few lines to trigger any encoding errors
                for _ in zip(range(100), f):
                    pass
            return encoding
        except UnicodeDecodeError:
            continue
    # If both fail, return utf-8 with errors='replace' as last resort
    return 'utf-8'


def map_schema(columns):
    """
    Map actual column names to logical field names by substring matching.

    For each logical field, find the first actual column whose name contains
    the logical field name as a case-insensitive substring.

    Parameters
    ----------
    columns : list of str
        Actual column names from the CSV header.

    Returns
    -------
    dict
        {actual_column_name: logical_field_name, ...} for matched columns only.
    """
    mapping = {}
    for logical in LOGICAL_FIELDS:
        for col in columns:
            if logical.lower() in col.lower():
                if col not in mapping:
                    mapping[col] = logical
                break
    return mapping


def find_job_id_column(columns, schema_mapping):
    """
    Return the actual column name that maps to the 'job_id' logical field,
    or None if no such mapping exists.
    """
    for col, logical in schema_mapping.items():
        if logical == 'job_id':
            return col
    return None


def load_csv(filepath, encoding):
    """
    Load a CSV file into a list of dicts using the csv module (handles quoted fields).

    Parameters
    ----------
    filepath : str
        Path to the CSV file.
    encoding : str
        File encoding to use.

    Returns
    -------
    tuple of (list of dict, list of str)
        Rows and column names.
    """
    rows = []
    columns = []
    with open(filepath, newline='', encoding=encoding, errors='replace') as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames) if reader.fieldnames else []
        for row in reader:
            rows.append(dict(row))
    return rows, columns


def count_missing(rows, columns):
    """
    Count missing values per column.

    A value is considered missing if it is None or an empty/whitespace-only string.

    Parameters
    ----------
    rows : list of dict
    columns : list of str

    Returns
    -------
    dict
        {column_name: missing_count, ...}
    """
    missing = {col: 0 for col in columns}
    for row in rows:
        for col in columns:
            val = row.get(col)
            if val is None or (isinstance(val, str) and not val.strip()):
                missing[col] += 1
    return missing


def deduplicate(rows, job_id_col):
    """
    Deduplicate rows by job_id column, keeping first occurrence.

    If job_id_col is None, deduplicates by full-row string representation.

    Parameters
    ----------
    rows : list of dict
    job_id_col : str or None

    Returns
    -------
    tuple of (deduped_rows, duplicate_count)
    """
    seen = set()
    deduped = []
    duplicates = 0
    for row in rows:
        if job_id_col:
            key = row.get(job_id_col, '')
        else:
            key = str(sorted(row.items()))

        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
            deduped.append(row)
    return deduped, duplicates


def reject_rows(rows, required_logicals, schema_mapping):
    """
    Reject rows that are missing values in required logical fields.

    Required logical fields: job_id, job_title, description (if mapped).

    Parameters
    ----------
    rows : list of dict
    required_logicals : list of str
        Logical field names that must be present.
    schema_mapping : dict
        {actual_col: logical_field} mapping.

    Returns
    -------
    tuple of (retained_rows, rejected_count)
    """
    # Build reverse mapping: logical -> actual column
    logical_to_col = {v: k for k, v in schema_mapping.items()}

    retained = []
    rejected = 0
    for row in rows:
        keep = True
        for logical in required_logicals:
            col = logical_to_col.get(logical)
            if col is None:
                continue  # Column not present in dataset — skip check
            val = row.get(col)
            if val is None or (isinstance(val, str) and not val.strip()):
                keep = False
                break
        if keep:
            retained.append(row)
        else:
            rejected += 1
    return retained, rejected


def validate(input_path, output_path):
    """
    Run full validation pipeline and write a JSON quality report.

    Parameters
    ----------
    input_path : str
        Path to the input CSV file.
    output_path : str
        Path to write the JSON quality report.

    Returns
    -------
    dict
        The quality report dictionary.
    """
    if not os.path.isfile(input_path):
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Step 1: detect encoding
    encoding = detect_encoding(input_path)

    # Step 2: load CSV
    rows, columns = load_csv(input_path, encoding)
    total_rows_raw = len(rows)

    # Step 3: schema mapping
    schema_mapping = map_schema(columns)
    job_id_col = find_job_id_column(columns, schema_mapping)

    # Step 4: missing values (on raw rows)
    missing_values = count_missing(rows, columns)

    # Step 5: deduplicate
    deduped_rows, duplicate_count = deduplicate(rows, job_id_col)
    rows_after_dedup = len(deduped_rows)

    # Step 6: reject rows missing required fields
    retained_rows, rejected_count = reject_rows(
        deduped_rows,
        required_logicals=['job_id', 'job_title', 'description'],
        schema_mapping=schema_mapping,
    )
    rows_retained = len(retained_rows)

    # Step 7: build report
    report = {
        'source_path': os.path.abspath(input_path),
        'encoding_detected': encoding,
        'total_rows_raw': total_rows_raw,
        'columns': columns,
        'schema_mapping': schema_mapping,
        'missing_values': missing_values,
        'duplicate_rows': duplicate_count,
        'rows_after_dedup': rows_after_dedup,
        'rejected_rows': rejected_count,
        'rows_retained': rows_retained,
        'validation_timestamp': datetime.now(timezone.utc).isoformat(),
    }

    # Step 8: write output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Validation complete.")
    print(f"  Total rows (raw):  {total_rows_raw}")
    print(f"  Duplicates:        {duplicate_count}")
    print(f"  Rejected rows:     {rejected_count}")
    print(f"  Rows retained:     {rows_retained}")
    print(f"  Report written to: {output_path}")

    return report


def main():
    """Parse CLI arguments and run validation."""
    parser = argparse.ArgumentParser(
        description='Validate a job postings CSV and produce a quality report.'
    )
    parser.add_argument(
        '--input', required=True,
        help='Path to input CSV file (e.g. data/job_postings.csv)'
    )
    parser.add_argument(
        '--output', default='outputs/data_quality_report.json',
        help='Path to output JSON report (default: outputs/data_quality_report.json)'
    )
    args = parser.parse_args()
    validate(args.input, args.output)


if __name__ == '__main__':
    main()
