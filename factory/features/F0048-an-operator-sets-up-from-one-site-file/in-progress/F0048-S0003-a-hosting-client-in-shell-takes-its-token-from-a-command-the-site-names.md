---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 500
comments_read: [6582972884]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-02T16:55:44.170118Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-02T16:52:50.742613Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-02T16:52:50.749217Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-02T16:53:21.312678Z'
  stage: intake
  run: 7f1bb66938064c6390c3fa0f615b66f5
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-02T16:54:38.671003Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-02T16:54:58.505369Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-02T16:55:23.148204Z'
  stage: intake
  run: 5bd3ebb98b154e40adc56c04a847b242
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-02T16:55:44.170118Z'
  stage: tests
---

# A hosting client in shell takes its token from a command the site names

## Description

The operator's scripts talk to the code host in three ways: the REST API (pull requests, comments, files), git over HTTPS (fetch, push) and, until now, the `gh` program, whose login is the person's own and, at one site, did not see the project's repository. This story adds one shell library, `operator/lib/hosting.sh`, that does the first two with a token from a source the site names: the command in `SITE_TOKEN_CMD` (a secret store, a keychain, any program that prints a token), or, when that is unset, `gh auth token`, so that a home setup works as it does today. The token never appears in an argument list, where `ps` would show it to every user of the machine: the API call gets its authorization through the configuration `curl` reads on standard input, and git gets it through `GIT_CONFIG_*` environment variables. A failing source stops with a message that never repeats its output. The story changes no existing script (S0004 does) and reads the site through S0001's loader.

## Interface

`operator/lib/hosting.sh` (POSIX `sh`, sourced after `site.sh`; it calls `site_load` itself when `SITE_` values are not loaded yet)

```sh
hosting_token                    # prints the token and a newline; exit 0 or 4
hosting_api METHOD PATH [BODY]   # the API call; prints the response body; exit 0, 4 or 22
hosting_repo_api METHOD PATH [BODY]  # hosting_api METHOD /repos/$SITE_REPOSITORY$PATH [BODY]
hosting_git ARG...               # git with the token for https remotes; the exit status of git
```

- `hosting_token` runs `sh -c "$SITE_TOKEN_CMD"` when `SITE_TOKEN_CMD` is set and not empty, else `gh auth token`; it takes the first line of the standard output, removes surrounding whitespace and a trailing carriage return, and prints it. The command's standard error is discarded.
- When the command exits non-zero, prints nothing, or no command is available (`SITE_TOKEN_CMD` unset and no `gh`), `hosting_token` prints `hosting: the token command failed; see SITE_TOKEN_CMD in the site file` to standard error, prints nothing to standard output and returns 4. Nothing the command printed is in that message.
- `hosting_api` calls `curl --silent --show-error --max-time 40 --config -` with the configuration on standard input: the URL `$SITE_API_URL$PATH` (`SITE_API_URL` defaults to `https://api.github.com`), `request = "METHOD"`, the headers `Authorization: Bearer <token>`, `Accept: application/vnd.github+json` and `X-GitHub-Api-Version: 2022-11-28`, and, when BODY is given, `data = ` BODY in the configuration's quoted form (backslash and double quote escaped, a newline written `\n`). The token is in no argument of `curl`.
- The response body goes to standard output; `curl` writes the HTTP status after it with `--write-out` to a temporary file that `hosting_api` removes. A status from 200 to 299 returns 0. Any other status returns 22 and prints `hosting: <METHOD> <PATH>: <status> <message>` to standard error, `<message>` being the body's JSON `message` when there is one (else the first 100 characters of the body, on one line). A `curl` failure (no status) returns 22 with `hosting: <METHOD> <PATH>: no answer`.
- When the token cannot be had, `hosting_api` and `hosting_repo_api` return 4 with the message of `hosting_token` and do not run `curl`.
- `hosting_repo_api` requires `SITE_REPOSITORY` (`site_require`); unset, it returns 2 with the message of `site_require`.
- `hosting_git` runs `git` with `GIT_CONFIG_COUNT=2`, `GIT_CONFIG_KEY_0=credential.helper`, `GIT_CONFIG_VALUE_0=` (empty, so no helper answers), `GIT_CONFIG_KEY_1=http.extraHeader` and `GIT_CONFIG_VALUE_1=Authorization: Basic <base64 of x-access-token:<token>>` in its environment, `GIT_TERMINAL_PROMPT=0`, and its arguments unchanged. The token is in no argument of `git`. When the token cannot be had it returns 4 without running `git`.
- The token is never written to a file and never printed except by `hosting_token`.

Tests: `tests/test_operator_hosting.py`, with stand-ins for `curl` and `gh` on the `PATH` (each records its arguments and its standard input to a file, and answers as the row says) and the real `git` (`CLAUDE.md` *Tests*: git is never faked) and the site file in `tmp_path`; the helper of S0001's `tests/operator_support.py` is extended, not copied.

## Acceptance criteria

