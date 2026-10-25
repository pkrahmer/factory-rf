---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 443
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-25T09:55:06.885690Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-25T10:02:07.473927Z'
  stage: acceptance
  run: 75f76f40dd9f43ba95bc018119a01a4a
stories: [F0043-S0001, F0043-S0002, F0043-S0003, F0043-S0004, F0043-S0005, F0043-S0006, F0043-S0007, F0043-S0008, F0043-S0009, F0043-S0010]
outcome: null
---

# Acceptance of The machine and the stage image

## Recommendation

**Accepted.** All ten stories are built, and `make check` is green as I found it. The feature's smoke test passes end to end, and step 12 of *On GCP, step by step* is now covered too. `factory-watch`, run against a clone with the script's environment file, shows this acceptance's own claim (`claim=vm`), so the wait that step 12 and the rebuild ask for can be done with the tool they name. S0010 closed the one finding of the third acceptance, and nothing new of weight turned up. What stays open is the human's to decide (check 6): whether a stop should let a stage finish, `make secrets` on `main`, Node 18, and the GCP path, which nobody has walked yet. No story is proposed.

## 1 Scope

Every scope item of `feature.md` has its story and its code, as the three earlier acceptances found (F0043-A0001 to A0003). S0010 is the one new story. It is the proposal of F0043-A0003, which the human created and started. It changes only step 12 of `### On GCP, step by step` in `docs/operator-guide.md`. Its reviewer found the diff outside `factory/` empty before the docs stage. Its smoke tester found one hunk in the guide and nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/`. So it lies inside S0004's scope item (the chapter "The machine") and touches nothing Out of scope names. `feature.md`'s *Stories* list still ends at S0004 and names none of S0007 to S0010. That file is the human's, so this is a note, not a finding. The goal is reached on the local VM, where the night log records the human's change 4, and every story since S0004 was built by the instance `vm`, this acceptance included. The GCP path of the chapter (change 3) has still not been walked.

## 2 Feature smoke test

The walk-through an operator does: take `vm/setup.sh` from their own checkout and run that copy from a folder outside any checkout. Then let the factory read the environment file the script writes, check the unit against the layout, and follow the evening stop and the morning start of step 12, which S0010 rewrote. After that, check what the rebuild passes to the script, use `factory-watch` the way step 12 asks, and see an invalid setting stop the instance. It is one script, `smoke.sh`, run from the checkout root in a `mktemp -d` folder that is removed on exit. It runs against the real entry points: the script itself, its own `factory.env` heredoc and the `sed` reads of `vm/Dockerfile`, `read_settings`, `vm/factory.service` through `configparser`, the guide's sections, and the console scripts `factory-watch` and `factory-run`. It runs no podman, zfs, systemctl or gcloud, as `feature.md` requires.

```sh
cd /work/checkout && d=$(mktemp -d) && trap 'rm -rf "$d"' EXIT && mkdir "$d/s" "$d/w" && cat > "$d/s/smoke.sh" <<'SH' ... SH
sh "$d/s/smoke.sh" "$d/w"
# smoke.sh, in short:
#  1 cp vm/setup.sh to $w/home; cd there; sh -n, --help, no arguments, --runtime gpt, as non-root
#  2 base=$w/srv/factory/vm with vm/Dockerfile and an image-id; the script's claude_version..opencode_models
#    lines and its factory.env heredoc evaluated with its own variables, $(id -u factory) as $(id -u)
#  3 read_settings(factory.env, read_file)
#  4 configparser over vm/factory.service with %i=vm
#  5 step 12: the line order of factory-watch, systemctl stop, gcloud stop, gcloud start; no restart;
#    no code block mixing gcloud and sudo; the reason; step 11 runs factory-watch; the rebuild agrees; the zone
#  6 the rebuild: every option it passes to setup.sh is in the script; FACTORY_IMAGE an ARG of vm/Dockerfile
#  7 git clone of the checkout (with its origin/* refs) as FACTORY_CHECKOUT, the checkout's claude/ at
#    FACTORY_CLAUDE_HOME; . factory.env; factory-watch
#  8 . factory.env with FACTORY_CHECKOUT inside the workspace; factory-run; list $FACTORY_STATE
```

Output, with the temporary path shown as `<tmp>`. The usage text after each argument fault is cut to its first line here:

```text
== 1 the operator's copy of the script, run from a folder outside any checkout
sh -n: ok
--help: exit 0
no arguments: exit 2 (setup.sh: --device is required)
bad runtime: exit 2 (setup.sh: --runtime is claude or opencode, not gpt)
as uid 1001: exit 2 (setup.sh: run as root)
== 2 the environment file, from the script's own heredoc and the pins of vm/Dockerfile
# Written by vm/setup.sh from its arguments and vm/Dockerfile; change those and run it again.
FACTORY_INSTANCE=vm
FACTORY_REPOSITORY_URL=https://github.com/pkrahmer/factory-rf.git
FACTORY_AGENT_RUNTIME=claude
FACTORY_STAGE_ENVIRONMENT=container
FACTORY_DATASET=tank/factory/vm
FACTORY_WORKSPACE=<tmp>/srv/factory/vm/work
FACTORY_STAGE_IMAGE=factory-stage:vm
FACTORY_ZFS=zfs
FACTORY_CHECKOUT=<tmp>/srv/factory/vm/repo
FACTORY_STATE=<tmp>/srv/factory/vm/state
FACTORY_IMAGE_ID_FILE=<tmp>/srv/factory/vm/image-id
FACTORY_CLAUDE_HOME=<tmp>/srv/factory/vm/factory/claude
FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token
FACTORY_CLAUDE_LOGIN_FILE=/home/factory/.secrets/claude-token
FACTORY_API_LOGIN_FILE=/home/factory/.secrets/anthropic-api-key
FACTORY_CLAUDE_VERSION=2.1.296
FACTORY_OPENCODE_VERSION=1.19.3
FACTORY_OPENCODE_MODELS=opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5
PATH=/srv/factory/vm/tools/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
XDG_RUNTIME_DIR=/run/user/1001
== 3 the factory reads it as a container instance
stage_environment: container | checkout: <tmp>/srv/factory/vm/repo | state: <tmp>/srv/factory/vm/state | image id read: True
== 4 the unit points at the script's layout
User = factory ok
WorkingDirectory = /srv/factory/vm ok
EnvironmentFile = /srv/factory/vm/factory.env ok
ExecStart = /srv/factory/vm/factory/.venv/bin/factory-run ok
Restart = always | RestartSec = 15 | TimeoutStopSec: unset (systemd's default, 90 s)
WantedBy = multi-user.target (enabled, so it comes up with the VM)
== 5 the evening stop and the morning start: step 12 of On GCP, step by step
lines: factory-watch 1, systemctl stop 4, gcloud stop 10, gcloud start 13
order watch < stop instance < stop VM <= start VM: yes
restart lines: 0
mixed gcloud+sudo code blocks: 0
the reason (90 s, crash) is given
step 11, which step 12 points to, runs factory-watch
the rebuild stops the instance the same way
zone in step 12: factory-vm --zone=europe-west3-a
zone at create: --zone=europe-west3-a
== 6 the rebuild after a merge: every option it passes to setup.sh exists
  --device: in setup.sh
  --ref: in setup.sh
  --repository-url: in setup.sh
--build-arg FACTORY_IMAGE: an ARG of vm/Dockerfile
== 7 factory-watch, the tool step 12 waits with, on a clone that holds this acceptance's claim
factory-watch: exit 1
factory-watch: agent home unavailable: no agents directory at <tmp>/srv/factory/vm/factory/claude/agents
== 8 an invalid setting stops into the state directory the file names
factory-run: exit 2
2026-10-25T10:00:05Z settings invalid: FACTORY_CHECKOUT: <tmp>/srv/factory/vm/work/repo lies inside FACTORY_WORKSPACE
factory.log
health.json
{"stops":[{"scope":"machine","reason":"preflight_failed","detail":"FACTORY_CHECKOUT: <tmp>/srv/factory/vm/work/repo lies inside FACTORY_WORKSPACE","at":"2026-10-25T10:00:05.429078Z"}]}
```

Section 7's exit 1 was a fault of my fixture, not of the feature. On the VM the script's `checkout` step clones the whole factory into `$base/factory`, `claude/` included, but my fixture held only `vm/Dockerfile` there. `factory-watch` refused, correctly and with a clear line, because the folder `FACTORY_CLAUDE_HOME` names had no agents. I reran section 7 alone with the checkout's `claude/` copied to `$base/factory/claude` and the environment file written from the same heredoc lines (`vm/setup.sh:333-352`):

```text
unexpanded lines: 0
factory-watch: exit 0
event: idle:-  F0043-A0004 is held by vm

1:event: idle:-  F0043-A0004 is held by vm
29:F0043  The machine and the stage image  backlog=0  in-progress=0  done=10  acceptance=in_flight
31:F0043-A0004  Acceptance of The machine and the stage image  in-progress  stage=acceptance  blocked=-  claim=vm  running_since=2026-10-25T09:55:06Z  pull_request=-
rows with a claim: 1
```

That is the operator's evening check, run for real: the board names the one work item held by `vm` (this acceptance) and how long it has run. The event line says the same in words. An operator who follows step 12 would wait here, and would stop the instance once the row shows `claim=-`. The smoke test is green on every promise. The real-machine half (packages, pool, delegation, image build, `factory@vm` up, a story built end to end) is the human's change 4, recorded in `docs/runs/`, and S0010 and this acceptance ran on that instance.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **S0010**: the coder's "noticed but not touched", the documenter's "Not touched" and the smoke tester's "Open" name one thing only, the same as in S0009: `vm/factory.service` still sets no `TimeoutStopSec`. It stays open for the human under 6. The reviewer had no remarks. The documenter found *The rebuild after a merge* and steps 6 and 11 current, and named nothing stale. The documenter also made two changes beyond the criteria, both small and correct. The start command gained `factory-vm --zone=europe-west3-a`, which matches the zone at create (smoke test, section 5). The reason `systemctl stop` does not disable the service was added.
- **Still open from the earlier acceptances, unchanged.** `make secrets` on `main` is still red. I ran `detect-secrets-hook --baseline .secrets.baseline` over every finished acceptance report, and it exits 1 on the same seven hex values in `F0023-A0001`, `F0023-A0002` and `F0042-A0002`. Claude Code 2.1.296 still runs on Debian's Node 18 in both images. The reviewers' test-hygiene notes and the v1.1 sentence at `README.md:12` ("An instance runs in the container") are left for F0044. None of these is proposed again. The earlier acceptances placed them with the human or with F0044, and nothing since has changed that.
- **Mine, not a finding.** The guide has two sections with nearly the same title: `### What the container can and cannot see`, under `## The machine` (the stage container), and `### What the container cannot see`, under `## The machine's image` (Docker Desktop's disk, v1.1). The chapter above each one tells them apart, and the second goes with `image/` in F0044. F0044's documenter should check that the second leaves with it.

## 5 The documentation as a whole

I read `README.md` and the chapter `## The machine` (`docs/operator-guide.md:393-748`) from the top. Step 12 (`:648`) now agrees with *The rebuild after a merge* (`:708`). Both wait for no claim with `factory-watch`, both stop with `sudo systemctl stop factory@vm` on the VM from your own account, and both give the same reason (systemd's 90 seconds, then a crash at the next start). Step 12 points to the rebuild for that reason. Each command is introduced by where it runs, and no code block mixes `gcloud` and `sudo`. The cost sentence and the morning start stay, now with the instance and the zone. The contradiction the third acceptance found is gone. The ones the first acceptance found stay fixed. The variable table still matches the script line for line (smoke test, section 2), and so do the unit (section 4) and the rebuild's options (section 6).

Small things, none a finding. Step 12 says "run `factory-watch` as in step 11". Step 11's block begins with `sudo systemctl start factory@vm`, so an operator who copies the block whole starts an instance that is already running, which is harmless. Step 12 says "A stopped VM costs only its disks and NAT", and *The costs* (`:685`) says "its disks (the boot disk and the data disk), not the machine". The two say the same thing, since NAT is billed apart from the VM. `README.md` sends the newcomer to the chapter "The machine" in its v1.2 paragraph. Its line 12 still presents v1.1's container as the way an instance runs, which is F0044's (check 4).

## 6 Decisions taken for the human

For the human to accept or revisit:

- `feature.md` decisions 1 to 18, as the first acceptance listed them, with the same notes. Decisions 17 and 18, and decision 17's test leave, were given by Claude for the human under the order to go on unattended.
- **S0008**: option (a), the operator's own copy of `setup.sh`, was settled by starting the story, not by an answer (F0043-A0002).
- **S0009 and S0010**: option (a) of F0043-A0002's open question (the operator stops between two stages, documents only) was taken by starting each story, not by an answer. S0010 asked no question and took no default. Its documenter added the zone to the start command and the reason the service stays enabled, both beyond the criteria and both true.
- **Still open: should a stop let the running stage finish?** Option (a), stopping by hand between stages, now holds in both places the guide stops the instance: the rebuild and step 12. It leaves two gaps that no guide text closes. A claim taken in the seconds between `factory-watch` and `systemctl stop` still ends as a crash. A shutdown the operator does not start (a GCP host maintenance event, a reboot after an unattended upgrade) gets the same 90 s. Option (b) is a `TimeoutStopSec=` beyond the lease in `vm/factory.service`. Option (c) is the factory giving up its claim on `SIGTERM`. Both (b) and (c) would cover those gaps. I would keep (a) for now and take (b) or (c) up before the instance runs unattended for long. The choice is the human's, so I propose no story for it.
- **Still open from the earlier acceptances**: `make secrets` red on `main` (a `.secrets.baseline` update, or a rewrite of the finished reports, both yours), Node 18 under Claude Code 2.1.296, the unwalked GCP path (change 3), and the agent's first step, which nothing times.

Earlier tests changed: S0010 changed none (the reviewer's "Earlier tests: none", and the smoke tester's diff holds no test file). For S0001 to S0009 the list is the earlier acceptances'. Every change there has its leave named. No earlier test was changed without a leave.

## 7 The slow checks

The project offers nothing beyond `make check` except `make duplicates` (a record) and `make mutants` (check 3). There is no image scan and no SBOM. `make duplicates` stayed at `11 new, 36 known, 2 gone` in S0010, which changed no code. My run of `make check` was green: `test: green (197.0 s)`, coverage 99.20 %, 7849 tests in `.reports/junit.xml`. The slowest tests lie outside this feature. They are the two rows of `test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login` (`status-1-past-the-limit` and `sigkill-past-the-limit`), 11.5 s each, then `test_process_session::test_process_the_kill_cannot_reach_does_not_hold_the_call` (`ended-in-between` and `may-not-signal`), 10.1 s each. Of the feature's 221 tests (`test_vm_*`, `test_stage_image*`, `test_container_sync*`), the slowest is `test_container_sync_origin::test_a_branch_deleted_on_the_host_is_gone_from_local_and_origin_refs`, at 0.1 s.

Disk, against the previous record (the third acceptance's): `/srv/factory/vm` 1.1 GB used, `state` and `/tmp` 0.0 GB used, all unchanged. Free space on the shared filesystem fell from 52.8 to 52.7 GB. That is 0.1 GB outside the measured paths, over S0010's six runs, the third acceptance's closing and this run (caches and `make check`), and rounding covers part of it. No growth needs explaining.

## 8 Cost

103 runs, 159.1 min, 808 turns, $33.24 for ten stories:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 10 | 13.9 | $3.50 |
| S0002 | 11 | 14.0 | $3.68 |
| S0003 | 33 | 64.9 | $17.02 |
| S0004 | 8 | 12.8 | $1.62 |
| S0005 | 7 | 7.1 | $1.76 |
| S0006 | 10 | 18.7 | $2.19 |
| S0007 | 6 | 8.3 | $0.81 |
| S0008 | 6 | 5.5 | $0.89 |
| S0009 | 6 | 8.7 | $0.94 |
| S0010 | 6 | 5.2 | $0.83 |

S0003 still stands out, at 51 % of the cost and 41 % of the minutes. Its journal says why: a root script writing into a folder another user owns drew one privilege-path finding per review round, each with a human answer and a new test row. S0010 went through every stage in one round, with no finding and no question, at $0.83. 3.7 of its 5.2 minutes are the coder's run (220 s, of which the model took 14 s). Most of that run is the coder's own `make check`, run on a story that changes only a document. Every other run took under 30 s. It is the same pattern as S0007 to S0009.

Human interventions: 9 questions answered (7 questions and 2 round caps), and the stories waited 4.6 h for them. The figures are the same as at all three earlier acceptances, because S0007 to S0010 asked nothing. S0003 needed the human most, 5 of the 9 (its entries 4, 26, 37, 49 and 60). Its second round cap, from 01:42 to 05:50, is most of the 4.6 h.

## Proposed stories

None. S0010 closed the third acceptance's one finding. What remains is either the human's choice (a stop that lets a stage finish, `make secrets` on `main`, Node 18, the GCP walk) or F0044's (the v1.1 text and the second "What the container cannot see").

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 0 stories proposed

   1 Scope: every scope item is built. S0010 is the third acceptance's proposal. It changes only step 12 of the GCP steps, which lies inside S0004's scope item, and touches nothing Out of scope. feature.md's Stories list names none of S0007–S0010; that file is the human's, so this is a note. Nobody has walked the GCP path yet (change 3).
   2 Feature smoke test: green. The operator's copy of vm/setup.sh refuses bad arguments with exit 2. Its environment file is read as a container instance, and the unit matches the layout. Step 12 runs in order: factory-watch, the instance stop, the VM stop, the VM start. It has no restart, no block mixing gcloud and sudo, and the zone it names is the zone at create. factory-watch, run against a clone with the environment file, shows this acceptance's own claim=vm, so the wait step 12 asks for can be done. factory-run exits 2 and writes its stop into FACTORY_STATE. My first run of factory-watch exited 1 because my fixture had no claude/; the rerun with it exited 0.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0010's coder, documenter and smoke tester name only the open TimeoutStopSec question. Still open from A0001–A0003: make secrets is red on main (I reran it: exit 1, the same 7 values in F0023-A0001/A0002 and F0042-A0002), Node 18, the test-hygiene notes, and README:12 for F0044. Mine: two guide sections are titled nearly alike ("What the container can and cannot see" and the v1.1 "What the container cannot see"); the second goes with image/ in F0044.
   5 Docs: step 12 now agrees with the rebuild section on the wait, the stop, the reason and where each command runs. The third acceptance's contradiction is gone. The variable table, the unit and the rebuild's options still match the code. Remaining wording points are small, none a finding.
   6 Decisions: feature decisions 1–18 as in A0001. S0008's option (a), and option (a) for S0009 and S0010, were settled by starting the stories, not by answers. S0010 took no default. Still open: should a stop let a stage finish? The options are (a) stop by hand, which leaves the gap between watch and stop and the shutdowns the operator does not start; (b) TimeoutStopSec beyond the lease; (c) release the claim on SIGTERM. Also open: make secrets on main, Node 18, the GCP walk, and the untimed first step. No earlier test was changed without a leave; S0010 changed none.
   7 Slow checks: nothing beyond make check, which is green (197.0 s, 99.20 %, 7849 tests). The slowest tests are 11.5 s time-limit tests outside the feature; the feature's 221 tests peak at 0.1 s. Disk use is unchanged at 1.1 GB. Free space fell 0.1 GB (52.8 to 52.7), which the runs and caches explain.
   8 Cost: $33.24 in 103 runs and 159.1 min. S0003 is 51 % of the cost and drew 5 of the 9 human answers (7 questions, 2 round caps, 4.6 h waited); its second round cap is most of the wait. S0010 cost $0.83 in one round with no question; 3.7 of its 5.2 min are the coder's make check on a documents-only story.
