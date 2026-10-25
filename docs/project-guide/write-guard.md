# The write paths, the guard and the undo

This file covers the write paths, the guard and the undo; read the index, `README.md`, first.

## The write paths

What an agent may write is decided in one place, for the undo of a stage and for the take of a `container` instance.

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

## The undo

`UndoService(boundaries).undo(stage_start, work_item_path)` (`factory.application.undo`) puts the work tree back after an agent run. Nothing refuses a write while the agent works; the undo reverts what the agent wrote outside the write paths, among them a protected path inside a folder a write path opens. It returns an `UndoReport` (frozen, no unknown fields): `reverted` and `deleted`, sorted ascending without repeats, and `restored_work_item`. `InlineEnvironment.take` (`stage-environment.md`, *The stage environment*) runs it and turns its report into a `TakeReport`; `AfterAgent` calls that take after every completed agent run (see "After the agent run"). The container environment's take is *The take* in `stage-environment.md`; A stall's undo is the inline environment's take too: `StallService` takes through the stage environment (`stage-environment.md`, *Who calls what*).

### What it undoes

Everything is compared with the stage-start commit, not with the work tree as it was when the agent began, so a file the agent changed in the work tree or in a commit of its own ends with the content of the stage-start commit. `Git.changed_paths(stage_start.commit)` gives the candidates: commits since then, the work tree and untracked files; ignored paths are not in it.

A candidate is refused, and so undone, in two cases:

- `refusal(path, settings)` is not `None`: the path is outside the write paths of the stage or is protected (see "The write paths"). The settings come from `WritePathService.at`, that is from the pipeline definition at the stage-start commit. An agent that rewrites `factory/pipeline.yml` to widen its role widens nothing, and an invalid rewrite does not make the undo raise; the pipeline definition itself is put back.
- The path lies directly in an `in-progress` folder of a feature (`factory/features/<feature>/in-progress/<file>`) and is not the stage's own work item. This undoes every other work item in progress, every cost-record file (`.costs.jsonl`), the stage's own included, and any other file there, whatever the write paths say. Nested files (`in-progress/sub/x`), other lifecycle folders and an `in-progress` folder outside `factory/features/` follow the write paths.

A refused path that did not exist at the stage-start commit (`added`) is deleted and listed in `deleted`; any other is checked out from that commit with `Git.revert_paths` and listed in `reverted`. Paths allowed by the write paths are not touched.

### The work item

After the refused paths, the stage's own work item is handled separately. Its state and journal are restored from the stage-start commit with `restore_state_and_journal`; the agent's edits to its sections stay. `restored_work_item` is true when that changed the file. If the agent deleted the file or left front matter that cannot be read, the file is checked out whole from the stage-start commit and `restored_work_item` is true; it is not listed in `reverted`. A work item the role may not write at all is refused like any path: it is put back whole, listed in `reverted`, and `restored_work_item` is false.

The baseline is read first. When the stage-start commit does not hold the work item, or holds it unreadable, `undo` raises `WorkItemFormatError` naming the path before it changes anything.

### Limits

- The undo makes no commit and no push. A commit the agent made stays in the history; only the work tree is put back.
- Ignored paths are not seen by the undo and it does not judge them. `run_sealed` removes them before the undo (`remove_ignored()`), after every run that returned; a run that raised leaves them to the next restore. Anything outside the checkout is not seen and stays as it is.
- Git's paths are taken as they are; renames show as a deletion and an addition (see "The git wrapper").

In the container environment the take applies the same two rules the other way round: it copies what they allow from the dataset into the work tree and leaves the rest (see *The take*, `stage-environment.md`).

Tests: `tests/application/test_undo.py`; a fake agent writes into `boundaries.checkout` between `ClaimService` and `undo`.

## The end of a run's processes

