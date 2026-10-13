-- build_job_skills.pig
-- Extracts one row per job-skill pair from clean job postings.
--
-- Usage:
--   pig -param INPUT=/user/hadoop/bigdata/clean_jobs \
--       -param OUTPUT=/user/hadoop/bigdata/job_skills \
--       build_job_skills.pig
--
-- This script tokenizes the skills_required field (comma-separated) and
-- generates a flat job_id, skill_name table.
-- For description-based skill extraction, use the MapReduce job instead.

clean_jobs = LOAD '$INPUT'
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

-- Filter records that have a skills_required field
with_skills = FILTER clean_jobs BY
    (skills_required IS NOT NULL AND skills_required != '');

-- Alternative approach using STRSPLIT for comma-delimited skills
skill_pairs_raw = FOREACH with_skills GENERATE
    job_id,
    job_title,
    FLATTEN(STRSPLIT(skills_required, ',', 0)) AS raw_skill;

-- Trim whitespace and lowercase each skill
skill_pairs = FOREACH skill_pairs_raw GENERATE
    job_id,
    job_title,
    LOWER(TRIM(raw_skill)) AS skill_name;

-- Filter out empty skill tokens
skill_pairs_clean = FILTER skill_pairs BY
    (skill_name IS NOT NULL AND skill_name != '');

-- Deduplicate: each (job_id, skill_name) pair should appear only once
grouped = GROUP skill_pairs_clean BY (job_id, skill_name);
deduped = FOREACH grouped GENERATE
    FLATTEN(group) AS (job_id, skill_name);

-- Store output
STORE deduped INTO '$OUTPUT' USING PigStorage('\t');
