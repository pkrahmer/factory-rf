# The job's log and state are read and sanitised by one command

## Description

Watching a factory in a job means reading Cloud Logging, which arrives a minute or two late, hides a failed query unless the error is shown, and mixes the factory's own lines with package-manager noise; the session of 2026-11-02 lost a quarter of an hour to a `gcloud` error sent to `/dev/null`, and found the machine stop that held an execution for forty minutes only by reading the log by hand. This story adds two commands to `operator/job/job.sh` (S0005): `log`, the lines of an execution, sanitised by S0006's command, with an option that drops the noise; and `status`, one line for each of the job's latest executions with the platform's own words for a failed one, and one line that says whether the factory's log shows a stop. A `gcloud` failure is shown, not swallowed.

## Interface

`operator/job/job.sh`

```sh
job.sh log [N] [--execution NAME] [--quiet]   # the last N lines (default 60), sanitised
job.sh status                                  # the latest executions, and the factory's stop, if any
```

- Both need `SITE_PROJECT`, `SITE_REGION` and `SITE_JOB`; the impersonation flag is added as in S0005.
- `log` reads the execution named by `--execution`, else the one in `last-execution` (S0005's state file), else the newest of `gcloud run jobs executions list --job=$SITE_JOB --limit=1 --format=value(metadata.name)`; none: `job: no execution of <job> found` and exit 1. It runs `gcloud logging read` with the filter `resource.type=cloud_run_job AND labels."run.googleapis.com/execution_name"=<name>`, `--order=asc`, `--limit=4000`, `--freshness=2d` and `--format=value(timestamp.date("%H:%M:%S"),textPayload)`, drops empty lines, passes the rest through `operator/bin/sanitise`, and prints the last N lines as `HH:MM:SS<TAB>text`.
- `--quiet` first drops the lines that start (after the time) with `Selecting `, `Preparing to unpack`, `Unpacking `, `Setting up `, `Get:`, `Fetched `, `Processing triggers`, `debconf:`, `Copying blob`, `Copying config`, `Writing manifest`, or that contain `token refreshed:`.
- When `gcloud` fails, `log` prints `job: gcloud logging read failed: <the first line of its standard error>` to standard error and exits 1. When it succeeds and there is no line, `log` prints `job: no log lines yet; Cloud Logging arrives one to two minutes late` and exits 0.
- `status` lists the five newest executions (`gcloud run jobs executions list --job=$SITE_JOB --limit=5 --format=json`), newest first, one line each: `<name> <state> started <HH:MM>` with ` ended <HH:MM>` for a finished one and, for a failed one, `: <the message of its first failed condition>`; `<state>` is `running` when the running count is 1 or more, `succeeded` when the succeeded count is 1 or more, `failed` when the failed count is 1 or more, else `waiting`. Times are in UTC.
- After the list, for the execution `log` would read, `status` prints `factory: stopped: <the newest log line that contains " stop ", sanitised>` when the last 200 log lines hold a line of the factory's stop form `stop <kind> <reason>: <detail>` and no later line shows the factory running again (a later `preflight:` item line counts as running), else `factory: no stop in the last 200 lines`.

Tests: `tests/test_operator_job_log.py`, the `gcloud` stand-in of S0005's tests answering `logging read` with a fixture and `executions list` with JSON, the site and the rules file in `tmp_path`.

## Acceptance criteria

1. `log` runs `gcloud logging read` once with the filter, order, limit, freshness and format of the Interface for the execution named by `--execution` (a test checks each argument), and prints the lines in order with the tab between the time and the text.
2. The choice of the execution, as rows of one parametrized test: `--execution` wins over the state file, the state file wins over the newest execution, and with none of the three the command prints `job: no execution of <job> found` and exits 1.
3. `log 3` prints the last three lines of ten; `log` prints at most 60; `log 0` prints nothing and exits 0.
4. The lines pass through the sanitiser: a fixture line holding a site pattern is printed with its replacement, a line holding a token is printed with `***TOKEN***`; with no rules file the built-ins apply and the sanitiser's warning is on standard error once.
5. `--quiet` drops each kind of line of the Interface (a row for each of the twelve prefixes and one for `token refreshed:`) and keeps a line that only contains a prefix in its middle; without `--quiet` all are kept.
6. A failing `gcloud logging read` (exit 1, `ERROR: (gcloud.logging.read) PERMISSION_DENIED` on standard error) prints `job: gcloud logging read failed: ERROR: (gcloud.logging.read) PERMISSION_DENIED` to standard error, prints nothing to standard output and exits 1.
7. An empty answer prints the `no log lines yet` message and exits 0.
8. `status` prints the newest five of six executions, newest first, with the right state for each of `running`, `succeeded`, `failed` and `waiting` (a fixture row for each) and the time of its start in UTC; a finished one has ` ended <HH:MM>`; a failed one ends with `: <message>` from its condition.
9. `status` prints `factory: stopped: <line>` for a log whose last lines hold `stop machine preflight_failed: tool:uv: uv is not on the PATH` and nothing after it, with the line sanitised; it prints `factory: no stop in the last 200 lines` when the log holds no such line, and when a `preflight:` line follows the stop line (two rows).
10. `status` with no executions prints `job: no execution of <job> found` and exits 1; its `gcloud` failures are shown as in criterion 6 (with `gcloud run jobs executions list failed`).
11. `log` and `status` read `last-execution` from `XDG_STATE_HOME` as S0005 writes it (a test writes the file with the S0005 command's own function).
12. `make check` stays green.
13. docs: `docs/operator-guide.md`, in the job part: *Watching the job* (`log` and its options, that the log is late, `status`, how to read `factory: stopped`, that the commands sanitise); `README.md` and the other documents: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/bin"
cat > "$d/bin/gcloud" <<'SH'
#!/bin/sh
case "$*" in
  *"logging read"*) printf '10:00:01\tjob-start: inputs\n10:00:02\tSetting up x\n10:00:03\tstop machine preflight_failed: tool:uv\n' ;;
  *) echo "unexpected: $*" >&2; exit 1 ;;
esac
SH
chmod +x "$d/bin/gcloud"
printf 'SITE_PROJECT=p\nSITE_REGION=r\nSITE_JOB=j\n' > "$d/site.env"
PATH="$d/bin:$PATH" FACTORY_SITE="$d/site.env" sh operator/job/job.sh log 5 --execution e1 --quiet 2>/dev/null
```

Expect: two lines, `10:00:01<TAB>job-start: inputs` and `10:00:03<TAB>stop machine preflight_failed: tool:uv` (the tab shown as a tab; the `Setting up` line is dropped).

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/bin"; printf '#!/bin/sh\necho "ERROR: (gcloud.logging.read) PERMISSION_DENIED" >&2; exit 1\n' > "$d/bin/gcloud"; chmod +x "$d/bin/gcloud"
printf 'SITE_PROJECT=p\nSITE_REGION=r\nSITE_JOB=j\n' > "$d/site.env"
PATH="$d/bin:$PATH" FACTORY_SITE="$d/site.env" sh operator/job/job.sh log --execution e1; echo "exit $?"
```

Expect: two lines, `job: gcloud logging read failed: ERROR: (gcloud.logging.read) PERMISSION_DENIED` (standard error) and `exit 1`.

## Journal
