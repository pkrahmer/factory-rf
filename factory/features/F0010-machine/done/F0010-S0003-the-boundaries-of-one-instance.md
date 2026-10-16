---
stage: done
pr: 121
blocked: null
comments_seen: 2
round: 1
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
4. coder: Implemented the story in commit da206a3. One test fails because the test itself is wrong, so this is a question, not a hand-off to review.

   Built:
   - `src/factory/domain/settings.py`: adds `agent_home`, `claude_executable`, `token_file` and the constants from the Interface. `read_settings` fills them, falling back from `FACTORY_CLAUDE_HOME` to `<HOME>/.claude` to the default.
   - `src/factory/application/boundaries.py`: `settings: InstanceSettings | None = None`, the last field.
   - `src/factory/adapters/pygithub_hosting.py`: `pygithub_service`, built lazily with `Github(auth=Auth.Token(token), lazy=True).get_repo(...)`.
   - `src/factory/entry/wiring.py`: `CREDENTIAL_HELPER`, `git_environment`, `git_options`, `repository_name` (one full-match regex for the https, scp-like and ssh forms), `read_hosting_token` and `build_boundaries`. `build_boundaries` resolves the hosting service before it builds anything else.

   Status: `make lint` is green. Every new test passes except one. The rest of the suite also passes, with coverage at 99.55%.

   The contradiction: `tests/entry/test_wiring_boundaries.py::test_the_built_agent_runtime_keeps_its_run_files_under_runs` builds `AgentRunRequest(allowed_decisions=["doing"], ...)`. The existing domain rule (`factory/domain/agent_runs.py`, the validator `_question_is_allowed_once_each`) refuses that: "allowed decisions must contain 'question'". The test therefore fails while it is still setting up, before it reaches the code under test. This is not something the implementation can fix.

   Options:
   (a) The tester changes the request in that test to `allowed_decisions=["doing", "question"]`. Nothing else changes, and the reply's `decision: "doing"` stays valid.
   (b) Loosen the domain rule. That would be out of scope and would change established behaviour.

   I recommend (a). If you agree, I will end the next round with `tests` and name exactly that change.

   Refactor step: not done yet. It follows once `make check` is green.
5. human (pull request comment, 2026-10-16): (a): the tester changes the request in `test_the_built_agent_runtime_keeps_its_run_files_under_runs` to `allowed_decisions=["doing", "question"]` and changes nothing else; the domain rule stays. End with `tests` and name exactly that change.
6. coder: The human answered in entry 5, so this round makes no code change and sends the ticket back to the tester.
   - Test change, exactly as the human worded it: in `tests/entry/test_wiring_boundaries.py::test_the_built_agent_runtime_keeps_its_run_files_under_runs`, change the `AgentRunRequest` to use `allowed_decisions=["doing", "question"]` instead of `["doing"]`. Change nothing else. The domain rule in `factory/domain/agent_runs.py` stays as it is.
   - The implementation is already committed in da206a3. When the tester returns the ticket, I will run `make check`, do the refactor step and hand the ticket to review.
   - `## Assignment` is unchanged, because the answer does not change what the task means.
7. tester: tester (approved test change): Made exactly the change the human approved in entry 5 and the coder named in entry 6.
      - `tests/entry/test_wiring_boundaries.py::test_the_built_agent_runtime_keeps_its_run_files_under_runs`: the `AgentRunRequest` now has `allowed_decisions=["doing", "question"]` instead of `["doing"]`. The reason: the domain rule in `factory/domain/agent_runs.py` requires `question`, so the old value made the test fail during setup, before it reached the code under test. The domain rule is unchanged, and nothing else in the test changed.
      - `make test`: green, coverage 99.55%.

   `make lint`: lint: green
   `make test`: test: green
