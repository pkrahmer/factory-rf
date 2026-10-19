---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 290
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-19T21:59:16.728661Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T21:53:37.376883Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T21:53:37.383297Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T21:54:06.126508Z'
  stage: intake
  run: c4366d1b426f4c47b3948a9ee9ae396d
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T21:54:26.942465Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T21:55:28.101651Z'
  stage: tests
  run: 66bd65e09cbc498bac058397de2c6d2c
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T21:55:48.649261Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T21:57:37.405541Z'
  stage: doing
  run: 12c3d3f6e8e54776b7a48da2318cb3d3
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T21:57:58.586597Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T21:58:16.966835Z'
  stage: review
  run: d80dab0ffaff4cfaa853cec7574bf512
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T21:58:37.410370Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T21:58:56.345940Z'
  stage: docs
  run: 3809f80a3acb45eda1325ad17d3b7a5a
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T21:59:16.728661Z'
  stage: smoke-test
---

# The operator guide's not_read example leaves out only what lint does not read

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

`docs/operator-guide.md`, *The pipeline definition*, explains `not_read` with two examples that disagree. S0001's documenter wrote the first one, `lint: {time_limit: 10, not_read: ["factory/*", "docs/*"]}`, which leaves whole folders out of `lint`. S0002's documenter wrote, a few paragraphs further on, that factory-rf leaves out only Markdown and JSON Lines files because `make lint` reads every Python file of the tree, wherever it lies. An operator who copies the first example keeps a reused `lint` from seeing a Python file under `docs/`, which is the silenced check that the feature's decision 2 rules out. The same section also says, in the future tense, that factory-rf's definition "takes this after the story that built the key" and that its docs stage "will run `secrets`". That stopped being true when the human's change 1 of `feature.md` reached `main`. It is documentation only: no code, test, template or agent file changes.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *The pipeline definition*, makes these changes and no other passage changes:
   - The first `not_read` example leaves out files by their type, not whole folders. It becomes `check: {time_limit: 10, not_read: ["README.md", "docs/*.md"]}`.
   - After "List only what the command does not read at all", one sentence is added: a linter, formatter or type checker that walks the whole tree reads every source file in every folder, so leave out file types it does not read, never a whole folder.
   - The sentence that says factory-rf's own definition takes the example "after the story that built the key" becomes the present tense and names `factory/pipeline.yml`.
   - The `check` line of factory-rf's block below that sentence is the line `factory/pipeline.yml` holds on `main` when the story starts (its `time_limit` is `15` before F0024's change 2 and `8` after it).
   - The warning that factory-rf's docs stage "will run `secrets`" becomes "runs `secrets` as a check of its own, with nothing left out".
   - `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c 'not_read: \["factory/\*", "docs/\*"\]' docs/operator-guide.md
```
Expect: `0`

```bash
grep -c 'will run `secrets`' docs/operator-guide.md
```
Expect: `0`

