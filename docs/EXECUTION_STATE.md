# Execution State — Big Data Job Profile Recruitment Analyzer

**Student:** Sahil Goyal | Roll No.: 11242424 | Section: I/I2
**Last Updated:** Phase 1 — Scaffolding Complete

## Current Phase
Phase 1 — Project Scaffolding

## Status
In Progress

## Completed Phases
- [x] Phase 0 — Workspace Audit
- [x] Phase 1 — Project Scaffolding

## Next Exact Action
1. Acquire dataset: download a public job postings CSV (e.g. from Kaggle) and place it in `data/` directory
2. Run `python analytics/validate_dataset.py --input data/<your_dataset>.csv`
3. Review `outputs/data_quality_report.json`
4. Configure Hadoop VM and verify HDFS access

## Environment Blockers
- **BLOCKED:** HDFS upload, MapReduce, Pig, Hive stages require Hadoop VM (not yet verified)
- **PENDING:** Dataset not yet acquired
- **OK:** Python analytics scripts can run standalone once dataset is available

## Tests
- Scaffold tests: see test run results below
- Real data tests: BLOCKED pending dataset acquisition

## Test Results (Latest Run)
_Updated after scaffolding — run: `python -m pytest tests/ -v`_

```
tests/test_mapper.py::test_alias_matching PASSED
tests/test_mapper.py::test_case_insensitive PASSED
tests/test_mapper.py::test_phrase_matching PASSED
tests/test_mapper.py::test_no_false_positive_R PASSED
tests/test_mapper.py::test_distinct_per_post PASSED
tests/test_mapper.py::test_mentions_mode PASSED
tests/test_mapper.py::test_empty_text PASSED
tests/test_mapper.py::test_unicode_input PASSED
tests/test_mapper.py::test_fixture_counts PASSED
tests/test_reducer.py::test_basic_aggregation PASSED
tests/test_reducer.py::test_multiple_skills PASSED
tests/test_reducer.py::test_empty_input PASSED
tests/test_reducer.py::test_sorted_by_count_desc PASSED
tests/test_reducer.py::test_malformed_lines_skipped PASSED
tests/test_validate_dataset.py::test_basic_valid_csv PASSED
tests/test_validate_dataset.py::test_quoted_commas PASSED
tests/test_validate_dataset.py::test_duplicate_job_ids PASSED
tests/test_validate_dataset.py::test_missing_fields PASSED
tests/test_validate_dataset.py::test_unicode_text PASSED
tests/test_validate_dataset.py::test_output_json_structure PASSED
```

All 20 tests passed.
