# The tests pin the expiry note's key at the crash cap and the stalls at their edges

## Description

The mutation sweeps of 2026-10-19 over `factory.application` (`planning/overnight/mutation-sweep-2026-10-19-part2.md`, story 7, and `-part3.md`, its addition to it) left seven live mutants in the recovery and the stalls, each a side that no test reaches. An expiry at the crash cap posts its note under the key of the *expiry* record (`recovery.py:124`). The last factory record is then the crash-cap question, and no test reads the note's number there. Two stalls carry no detail: the merge-conflict stall (`stage.py:452`, through `StallService.stall`'s default at `stalls.py:64`) and the stall when the agent left its branch (`stage.py:226`). No test pins their note or their entry, so a default detail would pass. When the agent commits on its work branch and then switches to another one, the stall must start the branch again at the stage-start commit (`stalls.py:103`). No test has such an agent, so a stall that kept the agent's commit would pass. A red check stalls with the stage-start commit, so the stall undoes what the check wrote outside the write paths (`stage.py:362`). No check in a test writes such a file. This story pins these as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003.

## Interface

No module under `src/factory/` changes. The behaviour pinned (`application`):

- `factory.application.recovery.RecoveryHandler.handle(event)` for an `expired` event: the expiry note's key is `PostKey(work_item=<id>, kind="expiry", n=<the expiry record's number>)`, also at the crash cap, where the crash-cap question follows under its own record's number.
- `factory.application.stalls.StallService.stall(context, reason, detail="")` with the stalls of `factory.application.stage.StageRunner.run`: a merge conflict and a run that left the work item's branch stall with no detail, so the note says only the reason's sentence and the entry ends with it.
- `StallService.stall` after a run that left the branch: the branch is checked out again at the stage-start commit, so a commit the agent made on it is not part of the stall.
- `factory.application.stage.StageFinisher.finish` at a red check: the stall undoes from the stage-start commit, a file the check wrote outside the write paths included.

Tests (the tester writes them):

- `tests/application/test_recovery_expiry_key.py` builds on `tests/crash_support.py` as it is: `expired_claim`, `open_pull_request`, `snapshot`, `expired_event`, `other_handler` and `Rerun`.
- `tests/application/test_stall_edges.py` builds on `tests/stage_run_support.py` as it is: `open_story`, `run_stage`, `completed`, `stage_makefile`, `BRANCH` and `PATH`. Its agent runtime that leaves the branch is a small class of its own around the `agent_runtime` fixture, as `CommittingRuntime` of `tests/application/test_stage_run.py` is one there. Before it plays the queued run, it always writes `tests/test_a.py` and commits it (`"the agent's commit"`) on the work branch, and it then checks out `elsewhere` at `HEAD`. So it is no copy of the two `SwitchingRuntime` classes: the one of `tests/application/test_after_agent.py` leaves without a commit, the one of `tests/application/test_stalls.py` commits on the other branch. The test runs the stage with `run_stage(replace(boundaries, agent_runtime=<it>))`.

A stall's *note* is the first line of the one factory post on `report.pull_request`. Its *entry* is the text (`entry_text`) of the last journal record of the work item at `report.commit`. No earlier test changes.

## Acceptance criteria

1. The expiry note's key (rows of one parametrized test; `number = open_pull_request(hosting)`, `expired_claim(boundaries, human, clock, crashes=<crashes>, pull_request=number)`, then `other_handler(boundaries, claimed, Rerun()).handle(expired_event(snapshot(boundaries)))`; the journal before is `1` human `created`, `2` factory `started`):
   - `crashes=1`, at the cap of 2: the keys of `hosting.factory_posts(number)` are exactly `[PostKey(work_item="F0001-S0001", kind="expiry", n="3"), PostKey(work_item="F0001-S0001", kind="crash_cap", n="4")]`.
   - `crashes=0`, below the cap: exactly `[PostKey(work_item="F0001-S0001", kind="expiry", n="3")]`.
2. The stalls without a detail (rows of one parametrized test; each gives the note and the entry):
   - A merge conflict: `open_story(boundaries, human, agent_home, main_files={"notes.md": "base\n"})`, then the human pushes `notes.md` as `branch\n` to `work-item/F0001-S0001` and as `main\n` to `main`, a fetch, `run_stage(boundaries)`: the note `Stalled (attempt 1 of 2): merging the main branch conflicts and the merge was aborted. Retrying on the next tick.`, the entry `Stage tests stalled (attempt 1 of 2): merging the main branch conflicts and the merge was aborted`.
   - A run that left the branch: `open_story(boundaries, human, agent_home)`, `ScriptedRun(result=completed())` queued, the runtime of the Interface: the note `Stalled (attempt 1 of 2): the agent left the work item's branch. Retrying on the next tick.`, the entry `Stage tests stalled (attempt 1 of 2): the agent left the work item's branch`.
3. A commit on the branch before the agent left it (one test; as the second row of criterion 2): `report.stall.reason` is `left_branch`; the subjects of `boundaries.git.log(report.commit, since="origin/main")` are exactly `["work item F0001-S0001: tests stalled", "work item F0001-S0001: tests starts as factory-1", "write factory/features/F0001-example/in-progress/F0001-S0001-first.md"]`, so the stall commit's parent is the stage-start commit; and `boundaries.git.show_file(report.commit, "tests/test_a.py")` is `None`.
4. What a red check wrote is undone (one test): `open_story(boundaries, human, agent_home, makefile=stage_makefile({"lint": 1}, extra=["@echo checked > written-by-lint.txt"]))`, `ScriptedRun(result=completed("doing"))` queued, `run_stage(boundaries)`: `report.rule` is `5` and `report.stall.reason` is `check_red`; `boundaries.git.show_file(report.commit, "written-by-lint.txt")` is `None`, and the file is not in the checkout.
5. `make check` stays green.
6. docs: none. The operator guide and `docs/project-guide/` already describe the expiry note, the stalls and the undo, and this story changes none of them.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.domain.post_texts import stall_note

print(stall_note("merge_conflict", 1, 2))
print(stall_note("left_branch", 1, 2))
EOF
```

Expect: two lines, `Stalled (attempt 1 of 2): merging the main branch conflicts and the merge was aborted. Retrying on the next tick.` and `Stalled (attempt 1 of 2): the agent left the work item's branch. Retrying on the next tick.`

## Journal
