---
stage: doing
pr: 16
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The four interfaces as abstract base classes

## Assignment (as of log entry 1)

The four interfaces of F0001 (`Git`, `HostingService`, `ProjectCommands`, `AgentRuntime`) are `typing.Protocol` classes today, and their six implementations fit them by shape only: a reader of an adapter cannot see which interface it implements, and nothing checks the fit at the class itself. The human decided on 2026-10-13 that the factory's interfaces are abstract base classes and its own implementations inherit them. This story changes the base of the four interfaces to `abc.ABC` with every operation an `@abstractmethod`, makes the six implementations inherit their interface, and replaces the tests that asserted the opposite. No operation, signature, docstring or behaviour changes. It keeps R5, R6, R11 and R12.

## Interface

The four modules keep their names, operations, signatures, return types and docstrings. Only the base class and the decorator change, in this form (shown for `ProjectCommands` in `src/factory/application/project_commands.py`):

```python
from abc import ABC, abstractmethod
from datetime import timedelta

from factory.domain.checks import CheckResult


class ProjectCommands(ABC):
    """The project's named commands, such as `check`, `lint` and `test`."""

    @abstractmethod
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        """Run `command` until it ends or reaches `time_limit`.

        A red or timed-out command is a result; `ProjectCommandError` means it could not start.
        """
```

The same change is made to `Git` in `src/factory/application/git.py` (19 operations), `HostingService` in `src/factory/application/hosting.py` (10 operations) and `AgentRuntime` in `src/factory/application/agent_runtime.py` (`run`, `version`).

The six implementations inherit their interface, with their constructors unchanged:

```python
class GitCli(Git): ...
class PyGithubHostingService(HostingService): ...
class FakeHostingService(HostingService): ...
class MakeProjectCommands(ProjectCommands): ...
class ClaudeCodeRuntime(AgentRuntime): ...
class FakeAgentRuntime(AgentRuntime): ...
```

Rules:

- Every public operation of an interface is an `@abstractmethod`; the interface has no other public member and no state.
- The body of each abstract method is its docstring alone: no `...`, no `pass`, no code.
- No class in `factory.application` derives from `typing.Protocol`.
- An interface cannot be instantiated, and neither can a subclass that leaves any of its operations unimplemented (Python raises `TypeError` at construction).
- Each implementation module imports its interface from `factory.application`; the layer contract (adapters may import application) is unchanged.
- The tests that asserted an implementation does not inherit its interface are rewritten to assert that it does; no test keeps an assertion that an interface is absent from an implementation's `__mro__`.
- The posting search counts concrete classes only: the abstract `HostingService` is the interface, not an implementation of `post_comment`.

Tests: `tests/application/test_interfaces.py` (new) for the interfaces; the six "fits without inheriting" tests in `tests/adapters/test_git_cli_reading.py`, `test_pygithub_hosting.py`, `test_fake_hosting.py`, `test_make_commands.py`, `test_fake_agent_runtime.py` and `test_claude_runtime_resume.py` are rewritten in place; `tests/test_hosting_fake_search.py` replaces its `Protocol` test by an abstract-class test. mypy refuses a direct call of an abstract class, so the tests for criteria 7 and 8 call the interfaces and the incomplete subclass through a variable typed `Callable[[], object]` (or a parametrized argument typed `type[object]`), with no `type: ignore`.

## Acceptance criteria

