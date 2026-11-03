---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 521
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-03T12:02:06.004111Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-03T12:08:30.836621Z'
  stage: acceptance
  run: cf3072fab80a4fa4a54ade7870b9bfbd
- number: 3
  speaker: factory
  kind: done
  at: '2026-11-03T12:16:34.244197Z'
  stage: done
stories: [F0048-S0001, F0048-S0002, F0048-S0003, F0048-S0004, F0048-S0005, F0048-S0006, F0048-S0007, F0048-S0008, F0048-S0009, F0048-S0010, F0048-S0011, F0048-S0012, F0048-S0013, F0048-S0014, F0048-S0015, F0048-S0016, F0048-S0017, F0048-S0018, F0048-S0019, F0048-S0020]
outcome: accepted
---

# Acceptance of An operator sets up from one site file

## Recommendation

**accepted.** Every scope bullet of `feature.md` has its archived story and its code. `make check` is green, and it now leaves no `/tmp/tmp.*` folder behind. The feature's walk-through is green end to end. It runs A0003's whole walk unchanged, from `site init` to `site check: ready`, the job's whole life, the skill's scripts and the build without the layer cache. It adds S0020's three ways out of the `runc` step, each leaving nothing in `TMPDIR`, and S0019's guide, index and rename. A0003's one finding is settled by S0019. What is left is not a broken promise, so it is a story only for a noticed item. S0019's documenter asked for its new decision log entries to be checked against `feature.md`. They contradict no script, but some leave out the human's own reasons, and five of their "Rejected" options have no source. That is F0048-S0021, documents only.

## 1 Scope

All twenty scope bullets are built. A0001 to A0003 checked S0001 to S0018 in the code, and the walk below repeats it. Two stories are new since A0003:

- **S0019** (decision 25). Its part A is new: `docs/project-guide/operator.md`, with *The layout*, *The site file and its loader*, *The hosting client*, *`job.sh`*, *The sanitiser*, *The skill's scripts* and *Tests of the scripts*. The index line for it is at `docs/project-guide/README.md:21`. All ten missing support modules are now listed, and the walk finds every one of the 76 non-test modules under `tests/` named there. Eight entries are new at `docs/decisions.md:1378-1440`. I compared the guide's claims with the code: the loader's statuses 0 to 3 (`operator/lib/site.sh:4`), the job's four defaults (`operator/job/job.sh:113`, `:192-194`), the sanitiser's three built-in rules (`operator/bin/sanitise:30-33`) and the died line's 300 characters joined by ` / ` (`src/factory/adapters/agent_launch.py:31`, `:397`). All of them match. Part B: `factory-rf` is gone from every current text (the walk's `git grep` exits 1), and the two skill texts changed one line each.
- **S0020** (decision 26). `vm/job-start.sh:105-113` sets `trap 'rm -rf "$download"' EXIT` right after `mktemp -d` and clears it with `trap - EXIT` after the step's own `rm -rf`. The script sets no other trap (`grep trap`: only lines 106, 107 and 113), and its last step `exec`s `factory-run` (`:170`). So the trap cannot reach a later step. The guide's "fail it" is now "fails it" (`docs/operator-guide.md:1377`).

I found no story outside the scope and no scope bullet without a story. The Goal is reached: "copies `site.env.example`, fills in the values, runs `site check`, and is ready". The walk goes exactly that way.

## 2 Feature smoke test

A walk-through as an operator on a new machine, with an empty `HOME`. The first 145 lines are A0003's script unchanged:
- `site init`, the values filled in, and `site check`, with the `job` line's three cases;
- the job's whole life through `job.sh`;
- the log sanitised and proved clean;
- the skill's `status.sh` and `comment.sh` through `SITE_TOKEN_CMD`, `-I` against a planted `json.py`, and a failing read;
- every key of the example removed in turn against `job.sh create --dry-run`;
- the died line, the unit's stop line, and the real `vm/job-start.sh` on the tests' stand-ins for the build and the prune;
- the guide's corrected passages.

The last part is new. It runs the real `vm/job-start.sh` through the tests' own rig (`tests/vm_support.py:run_job_start`) with `TMPDIR` set to a folder of the run, three times: once with everything working, once with `curl` failing and once with `sha256sum` failing. It lists what each run left in `TMPDIR`. Then it checks S0019's index line, that every support module is listed, that `factory-rf` is gone from the current texts, and the document check. Stand-ins replace only `gcloud` and `curl` in the first part (decision 10). git is real: the checkout is a clone, and `SITE_CODE_URL` is this repository.

Command, run from the checkout's root: `sh "$w/feature-smoke.sh"`, with `w=$(mktemp -d)` and `trap 'rm -rf "$w"' EXIT`. The script:

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
echo '$ the job start script builds without the layer cache, then prunes (stand-ins, the tests'\'' rig)'
uv run -q python - "$d" <<'P'
import sys
from pathlib import Path
sys.path[:0] = ["tests", "."]
from vm_support import run_job_start
base = Path(sys.argv[1])
for name, failing in (("all well", frozenset()), ("podman fails", frozenset({"podman"}))):
    tmp = base / name.replace(" ", "-"); tmp.mkdir()
    run = run_job_start(tmp, failing=failing)
    calls = [" ".join(w for w in c.argv if not w.startswith("--runtime") and not w.startswith("--storage")) for c in run.named("podman")]
    print(name, "-> status", run.result.exit_status)
    for c in calls: print("  podman", c[:110])
    last = [l for l in (run.result.stdout + run.result.stderr).splitlines() if l][-1:]
    print("  last line:", last[0] if last else "")
