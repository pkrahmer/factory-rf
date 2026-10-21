"""The watcher reports a refused agent file without touching a stop."""

import io
from pathlib import Path

from factory.application.boundaries import Boundaries
from factory.entry.watch import run_watch
from git_support import COLOURED_AGENT_FILE, PIPELINE_YAML, install_agents, write_agent
from stage_run_support import INSTANCE

ROLE = "coder"


def test_a_refused_agent_file_is_reported_without_a_stop(
    boundaries: Boundaries, agent_home: Path
) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    write_agent(agent_home, ROLE, COLOURED_AGENT_FILE)
    before = boundaries.health.read()
    out, err = io.StringIO(), io.StringIO()

    status = run_watch(boundaries, INSTANCE, out, err)

    assert status == 1
    assert err.getvalue() == (
        f"factory-watch: agent {ROLE}: key not applied by the agent runtime: colour\n"
    )
    assert out.getvalue() == ""
    assert boundaries.health.read() == before
