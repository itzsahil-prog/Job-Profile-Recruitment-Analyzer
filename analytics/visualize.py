#!/usr/bin/env python3
"""
visualize.py — Generate all project visualizations from pipeline outputs.

Reads actual output files from the outputs/ directory and produces exactly
six charts in the visualizations/ directory. Fails clearly with a
FileNotFoundError message if any required input file is missing — does NOT
produce blank or placeholder charts.

Charts produced:
    1. visualizations/skill_frequency.png
       Horizontal bar chart, top 20 skills by distinct post count.
       Source: outputs/skill_frequency.csv

    2. visualizations/job_family_sizes.png
       Bar chart of job family cluster sizes.
       Source: outputs/job_family_summary.csv

    3. visualizations/skill_group_sizes.png
       Bar chart of skill group sizes.
       Source: outputs/skill_group_summary.csv

    4. visualizations/competence_heatmap.png
       4×9 heatmap with percentage annotations.
       Source: outputs/competence_matrix_numeric.csv

    5. visualizations/elbow_plot.png
       Elbow curves (inertia vs k) for both clusterings on the same axes.
       Source: outputs/cluster_evaluation.json

    6. visualizations/data_quality.png
       Bar chart: retained vs rejected records.
       Source: outputs/data_quality_report.json

Usage:
    python analytics/visualize.py
    python analytics/visualize.py --outputs-dir outputs/ --vis-dir visualizations/
"""

import argparse
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')  # non-interactive backend for server/CI use
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns


def require_file(path):
    """
    Exit with a clear error message if path does not exist.

    Parameters
    ----------
    path : str
    """
    if not os.path.isfile(path):
        print(
            f"ERROR: Required output file not found: {path}\n"
            f"Run the pipeline steps that produce this file before running visualize.py.",
            file=sys.stderr,
        )
        sys.exit(1)


def save_and_close(fig, path):
    """Save figure to path and close it to free memory."""
    fig.savefig(path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"  Saved: {path}")


def plot_skill_frequency(outputs_dir, vis_dir):
    """
    Chart 1: Top 20 skills by distinct post count (horizontal bar chart).

    Parameters
    ----------
    outputs_dir : str
    vis_dir : str
    """
    path = os.path.join(outputs_dir, 'skill_frequency.csv')
    require_file(path)

    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip()

    # Flexible column detection
    skill_col = next((c for c in df.columns if 'skill' in c.lower()), None)
    count_col = next((c for c in df.columns if 'count' in c.lower() or 'posts' in c.lower()), None)
    if not skill_col or not count_col:
        print(f"ERROR: Cannot find skill/count columns in {path}. Columns: {list(df.columns)}", file=sys.stderr)
        sys.exit(1)

    df[count_col] = pd.to_numeric(df[count_col], errors='coerce')
    df = df.dropna(subset=[count_col]).sort_values(count_col, ascending=False).head(20)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(df[skill_col].iloc[::-1], df[count_col].iloc[::-1], color='steelblue')
    ax.set_xlabel('Number of Job Postings', fontsize=11)
    ax.set_ylabel('Skill', fontsize=11)
    ax.set_title('Top 20 Skills by Job Posting Frequency', fontsize=13, fontweight='bold')
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.text(0.99, 0.01, f'Source: {path}', ha='right', fontsize=7, color='gray')

    save_and_close(fig, os.path.join(vis_dir, 'skill_frequency.png'))


