#!/usr/bin/env python3
"""
build_competence_matrix.py — Build the 4×9 job-family × skill-group competence matrix.

For each (job_family, skill_group) cell, calculates the prevalence percentage:

    prevalence(f, g) = distinct posts in family f with ≥1 skill in group g
                       ─────────────────────────────────────────────────────  × 100
                       total distinct posts in family f

Thresholds (Low/Medium/High labels):
    Low:    prevalence  < 20%
    Medium: prevalence >= 20% and < 50%
    High:   prevalence >= 50%

Inputs (all from outputs/):
    job_family_assignments.csv   — columns: job_id, cluster_id
    skill_group_assignments.csv  — columns: canonical_skill, group_id
    job_skills CSV               — columns: job_id, skill_name

Outputs:
    outputs/competence_matrix_numeric.csv  — numeric percentages
    outputs/competence_matrix_labels.csv   — Low / Medium / High labels

Usage:
    python analytics/build_competence_matrix.py \\
        --job-families outputs/job_family_assignments.csv \\
        --skill-groups outputs/skill_group_assignments.csv \\
        --job-skills outputs/job_skills.csv

    python analytics/build_competence_matrix.py \\
        --job-families outputs/job_family_assignments.csv \\
        --skill-groups outputs/skill_group_assignments.csv \\
        --job-skills outputs/job_skills.csv \\
        --output-dir outputs/
"""

import argparse
import os
import sys

import pandas as pd


# Threshold constants (documented — adjust for real data)
THRESHOLD_HIGH = 50.0    # percent
THRESHOLD_MED = 20.0     # percent


def apply_label(pct):
    """
    Convert a numeric prevalence percentage to a Low/Medium/High label.

    Parameters
    ----------
    pct : float
        Percentage in [0, 100].

    Returns
    -------
    str
        'High', 'Medium', or 'Low'
    """
    if pct >= THRESHOLD_HIGH:
        return 'High'
    elif pct >= THRESHOLD_MED:
        return 'Medium'
    else:
        return 'Low'


def load_csv_required(path, label):
    """
    Load a CSV file, exiting with a clear error if not found.

    Parameters
    ----------
    path : str
    label : str
        Human-readable name for error messages.

    Returns
    -------
    pd.DataFrame
    """
    if not os.path.isfile(path):
        print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return pd.read_csv(path, dtype=str)


