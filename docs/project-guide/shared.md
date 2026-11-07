# Processes and this repository's checks

This file covers the one module that starts processes and the commands behind this repository's checks. Read the index, [README.md](README.md), first. The rest of the area `shared` is described where it is used.

## Starting a process

Every command-line tool the factory runs is started in one module, [process.py](../../src/factory/shared/adapters/process.py) (`factory.shared.adapters.process`). It runs a program without a shell, in its own process group, with a time limit, and it kills the group when the limit passes. A wrapper such as the git wrapper never calls `subprocess` itself.

    run_process(request: ProcessRequest) -> ProcessResult
    run_streaming(request: ProcessRequest, on_line: Callable[[Stream, str], bool]) -> ProcessResult
    run_or_raise(argv, *, time_limit, fault, cwd=ROOT, accepted=(0,)) -> ProcessResult

- Only `process.py` imports `subprocess`. Nine other modules import `process.py`, as [test_wrapper_search.py](../../tests/guards/test_wrapper_search.py) lists them.
- These modules use `run_process`:
  - the git wrapper, [git_cli.py](../../src/factory/hosting/adapters/git_cli.py);
  - the make class, [make_commands.py](../../src/factory/machine/adapters/make_commands.py);
  - the `claude -p` runtime, [claude_runtime.py](../../src/factory/agents/adapters/claude_runtime.py);
  - the tests' container fake, [fake_containers.py](../../src/factory/machine/adapters/fake_containers.py);
  - the example runner of the document check, [document_examples.py](../../src/factory/shared/adapters/document_examples.py).
- The opencode runtime, [opencode_runtime.py](../../src/factory/agents/adapters/opencode_runtime.py), uses `run_process`. For a run it watches line by line, it uses `run_streaming`.
- The Podman wrapper, [podman_runs.py](../../src/factory/machine/adapters/podman_runs.py), uses `run_process` for a container run. It uses `run_or_raise` for its queries.
- The ZFS wrapper, [zfs_snapshots.py](../../src/factory/machine/adapters/zfs_snapshots.py), uses `run_or_raise` only. So does the power-off, [power_off.py](../../src/factory/machine/adapters/power_off.py).
- `ProcessRequest` holds `argv`, `cwd`, `env`, `time_limit` and `merge_stderr`; it is frozen and forbids unknown keys.
- `argv` has at least one element and is passed as given. There is never a shell, so `$HOME; echo x` reaches the child as that text.
- `env=None` lets the child inherit the environment. A mapping is the child's whole environment, and nothing is added.
- `time_limit` is `None` or greater than zero. A zero or negative value is a `ValidationError`.
- The child runs in its own session, so it leads its own process group, and its stdin is closed.
- At the `time_limit` the group is killed. `run_process` returns `exit_status=None`, `timed_out=True` and the output written so far.
- A child that ends in time gives its real exit status and `timed_out=False`. A non-zero status is returned, not raised.
- A failure to start, such as `FileNotFoundError`, is an `OSError` that `run_process` does not catch. The wrapper above decides what it means.
- `run_process` hands the output over only when the process has ended.

The call looks like this:

    result = run_process(ProcessRequest(argv=["git", "status"], cwd=repo, time_limit=timedelta(seconds=30)))

### Reading output and killing a group

Output is read until both pipes close. A process that left the group and keeps a pipe open must not hold the call, so the read is bounded after the child's end.

- `PIPE_DRAIN` is five seconds. It is read at each call, so a test sets it with `monkeypatch.setattr`.
- Once the child has ended on its own, both functions read on until both pipes close or `PIPE_DRAIN` has passed. If the pipes did not close, they close them and return the child's own exit status with `timed_out=False`, `stopped=False` and every byte read. `run_streaming` has by then passed every complete line to `on_line`.
- A time limit that falls before the child's end, or during the drain, is a `timed_out` call. After that kill `run_process` reads what is left for at most `PIPE_DRAIN` and closes the pipes. The bound holds also for a request without `time_limit`.
- The kill is `os.killpg(process.pid, signal.SIGKILL)`. A group already gone (`ProcessLookupError`) is no error, and a `PermissionError` propagates.
- The kill reads no process table and does not wait for the group's processes to end. A grandchild may still be ending for a moment after the kill returns.
- The child is not yet reaped, so its id, which is the group's, cannot belong to an unrelated process meanwhile.
- A descendant that takes a process group or a session of its own (`setpgid`, `setsid`, GNU `timeout` without `--foreground`) is not killed. In a container it ends with the container.
- A line that such a holder writes later than `PIPE_DRAIN` after the child's end is lost to the result.

