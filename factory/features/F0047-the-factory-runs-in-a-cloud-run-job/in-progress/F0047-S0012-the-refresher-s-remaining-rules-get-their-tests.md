---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-01T09:47:33.258348Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-01T09:47:33.250954Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-01T09:47:33.258348Z'
  stage: intake
---

# The refresher's remaining rules get their tests
<!-- proposed by feature acceptance of 2026-11-01; refine before starting -->

## Description

S0004's refresher (`python -m factory.entry.refresh_token`) states three rules that no test pins. Its review (entries 69 and 77) noted them after the human's entry 52, which kept further edge cases "as a note, which I record on `main` for a later story"; the feature acceptance F0047-A0001 found them recorded nowhere else. The rules:

- `main` restores the previous `SIGTERM` and `SIGINT` handlers before it returns. Every loop test runs under the `restored_signals` fixture, which restores them anyway.
- A `KeyboardInterrupt` or `SystemExit` of one refresh is not caught.
- `masked` in `factory.domain.tokens` replaces every non-empty hidden value with `***`. It is tested only through the adapter and the command.

This story writes those tests; the code is expected to pass them as it is. Unchanged: every module under `src/factory/` (a test that fails is a finding for the coder, not a test change), and S0004's tests. Left out: the `incomplete-read` row that computes its expected detail with the code's own expression, and the names `SECOND` and `SECOND_CLIENT` of `tests/test_hosting_search.py`. Both are changes to S0004's tests and need a leave in `feature.md`; refine this story to add them if the human gives it.

## Interface

No module under `src/factory/` changes. The rules under test, as they are:

```python
# factory.domain.tokens (domain)
def masked(message: str, hidden: list[str]) -> str: ...
# factory.entry.refresh_token (entry)
def main(argv: Sequence[str] | None = None, environ: Mapping[str, str] = os.environ, *,
         source: Callable[[str, str, str, str], TokenSource] | None = None,
         sleep: Callable[[float], None] | None = None) -> int: ...
```

- `masked` replaces every occurrence of each non-empty value of `hidden` by `***`, leaves an empty value out, and returns `message` unchanged when no value occurs.
- `main` installs its own `SIGTERM` and `SIGINT` handlers while it runs, and on return the handlers are the very objects `signal.getsignal` gave before the call: after `--once`, after the loop ended by a signal, and after an exit 2 for a missing variable.
- A source whose `fetch` raises `KeyboardInterrupt` or `SystemExit(3)` lets it leave `main` as raised, under `--once` and in the loop; the login file is left as it was.

Tests (the tester writes them): `tests/domain/test_tokens_masked.py`, `tests/entry/test_refresh_token_signals.py`, using `tests/token_support.py` and the `restored_signals` fixture of `tests/conftest.py`. A test's own handler, installed before the call, is the "previous" handler it compares against.

## Acceptance criteria

1. `masked`, rows of one test: `("token tok-1 and s3 s3", ["tok-1", "s3"])` gives `"token *** and *** ***"`; `("nothing here", ["tok-1"])` gives `"nothing here"`; `("a b", ["", "b"])` gives `"a ***"`; `("x", [])` gives `"x"`.
2. With a test's own handler installed for `SIGTERM` and for `SIGINT`, `signal.getsignal` returns those same handlers after `main` returns, in three rows: `--once` with a source that answers (exit 0); the loop ended by `SIGTERM` raised from the injected `sleep` (exit 0); `FACTORY_TOKEN_URL` unset (exit 2). While the source's `fetch` runs, `signal.getsignal(signal.SIGTERM)` is not the test's handler.
3. A source whose `fetch` raises `KeyboardInterrupt`, and one that raises `SystemExit(3)`, each make `main` raise that exception (for `SystemExit`, with code 3), under `--once` and in the loop (four rows of one test). The login file keeps its earlier content, and standard error holds no `refresh_token:` line.
4. `make check` stays green.
5. docs: none. The rules are already in the operator guide (*A bearer token for the model API*) and in the project guide (`docs/project-guide/agents.md`, **The bearer token**); this story adds only tests.

## Smoke test

```bash
uv run pytest tests/domain/test_tokens_masked.py tests/entry/test_refresh_token_signals.py 2>&1 | tail -1
```
Expect: one line that holds `passed` and neither `failed` nor `error`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-11-01 human: created.
2. factory: started intake as vm.