def main():
    """Build the competence matrix from clustering outputs and job-skill pairs."""
    parser = argparse.ArgumentParser(
        description='Build the 4×9 job-family × skill-group competence matrix.'
    )
    parser.add_argument(
        '--job-families', default='outputs/job_family_assignments.csv',
        help='Path to job family assignments CSV (columns: job_id, cluster_id)'
    )
    parser.add_argument(
        '--skill-groups', default='outputs/skill_group_assignments.csv',
        help='Path to skill group assignments CSV (columns: canonical_skill, group_id)'
    )
    parser.add_argument(
        '--job-skills', default='outputs/job_skills.csv',
        help='Path to job-skill pairs CSV (columns: job_id, skill_name)'
    )
    parser.add_argument(
        '--output-dir', default='outputs',
        help='Directory to save output matrices (default: outputs/)'
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Load all inputs
    fam_df = load_csv_required(args.job_families, 'Job family assignments')
    sg_df = load_csv_required(args.skill_groups, 'Skill group assignments')
    js_df = load_csv_required(args.job_skills, 'Job-skill pairs')

    # Normalize column names (strip whitespace, lowercase detection)
    fam_df.columns = fam_df.columns.str.strip()
    sg_df.columns = sg_df.columns.str.strip()
    js_df.columns = js_df.columns.str.strip()

    # Flexible column detection for job families
    fam_id_col = next((c for c in fam_df.columns if 'job' in c.lower()), None)
    fam_cluster_col = next((c for c in fam_df.columns if 'cluster' in c.lower() or 'family' in c.lower()), None)
    if not fam_id_col or not fam_cluster_col:
        print(f"ERROR: Cannot find job_id/cluster_id columns in {args.job_families}. "
              f"Columns: {list(fam_df.columns)}", file=sys.stderr)
        sys.exit(1)
    fam_df = fam_df[[fam_id_col, fam_cluster_col]].rename(
        columns={fam_id_col: 'job_id', fam_cluster_col: 'job_family'}
    )
    fam_df['job_id'] = fam_df['job_id'].str.strip()
    fam_df['job_family'] = fam_df['job_family'].str.strip()

    # Flexible column detection for skill groups
    sg_skill_col = next((c for c in sg_df.columns if 'skill' in c.lower()), None)
    sg_group_col = next((c for c in sg_df.columns if 'group' in c.lower()), None)
    if not sg_skill_col or not sg_group_col:
        print(f"ERROR: Cannot find canonical_skill/group_id columns in {args.skill_groups}. "
              f"Columns: {list(sg_df.columns)}", file=sys.stderr)
        sys.exit(1)
    sg_df = sg_df[[sg_skill_col, sg_group_col]].rename(
        columns={sg_skill_col: 'canonical_skill', sg_group_col: 'skill_group'}
    )
    sg_df['canonical_skill'] = sg_df['canonical_skill'].str.strip().str.lower()
    sg_df['skill_group'] = sg_df['skill_group'].str.strip()

    # Flexible column detection for job skills
    js_job_col = next((c for c in js_df.columns if 'job' in c.lower() and 'id' in c.lower()), None)
    js_skill_col = next((c for c in js_df.columns if 'skill' in c.lower()), None)
    if not js_job_col or not js_skill_col:
        print(f"ERROR: Cannot find job_id/skill columns in {args.job_skills}. "
              f"Columns: {list(js_df.columns)}", file=sys.stderr)
        sys.exit(1)
    js_df = js_df[[js_job_col, js_skill_col]].rename(
        columns={js_job_col: 'job_id', js_skill_col: 'skill_name'}
    )
    js_df['job_id'] = js_df['job_id'].str.strip()
    js_df['skill_name'] = js_df['skill_name'].str.strip().str.lower()

    # Merge: job_skills + job_family + skill_group
    merged = (
        js_df
        .merge(fam_df, on='job_id', how='inner')
        .merge(sg_df, left_on='skill_name', right_on='canonical_skill', how='inner')
    )

    # Total posts per family (denominator)
    family_sizes = fam_df.groupby('job_family')['job_id'].nunique().rename('total_posts')

    all_families = sorted(fam_df['job_family'].unique())
    all_groups = sorted(sg_df['skill_group'].unique())

    # Validate denominators are nonzero
    zero_families = family_sizes[family_sizes == 0].index.tolist()
    if zero_families:
        print(f"WARNING: Job families with zero posts: {zero_families}", file=sys.stderr)

    # Build numeric and label matrices
    numeric_rows = []
    label_rows = []

    for family in all_families:
        total = int(family_sizes.get(family, 0))
        if total == 0:
            numeric_rows.append({g: 0.0 for g in all_groups})
            label_rows.append({g: 'Low' for g in all_groups})
            continue

        family_merged = merged[merged['job_family'] == family]
        numeric_row = {}
        label_row = {}
        for group in all_groups:
            posts_with_group = family_merged[family_merged['skill_group'] == group]['job_id'].nunique()
            pct = (posts_with_group / total) * 100.0
            # Validate percentage in [0, 100]
            assert 0.0 <= pct <= 100.0, f"Percentage out of range: {pct} for ({family}, {group})"
            numeric_row[group] = round(pct, 2)
            label_row[group] = apply_label(pct)
        numeric_rows.append(numeric_row)
        label_rows.append(label_row)

    numeric_df = pd.DataFrame(numeric_rows, index=all_families)
    label_df = pd.DataFrame(label_rows, index=all_families)
    numeric_df.index.name = 'job_family'
    label_df.index.name = 'job_family'

    # Save outputs
    numeric_out = os.path.join(args.output_dir, 'competence_matrix_numeric.csv')
    label_out = os.path.join(args.output_dir, 'competence_matrix_labels.csv')
    numeric_df.to_csv(numeric_out)
    label_df.to_csv(label_out)

    print(f"Competence matrix ({len(all_families)}×{len(all_groups)}) saved:")
    print(f"  Numeric: {numeric_out}")
    print(f"  Labels:  {label_out}")
    print("\nMatrix preview (numeric %):")
    print(numeric_df.to_string())


if __name__ == '__main__':
    main()
