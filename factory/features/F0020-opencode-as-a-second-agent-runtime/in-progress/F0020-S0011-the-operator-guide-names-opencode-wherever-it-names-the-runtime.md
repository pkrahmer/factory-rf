---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 280
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T19:08:38.014815Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T19:08:38.021500Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T19:09:01.860400Z'
  stage: intake
  run: 1954926014f04202a4728400b340dfdc
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T19:09:22.418535Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T19:11:14.011588Z'
  stage: tests
  run: 001ce14c6be444bfa9860773496b90c6
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T19:11:35.643326Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T19:12:53.263834Z'
  stage: doing
  run: 6a908e56d8d344909a2f95f4f72d8f9e
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T19:13:14.119943Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T19:13:28.960158Z'
  stage: review
  run: 04dd7b7527494015ab915528d665aa37
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T19:13:49.750625Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T19:14:21.703504Z'
  stage: docs
  run: 3b6072a462e043dbb6266cf6753e44c7
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T19:14:42.602822Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T19:15:03.629878Z'
  stage: smoke-test
  run: 32d404772e59488d989c5b29c4332a26
---

# The operator guide names opencode wherever it names the runtime

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0020 added a section on running on opencode to `docs/operator-guide.md`. The guide's older passages still speak of the agent runtime as if Claude Code were the only one, and an operator who reads them for an opencode instance is sent the wrong way:

- *The agent runtime* opens with "The factory runs each agent as a `claude -p` call".
- The configuration table calls `FACTORY_CLAUDE` "The agent runtime's executable" and `FACTORY_CLAUDE_VERSION` "The version of the agent runtime the image pins".
- *The kernel refuses every other write* names `~/.claude` as "the runtime's own folder" and not opencode's three folders.
- *The machine's image* lists Claude Code, `uv` and the Debian tools as its pinned versions and leaves out opencode.
- *Update the pins* has no line for `OPENCODE_VERSION`, though *Running on opencode* sends the operator there ("Change both together, as for Claude Code (see "Update the pins")"). It does not say that the models in `image/Dockerfile`, the compose defaults of `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` in `image/compose.yml` and the pins of `tests/test_opencode_image.py` must change with it.
- The preflight's closing paragraph names only `FACTORY_CLAUDE_HOME`, `FACTORY_CLAUDE` and `FACTORY_CLAUDE_VERSION` as the variables to check first.

The documenter of S0008 noticed the pins and left them; nobody owned them. This story corrects these passages. It changes no code and no test, and adds no new section.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `docs/operator-guide.md` only.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`:
   - *The agent runtime*: the opening sentence says that the factory runs each agent as a `claude -p` call under Claude Code, or as an `opencode run` call under opencode (see "Running on opencode"). The passage that follows stays about Claude Code and says so.
   - Configuration table: `FACTORY_CLAUDE` is "Claude Code's executable, used when the runtime is `claude`". `FACTORY_CLAUDE_VERSION` is "the version of Claude Code the image pins", and the preflight fails without it only under Claude Code.
   - *The kernel refuses every other write*: the bullet on `~/.claude` says it is Claude Code's own folder. A bullet beside it names opencode's three folders (`.local/share/opencode`, `.local/state/opencode`, `.cache/opencode`) and the folders of `FACTORY_OPENCODE_FOLDERS`, which an opencode run may write instead.
   - *The machine's image*: the opening paragraph names opencode among the pinned tools.
   - *Update the pins*: a bullet for opencode. It names the `OPENCODE_VERSION` default and the `FACTORY_OPENCODE_MODELS` value in `image/Dockerfile` and the defaults of `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` in `image/compose.yml`, which change with it; says to check the model ids with `opencode models anthropic`; and says that `tests/test_opencode_image.py` pins the version and the model ids as well, so it changes with them and is run with `tests/test_image.py`.
   - The preflight's closing paragraph names `FACTORY_OPENCODE`, `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` as the variables to check first under opencode.
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "The agent runtime's executable" docs/operator-guide.md; sed -n '/^### Update the pins/,/^### Claude Code/p' docs/operator-guide.md | grep -c "OPENCODE_VERSION"
```
Expect: `0`, then a number of at least `1`

