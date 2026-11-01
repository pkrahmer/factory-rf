---
stage: docs
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 492
comments_read: [6556376362, 6556503545, 6557892923]
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
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-01T10:00:48.436171Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-01T10:04:22.624923Z'
  stage: doing
  run: e03571afdef14dbfb368d00a38e1454e
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-01T10:06:40.933170Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-01T10:06:58.823135Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-01T10:07:11.837418Z'
  stage: doing
  run: ed59568a8e8246b0a62cb2f1969a49a2
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-01T10:07:31.968088Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-01T10:13:46.570201Z'
  stage: tests
  run: 996d8c0180774e7dbdfde268851a17d7
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-01T10:14:06.981623Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-01T10:20:29.713672Z'
  stage: doing
  run: 4ee2725fd2fc422b9abab9f31446b79b
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-01T10:20:50.425933Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-01T10:21:39.453746Z'
  stage: review
  run: 5fbae22966b74826bb6fdcfe2ae5ff1d
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-01T10:22:00.010978Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-01T10:22:14.836508Z'
  stage: doing
  run: c2b05b2d6d1d4fad84573de4d1d9d799
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-01T10:22:35.261099Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-11-01T10:29:05.893339Z'
  stage: tests
  run: f2cde5f6b95f4c27bbf8f13fd6d1e40f
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-01T10:29:26.160445Z'
  stage: doing
- number: 25
  speaker: coder
  kind: question
  at: '2026-11-01T10:33:09.385142Z'
  stage: doing
  run: 0d14cd9cae26409ab345a5e8e14eaa2b
  blocked: question
- number: 26
  speaker: human
  kind: comment
  at: '2026-11-01T12:25:41.020118Z'
  stage: doing
- number: 27
  speaker: factory
  kind: started
  at: '2026-11-01T12:25:58.915769Z'
  stage: doing
- number: 28
  speaker: coder
  kind: result
  at: '2026-11-01T12:34:53.985795Z'
  stage: doing
  run: e76727bba739408b836236c0d5924c2b
- number: 29
  speaker: factory
  kind: started
  at: '2026-11-01T12:35:14.202151Z'
  stage: review
- number: 30
  speaker: reviewer
  kind: result
  at: '2026-11-01T12:36:01.531821Z'
  stage: review
  run: 5304fe46a84c492aa4bf9acdd0db40f9
---

# The refresher's remaining rules get their tests
<!-- proposed by feature acceptance of 2026-11-01; refine before starting -->

## Description

S0004's refresher (`python -m factory.entry.refresh_token`) states three rules that no test pins. Its review (entries 69 and 77) noted them after the human's entry 52, which kept further edge cases "as a note, which I record on `main` for a later story"; the feature acceptance F0047-A0001 found them recorded nowhere else. The rules:

- `main` restores the previous `SIGTERM` and `SIGINT` handlers before it returns. Every loop test runs under the `restored_signals` fixture, which restores them anyway.
- A `KeyboardInterrupt` or `SystemExit` of one refresh is not caught.
- `masked` in `factory.domain.tokens` replaces every non-empty hidden value with `***`. It is tested only through the adapter and the command.

