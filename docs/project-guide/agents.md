# The agent runtime, the agent files and the template

This file covers the agent runtime, the agent files, the shipped agents and the template; read the index, `README.md`, first.

## The agent runtime

The factory reaches an agent only through the `AgentRuntime` interface (an abstract base class, `factory.application.agent_runtime`): `run(request) -> AgentRunResult` and `version() -> str`. The DTOs are in `factory.domain.agent_runs`. All are frozen and forbid unknown keys. The `claude -p` implementation is `ClaudeCodeRuntime` and the `opencode run` implementation is `OpencodeRuntime` (both below); each inherits `AgentRuntime`. The fake is the third implementation.

`AgentRunRequest` holds:

- `agent`: an `AgentDefinition` (`name`, `model`, `tools`, `effort` or `None`, `budget_usd` greater than 0, `instructions`). `name` is a `Name` (`factory.domain.identifiers`): lower-case letters, digits and hyphens, starting with a letter.
- `prompt`, `time_limit` (greater than zero) and `working_directory` (absolute).
- `allowed_decisions`: must contain `QUESTION` (`"question"`) and have no repeats, so an agent can always ask the human. The validation error names `question`.
- `environment`: the run's whole environment, `{}` by default; `guard`: optional `GuardSettings` (absolute `root`, `write_paths`, `protected_paths`). The request carries no operating-system user: the agent runs as the factory's own user, or in a container.

`AgentRunResult` holds `end_reason`, `decision`, `entry`, `duration`, `turns`, `tokens` (`TokenCounts`: `input`, `output`, `cache_read`, `cache_creation`, none negative), `cost_usd`, `permission_denials` and `login`. `login` (`Login = Literal["api_key", "subscription", "none"]`) is the login the run's calls were handed, `None` when the runtime has no login file; unlike `decision` and `entry` it is set whatever the end reason, and a resumed run's is that of its last call. `end_reason` is one of `completed`, `no_result`, `time_limit`, `budget`, `died` and `provider_limit`. `session` is the runtime's own id of the session the run used, set by both runtimes whatever the end reason (`None` when the runtime never learned one); `limit_wait` (a positive `timedelta`) is set only on a `provider_limit` run, and a result of any other end reason with a `limit_wait` is refused (`a run that ended by <reason> has no limit_wait`). `AgentRunRequest.resume_session`, when set, is not blank and names a session the same runtime made: the run continues it with the request's prompt and budget. `decision` and `entry` are set exactly when the run is `completed`, and `ok` is true exactly then. A measure the runtime did not report is `None`, never 0: unknown is unknown.

A run that dies, reaches its `time_limit`, exhausts its budget or meets a provider's spend limit is a result with an end reason, not an exception; for the caller it is a stall. `AgentRuntimeError` is for a runtime that cannot be used at all. See `docs/decisions.md`.

### The `claude -p` runtime

`ClaudeCodeRuntime(executable, state_directory, kill_points=None, *, version_time_limit=VERSION_TIME_LIMIT, login_file=None, api_login_file=None, provider_limit=None, containers=None)` (`factory.adapters.claude_runtime`) runs an agent as a `claude -p` call, under the factory process's own login; a call stopped by its budget is resumed once (below).

With `login_file` or `api_login_file` set, every call (not `version()`) starts through a login shell whose words come from `login_argv(LoginFiles(subscription=login_file, api=api_login_file))` (`factory.adapters.agent_launch`, below), followed by `<executable> <arguments>`. With neither file there are no words. The request's own `CLAUDE_CODE_OAUTH_TOKEN` and `ANTHROPIC_API_KEY` entries are dropped (`without_login`): the files are the only source. The factory never reads either file. A refusal in standard error (`login_refusal`) raises `AgentRuntimeError("cannot read the agent's login file <path>: <reason>")`, or `"cannot read the agent's API login file <path>: <reason>"` for the API file, unless the reply parses. The result's `login` is `login_used(stderr)` of the run's last call. The file is read again at every call, so a changed file applies to the next call of the same runtime. The module re-exports `LOGIN_SCRIPT`, `LOGIN_VARIABLE`, `LOGIN_PREFIX` and `SHELL_EXECUTABLE` in its `__all__`. It starts the process through `run_process`, and with `git_cli` and `make_commands` it is one of the modules that import `factory.adapters.process` (`git_cli`, `make_commands` and `opencode_runtime` are the others; `tests/test_wrapper_search.py`).