1. `Git`, `HostingService`, `ProjectCommands` and `AgentRuntime` are each a subclass of `abc.ABC`.
2. No class in the four modules of `factory.application` derives from `typing.Protocol` (an `ast` search over the modules finds no base named `Protocol`).
3. `Git.__abstractmethods__` is exactly the nineteen operations of `tests/application/test_git_protocol.py`'s `OPERATIONS`.
4. `HostingService.__abstractmethods__` is exactly the ten operations of `tests/application/test_hosting_protocol.py`'s `OPERATIONS`, and each keeps the return type that test pins.
5. `ProjectCommands.__abstractmethods__` is exactly `{"run"}`, and `AgentRuntime.__abstractmethods__` is exactly `{"run", "version"}`; none of the four interfaces has a public member (a name not starting with `_`) other than its abstract operations.
6. The body of every abstract method in the four modules is a single docstring (an `ast` check: one statement, a string constant).
7. Calling any of the four interfaces with no arguments raises `TypeError`.
8. A subclass of `ProjectCommands` that defines no `run` raises `TypeError` when it is constructed, and one that defines `run` is constructed.
9. `GitCli` is a subclass of `Git`, and a `GitCli` built as the `checkout` fixture builds it is an instance of `Git`.
10. `PyGithubHostingService` and `FakeHostingService` are subclasses of `HostingService`, and the `hosting` fixture's object is an instance of it.
11. `MakeProjectCommands` is a subclass of `ProjectCommands`.
12. `ClaudeCodeRuntime` and `FakeAgentRuntime` are subclasses of `AgentRuntime`, and the `agent_runtime` fixture's object is an instance of it.
13. No file under `tests/` asserts that an interface is not in an implementation's `__mro__`: an `ast` search finds no comparison with `not in` whose right side is an attribute named `__mro__`.
14. Exactly two concrete classes under `src/factory` define `post_comment`, `FakeHostingService` and `PyGithubHostingService`; the abstract `HostingService` is not counted, and no test class defines `post_comment`.
15. make check stays green.
16. docs: `docs/project-guide.md` says for each of the six implementations that it inherits its interface, an abstract base class, and no longer that it fits "structurally"; `docs/decisions.md` records that the factory's interfaces are abstract base classes its own implementations inherit, decided by the human on 2026-10-13, and that `typing.Protocol` is kept for shapes of code the factory does not own.

## Demo

```bash
uv run python -c "from abc import ABC; from factory.application.git import Git; from factory.application.hosting import HostingService; from factory.application.project_commands import ProjectCommands; from factory.application.agent_runtime import AgentRuntime; print([issubclass(c, ABC) for c in (Git, HostingService, ProjectCommands, AgentRuntime)]); print(len(Git.__abstractmethods__), len(HostingService.__abstractmethods__), sorted(ProjectCommands.__abstractmethods__), sorted(AgentRuntime.__abstractmethods__))"
```
Expect: two lines, `[True, True, True, True]` and `19 10 ['run'] ['run', 'version']`.

```bash
uv run python -c "from factory.adapters.git_cli import GitCli; from factory.application.git import Git; from factory.adapters.fake_hosting import FakeHostingService; from factory.adapters.pygithub_hosting import PyGithubHostingService; from factory.application.hosting import HostingService; from factory.adapters.make_commands import MakeProjectCommands; from factory.application.project_commands import ProjectCommands; from factory.adapters.claude_runtime import ClaudeCodeRuntime; from factory.adapters.fake_agent_runtime import FakeAgentRuntime; from factory.application.agent_runtime import AgentRuntime; print(issubclass(GitCli, Git), issubclass(FakeHostingService, HostingService), issubclass(PyGithubHostingService, HostingService), issubclass(MakeProjectCommands, ProjectCommands), issubclass(ClaudeCodeRuntime, AgentRuntime), issubclass(FakeAgentRuntime, AgentRuntime))"
```
Expect: one line, `True True True True True True`.

## Log (append only)

1. 2026-10-13 human: created.
2. intake: accepted
   - Interface: concrete. It names the four modules and their paths, the ABC/@abstractmethod form with a worked example, the six implementations with unchanged constructors, and the test files to rewrite. The files that criteria 3 and 4 cite (`test_git_protocol.py`, `test_hosting_protocol.py`) exist and define `OPERATIONS`. No behaviour is stated in an Interface comment that lacks a criterion.
   - Criteria: each is testable by one function (ast searches for 2, 6 and 13; set equality on `__abstractmethod__s` for 3 to 5; `TypeError` for 7 and 8; subclass/instance checks for 9 to 12; a class count for 14). The rules have their failing sides: the interface and an incomplete subclass cannot be built (7, 8), and a complete subclass can (8).
   - Demo: both commands are runnable one-liners, and each `Expect:` line gives exact output to compare.
   - Architecture: matches CLAUDE.md (interfaces as ABCs in `factory.application`, implementations in `factory.adapters` inheriting them, layer contract unchanged).
   - Scope: within F0001 Boundaries. It is listed in FEATURE.md as S0019, decision 20 records it, and nothing out of scope is touched.
