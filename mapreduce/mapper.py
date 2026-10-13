#!/usr/bin/env python3
"""
mapper.py — Hadoop Streaming mapper for skill-frequency counting.

Reads job posting records from stdin (CSV format, one record per line).
Emits: skill_name<TAB>1 for each skill detected in each posting.

By default uses DISTINCT mode: each skill emitted at most once per posting.
With --mentions flag: emits once per mention (total frequency, not post count).

Skill detection uses word-boundary regex matching (case-insensitive) to avoid
false positives (e.g. 'R' is not matched inside 'Recruiter').
"""

import sys
import csv
import re
import os
import argparse

SKILLS_DICT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'config', 'skills_dictionary.csv'
)


def load_skill_patterns(dict_path):
    """
    Load skill dictionary and compile word-boundary regex patterns.
    Returns list of (canonical_skill, compiled_pattern) tuples.
    """
    patterns = []
    try:
        with open(dict_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                canonical = row['canonical_skill'].strip()
                aliases_raw = row.get('aliases', '')
                # Build list of terms to match: canonical + all aliases
                terms = [canonical]
                if aliases_raw:
                    terms += [a.strip() for a in aliases_raw.split(',') if a.strip()]
                # Compile a single pattern for all terms of this skill
                # Use word boundaries; escape special regex chars
                escaped = [re.escape(t) for t in terms]
                # Sort by length descending so longer phrases match first
                escaped.sort(key=len, reverse=True)
                combined = '|'.join(escaped)
                pattern = re.compile(r'(?i)(?<![\w])(' + combined + r')(?![\w])')
                patterns.append((canonical, pattern))
    except FileNotFoundError:
        print(f"ERROR: Skills dictionary not found at {dict_path}", file=sys.stderr)
        sys.exit(1)
    return patterns


def detect_skills(text, patterns, distinct=True):
    """
    Given a text string and skill patterns, return list of matched canonical skills.
    If distinct=True, each skill appears at most once.
    """
    found = []
    seen = set()
    for canonical, pattern in patterns:
        matches = pattern.findall(text)
        if matches:
            if distinct:
                if canonical not in seen:
                    found.append(canonical)
                    seen.add(canonical)
            else:
                found.extend([canonical] * len(matches))
    return found


def main():
    """Entry point for Hadoop Streaming mapper."""
    parser = argparse.ArgumentParser(description='Hadoop Streaming mapper for skill frequency')
    parser.add_argument('--mentions', action='store_true',
                        help='Count total mentions instead of distinct posts')
    # Parse known args; Hadoop may pass extra args
    args, _ = parser.parse_known_args()

    patterns = load_skill_patterns(SKILLS_DICT_PATH)
    distinct = not args.mentions

    reader = csv.reader(sys.stdin)
    for row in reader:
        if not row:
            continue
        # Concatenate all fields to search for skills
        # Typically description is a specific field; concatenate all for robustness
        text = ' '.join(field for field in row if field)
        if not text.strip():
            continue
        skills = detect_skills(text, patterns, distinct=distinct)
        for skill in skills:
            print(f"{skill}\t1")


if __name__ == '__main__':
    main()
