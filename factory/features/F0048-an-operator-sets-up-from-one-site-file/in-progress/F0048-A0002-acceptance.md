---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 516
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-03T09:16:50.968020Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-03T09:25:41.215637Z'
  stage: acceptance
  run: 844407f8c67c4ec9a5896c537ecb399b
stories: [F0048-S0001, F0048-S0002, F0048-S0003, F0048-S0004, F0048-S0005, F0048-S0006, F0048-S0007, F0048-S0008, F0048-S0009, F0048-S0010, F0048-S0011, F0048-S0012, F0048-S0013, F0048-S0014, F0048-S0015, F0048-S0016, F0048-S0017]
outcome: null
---

# Acceptance of An operator sets up from one site file

## Recommendation

**accepted with stories.** Every scope item of `feature.md` has its story and its code, and `make check` is green. The feature's walk-through runs green end to end, from `site init` through `site check: ready`, the job's whole life and the skill's scripts. The finding that made F0048-A0001 `not accepted` is repaired: removing each of the example's 31 keys one at a time shows `job.sh` doing what the key's comment says, with no mismatch. What is left has no broken promise in it. Three passages of the operator guide still advise against what the factory now does: "Eight vCPUs ... at least" against the default of 4, a 23-hour timeout for a daily schedule against the default of 24 hours, and "no text that says why" for a died run. They are one small documents-only story (F0048-S0018). Separately, `feature.md`'s *Scope* and *Out of scope* no longer describe four stories that the human added with their own decisions; that file is the human's to update.

## 1 Scope

The twelve scope bullets are all built, as F0048-A0001 found: the site file and `site` (S0001, S0009), `vm/job-start.sh` (S0002), `operator/lib/hosting.sh` (S0003), the six skill scripts on it (S0004), `job.sh create|update|execute|delete` (S0005) and `log|status` (S0007), `operator/bin/sanitise` (S0006), `merge.sh` and `reset-to-tag.sh` (S0008), `site check` and the guide's chapter (S0009), the job's ten-minute machine stop (S0010, `src/factory/entry/run.py:47`), the reviewer's five groups (S0011) and Kumpel's signature (S0012). Since then, S0014 repaired A0001's three proposals, folded into one story (decision 18): the example's comments, the defaults, `site`'s usage line, `site check`'s `job` line, the fault for a space after `=`, `-I` on every `python3` start, and `status.sh`'s failed reads. I checked each in the code and in the walk below.

One finding, on the feature file rather than the build. Four archived stories lie outside *Scope* as written, and three of them contradict *Out of scope*. S0013 (`src/factory/application/scheduler.py`), S0015 (`src/factory/domain/died_runs.py`, `agent_launch.died_text`, the stage's log line), S0016 (`PodmanRuns(instance=...)`, `vm/factory.service`'s `ExecStopPost`) and S0017 (`claude/agents/reviewer.md`) appear in *Stories* and in decisions 17, 19, 20 and 23, but not among the *Scope* bullets. *Out of scope* still says "The factory's own code under `src/factory/`: nothing here changes it, except S0010's rule for a machine stop in a job", and S0013, S0015 and S0016 all change `src/factory/`. Each came in by the human's hand, with its reason recorded, so it is no scope creep by an agent. But a reader of `feature.md` alone gets a wrong picture of what F0048 changed. The fix is the human's (R14): two bullets of *Scope* and one clause of *Out of scope*. No story.

The Goal is reached: "copies `site.env.example`, fills in the values, runs `site check`, and is ready". The walk below goes exactly that way.

## 2 Feature smoke test

A walk-through as an operator on a new machine, with an empty `HOME`. It runs `site` without arguments, `site init`, fills in the values and runs `site check`. Then the job's whole life through `job.sh`, the log sanitised and proved clean, and the skill's `status.sh` and `comment.sh` through `SITE_TOKEN_CMD`. Then what S0014 to S0016 added: the `job` line for an unreadable job, the fault for a space after `=`, `status.sh` run from a folder with a planted `json.py` and with a failing read, every key of the example removed in turn against `job.sh create --dry-run`, a died run's log line through the library, and the unit's stop line. Stand-ins replace only `gcloud` and `curl` (decision 10). git is real: the checkout is a clone, and `SITE_CODE_URL` is this repository.

