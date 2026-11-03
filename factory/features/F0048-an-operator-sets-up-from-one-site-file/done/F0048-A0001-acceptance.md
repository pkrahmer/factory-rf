---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 511
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-03T02:17:44.580565Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-11-03T02:20:30.364966Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-11-03T02:20:31.957767Z'
  stage: acceptance
- number: 4
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-03T02:31:42.051095Z'
  stage: acceptance
  run: ba67ca6b621e4c7b9d8af49d3406b356
- number: 5
  speaker: factory
  kind: done
  at: '2026-11-03T06:30:38.183705Z'
  stage: done
stories: [F0048-S0001, F0048-S0002, F0048-S0003, F0048-S0004, F0048-S0005, F0048-S0006, F0048-S0007, F0048-S0008, F0048-S0009, F0048-S0010, F0048-S0011, F0048-S0012, F0048-S0013]
outcome: accepted
---

# Acceptance of An operator sets up from one site file

## Recommendation

**not accepted.** Every scope item of `feature.md` has its story, `make check` is green, and the feature's walk-through runs green against the real scripts. It goes from `site init` to `site check: ready`, through a job created, executed, watched and refused where it must be, to the skill reading and commenting through the token command, with the token in no argument list. But `operator/site.env.example`, the file the Goal tells a newcomer to copy and fill in, still carries S0001's guessed comments. Eight of the keys that `job.sh` requires are called optional, and six defaults differ from what `job.sh` and `sanitise` do. The guide sends the reader to that file: "it is the first place to look" and "the defaults are those of the example's comments" (`docs/operator-guide.md:943`), although the guide's own table below that line gives other defaults. That is a contradiction between documentation and behaviour that misleads a user: a line deleted as "optional" silently gives another job size. The repair is one small story (F0048-S0014); with it merged, the feature would be `accepted with stories`. The other two proposals are stale text and hardening.

## 1 Scope

None missing. Each of the twelve scope bullets has its story in `done/` and its code: the site file, loader, example and `site path|init|show|get|check` (`operator/lib/site.sh`, `operator/bin/site`, S0001, S0009); `vm/job-start.sh`'s `PATH`, private token copy and four proxy spellings (S0002); `operator/lib/hosting.sh` with `hosting_token`, `hosting_api`, `hosting_repo_api`, `hosting_git` (S0003); the six skill scripts on that client (S0004; no `gh` call is left in `operator/skill/kumpel/scripts/`); `operator/job/job.sh` `create|update|execute|delete` (S0005) and `log|status` (S0007); `operator/bin/sanitise` (S0006); `merge.sh`, `reset-to-tag.sh` (S0008); the guide's chapter *Setting up an operator's machine* (S0009); the job's ten-minute machine stop (S0010, the only change under `src/factory/`, as *Out of scope* allows); the reviewer's five groups (S0011); Kumpel's signature and `comment.sh` (S0012). S0013 (no pause after an active tick) is not a scope bullet, but `feature.md`'s decision 17 and its build order name it, so it came in with the human's leave. No story is outside the scope.

The Goal is reached as a whole: "copies `site.env.example`, fills in the values, runs `site check`, and is ready". The walk below goes that way. One part of the Goal is reached with a defect: the example's comments describe another `job.sh` than the one built (see 5).

## 2 Feature smoke test

A walk-through as an operator on a new machine: an empty `HOME`, `site init`, the values filled in, `site check`, the job's whole life through `job.sh`, the log sanitised and proved clean, the skill's `status.sh` and `comment.sh` through `SITE_TOKEN_CMD`, and at the end the token searched in every recorded argument list. Stand-ins replace only `gcloud` and `curl` (decision 10); git is real (the checkout is a clone, `SITE_CODE_URL` is this repository). The last two blocks test what the example's comments promise.

Command, run from the checkout's root: `sh "$d/feature-smoke.sh"`, where the script is:

