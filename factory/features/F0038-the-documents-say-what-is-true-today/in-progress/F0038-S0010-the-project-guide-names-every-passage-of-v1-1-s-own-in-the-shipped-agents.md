---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 398
comments_read: []
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-21T08:24:10.043630Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T08:17:47.336100Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T08:17:47.342013Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T08:18:05.059834Z'
  stage: intake
  run: d299f6484b2e447ab859905e28f64a33
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T08:18:25.792991Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T08:20:56.960160Z'
  stage: tests
  run: cbb687a3af784fcf870c38f6c7d699eb
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T08:21:17.668231Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T08:22:50.374294Z'
  stage: doing
  run: 3ed02e41be154e3e923b9938405047e8
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T08:23:11.755565Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T08:23:49.325307Z'
  stage: review
  run: b529dd158dfd472190bda1c01643382f
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T08:24:10.043630Z'
  stage: docs
---

# The project guide names every passage of v1.1's own in the shipped agents

## Description

`docs/project-guide/agents.md`, *The seven agents*, says the shipped bodies carry v1's texts, "the sentences are not rewritten in other words", and that "Six passages are v1.1's own text and not v1's". *Replaced from v1* repeats the count ("except the six passages"). The count is short. `git log -- claude/agents/` after `830029c9` (F0010-S0017, which carried v1's texts in) shows more passages of v1.1's own outside `## Lessons`: R14's write-guard sentences in every `## Rules` (F0019-S0006; F0041-S0001 took out its clause on the hook), rule R15 on a project's skills and agents (F0022-S0002), `intake`'s sentence in its *Stage* step 2 on a smoke test that passes `-q` (F0035-S0001), the `acceptance-reviewer`'s comparison of the Disk now line with the previous record in its check 7 (F0012-S0017), and its check 3 *Mutation testing*, "By sweep, not run here", with the words F0031-S0001 changed in its check 7, its recommendation, its proposals paragraph and its stage steps 1 and 3. The guide describes R14, R15 and the `-q` sentence elsewhere, but does not count them as v1.1's own, and it does not mention the acceptance reviewer's check 3 or its disk comparison at all. An agent that changes an agent text reads the guide to learn which sentences are v1's and must keep v1's words; a closed count that the next passage makes wrong tells it wrongly. This story makes the guide list every passage of v1.1's own, each with the story that wrote it, with no count (folded in from F0034-S0003, proposed by the acceptance of F0034). The agent texts, the tests and the other documents stay as they are.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/project-guide/agents.md`. It checks the list against `git log -p 830029c9.. -- claude/agents/` and against the shipped bodies under `claude/agents/` as they are: every sentence there that is not in v1's text and is not under `## Lessons` is one of the passages.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/project-guide/agents.md`, and no other file:
   - *The seven agents*: the sentence "Six passages are v1.1's own text and not v1's." and the two sentences after it (to "... (F0034-S0001).") become one sentence, that the passages below are v1.1's own text and not v1's, and a list with one bullet per passage, each naming the agent or agents, the section, what the passage says in a few words, and the story that wrote it. The list holds: the sentence before the `reviewer`'s checklist, the checklist's sixth item *Earlier tests* and the `acceptance-reviewer`'s added sentence in its check 6 (F0016-S0002); the reviewer's `Notes:` from round 1 on and its added criterion (F0021-S0005); the reviewer's correction of a stale Description, named as `description corrected:` (F0034-S0001); R14's write-guard sentences in every `## Rules` (the kernel refuses every other write, a refused write fails with `Permission denied`, temporary files only in `$TMPDIR`; F0019-S0006, and F0041-S0001 took out the clause on the hook); R15 in every `## Rules` (F0022-S0002); `intake`'s sentence in its *Stage* step 2 on a smoke test that passes `-q` (F0035-S0001); the `acceptance-reviewer`'s comparison of the Disk now line with the previous record in its check 7 (F0012-S0017); its check 3 *Mutation testing* with the words F0031-S0001 changed around it (F0031-S0001); and any other passage the Interface's `git log` shows. No sentence of the guide gives a count of the passages.
   - *Replaced from v1*: "except the six passages of v1.1's own text that *The seven agents* names" becomes "except the passages of v1.1's own text that *The seven agents* lists".
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -E '(Three|Six|Seven|Eight|Nine|Ten|three|six|seven|eight|nine|ten) passages' docs/project-guide/agents.md || true
```
Expect: `0`

```bash
for s in F0016-S0002 F0021-S0005 F0034-S0001 F0019-S0006 F0041-S0001 F0022-S0002 F0035-S0001 F0012-S0017 F0031-S0001; do grep -q -F "$s" docs/project-guide/agents.md && echo "named: $s" || echo "missing: $s"; done
```
Expect: nine lines, `named: F0016-S0002`, `named: F0021-S0005`, `named: F0034-S0001`, `named: F0019-S0006`, `named: F0041-S0001`, `named: F0022-S0002`, `named: F0035-S0001`, `named: F0012-S0017`, `named: F0031-S0001`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/project-guide/agents.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is right for a documents-only story. It says what the documenter changes (`docs/project-guide/agents.md` only) and how it checks the list (`git log -p 830029c9.. -- claude/agents/` and the shipped bodies). No signature is needed.
   - Criteria: the three criteria are checkable. 1: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. 2: `make check` stays green. 3: the docs criterion names the exact sentences to replace and the nine stories that must be named. It also gives the replacement for the *Replaced from v1* phrase and ends with `documents ok`. The rule "no sentence gives a count" has its failing side in smoke test 1. The open clause "any other passage the Interface's git log shows" depends on the documenter's judgement. I accept it because the Description names the passages and the Interface gives the method.
   - Smoke test: all four commands run as written. The `|| true` keeps the first one's exit status clean. No pytest is involved, so the `-q` rule does not apply. Each `Expect:` line can be checked against the output: `0`, nine `named:` lines, `0` followed by the docs path, and `documents ok`.
   - Architecture: the story changes only a project-guide document. It touches no layer and no code.
   - Scope: the story is within F0038's scope, which lists S0010 as "every passage of v1.1's own in the shipped agents". It touches only `agents.md` and none of the feature's "Out of scope" items. The feature file's note that it runs after S0004 is the human's ordering, not a problem for the story.
4. factory: started tests as self.
5. tester: No tests written: this story changes only the documents. The Interface is "None", and criterion 1 says nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` may change. Nothing under those paths changed.
   - criterion 1 (nothing under src/, tests/, image/, template/, demo/ or claude/ changes): no test function. It is checked by smoke test 3, and the working tree has no change under those paths.
   - criterion 2 (`make check` stays green): no test function. The factory's checks cover it.
   - criterion 3 (docs, `docs/project-guide/agents.md`): no test function. The documenter's work, checked by `make documents` and smoke tests 1, 2 and 4.
   Files created: none. Modules the test run could not import: none. `make test` is green with the existing suite (coverage 99.14 %, `test: green`), so there are no red tests for the coder this time. `make lint` is green.

   `lint`: lint: green (0.7 s)
   `test`: test: green (67.7 s)