Command, run from the checkout's root: `sh "$w/feature-smoke.sh"`, with `w=$(mktemp -d)`, where the script is:

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
  "run jobs describe"*)
    [ -n "${DESCRIBE_DENIED:-}" ] && { echo "ERROR: (gcloud.run.jobs.describe) PERMISSION_DENIED: Permission 'run.jobs.get' denied" >&2; exit 1; }
    [ -f "$STATE/created" ] && exit 0
    echo "ERROR: (gcloud.run.jobs.describe) Cannot find job [example-factory]." >&2; exit 1 ;;
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
  */repos/owner/repo/issues/7)
    if [ -n "${FAIL_ISSUE:-}" ]; then printf '{"message":"Server Error"}'; printf '500' >&2; exit 0; fi
    printf '{"comments":0}' ;;
  */repos/owner/repo/commits*) printf '[{"sha":"%s","commit":{"message":"work item F0001-S0000: merged, archived"}}]' aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ;;
  *) printf '[]' ;;
esac
printf '200' >&2
C
chmod +x "$d/bin/gcloud" "$d/bin/curl"
export PATH="$d/bin:$PATH" REC="$rec" STATE="$d"
git clone -q "$repo" "$d/checkout" && git -C "$d/checkout" remote set-url origin https://git.example.invalid/owner/repo.git
S="$repo/operator/bin/site"; J="$repo/operator/job/job.sh"; K="$repo/operator/skill/kumpel/scripts"

