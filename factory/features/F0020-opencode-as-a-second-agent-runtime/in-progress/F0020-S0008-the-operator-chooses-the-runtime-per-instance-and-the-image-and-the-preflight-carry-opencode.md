---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 260
comments_read: [6265790615]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T11:01:42.422626Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T11:01:42.428672Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T11:02:10.349477Z'
  stage: intake
  run: 2374b9efe1e6470aae7e6cdb6c6633d4
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T11:02:30.592165Z'
  stage: tests
- number: 5
  speaker: tester
  kind: question
  at: '2026-10-19T11:07:31.363511Z'
  stage: tests
  run: 21766fb91a18405dadb558f9b954e10e
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-10-19T11:08:16.132135Z'
  stage: tests
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-19T11:08:34.010755Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-19T11:10:29.589401Z'
  stage: tests
  run: e99f1c09789243b98eab997cc1454054
---

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
- `FACTORY_OPENCODE_MODELS` unset or blank gives `{}`; otherwise comma-separated entries `<alias>=<provider>/<model>`, spaces around each part stripped, give the mapping in their order. An entry without `=`, with an empty alias, or whose model has no `/` or an empty side of its first `/` (the provider is the part before the first `/`, so `openrouter/anthropic/claude-opus-5-5` is one model) raises `SettingsInvalid` naming the variable with `holds <entry>, which is not <alias>=<provider>/<model>`; an alias named twice raises it with `names <alias> twice`.
- `OPENCODE_FOLDERS_VARIABLE = "FACTORY_OPENCODE_FOLDERS"` and `InstanceSettings.opencode_folders: list[str] = []`, last: unset or blank gives `[]`; otherwise comma-separated folders relative to the agent user's home `/home/agent` (not `FACTORY_CLAUDE_HOME`), spaces around each stripped, in their order. An entry that is empty, absolute, or has an empty, `.` or `..` segment raises `SettingsInvalid` naming the variable with `holds <entry>, which is not a folder inside the agent's home`.

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

1. `read_settings` gives `claude` without `FACTORY_AGENT_RUNTIME`, with `""`, with `" "` and with `claude`, `opencode` for `opencode` and for ` opencode `, and raises `SettingsInvalid` naming the variable with `is neither claude nor opencode` for `Opencode`, `claude-code` and `both` (rows).
2. `read_settings` gives `opencode` and `None` without `FACTORY_OPENCODE` and `FACTORY_OPENCODE_VERSION` and with both blank (`" "`), and `/opt/bin/opencode` and `1.19.3` with them (rows).
3. `FACTORY_OPENCODE_MODELS` `opus=anthropic/claude-opus-5-5, sonnet = anthropic/claude-sonnet-5-5` gives the two entries in order; `opus=openrouter/anthropic/claude-opus-5-5` gives that model as it is; unset and blank give `{}`; `opus`, `=anthropic/x`, `opus=anthropic`, `opus=/x`, `opus=anthropic/` and `opus=a/b,opus=c/d` raise `SettingsInvalid` with their texts (rows).
4. `build_boundaries` with `agent_runtime` `opencode` gives an `OpencodeRuntime` whose run of a stand-in (`opencode_executable` set to it, `confine_executable=None`, and `<state>/runs` made by the test, since the opencode runtime makes no state directory of its own and the entrypoint makes it in the image) gets the mapped model, the installed `settings.json`'s denies in its configuration and the API key file's key, keeps its configuration file in `<state>/runs`, and ends `provider_limit` on an error event with the settings' limit status; with `claude` it gives a `ClaudeCodeRuntime` (rows).
5. `machine_extras` for `opencode` gives the item names in the order `token-file`, `agent-user`, `tool:sudo`, `agent-environment`, `confinement`, `opencode`, `agent-run-probe` with an agent user, and without `tool:sudo` without one; for `claude` the names of today, without `opencode` (rows).
6. `opencode_item` passes for an executable on the agent run's `PATH` and agents whose models are `opus` and `anthropic/claude-haiku-5-5` with `opus` mapped; it fails with each fault's text alone for an executable not on the `PATH`, an environment without `PATH` and an unmapped `sonnet`; with `no model is set for haiku in FACTORY_OPENCODE_MODELS; no model is set for sonnet in FACTORY_OPENCODE_MODELS` for the unmapped models `sonnet`, `haiku` and `sonnet`, in that order; and with the PATH fault and the model fault joined by `; ` in that order (rows).
7. `opencode_item` is the same whatever the API login file: unset, a path that does not exist, an empty file and a file holding a key give the same item (rows).
8. `installed_models` gives `["opus", "sonnet"]` for three agents using `sonnet`, `opus` and `sonnet` in the order of their names `coder`, `intake`, `tester`, and `[]` without an agents folder and with an agent file that cannot be read (rows).
9. `MachineChecks.run` checks `tool:opencode` (the opencode executable) instead of `tool:claude` under opencode; the version item passes for a reported `1.19.3` and a pin `1.19.3`, fails with `the agent runtime reports 1.19.4, the image pins 1.19.3; ...` for another, and fails with `the image does not pin a version: FACTORY_OPENCODE_VERSION is not set` without a pin; under Claude Code it is today's item (rows).
10. A probe under opencode that ends `died` fails with `the probe run ended died; run opencode run by hand as agent to see why` and no token hint; with the login `api_key` it gets S0001's API hint; with the login `none` it gets the single sign-on hint above (rows).
11. The Dockerfile has `ARG OPENCODE_VERSION=1.19.3` (three numbers) once, one `npm install` of `opencode-ai@${OPENCODE_VERSION}` after the one of Claude Code, `FACTORY_OPENCODE_VERSION` set to `${OPENCODE_VERSION}` and `FACTORY_OPENCODE_MODELS` set to the three ids, both before `USER factory`; `tests/test_image.py` passes unchanged (no floating reference).
12. The compose service's environment holds the five entries above in that order after `FACTORY_INSTANCE`; the default of `FACTORY_OPENCODE_VERSION` equals the Dockerfile's `ARG OPENCODE_VERSION` and that of `FACTORY_OPENCODE_MODELS` the Dockerfile's `FACTORY_OPENCODE_MODELS`; the two required variables keep their form (`tests/test_compose.py` passes).
13. `read_settings` gives `[]` without `FACTORY_OPENCODE_FOLDERS` and for a blank one, `[".config/sso-opencode", ".local/share/sso"]` for `.config/sso-opencode, .local/share/sso`, and raises `SettingsInvalid` naming the variable with `holds <entry>, which is not a folder inside the agent's home` for `/abs`, `../up`, `a/../b`, `a//b`, `.` and `a,` (rows).
14. An `OpencodeRuntime` built with `runtime_folders=(*RUNTIME_FOLDERS, ".config/sso-opencode")`, through a stand-in wrapper, gives rules whose folders after the checkout's hold `<HOME>/.local/share/opencode`, `<HOME>/.local/state/opencode`, `<HOME>/.cache/opencode` and `<HOME>/.config/sso-opencode` in that order; built without it, the first three alone; `build_boundaries` passes the setting's folders after the three (rows).
15. `make check` stays green.
16. docs: `docs/operator-guide.md`: a section *Running on opencode*: `FACTORY_AGENT_RUNTIME=opencode` per instance; its login, either an API key in its own key file (`FACTORY_API_KEY_FILE`, S0001; every run paid through the API) or the login an operator's own build keeps in the agent's home (single sign-on), made once by the operator as the agent user (`docker exec -it -u agent <container> <executable> <the build's login command>`, as `claude setup-token` is for Claude Code), lost when the container is recreated unless the operator mounts its folder with a compose override file, and its folder named in `FACTORY_OPENCODE_FOLDERS` (relative to the agent user's home `/home/agent`, not to `FACTORY_CLAUDE_HOME`) when it lies outside opencode's three; an operator's own build chosen per compose call with `FACTORY_OPENCODE` (its path in the container, which the operator mounts or installs), `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS`, the image's `opencode-ai` being the default; the models of `FACTORY_OPENCODE_MODELS` and how to check them (`opencode models anthropic`), the pinned version, the item `opencode` and what to do about each of its faults, what opencode keeps in the agent's home, and what differs from Claude Code (no hook, the result block, the factory's own budget stop). The configuration table gets `FACTORY_AGENT_RUNTIME`, `FACTORY_OPENCODE`, `FACTORY_OPENCODE_VERSION`, `FACTORY_OPENCODE_MODELS` and `FACTORY_OPENCODE_FOLDERS`; the preflight's items get `opencode`. `README.md`: one sentence that the factory runs its agents on Claude Code or on opencode. `docs/decisions.md`: an entry *The agent runtime is chosen per instance*, dated with the story, with the reasons of the feature's decisions 9, 16 and 17. `docs/project-guide/watching.md`, *The tick*, step 4: the extras under opencode (`opencode` after `confinement`), `opencode_item`, `installed_models`, and the runtime's executable among the tools. `docs/project-guide/agents.md`, *The opencode runtime*: the runtime chosen in `build_boundaries` by `agent_runtime`, and `runtime_folders` with `FACTORY_OPENCODE_FOLDERS`.

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
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: concrete modules and signatures throughout (`factory.domain.settings`, `factory.entry.wiring`, `OpencodeRuntime.__init__`, `opencode_item`, `installed_models`, Dockerfile and compose lines), with exact error texts.
   - Criteria: each can be tested by one parametrized test function. Every rule has a criterion for its failing side. Blank and invalid runtime values are in 1. Each malformed model entry and the duplicate alias are in 3. Each bad folder entry is in 13. A missing PATH, an unmapped alias and the order of the joined faults are in 6. The unreadable agents folder is in 8. A missing pin is in 9. Both login hints are in 10. Folder order with and without `runtime_folders` is in 14. The one gap is the comment line above each `ENV` in the Dockerfile, which no criterion covers. I did not raise it because it only documents the line and changes no behaviour.
   - Smoke test: runnable as written. I traced the output against the Interface and the four Expect values match: `OpencodeRuntime {...}`, `False`, the PATH fault joined with the missing `opus` model, and `1`.
   - Architecture: the settings and DTO changes sit in domain, the item and checks in application, the runtime folders in adapters, and the runtime choice and extras in entry wiring. This respects the layer order. No new dependency or package.
   - Scope: within F0020's scope for S0008. It touches no item in Out of scope, and it names no earlier test change beyond the standing leave.
