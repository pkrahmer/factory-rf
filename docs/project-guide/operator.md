# The operator's scripts

This file covers the shell and Python scripts under `operator/`, and the tests that run them. They let an operator set up one machine from one site file, and drive an instance from a terminal. Read the index, [README.md](README.md), first. The exact detail (every status code, key and file) is in the *Reference* at the end. The operator's side (install, the values, the stops) is *Setting up an operator's machine* in [site.md](../operator-guide/site.md).

## The layout

The scripts are small and each has one job. The loader and the hosting client are libraries that the others source; everything else is a command. [README.md](../../operator/README.md) in `operator/` is the documenter's table of the files; keep it current from the docs criterion and do not copy it here.

    operator/site.env.example
    operator/lib/site.sh           site_path, site_load, site_require, site_value, site_refuse_repository, site_gcloud_with, site_job_keys
    operator/lib/hosting.sh        hosting_token, hosting_api, hosting_repo_api, hosting_git, hosting_api_url
    operator/bin/site              path | init | show | get | check
    operator/bin/sanitise          sanitise < raw > clean | sanitise check FILE...
    operator/job/job.sh            create | update | execute | delete | log | status
    operator/vm/                   setup.sh, job-start.sh, factory.service, git-credential-factory, Dockerfile
    operator/template/             CLAUDE.md, Makefile, factory/
    operator/skill/kumpel/         SKILL.md, references/, scripts/
    operator/opencode/command/kumpel.md
    operator/claude/commands/kumpel.md

- [site.env.example](../../operator/site.env.example) holds every key of the site file, each with a comment and a made-up value. `site init` copies it.
- `operator/vm/` sets up and runs an instance on a VM; its `Dockerfile` is the base image's.
- `operator/template/` is what the operator copies into a new project.
- The skill's `references/` hold the standing orders and how to answer, approve and shape. Its `scripts/` are `settings.sh`, `status.sh`, `wait.sh`, `approval.sh`, `next-story.sh`, `start-story.sh`, `comment.sh`, `merge.sh` and `reset-to-tag.sh`.
- The two `kumpel.md` files are the `/kumpel` command, one for each tool.

See also: *The skill's scripts* below.

## The site file and its loader

The site file holds a site's own values, the `SITE_*` keys, as `KEY=value` lines. The loader, [site.sh](../../operator/lib/site.sh), reads them as data and exports them for the scripts that source it. [site](../../operator/bin/site) is the command for the file.

    site_path                          -> prints the file's path
    site_load                          -> 0 | 1 | 2 | 3
    site_require NAME...               -> 0 | 2
    site_value NAME                    -> prints the value
    site_refuse_repository PATH        -> 0 | 3
    site_gcloud_with RUNNER ARG...     -> runs RUNNER with the site's gcloud flags

- The path is `$FACTORY_SITE`, else `$XDG_CONFIG_HOME/kumpel/site.env`, else `~/.config/kumpel/site.env`.
- The folder for state is `~/.local/state/kumpel/` (`$XDG_STATE_HOME/kumpel`); `job.sh` keeps `last-execution` there.
- `site_load` reads each line and stores the value literally. It never sources the file and never runs a value.
- A value reaches `eval` only as the right-hand side of an assignment to a name that `_site_is_name` has accepted.
- One pair of matching quotes around a whole value is removed. A blank after `=` is a fault.
- Only `SITE_` keys are allowed. Another key, a line without `=` and a name that is not upper case, digits and `_` are faults, reported as `site: <file>:<line>: <what>`.
- A variable that is already set, even empty, is not overwritten, so a test or an operator overrides one value for one run.
- The whole file is checked before any value is exported, so a faulty file leaves the environment as it was.
- `site_refuse_repository` refuses a path inside a git work tree. It asks git from the nearest existing ancestor, because `site init` runs before the folder exists.
- `site_require` names every missing key; a bare name gets the `SITE_` prefix.
- `site_gcloud_with` adds `--project` to every call, `--region` to every `gcloud run` call and `--impersonate-service-account` when `SITE_IMPERSONATE` is set. Nothing is left to gcloud's own defaults.
- `site check` is read-only. It prints one `ok NAME` or `FAIL NAME: DETAIL` line for each check, and a check whose keys are missing fails on its keys and does not run.

