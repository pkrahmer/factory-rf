---
stage: review
pr: 1
blocked: null
comments_seen: 4
round: 1
attempts: 0
---
# Kill points in the wrappers

## Assignment (as of log entry 10)

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
16. Arming one point leaves an armed other point as it was: after `arm(BEFORE_PUSH, after=1)` and then `arm(AFTER_PUSH)`, the first reach of `BEFORE_PUSH` returns and the second raises.
17. make check stays green.
18. docs: `docs/project-guide.md` explains how a test arms a kill point (the `kill_points` fixture, `arm`, `after`) and names which wrapper reaches which of the four points; `docs/decisions.md` records why `InjectedKill` is a `BaseException` (WE6.3).

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
2. intake: accepted
   - Interface: `factory.domain.errors` (`FactoryError`) and `factory.domain.kill_points` (`KillPoint`, `InjectedKill`, `KillPoints` with `arm`, `reach`, `reached`) are concrete, with signatures and defaults. The `kill_points` fixture in `tests/conftest.py` is named. Every behaviour in the Interface rules has a criterion.
   - Criteria: the 14 behavioural criteria (1–14) and the structural one (15) can each be tested by one test function without further decisions. Every rule has its failing side: negative `after` leaves an inert or armed point unchanged (10), the other points stay inert (7), the point is disarmed after firing (6), the instances are independent (14), and `InjectedKill` is not an `Exception` or a `FactoryError` (11, 12). The only gap is that no criterion says an armed point stays armed when another point is armed. Criterion 7 covers the inert side and the story rule reads "as they were", so I did not treat it as a blocker.
   - Demo: both commands are runnable with `uv run python -c`. The expected output of each can be checked line by line: `1 passed`, `2 injected kill at before-push`, `3 passed`, `3 0`, and `InjectedKill False` with no `swallowed`.
   - Architecture: both modules sit in `factory.domain` with no I/O, which fits the four layers in `CLAUDE.md`. The tests mirror the package under `tests/domain/`, and the criterion 17 docs targets are the ones `CLAUDE.md` assigns to the documenter.
   - Scope: the story builds only the seam (R36) and the error root, as `FEATURE.md` scope item 1 says. Wiring the points into the wrappers and the kill-point tests are left to later stories and to F0011, which matches "Out of scope".
3. tester: wrote red tests for criteria 1–15, one test function for each.
   - criterion 1: tests/domain/test_kill_points.py::test_kill_point_has_exactly_the_four_named_members
   - criterion 2: tests/domain/test_kill_points.py::test_new_kill_points_never_raise (parametrized over the four points, 5 reaches each)
   - criterion 3: tests/domain/test_kill_points.py::test_reached_counts_every_reach_per_point
   - criterion 4: tests/domain/test_kill_points.py::test_armed_point_raises_injected_kill_on_next_reach
   - criterion 5: tests/domain/test_kill_points.py::test_after_lets_that_many_reaches_pass_first
   - criterion 6: tests/domain/test_kill_points.py::test_point_is_disarmed_after_it_fires_and_the_raising_reach_counts
   - criterion 7: tests/domain/test_kill_points.py::test_arming_one_point_leaves_the_others_inert
   - criterion 8: tests/domain/test_kill_points.py::test_after_counts_from_the_arming
   - criterion 9: tests/domain/test_kill_points.py::test_arming_an_armed_point_replaces_the_earlier_arming
   - criterion 10: tests/domain/test_kill_points.py::test_after_must_not_be_negative checks the boundary (-1 raises ValueError and leaves the point inert; 0 is accepted and fires on the next reach). tests/domain/test_kill_points.py::test_negative_after_leaves_an_earlier_arming_as_it_was checks that arm(after=1), then a rejected arm(after=-1), lets one reach pass and raises on the second.
   - criterion 11: tests/domain/test_kill_points.py::test_injected_kill_passes_through_except_exception
   - criterion 12: tests/domain/test_kill_points.py::test_injected_kill_message_names_the_point_and_is_no_factory_error
   - criterion 13: tests/domain/test_errors.py::test_factory_error_is_an_exception_with_its_message
   - criterion 14: tests/domain/test_kill_points.py::test_two_kill_points_instances_are_independent
   - criterion 15: tests/domain/test_kill_points.py::test_domain_modules_import_nothing_that_touches_the_outside. It finds each module's source through importlib.util.find_spec without importing the module, parses it with ast, and checks the top-level names of `import` and absolute `from` imports.

   Files created: tests/conftest.py (the `kill_points` fixture returns a new KillPoints() for each test), tests/domain/__init__.py, tests/domain/test_kill_points.py, tests/domain/test_errors.py.

   Red as intended: `make test` fails while loading tests/conftest.py with ModuleNotFoundError: No module named 'factory.domain.kill_points'. Because the conftest import fails, pytest aborts the whole run, so tests/test_layers.py does not run either until the module exists. factory.domain.errors is missing as well. `make lint` is green.

   Rejected: importing KillPoints lazily inside the fixture so the rest of the suite could still collect. A top-level import is the normal idiom, and the run stays red for the right reason. Not tested, because no criterion names it: whether arming one point leaves an already armed point armed (intake noted this gap).

   `make lint`: lint: green
   `make test`: E   ModuleNotFoundError: No module named 'factory.domain.kill_points'
