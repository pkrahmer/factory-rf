# Processes and this repository's checks

This file covers the one module that starts processes and the commands behind this repository's checks; read the index, `README.md`, first.

## Starting a process

`subprocess` is imported, and a process started, in `factory.shared.adapters.process` only (R5). Eight modules import it, as `tests/guards/test_wrapper_search.py` lists them. The git wrapper (`git_cli`), the make class (`make_commands`), the `claude -p` runtime (`claude_runtime`) and the tests' container fake (`fake_containers`) reach their tool through `run_process(request) -> ProcessResult`; the opencode runtime (`opencode_runtime`) through `run_process` and, for a run it watches line by line, `run_streaming`; the Podman wrapper (`podman_runs`) through `run_process` for a container run and `run_or_raise` for its queries; the ZFS wrapper (`zfs_snapshots`) and the power-off (`power_off`) through `run_or_raise` only. No other module calls a command-line tool.

`ProcessRequest` (frozen, unknown keys forbidden) holds:

- `argv`: the program and its arguments, at least one element, passed as given. There is never a shell, so `$HOME; echo x` reaches the child as that text.
- `cwd`: the working directory.
- `env`: `None` lets the child inherit the current environment; a mapping is the child's whole environment, nothing is added.
- `time_limit`: `None` for no limit, otherwise greater than zero (a zero or negative value is a `ValidationError`).
- `merge_stderr`: the child's stderr goes into the same pipe as its stdout, in the order written, and `ProcessResult.stderr` is empty.

The child runs in its own session (so it leads its own process group), with stdin closed. At the `time_limit` the child's process group is killed with SIGKILL (below, *Killing a process group*), so what the command started in that group ends too, and `run_process` returns with `exit_status=None`, `timed_out=True` and the output written so far (it reads once more after the kill, for at most `PIPE_DRAIN`; see *Reading after the child's end*). A child that ends in time gives its real exit status and `timed_out=False`; a non-zero status is returned, not raised. Output is decoded as UTF-8 with undecodable bytes replaced. A failure to start, such as `FileNotFoundError`, is an `OSError` and is not caught: the wrapper above decides what it means.

`ProcessResult` also has `stopped` (default `False`): true when `run_streaming` was stopped by its callback. The fields are `exit_status`, `stdout`, `stderr`, `timed_out`, `duration` and `stopped`; a call that closes a pipe still open after the drain (below) says so in no field.

`run_or_raise(argv, *, time_limit, fault, cwd=ROOT, accepted=(0,)) -> ProcessResult` is the block that a wrapper of a short command repeats, written once. It runs `ProcessRequest(argv=argv, cwd=cwd, env=None, time_limit=time_limit, merge_stderr=True)` through `run_process` and returns the result. `ROOT` is `Path("/")`, the default `cwd`: these commands read no file from their working directory. `fault` is the wrapper's own error, called with one detail string; the helper raises what it returns:

- A program that cannot start (`OSError`) raises `fault(str(error))`, chained from the `OSError`.
- A call that reached `time_limit` raises `fault(no_end_detail(time_limit))`.
- An exit status not in `accepted` raises `fault(failure_detail(result.stdout, result.exit_status))`; `accepted=None` returns every exit status.

