---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 489
comments_read: [6555129644]
handed_over: null
claim: null
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
- number: 7
  speaker: coder
  kind: question
  at: '2026-11-01T07:45:40.534074Z'
  stage: doing
  run: e8f5fe78616041d7a2bb7eb2237aaff5
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-11-01T07:47:58.601427Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-01T07:48:16.223334Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-01T07:48:34.762781Z'
  stage: doing
  run: 26f56bf6ce874a8f883fc9f558b228f1
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-01T07:48:55.362010Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-11-01T07:55:12.284295Z'
  stage: tests
  run: 1be3666fb34642d1bfc52e06a30c5841
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-01T07:55:32.594519Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-01T08:02:00.939912Z'
  stage: doing
  run: 515375dd3439490bbc2adb8a5881e6b9
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-01T08:02:21.546063Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-11-01T08:03:45.262366Z'
  stage: review
  run: d07051594d4747098c69b21f602a69d8
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-01T08:04:05.620135Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-01T08:04:22.183421Z'
  stage: doing
  run: 6e0de64de6a440a5bd8330c37051e66a
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-01T08:04:42.999254Z'
  stage: tests
- number: 20
  speaker: tester
  kind: result
  at: '2026-11-01T08:11:40.313727Z'
  stage: tests
  run: b8d1add6cac045c18d994dd30dd70054
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-01T08:12:00.933740Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-11-01T08:18:28.971037Z'
  stage: doing
  run: 1523aa7440f0432494733a7ae3f124f4
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-01T08:18:49.583149Z'
  stage: review
- number: 24
  speaker: reviewer
  kind: result
  at: '2026-11-01T08:19:32.600680Z'
  stage: review
  run: ab819fda771448da88c6cbf2cdfdc289
- number: 25
  speaker: factory
  kind: started
  at: '2026-11-01T08:19:52.996296Z'
  stage: docs
- number: 26
  speaker: documenter
  kind: result
  at: '2026-11-01T08:20:35.146122Z'
  stage: docs
  run: 749c6db198214540a1708e5b0ab53ec0
- number: 27
  speaker: factory
  kind: started
  at: '2026-11-01T08:20:55.428461Z'
  stage: smoke-test
- number: 28
  speaker: smoke-tester
  kind: result
  at: '2026-11-01T08:21:20.139884Z'
  stage: smoke-test
  run: 0dada2b3cf664a538bc90630bf8ceb95
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
7. coder: I stopped because an earlier test conflicts with the Interface. The code is done and is in the working tree. `make check` is red on that one earlier test only.

   Built, in `src/factory/adapters/opencode_runtime.py` only:
   - `LOCKDOWN_SWITCHES` holds the three opencode switches, each with the value `1`.
   - `_provider_keys` now returns `{**provider_configuration(provider), "enabled_providers": [provider.id]}`. The domain `provider_configuration` is unchanged, as the Interface says.
   - `_process_request` builds `{CONFIG_VARIABLE: ..., **SWITCHES, **lockdown}`. `lockdown` is `LOCKDOWN_SWITCHES` when a provider file is set and `{}` otherwise. The same dictionary goes to `run_launch` and to `container_launch`, so the runtime's values win over the request's and the resume gets the same values.

   All tests in `tests/adapters/test_opencode_runtime_lockdown.py` pass.

   The conflict: `tests/adapters/test_opencode_runtime_provider.py::test_a_provider_file_adds_its_keys_beside_the_existing_ones` (line 62, from F0046-S0001) fails. It expects the configuration to be exactly `{**request_configuration(), **CONFIGURATION}`. The Interface and criterion 2 require the extra key `enabled_providers: ["corp"]` there. The Description also says "The existing opencode runtime tests pass unchanged", which cannot hold together with criterion 2. Failure from the run: `AssertionError: assert {'autoupdate'...low'}}}}, ...} == {'autoupdate'...low'}...` at `tests/adapters/test_opencode_runtime_provider.py:62`.

   Options:
   (a) The tester adds `"enabled_providers": ["corp"]` to that test's expected dictionary. I would choose this. `CONFIGURATION` in `tests/opencode_provider_support.py` stays as it is, because it is the domain function's output.
   (b) The tester instead adds the key to `CONFIGURATION`. That would break the domain tests of `provider_configuration`, which the Interface keeps unchanged.
   (c) Drop the key from the runtime. That goes against criterion 2 and the feature's decision 14.

   I cannot change the test myself (R9), and the coder's `tests` decision needs your answer first. With (a), I will end the next run with `tests` and name that change.

   Refactor: the diff is three small edits, so nothing needed changing.

   Noticed but not touched: nothing else.
