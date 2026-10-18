---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 231
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T20:16:45.862815Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T20:16:45.868511Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T20:17:08.179405Z'
  stage: intake
  run: 844ab25542b1472cacced9ccd906d55a
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T20:17:27.845408Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T20:18:28.252181Z'
  stage: tests
  run: 7e234a1e2ba042ac917e23bcaa186b42
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-18T20:18:48.606730Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-18T20:20:28.394991Z'
  stage: doing
  run: 20d938c08bf146b8acd211fc4284fa11
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-18T20:20:48.217591Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-18T20:21:10.273517Z'
  stage: review
  run: 87ab110ee72440c498ea3b63646257b2
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-18T20:21:30.744170Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-18T20:22:31.353363Z'
  stage: docs
  run: 2c1bfc39bd9949c8b163cd8ef741832c
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-18T20:22:51.436219Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-18T20:23:14.766419Z'
  stage: smoke-test
  run: 8c35133d8ba94818ba608db971c9d33c
---

# The project guide's start wrapper section says the runtime starts it

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

F0019's second acceptance read the documents as a whole and found one stale sentence that two documenters had already noticed (S0007's entry 11 and S0009's entry 11). Neither could change it, because their criteria said "no other passage changes". `docs/project-guide.md`, section *The start wrapper*, ends its first paragraph with "Nothing starts it yet: the runtime will." Since S0004, `ClaudeCodeRuntime` has started every agent run through `factory-confine` when it is built with `confine_executable`, and `build_boundaries` builds it that way by default. `docs/operator-guide.md` (*The agent runtime*) and `README.md` already say so. The same section's second paragraph describes `confinement_item`, the preflight item. S0007's criterion placed it in *The kernel's write guard*, and its reviewer and smoke tester passed it where it landed. This story replaces the stale sentence with one that is true and points to where the runtime builds the command, and it moves the `confinement_item` paragraph, unchanged, to the end of *The kernel's write guard*. It is documentation only: no code, test, template or agent file changes.

## Interface

None: no module under `src/factory/`, no test, no image, template, demo or agent file changes. The documenter changes `docs/project-guide.md` only.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/project-guide.md`, section *The start wrapper*, first paragraph: the sentence "Nothing starts it yet: the runtime will." becomes a sentence saying that `ClaudeCodeRuntime` starts every agent run through it when built with `confine_executable`, which `build_boundaries` passes by default, and that the command line is in *The `claude -p` runtime*. The paragraph that begins "`confinement_item(abi, environment, find)`" moves, word for word, from *The start wrapper* to the end of *The kernel's write guard*. No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "Nothing starts it yet" docs/project-guide.md
```
Expect: `0`

```bash
sed -n '/^## The start wrapper/,/^### /p' docs/project-guide.md | grep -c "confine_executable"
```
Expect: `1`

```bash
sed -n '/^## The start wrapper/,$p' docs/project-guide.md | grep -c "^\`confinement_item(abi, environment, find)\`"; sed -n '/^## The kernel.s write guard/,/^## The start wrapper/p' docs/project-guide.md | grep -c "^\`confinement_item(abi, environment, find)\`"
```
Expect: `0`, then `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is correct for a documentation-only story. It names no module and states no behaviour or rule, so nothing needs a criterion. It limits the documenter to `docs/project-guide.md`.
   - Criteria: three, each checkable. (1) No change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` is checkable from the diff. (2) `make check` is the closing criterion. (3) The docs criterion names the stale sentence, which I confirmed at line 1335 of `docs/project-guide.md`. It also names the replacement's content (`ClaudeCodeRuntime`, `confine_executable`, the `build_boundaries` default, the pointer to *The `claude -p` runtime*) and the paragraph to move, which I confirmed at line 1337 and which currently sits in *The start wrapper*. The destination, the end of *The kernel's write guard*, begins at line 1300. The criterion ends with `documents ok`. The story states no limits or error rules, so there is no failing side to cover.
   - Smoke test: all four commands are runnable. I checked the sed ranges against the current headings. After the edit, `confine_executable` appears only on the new sentence's line in the start wrapper range, because the paragraph is a single line. The `confinement_item` paragraph is one line too, so the count of 0 in the start wrapper range and 1 in the write guard range is checkable. Each `Expect:` line gives an exact value.
   - Architecture: it fits. It changes only the project guide, which the documenter owns. The facts it states match the guide's own *Confinement* paragraph (line 327), the operator guide and the README.
   - Scope: it matches the feature's scope ("`docs/project-guide.md` ... from each story's docs criterion"). It touches nothing in "Out of scope" and removes the stale-text note raised by S0007 and S0009.
4. factory: started tests as self.
5. tester: No tests written, because this is a documentation-only story. The Interface is "None" and no criterion states a behaviour that a test under `tests/` could check.
   - criterion 1: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed in this stage. I created and changed no files. That is checkable from the branch diff, not by a test.
   - criterion 2: `make check` is the factory's gate and has no test function. `make lint` is green.
   - criterion 3 (docs): the documenter's work on `docs/project-guide.md`. The check is `python -m factory.entry.check_documents` (`documents ok`) and the story's smoke test, not a pytest test.
   Files created: none. Modules the test run could not import: none. No new tests exist, so there are no red tests for the coder. The coder's stage has nothing to implement under `src/` and should only confirm criterion 1 in its entry.

   `lint`: lint: green (0.0 s)
   `test`: test: green (42.5 s)