def plot_job_family_sizes(outputs_dir, vis_dir):
    """
    Chart 2: Bar chart of job family cluster sizes.

    Parameters
    ----------
    outputs_dir : str
    vis_dir : str
    """
    path = os.path.join(outputs_dir, 'job_family_summary.csv')
    require_file(path)

    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip()

    cluster_col = next((c for c in df.columns if 'cluster' in c.lower() or 'family' in c.lower()), None)
    size_col = next((c for c in df.columns if 'size' in c.lower()), None)
    if not cluster_col or not size_col:
        print(f"ERROR: Cannot find cluster/size columns in {path}. Columns: {list(df.columns)}", file=sys.stderr)
        sys.exit(1)

    df[size_col] = pd.to_numeric(df[size_col], errors='coerce')
    df = df.dropna(subset=[size_col])
    labels = [f"Family {v}" for v in df[cluster_col]]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, df[size_col], color='teal')
    ax.bar_label(bars, fmt='%d', padding=3)
    ax.set_xlabel('Job Family Cluster', fontsize=11)
    ax.set_ylabel('Number of Job Postings', fontsize=11)
    ax.set_title('Job Family Cluster Sizes (k=4)', fontsize=13, fontweight='bold')
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.text(0.99, 0.01, f'Source: {path}', ha='right', fontsize=7, color='gray')

    save_and_close(fig, os.path.join(vis_dir, 'job_family_sizes.png'))


def plot_skill_group_sizes(outputs_dir, vis_dir):
    """
    Chart 3: Bar chart of skill group sizes.

    Parameters
    ----------
    outputs_dir : str
    vis_dir : str
    """
    path = os.path.join(outputs_dir, 'skill_group_summary.csv')
    require_file(path)

    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip()

    group_col = next((c for c in df.columns if 'group' in c.lower()), None)
    # size may be stored as count of member_skills pipe-separated, or explicit 'size' col
    size_col = next((c for c in df.columns if 'size' in c.lower()), None)
    member_col = next((c for c in df.columns if 'member' in c.lower()), None)

    if not group_col:
        print(f"ERROR: Cannot find group column in {path}. Columns: {list(df.columns)}", file=sys.stderr)
        sys.exit(1)

    if size_col:
        df[size_col] = pd.to_numeric(df[size_col], errors='coerce')
        df = df.dropna(subset=[size_col])
        sizes = df[size_col]
    elif member_col:
        # Derive size from pipe-separated member_skills
        df['_size'] = df[member_col].fillna('').apply(lambda x: len([s for s in x.split('|') if s.strip()]))
        sizes = df['_size']
        size_col = '_size'
    else:
        print(f"ERROR: Cannot find size/member columns in {path}. Columns: {list(df.columns)}", file=sys.stderr)
        sys.exit(1)

    labels = [f"Group {v}" for v in df[group_col]]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, sizes, color='darkorange')
    ax.bar_label(bars, fmt='%d', padding=3)
    ax.set_xlabel('Skill Group', fontsize=11)
    ax.set_ylabel('Number of Skills', fontsize=11)
    ax.set_title('Skill Group Sizes (k=9)', fontsize=13, fontweight='bold')
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    plt.xticks(rotation=15)
    fig.text(0.99, 0.01, f'Source: {path}', ha='right', fontsize=7, color='gray')

    save_and_close(fig, os.path.join(vis_dir, 'skill_group_sizes.png'))


def plot_competence_heatmap(outputs_dir, vis_dir):
    """
    Chart 4: 4×9 competence heatmap with percentage annotations.

    Parameters
    ----------
    outputs_dir : str
    vis_dir : str
    """
    path = os.path.join(outputs_dir, 'competence_matrix_numeric.csv')
    require_file(path)

    df = pd.read_csv(path, index_col=0)
    df.index = [f"Family {v}" for v in df.index]
    df.columns = [f"Group {v}" for v in df.columns]

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(
        df.astype(float),
        ax=ax,
        annot=True,
        fmt='.1f',
        cmap='YlOrRd',
        linewidths=0.5,
        cbar_kws={'label': 'Prevalence (%)'},
        vmin=0,
        vmax=100,
    )
    ax.set_title('Job Family × Skill Group Competence Matrix (% postings)', fontsize=13, fontweight='bold')
    ax.set_xlabel('Skill Group', fontsize=11)
    ax.set_ylabel('Job Family', fontsize=11)
    plt.xticks(rotation=30, ha='right')
    plt.yticks(rotation=0)
    fig.text(0.99, 0.01, f'Source: {path}', ha='right', fontsize=7, color='gray')

    save_and_close(fig, os.path.join(vis_dir, 'competence_heatmap.png'))


