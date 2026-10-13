# data/ — Raw Input Dataset

This directory holds the raw job postings dataset used by the pipeline.

## Important: Large files are git-ignored

CSV files in this directory (other than files named `sample*.csv`) are excluded
from git by `.gitignore`. Do NOT commit large datasets to this repository.

## Recommended Dataset

Search Kaggle for a job postings dataset, for example:

- **Data Science Job Posting on Glassdoor**
  https://www.kaggle.com/datasets/andrewmvd/data-science-job-posting-on-glassdoor

- **Job Listings Dataset** — any similar dataset with job titles, descriptions, and skills

Download the CSV and place it in this directory.

## Expected Columns

The pipeline works best when the CSV contains these logical fields
(column names do not need to match exactly — `validate_dataset.py` performs fuzzy schema mapping):

| Logical Field | Description |
|--------------|-------------|
| `job_id` | Unique job posting identifier (or row index) |
| `job_title` | Job title text |
| `company` | Hiring company name |
| `location` | City and/or state |
| `salary_range` | Salary range as posted |
| `experience_required` | Experience requirement |
| `skills_required` | Comma-separated required skills |
| `description` | Full job description text |
| `post_date` | Date the posting was published |

## After Placing the Dataset

Run validation first:

```bash
python analytics/validate_dataset.py --input data/<filename>.csv
```

Review the report at `outputs/data_quality_report.json` before proceeding.

## Sample Data

A tiny synthetic sample file (`data/sample_5rows.csv`) may be placed here for
offline testing of the Python analytics scripts. This sample is NOT real data
and is committed to git (the `.gitignore` rule `!data/sample*.csv` permits it).
