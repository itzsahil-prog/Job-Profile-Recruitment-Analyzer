import json
import os
import py_compile
import pandas as pd
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(ROOT_DIR, 'outputs')
VIZ_DIR = os.path.join(ROOT_DIR, 'visualizations')

def test_app_py_compiles():
    app_path = os.path.join(ROOT_DIR, 'app.py')
    assert os.path.isfile(app_path), "app.py does not exist"
    py_compile.compile(app_path, doraise=True)

def test_requirements_file():
    req_path = os.path.join(ROOT_DIR, 'requirements.txt')
    assert os.path.isfile(req_path), "requirements.txt does not exist"
    with open(req_path, 'r') as f:
        content = f.read().lower()
    for pkg in ['streamlit', 'pandas', 'scikit-learn', 'matplotlib']:
        assert pkg in content, f"Missing required dependency {pkg} in requirements.txt"

def test_skill_frequency_output():
    path = os.path.join(OUTPUTS_DIR, 'skill_frequency.csv')
    assert os.path.isfile(path), f"Missing {path}"
    df = pd.read_csv(path)
    assert len(df) >= 30, f"Expected at least 30 skills, got {len(df)}"
    assert 'skill_name' in df.columns or any('skill' in c.lower() for c in df.columns)

def test_clustering_outputs():
    fam_path = os.path.join(OUTPUTS_DIR, 'job_family_assignments.csv')
    assert os.path.isfile(fam_path), f"Missing {fam_path}"
    fam_df = pd.read_csv(fam_path)
    assert 'cluster_id' in fam_df.columns
    assert fam_df['cluster_id'].nunique() == 4

    grp_path = os.path.join(OUTPUTS_DIR, 'skill_group_assignments.csv')
    assert os.path.isfile(grp_path), f"Missing {grp_path}"
    grp_df = pd.read_csv(grp_path)
    col = next((c for c in grp_df.columns if 'cluster' in c.lower() or 'group' in c.lower()))
    assert grp_df[col].nunique() == 9

def test_competence_matrix():
    path = os.path.join(OUTPUTS_DIR, 'competence_matrix_numeric.csv')
    assert os.path.isfile(path), f"Missing {path}"
    df = pd.read_csv(path, index_col=0)
    assert df.shape == (4, 9), f"Expected 4x9 matrix, got {df.shape}"
    for col in df.columns:
        vals = pd.to_numeric(df[col], errors='coerce')
        assert vals.between(0.0, 100.0).all(), f"Values out of range 0..100 in {col}"

def test_visualizations_exist():
    expected_charts = [
        'skill_frequency.png',
        'job_family_sizes.png',
        'skill_group_sizes.png',
        'competence_heatmap.png',
        'elbow_plot.png',
        'data_quality.png'
    ]
    for chart in expected_charts:
        chart_path = os.path.join(VIZ_DIR, chart)
        assert os.path.isfile(chart_path), f"Missing chart {chart}"
        assert os.path.getsize(chart_path) > 1000, f"Chart {chart} is too small / empty"

def test_evaluation_json():
    path = os.path.join(OUTPUTS_DIR, 'cluster_evaluation.json')
    assert os.path.isfile(path), f"Missing {path}"
    with open(path, 'r') as f:
        data = json.load(f)
    assert 'job_families' in data
    assert 'skill_groups' in data
    assert 'silhouette' in data['job_families']
    assert 'silhouette' in data['skill_groups']