8. coder: The tester made the approved change in entry 7. `make check` now passes with every test, including `test_the_built_agent_runtime_keeps_its_run_files_under_runs`, and coverage is 99.55%. This round added no code. All the work is still in commit da206a3.

   Built:
   - `src/factory/domain/settings.py`: adds the constants from the Interface and the fields `agent_home`, `claude_executable` and `token_file`. `read_settings` fills them. `agent_home` comes from `FACTORY_CLAUDE_HOME`, then from `<HOME>/.claude`, then from `AGENT_HOME_DEFAULT`. A blank variable counts as missing.
   - `src/factory/application/boundaries.py`: adds `settings: InstanceSettings | None = None` as the last field.
   - `src/factory/adapters/pygithub_hosting.py`: adds `pygithub_service`, which builds `github.Github(auth=github.Auth.Token(token), lazy=True).get_repo(repository)`. It sits in the one module that already imports `github`.
   - `src/factory/entry/wiring.py`: adds `CREDENTIAL_HELPER`, `git_environment`, `git_options`, `repository_name`, `read_hosting_token` and `build_boundaries`.

   Main design decisions:
   - `repository_name` uses one regex that must match the whole URL. It covers the https, ssh and `git@host:` forms. The name segment matches as little as possible, so a trailing `.git` and `/` are dropped. I rejected `urllib.parse`. It does not understand `git@host:owner/name`, so it would have needed a second code path.
   - `build_boundaries` resolves the hosting service before it builds anything else. A bad URL therefore fails before any adapter exists (criterion 19).
   - One `SystemClock` is shared between `clock` and the log.

   Refactor step: I read the whole diff (`git diff main...HEAD -- src`) and found nothing to rename, simplify or remove, so there is no refactor commit.

   Noticed, not touched:
   - The file names `factory.log` and `health.json` are literals in `build_boundaries`. No constant for them existed elsewhere, and the Interface names none.
   - Intake noted the default token path from F0010 decision 18 (`/run/secrets/hosting-token`). It is still not implemented: `token_file` defaults to `None`, as the Interface says.

   `make check`: check: green
9. reviewer: Checked the diff against the criteria, the architecture and security, and they hold. Every criterion from 1 to 21 has a test that checks what the criterion says. The failing sides are parametrized: URLs in 5, the token file in 7, and the blank and missing variables in 1 to 3. The coder's entry 8 reports `make check` green. The layers are respected: `github` is still imported only in `factory.adapters.pygithub_hosting`, and the concrete adapters are picked only in `factory.entry.wiring`. There are no secrets, and the error messages name the path but never the token. Review stopped at Quality with one finding:

   1. `src/factory/entry/wiring.py` `read_hosting_token`: this is a second copy of the logic in `src/factory/domain/settings.py` `_image`. Both read a file, strip it, turn an `OSError` into `SettingsInvalid(variable, f"cannot read {path}: {error}")` and turn blank content into `SettingsInvalid(variable, f"{path} is empty")`. CLAUDE.md counts a second copy of an existing helper as a finding. Fix: move that logic into one public domain function in `settings.py`, for example `read_setting_file(variable, path, read_file) -> str`, so that the domain stays pure because the reader is passed in. Make `_image` use it. `read_hosting_token` keeps its `None` check and then calls it with a reader built on `Path.read_text(encoding="utf-8")`. No test changes.
10. coder: Round 1: fixed the one finding from review entry 9, in commit 41e71af. The commit changes no behaviour and touches no tests.
    - `src/factory/domain/settings.py`: new public `read_setting_file(variable, path, read_file) -> str`. It reads the file through the `read_file` it is given, strips the content and raises `SettingsInvalid(variable, ...)` with the same messages as before: `cannot read {path}: {error}` on an `OSError`, `{path} is empty` on blank content. `_image` now calls it with `IMAGE_ID_FILE_VARIABLE`. Because the reader is passed in, the domain stays free of I/O.
    - `src/factory/entry/wiring.py`: `read_hosting_token` keeps its `None` check and then calls `read_setting_file(CREDENTIAL_FILE_VARIABLE, path, _read_utf8)`. `_read_utf8` is a private reader built on `Path.read_text(encoding="utf-8")`.
    - Rejected: a lambda for the reader. A named private function is easier to read and matches the style of the module.
    - `make check`: green, coverage 99.55%.
    - `## Assignment` is unchanged. Nothing else was touched.

    `make check`: check: green