P
echo '$ the guide follows the defaults and the died line'
g="$repo/docs/operator-guide.md"
printf 'Eight vCPUs: %s; no text that says why: %s\n' "$(grep -c 'Eight vCPUs' "$g")" "$(grep -c 'no text that says why' "$g")"
grep -n -o 'gets 4 vCPUs and 16 GiB[^.]*' "$g"
grep -n -o 'such as `23h`' "$g"
grep -n -o 'run <run id> of <work item> (<stage>) died: <text>' "$g" | head -3
grep -n 'podman image prune -f' "$g"
echo '$ the runc step leaves no download folder, however it ends (stand-ins, the tests'\'' rig, TMPDIR under the run)'
uv run -q python - "$d" <<'P'
import sys
from pathlib import Path
sys.path[:0] = ["tests", "."]
from vm_support import run_job_start
base = Path(sys.argv[1]) / "runc"; base.mkdir()
for name, failing in (("success", frozenset()), ("download fails", frozenset({"curl"})), ("checksum fails", frozenset({"sha256sum"}))):
    tmp = base / name.replace(" ", "-"); tmp.mkdir(); t = tmp / "tmpdir"; t.mkdir()
    run = run_job_start(tmp, {"TMPDIR": str(t)}, failing=failing)
    msgs = [l for l in run.result.stderr.splitlines() if l.startswith("job-start: runc")]
    print(f"{name} -> status {run.result.exit_status}; {msgs[0] if msgs else 'no runc message'}; left in TMPDIR: {sorted(p.name for p in t.iterdir())}")
