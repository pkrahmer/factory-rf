---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 499
comments_read: [6582236900, 6582370543]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-02T16:17:59.618427Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-02T16:17:59.624853Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-02T16:18:21.287346Z'
  stage: intake
  run: f866530a38794b1ea39e8aa27ed0cdc1
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-02T16:22:46.098830Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-02T16:23:04.242056Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-02T16:23:29.255773Z'
  stage: intake
  run: 6c6170e248fe41449e59831ad3e4e4d7
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-02T16:23:50.781477Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-02T16:25:31.302428Z'
  stage: tests
  run: 7a1a9040efce4d149d52b208dbc7080c
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-02T16:27:53.347742Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-02T16:28:11.454339Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-02T16:30:06.029465Z'
  stage: tests
  run: d28fb466ff55410d9466210cb6030d16
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-02T16:30:27.458755Z'
  stage: doing
- number: 13
  speaker: factory
  kind: crash
  at: '2026-11-02T16:34:54.434395Z'
  stage: doing
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-02T16:34:56.584717Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-11-02T16:38:44.009132Z'
  stage: doing
  run: 77b28f577c1840fd915159af68a31201
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-02T16:39:05.444119Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-11-02T16:40:35.219675Z'
  stage: review
  run: 47dbff94d7424241b09fee1b6375ca31
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-02T16:40:56.214244Z'
  stage: doing
- number: 19
  speaker: coder
  kind: result
  at: '2026-11-02T16:41:09.062150Z'
  stage: doing
  run: 8cf95e6f6f8a4962bf038762c6561911
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-02T16:41:30.255582Z'
  stage: tests
- number: 21
  speaker: tester
  kind: result
  at: '2026-11-02T16:43:28.864250Z'
  stage: tests
  run: beba9797f40947aa809f89951da3cc1d
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-02T16:43:49.854097Z'
  stage: doing
- number: 23
  speaker: coder
  kind: result
  at: '2026-11-02T16:47:02.526009Z'
  stage: doing
  run: 554ced8e0b8b45ebbc5158c4bccec89c
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-02T16:47:23.595988Z'
  stage: review
- number: 25
  speaker: reviewer
  kind: result
  at: '2026-11-02T16:48:05.542172Z'
  stage: review
  run: 7dfb0b3190e54dbfbbe9ce33470b17aa
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-02T16:48:26.587671Z'
  stage: docs
- number: 27
  speaker: documenter
  kind: result
  at: '2026-11-02T16:49:18.922529Z'
  stage: docs
  run: 58ed0c71fd10497e8dedd7e70510521f
---

# The job script sets its own PATH, keeps the token in a private folder and exports all four proxy spellings

## Description

The first whole run of the factory in a Cloud Run job (2026-11-02, `planning/cloud-sandbox/TRIAL-2-F0001-IN-A-JOB.md`) needed three workarounds in the job's configuration because `vm/job-start.sh` leaves three things to the operator. It never puts the tools folder it builds on the `PATH`, so the preflight stops on `tool:uv` (the VM's service file sets it, the job script does not). It takes the hosting token from the path the job gives, and a mounted secret's folder is read-only at mode 0555, so the preflight's `token-file` item, which wants the folder private, can never pass for a token mounted as the guide says. And it exports only the two HTTPS spellings of the proxy, while the stage image's `apt-get` fetches over plain HTTP, so the build cannot resolve its package host. This story makes the script do all three: `PATH` begins with `<root>/tools/bin`; a token whose folder is not private is copied into a private folder of the instance and `FACTORY_TOKEN_FILE` names the copy; and a given proxy is exported in all four spellings. It changes nothing else of the script and no step's name or order.

## Interface

`vm/job-start.sh`

