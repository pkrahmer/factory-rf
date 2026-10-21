---
stage: smoke-test
blocked: null
round: 2
attempts: 1
crashes: 0
pull_request: 382
comments_read: [6305445672]
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-21T01:40:31.171158Z'
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
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-21T01:20:46.489698Z'
  stage: doing
  run: b2af91662bb9450fa75ebe4c2ea990f6
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-21T01:21:06.848658Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-21T01:23:45.137156Z'
  stage: tests
  run: 4fb7b8c0894a4e5a8a830da2667d2c53
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-21T01:24:05.623552Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-21T01:26:39.872180Z'
  stage: doing
  run: f18ef9c6a55f4001be6325047586c9c5
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-21T01:27:00.711603Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-21T01:28:34.167496Z'
  stage: review
  run: 5e9dae8b2d4649a38eba2aa3a44fe17f
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-21T01:28:54.881893Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-10-21T01:29:20.381486Z'
  stage: doing
  run: 0c411aff3adc413ebce514311d5b54f2
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-21T01:29:40.495946Z'
  stage: tests
- number: 24
  speaker: tester
  kind: result
  at: '2026-10-21T01:32:24.542572Z'
  stage: tests
  run: 28b3f1d50a99444584cd9a893c98f95f
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-21T01:32:45.346212Z'
  stage: doing
- number: 26
  speaker: coder
  kind: result
  at: '2026-10-21T01:34:33.712858Z'
  stage: doing
  run: f93cc273aa37462990ed0f69a178601b
- number: 27
  speaker: factory
  kind: stall
  at: '2026-10-21T01:34:33.743091Z'
  stage: doing
  run: f93cc273aa37462990ed0f69a178601b
  reason: check_red
- number: 28
  speaker: factory
  kind: started
  at: '2026-10-21T01:34:56.396335Z'
  stage: doing
- number: 29
  speaker: coder
  kind: result
  at: '2026-10-21T01:38:00.587227Z'
  stage: doing
  run: 54e7fcd1380441e1b0741ca95b66acd0
- number: 30
  speaker: factory
  kind: started
  at: '2026-10-21T01:38:21.117717Z'
  stage: review
- number: 31
  speaker: reviewer
  kind: result
  at: '2026-10-21T01:39:25.683875Z'
  stage: review
  run: 87616090614e499198090ce4da59c581
- number: 32
  speaker: factory
  kind: started
  at: '2026-10-21T01:39:45.966323Z'
  stage: docs
- number: 33
  speaker: documenter
  kind: result
  at: '2026-10-21T01:40:09.834723Z'
  stage: docs
  run: 9832452906eb4674af9507540868cb3c
- number: 34
  speaker: factory
  kind: started
  at: '2026-10-21T01:40:31.171158Z'
  stage: smoke-test
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
5. The guard strips one leading `_` and no more (a row of the parametrized test of criterion 2): `def __pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:\n    ...\n` is not a copy of `pushed`.
6. `make check` stays green.
7. docs: `docs/project-guide/README.md`, *Shared test helpers*: one line for the new module in the list, in its alphabetical place after `bill_support.py`, in the form of the other lines: `` - `branch_reading.py`: the work item on a work item's branch and the factory's posts on its pull request (`remote_document`, `error_posts`, `push_state`). ``; and, as the section asks of a story that adds a fixture, the line of `conftest.py` names `disk_settings` (settings whose checkout and state directory lie under `tmp_path`) and `disk_records` (the disk record log in `tmp_path`) under *Paths and settings*. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, nothing an operator or a newcomer sees changes and no decision is taken.

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
14. coder: No code changed this round. The reviewer's three findings (journal 12) are all in test files, so they are the tester's work under the standing leave in `CLAUDE.md` (*Tests*). The coder never edits tests (R9).

    I checked each finding with grep on the committed state, and each holds. The changes for the tester:
    1. `tests/application/test_stop_records_service.py:44`: delete `_records_path`. Its only caller was the `records` fixture that was removed, so it is now unused.
    2. `tests/application/test_watcher.py:33` and `tests/entry/test_watch.py:40`: delete `BODY = "# First story\n"`. Nothing uses it in either module now.
    3. `tests/application/test_watcher_move_rule.py:28`: delete the local `BODY` and import `BODY` from `branch_reading`. Line 147 still uses it.

    Each change keeps every test's name and what it checks.

    Main choice: I'm handing this on with `tests`. The alternative I rejected was making the deletions myself, because I don't edit tests even for dead code. I did not run `make check` this round, because I left nothing in the working tree.

    Noticed but not touched: nothing further.
