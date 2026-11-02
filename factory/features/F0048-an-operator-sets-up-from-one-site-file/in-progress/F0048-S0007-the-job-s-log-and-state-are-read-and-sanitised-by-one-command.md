---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 505
comments_read: [6588115691]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-02T20:57:02.254547Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-02T20:48:08.495259Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-02T20:48:08.501904Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-02T20:48:38.183807Z'
  stage: intake
  run: 6cc8d335d8454698bcb248dd471f0395
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-02T20:49:56.918224Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-02T20:50:14.796694Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-02T20:50:37.438270Z'
  stage: intake
  run: 9e1ebd00a8d74424b1b3ca0f907f76e6
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-02T20:50:58.216190Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-02T20:56:41.491751Z'
  stage: tests
  run: 94489c0296334d27b7c028ef18f349a4
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-02T20:57:02.254547Z'
  stage: doing
---

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

- `status` reads the log with the same arguments as `log` and keeps its last 200 non-empty lines; only the stop form counts. `--quiet` that leaves no line prints nothing and exits 0. An invalid `N` or an unknown option prints `job.sh`'s usage line on standard error and exits 2; a missing `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB` gives `site_require`'s message and exit 2. (Journal 4.)

Tests: `tests/test_operator_job_log.py`, the `gcloud` stand-in of S0005's tests answering `logging read` with a fixture and `executions list` with JSON, the site and the rules file in `tmp_path`.

## Acceptance criteria

