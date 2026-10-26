---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 459
comments_read: [6416165613, 6416662775, 6417568826]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-10-26T13:56:18.262154Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T11:46:23.877366Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T11:46:23.882644Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-26T11:46:43.571075Z'
  stage: intake
  run: cf99657d94064b7c9561084db41cf111
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-26T12:38:06.947848Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-26T12:38:24.727799Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-26T12:38:45.437835Z'
  stage: intake
  run: 83123bf447f84c07864276f2a240a875
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-26T12:39:05.646518Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-26T12:57:02.605529Z'
  stage: tests
  run: 83bd351a2d2c43639cf4aff8d439d537
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-26T12:57:23.067909Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-10-26T13:01:37.329002Z'
  stage: doing
  run: 926db96799044f4890b3cabc59d425b5
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-10-26T13:13:59.746205Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-26T13:14:20.935502Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-10-26T13:14:41.258954Z'
  stage: doing
  run: 050490246e1d44b5b7c3200c9422bbb9
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-26T13:15:02.011665Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-10-26T13:21:16.901694Z'
  stage: tests
  run: beb2c07c41624933a3333cb677c39a5d
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-26T13:21:37.883929Z'
  stage: doing
- number: 17
  speaker: coder
  kind: question
  at: '2026-10-26T13:24:55.659059Z'
  stage: doing
  run: b688f39c285a49b1a91f3bef4718cbc9
  blocked: question
- number: 18
  speaker: human
  kind: comment
  at: '2026-10-26T13:47:42.667974Z'
  stage: doing
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-26T13:48:00.830661Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-10-26T13:54:12.606941Z'
  stage: doing
  run: 5e68c74f7b6e485f83c288ed08c69b9d
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-26T13:54:33.949081Z'
  stage: review
- number: 22
  speaker: reviewer
  kind: result
  at: '2026-10-26T13:55:57.242746Z'
  stage: review
  run: d08e37e6c00d4316998042f49327a798
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-26T13:56:18.262154Z'
  stage: doing
---

# The opencode runtime merges a provider file into every run's configuration

## Description

An operator behind a company proxy that speaks the OpenAI protocol cannot point opencode at it: the per-run `opencode-<run>.json` holds `autoupdate`, `share`, `snapshot` and the one agent, and no `provider`. This story adds the setting `FACTORY_OPENCODE_PROVIDER_FILE`, the path of a JSON file on the machine. When it is set, the opencode runtime reads the file and merges it into the configuration of every run: one custom provider (`npm`, `baseURL`, the name of the environment variable that holds the key, its models with optional limits and prices) and the `small_model`, which opencode otherwise takes from a service of its own. The file is validated into a model that refuses unknown keys; a fault in it is an `AgentRuntimeError` before any file is written. The key is never in the file: it is the text `{env:<NAME>}`, and the runtime refuses a name that is not an environment variable name. The agents reach the provider through `FACTORY_OPENCODE_MODELS` (`opus=<provider>/<model>`), which already accepts that form. Unchanged: with the setting unset the configuration is byte-identical to today's, the Claude Code runtime, the login shell, the preflight's `opencode` item, and every other setting. Left to later stories: the proxy and the CA bundle of the containers (S0002) and the file for the operator's settings (S0003).

## Interface

`factory.domain.settings` (domain): the constant `OPENCODE_PROVIDER_FILE_VARIABLE = "FACTORY_OPENCODE_PROVIDER_FILE"` and the field `InstanceSettings.opencode_provider_file: Path | None = None`.

- `read_settings` reads the variable with `_optional`: unset or blank is `None`. A value that is not an absolute path is `SettingsInvalid(FACTORY_OPENCODE_PROVIDER_FILE, "is not an absolute path")`. The model validator of `InstanceSettings` refuses a relative path the same way (a `ValidationError`).

`factory.domain.opencode_provider` (domain, new):

