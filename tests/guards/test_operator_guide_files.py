"""The operator guide is a folder of topic files, and nothing names the single file it was."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
GUIDE = ROOT / "docs" / "operator-guide"
OLD_GUIDE = ROOT / "docs" / "operator-guide.md"
TOPIC_FILES = (
    "install.md",
    "agent-runtime.md",
    "machine.md",
    "site.md",
    "cloud-run.md",
    "health.md",
    "stops.md",
    "pipeline.md",
    "records.md",
    "work-items.md",
)
SEARCHED = (
    ROOT / "src",
    ROOT / "claude",
    ROOT / "operator",
    ROOT / "vm",
    ROOT / "docs",
    ROOT / "README.md",
)
NOT_SEARCHED = (ROOT / "docs" / "runs", ROOT / "docs" / "decisions.md")

# Every section heading of the single guide before the split, with how often it appeared.
HEADINGS = (
    ("## Install", 1),
    ("## Configuration", 1),
    ("### A repository URL with a password is refused", 1),
    ("## When the process refuses to start", 1),
    ("## The loop and its pauses", 1),
    ("### The checkout is cloned when it is missing", 1),
    ("## The project's make targets", 1),
    ("### Mutation testing by sweep", 1),
    ("## The agent runtime", 1),
    ("### The agent in a container", 1),
    ("### Behind a proxy", 1),
    ("### The agent run's `PATH` and `HOME`", 1),
    ("### A provider's spend limit", 1),
    ("### An opencode run's budget", 1),
    ("### Running on opencode", 1),
    ("### A company's provider", 1),
    ("### A bearer token for the model API", 1),
    ("## The machine", 1),
    ("### What it is", 1),
    ("### The job profile", 1),
    ("### The metadata server in a job", 1),
    ("### Without ZFS", 1),
    ("### The stage image", 1),
    ("### The project's stage file", 1),
    ("### The image on the cost records", 1),
    ("### The code and the project apart", 1),
    ("### The script", 1),
    ("### The service", 1),
    ("### On GCP, step by step", 1),
    ("### On any Ubuntu 24.04 VM", 1),
    ("### What the container can and cannot see", 1),
    ("### The costs", 1),
    ("### The metadata server", 1),
    ("### Where the logs are", 1),
    ("### The idle shutdown", 1),
    ("### The rebuild after a merge", 1),
    ("## The site file", 1),
    ("### Its place", 1),
    ("### The format", 1),
    ("### The `site` command", 1),
    ("### The keys", 1),
    ("### The token source", 1),
    ("### Sanitising what leaves the machine", 1),
    ("## Repeating a trial", 1),
    ("### Telling Kumpel's acts from the human's", 1),
    ("## Setting up an operator's machine", 1),
    ("### What the platform must provide first", 1),
    ("### The steps", 2),
    ("### The checks", 1),
    ("## On Cloud Run", 1),
    ("### What the job needs", 1),
    ("### The environment", 1),
    ("### Starts, restarts and the end of an execution", 1),
    ("### A free model", 1),
    ("### Creating the job", 1),
    ("### Watching the job", 1),
    ("## The preflight and the health check", 1),
    ("### The hosting-service token", 1),
    ("### The health check", 1),
    ("### The preflight's items", 1),
    ("### The stamp and the probe of the main branch", 1),
    ("### The wait for a repository that is not ready", 1),
    ("## The factory log and the health status file", 1),
    ("### The factory log", 1),
    ("### The health status file", 1),
    ("### The records", 1),
    ("## Transcripts", 1),
    ("### The setting", 1),
    ("### What is kept", 1),
    ("### When one is not kept", 1),
    ("### The site's part", 1),
    ("### On a VM", 1),
    ("### In a Cloud Run job", 1),
    ("## The stops", 1),
    ("### The stops of the repository or the machine", 1),
    ("### The stop records on main", 1),
    ("### The stops of one work item", 1),
    ("## What a stage run shows", 1),
    ("## A stall: the stall note", 1),
    ("## A stall by a red check", 1),
    ("## The factory's own questions", 1),
    ("### Which comment answers a question", 1),
    ("### The reviewer's notes and added criteria", 1),
    ("## The stop `pipeline_definition_invalid`", 1),
    ("## The stop `agent_definition_invalid`", 1),
    ("## The stops of the tick", 1),
    ("### The low disk", 1),
    ("### The preflight in the tick", 1),
    ("## The pipeline definition", 1),
    ("## The agent files", 1),
    ("### A project's own agents", 1),
    ("### A project's own skills", 1),
    ("### The shipped agents and settings", 1),
    ("## The records contract", 1),
    ("## Checking a story before it starts", 1),
    ("## What a work item cost: `factory-bill`", 1),
    ("### The cost table", 1),
    ("### Refused tool calls in the sidecar", 1),
    ("### The machine on the cost records", 1),
    ("### The tool calls on the cost records", 1),
    ("### The cost line", 1),
    ("### An unknown cost", 1),
    ("## Looking at the remote: `factory-watch`", 1),
    ("## When a feature acceptance is due", 1),
    ("## The hand-over at the approval", 1),
    ("### The hand-over of an acceptance", 1),
    ("### When the hand-over fails or is killed", 1),
    ("## A stale branch is deleted by the tick", 1),
    ("## A merge archives the story", 1),
    ("## A close before the approval discards the story", 1),
    ("## A close at the approval sends the story back", 1),
    ("### The reason and the round cap", 1),
    ("### When something fails or is killed", 1),
    ("## Branch deletion on merge must be off", 1),
    ("## An idle tick that is not empty", 1),
    ("## A stage changed by hand", 1),
    ("### What the factory does when it moves a stage back", 1),
    ("### Never edit a running work item on main", 1),
    ("## An event that keeps failing", 1),
    ("### A refused push is tried again", 1),
    ("### During an outage of the hosting service", 1),
    ("## Stops that cannot be done", 1),
    ("## A restart during a stage", 1),
    ("### The crash cap", 1),
    ("## An expired lease", 1),
    ("## Claims, leases and the clock", 1),
    ("## Replaced in v1.2", 1),
    ("## Replaced from v1", 1),
)


def _lines_outside_fences(text: str) -> list[str]:
    lines: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced:
            lines.append(line)
    return lines


def _guide_headings() -> list[str]:
    return [
        line
        for path in sorted(GUIDE.glob("*.md"))
        for line in _lines_outside_fences(path.read_text(encoding="utf-8"))
        if re.match(r"#{2,3} ", line)
    ]


def _searched_files() -> list[Path]:
    files: list[Path] = []
    for place in SEARCHED:
        candidates = [place] if place.is_file() else sorted(place.rglob("*"))
        files.extend(
            path
            for path in candidates
            if path.is_file()
            and "__pycache__" not in path.parts
            and not any(path == skip or skip in path.parents for skip in NOT_SEARCHED)
        )
    return files


def test_the_single_guide_is_gone_and_the_folder_holds_the_index_and_ten_topics() -> None:
    assert not OLD_GUIDE.exists()
    names = sorted(path.name for path in GUIDE.iterdir())
    assert names == sorted(("README.md", *TOPIC_FILES))


@pytest.mark.parametrize(("heading", "count"), HEADINGS)
def test_every_earlier_heading_is_kept_in_the_folder(heading: str, count: int) -> None:
    assert _guide_headings().count(heading) == count


def test_no_file_names_the_single_guide() -> None:
    found = [
        f"{path.relative_to(ROOT)}:{number}"
        for path in _searched_files()
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
        )
        if "docs/operator-guide.md" in line
    ]
    assert found == []
