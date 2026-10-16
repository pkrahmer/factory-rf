---
stage: doing
pr: 121
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The boundaries of one instance

## Assignment (as of log entry 1)

Build the one function that turns the instance's settings and its token into the `Boundaries` every service works through, and the settings it needs. This completes `build_boundaries`, which F0003 and F0006 left to this feature (questionnaire 1, Q20: the production wiring grows with each feature). The function picks the concrete adapters behind the interfaces, and it answers the open questions of the wiring: the `owner/name` that PyGithub needs comes from the repository URL, the git wrapper gets the identity of the settings and, as its only route to a credential, the credential helper and the shared-group setting as `GitOptions.environment` entries (F0001 decision 7: git ignores system and global configuration, so nothing is set there), the agent runtime keeps its run files under `<state directory>/runs` (that directory is made readable but not writable for the agent by the image story), the agents are read where `FACTORY_CLAUDE_HOME` points (ST4.4), and the token is read once from the file `FACTORY_TOKEN_FILE` names. This story covers the wiring half of ST4.4 and implements R25 and the factory-process half of R33 (the token reaches PyGithub from the factory process and git through the helper, which the token story builds). The process that runs the boundaries is the next story; nothing here starts a tick. `Boundaries` gains the field `settings`, the one place the services read the instance's settings from: the image story reads the image identity from it, the agent-user story the agent user.

## Interface

`src/factory/domain/settings.py` (extends the module)

```python
AGENT_HOME_DEFAULT = Path("/home/agent/.claude")
AGENT_HOME_VARIABLE = "FACTORY_CLAUDE_HOME"
CLAUDE_EXECUTABLE_VARIABLE = "FACTORY_CLAUDE"
CREDENTIAL_FILE_VARIABLE = "FACTORY_TOKEN_FILE"   # no word `token` in the name: ruff's S105 flags a string assigned to such a name, and `tests/test_process_search.py` allows no `noqa` in `src`
RUNS_DIRECTORY_NAME = "runs"

class InstanceSettings(BaseModel):
    ...
    agent_home: Path = AGENT_HOME_DEFAULT
    claude_executable: str = "claude"
    token_file: Path | None = None            # the value of FACTORY_TOKEN_FILE; missing or blank is None
```

`read_settings` sets `agent_home` from `FACTORY_CLAUDE_HOME`; when that is missing or blank it is `<HOME>/.claude` if `HOME` is set and not blank, else `AGENT_HOME_DEFAULT`. It sets `claude_executable` from `FACTORY_CLAUDE` (missing or blank: `claude`) and `token_file` from `FACTORY_TOKEN_FILE` (`CREDENTIAL_FILE_VARIABLE`; missing or blank: `None`).

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

- `pygithub_service(repository, token)` builds `github.Github(auth=github.Auth.Token(token), lazy=True)` and takes the repository with `get_repo(repository)`, so that construction calls out to nothing (the `lazy` argument of `get_repo` itself is deprecated in PyGithub 2.10), and returns `PyGithubHostingService(<that repository>)`. It is the only code outside the class that touches `github`, and it lives in the module that already imports it.
- `git_environment(helper)` returns exactly these five entries: `GIT_CONFIG_COUNT` = `2`, `GIT_CONFIG_KEY_0` = `credential.helper`, `GIT_CONFIG_VALUE_0` = `helper`, `GIT_CONFIG_KEY_1` = `core.sharedRepository`, `GIT_CONFIG_VALUE_1` = `group`. The first pair is the factory's only route to a credential (the helper reads the token file, see the token story); the second keeps the files git creates in the shared checkout writable for the group of the two users.
- `git_options(settings)` is `GitOptions(identity=settings.git_identity, environment=git_environment())`.
- `repository_name(url)` reads `owner/name` from `https://<host>/<owner>/<name>`, `https://<host>/<owner>/<name>.git`, `git@<host>:<owner>/<name>.git` and `ssh://git@<host>/<owner>/<name>.git`, with or without a trailing `/` or `.git`; `owner` and `name` are made of letters, digits, `-`, `_` and `.`. Any other text, a local path included, raises `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"`.
- `read_hosting_token(path)` returns the content of the file without surrounding whitespace. A `None` path, a missing or unreadable file, and a blank content raise `SettingsInvalid` with `variable == "FACTORY_TOKEN_FILE"`.
- `build_boundaries(settings, token, hosting=None)` returns a `Boundaries` of: `GitCli(settings.checkout, git_options(settings))`; `hosting` when it is given, else `pygithub_service(repository_name(settings.repository_url), token)`; `ClaudeCodeRuntime(settings.claude_executable, settings.state_directory / RUNS_DIRECTORY_NAME)`; `MakeProjectCommands(settings.checkout)`; `build_work_item_reader()` (F0002 decision 13) and `FrontmatterWorkItemWriter()`; `JsonLinesCostRecordReader()` and `JsonLinesCostRecordWriter()`; `RuamelPipelineDefinitionReader()`; `FrontmatterAgentDefinitionReader(settings.agent_home)`; a `SystemClock()`; `TimestampedFactoryLog(<state directory>/factory.log, <that clock>)`; `JsonHealthStatusFile(<state directory>/health.json)`; `checkout=settings.checkout`; `settings=settings`. It starts no process and writes nothing. The token is used for PyGithub only and is kept nowhere else.
- The only construction of `FrontmatterAgentDefinitionReader` in `src/factory` is in `factory.entry.wiring`, and its argument is `settings.agent_home`, so the agents are looked for where `FACTORY_CLAUDE_HOME` points.
- The settings reach the services through `Boundaries.settings` and, where a story names it, as an argument; the wiring passes one and the same object to both, and a service never builds settings of its own.

