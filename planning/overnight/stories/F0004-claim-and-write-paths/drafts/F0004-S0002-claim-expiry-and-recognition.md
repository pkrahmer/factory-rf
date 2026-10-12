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
- Search tests (GH1.2). They parse every `.py` file under `src/factory` with `ast`. First: the names `claim_status`, `lease_expired` and `lease_age` occur (as a name, an attribute or an imported name) only in `factory/domain/lease.py` and `factory/application/claims.py`, and the test fails when it finds them in neither of those two. Second: `Claim` is called as a constructor only in `factory/application/claims.py`.

Tests: `tests/domain/test_lease.py`, `tests/application/test_claims.py` (the same module as S0001, with the shared fixtures; the clock is the `clock` fixture, advanced with `advance`), `tests/test_claim_ownership.py` for the search tests.

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
10. `ClaimService.status` judges by the claim's own `lease_duration`: a claim made with 60 minutes by another instance reads `"held"` after 30 minutes even when the service's definition sets the role's `lease_duration` to 5.
11. `ClaimService.release` returns the document with `state.claim` set to `None`, and every other state field, the journal records and the body equal to the given document's.
12. `ClaimService.release` on a document without a claim returns an equal document.
13. `ClaimService.release` on a document whose `state` is `None` raises `ValueError`.
14. The first search test finds `claim_status`, `lease_expired` and `lease_age` in `factory/domain/lease.py` and `factory/application/claims.py` and in no other module under `src/factory`.
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
grep -rlE 'claim_status|lease_expired|lease_age' src/factory --include='*.py' | sort
```
Expect: exactly two lines, `src/factory/application/claims.py` and `src/factory/domain/lease.py`.

## Log (append only)

1. 2026-10-12 human: created.
