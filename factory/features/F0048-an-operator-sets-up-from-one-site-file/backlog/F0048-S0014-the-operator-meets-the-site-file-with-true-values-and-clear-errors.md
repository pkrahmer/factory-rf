# The operator meets the site file, with true values and clear errors

<!-- folded by the human on 2026-11-03 from the three stories the acceptance F0048-A0001 proposed (decision 18) -->

## Description

The acceptance F0048-A0001 found three places where an operator does not meet the site file, or meets it with wrong values. This story fixes all three. Each part keeps the scope the acceptance gave it.

**A. The example names the required keys and the defaults that `job.sh` uses.** `operator/site.env.example` is the operator's first copy of the site file (`site init` writes it) and, by `docs/operator-guide.md` (*The keys*), "the first place to look". Its comments were S0001's reading of the key names before any story used the keys, and no later story confirmed them. Eight keys that `site_job_keys` in `operator/lib/site.sh` requires, so that `job.sh create` refuses without them and `site check` fails `keys`, are marked `Optional`: `SITE_PROXY`, `SITE_NO_PROXY`, `SITE_INSTANCE`, `SITE_CODE_REF`, `SITE_MODEL_BASE_URL`, `SITE_LOGIN_URL`, `SITE_LOGIN_SCOPE` and `SITE_LOGIN_CLIENT_ID`. Six defaults are not the ones `job.sh` uses: CPU 4 (`job.sh` uses 8), memory 16Gi (32Gi), timeout 24h (14400), idle minutes 30 (60), and the two prices "no cost record" (`0`). The `SITE_SANITISE_RULES` comment says "the default is none", where `sanitise` reads `sanitise.rules` beside the site file. An operator who deletes an "optional" line gets a job of another size without a word. This part rewrites those comments so that each says what the code does, and pins the agreement with a test. The example's values stay as they are; `SITE_TIMEOUT=24h` stays too, because `gcloud run jobs --task-timeout` takes a duration as well as seconds (decision 18).