### Calls in a container

Both runtimes take `containers: ContainerRuns | None = None`, readable as the `containers` property. This is step 5 of the cycle (*The agent's container* in `stage-environment.md`); the wiring that gives the runtimes their `PodmanRuns` is not part of the runtimes.

- The run's files are the same as on the host: the instructions file (Claude Code) or the configuration file (opencode) in the state directory, nothing else. Each call's `ProcessRequest` comes from `container_launch` instead of `run_launch`, the choice made in the runtime's `_process_request`. Its words are the same as on the host (the login shell words, then the runtime's), The files it mounts are `[*login_paths(files), <the call's file>]`, read-only at their own paths, so the words do not change. The environment is `run_environment(...)`: for Claude Code the three switches, for opencode `OPENCODE_CONFIG` (the configuration file's path) and its switches. The working directory in the container is `/work/checkout` and `HOME` is whatever the request's environment says (`/work/home` in a stage); the request's `working_directory` is the `cwd` of podman on the host.
- Nothing follows the call: the container ends with it, and podman's `--timeout` ends it whole. The login files are mounted, so the login shell reads them as ever and `factory-login-used:` is read as ever.
- A call that ends with exit status 137, -9 or 255 (podman's `--timeout` status) at or after its time limit is read as `time_limit` (`in_container=True`), is not resumed and has its measures unknown; before the limit it is `died`. A budget stop of Claude Code is resumed as on the host, in a second container with the same mounts.
- `version()` runs `version_launch(executable, containers=..., time_limit=version_time_limit)` in a container too, with no mounts and an empty environment, so the preflight's `agent-runtime-version` reads the stage image's runtime.

### The shared launch module

`factory.adapters.agent_launch` holds what every agent runtime shares to start a call; the opencode runtime reuses it. It imports no `factory.adapters.process` and reads no `os.environ`: it builds words, rules and texts, and each runtime starts its own processes. It holds the login shell (below) and the start of a run: the words, the refusals and the resume share. No call starts through a write guard's wrapper, so the module builds no rules file and no temporary folder, and sets no `CLAUDE_CONFIG_DIR`. `ClaudeCodeRuntime` calls these functions; it keeps its own process calls, the reply's parsing and `_since`. The names a test sets on `claude_runtime` (`SHELL_EXECUTABLE`, `run_process`) are read from that module's namespace at the call and passed in, and the moved constants (`ENTRY_DESCRIPTION`, `FINISH_MESSAGE`, `VERSION_TIME_LIMIT`, `resume_budget`) stay names of `claude_runtime` through its `__all__`.

- `launch(argv, environment, *, time_limit)` gives a frozen `Launch(argv=list(argv), env=dict(environment), time_limit=time_limit)`; `env` is `None` only where a caller builds the `Launch` itself (what `PodmanRuns.launch` gives and `version_launch` uses without containers). `run_launch(request, argv, runtime_environment, *, time_limit)` is the same for a request: its environment without logins, with the runtime's switches. No `sudo`, `timeout` or `env -i` word is added.
- `line_starting(stderr, prefix)` is the first line that starts with the prefix (the login prefixes). `killed_at_limit(*, exit_status, duration, time_limit, in_container=False)` is true only `in_container`, with a status in `CONTAINER_KILL_STATUSES` (137, -9 and 255, `PODMAN_TIMEOUT_STATUS`) and a duration at or above the limit, so podman's `--timeout` kill is read as the limit. A call on the host is ended at its limit by the factory's own kill, which `run_process` reports as `timed_out`, so a kill status there is a death. `first_word(output)` is the first word of the first non-blank line (the version).
- `Starters` holds `login_files` alone.
- `call_refusal(stderr, *, printed, starters)` reads a refused login file only (a `factory-login:` or `factory-api-login:` line): it returns the refusal, or `None`. A `sudo:` line is no refusal.
- `read_call_end(end, *, time_limit, starters, in_container=False)` reads the end of a call for both runtimes and gives whether it ended at its time limit. `end` is a frozen `CallEnd(stderr, printed, exit_status, duration, timed_out)`, the process's fields and not a `ProcessResult` (the module imports no `process`). The kill is read first: the call is timed out when `end.timed_out` is set (the factory's own kill) or `killed_at_limit(...)` is true. The refusal of the login shell (`call_refusal`) is read with that value, so a call that printed a reply and was killed is still read for refusals; a refusal raises `AgentRuntimeError` with the refusal as its detail. `state_directory_error(state_directory, error)` returns (does not raise) `AgentRuntimeError("cannot write the state directory <dir>: <error>")`; both runtimes use it. Each runtime keeps its own process calls (`_start`, `_request_of`, `version`), because the module imports no process module.
- `container_launch(containers, argv, environment, *, files, time_limit)` is `containers.launch(argv, mounts=..., environment=environment, time_limit=time_limit, working_directory=WORK_CHECKOUT)` as a `Launch`: one read-only `Mount` per file, at the file's own path, each file once in the order first given. It raises what `launch` raises (`ValueError` for a file under `/work`, with no call recorded). `run_environment(request, runtime_environment)` is the call's environment for both ways: the request's without logins, with the runtime's switches. `login_paths(files)` lists the login files that are set, the subscription file first. `version_launch(executable, *, containers, time_limit)` is `<executable> --version`: `Launch(env=None)` without containers, `container_launch(..., {}, files=[])` with them.
- `resume_budget(budget)` is a quarter of the budget, at least `MINIMUM_RESUME_BUDGET` (0.50), rounded half up to cents; `FINISH_MESSAGE` is the resumed call's prompt.
- `resumed_result(first, second)` is in the domain (`factory.domain.agent_runs`): the sum of a resumed run, by the rules under "Measures of a resumed run" below. It takes `second`'s end reason, decision, entry and login, joins the refused calls (first call's first, `path` unchanged) and adds the durations; the run sets the whole run's clock afterwards.