- After the `inputs` step the script exports `PATH` as `<root>/tools/bin` followed by `:` and the `PATH` it was started with (unchanged, not de-duplicated). `<root>` is the one the script already derives (`FACTORY_JOB_ROOT`, default `/srv/factory/<instance>`).
- In the `inputs` step, after the check that `FACTORY_TOKEN_FILE` is a readable file: when the file's folder is not owned by the user running the script, or has any permission bit for group or others, the script makes `<root>/secrets` (mode 0700, owner the running user), copies the file to `<root>/secrets/hosting-token` with mode 0600 (content byte for byte, the original untouched) and sets and exports `FACTORY_TOKEN_FILE` to the copy. It prints `job-start: token-file: copied to <root>/secrets`. When the folder is owned by the running user and has no bit for group or others, nothing is copied, nothing is printed and `FACTORY_TOKEN_FILE` is as given.
- The folder is made with `mkdir -p` followed by `chmod 0700`, so an existing `<root>/secrets` ends at mode 0700; the copy replaces an existing `hosting-token` (mode 0600 again).
- A failing `mkdir`, `cp` or `chmod` of the copy stops with `job-start: token-file: failed`, status 1.
- The tests cover only the mode bits of the token's folder; the ownership clause stays in the Interface and is untested by design (a normal user cannot make a folder another user owns, and there is no stand-in for `stat` or `id`).
- In the `proxy` step, when `HTTPS_PROXY` or `https_proxy` is set (`HTTPS_PROXY` when it is not empty, else `https_proxy`), all four of `HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY` and `http_proxy` are exported with that value, except that a `HTTP_PROXY` or `http_proxy` the job set itself and not empty keeps its own value (one that is set but empty counts as not set and gets the value). The `apt` configuration file written by the step is unchanged.

Tests: the existing job-start test modules and `tests/vm_support.py` are the pattern; a new `tests/test_vm_job_start_environment.py` holds this story's, with the stand-ins of `JOB_STAND_INS` recording the environment they are started with. No earlier test changes.

## Acceptance criteria

