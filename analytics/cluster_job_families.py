#!/usr/bin/env python3
"""
cluster_job_families.py — K-means clustering of job postings into k=4 job families.

Reads the binary job-by-skill matrix produced by build_vectors.py and assigns
each job posting to one of k=4 clusters (job families) using scikit-learn KMeans.

Parameters:
    k = 4 (configurable via --k)
    random_state = 42 (fixed for reproducibility)
    n_init = 10

Outputs:
    outputs/job_family_assignments.csv  — columns: job_id, cluster_id
    outputs/job_family_summary.csv      — columns: cluster_id, size, top_skills

Usage:
    python analytics/cluster_job_families.py --matrix outputs/job_skill_matrix.csv
    python analytics/cluster_job_families.py --matrix outputs/job_skill_matrix.csv \\
        --k 4 --output-dir outputs/
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


RANDOM_STATE = 42
DEFAULT_K = 4
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


def validate_matrix(df, k):
    """
    Validate that the matrix is large enough and non-degenerate.

    Removes zero-variance columns (skills that are always 0 or always 1),
    then checks that at least k*2 rows remain.

    Parameters
    ----------
    df : pd.DataFrame
    k : int

    Returns
    -------
    pd.DataFrame
        Cleaned matrix with non-degenerate columns only.
    """
    # Drop zero-variance columns
    variance = df.var(axis=0)
    nonzero_var_cols = variance[variance > 0].index.tolist()
    if len(nonzero_var_cols) == 0:
        print("ERROR: All feature columns have zero variance. Cannot cluster.", file=sys.stderr)
        sys.exit(1)
    df_clean = df[nonzero_var_cols]

    if len(df_clean) < k * 2:
        print(
            f"ERROR: Not enough records ({len(df_clean)}) to form {k} clusters. "
            f"Need at least {k * 2} rows.",
            file=sys.stderr,
        )
        sys.exit(1)

    return df_clean


def get_top_skills(cluster_centers, feature_names, top_n=5):
    """
    Return the top-n skill names for each cluster center.

    Parameters
    ----------
    cluster_centers : np.ndarray  shape (k, n_features)
    feature_names : list of str
    top_n : int

    Returns
    -------
    list of str
        One string per cluster with top skill names joined by '|'.
    """
    result = []
    for center in cluster_centers:
        indices = np.argsort(center)[::-1][:top_n]
        top = [feature_names[i] for i in indices]
        result.append('|'.join(top))
    return result


def main():
    """Parse arguments, run k-means on job postings, and save results."""
    parser = argparse.ArgumentParser(
        description='Cluster job postings into k job families using K-means.'
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
        help=f'Number of job family clusters (default: {DEFAULT_K})'
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Load and validate
    df = load_matrix(args.matrix)
    df = validate_matrix(df, args.k)

    print(f"Matrix shape: {df.shape} ({df.shape[0]} jobs, {df.shape[1]} skills)")

    X = df.values.astype(float)
    job_ids = df.index.tolist()
    feature_names = df.columns.tolist()

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
    assignments_df = pd.DataFrame({'job_id': job_ids, 'cluster_id': labels})
    assignments_out = os.path.join(args.output_dir, 'job_family_assignments.csv')
    assignments_df.to_csv(assignments_out, index=False)
    print(f"Assignments saved to: {assignments_out}")

    # Build summary
    top_skills_list = get_top_skills(km.cluster_centers_, feature_names)
    cluster_sizes = assignments_df['cluster_id'].value_counts().sort_index()

    summary_rows = []
    for cid in range(args.k):
        summary_rows.append({
            'cluster_id': cid,
            'size': int(cluster_sizes.get(cid, 0)),
            'top_skills': top_skills_list[cid],
        })
    summary_df = pd.DataFrame(summary_rows)
    summary_out = os.path.join(args.output_dir, 'job_family_summary.csv')
    summary_df.to_csv(summary_out, index=False)
    print(f"Summary saved to: {summary_out}")


if __name__ == '__main__':
    main()
