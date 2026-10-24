# No test sees the agent's login

## Description

An agent's run holds its login in its environment: `CLAUDE_CODE_OAUTH_TOKEN` under the subscription, `ANTHROPIC_API_KEY` under an API key, which the login shell hands to the runtime (`factory.adapters.agent_launch`). Every test an agent runs (`make test`, `make check`, a smoke test's pytest) inherits that environment, and so does every child process a test starts with the process's own environment (the `version()` calls of both runtimes). On 2026-10-24 an instance on an API key failed `tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words`, whose stand-in inherited `ANTHROPIC_API_KEY`, and pytest's assertion message printed the whole inherited environment, the key in full, into the run's output and from there into a journal entry (decision 21 of `feature.md`). This story makes the suite independent of the login of whoever runs it: one fixture in `tests/conftest.py`, used by every test, removes the two variables from the test process's environment before each test, so no test and no child process a test starts sees them, and the version test's assertion names only variable names when it fails. Nothing under `src/` changes; the runtimes still pass the login exactly as today. What stays: every other test as it is; the login of the agent's own run, which the factory gives and the suite never reads.

## Interface

No module under `src/factory/` changes.

`tests/conftest.py`: one fixture with `autouse=True`, named by the tester, that removes `LOGIN_VARIABLE` and `API_LOGIN_VARIABLE` (the two names `factory.adapters.agent_launch` defines, imported from there, not written again) from the test process's environment for the duration of each test, through `monkeypatch.delenv(name, raising=False)`, so the environment is restored after the test and a test may still set either name itself with `monkeypatch.setenv`. Leave: decision 18 (i) of `feature.md`.

`tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words`: its last assertion compares against the set of the call's variable names, `assert API_LOGIN_VARIABLE not in set(call.environment)`, so that a failure prints names and no value; the test keeps its name, its setup and what it checks. Leave: decision 18 (i).

Tests (the tester writes them): one new test module at the `tests/` root, `tests/test_no_agent_login.py` (the smoke test names it), holding one parametrized test over the two names that asserts the name is not in `os.environ` inside a test.

## Acceptance criteria

1. Inside a test, neither `CLAUDE_CODE_OAUTH_TOKEN` nor `ANTHROPIC_API_KEY` is in `os.environ`, also when the pytest process was started with both set (rows of one parametrized test over the two names; the smoke test runs it with both set).
2. A test that sets one of the two names with `monkeypatch.setenv` sees the value it set (one row per name in the same new module), and after the test the variable is back as the pytest process had it: the fixture removes through `monkeypatch`, not through `os.environ` directly (a row that reads `tests/conftest.py`'s text and finds `monkeypatch.delenv` and no `os.environ.pop` and no `del os.environ`).
3. `tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words` passes when the pytest process was started with `ANTHROPIC_API_KEY` set (the smoke test), and its last assertion is `assert API_LOGIN_VARIABLE not in set(call.environment)`.
4. Every other test under `tests/` keeps its name and passes unchanged.
5. `make check` stays green.
6. docs: `docs/project-guide/processes-and-checks.md`, in its passage on the tests (or the section that names `tests/conftest.py`'s shared fixtures): one paragraph that the suite removes the agent's two login variables from every test's environment, why (an agent's run holds them; a child process with the process's own environment inherits them; an assertion message prints what it compares), and that an assertion about an environment compares names (`set(environment)`), never the mapping. `README.md`, `docs/operator-guide.md`, `docs/decisions.md`: none (no behaviour of the factory changes).

## Smoke test

```bash
env "$(printf 'ANTHROPIC_%s=x' API_KEY)" "$(printf 'CLAUDE_CODE_OAUTH_%s=x' TOKEN)" uv run pytest tests/test_no_agent_login.py "tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words" 2>&1 | tail -1 | sed -E 's/[0-9]+ passed/N passed/; s/ in [0-9.]+s.*$//'
```
Expect: one line that starts with `N passed` and names no `failed` and no `error`.

## Journal