See also: *Status of the site scripts* in the *Reference*.

## The hosting client

The scripts talk to the hosting service through one small client, [hosting.sh](../../operator/lib/hosting.sh), so that the token is handled in one place. It is sourced after `site.sh`, and loads the site itself when no `SITE_` variable is set.

    hosting_token                      -> prints the token
    hosting_api METHOD PATH [BODY]     -> prints the body of a 2xx answer
    hosting_repo_api METHOD PATH [BODY]
    hosting_git ARG...                 -> runs git with the token
    hosting_api_url                    -> prints the API base

- `hosting_token` runs `SITE_TOKEN_CMD` with `sh -c`; without it, it runs `gh auth token` when `gh` is installed.
- It prints the first line, trimmed, and returns 4 when the source fails or prints nothing.
- It never repeats the source's output, because an error text can hold a secret.
- `hosting_api` returns 22 for any other status than 2xx and prints `hosting: <method> <path>: <status> <message>` on standard error. Without a token it returns 4.
- `hosting_repo_api` prefixes `/repos/$SITE_REPOSITORY` and returns 2 when the key is missing.
- The API base is `SITE_API_URL`, else `https://api.github.com`.
- `hosting_git` runs git with a Basic header for https remotes.
- The token is in no argument list. `hosting_api` writes curl's configuration (url, headers, body) to curl's standard input with `printf`, a builtin.
- `hosting_git` passes the header through `GIT_CONFIG_COUNT` and `GIT_CONFIG_KEY_n`/`GIT_CONFIG_VALUE_n`, with an empty `credential.helper` so a stored credential does not answer. `ps` shows neither.

## `job.sh`

[job.sh](../../operator/job/job.sh) creates, runs and reads the factory's Cloud Run job from the site's values alone. It reaches gcloud only through `site_gcloud_with`.

    job.sh create [--dry-run]
    job.sh update [--dry-run]
    job.sh execute
    job.sh delete [--yes]
    job.sh log [N] [--execution NAME] [--quiet]
    job.sh status

- `--dry-run` prints the gcloud call one argument per line and runs nothing.
- `require_settings` needs every key of `site_job_keys` and stops naming the missing ones. No value is guessed.
- Only `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT` and `SITE_IDLE_MINUTES` have defaults.
- `check_instance`, `check_env_values` and `check_costs` refuse values that would break the env list (`@` is its delimiter) or the shell text.
- `write_wrapper` takes [job-start.sh](../../operator/vm/job-start.sh) from `git show "$SITE_CODE_REF:operator/vm/job-start.sh"`, never from the working tree, so the wrapper and the code it starts are one version.
- `check_code_ref` stops when `SITE_CODE_REF` is unknown here. The wrapper is gzipped and base64-encoded into the job's `--args`.
- `provider_json` makes the provider file with `python3 -I` from the site's model values; it travels in the wrapper.
- `execute` lists the executions and refuses while one has a running count of at least 1 (`running_execution`). It prints the new execution's name and writes it to `<state folder>/last-execution`; `log` and `status` default to it.
- `delete` without `--yes` prints what it would do and exits 1.
- `status` prints the newest executions and the factory's stop, if any (`stop_line`).
- `log` passes the lines through `drop_noise` and [sanitise](../../operator/bin/sanitise); nothing unsanitised is printed.

## The sanitiser

The sanitiser strips the site's names and the tokens from text that leaves the machine, and proves a file clean. [sanitise](../../operator/bin/sanitise) filters standard input to standard output.

    sanitise < raw > clean
    sanitise check FILE...

