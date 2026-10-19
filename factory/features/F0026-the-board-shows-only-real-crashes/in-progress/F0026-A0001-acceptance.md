---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 263
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T12:54:26.517792Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T13:12:44.897605Z'
  stage: acceptance
  run: 3b7b8dd78a92487392e2b4f189162382
stories: [F0026-S0001]
outcome: null
---

# Acceptance of The board shows only real crashes

## Recommendation

**Accepted with stories.** The feature does what `feature.md` promised. `factory-watch` now shows a claim of its own instance as `event: idle:-  <work item> is held by <instance>` while the claim's lease runs, and as `event: crash:<work item>` from the lease's end on, for stories and acceptances alike. The tick's judgement is unchanged: it still shows `crash` for its own claim at any age. The feature smoke test below is green on the real entry points, `make check` is green, and the documents agree with the behaviour.

None of the findings is a broken promise. They are survivors and leftovers in the modules the story touched:
- `factory-watch`'s `main` is never run through to the watch by any test (14 survivors).
- The refusals of `ClaimService` and the "does not resolve" errors are not pinned by their text.
- The story moved the `definition` fixture to `tests/conftest.py`, but 11 earlier modules still hold word-for-word copies of it, and 7 modules hold copies of the agent-installing fixture.

Three stories are proposed (S0002 to S0004).

## 1 Scope

The one archived story, S0001, built every scope bullet:
- `observed_claim_status` in `src/factory/domain/lease.py:36`;
- `ClaimService.observed_status` in `src/factory/application/claims.py:77`;
- `Watcher`'s keyword `observer` in `src/factory/application/watcher.py:23,48-49`;
- `run_watch` evaluating with `Watcher(boundaries, instance, observer=True)` in `src/factory/entry/watch.py:53`;
- the tests it names, and the earlier test module of decision 5: only `LEASE_FUNCTIONS` in `tests/test_claim_ownership.py` changed;
- the docs of its criterion 8, in the operator guide, `docs/project-guide/stages.md`, `docs/project-guide/watching.md` and `docs/decisions.md`.

Out of scope held. The merge's diff (`git diff cf1f6900^1 cf1f6900`) does not touch:
- `src/factory/domain/evaluation.py` (`CLAIM_EVENTS`);
- `src/factory/application/tick.py` (the tick still evaluates with `Watcher(self._boundaries, self._instance)`, `tick.py:110`);
- `src/factory/application/recovery.py`;
- `tests/application/test_watcher_move_rule.py`.

`claim_status` and `required_claim_status` are unchanged. The board's rows are unchanged, and no story or smoke test made a paid call. Decision 6's flaky test got no story, as decided.

The "Done when" is met:
- S0001 is merged;
- the human's change 1 is in `CLAUDE.md`, *Tests*, right after the bullet on time limits;
- `make check` is green on this branch (`check: green`, coverage 99.06 %).

The goal is reached as a whole, not only for the story's case. The feature smoke test shows both the story and the acceptance case that the night of 2026-10-19 reported.

## 2 Feature smoke test

What the operator does: reads `factory-watch` while the container's own tick runs a stage, a story under a 60-minute lease and an acceptance under a 100-minute one (the acceptance reviewer's lease). Beside each look, the script shows what the tick's own evaluation gives at the same moment. The script runs against the real entry points: `factory.entry.watch.main` with given boundaries and instance, `AcceptanceService.open` to open the acceptance as the factory does, and `Watcher(boundaries, "self")` as `Tick` calls it. The remote is a real local bare repository with clones, the hosting service is the fake, and nothing is paid.

Command, from the root of the checkout:

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; uv run -q python "$TMPDIR/f26-scripts/feature_smoke.py" "$d"; echo "exit $?"   # the script below, saved in the run's own temporary folder
```

The script:

```python
"""F0026 end to end: the operator reads factory-watch while the instance's own tick runs a stage."""
import io
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


def look(label: str) -> None:
    boundaries.git.fetch()
    out, err = io.StringIO(), io.StringIO()
    status = main([], boundaries=boundaries, instance="self", out=out, err=err)
    definition = PipelineLoader(boundaries).load(boundaries.git.resolve(PIPELINE_REF))
    tick = render_event(Watcher(boundaries, "self").evaluate(definition))  # what Tick evaluates
    lines = out.getvalue().splitlines()
    rows = [f"{line.split()[0]} {next(c for c in line.split() if c.startswith('claim='))}" for line in lines[2:] if line.startswith(("F0001-S0001", "F0002-A0001"))]
    print(f"{label:<31} watch: {status} {lines[0]!r:<47} err={err.getvalue()!r} {rows} | tick: {tick!r}")


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

