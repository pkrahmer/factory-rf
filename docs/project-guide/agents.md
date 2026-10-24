# The agent runtime, the agent files and the template

This file covers the agent runtime, the agent files, the shipped agents and the template; read the index, `README.md`, first.

## The agent runtime

The factory reaches an agent only through the `AgentRuntime` interface (an abstract base class, `factory.application.agent_runtime`): `run(request) -> AgentRunResult` and `version() -> str`. The DTOs are in `factory.domain.agent_runs`. All are frozen and forbid unknown keys. The `claude -p` implementation is `ClaudeCodeRuntime` and the `opencode run` implementation is `OpencodeRuntime` (both below); each inherits `AgentRuntime`. The fake is the third implementation.

`AgentRunRequest` holds:

- `agent`: an `AgentDefinition` (`name`, `model`, `tools`, `effort` or `None`, `budget_usd` greater than 0, `instructions`). `name` is a `Name` (`factory.domain.identifiers`): lower-case letters, digits and hyphens, starting with a letter.
- `prompt`, `time_limit` (greater than zero) and `working_directory` (absolute).
- `allowed_decisions`: must contain `QUESTION` (`"question"`) and have no repeats, so an agent can always ask the human. The validation error names `question`.
- `environment`: the run's whole environment, `{}` by default; `guard`: optional `GuardSettings` (absolute `root`, `write_paths`, `protected_paths`); `os_user`: optional; `TaskComposer` fills it with `boundaries.settings.agent_user`.

`AgentRunResult` holds `end_reason`, `decision`, `entry`, `duration`, `turns`, `tokens` (`TokenCounts`: `input`, `output`, `cache_read`, `cache_creation`, none negative), `cost_usd`, `permission_denials` and `login`. `login` (`Login = Literal["api_key", "subscription", "none"]`) is the login the run's calls were handed, `None` when the runtime has no login file; unlike `decision` and `entry` it is set whatever the end reason, and a resumed run's is that of its last call. `end_reason` is one of `completed`, `no_result`, `time_limit`, `budget`, `died` and `provider_limit`. `session` is the runtime's own id of the session the run used, set by both runtimes whatever the end reason (`None` when the runtime never learned one); `limit_wait` (a positive `timedelta`) is set only on a `provider_limit` run, and a result of any other end reason with a `limit_wait` is refused (`a run that ended by <reason> has no limit_wait`). `AgentRunRequest.resume_session`, when set, is not blank and names a session the same runtime made: the run continues it with the request's prompt and budget. `decision` and `entry` are set exactly when the run is `completed`, and `ok` is true exactly then. A measure the runtime did not report is `None`, never 0: unknown is unknown.

A run that dies, reaches its `time_limit`, exhausts its budget or meets a provider's spend limit is a result with an end reason, not an exception; for the caller it is a stall. `AgentRuntimeError` is for a runtime that cannot be used at all. See `docs/decisions.md`.

### The `claude -p` runtime

`ClaudeCodeRuntime(executable, state_directory, kill_points=None, *, version_time_limit=VERSION_TIME_LIMIT, sudo_executable=SUDO_EXECUTABLE, login_file=None, confine_executable=None, temporary_root=None, api_login_file=None, provider_limit=None, leftovers=None, containers=None)` (`factory.adapters.claude_runtime`) runs an agent as a `claude -p` call, under the login of `request.os_user` when it is set and under the factory process's own login when not; a call stopped by its budget is resumed once (below).

With `login_file` or `api_login_file` set, every call (not `version()`) starts through a login shell whose words come from `login_argv(LoginFiles(subscription=login_file, api=api_login_file))` (`factory.adapters.agent_launch`, below), followed by `<executable> <arguments>`, after `env -i` and its assignments when there is an `os_user`. With neither file there are no words. The request's own `CLAUDE_CODE_OAUTH_TOKEN` and `ANTHROPIC_API_KEY` entries are dropped (`without_login`): the files are the only source. The factory never reads either file. A refusal in standard error (`login_refusal`) raises `AgentRuntimeError("cannot read the agent's login file <path>: <reason>")`, or `"cannot read the agent's API login file <path>: <reason>"` for the API file, unless the reply parses. The result's `login` is `login_used(stderr)` of the run's last call. The file is read again at every call, so a changed file applies to the next call of the same runtime. The module re-exports `LOGIN_SCRIPT`, `LOGIN_VARIABLE`, `LOGIN_PREFIX` and `SHELL_EXECUTABLE` in its `__all__`, and keeps reading `SHELL_EXECUTABLE` from its own namespace when it removes the temporary folder. It starts the process through `run_process`, and with `git_cli` and `make_commands` it is one of the modules that import `factory.adapters.process` (`git_cli`, `make_commands` and `opencode_runtime` are the others; `tests/test_wrapper_search.py`).

### Calls in a container

Both runtimes take `containers: ContainerRuns | None = None`, readable as the `containers` property. Built with `containers` and a `confine_executable`, the constructor raises `ValueError`: the kernel's guard does not reach into a container. This is step 5 of the cycle (*The agent's container* in `stage-environment.md`); the wiring that gives a `container` instance's runtimes their `PodmanRuns` is not part of the runtimes.