15. factory: started tests as self.
16. tester: I made the three test changes the coder handed on in journal 14, which answer the reviewer's findings in journal 12. I made them under the standing leave in `CLAUDE.md` (*Tests*). Every test keeps its name and checks the same thing.

    Files changed (all earlier test files, under the standing leave):
    - tests/application/test_stop_records_service.py: deleted the dead `_records_path` helper. Its only caller was the `records` fixture that was removed in this story. `Path` is still imported because other code in the module uses it.
    - tests/application/test_watcher.py: deleted the dead constant `BODY = "# First story\n"`.
    - tests/entry/test_watch.py: deleted the same dead constant `BODY`.
    - tests/application/test_watcher_move_rule.py: deleted the local copy of `BODY`. The module now imports `BODY` from `branch_reading`, next to `push_state`. Its one use, at `test_watcher_move_rule.py:146`, now reads the shared constant.

    Files created: none. Criterion → test mapping: unchanged from journal 8. No test was added or renamed.

    Runs: `make test` is green (coverage 99.14 %). `make lint` is green.

    Modules the test runner could not import: none.

    `lint`: lint: green (0.6 s)
    `test`: test: green (60.6 s)
17. factory: started doing as self.
18. coder: Round 1: no code changed. The reviewer's findings (journal 12) went to the tester through the coder's `tests` hand-on (journal 14). The tester fixed them (journal 16), and I checked each fix on the committed state:
    1. `_records_path` is gone from `tests/application/test_stop_records_service.py`.
    2. `BODY` is gone from `tests/application/test_watcher.py` and from `tests/entry/test_watch.py`.
    3. `tests/application/test_watcher_move_rule.py:8` now imports `BODY, push_state` from `branch_reading`, and the local copy is gone.

    What I built: nothing. The Interface says no module under `src/factory/` changes. `git diff main -- . ':!factory' ':!tests'` is empty, and the working tree holds only the factory's costs sidecar.

    Main choice: I hand on to `review` with no change of mine. The alternative I rejected was touching the moved test helpers. That is the tester's work (R9), and no finding is left open.

    Refactor: there is no diff of mine, so nothing needed changing.

    What the journal changed: nothing in the meaning of the task. The Description is unchanged.

    Noticed but not touched: criterion 6, the `docs/project-guide/README.md` lines for `branch_reading.py` and `disk_settings`/`disk_records`, is the documenter's.

    `check`: check: green (coverage 99.14 %)

    `check`: check: green
    `duplicates`: duplicates: 0 new, 38 known, 0 gone
