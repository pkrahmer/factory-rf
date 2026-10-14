# The boundaries of one instance

## Assignment (as of log entry 1)

Build the one function that turns the instance's settings and its token into the `Boundaries` every service works through, and the settings it needs. This completes `build_boundaries`, which F0003 and F0006 left to this feature (questionnaire 1, Q20: the production wiring grows with each feature). The function picks the concrete adapters behind the interfaces, and it answers the open questions of the wiring: the `owner/name` that PyGithub needs comes from the repository URL, the git wrapper gets the identity of the settings and, as its only route to a credential, the credential helper and the shared-group setting as `GitOptions.environment` entries (F0001 decision 7: git ignores system and global configuration, so nothing is set there), the agent runtime keeps its run files under `<state directory>/runs` (that directory is made readable but not writable for the agent by the image story), the agents are read where `FACTORY_CLAUDE_HOME` points (ST4.4), and the token is read once from the file `FACTORY_TOKEN_FILE` names. This story covers the wiring half of ST4.4 and implements R25 and the factory-process half of R33 (the token reaches PyGithub from the factory process and git through the helper, which the token story builds). The process that runs the boundaries is the next story; nothing here starts a tick. `Boundaries` gains the field `settings`, the one place the services read the instance's settings from: the image story reads the image identity from it, the agent-user story the agent user.

## Interface

`src/factory/domain/settings.py` (extends the module)

```python
AGENT_HOME_DEFAULT = Path("/home/agent/.claude")
AGENT_HOME_VARIABLE = "FACTORY_CLAUDE_HOME"
CLAUDE_EXECUTABLE_VARIABLE = "FACTORY_CLAUDE"
TOKEN_FILE_VARIABLE = "FACTORY_TOKEN_FILE"
RUNS_DIRECTORY_NAME = "runs"

class InstanceSettings(BaseModel):
    ...
    agent_home: Path = AGENT_HOME_DEFAULT
    claude_executable: str = "claude"
    token_file: Path | None = None            # the value of FACTORY_TOKEN_FILE; missing or blank is None
```

`read_settings` sets `agent_home` from `FACTORY_CLAUDE_HOME`; when that is missing or blank it is `<HOME>/.claude` if `HOME` is set and not blank, else `AGENT_HOME_DEFAULT`. It sets `claude_executable` from `FACTORY_CLAUDE` (missing or blank: `claude`) and `token_file` from `FACTORY_TOKEN_FILE` (missing or blank: `None`).

`src/factory/application/boundaries.py` (extends `Boundaries`)

```python
@dataclass(frozen=True, kw_only=True)
class Boundaries:
    ...
    settings: InstanceSettings | None = None  # last field, so existing constructions stay valid
```

`src/factory/adapters/pygithub_hosting.py` (extends the module)

```python
def pygithub_service(repository: str, token: str) -> PyGithubHostingService: ...
```

`src/factory/entry/wiring.py` (extends the module)

```python
CREDENTIAL_HELPER = "/usr/local/bin/git-credential-factory"

def git_environment(helper: str = CREDENTIAL_HELPER) -> dict[str, str]: ...
def git_options(settings: InstanceSettings) -> GitOptions: ...
def repository_name(url: str) -> str: ...
def read_hosting_token(path: Path | None) -> str: ...
def build_boundaries(
    settings: InstanceSettings, token: str, *, hosting: HostingService | None = None
) -> Boundaries: ...
```

Rules:

