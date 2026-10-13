-- =============================================================================
-- 04_index_version_demo.sql
-- HIVE VERSION COMPATIBILITY NOTE
--
-- This file demonstrates index syntax differences between Hive 2.x and 3.x.
-- Hive 3.x REMOVED the CREATE INDEX / DROP INDEX commands entirely.
-- Choose the correct section for your environment.
-- =============================================================================

USE bigdata_jobs;

-- =============================================================================
-- HIVE 2.x — CREATE INDEX (supported in Hive 0.7 through 2.x)
-- =============================================================================
-- Hive 2.x supports bitmap and compact indexes on table columns.
-- Indexes speed up WHERE and JOIN predicates on indexed columns by storing
-- a compact column-to-block mapping in a separate index table.
--
-- IMPORTANT: Hive indexes are NOT automatically maintained — you must
-- REBUILD the index after loading new data.
-- =============================================================================

-- Create a compact index on skill_name in the job_skills table
-- (Hive 2.x only — will FAIL on Hive 3.x)
/*
CREATE INDEX idx_skill_name
    ON TABLE job_skills (skill_name)
    AS 'org.apache.hadoop.hive.ql.index.compact.CompactIndexHandler'
    WITH DEFERRED REBUILD
    IDXPROPERTIES ('creator' = 'Sahil Goyal', 'created_on' = '2026-10-13')
    IN TABLE job_skills_skill_name_idx
    COMMENT 'Compact index on skill_name for faster skill lookup queries';

-- Rebuild the index after data load
ALTER INDEX idx_skill_name ON job_skills REBUILD;

-- Show all indexes on the table
SHOW FORMATTED INDEX ON job_skills;

-- Drop the index when no longer needed
DROP INDEX IF EXISTS idx_skill_name ON job_skills;
*/

-- =============================================================================
-- HIVE 3.x — Indexes REMOVED; use these alternatives instead
-- =============================================================================
-- Hive 3.x dropped CREATE INDEX because modern file formats (ORC, Parquet)
-- provide built-in statistics, bloom filters, and min/max indexes that
-- outperform the legacy index mechanism.
--
-- Recommended alternatives:
--   1. Partitioning — prune entire partitions at query planning time
--   2. ORC file format — column statistics, min/max, bloom filters built-in
--   3. Bloom filter table properties — per-column probabilistic filtering
--   4. Materialized views (Hive 3.0+) — pre-computed query results
-- =============================================================================

-- ALTERNATIVE 1: Partitioned table (partition pruning replaces index scans)
-- Partition job_skills by a high-cardinality filter column (e.g., post year)
CREATE TABLE IF NOT EXISTS job_skills_partitioned (
    job_id      STRING COMMENT 'Job posting identifier',
    job_title   STRING COMMENT 'Job title',
    skill_name  STRING COMMENT 'Canonical skill name'
)
COMMENT 'job_skills partitioned by post year for efficient time-range queries'
PARTITIONED BY (post_year INT COMMENT 'Year the job was posted')
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
STORED AS ORC
TBLPROPERTIES (
    'orc.compress' = 'SNAPPY'
);

-- Enable dynamic partitioning for bulk loads
-- SET hive.exec.dynamic.partition = true;
-- SET hive.exec.dynamic.partition.mode = nonstrict;

-- ALTERNATIVE 2: ORC table with bloom filter index (Hive 3.x)
-- Bloom filters efficiently answer "does this value exist in this stripe?"
CREATE TABLE IF NOT EXISTS job_skills_orc (
    job_id      STRING COMMENT 'Job posting identifier',
    job_title   STRING COMMENT 'Job title',
    skill_name  STRING COMMENT 'Canonical skill name'
)
COMMENT 'job_skills stored as ORC with bloom filter on skill_name'
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
STORED AS ORC
TBLPROPERTIES (
    'orc.compress'                  = 'SNAPPY',
    'orc.create.index'              = 'true',
    -- Bloom filter on skill_name: reduces I/O for equality predicates
    'orc.bloom.filter.columns'      = 'skill_name',
    'orc.bloom.filter.fpp'          = '0.05'   -- 5% false-positive rate
);

-- ALTERNATIVE 3: Materialized view (Hive 3.0+)
-- Pre-compute the top-skills aggregation for fast dashboard queries.
/*
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_skill_counts
DISABLE REWRITE    -- enable REWRITE on Hive 3.2+ with ACID tables
AS
SELECT
    skill_name,
    COUNT(DISTINCT job_id) AS post_count
FROM job_skills
GROUP BY skill_name;

-- Rebuild the materialized view after new data is loaded
ALTER MATERIALIZED VIEW mv_skill_counts REBUILD;

-- Drop the materialized view
DROP MATERIALIZED VIEW IF EXISTS mv_skill_counts;
*/

-- =============================================================================
-- SUMMARY: Which Hive version are you on?
-- =============================================================================
-- | Feature                    | Hive 2.x | Hive 3.x |
-- |----------------------------|----------|----------|
-- | CREATE INDEX               |    YES   |    NO    |
-- | ORC bloom filter           |    YES   |    YES   |
-- | Partitioning               |    YES   |    YES   |
-- | Materialized views         |    NO    |    YES   |
-- | ACID transactions (full)   | partial  |    YES   |
-- =============================================================================