This story writes those tests; the code is expected to pass them as it is. Unchanged: every module under `src/factory/` (a test that fails is a finding for the coder, not a test change). S0004's tests keep their names and what they check; the helpers they share with the new tests (the secret-file, login-file and environ fixtures, `scripted` and `never_sleep`) move to `tests/conftest.py` and `tests/token_support.py` under the standing leave to move a shared test helper. Left out: the `incomplete-read` row that computes its expected detail with the code's own expression, and the names `SECOND` and `SECOND_CLIENT` of `tests/test_hosting_search.py`. Both are changes to S0004's tests and need a leave in `feature.md`; refine this story to add them if the human gives it.

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
9. factory: started doing as vm.
10. coder: Question: one of the tester's new tests fails `make types`. I can't fix this from `src/`, and the coder doesn't edit tests (R9).

    What I found: I changed nothing. As the story expects, the code already passes every new test. `make -k check` is green on lint, layers, sast, secrets, licenses and test (`test: green (174.2 s)`). `make types` is red:

    ```
    tests/entry/test_refresh_token_signals.py:108: error: "BaseException" has no attribute "code"  [attr-defined]
    ```

    The cause is in `test_an_interrupt_or_exit_of_a_refresh_leaves_main_as_raised`. It narrows with `isinstance(error, SystemExit)` and then reads `raised.value.code`. mypy narrows `error`, not `raised.value`, which is still typed `BaseException`. The tester's entry 8 says they skipped the type check, so this wasn't caught.

    Options:
    (a) Leave the test to the tester for a one-line change: line 108 reads `error.code` instead of `raised.value.code`. The line before already asserts `raised.value is error`, so the test checks the same thing. I would choose this.
    (b) Narrow `raised.value` instead: `assert isinstance(raised.value, SystemExit)` inside the branch, then `raised.value.code == 3`.
    No `src/` change can make this check green. Choosing (a) or (b) sends the story to the tests stage for exactly that line.

    Built: nothing; no file under `src/` changed. The Description is unchanged: entry 6 kept its meaning (the handler is checked during `fetch` in the loop row only).
