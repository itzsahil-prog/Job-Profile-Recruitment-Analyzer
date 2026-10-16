#!/usr/bin/env python3
"""
build_vectors.py — Build binary job-by-skill matrix for clustering.

Reads outputs/job_skills.csv, deterministically samples 200k jobs (sorted by job_id),
builds a binary job-by-skill matrix, and saves it to outputs/.

Outputs:
    outputs/job_skill_matrix.csv  — rows=job_ids, cols=skills, values=0/1
    outputs/job_ids_sample.csv    — list of the 200k job_ids used
    outputs/skill_columns.json    — ordered list of skill column names
"""
import json
import os
import sys
import time

import pandas as pd

WORKDIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV  = os.path.join(WORKDIR, 'outputs', 'job_skills.csv')
MATRIX_OUT = os.path.join(WORKDIR, 'outputs', 'job_skill_matrix.csv')
IDS_OUT    = os.path.join(WORKDIR, 'outputs', 'job_ids_sample.csv')
COLS_OUT   = os.path.join(WORKDIR, 'outputs', 'skill_columns.json')
SAMPLE_N   = 200_000
CHUNKSIZE  = 50_000

def main():
    start = time.time()
    print(f"[build_vectors] Reading {INPUT_CSV}")

    if not os.path.isfile(INPUT_CSV):
        print(f"ERROR: {INPUT_CSV} not found. Run run_pig_job_skills.py first.", file=sys.stderr)
        sys.exit(1)

    # Pass 1: collect all unique job_ids
    print("Pass 1: collecting unique job_ids...")
    all_job_ids = set()
    for chunk in pd.read_csv(INPUT_CSV, dtype=str, chunksize=CHUNKSIZE, usecols=['job_id']):
        all_job_ids.update(chunk['job_id'].dropna().str.strip().tolist())
    print(f"  Total unique job_ids: {len(all_job_ids):,}")

    # Deterministic sample: sort, take first 200k
    sorted_ids = sorted(all_job_ids)
    sample_ids = sorted_ids[:SAMPLE_N]
    sample_set = set(sample_ids)
    print(f"  Sample size: {len(sample_ids):,}")

    # Save job_ids_sample.csv
    pd.DataFrame({'job_id': sample_ids}).to_csv(IDS_OUT, index=False)
    print(f"  Saved sample ids: {IDS_OUT}")

    # Pass 2: load only sampled rows
    print("Pass 2: loading skill pairs for sampled jobs...")
    chunks = []
    for chunk in pd.read_csv(INPUT_CSV, dtype=str, chunksize=CHUNKSIZE, usecols=['job_id', 'skill_name']):
        chunk = chunk.dropna(subset=['job_id', 'skill_name'])
        chunk['job_id'] = chunk['job_id'].str.strip()
        chunk['skill_name'] = chunk['skill_name'].str.strip().str.lower()
        filtered = chunk[chunk['job_id'].isin(sample_set)]
        if not filtered.empty:
            chunks.append(filtered)
    df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=['job_id', 'skill_name'])
    df = df.drop_duplicates()
    print(f"  Loaded {len(df):,} (job_id, skill_name) pairs")

    # Build binary matrix
    print("Building binary matrix (pivot)...")
    df['value'] = 1
    matrix = df.pivot_table(index='job_id', columns='skill_name', values='value', fill_value=0)
    matrix.columns.name = None
    matrix.index.name = 'job_id'
    print(f"  Matrix shape: {matrix.shape} ({matrix.shape[0]} jobs x {matrix.shape[1]} skills)")

    # Save matrix
    print(f"  Saving matrix to {MATRIX_OUT}...")
    matrix.to_csv(MATRIX_OUT)
    print(f"  Saved.")

    # Save skill columns
    skill_cols = matrix.columns.tolist()
    with open(COLS_OUT, 'w', encoding='utf-8') as f:
        json.dump(skill_cols, f, indent=2)
    print(f"  Saved skill columns: {COLS_OUT} ({len(skill_cols)} skills)")

    elapsed = time.time() - start
    print(f"\nbuild_vectors complete in {elapsed:.1f}s")
    print(f"  Matrix: {matrix.shape[0]} jobs x {matrix.shape[1]} skills")
    print(f"  Files: {MATRIX_OUT}, {IDS_OUT}, {COLS_OUT}")

if __name__ == '__main__':
    main()
