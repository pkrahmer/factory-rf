---
stage: tests
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 500
comments_read: [6582972884]
handed_over: null
claim: null
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
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-02T17:00:59.958628Z'
  stage: tests
  run: f8a12314b51a47bface3831fba2ffe6f
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-02T17:01:21.079833Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-02T17:06:10.251061Z'
  stage: doing
  run: 6c31637749d84515a2d5cfea3597cb0d
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-02T17:06:31.267022Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-02T17:08:27.877400Z'
  stage: review
  run: aa3e06e57778413bab31fdb624ef56db
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-02T17:08:48.884344Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-02T17:09:07.084569Z'
  stage: doing
  run: 79b5816ba2354c5eb40d7097b9207d3e
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-02T17:09:28.049917Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-02T17:11:24.352529Z'
  stage: tests
  run: cac045a0793c4ffc8de63a2289dfb164
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-02T17:11:45.090252Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-02T17:15:10.361268Z'
  stage: doing
  run: d6776f4672194f449535b4466f7218f7
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-02T17:15:31.620526Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-11-02T17:17:25.782778Z'
  stage: review
  run: 581c62d6bf5545b7b6cea24ba831cdba
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-02T17:17:46.583436Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-11-02T17:20:17.757924Z'
  stage: doing
  run: 9d5b3076a3f1414aacafffaee45bbd5d
---

# A hosting client in shell takes its token from a command the site names

## Description

