---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 390
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T06:58:49.228286Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T06:58:49.235031Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T06:59:11.542590Z'
  stage: intake
  run: f3ee17162d754e968a1a4480cda6dc42
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T06:59:31.866066Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T07:00:59.744998Z'
  stage: tests
  run: db7aa59a5a454051a86e9f16af2825af
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T07:01:21.004882Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T07:04:04.796083Z'
  stage: doing
  run: f70c6ae5ff9240cb9b36068bd5a13893
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T07:04:25.902773Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T07:04:50.912426Z'
  stage: review
  run: b9090076a47a4a898243239236dba148
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T07:05:11.713526Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-21T07:05:43.760229Z'
  stage: docs
  run: 80e579925e46416c9f5d7cc866a6e6f7
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-21T07:06:04.775871Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-21T07:06:28.153820Z'
  stage: smoke-test
  run: e2689e33ef4a4610802ad71d05408517
---

# The project guide points to the template's pipeline definition and describes `factory-health`

## Description

Two gaps in the project guide (findings H4 and M5 of the documentation review of 2026-10-20, re-checked on `main` of 2026-10-20). First, `docs/project-guide/agents.md`, *The template*, quotes `template/factory/pipeline.yml` in a YAML block, and the copy has gone stale: it lacks the `tool_paths` line and its comment, which the file has. An agent or an operator who copies the definition from the guide gets one under which every `make check` ends with `Permission denied`, because the kernel allows no write outside the write paths and tool paths. A copy goes stale again with every change of the file, so the block gives way to a pointer and one sentence on what the file holds. Second, every module under `src/factory` is named in the guide's index, `docs/project-guide/README.md`, except four. No guide file describes `factory.entry.health` (the console command `factory-health`, the container's health check). `factory.domain.sessions` (F0030-S0001: one line of the kernel's process table, and what of a session is left to kill) is described in `processes-and-checks.md`, under *Starting a process* (**Killing a session.**), but its index line does not name it. `factory.application.agent_home` (the interface `AgentHome`) and `factory.adapters.agent_home` (`SudoAgentHome`), both F0040-S0004's, are described in `agents.md`, *The fresh home*, but the index line of `agents.md` names only the other three modules of the fresh home. The five other modules the review found missing were added since by F0025-S0004 and F0025-S0005. This story adds one paragraph on `factory-health` to `watching.md`, names it on that file's index line, names `factory.domain.sessions` on the index line of `processes-and-checks.md`, and names the two `agent_home` modules on the index line of `agents.md`. Nothing else changes; a lasting check that keeps the index complete (the review's structural proposal S4) is the human's to decide.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes `docs/project-guide/agents.md`, `docs/project-guide/watching.md` and `docs/project-guide/README.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/project-guide/agents.md`, *The template*, the bullet on `template/factory/pipeline.yml`: the YAML block is removed. In its place the bullet says, in one sentence, that the file holds the three project commands `check`, `lint` and `test` with their `time_limit`s, the `tool_paths` the project's tools may write besides the write paths, the seven roles with their write paths, and the stages; and that the guide does not copy it, so read the file itself. The bullet's other sentences (the stage order, "Copy it to `factory/pipeline.yml` and adjust it", the coder's write path) stay. `agents.md` holds no fenced `yaml` block after the story.
   - `docs/project-guide/watching.md`, *Stops, the clock and the factory log*: one paragraph after the paragraph on `factory.application.machine` describes `factory-health` (`factory.entry.health`, `main(argv=None, *, store=None) -> int`), checked against `src/factory/entry/health.py`: it reads the health status from the health file of the state directory (`--state-directory <path>`, default the image's `/state`), or from the `HealthStatusStore` it is given; it prints `healthy` and returns 0, or prints one line per stop in force, `<reason> (<scope>): <detail> (since <at>)`, and returns 1; a missing health file prints `no health status: <path> is missing` and returns 1.
   - `docs/project-guide/README.md`, *The files*, the `watching.md` line: "It describes ..." gains `factory-health` after `factory-run`, and "It also names ..." gains `factory.entry.health` before `factory.entry.run`, each in backticks. The `processes-and-checks.md` line: "It also names ..." gains `factory.domain.sessions` after `factory.domain.known_results`. The `agents.md` line: "The fresh home (`factory.domain.agent_home`, `factory.adapters.home_files`, `factory.entry.fresh_home`)" becomes "The fresh home (`factory.domain.agent_home`, `factory.application.agent_home`, `factory.adapters.agent_home`, `factory.adapters.home_files`, `factory.entry.fresh_home`)". No other line of the index changes.
   - After the story every module under `src/factory` (each `.py` file but `__init__.py`, by its dotted name) is named in backticks in the index. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c '^ *```yaml' docs/project-guide/agents.md || true
grep -c 'tool_paths' docs/project-guide/agents.md
```
Expect: two lines, `0`, then a number of at least `1`

```bash
grep -c -F -e '`factory.entry.health`' -e 'no health status: <path> is missing' docs/project-guide/watching.md
( cd src && for m in $(find factory -name '*.py' ! -name '__init__.py' | sed 's/\.py$//; s#/#.#g' | sort); do grep -q -F "\`$m\`" ../docs/project-guide/README.md || echo "missing: $m"; done ); echo end
```
Expect: a number of at least `1`, then the single line `end` (no module of `src/factory` is missing from the index)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: four lines, `0`, then `docs/project-guide/README.md`, `docs/project-guide/agents.md` and `docs/project-guide/watching.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: none by design (documents only). It names the three files the documenter changes. The `factory.entry.health` signature it quotes, `main(argv=None, *, store=None) -> int`, matches `src/factory/entry/health.py`.
   Criteria: each is checkable by one check. The YAML block is removed, and `agents.md` has exactly one fenced yaml block, at line 323. The `factory-health` paragraph states both sides of the behaviour: `healthy` with 0, one line per stop with 1, and a missing file printing `no health status: <path> is missing` with 1. The text matches `health.py`. The three index edits are given as exact before and after text. The index-completeness criterion is checked by the smoke test's loop. `make check` and `docs:` are the last two criteria.
   Smoke test: the commands are runnable. None runs pytest, so the `-q` rule does not apply. Every `Expect:` line is checkable: `0` then at least 1, at least 1 then `end`, four lines, and `documents ok`.
   Architecture: no code, layer or interface is touched. The change stays in `README.md` and `docs/project-guide/`, which is the documenter's write path.
   Scope: it matches the feature's S0003 (H4 and the rest of M5). The structural proposal S4 is explicitly left out, and no file outside the docs changes.
4. factory: started tests as self.
5. tester: Tests: none written, as the work item asks. Its Interface says nothing changes in any test, and criterion 1 says nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. This entry confirms that for the tester: I changed nothing under any of those folders, or anywhere else.
   Criterion 1 (no change under src, tests, image, template, demo, claude): no test function. Checked by the third smoke-test command (`git diff --name-only origin/main -- src tests image template demo claude | wc -l` gives `0`). A test under `tests/` would itself break this criterion.
   Criterion 2 (`make check` stays green): no test function. It is the stage checks' gate.
   Criterion 3 (docs): no test function. It is the documenter's criterion and is checked by the smoke test (the fenced yaml count, `tool_paths`, the `factory-health` paragraph, the loop that checks every module is in the index) and by `make documents`.
   Files created: none. Modules the test runner could not import: none, since there are no new tests and so no red tests for the coder. I did not run `make test`: with no new tests it has nothing to show failing. `make lint` is green.
   Open: nothing. The coder has no code to write for this story either; per criterion 1, the coder's entry should say the same.

   `lint`: lint: green (0.7 s)
   `test`: test: green (66.3 s)
6. factory: started doing as self.
7. coder: Built: nothing. This story only changes documents. Its Interface says nothing under `src/factory/` and no test changes, and criterion 1 says nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. For the coder: I changed no file under any of those folders, or anywhere else. The tester wrote no tests, so there were no failing tests to make pass.
   Main choice: hand forward with an empty diff. The other option was to make the three docs edits here (`docs/project-guide/agents.md`, `watching.md`, `README.md`), and I rejected it: they belong to the documenter's docs criterion, and the coder does not write the project guide (CLAUDE.md, *Docs*).
   Refactor: no diff, so there was nothing to refactor.
   Description: no journal entry changed the meaning of the task, so it stays as written.
   Noticed but not touched: nothing.
   `make check`: check: green (test: green, 64.1 s, coverage 99.14 %).

   `check`: check: green
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   Reviewed `git diff main...HEAD -- . ':!factory'`. It is empty: `--stat` lists nothing, and `--name-status` shows only the work item and its `.costs.jsonl` sidecar under `factory/`.
   - Criterion 1 holds. Nothing changes under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The tester's entry (5) and the coder's entry (7) each say so.
   - Criterion 2 holds. The factory's `make check` after the coder was green (entry 7: `check: green`, coverage 99.14 %, `duplicates: 0 new`). The criteria state no rule or limit under `src/` that would need a test for its failing side.
   - Architecture and security: nothing is touched.
   - Work item hygiene. The Description matches what was built (nothing yet; the documenter writes the docs next). The coder's entry gives the main decision and what it rejected (writing the docs itself). I checked the docs criterion against what is there today, and it is accurate:
     - `src/factory/entry/health.py` has `main(argv=None, *, store=None) -> int`, `--state-directory` with default `STATE_DIRECTORY`, prints `healthy` and returns 0, or prints one line per stop as `<reason> (<scope>): <detail> (since <at>)` and returns 1, and on a missing file prints `no health status: <path> is missing` and returns 1.
     - The only fenced `yaml` block in `docs/project-guide/agents.md` is the template copy at line 323. It lacks the `tool_paths` line and its comment, which `template/factory/pipeline.yml` (lines 9–10) has.
     - The sentence about the coder's write path stays after the block.
     - The module loop from the smoke test reports exactly the four modules the Description names as missing from the index: `factory.adapters.agent_home`, `factory.application.agent_home`, `factory.domain.sessions` and `factory.entry.health`.
   - Earlier tests: the diff changes, renames or deletes no test file, so there is nothing to name.
10. factory: started docs as self.
11. documenter: Files changed (documents only, so I did not run `make check`; the factory's checks decide):
    - `docs/project-guide/agents.md`, *The template*: removed the stale YAML copy of `template/factory/pipeline.yml`. It lacked `tool_paths`. The bullet now says in one sentence what the file holds (the three project commands with their `time_limit`s, the `tool_paths`, the seven roles with write paths, the stages) and that the guide does not copy it. The stage order, "Copy it ... and adjust it" and the coder's write-path sentence stay. The file has no fenced `yaml` block now.
    - `docs/project-guide/watching.md`, *Stops, the clock and the factory log*: one paragraph on `factory-health` after the `factory.application.machine` paragraph. I checked it against `src/factory/entry/health.py`: the signature, `--state-directory` with default `/state` (`STATE_DIRECTORY`), `healthy` with 0, one line per stop with 1, and the missing-file line with 1.
    - `docs/project-guide/README.md`, the index: `factory-health` after `factory-run` and `factory.entry.health` before `factory.entry.run` on the `watching.md` line; `factory.domain.sessions` after `factory.domain.known_results` on the `processes-and-checks.md` line; `factory.application.agent_home` and `factory.adapters.agent_home` in the fresh-home list on the `agents.md` line. Nothing else in the index changed.

    Checks I ran: the smoke test's module loop prints only `end` (every module of `src/factory` is in the index), the yaml count in `agents.md` is 0, and `make documents` ends with `documents ok`.

    Cross-read and found current: the rest of `agents.md` (*The template*, its `CLAUDE.md` and Makefile bullets), `watching.md`'s `machine` paragraph, and the index lines for the other files, against the empty code diff (nothing under `src/` changed).

    Findings: none. Stale text noticed but not touched: none.

    `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test passed: all four commands met their `Expect:` lines, and nothing in the run contradicts any acceptance criterion. Findings: none. I fixed nothing; I ran the commands as written from the repository root, in order, and changed no file.

    Command 1, the yaml block count and the `tool_paths` count in `agents.md`:
    ```
    0
    1
    ```
    Met (`0`, then at least `1`).

    Command 2, the `factory-health` lines in `watching.md` and the module-index loop:
    ```
    1
    end
    ```
    Met (at least `1`, then the single line `end`: every module of `src/factory` is named in the index).

    Command 3, the changed files against `origin/main`:
    ```
    0
    docs/project-guide/README.md
    docs/project-guide/agents.md
    docs/project-guide/watching.md
    ```
    Met (four lines: `0`, then the three project-guide files).

    Command 4, `make documents 2>&1 | tail -n 1`:
    ```
    documents ok
    ```
    Met.

    Check against the acceptance criteria (I read `git diff origin/main -- docs` and `src/factory/entry/health.py`):
    - Criterion 1: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed (command 3 gives `0`). The tester's entry (5) and the coder's entry (7) each say so.
    - Criterion 2: I did not run `make check` again. The factory's run after the coder was green (entry 7), and the docs stage changed only files under `docs/`.
    - Criterion 3, `agents.md`: the YAML block is gone. In its place is a sentence naming `check`, `lint` and `test` with their `time_limit`s, the `tool_paths`, the seven roles with their write paths, and the stages, and saying to read the file itself. The sentences on the stage order, "Copy it … and adjust it" and the coder's write path are still there.
    - Criterion 3, `watching.md`: the new `factory-health` paragraph comes right after the `factory.application.machine` paragraph. It matches `health.py`: the signature, `--state-directory` with default `STATE_DIRECTORY`, `healthy` with 0, the per-stop line format with 1, and the missing-file message with 1.
    - Criterion 3, `README.md`: the index gained exactly the stated items (`factory-health`, `factory.entry.health`, `factory.domain.sessions`, `factory.application.agent_home`, `factory.adapters.agent_home`), each at the stated place. Only those three index lines changed.

    Open: nothing.
