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
   - `docs/operator-guide.md`: the section *`factory-guard` on the agent run's `PATH`* is deleted, and no other section links to it. The preflight table's row `agent-environment` says the item checks that the agent run's `HOME` is an existing directory, with the faults `the agent run has no HOME` and `the agent run's HOME <dir> is no directory`. In *What differs from Claude Code*, the bullet "No hook. ..." is deleted (neither runtime registers one). The passage on the kernel's targets says that the undo after the run judges the exact write paths (not "the hook and the undo"). *A project's own skills* says that the undo removes a nested `.claude/` write after every run, under either runtime, and that the kernel cannot refuse it inside a folder a write path opens (it no longer names a hook). The `preflight_failed` row keeps "there is no fallback" without "to the hook".
   - `docs/project-guide/write-guard.md`: the section *The guard command* is deleted, with its test list. *The write paths* says the decision is made in one place for the undo (and, through the targets, the kernel); every "the hook and the undo" becomes "the undo". *The undo* says the kernel refuses during the run and the undo reverts what the kernel allowed outside the write paths after it (a protected path inside an allowed folder, a file the targets widened to its folder). *The kernel's write guard* no longer refers to "The guard command".
   - `docs/project-guide/agents.md`, *The `claude -p` runtime*: the argument block and the sentence after it name no `--settings`; the list of files under `state_directory` holds `instructions-<session>.md` and, with `confine_executable`, `confine-<session>.json`, and no guard or hooks file; the environment paragraph names no `factory-guard`; the sentence on `RUN_FILE_MODE` names the instructions and rules files.
   - `docs/project-guide/watching.md`: `production_environment()` is said to use the directory where the console scripts, `factory-confine` among them, are installed.
   - `docs/project-guide/README.md`: the entry `guard_support.py` among the shared test helpers is deleted; the line on `write-guard.md` names neither `factory.adapters.claude_guard` nor `factory.entry.guard`, and its list of sections no *The guard command*; the paragraph on `extra="ignore"` models says "There are twelve" and names `_Usage`, `_Denial`, `_StructuredOutput` and `_Reply` in `factory.adapters.claude_runtime` and `_Event`, `_Part`, `_Tokens`, `_CacheTokens`, `_ToolState`, `_Span`, `_Error` and `_ErrorData` in `factory.adapters.opencode_runtime` (the list of `tests/test_model_configuration.py` after S0002).
   - `docs/decisions.md`: a new entry *The Claude Code hook is removed; the kernel and the undo are the write guard*, dated with the story, from the feature's decisions 2, 3, 5 and 6 and F0019's decision 16. Its reasons: the cross-check of 2026-10-19 (405 transcripts, no refusal of the hook in the 264 runs after the kernel guard went live, the one disagreement fixed by F0019-S0011); the hook saw two tools only; opencode runs had no hook already. It rejects a reduced hook for the protected paths only. The entries *The guard reads only the settings file taken at the stage-start commit, and reads the payload as v1 does*, *The hook allows the run's temporary folder* and *No agent runs without the kernel's write guard* each gain one line at their end that names the new entry by its title as superseding the hook's part.
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
Expect: two lines, `1` (the entry's heading) and `4` (the heading and the three lines that name it in the superseded entries)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l
```
Expect: `0`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
