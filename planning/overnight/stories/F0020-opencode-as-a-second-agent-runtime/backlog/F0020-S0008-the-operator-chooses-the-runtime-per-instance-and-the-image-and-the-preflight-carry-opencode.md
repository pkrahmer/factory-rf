# The operator chooses the runtime per instance, and the image and the preflight carry opencode

## Description

After S0004 to S0007 the opencode runtime exists, but nothing builds it and the image does not hold opencode. This story lets the operator choose the runtime of an instance with one setting, `FACTORY_AGENT_RUNTIME` (`claude`, the default, or `opencode`), set for the instance's compose calls like `FACTORY_INSTANCE`; the wiring then builds the opencode runtime with the agent user, the write guard's wrapper, the API key's file, the provider limit and the models of `FACTORY_OPENCODE_MODELS`, which maps the agent files' aliases (`opus`, `sonnet`, `haiku`) to opencode's `provider/model` ids. The image installs opencode from npm at a pinned version, beside Claude Code, and sets the pin and the three Anthropic ids. The preflight checks the runtime in force: its executable on the `PATH`, its version against its pin, and for opencode a new item, `opencode`: the executable on the agent run's `PATH`, the API key's file present and not empty (by its size; the factory never reads the key), and a model for every alias the installed agents use; the probe's hint names the runtime's own command. An instance without the setting runs exactly as today. The real run on opencode is the human's (the feature's change 6).

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

`factory.entry.wiring` (`entry`):

- `build_boundaries` builds, for `agent_runtime` `opencode`, `OpencodeRuntime(settings.opencode_executable, <state>/runs, models=settings.opencode_models, settings_file=settings.agent_home / "settings.json", sudo_executable=<the sudo which finds>, api_login_file=settings.api_login_file, confine_executable=confine_executable, provider_limit=settings.provider_limit)`; for `claude`, the Claude Code runtime as today.
- `machine_extras` adds, for `opencode` only, the item `opencode` right after `confinement` and before `agent-run-probe`; for `claude` the extras are those of today, in today's order.

`factory.application.preflight` (`application`):

```python
def opencode_item(settings: InstanceSettings, environment: Mapping[str, str],
                  find: Callable[[str, str], str | None], size: Callable[[Path], int],
                  agent_models: Sequence[str]) -> PreflightItem: ...
def installed_models(boundaries: Boundaries) -> list[str]: ...
```

- `opencode_item` is named `opencode`; it passes without a detail, or fails with its faults joined by `; ` in this order:
  - `<executable> is not on the agent run's PATH <path>` (or `the agent run has no PATH`), as for the wrapper;
  - `the opencode runtime needs an API key, and FACTORY_API_LOGIN_FILE is not set`; or, by `size` alone, `the API key file <path> does not exist` (for `FileNotFoundError`) or `the API key file <path> is empty: put the key in the host file it is mounted from` (size 0);
  - `no model is set for <alias> in FACTORY_OPENCODE_MODELS`, once for each alias among `agent_models` (a model without `/`) that the mapping lacks, sorted.
- It never opens the key's file: `size` is the file's size from `os.stat` in the wiring.
- `installed_models`: the `model` of every installed agent, in the order of the agents' names, each once; `[]` when the agent definitions cannot be read (the item `agents` reports that).
- `MachineChecks.run`: the last of the required tools is the runtime's executable (`claude_executable` for `claude`, `opencode_executable` for `opencode`).
- The version item compares the runtime's version against the pin of the runtime in force; without a pin, its detail names that runtime's variable: `the image does not pin a version: FACTORY_OPENCODE_VERSION is not set` for opencode, today's text for Claude Code.
- `agent_run_probe_item`: a failed probe under opencode says `run opencode run by hand as <user> to see why` instead of `run claude -p by hand ...`, and gets no token hint; S0001's API hint applies to both runtimes when the probe's login was `api_key`.

`image/Dockerfile`, `image/compose.yml` (`image`, the coder's):

- After `ARG CLAUDE_CODE_VERSION=2.1.296`: `ARG OPENCODE_VERSION=1.19.3`.
- Right after the Claude Code install: `RUN npm install --global --no-audit --no-fund opencode-ai@${OPENCODE_VERSION}`.
- Before `USER factory`, each its own instruction, with a comment line above: `ENV FACTORY_OPENCODE_VERSION=${OPENCODE_VERSION}` and `ENV FACTORY_OPENCODE_MODELS=opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5`.
- The compose service's `environment` gains `FACTORY_AGENT_RUNTIME: ${FACTORY_AGENT_RUNTIME:-claude}`, after `FACTORY_INSTANCE`.

Tests (the tester writes them): `tests/domain/test_settings_agent_runtime.py`, `tests/domain/test_settings_opencode_models.py`, `tests/application/test_opencode_item.py`, `tests/application/test_machine_checks_runtime.py`, `tests/application/test_agent_run_probe_opencode.py`, `tests/entry/test_wiring_opencode.py` (the shared `every_tool` of `tests/wiring_support.py`, imported), `tests/test_opencode_image.py` (the Dockerfile through `tests/dockerfile_support.py`, the compose file as `tests/test_compose.py` reads it). No earlier test changes: the extras, tools and version item of a Claude Code instance stay as they are.

## Acceptance criteria

1. `read_settings` gives `claude` without `FACTORY_AGENT_RUNTIME`, with `""` and with `" "`, `opencode` for `opencode` and for ` opencode `, and raises `SettingsInvalid` naming the variable for `Opencode`, `claude-code` and `both` (rows).
2. `read_settings` gives `opencode` and `None` without `FACTORY_OPENCODE` and `FACTORY_OPENCODE_VERSION`, and `/opt/bin/opencode` and `1.19.3` with them (rows).
3. `FACTORY_OPENCODE_MODELS` `opus=anthropic/claude-opus-5-5, sonnet = anthropic/claude-sonnet-5-5` gives the two entries in order; blank gives `{}`; `opus`, `=anthropic/x`, `opus=anthropic`, `opus=/x`, `opus=anthropic/` and `opus=a/b,opus=c/d` raise `SettingsInvalid` with their texts (rows).
4. `build_boundaries` with `agent_runtime` `opencode` gives an `OpencodeRuntime` whose run of a stand-in (`opencode_executable` set to it, `confine_executable=None`) gets the mapped model, the installed `settings.json`'s denies in its configuration, and the API key file's key; with `claude` it gives a `ClaudeCodeRuntime` (rows).
5. `machine_extras` for `opencode` gives the item names in the order `token-file`, `agent-user`, `tool:sudo`, `agent-environment`, `confinement`, `opencode`, `agent-run-probe` with an agent user, and without `tool:sudo` without one; for `claude` the names of today, without `opencode` (rows).
6. `opencode_item` passes for an executable on the agent run's `PATH`, a key file of size 40 and agents whose models are `opus` and `anthropic/claude-haiku-5-5` with `opus` mapped; it fails with each fault's text alone for an executable not on the `PATH`, no `api_login_file`, a missing file, an empty file and an unmapped `sonnet`, and with all of them joined by `; ` in the order above (rows).
7. `opencode_item` calls `size` with the key file's path and opens no file: with a `size` that returns 40 for a path that does not exist on disk, it passes.
8. `installed_models` gives `["opus", "sonnet"]` for three agents using `sonnet`, `opus` and `sonnet` in the order of their names `coder`, `intake`, `tester`, and `[]` without an agents folder (rows).
9. `MachineChecks.run` checks `tool:opencode` (the opencode executable) instead of `tool:claude` under opencode; the version item passes for a reported `1.19.3` and a pin `1.19.3`, fails with `the agent runtime reports 1.19.4, the image pins 1.19.3; ...` for another, and fails with `the image does not pin a version: FACTORY_OPENCODE_VERSION is not set` without a pin; under Claude Code it is today's item (rows).
10. A probe under opencode that ends `died` fails with `the probe run ended died; run opencode run by hand as agent to see why` and no token hint; with the login `api_key` it gets S0001's API hint (rows).
11. The Dockerfile has `ARG OPENCODE_VERSION=1.19.3` (three numbers) once, one `npm install` of `opencode-ai@${OPENCODE_VERSION}` after the one of Claude Code, `FACTORY_OPENCODE_VERSION` set to `${OPENCODE_VERSION}` and `FACTORY_OPENCODE_MODELS` set to the three ids, both before `USER factory`; `tests/test_image.py` passes unchanged (no floating reference).
12. The compose service's environment holds `FACTORY_AGENT_RUNTIME: ${FACTORY_AGENT_RUNTIME:-claude}`, and the two required variables keep their form (`tests/test_compose.py` passes).
13. `make check` stays green.
14. docs: `docs/operator-guide.md`: a section *Running on opencode*: `FACTORY_AGENT_RUNTIME=opencode` per instance with its own API key file (`FACTORY_API_KEY_FILE`, S0001), every run paid through the API, the models of `FACTORY_OPENCODE_MODELS` and how to check them (`opencode models anthropic`), the pinned version, the item `opencode` and what to do about each of its faults, what opencode keeps in the agent's home, and what differs from Claude Code (no hook, the result block, the factory's own budget stop). The configuration table gets `FACTORY_AGENT_RUNTIME`, `FACTORY_OPENCODE`, `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS`; the preflight's items get `opencode`. `README.md`: one sentence that the factory runs its agents on Claude Code or on opencode. `docs/decisions.md`: an entry *The agent runtime is chosen per instance*, dated with the story, with the reasons of the feature's decisions 9, 16 and 17.

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
item = opencode_item(settings, {"PATH": "/nowhere"}, lambda name, path: None, lambda path: 0, ["sonnet", "opus"])
print(item.passed)
print(item.detail.replace(str(d), "D"))
EOF
grep -c 'opencode-ai@${OPENCODE_VERSION}' image/Dockerfile
```
Expect: four lines, `OpencodeRuntime {'sonnet': 'anthropic/claude-sonnet-5-5'}`, `False`, `opencode is not on the agent run's PATH /nowhere; the API key file D/api-login is empty: put the key in the host file it is mounted from; no model is set for opus in FACTORY_OPENCODE_MODELS`, `1`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