1. `log` runs `gcloud logging read` once with the filter, order, limit, freshness and format of the Interface for the execution named by `--execution` (a test checks each argument), and prints the lines in order with the tab between the time and the text.
2. The choice of the execution, as rows of one parametrized test: `--execution` wins over the state file, the state file wins over the newest execution, and with none of the three the command prints `job: no execution of <job> found` and exits 1.
3. `log 3` prints the last three lines of ten; `log` prints at most 60; `log 0` prints nothing and exits 0.
4. The lines pass through the sanitiser: a fixture line holding a site pattern is printed with its replacement, a line holding a token is printed with `***TOKEN***`; with no rules file the built-ins apply and the sanitiser's warning is on standard error once.
5. `--quiet` drops each kind of line of the Interface (a row for each of the eleven prefixes and one for `token refreshed:`) and keeps a line that only contains a prefix in its middle; without `--quiet` all are kept.
6. A failing `gcloud logging read` (exit 1, `ERROR: (gcloud.logging.read) PERMISSION_DENIED` on standard error) prints `job: gcloud logging read failed: ERROR: (gcloud.logging.read) PERMISSION_DENIED` to standard error, prints nothing to standard output and exits 1.
7. An empty answer prints the `no log lines yet` message and exits 0.
8. `status` prints the newest five of six executions, newest first, with the right state for each of `running`, `succeeded`, `failed` and `waiting` (a fixture row for each) and the time of its start in UTC; a finished one has ` ended <HH:MM>`; a failed one ends with `: <message>` from its condition.
9. `status` prints `factory: stopped: <line>` for a log whose last lines hold `stop machine preflight_failed: tool:uv: uv is not on the PATH` and nothing after it, with the line sanitised; it prints `factory: no stop in the last 200 lines` when the log holds no such line, and when a `preflight:` line follows the stop line (two rows).
10. `status` with no executions prints `job: no execution of <job> found` and exits 1; its `gcloud` failures are shown as in criterion 6 (with `gcloud run jobs executions list failed`).
11. `log` and `status` read `last-execution` from `XDG_STATE_HOME` as S0005 writes it (a test writes the file with the S0005 command's own function).
12. Empty lines in the answer are not printed, and `log N` counts only the non-empty lines (a fixture with empty lines between).
13. With the site's impersonation value set, `log` and `status` pass the impersonation flag to every `gcloud` call (`logging read` and `executions list`).
14. With `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB` missing, `log` and `status` print `site_require`'s message and exit 2 (one row per command).
15. `status` gives `running` for an execution with running 1 and failed 1.
16. `status` reads the log with the same arguments as `log` and keeps its last 200 non-empty lines: a stop line that is the 200th from the end is found, one that is the 201st gives `factory: no stop in the last 200 lines` (two rows).
17. Only the stop form `stop <kind> <reason>: <detail>` counts: a line that only contains ` stop ` (`job: stop requested by user`) gives `factory: no stop in the last 200 lines`.
18. `--quiet` that leaves no line prints nothing and exits 0, without the `no log lines yet` message.
19. An invalid `N` (not a number, negative) and an unknown option each print `job.sh`'s usage line on standard error and exit 2 (a row each).
20. `make check` stays green.
21. docs: `docs/operator-guide.md`, in the job part: *Watching the job* (`log` and its options, that the log is late, `status`, how to read `factory: stopped`, that the commands sanitise); `README.md` and the other documents: none.

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

1. 2026-11-02 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. Questions:

   1. Criterion 5 says "a row for each of the twelve prefixes and one for `token refreshed:`", but the Interface lists eleven prefixes: `Selecting `, `Preparing to unpack`, `Unpacking `, `Setting up `, `Get:`, `Fetched `, `Processing triggers`, `debconf:`, `Copying blob`, `Copying config` and `Writing manifest`. Is one prefix missing from the Interface, or should the criterion say eleven? I would say eleven.
   2. The Interface says `log` "drops empty lines" and has no criterion for it. I would add one: a fixture with empty lines in between prints none of them, and `log N` counts only the non-empty lines.
   3. The Interface says "the impersonation flag is added as in S0005", and no criterion tests it for `log` or `status`. I would add a criterion: with the site's impersonation value set, both commands pass the flag to every `gcloud` call (logging read and executions list). Please also confirm what happens when `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB` is missing. Is that the loader's error as in S0005, and does it need a row here?
   4. The state rule has no criterion for the executions list. In `status`, the `<state>` precedence (`running`, then `succeeded`, then `failed`, else `waiting`) is only tested with single-count fixtures. I would add a row where two counts are 1 or more, such as running 1 and failed 1, expecting `running`.
   5. The last-200-lines window in `status` has no test on its edge. I would add a row: a stop line that is the 200th line from the end is found, and one that is the 201st gives `no stop in the last 200 lines`. Also say what `status` asks `gcloud logging read` for: the same arguments as `log` with its last 200 lines kept?
   6. The stop rule is ambiguous. The text says "the newest log line that contains ` stop `", but the condition is a line of the form `stop <kind> <reason>: <detail>`. A line that contains ` stop ` without that form (say `job: stop requested by user`) has no stated outcome. I would say only the stop form counts, and add a row for it that gives `no stop`.
   7. `log` after `--quiet` leaves no line. Does it print the `no log lines yet` message (my choice: no, only an empty answer from `gcloud` does) or nothing? Please state it, with a row.
   8. An invalid `N` (not a number, negative) and an unknown option have no stated behaviour. I would add a row: a message on standard error and exit 2, or whatever the S0005 commands do.
4. 2026-11-02 human: All as you propose:
   1. Eleven; criterion 5 says eleven.
   2. Yes, the empty-line criterion, and `log N` counts only non-empty lines.
   3. Yes, the impersonation criterion for both commands; a missing `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB` gives `site_require`'s message and exit 2, as in S0005, one row per command.
   4. Yes, the row with running 1 and failed 1 giving `running`.
   5. Yes, both edge rows; `status` reads the log with the same arguments as `log` and keeps its last 200 non-empty lines.
   6. Only the stop form `stop <kind> <reason>: <detail>` counts; add the row for a line that only contains ` stop `.
   7. `--quiet` that leaves no line prints nothing and exits 0; the `no log lines yet` message is only for an empty answer from `gcloud`. A row.
   8. An invalid `N` or an unknown option prints `job.sh`'s usage line on standard error and exits 2, as its other commands do. A row each.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: `operator/job/job.sh` `log [N] [--execution NAME] [--quiet]` and `status` are concrete: exact gcloud arguments, formats, messages and exit codes. Journal 4's answers are now in the Interface (one added bullet).
   - Criteria: each is testable by one parametrized test. Carried in from journal 4 (the human's edit, not mine): criterion 5 now says eleven prefixes. New criteria 12 to 19 cover empty lines, impersonation, missing SITE_ values, state precedence, the 200-line edge on both sides, the stop form only, `--quiet` leaving nothing, and invalid N or option (exit 2). `make check` and `docs:` are now 20 and 21. Every rule has its failing side.
   - Smoke test: both blocks are runnable with a stand-in gcloud on PATH. Each has an `Expect:` line that can be checked against the output. No pytest command is involved.
   - Architecture: shell under `operator/job/`, using S0005's state file and S0006's sanitiser. It touches no layer of `src/factory`. Tests are at the `tests/` root, as the story names.
   - Scope: within feature scope (S0007 `job.sh log` and `status`). Nothing from "Out of scope" is touched.
7. factory: started tests as vm.
8. tester: I wrote the tests for `job.sh log` and `job.sh status` in one new module. It runs `operator/job/job.sh` from the checkout, with a `gcloud` stand-in first on the `PATH`, the site file and `sanitise.rules` in `tmp_path/site`, and `XDG_STATE_HOME` in `tmp_path`.

   Criterion → test (all in `tests/test_operator_job_log.py`):
   - criterion 1: `test_log_reads_the_named_execution_and_prints_its_lines_in_order`
   - criterion 2: `test_log_chooses_the_execution` (rows: option-over-state-file, state-file-over-newest, newest, none)
   - criterion 3: `test_log_prints_the_last_n_lines` (rows: three-of-ten, sixty-of-sixty, sixty-of-sixty-one, zero)
   - criterion 4: `test_log_passes_its_lines_through_the_sanitiser` (rows: site-pattern, token, no-rules-file with exactly one warning)
   - criterion 5: `test_quiet_drops_the_noise` (one row for each of the eleven prefixes, one for `token refreshed:`, keeps-prefix-in-the-middle, keeps-all-without-quiet)
   - criterion 6: `test_a_failing_logging_read_is_shown`
   - criterion 7: `test_an_empty_answer_says_the_log_is_late`
   - criterion 8: `test_status_lists_the_five_newest_executions` (six executions; TZ is `XYZ-9`, so a time printed in local time would show)
   - criterion 9: `test_status_shows_the_factory_s_stop` (rows: stopped, none, preflight-after-stop)
   - criterion 10: `test_status_shows_a_missing_execution_and_gcloud_failures` (rows: no-execution, executions-list-fails, logging-read-fails)
   - criterion 11: `test_log_and_status_read_the_execution_job_execute_saved` (the file is written by running `job.sh execute` itself)
   - criterion 12: `test_log_leaves_out_empty_lines` (rows: all, two)
   - criterion 13: `test_every_gcloud_call_carries_the_impersonation` (log, status)
   - criterion 14: `test_a_missing_site_value_is_refused` (log and status × each of the three values)
   - criterion 15: `test_status_names_running_before_failed`
   - criterion 16: `test_status_looks_for_the_stop_in_the_last_200_lines` (rows: 200th-from-the-end, 201st-from-the-end; it also checks that status's `logging read` call equals log's)
   - criterion 17: `test_only_the_stop_form_counts_as_a_stop`
   - criterion 18: `test_quiet_that_leaves_no_line_prints_nothing`
   - criterion 19: `test_a_wrong_argument_prints_the_usage` (rows: n-not-a-number, n-negative, log-unknown-option, status-unknown-option)

   Choices where the criteria leave room. None of them decides behaviour the criteria leave open:
   - **Own stand-in.** The `gcloud` stand-in is a new one in my module. The S0005 stand-in in `tests/test_operator_job.py` cannot answer `logging read`, and `executions list` there cannot answer as each `--format` asks. Extending it would go beyond the standing leave to move a helper. No earlier test file was changed.
   - **Execution shape.** Fixture executions use the Cloud Run v1 JSON shape: `metadata.name`, `status.startTime`, `completionTime`, `runningCount`, `succeededCount`, `failedCount`, `conditions`. Zero counts are left out, as gcloud does. The stand-in honours `--limit`.
   - **Failed condition.** The failed execution has one condition with status `True` first and one with status `False` that carries the message. Any reasonable reading of "first failed condition" passes.
   - **Stop line.** The stop line is the factory's own log form, `<stamp> stop machine preflight_failed: …`. The test checks only that the `factory: stopped: ` line ends with the sanitised stop text, so it does not decide whether the time prefix is kept.
   - **Not asserted.** For `status`, the tests do not check the exit status where no criterion states it. They also do not check standard output after a failure in `status`, because the list is printed before the log is read.

   Files created: `tests/test_operator_job_log.py`.

   Test run (`uv run pytest -q tests/test_operator_job_log.py`): the tests fail because `job.sh` has no `log` or `status` command yet. It answers both with its usage line and exit 2. No module failed to import, because the code under test is a shell script. The rows of `test_a_wrong_argument_prints_the_usage` probably pass already, since today's usage line covers them, but I did not confirm it: the output I read showed only the failures. `make lint` is green.

   `lint`: lint: green (0.1 s)
   `test`: FAILED tests/test_operator_job_log.py::test_quiet_that_leaves_no_line_prints_nothing - AssertionError: usage: job.sh create [--dry-run] | update [--dry-run] | execute | delete [--yes]
9. factory: started doing as vm.
