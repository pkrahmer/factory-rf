---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 367
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-20T22:49:01.382584Z'
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
