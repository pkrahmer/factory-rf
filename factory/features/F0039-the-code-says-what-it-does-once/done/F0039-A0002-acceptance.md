---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 404
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-21T09:31:03.560200Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-21T09:37:41.746093Z'
  stage: acceptance
  run: adf18e34e3f44b2da7cf9ca8bca52141
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-21T09:39:02.423401Z'
  stage: done
stories: [F0039-S0001, F0039-S0002, F0039-S0003, F0039-S0004, F0039-S0005, F0039-S0006, F0039-S0007, F0039-S0008, F0039-S0009]
outcome: accepted
---

# Acceptance of The code says what it does, once

## Recommendation

**Accepted.** Every scope item of `feature.md` is built and archived. The two stories that the first acceptance (F0039-A0001) proposed are built too: S0008 adds the guard by body that the Goal promised, and S0009 puts `INSTANCE` in one module. With them, the Goal's "a guard that finds them by their body" holds for every shared helper the feature named. `make check` is green, and the feature smoke test is green: every guard fails on a copy planted under a new name. What is left is a noticed item of the feature's own kind, not a broken promise: twenty test modules still copy two `ENVIRONMENT` constants, which S0009 named and left out. It is proposed as S0010. Two one-line leftovers of S0006 (a comment on `agent_home`, a dated note in the decision log) stay for the human, as A0001 left them.

## 1 Scope

Each scope bullet has its story in `done/`. A0001 read S0001 to S0007 against the code; I checked those again through the smoke test (check 2). Both stories added since then lie inside the Goal and decision 5, and each was proposed by A0001:

- **S0008**: `tests/test_shared_bodies.py` finds a copy of `log_lines`, `pushed`, `pushed_state`, `remote_document` and `push_state` by its body under any name and parameters. The one copy it found (`_branch_document` of `tests/application/handlers/test_reject.py`) now calls `branch_reading.remote_document`. The two `ast` helpers it shares with `tests/test_shared_definition.py` live once, in `tests/function_support.py`.
- **S0009**: `INSTANCE = "factory-1"` is assigned in `tests/stage_run_support.py` only, and 52 modules import it from there. `tests/domain/test_lease.py` keeps `OWN = INSTANCE`. `tests/test_shared_constants.py` guards the value.

No story lies outside the scope, and the Goal is reached. A0001's scope gap, the guard by body, is closed.

One small part of decision 10 is still open: S0006 should have given `agent_home` "a comment of its own reason". `src/factory/application/boundaries.py:51` still reads `agent_home: AgentHome | None = None` without a comment. Its meaning (`None` when the agents run as no second user) is in `agent_home_of`'s docstring and in `docs/project-guide/watching.md:264`. A0001 left it for the human's own commit, and nobody has made that commit. It is a one-line comment with no testable side, so I again propose no story.

## 2 Feature smoke test

This is the walk-through of the feature's promise against the real modules, the six guards `tests/test_shared_*.py` and `make duplicates`. Step 4 copies `tests/` into a temporary folder and runs the guards there twice: once as the tree is, and once with a planted module. The planted module copies four shared things under new names: the definition reading, the body of `log_lines` under another name and parameter, the body of `pushed` under another name, and the value `"factory-1"` under the name `OWNER`.

Command: the script below, run with `TMPDIR_WALK="$d" bash "$d/walk.sh" 2>&1 | grep -v "Bytecode compiled"` in a `mktemp -d` folder that is removed on exit.

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
G="tests/test_shared_definition.py tests/test_shared_branch_helpers.py tests/test_shared_bodies.py tests/test_shared_constants.py tests/test_shared_fixtures.py tests/test_shared_test_helpers.py"
run_guards() { (cd "$1" && uv run --quiet --project "$repo" pytest -p no:randomly -p no:cacheprovider -o addopts="" -q --no-header --tb=line $G 2>&1 | grep -E "planted|passed|failed" | cut -c1-200); }
echo "== 4. the guards on a copy of the tree, then with copies under new names planted"
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
echo "== 5. the duplicates report holds no standing finding"
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
== 4. the guards on a copy of the tree, then with copies under new names planted
639 passed in 9.04s
      At index 0 diff: 'application/test_planted.py' != 'definition_support.py'
      At index 0 diff: 'application/test_planted.py' != 'log_support.py'
      At index 0 diff: 'application/test_planted.py' != 'stage_run_support.py'
      At index 0 diff: 'application/test_planted.py' != 'stage_run_support.py'
