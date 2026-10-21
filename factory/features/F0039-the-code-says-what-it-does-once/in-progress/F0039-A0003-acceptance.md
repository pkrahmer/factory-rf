---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 406
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-21T12:35:13.025531Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-21T12:39:59.419211Z'
  stage: acceptance
  run: 65a70462fc0c496189db266e95993fb9
stories: [F0039-S0001, F0039-S0002, F0039-S0003, F0039-S0004, F0039-S0005, F0039-S0006, F0039-S0007, F0039-S0008, F0039-S0009, F0039-S0010]
outcome: null
---

# Acceptance of The code says what it does, once

## Recommendation

**Accepted.** Every scope item of `feature.md` is built and archived. So are the stories the two earlier acceptances proposed: S0008 (the guard by body), S0009 (`INSTANCE` in one module) and now S0010 (the two `ENVIRONMENT` values in one module each, and the bodies guard's relative-path rule of decision 14). `make check` is green as I found it. The feature smoke test is green: every guard passes on the tree and fails on a copy planted under a new name, including a copy in a subfolder module named like a defining one. A0002's open one-line items (the `agent_home` comment and two stale sentences in the decision log) were closed by the human's commit `9227f5ee`. Nothing of weight is left, and I propose no story.

## 1 Scope

Each scope bullet has its story in `done/`. A0001 and A0002 read S0001 to S0009 against the code, and the smoke test (check 2) walks them again. The one story added since A0002 lies inside the Goal ("the test copies give way to one shared place each with a guard that finds them") and inside decision 14:

- **S0010**: `ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}` is assigned only in `tests/stage_run_support.py:21`. The second value, `{"PATH": "/opt/scripts:/usr/bin:/bin", ...}`, is assigned only in `tests/wiring_support.py:9`. Twenty modules import them, and so do the two modules that imported from other test modules (`test_tick_project_agent.py`, `test_sealed_runs_runner.py`). `tests/test_shared_environments.py` guards both values by their literal under any name. `tests/test_shared_bodies.py:153` now decides a defining module by `path.relative_to(TESTS).as_posix()`. Nothing under `src/` changed.

No story lies outside the scope, and the Goal is reached. Decision 10's `agent_home` comment, which A0001 and A0002 left open, is now at `src/factory/application/boundaries.py:51` ("`None` when the agents run as no second user"), from the human's commit `9227f5ee`. The human's second change in `feature.md` (the `replace` example in `CLAUDE.md`, *Tests*) is in place too.

## 2 Feature smoke test

This is the walk-through of the feature's promise against the real modules, the seven guards `tests/test_shared_*.py` and `make duplicates`. It is A0002's script with three additions:

- Step 4 greps the tree for both environment values and for imports of `ENVIRONMENT` from a `test_` module.
- Step 5's planted module also carries both environment values, under the new names `RUNNER_ENV` (annotated, keys in reverse order) and `HANDLER_ENV`.
- Step 6 plants `tests/entry/log_support.py`: a copy of `log_lines` named `_lines`, in a subfolder module with the same file name as a defining module. Before decision 14, the empty-check exempted that module by its file name.

Command: the script below, run with `TMPDIR_WALK="$d" bash "$d/walk.sh" 2>&1 | grep -v "Bytecode compiled"`, where `d=$(mktemp -d)` with `trap 'rm -rf "$d"' EXIT`.

```bash
#!/usr/bin/env bash
set -u
repo=/work/checkout; cd "$repo"
echo "== 1. one reading of a call's end, used by both runtimes"
uv run --quiet python - <<'PY'
import ast, inspect
from datetime import timedelta
from pathlib import Path
import factory.adapters.claude_runtime as c, factory.adapters.opencode_runtime as o
from factory.adapters.agent_launch import CallEnd, LoginFiles, Starters, read_call_end, state_directory_error
from factory.domain.errors import AgentRuntimeError
for m in (c, o):
    calls = {n.func.id for n in ast.walk(ast.parse(inspect.getsource(m))) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    print(m.__name__.rsplit(".")[-1], "read_call_end" in calls, "state_directory_error" in calls, "killed_at_limit" in calls, "call_refusal" in calls)
s = Starters(sudo_executable="/usr/bin/sudo", confine_executable="/opt/factory/bin/factory-confine", login_files=LoginFiles())
lim = timedelta(seconds=30)
try:
    read_call_end(CallEnd(stderr="sudo: a password is required\n", printed=False, exit_status=1, duration=timedelta(seconds=1), timed_out=False), time_limit=lim, os_user="agent", starters=s)
except AgentRuntimeError as e:
    print("refused:", e.detail)
print("killed at limit:", read_call_end(CallEnd(stderr="", printed=True, exit_status=137, duration=lim, timed_out=False), time_limit=lim, os_user="agent", starters=s))
print(state_directory_error(Path("/state/runs"), PermissionError(13, "Permission denied")).detail)
PY
echo "== 2. the docstrings and the return type say what the code does"
uv run --quiet python - <<'PY'
from typing import get_type_hints
from factory.application.tick import Tick
from factory.application.scheduler import CheckoutPreparer
print("nothing local is read" in (Tick.__doc__ or ""), "publish the stop records" in (Tick.run.__doc__ or ""))
print(get_type_hints(CheckoutPreparer.prepare)["return"])
PY
echo "== 3. no list of unhandled kinds; the six collaborators are required"
uv run --quiet python - <<'PY'
import dataclasses
import factory.entry.wiring as w
from factory.application.boundaries import Boundaries
print(hasattr(w, "NOT_YET_HANDLED"), "NOT_YET_HANDLED" in w.__all__)
fields = {f.name: f for f in dataclasses.fields(Boundaries)}
print([n for n, f in fields.items() if f.default is not dataclasses.MISSING])
try:
    Boundaries(**{n: object() for n in fields if n not in ("disk", "agent_home")})
except TypeError as e:
    print("TypeError:", e)
PY
echo "== 4. each shared value assigned once; no ENVIRONMENT imported from a test_ module"
for v in '"/usr/local/bin:/usr/bin"' '"/opt/scripts:/usr/bin:/bin"'; do grep -rlF --include='*.py' "{\"PATH\": $v, \"HOME\": \"/home/factory\"}" tests | sort; done
grep -rnE '^from (application|entry|adapters|domain)?\.?test_[a-z_]+ import .*\bENVIRONMENT\b' tests | wc -l
G="tests/test_shared_definition.py tests/test_shared_branch_helpers.py tests/test_shared_bodies.py tests/test_shared_constants.py tests/test_shared_environments.py tests/test_shared_fixtures.py tests/test_shared_test_helpers.py"
run_guards() { (cd "$1" && uv run --quiet --project "$repo" pytest -p no:randomly -p no:cacheprovider -o addopts="" -q --no-header --tb=no -rf $G 2>&1 | grep -E "^FAILED|passed|failed" | cut -c1-200); }
echo "== 5. the guards on a copy of the tree, then with copies under new names planted"
copy="$TMPDIR_WALK/copy"; mkdir -p "$copy"; cp -r tests pyproject.toml "$copy/"
run_guards "$copy"
cat > "$copy/tests/application/test_planted.py" <<'PYP'
"""A module that copies the shared helpers under other names."""

from pathlib import Path

from factory.application.boundaries import Boundaries
from factory.domain.work_item import WorkItemDocument
from git_support import PIPELINE_YAML
from stage_run_support import PATH, branch_head

OWNER = "factory-1"
RUNNER_ENV: dict[str, str] = {"HOME": "/home/factory", "PATH": "/usr/local/bin:/usr/bin"}
HANDLER_ENV = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}


def _read_the_definition(boundaries):
    return boundaries.pipeline_reader.parse(PIPELINE_YAML)


def _factory_log(state_root: Path) -> list[str]:
    """Another name, another parameter, the same body."""
    log = tmp_path / "state" / "factory.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _head_item(boundaries: Boundaries, remote: Path) -> WorkItemDocument:
    text = boundaries.git.show_file(branch_head(remote), PATH)
    assert text is not None
    return boundaries.work_item_reader.parse(text)
PYP
run_guards "$copy"
echo "== 6. a module named like a defining one, in a subfolder, is checked for copies too"
rm "$copy/tests/application/test_planted.py"
mkdir -p "$copy/tests/entry"; sed -n '/^def log_lines/,$p' "$copy/tests/log_support.py" | sed 's/^def log_lines/def _lines/' > "$copy/tests/entry/log_support.py"
head -3 "$copy/tests/entry/log_support.py"
run_guards "$copy"
echo "== 7. the duplicates report holds no standing finding"
make duplicates 2>&1 | tail -1
```

Output:

```text
== 1. one reading of a call's end, used by both runtimes
claude_runtime True True False False
opencode_runtime True True False False
refused: /usr/bin/sudo refused the agent run: sudo: a password is required
killed at limit: True
cannot write the state directory /state/runs: [Errno 13] Permission denied
== 2. the docstrings and the return type say what the code does
False True
<class 'NoneType'>
== 3. no list of unhandled kinds; the six collaborators are required
False False
['agent_home']
TypeError: Boundaries.__init__() missing 1 required keyword-only argument: 'disk'
== 4. each shared value assigned once; no ENVIRONMENT imported from a test_ module
tests/stage_run_support.py
tests/test_shared_environments.py
tests/test_shared_environments.py
tests/wiring_support.py
0
== 5. the guards on a copy of the tree, then with copies under new names planted
652 passed in 8.97s
FAILED tests/test_shared_definition.py::test_each_shared_reading_is_written_in_one_module[definition]
FAILED tests/test_shared_bodies.py::test_each_shared_helper_is_written_in_one_module[log_lines]
FAILED tests/test_shared_bodies.py::test_each_shared_helper_is_written_in_one_module[pushed]
FAILED tests/test_shared_bodies.py::test_no_test_module_holds_a_copy[application/test_planted.py]
FAILED tests/test_shared_constants.py::test_the_instance_name_is_assigned_in_one_module
FAILED tests/test_shared_environments.py::test_each_shared_environment_is_assigned_in_one_module[stage_run_support.py]
FAILED tests/test_shared_environments.py::test_each_shared_environment_is_assigned_in_one_module[wiring_support.py]
7 failed, 646 passed in 8.87s
== 6. a module named like a defining one, in a subfolder, is checked for copies too
def _lines(tmp_path: Path) -> list[str]:
    """Return the lines of the factory log under `tmp_path`, none when it does not exist."""
    log = tmp_path / "state" / "factory.log"
FAILED tests/test_shared_bodies.py::test_each_shared_helper_is_written_in_one_module[log_lines]
FAILED tests/test_shared_bodies.py::test_no_test_module_holds_a_copy[entry/log_support.py]
2 failed, 651 passed in 8.72s
== 7. the duplicates report holds no standing finding
duplicates: 0 new, 38 known, 0 gone
```

Every step is green:

- Steps 1 to 3 and 7 give the same results as at A0002.
- In step 4, `tests/test_shared_environments.py` is listed twice because the guard's own case strings and its fixture write both values. The guard's `ast` reading counts neither, which is why its row 1 passes on the tree. The import count is 0.
- In step 5, both planted environments are found under their new names, one of them annotated and with its keys reordered. The four older guards fail as they did at A0002.
- In step 6, `test_no_test_module_holds_a_copy[entry/log_support.py]` fails. Under the old file-name rule, that row would have passed: it asserted only that the module holds a copy.

`make check` as I found it ended with `test: green (63.8 s)`, coverage 99.14 % and `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

These are new since A0002, from S0010's entries, plus what is left of A0002's list:

- **The tester's three choices inside the Interface** (S0010, entry 5; the coder's entry 7 carried them, and the reviewer's entry 9 accepted them):
  - A dict that holds a name counts as no copy (`_literal` catches `ValueError`).
  - The guard's own cases read against a fixture, not a top-level constant.
  - The docstring is shortened for E501.

  All three are sound. One detail of the first: `_literal` catches only `ValueError`. A top-level dict literal that `ast.literal_eval` refuses with another error, such as a `TypeError` for an unhashable key, would crash the guard loudly rather than pass it silently. No such dict exists under `tests/`. No story.
- **The `/opt/guard` pair** (S0010's Description): `{"PATH": "/opt/guard", "HOME": "/home/factory"}` is still copied in `tests/application/test_task.py:26` and `tests/application/test_task_acceptance.py:26`. A third module, `test_task_os_user.py:17`, has a variant with `/home/agent`. S0010 left it to the human: two copies, and no shared module of the task tests to put it in. I agree, and propose no story. It can join the human's v1.2 item on imports between test modules.
- **Imports between test modules** (A0002, note 4): the human recorded this in `planning/v1.2-candidates.md` (2026-10-21) as a story of its own. It is no longer this feature's to carry.
- **From A0002, closed:** the `agent_home` comment and the stale sentences at `docs/decisions.md` `:272` and `:499` were fixed by the human's commit `9227f5ee`. The bodies guard's file-name rule was changed by S0010 (decision 14).
- **From A0002, still open:** the overstatement in the project guide (check 5).
- The night log in `docs/runs/` is the human's, as S0010's documenter noted. No stall, mypy fault or flaky test was recorded in S0010.

## 5 The documentation as a whole

I read *Shared test helpers* (`docs/project-guide/README.md:21-67`) again in full after S0010's documenter. The section agrees with the code:

- The `stage_run_support.py` line (60) names `ENVIRONMENT`.
- The `wiring_support.py` line (66) names `ENVIRONMENT` and says that `tests/test_shared_environments.py` fails on another top-level assignment of either value.
- The documenter narrowed line 60's guard clause to "another top-level assignment of the instance name", so it no longer reads as covering `ENVIRONMENT`.

Two small points. Neither misleads a user:

- Line 60 still says `INSTANCE` is the name "that every test module imports from here". Only the modules that name the instance import it. A0002 noted this too. It is one phrase, which the next documenter who touches the line, or the human's own commit, can narrow to "that every test naming the instance imports".
- The section's opening sentence names the five helpers that `test_shared_bodies.py` finds by body. It does not say that `test_shared_constants.py` and `test_shared_environments.py` find copies by value. The two module lines do say it, so nothing is missing, only gathered in another place.

`README.md`, `docs/operator-guide.md` and `docs/decisions.md` needed nothing from S0010 (its docs criterion said none), and nothing in them contradicts the feature. The human's commit `9227f5ee` removed the last two sentences in the decision log that described the optional settings.

## 6 Decisions taken for the human

A0002's list, items 1 to 18, still stands. It covers:

- `CallEnd`, the process calls kept in the runtimes, the state directory and no structural test.
- One shared place per helper.
- The leaves of decisions 6, 7 and 11, and the required `Boundaries` fields.
- The stop records file and the duplicates baseline.
- The intake answers of S0003, S0005, S0008 and S0009, the operator's answers, and the coders' defaults.

Added since then:

19. **Decision 14, the human's leave for S0010** (2026-10-21): `test_no_test_module_holds_a_copy` decides a defining module by its relative path. It was granted before S0010 started, so S0010 asked no question.
20. **The `/opt/guard` pair and the other `ENVIRONMENT` variants stay as they are** (S0010's Description, drafted by A0002 and started by the human as written). The human may want them in the v1.2 item on test-module imports.
21. **S0010's tester defaults**, accepted by the reviewer: the `ValueError` fallback of `_literal`, the fixture for the guard's own cases, and the docstring shortened from the Interface's wording for E501.
22. **The collect-only check**: this time the tester pasted the counts into the entry (871 ids before, 872 after; the one new id is the bodies guard's row for the new module). The reviewer confirmed it from the diff, because the lists were gone with the run. A0002's suggestion was followed.

Earlier tests changed by S0010, with the leave each was changed under, as the reviewer's entry 9 names them:

- **23 modules under the standing leave** to move a shared test helper (a constant):
  - Ten modules now import `ENVIRONMENT` from `stage_run_support`.
  - Ten modules now import it from `wiring_support`.
  - `tests/wiring_support.py` gains the constant.
  - The two cross-imports were redirected (`test_tick_project_agent.py`, `test_sealed_runs_runner.py`).
- **`tests/test_shared_bodies.py::test_no_test_module_holds_a_copy`**, under the human's leave of decision 14. Its name and ids are kept.

No earlier test was changed without a named leave.

## 7 The slow checks

Beyond `make check`, the project offers only:

- `make duplicates`, a record: `0 new, 38 known, 0 gone`.
- `make documents`, the docs stage's check.

`make mutants` belongs to check 3. Today there is nothing else to run.

The JUnit report (`.reports/junit.xml`) of my `make check` holds 7084 tests, summing 746.6 s on all workers. A0002 counted 7071 tests and 777.1 s.

- S0010 added 13 tests: 12 of `test_shared_environments.py`, summing 0.7 s, and one row of the bodies guard.
- The seven guards together are 652 tests and 17.4 s.
- `make test` took 63.8 s, against 68.7 s at A0002. The difference is noise between runs.

The slowest tests are still the ten-second time-limit tests, as designed, none of them from this feature:

- `test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`, two rows at 11.5 s each.
- Three rows of `test_process_session` at 10.1 s each: `test_time_limit_ends_every_process_of_the_session[run_process-own-group]`, and `test_process_the_kill_cannot_reach_does_not_hold_the_call` with `[ended-in-between]` and `[may-not-signal]`.

Disk, now against the previous record (`disk start`):

- `/work` used 0.5 GB at both; that is the checkout's `.venv` (511 MB).
- `/state` and `/tmp` used 0.0 GB at both.
- Free space fell by 0.5 GB on all three, equally (968.6 to 968.1 GB). They share one host disk, and the used figures did not move, so the drop comes from outside this checkout.

The feature's changes, all to tests and documents, explain no growth, and none was found.

## 8 Cost

The ten stories cost 89 runs, 97.5 min, 691 turns and $23.23 together:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 6 | 5.5 | $1.47 |
| S0002 | 10 | 9.6 | $2.36 |
| S0003 | 16 | 20.6 | $4.98 |
| S0004 | 6 | 4.6 | $1.09 |
| S0005 | 7 | 5.0 | $1.38 |
| S0006 | 14 | 21.3 | $4.97 |
| S0007 | 6 | 3.8 | $0.82 |
| S0008 | 11 | 11.0 | $2.50 |
| S0009 | 7 | 7.2 | $1.64 |
| S0010 | 6 | 8.9 | $2.03 |

S0003 and S0006 still stand out, for the reasons A0001 gave:

- **S0003**: three review rounds over the dead leftovers of its moves, and a mypy stall.
- **S0006**: the largest change, a question at doing, and a docs stall.

**S0010** ran each stage once, with no question, no round and no finding: 6 runs for 23 changed modules and a new guard. It cost more than S0009 ($2.03 against $1.64 for 52 modules) because its tester wrote a guard with ten cases and ran the collect-only comparison, not only a mechanical move.

Human interventions: 5 questions answered, all of the cause `question`, and the stories waited 3.7 h for them. These are the same figures as at A0002, so S0010 added none: its one leave (decision 14) was granted in `feature.md` before it started. The questions were:

- S0003 at intake.
- S0005 at intake.
- S0006 at doing.
- S0008 at intake.
- S0009 at intake.

S0006 needed the human most: decision 11's leave missed two test rows, and that stopped a finished source change at doing.

## Proposed stories

None. The two remaining notes are not worth a story each, and both are left to the human's own commits or plans:

- The `/opt/guard` pair: two copies, with no shared module to hold them, and the human's v1.2 item on test-module imports is the better place for it.
- The one overstated phrase in the project guide.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed
   1. Scope: every scope item is built and archived. S0010 moved the two `ENVIRONMENT` values to `stage_run_support` and `wiring_support`, added the guard `tests/test_shared_environments.py`, and gave the bodies guard its relative-path rule (decision 14), so the Goal is reached. The `agent_home` comment that A0001 and A0002 left open is in place, from the human's commit `9227f5ee`.
   2. Feature smoke test: green. The runtimes share `read_call_end`, `prepare -> None` holds, `NOT_YET_HANDLED` is gone, the six fields are required, and `make duplicates` reports 0 new. Each value is assigned once, and no `ENVIRONMENT` is imported from a `test_` module. All seven guards pass on the tree. The planted copies made 7 tests fail, both environments among them, found under new names. A copy in `tests/entry/log_support.py` is now found too. `make check` was green as found.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: the tester's three choices inside the Interface are sound. `_literal` catches only `ValueError`, so an odd literal would crash the guard loudly rather than slip past it; no story. The `/opt/guard` pair is left to the human. The imports between test modules are now in the human's v1.2 candidates. A0002's `decisions.md` sentences were fixed by `9227f5ee`.
   5. Documentation: *Shared test helpers* agrees with the code and names both `ENVIRONMENT` values and the new guard. The phrase "every test module imports" `INSTANCE` still overstates slightly; it is a one-phrase fix for the human or the next documenter.
   6. Decisions: A0002's items 1 to 18 stand. New are decision 14 (granted before start), the `/opt/guard` pair left as it is, S0010's tester defaults, and the collect-only counts, which this time were pasted (871/872). S0010 changed 23 earlier modules under the standing leave and `test_no_test_module_holds_a_copy` under decision 14; every change names its leave.
   7. Slow checks: nothing beyond `make check` except `make duplicates` (0 new) and `make documents`. There are 7084 tests summing 746.6 s; S0010 added 13 of them, 0.7 s. The slowest are the ten-second time-limit tests, none from this feature. Disk used is unchanged (`/work` 0.5 GB, the `.venv`). Free space fell 0.5 GB equally on the three mounts of one host disk, which this feature does not explain.
   8. Cost: 89 runs, 97.5 min, $23.23. S0003 ($4.98) and S0006 ($4.97) stand out. S0010 cost $2.03 in 6 runs, with no round and no question. The human answered 5 questions (cause `question`) and the stories waited 3.7 h, unchanged since A0002. S0006 needed the human most.
