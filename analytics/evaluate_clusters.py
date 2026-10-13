#!/usr/bin/env python3
"""
evaluate_clusters.py — Evaluate clustering quality using elbow method and silhouette scores.

For both job-family and skill-group clustering:
  - Computes inertia (within-cluster sum of squares) for k = 2 through 10
  - Computes silhouette score using the actual cluster assignments (if valid)

Outputs:
    outputs/cluster_evaluation.json

JSON structure:
{
    "job_families": {
        "elbow": [{"k": 2, "inertia": ...}, ...],
        "silhouette": 0.42
    },
    "skill_groups": {
        "elbow": [{"k": 2, "inertia": ...}, ...],
        "silhouette": 0.38
    }
}

Usage:
    python analytics/evaluate_clusters.py \\
        --job-matrix  outputs/job_skill_matrix.csv \\
        --skill-matrix outputs/job_skill_matrix.csv \\
        --job-clusters outputs/job_family_assignments.csv \\
        --skill-clusters outputs/skill_group_assignments.csv

    python analytics/evaluate_clusters.py \\
        --job-matrix  outputs/job_skill_matrix.csv \\
        --skill-matrix outputs/job_skill_matrix.csv \\
        --job-clusters outputs/job_family_assignments.csv \\
        --skill-clusters outputs/skill_group_assignments.csv \\
        --output-dir outputs/
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


RANDOM_STATE = 42
N_INIT = 10
K_RANGE = range(2, 11)


def load_matrix(path, label):
    """
    Load a feature matrix CSV.

    Parameters
    ----------
    path : str
    label : str

    Returns
    -------
    np.ndarray
    """
    if not os.path.isfile(path):
        print(f"ERROR: {label} matrix not found: {path}", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(path, index_col=0)
    return df.values.astype(float), df.index.tolist()


def load_labels(path, label_col_hint, label):
    """
    Load cluster label assignments from CSV.

    Parameters
    ----------
    path : str
    label_col_hint : str
        Substring to identify the label column (e.g. 'cluster', 'group').
    label : str
        Human-readable name for error messages.

    Returns
    -------
    np.ndarray of int labels
    """
    if not os.path.isfile(path):
        print(f"ERROR: {label} assignments not found: {path}", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip()
    label_col = next(
        (c for c in df.columns if label_col_hint.lower() in c.lower()),
        None
    )
    if label_col is None:
        print(f"ERROR: Could not find '{label_col_hint}' column in {path}. "
              f"Columns: {list(df.columns)}", file=sys.stderr)
        sys.exit(1)
    return df[label_col].astype(int).values


def compute_elbow(X, k_range):
    """
    Compute KMeans inertia for each k in k_range.

    Parameters
    ----------
    X : np.ndarray
    k_range : iterable of int

    Returns
    -------
    list of dict  [{"k": k, "inertia": float}, ...]
    """
    elbow_data = []
    for k in k_range:
        if k >= X.shape[0]:
            break
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=N_INIT)
        km.fit(X)
        elbow_data.append({'k': k, 'inertia': round(float(km.inertia_), 4)})
    return elbow_data


def compute_silhouette(X, labels):
    """
    Compute silhouette score if valid (>1 cluster, not all same label).

    Parameters
    ----------
    X : np.ndarray
    labels : np.ndarray

    Returns
    -------
    float or None
    """
    unique = np.unique(labels)
    if len(unique) < 2:
        return None
    if len(unique) == X.shape[0]:
        return None  # Every point in its own cluster — undefined
    try:
        return round(float(silhouette_score(X, labels)), 6)
    except Exception:
        return None


def main():
    """Evaluate job-family and skill-group clustering quality."""
    parser = argparse.ArgumentParser(
        description='Evaluate clustering quality: elbow method + silhouette scores.'
    )
    parser.add_argument(
        '--job-matrix', required=True,
        help='Path to job-by-skill matrix CSV (for job-family elbow curve)'
    )
    parser.add_argument(
        '--skill-matrix', required=True,
        help='Path to job-by-skill matrix CSV (transposed for skill-group elbow curve)'
    )
    parser.add_argument(
        '--job-clusters', required=True,
        help='Path to job family assignments CSV (columns: job_id, cluster_id)'
    )
    parser.add_argument(
        '--skill-clusters', required=True,
        help='Path to skill group assignments CSV (columns: canonical_skill, group_id)'
    )
    parser.add_argument(
        '--output-dir', default='outputs',
        help='Directory to save evaluation output (default: outputs/)'
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Job families — use job-by-skill matrix rows
    print("Computing job family elbow curve...")
    X_jobs, _ = load_matrix(args.job_matrix, 'Job-skill matrix')
    job_elbow = compute_elbow(X_jobs, K_RANGE)
    job_labels = load_labels(args.job_clusters, 'cluster', 'Job family assignments')
    job_sil = compute_silhouette(X_jobs, job_labels)
    print(f"  Job family silhouette: {job_sil}")

    # Skill groups — transpose the matrix so rows = skills
    print("Computing skill group elbow curve...")
    X_skill_jobs, _ = load_matrix(args.skill_matrix, 'Skill matrix (for transposing)')
    X_skills = X_skill_jobs.T  # rows = skills
    skill_elbow = compute_elbow(X_skills, K_RANGE)
    skill_labels = load_labels(args.skill_clusters, 'group', 'Skill group assignments')
    skill_sil = compute_silhouette(X_skills, skill_labels)
    print(f"  Skill group silhouette: {skill_sil}")

    # Build output
    evaluation = {
        'job_families': {
            'elbow': job_elbow,
            'silhouette': job_sil,
        },
        'skill_groups': {
            'elbow': skill_elbow,
            'silhouette': skill_sil,
        },
    }

    out_path = os.path.join(args.output_dir, 'cluster_evaluation.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(evaluation, f, indent=2)

    print(f"Evaluation saved to: {out_path}")


if __name__ == '__main__':
    main()
