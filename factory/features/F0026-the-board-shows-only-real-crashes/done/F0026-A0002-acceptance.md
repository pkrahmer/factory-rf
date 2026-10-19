---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 277
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T18:31:45.378224Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T18:40:35.120866Z'
  stage: acceptance
  run: 73149d370e334165bb2874178d4709c9
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-19T18:42:58.724313Z'
  stage: done
stories: [F0026-S0001, F0026-S0002, F0026-S0003, F0026-S0004]
outcome: accepted
---

# Acceptance of The board shows only real crashes

## Recommendation

**Accepted.** The whole does what `feature.md` promised: through `factory-watch`'s `main`, a claim of the instance's own tick reads `event: idle:-  <work item> is held by self` while its lease runs and `event: crash:<work item>` from the lease's end on, for a story and for an acceptance. The tick's own evaluation still reads `crash` at any age. The feature smoke test is green, `make check` is green, and the mutation run kills 335 of 336 mutants, the one survivor being equivalent. S0002 to S0004, the stories the first acceptance (F0026-A0001) proposed, closed every finding it raised. What is left are small leftovers in tests and in the project guide, named below with a home. None of them is worth a story of its own, so none is proposed.

## 1 Scope

None. Every scope bullet of `feature.md` was built by S0001, which the first acceptance (F0026-A0001, merged as #263) checked against the code:
- `observed_claim_status` (`src/factory/domain/lease.py`);
- `ClaimService.observed_status` (`src/factory/application/claims.py`);
- `Watcher`'s keyword `observer` (`src/factory/application/watcher.py`);
- `run_watch` with `Watcher(boundaries, instance, observer=True)` (`src/factory/entry/watch.py:53`);
- the tests, and decision 5's change to `tests/test_claim_ownership.py`;
- the docs.

S0002 to S0004 are that acceptance's proposals, merged by the human. They lie outside `feature.md`'s Scope list, but inside its goal, and they change no code. Their merges touch only tests, and one sentence of `docs/project-guide/stages.md`:
- `b440b592` (S0002): `tests/entry/test_watch_main.py`, `tests/application/test_watcher_main_ref.py`;
- `6ac70a43` (S0003): `tests/application/test_claims_refusals.py`, the new `tests/work_item_support.py`, `tests/application/test_claims.py`, `tests/application/test_undo.py`, `docs/project-guide/stages.md:31`;
- `b96a0c5c` (S0004): `tests/conftest.py`, the new `tests/test_shared_fixtures.py`, 18 earlier test modules.

Out of scope held: no merge since #263 touches `src/`, `tests/application/test_watcher_move_rule.py`, `CLAIM_EVENTS`, `Tick` or `RecoveryHandler`. No story or smoke test made a paid call.

The "Done when" is met. Every story is merged, and `make check` on this branch ends `check: green` (`test: green (50.7 s)`, coverage 99.10 %). The only line `watch.py` leaves uncovered is 87, `raise SystemExit(main())`, which the human settled in S0002, entry 14.

## 2 Feature smoke test

The operator reads `factory-watch` while the container's own tick runs a stage: a story under a 60-minute lease and an acceptance under a 100-minute lease. Beside each look, the script shows what the tick's own evaluation (`Watcher(boundaries, "self")`, as `Tick` calls it) gives at the same moment.

Compared with the first acceptance's walk-through, this one also goes through the parts of `main` that S0002 pinned:
- `given`: boundaries, instance and streams are given;
- `std`: no streams are given, so `main` writes to `sys.stdout`/`sys.stderr`, as the installed command does;
- `env`: nothing is given, and `main` takes boundaries and instance from `boundaries_from_environment`.

In the `env` case only the fixed checkout is replaced by a stand-in that returns the same settings, since `/work/checkout` is not a test remote. The remote is a real local bare repository with clones, the acceptance is opened by `AcceptanceService.open`, and the hosting service is the fake. Nothing is paid.

Command, from the root of the checkout, with the script below saved in the run's own temporary folder:

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; uv run -q python "$TMPDIR/f26/feature_smoke.py" "$d"; echo "exit $?"
```

The script:

```python
"""F0026 end to end: the operator reads factory-watch while the instance's own tick runs a stage."""
import contextlib
import io
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.application.acceptance import AcceptanceService
from factory.application.pipeline_loading import PIPELINE_REF, PipelineLoader
from factory.application.watcher import Watcher
from factory.domain.settings import InstanceSettings
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState
from factory.entry import watch as watch_module
from factory.entry.watch import main, render_event
from factory.entry.wiring import build_boundaries

d = Path(sys.argv[1])
FEATURES = "factory/features"
STORY = f"{FEATURES}/F0001-example/in-progress/F0001-S0001-first.md"
REPORT = f"{FEATURES}/F0002-todo/in-progress/F0002-A0001-acceptance.md"
PIPELINE = """contract: "1.0"
acceptance_stage: acceptance
project_commands:
  check: {time_limit: 10}
roles:
  coder: {write_paths: ["src/*"]}
  acceptance-reviewer: {write_paths: ["{work_item}", "{feature}/backlog/*"]}
stages:
  doing: {role: coder, next: [approval], checks: [check]}
  acceptance: {role: acceptance-reviewer, next: [approval]}
  approval: {approval: true, next: [done, doing]}
  done: {}
"""


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args], cwd=cwd, check=True, capture_output=True)