The operator's scripts talk to the code host in three ways: the REST API (pull requests, comments, files), git over HTTPS (fetch, push) and, until now, the `gh` program, whose login is the person's own and, at one site, did not see the project's repository. This story adds one shell library, `operator/lib/hosting.sh`, that does the first two with a token from a source the site names: the command in `SITE_TOKEN_CMD` (a secret store, a keychain, any program that prints a token), or, when that is unset or empty, `gh auth token`, so that a home setup works as it does today. The token never appears in an argument list, where `ps` would show it to every user of the machine: the API call gets its authorization through the configuration `curl` reads on standard input, and git gets it through `GIT_CONFIG_*` environment variables. A failing source stops with a message that never repeats its output. The story changes no existing script (S0004 does) and reads the site through S0001's loader.

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
15. The edges of the 200 to 299 range, as more rows of criterion 7's test: 299 returns 0 and prints the body; 199 and 300, each with the body `{"message":"Edge"}`, return 22 with `hosting: GET /user: 199 Edge` and `hosting: GET /user: 300 Edge`.
16. `hosting_git` returns git's exit status when git fails: `hosting_git config --get no.such.key` (a key no configuration holds) returns 1, as git does.
17. Sourced without a prior `site_load`, with a `SITE_` value already in the environment (`SITE_TOKEN_CMD` naming the token command) and `FACTORY_SITE` naming a file that does not exist, the library does not call `site_load`: `hosting_token` prints the token and standard error is empty (no `site: no site file` message). A row of criterion 14's test.
18. `hosting_repo_api POST /pulls '{"a":"b"}'` with `SITE_REPOSITORY=owner/repo` passes its BODY on to the API call: the `curl` stand-in's standard input holds the URL `url = "https://api.github.com/repos/owner/repo/pulls"`, `request = "POST"` and the line `data = "{\"a\":\"b\"}"`.
19. `make check` stays green.
20. docs: `docs/operator-guide.md` gets a section *The token source* in the site file's part (the three ways to give a token, the command's rules, that the token is never in an argument list and why, `SITE_API_URL`); `README.md` and the other documents: none.

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
8. tester: Tests written for criteria 1–14. They fail because `operator/lib/hosting.sh` does not exist yet.

   Criterion → test (all in tests/test_operator_hosting.py):
   - criterion 1: test_the_token_is_the_first_line_of_the_command_trimmed
   - criterion 2: test_without_a_token_command_the_token_comes_from_gh. Rows: unset, empty and set; the `set` row checks that `gh` is not called.
   - criterion 3: test_a_failing_token_source_stops_without_repeating_its_output. Rows: LEAKMARK on stdout, LEAKMARK on stderr, prints nothing, blank lines only, no command and no `gh`.
   - criterion 4: test_the_api_call_gives_curl_the_token_on_standard_input_only
   - criterion 5: test_the_site_api_url_replaces_the_default. Rows: without and with a trailing `/`.
   - criterion 6: test_a_body_is_passed_quoted_in_the_configuration. Rows: quote, no body, newline.
   - criterion 7: test_the_status_decides_the_result_of_the_api_call. Rows: 200, 201, 204, 301, 404, 500, curl exits 7.
   - criterion 8: test_the_repository_call_puts_the_site_repository_in_the_path. Rows: set and unset.
   - criterion 9: test_git_gets_the_token_through_its_environment. It uses the real git.
   - criterion 10: test_git_does_not_run_without_a_token
   - criterion 11: test_the_token_is_neither_left_in_a_file_nor_printed
   - criterion 12: test_the_api_call_leaves_no_temporary_file. Rows: 200 and 404; `TMPDIR` points to a folder in tmp_path.
   - criterion 13: test_the_api_call_does_not_run_curl_without_a_token. Rows: hosting_api and hosting_repo_api.
   - criterion 14: test_the_library_loads_the_site_itself

   Files:
   - Created: tests/test_operator_hosting.py.
   - Extended: tests/operator_support.py, the helper the Interface says to extend. It gets `HOSTING_LIBRARY` and `run_hosting(code, cwd, env, *, load=True)`. That function sources site.sh, runs `site_load` unless `load=False`, sources hosting.sh, then runs `code`. No earlier test changed.

   Stand-ins:
   - `curl` (Python, through git_support.write_executable) records its argv and stdin as JSON lines.
   - It reads its configuration the way curl does: url, request, header, data, output, and write-out with `%{http_code}`, `%output{file}`, `%{stdout}` and `%{stderr}`.
   - It answers with the status, body and exit set in its environment. When it exits non-zero it writes `000` as the status, as real curl does, and prints nothing on stderr.
   - `gh` records its calls and prints `ghtok` for `auth token`.
   - Each test's `PATH` leaves out every system folder that holds a `gh`.

   Choices that do not decide anything the criteria leave open:
   - The tests never type the token. The command `printf 'tok%s\n' 123` prints `tok123`, so the token's text is in no file the test writes. The search in criterion 11 skips only the stand-ins' record folder, which holds curl's stdin.
   - The 500 body is `x`*60, a newline, `y`*39, then `Z`*20. The test checks four things: the message is one line, it starts with the 60 `x`, it holds the 39 `y`, and it has no `Z`. It does not decide what replaces the newline.

   Test run: one run of `uv run pytest -q` on the new file and tests/test_operator_site.py. The hosting tests failed because hosting.sh is missing; sourcing it fails in `sh`. Afterwards I only renamed constants and made parameters keyword-only, to satisfy ruff's S105/S106 and PLR0917, so the tests check the same things.

   Could not import: no Python module is missing. The missing module under test is the shell library operator/lib/hosting.sh.

   `make lint` is green.

   `lint`: lint: green (0.1 s)
   `test`: FAILED tests/test_operator_hosting.py::test_the_library_loads_the_site_itself - AssertionError: assert (2, '') == (0, 'tok123\n')
