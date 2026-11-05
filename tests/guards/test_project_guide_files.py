"""The project guide has one file per area, and nothing names a file it lost."""

import re
from pathlib import Path

import pytest

from support.guide_files_support import guide_headings, lines_outside_fences, searched_files

ROOT = Path(__file__).parents[2]
GUIDE = ROOT / "docs" / "project-guide"
AREA_FILES = (
    "shared.md",
    "hosting.md",
    "work.md",
    "agents.md",
    "watching.md",
    "machine.md",
    "pipeline.md",
)
NAMED_FILES = (*AREA_FILES, "operator.md")
REMOVED_FILES = (
    "git-and-hosting.md",
    "work-items.md",
    "write-paths.md",
    "costs.md",
    "stages.md",
    "stage-environment.md",
    "processes-and-checks.md",
)
SEARCHED = (ROOT / "claude", ROOT / "docs", ROOT / "README.md")
NOT_SEARCHED = (
    ROOT / "docs" / "runs",
    ROOT / "docs" / "decisions.md",
    ROOT / "docs" / "operator-guide",
)

# Every section heading of the guide before the regrouping, with how often it
# appeared; the index's own "The files" is left out.
HEADINGS = (
    ("## The code's layout", 1),
    ("## Shared test helpers", 1),
    ("## Errors", 1),
    ("## The models' configuration", 1),
    ("## Kill points", 1),
    ("### The kill-point cases", 1),
    ("## Fault-injection paths", 1),
    ("## The agent runtime", 1),
    ("### The `claude -p` runtime", 1),
    ("### Calls in a container", 1),
    ("### The shared launch module", 1),
    ("### The agent's home", 1),
    ("### The opencode runtime", 1),
    ("### Ending the agent's leftover processes", 1),
    ("### The fake", 2),
    ("## The agent definition reader", 1),
    ("### A project's own agents", 1),
    ("### Faults", 4),
    ("## The shipped agents, settings and template", 1),
    ("### The seven agents", 1),
    ("### The settings", 1),
    ("### The template", 1),
    ("## Replaced in v1.2", 3),
    ("## Replaced from v1", 1),
    ("## Cost records", 1),
    ("### When a record is created, completed and committed", 1),
    ("## Bills", 1),
    ("### The human's waits", 1),
    ("### No code reads data from the journal's text", 1),
    ("## The hosting service", 1),
    ("### The PyGithub client", 1),
    ("### Data", 1),
    ("### The marker and the post key", 1),
    ("## The git wrapper", 1),
    ("### Deleting and merging branches", 1),
    ("### Restoring the checkout", 1),
    ("### Which part uses which operation", 1),
    ("## The layout", 1),
    ("## The site file and its loader", 1),
    ("## The hosting client", 1),
    ("## `job.sh`", 1),
    ("## The sanitiser", 1),
    ("## The skill's scripts", 1),
    ("## Tests of the scripts", 1),
    ("## Project commands", 1),
    ("## Starting a process", 1),
    ("## The duplicates report", 1),
    ("### The keys", 1),
    ("### The baseline", 1),
    ("### The output and the exit status", 1),
    ("## The document check", 1),
    ("## The demos", 1),
    ("## Mutation testing", 1),
    ("## The cycle", 1),
    ("## The snapshots", 1),
    ("## The container runs", 1),
    ("## The copy snapshots", 1),
    ("## The fakes", 1),
    ("## The ZFS adapter", 1),
    ("### The commands", 1),
    ("### Reading `zfs diff -FH`", 1),
    ("### For the preflight", 2),
    ("### The stand-in", 2),
    ("## The podman adapter", 1),
    ("### The command line", 1),
    ("### The job profile", 1),
    ("### The grace", 1),
    ("### Reading the end", 1),
    ("## The stage environment", 1),
    ("### The three operations", 1),
    ("### Who calls what", 1),
    ("### The sync time limit", 1),
    ("### One environment per runner", 1),
    ("## The container environment", 1),
    ("### `prepare`", 1),
    ("### What a fault leaves behind", 1),
    ("### `run_agent`", 1),
    ("### `take`", 1),
    ("### The timing line", 1),
    ("### Wiring and tests", 1),
    ("## The sync command", 1),
    ("## The agent's container", 1),
    ("## The take", 1),
    ("### The seven steps", 1),
    ("### copy_changed", 1),
    ("### Errors", 1),
    ("## The checks", 1),
    ("## The settings and the wiring", 1),
    ("## The project's stage image", 1),
    ("## The preflight", 1),
    ("## The claim service", 1),
    ("## The pipeline definition", 1),
    ("### The rules of the definition", 1),
    ("### The pipeline loader", 1),
    ("## The prompt and the request for a stage", 1),
    ("### The decisions", 1),
    ("### The prompt", 1),
    ("### The request", 1),
    ("### The story form check", 1),
    ("## Opening a work item", 1),
    ("### `prepare(work_item, path)`", 1),
    ("### `ensure_pull_request(work_item, document)`", 1),
    ("## Starting a stage", 1),
    ("## Stalls", 1),
    ("### The reasons", 1),
    ('### `StallService.stall(context, reason, detail="")`', 1),
    ("## After the agent run", 1),
    ("## The decision rules", 1),
    ("## The stage protocol", 1),
    ("### `StageFinisher.finish(aftermath)`", 1),
    ("## The evaluation", 1),
    ("### The event", 1),
    ("### The four tiers", 1),
    ("### The move rule", 1),
    ("### The watcher's command line", 1),
    ("## The tick", 1),
    ("## The handlers of the events", 1),
    ("### Asking the human", 1),
    ("### Recording the human's act", 1),
    ("### The merge archives the story", 1),
    ("### A close before the approval discards the story", 1),
    ("### A close at the approval sends the story back", 1),
    ("### A comment can end a wait", 1),
    ("### The hand-over at the approval", 1),
    ("### An illegal stage change is put back", 1),
    ("### A stop with no work to do is an error", 1),
    ("### Comments are copied by id", 1),
    ("## Stops, the clock and the factory log", 1),
    ("### Boundaries", 1),
    ("### The idle shutdown", 1),
    ("## Identity, order and places of work items", 1),
    ("### Ids and names", 1),
    ("### Order", 1),
    ("### The tree", 1),
    ("## The data of a work item", 1),
    ("### The state", 1),
    ("### The claim", 1),
    ("### The journal's data", 1),
    ("### The journal's entries", 1),
    ("### The feature acceptance", 1),
    ("### The document and its error", 1),
    ("### The remote's work items", 1),
    ("### The records contract", 1),
    ("## Reading and writing a work item file", 1),
    ("### The layout", 1),
    ("### The body", 1),
    ("## Sections of a Markdown body", 1),
    ("## The form check of a story", 1),
    ("### Where a story sits", 1),
    ("### The check command", 1),
    ("## The write paths", 1),
    ("### Where they come from", 1),
    ("### Matching and placeholders", 1),
    ("### Protected paths and the refusal", 1),
    ("## The take's rule", 1),
    ("### What is left out", 1),
    ("### The work item", 1),
    ("### The sidecar", 1),
    ("### Limits", 1),
)