- `LOGIN_SCRIPT` is built from the module's constants only (an f-string, so its source holds no `NAME="..."` pair of a secret's name), and runs as the factory's own user. With `--api-login <file>` and a file that holds a key (anything left once spaces, tabs, carriage returns and line feeds are removed) it exports `ANTHROPIC_API_KEY`, unsets `CLAUDE_CODE_OAUTH_TOKEN`, prints `factory-login-used: api_key` on standard error and `exec`s the command; the token file is not read. Otherwise it unsets `ANTHROPIC_API_KEY`, reads the token file as before (a missing or empty file, or an empty argument, is no token) and prints `factory-login-used: subscription` or `factory-login-used: none`. A file that exists but is not a readable regular file, or holds a byte other than printable ASCII, space, tab, carriage return or line feed, prints `factory-api-login: <reason>` (API file) or `factory-login: <reason>` (token file), with the reason `cannot be read` or `not ASCII text`, and exits 1 without starting the command.
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

Environment: the call gets `request.environment` plus `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` and `PYTHONDONTWRITEBYTECODE=1`. Nothing is inherited from the factory's process and no `PATH` is added. The call runs in `request.working_directory`.

A call on the host. The argument vector is the login words (when a login file is set) followed by `<executable> <arguments>`, started with the environment above and nothing from the factory's process: no `sudo`, `timeout` or `env -i` word. A call that reaches its `time_limit` is ended by the factory's own kill (`run_process` reports `timed_out`) and ends `time_limit` without measures; the resume goes through the same call with what is left of the limit. The instructions file keeps the mode the process's umask gives. A standard-error line from the login shell (`factory-login:` or `factory-api-login:`) raises `AgentRuntimeError` when the call printed no reply that parses; a `sudo:` line is no refusal. `agent_run_environment(settings, base)` in `factory.entry.wiring` sets `HOME` to `/work/home` whatever the settings; a call on the host, which only the suite makes since F0044-S0008, keeps the environment it is given.

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

