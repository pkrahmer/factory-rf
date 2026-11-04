---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 545
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T19:50:44.061281Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T19:50:44.068238Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-04T19:51:09.837277Z'
  stage: intake
  run: 7a058d81a3aa41e99c47fd5b3d73309b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-04T19:51:15.743127Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-04T19:54:12.959383Z'
  stage: tests
  run: b9d69d1bfff64ee5ae1d1559dfa99d9c
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-04T19:54:22.971858Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-04T20:00:08.929538Z'
  stage: doing
  run: 9a50f13b4fe442b09a84374110bd2083
---

# The transcript folder is set up on the VM and in Cloud Run

## Description

S0005 keeps transcripts in the folder `FACTORY_TRANSCRIPT_DIR` names; this story gives each kind of site that folder. On a VM, `vm/setup.sh` makes `/srv/factory/<instance>/transcripts`, owned by the factory's user with mode `0700`, writes `FACTORY_TRANSCRIPT_DIR` into the instance's environment file, and writes a `tmpfiles.d` rule that makes systemd remove the folder's files older than 30 days (systemd's daily `systemd-tmpfiles-clean` runs it). In a Cloud Run job the folder is a Cloud Storage bucket of the site's own project, mounted into the job as a volume; the operator creates the bucket, its lifecycle rule and the mount, and `vm/job-start.sh` only checks that the folder it is given can be written. The bucket stays inside the site, readable only by the job's service account and the people the site allows; the factory needs no Cloud Storage client and no new right.

## Interface

- `vm/setup.sh`: a step `transcripts` that makes the folder (owner `factory`, mode `0700`), the line `FACTORY_TRANSCRIPT_DIR=/srv/factory/<instance>/transcripts` in `factory.env`, and the file `/etc/tmpfiles.d/factory-<instance>-transcripts.conf` with the one line `d /srv/factory/<instance>/transcripts 0700 factory factory 30d`. A second run of the script finds all done and changes nothing. A new option `--transcript-days <n>` sets another age; `--transcript-days 0` writes neither the line nor the rule, makes no folder and keeps no transcript.
- `vm/job-start.sh`: when `FACTORY_TRANSCRIPT_DIR` is set, it checks before the factory starts that the folder exists and a file can be written and removed there; a failure ends the start with the message `transcript folder <path> cannot be written` and a status that is not 0. When it is unset, nothing changes.
- No change to `src/` beyond what S0005 built.

## Acceptance criteria

1. A run of `vm/setup.sh` makes the folder with owner `factory` and mode `0700`, writes the setting's line and the `tmpfiles.d` rule with `30d`; a second run changes nothing. Rows: the default, `--transcript-days 7` (the rule says `7d`), `--transcript-days 0` (no line, no rule, no folder), `--transcript-days x` (refused with the option's name).
2. `vm/job-start.sh` with a writable folder starts as before; with a folder that does not exist or cannot be written it ends with the message and a status that is not 0; with the setting unset it starts as before.
3. `make check` stays green. No test creates anything in a cloud.
4. docs: `docs/operator-guide.md`: in *Transcripts*, the VM's folder, its `tmpfiles.d` rule and the option; for Cloud Run, the steps the operator takes once: a bucket in the job's project and region, uniform access, no public access, a lifecycle rule that deletes objects after 30 days, the job's service account with `roles/storage.objectUser` on that bucket only, and the job's volume mount (`gcloud run jobs update <job> --add-volume name=transcripts,type=cloud-storage,bucket=<bucket> --add-volume-mount volume=transcripts,mount-path=<path>`), with `FACTORY_TRANSCRIPT_DIR=<path>`; and that a bucket costs a few cents a month at these sizes (about 5 MB per feature). `docs/decisions.md`: none beyond S0005's. `README.md` and the project guide: none.

## Smoke test

```bash
grep -c 'FACTORY_TRANSCRIPT_DIR=/srv/factory/' vm/setup.sh
grep -c 'cannot be written' vm/job-start.sh
uv run pytest tests/test_vm_setup.py tests/test_vm_job_start.py 2>&1 | tail -1
```

