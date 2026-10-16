# Implementation Plan: Big Data Job Profile Recruitment Analyzer - Completion & Deployment

## Overview

This task plan covers the final stages of completing, validating, and deploying the Big Data Job Profile Recruitment Analyzer project. Since the project is running on Windows without a Hadoop VM, all tasks will use the local simulation mode provided in the `local_sim/` directory.

The pipeline executes 7 stages in local simulation mode:
1. Data Validation → 2. Local MapReduce → 3. Local Pig Cleaning → 4. Local Pig Job-Skills → 5. Local Hive Analytics → 6. Python Clustering (5 scripts) → 7. Visualizations

All core implementation is complete and unit tests pass. This plan focuses on:
- Environment setup and dependency installation
- Full pipeline execution in local simulation mode
- Validation of all outputs
- Git repository management
- GitHub deployment
- Deployment documentation

---

## Tasks

### Phase 1: Environment Setup & Validation

- [x] 1.1 Set up Python virtual environment
  - Create virtual environment: `python -m venv .venv`
  - Activate virtual environment (Windows): `.venv\Scripts\activate`
  - Verify Python version: `python --version` (should be 3.9+)
  - _Requirements: Environment isolation for reproducible execution_

- [x] 1.2 Install all required Python dependencies
  - Install packages: `pip install -r analytics\requirements.txt`
  - Verify installation: `pip list` (check pandas, numpy, scikit-learn, matplotlib, seaborn, pytest)
  - _Requirements: All Python packages needed for analytics and testing_

- [x] 1.3 Verify package imports and environment health
  - Run quick import test: `python -c "import pandas, numpy, sklearn, matplotlib, seaborn, pytest; print('All packages imported successfully')"`
  - If any import fails, diagnose and reinstall specific package
  - _Requirements: Ensure all dependencies are functional before pipeline execution_

- [x] 1.4 Run full unit test suite to confirm environment
  - Execute tests: `python -m pytest tests/ -v`
  - Verify all 20 tests pass
  - Review test output for any warnings or deprecation notices
  - _Requirements: Validate that mapper, reducer, and dataset validation logic work correctly_

- [x] 1.5 Checkpoint - Environment ready
  - Confirm .venv is activated, all packages installed, all tests pass
  - Ask user if any issues arose during setup

---

### Phase 2: Execute Full Pipeline (Local Simulation Mode)

- [x] 2.1 Run Stage 1 - Data Validation
  - Command: `python analytics\validate_dataset.py --input data\job_descriptions.csv`
  - Expected output: `outputs\data_quality_report.json`
  - Verify output file exists and contains valid JSON
  - Check for any data quality warnings in the report
  - _Requirements: Validate dataset schema, encoding, duplicates, missing values_

- [x] 2.2 Run Stage 2 - Local MapReduce Simulation
  - Command: `python local_sim\run_mapreduce.py`
  - Expected outputs: 
    - `outputs\skill_frequency.csv` (distinct post count mode)
    - `outputs\skill_frequency_post_count.csv`
    - `outputs\skill_frequency_mention_count.csv`
    - `outputs\mapreduce_run_log.txt`
  - Verify all output files exist and contain data
  - Check log file for any errors or warnings
  - _Requirements: Count skill frequencies using MapReduce logic (post count and mention count)_

- [x] 2.3 Run Stage 3 - Local Pig Cleaning Simulation
  - Command: `python local_sim\run_pig_cleaning.py`
  - Expected outputs:
    - `outputs\clean_jobs.csv`
    - `outputs\pig_cleaning_log.txt`
  - Verify clean_jobs.csv exists and has fewer rows than raw data (duplicates removed)
  - Check log file for cleaning statistics
  - _Requirements: Remove invalid records, normalize job titles, deduplicate by job_id_