4. coder: implemented the seam in commit 0d091ba, but `make check` is red because of how the tests are written. I have not changed them.
      - Built: `src/factory/domain/errors.py` (`FactoryError`) and `src/factory/domain/kill_points.py` (`KillPoint`, `InjectedKill`, `KillPoints`). `KillPoints` keeps a reach count for every point, and for each armed point the number of reaches still allowed to pass. Arming overwrites that number, firing deletes it, and a negative `after` raises before anything changes. `make test` is green with 100 % coverage, and the first demo prints the expected four lines.
      - Contradiction: `make types` (`mypy --strict` over `tests`) fails with 6 errors `func-returns-value` in `tests/domain/test_kill_points.py`, at lines 33, 75, 86, 118, 128 and 162. Each of those lines writes `assert kill_points.reach(point) is None`. The interface fixes `reach(...) -> None`, and mypy rejects using the value of a function that returns None. The tester could not see this, because mypy could not run before the module existed. No implementation that keeps the interface can satisfy both the tests and `make check`.
      - Options: (a) the tester changes those six lines to call `kill_points.reach(point)` without `assert ... is None`. The test still fails if `reach` raises, so criterion 2 stays covered. (b) Relax mypy's `func-returns-value` for `tests/` in `pyproject.toml`, which weakens a check to fit a test. (c) Change `reach`'s return type away from `None`, which breaks the interface.
      - I would choose (a). If you agree, the next doing run ends with `tests` and names that change.
5. human (pull request comment, 2026-10-12): (a): the tester changes the six lines to call `kill_points.reach(point)` without `assert ... is None`; the test still fails if `reach` raises, so criterion 2 stays covered. The interface (`reach(...) -> None`) and mypy's settings stay as they are.
6. coder: the human's answer (entry 5, option a) calls for a test change. I have not touched the test and the implementation stays as it was (commit 0d091ba).
      - Change for the tester: in `tests/domain/test_kill_points.py`, lines 33, 75, 86, 118, 128 and 162, replace `assert <kp>.reach(<point>) is None` with a plain call `<kp>.reach(<point>)`. That is `kill_points.reach(point)`, `kill_points.reach(other)` on line 86 and `untouched.reach(point)` on line 162. These lines fail `mypy --strict` with `func-returns-value`.
      - Unchanged: the interface stays `reach(...) -> None`, and the mypy settings stay as they are. Once those six lines are changed, `make check` should be green with no further work from the coder.
7. tester: made the test change the human approved in entry 5 (option a), as entry 6 names it. Nothing else changed.
      - Changed: `tests/domain/test_kill_points.py`, lines 33, 75, 86, 118, 128 and 162. Each `assert <kp>.reach(<point>) is None` is now a plain call: `kill_points.reach(point)` five times, and `untouched.reach(point)` on line 162. On line 86 the call is `kill_points.reach(other)`.
      - Why: `reach` is typed `-> None`, so `mypy --strict` rejected using its value (`func-returns-value`). The test still fails if `reach` raises, so criterion 2 is still covered, and so are the other criteria that use these lines (5, 6, 7, 10 and 14). The interface and the mypy settings are unchanged.
      - Diff: 6 lines changed in that one file.
      - `make test`: green, 100 % coverage. `make lint`: green. I did not run `make types` myself; the coder's entry 6 expects `make check` to be green with this change.

   `make lint`: lint: green
   `make test`: test: green
