"""
test_reducer.py — Unit tests for mapreduce/reducer.py

Tests mock stdin and capture stdout to exercise the reducer's aggregation logic.
All test data is SYNTHETIC.
"""

import io
import os
import sys

import pytest

# Make mapreduce/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mapreduce'))

from reducer import aggregate


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def run_reducer(input_lines):
    """
    Run the reducer aggregation logic against a list of input lines.

    Parameters
    ----------
    input_lines : list of str
        Lines in the format "skill<TAB>count".

    Returns
    -------
    list of tuple (str, int)
        Output sorted by count descending, then skill ascending — same order
        as the reducer's main() output.
    """
    counts = aggregate(iter(input_lines))
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_basic_aggregation():
    """TP-RED-001: Python×2 and Java×1 are aggregated correctly."""
    result = run_reducer(["Python\t1", "Python\t1", "Java\t1"])
    result_dict = dict(result)
    assert result_dict.get('Python') == 2, f"Expected Python=2, got {result_dict}"
    assert result_dict.get('Java') == 1, f"Expected Java=1, got {result_dict}"


def test_multiple_skills():
    """TP-RED-002: Multiple skills with varied counts are totalled correctly."""
    lines = [
        "Spark\t1", "Spark\t1", "Spark\t1",
        "Hive\t1", "Hive\t1",
        "Hadoop\t1",
    ]
    result_dict = dict(run_reducer(lines))
    assert result_dict.get('Spark') == 3, f"Expected Spark=3, got {result_dict}"
    assert result_dict.get('Hive') == 2, f"Expected Hive=2, got {result_dict}"
    assert result_dict.get('Hadoop') == 1, f"Expected Hadoop=1, got {result_dict}"


def test_empty_input():
    """TP-RED-003: Empty input produces empty output."""
    result = run_reducer([])
    assert result == [], f"Expected [], got {result}"


def test_sorted_by_count_desc():
    """TP-RED-004: Output is sorted by count descending."""
    lines = [
        "Python\t1",
        "Spark\t1", "Spark\t1", "Spark\t1",
        "Hive\t1", "Hive\t1",
    ]
    result = run_reducer(lines)
    counts = [count for _, count in result]
    assert counts == sorted(counts, reverse=True), (
        f"Output is not sorted descending: {result}"
    )
    # First entry should be Spark with count 3
    assert result[0] == ('Spark', 3), f"Expected ('Spark', 3) first, got {result[0]}"


def test_malformed_lines_skipped():
    """TP-RED-005: Lines without a tab separator are silently skipped."""
    lines = [
        "Python\t1",
        "this_line_has_no_tab",
        "",
        "Java\t1",
        "badly formatted line without tab",
    ]
    result_dict = dict(run_reducer(lines))
    # Only Python and Java should appear
    assert set(result_dict.keys()) == {'Python', 'Java'}, (
        f"Expected only Python and Java, got {set(result_dict.keys())}"
    )
    assert result_dict['Python'] == 1
    assert result_dict['Java'] == 1
