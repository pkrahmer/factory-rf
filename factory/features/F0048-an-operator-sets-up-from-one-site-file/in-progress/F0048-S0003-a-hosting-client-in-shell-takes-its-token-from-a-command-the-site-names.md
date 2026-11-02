# A hosting client in shell takes its token from a command the site names

## Description

The operator's scripts talk to the code host in three ways: the REST API (pull requests, comments, files), git over HTTPS (fetch, push) and, until now, the `gh` program, whose login is the person's own and, at one site, did not see the project's repository. This story adds one shell library, `operator/lib/hosting.sh`, that does the first two with a token from a source the site names: the command in `SITE_TOKEN_CMD` (a secret store, a keychain, any program that prints a token), or, when that is unset, `gh auth token`, so that a home setup works as it does today. The token never appears in an argument list, where `ps` would show it to every user of the machine: the API call gets its authorization through the configuration `curl` reads on standard input, and git gets it through `GIT_CONFIG_*` environment variables. A failing source stops with a message that never repeats its output. The story changes no existing script (S0004 does) and reads the site through S0001's loader.

## Interface

`operator/lib/hosting.sh` (POSIX `sh`, sourced after `site.sh`; it calls `site_load` itself when `SITE_` values are not loaded yet)

```sh
hosting_token                    # prints the token and a newline; exit 0 or 4
hosting_api METHOD PATH [BODY]   # the API call; prints the response body; exit 0 or 22
hosting_repo_api METHOD PATH [BODY]  # hosting_api METHOD /repos/$SITE_REPOSITORY$PATH [BODY]
hosting_git ARG...               # git with the token for https remotes; the exit status of git
```

- `hosting_token` runs `sh -c "$SITE_TOKEN_CMD"` when `SITE_TOKEN_CMD` is set and not empty, else `gh auth token`; it takes the first line of the standard output, removes surrounding whitespace and a trailing carriage return, and prints it. The command's standard error is discarded.
- When the command exits non-zero, prints nothing, or no command is available (`SITE_TOKEN_CMD` unset and no `gh`), `hosting_token` prints `hosting: the token command failed; see SITE_TOKEN_CMD in the site file` to standard error, prints nothing to standard output and returns 4. Nothing the command printed is in that message.
- `hosting_api` calls `curl --silent --show-error --max-time 40 --config -` with the configuration on standard input: the URL `$SITE_API_URL$PATH` (`SITE_API_URL` defaults to `https://api.github.com`), `request = "METHOD"`, the headers `Authorization: Bearer <token>`, `Accept: application/vnd.github+json` and `X-GitHub-Api-Version: 2022-11-28`, and, when BODY is given, `data = ` BODY in the configuration's quoted form (backslash and double quote escaped, a newline written `\n`). The token is in no argument of `curl`.
- The response body goes to standard output; `curl` writes the HTTP status after it with `--write-out` to a temporary file that `hosting_api` removes. A status from 200 to 299 returns 0. Any other status returns 22 and prints `hosting: <METHOD> <PATH>: <status> <message>` to standard error, `<message>` being the body's JSON `message` when there is one (else the first 100 characters of the body, on one line). A `curl` failure (no status) returns 22 with `hosting: <METHOD> <PATH>: no answer`.
- `hosting_repo_api` requires `SITE_REPOSITORY` (`site_require`); unset, it returns 2 with the message of `site_require`.
- `hosting_git` runs `git` with `GIT_CONFIG_COUNT=2`, `GIT_CONFIG_KEY_0=credential.helper`, `GIT_CONFIG_VALUE_0=` (empty, so no helper answers), `GIT_CONFIG_KEY_1=http.extraHeader` and `GIT_CONFIG_VALUE_1=Authorization: Basic <base64 of x-access-token:<token>>` in its environment, `GIT_TERMINAL_PROMPT=0`, and its arguments unchanged. The token is in no argument of `git`. When the token cannot be had it returns 4 without running `git`.
- The token is never written to a file and never printed except by `hosting_token`.