```python
class OpencodeModel(BaseModel):
    """One model of the provider: its limits and its prices, all optional."""
    name: str | None = None
    context: PositiveInt | None = None
    output: PositiveInt | None = None
    input_cost: NonNegativeFloat | None = None    # dollars per million tokens
    output_cost: NonNegativeFloat | None = None

class OpencodeProvider(BaseModel):
    """The provider file: one OpenAI-compatible provider and the small model."""
    id: str                       # the provider's id in the model names
    base_url: str                 # http:// or https://
    api_key_env: str              # the name of the environment variable that holds the key
    models: dict[str, OpencodeModel]
    small_model: str              # "<id>/<model>"

def read_provider(text: str) -> OpencodeProvider: ...
def provider_configuration(provider: OpencodeProvider) -> dict[str, object]: ...
```

- `read_provider` validates JSON text into the model (frozen, unknown keys refused) and raises `ValueError` whose message names the first fault. Rules, each with both sides:
  - `id` matches `[a-z][a-z0-9-]*`; `models` holds at least one entry; each model key is not blank.
  - `base_url` starts with `http://` or `https://` and has a host; a trailing `/` is kept as it is.
  - `api_key_env` matches `[A-Z_][A-Z0-9_]*`.
  - `small_model` is `<id>/<key>` with `<id>` the provider's id and `<key>` one of `models`.
  - `input_cost` and `output_cost` are given together or not at all; `context` and `output` likewise.
- `provider_configuration` gives the two top-level keys the runtime merges: `provider`: `{<id>: {"npm": "@ai-sdk/openai-compatible", "options": {"baseURL": <base_url>, "apiKey": "{env:<api_key_env>}"}, "models": {<key>: {...}}}}` and `small_model`. A model with a `name` has `"name"`; with `context` and `output` it has `"limit": {"context": .., "output": ..}`; with prices it has `"cost": {"input": .., "output": ..}`. A model with none of those is `{}`.

`factory.adapters.opencode_runtime` (adapters): `OpencodeRuntime(..., provider_file: Path | None = None)`, keyword, last.

- `provider_file=None`: `_configuration` returns exactly what it returns today.
- A file: it is read and validated when a run starts, before the state directory is touched; a missing or unreadable file, or a `ValueError` of `read_provider`, is `AgentRuntimeError("cannot use the opencode provider file <path>: <reason>")` and no configuration file is written. The merged configuration holds the keys of `provider_configuration` beside the existing ones; no existing key changes.
- A request whose model is `<id>/<key>` of the file passes unchanged (`_model` already returns a name with a `/`).

`factory.entry.wiring` (entry): `_agent_runtime` gives `OpencodeRuntime` `provider_file=settings.opencode_provider_file`.

Tests (the tester writes them): `tests/domain/test_opencode_provider.py`, `tests/domain/test_settings_opencode_provider.py`, `tests/adapters/test_opencode_runtime_provider.py` (through `tests/adapters/opencode_stand_in.py`), `tests/entry/test_wiring_opencode_provider.py`.

## Acceptance criteria

