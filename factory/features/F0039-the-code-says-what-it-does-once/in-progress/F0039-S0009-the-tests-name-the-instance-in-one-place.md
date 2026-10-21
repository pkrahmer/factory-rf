---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 403
comments_read: [6312436133]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T09:14:38.811467Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T09:14:38.817732Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-21T09:15:00.929651Z'
  stage: intake
  run: f9a8aa83b9bc4c65a4dec10f205f7757
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-21T09:17:23.808366Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-21T09:17:42.021954Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-21T09:17:59.454576Z'
  stage: intake
  run: 58488a49e33940d2a6842ab596a0e7f5
---

# The tests name the instance in one place

<!-- proposed by feature acceptance of 2026-10-21; refine before starting -->

## Description

Forty-eight test modules define `INSTANCE = "factory-1"` at the top level, beside `tests/stage_run_support.py`, and five modules already import it from there or from a copy. `tests/domain/test_lease.py` names the same instance `OWN = "factory-1"`. One module imports the constant from another test module: `tests/application/test_tick_project_agent.py` from `application.test_tick_agent_definition`, the pattern F0039-S0003 removed for `_pushed`. The reviewer of F0039-S0005 noted the copies and did not count them as a finding, because the feature's scope did not name them. This story moves them, under the standing leave of `CLAUDE.md` (*Tests*), which names constants. `stage_run_support.INSTANCE` becomes the one definition. Every other module imports it from there, and `OWN` becomes `OWN = INSTANCE`. A guard finds a new copy by its value. The tester does the work; no module under `src/factory/` changes and the coder has nothing to build. Unchanged: every other instance name (`"factory-7"` and the like), the instance that the `boundaries` fixture's settings name inside a call, and the `ENVIRONMENT` constants, which are copied too (eleven and ten modules with two different values). They are left to a later story if the human wants it.

A check on the work, not a criterion: the tester lists the `pytest --collect-only` ids of the modules the Interface names before and after the move (in `$TMPDIR`), says in the journal that they match, and the reviewer confirms it.

## Interface

No module under `src/factory/` changes.

`tests/stage_run_support.py`: `INSTANCE = "factory-1"` stays, the one top-level assignment of that value under `tests/`.

The modules whose top-level `INSTANCE = "factory-1"` is removed and that import `INSTANCE` from `stage_run_support` instead: `tests/acceptance_walk.py`, `tests/application/handlers/test_run.py`, `tests/application/test_after_agent.py`, `tests/application/test_board_reader.py`, `tests/application/test_board_reader_acceptance.py`, `tests/application/test_claims.py`, `tests/application/test_claims_observed.py`, `tests/application/test_cost_image.py`, `tests/application/test_costs.py`, `tests/application/test_no_state_refusals.py`, `tests/application/test_recovery_crash.py`, `tests/application/test_sealed_runs.py`, `tests/application/test_stage_finish.py`, `tests/application/test_stage_launch.py`, `tests/application/test_stage_run_acceptance.py`, `tests/application/test_stall_labels.py`, `tests/application/test_stalls.py`, `tests/application/test_stop_records_service.py`, `tests/application/test_tick.py`, `tests/application/test_tick_agent_definition.py`, `tests/application/test_tick_disk.py`, `tests/application/test_tick_ignored.py`, `tests/application/test_tick_preflight.py`, `tests/application/test_tick_stale_branch.py`, `tests/application/test_tick_stop_details.py`, `tests/application/test_tick_stop_records.py`, `tests/application/test_watcher.py`, `tests/application/test_watcher_acceptance.py`, `tests/application/test_watcher_move_rule.py`, `tests/application/test_watcher_observer.py`, `tests/crash_support.py`, `tests/domain/test_lease_observed.py`, `tests/entry/test_run.py`, `tests/entry/test_watch.py`, `tests/entry/test_watch_acceptance.py`, `tests/entry/test_watch_agent_definition.py`, `tests/entry/test_watch_main.py`, `tests/entry/test_watch_own_claim.py`, `tests/entry/test_watch_settings.py`, `tests/entry/test_wiring_acceptance.py`, `tests/entry/test_wiring_constants.py`, `tests/entry/test_wiring_environment.py`, `tests/entry/test_wiring_handlers.py`, `tests/entry/test_wiring_human_handlers.py`, `tests/entry/test_wiring_recovery.py`, `tests/entry/test_wiring_recovery_expired.py`, `tests/proof_support.py` and `tests/undo_support.py`.

- A module that imported `INSTANCE` from `crash_support` or from `application.test_tick_agent_definition` (`test_recovery_expiry.py`, `test_recovery_cap.py`, `test_tick_project_agent.py`) imports it from `stage_run_support`. `mypy --strict` refuses an import of a name that a module only imported itself.
- `tests/domain/test_lease.py`: `OWN = "factory-1"` becomes `OWN = INSTANCE`, with `INSTANCE` from `stage_run_support`. The name `OWN` stays.
- No import cycle is added: `stage_run_support` imports `git_support` and `human_clone` only, and keeps doing so.

`tests/test_shared_constants.py` (new), the guard:

```python
def instance_copies(source: str) -> list[str]:
    """The names that a top-level assignment in `source` gives the value `"factory-1"`."""
```