8. 2026-11-01 human: Answer: (a). The tester adds `"enabled_providers": ["corp"]` to the expected dictionary of `tests/adapters/test_opencode_runtime_provider.py::test_a_provider_file_adds_its_keys_beside_the_existing_ones`; `CONFIGURATION` in `tests/opencode_provider_support.py` stays the domain function's output. The leave covers that expectation and nothing else in the file; the Description's "pass unchanged" was written before criterion 2 met that test. End with `tests` and name the change.
9. factory: started doing as vm.
10. coder: The human chose (a), so this goes to the tester for one test change. I changed no code in this run. The code from the last run is already committed in `src/factory/adapters/opencode_runtime.py`: `LOCKDOWN_SWITCHES`, the `enabled_providers` key from `_provider_keys`, and the switches added in `runtime_environment` only when a provider file is set.

    The change for the tester: in `tests/adapters/test_opencode_runtime_provider.py::test_a_provider_file_adds_its_keys_beside_the_existing_ones`, add `"enabled_providers": ["corp"]` to the expected dictionary, so it becomes `{**request_configuration(), **CONFIGURATION, "enabled_providers": ["corp"]}`. Leave `CONFIGURATION` in `tests/opencode_provider_support.py` unchanged; it stays the domain function's output.

    What the journal changed: the Description's line "The existing opencode runtime tests pass unchanged" now has this one exception, the expectation above. My write paths do not include the work item, so I have not rewritten the Description.

    `make check` is still red on that one test, as in the last run, until the tester makes the change. Noticed but not touched: nothing else.
11. factory: started tests as vm.
12. tester: I made the one test change that the human approved in entry 8 and that the coder named in entry 10. Nothing else changed.

    - The change: in `tests/adapters/test_opencode_runtime_provider.py::test_a_provider_file_adds_its_keys_beside_the_existing_ones`, the expected dictionary gets `"enabled_providers": ["corp"]`. It is now `{**request_configuration(), **CONFIGURATION, "enabled_providers": ["corp"]}`.
    - Why: criterion 2 and the Interface add `enabled_providers` to the configuration whenever a provider file is set. The old expectation did not allow for that key.
    - Left as it was: `CONFIGURATION` in `tests/opencode_provider_support.py` is unchanged and stays the domain function's output. The rest of the file is untouched, as the human's leave allows.

    Criterion mapping: unchanged from entry 5. This run created no files. The earlier test file I changed is `tests/adapters/test_opencode_runtime_provider.py`, and the human's answer in entry 8 is the leave for it.

    `make test` passed: `test: green (175.5 s)`, coverage 99.56 %. Every module imported.

    Open: the Description still says "The existing opencode runtime tests pass unchanged". Entry 8 makes this test the one exception. I did not rewrite that line in this run, because this mode allows only the named test change.

    `lint`: lint: green (0.2 s)
    `test`: test: green (175.9 s)
13. factory: started doing as vm.
14. coder: `make check` is green: `check: green`, `test: green (175.2 s)`, coverage 99.56 %. The tester's change to the expectation in entry 12 cleared the one red test. I changed no code in this run. The code from the first doing run is already committed, and it is all in `src/factory/adapters/opencode_runtime.py`:
    - `LOCKDOWN_SWITCHES` holds the three opencode switches (`OPENCODE_DISABLE_MODELS_FETCH`, `OPENCODE_DISABLE_AUTOUPDATE` and `OPENCODE_DISABLE_DEFAULT_PLUGINS`), each with the value `1`. A comment above it says why they apply only with a provider file.
    - `_provider_keys` returns `{**provider_configuration(provider), "enabled_providers": [provider.id]}`. The domain `provider_configuration` is unchanged.
    - `_process_request` builds `{CONFIG_VARIABLE: ..., **SWITCHES, **lockdown}`. `lockdown` is `LOCKDOWN_SWITCHES` when a provider file is set and `{}` otherwise.

    Main choice: the switches are added in one place, the single `runtime_environment` dictionary that both `run_launch` and `container_launch` receive. That one place gives the same values on the host, in a container and in the budget resume, and the runtime's values win over the request's. Rejected: adding the switches separately in each launch path. That would have meant two copies to keep in step, and the resume could have drifted from the first call.

    Refactor: I read the diff again (three small edits) and nothing needed changing.

    What the journal changed: entry 8 makes `tests/adapters/test_opencode_runtime_provider.py::test_a_provider_file_adds_its_keys_beside_the_existing_ones` an exception to the Description's line "The existing opencode runtime tests pass unchanged". My write paths do not include the work item, so I have not rewritten the Description.

    Noticed but not touched: nothing.

    `check`: check: green
    `duplicates`: duplicates: 1 new, 41 known, 1 gone