```sh
#!/bin/sh
set -u
repo=$(pwd)
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
export HOME="$d/home"; mkdir -p "$HOME" "$d/bin"; unset XDG_CONFIG_HOME XDG_STATE_HOME FACTORY_SITE
rec="$d/calls"; : >"$rec"
cat >"$d/bin/gcloud" <<'G'
#!/bin/sh
printf 'gcloud %s\n' "$*" >>"$REC"
case "$*" in
  "run jobs list"*) exit 0 ;;
  "secrets describe"*) exit 0 ;;
  "run jobs describe"*) [ -f "$STATE/created" ] && exit 0; echo "ERROR: not found" >&2; exit 1 ;;
  "run jobs create"*) touch "$STATE/created"; echo "Job created" ;;
  "run jobs executions list"*"--format=json"*)
    printf '[{"metadata":{"name":"factory-x1"},"status":{"failedCount":1,"startTime":"2026-11-03T01:00:00Z","completionTime":"2026-11-03T01:12:00Z","conditions":[{"status":"False","message":"Task failed with exit code 1"}]}}]\n' ;;
  "run jobs executions list"*) [ -f "$STATE/executed" ] && printf 'factory-x1\t1\n'; exit 0 ;;
  "run jobs execute"*) touch "$STATE/executed"; echo factory-x1 ;;
  "logging read"*)
    printf '01:00:01\tGet:1 http://deb.example.invalid trixie InRelease\n'
    printf '01:00:05\tpreflight: tool:uv ok\n'
    printf '01:02:00\tclone https://git.corp.example.invalid/owner/repo.git\n'
    printf '01:02:01\tauth ghp_abcdefghijklmnopqrstuvwxyz0123\n'
    printf '01:02:02\tstop machine preflight_failed: tool:uv: uv is not on the PATH\n' ;;
  *) echo "unexpected gcloud $*" >&2; exit 9 ;;
esac
G
cat >"$d/bin/curl" <<'C'
#!/bin/sh
printf 'curl %s\n' "$*" >>"$REC"
cfg=$(cat)
url=$(printf '%s\n' "$cfg" | sed -n 's/^url = "\(.*\)"$/\1/p')
printf 'url %s\n' "$url" >>"$REC"
case $url in
  */repos/owner/repo) printf '{"full_name":"owner/repo","permissions":{"push":true}}' ;;
  */repos/owner/repo/pulls*) printf '[{"number":7,"head":{"ref":"work-item/F0001-S0001"},"labels":[{"name":"stage:approval"}]}]' ;;
  */repos/owner/repo/issues/7) printf '{"comments":0}' ;;
  */repos/owner/repo/commits*) printf '[{"sha":"%s","commit":{"message":"work item F0001-S0000: merged, archived"}}]' aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ;;
  *) printf '[]' ;;
esac
printf '200' >&2
C
chmod +x "$d/bin/gcloud" "$d/bin/curl"
export PATH="$d/bin:$PATH" REC="$rec" STATE="$d"
git clone -q "$repo" "$d/checkout" && git -C "$d/checkout" remote set-url origin https://git.example.invalid/owner/repo.git

echo '$ site path';  sh operator/bin/site path | sed "s|$d|<d>|"
echo '$ site init';  sh operator/bin/site init | sed "s|$d|<d>|"
echo '$ site show | head -3'; sh operator/bin/site show | head -3
echo '$ site check (example values)'; sh operator/bin/site check | tail -1
f=$(sh operator/bin/site path)
python3 - "$f" "$d" <<'P'
import sys, re
f, d = sys.argv[1:]
values = {"SITE_CHECKOUT": d + "/checkout", "SITE_TOKEN_CMD": "printf tok-s3cret-value",
          "SITE_CODE_URL": "file:///work/checkout", "SITE_NO_PROXY": "localhost,models.example.invalid",
          "SITE_SANITISE_RULES": "sanitise.rules"}
out = []
for line in open(f).read().splitlines():
    m = re.match(r"(SITE_[A-Z_]+)=", line)
    if m and m.group(1) in values:
        line = m.group(1) + "=" + values[m.group(1)]
    out.append(line)
open(f, "w").write("\n".join(out) + "\n")
P
printf 'corp\\.example\\.invalid => <company-host>\n' >"$(dirname "$f")/sanitise.rules"
echo '$ site check (filled in)'; sh operator/bin/site check
echo '$ job.sh create --dry-run | head -3'; sh operator/job/job.sh create --dry-run | head -3
echo '$ job.sh create'; sh operator/job/job.sh create; echo "status $?"
echo '$ job.sh create (again)'; sh operator/job/job.sh create; echo "status $?"
echo '$ job.sh execute'; sh operator/job/job.sh execute; echo "status $?"
echo '$ job.sh execute (again)'; sh operator/job/job.sh execute; echo "status $?"
echo '$ job.sh status'; sh operator/job/job.sh status; echo "status $?"
echo '$ job.sh log --quiet'; sh operator/job/job.sh log --quiet >"$d/log.txt"; cat "$d/log.txt"
echo '$ sanitise check log'; sh operator/bin/sanitise check "$d/log.txt"; echo "status $?"
echo '$ status.sh'; sh operator/skill/kumpel/scripts/status.sh; echo "status $?"
echo '$ comment.sh 7'; printf 'Approved.\n' >"$d/c.txt"; sh operator/skill/kumpel/scripts/comment.sh 7 "$d/c.txt"; echo "status $?"
echo '$ job.sh delete'; sh operator/job/job.sh delete; echo "status $?"
echo '$ token in any argument list?'; grep -c 'tok-s3cret' "$rec"
echo '$ the example says SITE_INSTANCE is optional (default: the job name); unset it:'
sed -i '/^SITE_INSTANCE=/d' "$f"; sh operator/job/job.sh create --dry-run >/dev/null; echo "status $?"
echo '$ the example says SITE_CPU defaults to 4; unset it:'
sed -i '/^SITE_CPU=/d' "$f"; printf 'SITE_INSTANCE=example-instance\n' >>"$f"; sh operator/job/job.sh create --dry-run | grep -e '--cpu' -e '--memory' -e '--task-timeout'
```

