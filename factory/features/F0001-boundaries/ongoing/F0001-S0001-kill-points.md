---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Kill points in the wrappers

## Assignment (as of log entry 1)

Create the injection seam of R36 and the root of the factory's error hierarchy. `KillPoints` holds four named points that are inert until a test arms one; reaching an armed point raises `InjectedKill`, a `BaseException`, so that no handler's `except Exception` survives it, just as no handler survives a real death. This story builds only the seam. The wrappers reach the points in their own stories (the fake hosting service and the PyGithub client reach `after-post`, the git wrapper reaches `before-push` and `after-push`, the two agent runtimes reach `agent-run`), each with its own criterion; the tests that use the points to prove recovery come in F0008 and F0011. Covers R36 (the seam); keeps kept thing 13 (recover by construction) by making a crash testable. It also creates `factory.domain.errors` with `FactoryError`, the root that the later stories add their error types to.

## Interface

`src/factory/domain/errors.py`

```python
class FactoryError(Exception):
    """Every error the factory raises on purpose."""
```

`src/factory/domain/kill_points.py`

```python
class KillPoint(StrEnum):
    AGENT_RUN = "agent-run"
    BEFORE_PUSH = "before-push"
    AFTER_POST = "after-post"
    AFTER_PUSH = "after-push"

class InjectedKill(BaseException):
    point: KillPoint
    def __init__(self, point: KillPoint) -> None: ...

class KillPoints:
    def __init__(self) -> None: ...
    def arm(self, point: KillPoint, *, after: int = 0) -> None: ...
    def reach(self, point: KillPoint) -> None: ...
    def reached(self, point: KillPoint) -> int: ...
```

The rules, each with a criterion below:

- A new `KillPoints` is inert: `reach` never raises on it.
- `arm(point, after=n)` makes the point raise `InjectedKill(point)` on its (n + 1)-th reach counted from the arming; `after=0` fires on the next reach. `after` below 0 raises `ValueError` and changes nothing.
- A point fires once and is then disarmed. Arming a point that is already armed replaces the earlier arming. Arming one point leaves the others as they were.
- `reached(point)` counts every call of `reach(point)`, the one that raises included, whether or not the point was armed.
- Each `KillPoints` instance keeps its own state.
- `str(InjectedKill(point))` is `injected kill at <point value>`. `InjectedKill` is a `BaseException` and not a `FactoryError`.
- Both modules are pure domain code: nothing from the standard library that touches the outside world.

Tests: `tests/domain/test_kill_points.py` and `tests/domain/test_errors.py`; `tests/conftest.py` is created here with the fixture `kill_points`, which returns a new `KillPoints()` for each test.

## Acceptance criteria

1. `KillPoint` is a `StrEnum` with exactly four members: `AGENT_RUN` with value `"agent-run"`, `BEFORE_PUSH` with `"before-push"`, `AFTER_POST` with `"after-post"` and `AFTER_PUSH` with `"after-push"`.
2. On a new `KillPoints`, `reach(point)` returns `None` and raises nothing, for each of the four points, five times in a row.
3. `reached(point)` is 0 for every point of a new `KillPoints`; after three reaches of `AGENT_RUN` and one of `AFTER_POST` it is 3 for `AGENT_RUN`, 1 for `AFTER_POST` and 0 for the other two.
4. After `arm(point)`, the next `reach(point)` raises `InjectedKill`, and the exception's `point` is that point.
5. After `arm(point, after=2)`, the first two reaches of the point return and the third raises.
6. After a raise the point is disarmed: the next `reach` returns. `reached` counts the raising reach too: 1 right after the raise, 2 after the next reach.
7. Arming one point leaves the other three inert: reaching them raises nothing.
8. `after` counts from the arming, not from the start: after two reaches of a point, `arm(point)` makes the third reach raise.
9. Arming an armed point replaces the earlier arming: `arm(point, after=3)` followed by `arm(point)` makes the next reach raise.
10. `arm(point, after=-1)` raises `ValueError` and leaves the point inert, and on a point that is already armed it leaves the earlier arming as it was; `arm(point, after=0)` is accepted.
11. `InjectedKill` is a `BaseException` and not an `Exception`: a function that calls `reach` inside `try` with `except Exception` does not stop it, and `pytest.raises(InjectedKill)` around that function sees it.
12. `str(InjectedKill(KillPoint.AFTER_PUSH))` is `injected kill at after-push`, and `InjectedKill` is not a subclass of `FactoryError`.
13. `FactoryError` is a subclass of `Exception`, and `str(FactoryError("x"))` is `x`.
14. Two `KillPoints` instances are independent: arming a point on one does not make the same point raise on the other.
15. Neither `factory.domain.kill_points` nor `factory.domain.errors` imports `os`, `subprocess`, `time`, `socket` or `pathlib` (a test parses both files with `ast`).
16. make check stays green.
17. docs: `docs/project-guide.md` explains how a test arms a kill point (the `kill_points` fixture, `arm`, `after`) and names which wrapper reaches which of the four points; `docs/decisions.md` records why `InjectedKill` is a `BaseException` (WE6.3).

## Demo

```bash
uv run python -c "
from factory.domain.kill_points import KillPoint, KillPoints, InjectedKill
kp = KillPoints()
kp.arm(KillPoint.BEFORE_PUSH, after=1)
for attempt in (1, 2, 3):
    try:
        kp.reach(KillPoint.BEFORE_PUSH)
        print(attempt, 'passed')
    except InjectedKill as kill:
        print(attempt, kill)
print(kp.reached(KillPoint.BEFORE_PUSH), kp.reached(KillPoint.AGENT_RUN))
"
```
Expect: four lines, `1 passed`, `2 injected kill at before-push`, `3 passed`, then `3 0`: the point fired on its second reach only, and the counts include the raising reach.

```bash
uv run python -c "
from factory.domain.kill_points import KillPoint, KillPoints, InjectedKill
kp = KillPoints()
kp.arm(KillPoint.AGENT_RUN)
try:
    try:
        kp.reach(KillPoint.AGENT_RUN)
    except Exception:
        print('swallowed')
except BaseException as kill:
    print(type(kill).__name__, issubclass(InjectedKill, Exception))
"
```
Expect: one line, `InjectedKill False`; the word `swallowed` is not printed.

## Log (append only)

1. 2026-10-12 human: created.
