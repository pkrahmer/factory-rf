---
stage: demo
pr: 126
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The preflight's items

## Assignment (as of log entry 1)

Build the checks of the machine that the preflight runs: the tools are on the `PATH`, the hosting service answers, the agents are installed where `FACTORY_CLAUDE_HOME` points, and the agent runtime's version equals the version the image pins. Every item runs whatever the others found, so one report names everything that is wrong, and a failed report becomes one machine stop whose detail lists every failed item. A missing tool is reported and never worked around: nothing here installs anything. This covers ST5.3 (the preflight fails, naming both versions) and ST4.4 (the agents check finds the agents where `FACTORY_CLAUDE_HOME` points), implements part of R29 (the agent runtime is held to the pinned version), and keeps kept thing 8 (a missing tool is reported, never worked around) and kept thing 18 (the machine and its preflight). The items are built here; the next two stories add the stamp and the probe of the main branch and wire the preflight into the tick. v1's item for the git identity is not rebuilt: `GitIdentity`'s default stands and `GIT_USER_NAME` and `GIT_USER_EMAIL` override it (the first story of this feature; questionnaire 1, Q18). The settings gain the one field these items need that the earlier stories did not give them, the pinned version; `agent_home` and `claude_executable` came with the boundaries story. The agent runtime's `version()` is F0001-S0010's: it runs `claude --version` and returns the first word it prints.

## Interface

`src/factory/domain/settings.py` (extends the module)

```python
CLAUDE_VERSION_VARIABLE = "FACTORY_CLAUDE_VERSION"

class InstanceSettings(BaseModel):
    ...
    pinned_agent_version: str | None = None   # the value of FACTORY_CLAUDE_VERSION; missing or blank is None
```

`src/factory/domain/preflight.py`

```python
class PreflightItem(BaseModel):               # frozen, extra="forbid"
    name: str
    passed: bool
    detail: str = ""                          # what is wrong and how to fix it; empty when passed

class PreflightReport(BaseModel):             # frozen, extra="forbid"
    items: list[PreflightItem]
    @property
    def passed(self) -> bool: ...
    def failed(self) -> list[PreflightItem]: ...

def version_matches(reported: str, pinned: str) -> bool: ...
def machine_stop(report: PreflightReport, *, at: AwareDatetime) -> RepositoryStop | None: ...
```

`src/factory/application/preflight.py`

```python
REQUIRED_TOOLS = ("git", "uv", "make")

def tool_item(name: str, which: Callable[[str], str | None]) -> PreflightItem: ...

class MachineChecks:
    def __init__(
        self,
        boundaries: Boundaries,
        settings: InstanceSettings,
        which: Callable[[str], str | None],
        extra: Sequence[Callable[[], PreflightItem]] = (),
    ) -> None: ...
    def run(self) -> PreflightReport: ...
```

Rules:

- `read_settings` sets `pinned_agent_version` from `FACTORY_CLAUDE_VERSION` (missing or blank: `None`).
- `PreflightItem` and `PreflightReport` are frozen and refuse unknown keys, like every DTO.
- `PreflightReport.passed` is true exactly when every item passed (an empty report passes); `failed()` returns the failed items in order.
- `version_matches(reported, pinned)` is true exactly when `pinned` is not blank and the first whitespace-separated word of `reported` equals `pinned` (so `2.1.289 (Claude Code)` matches `2.1.289`).
- `machine_stop` returns `None` for a passed report. Otherwise it returns `RepositoryStop(scope="machine", reason="preflight_failed", detail=<every failed item as "name: detail", joined by "; ">, at=at)`.
- `tool_item(name, which)` is named `tool:<name>`; it passes when `which(name)` returns a path, else it fails with the detail `<name> is not on the PATH; add it to the image`.
- `MachineChecks.run` returns the items in this order, each run whatever the earlier ones found: `tool:git`, `tool:uv`, `tool:make`, `tool:<settings.claude_executable>`, `hosting-service`, `agents`, `agent-runtime-version`, then the `extra` items in the order given.
- `hosting-service` calls `boundaries.hosting.find_open_pull_request(MAIN_BRANCH)`, a read-only call; any answer passes; a `HostingServiceError` fails with a detail that holds the error's `operation` and `detail`.
- `agents` calls `boundaries.agent_definitions.names()`. A non-empty list passes. An empty list, and an `AgentDefinitionError`, fail with a detail that names `settings.agent_home`.
- `agent-runtime-version` fails when `settings.pinned_agent_version` is `None` with the detail `the image does not pin a version: FACTORY_CLAUDE_VERSION is not set`, fails with a detail that contains the error's `detail` when `boundaries.agent_runtime.version()` raises `AgentRuntimeError`, and otherwise passes exactly when `version_matches(<reported>, <pinned>)`; a failure's detail contains both versions.
- `settings` is the same object as `boundaries.settings` when the wiring builds both (the boundaries story); the items read `settings` and never `boundaries.settings`.

