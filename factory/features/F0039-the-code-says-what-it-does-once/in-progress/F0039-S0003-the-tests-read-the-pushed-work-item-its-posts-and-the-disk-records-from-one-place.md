---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 382
comments_read: [6305445672]
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-21T01:20:24.881242Z'
  lease_duration: 60
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
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-21T01:08:35.127116Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-21T01:08:48.692000Z'
  stage: intake
  run: 7343983e890f41b9b3e99b2ca935ef89
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-21T01:09:08.993807Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-21T01:15:49.611613Z'
  stage: tests
  run: 49aeb856da5a497a9c895d2c431a3483
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-21T01:16:10.865505Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-21T01:18:47.948780Z'
  stage: doing
  run: fe82724f2e3f490c8ba4985287604d42
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-21T01:19:08.916830Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-21T01:20:03.746218Z'
  stage: review
  run: cf2a7d3bf82d40348197963ac646367d
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-21T01:20:24.881242Z'
  stage: doing
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
5. factory: started intake as self.
6. intake: accepted
   Interface: names concrete modules and signatures (`tests/stage_run_support.py` `pushed`/`pushed_state`, new `tests/branch_reading.py`, `disk_settings`/`disk_records` in `tests/conftest.py`, the sixteen changed modules). No `src/factory/` change. The guard's function names are the tester's choice (human's answer, journal 4, item 1); the tester may take intake's suggested `helper_copies`, `record_fixture_copies` and `copies_by_module`. The copy rules (name without one leading `_`, annotations compared as `ast.unparse`, return annotation of the record fixtures) are fixed.
   Criteria: each is testable by one test function or one parametrized test. Criterion 1 fixes the exact module lists for every helper and fixture. Criterion 2 gives source-text rows for both sides: copy and non-copy, including the keyword-only variant, the `path: str` variant and the method inside a class. Criterion 3 covers behaviour, including the `error` versus `cost_table` filter. Criterion 4 covers the unchanged test ids. The closing two criteria are in place. The only remaining variants with the same name but other parameters (`_pushed_state(boundaries, path)`, `_pushed(world, work_item)`) are confirmed by the human (journal 4, item 2).
   Smoke test: the grep, the pytest run and the docs greps are runnable. The pytest line passes no `-q`. Every `Expect:` line is checkable (`0`, `exit 0`, `1` and `1`).
   Architecture: only `tests/` and the project guide change. The shared places follow the standing leave in `CLAUDE.md` (*Tests*) and feature decision 5.
   Scope: matches S0003 in `feature.md`. The variants in *Out of scope* stay. S0003 starts after F0033, per decision 10. The human's answers add no change to the story, so none was written.
7. factory: started tests as self.
8. tester: Tests written, and the moves done under the standing leave of `CLAUDE.md` (*Tests*). No module under `src/factory/` changed. `make test` is green: the tests are not red, because the moves are the story's work and the coder has nothing to build. Before the moves, the guard's criterion-1 rows would fail on the copies (the smoke grep counted 12 of them).

   Criterion → test:
   - criterion 1: tests/test_shared_branch_helpers.py::test_each_shared_helper_and_fixture_is_written_in_one_module (rows `pushed`, `pushed_state`, `remote_document`, `push_state`, `stop-records`, `disk-records`)
   - criterion 2: tests/test_shared_branch_helpers.py::test_the_guard_finds_a_copy_by_name_and_parameters_only (the five source rows of the criterion)
   - criterion 3: tests/test_shared_branch_helpers.py::test_the_shared_helpers_read_and_write_as_the_copies_did
   - criterion 4: no test function. Checked by `pytest --collect-only -q -o addopts=` over the sixteen modules: the HEAD copy (from `git archive`) and the working tree each list the same 279 ids. The full `make test` then passed.
   - criteria 5 and 6: `make check` and the docs, left to the coder's check and the documenter. I did not touch `docs/`.

   The guard's function: a single `copies(source) -> list[str]` in the guard module. It returns, for each top-level function, the shared helper name it copies (name without one leading `_`, plus the parameter annotations, keyword-only ones included, compared through `ast.unparse`) or the record-log return annotation it repeats. The human left the guard's names and signatures to the tester (journal 4).

   Files created:
   - tests/branch_reading.py (`remote_document`, `error_posts`, `push_state`, `BODY = "# First story\n"`)
   - tests/test_shared_branch_helpers.py

   Files changed:
   - tests/stage_run_support.py: new `pushed`; `pushed_state` now calls it.
   - tests/conftest.py: new `disk_settings` and `disk_records` fixtures.
   - The sixteen modules the Interface names:
     - test_after_agent, test_stage_finish, test_stalls, test_stall_labels and test_stage_known_results lose `_pushed`, `_pushed_state` and `_head`, and use `pushed`, `pushed_state` and `branch_head`. Where a local variable named `pushed` would now shadow the helper inside the same function, I renamed it to `document`.
     - test_closed_send_back, test_comment_handler, test_questions and test_hand_over lose `_remote_document` and `_error_posts`.
     - test_watcher, test_watcher_move_rule and entry/test_watch lose `_push_state`.
     - test_stop_publisher and test_stop_records_service lose their shadowing `records` fixtures.
     - test_disk_recorder and test_acceptance_facts_disk lose their `settings` and `records` fixtures; their tests and fixtures take `disk_settings` and `disk_records`.
   - One earlier test file outside that list, under the same leave: tests/application/test_nested_repositories.py imported `_pushed` from test_after_agent. It now imports `pushed` from stage_run_support, and its local variable is renamed to `document`. Its test names and checks are unchanged.

   Runs:
   - My first `make test` ended with an ImportError collecting test_nested_repositories.py (the `_pushed` import above). After fixing it I ran `make test` a second time, against the stage's run-once rule, because this story's moves must leave every test passing: green, coverage 99.14 %.
   - `make lint` is green.
   - I also ran `make types`: green, since every module exists.

   Modules the test runner could not import: none.

   `lint`: lint: green (0.5 s)
   `test`: test: green (59.4 s)
9. factory: started doing as self.
10. coder: Nothing built. The Interface says no module under `src/factory/` changes. The tester's entry (journal 8) records that the moves to `tests/stage_run_support.py`, `tests/branch_reading.py` and `tests/conftest.py`, and the guard `tests/test_shared_branch_helpers.py`, were the story's work under the standing leave. `make test` was already green when this stage started.

    What I did: ran `make check` on the committed state, with no changes of my own. It ended `check: green`, with coverage at 99.14 %. `git diff main -- . ':!factory' ':!tests'` is empty, and `git status --short` shows only the factory's costs sidecar. So there was no diff of mine to refactor.

    Main choice: I added no code and changed no test. The alternative I rejected was touching the moved test helpers to tidy them; that is the tester's work, and the coder never edits tests (R9).

    What the journal changed: the human's answer (journal 4) left the guard's function names to the tester. The tester used a single `copies(source)`. The Description is unchanged.

    Noticed but not touched:
    - Criterion 6, the docs line for `branch_reading.py` and the `disk_settings`/`disk_records` fixtures in `docs/project-guide/README.md`, is the documenter's.
    - Criterion 4 (the same test ids before and after) has no test function. The tester checked it by hand: 279 ids on each side.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 38 known, 0 gone
11. factory: started review as self.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` against the work item. No module under `src/factory/` changes, as the Interface says.

    Acceptance criteria: criteria 1 to 3 have their tests in `tests/test_shared_branch_helpers.py`. They are parametrized as the criteria ask, and the criterion-2 rows match the criterion's source texts. Criterion 4 holds when the diff is read: no `def test_` and no `@pytest.mark` line is added or removed in any changed module. The coder's journal entry says `make check` was green. The architecture and security checks have nothing to judge, since only tests change and no marker was added. The quality check turned up the findings below.

    Findings:
    1. `tests/application/test_stop_records_service.py:44`: `_records_path` is dead code. Its only caller was the shadowing `records` fixture that the move removed. Fix: delete the function.
    2. `tests/application/test_watcher.py:33` and `tests/entry/test_watch.py:40`: `BODY = "# First story\n"` is dead code. Its only user was the removed `_push_state`, and `push_state` now carries its own `BODY` in `tests/branch_reading.py`. Fix: delete both constants.
    3. `tests/application/test_watcher_move_rule.py:28`: `BODY` is still used at line 147, but it is now a copy of `branch_reading.BODY`. Fix: import `BODY` from `branch_reading` and delete the local copy.

    All three are in test files that `main` already holds, so the tester makes the change under the standing leave. The coder hands it on with `tests` (R9).

    Earlier tests (changed under the leave named):
    - tests/application/handlers/test_closed_send_back.py: standing leave (`_remote_document` moved)
    - tests/application/handlers/test_comment_handler.py: standing leave (`_remote_document` and `_error_posts` moved)
    - tests/application/handlers/test_hand_over.py: standing leave (`_error_posts` moved)
    - tests/application/handlers/test_questions.py: standing leave (`_remote_document` moved)
    - tests/application/test_acceptance_facts_disk.py: standing leave (`settings` and `records` moved to `disk_settings` and `disk_records`)
    - tests/application/test_after_agent.py: standing leave (`_head`, `_pushed` and `_pushed_state` moved; a local `pushed` renamed to `document` to avoid shadowing)
    - tests/application/test_disk_recorder.py: standing leave (`settings` and `records` moved to `disk_settings` and `disk_records`)
    - tests/application/test_nested_repositories.py: standing leave (its `_pushed` import replaced by the shared `pushed`; a local variable renamed)
    - tests/application/test_stage_finish.py: standing leave (`_head`, `_pushed` and `_pushed_state` moved; local variable renamed)
    - tests/application/test_stage_known_results.py: standing leave (`_pushed` moved)
    - tests/application/test_stall_labels.py: standing leave (`_pushed` and `_pushed_state` moved)
    - tests/application/test_stalls.py: standing leave (`_head`, `_pushed` and `_pushed_state` moved; local variable renamed)
    - tests/application/test_stop_publisher.py: standing leave (shadowing `records` fixture removed in favour of conftest's)
    - tests/application/test_stop_records_service.py: standing leave (shadowing `records` fixture removed; it went beyond the move by leaving `_records_path` dead, see finding 1)
    - tests/application/test_watcher.py: standing leave (`_push_state` moved; it went beyond the move by leaving `BODY` dead, see finding 2)
    - tests/application/test_watcher_move_rule.py: standing leave (`_push_state` moved; it left a copy of `BODY`, see finding 3)
    - tests/entry/test_watch.py: standing leave (`_push_state` moved; it went beyond the move by leaving `BODY` dead, see finding 2)
    - tests/conftest.py: standing leave (`disk_settings` and `disk_records` fixtures added as the shared place)
    - tests/stage_run_support.py: standing leave (`pushed` added; `pushed_state` now calls it)
13. factory: started doing as self.
