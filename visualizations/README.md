# visualizations/ — Generated Charts

This directory contains all PNG charts produced by `analytics/visualize.py`.
PNG files are git-ignored (see `.gitignore`).

## Charts Generated

| File | Description | Source File |
|------|-------------|------------|
| `skill_frequency.png` | Horizontal bar chart — top 20 skills by distinct post count | `outputs/skill_frequency.csv` |
| `job_family_sizes.png` | Bar chart — number of job postings per job family cluster | `outputs/job_family_summary.csv` |
| `skill_group_sizes.png` | Bar chart — number of skills per skill group | `outputs/skill_group_summary.csv` |
| `competence_heatmap.png` | Heatmap — 4×9 job family × skill group competence matrix with % annotations | `outputs/competence_matrix_numeric.csv` |
| `elbow_plot.png` | Line chart — inertia vs k for both job-family and skill-group clustering | `outputs/cluster_evaluation.json` |
| `data_quality.png` | Bar chart — total, retained, and rejected record counts | `outputs/data_quality_report.json` |

## How to Regenerate

```bash
python analytics/visualize.py
```

All required output files must exist before running the visualization script.
The script fails clearly if any required input file is missing.

## Chart Specifications

- All charts include: title, axis labels with units, and a source file footnote
- Resolution: 150 DPI
- Backend: matplotlib Agg (non-interactive, suitable for server/CI environments)
- Color palette: steelblue for primary series, seaborn default for heatmaps