Tests: `tests/domain/test_settings_pinned.py`, `tests/domain/test_preflight.py`, `tests/application/test_preflight.py` (the real `FrontmatterAgentDefinitionReader` on a directory in `tmp_path`, `FakeHostingService` with `fail_next("find_open_pull_request")`, `FakeAgentRuntime(version=...)`, a `which` stub backed by a dictionary). The closed-model test builds the models through a variable typed `type[BaseModel]` and assigns with `setattr`, the field's name in a variable. `tests/test_make_search.py::test_only_the_make_class_names_make` (F0001-S0007) expects the string literal `"make"` in `factory.adapters.make_commands` only; `REQUIRED_TOOLS` holds it too, so the tester of this story changes that test's expected set to `{"factory.adapters.make_commands", "factory.application.preflight"}` and nothing else in the file, with the human's word in `FEATURE.md` decision 28.

## Acceptance criteria

1. `read_settings` sets `pinned_agent_version` to the value of `FACTORY_CLAUDE_VERSION`, and to `None` when the variable is missing or blank.
2. `PreflightItem` and `PreflightReport` refuse an unknown key and an assignment to a field with `ValidationError`.
3. `tool_item("git", which)` passes when `which` answers a path, with the name `tool:git` and an empty detail.
4. `tool_item("make", which)` fails when `which` answers `None`, with the detail `make is not on the PATH; add it to the image`.
5. With every tool present, the hosting service answering, agents installed and the versions equal, `MachineChecks.run()` passes and its item names are `tool:git`, `tool:uv`, `tool:make`, `tool:claude`, `hosting-service`, `agents`, `agent-runtime-version`, in that order; with `claude_executable` set to `/opt/claude/bin/claude` the fourth item is named `tool:/opt/claude/bin/claude` and `which` is asked for that path.
6. Every item is reported at once: with `git` and `uv` missing, the hosting service failing and the version differing, the report holds the same seven items and exactly four of them failed, in order, and the report does not pass.
7. `hosting-service` passes when the fake answers, and fails with a detail that holds the operation `find_open_pull_request` and the fake's detail `injected failure` when `fail_next("find_open_pull_request")` is set.
8. `agents` passes with the real reader bound to a directory other than the user's home that holds `agents/intake.md`, when `settings.agent_home` is that directory (ST4.4).
9. `agents` fails, naming `settings.agent_home` in its detail, when that directory has no agent file and when it does not exist.
10. `agent-runtime-version` passes when the runtime reports `2.1.289 (Claude Code)` and the settings pin `2.1.289`.
11. `agent-runtime-version` fails when the runtime reports `2.1.290` and the settings pin `2.1.289`, and its detail contains both `2.1.290` and `2.1.289` (ST5.3).
12. `agent-runtime-version` fails when `pinned_agent_version` is `None`, with the detail `the image does not pin a version: FACTORY_CLAUDE_VERSION is not set`, and when `version()` raises `AgentRuntimeError`, with a detail that contains that error's `detail` (the test uses a `ClaudeCodeRuntime` whose executable path does not exist, so the detail contains `cannot start`).
13. `version_matches` is false for a blank pinned version, for `2.1.289-beta` against `2.1.289`, and for an empty reported string, and true for `2.1.289` against `2.1.289`.
14. The `extra` items run after the seven, in the order given, and a failing extra item is reported with the others in the same report.
15. The items read the `settings` given and not `boundaries.settings`: with `boundaries.settings` `None` and settings whose `agent_home` holds `agents/intake.md` and whose `pinned_agent_version` equals the runtime's version, every item passes.
16. `PreflightReport(items=[]).passed` is true, and `machine_stop` of an empty or any other passed report is `None`.
17. `machine_stop` of a report with two failed items is a stop with scope `machine`, reason `preflight_failed`, the given `at`, and the detail `<name one>: <detail one>; <name two>: <detail two>`.
18. make check stays green.
19. docs: `docs/operator-guide.md` lists the preflight's seven items with the fix for each (add the tool to the image, check the token and the network, install the agents into `FACTORY_CLAUDE_HOME`, rebuild the image or the pinned version), says that every item is reported at once and that nothing is installed for the operator, and names the variables `FACTORY_CLAUDE_HOME`, `FACTORY_CLAUDE` and `FACTORY_CLAUDE_VERSION`.

