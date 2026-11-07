# The agents area: runtimes, agent files, the template and the write paths

Read this page when you change how the factory starts an agent, reads an agent file, ships its agents and template, or decides what an agent may write. Read the index, [README.md](README.md), first. The words in italics that the factory gave its own meaning are in the [glossary](glossary.md).

## The agent runtime

The factory reaches an agent only through one interface, so that a second tool can stand beside the first. A run is a request in and a result out: a run that dies or runs out of time or money is a result with an end reason, not an exception, and for the caller it is a stall. The interface is in [agent_runtime.py](../../src/factory/agents/application/agent_runtime.py), the DTOs in [agent_runs.py](../../src/factory/agents/domain/agent_runs.py). All DTOs are frozen and forbid unknown keys.

    AgentRuntime.run(request: AgentRunRequest) -> AgentRunResult
    AgentRuntime.version() -> str
    AgentRuntime.read_transcript(home: Path, session: str) -> Transcript | None
    AgentRuntime.tool_uses(transcript: Transcript) -> list[ToolUse] | None

- `ClaudeCodeRuntime` (the `claude -p` call, see [claude_runtime.py](../../src/factory/agents/adapters/claude_runtime.py)) and `OpencodeRuntime` (the `opencode run` call, see [opencode_runtime.py](../../src/factory/agents/adapters/opencode_runtime.py)) inherit `AgentRuntime`; `FakeAgentRuntime` is the third implementation.
- `AgentRuntimeError` is for a runtime that cannot be used at all; every other fault of a run is an end reason of the result. See [decisions.md](../decisions.md).
- `AgentRunRequest.allowed_decisions` must contain `QUESTION` (`"question"`) and have no repeats, so that an agent can always ask the human. The validation error names `question`.
- `AgentRunRequest.time_limit` is greater than zero and `working_directory` is absolute. `environment` is the run's whole environment, `{}` by default. The request carries no operating-system user: the agent runs as the factory's own user, or in a container.
- `AgentRunResult.ok` is true exactly when the end reason is `completed`; `decision` and `entry` are set exactly then.
- A measure the runtime did not report is `None`, never 0.
- The runtime is chosen per instance by `FACTORY_AGENT_RUNTIME`; `_agent_runtime` in [wiring.py](../../src/factory/entry/wiring.py), called by `build_boundaries`, builds it.

The details of the two DTOs are in *Reference: the request and the result*.

See also: *The agent's container* in [machine.md](machine.md); *The take* in [pipeline.md](pipeline.md).

### The `claude -p` runtime

`ClaudeCodeRuntime` runs an agent as a `claude -p` call, under the factory process's own login. It writes the agent's instructions to a file, passes the model, tools and budget as flags, and reads the JSON reply. A call stopped by its budget is resumed once.

    ClaudeCodeRuntime(executable, state_directory, kill_points=None, *, version_time_limit=VERSION_TIME_LIMIT,
                      login_file=None, api_login_file=None, provider_limit=None, containers=None,
                      extra_environment={}, ca_bundle=None)

- The arguments of a call, in this order, are listed in *Reference: the `claude` call*. `--effort` is left out when the agent has none; `--tools` is always there, with an empty value for an empty list.
- The call gets `request.environment` plus `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` and `PYTHONDONTWRITEBYTECODE=1`. Nothing is inherited from the factory's process and no `PATH` is added. The call runs in `request.working_directory`.
- With `login_file` or `api_login_file` set, every call except `version()` starts through a login shell whose words come from `login_argv(LoginFiles(subscription=login_file, api=api_login_file))`, followed by `<executable> <arguments>`. With neither file there are no words.
- The request's own `CLAUDE_CODE_OAUTH_TOKEN` and `ANTHROPIC_API_KEY` entries are dropped (`without_login`): the files are the only source. The factory never reads either file, and a changed file applies to the next call.
- A refusal in standard error (`login_refusal`) raises `AgentRuntimeError("cannot read the agent's login file <path>: <reason>")`, or `"cannot read the agent's API login file <path>: <reason>"` for the API file, unless the reply parses. A `sudo:` line is no refusal.
- The result's `login` is `login_used(stderr)` of the run's last call.
- The run's one file is `instructions-<session>.md` in `state_directory` (made with its parents by `agent_launch.make_state_directory`, `<session>` a new `uuid4` per run). It is written before the call and removed when the run ends, by a result, `InjectedKill` or `AgentRuntimeError`, and keeps the mode the process's umask gives.
- A call that reaches its `time_limit` is ended by the factory's own kill (`run_process` reports `timed_out`) and ends `time_limit` without measures.
- The module starts its process through `run_process` and, with `git_cli`, `make_commands` and `opencode_runtime`, is one of the modules that import `factory.shared.adapters.process` (`tests/guards/test_wrapper_search.py`).
- `agent_run_environment(settings, base)` in `factory.entry.wiring` sets `HOME` to `/work/home` whatever the settings. A call on the host, which only the test suite makes, keeps the environment it is given.
- Tests use a stand-in executable written into `tmp_path` (`tests/support/claude_stand_in.py`: `write_stand_in(directory, steps)` and `read_calls(directory)`); the real `claude` is never run.

The end reasons, measures, provider limit and resume are in *Reference: the `claude` call*.

See also: *The shared launch module* below; *Calls in a container* below.

### Calls in a container

Every agent call of a stage runs in a throwaway container of the stage image. Both runtimes take the container interface as a constructor argument; the wiring that gives them their `PodmanRuns` is not part of the runtimes.

    ClaudeCodeRuntime(..., containers: ContainerRuns | None = None)
    OpencodeRuntime(..., containers: ContainerRuns | None = None)

