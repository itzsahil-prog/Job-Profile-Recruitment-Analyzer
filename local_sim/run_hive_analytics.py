#!/usr/bin/env python3
"""
run_hive_analytics.py — SQLite local equivalent of Hive warehouse queries.

Creates outputs/bigdata_jobs.db, loads cleaned data, creates indexes,
runs analytics queries, and saves results to CSV / log files.

Prerequisites (run in order):
    1. run_pig_cleaning.py      -> outputs/clean_jobs.csv
    2. run_pig_job_skills.py    -> outputs/job_skills.csv
    3. run_mapreduce.py         -> outputs/skill_frequency_post_count.csv
"""
import csv
import os
import sqlite3
import sys
import time

import pandas as pd

WORKDIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(WORKDIR, 'outputs')

DB_PATH              = os.path.join(OUTPUT_DIR, 'bigdata_jobs.db')
CLEAN_JOBS_CSV       = os.path.join(OUTPUT_DIR, 'clean_jobs.csv')
JOB_SKILLS_CSV       = os.path.join(OUTPUT_DIR, 'job_skills.csv')
SKILL_FREQ_CSV       = os.path.join(OUTPUT_DIR, 'skill_frequency_post_count.csv')
LOG_FILE             = os.path.join(OUTPUT_DIR, 'hive_run_log.txt')

CHUNKSIZE = 50_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_table(headers, rows, max_rows=30):
    """Format a list of rows as a simple fixed-width text table."""
    all_rows = [headers] + [list(map(str, r)) for r in rows[:max_rows]]
    widths   = [max(len(str(cell)) for cell in col) for col in zip(*all_rows)]
    sep      = "  ".join("-" * w for w in widths)
    lines    = []
    for i, row in enumerate(all_rows):
        line = "  ".join(str(cell).ljust(w) for cell, w in zip(row, widths))
        lines.append(line)
        if i == 0:
            lines.append(sep)
    return "\n".join(lines)


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


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

DDL = """
CREATE TABLE IF NOT EXISTS job_posts (
    job_id              TEXT PRIMARY KEY,
    normalized_job_title TEXT,
    raw_job_title       TEXT,
    company             TEXT,
    location            TEXT,
    experience_required TEXT,
    description_clean   TEXT,
    skills              TEXT
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id       TEXT,
    skill_name   TEXT,
    match_method TEXT
);

CREATE TABLE IF NOT EXISTS skill_frequency (
    skill_name TEXT,
    post_count INTEGER
);
"""


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_job_posts(conn, path):
    """Load clean_jobs.csv into job_posts table in chunks."""
    if not os.path.isfile(path):
        print(f"  WARNING: {path} not found — skipping job_posts load.", file=sys.stderr)
        return 0

    total = 0
    chunk_iter = pd.read_csv(
        path,
        encoding='utf-8',
        encoding_errors='replace',
        chunksize=CHUNKSIZE,
        low_memory=False,
        dtype=str,
    )
    cursor = conn.cursor()
    sql = """
        INSERT OR IGNORE INTO job_posts
            (job_id, normalized_job_title, raw_job_title, company, location,
             experience_required, description_clean, skills)
        VALUES (?,?,?,?,?,?,?,?)
    """
    for chunk in chunk_iter:
        rows = [
            (
                safe_str(r.get('job_id')),
                safe_str(r.get('normalized_job_title')),
                safe_str(r.get('raw_job_title')),
                safe_str(r.get('company')),
                safe_str(r.get('location')),
                safe_str(r.get('experience_required')),
                safe_str(r.get('description_clean')),
                safe_str(r.get('skills')),
            )
            for _, r in chunk.iterrows()
            if safe_str(r.get('job_id'))
        ]
        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        print(f"  job_posts: {total:,} rows loaded...", flush=True)

    return total


