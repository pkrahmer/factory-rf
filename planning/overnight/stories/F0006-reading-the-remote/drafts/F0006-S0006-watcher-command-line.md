# The watcher's command line

## Assignment (as of log entry 1)

Build `factory-watch` as the human's window on the remote: evaluate once, print the event the next tick would handle, and print the board of features and work items. It reads the remote-tracking refs as the last tick left them and fetches nothing, writes nothing and keeps no state of its own. The leftover `--follow` mode and its `factory-last-line` file are not part of v1.1: asking for `--follow` is an unknown option, and no full tick or watch run writes that file. The board counts story files per lifecycle folder for each feature, with the feature's title from its `feature.md`, and shows one row per work item in progress with its stage, what it waits for, its claim, since when an agent run is shown running (display only, from the run record) and its pull request. The acceptance column of a feature stays empty until F0009. The console script entry in `pyproject.toml` and the production wiring of the boundaries come with F0010-S0001 (the instance settings); `main` therefore takes the boundaries and the instance name as arguments, and the `pyproject.toml` entry is the human's, outside the coder's write paths. Covers SI3.1 and SI3.2; the board is the command line of v1's `--board` rebuilt. Builds on `Watcher` (F0006-S0002), `RemoteWorkItems` (F0006-S0001), `PipelineLoader` (F0003-S0004) and `Tick` (F0006-S0004, for the search of the last-line file).

## Interface

`src/factory/domain/board.py`

```python
AcceptanceStatus = Literal["incomplete", "due", "in_flight", "merged_unrecorded", "accepted", "refused"]

class BoardRow(BaseModel):
    work_item: WorkItemId
    title: str
    folder: LifecycleFolder
    stage: Name | None
    blocked: Blocked | None
    claim: Claim | None
    running_since: AwareDatetime | None       # from the run record, display only
    pull_request: PositiveInt | None

class FeatureRow(BaseModel):
    feature: FeatureId
    title: str
    backlog: NonNegativeInt
    in_progress: NonNegativeInt
    done: NonNegativeInt                      # story files only (ST6.2)
    acceptance: AcceptanceStatus | None = None    # filled from F0009-S0001

def work_item_row(snapshot: WorkItemSnapshot, run_record: RunRecord | None) -> BoardRow: ...
def feature_rows(stories: Sequence[StoryFile], titles: Mapping[FeatureId, str]) -> list[FeatureRow]: ...
def render_board(features: Sequence[FeatureRow], rows: Sequence[BoardRow]) -> str: ...
```

`src/factory/application/board.py`

```python
class BoardView(BaseModel):
    features: list[FeatureRow]
    rows: list[BoardRow]

class BoardReader:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def read(self, definition: PipelineDefinition) -> BoardView: ...     # GitError; WorkItemFormatError
```

`src/factory/entry/watch.py`

```python
def render_event(event: Event) -> str: ...
    # f"event: {event.key}", and when event.detail is not empty, two spaces and the detail
def run_watch(boundaries: Boundaries, instance: Name, out: TextIO, err: TextIO) -> int: ...
def main(argv: Sequence[str] | None = None, *, boundaries: Boundaries, instance: Name,
         out: TextIO | None = None, err: TextIO | None = None) -> int: ...
    # out and err default to sys.stdout and sys.stderr
```

Rules:

- `work_item_row`: `work_item`, `folder`, `stage`, `blocked`, `claim` and `pull_request` come from the snapshot and its state; `title` is the first `# ` title of the body (`factory.domain.sections.title`), else the id; `running_since` is `run_record.started_at` when `run_record` is not `None` and its `work_item` equals the snapshot's id, else `None`.
- `feature_rows`: one row for each feature id found in the `feature_directory` of the stories (`parse_feature_directory_name`), in plain id order; `backlog`, `in_progress` and `done` count the stories of that folder; `title` is `titles[feature]` when present, else the feature directory's name; `acceptance` is `None`.
- `render_board` returns text of this shape, every line ending in a newline, fields separated by two spaces, an absent value written as `-`, `claim=` holding the claiming instance's name only and `running_since=` an ISO 8601 UTC time with a trailing `Z` (`%Y-%m-%dT%H:%M:%SZ`):

```
features
<feature id>  <title>  backlog=<n>  in-progress=<n>  done=<n>  acceptance=<status or ->
work items
<work item id>  <title>  <folder>  stage=<stage or ->  blocked=<blocked or ->  claim=<instance or ->  running_since=<time or ->  pull_request=<number or ->
```

- `BoardReader.read(definition)` takes the stories of all three folders from `RemoteWorkItems.list_stories`, the feature titles from `Git.show_file("origin/main", "factory/features/<directory>/feature.md")` (the first `# ` title; a missing file or one without a title gives no entry), the rows from `RemoteWorkItems.read(definition).snapshots` with `boundaries.run_record.read()`. An unreadable run record is `None` (the store already returns `None`).
- `run_watch` loads the definition with `PipelineLoader(boundaries).load()`; on `PipelineDefinitionInvalid` it writes `factory-watch: <fault>` and a newline to `err`, writes nothing to `out` and returns 1. Otherwise it evaluates once with `Watcher(boundaries, instance).evaluate(definition)`, writes `render_event(event)`, a newline, a blank line and `render_board(...)` to `out`, and returns 0. It fetches nothing and writes nothing to the repository or the hosting service.
- `main` parses `argv` with an `argparse.ArgumentParser(prog="factory-watch")` that has no options of its own; an unknown option ends with `SystemExit(2)` before anything is read. Otherwise it returns `run_watch(...)`.

