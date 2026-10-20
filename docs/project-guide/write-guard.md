# The write paths, the guard and the start wrapper

This file covers the write paths, the guard, the undo, the kernel's guard and the start wrapper; read the index, `README.md`, first.

## The write paths

What an agent may write is decided in one place, for the undo of a stage and, through the kernel's targets, for the kernel.

### Where they come from

`WritePathService(boundaries).at(stage_start, work_item_path)` (`factory.application.write_paths`) returns the `GuardSettings` of the claimed stage. It reads `factory/pipeline.yml` at `stage_start.commit` with `git.show_file` and parses it with `pipeline_reader`; it never reads the work tree's copy, so an agent that rewrites the pipeline definition widens nothing and an invalid rewrite breaks nothing. The write paths are those of the role of `stage_start.claim.stage`, expanded; `root` is `boundaries.checkout`; `protected_paths` is `PROTECTED_PATHS`.

It parses the definition itself and does not use `PipelineLoader`, which stays the one place that loads the definition for the tick. This read has another purpose: it checks no installed agent file and raises or clears no stop.

Errors: `ValueError` when `work_item_path` is not `factory/features/<feature directory>/<lifecycle folder>/<work item file name>`. `PipelineDefinitionInvalid`, naming the fault, when the definition is absent or invalid at the commit, when the stage is not in it or has no role, and when a write path holds a placeholder other than the two below.

### Matching and placeholders

`factory.domain.write_paths`, all pure. `matches_any(path, patterns)` is `fnmatch.fnmatchcase`: case-sensitive, and `*` also matches `/` (`src/*` matches `src/a/b.py`; `SRC/a.py` does not match). `is_writable(path, write_paths)` adds a safety test: an empty path, a path beginning with `/` and a path with a `..` segment are never writable (`src/../factory/pipeline.yml` does not pass `src/*`); `src/..x/a.py` is safe. Callers pass normalised repository paths (POSIX separators, no `.` or empty segment, no trailing `/`).

`expand_write_paths(patterns, work_item_path=..., feature_path=...)` replaces `{work_item}` with the work item's path and `{feature}` with the feature's path, `factory/features/F0004-x` (the work item's path without its last two segments), keeps the order and leaves other patterns as they are. Any other `{name}` of lowercase letters and underscores raises `ValueError` naming it; a brace that is no such name (`{Feature}`, `{1}`) stays.

### Protected paths and the refusal

`PROTECTED_PATHS` is the engine's fixed list of twelve patterns: `.claude/*`, `*/.claude/*`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, `feature.md`, `*/feature.md` and `factory/agents/*` (a project's own agents, `PROJECT_AGENTS_DIRECTORY` in `factory.domain.paths`). The last pattern reaches subfolders too; `factory/agentsx/coder.md` and `docs/factory/agents/coder.md` are not protected. No write path can reach them, and a project cannot change the list. A `.claude` segment is protected at any depth (`src/.claude/skills/x/SKILL.md`) and only as a whole segment: `src/.claudex/a`, `src/x.claude/a`, `claude/agents/coder.md` and a path that only ends in `.claude` are not. The kernel's targets do not change. The patterns are anchored: `docs/CLAUDE.md` and `src/pyproject.toml` are not protected. `docs/project-guide/` is not protected; the documenter keeps it.

`refusal(path, guard)` is the one verdict, `None` when the write is allowed, else a text, checked in this order:

1. `<path> is not a path inside the checkout.` (unsafe path, as above)
2. `<path> is owned by the human; a change there is a question.` (matches `guard.protected_paths`, even when a write path also matches)
3. `<path> is outside the write paths of this stage.` (matches no write path)

Tests: `tests/domain/test_write_paths.py`, `tests/application/test_write_paths.py`; a later version of the definition is made with `human.push_file("main", "factory/pipeline.yml", text)` and `checkout.fetch()`.

### The kernel's targets

The kernel (Landlock, see `factory.adapters.landlock` and the decision log) allows writes beneath a folder and on a file that exists. A write path is an `fnmatch` pattern and a run also writes the project's tool state, so two pure functions in `factory.domain.confinement` turn the settings into what the kernel can name. The agent runtime calls them when it builds a run's rules (see "The `claude -p` runtime").

`GuardSettings.tool_paths` carries the definition's `tool_paths` as `WritePathService.at` reads them at the stage-start commit, unchanged: no placeholder is expanded in them. `refusal`, which the undo uses, ignores them: with write paths `["src/*"]` and tool paths `[".venv/*"]`, `.venv/x` is refused as outside the write paths. The tool paths widen only what the kernel allows, never what the undo accepts.