19. factory: started review as self.
20. reviewer: Round 1 review of `git diff main...HEAD -- . ':!factory'` (21 files, all under `tests/`; nothing under `src/factory/` changes, as the Interface says) against the work item. The three findings from round 0 (journal 12) are fixed: `_records_path` is gone, and so are both dead `BODY` constants, and `test_watcher_move_rule.py` imports `BODY` from `branch_reading`. I read the guard `tests/test_shared_branch_helpers.py` against criteria 1 to 3. Its rows match the criteria's texts, and `copies` follows the Interface: top-level functions only, keyword-only annotations included, compared by `ast.unparse`. The shared `push_state` and `remote_document` use `stage_run_support`'s `BRANCH` and `PATH`, which equal the values the removed copies used, so the moved tests check the same thing. The coder's entry (journal 18) records `check: green` and `duplicates: 0 new`. Architecture and security: no `src/` change and no silencing marker.

    Findings:
    1. `tests/application/test_watcher.py:32`, `tests/application/test_watcher_move_rule.py:27` and `tests/entry/test_watch.py:39`: `PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"` is now dead code. Its only user was the removed `_push_state`, and no other module imports it. This is the same kind of leftover as round 0's `BODY`, so it goes beyond the move the standing leave allows. Fix: the tester deletes the constant in all three modules, under the standing leave.
    2. criterion 5 added: it needs its test. The Interface says the guard strips "one leading `_`", but only the zero-underscore and one-underscore sides are tested; `__pushed` is never tried. The fix is one more row in `test_the_guard_finds_a_copy_by_name_and_parameters_only` (`tests/test_shared_branch_helpers.py`): `def __pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:\n    ...\n` -> `[]`. The closing criteria are renumbered 6 (`make check`) and 7 (docs). No code change is needed; `removeprefix("_")` already refuses it.

    Both fixes are test changes, so the coder hands them on with `tests` (R9).

    Earlier tests (changed under the leave named):
    - tests/application/handlers/test_closed_send_back.py: standing leave (`_remote_document` moved)
    - tests/application/handlers/test_comment_handler.py: standing leave (`_remote_document` and `_error_posts` moved)
    - tests/application/handlers/test_hand_over.py: standing leave (`_error_posts` moved)
    - tests/application/handlers/test_questions.py: standing leave (`_remote_document` moved)
    - tests/application/test_acceptance_facts_disk.py: standing leave (`settings` and `records` moved to `disk_settings` and `disk_records`)
    - tests/application/test_after_agent.py: standing leave (`_head`, `_pushed` and `_pushed_state` moved; local `pushed` renamed to `document`)
    - tests/application/test_disk_recorder.py: standing leave (`settings` and `records` moved to `disk_settings` and `disk_records`)
    - tests/application/test_nested_repositories.py: standing leave (its `_pushed` import replaced by the shared `pushed`; local renamed)
    - tests/application/test_stage_finish.py: standing leave (`_head`, `_pushed` and `_pushed_state` moved; local renamed)
    - tests/application/test_stage_known_results.py: standing leave (`_pushed` moved)
    - tests/application/test_stall_labels.py: standing leave (`_pushed` and `_pushed_state` moved)
    - tests/application/test_stalls.py: standing leave (`_head`, `_pushed` and `_pushed_state` moved; local renamed)
    - tests/application/test_stop_publisher.py: standing leave (shadowing `records` fixture removed)
    - tests/application/test_stop_records_service.py: standing leave (shadowing `records` fixture and its `_records_path` removed)
    - tests/application/test_watcher.py: standing leave (`_push_state` and `BODY` moved); the dead `PATH` it leaves goes beyond the leave, see finding 1
    - tests/application/test_watcher_move_rule.py: standing leave (`_push_state` moved; `BODY` now imported); the dead `PATH` goes beyond the leave, see finding 1
    - tests/entry/test_watch.py: standing leave (`_push_state` and `BODY` moved); the dead `PATH` goes beyond the leave, see finding 1
    - tests/conftest.py: standing leave (`disk_settings` and `disk_records` added as the shared place)
    - tests/stage_run_support.py: standing leave (`pushed` added; `pushed_state` now calls it)