1. `hosting_token` with `SITE_TOKEN_CMD='printf "  tok123  \r\nsecond\n"'` prints `tok123` and a newline and returns 0 (first line only, whitespace and the carriage return removed).
2. With `SITE_TOKEN_CMD` unset, and again with `SITE_TOKEN_CMD=` (set, empty), and a stand-in `gh` that prints `ghtok` for `auth token`, it prints `ghtok`; with `SITE_TOKEN_CMD` set and not empty, the `gh` stand-in is not called.
3. Failures, as rows of one parametrized test: a command that exits 1 after printing `LEAKMARK` on its standard output; the same on its standard error; a command that exits 0 and prints nothing; a command that prints only blank lines; `SITE_TOKEN_CMD` unset and no `gh` on the `PATH`. Each returns 4, prints nothing to standard output, and prints exactly the message of the Interface to standard error, which does not contain `LEAKMARK`.
4. `hosting_api GET /user` runs `curl` once with the arguments `--silent --show-error --max-time 40 --config -` (in that order), and the token appears in none of the stand-in's arguments; it appears in its standard input as the header line `header = "Authorization: Bearer <token>"`, with the URL `url = "https://api.github.com/user"`, `request = "GET"`, `header = "Accept: application/vnd.github+json"` and `header = "X-GitHub-Api-Version: 2022-11-28"` there as well.
5. `SITE_API_URL=https://api.example.invalid` changes the URL of criterion 4 to `https://api.example.invalid/user`; a trailing `/` of `SITE_API_URL` is removed before the path is added.
6. A body is passed in the configuration: `hosting_api POST /x '{"a":"b\"c"}'` gives the line `data = "{\"a\":\"b\\\"c\"}"` on the stand-in's standard input (the backslash and the quote escaped), and no `data` line when there is no body; a body holding a newline (`a<newline>b`) gives the single line `data = "a\nb"`.
7. Status handling, as rows of one parametrized test: 200, 201 and 204 return 0 and print the body; 301 with a body returns 22 with `hosting: GET /user: 301 <the first 100 characters of the body>`; 404 with the body `{"message":"Not Found"}` returns 22 with `hosting: GET /user: 404 Not Found`; 500 with a body that is not JSON, longer than 100 characters and holding a newline, returns 22 with its first 100 characters on one line; a `curl` that exits 7 returns 22 with `hosting: GET /user: no answer`.
8. `hosting_repo_api GET /pulls` with `SITE_REPOSITORY=owner/repo` calls the URL `.../repos/owner/repo/pulls`; with `SITE_REPOSITORY` unset it returns 2, prints the `site_require` message and does not call `curl`.
9. With the real `git`: `hosting_git config --get http.extraHeader` prints `Authorization: Basic ` followed by the base64 of `x-access-token:<token>`; `hosting_git config --get-all credential.helper` prints one empty line; `hosting_git -c 'alias.envdump=!env' envdump` shows `GIT_TERMINAL_PROMPT=0` and `GIT_CONFIG_COUNT=2` in git's environment; and `hosting_git` passes its arguments unchanged (`hosting_git -C <a real repository in tmp_path> log -1 --format=%s` prints that repository's subject). No argument git is given holds the token or its base64 (a test over the `trace: built-in: git ...` line that `GIT_TRACE=1` prints).
10. `hosting_git init <a folder in tmp_path>` with a failing token source returns 4 and the folder does not exist afterwards (git did not run).
11. The token and its base64 are in no file the functions leave in `tmp_path` and in none of the lines they print, except the one line of `hosting_token` (a search of the folder and of the captured output).
12. After `hosting_api` has run, for a success and for a failure alike, no file remains in the temporary folder that was not there before (the status file is removed).
13. With the token source failing, `hosting_api GET /user` and `hosting_repo_api GET /pulls` return 4, print the message of the Interface to standard error and nothing to standard output, and the `curl` stand-in is not called.
14. Sourced without a prior `site_load`, with `FACTORY_SITE` naming a site file that holds `SITE_TOKEN_CMD`, `hosting_token` prints that command's token.
15. `make check` stays green.
16. docs: `docs/operator-guide.md` gets a section *The token source* in the site file's part (the three ways to give a token, the command's rules, that the token is never in an argument list and why, `SITE_API_URL`); `README.md` and the other documents: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_TOKEN_CMD=printf "  abc  "\n' > "$d/site.env"
FACTORY_SITE="$d/site.env" sh -c '. operator/lib/site.sh; . operator/lib/hosting.sh; hosting_token'
```

Expect: one line, `abc`.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_TOKEN_CMD=echo SECRETWORD; exit 1\n' > "$d/site.env"
FACTORY_SITE="$d/site.env" sh -c '. operator/lib/site.sh; . operator/lib/hosting.sh; hosting_token' 2>"$d/err"; echo "exit $?"; cat "$d/err"
```

Expect: two lines, `exit 4` and `hosting: the token command failed; see SITE_TOKEN_CMD in the site file`; the word `SECRETWORD` is in neither.

