---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 515
comments_read: [6599499091]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T08:47:10.602256Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T08:47:10.608804Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-03T08:47:38.006721Z'
  stage: intake
  run: e104c71b35114c50b447ef49b4dd25d2
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-03T08:47:43.707132Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-03T08:52:36.425091Z'
  stage: tests
  run: d06f7b4cb3894ea58c23c86495936aed
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-03T08:52:42.195554Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-03T08:57:26.994973Z'
  stage: doing
  run: 5258c7909e8c4f2ebb789c7c606fad16
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-03T08:57:32.870255Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-03T08:59:43.496521Z'
  stage: review
  run: e4abc88e80e64bd08cf0bac6067d36c5
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-03T08:59:49.094270Z'
  stage: doing
- number: 11
  speaker: coder
  kind: question
  at: '2026-11-03T09:00:28.769335Z'
  stage: doing
  run: dbf4e80be8c24ef288c648e00a244cb5
  blocked: question
- number: 12
  speaker: human
  kind: comment
  at: '2026-11-03T09:02:20.979497Z'
  stage: doing
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-03T09:02:23.897098Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-03T09:02:48.903391Z'
  stage: doing
  run: de1caa48bbc6470eaf4b5bf39915aa7f
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-03T09:02:54.532461Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-03T09:04:16.182468Z'
  stage: tests
  run: fc33ad334ae5408d97989ff6d9b6090d
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-03T09:04:22.013230Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-03T09:08:09.957980Z'
  stage: doing
  run: 09e24eb895af4a33b9d64e360ebd573f
---

# The operator meets the site file, with true values and clear errors

<!-- folded by the human on 2026-11-03 from the three stories the acceptance F0048-A0001 proposed (decision 18) -->

## Description

The acceptance F0048-A0001 found three places where an operator does not meet the site file, or meets it with wrong values (parts A to C). The human's answers on the acceptance's decisions add two more (parts D and E, decision 21). Each part keeps the scope it is given here.

**A. The example names the required keys and the defaults that `job.sh` uses.** `operator/site.env.example` is the operator's first copy of the site file (`site init` writes it) and, by `docs/operator-guide.md` (*The keys*), "the first place to look". Its comments were S0001's reading of the key names before any story used the keys, and no later story confirmed them. Eight keys that `site_job_keys` in `operator/lib/site.sh` requires, so that `job.sh create` refuses without them and `site check` fails `keys`, are marked `Optional`: `SITE_PROXY`, `SITE_NO_PROXY`, `SITE_INSTANCE`, `SITE_CODE_REF`, `SITE_MODEL_BASE_URL`, `SITE_LOGIN_URL`, `SITE_LOGIN_SCOPE` and `SITE_LOGIN_CLIENT_ID`. Six defaults are not the ones `job.sh` uses: CPU 4 (`job.sh` uses 8), memory 16Gi (32Gi), timeout 24h (14400), idle minutes 30 (60), and the two prices "no cost record" (`0`). The `SITE_SANITISE_RULES` comment says "the default is none", where `sanitise` reads `sanitise.rules` beside the site file. An operator who deletes an "optional" line gets a job of another size without a word. This part rewrites those comments so that each says what the code does, and pins the agreement with a test. The human chose the example's sizes (decision 21): `job.sh`'s defaults become 4 CPUs, 16Gi, 86400 seconds (24 hours) and 30 idle minutes, and the prices' default stays 0. The example's values stay as they are; `SITE_TIMEOUT=24h` stays too, because `gcloud run jobs --task-timeout` takes a duration as well as seconds (decision 18).