11. reviewer: reviewer (round 1): no findings.
    - Checked the fix in 41e71af for finding 1 of entry 9. `src/factory/domain/settings.py` now has one public `read_setting_file(variable, path, read_file)`. `_image` and `src/factory/entry/wiring.py` `read_hosting_token` both call it. The domain stays free of I/O because the reader is passed in. Both keep the error messages they had before. `read_hosting_token` still checks for a `None` path itself.
    - `_read_utf8` is not a copy of an existing helper. The only similar reader, `_read_text` in `entry/check_story.py`, wraps its error in a different type.
    - The fix touches no tests. Criteria 1–21 are still covered as entry 9 found. The coder's entry 10 reports `make check` green.
    - Read the whole diff `main...HEAD` again: settings, boundaries, the PyGithub adapter, the wiring, and the five test files. Architecture holds: `github` is imported only in the adapter module, and the concrete adapters are picked only in `factory.entry.wiring`. Security holds: no silencing markers, and no error message contains the token. Quality holds: docstrings are present and comments say why. Ticket hygiene holds: the log records the choice of a regex over `urllib.parse`, the Assignment matches what was built, and the docs criterion 23 still describes what the reader needs.
    - Considered and not raised: a token file that is not valid UTF-8 raises `UnicodeDecodeError` rather than `SettingsInvalid`. The Rules list only missing, unreadable and blank files, and the image file behaved this way before this story.
12. documenter: wrote the documentation criterion 23 asks for, and `make check` is green (coverage 99.55%).

    Files changed:
    - `docs/operator-guide.md`, "The instance's settings": added `FACTORY_CLAUDE_HOME`, `FACTORY_CLAUDE` and `FACTORY_TOKEN_FILE` to the table, with their defaults and the fact that a blank value counts as unset. Added how the token is read once and which faults are refused. Added which repository URL forms give `owner/name`. States that no running process reads these variables yet.
    - `docs/project-guide.md`, "Boundaries": the new `settings` field, `build_boundaries(settings, token, hosting=None)` as the one place that picks the concrete adapters with every component it builds, `git_options`, `git_environment`, `repository_name`, `read_hosting_token` and `read_setting_file`, plus the new `InstanceSettings` fields.
    - `docs/decisions.md`: two entries. The first gives why git gets its credential helper and the shared-group setting through `GitOptions.environment` (F0001 decision 7) and not through git configuration, and why `urllib.parse` was rejected for the URL. The second gives why the settings reach the services through `Boundaries.settings`, and records the open item that the default token path (F0010 decision 18) is not implemented.

    Cross-read and found current: the other operator-guide sections on the agent runtime and the settings, the project guide's agent definition reader section, and the README, which does not mention these names.

    I did not run the three Demo commands. I only checked the docs against the diff.

    Findings: none. The code matches the Interface. I noted but did not touch two things. A token file that is not valid UTF-8 raises `UnicodeDecodeError` instead of `SettingsInvalid`, which review already considered and did not raise. The file names `factory.log` and `health.json` are literals in `build_boundaries`.

    `make check`: check: green
13. demo: Ran the three `## Demo` commands from the repository root, exactly as written and in order. All three exited 0.

    Command 1 (`repository_name` and `git_environment`):
    ```
    owner/project
    ['GIT_CONFIG_COUNT', 'GIT_CONFIG_KEY_0', 'GIT_CONFIG_KEY_1', 'GIT_CONFIG_VALUE_0', 'GIT_CONFIG_VALUE_1']
    ```
    Met its Expect: line. Both lines are exactly as expected.

    Command 2 (`build_boundaries` with the fake hosting service):
    ```
    GitCli ClaudeCodeRuntime True
    ```
    Met its Expect: line.

    Command 3 (`read_settings` with `FACTORY_CLAUDE_HOME`):
    ```
    /srv/agents claude None
    ```
    Met its Expect: line.

    Checked against the acceptance criteria: the output agrees with criteria 1, 2 and 3 (with the variables missing, `claude_executable` falls back to `claude` and `token_file` to `None`). It agrees with criterion 4 for the scp form, criterion 8 for the five environment keys, and criteria 11 and 12 for the `GitCli` and `ClaudeCodeRuntime` types and for `settings` being held. Nothing in the demo goes against any criterion. The demo does not cover the other criteria (no network, no state written, hosting through PyGithub); the tests cover those.

    No findings.
14. done (pull request merged); cost: 11 runs, 23.1 min, 91 turns, 274k tokens in (2023k more from cache), 42k out, $3.17
