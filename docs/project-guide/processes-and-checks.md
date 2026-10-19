# Processes, project commands and this repository's checks

This file covers processes, project commands and this repository's checks; read the index, `README.md`, first.

## Project commands

The factory reaches a project's build only through the `ProjectCommands` interface (an abstract base class, `factory.application.project_commands`). It has one operation, `run(command, *, time_limit) -> CheckResult`. `MakeProjectCommands(directory, kill_points=None, *, executable="make")` (`factory.adapters.make_commands`) is the first implementation. It inherits `ProjectCommands`. The string `"make"` appears in this module and in `factory.application.preflight` (its `REQUIRED_TOOLS`); `tests/test_make_search.py` allows exactly those two. The pipeline uses the results, and so does the preflight's probe.

`run` starts `<executable> --no-print-directory <command>` in `directory` through `run_process`, with stderr merged into stdout. The environment is the current one less `MAKELEVEL`, `MAKEFLAGS` and `MFLAGS`. Without that, a run inside `make check` (where `MAKELEVEL` is set) would print `make[N]: Entering directory` lines that a run on its own does not. `directory` is where make finds the project's Makefile.

Rules of `run`:

- `time_limit` of zero or less raises `ValueError`.
- `command` must match `^[a-z][a-z0-9-]*$`, checked with a full match. Otherwise `ProjectCommandError` is raised before anything is started. So is an `executable` that cannot be started; the detail is the operating system's message.
- The exit status is the only judgment. 0 is `"passed"`, any other is `"failed"`, and a command ended by the `time_limit` is `"time_limit"` with `exit_status` `None`; the process group is killed. GNU make, not the recipe, sets the status: it exits 2 whenever a recipe fails, whatever status the recipe's command had, and when the target is missing. A missing target is therefore a failed command, not an error.
- `output_tail` is the last 30 lines (`OUTPUT_TAIL_LINES`) of the merged output, in the order written; all of it when shorter.
- `last_line` is the last line that is not blank and does not start with `make:` or `make[` (make's own messages); `""` when there is none.
- `duration` is the time the command ran.
- `kill_points` is accepted so that wiring builds every wrapper the same way; this wrapper reaches no kill point.

`CheckResult` (`factory.domain.checks`) is frozen, forbids unknown keys, and has the fields `command`, `status`, `exit_status`, `duration`, `last_line`, `output_tail` and `targets`. `status` and `exit_status` must agree (`status_of(exit_status)` is the one mapping), or validation fails. `passed` is true only for `"passed"`. The result is generic: it carries no layer names (R8), and no identifier in the three modules contains `layer`.

`targets` is a list of `TargetTime` (`target`, `seconds`), one for each line of the whole output (not only the tail) that is exactly `<target>: green (<seconds> s)`, in the order printed; `target_times(output)` reads them. A target printed twice gives two entries, and a project whose Makefile prints no such line gets `[]`. A red target prints no such line. This repository's `Makefile` prints that line for each target, so the factory knows no target names.

`RecordingProjectCommands(inner, git, records, clock, log)` (`factory.application.project_commands`) is the `ProjectCommands` that the wiring hands out: it wraps another implementation (`MakeProjectCommands`) and records every run. `run` reads `git.resolve("HEAD")` (a `GitError` gives `commit=None`) and the clock, runs `inner.run`, appends a `CommandRecord` (`factory.domain.command_records`: command, commit, `started_at`, `duration_seconds`, status, exit status, targets) and returns the inner result unchanged. A `ProjectCommandError` or `ValueError` of the inner run propagates and records nothing. An `OSError` of the append is logged as `cannot write the record of <command>: <error>` and the result is still returned.

The records go through `RecordLog[R]` (`factory.application.files`), an interface for an append-only file of records: `append(record)` raises `OSError` when it cannot write, `read()` gives the records in file order, `[]` without a file, and skips a line that does not validate. `JsonLinesRecordLog(path, model)` (`factory.adapters.record_log_jsonl`) is its implementation: one `model_dump_json()` line per record, written in one write to the file opened for appending, the folder created on the first append. `build_boundaries` points it at `<state directory>/records/project-commands.jsonl`. Tests use `UnwritableRecordLog` (`tests/record_support.py`) for a log that cannot be written.

The disk record uses the same log. `DiskRecord` (`factory.domain.disk`: `at`, `occasion` of `DiskOccasion` = `start` or `acceptance`, and `folders`, a list of `DiskUse` with `path`, `free_bytes` and `used_bytes`, `None` when unknown) is what `Boundaries.disk_records` (optional) holds; `disk_line(record)` is its factory log line. `DiskRecorder(boundaries)` (`factory.application.disk_records`) measures the checkout's parent, the state directory and, when `InstanceSettings.temporary_directory` is set, that directory through `DiskSpace`: `record(occasion)` appends the record, logs its line and returns it (`None` without `disk`, `disk_records` or `settings`; a failed append is logged and the record still returned), and `last()` gives the latest record whatever its occasion. `run_instance` records `start` once; `read_environment_settings` sets `temporary_directory`, `read_settings` does not. `build_boundaries` points the log at `<state directory>/records/disk.jsonl`.

A project declares its own layers and checks them with a project command of its own. To add the layers check, the project adds a make target (for example `layers`, which calls its tool through uv) to its Makefile and, where it belongs in the gate, makes `check` depend on it. The factory sees only that target's `CheckResult`: its status, `last_line` and `output_tail`.

```python
result = MakeProjectCommands(Path(".")).run("check", time_limit=timedelta(minutes=10))
if not result.passed:
    print(result.status, result.exit_status, result.last_line)
```

Tests write a Makefile into `tmp_path` and run the class against it; nothing is faked.

## Starting a process

`subprocess` is imported, and a process started, in `factory.adapters.process` only (R5). The git wrapper, the make class and the `claude -p` runtime each reach their tool through `run_process(request) -> ProcessResult`; no other module calls a command-line tool.

`ProcessRequest` (frozen, unknown keys forbidden) holds:

- `argv`: the program and its arguments, at least one element, passed as given. There is never a shell, so `$HOME; echo x` reaches the child as that text.
- `cwd`: the working directory.
- `env`: `None` lets the child inherit the current environment; a mapping is the child's whole environment, nothing is added.
- `time_limit`: `None` for no limit, otherwise greater than zero (a zero or negative value is a `ValidationError`).
- `merge_stderr`: the child's stderr goes into the same pipe as its stdout, in the order written, and `ProcessResult.stderr` is empty.

The child runs in its own session, with stdin closed. At the `time_limit` the whole process group is killed with SIGKILL, so what the command started ends too, and `run_process` returns with `exit_status=None`, `timed_out=True` and the output written so far. A child that ends in time gives its real exit status and `timed_out=False`; a non-zero status is returned, not raised. Output is decoded as UTF-8 with undecodable bytes replaced. A failure to start, such as `FileNotFoundError`, is an `OSError` and is not caught: the wrapper above decides what it means.

`ProcessResult` also has `stopped` (default `False`, last field): true when `run_streaming` was stopped by its callback.

`run_streaming(request, on_line) -> ProcessResult` is for a runtime that must act on a run's output as it comes (the opencode runtime's budget and provider limit, from F0020-S0004), where `run_process` hands the output over only when the process has ended. It starts the child exactly as `run_process` does (both go through the private `_start`, which holds the module's one `subprocess.Popen(` line) and calls `on_line(stream, line)` for every line of standard output (`"stdout"`) and standard error (`"stderr"`) while the child runs. A line comes without its line feed, decoded as UTF-8 with replacement; a last line without a line feed is passed when its stream ends. With `merge_stderr` every line is `"stdout"`. The calls come one at a time from the calling thread, from a selector loop, not from reader threads.

- `on_line` returns `True` to stop: the process group is killed at once, no further line is passed (also not one already read in the same chunk), and the result has `stopped=True`, `exit_status=None`, `timed_out=False`.
- At the `time_limit` the group is killed as in `run_process` (`timed_out=True`, `stopped=False`, `exit_status=None`), also when the child closed both its streams and kept running. No line read after the kill is passed.
- When `on_line` raises, the group is killed and the exception propagates.
- `stdout` and `stderr` of the result hold what was read up to the end, the stop or the kill (unlike `run_process`, nothing is read after a kill). A child that ends by itself gives its exit status after `on_line` has had every line.

Tests: `tests/adapters/test_process_streaming.py`; the helpers `python_argv` and `is_gone` are in `tests/process_support.py`.

```python
result = run_process(ProcessRequest(argv=["git", "status"], cwd=repo, time_limit=timedelta(seconds=30)))
```

`replace_process(argv, env) -> NoReturn` is the one `exec` of the package: it calls `os.execvpe(argv[0], list(argv), dict(env))`, the program found on the `PATH` of `env`, and the process becomes that program. Only `factory-confine` uses it (see "The start wrapper"). The reason it replaces the process instead of starting a child: the command keeps the wrapper's process and process group, so the `timeout` that wraps the runtime and the factory's kills of the process group still reach it. An empty `argv` raises `ValueError`; a program that cannot be started raises the `OSError` of `os.execvpe` (`FileNotFoundError` for one not on the `PATH`) and this process goes on.

Known limits: after the kill, the output is read without a limit, so a descendant that left the group (by calling `setsid`) and still holds the pipe would block the call; and a child that exits normally but leaves a background process holding its stdout open makes the call wait for that process (bounded by `time_limit` if one is set).

`tests/test_process_search.py` keeps the boundary: only `process.py` imports `subprocess`; `shell=True`, `os.system`, `os.popen`, `os.exec*` (but for the one below), `os.spawn*`, `os.posix_spawn*` and `asyncio.create_subprocess_*` are used nowhere under `src/factory`; the one exception is `os.execvpe` in `process.py`; and the only suppression markers there are the six in `process.py` (`noqa: S404` and `nosec B404` on `import subprocess`, `noqa: S603` and `nosec B603` on the `subprocess.Popen(` line, `noqa: S606` and `nosec B606` on the `os.execvpe(` line). Do not write those marker words in a comment or docstring in `src/factory`. Why: see `docs/decisions.md`. Tests run real child processes (Python one-liners through `sys.executable`) in `tmp_path`; nothing is faked.

## The duplicates report

`make duplicates` prints what the reviewer would otherwise have to spot by eye: blocks of similar code and dead code that no one accepted. It runs pylint (only its duplicate-code messages, R0801, as JSON) and vulture (text), and hands both outputs to `python -m factory.entry.check_duplicates <pylint-json> <vulture-text> --baseline security/duplicates-baseline.txt`. The target and the pipeline step that calls it are added by a later change of the housekeeping feature; the command and the rules below exist now, and pylint and vulture are development dependencies.

The rules are pure functions in `factory.domain.duplicates` (`similar_code_findings`, `dead_code_findings`, `read_baseline`, `compare`, `report_lines`); the command only reads the files, prints and returns the exit status.

### The keys

Each finding has a key that holds no line number, so editing code above or below a finding does not make it new:

- similar code: `similar-code <modules>: <first code line>`. The modules are those the message names, sorted, unique and joined by `, `; the first code line is the first non-blank line after the message's `==<module>:[<start>:<end>]` lines, stripped. Example: `similar-code factory.domain.git, factory.domain.stops: @field_validator("at")`.
- dead code: `dead-code <path>: <message>`, from a vulture line `<path>:<line>: <message> (<n>% confidence)` (with an optional `, <m> lines` before the parenthesis). Example: `dead-code src/factory/x.py: unused function 'helper'`.

The line numbers stay in the finding's `where`, which the report prints. A pylint text or a message that is not in the expected form (not a JSON array, a `duplicate-code` object without a string message, a message without a module line, a malformed `==` line or no code line), and a vulture line out of form, is refused with a `ValueError`; the command turns it into status 2, so a change in a tool's output stops the report and is not hidden.

### The baseline

`security/duplicates-baseline.txt` holds the accepted findings, one key per line; blank lines and lines starting with `#` (after stripping) are skipped. `--baseline <path>` is required. `--write-baseline` writes the file instead of comparing: the header line `# Accepted findings of make duplicates, one key per line.`, then the key of every finding (similar code first, then dead code, in input order, a key found twice written once), and prints `duplicates: baseline of <n> findings written to <path>`. Review the file's diff before committing it: it is the list of what the human accepted.

### The output and the exit status

The command prints, in this order:

- `new <key> at <where>: <message>` for each finding whose key is not in the baseline;
- `gone <key>` for each baseline key that no finding has any more (remove it from the baseline);
- the last line `duplicates: <n> new, <k> known, <g> gone`.

The exit status is 0 when nothing is new (gone keys alone do not change it), 1 when something is new, and 2 when an input file or the baseline cannot be read or a text cannot be parsed; then one line `check-duplicates: <reason>` goes to standard error. Without `--baseline` argparse refuses with status 2.

This repository's pipeline runs the report after the coder and writes its last line into the coder's journal entry, whatever the exit status: the report is a record for the reviewer, not a gate, and `make check` does not run it.

## The document check

`uv run python -m factory.entry.check_documents` reads the four documents and the other files of this guide, and prints `documents ok`, or one finding per line and exits 1. The rule is the pure function `factory.domain.documents.check_documents`; the command only reads the files (`--root` names another checkout). It requires:

- the operator guide's sections *Install*, *Configuration* and *The stops*, with a table row for each row of `STOP_TABLE` that holds the stop's id in backticks and its destination in words;
- the guide's index, `docs/project-guide/README.md`, with its sections *Kill points* and *Fault-injection paths*, with a table row for each case of `KILL_POINT_CASES` and each path of `FAULT_PATHS`, each with its id or test name in backticks;
- none of the phrases of `REPLACED_PHRASES` and none of the v1 words of `GLOSSARY_FORBIDDEN` outside a `## Replaced from v1` section; the decision log is exempt from both lists.

The command also reads every other `.md` file directly in `docs/project-guide/` (`factory.domain.documents.is_guide_file` says which: not the index, no subfolder, no other extension) and checks it for the phrases and the v1 words only, so that a section moved out of the index does not leave the check. Its findings follow those of the four documents, in path order. A folder, a file in a subfolder and a missing folder add nothing.

This repository's pipeline definition (`factory/pipeline.yml`) runs it as a check of the docs stage through `make documents`, so a missing row or a v1 word is found where the four documents are written, before the human sees the pull request; red holds the work item at the docs stage. `make check` does not run it (the decision log, *The four documents are checked by a command*, and its 2026-10-17 entry for the docs stage). A story that adds a row to `STOP_TABLE`, `KILL_POINT_CASES` or `FAULT_PATHS`, changes one of the four documents or changes a file of the guide, runs the check and ends with `documents ok`.

## The demos

`demo/` holds the demos v1.1 ships, one folder per demo `demo/<name>/`, for different kinds of project. A demo has three parts:

- `README.md`: what the demo is.
- `project/`: the project as the factory would find it. It holds `factory/pipeline.yml` (the pipeline definition) and `factory/story-form.md` (the story form).
- `features/`: the features and stories the factory is given, as `features/<feature>/feature.md` and `features/<feature>/backlog/<story>.md`. They stand beside `project/` and not under `project/factory/features/`, because the demo is the input of a run and the stories are not part of the project yet.

`demo/README.md` is the index and names each demo as its folder in backticks, such as `` `todo/` ``, on a line of its own text.

`uv run python -m factory.entry.check_demos` (`--root <path>` names another root; the default is the current directory) prints `demos ok` and exits 0, or prints one finding per line, demos in name order, and exits 1. `check_demos(root)` returns the findings. It finds, in this order:

- no `demo/` folder: nothing; a `demo/` without `README.md`: `demo/README.md: missing`;
- for each folder of `demo/` (loose files and folders that start with `.` are skipped): an index that does not name it; a missing `README.md`, `project/` or `features/`; a missing or refused `project/factory/pipeline.yml` (`RuamelPipelineDefinitionReader` reads it, through `build_pipeline_definition_reader()` of `factory.entry.wiring`); a missing `project/factory/story-form.md`, after which no story is checked;
- each file under `features/`, in path order: any file that is not a `feature.md` directly in a feature folder or a `.md` file in its `backlog/` folder is a finding.

A demo's stories are backlog stories checked at the path they will have in the project, `factory/features/<feature>/backlog/<story>.md`, with the story check's own rules (see *The form check of a story*): `check_demos` calls `backlog_story_findings` and `finding_line` of `factory.entry.check_story`, the same code `factory-check-story` runs for a backlog story, so a demo story and a project story give the same findings. A finding is `demo/<name>/features/<rest>: <message>`, with `:<line>` before the message when it has a line. The story form is the demo's own.

`make check` runs the check through `tests/test_demos.py`, which expects `main` to return 0 for this repository, so a demo that goes stale fails the build. The code knows no demo by name (see the decision log); a new demo is a new folder and a line in the index.

## Mutation testing

`make mutants FEATURE=<id>` (for example `FEATURE=F0012`) runs mutmut over the modules under `src/factory` that the commits of that feature changed. It finds them by the feature's id in the commit subjects on `origin/main`. It is not part of `make check`: it is slow, and the feature acceptance runs it. On v1's acceptance branch `acceptance/<id>-<slug>` the id is read from the branch name, so plain `make mutants` works there.

The recipe runs mutmut with `TMPDIR` set to a folder of its own, made by `mktemp -d`, and its `EXIT` trap opens that folder for its owner and removes it when the recipe ends, also after `mutants: stopped after ...` and after a failed run. So every pytest that mutmut starts keeps its base folders there, and a run leaves `/tmp/pytest-of-<user>` as it found it. Why, and the ways rejected, is in the decision log (*make mutants runs under a temporary root of its own*).

The acceptance reads the survivors with `uv run mutmut results` and `uv run mutmut show <name>`. The target drops mutmut's `not checked` lines, but it lists every survivor and timeout that `mutants/` holds, including those that earlier runs left for earlier features' modules. So the acceptance reads the survivors of its own feature's modules by their module name, for example `uv run mutmut results | grep 'factory.application.stage\.'`.

Two ends are not a run. Without `FEATURE` the target prints `mutants: set FEATURE, as in make mutants FEATURE=F0012` and exits 2. A feature with no changed module prints `mutants: no module under src/factory changed by <id>` and exits 0. Which subjects it reads, and why only one feature's modules, is in the decision log (*Mutation testing is limited to one feature's modules*).
