---
stage: accept
pr: 188
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
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
2. intake: accepted
   - Interface: no new names. The table gives the exact detail text for each of the four items, with placeholders for the values. It also names the four tests to strengthen and the human's leave for that (FEATURE.md decision 16).
   - Criteria: each one is testable by one parametrized test. Criterion 1 covers the four single faults and the PATH+HOME pair. Criterion 2 covers four end reasons, each with and without an agent user. Criteria 3 and 4 pin the exact hosting-service and runtime-version details. Criterion 5 covers the passing side: the existing passing tests stay green. Every rule in the table has a case for the faulty side and the passing side.
   - Demo: both commands are runnable. Each Expect line is checkable: an exact string, and a pytest summary line with no failed, error or skipped count.
   - Architecture: the story touches only application-layer tests and one operator-guide paragraph. It needs no change in src and crosses no layer.
   - Scope: it is within the feature acceptance's follow-up on the survivors of F0013's mutants. It is not listed under the feature's Out of scope.
   Caveat: I did not read preflight.py or the four tests. The story itself says the code already behaves as the criteria state.
3. tester: I tightened the four existing tests that the Interface names, which the human allowed when they promoted this story. Each one now compares the whole detail string, where before it checked part of it with `in`. I did not create or change any other test.
   - criterion 1: tests/application/test_agent_environment_item.py::test_a_fault_in_the_environment_fails_with_its_detail. This was `..._fails_naming_it`. It has one row for each of the four single faults with the table's exact text (`{file}` stands for tmp_path/file in the HOME-not-a-directory row), plus a new row `neither-path-nor-home` expecting `the agent run has no PATH; the agent run has no HOME`.
   - criterion 2: tests/application/test_agent_run_probe.py::test_a_probe_that_does_not_complete_fails_with_its_detail. This was `..._naming_its_end_and_claude_p`. It crosses the four end reasons with agent_user `agent` / `None` (the second through `settings.model_copy`), expecting `... as agent to see why` and `... as the factory user to see why`.
   - criterion 3: tests/application/test_preflight.py::test_the_hosting_service_item_reports_a_failed_call. The name is unchanged; the `fails` row now compares the whole detail.
   - criterion 4: tests/application/test_preflight.py::test_the_version_item_fails_with_its_detail_when_the_versions_differ. This was `..._naming_both_versions_when_they_differ` and now compares the whole detail.
   - criterion 5: I left the existing passing tests of the three modules unchanged.
   Files changed: the three test modules above. No new files.
   Red/green: as the story expected, every module imports and the new tests pass already, because `src/factory/application/preflight.py` already produces these details. `make test` is green at 99.50 % coverage, and so is `make lint`. They are not red: they pin behaviour that already exists so that the mutants survivors die. The coder should not need to change anything in `src/`.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (27.7 s)
4. coder: I changed nothing in `src/`, as the story expected, so this round has no commits. `src/factory/application/preflight.py` already produces every detail in the Interface table. The four tests the tester tightened pass against the code as it stands.
      - Verified: `make check` is green (test: green, 99.50 % coverage; check: green). The first demo command prints `the agent run has no PATH; the agent run has no HOME`.
      - Refactor: none, because there is no diff to refactor.
      - Rejected: touching the detail texts in preflight.py. They already match the table, and the operator guide quotes them.
      - Open: the documenter still has to do criterion 7, adding the note about `the factory user` to the operator guide's paragraph "The probe of the agent run".

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Scope: the diff changes only three test modules. There are no changes in `src/`, which matches the coder's entry. I compared each new expected string with the text in `src/factory/application/preflight.py` (lines 149–277): the `"; ".join(faults)` call, the PATH and HOME faults, `agent_user or 'the factory user'`, and both hints.
      - Criterion 1: `tests/application/test_agent_environment_item.py::test_a_fault_in_the_environment_fails_with_its_detail` compares the whole detail. It has one row for each of the four single faults and the `neither-path-nor-home` row, all in one parametrized test.
      - Criterion 2: `tests/application/test_agent_run_probe.py::test_a_probe_that_does_not_complete_fails_with_its_detail` crosses the four end reasons with agent user `agent` and with `None` (through `model_copy`). Each case is checked against the exact detail.
      - Criteria 3 and 4: in `tests/application/test_preflight.py`, `test_the_hosting_service_item_reports_a_failed_call` and `test_the_version_item_fails_with_its_detail_when_the_versions_differ` now compare exactly the strings the criteria give.
      - Criterion 5: the passing tests of the three modules are unchanged and still pass, so each item still passes on a ready machine.
      - Criterion 6: the coder's entry reports `make check: check: green`. `make duplicates` reports 0 new.
      - The test changes stay within the human's leave as the Interface states it: only the four named tests changed, plus the renames it allows.
      - Architecture and security: nothing changed in `src/`, and no suppression markers were added.
      - Quality: no findings.
      - Ticket hygiene: `Assignment` matches what was built. Criterion 7 (the docs criterion) is still open and goes to the documenter.
6. documenter: changed `docs/operator-guide.md`, paragraph "The probe of the agent run". It now says that without `FACTORY_AGENT_USER` the detail names `the factory user` in place of the agent user (criterion 7). No other file changed.
   - Cross-read: the operator guide's "The preflight's items" and the probe paragraph against the diff and the Interface table. The other details (agent-environment, hosting-service, agent-runtime-version) are already quoted or described and stay as they are. The diff is tests only; `src/` is unchanged, so no code finding.
   - Not run: only documents changed, so I did not run `make check`. The factory runs it next.
   - Stale but unrelated: nothing seen.

   `make check`: check: green
   `make documents`: documents ok
7. demo: I ran both demo commands from the repository root, exactly as written. Both met their `Expect:` lines and there are no findings.

   1. The `agent_environment_item` call with an empty environment:
   ```
   the agent run has no PATH; the agent run has no HOME
   ```
   Met the expectation: this is exactly `the agent run has no PATH; the agent run has no HOME` (exit 0).

   2. pytest over the three test modules:
   ```
   ....................................                                     [100%]
   36 passed in 0.65s
   ```
   Met the expectation: the last line is `36 passed in 0.65s`, with no failed, error or skipped count (exit 0).

   Criteria checked against the demo:
   - Criterion 1: the demo's output is the both-faults detail.
   - Criteria 1–5: the tests that pin these criteria (the tester's entry names them) are among the 36 that passed.
   - Criterion 7: I read the paragraph "The probe of the agent run" in `docs/operator-guide.md`. At line 282 it now says that without `FACTORY_AGENT_USER` the detail names `the factory user`.
   - No criterion is contradicted.
   - Criterion 6 (`make check`) is the factory's gate; I did not run it in this stage.
