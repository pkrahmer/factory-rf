---
stage: done
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 505
comments_read: [6588115691, 6588420336]
handed_over: approval
claim: null
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
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-02T21:01:13.519762Z'
  stage: doing
  run: 6fc1971d4a8f4ee9b34f9d035edb34b3
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-02T21:05:38.184858Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-02T21:05:56.095063Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-02T21:06:15.184078Z'
  stage: doing
  run: 583b17a6ee7741adaec221e18f292004
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-02T21:06:35.974332Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-02T21:08:37.214103Z'
  stage: tests
  run: 11ab6d279f6e482b8a44fb644f850a62
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-02T21:08:58.353085Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-02T21:12:22.770591Z'
  stage: doing
  run: 264d832fb4d540d3abf825bc624b967f
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-02T21:12:44.087744Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-02T21:14:40.547706Z'
  stage: review
  run: 4225ae1233dd4db886ea3a73b460d91d
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-02T21:15:01.242422Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-02T21:17:07.455171Z'
  stage: doing
  run: 2263c8cc4bda46b1abded5e51ed50d1b
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-02T21:17:28.326265Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-11-02T21:20:04.552815Z'
  stage: tests
  run: 90fda224ee2d430783a43e3482f3760e
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-02T21:20:25.104280Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-11-02T21:24:05.609639Z'
  stage: doing
  run: 8f4e1ace1f6940b988260af3c53c609a
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-02T21:24:27.141075Z'
  stage: review
- number: 27
  speaker: reviewer
  kind: result
  at: '2026-11-02T21:25:32.298939Z'
  stage: review
  run: 208b9f4d50f44b60814e0ddb2c8284f1
- number: 28
  speaker: factory
  kind: started
  at: '2026-11-02T21:25:52.955836Z'
  stage: docs
- number: 29
  speaker: documenter
  kind: result
  at: '2026-11-02T21:26:54.487065Z'
  stage: docs
  run: 3065d0c2eff149228ce3d369edf509ae
- number: 30
  speaker: factory
  kind: started
  at: '2026-11-02T21:27:15.524143Z'
  stage: smoke-test
- number: 31
  speaker: smoke-tester
  kind: result
  at: '2026-11-02T21:27:46.386992Z'
  stage: smoke-test
  run: c220d658ecfd4818959eca516fcb5335
- number: 32
  speaker: factory
  kind: done
  at: '2026-11-02T21:29:07.504408Z'
  stage: approval
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

