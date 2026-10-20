---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 305
comments_read: []
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-20T00:09:00.189530Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T00:04:19.808772Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T00:04:19.815448Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T00:04:39.455547Z'
  stage: intake
  run: 9d1da6c545b64bab91b4c805a0b98878
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T00:05:00.575698Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T00:06:30.702809Z'
  stage: tests
  run: 6d125f7d99a74557a3c6a874653c4a6e
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T00:06:51.277228Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T00:07:53.088847Z'
  stage: doing
  run: adee967a81d64392892fc6fabc934758
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T00:08:13.849524Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T00:08:38.155102Z'
  stage: review
  run: 7bc3a2e2539449f6bbc632dd8c8c62a1
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T00:09:00.189530Z'
  stage: docs
---

# The second-user section names the API login and opencode's run files

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

S0014 fixed three passages of `docs/operator-guide.md` that spoke only of Claude Code. Its documenter noticed one more in the section *The agent runs as a second user*, and it was not one of the story's three. Two paragraphs of that section are still written for Claude Code on the subscription only, and one sentence now contradicts the guide's own section on the login shell:

- The `sudo` paragraph says that `env -i` passes the runtime's "three switches and, from the login shell, `CLAUDE_CODE_OAUTH_TOKEN`". It also says "The login shell is there only when `FACTORY_CLAUDE_LOGIN_FILE` is set; it `exec`s `claude`". Since S0001 the login shell also starts when `FACTORY_API_LOGIN_FILE` is set, and it then hands over `ANTHROPIC_API_KEY`. The guide's list of login-shell points says this, as does `docs/project-guide/agents.md`, which also says that an opencode run's login shell comes from the API login file only. Under opencode, the call's environment holds `OPENCODE_CONFIG` and one switch (`PYTHONDONTWRITEBYTECODE`), not Claude Code's three.
- The paragraph on the files of a run names `instructions-<session>.md`, `guard-<session>.json` and `hooks-<session>.json`. An opencode run writes `opencode-<run>.json` (its per-run configuration, mode `0640`) beside its confinement rules instead.

An operator who sets up an opencode instance on an API key would read in this section that the key cannot reach the agent. This story corrects these two paragraphs. It changes no code and no test, and adds no section.

## Interface

None. No module under `src/factory/` changes, and no test, image, template or agent file. The documenter changes `docs/operator-guide.md` only.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, section *The agent runs as a second user*:
   - The sentence on what `env -i` lets through names, from the login shell, `CLAUDE_CODE_OAUTH_TOKEN`, or `ANTHROPIC_API_KEY` when an API key is in force. It names the switches as the runtime's own: Claude Code's three with `CLAUDE_CONFIG_DIR` (set for a confined run with a `HOME`, as every run in the image is), or, under opencode, `PYTHONDONTWRITEBYTECODE` with `OPENCODE_CONFIG`.
   - The sentence "The login shell is there only when `FACTORY_CLAUDE_LOGIN_FILE` is set; it `exec`s `claude`" is replaced. The new text says the login shell is there when `FACTORY_CLAUDE_LOGIN_FILE` or `FACTORY_API_LOGIN_FILE` is set (under opencode, only the API login file counts), and that it `exec`s the runtime's executable, so `timeout`'s kill still reaches it.
   - The paragraph on the files of a run says that an opencode run writes `opencode-<run>.json` (its per-run configuration, mode `0640`) in place of the instructions, guard and hooks files (see "Running on opencode").
   - The documenter checks each claim against `docs/project-guide/agents.md` (*The shared launch module*, *The opencode runtime*), `SWITCHES` and `CONFIG_VARIABLE` in `factory.adapters.opencode_runtime` and in `factory.adapters.claude_runtime` (with `_config_folder`), and `login_argv` in `factory.adapters.agent_launch`.
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c 'The login shell is there only when `FACTORY_CLAUDE_LOGIN_FILE` is set;' docs/operator-guide.md
```
Expect: `0`

```bash
s=$(sed -n '/^### The agent runs as a second user/,/^### The kernel refuses every other write/p' docs/operator-guide.md); printf '%s\n' "$s" | grep -c 'FACTORY_API_LOGIN_FILE'; printf '%s\n' "$s" | grep -c 'ANTHROPIC_API_KEY'; printf '%s\n' "$s" | grep -c 'opencode-<run>.json'
```
Expect: three lines, each a number of at least `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is right for a docs-only story. It says no module, test, image, template or agent file changes, and only `docs/operator-guide.md` changes. There is no signature or comment behaviour to pin.
   - Criteria: criterion 1 (nothing outside docs changes) is a statement about the diff, not a test function; the tests stage can only confirm it by writing no tests, which it already has to say in its entry. Criterion 2 is `make check` and criterion 3 is the docs criterion, both in the closing positions. The docs criterion lists each claim to change: the `env -i` sentence with both logins and both runtimes' switches, the login-shell sentence with both login files, the opencode-only API login file and the `exec` of the runtime's executable, and the run-files paragraph with `opencode-<run>.json` (mode `0640`). It also names the sources to check each claim against. No Interface rule is stated, so no failing side is needed. Each behaviour in the Description has a criterion.
   - Smoke test: the three blocks are runnable. The section's start and end headings exist in `docs/operator-guide.md` (lines 113 and 143), and the old sentence is on line 117. Each `Expect:` line can be checked against the output: `0`, three numbers of at least 1, and `documents ok`.
   - Architecture: nothing under `src/` changes, so the four layers are untouched. The change falls within the documenter's write paths (`docs/*`).
   - Scope: it is inside F0020's scope ("`docs/operator-guide.md` ... from each story's docs criterion"). Nothing in the story touches an "Out of scope" item. It changes no test written by another story.
