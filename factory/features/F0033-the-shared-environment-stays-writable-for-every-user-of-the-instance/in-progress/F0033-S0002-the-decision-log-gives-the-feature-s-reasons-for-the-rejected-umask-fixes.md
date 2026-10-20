---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 326
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-20T03:45:53.392467Z'
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
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T03:41:27.407684Z'
  stage: intake
  run: 49b54f3a9c26444ab5ba0ef4ca0942c2
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T03:41:47.853792Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T03:43:24.492806Z'
  stage: tests
  run: 1695214151c543319459aac599d4010f
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T03:43:45.286762Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T03:45:32.520622Z'
  stage: doing
  run: e3c80ec8f4e349bf8347c0c75bfac32c
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T03:45:53.392467Z'
  stage: review
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
3. intake: accepted
   - Interface: no module under `src/` changes and no test module is written; the story names the documents to compare against (F0033 `feature.md`, *Goal* second paragraph, decisions 1 and 2). The Interface states no behaviour of code, so there is nothing to leave untested. Docs-only.
   - Criteria: criterion 1 is `make check` and criterion 2 is the docs criterion, which names the exact edits to the entry in `docs/decisions.md`. The edits are the reverse-direction sentence, the three reasons in *Rejected*, the phrase to remove, and what stays. No rule has a failing side, since there is no behaviour. The Description's no-criterion claim matches the form's two closing ones. I read the current entry in `docs/decisions.md`. It exists, and the old wrong reason ("the fault would come back with the next recipe that calls `uv`") is there as described.
   - Smoke test: both blocks are runnable `sed`/`grep` commands against `docs/decisions.md`. Each `Expect:` line is checkable: three `found` lines, and `0`. The three search strings match the criterion's wording (`needs a new step as \`agent\``, `would not get the tests`, `644\` files that an agent`).
   - Architecture: nothing under `src/` or the layers is touched. Only the decision log changes, which is the documenter's file under CLAUDE.md's Docs section.
   - Scope: within F0033. The reasons come from the feature's decisions 1 and 2 and its Goal. The story touches no *Out of scope* item, no code, no `Makefile` and no earlier story's test.
4. factory: started tests as self.
5. tester: No tests written. The story only changes the docs, and its Interface says the tester writes no test module.
   - criterion 1 (`make check` stays green): no test function. The check itself covers it.
   - criterion 2 (docs: the entry in `docs/decisions.md`): no test function. The documenter checks it, and so do the smoke test's `grep` blocks.
   Files created: none. Modules the test runner could not import: none. No module under `src/factory/` changes, so there are no red tests on this branch on purpose. `make test` ran once and passed: `test: green (41.6 s)`, total coverage 99.14 %. `make lint` passed: `lint: green`. No criterion needed interpreting.

   `lint`: lint: green (0.0 s)
   `test`: test: green (40.3 s)
6. factory: started doing as self.
7. coder: No code built and no paths changed. The story only edits a document, and its Interface says no module under `src/factory/` changes and no test module is written. Its one docs criterion asks for an edit to `docs/decisions.md` (the entry *The tests set their own umask, and uv syncs under the caller's*). That file is the documenter's under CLAUDE.md's Docs section, so the coder does not write it. `make check` ran on the branch as it stands: `check: green` (test: green, 40.7 s, coverage 99.14 %).
      - Main choice: I leave the decision-log edit to the docs stage, as CLAUDE.md assigns it. Rejected: writing the entry's new reasons in this stage, which would take over the documenter's file and skip the check the story asks for against F0033's `feature.md`.
      - Refactor: there is no diff, so there was nothing to refactor.
      - Description: no journal entry changed the meaning of the task, so it stays as it is.
      - Noticed but not touched: nothing.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