15. factory: started review as vm.
16. reviewer: Review, round 0. Groups 1 to 3 pass. Group 1: every criterion and every Interface rule has a test that checks it. That covers the exact `LOCKDOWN_SWITCHES`, the `{}` from `_provider_keys` without a file, host and container, the override with and without a file over all three switches, the resume, and the refused file. Entry 14 records `check: green`. Group 2: the change stays in `factory.adapters.opencode_runtime`, and the domain `provider_configuration` is untouched. Group 3: nothing to report, and the diff adds no silencing marker. In `src/` the change is clean: the switches are added once, in the dictionary that the host launch, the container launch and the resume all share. `make duplicates` shows `1 new, 41 known, 1 gone`. The new entry is a relabel of `__call__` in `src/factory/adapters/oauth_token.py:27` (method -> function), which is not in this diff. Group 4 fails on the new test module. Because this is round 0, these points count as findings:

    1. `tests/adapters/test_opencode_runtime_lockdown.py:36` `_runtime`: it copies the body of `stand_in_runtime` in `tests/adapters/opencode_stand_in.py:253` (write_opencode, state folder, `OpencodeRuntime(..., models=MODELS, ...)`). Fix: the tester extends `stand_in_runtime` with keyword parameters `provider_file` and `containers` and uses it here instead of a local copy.
    2. `tests/adapters/test_opencode_runtime_lockdown.py:56` `_configuration_text`: it copies `_configuration_text` of `tests/adapters/test_opencode_runtime_provider.py:38` (`call.files[call.environment[CONFIG_VARIABLE]]`). Fix: move one helper, taking a `StandInCall`, into `tests/adapters/opencode_stand_in.py` under the standing leave, and use it from both modules, each earlier test keeping its name and what it checks.
    3. `tests/adapters/test_opencode_runtime_lockdown.py:33` `HOST_ENVIRONMENT`: it copies the default environment that `opencode_request` writes inline at `tests/adapters/opencode_stand_in.py:227`. Fix: name that default once as a constant in `tests/adapters/opencode_stand_in.py`, let `opencode_request` use it, and import it here.

    Group 5 was not reached. Its point is found already, so the next round need not find it: the Interface line "The existing opencode runtime tests pass unchanged" is stale since the human's answer in entry 8. I did not change it, because my correction covers only the Description.

    Earlier tests:
    - `tests/adapters/test_opencode_runtime_provider.py`: the standing leave covers moving `_base_configuration` to `request_configuration` in `tests/adapters/opencode_stand_in.py` (same body, every test keeps its name). The human's answer in entry 8 covers the added `"enabled_providers": ["corp"]` expectation in `test_a_provider_file_adds_its_keys_beside_the_existing_ones`.
    - `tests/adapters/opencode_stand_in.py`: covered by the standing leave. It is the shared place that receives the moved `request_configuration`, it only gains that function and its imports, and no existing helper changed.