## Demo

```bash
uv run python -c "
from factory.domain.preflight import version_matches
from factory.application.preflight import tool_item
print(version_matches('2.1.289 (Claude Code)', '2.1.289'), version_matches('2.1.290', '2.1.289'))
item = tool_item('make', lambda name: None)
print(item.name, item.passed)
"
```
Expect: two lines, `True False` and `tool:make False`.

```bash
uv run python -c "
from datetime import UTC, datetime
from factory.domain.preflight import PreflightItem, PreflightReport, machine_stop
report = PreflightReport(items=[
    PreflightItem(name='tool:uv', passed=False, detail='uv is not on the PATH; add it to the image'),
    PreflightItem(name='agents', passed=True),
    PreflightItem(name='agent-runtime-version', passed=False, detail='agent runtime reports 2.1.290, the image pins 2.1.289'),
])
stop = machine_stop(report, at=datetime(2026, 10, 12, tzinfo=UTC))
print(stop.scope, stop.reason)
print(stop.detail)
"
```
Expect: `machine preflight_failed`, then one line `tool:uv: uv is not on the PATH; add it to the image; agent-runtime-version: agent runtime reports 2.1.290, the image pins 2.1.289`.

```bash
uv run python -c "
from factory.domain.settings import read_settings
env = {'FACTORY_REPOSITORY_URL': '/srv/project.git', 'FACTORY_INSTANCE': 'factory-1', 'FACTORY_CLAUDE_HOME': '/srv/agents', 'FACTORY_CLAUDE_VERSION': '2.1.289'}
s = read_settings(env)
print(s.agent_home, s.claude_executable, s.pinned_agent_version)
"
```
Expect: one line, `/srv/agents claude 2.1.289`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: concrete modules and signatures (`domain/settings.py`, `domain/preflight.py`, `application/preflight.py`). Every rule is stated. The pieces it relies on exist: `FakeAgentRuntime.version`, `FrontmatterAgentDefinitionReader.names`, the fake hosting's `injected failure`, and the `cannot start` text in `ClaudeCodeRuntime`.
   - Criteria: each is testable by one test function. Criterion 1 covers `read_settings` for set, missing and blank. Criterion 2 covers the frozen and closed models. Criteria 3 and 4 cover `tool_item` pass and fail. Criteria 5 and 6 cover the item order and reporting every item at once. Criteria 7 to 12 cover each item's pass side and fail side (hosting, agents with an empty or missing directory, version equal, different, unpinned, and a raising runtime). Criterion 13 covers `version_matches` on both sides. Criterion 14 covers the `extra` items. Criterion 15 covers reading `settings` and not `boundaries.settings`. Criteria 16 and 17 cover `machine_stop` for a passed and a failed report.
   - Demo: the three commands are runnable. Each Expect line gives output that can be checked.
   - Architecture: the domain DTOs and rules are in `factory.domain`. The checks and `REQUIRED_TOOLS` are in `factory.application` and take `which` as an argument, so no tool is called directly. The change to the `test_only_the_make_class_names_make` test has the human's word in FEATURE.md decision 28.
   - Scope: within F0010's "preflight's items". The token file, agent user, sudo and probe items are left to later stories, and the stamp and the wiring are S0009 and S0010.