The users: `ZfsSnapshots._execute` (`fault` is `SnapshotError` with the command as first argument, `accepted` the caller's), `SystemctlPowerOff.power_off` (`PowerOffError`; it prefixes `cannot start <sudo>: ` to the detail when the cause is an `OSError`) and `PodmanRuns._query` (`ContainerError` with the command, `cwd` the workspace, `accepted=None`). `PodmanRuns.run` keeps its own `ProcessRequest`, because it passes the launch's environment; it uses `cwd=ROOT`. A wrapper that needs more than this builds its own request and calls `run_process`. Tests: `tests/shared/adapters/test_run_or_raise.py`.

`run_streaming(request, on_line) -> ProcessResult` is for a runtime that must act on a run's output as it comes (the opencode runtime's budget and provider limit, from F0020-S0004), where `run_process` hands the output over only when the process has ended. It starts the child exactly as `run_process` does (both go through the private `_start`, which holds the module's one `subprocess.Popen(` line) and calls `on_line(stream, line)` for every line of standard output (`"stdout"`) and standard error (`"stderr"`) while the child runs. A line comes without its line feed, decoded as UTF-8 with replacement; a last line without a line feed is passed when its stream ends (not when the drain below runs out; the bytes stay in `stdout`). With `merge_stderr` every line is `"stdout"`. The calls come one at a time from the calling thread, from a selector loop, not from reader threads. A line reaches the callback once and whole however many reads it takes to arrive (a line longer than one 64 KiB read, or one split by a pause), and `stdout` and `stderr` hold the whole output.

- `on_line` returns `True` to stop: the child's process group is killed at once (*Killing a process group*), no further line is passed (also not one already read in the same chunk), and the result has `stopped=True`, `exit_status=None`, `timed_out=False`. The same holds when `on_line` stops on a last line without a line feed, passed when its stream closes: the call stops at once, also while the other stream is still open.
- At the `time_limit` the process group is killed as in `run_process` (`timed_out=True`, `stopped=False`, `exit_status=None`), also when the child closed both its streams and kept running. No line read after the kill is passed.
- When `on_line` raises, the process group is killed and the exception propagates.
- `stdout` and `stderr` of the result hold what was read up to the end, the stop or the kill (unlike `run_process`, nothing is read after a kill). A child that ends by itself gives its exit status after `on_line` has had every line.

**Killing a process group.** The same kill, `_kill_session` in `factory.shared.adapters.process`, runs at the `time_limit`, at a stop by `on_line` and when `on_line` raises. It sends SIGKILL to the child's process group, `os.killpg(process.pid, signal.SIGKILL)`; a group already gone (`ProcessLookupError`) is no error. It reads no process table and does not wait for the group's processes to end, so a grandchild may still be ending for a moment after the call returns. The child is not reaped yet, so its id, which is the group's, cannot belong to an unrelated process meanwhile.

- Why a group is enough: no agent code runs on the host (every agent call and every project command runs in a container, which ends whole with its call), and what the factory starts there is git, `zfs` and `podman`. Decision: *The process group is killed*, in `docs/decisions.md`.
- A descendant that takes a process group or a session of its own (`setpgid`, `setsid`, GNU `timeout` without `--foreground`) is not killed.
- A `PermissionError` (another user's process) propagates.

Tests: `tests/shared/adapters/test_process_session.py`.

Tests: `tests/shared/adapters/test_process_streaming.py` and `tests/shared/adapters/test_process_streaming_reads.py` (long and split lines), `tests/shared/adapters/test_process_streaming_last_line.py` (a stop on a last line without a line feed); the helpers `python_argv`, `is_gone` and the callback `Recorder` are in `tests/support/process_support.py`.

A test whose child must act before its time limit ends it (write a record or a pid file, print a line, finish a first call) takes `ROOMY_LIMIT` (10 s) and `ROOMY_BOUND_SECONDS` (25, for an elapsed-time bound) from `tests/support/time_limits.py`. The stand-ins the limit must end wait longer than the bound, so a missed kill fails. A child that need not start to be killed may keep a shorter limit.

```python
result = run_process(ProcessRequest(argv=["git", "status"], cwd=repo, time_limit=timedelta(seconds=30)))
```

**Reading after the child's end.** `PIPE_DRAIN` (`timedelta(seconds=5)`, read at each call, so a test sets it with `monkeypatch.setattr`) bounds how long a call waits for a pipe that stays open. Both functions read in steps of at most 0.05 s and check in between whether the child has ended. They check with `os.waitid(..., WNOWAIT)`, which does not reap the child, so a kill at the time limit during the drain still signals a process group that is the child's. Once the child has ended on its own, they read on until both pipes close or `PIPE_DRAIN` has passed, whichever comes first. If the pipes closed, the result is as it always was. If not, they stop reading, close the pipes and return the child's own exit status with `timed_out=False`, `stopped=False` and every byte read; `run_streaming` has passed every complete line to `on_line`.

The time limit counts as before: one that falls before the child's end or during the drain is a `timed_out` call. After that kill `run_process` reads what is left for at most `PIPE_DRAIN` and closes the pipes. The bound holds also for a request without `time_limit`.

Known limits: a process that left the process group (by `setpgid` or `setsid`) and keeps a pipe open holds the call for at most `PIPE_DRAIN` after the child's end or the kill, no longer until it ends. This module does not kill it, and nothing ends it after the call as another user; in a container it ends with the container. A line a holder writes later than `PIPE_DRAIN` after the child's end is lost to the result. Reason: `docs/decisions.md`, *A call stops reading five seconds after its own process ended*. Tests: `tests/shared/adapters/test_process_drain.py`.

`tests/guards/test_process_search.py` keeps the boundary: only `process.py` imports `subprocess`; `shell=True`, `os.system`, `os.popen`, `os.exec*`, `os.spawn*`, `os.posix_spawn*` and `asyncio.create_subprocess_*` are used nowhere under `src/factory`; and the only suppression markers there are the four in `process.py` (`noqa: S404` and `nosec B404` on `import subprocess`, `noqa: S603` and `nosec B603` on the `subprocess.Popen(` line). Do not write those marker words in a comment or docstring in `src/factory`. Why: see `docs/decisions.md`. Tests run real child processes (Python one-liners through `sys.executable`) in `tmp_path`; nothing is faked.

## The duplicates report

`make duplicates` prints what the reviewer would otherwise have to spot by eye: blocks of similar code and dead code that no one accepted. It runs pylint (only its duplicate-code messages, R0801, as JSON) and vulture (text), and hands both outputs to `python -m factory.entry.check_duplicates <pylint-json> <vulture-text> --baseline security/duplicates-baseline.txt`. The target and the pipeline step that calls it are added by a later change of the housekeeping feature; the command and the rules below exist now, and pylint and vulture are development dependencies.

The rules are pure functions in `factory.shared.domain.duplicates` (`similar_code_findings`, `dead_code_findings`, `read_baseline`, `compare`, `report_lines`); the command only reads the files, prints and returns the exit status.

The command reads its three files through `factory.entry.inputs.read_input`, which raises `UnreadableInput` for a file that is missing or not UTF-8; the command turns that into status 2 like a parse fault.

### The keys

Each finding has a key that holds no line number, so editing code above or below a finding does not make it new:

- similar code: `similar-code <modules>: <first code line>`. The modules are those the message names, sorted, unique and joined by `, `; the first code line is the first non-blank line after the message's `==<module>:[<start>:<end>]` lines, stripped. Example: `similar-code factory.hosting.domain.git, factory.pipeline.domain.stops: @field_validator("at")`.
- dead code: `dead-code <path>: <message>`, from a vulture line `<path>:<line>: <message> (<n>% confidence)` (with an optional `, <m> lines` before the parenthesis). Example: `dead-code src/factory/x.py: unused function 'helper'`.

The line numbers stay in the finding's `where`, which the report prints. A pylint text or a message that is not in the expected form (not a JSON array, a `duplicate-code` object without a string message, a message without a module line, a malformed `==` line or no code line), and a vulture line out of form, is refused with a `ValueError`; the command turns it into status 2, so a change in a tool's output stops the report and is not hidden.

### The baseline

`security/duplicates-baseline.txt` holds the accepted findings, one key per line; blank lines and lines starting with `#` (after stripping) are skipped. `--baseline <path>` is required. `--write-baseline` writes the file instead of comparing: the header line `# Accepted findings of make duplicates, one key per line.`, then the key of every finding (similar code first, then dead code, in input order, a key found twice written once), and prints `duplicates: baseline of <n> findings written to <path>`. Review the file's diff before committing it: it is the list of what the human accepted.

The baseline accepts the process calls of the two agent runtimes (decision log, *What the agent runtimes share lies in one module*) and the fakes that only the tests use (`ManualClock` and `ManualWaiter` in `factory.shared.adapters.clock`, `FakeAgentRuntime` in `factory.agents.adapters.fake_agent_runtime`, `FakeHostingService` in `factory.hosting.adapters.fake_hosting`), so a new finding there is a copy that the decision does not cover.

### The output and the exit status

The command prints, in this order:

- `new <key> at <where>: <message>` for each finding whose key is not in the baseline;
- `gone <key>` for each baseline key that no finding has any more (remove it from the baseline);
- the last line `duplicates: <n> new, <k> known, <g> gone`.

The exit status is 0 when nothing is new (gone keys alone do not change it), 1 when something is new, and 2 when an input file or the baseline cannot be read or a text cannot be parsed; then one line `check-duplicates: <reason>` goes to standard error. Without `--baseline` argparse refuses with status 2.

This repository's pipeline runs the report after the coder and writes its last line into the coder's journal entry, whatever the exit status: the report is a record for the reviewer, not a gate, and `make check` does not run it.

## The document check

`uv run python -m factory.entry.check_documents` reads the four documents (the operator guide is its index `docs/operator-guide/README.md` and ten topic files, listed in `OPERATOR_GUIDE_FILES`; a missing one is reported as `docs/operator-guide/<file>: missing`) and the other files of this guide, and prints one finding per line and exits 1, or, when nothing blocks, ends with `documents ok (<seconds> s)`. The rule is the pure function `factory.shared.domain.documents.check_documents`; the command only reads the files (`--root` names another checkout). It requires:

- the operator guide's sections *Install* and *Configuration* in `docs/operator-guide/install.md` and *The stops* in `docs/operator-guide/stops.md`, with a table row for each row of `STOP_TABLE` that holds the stop's id in backticks and its destination in words;
- the guide's index, `docs/project-guide/README.md`, with its sections *Kill points* and *Fault-injection paths*, with a table row for each case of `KILL_POINT_CASES` and each path of `FAULT_PATHS`, each with its id or test name in backticks;
- none of the phrases of `REPLACED_PHRASES` and none of the v1 words of `GLOSSARY_FORBIDDEN` outside a `## Replaced from v1` section; the decision log is exempt from both lists.

The command also reads every other `.md` file directly in `docs/project-guide/` (`factory.shared.domain.documents.is_guide_file` says which: not the index, no subfolder, no other extension) and checks it for the phrases and the v1 words only, so that a section moved out of the index does not leave the check. Its findings follow those of the four documents, in path order. A folder, a file in a subfolder and a missing folder add nothing.

### The examples

After the settings lines the command runs the `console` blocks of every document it reads for names (the README and the files of both guides). How to write one is in [style.md](style.md), *Runnable examples*; this section is the machinery.

- `factory.shared.domain.documents.examples(text)` returns `Examples` with `runnable` (each `Example`: its line, its fixture and its `Command`s with their expected lines) and `skipped` (`Skipped`: line and kind). A block marked `vm`, `github` or `model`, or with a command for which `runs_the_suite` holds, is skipped; `first_difference` is the match, with `...` and `<placeholder>`.
- `factory.shared.application.document_examples` holds the two interfaces: `Fixture.prepare(folder)` fills an empty folder and returns the extra environment, and `ExampleRunner.run_document(document, examples, fixtures)` returns the document's findings.
- `factory.shared.adapters.document_examples.ProcessExampleRunner` runs each command through `run_process` as `env -i <variables> sh -c <command>`. The fixed variables come last, so a fixture cannot replace `PATH`, `HOME`, `TZ` or `LANG`. Its default limit is 60 seconds; a test passes a shorter one. The folder and the home are temporary and removed when `run_document` returns, also after a timeout.
- `factory.hosting.adapters.checkout_fixture.CheckoutFixture` is the fixture `checkout`: it exports the tracked files of the checked commit through `GitCli.export`. It raises `FixtureError` outside a git repository; the runner then gives one finding, `fixture <name> could not be prepared`, at the block's line and runs none of the document's commands on that fixture.
- `factory.hosting.adapters.instance_fixture.InstanceFixture(git)` is the fixture `instance`. `prepare(folder)` makes the bare remote `<folder>/remote.git` with `GitCli.clone_bare`, a healthy health file in `<folder>/state` (named by `HEALTH_FILE_NAME` in `factory.watching.adapters.health_file`, the name `factory-health` reads), the image id file and the empty agent home, workspace and copy base, and writes `<folder>/factory.env`, one `NAME=value` line for each variable it returns. The name `INSTANCE_FIXTURE` is in `factory.shared.domain.documents`. A `GitError` becomes a `FixtureError`, as for `checkout`.
- `factory.entry.check_documents` wires the runner and the two fixtures. Its output is described under *The checked documents and the report*. A line for a skipped block reads `<document>:<line>: not run (<kind>)`.

### The name check

The command prints one line per name a document writes that does not exist, as `<document>:<line>: <name> does not exist`. Whether such a line blocks depends on the document: see *The checked documents and the report*. `uv run python -m factory.entry.check_documents | grep -c "does not exist"` counts them.

It reads `README.md` and every `.md` file under `docs/operator-guide/` and `docs/project-guide/`; `docs/decisions.md` and `docs/runs/` are not read. The pure functions are `named_references` (finds the names, with their lines) and `unresolved` (turns the refused ones into findings) in `factory.shared.domain.documents`; the command gives them the checkout's top-level entries and the real test of existence. Three kinds of reference are found:

- **A module or attribute:** a backticked dotted name that starts with `factory.`. A name that ends in `.env`, `.service`, `.yml`, `.yaml`, `.json`, `.toml`, `.md` or `.txt` is a file name (`factory.env`) and is not checked. It exists when `importlib` imports the longest leading part that is a module and the rest are attributes of it in turn (`factory.shared.domain.documents.named_references` is checked that way). Other dotted names, such as `os.path`, are not checked.
- **A repository path:** a backticked text that contains `/` and no `$` (a text with `$` is a shell expression and is skipped as a whole). In a pytest node id (a test file, then `::`, then the test name) only the path before `::` is read. The text has no whitespace, does not start with `/` or `~` and holds no `://`, and either starts with a top-level entry of the checkout or ends in a file name with an extension (so a path whose first folder was renamed is still checked). `origin/main` is not a path. It exists when it resolves to something inside the checkout.
- **A link:** the target of a relative Markdown link, read from the document's own folder (`../` included) with any `#fragment` left off. A web address, a `mailto:` address, an absolute path and a link to a heading alone (`#...`) are not checked.

Never checked, whatever the kind: a placeholder in angle brackets (`<instance>`), a glob (`*`), an absolute path such as one under `/srv` or `/etc`, anything inside a fenced code block, and a section headed `## Replaced from v1` or `## Replaced in v1.2` up to the next `##` heading. A name after that heading is checked again.

### The checked documents and the report

`docs/checked-documents.txt` lists the documents whose findings of the name, settings and example checks fail the command: one path per line, `#` starts a comment, blank lines are skipped. `factory.shared.domain.documents.read_checked_documents(text)` reads it. A missing file is an empty list. A listed path that does not exist, or that is not a document the check reads (`docs/decisions.md`, for example), is one blocking finding.

The output has three parts, in this order:

1. One line per blocking finding: today's checks (a missing stop row, a missing section, an old word) for every document, and the new checks for the listed ones.
2. The heading `Report (not checked yet):` and the other findings of the new checks, then the `not run` lines of skipped examples. The heading is left out when there is nothing to report. A `not run` line never blocks, also for a listed document.
3. When nothing blocks, the last line `documents ok (<seconds> s)`. Otherwise there is no such line and the exit status is 1.

`split_findings` makes the split from the document each finding carries. A document is added to the list when it has been rewritten; the list is complete when every document is on it.

### The settings check

The settings code is the one source of the instance's settings. `factory.shared.domain.settings.SETTINGS` is a tuple of `SettingDoc` (frozen: `name`, `required`, `default`), one row for each variable `read_settings` reads, `FACTORY_DATASET` and `FACTORY_STAGE_IMAGE` included. `required` is `yes`, `no` or a condition such as `with zfs`; it is kept for whoever writes the guide and is never compared. `default` is `None` where the code has none; the other defaults are built from the module's own constants, so the table cannot drift from what `read_settings` applies. A story that makes `read_settings` read another variable adds its row: `tests/shared/domain/test_settings_table.py` calls `read_settings` with a mapping that records every key looked up and compares those keys with the names in `SETTINGS`.

The command reads the section *Configuration* of `docs/operator-guide/install.md` with `guide_tables(text, section)`, which returns the tables of the section and its subsections as `GuideTable` (`heading` is the nearest heading above the table, then `header` and `rows`), and prints two kinds of finding after the name findings, each line prefixed with the guide's path. Like the name lines they do not change the exit status.

- `settings_findings(guide_tables, SETTINGS)`: only a table whose first column is `Name` or `Variable` counts; any other table is ignored. A setting the code reads and no such table names, and a name that no setting has, are one finding each. A default is compared only in a table with a `Default` column, exactly against `SettingDoc.default` (`None` against an empty cell or `none`); without that column only names are compared. A guide with no such table gives no finding.
- `refusal_findings(guide_tables, settings_source)`: only a table under the heading `The refusals` whose first column is `Refusal` counts. A refusal is the backticked text of its first cell; its `<placeholder>`s are cut out and each remaining piece of three characters or more must occur in `settings_source`, which the command takes from the source file of `factory.shared.domain.settings`. A text no source holds is one finding.

Today's operator guide has no `Default` column and no refusal table, so it gives no settings finding. Both functions are pure; the command does the reading.

This repository's pipeline definition (`factory/pipeline.yml`) runs it as a check of the docs stage through `make documents`, so a missing row or a v1 word is found where the four documents are written, before the human sees the pull request; red holds the work item at the docs stage. `make check` does not run it (the decision log, *The four documents are checked by a command*, and its 2026-10-17 entry for the docs stage). A story that adds a row to `STOP_TABLE`, `KILL_POINT_CASES` or `FAULT_PATHS`, changes one of the four documents or changes a file of the guide, runs the check and ends with `documents ok`.