9. factory: started doing as vm.
10. coder: Built `operator/lib/hosting.sh`, a new POSIX `sh` library. No other file changed. It has four public functions: `hosting_token`, `hosting_api`, `hosting_repo_api` and `hosting_git`. Its private helpers are:
    - `_hosting_token_source` runs `sh -c "$SITE_TOKEN_CMD"`, else `gh auth token`, else fails.
    - `_hosting_no_token` prints the one failure message.
    - `_hosting_curl_config` builds curl's configuration on standard input.
    - `_hosting_quote` writes curl's quoted form: sed escapes the backslash and the quote, awk joins lines with a literal `\n`.
    - `_hosting_error_message` takes the JSON `message`, else the first 100 characters on one line.

    Trimming reuses `_site_trim_leading` and `_site_trim_trailing` from `site.sh` rather than adding a second copy. At sourcing time, if the environment holds no `SITE_` variable, the library calls `site_load || :`. A failed load has already printed its reason, and `gh` can still be the token source, so a missing site file does not stop a `set -e` script.

    Main choice: `hosting_api` captures the body with a sentinel (`$(... | curl ...; echo .)`, then strips the `.`). This keeps the body's trailing newlines exactly and holds back the body on a failing status. The status goes to the `mktemp` file through `write-out = "%output{file}%{http_code}"` and is read back, and the file is removed right after. An empty status or `000` means "no answer". I rejected writing the body to a second temporary file with `output =`: it would add a file to clean up, and the Interface says the body goes to standard output.

    Other choices:
    - The token reaches curl only through `printf`, which is a shell builtin, so it appears in no process's arguments.
    - git gets it through `GIT_CONFIG_*` assignments placed before the `git` command.
    - When `hosting_repo_api` lacks `SITE_REPOSITORY` and the token also fails, it checks the repository first and returns 2. The Interface leaves this order open.
    - With an empty body, the error message has no trailing space after the status.

    Refactor pass: I read the new file as a reviewer would, and nothing needed changing.

    Checks: `make check` is green. The new test file and `tests/test_operator_site.py` pass. My one run of both smoke-test blocks together with `make check` was denied permission, and I did not retry them. Tests cover the same behaviour: criteria 14 and 3.

    Noticed, not touched:
    - `%output{}` in `--write-out` needs curl 8.3 or later. An older curl on an operator's machine would not write the status file, and every call would come back as "no answer". The operator guide's token section (the docs criterion) may want to say this.
    - The JSON message is found with a sed pattern, not a JSON parser. A body holding several `"message"` keys gives the last one.
    - The journal changed nothing in the Description; the human's answers went into the Interface and the criteria at intake.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
11. factory: started review as vm.
12. reviewer: Review, round 0. Group 1 (acceptance criteria) fails. I read every criterion and every Interface rule against `tests/test_operator_hosting.py` and `operator/lib/hosting.sh`. Criteria 1–14 each have a test that checks what the criterion says, and the coder's `make check` was green (entry 10). The gaps are untested sides of rules the Interface states. The code under `operator/` already handles all three, so I added the criteria rather than asking.

    1. criterion 15 added, and it needs its test: Interface "A status from 200 to 299 returns 0". Criterion 7 tests 200, 201, 204 and 301, so 299 inside the range and 199 and 300 outside it are untested. Fix: add rows 299 → 0, and 199 and 300 → 22 with `hosting: GET /user: <status> Edge`, to the parametrized test `test_the_status_decides_the_result_of_the_api_call`.
    2. criterion 16 added, and it needs its test: Interface "`hosting_git` ... the exit status of git". `test_git_gets_the_token_through_its_environment` only checks git succeeding (exit 0). Fix: a test where `hosting_git config --get no.such.key` returns 1.
    3. criterion 17 added, and it needs its test: Interface "it calls `site_load` itself when `SITE_` values are not loaded yet". Only the not-loaded side is tested (`test_the_library_loads_the_site_itself`). Fix: make that test parametrized and add a row with `SITE_TOKEN_CMD` in the environment and `FACTORY_SITE` naming a missing file. That row expects the token on stdout and an empty stderr.
    4. tests/test_operator_hosting.py `test_the_api_call_leaves_no_temporary_file`: the test never checks that the call ran (no exit status, no curl call recorded). A `hosting_api` that failed before `mktemp` would still pass, so it does not show criterion 12. Fix: assert the exit status (0 for 200, 22 for 404) and one recorded `curl` call.

    Closing criteria renumbered: `make check` is now 18 and `docs:` is 19.

    description corrected: "or, when that is unset, `gh auth token`" -> "or, when that is unset or empty, `gh auth token`". This follows human answer 5 (entry 4) and the Interface's "set and not empty".

    Groups 2–5 were not reviewed because group 1 failed.

    Earlier tests:
    - tests/operator_support.py: no leave needed. The change only adds `HOSTING_LIBRARY` and `run_hosting` and leaves every existing helper as it was. The story's Interface also asks for this helper to be extended.