- `run(request)` with an `os_user` raises `AgentRuntimeError("a run in a container has no operating-system user")` (`CONTAINER_OS_USER`) before any file is written or call made.
- The run's files are written as without a confine executable: the instructions file (Claude Code) or the configuration file (opencode) in the state directory, no rules file. Each call's `ProcessRequest` comes from `container_launch` instead of `run_launch`, the choice made in the runtime's `_process_request`. Its words are the same as on the host (the login shell words, then the runtime's), without `sudo`, `timeout`, `env -i` and `factory-confine`. The files it mounts are `[*login_paths(files), <the call's file>]`, read-only at their own paths, so the words do not change. The environment is `run_environment(...)`: for Claude Code the three switches and no `CLAUDE_CONFIG_DIR`, for opencode `OPENCODE_CONFIG` (the configuration file's path) and its switches. The working directory in the container is `/work/checkout` and `HOME` is whatever the request's environment says (`/work/home` in a stage); the request's `working_directory` is the `cwd` of podman on the host.
- No leftovers program runs and no temporary folder is made or removed: both belong to the layers the container replaces. The login files are mounted, so the login shell reads them as ever and `factory-login-used:` is read as ever.
- A call that ends with exit status 137, -9 or 255 (podman's `--timeout` status) at or after its time limit is read as `time_limit` (`in_container=True`), is not resumed and has its measures unknown; before the limit it is `died`. A budget stop of Claude Code is resumed as on the host, in a second container with the same mounts.
- `version()` runs `version_launch(executable, containers=..., time_limit=version_time_limit)` in a container too, with no mounts and an empty environment, so the preflight's `agent-runtime-version` reads the stage image's runtime.

### The shared launch module

`factory.adapters.agent_launch` holds what every agent runtime shares to start a call; the opencode runtime reuses it. It imports no `factory.adapters.process` and reads no `os.environ`: it builds words, rules and texts, and each runtime starts its own processes. It holds the login shell (below) and the start of a run: the words, the rules, the removal of the run's folder, the refusals and the resume share. `ClaudeCodeRuntime` calls these functions; it keeps its own process calls, the reply's parsing and `_since`. The names a test sets on `claude_runtime` (`SHELL_EXECUTABLE`, `CLEANUP_TIME_LIMIT`, `DEVICE_FOLDERS`, `DEVICE_FILES`, `run_process`) are read from that module's namespace at the call and passed in, and the moved constants (`ENTRY_DESCRIPTION`, `FINISH_MESSAGE`, `VERSION_TIME_LIMIT`, `SUDO_EXECUTABLE`, `CLEANUP_TIME_LIMIT`, `CLEANUP_SCRIPT`, `resume_budget`) stay names of `claude_runtime` through its `__all__`.

The make class (`MakeProjectCommands` with a `CommandUser`, `processes-and-checks.md`, *Running as another user*) also starts its commands through `launch`, and judges the kill with `killed_at_limit`, `SUDO_PREFIX`, `leftovers_launch` and `leftovers_fault`; it copies none of them.

- `launch(argv, environment, *, os_user, sudo_executable, time_limit)` gives a frozen `Launch(argv, env, time_limit)`; `env` is `None` for the process's own environment (what `PodmanRuns.launch` gives and `version_launch` uses without containers), a dict otherwise. Without `os_user` it keeps all three as given. With one, `argv` is `sudo_prefix(...)` (`[sudo, -n, -u, <user>, --]`), `timeout --signal=KILL <seconds>s` (the limit rounded up), `env -i`, one `NAME=value` per entry in the environment's order, then the command; `env` is empty and the limit is the given one plus `SUDO_GRACE` (30 s). `confined_argv(argv, confine_executable, rules)` puts `[confine_executable, --rules, <rules file>, --]` before the command, or leaves it unchanged without a wrapper.
- `temporary_folder(root, run)` is `root / "factory-run-<run>"`. `cleanup_argv(shell, temporary, *, os_user, sudo_executable)` is `[shell, -c, CLEANUP_SCRIPT, factory-cleanup, <folder>]`, after `sudo_prefix` with a user.
- `run_confinement(request, temporary, *, runtime_folders, devices)` builds the run's `Confinement`. `runtime_folders` are relative to the request's `HOME` (`[".claude"]` for Claude Code), each becoming a folder target `<HOME>/<folder>` in the order given and none without a `HOME`; a request without guard settings may write nothing of the checkout. `existing_devices(folders, files)` gives the folder targets, then the file targets of those that exist. `request_home(request)` is the request's `HOME` or `None`.
- `line_starting(stderr, prefix)` is the first line that starts with the prefix (`SUDO_PREFIX` `sudo:`, `CONFINE_PREFIX` `factory-confine:`, the login prefixes). `killed_at_limit(*, os_user, exit_status, duration, time_limit, in_container=False)` is true only with a user or `in_container`, a status in `KILL_STATUSES` (137, -9) and a duration at or above the limit; with `in_container` the statuses are `CONTAINER_KILL_STATUSES` (those two and 255, `PODMAN_TIMEOUT_STATUS`), whether or not there is a user, so podman's `--timeout` kill is read the way the agent's own `timeout` under `sudo` is read. `first_word(output)` is the first word of the first non-blank line (the version).
- `Starters.leftovers` is the words that start the program that ends the agent's leftover processes, without `--user`, or `None` (the default: the runtime starts none). `leftovers_due(starters, os_user, own_user)` is true exactly when `leftovers` is not `None`, `os_user` is not `None` and `os_user` differs from `own_user`. `leftovers_launch(leftovers, *, os_user, sudo_executable)` gives `Launch(argv=[*sudo_prefix(...), *leftovers, "--user", os_user], env={}, time_limit=LEFTOVERS_TIME_LIMIT)` (30 s). `leftovers_fault(*, exit_status, timed_out, stderr)` is `None` for status 0 without a time-out, `cannot end the agent's processes: no end within 30 s` when timed out (whatever the status), else `cannot end the agent's processes: <line>` with the first `factory-leftovers:` line of `stderr` whole (`LEFTOVERS_PREFIX`; a `sudo:` line is never that line) or `exit status <n>`. It takes three values and not a `ProcessResult` because the module imports no `process`. `due_leftovers_launch` joins `leftovers_due` and `leftovers_launch` for both runtimes (`None` when not due).
- `read_call_end(end, *, time_limit, os_user, starters, in_container=False)` reads the end of a call for both runtimes and gives whether it ended at its time limit. `end` is a frozen `CallEnd(stderr, printed, exit_status, duration, timed_out)`, the process's fields and not a `ProcessResult` (the module imports no `process`). The kill is read first: the call is timed out when `end.timed_out` is set (the runtime's own `timeout`) or `killed_at_limit(...)` is true. The refusals of `sudo`, the write guard's wrapper and the login shell (`call_refusal`) are read with that value, so a call that printed a reply and was killed is still read for refusals; a refusal raises `AgentRuntimeError` with the refusal as its detail. `state_directory_error(state_directory, error)` returns (does not raise) `AgentRuntimeError("cannot write the state directory <dir>: <error>")`; both runtimes use it. Each runtime keeps its own process calls (`_start`, `_request_of`, the removal of the temporary folder, `version`), because the module imports no process module.
- `container_launch(containers, argv, environment, *, files, time_limit)` is `containers.launch(argv, mounts=..., environment=environment, time_limit=time_limit, working_directory=WORK_CHECKOUT)` as a `Launch`: one read-only `Mount` per file, at the file's own path, each file once in the order first given. It raises what `launch` raises (`ValueError` for a file under `/work`, with no call recorded). `run_environment(request, runtime_environment)` is the call's environment for both ways: the request's without logins, with the runtime's switches. `login_paths(files)` lists the login files that are set, the subscription file first. `version_launch(executable, *, containers, time_limit)` is `<executable> --version`: `Launch(env=None)` without containers, `container_launch(..., {}, files=[])` with them.
- `resume_budget(budget)` is a quarter of the budget, at least `MINIMUM_RESUME_BUDGET` (0.50), rounded half up to cents; `FINISH_MESSAGE` is the resumed call's prompt.
- `resumed_result(first, second)` is in the domain (`factory.domain.agent_runs`): the sum of a resumed run, by the rules under "Measures of a resumed run" below. It takes `second`'s end reason, decision, entry and login, joins the refused calls (first call's first, `path` unchanged) and adds the durations; the run sets the whole run's clock afterwards.