6. factory: started doing as self.
7. coder: No code written. This story changes only documents. The Interface is "None", and criterion 1 says nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` may change. Nothing under those paths changed: the working tree holds only the factory's `.costs.jsonl` sidecar.
   - `make test`: there are no failing tests. The tester wrote none, and the existing suite is green.
   - `make check`: green (coverage 99.14 %, `check: green`).
   - Main choice: I left `docs/project-guide/agents.md` unedited. Criterion 3 and CLAUDE.md (*Docs*) give that file to the documenter, and they keep the coder out of `docs/`. The alternative I rejected was writing the passage list now, which would take over the documenter's work.
   - Refactor: there was no diff, so there was nothing to refactor.
   - Description: the journal did not change the meaning of the task, so the Description stays as it is.
   - Noticed, not touched: nothing.

   `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar (`git diff --name-status main...HEAD`: `M` for the `.md`, `A` for the sidecar). Criterion 1 holds: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester's entry (5) and the coder's entry (7) both say so.
   - Criterion 2: the coder's entry (7) records `check: green` on the tree. With no code diff there is nothing for the architecture, security or quality groups to judge.
   - Criterion 3 is the documenter's. I checked its premises against `docs/project-guide/agents.md` as it is on the branch. Line 303 holds "Six passages are v1.1's own text and not v1's." and the two sentences after it, to "... (F0034-S0001).". Line 331 holds "except the six passages of v1.1's own text that *The seven agents* names". So the criterion names sentences that exist, and the documenter can rewrite them as it says.
   - Work item hygiene: the Description still matches what was built (nothing yet; the docs stage writes the list). The coder's entry gives the main decision, which was to leave `agents.md` to the documenter, and the alternative it rejected. The docs criterion still says what the reader must know after this story.
   - Earlier tests: none. The diff changes no test file.
10. factory: started docs as self.
