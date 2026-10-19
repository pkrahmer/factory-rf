---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 246
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T02:10:38.357659Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T02:10:38.363701Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T02:10:57.080490Z'
  stage: intake
  run: d19a9d232e94442eb845175f9adfb69c
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T02:11:16.777828Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T02:12:16.168276Z'
  stage: tests
  run: 9b127a4d5be04df49fb0816313ff0c3f
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T02:12:36.275618Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T02:14:25.469564Z'
  stage: doing
  run: 9114f168a38c4514a3c396121a9c3cb2
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T02:14:45.949434Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T02:15:01.701468Z'
  stage: review
  run: e5d1f0c18bf349b88b04e1544b48620b
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T02:15:21.748120Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T02:16:22.234655Z'
  stage: docs
  run: 871e22203f41497eb8b6b15e504447a3
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T02:16:43.132879Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T02:17:05.948848Z'
  stage: smoke-test
  run: 5d3878beadb64826a0d47454f695f10e
---

# The README names what the feature built and counts its commands right

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0021's second acceptance read `README.md` and `docs/` from the top, as a newcomer would. The four documents agree on what the feature built, but the README, which a newcomer reads first, says nothing about it, and contradicts itself on one count. First, the README's summary of what is built names the stops and the health status and the cost records with the bill. It does not name what F0021 added to them: the cause on a journal's question and stall records, the `Human:` line under the cost table, the stop records published to `factory/stops.jsonl` on `main`, and the records contract under `src/factory/contract/`. Second, the README's paragraph on the `python -m` commands names `factory.entry.check_documents` and (under *Where to look next*) `factory.entry.check_demos`, but not `factory.entry.contract`, the command a later story runs whenever it changes a model the contract covers. Third, *Getting started* says "Seven commands exist", matching the seven `[project.scripts]` in `pyproject.toml`, and the next paragraph says "Beside the six console commands". The six dates from before F0019 added `factory-confine`. Fourth, the operator guide's "The records contract" says what the command prints on success. It does not say what it does with two or more arguments: it prints its usage line to standard error, writes nothing and exits with 2. That is pinned since F0021-S0009, whose documenter offered the sentence. This story repairs exactly these four passages and changes no code, no test and no other passage.

## Interface

None: no module under `src/factory/`, no test, no image, template, demo or agent file changes. The documenter changes `README.md` and `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `README.md`, the summary of what is built (the paragraph under the title): one sentence names four things and points to `docs/operator-guide.md`, "The records contract". They are the cause recorded on a blocking question and on a stall, the `Human:` line under the cost table (questions answered and hours waited), the stop records published to `factory/stops.jsonl` on `main`, and the records contract of generated JSON Schemas under `src/factory/contract/`.
   - `README.md`, *Getting started*: "Beside the six console commands" reads "Beside the seven console commands". It then names `uv run python -m factory.entry.contract [<folder>]` with one clause: it regenerates the records contract's schemas, and a story that changes a model the contract covers runs it. `factory.entry.contract` appears in `README.md` exactly once.
   - `docs/operator-guide.md`, "The records contract": after "The command prints `contract: 5 schemas written`.", one sentence says that with two or more arguments it prints `usage: python -m factory.entry.contract [<folder>]` to standard error, writes nothing and exits with status 2.
   - No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "six console commands" README.md
```

Expect: `0`

```bash
grep -c "seven console commands" README.md; grep -c "factory.entry.contract" README.md; grep -c "factory/stops.jsonl" README.md
```

Expect: three lines, `1`, `1` and `1`.

```bash
grep -c "usage: python -m factory.entry.contract \[<folder>\]" docs/operator-guide.md
```

Expect: `1`

```bash
uv run -q python -m factory.entry.contract one two 2>/dev/null; echo "status $?"
```

Expect: `status 2`

```bash
uv run python -m factory.entry.check_documents
```

Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is right for a docs-only story. It names the two files the documenter changes (`README.md`, `docs/operator-guide.md`) and no module or signature is needed.
   Criteria: each is checkable by one test or grep. Criterion 1 (nothing outside the docs changes) is a diff check. The docs bullets are pinned by the smoke greps: the "six"/"seven console commands" wording, `factory.entry.contract` exactly once, `factory/stops.jsonl` once, and the usage sentence. The rule for two or more arguments (usage on stderr, nothing written, status 2) has its failing side stated and is checked by the smoke test's `status 2`. I checked the current text: README has none of the new strings, line 14 says "six console commands", and the guide has 0 usage lines. So the "0" and "1" expectations are reachable only after the edit.
   Smoke test: every command is runnable. Each has an `Expect:` line that output can be checked against. The `grep -c` and `uv run` commands are the project's own.
   Architecture: no code layer is touched, so there is nothing to place. The documenter's write paths cover `README.md` and `docs/*`.
   Scope: within F0021. The story repairs the README and the operator guide's contract section, which belong to the S0006 docs and the feature's goal. Nothing in "Out of scope" is touched.
4. factory: started tests as self.
5. tester: No tests written. This story only changes docs, and its Interface is "None".
   - criterion 1: no test function. The criterion forbids changes under `tests/`, so I wrote no test, and nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed in this stage. `git status` shows only the work item's `.costs.jsonl` sidecar, which the factory writes.
   - criterion 2: no test function. The factory's `make check` covers it.
   - criterion 3 (docs): no test function. The documenter's work is checked by the smoke test's greps and by `python -m factory.entry.check_documents`. A pytest test that pins README wording would itself be a change under `tests/`, which criterion 1 rules out.
   Files created: none. Modules the test run could not import: none, since there are no new tests. I did not run `make test` because there is no new red test to see fail. `make lint` is green.

   `lint`: lint: green (0.0 s)
   `test`: test: green (40.0 s)