21. factory: started doing as self.
22. coder: Round 2: I changed no code. Both of the reviewer's findings (journal 20) are test changes, so I am handing them to the tester (R9):
    1. Delete the dead constant `PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"` from `tests/application/test_watcher.py:32`, `tests/application/test_watcher_move_rule.py:27` and `tests/entry/test_watch.py:39`, under the standing leave. I checked all three: in each module that assignment is the only place `PATH` appears.
    2. Criterion 5 needs only its test. Add one row to `test_the_guard_finds_a_copy_by_name_and_parameters_only` in `tests/test_shared_branch_helpers.py`: `def __pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:\n    ...\n` -> `[]`. That file has no `__pushed` row yet.

    What I built: nothing. Nothing under `src/factory/` changes, and the working tree holds only the factory's costs sidecar.

    Main choice: I hand on with `tests` and leave the code alone. I rejected deleting the constants myself, because the coder never edits tests.

    Refactor: I have no diff, so there was nothing to refactor.

    What the journal changed: the reviewer added criterion 5, which is already in the Acceptance criteria with the closing ones renumbered 6 and 7. The Description needs no rewrite.

    Noticed but not touched: the `docs/project-guide/README.md` lines in criterion 7 are the documenter's work.
23. factory: started tests as self.
24. tester: Round 2, a test change the human approved: I made the two test changes the coder handed on in journal 22. They answer the reviewer's findings in journal 20.

    1. I deleted the dead constant `PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"` from three earlier test files, under the standing leave in `CLAUDE.md` (*Tests*):
       - tests/application/test_watcher.py
       - tests/application/test_watcher_move_rule.py
       - tests/entry/test_watch.py

       `FEATURE` stays in all three, because `BACKLOG_PATH` still uses it. Every test keeps its name and checks the same thing.
    2. Criterion 5's test: I added one row, `two-leading-underscores`, to `test_the_guard_finds_a_copy_by_name_and_parameters_only` in `tests/test_shared_branch_helpers.py`. The row is `def __pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:\n    ...\n` -> `[]`.

    Criterion → test mapping:
    - criterion 1: tests/test_shared_branch_helpers.py::test_each_shared_helper_is_written_in_one_module (unchanged from journal 8)
    - criterion 2: tests/test_shared_branch_helpers.py::test_the_guard_finds_a_copy_by_name_and_parameters_only
    - criterion 3: tests/test_shared_branch_helpers.py::test_the_shared_helpers_read_and_write_as_the_copies_did
    - criterion 4: the unchanged test ids of the sixteen modules, which pass under `make test`
    - criterion 5: tests/test_shared_branch_helpers.py::test_the_guard_finds_a_copy_by_name_and_parameters_only[two-leading-underscores]
    - criteria 6 and 7: `make check`, and the documenter's work

    Files created: none.

    Modules the test runner could not import: none.

    Runs: `make test` is green (coverage 99.14 %), and `make lint` is green.

    `lint`: lint: green (0.6 s)
    `test`: test: green (60.7 s)
25. factory: started doing as self.
26. coder: Round 2: I changed no code. I checked the tester's fixes for the reviewer's two findings (journal 20, handed on in journal 22, made in journal 24) on the committed state:
    1. The dead `PATH` constant is gone from `tests/application/test_watcher.py`, `tests/application/test_watcher_move_rule.py` and `tests/entry/test_watch.py`. No line in those files starts with `PATH` any more.
    2. Criterion 5 now has its test: the row `two-leading-underscores` in `tests/test_shared_branch_helpers.py` (line 82).

    What I built: nothing. The Interface says no module under `src/factory/` changes. `git diff main -- . ':!factory' ':!tests'` is empty, and the working tree holds only the factory's costs sidecar.

    Main choice: I hand on to `review` unchanged. The alternative I rejected was going back over the moved test helpers. That is the tester's work (R9), and no finding is still open.

    Refactor: I have no diff, so there was nothing to change.

    What the journal changed: nothing in the meaning of the task. Criterion 5 was already in the Acceptance criteria, so the Description stands.

    Noticed but not touched: criterion 7, the `docs/project-guide/README.md` lines for `branch_reading.py` and for `disk_settings`/`disk_records`, is the documenter's work.

    `make check`: check: green (coverage 99.14 %).
27. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
    Using CPython 3.12.15 interpreter at: /usr/local/bin/python3.12
    Creating virtual environment at: .venv
    Installed 106 packages in 99ms
    Bytecode compiled 4164 files in 355ms
    All checks passed!
    Bytecode compiled 4164 files in 92ms
    lint: green (0.6 s)
    Bytecode compiled 4164 files in 125ms
    make: *** [Makefile:32: types] Error 139
28. factory: started doing as self.
29. coder: Round 2, after the stall in journal 27: I changed no code. The red check was `make types` ending with `make: *** [Makefile:32: types] Error 139`. Exit 139 is a segfault in mypy itself, not a type error, and it happened on the factory's fresh virtual environment. I could not make it happen again on the committed state:
    - `make check` ran in the foreground and is green: `check: green`, `test: green (61.3 s)`, coverage 99.14 %.
    - `make types` ran twice and was green both times: `Success: no issues found in 716 source files`.
    - A cold mypy run with an empty cache (`MYPY_CACHE_DIR` in `$TMPDIR`, `uv run mypy --strict src tests`) also finished cleanly, with exit 0 and no issues.

    So nothing in this branch's diff causes the crash. The branch changes only tests, and mypy accepts them.

    What I built: nothing. The Interface says no module under `src/factory/` changes. `git diff main -- . ':!factory' ':!tests'` is empty, and the working tree holds only the factory's costs sidecar.

    Main choice: I hand on to `review` unchanged. I rejected ending with `question` about the segfault, because it does not happen again here, on a warm or a cold mypy cache. If it happens again in the factory's check, the cause is mypy or the machine, not this story. That would be a question for the human then.

    Refactor: I have no diff, so there was nothing to change.

    What the journal changed: nothing in the meaning of the task. The Description stands.

    Noticed but not touched: the mypy segfault (Error 139) seen once in the factory's fresh-venv check, which I could not reproduce. Criterion 7, the lines in `docs/project-guide/README.md`, is the documenter's work.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 38 known, 0 gone
