---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 460
comments_read: [6418348227, 6418462516, 6418969803]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-10-26T14:48:57.518523Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T14:18:28.749276Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T14:18:28.755146Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-26T14:18:48.497325Z'
  stage: intake
  run: db594303457849ce9eb2a82c2238888e
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-26T14:21:09.837031Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-26T14:21:27.621805Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-26T14:21:47.781262Z'
  stage: intake
  run: bb2b6e5621404ff9aeab9956d8053a4c
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-26T14:22:09.099612Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-26T14:23:28.213287Z'
  stage: tests
  run: 6217ea9dd2cc4b08ade6ea7a2e915f5a
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-26T14:25:49.020811Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-26T14:26:06.902604Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-10-26T14:39:39.626247Z'
  stage: tests
  run: 9b9dc4d01b3b4bbc9cfbde06166bd4e3
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-26T14:40:00.613826Z'
  stage: doing
- number: 13
  speaker: coder
  kind: question
  at: '2026-10-26T14:45:32.948689Z'
  stage: doing
  run: cc543d01425d4651bae6e41d0db5e8b5
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-10-26T14:47:54.472451Z'
  stage: doing
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-26T14:48:12.590472Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-10-26T14:48:36.680277Z'
  stage: doing
  run: 975890c0fc7f4e0682737ff87825b4d0
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-26T14:48:57.518523Z'
  stage: tests
---

# The containers pass the environment names the operator lists and trust the operator's CA bundle

## Description

Every container the factory starts gets a closed environment: the agent's request is scrubbed to six names (`ALLOWED_ENVIRONMENT_NAMES`), the sync container gets `SYNC_ENVIRONMENT` and the check containers `CHECK_ENVIRONMENT`, and the factory's own environment reaches none of them. Behind a company proxy a container needs `HTTPS_PROXY`, `NO_PROXY`, a package mirror (`UV_INDEX_URL`, `NPM_CONFIG_REGISTRY`) and the company's CA certificate, and today none can be given. This story adds two settings. `FACTORY_CONTAINER_ENV` is a comma-separated list of environment variable names; each name that the factory's own environment holds is passed, with its value, into the agent, sync and check containers. `FACTORY_CA_BUNDLE` is the absolute path of a PEM file on the machine; it is mounted read-only into the same containers at its own path and named by `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE`. The allow-list stays closed for every other name, and the login names stay as they are (`without_login` still removes them). Unchanged: with neither setting the containers' command lines and environments are as today; the dataset, the take and the checks' rules; the hosting token, which no container gets. Left to later stories: the file for the operator's settings (S0003).

## Interface

`factory.domain.settings` (domain): constants `CONTAINER_ENV_VARIABLE = "FACTORY_CONTAINER_ENV"` and `CA_BUNDLE_VARIABLE = "FACTORY_CA_BUNDLE"`, and the fields `container_env: tuple[str, ...] = ()` and `ca_bundle: Path | None = None` of `InstanceSettings`.

