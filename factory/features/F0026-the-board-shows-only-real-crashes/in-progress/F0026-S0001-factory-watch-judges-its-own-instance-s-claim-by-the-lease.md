---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 262
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T12:31:07.006545Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T12:31:07.012649Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T12:31:31.557576Z'
  stage: intake
  run: 84ef30c790f64bcd8e0f7badc61a6271
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T12:31:51.835974Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T12:36:48.602420Z'
  stage: tests
  run: 123b6c61b7364611891103a5ea96d9d2
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T12:37:09.492769Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T12:39:39.164347Z'
  stage: doing
  run: 04dd0edb36d04a29a8ee9d14e215e01e
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T12:39:59.673720Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T12:40:46.296997Z'
  stage: review
  run: bb1159f652174673b6a4ca6eadb76441
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T12:41:12.790764Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-19T12:42:47.966695Z'
  stage: doing
  run: 6a248fe4e04746e994954f9b7e6db0b0
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T12:43:08.557633Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-19T12:46:06.226271Z'
  stage: tests
  run: d4ec544a69694771be47df22e7d9d714
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T12:46:26.511546Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-19T12:48:33.373150Z'
  stage: doing
  run: 7419d7b79f3e4f2a9ae79ff5504421aa
---

# factory-watch judges its own instance's claim by the lease

## Description

`factory-watch` shows `event: crash:<work item>` for every stage its own instance is running, story or acceptance, though nothing crashed. It evaluates with the tick's `Watcher` as the container's instance, an own claim is `own` whatever its age, and `own` raises `crash`. That is right for the tick, which never looks while its own stage runs, and wrong for `factory-watch`, a second process that looks while the tick runs a stage. This story lets a look from outside judge an own claim by the claim's lease, as it judges another instance's: within the lease it is `held` and the event is `idle` with the detail `<work item> is held by <instance>`; at and past the lease it is `own`, and the event stays `crash`. `factory-watch` looks from outside; the tick does not, and its events, its recovery and every other claim's judgement stay as they are. The board's rows do not change. Nothing is left to a later story.

## Interface

`factory.domain.lease` (`domain`):

```python
def observed_claim_status(claim: Claim | None, *, instance: str, now: datetime) -> ClaimStatus:
    """The status of `claim` as a look from outside `instance`'s tick sees it at `now`.

    An own claim within its lease is "held", since the tick may be running its stage; at and
    past its lease it is "own". Every other claim has its `claim_status`.
    """
```

- `None` gives `"none"`.
- A claim whose `instance` is `instance` gives `"held"` while `lease_expired(claim, now)` is false (a negative age included) and `"own"` when it is true: `"held"` at 59 minutes 59 seconds of a 60-minute lease, `"own"` at 60 minutes and after.
- A claim of another instance gives what `claim_status` gives: `"held"` within its lease, `"expired"` at and past it.
- `claim_status`, `lease_expired` and `lease_age` are unchanged.

`factory.application.claims` (`application`):

```python
class ClaimService:
    def observed_status(self, state: WorkItemState) -> ClaimStatus:
        """The status of the state's claim as seen from outside this instance's tick."""
```

- `observed_claim_status(state.claim, instance=<the service's instance>, now=boundaries.clock.now())`. `status` is unchanged.

`factory.application.watcher` (`application`):

```python
class Watcher:
    def __init__(self, boundaries: Boundaries, instance: Name, *, observer: bool = False) -> None:
        """Read through `boundaries`; judge claims as `instance`, from outside if `observer`."""
```

- `evaluate` hands `evaluate(...)` the claim status `ClaimService.status` when `observer` is false (the tick: an own claim is a `crash` at any age) and `ClaimService.observed_status` when it is true. Nothing else in `evaluate` depends on `observer`.
- `factory.domain.evaluation` is unchanged: a `held` status is the `idle` event whose detail is `<work item> is held by <claim's instance>`, `own` is `crash`, `expired` is `expired`.