# 1. A story: the instance's own tick runs its doing stage under a 60-minute lease.
for minutes in (1, 59, 61):
    push("work-item/F0001-S0001", STORY, WorkItemState(stage="doing", claim=claim("self", "doing", minutes)), "# First story\n")
    look(f"story, own claim, {minutes}/60 min")
# 2. Another instance's claim keeps its judgement.
for minutes in (1, 61):
    push("work-item/F0001-S0001", STORY, WorkItemState(stage="doing", claim=claim("other", "doing", minutes)), "# First story\n")
    look(f"story, other's claim, {minutes}/60 min")
# 3. The story leaves; the feature F0002 is complete and due; its acceptance runs under a 100-minute lease.
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
    look(f"acceptance, own, {minutes}/100 min")
```

Output:

```
story, own claim, 1/60 min      watch: 0 'event: idle:-  F0001-S0001 is held by self'    err='' ['F0001-S0001 claim=self'] | tick: 'event: crash:F0001-S0001'
story, own claim, 59/60 min     watch: 0 'event: idle:-  F0001-S0001 is held by self'    err='' ['F0001-S0001 claim=self'] | tick: 'event: crash:F0001-S0001'
story, own claim, 61/60 min     watch: 0 'event: crash:F0001-S0001'                      err='' ['F0001-S0001 claim=self'] | tick: 'event: crash:F0001-S0001'
story, other's claim, 1/60 min  watch: 0 'event: idle:-  F0001-S0001 is held by other'   err='' ['F0001-S0001 claim=other'] | tick: 'event: idle:-  F0001-S0001 is held by other'
story, other's claim, 61/60 min watch: 0 'event: expired:F0001-S0001'                    err='' ['F0001-S0001 claim=other'] | tick: 'event: expired:F0001-S0001'
F0002 complete, nothing claimed watch: 0 'event: acceptance_due:F0002  acceptance of F0002 is due' err='' [] | tick: 'event: acceptance_due:F0002  acceptance of F0002 is due'
acceptance, own, 2/100 min      watch: 0 'event: idle:-  F0002-A0001 is held by self'    err='' ['F0002-A0001 claim=self'] | tick: 'event: crash:F0002-A0001'
acceptance, own, 99/100 min     watch: 0 'event: idle:-  F0002-A0001 is held by self'    err='' ['F0002-A0001 claim=self'] | tick: 'event: crash:F0002-A0001'
acceptance, own, 100/100 min    watch: 0 'event: crash:F0002-A0001'                      err='' ['F0002-A0001 claim=self'] | tick: 'event: crash:F0002-A0001'
acceptance, own, 130/100 min    watch: 0 'event: crash:F0002-A0001'                      err='' ['F0002-A0001 claim=self'] | tick: 'event: crash:F0002-A0001'
exit 0
```

**Green.** Within its lease, an own claim reads as held in `factory-watch` and as a crash in the tick's evaluation, for a story and for an acceptance. From the lease's end on, both read it as a crash. Another instance's claim is judged the same by both. The board row names the claim in every case.

Two earlier tries of the script failed in my own setup, not in the code under test:
- A handed-over story without a pull request raised `ask` ahead of the acceptance.
- The helper branched the opened acceptance from `main`.

The script above is the corrected one.

## 3 Mutation score

`make mutants` (feature taken from the branch; it mutates `claims.py`, `watcher.py`, `lease.py` and `watch.py`) ran to its end within its 540 s, without the `stopped after` line. It then listed the survivors, together with older results that `mutants/` keeps for modules outside this feature. Counted for the four modules with `uv run mutmut results --all true`:

```
    138 application.claims killed
      7 application.claims survived
     90 application.watcher killed
      3 application.watcher survived
     38 domain.lease killed
     43 entry.watch killed
     17 entry.watch survived
