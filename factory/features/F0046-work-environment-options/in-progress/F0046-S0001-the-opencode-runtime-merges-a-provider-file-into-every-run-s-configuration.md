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
3. `read_provider` accepts a complete file and refuses each fault, rows of one parametrized test: `id` `Corp` and `1corp` refused, `corp-1` accepted; empty `models` refused, one entry accepted; a blank model key refused; `base_url` `ftp://x`, `https://` and `example.invalid` refused, `https://example.invalid/v1` and `http://example.invalid` accepted; `api_key_env` `lower` and `1KEY` refused, `PROXY_KEY` accepted; `small_model` `other/m`, `corp` and `corp/missing` refused, `corp/m` accepted; `input_cost` without `output_cost` and `context` without `output` refused; a cost of `-0.01` refused and `0` accepted; `context` of `0` refused and `1` accepted; an unknown key at the top and in a model refused; JSON that is not an object refused.
4. `provider_configuration` of a provider with one model that has a name, limits and prices gives exactly `{"provider": {"corp": {"npm": "@ai-sdk/openai-compatible", "options": {"baseURL": "https://example.invalid/v1", "apiKey": "{env:PROXY_KEY}"}, "models": {"m": {"name": "M", "limit": {"context": 1000, "output": 100}, "cost": {"input": 3.0, "output": 15.0}}}}}, "small_model": "corp/m"}`; a model with none of the three optional groups is `{}`.
5. With a valid file, the run's configuration file holds the keys of criterion 4 beside `autoupdate`, `share`, `snapshot` and `agent`, and the agent's entry is as without the file.
6. A missing file, a directory in its place and an invalid file each end the run with `AgentRuntimeError` whose message starts `cannot use the opencode provider file <path>:`; the stand-in is not started and no `opencode-*.json` is in the state directory.
7. A request whose agent model is `corp/m` is passed as `--model corp/m`; an alias in `models` that maps to `corp/m` gives the same words.
8. `build_boundaries` on an opencode instance with the setting gives a runtime that merges the file (the wiring test reads the configuration of one run); on a Claude Code instance the setting changes nothing.
9. `make check` stays green.
10. docs: `docs/operator-guide.md`: a subsection under the opencode runtime, *A company's provider*, with the variable's row in the configuration table, an example file written with `example.invalid` and made-up ids, the rule that the key stays in `FACTORY_API_LOGIN_FILE` and is named as `api_key_env: ANTHROPIC_API_KEY`, the small model, and the note that a model without prices is costed at 0 so the budget stop does not fire. The same chapter's passage on a login that an operator's own build keeps in the agent's home is corrected: on the machine the home lies on the dataset and is rolled back, so only the API login file works; the sentence that all three secret files must exist whatever the runtime is made exact for opencode (the file `claude-token` may be empty). `docs/project-guide/agents.md`, *The opencode runtime*: the setting, the module and the merge rule. `docs/decisions.md`: an entry *A company's provider for opencode*, from the feature's decisions 1 to 5 and 9. `README.md`: none.

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
