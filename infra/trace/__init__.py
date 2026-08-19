"""The independent trace suite.

Experiments emit raw logs; this package owns everything downstream: parsing,
clock alignment, bundling, and Perfetto export. No experiment holds trace or
plotting code of its own, and nothing in here knows any experiment by name —
behavior keys on which artifacts a run directory actually contains.
"""