```bash
grep -c "the runtime's own folder" docs/operator-guide.md; grep -c ".local/state/opencode" docs/operator-guide.md
```
Expect: `0`, then a number of at least `2`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: it says "None" and names no module. That fits a docs-only story; it states no conversion, format, ordering or default of its own.
   - Criteria: criterion 1 (nothing outside the guide changes) and criterion 2 (`make check`) are each testable. The docs criterion lists one concrete edit per passage, each with the exact phrase or value to use. It states no limit, validation or rejected input, so no failing side is owed. The guide's headings match the passages the story names: *The agent runtime*, *The kernel refuses every other write*, *The machine's image*, *Update the pins*, and the preflight section.
   - Smoke test: all three blocks run as written. I checked the current counts in `docs/operator-guide.md` and the headings the `sed` range uses. "The agent runtime's executable" appears once and "the runtime's own folder" appears once, so the Expect values of `0` are reachable by the edit. `.local/state/opencode` appears once now, so the Expect of at least `2` needs the new bullet to mention it, as criterion 3 requires. `### Update the pins` and `### Claude Code` both exist, in that order, so the `sed` range is valid. Each `Expect:` line is a number or a string that the output can be checked against.
   - Architecture: the story changes only `docs/operator-guide.md`, which is the documenter's write path. It touches no layer, no code and no test. It names `tests/test_opencode_image.py` and `image/` only as text for the guide to cite.
   - Scope: F0020's scope lists `docs/operator-guide.md` under each story's docs criterion. The story adds no new section and does not touch Out of scope items. It corrects older passages that S0008's `Running on opencode` section left inconsistent.
4. factory: started tests as self.
5. tester: No tests written: this story is docs-only. Its Interface is "None", and criterion 1 says no test changes.
   - criterion 1 (nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes): I created and changed no file under any of those folders. `git status` shows only the work item's `.costs.jsonl` sidecar, which the factory writes.
   - criterion 2 (`make check` stays green): this is the stage gate, not a test. I ran `make test` once and it passed with no new tests (`test: green`, coverage 99.12 %). `make lint` passed as well.
   - criterion 3 (docs, `docs/operator-guide.md`): the documenter owns this criterion. The smoke test and `uv run python -m factory.entry.check_documents` check it. There is no test, because writing one would break criterion 1.
   Files created: none. Modules the test runner could not import: none. Since nothing new is red, the coder has no tests to turn green; the remaining work is the documenter's edit of `docs/operator-guide.md`.

   `lint`: lint: green (0.0 s)
   `test`: test: green (47.8 s)
