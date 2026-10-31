---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 485
comments_read: [6547461929, 6547499303, 6547757087]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-31T18:28:13.483562Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-31T18:28:13.489362Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-31T18:28:36.343974Z'
  stage: intake
  run: 273dfe6c5cf34a6cbd137820f910b0be
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-31T18:30:56.023993Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-31T18:31:13.667716Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-31T18:31:35.962632Z'
  stage: intake
  run: b032c6603b4b4ab7959a124b35582e96
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-31T18:31:56.119016Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-31T18:32:29.594579Z'
  stage: tests
  run: 99abe17cb5844bb88c91d9f4c25c1923
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-31T18:34:47.752318Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-31T18:35:05.467890Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-10-31T18:43:11.621775Z'
  stage: tests
  run: 0e8204d4eafb473c9edc6d20588c7bc5
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-31T18:43:34.121408Z'
  stage: doing
- number: 13
  speaker: coder
  kind: question
  at: '2026-10-31T18:55:18.761625Z'
  stage: doing
  run: 020995acf7214c7b9fe7835a7d710756
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-10-31T18:57:38.771324Z'
  stage: doing
---

# A refresher keeps a bearer token in the login file

## Description

A model API behind an OAuth2 client-credentials grant gives out a bearer token that lives one hour (measured on 2026-10-31, `planning/cloud-sandbox/`, P10: `expires_in` 3599, a 1278-character JWT; opencode reading it as the API key ran a real task). The opencode runtime already reads the file named by `FACTORY_API_LOGIN_FILE` at every call and hands its content to the agent as `ANTHROPIC_API_KEY`; the F0046 provider file names that variable as the provider's key. So the factory needs no runtime change, only something that keeps that file fresh. This story adds a command, `python -m factory.entry.refresh_token`, that requests a token from the grant's endpoint with a client id and a client secret read from a file (Secret Manager mounts it), writes the token into the login file atomically, and again every ten minutes (the human, 2026-10-31: a fixed interval, not a rule on the token's life). A container mounts the file when it starts and its login shell reads it once, so a run has at least the token's life less ten minutes: fifty minutes with the measured token, more than one forty-minute stage. A failed request keeps the old file and tries again after a minute. The client secret appears in no log line, no error message and no child's environment. The HTTP goes through the standard library, which honours `https_proxy` and `no_proxy`. Unchanged: the runtimes, the login shell, every setting that exists. Left to later stories: running it (S0006).

## Interface

`factory.domain.tokens` (domain, new): `class Token(BaseModel)` frozen with `value: str` (not blank, no whitespace) and `expires_in: PositiveInt` (seconds); `REFRESH_INTERVAL = timedelta(minutes=10)`, `MIN_REFRESH_INTERVAL = timedelta(seconds=30)`, `RETRY_INTERVAL = timedelta(minutes=1)` and `def refresh_wait(token: Token) -> timedelta`: `REFRESH_INTERVAL`, or half the token's life when that is shorter (a token that lives under twenty minutes would otherwise expire between two refreshes), and at least `MIN_REFRESH_INTERVAL`.

`factory.domain.errors` (domain): `class TokenError(BoundaryError)` with `detail`; the message is `token request failed: <detail>`.

`factory.application.tokens` (application, new): `class TokenSource(ABC)` with `fetch() -> Token`, raising `TokenError`; `class TokenRefresher` with `__init__(source: TokenSource, target: Path)`, `refresh() -> Token` (fetch, then `replace_text(target, token.value)`; `TokenError` propagates, an `OSError` of the write is a `TokenError("cannot write <target>: <error>")`), and `wait_after(token) -> timedelta` (`refresh_wait`).

`factory.adapters.oauth_token` (adapters, new): `class ClientCredentialsTokenSource(TokenSource)` with `__init__(url: str, client_id: str, client_secret: str, scope: str, *, open_url=urllib.request.urlopen, timeout: float = 30.0)`. `fetch` posts `client_id`, `scope`, `client_secret` and `grant_type=client_credentials` form-encoded (`Content-Type: application/x-www-form-urlencoded`) to `url` through `open_url(request, timeout)` used as a context manager, reads the body as JSON and returns `Token(access_token, expires_in)` (`expires_in` as an integer or a numeric string). A `urllib.error.HTTPError` becomes `TokenError("HTTP <code>: <the body's error and the first line of its error_description, at most 200 characters>")`, a `URLError`, `OSError` or `TimeoutError` becomes `TokenError(<its message>)`, a body that is no JSON object or lacks `access_token` or a positive `expires_in` becomes `TokenError("the answer holds no access_token")` or `("the answer holds no expires_in")`. Every detail has the client secret and the token removed (replaced by `***`).

`factory.entry.refresh_token` (entry, new): `main(argv: Sequence[str] | None = None, environ=os.environ, ...) -> int`. It reads `FACTORY_TOKEN_URL`, `FACTORY_TOKEN_SCOPE`, `FACTORY_TOKEN_CLIENT_ID`, `FACTORY_TOKEN_CLIENT_SECRET_FILE` and `FACTORY_API_LOGIN_FILE`; a missing or blank one prints `refresh_token: <variable> is not set` to standard error and exits 2; an unreadable or blank secret file exits 2 with `refresh_token: cannot read <path>`. With `--once` it refreshes once and exits 0, or 1 after printing `refresh_token: <the error>`; without it it refreshes, then waits `wait_after` and repeats until `SIGTERM` or `SIGINT` (exit 0); after a failure it keeps the old file, prints the error and waits `RETRY_INTERVAL`. Each success prints `token refreshed: valid <n> s, next in <m> s`. Waiting and the clock are injected so that no test sleeps.

Tests (the tester writes them): `tests/domain/test_tokens.py`, `tests/application/test_tokens.py`, `tests/adapters/test_oauth_token.py` (an injected `open_url`), `tests/entry/test_refresh_token.py`.

## Acceptance criteria

1. `refresh_wait`, rows of one test: a life of 3599 s waits 600 s (the interval); 7200 s waits 600 s; 1200 s waits 600 s; 1000 s waits 500 s (half of a short life); 40 s waits 30 s (the floor); 10 s waits 30 s.
2. `Token` refuses a blank value, a value with a space or a newline, an `expires_in` of 0 and of -1, and accepts 1.
3. `ClientCredentialsTokenSource.fetch` with an `open_url` that records its request and answers `{"access_token": "t", "expires_in": 3599}`: the request is a POST to the given URL with the content type above and a body that holds the four fields, URL-encoded (a secret with `&`, `=`, `+` and a space round-trips through `parse_qs`), and the token is `Token(value="t", expires_in=3599)`; `"expires_in": "3599"` gives the same; `open_url` receives `timeout=30.0` by default and the given value when `timeout` is passed.
4. Faults, rows of one test: an `HTTPError` 400 with the body `{"error": "invalid_client", "error_description": "AADSTS7000215: bad secret\r\nTrace ID: x"}` gives `HTTP 400: invalid_client: AADSTS7000215: bad secret`; the 200-character cut applies to the first line of `error_description` alone, so an error description of 300 characters gives `HTTP 400: invalid_client: ` followed by its first 200 characters; an `HTTPError` 500 whose body is not JSON gives `HTTP 500`; an `HTTPError` 400 whose JSON body has neither `error` nor `error_description` gives `HTTP 400`; a `URLError("no route")` gives `no route`; a plain `OSError("boom")` gives `boom`; a `TimeoutError` gives its message; the body `[]`, a body without `access_token` and a body with `expires_in` 0 give the sentences of the Interface; none of these details contains the client secret or the token even when the server's body echoes either (the echo is replaced by `***`, one row for the secret and one for the token).
5. `TokenRefresher.refresh` writes the token into the target with no other text and no newline, replaces an older value, creates the folder, leaves the old file untouched when the source raises, and turns an `OSError` of the write (a target that is a folder) into `TokenError("cannot write <target>: <error>")`.
6. The command: a missing and a blank variable each exit 2 and name it as `refresh_token: <variable> is not set` on standard error (two rows per variable); a missing secret file and a blank one each exit 2 with `refresh_token: cannot read <path>` on standard error; `--once` with a source that answers 3599 s writes the file, prints `token refreshed: valid 3599 s, next in 600 s` (the wait's whole seconds) and exits 0; `--once` with a source that fails prints `refresh_token: token request failed: <detail>` to standard error, leaves the file as it was and exits 1.
7. The loop (injected wait), rows `SIGTERM` and `SIGINT`: two successes then the signal gives two writes, waits of the refresh interval, exit 0; a failure between two successes keeps the file of the first, prints the error, waits `RETRY_INTERVAL` once and goes on.
8. Neither standard output, standard error, a raised error nor the environment given to a child process contains the client secret or the token (a test over all of them with a secret `s3cret-value` and a token `tok-abc`).
9. `make check` stays green.
10. docs: `docs/operator-guide.md`: a subsection *A bearer token for the model API* with the variables, what the command writes and when (every ten minutes; a run reads the file when its container starts, so the token must live longer than the interval plus the longest stage), that the file is the one `FACTORY_API_LOGIN_FILE` names, the provider file's `api_key_env` that reads it as `ANTHROPIC_API_KEY`, the proxy (set `NO_PROXY` for an internal API host and `https_proxy` for the token endpoint) and that the secret is a file mounted from Secret Manager. `docs/project-guide/agents.md`: *The opencode runtime* names the refresher. `docs/decisions.md`: an entry *A refresher keeps the bearer token fresh*, from the feature's decisions 7 and 8. `README.md`: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run python - "$d" <<'PY'
import io, json, sys
from pathlib import Path
from factory.adapters.oauth_token import ClientCredentialsTokenSource
from factory.application.tokens import TokenRefresher
def opener(request, timeout):
    assert b"grant_type=client_credentials" in request.data
    return io.BytesIO(json.dumps({"access_token": "tok-1", "expires_in": 3599}).encode())
source = ClientCredentialsTokenSource("https://example.invalid/token", "client-1", "s3cret", "api://x/.default", open_url=opener)
target = Path(sys.argv[1]) / "login"
refresher = TokenRefresher(source, target)
token = refresher.refresh()
print(target.read_text(), token.expires_in, refresher.wait_after(token).total_seconds())
PY
```
Expect: one line, `tok-1 3599 600.0`

```bash
FACTORY_TOKEN_URL= uv run python -m factory.entry.refresh_token --once; echo "exit $?"
```
Expect: two lines, `refresh_token: FACTORY_TOKEN_URL is not set` and `exit 2`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-31 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed, so none from it). The Interface, smoke test, architecture and scope are otherwise fine; these gaps in the criteria are not:

   1. SIGINT: the Interface ends the loop on `SIGTERM` or `SIGINT` (exit 0). Criterion 7 tests only `SIGTERM`. Proposal: add a row for `SIGINT`, with the same two writes and exit 0.

   2. An unreadable secret file: the Interface says exit 2 with `refresh_token: cannot read <path>`. Criterion 6 covers only a blank file, and checks the exit code but not the message. Proposal: add rows for a missing file and for a blank file, each with exit 2 and the exact message on standard error.

   3. HTTPError detail, cases the Interface leaves open:
      a. A body that is not JSON, or a JSON body with no `error` and no `error_description`. What is the detail? Proposal: `HTTP <code>` alone, with one criterion row for each case.
      b. "at most 200 characters": does that cut the description line alone, or the whole detail after `HTTP 400: `? Criterion 4 only says "cut at 200". Proposal: it cuts the `error_description` line alone, and the criterion states the expected full string.

   4. Criterion 4 has no row for a plain `OSError` (the Interface names it next to `URLError` and `TimeoutError`). It also tests only the client secret being removed from details, not the token, although the Interface says both become `***`. Proposal: add an `OSError` row and a row where the server's body echoes the token.

   5. Criterion 3 does not check that `open_url` receives `timeout=30.0` by default, or a custom value. The `timeout` parameter is Interface behaviour. Proposal: add a check of the timeout argument in criterion 3.

   6. Criterion 6 says a missing variable exits 2, but the Interface says "missing or blank". Proposal: make each variable's row cover both an unset and a blank value.
4. 2026-10-31 human: Answers to question 3: all six as you propose.

   1. Yes: a `SIGINT` row in criterion 7, the same two writes and exit 0.
   2. Yes: rows for a missing secret file and a blank one, each exit 2 with the exact message on standard error.
   3. a. Yes: a body that is not JSON, and a JSON body with neither `error` nor `error_description`, each give `HTTP <code>` alone (one row each).
      b. The 200-character cut applies to the first line of `error_description` alone; the criterion states the full expected string.
   4. Yes: an `OSError` row, and a row where the server's body echoes the token, which is replaced by `***` as the secret is.
   5. Yes: criterion 3 checks that `open_url` receives `timeout=30.0` by default and a custom value when one is given.
   6. Yes: each variable's row covers both an unset and a blank value.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: concrete modules and signatures (`factory.domain.tokens`, `factory.domain.errors.TokenError`, `factory.application.tokens`, `factory.adapters.oauth_token`, `factory.entry.refresh_token`). Every rule has a criterion on both sides. The human's answers in journal entry 4 settled the open cases: a non-JSON body or a JSON body without `error`/`error_description` gives `HTTP <code>`, and the 200-character cut applies to the first line of `error_description` alone.
   - Criteria: after the edits below, each is testable by one parametrized test. Entry 4 (the human's answers 1 to 6) is carried into the story as the human's edit, not as my own improvement:
     - Criterion 3 now checks `timeout=30.0` by default and a custom value.
     - Criterion 4 now has rows for the non-JSON body, the JSON body without `error` or `error_description`, a plain `OSError`, and the echoed token. It also states that the cut applies to the first line of `error_description`.
     - Criterion 6 now covers missing and blank variables, and a missing and a blank secret file, each with the exact stderr message.
     - Criterion 7 now has `SIGTERM` and `SIGINT` rows.
     - The Description is unchanged, since the task's meaning did not change. The two closing criteria stay last.
   - Smoke test: both commands are runnable. The first is a Python snippet with an injected opener whose output is `tok-1 3599 600.0`. The second is `FACTORY_TOKEN_URL=` with `--once`, which gives the stderr line and `exit 2`. Neither runs pytest, so the `-q` rule does not apply. Both `Expect:` lines are checkable.
   - Architecture: the layers are right. The `Token` DTO and `refresh_wait` are domain, the `TokenSource` ABC and `TokenRefresher` are application, the urllib adapter is in adapters, and the command is in entry. `TokenSource` is an ABC with the adapter inheriting it. No new dependency, and no wrapper rule is broken, because the standard library HTTP sits in one adapter.
   - Scope: this is S0004 of F0047, the refresher only. Running it is left to S0006. It is within the feature's scope and touches nothing in its "Out of scope".
7. factory: started tests as vm.
8. tester: Question before I write the tests. I stopped before writing any files. Criteria 1 to 5 can be tested against the Interface as it stands. Criteria 6, 7 and 8 cannot, because the Interface leaves `main`'s injected parameters as `...`.

   1. **How a test gives `main` its token source, its wait and its stop.** Criterion 6 needs "a source that answers 3599 s" and "a source that fails". Criterion 7 needs an injected wait and a `SIGTERM`/`SIGINT` that ends the loop. The Interface does not name any of these parameters. My proposal, following `factory.entry.run` (`install_stop_handlers`, `run_instance(sleep=…, should_stop=…)`):
      `main(argv=None, environ=os.environ, *, source: Callable[[str, str, str, str], TokenSource] | None = None, sleep: Callable[[float], None] | None = None) -> int`
      - `source` takes `url, client_id, client_secret, scope` and defaults to `ClientCredentialsTokenSource`.
      - `sleep` takes seconds and defaults to waiting on a `threading.Event`.
      - `main` installs `SIGTERM` and `SIGINT` handlers that set its stop flag, checks the flag after each wait, and restores the previous handlers before it returns.
      - The loop test's fake `sleep` records the seconds and, on the chosen wait, calls `signal.raise_signal(sig)`. That exercises the real handlers without sleeping.
      - "The clock" in the Interface would then need no parameter: nothing in the criteria reads a time.
      - Alternatives:
        - (b) inject a `threading.Event` stop and have the test set it directly. This would not test the signals themselves, so the SIGTERM/SIGINT rows would only be labels.
        - (c) other parameter names you prefer.
      - I would choose the proposal.

   2. **Criterion 8, "the environment given to a child process".** The command starts no child process, so there is nothing to observe. Options:
      - (a) Test that `os.environ` holds neither the secret nor the token after `main` has run. Any child the process later starts inherits `os.environ`.
      - (b) Drop the child clause from criterion 8.
      - (c) Name the child you mean.
      - I would choose (a).

   The tests, once the answers are in:
   - `tests/domain/test_tokens.py`
   - `tests/application/test_tokens.py`
   - `tests/adapters/test_oauth_token.py`
   - `tests/entry/test_refresh_token.py`

   A note for the coder, not a question for the tests: the Interface has `factory.application.tokens` call `replace_text`, but that function lives in `factory.adapters.atomic_file`, and the application layer may not import adapters.
9. 2026-10-31 human: Answers to question 8:

   1. Your proposal: `main(argv=None, environ=os.environ, *, source: Callable[[str, str, str, str], TokenSource] | None = None, sleep: Callable[[float], None] | None = None) -> int`, with `source` defaulting to `ClientCredentialsTokenSource` and `sleep` to waiting on a `threading.Event`; `main` installs `SIGTERM` and `SIGINT` handlers that set its stop flag, checks it after each wait, and restores the previous handlers before it returns. The loop test raises the real signal from its fake `sleep`. No clock parameter.
   2. (a): after `main` has run, `os.environ` holds neither the secret nor the token.

   On your note to the coder: right, the application layer may not import `factory.adapters.atomic_file`. `TokenRefresher` takes the writer as a third constructor argument, `write: Callable[[Path, str], None]`, without a default; `factory.entry.refresh_token` passes `replace_text`. Criterion 5's tests construct it with `replace_text` (a test may import the adapter), so the file behaviour it names (no newline, replace, folder made, an `OSError` of the write becoming `TokenError("cannot write <target>: <error>")`) is tested on the real writer.
10. factory: started tests as vm.
11. tester: I wrote the tests from the criteria, using the human's answers in entry 9: `main(argv, environ, *, source=<factory of url, client_id, secret, scope>, sleep=<seconds>)`, and `TokenRefresher(source, target, write)` built with `replace_text`. The loop tests raise the real signal from the fake `sleep`, and criterion 8 checks `os.environ`.

    - criterion 1: tests/domain/test_tokens.py::test_the_wait_is_the_interval_or_half_a_short_life_and_at_least_the_floor (six rows)
    - criterion 2: tests/domain/test_tokens.py::test_a_token_needs_a_value_without_whitespace_and_a_positive_life (blank, space, newline, 0, -1 refused; 1 accepted)
    - criterion 3: tests/adapters/test_oauth_token.py::test_a_fetch_posts_the_four_fields_form_encoded_and_returns_the_token (integer and string `expires_in`) and ::test_open_url_receives_the_timeout (default 30.0 and a given 5.0)
    - criterion 4: tests/adapters/test_oauth_token.py::test_a_failed_fetch_is_a_token_error_without_the_secret_or_the_token (12 rows)
    - criterion 5: tests/application/test_tokens.py::test_a_refresh_writes_the_token_alone_and_replaces_the_older_one (also creates the folder), ::test_a_failed_fetch_leaves_the_old_file_untouched, ::test_a_write_that_fails_is_a_token_error_naming_the_target
    - criterion 6: tests/entry/test_refresh_token.py::test_a_missing_or_blank_variable_exits_2_naming_it (5 variables × unset/blank), ::test_an_unreadable_or_blank_secret_file_exits_2, ::test_once_writes_the_token_and_names_its_life_and_the_wait, ::test_once_with_a_failing_source_keeps_the_file_and_exits_1
    - criterion 7: tests/entry/test_refresh_token.py::test_the_loop_refreshes_after_each_wait_until_a_signal and ::test_the_loop_keeps_the_file_after_a_failure_and_retries_after_a_minute (each with SIGTERM and SIGINT rows)
    - criterion 8: tests/entry/test_refresh_token.py::test_the_secret_and_the_token_appear_in_no_output_error_or_environment

    **How I read criterion 4's echoed-token row.** In a failure, the only token the source can know is one its body holds or one it handed out earlier. The test covers both: each fault row first fetches `tok-abc` successfully, and the echo row's error body also carries `"access_token": "tok-abc"`. An implementation that masks either one passes, so the test does not pick a reading.

    Files created:
    - tests/domain/test_tokens.py
    - tests/application/test_tokens.py
    - tests/adapters/test_oauth_token.py
    - tests/entry/test_refresh_token.py
    - tests/token_support.py: `ScriptedTokenSource(TokenSource)`, `RecordingOpener`, `answer`, `http_error`, `ENDPOINT`

    **Earlier test files I changed, under the standing leave to move a shared test helper:**
    - tests/entry/test_run.py: I moved its `restored_signals` fixture unchanged to tests/conftest.py and dropped the `Iterator` import it no longer needs. Every test keeps its name and checks the same thing.
    - tests/conftest.py: now holds that fixture.

    **`make test`, one run:** it fails with collection errors (ImportError) for the four new modules. The modules the test run could not import are `factory.domain.tokens`, `factory.application.tokens`, `factory.adapters.oauth_token` and `factory.entry.refresh_token`, plus `factory.domain.errors.TokenError`. That run started before the last renames below; they change no import, so I did not run it again. `make lint` is green. `make secrets` is green too, but it may not have scanned the new files, because they are not tracked yet.

    **Name choices:** I named the test constants `HIDDEN`, `ISSUED` and `ENDPOINT`, because ruff's S105 flags names like `SECRET` and `TOKEN`.

    **Open, for the coder and intake:**
    - The Interface still says `TokenRefresher(source, target)` with two arguments, but the human's answer in entry 9 adds `write` as a third, required argument.
    - The smoke test's Python snippet also constructs it with two arguments, so it will fail as written until the snippet passes `replace_text`.

    `lint`: lint: green (0.2 s)
    `test`: ERROR tests/entry/test_refresh_token.py - ImportError while importing test module '/work/checkout/tests/entry/test_refresh_token.py'.
12. factory: started doing as vm.
13. coder: I stopped with the code written. Every new test passes, along with `make types`, `make layers`, `make sast`, `make secrets` and `make licenses`. `make check` is still red for two reasons I may not fix myself.

    **Built (working tree):**
    - `src/factory/domain/tokens.py`: `Token`, the three intervals and `refresh_wait`.
    - `src/factory/domain/errors.py`: `TokenError`.
    - `src/factory/application/tokens.py`: `TokenSource` and `TokenRefresher(source, target, write)`, as entry 9 says.
    - `src/factory/adapters/oauth_token.py`: `ClientCredentialsTokenSource`. It calls `open_url(request, timeout=...)` by keyword, because `urlopen`'s second positional parameter is `data`. It masks the client secret, every token it has handed out, and an `access_token` that an error body echoes.
    - `src/factory/entry/refresh_token.py`: `main`. It reuses `install_stop_handlers` from `factory.entry.run` and restores the previous handlers when it returns.
    - `src/factory/entry/wiring.py`: `client_credentials_source` and `build_token_refresher`.

    **Main choice:** the adapter construction lives in `factory.entry.wiring`. The rejected alternative was importing the adapters directly in `refresh_token.py`, as the Interface reads; `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` forbids that. I also renamed one internal constant to `_CLIENT_CREDENTIAL_FILE`, because ruff S105 flags `SECRET` in a name; the variable's text is unchanged.

    **Questions:**

    1. **An existing test contradicts the Interface.** `tests/test_hosting_search.py::test_no_module_imports_another_route_to_the_hosting_service[urllib.request]` forbids any module from importing `urllib.request`. The Interface requires `oauth_token` to use it, for its `Request` and the default `open_url=urllib.request.urlopen`. That test fails now: `assert {'factory.ada....oauth_token'} == set()`. The options I see:
       - (a) The tester changes that test so `factory.adapters.oauth_token` may import `urllib.request` (and only it). This needs your leave, since another story wrote it.
       - (b) Another HTTP route. `httpx`, `requests`, `urllib3` and `http.client` are all forbidden too, and the first three would be new dependencies.
       - (c) `from urllib import request`. That only gets past the test without honouring it, so I rule it out.
       
       I would choose (a). With it I would end with `tests` and name exactly that change.

    2. **Two `make lint` findings on `oauth_token.py` that only a per-file ignore in `pyproject.toml` can settle.** Earlier ignores of this kind were your commits (b3022aba5), and the project wants no `noqa` in the source.
       - PLR0913: the six-argument constructor is pinned by the Interface and the tests.
       - S310: `urllib.request.Request` gets a URL that is not a literal; it comes from the operator's `FACTORY_TOKEN_URL`.
       
       The options I see:
       - (a) You add `"src/factory/adapters/oauth_token.py" = ["PLR0913", "S310"]` with a reason, or tell me I may.
       - (b) For S310, also refuse a non-https `url` in the constructor. That is beyond the Interface, and it would still need the PLR0913 ignore.
       
       I would choose (a) without the scheme check.

    **Noticed, not touched:**
    - `make duplicates` reports one new finding: vulture's "unused `__call__`" on the `OpenUrl` Protocol in `oauth_token.py`. That is a false positive, because the Protocol only types `open_url`.
    - The Interface's text and the first smoke-test snippet still build `TokenRefresher` with two arguments. Entry 9 made `write` a third, required argument, so the snippet fails as written until it passes `replace_text`. My write paths do not cover the smoke test, so I left it.
    - No refactor yet; I will do it once `make check` can go green.
14. 2026-10-31 human: Answers to question 13:

    1. (a). The tester may change `tests/test_hosting_search.py::test_no_module_imports_another_route_to_the_hosting_service` so that `factory.adapters.oauth_token`, and no other module, may import `urllib.request`: the feature names the standard library's `urllib` as the refresher's HTTP (*The human's changes*, decision 8), and the token endpoint is not the hosting service. Every other module stays refused, and a row shows that a second module importing it is still caught. End with `tests` and name that change.
    2. (a), without the scheme check. The per-file ignore is on `main` now (commit after this answer's time, `pyproject.toml`: `"src/factory/adapters/oauth_token.py" = ["PLR0913", "S310"]` with its reason); your stage merges `origin/main`, so `make lint` sees it.

    On your notes: the smoke test's first snippet and the Interface's sentence about `TokenRefresher` are the work item's text; the reviewer corrects both to pass `replace_text` as the third argument (entry 9). The vulture finding on the `OpenUrl` Protocol's `__call__` is a known false positive; leave it, it goes into the duplicates baseline at approval.
