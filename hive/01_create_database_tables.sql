-- =============================================================================
-- 01_create_database_tables.sql
-- HiveQL DDL for the Big Data Job Profile Recruitment Analyzer
-- =============================================================================

-- Create the project database
CREATE DATABASE IF NOT EXISTS bigdata_jobs
COMMENT 'Big Data Job Profile Recruitment Analyzer database'
WITH DBPROPERTIES (
    'creator'     = 'Sahil Goyal',
    'roll_no'     = '11242424',
    'section'     = 'H/H2',
    'created_on'  = '2026-10-13',
    'version'     = '0.1.0'
);

USE bigdata_jobs;

-- =============================================================================
-- Main job postings table (tab-delimited text file)
-- =============================================================================
-- NOTE: PigStorage and this table use tab-delimited format.
-- If your source CSV uses quoted commas in description fields, use the
-- CSV SerDe alternative (see comment block below) or pre-process with Pig/Python.
-- =============================================================================

CREATE TABLE IF NOT EXISTS job_posts (
    job_id               STRING  COMMENT 'Unique job posting identifier',
    job_title            STRING  COMMENT 'Job title (normalized to lowercase)',
    company              STRING  COMMENT 'Hiring company name',
    location             STRING  COMMENT 'Job location (city, state)',
    salary_range         STRING  COMMENT 'Salary range as posted (e.g. 80000-120000)',
    experience_required  STRING  COMMENT 'Experience requirement (e.g. 3-5 years)',
    skills_required      STRING  COMMENT 'Comma-separated list of required skills',
    description          STRING  COMMENT 'Full job description text',
    post_date            STRING  COMMENT 'Date the posting was published'
)
COMMENT 'Raw and cleaned job postings loaded from HDFS'
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
TBLPROPERTIES (
    'skip.header.line.count' = '1',
    'serialization.null.format' = ''
);

-- CSV SerDe alternative (for files with quoted commas in description fields):
-- ADD JAR /path/to/hive-csv-serde.jar;
-- CREATE TABLE job_posts_csv (...)
-- ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
-- WITH SERDEPROPERTIES (
--     "separatorChar" = ",",
--     "quoteChar"     = "\"",
--     "escapeChar"    = "\\"
-- )
-- STORED AS TEXTFILE
-- TBLPROPERTIES ("skip.header.line.count"="1");

-- =============================================================================
-- Job-skill pairs table (output of Pig build_job_skills.pig)
-- =============================================================================

CREATE TABLE IF NOT EXISTS job_skills (
    job_id      STRING  COMMENT 'Job posting identifier (FK to job_posts)',
    job_title   STRING  COMMENT 'Job title for this posting',
    skill_name  STRING  COMMENT 'Canonical skill name (lowercased)'
)
COMMENT 'One row per job-skill pair, extracted from skills_required field'
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE;

-- =============================================================================
-- Skill frequency table (output of MapReduce skill count job)
-- =============================================================================

CREATE TABLE IF NOT EXISTS skill_frequency (
    skill_name  STRING  COMMENT 'Canonical skill name',
    post_count  INT     COMMENT 'Number of distinct job postings requiring this skill'
)
COMMENT 'Aggregate skill counts from MapReduce job'
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE;

-- =============================================================================
-- External table pointing to HDFS raw data (does not move data on DROP)
-- =============================================================================

CREATE EXTERNAL TABLE IF NOT EXISTS job_posts_ext (
    job_id               STRING,
    job_title            STRING,
    company              STRING,
    location             STRING,
    salary_range         STRING,
    experience_required  STRING,
    skills_required      STRING,
    description          STRING,
    post_date            STRING
)
COMMENT 'External table over raw HDFS job postings — safe to drop without deleting data'
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/user/hadoop/bigdata/raw/'
TBLPROPERTIES (
    'skip.header.line.count' = '1'
);

-- =============================================================================
-- Schema evolution example: ADD COLUMNS
-- =============================================================================

-- Example: adding a normalized_title column after initial load
-- ALTER TABLE job_posts ADD COLUMNS (normalized_title STRING COMMENT 'Title after alias normalization');

-- Actual demo (safe to run — adds a nullable column with no data impact):
ALTER TABLE job_posts ADD COLUMNS (
    normalized_title STRING COMMENT 'Normalized job title after alias mapping'
);

-- =============================================================================
-- Demo table: create and immediately drop (shows CREATE/DROP syntax)
-- =============================================================================

CREATE TABLE IF NOT EXISTS demo_drop_test (
    id INT COMMENT 'Demo column'
)
COMMENT 'Temporary demo table — dropped immediately below';

DROP TABLE IF EXISTS demo_drop_test;

-- =============================================================================
-- ALTER DATABASE example
-- =============================================================================

ALTER DATABASE bigdata_jobs SET DBPROPERTIES (
    'last_modified' = '2026-10-13',
    'status'        = 'active'
);
