---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-20T03:41:10.029071Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T03:41:10.023192Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T03:41:10.029071Z'
  stage: intake
---

# The decision log gives the feature's reasons for the rejected umask fixes

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0033-S0001's documenter wrote the decision log's entry *The tests set their own umask, and uv syncs under the caller's* (`docs/decisions.md`). The story named the three rejected fixes but not their reasons. The documenter wrote one-clause reasons of their own, inferred from the fault, and asked for them to be checked against F0033's decisions 1 and 2 (S0001's journal entry 11). Nobody answered before the merge. Two of the three reasons differ from the feature's, and one is wrong. A shell wrapper in the recipe (`uv run sh -c 'umask 022; exec pytest ...'`) sets the umask after `uv run` has synced, so the fault would not come back with it. The feature rejected the wrapper because a test module run on its own with `uv run pytest <module>` would not get the tests' umask, and because the hook makes the `Makefile` simpler. The feature rejected a repair of modes after every agent call because it fixes the symptom, needs a new step as `agent`, and misses the factory's own `644` files. The entry also tells only one side of the fault. The feature's *Goal* names the other side too: the factory's own `make test` left factory-owned `644` files that an agent's `uv run` could not replace. This story is for the agent or human who reads the decision log before touching a umask again. It brings the entry's reasons in line with F0033's decisions 1 and 2 and adds the reverse direction. The code, the tests, the `Makefile` and the other documents stay as they are. Because it changes no behaviour, it has no criterion beyond the two closing ones.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The documenter checks the entry against F0033's `feature.md`: *Goal* (its second paragraph, on the reverse direction) and *Decisions taken for the human* 1 and 2.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/decisions.md`, the entry *The tests set their own umask, and uv syncs under the caller's*. Its opening paragraph adds that the reverse failed too: the factory's own `make test` left factory-owned `644` files in `.venv` that an agent's `uv run` could not replace. Its *Rejected* line gives these reasons. `UV_NO_SYNC` for agents: an agent's `make check` after a dependency change would test a stale environment (unchanged). A repair of modes after every agent call: it fixes the symptom, needs a new step as `agent`, and misses the factory's own `644` files. A shell wrapper in the recipe (`uv run sh -c 'umask 022; exec pytest ...'`): a test module run on its own with `uv run pytest <module>` would not get the tests' umask, and the hook in `tests/conftest.py` makes the `Makefile` simpler. The words "the fault would come back with the next recipe that calls `uv`" go. The entry's date, its two *Decision* lines and its title stay. `README.md`, `docs/operator-guide.md` and the project guide: none, because no behaviour and nothing an operator does changes.

## Smoke test

```bash
e=$(sed -n '/^## The tests set their own umask, and uv syncs under the caller.s$/,/^## /p' docs/decisions.md)
for s in 'needs a new step as `agent`' 'would not get the tests' '644` files that an agent'; do printf '%s\n' "$e" | grep -qF -e "$s" && echo found || echo "missing: $s"; done
```
Expect: three lines `found` (the repair's reason, the wrapper's reason and the reverse direction are in the entry)

```bash
grep -c -F 'the fault would come back with the next recipe' docs/decisions.md
```
Expect: `0`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
