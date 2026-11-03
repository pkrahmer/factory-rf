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