No agent code runs on the host: every agent call and every [project command](glossary.md) runs in a container, which ends whole with its call. What the factory starts on the host is git, `zfs`, `podman` and the `sudo -n /usr/bin/systemctl poweroff` of the power-off, so a group is enough.

### run_streaming

`run_streaming` is for a runtime that must act on a run's output as it comes, such as the opencode runtime with its budget and its provider limit. It starts the child as `run_process` does and calls `on_line(stream, line)` for every line of standard output, which is `"stdout"`. It does the same for standard error, which is `"stderr"`.

- A line comes without its line feed, decoded as UTF-8 with replacement. With `merge_stderr` every line is `"stdout"`.
- A last line without a line feed is passed when its stream ends, not when the drain runs out. Its bytes stay in `stdout`.
- The calls come one at a time from the calling thread, from a selector loop, not from reader threads.
- A line reaches the callback once and whole, however many reads it takes. A line longer than one 64 KiB read, or one split by a pause, is passed once.
- `stdout` and `stderr` of the result hold the whole output.
- `on_line` returns `True` to stop. The group is killed at once, no further line is passed (also not one already read in the same chunk), and the result has `stopped=True`, `exit_status=None` and `timed_out=False`.
- A stop on a last line without a line feed ends the call at once, also while the other stream is still open.
- At the `time_limit` the group is killed as in `run_process`, also when the child closed both streams and kept running. No line read after the kill is passed.
- When `on_line` raises, the group is killed and the exception propagates.
- The result holds what was read up to the end, the stop or the kill. Unlike `run_process`, nothing is read after a kill.
- A child that ends by itself gives its exit status after `on_line` has had every line.

### run_or_raise

`run_or_raise` is the block that a wrapper of a short command repeats, written once. It runs `ProcessRequest(argv=argv, cwd=cwd, env=None, time_limit=time_limit, merge_stderr=True)` and returns the result. `fault` is the wrapper's own error, called with one detail string. The helper raises what it returns.

- A program that cannot start (`OSError`) raises `fault(str(error))`, chained from the `OSError`.
- A call that reached `time_limit` raises `fault(no_end_detail(time_limit))`.
- An exit status not in `accepted` raises `fault(failure_detail(result.stdout, result.exit_status))`. `accepted=None` returns every exit status.
- `ROOT` is `Path("/")`, the default `cwd`: these commands read no file from their working directory.
- `ZfsSnapshots._execute` passes `SnapshotError` with the command as first argument, and the caller's `accepted`.
- `SystemctlPowerOff.power_off` passes `PowerOffError`. It prefixes `cannot start <sudo>: ` to the detail when the cause is an `OSError`.
- `PodmanRuns._query` passes `ContainerError` with the command, the workspace as `cwd` and `accepted=None`.
- `PodmanRuns.run` keeps its own `ProcessRequest`, because it passes the launch's environment. It uses `cwd=ROOT`.
- A wrapper that needs more builds its own request and calls `run_process`.

### The boundary and its tests

[test_process_search.py](../../tests/guards/test_process_search.py) keeps the boundary.