3. tester: wrote the red tests for the preflight's items.
   - criterion 1: tests/domain/test_settings_pinned.py::test_the_pinned_version_comes_from_its_variable_or_is_none (cases: set, missing, empty, blank)
   - criterion 2: tests/domain/test_preflight.py::test_both_models_reject_an_unknown_field and ::test_a_field_cannot_be_assigned (uses `type[BaseModel]` variables and `setattr`)
   - criterion 3: tests/application/test_preflight.py::test_a_tool_on_the_path_passes
   - criterion 4: tests/application/test_preflight.py::test_a_tool_missing_from_the_path_fails_and_says_to_add_it_to_the_image
   - criterion 5: tests/application/test_preflight.py::test_a_ready_machine_passes_every_item_in_order and ::test_the_claude_tool_item_asks_for_the_configured_executable
   - criterion 6: tests/application/test_preflight.py::test_every_item_is_reported_whatever_the_others_found
   - criterion 7: tests/application/test_preflight.py::test_the_hosting_service_item_reports_a_failed_call (cases: answers, fails)
   - criterion 8: tests/application/test_preflight.py::test_the_agents_item_finds_the_agents_where_the_agent_home_points
   - criterion 9: tests/application/test_preflight.py::test_the_agents_item_fails_naming_the_agent_home_without_agents (cases: no agent file, missing directory)
   - criterion 10: tests/application/test_preflight.py::test_the_version_item_passes_when_the_first_word_is_the_pinned_version
   - criterion 11: tests/application/test_preflight.py::test_the_version_item_fails_naming_both_versions_when_they_differ
   - criterion 12: tests/application/test_preflight.py::test_the_version_item_fails_when_the_image_pins_no_version and ::test_the_version_item_fails_with_the_runtime_error_when_the_version_cannot_be_read (a `ClaudeCodeRuntime` whose executable does not exist, so the detail contains `cannot start`)
   - criterion 13: tests/domain/test_preflight.py::test_a_version_matches_exactly_when_its_first_word_is_the_pinned_one (cases: equal, first word, empty pin, blank pin, `-beta` suffix, empty reported)
   - criterion 14: tests/application/test_preflight.py::test_the_extra_items_run_last_in_order_and_are_reported_with_the_others
   - criterion 15: tests/application/test_preflight.py::test_the_items_read_the_settings_given_and_not_those_of_the_boundaries
   - criterion 16: tests/domain/test_preflight.py::test_a_passed_report_passes_and_makes_no_stop (cases: empty report, all passed)
   - criterion 17: tests/domain/test_preflight.py::test_a_failed_report_becomes_one_machine_stop_naming_every_failed_item
   - criteria 18 and 19: no tests. They are `make check` and the docs.

   New files: tests/domain/test_settings_pinned.py, tests/domain/test_preflight.py, tests/application/test_preflight.py. The application tests use the shared `boundaries` fixture with `dataclasses.replace`. They swap in `FakeAgentRuntime(version=...)` and the real `FrontmatterAgentDefinitionReader` on a directory in `tmp_path`, and use a `which` stub that answers from a dictionary and records what it was asked.

   Changed file: tests/test_make_search.py::test_only_the_make_class_names_make. Its expected set is now `{"factory.adapters.make_commands", "factory.application.preflight"}`. This is the change the Interface asks for, on the human's word (FEATURE.md decision 28); nothing else in the file changed.

   `make test` fails with collection errors because `factory.domain.preflight` and `factory.application.preflight` do not exist yet. test_settings_pinned will also fail until `InstanceSettings` has `pinned_agent_version`. `make lint` passes.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: built the preflight's items. All tests pass and `make check` is green (coverage 99.52 %). Commit 1f730a8.
      - `src/factory/domain/settings.py`: adds `CLAUDE_VERSION_VARIABLE` and `InstanceSettings.pinned_agent_version`. `read_settings` reads it with the existing `_optional` helper, and a missing or blank value becomes `None`.
      - `src/factory/domain/preflight.py`: adds `PreflightItem` and `PreflightReport`, both frozen with `extra="forbid"`. The report has the `passed` property and `failed()`. Also adds `version_matches` (the pin must not be blank and must equal the first word of the reported version) and `machine_stop`, which joins the failed items as `name: detail` with `; ` into a `RepositoryStop` with scope `machine` and reason `preflight_failed`.
      - `src/factory/application/preflight.py`: adds `REQUIRED_TOOLS`, `tool_item` and `MachineChecks`. `MachineChecks.run` builds the four tool items (the three required tools, then `settings.claude_executable`), then `hosting-service`, `agents` and `agent-runtime-version`, then the `extra` items. Each item reads only `self._settings`. Each failure's detail says how to fix it: check the token and the network, install the agents there, or rebuild the image or change the pinned version.
      - Main design decision: each item catches only its own boundary's error (`HostingServiceError`, `AgentDefinitionError`, `AgentRuntimeError`) and turns it into a failed item. That way every item runs whatever the earlier ones found, and anything unexpected still surfaces as an error. Rejected: a generic `except Exception` wrapper around every item. It would hide programming errors as preflight failures.
      - Refactor: I read the diff and found nothing to change, so there is no separate refactor commit.
      - Not touched: the docs criterion (19) is the documenter's. `which` is passed in by the caller. Wiring the real `shutil.which` into the tick is a later story.

   `make check`: check: green