echo '$ site';       sh "$S"; echo "status $?"
echo '$ site init';  sh "$S" init | sed "s|$d|<d>|"
echo '$ site check (example values)'; sh "$S" check | tail -1
f=$(sh "$S" path)
python3 - "$f" "$d" "$repo" <<'P'
import sys, re
f, d, repo = sys.argv[1:]
values = {"SITE_CHECKOUT": d + "/checkout", "SITE_TOKEN_CMD": "printf tok-s3cret-value",
          "SITE_CODE_URL": "file://" + repo, "SITE_NO_PROXY": "localhost,models.example.invalid",
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
echo '$ site check (filled in)'; sh "$S" check
echo '$ site check, job not readable'; DESCRIBE_DENIED=1 sh "$S" check | grep -e '^ok job' -e '^site:'
cp "$f" "$d/site.good"
echo '$ a space after = is a fault'; sed -i 's/^SITE_PROXY=/SITE_PROXY= /' "$f"; sh "$S" show >/dev/null; echo "status $?"; cp "$d/site.good" "$f"
echo '$ job.sh create'; sh "$J" create; echo "status $?"
echo '$ job.sh create (again)'; sh "$J" create; echo "status $?"
echo '$ site check, job exists'; sh "$S" check | grep '^ok job'
echo '$ job.sh execute'; sh "$J" execute; echo "status $?"
echo '$ job.sh execute (again)'; sh "$J" execute; echo "status $?"
echo '$ job.sh status'; sh "$J" status; echo "status $?"
echo '$ job.sh log --quiet'; sh "$J" log --quiet >"$d/log.txt"; cat "$d/log.txt"
echo '$ sanitise check log'; sh "$repo/operator/bin/sanitise" check "$d/log.txt"; echo "status $?"
mkdir "$d/planted"; printf 'open("%s", "w").close()\n' "$d/imported" >"$d/planted/json.py"
echo '$ control: python3 without -I in that folder'; (cd "$d/planted" && python3 -c 'import json'); test -e "$d/imported" && echo "planted json.py imported"; rm -f "$d/imported"
echo '$ status.sh, run in a folder with a planted json.py'; (cd "$d/planted" && sh "$K/status.sh"); echo "status $?"; test -e "$d/imported" && echo "planted json.py imported" || echo "planted json.py not imported"
echo '$ status.sh, the issue read fails'; FAIL_ISSUE=1 sh "$K/status.sh" >"$d/out" 2>&1; echo "status $?"; cat "$d/out"; echo "traceback lines: $(grep -c Traceback "$d/out")"
echo '$ comment.sh 7'; printf 'Approved.\n' >"$d/c.txt"; sh "$K/comment.sh" 7 "$d/c.txt"; echo "status $?"
echo '$ job.sh delete'; sh "$J" delete; echo "status $?"
echo '$ token in any argument list?'; grep -c 'tok-s3cret' "$rec"
echo '$ the example comments against job.sh create --dry-run, one key removed at a time'
python3 - "$repo/operator/site.env.example" "$f" "$J" <<'P'
import re, subprocess, sys
example, f, job = sys.argv[1:]
good = open(f).read()
comment, bad, keys = "", 0, 0
for line in open(example).read().splitlines():
    if line.startswith("# "): comment = line; continue
    m = re.match(r"(SITE_[A-Z_]+)=", line)
    if not m: continue
    key, keys = m.group(1), keys + 1
    open(f, "w").write("".join(l + "\n" for l in good.splitlines() if not l.startswith(key + "=")))
    r = subprocess.run(["sh", job, "create", "--dry-run"], capture_output=True, text=True)
    if "Required for a job." in comment:
        ok = r.returncode != 0 and key in r.stderr
    else:
        ok = r.returncode == 0
        dm = re.search(r"the default is ([^.]+?)\.?$", comment)
        default = dm.group(1) if dm else ""
        flag = {"SITE_CPU": "--cpu=", "SITE_MEMORY": "--memory=", "SITE_TIMEOUT": "--task-timeout=",
                "SITE_IDLE_MINUTES": "FACTORY_IDLE_SHUTDOWN_MINUTES="}.get(key)
        if flag: ok = ok and (flag + default) in r.stdout
    if not ok: bad += 1; print("mismatch", key, r.returncode, r.stderr.strip()[:120])
open(f, "w").write(good)
print(f"{keys} keys, {bad} mismatches")
P
echo '$ a died run in the factory log (the library)'
uv run -q python -c 'from factory.adapters.agent_launch import died_text
from factory.domain.died_runs import died_line
print(died_line("r1", "F0001-S0001", "doing", died_text(None, "warn\n\nAPI Error: 400 flag rejected\n", 1)))
print(died_line("r2", "F0001-S0001", "doing", died_text("", "", 137)))'
echo '$ the service stops its instance'\''s containers'; grep -n 'ExecStopPost' "$repo/vm/factory.service"
```

What it printed (exit status 0; the temporary folder shown as `<d>`):

```text
$ site
usage: site path | init | show | get SITE_X | check
status 2
$ site init
site: wrote <d>/home/.config/kumpel/site.env; edit it, then run: site check
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
$ site check, job not readable
ok job: example-factory cannot be read: ERROR: (gcloud.run.jobs.describe) PERMISSION_DENIED: Permission 'run.jobs.get' denied
site: ready
$ a space after = is a fault
site: <d>/home/.config/kumpel/site.env:14: not a KEY=value line
status 2
$ job.sh create
Job created
status 0
$ job.sh create (again)
job: example-factory exists; use update
status 1
$ site check, job exists
ok job: example-factory exists
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
$ control: python3 without -I in that folder
planted json.py imported
$ status.sh, run in a folder with a planted json.py
#7 F0001-S0001 stage:approval waits: approval
last archive: work item F0001-S0000: merged, archived
status 0
planted json.py not imported
$ status.sh, the issue read fails
status 1
hosting: GET /repos/owner/repo/issues/7: 500 Server Error
traceback lines: 0
$ comment.sh 7
commented #7
status 0
$ job.sh delete
job: would delete example-factory and stop its running execution; run again with --yes
status 1
$ token in any argument list?
0
$ the example comments against job.sh create --dry-run, one key removed at a time
31 keys, 0 mismatches
$ a died run in the factory log (the library)
run r1 of F0001-S0001 (doing) died: warn / API Error: 400 flag rejected
run r2 of F0001-S0001 (doing) died: exit 137
$ the service stops its instance's containers
17:ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i
```

Green. `site check` goes from `site: 5 failed` (the example's own values) to `site: ready`. Its `job` line tells the three cases apart (`does not exist yet`, `cannot be read: <gcloud's first line>`, `exists`) and never fails. `SITE_PROXY= http://...` is refused with its line number. `create` refuses an existing job and `execute` refuses an overlap. `log --quiet` drops the package noise, and the site's rule and the built-in token rule replace the company host and the token. Run from a folder where a plain `python3` imports a planted `json.py` (the control line), `status.sh` does not import it. With a 500 on the issue read it stops with the hosting client's one line, status 1 and no traceback. The token is in none of the recorded argument lists. The 31-key table is the repair of A0001's finding 5.1. Each key marked "Required for a job." is refused by name when missing. Each optional key may be missing, and `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT` and `SITE_IDLE_MINUTES` then give exactly the default their comment names. The library prints the died line in the form the guide gives. My script's first run had one fault of its own: it wrote the planted `json.py` with `printf %r`, which `sh` does not know. I fixed it before the run above.

Not walked: S0010's ten-minute exit and S0013's pause rule need a running factory loop and a clock. Their tests (`tests/entry/test_run_machine_stop_exit.py`, `tests/application/test_scheduler.py`) cover them, and A0001 accepted them. S0016's real stop of containers is the human's check on `vm` (decision 20).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Collected from S0014 to S0017. F0048-A0001 already collected S0001 to S0013. Of its list, these are settled: the example's comments, `site`'s usage, `operator/README.md` and `SKILL.md`, `status.sh`'s traceback, `-I` and the reviewer's notes rule. Its other notes still stand as notes: `hosting_api` drops curl's text, `hosting.sh` loads itself through `env`, `HealthStatus.with_stop` moves `at`, the mode of the token copy for a moment, and `started -`.

- **The guide's probe paragraph is stale** (S0015 documenter 25). `docs/operator-guide.md:1374` still says a rejected flag makes every real run end `died` "with no text that says why". Since S0015 the factory log quotes the text (`:244`). Proposed as F0048-S0018.
- **The guide's job size advice now contradicts the default** (A0001 called it "advice, not a contradiction" when the default was 8 CPUs and 32Gi). See 5. Proposed as F0048-S0018.
- **gcloud's real wording for a missing job was never checked** (S0014 coder 7 and 18, documenter 22). `is_not_found` (`operator/bin/site`) matches `Cannot find job` or `NOT_FOUND`. If the real text is different, a missing job reads `cannot be read: ...`. The line still passes, and the guide's row describes that case. One `gcloud run jobs describe <missing>` on a real project settles it. That is the human's to do, since no story may call `gcloud`. A note, no story.
- **`claude/agents/reviewer.md` checklist item 1 (`:55`) and the lesson at `:85` still state the general rule** that S0017 made an exception to (S0017 documenter). `docs/decisions.md:1366` keeps them so on purpose, "limited by this exception". A note.
- **`pyproject.toml:65` names a work item in a comment** (`# F0048-S0016 adds the instance label ...`; S0016 coder 16, reviewer and documenter). It is the human's commit `6e00f08ce`, and the four lines above it follow the same pattern (`F0014-S0003`, `F0020-S0004`, `F0046-S0002`, `F0047-S0004`), against R4's rule that code does not name work items. A note for the human.
- **Test-side duplicates the reviewers named as notes**: `gcloud_words` in `tests/site_check_support.py` beside `words` in `tests/operator_job_support.py`, with `JOB` and `IMPERSONATE` defined in both (S0014 reviewer 20). The `InstanceSettings(...)` block of `tests/entry/test_wiring_instance_label.py:22` copies `tests/entry/test_wiring_container_profile.py:31`, and `EARLIER_LINES` in `tests/test_vm_service_stop.py` copies `UNIT` (S0016 reviewer 26). `tests/adapters/test_runtime_died_text.py` imports the private `_budget_reply` and `_reply`, and two of its tests could be one table (S0015 reviewer). They are the tester's under the standing leave, with no behaviour behind them. No story.
- **`src/factory/adapters/opencode_runtime.py:480`** (`return "time_limit"` in `_end_reason`) is uncovered. It was so before S0015 (S0015 coder), and my run's coverage shows it too. A note.
- **S0016's tester entry 22 names the wrong test file for criterion 2.** The test is `tests/test_vm_service_stop.py::test_the_unit_stops_the_instances_containers_after_its_start_line` (S0016 reviewer 26). A journal slip. A note.

## 5 Documentation as a whole

I read `README.md` (line 28 points at the guide's chapter and at `operator/README.md`), `operator/README.md` (*Installing* now starts with `site init` and `site check`, and *Needs* names `SITE_TOKEN_CMD` with `gh` as the fallback), `operator/skill/kumpel/SKILL.md`'s step 1, and the guide's chapters *The site file*, *Setting up an operator's machine* and *On Cloud Run*. The site file chapter agrees with the code: the format with the new `=` rule, the usage line with `check`, and the key table with 4, 16Gi, 86400 and 30, which a test now keeps equal to the example and to `job.sh`. A0001's two stale sentences ("the first place to look ... confirmed as the stories land" and "the stories to come") are gone. Findings:

1. **The guide's *What the job needs* advises against the defaults** (`docs/operator-guide.md:1178` and `:1180`). **Size**: "Eight vCPUs and 16 GiB of memory at least", while `job.sh` and the example give 4 CPUs by default (decision 21). **The task timeout**: "Set the timeout shorter than the schedule's interval: 23 hours for a daily schedule", while the default is now 86400 seconds, the interval itself, and the passage does not say that the default must be lowered for a daily schedule. The key table (`:975-979`) and the table of `job.sh`'s keys (`:1263`) state the defaults correctly, so the guide contradicts itself. A user is not led into harm: following the advice costs CPUs, and the overlap is refused by `job.sh execute`, though not by a platform schedule. But one of the two statements is wrong. Proposed as F0048-S0018, which follows the human's defaults. If eight CPUs is the real floor, the story is to be refined the other way (see 6).
2. **The probe paragraph's "no text that says why"** (`:1374`), see 4. In F0048-S0018.

No example that no longer runs: the guide's blocks under *The `site` command* and *Creating the job* match what I ran. No section the feature needs is missing.

## 6 Decisions taken for the human

The 23 decisions of `feature.md` stand as built; I found no story that departs from one. A0001's nine additional items were answered in decision 21 or settled by S0014 and S0017. New from the journals of S0014 to S0017, for the human to accept or revisit:

1. **`site check`'s `job` line tells a missing job from an unreadable one by gcloud's error text** (`Cannot find job` or `NOT_FOUND`). A second `gcloud run jobs list` call was rejected (S0014 coder 7). The real wording is unconfirmed (see 4).
2. **The defaults are 4 CPUs and 24 hours, against the guide's advice of eight CPUs and 23 hours for a daily schedule** (decision 21 and `docs/operator-guide.md:1178-1180`). F0048-S0018 as proposed keeps the defaults and corrects the advice. Refine it the other way if the advice was right.
3. **A died run's text** (S0015 entries 4 and 9, the coder's rows). It is the error reply's text, else the last 3 non-empty lines of standard error without the login shell's `factory-login-used:` line, else `exit <status>`. Lines are stripped, blank ones dropped and the rest joined with ` / `. The text is cut to 300 characters plus `…`, so a cut text is 301 characters long. It travels on `AgentRunResult.died_text`, not in the cost record or the records contract.
4. **The instance label and the stop** (S0016 entries 4 and 9). `PodmanRuns` takes a required keyword `instance`. `--label factory.instance=<instance>` stands directly after `--rm`. `ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i` follows `RestartSec=15`, and its `-` keeps a failed stop or an empty match from failing the unit. No test starts a container; the human checks the stop on `vm`.
5. **`PLR0913` is ignored per file for `src/factory/adapters/podman_runs.py`** (the human's commit `6e00f08ce`, S0016 entry 14), with a comment that names the work item (see 4).
6. **`reviewer.md`'s checklist item 1 and its lesson keep their general wording**, limited by S0017's exception (`docs/decisions.md:1366`).
7. **Leaves given in a story's journal rather than in `feature.md`**: S0014 entry 12, S0016 entry 9 and S0017 entry 11. Each is named, so none is a finding. But *The human's changes* in `feature.md` lists only the S0014 and S0017 leaves it gave beforehand, as A0001 noted for S0012.

Earlier tests changed by S0014 to S0017, each with its leave (S0001 to S0013 as A0001 listed them):

- `tests/test_operator_site.py`: `USAGE` and the rows for a space after `=`, under the feature's leave for S0014. The test's rename to `test_a_space_beside_the_equals_sign_is_a_fault_and_one_inside_the_value_is_kept`, under the human's answer in S0014 entry 12. `INTERFACE_KEYS` moved to `tests/operator_support.py` under the standing leave.
- `tests/test_operator_job.py`: the `defaults` row and the `job_flags`/`env_list` defaults, under the feature's leave. The `overrides` row at 8/32Gi, under S0014 entry 12. Fixtures and constants moved to `tests/operator_job_support.py` under the standing leave.
- `tests/test_operator_site_check.py`: the `job`-line rows, under the feature's leave. Its machine, stand-ins and helpers moved to `tests/site_check_support.py` under the standing leave.
- `tests/operator_support.py`: `example_values` moved there under the standing leave. `url` and `route` are now computed once in `CURL_STAND_IN` (S0014 reviewer finding 3 and entry 12).
- S0015 changed no earlier test.
- `tests/adapters/test_podman_runs.py`, `test_podman_runs_fence.py`, `test_podman_runs_results.py` and `test_podman_timeout_status.py`, `tests/conftest.py`, `tests/container_extra_support.py`, `tests/test_vm_service.py` and `tests/test_vm_local_environment.py`: `instance=`, the label in the three pinned lists and the `ExecStopPost` line, under the human's leave in S0016 entry 9. `launch_words` moved to `tests/podman_support.py` from `test_podman_runs_job_profile.py` under the standing leave.
- `tests/test_claude_agent_texts_review_leave.py`: the pinned sentence, under the feature's leave for S0017. `tests/test_claude_agent_texts_review_groups.py::test_the_rest_of_the_reviewer_body_is_unchanged`, under S0017 entry 11.

No earlier test was changed without a leave named.

## 7 Slow checks

Nothing to run. The `Makefile` offers no image scan or SBOM beyond `make check`. `duplicates` is the reviewer's record (0 new, 42 known in every coder entry of S0014 to S0017), `documents` is the docs stage's check, and `mutants` falls under 3.

My `make check` was green (`test: green (83.5 s)`, total coverage 99.56 %). By its JUnit report (`.reports/junit.xml`, 8614 tests, 704.1 s summed), the slowest tests take 10.0 s each. All of them are `ROOMY_LIMIT` tests outside this feature: `tests/adapters/test_podman_timeout_status.py`, `test_process_session.py` and `test_opencode_budget.py`. The feature's slowest modules are `tests/test_operator_site_check.py` (53 tests, 11.4 s), `test_operator_merge_reset.py` (7.9 s), `test_operator_job.py` (88 tests, 6.3 s) and `test_vm_job_start.py` (6.2 s). S0014 to S0017 added little: `tests/adapters/test_runtime_died_text.py` 2.4 s, `test_operator_python_isolation.py` 1.3 s, the rest under 1 s.

Disk: at the previous record (`disk start`) all three paths had 18.0 GB free; now (`disk acceptance`) they have 15.4 GB free. The instance's own figures are unchanged: `/srv/factory/vm` uses 1.3 GB, and its state and `/tmp` 0.0 GB. So 2.6 GB of the shared pool went somewhere outside the measured datasets. At F0048-A0001 the same paths had 30.2 GB free, so 14.8 GB went in four stories and two acceptances, while the instance's use stayed at 1.3 GB. The feature's changes (scripts, tests, documents, one label and one unit line) do not explain it. A candidate I did not measure: the feature's cost records name 8 distinct stage images, and no part of the guide removes old ones. At this rate the pool is full within a few features. **Unexplained growth, for the human to look at on `vm`** (for example `podman system df` as the factory user). No story, because it lies outside this feature.

## 8 Cost

The stories cost 233 runs, 330.5 minutes, 2010 turns and $86.16 (7.24 M tokens in, 55.23 M more from cache, 1.16 M out). By story, from the `.costs.jsonl` files: S0005 $9.15 (19 runs), S0001 $8.48 (22 runs, 47.5 min), S0003 $7.92 (20), S0008 $7.12 (20, two runs `died`), S0009 $6.46, S0014 $5.88 (11), S0006 $5.71, S0007 $5.37, S0015 $5.01 (12), S0004 $4.99, S0010 $4.64, S0016 $4.09 (13), S0012 $3.75, S0002 $2.88, S0013 $1.77, S0017 $1.48 (10), S0011 $1.44. The four stories since A0001 cost $16.46 in 46 runs. None stands out. S0014 is the dearest of them because it is three stories folded into one with five parts, and its tester is the dearest role ($2.21). The three that stand out over the whole feature are still S0005, S0001 and S0003, for the reason A0001 gave: each review stopped at the first failing group, until S0011.

Human interventions: 36 questions answered (32 `question`, 1 `attempts_cap`, 3 `round_cap`), and the stories waited 5.2 h for them. Since A0001 (28 questions, 4.3 h) that is 8 more, all `question`, and about 0.9 h. The story that needed the human most is still S0001: four answers, one of them a round cap. Of the later stories, S0016 needed three answers. Intake asked how the instance reaches `PodmanRuns` and whether every start goes through `launch`. The tester needed the leave for 14 earlier calls and the pinned lists. The coder needed the human's per-file `PLR0913` ignore, and found that the smoke test's `grep` matched `.` as any character (`-F` fixed it). S0015 needed two answers: the helper's place, and how the line reaches the factory log without the runtimes knowing it.

## Proposed stories

- `F0048-S0018-the-guide-s-advice-on-the-job-and-on-the-probe-follows-the-defaults-and-the-died-line.md`: a documents-only repair of `docs/operator-guide.md`. *What the job needs* follows the job's defaults (4 vCPUs; `SITE_TIMEOUT` below the 24-hour default for a daily schedule), and the probe paragraph names the died line instead of "no text that says why". These are finding 5.1 and 5.2. `factory-check-story` says `ok`.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 1 story proposed (F0048-S0018)
   1 Scope: every scope bullet is built, and S0014 repaired A0001's findings. Finding: feature.md's Scope does not list S0013, S0015, S0016 or S0017, and its Out of scope ("nothing here changes src/factory/ except S0010") contradicts S0013, S0015 and S0016. Each of those came in with the human's decision (17, 19, 20, 23). That file is the human's to update; no story.
   2 Feature smoke test: green. One script with stand-ins for gcloud and curl only:
      - site init, then site check: 5 failed, then ready. The job line says, in turn, "does not exist yet", "cannot be read" and "exists".
      - A space after = is refused with its line number.
      - job.sh create, execute, status, log --quiet and delete each work or refuse as documented, and sanitise check says clean.
      - status.sh does not import a planted json.py. On a 500 it prints one line, exits 1 and shows no traceback.
      - The token appears in no recorded argument list.
      - I removed each of the example's 31 keys in turn and ran job.sh create --dry-run: 0 mismatches with the comments.
      - The library prints the died line, and vm/factory.service has the ExecStopPost line.
   3 Mutation testing: by sweep, not run here.
   4 Noticed:
      - The guide's probe paragraph is stale ("no text that says why"). It goes into S0018.
      - Nobody has checked gcloud's real wording for a missing job against gcloud.
      - reviewer.md's checklist item 1 and its lesson keep their general wording; this was decided on purpose.
      - pyproject.toml:65 names a work item in a comment. It is the human's commit, following the pattern of the lines above it.
      - Test-helper duplicates are left to the tester.
      - opencode_runtime.py:480 is uncovered; it was uncovered before this feature.
   5 Documentation: operator-guide.md:1178-1180 advises "Eight vCPUs ... at least" and a 23-hour timeout for a daily schedule. The defaults are now 4 CPUs and 86400 s, and the guide's own key tables state them correctly, so the guide contradicts itself. Together with the stale probe paragraph this is F0048-S0018. The rest is consistent: README, operator/README.md, SKILL.md and the site file chapter.
   6 Decisions: the 23 decisions in feature.md stand. Seven more are listed for the human:
      - the job line matches gcloud's error text;
      - the defaults against the guide's advice (S0018 follows the defaults);
      - the rules for a died run's text;
      - the instance label and ExecStopPost;
      - the PLR0913 per-file ignore;
      - the reviewer's text is unchanged except for the exception;
      - leaves were given in story journals (S0014 e12, S0016 e9, S0017 e11).
      Every earlier test that changed has its leave named.
   7 Slow checks: there is nothing beyond make check. make check is green: test 83.5 s, coverage 99.56 %, slowest tests 10 s, all ROOMY_LIMIT tests outside this feature. Disk: free space fell from 18.0 to 15.4 GB, and from 30.2 GB at A0001, while the instance stays at 1.3 GB used. The feature does not explain this. It is unexplained, for the human to check on vm (8 distinct stage images and no pruning are a candidate I did not measure).
   8 Cost: $86.16, 233 runs, 330.5 min. S0014 to S0017 cost $16.46 in 46 runs, and none of them stands out. Over the whole feature S0005, S0001 and S0003 stand out, because their reviews stopped at the first failing group until S0011. There were 36 questions (32 question, 1 attempts_cap, 3 round_cap) and 5.2 h of waiting. S0001 needed the human most (4 answers); among the later stories S0016 needed 3.
   Open: I could not remove my temporary folder /tmp/tmp.a2xnsrUGeM (smoke script and output): rm was denied.
