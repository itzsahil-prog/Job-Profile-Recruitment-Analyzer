#!/usr/bin/env python3
"""
cluster_skill_groups.py — K-means clustering of skills into k=9 groups.

Reads the binary job-by-skill matrix produced by build_vectors.py, transposes it
to obtain a skill-by-job co-occurrence matrix, and clusters skills into k=9 groups
using scikit-learn KMeans.

Parameters:
    k = 9 (configurable via --k)
    random_state = 42 (fixed for reproducibility)
    n_init = 10

Outputs:
    outputs/skill_group_assignments.csv — columns: canonical_skill, group_id
    outputs/skill_group_summary.csv     — columns: group_id, size, top_skills

Usage:
    python analytics/cluster_skill_groups.py --matrix outputs/job_skill_matrix.csv
    python analytics/cluster_skill_groups.py --matrix outputs/job_skill_matrix.csv \\
        --k 9 --output-dir outputs/
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


RANDOM_STATE = 42
DEFAULT_K = 9
DEFAULT_N_INIT = 10


def load_matrix(path):
    """
    Load the job-by-skill binary matrix from CSV.

    Parameters
    ----------
    path : str

    Returns
    -------
    pd.DataFrame
        Index = job_id, columns = skill names.
    """
    if not os.path.isfile(path):
        print(f"ERROR: Matrix file not found: {path}", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(path, index_col=0)
    df.index = df.index.astype(str)
    return df


def main():
    """Parse arguments, run k-means on skills, and save results."""
    parser = argparse.ArgumentParser(
        description='Cluster skills into k groups based on job co-occurrence using K-means.'
    )
    parser.add_argument(
        '--matrix', required=True,
        help='Path to job-by-skill binary matrix CSV (from build_vectors.py)'
    )
    parser.add_argument(
        '--output-dir', default='outputs',
        help='Directory to save output files (default: outputs/)'
    )
    parser.add_argument(
        '--k', type=int, default=DEFAULT_K,
        help=f'Number of skill groups (default: {DEFAULT_K})'
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Load matrix
    df = load_matrix(args.matrix)
    print(f"Matrix loaded: {df.shape} ({df.shape[0]} jobs, {df.shape[1]} skills)")

    # Transpose to skill-by-job matrix
    skill_df = df.T  # rows = skills, cols = jobs
    skill_names = skill_df.index.tolist()

    if len(skill_names) < args.k:
        print(
            f"ERROR: Not enough distinct skills ({len(skill_names)}) to form "
            f"{args.k} groups.",
            file=sys.stderr,
        )
        sys.exit(1)

    X = skill_df.values.astype(float)

    # Run KMeans
    km = KMeans(n_clusters=args.k, random_state=RANDOM_STATE, n_init=DEFAULT_N_INIT)
    labels = km.fit_predict(X)

    print(f"Inertia: {km.inertia_:.2f}")

    if len(set(labels)) > 1:
        sil = silhouette_score(X, labels)
        print(f"Silhouette score: {sil:.4f}")
    else:
        print("Silhouette score: N/A (only one cluster found)")

    # Build assignments
    assignments_df = pd.DataFrame({
        'canonical_skill': skill_names,
        'group_id': labels,
    })
    assignments_out = os.path.join(args.output_dir, 'skill_group_assignments.csv')
    assignments_df.to_csv(assignments_out, index=False)
    print(f"Assignments saved to: {assignments_out}")

    # Build summary: for each group, list its skills
    summary_rows = []
    for gid in range(args.k):
        group_skills = assignments_df.loc[assignments_df['group_id'] == gid, 'canonical_skill'].tolist()
        summary_rows.append({
            'group_id': gid,
            'size': len(group_skills),
            'top_skills': '|'.join(group_skills[:10]),  # first 10 as representative
        })
    summary_df = pd.DataFrame(summary_rows)
    summary_out = os.path.join(args.output_dir, 'skill_group_summary.csv')
    summary_df.to_csv(summary_out, index=False)
    print(f"Summary saved to: {summary_out}")


if __name__ == '__main__':
    main()
