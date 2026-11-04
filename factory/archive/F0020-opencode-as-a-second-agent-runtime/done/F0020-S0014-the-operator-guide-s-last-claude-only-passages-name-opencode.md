---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 299
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T23:13:01.486862Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T23:13:01.492494Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T23:13:20.101165Z'
  stage: intake
  run: 102f8d77503842dcbc5158feaa1df5cf
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T23:13:40.263542Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T23:14:32.037768Z'
  stage: tests
  run: a1cace4b738347cfbb35d180c1715571
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T23:14:52.278234Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T23:15:55.673183Z'
  stage: doing
  run: 0f7bfd1e3f9f41d99e1731c51f115065
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T23:16:15.921191Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T23:16:44.546546Z'
  stage: review
  run: 4c322100d23f46d3a011b2d91d1c7077
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T23:17:04.740268Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T23:17:24.886615Z'
  stage: docs
  run: 6fd60492cc4d47598bea35f34fc6e396
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T23:17:45.125062Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T23:18:05.351944Z'
  stage: smoke-test
  run: f3bd92afdafb4baab17c1614a1c99376
- number: 14
  speaker: factory
  kind: done
  at: '2026-10-19T23:19:24.814948Z'
  stage: approval
---

# The operator guide's last Claude-only passages name opencode

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

S0011 fixed six passages of `docs/operator-guide.md` that spoke of the agent runtime as if Claude Code were the only one. Its documenter saw three more and left them, because the story did not name them, and nobody owns them now. An operator who reads them for an opencode instance gets a half-true picture:

- The guide's opening paragraph lists among the built parts "the `claude -p` runtime" and not the opencode runtime.
- *The agent runs as a second user* says that with `FACTORY_AGENT_USER=agent` "the runtime does not start `claude` itself" and shows a chain that ends in `claude ...`. Under opencode the same chain (`sudo`, `timeout`, `env -i`, `factory-confine`, the login shell) starts `opencode run ...`, and the section does not say so.
- *`factory-guard` on the agent run's `PATH`* says that the runtime registers the guard as a Claude Code hook. It does not say that an opencode run registers no hook, while the preflight's item `agent-environment` still checks that the command is on the `PATH` under either runtime.

This story corrects these three passages. It changes no code and no test, and adds no new section.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `docs/operator-guide.md` only.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`:
   - The opening paragraph names "the `claude -p` and `opencode run` runtimes" where it now names "the `claude -p` runtime".
   - *The agent runs as a second user*: after the sentence that shows the `sudo` chain, one sentence says that under opencode the same chain starts the opencode executable (`FACTORY_OPENCODE`) with `run` and its arguments in place of `claude` (see "Running on opencode"). The documenter checks the words against `docs/project-guide/agents.md` (*The opencode runtime*). The sentence on the `claude` login in `~/.claude` says it concerns Claude Code.
   - *`factory-guard` on the agent run's `PATH`*: one sentence says that an opencode run registers no hook (see "What differs from Claude Code"), and that the item `agent-environment` checks the command on the `PATH` under either runtime. The documenter checks this against `agent_environment_item` (`factory.application.preflight`) and `machine_extras` (`factory.entry.wiring`), which adds the item whatever the runtime.
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c 'the `claude -p` runtime,' docs/operator-guide.md; sed -n '/^### The agent runs as a second user/,/^### The kernel refuses every other write/p' docs/operator-guide.md | grep -c opencode
```
Expect: `0`, then a number of at least `1`