def plot_elbow(outputs_dir, vis_dir):
    """
    Chart 5: Elbow curves for both clusterings on the same axes.

    Parameters
    ----------
    outputs_dir : str
    vis_dir : str
    """
    jf_path = os.path.join(outputs_dir, 'job_family_elbow.json')
    sg_path = os.path.join(outputs_dir, 'skill_group_elbow.json')
    require_file(jf_path)
    require_file(sg_path)

    with open(jf_path, encoding='utf-8') as f:
        jf_data = json.load(f)
    with open(sg_path, encoding='utf-8') as f:
        sg_data = json.load(f)

    fig, ax = plt.subplots(figsize=(8, 5))

    jf_elbow = jf_data.get('elbow', [])
    if jf_elbow:
        ks = [e['k'] for e in jf_elbow]
        inertias = [e['inertia'] for e in jf_elbow]
        ax.plot(ks, inertias, marker='o', color='steelblue', label='Job Families (jobs)')

    sg_elbow = sg_data.get('elbow', [])
    if sg_elbow:
        ks = [e['k'] for e in sg_elbow]
        inertias = [e['inertia'] for e in sg_elbow]
        ax.plot(ks, inertias, marker='s', color='darkorange', label='Skill Groups (skills)')

    ax.set_xlabel('Number of Clusters (k)', fontsize=11)
    ax.set_ylabel('Inertia (within-cluster sum of squares)', fontsize=11)
    ax.set_title('Elbow Method — Optimal k Selection', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.text(0.99, 0.01, f'Source: job_family_elbow.json + skill_group_elbow.json', ha='right', fontsize=7, color='gray')
    fig.tight_layout()

    save_and_close(fig, os.path.join(vis_dir, 'elbow_plot.png'))


def plot_data_quality(outputs_dir, vis_dir):
    """
    Chart 6: Bar chart showing retained vs rejected records from data quality report.

    Parameters
    ----------
    outputs_dir : str
    vis_dir : str
    """
    path = os.path.join(outputs_dir, 'data_quality_report.json')
    require_file(path)

    with open(path, encoding='utf-8') as f:
        report = json.load(f)

    retained = report.get('rows_retained', 0)
    rejected = report.get('rejected_rows', 0) + report.get('duplicate_rows', 0)
    total = report.get('total_rows_raw', retained + rejected)

    categories = ['Total (raw)', 'Retained', 'Rejected / Duplicates']
    values = [total, retained, rejected]
    colors = ['steelblue', 'green', 'crimson']

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(categories, values, color=colors)
    ax.bar_label(bars, fmt='%d', padding=3)
    ax.set_ylabel('Number of Records', fontsize=11)
    ax.set_title('Data Quality — Record Counts After Validation', fontsize=13, fontweight='bold')
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.text(0.99, 0.01, f'Source: {path}', ha='right', fontsize=7, color='gray')

    save_and_close(fig, os.path.join(vis_dir, 'data_quality.png'))


def main():
    """Parse arguments and generate all six visualizations."""
    parser = argparse.ArgumentParser(
        description='Generate all project visualizations from pipeline outputs.'
    )
    parser.add_argument(
        '--outputs-dir', default='outputs',
        help='Directory containing pipeline output files (default: outputs/)'
    )
    parser.add_argument(
        '--vis-dir', default='visualizations',
        help='Directory to save visualization PNGs (default: visualizations/)'
    )
    args = parser.parse_args()

    os.makedirs(args.vis_dir, exist_ok=True)

    print("Generating visualizations...")
    plot_skill_frequency(args.outputs_dir, args.vis_dir)
    plot_job_family_sizes(args.outputs_dir, args.vis_dir)
    plot_skill_group_sizes(args.outputs_dir, args.vis_dir)
    plot_competence_heatmap(args.outputs_dir, args.vis_dir)
    plot_elbow(args.outputs_dir, args.vis_dir)
    plot_data_quality(args.outputs_dir, args.vis_dir)

    print("\nAll 6 charts saved successfully.")


if __name__ == '__main__':
    main()
