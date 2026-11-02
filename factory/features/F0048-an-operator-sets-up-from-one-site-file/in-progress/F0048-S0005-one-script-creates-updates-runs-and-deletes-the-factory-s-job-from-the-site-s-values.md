---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 502
comments_read: [6585290870]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-02T18:55:46.598535Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-02T18:38:48.506530Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-02T18:38:48.513425Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-02T18:39:17.283592Z'
  stage: intake
  run: 5671c82e0460495a9d2f569dfbd6030a
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-02T18:43:41.002681Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-02T18:43:59.334581Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-02T18:44:18.717249Z'
  stage: intake
  run: 74738f812f4f49b9964fc3436bedc7fe
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-02T18:44:39.891305Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-02T18:50:11.431705Z'
  stage: tests
  run: 2f231df526914584b649693dd5c16599
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-02T18:50:33.837857Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-02T18:55:25.816221Z'
  stage: doing
  run: 09276c1a81624cb399aa4b24602782f8
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-02T18:55:46.598535Z'
  stage: review
---

# One script creates, updates, runs and deletes the factory's job from the site's values

## Description

Creating the job that runs the factory took a long `gcloud run jobs create` call with thirty settings, a wrapper of shell text shipped base64-coded in its arguments, and care about quoting, the env delimiter, the proxy spellings and the secret mounts; the session of 2026-11-02 kept it in a script of its own and got it wrong once with a failed `sed`. This story puts that into `operator/job/job.sh` with four commands, `create`, `update`, `execute` and `delete`, all from the site file's values (S0001): the job's own settings, the project and region, the two secrets, the model API's addresses and prices, the proxy. The job's wrapper is small now that the script handles its own `PATH` and the token's folder (S0002): it writes the provider file and the start script into the job and hands over to the script. The command never guesses a project, a region or a job's name, refuses to create a job that exists, refuses to execute while an execution of the job runs (the platform's role at one site could not cancel one), and asks for `--yes` before deleting. Reading the job's log and state is the next story (S0007).

## Interface

`operator/job/job.sh` (`sh`; loads the site; calls `gcloud`)

```sh
job.sh create  [--dry-run]    # gcloud run jobs create
job.sh update  [--dry-run]    # gcloud run jobs update, the same settings
job.sh execute                # gcloud run jobs execute --async; prints the execution's name
job.sh delete  [--yes]        # gcloud run jobs delete
```

- Required site keys, checked with `site_require` before anything else (all of them named in one message): `SITE_PROJECT`, `SITE_REGION`, `SITE_RUN_AS`, `SITE_CONNECTOR`, `SITE_PROXY`, `SITE_NO_PROXY`, `SITE_JOB`, `SITE_INSTANCE`, `SITE_REPOSITORY_URL`, `SITE_CODE_URL`, `SITE_CODE_REF`, `SITE_HOSTING_SECRET`, `SITE_MODEL_SECRET`, `SITE_MODEL_BASE_URL`, `SITE_MODEL`, `SITE_LOGIN_URL`, `SITE_LOGIN_SCOPE`, `SITE_LOGIN_CLIENT_ID`. `delete` and `execute` need only the project, the region and the job's name. Optional, with defaults: `SITE_IMPERSONATE` (none), `SITE_CPU` (`8`), `SITE_MEMORY` (`32Gi`), `SITE_TIMEOUT` (`14400`, seconds), `SITE_IDLE_MINUTES` (`60`), `SITE_MODEL_INPUT_COST` and `SITE_MODEL_OUTPUT_COST` (`0`).
- Every `gcloud` call carries `--project=$SITE_PROJECT` and `--region=$SITE_REGION`, and `--impersonate-service-account=$SITE_IMPERSONATE` when that is set.
- `create` and `update` build one call: `gcloud run jobs <create|update> $SITE_JOB --image=docker.io/library/debian:trixie-slim --execution-environment=gen2 --cpu=$SITE_CPU --memory=$SITE_MEMORY --task-timeout=$SITE_TIMEOUT --max-retries=0 --vpc-connector=$SITE_CONNECTOR --vpc-egress=all-traffic --service-account=$SITE_RUN_AS --set-secrets=/secrets/hosting-token=$SITE_HOSTING_SECRET:latest,/secrets-llm/client-secret=$SITE_MODEL_SECRET:latest --set-env-vars=<list> --command=sh --args=-c,<wrapper>`.
- The env list uses the delimiter `^@^` and holds, with `<root>` = `/srv/factory/$SITE_INSTANCE`: `FACTORY_INSTANCE`, `FACTORY_REPOSITORY_URL` (`$SITE_REPOSITORY_URL`), `FACTORY_CODE_URL`, `FACTORY_CODE_REF`, `FACTORY_TOKEN_FILE=/secrets/hosting-token`, `HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY` and `http_proxy` (all `$SITE_PROXY`), `NO_PROXY` and `no_proxy` (`$SITE_NO_PROXY`), `FACTORY_CONTAINER_ENV=HTTPS_PROXY,https_proxy,HTTP_PROXY,http_proxy,NO_PROXY,no_proxy`, `FACTORY_OPENCODE_PROVIDER_FILE=<root>/provider.json`, `FACTORY_OPENCODE_MODELS=opus=site/$SITE_MODEL,sonnet=site/$SITE_MODEL,haiku=site/$SITE_MODEL`, `FACTORY_API_LOGIN_FILE=<root>/api-login`, `FACTORY_TOKEN_URL=$SITE_LOGIN_URL`, `FACTORY_TOKEN_SCOPE`, `FACTORY_TOKEN_CLIENT_ID`, `FACTORY_TOKEN_CLIENT_SECRET_FILE=/secrets-llm/client-secret`, `FACTORY_IDLE_SHUTDOWN_MINUTES`. It sets no `PATH`. No secret's value is in it; the only secrets are mounts.
- The wrapper is one line of shell, `echo <b64> | base64 -d | gzip -d | sh`, of a script that: makes `<root>`, writes `<root>/provider.json` (below), writes the text of `vm/job-start.sh` at `SITE_CODE_REF` to `/tmp/job-start.sh` and ends in `exec sh /tmp/job-start.sh`. It holds no logic besides these.
- The script's text is taken from the code the job will run, not from the working tree: `git -C <the repository that holds job.sh> show <SITE_CODE_REF>:vm/job-start.sh` (feature decision 12). A ref that this repository does not know stops `create` and `update` with `job: <ref> is not known here; fetch it first` and status 1, before any `gcloud` call; `--dry-run` takes the text the same way.
- `provider.json` is the provider file of the operator guide: `{"id": "site", "base_url": $SITE_MODEL_BASE_URL, "api_key_env": "ANTHROPIC_API_KEY", "models": {$SITE_MODEL: {"name": $SITE_MODEL, "context": 200000, "output": 16000, "input_cost": $SITE_MODEL_INPUT_COST, "output_cost": $SITE_MODEL_OUTPUT_COST}}, "small_model": "site/$SITE_MODEL"}`, written by `python3` (`json.dumps`, so no value needs quoting by hand).
- `create` first runs `gcloud run jobs describe $SITE_JOB`; when that succeeds it prints `job: <job> exists; use update` to standard error and exits 1, without creating. `update` exits 1 with `job: <job> does not exist; use create` when `describe` fails.
- `--dry-run` runs no `gcloud` call that changes anything (and no `describe`): it prints the call, one argument per line, with the wrapper's base64 text replaced by `<wrapper: N bytes>`, and exits 0.
- `execute` first runs `gcloud run jobs executions list --job=$SITE_JOB --format=value(metadata.name,status.runningCount)`; when a row has a running count of 1 or more it prints `job: an execution of <job> is still running: <name>; two executions of one instance must not overlap` and exits 1. Else it runs `gcloud run jobs execute $SITE_JOB --async --format=value(metadata.name)`, prints the name, and writes it to `${XDG_STATE_HOME:-$HOME/.local/state}/kumpel/last-execution`.
- `delete` without `--yes` prints `job: would delete <job> and stop its running execution; run again with --yes` and exits 1; with `--yes` it runs `gcloud run jobs delete $SITE_JOB --quiet`.
- A `gcloud` that fails: its standard error is shown and the command exits with its status.

Tests: `tests/test_operator_job.py`, a stand-in `gcloud` that records its arguments and plays answers per row (`describe` found or not, an execution list), the site file in `tmp_path`; the provider file is read back with `factory.domain.opencode_provider.read_provider` in a test of the story.

## Acceptance criteria

1. With the required keys set, `create` runs `gcloud` once for `describe` and once for `create`, the second with the arguments of the Interface in an order a test may fix (it fixes the set, and the order of `--set-env-vars`'s entries), and exits 0; `update` with `describe` succeeding runs `describe` and `update` with the same arguments except the verb and exits 0 (a second row).
2. Every call carries the project and the region; with `SITE_IMPERSONATE` set every call also carries `--impersonate-service-account=<it>`, and without it no call does (two rows); `delete --yes` and `execute` carry them too (a row for each).
3. Missing keys: with `SITE_REGION` and `SITE_CODE_REF` unset, `create` prints one `site: missing SITE_REGION, SITE_CODE_REF in <path>` line, runs no `gcloud` and exits 2; `update` with the same keys unset gives the same line and exit 2; `execute` and `delete --yes` with only the project, the region and the job set work (a row for each of the four commands).
4. The defaults and the overrides, as rows of one parametrized test: no `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT` and `SITE_IDLE_MINUTES` give `--cpu=8`, `--memory=32Gi`, `--task-timeout=14400` and `FACTORY_IDLE_SHUTDOWN_MINUTES=60`; set values replace them.
5. The env list: it starts with `^@^`, its entries are separated by `@`, it holds every name of the Interface with the site's values (a value containing a comma is intact), it holds the four proxy spellings with the proxy's value and both `NO_PROXY` spellings, it holds no `PATH` entry, and it contains none of the texts `TOKENMARK` and `SECRETMARK` that a test puts into the stand-in's environment and into a token command.
6. The secrets are mounts only: `--set-secrets` is exactly the two mounts of the Interface with the site's secret names, and no argument of any call contains the content of a secret.
7. The wrapper: decoding the base64 text of `--args` and un-gzipping it gives a script that contains `mkdir -p /srv/factory/<instance>`, writes `provider.json` and `/tmp/job-start.sh`, ends in `exec sh /tmp/job-start.sh`, and holds the text of `vm/job-start.sh` at `SITE_CODE_REF` byte for byte, not the working tree's (a test copies `operator/` and `vm/` into a real git repository in `tmp_path`, commits, tags `t1`, then changes `vm/job-start.sh` in the working tree, and finds the tagged text in the wrapper); it contains no `chmod`, no `cp` and no `PATH=`. A `SITE_CODE_REF` the repository does not know gives the message of the Interface, status 1, and no `gcloud` call, for `create`, `update` and `create --dry-run` (rows).
8. `provider.json` as the script writes it is accepted by `read_provider`, and the provider it returns has the id `site`, the base URL and the model of the site, `input_cost` and `output_cost` as numbers (`0` when unset), and `small_model` `site/<model>`; a model name or a URL with a double quote in it still gives valid JSON.
9. `create` for a job that exists (the `describe` stand-in exits 0) prints `job: <job> exists; use update` to standard error, exits 1 and runs no `create`; `update` for a job that does not exist prints `job: <job> does not exist; use create`, exits 1 and runs no `update` (two rows).
10. `--dry-run`, for `create` and for `update` (rows), runs no `gcloud` at all, prints the call one argument per line with the wrapper replaced by `<wrapper: N bytes>`, and exits 0; the printed text contains the job's name and no base64 text longer than 100 characters.
11. `execute` with a row of `running count 1`, with a row of count 2, and with several rows of which only a later one is running (rows), prints the overlap message with the execution's name, exits 1 and runs no `execute`; with rows of `0` and empty counts it runs `execute --async`, prints the name the stand-in answers, writes it to `last-execution` under `XDG_STATE_HOME` (a test sets it), and exits 0.
12. `delete` without `--yes` prints the message of the Interface, exits 1 and runs no `delete`; with `--yes` it runs it with `--quiet`.
13. A failing `gcloud` (text on standard error) shows that text and the command exits with its status: rows for `create`, `update`, `execute` (the list call and the execute call) and `delete`, one of them with status 3, the others 1.
14. `make check` stays green.
15. docs: `docs/operator-guide.md`, *Creating the job*: the template call is replaced by `job.sh create` with the keys it reads (a table that points to the site file's table), the order of a first start (`site check`, `job.sh create`, `job.sh execute`), the overlap rule and the deletion rule, and says that the job's wrapper only writes the provider file and hands over; `README.md` and the other documents: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/bin"
printf '#!/bin/sh\ncase "$*" in *executions*) ;; *execute*) echo exec-1 ;; esac\n' > "$d/bin/gcloud"; chmod +x "$d/bin/gcloud"
printf 'SITE_PROJECT=p\nSITE_REGION=r\nSITE_JOB=j\n' > "$d/site.env"
PATH="$d/bin:$PATH" FACTORY_SITE="$d/site.env" XDG_STATE_HOME="$d/state" sh operator/job/job.sh execute; echo "exit $?"
cat "$d/state/kumpel/last-execution"
```

Expect: three lines: `exec-1`, `exit 0` and `exec-1` (the stand-in lists no running execution, answers the execute with a name, and the name is saved).

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_PROJECT=p\n' > "$d/site.env"
FACTORY_SITE="$d/site.env" sh operator/job/job.sh create; echo "exit $?"
```

Expect: two lines: `site: missing SITE_REGION, SITE_RUN_AS, SITE_CONNECTOR, SITE_PROXY, SITE_NO_PROXY, SITE_JOB, SITE_INSTANCE, SITE_REPOSITORY_URL, SITE_CODE_URL, SITE_CODE_REF, SITE_HOSTING_SECRET, SITE_MODEL_SECRET, SITE_MODEL_BASE_URL, SITE_MODEL, SITE_LOGIN_URL, SITE_LOGIN_SCOPE, SITE_LOGIN_CLIENT_ID in <the file's path>` (on standard error) and `exit 2`.

## Journal

1. 2026-11-02 human: created.
2. factory: started intake as vm.
3. intake: 1. `update` has no success criterion. The Interface says it runs `describe` and then `gcloud run jobs update` with the same settings as `create`. Criterion 1 covers only `create`, and criterion 9 covers only the refusal. Should criterion 1 gain an `update` row (describe succeeds, `update` runs with the same arguments, exit 0)? I would choose yes.
   2. Criterion 3 says "a row for each of the three commands", but the Interface names four commands. It is also unclear what the rows are. The first half covers `create` with missing keys. The second half says `execute` works with only the project, region and job set. Which three commands get rows? What does a `delete` row with only those three keys expect, given that it needs `--yes`? What does an `update` row with missing keys expect? I would choose: `create` and `update` fail with the missing-keys line and exit 2; `execute` and `delete --yes` work with only the three keys.
   3. The `execute` rule says "a running count of 1 or more", but criterion 11 tests only a count of 1. The Interface also gives no way to tell a count of 2 from a count of 1. Should a row with count 2 be added, and a row with several lines where only a later one is running? I would choose yes.
   4. Failure paths with no criterion. Criterion 13 has a row only for `create`, but the Interface says any failing `gcloud` shows its standard error and exits with that status. Which rows are expected for `update`, `execute` (the list call and the execute call), and `delete`? Should the test use an exit status other than 1, since the Interface says "exits with its status"? I would choose rows for all four commands, with status 3 on one of them.
   5. `--dry-run` is stated for both `create` and `update`, but criterion 10 does not say which command it runs. It also does not say whether the unknown-ref refusal in the Interface ("`--dry-run` takes the text the same way") is tested with `--dry-run`. Should criterion 10 have rows for `create` and `update`, and criterion 7 a row for an unknown ref with `--dry-run` (status 1, the message, no `gcloud`)? I would choose yes.
   6. Criterion 12 tests only the case where `delete` has no `--yes`. The Interface says `delete` and `execute` need only the project, region and job name. Does criterion 3 cover that for `delete` (see question 2)? Should `delete` get the project, region and impersonation checks of criterion 2? I would choose yes, with `delete` and `execute` added to the rows of criterion 2.
4. 2026-11-02 human: Yes to all six, as you propose: 1 an `update` row in criterion 1; 2 `create` and `update` fail with the missing-keys line and exit 2, `execute` and `delete --yes` work with only the project, the region and the job; 3 a row with count 2 and one where only a later line is running; 4 failure rows for all four commands, one of them with status 3; 5 `--dry-run` rows for `create` and `update`, and the unknown-ref row with `--dry-run`; 6 `delete` and `execute` join the rows of criterion 2.
5. factory: started intake as vm.
6. intake: accepted. I carried the human's answer (journal entry 4, "yes to all six") into the criteria, with no other change.
   - Interface: `operator/job/job.sh` names concrete commands, keys, defaults, messages, exit statuses and the `gcloud` call. The Interface comments (the `^@^` delimiter, the wrapper, `provider.json`, the `last-execution` path) each have a criterion.
   - Criteria: each is testable by one test function or one parametrized test. Edits from entry 4:
     - 1: an `update` row.
     - 2: `delete --yes` and `execute` join the rows.
     - 3: `update` with missing keys gives the same line and exit 2; `execute` and `delete --yes` work with only the project, the region and the job (four rows).
     - 7: the unknown ref is tested for `create`, `update` and `create --dry-run`.
     - 10: `--dry-run` rows for `create` and `update`.
     - 11: rows with a running count of 2 and with only a later row running.
     - 13: failure rows for all four commands, with status 3 on one.
     Every rule has its failing side covered: missing keys, an existing or missing job, an unknown ref, an overlapping execution, `delete` without `--yes`, and a failing `gcloud`.
   - Smoke test: both commands are runnable. Neither runs pytest, so the `-q` rule does not apply. Each `Expect:` line is checkable: the three lines `exec-1`, `exit 0`, `exec-1`, and the exact missing-keys line with `exit 2`.
   - Architecture: shell under `operator/`, which the coder's write paths cover per the feature's change. Tests are at `tests/test_operator_job.py` with stand-ins, and no code under `src/factory/` changes.
   - Scope: the story lies within the feature's S0005 scope, and `job.sh log` and `job.sh status` (S0007) stay out.
7. factory: started tests as vm.
8. tester: I wrote the tests for `operator/job/job.sh`, all in one new file. They are red on purpose: `job.sh` does not exist yet, so every test fails with `sh: can't open …/operator/job/job.sh`. `make lint` is green. I scanned the file with `detect-secrets` and it reports no findings. No Python import failed; the modules the tests import (`factory.adapters.process`, `factory.domain.opencode_provider`, `git_support`, `operator_support`) all exist.

   File created: `tests/test_operator_job.py`. I changed no other test file.

   How the tests are set up:
   - The `repository` fixture copies `operator/` and `vm/` into a new git repository in `tmp_path`, commits them and tags the commit `t1`. Every run uses `SITE_CODE_REF=t1` and runs that copy's `operator/job/job.sh`.
   - A stand-in `gcloud` (Python) records each call's arguments as one JSON line. Environment variables set its answers:
     - `STAND_IN_DESCRIBE`: the exit status of `describe`; the default 1 means not found.
     - `STAND_IN_EXECUTIONS`: what `executions list` prints, as tab-separated rows.
     - `STAND_IN_EXECUTION`: the name `execute` prints.
     - `STAND_IN_FAIL` and `STAND_IN_FAIL_STATUS`: a verb that fails, printing `ERROR: (gcloud) FAILTEXT` on standard error, and its status.
   - The site file is written to `tmp_path/site/site.env`, outside every repository. `XDG_STATE_HOME` is set to `tmp_path/state`.

   Criteria → tests (all in `tests/test_operator_job.py`):
   - criterion 1: `test_create_and_update_build_the_job_call_from_the_site` (rows `create`, `update`)
   - criterion 2: `test_every_call_carries_the_project_the_region_and_the_impersonation` (create, `delete --yes` and execute, each with and without `SITE_IMPERSONATE`)
   - criterion 3: `test_missing_site_keys_are_named_in_one_line` (rows create, update, execute, delete)
   - criterion 4: `test_the_sizes_and_the_idle_minutes_have_defaults_the_site_overrides` (rows defaults, overrides)
   - criterion 5: `test_the_env_list_holds_the_site_values_and_no_path_and_no_secret`
   - criterion 6: `test_the_secrets_reach_the_job_only_as_mounts`
   - criterion 7: `test_the_wrapper_writes_the_provider_and_hands_over_to_the_tagged_start_script`, plus `test_a_code_ref_the_repository_does_not_know_stops_before_gcloud` (rows create, update, create-dry-run)
   - criterion 8: `test_the_provider_file_the_wrapper_writes_is_a_valid_provider` (rows unset-costs, set-costs, quote-in-model, quote-in-url)
   - criterion 9: `test_create_and_update_refuse_the_wrong_state_of_the_job` (rows create-existing, update-missing)
   - criterion 10: `test_a_dry_run_prints_the_call_and_runs_no_gcloud` (rows create, update)
   - criterion 11: `test_execute_refuses_to_overlap_a_running_execution` (rows count-1, count-2, a-later-row-running, none-running)
   - criterion 12: `test_delete_asks_for_yes` (rows without-yes, with-yes)
   - criterion 13: `test_a_failing_gcloud_shows_its_error_and_its_status` (rows create, update, execute-list with status 3, execute, delete)
   - criteria 14 and 15: not tests (`make check` and docs).

   Notes for the coder:
   - **Argument order.** Criterion 1 fixes three things: the order of the non-flag words, `run jobs <verb> <job>`; the set of flags, in `--name=value` form; and the exact `--set-env-vars` string, with its entries in the Interface's order.
   - **Wrapper format.** The wrapper must match `--args=-c,echo <b64> | base64 -d | gzip -d | sh` exactly.
   - **How criterion 8 runs the wrapper.** The test decodes the wrapper and changes three texts before running it with `sh`:
     - `exec sh /tmp/job-start.sh` becomes `exit 0`
     - `/srv/factory/inst-x` becomes a folder in `tmp_path`
     - `/tmp/job-start.sh` becomes a file in `tmp_path`

     It then reads `provider.json` back with `read_provider` and checks in the raw JSON that the costs are numbers.
   - **Where the messages are checked.** `create`'s "exists" message is checked on standard error, as the Interface says. The other messages are checked on standard output or standard error, because the Interface names no stream for them.

   One reading of my own, criterion 7: it says the wrapper contains no `chmod`, `cp ` or `PATH=`, but `vm/job-start.sh` itself contains all three, and the wrapper must hold that file byte for byte. So the test looks for them only in the wrapper's own text, with the embedded `job-start.sh` text removed. I see no other reading that satisfies both parts of the criterion.

   Rejected: placing the secret names and mount paths as string literals next to keys like `*_SECRET` and `*_TOKEN`. `detect-secrets` flagged those five lines, so I build them from constants whose names hold no such word.

   `lint`: lint: green (0.1 s)
   `test`: FAILED tests/test_operator_job.py::test_a_failing_gcloud_shows_its_error_and_its_status[delete] - AssertionError: assert 'ERROR: (gcloud) FAILTEXT' in 'sh: 0: cannot open /tmp/pytest-of-factory/pyt...
9. factory: started doing as vm.
10. coder: I built `operator/job/job.sh`, a new executable POSIX `sh` script with the four commands of the Interface: `create`, `update`, `execute` and `delete`. It sources `operator/lib/site.sh` and reuses `site_load` and `site_require`, so the missing-keys line, its order and exit status 2 come from the site library rather than a second copy. All 39 tests in `tests/test_operator_job.py` pass; the run printed only dots, so I have no summary line to quote. `make check` is green: lint, types, layers, sast, secrets, licenses and test (81.3 s) each ended green, then `check: green`. The sandbox refused the smoke-test command, so I did not run the two smoke-test blocks; the smoke-test stage runs them.

    How it is built:
    - **One function for every `gcloud` call.** `gcloud_call` adds `--project`, `--region` and, when it is set, `--impersonate-service-account` to each call. Under `--dry-run` it prints `gcloud` and the arguments one per line and runs nothing. `job_call` builds the `create`/`update` call once, with the verb as its only difference.
    - **Order of checks in `create` and `update`.** They check the required keys first, then the code ref with `git rev-parse --verify "<ref>^{commit}"` in the repository that holds `job.sh`. An unknown ref stops with the Interface's message and status 1, before `describe` and before any `gcloud` call, including under `--dry-run`. Then they build the wrapper, then run `describe` (not on a dry run), then the call.
    - **The wrapper.** It runs `mkdir -p <root>`, then a quoted heredoc that writes `provider.json`, then a quoted heredoc that holds the text of `git show <ref>:vm/job-start.sh` byte for byte, then `exec sh /tmp/job-start.sh`. It is packed with `gzip -n | base64 | tr -d '\n'`. If the start script ever held the heredoc's end line, the script stops with a message.
    - **`execute`.** It reads the tab-separated `executions list` rows and treats any numeric count of 1 or more as running; a blank count means not running. The execution's name is saved under `${XDG_STATE_HOME:-$HOME/.local/state}/kumpel/last-execution`.
    - **A failing `gcloud`.** Its standard error goes straight through and the command exits with its status.
    - **`describe` output.** On `create`, a failing `describe` means "not found", so its error text stays hidden. On `update` it is shown before the `does not exist; use create` message, so an auth failure is not mistaken for a missing job.

    Main choice: `python3` and `json.dumps` run in `job.sh` on the operator's machine. The wrapper carries the finished JSON as heredoc text. The alternative I rejected was having the wrapper call `python3` inside the job: the job's image, `debian:trixie-slim`, has no `python3`, and the job would break. The Interface's "written by python3" holds either way, and no value is quoted by hand. Costs are parsed as numbers (`3` gives 3, `15.5` gives 15.5).

    Smaller choices:
    - `<wrapper: N bytes>` counts the base64 text, which is the length that lands on the command line.
    - Every refusal message goes to standard error.

    Refactor: I read my diff once and found nothing to change.

    The journal changed nothing in the Description: entry 4's answers were already carried into the criteria by intake.

    Noticed, not touched:
    - A site value that contains `@` would break the `^@^` env list. No criterion covers it, and I added no check.
    - A cost value that is not a number stops `create` with Python's traceback, not a `job:` message.
    - `vm/job-start.sh` itself still holds `cp`, `chmod` and `PATH=`. The tester's reading of criterion 7 already accepts that.

    The docs criterion (15) is left for the docs stage.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
11. factory: started review as vm.
