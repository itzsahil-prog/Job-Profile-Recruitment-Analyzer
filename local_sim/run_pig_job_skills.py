#!/usr/bin/env python3
"""
run_pig_job_skills.py — Local simulation of Pig's build_job_skills.pig.

Uses a single combined regex (one pass per row) to extract all skills at once.
Much faster than 79 separate str.contains() calls.

Output columns: job_id, skill_name, match_method
  match_method: 'both' | 'description' | 'explicit'
"""
import csv
import os
import re
import sys
import time
from collections import defaultdict

import pandas as pd

WORKDIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_CSV = os.path.join(WORKDIR, 'config', 'skills_dictionary.csv')
INPUT_CSV  = os.path.join(WORKDIR, 'outputs', 'clean_jobs.csv')
OUTPUT_CSV = os.path.join(WORKDIR, 'outputs', 'job_skills.csv')
LOG_FILE   = os.path.join(WORKDIR, 'outputs', 'pig_job_skills_log.txt')
OUTPUT_DIR = os.path.join(WORKDIR, 'outputs')
CHUNKSIZE  = 50_000

OUTPUT_COLUMNS = ['job_id', 'skill_name', 'match_method']


def load_skill_map(skills_csv):
    """Single combined regex + term→canonical dict."""
    if not os.path.isfile(skills_csv):
        print(f"ERROR: {skills_csv} not found", file=sys.stderr)
        sys.exit(1)

    term_to_canonical = {}
    all_terms = []

    with open(skills_csv, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if not row:
                continue
            canonical = row[0].strip()
            if not canonical:
                continue
            terms = [canonical] + [t.strip() for t in row[1:-1] if t.strip()]
            for term in terms:
                tl = term.lower()
                if tl not in term_to_canonical:
                    term_to_canonical[tl] = canonical
                    all_terms.append(term)

    all_terms.sort(key=len, reverse=True)
    alternation = '|'.join(re.escape(t) for t in all_terms)
    combined = re.compile(r'(?<!\w)(?:' + alternation + r')(?!\w)', re.IGNORECASE)
    return combined, term_to_canonical


def extract_skills(text, combined_pat, term_to_canonical):
    """Return set of canonical skill names found in text."""
    if not text:
        return set()
    matches = combined_pat.findall(text)
    return {term_to_canonical.get(m.lower(), m) for m in matches}


def main():
    start_time = time.time()
    start_str  = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    print(f"[run_pig_job_skills] Started at {start_str}")
    print(f"Input:  {INPUT_CSV}")
    print(f"Output: {OUTPUT_CSV}")

    if not os.path.isfile(INPUT_CSV):
        print(f"ERROR: {INPUT_CSV} not found. Run run_pig_cleaning.py first.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading skill patterns...")
    combined_pat, term_to_canonical = load_skill_map(SKILLS_CSV)
    print(f"  Loaded {len(term_to_canonical)} terms → combined regex.")

    total_input  = 0
    total_output = 0
    first_write  = True

    # Track globally seen (job_id, skill) pairs to avoid cross-chunk duplicates
    seen_pairs = set()

    print("\nExtracting skills (single-pass regex)...")
    chunk_iter = pd.read_csv(
        INPUT_CSV,
        encoding='utf-8',
        encoding_errors='replace',
        chunksize=CHUNKSIZE,
        low_memory=False,
        dtype=str,
        usecols=['job_id', 'description_clean', 'skills'],
    )

    for chunk in chunk_iter:
        chunk = chunk.fillna('')
        batch_rows = []

        for _, row in chunk.iterrows():
            job_id     = row['job_id'].strip()
            desc_text  = row['description_clean'].lower()
            skill_text = row['skills'].lower()

            if not job_id:
                total_input += 1
                continue

            desc_skills = extract_skills(desc_text, combined_pat, term_to_canonical)
            expl_skills = extract_skills(skill_text, combined_pat, term_to_canonical)
            all_skills  = desc_skills | expl_skills

            for skill in all_skills:
                pair = (job_id, skill)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                if skill in desc_skills and skill in expl_skills:
                    method = 'both'
                elif skill in desc_skills:
                    method = 'description'
                else:
                    method = 'explicit'
                batch_rows.append((job_id, skill, method))

            total_input += 1

        if batch_rows:
            df_batch = pd.DataFrame(batch_rows, columns=OUTPUT_COLUMNS)
            mode   = 'w' if first_write else 'a'
            header = first_write
            df_batch.to_csv(OUTPUT_CSV, mode=mode, header=header, index=False)
            total_output += len(batch_rows)
            first_write = False

        if (total_input // 100_000) > ((total_input - len(chunk)) // 100_000):
            print(f"  Processed {total_input:,} rows | skill pairs: {total_output:,}", flush=True)

    if first_write:
        pd.DataFrame(columns=OUTPUT_COLUMNS).to_csv(OUTPUT_CSV, index=False)

    end_time = time.time()
    elapsed  = end_time - start_time
    end_str  = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Pig Job Skills — Local Simulation Log\n")
        f.write("=" * 60 + "\n")
        f.write(f"Start:               {start_str}\n")
        f.write(f"End:                 {end_str}\n")
        f.write(f"Elapsed (s):         {elapsed:.1f}\n")
        f.write(f"Input rows:          {total_input:,}\n")
        f.write(f"Output (job,skill):  {total_output:,}\n")
        f.write(f"Output file:         {OUTPUT_CSV}\n")

    print(f"\n{'='*60}")
    print(f"Pig job_skills complete in {elapsed:.1f}s")
    print(f"  Input rows:          {total_input:,}")
    print(f"  Output (job,skill):  {total_output:,}")
    print(f"  Written to:          {OUTPUT_CSV}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
