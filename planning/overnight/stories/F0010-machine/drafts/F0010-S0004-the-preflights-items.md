# The preflight's items

## Assignment (as of log entry 1)

Build the checks of the machine that the preflight runs: the tools are on the `PATH`, the hosting service answers, the agents are installed where `FACTORY_CLAUDE_HOME` points, and the agent runtime's version equals the version the image pins. Every item runs whatever the others found, so one report names everything that is wrong, and a failed report becomes one machine stop whose detail lists every failed item. A missing tool is reported and never worked around: nothing here installs anything. This covers ST5.3 (the preflight fails, naming both versions) and ST4.4 (the agents check finds the agents where `FACTORY_CLAUDE_HOME` points), implements part of R29 (the agent runtime is held to the pinned version), and keeps kept thing 8 (a missing tool is reported, never worked around) and kept thing 18 (the machine and its preflight). The items are built here and wired into the tick by the next story, which adds the stamp and the probe of the main branch. v1's item for the git identity is not rebuilt: the entrypoint sets the identity from its defaults, so it cannot be missing. The settings gain the fields these items need.

## Interface

`src/factory/domain/settings.py` (extends the module)

```python
AGENT_HOME_DEFAULT = Path("/home/agent/.claude")
AGENT_HOME_VARIABLE = "FACTORY_CLAUDE_HOME"
CLAUDE_EXECUTABLE_VARIABLE = "FACTORY_CLAUDE"
CLAUDE_VERSION_VARIABLE = "FACTORY_CLAUDE_VERSION"

class InstanceSettings(BaseModel):
    ...
    agent_home: Path = AGENT_HOME_DEFAULT
    claude_executable: str = "claude"
    pinned_agent_version: str | None = None
```

`read_settings` sets `agent_home` from `FACTORY_CLAUDE_HOME`; when that is missing or blank it is `<HOME>/.claude` if `HOME` is set and not blank, else `AGENT_HOME_DEFAULT`. It sets `claude_executable` from `FACTORY_CLAUDE` (missing or blank: `claude`) and `pinned_agent_version` from `FACTORY_CLAUDE_VERSION` (missing or blank: `None`).

`src/factory/domain/preflight.py`

```python
class PreflightItem(BaseModel):
    name: str
    passed: bool
    detail: str = ""                          # what is wrong and how to fix it; empty when passed

class PreflightReport(BaseModel):
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

- `PreflightReport.passed` is true exactly when every item passed (an empty report passes); `failed()` returns the failed items in order.
- `version_matches(reported, pinned)` is true exactly when `pinned` is not blank and the first whitespace-separated word of `reported` equals `pinned` (so `2.1.289 (Claude Code)` matches `2.1.289`).
- `machine_stop` returns `None` for a passed report. Otherwise it returns `RepositoryStop(scope="machine", reason="preflight_failed", detail=<every failed item as "name: detail", joined by "; ">, at=at)`.
- `tool_item(name, which)` is named `tool:<name>`; it passes when `which(name)` returns a path, else it fails with a detail that names the tool and says to add it to the image.
- `MachineChecks.run` returns the items in this order, each run whatever the earlier ones found: `tool:git`, `tool:uv`, `tool:make`, `tool:<settings.claude_executable>`, `hosting-service`, `agents`, `agent-runtime-version`, then the `extra` items in the order given.
- `hosting-service` calls `boundaries.hosting.find_open_pull_request(MAIN_BRANCH)`, a read-only call; any answer passes; a `HostingServiceError` fails with a detail that holds the error's `operation` and `detail`.
- `agents` calls `boundaries.agent_definitions.names()`. A non-empty list passes. An empty list, and an `AgentDefinitionError`, fail with a detail that names `settings.agent_home`.
- `agent-runtime-version` fails when `settings.pinned_agent_version` is `None` (the detail says the image does not pin a version), fails with the error's detail when `boundaries.agent_runtime.version()` raises `AgentRuntimeError`, and otherwise passes exactly when `version_matches(<reported>, <pinned>)`; a failure's detail contains both versions.
- The only construction of `FrontmatterAgentDefinitionReader` in `src/factory` passes `settings.agent_home` (in `factory.entry.wiring`), so the agents are looked for where `FACTORY_CLAUDE_HOME` points.

Tests: `tests/domain/test_settings.py`, `tests/domain/test_preflight.py`, `tests/application/test_preflight.py` (the real `FrontmatterAgentDefinitionReader` on a directory in `tmp_path`, `FakeHostingService` with `fail_next("find_open_pull_request")`, `FakeAgentRuntime(version=...)`, a `which` stub backed by a dictionary), `tests/test_agent_home_wiring.py` (the search, with `ast`).

## Acceptance criteria

1. `read_settings` sets `agent_home` to the value of `FACTORY_CLAUDE_HOME` when it is set, to `<HOME>/.claude` when only `HOME` is set, and to `/home/agent/.claude` when neither is set or both are blank (three cases).
2. `read_settings` sets `claude_executable` to the value of `FACTORY_CLAUDE` (`claude` when missing or blank) and `pinned_agent_version` to the value of `FACTORY_CLAUDE_VERSION` (`None` when missing or blank).
3. `tool_item("git", which)` passes when `which` answers a path, with the name `tool:git` and an empty detail.
4. `tool_item("make", which)` fails when `which` answers `None`, and its detail names `make` and says to add it to the image.
5. With every tool present, the hosting service answering, agents installed and the versions equal, `MachineChecks.run()` passes and its item names are `tool:git`, `tool:uv`, `tool:make`, `tool:claude`, `hosting-service`, `agents`, `agent-runtime-version`, in that order.
6. Every item is reported at once: with `git` and `uv` missing, the hosting service failing and the version differing, the report holds the same seven items and exactly four of them failed, in order, and the report does not pass.
7. `hosting-service` passes when the fake answers and fails with a detail that holds the operation `find_open_pull_request` when `fail_next("find_open_pull_request")` is set.
8. `agents` passes with the real reader bound to a directory other than the user's home that holds `agents/intake.md`, when `settings.agent_home` is that directory (ST4.4).
9. `agents` fails, naming `settings.agent_home` in its detail, when that directory has no agent file and when it does not exist.
10. `agent-runtime-version` passes when the runtime reports `2.1.289 (Claude Code)` and the settings pin `2.1.289`.
11. `agent-runtime-version` fails when the runtime reports `2.1.290` and the settings pin `2.1.289`, and its detail contains both `2.1.290` and `2.1.289` (ST5.3).
12. `agent-runtime-version` fails when `pinned_agent_version` is `None`, and when `version()` raises `AgentRuntimeError`.
13. `version_matches` is false for a blank pinned version, for `2.1.289-beta` against `2.1.289`, and for an empty reported string, and true for `2.1.289` against `2.1.289`.
14. The `extra` items run after the seven, in the order given, and a failing extra item is reported with the others in the same report.
15. `machine_stop` of a passed report is `None`.
16. `machine_stop` of a report with two failed items is a stop with scope `machine`, reason `preflight_failed`, the given `at`, and the detail `<name one>: <detail one>; <name two>: <detail two>`.
17. A search with `ast` over `src/factory` finds exactly one call of `FrontmatterAgentDefinitionReader(...)`, in `factory.entry.wiring`, and its argument is `settings.agent_home`.
18. `make check` stays green.
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