def load_job_skills(conn, path):
    """Load job_skills.csv into job_skills table in chunks."""
    if not os.path.isfile(path):
        print(f"  WARNING: {path} not found — skipping job_skills load.", file=sys.stderr)
        return 0

    total = 0
    chunk_iter = pd.read_csv(
        path,
        encoding='utf-8',
        encoding_errors='replace',
        chunksize=CHUNKSIZE,
        low_memory=False,
        dtype=str,
    )
    cursor = conn.cursor()
    sql = "INSERT INTO job_skills (job_id, skill_name, match_method) VALUES (?,?,?)"
    for chunk in chunk_iter:
        rows = [
            (
                safe_str(r.get('job_id')),
                safe_str(r.get('skill_name')),
                safe_str(r.get('match_method')),
            )
            for _, r in chunk.iterrows()
            if safe_str(r.get('job_id')) and safe_str(r.get('skill_name'))
        ]
        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        print(f"  job_skills: {total:,} rows loaded...", flush=True)

    return total


def load_skill_frequency(conn, path):
    """Load skill_frequency_post_count.csv into skill_frequency table."""
    if not os.path.isfile(path):
        print(f"  WARNING: {path} not found — skipping skill_frequency load.", file=sys.stderr)
        return 0

    total = 0
    cursor = conn.cursor()
    sql = "INSERT INTO skill_frequency (skill_name, post_count) VALUES (?,?)"
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            skill = row.get('skill', '').strip()
            count = row.get('post_count', '0').strip()
            if skill:
                rows.append((skill, int(count) if count.isdigit() else 0))
    cursor.executemany(sql, rows)
    conn.commit()
    total = len(rows)
    print(f"  skill_frequency: {total:,} rows loaded.")
    return total


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def run_query_to_csv(conn, sql, out_path, description):
    """Execute SQL, save results to CSV, return rows."""
    cursor = conn.cursor()
    cursor.execute(sql)
    rows    = cursor.fetchall()
    headers = [d[0] for d in cursor.description]

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"  {description}: {len(rows)} rows -> {out_path}")
    return headers, rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    start_time = time.time()
    start_str  = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    print(f"[run_hive_analytics] Started at {start_str}")
    print(f"Database: {DB_PATH}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Create / connect to SQLite database
    # ------------------------------------------------------------------
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    for stmt in DDL.strip().split(';'):
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)
    conn.commit()
    print("Schema created (or already exists).")

    # ------------------------------------------------------------------
    # 2. Load data
    # ------------------------------------------------------------------
    print("\nLoading data...")
    jp_count  = load_job_posts(conn, CLEAN_JOBS_CSV)
    js_count  = load_job_skills(conn, JOB_SKILLS_CSV)
    sf_count  = load_skill_frequency(conn, SKILL_FREQ_CSV)

    # ------------------------------------------------------------------
    # 3. Create indexes
    # ------------------------------------------------------------------
    print("\nCreating indexes...")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill_name);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_job_skills_job   ON job_skills(job_id);")
    conn.commit()
    print("  Indexes ready.")

    # ------------------------------------------------------------------
    # 4. Analytics queries
    # ------------------------------------------------------------------
    print("\nRunning analytics queries...")

    q1_headers, q1_rows = run_query_to_csv(
        conn,
        """
        SELECT skill_name,
               COUNT(DISTINCT job_id) AS post_count
        FROM   job_skills
        GROUP  BY skill_name
        ORDER  BY post_count DESC
        LIMIT  50
        """,
        os.path.join(OUTPUT_DIR, 'hive_top_skills.csv'),
        "Q1 top_skills",
    )

    q2_headers, q2_rows = run_query_to_csv(
        conn,
        """
        SELECT normalized_job_title,
               COUNT(DISTINCT job_id) AS job_count
        FROM   job_posts
        GROUP  BY normalized_job_title
        ORDER  BY job_count DESC
        LIMIT  50
        """,
        os.path.join(OUTPUT_DIR, 'hive_job_title_distribution.csv'),
        "Q2 job_title_distribution",
    )

    q3_headers, q3_rows = run_query_to_csv(
        conn,
        """
        SELECT jp.normalized_job_title,
               js.skill_name,
               COUNT(DISTINCT js.job_id) AS post_count
        FROM   job_skills js
        JOIN   job_posts  jp ON js.job_id = jp.job_id
        GROUP  BY jp.normalized_job_title, js.skill_name
        ORDER  BY jp.normalized_job_title ASC, post_count DESC
        LIMIT  500
        """,
        os.path.join(OUTPUT_DIR, 'hive_skill_by_title.csv'),
        "Q3 skill_by_title",
    )

    # Q4 and Q5 — logged only
    cursor = conn.cursor()

    cursor.execute("""
        SELECT   location,
                 COUNT(DISTINCT job_id) AS posting_count
        FROM     job_posts
        WHERE    location IS NOT NULL AND location != ''
        GROUP BY location
        ORDER BY posting_count DESC
        LIMIT    30
    """)
    q4_rows    = cursor.fetchall()
    q4_headers = [d[0] for d in cursor.description]
    print(f"  Q4 location_distribution: {len(q4_rows)} rows (logged)")

    cursor.execute("""
        SELECT   LOWER(skill_name) AS skill_lower,
                 COUNT(*) AS cnt
        FROM     job_skills
        GROUP BY LOWER(skill_name)
        ORDER BY cnt DESC
        LIMIT    10
    """)
    q5_rows    = cursor.fetchall()
    q5_headers = [d[0] for d in cursor.description]
    print(f"  Q5 lower_skill_demo: {len(q5_rows)} rows (logged)")

    # ------------------------------------------------------------------
    # 5. Write log
    # ------------------------------------------------------------------
    end_time = time.time()
    end_str  = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    elapsed  = end_time - start_time

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("Hive Analytics — Local Simulation (SQLite) Log\n")
        f.write("=" * 70 + "\n")
        f.write(f"Start time:          {start_str}\n")
        f.write(f"End time:            {end_str}\n")
        f.write(f"Elapsed (seconds):   {elapsed:.1f}\n")
        f.write(f"Database:            {DB_PATH}\n")
        f.write(f"\nRows loaded:\n")
        f.write(f"  job_posts:         {jp_count:,}\n")
        f.write(f"  job_skills:        {js_count:,}\n")
        f.write(f"  skill_frequency:   {sf_count:,}\n")

        f.write("\n\n" + "=" * 70 + "\n")
        f.write("Q1: Top 50 Skills (by distinct job_id count)\n")
        f.write("=" * 70 + "\n")
        f.write(fmt_table(q1_headers, q1_rows) + "\n")

        f.write("\n\n" + "=" * 70 + "\n")
        f.write("Q2: Job Title Distribution (top 50)\n")
        f.write("=" * 70 + "\n")
        f.write(fmt_table(q2_headers, q2_rows) + "\n")

        f.write("\n\n" + "=" * 70 + "\n")
        f.write("Q4: Location Distribution (top 30)\n")
        f.write("=" * 70 + "\n")
        f.write(fmt_table(q4_headers, q4_rows) + "\n")

        f.write("\n\n" + "=" * 70 + "\n")
        f.write("Q5: LOWER(skill_name) frequency demo (top 10)\n")
        f.write("=" * 70 + "\n")
        f.write(fmt_table(q5_headers, q5_rows) + "\n")

    print(f"\nWrote log: {LOG_FILE}")

    conn.close()

    # ------------------------------------------------------------------
    # 6. Final summary
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"Hive analytics simulation complete.")
    print(f"  Elapsed:       {elapsed:.1f}s")
    print(f"  job_posts:     {jp_count:,}")
    print(f"  job_skills:    {js_count:,}")
    print(f"Outputs:")
    print(f"  outputs/hive_top_skills.csv")
    print(f"  outputs/hive_job_title_distribution.csv")
    print(f"  outputs/hive_skill_by_title.csv")
    print(f"  outputs/hive_run_log.txt")
    print(f"  outputs/bigdata_jobs.db")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
