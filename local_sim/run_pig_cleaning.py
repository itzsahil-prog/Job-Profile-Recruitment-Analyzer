#!/usr/bin/env python3
"""
run_pig_cleaning.py — Local simulation of Pig LOAD -> FILTER -> DISTINCT
                      -> FOREACH GENERATE -> STORE pipeline.

Reads data/job_descriptions.csv in chunks, applies the same cleaning rules
that build_clean_jobs.pig would apply, and writes outputs/clean_jobs.csv.

Output columns: job_id, job_title, raw_job_title, company, location,
                experience_required, description_clean, skills
"""
import csv
import os
import sys
import time

import pandas as pd

WORKDIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV  = os.path.join(WORKDIR, 'data', 'job_descriptions.csv')
OUTPUT_CSV = os.path.join(WORKDIR, 'outputs', 'clean_jobs.csv')
LOG_FILE   = os.path.join(WORKDIR, 'outputs', 'pig_cleaning_log.txt')
ALIASES_CSV = os.path.join(WORKDIR, 'config', 'title_aliases.csv')
OUTPUT_DIR = os.path.join(WORKDIR, 'outputs')
CHUNKSIZE  = 50_000

OUTPUT_COLUMNS = [
    'job_id', 'raw_job_title', 'normalized_job_title', 'company', 'location',
    'experience_required', 'description_clean', 'skills',
]


def load_title_aliases(path):
    """
    Load title_aliases.csv into a dict: {lowercase_pattern: normalized_title}.
    """
    aliases = {}
    if not os.path.isfile(path):
        print(f"Warning: title_aliases.csv not found at {path}", file=sys.stderr)
        return aliases
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pattern    = row.get('raw_title_pattern', '').strip().lower()
            normalized = row.get('normalized_title', '').strip()
            if pattern and normalized:
                aliases[pattern] = normalized
    return aliases


def safe_str(val):
    """Return stripped string, or '' for NaN / None."""
    if val is None:
        return ''
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return ''
    except (TypeError, ValueError):
        pass
    return str(val).strip()


def build_location(loc_val, country_val):
    """Combine location and country, handling empty parts."""
    loc     = safe_str(loc_val)
    country = safe_str(country_val)
    if loc and country:
        return f"{loc}, {country}"
    return loc or country


def process_chunk(chunk, aliases, seen_ids):
    """
    Apply Pig-equivalent transformations to one DataFrame chunk.

    Returns
    -------
    pd.DataFrame  — cleaned rows in OUTPUT_COLUMNS order
    stats dict    — {input, duplicates, invalid}
    """
    input_count     = len(chunk)
    duplicates      = 0
    invalid_removed = 0
    output_rows     = []

    for _, row in chunk.iterrows():
        job_id    = safe_str(row.get('Job Id'))
        job_title_raw = safe_str(row.get('Job Title'))
        description   = safe_str(row.get('Job Description'))

        # --- Filter: reject rows missing required fields ---
        if not job_id or not job_title_raw or not description:
            invalid_removed += 1
            continue

        # --- Deduplicate by Job Id (keep first across all chunks) ---
        if job_id in seen_ids:
            duplicates += 1
            continue
        seen_ids.add(job_id)

        # --- Normalise strings ---
        company     = safe_str(row.get('Company'))
        location    = build_location(row.get('location'), row.get('Country'))
        experience  = safe_str(row.get('Experience'))
        skills_val  = safe_str(row.get('skills'))

        # --- Title alias mapping ---
        title_lower = job_title_raw.lower()
        raw_job_title = title_lower
        job_title_normalized = aliases.get(title_lower, title_lower)

        output_rows.append({
            'job_id':               job_id,
            'raw_job_title':        raw_job_title,
            'normalized_job_title': job_title_normalized,
            'company':              company,
            'location':             location,
            'experience_required':  experience,
            'description_clean':    description,
            'skills':               skills_val,
        })

    df_out = pd.DataFrame(output_rows, columns=OUTPUT_COLUMNS) if output_rows else pd.DataFrame(columns=OUTPUT_COLUMNS)
    stats  = {
        'input':      input_count,
        'duplicates': duplicates,
        'invalid':    invalid_removed,
    }
    return df_out, stats


def main():
    start_time = time.time()
    start_str  = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    print(f"[run_pig_cleaning] Started at {start_str}")
    print(f"Input:  {INPUT_CSV}")
    print(f"Output: {OUTPUT_CSV}")

    if not os.path.isfile(INPUT_CSV):
        print(f"ERROR: Input file not found: {INPUT_CSV}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # Load title aliases
    # ------------------------------------------------------------------
    aliases = load_title_aliases(ALIASES_CSV)
    print(f"Loaded {len(aliases)} title aliases.")

    # ------------------------------------------------------------------
    # Detect encoding
    # ------------------------------------------------------------------
    encoding = 'utf-8'
    for enc in ('utf-8', 'latin-1'):
        try:
            with open(INPUT_CSV, encoding=enc) as f:
                for _ in zip(range(200), f):
                    pass
            encoding = enc
            break
        except UnicodeDecodeError:
            continue
    print(f"Encoding: {encoding}")

    # ------------------------------------------------------------------
    # Stream and clean
    # ------------------------------------------------------------------
    seen_ids            = set()
    total_input         = 0
    total_duplicates    = 0
    total_invalid       = 0
    total_output        = 0
    first_write         = True

    chunk_iter = pd.read_csv(
        INPUT_CSV,
        encoding=encoding,
        encoding_errors='replace',
        chunksize=CHUNKSIZE,
        low_memory=False,
        dtype=str,
    )

    print("\nCleaning rows...")
    for chunk in chunk_iter:
        df_clean, stats = process_chunk(chunk, aliases, seen_ids)

        total_input      += stats['input']
        total_duplicates += stats['duplicates']
        total_invalid    += stats['invalid']
        total_output     += len(df_clean)

        # Write cleaned chunk to output CSV
        if not df_clean.empty:
            mode   = 'w' if first_write else 'a'
            header = first_write
            df_clean.to_csv(OUTPUT_CSV, mode=mode, header=header, index=False)
            first_write = False

        # Progress every ~100k rows
        prev_bucket = (total_input - stats['input']) // 100_000
        curr_bucket = total_input // 100_000
        if curr_bucket > prev_bucket:
            print(f"  Processed {total_input:,} input rows  |  output so far: {total_output:,}", flush=True)

    # ------------------------------------------------------------------
    # Write log
    # ------------------------------------------------------------------
    end_time = time.time()
    end_str  = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    elapsed  = end_time - start_time

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Pig Cleaning — Local Simulation Log\n")
        f.write("=" * 60 + "\n")
        f.write(f"Start time:           {start_str}\n")
        f.write(f"End time:             {end_str}\n")
        f.write(f"Elapsed (seconds):    {elapsed:.1f}\n")
        f.write(f"\nInput rows:           {total_input:,}\n")
        f.write(f"Duplicates removed:   {total_duplicates:,}\n")
        f.write(f"Invalid rows removed: {total_invalid:,}\n")
        f.write(f"Output rows:          {total_output:,}\n")
        f.write(f"\nOutput file:          {OUTPUT_CSV}\n")

    print(f"\nWrote log: {LOG_FILE}")

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"Pig cleaning simulation complete.")
    print(f"  Elapsed:            {elapsed:.1f}s")
    print(f"  Input rows:         {total_input:,}")
    print(f"  Duplicates removed: {total_duplicates:,}")
    print(f"  Invalid removed:    {total_invalid:,}")
    print(f"  Output rows:        {total_output:,}")
    print(f"  Written to:         {OUTPUT_CSV}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