- An assignment counts at the top level of a module, plain (`=`) or annotated, when its value is the string constant `"factory-1"`, whatever the name.
- An assignment inside a function or a class, a different string, or a name as the value (`OWN = INSTANCE`) does not count.
- The guard reads every `*.py` file under `tests/`.

## Acceptance criteria

1. The instance is written in one module: the modules under `tests/` for which `instance_copies` is not empty are exactly `["stage_run_support.py"]` (paths relative to `tests/`, sorted).
2. The guard counts a top-level assignment of the value under any name and nothing else (rows of one parametrized test, each a source text read by `instance_copies`). `INSTANCE = "factory-1"\n` → `["INSTANCE"]`. `OWN = "factory-1"\n` → `["OWN"]`. `NAME: str = "factory-1"\n` → `["NAME"]`. `INSTANCE = "factory-7"\n` → `[]`. `OWN = INSTANCE\n` → `[]`. `def f():\n    name = "factory-1"\n` → `[]`. `class C:\n    NAME = "factory-1"\n` → `[]`.
3. `make check` stays green.
4. docs: `docs/project-guide/README.md`, *Shared test helpers*: the `stage_run_support.py` line also names `INSTANCE`, the instance name `"factory-1"` that every test module imports from there. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none. Nothing an operator or a newcomer sees changes, and no decision is taken.

## Smoke test

```bash
grep -rl --include='*.py' '^[A-Z_]* = "factory-1"$' tests | sort
```
Expect: one line, `tests/stage_run_support.py` (before the story, 50 lines)

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
TMPDIR="$d" uv run pytest --no-header --tb=short -p no:cacheprovider tests/test_shared_constants.py tests/domain/test_lease.py tests/application/test_tick_project_agent.py tests/application/test_recovery_cap.py tests/entry/test_wiring_constants.py > "$d/out" 2>&1
echo "exit $?"
```
Expect: one line, `exit 0`

```bash
grep -c '^- `stage_run_support.py`:.*`INSTANCE`' docs/project-guide/README.md
```
Expect: one line, `1` (before the story, `0`)

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: 1. Criterion 3 ("the ids that `pytest --collect-only` lists for the modules the Interface names are the same before and after the story, and all of them pass") cannot be tested by one test function. A test cannot see the ids from before the story, and the criterion names no stored list to compare with. It is a check on the work, not on the behaviour. The options I see:
      (a) Drop criterion 3. `make check` (criterion 4) already runs every earlier test, and the standing leave in `CLAUDE.md` (*Tests*) already requires that each earlier test keeps its name. I would choose this one.
      (b) Keep it as a note for the reviewer and not as a criterion. It would move to the Description.
      (c) Make it testable: the criterion names a file with the ids, committed by the story, and a test compares `--collect-only` against it. This adds a maintenance burden for no gain.

   The other checks found nothing to ask.
   - Format check: passed.
   - Interface: modules and signatures are concrete (`instance_copies(source) -> list[str]`, the full list of modules, `OWN = INSTANCE`).
   - Rules with a failing side: the guard's rules each have a row in criterion 2, covering annotated, `OWN = INSTANCE`, a function, a class and a different value.
   - Smoke test: the commands are runnable. pytest's `addopts` sets `-q`, and the command passes none. Every `Expect:` line is checkable.
   - Architecture: the story changes only `tests/` and one docs line.
   - Scope: it is within F0039's scope (*Shared test helpers*, the standing leave for constants). It touches nothing under *Out of scope*, and `ENVIRONMENT` stays out.
4. 2026-10-21 human: Answer from the human's operator, within F0039's decisions (no new leave, no product decision):

   (b). Move criterion 3 into the Description as a check on the work, not a criterion: the tester lists the `pytest --collect-only` ids of the modules the Interface names before and after the move (in `$TMPDIR`), says in the journal that they match, and the reviewer confirms it. The story changes about fifty test modules, so the comparison should be made, as F0039-S0008's tester did. Renumber the criteria that follow.

   Please write this into the story and go on.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete. It gives `instance_copies(source: str) -> list[str]`, the full list of modules that import `INSTANCE` from `stage_run_support`, and `OWN = INSTANCE`.
   - Criteria: each is testable by one test function, and the guard's rules each have a row in criterion 2. Those rows cover plain and annotated assignments, a different value, a name as the value, a function and a class. Criterion 3 of my first entry is carried in as the human's edit from journal entry 4, answer (b). It is now a sentence in the Description: a check on the work. The tester lists the `pytest --collect-only` ids of the modules the Interface names before and after the move (in `$TMPDIR`) and says in the journal that they match, and the reviewer confirms it. The criteria after it are renumbered: `make check` is 3 and `docs:` is 4.
   - Smoke test: the commands are runnable. The pytest command passes no `-q`, because the project's `addopts` already sets one. Each `Expect:` line is checkable.
   - Architecture: the story changes only `tests/` and one docs line, and no module under `src/factory/` changes.
   - Scope: it is within F0039's scope (*Shared test helpers* and the standing leave for constants). It touches nothing under *Out of scope*, and the `ENVIRONMENT` constants stay out.
