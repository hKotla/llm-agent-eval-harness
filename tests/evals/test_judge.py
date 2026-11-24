"""Week 3 placeholder. Collection succeeds; the test is skipped on purpose.

TODO(week-3): remove the skip and assert on accuracy, helpfulness, and
groundedness. Use a fake judge so this file still runs without an API key.
"""

import pytest

from evals.judge import Judge


@pytest.mark.skip(reason="TODO(week-3): score accuracy, helpfulness, and groundedness")
def test_judge_returns_three_scores() -> None:
    score = Judge().score(transcript=[], expected={})
    assert score.accuracy is not None
    assert score.helpfulness is not None
    assert score.groundedness is not None