- `pygithub_service(repository, token)` builds `github.Github` with the token as its authentication and takes the repository by name without a request (`Github.get_repo(repository, lazy=True)`), so that construction calls out to nothing, and returns `PyGithubHostingService(<that repository>)`. It is the only code outside the class that touches `github`, and it lives in the module that already imports it.
- `git_environment(helper)` returns exactly these five entries: `GIT_CONFIG_COUNT` = `2`, `GIT_CONFIG_KEY_0` = `credential.helper`, `GIT_CONFIG_VALUE_0` = `helper`, `GIT_CONFIG_KEY_1` = `core.sharedRepository`, `GIT_CONFIG_VALUE_1` = `group`. The first pair is the factory's only route to a credential (the helper reads the token file, see the token story); the second keeps the files git creates in the shared checkout writable for the group of the two users.
- `git_options(settings)` is `GitOptions(identity=settings.git_identity, environment=git_environment())`.
- `repository_name(url)` reads `owner/name` from `https://<host>/<owner>/<name>`, `https://<host>/<owner>/<name>.git`, `git@<host>:<owner>/<name>.git` and `ssh://git@<host>/<owner>/<name>.git`, with or without a trailing `/` or `.git`; `owner` and `name` are made of letters, digits, `-`, `_` and `.`. Any other text, a local path included, raises `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"`.
- `read_hosting_token(path)` returns the content of the file without surrounding whitespace. A `None` path, a missing or unreadable file, and a blank content raise `SettingsInvalid` with `variable == "FACTORY_TOKEN_FILE"`.
- `build_boundaries(settings, token, hosting=None)` returns a `Boundaries` of: `GitCli(settings.checkout, git_options(settings))`; `hosting` when it is given, else `pygithub_service(repository_name(settings.repository_url), token)`; `ClaudeCodeRuntime(settings.claude_executable, settings.state_directory / RUNS_DIRECTORY_NAME)`; `MakeProjectCommands(settings.checkout)`; `FrontmatterWorkItemReader()` and `FrontmatterWorkItemWriter()`; `JsonLinesCostRecordReader()` and `JsonLinesCostRecordWriter()`; `RuamelPipelineDefinitionReader()`; `FrontmatterAgentDefinitionReader(settings.agent_home)`; a `SystemClock()`; `TimestampedFactoryLog(<state directory>/factory.log, <that clock>)`; `JsonHealthStatusFile(<state directory>/health.json)`; `checkout=settings.checkout`; `settings=settings`. It starts no process and writes nothing. The token is used for PyGithub only and is kept nowhere else.
- The only construction of `FrontmatterAgentDefinitionReader` in `src/factory` is in `factory.entry.wiring`, and its argument is `settings.agent_home`, so the agents are looked for where `FACTORY_CLAUDE_HOME` points.
- The settings reach the services through `Boundaries.settings` and, where a story names it, as an argument; the wiring passes one and the same object to both, and a service never builds settings of its own.

