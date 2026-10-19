# The operator chooses the runtime per instance, and the image and the preflight carry opencode

## Description

After S0004 to S0007 the opencode runtime exists, but nothing builds it and the image does not hold opencode. This story lets the operator choose the runtime of an instance with one setting, `FACTORY_AGENT_RUNTIME` (`claude`, the default, or `opencode`), set for the instance's compose calls like `FACTORY_INSTANCE`; the wiring then builds the opencode runtime with the agent user, the write guard's wrapper, the API key's file, the provider limit and the models of `FACTORY_OPENCODE_MODELS`, which maps the agent files' aliases (`opus`, `sonnet`, `haiku`) to opencode's `provider/model` ids. The image installs opencode from npm at a pinned version, beside Claude Code, and sets the pin and the three Anthropic ids. The preflight checks the runtime in force: its executable on the `PATH`, its version against its pin, and for opencode a new item, `opencode`: the executable on the agent run's `PATH`, and a model for every alias the installed agents use. An API key is optional: an operator's own build of opencode may log in through single sign-on with a login it keeps in the agent's home, and whether a run can log in is the probe's to show; the probe's hint names the runtime's own command. An instance without the setting runs exactly as today. The real run on opencode is the human's (the feature's change 6).

## Interface

`factory.domain.settings` (`domain`):

```python
AGENT_RUNTIME_VARIABLE = "FACTORY_AGENT_RUNTIME"
OPENCODE_EXECUTABLE_VARIABLE = "FACTORY_OPENCODE"
OPENCODE_VERSION_VARIABLE = "FACTORY_OPENCODE_VERSION"
OPENCODE_MODELS_VARIABLE = "FACTORY_OPENCODE_MODELS"
AgentRuntimeName = Literal["claude", "opencode"]

class InstanceSettings(BaseModel):
    ...
    agent_runtime: AgentRuntimeName = "claude"         # new, after provider_limit
    opencode_executable: str = "opencode"
    pinned_opencode_version: str | None = None
    opencode_models: dict[str, str] = {}
```

- `read_settings`: `FACTORY_AGENT_RUNTIME` unset or blank gives `claude`; `claude` or `opencode`, with surrounding spaces stripped, gives that; anything else raises `SettingsInvalid` naming the variable with `is neither claude nor opencode`.
- `FACTORY_OPENCODE` unset or blank gives `opencode`; `FACTORY_OPENCODE_VERSION` unset or blank gives `None`.
- `FACTORY_OPENCODE_MODELS` unset or blank gives `{}`; otherwise comma-separated entries `<alias>=<provider>/<model>`, spaces around each part stripped, give the mapping in their order. An entry without `=`, with an empty alias, or whose model has no `/` or an empty side of it raises `SettingsInvalid` naming the variable with `holds <entry>, which is not <alias>=<provider>/<model>`; an alias named twice raises it with `names <alias> twice`.
- `OPENCODE_FOLDERS_VARIABLE = "FACTORY_OPENCODE_FOLDERS"` and `InstanceSettings.opencode_folders: list[str] = []`, last: unset or blank gives `[]`; otherwise comma-separated folders relative to the agent's home, spaces around each stripped, in their order. An entry that is empty, absolute, or has an empty, `.` or `..` segment raises `SettingsInvalid` naming the variable with `holds <entry>, which is not a folder inside the agent's home`.

`factory.entry.wiring` (`entry`):

- `build_boundaries` builds, for `agent_runtime` `opencode`, `OpencodeRuntime(settings.opencode_executable, <state>/runs, models=settings.opencode_models, settings_file=settings.agent_home / "settings.json", sudo_executable=<the sudo which finds>, api_login_file=settings.api_login_file, confine_executable=confine_executable, provider_limit=settings.provider_limit, runtime_folders=(*RUNTIME_FOLDERS, *settings.opencode_folders))`; for `claude`, the Claude Code runtime as today.
- `machine_extras` adds, for `opencode` only, the item `opencode` right after `confinement` and before `agent-run-probe`; for `claude` the extras are those of today, in today's order.

`factory.adapters.opencode_runtime` (`adapters`):

- `OpencodeRuntime.__init__` gains the keyword `runtime_folders: Sequence[str] = RUNTIME_FOLDERS`, last; a run's rules allow `<HOME>/<folder>` for each, in that order, in place of `RUNTIME_FOLDERS` alone (an operator's build may keep its single sign-on login and its state in folders of its own, and refresh the login during a run).

`factory.application.preflight` (`application`):

```python
def opencode_item(settings: InstanceSettings, environment: Mapping[str, str],
                  find: Callable[[str, str], str | None], agent_models: Sequence[str]) -> PreflightItem: ...
def installed_models(boundaries: Boundaries) -> list[str]: ...
```

- `opencode_item` is named `opencode`; it passes without a detail, or fails with its faults joined by `; ` in this order:
  - `<executable> is not on the agent run's PATH <path>` (or `the agent run has no PATH`), as for the wrapper;
  - `no model is set for <alias> in FACTORY_OPENCODE_MODELS`, once for each alias among `agent_models` (a model without `/`) that the mapping lacks, sorted.
- It reads no login file and asks for no API key: an opencode run logs in with the key of `FACTORY_API_LOGIN_FILE` when the file holds one, or with the login the build keeps in the agent's home; the probe's passed detail names the login in force (S0001).
- `installed_models`: the `model` of every installed agent, in the order of the agents' names, each once; `[]` when the agent definitions cannot be read (the item `agents` reports that).
- `MachineChecks.run`: the last of the required tools is the runtime's executable (`claude_executable` for `claude`, `opencode_executable` for `opencode`).
- The version item compares the runtime's version against the pin of the runtime in force; without a pin, its detail names that runtime's variable: `the image does not pin a version: FACTORY_OPENCODE_VERSION is not set` for opencode, today's text for Claude Code.
- `agent_run_probe_item`: a failed probe under opencode says `run <opencode executable> run by hand as <user> to see why` instead of `run claude -p by hand ...`, and gets no token hint; S0001's API hint applies to both runtimes when the probe's login was `api_key`; under opencode, a failed probe whose login was `none` ends its detail with `; the agent runs get no API key: log in once as <user> with the opencode build's own login, or put a key in the file FACTORY_API_LOGIN_FILE names`.

`image/Dockerfile`, `image/compose.yml` (`image`, the coder's):

- After `ARG CLAUDE_CODE_VERSION=2.1.296`: `ARG OPENCODE_VERSION=1.19.3`.
- Right after the Claude Code install: `RUN npm install --global --no-audit --no-fund opencode-ai@${OPENCODE_VERSION}`.
- Before `USER factory`, each its own instruction, with a comment line above: `ENV FACTORY_OPENCODE_VERSION=${OPENCODE_VERSION}` and `ENV FACTORY_OPENCODE_MODELS=opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5`.
- The compose service's `environment` gains, after `FACTORY_INSTANCE`, in this order: `FACTORY_AGENT_RUNTIME: ${FACTORY_AGENT_RUNTIME:-claude}`, `FACTORY_OPENCODE: ${FACTORY_OPENCODE:-opencode}`, `FACTORY_OPENCODE_VERSION: ${FACTORY_OPENCODE_VERSION:-1.19.3}`, `FACTORY_OPENCODE_MODELS: ${FACTORY_OPENCODE_MODELS:-opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5}` and `FACTORY_OPENCODE_FOLDERS: ${FACTORY_OPENCODE_FOLDERS:-}`, so that the operator chooses the opencode build of an instance (its path in the container, its version, its model ids, its folders) and the image's `opencode-ai` is the default; each default equals the image's own value (`OPENCODE_VERSION`, `FACTORY_OPENCODE_MODELS`).

Tests (the tester writes them): `tests/domain/test_settings_agent_runtime.py`, `tests/domain/test_settings_opencode_models.py`, `tests/domain/test_settings_opencode_folders.py`, `tests/adapters/test_opencode_runtime_folders.py` (the wrapper through `build_layout`, `write_confine` and `read_records` of `tests/confine_support.py`), `tests/application/test_opencode_item.py`, `tests/application/test_machine_checks_runtime.py`, `tests/application/test_agent_run_probe_opencode.py`, `tests/entry/test_wiring_opencode.py` (the shared `every_tool` of `tests/wiring_support.py`, imported), `tests/test_opencode_image.py` (the Dockerfile through `tests/dockerfile_support.py`, the compose file as `tests/test_compose.py` reads it). No earlier test changes: the extras, tools and version item of a Claude Code instance stay as they are.

## Acceptance criteria

1. `read_settings` gives `claude` without `FACTORY_AGENT_RUNTIME`, with `""` and with `" "`, `opencode` for `opencode` and for ` opencode `, and raises `SettingsInvalid` naming the variable for `Opencode`, `claude-code` and `both` (rows).
2. `read_settings` gives `opencode` and `None` without `FACTORY_OPENCODE` and `FACTORY_OPENCODE_VERSION`, and `/opt/bin/opencode` and `1.19.3` with them (rows).
3. `FACTORY_OPENCODE_MODELS` `opus=anthropic/claude-opus-5-5, sonnet = anthropic/claude-sonnet-5-5` gives the two entries in order; blank gives `{}`; `opus`, `=anthropic/x`, `opus=anthropic`, `opus=/x`, `opus=anthropic/` and `opus=a/b,opus=c/d` raise `SettingsInvalid` with their texts (rows).
4. `build_boundaries` with `agent_runtime` `opencode` gives an `OpencodeRuntime` whose run of a stand-in (`opencode_executable` set to it, `confine_executable=None`) gets the mapped model, the installed `settings.json`'s denies in its configuration, and the API key file's key; with `claude` it gives a `ClaudeCodeRuntime` (rows).
5. `machine_extras` for `opencode` gives the item names in the order `token-file`, `agent-user`, `tool:sudo`, `agent-environment`, `confinement`, `opencode`, `agent-run-probe` with an agent user, and without `tool:sudo` without one; for `claude` the names of today, without `opencode` (rows).
6. `opencode_item` passes for an executable on the agent run's `PATH` and agents whose models are `opus` and `anthropic/claude-haiku-5-5` with `opus` mapped; it fails with each fault's text alone for an executable not on the `PATH`, an environment without `PATH` and an unmapped `sonnet`, and with the PATH fault and the model fault joined by `; ` in that order (rows).
7. `opencode_item` is the same whatever the API login file: unset, a path that does not exist, an empty file and a file holding a key give the same item (rows).
8. `installed_models` gives `["opus", "sonnet"]` for three agents using `sonnet`, `opus` and `sonnet` in the order of their names `coder`, `intake`, `tester`, and `[]` without an agents folder (rows).
9. `MachineChecks.run` checks `tool:opencode` (the opencode executable) instead of `tool:claude` under opencode; the version item passes for a reported `1.19.3` and a pin `1.19.3`, fails with `the agent runtime reports 1.19.4, the image pins 1.19.3; ...` for another, and fails with `the image does not pin a version: FACTORY_OPENCODE_VERSION is not set` without a pin; under Claude Code it is today's item (rows).
10. A probe under opencode that ends `died` fails with `the probe run ended died; run opencode run by hand as agent to see why` and no token hint; with the login `api_key` it gets S0001's API hint; with the login `none` it gets the single sign-on hint above (rows).
11. The Dockerfile has `ARG OPENCODE_VERSION=1.19.3` (three numbers) once, one `npm install` of `opencode-ai@${OPENCODE_VERSION}` after the one of Claude Code, `FACTORY_OPENCODE_VERSION` set to `${OPENCODE_VERSION}` and `FACTORY_OPENCODE_MODELS` set to the three ids, both before `USER factory`; `tests/test_image.py` passes unchanged (no floating reference).
12. The compose service's environment holds the five entries above in that order after `FACTORY_INSTANCE`; the default of `FACTORY_OPENCODE_VERSION` equals the Dockerfile's `ARG OPENCODE_VERSION` and that of `FACTORY_OPENCODE_MODELS` the Dockerfile's `FACTORY_OPENCODE_MODELS`; the two required variables keep their form (`tests/test_compose.py` passes).
13. `read_settings` gives `[]` without `FACTORY_OPENCODE_FOLDERS` and for a blank one, `[".config/sso-opencode", ".local/share/sso"]` for `.config/sso-opencode, .local/share/sso`, and raises `SettingsInvalid` naming the variable for `/abs`, `../up`, `a/../b`, `a//b`, `.` and `a,` (rows).
14. An `OpencodeRuntime` built with `runtime_folders=(*RUNTIME_FOLDERS, ".config/sso-opencode")`, through a stand-in wrapper, gives rules whose folders after the checkout's hold `<HOME>/.local/share/opencode`, `<HOME>/.local/state/opencode`, `<HOME>/.cache/opencode` and `<HOME>/.config/sso-opencode` in that order; built without it, the first three alone; `build_boundaries` passes the setting's folders after the three (rows).
15. `make check` stays green.
16. docs: `docs/operator-guide.md`: a section *Running on opencode*: `FACTORY_AGENT_RUNTIME=opencode` per instance; its login, either an API key in its own key file (`FACTORY_API_KEY_FILE`, S0001; every run paid through the API) or the login an operator's own build keeps in the agent's home (single sign-on), made once by the operator as the agent user (`docker exec -it -u agent <container> <executable> <the build's login command>`, as `claude setup-token` is for Claude Code), lost when the container is recreated unless the operator mounts its folder with a compose override file, and its folder named in `FACTORY_OPENCODE_FOLDERS` when it lies outside opencode's three; an operator's own build chosen per compose call with `FACTORY_OPENCODE` (its path in the container, which the operator mounts or installs), `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS`, the image's `opencode-ai` being the default; the models of `FACTORY_OPENCODE_MODELS` and how to check them (`opencode models anthropic`), the pinned version, the item `opencode` and what to do about each of its faults, what opencode keeps in the agent's home, and what differs from Claude Code (no hook, the result block, the factory's own budget stop). The configuration table gets `FACTORY_AGENT_RUNTIME`, `FACTORY_OPENCODE`, `FACTORY_OPENCODE_VERSION`, `FACTORY_OPENCODE_MODELS` and `FACTORY_OPENCODE_FOLDERS`; the preflight's items get `opencode`. `README.md`: one sentence that the factory runs its agents on Claude Code or on opencode. `docs/decisions.md`: an entry *The agent runtime is chosen per instance*, dated with the story, with the reasons of the feature's decisions 9, 16 and 17.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python - "$d" <<'EOF'
import sys
from pathlib import Path
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.preflight import opencode_item
from factory.domain.settings import read_settings
from factory.entry.wiring import build_boundaries

d = Path(sys.argv[1])
environ = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "smoke", "FACTORY_AGENT_RUNTIME": "opencode", "FACTORY_OPENCODE_MODELS": "sonnet=anthropic/claude-sonnet-5-5", "FACTORY_API_LOGIN_FILE": str(d / "api-login")}
settings = read_settings(environ).model_copy(update={"checkout": d / "checkout", "state_directory": d / "state", "agent_home": d / "home" / ".claude"})
boundaries = build_boundaries(settings, "", hosting=FakeHostingService(), confine_executable=None)
print(type(boundaries.agent_runtime).__name__, settings.opencode_models)
item = opencode_item(settings, {"PATH": "/nowhere"}, lambda name, path: None, ["sonnet", "opus"])
print(item.passed)
print(item.detail.replace(str(d), "D"))
EOF
grep -c 'opencode-ai@${OPENCODE_VERSION}' image/Dockerfile
```
Expect: four lines, `OpencodeRuntime {'sonnet': 'anthropic/claude-sonnet-5-5'}`, `False`, `opencode is not on the agent run's PATH /nowhere; no model is set for opus in FACTORY_OPENCODE_MODELS`, `1`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