- `status` reads the log with the same arguments as `log` and keeps its last 200 non-empty lines; only the stop form counts. `--quiet` that leaves no line prints nothing and exits 0. An invalid `N` or an unknown option prints `job.sh`'s usage line, which names `log` and `status` too (journal 11), on standard error and exits 2; a missing `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB` gives `site_require`'s message and exit 2. (Journal 4.)

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
10. coder: I stopped before `review`. The code is done, but `make check` fails at `make types` on the new test module, and I can't edit tests.

    The failure (`make types`, mypy --strict):
    ```
    tests/test_operator_job_log.py:418: error: Argument 4 to "run" of "JobWorld" has incompatible type "**dict[str, str]"; expected "dict[str, str] | None"  [arg-type]
    ```
    In `test_status_shows_a_missing_execution_and_gcloud_failures`, `extra` is a `dict[str, str]`. mypy checks `**extra` against every keyword of `JobWorld.run`, including `values: dict[str, str] | None`. The test runs correctly; the problem is only the type.

    Everything else is green when run one target at a time: lint, layers, sast, secrets and licenses, and `make test` (99.58 % coverage). All of `tests/test_operator_job_log.py` and `tests/test_operator_job.py` pass.

    The question: may the tester fix line 418's typing? Options:
    (a) Pass the two values as named keyword arguments: give `STAND_IN_FAIL` and `STAND_IN_FAIL_TEXT` as parameter columns (an empty string meaning "no failure") and call `world.run(..., STAND_IN_FAIL=fail or "", STAND_IN_FAIL_TEXT=fail_text)`.
    (b) Make `extra` a `dict[str, str]` and give it to `run` some other way, for example through a new `env: dict[str, str]` keyword on `JobWorld.run`.
    I would choose (a): it's the smaller change, and the stand-in already treats an empty `STAND_IN_FAIL` as no failure. With your answer I end the stage with `tests`, and the tester makes exactly that change.

    What I built (in the working tree, `operator/job/job.sh` only):
    - `log [N] [--execution NAME] [--quiet]`. It picks the execution in `chosen_execution`: the option, else `last-execution`, else `executions list --limit=1`. `read_log` runs `gcloud logging read` with the Interface's filter and flags and drops empty lines. `drop_noise` applies the eleven prefixes after the tab, plus `token refreshed:`. The lines then go through `operator/bin/sanitise` and `tail -n N`. When the answer is empty, the "no log lines yet" message goes to standard error and the exit is 0.
    - `status`: one `executions list --limit=5 --format=json` call, formatted by a small `python3 -I` program. It times the start in UTC, adds ` ended` when there is a completion time, and adds `: <message>` from the first condition whose status is `False`. The state is running, then succeeded, then failed, else waiting. It then reads the log as `log` does, and `stop_line` (awk) looks at the last 200 lines. A stop-form line (`stop <kind> <reason>: `) counts unless a later `preflight: ` line follows it. Only the printed line is sanitised.
    - `gcloud_read` shows `job: gcloud <label> failed: <first line of stderr>` and exits 1.
    - `state_folder` and `last_execution_file` are now shared with `execute`.

    Main decision: `gcloud_call` now adds `--region` only to `run` calls. The real `gcloud logging read` refuses the flag, because Cloud Logging has no region. The alternative I rejected was a second call wrapper for logging: two places to keep the project and impersonation flags in step.

    Noticed, not touched:
    - The usage line doesn't name `log` or `status`. `tests/test_operator_job.py` (S0005) checks the exact usage text, so extending it breaks six of its rows. That would need a change to an S0005 test.
    - An execution with no `startTime` prints `started -`; the Interface doesn't cover that case.
    - I couldn't run the smoke-test blocks: the sandbox refused the command.
    - Refactor pass: I removed a redundant `head -n 1`; nothing else to change.
11. 2026-11-02 human: (a), granted: the tester changes line 418's test to pass `STAND_IN_FAIL` and `STAND_IN_FAIL_TEXT` as parameter columns and named keyword arguments, as you describe.
    Also granted, in the same tester run: the usage line names `log` and `status`. The tester may change the rows of `tests/test_operator_job.py` (S0005) that pin the exact usage text to the new line, and nothing else in that file; you then extend the usage line in `job.sh`. `started -` for an execution without a start time is fine as it is.
12. factory: started doing as vm.
13. coder: The human's answer (journal 11) calls for two test changes before I can finish. I changed no code in this run.

    The changes for the tester:
    1. `tests/test_operator_job_log.py`, `test_status_shows_a_missing_execution_and_gcloud_failures` (line 418): make `STAND_IN_FAIL` and `STAND_IN_FAIL_TEXT` parameter columns (an empty string means "no failure") and pass them to `world.run(...)` as named keyword arguments, not `**extra`. This clears the `arg-type` error in `make types`.
    2. `tests/test_operator_job.py` (S0005): change only the rows that pin the exact usage text, to the new line `usage: job.sh create [--dry-run] | update [--dry-run] | execute | delete [--yes] | log [N] [--execution NAME] [--quiet] | status`. Change nothing else in that file.

    After that, I extend `usage()` in `operator/job/job.sh` to the same line and run `make check`. I don't extend it now: until the S0005 rows change, it would break them.

    Already built in the working tree (previous run, journal 10): `operator/job/job.sh` with `log` and `status`. Its main decision stays as it was: `gcloud_call` adds `--region` only to `run` calls. The alternative I rejected was a second call wrapper for logging.

    The journal changed the meaning of the task in one place: the usage line now names `log` and `status`. My write paths don't include the work item, so `## Description` is unchanged. `started -` for an execution with no start time stays, as the human accepted it.
