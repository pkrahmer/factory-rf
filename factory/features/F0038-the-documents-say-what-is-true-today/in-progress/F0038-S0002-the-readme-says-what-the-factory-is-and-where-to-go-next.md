---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 389
comments_read: []
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-21T06:55:17.843498Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T06:50:29.392556Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T06:50:29.398040Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T06:50:50.064067Z'
  stage: intake
  run: fcfe2a9acb51425c9276df4f839ee796
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T06:51:10.904717Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T06:52:30.055046Z'
  stage: tests
  run: 2367ddd6981d47c2a53aecdb686d3aba
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T06:52:50.769661Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T06:54:16.536185Z'
  stage: doing
  run: 11d4eb8f4aa14136b899c46c167ec43c
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T06:54:37.872369Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T06:54:57.130651Z'
  stage: review
  run: 9049f402dce24d87871a411996c963fc
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T06:55:17.843498Z'
  stage: docs
---

# The README says what the factory is, that an instance runs in the container, and where to go next

## Description

`README.md` is for the newcomer: what it is, how to run it, where to look next (`CLAUDE.md`, *Docs*). Its first paragraph is a build inventory of about 3,000 characters on one line. It says the repository "is under construction" and that "what is built so far is the groundwork the pipeline will run on", then lists some 30 parts and dated observations ("the probe of 2026-10-17"). Since the handover of 2026-10-18 v1.1 builds this repository itself, so "groundwork" is stale, and a newcomer cannot tell what the factory is. Its *Getting started* paragraph lists the six console commands with their exit statuses in one sentence of about 1,200 characters and tells the newcomer to run `uv run factory-run`, while an instance runs in the container (its checkout is `/work/checkout` and its state `/state`); the exit statuses are the operator guide's. *Where to look next* does not name `docs/operator-playbook.md`, the fifth document. This story makes those three passages short and true (findings H2, M10 and M11 of the documentation review of 2026-10-20). The paragraph on `python -m factory.entry.contract` and `check_documents` keeps its text but its first words, which still count seven console commands from before F0041 removed `factory-guard`; *How it is built* and *Replaced from v1* stay as they are. The full rewrite of the README (the review's structural proposal S3) is the human's to decide and not part of this story.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `README.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `README.md`, and no other file:
   - The paragraph under the title becomes exactly: "The factory takes a feature, split into stories, through tests, code, review, documentation and a smoke test, one agent at a time (on Claude Code, or on opencode when the operator chooses it for an instance), and the human approves each story on its pull request. This repository is its second implementation, v1.1. The first (github.com/pkrahmer/factory) built it until the handover of 2026-10-18; since then v1.1 builds this repository itself (see *How it is built*). `docs/project-guide/README.md` maps every part of the code." The words "under construction", "groundwork" and "probe of 2026-10-17" no longer occur in the file.
   - *Getting started*: the code block and the sentence "When it works, `make check` ends with the line `check: green`." stay. The rest of that paragraph becomes one sentence, "An instance runs in the container: see *The container: compose, entrypoint and health check* in `docs/operator-guide.md`, which also gives the exit statuses of the commands you run.", and then a table with the header `| Command | What it does |` and exactly six rows, in this order, each starting `` | `factory-<name> ``: `factory-run` (runs one instance, one tick per iteration, until a signal stops it), `factory-check-story <path>...` (checks a story against the story form before it starts), `factory-bill [<work item id>]` (shows what a work item cost), `factory-watch` (shows what the next tick would do and the board of features and work items; it changes nothing), `factory-health` (prints `healthy`, or one line per stop in force), `factory-confine` (run by the agent runtime: starts every agent run with its writes confined by the kernel). No exit status is named in the table.
   - The paragraph that begins "Beside the seven console commands" begins "Beside the six console commands"; the rest of it stays.
   - *Where to look next* gains one bullet after the `docs/decisions.md` bullet: "`docs/operator-playbook.md`: how the human runs the factory day to day".
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -F -e 'under construction' -e 'groundwork' -e 'probe of 2026-10-17' -e 'seven console commands' -e 'factory-guard' README.md || true
grep -c '^| `factory-' README.md
grep -c -F -e '- `docs/operator-playbook.md`: how the human runs the factory day to day' -e 'see *The container: compose, entrypoint and health check* in `docs/operator-guide.md`' README.md
awk 'NR == 3 { print length($0) <= 700 }' README.md
```
Expect: four lines, `0`, `6`, `2` and `1` (no inventory, no count of seven and no `factory-guard`, six command rows, the playbook bullet and the container sentence, and a first paragraph of at most 700 characters)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `README.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is right for a documents-only story. Nothing changes under `src/`, tests, image, template, demo or agent files, and criterion 1 pins that. The six console commands in the table match the six scripts in `pyproject.toml`.
   - Criteria: each is checkable by a command or a grep. These are the exact paragraph text, the forbidden words, the six table rows in order, the container sentence, "six console commands", the playbook bullet and `documents ok`. The failing side is covered by the first smoke test: the forbidden phrases, "seven console commands" and `factory-guard` must count 0. The first paragraph is line 3 of README.md, so the length check at `NR == 3` is valid. Every Description behaviour has a criterion.
   - Smoke test: the commands are runnable. No command runs pytest, so the `-q` rule does not apply. Each `Expect:` line is concrete: 0, 6, 2 and 1; then 0 and `README.md`; then `documents ok`. The target section "The container: compose, entrypoint and health check" exists in `docs/operator-guide.md`.
   - Architecture: no layer is touched. The story only edits `README.md`, which the documenter writes and `CLAUDE.md`'s *Docs* section assigns to it.
   - Scope: it matches feature.md's Scope line for S0002 (H2, M10, M11). It leaves out the README rewrite (S3, structural proposal), which feature.md puts out of scope.
