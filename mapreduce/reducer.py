#!/usr/bin/env python3
"""
reducer.py — Hadoop Streaming reducer for skill-frequency counting.

Reads sorted key<TAB>value pairs from stdin (output of mapper.py).
Aggregates counts per skill and outputs skill<TAB>count, sorted by count descending.
"""

import sys
from collections import defaultdict


def aggregate(lines):
    """
    Aggregate skill counts from an iterable of tab-separated lines.

    Parameters
    ----------
    lines : iterable of str
        Each line should be "skill<TAB>count". Malformed lines are skipped.

    Returns
    -------
    dict
        Mapping of skill name -> total count.
    """
    counts = defaultdict(int)
    for line in lines:
        line = line.rstrip('\n')
        if not line:
            continue
        parts = line.split('\t', 1)
        if len(parts) != 2:
            continue
        skill, count_str = parts
        try:
            counts[skill] += int(count_str)
        except ValueError:
            continue
    return counts


def main():
    """Entry point for Hadoop Streaming reducer."""
    counts = aggregate(sys.stdin)

    # Output sorted by count descending, then skill name ascending for stability
    for skill, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"{skill}\t{count}")


if __name__ == '__main__':
    main()