- [ ] 2.4 Run Stage 4 - Local Pig Job-Skills Join Simulation
  - Command: `python local_sim\run_pig_job_skills.py`
  - Expected outputs:
    - `outputs\job_skills.csv`
    - `outputs\pig_job_skills_log.txt`
  - Verify job_skills.csv exists and contains (job_id, job_title, skill_name) tuples
  - Check row count is reasonable (multiple skills per job)
  - _Requirements: Tokenize skills_required field into flat job-skill pairs_

- [~] 2.5 Run Stage 5 - Local Hive Analytics Simulation
  - Command: `python local_sim\run_hive_analytics.py`
  - Expected output: `outputs\hive_analytics_log.txt` (or similar analytics results)
  - Verify analytics queries complete successfully
  - Check log for query results and execution summaries
  - _Requirements: Simulate Hive analytics queries on cleaned data_

- [~] 2.6 Run Stage 6a - Build Feature Vectors
  - Command: `python analytics\build_vectors.py --job-skills outputs\job_skills.csv --skill-groups config\skills_dictionary.csv`
  - Expected outputs:
    - `outputs\job_skill_matrix.csv` (binary matrix: jobs × skills)
    - `outputs\skill_job_matrix.csv` (binary matrix: skills × jobs, transpose)
  - Verify both matrices exist and have correct dimensions
  - _Requirements: Create binary feature matrices for clustering_

- [~] 2.7 Run Stage 6b - Cluster Job Families
  - Command: `python analytics\cluster_job_families.py --matrix outputs\job_skill_matrix.csv`
  - Expected output: `outputs\job_family_assignments.csv`
  - Verify output contains job_id and cluster_id columns
  - Check that k=4 clusters are assigned
  - _Requirements: KMeans clustering with k=4 to identify job families_

- [~] 2.8 Run Stage 6c - Cluster Skill Groups
  - Command: `python analytics\cluster_skill_groups.py --matrix outputs\skill_job_matrix.csv`
  - Expected output: `outputs\skill_group_assignments.csv`
  - Verify output contains skill_name and cluster_id columns
  - Check that k=9 clusters are assigned
  - _Requirements: KMeans clustering with k=9 to identify skill groups_

- [~] 2.9 Run Stage 6d - Build Competence Matrix
  - Command: `python analytics\build_competence_matrix.py --job-families outputs\job_family_assignments.csv --skill-groups outputs\skill_group_assignments.csv --job-skills outputs\job_skills.csv`
  - Expected output: `outputs\competence_matrix.csv` (4×9 matrix)
  - Verify matrix has 4 rows (job families) and 9 columns (skill groups)
  - Check values are prevalence percentages (0-100%)
  - _Requirements: Calculate skill group prevalence per job family_

- [~] 2.10 Run Stage 6e - Evaluate Clusters
  - Command: `python analytics\evaluate_clusters.py --job-matrix outputs\job_skill_matrix.csv --skill-matrix outputs\skill_job_matrix.csv --job-clusters outputs\job_family_assignments.csv --skill-clusters outputs\skill_group_assignments.csv`
  - Expected outputs:
    - `outputs\job_family_elbow.csv`
    - `outputs\skill_group_elbow.csv`
    - `outputs\job_family_silhouette.csv`
    - `outputs\skill_group_silhouette.csv`
  - Verify all evaluation metrics files exist
  - Review scores to validate clustering quality
  - _Requirements: Generate elbow and silhouette scores for k selection validation_

- [~] 2.11 Run Stage 7 - Generate Visualizations
  - Command: `python analytics\visualize.py`
  - Expected outputs in `visualizations/`:
    - `skill_frequency_top20.png`
    - `job_family_distribution.png`
    - `skill_group_distribution.png`
    - `competence_matrix_heatmap.png`
    - `job_family_elbow.png`
    - `skill_group_elbow.png`
  - Verify all 6 PNG files exist and are viewable
  - Check file sizes are reasonable (not empty or corrupted)
  - _Requirements: Generate all project visualizations using matplotlib/seaborn_

- [~] 2.12 Checkpoint - Full pipeline executed successfully
  - Review all outputs in `outputs/` directory (14+ files expected)
  - Review all visualizations in `visualizations/` directory (6 PNG files)
  - Check all log files for errors
  - Ask user to confirm all stages completed without errors

