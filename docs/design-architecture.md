# Design Architecture — Big Data Job Profile Recruitment Analyzer

**Student:** Sahil Goyal | Roll No.: 11242424 | Section: H/H2

---

## Pipeline Overview

The pipeline processes raw job-posting CSV data through seven stages:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE DATA FLOW                               │
│                                                                         │
│  Raw CSV Dataset                                                        │
│       │                                                                 │
│       ▼                                                                 │
│  [1] Data Validation (Python)                                           │
│       analytics/validate_dataset.py                                     │
│       Output: data_quality_report.json                                  │
│       │                                                                 │
│       ▼                                                                 │
│  [2] HDFS Ingestion (Hadoop)                                            │
│       hadoop fs -put data/job_postings.csv /user/hadoop/bigdata/raw/    │
│       │                                                                 │
│       ▼                                                                 │
│  [3] MapReduce — Skill Frequency (Hadoop Streaming)                     │
│       mapreduce/mapper.py + reducer.py                                  │
│       Output: HDFS /user/hadoop/bigdata/skill_counts/                   │
│       │                                                                 │
│       ▼                                                                 │
│  [4] Pig — Data Cleaning + Job-Skill Join (Apache Pig)                  │
│       pig/clean_jobs.pig → /user/hadoop/bigdata/clean_jobs/             │
│       pig/build_job_skills.pig → /user/hadoop/bigdata/job_skills/       │
│       │                                                                 │
│       ▼                                                                 │
│  [5] Hive — Analytics and Export (Apache Hive)                          │
│       hive/01_create_database_tables.sql                                │
│       hive/02_views_and_queries.sql                                     │
│       Export: skill_frequency.csv, job_skills.csv                       │
│       │                                                                 │
│       ▼                                                                 │
│  [6] Python Clustering (scikit-learn)                                   │
│       analytics/build_vectors.py        → feature matrices              │
│       analytics/cluster_job_families.py → k=4 job family clusters       │
│       analytics/cluster_skill_groups.py → k=9 skill group clusters      │
│       analytics/build_competence_matrix.py → 4×9 competence matrix      │
│       analytics/evaluate_clusters.py    → elbow + silhouette scores     │
│       │                                                                 │
│       ▼                                                                 │
│  [7] Visualizations (matplotlib/seaborn)                                │
│       analytics/visualize.py                                            │
│       Output: 6 PNG charts in visualizations/                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Descriptions

### Stage 1 — Data Validation
**Script:** `analytics/validate_dataset.py`

Performs quality checks on the raw CSV: encoding detection (UTF-8/latin-1),
schema mapping (fuzzy match of column names to logical fields), duplicate
detection by job_id, missing value counting, and rejection of records missing
required fields (job_id, job_title, description).

### Stage 2 — HDFS Ingestion
**Tool:** Hadoop HDFS CLI

Uploads the validated CSV to HDFS at `/user/hadoop/bigdata/raw/`. No transformation
is applied at this stage — the raw data is preserved for reproducibility.

### Stage 3 — MapReduce Skill Frequency
**Scripts:** `mapreduce/mapper.py`, `mapreduce/reducer.py`

Implemented as a Hadoop Streaming job. The mapper reads each CSV record,
matches skill names and aliases using word-boundary regex patterns loaded
from `config/skills_dictionary.csv`, and emits `skill_name<TAB>1` for each
detected skill. The reducer aggregates counts per skill.

Default mode: distinct-post counting (each skill counted at most once per posting).

### Stage 4 — Pig Cleaning and Join
**Scripts:** `pig/clean_jobs.pig`, `pig/build_job_skills.pig`

`clean_jobs.pig` removes records with missing required fields, normalizes
job titles to lowercase, trims whitespace, and deduplicates by job_id.

`build_job_skills.pig` tokenizes the `skills_required` comma-separated field
into a flat `(job_id, skill_name)` table.

### Stage 5 — Hive Analytics
**Scripts:** `hive/01_create_database_tables.sql`, `hive/02_views_and_queries.sql`

Creates the `bigdata_jobs` database, loads cleaned data into managed tables,
and runs analytics queries (top skills, skills by job title, location
distribution, skill co-occurrence, competence matrix support query).

### Stage 6 — Python Clustering
**Scripts:** `analytics/build_vectors.py`, `analytics/cluster_job_families.py`,
`analytics/cluster_skill_groups.py`, `analytics/build_competence_matrix.py`,
`analytics/evaluate_clusters.py`

Builds binary feature matrices, then applies scikit-learn KMeans with
`random_state=42` and `n_init=10`.

### Stage 7 — Visualizations
**Script:** `analytics/visualize.py`

Reads all output files and produces 6 charts using matplotlib and seaborn.

---

## Data Model

### Hive Tables in `bigdata_jobs`

| Table | Key Columns | Source |
|-------|------------|--------|
| `job_posts` | job_id, job_title, company, location, salary_range, experience_required, skills_required, description, post_date | HDFS raw CSV |
| `job_skills` | job_id, job_title, skill_name | Pig build_job_skills.pig |
| `skill_frequency` | skill_name, post_count | MapReduce reducer output |
| `job_posts_ext` | (same as job_posts) | External table over HDFS raw path |

---

## Clustering Design

### Job Families (k=4)

Each job posting is represented as a binary vector over all skill dimensions
(the job-by-skill matrix, rows=jobs, cols=skills, values=0/1).

KMeans with k=4 groups postings into four broad job families. The cluster
center coordinates identify the skills most characteristic of each family.

**Why k=4:** Empirically, job posting datasets tend to stratify naturally into
Data Engineering, Data Science, Analytics/BI, and Platform/DevOps clusters.
The elbow plot is used to validate this choice.

### Skill Groups (k=9)

Each skill is represented as a binary vector over all job posting dimensions
(the skill-by-job matrix — transpose of the job-by-skill matrix).
Two skills with similar co-occurrence patterns across jobs will cluster together.

KMeans with k=9 produces groups that tend to align with technology domains
(Big Data tools, ML frameworks, Cloud platforms, Databases, etc.).

**Why k=9:** Corresponds to the seven technology categories in the skills
dictionary, with room for cross-category groupings. Silhouette score validates fit.

---

## Competence Matrix Design

The 4×9 competence matrix answers: "For job family F, what fraction of its
postings require at least one skill from skill group G?"

```
prevalence(F, G) = |{jobs in F with ≥1 skill in G}| / |jobs in F| × 100%
```

Thresholds:
- **Low:**    prevalence < 20%
- **Medium:** 20% ≤ prevalence < 50%
- **High:**   prevalence ≥ 50%

These thresholds are documented in `docs/DECISIONS.md` (DD-003) and can be
recalibrated after examining real data distribution.

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/skills_dictionary.csv` | 60+ canonical skills with aliases and categories |
| `config/title_aliases.csv` | Raw job title patterns → normalized job titles |