6. factory: started doing as self.
7. coder: No code written: the story is docs-only. Its Interface is "None", and criterion 1 says no file changes under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`.
   - criterion 1: I created and changed no file under any of those folders, and no test. `git status --short` shows only the work item's `.costs.jsonl` sidecar, which the factory writes.
   - criterion 2: `make check` ends `check: green` (test: green, coverage 99.12 %).
   - criterion 3 (the docs criterion): the documenter edits `docs/operator-guide.md`. It is outside the coder's write paths and the coder does not write the docs.
   Main choice: hand forward with no change. I rejected touching `docs/operator-guide.md` from this stage: CLAUDE.md gives the docs to the documenter. Refactor step: there is no diff to refactor. The journal did not change the meaning of the Description. I noticed nothing else and left nothing open.

   `check`: check: green (not run again: passed on tree 5e9e997b80f0 at 2026-10-19T19:01:37Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar (`git diff --name-status main...HEAD`), as expected for a story that only changes docs.
   - Item 1 (acceptance criteria): criterion 1 holds. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes, and the tester (entry 5) and the coder (entry 7) each say so. Criterion 2 holds: the coder's entry 7 carries `check: green`, a reused pass on tree 5e9e997b80f0, and that tree holds no change to anything `make check` reads. Criterion 3 is the docs criterion and belongs to the documenter, who comes next. The Interface states no rule or limit, so no failing side is owed. There is no mutation report line, because no module changed.
   - Item 2 (architecture), item 3 (security) and item 4 (quality): there is no code or test in the diff to judge. The coder's `duplicates: 5 new` cannot come from this branch, since it changes nothing under `src/factory`. They are findings already on `main` and outside this review's scope.
   - Item 5 (work item hygiene): the coder's entry gives the main choice (hand forward with no change) and what was rejected (editing `docs/operator-guide.md` from the doing stage). The Description still matches the work. The docs criterion names each passage and the exact wording the documenter must write.
   - Item 6 (earlier tests): no test file that `main` holds is changed, renamed or deleted.
10. factory: started docs as self.
11. documenter: Changed `docs/operator-guide.md` only, in the six passages the docs criterion lists:
    - Configuration table: `FACTORY_CLAUDE` is now "Claude Code's executable, used when the runtime is `claude`". `FACTORY_CLAUDE_VERSION` is "the version of Claude Code the image pins", and the preflight fails without it only under Claude Code.
    - *The agent runtime*: the opening sentence now says `claude -p` under Claude Code or `opencode run` under opencode (see "Running on opencode"), and that the rest of the passage is about Claude Code.
    - *The kernel refuses every other write*: the `~/.claude` bullet says it is Claude Code's own folder. A new bullet beside it names opencode's three folders and the folders of `FACTORY_OPENCODE_FOLDERS`, which an opencode run may write instead.
    - *The machine's image*: the opening paragraph lists opencode among the pinned tools.
    - *Update the pins*: a new opencode bullet. It names the `OPENCODE_VERSION` default and the `FACTORY_OPENCODE_MODELS` value in `image/Dockerfile`, and the defaults of `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` in `image/compose.yml`. It says to check the model ids with `opencode models anthropic`, and that `tests/test_opencode_image.py` pins the version and model ids too, so it changes with them and runs with `tests/test_image.py`.
    - The preflight's closing paragraph names `FACTORY_OPENCODE`, `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` as the variables to check first under opencode.

    I checked the new text against `image/Dockerfile` and `image/compose.yml`: the variable names and defaults match. `uv run python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, because only a document changed; the factory's check runs after this stage.

    Cross-read and found current: *Running on opencode* (including its "Update the pins" reference), the preflight items table, and *What opencode keeps in the agent's home*.

    Stale text I saw and left, because this story does not cover it:
    - Line 3 (the guide's intro) still describes the built parts as "the `claude -p` runtime".
    - Several passages are written only for Claude Code: *The agent runs as a second user*, the `claude-home` volume text, and *`factory-guard` on the agent run's `PATH`*, which calls the guard "a Claude Code hook".

    No findings for the coder.

    `check`: check: green (not run again: passed on tree 5e9e997b80f0 at 2026-10-19T19:01:37Z)
    `secrets`: secrets: green (1.0 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: I ran the three smoke test commands as written, in order, from the repository root. All three met their `Expect:` lines. I found nothing to report.

    1. Stale label gone, opencode pin added:
    ```
    0
    1
    ```
    Met. `Expect: 0, then a number of at least 1`.

    2. Stale folder wording gone, opencode state folder named twice:
    ```
    0
    2
    ```
    Met. `Expect: 0, then a number of at least 2`.

    3. `uv run python -m factory.entry.check_documents`:
    ```
    documents ok
    ```
    Met. `Expect: documents ok`.

    Checking against the acceptance criteria: I read `git diff main -- . ':!factory'`. It changes only `docs/operator-guide.md` (8 insertions, 6 deletions), so criterion 1 holds: nothing changed under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The diff covers every bullet of criterion 3, and nothing else in the guide changed:
    - *The agent runtime* now opens with `claude -p` under Claude Code or `opencode run` under opencode. The rest of that passage stays about Claude Code and says so.
    - The configuration table has the new text for `FACTORY_CLAUDE` and `FACTORY_CLAUDE_VERSION`.
    - The `~/.claude` bullet now calls it Claude Code's own folder, and a new bullet beside it names opencode's three folders and `FACTORY_OPENCODE_FOLDERS`.
    - *The machine's image* now lists opencode among the pinned tools.
    - *Update the pins* has a new opencode bullet with everything the criterion asks for.
    - The preflight's closing paragraph now names the three `FACTORY_OPENCODE*` variables.

    I did not run `make check` (criterion 2). This stage does not run it, and the smoke test does not contradict it.

    Open: the documenter's entry lists some stale Claude-only wording that this story does not cover: the guide's intro line, *The agent runs as a second user*, the `claude-home` volume text, and *`factory-guard` on the agent run's `PATH`*. That is a candidate for a later story; it is not a finding here.