6. factory: started doing as self.
7. coder: Nothing to build. This story only changes documentation, and the documenter edits `docs/project-guide.md` in a later stage.
   - criterion 1: I changed nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The tester added no tests, so no test was failing. `git status --short` shows only the work item's `.costs.jsonl` sidecar, which the factory writes.
   - criterion 2: `make check` is green (`check: green`, coverage 98.80 %).
   - Main choice: I made no code change. The other option was to edit `docs/project-guide.md` myself, and I rejected it: CLAUDE.md gives the docs to the documenter stage, and the story's Interface names the documenter as the only one who changes that file.
   - Refactor: no diff, so nothing to refactor.
   - The journal did not change what the task means, so the Description stays as it is.
   - Noticed but did not touch: nothing.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item's `.md` and adds its `.costs.jsonl` sidecar. Criterion 1 holds: nothing changed under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`.
   - Criterion 2: entry 7 records `check: green` after the coder, and `duplicates` reports 0 new findings.
   - Criterion 3, the docs criterion: it is still the documenter's work, and it matches the code and the guide as they stand.
     - `ClaudeCodeRuntime` starts each call through `confine_executable` when it is given (`src/factory/adapters/claude_runtime.py:454-465`, `:561`, `:577`).
     - `build_boundaries` defaults it to `CONFINE_COMMAND` (`src/factory/entry/wiring.py:233`).
     - The stale sentence is at `docs/project-guide.md:1335`, and the paragraph to move is at `:1337`. The target sections exist: *The kernel's write guard* at `:1300` and *The `claude -p` runtime* at `:302`.
   - Work item hygiene: entry 7 gives the main choice, no code change, and what it rejected, the coder editing the guide itself. The Description matches what was built, which is nothing yet.
   - Earlier tests: no test file that `main` holds is changed, renamed or deleted.
10. factory: started docs as self.
11. documenter: Changed one file: `docs/project-guide.md`.
    - *The start wrapper*, first paragraph: "Nothing starts it yet: the runtime will." now says that `ClaudeCodeRuntime` starts every agent run through `factory-confine` when it is built with `confine_executable`, which `build_boundaries` passes by default, and that the command line is in "The `claude -p` runtime".
    - The `confinement_item(abi, environment, find)` paragraph moved word for word from *The start wrapper* to the end of *The kernel's write guard*, after its *Tests* subsection.

    No other passage changed.

    Checks I ran:
    - `uv run python -m factory.entry.check_documents` prints `documents ok`.
    - `grep -c "Nothing starts it yet" docs/project-guide.md` gives 0.
    - I did not run the smoke test's other three commands. The moved paragraph is a single line that begins with the quoted text, and I saw it at the end of the write guard section.
    - I did not run `make check`, because I changed only a document. The factory's check after this stage is the gate.

    Cross-read and found current: the first paragraph of *The kernel's write guard*, which already says the runtime starts every agent run through the wrapper. I did not re-read `docs/operator-guide.md` or `README.md`: the story says they already agree, and the diff changes no code. I made no code-versus-docs comparison, because the diff has no code.

    Findings for the coder: none. Stale text noticed but not touched: nothing.

    `check`: check: green
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test passed: I ran all four commands from the repository root as written, in order, and all four met their `Expect:` lines. There are no findings. I fixed nothing.

    1. `grep -c "Nothing starts it yet" docs/project-guide.md`
    ```
    0
    ```
    Expect `0`: met.

    2. `sed -n '/^## The start wrapper/,/^### /p' docs/project-guide.md | grep -c "confine_executable"`
    ```
    1
    ```
    Expect `1`: met.

    3. `sed -n '/^## The start wrapper/,$p' ... | grep -c "^\`confinement_item(abi, environment, find)\`"; sed -n '/^## The kernel.s write guard/,/^## The start wrapper/p' ... | grep -c ...`
    ```
    0
    1
    ```
    Expect `0`, then `1`: met.

    4. `uv run python -m factory.entry.check_documents`
    ```
    documents ok
    ```
    Expect `documents ok`: met.

    Checked against the acceptance criteria:
    - Criterion 1: met. `git diff --stat main...HEAD` lists only three files: `docs/project-guide.md`, the work item's `.md` and its `.costs.jsonl` sidecar. Nothing changed under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`.
    - Criterion 2: I did not run `make check` in this stage. Entries 7 and 11 record `check: green`, and the factory runs the check itself.
    - Criterion 3: met. In the diff of `docs/project-guide.md`, the stale sentence is replaced by one that names `ClaudeCodeRuntime`, `confine_executable`, the `build_boundaries` default and the section "The `claude -p` runtime". The removed and the added `confinement_item(abi, environment, find)` lines are identical. The moved paragraph now sits directly before `## The start wrapper`, after the *Tests* text, which is the end of *The kernel's write guard*. The diff changes no other passage.

    The smoke test contradicts no criterion. Open: nothing.