8. coder: with the tester's change from entry 7 in place, `make check` is green (100 % coverage). This round needed no new code: the implementation is still the one in commit 0d091ba.
      - Built: `src/factory/domain/errors.py` has `FactoryError`. `src/factory/domain/kill_points.py` has `KillPoint`, `InjectedKill` and `KillPoints`. `KillPoints` keeps a reach count for every point, plus a map from each armed point to the number of reaches still allowed to pass. Arming overwrites that number, which gives replacement for free. Firing deletes the entry, which disarms the point. A negative `after` raises `ValueError` before anything changes, so an earlier arming is kept. Each instance keeps its own state, and the module imports only `enum`.
      - Design decision: I store a "passes left" countdown for each armed point. The alternative was to store an absolute target reach number taken from `reached` at arming time. I rejected it because the countdown makes "counts from the arming" structural: no arithmetic on the global count is needed.
      - Demos: both print exactly the expected output. The first prints `1 passed`, `2 injected kill at before-push`, `3 passed`, `3 0`. The second prints `InjectedKill False`, and `swallowed` is not printed.
      - Refactor: I read the diff and found nothing to rename, simplify or remove, so there is no refactor commit.
      - Noticed, not touched: the intake gap still stands. No test checks that arming one point leaves an already armed point armed. The implementation does keep it armed, because the map is per point. Criterion 17 (the docs) belongs to the documenter.

   `make check`: check: green
9. reviewer: I read the full diff. One gap in the story stops me from passing it. The coder cannot fix it, so I am asking instead of sending the ticket back to doing.

   **The gap.** The Interface rule "Arming one point leaves the others as they were" has no criterion for its failing side when the other point is already armed. Criterion 7 covers only other points that are still inert. No test checks that `arm(A)` leaves an earlier `arm(B, after=n)` as it was. The intake (entry 2), the tester (entry 3) and the coder (entry 8) each noted this gap and left it open. The checklist says a rule without its failing side is a finding against the story, so I am raising it with you.

   The code is correct on this point. In `src/factory/domain/kill_points.py`, `_passes_left` is a separate entry for each point, so arming one point does not touch another. What is missing is the test.

   **Options:**
   - (a) Add a criterion before the two closing ones: "Arming one point leaves an armed other point as it was: after `arm(BEFORE_PUSH, after=1)` and then `arm(AFTER_PUSH)`, the first reach of `BEFORE_PUSH` returns and the second raises." The ticket goes back to doing, ends with `tests`, and the tester adds one test for it. No code changes.
   - (b) Accept the gap as it is, with criterion 7 covering only the inert case. I would then pass the review on the next run.

   **My recommendation is (a).** It costs one test and closes the last uncovered rule of the seam that F0008 and F0011 will rely on.

   **What I checked besides the gap:**
   - Acceptance criteria: the tests for criteria 1–15 match their criteria. The boundary of criterion 10 is tested on both sides (−1 is rejected and 0 is accepted), including the case where a rejected `arm` leaves an earlier arming in place. The coder reports `make check` green in entry 8.
   - Architecture: both modules are in `factory.domain` and import only `enum`.
   - Security: nothing to report. The only marker is the `# noqa: BLE001` in the test, and its reason is written beside it.
   - Quality: docstrings are present and accurate, and there is no dead code.
   - Ticket hygiene: the log explains the countdown design and why the alternative was rejected.
   - The `CLAUDE.md` and `docs/runs/` lines in the diff are your own commits merged from main (78d9609, 0f1bbf5), so I did not review them.