```bash
sed -n '/^### `factory-guard` on the agent run/,/^### A provider/p' docs/operator-guide.md | grep -c opencode
```
Expect: a number of at least `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is stated and fits a docs-only story; it names no module, so there is no signature or comment behaviour to pin. The only symbols it cites (`agent_environment_item` in `factory.application.preflight`, `machine_extras` in `factory.entry.wiring`) are named as sources the documenter checks, not as changes.
   Criteria: criterion 1 (nothing under src, tests, image, template, demo or claude changes) is checked by the diff. Criterion 2 is `make check`. Criterion 3 gives the three passages in the guide, each with the exact sentence to add. The story states no limit, validation, error or default, so there is no failing side to test. No behaviour is left without a criterion.
   Smoke test: I ran the greps' anchors against the guide. The opening paragraph (line 3) contains "the `claude -p` runtime," once, so the first command prints 1 now and 0 after the fix. The headings `### The agent runs as a second user` (line 113), `### The kernel refuses every other write` (143), `### \`factory-guard\` on the agent run's PATH` (216) and `### A provider's spend limit` (220) exist, so both `sed` ranges resolve. The referenced sections "Running on opencode" (260) and "What differs from Claude Code" (281) also exist. Each `Expect:` line is checkable against the output, and `check_documents` prints `documents ok`.
   Architecture: only `docs/operator-guide.md` changes, and it is the documenter's write path. No layer is touched.
   Scope: it is within feature F0020's documentation scope (`docs/operator-guide.md`, from a story's docs criterion). It touches nothing in the feature's Out of scope and changes no test another story wrote.
4. factory: started tests as self.
5. tester: No tests written: this is a docs-only story, its Interface is "None", and criterion 1 forbids any change under `tests/`.
   criterion 1: no test. It is checked by the diff, and this stage changed nothing under src/, tests/, image/, template/, demo/ or claude/.
   criterion 2: no test. It is `make check`, which the factory runs.
   criterion 3: no test. It is the docs criterion for `docs/operator-guide.md`. The smoke test and `check_documents` (the document check) cover it.
   Files created: none. Modules the test run could not import: none, because no new test exists. So the branch has no red tests, and the coder has nothing to implement under `src/`. `make lint` is green. I did not run `make test`, because no test changed.

   `lint`: lint: green (0.0 s)
   `test`: test: green (38.7 s)