1. The environment `factory-run` is started with has a `PATH` whose first entry is `<root>/tools/bin` and whose remaining entries are the `PATH` the script was started with, in order.
2. The environment the `podman build` stand-in is started with has the same `PATH`.
3. A token file in a folder that has mode 0755 is copied: `FACTORY_TOKEN_FILE` in the environment of `factory-run` is `<root>/secrets/hosting-token`, that folder has mode 0700 and the file mode 0600, the copy equals the original, the original is unchanged, and standard output holds the line `job-start: token-file: copied to <root>/secrets`.
4. A token file in a folder of mode 0700 owned by the running user is not copied: `FACTORY_TOKEN_FILE` in the environment of `factory-run` is the path given, `<root>/secrets` does not exist, and no `token-file` line is printed. A folder of mode 0750 and a folder of mode 0705 are copied (two more rows of the test of criterion 3: any bit for group or others counts).
5. The token's text is in no line the script prints (a token file holding `TOKENMARK` and a search of standard output and standard error).
6. A copy that fails (`<root>/secrets` made impossible by a file of that name) stops with `job-start: token-file: failed` on standard error and status 1, and `factory-run` is not started.
7. A missing or unreadable token file stops as before: `job-start: FACTORY_TOKEN_FILE is not a file`, status 2 (the existing behaviour, one row).
8. With only `https_proxy=P` given, the environment of the `podman build` stand-in has `HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY` and `http_proxy` all equal to `P`; with `HTTPS_PROXY=P` only, the same; with `https_proxy=P` and `http_proxy=Q`, `http_proxy` stays `Q` and `HTTP_PROXY` is `P`; with `https_proxy=P` and `HTTP_PROXY=Q`, `HTTP_PROXY` stays `Q` and `http_proxy` is `P`; with `HTTPS_PROXY=` (empty) and `https_proxy=P`, all four are `P`; with `HTTPS_PROXY=A` and `https_proxy=B`, all four are `A`; with `https_proxy=P` and `http_proxy=` (empty), all four are `P` (a plain-HTTP variable that is set but empty counts as not set) (seven rows of one parametrized test).
9. With no proxy given, none of the four is set in the environment of the stand-ins and the `apt` configuration file is not written (the existing behaviour, one row).
10. The steps still print in their order and names: `inputs`, `proxy`, `packages`, `runc`, `metadata`, `directories`, `storage`, `code`, `tools`, `image`, `token`, `start` (the existing tests keep passing unchanged).
11. A second run: `<root>/secrets` already exists with mode 0755 and holds an old `hosting-token`, and the token file's folder is not private: afterwards `<root>/secrets` has mode 0700, `hosting-token` has mode 0600 and holds the new token.
12. `make check` stays green.
13. docs: `docs/operator-guide.md` in *What the job needs*: the proxy sentence says that the script exports all four spellings and why (the image's package manager fetches over HTTP); the secrets sentence says that a mounted secret may be given as it is, because the script copies it into a private folder when its own folder is not private; the *Environment* table's `FACTORY_TOKEN_FILE` row says so too; *The steps* names the `PATH`; `README.md` and the other documents: none.

## Smoke test

The script's behaviour is proved by the tests with stand-ins; a real start needs a job. These blocks check what a container can: that the script is valid and that its first refusal is unchanged.

```bash
sh -n vm/job-start.sh; echo "exit $?"
```

Expect: one line, `exit 0`.

```bash
env -i PATH="$PATH" sh vm/job-start.sh; echo "exit $?"
```

Expect: two lines, `job-start: FACTORY_INSTANCE is not set` (on standard error) and `exit 2`.

```bash
grep -c 'tools/bin' vm/job-start.sh
```

Expect: one line holding a number of at least 2 (the tools step and the new `PATH` line both name the folder).

## Journal

1. 2026-11-02 human: created.
2. factory: started intake as vm.
3. intake: Questions (format check passed; the Interface, smoke test, architecture and scope are otherwise fine):

   1. Interface, proxy step: "the first of the two that is not empty, as now" has no criterion for the case where both `HTTPS_PROXY` and `https_proxy` are set to different values, or where the first is set but empty. Criterion 8 has three rows and none of them covers it. I would add a row: `HTTPS_PROXY=` (empty) with `https_proxy=P` gives P everywhere, and `HTTPS_PROXY=A` with `https_proxy=B` gives A everywhere (with the existing precedence). Please confirm the precedence and add the criterion.

   2. Interface, proxy step: the exception "a `HTTP_PROXY` or `http_proxy` the job set itself keeps its own value" is tested only for `http_proxy=Q`. The `HTTP_PROXY=Q` side has no criterion. I would add a row with `https_proxy=P` and `HTTP_PROXY=Q`, where `HTTP_PROXY` stays Q and `http_proxy` is P. Is that right? Also, what happens when one is set and empty: is it kept empty or overwritten?

   3. Interface, token step: the condition "folder not owned by the user running the script" has no criterion. Criterion 4 covers only the permission-bit side. Either add a criterion (which a non-root test can only do with a stand-in `stat` or `id`, so please say how) or state that only the mode bits are tested and the ownership clause is untested by design.

   4. Interface: "A failing `mkdir`, `cp` or `chmod`" stops with `job-start: token-file: failed`. Criterion 6 covers only `mkdir` (a file named `<root>/secrets`). Is a test of `cp` and `chmod` failing wanted, or is one row enough? I would choose one row.

   5. Criterion 3 says the copy has mode 0600 and `<root>/secrets` has mode 0700, but the Interface does not say what happens when `<root>/secrets` already exists with another mode, for example on a restart in the same instance. Does `mkdir -p` plus `chmod 0700` apply, or is it an error? I would choose `mkdir -p` followed by `chmod 0700`, and a criterion for a second run.
4. 2026-11-02 human: 1. Confirmed: `HTTPS_PROXY` when it is not empty, else `https_proxy`. Add both rows as you propose (`HTTPS_PROXY=` empty with `https_proxy=P` gives P everywhere; `HTTPS_PROXY=A` with `https_proxy=B` gives A everywhere).
   2. Yes, add the row (`https_proxy=P`, `HTTP_PROXY=Q`: `HTTP_PROXY` stays Q, `http_proxy` is P). A plain-HTTP variable that is set but empty counts as not set and gets P; add that as one more row.
   3. The ownership clause stays in the Interface and is untested by design: a test as a normal user cannot make a folder another user owns, and no stand-in for `stat` or `id`. Only the mode bits are tested; say so in one sentence under the Interface.
   4. One row is enough.
   5. `mkdir -p` followed by `chmod 0700`, and the copy replaces an existing `hosting-token` (mode 0600 again). Add a criterion for a second run: `<root>/secrets` already there with mode 0755 and an old token in it gives mode 0700 and the new token.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: `vm/job-start.sh` names concrete behaviour per step (PATH after `inputs`, token copy, proxy exports). Carried in from journal entry 4 (the human's answer): `mkdir -p` then `chmod 0700` and the copy replaces an existing token; the proxy precedence (`HTTPS_PROXY` when not empty, else `https_proxy`) and that an empty plain-HTTP variable counts as not set; one sentence that only the mode bits are tested and the ownership clause is untested by design.
   - Criteria: each is testable by one test function or one parametrized test. From entry 4 I added the rows to criterion 8 (now seven rows: `HTTP_PROXY=Q`, empty `HTTPS_PROXY`, `HTTPS_PROXY=A` with `https_proxy=B`, empty `http_proxy`) and a new criterion 11 for the second run (existing 0755 folder with an old token). `make check` and `docs:` are now criteria 12 and 13. Failing sides are covered: criterion 6 (a failing copy, one row is enough per the human), 7 (missing file) and 4 (private folder not copied). A failing `cp` or `chmod` is not tested, by the human's word.
   - Smoke test: the three commands are runnable. Each `Expect:` is checkable, and none runs pytest.
   - Architecture: a shell script under `vm/`, tests under `tests/` with `tests/vm_support.py` stand-ins. This is consistent with `CLAUDE.md`, and the coder's write paths include `vm/*`.
   - Scope: within feature F0048's S0002 scope (PATH, private token copy, four proxy spellings), and not in its Out of scope. No earlier test changes.
7. factory: started tests as vm.
8. tester: Question: an earlier test conflicts with the new copy behavior, and making it pass again needs a test change I am not allowed to make without your approval.

   `run_job_start` in `tests/vm_support.py` writes its default token to `<tmp>/secrets/hosting-token` and creates that folder with a plain `mkdir()`. Under the usual umask 022 (this VM's umask), the folder gets mode 0755. Once the coder implements the Interface, every earlier job-start run takes the copy path and writes the token text into `<root>/secrets/hosting-token`. `tests/test_vm_job_start.py::test_the_token_is_never_printed_written_or_passed_on_a_command_line` searches every file under `full_run.root` for `HIDDEN_TEXT` and expects none. So that test turns red once the coder implements the Interface. This contradicts criterion 10 ("the existing tests keep passing unchanged") and the Interface's "No earlier test changes". The coder cannot fix it, because the coder never edits tests.

   Options:
   (a) In `run_job_start` (`tests/vm_support.py`), add `token.parent.chmod(0o700)` after the token folder is made. The earlier runs then take the no-copy path, and the earlier test still checks the same thing. No earlier test file changes; only the shared helper does.
   (b) Change the earlier test so it skips `<root>/secrets/hosting-token` when it searches for written token text. This weakens what it checks.
   (c) Leave both as they are. The earlier test then goes red and the story cannot pass `make check`.
   I would choose (a): one line in the shared helper, every earlier test name and check unchanged. Please give the word for it. (`tests/vm_support.py` is a shared helper this story did not write, and the standing leave only covers moving helpers, so I need your approval.)

   The tests for the story's criteria are already written, in the new file `tests/test_vm_job_start_environment.py`. They pass their own token file, so they work the same under (a), (b) or (c):
   criterion 1: tests/test_vm_job_start_environment.py::test_factory_run_starts_with_the_tools_folder_first_on_the_path
   criterion 2: tests/test_vm_job_start_environment.py::test_the_image_build_starts_with_the_tools_folder_first_on_the_path
   criterion 3: tests/test_vm_job_start_environment.py::test_a_token_is_copied_into_a_private_folder_only_when_its_folder_is_not_private (rows 0755, 0750, 0705)
   criterion 4: same test, row 0700; the 0750 and 0705 rows are the copied rows above
   criterion 5: tests/test_vm_job_start_environment.py::test_the_token_s_text_is_never_printed_when_it_is_copied
   criterion 6: tests/test_vm_job_start_environment.py::test_a_failing_copy_stops_the_script_before_factory_run
   criterion 7: tests/test_vm_job_start_environment.py::test_a_missing_token_file_stops_the_script_as_before
   criterion 8: tests/test_vm_job_start_environment.py::test_a_given_proxy_reaches_the_image_build_under_all_four_names (seven rows)
   criterion 9: tests/test_vm_job_start_environment.py::test_without_a_proxy_no_stand_in_sees_one_and_apt_is_not_configured
   criterion 10: the existing tests/test_vm_job_start.py::test_the_steps_run_in_order_and_factory_run_replaces_the_script, unchanged
   criterion 11: tests/test_vm_job_start_environment.py::test_a_second_run_makes_an_existing_secrets_folder_private_and_replaces_the_old_token

   Files created: `tests/test_vm_job_start_environment.py`. No earlier test file was changed. Every module imported, with no collection errors. My one run (`uv run pytest -q` on the new file) ended red as intended: the copy, `PATH` and proxy tests fail on wrong results, since the script does not do these yet. `make lint` is green. I renamed two constants (`GIVEN_CONTENT`, `OLD_CONTENT`) because ruff's S105 rule flagged the names as hardcoded passwords. Once you answer, the next run makes the agreed change to the helper (if you choose (a) or (b)) and ends with `doing`.
9. 2026-11-02 human: (a), granted: add `token.parent.chmod(0o700)` in `run_job_start` of `tests/vm_support.py` after the token folder is made, so the earlier runs keep the no-copy path; every earlier test keeps its name and check. Name the helper change in your entry.
10. factory: started tests as vm.
11. tester: I made the helper change the human approved in entry 9. In `run_job_start` of `tests/vm_support.py`, the line `token.parent.chmod(0o700)` now follows the `mkdir()` of the default token folder. Earlier job-start runs therefore keep the no-copy path, so `tests/test_vm_job_start.py::test_the_token_is_never_printed_written_or_passed_on_a_command_line` still finds no token text under the root once the copy is implemented. Every earlier test keeps its name and its check. The only earlier test file changed is `tests/vm_support.py`, as the human approved (not under the standing leave).

    The tests for the criteria were written and committed in the previous run and are unchanged:
    criterion 1: tests/test_vm_job_start_environment.py::test_factory_run_starts_with_the_tools_folder_first_on_the_path
    criterion 2: tests/test_vm_job_start_environment.py::test_the_image_build_starts_with_the_tools_folder_first_on_the_path
    criterion 3: tests/test_vm_job_start_environment.py::test_a_token_is_copied_into_a_private_folder_only_when_its_folder_is_not_private (row 0755)
    criterion 4: same test, row 0700 (not copied) and rows 0750 and 0705 (copied)
    criterion 5: tests/test_vm_job_start_environment.py::test_the_token_s_text_is_never_printed_when_it_is_copied
    criterion 6: tests/test_vm_job_start_environment.py::test_a_failing_copy_stops_the_script_before_factory_run
    criterion 7: tests/test_vm_job_start_environment.py::test_a_missing_token_file_stops_the_script_as_before
    criterion 8: tests/test_vm_job_start_environment.py::test_a_given_proxy_reaches_the_image_build_under_all_four_names (seven rows)
    criterion 9: tests/test_vm_job_start_environment.py::test_without_a_proxy_no_stand_in_sees_one_and_apt_is_not_configured
    criterion 10: tests/test_vm_job_start.py::test_the_steps_run_in_order_and_factory_run_replaces_the_script, existing and unchanged
    criterion 11: tests/test_vm_job_start_environment.py::test_a_second_run_makes_an_existing_secrets_folder_private_and_replaces_the_old_token

    Files: `tests/test_vm_job_start_environment.py` was created in the previous run; `tests/vm_support.py` was changed in this one. Every module imported; there were no collection errors.

    I made one run, `uv run pytest -q` on the new file and `tests/test_vm_job_start.py`. It ended red as intended: the new `PATH`, copy and proxy tests fail on wrong results, because `vm/job-start.sh` does not do those things yet. The failures it printed were all from the new file. `make lint` is green.

    `lint`: lint: green (0.1 s)
    `test`: FAILED tests/test_vm_job_start_environment.py::test_a_second_run_makes_an_existing_secrets_folder_private_and_replaces_the_old_token - AssertionError: assert 493 == 448
12. factory: started doing as vm.
13. factory: crash 1: the run of stage doing ended without a result. Its work is discarded back to commit 70d62a4b979f9f2ddc4eba0f8801ad597644be92.
14. factory: started doing as vm.
15. coder: I built all three changes in `vm/job-start.sh`. No other file changed. `make check` is green, and the new `tests/test_vm_job_start_environment.py` and the existing `tests/test_vm_job_start.py` both pass.

    - **Token copy.** It sits in the `inputs` step, after `root` is derived. The script checks whether the token's folder is private with `find "$token_folder" -maxdepth 0 -user "$(id -u)" ! -perm /077`, which prints nothing unless the folder is owned by the running user and has no bit for group or others. If it is not private, the script runs `mkdir -p` and `chmod 0700` on `<root>/secrets`, copies the token there as `hosting-token`, and runs `chmod 0600` on the copy. Each of these four commands ends in `|| failed token-file`, which stops with `job-start: token-file: failed`, status 1. The script then exports `FACTORY_TOKEN_FILE` as the copy and prints `job-start: token-file: copied to <root>/secrets` with `printf`. I used `printf` rather than `step` so the line does not read as a step of its own.
    - **PATH.** After the `inputs` step the script exports `PATH="$root/tools/bin:$PATH"`.
    - **Proxy.** In the `proxy` step, besides the two HTTPS names, `HTTP_PROXY` and `http_proxy` are set through the existing `default` helper. It keeps a value the job gave that is not empty, fills in one that is unset or empty, and exports the name. The `apt` file is unchanged.

    Main choice: I tested ownership and mode in one `find` expression. I rejected `stat -c '%u %a'` compared with `id -u` plus octal arithmetic in sh. That would take more lines, and setgid/sticky digits would make `%a` awkward to parse.

    I copied with `cp` and `chmod`, not `install -m`, because `install` is one of the test stand-ins and would not really copy the file. That is also a sound reason in the real script: the steps call `install` only for binaries.

    Refactor pass: I read the diff, which is 16 added lines, and found nothing to change.

    The journal changed nothing in the Description. The human's answers were already folded in at intake, and the helper change in `tests/vm_support.py` from entries 9 and 11 is the tester's.

    Noticed, not touched: between `cp` and `chmod 0600`, a replaced old `hosting-token` keeps its old mode for a moment. That is harmless because the folder is already 0700.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
16. factory: started review as vm.
17. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (vm/job-start.sh +16, tests/vm_support.py +1, new tests/test_vm_job_start_environment.py) against the work item. I did not run `make check`: the journal records it green after the coder (entry 15).

    Acceptance criteria: criteria 1 to 11 each have a test that checks what the criterion says. The token test has rows 0755, 0750, 0705 (copied) and 0700 (not copied). The proxy test has the seven rows as one parametrized test. Criterion 11 has the second-run test and criterion 6 the failing copy. The ownership clause and a failing `cp` or `chmod` are untested by the human's word (entry 4).

    The script matches the Interface:
    - the folder's privacy is tested with one `find -maxdepth 0 -user "$(id -u)" ! -perm /077`;
    - `mkdir -p` + `chmod 0700`, `cp`, `chmod 0600`, each `|| failed token-file`;
    - `PATH="$root/tools/bin:$PATH"` is exported after `inputs`;
    - `default HTTP_PROXY` / `default http_proxy` keep a non-empty value the job set and fill an empty one;
    - the apt file is unchanged.

    Architecture holds: a shell script under vm/ and no src/ change. Security is fine: no token in any output, no command built from a string, no silencing marker.

    Findings:
    1. tests/test_vm_job_start_environment.py:15: `_mode` is a second copy of the helper `_mode` in tests/test_tmp_path_reopening.py:52 (`stat.S_IMODE(path.lstat().st_mode)`; the new copy differs only in using `stat`). Fix: the tester moves it once into a shared module under tests/ (for example tests/tmp_path_support.py, or a new `*_support.py`) and both modules import it. Under the standing leave, test_tmp_path_reopening.py keeps its test names and checks. The `lstat` form serves the new tests too, since the token folder and the copy are not symbolic links.

    Earlier tests:
    - tests/vm_support.py: changed under the human's leave, journal entry 9 (`token.parent.chmod(0o700)` in `run_job_start`, only that line).
18. factory: started doing as vm.
19. coder: I changed no code. The reviewer's only finding (entry 17, finding 1) is a copied test helper, so it is a change to tests. `CLAUDE.md` *Tests* gives the standing leave to move a shared test helper, so the tester makes this change.

    The move: `_mode` in `tests/test_vm_job_start_environment.py:15` is a second copy of `_mode` in `tests/test_tmp_path_reopening.py:52`. It should go once into one shared support module under `tests/`. That can be the existing `tests/tmp_path_support.py` or a new `*_support.py`, keeping the `stat.S_IMODE(path.lstat().st_mode)` form. Both modules then import it from there. The earlier test file to change is `tests/test_tmp_path_reopening.py`, and every test in it keeps its name and its check.

    `vm/job-start.sh` stays as it was after entry 15. The journal changed nothing in the Description.
20. factory: started tests as vm.
21. tester: I moved the shared test helper that the reviewer's finding 1 (entry 17) and the coder's entry 19 name. The move falls under the standing leave in `CLAUDE.md` *Tests*: one shared place, earlier tests keep their names and checks.

    - `tests/tmp_path_support.py`: I added the public helper `file_mode(path)`, which returns `stat.S_IMODE(path.lstat().st_mode)` (the `lstat` form, as the coder asked). The module's private `_add` used the same expression, so it now calls `file_mode` too, and there is one copy.
    - `tests/test_tmp_path_reopening.py` (an earlier story's test file, changed under the standing leave): I removed its `_mode`. Its three uses now call `file_mode` from `tmp_path_support`, and the `stat` import it no longer needs is gone. `ruff format` re-wrapped one assertion. Every test keeps its name and its check.
    - `tests/test_vm_job_start_environment.py`: I removed its `_mode` (the `path.stat()` copy) and its `stat` import, and its uses call `file_mode`. The token folder and the copy are not symbolic links, so `lstat` checks the same thing here.

    The criterion → test mapping is unchanged from entry 11. No new test file was created. Every module imported.

    My one run, `uv run pytest -q tests/test_tmp_path_reopening.py tests/test_vm_job_start_environment.py`, passed all 31 tests, because the script is already built. `make lint` is green.

    `lint`: lint: green (0.1 s)
    `test`: test: green (75.1 s)
22. factory: started doing as vm.
23. coder: Round 1. I changed no code. The reviewer's only finding (entry 17, finding 1) was the copied `_mode` test helper. The tester has fixed it under the standing leave (entry 21): it is now `file_mode` in `tests/tmp_path_support.py`, used by `tests/test_tmp_path_reopening.py` and `tests/test_vm_job_start_environment.py`. Nothing in the code was left to change for this round.

    What I built is unchanged since entry 15, and all of it is in `vm/job-start.sh`:
    - **Token copy.** If the token's folder is not private (checked with one `find -maxdepth 0 -user "$(id -u)" ! -perm /077`), the script runs `mkdir -p` and `chmod 0700` on `<root>/secrets`, then `cp` and `chmod 0600` on the copy. Each of those commands stops with `job-start: token-file: failed` if it fails.
    - **PATH.** After `inputs` the script exports `PATH="$root/tools/bin:$PATH"`.
    - **Proxy.** `HTTP_PROXY` and `http_proxy` are filled through the existing `default` helper.

    Main choice: one `find` expression tests both owner and mode. I rejected `stat -c '%u %a'` plus octal arithmetic in sh, which would be longer and makes the setgid and sticky digits awkward to parse.

    Refactor pass: I found nothing to change. The working tree holds no uncommitted changes, and `make check` is green on the committed state (`check: green`, test: green 78.4 s).

    The journal changed nothing in the Description.

    Noticed, not touched: when the copy replaces an old `hosting-token`, the file keeps its old mode for a moment between `cp` and `chmod 0600`. This is harmless because the folder is already 0700.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
24. factory: started review as vm.
25. reviewer: Round 1 review. I reviewed `git diff main...HEAD -- . ':!factory'` against the work item. The diff changes `vm/job-start.sh` (+16), adds `tests/test_vm_job_start_environment.py` and changes `tests/tmp_path_support.py`, `tests/test_tmp_path_reopening.py` and `tests/vm_support.py`. I did not run `make check`: the journal records it green after the coder (entry 23).

    Acceptance criteria: each of criteria 1 to 11 has a test, and each test checks what its criterion says.
    - **Criteria 1 and 2:** the tests compare the whole `PATH` of the `factory-run` and `podman build` stand-ins with `<root>/tools/bin` followed by the starting `PATH`, in order.
    - **Criteria 3 and 4:** one parametrized test. The 0755, 0750 and 0705 rows are copied: the copy is the token file, the folder is 0700, the file is 0600, the original keeps its text and mode, and the line is printed. The 0700 row is not copied: the token file is as given, there is no `<root>/secrets` and no `token-file` line.
    - **Criteria 5, 6, 7, 9 and 11:** each has its own test, and each checks the status and output its criterion states.
    - **Criterion 8:** the seven rows are one parametrized test.
    - **Criterion 10:** the existing step-order test, unchanged.

    The ownership clause and a failing `cp` or `chmod` stay untested by the human's word (entry 4). The helper builds the environment from scratch, so no proxy from the host's environment can reach the no-proxy test.

    The script matches the Interface:
    - One `find -maxdepth 0 -user "$(id -u)" ! -perm /077` decides whether the folder is private.
    - `mkdir -p` and `chmod 0700` make the folder, then `cp` and `chmod 0600` make the copy. Each of the four ends in `|| failed token-file`.
    - `FACTORY_TOKEN_FILE` is exported as the copy, and the `copied to` line is printed with `printf`.
    - `PATH="$root/tools/bin:$PATH"` is exported after `inputs`.
    - `HTTP_PROXY` and `http_proxy` are filled through the existing `default` helper, which keeps a value the job set that is not empty and fills one that is empty.
    - The apt file and every step's name and order are unchanged.

    Architecture: no `src/` change. The script stays under `vm/` and the tests under `tests/`.

    Security: no secret, and no command built from a string. The token's text reaches no output. The diff adds no marker that silences a check.

    Quality: the comments say why. Round 0's finding is fixed: there is one `file_mode` in `tests/tmp_path_support.py`, and `_add` there uses it too.

    Work item: the Description matches what was built, and criterion 13 (`docs:`) still says what the documenter must write.

    no findings

    Earlier tests:
    - `tests/vm_support.py`: changed under the human's leave in journal entry 9 (`token.parent.chmod(0o700)` in `run_job_start`, only that line).
    - `tests/test_tmp_path_reopening.py`: changed under the standing leave to move a shared test helper. Its `_mode` was replaced by `file_mode` from `tmp_path_support`, and every test keeps its name and its check.
    - `tests/tmp_path_support.py`: the shared place, changed under the same standing leave. It gains `file_mode`, and `_add` uses it in place of the same expression.
26. factory: started docs as vm.
27. documenter: I changed one file, `docs/operator-guide.md`, in the Cloud Run job chapter. That is the only document the docs criterion names. I changed four places:
    - *Secrets are files*: I replaced the "has not been measured" sentence. A mounted secret may be given as it is. If its folder is not private, the script copies the token to `<root>/secrets/hosting-token` (folder 0700, file 0600), points `FACTORY_TOKEN_FILE` at the copy and prints `job-start: token-file: copied to <root>/secrets`. A private folder is used as it is. A failed copy stops with `job-start: token-file: failed`, status 1.
    - The environment table, `FACTORY_TOKEN_FILE` row: it now says the copy is made and used.
    - The environment table, proxy row: the script exports all four spellings, and the reason is that the stage image's package manager fetches over plain HTTP. `HTTPS_PROXY` wins when both are given and not empty. An `HTTP_PROXY` or `http_proxy` the job sets to a value that is not empty keeps its own value.
    - *The steps*: item 1 names the copy and the `PATH` (`<root>/tools/bin` first, then the starting `PATH`). Item 2 says the proxy step exports the four spellings.

    I checked the text against the diff of `vm/job-start.sh`. I did not run any example, because the changes are prose and the script's behaviour is proved by the tests. Every file I changed is a document, so I did not run `make check`. The factory's checks after this stage decide.

    I cross-read the rest of `docs/operator-guide.md`, including the VM sections: `PATH` in the service environment (line 653), the hosting-service token section and the preflight messages for `token-file`. They describe the VM and are current. The README and `docs/project-guide/` do not mention these behaviours, so they are current too. I found no mismatch between code and Interface, so I have no findings for the coder.

    I noticed nothing stale and unrelated.

    `check`: check: green (not run again: passed on tree 89cb77e40df4 at 2026-11-02T16:45:33Z)
    `secrets`: secrets: green (1.3 s)
    `documents`: documents ok