4. factory: started tests as self.
5. tester: I wrote no tests. This story only changes documents, and criterion 1 forbids any change under `tests/`.
   - criterion 1 (nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes): no test function, because a test would itself break the criterion. I changed nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. `git status` shows only the factory's own `.costs.jsonl` sidecar.
   - criterion 2 (`make check` stays green): no test function. The factory's check gate covers it.
   - criterion 3 (docs: `README.md`): no test function. It is the documenter's criterion. The smoke test's greps and `make documents` check it.
   Files I created: none. Modules the test runner could not import: none, because there are no new tests.
   I did not run `make test` (step 2): with no new tests, nothing could fail for the right reason. The suite is the same as on `origin/main`, and the factory runs it after this stage. `make lint`: green (0.6 s).
   I rejected one option: a structural test that reads `README.md` for the required text. It would add a file under `tests/`, which criterion 1 forbids, and the smoke test already covers the same checks.

   `lint`: lint: green (0.6 s)
   `test`: test: green (59.5 s)
6. factory: started doing as self.
7. coder: I built nothing: no path changed. This story changes documents only. The Interface is "None", and criterion 1 forbids any change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The tester wrote no tests, so `make test` has no failing test to specify work.
      - criterion 1: I changed nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. `git status --short` shows only the factory's own `.costs.jsonl` sidecar.
      - criterion 2: `make check` ran in the foreground and ended with `check: green` (test: green, coverage 99.14 %).
      - criterion 3 (`README.md`): left for the documenter. `CLAUDE.md` *Docs* says the documenter stage keeps `README.md` true and the coder does not write it.
      Main choice: hand the story forward with no change and leave `README.md` to the docs stage. I rejected editing `README.md` here, even though it would be quick: that would take over the documenter's work and go against the work item's Interface ("The documenter changes only `README.md`").
      Refactor: there is no diff to refactor. The journal did not change the meaning of the task, so `## Description` is unchanged.
      Noticed, not touched: nothing.

   `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T06:37:06Z)
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar, which are the factory's files. Criterion 1 holds: nothing changed under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`.
   - Criterion 2: journal entry 7 records `check: green` after the coder, on the tree already passed at the factory's earlier run.
   - Criterion 3 is the documenter's. I checked that it is true against the repository:
     - `README.md:14` begins "Beside the seven console commands".
     - `pyproject.toml` `[project.scripts]` lists exactly the six commands named for the table: run, check-story, bill, watch, health, confine.
     - `docs/operator-guide.md:389` holds the section *The container: compose, entrypoint and health check* that the container sentence names.
     - `docs/operator-playbook.md` exists.
   - The Description matches what was built: nothing yet, since the README is the docs stage's work. The coder's journal explains why they left `README.md` to the documenter.
   - Earlier tests: none changed. The diff holds no test file.
10. factory: started docs as self.