`factory.entry.watch` (`entry`):

- `run_watch` evaluates with `Watcher(boundaries, instance, observer=True)`; the board, the exit statuses and the error lines are unchanged.
- The module's docstring says that it shows the event of one evaluation as a look from outside the tick sees it, and the board, instead of "the event the next tick would handle".

Unchanged: `Tick` (it evaluates with `Watcher(boundaries, instance)`), `RecoveryHandler`, `required_claim_status`, `CLAIM_EVENTS`, the board, `factory-run`.

Tests (the tester writes them): `tests/domain/test_lease_observed.py`, `tests/application/test_claims_observed.py` (the `boundaries` and `clock` fixtures of `tests/conftest.py`), `tests/application/test_watcher_observer.py` (a story's branch state pushed with `human.push_file`, as `tests/application/test_watcher.py` does, and an acceptance opened with `AcceptanceService.open` on a due feature `F0002-todo` with its state pushed to its branch, as `tests/application/test_watcher_acceptance.py` does), `tests/entry/test_watch_own_claim.py` (with the `_agents` fixture of `tests/entry/test_watch.py` copied or moved under the standing leave). In every claim the tests build, `started_at` is `clock.now()` minus the age and `lease_duration` is 60.

Changed under the feature's decision 5, by the tester only, nothing else in that module: `tests/test_claim_ownership.py`, whose `LEASE_FUNCTIONS` becomes `("claim_status", "lease_expired", "lease_age", "observed_claim_status")`. Its two tests keep their names and what they check.

## Acceptance criteria

1. `observed_claim_status` (rows of one parametrized test, `instance="factory-1"`, `now` fixed, a 60-minute lease): no claim gives `"none"`; a claim of `factory-1` aged -5 minutes, 0, 59 minutes and 59 minutes 59 seconds gives `"held"`; aged 60 minutes, 60 minutes 1 second and 120 minutes gives `"own"`; a claim of `factory-2` aged 59 minutes gives `"held"` and aged 60 minutes `"expired"`.
2. `ClaimService(boundaries, "factory-1", definition)` (rows of one parametrized test, on the `clock` fixture): for a state whose claim is `factory-1`'s and aged 59 minutes, `observed_status` gives `"held"` and `status` gives `"own"`; aged 60 minutes both give `"own"`; for `factory-2`'s claim aged 59 minutes both give `"held"`, aged 60 minutes both `"expired"`; for a state without a claim both give `"none"`.
3. A story's claim (rows of one parametrized test, the story `F0001-S0001` started by the human and its branch state at stage `intake` with the claim): with `observer=True`, `factory-1`'s claim aged 59 minutes gives an event of kind `idle` with no work item and the detail `F0001-S0001 is held by factory-1`; aged 60 minutes it gives `crash` for `F0001-S0001`; `factory-2`'s claim aged 59 minutes gives `idle` with the detail `F0001-S0001 is held by factory-2`, aged 60 minutes `expired`. With `observer` left out, `factory-1`'s claim aged 0 and 59 minutes gives `crash` for `F0001-S0001`.
4. An acceptance's claim (rows of one parametrized test, the acceptance `F0002-A0001` opened on the due feature `F0002-todo` and its branch state at stage `acceptance` with a claim of `factory-1`): with `observer=True`, aged 59 minutes the event is `idle` with the detail `F0002-A0001 is held by factory-1`, aged 60 minutes it is `crash` for `F0002-A0001`; with `observer` left out, aged 59 minutes it is `crash` for `F0002-A0001`.
5. `run_watch(boundaries, "factory-1", out, err)` (rows of one parametrized test): for the story of criterion 3 with `factory-1`'s claim aged 59 minutes the first line of `out` is `event: idle:-  F0001-S0001 is held by factory-1`; aged 60 minutes it is `event: crash:F0001-S0001`; for the acceptance of criterion 4 aged 59 minutes it is `event: idle:-  F0002-A0001 is held by factory-1`. In each row the status is 0, `err` is empty, and the work item's board row names `claim=factory-1`.
6. `tests/test_claim_ownership.py` passes with `observed_claim_status` among its `LEASE_FUNCTIONS` (the change of decision 5): only `factory.application.claims` imports it.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`, *Looking at the remote: `factory-watch`*: a bullet saying that a claim of the instance `factory-watch` runs as shows as `event: idle:-  <work item> is held by <instance>` while its lease runs, because the instance may be running that stage, and as `event: crash:<work item>` once the lease has run out; that the tick itself still reruns its own claim at its first look after a restart; and that a stage waiting out a provider limit past its lease shows as a crash there, the factory log's line of the wait telling the two apart. The section's opening sentence says that it evaluates as a tick would, except that it judges its own instance's claim by the lease, since a tick never looks while its own stage runs. *Claims, leases and the clock*, the first bullet: the same in one sentence. `docs/project-guide/stages.md`, *The claim service*: `observed_status` and `observed_claim_status` beside `status`, and `observed_claim_status` among the lease functions only `factory.application.claims` reaches. `docs/project-guide/watching.md`, *The evaluation*: `Watcher`'s `observer` and which claim status it hands over; *The watcher's command line*: `run_watch` evaluates with `observer=True`. `docs/decisions.md`: an entry *factory-watch judges its own instance's claim by the lease*, dated with the story, with the reasons of the feature's decisions 1 to 4.

## Smoke test

```bash
uv run -q python - <<'EOF'
from datetime import UTC, datetime, timedelta

from factory.domain.lease import claim_status, observed_claim_status
from factory.domain.work_item import Claim

now = datetime(2026, 10, 19, 2, 16, tzinfo=UTC)
for instance, age in [("self", 0), ("self", 59), ("self", 60), ("other", 59), ("other", 60)]:
    claim = Claim(instance=instance, stage="acceptance", started_at=now - timedelta(minutes=age), lease_duration=60)
    print(instance, age, observed_claim_status(claim, instance="self", now=now), claim_status(claim, instance="self", now=now))
print(observed_claim_status(None, instance="self", now=now))
EOF
```
Expect: six lines, `self 0 held own`, `self 59 held own`, `self 60 own own`, `other 59 held held`, `other 60 expired expired`, `none`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python - "$d" <<'EOF'
import io
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.domain.settings import InstanceSettings
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState
from factory.entry.watch import run_watch
from factory.entry.wiring import build_boundaries

d = Path(sys.argv[1])
story = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
pipeline = 'contract: "1.0"\nproject_commands:\n  check: {time_limit: 10}\nroles:\n  coder: {write_paths: ["src/*"]}\nstages:\n  doing: {role: coder, next: [done], checks: [check]}\n  done: {}\n'


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args], cwd=cwd, check=True, capture_output=True)


def write(root: Path, path: str, text: str) -> None:
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(text, encoding="utf-8")


git(d, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
git(d, "clone", "-q", str(d / "remote.git"), "human")
human = d / "human"
write(human, "factory/pipeline.yml", pipeline)
write(human, "factory/features/F0001-example/feature.md", "# Example feature\n")
write(human, story, "# First story\n")
git(human, "add", "-A")
git(human, "commit", "-q", "-m", "start")
git(human, "push", "-q", "origin", "main")
write(d / "agents-home", "agents/coder.md", "---\nmodel: sonnet\ntools: [Read, Write]\nbudget_usd: 1\n---\nDo the work.\n")
git(d, "clone", "-q", str(d / "remote.git"), "checkout")
settings = InstanceSettings(repository_url="https://github.com/example/project.git", instance="self", checkout=d / "checkout", state_directory=d / "state", agent_home=d / "agents-home")
boundaries = build_boundaries(settings, "unused", hosting=FakeHostingService())
git(human, "switch", "-q", "-c", "work-item/F0001-S0001")
for minutes in (1, 61):
    claim = Claim(instance="self", stage="doing", started_at=datetime.now(UTC) - timedelta(minutes=minutes), lease_duration=60)
    document = WorkItemDocument(state=WorkItemState(stage="doing", claim=claim), body="# First story\n")
    write(human, story, FrontmatterWorkItemWriter().render(document))
    git(human, "commit", "-q", "-am", f"doing starts {minutes} minutes ago")
    git(human, "push", "-q", "origin", "work-item/F0001-S0001")
    boundaries.git.fetch()
    out, err = io.StringIO(), io.StringIO()
    status = run_watch(boundaries, "self", out, err)
    print(status, out.getvalue().splitlines()[0], repr(err.getvalue()))
EOF
```
Expect: two lines, `0 event: idle:-  F0001-S0001 is held by self ''` and `0 event: crash:F0001-S0001 ''`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: concrete and placed right. `observed_claim_status` in `factory.domain.lease`, `ClaimService.observed_status` in `factory.application.claims`, `Watcher(..., observer=False)` in `factory.application.watcher`, and `run_watch` in `factory.entry.watch`. Each has a signature and a rule for every case: None, own within and past the lease (negative age included), another instance's claim, and what stays unchanged.
   Criteria: each is testable by one parametrized test with the ages and expected values spelled out. Criterion 1 covers both sides of the lease boundary for an own claim (59m59s held, 60m own, negative age held) and for another instance's claim. Criterion 2 compares `observed_status` with `status`. Criteria 3 and 4 cover observer true and false, for stories and for acceptances. Criterion 5 covers the exact `run_watch` output line, status, empty `err` and board row. Criterion 6 covers decision 5's change to the ownership test. Criterion 8 covers the docs. The Interface's docstring wording for the `watch` module has no test of its own; I judged it documentation, which criterion 8 and the reviewer cover, not a behaviour.
   Smoke test: both blocks are runnable as written, using the project's own adapters and fakes with no network or paid call. Each Expect line states exact lines that can be checked against the output.
   Architecture: the lease rule sits in domain and is pure. The service wraps it in application and `Watcher` chooses the status function. Only `entry` changes the wiring, and the layer order is kept. The only test change to another story's module is `tests/test_claim_ownership.py`, and the human gave it in decision 5.
   Scope: it matches feature.md's Scope list. The tick, `RecoveryHandler`, `CLAIM_EVENTS`, the board and `claim_status` stay unchanged, as Out of scope requires. Decision 4's precondition (F0020-S0007 archived) is the human's to keep, and they started this story.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 6. Each criterion is one parametrized test, and every claim is aged from `clock.now()` (a fixed `NOW` in the domain test) with `lease_duration` 60.
   criterion 1: tests/domain/test_lease_observed.py::test_an_observed_claim_is_judged_by_its_lease
   criterion 2: tests/application/test_claims_observed.py::test_the_observed_status_judges_an_own_claim_by_its_lease
   criterion 3: tests/application/test_watcher_observer.py::test_a_story_claim_is_judged_from_outside_by_its_lease
   criterion 4: tests/application/test_watcher_observer.py::test_an_acceptance_claim_is_judged_from_outside_by_its_lease
   criterion 5: tests/entry/test_watch_own_claim.py::test_the_watch_judges_its_own_instances_claim_by_the_lease
   criterion 6: tests/test_claim_ownership.py::test_only_the_claim_service_uses_the_lease_functions (its `LEASE_FUNCTIONS` now ends with "observed_claim_status"; nothing else in the module changed, under the feature's decision 5)
   criteria 7 and 8: no test (make check, docs).

   Files created: tests/domain/test_lease_observed.py, tests/application/test_claims_observed.py, tests/application/test_watcher_observer.py, tests/entry/test_watch_own_claim.py. Earlier test file changed: tests/test_claim_ownership.py (decision 5). I copied the `_agents` fixture of tests/entry/test_watch.py into test_watch_own_claim.py, as the Interface allows, and left test_watch.py unchanged.

   How the tests are built: in the watcher test rows, "observer left out" means `Watcher(boundaries, INSTANCE)` with no keyword at all. The acceptance rows open `F0002` with `AcceptanceService.open` on a complete `F0002-todo`. They then push the branch state at stage `acceptance` with the claim, through `human.push_file`.

   `make test` (one run) is red, as intended:
   - tests/domain/test_lease_observed.py does not import, because `observed_claim_status` is not in `factory.domain.lease` yet.
   - The observer rows of the watcher tests fail, because `Watcher` does not take `observer` yet.
   - The claim-service and watch tests fail because `observed_status` does not exist and `run_watch` still shows an own claim within its lease as `crash`.
   - The ownership test fails because `observed_claim_status` is not imported by `factory.application.claims` yet.

   The rows that pin unchanged behaviour (the tick's own-claim crash, another instance's claim, the watch's crash at the lease) may already pass. `make lint` is green; I ran `ruff format` on the new files. I skipped the type check, as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/domain/test_lease_observed.py - ImportError while importing test ...
6. factory: started doing as self.
7. coder: `factory-watch` now judges its own instance's claim by the claim's lease. `make check` is green, and the first smoke-test block prints the six lines the story expects.

   What I built:
   - `src/factory/domain/lease.py`: `observed_claim_status`. An own claim whose lease has not run out gives "held". Every other case goes to `claim_status`, so the none, other-instance and expired-own cases are judged in one place only.
   - `src/factory/application/claims.py`: `ClaimService.observed_status`, next to `status`, which is unchanged.
   - `src/factory/application/watcher.py`: `Watcher(..., *, observer=False)`. `evaluate` passes `claims.observed_status` when `observer` is true and `claims.status` when it is false. A short comment says why: a tick never looks while its own stage runs.
   - `src/factory/entry/watch.py`: `run_watch` evaluates with `observer=True`. The module docstring now says it shows the event of one evaluation as a look from outside the tick sees it, and the board.

   Main choice: `observed_claim_status` handles only the one case that differs and hands the rest to `claim_status`. I rejected a function that repeats every branch, because it would be a second copy of the none, held and expired rules.

   Refactor: I read my diff and found nothing to change.

   Noticed but not touched:
   - The docs for criterion 8 (operator guide, project guide, decision log) are the documenter's.
   - `src/factory/entry/watch.py` lines 85-86 and 90 were already uncovered; the coverage gate still passes.
   - I did not run the second smoke-test block (the full git round trip). Criterion 5's tests cover the same path.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: Review of `git diff main...HEAD -- . ':!factory'` against the work item. Groups 1 to 3 hold:
   - Acceptance criteria: criteria 1 to 6 each have a parametrized test that checks what its criterion says, the lease boundary is tested on both sides, and the coder's journal entry says `make check` is green.
   - Architecture: the rule is pure and sits in `factory.domain.lease`, `ClaimService` wraps it, `Watcher` picks the status function, and `entry` sets `observer=True`. The layer order is kept.
   - Security: no suppression markers, no secrets, no built commands.

   Group 4 (quality) fails:

   1. `tests/application/test_watcher_observer.py:109` `_push_complete_todo` and `tests/entry/test_watch_own_claim.py:53-55` are copies of `_push_complete` in `tests/application/test_watcher_acceptance.py:35` (and of the `todo` fixture in `tests/entry/test_watch_acceptance.py:24`). Fix: the tester moves the push of the complete `F0002-todo` to one shared place under `tests/` (`tests/conftest.py` as a fixture, or a root module) under the standing leave, and the new tests use it.
   2. `tests/application/test_watcher_observer.py:115` `_push_acceptance_claim` and `tests/entry/test_watch_own_claim.py:52` `_push_acceptance` hold the same open/read/claim/push sequence twice, and that sequence copies `_open`, `_branch_state` and `_push_state` of `tests/application/test_watcher_acceptance.py:42-63`. Fix: one shared helper under `tests/` that opens `F0002` and pushes its branch state with a given claim, used by both new files.
   3. `tests/application/test_watcher_observer.py:39` and `tests/entry/test_watch_own_claim.py:36`: `_claim` is written twice in the diff, and so are the `STORY`, `STORY_PATH`, `BACKLOG_PATH`, `ACCEPTANCE`, `REPORT` and `TODO` constants. Fix: one shared helper and one set of constants that both files import.
   4. `tests/application/test_watcher_observer.py:33`: the `definition` fixture is a word-for-word copy, docstring included, of `tests/application/test_watcher_acceptance.py:29`. Fix: move it to `tests/conftest.py` under the standing leave and use it in both files.
   5. `src/factory/entry/watch.py:1-4`: the module docstring's body repeats its summary line ("as seen from outside the tick" / "as a look from outside the tick sees it"). Fix: one sentence, "The watcher's command line: the event of one evaluation as a look from outside the tick sees it, and the board."

   Earlier tests:
   - `tests/test_claim_ownership.py`: changed under the feature's decision 5, which the story names. Only `LEASE_FUNCTIONS` changed; both tests keep their names and what they check.
10. factory: started doing as self.
11. coder: Round 1. I fixed finding 5 myself. Findings 1 to 4 are moves of shared test helpers, which the tester makes under the standing leave in `CLAUDE.md`, so I'm handing them to the tester.

    Finding 5 (fixed): `src/factory/entry/watch.py` now has a one-line module docstring: "The watcher's command line: an evaluation's event seen from outside the tick, and the board." I did not use the reviewer's exact sentence: it is 117 characters and ruff's E501 refuses lines over 100. A `noqa` marker or a two-line summary (which the docstring rules refuse) were the other options, and I rejected both. `make check` is green.

    For the tester (standing leave). No test keeps a copy, and every earlier test keeps its name and what it checks:
    - Finding 1: move the push of the complete `F0002-todo` to one shared place under `tests/`. These copies should use it:
      - `_push_complete` in `tests/application/test_watcher_acceptance.py`
      - the `todo` fixture in `tests/entry/test_watch_acceptance.py`
      - `_push_complete_todo` in `tests/application/test_watcher_observer.py`
      - the copy in `tests/entry/test_watch_own_claim.py`
    - Finding 2: one shared helper that opens `F0002` and pushes its branch state with a given claim. It replaces:
      - `_push_acceptance_claim` in `test_watcher_observer.py`
      - `_push_acceptance` in `test_watch_own_claim.py`
      - the `_open`, `_branch_state` and `_push_state` sequence in `test_watcher_acceptance.py`, if it stays the same thing
    - Finding 3: one shared `_claim` helper and one set of constants (`STORY`, `STORY_PATH`, `BACKLOG_PATH`, `ACCEPTANCE`, `REPORT`, `TODO`), imported by `test_watcher_observer.py` and `test_watch_own_claim.py`.
    - Finding 4: move the `definition` fixture of `tests/application/test_watcher_acceptance.py` to `tests/conftest.py`, and use it there and in `test_watcher_observer.py`.

    Refactor: I read my diff again and found nothing else to change.

    Not touched: the docs for criterion 8 are the documenter's.
12. factory: started tests as self.
13. tester: Moved the shared test helpers that review findings 1 to 4 name, as coder entry 11 asked, under the standing leave in `CLAUDE.md`. Every earlier test keeps its name and still checks the same thing. No test now holds a copy of these helpers.

    New file: `tests/watch_support.py`, one shared place at the root of `tests/`. It holds:
    - The constants `FEATURES`, `STORY`, `STORY_BRANCH`, `STORY_FEATURE`, `BACKLOG_PATH`, `STORY_PATH`, `ACCEPTANCE`, `ACCEPTANCE_BRANCH`, `TODO` and `REPORT` (finding 3).
    - `aged_claim(clock, instance, stage, age)` (finding 3).
    - `push_story_claim`, which replaces the story push that the two new files each held.
    - `push_complete(human, directory="F0002-todo")` (finding 1).
    - `open_acceptance`, `acceptance_branch_state`, `push_acceptance_state`, and `push_acceptance_claim`, which is built from those three (finding 2).

    `tests/conftest.py`: the `definition` fixture now lives here, docstring included (finding 4). Test modules that define their own `definition` fixture still shadow it; I left them unchanged, because the findings do not name them.

    Earlier test files changed under the standing leave:
    - `tests/application/test_watcher_acceptance.py`: its `definition` fixture, `_push_complete`, `_open`, `_branch_state`, `_push_state` and the constants `FEATURES`, `ACCEPTANCE`, `BRANCH`, `TODO` and `REPORT` are removed. It now imports the shared ones; `BRANCH` became `ACCEPTANCE_BRANCH`.
    - `tests/entry/test_watch_acceptance.py`: the `todo` fixture keeps its name and docstring and now calls `push_complete(human)`. Its `TODO` constant is removed.

    This story's own tests:
    - `tests/application/test_watcher_observer.py` and `tests/entry/test_watch_own_claim.py` now use the shared helpers and the `definition` fixture from conftest. `test_watch_own_claim.py` takes `definition` as a new parameter.
    - Criterion mapping is unchanged:
      - criterion 3: `tests/application/test_watcher_observer.py::test_a_story_claim_is_judged_from_outside_by_its_lease`
      - criterion 4: `tests/application/test_watcher_observer.py::test_an_acceptance_claim_is_judged_from_outside_by_its_lease`
      - criterion 5: `tests/entry/test_watch_own_claim.py::test_the_watch_judges_its_own_instances_claim_by_the_lease`
      - criteria 1, 2 and 6 keep their tests from entry 5.

    Not done: the copied `definition` fixture and push of the complete feature in other acceptance test modules, such as `test_acceptance_service.py` and `test_acceptance_reading.py`. Neither review nor coder named them.

    Checks:
    - `make lint` is green.
    - I ran `make test` once: test: green, total coverage 99.06 %. The test runner could import every module.
    - I did not run the type check, as the stage says; the factory's `make check` covers it.

    `lint`: lint: green (0.0 s)
    `test`: test: green (46.5 s)
14. factory: started doing as self.
15. coder: Round 1, after the tester's move (entry 13). I made no code changes in this run. All five review findings are now dealt with:
    - Findings 1 to 4: the tester moved the shared test helpers to `tests/watch_support.py` and the `definition` fixture to `tests/conftest.py`.
    - Finding 5: I fixed it in entry 11. `src/factory/entry/watch.py` now has a one-line module docstring.

    I ran `make check` against the working tree with the tester's move in it, and it is green.

    What the story built:
    - `src/factory/domain/lease.py`: `observed_claim_status`.
    - `src/factory/application/claims.py`: `ClaimService.observed_status`.
    - `src/factory/application/watcher.py`: `Watcher(..., *, observer=False)`, which chooses `observed_status` or `status`.
    - `src/factory/entry/watch.py`: `run_watch` evaluates with `observer=True`, and its docstring is the one-line version.

    Main choice: `observed_claim_status` handles only the case that differs, an own claim still within its lease, and passes everything else to `claim_status`. I rejected writing all the branches out again, because that would make a second copy of the none, held and expired rules.

    Refactor: I read the `src` diff again and found nothing to change.

    Description: no journal entry changed what the task means, so it is unchanged.

    Noticed, not touched:
    - Entry 13 says other acceptance test modules still hold their own copies of `definition` and of the complete-feature push, for example `test_acceptance_service.py` and `test_acceptance_reading.py`. Those are for the tester, and no finding names them.
    - The criterion 8 docs are the documenter's.
    - `src/factory/entry/watch.py` lines 82-83 and 87 were uncovered before this story and still are; coverage is 99.06 %.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
