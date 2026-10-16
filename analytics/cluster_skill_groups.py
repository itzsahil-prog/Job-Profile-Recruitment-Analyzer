#!/usr/bin/env python3
"""
cluster_skill_groups.py — K-means clustering of skills into k=9 groups.

Reads outputs/job_skill_matrix.csv, transposes to skill-by-job vectors,
clusters skills into k=9 groups.

Outputs:
    outputs/skill_group_assignments.csv — columns: skill_name, group_id, group_label
    outputs/skill_group_summary.csv     — columns: group_id, group_label, member_skills
    outputs/skill_group_elbow.json      — elbow data (k=2..12) and silhouette score
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
ASSIGN_OUT    = os.path.join(WORKDIR, 'outputs', 'skill_group_assignments.csv')
SUMMARY_OUT   = os.path.join(WORKDIR, 'outputs', 'skill_group_summary.csv')
ELBOW_OUT     = os.path.join(WORKDIR, 'outputs', 'skill_group_elbow.json')
RANDOM_STATE  = 42
N_CLUSTERS    = 9
N_INIT        = 10

GROUP_LABEL_HINTS = [
    (['python', 'r ', 'julia', 'scala', 'perl'], 'Scripting Languages'),
    (['java', 'c++', 'c#', '.net', 'go ', 'rust', 'swift', 'kotlin'], 'Compiled & OOP Languages'),
    (['sql', 'mysql', 'postgresql', 'oracle', 'nosql', 'mongodb', 'redis', 'cassandra', 'database'], 'Databases & Storage'),
    (['hadoop', 'spark', 'hive', 'pig', 'kafka', 'hdfs', 'flink', 'storm', 'big data', 'mapreduce'], 'Big Data Platforms'),
    (['tensorflow', 'pytorch', 'keras', 'scikit', 'machine learning', 'deep learning', 'nlp', 'ai ', 'neural', 'xgboost', 'regression'], 'ML & AI'),
    (['aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes', 'terraform', 'devops', 'ci/cd', 'jenkins', 'ansible'], 'Cloud & DevOps'),
    (['tableau', 'power bi', 'qlik', 'looker', 'excel', 'reporting', 'dashboard', 'bi ', 'analytics', 'visualization'], 'BI & Visualization'),
    (['javascript', 'typescript', 'react', 'angular', 'vue', 'node', 'html', 'css', 'frontend', 'backend', 'rest', 'api', 'web'], 'Web & App Development'),
    (['agile', 'scrum', 'jira', 'project management', 'communication', 'leadership', 'stakeholder', 'excel', 'powerpoint'], 'Soft Skills & Management'),
]

def assign_group_label(skills_list):
    """Assign label by majority vote among top skills."""
    text = ' '.join(skills_list).lower()
    scores = {}
    for hints, label in GROUP_LABEL_HINTS:
        score = sum(1 for h in hints if h in text)
        if score > 0:
            scores[label] = score
    if scores:
        return max(scores, key=scores.get)
    return 'General Technology'

def main():
    start = time.time()
    print(f"[cluster_skill_groups] Reading {MATRIX_CSV}")

    if not os.path.isfile(MATRIX_CSV):
        print(f"ERROR: {MATRIX_CSV} not found.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(MATRIX_CSV, index_col=0)
    df.index = df.index.astype(str)
    print(f"Matrix loaded: {df.shape} ({df.shape[0]} jobs x {df.shape[1]} skills)")

    # Transpose: rows=skills, cols=jobs
    skill_df = df.T
    skill_names = skill_df.index.tolist()
    print(f"Transposed: {skill_df.shape} ({len(skill_names)} skills x {skill_df.shape[1]} jobs)")

    if len(skill_names) < N_CLUSTERS:
        print(f"ERROR: Only {len(skill_names)} skills, need at least {N_CLUSTERS}", file=sys.stderr)
        sys.exit(1)

    X = skill_df.values.astype(float)

    # Run KMeans k=9
    print(f"Running KMeans(k={N_CLUSTERS}, random_state={RANDOM_STATE}, n_init={N_INIT})...")
    km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=N_INIT)
    labels = km.fit_predict(X)
    print(f"Inertia: {km.inertia_:.2f}")

    # Silhouette
    if len(set(labels)) > 1:
        sil = silhouette_score(X, labels)
        print(f"Silhouette score: {sil:.4f}")
    else:
        sil = None

    # Build assignments with group_label
    group_labels = []
    for i, skill in enumerate(skill_names):
        group_labels.append(None)  # fill below

    # First get member skills per group for labeling
    group_members = {}
    for gid in range(N_CLUSTERS):
        members = [skill_names[i] for i, l in enumerate(labels) if l == gid]
        group_members[gid] = members

    # Assign labels
    gid_to_label = {}
    for gid, members in group_members.items():
        lbl = assign_group_label(members[:20])
        gid_to_label[gid] = lbl

    # Build assignments df
    assign_df = pd.DataFrame({
        'skill_name': skill_names,
        'group_id': labels,
        'group_label': [gid_to_label[l] for l in labels],
    })
    assign_df.to_csv(ASSIGN_OUT, index=False)
    print(f"Assignments saved: {ASSIGN_OUT}")

    # Build summary
    summary_rows = []
    print("\nGroup summary:")
    for gid in range(N_CLUSTERS):
        members = group_members[gid]
        lbl = gid_to_label[gid]
        summary_rows.append({
            'group_id': gid,
            'group_label': lbl,
            'member_skills': '|'.join(members),
        })
        print(f"  Group {gid}: label={lbl}, size={len(members)}, sample={members[:5]}")
    pd.DataFrame(summary_rows).to_csv(SUMMARY_OUT, index=False)
    print(f"Summary saved: {SUMMARY_OUT}")

    # Elbow data k=2..12
    print("Computing elbow data (k=2..12)...")
    elbow = []
    for k in range(2, 13):
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

    elapsed = time.time() - start
    print(f"\ncluster_skill_groups complete in {elapsed:.1f}s")

if __name__ == '__main__':
    main()