1. With `opencode_provider_file` unset, the configuration file of a run is byte-identical to the one the runtime wrote before this story (a row with the file set to `None`, the expected text built by the test from the same keys as the existing tests).
2. `FACTORY_OPENCODE_PROVIDER_FILE` is read: unset and blank (`"  "`) give `None`, `/etc/p.json` gives that path, `p.json` is `SettingsInvalid` naming the variable and `is not an absolute path`; building `InstanceSettings(opencode_provider_file=Path("p.json"))` is a `ValidationError`.
3. `read_provider` accepts a complete file and refuses each fault, rows of one parametrized test: `id` `Corp` and `1corp` refused, `corp-1` accepted; empty `models` refused, one entry accepted; a blank model key refused; `base_url` `ftp://x`, `https://` and `example.invalid` refused, `https://example.invalid/v1`, `https://example.invalid/v1/` and `http://example.invalid` accepted; `api_key_env` `lower` and `1KEY` refused, `PROXY_KEY` accepted; `small_model` `other/m`, `corp` and `corp/missing` refused, `corp/m` accepted; `input_cost` without `output_cost`, `output_cost` without `input_cost`, `context` without `output` and `output` without `context` refused; a cost of `-0.01` refused and `0` accepted; `context` of `0` refused and `1` accepted; an unknown key at the top and in a model refused; JSON that is not an object refused.
4. `provider_configuration` of a provider with one model that has a name, limits and prices gives exactly `{"provider": {"corp": {"npm": "@ai-sdk/openai-compatible", "options": {"baseURL": "https://example.invalid/v1", "apiKey": "{env:PROXY_KEY}"}, "models": {"m": {"name": "M", "limit": {"context": 1000, "output": 100}, "cost": {"input": 3.0, "output": 15.0}}}}}, "small_model": "corp/m"}`; a model with none of the three optional groups is `{}`; rows of one parametrized test give a model with the name only `{"name": ..}`, with limits only `{"limit": ..}` and with prices only `{"cost": ..}`, and no key is ever null; a `base_url` with a trailing slash (`https://example.invalid/v1/`) gives `"baseURL": "https://example.invalid/v1/"`, the slash kept.
5. With a valid file, the run's configuration file holds the keys of criterion 4 beside `autoupdate`, `share`, `snapshot` and `agent`, and the agent's entry is as without the file.
6. A missing file, a directory in its place and an invalid file each end the run with `AgentRuntimeError` whose message starts `cannot use the opencode provider file <path>:`; the stand-in is not started and no `opencode-*.json` is in the state directory.
7. A request whose agent model is `corp/m` is passed as `--model corp/m`; an alias in `models` that maps to `corp/m` gives the same words.
8. `build_boundaries` on an opencode instance with the setting gives a runtime that merges the file (the wiring test reads the configuration of one run); on a Claude Code instance the setting changes nothing.
9. `read_provider` refuses an `output` of `0` and accepts `1`, and refuses an `output_cost` of `-0.01` and accepts `0`: rows of the parametrized test of criterion 3, each with its pair given so that only the bound is under test.
10. The `ValueError` of `read_provider` names the first fault: in every refused row of criterion 3 but the one that is not an object, the message holds the name of the field at fault (`id`, `models`, `base_url`, `api_key_env`, `small_model`, `input_cost`, `output_cost`, `context`, `output`, or the unknown key).
11. `make check` stays green.
12. docs: `docs/operator-guide.md`: a subsection under the opencode runtime, *A company's provider*, with the variable's row in the configuration table, an example file written with `example.invalid` and made-up ids, the rule that the key stays in `FACTORY_API_LOGIN_FILE` and is named as `api_key_env: ANTHROPIC_API_KEY`, the small model, and the note that a model without prices is costed at 0 so the budget stop does not fire. The same chapter's passage on a login that an operator's own build keeps in the agent's home is corrected: on the machine the home lies on the dataset and is rolled back, so only the API login file works; the sentence that all three secret files must exist whatever the runtime is made exact for opencode (the file `claude-token` may be empty). `docs/project-guide/agents.md`, *The opencode runtime*: the setting, the module and the merge rule. `docs/decisions.md`: an entry *A company's provider for opencode*, from the feature's decisions 1 to 5 and 9. `README.md`: none.

## Smoke test

```bash
uv run python -c "
from factory.domain.opencode_provider import read_provider, provider_configuration
text = '{\"id\": \"corp\", \"base_url\": \"https://example.invalid/v1\", \"api_key_env\": \"ANTHROPIC_API_KEY\", \"models\": {\"m\": {}}, \"small_model\": \"corp/m\"}'
print(sorted(provider_configuration(read_provider(text))))
"
```
Expect: `['provider', 'small_model']`

