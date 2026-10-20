---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 373
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T23:41:06.488134Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T23:41:06.493786Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T23:41:25.673543Z'
  stage: intake
  run: 2120597f6a7d4b2da8c6e571a0ef5da1
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T23:41:47.276206Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T23:44:10.032417Z'
  stage: tests
  run: 573ba301d3be46e5810fd5d81a1dea81
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T23:44:30.499994Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T23:46:06.506765Z'
  stage: doing
  run: f33b6ae48c0c44e58aea9a4751400e44
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T23:46:27.226146Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T23:46:54.179360Z'
  stage: review
  run: 30abd1fe4c804bcdb33771de684e3dd3
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T23:47:15.032762Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T23:47:33.565438Z'
  stage: docs
  run: 3fcdfbb2172f4ae1807f82b96482dc78
---

# The decision log says why an un-ignored path is accepted

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0027's `feature.md` decision 7 accepts that an agent can un-ignore a path inside its write paths, and adds no rule against it. A nested `.gitignore` with `!__pycache__/` in `src/` makes a `.pyc` there untracked and not ignored. `remove_ignored()` then keeps it, and it is committed with the result and shows in the pull request's diff, where the reviewer and the human see it. The undo removes it when it lies outside the stage's write paths. Inside the tool paths no `.gitignore` takes effect, since git does not read the rules of an ignored folder. An agent cannot write the protected root `.gitignore` or `.git/info/exclude` (the kernel's rules and the seal). That reason reached no document. The entry *The factory removes the git-ignored paths after every agent run and at the restore* in `docs/decisions.md` names the feature's decisions 2 and 4 to 7 in its date line, but it says nothing of decision 7. So a later story that finds an un-ignored file in a diff has no record that this was weighed and accepted, and may add a rule the feature chose not to add. This story adds one bullet to that entry. No code, test or other document changes.

## Interface

None: documents only (`docs/decisions.md`). No module under `src/factory/` and no test changes.

## Acceptance criteria

1. Nothing under `src/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/decisions.md`, the entry *The factory removes the git-ignored paths after every agent run and at the restore*, gains a bullet that starts `Accepted: an agent can un-ignore a path`, after its `Rejected:` bullet and before its `Test children (F0027-S0004)` bullet. It says that a nested `.gitignore` in a write path with a negated rule (`!__pycache__/`) makes the path untracked and not ignored, so `remove_ignored()` keeps it. It says why that is accepted: the path is committed with the result and shows in the pull request's diff; the undo removes it outside the stage's write paths; no `.gitignore` takes effect inside an ignored tool path, because git does not read the rules of an ignored folder; and an agent cannot write the root `.gitignore` or `.git/info/exclude`. So nothing is hidden, and no rule is added (F0027 decision 7). `README.md`, `docs/operator-guide.md` and `docs/project-guide/`: none, since no behaviour changes.

## Smoke test

```bash
grep -c "Accepted: an agent can un-ignore a path" docs/decisions.md
```
Expect: `1`

```bash
git diff --name-only origin/main -- src tests | wc -l
```
Expect: `0`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: none, documents only (`docs/decisions.md`). That is consistent with the story, which changes no module or signature, and no Interface comment states a behaviour that needs a criterion.
   Criteria: three. (1) Nothing under `src/` or `tests/` changes, checked by the second smoke test. (2) `make check` stays green. (3) The docs criterion names the bullet's opening words, its position (after `Rejected:`, before the `Test children (F0027-S0004)` bullet) and its content: a nested `.gitignore` with `!__pycache__/`, and the four reasons it is accepted. I confirmed that the entry and both neighbouring bullets exist in `docs/decisions.md` (the entry heading is at line 934, its `Rejected:` bullet at line 940, and the next bullet follows at line 941). The story states no rule with a failing side, because it adds a record and no behaviour.
   Smoke test: both commands are runnable. `grep -c ... docs/decisions.md` expects `1`, and `git diff --name-only origin/main -- src tests | wc -l` expects `0`. Neither runs pytest, so the `-q` rule does not apply. Each `Expect:` line can be checked against the output.
   Architecture: a decision-log bullet belongs in `docs/decisions.md`, which the documenter stage keeps. Nothing in the layers is touched.
   Scope: it follows F0027 `feature.md` decision 7, which accepts that an agent can un-ignore a path and adds no rule, and it adds nothing beyond that. It is not in the feature's Out of scope. It adds no test and changes no test another story wrote.
