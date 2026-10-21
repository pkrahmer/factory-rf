---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 386
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-21T06:19:33.784240Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-21T06:28:41.525443Z'
  stage: acceptance
  run: a5339d42003d43038e3da25295db549d
stories: [F0039-S0001, F0039-S0002, F0039-S0003, F0039-S0004, F0039-S0005, F0039-S0006, F0039-S0007]
outcome: null
---

# Acceptance of The code says what it does, once

## Recommendation

**Accepted with stories.** Every scope item of `feature.md` was built and archived, `make check` is green, and the feature's smoke test met every promise of the runtimes, the docstrings, the wiring, the boundaries and the duplicates report. One promise of the Goal is kept only in part: "a guard that finds them by their body" holds for the definition only. The log reading and the four branch helpers are found by name, so a copy with the same body under another name passes. One such copy, `_branch_document` in `tests/application/handlers/test_reject.py`, is still in the tests. S0002's and S0003's own Interfaces, which the human wrote, set the narrower rule and were met, so I count this as a story's worth (S0008) and not a broken promise; the human may weigh it otherwise.

## 1 Scope

Each scope bullet has its story in `done/`, and I read the code each one names:

- S0001: `read_call_end`, `CallEnd` and `state_directory_error` are in `src/factory/adapters/agent_launch.py:448`. Both runtimes call them (`claude_runtime.py:501`, `opencode_runtime.py:686`) and neither calls `killed_at_limit` or `call_refusal` any more.
- S0002 and S0003: the shared modules exist (`tests/definition_support.py`, `tests/branch_reading.py`, `pushed` in `tests/stage_run_support.py`, `disk_settings` and `disk_records` in `tests/conftest.py`), with their guards `tests/test_shared_definition.py` and `tests/test_shared_branch_helpers.py`.
- S0004: the `Tick` docstrings no longer say "nothing local is read", and `Tick.run`'s docstring names the publication. `CheckoutPreparer.prepare` is `-> None` (`scheduler.py:84`).
- S0005: `NOT_YET_HANDLED` is gone from `src/` and from `__all__`.
- S0006: the six `Boundaries` fields are required (`boundaries.py:45-50`), and no `is None` branch on them is left in `factory.application`.
- S0007: the decision log and the project guide record the baseline; `make duplicates` gives `0 new, 38 known, 0 gone`.

No story lies outside the scope.

Two gaps:

- **The Goal's guard "by its body".** The Goal says the copies "give way to one shared place each with a guard that finds them by their body". Decision 5 says "by its body or its parameters, not by its name, so the next copy under a new name is found too". As built, only the definition guard matches by body (`tests/test_shared_definition.py::_copies_the_definition`). The log rule matches the names `log_lines`/`_log_lines` (`_copies_the_log_reading`). The branch helpers' guard matches the name without one `_` plus the annotations (`tests/test_shared_branch_helpers.py::_copied`). Check 2 shows the effect. A search by body found one copy that S0003's by-name search missed: `tests/application/handlers/test_reject.py:106` `_branch_document` has the body of `branch_reading.remote_document` and reads the same `BRANCH`/`PATH` values. Proposed as S0008.
- **Decision 10's comment on `agent_home`.** Decision 10 planned that S0006 "keeps `agent_home` optional with a comment of its own reason". S0006's Interface only removed the old comment, so `agent_home: AgentHome | None = None` (`src/factory/application/boundaries.py:51`) now has no comment. Its meaning (`None` when the agents run as no second user) is only in `agent_home_of`'s docstring (`src/factory/entry/wiring.py:316`). S0006's reviewer and documenter both left this to the human. It is a one-line comment, so no story is proposed: a change for the human's own commit, or a line in the next story that touches `boundaries.py`.

## 2 Feature smoke test

The walk-through of the feature's promise, run against the real modules, the test guards and `make duplicates`. Step 4 copies `tests/` into a temporary folder, plants a module that copies the shared helpers under other names, and runs the two guards there.