FAILED tests/test_shared_bodies.py::test_no_test_module_holds_a_copy[application/test_planted.py]
5 failed, 635 passed in 8.99s
== 5. the duplicates report holds no standing finding
duplicates: 0 new, 38 known, 0 gone
```

To name the failing tests, I ran the same planted copy again with `--tb=no -rf`:

```text
FAILED tests/test_shared_definition.py::test_each_shared_reading_is_written_in_one_module[definition]
FAILED tests/test_shared_bodies.py::test_each_shared_helper_is_written_in_one_module[log_lines]
FAILED tests/test_shared_bodies.py::test_each_shared_helper_is_written_in_one_module[pushed]
FAILED tests/test_shared_bodies.py::test_no_test_module_holds_a_copy[application/test_planted.py]
FAILED tests/test_shared_constants.py::test_the_instance_name_is_assigned_in_one_module
5 failed, 635 passed in 8.95s
```

Every step is green. All six guards pass on the real tree. Each planted copy is found under its new name, which the first acceptance showed was not possible for `log_lines` and `pushed`. The feature does what it promised.

`make check` as I found it ended with `test: green (68.7 s)`, coverage 99.14 % and `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

These are new since A0001, from the entries of S0008 and S0009, plus what remains of A0001's list:

- **The `ENVIRONMENT` copies** (S0009's Description, its coder entry 10 and its documenter entry 14). The value of `stage_run_support.ENVIRONMENT` is copied in ten more modules. A second value, `{"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}`, is copied in ten modules and has no shared home. `test_tick_project_agent.py` and `test_sealed_runs_runner.py` import `ENVIRONMENT` from other test modules. This is the feature's own kind of copy, so it is proposed as S0010. That story leaves out the `/opt/guard` pair (two copies, in `test_task.py` and `test_task_acceptance.py`).
- **The bodies guard skips a module by its file name alone** (S0008 reviewer entry 20, note 1; the night log carried it "for the morning"). `test_no_test_module_holds_a_copy` (`tests/test_shared_bodies.py:153`) checks `path.name in SHARED.values()`. A module named `log_support.py` in a subfolder would therefore escape the empty check. Comparing the path relative to `TESTS` would be exact. No such module exists. The change would touch a test S0008 wrote, and the standing leave does not cover that, so it is not proposed: it is for the human's leave, or for the next story that touches the guard.
- **Imports from one test module into another.** This is my own count, outside the scope. About forty-five lines under `tests/` import from another `test_*` module, for example `adapters.test_claude_runtime_os_user` (`_request`, `_write_sudo`, `REPLY`), `application.test_preflight_run` (`Rig`, `IMAGE`) and `application.test_known_results` (`_rig`). Some of these names are private. S0003 and S0009 each removed one such import, but the pattern is wide and the project's rules do not forbid it. Whether those helpers should move to support modules is a question for the human, not a story of this feature.
- **From A0001, still open:**
  - The `agent_home` comment (check 1).
  - `docs/decisions.md:499` ("without settings it is `None`") and `:272` ("`CostRecorder.begin`, `None` without settings"). Both describe a state that S0006 ended, and neither has a dated follow-up line as the entries for S0005 and S0006 have. Both lines are dated history, so they are left for the next story that touches costs.
  - A0001 recorded the mypy segfault and the detect-secrets false positive. Neither happened again in S0008 or S0009.

## 5 The documentation as a whole

I read the project guide's *Shared test helpers* again in full (`docs/project-guide/README.md:21-67`) after S0008's and S0009's edits. It agrees with the code:

- The new sentence on the guards (line 23) names `test_shared_bodies.py` and its five helpers.
- `function_support.py` is listed (line 43). S0008's documenter added that line beyond the criterion, as the section asks.
- The `stage_run_support.py` line (line 60) names `INSTANCE` and `test_shared_constants.py`.

Two small points. Neither misleads:

- Line 60 says `INSTANCE` is the instance name "that every test module imports from here". Only the modules that name the instance import it (about fifty-five). Read strictly, the sentence overstates.
- The same line does not name `ENVIRONMENT`, which `stage_run_support` already shares. S0010's docs criterion adds it there and in the `wiring_support.py` line.

`README.md`, `docs/operator-guide.md` and `docs/decisions.md` needed nothing from S0008 or S0009, and nothing in them contradicts the feature. A0001's documentation findings stand: the six removed statements are gone outside dated history, and the guide's missing mention of the guards is now written.

## 6 Decisions taken for the human

A0001's list, items 1 to 13, still stands: `CallEnd`, the process calls kept in the runtimes, the state directory, no structural test, one shared place per helper, the leaves of decisions 6, 7 and 11, the required `Boundaries` fields, the stop records file, the duplicates baseline, the intake answers of S0003 and S0005, the coders' defaults, and the reading of the standing leave for dead leftovers. Added since then:

14. **S0008's intake answers** (journal entry 4, from "the human's operator"):
    - A criterion for the tree scan.
    - The tree test skips the three defining modules, and `copies` keeps its signature.
    - The phrase "the guard's own module included" was dropped.
15. **S0009's intake answer (b)** (journal entry 4, the operator): the `--collect-only` comparison is a check on the work, not a criterion. The tester compared the ids (7062 before, 7071 after, the 9 new ones all from the new guard). The reviewer confirmed it from the diff, because the tester's lists in `$TMPDIR` were gone with its run. So the check was made, but the reviewer saw no record of it. A later story with the same check might ask the tester to paste the count lines into its entry.
16. **Who answered.** S0008 and S0009 were answered by the human's operator "within F0039's decisions (no new leave, no product decision)". I read both answers as within that bound: each only shaped a criterion. The human may still want to accept them as their own.
17. **S0008's defaults:**
    - The guard's helpers live in the test module.
    - The round-0 reviewer counted the second copy of `_functions` and `_without_docstring` as a finding, and the tester moved both to `tests/function_support.py`.
    - The documenter listed `function_support.py` in the guide without a criterion naming it.
18. **What S0009 left out:** the `ENVIRONMENT` constants, "left to a later story if the human wants it". S0010 is that story, for the human to start or drop.

Earlier tests changed since A0001, with the leave each was changed under, as the reviewers' entries name them:

- **S0008**, 2 modules, both under the standing leave to move a shared test helper:
  - `tests/application/handlers/test_reject.py`: `_branch_document` was removed and the module uses `remote_document`.
  - `tests/test_shared_definition.py`: `_functions` and `_without_docstring` moved to `function_support`.
- **S0009**, 52 modules, all under the standing leave (constant move). The reviewer lists each one in entry 12. They are 48 removals of `INSTANCE = "factory-1"`, three import changes (`test_recovery_cap.py`, `test_recovery_expiry.py`, `test_tick_project_agent.py`) and `OWN = INSTANCE` in `tests/domain/test_lease.py`.

No earlier test was changed without a named leave.

## 7 The slow checks

The project offers nothing beyond `make check` but `make duplicates`, which is a record (`0 new, 38 known, 0 gone`), and `make documents`, which is the docs stage's check. `make mutants` belongs to check 3. Today there is nothing else to run.

The JUnit report (`.reports/junit.xml`) holds 7071 tests, summing 777.1 s on all workers. A0001 counted 6464 tests and 720.9 s. Most of the growth is S0008's tree test:

- `test_no_test_module_holds_a_copy` has one row per module under `tests/`.
- S0008's and S0009's guards together add 607 tests and 14.6 s of summed time.
- `make test` took 68.7 s against 61.2 s at A0001. That is still small, but every new test module now adds one row.

The slowest tests are the ten-second time-limit tests, as designed, and none of them comes from this feature:

- `test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`, two rows at 11.5 s each.
- `test_process_session::test_process_the_kill_cannot_reach_does_not_hold_the_call[may-not-signal]`, 10.1 s.
- `test_process::test_child_is_killed_at_the_time_limit`, 10.1 s.
- `test_process_session::test_time_limit_of_a_make_target_ends_what_timeout_started[own-group]`, 10.1 s.

Disk: the Disk now line equals the record at the previous acceptance. `/work`, `/state` and `/tmp` each show 968.8 GB free and 0.0 GB used. There is no growth to explain.

## 8 Cost

The nine stories cost 83 runs, 88.5 min, 642 turns and $21.20 together:

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

S0003 and S0006 still stand out, for the reasons A0001 gave:

- **S0003**: three review rounds over the dead leftovers of its moves, and one mypy stall.
- **S0006**: the largest change, a question at doing, and a docs stall.

Of the two new stories:

- **S0008** took 11 runs: an intake question and one review round. The round was about a copied `ast` helper in its own new guard, so the feature's rule caught the feature's own story.
- **S0009** changed 52 modules in 7 runs for $1.64. That is the cheapest change per module in the feature, because it was purely mechanical and the reviewer found nothing.

Human interventions: 5 questions answered, all of the cause `question`, and the stories waited 3.7 h for them. A0001 counted 3 questions and the same 3.7 h, so the two new intake questions (S0008 and S0009) were answered by the operator with no wait that counts. The questions were:

- S0003 at intake: the guard's names.
- S0005 at intake: a criterion that contradicted the smoke test.
- S0006 at doing: two test rows outside decision 11's leave.
- S0008 at intake: a missing tree-scan criterion.
- S0009 at intake: a criterion no test could check.

S0006 needed the human most. Its question stopped a finished source change at doing, because decision 11's leave had missed two test rows. The four intake questions were defects in the drafts that intake caught before any work started. Two of them (S0008, S0009) were in drafts that the first acceptance wrote: one lacked the tree-wide criterion, the other had a criterion no test could check. S0010 states its tree-wide criterion (1) itself and keeps the `--collect-only` comparison in its Description.

## Proposed stories

- `backlog/F0039-S0010-the-tests-name-the-agent-environment-in-one-place-each.md`: the twenty copies of the two `ENVIRONMENT` values move to `stage_run_support.ENVIRONMENT` and a new `wiring_support.ENVIRONMENT`, the two imports from other test modules move with them, and a guard by value catches the next copy. This is the feature's own kind of copy, noticed by S0009 and left outside its scope.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed
   1. Scope: every scope item is built and archived. S0008, from the first acceptance (A0001), closed its gap: a guard by body now covers `log_lines`, `pushed`, `pushed_state`, `remote_document` and `push_state`. S0009 put `INSTANCE` in one module. The Goal is reached. Decision 10's comment on `agent_home` (`boundaries.py:51`) is still missing; it is a one-line change, so it is left to the human again.
   2. Feature smoke test: green. The runtimes share `read_call_end`, the docstrings and `prepare -> None` hold, `NOT_YET_HANDLED` is gone, the six fields are required, and `make duplicates` reports 0 new. All six guards are green on the tree. A planted module made five tests fail: its copies of the definition, of `log_lines`, of `pushed` and of `"factory-1"`, each under a new name, were all found. `make check` was green as found.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: twenty modules copy two `ENVIRONMENT` values, which S0009 left out, so I propose S0010. The bodies guard skips a defining module by file name only (S0008's reviewer); fixing that needs the human's leave. About forty-five imports go from one test module into another; that is the human's question. Two sentences in `docs/decisions.md` still say "`None` without settings" (`:272` and `:499`).
   5. Documentation: *Shared test helpers* agrees with the code and names the guards, `function_support.py` and `INSTANCE`. "Every test module imports" `INSTANCE` overstates slightly. `ENVIRONMENT` is not named yet; S0010's docs criterion adds it.
   6. Decisions: A0001's items 1 to 13 stand. New are the intake answers for S0008 and S0009, given by the human's operator, which the human may want to own. S0009's collect-only check was confirmed from the diff, not from a pasted record. S0008 changed 2 earlier tests and S0009 changed 52, all under the standing leave. Every change names its leave.
   7. Slow checks: nothing beyond `make check` except `make duplicates` (0 new) and `make documents`. There are now 7071 tests summing 777 s (A0001: 6464, 721 s); S0008's per-module guard rows account for most of the growth. The slowest tests are the ten-second time-limit tests, none of them from this feature. Disk is unchanged from the previous record.
   8. Cost: 83 runs, 88.5 min, $21.20. S0003 ($4.98) and S0006 ($4.97) stand out. S0008 cost $2.50 (an intake question and a review round on its own copied helper), and S0009 changed 52 modules for $1.64. The human answered 5 questions (cause `question`) and the stories waited 3.7 h in total. S0006 needed the human most: decision 11's leave missed two test rows. Two of the intake questions came from drafts the first acceptance wrote.
3. factory: done (pull request merged); cost: 1 runs, 6.6 min, 31 turns, 110306 tokens in (2183553 more from cache), 29182 out, $1.90
