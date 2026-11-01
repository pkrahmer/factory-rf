---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 492
comments_read: [6556376362]
handed_over: null
claim: null
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
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-01T09:47:53.013246Z'
  stage: intake
  run: 349d685ab1c848c09be4001b8ed29f0e
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-01T09:48:12.901233Z'
  stage: tests
- number: 5
  speaker: tester
  kind: question
  at: '2026-11-01T09:52:19.141237Z'
  stage: tests
  run: 6bb95a218aff45399b5685f4637a063d
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-11-01T09:53:34.708187Z'
  stage: tests
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-01T09:53:52.584756Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-01T10:00:27.763229Z'
  stage: tests
  run: 828c251eccf8436db71201c733a6b885
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
3. intake: accepted
   Interface: no `src/` change; it names `factory.domain.tokens.masked` and `factory.entry.refresh_token.main` with signatures that match the code (`src/factory/domain/tokens.py:31`, `refresh_token.py:37`). The behaviours it states are the mask, the empty value, the unchanged message, the handler restore and the exceptions that pass through. The test files and the helpers they use (`tests/token_support.py`, the `restored_signals` fixture in `tests/conftest.py`) exist or are named for the tester to create.
   Criteria: 1 is four `masked` rows, one test, covering each clause: several values, no occurrence, an empty value, an empty list. 2 has three rows, covering the restore after `--once`, after the loop ended by a signal and after exit 2 (the failing side), and it adds the check that the handler differs while `fetch` runs. 3 has four rows covering `KeyboardInterrupt` and `SystemExit(3)` under `--once` and in the loop, with the login file and standard error asserted. Each criterion is one test function with no open decision. 4 and 5 are the two closing criteria, in order.
   Smoke test: the pytest command is runnable. The project's pytest config already sets `-q` and the command passes none. The `Expect:` line can be checked against the summary line, which holds `passed` and neither `failed` nor `error`.
   Architecture: tests only, in `tests/domain/` and `tests/entry/` as the layer mirror requires, using the shared support module and fixture. No layer is crossed.
   Scope: the story is listed in `feature.md` as S0012. It changes no `src/` module and no S0004 test, and it leaves out the two items that need the human's leave, as `feature.md` and decision 21 say.
4. factory: started tests as vm.
5. tester: Question on criterion 2. The Interface says "`main` installs its own `SIGTERM` and `SIGINT` handlers while it runs". Criterion 2 adds "While the source's `fetch` runs, `signal.getsignal(signal.SIGTERM)` is not the test's handler", but does not say which rows that applies to. In the code, `--once` returns before `_stop_on_signal` (`src/factory/entry/refresh_token.py:57-58`). So under `--once`, `fetch` runs under the test's own handler, and the check would fail there. Fixing that means changing `src/factory/`, which this story rules out. In the exit-2 row `fetch` never runs.

   Options:
   (a) Check the handler during `fetch` only in the loop row. The code passes as it is, and the Interface sentence means "while the loop runs".
   (b) Check it in the `--once` row too. That test fails, and the story has to allow a `src/` change so that `--once` installs the handlers as well.
   I would choose (a). The tests in the working tree do (a) now: the `once` and `url-unset` rows don't check the handler during `fetch`. If you choose (b), the next run turns on the `watched` flag of the `once` row in `test_main_puts_back_the_signal_handlers_it_found`, and the story is refined to allow the `src/` change.

   What is done (written, `make test` green, `make lint` green; all pass because the code already exists, as the story expects):
   criterion 1: tests/domain/test_tokens_masked.py::test_every_non_empty_hidden_value_is_replaced_by_the_mask
   criterion 2: tests/entry/test_refresh_token_signals.py::test_main_puts_back_the_signal_handlers_it_found
   criterion 3: tests/entry/test_refresh_token_signals.py::test_an_interrupt_or_exit_of_a_refresh_leaves_main_as_raised
   Files created: tests/domain/test_tokens_masked.py, tests/entry/test_refresh_token_signals.py. Every module imported, so the test run reported none it could not import.

   Notes:
   - `ScriptedTokenSource` in `tests/token_support.py` raises only `Exception`, not `KeyboardInterrupt`, so the new module has its own `RaisingSource`.
   - The new module has its own `environ`, `login_file` and `scripted` helpers instead of moving S0004's from `tests/entry/test_refresh_token.py` under the standing leave. This story says S0004's tests stay unchanged. If you want them in one shared place, that move is a later story's.
6. 2026-11-01 human: Answer: (a). The handler is checked during `fetch` in the loop row only; `--once` refreshes once and returns before the loop's handlers are installed, which is what the Interface's sentence means. No `src/` change.

   On your second note: move `environ`, `login_file` and `scripted` to a shared place now, under the standing leave to move a shared test helper (`tests/token_support.py`, or `tests/conftest.py` for a fixture), and have `tests/entry/test_refresh_token.py` use them from there. "S0004's tests stay unchanged" means they keep their names and check the same things, which the standing leave keeps; a copy left in two modules is what the reviewer counts as a finding, and it would cost a round.
7. factory: started tests as vm.
8. tester: Following the human's answer (a) in entry 6: the handler is checked during `fetch` only in the loop row (`watched` stays False for the `once` and `url-unset` rows). As the human asked, `environ`, `login_file` and `scripted` now live in one shared place under the standing leave to move a shared test helper.

   criterion 1: tests/domain/test_tokens_masked.py::test_every_non_empty_hidden_value_is_replaced_by_the_mask
   criterion 2: tests/entry/test_refresh_token_signals.py::test_main_puts_back_the_signal_handlers_it_found
   criterion 3: tests/entry/test_refresh_token_signals.py::test_an_interrupt_or_exit_of_a_refresh_leaves_main_as_raised

   Files created (in the earlier run, already on the branch): tests/domain/test_tokens_masked.py, tests/entry/test_refresh_token_signals.py.

   Shared helpers moved under the standing leave:
   - The fixtures `secret_file`, `login_file` and `environ` moved from tests/entry/test_refresh_token.py into tests/conftest.py. They are unchanged except for their docstrings, which now name "the token refresher".
   - `scripted` moved into tests/token_support.py.
   - Earlier test file changed: tests/entry/test_refresh_token.py. It drops its own copies and imports `scripted` from `token_support`. Every test in it keeps its name and checks the same thing.
   - tests/entry/test_refresh_token_signals.py drops its copies too. Its old `login_file` fixture pre-wrote "old-token". The exception test now writes that earlier content itself, after creating the shared `login_file`'s parent directory. The `environ` it uses is the shared one, so its secret file is now under `secret/`, as in S0004's tests.

   Test run: `make test` and `make lint` are green. Every test passes because the code under test already exists, as the story expects. Every module imported, so there were no modules the test run could not import. Type check skipped as the stage says.

   `lint`: lint: green (0.2 s)
   `test`: test: green (173.6 s)