```bash
uv run python -c "
from factory.domain.opencode_provider import read_provider
try:
    read_provider('{\"id\": \"corp\", \"base_url\": \"https://example.invalid/v1\", \"api_key_env\": \"ANTHROPIC_API_KEY\", \"models\": {\"m\": {}}, \"small_model\": \"corp/x\"}')
except ValueError:
    print('refused')
"
```
Expect: `refused`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: Intake found gaps. The format check passed. Questions:

   1. The Interface says of `base_url`: "a trailing `/` is kept as it is". No criterion tests this. Criterion 3 lists only `https://example.invalid/v1` and `http://example.invalid` as accepted, and criterion 4 uses a `base_url` without a trailing slash. Two coders could strip the slash or keep it, and both would pass. Proposal: add a criterion, or extend criterion 4, so that `https://example.invalid/v1/` gives `"baseURL": "https://example.invalid/v1/"` in `provider_configuration`, and `read_provider` accepts it.

   2. The Interface says `provider_configuration` gives `"name"` for a model with a name, `"limit"` for one with `context` and `output`, and `"cost"` for one with prices. Criterion 4 tests only all three together, or none. A coder could add the groups wrongly when only one is present (for example `limit` emitted with null values, or `name` emitted as null) and still pass. Proposal: add a parametrized row per group alone (name only → `{"name": ..}`, limits only → `{"limit": ..}`, prices only → `{"cost": ..}`).

   3. The pair rules say "given together or not at all". Criterion 3 tests only `input_cost` without `output_cost` and `context` without `output`. The reverse sides (`output_cost` without `input_cost`, `output` without `context`) have no row. Proposal: add both rows.

   Everything else passes. The Interface names concrete modules and signatures. The architecture fits: domain model, adapter option, and wiring in entry. The scope is within the feature's S0001 and its Out of scope. The smoke test commands run with `uv run python` and use no pytest, so there is no `-q` problem. Each `Expect:` line is checkable.

   I would choose to add all three, as written in the proposals.
4. 2026-10-26 human: Add all three, as proposed:
   1. `https://example.invalid/v1/` is accepted by `read_provider` and gives `"baseURL": "https://example.invalid/v1/"`, with the slash kept.
   2. One parametrized row per group alone: name only gives `{"name": ..}`, limits only give `{"limit": ..}`, prices only give `{"cost": ..}`; no key is ever null.
   3. The reverse rows: `output_cost` without `input_cost` and `output` without `context` are refused.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: `factory.domain.settings`, the new `factory.domain.opencode_provider` (models, `read_provider`, `provider_configuration`), `OpencodeRuntime(provider_file=)` and the wiring name concrete modules and signatures. Every rule is stated with its sides.
   - Criteria: each is testable by one parametrized or plain test. Every rule has its failing side. I carried the human's answer (journal entry 4) into the story, and added nothing else. Criterion 3 now also accepts `https://example.invalid/v1/` and refuses `output_cost` without `input_cost` and `output` without `context`. Criterion 4 now has the rows for name only, limits only and prices only (no key null), and for the trailing slash kept in `baseURL`.
   - Smoke test: both commands are `uv run python -c` with no pytest, so there is no `-q` problem. Their `Expect:` lines (`['provider', 'small_model']` and `refused`) can be checked against the output.
   - Architecture: the model and rules are in domain, the file read and the merge are in the adapter, and the wiring is in entry. This matches the four layers in CLAUDE.md.
   - Scope: the story is S0001 of F0046. The proxy and CA bundle (S0002) and the environment file (S0003) are left out, and nothing in Out of scope is touched.
