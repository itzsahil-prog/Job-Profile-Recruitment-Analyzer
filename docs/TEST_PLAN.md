# Test Plan — Big Data Job Profile Recruitment Analyzer

**Student:** Sahil Goyal | Roll No.: 11242424 | Section: I/I2

---

## TP-MAP: Mapper Tests (`tests/test_mapper.py`)

| ID | Test Name | Description |
|----|-----------|-------------|
| TP-MAP-001 | `test_alias_matching` | Alias "PySpark" maps to canonical skill "Spark" |
| TP-MAP-002 | `test_case_insensitive` | "HADOOP" and "hive" both match their canonical forms |
| TP-MAP-003 | `test_phrase_matching` | Multi-word alias "scikit learn" matches "scikit-learn" |
| TP-MAP-004 | `test_no_false_positive_R` | "R" not matched inside "Recruiter"; IS matched in "R programming" |
| TP-MAP-005 | `test_distinct_per_post` | Spark mentioned 3× emits only once in distinct mode |
| TP-MAP-006 | `test_mentions_mode` | Spark mentioned 3× emits 3 times with distinct=False |
| TP-MAP-007 | `test_empty_text` | Empty string returns empty list |
| TP-MAP-008 | `test_unicode_input` | Unicode text correctly detects Python |
| TP-MAP-009 | `test_fixture_counts` | Mini fixture: Python×1, Java×1 in distinct mode |

---

## TP-RED: Reducer Tests (`tests/test_reducer.py`)

| ID | Test Name | Description |
|----|-----------|-------------|
| TP-RED-001 | `test_basic_aggregation` | Python×2, Java×1 summed correctly |
| TP-RED-002 | `test_multiple_skills` | Three skills with varied counts totalled correctly |
| TP-RED-003 | `test_empty_input` | Empty input produces empty output |
| TP-RED-004 | `test_sorted_by_count_desc` | Output is sorted by count descending |
| TP-RED-005 | `test_malformed_lines_skipped` | Lines without tab separators are silently skipped |

---

## TP-VAL: Validate Dataset Tests (`tests/test_validate_dataset.py`)

| ID | Test Name | Description |
|----|-----------|-------------|
| TP-VAL-001 | `test_basic_valid_csv` | 5 synthetic rows → total_rows_raw=5 |
| TP-VAL-002 | `test_quoted_commas` | Commas inside quoted description fields don't split rows |
| TP-VAL-003 | `test_duplicate_job_ids` | 3 rows with 2 sharing job_id → rows_after_dedup=2 |
| TP-VAL-004 | `test_missing_fields` | Rows with empty job_title → missing_values count > 0 |
| TP-VAL-005 | `test_unicode_text` | Unicode in description → no crash, correct row count |
| TP-VAL-006 | `test_output_json_structure` | Report JSON contains all required keys |

---

## TP-INT: Integration Tests (manual — requires Hadoop VM)

| ID | Description | Status |
|----|-------------|--------|
| TP-INT-001 | HDFS upload of raw CSV | BLOCKED — Hadoop VM required |
| TP-INT-002 | MapReduce skill count job (`run_skill_count.sh`) | BLOCKED |
| TP-INT-003 | Pig `clean_jobs.pig` script | BLOCKED |
| TP-INT-004 | Pig `build_job_skills.pig` script | BLOCKED |
| TP-INT-005 | Hive DDL execution (`01_create_database_tables.sql`) | BLOCKED |
| TP-INT-006 | Hive analytics queries (`02_views_and_queries.sql`) | BLOCKED |
| TP-INT-007 | Full Python pipeline end-to-end (validate → cluster → visualize) | PENDING (dataset required) |

---

## Running Unit Tests

```bash
python -m pytest tests/ -v
```

Expected: 20 tests, all PASSED.
