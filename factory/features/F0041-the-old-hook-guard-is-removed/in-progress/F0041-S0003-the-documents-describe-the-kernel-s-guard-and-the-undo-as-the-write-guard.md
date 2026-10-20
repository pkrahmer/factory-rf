---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 349
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T11:34:44.716396Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T11:34:44.722075Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T11:35:06.025413Z'
  stage: intake
  run: aa91e10b7b8d46938870c13728707db0
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T11:35:26.412879Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T11:40:17.333198Z'
  stage: tests
  run: ecc7c5e076cf4d5c91c4c30f9d59e97d
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T11:40:38.700979Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T11:45:36.765264Z'
  stage: doing
  run: d26feb45b3294fd4b18607759c89733e
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T11:45:57.376677Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T11:46:20.386895Z'
  stage: review
  run: 4eaf986b57be484485ce97130820fcab
---

# The documents describe the kernel's guard and the undo as the write guard

## Description

S0001 stopped registering the Claude Code hook `factory-guard`, and S0002 removed its command, its adapter, `GUARD_COMMAND`, `GuardSettings.temporary_directory` and the preflight's search for it. The documents still describe the hook in about a dozen places: the README's list of commands, the operator guide's section on `factory-guard` on the agent run's `PATH`, its preflight row `agent-environment` and its passages on the kernel's targets, the probe and a project's own skills, and the project guide's write-guard, agents, watching and index files. This story makes them say what is true after S0002: every agent run is guarded by the kernel (`factory-confine`, Landlock) during the run and by the undo after it, under either runtime; nothing judges a tool call; a protected path inside a folder a write path opens is written and then reverted by the undo (the feature's decision 6). The decision log gains one entry for the removal, and the older entries it supersedes each gain one line naming it. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes `README.md`, `docs/operator-guide.md`, `docs/project-guide/README.md`, `docs/project-guide/write-guard.md`, `docs/project-guide/agents.md`, `docs/project-guide/watching.md` and `docs/decisions.md`, as criterion 3 lists.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `README.md`, *Getting started*: "Seven commands exist" becomes "Six commands exist", and the closing clause names only `factory-confine` ("the agent runtime runs `factory-confine` to start every agent run with its writes confined by the kernel"). If F0038-S0002's table of commands is on `main` by then, its `factory-guard` row is deleted instead and the table has six rows (the feature's decision 11).
   - `docs/operator-guide.md`: the opening paragraph names `factory-confine` alone as the command the agent runtime runs. The section *`factory-guard` on the agent run's `PATH`* becomes *The agent run's `PATH` and `HOME`*: it keeps the allow list of six names, the `PATH` of the directory where the factory's console scripts, `factory-confine` among them, are installed followed by `/usr/local/bin:/usr/bin:/bin`, the `HOME` (the agent user's home when `FACTORY_AGENT_USER` is set), and the rule that the tools an agent needs must be in one of those four directories; it names no hook and no guard command, and no other section links to the old title. In *The agent runs as a second user*, the files of a run are `instructions-<session>.md` and, with confinement, `confine-<session>.json` (no guard or hooks file), and an opencode run's `opencode-<run>.json` is written in place of the instructions file. The preflight table's row `agent-environment` says the item checks that the agent run's `HOME` is an existing directory, with the faults `the agent run has no HOME` and `the agent run's HOME <dir> is no directory`. In *What differs from Claude Code*, the bullet "No hook. ..." becomes one that keeps only its second fact: the denied commands of `settings.json` become `deny` permissions in the run's own configuration file. The passage on the kernel's targets says that the undo after the run judges the exact write paths (not "the hook and the undo"). *The kernel refuses every other write* says there is no fallback without naming a hook. In *The pipeline definition*, the tool paths widen what the kernel allows only, and the undo still judges the write paths alone. *A project's own skills* says that the undo removes a nested `.claude/` write after every run, under either runtime, and that the kernel cannot refuse it inside a folder a write path opens (it no longer names a hook). The `preflight_failed` row keeps "there is no fallback" without "to the hook".
   - `docs/project-guide/write-guard.md`: the section *The guard command* is deleted, with its test list. *The write paths* says the decision is made in one place for the undo (and, through the targets, the kernel); every "the hook and the undo" becomes "the undo", "never what the hook or the undo accept" becomes "never what the undo accepts", and *Protected paths and the refusal* loses the sentence on how the guard hook resolves the path it judges (the undo takes git's paths as they are). *The undo* says the kernel refuses during the run and the undo reverts what the kernel allowed outside the write paths after it (a protected path inside an allowed folder, a file the targets widened to its folder). *The kernel's write guard* no longer refers to "The guard command".
   - `docs/project-guide/agents.md`, *The `claude -p` runtime*: the argument block and the sentence after it name no `--settings`; the list of files under `state_directory` holds `instructions-<session>.md` and, with `confine_executable`, `confine-<session>.json`, and no guard or hooks file; the environment paragraph names no `factory-guard`; the sentence on `RUN_FILE_MODE` names the instructions and rules files.
   - `docs/project-guide/watching.md`: `production_environment()` is said to use the directory where the console scripts, `factory-confine` among them, are installed; the preflight step names `agent_environment_item(environment, is_directory)`.
   - `docs/project-guide/README.md`: the entry `guard_support.py` among the shared test helpers is deleted; the line on `write-guard.md` names neither `factory.adapters.claude_guard` nor `factory.entry.guard`, and its list of sections no *The guard command*; the paragraph on `extra="ignore"` models says "There are twelve" and names `_Usage`, `_Denial`, `_StructuredOutput` and `_Reply` in `factory.adapters.claude_runtime` and `_Event`, `_Part`, `_Tokens`, `_CacheTokens`, `_ToolState`, `_Span`, `_Error` and `_ErrorData` in `factory.adapters.opencode_runtime` (the list of `tests/test_model_configuration.py` after S0002).
   - `docs/decisions.md`: a new entry *The Claude Code hook is removed; the kernel and the undo are the write guard*, dated with the story, from the feature's decisions 2, 3, 5 and 6 and F0019's decision 16. Its reasons: the cross-check of 2026-10-19 (405 transcripts, no refusal of the hook in the 264 runs after the kernel guard went live, the one disagreement fixed by F0019-S0011); the hook saw two tools only; opencode runs had no hook already. It rejects a reduced hook for the protected paths only. The entries *The guard reads only the settings file taken at the stage-start commit, and reads the payload as v1 does*, *The hook allows the run's temporary folder*, *No agent runs without the kernel's write guard*, *The preflight runs the factory's own arguments once for each image build, and finds a refused `sudo` before any claim* and *One test checks the configuration of every model; six models ignore unknown keys* each gain one line at their end that names the new entry by its title as superseding the hook's part.
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
cat README.md docs/operator-guide.md docs/project-guide/*.md | grep -c -e 'factory-guard' -e 'PreToolUse' -e 'claude_guard' -e 'guard_support' -e 'GUARD_COMMAND' || true
```
Expect: `0`