4. factory: started tests as self.
5. tester: No tests written: this story only changes docs, and its Interface is "None".
   - criterion 1 (nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes): no test function. That is a fact about the diff. This stage changed nothing under `tests/` or anywhere else (`git status` shows only the factory's costs sidecar).
   - criterion 2 (`make check` stays green): no test function. It is the check itself. `make test` was green (coverage 99.13 %) and `make lint` was green before the hand-forward.
   - criterion 3 (docs, `docs/operator-guide.md`): no test function. It is the documenter's criterion, checked by the smoke test and by `make documents`.
   Files created: none. Modules the test run could not import: none. There are no red tests on this branch, because nothing here specifies code for the coder. Their work is to confirm that nothing outside the docs changes.

   `lint`: lint: green (0.0 s)
   `test`: test: green (37.1 s)
6. factory: started doing as self.
7. coder: No code written: this story only changes docs. Its Interface is "None", and the tester left no red tests.
   - Criterion 1: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. This stage changed no file. `git status --short` shows only the factory's own costs sidecar.
   - Criterion 2: I ran `make check` in the foreground and it was green (`test: green (40.0 s)`, coverage 99.13 %, `check: green`).
   - Criterion 3 is for the documenter: it changes `docs/operator-guide.md`, section *The agent runs as a second user*. The coder does not write docs.
   Main choice: hand forward with no change. The alternative I rejected was editing the operator guide in this stage, because docs are outside the coder's work under `CLAUDE.md` *Docs*. Refactor step: there is no diff, so there was nothing to refactor. The journal did not change what the task means, so `## Description` is unchanged. I noticed nothing that I left untouched.

   `check`: check: green (not run again: passed on tree 7897e571521e at 2026-10-19T23:58:37Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its costs sidecar, both under `factory/`. So criterion 1 holds: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester (entry 5) and the coder (entry 7) each said so.
   - Criterion 2: the coder's entry 7 records `check: green` (coverage 99.13 %). I did not run `make check` again, as the stage says.
   - Criterion 3 (docs) is the documenter's work. I checked its claims against the code so the documenter starts from correct facts, and they match:
     - The opencode runtime's `CONFIG_VARIABLE = "OPENCODE_CONFIG"` and `SWITCHES = {"PYTHONDONTWRITEBYTECODE": "1"}` are at `src/factory/adapters/opencode_runtime.py:74,79`.
     - Its run file `opencode-{run}.json` is at `:250`, set to `RUN_FILE_MODE` at `:629`.
     - Claude Code's three `SWITCHES` and `CONFIG_VARIABLE = "CLAUDE_CONFIG_DIR"`, set through `_config_folder`, are at `src/factory/adapters/claude_runtime.py:88-97,537`.
     - `login_argv` at `src/factory/adapters/agent_launch.py:116` starts the login shell when either login file is set.
   - Hygiene: the Interface says "None", which fits a docs-only story. Entry 7 states the main choice (hand forward with no change) and what it rejected (editing the guide in the coder stage). The Description matches what was built, which is nothing outside `factory/`.
   - `duplicates: 5 new` (entry 7) comes from code already on `main`. This branch changes nothing under `src/`, so those findings are outside this review.

   Earlier tests: none. The diff changes, renames or deletes no test file.
10. factory: started docs as self.