Command (the script, run with `TMPDIR_WALK="$d" bash "$d/walk.sh"` in a `mktemp -d` folder removed on exit; `Bytecode compiled` lines filtered):

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
from factory.application.scheduler import CheckoutPreparer, RepositoryWaiter
print("nothing local is read" in (Tick.__doc__ or ""), "publish the stop records" in (Tick.run.__doc__ or ""))
print(get_type_hints(CheckoutPreparer.prepare)["return"], get_type_hints(RepositoryWaiter.prepare)["return"])
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
echo "== 4. the guards find the next copy under a new name"
copy="$TMPDIR_WALK/copy"; mkdir -p "$copy"; cp -r tests pyproject.toml "$copy/"
uv run --quiet pytest -p no:randomly -o addopts="-p no:cacheprovider" -q --no-header "$copy/tests/test_shared_definition.py" "$copy/tests/test_shared_branch_helpers.py" 2>&1 | tail -1
cat > "$copy/tests/application/test_planted.py" <<'PYP'
"""A module that copies the shared helpers under other names."""

from pathlib import Path

from factory.application.boundaries import Boundaries
from factory.domain.work_item import WorkItemDocument
from git_support import PIPELINE_YAML


def _read_the_definition(boundaries):
    return boundaries.pipeline_reader.parse(PIPELINE_YAML)


def _the_log(tmp_path):
    return []


def _pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:
    raise NotImplementedError
PYP
uv run --quiet pytest -p no:randomly -o addopts="-p no:cacheprovider" -q --no-header --tb=line "$copy/tests/test_shared_definition.py" "$copy/tests/test_shared_branch_helpers.py" 2>&1 | grep -E "test_planted|passed|failed" | sed "s#$copy/##" | cut -c1-220
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
<class 'NoneType'> <class 'bool'>
== 3. no list of unhandled kinds; the six collaborators are required
False False
['agent_home']
TypeError: Boundaries.__init__() missing 1 required keyword-only argument: 'disk'
== 4. the guards find the next copy under a new name
25 passed in 2.24s
      At index 0 diff: 'application/test_planted.py' != 'definition_support.py'
      At index 0 diff: 'application/test_planted.py' != 'stage_run_support.py'
2 failed, 23 passed in 2.22s
== 5. the duplicates report holds no standing finding
duplicates: 0 new, 38 known, 0 gone
```

Steps 1, 2, 3 and 5 are green. In step 4 the guards are green on the real tree and fail on the planted definition copy (new name, same body) and on the planted `_pushed` (same name, same annotations). The planted `_the_log` (another name) is not found, which is what the log rule's Interface asks.

To check the Goal's "by their body", a second planted module held the real bodies of `log_lines` and `pushed` under the names `_factory_log(tmp_path: Path)` and `_branch_document(boundaries: Boundaries, remote: Path)`. Both guards stayed green:

```text
$ uv run --quiet pytest -o addopts="-p no:cacheprovider" -q --no-header --tb=line "$d/copy/tests/test_shared_definition.py" "$d/copy/tests/test_shared_branch_helpers.py"
.........................                                                [100%]
25 passed in 2.21s
```

Then a search by body (the shared helpers' bodies, docstrings aside, compared by `ast.unparse` with every top-level function under `tests/`) printed:

```text
log_lines ['log_support.py::log_lines']
pushed ['stage_run_support.py::pushed']
pushed_state ['stage_run_support.py::pushed_state']
remote_document ['application/handlers/test_reject.py::_branch_document', 'branch_reading.py::remote_document']
error_posts ['branch_reading.py::error_posts']
push_state ['branch_reading.py::push_state']
pipeline_definition ['definition_support.py::pipeline_definition']
```

The feature smoke test is green in everything the stories built. The one gap is the guard by body (check 1, S0008).

`make check` as I found it: `test: green (61.2 s)`, coverage 99.14 %, `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Gathered from the coder, reviewer and documenter entries of the seven stories:

- **`agent_home` has no comment of its own** (S0006 reviewer entry 24, documenter entries 26 and 29). Decision 10 planned one; see check 1. For the human.
- **Copied test constants** (S0005 reviewer entry 12): the new `tests/entry/test_wiring_constants.py` copies `INSTANCE` and `ENVIRONMENT`, as other modules do. Counted on 2026-10-21:
  - `INSTANCE = "factory-1"` in 49 modules (48 beside `tests/stage_run_support.py`).
  - `OWN = "factory-1"` in `tests/domain/test_lease.py`.
  - `tests/application/test_tick_project_agent.py` imports `INSTANCE` from another test module (`application.test_tick_agent_definition`).
  - Two `ENVIRONMENT` values in eleven and ten modules.

  This is the feature's own kind of finding, outside its scope. The `INSTANCE` part is proposed as S0009; the `ENVIRONMENT` copies are named there and left out.
- **A mypy segfault** (S0003 coder entry 29): `make types` ended with `Error 139` once in the factory's fresh-venv check (journal entry 27, a stall). It did not happen again on a warm or a cold cache. Seen once in this feature; no story. Worth watching in the night logs.
- **A detect-secrets false positive on prose** (S0006 entry 27, a docs stall). An edit of `docs/project-guide/costs.md:18` ("…; either status may carry it") was flagged as a "Secret Keyword". The documenter reworded the line rather than add a baseline entry. The detector can flag plain English, so a documenter can stall on wording. No story; for the human's notes.
- **The old `instance` is `None` sentence** (S0006 documenter entries 26 and 29): `docs/decisions.md:493` still says "without settings it is `None`" for the cost record's `instance`. It is the log's account of 2026-10-18, and the settings are now always there. Unlike the entries of S0005 (`docs/decisions.md:202`) and S0006 (`:262`), it has no dated follow-up line. Small; it could join the docs criterion of a later story that touches costs.
- **A local `pushed` hides the shared helper** (S0003 reviewer entry 31): `tests/application/test_stalls.py:252`. Harmless; no story.
- **Similar guard walks** (S0002 reviewer entries 9 and 17): the walk over `tests/` in `test_shared_definition.py` is similar to `_defining` in `test_shared_fixtures.py`. There are now five guard modules: `test_shared_fixtures.py` (by signature text), `test_shared_test_helpers.py` (by regex), `test_shared_definition.py` (by body and by name), `test_shared_branch_helpers.py` (by name and annotations), and S0008's proposal by body. Folding them into one is not proposed: each is small, and the merge would change tests of four stories.
- **Another time-limit reading** (my own finding, outside the scope): `src/factory/adapters/agent_home.py:80` (F0040) reads `result.timed_out or killed_at_limit(...)`, the first half of `read_call_end` without the refusals. `make_commands.py:132` reads `killed_at_limit` alone. Neither reads a refusal the way the runtimes do, so `read_call_end` does not fit them, and the shared part is already `killed_at_limit`. No story.

## 5 The documentation as a whole

I read `README.md`, the project guide's index (*Shared test helpers* in full) and the sections the stories changed: `agents.md` *The shared launch module* and *The opencode runtime*, `watching.md` *Boundaries* and the preparer paragraph (`:274`), `processes-and-checks.md` *The baseline*, and the decision log's entries at `:200-202`, `:262` and `:674-675`.

They agree with the code:

- `CheckoutPreparer.prepare()` "returns nothing".
- The six fields are documented as required, with `agent_home` "an `AgentHome | None`, last, default `None`".
- `read_call_end` and `CallEnd` are described in `agents.md:37`.
- `NOT_YET_HANDLED` is left only in the dated history of the decision log, with its removal dated beneath it.

A grep for the removed statements finds none outside the decision log's history and the human's `docs/runs/`. Those statements are "always `True`", "nothing local is read", "Last and optional", "without a waiter", "`None` without settings" and "5 new".

One gap: *Shared test helpers* tells an agent to look there before writing a helper, but it does not say that the guards `tests/test_shared_*.py` exist or what each finds. An agent learns of them only when one fails. S0008's docs criterion adds that sentence. `README.md` and `docs/operator-guide.md` needed nothing from this feature, and nothing in them contradicts it.

## 6 Decisions taken for the human

From `feature.md` and the journals, for the human to accept or revisit:

