# Hive UDFs — Notes and Examples

## What are Hive UDFs?

A Hive **User-Defined Function (UDF)** lets you extend HiveQL with custom logic that the
built-in functions do not cover. Common use cases in this project include:

- Normalizing raw job titles against the `title_aliases.csv` mapping
- Matching free-text skill mentions against the skills dictionary
- Parsing non-standard date or salary formats

Hive supports three UDF types:

| Type | Class to extend | Use case |
|------|----------------|----------|
| UDF | `org.apache.hadoop.hive.ql.exec.UDF` | One input row → one output value |
| UDAF | `org.apache.hadoop.hive.ql.udf.generic.AbstractGenericUDAFResolver` | Aggregation (like COUNT/SUM) |
| UDTF | `org.apache.hadoop.hive.ql.udf.generic.GenericUDTF` | One input row → multiple output rows |

---

## Writing a Simple Java UDF

### Example: Skill Normalization UDF

This UDF looks up a raw skill string in the skills dictionary and returns its canonical name.

```java
package com.bigdata.udf;

import org.apache.hadoop.hive.ql.exec.UDF;
import org.apache.hadoop.io.Text;
import java.util.HashMap;
import java.util.Map;

/**
 * SkillNormalizer — maps raw skill aliases to canonical skill names.
 * Usage in HiveQL: SELECT normalize_skill(raw_skill) FROM job_skills;
 */
public class SkillNormalizer extends UDF {

    // In a production UDF, load this map from a distributed cache file.
    // For illustration, a small inline map is shown here.
    private static final Map<String, String> ALIAS_MAP = new HashMap<>();
    static {
        ALIAS_MAP.put("pyspark",      "Spark");
        ALIAS_MAP.put("apache spark", "Spark");
        ALIAS_MAP.put("sklearn",      "scikit-learn");
        ALIAS_MAP.put("scikit learn", "scikit-learn");
        ALIAS_MAP.put("tensorflow",   "TensorFlow");
        ALIAS_MAP.put("tf",           "TensorFlow");
        // ... add all aliases from config/skills_dictionary.csv
    }

    /**
     * Evaluate: normalize one skill string.
     * @param rawSkill the raw skill text (e.g. "pyspark")
     * @return canonical skill name (e.g. "Spark"), or the original if not found
     */
    public Text evaluate(Text rawSkill) {
        if (rawSkill == null) return null;
        String lower = rawSkill.toString().trim().toLowerCase();
        String canonical = ALIAS_MAP.getOrDefault(lower, rawSkill.toString().trim());
        return new Text(canonical);
    }
}
```

### Building the JAR

```bash
# Compile (assumes hive-exec jar is on classpath)
javac -cp /path/to/hive/lib/hive-exec-*.jar SkillNormalizer.java
jar cf skill-normalizer-udf.jar SkillNormalizer.class
```

---

## Registering and Using the UDF in Hive

### Temporary function (session-scoped)

```sql
-- Add the JAR to the current session
ADD JAR /path/to/skill-normalizer-udf.jar;

-- Create a temporary function (gone when session ends)
CREATE TEMPORARY FUNCTION normalize_skill
    AS 'com.bigdata.udf.SkillNormalizer';

-- Use it
SELECT job_id, normalize_skill(skill_name) AS canonical_skill
FROM job_skills;
```

### Permanent function (persists across sessions — Hive 0.13+)

```sql
-- Register permanently in the Hive metastore
CREATE FUNCTION bigdata_jobs.normalize_skill
    AS 'com.bigdata.udf.SkillNormalizer'
    USING JAR 'hdfs:///user/hadoop/udf/skill-normalizer-udf.jar';

-- Drop when no longer needed
DROP FUNCTION IF EXISTS bigdata_jobs.normalize_skill;
```

---

## Using Python UDFs (TRANSFORM clause)

When the logic is easier to write in Python than Java, use Hive's `TRANSFORM` clause
to pipe rows through a Python script:

```sql
-- Example: normalize job titles using Python logic
ADD FILE /path/to/normalize_title.py;

SELECT
    TRANSFORM(job_id, job_title)
    USING 'python3 normalize_title.py'
    AS (job_id STRING, normalized_title STRING)
FROM job_posts;
```

**When to prefer Python UDFs:**
- Rapid prototyping — no compile/package step
- Complex string logic already written in Python (e.g., regex-based skill matching)
- When the UDF needs to load a config file (distribute via `ADD FILE`)

**When to prefer Java UDFs:**
- Performance-critical aggregations (Java avoids the inter-process serialization overhead)
- When the UDF needs to be registered as a permanent function in the Hive metastore
- Enterprise environments that restrict `TRANSFORM` for security reasons

---

## Loading Alias Maps from Distributed Cache

For a production-quality skill normalization UDF, load `config/skills_dictionary.csv`
from the Hive distributed cache rather than hardcoding aliases:

```sql
ADD FILE hdfs:///user/hadoop/bigdata/config/skills_dictionary.csv;
```

Then in the UDF constructor, read the file from the local working directory
(Hadoop copies distributed cache files to each task node's working directory).
