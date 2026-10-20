---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 367
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-20T22:53:23.829247Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T22:45:08.045041Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T22:45:08.050814Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T22:45:25.711472Z'
  stage: intake
  run: 5c182e5ae5d44a1c930d81a82d122eb6
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T22:45:45.921365Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T22:48:40.052242Z'
  stage: tests
  run: 86768edae34e4cc28d5ce478dfe7f667
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T22:49:01.382584Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T22:51:46.932024Z'
  stage: doing
  run: e82aa699027b45be8f0cf59b79c9984e
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T22:52:07.634926Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T22:52:29.377963Z'
  stage: review
  run: 197e98e6e8d64995a6498309ced3184e
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T22:52:50.030439Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T22:53:03.204061Z'
  stage: docs
  run: 6e7720c4b98b43489b77c3f98f0ed8df
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T22:53:23.829247Z'
  stage: smoke-test
---

# The shared time limits' test names the values of a relation that broke

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

`tests/test_time_limits.py::test_the_roomy_limit_leaves_room_and_stays_below_every_wait` (F0029-S0002) pins the relations between `ROOMY_LIMIT`, `ROOMY_BOUND_SECONDS`, the stand-ins' `WAIT_SECONDS` and the `sudo` test's `PAST_LIMIT_SECONDS`. Each of its nine rows is a `bool` worked out when pytest collects the module, so a row that breaks prints only `assert False`. Whoever raises a stand-in's wait, or the limit, then has to work out by hand which two numbers no longer fit. This story makes each row carry its two values and the relation between them (`operator.eq`, `operator.gt`, `operator.ge`, `operator.lt`), so a failing row prints both values and the relation's name. The nine rows keep their ids and check the same relations; `tests/time_limits.py`, every other test and every module under `src/` stay as they are. Found by the reviewer of F0029-S0002 (journal entry 17, *Notes*) and owned by nobody since.

## Interface

No module under `src/factory/` changes; the coder has nothing to build.

