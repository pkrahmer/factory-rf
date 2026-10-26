# The opencode probe no longer advises a login kept in the agent's home

<!-- proposed by feature acceptance of 2026-10-26; refine before starting -->

## Description

S0001 corrected the operator guide's *Running on opencode*: on the machine the agent's home is `home/` on the dataset, and the rollback to the base clears it before every stage. A login that an operator's own opencode build keeps there therefore does not survive to the next run, and only the API login file works. The preflight's code still gives the old advice. When an opencode probe fails with the login `none`, its detail ends `; the agent runs get no API key: log in once as the factory user with the opencode build's own login, or put a key in the file FACTORY_API_LOGIN_FILE names`. When an opencode probe completes with the login `none` (a provider whose key comes through `FACTORY_CONTAINER_ENV`, for example), the factory log says `the runtime uses the login kept in its home`. Both texts send the operator to a login that cannot work. This story changes those two texts under opencode only. The failed probe's hint keeps only the API login file. The completed probe's detail no longer names the agent's home. Unchanged: every text under Claude Code (its third login, the login in the agent's home, stays as it is), the hints for `api_key` and `subscription`, the order of the detail's parts, and when the probe runs. Left to a later story: whether Claude Code's login in the agent's home still works on the machine. That question is outside F0046.

## Interface

`factory.application.preflight` (application):

- `_opencode_login_hint(login)` with `login == "none"` returns `"; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names"` (the variable's name taken from `API_LOGIN_FILE_VARIABLE`, as today). For any other login it returns `""`, as today.
- `_login_detail(settings, login)` with `login == "none"` returns `"the agent runs get no login from a file"` when `settings.agent_runtime == "opencode"`. It returns the text of today when the runtime is `claude`. The other logins are unchanged.

Tests (the tester writes them): rows in `tests/application/test_agent_run_probe_opencode.py` and `tests/application/test_agent_run_probe_api_login.py`. The shared helper `opencode_sso_hint` in `tests/probe_support.py` changes its text. That changes what `tests/application/test_agent_run_probe_opencode.py` and `tests/application/test_agent_run_probe_factory_user.py` check, which needs the human's leave in `feature.md` before the story starts.

## Acceptance criteria

1. A probe under opencode that ends `died` with the login `none` fails with a detail that ends `; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names`, and the detail does not contain `own login`. Under Claude Code, the rows for `died` with `api_key` and with `subscription` keep their texts of today. These are rows of one parametrized test.
2. A probe under opencode that completes with the login `none` passes with the detail `the agent runs get no login from a file`. The same probe under Claude Code keeps `the agent runs get no login from a file; the runtime uses the login kept in its home`. These are rows of one parametrized test.
3. A probe under opencode with the login `api_key` keeps its texts of today, both when it completes and when it dies.
4. `make check` stays green.
5. docs: `docs/operator-guide.md`, *The probe of the agent run*: the opencode hint quoted with its new text. The completed probe's detail under opencode is named as `the agent runs get no login from a file`. `README.md`, `docs/project-guide/` and `docs/decisions.md`: none, because the rule is already S0001's decision entry *A company's provider for opencode* ("Why only the API login works").

## Smoke test

```bash
grep -c "opencode build's own login" src/factory/application/preflight.py docs/operator-guide.md
```
Expect: two lines, `src/factory/application/preflight.py:0` and `docs/operator-guide.md:0`

```bash
uv run pytest tests/application/test_agent_run_probe_opencode.py tests/application/test_agent_run_probe_api_login.py tests/application/test_agent_run_probe_factory_user.py 2>&1 | tail -n 1
```
Expect: a line that ends with `passed in <seconds>s` and names no `failed`

## Journal