def write(root: Path, path: str, text: str) -> None:
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(text, encoding="utf-8")


def push(branch: str, path: str, state: WorkItemState, body: str) -> None:
    git(human, "fetch", "-q", "origin")
    git(human, "switch", "-q", "-C", branch, f"origin/{branch}" if branch in pushed else "origin/main")
    pushed.add(branch)
    write(human, path, FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body=body)))
    git(human, "add", "-A")
    git(human, "commit", "-q", "-m", "state")
    git(human, "push", "-q", "origin", branch)


def claim(instance: str, stage: str, minutes: float, lease: int = 60) -> Claim:
    return Claim(instance=instance, stage=stage, started_at=datetime.now(UTC) - timedelta(minutes=minutes), lease_duration=lease)


def look(label: str, how: str = "given") -> None:
    boundaries.git.fetch()
    out, err = io.StringIO(), io.StringIO()
    if how == "given":
        status = main([], boundaries=boundaries, instance="self", out=out, err=err)
    elif how == "std":  # factory-watch as installed: no streams given
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = main([], boundaries=boundaries, instance="self")
    else:  # the environment gives boundaries and instance
        status = main([], out=out, err=err)
    definition = PipelineLoader(boundaries).load(boundaries.git.resolve(PIPELINE_REF))
    tick = render_event(Watcher(boundaries, "self").evaluate(definition))  # what Tick evaluates
    lines = out.getvalue().splitlines()
    print(f"{label:<34} [{how:<5}] watch: {status} {(lines[0] if lines else '')!r:<47} err={err.getvalue()!r} | tick: {tick!r}")


