# The demo check

## Assignment (as of log entry 1)

v1.1 ships its demos in `demo/`, one folder per demo, because there will be demos of different kinds of project (the human's word, "The demo, shipped with v1.1"). The first, the to-do service of v1's run 4, is written by hand in step 2 and is the input of the todo run. A demo that no test reads goes stale as v1.1 changes: its stories stop passing the story check, its pipeline definition stops loading. This story builds the check every demo must pass and runs it in `make check` over this repository's `demo/`: each demo folder holds its three parts, each of its stories passes v1.1's story check as a backlog story at the path it will have in the project, its `project/factory/pipeline.yml` passes the pipeline definition reader, and the index `demo/README.md` names it. A demo's name is its folder; nothing in the code knows the list. Until step 2 there is no demo, and the check passes. The index is the human's file (change H6, after this story), because no write path covers `demo/`.

## Interface

`src/factory/entry/check_demos.py` (new):

```python
def check_demos(root: Path) -> list[str]:
    """The findings of every demo under `root / "demo"`, one line each, in path order."""

def main(argv: Sequence[str] | None = None) -> int:
    """Print `demos ok` and return 0, or print one line per finding and return 1."""
```

`main` takes `--root <path>` (default: the current directory) and passes `argv` to `argparse` as given. `check_demos` finds, in this order:

- No `demo/` folder under `root`: no finding.
- `demo/` without a file `README.md`: `demo/README.md: missing`.
- Every folder `demo/<name>/` (files directly under `demo/` other than `README.md`, and folders whose name starts with `.`, are skipped), in name order:
  - `demo/README.md` has no line that holds `` `<name>/` ``: `demo/README.md: names no demo '<name>'`.
  - each of `README.md` (a file), `project/` and `features/` (folders) that is missing: `demo/<name>: missing <part>` (`missing README.md`, `missing project/`, `missing features/`). Without `project/`, nothing under it and no story is checked; without `features/`, no story is checked.
  - `project/factory/pipeline.yml` missing: `demo/<name>: missing project/factory/pipeline.yml`; present but refused by `RuamelPipelineDefinitionReader().parse`: `demo/<name>/project/factory/pipeline.yml: <the fault>`.
  - `project/factory/story-form.md` missing: `demo/<name>: missing project/factory/story-form.md` (then no story is checked).
  - every file under `features/`, in path order: it must be `features/<feature>/feature.md` or `features/<feature>/backlog/<story>.md`; any other file gives `demo/<name>/features/<rest>: not a feature file or a backlog story`. A backlog story is checked as the factory checks it on `main`: `check_story_place("factory/features/<feature>/backlog/<story>.md", feature_file_exists=<features/<feature>/feature.md exists>)`, then its text read with `FrontmatterWorkItemReader().parse_specification` and `check_story_form(<document>, <the story form>, folder="backlog")`; a `WorkItemFormatError` of the reader is one finding with its fault. Each finding is `demo/<name>/features/<rest>: <message>`, or `demo/<name>/features/<rest>:<line>: <message>` when the finding has a line.

The story part is the story check's own: `factory.entry.check_story` gains `backlog_story_findings(reader: WorkItemReader, path: str, text: str, form: str, *, feature_file_exists: bool) -> list[FormFinding]`, the place findings of `path` and then the form findings of `text` read as a specification (a `WorkItemFormatError` of the reader is one finding with its fault), and `finding_line(path: str, finding: FormFinding) -> str`, `<path>: <message>` or `<path>:<line>: <message>`. `factory-check-story` uses both for a backlog story and `check_demos` for every demo story; the reader is `build_work_item_reader()` of `factory.entry.wiring`. The tests of `tests/entry/test_check_story.py` still pass unchanged.

Tests: `tests/entry/test_check_demos.py` (criteria 1 to 13, with demos written into `tmp_path`, the pipeline definition `PIPELINE_YAML` and the form `STORY_FORM` of `tests/git_support.py`, and story texts that pass that form); `tests/test_demos.py` (criterion 14), which runs `main(["--root", <the repository root>])` and expects 0, so `make check` checks every demo.

## Acceptance criteria

1. A root without `demo/` gives no finding, and `main` prints `demos ok` and returns 0.
2. A complete demo `todo` (its `README.md`; `project/factory/pipeline.yml` = `PIPELINE_YAML`; `project/factory/story-form.md` = `STORY_FORM`; `features/F0001-x/feature.md`; one valid backlog story `features/F0001-x/backlog/F0001-S0001-first.md`) with an index that holds `` `todo/` `` gives no finding.
3. Without the index file: `demo/README.md: missing`; with an index that does not name the demo: `demo/README.md: names no demo 'todo'`.
4. A demo without its `README.md`, without `project/` or without `features/` gives exactly the one finding `demo/todo: missing README.md`, `demo/todo: missing project/` or `demo/todo: missing features/` respectively. Three rows of one parametrized test.
5. A demo whose pipeline definition holds a repeated key gives one finding that starts with `demo/todo/project/factory/pipeline.yml: not valid YAML`; one without the file gives `demo/todo: missing project/factory/pipeline.yml`.
6. A demo without the story form gives `demo/todo: missing project/factory/story-form.md` and no finding of its stories.
7. A backlog story without its `## Smoke test` section gives the finding the story check gives for it, prefixed `demo/todo/features/F0001-x/backlog/F0001-S0001-first.md`; a story `F0002-S0001-other.md` in the folder of `F0001-x` gives the place finding `the story F0002-S0001 is in the directory of feature F0001`; a feature folder without `feature.md` gives the finding that the feature file is missing.
8. A file `features/F0001-x/in-progress/F0001-S0002-y.md` or `features/notes.txt` gives `... : not a feature file or a backlog story`. Two rows of one parametrized test.
9. Two demos `a` and `b`, each with one finding, give `a`'s findings before `b`'s; `main` prints each finding on its own line and returns 1.
10. A file `demo/notes.txt` and a folder `demo/.cache/` holding a file, beside the complete demo `todo` of criterion 2, give no finding: neither is a demo, and the index need not name them.
11. Within one demo the story findings come in path order, and a finding with a line carries it: with `features/F0001-x/backlog/F0001-S0001-first.md` carrying the journal entry `1. 2026-10-17 human: created.` and `features/F0001-x/backlog/F0001-S0002-second.md` without its `## Smoke test`, the findings are exactly `demo/todo/features/F0001-x/backlog/F0001-S0001-first.md:<n>: a backlog story carries no journal entries`, `<n>` the line of that entry in the file, then `demo/todo/features/F0001-x/backlog/F0001-S0002-second.md: missing section: ## Smoke test`.
12. A backlog story whose text starts with front matter that is not valid YAML (`---\na: [\n---\n`) gives exactly one finding for that story, `demo/todo/features/F0001-x/backlog/F0001-S0001-first.md: front matter is not valid YAML`.
13. `main([])`, run with the current directory at a root whose complete demo `todo` has no index, prints `demo/README.md: missing` and returns 1: the root defaults to the current directory.
14. `main(["--root", <the repository root>])` returns 0 (this repository's `demo/`, whatever it holds).
15. `make check` stays green.
16. docs: the README's pointer list names `demo/` and `python -m factory.entry.check_demos`; the project guide gets a section *The demos*: the layout of a demo (its three parts and what `project/` and `features/` hold), the rules of the check, that `make check` runs it through `tests/test_demos.py`, and that a demo's stories are backlog stories checked at the path they will have in the project; the decision log records that the code knows no demo by name. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -m factory.entry.check_demos; echo "status $?"
```
Expect: two lines, `demos ok` and `status 0`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/entry/test_check_demos.py tests/test_demos.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