`tests/test_time_limits.py` (F0029-S0002's test, changed by the tester under the leave of `feature.md`, decision 9, S0003):

```python
@pytest.mark.parametrize(
    ("left", "relation", "right"),
    [
        pytest.param(ROOMY_LIMIT.total_seconds(), operator.eq, 10.0, id="limit"),
        pytest.param(ROOMY_BOUND_SECONDS, operator.eq, 25, id="bound"),
        pytest.param(ROOMY_BOUND_SECONDS - ROOMY_LIMIT.total_seconds(), operator.ge, 10, id="room"),
        # ... the six rows of the waits and of PAST_LIMIT_SECONDS, ids unchanged
    ],
)
def test_the_roomy_limit_leaves_room_and_stays_below_every_wait(
    *, left: float, relation: Callable[[float, float], bool], right: float
) -> None:
    assert relation(left, right), f"{left} {relation.__name__} {right}"
```

- The test keeps its name and its nine row ids: `limit`, `bound`, `room`, `claude-confinement-wait`, `stand-in-wait`, `resume-session-wait`, `events-wait`, `sudo-past-limit`, `sudo-within-bound`.
- Each row's `left`, `relation` and `right` state the same relation the row's `bool` states today, with the same constants read from the same modules.
- A row that does not hold fails with the message `<left> <relation name> <right>`, such as `30 gt 30`.
- `test_a_relation_that_breaks_names_its_values` (new, in the same module) calls the test above directly, as criterion 2 says. `timedelta` leaves the module's imports, as nothing else there uses it.

The leave: `feature.md`, decision 9, S0003, lets the tester change `tests/test_time_limits.py`, written by F0029-S0002, beyond the standing leave of `CLAUDE.md`, as this Interface says and in nothing else.

## Acceptance criteria

1. Every relation still holds: `test_the_roomy_limit_leaves_room_and_stays_below_every_wait` passes with its nine rows, ids as listed in the Interface.
2. A relation that breaks names its values (rows of one parametrized test, `test_a_relation_that_breaks_names_its_values`): calling `test_the_roomy_limit_leaves_room_and_stays_below_every_wait` directly with `left=30, relation=operator.gt, right=30` raises `AssertionError` whose message's first line is `30 gt 30` (inside pytest, its assertion rewriting adds its own explanation on the lines below); with `left=11.5, relation=operator.lt, right=25` it returns without raising.
3. `make check` stays green.
4. docs: none. No operator, newcomer or agent reads the test's failure message from the documents; `docs/project-guide/processes-and-checks.md` names `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS`, which stay as they are.

## Smoke test

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_time_limits.py::test_the_roomy_limit_leaves_room_and_stays_below_every_wait 2>&1 | tail -1 | cut -d' ' -f1-2
```
Expect: `9 passed`

```bash
uv run -q python - <<'PY'
import operator, sys
sys.path.insert(0, "tests")
from test_time_limits import test_the_roomy_limit_leaves_room_and_stays_below_every_wait as check
try:
    check(left=30, relation=operator.gt, right=30)
except AssertionError as error:
    print(error)
PY
```
Expect: `30 gt 30`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: no `src/` change, which is right for a test-only story. It names the one test (`tests/test_time_limits.py::test_the_roomy_limit_leaves_room_and_stays_below_every_wait`), its `left`/`relation`/`right` signature, the failure message format, the nine row ids, the new test and the dropped `timedelta` import. The leave for changing F0029-S0002's test is stated (feature.md, decision 9, S0003).
   Criteria: 1 (the nine rows pass) and 2 (message `30 gt 30` for a broken relation, a return for `11.5 lt 25`) are each testable by one test function. The only rule here is the message, and both its failing side and its passing side have a criterion. Criterion 3 is `make check`. Criterion 4 is `docs: none`, with a stated reason.
   Smoke test: both blocks are runnable. `pyproject.toml` already sets `-q` in `addopts`, and the command does not repeat it, so the last line is `9 passed in ...` and the `cut` gives `9 passed`. The second block prints the first line of the assertion message, `30 gt 30`, and the `Expect:` lines are checkable.
   Architecture: only `tests/` changes, and the test sits at the `tests/` root because it tests a module outside the layers. `tests/time_limits.py` and `src/` stay as they are.
   Scope: the change falls inside feature.md's scope (S0003 is named for `tests/test_time_limits.py`, "its failure message") and touches nothing in its Out of scope list.
4. factory: started tests as self.
5. tester: Changed `tests/test_time_limits.py` (written by F0029-S0002) under the leave in `feature.md`, decision 9, S0003, and only as far as the Interface says. No other test file changed. No files were created.

   Criteria → tests:
   - criterion 1: tests/test_time_limits.py::test_the_roomy_limit_leaves_room_and_stays_below_every_wait. It keeps its name and its nine row ids (limit, bound, room, claude-confinement-wait, stand-in-wait, resume-session-wait, events-wait, sudo-past-limit, sudo-within-bound). Each row is now `(left, relation, right)` and states the same relation the row's `bool` stated before, with the same constants from the same modules. The `limit` row is now `ROOMY_LIMIT.total_seconds() eq 10.0`, as the Interface writes it. On failure the test prints `f"{left} {relation.__name__} {right}"`.
   - criterion 2: tests/test_time_limits.py::test_a_relation_that_breaks_names_its_values. It has two rows, `broken` and `holds`. Each calls the test above directly. `broken` (30 gt 30) expects an `AssertionError` whose message's first line is `30 gt 30`; `holds` (11.5 lt 25) expects no error.
   - criterion 3: `make check`. The factory and the coder cover it.
   - criterion 4: docs: none.

   The `timedelta` import is gone; `operator` and `collections.abc.Callable` were added.

   Red/green: these tests are not red. The story changes no module under `src/`, so all 11 tests pass already (`make test`: `test: green (61.6 s)`). The coder has nothing to build. No module failed to import. `make lint` is green. I also ran pytest once on this module alone and mypy --strict on this file: mypy reported nothing in `tests/test_time_limits.py`. Its other errors were import-untyped errors in the modules this file imports, which come from running mypy outside `make types`.

   `lint`: lint: green (0.6 s)
   `test`: test: green (63.2 s)
6. factory: started doing as self.
7. coder: Built nothing. The Interface says no module under `src/factory/` changes, and the tester's change to `tests/test_time_limits.py` already passes against the code as it is. I edited no file.

   Main choice: I handed forward with an empty diff and did not add anything under `src/`. The alternative was to look for production code for this story, and I rejected it because the Interface says "the coder has nothing to build". Anything I added would go beyond the description (R13).

   Refactor: there was no diff of my own to read, so nothing needed changing.

   Description: the journal does not change what the task means, so I did not rewrite it.

   Noticed but did not touch: nothing.

   `make check`: check: green (test: green (61.3 s), total coverage 99.14 %).

   `check`: check: green
   `duplicates`: duplicates: 6 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'` contains one file, `tests/test_time_limits.py`, plus the work item. Nothing under `src/` changed, which matches the Interface.

   - Criterion 1: `test_the_roomy_limit_leaves_room_and_stays_below_every_wait` keeps its name and its nine ids (limit, bound, room, claude-confinement-wait, stand-in-wait, resume-session-wait, events-wait, sudo-past-limit, sudo-within-bound). Each row is now `(left, relation, right)` and states the same relation as the old `bool`, with the same constants from the same modules. The `limit` row changed from `timedelta(seconds=10) == ROOMY_LIMIT` to `ROOMY_LIMIT.total_seconds() eq 10.0`, which means the same thing and is the form the Interface writes. The failure message is `f"{left} {relation.__name__} {right}"`, as the Interface says.
   - Criterion 2: `test_a_relation_that_breaks_names_its_values` is one parametrized test with two rows. `broken` (30 gt 30) checks that the first line of the `AssertionError` message is `30 gt 30`. `holds` (11.5 lt 25) checks that the call returns without raising. Both sides of the one rule are covered, as rows of the same test.
   - Criterion 3: the factory's `make check` after the coder was green (entry 7: `check: green`).
   - Criterion 4: docs: none, with a reason that still holds; `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS` stay as they are.
   - `timedelta` is no longer imported. `operator` and `collections.abc.Callable` were added and are used. There is no dead code, and no helper is copied.
   - Architecture and security: the change is test-only, at the `tests/` root, which is right for testing a module outside the layers. It adds no suppression marker.
   - Work item hygiene: the Description matches what was built. The tester's and the coder's entries explain the empty coder diff and why the tests were green from the start.

   Earlier tests:
   - `tests/test_time_limits.py` (M, written by F0029-S0002): changed under the human's leave in `feature.md`, decision 9, S0003 (the human, 2026-10-20). The change stays within that leave: same test name, nine row ids and relations, the message, the new test, and the `timedelta` import removed.
10. factory: started docs as self.
11. documenter: Docs criterion is `none`, so I wrote nothing new and changed no file. I ran no `make check`, because I changed no file.

    The diff outside `factory/` and `docs/` is one file, `tests/test_time_limits.py`: the nine rows now carry `(left, relation, right)`, plus the new test for the failure message. No module under `src/` changed.

    Cross-read and found current:
    - `docs/project-guide/processes-and-checks.md` (line 125) names `ROOMY_LIMIT` (10 s) and `ROOMY_BOUND_SECONDS` (25) from `tests/time_limits.py`. Both are unchanged, and the text matches the code.
    - `docs/decisions.md` (line 896) says the same about those constants and is current.
    - `README.md` and `docs/operator-guide.md` do not mention the test or its failure message.

    Stale text noticed and not touched: none.

    `check`: check: green (not run again: passed on tree fb0e305c50f3 at 2026-10-20T22:50:35Z)
    `secrets`: secrets: green (0.6 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