**B. The operator's README, the skill and `site`'s usage name the site file.** `operator/README.md`'s *Installing* says that "the first act of the skill asks for the repository and the checkout and writes `~/.config/kumpel/settings.json`", and its *Needs* asks for "`gh` logged in". Since S0001 and S0004, the site file gives the repository and the checkout, and `SITE_TOKEN_CMD` replaces the `gh` login. The guide's step 9 (*Setting up an operator's machine*) sends the reader to exactly this section. `operator/skill/kumpel/SKILL.md` (*Before anything*, step 1) tells the agent to ask the human for the repository and the checkout and does not name the site file. And `operator/bin/site` accepts `check` (S0009) while its usage line still reads `usage: site path | init | show | get SITE_X`. This part brings the three in line with what the commands do. It changes no other line of the skill, its references or its switches, and no behaviour of `site` except the usage text.

**C. The operator's scripts run Python isolated and stop at a failed read with the hosting message.** The operator's scripts parse the code host's answers and their own JSON files with inline Python (`python3 -c '...'` and `python3 - <<'PY'`) in 20 places in `operator/bin/site`, `operator/job/job.sh` and six of the skill's scripts. Both forms put the current folder first on Python's import path. A script run from a project checkout, where the factory's agents write files, would import a planted `json.py` instead of the standard library and run it with the operator's environment, the site's token command included. Only `operator/bin/sanitise` and one call in `job.sh` use `-I` (isolated mode). This part makes every Python start in those scripts isolated. In the same scripts, `status.sh` pipes `hosting_repo_api` straight into Python at three reads, so a failing read prints the hosting client's message followed by a `JSONDecodeError` traceback. S0008 fixed the same pattern in `merge.sh` and `reset-to-tag.sh` by assigning the answer first; this part does the same in `status.sh`. What every script prints on success stays line for line, so that the skill's text needs no change beyond part B.

## Interface

**A.** `operator/site.env.example` (the comments only; every `SITE_*=value` line stays):

- Each key's comment line is the line directly above it. Its last sentence is one of: `Required.` (`SITE_REPOSITORY`, `SITE_CHECKOUT`); `Required for a job.` (exactly the 18 keys of `site_job_keys` in `operator/lib/site.sh`); or `Optional; the default is <default>.` (every other key).
- The new comment lines, word for word:
  - `# The proxy through which the job and its tools reach the network. Required for a job.`
  - `# The hosts reached without the proxy, comma-separated: the model API's host, never a code host. Required for a job.`
  - `# The factory instance's name in the job: letters, digits, '.', '_' and '-'. Required for a job.`
  - `# The branch or tag of the factory's code the job runs. Required for a job.`
  - `# The model provider's API. Required for a job.`
  - `# The login service that issues the model provider's tokens. Required for a job.`
  - `# The scope asked of the login service. Required for a job.`
  - `# The client id given to the login service. Required for a job.`
  - `# The model's price per million input tokens, in dollars. Optional; the default is 0.`
  - `# The model's price per million output tokens, in dollars. Optional; the default is 0.`
  - `# The job's CPUs. Optional; the default is 8.`
  - `# The job's memory. Optional; the default is 32Gi.`
  - `# The job's task timeout, as gcloud takes it (seconds, or a duration such as 4h). Optional; the default is 14400.`
  - `# The idle minutes after which the job ends itself. Optional; the default is 60.`
  - `# The file of rules that sanitise what leaves the site, absolute or relative to the site file's folder. Optional; the default is sanitise.rules beside the site file.`

**B.** `operator/bin/site`: the usage line becomes `usage: site path | init | show | get SITE_X | check`, printed to standard error with exit 2 in every case where it is printed today. `site check` with an argument keeps `usage: site check`.

`operator/README.md`:

- *Installing* says, in this order: write the site file (`sh operator/bin/site init`, fill in the values, `sh operator/bin/site check`); install the skill and the command as today. When the site file gives `SITE_REPOSITORY` and `SITE_CHECKOUT`, `settings.json` holds only the switches (`sh scripts/settings.sh init` takes no argument); otherwise the skill asks for both. It names `docs/operator-guide.md`, *Setting up an operator's machine*.
- *Needs* names `git`, `curl`, `python3` and a POSIX shell, and a token from `SITE_TOKEN_CMD` or, without it, a `gh` login; `gcloud` for an instance in a Cloud Run job. The words "`gh` logged in for the project's GitHub" go.

`operator/skill/kumpel/SKILL.md`, *Before anything*, step 1: `sh scripts/settings.sh show` answers the repository and the checkout from the site file first (`SITE_REPOSITORY`, `SITE_CHECKOUT`). When it has no settings, run `sh scripts/settings.sh init` if the site file gives both. Otherwise ask the human for the two values and suggest putting them into the site file. Every other line of `SKILL.md` stays.

**C.** `operator/bin/site`, `operator/job/job.sh` and `operator/skill/kumpel/scripts/{status,settings,approval,comment,merge,reset-to-tag}.sh`:

- Every start of `python3` passes `-I` as its first option: `python3 -I -c '...' ARGS` and `python3 -I - ARGS <<'PY'`. The programs, their arguments and their output are unchanged.

`operator/skill/kumpel/scripts/status.sh`:

- The reads `GET /issues/<n>`, `GET /issues/<n>/comments?per_page=1&page=<count>` and `GET /commits?per_page=20` are each assigned to a variable first and parsed after. A failing read stops the script with exit 1, and the hosting client's message (`hosting: GET /repos/<repository>/...: <status> <message>`) is the last line on standard error. No Python traceback is printed. The read of the pull-request list keeps its behaviour.

Tests: `tests/test_operator_site_example.py` (A), a new `tests/test_operator_texts.py` (B), the `USAGE` constant of `tests/test_operator_site.py` (B, with the human's leave in `feature.md`, *The human's changes*), `tests/test_operator_python_isolation.py` (C), and new rows in `tests/test_operator_skill_scripts.py` for `status.sh` (C; the standing leave covers new rows that keep every earlier test's name and check). The helpers of `tests/operator_support.py`, `tests/operator_job_support.py` and `tests/operator_skill_support.py` serve all three. The list of required keys is read from `operator/lib/site.sh` by sourcing it (`$site_job_keys`), not copied into a test.

## Acceptance criteria

1. (A) The last sentence of each key's comment line in `operator/site.env.example`, as rows of one parametrized test over every key of the example: `Required.` for `SITE_REPOSITORY` and `SITE_CHECKOUT`; `Required for a job.` for each key of `site_job_keys`; and a sentence that starts with `Optional; the default is` for each of the other 11 keys (`SITE_API_URL`, `SITE_TOKEN_CMD`, `SITE_IMPERSONATE`, `SITE_MODEL_INPUT_COST`, `SITE_MODEL_OUTPUT_COST`, `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT`, `SITE_IDLE_MINUTES`, `SITE_RESET_REPOSITORY`, `SITE_SANITISE_RULES`). A key of `site_job_keys` whose comment says `Optional` fails its row, and so does an optional key whose comment says `Required for a job.`.
2. (A) The default named in the comment of `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT` and `SITE_IDLE_MINUTES` equals what `job.sh create --dry-run` puts in its call when the key's line is left out of a site file copied from the example: `--cpu=8`, `--memory=32Gi`, `--task-timeout=14400` and `FACTORY_IDLE_SHUTDOWN_MINUTES=60` in the env list. One row per key; a comment that names another value fails its row.
3. (A) The default named in the comments of `SITE_MODEL_INPUT_COST` and `SITE_MODEL_OUTPUT_COST` (`0`) equals the price in the `provider.json` that the job's wrapper writes when the key's line is left out, read back as S0005's tests read it. One row per key.
4. (A) The comment of `SITE_SANITISE_RULES` names `sanitise.rules beside the site file` as its default.
5. (A) Every `SITE_*=value` line of the example is unchanged: `site show` on a copy of the example prints `=set` for every key, in the same order as before.
6. (B) `operator/README.md`'s *Installing* section contains `site init` and `site check`, and contains no sentence saying that the skill's first act asks for the repository and the checkout. A row with today's text fails.
7. (B) `operator/README.md`'s *Needs* section contains `SITE_TOKEN_CMD` and does not contain `` `gh` logged in ``.
8. (B) `sh operator/bin/site` with no command, with `bogus`, and with `get` alone each print `usage: site path | init | show | get SITE_X | check` on standard error and exit 2 (rows of S0001's usage test); `site check extra` still prints `usage: site check` and exits 2.
9. (B) `operator/skill/kumpel/SKILL.md`'s *Before anything* step 1 names `SITE_REPOSITORY`, `SITE_CHECKOUT` and the site file. The other numbered steps and the loop are word for word as before, which the test checks against a copy of today's text after step 1.
10. (C) A `json.py` that writes a marker file when it is imported lies in the working folder of each script, one row per script: `settings.sh show`, `settings.sh init` (the site gives both values), `status.sh`, `comment.sh 7 <file>`, `site check` (stand-ins answering as in S0009's tests) and `job.sh create --dry-run`. Each run leaves no marker file and prints the same lines as the same run from a folder without `json.py`.
11. (C) A text check over the files of the Interface: every line that starts `python3` as a command passes `-I` as its first option. Rows: one per file. A file with a `python3 -c` without `-I` fails its row.
12. (C) `status.sh` with one work-item pull request, where one read is answered 500: rows for `GET /issues/<n>`, for the comments page and for `GET /commits`. Each prints `hosting: GET /repos/owner/repo/<path>: 500 <message>` as the last line on standard error, prints no line that contains `Traceback`, and exits 1. With every read answered 200, the output is the same as before (the existing rows of `status.sh`'s test stay green).
13. `make check` stays green.
14. docs: `docs/operator-guide.md`, *The site file*: drop "the stories to come make the other keys live" from its intro. In *The keys*, replace "The defaults are those of the example's comments and are confirmed as the stories that read each key land" with a sentence saying that the example's comments and this table name the same required keys and defaults, and make the `SITE_TIMEOUT` row say what format the value takes (seconds, or a duration as gcloud takes it). *The `site` command*: the usage line with `check`; step 9 of *Setting up an operator's machine* stays true as written. `docs/decisions.md`: one entry stating that the operator's scripts start Python with `-I` and why (a folder an agent writes may be the working folder), with the rejected alternative (`cd` to the script's folder before each call). `README.md` and the project guide: none, because nothing changes for them.

## Smoke test

```bash
grep -c 'Required for a job\.$' operator/site.env.example
grep -E "^# The job's (CPUs|memory)\." operator/site.env.example
sh operator/bin/site 2>&1; echo "exit $?"
r=$(pwd); d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'open("%s/imported", "w").close()\n' "$d" > "$d/json.py"
printf 'SITE_REPOSITORY=owner/repo\nSITE_CHECKOUT=%s\n' "$d" > "$d/site.env"
(cd "$d" && HOME="$d" XDG_CONFIG_HOME="$d/config" FACTORY_SITE="$d/site.env" sh "$r/operator/skill/kumpel/scripts/settings.sh" init >/dev/null 2>&1)
test -e "$d/imported"; echo "imported: $?"
```

Expect: `18`; the two lines `# The job's CPUs. Optional; the default is 8.` and `# The job's memory. Optional; the default is 32Gi.`; then `usage: site path | init | show | get SITE_X | check` and `exit 2`; then `imported: 1`.

## Journal