- Only `process.py` imports `subprocess`.
- `shell=True`, `os.system`, `os.popen`, `os.exec*`, `os.spawn*`, `os.posix_spawn*` and `asyncio.create_subprocess_*` are used nowhere under `src/factory`.
- The only suppression markers there are the four in `process.py`. Two sit on the import of `subprocess` and two on the `subprocess.Popen(` line; the *Reference* names them.
- Do not write those marker words in a comment or docstring in `src/factory`.
- The tests run real child processes (Python one-liners through `sys.executable`) in `tmp_path`. Nothing is faked.
- A test whose child must act before its time limit ends it takes `ROOMY_LIMIT` (10 s) from [time_limits.py](../../tests/support/time_limits.py). Such a child writes a record or a pid file, prints a line or finishes a first call.
- The same module gives `ROOMY_BOUND_SECONDS` (25) for an elapsed-time bound. The stand-ins the limit must end wait longer than the bound, so a missed kill fails.
- A child that need not start to be killed may keep a shorter limit.

See also: *A command stopped at its time limit loses every process of its session* and *A call stops reading five seconds after its own process ended* in [decisions.md](../decisions.md).

## The duplicates report

`make duplicates` prints what the reviewer would otherwise have to spot by eye: blocks of similar code and dead code that no one accepted. It runs pylint for its duplicate-code messages, R0801, as JSON. It also runs vulture, as text. Both are development dependencies. It hands both outputs to the command, which compares the findings with the baseline of accepted ones in [duplicates-baseline.txt](../../security/duplicates-baseline.txt). The report is a record for the reviewer, not a gate.

The command is [check_duplicates.py](../../src/factory/entry/check_duplicates.py). The rules are pure functions in [duplicates.py](../../src/factory/shared/domain/duplicates.py). The command only reads the files, prints and returns the exit status.

    uv run python -m factory.entry.check_duplicates <pylint-json> <vulture-text> --baseline security/duplicates-baseline.txt
    similar_code_findings, dead_code_findings, read_baseline, compare, report_lines

- The command reads its three files through `read_input` of [inputs.py](../../src/factory/entry/inputs.py). `read_input` raises `UnreadableInput` for a file that is missing or not UTF-8, and the command turns that into status 2, like a parse fault.
- The pipeline runs the report after the coder and writes its last line into the coder's [journal](glossary.md) entry, whatever the exit status. `make check` does not run it.
- A pylint message or a vulture line out of form is refused with a `ValueError`. The command turns it into status 2, so a change in a tool's output stops the report and is not hidden.
- The output has three parts, in this order.
  - `new <key> at <where>: <message>` for each finding whose key is not in the baseline.
  - `gone <key>` for each baseline key that no finding has any more. Remove it from the baseline.
  - The last line, `duplicates: <n> new, <k> known, <g> gone`.
- The exit status is 0 when nothing is new. Gone keys alone do not change it.
- The status is 1 when something is new.
- The status is 2 when a file or the baseline cannot be read or a text cannot be parsed. Then one line `check-duplicates: <reason>` goes to standard error.
- Without `--baseline` argparse refuses with status 2.

### The keys and the baseline

Each finding has a key that holds no line number, so editing code above or below a finding does not make it new. The line numbers stay in the finding's `where`, which the report prints.

- Similar code: `similar-code <modules>: <first code line>`. The modules are those the message names, sorted, unique and joined by `, `.
- The first code line is the first non-blank line after the message's `==<module>:[<start>:<end>]` lines, stripped. Example: `similar-code factory.hosting.domain.git, factory.pipeline.domain.stops: @field_validator("at")`.
- Dead code: `dead-code <path>: <message>`, from a vulture line `<path>:<line>: <message> (<n>% confidence)`. An optional `, <m> lines` may stand before the parenthesis. Example: `dead-code src/factory/x.py: unused function 'helper'`.
- A pylint message is refused when it is not a JSON array. It is also refused when a `duplicate-code` object has no string message.
- It is refused too when a message has no module line, a malformed `==` line or no code line.

The baseline holds the accepted findings, one key per line. Blank lines and lines starting with `#` (after stripping) are skipped.