- The rules file is `$SITE_SANITISE_RULES` (relative to the site file's folder), else `sanitise.rules` beside the site file. It lies outside every repository, because the patterns are the site's names.
- Without the file the filter warns and applies only the three built-in rules: ANSI escapes, JWTs and GitHub tokens.
- The file adds `PATTERN => REPLACEMENT` lines, `drop: PATTERN` lines (the whole line is dropped), `#` comments and blank lines.
- Group references `\1` to `\99` work in a replacement; any other backslash is literal.
- An empty or invalid pattern, a missing group and a line that is no rule are faults (exit 2).
- `sanitise check` runs every built-in pattern and every pattern of the file, replacements and drops included, over the files.
- It exits 0 with `sanitise: clean`, 1 after printing `file:line: rule` for each hit, 2 on a fault and 3 without a rules file, because a check against nothing proves nothing.
- A report names the file, the line and the rule, never the matched text.

## The skill's scripts

The skill is `operator/skill/kumpel/`. Its scripts run from a project checkout where agents write files, so they take care with what they run and what they post.

    operator/skill/kumpel/scripts/comment.sh <pr> <file>
    operator/skill/kumpel/scripts/reset-to-tag.sh <tag> [--yes]

- Every `python3` starts with `-I`, as its first option, for `-c` and for a program on standard input alike. It keeps a planted `json.py` out of the import path ([decisions.md](../decisions.md)).
- [test_operator_python_isolation.py](../../tests/operator_scripts/test_operator_python_isolation.py) pins that rule.
- A hosting read is assigned to a variable before it is parsed (`x=$(hosting_repo_api GET ...) || exit 1`), so a failing read ends with the client's message and not a traceback.
- Comments are posted only through `comment.sh`. It appends the signature line (`— Kumpel, for the human who owns this project`) and the marker `<!-- kumpel -->` once.
- `merge.sh` and the start commit carry Kumpel's signature as well.
- [test_operator_skill_signature.py](../../tests/operator_scripts/test_operator_skill_signature.py) and [test_operator_texts.py](../../tests/operator_scripts/test_operator_texts.py) pin the texts.
- `reset-to-tag.sh` closes the open work-item pull requests, deletes the `work-item/` branches and moves `main` to the tag's commit by force. Each step stops at its first failure.

## Tests of the scripts

The scripts run for real, in `tmp_path`, with stand-ins on the `PATH` for `gcloud`, `gh` and `curl`. The stand-ins record their arguments and answer from a plan. The real `git` runs against a local bare repository. Nothing reaches the network.

    tests/support/operator_support.py
    tests/support/operator_job_support.py
    tests/support/operator_skill_support.py
    tests/support/site_check_support.py

- `operator_support.py` holds the paths of the scripts, `INTERFACE_KEYS`, `operator_environment`, and runners for a script, `site`, a library and the hosting client.
- `operator_job_support.py` holds the job's site values, `words` (the words of a recorded call), the wrapper's pattern and the `gcloud` stand-in.
- `operator_skill_support.py` holds `SKILL`, `SCRIPTS`, the `curl` stand-in's `Request` records and `Operator`, a machine with a site, answers and a bare remote.
- `site_check_support.py` holds `Machine`, a machine for `site check`, and the readers of its `ok`/`FAIL` lines.
- The tests of the scripts are in `tests/operator_scripts/`; the next section lists them.

## Reference

### Status of the site scripts

- `site_load` returns 0, 1 (no file), 2 (a fault) or 3 (the file lies in a repository).
- `site_require` returns 2 and names every missing key.
- `bin/site` ends with the same codes. `site check` ends 0 (`site: ready`) or 1 (`site: N failed`). A wrong command line is 2.
- The checks of `site check` are `check_keys`, `check_tools`, `check_token`, `check_repository`, `check_checkout`, `check_identity`, `check_secrets`, `check_code`, `check_no_proxy` and `check_job`.
- `site_job_keys` holds the keys that `job.sh` requires.

### Test modules by script

| Script | Test modules in `tests/operator_scripts/` |
| --- | --- |
| the site file, its example and `site check` | `test_operator_site.py`, `test_operator_site_example.py`, `test_operator_site_check.py` |
| the hosting client | `test_operator_hosting.py` |
| `job.sh` | `test_operator_job.py`, `test_operator_job_log.py` |
| the sanitiser | `test_operator_sanitise.py` |
| the skill's scripts | `test_operator_skill_scripts.py`, `test_operator_merge_reset.py`, `test_operator_skill_signature.py`, `test_operator_texts.py` |
| the skill's name (neither skill text names the repository's old name) | `test_operator_skill_name.py` |
| the Python isolation | `test_operator_python_isolation.py` |