- `containers` is readable as the `containers` property.
- The run's files are the same as on the host: the instructions file (Claude Code) or the configuration file (opencode) in the state directory, nothing else.
- Each call's `ProcessRequest` comes from `container_launch` instead of `run_launch`, chosen in the runtime's `_process_request`. Its words are the same as on the host: the login shell words, then the runtime's.
- The files it mounts are `[*login_paths(files), <the call's file>]`, read-only at their own paths, so the words do not change. `ca_bundle` is added to the mounted files, read-only at its own path.
- The environment is `{**extras, **run_environment(...)}`: for Claude Code the three switches, for opencode `OPENCODE_CONFIG` and its switches, beneath which sit the operator's extras (`extra_environment`: the names of `FACTORY_CONTAINER_ENV` and the CA variables). A name the request or the runtime sets wins, and `without_login` still removes the login names afterwards.
- The working directory in the container is `/work/checkout` and `HOME` is whatever the request's environment says (`/work/home` in a stage); the request's `working_directory` is the `cwd` of podman on the host.
- Nothing follows the call: the container ends with it, and podman's `--timeout` ends it whole, so nothing an agent started outlives the call. The login shell reads the mounted login files as ever, and `factory-login-used:` is read as ever.
- A call that ends with exit status 137, -9 or 255 (podman's `--timeout` status) at or after its time limit is read as `time_limit` (`in_container=True`), is not resumed and has its measures unknown. Before the limit the same status is `died`.
- A budget stop of Claude Code is resumed as on the host, in a second container with the same mounts.
- `version()` runs `version_launch(executable, containers=..., time_limit=version_time_limit)` in a container too, with no mounts and an empty environment, so that the preflight's `agent-runtime-version` reads the stage image's runtime.

See also: *The agent's container* in [machine.md](machine.md).

### The shared launch module

[agent_launch.py](../../src/factory/agents/adapters/agent_launch.py) holds what every runtime shares to start a call: the login shell, the words, the refusals and the resume share. It imports no `factory.shared.adapters.process` and reads no `os.environ`; it builds words, rules and texts, and each runtime starts its own processes. No wrapper word stands in front of a call, so the module builds no rules file and no temporary folder and sets no `CLAUDE_CONFIG_DIR`.

    launch(argv, environment, *, time_limit) -> Launch
    run_launch(request, argv, runtime_environment, *, time_limit) -> Launch
    container_launch(containers, argv, environment, *, files, time_limit) -> Launch
    read_call_end(end: CallEnd, *, time_limit, starters, in_container=False) -> bool
    login_argv(files: LoginFiles) -> list[str]

- `launch` gives a frozen `Launch(argv=list(argv), env=dict(environment), time_limit=time_limit)`. `env` is `None` only where a caller builds the `Launch` itself (what `PodmanRuns.launch` gives and `version_launch` uses without containers).
- `run_launch` is the same for a request: its environment without logins, with the runtime's switches.
- `container_launch` is `containers.launch(argv, mounts=..., environment=environment, time_limit=time_limit, working_directory=WORK_CHECKOUT)` as a `Launch`: one read-only `Mount` per file, at the file's own path, each file once in the order first given. It raises what `launch` raises (`ValueError` for a file under `/work`, with no call recorded).
- `run_environment(request, runtime_environment)` is the call's environment for both ways: the request's without logins, with the runtime's switches.
- `read_call_end` reads the end of a call for both runtimes. The kill is read first: the call is timed out when `end.timed_out` is set (the factory's own kill) or `killed_at_limit(...)` is true. The login shell's refusal (`call_refusal`) is read with that value, so a call that printed a reply and was killed is still read for refusals. A refusal raises `AgentRuntimeError` with the refusal as its detail.
- `end` is a frozen `CallEnd(stderr, printed, exit_status, duration, timed_out)`: the process's fields, not a `ProcessResult`.
- `killed_at_limit(*, exit_status, duration, time_limit, in_container=False)` is true only `in_container`, with a status in `CONTAINER_KILL_STATUSES` (137, -9 and 255, `PODMAN_TIMEOUT_STATUS`) and a duration at or above the limit. On the host the factory's own kill ends a call, so a kill status there is a death.
- `Starters` holds `login_files` alone. `call_refusal(stderr, *, printed, starters)` reads a refused login file only (a `factory-login:` or `factory-api-login:` line) and returns the refusal or `None`. A `sudo:` line is no refusal.
- `state_directory_error(state_directory, error)` returns, and does not raise, `AgentRuntimeError("cannot write the state directory <dir>: <error>")`. `make_state_directory(state_directory)` makes the folder with its parents (an existing folder and its files are left as they are) and raises `state_directory_error(...)` from the `OSError` of the `mkdir`, such as a file in the folder's place. Both runtimes call it before they write a run's files.
- `login_paths(files)` lists the login files that are set, the subscription file first. `version_launch(executable, *, containers, time_limit)` is `<executable> --version`: `Launch(env=None)` without containers, `container_launch(..., {}, files=[])` with them.
- `line_starting(stderr, prefix)` is the first line that starts with the prefix. `first_word(output)` is the first word of the first non-blank line (the version).
- `resume_budget(budget)` is a quarter of the budget, at least `MINIMUM_RESUME_BUDGET` (0.50), rounded half up to cents. `FINISH_MESSAGE` is the resumed call's prompt.
- `resumed_result(first, second)` is in the domain (`factory.agents.domain.agent_runs`): the sum of a resumed run (see *Reference: a resumed run*). It takes `second`'s end reason, decision, entry and login, joins the refused calls (first call's first, `path` unchanged) and adds the durations; the run sets the whole run's clock afterwards.
- The names a test sets on `claude_runtime` (`SHELL_EXECUTABLE`, `run_process`) are read from that module's namespace at the call and passed in. The moved constants (`ENTRY_DESCRIPTION`, `FINISH_MESSAGE`, `VERSION_TIME_LIMIT`, `resume_budget`) stay names of `claude_runtime` through its `__all__`, which also re-exports `LOGIN_SCRIPT`, `LOGIN_VARIABLE`, `LOGIN_PREFIX` and `SHELL_EXECUTABLE`.
- `ClaudeCodeRuntime` keeps its own process calls, the reply's parsing and `_since`; each runtime keeps its own `_start`, `_request_of` and `version`.
- Names that contain `key`, `token`, `secret` or `password` are never assigned a string literal (ruff's `S105`, `make secrets`). Tests hold a stand-in key in a name such as `API_LOGIN` and write an environment entry with the name's constant.

The login shell itself (`LOGIN_SCRIPT`, `LoginFiles`, `login_used`, `login_refusal`, `without_login`) is in *Reference: the login shell*.

### The agent's home

The agent's home is the dataset's `home/` (`HOME=/work/home` in every container). The rollback to the base gives every stage a fresh one, so the factory resets nothing; a run resumed after a provider limit finds its session in the same `home/`.

    AgentRuntime.read_transcript(home, session) -> Transcript | None     # Transcript(extension, content)

- The stage calls `read_transcript` right after the run with `<workspace>/home` (the dataset's, not `settings.agent_home`), before the rollback. It keeps the result through `TranscriptKeeper` (`factory.watching.application.transcripts`) into `FACTORY_TRANSCRIPT_DIR` (*Transcripts* in [health.md](../operator-guide/health.md)).
- Claude Code's runtime finds `.claude/projects/*/<session>.jsonl` under `home`. A session id that is not one plain file name (empty, `.`, `..`, or with `/`, `\`, `*`, `?`, `[` or `]`) gets `None`.
- The opencode runtime reads nothing from `home`: it keeps the JSON events the latest run printed (both calls of a run with a budget resume) and returns them for that run's session, `None` for any other.
- The fake returns `ScriptedRun.transcript` for the result's session.
- opencode writes its sessions, logs and caches to its folders under `.local` and `.cache`, in the agent's home and its configuration under `.config`. The runtime names no folder for them; the dataset's rollback clears them with the rest of the home.

### The opencode runtime

`OpencodeRuntime` runs an agent as one `opencode run` call and reads the run's result from the JSON events the call prints. opencode has no flag for an agent's prompt, tools, permissions, budget or structured output, so the runtime generates a configuration for every run, keeps the budget itself while the call streams and asks the agent to end with a fixed result block.

    OpencodeRuntime(executable, state_directory, kill_points=None, *, models=None, settings_file=None,
                    version_time_limit=VERSION_TIME_LIMIT, api_login_file=None, provider_limit=None,
                    containers=None, extra_environment={}, ca_bundle=None, provider_file=None)

- `_agent_runtime` in [wiring.py](../../src/factory/entry/wiring.py) builds it when `settings.agent_runtime` is `opencode` (`FACTORY_AGENT_RUNTIME`; otherwise it builds the Claude Code runtime). It passes `settings.opencode_executable`, `<state>/runs`, `models=settings.opencode_models`, `settings_file=agent_home / "settings.json"`, `api_login_file`, `provider_limit` and `provider_file=settings.opencode_provider_file` (`FACTORY_OPENCODE_PROVIDER_FILE`, an absolute path or `None`).
- `provider_limit` is the limit it recognizes; `None` is `ProviderLimit()`, status 428 and no message.
- It reads no `os.environ`. Its starts go through `run_process` and `run_streaming`, whose callback (`_Watch`) reads each line as it arrives and may stop the call.
- The call's words are, in order, the login words of `login_argv` (an API login file only; there is no subscription file), then `<executable> run --format json --auto --model <model> --agent factory-<name> <prompt>`, the prompt one argument, in the request's working directory. No wrapper, rules file or temporary folder stands between the login words and the command.
- `<model>` is the agent's `model` as it is when it holds a `/`, otherwise `models[alias]`. An alias without a mapping raises `AgentRuntimeError`.
- The call's environment is the request's without `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` (the login file is the only source), plus `OPENCODE_CONFIG`, `PYTHONDONTWRITEBYTECODE=1` and, only with a provider file, the three lockdown switches.
- `version()` runs `<executable> --version` without login words and returns the first word of the first non-blank line (`1.19.3`), with the errors of the Claude Code runtime.
- The model, tools, settings and provider file are checked before any file is written. The runtime then makes its state directory with `agent_launch.make_state_directory`, before the `try` that removes the run's files, so the cleanup cannot hide that error. A job starts with an empty state, so the folder is not there at the first run.
- The per-run configuration `opencode-<run>.json` is written into `state_directory` (the mode the process's umask gives), named in `OPENCODE_CONFIG`, and removed after the run, whatever its end.
- The session, the end reason, the budget, the budget resume and the provider limit are in *Reference: the opencode call*; the configuration, the result block, the provider file and the lockdown switches are in *Reference: the opencode configuration*.
- Tests use `tests/support/opencode_stand_in.py` in `tmp_path`; the real `opencode` is never run.

See also: *The agent definition reader* below, for the `AgentDefinition` the configuration is built from; [decisions.md](../decisions.md), *opencode's agent is generated per run from the shipped agent files*.

### The bearer token

The runtime does not renew a token. For a model API behind a client-credentials grant, a refresher runs beside the factory and keeps the file `FACTORY_API_LOGIN_FILE` names fresh; the runtime reads that file at every call.

    python -m factory.entry.refresh_token

- The command is [refresh_token.py](../../src/factory/entry/refresh_token.py), `factory.entry.refresh_token`.
- `Token` and `refresh_wait` are in `factory.agents.domain.tokens`. The wait is ten minutes, or half the token's life when shorter, at least thirty seconds. `TokenError` is in `factory.shared.domain.errors`.
- `TokenSource` and `TokenRefresher` are in `factory.agents.application.tokens`: fetch, then write through `replace_text`.
- `ClientCredentialsTokenSource` is in `factory.agents.adapters.oauth_token`, the one module that may import `urllib.request` and `http.client` (`tests/guards/test_hosting_search.py`).
- Every detail has the client secret and the token replaced by `***`.

See also: *A bearer token for the model API* in [agent-runtime.md](../operator-guide/agent-runtime.md), for the operator's side; [decisions.md](../decisions.md), *A refresher keeps the bearer token fresh*.

### The fake

`FakeAgentRuntime` is what every stage test uses. It inherits `AgentRuntime`. The `agent_runtime` fixture in `tests/conftest.py` builds one with the test's `kill_points`.

    FakeAgentRuntime(kill_points=None, version="fake")     # factory.agents.adapters.fake_agent_runtime
    agent_runtime.queue(ScriptedRun(writes=..., deletes=..., result=..., kill=...))
    agent_runtime.requests() -> list[AgentRunRequest]

- A `ScriptedRun` holds `writes` (path to UTF-8 text), `deletes`, `result`, `kill` and `transcript`.
- Each `run` call records the request first (`requests()` lists all, in order, also one that raised).
- It takes the oldest queued run, or raises `AgentRuntimeError` when none is queued.
- It checks every path, then writes (parent folders created, an existing file replaced) and deletes (a missing path is ignored), relative to `request.working_directory`. An absolute path or a `..` segment raises `AgentRuntimeError` before anything is written or deleted.
- When `kill` is true and the fake has kill points, it reaches `KillPoint.AGENT_RUN`, which raises `InjectedKill` if armed. The writes are already on disk, as after a real crash.
- It then returns the scripted `result`.

```python
agent_runtime.queue(ScriptedRun(writes={"tests/test_a.py": "x = 1\n"}, result=result))
outcome = agent_runtime.run(request)
assert outcome.ok and agent_runtime.requests() == [request]
```

## The agent definition reader

Every role of the pipeline definition needs an agent file of the same name, `<agent home>/agents/<name>.md`. The reader turns a file into an `AgentDefinition`. Starting a stage uses `read` to compose every task; `PipelineLoader` uses `names()` to check the roles.

    AgentDefinitionReader.names() -> list[str]
    AgentDefinitionReader.read(name) -> AgentDefinition
    AgentDefinitionReader.parse(name, text) -> AgentDefinition

`AgentDefinitionReader` is an abstract base class in [agent_runtime.py](../../src/factory/agents/application/agent_runtime.py) (`Boundaries.agent_definitions`). `FrontmatterAgentDefinitionReader(agent_home)` in [agent_files.py](../../src/factory/agents/adapters/agent_files.py) implements it, and `ProjectAgentDefinitions` (below) is the one wired as `Boundaries.agent_definitions`.

| Operation | Does |
|---|---|
| `names()` | the sorted stems of the regular `.md` files directly in `agents/` whose stem is a `Name`; `[]` for an empty directory |
| `read(name)` | the `AgentDefinition` of the file; `name` is checked as a `Name` before any path is built (`check_agent_name` in `factory.agents.domain.agent_runs`, raising `AgentDefinitionMissing`) |
| `parse(name, text)` | the `AgentDefinition` of the text of an agent file, with every check `read` makes once it has the text; `read` is the file lookup plus `parse` |

- The front matter is split as the work item reader splits it, with `split_front_matter`, and loaded with ruamel.yaml through `RuamelYamlHandler`, never PyYAML (so `model: on` is the text `on`). The body, stripped, is `instructions`.
- Only `model`, `tools`, `effort` and `budget_usd` may appear (`APPLIED_AGENT_KEYS`): the runner builds its flags and its prompt from them, because Claude Code ignores an agent file in print mode.
- Any other key is refused with `AgentDefinitionInvalid` (fault `key not applied by the agent runtime: <key>`, `key` the first such key in the file's order, keys compared as written so `Model` is refused) before the applied keys are validated, so it wins over a missing `model` or a bad `budget_usd`.
- `budget_usd` becomes a `Decimal` (`0.1` gives `Decimal("0.1")`).
- No variable in the module is named `yaml`, because the semgrep rule `factory-no-unsafe-yaml-load` matches any `yaml.load(...)`.

| Key | What the runner does with it |
|---|---|
| `model` | passed as the model of the run |
| `tools` | the tools the run may use |
| `effort` | the effort level of the run; optional |
| `budget_usd` | the budget of the run; the run ends with `budget` when it is spent |

The example below reads an agent file whose `tools` is not a list. It runs from a plain shell with `uv run`, and prints the last line of the error:

```console
$ uv run python -c "from factory.agents.adapters.agent_files import FrontmatterAgentDefinitionReader as R; from pathlib import Path; R(Path('.')).parse('coder', '---\nmodel: sonnet\ntools: Read\nbudget_usd: 1\n---\nGo.\n')" 2>&1 | tail -1
factory.shared.domain.errors.AgentDefinitionInvalid: agent coder: invalid tools: <message>
```

See also: *The pipeline definition* in [pipeline.md](pipeline.md); the work item reader's faults in [work.md](work.md).

### A project's own agents

A project may carry its own agents. They are read from `origin/main`, never from the work tree, so a branch cannot change its own agents. `ProjectAgentDefinitions` is an `AgentDefinitionReader` over the `Git` interface and an installed reader.

    ProjectAgentDefinitions(git, installed, ref=PIPELINE_REF)     # factory.agents.application.project_agents

- `build_boundaries` wires it with the boundaries' `GitCli` and `FrontmatterAgentDefinitionReader(settings.agent_home)`. The loader, the task composer and the preflight reach it through `boundaries.agent_definitions` and know nothing of it.
- Module: [project_agents.py](../../src/factory/agents/application/project_agents.py).
- `read(name)` checks the name first (no `git` call for a bad one), then reads `factory/agents/<name>.md` at `ref` (`origin/main`) with `git.show_file`.
- No file: `installed.read(name)`. A file: `installed.parse(name, text)`, so the rules are the installed reader's, and a fault is raised again with the fault text `factory/agents/<name>.md at origin/main: <fault>` and the same `key`.
- The installed file is then not read: a faulty project file is never replaced.
- `names()` is the sorted union of `installed.names()` and the stems of the files directly in `<project>/factory/agents/` at `ref` that are `<name>.md` with a `Name` stem. `GitError` and the installed reader's `AgentDefinitionError` propagate.
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

- Of several validation faults the first in the order of `first_fault` is reported: unapplied key, unknown key, missing key, invalid value.
- `first_error` in `factory.shared.adapters.validation_faults` gives the error `first_fault` formats, so the `key` and the fault name the same problem.

## The shipped agents, settings and template

[agents/](../../agents/) and [operator/template/](../../operator/template/) are data the image carries; no code under `src/` reads them except through the readers named here. To change what an agent is told, edit its file under `agents/agents/`; there is no other copy of a shipped agent. A project's own agent is its file under `<project>/factory/agents/` on `origin/main` (see *A project's own agents*).

### The seven agents

`agents/agents/<role>.md` holds one agent for each role of the starting pipeline definition. Each file's front matter has exactly the four keys the runner applies (see *The agent definition reader*).

| Agent | model | effort | budget_usd | tools |
|---|---|---|---|---|
| `intake` | sonnet | low | 1 | Read, Grep, Glob, Edit, Bash, Skill |
| `tester` | opus | medium | 2 | Read, Grep, Glob, Edit, Bash, Write, Skill |
| `coder` | opus | medium | 4 | Read, Grep, Glob, Edit, Bash, Write, Skill |
| `reviewer` | opus | high | 3 | Read, Grep, Glob, Edit, Bash, Skill |
| `documenter` | sonnet | medium | 1.5 | Read, Grep, Glob, Edit, Bash, Write, Skill |
| `smoke-tester` | opus | medium | 2 | Read, Grep, Glob, Edit, Bash, Skill |
| `acceptance-reviewer` | opus | high | 8 | Read, Grep, Glob, Edit, Bash, Write, Skill |

Each body starts with two paragraphs: the role's boundary as one sentence, a blank line, and one sentence on what the role's journal entry contains. After them come these `## ` sections and no other `## ` heading, in this order:

- `## Rules`, in every body. The agent ends with a decision, one of the `Allowed decisions` its prompt lists (`question` is always among them), and with a journal entry. The factory commits, pushes and moves the work item; the agent never pushes, checks out, switches, merges, pulls or calls `gh`.
- Rule R14 in every `## Rules` says that after the stage the factory takes only the changed paths the role may write and leaves every other change out, whatever tool or command made it, so a write elsewhere is lost. The agent ends with `question` when the work needs another path, and makes temporary files with `mktemp` or `tempfile`, which are lost with the stage. `tests/agent_files/test_claude_agent_refusal.py` pins the paragraph word for word.
- Rule R15, the line after R14, says a project's skills (`.claude/skills/`) and agents (`<project>/factory/agents/`) are the human's files, that an agent loads a skill whose description fits its work, and that where a skill contradicts the agent's instructions the instructions win and the entry names the skill and the step set aside. `tests/agent_files/test_claude_agent_skills.py` pins the line.
- `## Role`. `intake` and `smoke-tester` have none.
- `## Stage`: the stage skill for the agent's stage.
- `## Lessons`, always last: one bullet each. The first two (run make targets in the foreground; give a long project command such as `make check` the shell tool's largest timeout, 600000 ms) are in every body; `intake`, `tester`, `coder`, `reviewer` and `documenter` have more.

The lessons that go beyond those two:

- `tester` has two lessons on earlier tests: the standing leave `CLAUDE.md` gives to move a shared test helper, with its entry naming each earlier test file it changed; and, in the mode `a test change the human approved`, making the move that a coder's entry names under that leave. It ends with the time-limit lesson: a test that waits for a time limit gives the process it starts room to start (a limit of a few seconds, an upper bound on the elapsed time with room above it, never a check that a one-second limit is met to the tenth).
- `coder` ends with one that sends a reviewer's finding of a copied test helper to the tester with `tests`.
- `documenter` has one lesson on the decision log: a "Why" or a "Rejected" in `docs/decisions.md` comes only from what the story names (its Description, Interface, docs criterion and journal, where the human's answers stand), never from the documenter's own reading of the code. Where the story names no rejected option the entry has no "Rejected" line, and the documenter's journal entry names that entry. It ends with the documents-only lesson: when every file it changed is a document, it ends without running `make check`, because the factory runs the stage's checks right after it; when it changed any other file, it runs it.
- `smoke-tester`, `acceptance-reviewer` and `documenter` (before its last bullet) carry the temporary-directory lesson: make every file outside the repository in a self-removing temporary directory (`tempfile.TemporaryDirectory()`, or `mktemp -d` with a `trap` in the shell) and leave nothing in `/tmp`. No other agent carries it.
- `acceptance-reviewer` ends with one more: when `make test` writes a JUnit report, read each test's time from it and name the slowest tests in the slow checks and in the cost.

Other fixed passages:

- The `reviewer`'s checklist has a sixth item, *Earlier tests*, done in every review. The sentence before the checklist says the reviewer goes through all of groups 1 to 5 in every review, also when an earlier group fails, and reports every finding of every group in one entry; item 6 is always part of the review. The reviewer lists each test file that `main` already holds and the diff changes, renames or deletes (any status but `A` in `git diff --name-status main...HEAD`), with the leave for each: the standing leave of `CLAUDE.md` to move a shared test helper, the human's leave (the story naming the test, or the human's answer in the journal), or none needed when the change only adds tests. A change under none of them, or beyond its leave, is a finding.
- The `acceptance-reviewer`'s check 6 gathers those lists for the human, and an earlier test changed with no leave named is a finding there. The acceptance reviewer does not repeat the diff check over the whole feature. `tests/agent_files/test_claude_agent_texts.py` pins these passages with anchors.
- The `reviewer`'s `Notes:` from round 1 on, and its added criterion; its correction of a stale Description, which it rewrites when the journal, the Interface or the criteria settle it and names as `description corrected:`.
- `intake`'s *Stage* step 2 also asks about a smoke test command that passes pytest a `-q` the project's pytest configuration already sets (`addopts` in `pyproject.toml`, `pytest.ini`, `setup.cfg` or `tox.ini`), because at `-qq` pytest prints no summary line. `tests/agent_files/test_claude_agent_texts_smoke_pytest.py` pins the sentence and that no other agent carries it.
- The `acceptance-reviewer`'s comparison, in its check 7, of the Disk now line with the previous record line; its check 3 *Mutation testing*, "By sweep, not run here" (check 7 says "but not `make mutants`"; neither the recommendation, the proposals paragraph nor *Stage* steps 1 and 3 run `make mutants` or report its score).
- `stuck` is not a decision: an agent that cannot finish asks (`question`).
- The `acceptance-reviewer` body names the report sections `## Recommendation` and `## Proposed stories` inline (the acceptance reads them; at the start of a line they would be headings), the recommendations `accepted`, `accepted with stories` and `not accepted`, and tells the agent to write proposed stories into the feature's `backlog/`.

The words of the agent files are the factory's (work item, journal, backlog, `in-progress/`, start, the pipeline definition, write paths, approval, smoke test, acceptance reviewer, decision, recommendation, `round_cap`, `question`, `## Description`, `## Journal`, `## Smoke test`).

- `tests/agent_files/test_claude_agent_texts.py` checks the sections, the banned old words, the decisions (derived from `next` in `operator/template/factory/pipeline.yml`), the anchor phrases and the exact `## Lessons` bullets.
- `tests/agent_files/test_claude_files.py` checks the files (keys, values, bodies).
- `tests/agents/adapters/test_shipped_agents_effect.py` runs `ClaudeCodeRuntime` against the stand-in executable over each shipped agent and checks that `--model`, `--effort`, `--tools`, `--max-budget-usd` and the instructions file carry the file's values. `tests/support/shipped_agents.py` holds the shared table.
- No skills are shipped: the agents load the project's own with the `Skill` tool (last in every `tools`; allowed in `agents/settings.json`).

### The docs route

A story whose Interface changes only paths the documenter may write (`README.md`, `docs/*`, `operator/README.md`) takes the docs route. It has no tests stage and no doing stage, so its criteria are about documents only. Three agent files carry the route; the pipeline definition (`factory/pipeline.yml`) holds the stages `docs-only`, `docs-review` and `docs-approval`.

| Agent | In the stage | What it does |
| --- | --- | --- |
| `intake` | `intake` | Step 6: chooses `docs-only` when every path the Interface changes is one of the three above; otherwise `tests`. |
| `documenter` | `docs-only` | Its `### docs-only` subsection replaces steps 1 to 6 of its Stage. It writes the whole change the docs criterion asks for, runs `make documents` and ends with `docs-review`. Back from the reviewer, it fixes exactly the numbered findings and ends with `docs-review` again. |
| `reviewer` | `docs-review` | Its `### docs-review` subsection replaces the Role's scope, its checklist and its decisions, and steps 1 to 3 of the Stage. It reads the work item and `git diff main...HEAD -- README.md docs operator/README.md`, judges the facts against the code and the criteria and the writing against [style.md](style.md), and ends with `docs-approval` or with `docs-only` and numbered findings. |

- When the documenter finds that the story needs a change outside the documents, it writes nothing for it and ends with `tests`; its entry names the change, and the story takes the code route from there.
- On `docs-review` the reviewer judges the writing against `docs/project-guide/style.md` alone: its rules for all documents and the section for the kind of document the diff changes. The subsection holds no list of rules of its own.
- The agents' other stages do not change, and the opencode runtime reads the same files.
- `tests/agent_files/test_claude_agent_texts_docs_route.py` pins each sentence above in the shipped files. The reviewer's body is also pinned by a checksum (`test_claude_agent_texts_review_groups.py`), which leaves out the `### docs-review` subsection.

### How the agents treat documents

The checks of `make documents` catch names, settings and examples; the rest of a document's truth depends on how the agents work, so three agent files carry rules about it. `tests/agent_files/test_claude_agent_texts_documents.py` pins each rule in the shipped files, one row per rule.

| Agent | Where | The rule |
| --- | --- | --- |
| `documenter` | *Role* | Read the code first: before it writes a sentence about a module, a setting, a command or a behaviour, it reads that code on the branch and writes only what it found. The story and the old text say where to look. |
| `documenter` | *Role* | Every example is runnable, and the documenter ran it. An example that needs the VM, GitHub or a model is marked as such and copied from a real run, and the text names where that run took place. It never writes an output it did not see. |
| `documenter` | *Role* | Exact detail (every option, field, limit and message) goes in a *Reference* section of the document and is moved there, never cut. |
| `documenter` | *Stage* step 2 | When the Makefile has a `documents` target, it runs `make documents` in the same command as its last edit and ends only when the last line is `documents ok (<seconds> s)`. A finding the command prints is the documenter's to fix. Step 3 then runs `make check` after it. |
| `reviewer` | *Role*, `### Documents` | A checklist item of every review whose diff changes a document the documenter may write. It reads each changed document against the code on the branch. A claim it cannot find in the code, or that the code contradicts, is a finding; so is a command shown with neither a runnable example nor a marked example that names its real run. The item holds in `docs-review` too. |
| `intake` | *Stage* step 4 | A docs criterion names what the reader must know afterwards. One that dictates the sentences (quoted text, a paragraph to paste) is a question, and the agent ends with `question`. |

These rules do not change the other stages, the allowed decisions or the opencode runtime.

### The settings

[settings.json](../../agents/settings.json) is the permissions and environment every agent run shares. A test compares the file with the expected document, so any change is a deliberate edit of both.

- It allows the file tools, `uv run`, `uv sync`, `make`, `factory-check-story` and the read-only git commands `status`, `diff`, `log`, `show` and `rev-parse`.
- It denies `git add` and `git commit`: the agent leaves its changes in the working tree and the factory makes the result commit. The agents' `## Rules` say "You do not commit either", and a denied command is refused by the runtime where an unlisted one would ask for a permission nobody can give.
- It also denies `git push`, `checkout`, `switch`, `merge`, `pull`, `rebase`, `reset`, `branch -D`, `gh` and `rm -rf`.
- `factory-check-story` is the only `factory-` command allowed: an agent may not run `factory-run`, `factory-watch` or `factory-bill`.
- The environment sets `CLAUDE_CODE_FORK_SUBAGENT` to `0`.

### The template

[operator/template/](../../operator/template/) is what a new project starts from, laid out as the project's tree. It holds three files and nothing else.

- [pipeline.yml](../../operator/template/factory/pipeline.yml) (`operator/template/factory/pipeline.yml`), the starting pipeline definition. Copy it to `factory/pipeline.yml` and adjust it. This guide does not copy it, because a copy goes stale with every change of the file: read the file itself.
  - Its roles are the seven agents above. The stages run `intake`, `tests`, `doing`, `review`, `docs`, `smoke-test`, then `approval`; `acceptance` is the acceptance stage.
  - The smoke test's `next` is `approval`, `doing`, `docs` (`round_cap` 3). `docs` is a rework like `doing`, counted against the cap by `decide`, for a finding that is only a slip in a document. R12 in every agent names it (`smoke-test → docs`); the smoke tester's *Stage* steps 5 and 6 choose between `docs` and `doing`, and the documenter's step 1 says what to do on a `docs` round (`tests/agent_files/test_claude_agent_texts_docs_slip.py` pins the texts).
  - It holds the four project commands `check`, `lint`, `test` and `sync` with their `time_limit`s (`sync`, the tools after a checkout, is run by the stage environment and listed by no stage), the seven roles with their write paths, and the stages.
  - The coder's write path is `src/*` only; a project that keeps code elsewhere changes it.
- [CLAUDE.md](../../operator/template/CLAUDE.md) (`operator/template/CLAUDE.md`), the starting rules file of a Python project. It has placeholders in angle brackets for the project's own architecture, test framework and checks. It carries the Python lessons (the `mypy --strict` traps in tests, low-entropy hexadecimal test values, and the time-limit lesson: a test that waits for a time limit gives the process it starts room to start). It also gives the standing leave to move a shared test helper: a helper, constant or fixture that a new test would copy from another story's test module, or that an earlier module still holds as a copy, may be moved to one shared place under `tests/`, and the earlier tests changed to use it, without asking, as long as every earlier test keeps its name and checks the same thing. The tester makes the move, never the coder; any other change to another story's test still needs the human's leave.
- [Makefile](../../operator/template/Makefile) (`operator/template/Makefile`), the project commands of a Python project with a src layout, in the pattern of this repository's own.
  - Its targets are the contract's four, `check`, `lint`, `test` and `sync` (`uv sync --frozen`, between `check` and `lint`, not run by `check`), and the other targets `check` runs: `types`, `layers`, `sast`, `secrets` and `licenses`.
  - Every recipe runs in one shell and ends with `<target>: green (<seconds> s)`. `make test` runs on every core and writes a JUnit report.
  - `make secrets` scans the files changed against `origin/main`, and leaves out `uv.lock`, `.secrets.baseline` and every file ending `.costs.jsonl`: those are the factory's cost records, which hold run metadata and no secret, and their 32-character hexadecimal run ids read to detect-secrets as high-entropy secrets. This repository's `secrets` recipe is the template's, and `tests/agent_files/test_demo_makefile_secrets.py` keeps them equal.
  - `duplicates` is a report outside `check`: it writes similar code and dead code to `.reports/` and counts them, and compares them with no baseline.
  - `mutants` is for a sweep by hand and is never run by a stage: `make mutants FEATURE=<feature id>` runs mutmut over the modules that the feature's story commits on `origin/main` changed, found by the subjects `work item <id>: ...` (or `<id>: ...` after a squash merge). `FEATURE` is taken from an acceptance's branch `work-item/<feature id>-A<number>`.
  - There is no `documents` target.
  - A project fills in two placeholders, `SOURCE` (its package folder) and `LAYERS` (its layers command), and the file's header names the development dependencies the targets need.

The template ships no forms. The story and feature forms (`factory/story-form.md`, `factory/feature-form.md`) are the human's to add to a project made from it. Until `factory/story-form.md` exists, `StoryFormChecker` (see *The story form check* in [pipeline.md](pipeline.md)) stops every stage.

## The write paths

What an agent may write is decided in one place, for the take of a stage. The take copies back only the changed paths the role's write paths allow and no protected path forbids; everything else the agent changed is dropped.

    WritePathService(boundaries).at(stage_start, work_item_path) -> WritePathSettings
    refusal(path, settings) -> str | None
    expand_write_paths(patterns, work_item_path=..., feature_path=...) -> list[str]

- The service is in [write_paths.py](../../src/factory/agents/application/write_paths.py) and the pure rules in [write_paths.py](../../src/factory/agents/domain/write_paths.py) (`factory.agents.domain.write_paths`).
- `WritePathService.at` reads `factory/pipeline.yml` at `stage_start.commit` with `git.show_file` and parses it with `pipeline_reader`. It never reads the work tree's copy, so an agent that rewrites the pipeline definition widens nothing and an invalid rewrite breaks nothing.
- The write paths are those of the role of `stage_start.claim.stage`, expanded; `root` is `boundaries.checkout`; `protected_paths` is `PROTECTED_PATHS`.
- It parses the definition itself and does not use `PipelineLoader`, which stays the one place that loads the definition for the tick. This read checks no installed agent file and raises or clears no stop.
- `ValueError` when `work_item_path` is not `factory/features/<feature directory>/<lifecycle folder>/<work item file name>`. `PipelineDefinitionInvalid`, naming the fault, when the definition is absent or invalid at the commit, when the stage is not in it or has no role, and when a write path holds a placeholder other than the two below.
- Tests: `tests/agents/domain/test_write_paths.py`, `tests/pipeline/application/test_write_paths.py`. A later version of the definition is made with `human.push_file("main", "factory/pipeline.yml", text)` and `checkout.fetch()`.

See also: *The take* in [pipeline.md](pipeline.md).

### Matching and placeholders

- `matches_any(path, patterns)` is `fnmatch.fnmatchcase`: case-sensitive, and `*` also matches `/`.
- `is_writable(path, write_paths)` adds a safety test: an empty path, a path beginning with `/` and a path with a `..` segment are never writable; a name that only starts with two dots is safe. Callers pass normalised repository paths (POSIX separators, no `.` or empty segment, no trailing `/`).
- `expand_write_paths` replaces `{work_item}` with the work item's path and `{feature}` with the feature's path (the work item's path without its last two segments), keeps the order and leaves other patterns as they are.
- Any other `{name}` of lowercase letters and underscores raises `ValueError` naming it; a brace that is no such name (`{Feature}`, `{1}`) stays.

```console
$ uv run python -c "from factory.agents.domain.write_paths import matches_any, is_writable; print(matches_any('src/a/b.py', ['src/*']), matches_any('SRC/a.py', ['src/*']), is_writable('src/../factory/pipeline.yml', ['src/*']), is_writable('src/..x/a.py', ['src/*']))"
...
True False False True
$ uv run python -c "from factory.agents.domain.write_paths import PROTECTED_PATHS as P, matches_any as m; print([m(x, P) for x in ['src/.claude/skills/x/SKILL.md', 'src/.claudex/a', 'docs/CLAUDE.md', 'docs/factory/agents/coder.md']])"
...
[True, False, False, False]
```

### Protected paths and the refusal

`PROTECTED_PATHS` is the engine's fixed list of twelve patterns: `.claude/*`, `*/.claude/*`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, `feature.md`, `*/feature.md` and `<project>/factory/agents/*` (a project's own agents, `PROJECT_AGENTS_DIRECTORY` in `factory.shared.domain.paths`).

- No write path can reach them, and a project cannot change the list.
- The last pattern reaches subfolders too; a folder that only starts with `agents`, and an agents folder below another folder, are not protected.
- A `.claude` segment is protected at any depth and only as a whole segment: `.claudex`, `x.claude` and `agents/agents/coder.md` are not protected, and nor is a path that only ends in `.claude`.
- The patterns are anchored: a `CLAUDE.md` or `pyproject.toml` below another folder is not protected. `docs/project-guide/` is not protected; the documenter keeps it.

`refusal(path, settings)` is the one verdict, `None` when the write is allowed, else a text, checked in this order:

1. `<path> is not a path inside the checkout.` (unsafe path, as above)
2. `<path> is owned by the human; a change there is a question.` (matches `settings.protected_paths`, even when a write path also matches)
3. `<path> is outside the write paths of this stage.` (matches no write path)

## Reference

Exact detail for the sections above, kept whole.

### Reference: the request and the result

`AgentRunRequest` holds:

- `agent`: an `AgentDefinition` (`name`, `model`, `tools`, `effort` or `None`, `budget_usd` greater than 0, `instructions`). `name` is a `Name` (`factory.shared.domain.identifiers`): lower-case letters, digits and hyphens, starting with a letter.
- `prompt`, `time_limit` (greater than zero) and `working_directory` (absolute).
- `allowed_decisions`: must contain `QUESTION` and have no repeats.
- `environment`: the run's whole environment, `{}` by default.
- `resume_session`: optional. When set, it is not blank and names a session the same runtime made: the run continues it with the request's prompt and budget.

`AgentRunResult` holds `end_reason`, `decision`, `entry`, `duration`, `turns`, `tokens` (`TokenCounts`: `input`, `output`, `cache_read`, `cache_creation`, none negative), `cost_usd`, `permission_denials` and `login`, and also `session` and `limit_wait`.

- `end_reason` is one of `completed`, `no_result`, `time_limit`, `budget`, `died` and `provider_limit`.
- `decision` and `entry` are set exactly when the run is `completed`, and `ok` is true exactly then.
- `login` (`Login = Literal["api_key", "subscription", "none"]`) is the login the run's calls were handed, `None` when the runtime has no login file. Unlike `decision` and `entry` it is set whatever the end reason, and a resumed run's is that of its last call.
- `session` is the runtime's own id of the session the run used, set by both runtimes whatever the end reason (`None` when the runtime never learned one).
- `limit_wait` (a positive `timedelta`) is set only on a `provider_limit` run. A result of any other end reason with a `limit_wait` is refused (`a run that ended by <reason> has no limit_wait`).
- A measure the runtime did not report is `None`, never 0: unknown is unknown.
- A run that dies, reaches its `time_limit`, exhausts its budget or meets a provider's spend limit is a result with an end reason, not an exception. `AgentRuntimeError` is for a runtime that cannot be used at all.

### Reference: the login shell

`LOGIN_SCRIPT` in [agent_launch.py](../../src/factory/agents/adapters/agent_launch.py) is built from the module's constants only (an f-string, so its source holds no `NAME="..."` pair of a secret's name), and runs as the factory's own user.

- With `--api-login <file>` and a file that holds a key (anything left once spaces, tabs, carriage returns and line feeds are removed) it exports `ANTHROPIC_API_KEY`, unsets `CLAUDE_CODE_OAUTH_TOKEN`, prints `factory-login-used: api_key` on standard error and `exec`s the command. The token file is not read.
- Otherwise it unsets `ANTHROPIC_API_KEY`, reads the token file (a missing or empty file, or an empty argument, is no token) and prints `factory-login-used: subscription` or `factory-login-used: none`.
- A file that exists but is not a readable regular file, or holds a byte other than printable ASCII, space, tab, carriage return or line feed, prints `factory-api-login: <reason>` (API file) or `factory-login: <reason>` (token file), with the reason `cannot be read` or `not ASCII text`, and exits 1 without starting the command.
- `LoginFiles(subscription=None, api=None)` is the frozen pair of files. `login_argv(files)` is `[]` for neither, `[/bin/sh, -c, LOGIN_SCRIPT, factory-login, <subscription>]` for the token only, and `[..., factory-login, --api-login, <api>, <subscription or "">]` with an API file.
- `login_used(stderr)` reads the first `factory-login-used:` line (`None` for none or an unknown word). `login_refusal(stderr, files)` gives the API text first, then the token text, else `None`. `without_login(environment)` is the copy without both names.

### Reference: the `claude` call

The arguments, in this order (`<session>` is a new `uuid4` per run):

```text
-p <prompt>  --model <model>  [--effort <effort>]  --tools <tools joined with commas>
--session-id <session>  --append-system-prompt-file <state_directory>/instructions-<session>.md
--permission-mode auto  --permission-prompts none
--strict-mcp-config  --max-budget-usd <budget as plain decimal>  --output-format json  --json-schema <schema>
```

The preflight's `agent-run-probe` makes one call with these flags, so a flag the pinned `claude` rejects stops the machine. The schema asks for an object with `decision` (an enum of `allowed_decisions`, in the request's order) and `entry` (described by `ENTRY_DESCRIPTION`), both required, nothing else.

**End reason**, first rule that applies:

1. `time_limit` when the time limit ended the call (it is killed with its children).
2. `budget` when the reply has `subtype` `error_max_budget_usd`; this is checked right after `time_limit` and before the exit status, because `claude` may exit non-zero on a budget stop.
3. `died` when the exit status is not 0, the output is not a JSON object with a string `subtype` and a boolean `is_error`, or `is_error` is true.
4. `completed` when `structured_output` has a `decision` from `allowed_decisions` and a non-blank `entry`.
5. Otherwise `no_result`.

A reply that is an error whose `result` holds the provider limit, or, when no reply parses, a line of standard error that holds it, is `provider_limit`. These rules describe one call; the resume applies them to each call.

**Measures:**

- `duration` is what the factory measured around the call.
- `model_duration` is the reply's `duration_api_ms`, the time the model took (the JSON's `duration_ms` is ignored). It is `None` when the reply lacks the field and after a `time_limit`, and a negative value makes the reply unparsable (`died`).
- `turns`, `cost_usd` (`Decimal(str(total_cost_usd))`), `tokens` and `permission_denials` come from the JSON when it parses, and are `None` for any field it lacks, and for all of them after a `time_limit`.
- `tokens` is known only when both `input_tokens` and `output_tokens` are present; the cache counts default to 0.
- A denial's `detail` is its `tool_input` as JSON with sorted keys; its `path` is the `tool_input`'s `file_path` when that is a string, or else its `notebook_path` when that is a string, otherwise `None` (also when `tool_input` is not an object).
- A reply with the wrong type in a field it carries does not parse and counts as `died`. So does a reply with a negative `num_turns`, token count or `total_cost_usd`: every measure is unknown (`None`); zero is valid. This holds for a budget-stop reply too, which is then not resumed.

**Kill point.** `KillPoint.AGENT_RUN` is reached once, after the last call and the result, whatever the end reason, and not when the call could not be started. A missing executable or an unwritable state directory raises `AgentRuntimeError` naming the cause.

**The provider limit.** `ClaudeCodeRuntime(..., provider_limit=None)` takes a `ProviderLimit` (`factory.agents.domain.provider_limits`: `status` 100 to 599, default `DEFAULT_LIMIT_STATUS` 428, and `message`, a regular expression that must compile). `None` is the default limit. `build_boundaries` passes `settings.provider_limit`, read from `FACTORY_PROVIDER_LIMIT_STATUS` and `FACTORY_PROVIDER_LIMIT_MESSAGE` (`SettingsInvalid` names the variable).

- `limit_in_text(text, limit)` is true when the status stands in the text as a whole number or `message` searches it (`re.search`).
- `named_wait(text)` is the earliest wait the text names (`in|after <n> <unit>`, unit `s`/`sec`/`second(s)`, `m`/`min`/`minute(s)`, `h`/`hour(s)` or none for seconds, or `retry-after[:] <n>` seconds, `<n>` of one to six digits), `None` for none or zero.
- A call ends `provider_limit` only when it did not reach its time limit and was not stopped by its budget, and the limit is in the error reply's `result` (never in `structured_output`) or, with no parsable reply, in a line of standard error.
- The result keeps the reply's measures, as a `died` one does, and its `limit_wait` is `named_wait` of that text. A budget-stop resume that ends `provider_limit` makes the run `provider_limit` with both calls' measures.
- `StallReason` has `provider_limit` too; its sentence is `the provider's spend limit lasted past the waiting ceiling`. Until the application layer waits the limit out, it is a stall like `died`.
- The cost recorder treats the end reason as a run that replied: `denials` and `denied_paths` are set.

**Resuming a session.** Every result's `session` is the id of `--session-id` or, for a request with `resume_session`, that id. Such a request is called with `--resume <resume_session>` in place of `--session-id <new id>`, with the request's prompt and the agent's budget; the run's files are named by a fresh id. A budget stop of that call resumes the same session once. `resumed_result` takes the second call's `session` (the first's when the second has none) and `limit_wait`.

**The budget resume.** When a call ends with `budget`, the same session is resumed once, so that an agent that ran out of money still gives its decision and entry.

- The arguments are the first call's, except `-p` is `FINISH_MESSAGE`, `--session-id <session>` becomes `--resume <session>`, and `--max-budget-usd` is `resume_budget(agent.budget_usd)`: a quarter of the budget, at least `MINIMUM_RESUME_BUDGET` (0.50), rounded half up to cents.
- The run's files are the same ones and are removed when the run ends.
- The resumed call's reply is read by the rules above; if it also ends with `budget`, so does the run. A third call is never made.
- `FINISH_MESSAGE` asks for `question`, not for a decision named `stuck`.
- One `time_limit` counts across the run: the first call may take `request.time_limit`, the resume what is left of it, measured by the factory from the start of `run`. A first call ended by the time limit is never resumed. If nothing is left when the first call ends, the resume is skipped and the run ends as `time_limit`.

**`version()`** runs `<executable> --version` through `run_process` in the process's current directory, with its current environment and the limit `version_time_limit` (`VERSION_TIME_LIMIT`, 30 seconds). It returns the first word of the first non-blank line, so `2.1.289 (Claude Code)` gives `2.1.289`. It raises `AgentRuntimeError` when the call cannot be started, exits non-zero, reaches the limit or prints nothing.

### Reference: a resumed run

`resumed_result` sums the two calls of a resumed run.

- `turns`, `cost_usd` and each of the four token counts are the sums over both calls. A call that reported none adds nothing, and a measure is `None` only when neither call reported it.
- When the resumed call is ended by the time limit, `turns`, `cost_usd` and `tokens` are all `None` (no partial figure: the first call's alone would be one).
- Permission denials are joined, the first call's first.
- `duration` is the factory's own, from the start of `run` to the end of the last call.
- `model_duration` is the sum of both calls' when both are known, the known one when only one is, `None` when neither. A resume ended by the time limit keeps the second call's `None`.

### Reference: the opencode call

**The events.** With `--format json` each stdout line is one event. A line that is no JSON, has no known `type` (`step_start`, `tool_use`, `text`, `step_finish`, `error`), or has a negative number where a count, cost or timestamp belongs, is skipped, and so is a `step_finish` without `cost` or `tokens`. The measures come from the valid lines alone:

- `cost_usd`, `turns` and `tokens` are summed over the `step_finish` events: `input`, `output` (plus `reasoning`), `cache.read` and `cache.write` (a missing part counts 0). Cost is added as `Decimal(str(cost))`.
- `model_duration` is, for each step, the `step_finish` timestamp minus the earlier `step_start` timestamp, minus the spans of the `tool_use` events between them by line order, never below 0. A finish with no earlier start adds 0 and still counts as a turn.
- A `tool_use` whose state is an error that mentions `permission` or `denied`, in any case, is a `PermissionDenial` (tool, sorted input as JSON, and `path` from the input's `filePath` when it is a string).

**The session.** Every result's `session` is the `sessionID` of the first event that carries one, else the request's `resume_session`, else `None`, whatever the end reason, a timeout included. A request with `resume_session` is called with `--session <resume_session>` right before the prompt. A resume (the budget resume, or a request's `resume_session`) is called the same way.

**The end reason.**

- A timeout is `time_limit` with no measures.
- In a container, a call that ends with a status in `CONTAINER_KILL_STATUSES` after a duration of at least its limit is `time_limit` too, with the `session` of its events and the `login` the shell reported. The same kill status before the limit, or any other status after it, is `died`.
- A call the callback stopped is `budget` or `provider_limit`.
- Otherwise a non-zero exit or no `step_finish` is `died`; a valid block is `completed` (with its decision and entry); anything else is `no_result`.
- A stderr line from the login shell is a refusal only when no valid event was printed.

**The budget.** opencode has no budget flag, so the callback keeps it.

- It adds up the `cost` of each `step_finish` of the call (as `Decimal`) while the call streams and stops the call as soon as the sum is greater than the call's budget: the agent's `budget_usd` for the first call, `resume_budget(budget_usd)` for a resume. A sum equal to the budget does not stop it.
- The call ends `budget` with the measures of the events read. A step is only counted when it finishes, so a run may pass its budget by the cost of one step.

**The budget resume.** A first call that ends `budget` with a known session is resumed once: the same words with `--session <session>` before the prompt, `FINISH_MESSAGE` as the prompt, `resume_budget(budget_usd)` as the budget, within what is left of the request's time limit (a resume past it ends the run `time_limit`).

- The run's configuration and rules files are the first call's and are removed only after the resume.
- The result is `resumed_result` of the two calls. A resume that is also over its budget ends the run `budget`, with no third call; one stopped by a limit ends it `provider_limit`.
- With no known session (no event carried a `sessionID`) the budget stop is the run's result.
- The kill point `AGENT_RUN` is reached once, after the whole run.

**The provider limit.** The callback stops the call at once, as `provider_limit`, on an `error` event whose `error.data.statusCode` is the limit's status or whose `error.data.message` holds the limit (`limit_in_text`), and on a line of standard error that holds it.

- It reads no limit from a `text` or `tool_use` event or from any other field, so an agent that writes "428", or a tool whose output holds it, stops nothing.
- An `error` event that is no limit does not stop the call; the call ends by the rules above.
- The result keeps the measures of the events read, the session, and a `limit_wait` of `named_wait` of the message or line (`None` when it names none).
- A limit is never resumed here: waiting it out and continuing the session is the application layer's.
- A time limit that ended the call wins over a recorded stop.

### Reference: the opencode configuration

**The per-run configuration.** `opencode-<run>.json` defines one primary agent, `factory-<name>`, from the same `AgentDefinition` the Claude Code runtime gets from `agents/agents/*.md`:

- `prompt`: the agent file's body, a blank line and `result_instructions(allowed_decisions)`.
- `tools`: all twelve of `OPENCODE_TOOLS`, true for the agent file's tools translated through `TOOL_NAMES` (`Read` is `read`, `Bash` is `bash`, and so on) and false for the rest. A tool in `LEFT_OUT_TOOLS` (`Skill`) turns on no opencode tool and is not refused, so only Claude Code's runs load skills. Every other tool outside `TOOL_NAMES` raises `AgentRuntimeError`.
- `permission`: `edit` allowed and `bash` `{"*": "allow"}` plus a `"deny"` for the pattern of each `Bash(<pattern>)` entry in `permissions.deny` of `settings_file` (the installed `settings.json`). Entries for other tools are not translated. A settings file that cannot be read, or holds no `permissions.deny` list of strings (also when it is no JSON), raises `AgentRuntimeError`; with no `settings_file` only `{"*": "allow"}` is written.
- `autoupdate` false, `share` `disabled` and `snapshot` false, so a run neither updates itself nor uploads or snapshots anything.
- With `provider_file`, the three keys `provider`, `small_model` and `enabled_providers` (`[<provider id>]`), added after `agent`; without it the file has none of them. `disabled_providers` is never written.

**The result block.** opencode has no structured-output flag, so the prompt ends with a fixed block the agent must end its final message with:

```
<factory-result>
decision: <one of: doing, question>
entry:
<the entry>
</factory-result>
```

`parse_result_block(text, allowed_decisions)` reads it strictly from the last `text` event:

- The text must end with `</factory-result>` (trailing spaces and line feeds are ignored; text after it is not).
- The last `<factory-result>` before it opens the block.
- The first line is `decision:` and a word in `allowed_decisions` (spaces around it are fine).
- The second line is exactly `entry:`; `entry: text` there gives `None`.
- The lines after it, joined with line feeds and stripped (line breaks inside the entry stay), are the entry and must not be blank.
- Anything else gives `None`, and the run is `no_result`. There is no repair and no fuzzy match: a reply the factory cannot trust is not a decision.

**The provider file.** [opencode_provider.py](../../src/factory/agents/domain/opencode_provider.py) (`factory.agents.domain.opencode_provider`, pure, no I/O) holds `OpencodeProvider` and `OpencodeModel` (frozen, unknown keys refused), `read_provider(text)` and `provider_configuration(provider)`.

- `read_provider` raises a `ValueError` naming the first field at fault.
- `provider_configuration` gives the `provider` entry (`npm` `@ai-sdk/openai-compatible`, `options.baseURL`, `options.apiKey` as `{env:<api_key_env>}`, and the models with only the groups `name`, `limit`, `cost` that were given) and `small_model`. The key itself is never in the file or the configuration.
- The runtime reads and validates the file at the start of every run, before the state directory is touched (`_provider_keys`). A missing or unreadable file or a `ValueError` is `AgentRuntimeError("cannot use the opencode provider file <path>: <reason>")` and no configuration is written.
- It is read per run, not in `__init__`, so a bad file does not fail `build_boundaries` and a fixed file applies without a restart.
- `_provider_keys` adds `enabled_providers: [provider.id]` to what `provider_configuration` gives (the domain function is unchanged). The merge only adds keys.
- A request whose model is `<id>/<key>` passes unchanged, as any model with a `/` does.
- Why: see *A company's provider for opencode* in [decisions.md](../decisions.md).

**The lockdown switches.** `LOCKDOWN_SWITCHES` in `factory.agents.adapters.opencode_runtime` is `OPENCODE_DISABLE_MODELS_FETCH`, `OPENCODE_DISABLE_AUTOUPDATE` and `OPENCODE_DISABLE_DEFAULT_PLUGINS`, each `1`.

- `_process_request` puts them, with `OPENCODE_CONFIG` and `SWITCHES`, into the one `runtime_environment` dictionary when a provider file is set, so the host launch, `container_launch` and the budget resume all carry the same values.
- They come after the request's environment, so a request's `OPENCODE_DISABLE_MODELS_FETCH=0` is overridden with a provider file and left alone without one.
- Without a provider file the configuration and the environment hold none of the provider keys or switches.
- Why: see *opencode loads and contacts only what the company provider needs* in [decisions.md](../decisions.md).