7. factory: started tests as vm.
8. tester: I wrote the tests for criteria 1 to 8. Criteria 9 and 10 are the check and the docs, so they get no test.

   - criterion 1: tests/adapters/test_opencode_runtime_provider.py::test_without_a_provider_file_the_configuration_is_as_before (one row leaves out `provider_file`, the other passes `None`; the expected text is `json.dumps` of the keys the existing tests use)
   - criterion 2: tests/domain/test_settings_opencode_provider.py::test_the_provider_file_setting_is_read_as_an_optional_path (unset, blank, absolute), ::test_a_relative_provider_file_setting_is_refused_naming_it, ::test_the_settings_model_takes_only_an_absolute_provider_file (absolute accepted, relative is a `ValidationError`)
   - criterion 3: tests/domain/test_opencode_provider.py::test_the_provider_file_is_accepted_only_when_it_keeps_every_rule (one parametrized test, one row per side the criterion names, plus a complete file and a minimal one; in each `id` row `small_model` follows the id, so only the id rule is under test)
   - criterion 4: tests/domain/test_opencode_provider.py::test_a_complete_provider_gives_the_provider_and_the_small_model and ::test_each_model_holds_only_the_groups_it_was_given (rows: none, name only, limits only, prices only, trailing slash kept; each compares the whole dict exactly, so a null key fails)
   - criterion 5: tests/adapters/test_opencode_runtime_provider.py::test_a_provider_file_adds_its_keys_beside_the_existing_ones
   - criterion 6: tests/adapters/test_opencode_runtime_provider.py::test_a_provider_file_that_cannot_be_used_fails_before_anything_starts (rows: missing, directory, invalid `{}`)
   - criterion 7: tests/adapters/test_opencode_runtime_provider.py::test_a_model_of_the_provider_file_is_passed_as_it_is (rows: `corp/m`, and the alias `opus` mapped to `corp/m`)
   - criterion 8: tests/entry/test_wiring_opencode_provider.py::test_the_built_opencode_runtime_merges_the_provider_file and ::test_the_provider_file_changes_nothing_on_a_claude_code_instance (with and without the file, the runtime is `ClaudeCodeRuntime`)

   How the wiring test reads the configuration: the stand-in podman runs the container's words (`PodmanPlan(image=IMAGE)`). The configured `opencode` is a small script that copies `runs/opencode-*.json` into `tmp_path/capture` before it replies, because the runtime deletes the file after the run. I did this because podman's process does not get `OPENCODE_CONFIG`, so the existing stand-in cannot record the file.

   Files created:
   - tests/opencode_provider_support.py (the complete provider file, the configuration it gives, `write_provider`)
   - tests/domain/test_opencode_provider.py
   - tests/domain/test_settings_opencode_provider.py
   - tests/adapters/test_opencode_runtime_provider.py
   - tests/entry/test_wiring_opencode_provider.py

   I changed no earlier test file.

   Modules the test run could not import: `factory.domain.opencode_provider` (it does not exist yet) and `OPENCODE_PROVIDER_FILE_VARIABLE` from `factory.domain.settings`. Both domain test modules fail with ImportError at collection. The adapter tests fail with `TypeError: OpencodeRuntime.__init__() got an unexpected keyword argument 'provider_file'`.

   My one `make test` printed only its last five lines. I did not see how the wiring tests ended. Some tests may already pass, because they pin behaviour that does not change: the adapter row that leaves out `provider_file`, and possibly the two Claude Code wiring rows.

   `make lint` is green after `ruff --fix` sorted one import block. I skipped the type check, as this stage says to.

   `lint`: lint: green (0.2 s)
   `test`: ERROR tests/domain/test_settings_opencode_provider.py - ImportError while importing test module '/work/checkout/tests/domain/test_settings_opencode_provider.py'.