Tests: `tests/domain/test_settings_boundaries.py`, `tests/application/test_boundaries_settings.py` (a file of its own: `tests/application/test_boundaries.py` is F0003's), `tests/adapters/test_pygithub_service.py`, `tests/entry/test_wiring_boundaries.py`, `tests/test_agent_home_wiring.py` (the search, with `ast`). `build_boundaries` is tested with a `FakeHostingService` given as `hosting` and settings whose checkout, state directory and agent home lie in `tmp_path`; the runtime test uses `write_stand_in` and `read_calls` of `tests/adapters/claude_stand_in.py`.

## Acceptance criteria

1. `read_settings` sets `agent_home` to the value of `FACTORY_CLAUDE_HOME` when it is set, to `<HOME>/.claude` when only `HOME` is set, and to `/home/agent/.claude` when neither is set or both are blank (three cases).
2. `read_settings` sets `claude_executable` to the value of `FACTORY_CLAUDE`, and to `claude` when the variable is missing or blank.
3. `read_settings` sets `token_file` to the path in `FACTORY_TOKEN_FILE`, and to `None` when the variable is missing or blank.
4. `repository_name` reads `owner/project` from `https://github.com/owner/project.git`, `https://github.com/owner/project`, `git@github.com:owner/project.git` and `ssh://git@github.com/owner/project.git`.
5. `repository_name` raises `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"` for `/srv/project.git`, `https://github.com/project.git` and `https://github.com/a/b/c.git`.
6. `read_hosting_token` returns `example-value` for a file that holds `example-value` and a newline.
7. `read_hosting_token` raises `SettingsInvalid` naming `FACTORY_TOKEN_FILE` for a `None` path, a missing file, and a file that holds only whitespace.
8. `git_environment()` has exactly the five entries of the Rules with the helper `/usr/local/bin/git-credential-factory`, and `git_environment("/tmp/helper")` has the same entries with that helper as the value of `GIT_CONFIG_VALUE_0`.
9. `git_options(settings)` has the identity of `settings.git_identity` and the environment `git_environment()`; with `GIT_USER_NAME=Ann` read into the settings, the identity's name is `Ann`.
10. A `Boundaries` built without `settings` has `settings is None`, and `dataclasses.replace(boundaries, settings=settings)` returns a `Boundaries` holding those settings.
11. `build_boundaries(settings, "example-value", hosting=fake)` returns a `Boundaries` whose `hosting` is that fake, whose `checkout` is `settings.checkout` and whose `settings` is `settings`.
12. Its `git` is a `GitCli`, its `agent_runtime` a `ClaudeCodeRuntime`, its `project_commands` a `MakeProjectCommands`, its `agent_definitions` a `FrontmatterAgentDefinitionReader`, its `log` a `TimestampedFactoryLog` and its `health` a `JsonHealthStatusFile` (R5, R6: the concrete tools are picked here and nowhere else).
13. Its `agent_definitions.names()` lists the agents installed under `settings.agent_home` and not those under the test's own `HOME` (ST4.4, the wiring half).
14. A search with `ast` over `src/factory` finds exactly one call of `FrontmatterAgentDefinitionReader(...)`, in `factory.entry.wiring`, and its argument is `settings.agent_home`.
15. Its log and its health file lie under the state directory: after `boundaries.log.line("x")` the file `<state directory>/factory.log` ends with a line that ends in ` x`, and after `boundaries.health.write(HealthStatus())` the file `<state directory>/health.json` exists.
16. Its agent runtime keeps the files of a run under `<state directory>/runs`: with `claude_executable` set to the stand-in, one `run` makes the stand-in see an instructions file whose parent directory is `<state directory>/runs`.
17. `build_boundaries` without `hosting`, for settings whose repository URL gives no `owner/name` (`/srv/project.git`), raises `SettingsInvalid` naming `FACTORY_REPOSITORY_URL` before anything is started.
18. `pygithub_service("owner/project", "example-value")` returns a `PyGithubHostingService` and makes no request (the test has no network, so a request would raise).
19. make check stays green.
20. docs: `docs/operator-guide.md` names the variables `FACTORY_CLAUDE_HOME` (where the agents are installed), `FACTORY_CLAUDE` (the agent runtime's executable) and `FACTORY_TOKEN_FILE`, and says that the token is read once from that file; `docs/project-guide.md` describes `build_boundaries(settings, token)` as the one place that picks the concrete adapters, with the components it builds; `docs/decisions.md` records why git gets its credential helper and the shared-group setting through `GitOptions.environment` and not through git configuration (F0001 decision 7) and why the settings reach the services through one object.

## Demo

```bash
uv run python -c "
from factory.entry.wiring import repository_name, git_environment
print(repository_name('git@github.com:owner/project.git'))
print(sorted(git_environment('/h')))
"
```
Expect: two lines, `owner/project` and `['GIT_CONFIG_COUNT', 'GIT_CONFIG_KEY_0', 'GIT_CONFIG_KEY_1', 'GIT_CONFIG_VALUE_0', 'GIT_CONFIG_VALUE_1']`.

```bash
uv run python -c "
import tempfile, pathlib
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.settings import read_settings
from factory.entry.wiring import build_boundaries
d = pathlib.Path(tempfile.mkdtemp())
env = {'FACTORY_REPOSITORY_URL': '/srv/project.git', 'FACTORY_INSTANCE': 'factory-1', 'FACTORY_CLAUDE_HOME': str(d)}
b = build_boundaries(read_settings(env), 'example-value', hosting=FakeHostingService())
print(type(b.git).__name__, type(b.agent_runtime).__name__, b.settings.agent_home == d)
"
```
Expect: one line, `GitCli ClaudeCodeRuntime True`.

```bash
uv run python -c "
from factory.domain.settings import read_settings
env = {'FACTORY_REPOSITORY_URL': '/srv/project.git', 'FACTORY_INSTANCE': 'factory-1', 'FACTORY_CLAUDE_HOME': '/srv/agents'}
s = read_settings(env)
print(s.agent_home, s.claude_executable, s.token_file)
"
```
Expect: one line, `/srv/agents claude None`.

## Log (append only)

1. 2026-10-12 human: created.