Expect: a number of at least `1`, a number of at least `1`, then a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: concrete. It names `vm/setup.sh` (step `transcripts`, option `--transcript-days <n>`, the folder, the `factory.env` line, the exact `tmpfiles.d` file name and rule line) and `vm/job-start.sh` (the exact message, status not 0, unset changes nothing). `src/` is unchanged, as it says.
   - Criteria: each is testable. Criterion 1 is table rows (default, 7 → `7d`, 0 → no line, no rule, no folder, `x` → refused with the option's name) plus the second run that changes nothing. Criterion 2 covers the writable folder, the missing folder, the folder that cannot be written, and the unset setting. Every rule has its failing side: `x` is refused, and the missing and unwritable folders end with the message. Criterion 3 is `make check`. Docs criterion 4 is the last one.
   - Smoke test: runnable. The two greps return counts. The pytest command has no `-q`, and `pyproject.toml` `addopts` already sets `-q`, so `tail -1` shows the `... passed` summary line, which the Expect line can be checked against.
   - Architecture: shell scripts under `vm/` only, with no `src/` change and no cloud client. This matches decision 10 and the guide's "site's own folder" design.
   - Scope: inside the feature's scope (the S0007 line), and it touches nothing in Out of scope (creating a bucket stays the operator's step, described in the guide).
   - Notes for the tester, not questions: `--transcript-days` with a negative value is not spelled out; treat it like `x` (refused). The Interface does not say whether `0` removes a folder an earlier run made, so test only that none is made.