4. factory: started tests as self.
5. tester: I wrote no tests. Nothing under `src/` or `tests/` changes in this stage, which is what criterion 1 requires.
   - criterion 1 (nothing under `src/` or `tests/` changes): I added no test function, and the story's second smoke test checks this (`git diff --name-only origin/main -- src tests`). The only change in my working tree is the factory's `.costs.jsonl` sidecar.
   - criterion 2 (`make check` stays green): no test function. The factory's checks cover it. I ran `make test` once and it is green (99.14 % coverage); `make lint` is green too.
   - criterion 3 (docs: the `Accepted: an agent can un-ignore a path` bullet in `docs/decisions.md`): no test function. It is a docs criterion, and the documenter stage and the first smoke test (`grep -c`) check it.
   Files created: none. Modules the test run could not import: none. There are no red tests on this branch on purpose, because the story is documents only (Interface: none). For the coder: do not change anything under `src/` or `tests/`, and end your entry by saying so, as criterion 1 asks.

   `lint`: lint: green (0.5 s)
   `test`: test: green (63.5 s)
6. factory: started doing as self.
7. coder: Built: nothing. I changed nothing under `src/` or `tests/`, and no other file either, as criterion 1 asks. The Interface is "None: documents only", and the tester left no red tests, so there was nothing to make pass. `make check` is green (`check: green`, coverage 99.14 %).
   Main choice: I left `docs/decisions.md` for the documenter stage. I rejected writing the `Accepted: an agent can un-ignore a path` bullet myself, because CLAUDE.md says the documenter keeps `docs/decisions.md` true from the docs criterion and the coder does not write it.
   Refactor: there is no diff, so there was nothing to refactor. The journal did not change what the task means, so `## Description` stays as it is.
   Noticed, not touched: the only change in the working tree is the factory's `.costs.jsonl` sidecar for this work item.

   `check`: check: green (not run again: passed on tree 4c5c6c3d981c at 2026-10-20T23:21:09Z)
   `duplicates`: duplicates: 6 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar, both under `factory/`.
   - Acceptance criteria: criterion 1 (nothing under `src/` or `tests/` changes) holds, because the diff touches neither folder. The tester's entry 5 and the coder's entry 7 each say so, as the criterion asks. Criterion 2: the coder's entry records `check: green` (coverage 99.14 %). Criterion 3 is the docs criterion and is left to the documenter. The story states no rule or limit, so there is no failing side to test.
   - Architecture, security, quality: nothing under review, since no code changed. The `duplicates: 6 new` in entry 7 does not come from this branch, because the branch has no `src/` diff.
   - Work item hygiene: the Description matches what was built (nothing yet; the bullet comes in the docs stage). The coder's journal gives the main choice, leaving `docs/decisions.md` to the documenter, and what was rejected. The docs criterion still holds against `docs/decisions.md`: the entry *The factory removes the git-ignored paths after every agent run and at the restore* is at line 934, and its `Rejected:` bullet is followed directly by the `Test children (F0027-S0004)` bullet. So the place the criterion names for the new `Accepted: an agent can un-ignore a path` bullet exists.

   Earlier tests: none. No test file on `main` is changed, renamed or deleted.
10. factory: started docs as self.
11. documenter: Changed one file: `docs/decisions.md`. In the entry *The factory removes the git-ignored paths after every agent run and at the restore* I added the bullet `Accepted: an agent can un-ignore a path ...`, after `Rejected:` and before `Test children (F0027-S0004)`. It records F0027 decision 7. A nested `.gitignore` with `!__pycache__/` in a write path leaves the path untracked and not ignored, so `remove_ignored()` keeps it. That is accepted for four reasons: the path is committed and shows in the pull request's diff; the undo removes it outside the stage's write paths; no `.gitignore` takes effect inside an ignored tool path, because git does not read the rules of an ignored folder; and an agent cannot write the root `.gitignore` or `.git/info/exclude`. The bullet ends by saying no rule is added and a later story should ask first. That last sentence is my addition, to guard against the failure the story describes.

    Ran the first smoke command: `grep -c "Accepted: an agent can un-ignore a path" docs/decisions.md` prints `1`. I did not run the second smoke command (`git diff --name-only origin/main -- src tests | wc -l`). `git diff main...HEAD` showed no change under `src/` or `tests/` before my edit, and I changed only `docs/decisions.md`. I did not run `make check`, because I changed only a document and the factory runs it next.

    Cross-read and found current: the same decision-log entry (its date line and the neighbouring bullets) against the story. README, the operator guide and the project guide need no change, as the docs criterion says, since no behaviour changed.

    Stale text seen but not touched: none.

    `check`: check: green (not run again: passed on tree 4c5c6c3d981c at 2026-10-20T23:21:09Z)
    `secrets`: secrets: green (1.3 s)
    `documents`: documents ok