17. factory: started doing as vm.
18. coder: All three review findings (entry 16) are copied test helpers in the new test module, so this round goes to the tester. `CLAUDE.md` gives standing leave to move a shared test helper, and the tester makes that move, not the coder. I changed no code. The source in `src/factory/adapters/opencode_runtime.py` is the same as in entry 14, where `make check` was green.

    The changes for the tester, each covered by the standing leave:
    1. `tests/adapters/test_opencode_runtime_lockdown.py:36` `_runtime` repeats the body of `stand_in_runtime` in `tests/adapters/opencode_stand_in.py:253`. Give `stand_in_runtime` the keyword parameters `provider_file` and `containers`. Use it in the lockdown module and delete the local copy.
    2. `tests/adapters/test_opencode_runtime_lockdown.py:56` `_configuration_text` is a copy of `_configuration_text` in `tests/adapters/test_opencode_runtime_provider.py:38`. Move one helper that takes a `StandInCall` into `tests/adapters/opencode_stand_in.py` and use it from both modules. The earlier test file to change is `tests/adapters/test_opencode_runtime_provider.py`. Every test there keeps its name and checks the same thing.
    3. `tests/adapters/test_opencode_runtime_lockdown.py:33` `HOST_ENVIRONMENT` copies the default environment that `opencode_request` writes inline at `tests/adapters/opencode_stand_in.py:227`. Name that default once as a constant in `tests/adapters/opencode_stand_in.py`, have `opencode_request` use it, and import it in the lockdown module.

    What I built (from earlier rounds, unchanged): `LOCKDOWN_SWITCHES` and `_provider_keys` (now adding `enabled_providers`) in `src/factory/adapters/opencode_runtime.py`. The switches go into the one `runtime_environment` dictionary that the host launch, the container launch and the budget resume share. The alternative I rejected was adding the switches separately in each launch path.

    What the journal changed: after entry 8, the Description's line "The existing opencode runtime tests pass unchanged" is out of date (the reviewer named this too). My write paths do not include the work item, so I have not rewritten it.

    Noticed but not touched: `make duplicates` reports one new entry, a relabel of `__call__` in `src/factory/adapters/oauth_token.py:27`, which is outside this diff.
19. factory: started tests as vm.
20. tester: I moved the three copied helpers that the reviewer found (entry 16) and the coder named (entry 18). The standing leave in `CLAUDE.md` covers these moves. I changed no assertion, and every test keeps its name and checks the same thing.

    1. `stand_in_runtime` in `tests/adapters/opencode_stand_in.py` gained the keyword parameters `provider_file: Path | None = None` and `containers: ContainerRuns | None = None`, and passes both to `OpencodeRuntime`. The local `_runtime` copy in `tests/adapters/test_opencode_runtime_lockdown.py` is gone. Its tests now call `stand_in_runtime(tmp_path, [REPLY], provider_file=..., containers=...)`, and the resume test calls it with `[over_budget(), RESUME_REPLY]`.
    2. The new helper `configuration_text(call: StandInCall) -> str` in `tests/adapters/opencode_stand_in.py` replaces `_configuration_text` in the lockdown module. In `tests/adapters/test_opencode_runtime_provider.py`, the private `_configuration_text(tmp_path)` still reads the one call and now returns `configuration_text(call)`. The import of `CONFIG_VARIABLE` there, no longer needed, was removed.
    3. The new constant `REQUEST_ENVIRONMENT` in `tests/adapters/opencode_stand_in.py` holds the default that `opencode_request` used to write inline, and `opencode_request` now uses it. The lockdown module imports it in place of its own `HOST_ENVIRONMENT`.

    Criterion mapping: the same as entry 5, with the same test names. This run created no files. The files changed are `tests/adapters/opencode_stand_in.py` (shared support module), `tests/adapters/test_opencode_runtime_lockdown.py` (this story's tests) and `tests/adapters/test_opencode_runtime_provider.py` (an earlier story's tests, under the standing leave). Every module imported.

    `make lint`: `lint: green (0.2 s)`. `make test`: `test: green (175.9 s)`, coverage 99.56 %. I did not run `make types`; the coder's `make check` covers it.

    Open, as the reviewer noted: the Description's line "The existing opencode runtime tests pass unchanged" is out of date since entry 8. This mode allows only the named test change, so I did not rewrite it.

    `lint`: lint: green (0.2 s)
    `test`: test: green (174.6 s)