## Journal

1. 2026-11-02 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed; no findings from it). The Interface states behaviour and rules that no criterion tests, and one case it leaves open:

   1. Headers: the Interface sends `Accept: application/vnd.github+json` and `X-GitHub-Api-Version: 2022-11-28`, but criterion 4 only checks the `Authorization` header line. Should criterion 4 (or a new one) require both header lines on the stand-in's standard input? I would choose yes.
   2. Body escaping: the Interface says a newline in BODY is written `\n`. Criterion 6 covers only the backslash and the double quote. Should a new criterion check a body that holds a newline (`data = "a\nb"` on one line)? I would choose yes.
   3. Temporary file: the Interface says the `--write-out` status file is removed by `hosting_api`. No criterion checks this. Should one require that no new file remains in the temporary folder after the call, for success and failure alike? I would choose yes.
   4. Token failure in `hosting_api`: the Interface gives `hosting_api` exit 0 or 22 only, and no criterion covers a failing token source. What should `hosting_api` and `hosting_repo_api` return then? I would choose 4 with the token message, `curl` not run, plus a criterion for it.
   5. Empty `SITE_TOKEN_CMD`: the Interface says the command runs when `SITE_TOKEN_CMD` is "set and not empty", else `gh`. Criterion 2 covers only the unset case. Should a row cover `SITE_TOKEN_CMD=` (set, empty) falling back to `gh`? I would choose yes, as a row of criterion 2.
   6. Loading: the Interface says `hosting.sh` calls `site_load` itself when `SITE_` values are not loaded. No criterion tests it. Should one require that, sourced without a prior `site_load` and with `FACTORY_SITE` naming a file holding `SITE_TOKEN_CMD`, `hosting_token` prints that command's token? I would choose yes.
   7. Criterion 3, row 1: it does not say whether `LEAKMARK` is printed on the command's standard output or its standard error. The Interface discards stderr, so the row should use both. I would choose one row for each stream.
   8. Criterion 7, status 301: it says "returns 22" but not the message. Should the row also require `hosting: GET /user: 301 <the body's first 100 characters>`? Also, should the 500 row use a body longer than 100 characters with a newline in it, so that both the cut and the one-line rule are tested? I would choose yes to both.

   Checked and fine: the architecture (shell library under `operator/lib/`, reading the site through S0001's loader, no change to existing scripts), the scope (inside F0048's "A hosting client in shell"; nothing in its Out of scope), and the smoke tests (runnable; both `Expect:` lines are checkable; the pytest `-q` rule does not apply).
4. 2026-11-02 human: Yes to all eight, as you propose: 1 both header lines in criterion 4; 2 a newline row in criterion 6; 3 no file left in the temporary folder, success and failure; 4 `hosting_api` and `hosting_repo_api` return 4 with the token message and do not run `curl` (add it to the Interface and a criterion); 5 `SITE_TOKEN_CMD=` falls back to `gh`, a row of criterion 2; 6 the self-load criterion; 7 one row per stream; 8 the 301 message and a 500 body over 100 characters with a newline.
5. factory: started intake as vm.
6. intake: accepted. The human's answer (journal entry 4) changed the story. I wrote exactly that into it and added nothing of my own.
   - Interface: `hosting.sh` names concrete functions with signatures and exit codes. From answer 4, `hosting_api` now exits 0, 4 or 22, and a new line says `hosting_api` and `hosting_repo_api` return 4 with the token message and do not run `curl`.
   - Criteria: each is testable by one test function, and every Interface behaviour has one. Edits from the answer:
     - Criterion 2 gets the `SITE_TOKEN_CMD=` (set, empty) row (answer 5).
     - Criterion 3 gets one `LEAKMARK` row per stream (answer 7).
     - Criterion 4 now requires the Accept and API-version header lines (answer 1).
     - Criterion 6 gets the newline row (answer 2).
     - Criterion 7 gets the 301 message and a 500 body over 100 characters that holds a newline (answer 8).
     - New criterion 12: no status file is left after `hosting_api`, on success or failure (answer 3).
     - New criterion 13: token failure in `hosting_api` and `hosting_repo_api` returns 4 and does not call `curl` (answer 4).
     - New criterion 14: self-load through `FACTORY_SITE` (answer 6).
     - The closing criteria `make check` and `docs:` are now 15 and 16 and stay last. The rules have passing and failing sides.
   - Smoke test: both blocks run as written and neither runs pytest. The `Expect:` lines (`abc`; `exit 4` plus the message, with no `SECRETWORD`) can be checked against the output.
   - Architecture: a shell library under `operator/lib/` that reads the site through S0001's loader. It changes no existing script and matches `feature.md` decisions 3, 4, 5 and 14.
   - Scope: inside F0048's "A hosting client in shell" and nothing in its Out of scope. No test of another story is changed. The `Description` is unchanged because the meaning of the task did not change.
7. factory: started tests as vm.
