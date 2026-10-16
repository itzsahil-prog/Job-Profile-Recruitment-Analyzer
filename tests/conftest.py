"""
conftest.py — pytest configuration for the tests package.

Adds the mapreduce/ directory to sys.path so that `import mapper` and
`import reducer` work regardless of how pytest is invoked.
"""

import os
import sys

# Ensure mapreduce/ is on the path before any test module is imported.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mapreduce'))