def _the_files_section() -> list[str]:
    lines = lines_outside_fences((GUIDE / "README.md").read_text(encoding="utf-8"))
    start = lines.index("## The files") + 1
    section: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        section.append(line)
    return section


def test_the_guide_holds_the_index_operator_and_the_seven_area_files() -> None:
    names = sorted(path.name for path in GUIDE.iterdir())
    assert names == sorted(("README.md", *NAMED_FILES))


@pytest.mark.parametrize(("heading", "count"), HEADINGS)
def test_every_earlier_heading_is_kept_as_often_as_before(heading: str, count: int) -> None:
    assert guide_headings(GUIDE).count(heading) == count


@pytest.mark.parametrize("name", NAMED_FILES)
def test_the_index_names_each_file_with_a_sentence(name: str) -> None:
    pattern = re.compile(rf"^- `{re.escape(name)}`[^.]*\w[^.]*\.")
    assert any(pattern.match(line) for line in _the_files_section())


def test_every_source_path_the_index_names_exists() -> None:
    text = (GUIDE / "README.md").read_text(encoding="utf-8")
    paths = set(re.findall(r"src/factory/[\w./]*\w", text))
    assert [path for path in sorted(paths) if not (ROOT / path).exists()] == []


def test_no_file_names_a_removed_guide_file() -> None:
    pattern = re.compile(
        r"(?<![\w.-])(?<!operator-guide/)(?:project-guide/)?(?:"
        + "|".join(re.escape(name) for name in REMOVED_FILES)
        + r")"
    )
    found = [
        f"{path.relative_to(ROOT)}:{number}: {match.group(0)}"
        for path in searched_files(SEARCHED, NOT_SEARCHED)
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
        )
        for match in pattern.finditer(line)
    ]
    assert found == []