30. factory: started review as self.
31. reviewer: Round 2 review of `git diff main...HEAD -- . ':!factory'` against the work item. The diff has 21 files, all under `tests/`. Nothing under `src/factory/` changes, as the Interface says.

    Round 1's findings (journal 20) are fixed:
    - The dead `PATH` constant is gone from `tests/application/test_watcher.py`, `tests/application/test_watcher_move_rule.py` and `tests/entry/test_watch.py`.
    - Criterion 5 has its row, `two-leading-underscores`, in `tests/test_shared_branch_helpers.py`.

    Acceptance criteria:
    - Criteria 1, 2 and 5 are the rows of two parametrized tests in `tests/test_shared_branch_helpers.py`. The rows match the source texts the criteria give. `copies` follows the Interface: top-level functions only, keyword-only annotations included, compared through `ast.unparse`, and `removeprefix("_")` strips exactly one underscore.
    - Criterion 3 is `test_the_shared_helpers_read_and_write_as_the_copies_did`. It pushes a state of stage `doing` with pull request 1, reads it back through `remote_document` and through `pushed_state`, and posts one `error` and one `cost_table` post to show that `error_posts` returns only the `error` one.
    - Criterion 4 holds when the diff is read: no `def test_`, `pytest.param` or `@pytest.mark` line is added or removed in any earlier module.

    Two more things I checked:
    - The shared helpers use `stage_run_support`'s `BRANCH` and `PATH`, which have the values the removed copies used.
    - No top-level name in the changed modules is left unused, apart from tests and fixtures.

    On `make check`: journal 27 records the factory's one red `make types` (Error 139, a mypy segfault). The coder's rerun (journal 29) was green, and the factory's check then let the stage move forward.

    Architecture and security: no `src/` change and no silencing marker. The Description, the Interface and docs criterion 7 still match what was built.

    I considered one more point and rejected it as a finding: `tests/application/test_stalls.py:252` keeps its local variable `pushed`, which now hides the imported helper inside that one test. The helper is not called in that test, and the line is unchanged from `main`.

    no findings

    Earlier tests (changed under the leave named):
    - tests/application/handlers/test_closed_send_back.py: standing leave (`_remote_document` moved)
    - tests/application/handlers/test_comment_handler.py: standing leave (`_remote_document` and `_error_posts` moved)
    - tests/application/handlers/test_hand_over.py: standing leave (`_error_posts` moved)
    - tests/application/handlers/test_questions.py: standing leave (`_remote_document` moved)
    - tests/application/test_acceptance_facts_disk.py: standing leave (`settings` and `records` moved to `disk_settings` and `disk_records`)
    - tests/application/test_after_agent.py: standing leave (`_head`, `_pushed` and `_pushed_state` moved; local `pushed` renamed to `document`)
    - tests/application/test_disk_recorder.py: standing leave (`settings` and `records` moved to `disk_settings` and `disk_records`)
    - tests/application/test_nested_repositories.py: standing leave (its `_pushed` import replaced by the shared `pushed`; a local renamed)
    - tests/application/test_stage_finish.py: standing leave (`_head`, `_pushed` and `_pushed_state` moved; a local renamed)
    - tests/application/test_stage_known_results.py: standing leave (`_pushed` moved)
    - tests/application/test_stall_labels.py: standing leave (`_pushed` and `_pushed_state` moved)
    - tests/application/test_stalls.py: standing leave (`_head`, `_pushed` and `_pushed_state` moved; a local renamed)
    - tests/application/test_stop_publisher.py: standing leave (the shadowing `records` fixture removed)
    - tests/application/test_stop_records_service.py: standing leave (the shadowing `records` fixture and its `_records_path` removed)
    - tests/application/test_watcher.py: standing leave (`_push_state` moved, with its `PATH` and `BODY`)
    - tests/application/test_watcher_move_rule.py: standing leave (`_push_state` and `PATH` moved; `BODY` now imported from `branch_reading`)
    - tests/entry/test_watch.py: standing leave (`_push_state` moved, with its `PATH` and `BODY`)
    - tests/conftest.py: standing leave (`disk_settings` and `disk_records` added as the shared place)
    - tests/stage_run_support.py: standing leave (`pushed` added; `pushed_state` now calls it)
32. factory: started docs as self.
33. documenter: Docs round 2. I read the story, the journal and the diff (21 files, all under `tests/`; nothing under `src/factory/` changes). I changed one file, and it is a document, so I did not run `make check`; the factory's check after this stage decides.

    Changed:
    - `docs/project-guide/README.md`, *Shared test helpers*:
      - Added the `branch_reading.py` line after `bill_support.py`, in the form of the other lines (criterion 7).
      - Added `disk_settings` and `disk_records` to the `conftest.py` line under *Paths and settings* (criterion 7).
      - Added `pushed` and `pushed_state` to the `stage_run_support.py` line. Criterion 7 does not ask for this, but the diff moved `pushed` there and the line lists the module's helpers, so it would otherwise be stale.
    - I ran the two smoke-test greps for the docs: both print `1`.

    Cross-read and found current: `README.md`, `docs/operator-guide.md` and `docs/decisions.md`. Nothing an operator or a newcomer sees changes, and no decision is taken, as criterion 7 says. The rest of the *Shared test helpers* list is also still true against the diff.

    Findings: none. The code (tests only) matches the Interface and the criteria.

    Stale text I noticed and did not touch: none from this story. `docs/runs/2026-10-12-overnight/night-log.md` mentions that this story's "docs: none" was false. That file is the human's, and the criterion has since been fixed.

    `check`: check: green (not run again: passed on tree eca9aa518208 at 2026-10-21T01:36:48Z)
    `secrets`: secrets: green (1.5 s)
    `documents`: documents ok
34. factory: started smoke-test as self.