6. factory: started doing as self.
7. coder: No code changed. This is a docs-only story with Interface "None". Criterion 1 forbids any change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`, and nothing there changed in this stage. `git status --short` shows only the work item's `.costs.jsonl` sidecar, which the factory writes.
   - Built: nothing. The four passages in `README.md` and `docs/operator-guide.md` are the documenter's to change. The coder does not write those documents (CLAUDE.md, *Docs*).
   - Main choice: hand forward empty. The alternative I rejected was editing the README and the operator guide here. That would take the docs criterion away from the documenter, which owns it.
   - Refactor: no diff, so nothing to refactor.
   - Description: the journal did not change the task's meaning, so the description stays as written.
   - Noticed, not touched: none.

   `make check`: check: green (test: green, 37.1 s; coverage 99.06 %).

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   Reviewed `git diff main...HEAD -- . ':!factory'`, together with the work item.
   - The diff is empty outside `factory/`. Only the work item and its `.costs.jsonl` sidecar changed, so criterion 1 holds. The tester's entry (5) and the coder's entry (7) each say that nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed.
   - Criterion 2: the factory's `make check` after the coder was green (entry 7: `check: green`). `duplicates` reported 0 new findings.
   - Criterion 3 is the documenter's job, and every premise it rests on still holds on this branch:
     - `README.md:12` says "Seven commands exist", and `pyproject.toml` has seven `[project.scripts]`.
     - `README.md:14` still says "six console commands".
     - `factory.entry.contract` does not yet appear in `README.md`.
     - `docs/operator-guide.md:814` holds the sentence "The command prints `contract: 5 schemas written`." that the new sentence goes after.
     - `src/factory/entry/contract.py:12` prints exactly the usage line the docs criterion quotes.
     - `src/factory/contract/` holds the five schemas.
   - Hygiene: the coder's entry explains the main choice, which was to hand forward empty and leave the README and the guide to the documenter, and it names what was rejected. The Description matches what was built, which is nothing yet. The docs criterion still says what a newcomer and an operator must know.
   - Earlier tests: none. The diff changes, renames or deletes no test file.
10. factory: started docs as self.
11. documenter: Changed two documents, nothing else. I ran no `make check`, since only documents changed.
    - `README.md`: the summary of what is built now has one sentence naming the cause on a blocking question and on a stall, the `Human:` line under the cost table, the stop records in `factory/stops.jsonl` on `main`, and the records contract under `src/factory/contract/`. It points to "The records contract" in the operator guide. "Six console commands" now reads "seven". The paragraph names `uv run python -m factory.entry.contract [<folder>]` once, with one clause on what it does.
    - `docs/operator-guide.md`, "The records contract": added the sentence that with two or more arguments the command prints the usage line to standard error, writes nothing and exits with 2.

    Checks I ran:
    - The smoke greps give 0, 1, 1 and 1 for the README counts, as expected.
    - The command with `one two` exits with status 2.
    - `python -m factory.entry.check_documents` prints `documents ok`.

    I cross-read the rest of the README and the guide's contract section against the diff, which is empty outside `factory/`. They were current, and I found nothing that contradicts the code.

    I noticed no stale text outside this story. There are no findings for the coder.

    `check`: check: green
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test passed. I ran all five commands from the repository root, as written and in order. Every output met its `Expect:` line, and none of the acceptance criteria is contradicted.

    1. `grep -c "six console commands" README.md`
    ```
    0
    ```
    Met: `0`.

    2. `grep -c "seven console commands" README.md; grep -c "factory.entry.contract" README.md; grep -c "factory/stops.jsonl" README.md`
    ```
    1
    1
    1
    ```
    Met: three lines, `1`, `1` and `1`.

    3. `grep -c "usage: python -m factory.entry.contract \[<folder>\]" docs/operator-guide.md`
    ```
    1
    ```
    Met: `1`.

    4. `uv run -q python -m factory.entry.contract one two 2>/dev/null; echo "status $?"`
    ```
    status 2
    ```
    Met: `status 2`. Afterwards `git status --short` showed only the work item's `.costs.jsonl` sidecar. So the call with two arguments wrote nothing under `src/factory/contract/`.

    5. `uv run python -m factory.entry.check_documents`
    ```
    documents ok
    ```
    Met: `documents ok`.

    Checking the criteria against `git diff main...HEAD`:
    - Criterion 1 holds. The diff outside `factory/` touches only `README.md` and `docs/operator-guide.md`. Nothing changed under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The tester's entry (5) and the coder's entry (7) each say so.
    - Criterion 2: the factory's `make check` was green after the coder (entry 7) and after the docs stage (entry 11). The only later change is mine, and I changed nothing.
    - Criterion 3 holds. In the README's summary paragraph, one added clause names all four things: the cause on a blocking question and on a stall, the `Human:` line, `factory/stops.jsonl` on `main`, and the records contract under `src/factory/contract/`. It points to "The records contract" in `docs/operator-guide.md`. *Getting started* now says "Beside the seven console commands" and names `uv run python -m factory.entry.contract [<folder>]` with one clause, and that name appears exactly once in the README. In the operator guide, the usage sentence comes right after "The command prints `contract: 5 schemas written`." No other passage changed (the README hunk is one changed line in each of the two places).

    Findings: none.

    Not a finding, just a note: the README's summary sentence now chains "and the cost records with the bill, and the records the human can read…". That is clumsy wording but meets the criterion. The same goes for the following "It is no console script", which now follows two `python -m` commands and reads slightly oddly.
