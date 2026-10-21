---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 382
comments_read: [6305445672]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T01:06:40.390373Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T01:06:40.395708Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-21T01:06:59.820235Z'
  stage: intake
  run: 718b4ae212f04313963dcd613e8c5d46
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-21T01:08:17.124593Z'
  stage: intake
---

# The tests read the pushed work item, its posts and the disk records from one place

## Description

Test modules still hold copies of helpers and fixtures that exist once elsewhere or in each other: `_pushed` and `_pushed_state` in five modules, although `tests/stage_run_support.py` has `pushed_state`; `_remote_document` in three handler modules; `_error_posts` in two; `_push_state` in three watcher modules; a `records` fixture in two modules that shadows the one of `tests/conftest.py`; and identical disk `settings` and `records` fixtures in two modules. This story, the tester's under the standing leave of `CLAUDE.md` (*Tests*), moves each to one shared place: `pushed` beside `pushed_state` in `tests/stage_run_support.py`; `remote_document`, `error_posts` and `push_state` in a new `tests/branch_reading.py`; the disk fixtures into `tests/conftest.py` as `disk_settings` and `disk_records`. The shadowing `records` fixtures go. A guard finds a copy of the four branch helpers by name and parameters, and of the two record fixtures by their return type (the feature's decision 5). Every earlier test keeps its name and checks the same thing. Unchanged: the variants that differ in parameters or body (the feature's *Out of scope*). No module under `src/factory/` changes; the coder has nothing to build.

## Interface

No module under `src/factory/` changes.

`tests/stage_run_support.py`:

```python
def pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:
    """The work item at the head of the remote's branch."""


def pushed_state(boundaries: Boundaries, remote: Path) -> WorkItemState:
    """The work item's state at the head of the remote's branch."""
```

- `pushed` reads `PATH` at `branch_head(remote)` through `boundaries.git.show_file` and parses it with `boundaries.work_item_reader`; `pushed_state` is `pushed(...).state`, asserted not `None`, as today.

`tests/branch_reading.py` (new; `BRANCH` and `PATH` from `stage_run_support`):

```python
def remote_document(boundaries: Boundaries, checkout: GitCli) -> WorkItemDocument:
    """Fetch, then the work item the remote's branch holds."""


def error_posts(hosting: FakeHostingService, number: int) -> list[PullRequestComment]:
    """The factory's posts of kind `error` on pull request `number`, in order."""


def push_state(human: HumanClone, state: WorkItemState) -> None:
    """Push the work item with `state` and the body `# First story` to the branch."""
```

- Each has the body of today's copies: `remote_document` that of `tests/application/handlers/test_comment_handler.py`, `error_posts` that of `tests/application/handlers/test_hand_over.py`, `push_state` that of `tests/application/test_watcher.py` with `BODY = "# First story\n"`.

`tests/conftest.py`: two fixtures, with the bodies of today's `settings` and `records` fixtures of `tests/application/test_disk_recorder.py`:

```python
@pytest.fixture
def disk_settings(tmp_path: Path) -> InstanceSettings:
    """Return settings whose checkout and state directory lie under `tmp_path`."""


@pytest.fixture
def disk_records(tmp_path: Path) -> JsonLinesRecordLog[DiskRecord]:
    """Return the disk record log of the test, in `tmp_path`."""
```

The modules changed, each losing its copy and taking the shared one:

- `_pushed` and `_pushed_state` (and `_head` where nothing else uses it): `tests/application/test_after_agent.py`, `tests/application/test_stage_finish.py`, `tests/application/test_stalls.py`, `tests/application/test_stall_labels.py`, `tests/application/test_stage_known_results.py`.
- `_remote_document`: `tests/application/handlers/test_closed_send_back.py`, `tests/application/handlers/test_comment_handler.py`, `tests/application/handlers/test_questions.py`.
- `_error_posts`: `tests/application/handlers/test_comment_handler.py`, `tests/application/handlers/test_hand_over.py`.
- `_push_state`: `tests/application/test_watcher.py`, `tests/application/test_watcher_move_rule.py`, `tests/entry/test_watch.py`.
- The `records` fixture that shadows `tests/conftest.py`'s: `tests/application/test_stop_publisher.py`, `tests/application/test_stop_records_service.py`.
- The disk `settings` and `records` fixtures, whose users take `disk_settings` and `disk_records`: `tests/application/test_acceptance_facts_disk.py`, `tests/application/test_disk_recorder.py`.

`tests/test_shared_branch_helpers.py` (new), the guard:

- A copy of a branch helper is a function at the top level of a module whose name, without one leading `_`, is `pushed`, `pushed_state`, `remote_document` or `push_state`, and whose parameters, keyword-only ones included, carry the annotations of the shared one, compared as `ast.unparse` prints them.
- A copy of a record fixture is a function at the top level of a module whose return annotation is `JsonLinesRecordLog[StopRecord]` or `JsonLinesRecordLog[DiskRecord]`.
- The guard reads every `*.py` file under `tests/`, parsed with `ast`.

## Acceptance criteria

1. Each shared helper and fixture is written in one module (rows of one parametrized test, paths relative to `tests/`): the copies of `pushed` and of `pushed_state` are exactly `["stage_run_support.py"]`; of `remote_document` and of `push_state`, exactly `["branch_reading.py"]`; the functions returning `JsonLinesRecordLog[StopRecord]` and those returning `JsonLinesRecordLog[DiskRecord]`, exactly `["conftest.py"]`.
2. The guard finds a copy by name and parameters and nothing else (rows of one parametrized test, each a source text the guard's functions read): `def _pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:\n    ...\n` is a copy of `pushed`; `def _pushed_state(boundaries: Boundaries, path: str) -> WorkItemState:\n    ...\n` is not a copy of `pushed_state`; `def _push_state(human: HumanClone, state: WorkItemState, *, path: str = PATH) -> None:\n    ...\n` is not a copy of `push_state`; `def disk_log(tmp_path: Path) -> JsonLinesRecordLog[DiskRecord]:\n    ...\n` is a copy of a record fixture; `class Rig:\n    def pushed(self, boundaries: Boundaries, remote: Path) -> None:\n        ...\n` is not a copy.
3. The shared helpers read and write as the copies did: after `human.start(BACKLOG_PATH)` (`stage_run_support`) and `push_state(human, state)` with a `WorkItemState` of stage `doing` and pull request 1, `remote_document(boundaries, checkout).state` equals that state, and `pushed_state(boundaries, remote)` equals it too; `error_posts(hosting, number)` of a pull request on which the factory posted one comment whose `PostKey` has the kind `error` and one whose kind is `cost_table` (`work_item="F0001-S0001"`, `n="1"`) is the one `error` post.
4. Every earlier test keeps its name and checks the same thing: the tests that `pytest --collect-only` lists in the sixteen test modules the Interface names are, after the story, the same ids as before it, and all of them pass.
5. `make check` stays green.
6. docs: `docs/project-guide/README.md`, *Shared test helpers*: one line for the new module in the list, in its alphabetical place after `bill_support.py`, in the form of the other lines: `` - `branch_reading.py`: the work item on a work item's branch and the factory's posts on its pull request (`remote_document`, `error_posts`, `push_state`). ``; and, as the section asks of a story that adds a fixture, the line of `conftest.py` names `disk_settings` (settings whose checkout and state directory lie under `tmp_path`) and `disk_records` (the disk record log in `tmp_path`) under *Paths and settings*. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, nothing an operator or a newcomer sees changes and no decision is taken.

## Smoke test

```bash
grep -lE '^def (_pushed|_pushed_state|_remote_document|_error_posts|_push_state)\((boundaries: Boundaries, (remote: Path|checkout: GitCli)|hosting: FakeHostingService, (number|pull_request): int|human: HumanClone, state: WorkItemState)\)' tests/application/test_after_agent.py tests/application/test_stage_finish.py tests/application/test_stalls.py tests/application/test_stall_labels.py tests/application/test_stage_known_results.py tests/application/handlers/test_closed_send_back.py tests/application/handlers/test_comment_handler.py tests/application/handlers/test_questions.py tests/application/handlers/test_hand_over.py tests/application/test_watcher.py tests/application/test_watcher_move_rule.py tests/entry/test_watch.py | wc -l
```
Expect: one line, `0` (before the story, `12`)

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
TMPDIR="$d" uv run pytest --no-header --tb=short -p no:cacheprovider tests/test_shared_branch_helpers.py tests/application/test_disk_recorder.py tests/application/test_stop_publisher.py tests/application/handlers/test_hand_over.py > "$d/out" 2>&1
echo "exit $?"
```
Expect: one line, `exit 0`

```bash
grep -c '^- `branch_reading.py`: ' docs/project-guide/README.md
grep -c '^- `conftest.py`: .*`disk_settings`.*`disk_records`' docs/project-guide/README.md
```
Expect: two lines, `1` and `1` (before the story, `0` and `0`)

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: Questions (the format check passed, so no findings from it):

   1. The Interface names no functions for the guard `tests/test_shared_branch_helpers.py`, yet criterion 2 says "a source text the guard's functions read" and tests them on source strings. The tester cannot call a function the Interface doesn't name, and two testers would pick two names and signatures. What are the guard's functions? My suggestion, in the guard module: `helper_copies(source: str) -> list[str]` returning the names of top-level functions that copy a branch helper (name without one leading `_`, plus the parameter annotations of the shared one), and `record_fixture_copies(source: str) -> list[str]` returning the names of top-level functions whose return annotation is `JsonLinesRecordLog[StopRecord]` or `JsonLinesRecordLog[DiskRecord]`. Add a third function, or say how criterion 1 gets "the modules that hold a copy" from every `*.py` under `tests/`, e.g. `copies_by_module(root: Path) -> dict[str, list[str]]`.

   2. Criterion 1 expects the copies of `pushed` and `pushed_state` to be exactly `["stage_run_support.py"]`. That holds only if `Boundaries` and `Path` are annotated in the same spelling in every copy, because the guard compares `ast.unparse` text. This is probably fine, since criterion 2 pins the spelling. Please confirm that the earlier `_pushed_state(boundaries, path: str)` of `test_stage_run_acceptance.py` is the only variant left, so the "exactly" list is not broken by a variant that has the same parameters but another body.

   Everything else I checked is in order. Both closing criteria are present. The Interface names concrete files and signatures. Criteria 3 and 4 are testable, and the smoke commands are runnable (the pytest line passes no `-q`). The scope matches `feature.md` S0003. I confirmed with grep that the `records` copies exist in the four modules named, with the `conftest.py` one as the shared fixture.
4. 2026-10-21 human: Answers (2026-10-21):
   1. The guard's function names and signatures are the tester's choice; the criteria fix only what the guard finds. Your suggestion (`helper_copies(source)`, `record_fixture_copies(source)` and a `copies_by_module(root)` for criterion 1) is a good one, and the tester may take it.
   2. Confirmed on `main` (grep of `def _?pushed` and `def _?pushed_state` under `tests/`): besides the copies with `(boundaries: Boundaries, remote: Path)`, only two variants remain, `test_stage_run_acceptance.py`'s `_pushed_state(boundaries: Boundaries, path: str)` and `test_approval_description.py`'s `_pushed(world: World, work_item: WorkItemId)`; both differ in their parameters, so the guard does not count them. Every remaining copy spells `Boundaries` and `Path` the same way.
