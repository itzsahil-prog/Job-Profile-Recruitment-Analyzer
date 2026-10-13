#!/usr/bin/env python3
"""
build_vectors.py — Build binary feature matrices for clustering.

Reads a job-skill pairs CSV and a skill-group assignments CSV, then produces:
  1. A binary job-by-skill matrix (rows=jobs, cols=skills, values=0/1)
  2. A binary job-by-skill-group matrix (rows=jobs, cols=group_ids, values=0/1)

Both matrices are saved as CSV files to the output directory.

Usage:
    python analytics/build_vectors.py \\
        --job-skills outputs/job_skills.csv \\
        --skill-groups outputs/skill_group_assignments.csv

    python analytics/build_vectors.py \\
        --job-skills outputs/job_skills.csv \\
        --skill-groups outputs/skill_group_assignments.csv \\
        --output-dir outputs/
"""

import argparse
import os
import sys

import pandas as pd


def load_job_skills(path):
    """
    Load job-skill pairs CSV.

    Expected columns: job_id, skill_name (exact names or containing those substrings).

    Parameters
    ----------
    path : str

    Returns
    -------
    pd.DataFrame with columns ['job_id', 'skill_name']
    """
    if not os.path.isfile(path):
        print(f"ERROR: Job-skills file not found: {path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip()

    # Flexible column detection
    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if 'job_id' in cl or 'jobid' in cl:
            col_map['job_id'] = col
        elif 'skill' in cl:
            col_map['skill_name'] = col

    if 'job_id' not in col_map or 'skill_name' not in col_map:
        print(
            f"ERROR: Could not find job_id and skill_name columns in {path}. "
            f"Found columns: {list(df.columns)}",
            file=sys.stderr,
        )
        sys.exit(1)

    df = df[[col_map['job_id'], col_map['skill_name']]].rename(
        columns={col_map['job_id']: 'job_id', col_map['skill_name']: 'skill_name'}
    )
    df = df.dropna(subset=['job_id', 'skill_name'])
    df['job_id'] = df['job_id'].str.strip()
    df['skill_name'] = df['skill_name'].str.strip().str.lower()
    return df


def load_skill_groups(path):
    """
    Load skill group assignments CSV.

    Expected columns: canonical_skill, group_id (exact or containing substrings).

    Parameters
    ----------
    path : str

    Returns
    -------
    dict mapping canonical_skill (lowercased) -> group_id (str)
    """
    if not os.path.isfile(path):
        print(f"ERROR: Skill groups file not found: {path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip()

    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if 'canonical' in cl or 'skill' in cl:
            col_map.setdefault('skill', col)
        if 'group' in cl:
            col_map['group'] = col

    if 'skill' not in col_map or 'group' not in col_map:
        print(
            f"ERROR: Could not find skill and group columns in {path}. "
            f"Found columns: {list(df.columns)}",
            file=sys.stderr,
        )
        sys.exit(1)

    df = df[[col_map['skill'], col_map['group']]].rename(
        columns={col_map['skill']: 'canonical_skill', col_map['group']: 'group_id'}
    )
    df = df.dropna()
    df['canonical_skill'] = df['canonical_skill'].str.strip().str.lower()
    df['group_id'] = df['group_id'].str.strip()
    return dict(zip(df['canonical_skill'], df['group_id']))


def build_job_skill_matrix(job_skills_df):
    """
    Build a binary job-by-skill matrix.

    Parameters
    ----------
    job_skills_df : pd.DataFrame with columns ['job_id', 'skill_name']

    Returns
    -------
    pd.DataFrame
        Index = job_id, columns = skill names, values = 0/1.
    """
    matrix = (
        job_skills_df
        .drop_duplicates()
        .assign(value=1)
        .pivot_table(index='job_id', columns='skill_name', values='value', fill_value=0)
    )
    matrix.columns.name = None
    return matrix


def build_job_skillgroup_matrix(job_skills_df, skill_group_map):
    """
    Build a binary job-by-skill-group matrix.

    Skills not found in skill_group_map are assigned group_id 'unassigned'.

    Parameters
    ----------
    job_skills_df : pd.DataFrame with columns ['job_id', 'skill_name']
    skill_group_map : dict  skill_name -> group_id

    Returns
    -------
    pd.DataFrame
        Index = job_id, columns = group_ids, values = 0/1.
    """
    df = job_skills_df.copy()
    df['group_id'] = df['skill_name'].map(skill_group_map).fillna('unassigned')
    matrix = (
        df[['job_id', 'group_id']]
        .drop_duplicates()
        .assign(value=1)
        .pivot_table(index='job_id', columns='group_id', values='value', fill_value=0)
    )
    matrix.columns.name = None
    return matrix


def main():
    """Parse arguments and build feature matrices."""
    parser = argparse.ArgumentParser(
        description='Build binary job-by-skill and job-by-skill-group feature matrices.'
    )
    parser.add_argument(
        '--job-skills', required=True,
        help='Path to job-skill pairs CSV (columns: job_id, skill_name)'
    )
    parser.add_argument(
        '--skill-groups', required=True,
        help='Path to skill group assignments CSV (columns: canonical_skill, group_id)'
    )
    parser.add_argument(
        '--output-dir', default='outputs',
        help='Directory to save output matrices (default: outputs/)'
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Load inputs
    job_skills_df = load_job_skills(args.job_skills)
    skill_group_map = load_skill_groups(args.skill_groups)

    print(f"Loaded {len(job_skills_df)} job-skill pairs.")
    print(f"Loaded {len(skill_group_map)} skill-group mappings.")

    # Build matrices
    skill_matrix = build_job_skill_matrix(job_skills_df)
    group_matrix = build_job_skillgroup_matrix(job_skills_df, skill_group_map)

    # Save outputs
    skill_out = os.path.join(args.output_dir, 'job_skill_matrix.csv')
    group_out = os.path.join(args.output_dir, 'job_skillgroup_matrix.csv')

    skill_matrix.to_csv(skill_out)
    group_matrix.to_csv(group_out)

    print(f"Job-by-skill matrix: {skill_matrix.shape} → {skill_out}")
    print(f"Job-by-skill-group matrix: {group_matrix.shape} → {group_out}")


if __name__ == '__main__':
    main()
