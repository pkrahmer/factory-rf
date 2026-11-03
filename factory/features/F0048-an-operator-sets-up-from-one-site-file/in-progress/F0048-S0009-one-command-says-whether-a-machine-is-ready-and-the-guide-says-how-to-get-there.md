---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 509
comments_read: [6592609715, 6592698453, 6592936353]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T01:01:53.471788Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T01:01:53.478624Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-03T01:02:15.556378Z'
  stage: intake
  run: 1e69e63922dd4fe6a58b4fc73d4e0894
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-03T01:06:10.660287Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-03T01:06:13.682491Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-03T01:06:35.749546Z'
  stage: intake
  run: afc8017aa8f04c3485c78370c4dde402
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-03T01:06:41.134646Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-03T01:07:58.006789Z'
  stage: tests
  run: ae9f74736bc640588b1213177100a1fe
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-03T01:09:46.791026Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-03T01:09:51.656850Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-03T01:15:22.259538Z'
  stage: tests
  run: 12340214e36a4eedb4862d3d54672219
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-03T01:15:28.090101Z'
  stage: doing
- number: 13
  speaker: coder
  kind: question
  at: '2026-11-03T01:22:32.985507Z'
  stage: doing
  run: fb3ec15861784b0997b731fc9fa8f97f
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-11-03T01:26:26.466973Z'
  stage: doing
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-03T01:26:29.258714Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-11-03T01:29:53.078649Z'
  stage: doing
  run: 95856af522d841e9978866485cd9a551
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-03T01:29:58.736350Z'
  stage: review
- number: 18
  speaker: reviewer
  kind: result
  at: '2026-11-03T01:32:28.117655Z'
  stage: review
  run: d26a6214f54a40cfbc75343f85f9e351
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-03T01:32:34.048929Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-11-03T01:35:09.674496Z'
  stage: doing
  run: 7eea0fd2b95749af8d67a00f7342d307
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-03T01:35:15.436317Z'
  stage: tests
- number: 22
  speaker: tester
  kind: result
  at: '2026-11-03T01:36:03.948619Z'
  stage: tests
  run: fd49c2464db245938ab01ebeb9c7059d
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-03T01:36:09.669143Z'
  stage: doing
- number: 24
  speaker: coder
  kind: result
  at: '2026-11-03T01:39:35.761655Z'
  stage: doing
  run: e0101d5474a54274ab7a6b70213a685d
- number: 25
  speaker: factory
  kind: started
  at: '2026-11-03T01:39:41.391763Z'
  stage: review
- number: 26
  speaker: reviewer
  kind: result
  at: '2026-11-03T01:41:40.119290Z'
  stage: review
  run: 35f639ca7df145a0baa23a8c5dfb93cc
- number: 27
  speaker: factory
  kind: started
  at: '2026-11-03T01:41:45.719151Z'
  stage: docs
- number: 28
  speaker: documenter
  kind: result
  at: '2026-11-03T01:43:02.626926Z'
  stage: docs
  run: c1437a7a857247e3a6949bb638ed9aa8
- number: 29
  speaker: factory
  kind: started
  at: '2026-11-03T01:43:09.060525Z'
  stage: smoke-test
- number: 30
  speaker: smoke-tester
  kind: result
  at: '2026-11-03T01:43:38.509650Z'
  stage: smoke-test
  run: 2519927d96964f9cbdf50735c8c7a11f
---

# One command says whether a machine is ready, and the guide says how to get there

## Description

A fresh setup has failed in small ways: a token command that prints nothing, a secret the identity cannot see, a code reference that does not exist, a `NO_PROXY` that names the code host (the guide forbids it) or leaves out the model API's host (opencode then hangs for 79 seconds), a repository the token can read but not push to. Each cost a failed start. This story adds `site check` to the command of S0001: a list of read-only checks, one line each, that says `ok` or `FAIL <name>: <detail>` and exits 0 only when nothing failed, so that the first start of a job is not the first test of the setup. It adds no write to any system. It also writes the chapter of the operator guide that this whole feature exists for: setting an operator's machine up from nothing, in the order of the commands, and `operator/README.md` as the map of the folder. The model API's login is not tested here (it needs the secret's value); the job's preflight proves it at the first start.

## Interface

`operator/bin/site check` (the loader of S0001, the hosting client of S0003; `gcloud`, `curl`, `git` and `python3` from the `PATH`)