21. factory: started doing as vm.
22. coder: Round 1. The tester's helper moves (entry 20) settle the three review findings from entry 16. All three were test-only, so I changed no code in this run. `make check` is green: `test: green (174.8 s)`, coverage 99.56 %, `check: green`.

    What I built (committed in earlier runs, all in `src/factory/adapters/opencode_runtime.py`):
    - `LOCKDOWN_SWITCHES` holds the three opencode switches, each set to `1`.
    - `_provider_keys` now adds `enabled_providers: [provider.id]` to the domain's `provider_configuration`. The domain function itself is unchanged.
    - `_process_request` builds the single `runtime_environment` dictionary as `{CONFIG_VARIABLE: ..., **SWITCHES, **lockdown}`. `lockdown` is `LOCKDOWN_SWITCHES` when a provider file is set and `{}` otherwise.

    Main choice: the switches go in that one dictionary, which the host launch, the container launch and the budget resume all receive. So the values are the same on every path, and the runtime's values override the request's. Rejected: adding the switches separately in each launch path. That would leave two copies to keep in step, and the resume could drift from the first call.

    Refactor: no code changed this round, so there was nothing to refactor.

    What the journal changed: since entry 8, the Description's line "The existing opencode runtime tests pass unchanged" has one exception, the expectation in `tests/adapters/test_opencode_runtime_provider.py::test_a_provider_file_adds_its_keys_beside_the_existing_ones`. My write paths do not include the work item, so I did not rewrite the Description.

    Noticed but not touched: `make duplicates` reported one new finding in entry 14, a relabel of `__call__` in `src/factory/adapters/oauth_token.py:27`. That file is outside this diff.

    `check`: check: green
    `duplicates`: duplicates: 1 new, 41 known, 1 gone
23. factory: started review as vm.
24. reviewer: Review, round 1: no findings.

    I read the diff (`git diff main...HEAD -- . ':!factory'`) and the work item.

    - Group 1, acceptance criteria. Each criterion has a test in `tests/adapters/test_opencode_runtime_lockdown.py` that checks what it says.
      - Criterion 1: rows for the host and the container. The environment must match exactly, and the configuration text must equal `json.dumps(request_configuration())`. That also covers `_provider_keys` giving `{}` without a provider file.
      - Criterion 2: rows for `corp` and `corp-1`. The keys must be exactly the seven named, with no `disabled_providers`.
      - Criterion 3: host and container rows, each checked as the earlier environment plus the three switches and nothing more. The test also checks that `LOCKDOWN_SWITCHES` is exactly the dict the Interface gives.
      - Criterion 4: the override rule is tested on both sides (`1` with a provider file, `0` without one) for all three switches.
      - Criterion 5: the budget resume gets the same environment and the same configuration as the first call.
      - Criterion 6: a refused file raises `AgentRuntimeError`, the stand-in is never called, and no `opencode-*.json` is written.
      - Entry 22 records `check: green`.
    - Group 2, architecture. The change stays inside `factory.adapters.opencode_runtime`, and the domain `provider_configuration` is untouched.
    - Group 3, security. Nothing to report, and the diff adds no silencing marker.
    - Group 4, quality. The source change is clean (`src/factory/adapters/opencode_runtime.py:74`, `:313`, `:681`). The switches are added once, in the one `runtime_environment` dict that the host launch, the container launch and the resume all share. The comment above `LOCKDOWN_SWITCHES` says why they depend on the provider file. The three round-0 findings are fixed: `_runtime` is gone in favour of `stand_in_runtime(..., provider_file=, containers=)`, `configuration_text` is shared, and `REQUEST_ENVIRONMENT` is shared. `make duplicates` reports `1 new`, which is in `src/factory/adapters/oauth_token.py:27`, outside this diff.
    - Group 5, work item. The `## Description` matches what was built, and criterion 8 still describes what the documenter must write.

    Open, not a finding: the Interface's line "The existing opencode runtime tests pass unchanged" has one exception since the human's answer in entry 8. The journal records that answer. My corrections may only touch the Description, so I left the line as it is.

    Earlier tests:
    - `tests/adapters/test_opencode_runtime_provider.py`. Two leaves cover it:
      - the human's answer in entry 8 covers the added `"enabled_providers": ["corp"]` expectation in `test_a_provider_file_adds_its_keys_beside_the_existing_ones`;
      - the standing leave covers moving `_base_configuration` to `request_configuration` and having `_configuration_text` use the shared `configuration_text`. Every test keeps its name and what it checks.
    - `tests/adapters/opencode_stand_in.py`. The standing leave covers it. This is the shared place that received `request_configuration`, `configuration_text` and the `REQUEST_ENVIRONMENT` constant, which `opencode_request` now uses with the same behaviour. `stand_in_runtime` gained two optional keyword parameters that default to `None`, so every earlier caller gets the same runtime.
