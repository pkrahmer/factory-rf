---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 509
comments_read: [6592609715]
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-03T01:06:13.682491Z'
  lease_duration: 60
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
---

# One command says whether a machine is ready, and the guide says how to get there

## Description

A fresh setup has failed in small ways: a token command that prints nothing, a secret the identity cannot see, a code reference that does not exist, a `NO_PROXY` that names the code host (the guide forbids it) or leaves out the model API's host (opencode then hangs for 79 seconds), a repository the token can read but not push to. Each cost a failed start. This story adds `site check` to the command of S0001: a list of read-only checks, one line each, that says `ok` or `FAIL <name>: <detail>` and exits 0 only when nothing failed, so that the first start of a job is not the first test of the setup. It adds no write to any system. It also writes the chapter of the operator guide that this whole feature exists for: setting an operator's machine up from nothing, in the order of the commands, and `operator/README.md` as the map of the folder. The model API's login is not tested here (it needs the secret's value); the job's preflight proves it at the first start.

## Interface

`operator/bin/site check` (the loader of S0001, the hosting client of S0003; `gcloud`, `curl`, `git` and `python3` from the `PATH`)

- The checks, in this order, each printing `ok <name>` or `FAIL <name>: <detail>` (the detail one line, never a value that is a secret; names and statuses only), then a last line `site: <n> failed` (n at least 1, exit 1) or `site: ready` (exit 0):
  1. `site file`: the file loads (a fault of the loader is the detail).
  2. `keys`: every key of the job set (the required ones of S0005) and of the hosting set (`SITE_REPOSITORY`, `SITE_CHECKOUT`) is set; the detail names the missing ones.
  3. `tools`: `gcloud`, `curl`, `git` and `python3` are on the `PATH`; the detail names the missing ones.
  4. `token`: `hosting_token` succeeds (the detail is the hosting client's message).
  5. `repository`: `GET /repos/$SITE_REPOSITORY` answers 200 and its `permissions.push` is true (details: the status and message, or `the token has no push permission`).
  6. `checkout`: `$SITE_CHECKOUT` is a git work tree whose `origin` url names `$SITE_REPOSITORY` (the detail says which part fails).
  7. `identity`: `gcloud run jobs list --project --region --limit=1` (with the impersonation flag when set) exits 0 (the detail is the first line of its error).
  8. `secrets`: `gcloud secrets describe <name> --project` exits 0 for `SITE_HOSTING_SECRET` and for `SITE_MODEL_SECRET`; the detail names the one that fails. Neither secret's value is read.
  9. `code`: `git ls-remote $SITE_CODE_URL`, run with `https_proxy` set to `$SITE_PROXY` and no credential, exits 0 and, when `SITE_CODE_REF` is not 40 hexadecimal characters, lists that ref as a branch or tag (a commit id is accepted without a lookup).
  10. `no_proxy`: the hosts of `SITE_CODE_URL`, `SITE_REPOSITORY_URL` and `SITE_API_URL` are not covered by `SITE_NO_PROXY` (a domain `d` covers a host that equals `d` or ends in `.d`, a leading `.` ignored; the guide says `NO_PROXY` must not name a code host, since the job cannot resolve it), and the host of `SITE_MODEL_BASE_URL` is covered by it (opencode otherwise waits for the proxy to answer for an internal host). The detail names the host and the rule.
  11. `job`: informational, always `ok`: `ok job: <name> exists` or `ok job: <name> does not exist yet`.
- When the site file does not load (check 1 fails), no other check runs: the output is the `FAIL site file: <the loader's message>` line and `site: 1 failed`.
- A check whose keys are missing prints `FAIL <name>: needs <keys>` and does not run; the others still run.
- `site check` makes no write: no `gcloud` call other than `list` and `describe`, no `POST`, `PUT`, `PATCH` or `DELETE`, no `git push`.

`docs/operator-guide.md` gets the chapter *Setting up an operator's machine*: the order (install `gcloud`, `git`, `curl`, `python3`; get the repository; `site init`; fill in the file by the table of its keys; `site check`; `job.sh create`; `job.sh execute`; `job.sh log` and `status`; drive a story with the skill; `job.sh delete`), with what each step proves and what its failure means; a short list of what the platform must provide before (the project, the connector, the run-as identity, the two secrets, the code host's bot user and its access to the project's repository), which this feature does not make. `operator/README.md` becomes the map of the folder: each script, its story and its use.

Tests: `tests/test_operator_site_check.py`, with the stand-ins of the earlier stories (`gcloud`, `curl`, `git`) answering per row.

## Acceptance criteria

1. With every key set and every stand-in answering well, `site check` prints `ok <name>` for the eleven checks in the order of the Interface, then `site: ready`, and exits 0.
2. Each check's failure, as rows of one parametrized test (a missing site file ends the run after its own line, as the Interface says): a missing file; a missing key (`SITE_RESET_REPOSITORY` is not one of the required); a `gcloud` that is not on the `PATH`; a token command that prints nothing; a repository answering 404; a token without push permission; a checkout that is not a work tree and one whose `origin` names another repository; a `gcloud run jobs list` that fails; a `gcloud secrets describe` that fails for the second secret only (the detail names it); a `git ls-remote` that fails; a ref that is not listed. Each prints its `FAIL <name>: <detail>` line (the detail checked), the other checks still run, the last line is `site: 1 failed` and the exit status is 1.
3. Two failures give `site: 2 failed`.
4. The `no_proxy` rules, as rows of one parametrized test: `SITE_NO_PROXY=.example.invalid` with a model host `llm.example.invalid` and a code host `code.example.net` is `ok`; the code host `code.example.invalid` covered is `FAIL`; the model host not covered is `FAIL`; a `NO_PROXY` of `example.invalid` covers `a.b.example.invalid` and does not cover `badexample.invalid`; a leading dot is ignored.
5. A check whose key is missing prints `FAIL <name>: needs <keys>` and is not run (the stand-in for it is not called), while the checks whose keys are set run.
6. A 40-character hexadecimal `SITE_CODE_REF` is accepted without a lookup (the `git` stand-in is asked for `ls-remote` once, without a ref argument); a branch name is looked up and found or not (rows).
7. `site check` makes no write: a test over every call of the stand-ins finds only `gcloud run jobs list`, `gcloud run jobs describe`, `gcloud secrets describe`, `GET` requests and `git ls-remote`.
8. No secret value is read or printed: the stand-in `gcloud` fails the test if it is asked to `versions access`, and a token's text (`TOKENMARK`) is in no output line.
9. `site check` with a command line argument other than none prints `usage: site check` and exits 2.
10. `operator/README.md` names every file under `operator/lib/`, `operator/bin/`, `operator/job/` and `operator/skill/kumpel/scripts/` (a test over the folder and the text).
11. `make check` stays green.
12. docs: `docs/operator-guide.md` the chapter named in the Interface, and the site file's section's table of keys now covers every key of the example file (a test that every `SITE_` key of `operator/site.env.example` appears in the guide's text); `README.md` names the chapter in its pointers; the other documents: none.

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