- `container_env`: the value is split at commas, each part stripped, blank parts left out, duplicates refused (`SettingsInvalid(FACTORY_CONTAINER_ENV, "names <name> twice")`). Each name matches `[A-Za-z_][A-Za-z0-9_]*` or is `SettingsInvalid(FACTORY_CONTAINER_ENV, "holds <name>, which is not a variable name")`. A name in `RESERVED_CONTAINER_NAMES` (exactly `HOME`, `ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, `OPENCODE_CONFIG`, `GIT_ASKPASS` and every name that starts with `FACTORY_`) is `SettingsInvalid(FACTORY_CONTAINER_ENV, "holds <name>, which the factory sets itself")`. Unset or blank is `()`.
- `ca_bundle`: unset or blank is `None`; a relative path is `SettingsInvalid(FACTORY_CA_BUNDLE, "is not an absolute path")`. The model validator refuses a relative path with a `ValidationError`.

`factory.domain.containers` (domain): `def extra_environment(settings: InstanceSettings, source: Mapping[str, str]) -> dict[str, str]`: for each name of `settings.container_env`, in order, `source[name]` when present, nothing otherwise; then, when `settings.ca_bundle` is set, `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE`, each the bundle's path as text. A name that appears twice in the result keeps the later value.

`factory.adapters.agent_launch` (adapters): `container_launch(..., files=...)` already mounts `files` read-only at their own paths; the runtimes add `settings.ca_bundle` to `files` and the result of `extra_environment` to `run_environment`'s runtime part. `without_login` still removes the two login names afterwards.

`factory.application.stage_environment` (application): `ContainerEnvironment` gives the sync container `{**extra, **SYNC_ENVIRONMENT}` (the constants win) and mounts the bundle read-only; `factory.adapters.make_commands.ContainerMakeCommands` does the same for the check containers (`{**extra, **CHECK_ENVIRONMENT}`). Both take the extras and the bundle path as constructor keywords with the defaults `{}` and `None`.

`factory.entry.wiring` (entry): `build_boundaries` computes `extra_environment(settings, os.environ)` once and hands the extras and the bundle to the two runtimes, the container environment and `ContainerMakeCommands`.

Tests (the tester writes them): `tests/domain/test_settings_container_env.py`, `tests/domain/test_container_extra_environment.py`, `tests/adapters/test_agent_launch_extra.py`, `tests/application/test_container_environment_extra.py`, `tests/adapters/test_make_commands_extra.py`, `tests/entry/test_wiring_container_extra.py`.

## Acceptance criteria

1. With neither setting, the words and the environment of the agent, sync and check containers are those of today (rows for the three, comparing with the existing constants).
2. `FACTORY_CONTAINER_ENV` is read, rows of one parametrized test: unset, blank and `" , "` give `()`; `HTTPS_PROXY,NO_PROXY` gives both in order; `A,A` is refused as `names A twice`; `1X` and `A-B` are refused as not a variable name; `HOME`, `ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, `OPENCODE_CONFIG`, `GIT_ASKPASS` and `FACTORY_TOKEN_FILE` are refused as set by the factory; `FACTORYX` is accepted.
3. `FACTORY_CA_BUNDLE` is read: unset and blank give `None`, `/etc/ca.pem` that path, `ca.pem` is refused as not absolute; `InstanceSettings(ca_bundle=Path("ca.pem"))` is a `ValidationError`.
4. `extra_environment` returns the listed names that `source` holds, in order, skips a name `source` lacks, and with a bundle adds the three variables with the path; with nothing set it is `{}`; with `container_env=("SSL_CERT_FILE",)`, the source holding a value for it and `ca_bundle=/etc/ca.pem`, `SSL_CERT_FILE` is `/etc/ca.pem` (the bundle's variable wins over a listed name of the same name).
5. The agent's container: with `container_env=("HTTPS_PROXY",)` in the source environment, the launch's `--env` words hold `HTTPS_PROXY=<value>`; a name outside the list that the source holds is absent; `ANTHROPIC_API_KEY` in the request's environment is still removed. With a bundle, the launch mounts it `:ro` at its own path and holds the three variables. Both runtimes, rows of one test.
6. The sync container and the check containers hold the extra names and the bundle mount (`:ro`) exactly as in criterion 5, and every word before and after them is unchanged. A row with `FACTORY_CONTAINER_ENV=PATH` and a host value for `PATH` leaves the `PATH` of the sync and of the check containers as `SYNC_ENVIRONMENT` and `CHECK_ENVIRONMENT` give it.
7. `build_boundaries` with both settings gives runtimes, a container environment and project commands that carry them (read from the `FakeContainerRuns` calls of one stage); the hosting token is in no container's environment.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`: the two variables in the configuration table and a subsection *Behind a proxy* (the proxy and mirror names, the CA bundle and its mounts, the reserved names; that the bundle must hold the public certificates beside the company's, because `SSL_CERT_FILE` replaces Python's own list; and that `vm/setup.sh` and the stage image's build need the proxy in their own environment). `docs/project-guide/stage-environment.md`, *The podman adapter* and *The container environment*: the extras. `docs/project-guide/agents.md`, *Calls in a container*: the same sentence. `docs/decisions.md`: an entry *The containers' environment stays closed except for the operator's list*, from the feature's decisions 6 and 7. `README.md`: none.

## Smoke test

```bash
uv run python -c "
from pathlib import Path
from factory.domain.containers import extra_environment
from factory.domain.settings import InstanceSettings
settings = InstanceSettings(container_env=('HTTPS_PROXY', 'MISSING'), ca_bundle=Path('/etc/ca.pem'))
print(sorted(extra_environment(settings, {'HTTPS_PROXY': 'http://p.example.invalid:3128', 'OTHER': 'x'})))
"
```
Expect: `['HTTPS_PROXY', 'NODE_EXTRA_CA_CERTS', 'REQUESTS_CA_BUNDLE', 'SSL_CERT_FILE']`

```bash
FACTORY_CONTAINER_ENV=HOME uv run python -c "
from factory.domain.settings import read_settings
import os
try:
    read_settings(os.environ)
except Exception as error:
    print(type(error).__name__)
"
```
Expect: `SettingsInvalid`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: 1. Interface, `extra_environment`: "A name that appears twice in the result keeps the later value" has no criterion. Criterion 4 covers the listed names, the skipped name, the bundle and the empty case, but not a listed name such as `SSL_CERT_FILE` that the bundle's three variables then override. I would add to criterion 4 a row: `container_env=("SSL_CERT_FILE",)`, the source holds a value, `ca_bundle=/etc/ca.pem` gives `SSL_CERT_FILE=/etc/ca.pem`. Do you want that?
   2. Interface, `ContainerEnvironment` and `ContainerMakeCommands`: `{**SYNC_ENVIRONMENT, **extra}` and `{**CHECK_ENVIRONMENT, **extra}` mean an extra name overrides a constant of the same name, but no criterion tests that. Criterion 6 only says the other words are unchanged. I would add to criterion 6: an extra whose name is also in `SYNC_ENVIRONMENT` or `CHECK_ENVIRONMENT` (taking a name from the constant) wins in the container. Or should the constants win, which would change the Interface? I would choose the extra wins, with the criterion.
   3. Criterion 5 and the Interface for the agent's container: the extras are added to "`run_environment`'s runtime part", and `without_login` runs afterwards. `container_env` refuses the login names, so only the request's own `ANTHROPIC_API_KEY` is tested. Is that enough? I would accept it. This is not a blocker.
   4. Criterion 2: the refusal of a name that starts with `FACTORY_` is tested only with `FACTORY_TOKEN_FILE`. Both sides are covered by `FACTORYX`. This is fine and needs no change.

   Format check passed. The smoke tests are runnable. Neither runs pytest. Both `Expect:` lines can be checked against the output. The architecture and scope fit the feature's S0002 entry. Questions 1 and 2 must be answered before this can be accepted.
4. 2026-10-26 human: 1. Yes, add that row to criterion 4: the bundle's variable wins over a listed name of the same name.
   2. The constants win, not the extra: the factory's own `PATH` and `HOME` in a container must not come from the host. The Interface becomes `{**extra, **SYNC_ENVIRONMENT}` and `{**extra, **CHECK_ENVIRONMENT}`; add to criterion 6 a row where `FACTORY_CONTAINER_ENV=PATH` with a host value leaves the sync and check containers' `PATH` as the constant gives it.
   3. Accepted as it is.
   4. Fine, no change.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: concrete modules and signatures (`factory.domain.settings` constants and fields, `extra_environment(settings, source)`, agent_launch, `ContainerEnvironment`, `ContainerMakeCommands`, `build_boundaries`). Carried in from journal entry 4, answer 2: the Interface now reads `{**extra, **SYNC_ENVIRONMENT}` and `{**extra, **CHECK_ENVIRONMENT}`, so the constants win.
   - Criteria: each is testable by one parametrized test. Every rule has both sides: names (duplicate, invalid, reserved, `FACTORYX` accepted), absolute and relative bundle paths, a listed name the source lacks, `ANTHROPIC_API_KEY` still removed. Carried in from entry 4: a row in criterion 4 (the bundle's `SSL_CERT_FILE` wins over a listed `SSL_CERT_FILE`) and a row in criterion 6 (`FACTORY_CONTAINER_ENV=PATH` leaves the sync and check containers' `PATH` as the constants give it). Answers 3 and 4 needed no change.
   - Smoke test: both commands are runnable and neither runs pytest. Each `Expect:` line can be checked against the output.
   - Architecture: pure rules in domain, mounts and environment in adapters and application, wiring only in entry. This matches the layers in CLAUDE.md.
   - Scope: within the feature's S0002 entry and decisions 6 and 7. S0003 and the provider file are not touched, and no test of another story is changed.
7. factory: started tests as vm.
8. tester: I stopped partway through. The Interface doesn't give the constructor keywords that criteria 5, 6 and 7 must call, so I can't write those tests without guessing.

   The question: the Interface says `ContainerEnvironment` and `ContainerMakeCommands` "take the extras and the bundle path as constructor keywords with the defaults `{}` and `None`", but it does not name the keywords. It also says the runtimes add `settings.ca_bundle` and `extra_environment`'s result, and that `build_boundaries` "hands the extras and the bundle to the two runtimes", without saying how `ClaudeCodeRuntime` and `OpenCodeRuntime` receive them. Their constructors take neither settings nor such keywords today. My tests for criteria 5 and 6 build these classes directly, so they need the names. The options I see:
     a) Use the same two keywords on all four classes: `extra_environment: Mapping[str, str] = {}` and `ca_bundle: Path | None = None`. This works on `ClaudeCodeRuntime`, `OpenCodeRuntime`, `ContainerEnvironment` and `ContainerMakeCommands`.
     b) Hand the runtimes the whole `InstanceSettings` plus the source environment, and give only the two container classes the keywords from (a).
     c) Other names of your choosing.
   I would choose (a). It matches the defaults the Interface already gives, keeps the runtimes free of the settings model, and lets `build_boundaries` compute the extras once as the Interface says. With your answer, the Interface should name the keywords for all four classes.

   Done so far. These test files are left in the working tree for the next run:
   - criterion 2: tests/domain/test_settings_container_env.py::test_the_container_env_setting_is_read_as_a_list_of_names
   - criterion 3: tests/domain/test_settings_container_env.py::test_the_ca_bundle_setting_is_read_as_an_absolute_path and ::test_the_settings_model_refuses_a_relative_ca_bundle
   - criterion 4: tests/domain/test_container_extra_environment.py::test_the_extra_environment_holds_the_listed_names_and_the_bundle (with the row where the bundle's `SSL_CERT_FILE` wins over a listed `SSL_CERT_FILE`)

   Still open, waiting on the answer: criteria 1, 5, 6 and 7 (tests/adapters/test_agent_launch_extra.py, tests/application/test_container_environment_extra.py, tests/adapters/test_make_commands_extra.py, tests/entry/test_wiring_container_extra.py). I did not run `make test`; that comes once every test is written. `make lint` is green.

   A side note for the coder, not a blocker: the story's first smoke test calls `InstanceSettings(container_env=..., ca_bundle=...)` without `repository_url` and `instance`, which the model requires today. That command would fail with a `ValidationError` unless the smoke test passes those two fields.
9. 2026-10-26 human: (a): the same two keywords on all four classes, `extra_environment: Mapping[str, str] = {}` and `ca_bundle: Path | None = None`, on `ClaudeCodeRuntime`, `OpencodeRuntime`, `ContainerEnvironment` and `ContainerMakeCommands`; `build_boundaries` computes the extras once and hands both to all four. Read the Interface with those names.

   The side note is right: the first smoke test is corrected by this answer to `InstanceSettings(repository_url='https://github.com/o/n', instance='vm', container_env=('HTTPS_PROXY', 'MISSING'), ca_bundle=Path('/etc/ca.pem'))`; its `Expect:` stays. Run it in that form.
10. factory: started tests as vm.
11. tester: I wrote the tests for criteria 1 to 7, using the keyword names from the human's answer in entry 9 (`extra_environment: Mapping[str, str] = {}`, `ca_bundle: Path | None = None` on `ClaudeCodeRuntime`, `OpencodeRuntime`, `ContainerEnvironment` and `ContainerMakeCommands`). The tests for criteria 2 to 4 are the ones the previous run left in the tree; I did not change them.

    - criterion 1: tests/application/test_container_environment_extra.py::test_with_neither_setting_the_containers_are_those_of_today (rows: agent, sync, check; each compared with `SWITCHES`, `SYNC_ENVIRONMENT` or `CHECK_ENVIRONMENT`, the extras computed by `extra_environment` from settings that set neither)
    - criterion 2: tests/domain/test_settings_container_env.py::test_the_container_env_setting_is_read_as_a_list_of_names
    - criterion 3: tests/domain/test_settings_container_env.py::test_the_ca_bundle_setting_is_read_as_an_absolute_path and ::test_the_settings_model_refuses_a_relative_ca_bundle
    - criterion 4: tests/domain/test_container_extra_environment.py::test_the_extra_environment_holds_the_listed_names_and_the_bundle
    - criterion 5: tests/adapters/test_agent_launch_extra.py::test_the_agent_s_container_holds_the_listed_names_and_the_bundle (claude and opencode × names and bundle)
    - criterion 6: tests/application/test_container_environment_extra.py::test_the_sync_and_check_containers_hold_the_extras_and_the_bundle (sync and check × listed name, bundle, and `PATH` staying the constant)
    - criterion 7: tests/entry/test_wiring_container_extra.py::test_every_container_of_a_stage_carries_both_settings_and_no_hosting_token (claude and opencode)

    Choices the coder should know about:
    - **Where the words come from.** Criteria 5 and 6 speak of `--env` words and a `:ro` mount, so the tests read real podman words. The new shared helper `WordsRuns` in tests/container_extra_support.py records what `PodmanRuns.launch` would build for each call. Agent launches then run through `FakeContainerRuns` as usual. Sync and check runs execute nothing and pass.
    - **Criterion 6 test file.** The check rows sit beside the sync rows in one parametrized test, because they are the sides of one rule. So the Interface's `tests/adapters/test_make_commands_extra.py` was not created.
    - **Criterion 7 mechanism.** `build_boundaries` builds `PodmanRuns`, not `FakeContainerRuns`, so "the `FakeContainerRuns` calls of one stage" cannot be taken literally. The test reads the calls of a recording stand-in `podman` (as tests/entry/test_wiring_stage_environment.py does) for one sync through `stage_environment_of(boundaries).prepare`, one agent run and one `make check` through the project commands. This means `stage_environment_of` must give a container environment that carries both settings.

    Files created this run:
    - tests/container_extra_support.py
    - tests/adapters/test_agent_launch_extra.py
    - tests/application/test_container_environment_extra.py
    - tests/entry/test_wiring_container_extra.py

    Files from the previous run: tests/domain/test_settings_container_env.py and tests/domain/test_container_extra_environment.py.

    `make test` result:
    - Four modules could not be imported: `CA_BUNDLE_VARIABLE` is missing from `factory.domain.settings` (test_settings_container_env), and `extra_environment` is missing from `factory.domain.containers` (test_container_extra_environment, test_agent_launch_extra, test_container_environment_extra).
    - Both rows of the criterion 7 test fail. I did not read their failure output. The likely cause is that `InstanceSettings` does not yet accept `container_env` and `ca_bundle`.
    - I ran `make test` twice, not once: a slip; the second run gave the same result.

    `make lint` is green.

    `lint`: lint: green (0.2 s)
    `test`: ERROR tests/domain/test_settings_container_env.py - ImportError while importing test module '/work/checkout/tests/domain/test_settings_container_env.py'.
12. factory: started doing as vm.
13. coder: I stopped with the code in place, but `make check` is red for two reasons I may not fix myself. Every other target is green: types, layers, sast, secrets, licenses. Every test passes except one row.

    Question 1, a wrong test: in `tests/entry/test_wiring_container_extra.py::test_every_container_of_a_stage_carries_both_settings_and_no_hosting_token[opencode]`, the request's agent has `model="sonnet"`. The settings have no `opencode_models`, so `OpencodeRuntime` refuses the run before any container is launched:
    ```
    tests/entry/test_wiring_container_extra.py:95: in test_every_container_of_a_stage_carries_both_settings_and_no_hosting_token
    src/factory/adapters/opencode_runtime.py:252: in _model
    E   factory.domain.errors.AgentRuntimeError: agent runtime failed: the opencode runtime has no model for sonnet: set FACTORY_OPENCODE_MODELS
    ```
    Options: (a) the tester adds `opencode_models={"sonnet": "anthropic/claude-sonnet"}` to that test's `InstanceSettings`; (b) the request's model becomes a `provider/model` value, which opencode passes through as it is. I would choose (a): it keeps the claude row unchanged.

    Question 2, a lint rule: `ContainerMakeCommands.__init__` now takes six arguments, as the tests pin it (`snapshots, containers, git, checkout=, extra_environment=, ca_bundle=`), and ruff's PLR0913 (max 5) refuses it at `src/factory/adapters/make_commands.py:95`. The two runtimes are exempt only through your per-file ignores in `pyproject.toml`, marked "no noqa in the source". Options: (a) you add `"src/factory/adapters/make_commands.py" = ["PLR0913"]` to `pyproject.toml`, the same way, or allow me to add it; (b) a `# noqa: PLR0913` on the constructor; (c) the extras and the bundle become one DTO argument, which changes the Interface and the tests. I would choose (a).

    What I built:
    - `src/factory/domain/settings.py`: `CONTAINER_ENV_VARIABLE`, `CA_BUNDLE_VARIABLE`, `RESERVED_CONTAINER_NAMES` and the prefix `FACTORY_`; the fields `container_env` and `ca_bundle` (the latter in the absolute-path validator); and `_container_env`, which parses and refuses names.
    - `src/factory/domain/containers.py`: `CA_BUNDLE_NAMES`, `extra_environment`, and `read_only_at_own_path` and `bundle_mounts`. `container_launch` in `src/factory/adapters/agent_launch.py` now uses `read_only_at_own_path` instead of its inline `Mount`.
    - `src/factory/adapters/claude_runtime.py` and `opencode_runtime.py`: the keywords `extra_environment` and `ca_bundle`. In a container, the runtime part becomes `{**extra, **SWITCHES}` (or opencode's own part), so the runtime's names win, and the bundle joins `files`.
    - `src/factory/application/stage_environment.py`: `ContainerEnvironment` takes the same keywords; the sync gets `{**extra, **SYNC_ENVIRONMENT}` and the bundle mount. `src/factory/adapters/make_commands.py`: the check gets `{**extra, **CHECK_ENVIRONMENT}` and the bundle mount.
    - `src/factory/application/boundaries.py`: a new field, `container_extra_environment`, defaulting to `{}`.
    - `src/factory/entry/wiring.py`: `build_boundaries` computes `extra_environment(settings, os.environ)` once and hands it, with the bundle, to the runtime, `ContainerMakeCommands` and `Boundaries`.

    Main choice: `stage_environment_of(boundaries)` is what the stages and the criterion 7 test call. It builds the container environment from the boundaries, so the extras computed once in wiring have to travel there. I put them on `Boundaries` as `container_extra_environment`, and took the bundle from `boundaries.settings.ca_bundle`. I rejected computing `extra_environment(settings, os.environ)` inside `stage_environment_of`: that reads the host environment in the application layer and computes the extras a second time.

    Noticed, not touched: the tester's note in entry 11 that `tests/adapters/test_make_commands_extra.py` was folded into `tests/application/test_container_environment_extra.py`. The refactor pass is not done yet, because `make check` is not green. My own read of the diff found nothing to change so far.
14. 2026-10-26 human: 1. (a): the tester adds `opencode_models={"sonnet": "anthropic/claude-sonnet"}` to that test's `InstanceSettings`; the claude row stays.
    2. (a): `main` now holds `"src/factory/adapters/make_commands.py" = ["PLR0913"]` in `pyproject.toml` (the human's change); it reaches this branch through the merge of `origin/main` at the next stage. No noqa in the source.
15. factory: started doing as vm.
16. coder: The test change from the human's answer in entry 14, point 1: in `tests/entry/test_wiring_container_extra.py::test_every_container_of_a_stage_carries_both_settings_and_no_hosting_token`, give the opencode row's `InstanceSettings` `opencode_models={"sonnet": "anthropic/claude-sonnet"}` and leave the claude row unchanged.

    State of the branch: the code from entry 13 is committed. These are the paths: `src/factory/domain/settings.py`, `src/factory/domain/containers.py`, `src/factory/adapters/agent_launch.py`, `claude_runtime.py`, `opencode_runtime.py`, `make_commands.py`, `src/factory/application/stage_environment.py`, `boundaries.py` and `src/factory/entry/wiring.py`. I changed no code in this run.

    The human's `PLR0913` exemption for `src/factory/adapters/make_commands.py` (entry 14, point 2) is now in `pyproject.toml` on this branch, and `make lint` is green.

    I ran the six test modules of this story together. Only that opencode row fails, the same as before:
    ```
    src/factory/adapters/opencode_runtime.py:252: AgentRuntimeError
    E   factory.domain.errors.AgentRuntimeError: agent runtime failed: the opencode runtime has no model for sonnet: set FACTORY_OPENCODE_MODELS
    ```

    Still open for when the work item comes back: a full `make check` and the refactor pass over my diff. Neither has been done, because the check cannot be green until the test is changed.
17. factory: started tests as vm.