What it printed (the temporary folder shown as `<d>`):

```text
$ site path
<d>/home/.config/kumpel/site.env
$ site init
site: wrote <d>/home/.config/kumpel/site.env; edit it, then run: site check
$ site show | head -3
SITE_REPOSITORY=set
SITE_CHECKOUT=set
SITE_API_URL=set
$ site check (example values)
site: 5 failed
$ site check (filled in)
ok site file
ok keys
ok tools
ok token
ok repository
ok checkout
ok identity
ok secrets
ok code
ok no_proxy
ok job: example-factory does not exist yet
site: ready
$ job.sh create --dry-run | head -3
gcloud
run
jobs
$ job.sh create
Job created
status 0
$ job.sh create (again)
job: example-factory exists; use update
status 1
$ job.sh execute
factory-x1
status 0
$ job.sh execute (again)
job: an execution of example-factory is still running: factory-x1; two executions of one instance must not overlap
status 1
$ job.sh status
factory-x1 failed started 01:00 ended 01:12: Task failed with exit code 1
factory: stopped: 01:02:02	stop machine preflight_failed: tool:uv: uv is not on the PATH
status 0
$ job.sh log --quiet
01:00:05	preflight: tool:uv ok
01:02:00	clone https://git.<company-host>/owner/repo.git
01:02:01	auth ***TOKEN***
01:02:02	stop machine preflight_failed: tool:uv: uv is not on the PATH
$ sanitise check log
sanitise: clean
status 0
$ status.sh
#7 F0001-S0001 stage:approval waits: approval
last archive: work item F0001-S0000: merged, archived
status 0
$ comment.sh 7
commented #7
status 0
$ job.sh delete
job: would delete example-factory and stop its running execution; run again with --yes
status 1
$ token in any argument list?
0
$ the example says SITE_INSTANCE is optional (default: the job name); unset it:
site: missing SITE_INSTANCE in <d>/home/.config/kumpel/site.env
status 2
$ the example says SITE_CPU defaults to 4; unset it:
--cpu=8
--memory=16Gi
--task-timeout=24h
```

