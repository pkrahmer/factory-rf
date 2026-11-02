---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 499
comments_read: [6582236900]
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
---

# The job script sets its own PATH, keeps the token in a private folder and exports all four proxy spellings

## Description

The first whole run of the factory in a Cloud Run job (2026-11-02, `planning/cloud-sandbox/TRIAL-2-F0001-IN-A-JOB.md`) needed three workarounds in the job's configuration because `vm/job-start.sh` leaves three things to the operator. It never puts the tools folder it builds on the `PATH`, so the preflight stops on `tool:uv` (the VM's service file sets it, the job script does not). It takes the hosting token from the path the job gives, and a mounted secret's folder is read-only at mode 0555, so the preflight's `token-file` item, which wants the folder private, can never pass for a token mounted as the guide says. And it exports only the two HTTPS spellings of the proxy, while the stage image's `apt-get` fetches over plain HTTP, so the build cannot resolve its package host. This story makes the script do all three: `PATH` begins with `<root>/tools/bin`; a token whose folder is not private is copied into a private folder of the instance and `FACTORY_TOKEN_FILE` names the copy; and a given proxy is exported in all four spellings. It changes nothing else of the script and no step's name or order.

## Interface

`vm/job-start.sh`

- After the `inputs` step the script exports `PATH` as `<root>/tools/bin` followed by `:` and the `PATH` it was started with (unchanged, not de-duplicated). `<root>` is the one the script already derives (`FACTORY_JOB_ROOT`, default `/srv/factory/<instance>`).
- In the `inputs` step, after the check that `FACTORY_TOKEN_FILE` is a readable file: when the file's folder is not owned by the user running the script, or has any permission bit for group or others, the script makes `<root>/secrets` (mode 0700, owner the running user), copies the file to `<root>/secrets/hosting-token` with mode 0600 (content byte for byte, the original untouched) and sets and exports `FACTORY_TOKEN_FILE` to the copy. It prints `job-start: token-file: copied to <root>/secrets`. When the folder is owned by the running user and has no bit for group or others, nothing is copied, nothing is printed and `FACTORY_TOKEN_FILE` is as given.
- A failing `mkdir`, `cp` or `chmod` of the copy stops with `job-start: token-file: failed`, status 1.
- In the `proxy` step, when `HTTPS_PROXY` or `https_proxy` is set (the first of the two that is not empty, as now), all four of `HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY` and `http_proxy` are exported with that value, except that a `HTTP_PROXY` or `http_proxy` the job set itself keeps its own value. The `apt` configuration file written by the step is unchanged.

Tests: the existing job-start test modules and `tests/vm_support.py` are the pattern; a new `tests/test_vm_job_start_environment.py` holds this story's, with the stand-ins of `JOB_STAND_INS` recording the environment they are started with. No earlier test changes.

## Acceptance criteria

1. The environment `factory-run` is started with has a `PATH` whose first entry is `<root>/tools/bin` and whose remaining entries are the `PATH` the script was started with, in order.
2. The environment the `podman build` stand-in is started with has the same `PATH`.
3. A token file in a folder that has mode 0755 is copied: `FACTORY_TOKEN_FILE` in the environment of `factory-run` is `<root>/secrets/hosting-token`, that folder has mode 0700 and the file mode 0600, the copy equals the original, the original is unchanged, and standard output holds the line `job-start: token-file: copied to <root>/secrets`.
4. A token file in a folder of mode 0700 owned by the running user is not copied: `FACTORY_TOKEN_FILE` in the environment of `factory-run` is the path given, `<root>/secrets` does not exist, and no `token-file` line is printed. A folder of mode 0750 and a folder of mode 0705 are copied (two more rows of the test of criterion 3: any bit for group or others counts).
5. The token's text is in no line the script prints (a token file holding `TOKENMARK` and a search of standard output and standard error).
6. A copy that fails (`<root>/secrets` made impossible by a file of that name) stops with `job-start: token-file: failed` on standard error and status 1, and `factory-run` is not started.
7. A missing or unreadable token file stops as before: `job-start: FACTORY_TOKEN_FILE is not a file`, status 2 (the existing behaviour, one row).
8. With only `https_proxy=P` given, the environment of the `podman build` stand-in has `HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY` and `http_proxy` all equal to `P`; with `HTTPS_PROXY=P` only, the same; with `https_proxy=P` and `http_proxy=Q`, `http_proxy` stays `Q` and `HTTP_PROXY` is `P` (three rows of one parametrized test).
9. With no proxy given, none of the four is set in the environment of the stand-ins and the `apt` configuration file is not written (the existing behaviour, one row).
10. The steps still print in their order and names: `inputs`, `proxy`, `packages`, `runc`, `metadata`, `directories`, `storage`, `code`, `tools`, `image`, `token`, `start` (the existing tests keep passing unchanged).
11. `make check` stays green.
12. docs: `docs/operator-guide.md` in *What the job needs*: the proxy sentence says that the script exports all four spellings and why (the image's package manager fetches over HTTP); the secrets sentence says that a mounted secret may be given as it is, because the script copies it into a private folder when its own folder is not private; the *Environment* table's `FACTORY_TOKEN_FILE` row says so too; *The steps* names the `PATH`; `README.md` and the other documents: none.

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
