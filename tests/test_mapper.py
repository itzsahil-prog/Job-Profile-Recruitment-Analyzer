"""
test_mapper.py — Unit tests for mapreduce/mapper.py

Tests use a synthetic skills dictionary fixture, not the real config file.
All test data is SYNTHETIC and created solely for testing purposes.
It does NOT represent real job postings or real persons.
"""

import csv
import io
import os
import sys
import tempfile

import pytest

# Make mapreduce/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mapreduce'))

from mapper import detect_skills, load_skill_patterns


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_skills_csv(rows, tmp_path=None):
    """
    Write a temporary CSV file with columns: canonical_skill, aliases, category.

    Parameters
    ----------
    rows : list of dict  [{"canonical_skill": ..., "aliases": ..., "category": ...}]
    tmp_path : str or None  — if None, uses tempfile

    Returns
    -------
    str  path to the temp CSV file
    """
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.csv', delete=False, encoding='utf-8', newline=''
    ) as f:
        writer = csv.DictWriter(f, fieldnames=['canonical_skill', 'aliases', 'category'])
        writer.writeheader()
        writer.writerows(rows)
        return f.name


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_alias_matching():
    """TP-MAP-001: PySpark alias should map to canonical skill 'Spark'."""
    csv_path = make_skills_csv([
        {'canonical_skill': 'Spark', 'aliases': 'pyspark,apache spark', 'category': 'Big Data'}
    ])
    try:
        patterns = load_skill_patterns(csv_path)
        found = detect_skills("We use PySpark for processing.", patterns, distinct=True)
        assert 'Spark' in found, f"Expected 'Spark' in {found}"
    finally:
        os.unlink(csv_path)


def test_case_insensitive():
    """TP-MAP-002: Skill matching is case-insensitive."""
    csv_path = make_skills_csv([
        {'canonical_skill': 'Hadoop', 'aliases': '', 'category': 'Big Data'},
        {'canonical_skill': 'Hive', 'aliases': '', 'category': 'Big Data'},
    ])
    try:
        patterns = load_skill_patterns(csv_path)
        found = detect_skills("HADOOP and hive", patterns, distinct=True)
        assert 'Hadoop' in found, f"Expected 'Hadoop' in {found}"
        assert 'Hive' in found, f"Expected 'Hive' in {found}"
    finally:
        os.unlink(csv_path)


def test_phrase_matching():
    """TP-MAP-003: Multi-word alias 'scikit learn' matches canonical 'scikit-learn'."""
    csv_path = make_skills_csv([
        {'canonical_skill': 'scikit-learn', 'aliases': 'sklearn,scikit learn', 'category': 'ML/AI'}
    ])
    try:
        patterns = load_skill_patterns(csv_path)
        found = detect_skills("experience with scikit learn required", patterns, distinct=True)
        assert 'scikit-learn' in found, f"Expected 'scikit-learn' in {found}"
    finally:
        os.unlink(csv_path)


def test_no_false_positive_R():
    """TP-MAP-004: 'R' must NOT match inside 'Recruiter', but MUST match in 'R programming'."""
    csv_path = make_skills_csv([
        {'canonical_skill': 'R', 'aliases': 'r programming,r language', 'category': 'Programming'}
    ])
    try:
        patterns = load_skill_patterns(csv_path)
        # Should NOT match: 'R' embedded inside the word 'Recruiter'
        not_found = detect_skills("Recruiter needed", patterns, distinct=True)
        assert 'R' not in not_found, f"'R' should NOT appear in {not_found} for 'Recruiter needed'"
        # SHOULD match: explicit alias 'r programming'
        found = detect_skills("experience with R programming", patterns, distinct=True)
        assert 'R' in found, f"Expected 'R' in {found} for 'experience with R programming'"
    finally:
        os.unlink(csv_path)


def test_distinct_per_post():
    """TP-MAP-005: With distinct=True, Spark appears at most once even if mentioned three times."""
    csv_path = make_skills_csv([
        {'canonical_skill': 'Spark', 'aliases': 'pyspark,apache spark', 'category': 'Big Data'}
    ])
    try:
        patterns = load_skill_patterns(csv_path)
        text = "Spark is required. We use Spark daily. Our Spark cluster is large."
        found = detect_skills(text, patterns, distinct=True)
        assert found.count('Spark') == 1, f"Expected exactly 1 'Spark', got {found}"
    finally:
        os.unlink(csv_path)


def test_mentions_mode():
    """TP-MAP-006: With distinct=False, Spark appears three times when mentioned three times."""
    csv_path = make_skills_csv([
        {'canonical_skill': 'Spark', 'aliases': 'pyspark,apache spark', 'category': 'Big Data'}
    ])
    try:
        patterns = load_skill_patterns(csv_path)
        text = "Spark is required. We use Spark daily. Our Spark cluster is large."
        found = detect_skills(text, patterns, distinct=False)
        assert found.count('Spark') == 3, f"Expected 3 'Spark', got {found.count('Spark')} in {found}"
    finally:
        os.unlink(csv_path)


def test_empty_text():
    """TP-MAP-007: detect_skills on empty string returns an empty list."""
    csv_path = make_skills_csv([
        {'canonical_skill': 'Python', 'aliases': 'python3', 'category': 'Programming'}
    ])
    try:
        patterns = load_skill_patterns(csv_path)
        found = detect_skills("", patterns, distinct=True)
        assert found == [], f"Expected [], got {found}"
    finally:
        os.unlink(csv_path)


def test_unicode_input():
    """TP-MAP-008: Unicode text containing Python is detected correctly."""
    csv_path = make_skills_csv([
        {'canonical_skill': 'Python', 'aliases': 'python3,python scripting', 'category': 'Programming'}
    ])
    try:
        patterns = load_skill_patterns(csv_path)
        found = detect_skills("Données avec Python et analyse.", patterns, distinct=True)
        assert 'Python' in found, f"Expected 'Python' in {found}"
    finally:
        os.unlink(csv_path)


def test_fixture_counts():
    """
    TP-MAP-009: Mini fixture with Python and Java.
    Text: 'We need Python, Java, and Python experts.'
    Distinct mode: Python appears once, Java appears once.
    """
    csv_path = make_skills_csv([
        {'canonical_skill': 'Python', 'aliases': 'python3', 'category': 'Programming'},
        {'canonical_skill': 'Java', 'aliases': 'java 8', 'category': 'Programming'},
    ])
    try:
        patterns = load_skill_patterns(csv_path)
        text = "We need Python, Java, and Python experts."
        found = detect_skills(text, patterns, distinct=True)
        assert found.count('Python') == 1, f"Expected 1 Python, got {found.count('Python')}"
        assert found.count('Java') == 1, f"Expected 1 Java, got {found.count('Java')}"
    finally:
        os.unlink(csv_path)