A process that an agent run starts in a new session (`setsid`) outlives the run: neither the end of the call nor the time limit's kill of the run's process group reaches it, and it goes on writing under the run's rules while later stages run, are undone and are checked. `python -I -m factory.entry.leftovers --user <name>` ends such processes. It runs as the agent's user, through the one `sudo` rule: both agent runtimes start `sudo -n -u <user> -- <python> -I -m factory.entry.leftovers --user <user>` after every call of a run that has an operating-system user other than the factory's own, from the folder `/`, with an empty environment and a 30-second limit. It comes after the call and before the removal of the run's temporary folder, inside `AgentRuntime.run`, so before the seal's check, the undo and the checks. When it fails or does not end in time, the run raises `AgentRuntimeError` (`cannot end the agent's processes: <line>`) unless the call's own refusal stands. See `agents.md`, *Ending the agent's leftover processes*, and the operator guide, *The agent runs as a second user*.

`main(argv=None, *, stderr=None, identity=None, kill=None, processes=None, sleep=None) -> int` is in `factory.entry.leftovers` (`None` is `sys.argv[1:]`, `sys.stderr`, and `own_identity`, `signal_every_other` and `read_process_table` of `factory.adapters.process`, and `time.sleep`; the four calls are injected by tests). It writes nothing to standard output. Every fault is one line on standard error, `factory-leftovers: <fault>`, and status 1; no later step runs. The pure rules are in `factory.domain.leftovers`.

### The three steps

1. The arguments are exactly `--user` and one non-empty name. Anything else is `factory-leftovers: usage: python -m factory.entry.leftovers --user <name>`, before the identity is read.
2. `leftovers_refusal(identity(), name)`, before the first signal. Two refusals: `refuses to run as root`, and `runs as <user>, not <name>` (case-sensitive). Root is refused whatever the name: `kill(-1)` as root would end every process of the container, the factory included. The second guards the same mistake from the other side: a stand-in `sudo` that does not switch users leaves the program running as the factory's user, and it then refuses instead of ending the factory's own processes.
3. The rounds, 1 to 50 (`LEFTOVER_ROUNDS`): `kill(SIGKILL)`, then read the process table and take `leftover_pids`. None left ends the program with status 0 and no output. Otherwise, unless it was the last round, it pauses 0.1 s (`LEFTOVER_PAUSE_SECONDS`), so 50 rounds have 49 pauses. Each round signals again, since a process may have been started between the signal and the read. After round 50 with processes left: `factory-leftovers: <n> processes left after 50 rounds: <ids, joined by ", ">`, the ids of the last round.

The faults of step 3: an `OSError` from the signal is `cannot signal the processes: <error>`; an `OSError`, or a `ValueError` for a status line that cannot be parsed, from the process table is `cannot list the processes: <error>`.

### What counts as left

`kill(-1)` sends the signal to every process the user may signal and spares the calling process, so the program does not end itself. `leftover_pids(entries, identity)` returns the ids, ascending and each once, of the entries whose `uid` is the identity's, whose `pid` is not the program's own and whose `ended` is false: zombies and dead entries are not counted, since SIGKILL cannot do more to them. `Identity` (uid, user name, own pid) comes from `own_identity()`.

The table is read by `read_process_table(proc)` in `factory.adapters.process`, the reader that *Killing a session* in `processes-and-checks.md` describes, with the model `ProcessEntry` of `factory.domain.sessions`: `ended` comes from `/proc/<pid>/stat`, `uid` from the owner of the folder `/proc/<pid>`. It is the folder's owner and not a file's because a process that makes itself not dumpable (`prctl(PR_SET_DUMPABLE, 0)`) gets root-owned files under `/proc/<pid>` while its folder keeps its user; a file's owner would hide exactly the process that most needs ending. An entry that vanishes while it is read is left out. The program has no second reading of `/proc`.

The program never waits with `kill -0 -1`: on Linux, a target the caller may not signal still counts as found, so the call would report processes of other users as left and never settle.

### Tests

`tests/domain/test_leftovers.py` (`leftover_pids`, `leftovers_refusal`, the limits of `Identity` and of `ProcessEntry.uid`), `tests/adapters/test_process_table.py` (`read_process_table` on fake tables of folders under `tmp_path`, and `own_identity`) and `tests/entry/test_leftovers.py` (`main` in-process with every call injected; one test runs the real module in a child process with `-I -B`, naming a user it does not run as, so it refuses before its first signal). `-B` matters: under the tests' umask `022` the bytecode the child would write into `src/factory` makes folders the removal of ignored paths cannot remove. `tests/leftovers_support.py` holds the shared `AGENT` and `ROOT` identities and `process_entry`.

No test calls `signal_every_other`, and no test or smoke test runs the program as the user it names: it would end every process of that user, which in an agent's run is the run itself, and under `make check` the factory.

## Replaced in v1.2

The kernel's write guard went with F0044-S0002; the write paths are kept by other means.

- *The kernel's targets* (`write_targets`, `confinement_of`, the tool paths): replaced by the dataset's rollback and the take, which copies only the changed paths the role may write.
- *The kernel's write guard* (`factory.adapters.landlock`): replaced by the dataset's rollback and the take.
- *The start wrapper* (`factory-confine`, `factory.entry.confine`, `replace_process`): replaced by the dataset's rollback and the take; an agent call starts without a wrapper.
