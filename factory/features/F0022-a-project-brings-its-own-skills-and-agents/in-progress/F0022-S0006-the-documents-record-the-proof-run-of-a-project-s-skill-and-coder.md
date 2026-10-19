---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 302
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-19T23:40:14.734792Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T23:36:02.215410Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T23:36:02.221021Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T23:36:21.450502Z'
  stage: intake
  run: 5922b8a2708f479d9b0c3295cb9c9d78
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T23:36:41.771479Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T23:38:24.619435Z'
  stage: tests
  run: b14725f670f44e75b10950c951cfc57f
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T23:38:45.610400Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T23:39:53.147377Z'
  stage: doing
  run: ca01e392c260448794586ac83e3d688d
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T23:40:14.734792Z'
  stage: review
---

# The documents record the proof run of a project's skill and coder

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

The human's change 2 of F0022, the proof run, took place on 2026-10-19 (night log rows 19:29 to 19:34), on the demo's own instance `skills-demo` against `pkrahmer/factory-demo-skills`. It showed both halves. The project coder's entry began `project coder:`. The intake's, tester's and coder's entries ended with `skill: journal-marker`. The log held no `agent_definition_invalid`. As `agent`, `mkdir` in the home's `skills/` was refused. After `factory/agents/coder.md` was removed from `main`, the shipped coder came back. The documents do not record any of this. Three passages are now out of date:
- `docs/operator-guide.md`, *A project's own skills*, says whether Claude Code loads a nested `.claude/skills/` "is not known (the feature's proof run looks)". The night log's rows of the proof run record no such look, so the sentence points to a check that never happened. The human corrects this story if the run did look.
- In the same paragraph, F0022-S0004 put two sentences on the nested folder before "A run reads them from its checkout". "Them" now reads as the nested folder, but it means the root `.claude/skills/`.
- `docs/decisions.md`, *The agents load a project's skills, and the agent's home gets none*, gives no evidence that Claude Code offers and loads a skill under `--tools …,Skill`. The feature's decision 15 left that to the proof run.

The story changes documents only. The nested folder stays open, as it is now.

## Interface

None: no module under `src/factory/` changes, and neither does any test, image, template, demo or agent file. The documenter changes `docs/operator-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *A project's own skills*, second paragraph:
   - "(the feature's proof run looks)" goes. The sentence says instead that whether Claude Code loads such a nested folder was not checked, and that the review and your merge see it in the diff.
   - "A run reads them from its checkout, the work item's branch." becomes "A run reads the root `.claude/skills/` from its checkout, the work item's branch."

   `docs/decisions.md`, the entry *The agents load a project's skills, and the agent's home gets none*: a new bullet `- Proven:` goes before its `Open:` bullet. It says, in one or two sentences, what the proof run of 2026-10-19 showed: on the todo demo's own instance (`skills-demo`), a project coder's entry began `project coder:` and the intake's, tester's and coder's entries ended with the project skill's line `skill: journal-marker`; once the project's coder was removed from that repository's `main`, the factory's reader gave the shipped coder again; and in a container of the same image (`self`), the agent could not make a folder in the home's `skills/`. The `Open:` bullet keeps the nested `.claude/skills/` and says that the proof run did not check it.

   No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "the feature's proof run looks" docs/operator-guide.md
```
Expect: `0`

```bash
grep -c 'A run reads them from its checkout' docs/operator-guide.md
```
Expect: `0`

```bash
sed -n "/^## The agents load a project's skills/,/^## /p" docs/decisions.md | grep -c 'skill: journal-marker'
```
Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is right for a documents-only story. It names no module or signature, and it states no behaviour that needs a criterion. The documenter's two files, `docs/operator-guide.md` and `docs/decisions.md`, are named.
   - Criteria: all three are checkable. Criterion 1 is a negative, "nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes", and the entries of the tester and the coder state it. Criterion 3 names exact strings to remove or replace, plus the content of the new `- Proven:` bullet and the `Open:` change. I confirmed that the old strings exist: `docs/operator-guide.md:989` holds both "(the feature's proof run looks)" and "A run reads them from its checkout". `docs/decisions.md:757` holds the entry, with an `Open:` bullet at line 767. The story states no limit, validation or rejected input, so there is no failing side to cover.
   - Smoke test: the four commands are runnable, and each `Expect:` line is a literal output (`0`, `0`, `1`, `documents ok`). The `sed` range in the third command starts at the exact heading at line 757 of `docs/decisions.md`. It stops at the next `## `, and the new bullet falls inside that range.
   - Architecture: no layer is touched, and the change is limited to documents, which fits the documenter's write paths (`README.md` and `docs/*`).
   - Scope: the story belongs to F0022 and records the proof run (the feature's change 2, decision 15). It leaves the nested `.claude/skills/` open, as decision 12 does, and touches nothing the feature puts out of scope. The story's description of the proof run's evidence is the human's account, and I did not verify it.
4. factory: started tests as self.
5. tester: No tests written. This story changes documents only, and its Interface says no test changes.
   - criterion 1 (nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes): no test function. I made no change under any of those paths. `git status` shows only the factory's own `.costs.jsonl` sidecar.
   - criterion 2 (`make check` stays green): no test function. It is the factory's check. `make test` is green now (coverage 99.13 %) and `make lint` is green.
   - criterion 3 (docs): no test function. The documenter writes it, and the smoke test and `make documents` cover it.
   Files created: none. Every test module imported: since there are no new tests, nothing is red on purpose, and the coder has no test specification for this story.

   `lint`: lint: green (0.0 s)
   `test`: test: green (40.4 s)
6. factory: started doing as self.
7. coder: No code written. This story changes documents only. Its Interface is "None" and the tester wrote no tests, so the coder has nothing to make pass.
   - Criterion 1: I changed nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. `git status --short` shows only the factory's own `.costs.jsonl` sidecar.
   - Criterion 2: `make check` is green on the branch as it stands (`test: green (44.3 s)`, coverage 99.13 %, `check: green`).
   - Criterion 3: the docs stage writes this, not the coder. The two passages in `docs/operator-guide.md` and the new `- Proven:` bullet in `docs/decisions.md` are still to be written there.
   - Main choice: I left `docs/` alone. CLAUDE.md gives the documents to the documenter, and the coder does not write them. The alternative I rejected was to make the doc edits here to get ahead. That would be outside the coder's role.
   - Refactor: there is no diff, so there was nothing to refactor.
   - Description: no journal entry changed the meaning of the task, so I left the Description as it is.
   - Noticed but not touched: nothing.

   `check`: check: green (not run again: passed on tree 5006d1b6db9a at 2026-10-19T23:02:45Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
