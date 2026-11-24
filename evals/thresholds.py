"""Quality-gate thresholds.

TODO(week-5): set these from a baseline run, then fail CI when a score drops
below them. None means "not enforced yet".
"""

ACCURACY_MIN: float | None = None
HELPFULNESS_MIN: float | None = None
GROUNDEDNESS_MIN: float | None = None
