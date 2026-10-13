-- clean_jobs.pig
-- Cleans and deduplicates raw job postings from HDFS.
--
-- Usage:
--   pig -param INPUT=/user/hadoop/bigdata/raw/job_postings.csv \
--       -param OUTPUT=/user/hadoop/bigdata/clean_jobs \
--       clean_jobs.pig
--
-- NOTE on CSV quoting: PigStorage does NOT handle quoted commas in CSV fields.
-- If the dataset uses quoted commas in description fields, pre-process with
-- a Python/Java UDF or use a CSV SerDe (e.g. org.apache.pig.piggybank.storage.CSVExcelStorage).
-- This script assumes tab-delimited input (exported from Hive or pre-converted).

-- Load raw job postings (tab-delimited schema)
raw_jobs = LOAD '$INPUT'
    USING PigStorage('\t')
    AS (
        job_id:chararray,
        job_title:chararray,
        company:chararray,
        location:chararray,
        salary_range:chararray,
        experience_required:chararray,
        skills_required:chararray,
        description:chararray,
        post_date:chararray
    );

-- Filter records with missing required fields
filtered = FILTER raw_jobs BY
    (job_id IS NOT NULL AND job_id != '') AND
    (job_title IS NOT NULL AND job_title != '') AND
    (description IS NOT NULL AND description != '');

-- Normalize: trim whitespace, lowercase job_title
normalized = FOREACH filtered GENERATE
    TRIM(job_id)               AS job_id,
    LOWER(TRIM(job_title))     AS job_title,
    TRIM(company)              AS company,
    TRIM(location)             AS location,
    TRIM(salary_range)         AS salary_range,
    TRIM(experience_required)  AS experience_required,
    TRIM(skills_required)      AS skills_required,
    TRIM(description)          AS description,
    TRIM(post_date)            AS post_date;

-- Deduplicate by job_id: keep the first occurrence
grouped = GROUP normalized BY job_id;
deduped = FOREACH grouped {
    sorted_by_id = ORDER normalized BY job_id;
    first_only = LIMIT sorted_by_id 1;
    GENERATE FLATTEN(first_only);
};

-- Store clean output (tab-delimited)
STORE deduped INTO '$OUTPUT' USING PigStorage('\t');