---

### Phase 3: Validation & Quality Assurance

- [~] 3.1 Verify all expected output files exist
  - Check `outputs/` directory for:
    - data_quality_report.json
    - skill_frequency.csv (and variants)
    - clean_jobs.csv
    - job_skills.csv
    - job_skill_matrix.csv
    - skill_job_matrix.csv
    - job_family_assignments.csv
    - skill_group_assignments.csv
    - competence_matrix.csv
    - job_family_elbow.csv, skill_group_elbow.csv
    - job_family_silhouette.csv, skill_group_silhouette.csv
  - Create a checklist and mark each file as present/absent
  - _Requirements: Confirm complete pipeline execution with all artifacts_

- [~] 3.2 Verify all visualization files exist
  - Check `visualizations/` directory for all 6 PNG files
  - Open each PNG to confirm it renders properly
  - Verify file sizes are > 10KB (not corrupted/empty)
  - _Requirements: Validate all charts are generated and viewable_

- [~] 3.3 Inspect data quality report
  - Open `outputs\data_quality_report.json`
  - Review: total_rows, duplicates, missing_values, rejected_rows
  - Check encoding_detected (should be UTF-8 or latin-1)
  - Verify schema_mapping shows all required columns matched
  - _Requirements: Understand dataset quality and any cleaning that occurred_

- [~] 3.4 Review cluster evaluation metrics
  - Open elbow and silhouette CSV files
  - Confirm k=4 and k=9 choices are reasonable (elbow point visible, silhouette scores positive)
  - Document any concerns about cluster quality
  - _Requirements: Validate clustering parameters are appropriate_

- [~] 3.5 Run full test suite again
  - Command: `python -m pytest tests/ -v`
  - Verify all tests still pass after pipeline execution
  - Check for any new warnings or issues
  - _Requirements: Ensure pipeline execution didn't introduce regressions_

- [~] 3.6 Review all log files for errors
  - Check: mapreduce_run_log.txt, pig_cleaning_log.txt, pig_job_skills_log.txt
  - Search for keywords: ERROR, FAILED, Exception
  - Document any warnings or issues found
  - _Requirements: Confirm no hidden errors in pipeline execution_

- [~] 3.7 Checkpoint - Validation complete
  - Confirm all outputs exist, visualizations render, no errors in logs, tests pass
  - Ask user if they want to review any specific outputs before proceeding to Git operations

---

### Phase 4: Git Repository Management

- [~] 4.1 Review and update .gitignore
  - Current .gitignore already excludes:
    - `__pycache__/`, `*.pyc`
    - `.venv/`, `venv/`, `env/`
    - `data/*.csv` (except sample*.csv)
    - `outputs/*.csv`
    - `visualizations/*.png`
    - `*.log`, `*.tmp`
  - Add `.pytest_cache/` if not already present
  - Verify .venv directory is excluded
  - _Requirements: Prevent committing large data files, outputs, and environment directories_

