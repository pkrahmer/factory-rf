# The preflight's details pinned in full

<!-- proposed by feature acceptance of 2026-10-17; refine before promoting -->

## Assignment (as of log entry 1)

F0013's feature acceptance ran `make mutants FEATURE=F0013` over `src/factory/application/preflight.py`: 379 of 394 mutants were killed, and every mutant of the token item F0013-S0002 rewrote was among them. The 15 survivors are in the items F0013 did not change, and most of them change the text of a failed item's detail: `"; ".join(faults)` becomes `"XX; XX".join(faults)` in `agent_environment_item`; `"the agent run has no PATH"` and `"the agent run has no HOME"` are upper-cased or wrapped in `XX`; `settings.agent_user or 'the factory user'` becomes `and` in `agent_run_probe_item`; and the hints `check the token and the network` (`MachineChecks._hosting_service`) and `rebuild the image or change the pinned version` (`MachineChecks._agent_runtime_version`) are changed. All of these survive because the tests check a part of the detail with `in`. The detail is what the operator reads in the `preflight_failed` stop, and `docs/operator-guide.md` ("The preflight's items") quotes these texts. This story pins the whole detail of those four items, both faults of `agent-environment` together included, and the probe's detail without an agent user. The code already behaves as the criteria say. The tester strengthens four existing tests, which needs the human's leave (see Interface); the coder expects to change nothing in `src/`.

## Interface

No new or changed names. The details pinned, in `factory.application.preflight`:

| Item | Case | Detail |
|---|---|---|
| `agent-environment` | no `PATH` | `the agent run has no PATH` |
| `agent-environment` | `PATH` without `factory-guard` | `factory-guard is not on the agent run's PATH <path>` |
| `agent-environment` | no `HOME` | `the agent run has no HOME` |
| `agent-environment` | `HOME` not a directory | `the agent run's HOME <home> is no directory` |
| `agent-environment` | a `PATH` fault and a `HOME` fault | the `PATH` fault, `; `, the `HOME` fault |
| `agent-run-probe` | the run ends `<reason>`, agent user `<user>` set | `the probe run ended <reason>; run claude -p by hand as <user> to see why` |
| `agent-run-probe` | the run ends `<reason>`, no agent user | `the probe run ended <reason>; run claude -p by hand as the factory user to see why` |
| `hosting-service` | the call fails with `HostingServiceError(<operation>, <detail>)` | `the hosting service failed <operation>: <detail>; check the token and the network` |
| `agent-runtime-version` | the runtime reports `<reported>`, the image pins `<pinned>` | `the agent runtime reports <reported>, the image pins <pinned>; rebuild the image or change the pinned version` |

Tests, by the human's leave when this story is promoted (it changes tests of earlier stories; the alternative, a new module, would copy the fixtures of three modules): in `tests/application/test_agent_environment_item.py`, `test_a_fault_in_the_environment_fails_naming_it` compares the whole detail and gains a row with neither `PATH` nor `HOME`; in `tests/application/test_agent_run_probe.py`, `test_a_probe_that_does_not_complete_fails_naming_its_end_and_claude_p` compares the whole detail and gains rows with `agent_user=None`; in `tests/application/test_preflight.py`, `test_the_hosting_service_item_reports_a_failed_call` and `test_the_version_item_fails_naming_both_versions_when_they_differ` compare the whole detail. Each test's name may change to say "with its detail"; nothing else in the three modules changes.

## Acceptance criteria

1. `agent_environment_item` fails with exactly the detail of the table for each of its four single faults (rows of one parametrized test), and, for an environment with neither `PATH` nor `HOME`, with `the agent run has no PATH; the agent run has no HOME`.
2. `agent_run_probe_item`, for a run that ends `died`, `no_result`, `time_limit` or `budget`, fails with `the probe run ended <reason>; run claude -p by hand as agent to see why` when the settings' agent user is `agent`, and with `... as the factory user to see why` when it is `None` (rows of one parametrized test).
3. The `hosting-service` item, after `FakeHostingService.fail_next("find_open_pull_request")`, fails with exactly `the hosting service failed find_open_pull_request: injected failure; check the token and the network`.
4. The `agent-runtime-version` item, for a runtime that reports `2.1.290` and a pin of `2.1.289`, fails with exactly `the agent runtime reports 2.1.290, the image pins 2.1.289; rebuild the image or change the pinned version`.
5. What must still hold: each of the four items passes on a ready machine (the existing passing tests of the three modules pass).
6. `make check` stays green.
7. docs: the operator guide's paragraph "The probe of the agent run" says that without `FACTORY_AGENT_USER` the detail names `the factory user`; every other detail of the table is already quoted in "The preflight's items" and stays as it is.

## Demo

```bash
uv run python -c "
from pathlib import Path
from factory.application.preflight import agent_environment_item
print(agent_environment_item({}, lambda name, path: None, Path.is_dir).detail)
"
```
Expect: `the agent run has no PATH; the agent run has no HOME`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_agent_environment_item.py tests/application/test_agent_run_probe.py tests/application/test_preflight.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 feature acceptance of F0013: proposed.