- The checks, in this order, each printing `ok <name>` or `FAIL <name>: <detail>` (the detail one line, never a value that is a secret; names and statuses only), then a last line `site: <n> failed` (n at least 1, exit 1) or `site: ready` (exit 0):
  1. `site file`: the file loads (a fault of the loader is the detail).
  2. `keys`: every key of the job set (exactly the keys `require_settings` in `operator/job/job.sh` requires: `SITE_PROJECT SITE_REGION SITE_RUN_AS SITE_CONNECTOR SITE_PROXY SITE_NO_PROXY SITE_JOB SITE_INSTANCE SITE_REPOSITORY_URL SITE_CODE_URL SITE_CODE_REF SITE_HOSTING_SECRET SITE_MODEL_SECRET SITE_MODEL_BASE_URL SITE_MODEL SITE_LOGIN_URL SITE_LOGIN_SCOPE SITE_LOGIN_CLIENT_ID`) and of the hosting set (`SITE_REPOSITORY`, `SITE_CHECKOUT`) is set; the detail names the missing ones.
  3. `tools`: `gcloud`, `curl`, `git` and `python3` are on the `PATH`; the detail names the missing ones.
  4. `token`: `hosting_token` succeeds (the detail is the hosting client's message).
  5. `repository`: `GET /repos/$SITE_REPOSITORY` answers 200 and its `permissions.push` is true (details: the hosting client's own message for a non-200 answer, for example `hosting: GET /repos/owner/repo: 404 Not Found`, or `the token has no push permission`).
  6. `checkout`: `$SITE_CHECKOUT` is a git work tree whose `origin` url names `$SITE_REPOSITORY` (the detail says which part fails).
  7. `identity`: `gcloud run jobs list --project --region --limit=1` (with `--impersonate-service-account=<value>` when `SITE_IMPERSONATE` is set, as in `job.sh`; the flag goes on every `gcloud` call of `site check`, checks 7, 8 and 11) exits 0 (the detail is the first line of its error).
  8. The `secrets` check runs `gcloud secrets describe <name> --project`, which exits 0 for `SITE_HOSTING_SECRET` and for `SITE_MODEL_SECRET`; the detail names the one that fails. Neither secret's value is read.
  9. `code`: `git ls-remote $SITE_CODE_URL`, run with `https_proxy` set to `$SITE_PROXY` and no credential, exits 0 and, when `SITE_CODE_REF` is not 40 hexadecimal characters, lists that ref as a branch or tag (a commit id is accepted without a lookup).
  10. `no_proxy`: the hosts of `SITE_CODE_URL`, `SITE_REPOSITORY_URL` and `SITE_API_URL` are not covered by `SITE_NO_PROXY` (a domain `d` covers a host that equals `d` or ends in `.d`, a leading `.` ignored; the guide says `NO_PROXY` must not name a code host, since the job cannot resolve it), and the host of `SITE_MODEL_BASE_URL` is covered by it (opencode otherwise waits for the proxy to answer for an internal host). The detail names the host and the rule.
  11. `job`: informational, `ok` whenever its keys are set (a missing `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB` fails it by the `needs` rule below): runs `gcloud run jobs describe $SITE_JOB --project $SITE_PROJECT --region $SITE_REGION`, as `job_exists` in `operator/job/job.sh` does; exit 0 prints `ok job: <name> exists`, any other exit prints `ok job: <name> does not exist yet` (a missing job is not told from a failed call; check 7 catches a broken identity).
- When the site file does not load (check 1 fails), no other check runs: the output is the `FAIL site file: <the loader's message>` line and `site: 1 failed`.
- A check whose keys are missing prints `FAIL <name>: needs <keys>` and does not run; the others still run.
- `site check` makes no write: no `gcloud` call other than `list` and `describe`, no `POST`, `PUT`, `PATCH` or `DELETE`, no `git push`.

`docs/operator-guide.md` gets the chapter *Setting up an operator's machine*: the order (install `gcloud`, `git`, `curl`, `python3`; get the repository; `site init`; fill in the file by the table of its keys; `site check`; `job.sh create`; `job.sh execute`; `job.sh log` and `status`; drive a story with the skill; `job.sh delete`), with what each step proves and what its failure means; a short list of what the platform must provide before (the project, the connector, the run-as identity, the two secrets, the code host's bot user and its access to the project's repository), which this feature does not make. `operator/README.md` becomes the map of the folder: each script, its story and its use.

Tests: `tests/test_operator_site_check.py`, with the stand-ins of the earlier stories (`gcloud`, `curl`, `git`) answering per row.

## Acceptance criteria

1. With every key set and every stand-in answering well, `site check` prints `ok <name>` for the eleven checks in the order of the Interface, then `site: ready`, and exits 0.
2. Each check's failure, as rows of one parametrized test (a missing site file ends the run after its own line, as the Interface says): a missing file; a missing key (`SITE_RESET_REPOSITORY` is not one of the required); a `gcloud` that is not on the `PATH`; a token command that prints nothing; a repository answering 404; a token without push permission; a checkout that is not a work tree and one whose `origin` names another repository; a `gcloud run jobs list` that fails; a `gcloud secrets describe` that fails for the second secret only (the detail names it); a `git ls-remote` that fails; a ref that is not listed. Each prints its `FAIL <name>: <detail>` line (the detail checked), the other checks still run, the last line is `site: 1 failed` (`site: 3 failed` for the missing `gcloud`, which `identity` and `secrets` need too, and `site: 2 failed` for the empty token, which `repository` needs too) and the exit status is 1.
3. Two failures give `site: 2 failed`.
4. The `no_proxy` rules, as rows of one parametrized test: `SITE_NO_PROXY=.example.invalid` with a model host `llm.example.invalid` and a code host `code.example.net` is `ok`; the code host `code.example.invalid` covered is `FAIL`; the model host not covered is `FAIL`; a `NO_PROXY` of `example.invalid` covers `a.b.example.invalid` and does not cover `badexample.invalid`; a leading dot is ignored.
5. A check whose key is missing prints `FAIL <name>: needs <keys>` and is not run (the stand-in for it is not called), while the checks whose keys are set run.
6. A 40-character hexadecimal `SITE_CODE_REF` is accepted without a lookup (the `git` stand-in is asked for `ls-remote` once, without a ref argument); a branch name is looked up and found or not (rows).
7. `site check` makes no write: a test over every call of the stand-ins finds only `gcloud run jobs list`, `gcloud run jobs describe`, `gcloud secrets describe`, `GET` requests, `git ls-remote` and git's local reads (`rev-parse`, `remote get-url`, `config --get` or `config <key>`), and no `git push`.
8. No secret value is read or printed: the stand-in `gcloud` fails the test if it is asked to `versions access`, and a token's text (`TOKENMARK`) is in no output line.
9. `site check` with a command line argument other than none prints `usage: site check` and exits 2.
10. `operator/README.md` names every file under `operator/lib/`, `operator/bin/`, `operator/job/` and `operator/skill/kumpel/scripts/` (a test over the folder and the text).
11. The `job` check, as rows of one parametrized test: `gcloud run jobs describe` succeeds (`ok job: <name> exists`); it fails (`ok job: <name> does not exist yet`, and the exit status stays 0).
12. The `no_proxy` rows of criterion 4 include a covered-FAIL row for the host of `SITE_REPOSITORY_URL` and one for the host of `SITE_API_URL`.
13. The `git ls-remote` stand-in sees `https_proxy` equal to `SITE_PROXY`, and sees no token and no credential configuration (no `GIT_CONFIG_*` authorization, no `http.extraHeader`).
14. The impersonation flag, as rows on the `identity` check: `--impersonate-service-account=<value>` is in the `gcloud run jobs list` call when `SITE_IMPERSONATE` is set, and absent when it is not.
15. A failing `gcloud run jobs list` whose stand-in writes a multi-line error has as detail the error's first line only.
16. The `tools` check with two tools missing at once names both in its detail.
17. A repository answering 404 has the detail `hosting: GET /repos/owner/repo: 404 Not Found` (the hosting client's message).
18. The impersonation flag on the other `gcloud` calls, as rows of one parametrized test: with `SITE_IMPERSONATE` set, both `gcloud secrets describe` calls and the `gcloud run jobs describe` call carry `--impersonate-service-account=<value>`; with it unset, none does.
19. The `checkout` check on the `origin` url, as rows of one parametrized test: a work tree with no `origin` is `FAIL checkout` with a detail that says the origin is missing; an `origin` of the form `git@<host>:owner/repo.git` and one without `.git` are `ok`; an `origin` ending in `/xowner/repo.git` is `FAIL`.
20. `make check` stays green.
21. docs: `docs/operator-guide.md` the chapter named in the Interface, and the site file's section's table of keys now covers every key of the example file (a test that every `SITE_` key of `operator/site.env.example` appears in the guide's text); `README.md` names the chapter in its pointers; the other documents: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
FACTORY_SITE="$d/none.env" sh operator/bin/site check; echo "exit $?"
```

Expect: three lines: `FAIL site file: site: no site file at <d>/none.env; run: site init`, `site: 1 failed` and `exit 1`.

```bash
sh operator/bin/site check extra; echo "exit $?"
```

Expect: two lines, `usage: site check` (standard error) and `exit 2`.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. Questions, none answered by me:

   1. Check 11 `job` has no criterion. The Interface says it prints `ok job: <name> exists` or `ok job: <name> does not exist yet`, and criterion 1 only shows a generic `ok`. Please add a criterion with a row for each variant. I recommend one row where the stand-in `gcloud run jobs describe` succeeds and one where it reports the job as missing.
   2. The Interface does not say which command check 11 runs, or how a missing job differs from a failed call. Criterion 7 lists `gcloud run jobs describe` as allowed, but the Interface names only `jobs list` and `secrets describe`. Please state the command and the rule: exit 0 means it exists, and what means "does not exist yet"? Also say whether any other error still prints `ok` (the check is "always ok").
   3. Check 10 (`no_proxy`) says `SITE_REPOSITORY_URL` and `SITE_API_URL` must not be covered, but criterion 4 only has rows for the code host and the model host. Please add a covered-FAIL row for each of those two hosts.
   4. Check 9 (`code`) says `ls-remote` runs with `https_proxy` set to `$SITE_PROXY` and no credential. No criterion tests either clause. Please add one that the stand-in `git` sees `https_proxy` equal to `SITE_PROXY`, and one that it sees no token or credential configuration.
   5. Check 7 (`identity`) says the impersonation flag is added "when set". Please add criteria for both sides: the flag is in the `gcloud run jobs list` call when the impersonation key is set, and absent when it is not. Name the key, because the Interface does not.
   6. Check 7 says the detail is "the first line of its error". Criterion 2 only says "a `gcloud run jobs list` that fails". Please say that the row's detail is checked as the first line of a multi-line stderr.
   7. Check 2 (`keys`) says the job set means "the required ones of S0005". Please list the key names in this Interface, or name the exact place in S0005 that fixes them. Criterion 2's "a missing key" row cannot be written without knowing which keys are required.
   8. Check 3 (`tools`) names four tools, but criterion 2 has a row only for `gcloud`. If you want a row per tool, say so. Otherwise confirm that one tool's row stands for the rule "the detail names the missing ones", and add a row with two tools missing at once, so the plural detail is tested.
   9. Check 5 (`repository`) has the detail "the status and message" for a non-200 answer. Criterion 2 has a 404 row only. Please state the exact detail format, for example `HTTP 404: Not Found`, so the test can check it.

   My recommendation for 1 to 9 is to add the criteria and Interface lines as above. The architecture and scope are fine: the work is shell under `operator/`, inside the feature's scope and inside the coder's write paths.
4. 2026-11-03 human: All nine as you recommend, with these facts:

   1. Add the criterion, with one row where `gcloud run jobs describe` succeeds (`ok job: <name> exists`) and one where it fails (`ok job: <name> does not exist yet`).
   2. Check 11 runs `gcloud run jobs describe $SITE_JOB --project $SITE_PROJECT --region $SITE_REGION`, as `job_exists` in `operator/job/job.sh` does. Exit 0 means it exists; any other exit means "does not exist yet", and the line is still `ok`. Like `job.sh create`, the check does not tell a missing job from a failed call; a broken identity already fails check 7.
   3. Add a covered-FAIL row for the host of `SITE_REPOSITORY_URL` and one for the host of `SITE_API_URL`.
   4. Add both: the `git` stand-in sees `https_proxy` equal to `SITE_PROXY`, and it sees no token and no credential configuration (no `GIT_CONFIG_*` authorization, no `http.extraHeader`).
   5. The key is `SITE_IMPERSONATE`, and the flag is `--impersonate-service-account=<value>`, as in `job.sh`. It goes on every `gcloud` call of `site check` (checks 7, 8 and 11). Rows on check 7: the flag is present when the key is set and absent when it is not.
   6. Yes: the row's `gcloud` stand-in writes a multi-line error, and the detail is its first line.
   7. The job set is exactly the keys `require_settings` in `operator/job/job.sh` requires: `SITE_PROJECT SITE_REGION SITE_RUN_AS SITE_CONNECTOR SITE_PROXY SITE_NO_PROXY SITE_JOB SITE_INSTANCE SITE_REPOSITORY_URL SITE_CODE_URL SITE_CODE_REF SITE_HOSTING_SECRET SITE_MODEL_SECRET SITE_MODEL_BASE_URL SITE_MODEL SITE_LOGIN_URL SITE_LOGIN_SCOPE SITE_LOGIN_CLIENT_ID`. Name them in the Interface.
   8. One tool's row stands for the rule, plus one row with two tools missing at once for the plural detail.
   9. The detail of a non-200 answer is the hosting client's own message, as in check 4 and in S0008, for example `hosting: GET /repos/owner/repo: 404 Not Found`.
5. factory: started intake as vm.
6. intake: accepted. I carried the human's answers (journal entry 4) into the story as their edit and added nothing of my own.
   - Interface: it names `operator/bin/site check` and the eleven checks in order. Entry 4 fixed the gaps. I wrote in the job-set key list (the keys `require_settings` in `job.sh` requires), the `SITE_IMPERSONATE` flag on every `gcloud` call, the check 5 detail (the hosting client's own message) and the check 11 command and rule.
   - Criteria: I added criteria 11 to 17 from answers 1, 3, 4, 5, 6, 8 and 9. They cover the `job` rows, the repository-URL and API-URL covered-FAIL rows, the `https_proxy` and no-credential checks on `ls-remote`, the impersonation flag on both sides, the first line of a multi-line error, the two-tools-missing detail and the 404 detail. `make check` is now 18 and `docs:` 19, still the last two. Each criterion is one test function. Every rule has its failing side.
   - Smoke test: both commands are runnable, with no pytest `-q` issue. Each `Expect:` line is checkable against the output and the exit status.
   - Architecture: the work is shell under `operator/`, plus the guide and README, all inside the coder's and documenter's write paths.
   - Scope: it is within the feature's scope (S0009) and touches nothing in "Out of scope". The model API login is not tested here, as the Description says.
7. factory: started tests as vm.
8. tester: I stopped before writing tests. I read the work item, `operator/bin/site`, `operator/lib/site.sh`, `operator/lib/hosting.sh`, `operator/site.env.example` and the stand-ins in `tests/operator_support.py` and `tests/test_operator_job.py`. Criterion 2 contradicts the Interface in two rows, and criterion 7 cannot hold as written. No files were created.

   1. **Criterion 2: two rows cannot end in `site: 1 failed`.**
      - *`gcloud` not on the `PATH`.* The `tools` check fails. Checks 7 (`identity`) and 8 (`secrets`) still run `gcloud`, so they fail too. The Interface only skips a check for missing keys, not for a missing tool. Check 11 stays `ok`.
      - *A token command that prints nothing.* The `token` check fails. Check 5 (`repository`) calls the hosting client, which asks for the token again, so it fails too.

      The options I see:
      - **(a)** Keep the Interface. These two rows check their own `FAIL` line and that every other check still prints its line. They expect the true counts: `site: 3 failed` for `gcloud` and `site: 2 failed` for the token, exit 1. The details of the follow-on failures are not checked. The other rows stay at `site: 1 failed`.
      - **(b)** Add an Interface rule: a check whose tool or token is missing prints `FAIL <name>: needs <gcloud|token>` and does not run. It still counts as failed, so the counts are the same as in (a).
      - **(c)** Add an Interface rule: such a check is skipped and not counted. This needs a new line form, for example `skip identity: needs gcloud`, so these rows can stay at `site: 1 failed`.

      I would choose (a).

   2. **Criterion 7: "only `git ls-remote`" cannot hold.** The loader already runs `git -C <folder> rev-parse --is-inside-work-tree` (`_site_in_work_tree` in `operator/lib/site.sh`). Check 6 has to ask `git` about the checkout and its `origin` url.

      My plan: the `git` stand-in answers `ls-remote` itself. It passes local reads to the real `git`: `rev-parse`, `remote get-url`, and `config --get` or `config <key>` with one key. It records every call. The criterion 7 test then asserts that every `git` call is `ls-remote` or one of those local reads, and that there is no `push`. The `gcloud` and `curl` calls stay as written (`run jobs list`, `run jobs describe`, `secrets describe`, `GET` only). The options:
      - **(a)** this plan;
      - **(b)** allow only `ls-remote` and `rev-parse`, which ties the coder to `rev-parse` for check 6 too;
      - **(c)** assert only that no `git` call is a `push`.

      I would choose (a).

   **Choices I made myself (tell me if any is wrong).**
   - The missing-key row of criterion 2 removes a key that only check 2 reads, such as `SITE_CONNECTOR`, so the count stays at 1.
   - Criterion 16 removes `gcloud` and `curl`. It checks only that the `tools` detail names both, not the total.
   - To make a tool missing, the test builds a `PATH` of symlinks to the system's programs without `gcloud`, `curl`, `git`, `python3` and `gh`, with the stand-ins first.
9. 2026-11-03 human: Both (a), as you propose. 1: keep the Interface; the gcloud row expects `site: 3 failed` and the token row `site: 2 failed`, exit 1, each checking its own FAIL line and that every other check still prints its line. 2: the git stand-in answers `ls-remote` itself and passes the local reads (`rev-parse`, `remote get-url`, `config --get` or `config <key>`) to the real git; criterion 7 asserts every git call is one of those and none is a push. Your three own choices are right.
10. factory: started tests as vm.
11. tester: I wrote the tests for `site check` in one new file, `tests/test_operator_site_check.py`. I took the human's answers in entry 9 as given: the `gcloud`-missing row expects `site: 3 failed`, the empty-token row expects `site: 2 failed`, and the `git` stand-in answers `ls-remote` itself and passes the local reads to the real `git`.

    Criterion → test (all in `tests/test_operator_site_check.py`):
    - criterion 1: `test_a_ready_machine_passes_every_check_in_order`
    - criterion 2: `test_each_failing_check_names_its_fault_and_the_others_still_run` (12 rows: site-file-missing, key-missing, gcloud-not-on-the-path, token-command-prints-nothing, repository-not-found, no-push-permission, checkout-not-a-work-tree, checkout-of-another-repository, jobs-list-fails-with-a-multi-line-error, second-secret-not-visible, ls-remote-fails, ref-not-listed)
    - criterion 3: `test_two_failures_are_counted`
    - criterion 4: `test_no_proxy_bypasses_the_model_host_and_never_a_code_host`
    - criterion 5: `test_a_check_without_its_keys_says_what_it_needs_and_does_not_run` (rows: secrets, code, repository)
    - criterion 6: `test_a_commit_id_is_accepted_without_lookup_and_a_name_must_be_listed` (rows: 40 hex chars accepted with one `ls-remote` call and no ref argument; 39 and 41 hex chars and 40 non-hex chars are looked up; branch found and not found; tag found)
    - criterion 7: `test_site_check_makes_no_write`
    - criterion 8: `test_no_secret_value_is_read_or_printed`
    - criterion 9: `test_an_argument_after_check_prints_the_usage`
    - criterion 10: `test_the_operator_readme_names_every_script_and_library`
    - criterion 11: `test_the_job_check_tells_whether_the_job_exists_and_never_fails`
    - criterion 12: `test_no_proxy_bypasses_the_model_host_and_never_a_code_host[repository-host-covered]` and `[api-host-covered]`
    - criterion 13: `test_ls_remote_runs_through_the_proxy_without_a_credential`
    - criterion 14: `test_the_identity_check_impersonates_when_the_site_says_so`
    - criterion 15: `test_each_failing_check_names_its_fault_and_the_others_still_run[jobs-list-fails-with-a-multi-line-error]` (a three-line error; the detail must be exactly its first line)
    - criterion 16: `test_the_tools_check_names_every_missing_tool`
    - criterion 17: `test_each_failing_check_names_its_fault_and_the_others_still_run[repository-not-found]` (exact detail `hosting: GET /repos/owner/repo: 404 Not Found`)
    - criterion 18: no test (`make check`)
    - criterion 19: `test_the_guide_names_every_key_of_the_example_site_file`

    How the tests are built:
    - **Machine:** each test gets a site file, a real git checkout and per-test stand-ins for `gcloud`, `git` and `curl`. The `curl` stand-in reuses `CURL_STAND_IN` from `tests/operator_support.py`, with a routes file.
    - **Answers:** the record and answers file paths are written into each stand-in, so the stand-ins do not depend on environment variables reaching them.
    - **PATH:** the per-test stand-ins folder plus a module-scoped folder of links to the system's programs, leaving out `gcloud`, `curl`, `git`, `python3` and `gh`. A tool is removed from a row by leaving its stand-in out.
    - **Token:** the token command builds `TOKENMARK` at run time, so the mark is in no file the test writes.
    - **No-write allow-list (criterion 7):** `gcloud` may only run `run jobs list`, `run jobs describe` and `secrets describe`. Every `curl` config must hold `request = "GET"`. Every `git` call must be `ls-remote`, `rev-parse`, `remote get-url`, or `config --get`/`config <key>`, and none may be `push`.

    Where the Interface gives no exact detail text, I check only the smallest thing its wording implies. The reviewer or the human may want to look at these:
    - checkout not a work tree: the detail contains `work tree`;
    - other origin: the detail contains `origin`;
    - `ls-remote` fails: the detail is not empty;
    - ref not listed: the detail names the ref;
    - `no_proxy` FAIL rows: the detail contains the host;
    - a `needs` line: it starts with `needs ` and names the missing key.

    Check lines and the summary line are read from standard output, and the usage line from standard error, as the smoke test shows.

    Run: `uv run pytest -q tests/test_operator_site_check.py | tail -5` showed only FAILED lines (the job, ls-remote, identity and tools tests). That is the right reason: `operator/bin/site` has no `check` subcommand yet, so it prints its usage and exits 2. The tail showed no import or collection errors. `make lint` is green.

    Files created: `tests/test_operator_site_check.py`. Modules the test run could not import: none. The code under test is the shell command `operator/bin/site check`, which does not exist yet.

    Set aside: `test_site_check_makes_no_write` and `test_no_secret_value_is_read_or_printed` may pass already, because they assert on calls that do not happen yet. The README test (criterion 10) and the guide-keys test (criterion 19) read files that already exist. I cannot tell from the tail whether they pass or fail now.

    `lint`: lint: green (0.1 s)
12. factory: started doing as vm.
13. coder: I stopped before handing on. The code is done and `make test` is green (82 s, coverage 99.58 %). `lint`, `types`, `layers`, `sast` and `licenses` are green too. `make check` is still red, because `make secrets` flags a line that I did not write.

    **The finding.** detect-secrets reports a "Secret Keyword" at line 102 of this work item: the Interface line check 8 of the Interface (the `secrets` check and its `gcloud secrets describe` call). It reads the check's name, a colon and the quoted call as a keyword followed by a value. The line was committed before this stage (intake carried it in from entry 4). The files I changed are not flagged.

    **Options:**
    - (a) You add `pragma: allowlist secret` to that line, or an entry in `.secrets.baseline`. I may not do either without asking (CLAUDE.md, "Not without asking").
    - (b) I reword the line so the keyword no longer has a value after a colon, for example "8. The `secrets` check runs `gcloud secrets describe <name> --project` …". The meaning stays the same, but the Description changes when no journal entry asked for it.
    - (c) You or intake reword it.

    I would choose (b), if you allow it. Say which and the stage runs again.

    **What I built** (in the working tree, not committed):
    - `operator/bin/site`: a new `check` subcommand.
      - The eleven checks run in the Interface's order. Each prints `ok <name>` or `FAIL <name>: <detail>`. The run ends with `site: ready` (exit 0) or `site: <n> failed` (exit 1).
      - If the site file does not load, that check's line and `site: 1 failed` are the only output.
      - A check whose keys are missing prints `needs <keys>` through `needs` and does not run.
      - `gcloud` calls go through `site_gcloud`. It adds `--project=`, `--region=` for `run`, and `--impersonate-service-account=` when `SITE_IMPERSONATE` is set.
      - `ls-remote` runs with `https_proxy=$SITE_PROXY` and an empty credential helper. For a ref that is not a commit id it runs `--exit-code <url> refs/heads/<ref> refs/tags/<ref>`.
      - `check extra` prints `usage: site check` and exits 2.
    - `operator/README.md`: the "What is here" section is now the map of the folder. Each file has its story and its use.

    **Main choice.** The repository check captures `hosting_repo_api` with `2>&1`. On a failure the hosting client prints nothing on standard output, so the captured text is its own message (`hosting: GET /repos/owner/repo: 404 Not Found`). I rejected a temporary file for standard error.

    **Two smaller choices:**
    - The general usage line stays `usage: site path | init | show | get SITE_X`. Adding `| check` broke two rows of `tests/test_operator_site.py`, so I put it back.
    - The `job` check follows the general `needs` rule, so with `SITE_JOB` missing it prints `FAIL`. The Interface calls the check "always ok", but it cannot name the job without the key.

    **Noticed, not touched:**
    - `job_keys` in `site` repeats the list in `require_settings` in `operator/job/job.sh`.
    - `site_gcloud` mirrors `gcloud_call` there, without its dry run. Sharing them would mean moving them into `operator/lib/`, which is a change to `job.sh` beyond this story.
    - `docs/operator-guide.md` still says "`site check` does not exist yet" (around line 928). The guide's chapter belongs to the documenter. Its test for the example file's keys already passes.

    **Not run:** I could not run the smoke test's own commands (the shell call was denied). The `site-file-missing` and usage tests check the same output.

    **Refactor pass:** I read my diff and nothing needed changing.
14. 2026-11-03 human: I reworded the line myself on the branch under my standing leave (61948207d): check 8 now reads "The `secrets` check runs `gcloud secrets describe <name> --project`, which exits 0 …", and your journal's quote of it is reworded too; the scan passes on the new text. Your other choices are right: `2>&1` for the repository check, the usage line unchanged, and the `job` check following the `needs` rule when `SITE_JOB` is missing. Run `make check` again and hand on.
15. factory: started doing as vm.
16. coder: `make check` is green now (`check: green`; `test: green (81.9 s)`, coverage 99.58 %). The human reworded check 8's Interface line in 61948207d, which cleared the earlier `make secrets` finding. I changed no code in this run. My code from entry 13 was already committed, so I did not repeat the refactor pass. The diff has not changed since that pass, and the pass found nothing to change.

    What I built (in the branch since entry 13):
    - `operator/bin/site`: a new `check` subcommand.
      - The eleven checks run in the Interface's order. Each prints `ok <name>` or `FAIL <name>: <detail>`, and the run ends with `site: ready` (exit 0) or `site: <n> failed` (exit 1).
      - If the site file does not load, only its own line and `site: 1 failed` are printed.
      - A check whose keys are missing prints `FAIL <name>: needs <keys>` and does not run.
      - Every `gcloud` call goes through `site_gcloud`, which adds `--impersonate-service-account=` when `SITE_IMPERSONATE` is set.
      - `ls-remote` runs with `https_proxy=$SITE_PROXY` and an empty credential helper.
      - `check extra` prints `usage: site check` and exits 2.
    - `operator/README.md`: now the map of the folder. Each file has its story and its use.

    Main choice: the repository check captures `hosting_repo_api` with `2>&1`, so on a failure the detail is the hosting client's own message. I rejected a temporary file for standard error. The human confirmed this in entry 14, along with two other choices: the general usage line stays as it was, and the `job` check follows the `needs` rule when `SITE_JOB` is missing.

    What the journal changed: entry 14 reworded check 8's line in the Interface. The meaning is the same, and the human made that edit themselves, so I rewrote nothing in the Description.

    Noticed, not touched:
    - `job_keys` in `operator/bin/site` repeats the key list in `require_settings` in `operator/job/job.sh`.
    - `site_gcloud` mirrors `gcloud_call` in `job.sh`. Sharing them would mean moving both into `operator/lib/`, which would change `job.sh` beyond this story.
    - `docs/operator-guide.md` still says that `site check` does not exist yet. The guide's chapter is the documenter's work.
    - I did not run the smoke test's commands myself. The `site-file-missing` and usage tests check the same output.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
17. factory: started review as vm.
18. reviewer: Review, round 0. I read the work item and `git diff main...HEAD -- . ':!factory'`: `operator/bin/site` (the new `check`), `operator/README.md` and `tests/test_operator_site_check.py`. I compared them with `operator/job/job.sh`, `operator/lib/site.sh` and `operator/lib/hosting.sh`. Each of criteria 1 to 17 and 21 has a test that checks what the criterion says, and the coder's `make check` was green (entry 16). The README map names every file the test of criterion 10 looks for. Architecture and security are clean. The diff touches no code under `src/`. It adds no suppression markers. The `ls-remote` call runs without a credential. Details carry secret names, never their values. The checkout's origin url is not echoed.

    Findings:
    1. criterion 18 added: it needs its test. The Interface says the `--impersonate-service-account` flag goes on every `gcloud` call (checks 7, 8 and 11). Criterion 14 only tests check 7, so nothing covers the `secrets describe` and `run jobs describe` calls (`operator/bin/site:135`, `site_gcloud`).
    2. criterion 19 added: it needs its test. `check_checkout` (`operator/bin/site:195-216`) has a no-origin branch with its own detail, at line 200. `names_repository` accepts `:owner/repo` and urls without `.git`. No test reaches the no-origin branch, any origin form other than `https://…/owner/repo.git`, or a lookalike owner. The closing criteria are now 20 (`make check`) and 21 (docs).
    3. `operator/bin/site:135` `site_gcloud` is a second copy of `gcloud_call` in `operator/job/job.sh:30`: the same `--project`, `--region` and `--impersonate-service-account` logic, minus the dry run. Fix: move one helper into `operator/lib/` (for example beside the loader), with the dry run left to `job.sh`, and have both scripts use it.
    4. `operator/bin/site:59` `job_keys` copies the key list of `require_settings` in `operator/job/job.sh:52-55`. The Interface defines the job set as exactly that list, so two copies can drift. Fix: keep the list once in `operator/lib/site.sh` (a variable or function) and use it in both `require_settings` and `check_keys`.
    5. `operator/bin/site:274` repeats the hosting client's default `${SITE_API_URL:-https://api.github.com}` from `operator/lib/hosting.sh:89`. Fix: take the base url from `hosting.sh`, for example a small function the client also uses, so the `no_proxy` check tests the host the client actually calls.
    6. The work item's Interface, check 11, says "`job`: informational, always `ok`". The code (`operator/bin/site:316`) fails it with `needs SITE_JOB` when the key is missing, as the human confirmed in entry 14. Fix: the coder rewrites that clause, for example "`ok` whenever its keys are set (a missing `SITE_JOB` fails by the `needs` rule)". I left it alone because I may only correct the Description.

    Earlier tests: none changed. `git diff --name-status main...HEAD` lists the one test file, `tests/test_operator_site_check.py`, as `A`.
19. factory: started doing as vm.
20. coder: Round 1. I fixed review findings 3 to 6 (entry 18). Findings 1 and 2 add criteria that only need tests, so this goes to the tester: **criterion 18**, the `--impersonate-service-account=<value>` flag on both `gcloud secrets describe` calls and on `gcloud run jobs describe`, present when `SITE_IMPERSONATE` is set and absent when it is not; and **criterion 19**, the `checkout` check on the `origin` url, with no `origin` (a FAIL whose detail says the origin is missing), `git@<host>:owner/repo.git` and an origin without `.git` (both ok), and `/xowner/repo.git` (FAIL). The code already handles all of these (`site_gcloud_with` in `operator/lib/site.sh`; `check_checkout` and `names_repository` in `operator/bin/site`), so the new tests should pass without a code change.

    What I changed:
    - Finding 3: `operator/lib/site.sh` now holds the one gcloud helper, `site_gcloud_with RUNNER ARG...`. It adds `--project=`, `--region=` for `run` calls, and `--impersonate-service-account=` when `SITE_IMPERSONATE` is set, then runs RUNNER. In `operator/job/job.sh`, `gcloud_call` passes `print_call` as the runner for a dry run and `gcloud` otherwise, so the dry-run output is unchanged. `operator/bin/site` calls `site_gcloud_with gcloud` directly, and its own `site_gcloud` copy is gone.
    - Finding 4: the job's key list now lives once, as `site_job_keys` in `operator/lib/site.sh`. `require_settings` in `job.sh` and `check_keys` in `site` both read it, and the `job_keys` copy is removed.
    - Finding 5: `operator/lib/hosting.sh` has a new public `hosting_api_url`, which prints the default `https://api.github.com` or `SITE_API_URL`, without a trailing `/`. The client's `_hosting_curl_config` uses it, and so does the `no_proxy` check in `site`, so the check tests the host the client actually calls.
    - Finding 6: in the work item's Interface, check 11 now reads "informational, `ok` whenever its keys are set (a missing `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB` fails it by the `needs` rule below)". This matches the human's confirmation in entry 14. No other part of the Description changed.

    Main choice: I pass the runner as the helper's first argument, so `job.sh` keeps its dry run without the library knowing about it. I rejected two alternatives: a dry-run variable read inside `site.sh`, and a helper that only prints the flags, which shell cannot hand back safely as separate words.

    Refactor pass: I read the diff. Once all three calls used `site_gcloud_with gcloud` directly, a one-line `site_gcloud` wrapper in `site` had nothing left to do, so I removed it. Nothing else needed changing.

    Noticed, not touched: `docs/operator-guide.md` still says that `site check` does not exist yet. That is the documenter's work.

    `check`: check: green (test: green, 80.6 s)

    The factory left out changes outside the write paths: factory/features/F0048-an-operator-sets-up-from-one-site-file/in-progress/F0048-S0009-one-command-says-whether-a-machine-is-ready-and-the-guide-says-how-to-get-there.md.
21. factory: started tests as vm.
22. tester: Tests for the two criteria the reviewer added (entry 18). The coder's entry 20 said these need tests only. I edited no existing test. I added two parametrized tests and one table to `tests/test_operator_site_check.py`, the file this story already wrote.

    - criterion 18: `tests/test_operator_site_check.py::test_the_secrets_and_job_checks_impersonate_when_the_site_says_so`. There are two rows, `set` and `unset`. Each row first asserts that the run made exactly the two `gcloud secrets describe` calls (one per secret) and the one `gcloud run jobs describe` call. It then asserts that each of those calls carries `--impersonate-service-account=<value>` when `SITE_IMPERSONATE` is set and no such flag when it is unset.
    - criterion 19: `tests/test_operator_site_check.py::test_the_checkout_check_reads_the_origin_url`, with four rows:
      - `no-origin`: `FAIL checkout`, and the detail mentions the origin and says "no origin" or "missing".
      - `scp-form` (`git@repo.example.net:owner/repo.git`): `ok`.
      - `without-dot-git` (`https://repo.example.net/owner/repo`): `ok`.
      - `lookalike-owner` (`…/xowner/repo.git`): `FAIL`.

    To build these checkouts, `Machine._checkout` now takes its `origin` url from a new `ORIGINS` table keyed by the checkout's kind; `None` means no origin is added. The existing kinds `work tree` and `other origin` keep their urls, so the earlier rows still check the same thing.

    Files changed: `tests/test_operator_site_check.py`. No files created. The test run imported every module.

    Test run (`uv run pytest -q tests/test_operator_site_check.py`): all pass, as entry 20 expected. The code from round 1 already covers both criteria, so the new tests are green on purpose, not red. `make lint`: green.

    Open, outside my change: entry 20 says the factory dropped the coder's rewrite of check 11 in the Interface (finding 6, "always `ok`"). The Description still says "informational, always `ok`", so that wording fix is still open.

    `lint`: lint: green (0.1 s)
23. factory: started doing as vm.
24. coder: Round 1, after the tester. I changed nothing in this run. The tester added the tests for criteria 18 and 19 (entry 22) in `tests/test_operator_site_check.py`. They pass against the round-1 code as it stands, and `make check` is green on the branch (`check: green`; `test: green (79.9 s)`, coverage 99.58 %). `git status` shows nothing uncommitted.

    What this round built (my entry 20 has the details):
    - `operator/lib/site.sh`: `site_gcloud_with RUNNER ARG...` is now the one gcloud helper, used by `operator/job/job.sh` and `operator/bin/site`. `site_job_keys` holds the job's key list once (findings 3 and 4).
    - `operator/lib/hosting.sh`: `hosting_api_url` gives the base URL for both the client and the `no_proxy` check (finding 5).
    - `operator/bin/site`: `check` uses the three helpers above.

    Main choice: the runner is passed as the helper's first argument, so `job.sh` keeps its dry run without the library knowing about it. I rejected a dry-run variable read inside `site.sh`.

    Refactor pass: I did not repeat it. The diff is the same as at entry 20, where I last did it.

    Open, not touched: finding 6 is still not done. Check 11 in the Interface still says "informational, always `ok`", but the code fails it by the `needs` rule when `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB` is missing, as the human confirmed in entry 14. I rewrote that clause in round 1, but the factory dropped the change because the work item is outside my write paths (entry 20). Someone who may edit the Description (the reviewer or the human) needs to make that change. I also noticed that `docs/operator-guide.md` still says `site check` does not exist yet. That is the documenter's work.

    What the journal changed: entries 18 to 22 added criteria 18 and 19 (now tested) and the check 11 wording above. I could not write either into the Description myself.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
25. factory: started review as vm.
26. reviewer: Review, round 1. I read the work item and `git diff main...HEAD -- . ':!factory'`: `operator/bin/site` (`check`), `operator/lib/site.sh` (`site_gcloud_with`, `site_job_keys`), `operator/lib/hosting.sh` (`hosting_api_url`), `operator/job/job.sh`, `operator/README.md` and `tests/test_operator_site_check.py`.

    - Criteria: each of criteria 1 to 19 and 21 has a test that checks what it says. Criteria 18 and 19, which I added in round 0, are now `test_the_secrets_and_job_checks_impersonate_when_the_site_says_so` and `test_the_checkout_check_reads_the_origin_url`. Both sides of the commit-id rule are tested (39, 40 and 41 hex characters, and non-hex). The coder's `make check` was green (entry 24).
    - Round-0 findings 3 to 5 are fixed. `site_gcloud_with RUNNER` is now the one gcloud helper, and `job.sh` keeps its dry run through `print_call`. The key list exists once, as `site_job_keys`. The `no_proxy` check reads the API host from `hosting_api_url`, which the client also uses.
    - Security: no write calls. Secret names are printed, never their values. `ls-remote` runs with an empty credential helper. The origin url is not echoed. No suppression markers. No change under `src/`.

    no findings

    Description corrections. The coder and tester could not make these, because the work item is outside their write paths. The lines are in the Interface and the criteria, not under `## Description`. I made them under my write path because the human's answers settle each one word for word, and no behaviour or test changes:
    - description corrected: Interface check 11 "`job`: informational, always `ok`" -> "`job`: informational, `ok` whenever its keys are set (a missing `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB` fails it by the `needs` rule below)". This is round-0 finding 6, as the human confirmed in entry 14 and `check_job` does.
    - description corrected: criterion 2 "the last line is `site: 1 failed`" -> the same, plus "(`site: 3 failed` for the missing `gcloud`, which `identity` and `secrets` need too, and `site: 2 failed` for the empty token, which `repository` needs too)". This follows the human's entry 9, answer 1.
    - description corrected: criterion 7 "finds only … `GET` requests and `git ls-remote`" -> "… `GET` requests, `git ls-remote` and git's local reads (`rev-parse`, `remote get-url`, `config --get` or `config <key>`), and no `git push`". This follows the human's entry 9, answer 2.

    Open for the docs stage: `docs/operator-guide.md` still says `site check` does not exist yet, at line 928 (the `site` command's paragraph, which also gives the old usage line) and at line 1215.

    Notes:
    - `tests/test_operator_site_check.py:698-750`: `test_the_identity_check_impersonates_when_the_site_says_so` and `test_the_secrets_and_job_checks_impersonate_when_the_site_says_so` repeat the same set/unset parametrization. One test over all four gcloud calls would cover both.
    - `tests/test_operator_site_check.py:521-527`: the `no_proxy` FAIL rows check that the detail names the host, not that it names the rule the Interface asks for.

    Earlier tests: none changed. `git diff --name-status main...HEAD` lists the one test file, `tests/test_operator_site_check.py`, as `A`.
27. factory: started docs as vm.
28. documenter: Docs, round 1. I changed only documents, so I did not run `make check`; the factory runs it after this stage. `make documents` printed `documents ok`.

    Files changed:
    - `docs/operator-guide.md`: new chapter *Setting up an operator's machine* before *On Cloud Run*, and a line for it in the contents list. It has three parts. The first lists what the platform must provide first. The second is the ten steps in order, each with what it proves and what its failure means. The third is a table of the eleven `site check` checks, with what each proves and what a `FAIL` means. It also covers the dependent failures (`site: 3 failed` for a missing `gcloud`, `site: 2 failed` for an empty token).
    - `docs/operator-guide.md`, *The `site` command*: I added the `site check` row to the command table. I replaced "`site check` does not exist yet" with the real usage behaviour (`usage: site check`, exit 2).
    - `docs/operator-guide.md`, *Creating the job*: the first-start list said `site check` does not exist yet. It now points to the new chapter.
    - `README.md`: the pointer to the operator guide names the new chapter and `operator/README.md`.

    I ran the two smoke commands, and the output matches the Smoke test section. With a missing site file they print `FAIL site file: site: no site file at <path>; run: site init`, then `site: 1 failed`, and exit 1. `site check extra` prints `usage: site check` and exits 2.

    Cross-read and found current:
    - `operator/README.md`. It already has the map table with a row for every file under `operator/lib/`, `operator/bin/`, `operator/job/` and `operator/skill/kumpel/scripts/`. The table in *The keys* covers every `SITE_` key of `operator/site.env.example`, which I checked with a loop.
    - *The site file* and *Creating the job*, against the diff in `operator/job/job.sh` and `operator/lib/site.sh`.

    Stale text I saw and did not touch, because it is unrelated to this story:
    - The defaults in *The keys* do not match the comments in `operator/site.env.example`. The guide says `SITE_CPU` 8, `SITE_MEMORY` 32Gi, `SITE_TIMEOUT` 14400, and `SITE_INSTANCE` and `SITE_CODE_REF` required. The example says 4, 16Gi, 24h, and that `SITE_INSTANCE` and `SITE_CODE_REF` have defaults. This belongs to the stories that confirm each key's default (the table itself says defaults are confirmed as those stories land).
    - The generic usage line (`usage: site path | init | show | get SITE_X`, `operator/bin/site:15`) does not name `check`. This is code, so it is not mine to change. The guide states the behaviour as it is. It is a small point for a later story and not a finding against the Interface, which does not say what the line contains.
    - *What the job needs* says "Eight vCPUs and 16 GiB at least", while the `SITE_MEMORY` default is 32Gi. This is also unrelated to this story.

    `check`: check: green (not run again: passed on tree de1b85f8416e at 2026-11-03T01:38:02Z)
    `secrets`: secrets: green (1.5 s)
    `documents`: documents ok
29. factory: started smoke-test as vm.
30. smoke-tester: Smoke test run from the repository root, both commands exactly as written, in order. No server involved. Nothing was fixed or changed; the working tree is clean and the temporary directory removed itself.

    Command 1:

    ```bash
    d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
    FACTORY_SITE="$d/none.env" sh operator/bin/site check; echo "exit $?"
    ```

    Output:

    ```
    FAIL site file: site: no site file at /tmp/tmp.mJXTdom4f7/none.env; run: site init
    site: 1 failed
    exit 1
    ```

    Met its `Expect:` line: three lines, `FAIL site file: site: no site file at <d>/none.env; run: site init`, `site: 1 failed`, `exit 1`. No other check ran after the site file failed (Interface; criterion 2's missing-file row).

    Command 2:

    ```bash
    sh operator/bin/site check extra; echo "exit $?"
    ```

    Output (standard output and standard error captured separately to check the stream):

    ```
    stdout:
    exit 2
    stderr:
    usage: site check
    ```

    Met its `Expect:` line: two lines, `usage: site check` on standard error and `exit 2` (criterion 9).

    Re-read the acceptance criteria: neither command's output contradicts any criterion. The two commands only touch the site-file failure path and the usage error. The other criteria (the eleven checks, no_proxy rules, impersonation, no writes, docs) are not exercised by this smoke test and are left to the tests and the review.

    Findings: none.