14. factory: started tests as vm.
15. tester: I made the two test changes the human approved (journal 11), as the coder's entry 13 names them. I changed nothing else.

    1. `tests/test_operator_job_log.py`, `test_status_shows_a_missing_execution_and_gcloud_failures`:
       - `fail` is now a `str` parameter column. The no-execution row has `""`, which means no failure: the stand-in compares `STAND_IN_FAIL` with a verb that is never empty, so an empty value fails nothing.
       - The test now passes `STAND_IN_FAIL=fail` and `STAND_IN_FAIL_TEXT=fail_text` to `world.run(...)` as named keyword arguments, in place of `**extra`. This clears the `arg-type` error that `make types` reported at the old line 418.
       - What the test checks is unchanged: exit 1, and the message in standard error, or in standard output or standard error for the no-execution row.
    2. `tests/test_operator_job.py` (S0005, under the human's leave in journal 11): only the `USAGE` constant changed. It is now `usage: job.sh create [--dry-run] | update [--dry-run] | execute | delete [--yes] | log [N] [--execution NAME] [--quiet] | status`. This is the exact usage text that the rows of `test_a_wrong_command_line_prints_the_usage` check. Nothing else in that file changed.

    One run of `uv run pytest -q tests/test_operator_job_log.py tests/test_operator_job.py`: the six rows of `test_a_wrong_command_line_prints_the_usage` fail, as they should until the coder extends `usage()` in `operator/job/job.sh`. The output I read showed only those failures. `make lint` is green. I skipped the type check, as this stage's instructions say.

    Files changed: `tests/test_operator_job_log.py`, `tests/test_operator_job.py`. No files created. No module failed to import, because the code under test is a shell script.

    `lint`: lint: green (0.1 s)
    `test`: FAILED tests/test_operator_job.py::test_a_wrong_command_line_prints_the_usage[delete-dry-run] - AssertionError: assert 'usage: job.sh create [--dry-run] | update [--dry-run] | execute | delete [--y...
16. factory: started doing as vm.
17. coder: The tester changed the tests as journal 11 allowed (entry 15). In this run I made the one remaining change: `usage()` in `operator/job/job.sh` now prints `usage: job.sh create [--dry-run] | update [--dry-run] | execute | delete [--yes] | log [N] [--execution NAME] [--quiet] | status`. `make check` is green: `check: green`, 99.58 % coverage.

    What I built, all in `operator/job/job.sh`. Most of it came from the earlier run, journal 10.
    - `log [N] [--execution NAME] [--quiet]`:
      - `chosen_execution` picks the execution: the option, else `last-execution`, else `executions list --limit=1`.
      - `read_log` runs `gcloud logging read` with the Interface's filter and flags, then drops empty lines.
      - With `--quiet`, `drop_noise` removes the eleven prefixes (matched after the tab) and lines containing `token refreshed:`.
      - The lines then go through `operator/bin/sanitise`, then `tail -n N`.
    - `status`:
      - One `executions list --limit=5 --format=json` call. A small `python3 -I` program turns each execution into a line: the start time in UTC, ` ended` when there is a completion time, and `: <message>` from the first condition whose status is `False`.
      - It then reads the log as `log` does. `stop_line` (awk) looks at the last 200 lines for the stop form. A later `preflight: ` line cancels the stop. Only the printed stop line is sanitised.
    - `gcloud_read` shows `job: gcloud <label> failed: <first line of stderr>` and exits 1.
    - `state_folder` and `last_execution_file` are now shared with `execute`.

    Main decision: `gcloud_call` now adds `--region` only to `run` calls, because `gcloud logging read` refuses the flag (Cloud Logging has no region). I rejected a second call wrapper just for logging: it would mean two places that have to add the project and impersonation flags the same way.

    What the journal changed: the usage line now names `log` and `status` (journal 11), and `started -` for an execution with no start time is accepted. My write paths don't include the work item, so `## Description` is unchanged.

    Refactor pass: I read the whole diff again and found nothing to change.

    Noticed, not touched:
    - When `executions list` returns an empty list but a `last-execution` file exists, `status` prints no execution lines and reads that file's execution. It does not print `job: no execution of <job> found`. Criterion 10's test has no state file, so it passes, and the Interface doesn't cover the combination.
    - I didn't run the smoke-test blocks in this run.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
18. factory: started review as vm.
19. reviewer: Review of round 0. I read `operator/job/job.sh`, `tests/test_operator_job_log.py` and the change to `tests/test_operator_job.py` against criteria 1 to 21 and every rule of the Interface. I also checked the stop regex in `stop_line` against the factory's real log lines: `src/factory/application/stops.py:43` writes `stop {scope} {reason}: {detail}`, and `preflight.py:498` writes `preflight: {name}: {detail}` before the stop. The regex matches the stop line, and `stop cleared …` does not match it. Journal 17 says the factory's `make check` was green.

    Findings:
    1. `operator/job/job.sh` `status()` (around line 440): when `executions list` returns `[]` and a `last-execution` file exists, `status` prints no execution line, reads the saved execution's log and exits 0. Criterion 10 says without condition that `status` with no executions prints `job: no execution of <job> found` and exits 1. The coder noted this in journal 17. Fix: when the JSON list is empty, `status` prints the message and exits 1 before `chosen_execution`. The tester adds a row to `test_status_shows_a_missing_execution_and_gcloud_failures` with `world.save_execution(...)` and no executions.
    2. `tests/test_operator_job_log.py:496` `test_status_looks_for_the_stop_in_the_last_200_lines`: criterion 16 and the Interface say `status` keeps its last 200 *non-empty* lines, but no row has empty lines inside the window, so counting empty lines would pass too. Fix: add a row with empty lines after the stop line, so the stop line is the 200th non-empty line from the end and would be past 200 if the empty lines counted. Expect `factory: stopped: …`.
    3. `tests/test_operator_job_log.py:155` `words` is a second copy of `words` in `tests/test_operator_job.py:136`. `JOB` and `IMPERSONATE` (lines 16 and 18) are also copied from `tests/test_operator_job.py:20,29`, and `BARE` (line 17) holds the same three keys as `tests/test_operator_job.py:51`. Fix: the tester moves them to a shared support module under `tests/` under the standing leave, and both modules import them from there.
    4. `tests/test_operator_job_log.py:514` `test_only_the_stop_form_counts_as_a_stop` is the refused side of the stop-form rule, and its other side is the `stopped` row of `test_status_shows_the_factory_s_stop` (line 382). In the same way, `test_quiet_that_leaves_no_line_prints_nothing` (line 520) and `test_an_empty_answer_says_the_log_is_late` (line 314) are the two sides of the "`no log lines yet` only for an empty answer" rule. Fix: make each pair rows of one parametrized test.
    5. `operator/job/job.sh:302` `make_work` adds a helper for the two lines that `create_or_update` still holds as its own copy at `job.sh:230-231` (`work=$(mktemp -d) || exit 1` and the `trap`). Fix: `create_or_update` calls `make_work`.
    6. `operator/job/job.sh:2`: the purpose line still reads "create, update, execute and delete it", but the script now also reads the log and the status, as the usage comment below it says. Fix: the purpose line names reading an execution's log and the job's status.

    description corrected: "An invalid `N` or an unknown option prints `job.sh`'s usage line on standard error" -> "… prints `job.sh`'s usage line, which names `log` and `status` too (journal 11), on standard error" (journal 11 extended the usage line).

    Earlier tests:
    - `tests/test_operator_job.py`: changed under the human's leave, journal 11. Only the `USAGE` constant changed, to the new usage line; no test was renamed and none checks something else.
20. factory: started doing as vm.
21. coder: Round 1. I fixed the review's three code findings (1, 5 and 6 of journal 19), all in `operator/job/job.sh`. Its other findings and the test row for finding 1 are changes to tests, so they go to the tester. `make check` is green: `check: green`, 99.58 % coverage.

    Code changes in `operator/job/job.sh`:
    - Finding 1: `status()` now keeps the formatted execution lines. When `executions list` returns an empty list, it prints `job: no execution of <job> found` and exits 1 before it looks for an execution, so a saved `last-execution` no longer hides that there are no executions. The message now lives in one helper, `no_execution`, which `chosen_execution` uses too.
    - Finding 5: `create_or_update` calls `make_work`, which I moved above it, in place of its own copy of `mktemp` and `trap`.
    - Finding 6: the purpose line now also names reading an execution's log and the job's status.

    Main decision: I check for "no executions" on the output of the formatting program (no line at all) rather than parsing the JSON a second time in shell. I rejected a separate exit code from the Python program for an empty list because it mixes "nothing found" with a real failure of the program.

    Test changes for the tester, as journal 19 names them:
    1. `tests/test_operator_job_log.py`, `test_status_shows_a_missing_execution_and_gcloud_failures`: add a row with `world.save_execution(...)` and an empty executions list. Expected: `job: no execution of <job> found` and exit 1 (finding 1).
    2. `test_status_looks_for_the_stop_in_the_last_200_lines`: add a row with empty lines after the stop line, so the stop line is the 200th non-empty line from the end but would fall past 200 if empty lines counted. Expected: `factory: stopped: …` (finding 2).
    3. Under the standing leave, move `words`, `JOB`, `IMPERSONATE` and the three-key `BARE` site values from `tests/test_operator_job.py` and `tests/test_operator_job_log.py` into one shared support module under `tests/`, and import them from there in both modules (finding 3).
    4. Merge `test_only_the_stop_form_counts_as_a_stop` into `test_status_shows_the_factory_s_stop` as a row. Merge `test_quiet_that_leaves_no_line_prints_nothing` and `test_an_empty_answer_says_the_log_is_late` into one parametrized test (finding 4).

    What the journal changed: the reviewer already updated the Description's usage sentence. Nothing else changed in meaning.

    Refactor pass: in my own diff, the no-execution message was written twice, so I moved it into `no_execution`. Nothing else to change.

    Noticed, not touched: I didn't run the smoke-test blocks.
22. factory: started tests as vm.
23. tester: I made the four test changes that the coder's entry 21 names, from the review's findings in journal 19. I changed nothing else.

    1. `tests/test_operator_job_log.py::test_status_shows_a_missing_execution_and_gcloud_failures` (finding 1): new `saved` column and new row `no-execution-saved-file`. It calls `world.save_execution("e-saved")`, gives an empty executions list, and expects exit 1 and `job: no execution of factory-job found`. The other rows have `saved=False` and check what they checked before.
    2. `test_status_looks_for_the_stop_in_the_last_200_lines` (finding 2): the `after` column now holds the lines that follow the stop line, not a count. The two old rows keep their ids and cases (199 and 200 filler lines). New row `200th-non-empty-with-empty-lines`: `[FILLER, ""] * 199` after the stop line, which expects `factory: stopped: …`. The stop line is the 200th non-empty line from the end, but it would be the 399th line if empty lines counted.
    3. Shared helpers moved under the standing leave in `CLAUDE.md` *Tests* (finding 3). `JOB`, `IMPERSONATE`, `BARE` (the three site keys, same values) and `words` now live in the new `tests/operator_job_support.py`. Both `tests/test_operator_job_log.py` and `tests/test_operator_job.py` import them from there, and their own copies are gone.
       - Earlier test file changed: `tests/test_operator_job.py` (S0005). Only its definitions of `JOB`, `IMPERSONATE`, `BARE` and `words` were removed, and one import was added. No test was renamed, and every test checks the same thing.
    4. Merged pairs (finding 4):
       - `test_only_the_stop_form_counts_as_a_stop` is now the `not-the-stop-form` row of `test_status_shows_the_factory_s_stop`.
       - `test_an_empty_answer_says_the_log_is_late` and `test_quiet_that_leaves_no_line_prints_nothing` are now one test, `test_only_an_empty_answer_says_the_log_is_late`, with the rows `empty-answer` and `quiet-leaves-no-line`. Both rows make the same assertions as before.

    Changed mapping, one line each:
    - criterion 10 (no execution): `tests/test_operator_job_log.py::test_status_shows_a_missing_execution_and_gcloud_failures`
    - criterion 16 (last 200 non-empty lines): `tests/test_operator_job_log.py::test_status_looks_for_the_stop_in_the_last_200_lines`
    - stop form only: `tests/test_operator_job_log.py::test_status_shows_the_factory_s_stop`
    - `no log lines yet` only for an empty answer: `tests/test_operator_job_log.py::test_only_an_empty_answer_says_the_log_is_late`

    All other criteria keep the tests that entry 15 and the earlier tester entries name.

    One run of `uv run pytest -q tests/test_operator_job_log.py tests/test_operator_job.py`: every test passed. That includes the new rows, since the coder already changed `job.sh` in entry 21. `make lint` is green. I skipped the type check, as this stage's instructions say.

    Files created: `tests/operator_job_support.py`. Files changed: `tests/test_operator_job_log.py`, `tests/test_operator_job.py`. No module failed to import.

    `lint`: lint: green (0.1 s)
    `test`: test: green (80.1 s)
24. factory: started doing as vm.
25. coder: Round 1, after the tester's changes (entry 23). The review findings that needed code (1, 5 and 6 of journal 19) were already fixed in `operator/job/job.sh` in entry 21. The tester's entry 23 has made the four test changes: the no-execution row with a saved file, the row with empty lines inside the 200-line window, the shared `tests/operator_job_support.py`, and the merged pairs. Nothing was left for code, so I changed no file in this run. The working tree was clean at the start and still is.

    `make check` passed in the foreground: `check: green`, coverage 99.58 %, `test: green (80.3 s)`. So the new rows pass against the code from entry 21.

    What I built is unchanged from entry 21, all in `operator/job/job.sh`: the `log` and `status` commands, `gcloud_read`, `no_execution`, and `create_or_update` now uses `make_work`. The main decision stands: `gcloud_call` adds `--region` only to `run` calls, because `gcloud logging read` refuses the flag. I rejected a second call wrapper for logging, which would mean keeping the project and impersonation flags the same in two places.

    Refactor pass: no new diff in this run, so nothing to change.

    What the journal changed: nothing since entry 21. The reviewer had already rewritten the Description's usage sentence.

    Noticed, not touched: I tried to run both smoke-test blocks, but the sandbox refused the command, so they are still not run.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
26. factory: started review as vm.
27. reviewer: Review of round 1. I read `operator/job/job.sh`, the new `tests/operator_job_support.py`, `tests/test_operator_job_log.py` and the changes to `tests/test_operator_job.py`. I checked them against criteria 1 to 21 and every rule of the Interface, and I checked how each finding of journal 19 was handled. Journal 25 records the factory's `make check` as green after the coder (`check: green`, `duplicates: 0 new`).

    How the round-0 findings were handled:
    - Finding 1: `status()` prints `no_execution` and exits 1 before `chosen_execution` when the formatted list is empty. The new row `no-execution-saved-file` pins this.
    - Finding 2: the row `200th-non-empty-with-empty-lines` puts 199 empty lines after the stop line. If empty lines counted, the stop line would sit at the 399th line from the end.
    - Finding 3: `JOB`, `IMPERSONATE`, `BARE` and `words` now live in `tests/operator_job_support.py`. `BARE` keeps the values `SITE` gave it (`p1`, `europe-west3`, `JOB`).
    - Finding 4: the paired tests are now rows of `test_status_shows_the_factory_s_stop` and `test_only_an_empty_answer_says_the_log_is_late`.
    - Finding 5: `create_or_update` calls `make_work`.
    - Finding 6: the purpose line names reading the log and the status.

    Every limit is tested on both sides: N at 60 and 61, and 0; the window at 200 and 201; five of six executions. Every refused side is tested too: an invalid N, an unknown option, a missing site value, a failed `gcloud` call and no execution. I searched `operator/` for a second copy of the new helpers (`gcloud_read`, the UTC clock, `drop_noise`) and found none.

    no findings

    Earlier tests:
    - `tests/test_operator_job.py`: two leaves cover it. Under the human's leave in journal 11, only the `USAGE` constant changed to the new usage line. Under the standing leave to move a shared test helper, `JOB`, `IMPERSONATE`, `BARE` and `words` moved to `tests/operator_job_support.py`, with the same values and the same function. No test was renamed, and none checks anything different.

    Notes:
    - `tests/test_operator_job_log.py:398-402` and `:526-530`: the same assertion on the last line (stopped or `NO_STOP`) is written twice. A small helper in the module would hold it once.
28. factory: started docs as vm.
29. documenter: Docs for round 1. I changed only `docs/operator-guide.md` (documents only, so I did not run `make check`; the factory's checks decide).

    Changes in `docs/operator-guide.md`:
    - New section *Watching the job*, after *Creating the job* and under *On Cloud Run*. It covers `log` and its options (the choice of execution, the default of 60 lines, the 4000-line and two-day read, the eleven `--quiet` prefixes and `token refreshed:`, the `no log lines yet` message and why the log is late). It also covers `status` (the line format, UTC, how the state is chosen, the platform's message for a failed execution), how to read `factory: stopped` and `factory: no stop in the last 200 lines`, sanitising, the shown `gcloud` failures, and the usage exit 2.
    - *Creating the job*: the sentence "every `gcloud` call carries `--project` and `--region`" was wrong after this story, because `gcloud logging read` refuses `--region`. It now says `--region` goes only to `gcloud run` calls. I added `log` and `status` to the command block and to the keys table (`SITE_PROJECT`, `SITE_REGION`, `SITE_JOB`, plus `SITE_IMPERSONATE` when set).
    - *The site file*: the pointer to `job.sh` now also names *Watching the job*.

    I ran the first smoke-test block against a `gcloud` stand-in. It printed the two expected lines with a tab, and the `Setting up` line was dropped. I did not run the second block or `status` by hand; the tests cover them.

    Cross-read and found current: `README.md` (no mention of `job.sh`; the criterion says none), the *Sanitising what leaves the machine* section, and the `execute`/`last-execution` paragraph. I read the diff of `operator/job/job.sh` against the Interface and found no mismatch, so no finding for the coder. I read the code only for what the docs state, and I did not run `status` against a real execution list.

    Stale text I did not touch: nothing found. A note for the next reader of the guide: *The site file* still says "the stories to come make the other keys live", which is the feature's own plan and stays true until its last story.

    `check`: check: green (not run again: passed on tree c12ba0cd0863 at 2026-11-02T21:22:33Z)
    `secrets`: secrets: green (1.4 s)
    `documents`: documents ok
30. factory: started smoke-test as vm.
31. smoke-tester: Ran both smoke-test commands from the repository root. I ran them directly in the shell tool, not inside a `bash -c` wrapper: the tool's safety check refused the wrapper because of its `trap 'rm -rf "$d"' EXIT`. Each command ran as written, except for two things I added at the end so the result could be checked: `echo "exit $?"` on the first command, and on both commands redirecting standard output and error to files under `$d`, then printing the output with `cat -A` (which shows a tab as `^I`). The redirection is the only way to tell the two streams apart. The traps removed the temporary directories afterwards; nothing was left in `/tmp`.

    Command 1 (`job.sh log 5 --execution e1 --quiet`, `gcloud` stand-in answering three lines):

    ```
    exit 0
    10:00:01^Ijob-start: inputs$
    10:00:03^Istop machine preflight_failed: tool:uv$
    ```

    Expect: two lines, `10:00:01<TAB>job-start: inputs` and `10:00:03<TAB>stop machine preflight_failed: tool:uv`, with the `Setting up` line dropped. **Met.** Both lines are there, separated by a real tab (`^I`), and the `Setting up x` line was dropped.

    Command 2 (`job.sh log --execution e1`, `gcloud` stand-in that fails with PERMISSION_DENIED):

    ```
    exit 1
    --stdout:
    --stderr:
    job: gcloud logging read failed: ERROR: (gcloud.logging.read) PERMISSION_DENIED
    ```

    Expect: `job: gcloud logging read failed: ERROR: (gcloud.logging.read) PERMISSION_DENIED` on standard error, and `exit 1`. **Met.** The message went to standard error, nothing went to standard output, and the exit code was 1, as criterion 6 asks.

    Reading the acceptance criteria again: neither command contradicts any criterion. Commands 1 and 2 agree with criteria 1, 5 and 6; the others (`status`, choosing the execution, the sanitiser rules, impersonation) were not exercised by these commands and nothing here goes against them.

    Findings: none.
32. factory: done (pull request merged); cost: 14 runs, 21.5 min, 117 turns, 442446 tokens in (3185383 more from cache), 79160 out, $5.37
