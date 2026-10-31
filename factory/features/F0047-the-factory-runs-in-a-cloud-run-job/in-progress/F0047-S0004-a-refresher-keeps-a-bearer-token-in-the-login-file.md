---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 485
comments_read: [6547461929]
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
3. `ClientCredentialsTokenSource.fetch` with an `open_url` that records its request and answers `{"access_token": "t", "expires_in": 3599}`: the request is a POST to the given URL with the content type above and a body that holds the four fields, URL-encoded (a secret with `&`, `=`, `+` and a space round-trips through `parse_qs`), and the token is `Token(value="t", expires_in=3599)`; `"expires_in": "3599"` gives the same.
4. Faults, rows of one test: an `HTTPError` 400 with the body `{"error": "invalid_client", "error_description": "AADSTS7000215: bad secret\r\nTrace ID: x"}` gives `HTTP 400: invalid_client: AADSTS7000215: bad secret`; an error description of 300 characters is cut at 200; a `URLError("no route")` gives `no route`; a `TimeoutError` gives its message; the body `[]`, a body without `access_token` and a body with `expires_in` 0 give the sentences of the Interface; none of these details contains the client secret even when the server's body echoes it (the echo is replaced by `***`).
5. `TokenRefresher.refresh` writes the token into the target with no other text and no newline, replaces an older value, creates the folder, leaves the old file untouched when the source raises, and turns an `OSError` of the write (a target that is a folder) into `TokenError("cannot write <target>: <error>")`.
6. The command: a missing variable exits 2 and names it (one row per variable); a blank secret file exits 2; `--once` with a source that answers 3599 s writes the file, prints `token refreshed: valid 3599 s, next in 600 s` (the wait's whole seconds) and exits 0; `--once` with a source that fails prints `refresh_token: token request failed: <detail>` to standard error, leaves the file as it was and exits 1.
7. The loop (injected wait): two successes then `SIGTERM` gives two writes, waits of the refresh interval, exit 0; a failure between two successes keeps the file of the first, prints the error, waits `RETRY_INTERVAL` once and goes on.
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