4. factory: started tests as self.
5. tester: Question: one row of criterion 8 contradicts the Interface for `installed_models`. Which order is right?

   The Interface says `installed_models` gives "the `model` of every installed agent, in the order of the agents' names, each once". Criterion 8 gives the agents as `coder` (sonnet), `intake` (opus) and `tester` (sonnet), in that name order, and expects `["opus", "sonnet"]`. Reading the agents in name order and keeping each model once gives `["sonnet", "opus"]` instead. Options:
   - (a) Name order, as the Interface says. The criterion's expected value becomes `["sonnet", "opus"]`.
   - (b) Sorted models. The Interface becomes "each once, sorted" and the criterion stays `["opus", "sonnet"]`.

   I would choose (a). `opencode_item` sorts its own faults, so `installed_models` needs no order of its own. I have not written that row; once you answer I add it to `tests/application/test_opencode_item.py::test_the_installed_models_are_none_when_the_agents_cannot_be_read`, renamed to cover both cases. Its two `[]` rows (no agents folder, an agent file that cannot be read) are written.

   Where I stopped: every other criterion's tests are written and `make lint` is green. I ran `make test` once and it fails for the right reasons. Some test modules cannot be imported because names are missing: `AGENT_RUNTIME_VARIABLE`, `OPENCODE_EXECUTABLE_VARIABLE`, `OPENCODE_VERSION_VARIABLE`, `OPENCODE_MODELS_VARIABLE` and `OPENCODE_FOLDERS_VARIABLE` from `factory.domain.settings`, and `opencode_item` and `installed_models` from `factory.application.preflight`. Other tests error because `InstanceSettings` refuses the new fields (`agent_runtime`, `opencode_*`). In the remaining tests the Dockerfile and compose file lack the opencode lines, or `OpencodeRuntime` refuses `runtime_folders`.

   Mapping:
   - criterion 1: tests/domain/test_settings_agent_runtime.py::test_the_agent_runtime_is_claude_by_default_or_the_one_named
   - criterion 2: tests/domain/test_settings_agent_runtime.py::test_the_opencode_executable_and_pin_default_to_opencode_and_none
   - criterion 3: tests/domain/test_settings_opencode_models.py::test_the_opencode_models_map_each_alias_in_their_order and ::test_a_malformed_opencode_models_entry_is_refused_naming_it
   - criterion 4: tests/entry/test_wiring_opencode.py::test_the_built_runtime_is_the_one_the_instance_names and ::test_the_built_opencode_runtime_runs_with_the_instance_s_models_denies_key_and_limit
   - criterion 5: tests/entry/test_wiring_opencode.py::test_the_opencode_item_comes_after_confinement_only_under_opencode
   - criterion 6: tests/application/test_opencode_item.py::test_the_opencode_item_names_a_missing_executable_and_each_unmapped_alias
   - criterion 7: tests/application/test_opencode_item.py::test_the_opencode_item_does_not_depend_on_the_api_login_file
   - criterion 8: tests/application/test_opencode_item.py::test_the_installed_models_are_none_when_the_agents_cannot_be_read (the three-agent row is open, see above)
   - criterion 9: tests/application/test_machine_checks_runtime.py::test_the_last_required_tool_is_the_runtime_s_executable and ::test_the_version_item_compares_against_the_pin_of_the_runtime_in_force
   - criterion 10: tests/application/test_agent_run_probe_opencode.py::test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint
   - criterion 11: tests/test_opencode_image.py::test_the_image_installs_opencode_at_its_pin_and_sets_its_version_and_models
   - criterion 12: tests/test_opencode_image.py::test_the_compose_service_passes_the_runtime_and_opencode_build_with_the_image_s_defaults
   - criterion 13: tests/domain/test_settings_opencode_folders.py::test_the_opencode_folders_are_the_named_ones_in_their_order and ::test_an_opencode_folder_outside_the_agent_s_home_is_refused_naming_it
   - criterion 14: tests/adapters/test_opencode_runtime_folders.py::test_the_rules_allow_each_runtime_folder_in_the_home_in_order, and for build_boundaries tests/entry/test_wiring_opencode.py::test_the_built_opencode_runtime_allows_the_instance_s_folders_after_opencode_s

   Smaller readings I took, which you can overrule along with the answer:
   - For `a,` in criterion 13 the entry named in the error is empty: `holds , which is not a folder inside the agent's home`.
   - The mismatch text in criterion 9 and the runtime text in criterion 1 are checked as a prefix and as contained text, because the criteria show them only in part.

   Files created: tests/domain/test_settings_agent_runtime.py, tests/domain/test_settings_opencode_models.py, tests/domain/test_settings_opencode_folders.py, tests/adapters/test_opencode_runtime_folders.py, tests/application/test_opencode_item.py, tests/application/test_machine_checks_runtime.py, tests/application/test_agent_run_probe_opencode.py, tests/entry/test_wiring_opencode.py, tests/test_opencode_image.py. I changed no earlier test file.
