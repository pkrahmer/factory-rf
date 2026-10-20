"""The opencode stand-in's reply and waiting steps are written in its module alone."""

import re
from pathlib import Path

import pytest

from search_support import modules_matching

# The texts below are split so that a search of `tests` for them finds only their one module.
THIS = Path(__file__).name
STAND_IN = "adapters/opencode_stand_in.py"


@pytest.mark.parametrize(
    "step",
    [
        pytest.param("stdout(step_start(), " + "text(result_text()), step_finish())", id="reply"),
        pytest.param(
            "Step(stdout_before_wait=stdout(step_start()), " + "wait_seconds=WAIT_SECONDS)",
            id="waiting",
        ),
    ],
)
def test_each_opencode_step_is_written_in_the_stand_in_module_alone(step: str) -> None:
    assert modules_matching(re.escape(step), THIS) == [STAND_IN]