git(d, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
git(d, "clone", "-q", str(d / "remote.git"), "human")
human = d / "human"
pushed: set[str] = set()
write(human, "factory/pipeline.yml", PIPELINE)
write(human, f"{FEATURES}/F0001-example/feature.md", "# Example feature\n")
write(human, STORY, "# First story\n")
git(human, "add", "-A")
git(human, "commit", "-q", "-m", "start")
git(human, "push", "-q", "origin", "main")
for role in ("coder", "acceptance-reviewer"):
    write(d / "agents-home", f"agents/{role}.md", "---\nmodel: sonnet\ntools: [Read, Write]\nbudget_usd: 1\n---\nDo the work.\n")
git(d, "clone", "-q", str(d / "remote.git"), "checkout")
settings = InstanceSettings(repository_url="https://github.com/example/project.git", instance="self", checkout=d / "checkout", state_directory=d / "state", agent_home=d / "agents-home")
boundaries = build_boundaries(settings, "unused", hosting=FakeHostingService())
# The container's environment, as factory-watch reads it; only the fixed checkout is replaced.
watch_module.boundaries_from_environment = lambda environ, hosting=None: (settings, boundaries)

# 1. A story: the instance's own tick runs its doing stage under a 60-minute lease.
for minutes in (1, 59, 61):
    push("work-item/F0001-S0001", STORY, WorkItemState(stage="doing", claim=claim("self", "doing", minutes)), "# First story\n")
    for how in ("given", "std", "env"):
        look(f"story, own claim, {minutes}/60 min", how)
# 2. Another instance's claim keeps its judgement.
for minutes in (1, 61):
    push("work-item/F0001-S0001", STORY, WorkItemState(stage="doing", claim=claim("other", "doing", minutes)), "# First story\n")
    look(f"story, other's claim, {minutes}/60 min")
# 3. The story leaves; F0002 is complete and due; its acceptance runs under a 100-minute lease.
git(human, "switch", "-q", "main")
git(human, "pull", "-q", "--ff-only")
git(human, "rm", "-q", STORY)
write(human, f"{FEATURES}/F0002-todo/feature.md", "# Todo service\n")
write(human, f"{FEATURES}/F0002-todo/done/F0002-S0001-a.md", "# A\n")
git(human, "add", "-A")
git(human, "commit", "-q", "-m", "story gone, F0002 complete")
git(human, "push", "-q", "origin", "main")
git(human, "push", "-q", "origin", "--delete", "work-item/F0001-S0001")
look("F0002 complete, nothing claimed")
boundaries.git.fetch()
definition = PipelineLoader(boundaries).load(boundaries.git.resolve(PIPELINE_REF))
branch = AcceptanceService(boundaries, definition).open("F0002").branch
pushed.add(branch)
boundaries.git.fetch()
head = boundaries.work_item_reader.parse(boundaries.git.show_file(f"origin/{branch}", REPORT))
for minutes in (2, 99, 100, 130):
    state = head.state.model_copy(update={"stage": "acceptance", "claim": claim("self", "acceptance", minutes, 100)})
    push(branch, REPORT, state, head.body)
    look(f"acceptance, own, {minutes}/100 min", "env" if minutes == 99 else "given")
```

Output:

```
story, own claim, 1/60 min         [given] watch: 0 'event: idle:-  F0001-S0001 is held by self'    err='' | tick: 'event: crash:F0001-S0001'
story, own claim, 1/60 min         [std  ] watch: 0 'event: idle:-  F0001-S0001 is held by self'    err='' | tick: 'event: crash:F0001-S0001'
story, own claim, 1/60 min         [env  ] watch: 0 'event: idle:-  F0001-S0001 is held by self'    err='' | tick: 'event: crash:F0001-S0001'
story, own claim, 59/60 min        [given] watch: 0 'event: idle:-  F0001-S0001 is held by self'    err='' | tick: 'event: crash:F0001-S0001'
story, own claim, 59/60 min        [std  ] watch: 0 'event: idle:-  F0001-S0001 is held by self'    err='' | tick: 'event: crash:F0001-S0001'
story, own claim, 59/60 min        [env  ] watch: 0 'event: idle:-  F0001-S0001 is held by self'    err='' | tick: 'event: crash:F0001-S0001'
story, own claim, 61/60 min        [given] watch: 0 'event: crash:F0001-S0001'                      err='' | tick: 'event: crash:F0001-S0001'
story, own claim, 61/60 min        [std  ] watch: 0 'event: crash:F0001-S0001'                      err='' | tick: 'event: crash:F0001-S0001'
story, own claim, 61/60 min        [env  ] watch: 0 'event: crash:F0001-S0001'                      err='' | tick: 'event: crash:F0001-S0001'
story, other's claim, 1/60 min     [given] watch: 0 'event: idle:-  F0001-S0001 is held by other'   err='' | tick: 'event: idle:-  F0001-S0001 is held by other'
story, other's claim, 61/60 min    [given] watch: 0 'event: expired:F0001-S0001'                    err='' | tick: 'event: expired:F0001-S0001'
F0002 complete, nothing claimed    [given] watch: 0 'event: acceptance_due:F0002  acceptance of F0002 is due' err='' | tick: 'event: acceptance_due:F0002  acceptance of F0002 is due'
acceptance, own, 2/100 min         [given] watch: 0 'event: idle:-  F0002-A0001 is held by self'    err='' | tick: 'event: crash:F0002-A0001'
acceptance, own, 99/100 min        [env  ] watch: 0 'event: idle:-  F0002-A0001 is held by self'    err='' | tick: 'event: crash:F0002-A0001'
acceptance, own, 100/100 min       [given] watch: 0 'event: crash:F0002-A0001'                      err='' | tick: 'event: crash:F0002-A0001'
acceptance, own, 130/100 min       [given] watch: 0 'event: crash:F0002-A0001'                      err='' | tick: 'event: crash:F0002-A0001'
exit 0
```

**Green.** Within its lease, an own claim reads as held in `factory-watch` and as a crash in the tick's evaluation, for a story and for an acceptance. This holds through every way into `main`: given streams, the standard streams, and the environment. From the lease's end on, both read a crash. Another instance's claim is judged the same by both.

I also tried a look at a mirror of the real remote, where this very acceptance is claimed by `self` under a 100-minute lease, which is the night's case. It did not happen:
- The wrapper's git runs without global configuration, so it refuses `/work/checkout` itself ("dubious ownership"), which another user owns.
- The permission layer refused the mirror (a `git push` into a temporary bare repository).

I did not try another route. The synthetic walk-through above covers the same case.

## 3 Mutation score

`make mutants` on this branch re-ran the mutants that were not killed in the four modules the feature's story commits changed (`claims.py`, `watcher.py`, `lease.py`, `watch.py`). It ran once, to its end, without a `stopped after` line. The part of its output after the progress lines:

```
🎉 factory.application.claims.x__work_item_id__mutmut_5
🎉 factory.application.claims.xǁClaimServiceǁ__init____mutmut_3
🎉 factory.application.claims.xǁClaimServiceǁ_check_preconditions__mutmut_11
🎉 factory.application.claims.xǁClaimServiceǁ_check_preconditions__mutmut_2
🎉 factory.application.claims.xǁClaimServiceǁ_check_preconditions__mutmut_8
🎉 factory.application.claims.xǁClaimServiceǁ_lease_duration_of__mutmut_2
🎉 factory.application.claims.xǁClaimServiceǁ_lease_duration_of__mutmut_6
🎉 factory.application.watcher.xǁWatcherǁ_main_commit__mutmut_4
🎉 factory.application.watcher.xǁWatcherǁ_main_commit__mutmut_5
🙁 factory.application.watcher.xǁWatcherǁevaluate__mutmut_40
🎉 factory.entry.watch.x_main__mutmut_13
🎉 factory.entry.watch.x_main__mutmut_18
  ... (x_main__mutmut_19 to _26, _4, _5, _6, _7, _9 and x_run_watch__mutmut_4, _5: all 🎉)
factory.application.watcher.xǁWatcherǁevaluate__mutmut_40: survived
mutants: 335 killed, 1 survived, 0 timed out, 0 without tests, 0 not checked, 0 other of 336 mutant(s) in 4 module(s)
```

**335 of 336 killed. The result is not partial** (the first acceptance had 309 of 336). Every survivor of the first acceptance's groups is now killed:
- group 1, `watch.main` (14), by S0002;
- group 2, the "origin/main does not resolve" text (4), by S0002;
- group 3, `ClaimService`'s refusal texts (7), by S0003.

The one survivor is the first acceptance's group 4, `Watcher.evaluate__mutmut_40`, which passes `None` for the definition to `ClaimService`. It is equivalent: `status` and `observed_status` never read the definition, which serves `claim`'s lease only. No new group, and no story.

None of S0002 to S0004 had a mutation report to read: their coder entries carry no `mutants` line, or S0004's "no module under src/factory changed". So no review passed on any group as a note. These survivors were read only by the first acceptance, and are closed here.

## 4 What the stories noticed

From the archived stories since the first acceptance, each judged:
- **S0002, coder (entries 9, 13) and reviewer (entry 11):** line 87 of `watch.py` stays uncovered, while the Description says "pins all of that". The human settled it with option (a) in entry 14. The archived Description still carries the old sentence, and only the journal records the exception. Closed; `done/` is not mine to edit.
- **S0002, reviewer notes (entry 18):**
  - The stand-in in `tests/entry/test_watch_main.py:112` names its keyword `_hosting`, while the real `boundaries_from_environment` names it `hosting`.
  - The criterion-3 test does not assert `main`'s status, which criteria 1 and 2 pin.

  Both are cosmetic, and no story is proposed. A later tester touching the module may rename the keyword.
- **S0002, documenter (entry 20):** `docs/project-guide/watching.md`, *The watcher's command line* (line 68), does not say that `main` falls back to `sys.stdout`/`sys.stderr`. Seen here too: the same paragraph says `run_watch` returns 1 only "for `PipelineDefinitionInvalid`", though it also returns 1 for `AgentDefinitionInvalid` (`watch.py:49-51`). The operator guide (line 1169) states both correctly. This is an omission in the agents' guide, not a contradiction. See 5.
- **S0003, reviewer notes (entry 20):**
  - `_start` in `tests/application/test_undo.py:62-70` still repeats `put_work_item`'s sequence;
  - `BODY` is repeated in three claim and undo test modules;
  - `_snapshot` in `test_claims_refusals.py` is a four-field variant of the one in `test_claims.py`.

  Seen here: `_snapshot` is defined in ten test modules, and `_text` in five, with different signatures and purposes. They are variants, not copies of one helper, so no story is proposed.
- **S0003, tester and coder (entries 16, 18):** `test_undo.py`'s `_start` keeps its own checkout order, because it writes base files between checkout and work item. That reason is sound. Closed.
- **S0002 and S0003, coder (entries 13, 14, 16, 18):** the coder is told to rewrite `## Description` when the journal changes it, but `{work_item}` is not in the coder's write paths (`factory/pipeline.yml:26`), so each refusal cost a round:
  - In S0002 it became the human's question 1.
  - In S0003 the reviewer, whose write paths hold the work item, made the rewrite itself (entry 20).

  This is a property of the pipeline, not of this feature, and `factory/` is the human's. Listed under 6.
- **S0004, reviewer note (entry 9):** the coders' `make duplicates` showed `5 new` on every story. I ran it here, and it gives the same result: `duplicates: 5 new, 33 known, 3 gone`. The new findings are:
  - four similar-code pairs between `claude_runtime.py` and `opencode_runtime.py`;
  - the unused `ManualWaiter` in `adapters/clock.py`.

  None is in a module this feature changed, so none is this feature's. I name them for the human.
- **S0004, intake (entry 3):** `tests/adapters/test_agent_files.py::_agents(agent_home)` and `tests/domain/test_decision_rules.py::definition()` have other signatures and purposes. They are correctly left out. Closed.
- **Carried from the first acceptance:** the `_MAIN_REF`/`PIPELINE_REF` constant is defined in seven application modules. This is unchanged, and older than the feature, so I name it again with no story.

## 5 The documentation as a whole

Nothing of weight. S0002 and S0004 changed no document. S0003's documenter changed one sentence: `docs/project-guide/stages.md:31` now points to `put_work_item`/`created_state` in `tests/work_item_support.py`, which exist and are used as it says. Read from the top, these agree with each other and with the behaviour the smoke test shows:
- the operator guide's `factory-watch` section (lines 1150-1169);
- its *Claims, leases and the clock* (line 1469);
- `docs/project-guide/stages.md`, *Status* and *Observed status*;
- `docs/project-guide/watching.md` lines 9 and 68.

Two omissions in `watching.md` line 68, the agents' guide, contradict nothing:
- the agent-file refusal that also returns 1;
- `main`'s default streams.

The operator guide, which the operator reads, states both. The next story that touches `factory.entry.watch` can carry them in its docs criterion. The first acceptance's remark that the provider-limit section (*The wait*, around line 243) does not mention `factory-watch`'s crash display still stands. The `factory-watch` section says it (line 1168), so it is no contradiction either.

## 6 Decisions taken for the human

From `feature.md`, decisions 1 to 8, which the first acceptance listed and the human accepted by merging #263:
1. the cause is the second process;
2. `observed_claim_status`, with the `Watcher` keyword `observer`;
3. a real crash shows at the latest when its lease runs out;
4. a provider-limit wait past its lease shows as a crash;
5. the leave for `tests/test_claim_ownership.py`;
6. the flaky test gets no fix. No story of F0026 recorded a failure of it, so `CLAUDE.md`'s new bullet has not been needed yet;
7. the folder's name;
8. the human's answers of 2026-10-19.

The human's answers in the later stories:
- **S0002, entry 14, option (a):** line 87 of `watch.py` (`raise SystemExit(main())`) stays uncovered. There is no pragma and no subprocess test, and the Description's "pins all of that" is read with that exception.
- **S0003, entry 10, option (b):** the leave to move `_file_text` (merged with `test_undo.py`'s `_text`) and the work-item preparation into `tests/work_item_support.py`, and to change `test_claims.py` and `test_undo.py` to use it.

Defaults the agents took:
- **S0003, tester (entry 16):** `_start` in `test_undo.py` does not use `put_work_item`, rather than giving it a new parameter. `BODY` stays in each module.
- **S0003, reviewer (entry 20):** rewrote the work item's Description and Interface itself, from the human's wording, rather than sending it back to `doing`, where no stage could write it.
- **S0004, tester (entry 5):** the search tests match the signatures at column 0, so they do not find their own string literals. `installed_agents` is not autouse, and modules opt in with `pytestmark`, as the Interface said.

Left for the human (not decided here): the coder cannot write the work item, yet it is the stage told to rewrite `## Description` when the journal changes it. Twice in this feature that cost a round, and once a question. The options I see:
- give the coder `{work_item}` in `factory/pipeline.yml`;
- or let the reviewer own the rewrite, as S0003's reviewer did;
- or leave it.

I would choose the reviewer, since it already holds the path. This is a change to `factory/`, the human's.

Earlier tests changed, each with its leave, as the reviewers' entries name them:
- **S0002:** none (only added files, reviewer entries 11 and 18).
- **S0003** (reviewer entry 20):
  - `tests/application/test_claims.py`: the human's leave, entry 10;
  - `tests/application/test_undo.py`: the human's leave, entry 10.
- **S0004** (reviewer entry 9), all under the standing leave to move a shared test helper:
  - `tests/conftest.py`;
  - the eleven acceptance modules that lost their `definition` copy: `test_acceptance_closed.py`, `test_acceptance_due_handler.py`, `test_acceptance_hand_over.py`, `test_acceptance_merged.py`, `test_acceptance_merged_before_approval.py`, `test_acceptance_reading.py`, `test_acceptance_repeated.py`, `test_acceptance_service.py`, `test_acceptance_snapshots.py`, `test_stage_run_acceptance.py`, `test_task_acceptance.py`;
  - `test_pipeline_loading_agents.py`, `test_tick.py`, `test_tick_disk.py`, `test_tick_stop_records.py`, `tests/entry/test_watch.py`, `test_watch_acceptance.py`, `test_watch_own_claim.py`.

No earlier test was changed without a leave.

## 7 The slow checks

The project offers no slow check beyond `make check` and `make mutants`: no image scan, no SBOM. `make duplicates` is a record, not a check; see 4.

Disk: no growth the feature does not explain.

| Filesystem | Previous record | Now |
|---|---|---|
| `/work` | 0.5 GB used | 0.5 GB used |
| `/state` | 0.0 GB used | 0.0 GB used |
| `/tmp` | 0.0 GB used | 0.0 GB used |

Free space fell from 978.2 to 977.2 GB on all three, which share one filesystem. That 1 GB is outside the factory's folders, and the feature added only test files, so it is not this feature's.

The JUnit report of my `make check` holds 5947 tests, 545.4 s summed over the workers. The slowest four are none of this feature's:
- `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`, 5.01 s;
- `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`, 5.01 s;
- `test_fault_paths_7_to_13::test_acceptance_container_lost_in_review_reruns_once_and_books_result[accepted]`, 4.53 s;
- `test_fault_paths_7_to_13::test_round_cap_question_killed_between_post_and_record_posts_once_and_waits`, 3.76 s.

The 20 test cases S0002 to S0004 added take 2.63 s together. The slowest is `test_watch_main::test_main_writes_to_the_standard_streams_when_none_are_given[held-story]`, 0.34 s.

## 8 Cost

The four stories cost 36 runs, 34.8 min, 249 turns, 849492 tokens in (4898667 more from cache), 103167 out, **$8.91**.

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 10 | 12.2 | $3.33 |
| S0002 | 9 | 7.2 | $1.81 |
| S0003 | 11 | 10.2 | $2.54 |
| S0004 | 6 | 5.2 | $1.23 |

S0001 stands out. It is the only story that built code, and it had a round of moving copied test helpers (see the first acceptance's cost section).

S0002 to S0004 built no code; their tests passed on arrival. Still, S0002 and S0003 each took an extra round:
- **S0002:** a crash in its tests stage (entry 5, "ended without a result"), then the coder's refused Description edit (entries 13, 16).
- **S0003:** the reviewer's question on the copied helpers (entry 9) and the round that moved them (entries 12-20).

S0004 went straight through for $1.23.

Human interventions: **2 questions answered, both of the cause "question", 0.1 h waited.**
- S0002, entry 13: line 87 and the Description, answered (a).
- S0003, entry 9: the copied helpers against "no earlier test changes", answered (b).

Each story needed the human once. S0003 cost more for it, a full rework round. Both questions came from the text of the first acceptance's proposals, that is, from this role:
- S0002's Description promised "all of that" including a line only a subprocess reaches;
- S0003's Interface said "no earlier test changes", where the standing leave was the obvious remedy for a copy.

When I propose stories, I should say what stays uncovered, and name the standing leave in advance.

## Proposed stories

None. Every leftover found is cosmetic, settled, outside the feature or the human's to decide (4 and 6). The two omissions in `docs/project-guide/watching.md` (5) are too small to carry a story's cost of their own. The next story that touches `factory.entry.watch` can take them up in its docs criterion.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed; make mutants 335/336
   1 Scope: none. S0001 built every scope item. S0002 to S0004, the first acceptance's proposals, changed only tests and one sentence of `stages.md` (merges b440b592, 6ac70a43, b96a0c5c). No out-of-scope part was touched. `make check` is green (coverage 99.10 %).
   2 Feature smoke test: green. Through `factory-watch`'s `main`, an own claim reads `idle … is held by self` within its lease and `crash` at and past it. That holds for a story (60-min lease) and for an acceptance (100-min lease), with given streams, the standard streams and the environment fallback. The tick's evaluation reads `crash` at any age, and another instance's claim is unchanged. The look at a mirror of the real remote was not made: git refused the checkout's ownership, and the permission layer refused the mirror.
   3 Mutation score: 335/336 killed, not partial (the first acceptance had 309/336). S0002 and S0003 killed every survivor of the first acceptance's groups 1–3. The one survivor, `Watcher.evaluate__mutmut_40`, is equivalent. There is no new group, and no review passed on one as a note.
   4 What the stories noticed: line 87 of `watch.py` was settled by the human. The leftovers are cosmetic, and none is worth a story:
   - the `_hosting` keyword in the stand-in;
   - `BODY`, `_snapshot` and `_start` variants in the tests;
   - `duplicates: 5 new`, all in the runtimes and `clock.py`, not this feature's;
   - `_MAIN_REF` repeated in seven modules.
   The coder could not rewrite `## Description`; this cost two rounds and went to 6.
   5 Documentation: nothing of weight. `watching.md` line 68 omits the agent-file refusal and `main`'s default streams; the operator guide states both. Nothing contradicts the behaviour.
   6 Decisions taken for the human: `feature.md` decisions 1–8; the human's answers S0002 (a), line 87 uncovered, and S0003 (b), helpers moved to `tests/work_item_support.py`; the defaults of the S0003 and S0004 testers and of S0003's reviewer. Open for the human: who rewrites a Description, since the coder lacks `{work_item}`; I would choose the reviewer. Every earlier test was changed with a leave: entry 10 of S0003, or the standing leave for S0004's 19 modules.
   7 Slow checks: none beyond `make check` and `make mutants`. Disk used is unchanged (0.5 GB on /work). Free space fell by 1 GB on the shared filesystem, outside the factory's folders. The slowest tests are the 5.01 s runtime time-limit tests, none of them this feature's. The 20 new test cases take 2.63 s together.
   8 Cost: $8.91 over 36 runs and 34.8 min: S0001 $3.33, S0002 $1.81, S0003 $2.54, S0004 $1.23. Two questions answered, 0.1 h waited, one each for S0002 and S0003. S0003 cost more for its question: a full rework round. Both questions came from the wording of the first acceptance's proposals.
3. factory: done (pull request merged); cost: 1 runs, 8.8 min, 25 turns, 113992 tokens in (1832007 more from cache), 22537 out, $1.73