- `--baseline <path>` is required.
- `--write-baseline` writes the file instead of comparing. It writes the header line `# Accepted findings of make duplicates, one key per line.`. Then it writes the key of every finding: similar code first, then dead code, in input order. A key found twice is written once. It prints `duplicates: baseline of <n> findings written to <path>`.
- Review the file's diff before committing it: it is the list of what the human accepted.
- The baseline accepts the process calls of the two agent runtimes and the fakes that only the tests use. These are `ManualClock` and `ManualWaiter` in [clock.py](../../src/factory/shared/adapters/clock.py), `FakeAgentRuntime` in [fake_agent_runtime.py](../../src/factory/agents/adapters/fake_agent_runtime.py) and `FakeHostingService` in [fake_hosting.py](../../src/factory/hosting/adapters/fake_hosting.py). A new finding there is a copy that the decision does not cover.

See also: *What the agent runtimes share lies in one module* in [decisions.md](../decisions.md).

## The document check

`make documents` runs the document check. It reads the README, the two guides and the decision log, prints one finding per line and exits 1, or, when nothing blocks, ends with `documents ok (<seconds> s)`. It is a check of the docs [stage](glossary.md), not of `make check`. A missing row or an old word is found where the documents are written, before the human sees the pull request. Red holds the [work item](glossary.md) at the docs stage.

The command is [check_documents.py](../../src/factory/entry/check_documents.py) and only reads files. `--root` names another checkout. The rules are pure functions in [documents.py](../../src/factory/shared/domain/documents.py), above all `check_documents`.

    uv run python -m factory.entry.check_documents [--root <checkout>]

A [story](glossary.md) that adds a row to `STOP_TABLE`, `KILL_POINT_CASES` or `FAULT_PATHS` runs the check. So does a story that changes one of the four documents or a file of the guide. Each ends with `documents ok`.

- The four documents are the README, the operator guide, the project guide and the decision log. The operator guide is its index [README.md](../operator-guide/README.md) and ten topic files, listed in `OPERATOR_GUIDE_FILES`. A missing one is reported as `docs/operator-guide/<file>: missing`.
- The operator guide must have the sections *Install* and *Configuration* in [install.md](../operator-guide/install.md) and *The stops* in [stops.md](../operator-guide/stops.md). The last has a table row for each row of `STOP_TABLE`, holding the [stop](glossary.md)'s id in backticks and its destination in words.
- The decision log must hold at least one decision. An absent or empty file is reported as `missing` or `empty`, and a log without one is reported as `no decision recorded`.
- The guide's index, `docs/project-guide/README.md`, must have the sections *Kill points* and *Fault-injection paths*. Each has a table row for each case of `KILL_POINT_CASES` and each path of `FAULT_PATHS`, with its id or test name in backticks.
- None of the phrases of `REPLACED_PHRASES` and none of the retired words of `GLOSSARY_FORBIDDEN` may stand outside a `## Replaced from v1` section. The decision log is exempt from both lists.
- Every other `.md` file directly in `docs/project-guide/` is read too. It is read for the phrases and the retired words only, so that a section moved out of the index does not leave the check.
- `is_guide_file` says which files: not the index, none in a subfolder, no other extension. Its findings follow those of the four documents, in path order.
- A folder, a file in a subfolder and a missing folder add nothing.
- The [pipeline definition](glossary.md), [pipeline.yml](../../factory/pipeline.yml), runs it through `make documents` as a check of the docs stage. `make check` does not run it.

### The checked documents and the report

[checked-documents.txt](../checked-documents.txt) lists the documents whose findings of the name, settings and example checks fail the command. A document is added to the list when it has been rewritten. The list is complete when every document is on it.

    read_checked_documents(text: str) -> list[str]
    split_findings(findings: Sequence[GatedFinding], checked: Collection[str]) -> SplitFindings

- One path per line. `#` starts a comment, and blank lines are skipped. A missing file is an empty list.
- A listed path that does not exist, or that is not a document the check reads (`docs/decisions.md`, for example), is one blocking finding.
- `split_findings` makes the split from the document each finding carries.

The output has three parts, in this order:

1. One line per blocking finding: the checks of the four documents for every document, and the name, settings and example checks for the listed ones.
2. The heading `Report (not checked yet):`, the other findings of those checks, then the `not run` lines of skipped examples. The heading is left out when there is nothing to report. A `not run` line never blocks, also for a listed document.
3. When nothing blocks, the last line `documents ok (<seconds> s)`. Otherwise there is no such line and the exit status is 1.