```bash
grep -c -F '## The Claude Code hook is removed; the kernel and the undo are the write guard' docs/decisions.md
grep -c -F 'The Claude Code hook is removed; the kernel and the undo are the write guard' docs/decisions.md
```
Expect: two lines, `1` (the entry's heading) and `6` (the heading and the five lines that name it in the superseded entries)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l
```
Expect: `0`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is right for a documents-only story. It names the seven files the documenter changes, and criterion 3 lists the passages in each. Nothing under `src/factory/` is touched.
   - Criteria: each can be checked by one test or command. Criterion 1 is the unchanged-paths check, criterion 2 is `make check`, and criterion 3 is a list of document passages that each have exact before/after wording. The decision-log changes are pinned by the exact title and the count of 6. The story states no limits or error rules, so there is no failing side to cover. The decision-log entry's content is covered by its dated title, the four named decisions and the rejected reduced hook. The five superseded entries are named by title.
   - Smoke test: all four blocks run as written.
     - The grep count over the concatenated documents prints `0`; `|| true` covers grep's exit status 1.
     - The two `docs/decisions.md` greps print `1` and `6`, which matches the heading plus five superseding lines.
     - The `git diff --name-only origin/main` count prints `0`.
     - `make documents` ends with `documents ok`.
     - Each block has an `Expect:` line that can be checked against its output. No pytest command appears, so the `-q` rule does not apply.
   - Architecture: the story changes documents only, and the layers in `CLAUDE.md` are untouched. The documenter's write paths cover `README.md` and `docs/*`. The `CLAUDE.md` R12 edit is the human's change 2 and is not in this story.
   - Scope: it matches the feature's S0003 scope and decisions 1, 6, 11, 12 and 13. The human's answers of 2026-10-20 (the `PATH` and `HOME` section kept, six superseded entries counted as 6) are already in the story. Nothing in the feature's Out of scope is touched.
4. factory: started tests as self.
5. tester: No tests written. This story changes documents only: its Interface is "None", and criterion 1 forbids any change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`.
   - criterion 1: no test. As the criterion asks, this entry records that the tests stage changed nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The smoke test's `git diff --name-only origin/main -- src tests image template demo claude | wc -l` (expect `0`) checks it.
   - criterion 2: no test. It is `make check` itself, which the factory runs.
   - criterion 3 (docs): no pytest test. The documenter does this work, and the docs stage's gate checks it: `make documents` and the smoke test's greps for `factory-guard`, `PreToolUse`, `claude_guard`, `guard_support` and `GUARD_COMMAND`, plus the counts `1` and `6` for the new decision entry's title. A test under `tests/` that pins document wording would break criterion 1.
   Files created: none. Every module imported, because nothing new was written. `make test` passed on its one run (`test: green`, coverage 99.19 %), and so did `make lint` (`lint: green`). So the branch has no red tests, which is expected for a documents-only story. Open: nothing.

   `lint`: lint: green (0.0 s)
   `test`: test: green (134.8 s)
6. factory: started doing as self.
7. coder: No code written. This story only changes documents: its Interface is "None", and criterion 3 gives every document change to the documenter.
   - criterion 1: the doing stage changed nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. `git diff --name-only origin/main -- src tests image template demo claude | wc -l` prints `0`.
   - criterion 2: `make check` passed on the unchanged tree (`check: green`, coverage 99.19 %).
   - Main choice: I left `README.md` and `docs/` alone. The other option was to make the criterion-3 edits here. I rejected it because `CLAUDE.md` gives those four documents to the documenter stage, and the coder does not write them.
   - Refactor: there is no diff, so there was nothing to refactor.
   - Noticed but did not touch: nothing. The journal did not change what the task means, so the Description stays as it is.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar. That is what a documents-only story should have at review, because the documenter does criterion 3 next.
   - Criterion 1: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed, which I checked with `git diff --name-status main...HEAD`. The tester's entry (5) and the coder's entry (7) each say so, as the criterion asks.
   - Criterion 2: the coder's `make check` was green (entry 7: `check: green`). I did not run it again.
   - Tests: the Interface is "None" and states no rules or limits, so no failing side needs a test. The tester was right to write no pytest test for document wording.
   - Architecture and security: no code changed, so nothing applies.
   - Hygiene: the Description matches what the branch holds. Entry 7 says why the coder wrote nothing (the documents belong to the documenter).
   - I checked the docs criterion against `main`, and it still describes what is true:
     - `pyproject.toml` installs six console scripts, `factory-confine` among them, and none is `factory-guard`. `README.md:12` still says "Seven commands exist" and names `factory-guard`, which is the text criterion 3 changes.
     - `agent_environment_item(environment, is_directory)` in `src/factory/application/preflight.py:151` has that signature. It reports the faults `the agent run has no HOME` and `the agent run's HOME <dir> is no directory`.
     - `tests/test_model_configuration.py:12` lists the twelve `extra="ignore"` exceptions the criterion names.

   Earlier tests: none. The diff changes, renames or deletes no test file.