### The agent's home

The agent's home is the dataset's `home/` (`HOME=/work/home` in every container). The rollback to the base gives every stage a fresh one, so the factory resets nothing; a run resumed after a provider limit finds its session in the same `home/`.

### The opencode runtime

`OpencodeRuntime(executable, state_directory, kill_points=None, *, models=None, settings_file=None, version_time_limit=VERSION_TIME_LIMIT, api_login_file=None, provider_limit=None, containers=None)` (`factory.adapters.opencode_runtime`) runs an agent as one `opencode run` call and reads the run's result from the JSON events the call prints. `_agent_runtime` in `factory.entry.wiring`, called by `build_boundaries`, builds it when `settings.agent_runtime` is `opencode` (`FACTORY_AGENT_RUNTIME`; otherwise it builds the Claude Code runtime): with `settings.opencode_executable`, `<state>/runs`, `models=settings.opencode_models`, `settings_file=agent_home / "settings.json"`, `api_login_file` and `provider_limit`. The budget stop, the provider limit and the resume while the run streams are built in the runtime itself. Its keyword `provider_limit` (last; `None` is `ProviderLimit()`, status 428 and no message) is the limit it recognizes. It reads no `os.environ`; its starts go through `run_process` and `run_streaming`, whose callback (`_Watch`) reads each line as it arrives and may stop the call.

**The call.** The words are, in order, the login words of `login_argv` (an API login file only; there is no subscription file), `<executable> run --format json --auto --model <model> --agent factory-<name> <prompt>`, the prompt one argument, in the request's working directory. `<model>` is the agent's `model` as it is when it holds a `/`, otherwise `models[alias]`; an alias without a mapping raises `AgentRuntimeError`. No wrapper, rules file or temporary folder stands between the login words and the command. The call's environment is the request's, without `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` (the login file is the only source), plus `OPENCODE_CONFIG` and `PYTHONDONTWRITEBYTECODE=1`. `version()` runs `<executable> --version` without login words and returns the first word of the first non-blank line (`1.19.3`), with the errors of the Claude Code runtime.

**The per-run configuration.** opencode has no flag for an agent's prompt, tools or permissions, so the runtime writes `opencode-<run>.json` into `state_directory` (the mode the process's umask gives) and names it in `OPENCODE_CONFIG`. The file defines one primary agent, `factory-<name>`, from the same `AgentDefinition` the Claude Code runtime gets from `claude/agents/*.md`:

- `prompt`: the agent file's body, a blank line and `result_instructions(allowed_decisions)`;
- `tools`: all twelve of `OPENCODE_TOOLS`, true for the agent file's tools translated through `TOOL_NAMES` (`Read` is `read`, `Bash` is `bash`, and so on) and false for the rest; a tool in `LEFT_OUT_TOOLS` (`Skill`) turns on no opencode tool and is not refused, so only Claude Code's runs load skills; every other tool outside `TOOL_NAMES` raises `AgentRuntimeError`;
- `permission`: `edit` allowed and `bash` `{"*": "allow"}` plus a `"deny"` for the pattern of each `Bash(<pattern>)` entry in `permissions.deny` of `settings_file` (the installed `settings.json`). Entries for other tools are not translated. A settings file that cannot be read, or holds no `permissions.deny` list of strings (also when it is no JSON), raises `AgentRuntimeError`; with no `settings_file` only `{"*": "allow"}` is written;
- `autoupdate` false, `share` `disabled` and `snapshot` false, so a run neither updates itself nor uploads or snapshots anything.

The model, tools and settings are checked before any file is written; the state directory must exist (the runtime does not create it; the Claude Code runtime does). The difference is deliberate: the image creates `/state/runs`. The configuration is removed after the run, whatever its end. Why the agent is generated and not shipped: see *opencode's agent is generated per run from the shipped agent files* in `docs/decisions.md`.

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