- `LOGIN_SCRIPT` is built from the module's constants only (an f-string, so its source holds no `NAME="..."` pair of a secret's name), and runs as the user the call runs as. With `--api-login <file>` and a file that holds a key (anything left once spaces, tabs, carriage returns and line feeds are removed) it exports `ANTHROPIC_API_KEY`, unsets `CLAUDE_CODE_OAUTH_TOKEN`, prints `factory-login-used: api_key` on standard error and `exec`s the command; the token file is not read. Otherwise it unsets `ANTHROPIC_API_KEY`, reads the token file as before (a missing or empty file, or an empty argument, is no token) and prints `factory-login-used: subscription` or `factory-login-used: none`. A file that exists but is not a readable regular file, or holds a byte other than printable ASCII, space, tab, carriage return or line feed, prints `factory-api-login: <reason>` (API file) or `factory-login: <reason>` (token file), with the reason `cannot be read` or `not ASCII text`, and exits 1 without starting the command.
- `LoginFiles(subscription=None, api=None)` is the frozen pair of files. `login_argv(files)` is `[]` for neither, `[/bin/sh, -c, LOGIN_SCRIPT, factory-login, <subscription>]` for the token only, and `[..., factory-login, --api-login, <api>, <subscription or "">]` with an API file.
- `login_used(stderr)` reads the first `factory-login-used:` line (`None` for none or an unknown word). `login_refusal(stderr, files)` gives the API text first, then the token text, else `None`. `without_login(environment)` is the copy without both names.
- Names that contain `key`, `token`, `secret` or `password` are never assigned a string literal (ruff's `S105`, `make secrets`); tests hold a stand-in key in a name such as `API_LOGIN` and write an environment entry with the name's constant.

The arguments, in this order (`<session>` is a new `uuid4` per run):

```text
-p <prompt>  --model <model>  [--effort <effort>]  --tools <tools joined with commas>
--session-id <session>  --append-system-prompt-file <state_directory>/instructions-<session>.md
--permission-mode auto  --permission-prompts none
--strict-mcp-config  --max-budget-usd <budget as plain decimal>  --output-format json  --json-schema <schema>
```

`--effort` is left out when the agent has none; `--tools` is always there, with an empty value for an empty list. The flags are v1's; the preflight's `agent-run-probe` makes one call with them, so a flag the pinned `claude` rejects stops the machine. The schema asks for an object with `decision` (an enum of `allowed_decisions`, in the request's order) and `entry` (described by `ENTRY_DESCRIPTION`), both required, nothing else.

Files under `state_directory` (created with its parents when missing), written before the call and removed when the run ends, whether by a result, `InjectedKill` or `AgentRuntimeError`:

- `instructions-<session>.md`: the agent's instructions.
- With `confine_executable` only: `confine-<session>.json`, the kernel's rules (see *Confinement* below).

Environment: the call gets `request.environment` plus `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` and `PYTHONDONTWRITEBYTECODE=1`. Nothing is inherited from the factory's process and no `PATH` is added. The call runs in `request.working_directory`.

Confinement. With `confine_executable` set (the property of that name; `None` leaves the command line, the environment and the files exactly as described above), every call, a first one and a resumed one, starts as `[confine_executable, "--rules", <state_directory>/confine-<session>.json, "--", *<the call's command>]`, where the command is the login shell, when there is one, and `claude` with their arguments. With an `os_user` that list follows `env -i` and its assignments, after `sudo -n -u <user> -- timeout --signal=KILL <limit>s`. `build_boundaries(..., confine_executable=CONFINE_COMMAND)` passes `factory-confine`; `factory.entry.run` and `boundaries_from_environment` pass nothing, so every run of the factory is confined (a test pins the default and the source of `run`).

- The rules file is the `Confinement` as `model_dump_json()`, mode `0o640` (`RUN_FILE_MODE`), written with the run's other files and removed with them. `run_confinement` (`factory.adapters.agent_launch`) builds it with `confinement_of(write_targets(guard, home=home), root=guard.root, existing_files=..., extras=..., temporary_directory=...)`: `guard` is the request's, or `GuardSettings(root=working_directory, write_paths=[], protected_paths=[])` when it has none (so a run without a guard is confined with no path of the checkout); `home` is `HOME` of the request's environment or `None`; `existing_files` are the file targets that are files; `extras` are `<home>/.claude` (`RUNTIME_FOLDER`, passed as `runtime_folders=[RUNTIME_FOLDER]`; only with a `HOME`), then each of `DEVICE_FOLDERS` and then each of `DEVICE_FILES` (`factory.domain.confinement`) that exists. `DEVICE_FILES` is `/dev/null`, `/dev/zero`, `/dev/full`, `/dev/random`, `/dev/urandom` and `/dev/tty`; `DEVICE_FOLDERS` is `/dev/shm`, whose line carries the one `noqa: S108` and `nosec B108` that `CLAUDE.md` allows in the domain.
- The temporary folder is `temporary_root / f"{TEMPORARY_PREFIX}{session}"` (`TEMPORARY_PREFIX` is `factory-run-`; `temporary_root` `None` is `Path(tempfile.gettempdir())`), the same path for a first call and its resume. The wrapper makes it and sets `TMPDIR`; the runtime sets nothing for it.
- With a `HOME` in the request's environment the call's environment gains `CLAUDE_CONFIG_DIR` (`CONFIG_VARIABLE`) `=<HOME>/.claude`, so that Claude Code keeps `.claude.json` inside the one folder the rules allow. Without `HOME` the variable is not set, and the rules hold no `.claude` folder and no folder of a `~/` tool path.
- After every call the runtime runs `[SHELL_EXECUTABLE, "-c", CLEANUP_SCRIPT, "factory-cleanup", <temporary folder>]` through `run_process` (limit `CLEANUP_TIME_LIMIT`, 60 s), prefixed by `sudo -n -u <user> --` with an `os_user`, in the request's working directory and with an empty environment. `CLEANUP_SCRIPT` is `chmod -R u+rwX -- "$1" 2>/dev/null; rm -rf -- "$1"`: the folder is `$1`, never part of the script, and `chmod` first lets it remove a folder the agent closed. Status and output are not read, so a failed removal changes no result; an `OSError` starting it is `AgentRuntimeError`. It runs also after a kill at the time limit or an error.
- Refusal. A call that ends without a usable reply (none that parses, or one cut short by the time limit) and whose standard error holds a line starting `CONFINE_PREFIX` (`factory-confine:`) raises `AgentRuntimeError("<confine_executable> refused the agent run: <line>")`; such a line before a usable reply is ignored. The `sudo:` check comes first.

A call as another user (`request.os_user` set). The argument vector is `<sudo_executable> -n -u <os_user> -- timeout --signal=KILL <seconds>s env -i NAME=value ... <executable> <arguments>` (`TIMEOUT_EXECUTABLE`; `<seconds>` is the call's time limit rounded up to whole seconds), one assignment per name of the environment above, and the process itself starts with an empty environment: `env -i` drops whatever `sudo` keeps, so the agent sees the request's environment alone. `sudo_executable` defaults to `SUDO_EXECUTABLE` (`/usr/bin/sudo`) and is readable as the property `ClaudeCodeRuntime.sudo_executable`; `build_boundaries` gives the runtime the `sudo` on the `PATH` that the preflight's `tool:sudo` item finds (`which("sudo")`, its `which` parameter defaulting to `shutil.which`), and `/usr/bin/sudo` only when there is none, in which case the preflight stops the machine anyway. The instructions and rules files are written with `RUN_FILE_MODE` (`0o640`) for every request, so the other user can read them through the group. The factory may not signal `sudo`, so the agent's own `timeout` kills at the limit, and the outer `ProcessRequest` gets the limit plus `SUDO_GRACE` (30 s), so the factory's own kill fires only when the inner one did not. A call with an `os_user` that ends with status 137 or -9 after a duration of at least its limit (`KILL_STATUSES`) is marked `timed_out` (`killed_at_limit`), so it ends `time_limit` without measures; the same status earlier is `died`. The resume goes through the same call with what is left of the limit. When the call reached its `time_limit` or printed no reply that parses, a standard-error line starting with `sudo:` raises `AgentRuntimeError` (`<sudo_executable> refused the agent run: <line>`): a refused `sudo` is a misconfiguration, not a stall. A reply that parses, from a call within its `time_limit`, is a reply even when a `sudo:` warning came with it. `agent_run_environment(settings, base)` in `factory.entry.wiring` sets `HOME` to the parent of `settings.agent_home` when `settings.agent_user` is set, since the agent home is the `.claude` folder in the agent user's home.

End reason, first rule that applies: `time_limit` when the time limit ended the call (it is killed with its children); `died` when the exit status is not 0, the output is not a JSON object with a string `subtype` and a boolean `is_error`, or `is_error` is true; `completed` when `structured_output` has a `decision` from `allowed_decisions` and a non-blank `entry`; otherwise `no_result`. A reply that is an error whose `result` holds the provider limit, or, when no reply parses, a line of standard error that holds it, is `provider_limit` (below). A reply with `subtype` `error_max_budget_usd` is `budget`, checked right after `time_limit` and before the exit status, because `claude` may exit non-zero on a budget stop. The rules above describe one call; the resume below applies them to each call.

Measures: `duration` is what the factory measured around the call. `model_duration` is the reply's `duration_api_ms`, the time the model took (the JSON's `duration_ms` is ignored); it is `None` when the reply lacks the field and after a `time_limit`, and a negative value makes the reply unparsable (`died`). `turns`, `cost_usd` (`Decimal(str(total_cost_usd))`), `tokens` and `permission_denials` come from the JSON when it parses, and are `None` for any field it lacks, and for all of them after a `time_limit`. For a resumed run they are added up (below). `tokens` is known only when both `input_tokens` and `output_tokens` are present; the cache counts default to 0. A denial's `detail` is its `tool_input` as JSON with sorted keys; its `path` is the `tool_input`'s `file_path` when that is a string, or else its `notebook_path` when that is a string, otherwise `None` (also when `tool_input` is not an object). A reply with the wrong type in a field it carries does not parse and counts as `died`. So does a reply with a negative `num_turns`, token count or `total_cost_usd`: it counts as `died` and every measure is unknown (`None`); zero is valid. This holds for a budget-stop reply too, which is then not resumed.

Kill point: `KillPoint.AGENT_RUN` is reached once, after the last call and the result, whatever the end reason, and not when the call could not be started. A missing executable or an unwritable state directory raises `AgentRuntimeError` naming the cause.

The provider limit. `ClaudeCodeRuntime(..., provider_limit=None)` takes a `ProviderLimit` (`factory.domain.provider_limits`: `status` 100 to 599, default `DEFAULT_LIMIT_STATUS` 428, and `message`, a regular expression that must compile); `None` is the default limit, and `build_boundaries` passes `settings.provider_limit`, read from `FACTORY_PROVIDER_LIMIT_STATUS` and `FACTORY_PROVIDER_LIMIT_MESSAGE` (`SettingsInvalid` names the variable). `limit_in_text(text, limit)` is true when the status stands in the text as a whole number or `message` searches it (`re.search`); `named_wait(text)` is the earliest wait the text names (`in|after <n> <unit>`, unit `s`/`sec`/`second(s)`, `m`/`min`/`minute(s)`, `h`/`hour(s)` or none for seconds, or `retry-after[:] <n>` seconds, `<n>` of one to six digits), `None` for none or zero. A call ends `provider_limit` only when it did not reach its time limit and was not stopped by its budget, and the limit is in the error reply's `result` (never in `structured_output`) or, with no parsable reply, in a line of standard error. The result keeps the reply's measures, as a `died` one does, and its `limit_wait` is `named_wait` of that text. A budget-stop resume that ends `provider_limit` makes the run `provider_limit` with both calls' measures. `StallReason` has `provider_limit` too; its sentence is `the provider's spend limit lasted past the waiting ceiling`, and until the application layer waits the limit out (a later story) it is a stall like `died`. The cost recorder treats the end reason as a run that replied: `denials` and `denied_paths` are set.

Resuming a session. Every result's `session` is the id of `--session-id` or, for a request with `resume_session`, that id. Such a request is called with `--resume <resume_session>` in place of `--session-id <new id>`, with the request's prompt and the agent's budget; the run's files are named by a fresh id. A budget stop of that call resumes the same session once, as below. `resumed_result` takes the second call's `session` (the first's when the second has none) and `limit_wait`.

The budget resume. When a call ends with `budget`, the same session is resumed once, so that an agent that ran out of money still gives its decision and entry. The arguments are the first call's, except `-p` is `FINISH_MESSAGE`, `--session-id <session>` becomes `--resume <session>`, and `--max-budget-usd` is `resume_budget(agent.budget_usd)`: a quarter of the budget, at least `MINIMUM_RESUME_BUDGET` (0.50), rounded half up to cents. The run's files are the same ones and are removed when the run ends. The resumed call's reply is read by the rules above; if it also ends with `budget`, so does the run. A third call is never made. `FINISH_MESSAGE` asks for `question` where v1 asked for `stuck`.

One `time_limit` counts across the run: the first call may take `request.time_limit`, the resume what is left of it, measured by the factory from the start of `run`. A first call ended by the time limit is never resumed. If nothing is left when the first call ends, the resume is skipped and the run ends as `time_limit`.

Measures of a resumed run: `turns`, `cost_usd` and each of the four token counts are the sums over both calls; a call that reported none adds nothing, and a measure is `None` only when neither call reported it. When the resumed call is ended by the time limit, `turns`, `cost_usd` and `tokens` are all `None` (no partial figure: the first call's alone would be one). Permission denials are joined, the first call's first. `duration` is the factory's own, from the start of `run` to the end of the last call. `model_duration` is the sum of both calls' when both are known, the known one when only one is, `None` when neither; a resume ended by the time limit keeps the second call's `None`.

`version()` runs `<executable> --version` through `run_process` in the process's current directory, with its current environment and the limit `version_time_limit` (`VERSION_TIME_LIMIT`, 30 seconds). It returns the first word of the first non-blank line, so `2.1.289 (Claude Code)` gives `2.1.289`. It raises `AgentRuntimeError` when the call cannot be started, exits non-zero, reaches the limit or prints nothing.

Tests use a stand-in executable (`tests/adapters/claude_stand_in.py`: `write_stand_in(directory, steps)` and `read_calls(directory)`) written into `tmp_path`; the real `claude` is never run.

### The fresh home

`python -I -m factory.entry.fresh_home --home <folder> [--keep <path>]...` clears an agent's home of what the agent made. The home keeps everything every run left there: the transcripts of earlier runs, opencode's sessions, caches, and any file Claude Code reads on every later run (a user `CLAUDE.md`, a `rules/` folder). The program runs as the user whose files it removes and decides by ownership. It is built in three layers: the rule in `factory.domain.agent_home`, the walk in `factory.adapters.home_files` (`clear_home`, `own_entry`) and the command line in `factory.entry.fresh_home`. The program itself starts nothing and has no default home, so no call can clear a home it was not named; `SudoAgentHome` starts it (below).

**Arguments and status.** Exactly `--home <folder>` followed by any number of `--keep <path>`; each `--keep` is relative to the home.

| Status | When | Standard error |
| --- | --- | --- |
| 0 | the walk is done | nothing |
| 1 | the walk is done and some entry could not be removed | one line `factory-fresh-home: <relative>: <reason>` per fault |
| 2 | the arguments are refused; nothing is removed | the usage line `factory-fresh-home: usage: fresh_home --home <folder> [--keep <path>]...`, or `--home <folder> is not an absolute folder other than /` (relative, resolving to `/`, or not an existing folder), or `--keep <path> is not a path inside the home` |

**The rule.** `inside_home(relative)` is false for `""`, an absolute path and any path with an empty, `.` or `..` segment; `factory.domain.settings` uses it for `FACTORY_OPENCODE_FOLDERS` too. `kept_paths(...)` builds the list of kept paths, relative to the home: the login files that lie inside it, then the state files, then the folders, without repeats; a state file or folder that is not `inside_home` raises `ValueError`. For each entry of a folder, in name order, `fate(relative, owned=, folder=, kept=)` says:

- `keep` when the entry is a kept path or lies beneath one;
- otherwise `descend` when it is a real folder (a link to a folder is not one), also when a kept path lies beneath it;
- otherwise `remove` when it belongs to the program's user, and `keep` when it belongs to another user (the factory's agents, `settings.json`, `skills/`, `commands/`, the mounted login files).

After the walk of a folder, `removed_when_empty` decides whether the folder is removed: only when the user owns it and no kept path lies beneath it. A folder with a kept path or another user's entry in it stays.

**The walk.** `clear_home` never follows a link: a link is judged and removed as itself, and what it points to stays. An owned folder gets the owner's read, write and search bits before it is walked, so a folder the agent closed to itself is still cleared. The mode of an entry that is not the user's is never changed. The home itself is never removed. An `OSError` at an entry is recorded as `<relative>: <strerror>` and the walk goes on; the faults come back in the order met. `own_entry` compares the owner of the entry itself (`lstat`) with the process's effective user.

**Who starts it, and when.** `AgentHome` (`factory.application.agent_home`, an abstract base class) has one operation, `reset()`, which raises `AgentRuntimeError` when the home cannot be cleared. `SudoAgentHome(home, kept, *, os_user, sudo_executable, program)` (`factory.adapters.agent_home`) is its implementation. `reset` builds the call with `launch([*program, "--home", <home>, "--keep", <path>, ...], {}, os_user=..., sudo_executable=..., time_limit=FRESH_HOME_TIME_LIMIT)`, so it is `sudo -n -u <agent> -- timeout --signal=KILL 60s env -i <python> -I -B -m factory.entry.fresh_home --home /home/agent --keep ...`, with an empty environment, and starts it with `run_process` from `/`, with the time limit plus `SUDO_GRACE`. `-B` is there because `-I` ignores `PYTHONDONTWRITEBYTECODE`, and bytecode the agent's user wrote beside the factory's source is a file the checkout's restore cannot remove. `FRESH_HOME_TIME_LIMIT` (60 seconds) is read at each call.

- `run_sealed` calls `boundaries.agent_home.reset()` after `git.seal()` and before the run, once per stage run: a resume after a provider limit or the budget happens inside the one `run`, so it keeps its session. The preflight's probe goes through `run_sealed` and is reset too. A reset that raises propagates before the run; nothing ran, so the seal is not checked.
- `SealedProjectCommands` resets the home after the seal and before each command (`processes-and-checks.md`, *Sealed project commands*).
- Without `settings.agent_user` there is no `AgentHome` (`Boundaries.agent_home` is `None`) and nothing is reset.

**Faults of `reset`.** All are `AgentRuntimeError("cannot reset the agent's home <home>: <reason>")`. A call that reached its limit (the factory's kill, or `killed_at_limit` for the exit status and duration) has the reason `no end within <seconds> s` (60 by default). Any other non-zero status has the first standard-error line that starts with `FRESH_HOME_PREFIX`, else the last non-blank line, else `exit status <n>`. A program that cannot be started (`OSError`) has its `strerror`.

**What is kept.** `agent_home_of(settings, sudo_executable)` (`factory.entry.wiring`) builds the `SudoAgentHome`, or `None` without an agent user. Its `home` is `settings.agent_home.parent` and its `kept` is `kept_paths(...)` over the login files (`FACTORY_CLAUDE_LOGIN_FILE`, `FACTORY_API_LOGIN_FILE`; one outside the home drops out), the state files `claude_runtime.LOGIN_STATE_FILE` (`.claude/.credentials.json`) and `opencode_runtime.LOGIN_STATE_FILE` (`.local/share/opencode/auth.json`), and the folders `UV_CACHE_FOLDER` (`.cache/uv`) and `FACTORY_OPENCODE_FOLDERS`, whichever runtime the instance uses. The kept uv cache is the one thing a run leaves that a later run or check reads (the feature's decision 9: accepted). `fresh_home_command()` is `[sys.executable, "-I", "-B", "-m", FRESH_HOME_MODULE]`.

Tests: `tests/adapters/test_sudo_agent_home.py` (a stand-in `sudo`), `tests/application/test_agent_home_resets.py`, `tests/entry/test_wiring_agent_home.py`; no test resets a real home. `tests/domain/test_agent_home.py`, `tests/adapters/test_home_files.py`, `tests/entry/test_fresh_home.py`. Every home is a folder under `tmp_path`; the tests cannot `chown`, so an entry of another user is an `owned` that answers false. No test runs the program on a real home. `factory.entry.fresh_home` imports its adapter directly, as `factory.entry.confine` and `factory.entry.leftovers` do, and is in the expected set of `tests/entry/test_wiring.py`.

### The opencode runtime

`OpencodeRuntime(executable, state_directory, kill_points=None, *, models=None, settings_file=None, version_time_limit=VERSION_TIME_LIMIT, sudo_executable=SUDO_EXECUTABLE, api_login_file=None, confine_executable=None, temporary_root=None, provider_limit=None, runtime_folders=RUNTIME_FOLDERS, leftovers=None, containers=None)` (`factory.adapters.opencode_runtime`) runs an agent as one `opencode run` call and reads the run's result from the JSON events the call prints. `_agent_runtime` in `factory.entry.wiring`, called by `build_boundaries`, builds it when `settings.agent_runtime` is `opencode` (`FACTORY_AGENT_RUNTIME`; otherwise it builds the Claude Code runtime): with `settings.opencode_executable`, `<state>/runs`, `models=settings.opencode_models`, `settings_file=agent_home / "settings.json"`, `api_login_file`, `provider_limit` and `runtime_folders=(*RUNTIME_FOLDERS, *settings.opencode_folders)`. The budget stop, the provider limit and the resume while the run streams are built in the runtime itself. Its keyword `provider_limit` (last; `None` is `ProviderLimit()`, status 428 and no message) is the limit it recognizes. It reads no `os.environ`; its starts go through `run_process` and `run_streaming`, whose callback (`_Watch`) reads each line as it arrives and may stop the call.

**The call.** The words are, in order, the login words of `login_argv` (an API login file only; there is no subscription file), `<executable> run --format json --auto --model <model> --agent factory-<name> <prompt>`, the prompt one argument, in the request's working directory. `<model>` is the agent's `model` as it is when it holds a `/`, otherwise `models[alias]`; an alias without a mapping raises `AgentRuntimeError`. With an `os_user` and with `confine_executable`, `sudo`, `timeout`, `env -i` and `factory-confine` wrap the call exactly as for `claude -p`, through the helpers of `factory.adapters.agent_launch`. The call's environment is the request's, without `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` (the login file is the only source), plus `OPENCODE_CONFIG` and `PYTHONDONTWRITEBYTECODE=1`. `version()` runs `<executable> --version` without login words and returns the first word of the first non-blank line (`1.19.3`), with the errors of the Claude Code runtime.

**The per-run configuration.** opencode has no flag for an agent's prompt, tools or permissions, so the runtime writes `opencode-<run>.json` into `state_directory` (mode `0640`) and names it in `OPENCODE_CONFIG`. The file defines one primary agent, `factory-<name>`, from the same `AgentDefinition` the Claude Code runtime gets from `claude/agents/*.md`:

- `prompt`: the agent file's body, a blank line and `result_instructions(allowed_decisions)`;
- `tools`: all twelve of `OPENCODE_TOOLS`, true for the agent file's tools translated through `TOOL_NAMES` (`Read` is `read`, `Bash` is `bash`, and so on) and false for the rest; a tool in `LEFT_OUT_TOOLS` (`Skill`) turns on no opencode tool and is not refused, so only Claude Code's runs load skills; every other tool outside `TOOL_NAMES` raises `AgentRuntimeError`;
- `permission`: `edit` allowed and `bash` `{"*": "allow"}` plus a `"deny"` for the pattern of each `Bash(<pattern>)` entry in `permissions.deny` of `settings_file` (the installed `settings.json`). Entries for other tools are not translated. A settings file that cannot be read, or holds no `permissions.deny` list of strings (also when it is no JSON), raises `AgentRuntimeError`; with no `settings_file` only `{"*": "allow"}` is written;
- `autoupdate` false, `share` `disabled` and `snapshot` false, so a run neither updates itself nor uploads or snapshots anything.

The model, tools and settings are checked before any file is written; the state directory must exist (the runtime does not create it; the Claude Code runtime does). The difference is deliberate: the image creates `/state/runs`. The configuration and the `confine-<run>.json` rules are removed after the run, whatever its end. Why the agent is generated and not shipped: see *opencode's agent is generated per run from the shipped agent files* in `docs/decisions.md`.

**The result block.** opencode has no structured-output flag, so the prompt ends with a fixed block the agent must end its final message with:

```
<factory-result>
decision: <one of: doing, question>
entry:
<the entry>
</factory-result>
```

`parse_result_block(text, allowed_decisions)` reads it strictly from the last `text` event: the text must end with `</factory-result>` (trailing spaces and line feeds are ignored; text after it is not), the last `<factory-result>` before it opens the block, the first line is `decision:` and a word in `allowed_decisions` (spaces around it are fine), the second is `entry:`, and the lines after it, joined with line feeds and stripped (line breaks inside the entry stay), are the entry and must not be blank. The second line is exactly `entry:`: `entry: text` there gives `None`. Anything else gives `None`, and the run is `no_result`. There is no repair and no fuzzy match: a reply the factory cannot trust is not a decision.

**The events.** With `--format json` each stdout line is one event; a line that is no JSON, has no known `type` (`step_start`, `tool_use`, `text`, `step_finish`, `error`), or has a negative number where a count, cost or timestamp belongs, is skipped, and so is a `step_finish` without `cost` or `tokens`. The measures come from the valid lines alone:

- `cost_usd`, `turns` and `tokens` are summed over the `step_finish` events: `input`, `output` (plus `reasoning`), `cache.read` and `cache.write` (a missing part counts 0). Cost is added as `Decimal(str(cost))`.
- `model_duration` is, for each step, `step_finish` timestamp minus the earlier `step_start` timestamp, minus the spans of the `tool_use` events between them by line order, never below 0; a finish with no earlier start adds 0 and still counts as a turn.
- A `tool_use` whose state is an error that mentions `permission` or `denied`, in any case, is a `PermissionDenial` (tool, sorted input as JSON, and `path` from the input's `filePath` when it is a string).

**The session.** Every result's `session` is the `sessionID` of the first event that carries one, else the request's `resume_session`, else `None`, whatever the end reason, a timeout included. A request with `resume_session` is called with `--session <resume_session>` right before the prompt. A resume (the budget resume below, or a request's `resume_session`) is called the same way.

**The end reason.** A timeout is `time_limit` with no measures. Under an `os_user`, a call that ends with a status in `KILL_STATUSES` after a duration of at least its limit is `time_limit` too, with the `session` of its events and the `login` the shell reported; the same kill status before the limit, or any other status after it, is `died`. A call the callback stopped is `budget` or `provider_limit` (above). Otherwise a non-zero exit or no `step_finish` is `died`; a valid block is `completed` (with its decision and entry); anything else is `no_result`. A stderr line from `sudo` or `factory-confine` is a refusal only when no valid event was printed.

**The budget.** opencode has no budget flag, so the callback keeps it. It adds up the `cost` of each `step_finish` of the call (as `Decimal`) while the call streams and stops the call as soon as the sum is greater than the call's budget: the agent's `budget_usd` for the first call, `resume_budget(budget_usd)` for a resume. A sum equal to the budget does not stop it. The call ends `budget` with the measures of the events read. A step is only counted when it finishes, so a run may pass its budget by the cost of one step.

**The budget resume.** A first call that ends `budget` with a known session is resumed once: the same words with `--session <session>` before the prompt, `FINISH_MESSAGE` as the prompt, `resume_budget(budget_usd)` as the budget, within what is left of the request's time limit (a resume past it ends the run `time_limit`). The run's configuration and rules files are the first call's and are removed only after the resume. The result is `resumed_result` of the two calls: a resume that is also over its budget ends the run `budget`, with no third call, and one stopped by a limit ends it `provider_limit`. With no known session (no event carried a `sessionID`) the budget stop is the run's result. The kill point `AGENT_RUN` is reached once, after the whole run.

**The provider limit.** The callback stops the call at once, as `provider_limit`, on an `error` event whose `error.data.statusCode` is the limit's status or whose `error.data.message` holds the limit (`limit_in_text`), and on a line of standard error that holds it. It reads no limit from a `text` or `tool_use` event or from any other field, so an agent that writes "428", or a tool whose output holds it, stops nothing. An `error` event that is no limit does not stop the call; the call ends by the rules below. The result keeps the measures of the events read, the session, and a `limit_wait` of `named_wait` of the message or line (`None` when it names none). A limit is never resumed here: waiting it out and continuing the session is the application layer's (S0007). A time limit that ended the call wins over a recorded stop.

**opencode's folders.** opencode writes its sessions, logs and caches to `.local/share/opencode`, `.local/state/opencode` and `.cache/opencode` in the agent's home (`RUNTIME_FOLDERS`); the run's rules allow those three, with the run's temporary folder and the write paths. `runtime_folders` (last keyword, default `RUNTIME_FOLDERS`) replaces that list: each folder is allowed as `<HOME>/<folder>`, in order, and `build_boundaries` passes the three followed by `FACTORY_OPENCODE_FOLDERS` (relative to `/home/agent`), for an operator's build that keeps a single sign-on login in a folder of its own. The image makes `.config/opencode` itself (owned by `factory`, mode `0755`, so read-only to the agent), because opencode makes it on its first run in a fresh home and would die on the guard's refusal; `RUNTIME_FOLDERS` does not list it. `.config` stays the agent's, for the folders of `FACTORY_OPENCODE_FOLDERS`. Anything else under `.config` is not allowed unless named so: opencode's own configuration there is what the next run reads, and an agent that could write it could change its own tools and permissions.

With `confine_executable`, the run's temporary folder is removed after every call, as the agent user under `sudo` when `os_user` is set, also after a died or killed call.

Tests use `tests/adapters/opencode_stand_in.py` in `tmp_path`; the real `opencode` is never run.

### Ending the agent's leftover processes

Both runtimes take the keyword `leftovers` (a sequence of words, kept in `Starters` and readable as the property `leftovers`, `None` by default). A runtime built without it, as every runtime a test builds, starts no program. With it, `_call` does the following for every call, a first one and a resumed one (so a run stopped by its budget starts the program twice):

1. The call's process runs. A call that cannot be started raises `cannot start <program>: <error>` and nothing follows.
2. When `leftovers_due(...)` holds, with the factory process's own user read once per call by `own_identity().user`, the runtime starts `leftovers_launch(...)` through its `_start` in the working directory `/`. A request without `os_user`, or whose `os_user` is the factory's own user, starts nothing: in an agent's `make test` that user is `agent`, and the program would end the run itself. `version()` starts none.
3. The temporary folder is removed (with `confine_executable`), so no leftover process writes there meanwhile.
4. The call's end is read; a refusal (`sudo`, the wrapper, the login shell) raises as before, and the program's result is not read.
5. Otherwise a `leftovers_fault` that is not `None` raises `AgentRuntimeError(<fault>)`.

The order of the processes of a call is therefore the call, the program, the removal. Because this is inside `AgentRuntime.run`, it comes before the seal's check, the removal of nested repositories, the undo and the checks. `_end_leftovers`, `_remove_temporary_folder` and `_request_of` are near-copies in the two runtimes; `leftovers_fault` takes plain values so the shared part stays in `agent_launch`. The wiring passes the command (`build_boundaries`, *Boundaries* in `watching.md`). The program is described in `write-guard.md`, *The end of a run's processes*.

A project command run as another user by `MakeProjectCommands` is followed by the same program, as that user, in `/`, after every command that started and by the same rule (a `CommandUser` with `leftovers`, not the factory's own user). Its fault is a `ProjectCommandError` there, not an `AgentRuntimeError`.

Tests: `tests/adapters/test_agent_launch_leftovers.py`, `test_claude_runtime_leftovers.py`, `test_opencode_runtime_leftovers.py` (a stand-in `sudo` that records its arguments and working directory, and a stand-in program for `leftovers`; never the real command) and `tests/leftovers_runtime_support.py`. A request that must differ from the factory's user names `factory-test-other`.

### The fake

`FakeAgentRuntime(kill_points=None, version="fake")` (`factory.adapters.fake_agent_runtime`) is what every stage test uses. It inherits `AgentRuntime`, an abstract base class. The `agent_runtime` fixture in `tests/conftest.py` builds one with the test's `kill_points`.

A test queues `ScriptedRun`s (`writes`: path to UTF-8 text, `deletes`, `result`, `kill`) with `queue`. Each `run` call:

1. records the request (`requests()` lists all, in order, also one that raised);
2. takes the oldest queued run, or raises `AgentRuntimeError` when none is queued;
3. checks every path, then writes (parent folders created, an existing file replaced) and deletes (a missing path is ignored) relative to `request.working_directory`. An absolute path or a `..` segment raises `AgentRuntimeError` before anything is written or deleted;
4. when `kill` is true and the fake has kill points, reaches `KillPoint.AGENT_RUN`, which raises `InjectedKill` if armed. The writes are already on disk, as after a real crash;
5. returns the scripted `result`.

```python
agent_runtime.queue(ScriptedRun(writes={"tests/test_a.py": "x = 1\n"}, result=result))
outcome = agent_runtime.run(request)
assert outcome.ok and agent_runtime.requests() == [request]
```

## The agent definition reader

Every role of the pipeline definition needs an agent file of the same name, `<agent home>/agents/<name>.md`. `AgentDefinitionReader` (`factory.application.agent_runtime`, an abstract base class, `Boundaries.agent_definitions`) has three operations and `FrontmatterAgentDefinitionReader(agent_home)` (`factory.adapters.agent_files`) implements them. `ProjectAgentDefinitions` (below) is the one wired as `Boundaries.agent_definitions`. Starting a stage uses `read` to compose every task; `PipelineLoader` uses `names()` to check the roles.

| Operation | Does |
|---|---|
| `names()` | the sorted stems of the regular `.md` files directly in `agents/` whose stem is a `Name`; `[]` for an empty directory |
| `read(name)` | the `AgentDefinition` of the file; `name` is checked as a `Name` before any path is built (`check_agent_name` in `factory.domain.agent_runs`, raising `AgentDefinitionMissing`) |
| `parse(name, text)` | the `AgentDefinition` of the text of an agent file, with every check `read` makes once it has the text; `read` is the file lookup plus `parse` |

The front matter is split as the work item reader splits it, with `split_front_matter`, and loaded with ruamel.yaml through `RuamelYamlHandler`, never PyYAML (so `model: on` is the text `on`). The body, stripped, is `instructions`. Only `model`, `tools`, `effort` and `budget_usd` may appear (`APPLIED_AGENT_KEYS` in `factory.domain.agent_runs`): the runner builds its flags and its prompt from them, because Claude Code ignores an agent file in print mode.

| Key | What the runner does with it |
|---|---|
| `model` | passed as the model of the run |
| `tools` | the tools the run may use |
| `effort` | the effort level of the run; optional |
| `budget_usd` | the budget of the run; the run ends with `budget` when it is spent |

Any other key is refused with `AgentDefinitionInvalid` (fault `key not applied by the agent runtime: <key>`, `key` the first such key in the file's order, keys compared as written so `Model` is refused) before the applied keys are validated, so it wins over a missing `model` or a bad `budget_usd`. The validated keys go to `AgentDefinition`. `budget_usd` becomes a `Decimal` (`0.1` gives `Decimal("0.1")`). No variable in the module is named `yaml`, because the semgrep rule `factory-no-unsafe-yaml-load` matches any `yaml.load(...)`.

### A project's own agents

`ProjectAgentDefinitions(git, installed, ref=PIPELINE_REF)` (`factory.application.project_agents`) is an `AgentDefinitionReader` over the `Git` interface and an installed reader. `build_boundaries` wires it with the boundaries' `GitCli` and `FrontmatterAgentDefinitionReader(settings.agent_home)`; the loader, the task composer and the preflight reach it through `boundaries.agent_definitions` and know nothing of it.

- `read(name)` checks the name first (no `git` call for a bad one), then reads `factory/agents/<name>.md` at `ref` (`origin/main`) with `git.show_file`. No file: `installed.read(name)`. A file: `installed.parse(name, text)`, so the rules are the installed reader's, and a fault is raised again with the fault text `factory/agents/<name>.md at origin/main: <fault>` and the same `key`. The installed file is then not read: a faulty project file is never replaced.
- `names()` is the sorted union of `installed.names()` and the stems of the files directly in `factory/agents/` at `ref` that are `<name>.md` with a `Name` stem. `GitError` and the installed reader's `AgentDefinitionError` propagate.
- `parse` is the installed reader's.
- It keeps nothing between calls and never reads the work tree, so a push to `main` is seen after the next fetch (the tick fetches) and a branch's copy never.

### Faults

`AgentDefinitionError(name, fault)` is a `FactoryError`. `names()` raises it with `name == ""` and `no agents directory at <path>`. `read` raises a subclass:

| Error | Fault |
|---|---|
| `AgentDefinitionMissing` | `not an agent name: <name>`, `no agent file <path>` |
| `AgentDefinitionInvalid` (`key` is `""`) | `cannot read: <reason>`, `no front matter`, `front matter is not valid YAML`, `front matter is not a mapping` |
| `AgentDefinitionInvalid` (`key` is the unapplied key) | `key not applied by the agent runtime: <key>` (`KEY_NOT_APPLIED` and the key) |
| `AgentDefinitionInvalid` (`key` is the top-level key) | `missing key: <key>`, `budget_usd must be greater than 0`, `invalid <path>: <message>` |

Of several validation faults the first in the order of `first_fault` is reported (unapplied key, unknown key, missing key, invalid value); `first_error` in `factory.adapters.validation_faults` gives the error `first_fault` formats, so the `key` and the fault name the same problem.

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.domain.errors import AgentDefinitionInvalid
with tempfile.TemporaryDirectory() as folder:
    home = Path(folder)
    (home / 'agents').mkdir()
    (home / 'agents' / 'coder.md').write_text('---\nmodel: sonnet\ntools: Read\nbudget_usd: 1\n---\nGo.\n')
    reader = FrontmatterAgentDefinitionReader(home)
    print(reader.names())
    try:
        reader.read('coder')
    except AgentDefinitionInvalid as error:
        print(error.key, '|', error.fault)
"
```

prints `['coder']` and then a line that starts with `tools | invalid tools:`.

## The shipped agents, settings and template

`claude/` and `template/` are data the image carries; no code under `src/` reads them except through the readers named here.

### The seven agents

`claude/agents/<role>.md` holds one agent for each role of the starting pipeline definition. Each file's front matter has exactly the four keys the runner applies (see *The agent definition reader*):

| Agent | model | effort | budget_usd | tools |
|---|---|---|---|---|
| `intake` | sonnet | low | 1 | Read, Grep, Glob, Edit, Bash, Skill |
| `tester` | opus | medium | 2 | Read, Grep, Glob, Edit, Bash, Write, Skill |
| `coder` | opus | medium | 4 | Read, Grep, Glob, Edit, Bash, Write, Skill |
| `reviewer` | opus | high | 3 | Read, Grep, Glob, Edit, Bash, Skill |
| `documenter` | sonnet | medium | 1.5 | Read, Grep, Glob, Edit, Bash, Write, Skill |
| `smoke-tester` | opus | medium | 2 | Read, Grep, Glob, Edit, Bash, Skill |
| `acceptance-reviewer` | opus | high | 8 | Read, Grep, Glob, Edit, Bash, Write, Skill |

Each body starts with two paragraphs: the role's boundary as one sentence, a blank line, and one sentence on what the role's journal entry contains. After them the body carries v1's texts, renamed with the table under "Replaced from v1", under these `## ` sections and no other `## ` heading, in this order:

- `## Rules`: v1's pipeline rules, in every body. The agent ends with a decision, one of the `Allowed decisions` its prompt lists (`question` is always among them), and with a journal entry. The factory commits, pushes and moves the work item; the agent never pushes, checks out, switches, merges, pulls or calls `gh`. v1's rules on the work item, the pipeline definition, commit subjects and the pipeline files are rewritten to what the prompt, the pipeline definition and the write paths say, or dropped where the factory does them in code. R14 tells every agent what a refused write looks like (`Permission denied`), that it is the write guard and never to be retried by another route, and that the agent ends with `question` when the work needs the path; temporary files belong in `$TMPDIR`, the run's own folder, and `/tmp` itself is refused. `tests/test_claude_agent_refusal.py` pins the paragraph word for word.
- `## Role`: v1's role skill. `intake` and `smoke-tester` have none, because v1 had none for them.
  The `reviewer`'s checklist has a sixth item of v1.1's own, *Earlier tests*, done in every review whichever group failed (the sentence before the checklist says so: it stops at the first failing group of 1 to 5, and item 6 is always part of the review). The reviewer lists each test file that `main` already holds and the diff changes, renames or deletes (any status but `A` in `git diff --name-status main...HEAD`), with the leave for each: the standing leave of `CLAUDE.md` to move a shared test helper, the human's leave (the story naming the test, or the human's answer in the journal), or none needed when the change only adds tests. A change under none of them, or beyond its leave, is a finding. The `acceptance-reviewer`'s check 6 gathers those lists for the human, and an earlier test changed with no leave named is a finding there. The acceptance reviewer does not repeat the diff check over the whole feature. `tests/test_claude_agent_texts.py` pins these passages with anchors.
- `## Stage`: v1's stage skill for the agent's stage.
- `## Lessons`: v1.1's own part, after v1's texts, and always last. It holds the lessons of v1.1's build for the role, one bullet each: the first two bullets (run make targets in the foreground; give a long project command such as `make check` the shell tool's largest timeout, 600000 ms) are in every body; `intake`, `tester`, `coder`, `reviewer` and `documenter` have more. `tester` has two lessons on earlier tests (the standing leave `CLAUDE.md` gives to move a shared test helper, with its entry naming each earlier test file it changed; and, in the mode `a test change the human approved`, making the move that a coder's entry names under that leave), and `coder` ends with one that sends a reviewer's finding of a copied test helper to the tester with `tests`. `tester` still ends with the time-limit lesson: a test that waits for a time limit gives the process it starts room to start (a limit of a few seconds, an upper bound on the elapsed time with room above it, never a check that a one-second limit is met to the tenth). `documenter` ends with the documents-only lesson: when every file it changed is a document, it ends without running `make check`, because the factory runs the stage's checks right after it; when it changed any other file, it runs it. Two lessons belong to the agents that run scripts outside the repository. `smoke-tester` and `acceptance-reviewer` end with the temporary-directory lesson (`documenter` carries it before its last bullet): make every such file in a self-removing temporary directory (`tempfile.TemporaryDirectory()`, or `mktemp -d` with a `trap` in the shell) and leave nothing in `/tmp`. `acceptance-reviewer` ends with one more: when `make test` writes a JUnit report, read each test's time from it and name the slowest tests in the slow checks and in the cost. No other agent carries either.

`intake`'s *Stage* step 2 also asks about a smoke test command that passes pytest a `-q` the project's pytest configuration already sets (`addopts` in `pyproject.toml`, `pytest.ini`, `setup.cfg` or `tox.ini`), because at `-qq` pytest prints no summary line. `tests/test_claude_agent_texts_smoke_pytest.py` pins the sentence and that no other agent carries it.

The texts come from v1 (pkrahmer/factory at `f8bc9d2`) so that the baseline run compares with v1's run on the same instructions. The words are renamed, the sentences are not rewritten in other words. The passages below are v1.1's own text and not v1's. Every other sentence outside `## Lessons` is v1's, and an edit keeps v1's words there:

- The sentence before the `reviewer`'s checklist, the checklist's sixth item *Earlier tests*, and the `acceptance-reviewer`'s added sentence in its check 6, described in the `## Role` bullet above (F0016-S0002).
- The `reviewer`'s `Notes:` from round 1 on, and its added criterion (F0021-S0005).
- The `reviewer`'s correction of a stale Description, which it rewrites when the journal, the Interface or the criteria settle it and names as `description corrected:` (F0034-S0001).
- Rule R14 in every `## Rules`: the kernel refuses every other write, a refused write fails with `Permission denied` and is never retried by another route, and temporary files go only in `$TMPDIR` (F0019-S0006). F0041-S0001 took out its clause on the hook.
- Rule R15 in every `## Rules`: a project's skills and agents are the human's files (F0022-S0002).
- `intake`'s sentence in its *Stage* step 2 on a smoke test that passes `-q` (F0035-S0001).
- The `acceptance-reviewer`'s comparison, in its check 7, of the Disk now line with the previous record line (F0012-S0017).
- The `acceptance-reviewer`'s check 3 *Mutation testing*, "By sweep, not run here", and the words F0031-S0001 changed around it: check 7 ("but not `make mutants`"), the recommendation, the proposals paragraph and *Stage* steps 1 and 3, which no longer run `make mutants` or report its score (F0031-S0001).

(the table of renamed words is under "Replaced from v1")

`stuck` does not exist in v1.1: an agent that cannot finish asks. The `acceptance-reviewer` body names the report sections `## Recommendation` and `## Proposed stories` inline (the acceptance reads them; at the start of a line they would be headings), the recommendations `accepted`, `accepted with stories` and `not accepted`, and tells the agent to write proposed stories into the feature's `backlog/`.

To change what an agent is told, edit its file under `claude/agents/`; there is no other copy of a shipped agent. A project's own agent is its file under `factory/agents/` on `origin/main` (see *A project's own agents*). `tests/test_claude_agent_texts.py` checks the sections, the banned v1 words, the decisions (derived from `next` in `template/factory/pipeline.yml`), the anchor phrases and the exact `## Lessons` bullets. No skills are shipped: the agents load the project's own with the `Skill` tool (last in every `tools`; allowed in `claude/settings.json`). Rule R15, the line after R14 in every `## Rules`, says a project's skills (`.claude/skills/`) and agents (`factory/agents/`) are the human's files, that an agent loads a skill whose description fits its work, and that where a skill contradicts the agent's instructions the instructions win and the entry names the skill and the step set aside. `tests/test_claude_agent_skills.py` pins the line. The entrypoint empties `skills/` and `commands/` of the Claude home at every start (see the operator guide).

`tests/test_claude_files.py` checks the files (keys, values, bodies); `tests/adapters/test_shipped_agents_effect.py` runs `ClaudeCodeRuntime` against the stand-in executable over each shipped agent and checks that `--model`, `--effort`, `--tools`, `--max-budget-usd` and the instructions file carry the file's values. `tests/shipped_agents.py` holds the shared table.

### The settings

`claude/settings.json` is the permissions and environment every agent run shares. It allows file tools, `uv run`, `uv sync`, `make`, `factory-check-story` and the read-only git commands `status`, `diff`, `log`, `show` and `rev-parse`. It denies `git add` and `git commit` (the agent leaves its changes in the working tree and the factory makes the result commit, R10; the agents' `## Rules` say "You do not commit either", and a denied command is refused by the runtime where an unlisted one would ask for a permission nobody can give), `git push`, `checkout`, `switch`, `merge`, `pull`, `rebase`, `reset`, `branch -D`, `gh` and `rm -rf`. `factory-check-story` is the only `factory-` command allowed: an agent may not run `factory-run`, `factory-watch` or `factory-bill`. The environment sets `CLAUDE_CODE_FORK_SUBAGENT` to `0`. A test compares the file with the expected document, so any change is a deliberate edit of both.

### The template

`template/` is what a new project starts from, laid out as the project's tree. It holds three files and nothing else:

- `template/factory/pipeline.yml`, the starting pipeline definition. Its roles are the seven agents above. The stages run `intake`, `tests`, `doing`, `review`, `docs`, `smoke-test`, then `approval`; `acceptance` is the acceptance stage. Copy it to `factory/pipeline.yml` and adjust it. The file holds the four project commands `check`, `lint`, `test` and `sync` with their `time_limit`s (`sync`, the tools after a checkout, is run by the stage environment and listed by no stage), the `tool_paths` the project's tools may write besides the write paths, the seven roles with their write paths, and the stages. This guide does not copy it, because a copy goes stale with every change of the file: read the file itself.

  The coder's write path is `src/*` only; a project that keeps code elsewhere changes it.
- `template/CLAUDE.md`, the starting rules file of a Python project. It has placeholders in angle brackets for the project's own architecture, test framework and checks, and it carries the Python lessons of v1.1's build (the `mypy --strict` traps in tests, low-entropy hexadecimal test values, and the time-limit lesson: a test that waits for a time limit gives the process it starts room to start). It also gives a standing leave to move a shared test helper: a helper, constant or fixture that a new test would copy from another story's test module, or that an earlier module still holds as a copy, may be moved to one shared place under `tests/`, and the earlier tests changed to use it, without asking, as long as every earlier test keeps its name and checks the same thing. The tester makes the move, never the coder; any other change to another story's test still needs the human's leave.
- `template/Makefile`, the project commands of a Python project with a src layout, in the pattern of `factory-rf`'s own. Its targets are the contract's four, `check`, `lint`, `test` and `sync` (`uv sync --frozen`, between `check` and `lint`, not run by `check`), and the other targets `check` runs: `types`, `layers`, `sast`, `secrets` and `licenses`. Every recipe runs in one shell and ends with `<target>: green (<seconds> s)`; `make test` runs on every core and writes a JUnit report; `make secrets` scans the files changed against `origin/main`, and leaves out `uv.lock`, `.secrets.baseline` and every file ending `.costs.jsonl`. Those are the factory's cost records: they hold run metadata and no secret, and their 32-character hexadecimal run ids read to detect-secrets as high-entropy secrets, which made the coder's `make check` red at the tiny story of 2026-10-18 (F0099-S0001 on the todo demo). The todo demo's `secrets` recipe is the template's, and `tests/test_demo_makefile_secrets.py` keeps them equal. `duplicates` is a report outside `check`: it writes similar code and dead code to `.reports/` and counts them, and compares them with no baseline. `mutants` is for a sweep by hand and is never run by a stage: `make mutants FEATURE=<feature id>` runs mutmut over the modules that the feature's story commits on `origin/main` changed, found by the subjects `work item <id>: ...` (or `<id>: ...` after a squash merge), and `FEATURE` is taken from an acceptance's branch `work-item/<feature id>-A<number>`. There is no `documents` target. A project fills in two placeholders, `SOURCE` (its package folder) and `LAYERS` (its layers command), and the file's header names the development dependencies the targets need.

The template ships no forms. The story and feature forms (`factory/story-form.md`, `factory/feature-form.md`) are the human's to add to a project made from it. Until `factory/story-form.md` exists, `StoryFormChecker` (see *The story form check* in `stages.md`) stops every stage.

## Replaced from v1

The shipped agents carry v1's texts, renamed with this table (the sentences are not rewritten in other words, except the passages of v1.1's own text that *The seven agents* lists):

| v1 | v1.1 |
|---|---|
| ticket | work item |
| log | journal |
| `drafts/` | `backlog/` |
| `ongoing/` | `in-progress/` |
| promote | start |
| `stages.yml`, stage table | the pipeline definition (`factory/pipeline.yml`) |
| lane | write paths |
| gate, the stage `accept` | approval |
| demo (the stage and the agent) | smoke test |
| acceptor | acceptance reviewer |
| outcome (of an agent) | decision |
| verdict | recommendation |
| `max_rounds` | `round_cap` |
| `stuck` | `question` |
| `Assignment`, `## Assignment` | `Description`, `## Description` |
| `## Log (append only)` | `## Journal` |
| `## Demo`, Demo (the story's section) | `## Smoke test`, smoke test |
