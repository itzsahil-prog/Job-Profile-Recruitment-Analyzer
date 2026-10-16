#!/usr/bin/env python3
"""
cluster_job_families.py — K-means clustering of job postings into k=4 job families.

Reads outputs/job_skill_matrix.csv, clusters into k=4 families, assigns labels
based on actual dominant skills.

Outputs:
    outputs/job_family_assignments.csv — columns: job_id, cluster_id
    outputs/job_family_summary.csv     — columns: cluster_id, family_label, size, top_skills
    outputs/job_family_elbow.json      — elbow data (k=2..8) and silhouette score
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

WORKDIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX_CSV    = os.path.join(WORKDIR, 'outputs', 'job_skill_matrix.csv')
ASSIGN_OUT    = os.path.join(WORKDIR, 'outputs', 'job_family_assignments.csv')
SUMMARY_OUT   = os.path.join(WORKDIR, 'outputs', 'job_family_summary.csv')
ELBOW_OUT     = os.path.join(WORKDIR, 'outputs', 'job_family_elbow.json')
RANDOM_STATE  = 42
N_CLUSTERS    = 4
N_INIT        = 10
SAMPLE_N      = 200_000  # max rows; already sampled by build_vectors

def assign_family_label(top_skills_str):
    """Assign a human-readable label based on top skill names."""
    skills_lower = top_skills_str.lower()
    if any(s in skills_lower for s in ['python', 'machine learning', 'tensorflow', 'pytorch', 'deep learning', 'nlp', 'scikit']):
        return 'Data Science & ML'
    elif any(s in skills_lower for s in ['java', 'spring', 'node', 'react', 'angular', 'javascript', 'typescript', 'backend', 'frontend', 'web']):
        return 'Software Engineering'
    elif any(s in skills_lower for s in ['sql', 'tableau', 'power bi', 'excel', 'reporting', 'bi ', 'analytics', 'business']):
        return 'Data Analytics & BI'
    elif any(s in skills_lower for s in ['hadoop', 'spark', 'kafka', 'hive', 'hdfs', 'big data', 'etl', 'pipeline', 'airflow']):
        return 'Big Data Engineering'
    elif any(s in skills_lower for s in ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'devops', 'terraform', 'cloud']):
        return 'Cloud & DevOps'
    elif any(s in skills_lower for s in ['project management', 'agile', 'scrum', 'leadership', 'communication', 'stakeholder']):
        return 'Management & Consulting'
    else:
        return 'General Technology'

def main():
    start = time.time()
    print(f"[cluster_job_families] Reading {MATRIX_CSV}")

    if not os.path.isfile(MATRIX_CSV):
        print(f"ERROR: {MATRIX_CSV} not found.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(MATRIX_CSV, index_col=0)
    df.index = df.index.astype(str)
    print(f"Matrix loaded: {df.shape} ({df.shape[0]} jobs x {df.shape[1]} skills)")

    # Drop zero-variance columns
    var = df.var(axis=0)
    df = df[var[var > 0].index]
    print(f"After variance filter: {df.shape}")

    X = df.values.astype(float)
    job_ids = df.index.tolist()
    feature_names = df.columns.tolist()

    # Run KMeans k=4
    print(f"Running KMeans(k={N_CLUSTERS}, random_state={RANDOM_STATE}, n_init={N_INIT})...")
    km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=N_INIT)
    labels = km.fit_predict(X)
    print(f"Inertia: {km.inertia_:.2f}")

    # Silhouette (sample 10k for speed)
    if len(set(labels)) > 1:
        idx = np.random.RandomState(42).choice(len(X), size=min(10000, len(X)), replace=False)
        sil = silhouette_score(X[idx], labels[idx])
        print(f"Silhouette score (10k sample): {sil:.4f}")
    else:
        sil = None
        print("Silhouette: N/A")

    # Save assignments
    pd.DataFrame({'job_id': job_ids, 'cluster_id': labels}).to_csv(ASSIGN_OUT, index=False)
    print(f"Assignments saved: {ASSIGN_OUT}")

    # Elbow data k=2..8
    print("Computing elbow data (k=2..8)...")
    elbow = []
    for k in range(2, 9):
        km_k = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=N_INIT)
        km_k.fit(X)
        elbow.append({'k': k, 'inertia': float(km_k.inertia_)})
        print(f"  k={k}: inertia={km_k.inertia_:.2f}")

    elbow_data = {
        'elbow': elbow,
        'silhouette': float(sil) if sil is not None else None,
        'chosen_k': N_CLUSTERS,
    }
    with open(ELBOW_OUT, 'w', encoding='utf-8') as f:
        json.dump(elbow_data, f, indent=2)
    print(f"Elbow data saved: {ELBOW_OUT}")

    # Build summary
    assignments_df = pd.DataFrame({'job_id': job_ids, 'cluster_id': labels})
    cluster_sizes = assignments_df['cluster_id'].value_counts().sort_index()

    summary_rows = []
    print("\nCluster summary:")
    for cid in range(N_CLUSTERS):
        center = km.cluster_centers_[cid]
        top_idx = np.argsort(center)[::-1][:5]
        top_skills_str = '|'.join(feature_names[i] for i in top_idx)
        label = assign_family_label(top_skills_str)
        sz = int(cluster_sizes.get(cid, 0))
        summary_rows.append({
            'cluster_id': cid,
            'family_label': label,
            'size': sz,
            'top_skills': top_skills_str,
        })
        print(f"  Cluster {cid}: label={label}, size={sz}, top_skills={top_skills_str}")

    pd.DataFrame(summary_rows).to_csv(SUMMARY_OUT, index=False)
    print(f"Summary saved: {SUMMARY_OUT}")

    elapsed = time.time() - start
    print(f"\ncluster_job_families complete in {elapsed:.1f}s")

if __name__ == '__main__':
    main()