### The name check

The command prints one line per name a document writes that does not exist, as `<document>:<line>: <name> does not exist`. Whether such a line blocks depends on the document.

It reads `README.md`, `operator/README.md`, every folder README of `FOLDER_READMES` (see below) that exists, and every `.md` file under `docs/operator-guide/` and `docs/project-guide/`. `docs/decisions.md` and `docs/runs/` are not read. The pure functions are `named_references`, which finds the names with their lines, and `unresolved`, which turns the refused ones into findings.

    named_references(document: str, text: str, top_level: frozenset[str]) -> list[Reference]
    unresolved(references: list[Reference], exists: Callable[[Reference], bool]) -> list[str]

The command gives them the checkout's top-level entries and the real test of existence. Three kinds of reference are found:

- **A module or attribute:** a backticked dotted name that starts with `factory.`. It exists when `importlib` imports the longest leading part that is a module and the rest are attributes of it in turn, as `factory.shared.domain.documents.named_references` does. Other dotted names, such as `os.path`, are not checked.
- A name that ends in `.env`, `.service`, `.yml`, `.yaml`, `.json`, `.jsonl`, `.toml`, `.md`, `.txt` or `.log` is a file name (`factory.env`, `factory.log`, `factory.records.jsonl`) and is not checked.
- **A repository path:** a backticked text that contains `/` and no `$`. A text with `$` is a shell expression and is skipped as a whole.
- In a pytest node id (a test file, then `::`, then the test name) only the path before `::` is read.
- The text has no whitespace, does not start with `/` or `~`, and has no `:` before its first `/`.
- So a web address such as `https://host/x` is no path, and neither is a scp-style git address such as `git@github.com:owner/project.git`. A `:` after the first `/` changes nothing.
- It must either start with a top-level entry of the checkout or end in a file name with an extension. So a path whose first folder was renamed is still checked, and `origin/main` is not a path.
- It exists when it resolves to something inside the checkout.
- **A link:** the target of a relative Markdown link, read from the document's own folder (`../` included) with any `#fragment` left off. A web address, a `mailto:` address, an absolute path and a link to a heading alone (`#...`) are not checked.

Never checked, whatever the kind: a placeholder in angle brackets such as `<instance>`, a glob such as `*` and an absolute path such as one under `/srv` or `/etc`. Anything inside a fenced code block is not checked either. The same holds for a section headed `## Replaced from v1` or `## Replaced in v1.2`, up to the next `##` heading. A name after that heading is checked again.

**A reference to another page's heading.** `factory.shared.domain.heading_references` checks the one form in which the documents point to a section of another page: a heading in italics (`*...*`) or in double quotes, then an optional `)` or `,`, then `in` or `of`, then a relative link to a `.md` file, as in `see *The idle shutdown* in [machine.md](../operator-guide/machine.md)`. `heading_references` finds these references with their lines, and `unresolved_headings` turns the ones whose heading the linked page lacks into findings:

    heading_references(document: str, text: str) -> list[HeadingReference]
    unresolved_headings(references: list[HeadingReference], headings: Callable[[str], set[str] | None]) -> list[str]
    page_headings(text: str) -> set[str]

A finding reads `<document>:<line>: <heading> is no heading of <target>` and blocks or is reported by the same rule as the other findings of the name check. The command builds `headings(target)` from `page_headings`, the heading lines of the linked page at every level with only the backticks and asterisks removed, so `StageFinisher.finish` is not `StageFinisher.finish(aftermath)`: the reference names the heading as the page writes it. Not checked: plain text before `in` (`described in [machine.md](machine.md)`), another mark than `)` or `,` between the heading and `in`, a link with a `#` anchor, a link to a file that is not `.md`, a link to the document's own file, and a link to a page that is no document of the check (`headings` gives `None`). Only the span right before `in` counts when a line holds several. A paragraph that has a bold name and no heading of its own is named in the sentence (`the paragraph *In a job* under *The idle shutdown* in [machine.md](../operator-guide/machine.md)`), so that the heading right before `in` is a real one.

