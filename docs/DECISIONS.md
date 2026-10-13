# Design Decisions — Big Data Job Profile Recruitment Analyzer

## DD-001: Duplicate Policy
**Decision:** Keep first occurrence by job_id when duplicates exist.
**Rationale:** The job_id is the canonical identifier; later records with the same id likely represent
re-postings or data feed errors. Keeping the first occurrence is reproducible and deterministic.

## DD-002: Count Semantics
**Decision:** Use distinct-post count — each skill counted at most once per job posting.
**Rationale:** Prevents description verbosity from inflating counts. Frequency reflects
breadth (how many jobs require the skill) not depth (how often it appears in text).

## DD-003: Competence Thresholds
**Decision:** Low <20%, Medium 20%-<50%, High ≥50%.
**Rationale:** These thresholds yield meaningful three-tier differentiation across typical
job posting datasets. Documented to allow recalibration with real data.

## DD-004: Random Seed
**Decision:** random_state=42 for all k-means runs.
**Rationale:** Reproducibility. All cluster assignments in reports must be generated
with this seed.

## DD-005: Skill Matching Strategy
**Decision:** Word-boundary regex matching, case-insensitive.
**Rationale:** Prevents false positives (e.g., matching 'R' inside 'Recruiter').
Word-boundary (negative lookbehind/lookahead for \w) catches standalone tokens
and multi-word phrases without requiring full tokenization.

## DD-006: Hive Index Compatibility
**Decision:** Index syntax demonstrated for Hive 2.x only; Hive 3.x section documents
partitioning and ORC bloom filters as the modern alternative.
**Rationale:** Hive 3.x removed CREATE INDEX; documenting both versions prevents
confusion and shows understanding of version differences.

## DD-007: Missing Experience Values
**Decision:** Missing experience_required values are kept as-is (NULL/empty), NOT
converted to zero.
**Rationale:** Zero years experience has a specific meaning (entry-level) that is
distinct from missing data. Imputing zero would introduce false signal.