Green as the feature promises: `site check` goes from `site: 5 failed` (the example's own values) to `site: ready`. `create` refuses an existing job, `execute` refuses an overlap, and `status` names the platform's failure and the factory's stop. `log --quiet` drops the package noise, the site's rule and the built-in token rule replace the company host and the token, and `sanitise check` proves the result clean. The skill's scripts work through `SITE_TOKEN_CMD` with no `gh` on the path, and the token appears in none of the 30-odd recorded argument lists. My script's first run had two faults of its own, both fixed before the run above: its clone had no `main` branch for `check code`, and its log stand-in used a stop line that is not the factory's form (`stop <scope> <reason>: <detail>`, `src/factory/application/stops.py:43`).

The last two blocks are finding 5.1: the example calls `SITE_INSTANCE` optional, with the job's name as its default, and `job.sh` refuses it as missing (status 2). It gives `SITE_CPU` a default of 4, and the job gets `--cpu=8`. The other two lines show the example's own values (`16Gi`, `24h`) passed through as written.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Collected from the coders' "noticed, not touched", the documenters' stale text and the reviewers' notes. I left out what a later story of the feature settled: `job.sh`'s usage line now names `log` and `status` (S0007), the references no longer name `gh` (S0012), `site check` shares `site_job_keys` and `site_gcloud_with` with `job.sh` through `operator/lib/site.sh` (S0009), the `@` and price checks exist (S0005), and the guide's "`site check` does not exist yet" is gone (S0009).

- **The example's defaults were the coder's guess and nobody confirmed them** (S0001 entries 10 to 44, reviewer 46; S0005 documenter 41; S0006 documenter 33; S0009 documenter 28). They still stand: see 5. Proposed as F0048-S0014.
- **`site`'s generic usage line does not name `check`** (`operator/bin/site:15`; S0009 documenter 28). Pinned by `tests/test_operator_site.py:55`. Folded into F0048-S0015, which names the leave that test change needs.
- **`operator/README.md` is stale** (S0001 coder 44 and documenter 48; S0004 coder 10). *Installing* still says the skill's first act asks for the repository and the checkout, and does not mention `site init` or `site check`. *Needs* still says "`gh` logged in". **`SKILL.md:12`** still says to ask the human when the settings are missing, with no word of the site file (S0004 documenter 25). Proposed as F0048-S0015.
- **A failed read of the code host is followed by a Python traceback** in `status.sh` (S0004 coders 10 to 21, documenter 25), and in `reset-to-tag.sh` after a failed GET of the pull requests or the branches (S0008 coders 13 and 17). I confirmed `status.sh` today: with a 500 on `/issues/7` it prints `hosting: GET /repos/owner/repo/issues/7: 500 Server Error`, then a 14-line `JSONDecodeError` traceback, and exits 1. Proposed as F0048-S0016 (`status.sh`; the story reads `merge.sh` and `reset-to-tag.sh` as already assigning the answer before parsing it).
- **`hosting_api` drops curl's own error text on a failed transfer** and says only `no answer` (S0003 coders 22 to 38). This was a deliberate Interface choice; a note, no story.
- **`hosting.sh`'s self-load looks at `env`, so a `SITE_` value set but not exported still triggers `site_load`** (S0003 coder 18). A note, no story.
- **`HealthStatus.with_stop` moves a re-raised stop's `at` forward**, so `health.json` shows the last raise, not the first (S0010 coder 10 to 18, documenter 22). The decision log records it as a rejected change. This matters to S0010's ten minutes only if someone reads `at` as the stop's start. A note for the human, no story.
- **A replaced `hosting-token` keeps its old mode between `cp` and `chmod`** (S0002 coder 15). Harmless inside the 0700 folder. A note.
- **`status.sh` and `job.sh` run `python3 -c` without `-I`, while `sanitise` uses `-I`** (S0006 reviewer side note, coders 14 to 29). Without `-I`, Python puts the current folder first on the import path, so a script run in a checkout where agents write files would import a planted `json.py`. F0048-S0016 makes every start isolated.
- **An execution with no `startTime` prints `started -`, and `status` with an empty list but a `last-execution` file reads that file's execution and prints no `no execution` line** (S0007 coders 10 and 17). Edge cases with no criterion. A note.
- **Test-side duplicates the reviewers named as notes** (S0003 reviewers 20 to 40, S0004 23, S0005 20 and 24, S0006 23 and 31, S0007 27, S0008 27 and 35, S0009 26, S0010 20, S0012 23): `test_operator_merge_reset.py` copies `SCRIPTS`, `REPOSITORY`, `PREFIX`, `API_URL` and `ACCESS_COMMAND` and the URL parsing of `test_operator_skill_scripts.py`; `test_operator_sanitise.py:47` `write_file` beside `git_support.write_files`; `test_operator_skill_scripts.py` `make_bare_remote` beside `git_support.make_remote`; `Operator.urls()` beside `recorded_requests`; `test_run_machine_stop_exit.py` `_log` beside `test_run_idle_exit.py`'s; and some parametrize merges. These are the tester's under the standing leave, with no behaviour behind them. No story. The tester of any later operator story may take them.
- **The guide's *What the job needs* advises "Eight vCPUs and 16 GiB of memory at least"** while `job.sh`'s default is 32Gi (S0005 documenter 41, S0009 documenter 28). That is advice, not a contradiction. A note.

## 5 Documentation as a whole

I read `README.md` (line 28 points at the guide's new chapter and at `operator/README.md`) and the guide's chapters *The site file*, *Setting up an operator's machine*, *Creating the job* and *Watching the job* through. The guide's key table (`docs/operator-guide.md:941`) and its table of `job.sh`'s keys give the same required keys and defaults as `operator/lib/site.sh:12` and `operator/job/job.sh:89-183`. But the sentence above the table defers to the example. Findings:

1. **`operator/site.env.example` contradicts the scripts, and the guide sends the reader to it.** It is the file `site init` copies and the Goal's newcomer edits. Eight of the 18 keys that `job.sh` requires are called "Optional": `SITE_PROXY` ("the default is no proxy"), `SITE_NO_PROXY`, `SITE_INSTANCE` ("the default is the job's name"), `SITE_CODE_REF` ("the default is main"), `SITE_MODEL_BASE_URL` ("the provider's public API"), and `SITE_LOGIN_URL`, `SITE_LOGIN_SCOPE` and `SITE_LOGIN_CLIENT_ID` ("the default is no login"). Defaults that differ: `SITE_CPU` 4 (the code uses 8), `SITE_MEMORY` 16Gi (32Gi), `SITE_TIMEOUT` 24h (14400 seconds), `SITE_IDLE_MINUTES` 30 (60), `SITE_MODEL_*_COST` "no cost record" (0), and `SITE_SANITISE_RULES` "none" (`sanitise.rules` beside the site file). Two blocks of the smoke test show it. This misleads: a user who keeps the example's `SITE_CPU=4` runs below the guide's eight-CPU minimum. A user without a proxy learns at `site check` that the "optional" proxy is required. `site check` does make every missing required key loud before anything is created. But `docs/operator-guide.md:943` calls the example "the first place to look" and says "the defaults are those of the example's comments and are confirmed as the stories that read each key land". The table right below that line gives other defaults, so the guide contradicts itself and sends the reader to the wrong one. This finding sets the recommendation (F0048-S0014, whose docs criterion rewrites that sentence).
2. **`operator/README.md` and `SKILL.md` speak of the setup before this feature** (see 4; F0048-S0015).
3. **The guide's intro to *The site file* (`docs/operator-guide.md:902`) still says "the stories to come make the other keys live"**. Every story has come, so the sentence is stale now (S0006 and S0007 documenters kept it as true until the last story). F0048-S0014's docs criterion drops it.
4. **The guide documents `site`'s usage line as it is** (`docs/operator-guide.md:932`, without `check`). It follows the code, and it changes with F0048-S0015.

No example that no longer runs: the guide's blocks at `:935`, `:1000` and `:1066` match the commands I ran. No section that the feature needs is missing.

## 6 Decisions taken for the human

The 17 decisions of `feature.md`'s *Decisions taken for the human* stand as built. I found no story that departs from one. In addition, from the journals, for the human to accept or revisit:

1. **`SITE_PROXY`, `SITE_NO_PROXY` and the three `SITE_LOGIN_*` keys are required for every job** (`site_job_keys`, S0005). So a site with no proxy, or a model provider without an OAuth login, cannot use `job.sh` at all. The example said otherwise. F0048-S0014 as proposed follows the code. If these keys should be optional, refine it the other way before starting it.
2. **The job's defaults are 8 CPUs, 32Gi, 14400 s and 60 idle minutes** (S0005, the guide's table), not the example's 4, 16Gi, 24h and 30.
3. **A job needs the `https://` form of the repository URL**, because `@` is the env list's delimiter (S0005, the human's answer in entry 37).
4. **A sanitiser replacement is literal except `\1` to `\99`**, and a group beyond the pattern's is a rules-file fault (S0006, the human's answer in entry 15).
5. **`hosting_api` needs curl 7.63 or later** (`%{stderr}` in `--write-out`; S0003 coder 22 and reviewer 32). It reports a failed transfer as `no answer`, without curl's own text.
6. **`site check`'s `job` line is informational and never fails**: a missing job and a failed describe both read "does not exist yet" (S0009, the human's answer in entry 4).
7. **The site file's whitespace rule**: a space before `=` is a fault, a space after it belongs to the value (S0001, the human's answer in entry 15).
8. **`operator/README.md` is the coder's, not the documenter's** (S0001, the human's answer in entry 42).
9. **The reviewer's notes rule**: a missing side that the code already handles and that needs only a test row is a note, not a reason to send a story back (the human, S0001 entry 33, S0003 entry 30, S0005 entry 26). It is stated three times in answers, never in `docs/decisions.md` or the reviewer's text. If it is lasting, it belongs there.

Earlier tests changed, each with its leave as the final review names it:

- `tests/vm_support.py` (`token.parent.chmod(0o700)` in `run_job_start`): the human's leave, S0002 entry 9.
- `tests/test_tmp_path_reopening.py`, `tests/tmp_path_support.py` (`file_mode`): standing leave, S0002.
- `tests/test_operator_hosting.py`, `tests/operator_support.py` (`CURL_STAND_IN`, `hosting_env` moved): standing leave, S0004. `tests/test_operator_hosting.py`, `tests/recording_stand_in_support.py` (`read_records`): standing leave, S0005.
- `tests/test_operator_job.py` (`USAGE`): the human's leave, S0007 entry 11. Its `JOB`, `IMPERSONATE`, `BARE` and `words` moved to `tests/operator_job_support.py`: standing leave.
- `tests/conftest.py`, `tests/entry/test_run_idle_exit.py` (fixtures and the scripted tick moved to `tests/scripted_tick_support.py`, made generic): standing leave, S0010.
- `tests/test_claude_agent_texts.py:120` (the reviewer's anchor): the human's leave, S0011 entry 8.
- `tests/test_operator_skill_scripts.py`, `tests/conftest.py` (`Operator` moved to `tests/operator_skill_support.py`): standing leave. The row `verdict-fourth-from-the-end`: the human's leave, S0012 entry 15. `tests/test_operator_merge_reset.py` (S0008's test made one row per field): S0012's criterion 5, a leave the human gave in the story they wrote, not in `feature.md`'s *The human's changes*. It is named, so it is no finding, but the form puts such a leave in `feature.md`.
- `tests/application/test_scheduler.py` (four tests under the new rule, one table test renamed): the human's leave, S0013 entry 6.

No earlier test was changed without a leave named.

## 7 Slow checks

Nothing to run. The `Makefile` offers no image scan or SBOM beyond `make check`. `duplicates` is the reviewer's record and `documents` is the docs stage's check, and `mutants` falls under 3.

The JUnit report of my `make check` (`.reports/junit.xml`, 8494 tests) has the slowest tests at 10 s each, all `ROOMY_LIMIT` tests outside this feature (`tests/adapters/test_podman_timeout_status.py`, `test_opencode_budget.py`, `test_claude_runtime_resume.py`, `test_process_session.py`). The feature's own modules come to 580 tests and 46.5 s of the 699.5 s summed test time: `test_operator_site_check` 10.8 s, `test_operator_merge_reset` 8.0 s, `test_vm_job_start` 6.3 s, `test_operator_job` 6.0 s. `make test` took 81.8 s on all cores.

Disk: at the previous record (`disk start`) all three paths had 32.7 GB free; now (`disk acceptance`) they have 30.2 GB free. They share one pool, and the instance's own figures are unchanged: `/srv/factory/vm` 1.3 GB used, its state and `/tmp` 0.0 GB. The 2.5 GB less free space therefore lies outside the measured datasets. The feature's changes (shell scripts, tests and documents, well under a megabyte) do not explain it. Container images or caches elsewhere on the pool are the likely cause, but I did not measure them. Unexplained.

## 8 Cost

The stories cost 187 runs, 273.1 minutes, 1575 turns and $69.70 (5.84 M tokens in, 41.86 M more from cache, 0.97 M out). By story, from the `.costs.jsonl` files: S0005 $9.15 (19 runs), S0001 $8.48 (22 runs, 47.5 min), S0003 $7.92 (20), S0008 $7.12 (20, two runs `died`), S0009 $6.46, S0006 $5.71, S0007 $5.37, S0004 $4.99, S0010 $4.64, S0012 $3.75, S0002 $2.88, S0013 $1.77, S0011 $1.44. S0001, S0003 and S0005 stand out, and their journals say why. Each review stopped at the first failing group, so each round brought the next group's findings, and all three reached the review round cap (feature.md decision 15). In those three the reviewer is the most expensive role, $3.22 to $3.82 in five or six runs. After S0011 made the reviewer judge all five groups, no story reached the round cap again, and the later stories cost between $1.44 and $7.12.

Human interventions: 28 questions answered: 24 questions, 1 `attempts_cap`, 3 `round_cap`. The stories waited 4.3 h for them. Twelve of the questions were intake's, one per story but S0011. The story that needed the human most is S0001: four questions, a round cap among them, and 57 minutes of waiting. Its journal shows the first-group-only reviews and the question of who owns `operator/README.md`. The longest single wait is S0008's: 121 minutes, almost all of it its `attempts_cap` at docs. Both docs runs ended at the provider's usage limit, and the human answered "Retry" once the limit had reset (entry 41).

## Proposed stories

- `F0048-S0014-the-site-file-s-example-names-the-required-keys-and-the-defaults-that-job-sh-uses.md`: the example's comments follow `site_job_keys`, `job.sh`'s defaults and `sanitise`'s rules file, pinned by a test. The guide's "defaults are those of the example's comments" and its "stories to come" go. This repairs finding 5.1, which makes the recommendation `not accepted`.
- `F0048-S0015-the-operator-s-readme-the-skill-and-site-s-usage-name-the-site-file.md`: `operator/README.md`'s *Installing* and *Needs*, `SKILL.md`'s first step and `site`'s usage line describe the setup with the site file. It needs the human's leave for the `USAGE` constant of S0001's test, or it drops that criterion.
- `F0048-S0016-the-operator-s-scripts-run-python-isolated-and-stop-at-a-failed-read-with-the-hosting-message.md`: every `python3` start in the operator's scripts is isolated (`-I`), and `status.sh` stops at a failed read with the hosting client's message and no traceback.

**A note on how this report came about.** The factory recorded a crash of this stage at 02:20:30 and discarded its work. But a second acceptance run kept writing in the same dataset: it wrote the three stories above into `backlog/` at 02:26 and a whole report of its own into this file before 02:29. Its process is not in this run's container. I found its report after I inserted mine. I checked its three stories with `factory-check-story` (all `ok`) and read them against my own findings. They cover the same changes (with one key more in S0014, `SITE_MODEL_BASE_URL`, which I confirmed), so I kept them instead of writing three more stories under the same numbers. I removed its duplicate report and took over its one finding that I had missed, `docs/operator-guide.md:943`, which changed my recommendation from `accepted with stories` to `not accepted`. The human may want to see why the crashed run's agent went on after the crash was recorded.

## Journal

1. factory: started acceptance as vm.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit a39b515adb0eb52dc2a98cc908bf45dd5841a18a.
3. factory: started acceptance as vm.
4. acceptance-reviewer: not accepted; 3 stories proposed (F0048-S0014, F0048-S0015, F0048-S0016).
   1 Scope: none missing. All twelve scope bullets have their stories and code; S0013 is outside the bullets but came in with the human's leave (decision 17); the Goal's path from site init to site check works.
   2 Feature smoke test: green. One script with only gcloud and curl as stand-ins ran site init, then site check (5 failed, then ready), job.sh create/execute/status/log --quiet/delete with every refusal, sanitise check clean, and status.sh and comment.sh through SITE_TOKEN_CMD. The token was in none of the recorded argument lists. Two blocks show the example's comments are wrong: SITE_INSTANCE called optional but refused when missing, and SITE_CPU said to default to 4 but the job gets --cpu=8.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the example's defaults were S0001's guess and no story ever confirmed them. Also still standing: operator/README.md's Installing and Needs and SKILL.md step 1 predate the site file; site's usage line leaves out check; status.sh prints a Python traceback after a failed read; python3 runs without -I. Notes only: curl's error text is dropped, and HealthStatus.with_stop moves at forward. Test-side duplicates are left to the tester.
   5 Documentation: operator/site.env.example calls 8 required keys optional and gives 6 wrong defaults. docs/operator-guide.md:943 calls the example "the first place to look" and says the defaults are the example's, while its own table below gives other values. This is a contradiction that misleads a user, and it sets the recommendation. The guide's "stories to come" sentence is now stale.
   6 Decisions: the 17 decisions in feature.md stand, and 9 more are listed for the human (proxy and login keys required for every job, the job's defaults, https URLs only, the sanitiser's \1–\99 rule, curl 7.63 or later, the job check never fails, the whitespace rule, operator/README.md belongs to the coder, the reviewer's notes rule). Every earlier test that changed has its leave named. S0012 changed S0008's test under a leave given in the story, not in feature.md.
   7 Slow checks: none beyond make check (green, test 81.8 s). The slowest tests are 10 s ROOMY_LIMIT tests outside the feature; the feature's tests take 46.5 s. Free disk fell 2.5 GB with the instance's used space unchanged; the feature does not explain it.
   8 Cost: $69.70 over 187 runs. S0005 ($9.15), S0001 ($8.48) and S0003 ($7.92) stand out: their reviews stopped at the first failing group until S0011. 28 questions (24 questions, 1 attempts_cap, 3 round_cap) and 4.3 h waited. S0001 needed the human most (4 questions, 57 min). The longest single wait was S0008's 121 min, at a provider usage limit.
   Open: a second acceptance run kept writing in this dataset after the crash recorded at 02:20:30. It wrote the three backlog stories at 02:26 and a whole report of its own. I checked its stories with factory-check-story (all ok) and kept them, removed its duplicate report, and took over its one finding I had missed (guide line 943), which changed my recommendation from accepted with stories to not accepted. The human may want to look into why the crashed run went on writing. My temporary script folder /tmp/acc-smoke-script could not be removed: the rm was denied.
5. factory: done (pull request merged); cost: 1 runs, 11.1 min, 49 turns, 154875 tokens in (4734970 more from cache), 43838 out, $3.06
