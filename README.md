# Big Data Job Profile Recruitment Analyzer

**Enterprise Talent Intelligence & Big Data Recruitment Competency Platform**

---

## Project Overview

A comprehensive Big Data talent intelligence and recruitment analytics platform that processes 1.6+ million job postings through:

**HDFS → MapReduce → Pig → Hive → Python ML Clustering → Competence Matrix → Interactive Dashboard**

Key capabilities:
- **Interactive Web App & Candidate Matcher:** Assess candidate fit, parse job descriptions, identify skill gaps, and explore hiring trends in real time (`app.py`).
- **Skill Frequency Engine:** Quantifies exact market demand for 39+ canonical technologies.
- **Dual K-Means Clustering:** Groups postings into $k=4$ Job Families and skills into $k=9$ Functional Domains.
- **$4 \times 9$ Competence Matrix:** Formulates Low/Medium/High skill coverage thresholds across job profiles.
- **Publication-Ready Visualizations:** 6 high-resolution charts covering market distributions, elbow plots, and data quality.

---

## 🌐 Interactive Web Application

Launch the full-featured talent intelligence platform:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the Streamlit app
streamlit run app.py
```

Or deploy instantly via **Docker**:
```bash
docker-compose up --build
```
Navigate to `http://localhost:8501` to use the interactive dashboard.

---

## Prerequisites

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.9+ | Analytics scripts |
| Hadoop | 2.x or 3.x | HDFS + MapReduce + YARN |
| Apache Pig | 0.17.x | Pig Latin scripts |
| Apache Hive | 2.3.x or 3.1.x | DDL and analytics queries |
| VMware + Linux | Ubuntu 20.04 LTS | Hadoop sandbox VM |

Python package dependencies are listed in `analytics/requirements.txt`.

---

## Directory Structure

```
bigdata/
├── README.md              — This file
├── .gitignore             — Git ignore rules
├── docs/                  — Project documentation and state tracking
├── data/                  — Raw input CSV dataset (not committed)
├── config/                — Skills dictionary and title alias mappings
├── mapreduce/             — Hadoop Streaming mapper and reducer scripts
├── pig/                   — Pig Latin cleaning and join scripts
├── hive/                  — HiveQL DDL, analytics queries, UDF notes
├── analytics/             — Python scripts for validation, clustering, visualization
├── outputs/               — Generated CSV/JSON outputs from analytics scripts
├── visualizations/        — Generated PNG charts
├── tests/                 — pytest unit tests
└── requirements/          — Software version tracking
```

---

## Dataset Acquisition

1. Download a public job postings CSV from Kaggle, for example:
   - **data-science-job-posting-on-glassdoor**: https://www.kaggle.com/datasets/andrewmvd/data-science-job-posting-on-glassdoor
   - Any similar "job listings" dataset with title, description, and skills fields
2. Place the CSV file in the `data/` directory.
3. Expected columns: `job_id` (or index), `job_title`, `company`, `location`, `salary_range`, `experience_required`, `skills_required`, `description`, `post_date`
4. Column names do not need to match exactly — `validate_dataset.py` performs fuzzy schema mapping.

---

## Execution Order

Run these steps in sequence:

1. **Validate dataset** (Python, local):
   ```bash
   python analytics/validate_dataset.py --input data/<your_dataset>.csv
   ```

2. **Upload to HDFS** (requires Hadoop VM):
   ```bash
   hadoop fs -mkdir -p /user/hadoop/bigdata/raw
   hadoop fs -put data/<your_dataset>.csv /user/hadoop/bigdata/raw/job_postings.csv
   ```

3. **MapReduce skill count** (requires Hadoop VM):
   ```bash
   bash mapreduce/run_skill_count.sh
   ```

4. **Pig cleaning and join** (requires Hadoop VM):
   ```bash
   pig -param INPUT=/user/hadoop/bigdata/raw/job_postings.csv \
       -param OUTPUT=/user/hadoop/bigdata/clean_jobs \
       pig/clean_jobs.pig

   pig -param INPUT=/user/hadoop/bigdata/clean_jobs \
       -param OUTPUT=/user/hadoop/bigdata/job_skills \
       pig/build_job_skills.pig
   ```

5. **Hive DDL and analytics** (requires Hadoop VM):
   ```bash
   hive -f hive/01_create_database_tables.sql
   hive -f hive/02_views_and_queries.sql
   ```

6. **Export from Hive to CSV** (requires Hadoop VM):
   ```bash
   hive -e "INSERT OVERWRITE LOCAL DIRECTORY 'outputs/' ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' SELECT * FROM bigdata_jobs.skill_frequency ORDER BY post_count DESC;"
   ```

7. **Build feature vectors** (Python, local):
   ```bash
   python analytics/build_vectors.py --job-skills outputs/job_skills.csv --skill-groups config/skills_dictionary.csv
   ```

8. **Cluster job families** (Python, local):
   ```bash
   python analytics/cluster_job_families.py --matrix outputs/job_skill_matrix.csv
   ```

9. **Cluster skill groups** (Python, local):
   ```bash
   python analytics/cluster_skill_groups.py --matrix outputs/job_skill_matrix.csv
   ```

10. **Build competence matrix** (Python, local):
    ```bash
    python analytics/build_competence_matrix.py \
        --job-families outputs/job_family_assignments.csv \
        --skill-groups outputs/skill_group_assignments.csv \
        --job-skills outputs/job_skills.csv
    ```

11. **Evaluate clusters** (Python, local):
    ```bash
    python analytics/evaluate_clusters.py \
        --job-matrix outputs/job_skill_matrix.csv \
        --skill-matrix outputs/job_skill_matrix.csv \
        --job-clusters outputs/job_family_assignments.csv \
        --skill-clusters outputs/skill_group_assignments.csv
    ```

12. **Generate visualizations** (Python, local):
    ```bash
    python analytics/visualize.py
    ```

---

## Known Environment Blockers

- **HDFS upload, MapReduce, Pig, and Hive stages** all require an active Hadoop VM (VMware sandbox). These cannot be run on Windows directly.
- The Python analytics scripts (steps 1, 7–12) can run standalone on any machine with Python 3.9+ and the packages in `analytics/requirements.txt`.

---

## Testing

Run the full unit test suite:

```bash
python -m pytest tests/ -v
```

Tests cover: mapper skill detection, reducer aggregation, and dataset validation. All tests use synthetic fixtures — no real data required.

---

## GitHub Repository

?? **GitHub:** [https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer](https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer)

---

## Deployment

For detailed installation and execution instructions, see [DEPLOYMENT.md](docs/DEPLOYMENT.md).

### Quick Start:

```bash
# Clone the repository
git clone https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer.git
cd Job-Profile-Recruitment-Analyzer

# Set up virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r analytics\requirements.txt

# Run tests
python -m pytest tests/ -v

# Run the pipeline (local simulation mode)
python analytics\validate_dataset.py --input data\job_descriptions.csv
python local_sim\run_mapreduce.py
python analytics\visualize.py
```

For complete pipeline execution and troubleshooting, refer to [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

