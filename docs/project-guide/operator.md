# The operator's scripts

The shell and Python scripts under `operator/`, which let an operator set up one machine from one site file, and the tests that run them. This file describes what they do today; the operator's side (install, the values, the stops) is `docs/operator-guide/site.md`, *Setting up an operator's machine*.

## The layout

- `operator/site.env.example`: every key of the site file, each with a comment and a made-up value. `site init` copies it.
- `operator/lib/site.sh`: the loader every script sources (`site_path`, `site_load`, `site_require`, `site_value`, `site_refuse_repository`, `site_gcloud_with`, and `site_job_keys`, the keys `job.sh` requires).
- `operator/lib/hosting.sh`: the hosting client (`hosting_token`, `hosting_api`, `hosting_repo_api`, `hosting_git`, `hosting_api_url`).
- `operator/bin/site`: the command for the site file (`path`, `init`, `show`, `get`, `check`).
- `operator/bin/sanitise`: the sanitiser.
- `operator/job/job.sh`: the factory's Cloud Run job.
- `operator/skill/kumpel/`: the skill. `SKILL.md`, `references/` (the standing orders and how to answer, approve and shape) and `scripts/` (`settings.sh`, `status.sh`, `wait.sh`, `approval.sh`, `next-story.sh`, `start-story.sh`, `comment.sh`, `merge.sh`, `reset-to-tag.sh`).
- `operator/opencode/command/kumpel.md` and `operator/claude/commands/kumpel.md`: the `/kumpel` command for each tool.
- `operator/README.md` is the documenter's (decision 22 of F0048): its table maps each file to the story that made it. Keep it current from the docs criterion; do not copy the table here.

## The site file and its loader

The site file holds a site's own values (`SITE_*` keys) in `KEY=value` lines. Its path is `$FACTORY_SITE`, else `$XDG_CONFIG_HOME/kumpel/site.env`, else `~/.config/kumpel/site.env` (`site_path`). Its sister folder for state is `~/.local/state/kumpel/` (`$XDG_STATE_HOME/kumpel`), where `job.sh` keeps `last-execution`.

- **Data, never code.** `site_load` reads each line and stores the value literally; it never sources the file and never runs a value. A value reaches `eval` only as the right-hand side of an assignment to a name that `_site_is_name` has accepted. One pair of matching quotes around a whole value is removed; a blank after `=` is a fault.
- **Only `SITE_` keys.** Any other key, a line without `=` and a name that is not upper case, digits and `_` is a fault, reported as `site: <file>:<line>: <what>`.
- **The environment wins.** A variable that is already set (even empty) is not overwritten, so a test or an operator overrides one value for one run.
- **All or nothing.** The whole file is checked before any value is exported, so a faulty file leaves the environment as it was.
- **Never in a repository.** `site_refuse_repository` refuses a path inside a git work tree. It asks git from the nearest existing ancestor, because `site init` runs before the folder exists.
- **Status.** `site_load` returns 0, 1 (no file), 2 (a fault) or 3 (the file lies in a repository). `site_require` returns 2 and names every missing key. `bin/site` ends with the same codes; `site check` ends 0 (`site: ready`) or 1 (`site: N failed`), and a wrong command line is 2.
- **Gcloud.** `site_gcloud_with RUNNER ARG...` adds `--project` to every call, `--region` to every `gcloud run` call and `--impersonate-service-account` when `SITE_IMPERSONATE` is set. Nothing leaves gcloud's own defaults to choose.

`site check` is read-only: one `ok NAME` or `FAIL NAME: DETAIL` line per check (`check_keys`, `check_tools`, `check_token`, `check_repository`, `check_checkout`, `check_identity`, `check_secrets`, `check_code`, `check_no_proxy`, `check_job`), where a check whose keys are missing fails on its keys and does not run.

## The hosting client

`hosting.sh` is sourced after `site.sh`, and loads the site itself when no `SITE_` variable is set.

- `hosting_token` runs `SITE_TOKEN_CMD` with `sh -c`; without it, `gh auth token` when `gh` is installed. It prints the first line, trimmed, and returns 4 when the source fails or prints nothing. The source's output is never repeated, because an error text can hold a secret.
- `hosting_api METHOD PATH [BODY]` prints the body of a 2xx answer. It returns 22 for another status (`hosting: <method> <path>: <status> <message>` on standard error) and 4 without a token. `hosting_repo_api` prefixes `/repos/$SITE_REPOSITORY` (2 when the key is missing). The base is `SITE_API_URL`, else `https://api.github.com`.
- `hosting_git ARG...` runs git with a Basic header for https remotes.
- **The token is in no argument list.** `hosting_api` writes curl's configuration (url, headers, body) to curl's standard input with `printf`, a builtin; `hosting_git` passes the header through `GIT_CONFIG_COUNT` and `GIT_CONFIG_KEY_n`/`GIT_CONFIG_VALUE_n`, with an empty `credential.helper` so a stored credential does not answer. `ps` shows neither.

