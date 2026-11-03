---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 518
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-03T10:31:40.884578Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-03T10:38:56.595636Z'
  stage: acceptance
  run: 6ca4c5c0141b4db08d65aef598c4c6ad
stories: [F0048-S0001, F0048-S0002, F0048-S0003, F0048-S0004, F0048-S0005, F0048-S0006, F0048-S0007, F0048-S0008, F0048-S0009, F0048-S0010, F0048-S0011, F0048-S0012, F0048-S0013, F0048-S0014, F0048-S0015, F0048-S0016, F0048-S0017, F0048-S0018]
outcome: null
---

# Acceptance of An operator sets up from one site file

## Recommendation

**accepted with stories.** Every scope bullet of `feature.md` has its archived story and its code. `make check` is green. The feature's walk-through is green end to end: from `site init` to `site check: ready`, the job's whole life, the skill's scripts, and now S0018's build without the layer cache followed by the prune. The guide's advice follows the defaults and the died line. A0002's two findings are settled: S0018 repaired the guide, and the human brought `feature.md`'s *Scope* and *Out of scope* up to date. One finding of weight is left, and no promise is broken by it. The agents' documents never learned about `operator/`: the project guide has no file for it and does not list ten support modules, five of them this feature's. The decision log also holds none of the site file's lasting decisions. That is one documents-only story, F0048-S0019.

## 1 Scope

All eighteen scope bullets are built. A0001 and A0002 checked S0001 to S0017 in the code, and the walk below repeats it. S0018 is new since A0002. Its part A is in `docs/operator-guide.md`:
- **Size** (`:1181`) gives 4 vCPUs and 16 GiB unless `SITE_CPU` and `SITE_MEMORY` say otherwise, and puts memory first.
- **The task timeout** (`:1183`) says to set `SITE_TIMEOUT` below the 86400-second default for a nightly job, such as `23h`.
- The probe paragraph (`:1377`) names the died line.
- The rebuild routine (`:879`, `:884`) gains `podman image prune -f`.

Its part B is in `vm/job-start.sh:155-157`: the build passes `--layers=false`, and right after it comes `podman $JOB_PODMAN_OPTIONS image prune -f || failed image`, without `-a`.

A0002's scope finding is repaired. *Scope* now has bullets for S0013, S0015, S0016, S0017 and S0018. *Out of scope* now excepts "S0010's rule ... and the three changes the human added during the build (S0013, S0015, S0016)". I found no story outside the scope and no scope bullet without a story.

The Goal is reached: "copies `site.env.example`, fills in the values, runs `site check`, and is ready". The walk below goes exactly that way.

## 2 Feature smoke test

A walk-through as an operator on a new machine, with an empty `HOME`. The first 123 lines are A0002's script unchanged:
- `site init`, the values filled in, and `site check`;
- the job's whole life through `job.sh`;
- the log sanitised and proved clean;
- the skill's `status.sh` and `comment.sh` through `SITE_TOKEN_CMD`;
- every key of the example removed in turn against `job.sh create --dry-run`;
- the died line and the unit's stop line.

The last part is new and covers S0018. It runs the real `vm/job-start.sh` through the tests' own rig (`tests/vm_support.py:run_job_start`, with stand-ins for `podman`, `git`, `apt-get` and the rest): once with every tool working, and once with `podman` failing. Then it checks the guide's corrected passages. Stand-ins replace only `gcloud` and `curl` (decision 10). git is real: the checkout is a clone, and `SITE_CODE_URL` is this repository.

