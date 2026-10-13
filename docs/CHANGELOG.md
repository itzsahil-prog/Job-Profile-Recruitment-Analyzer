# Changelog — Big Data Job Profile Recruitment Analyzer

## [0.1.0] — Phase 1 Scaffolding — 2026-10-13

### Added
- Full project directory structure scaffolded
- README.md with project overview, prerequisites, execution order
- .gitignore for Python/Hadoop/data files
- config/skills_dictionary.csv with 50+ skills and aliases
- config/title_aliases.csv with job title normalization patterns
- mapreduce/mapper.py — Hadoop Streaming skill-frequency mapper
- mapreduce/reducer.py — Hadoop Streaming skill-frequency reducer
- mapreduce/run_skill_count.sh — Hadoop Streaming run script template
- pig/clean_jobs.pig — Pig Latin cleaning and deduplication script
- pig/build_job_skills.pig — Pig Latin job-skill pair extraction script
- hive/01_create_database_tables.sql — HiveQL DDL
- hive/02_views_and_queries.sql — HiveQL analytics queries and views
- hive/03_udf_notes.md — UDF documentation
- hive/04_index_version_demo.sql — Index version compatibility notes
- analytics/validate_dataset.py — Dataset quality reporting
- analytics/build_vectors.py — Feature matrix construction
- analytics/cluster_job_families.py — K-means k=4 job family clustering
- analytics/cluster_skill_groups.py — K-means k=9 skill group clustering
- analytics/build_competence_matrix.py — 4x9 competence matrix builder
- analytics/evaluate_clusters.py — Elbow and silhouette evaluation
- analytics/visualize.py — All project visualizations
- tests/test_mapper.py, test_reducer.py, test_validate_dataset.py
- docs/EXECUTION_STATE.md, DECISIONS.md, TEST_PLAN.md
- requirements/software-versions.md

## [0.0.0] — Phase 0 Workspace Audit — 2026-10-13

### Noted
- Workspace was empty at audit time (no prior files)