9. factory: started doing as vm.
10. coder: I wrote the code, but `make check` is red. The two causes are in the tests, which I may not change, so I stopped before the refactor step.

    Built (in the working tree):
    - `src/factory/domain/opencode_provider.py` (new): `OpencodeModel` and `OpencodeProvider` (frozen, unknown keys refused, every rule of the Interface as a validator), plus `read_provider` and `provider_configuration`. `read_provider` turns pydantic's first error into `ValueError("<field>: <message>")`.
    - `src/factory/domain/settings.py`: `OPENCODE_PROVIDER_FILE_VARIABLE`, `InstanceSettings.opencode_provider_file`, and a new helper `_optional_absolute_path`. The existing `_absolute` field validator now also covers the new field. `_absolute_path` now uses the new helper, so the absolute-path rule lives in one place.
    - `src/factory/adapters/opencode_runtime.py`: `provider_file=` (keyword, last). `_provider_keys` reads the file before `_RunFiles` is made, and turns an `OSError` or `ValueError` into `AgentRuntimeError("cannot use the opencode provider file <path>: ...")`. `_configuration` adds the keys after `agent`, so with no file the dict and its JSON are unchanged.
    - `src/factory/entry/wiring.py`: passes `provider_file=settings.opencode_provider_file`.

    Main choice: the runtime reads and validates the file on every run instead of once in `__init__`. The Interface says "when a run starts", and an operator can fix the file without restarting the factory. I rejected reading it in `__init__`, because then `build_boundaries` would fail on a bad file.

    Where it stands: lint, types, layers, sast and licenses are green. The smoke test prints `['provider', 'small_model']`, and the second command is refused. `make test` passes except for one test. `make secrets` is red. Both problems need a change to the tests:

    1. `make secrets`: detect-secrets reports "Secret Keyword" at `tests/domain/test_opencode_provider.py:18`, `:47` and `:48`, and at `tests/opencode_provider_support.py:9`. Those are the `"api_key_env": "PROXY_KEY"` / `api_key_env="lower"` / `"1KEY"` lines: the field name `api_key...` with a quoted value. The Interface fixes the field name. Options:
       (a) the tester writes those values so the keyword detector does not match. For example, build the dict from a constant such as `KEY_ENV = "PROXY_KEY"` and use `api_key_env=KEY_ENV`, or spread the key name through a variable, then check that `make secrets` passes;
       (b) you allow `# pragma: allowlist secret` on those four lines (CLAUDE.md: not without asking);
       (c) add baseline entries (also not without asking).
       I would choose (a); if it cannot be done cleanly, (b).

    2. `tests/entry/test_wiring_opencode_provider.py::test_the_built_opencode_runtime_merges_the_provider_file` fails at `tests/entry/test_wiring_opencode_provider.py:54`, `src/factory/adapters/opencode_runtime.py:252` in `_model`:
       `E   factory.domain.errors.AgentRuntimeError: agent runtime failed: the opencode runtime has no model for sonnet: set FACTORY_OPENCODE_MODELS`
       The settings get no `opencode_models`, and `opencode_request` asks for the alias `sonnet`. Making that work would break the existing rule that an unknown alias is an error. Options:
       (a) the tester adds `"opencode_models": MODELS` (from `adapters.opencode_stand_in`) to the `model_copy` update;
       (b) the tester calls `opencode_request(tmp_path / "work", model="corp/m")`.
       I would choose (b), because it also runs the provider's own model through the wiring. Either one is a one-line change.

    Noticed, not touched: nothing else.
11. 2026-10-26 human: 1. (a): the tester writes the key names through a constant (`KEY_ENV = "PROXY_KEY"` and the like) so the keyword detector does not match, and checks that `make secrets` passes. No pragma, no baseline entry.
    2. (b): the wiring test calls `opencode_request(tmp_path / "work", model="corp/m")`, so the provider's own model runs through the wiring. The rule that an unknown alias is an error stays.
    Both are the tester's changes: the tests stage runs again for them; the code stays as built.
12. factory: started doing as vm.
13. coder: The human's answer (entry 11) calls for two test changes and leaves the code as built, so I changed no code this round and hand back to the tester.

    The two changes:
    1. In `tests/domain/test_opencode_provider.py` (lines 18, 47, 48) and `tests/opencode_provider_support.py` (line 9), write the `api_key_env` values through constants (for example `KEY_ENV = "PROXY_KEY"`, and likewise for `"lower"` and `"1KEY"`). Then detect-secrets' keyword detector no longer matches, and `make secrets` is green with no pragma and no baseline entry.
    2. In `tests/entry/test_wiring_opencode_provider.py::test_the_built_opencode_runtime_merges_the_provider_file`, call `opencode_request(tmp_path / "work", model="corp/m")`, so the provider's own model runs through the wiring.

    Built, unchanged since the last round and committed in 0bb1b395: `src/factory/domain/opencode_provider.py`, `src/factory/domain/settings.py`, `src/factory/adapters/opencode_runtime.py`, `src/factory/entry/wiring.py`. Main choice (from entry 10): the runtime reads and validates the provider file at the start of every run, not once in `__init__`. I rejected the `__init__` read because a bad file would then make `build_boundaries` fail.

    Still open: the refactor step, and a green `make check` once the tests are changed. Both fall to the next doing round. Noticed, not touched: nothing.