`write_targets(guard, *, home)` returns `WriteTarget(path, kind)` values (`kind` is `folder` or `file`), the write paths first and then the tool paths, in order, a repeated target left out. For each write path, relative to `guard.root`:

| Write path | Target |
|---|---|
| empty, starting with `/`, or holding a `.` or `..` segment | none |
| `src/*` (ends in `/*`, no wildcard before it) | the folder `root/src` |
| no `*`, `?` or `[` (`README.md`) | the file `root/README.md` |
| any other: `docs/*.md`, `a/b?/c`, `a/[bc]/d` | the folder of the segments before the first segment with a wildcard (`root/docs`, `root/a`, `root/a`) |
| a wildcard in the first segment (`*.md`, `*`) | none |

`~/<folder>/*` in a tool path is the folder `home/<folder>` (none when `home` is `None`); `<folder>/*` is the folder `root/<folder>`; any other form gives none.

`confinement_of(targets, *, root, existing_files, extras, temporary_directory)` returns the `Confinement`: a folder target goes to `folders`; a file target in `existing_files` goes to `files`; a file target that does not exist yet puts its parent folder in `folders` (`docs/openapi.json` gives `docs`), and at the root gives nothing, because the root would be the whole checkout. The `extras` (the runtime's own paths) are taken as given, never widened and never checked against `existing_files`, after the targets' folders and files respectively. A path repeated in one list is left out; `temporary_directory` is passed through.

So a pattern or a missing file is widened to the nearest folder the kernel can name, never to the root, and the undo after the run narrows the rest: whatever the run wrote in such a folder outside the write paths is reverted as it is today. A write path that only matches at the root (`*.md`) or a new file at the root has no target, and the run cannot write it under the kernel.

Tests: `tests/domain/test_tool_paths.py`, `tests/domain/test_write_targets.py`, `tests/domain/test_confinement_of.py`, `tests/application/test_write_paths_tool_paths.py`.

## The undo

`UndoService(boundaries).undo(stage_start, work_item_path)` (`factory.application.undo`) puts the work tree back after an agent run. The kernel refuses while the agent works; the undo reverts what the kernel allowed outside the write paths: a protected path inside a folder a write path opens, a file the targets widened to its folder. It returns an `UndoReport` (frozen, no unknown fields): `reverted` and `deleted`, sorted ascending without repeats, and `restored_work_item`. `AfterAgent` runs it after every completed agent run (see "After the agent run").

### What it undoes

Everything is compared with the stage-start commit, not with the work tree as it was when the agent began, so a file the agent changed in the work tree or in a commit of its own ends with the content of the stage-start commit. `Git.changed_paths(stage_start.commit)` gives the candidates: commits since then, the work tree and untracked files; ignored paths are not in it.

A candidate is refused, and so undone, in two cases:

- `refusal(path, settings)` is not `None`: the path is outside the write paths of the stage or is protected (see "The write paths"). The settings come from `WritePathService.at`, that is from the pipeline definition at the stage-start commit, the same source the kernel's targets use. An agent that rewrites `factory/pipeline.yml` to widen its role widens nothing, and an invalid rewrite does not make the undo raise; the pipeline definition itself is put back.
- The path lies directly in an `in-progress` folder of a feature (`factory/features/<feature>/in-progress/<file>`) and is not the stage's own work item. This undoes every other work item in progress, every cost-record file (`.costs.jsonl`), the stage's own included, and any other file there, whatever the write paths say. Nested files (`in-progress/sub/x`), other lifecycle folders and an `in-progress` folder outside `factory/features/` follow the write paths. The kernel does not know this second rule.

A refused path that did not exist at the stage-start commit (`added`) is deleted and listed in `deleted`; any other is checked out from that commit with `Git.revert_paths` and listed in `reverted`. Paths allowed by the write paths are not touched.

### The work item

After the refused paths, the stage's own work item is handled separately. Its state and journal are restored from the stage-start commit with `restore_state_and_journal`; the agent's edits to its sections stay. `restored_work_item` is true when that changed the file. If the agent deleted the file or left front matter that cannot be read, the file is checked out whole from the stage-start commit and `restored_work_item` is true; it is not listed in `reverted`. A work item the role may not write at all is refused like any path: it is put back whole, listed in `reverted`, and `restored_work_item` is false.

The baseline is read first. When the stage-start commit does not hold the work item, or holds it unreadable, `undo` raises `WorkItemFormatError` naming the path before it changes anything.

### Limits

- The undo makes no commit and no push. A commit the agent made stays in the history; only the work tree is put back.
- Ignored paths and anything outside the checkout are not seen and stay as they are (left for v2).
- Git's paths are taken as they are; renames show as a deletion and an addition (see "The git wrapper").

Tests: `tests/application/test_undo.py`; a fake agent writes into `boundaries.checkout` between `ClaimService` and `undo`.

## The kernel's write guard

`factory.adapters.landlock` lets a process ask the kernel to refuse its own writes and those of every process it starts later. Its user is the wrapper `factory-confine` (see "The start wrapper"); the agent runtime starts every agent run through it. The kernel refuses a write by any route, a shell command included, during the run; the undo reverts afterwards what the kernel allowed outside the write paths.

### What Landlock is

Landlock is a Linux security module that an unprivileged process uses on itself: no root, no capability. The process builds a ruleset, adds rules to it and restricts itself with it. The restriction cannot be lifted and is inherited by every child. It is built on the standard library's `ctypes` (the system calls 444, 445 and 446 and `prctl`), with no dependency.

### The rights and the two kinds of rule

The rules handle the twelve write rights of ABI 3 and nothing else: write a file, remove a folder, remove a file, make a character device, folder, regular file, socket, fifo, block device or symbolic link, refer (rename or link across folders) and truncate. `WRITE_RIGHTS` is their mask (`0x7FF2`). Reading, executing and the network stay open: a restricted process reads the whole file system.

- A folder rule (`restrict_writes(folders, ...)`) allows all twelve rights beneath the folder: create, delete, rename within and between allowed folders, link, truncate.
- A file rule (`restrict_writes(..., files)`) allows only writing and truncating that file in place (`FILE_RIGHTS`, `0x4002`). The file cannot be renamed, replaced or deleted, and nothing can be renamed onto it.

A refused write fails with `EACCES` (`PermissionError`, errno 13). Empty `folders` and `files` are allowed and refuse every write.

### The minimum ABI

`abi_version()` returns the ABI the kernel offers (7 in v1.1's container), or 0 when it offers none or a seccomp profile refuses the call; it restricts nothing. `factory.domain.confinement` holds `LANDLOCK_MINIMUM_ABI = 3` and `abi_fault(abi)`: `None` from 3 up, below it `the kernel offers Landlock ABI <n>, the write guard needs ABI 3 or higher`. The adapter itself does not call `abi_fault`.

### Checks first: fail closed

`restrict_writes` checks every path with `os.lstat` before its first system call, folders before files, each in the given order, and raises `ConfinementError` (`factory.domain.errors`; the message is `detail`, nothing added) at the first that fails: `cannot open <path>: <strerror>`, `<path> is a symbolic link`, `<path> is not a folder` (in `folders`) or `<path> is a folder` (in `files`). A refusal therefore leaves the process unrestricted. Symbolic links are refused because a rule on a link would apply to its target. A failing system call later raises `<call> failed: <strerror>`, the call being `landlock_create_ruleset`, `landlock_add_rule for <path>`, `prctl PR_SET_NO_NEW_PRIVS` or `landlock_restrict_self`; the descriptors the function opened are closed in every case.

### Stacking

A second call in a restricted process adds a ruleset on top of the first: a write must be allowed by both. A later call can narrow the restriction and never widen it.

### Tests

The tests (`tests/adapters/test_landlock.py`, `tests/domain/test_confinement_abi.py`) call `restrict_writes` in child processes (`sys.executable -c ...`, paths under `tmp_path`) wherever it reaches the system calls, because the restriction cannot be undone and would bind the pytest worker. The refusals before the first system call also run in the test process (`tests/adapters/test_landlock_checks.py`): every row there names a path that cannot be opened (missing, or a link to a missing target), so a check that is broken still fails at the first system call and binds nothing. The system calls themselves (`_create_ruleset`, `_add_rule`, `_restrict_self`) run only in child processes. Coverage does not measure the children, so the module shows little in the coverage table. No test is skipped without Landlock. Not tested: a failing system call and `abi_version`'s negative result, which no test can make the kernel produce.

`confinement_item(abi, environment, find)` (`factory.application.preflight`) is the preflight item `confinement`. It has two faults: the kernel's (`abi_fault(abi())`, followed by `: ` and the advice to update the kernel, on WSL with `wsl --update`, or to allow the Landlock system calls in the container runtime's seccomp profile) and `factory-confine` missing from the agent run's `PATH` (or no `PATH` at all). When both occur, the detail joins them with `; `, the kernel's first; with neither, the item passes. The wiring (`factory.entry.wiring`) passes `abi_version` and a search on the agent run's `PATH`, so the item runs against what the agent run will see.

## The start wrapper

`factory-confine --rules <file> -- <command> [<argument>...]` applies the kernel's write guard and becomes the command. It must run after `sudo` has made the process the agent's user (Landlock needs `no_new_privs`, which `sudo` cannot run under) and before the runtime starts, so that the runtime and everything it starts inherit the restriction. `pyproject.toml` registers it as `factory-confine = "factory.entry.confine:main"`; `python -m factory.entry.confine` does the same; `CONFINE_COMMAND` in `factory.domain.agent_runs` is its name. `ClaudeCodeRuntime` starts every agent run through it when it is built with `confine_executable`, which `build_boundaries` passes by default; the command line is in "The `claude -p` runtime".

### The arguments and the rules file

The arguments are exactly `--rules`, a file, `--` and at least one word of the command. Anything else writes `factory-confine: usage: factory-confine --rules <file> -- <command> [<argument>...]` and returns 1.

The rules file is JSON for the domain model `Confinement` (`factory.domain.confinement`, frozen, unknown keys forbidden): `folders` and `files` (lists of absolute paths) and `temporary_directory` (an absolute path); a relative path is a `ValidationError`.

```json
{"folders": ["/work/checkout/src"], "files": ["/work/checkout/notes.md"], "temporary_directory": "/tmp/run-1"}
```

### The six steps

`main(argv=None, *, stderr=None, abi=None, restrict=None, replace=None) -> int` does these in order (`restrict` and `replace` are for tests: `None` is `restrict_writes` and `replace_process`, and the console script passes neither); a fault writes one line to standard error and returns 1, and no later step runs.

1. Read the rules (UTF-8, validated as `Confinement`): `factory-confine: cannot read the rules <file>: <fault>`, the fault on one line.
2. Check the ABI with `abi_fault(abi())`: `factory-confine: the kernel offers Landlock ABI <n>, the write guard needs ABI 3 or higher`.
3. Make each folder of `folders` that does not exist, with its parents: `factory-confine: cannot make the folder <path>: <reason>`.
4. Make `temporary_directory` with mode `0700` and never `exist_ok`, so a folder or link made beforehand is refused: `factory-confine: cannot make the temporary folder <path>: File exists`.
5. `restrict_writes([*folders, temporary_directory], files)`: a `ConfinementError` is `factory-confine: <detail>` (for example `cannot open <path>: No such file or directory` for a missing file, `<path> is a symbolic link`).
6. `replace_process(command, {**os.environ, "TMPDIR": <temporary_directory>})`: `factory-confine: cannot start <command>: <reason>`.

### What the command gets

Fail closed: after any fault the command never starts. On success `main` does not return. The command keeps the wrapper's process and process group, so its exit status and output are its own. Its environment is the wrapper's with `TMPDIR` set to the temporary folder; every other variable is unchanged. It can write in the folders, in the listed files and in its temporary folder, and nowhere else; a process it starts is bound the same way.

### Tests

`tests/entry/test_confine.py` runs every row that reaches step 5 or 6 in a child process (`sys.executable -m factory.entry.confine`), because the restriction cannot be undone; rows that stop at steps 1 to 4 call `main` in-process with `abi` injected. These rows check the real kernel. `tests/entry/test_confine_steps.py` runs the steps up to step 6 in-process as well, with `restrict` and `replace` injected as recorders (`replace` raises a test-local exception instead of replacing the process), so coverage and mutation testing see them. `tests/entry/test_confine_defaults.py` also runs in-process the rows for `main`'s defaults (`sys.argv`, `sys.stderr`, `abi_version`, `restrict_writes` and `replace_process`, each row refusing before the first system call or the `exec`), for a folder of the rules that already exists or cannot be made, and for the fault text of an unreadable rules file; `tests/confine_support.py` holds the helpers these modules share. `tests/adapters/test_process_replace_faults.py` does the same for `replace_process`'s refusals. Coverage does not follow the children. `factory.entry.confine` imports `factory.adapters.landlock` and `factory.adapters.process` directly: it picks no adapter behind an interface (feature decision 19).
