---
stage: review
pr: 53
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# One service for claim, expiry and recognition

## Assignment (as of log entry 1)

Finish the claim service. The lease clock becomes three pure functions in `factory.domain.lease`, and `ClaimService` gains `status` (tell an own claim, a held claim and an expired claim apart, with the clock of the boundaries) and `release` (clear the claim in a document, for the stage's result commit). The lease runs from the stage-start commit for the `lease_duration` that the claim itself carries, so a later change of the pipeline definition never shortens a running claim (R21). An own claim is recognised whatever its age, which is what lets a restart with the same instance name rerun its stage at once (R20); another instance's claim is held until its lease has run out. Two search tests make the claim service the only module that knows claims (GH1.2, an inspection). Covers GH1.2 (one service owns claim, expiry and recognition), R20, R21; keeps kept thing 13. The watcher's use of `status` (F0006) and the rerun after a crash (F0008) are not part of this story. Morning observation: none; the operator guide states that instances need a synchronised clock, because expiry compares the recorded start time with the checking instance's own clock.

## Interface

`src/factory/domain/lease.py`

```python
ClaimStatus = Literal["none", "own", "held", "expired"]

def lease_age(claim: Claim, now: datetime) -> timedelta: ...
def lease_expired(claim: Claim, now: datetime) -> bool: ...
def claim_status(claim: Claim | None, *, instance: str, now: datetime) -> ClaimStatus: ...
```

`src/factory/application/claims.py` (the module of S0001) gains two methods:

```python
class ClaimService:
    def status(self, state: WorkItemState) -> ClaimStatus: ...
    def release(self, document: WorkItemDocument) -> WorkItemDocument: ...
```

`now` is an aware datetime in UTC; `Claim`, `WorkItemState` and `WorkItemDocument` are the interface sheet's.

Rules:

- `lease_age` is `now - claim.started_at`; it is negative when `now` is before the start (clock skew).
- `lease_expired` is true exactly when `lease_age(claim, now) >= timedelta(minutes=claim.lease_duration)`. It uses the claim's own `lease_duration`. An age below zero is not expired.
- `claim_status`: `None` gives `"none"`; a claim whose `instance` equals `instance` gives `"own"` without consulting `now`, however old it is; any other claim gives `"expired"` when `lease_expired` is true, else `"held"`.
- `factory.domain.lease` reads no clock: `now` is always passed in.
- `ClaimService.status(state)` is `claim_status(state.claim, instance=<the service's instance>, now=boundaries.clock.now())`. It does not look at the definition's `lease_duration`.
- `ClaimService.release(document)` returns the document with `state.claim` set to `None`; the journal, the other state fields and the body are not changed and no entry is appended. A document without a claim comes back equal. A document whose `state` is `None` raises `ValueError`.
- Search tests (GH1.2). They parse every `.py` file under `src/factory` with `ast`, through `tests/source_search.py` (`modules` and `imported_modules`), which they import and do not change. First: only `factory.application.claims` imports `claim_status`, `lease_expired` or `lease_age` from `factory.domain.lease` (`imported_modules` of its tree holds `factory.domain.lease.<name>`), no other module reaches one of the three as an attribute of `factory.domain.lease` (an `ast.Attribute` with that attribute name whose value is the name `lease` or the dotted name `factory.domain.lease`), and the test fails when `factory.application.claims` imports none of the three. A parameter or variable that happens to be called `claim_status` is not a finding. Second: `Claim` is called as a constructor only in `factory/application/claims.py`.

Tests: `tests/domain/test_lease.py`, `tests/application/test_claims.py` (the same module as S0001, with the shared fixtures; the clock is the `clock` fixture, advanced with `advance`), `tests/test_claim_ownership.py` for the search tests, which use `source_search.modules` and `source_search.imported_modules`.

## Acceptance criteria

1. `lease_age` returns `now - claim.started_at`: 45 minutes for a `now` 45 minutes after the start, and a negative timedelta for a `now` 5 minutes before it.
2. `lease_expired` with a `lease_duration` of 60: false for an age of 59 minutes and 59 seconds, true for exactly 60 minutes, true for 60 minutes and 1 second.
3. `lease_expired` is false for a negative age, however short the `lease_duration`.
4. `lease_expired` uses the claim's own `lease_duration`: the same age of 45 minutes is expired for a claim with 30 and not expired for a claim with 90.
5. `claim_status(None, instance=..., now=...)` is `"none"`.
6. `claim_status` is `"own"` for a claim of the same instance, for a `now` before the start, within the lease and long after the lease has run out.
7. `claim_status` for another instance's claim is `"held"` at 59 minutes and 59 seconds of a 60-minute lease, and `"expired"` at exactly 60 minutes and after it.
8. The source of `factory.domain.lease` contains no call to `now`, `utcnow`, `today` or `time` (it reads no clock).
9. `ClaimService.status` follows the boundaries' clock: for a state carrying a claim of the service's own instance it is `"own"`; for the claim of another instance it is `"held"` after 59 minutes of a 60-minute lease and `"expired"` after 60 minutes, with the `clock` fixture advanced between the calls; for a state without a claim it is `"none"`.
10. `ClaimService.status` judges by the claim's own `lease_duration`: a claim of the stage `intake` made with 60 minutes by another instance reads `"held"` after 30 minutes even when the service's definition sets the `intake` role's `lease_duration` and `time_limit` to 5 (the stage `intake` has no checks, so the definition is valid).
11. `ClaimService.release` returns the document with `state.claim` set to `None`, and every other state field, the journal records and the body equal to the given document's.
12. `ClaimService.release` on a document without a claim returns an equal document.
13. `ClaimService.release` on a document whose `state` is `None` raises `ValueError`.
14. The first search test finds that `factory.application.claims` imports `claim_status`, `lease_expired` or `lease_age` from `factory.domain.lease`, and that no other module under `src/factory` imports one of the three from it or reaches one as an attribute of `factory.domain.lease`.
15. The second search test finds `Claim(...)` called only in `factory/application/claims.py`.
16. make check stays green.
17. docs: `docs/operator-guide.md` explains `lease_duration` per role (default 60 minutes), that an instance's own claim is rerun at once and another instance's is waited for until the lease has run out, and that instances need a synchronised clock; `docs/project-guide.md` names `ClaimService` as the only module that builds or judges claims; `docs/decisions.md` records that expiry compares the recorded start time with the checking instance's own clock.

## Demo

```bash
uv run python - <<'EOF'
from datetime import UTC, datetime, timedelta
from factory.domain.lease import claim_status, lease_age, lease_expired
from factory.domain.work_item import Claim

start = datetime(2026, 10, 12, tzinfo=UTC)
claim = Claim(instance='factory-1', stage='coder', started_at=start, lease_duration=60)
print(lease_age(claim, start + timedelta(minutes=45)).total_seconds())
print(claim_status(claim, instance='factory-1', now=start + timedelta(minutes=90)))
print(claim_status(claim, instance='factory-2', now=start + timedelta(minutes=59)))
print(claim_status(claim, instance='factory-2', now=start + timedelta(minutes=60)))
print(claim_status(None, instance='factory-2', now=start))
print(lease_expired(claim, start - timedelta(minutes=5)))
EOF
```
Expect: six lines. `2700.0`; `own` (the same instance 30 minutes after the lease has run out); `held`; `expired`; `none`; `False` (a `now` before the start is not expired).

```bash
uv run python - <<'EOF'
import ast
from pathlib import Path

NAMES = {'claim_status', 'lease_expired', 'lease_age'}
found = []
for path in sorted(Path('src/factory').rglob('*.py')):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    if any(isinstance(node, ast.ImportFrom) and node.module == 'factory.domain.lease' and NAMES & {alias.name for alias in node.names} for node in ast.walk(tree)):
        found.append(path.as_posix())
print(found)
EOF
```
Expect: one line, `['src/factory/application/claims.py']`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted.
   - Interface: `factory.domain.lease` (`ClaimStatus`, `lease_age`, `lease_expired`, `claim_status`) and `ClaimService.status` / `release` in `factory.application.claims` have concrete signatures. The rules are stated precisely: the `>=` boundary, a negative age, "own" without consulting `now`, no look at the definition's `lease_duration`, and `ValueError` for a document with no state.
   - Criteria: each is testable by one test function. Every Interface rule has a criterion for each side. Passing side: 1, 2, 4, 5, 6, 7, 9, 11. Failing or refused side: 2 (59:59 not expired), 3 (negative age), 7 (held versus expired), 10 (the definition's value is ignored), 12 (no claim), 13 (`state` is `None`). Search tests: 14 and 15. The "variable called `claim_status` is not a finding" clause is covered through 14's finding of exactly the imports and attribute accesses. Criterion 8 covers "reads no clock".
   - Demo: both blocks are runnable. Every `Expect:` line is checkable against the printed output (six lines; one list).
   - Architecture: the pure functions sit in `domain`, the service in `application`. `Claim`, `WorkItemState` and `WorkItemDocument` are the existing DTOs. No layer is crossed.
   - Scope: the story stays inside F0004's scope (lease clock, `status`, `release`, search tests, R20 and R21). It leaves out the watcher and the rerun after a crash, which `FEATURE.md` assigns to F0006 and F0008.
3. tester: Wrote red tests for every criterion from the Interface and the acceptance criteria. No criterion needed interpreting, so there is no question for the human.
   - criterion 1: tests/domain/test_lease.py::test_lease_age_is_now_minus_the_start (45 minutes after, 5 minutes before)
   - criterion 2: tests/domain/test_lease.py::test_lease_expires_when_its_age_reaches_the_lease_duration (59m59s false, 60m true, 60m1s true)
   - criterion 3: tests/domain/test_lease.py::test_a_negative_age_is_not_expired (lease_duration 1 and 60; age -1s and -5m)
   - criterion 4: tests/domain/test_lease.py::test_lease_expired_uses_the_claims_own_lease_duration (30 expired, 90 not)
   - criterion 5: tests/domain/test_lease.py::test_no_claim_has_status_none
   - criterion 6: tests/domain/test_lease.py::test_an_own_claim_is_own_whatever_its_age (before the start, within the lease, 3 days later)
   - criterion 7: tests/domain/test_lease.py::test_another_instances_claim_is_held_until_its_lease_has_run_out (59m59s held, 60m and 60m1s expired)
   - criterion 8: tests/domain/test_lease.py::test_the_lease_module_reads_no_clock. It parses the module's source with ast and refuses any call to a Name or Attribute named now, utcnow, today or time.
   - criterion 9: tests/application/test_claims.py::test_status_follows_the_boundaries_clock. It covers none, own, held at 59 minutes and expired at 60 minutes, with the `clock` fixture advanced between calls; own is checked again after the advance.
   - criterion 10: tests/application/test_claims.py::test_status_judges_by_the_claims_own_lease_duration. The definition sets the intake role's lease_duration and time_limit to 5 (new constant LEASE_5_YAML). The claim was made by another instance with 60 minutes and reads held after 30 minutes.
   - criterion 11: tests/application/test_claims.py::test_release_clears_the_claim_and_keeps_everything_else
   - criterion 12: tests/application/test_claims.py::test_release_of_a_document_without_a_claim_returns_an_equal_document
   - criterion 13: tests/application/test_claims.py::test_release_of_a_document_without_state_raises_value_error
   - criterion 14: tests/test_claim_ownership.py::test_only_the_claim_service_uses_the_lease_functions
     - The set of modules whose `imported_modules` holds `factory.domain.lease.<name>` must equal exactly {factory.application.claims}, so the test fails when that module imports none of the three.
     - No other module may have an ast.Attribute with one of the three names whose value is `lease` or the dotted `factory.domain.lease`.
     - Plain variables or parameters named `claim_status` are not matched.
   - criterion 15: tests/test_claim_ownership.py::test_only_the_claim_service_constructs_a_claim. It looks for Call nodes whose func is the Name `Claim` or an Attribute `.Claim`; the set of modules that have one must equal {factory.application.claims}. This test already passes against current code, which is correct.
   - criteria 16 and 17: not test criteria.

   Files:
   - created tests/domain/test_lease.py and tests/test_claim_ownership.py
   - extended tests/application/test_claims.py (my own module from S0001): constants LEASE_5_YAML and OTHER_INSTANCE, helpers _service and _claimed_state, and the five tests above.

   Not importable: `factory.domain.lease`. The `make test` run stops at collection of tests/domain/test_lease.py with "ImportError: cannot import name 'lease' from 'factory.domain'". Once that module exists, these are expected to fail until implemented:
   - the status/release tests, because ClaimService has no `status` or `release` yet
   - the first search test, because the importer set is empty

   `make lint` is green. I did not run the type check, as the stage skill says.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Implemented the lease clock and the claim service's `status` and `release` (commit 5125046). `make check` is green, and both demo blocks print the expected output.
   - `src/factory/domain/lease.py` (new) holds `ClaimStatus`, `lease_age`, `lease_expired` and `claim_status`. They are pure functions: `now` is always passed in, and expiry uses `>=` against the claim's own `lease_duration`. An own claim returns "own" before `now` is looked at.
   - `src/factory/application/claims.py`:
     - `ClaimService.status(state)` calls `claim_status` with the service's instance and `boundaries.clock.now()`. It never reads the definition's `lease_duration`.
     - `ClaimService.release(document)` uses `model_copy` to set `state.claim` to None and leaves everything else as it was. A document without state raises `ValueError`.
     - The class docstring now says the service claims, judges and releases.
   - Design decision: `release` does not reuse `_state_of`, because that helper's error message talks about claiming. It checks for missing state inline with its own message instead. I rejected adding a parameter to `_state_of` for the message as more machinery than two lines are worth.
   - Refactor: I re-read the diff and found nothing to change, so there is no refactor commit.
   - Noticed, not touched: none.

   `make check`: check: green