10. human (pull request comment, 2026-10-12): (a): add the criterion before the two closing ones, exactly as you worded it: "Arming one point leaves an armed other point as it was: after `arm(BEFORE_PUSH, after=1)` and then `arm(AFTER_PUSH)`, the first reach of `BEFORE_PUSH` returns and the second raises." Back to doing, ending with `tests`; the tester adds the one test. It closes the failing side of an Interface rule (the story's own rule).
11. reviewer: I followed the human's answer in entry 10 (option a) and found one finding. The ticket goes back to doing.

    Ticket edit: I added the human's criterion word for word as criterion 16, ahead of the two closing ones, which are now 17 (make check) and 18 (docs). The Assignment heading now reads "as of log entry 10". The text of the Assignment and the Interface did not change, because the Interface rule "Arming one point leaves the others as they were" already covers the new criterion.

    Findings:
    1. `tests/domain/test_kill_points.py`: criterion 16 has no test. Fix: the coder ends with `tests` and names one new test, for example `test_arming_one_point_leaves_an_armed_other_point_as_it_was`. It should call `arm(KillPoint.BEFORE_PUSH, after=1)` and then `arm(KillPoint.AFTER_PUSH)`. The first `reach(BEFORE_PUSH)` should return and the second should raise `InjectedKill`. No code change is needed: in `src/factory/domain/kill_points.py`, `_passes_left` keeps each point's arming separate, so the new test should pass against commit 0d091ba as it is.

    Checked again in this round, all as entry 9 found them:
    - The tests for criteria 1–15 match their criteria. Criterion 10 is tested on both sides of the boundary (−1 and 0), including the case where an earlier arming must survive.
    - The coder reported `make check` green in entry 8.
    - Both modules import only `enum`.
    - No markers apart from the `# noqa: BLE001` in the test, which has its reason written beside it.
    - Docstrings are present and accurate.
    - The log explains the countdown design and the alternative it rejected.

    Not reviewed: the changes to `planning/`, `docs/runs/`, `CLAUDE.md` and `factory/features/F0001-boundaries/` other than this ticket come from the human's own commits on the branch (80e084e, 78d9609, 0f1bbf5), not from this ticket's work.
12. coder: the human's answer in entry 10 (option a) needs one new test for criterion 16 and no code change. I have not touched the tests, and the implementation stays as it is in commit 0d091ba.
       - Change for the tester: add one test function, `test_arming_one_point_leaves_an_armed_other_point_as_it_was`, to `tests/domain/test_kill_points.py`. Using the `kill_points` fixture, it calls `arm(KillPoint.BEFORE_PUSH, after=1)` and then `arm(KillPoint.AFTER_PUSH)`. The first `reach(KillPoint.BEFORE_PUSH)` should return (a plain call, without `assert ... is None`, as CLAUDE.md requires), and the second should raise `InjectedKill` with `point == KillPoint.BEFORE_PUSH`.
       - Why it should pass as it is: in `src/factory/domain/kill_points.py`, `KillPoints.arm` writes only `_passes_left[point]`, so arming `AFTER_PUSH` leaves the `BEFORE_PUSH` countdown alone. I have not run this test, because it does not exist yet.
       - Not touched: criterion 18 (docs) is the documenter's.
13. tester: added the one test that the human approved in entry 10 (option a), as the coder's entry 12 names it. Nothing else changed.
       - Added: `tests/domain/test_kill_points.py::test_arming_one_point_leaves_an_armed_other_point_as_it_was`. It sits directly after `test_arming_one_point_leaves_the_others_inert`.
       - What it checks (criterion 16): it uses the `kill_points` fixture to call `arm(KillPoint.BEFORE_PUSH, after=1)` and then `arm(KillPoint.AFTER_PUSH)`. The first `reach(BEFORE_PUSH)` is a plain call that must return. The second must raise `InjectedKill` with `point is KillPoint.BEFORE_PUSH`. There is no `assert ... is None`, so the test passes `mypy --strict`.
       - Why: criterion 16 covers the failing side of the Interface rule "Arming one point leaves the others as they were" in the case where the other point is already armed. Criterion 7 covers only the inert case.
       - Diff: one new function in that one file, 11 lines. No other test changed.
       - Not red: the test passes against commit 0d091ba as it stands. That is expected, because the coder's entry 12 says no code change is needed.
       - I did not run `make types` myself. The test follows the same pattern as the existing typed tests.

       `make test`: test: green (100 % coverage)
       `make lint`: lint: green

    `make lint`: lint: green
    `make test`: test: green
14. coder: coder (round 1): the tester's new test for criterion 16 passes as expected, `make check` is green, and I changed no code. The implementation is still the one in commit 0d091ba.
       - Finding from entry 11 is closed: `tests/domain/test_kill_points.py::test_arming_one_point_leaves_an_armed_other_point_as_it_was` (added in entry 13) passes against `src/factory/domain/kill_points.py` as it is. That is because `KillPoints.arm` writes only `_passes_left[point]`, so arming `AFTER_PUSH` leaves the `BEFORE_PUSH` countdown alone.
       - I ran `make check` myself: lint, types, layers, sast, secrets, licenses and test are all green, with 100 % branch coverage. That includes `mypy --strict` over the new test, which neither the tester nor I had run before.
       - Design is unchanged: a "passes left" countdown for each armed point. I rejected storing an absolute target reach number (see entry 8).
       - Refactor: nothing new to refactor this round, because there is no new code, so there is no refactor commit.
       - Open: criterion 18 (docs) is the documenter's.

       `make check`: check: green

    `make check`: check: green
