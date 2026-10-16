# Big Data Job Profile Recruitment Analyzer

**Student:** Sahil Goyal | **Roll No.:** 11242424 | **Section:** H/H2 | **Date:** October 13, 2026

---

## Project Overview

A Hadoop-oriented Big Data analytics pipeline that processes job-posting CSV data through:

**HDFS â†’ MapReduce â†’ Pig â†’ Hive â†’ Python export â†’ Clustering â†’ Competence Matrix â†’ Visualizations**

Key outputs:
- Skill frequency counts (how many job postings require each skill)
- k=4 job family clusters (grouping job postings by skill profile)
- k=9 skill group clusters (grouping skills by job co-occurrence)
- 4Ã—9 competence matrix (Low/Medium/High skill-group coverage per job family)
- Six visualizations covering all major results

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
â”œâ”€â”€ README.md              â€” This file
â”œâ”€â”€ .gitignore             â€” Git ignore rules
â”œâ”€â”€ docs/                  â€” Project documentation and state tracking
â”œâ”€â”€ data/                  â€” Raw input CSV dataset (not committed)
â”œâ”€â”€ config/                â€” Skills dictionary and title alias mappings
â”œâ”€â”€ mapreduce/             â€” Hadoop Streaming mapper and reducer scripts
â”œâ”€â”€ pig/                   â€” Pig Latin cleaning and join scripts
â”œâ”€â”€ hive/                  â€” HiveQL DDL, analytics queries, UDF notes
â”œâ”€â”€ analytics/             â€” Python scripts for validation, clustering, visualization
â”œâ”€â”€ outputs/               â€” Generated CSV/JSON outputs from analytics scripts
â”œâ”€â”€ visualizations/        â€” Generated PNG charts
â”œâ”€â”€ tests/                 â€” pytest unit tests
â””â”€â”€ requirements/          â€” Software version tracking
```

---

## Dataset Acquisition

1. Download a public job postings CSV from Kaggle, for example:
   - **data-science-job-posting-on-glassdoor**: https://www.kaggle.com/datasets/andrewmvd/data-science-job-posting-on-glassdoor
   - Any similar "job listings" dataset with title, description, and skills fields
2. Place the CSV file in the `data/` directory.
3. Expected columns: `job_id` (or index), `job_title`, `company`, `location`, `salary_range`, `experience_required`, `skills_required`, `description`, `post_date`
4. Column names do not need to match exactly â€” `validate_dataset.py` performs fuzzy schema mapping.

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
- The Python analytics scripts (steps 1, 7â€“12) can run standalone on any machine with Python 3.9+ and the packages in `analytics/requirements.txt`.

---

## Testing

Run the full unit test suite:

```bash
python -m pytest tests/ -v
```

Tests cover: mapper skill detection, reducer aggregation, and dataset validation. All tests use synthetic fixtures â€” no real data required.

---

## GitHub Repository

🔗 **GitHub:** [https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer](https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer)

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

