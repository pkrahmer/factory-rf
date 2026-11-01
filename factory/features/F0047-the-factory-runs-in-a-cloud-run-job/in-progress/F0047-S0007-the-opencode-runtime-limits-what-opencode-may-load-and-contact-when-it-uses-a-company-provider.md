---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 489
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-01T07:42:03.277699Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-01T07:33:16.150907Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-01T07:33:16.157018Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-01T07:33:37.174889Z'
  stage: intake
  run: 9490a9afc68e4e189f974a21b6389fdd
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-01T07:33:57.390775Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-01T07:41:40.868710Z'
  stage: tests
  run: 5741642678d945dfb60980cdc8060f30
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-01T07:42:03.277699Z'
  stage: doing
---

# The opencode runtime limits what opencode may load and contact when it uses a company provider

## Description

With a provider file (F0046-S0001) opencode runs against the company's model API, but it still loads its whole catalogue of providers, fetches the public model list at start, may update itself and loads its default plugins. A company build of opencode closes those doors (a provider allowlist, no traffic to the vendor, no updater); the factory runs upstream opencode, which has switches for the same, and does not set them. This story sets them, only when a provider file is given, so that the VM path and every run without the file are unchanged. With the file the per-run configuration gains `enabled_providers` (only the file's provider id), `disabled_providers` is not written, and the call's environment gains `OPENCODE_DISABLE_MODELS_FETCH=1`, `OPENCODE_DISABLE_AUTOUPDATE=1` and `OPENCODE_DISABLE_DEFAULT_PLUGINS=1`. The provider file already defines the models, so no fetch is needed. Measured on 2026-10-31 (`planning/cloud-sandbox/`, P14): opencode 1.19.3 accepts `enabled_providers` without complaint and the run works; without the switches every run contacts the vendor's catalogue host `models.opencode.ai` once, with them it does not (`OPENCODE_DISABLE_MODELS_FETCH` is the switch that does it; the other two changed nothing observable in that task and stay as upstream's guards); `registry.npmjs.org` is contacted at the start of every run either way, most likely for the provider's npm package, and no switch removes it. Unchanged: the default configuration and environment (byte for byte), the Claude Code runtime, the login shell, the preflight. Left out: an opencode that reads a model file offline (not needed), and a stage image that pre-installs the provider's package so that a run contacts no registry (a candidate after this feature, `planning/v1.2-candidates.md`).

## Interface

`factory.adapters.opencode_runtime` (adapters):

- `LOCKDOWN_SWITCHES: dict[str, str]` = `{"OPENCODE_DISABLE_MODELS_FETCH": "1", "OPENCODE_DISABLE_AUTOUPDATE": "1", "OPENCODE_DISABLE_DEFAULT_PLUGINS": "1"}`.
- `_provider_keys` (the provider file's keys) gives, besides `provider` and `small_model`, the key `enabled_providers` with the one id `[<provider id>]`; without a provider file it gives `{}` as today. (`provider_configuration` in `factory.domain.opencode_provider` stays as it is; the runtime adds the key.)
- `runtime_environment` of a call is `{OPENCODE_CONFIG: <path>, **SWITCHES, **LOCKDOWN_SWITCHES}` when a provider file is set and `{OPENCODE_CONFIG: <path>, **SWITCHES}` otherwise. The same dictionary is used on the host and in a container (`run_environment`, `container_launch`), and by every call of one run, the budget resume included.
- A request environment entry with the name of a lockdown switch is overridden by the runtime's value (the runtime's switches come last, as `SWITCHES` do today).

Tests (the tester writes them): `tests/adapters/test_opencode_runtime_lockdown.py` (through `tests/adapters/opencode_stand_in.py`, which records the environment and the configuration file of each call). The existing opencode runtime tests pass unchanged.

## Acceptance criteria

1. Without a provider file the configuration file of a run and the environment of its call are exactly those of before this story (a row comparing both with the existing expectations; no key `enabled_providers`, none of the three switches).
2. With a provider file whose provider id is `corp` the configuration file holds `"enabled_providers": ["corp"]` beside `provider`, `small_model`, `autoupdate`, `share`, `snapshot` and `agent`, and no key `disabled_providers`; with the id `corp-1` it holds `["corp-1"]`.
3. With a provider file the call's environment holds the three switches with the value `1`, plus `OPENCODE_CONFIG` and `PYTHONDONTWRITEBYTECODE`, and nothing else the runtime did not set before; rows for a call on the host and a call in a container (the `--env` words of the launch).
4. A request environment that sets `OPENCODE_DISABLE_MODELS_FETCH=0` is overridden: the call's value is `1` with a provider file and `0` without one (the runtime does not touch what it does not own).
5. A budget resume after a first call stopped by its budget carries the same switches and the same configuration as the first call.
6. A provider file that is refused (an unknown key) still ends the run with `AgentRuntimeError` before any file is written, as before (no configuration file and no stand-in call).
7. `make check` stays green.
8. docs: `docs/operator-guide.md`, *A company's provider*: a paragraph *What opencode may load and contact*: the allowlist key, the three switches and why they depend on the provider file (without it opencode needs its public model list), and that a deployment that must prove no traffic to the vendor reads the proxy's log or runs the startup probe of `planning/cloud-sandbox/`. `docs/project-guide/agents.md`, *The opencode runtime*: the keys and the switches. `docs/decisions.md`: an entry *opencode loads and contacts only what the company provider needs*, from the feature's decision 14. `README.md`: none.

## Smoke test

```bash
uv run python -c "
from factory.adapters.opencode_runtime import LOCKDOWN_SWITCHES
print(sorted(LOCKDOWN_SWITCHES))
"
```
Expect: one line, `['OPENCODE_DISABLE_AUTOUPDATE', 'OPENCODE_DISABLE_DEFAULT_PLUGINS', 'OPENCODE_DISABLE_MODELS_FETCH']`

```bash
uv run pytest tests/adapters/test_opencode_runtime_lockdown.py 2>&1 | tail -1
```
Expect: a final pytest line that says `passed` and does not say `failed` or `error`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-11-01 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `factory.adapters.opencode_runtime` with `LOCKDOWN_SWITCHES` (exact dict), `_provider_keys` (it exists at opencode_runtime.py:298, and `SWITCHES` at line 73 and `runtime_environment` at line 675 are the places to extend) and the exact `runtime_environment` for both the provider-file and no-file cases. The override order (the runtime's switches come last) is stated.
   - Criteria: each fits one test function. Criterion 1 is the unchanged default. Criterion 2 covers `enabled_providers` for two ids (`corp`, `corp-1`) and the absent `disabled_providers`. Criterion 3 covers the environment on the host and in a container. Criterion 4 covers both sides of the override (`1` with a file, `0` without one). Criterion 5 covers the resume. Criterion 6 covers the refused file, with no file written. Criterion 4 names only `OPENCODE_DISABLE_MODELS_FETCH`; the Interface rule covers all three switches, so the tester should parametrize that row over `LOCKDOWN_SWITCHES`.
   - Smoke test: both commands are runnable. The pytest command passes no `-q`, and `pyproject.toml` `addopts` already sets `-q`, so `tail -1` gives the summary line the `Expect:` checks. The first `Expect:` is an exact line.
   - Architecture: the change stays in the adapters layer (the opencode wrapper), and the domain `provider_configuration` is left as it is. No new dependency and no change to `factory/`.
   - Scope: within feature F0047 (S0007 is listed in its scope, and decisions 13 and 14 match the Description). Nothing in "Out of scope" is touched. The docs criterion names the three documents and says the README gets nothing.
4. factory: started tests as vm.
5. tester: Wrote the tests for the lockdown of the opencode runtime. They go through `tests/adapters/opencode_stand_in.py` and its stand-in, which records the environment and the configuration file of each call.

   - criterion 1: tests/adapters/test_opencode_runtime_lockdown.py::test_without_a_provider_file_the_configuration_and_environment_are_as_before (rows `host` and `container`: the exact environment as before, without the three switches, and the configuration text equal to `json.dumps(request_configuration())`, so no `enabled_providers`)
   - criterion 2: tests/adapters/test_opencode_runtime_lockdown.py::test_a_provider_file_enables_only_its_own_provider (rows `corp` and `corp-1`: `enabled_providers == [id]`, the keys exactly the seven named, no `disabled_providers`)
   - criterion 3: tests/adapters/test_opencode_runtime_lockdown.py::test_a_provider_file_adds_the_lockdown_switches_to_the_call_s_environment (rows `host`, which reads the stand-in's environment without `LC_CTYPE`, and `container`, which reads the fake launch's environment, i.e. the `--env` words; the environment must be exactly the earlier one plus the three switches; it also checks that `LOCKDOWN_SWITCHES` equals the dict the Interface gives)
   - criterion 4: tests/adapters/test_opencode_runtime_lockdown.py::test_a_request_s_lockdown_switch_is_overridden_only_with_a_provider_file (parametrized over all three switches, as intake suggested from the Interface's override rule, times with and without a provider file: the value is `1` with the file and `0` without it)
   - criterion 5: tests/adapters/test_opencode_runtime_lockdown.py::test_a_budget_resume_carries_the_first_call_s_switches_and_configuration (`over_budget()` then `RESUME_REPLY`: both calls get the same environment, with the switches, and the same configuration text with `enabled_providers`)
   - criterion 6: tests/adapters/test_opencode_runtime_lockdown.py::test_a_refused_provider_file_fails_before_any_file_is_written (a provider file with an unknown key gives `AgentRuntimeError`; no stand-in call and no `opencode-*.json` in the state folder)
   - criteria 7 and 8: no test (`make check` is the factory's gate; docs belong to the docs stage).

   Files: created `tests/adapters/test_opencode_runtime_lockdown.py`. Under the standing leave to move a shared test helper, I moved `_base_configuration` out of `tests/adapters/test_opencode_runtime_provider.py` into `tests/adapters/opencode_stand_in.py` as `request_configuration()`. I changed the earlier test file `tests/adapters/test_opencode_runtime_provider.py` to use it from there: its imports changed, and every test keeps its name and checks the same thing.

   `make test`: the new module could not be imported (ImportError). `factory.adapters.opencode_runtime` exists, but `LOCKDOWN_SWITCHES` does not yet. That is the expected red. `make lint` is green. I skipped the type check, as this stage says.

   Open: nothing.

   `lint`: lint: green (0.2 s)
   `test`: ERROR tests/adapters/test_opencode_runtime_lockdown.py - ImportError while importing test module '/work/checkout/tests/adapters/test_opencode_runtime_lockdown.py'.
6. factory: started doing as vm.