**B. The operator's README, the skill and `site`'s usage name the site file.** `operator/README.md`'s *Installing* says that "the first act of the skill asks for the repository and the checkout and writes `~/.config/kumpel/settings.json`", and its *Needs* asks for "`gh` logged in". Since S0001 and S0004, the site file gives the repository and the checkout, and `SITE_TOKEN_CMD` replaces the `gh` login. The guide's step 9 (*Setting up an operator's machine*) sends the reader to exactly this section. `operator/skill/kumpel/SKILL.md` (*Before anything*, step 1) tells the agent to ask the human for the repository and the checkout and does not name the site file. And `operator/bin/site` accepts `check` (S0009) while its usage line still reads `usage: site path | init | show | get SITE_X`. This part brings the three in line with what the commands do. `operator/README.md` is the documenter's alone (decision 22), so its two sections change in the docs stage, by the docs criterion. It changes no other line of the skill, its references or its switches, and no behaviour of `site` except the usage text.

**D. `site check` tells a missing job from a job it cannot read.** The `job` line never fails (S0009), but today a missing job and a failed `gcloud run jobs describe` (no rights, a wrong project) both read `does not exist yet`, so a rights problem shows only at `job.sh` time. This part keeps the line informational and says which of the two it met (decision 21).

**E. A space directly after `=` in the site file is a fault.** Since S0001 a space before `=` is a fault, while a space after it belongs to the value, so `SITE_PROXY= http://p` silently sets a value with a leading space that fails later and far from its cause. This part makes a space or a tab directly after `=` a fault too, with the loader's fault message naming the line, as for a space before `=` (decision 21).

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
  - `# The job's CPUs. Optional; the default is 4.`
  - `# The job's memory. Optional; the default is 16Gi.`
  - `# The job's task timeout, as gcloud takes it (seconds, or a duration such as 4h). Optional; the default is 86400.`
  - `# The idle minutes after which the job ends itself. Optional; the default is 30.`
  - `# The file of rules that sanitise what leaves the site, absolute or relative to the site file's folder. Optional; the default is sanitise.rules beside the site file.`

`operator/job/job.sh`: when a key's line is left out, the job takes `--cpu=4`, `--memory=16Gi`, `--task-timeout=86400` and `FACTORY_IDLE_SHUTDOWN_MINUTES=30`. Nothing else in the script changes for part A.

**B.** `operator/bin/site`: the usage line becomes `usage: site path | init | show | get SITE_X | check`, printed to standard error with exit 2 in every case where it is printed today. `site check` with an argument keeps `usage: site check`.

`operator/README.md` (the documenter's, in the docs stage; criterion 16):

- *Installing* says, in this order: write the site file (`sh operator/bin/site init`, fill in the values, `sh operator/bin/site check`); install the skill and the command as today. When the site file gives `SITE_REPOSITORY` and `SITE_CHECKOUT`, `settings.json` holds only the switches (`sh scripts/settings.sh init` takes no argument); otherwise the skill asks for both. It names `docs/operator-guide.md`, *Setting up an operator's machine*.
- *Needs* names `git`, `curl`, `python3` and a POSIX shell, and a token from `SITE_TOKEN_CMD` or, without it, a `gh` login; `gcloud` for an instance in a Cloud Run job. The words "`gh` logged in for the project's GitHub" go.

`operator/skill/kumpel/SKILL.md`, *Before anything*, step 1: `sh scripts/settings.sh show` answers the repository and the checkout from the site file first (`SITE_REPOSITORY`, `SITE_CHECKOUT`). When it has no settings, run `sh scripts/settings.sh init` if the site file gives both. Otherwise ask the human for the two values and suggest putting them into the site file. Every other line of `SKILL.md` stays.

**D.** `site check`'s `job` line: `job: <name> does not exist yet` when gcloud answers that the job is not found; `job: <name> cannot be read: <the first line of gcloud's error>` when the describe fails for any other reason. Both pass; the line never fails, and the check's result does not change.

**E.** The site file's loader (`operator/lib/site.sh`): a line with a space or a tab directly after its `=` is a fault, reported with the same message form and line number as a space before `=`. A space inside or at the end of a value keeps today's behaviour.

**C.** `operator/bin/site`, `operator/job/job.sh` and `operator/skill/kumpel/scripts/{status,settings,approval,comment,merge,reset-to-tag}.sh`:

- Every start of `python3` passes `-I` as its first option: `python3 -I -c '...' ARGS` and `python3 -I - ARGS <<'PY'`. The programs, their arguments and their output are unchanged.

`operator/skill/kumpel/scripts/status.sh`:

- The reads `GET /issues/<n>`, `GET /issues/<n>/comments?per_page=1&page=<count>` and `GET /commits?per_page=20` are each assigned to a variable first and parsed after. A failing read stops the script with exit 1, and the hosting client's message (`hosting: GET /repos/<repository>/...: <status> <message>`) is the last line on standard error. No Python traceback is printed. The read of the pull-request list keeps its behaviour.

Tests: `tests/test_operator_site_example.py` (A), a new `tests/test_operator_texts.py` (B, over `SKILL.md` only; the README's sections are the docs criterion's), new rows in the tests of `site check` (D) and of the loader (E), the `USAGE` constant of `tests/test_operator_site.py` (B, with the human's leave in `feature.md`, *The human's changes*), `tests/test_operator_python_isolation.py` (C), and new rows in `tests/test_operator_skill_scripts.py` for `status.sh` (C; the standing leave covers new rows that keep every earlier test's name and check). The helpers of `tests/operator_support.py`, `tests/operator_job_support.py` and `tests/operator_skill_support.py` serve all three. The list of required keys is read from `operator/lib/site.sh` by sourcing it (`$site_job_keys`), not copied into a test.

## Acceptance criteria

1. (A) The last sentence of each key's comment line in `operator/site.env.example`, as rows of one parametrized test over every key of the example: `Required.` for `SITE_REPOSITORY` and `SITE_CHECKOUT`; `Required for a job.` for each key of `site_job_keys`; and a sentence that starts with `Optional; the default is` for each of the other 11 keys (`SITE_API_URL`, `SITE_TOKEN_CMD`, `SITE_IMPERSONATE`, `SITE_MODEL_INPUT_COST`, `SITE_MODEL_OUTPUT_COST`, `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT`, `SITE_IDLE_MINUTES`, `SITE_RESET_REPOSITORY`, `SITE_SANITISE_RULES`). A key of `site_job_keys` whose comment says `Optional` fails its row, and so does an optional key whose comment says `Required for a job.`.
2. (A) The default named in the comment of `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT` and `SITE_IDLE_MINUTES` equals what `job.sh create --dry-run` puts in its call when the key's line is left out of a site file copied from the example: `--cpu=4`, `--memory=16Gi`, `--task-timeout=86400` and `FACTORY_IDLE_SHUTDOWN_MINUTES=30` in the env list. One row per key; a comment that names another value fails its row.
3. (A) The default named in the comments of `SITE_MODEL_INPUT_COST` and `SITE_MODEL_OUTPUT_COST` (`0`) equals the price in the `provider.json` that the job's wrapper writes when the key's line is left out, read back as S0005's tests read it. One row per key.
4. (A) The comment of `SITE_SANITISE_RULES` names `sanitise.rules beside the site file` as its default.
5. (A) Every `SITE_*=value` line of the example is unchanged: `site show` on a copy of the example prints `=set` for every key, in the same order as before.
6. (B) `sh operator/bin/site` with no command, with `bogus`, and with `get` alone each print `usage: site path | init | show | get SITE_X | check` on standard error and exit 2 (rows of S0001's usage test); `site check extra` still prints `usage: site check` and exits 2.
7. (B) `operator/skill/kumpel/SKILL.md`'s *Before anything* step 1 names `SITE_REPOSITORY`, `SITE_CHECKOUT` and the site file. The other numbered steps and the loop are word for word as before, which the test checks against a copy of today's text after step 1.
8. (C) A `json.py` that writes a marker file when it is imported lies in the working folder of each script, one row per script: `settings.sh show`, `settings.sh init` (the site gives both values), `status.sh`, `comment.sh 7 <file>`, `site check` (stand-ins answering as in S0009's tests) and `job.sh create --dry-run`. Each run leaves no marker file and prints the same lines as the same run from a folder without `json.py`.
9. (C) A text check over the files of the Interface: every line that starts `python3` as a command passes `-I` as its first option. Rows: one per file. A file with a `python3 -c` without `-I` fails its row.
10. (C) `status.sh` with one work-item pull request, where one read is answered 500: rows for `GET /issues/<n>`, for the comments page and for `GET /commits`. Each prints `hosting: GET /repos/owner/repo/<path>: 500 <message>` as the last line on standard error, prints no line that contains `Traceback`, and exits 1. With every read answered 200, the output is the same as before (the existing rows of `status.sh`'s test stay green).
11. (D) `site check` with a `gcloud` stand-in: a describe answered as not found prints `job: <name> does not exist yet`; a describe that fails with `PERMISSION_DENIED` prints `job: <name> cannot be read: ` followed by the stand-in's first error line; an existing job prints today's line. All three rows leave the check's result as it was without the line.
12. (E) The loader refuses `SITE_PROXY= http://p` and `SITE_PROXY=	http://p` with the fault message naming the line, as it refuses `SITE_PROXY =http://p`; it still accepts `SITE_PROXY=http://p` and a value with a space inside it. Rows of one parametrized test.
13. (A) `job.sh create --dry-run` with a site file that leaves out `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT` and `SITE_IDLE_MINUTES` puts the four defaults of the Interface in its call (S0005's rows of the defaults change to these values, with the human's leave).
14. (D) `site check` with a `gcloud` stand-in, as more rows of criterion 11's test: a describe whose error line contains `NOT_FOUND` (and not `Cannot find job`) prints `job: <name> does not exist yet`; a describe that fails with no text on standard error prints `job: <name> cannot be read: gcloud run jobs describe failed`. Both rows leave the check's result as it was without the line.
15. `make check` stays green.
16. docs: `docs/operator-guide.md`, *The site file*: drop "the stories to come make the other keys live" from its intro. In *The keys*, replace "The defaults are those of the example's comments and are confirmed as the stories that read each key land" with a sentence saying that the example's comments and this table name the same required keys and defaults, and make the `SITE_TIMEOUT` row say what format the value takes (seconds, or a duration as gcloud takes it). *The `site` command*: the usage line with `check`; step 9 of *Setting up an operator's machine* stays true as written. `docs/decisions.md`: one entry stating that the operator's scripts start Python with `-I` and why (a folder an agent writes may be the working folder), with the rejected alternative (`cd` to the script's folder before each call). `operator/README.md` (B): *Installing* and *Needs* as the Interface says. *Installing* contains `site init` and `site check` and no sentence saying that the skill's first act asks for the repository and the checkout; *Needs* contains `SITE_TOKEN_CMD` and not `` `gh` logged in ``. The guide's table of the keys gives the new job defaults, and its *The `site` command* says what the `job` line prints in each case. `README.md` and the project guide: none, because nothing changes for them.

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

Expect: `18`; the two lines `# The job's CPUs. Optional; the default is 4.` and `# The job's memory. Optional; the default is 16Gi.`; then `usage: site path | init | show | get SITE_X | check` and `exit 2`; then `imported: 1`.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete files and exact strings: the 15 comment lines word for word, the usage line, the `job` line texts, `-I` as first option, the status.sh read messages. Checked against the example: the 18 job keys are the 10 already marked "Required for a job." plus the 8 new ones, and the four untouched optional comments (API_URL, TOKEN_CMD, IMPERSONATE, RESET_REPOSITORY) already start "Optional; the default is".
   Criteria: each is testable by one parametrized test. Every stated rule has both sides: required vs optional in the comments (criterion 1), the loader's refused and accepted forms (12), the `job` line's not-found, unreadable and existing cases (11), usage with exit 2 and `check extra` (6), 500 on each of three reads vs all 200 (10), and `-I` per file (9). The defaults are each tested against what `job.sh` does (2, 3, 13). The leave for changing S0001, S0005 and S0009 tests is in feature.md. One note, not a question: the Interface says the pull-request list read "keeps its behaviour", and only the existing status.sh rows cover that.
   Smoke test: the commands are runnable and use no pytest. `grep -c` gives 18 once the 8 new lines exist. The two grep lines match the new comments. `site` with no command exits 2 with the usage. `imported: 1` follows from `test -e` failing when `-I` is in place. All four Expect parts are checkable against the output.
   Architecture: all changes are in the operator's shell and example files and in tests. The README is left to the documenter (decision 22), and the coder's write paths cover the rest. Nothing touches `src/factory/`.
   Scope: it matches F0048's S0014 entry and decisions 18, 21 and 22. Nothing in the feature's "Out of scope" is touched.
4. factory: started tests as vm.
5. tester: I wrote the tests for every acceptance criterion. One run of the changed test files (`uv run pytest -q -n 8 <files>`) fails where the code does not exist yet: the example's comments, the job's defaults, the usage line, the space after `=`, `-I`, the status.sh reads, the SKILL.md step 1 and the `cannot be read` job line. The earlier rows that are unaffected pass, and so does the unchanged `does-not-exist-yet` row. `make lint` is green. The test runner had no module it could not import, because everything under test is a shell script or a text file.

   Criterion → test:
   - criterion 1: tests/test_operator_site_example.py::test_each_comment_says_whether_its_key_is_required_and_otherwise_names_a_default (one row per key of the example; `site_job_keys` is read by sourcing `operator/lib/site.sh`)
   - criterion 2: tests/test_operator_site_example.py::test_the_named_size_defaults_are_those_the_job_takes_without_the_key (rows cpu, memory, timeout, idle-minutes; `job.sh create --dry-run` on the example's values with the key left out)
   - criterion 3: tests/test_operator_site_example.py::test_the_named_price_default_is_the_price_the_provider_file_holds_without_the_key (rows input, output; read back through `provider_text` and `read_provider`)
   - criterion 4: tests/test_operator_site_example.py::test_the_sanitise_rules_default_is_the_file_beside_the_site_file
   - criterion 5: tests/test_operator_site_example.py::test_show_on_a_copy_of_the_example_says_set_for_every_key_in_order
   - criterion 6: tests/test_operator_site.py::test_a_malformed_command_prints_the_usage_and_exits_2 (only the `USAGE` constant changed, with the leave in feature.md) and the unchanged tests/test_operator_site_check.py::test_an_argument_after_check_prints_the_usage
   - criterion 7: tests/test_operator_texts.py::test_the_first_step_names_the_site_file_and_the_rest_is_unchanged (`AFTER_FIRST_STEP` is today's text from step 2 through *The loop*)
   - criterion 8: tests/test_operator_python_isolation.py::test_a_json_module_in_the_working_folder_is_never_imported (rows settings-show, settings-init, status, comment, site-check, job-create-dry-run; stdout is compared with the folder path written as `<root>`)
   - criterion 9: tests/test_operator_python_isolation.py::test_every_python_start_passes_isolated_mode_first (one row per file of the Interface; it counts `python3` as a command at the start of a line or after `|`, `(`, `$(`, `;` or `&&`)
   - criterion 10: tests/test_operator_skill_scripts.py::test_status_stops_at_a_failing_read_with_the_hosting_message (rows issue, comments-page, commits); the existing status.sh rows stay as they were
   - criterion 11: tests/test_operator_site_check.py::test_the_job_check_tells_whether_the_job_exists_and_never_fails (rows exists, does-not-exist-yet, cannot-be-read; each also checks that the last line is `site: ready` and the exit is 0)
   - criterion 12: tests/test_operator_site.py::test_a_space_beside_the_equals_sign_is_a_fault_and_one_inside_the_value_is_kept (rows space-before, space-after, tab-after, no-space, space-inside-the-value)
   - criterion 13: tests/test_operator_job.py::test_the_sizes_and_the_idle_minutes_have_defaults_the_site_overrides (the `defaults` row is now 4/16Gi/86400/30)
   - criteria 14 and 15: no test (they belong to `make check` and the docs stage)

   Files created: tests/test_operator_site_example.py, tests/test_operator_texts.py, tests/test_operator_python_isolation.py, tests/site_check_support.py.

   Earlier test files I changed:
   - **Moves under the standing leave** (every earlier test keeps its name and what it checks):
     - tests/test_operator_site_check.py: its machine, stand-ins, constants and line helpers moved to tests/site_check_support.py. The `system` fixture now calls `link_system`.
     - tests/test_operator_job.py: `GCLOUD_STAND_IN`, `TAG`, `INSTANCE`, `JOB_ROOT`, `WRAPPER`, `START`, `START_SCRIPT`, `RunJob`, `wrapper_of` and `provider_text` moved to tests/operator_job_support.py. The bodies of the `repository` and `run_job` fixtures moved there as `make_job_repository` and `job_runner`, and the fixtures call them.
     - tests/test_operator_site.py: `INTERFACE_KEYS` moved to tests/operator_support.py.
   - **Additions to shared helpers:**
     - The curl stand-in in tests/operator_support.py answers a route listed in `STAND_IN_CURL_FAILURES` with that status and body.
     - `Operator.fail` in tests/operator_skill_support.py writes that file.
     - The gcloud stand-in of `site check` writes `Setup.describe_error` to standard error on a describe.
   - **Changes by the work item:**
     - tests/test_operator_job.py, criterion 13 (the human's leave): the defaults of `job_flags` and `env_list` and the `defaults` row are now 4/16Gi/86400/30. The `overrides` row now uses 8/32Gi, because 4/16Gi are the defaults now and the row would no longer show an override.
     - tests/test_operator_site.py, criterion 12 (decision 21): `test_a_space_before_the_equals_sign_is_a_fault_and_one_after_it_is_the_value` had a row `SITE_A= 1` accepted, which decision 21 reverses. It is replaced by the criterion 12 test above, which keeps the space-before row. This renames an earlier test; I read the Interface's "new rows in the tests of the loader" as covering it.
     - tests/test_operator_site_check.py, criterion 11: in the job-check test, the `does-not-exist-yet` row's stand-in now prints a not-found error, and a `cannot-be-read` row was added.

   Open for the coder:
   - In the not-found row, the gcloud stand-in prints `ERROR: (gcloud.run.jobs.describe) Cannot find job [factory-job].`, which is what I recall `gcloud run jobs describe` printing for a missing job; I could not check it against gcloud here. The permission row prints `ERROR: (gcloud.run.jobs.describe) PERMISSION_DENIED: ...` followed by a second line.
   - The failing status.sh read answers `500` with `{"message": "Server Error"}`, so the test expects `hosting: GET /repos/owner/repo/<path>: 500 Server Error` as the last line on standard error.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: I made the tester's failing tests pass without changing any test. `make check` is green: lint, types, layers, sast, secrets, licenses and test (83 s).

   What I built, by part:
   - A: In `operator/site.env.example` I replaced the 15 comment lines with the Interface's text word for word. No `SITE_*=value` line changed. In `operator/job/job.sh` the defaults are now `--cpu=4`, `--memory=16Gi`, `--task-timeout=86400` and `FACTORY_IDLE_SHUTDOWN_MINUTES=30`.
   - B: `operator/bin/site` has the usage line `usage: site path | init | show | get SITE_X | check`. In `operator/skill/kumpel/SKILL.md`, step 1 of *Before anything* now says:
     - the repository and the checkout come from the site file first (`SITE_REPOSITORY`, `SITE_CHECKOUT`);
     - when the site file gives both, the agent runs `settings.sh init` with no arguments;
     - otherwise it asks the human for the two values and suggests putting them into the site file.
     No other line of `SKILL.md` changed. `operator/README.md` is left to the docs stage (criterion 15).
   - D: `check_job` in `operator/bin/site` now captures gcloud's standard error. A message that contains `Cannot find job` or `NOT_FOUND` gives `does not exist yet` (helper `is_not_found`). Any other failure gives `cannot be read: <first line>`, through the existing `first_line`. The line always passes.
   - E: `_site_parse_line` in `operator/lib/site.sh` treats a space or tab directly after `=` as a fault. The message is the same as for a space before `=`: `not a KEY=value line` with the line number.
   - C: Every `python3 -c` and `python3 -` in these scripts now starts `python3 -I`: `operator/bin/site`, `operator/job/job.sh` and `operator/skill/kumpel/scripts/{status,settings,approval,comment,merge,reset-to-tag}.sh`. In `status.sh`, the issue read, the comments-page read and the commits read are each assigned to a variable first, followed by `|| exit 1`. The call `comment=$(newest_comment …)` also has `|| exit 1`, so a failure inside the command substitution stops the whole script. A failing read therefore ends with the hosting client's message and no traceback. The pull-request list read is unchanged.

   Main choice: for D, I tell a missing job from an unreadable one by matching gcloud's error text. The rejected alternative was a second gcloud call, for example `jobs list --filter`, to look for the job by name. That costs another call, and a rights problem would make it fail in the same way. I also accept `NOT_FOUND`, besides the stand-in's `Cannot find job`, because an API-level 404 reads that way. The tester could not confirm gcloud's real wording for a missing job, and neither could I. If the real text differs, a missing job would show as `cannot be read: …`. The line would still pass and the check's result would not change.

   Refactor pass: I read the diff and found nothing to change. The loader computes `${_site_line#*=}` twice, once for the new check and once for the value; I left that as it is, since it is a one-line expansion.

   Journal: no entry changed the meaning of the task, so I did not rewrite the Description.

   Noticed, not touched:
   - `merge.sh` and `reset-to-tag.sh` already used `-I` in some places; I only added it where it was missing.
   - The docs criterion (15) remains for the documenter: the `operator/README.md` sections, the guide's key table and *The `site` command*, and the `docs/decisions.md` entry about `-I`.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 42 known, 0 gone
8. factory: started review as vm.
9. reviewer: I reviewed `git diff main...HEAD -- . ':!factory'` against the work item. The operator scripts do what the Interface says for parts A to E: the comments match it word for word, the job defaults are 4, 16Gi, 86400 and 30, the usage line includes `check`, every `python3` start in the eight files has `-I` first, `status.sh` assigns its three reads before parsing them and exits 1, and the loader refuses a blank after `=`. Every criterion from 1 to 13 has a test that checks what the criterion says. The trailing-space side of part E is covered by the existing `trailing-spaces` row. The coder's journal reports `make check` green.

   1. criterion 14 added: it needs its test. `operator/bin/site:310-315` (`is_not_found`, the `*NOT_FOUND*` alternative) and `operator/bin/site:306` (the fallback `gcloud run jobs describe failed` when the error is empty) are behaviours no criterion named, and no row of `tests/test_operator_site_check.py::test_the_job_check_tells_whether_the_job_exists_and_never_fails` covers them. The fix is two rows in that test, as criterion 14 now says. The closing criteria were renumbered to 15 and 16, and the Interface's reference to the docs criterion now reads "criterion 16".
   2. `tests/test_operator_python_isolation.py:60-62` (`job_dry_run`) is a second copy of `example_values` in `tests/test_operator_site_example.py:41-45`: the same parsing of the example's `SITE_*=value` lines into a dict. The fix is to move `example_values` to `tests/operator_support.py` beside `example_keys` and use it from both modules.
   3. In `tests/operator_support.py`, `CURL_STAND_IN`'s new `STAND_IN_CURL_FAILURES` block repeats the two lines of the routes block just above it: `url = next(... name == "url" ...)` and `route = re.sub(r"^[a-z]+://[^/]*", "", url)`. The fix is to compute `url` and `route` once, before both blocks.
   4. `tests/test_operator_job.py`: the `overrides` row of `test_the_sizes_and_the_idle_minutes_have_defaults_the_site_overrides` was changed from 4/16Gi to 8/32Gi. The leave in `feature.md` (*The human's changes*, S0014) covers only the rows that pin the job's defaults and says "Nothing else in those modules". The change keeps the row meaningful, but it needs the human's leave. The fix is for the next stage to ask the human to confirm it (`question`), or to put the row back.
   5. `tests/test_operator_site.py`: `test_a_space_before_the_equals_sign_is_a_fault_and_one_after_it_is_the_value` was renamed to `test_a_space_beside_the_equals_sign_is_a_fault_and_one_inside_the_value_is_kept`. The leave covers the rows that pin a space after `=`, not the test's name. The old name is false once part E lands, so a rename is reasonable, but it needs the human's word. The fix is to ask the human to confirm the rename in the same question as finding 4. Changing the `space-before-equals` row to `SITE_PROXY =http://p` follows criterion 12's own words, so that part is covered.

   Earlier test files the diff changes:
   - tests/operator_job_support.py: the standing leave to move a shared test helper (`GCLOUD_STAND_IN`, `TAG`, `INSTANCE`, `JOB_ROOT`, `WRAPPER`, `START`, `START_SCRIPT`, `RunJob`, `wrapper_of`, `provider_text` and the fixture bodies moved from `tests/test_operator_job.py`).
   - tests/operator_skill_support.py: none needed (it adds `Operator.fail` and one environment variable; every earlier use is as it was).
   - tests/operator_support.py: the standing leave (`INTERFACE_KEYS` moved from `tests/test_operator_site.py`). The added `STAND_IN_CURL_FAILURES` route needs no leave, since it only adds; its duplication is finding 3.
   - tests/test_operator_job.py: the standing leave for the moves, and the human's leave in `feature.md` for the `defaults` row and the `job_flags`/`env_list` defaults. The `overrides` row goes beyond both (finding 4).
   - tests/test_operator_site.py: the human's leave in `feature.md` for `USAGE` and the space-after row, criterion 12 for the new rows, and the standing leave for `INTERFACE_KEYS`. The rename goes beyond them (finding 5).
   - tests/test_operator_site_check.py: the standing leave (the machine, stand-ins, constants and line helpers moved unchanged to `tests/site_check_support.py`, apart from the added `describe_error`), and the human's leave in `feature.md` for the `job`-line rows.
   - tests/test_operator_skill_scripts.py: none needed (it only adds `test_status_stops_at_a_failing_read_with_the_hosting_message`).
10. factory: started doing as vm.
11. coder: Round 1: all five of the reviewer's findings are changes to tests. None of them needs a code change, so I changed no code. The code for criterion 14 is already in place: `is_not_found` in `operator/bin/site` matches `NOT_FOUND`, and when gcloud's standard error is empty the check falls back to `gcloud run jobs describe failed`. Only the tests for it are missing.

    Findings 1 to 3 can go to the tester as they are:
    - **1:** criterion 14 needs two new rows in `tests/test_operator_site_check.py::test_the_job_check_tells_whether_the_job_exists_and_never_fails`.
    - **2:** move `example_values` to `tests/operator_support.py` under the standing leave, and use it from `tests/test_operator_site_example.py` and `tests/test_operator_python_isolation.py`.
    - **3:** in `tests/operator_support.py`, compute `CURL_STAND_IN`'s `url` and `route` once.

    Findings 4 and 5 go beyond the leave in `feature.md`. Only you can approve them, so I am asking before I send anything to the tests stage. That way the tester gets every change in one round.

    **Question.** Do you approve these two test changes that the tester made?

    - **(4)** In `tests/test_operator_job.py`, the `overrides` row of `test_the_sizes_and_the_idle_minutes_have_defaults_the_site_overrides` changed from 4/16Gi to 8/32Gi. The new defaults are 4/16Gi. If the row stays at 4/16Gi, it can no longer tell an override from the default.
    - **(5)** In `tests/test_operator_site.py`, `test_a_space_before_the_equals_sign_is_a_fault_and_one_after_it_is_the_value` was renamed to `test_a_space_beside_the_equals_sign_is_a_fault_and_one_inside_the_value_is_kept`. Part E makes the old name false.

    Options:
    - **(a)** Approve both. The test changes for findings 1 to 3 then go to the tests stage, and 4 and 5 stay as they are.
    - **(b)** Undo one or both. The tester reverts the row to 4/16Gi, or puts back the old name, or both.
    - **(c)** Approve one and undo the other.

    I would choose **(a)**. Reverting 4 would leave a row that no longer tests an override. Reverting 5 would leave a test name that says the opposite of the behaviour.

    Noticed, not touched: nothing beyond the reviewer's findings. The Description is unchanged, because no journal entry changed the meaning of the task.
12. 2026-11-03 human: (a). Both changes are approved after the fact, as the leave meant them:
    - (4) the `overrides` row of `test_the_sizes_and_the_idle_minutes_have_defaults_the_site_overrides` at 8/32Gi, so that it still tells an override from the new 4/16Gi default;
    - (5) the rename to `test_a_space_beside_the_equals_sign_is_a_fault_and_one_inside_the_value_is_kept`, because part E makes the old name false.

    Findings 1 to 3 go to the tests stage as you listed them. The tester's entry names every earlier test file it changes.

    — Kumpel, for the human who owns this project
    <!-- kumpel -->
13. factory: started doing as vm.
14. coder: Round 1, after the human's answer (entry 12). The human chose (a): the `overrides` row at 8/32Gi in `tests/test_operator_job.py` and the rename of `test_a_space_beside_the_equals_sign_is_a_fault_and_one_inside_the_value_is_kept` in `tests/test_operator_site.py` are approved and stay. That settles findings 4 and 5.

    The three test changes left for the tester (the reviewer's findings 1 to 3):
    - **1 (criterion 14):** add two rows to `tests/test_operator_site_check.py::test_the_job_check_tells_whether_the_job_exists_and_never_fails`. In the first, the describe's error line contains `NOT_FOUND` (and not `Cannot find job`), and the check prints `job: <name> does not exist yet`. In the second, the describe fails with an empty standard error, and the check prints `job: <name> cannot be read: gcloud run jobs describe failed`. In both rows the check's result stays as it was.
    - **2:** move `example_values` from `tests/test_operator_site_example.py` to `tests/operator_support.py`, beside `example_keys`. Use it from `tests/test_operator_site_example.py`, and in place of the copy in `tests/test_operator_python_isolation.py` (`job_dry_run`). This falls under the standing leave.
    - **3:** in `tests/operator_support.py`, `CURL_STAND_IN` should compute `url` and `route` once, before the routes block and the `STAND_IN_CURL_FAILURES` block, instead of once in each.

    I changed no code, because none of the three needs it. The code criterion 14 tests is already in `operator/bin/site`: the `NOT_FOUND` match in `is_not_found`, and the `gcloud run jobs describe failed` text used when gcloud's error is empty. I did not run `make check`, because the working tree has no change from this stage.

    The Description is unchanged: the human's answer approves two test changes and does not change what the task means.

    Noticed, not touched: nothing new.
15. factory: started tests as vm.
16. tester: Mode: a test change the human approved (entry 12). I made the three test changes from the coder's entry 14 (the reviewer's findings 1 to 3) and nothing else. Findings 4 and 5 are approved and stay as they were.

    - **Finding 1, criterion 14:** criterion 14 → `tests/test_operator_site_check.py::test_the_job_check_tells_whether_the_job_exists_and_never_fails`. I added two rows to it:
      - `api-not-found`: the describe exits 1 with an error line containing `NOT_FOUND` and not `Cannot find job` (new constant `API_NOT_FOUND`). It expects `ok job: <name> does not exist yet`.
      - `no-error-text`: the describe exits 1 with nothing on standard error. It expects `ok job: <name> cannot be read: gcloud run jobs describe failed`.
      
      Both rows keep the test's existing checks: the result is still `site: ready`, the exit status is 0, and there is one describe call. The `ok ` prefix is how `site check` already prints the job line in the existing rows.
    - **Finding 2, standing leave to move a shared test helper:** I moved `example_values` from `tests/test_operator_site_example.py` to `tests/operator_support.py`, beside `example_keys`. `tests/test_operator_site_example.py` now imports it. In `tests/test_operator_python_isolation.py`, `job_dry_run` uses it in place of its own copy of the parsing, and the import of `SITE_EXAMPLE` there, now unused, is gone.
    - **Finding 3:** in `tests/operator_support.py`, `CURL_STAND_IN` now computes `url` and `route` once, before the routes block. Both the routes block and the `STAND_IN_CURL_FAILURES` block use them.

    Earlier test files I changed:
    - `tests/operator_support.py` (the leave for finding 2, and finding 3)
    - `tests/test_operator_site_example.py` (the leave)
    - `tests/test_operator_python_isolation.py` (the leave)
    - `tests/test_operator_site_check.py` (the rows for criterion 14)

    Every earlier test keeps its name and checks the same thing. I created no new files.

    `make lint` is green. The one run of the touched modules (`uv run pytest -q tests/test_operator_site_check.py tests/test_operator_site_example.py tests/test_operator_python_isolation.py tests/test_operator_skill_scripts.py`) passed, including both new rows: the code criterion 14 tests is already in `operator/bin/site`. The test run could import every module. I did not run the type check, as the stage says.

    `lint`: lint: green (0.1 s)
17. factory: started doing as vm.
18. coder: Round 1, after the tester's entry 16. The reviewer's five findings are all settled. The human approved findings 4 and 5 in entry 12. The tester made findings 1 to 3 in tests: the two criterion 14 rows `api-not-found` and `no-error-text` in `tests/test_operator_site_check.py`, `example_values` moved to `tests/operator_support.py`, and `url`/`route` computed once in `CURL_STAND_IN`. None of these needs a code change. The behaviour criterion 14 tests was already in `operator/bin/site`: the `*NOT_FOUND*` match in `is_not_found`, and the `gcloud run jobs describe failed` fallback when gcloud's standard error is empty. So this stage changed no file, and the working tree is clean.

    What I built is unchanged from entry 7 (`operator/site.env.example`, `operator/job/job.sh`, `operator/bin/site`, `operator/lib/site.sh`, `operator/skill/kumpel/SKILL.md`, `operator/skill/kumpel/scripts/{status,settings,approval,comment,merge,reset-to-tag}.sh`), and so is its main choice. To tell a missing job from one it cannot read, the check matches gcloud's error text; I rejected a second gcloud call (`jobs list --filter`).

    Refactor pass: this round has no diff of its own, so there is nothing to change.

    `make check` is green with the new rows (test: green, 83.2 s; check: green).

    The Description is unchanged. The journal approved two test changes and added test rows, and neither changes what the task means.

    Noticed, not touched: as in entry 7, gcloud's real wording for a missing job was never checked against gcloud itself. If it matches neither `Cannot find job` nor `NOT_FOUND`, a missing job prints `cannot be read: …`. The line still passes and the check's result stays the same. The docs criterion 16 is still open for the documenter.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