## `job.sh`

`operator/job/job.sh` works from the site's values alone: `create` and `update` (both take `--dry-run`, which prints the gcloud call one argument per line and runs nothing), `execute`, `delete [--yes]`, `log [N] [--execution NAME] [--quiet]` and `status`.

- **No guessed values.** `require_settings` needs every key of `site_job_keys` and stops naming the missing ones. Only `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT` and `SITE_IDLE_MINUTES` have defaults. `check_instance`, `check_env_values` and `check_costs` refuse values that would break the env list (`@` is its delimiter) or the shell text.
- **The start script comes from `SITE_CODE_REF`.** `write_wrapper` takes `vm/job-start.sh` with `git show "$SITE_CODE_REF:vm/job-start.sh"`, never from the working tree, so the wrapper and the code it starts are one version. `check_code_ref` stops when the ref is unknown here. The wrapper is gzipped and base64-encoded into the job's `--args`.
- **The provider file** is made by `provider_json` (`python3 -I`) from the site's model values and travels in the wrapper.
- **No two executions at once.** `execute` lists the executions and refuses while one has a running count of at least 1 (`running_execution`). It prints the new execution's name and writes it to `<state folder>/last-execution`; `log` and `status` default to it.
- `delete` without `--yes` prints what it would do and exits 1. `status` prints the newest executions and the factory's stop, if any (`stop_line`).
- `log` passes the lines through `drop_noise` and `bin/sanitise`; nothing unsanitised is printed.

## The sanitiser

`operator/bin/sanitise` filters standard input to standard output. The rules file is `$SITE_SANITISE_RULES` (relative to the site file's folder), else `sanitise.rules` beside the site file, outside every repository, because the patterns are the site's names. Without the file the filter warns and applies only the three built-in rules (ANSI escapes, JWTs, GitHub tokens). The file adds `PATTERN => REPLACEMENT` lines, `drop: PATTERN` lines (the whole line is dropped), `#` comments and blank lines. Group references `\1` to `\99` work in a replacement; any other backslash is literal. An empty or invalid pattern, a missing group and a line that is no rule are faults (exit 2).

`sanitise check FILE...` is the leak check. It runs every built-in pattern and every pattern of the file, replacements and drops included, over the files and exits 0 with `sanitise: clean`, 1 after printing `file:line: rule` for each hit, 2 on a fault and 3 without a rules file (a check against nothing proves nothing). A report names the file, the line and the rule, never the matched text.

## The skill's scripts

- **Every `python3` starts with `-I`**, as its first option, for `-c` and for a program on standard input alike. The skill runs from a project checkout where agents write files, and `-I` keeps a planted `json.py` out of the import path (`docs/decisions.md`). `tests/operator_scripts/test_operator_python_isolation.py` pins it.
- **A hosting read is assigned to a variable before it is parsed** (`x=$(hosting_repo_api GET ...) || exit 1`), so a failing read ends with the client's message and not a traceback.
- **Comments are posted only through `comment.sh <pr> <file>`**, which appends the signature line (`— Kumpel, for the human who owns this project`) and the marker `<!-- kumpel -->` once. `merge.sh` and the start commit carry Kumpel's signature as well. The text-pin tests are `tests/operator_scripts/test_operator_skill_signature.py` and `tests/operator_scripts/test_operator_texts.py`.
- `reset-to-tag.sh <tag> [--yes]` closes the open work-item pull requests, deletes the `work-item/` branches and moves `main` to the tag's commit by force, each step stopping at its first failure.

## Tests of the scripts

The scripts run for real, in `tmp_path`, with stand-ins on the `PATH` for `gcloud`, `gh` and `curl` (they record their arguments and answer from a plan) and the real `git` against a local bare repository. Nothing reaches the network.

- `tests/support/operator_support.py`: the paths of the scripts, `INTERFACE_KEYS`, `operator_environment`, and runners for a script, `site`, a library and the hosting client.
- `tests/support/operator_job_support.py`: the job's site values, `words` (the words of a recorded call), the wrapper's pattern and the `gcloud` stand-in.
- `tests/support/operator_skill_support.py`: `SKILL`, `SCRIPTS`, the `curl` stand-in's `Request` records and `Operator`, a machine with a site, answers and a bare remote.
- `tests/support/site_check_support.py`: `Machine`, a machine for `site check`, and the readers of its `ok`/`FAIL` lines.

Test modules by script: `test_operator_site.py`, `test_operator_site_example.py` and `test_operator_site_check.py` (the site file, its example and `site check`); `test_operator_hosting.py`; `test_operator_job.py` and `test_operator_job_log.py`; `test_operator_sanitise.py`; `test_operator_skill_scripts.py`, `test_operator_merge_reset.py`, `test_operator_skill_signature.py`, `test_operator_skill_name.py` (neither skill text names the repository's old name) and `test_operator_texts.py`; `test_operator_python_isolation.py`.