13. factory: started doing as vm.
14. coder: Round 1: every finding in the reviewer's entry 12 is a test change, so I changed no code. The reviewer reports that `operator/lib/hosting.sh` already handles the three new criteria; I did not run them myself, since their tests do not exist yet. For the tester:

    - criterion 15: add rows to `test_the_status_decides_the_result_of_the_api_call` in tests/test_operator_hosting.py:
      - 299 returns 0 and prints the body.
      - 199 and 300, each with the body `{"message":"Edge"}`, return 22 with `hosting: GET /user: 199 Edge` and `hosting: GET /user: 300 Edge`.
    - criterion 16: a test that `hosting_git config --get no.such.key` returns 1, as git does.
    - criterion 17: make `test_the_library_loads_the_site_itself` parametrized. Add a row with `SITE_TOKEN_CMD` already in the environment and `FACTORY_SITE` naming a file that does not exist; it expects the token on standard output and an empty standard error.
    - Finding 4, criterion 12: `test_the_api_call_leaves_no_temporary_file` should also check that the call ran. It should assert the exit status (0 for the 200 row, 22 for the 404 row) and exactly one recorded `curl` call.

    What I built: nothing this round. The library from round 0 is unchanged.
    Main choice: no code change, because the findings only need tests. Rejected: changing the code ahead of the tests, since nothing in it has to change.
    The journal changed nothing in the Description this round: the reviewer already corrected "unset" to "unset or empty".
    Noticed, not touched: the round-0 notes still stand. `%output{}` in `--write-out` needs curl 8.3 or later; the docs criterion may want to say so. And the JSON `message` is found with sed, not a JSON parser.
15. factory: started tests as vm.
16. tester: I made the test changes that coder entry 14 lists, which carry out reviewer entry 12. All of them are in tests/test_operator_hosting.py. No code was changed and no other test file was touched.

    Criterion → test (all in tests/test_operator_hosting.py):
    - criterion 12: `test_the_api_call_leaves_no_temporary_file`. This fixes finding 4. The rows are now `(status, exit_status)`: 200 → 0 and 404 → 22. Each row also checks the exit status and that exactly one `curl` call was recorded (it now uses the `records` fixture).
    - criterion 15: `test_the_status_decides_the_result_of_the_api_call`, three new rows:
      - 299 returns 0 and prints the body `{"id":2}`.
      - 199 with the body `{"message":"Edge"}` returns 22 and prints `hosting: GET /user: 199 Edge`.
      - 300 with the same body returns 22 and prints `hosting: GET /user: 300 Edge`.
    - criterion 16: `test_git_returns_the_exit_status_of_git` (new). `hosting_git config --get no.such.key` returns 1.
    - criterion 17: `test_the_library_loads_the_site_itself`, now parametrized over `loaded`.
      - The `from-the-site-file` row is the original case and checks what it checked before.
      - The new `already-in-the-environment` row sets `SITE_TOKEN_CMD` in the environment and points `FACTORY_SITE` at a missing `tmp_path/absent.env`. It expects the token on standard output and an empty standard error.

    Criteria 1–11, 13 and 14 keep the tests that the tester's entry 8 lists.

    Files:
    - Changed: tests/test_operator_hosting.py.
    - Created: none.

    Test run: `uv run pytest -q tests/test_operator_hosting.py`, once: 37 passed. The new tests pass because `operator/lib/hosting.sh` already does what the three new criteria ask, as the reviewer said.

    `make lint` is green. Every module imported; nothing was missing.

    `lint`: lint: green (0.1 s)
    `test`: test: green (78.4 s)