1. `read_call_end` takes a frozen `CallEnd`, not eight parameters (decision 1, answer (a)).
2. The runtimes' process calls stay in each runtime; `agent_launch` imports no process module (decision 2).
3. The state directory's difference between the runtimes stays, documented as deliberate (decision 3).
4. No structural test of the runtimes' source (decision 4).
5. One shared place per helper, guard by body or parameters, `_error_posts` without a guard (decision 5). As built, the log and branch guards match by name; see check 1.
6. The leaves for S0004 (decision 6), S0005 (decision 7) and S0006 (decision 11, plus the human's answer of 2026-10-21 for two more rows).
7. The six `Boundaries` fields are required, `agent_home` stays optional (decisions 8 and 10).
8. The stop records file on `main` stays as it is (decision 9).
9. The five standing duplicates findings: one merged, four accepted in the baseline (decision 12).
10. S0003: the guard's function names are the tester's choice (the human's answer, journal 4).
11. S0005: the new test `tests/entry/test_wiring_constants.py` is the one module under `tests/` that names `NOT_YET_HANDLED` (the human's answer (a), journal 4).
12. Defaults taken in the stages:
    - S0001's coder always copies `timed_out` from `read_call_end` instead of keeping an `if`, and keeps `ClaudeCodeRuntime._state_error` as a one-line wrapper.
    - S0004's coder drops `return True` rather than writing `return None`.
    - S0006's coder inlined `TaskComposer._os_user` at its one caller.
13. The reading of the standing leave. The reviewers of S0003 (entries 12 and 20) and S0006 (entry 16) read "move a shared helper" to cover removing what the move left dead in the same module: `_records_path`, `BODY`, `PATH`, `LOG`, and, under decision 11, `CountingGit` and the `| None` of `_raised`. S0003's round-1 reviewer first wrote that the dead `PATH` "goes beyond the leave", then asked for its removal "under the standing leave". The human may want to say once whether the standing leave covers such leftovers.

Earlier tests changed, with the leave each was changed under, as the reviewers' entries name them:

- **S0002**, 21 modules, all under the standing leave: `conftest.py` and the twenty modules of its Interface.
- **S0003**, 18 modules, all under the standing leave: the sixteen of its Interface, `conftest.py`, and `tests/application/test_nested_repositories.py`, which imported `_pushed` from another test module.
- **S0004**, 3 modules under decision 6: `test_nested_repositories.py`, `test_checkout_preparer_seal.py` and `test_scheduler.py`.
- **S0005**, 5 modules under decision 7: `test_wiring_acceptance.py`, `test_wiring_handlers.py`, `test_wiring_human_handlers.py`, `test_wiring_recovery.py` and `test_wiring_recovery_expired.py`.
- **S0006**, 18 modules under decision 11: `conftest.py`, `proof_support.py`, and the sixteen test modules S0006's reviewer lists in entry 24. `test_cost_instance.py` and `test_stop_records_service.py` also fall under the human's answer of journal entry 8.
- **S0001 and S0007**: none.

No earlier test was changed without a named leave.

## 7 The slow checks

The project offers nothing beyond `make check` today but `make duplicates` (a record, `0 new, 38 known, 0 gone`) and `make documents` (the docs stage's check). Both are green, and `make mutants` is check 3's.

The JUnit report (`.reports/junit.xml`) holds 6464 tests summing 720.9 s on all workers. The slowest five tests are the time-limit tests, at the ten-second `ROOMY_LIMIT` by design; none comes from this feature:

- `test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`, two rows at 11.5 s each.
- `test_process_session::test_time_limit_ends_every_process_of_the_session[run_process-own-group]`, 10.1 s.
- `test_make_commands::test_command_reaching_its_time_limit_is_killed`, 10.1 s.
- `test_process_session::test_process_the_kill_cannot_reach_does_not_hold_the_call[ended-in-between]`, 10.1 s.

Disk: at the start, `/work` held 0.5 GB used with 968.8 GB free; now it holds 0.5 GB used with 968.3 GB free. `/state` and `/tmp` hold 0.0 GB used, as before. The used space did not grow. The 0.5 GB fall in free space is shared by all three mounts, which are one host disk, so it is the host's and not this feature's.

## 8 Cost

The seven stories cost 65 runs, 70.3 min, 503 turns and $17.07 together:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 6 | 5.5 | $1.47 |
| S0002 | 10 | 9.6 | $2.36 |
| S0003 | 16 | 20.6 | $4.98 |
| S0004 | 6 | 4.6 | $1.09 |
| S0005 | 7 | 5.0 | $1.38 |
| S0006 | 14 | 21.3 | $4.97 |
| S0007 | 6 | 3.8 | $0.82 |

Two stories stand out, together 58 % of the dollars:

- **S0003** took three review rounds, each finding dead constants that the moves left behind (`_records_path`, `BODY`, then `PATH`) or one more refused-side row. It also had one doing stall on the mypy segfault (journal entry 27). The leftovers could have been found in one pass; the rounds came from reviewing the cleanup piece by piece.
- **S0006** was the feature's largest change: nine source modules and twenty test modules. It had a question at doing, one review round, and a docs stall on the detect-secrets false positive.

S0002 needed one review round, for three refused-side rows of its guard.

The human answered 3 questions, all of the cause `question`, and the stories waited 3.7 h for them:

- **S0003 at intake**: the guard's function names, and a confirmation of the variants.
- **S0005 at intake**: criterion 1 contradicted criterion 3 and the smoke test.
- **S0006 at doing**: two tests outside decision 11 still passed `settings=None`.

S0006 needed the human most. Its question stopped a finished source change at doing, because the leave of decision 11 had missed two test rows; the night log records "F0039-S0006 waits for a leave". The two intake questions were defects in the drafts that intake caught before any work.

## Proposed stories

- `backlog/F0039-S0008-the-guards-find-a-copy-of-every-shared-test-helper-by-its-body.md`: a guard by body for `log_lines`, `pushed`, `pushed_state`, `remote_document` and `push_state`, plus the move of the one copy it finds today (`_branch_document` in `test_reject.py`). This keeps the Goal's "finds them by their body", which the by-name guards do not.
- `backlog/F0039-S0009-the-tests-name-the-instance-in-one-place.md`: the 48 copies of `INSTANCE = "factory-1"` and `OWN` import `stage_run_support.INSTANCE`, with a guard by value. It is the feature's own kind of copy, noticed by S0005's reviewer and left outside the scope.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 2 stories proposed
   1. Scope: every scope item is built and archived. The Goal's "guard that finds them by their body" holds only for the definition: the log and branch-helper guards match by name, and one copy that the by-name search missed is still in the tests (`_branch_document` in `tests/application/handlers/test_reject.py`), so S0008. Decision 10's comment on `agent_home` was not written; it is one line, so it is left to the human.
   2. Feature smoke test: green for the runtimes, the docstrings, the return type, the wiring, the required boundaries and `make duplicates` (0 new). A copy with a helper's real body under a new name passes both guards (shown with planted copies). `make check` was green as found.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: the `agent_home` comment; `INSTANCE = "factory-1"` copied in 48 modules, so S0009; a one-time mypy segfault (S0003) and a detect-secrets false positive on prose (S0006), each of which stalled one stage once; the stale `instance` `None` line at `docs/decisions.md:493`; five guard modules with different rules; F0040's time-limit reading in `agent_home.py`, which `read_call_end` does not fit.
   5. Documentation: it agrees with the code and no removed statement remains. *Shared test helpers* never mentions the guards; S0008's docs criterion adds that sentence.
   6. Decisions: 1 to 13 of `feature.md`, two intake answers, the coders' defaults, and how the reviewers read the standing leave for dead leftovers (`BODY`, `PATH`, `_records_path`, `CountingGit`). Every earlier test was changed under a named leave.
   7. Slow checks: nothing beyond `make check`. `make duplicates` gives 0 new and `make documents` is ok. The slowest tests are the ten-second time-limit tests, none from this feature. Used disk is unchanged at 0.5 GB on `/work`; the 0.5 GB fall in free space is the shared host's.
   8. Cost: 65 runs, $17.07. S0003 ($4.98: three review rounds over leftovers of the moves, plus a mypy stall) and S0006 ($4.97: the largest change, a question, a docs stall) stand out. There were 3 questions (cause `question`) and 3.7 h of waiting; S0006 needed the human most, because decision 11's leave missed two test rows and that held a finished source change at doing.
