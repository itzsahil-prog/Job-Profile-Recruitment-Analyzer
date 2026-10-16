# PROJECT SUBMISSION

**Course:** Big Data Analytics  
**Student Name:** Sahil Goyal  
**Roll Number:** 11242424  
**Section:** I/I2  
**Submission Date:** October 16, 2026

---

## Project Title
Big Data Job Profile Recruitment Analyzer

---

## GitHub Repository
https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer

---

## Project Overview
A comprehensive Hadoop-based Big Data analytics pipeline that processes 1.6 million job postings to analyze skill demand patterns, cluster job families, and generate insights through machine learning.

---

## Technologies Used
- **Big Data:** Hadoop HDFS, MapReduce, Apache Pig, Apache Hive
- **Programming:** Python 3.14
- **Analytics:** pandas, NumPy, scikit-learn
- **Machine Learning:** KMeans clustering (k=4 job families, k=9 skill groups)
- **Visualization:** matplotlib, seaborn
- **Testing:** pytest (20 unit tests)
- **Version Control:** Git, GitHub

---

## Key Features
1. **Data Validation** - Processes 1.6M job postings with quality checks
2. **MapReduce Pipeline** - Extracts 39 canonical skills from job descriptions
3. **Data Cleaning** - Pig-based normalization and deduplication
4. **Analytics** - Hive-based aggregations and competence matrix
5. **Machine Learning** - KMeans clustering for job families and skill groups
6. **Visualizations** - 6 comprehensive charts (skill frequency, distributions, heatmaps)

---

## Execution Results
- **Top Skill:** Python (66,013 job postings)
- **Job Families:** 4 distinct clusters identified
- **Skill Groups:** 9 technology domains discovered
- **Test Coverage:** 100% (20/20 tests passing)
- **Pipeline Execution Time:** ~11 minutes for full dataset

---

## How to Run
See DEPLOYMENT.md in the repository for detailed instructions:
https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer/blob/master/docs/DEPLOYMENT.md

Quick start:
```bash
git clone https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer.git
cd Job-Profile-Recruitment-Analyzer
python -m venv .venv
.venv\Scripts\activate
pip install -r analytics\requirements.txt
python -m pytest tests/ -v
python local_sim\run_mapreduce.py
```

---

## Project Structure
- **/analytics/** - Python analytics scripts (7 files)
- **/local_sim/** - Local Hadoop simulation (Windows-compatible)
- **/mapreduce/** - Hadoop Streaming mapper & reducer
- **/pig/** - Pig Latin data cleaning scripts
- **/hive/** - HiveQL analytics queries
- **/config/** - Skills dictionary (39 skills, 232 aliases)
- **/tests/** - pytest unit tests (20 tests)
- **/docs/** - Comprehensive documentation

---

## Documentation
1. **README.md** - Project overview and prerequisites
2. **DEPLOYMENT.md** - Installation and execution guide
3. **docs/design-architecture.md** - Technical design document
4. **docs/tasks.md** - Complete task breakdown (42 tasks)

---

## Outputs Generated
All outputs are in the /outputs/ directory:
1. data_quality_report.json
2. skill_frequency.csv (39 skills)
3. clean_jobs.csv (1.6M cleaned records)
4. job_skills.csv (flat job-skill pairs)
5. job_skill_matrix.csv (binary feature matrix)
6. job_family_assignments.csv (k=4 clusters)
7. skill_group_assignments.csv (k=9 clusters)
8. competence_matrix.csv (4×9 matrix)
9. Evaluation metrics (elbow, silhouette scores)

All visualizations are in the /visualizations/ directory (6 PNG charts).

---

## Testing
```bash
python -m pytest tests/ -v
```
**Result:** ? All 20 tests passed

Tests cover:
- Mapper skill detection logic (9 tests)
- Reducer aggregation logic (5 tests)
- Dataset validation (6 tests)

---

## Deployment Status
? **Source code:** Committed to GitHub  
? **Documentation:** Complete and accessible  
? **Tests:** All passing (100% success rate)  
? **Pipeline:** Fully functional without errors  
? **Public Repository:** https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer

---

## Academic Declaration
I declare that this project is my original work and has been completed as part of the Big Data Analytics course requirements.

**Signature:** Sahil Goyal  
**Date:** October 16, 2026
