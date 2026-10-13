"""
test_validate_dataset.py — Unit tests for analytics/validate_dataset.py

All test data in this file is SYNTHETIC and created solely for testing purposes.
It does NOT represent real job postings or real persons.

All synthetic records use:
  - job_id like "TEST_001"
  - job_title like "Test Engineer"
  - company "Test Corp"
  - location "Test City, TC"
  - Other fields similarly anonymized
"""

import csv
import json
import os
import sys
import tempfile

import pytest

# Make analytics/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analytics'))

from validate_dataset import validate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SYNTHETIC_FIELDNAMES = [
    'job_id', 'job_title', 'company', 'location',
    'salary_range', 'experience_required', 'skills_required',
    'description', 'post_date',
]


def write_csv(rows, fieldnames=None):
    """
    Write synthetic rows to a temporary CSV file and return its path.

    Parameters
    ----------
    rows : list of dict
    fieldnames : list of str or None (uses SYNTHETIC_FIELDNAMES if None)

    Returns
    -------
    str  path to the temporary file
    """
    if fieldnames is None:
        fieldnames = SYNTHETIC_FIELDNAMES
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.csv', delete=False, encoding='utf-8', newline=''
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
        return f.name


def make_report_path():
    """Return a temporary path for the JSON output report."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        return f.name


# ---------------------------------------------------------------------------
# Synthetic row factory
# ---------------------------------------------------------------------------

def synthetic_row(job_id, job_title='Test Engineer', company='Test Corp',
                  location='Test City, TC', salary_range='50000-70000',
                  experience_required='2-4 years', skills_required='Python,SQL',
                  description='This is a synthetic test job description.',
                  post_date='2026-01-01'):
    return {
        'job_id': job_id,
        'job_title': job_title,
        'company': company,
        'location': location,
        'salary_range': salary_range,
        'experience_required': experience_required,
        'skills_required': skills_required,
        'description': description,
        'post_date': post_date,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_basic_valid_csv():
    """TP-VAL-001: Five synthetic rows, all fields present — raw count should be 5."""
    rows = [synthetic_row(f'TEST_{i:03d}') for i in range(1, 6)]
    csv_path = write_csv(rows)
    report_path = make_report_path()
    try:
        report = validate(csv_path, report_path)
        assert report['total_rows_raw'] == 5, (
            f"Expected total_rows_raw=5, got {report['total_rows_raw']}"
        )
    finally:
        os.unlink(csv_path)
        if os.path.exists(report_path):
            os.unlink(report_path)


def test_quoted_commas():
    """TP-VAL-002: Description field contains commas inside quotes — row count stays correct."""
    rows = [
        synthetic_row(
            'TEST_001',
            description='Works with Python, Java, and SQL frameworks, including Spark.'
        ),
        synthetic_row('TEST_002'),
        synthetic_row('TEST_003'),
    ]
    csv_path = write_csv(rows)
    report_path = make_report_path()
    try:
        report = validate(csv_path, report_path)
        assert report['total_rows_raw'] == 3, (
            f"Expected 3 rows (quoted commas should not split rows), got {report['total_rows_raw']}"
        )
    finally:
        os.unlink(csv_path)
        if os.path.exists(report_path):
            os.unlink(report_path)


def test_duplicate_job_ids():
    """TP-VAL-003: Two rows share job_id TEST_001 — rows_after_dedup should be 2."""
    rows = [
        synthetic_row('TEST_001', job_title='Data Engineer'),
        synthetic_row('TEST_001', job_title='Senior Data Engineer'),  # duplicate
        synthetic_row('TEST_002'),
    ]
    csv_path = write_csv(rows)
    report_path = make_report_path()
    try:
        report = validate(csv_path, report_path)
        assert report['rows_after_dedup'] == 2, (
            f"Expected rows_after_dedup=2 after removing duplicate job_id, "
            f"got {report['rows_after_dedup']}"
        )
        assert report['duplicate_rows'] == 1, (
            f"Expected duplicate_rows=1, got {report['duplicate_rows']}"
        )
    finally:
        os.unlink(csv_path)
        if os.path.exists(report_path):
            os.unlink(report_path)


def test_missing_fields():
    """TP-VAL-004: Some rows have missing job_title — missing_values count should be > 0."""
    rows = [
        synthetic_row('TEST_001'),
        synthetic_row('TEST_002', job_title=''),    # missing job_title
        synthetic_row('TEST_003', job_title=''),    # missing job_title
        synthetic_row('TEST_004'),
        synthetic_row('TEST_005'),
    ]
    csv_path = write_csv(rows)
    report_path = make_report_path()
    try:
        report = validate(csv_path, report_path)
        total_missing = sum(report['missing_values'].values())
        assert total_missing > 0, (
            f"Expected some missing values, but missing_values sum is 0: {report['missing_values']}"
        )
    finally:
        os.unlink(csv_path)
        if os.path.exists(report_path):
            os.unlink(report_path)


def test_unicode_text():
    """TP-VAL-005: Description with unicode characters — no crash and row_count correct."""
    rows = [
        synthetic_row('TEST_001', description='Données de travail avec Python et Java.'),
        synthetic_row('TEST_002', description='Analyse des données en temps réel.'),
        synthetic_row('TEST_003', description='Machine learning and 自然言語処理 NLP.'),
    ]
    csv_path = write_csv(rows)
    report_path = make_report_path()
    try:
        report = validate(csv_path, report_path)
        assert report['total_rows_raw'] == 3, (
            f"Expected 3 rows despite unicode content, got {report['total_rows_raw']}"
        )
    finally:
        os.unlink(csv_path)
        if os.path.exists(report_path):
            os.unlink(report_path)


def test_output_json_structure():
    """TP-VAL-006: Output JSON contains all required keys."""
    required_keys = [
        'source_path',
        'total_rows_raw',
        'columns',
        'missing_values',
        'rows_retained',
    ]
    rows = [synthetic_row(f'TEST_{i:03d}') for i in range(1, 4)]
    csv_path = write_csv(rows)
    report_path = make_report_path()
    try:
        report = validate(csv_path, report_path)
        for key in required_keys:
            assert key in report, f"Required key '{key}' missing from report. Keys: {list(report.keys())}"
    finally:
        os.unlink(csv_path)
        if os.path.exists(report_path):
            os.unlink(report_path)