5. reviewer: no findings.
      - Acceptance criteria: each of criteria 1 to 17 has a test that checks what the criterion says. The coder's entry records `make check` green (commit 1f730a8). Every rule in the Interface has its failing side tested: a blank or missing `FACTORY_CLAUDE_VERSION` (empty, blank and missing cases), unknown keys and assignment on both models, a tool missing from the PATH, a `HostingServiceError` that holds its operation and detail, the agents directory empty and the agents directory missing (`AgentDefinitionError`), the version unpinned, different and unreadable (`cannot start` from a real `ClaudeCodeRuntime`), and `version_matches` with an empty pin, a blank pin, a suffixed version and an empty reported string. The change to `tests/test_make_search.py` is exactly the one the Interface names, under FEATURE.md decision 28.
      - Architecture: `factory.domain.preflight` is pure DTOs and rules. `factory.application.preflight` imports only `factory.application` and `factory.domain`, reaches the outside only through `Boundaries`, and takes `which` from the caller. No tool is called directly and nothing is installed. Each item catches only its own boundary's error. The items read `self._settings` and never `boundaries.settings`.
      - Security: no secrets, no shell or SQL strings, no suppression markers.
      - Quality: names and docstrings fit the module and its public names. `_optional` is reused for the new setting. There is no dead or duplicated logic.
      - Ticket hygiene: the coder's entry gives the main decision (each item catches only its own boundary's error) and what was rejected (a blanket `except Exception`). `Assignment` matches the code, and criterion 19 still describes what the operator guide must say.
6. documenter: one file changed, `docs/operator-guide.md`, and `make check` is green after the edit.
   - Settings table: added a `FACTORY_CLAUDE_VERSION` row. `FACTORY_CLAUDE_HOME` and `FACTORY_CLAUDE` were already listed.
   - New section "The preflight's items", placed before "The wait for a repository that is not ready". It covers:
     - the seven items, each with what makes it pass and the fix for each failure (add the tool to the image, check the token and the network, install the agents into `FACTORY_CLAUDE_HOME`, rebuild the image or change the pinned version);
     - that every item is reported at once and that a failed report becomes one machine stop whose detail lists each failed item;
     - that nothing is installed for the operator, and that the commit identity is not an item.
     - It also says plainly that nothing runs these items at start yet, because the wiring is the next two stories.
   - "The agent runtime" section: replaced the stale "the preflight that compares it arrives with F0010, and until then nothing checks it" with a pointer to the new section.
   - Cross-read and found current: `README.md`, `docs/project-guide.md` (the `"make"` literal remark in the project-commands paragraph, which this story widens to `factory.application.preflight`, was not touched), the "Claude Code" section of the image docs (`FACTORY_CLAUDE_VERSION` is already set there), and the stops table row for `preflight_failed`.
   - Stale but not touched, because the wiring stories own them:
     - The "The agent runtime" and `factory-guard` paragraphs say a guard probe is still to come.
     - The README and the operator guide's intro still say the preflight is to come.
     - The project-guide sentence "The string `"make"` appears in no other module under `src/factory`" is now slightly wrong, since `factory.application.preflight` holds it too. That is unrelated prose outside my lane to rewrite as a finding, so I am noting it here.
   - No findings for the coder: the code matches the Interface, and every public name has a docstring.

   `make check`: check: green
