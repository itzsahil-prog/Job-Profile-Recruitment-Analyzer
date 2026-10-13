# Pipeline Plan

## Stage order
1. Fix validate_dataset.py for chunked reading on real schema
2. Fix mapreduce/mapper.py to read Job Description + skills columns explicitly
3. Create local_sim/run_mapreduce.py
4. Create local_sim/run_pig_cleaning.py
5. Create local_sim/run_pig_job_skills.py
6. Create local_sim/run_hive_analytics.py
7. Fix analytics/build_vectors.py (sampling + skill_groups arg optional)
8. Fix analytics/cluster_job_families.py (add family_label, elbow eval output)
9. Fix analytics/cluster_skill_groups.py (add group_label, summary)
10. Fix analytics/build_competence_matrix.py (already good)
11. Fix analytics/visualize.py (update file path references)
12. Run entire pipeline end-to-end
13. Run pytest and fix failures
14. Update all checkpoint docs

## Column mapping
- Job Id -> job_id
- Job Title -> job_title
- Job Description -> description
- skills -> skills (explicit skills field)
- Experience -> experience_required
- Company -> company
- location + Country -> location

## Critical rules
- Always use chunksize=50000 for reading the 1.6M row dataset
- Sample 200k rows max for clustering (sort by Job Id, take first 200k)
- Never fabricate outputs
- Keep mapreduce/, pig/, hive/ scripts intact