14. factory: started tests as vm.
15. tester: I made the two test changes the human approved in entry 11, as the coder's entry 13 named them. I changed no other test and no code.

    1. Key names go through constants:
       - `tests/opencode_provider_support.py` now defines `KEY_ENV = "PROXY_KEY"`, and `PROVIDER` uses `"api_key_env": KEY_ENV`.
       - `tests/domain/test_opencode_provider.py` imports `KEY_ENV`. It uses `KEY_ENV` in `MINIMAL` and in the `OpencodeProvider(...)` of `test_each_model_holds_only_the_groups_it_was_given`. That last line was not one of the four flagged; I changed it so every key name in the file goes the same way.
       - The refused rows use the new constants `LOWER_KEY_ENV = "lower"` and `DIGIT_FIRST_KEY_ENV = "1KEY"`.
       - Every test keeps its name and checks the same thing. I added no pragma and no baseline entry.
    2. In `tests/entry/test_wiring_opencode_provider.py::test_the_built_opencode_runtime_merges_the_provider_file` the call is now `opencode_request(tmp_path / "work", model="corp/m")`.

    Results:
    - `make lint`: green.
    - `make test`: `test: green (161.9 s)`, coverage 99.56 %.
    - `make secrets`: no test file is flagged any more, but it is still red. detect-secrets reports "Secret Keyword" twice at line 254 of this work item. That line is in the coder's journal entry 10, which quotes the old test lines (`"api_key_env": "PROXY_KEY"` / `api_key_env="lower"`). The journal belongs to the factory and no stage may edit it, so I left it alone. Someone has to decide how to clear it before `make check` can go green, for example by rewording or baselining that journal line. The coder cannot fix it under the rules either.

    Files changed: `tests/opencode_provider_support.py`, `tests/domain/test_opencode_provider.py`, `tests/entry/test_wiring_opencode_provider.py`.

    Criterion → test mapping is unchanged from entry 8.

    `lint`: lint: green (0.2 s)
    `test`: test: green (161.4 s)
16. factory: started doing as vm.
17. coder: `make check` is red in only one place, and no stage can fix it under the rules. Every other part is green: lint, types, layers and sast pass, and `make test` is `test: green (162.1 s)` with 99.56 % coverage. The tester's changes from entry 15 cleared every test file. `make secrets` still reports "Secret Keyword" twice at line 265 of this work item's file. That line is in coder entry 10 of the `## Journal`, which quotes the old test lines (`api_key_env` with a quoted value). The journal belongs to the factory (R5), and a pragma or a `.secrets.baseline` entry needs your leave (CLAUDE.md, "Not without asking"). Because the check stops at `secrets`, `make licenses` and the `make test` inside `make check` did not run; I ran `make test` on its own.

    Code: no change this round. It is as built in 0bb1b395:
    - `src/factory/domain/opencode_provider.py`
    - `src/factory/domain/settings.py`
    - `src/factory/adapters/opencode_runtime.py`
    - `src/factory/entry/wiring.py`

    Main choice, from entry 10: the provider file is read and validated at the start of every run, not in `__init__`. I rejected the `__init__` read because a bad file would then make `build_boundaries` fail. Refactor step: I read the diff again and nothing needs changing.

    Question: how should the detect-secrets hit in journal entry 10 be cleared? I see three ways:
    (a) You (or the factory) reword that journal line in a human commit, so it no longer pairs `api_key_env` with a quoted value. Nothing in `src/` or `tests/` changes.
    (b) You allow a `.secrets.baseline` entry for that line of the work item. That needs your leave, and the entry goes stale when the line moves.
    (c) You allow `# pragma: allowlist secret` on that journal line. That needs your leave, and the journal is not ours to edit, so it comes back to (a) anyway.
    I would choose (a). Once the line is reworded, `make check` should be green with no code change, and the next doing round can end with `review`.

    Noticed, not touched: nothing else.