3. tester: Wrote tests for criteria 1–14 and rewrote the six "fits without inheriting" tests and the posting search in place.

   Mapping:
   - criterion 1: tests/application/test_interfaces.py::test_each_interface_is_an_abstract_base_class (parametrized over the four interfaces)
   - criterion 2: tests/application/test_interfaces.py::test_no_class_in_the_interface_modules_derives_from_protocol
   - criterion 3: tests/application/test_interfaces.py::test_git_abstract_methods_are_exactly_its_nineteen_operations (imports `OPERATIONS` from tests/application/test_git_protocol.py)
   - criterion 4: tests/application/test_interfaces.py::test_hosting_abstract_methods_are_its_ten_operations_with_their_return_types (imports `OPERATIONS` from tests/application/test_hosting_protocol.py)
   - criterion 5: tests/application/test_interfaces.py::test_project_commands_and_agent_runtime_have_exactly_their_operations_abstract and ::test_an_interface_has_no_public_member_but_its_abstract_operations
   - criterion 6: tests/application/test_interfaces.py::test_every_abstract_method_body_is_its_docstring_alone
   - criterion 7: tests/application/test_interfaces.py::test_an_interface_cannot_be_instantiated (parameter typed `type[object]`)
   - criterion 8: tests/application/test_interfaces.py::test_a_subclass_must_implement_every_operation_to_be_constructed (incomplete subclass called through a `Callable[[], object]`)
   - criterion 9: tests/adapters/test_git_cli_reading.py::test_git_cli_inherits_the_git_interface (uses the `checkout` fixture)
   - criterion 10: tests/adapters/test_pygithub_hosting.py::test_client_inherits_the_hosting_service_interface and tests/adapters/test_fake_hosting.py::test_the_fake_inherits_the_hosting_service_interface (uses the `hosting` fixture)
   - criterion 11: tests/adapters/test_make_commands.py::test_make_class_inherits_the_project_commands_interface
   - criterion 12: tests/adapters/test_fake_agent_runtime.py::test_fake_inherits_the_agent_runtime_interface (uses the `agent_runtime` fixture) and tests/adapters/test_claude_runtime_resume.py::test_claude_runtime_inherits_the_agent_runtime_interface
   - criterion 14: tests/test_hosting_fake_search.py::test_only_the_fake_and_the_pygithub_client_define_post_comment and ::test_no_test_class_defines_post_comment. The `_is_protocol` exclusion is now `_is_abstract`: it skips a class whose base is `ABC`.
   - criterion 13: tests/application/test_interfaces.py::test_no_test_asserts_an_interface_is_absent_from_an_mro

   Files: created tests/application/test_interfaces.py. Changed tests/adapters/test_git_cli_reading.py, test_pygithub_hosting.py (also dropped its module-level `STRUCTURAL_FIT`, which only that test used), test_fake_hosting.py, test_make_commands.py, test_fake_agent_runtime.py, test_claude_runtime_resume.py and tests/test_hosting_fake_search.py.

   Red as intended: every module imports. The failures are wrong results because the interfaces are still `Protocol`s. That covers the ABC, abstract-methods and docstring-body checks, the incomplete subclass that can still be constructed, the subclass checks, and the posting search, which now finds `HostingService` itself. `make lint` is green. I skipped the type check as the stage says.

   Rejected: a separate test for criterion 6 that every interface function is decorated. Criteria 3 to 5 already pin the abstract set and the public members exactly.

   Open: none.

   `make lint`: lint: green
   `make test`: FAILED tests/test_hosting_fake_search.py::test_only_the_fake_and_the_pygithub_client_define_post_comment