P
echo '$ the agents'\'' documents know operator/ and the new name'
grep -n -o '^- `operator.md`: the operator'\''s scripts under `operator/` and their tests' "$repo/docs/project-guide/README.md"
n=0; for f in "$repo"/tests/*.py; do b=$(basename "$f"); case $b in test_*|__init__.py|conftest.py) continue;; esac; n=$((n+1)); grep -q "\`$b\`" "$repo/docs/project-guide/README.md" || echo "missing $b"; done; echo "$n support modules, all listed"
(cd "$repo" && git grep -c 'factory-rf' -- README.md docs/operator-guide.md docs/project-guide operator src claude vm template; echo "factory-rf in current texts: exit $?")
(cd "$repo" && uv run -q python -m factory.entry.check_documents)
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
$ the job start script builds without the layer cache, then prunes (stand-ins, the tests' rig)
all well -> status 0
  podman --cgroup-manager=cgroupfs build --layers=false --network=host -f vm/Dockerfile --build-arg FACTORY_IMAGE=v9.9.
  podman --cgroup-manager=cgroupfs image prune -f
  last line: job-start: start
podman fails -> status 1
  podman --cgroup-manager=cgroupfs build --layers=false --network=host -f vm/Dockerfile --build-arg FACTORY_IMAGE=v9.9.
  last line: job-start: image: failed
$ the guide follows the defaults and the died line
Eight vCPUs: 0; no text that says why: 0
1181:gets 4 vCPUs and 16 GiB of memory unless `SITE_CPU` and `SITE_MEMORY` say otherwise
1183:such as `23h`
244:run <run id> of <work item> (<stage>) died: <text>
1377:run <run id> of <work item> (<stage>) died: <text>
879:podman image prune -f
884:`podman image prune -f` removes the previous stage image, which the build left untagged, and the build's leftovers. It removes only untagged images that no container uses, so another instance's tagged image and a running container are safe. Without it every rebuild leaves an image behind in the factory's storage. The prune also removes the intermediate images the build's layer cache would reuse, so the next build is slower without the cache.
$ the runc step leaves no download folder, however it ends (stand-ins, the tests' rig, TMPDIR under the run)
success -> status 0; no runc message; left in TMPDIR: []
download fails -> status 1; job-start: runc: failed; left in TMPDIR: []
checksum fails -> status 1; job-start: runc: checksum does not match; left in TMPDIR: []
$ the agents' documents know operator/ and the new name
21:- `operator.md`: the operator's scripts under `operator/` and their tests
76 support modules, all listed
factory-rf in current texts: exit 1
documents ok
```

Green. The part that A0003 also walked prints what it printed then, line for line. New for S0020: the `runc` step leaves nothing in `TMPDIR` after a success, a failed download or a checksum that does not match, and the two failures print their messages as before. The failed install is a row of `tests/test_vm_job_start.py::test_the_runc_download_folder_is_removed_however_the_step_ends`, and it is green in my `make check`. I counted the `/tmp/tmp.*` folders before and after both my `make check` and the walk, leaving out the walk's own folder: 0 and 0 each time. A0003's two leftover folders, which I could not remove then, are gone from this machine. New for S0019: the index names `operator.md`, all 76 support modules are listed, `factory-rf` is gone from the current texts, and the document check says `documents ok`.

Not walked:
- S0010's ten-minute exit and S0013's pause rule need a running factory loop and a clock. Their tests cover them.
- A real container stop (S0016) and a real `podman image prune` (S0018) are the human's checks on `vm`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

A0001 to A0003 collected S0001 to S0018. New from S0019 and S0020:
- **The new decision log entries were never checked against `feature.md`.** S0019's documenter (entry 19) wrote that it read neither `feature.md` nor the journals. It took the "Why" and "Rejected" lines from the scripts and the guide, and asked for a check against decisions 1 to 9, 11, 12, 14, 19, 24 and 25. The smoke tester (entry 21) left the same point open. I made the check:
  - No entry contradicts the scripts.
  - The `job.sh` entry gives another reason for refusing an overlap than decision 7's ("a platform that cannot cancel an execution makes an overlap expensive"). It also leaves out `create` refusing an existing job, and decision 6 (the wrapper carries no logic).
  - The reset entry leaves out "the factory's own repository must never be its target" (decision 8).
  - The site file entry leaves out decision 3's "a typo or a pasted secret" and decision 11's reason and state folder.
  - The token entry leaves out the Goal's reason (`gh`'s login did not see the repository at work), decision 5's home setup and decision 14 (the real `git`, read back through `git config` and its trace).
  - Five "Rejected" options are named in no decision and in no journal I searched: "an ignored file", "a second source of defaults", "a token stored in the site file", "the code host at run time" and "a prompt on the terminal".
  
  A later agent cites the log as the human's reasons (R4), so this goes into F0048-S0021, documents only.
- **S0019's reviewer and tester:** a copied skill folder constant was found and moved under the standing leave. Fixed in the story. S0019's tester left the separate `SKILL` constant of `tests/test_operator_texts.py`, which is the path to `SKILL.md`, not a copy. None.
- **S0020's coder, reviewer and documenter:** nothing noticed beyond the story. The documenter added one sentence on the `runc` folder to the guide's list of steps (`docs/operator-guide.md:1221`); the diff bears it out.

Still standing from A0003, as notes, with no story:
- gcloud's real wording for a missing job is unconfirmed (`is_not_found` in `operator/bin/site`).
- `pyproject.toml:65` names a work item in a comment (the human's file).
- Test-side copies that S0019 left on purpose: `gcloud_words` beside `words`, and `JOB` and `IMPERSONATE` in both `tests/site_check_support.py` and `tests/operator_job_support.py`. The project guide now names both modules, so a later tester sees them.
- `src/factory/adapters/opencode_runtime.py:480` is still uncovered, as before this feature.

A0003's own note, the `/tmp` leak of `vm/job-start.sh`, is repaired by S0020 (see 2).

## 5 Documentation as a whole

I read `README.md`, `operator/README.md`, `docs/project-guide/README.md` and the new `operator.md`, the operator guide's chapters on the site file, setting up a machine, Cloud Run and the rebuild, and the new decision log entries. A0003's finding is repaired: the project guide has a domain file for `operator/` and its index lists every support module. `operator.md` agrees with the code where I checked it (see 1) and with the operator guide. It does not repeat `operator/README.md`'s table, by its own rule. No example I ran is stale. The rename is complete in the current texts. History keeps the old name, as decision 25 says (`docs/decisions.md` earlier entries, `planning/`, `docs/runs/`), and `CLAUDE.md` is the human's.

The one finding is the decision log's new entries, under 4: they are right about what the scripts do and thinner than `feature.md` about why. They mislead no user, because the operator reads the guide, which is right. The log is the agents' record of the human's reasons, so F0048-S0021 brings them in line.

A note: the guide's sentence at `docs/operator-guide.md:884` ("The prune also removes the intermediate images the build's layer cache would reuse") is still unconfirmed on `vm`. That is A0003's open item, kept under 6.

## 6 Decisions taken for the human

The 26 decisions of `feature.md` stand as built. I found no story that departs from one. A0002's seven additional items and A0003's three are unchanged, and are the human's to accept or revisit. A0003's third item is still open: whether `podman image prune` without `-a` removes the intermediate images of the layer cache on a machine. One `podman images -a` before and after a prune on `vm` settles it.

New from S0019 and S0020:
1. **The decision log's reasons and rejected options for F0048 are the documenter's reading of the code** (S0019 entry 19), not the human's words. F0048-S0021 proposes to add the reasons `feature.md` gives and to remove the five options no source names, with `Rejected: none recorded.` where nothing is left. The alternative is to keep the documenter's readings as they stand. That choice is the human's, before the story starts; the story says how to drop the removals.
2. **Only the name changed in the skill texts** (S0019 coder, entry 7): rewording the two sentences was rejected.
3. **The runc folder is removed by an EXIT trap scoped to the step** (S0020 coder, entry 7). A helper that removes the folder and then stops was rejected, because a later way out that skipped it would leave the folder again. The trap is cleared after the step. Note: in `sh` an EXIT trap does not run when a signal ends the shell, so a job cancelled during the download still leaves the folder in memory. The job ends then anyway, so this matters nowhere.

Earlier tests changed by the two stories:
- S0019: `tests/test_operator_skill_signature.py` and `tests/operator_skill_support.py`, under `CLAUDE.md`'s standing leave to move a shared test helper (tester entry 13, reviewer entry 17). `git show 1e1a5ee8c` shows only `SKILL` moved and the unused `ROOT` import dropped; every test keeps its name.
- S0020: none. Commit `336ac4310` only adds 40 lines to `tests/test_vm_job_start.py` and removes none.

Every earlier test changed in F0048 has its leave named.

## 7 Slow checks

There is nothing to run. The `Makefile` offers no image scan or SBOM beyond `make check`. `duplicates` is the reviewer's record: both new stories recorded 0 new and 42 known. `documents` is the docs stage's check, and the walk ran it green. `mutants` falls under 3.

My `make check` was green: `test: green (84.1 s)`, total coverage 99.56 %. Its JUnit report (`.reports/junit.xml`) holds 8629 tests, 710.2 s summed. The slowest take 10.0 s each, and all of them are `ROOMY_LIMIT` tests outside this feature (`tests/adapters/test_podman_timeout_status.py`, `test_opencode_budget.py`, `test_opencode_events.py`, `test_claude_runtime_resume.py`, `test_opencode_resume_session.py`). The feature's slowest modules: `tests/test_operator_site_check.py` 10.9 s, `tests/test_vm_job_start.py` 7.0 s (6.5 s at A0003; S0020's four rows add about 0.5 s) and `tests/test_operator_job.py` 6.1 s. S0019's `tests/test_operator_skill_name.py` takes under 0.1 s.

Disk: at the previous record (`disk start` of this acceptance) all three paths had 43.8 GB free, and now they have 43.7 GB. The instance's own use is unchanged: 1.3 GB for `/srv/factory/vm`, 0.0 GB for its state and for `/tmp`. The 0.1 GB less free space is not in the instance's paths; it fits one `make check` and the walk's `uv` caches on the shared disk. No growth to explain.

## 8 Cost

The stories cost 259 runs, 349.5 minutes, 2173 turns and $91.87 (7.90 M tokens in, 58.41 M more from cache, 1.22 M out). Since A0003, two stories were added:
- S0019: 10 runs, 8.2 minutes, $2.52. One review round, for the copied constant.
- S0020: 6 runs, 4.0 minutes, $1.12. No rework, the cheapest story of the feature but for S0011 and S0017.

Over the whole feature, S0005 ($9.15), S0001 ($8.48) and S0003 ($7.92) still stand out. As A0001 found, each of their reviews stopped at the first failing group until S0011.

Human interventions: 38 questions answered (34 `question`, 1 `attempts_cap`, 3 `round_cap`), and the stories waited 5.5 h for them. That is unchanged since A0003: S0019 and S0020 asked nothing, because the human wrote both with their decisions in them (decisions 25 and 26). The story that needed the human most is still S0001, with four answers, one of them a round cap. A third of all questions were leaves for earlier tests or the notes rule, which S0017 has since written down.

## Proposed stories

- `F0048-S0021-the-decision-log-gives-the-feature-s-own-reasons-for-the-operator-s-scripts.md`: documents only. It adds the reasons `feature.md` and the journals give to S0019's seven F0048 decision log entries and removes the five "Rejected" options no source names. This is the item S0019's documenter asked to be checked (see 4). `factory-check-story` says `ok`. Before it starts, the human decides whether the removals stay in it (6, item 1).

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 1 story proposed (F0048-S0021)
   1 Scope: all 20 scope bullets are built. New since A0003: S0019 adds `docs/project-guide/operator.md`, which matches the code where I checked it, the ten support modules in the index (all 76 are listed now), eight decision log entries and the rename. S0020 adds an EXIT trap for the `runc` step (`vm/job-start.sh:105-113`) and the guide's "fails it". No story outside the scope, no gap.
   2 Feature smoke test: green. A0003's walk ran again and printed the same output: `site init` to `site check: ready`, the job's whole life, the sanitiser, the skill's scripts, 31 keys with 0 mismatches, and the build without the layer cache plus the prune. New: the real `job-start.sh` on the tests' stand-ins leaves nothing in `TMPDIR` after a success, a failed download or a checksum mismatch, and keeps its messages. The index names `operator.md`, `factory-rf` is gone from the current texts, and the document check says `documents ok`. `/tmp/tmp.*`: 0 before and after both `make check` and the walk.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0019's documenter asked for its new decision log entries to be checked against `feature.md`, and the smoke tester left that open. I checked them: no contradiction with the scripts. The human's reasons for decisions 3, 5, 6, 7, 8, 11 and 14 are missing or replaced, and five "Rejected" options have no source. That is F0048-S0021. A0003's `/tmp` leak is fixed by S0020. Still standing as notes: gcloud's wording for a missing job, `pyproject.toml:65`, the test helper copies S0019 left on purpose, and `opencode_runtime.py:480` uncovered.
   5 Documentation: A0003's finding is repaired, the operator's and the agents' documents agree with the code, and the rename is complete in the current texts. Only the decision log's new entries are thinner than `feature.md` (4); they mislead no user.
   6 Decisions: the 26 decisions stand, and A0002's and A0003's items are unchanged. A0003's question is still open: does a prune without `-a` remove the cache's intermediate images on `vm`? New: whether S0021 removes the five unsourced "Rejected" options or keeps them is the human's choice. The two stories made two coder choices: only the name swapped, and the EXIT trap scoped to the step (it does not run when a signal ends the job, which matters nowhere). S0019 changed `tests/test_operator_skill_signature.py` and `tests/operator_skill_support.py` under the standing leave. S0020 changed no earlier test. Every earlier test changed in F0048 has its leave named.
   7 Slow checks: there is nothing beyond `make check`. It is green: test 84.1 s, 8629 tests, coverage 99.56 %. The slowest tests take 10 s, all ROOMY_LIMIT tests outside F0048. `test_vm_job_start.py` went from 6.5 to 7.0 s. Disk: 43.8 GB free at this acceptance's start and 43.7 GB now; the instance is unchanged at 1.3 GB, so there is no growth to explain.
   8 Cost: $91.87, 259 runs, 349.5 min. S0019 cost $2.52 in 10 runs (one review round), S0020 $1.12 in 6 runs. Over the feature, S0005, S0001 and S0003 still stand out. 38 questions (34 question, 1 attempts_cap, 3 round_cap) and 5.5 h of waiting, unchanged since A0003, because S0019 and S0020 asked nothing. S0001 still needed the human most (4 answers).
3. factory: done (pull request merged); cost: 1 runs, 6.3 min, 30 turns, 108167 tokens in (1983278 more from cache), 27973 out, $1.82