- [~] 4.2 Review git status and staged changes
  - Command: `git status`
  - Review list of modified, new, and untracked files
  - Identify which files should be committed:
    - All source code (mapreduce/, pig/, hive/, analytics/, local_sim/)
    - Configuration files (config/)
    - Documentation (docs/, README.md)
    - Test files (tests/)
    - Requirements (analytics/requirements.txt)
  - Identify which files should NOT be committed (verify .gitignore works):
    - .venv/
    - __pycache__/
    - data/job_descriptions.csv
    - outputs/*.csv
    - visualizations/*.png
    - *.log files
  - _Requirements: Ensure only appropriate files are staged for commit_

- [~] 4.3 Stage all appropriate files for commit
  - Stage implementation files: `git add mapreduce/ pig/ hive/ analytics/ local_sim/`
  - Stage configuration: `git add config/`
  - Stage documentation: `git add docs/ README.md`
  - Stage tests: `git add tests/`
  - Stage project files: `git add .gitignore analytics/requirements.txt`
  - Verify staging: `git status`
  - _Requirements: Stage all project source code and documentation_

- [~] 4.4 Create comprehensive commit
  - Create commit with message:
    ```
    git commit -m "Complete Big Data Job Profile Recruitment Analyzer
    
    - Implement full 7-stage pipeline (MapReduce, Pig, Hive, Clustering, Visualization)
    - Add local simulation mode for Windows environment
    - Create 20 passing unit tests
    - Generate competence matrix (4x9 job families vs skill groups)
    - Produce 6 visualization charts
    - Document design architecture and execution state
    
    Student: Sahil Goyal | Roll No: 11242424 | Section: I/I2"
    ```
  - Verify commit success: `git log -1`
  - _Requirements: Create meaningful commit documenting project completion_

- [~] 4.5 Verify clean working directory
  - Command: `git status`
  - Expected: "nothing to commit, working tree clean" (except untracked outputs/data)
  - Verify only ignored files remain untracked
  - _Requirements: Confirm all appropriate changes are committed_

- [~] 4.6 Checkpoint - Git operations complete
  - Confirm commit created successfully with all source files
  - Ask user to confirm they're ready to push to GitHub

---

### Phase 5: GitHub Deployment

- [~] 5.1 Prompt user to create GitHub repository
  - Ask user to:
    1. Go to https://github.com/new
    2. Create repository named "bigdata-job-profile-analyzer" (or their preferred name)
    3. Do NOT initialize with README (project already has one)
    4. Copy the repository URL (e.g., https://github.com/username/bigdata-job-profile-analyzer.git)
  - Wait for user to provide the GitHub repository URL
  - _Requirements: User must create empty GitHub repository first_

- [~] 5.2 Add GitHub remote to local repository
  - Command: `git remote add origin <GITHUB_URL>`
  - Replace <GITHUB_URL> with the URL provided by user
  - Verify remote added: `git remote -v`
  - _Requirements: Link local repository to GitHub remote_

- [~] 5.3 Push to GitHub main branch
  - Command: `git push -u origin main`
  - Branch is now set to main
  - Monitor push progress and verify success
  - If authentication required, guide user through GitHub authentication
  - _Requirements: Upload all committed code to GitHub_

- [~] 5.4 Verify GitHub push success
  - Ask user to visit their GitHub repository URL in browser
  - Verify all files are visible on GitHub
  - Check that README.md displays properly
  - Confirm commit history is present
  - _Requirements: Validate successful deployment to GitHub_

- [~] 5.5 Document GitHub repository URL
  - Add GitHub URL to project documentation
  - Command: `echo "GitHub Repository: <GITHUB_URL>" >> docs\DEPLOYMENT.md`
  - _Requirements: Record deployment location for future reference_

- [~] 5.6 Checkpoint - GitHub deployment complete
  - Confirm project is live on GitHub with all source code
  - Ask user if they want to make the repository public or keep it private

---

### Phase 6: Deployment Documentation

- [~] 6.1 Create comprehensive DEPLOYMENT.md
  - Create file: `docs\DEPLOYMENT.md`
  - Include sections:
    - Project Information (student name, roll number, section)
    - GitHub Repository URL
    - Prerequisites (Python 3.9+, Git)
    - Installation Instructions (clone, venv setup, pip install)
    - Execution Instructions (how to run full pipeline)
    - Expected Outputs (list all output files and visualizations)
    - Troubleshooting (common issues and solutions)
    - Local Simulation Mode (explain Windows workaround)
  - _Requirements: Complete deployment guide for running the project_

- [~] 6.2 Update README.md with deployment section
  - Add "Deployment" section to README.md
  - Include:
    - Link to GitHub repository
    - Quick start instructions
    - Link to DEPLOYMENT.md for detailed instructions
  - _Requirements: Update main README with deployment information_

- [~] 6.3 Create RESULTS.md documenting pipeline outputs
  - Create file: `docs\RESULTS.md`
  - Document:
    - Summary of data_quality_report.json findings
    - Top 20 skills from skill_frequency.csv
    - Description of 4 job family clusters
    - Description of 9 skill group clusters
    - Competence matrix insights
    - Cluster evaluation metrics (elbow, silhouette)
  - Include notes about what each visualization shows
  - _Requirements: Document pipeline results for academic submission_

- [~] 6.4 Update EXECUTION_STATE.md with completion status
  - Update existing `docs\EXECUTION_STATE.md`
  - Mark all 7 pipeline stages as COMPLETE
  - Add "Deployment Status" section showing GitHub URL
  - Add timestamp of completion
  - _Requirements: Finalize execution state tracking document_

- [~] 6.5 Commit and push documentation updates
  - Stage new documentation: `git add docs/DEPLOYMENT.md docs/RESULTS.md docs/EXECUTION_STATE.md README.md`
  - Commit: `git commit -m "Add deployment documentation and results summary"`
  - Push: `git push origin main`
  - _Requirements: Update GitHub repository with deployment documentation_

- [~] 6.6 Final checkpoint - Project complete and deployed
  - Verify GitHub repository has all code, documentation, and deployment instructions
  - Confirm user can successfully clone and run the project following DEPLOYMENT.md
  - Ask user if they need any additional documentation or have questions

---

## Notes

- **Virtual Environment**: All Python commands assume `.venv\Scripts\activate` has been run first. Always activate the virtual environment before running Python scripts.

- **Local Simulation Mode**: This project is designed for Hadoop but includes local simulation scripts in `local_sim/` that replicate the pipeline behavior on Windows without requiring a Hadoop VM. All tasks use local simulation mode.

- **Git Operations**: Tasks carefully exclude large data files and outputs from commits via .gitignore. Only source code, configuration, and documentation are committed.

- **GitHub Authentication**: If user encounters authentication issues during push, guide them to use:
  - Personal Access Token (classic) with "repo" scope
  - Or GitHub CLI: `gh auth login`

- **Testing**: The project has 20 unit tests covering mapper, reducer, and dataset validation. Tests use synthetic data and don't require the full dataset.

- **Pipeline Dependencies**: Each stage depends on outputs from previous stages. The task order must be followed sequentially.

- **Validation**: Phase 3 includes comprehensive validation to ensure pipeline executed correctly before committing to Git.

- **Documentation**: Phase 6 creates three key documentation files:
  - DEPLOYMENT.md (how to install and run)
  - RESULTS.md (what the pipeline found)
  - Updated EXECUTION_STATE.md (completion tracking)

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3", "1.4"] },
    { "id": 3, "tasks": ["2.1"] },
    { "id": 4, "tasks": ["2.2"] },
    { "id": 5, "tasks": ["2.3"] },
    { "id": 6, "tasks": ["2.4"] },
    { "id": 7, "tasks": ["2.5"] },
    { "id": 8, "tasks": ["2.6"] },
    { "id": 9, "tasks": ["2.7", "2.8"] },
    { "id": 10, "tasks": ["2.9"] },
    { "id": 11, "tasks": ["2.10"] },
    { "id": 12, "tasks": ["2.11"] },
    { "id": 13, "tasks": ["3.1", "3.2", "3.3", "3.4"] },
    { "id": 14, "tasks": ["3.5", "3.6"] },
    { "id": 15, "tasks": ["4.1"] },
    { "id": 16, "tasks": ["4.2"] },
    { "id": 17, "tasks": ["4.3"] },
    { "id": 18, "tasks": ["4.4"] },
    { "id": 19, "tasks": ["4.5"] },
    { "id": 20, "tasks": ["5.1"] },
    { "id": 21, "tasks": ["5.2"] },
    { "id": 22, "tasks": ["5.3"] },
    { "id": 23, "tasks": ["5.4", "5.5"] },
    { "id": 24, "tasks": ["6.1", "6.2", "6.3", "6.4"] },
    { "id": 25, "tasks": ["6.5"] }
  ]
}
```
