# Deployment Guide - Big Data Job Profile Recruitment Analyzer

**Platform:** Enterprise Talent Intelligence Platform

---

## GitHub Repository

**Repository URL:** https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer

---

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-github-url>
cd bigdata
```

### 2. Install Prerequisites

- **Python 3.9+** (Python 3.14.6 recommended)
- **Git**
- **pip** (Python package manager)

### 3. Set Up Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\activate

# Windows CMD:
.venv\Scripts\activate.bat

# Install dependencies
pip install -r analytics\requirements.txt
```

### 4. Verify Installation

```bash
# Test package imports
python -c "import pandas, numpy, sklearn, matplotlib, seaborn, pytest; print('All packages installed')"

# Run test suite (all 20 tests should pass)
python -m pytest tests/ -v
```

---

## Running the Full Pipeline

### Option 1: Local Simulation Mode (Windows-Compatible)

This mode runs the entire 7-stage pipeline on Windows without requiring Hadoop VM:

```bash
# Stage 1: Data Validation
python analytics\validate_dataset.py --input data\job_descriptions.csv

# Stage 2: MapReduce Skill Frequency
python local_sim\run_mapreduce.py

# Stage 3: Pig Data Cleaning
python local_sim\run_pig_cleaning.py

# Stage 4: Pig Job-Skills Join
python local_sim\run_pig_job_skills.py

# Stage 5: Hive Analytics
python local_sim\run_hive_analytics.py

# Stage 6a: Build Feature Vectors
python analytics\build_vectors.py --job-skills outputs\job_skills.csv --skill-groups config\skills_dictionary.csv

# Stage 6b: Cluster Job Families
python analytics\cluster_job_families.py --matrix outputs\job_skill_matrix.csv

# Stage 6c: Cluster Skill Groups
python analytics\cluster_skill_groups.py --matrix outputs\skill_job_matrix.csv

# Stage 6d: Build Competence Matrix
python analytics\build_competence_matrix.py --job-families outputs\job_family_assignments.csv --skill-groups outputs\skill_group_assignments.csv --job-skills outputs\job_skills.csv

# Stage 6e: Evaluate Clusters
python analytics\evaluate_clusters.py --job-matrix outputs\job_skill_matrix.csv --skill-matrix outputs\skill_job_matrix.csv --job-clusters outputs\job_family_assignments.csv --skill-clusters outputs\skill_group_assignments.csv

# Stage 7: Generate Visualizations
python analytics\visualize.py
```

### Option 2: Hadoop VM Mode

If you have access to a Hadoop VM, see README.md for HDFS, MapReduce, Pig, and Hive commands.

---

## Expected Outputs

### In outputs/ directory:

1. **data_quality_report.json** - Dataset validation results
2. **skill_frequency.csv** - Top skills by posting count
3. **clean_jobs.csv** - Cleaned job postings
4. **job_skills.csv** - Flat job-skill pairs
5. **job_skill_matrix.csv** - Binary feature matrix (jobs  skills)
6. **skill_job_matrix.csv** - Transposed matrix (skills  jobs)
7. **job_family_assignments.csv** - k=4 job family clusters
8. **skill_group_assignments.csv** - k=9 skill group clusters
9. **competence_matrix.csv** - 49 competence matrix
10. **Evaluation metrics** - elbow and silhouette scores

### In isualizations/ directory:

1. **skill_frequency_top20.png** - Top 20 most demanded skills
2. **job_family_distribution.png** - Distribution across 4 job families
3. **skill_group_distribution.png** - Distribution across 9 skill groups
4. **competence_matrix_heatmap.png** - Heatmap of competence matrix
5. **job_family_elbow.png** - Elbow plot for job clustering
6. **skill_group_elbow.png** - Elbow plot for skill clustering

---

## Project Structure

```
bigdata/
+-- analytics/          # Python analytics scripts
+-- config/             # Skills dictionary and aliases
+-- data/               # Raw dataset (not in repo)
+-- docs/               # Documentation
+-- hive/               # Hive SQL scripts
+-- local_sim/          # Local simulation scripts (Windows)
+-- mapreduce/          # Hadoop MapReduce scripts
+-- outputs/            # Generated outputs (not in repo)
+-- pig/                # Pig Latin scripts
+-- tests/              # Unit tests (pytest)
+-- visualizations/     # Generated charts (not in repo)
+-- README.md           # Main documentation
```

---

## Troubleshooting

### Issue: Import errors (sklearn not found)

**Solution:**
```bash
pip install scikit-learn
```

### Issue: Python version too old

**Solution:**
Install Python 3.9 or higher from python.org

### Issue: Tests fail

**Solution:**
```bash
# Ensure virtual environment is activated
.venv\Scripts\activate

# Reinstall dependencies
pip install -r analytics\requirements.txt

# Run tests with verbose output
python -m pytest tests/ -v
```

### Issue: Dataset not found

**Solution:**
Place your job postings CSV in the data/ directory. The pipeline expects:
- Columns: Job Id, Job Title, Job Description, skills, Company, etc.
- UTF-8 or Latin-1 encoding
- CSV format

---

## Dataset

This project uses job posting data with approximately 1.6 million records. The dataset is not included in the repository due to size. Download a job postings dataset from Kaggle or similar source and place it in data/job_descriptions.csv.

Expected schema:
- Job Id (required)
- Job Title (required)
- Job Description (required)
- skills (required)
- Company, location, experience, salary, etc. (optional)

---

## Technology Stack

- **Big Data:** Hadoop HDFS, MapReduce, Apache Pig, Apache Hive
- **Analytics:** Python, pandas, NumPy, scikit-learn
- **Visualization:** matplotlib, seaborn
- **Testing:** pytest

---

## License

Educational project for academic submission.

---

## Contact

**Section:** I/I2

For questions or issues, refer to the documentation in the docs/ directory.

