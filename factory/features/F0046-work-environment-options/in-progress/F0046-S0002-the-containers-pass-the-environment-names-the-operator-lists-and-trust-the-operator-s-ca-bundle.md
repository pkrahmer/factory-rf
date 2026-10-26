---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 460
comments_read: [6418348227]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-10-26T14:22:09.099612Z'
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