### The folder READMEs

`FOLDER_READMES` in [folder_readmes.py](../../src/factory/shared/domain/folder_readmes.py), the module `factory.shared.domain.folder_readmes`, lists the path of every folder README of the repository, 23 in all. Each is a short pointer from a folder to the guide pages that explain it. Its form and limits are in *Folder READMEs* in [style.md](style.md).

    readme_problems(folder: str, readme: str | None, subfolders: Sequence[str]) -> list[str]

- `readme_problems` gives one sorted line per disagreement between a README and its folder, or `[]`. A `None` README gives `<folder>: no README.md`.
- The guard [test_folder_readmes.py](../../tests/guards/test_folder_readmes.py) runs it on every README of the list that exists, with the subfolders read from the folder (hidden folders and `__pycache__` left out). A README that does not exist yet is skipped with its path. Another test requires every path to end in `/README.md` and name a folder that exists, and another requires a README on the list for every package directly under `src/factory/`.
- The name check reads each listed README that exists, and `operator/README.md`, which keeps its own form and is not on the list. A missing module or path a README names is a finding. It blocks when the README is on [checked-documents.txt](../checked-documents.txt), and is reported otherwise.
- A listed path with no file is no finding of the name check. It is a blocking finding only when it is also on `checked-documents.txt`, as for any listed path that does not exist.
- A link counts as relative by the same function, `relative_link_targets` of [documents.py](../../src/factory/shared/domain/documents.py), in the form check and the name check: a web address, a path starting with `/`, a `mailto:` address and a link to a heading alone are no relative link.

### The examples

After the settings lines the command runs the `console` blocks of every document it reads for names. How to write one is in [style.md](style.md), *Runnable examples*. This section is the machinery. [document_examples.py](../../src/factory/shared/application/document_examples.py) holds the two interfaces `Fixture` and `ExampleRunner`.

    examples(text: str) -> Examples
    first_difference(expected: Sequence[str], actual: Sequence[str]) -> int | None
    Fixture.prepare(folder)
    ExampleRunner.run_document(document, examples, fixtures)

- `examples(text)` of `documents.py` returns `Examples` with `runnable` and `skipped`. A runnable `Example` holds its line, its fixture and its `Command`s with their expected lines. A `Skipped` holds a line and a kind.
- The spaces or tabs before a block's opening fence are removed from each of its lines before they are read. So a block indented under a numbered step reads as at column 0, with the same line numbers. A line indented less than the fence keeps what it has.
- A `console` block with no `$ ` line is neither runnable nor skipped. Its fence line is in `without_command`.
- The command turns each such line into the finding `<document>:<line>: the example has no command`, named `NO_COMMAND`.
- It goes through the same path as the runner's findings. So it blocks in a listed document and is reported in any other.
- A block marked `vm`, `github` or `model`, or with a command for which `runs_the_suite` holds, is skipped. A line for a skipped block reads `<document>:<line>: not run (<kind>)`.
- `first_difference` is the match, with `...` and `<placeholder>`.
- `Fixture.prepare(folder)` fills an empty folder and returns the extra environment. `ExampleRunner.run_document(document, examples, fixtures)` returns the document's findings.
- `ProcessExampleRunner` of `document_examples.py` runs each command through `run_process` as `env -i <variables> sh -c <command>`.
- The fixed variables come last, so a fixture cannot replace `PATH`, `HOME`, `TZ` or `LANG`.
- Its default limit is 60 seconds, and a test passes a shorter one.
- The folder and the home are temporary and removed when `run_document` returns, also after a timeout.
- `CheckoutFixture` of [checkout_fixture.py](../../src/factory/hosting/adapters/checkout_fixture.py) is the fixture `checkout`. It exports the tracked files of the checked commit through `GitCli.export`. It raises `FixtureError` outside a git repository. The runner then gives one finding, `fixture <name> could not be prepared`, at the block's line and runs none of the document's commands on that fixture.
- `InstanceFixture(git)` of [instance_fixture.py](../../src/factory/hosting/adapters/instance_fixture.py) is the fixture `instance`. Its name `INSTANCE_FIXTURE` is in `documents.py`. `prepare(folder)` does this:
  - It makes the bare remote `<folder>/remote.git` with `GitCli.clone_bare`.
  - It writes a healthy health file in `<folder>/state`, named by `HEALTH_FILE_NAME` in [health_file.py](../../src/factory/watching/adapters/health_file.py), the name `factory-health` reads.
  - It makes the image id file and the empty agent home, workspace and copy base.
  - It writes `<folder>/factory.env`, one `NAME=value` line for each variable it returns.
  - A `GitError` becomes a `FixtureError`, as for `checkout`.
