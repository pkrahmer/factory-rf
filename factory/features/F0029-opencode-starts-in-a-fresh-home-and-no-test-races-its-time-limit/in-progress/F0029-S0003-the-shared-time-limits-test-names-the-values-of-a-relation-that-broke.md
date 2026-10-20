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