6. factory: started doing as self.
7. coder: No code written. This story only changes docs: its Interface is "None", and criterion 1 forbids changes under src/, tests/, image/, template/, demo/ or claude/. This stage changed nothing in those folders, and the working tree holds only the factory's costs sidecar.
   What I built: nothing. The three passages in `docs/operator-guide.md` (the opening paragraph, *The agent runs as a second user*, *`factory-guard` on the agent run's `PATH`*) are the documenter's job under the docs criterion. The coder does not write docs (CLAUDE.md, *Docs*).
   Main choice: hand forward with no change. The alternative I rejected was editing the operator guide here, which is outside the coder's role and would have taken over the documenter's work.
   Refactor: there is no diff, so nothing to refactor.
   The journal did not change what the task means, so the Description stays as it is.
   Noticed but not touched: nothing.
   `make check`: check: green (test: green (39.9 s)).

   `check`: check: green (not run again: passed on tree 5006d1b6db9a at 2026-10-19T23:02:45Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar (`git diff --name-status main...HEAD`), so nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed.
   1. Acceptance criteria: criterion 1 holds, because the diff outside `factory/` is empty. The tester's entry (5) and the coder's entry (7) each say they changed nothing. Criterion 2 holds: the coder's entry records `check: green`. Criterion 3 is the docs criterion, which the documenter writes next. The story states no rule or limit, so no failing side needs a test, and no behaviour was built that would need a new criterion.
   2. Architecture, security and quality: there is no code to judge. `duplicates: 5 new` in entry 7 cannot come from this branch, because the branch changes no file under `src/factory`.
   3. Work item hygiene: entry 7 gives the main decision (hand forward with no change) and the alternative it rejected (editing the guide itself). The Description matches what was built, which is nothing yet. I checked the docs criterion's claims against the code so the documenter starts from correct facts. Each claim below holds:
      - `machine_extras` (`src/factory/entry/wiring.py:409`) adds `agent_environment_item` whatever the runtime, at line 422. Only `opencode_item` depends on `settings.agent_runtime == "opencode"`.
      - `opencode_runtime` registers no hook. It reads `settings.json` only for the `permissions.deny` list.
      - The opencode call is wrapped by `sudo`, `timeout`, `env -i` and `factory-confine` exactly as for `claude -p` (`docs/project-guide/agents.md`, *The opencode runtime*).
      - The target passages exist: line 3 of `docs/operator-guide.md` names "the `claude -p` runtime", line 117 says "does not start `claude` itself", line 137 covers the `claude` login in `~/.claude`, and line 218 says the guard is registered as a Claude Code hook. The anchors "Running on opencode" (260) and "What differs from Claude Code" (281) also exist.

   Earlier tests: none. The diff changes no test file.
10. factory: started docs as self.
11. documenter: Changed `docs/operator-guide.md` only, in the four places the docs criterion names:
    - Opening paragraph: now says "the `claude -p` and `opencode run` runtimes".
    - *The agent runs as a second user*: after the `sudo` chain and the sentence on running without `FACTORY_AGENT_USER`, one sentence says that under opencode the same chain starts the opencode executable (`FACTORY_OPENCODE`) with `run` and its arguments in place of `claude` (see "Running on opencode"). The sentence on the `claude` login in `~/.claude` now says it concerns Claude Code.
    - *`factory-guard` on the agent run's `PATH`*: the hook sentence now names the Claude Code runtime. A new sentence says an opencode run registers no hook (see "What differs from Claude Code") and that the item `agent-environment` checks the command on the `PATH` under either runtime.

    Checked the new words against `docs/project-guide/agents.md` (*The opencode runtime*: `sudo`, `timeout`, `env -i` and `factory-confine` wrap the call as for `claude -p`). The reviewer's entry 9 had already checked `machine_extras` (`src/factory/entry/wiring.py`), which adds `agent_environment_item` whatever the runtime, and that opencode_runtime registers no hook. I did not re-read the code. `FACTORY_OPENCODE` is in the guide's settings table (line 35).

    Ran `uv run python -m factory.entry.check_documents`: `documents ok`. Every file I changed is a document, so I did not run `make check`. The factory's checks decide.

    Cross-read: the rest of the operator guide's passages on the second user and the guard are current against the diff. The diff outside `factory/` is empty, so there was nothing else to compare.

    No findings. Stale text I saw and did not touch: none. One thing for the reader: the login shell in the second-user section is described only for the Claude login. Under opencode it is only for an API login file, per `agents.md`. That is not one of the three passages, so I left it.

    `check`: check: green (not run again: passed on tree 5006d1b6db9a at 2026-10-19T23:02:45Z)
    `secrets`: secrets: green (0.8 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test passed with no findings. I ran the three commands under `## Smoke test` from the repository root, as written and in order. Then I checked the acceptance criteria against `git diff main...HEAD`.

    Command 1: met its Expect (`0`, then a number of at least `1`).
    ```
    0
    1
    ```

    Command 2: met its Expect (a number of at least `1`).
    ```
    1
    ```

    Command 3: met its Expect (`documents ok`).
    ```
    documents ok
    ```

    Acceptance criteria against the branch diff:
    - Criterion 1 holds. The branch changes `docs/operator-guide.md` and, apart from that, only the work item and its `.costs.jsonl` sidecar. Nothing changed under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The tester's entry (5) and the coder's entry (7) each say they changed nothing.
    - Criterion 2: I did not run `make check` in this stage. The factory's recorded result is `check: green` on tree 5006d1b6db9a (entries 7 and 11), and the branch has changed no file outside documents since.
    - Criterion 3 holds:
      - The opening paragraph now names "the `claude -p` and `opencode run` runtimes".
      - *The agent runs as a second user* has one new sentence saying that under opencode the same chain starts the opencode executable (`FACTORY_OPENCODE`) with `run` and its arguments in place of `claude` (see "Running on opencode").
      - The `~/.claude` login sentence now says it concerns Claude Code.
      - *`factory-guard` on the agent run's `PATH`* has one new sentence: an opencode run registers no hook (see "What differs from Claude Code"), and `agent-environment` checks the command on the `PATH` under either runtime. The hook sentence was reworded to "The Claude Code runtime registers it as a hook", which is inside the named passage.
      - No other passage changed (the diff has exactly three hunks of changes, one per named section), and `check_documents` prints `documents ok`.

    Open: the documenter noted that the second-user section describes the login shell only for the Claude login. That passage is outside this story's three, so it is not a finding here.
14. factory: done (pull request merged); cost: 6 runs, 2.4 min, 28 turns, 117517 tokens in (405279 more from cache), 7613 out, $0.93