11. 2026-11-01 human: Answer: (a). The tester changes line 108 of `tests/entry/test_refresh_token_signals.py` (this story's own file) to read `error.code`; the line before already asserts `raised.value is error`. Then `make types` once before ending.
12. factory: started doing as vm.
13. coder: Following the human's answer (a) in entry 11: in `tests/entry/test_refresh_token_signals.py::test_an_interrupt_or_exit_of_a_refresh_leaves_main_as_raised`, line 108 should read `assert error.code == 3` instead of `assert raised.value.code == 3`. After that, run `make types` once before ending.

    Built: nothing. No file under `src/` changed, because the code already passes every new test, as the story expects. My entry 10 has the earlier `make -k check` run: every target was green except `make types`, which fails on exactly that line ("BaseException" has no attribute "code" [attr-defined]).

    Rejected: option (b), narrowing `raised.value` with a second `isinstance`. The human chose (a).

    Description unchanged: entries 6 and 11 settle how the tests are written. They don't change what the task means.

    Noticed, not touched: nothing else.
14. factory: started tests as vm.
15. tester: Following the human's answer (a) in entry 11, as the coder's entry 13 names it: in `tests/entry/test_refresh_token_signals.py::test_an_interrupt_or_exit_of_a_refresh_leaves_main_as_raised`, line 108 now reads `assert error.code == 3` instead of `assert raised.value.code == 3`. The line before still asserts `raised.value is error`, so the test checks the same thing. mypy now types `.code` through the `isinstance` narrowing of `error`. Nothing else changed.

    The criterion-to-test mapping is the same as in entry 8:
    criterion 1: tests/domain/test_tokens_masked.py::test_every_non_empty_hidden_value_is_replaced_by_the_mask
    criterion 2: tests/entry/test_refresh_token_signals.py::test_main_puts_back_the_signal_handlers_it_found
    criterion 3: tests/entry/test_refresh_token_signals.py::test_an_interrupt_or_exit_of_a_refresh_leaves_main_as_raised

    Files created: none in this run. The two test files are already on the branch. Changed in this run: tests/entry/test_refresh_token_signals.py, line 108 only.
    Modules the test run could not import: none.

    Runs, as the human asked:
    - `make types`: types: green (4.6 s). This was the target that failed before ("BaseException" has no attribute "code").
    - `make test`: test: green (173.7 s)
    - `make lint`: lint: green (0.2 s)

    `lint`: lint: green (0.2 s)
    `test`: test: green (173.7 s)
16. factory: started doing as vm.
17. coder: Built: nothing. No file under `src/` changed, which is what the story expects: the code already passes every new test. The only diff against `main` outside `factory/` is the tester's work: tests/conftest.py, tests/token_support.py, tests/entry/test_refresh_token.py, tests/domain/test_tokens_masked.py and tests/entry/test_refresh_token_signals.py.

    After the tester's change to line 108 in entry 15, I ran `make check` and it is green: `test: green (173.8 s)`, then `check: green`. In entry 10 `make types` was the one red target, and it now passes.

    Main choice: I left the code as it is. I rejected changing `src/factory/entry/refresh_token.py` so that `--once` installs the signal handlers as well; the human ruled that out in entry 6 (answer (a)).

    Refactor: there is no diff of mine to refactor, so nothing changed.

    Description unchanged. Entries 6 and 11 settle how the tests are written; they do not change what the task means.

    Noticed but not touched: `src/factory/entry/refresh_token.py:136` is the one line of that module that coverage leaves uncovered. It is outside this story's scope.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
18. factory: started review as vm.
19. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`: five test files, nothing under `src/`. Group 1 (acceptance criteria) holds. Criterion 1 is the four exact rows of one parametrized test. Criterion 2 is three rows, and the handler is checked during `fetch` in the loop row only, as the human's answer (a) in entry 6 says. Criterion 3 is four rows (two exceptions × `--once`/loop). Each row checks `raised.value is error`, code 3, the earlier content of the login file and that stderr has no `refresh_token:` line. In the loop rows, `never_sleep` makes a caught exception fail the test, so those rows really test that the exception is not caught. I read the tests against `src/factory/entry/refresh_token.py:57-63,127-137` and `src/factory/domain/tokens.py:31-36`, and they test what each criterion names. The Interface states no numeric limit. In entry 17 the coder's `make check` was green. Group 2 (architecture) and group 3 (security) hold: tests only, with the shared support module and fixtures. Group 4 (quality) fails on one point:

    1. `tests/entry/test_refresh_token_signals.py:53` (`never_sleep`) is a second copy of `never_sleep` at `tests/entry/test_refresh_token.py:51`. The body is the same and only the docstring differs. Fix: under the standing leave, the tester moves `never_sleep` into `tests/token_support.py` beside `scripted`, and both modules import it from there. Every earlier test keeps its name and what it checks.

    Considered and not counted: `RaisingSource` is not a copy, because `ScriptedTokenSource` takes only `Exception` and cannot raise `KeyboardInterrupt`/`SystemExit`. `terminate` and `WatchingSource` are new shapes that no existing helper covers.

    Earlier tests (item 6):
    - tests/conftest.py: standing leave to move a shared test helper, and the human's answer in entry 6. Only the secret-file, login-file and environ fixtures were added, moved from `tests/entry/test_refresh_token.py`; only their docstrings changed.
    - tests/entry/test_refresh_token.py: standing leave to move a shared test helper, and the human's answer in entry 6. It drops its copies of the three fixtures and of `scripted` and imports `scripted` from `token_support`. Every test keeps its name and what it checks.
    - tests/token_support.py: standing leave to move a shared test helper, and the human's answer in entry 6. `scripted` was moved in unchanged.
20. factory: started doing as vm.
21. coder: This round fixes the reviewer's finding in entry 19, which is about tests only. Move `never_sleep` into `tests/token_support.py` beside `scripted`, under the standing leave to move a shared test helper. Then delete its two copies, `tests/entry/test_refresh_token_signals.py:53` and `tests/entry/test_refresh_token.py:51`, and have both modules import it from `token_support`. Every earlier test keeps its name and checks the same thing. I confirmed the two copies have the same body (`raise AssertionError(f"waited {seconds} s")`); only the docstrings differ. The shared copy needs a docstring that fits both modules, for example "A wait the run must not reach."

    Built: nothing. No file under `src/` changed, and this finding doesn't need one. The code already passes every new test, and entry 17's `make check` was green.

    Main choice: I end with `tests` and don't touch the test files myself. The finding is a copied test helper, and `CLAUDE.md` gives the tester, never the coder, a standing leave to move one. I rejected a `question`, because that leave covers this move without asking the human.

    Description unchanged: the finding is about where a helper lives. It doesn't change what the task means.

    Noticed, not touched: as in entry 17, `src/factory/entry/refresh_token.py:136` is still the module's only line that coverage leaves uncovered. It is outside this story's scope.
22. factory: started tests as vm.
23. tester: This round fixes the reviewer's finding in entry 19, as the coder's entry 21 names it. Under the standing leave to move a shared test helper, `never_sleep` now lives in `tests/token_support.py`, beside `scripted`. Its docstring is "A wait the run must not reach.", which fits both modules. Its body is unchanged: `raise AssertionError(f"waited {seconds} s")`. The module docstring of `tests/token_support.py` now names it too; I shortened that line to stay within the length limit.

    Earlier test files changed under that leave:
    - tests/entry/test_refresh_token.py: I deleted its copy of `never_sleep` and it now imports it from `token_support`. Every test keeps its name and checks the same thing.
    - tests/entry/test_refresh_token_signals.py: this story's own file. I deleted its copy and it now imports it from `token_support`.

    The criterion-to-test mapping is unchanged:
    criterion 1: tests/domain/test_tokens_masked.py::test_every_non_empty_hidden_value_is_replaced_by_the_mask
    criterion 2: tests/entry/test_refresh_token_signals.py::test_main_puts_back_the_signal_handlers_it_found
    criterion 3: tests/entry/test_refresh_token_signals.py::test_an_interrupt_or_exit_of_a_refresh_leaves_main_as_raised

    Files created: none in this run. Changed in this run: tests/token_support.py, tests/entry/test_refresh_token.py and tests/entry/test_refresh_token_signals.py.
    Modules the test run could not import: none.

    Runs:
    - `make test`: test: green (174.0 s).
    - `make lint`: the first run failed on the long module docstring (tests/token_support.py:1, E501). After shortening it: lint: green (0.2 s).
    - `make types`: types: green (4.5 s).

    `lint`: lint: green (0.2 s)
    `test`: test: green (173.3 s)
24. factory: started doing as vm.
25. coder: Question: `make check` is red on `make secrets`. The cause is a line in this work item's journal, not in code or tests, and I can't fix it in this stage.

    What happened: the tester's entry 23 fixed the reviewer's finding. `never_sleep` now exists only in `tests/token_support.py:23`, and both test modules import it from there. With that, `make -k check` passes every target except one: lint, types, layers, sast, licenses and `test: green (173.5 s)` are green. `make secrets` fails:

    ```
    Secret Type: Secret Keyword
    Location:    factory/features/F0047-the-factory-runs-in-a-cloud-run-job/in-progress/F0047-S0012-the-refresher-s-remaining-rules-get-their-tests.md:316
    ```

    Line 316 is in the reviewer's entry 19: "- tests/conftest.py: standing leave … Only the secret-file, login-file and environ fixtures were added …". detect-secrets reads the fixture name `secret_file` in that sentence as a secret keyword. My green `make check` in entry 17 ran before entry 19 was written. So this is new, and it comes from the journal, which belongs to the factory. I may not edit the journal (R5), and `CLAUDE.md` forbids a new `.secrets.baseline` entry or a `pragma: allowlist secret` unless I ask first.

    Options:
    (a) You add a `.secrets.baseline` entry for this false positive, or give me leave to add it. I would choose this: the journal stays exactly as written, and the finding really is a false positive (a fixture's name, not a value).
    (b) You reword line 316 of entry 19 in your own commit, for example to "the secret-file, login-file and environ fixtures", so the detector no longer matches.
    (c) Change the detector's configuration so it skips work-item journals. That is broader than this story, and I would not choose it.

    Built: nothing in this round. No file under `src/` changed, and the code passes every new test as it is. Description unchanged.

    Noticed, not touched: as in entry 17, `src/factory/entry/refresh_token.py:136` is still the only line of that module that coverage leaves uncovered.
26. 2026-11-01 human: Answer: (b), done. The two places in the journal that named the fixtures as `secret_file` now read "secret-file, login-file and environ fixtures" (commit 1b6034367 on the branch, the human's leave); `make secrets` finds nothing in the work item now. Run `make check` and hand on.
27. factory: started doing as vm.
28. coder: Following the human's answer (b) in entry 26: the journal no longer names the fixture in a way detect-secrets flags (commit 1b6034367). I ran `make check` and it is green on every target: lint, types, layers, sast, `secrets: green (0.3 s)`, licenses, `test: green (164.1 s)`, then `check: green`.

    Built: nothing in this round. No file under `src/` changed, which is what the story expects: the code passes every new test as it is. The diff against `main` outside `factory/` is the tester's work only: tests/conftest.py, tests/token_support.py (now with `scripted` and `never_sleep`), tests/entry/test_refresh_token.py, tests/domain/test_tokens_masked.py and tests/entry/test_refresh_token_signals.py.

    Main choice: I left the code and the tests as they are and handed on. I rejected options (a) and (c) of entry 25, a `.secrets.baseline` entry and a change to the detector's configuration. The human's reword made both unnecessary.

    Refactor: there is no diff of mine, so nothing changed.

    Description unchanged: entry 26 fixes wording in the journal and does not change what the task means.

    Noticed, not touched: `src/factory/entry/refresh_token.py:136` is still the only line of that module that coverage leaves uncovered. It is outside this story's scope.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
29. factory: started review as vm.
30. reviewer: no findings

    I reviewed `git diff main...HEAD -- . ':!factory'`: five test files, nothing under `src/`. Round 1 fixes entry 19's finding. `never_sleep` now exists only at `tests/token_support.py:23`, and both modules import it from there. A grep of `tests/` finds one copy each of `never_sleep`, `scripted` and the secret-file, login-file and environ fixtures.
    Group 1 holds. Criterion 1 is the four exact rows of one parametrized test (`tests/domain/test_tokens_masked.py`). Criterion 2 is three rows of `test_main_puts_back_the_signal_handlers_it_found`. They check the restore of both handlers by identity after `--once`, after the loop ended by `SIGTERM` and after exit 2. The handler during `fetch` is checked only in the loop row, as the human's answer (a) in entry 6 says. I read this against `src/factory/entry/refresh_token.py:57-63,127-137`. Criterion 3 is four rows (two exceptions × `--once`/loop). Each row checks that the exception left as raised, the code 3, the earlier content of the login file and that stderr has no `refresh_token:` line. `never_sleep` makes an exception the loop caught fail the test. The Interface states no numeric limit. The coder's `make check` in entry 28 was green, after the human's journal reword in entry 26.
    Groups 2 to 5 hold: tests only, in the layer mirror, through the shared support module and fixtures. No marker silences a check, there are no secrets, and there is no dead code.

    description corrected: "Unchanged: every module under `src/factory/` (...), and S0004's tests." -> "Unchanged: every module under `src/factory/` (...). S0004's tests keep their names and what they check; the helpers they share with the new tests (the secret-file, login-file and environ fixtures, `scripted` and `never_sleep`) move to `tests/conftest.py` and `tests/token_support.py` under the standing leave to move a shared test helper." This follows the human's answer in entry 6. I wrote the fixture names in words, as in entry 26, so that detect-secrets does not flag them.

    Earlier tests (item 6):
    - tests/conftest.py: the standing leave to move a shared test helper, and the human's answer in entry 6. It only adds the secret-file, login-file and environ fixtures moved from tests/entry/test_refresh_token.py; only their docstrings changed.
    - tests/entry/test_refresh_token.py: the standing leave to move a shared test helper, and the human's answer in entry 6. It drops its copies of the three fixtures, `scripted` and `never_sleep` and imports them from the shared places. Every test keeps its name and what it checks.
    - tests/token_support.py: the standing leave to move a shared test helper, and the human's answer in entry 6. `scripted` and `never_sleep` moved in with the same bodies, and the module docstring names them.