Tests: `tests/domain/test_settings_boundaries.py`, `tests/application/test_boundaries_settings.py` (a file of its own: `tests/application/test_boundaries.py` is F0003's), `tests/adapters/test_pygithub_service.py`, `tests/entry/test_wiring_boundaries.py`, `tests/test_agent_home_wiring.py` (the search, with `ast`). `build_boundaries` is tested with a `FakeHostingService` given as `hosting` and settings whose checkout, state directory and agent home lie in `tmp_path`; the runtime test uses `write_stand_in` and `read_calls` of `tests/adapters/claude_stand_in.py`.

## Acceptance criteria

1. `read_settings` sets `agent_home` to the value of `FACTORY_CLAUDE_HOME` when it is set, to `<HOME>/.claude` when only `HOME` is set, and to `/home/agent/.claude` when neither is set or both are blank (three cases).
2. `read_settings` sets `claude_executable` to the value of `FACTORY_CLAUDE`, and to `claude` when the variable is missing or blank.
3. `read_settings` sets `token_file` to the path in `FACTORY_TOKEN_FILE`, and to `None` when the variable is missing or blank.
4. `repository_name` reads `owner/project` from `https://github.com/owner/project.git`, `https://github.com/owner/project`, `https://github.com/owner/project/`, `git@github.com:owner/project.git`, `git@github.com:owner/project` and `ssh://git@github.com/owner/project.git`, and `my.org/my_project-2` from `https://github.com/my.org/my_project-2.git`, and `owner/project` from `https://git.example.com/owner/project.git` (any host).
5. `repository_name` raises `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"` for `/srv/project.git`, `https://github.com/project.git`, `https://github.com/a/b/c.git` and `https://github.com/owner/pro*ject.git`.
6. `read_hosting_token` returns `example-value` for a file that holds `example-value` and a newline.
7. `read_hosting_token` raises `SettingsInvalid` naming `FACTORY_TOKEN_FILE` for a `None` path, a missing file, a path that is a directory (it cannot be read as a file) and a file that holds only whitespace.
8. `git_environment()` has exactly the five entries of the Rules with the helper `/usr/local/bin/git-credential-factory`, and `git_environment("/opt/other-helper")` has the same entries with that helper as the value of `GIT_CONFIG_VALUE_0`.
9. `git_options(settings)` has the identity of `settings.git_identity` and the environment `git_environment()`; with `GIT_USER_NAME=Ann` read into the settings, the identity's name is `Ann`.
10. A `Boundaries` built without `settings` has `settings is None`, and `dataclasses.replace(boundaries, settings=settings)` returns a `Boundaries` holding those settings.
11. `build_boundaries(settings, "example-value", hosting=fake)` returns a `Boundaries` whose `hosting` is that fake, whose `checkout` is `settings.checkout` and whose `settings` is `settings`.
12. Its `git` is a `GitCli`, its `agent_runtime` a `ClaudeCodeRuntime`, its `project_commands` a `MakeProjectCommands`, its `work_item_reader` a `FrontmatterWorkItemReader`, its `work_item_writer` a `FrontmatterWorkItemWriter`, its `cost_reader` a `JsonLinesCostRecordReader`, its `cost_writer` a `JsonLinesCostRecordWriter`, its `pipeline_reader` a `RuamelPipelineDefinitionReader`, its `agent_definitions` a `FrontmatterAgentDefinitionReader`, its `clock` a `SystemClock`, its `log` a `TimestampedFactoryLog` and its `health` a `JsonHealthStatusFile` (R5, R6: the concrete tools are picked here and nowhere else); the state directory and the checkout, which do not exist before the call, still do not exist after it (nothing is written).
13. Its `git` runs with `git_options(settings)`: for settings whose checkout is a clone of the `remote` fixture and whose `git_identity` is `GitIdentity(name="Ann", email="ann@example.invalid")`, a `pre-commit` hook written into that clone that records its environment sees, during `boundaries.git.commit`, `GIT_AUTHOR_NAME=Ann`, `GIT_CONFIG_KEY_0=credential.helper`, `GIT_CONFIG_VALUE_0=/usr/local/bin/git-credential-factory` and `GIT_CONFIG_VALUE_1=group`.
14. Its `project_commands` run in `settings.checkout`: with a `Makefile` in the checkout whose target `lint` is `@pwd`, `boundaries.project_commands.run("lint", time_limit=timedelta(seconds=30))` has the `last_line` `str(settings.checkout)`.
15. Its `agent_definitions.names()` lists the agents installed under `settings.agent_home` and not those under the test's own `HOME` (ST4.4, the wiring half).
16. A search with `ast` over `src/factory` finds exactly one call of `FrontmatterAgentDefinitionReader(...)`, in `factory.entry.wiring`, and its argument is `settings.agent_home`.
17. Its log and its health file lie under the state directory: after `boundaries.log.line("x")` the file `<state directory>/factory.log` ends with a line that ends in ` x`, and after `boundaries.health.write(HealthStatus())` the file `<state directory>/health.json` exists.
18. Its agent runtime keeps the files of a run under `<state directory>/runs`: with `claude_executable` set to the stand-in, one `run` makes the stand-in see an instructions file whose parent directory is `<state directory>/runs`.
19. `build_boundaries` without `hosting`, for settings whose repository URL gives no `owner/name` (`/srv/project.git`), raises `SettingsInvalid` naming `FACTORY_REPOSITORY_URL` before anything is started.
20. `build_boundaries(settings, "example-value")` without `hosting`, for the URL `https://github.com/owner/project.git`, returns a `Boundaries` whose `hosting` is a `PyGithubHostingService`, makes no request (the test has no network) and hands PyGithub the repository `owner/project`: with `github.Github.get_repo` wrapped through `monkeypatch` by a recorder that calls the original, `get_repo` is called once, with `owner/project`.
21. `pygithub_service("owner/project", "example-value")` returns a `PyGithubHostingService` and makes no request (the test has no network, so a request would raise); with `github.Github.__init__` and `github.Github.get_repo` wrapped through `monkeypatch` by recorders that call the originals, one `Github` is built, with `lazy=True` and an `auth` whose `token` is `example-value`, and `get_repo` is called once, with `owner/project`.
22. make check stays green.
23. docs: `docs/operator-guide.md` names the variables `FACTORY_CLAUDE_HOME` (where the agents are installed), `FACTORY_CLAUDE` (the agent runtime's executable) and `FACTORY_TOKEN_FILE`, and says that the token is read once from that file; `docs/project-guide.md` describes `build_boundaries(settings, token)` as the one place that picks the concrete adapters, with the components it builds; `docs/decisions.md` records why git gets its credential helper and the shared-group setting through `GitOptions.environment` and not through git configuration (F0001 decision 7) and why the settings reach the services through one object.

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
2. intake: accepted
   - Interface: names concrete modules and signatures (settings.py, boundaries.py, pygithub_hosting.py, wiring.py). The rules fix the five git environment entries, the accepted URL forms, the `SettingsInvalid` variable names and the components `build_boundaries` builds.
   - Criteria: each can be tested by one test function. Every rule has a criterion for its failing side. URLs: criterion 5. Token: criterion 7 (None, missing, directory, whitespace-only). `build_boundaries` without a repository name: criterion 19. The `HOME` fallback and the blank cases are in criterion 1, and the blank/missing cases of `FACTORY_CLAUDE` and `FACTORY_TOKEN_FILE` in criteria 2 and 3. Every comment-stated behaviour has one: the defaults, the `settings` default of None (10), the `lazy` construction (20, 21) and "writes nothing" (12).
   - Demo: all three commands can be run and each Expect line can be checked against the printed output.
   - Architecture: the concrete adapters are picked only in `factory.entry.wiring`, the PyGithub call stays in the adapter module, and the settings model stays in domain. Criterion 16 enforces the single construction of the agent reader. This matches the layer rules and R5/R6.
   - Scope: within F0010 "The boundaries of the instance" and F0010 decisions 3, 18 and 34. Nothing is in Out of scope.
   - Noted, not a question: F0010 decision 18 mentions a default token path, `/run/secrets/hosting-token`. This story's Interface gives `token_file` the default None, so I took the story as authoritative; a later story (S0004 or S0013) can add the default.
3. tester: Wrote the red tests for every criterion. Each test checks the Interface as specified. Limits are parametrized on both sides, including the blank and missing cases of each variable.

   - criterion 1: tests/domain/test_settings_boundaries.py::test_agent_home_comes_from_its_variable_then_home_then_the_default (variable set, alone and alongside HOME; only HOME, also with the variable blank; neither set; both blank)
   - criterion 2: tests/domain/test_settings_boundaries.py::test_claude_executable_comes_from_its_variable_or_is_claude
   - criterion 3: tests/domain/test_settings_boundaries.py::test_token_file_comes_from_its_variable_or_is_none
   - criterion 4: tests/entry/test_wiring_boundaries.py::test_repository_name_is_read_from_the_url
   - criterion 5: tests/entry/test_wiring_boundaries.py::test_a_url_without_owner_and_name_is_refused
   - criterion 6: tests/entry/test_wiring_boundaries.py::test_the_hosting_token_is_the_file_content_without_surrounding_whitespace
   - criterion 7: tests/entry/test_wiring_boundaries.py::test_a_hosting_token_that_cannot_be_read_is_refused (None, missing, directory, whitespace)
   - criterion 8: tests/entry/test_wiring_boundaries.py::test_git_environment_gives_the_credential_helper_and_the_shared_group
   - criterion 9: tests/entry/test_wiring_boundaries.py::test_git_options_carry_the_settings_identity_and_the_git_environment
   - criterion 10: tests/application/test_boundaries_settings.py::test_boundaries_hold_no_settings_until_given_them
   - criterion 11: tests/entry/test_wiring_boundaries.py::test_build_boundaries_uses_the_given_hosting_checkout_and_settings
   - criterion 12: tests/entry/test_wiring_boundaries.py::test_build_boundaries_picks_the_concrete_adapters_and_writes_nothing
   - criterion 13: tests/entry/test_wiring_boundaries.py::test_the_built_git_runs_with_the_git_options_of_the_settings (a pre-commit hook in a clone of `remote` writes its environment to a JSON file in tmp_path)
   - criterion 14: tests/entry/test_wiring_boundaries.py::test_the_built_project_commands_run_in_the_checkout
   - criterion 15: tests/entry/test_wiring_boundaries.py::test_the_built_agent_definitions_are_read_from_the_agent_home (HOME is set by monkeypatch to a home that has another agent)
   - criterion 16: tests/test_agent_home_wiring.py::test_the_agent_definition_reader_is_built_once_from_the_settings_agent_home (uses `source_search.modules` and `ast`)
   - criterion 17: tests/entry/test_wiring_boundaries.py::test_the_built_log_and_health_file_lie_in_the_state_directory (the test creates the state directory first)
   - criterion 18: tests/entry/test_wiring_boundaries.py::test_the_built_agent_runtime_keeps_its_run_files_under_runs. The instructions file is found as the file the stand-in saw whose content is the agent's instructions. It is not found by its file name, which is an implementation detail.
   - criterion 19: tests/entry/test_wiring_boundaries.py::test_build_boundaries_refuses_a_url_without_owner_and_name
   - criterion 20: tests/entry/test_wiring_boundaries.py::test_build_boundaries_without_hosting_hands_pygithub_the_repository
   - criterion 21: tests/adapters/test_pygithub_service.py::test_pygithub_service_is_built_lazily_for_the_repository_and_token

   Files created: tests/domain/test_settings_boundaries.py, tests/application/test_boundaries_settings.py, tests/adapters/test_pygithub_service.py, tests/entry/test_wiring_boundaries.py, tests/test_agent_home_wiring.py.

   Modules the runner could not import (collection errors):
   - tests/adapters/test_pygithub_service.py: the name `pygithub_service` is missing from `factory.adapters.pygithub_hosting`.
   - tests/entry/test_wiring_boundaries.py: `build_boundaries`, `git_environment`, `git_options`, `read_hosting_token` and `repository_name` are missing from `factory.entry.wiring`.

   The domain, application and ast-search tests do collect, and they will fail on the missing fields and the missing reader construction. `make lint` is green.

   Things for the coder to know:
   - ruff's S105 flags a string literal assigned to or compared with a name containing `token`. The tests therefore hold the token value in a constant named `CREDENTIAL`.
   - The settings fixture uses `tmp_path.resolve()`, so that `pwd` in criterion 14 prints the same path as `settings.checkout`.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
