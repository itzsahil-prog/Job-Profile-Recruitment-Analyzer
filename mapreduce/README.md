# MapReduce — Skill Frequency Counter

This directory contains the Hadoop Streaming mapper and reducer for counting
how many distinct job postings require each skill.

## Purpose

The skill-frequency MapReduce job reads raw job posting CSV records and emits
`skill_name<TAB>count` pairs indicating how many job postings mention each skill.

**Default mode (distinct posts):** Each skill is counted at most once per job posting,
so the output represents the number of job postings that require a skill — not the
number of times the skill appears in text.

**Mentions mode (`--mentions` flag):** Each occurrence of a skill in the text is counted,
giving total mention frequency.

## Inputs

- Raw job postings CSV uploaded to HDFS (one record per line, CSV format)
- `config/skills_dictionary.csv` — skill names and aliases (distributed to all nodes via `-files`)

## Outputs

HDFS directory containing `part-*` files with two tab-separated columns:

```
skill_name<TAB>count
```

Sorted by count descending.

## How to Run

See `run_skill_count.sh` for the full Hadoop Streaming command. Quick summary:

```bash
# Ensure HADOOP_HOME is set and Python 3 is on all nodes
bash mapreduce/run_skill_count.sh
```

Fetch results after the job completes:

```bash
hadoop fs -cat /user/hadoop/bigdata/skill_counts/part-* | sort -t$'\t' -k2 -rn | head -30
```

## Files

| File | Description |
|------|-------------|
| `mapper.py` | Reads CSV records from stdin, emits `skill<TAB>1` per detected skill |
| `reducer.py` | Aggregates counts per skill, outputs sorted `skill<TAB>count` |
| `run_skill_count.sh` | Hadoop Streaming shell script template |

## Requirements

- Hadoop installed, `HADOOP_HOME` set
- Python 3 available on all cluster nodes
- `config/skills_dictionary.csv` accessible (distributed via `-files` option)