25. factory: started docs as vm.
26. documenter: Docs, round 1: I wrote the documentation criterion 8 asks for. I changed only documents, so I did not run `make check`; the factory's checks after this stage decide. I ran no example, because I wrote none.

    Files changed:
    - `docs/operator-guide.md`, *A company's provider*: new paragraph *What opencode may load and contact*. It covers `enabled_providers` (and no `disabled_providers`), the three switches, and that the runtime's values override the request's. It says only `OPENCODE_DISABLE_MODELS_FETCH` changes traffic, why all of this depends on the provider file, and that `registry.npmjs.org` is still contacted. It says a deployment that must prove no vendor traffic reads the proxy's log or runs the startup probe of `planning/cloud-sandbox/`.
    - `docs/project-guide/agents.md`, *The opencode runtime*: I added `enabled_providers` to the per-run configuration keys. I added the switches to the call's environment sentence. I added `_provider_keys` adding the key, and a new paragraph *The lockdown switches* (one `runtime_environment` dict for host, container and resume; the override rule).
    - `docs/decisions.md`: new entry *opencode loads and contacts only what the company provider needs*, from decision 14, with its rejected alternatives.
    - `README.md`: none, as the criterion says.

    I checked the diff of `src/factory/adapters/opencode_runtime.py` (`LOCKDOWN_SWITCHES`, `_provider_keys`, `_process_request`). It matches the Interface and what I wrote. I found nothing for the coder.

    Cross-read and found current: the `FACTORY_OPENCODE_PROVIDER_FILE` row of the operator guide's configuration table, the *Running on opencode* section, the container-environment paragraph of `agents.md` (line 30, still true), and the *A company's provider for opencode* decision (the provider-file part is unchanged).

    Stale text not mine to fix: the work item's Interface line "The existing opencode runtime tests pass unchanged" has one exception since the human's answer in entry 8. The reviewer and coder both noted it. The work item is not in my write paths.

    `check`: check: green (not run again: passed on tree f9fde96ff742 at 2026-11-01T08:15:22Z)
    `secrets`: secrets: green (2.4 s)
    `documents`: documents ok
27. factory: started smoke-test as vm.
28. smoke-tester: Ran the two commands under `## Smoke test` from the repository root, in order, as written. Fixed nothing.

    Command 1:
    ```bash
    uv run python -c "
    from factory.adapters.opencode_runtime import LOCKDOWN_SWITCHES
    print(sorted(LOCKDOWN_SWITCHES))
    "
    ```
    Output (exit 0):
    ```
    Bytecode compiled 4164 files in 58ms
    ['OPENCODE_DISABLE_AUTOUPDATE', 'OPENCODE_DISABLE_DEFAULT_PLUGINS', 'OPENCODE_DISABLE_MODELS_FETCH']
    ```
    Met `Expect:`. The program printed exactly the expected line. The `Bytecode compiled` line comes from uv on stderr, not from the program.

    Command 2:
    ```bash
    uv run pytest tests/adapters/test_opencode_runtime_lockdown.py 2>&1 | tail -1
    ```
    Output (pytest exit 0):
    ```
    14 passed in 0.27s
    ```
    Met `Expect:`. The last line says `passed` and does not say `failed` or `error`.

    Acceptance criteria re-read: the smoke test contradicts none of them. Criteria 1 to 6 are covered by the 14 passing lockdown tests. For the docs criterion (8) I checked that the named sections exist: `docs/operator-guide.md` has the paragraph *What opencode may load and contact* (lines 330–331), which covers the allowlist key, the three switches, why they depend on the provider file, and the proxy log or startup probe. `docs/project-guide/agents.md` names the keys and the switches (lines 108–112). `docs/decisions.md` has the entry *opencode loads and contacts only what the company provider needs* (line 1312). I did not run `make check` (criterion 7) because it is the factory's gate.

    Findings: none.