18. 2026-10-26 human: Neither of the three as you put them: `main` now holds a line filter in `.secrets.baseline` (lines that name `api_key_env` are not scanned; the human's choice). It reaches this branch through the merge of `origin/main` at the next stage. No change to the journal, `src/` or `tests/`; end the next doing round with `review` once `make check` is green.
19. factory: started doing as vm.
20. coder: `make check` is green after the merge of `origin/main` that brought the human's line filter in `.secrets.baseline` (entry 18): `test: green (161.6 s)` with 99.56 % coverage, then `check: green`. I made no code change this round. The journal changes nothing in the task's meaning (entries 11 and 18 were about the tests and about the secrets scan), so `## Description` stays as it is.

    Built (from 0bb1b395, unchanged since):
    - `src/factory/domain/opencode_provider.py` (new): `OpencodeModel` and `OpencodeProvider` (frozen, unknown keys refused, every rule of the Interface as a field or model validator). `read_provider` turns pydantic's first error into `ValueError("<field>: <message>")`, and `provider_configuration` builds the `provider` and `small_model` keys, with `_model_entry` adding only the groups that were given.
    - `src/factory/domain/settings.py`: `OPENCODE_PROVIDER_FILE_VARIABLE` and `InstanceSettings.opencode_provider_file`. The existing `_absolute` field validator now also covers this field. The new `_optional_absolute_path` is shared with `_absolute_path`, so the absolute-path rule lives in one place.
    - `src/factory/adapters/opencode_runtime.py`: `provider_file=` (keyword, last). `_provider_keys` reads and validates the file before `_RunFiles` is made, and turns an `OSError` or `ValueError` into `AgentRuntimeError("cannot use the opencode provider file <path>: ...")`. `_configuration` spreads those keys after `agent`, so with no file the JSON is byte-identical to before.
    - `src/factory/entry/wiring.py`: passes `provider_file=settings.opencode_provider_file`.

    Main choice: the file is read and validated at the start of every run, as the Interface says ("when a run starts"), so an operator can fix the file without restarting the factory. I rejected reading it once in `__init__`, because a bad file would then make `build_boundaries` fail.

    Refactor step: I read the diff again and nothing needs changing. In `_model_entry`, both fields of each pair are checked against `None`, which the model's pair validator already guarantees. I kept it on purpose, because it narrows the types for mypy without a cast.

    Noticed, not touched: nothing.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 43 known, 0 gone
21. factory: started review as vm.
22. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (4 files under `src/`, 5 new test files) against criteria 1 to 8 and the Interface. The code matches the Interface. The domain module has no I/O, the adapter reads the file before `_RunFiles` is made, and the wiring only passes the setting on. I found no copy of an existing helper (no other env-name regex or `urlsplit` in `src/factory`), no security problem and no silencing marker. The tests for criteria 1 to 8 test what their criteria say. Group 1 still has two gaps, and I added a criterion for each:

    1. criterion 9 added: it needs its test. `tests/domain/test_opencode_provider.py::test_the_provider_file_is_accepted_only_when_it_keeps_every_rule` tests the `PositiveInt` bound of `context` (0 refused, 1 accepted) and the `NonNegativeFloat` bound of `input_cost` (-0.01 refused), but not the same bounds of `output` (no row with `output=0`) and `output_cost` (no row with `output_cost=-0.01`). Both bounds are stated in `OpencodeModel` in the Interface (`src/factory/domain/opencode_provider.py:31,34`), so each limit is tested on one side only. Fix: add the rows `_model(context=1, output=0)` refused and `_model(input_cost=1.0, output_cost=-0.01)` refused to that parametrized test. The accepted sides are already covered by `context-one` and `cost-zero`.
    2. criterion 10 added: it needs its test. The Interface says the `ValueError` of `read_provider` "names the first fault" (`src/factory/domain/opencode_provider.py:97-104`). The same test checks refused rows only with `pytest.raises(ValueError, match=r".")`, so a message that names nothing would pass. Fix: give each refused row (all but `not-an-object`) the name of the field at fault (`id`, `models`, `base_url`, `api_key_env`, `small_model`, `input_cost`, `output_cost`, `context`, `output`, `extra`) and match on it. As built, the messages already hold those names (for example `models.m.context: ...`, `models.m: Value error, input_cost and output_cost ...`), so no change under `src/` is needed.

    The closing criteria are renumbered to 11 (`make check`) and 12 (docs). I changed nothing else in the work item.

    Rejected: a finding on the claude-instance wiring row, which only checks the runtime's type. Criterion 8 asks only that the setting change nothing there, and the type check pins that.

    Earlier tests: the diff changes, renames or deletes no test file that `main` already holds (every test file has status `A`).

    The Description, the Interface and the docs criterion still match what was built.
23. factory: started doing as vm.