- `check_documents.py` wires the runner and the two fixtures.

### The settings check

The settings code is the one source of the [instance](glossary.md)'s settings. `factory.shared.domain.settings.SETTINGS`, in [settings.py](../../src/factory/shared/domain/settings.py), is a tuple of `SettingDoc` with one row for each variable `read_settings` reads, `FACTORY_DATASET` and `FACTORY_STAGE_IMAGE` included. The command compares it with the operator guide.

    SettingDoc(name, required, default)    # frozen
    guide_tables(text, section) -> list[GuideTable]
    settings_findings(guide_tables, SETTINGS)
    refusal_findings(guide_tables, settings_source)

- `required` is `yes`, `no` or a condition such as `with zfs`. It is kept for whoever writes the guide and is never compared.
- `default` is `None` where the code has none. The other defaults are built from the module's own constants, so the table cannot drift from what `read_settings` applies.
- A story that makes `read_settings` read another variable adds its row. [test_settings_table.py](../../tests/shared/domain/test_settings_table.py) calls `read_settings` with a mapping that records every key looked up and compares those keys with the names in `SETTINGS`.
- The command reads the section *Configuration* of `docs/operator-guide/install.md` with `guide_tables`. It returns the tables of the section and its subsections as `GuideTable` (`heading` is the nearest heading above the table, then `header` and `rows`).
- Both finding functions are pure, and each line is prefixed with the guide's path.
- Like the name and example findings, they follow the list of checked documents. In a listed `docs/operator-guide/install.md` they block the command with exit status 1. In an unlisted one they are only reported after the heading.
- `settings_findings` counts only a table whose first column is `Name` or `Variable`. Any other table is ignored, such as one with the first column `Setting` or one under another heading.
- A setting the code reads and no such table names, and a name that no setting has, are one finding each.
- A default is compared only in a table with a `Default` column, against `SettingDoc.default`. Without that column only names are compared.
- The cell is read as the name cell is: its first backticked text if it has one, the whole cell otherwise. A finding quotes the cell as written.
- `None` matches an empty cell or `none`.
- When no table counts and `SETTINGS` is not empty, the one finding is `no settings table (first column Name or Variable) in Configuration`. So the check says that it cannot compare instead of passing silently. With an empty `SETTINGS` there is no finding.
- A missing `install.md` or a missing *Configuration* section adds no settings finding. `check_documents` skips both settings checks there, and the operator guide's own finding stands.
- `refusal_findings` counts only a table under the heading `The refusals` whose first column is `Refusal`. A refusal is the backticked text of its first cell.
- Its `<placeholder>`s are cut out, and the whitespace and colons at both ends of each remaining piece are removed, so `<variable>: <fault>` looks up the fault alone.
- Each piece of three characters or more must occur in `settings_source`, which the command takes from the source file of `factory.shared.domain.settings`. A text no source holds is one finding.
- The operator guide's tables in `install.md` have a `Default` column, and it has a refusal table. The check compares both.

### How the check is tested

The tests of the check never read the repository's documents or its `docs/checked-documents.txt`, and they run no example of the real documents. So `make check` does not grow with the documents, and a rewrite of a document breaks no test. The real documents are checked by `make documents` alone, which runs in every docs stage.

A test starts from `minimal_documents(root)` of [minimal_documents_support.py](../../tests/support/minimal_documents_support.py). The fixture `minimal` of [conftest.py](../../tests/conftest.py) calls it for `tmp_path / "root"`.

    minimal_documents(root)
    add_and_commit(root, {path: text})