4. factory: started tests as vm.
5. tester: Tests written for criteria 1 and 2. Both new modules import; they fail on purpose, for the right reasons, and `make lint` is green.

   - criterion 1 (the option's values: default, `7`, `0` accepted; `x`, `-1`, `1.5`, empty and no value refused with the option's name): tests/test_vm_setup_transcripts.py::test_the_transcript_days_take_a_whole_number_of_zero_or_more; the help text names the option: tests/test_vm_setup_transcripts.py::test_the_usage_names_the_transcript_days
   - criterion 1 (default of 30 days, set before the option parsing): tests/test_vm_setup_transcripts.py::test_the_transcript_days_default_to_thirty_before_the_option_parsing
   - criterion 1 (folder made with `install -d -o factory -g factory -m 0700`, only when missing, only when days is not 0): tests/test_vm_setup_transcripts.py::test_the_step_makes_the_folder_factory_s_with_0700_only_when_it_is_missing
   - criterion 1 (the `FACTORY_TRANSCRIPT_DIR=/srv/factory/$instance/transcripts` line written once, only when days is not 0): tests/test_vm_setup_transcripts.py::test_the_setting_s_line_is_written_once_and_only_with_days
   - criterion 1 (`/etc/tmpfiles.d/factory-$instance-transcripts.conf` holds the rule `d /srv/factory/$instance/transcripts 0700 factory factory ${days}d`): tests/test_vm_setup_transcripts.py::test_the_tmpfiles_rule_says_the_folder_its_owner_mode_and_age
   - criterion 1 (second run changes nothing: the rule is compared before it is written, never written when days is 0, and the step has a "found" text): tests/test_vm_setup_transcripts.py::test_the_tmpfiles_rule_is_written_only_with_days_and_when_its_text_differs
   - criterion 2 (writable folder and unset setting start as before, and the writable folder is left empty): tests/test_vm_job_start_transcripts.py::test_a_writable_or_unset_transcript_folder_starts_the_factory_as_before
   - criterion 2 (missing and read-only folder end with `transcript folder <path> cannot be written`, a status that is not 0, and no factory-run): tests/test_vm_job_start_transcripts.py::test_a_transcript_folder_that_cannot_be_written_ends_the_start
   - criterion 3: `make check`; no test of its own. None of these tests touches a cloud.

   Why the setup tests read the script's text: `vm/setup.sh` refuses to run without root, so a test can only run it as far as its option and root checks. Earlier stories' `vm/setup.sh` tests also read the script's text (test_vm_setup_idle_shutdown.py, test_vm_setup_text.py), and these follow them. So the second run that changes nothing is tested through the script's guards, not by running it twice. My tests find the step by its `setup: transcripts: ` text, because `STEPS` in tests/vm_support.py does not name it; I did not change that shared list. Following the intake's note, a negative day count is refused like `x`; when days is 0, the tests check only that nothing is made, not that a folder from an earlier run is removed. The read-only job-start row is skipped when the tests run as root.

   Note for the coder: tests/test_vm_job_start.py::test_the_steps_run_in_order_and_factory_run_replaces_the_script expects the exact list of `job-start: <step>` lines, so a new printed step line in job-start.sh would break it.

   Run (`uv run pytest -q` on the two files): 10 failed, all for the right reason: `setup.sh` rejects `--transcript-days` as an unknown word, the help text doesn't name it, the step, the line and the rule are not in the script yet, and `job-start.sh` doesn't check the folder yet. The default, unset and writable rows pass, as they should before the change.

   Files created: tests/test_vm_setup_transcripts.py, tests/test_vm_job_start_transcripts.py. Modules the test run could not import: none. No earlier test file changed.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: Built the transcript folder for both kinds of site, in shell only. `src/` is unchanged.

   - `vm/setup.sh`:
     - The new option `--transcript-days <n>` is in the usage line and its help text, with a default of `transcript_days=30` set before the option parsing.
     - A new `need_days` refuses an empty value or anything that is not a whole number, with the option's name. That covers `x`, `-1` and `1.5`; a missing value is refused by the existing `need_value`.
     - `factory.env` gets `FACTORY_TRANSCRIPT_DIR=/srv/factory/$instance/transcripts` only when days > 0. The line is staged before `FACTORY_IDLE_SHUTDOWN_MINUTES`, because the idle-shutdown test wants that setting to stay last.
     - A new step `transcripts` comes after `service` and before the `done` lines. When days > 0 it:
       - refuses a planted link, as the `folders` step does;
       - makes `$base/transcripts` with `install -d -o factory -g factory -m 0700` only when `owned_with_mode` says it is not already so;
       - stages the rule `d /srv/factory/$instance/transcripts 0700 factory factory ${days}d` and installs `/etc/tmpfiles.d/factory-$instance-transcripts.conf` only when `unchanged` says it differs;
       - prints its "found ... unchanged" text, so a second run changes nothing.

       With 0 it prints `not asked; no transcript is kept` and makes and writes nothing.
   - `vm/job-start.sh`: when `FACTORY_TRANSCRIPT_DIR` is set, it checks after the token-file handling and before any install. The folder must exist, and a probe file `.job-start-probe` must be creatable and removable there. Otherwise the start stops with `job-start: transcript folder <path> cannot be written` and status 1. When the setting is unset nothing changes, and no new `job-start: <step>` line is printed, so the exact step list in `tests/test_vm_job_start.py` holds.

   Main choice: the step is placed last, after `service`, and not near `folders`. `tests/vm_support.py` `STEPS` does not name `transcripts`, and `step_texts` cuts each listed step from the end of the previous listed one. A step placed between two listed steps would have joined the next step's text and could break those step-text tests. Rejected: placing it after `folders` (the folder would be made before the setting is written, which reads more naturally) for that reason. The setting's line still lives in the `environment` step, where `factory.env` is staged.

   Two implementation details forced by tests or the shell:
   - The rule is staged with `echo ... | stage` and not a heredoc. A heredoc body at column 0 hides the enclosing `if` from the tests' indentation-based guard check.
   - The probe write is in a subshell, `(: >"$probe")`. dash exits the whole script when a redirection on the special builtin `:` fails.

   Noticed, not touched:
   - With `--transcript-days 0`, a rule file an earlier run wrote is left in place. The Interface and the intake left this open. Such a leftover `d` rule would make systemd-tmpfiles create the folder again at boot, though without the setting no transcript is written there. Removing it, as the `poweroff` step does with its right, would be a small follow-up if the human wants it.
   - `--transcript-days 00` counts as 0.

   Refactor pass: I read the diff and found nothing to change. The new code reuses the existing helpers (`need_value`, `owned_with_mode`, `stage`, `unchanged`, `changed`, `said`, `stop`).

   The `docs:` criterion (operator guide *Transcripts*) is the documenter's.

   `make check`: green (lint, types, layers, sast, secrets, licenses, test 88.4 s, `check: green`).

   `check`: check: green
   `duplicates`: duplicates: 4 new, 41 known, 2 gone
