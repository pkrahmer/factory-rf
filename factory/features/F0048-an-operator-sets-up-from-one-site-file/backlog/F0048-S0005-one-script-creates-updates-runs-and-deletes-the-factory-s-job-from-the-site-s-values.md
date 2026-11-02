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
- The wrapper is one line of shell, `echo <b64> | base64 -d | gzip -d | sh`, of a script that: makes `<root>`, writes `<root>/provider.json` (below), writes the text of `vm/job-start.sh` of this repository to `/tmp/job-start.sh` (as the job's first process it does so by `exec`) and ends in `exec sh /tmp/job-start.sh`. It holds no logic besides these.
- `provider.json` is the provider file of the operator guide: `{"id": "site", "base_url": $SITE_MODEL_BASE_URL, "api_key_env": "ANTHROPIC_API_KEY", "models": {$SITE_MODEL: {"name": $SITE_MODEL, "context": 200000, "output": 16000, "input_cost": $SITE_MODEL_INPUT_COST, "output_cost": $SITE_MODEL_OUTPUT_COST}}, "small_model": "site/$SITE_MODEL"}`, written by `python3` (`json.dumps`, so no value needs quoting by hand).
- `create` first runs `gcloud run jobs describe $SITE_JOB`; when that succeeds it prints `job: <job> exists; use update` to standard error and exits 1, without creating. `update` exits 1 with `job: <job> does not exist; use create` when `describe` fails.
- `--dry-run` runs no `gcloud` call that changes anything (and no `describe`): it prints the call, one argument per line, with the wrapper's base64 text replaced by `<wrapper: N bytes>`, and exits 0.
- `execute` first runs `gcloud run jobs executions list --job=$SITE_JOB --format=value(metadata.name,status.runningCount)`; when a row has a running count of 1 or more it prints `job: an execution of <job> is still running: <name>; two executions of one instance must not overlap` and exits 1. Else it runs `gcloud run jobs execute $SITE_JOB --async --format=value(metadata.name)`, prints the name, and writes it to `${XDG_STATE_HOME:-$HOME/.local/state}/factory-operator/last-execution`.
- `delete` without `--yes` prints `job: would delete <job> and stop its running execution; run again with --yes` and exits 1; with `--yes` it runs `gcloud run jobs delete $SITE_JOB --quiet`.
- A `gcloud` that fails: its standard error is shown and the command exits with its status.

Tests: `tests/test_operator_job.py`, a stand-in `gcloud` that records its arguments and plays answers per row (`describe` found or not, an execution list), the site file in `tmp_path`; the provider file is read back with `factory.domain.opencode_provider.read_provider` in a test of the story.

## Acceptance criteria

1. With the required keys set, `create` runs `gcloud` once for `describe` and once for `create`, the second with the arguments of the Interface in an order a test may fix (it fixes the set, and the order of `--set-env-vars`'s entries), and exits 0.
2. Every call carries the project and the region; with `SITE_IMPERSONATE` set every call also carries `--impersonate-service-account=<it>`, and without it no call does (two rows).
3. Missing keys: with `SITE_REGION` and `SITE_CODE_REF` unset, `create` prints one `site: missing SITE_REGION, SITE_CODE_REF in <path>` line, runs no `gcloud` and exits 2; `execute` with only the project, the region and the job set works (a row for each of the three commands).
4. The defaults and the overrides, as rows of one parametrized test: no `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT` and `SITE_IDLE_MINUTES` give `--cpu=8`, `--memory=32Gi`, `--task-timeout=14400` and `FACTORY_IDLE_SHUTDOWN_MINUTES=60`; set values replace them.
5. The env list: it starts with `^@^`, its entries are separated by `@`, it holds every name of the Interface with the site's values (a value containing a comma is intact), it holds the four proxy spellings with the proxy's value and both `NO_PROXY` spellings, it holds no `PATH` entry, and it contains none of the texts `TOKENMARK` and `SECRETMARK` that a test puts into the stand-in's environment and into a token command.
6. The secrets are mounts only: `--set-secrets` is exactly the two mounts of the Interface with the site's secret names, and no argument of any call contains the content of a secret.
7. The wrapper: decoding the base64 text of `--args` and un-gzipping it gives a script that contains `mkdir -p /srv/factory/<instance>`, writes `provider.json` and `/tmp/job-start.sh`, ends in `exec sh /tmp/job-start.sh`, and holds the text of this repository's `vm/job-start.sh` byte for byte; it contains no `chmod`, no `cp` and no `PATH=`.
8. `provider.json` as the script writes it is accepted by `read_provider`, and the provider it returns has the id `site`, the base URL and the model of the site, `input_cost` and `output_cost` as numbers (`0` when unset), and `small_model` `site/<model>`; a model name or a URL with a double quote in it still gives valid JSON.
9. `create` for a job that exists (the `describe` stand-in exits 0) prints `job: <job> exists; use update` to standard error, exits 1 and runs no `create`; `update` for a job that does not exist prints `job: <job> does not exist; use create`, exits 1 and runs no `update` (two rows).
10. `--dry-run` runs no `gcloud` at all, prints the call one argument per line with the wrapper replaced by `<wrapper: N bytes>`, and exits 0; the printed text contains the job's name and no base64 text longer than 100 characters.
11. `execute` with a row of `running count 1` prints the overlap message with the execution's name, exits 1 and runs no `execute`; with rows of `0` and empty counts it runs `execute --async`, prints the name the stand-in answers, writes it to `last-execution` under `XDG_STATE_HOME` (a test sets it), and exits 0.
12. `delete` without `--yes` prints the message of the Interface, exits 1 and runs no `delete`; with `--yes` it runs it with `--quiet`.
13. A failing `gcloud` (exit 1 with text on standard error) shows that text and the command exits 1 (a row for `create`).
14. `make check` stays green.
15. docs: `docs/operator-guide.md`, *Creating the job*: the template call is replaced by `job.sh create` with the keys it reads (a table that points to the site file's table), the order of a first start (`site check`, `job.sh create`, `job.sh execute`), the overlap rule and the deletion rule, and says that the job's wrapper only writes the provider file and hands over; `README.md` and the other documents: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/bin"
printf '#!/bin/sh\ncase "$*" in *executions*) ;; *execute*) echo exec-1 ;; esac\n' > "$d/bin/gcloud"; chmod +x "$d/bin/gcloud"
printf 'SITE_PROJECT=p\nSITE_REGION=r\nSITE_JOB=j\n' > "$d/site.env"
PATH="$d/bin:$PATH" FACTORY_SITE="$d/site.env" XDG_STATE_HOME="$d/state" sh operator/job/job.sh execute; echo "exit $?"
cat "$d/state/factory-operator/last-execution"
```

Expect: three lines: `exec-1`, `exit 0` and `exec-1` (the stand-in lists no running execution, answers the execute with a name, and the name is saved).

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_PROJECT=p\n' > "$d/site.env"
FACTORY_SITE="$d/site.env" sh operator/job/job.sh create; echo "exit $?"
```

Expect: two lines: `site: missing SITE_REGION, SITE_RUN_AS, SITE_CONNECTOR, SITE_PROXY, SITE_NO_PROXY, SITE_JOB, SITE_INSTANCE, SITE_REPOSITORY_URL, SITE_CODE_URL, SITE_CODE_REF, SITE_HOSTING_SECRET, SITE_MODEL_SECRET, SITE_MODEL_BASE_URL, SITE_MODEL, SITE_LOGIN_URL, SITE_LOGIN_SCOPE, SITE_LOGIN_CLIENT_ID in <the file's path>` (on standard error) and `exit 2`.

## Journal