Tests: `tests/domain/test_board.py`, `tests/application/test_board_reader.py`, `tests/entry/test_watch.py`, with the fixtures `remote`, `checkout`, `human`, `hosting` (wrapped in a counting subclass where calls are counted), `clock` and `boundaries`. The tests build stories, `feature.md` files and branches on the remote through `human.push_file`, replace the pipeline loader's agent definitions by an agent home under `tmp_path`, and read output through `io.StringIO`.

## Acceptance criteria

1. `feature_rows` counts the story files of each lifecycle folder per feature: for stories of `F0001` in `backlog` (1), `in-progress` (2) and `done` (3) it returns one row with `backlog == 1`, `in_progress == 2`, `done == 3` and `acceptance is None`.
2. `feature_rows` returns one row for each feature id, in plain id order, whatever the order of the stories.
3. A feature's `title` is `titles[feature]` when the mapping has it, else its directory name (`F0001-demo`).
4. `work_item_row` fills `work_item`, `folder`, `stage`, `blocked`, `claim` and `pull_request` from the snapshot, and `title` from the body's `# ` title, or the id when the body has none.
5. `running_since` is the run record's `started_at` when the record names the snapshot's work item, and `None` when it names another one or there is no record.
6. `render_board` of one feature (`F0001`, `Todo service`, 1, 2, 3, no acceptance) and one work item (`F0001-S0001`, `Domain model`, `in-progress`, stage `tests`, nothing blocked, claim by `factory-1`, no `running_since`, pull request 7) returns exactly `features`, `F0001  Todo service  backlog=1  in-progress=2  done=3  acceptance=-`, `work items`, `F0001-S0001  Domain model  in-progress  stage=tests  blocked=-  claim=factory-1  running_since=-  pull_request=7`, each line followed by a newline.
7. `render_board([], [])` returns `features` and `work items`, each on its own line followed by a newline.
8. `render_board` writes a row's `running_since` in UTC in the form `%Y-%m-%dT%H:%M:%SZ`.
9. `BoardReader.read` counts only story files on `origin/main`: a `.gitkeep`, a `feature.md` and a file that is not a work item name do not count in any folder.
10. `BoardReader.read` takes a feature's title from the first `# ` title of its `feature.md` on `origin/main`, and falls back to the directory name when the file is missing or has no title.
11. `BoardReader.read` returns one row for each story in `in-progress/` with the state read from its branch, and the run record's start for the work item the record names; an unreadable run record gives `running_since` `None` for all rows.
12. `run_watch` writes `event: <event key>` (and the event's detail after two spaces when there is one) as the first line, then a blank line, then the board, and returns 0.
13. `run_watch` evaluates once: with one waiting work item whose pull request is open it makes one `get_pull_request` and one `list_comments`.
14. `run_watch` writes nothing: afterwards the checkout's status has no change, the remote's branches are as before, and the hosting service holds no new pull request, post or label.
15. When the pipeline definition on `origin/main` is invalid, `run_watch` returns 1, writes `factory-watch: <fault>` to `err` and nothing to `out`.
16. SI3.1: `main(["--follow"], ...)` raises `SystemExit` with code 2, writes an error that names `--follow` to `err` and nothing to `out`, and makes no call to the hosting service.
17. `main(["--help"], ...)` exits with code 0 and its help text does not contain the word `follow`.
18. SI3.2: after one `Tick.run()` and one `run_watch` on the fixture's repository, no file named `factory-last-line` exists anywhere under the test's `tmp_path`.
19. No file under `src/factory` contains the text `--follow` or `factory-last-line`.
20. `make check` stays green.
21. docs: `README.md` and `docs/operator-guide.md` describe `factory-watch` (the event line and the board, read from the last fetch) and say that it has no `--follow` mode.

## Demo

```bash
uv run python -c "
from factory.entry.watch import main
try:
    main(['--follow'], boundaries=None, instance='factory-1')
except SystemExit as error:
    print('exit', error.code)
"
```
Expect: the standard output is the single line `exit 2`; the standard error shows a `usage: factory-watch` line and an error that names `--follow` (unrecognized arguments).

```bash
uv run python -c "
from factory.domain.board import BoardRow, FeatureRow, render_board
features = [FeatureRow(feature='F0001', title='Todo service', backlog=1, in_progress=2, done=3)]
rows = [BoardRow(work_item='F0001-S0001', title='Domain model', folder='in-progress', stage='tests', blocked=None, claim=None, running_since=None, pull_request=7)]
print(render_board(features, rows), end='')
"
```
Expect: exactly four lines: `features`, `F0001  Todo service  backlog=1  in-progress=2  done=3  acceptance=-`, `work items`, and `F0001-S0001  Domain model  in-progress  stage=tests  blocked=-  claim=-  running_since=-  pull_request=7`.

## Log (append only)

1. 2026-10-12 human: created.