**The end reason.** A timeout is `time_limit` with no measures. In a container, a call that ends with a status in `CONTAINER_KILL_STATUSES` after a duration of at least its limit is `time_limit` too, with the `session` of its events and the `login` the shell reported; the same kill status before the limit, or any other status after it, is `died`. A call the callback stopped is `budget` or `provider_limit` (above). Otherwise a non-zero exit or no `step_finish` is `died`; a valid block is `completed` (with its decision and entry); anything else is `no_result`. A stderr line from the login shell is a refusal only when no valid event was printed.

**The budget.** opencode has no budget flag, so the callback keeps it. It adds up the `cost` of each `step_finish` of the call (as `Decimal`) while the call streams and stops the call as soon as the sum is greater than the call's budget: the agent's `budget_usd` for the first call, `resume_budget(budget_usd)` for a resume. A sum equal to the budget does not stop it. The call ends `budget` with the measures of the events read. A step is only counted when it finishes, so a run may pass its budget by the cost of one step.

**The budget resume.** A first call that ends `budget` with a known session is resumed once: the same words with `--session <session>` before the prompt, `FINISH_MESSAGE` as the prompt, `resume_budget(budget_usd)` as the budget, within what is left of the request's time limit (a resume past it ends the run `time_limit`). The run's configuration and rules files are the first call's and are removed only after the resume. The result is `resumed_result` of the two calls: a resume that is also over its budget ends the run `budget`, with no third call, and one stopped by a limit ends it `provider_limit`. With no known session (no event carried a `sessionID`) the budget stop is the run's result. The kill point `AGENT_RUN` is reached once, after the whole run.

**The provider limit.** The callback stops the call at once, as `provider_limit`, on an `error` event whose `error.data.statusCode` is the limit's status or whose `error.data.message` holds the limit (`limit_in_text`), and on a line of standard error that holds it. It reads no limit from a `text` or `tool_use` event or from any other field, so an agent that writes "428", or a tool whose output holds it, stops nothing. An `error` event that is no limit does not stop the call; the call ends by the rules below. The result keeps the measures of the events read, the session, and a `limit_wait` of `named_wait` of the message or line (`None` when it names none). A limit is never resumed here: waiting it out and continuing the session is the application layer's (S0007). A time limit that ended the call wins over a recorded stop.

**opencode's folders.** opencode writes its sessions, logs and caches to `.local/share/opencode`, `.local/state/opencode` and `.cache/opencode` in the agent's home. The runtime names no folder for them: no rules file allows or refuses a write since F0044-S0001, and the dataset's rollback clears them with the rest of the home. The image makes `.config/opencode` itself (owned by `factory`, mode `0755`, so read-only to the agent): opencode's own configuration there is what the next run reads, and an agent that could write it could change its own tools and permissions.

Tests use `tests/adapters/opencode_stand_in.py` in `tmp_path`; the real `opencode` is never run.

### Ending the agent's leftover processes

A container ends with its call, and podman's time limit ends it whole, so nothing an agent started outlives the call there. The program that once ended the agent's processes after every call as another user went with F0044-S0003; the kill of a call at its time limit stays (`killed_at_limit`, above).

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
- Rule R14 in every `## Rules` (decision 4 of F0044, F0044-S0001): after the stage the factory takes only the changed paths the role may write and leaves every other change out, whatever tool or command made it, so a write elsewhere is lost; when the work needs another path the agent ends with `question`; temporary files go through `mktemp` or `tempfile` and are lost with the stage. Before F0044-S0001 the rule promised a kernel that refused every other write, with `$TMPDIR` as the one temporary place (F0019-S0006); F0041-S0001 took out its clause on the hook.
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

- `template/factory/pipeline.yml`, the starting pipeline definition. Its roles are the seven agents above. The stages run `intake`, `tests`, `doing`, `review`, `docs`, `smoke-test`, then `approval`; `acceptance` is the acceptance stage. Copy it to `factory/pipeline.yml` and adjust it. The file holds the four project commands `check`, `lint`, `test` and `sync` with their `time_limit`s (`sync`, the tools after a checkout, is run by the stage environment and listed by no stage), the seven roles with their write paths, and the stages. This guide does not copy it, because a copy goes stale with every change of the file: read the file itself.

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