- It writes a git repository in one commit with the smallest documents the check accepts.
  - They are the README, the operator guide's index and every file of `OPERATOR_GUIDE_FILES`.
  - They are also the project guide's index, one page for each area and an empty `docs/checked-documents.txt`.
- It builds them with `clean_texts()` of [document_texts.py](../../tests/support/document_texts.py). That reads `STOP_TABLE`, `KILL_POINT_CASES`, `FAULT_PATHS` and `SETTINGS` from the modules that define them each time it is called. So the documents follow the code's tables, and a test can extend a table with `monkeypatch`.
- On them `main(["--root", str(root)])` prints `documents ok (<seconds> s)` alone. They hold no runnable example.
- A test adds what its rule needs and nothing more.
- `add_and_commit` writes the files and commits them, and leaves `git status --porcelain` empty. It commits only when the work tree changed.
- `append_block`, `write_checked_list(root, paths)` and `drop_settings_row` of [check_documents_support.py](../../tests/support/check_documents_support.py) add a block to a document, write the list of checked documents and remove a settings row. `write_checked_list` commits only a change, so writing the list that is already there is no error.
- [test_document_tests_write_their_documents.py](../../tests/guards/test_document_tests_write_their_documents.py) fails when a module under `tests/entry/` that imports `factory.entry.check_documents` names `operator_support.ROOT`, `tracked_files`, `documents_copy_support` or the path `docs/checked-documents.txt`.

See also: *The four documents are checked by a command, outside `make check`; v1's words live in one section* in [decisions.md](../decisions.md).

## Reference

Exact detail that the sections above summarise.

- `ProcessResult` fields: `exit_status`, `stdout`, `stderr`, `timed_out`, `duration` and `stopped` (default `False`). `stopped` is true when `run_streaming` was stopped by its callback. A call that closes a pipe still open after the drain says so in no field.
- `ProcessRequest.merge_stderr`: the child's stderr goes into the same pipe as its stdout, in the order written, and `ProcessResult.stderr` is empty.
- Output is decoded as UTF-8 with undecodable bytes replaced.
- Both functions read in steps of at most 0.05 s and check in between whether the child has ended.
- They check with `os.waitid(..., WNOWAIT)`, which does not reap the child. So a kill at the time limit during the drain still signals a process group that is the child's.
- `run_process` and `run_streaming` both start the child through the private `_start`, which holds the module's one `subprocess.Popen(` line. Both kill through the private `_kill_session`, at the time limit, at a stop by `on_line` and when `on_line` raises.
- The tests of the process module:
  - [test_process_session.py](../../tests/shared/adapters/test_process_session.py) tests the kill.
  - [test_process_streaming.py](../../tests/shared/adapters/test_process_streaming.py) tests `run_streaming`.
  - [test_process_streaming_reads.py](../../tests/shared/adapters/test_process_streaming_reads.py) tests long and split lines.
  - [test_process_streaming_last_line.py](../../tests/shared/adapters/test_process_streaming_last_line.py) tests a stop on a last line without a line feed.
  - [test_process_drain.py](../../tests/shared/adapters/test_process_drain.py) tests the drain.
  - [test_run_or_raise.py](../../tests/shared/adapters/test_run_or_raise.py) tests `run_or_raise`.
  - The helpers `python_argv` and `is_gone` and the callback `Recorder` are in [process_support.py](../../tests/support/process_support.py).
- The suppression markers in `process.py`: `noqa: S404` and `nosec B404` on `import subprocess`, `noqa: S603` and `nosec B603` on the `subprocess.Popen(` line.
- `PIPE_DRAIN` is `timedelta(seconds=5)`.
- The settings table columns the check reads: `Name` or `Variable` first, `Default` for defaults, `Refusal` for the table under `The refusals`.
- The types of the check:
  - `Examples`: `runnable`, `skipped`, `without_command`.
  - `Example` and `Command`.
  - `Skipped`: line and kind.
  - `GuideTable`: `heading`, `header`, `rows`.
  - `SettingDoc`: `name`, `required`, `default`.
