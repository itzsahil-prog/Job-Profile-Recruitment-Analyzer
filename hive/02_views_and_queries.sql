-- =============================================================================
-- 02_views_and_queries.sql
-- HiveQL analytics views and queries for the Job Profile Recruitment Analyzer
-- =============================================================================

USE bigdata_jobs;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Top 50 skills by distinct post count
CREATE VIEW IF NOT EXISTS top_skills AS
SELECT
    skill_name,
    COUNT(DISTINCT job_id) AS post_count
FROM job_skills
GROUP BY skill_name
ORDER BY post_count DESC
LIMIT 50;

-- Demo: create a view then drop it (shows both syntaxes)
CREATE VIEW IF NOT EXISTS test_view_to_drop AS
SELECT 1 AS dummy_col;

DROP VIEW IF EXISTS test_view_to_drop;

-- =============================================================================
-- ANALYTICS QUERIES
-- =============================================================================

-- Q1: Top 20 skills by number of job postings
SELECT
    skill_name,
    COUNT(DISTINCT job_id) AS post_count
FROM job_skills
GROUP BY skill_name
ORDER BY post_count DESC
LIMIT 20;

-- Q2: Skills demanded per job title (top skill per title)
SELECT
    job_title,
    skill_name,
    COUNT(DISTINCT job_id) AS post_count
FROM job_skills
GROUP BY job_title, skill_name
ORDER BY job_title ASC, post_count DESC;

-- Q3: Posting distribution by location
SELECT
    location,
    COUNT(DISTINCT job_id) AS posting_count
FROM job_posts
WHERE location IS NOT NULL AND location != ''
GROUP BY location
ORDER BY posting_count DESC
LIMIT 30;

-- Q4: Posting distribution by salary range
SELECT
    salary_range,
    COUNT(DISTINCT job_id) AS posting_count
FROM job_posts
WHERE salary_range IS NOT NULL AND salary_range != ''
GROUP BY salary_range
ORDER BY posting_count DESC
LIMIT 20;

-- Q5: Skill co-occurrence (skills that appear together in job postings)
-- Self-join on job_skills to find pairs
SELECT
    a.skill_name    AS skill_a,
    b.skill_name    AS skill_b,
    COUNT(DISTINCT a.job_id) AS co_occurrence_count
FROM job_skills a
JOIN job_skills b
    ON  a.job_id     = b.job_id
    AND a.skill_name < b.skill_name   -- avoid duplicates and self-pairs
GROUP BY a.skill_name, b.skill_name
HAVING COUNT(DISTINCT a.job_id) > 5  -- filter to meaningful pairs
ORDER BY co_occurrence_count DESC
LIMIT 50;

-- Q6: Competence matrix support query
-- Counts distinct job postings per (job_family, skill_group) cell.
-- Requires:
--   job_family_assignments table: job_id, job_family  (from Python clustering output)
--   skill_group_assignments table: canonical_skill, skill_group  (from Python clustering output)
--
-- After loading these tables into Hive:
SELECT
    fa.job_family,
    sg.skill_group,
    COUNT(DISTINCT js.job_id) AS posts
FROM job_skills js
JOIN job_family_assignments fa
    ON js.job_id      = fa.job_id
JOIN skill_group_assignments sg
    ON js.skill_name  = sg.canonical_skill
GROUP BY fa.job_family, sg.skill_group
ORDER BY fa.job_family, sg.skill_group;

-- =============================================================================
-- BUILT-IN FUNCTION DEMONSTRATIONS
-- =============================================================================

-- LOWER(): normalize skill names to lowercase for consistent matching
SELECT LOWER(skill_name) AS skill_lower, COUNT(*) AS cnt
FROM job_skills
GROUP BY LOWER(skill_name)
ORDER BY cnt DESC
LIMIT 10;

-- SPLIT(): split skills_required string into an array of individual skills
SELECT
    job_id,
    SPLIT(skills_required, ',') AS skills_array
FROM job_posts
WHERE skills_required IS NOT NULL
LIMIT 5;

-- COUNT() with DISTINCT: count unique job IDs per skill
SELECT
    skill_name,
    COUNT(DISTINCT job_id)  AS unique_postings,
    COUNT(job_id)           AS total_occurrences
FROM job_skills
GROUP BY skill_name
ORDER BY unique_postings DESC
LIMIT 15;