6. 2026-10-19 human: (a). The Interface stands: `installed_models` gives each model once in the order of the agents' names, so criterion 8's three-agent row expects `["sonnet", "opus"]`. Add the row as you propose, with the test renamed to cover both cases. Your two smaller readings are accepted as you took them (the empty entry named in criterion 13's error for `a,`; prefix and contained-text checks for the texts criteria 1 and 9 show in part).
7. factory: started tests as self.
8. tester: Added criterion 8's three-agent row, following the human's answer (a): `installed_models` gives each model once, in the order of the agents' names. The agents are `coder` (sonnet), `intake` (opus) and `tester` (sonnet), and the row expects `["sonnet", "opus"]`. The test writes the agent files in the order tester, coder, intake, so a result in file order fails the row. I renamed the test to cover both cases. The two `[]` rows are unchanged. The readings the human accepted stay as they were: the empty entry named in criterion 13's error for `a,`, and prefix or contained-text checks for the texts that criteria 1 and 9 show only in part.

   I ran `make test` once. It fails for the right reasons only: collection errors where a module imports a name that does not exist yet (the new `*_VARIABLE` constants in `factory.domain.settings`, `opencode_item` and `installed_models` in `factory.application.preflight`), and test errors where `InstanceSettings` refuses the new fields. `make lint` is green.

   Mapping:
   - criterion 1: tests/domain/test_settings_agent_runtime.py::test_the_agent_runtime_is_claude_by_default_or_the_one_named
   - criterion 2: tests/domain/test_settings_agent_runtime.py::test_the_opencode_executable_and_pin_default_to_opencode_and_none
   - criterion 3: tests/domain/test_settings_opencode_models.py::test_the_opencode_models_map_each_alias_in_their_order and ::test_a_malformed_opencode_models_entry_is_refused_naming_it
   - criterion 4: tests/entry/test_wiring_opencode.py::test_the_built_runtime_is_the_one_the_instance_names and ::test_the_built_opencode_runtime_runs_with_the_instance_s_models_denies_key_and_limit
   - criterion 5: tests/entry/test_wiring_opencode.py::test_the_opencode_item_comes_after_confinement_only_under_opencode
   - criterion 6: tests/application/test_opencode_item.py::test_the_opencode_item_names_a_missing_executable_and_each_unmapped_alias
   - criterion 7: tests/application/test_opencode_item.py::test_the_opencode_item_does_not_depend_on_the_api_login_file
   - criterion 8: tests/application/test_opencode_item.py::test_the_installed_models_are_each_agent_s_model_once_or_none_when_unreadable
   - criterion 9: tests/application/test_machine_checks_runtime.py::test_the_last_required_tool_is_the_runtime_s_executable and ::test_the_version_item_compares_against_the_pin_of_the_runtime_in_force
   - criterion 10: tests/application/test_agent_run_probe_opencode.py::test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint
   - criterion 11: tests/test_opencode_image.py::test_the_image_installs_opencode_at_its_pin_and_sets_its_version_and_models
   - criterion 12: tests/test_opencode_image.py::test_the_compose_service_passes_the_runtime_and_opencode_build_with_the_image_s_defaults
   - criterion 13: tests/domain/test_settings_opencode_folders.py::test_the_opencode_folders_are_the_named_ones_in_their_order and ::test_an_opencode_folder_outside_the_agent_s_home_is_refused_naming_it
   - criterion 14: tests/adapters/test_opencode_runtime_folders.py::test_the_rules_allow_each_runtime_folder_in_the_home_in_order, and tests/entry/test_wiring_opencode.py::test_the_built_opencode_runtime_allows_the_instance_s_folders_after_opencode_s (build_boundaries)

   Files created on this branch (the last run wrote all of them; this run changed only test_opencode_item.py): tests/domain/test_settings_agent_runtime.py, tests/domain/test_settings_opencode_models.py, tests/domain/test_settings_opencode_folders.py, tests/adapters/test_opencode_runtime_folders.py, tests/application/test_opencode_item.py, tests/application/test_machine_checks_runtime.py, tests/application/test_agent_run_probe_opencode.py, tests/entry/test_wiring_opencode.py, tests/test_opencode_image.py. No earlier test file changed.

   Not importable by the test run:
   - `factory.domain.settings`: the new `*_VARIABLE` names are missing.
   - `factory.application.preflight`: `opencode_item` and `installed_models` are missing.

   `InstanceSettings` lacks the new fields, and `OpencodeRuntime` lacks `runtime_folders`. The Dockerfile and compose file lack the opencode lines.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/application/test_agent_run_probe_opencode.py::test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint[none]
