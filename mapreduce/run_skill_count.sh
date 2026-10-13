#!/bin/bash
# run_skill_count.sh — Template for running the skill-frequency MapReduce job
# via Hadoop Streaming.
#
# PREREQUISITES:
#   - Hadoop is installed and HADOOP_HOME is set
#   - Python 3 is available on all cluster nodes
#   - config/skills_dictionary.csv has been uploaded to HDFS or is accessible
#
# ADJUST the following variables for your environment:

HADOOP_STREAMING_JAR="${HADOOP_HOME}/share/hadoop/tools/lib/hadoop-streaming-*.jar"
INPUT_PATH="/user/hadoop/bigdata/raw/job_postings.csv"
OUTPUT_PATH="/user/hadoop/bigdata/skill_counts"
MAPPER="mapreduce/mapper.py"
REDUCER="mapreduce/reducer.py"
SKILLS_DICT="config/skills_dictionary.csv"

# Remove output path if it exists
hadoop fs -rm -r -f "${OUTPUT_PATH}"

hadoop jar ${HADOOP_STREAMING_JAR} \
  -files "${MAPPER}","${REDUCER}","${SKILLS_DICT}" \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py" \
  -input "${INPUT_PATH}" \
  -output "${OUTPUT_PATH}" \
  -cmdenv PYTHONIOENCODING=utf-8

echo "Job finished. Fetch results with:"
echo "  hadoop fs -cat ${OUTPUT_PATH}/part-* | sort -t$'\t' -k2 -rn | head -30"