Command, run from the checkout's root: `sh "$w/feature-smoke.sh"`, with `w=$(mktemp -d)`. The script:

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
```

Green. The part that A0002 also walked prints what it printed then:
- `site check` goes from `site: 5 failed` to `site: ready`, and its `job` line tells its three cases apart.
- A space after `=` is refused with its line number.
- `create` refuses an existing job, and `execute` refuses an overlap.
- The log is sanitised and `sanitise check` says clean.
- `status.sh` does not import a planted `json.py`, and on a 500 it ends with one line and no traceback.
- The token is in no recorded argument list.
- The 31 keys match their comments.

New for S0018: the real start script calls `podman ... build --layers=false ...`, then `podman ... image prune -f`, in that order, and reaches `job-start: start`. When `podman` fails it stops at `job-start: image: failed` with status 1. The guide no longer holds "Eight vCPUs" or "no text that says why". It names the 4 vCPU and 16 GiB defaults, `23h` for a nightly job, the died line and the prune.

Not walked:
- S0010's ten-minute exit and S0013's pause rule need a running factory loop and a clock. Their tests cover them (`tests/entry/test_run_machine_stop_exit.py`, `tests/application/test_scheduler.py`).
- A real container stop (S0016) and a real `podman image prune` (S0018) are the human's checks on `vm`. Decision 24 records the prune done there (26 GB).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

A0001 collected S0001 to S0013, and A0002 collected S0014 to S0017. New from S0018:
- **A grammar slip in the probe paragraph** (S0018 documenter, entry 21): `docs/operator-guide.md:1377` says "A state directory that cannot be written fail it". It should read "fails it". It predates this feature. One word, too small for a story run of its own: for the next story that touches the guide, or the human's own commit.
- **The guide's rebuild on a machine still builds with the layer cache** (S0018 smoke-tester, entry 23). The criterion asked only for the prune there, so the guide matches the story. Whether that cache survives the prune is an open question for the human; see item 2 under 6.

Still standing from A0002, as notes:
- gcloud's real wording for a missing job is unconfirmed (`is_not_found` in `operator/bin/site`).
- `pyproject.toml:65` names a work item in a comment (the human's commit, in the pattern of the four lines above it).
- Test-side copies: `gcloud_words` beside `words`, and `JOB` and `IMPERSONATE` defined in both `tests/site_check_support.py` and `tests/operator_job_support.py`; the `InstanceSettings` block of `tests/entry/test_wiring_instance_label.py`; `EARLIER_LINES` in `tests/test_vm_service_stop.py`.
- `src/factory/adapters/opencode_runtime.py:480` is uncovered. My run shows it too, and it was uncovered before this feature.

Noticed by me, outside this feature:
- **A test run leaves folders in `/tmp`.** `vm/job-start.sh:105` (step `runc`, from F0047-S0006) makes `download=$(mktemp -d)` and never removes it. The tests' `run_job_start` sets no `TMPDIR`, so a run of the script under test leaves `/tmp/tmp.*` behind, one holding the stand-in's `runc.amd64`. My `make check` left two, `/tmp/tmp.RUSz54v61h` and `/tmp/tmp.XeDyPAg2oX`. This is against `CLAUDE.md`'s "no files outside `tmp_path`". In a real job it is a few MB of memory. I could not remove them: `rm` was denied. It is F0047's script, not in F0048's scope: for the human to place, no story here.

The test copies are part of why I propose F0048-S0019 (see 5): the support modules they copy from are named in no guide.

## 5 Documentation as a whole

`README.md`, `operator/README.md`, the operator guide's chapters *The site file*, *Setting up an operator's machine*, *On Cloud Run* and *The rebuild after a merge*, and `SKILL.md` agree with the code and with each other. S0018's corrections removed the guide's last contradiction with the defaults. No example I ran is stale: the `site` blocks and the job's recipe match the walk. The decision log's line 347 still says a rejected flag would end every run "with no text that says why", but it is a dated record of the reason for the probe in 2026-10-16, not a description of today. A0001 and A0002 read the operator's documents. Reading the agents' documents as a newcomer, I found the section the feature made necessary that nobody wrote:

1. **The project guide knows nothing of `operator/`.** None of `docs/project-guide/*.md` names a file under `operator/`, the site loader, `hosting.sh`, `job.sh` or the sanitiser. No story's docs criterion named the guide for them: S0001 to S0009 named only the operator guide and `operator/README.md`. An agent whose story touches the scripts reads the index, as `CLAUDE.md` says, and finds no domain file. The rules it would need are written only in story journals and the operator guide:
   - POSIX `sh` and `python3 -I`;
   - each read assigned before it is parsed;
   - the token never in an argument list;
   - stand-ins on the `PATH` with the real `git`;
   - `operator/README.md` belongs to the documenter.
2. **Ten support modules are missing from the guide's list of every non-test module under `tests/`.** Five are F0048's: `operator_support.py` (S0001), `operator_job_support.py` (S0007), `operator_skill_support.py` (S0012), `scripted_tick_support.py` (S0010) and `site_check_support.py` (S0014). Five are older: `command_words_support.py`, `container_extra_support.py`, `opencode_provider_support.py`, `power_support.py` and `token_support.py`. The guide says "Before writing a helper, look here: the reviewer counts a copy as a finding". A list that misses these invites the copies noted under 4.
3. **The decision log holds none of the site file's lasting decisions.** I found no entry for:
   - data never code, and outside every repository (decisions 1 to 3 and 11);
   - the token never in an argument list, from a command (4, 5 and 14);
   - `job.sh` never guessing or overlapping, and running the start script of the code it clones (6, 7 and 12);
   - the reset's three safeguards (8);
   - the site's sanitiser rules (9);
   - the died line (19);
   - the job's one image (24).
   
   The code-side decisions have entries: 10, 13, 15, 17, 20, 23 and `-I`. R4 says lasting reasons are cited from `docs/decisions.md`. Today these reasons live only in the archived `feature.md`.

All three go into one documents-only story, F0048-S0019. It changes no code and no test. Nothing here misleads a user: the operator's documents are right, and the gap is in what the next agent is told.

## 6 Decisions taken for the human

The 24 decisions of `feature.md` stand as built. I found no story that departs from one. A0002's seven additional items are unchanged, and are the human's to accept or revisit. New from S0018's journal:

1. **Intake's four choices, answered by the human** (S0018 entries 3 and 4): the prune's failure fails the step (criterion 2); "never a tagged image" is pinned as no `-a` and no `--all` (criterion 3); the diff-scope criterion was dropped because the write paths confine the coder; "Nothing else in the script changes" is a description only.
2. **The prune runs straight after the build, before the image-id line** (S0018 coder, entries 13 and 17). Putting it at the end of the step was rejected, because a failed id write would then leave the leftovers in memory.
3. **On a machine the rebuild keeps the layer cache and then prunes** (`docs/operator-guide.md:879-884`; S0018 smoke-tester's note). The guide says the prune removes the cache's intermediate images, "so the next build is slower without the cache". Nobody checked on `vm` whether `podman image prune` (without `-a`) removes intermediate images that are parents of the tagged image. If it does not, that sentence is wrong. If it does, the cache on a machine buys nothing, and `--layers=false` would be the plain choice there too. One `podman images -a` before and after a prune on `vm` settles it. No story until the human says which.

Earlier tests changed by S0018, each with its leave: `tests/test_vm_job_start.py::test_the_stage_image_is_built_on_a_tmpfs_with_the_job_options`. One line was added, `"--layers=false",` after `"build",`, under the human's leave in S0018 entry 11. `git diff` of the story's commits shows exactly that line and nothing else in the module. Like the S0014, S0016 and S0017 leaves A0002 named, this leave was given in the journal and is not in `feature.md`'s *The human's changes*. Every earlier test changed in F0048 has its leave named.

## 7 Slow checks

There is nothing to run. The `Makefile` offers no image scan or SBOM beyond `make check`. `duplicates` is the reviewer's record: S0018's coder recorded 0 new and 42 known. `documents` is the docs stage's check, and `mutants` falls under 3.

My `make check` was green: `test: green (84.8 s)`, total coverage 99.56 %. Its JUnit report (`.reports/junit.xml`) holds 8622 tests, 709.2 s summed. The slowest take 10.0 s each, and all of them are `ROOMY_LIMIT` tests outside this feature (`tests/adapters/test_podman_timeout_status.py`, `test_opencode_budget.py`, `test_opencode_resume_session.py`, `test_process_session.py`). The feature's slowest modules are unchanged: `tests/test_operator_site_check.py` 10.9 s, `tests/test_vm_job_start.py` 6.5 s, `tests/test_operator_job.py` 6.1 s. S0018's `tests/test_vm_job_start_image.py` takes under 0.1 s.

Disk: at the previous record (`disk acceptance`, F0048-A0002) all three paths had 15.4 GB free; now they have 43.9 GB. The instance's own use is unchanged: 1.3 GB for `/srv/factory/vm`, 0.0 GB for its state and for `/tmp`. Free space rose by 28.5 GB, so there is no growth to explain. The rise also explains the fall A0002 could not explain (30.2 to 15.4 GB): decision 24 records 104 stage images, 26 GB, left by rebuilds on `vm` by 2026-11-03, and they were pruned. The guide's rebuild routine now prunes after every build.

## 8 Cost

The stories cost 243 runs, 337.3 minutes, 2066 turns and $88.23 (7.48 M tokens in, 56.13 M more from cache, 1.18 M out). Since A0002 only S0018 was added: 10 runs, 6.8 minutes and $2.07, the cheapest story of the feature but for S0011 and S0017. Its doing stage ran three times: once to build, once to name the approved test change, once to check green. The reason was the earlier exact-argv test, not a fault. Over the whole feature, S0005 ($9.15), S0001 ($8.48) and S0003 ($7.92) still stand out. As A0001 found, each of their reviews stopped at the first failing group until S0011.

Human interventions: 38 questions answered (34 `question`, 1 `attempts_cap`, 3 `round_cap`), and the stories waited 5.5 h for them. S0018 added 2 questions and about 0.3 h: intake's four points on the criteria (entry 3), and the coder's conflict with the exact build argv of an earlier test (entry 10). The story that needed the human most is still S0001, with four answers, one of them a round cap. A third of the questions (S0001 entry 33, S0003 entry 30, S0005 entry 26, then S0014, S0016 and S0018 for leaves on earlier tests) were leaves or the notes rule. S0017 has since written the notes rule down. An exact-argv test of an earlier story asked for a leave again in S0018.

## Proposed stories

- `F0048-S0019-the-project-guide-and-the-decision-log-describe-the-operator-s-scripts.md`: documents only. A project guide file `operator.md` for `operator/`, the ten missing support modules in the guide's index, and decision log entries for the site file's lasting decisions (1 to 9, 11, 12 and 14), the died line (19) and the job's one image (24). This is finding 5. `factory-check-story` says `ok`. If one documenter run is too little, it splits along its two documents: the guide, and the log.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 1 story proposed (F0048-S0019)
   1 Scope: all 18 scope bullets are built. S0018 is new since A0002: the guide follows the defaults and the died line, and `vm/job-start.sh:155-157` builds with `--layers=false` and then prunes. A0002's finding on `feature.md`'s Scope and Out of scope is repaired by the human. No story outside the scope, no gap.
   2 Feature smoke test: green. A0002's walk ran again with the same output: `site init`, `site check: ready`, the job's whole life, the sanitiser, `status.sh` and `comment.sh`, the token in no argument list, 31 keys with 0 mismatches. New: the real `job-start.sh`, run on the tests' stand-ins, calls `build --layers=false` and then `image prune -f` and reaches `start`. With podman failing it stops at `image: failed` with status 1. The guide's corrected passages are present.
   3 Mutation testing: by sweep, not run here.
   4 Noticed:
      - A grammar slip in the guide at `:1377` ("fail it"); too small for a story.
      - The rebuild on a machine keeps the layer cache and then prunes (see 6).
      - Still standing from A0002: gcloud's wording for a missing job is unconfirmed, `pyproject.toml:65` names a work item, the test helper copies remain, and `opencode_runtime.py:480` is uncovered.
      - New: `vm/job-start.sh:105` (F0047) never removes its `mktemp -d` folder, so `make check` leaves `/tmp/tmp.*` folders. Two from my run remain, because `rm` was denied.
   5 Documentation: the operator's documents are consistent. Finding: the project guide has no file for `operator/` and its list misses 10 support modules, 5 of them F0048's. The decision log has no entry for the site file's decisions (1–9, 11, 12, 14), the died line (19) or the one image (24). This is F0048-S0019, documents only.
   6 Decisions: the 24 decisions stand, and A0002's 7 items are unchanged. New from S0018: intake's four answered choices, and the prune placed before the image-id line. Also new: whether `podman image prune` without `-a` removes the cache's intermediate images is unchecked on `vm`, which decides whether the guide's "next build is slower" is true. `tests/test_vm_job_start.py` was changed by one line under the leave in S0018 entry 11. Every earlier test changed in F0048 has its leave named.
   7 Slow checks: there is nothing beyond `make check`. It is green: test 84.8 s, 8622 tests, coverage 99.56 %, slowest tests 10 s, all ROOMY_LIMIT tests outside F0048. Disk: free space rose from 15.4 to 43.9 GB, with the instance unchanged at 1.3 GB. This is explained by the 26 GB of old stage images pruned on `vm` (decision 24), which also explains A0002's unexplained fall.
   8 Cost: $88.23, 243 runs, 337.3 min. S0018 cost $2.07 in 10 runs. Over the feature, S0005, S0001 and S0003 still stand out, because their reviews stopped at the first failing group until S0011. 38 questions (34 question, 1 attempts_cap, 3 round_cap) and 5.5 h of waiting; S0018 added 2 questions and 0.3 h. S0001 still needed the human most (4 answers).