17. factory: started doing as vm.
18. coder: Round 1, after the tester's entry 16. I ran `make check` against the tests that tester entry 16 added or changed in tests/test_operator_hosting.py (criteria 12, 15, 16 and 17), and it is green. The library from round 0 already passes all of them, so I changed no code this round.

    What I built: nothing new. `operator/lib/hosting.sh` (round 0) is the whole change outside `factory/` and `tests/`.

    Main choice: leave the library as it is. The new criteria (the edges of the 200–299 range, git's exit status, and no `site_load` when a `SITE_` value is already in the environment) are already handled by the `2[0-9][0-9]` case, by `git "$@"` as the last command of `hosting_git`, and by the guard at sourcing time. The alternative I rejected was tightening the code ahead of any finding, for example making the status check a numeric range. Nothing calls for it, and a change would go beyond the findings of this round.

    Refactor pass: I read the diff against main again, as a reviewer would. Nothing needed changing.

    The journal changed nothing in the Description this round. The reviewer had already corrected "unset" to "unset or empty" (entry 12).

    Noticed, not touched:
    - `%output{}` in `--write-out` needs curl 8.3 or later. With an older curl, the status file stays empty and every call reports "no answer". The docs criterion's section *The token source* may want to say this.
    - The JSON `message` is found with sed, not a JSON parser. A body with several `"message"` keys gives the last one.
    - The guard at sourcing time looks for `SITE_` in `env`, which lists exported variables only. A script that sets `SITE_` values without exporting them would still trigger `site_load`. The criteria only cover the environment case, so I left it.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
19. factory: started review as vm.
20. reviewer: Review, round 1. Group 1 (acceptance criteria and the Interface) fails. I read every criterion (1–17) and every Interface rule against `operator/lib/hosting.sh` and `tests/test_operator_hosting.py`.

    Each of criteria 1–17 has a test that checks what the criterion says. The round-0 findings are fixed:
    - the 299, 199 and 300 rows exist;
    - `test_git_returns_the_exit_status_of_git` exists;
    - `test_the_library_loads_the_site_itself` has both sides;
    - `test_the_api_call_leaves_no_temporary_file` now checks the exit status and the one `curl` call.

    The coder's `make check` was green (entry 18). The tests pass, but two Interface rules do not hold for real input, and one Interface behaviour had no criterion.

    1. operator/lib/hosting.sh:92 (`write-out = "%output{...}%{http_code}"` in `_hosting_curl_config`): the status file only works with curl 8.3 or later, because `%output{}` was added in 8.3.0.
       - Debian 12 ships curl 7.88.1. That is the curl on this VM (`curl --version`) and the one the operator guide installs from Debian (docs/operator-guide.md:1020). With it the status file stays empty, so every `hosting_api` call returns 22 with "no answer", even on a 200.
       - The stand-in `CURL_STAND_IN` supports `%output{}`, so criteria 7, 12 and 15 pass only against the stand-in.
       - Fix: write the status with a write-out form that curl 7.x knows, and keep the Interface's temporary status file. For example, use `write-out = "%{stderr}%{http_code}"` (curl 7.63 and later), send curl's standard error to the status file, and read its last three characters. An empty result, or `000`, stays "no answer".
    2. operator/lib/hosting.sh:111 (the `sed` in `_hosting_error_message`): the greedy `.*"message"` takes the last `"message"` key in the body, not the body's own `message` that the Interface names. GitHub's 422 answers (`{"message":"Validation Failed","errors":[{...,"message":"A pull request already exists ..."}]}`) report the nested message. Fix: take the first `"message"` key. One way is to cut the text up to the first `"message"` with a parameter expansion before matching the value.
    3. criterion 18 added, and it needs its test. The Interface's `hosting_repo_api METHOD PATH [BODY]` passes BODY on to `hosting_api`, but no test calls `hosting_repo_api` with a body. Criterion 8 and its test only use `GET /pulls`. Fix: add a test (or a row of `test_the_repository_call_puts_the_site_repository_in_the_path`) where `hosting_repo_api POST /pulls '{"a":"b"}'` gives the repository URL, `request = "POST"` and `data = "{\"a\":\"b\"}"` on the stand-in's standard input.

    Closing criteria renumbered: `make check` is now 19, and `docs:` is 20.

    Not findings, for the documenter: the docs criterion's section *The token source* should state the lowest curl version that the fix for finding 1 needs.

    Groups 2–5 were not reviewed because group 1 failed.

    Earlier tests:
    - tests/operator_support.py: none needed. The change only adds `HOSTING_LIBRARY` and `run_hosting`, and every helper the file held stays as it was.

    Notes:
    - tests/test_operator_hosting.py `test_the_api_call_gives_curl_the_token_on_standard_input_only`: `CURL_ARGUMENTS + [str(arguments)]` also searches the test's own constant, which can never hold the token. Searching `arguments` alone says the same thing.
21. factory: started doing as vm.
22. coder: Round 2. I fixed reviewer entry 20's two code findings in `operator/lib/hosting.sh`. Finding 3 needs only a test, so I'm handing that to the tester.

    - Finding 1 (curl 7.x). curl's configuration now asks for `write-out = "%{stderr}%{http_code}"`, which curl 7.63 and later understand. Before, it used `%output{}`, which needs curl 8.3. `hosting_api` sends curl's standard error to the same `mktemp` status file as before, which it still removes afterwards. A new helper, `_hosting_last_three`, reads the last three characters of that file as the status. Anything `--show-error` wrote ahead of the status is ignored, and a text shorter than three characters counts as "no answer", the same as `000`.
    - Finding 2 (first `message`). `_hosting_error_message` now cuts the flattened body up to its first `"message"` key with a parameter expansion, and only then matches the value. So GitHub's 422 answers give the top-level `Validation Failed`, not a nested error's message.
    - Finding 3 (criterion 18), for the tester: add a test, or a row of `test_the_repository_call_puts_the_site_repository_in_the_path` in tests/test_operator_hosting.py. With `SITE_REPOSITORY=owner/repo`, `hosting_repo_api POST /pulls '{"a":"b"}'` must put `url = "https://api.github.com/repos/owner/repo/pulls"`, `request = "POST"` and `data = "{\"a\":\"b\"}"` on the curl stand-in's standard input. The code already passes BODY on (`hosting_api "$_hosting_method" "$_hosting_path" "$@"`), so it needs no change.

    Main choice: send curl's stderr to the status file and take the last three characters. I rejected writing the status to stdout after the body and cutting it off there, because the Interface keeps the body alone on standard output and the status in a temporary file.

    Checks:
    - `make check` is green, and the existing tests pass with the new write-out. The curl stand-in already handles `%{stderr}`.
    - I have not checked the fix against the real curl. My one run with curl 7.88.1 on this VM (against an unreachable local port, plus a nested-`message` body) was refused permission, and I did not retry. The smoke tests would show it.

    Refactor pass: I read the diff again, as a reviewer would. Nothing needed changing.

    The journal changed nothing in the Description this round. Entry 20 added criterion 18, and the reviewer had already written it into the work item.

    Noticed, not touched:
    - On a failed transfer, curl's own error text goes into the status file and is thrown away with it. The Interface's message is just `no answer`, so the cause is not shown.
    - A non-JSON body with no `"message"` key that starts with `:"...` would be read as a message. This is not realistic, so I left it.
    - The reviewer's note on `CURL_ARGUMENTS + [str(arguments)]` in `test_the_api_call_gives_curl_the_token_on_standard_input_only` is about the tests, so it is the tester's to change.
    - For the documenter: the lowest curl version is now 7.63.

    `check`: check: green