```

**309 of 336 killed (92 %).** Every mutant of the code the feature added was killed: `observed_claim_status`, `observed_status`, the `observer` keyword and the choice of the status function (78 killed in `observed_*` and `Watcher.__init__`/`evaluate`). `lease.py` has no survivor. The 27 survivors all lie in code older than the feature, in the modules it touched, and fall into four groups:

1. **`factory.entry.watch.main` is never run through to the watch** (14 survivors, `x_main__mutmut_4` to `_26`). Examples: `out_stream = None`; `sys.stdout if (out is None) or True else out`; `if boundaries is not None or instance is None:`; `instance = None` after the settings; `run_watch(boundaries, instance, out_stream, None)`. The tests call `main` only for an option or a settings refusal. The one test that would reach `run_watch` through the environment, `tests/entry/test_watch_settings.py::test_a_valid_environment_gets_past_the_settings_to_the_fixed_checkout`, skips when `/work/checkout/.git` exists, which is every factory run; that is also why `watch.py` lines 82-83 and 87 are uncovered. The missing criteria: `main` with given boundaries and instance writes the watch to the given streams, or to `sys.stdout`/`sys.stderr` when none are given, and uses the settings' instance when it takes the environment. Proposed as **S0002**.
2. **The "does not resolve" error's text** (4 survivors: `x_run_watch__mutmut_4`/`_5`, `Watcher._main_commit__mutmut_4`/`_5`). Each replaces either the command or the output tail of `GitError` with `None`. The tests check only the type (`test_run_watch_without_origin_main_raises_git_error`), or `match="origin/main"`, which either half still satisfies. The text is what the operator reads. It is folded into **S0002**.
3. **`ClaimService`'s refusals have no pinned text** (7 survivors: `__init__` 3, `_check_preconditions` 2/8/11, `_lease_duration_of` 2/6, `_work_item_id` 5, each `ValueError(f"...")` → `ValueError(None)`). `tests/application/test_claims.py` matches `r".+"` or `r".*"`, and `"None"` passes both. The message reaches the factory log when a tick's iteration fails. Proposed as **S0003**, with new tests only.
4. **An equivalent mutant** (1): `Watcher.evaluate__mutmut_40`, `ClaimService(boundaries, self._instance, None)`. `status` and `observed_status` never read the definition (it serves `claim`'s lease only), so no test can notice. No story.

## 4 What the stories noticed

- **Coder (entries 7, 15):** `src/factory/entry/watch.py` lines 82-83 and 87 were uncovered before the story and still are. The cause is the skipped settings test of check 3. This goes into **S0002**.
- **Coder (entry 7):** the coder did not run the second smoke-test block. The smoke tester ran both blocks (entry 21), and so does check 2 here. Closed.
- **Tester (entry 13) and coder (entry 15):** other acceptance test modules keep their own `definition` fixture and their own push of the complete feature. Counted now:
  - 11 modules under `tests/application/` define a `definition` fixture whose body and docstring are word for word those of the one `tests/conftest.py:187` now holds, and which they shadow: `test_acceptance_closed.py`, `test_acceptance_reading.py`, `test_task_acceptance.py`, `test_stage_run_acceptance.py`, `test_acceptance_repeated.py`, `test_acceptance_snapshots.py`, `test_acceptance_hand_over.py`, `test_acceptance_service.py`, `test_acceptance_due_handler.py` (its docstring differs slightly), `test_acceptance_merged.py` and `test_acceptance_merged_before_approval.py`.
  - The complete-feature pushes vary: other titles, other story counts, a `feature_text` parameter. So they are not one copy of `watch_support.push_complete` and are left out.
  - Proposed as **S0004**.
- **Reviewer (entry 17), documenter (entry 19):** the `_agents` fixture of `tests/entry/test_watch_own_claim.py:27` is a copy. There are now six identical `_agents` copies (`tests/entry/test_watch.py`, `test_watch_acceptance.py`, `test_watch_own_claim.py`, `tests/application/test_tick.py`, `test_tick_disk.py`, `test_tick_stop_records.py`). There is also a seventh copy in the shape the move would take, `installed_agents` with `pytestmark`, in `tests/application/test_pipeline_loading_agents.py:25`. This goes into **S0004**.
- **Reviewer (entry 17):** the `INSTANCE`/`OTHER_INSTANCE` constants repeat in the three new files, and `_claim` in `tests/domain/test_lease_observed.py` sits beside `watch_support.aged_claim`. These are one-line constants: 54 module-level `INSTANCE`/`OTHER_INSTANCE` definitions exist under `tests/`, which is the project's habit. The domain test's `_claim` takes a fixed `NOW` rather than a clock, as a pure domain test should. Left as they are; no story.
- **Documenter (entry 19):** the opening paragraph of `docs/operator-guide.md` is a running list of the built parts, and it names `factory-watch` already. No change is needed for this feature.
- **Coder (entries 7, 15):** `duplicates: 5 new, 33 known, 3 gone`. The reviewer found none of the five in a file the story changed. Not this feature's.
- **Seen here:** the constant `f"{REMOTE}/{MAIN_BRANCH}"` is defined under `_MAIN_REF` or `PIPELINE_REF` in seven application modules (`watcher.py:17`, `pipeline_loading.py:14`, `acceptance_reading.py:40`, `acceptance.py:67`, `preflight.py:57`, `tick.py:34`, `work_items.py:36`). It is older than this feature and outside its scope. I name it for the human; I propose no story.

## 5 The documentation as a whole

None of weight. Read from the top as a newcomer, the five places the story changed agree with each other and with the behaviour the smoke test shows:
- `docs/operator-guide.md` has the opening sentence of *Looking at the remote: `factory-watch`* (line 1046), the new bullet (line 1062) and the first bullet of *Claims, leases and the clock* (line 1363);
- `docs/project-guide/stages.md` has *Observed status* (line 23) and the lease functions (line 29);
- `docs/project-guide/watching.md` has *The evaluation* (line 9) and *The watcher's command line* (line 68);
- `docs/decisions.md` has its last entry (line 736).

*A restart during a stage* (line 1312) and *An expired lease* (line 1357, "Your own claim is never an expiry") speak of the tick, and stay true. One cross-reference is missing, but nothing contradicts. The provider-limit section's paragraph *The claim stays held while waiting* (around line 239) says that only another instance would act on the age. It does not say that `factory-watch` shows the wait as a crash; the `factory-watch` section says so, and the decision log does too. No example the feature touched has gone stale. `README.md` needs nothing from this feature.

## 6 Decisions taken for the human

From `feature.md`, to accept or revisit:
1. The cause of the false crash is the second process (`factory-watch` running the tick's evaluation as the same instance), not the acceptance.
2. From outside, an own claim is judged by its lease (`held` within it, `own` at and past it). The tick keeps `claim_status`, and the choice is the `Watcher` keyword `observer`.
3. A real crash shows at the latest when its lease runs out. A live stage that uses every limit can show as a crash for about a minute past its lease. A sign of life of the tick, and an own claim always shown as `held`, were rejected.
4. A stage waiting out a provider limit past its lease shows as a crash in `factory-watch`. This is accepted, and the operator guide says so.
5. The leave to change `tests/test_claim_ownership.py` (`LEASE_FUNCTIONS` gains `observed_claim_status`).
6. The flaky `test_every_factory_move_is_no_reject[tests-doing]` gets no fix and no leave. `CLAUDE.md`'s new bullet makes its next failure leave its text. No story recorded such a failure during F0026.
7. The folder's name.
8. The human's answers of 2026-10-19.

Defaults the story's agents took:
- **Coder (entry 11):** the module docstring of `src/factory/entry/watch.py` is "The watcher's command line: an evaluation's event seen from outside the tick, and the board." This differs from the reviewer's sentence and from the Interface's wording, because the reviewer's sentence is 117 characters and ruff refuses lines over 100. The reviewer accepted it in round 1.
- **Intake (entry 3):** the wording of that docstring got no test, as documentation.
- **Documenter (entry 19):** added two sentences beyond criterion 8, both from decision 3: the margin of "up to about a minute past its lease", and "the board's rows are the same either way".
- **Tester (entry 13):** put the shared helpers in a new root module, `tests/watch_support.py`, and renamed `BRANCH` to `ACCEPTANCE_BRANCH` in the moved constants.

Earlier tests changed, each with its leave, as reviewer entry 17 names them:
- `tests/test_claim_ownership.py`: the feature's decision 5.
- `tests/application/test_watcher_acceptance.py`: the standing leave to move a shared test helper (`definition`, `_push_complete`, `_open`, `_branch_state`, `_push_state` and the constants).
- `tests/entry/test_watch_acceptance.py`: the standing leave (its `todo` fixture calls `push_complete`).
- `tests/conftest.py`: the standing leave (gains `definition`).

No earlier test was changed without a leave.

## 7 The slow checks

Beyond `make check` and `make mutants`, the project offers no slow check today: no image scan and no SBOM target in the `Makefile`.

The disk line shows no growth. `/work` has 0.5 GB used, and `/state` and `/tmp` 0.0 GB, both at this acceptance and at the previous record (the story's start), with 978.8 GB free each time.

The JUnit report of my `make check` (`.reports/junit.xml`) holds 5689 tests, 432.0 s summed over the workers. The slowest are the time-limit tests of the runtimes:
- `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` and `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`, 5.01 s each;
- four tests at about 3.0 s.

None of them is this feature's. The feature's 27 new test cases take 0.38 s at most (`test_watcher_observer::test_an_acceptance_claim_is_judged_from_outside_by_its_lease[observer-at-lease]`), 2.86 s together.

## 8 Cost

The stories cost 10 runs, 12.2 min, 91 turns, 317345 tokens in (1751757 more from cache), 39462 out, **$3.33**. There is one story, S0001, with one rework round.

Round 0 (intake, tests, doing, review) cost $1.46. Round 1 cost $1.39: coder $0.25, tester $0.58, coder $0.15, reviewer $0.41. Round 1 was caused by the reviewer's four findings on test helpers that the new tests had copied from `test_watcher_acceptance.py` (entry 9). The Interface had said "as `tests/application/test_watcher_acceptance.py` does" without naming the shared helper, so the tester copied. The two tester runs ($0.60 and $0.58) are the largest items. Docs and smoke test cost $0.48 together.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

- `F0026-S0002-factory-watch-s-main-hands-its-streams-and-instance-to-the-watch.md`: pins `factory.entry.watch.main` through to the watch (its streams, its given or settings' instance, its error stream) and the exact text of the "origin/main does not resolve" error in `run_watch` and `Watcher`. Tests only; kills the 14 + 4 survivors of groups 1 and 2.
- `F0026-S0003-the-claim-service-s-refusals-name-their-cause.md`: pins the text of `ClaimService`'s seven refusals in a new test module. Tests only; kills the 7 survivors of group 3.
- `F0026-S0004-the-acceptance-and-watch-tests-use-the-shared-definition-and-agents-fixtures.md`: removes the 11 shadowing copies of the `definition` fixture, and moves the agent-installing fixture (7 copies) to `tests/conftest.py`, under the standing leave. Tests only.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 3 stories proposed; make mutants 309/336
   1 Scope: none. S0001 built every scope bullet. The merge's diff leaves the out-of-scope parts untouched: evaluation, tick, recovery, `claim_status` and `test_watcher_move_rule.py`. The human's change 1 is in `CLAUDE.md`, and `make check` is green.
   2 Feature smoke test: green. Through `factory.entry.watch.main` and the tick's `Watcher`, an own claim reads `idle … is held by self` within its lease and `crash` at and past it, for a story (60-min lease) and an acceptance opened by `AcceptanceService` (100-min lease). The tick reads `crash` at any age, and another instance's claim is unchanged.
   3 Mutation score: 309/336 killed, and every mutant of the feature's new code is killed. Survivors in older code: 14 in `watch.main` (no test runs it through to the watch, because the settings test skips on the fixed checkout), 4 in the "origin/main does not resolve" `GitError` text, 7 in the text of `ClaimService`'s refusals, and 1 equivalent mutant.
   4 What the stories noticed: 11 shadowing copies of the `definition` fixture and 7 copies of the agent-installing fixture (proposed as S0004); `watch.py` lines 82-83 and 87 uncovered (S0002); the repeated `INSTANCE` constants and the domain test's `_claim` left as the project's habit; `_MAIN_REF` defined in 7 application modules, named for the human with no story.
   5 Documentation: none of weight. The operator guide, both project-guide files and the decision log agree with each other and with the behaviour. The provider-limit section only lacks a cross-reference to `factory-watch`'s crash display, which the `factory-watch` section itself gives.
   6 Decisions taken for the human: feature decisions 1–8, plus the coder's shorter docstring (line length), the documenter's two sentences from decision 3 and the tester's `tests/watch_support.py`. Earlier tests changed: `test_claim_ownership.py` (decision 5), and `test_watcher_acceptance.py`, `test_watch_acceptance.py` and `conftest.py` (the standing leave). None was changed without a leave.
   7 Slow checks: the project has none beyond `make check` and `make mutants`. Disk is unchanged since the story's start (0.5 GB used on /work). The slowest tests are the 5.01 s runtime time-limit tests, none of them this feature's; its 27 new test cases take 2.86 s together.
   8 Cost: $3.33 over 10 runs and 12.2 min for the one story. Round 1 ($1.39) was spent on moving test helpers the new tests had copied, and the two tester runs ($0.60 and $0.58) are the largest items. No questions were asked and no time was spent waiting.
