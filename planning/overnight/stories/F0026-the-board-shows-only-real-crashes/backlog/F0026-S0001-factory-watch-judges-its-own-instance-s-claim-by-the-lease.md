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
