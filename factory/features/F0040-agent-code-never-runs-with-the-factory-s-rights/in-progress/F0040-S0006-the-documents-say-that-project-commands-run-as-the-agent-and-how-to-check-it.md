---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 376
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T00:01:52.378359Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T00:01:52.383497Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T00:02:12.015265Z'
  stage: intake
  run: 9f6c516de278494e89d09207a1a824ba
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T00:02:32.626715Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T00:05:06.097809Z'
  stage: tests
  run: 4bcdefe4a24d4299b8f6ab60ed1cc1d0
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T00:05:27.694943Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T00:07:03.484004Z'
  stage: doing
  run: efdf5df6a2ad4fb8ae55a0d0a9b14bf4
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T00:07:24.230825Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T00:07:36.809956Z'
  stage: review
  run: 573f872bf9b34d9d93f92703dc162132
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T00:07:57.285334Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-21T00:08:20.868515Z'
  stage: docs
  run: 9a09531e7cb2479bbb6ad46d14a299e0
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-21T00:08:41.530790Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-21T00:09:05.821815Z'
  stage: smoke-test
  run: cc3a2ef900bf49a7ab96cb3b4df06cfc
---

# The documents say that project commands run as the agent, and how to check it

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0040 made every project command run as the agent's user, under that user's own `timeout`, and gave every agent run and every project command a fresh agent home. Each story's documenter wrote its own part of this, but five older sentences still describe how things were before, and the operator guide is missing the checks that the feature's `feature.md` asks the operator to run after the merge (*The human's changes*, 3). The five sentences are these. (1) `docs/project-guide/processes-and-checks.md`, *Rules of `run`*, says without condition that when a command is ended by `time_limit`, "every process of its session is killed". That holds for the factory's own kill, when there is no user. With a `CommandUser`, the user's own `timeout` kills `make`'s process group, and the leftovers program ends whatever left that group (*Running as another user* in the same file says so). (2) `docs/decisions.md`, *The agent's git trusts the shared checkout*, says "A project command's git (`make` as `factory`) does read it". Since F0040-S0002, `make` runs as `agent`. (3) The decision log's entry of 2026-10-17 on the agent files (F0012-S0025) says, under "Open:", that the files the agent may add to `~/.claude` stay writable and that `claude` reads them (a user `CLAUDE.md`). Since F0040-S0004 the fresh home removes them before every run. The entry of 2026-10-16 got a "closed by" note for the same reason; this one did not. (4) The entry of 2026-10-19 (F0022-S0002), *The agents load a project's skills, and the agent's home gets none*, says the same under its own "Open:": a user `CLAUDE.md` and `.claude.json` in the home stay writable and are read by `claude`. (5) `docs/project-guide/watching.md` says that `build_boundaries` gives `leftovers_command()` to "every agent runtime it builds". It also gives it to the project commands' `CommandUser` when the instance has an agent user. The operator guide's *Morning observations* has rows for the fresh home and for the token's folder. It has no row for the operator's checks 3.1 (a stage's `make` runs as `agent`), 3.2 (the reset does not fail), 3.5 (the shared `.venv` stays group-writable after a check that synced it) and 3.7 (a check that reaches its time limit leaves no process of `agent`). This story corrects the five sentences and adds the four rows. No code, no test, no `README.md` change.

## Interface

None: documents only (`docs/project-guide/processes-and-checks.md`, `docs/project-guide/watching.md`, `docs/decisions.md`, `docs/operator-guide.md`). No module under `src/factory/` changes, and no test changes.

## Acceptance criteria

1. Nothing under `src/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/project-guide/processes-and-checks.md`, *Rules of `run`*, the bullet on the exit status: the clause "every process of its session is killed" becomes "without a user, every process of its session is killed; with a user, the user's own `timeout` kills `make`'s process group, and the leftovers program ends what left it (see *Running as another user*)". Nothing else in the bullet changes.
   - `docs/decisions.md`, *The agent's git trusts the shared checkout*: "(`make` as `factory`)" becomes "(`make`, as `agent` since F0040-S0002)".
   - `docs/decisions.md`, the entry of 2026-10-17 (F0012-S0025) on the agent files: right after "(a user `CLAUDE.md`, skills)", the note "(closed on 2026-10-20 by *Every agent run and every project command starts from a fresh agent home*)". The rest of its "Open:" list stays as it is.
   - `docs/decisions.md`, the entry of 2026-10-19 (F0022-S0002), *The agents load a project's skills, and the agent's home gets none*: in its "Open:" bullet, right after "a user `CLAUDE.md` and `.claude.json` in the home stay writable and are read by `claude`", the same note. The rest of the bullet stays as it is.
   - `docs/project-guide/watching.md`: the sentence on `leftovers=leftovers_command()` also says that, when the instance has an agent user, `build_boundaries` hands the same list to the project commands' `CommandUser` (see `processes-and-checks.md`, *Running as another user*).
   - `docs/operator-guide.md`, *Morning observations*: four new rows, after the row "The home is fresh". (a) "A project command runs as `agent`": `docker exec <container> ps -o user,args -C make` while a stage's check runs; expected: every line after the header shows `agent`, and none shows `factory`. (b) "The home is reset": `docker exec <container> tail -n 50 /state/factory.log` after the first stage run after a rebuild; expected: no `cannot reset the agent's home`, and the run passes. (c) "The shared `.venv` stays writable": `docker exec <container> find /work/checkout/.venv -maxdepth 3 ! -perm -g+w` after a check that synced it; expected: nothing printed. (d) "A check at its limit leaves no process": `docker exec <container> ps -o user,pid,args -U agent` after a check that reached its time limit; expected: only the header (the user's `timeout` ended its group, and the leftovers program ended the rest).
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`. `README.md`: none, because nothing a newcomer does changes.

## Smoke test

```bash
grep -c "(\`make\` as \`factory\`)" docs/decisions.md
```
Expect: `0`

```bash
grep -c "without a user, every process of its session is killed" docs/project-guide/processes-and-checks.md
```
Expect: `1`

```bash
grep -c "ps -o user,args -C make\|find /work/checkout/.venv -maxdepth 3" docs/operator-guide.md
```
Expect: `2`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None: documents only" is right for this story. It names the four files, and no module under `src/factory/` changes.
   - Criteria: each of the five sentence corrections and the four new rows can be checked by one test or grep, and each gives the exact wording to insert. I found every sentence to correct in the docs: `processes-and-checks.md:48`, `decisions.md:463`, `decisions.md:398` (2026-10-17) and `decisions.md:775` (2026-10-19), and `watching.md:264`. The anchor row "The home is fresh" is at `operator-guide.md:240`. The Interface states no rule with a failing side, so no refused-input criterion is missing.
   - Smoke test: the four commands are runnable, and none runs pytest, so the `-q` rule does not apply. Each `Expect:` can be checked against the output. Today the greps give 1, 0 and 0 against the expected 0, 1 and 2. The `-C make` and `maxdepth 3` rows are not in `operator-guide.md` yet.
   - Architecture: nothing in the layers changes. The four files are docs and the documenter's write paths.
   - Scope: this matches the feature's scope line "docs from each story's docs criterion". It is not in the feature's Out of scope.

   Minor: criterion 1 asks the tester and coder to end with an entry saying nothing under `src/` or `tests/` changes. That is a process note, not a testable behaviour. I accept it as written and did not change it.
4. factory: started tests as self.
5. tester: No tests written: this story only changes documents, and criterion 1 says nothing under `src/` or `tests/` changes. I changed nothing under `src/` or `tests/`.
   - criterion 1 (nothing under `src/` or `tests/` changes): no test function. This is a process rule, and `git status` shows no change under `src/` or `tests/`.
   - criterion 2 (`make check` stays green): no test function. The existing suite covers it. `make test` passed once (`test: green`, coverage 99.14 %) and `make lint` passed (`lint: green`).
   - criterion 3 (docs): no test function. The documenter checks the wording against the criterion, and `make documents` and the smoke-test greps check the result.
   Files created: none. Modules the test run could not import: none. No test is red, because there is no behaviour to specify. The coder's work is only the docs criterion. Open: nothing.

   `lint`: lint: green (0.6 s)
   `test`: test: green (63.9 s)
6. factory: started doing as self.
7. coder: I built nothing, and nothing under `src/` or `tests/` changed (criterion 1). This story only changes documents. Its Interface says "None: documents only", and the tester wrote no failing test. `CLAUDE.md` gives `docs/project-guide/`, `docs/decisions.md` and `docs/operator-guide.md` to the documenter stage: "the coder does not write them".
   - Main choice: I left all of criterion 3 (the five sentence corrections and the four *Morning observations* rows) to the documenter. The alternative I rejected was writing those docs edits here, because this stage is told not to write those documents.
   - Refactor: there is no diff, so nothing needs changing.
   - Description: no journal entry changed the meaning of the task, so I did not rewrite it.
   - Noticed, not touched: the intake found every passage to change at `processes-and-checks.md:48`, `decisions.md:463`, `decisions.md:398` and `:775`, `watching.md:264`, and the anchor row at `operator-guide.md:240`. The documenter can start from those.

   `make check`: check: green (test: green (63.7 s), coverage 99.14 %)

   `check`: check: green (not run again: passed on tree 4c5c6c3d981c at 2026-10-20T23:21:09Z)
   `duplicates`: duplicates: 6 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The only changes on the branch are the work item and its `.costs.jsonl` sidecar under `factory/`. This matches the Interface ("None: documents only") and criterion 1: nothing under `src/` or `tests/` changes, and both the tester (entry 5) and the coder (entry 7) say so.
   - Criterion 2: the factory's `make check` after the coder is green (entry 7: `check: green`). `duplicates: 6 new` cannot come from this branch, because it changes no file under `src/factory`.
   - Criterion 3 (docs) is the documenter's work, as `CLAUDE.md` *Docs* says. It names the exact wording for the five corrections and the four *Morning observations* rows. The intake checked each place it changes against the current documents (entry 3): `processes-and-checks.md:48`, `decisions.md:398`, `:463` and `:775`, `watching.md:264`, and the anchor row at `operator-guide.md:240`.
   - Description: it still matches what the story is to deliver. Nothing was built that it would have to describe, and no journal entry changes its meaning.
   - Earlier tests: none. The diff changes, renames or deletes no test file.
10. factory: started docs as self.
11. documenter: Changed only documents, as the docs criterion says; nothing under `src/` or `tests/`. I did not run `make check`, because every changed file is a document. `uv run python -m factory.entry.check_documents` printed `documents ok`.

    Files changed:
    - `docs/project-guide/processes-and-checks.md`: *Rules of `run`*, the exit-status bullet. The clause now separates the cases. Without a user every process of the session is killed. With a user, the user's own `timeout` kills `make`'s process group and the leftovers program ends what left it. It points to *Running as another user*. Nothing else in the bullet changed.
    - `docs/decisions.md`: three edits.
      - *The agent's git trusts the shared checkout*: "(`make` as `factory`)" is now "(`make`, as `agent` since F0040-S0002)".
      - The 2026-10-17 entry (F0012-S0025): the "closed on 2026-10-20 by *Every agent run and every project command starts from a fresh agent home*" note now follows "(a user `CLAUDE.md`, skills)".
      - The 2026-10-19 entry (F0022-S0002): the same note now follows "stay writable and are read by `claude`" in its "Open:" bullet. The rest of both "Open:" lists is unchanged.
    - `docs/project-guide/watching.md`: the paragraph on `leftovers_command()` now says that, when the instance has an agent user, `build_boundaries` hands the same list to the project commands' `CommandUser`. It points to *Running as another user*.
    - `docs/operator-guide.md`: *Morning observations* has four new rows after "The home is fresh". They are "A project command runs as `agent`", "The home is reset", "The shared `.venv` stays writable" and "A check at its limit leaves no process". Each has the command and the expected result from the criterion.

    Smoke-test greps: the `make as factory` pattern now matches 0 times in `docs/decisions.md`.

    Cross-read and found current against this story: the *Running as another user* section of `processes-and-checks.md` (the target of both new pointers) and the surrounding text of each edited passage. The diff has no code change, so there was nothing else to cross-read against. The code and the docs do not contradict each other, so there are no findings for the coder.

    Stale text I noticed and did not touch: none.

    `check`: check: green (not run again: passed on tree 4c5c6c3d981c at 2026-10-20T23:21:09Z)
    `secrets`: secrets: green (2.2 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test: I ran the four commands from the repository root, exactly as written and in order. All four met their `Expect:` lines, and I found nothing to report. I fixed nothing.

    1. `grep -c "(\`make\` as \`factory\`)" docs/decisions.md`
    ```
    0
    ```
    Met (`0`). grep exited with status 1, which is how grep reports zero matches. The count is the expected result.

    2. `grep -c "without a user, every process of its session is killed" docs/project-guide/processes-and-checks.md`
    ```
    1
    ```
    Met (`1`).

    3. `grep -c "ps -o user,args -C make\|find /work/checkout/.venv -maxdepth 3" docs/operator-guide.md`
    ```
    2
    ```
    Met (`2`).

    4. `uv run python -m factory.entry.check_documents`
    ```
    Using CPython 3.12.15 interpreter at: /usr/local/bin/python3.12
    Creating virtual environment at: .venv
    warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
             If the cache and target directories are on different filesystems, hardlinking may not be supported.
             If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.
    Installed 106 packages in 79ms
    Bytecode compiled 4164 files in 349ms
    documents ok
    ```
    Met (`documents ok`). The lines before it are uv creating the virtual environment on first use. They are not part of the check's result.

    Checked against the acceptance criteria. I read `git diff main...HEAD -- docs src tests README.md` against each criterion:
    - Criterion 1: nothing under `src/` or `tests/` changes. The tester (entry 5) and the coder (entry 7) each say so.
    - Criterion 2: I did not run `make check` again here, because this stage only runs the smoke test. The factory's last result is green (entries 7 and 11).
    - Criterion 3:
      - `processes-and-checks.md`, *Rules of `run`*: the exit-status clause has the required wording. Nothing else in the bullet changed.
      - `decisions.md`, *The agent's git trusts the shared checkout*: it now says "(`make`, as `agent` since F0040-S0002)".
      - The 2026-10-17 entry (F0012-S0025) and the 2026-10-19 entry (F0022-S0002): each has the "closed on 2026-10-20 by …" note right after the required phrase. The rest of each "Open:" list is unchanged.
      - `watching.md`: the sentence about `CommandUser` was added, with the pointer to *Running as another user*.
      - `operator-guide.md`: the four rows (a) to (d) come right after "The home is fresh", with the commands and expected results the criterion gives.
      - No other passage changes, and `README.md` is unchanged.

    None of the commands contradicts any criterion. Open: nothing.