Tests: `tests/test_operator_hosting.py`, with stand-ins for `curl` and `gh` on the `PATH` (each records its arguments and its standard input to a file, and answers as the row says) and the real `git` (`CLAUDE.md` *Tests*: git is never faked) and the site file in `tmp_path`; the helper of S0001's `tests/operator_support.py` is extended, not copied.

## Acceptance criteria

1. `hosting_token` with `SITE_TOKEN_CMD='printf "  tok123  \r\nsecond\n"'` prints `tok123` and a newline and returns 0 (first line only, whitespace and the carriage return removed).
2. With `SITE_TOKEN_CMD` unset and a stand-in `gh` that prints `ghtok` for `auth token`, it prints `ghtok`; with `SITE_TOKEN_CMD` set, the `gh` stand-in is not called.
3. Failures, as rows of one parametrized test: a command that exits 1 after printing `LEAKMARK`; a command that exits 0 and prints nothing; a command that prints only blank lines; `SITE_TOKEN_CMD` unset and no `gh` on the `PATH`. Each returns 4, prints nothing to standard output, and prints exactly the message of the Interface to standard error, which does not contain `LEAKMARK`.
4. `hosting_api GET /user` runs `curl` once with the arguments `--silent --show-error --max-time 40 --config -` (in that order), and the token appears in none of the stand-in's arguments; it appears in its standard input as the header line `header = "Authorization: Bearer <token>"`, with the URL `url = "https://api.github.com/user"` and `request = "GET"` there as well.
5. `SITE_API_URL=https://api.example.invalid` changes the URL of criterion 4 to `https://api.example.invalid/user`; a trailing `/` of `SITE_API_URL` is removed before the path is added.
6. A body is passed in the configuration: `hosting_api POST /x '{"a":"b\"c"}'` gives the line `data = "{\"a\":\"b\\\"c\"}"` on the stand-in's standard input (the backslash and the quote escaped), and no `data` line when there is no body.
7. Status handling, as rows of one parametrized test: 200, 201 and 204 return 0 and print the body; 301 returns 22; 404 with the body `{"message":"Not Found"}` returns 22 with `hosting: GET /user: 404 Not Found`; 500 with a body that is not JSON returns 22 with the first 100 characters of the body on one line; a `curl` that exits 7 returns 22 with `hosting: GET /user: no answer`.
8. `hosting_repo_api GET /pulls` with `SITE_REPOSITORY=owner/repo` calls the URL `.../repos/owner/repo/pulls`; with `SITE_REPOSITORY` unset it returns 2, prints the `site_require` message and does not call `curl`.
9. With the real `git`: `hosting_git config --get http.extraHeader` prints `Authorization: Basic ` followed by the base64 of `x-access-token:<token>`; `hosting_git config --get-all credential.helper` prints one empty line; `hosting_git -c 'alias.envdump=!env' envdump` shows `GIT_TERMINAL_PROMPT=0` and `GIT_CONFIG_COUNT=2` in git's environment; and `hosting_git` passes its arguments unchanged (`hosting_git -C <a real repository in tmp_path> log -1 --format=%s` prints that repository's subject). No argument git is given holds the token or its base64 (a test over the `trace: built-in: git ...` line that `GIT_TRACE=1` prints).
10. `hosting_git init <a folder in tmp_path>` with a failing token source returns 4 and the folder does not exist afterwards (git did not run).
11. The token and its base64 are in no file the functions leave in `tmp_path` and in none of the lines they print, except the one line of `hosting_token` (a search of the folder and of the captured output).
12. `make check` stays green.
13. docs: `docs/operator-guide.md` gets a section *The token source* in the site file's part (the three ways to give a token, the command's rules, that the token is never in an argument list and why, `SITE_API_URL`); `README.md` and the other documents: none.

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
