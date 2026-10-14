---
stage: doing
pr: 76
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The watcher's command line

## Assignment (as of log entry 1)

Build `factory-watch` as the human's window on the remote: evaluate once, print the event the next tick would handle, and print the board of features and work items. It reads the remote-tracking refs as the last tick left them and fetches nothing, writes nothing and keeps no state of its own; it loads the pipeline definition at the head commit of `origin/main`, which raises and clears no stop. The leftover `--follow` mode and its `factory-last-line` file are not part of v1.1: asking for `--follow` is an unknown option, and no full tick or watch run writes that file. The board counts story files per lifecycle folder for each feature, with the feature's title from its `feature.md`, and shows one row per work item in progress with its stage, what it waits for, its claim, since when its claim was taken (the claim's `started_at`, read from the remote) and its pull request. The acceptance column of a feature stays empty until F0009. The console script `factory-watch = "factory.entry.watch:main"` is already declared in `pyproject.toml` and calls `main()` with no arguments, so `main` takes every argument as an optional one and reads `sys.argv`; the production wiring of the boundaries and the instance name comes with F0010-S0001 (the instance settings), and until then a `main` called without boundaries ends with exit status 2 and a line that says so (F0010-S0001 replaces that line by `read_settings` and `build_boundaries`). Covers SI3.1 and SI3.2; the board is the command line of v1's `--board` rebuilt. Builds on `Watcher` (F0006-S0002), `RemoteWorkItems` (F0006-S0001), `PipelineLoader` (F0003-S0006) and `Tick` (F0006-S0004, for the search of the last-line file).

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
    running_since: AwareDatetime | None       # the claim's started_at; None without a claim
    pull_request: PositiveInt | None

class FeatureRow(BaseModel):
    feature: FeatureId
    title: str
    backlog: NonNegativeInt
    in_progress: NonNegativeInt
    done: NonNegativeInt                      # story files only (ST6.2)
    acceptance: AcceptanceStatus | None = None    # filled from F0009-S0001

def work_item_row(snapshot: WorkItemSnapshot) -> BoardRow: ...
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

Every model here is frozen and forbids unknown keys.

`src/factory/entry/watch.py`

```python
def render_event(event: Event) -> str: ...
    # f"event: {event.key}", and when event.detail is not empty, two spaces and the detail
def run_watch(boundaries: Boundaries, instance: Name, out: TextIO, err: TextIO) -> int: ...
def main(argv: Sequence[str] | None = None, *, boundaries: Boundaries | None = None,
         instance: Name | None = None, out: TextIO | None = None, err: TextIO | None = None) -> int: ...
    # argv None is sys.argv[1:]; out and err default to sys.stdout and sys.stderr and are used by run_watch only;
    # argparse writes its help to standard output and its errors to standard error
```

Rules:

- `work_item_row`: `work_item`, `folder`, `stage`, `blocked`, `claim` and `pull_request` come from the snapshot and its state; `title` is the first `# ` title of the body (`factory.domain.sections.title`), else the id; `running_since` is `state.claim.started_at` when `state.claim` is set, else `None`.
- `feature_rows`: one row for each feature id found in the `feature_directory` of the stories (`parse_feature_directory_name`), in plain id order; `backlog`, `in_progress` and `done` count the stories of that folder; `title` is `titles[feature]` when present, else the feature directory's name; `acceptance` is `None`.
- `render_board` returns text of this shape, every line ending in a newline, fields separated by two spaces, an absent value written as `-`, `claim=` holding the claiming instance's name only and `running_since=` an ISO 8601 UTC time with a trailing `Z` (`%Y-%m-%dT%H:%M:%SZ`):

```
features
<feature id>  <title>  backlog=<n>  in-progress=<n>  done=<n>  acceptance=<status or ->
work items
<work item id>  <title>  <folder>  stage=<stage or ->  blocked=<blocked or ->  claim=<instance or ->  running_since=<time or ->  pull_request=<number or ->
```

- `BoardReader.read(definition)` takes the stories of all three folders from `RemoteWorkItems.list_stories`, the feature titles from `Git.show_file("origin/main", f"{FEATURES_DIRECTORY}/{directory}/{FEATURE_FILE_NAME}")` (the first `# ` title; a missing file or one without a title gives no entry), and the rows from `RemoteWorkItems.read(definition)`. A feature appears with a row when it has at least one story file in any folder.
- `run_watch` resolves `origin/main` and loads the definition with `PipelineLoader(boundaries).load(<that commit>)`, which raises and clears no stop; a commit that does not resolve raises `GitError`. On `PipelineDefinitionInvalid` it writes `factory-watch: <fault>` and a newline to `err`, writes nothing to `out` and returns 1. Otherwise it evaluates once with `Watcher(boundaries, instance).evaluate(definition)`, writes `render_event(event)`, a newline, a blank line and `render_board(...)` to `out`, and returns 0. It fetches nothing and writes nothing to the repository, the hosting service, the health status or the log.
- `main` parses `argv` first, with an `argparse.ArgumentParser(prog="factory-watch")` that has no options of its own; an unknown option ends with `SystemExit(2)` before anything else is looked at, also when `boundaries` is `None`. Then, when `boundaries` or `instance` is `None`, it writes `factory-watch: no instance settings are wired yet` and a newline to `err` (standard error when `err` is `None`), writes nothing to `out` and returns 2. Otherwise it returns `run_watch(...)`.

Tests: `tests/domain/test_board.py`, `tests/application/test_board_reader.py`, `tests/entry/test_watch.py`, with the fixtures `remote`, `checkout`, `human`, `hosting` (wrapped in a counting subclass that overrides every operation except `post_comment`, which `tests/test_hosting_fake_search.py` refuses in a test class; posts are counted with `factory_posts`), `clock` and `boundaries`. The tests build stories, `feature.md` files and branches on the remote through `human.push_file`, fill the agent home with `install_agents(agent_home, <the roles of the fixture's pipeline definition>)` from `tests/git_support.py`, read `run_watch`'s output through `io.StringIO` and argparse's output through `capsys`. The closed-model tests build the models through a variable typed `type[BaseModel]` and assign with `setattr`, the field's name in a variable.

## Acceptance criteria

1. `feature_rows` counts the story files of each lifecycle folder per feature: for stories of `F0001` in `backlog` (1), `in-progress` (2) and `done` (3) it returns one row with `backlog == 1`, `in_progress == 2`, `done == 3` and `acceptance is None`.
2. `feature_rows` returns one row for each feature id, in plain id order, whatever the order of the stories.
3. A feature's `title` is `titles[feature]` when the mapping has it, else its directory name (`F0001-demo`).
4. `work_item_row` fills `work_item`, `folder`, `stage`, `blocked`, `claim` and `pull_request` from the snapshot, and `title` from the body's `# ` title, or the id when the body has none.
5. `running_since` is the claim's `started_at` when the state has a claim, and `None` without one.
6. `render_board` of one feature (`F0001`, `Todo service`, 1, 2, 3, no acceptance) and one work item (`F0001-S0001`, `Domain model`, `in-progress`, stage `tests`, nothing blocked, claim by `factory-1`, no `running_since`, pull request 7) returns exactly `features`, `F0001  Todo service  backlog=1  in-progress=2  done=3  acceptance=-`, `work items`, `F0001-S0001  Domain model  in-progress  stage=tests  blocked=-  claim=factory-1  running_since=-  pull_request=7`, each line followed by a newline.
7. `render_board([], [])` returns `features` and `work items`, each on its own line followed by a newline.
8. `render_board` writes a row's `running_since` in UTC in the form `%Y-%m-%dT%H:%M:%SZ`.
9. `BoardReader.read` counts only story files on `origin/main`: a `.gitkeep`, a `feature.md` and a file that is not a work item name do not count in any folder, and a feature directory that holds only `feature.md` and a `.gitkeep` gives no row.
10. `BoardReader.read` takes a feature's title from the first `# ` title of its `feature.md` on `origin/main`, and falls back to the directory name when the file is missing or has no title.
11. `BoardReader.read` returns one row for each story in `in-progress/` with the state read from its branch, and `running_since` the claim's `started_at` of a claimed work item.
12. `run_watch` writes `event: <event key>` (and the event's detail after two spaces when there is one) as the first line, then a blank line, then the board, and returns 0.
13. `run_watch` evaluates once: with one waiting work item whose pull request is open it makes one `get_pull_request` and one `list_comments`.
14. `run_watch` writes nothing: afterwards the checkout's status has no change, the remote's branches are as before, the hosting service holds no new pull request, post or label, and the health status and the factory log are as they were.
15. `run_watch` fetches nothing: after the human pushes a new commit to a work item's branch, `run_watch` without a tick shows the state from before the push, and `checkout.resolve("origin/<branch>")` is unchanged.
16. When the pipeline definition on `origin/main` is invalid, `run_watch` returns 1, writes `factory-watch: <fault>` to `err` and nothing to `out`, and the health status holds no `pipeline_definition_invalid` stop afterwards.
17. `run_watch` on a clone of an empty bare repository, where `origin/main` does not resolve, raises `GitError`.
18. SI3.1: `main(["--follow"], ...)` raises `SystemExit` with code 2, writes an error that names `--follow` to standard error and nothing to `out`, and makes no call to the hosting service.
19. SI3.1: `main()` with `sys.argv` set to `["factory-watch", "--follow"]` and no other argument raises `SystemExit` with code 2 and no `TypeError`, without any boundaries (the installed console script calls `main()` this way).
20. `main([])` with `boundaries` or `instance` `None` returns 2, writes `factory-watch: no instance settings are wired yet` to `err` and nothing to `out`.
21. `main(["--help"], ...)` exits with code 0, writes its help to standard output, and that text does not contain the word `follow`.
22. SI3.2: after one `Tick.run()` and one `run_watch` on the fixture's repository, no file named `factory-last-line` exists anywhere under the test's `tmp_path`.
23. No file under `src/factory` contains the text `--follow` or `factory-last-line`.
24. `BoardRow`, `FeatureRow` and `BoardView` refuse an unknown key and an assignment to a field; `FeatureRow.backlog` accepts 0 and refuses -1 (`in_progress` and `done` likewise); `BoardRow.pull_request` accepts 1 and `None` and refuses 0; `BoardRow.folder` accepts `in-progress` and refuses `ongoing`; `FeatureRow.acceptance` accepts `due` and refuses `other`; a `running_since` without a time zone is refused; all with `ValidationError`.
25. make check stays green.
26. docs: `README.md` and `docs/operator-guide.md` describe `factory-watch` (the event line and the board, read from the last fetch) and say that it has no `--follow` mode.

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
2. intake: accepted
   - Interface: names concrete modules and signatures (`domain/board.py`, `application/board.py`, `entry/watch.py`). Every rule is stated with types and behaviour. `Blocked` is a plain string literal in `domain/work_item.py`, so a set value renders as itself, with no open choice.
   - Criteria: each can be tested by one test function. Rules have both sides. The title comes from the body or falls back to the id (4). The feature title comes from the mapping or falls back to the directory name (3, 10). `running_since` is set or `None` (5). A valid definition gives 0 and an invalid one gives 1 (12, 16). A missing `origin/main` raises `GitError` (17). `--follow` is refused (18, 19, 23), and missing boundaries give 2 (20). Counts reject -1 and accept 0, `pull_request` rejects 0, and the unknown-key, frozen, folder, acceptance and naive-datetime cases are covered (24). The Interface comments on conversion, format and defaults (the `Z` UTC time, `-` for absent values, the event line with detail) each have a criterion (6, 7, 8, 12).
   - Demo: both blocks are runnable. Each `Expect:` line is checkable against the output (`exit 2` on standard output, the usage and `--follow` error on standard error, the exact four board lines).
   - Architecture: `domain/board.py` is pure. `application/board.py` reads through `RemoteWorkItems` and `Git.show_file`. `entry/watch.py` is the command line and wires nothing beyond what it is given. This follows the four layers in `CLAUDE.md`.
   - Scope: within F0006's scope ("The command line", SI3.1, SI3.2). The acceptance column stays empty (F0009) and the instance wiring is left to F0010-S0001, both listed under Out of scope in `FEATURE.md`.
3. tester: wrote red tests for every acceptance criterion against the Interface.
   - criterion 1: tests/domain/test_board.py::test_feature_rows_count_the_story_files_of_each_folder
   - criterion 2: tests/domain/test_board.py::test_feature_rows_are_one_per_feature_in_plain_id_order
   - criterion 3: tests/domain/test_board.py::test_a_feature_title_comes_from_the_mapping_else_the_directory_name
   - criterion 4: tests/domain/test_board.py::test_a_work_item_row_is_filled_from_the_snapshot (cases: first `# ` title, and no title, which falls back to the id)
   - criterion 5: tests/domain/test_board.py::test_running_since_is_the_claims_start
   - criterion 6: tests/domain/test_board.py::test_render_board_writes_the_features_and_the_work_items
   - criterion 7: tests/domain/test_board.py::test_an_empty_board_has_only_its_two_headings
   - criterion 8: tests/domain/test_board.py::test_render_board_writes_running_since_in_utc_with_a_z (the input is +02:00, so the output must be converted to UTC)
   - criterion 9: tests/application/test_board_reader.py::test_only_story_files_count_on_main
   - criterion 10: tests/application/test_board_reader.py::test_a_feature_title_comes_from_its_feature_file_else_its_directory
   - criterion 11: tests/application/test_board_reader.py::test_each_story_in_progress_is_a_row_with_its_state_from_its_branch
   - criterion 12: tests/entry/test_watch.py::test_run_watch_writes_the_event_a_blank_line_and_the_board and ::test_an_event_is_written_as_its_key_and_its_detail
   - criterion 13: tests/entry/test_watch.py::test_run_watch_evaluates_once
   - criterion 14: tests/entry/test_watch.py::test_run_watch_writes_nothing
   - criterion 15: tests/entry/test_watch.py::test_run_watch_fetches_nothing
   - criterion 16: tests/entry/test_watch.py::test_an_invalid_definition_is_reported_without_a_stop (the expected fault comes from `PipelineLoader.load(<commit id>)`, which touches no stop)
   - criterion 17: tests/entry/test_watch.py::test_run_watch_without_origin_main_raises_git_error
   - criterion 18: tests/entry/test_watch.py::test_follow_is_an_unknown_option
   - criterion 19: tests/entry/test_watch.py::test_the_console_script_refuses_follow_from_sys_argv
   - criterion 20: tests/entry/test_watch.py::test_main_without_instance_settings_returns_2 (parametrized: boundaries None, instance None)
   - criterion 21: tests/entry/test_watch.py::test_help_names_no_follow_mode
   - criterion 22: tests/entry/test_watch.py::test_no_tick_and_no_watch_run_writes_a_last_line_file
   - criterion 23: tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode (reads the bytes of every file under src/factory)
   - criterion 24: tests/domain/test_board.py::test_a_row_refuses_an_unknown_key, ::test_a_row_refuses_an_assignment, ::test_a_feature_count_is_not_negative, ::test_a_board_row_accepts_only_its_values, ::test_a_feature_row_accepts_only_an_acceptance_status; tests/application/test_board_reader.py::test_a_board_view_refuses_an_unknown_key, ::test_a_board_view_refuses_an_assignment

   Files created: tests/domain/test_board.py, tests/application/test_board_reader.py, tests/entry/test_watch.py. The entry tests use a local `_CountingHosting` subclass that copies the one in test_watcher.py and does not override `post_comment`. Posts are checked through `factory_posts` and labels through `labels`.

   Result: `make test` stops at collection on purpose, with ModuleNotFoundError for `factory.domain.board` and `factory.application.board` (`factory.entry.watch` is missing too, behind the first error). `make lint` is green. I skipped the type check as the stage says.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