```bash
grep -c 'not_read: \["README.md", "docs/\*.md"\]' docs/operator-guide.md
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
   - Interface: "None" is right for a documentation-only story. Nothing under `src/`, tests, image, template, demo or agent files changes. Only `docs/operator-guide.md` changes, and that is the documenter's write path.
   - Criteria: criterion 1 (nothing outside the docs changes) and criterion 2 (`make check` green) are checkable. Criterion 3 lists each passage change exactly, so each can be checked by grep or by reading the passage. Its failing side is covered: `documents ok` from the document check, and the smoke test greps for the old text being gone (`0`). Criterion 3 reads "the `check` line is the line `factory/pipeline.yml` holds on `main` when the story starts". That is deterministic. `factory/pipeline.yml` currently holds `time_limit: 8`, and the guide's line 909 has 15.
   - Smoke test: the four commands are runnable. Each `Expect:` line is a checkable value (`0`, `0`, `1`, `documents ok`). I confirmed in the guide that the old text exists: line 900 has `not_read: ["factory/*", "docs/*"]`, line 914 has "will run `secrets`", and line 905 has "after the story that built the key".
   - Architecture: not applicable beyond the write paths. The change is documentation in the operator guide, which the documenter stage keeps.
   - Scope: it stays within F0023, which covers the operator guide's `not_read` documentation and the feature's decisions 2 and 12. Nothing in "Out of scope" is touched.
4. factory: started tests as self.
5. tester: No tests written. This story only changes documentation, and its first criterion forbids any change under `tests/`.
   - criterion 1 (nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes): no test function. As the criterion asks, this entry confirms that the tester changed nothing under `tests/` or any other folder it names. `git status` shows only the factory's own `.costs.jsonl` sidecar as changed.
   - criterion 2 (`make check` stays green): no test function. The factory's check after each stage covers it.
   - criterion 3 (docs: the operator guide's *The pipeline definition* passage): no test function. Checking a document's wording is not a test of the code. The documents check (`documents ok`) and the story's smoke-test greps cover this criterion in the docs and smoke-test stages.
   Files created: none. Modules the test run could not import: none, since no new tests exist. I did not run `make test`, because there is no red test to confirm. `make lint`: green.
   Open: nothing. The coder has no code to write for this story and only needs to keep `make check` green, and the documenter makes the change to `docs/operator-guide.md`.

   `lint`: lint: green (0.0 s)
   `test`: test: green (39.6 s)
6. factory: started doing as self.
7. coder: No code written. This story changes only documentation, and its first criterion forbids changes under `src/`, `tests/`, `image/`, `template/`, `demo/` and `claude/`. I changed nothing in any of those folders or anywhere else. `git status --short` shows only the factory's `.costs.jsonl` sidecar for this work item.
      - Main choice: I left `docs/operator-guide.md` to the documenter stage, as the Interface and `CLAUDE.md` say ("the coder does not write them"). The alternative was to make the criterion-3 edits now, which would mean writing outside the coder's role. I rejected it.
      - `make check`: green (`check: green`, total coverage 99.12 %).
      - Refactor: no diff, so there was nothing to refactor.
      - Description: the journal did not change what the task means, so it is not rewritten.
      - Noticed, not touched: the intake entry reports that `factory/pipeline.yml` on `main` holds `time_limit: 8` for `check`, while the guide's factory-rf block still shows `15`. The documenter has to copy the line exactly as `factory/pipeline.yml` holds it.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   - Diff: `git diff main...HEAD -- . ':!factory'` is empty. Only the work item and its `.costs.jsonl` sidecar changed, so criterion 1 holds: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed. The tester's entry (5) and the coder's entry (7) both say so, as the criterion asks.
   - 1. Acceptance criteria: the story is documentation only and its Interface states no rule, so no test is owed. The journal reports that the factory's `make check` after the coder was green (`check: green`). The `duplicates: 5 new` that the coder recorded cannot come from this branch, because it changes nothing under `src/factory`, so it is not under review.
   - 2 to 4. Architecture, security and quality: nothing to judge on an empty code diff.
   - 5. Work item hygiene: the coder's entry gives the main decision (leave `docs/operator-guide.md` to the documenter) and what it rejected. The Description matches what was built, which is nothing outside the docs. The docs criterion is still accurate. Every passage it names is still on the branch: `docs/operator-guide.md:900` (`lint: {time_limit: 10, not_read: ["factory/*", "docs/*"]}`), `:903` ("List only what the command does not read at all"), `:905` ("after the story that built the key"), `:909` (`check: {time_limit: 15, ...}`) and `:914` ("will run `secrets`"). `factory/pipeline.yml:10` holds `check: {time_limit: 8, not_read: [...]}` with the same `not_read` list. The documenter copies that line.
   - 6. Earlier tests: no test file is changed, renamed or deleted (`git diff --name-status main...HEAD` lists only the two files under `factory/`).
10. factory: started docs as self.
11. documenter: Changed one file, `docs/operator-guide.md`, in *The pipeline definition* (criterion 3). No other passage changed.
    - The first `not_read` example is now `check: {time_limit: 10, not_read: ["README.md", "docs/*.md"]}`. It leaves out file types, not folders.
    - After "List only what the command does not read at all." I added one sentence: a linter, formatter or type checker that walks the whole tree reads every source file in every folder, so leave out file types it does not read, never a whole folder.
    - "factory-rf's own definition takes this after the story that built the key" is now "factory-rf's own definition, `factory/pipeline.yml`, takes this".
    - The `check` line in factory-rf's block now says `time_limit: 8`, the line `factory/pipeline.yml` holds on `main`. Its `not_read` list was already identical.
    - "docs stage will run `secrets`" is now "docs stage runs `secrets`", with the rest of the sentence unchanged.

    Run: `uv run python -m factory.entry.check_documents` printed `documents ok`.

    I did not run `make check`, because I changed only a document under `docs/`; the factory's check after this stage decides. I did not run the smoke-test greps. The edits are exact string replacements, so the old strings are gone and the new `not_read` example appears once.

    I did not cross-read other documents; the story covers one passage. The diff holds no code change, so there is no finding for the coder.

    Stale text noticed and not touched: none.

    `check`: check: green (not run again: passed on tree 3523d622cd0b at 2026-10-19T21:56:48Z)
    `secrets`: secrets: green (0.8 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
