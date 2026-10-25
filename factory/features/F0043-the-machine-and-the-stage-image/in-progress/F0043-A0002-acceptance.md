---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 439
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-25T08:55:36.875876Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-25T09:04:49.643533Z'
  stage: acceptance
  run: 796e070984fc4d2e838f8cbfe853019f
stories: [F0043-S0001, F0043-S0002, F0043-S0003, F0043-S0004, F0043-S0005, F0043-S0006, F0043-S0007, F0043-S0008]
outcome: null
---

# Acceptance of The machine and the stage image

## Recommendation

**Accepted with stories.** All eight stories are built and `make check` is green. The feature's smoke test passes. The operator's own copy of `vm/setup.sh`, run from a folder outside any checkout, writes an environment file that the factory reads as a `container` instance. The guide's variable table matches that file line for line, the unit points at the script's layout, and a bad setting stops into the state directory the file names. The two stories that the first acceptance (F0043-A0001) proposed are merged and do what they promised. The chapter now names all three secrets everywhere, and root no longer runs a file from the factory's checkout. One finding remains, documentation of the same kind, and it is no broken promise. *The rebuild after a merge* pulls and syncs the code under a running instance and then restarts it. A restart during a stage counts that stage as a crash. The section also mixes commands for the operator's computer and for the VM in one block. It is proposed as F0043-S0009.

## 1 Scope

Every scope item of `feature.md` has its story and its code. The first acceptance's check 1 still holds: S0001 to S0004 build the four scope items, S0005 and S0006 were added during the build (decisions 17 and 18), and nothing under `image/` changed. This acceptance adds S0007 and S0008, the two stories F0043-A0001 proposed, which the human merged into the backlog and started. Both change only documents in the chapter "The machine" (`docs/operator-guide.md`, and one sentence in `docs/decisions.md`), so both are inside the scope item of S0004. Neither touches anything Out of scope names. `feature.md`'s *Stories* list still ends at S0004 and names neither S0007 nor S0008. `feature.md` is the human's, so that is a note, not a finding. The goal is reached on the local VM. The GCP path of the chapter has still not been walked (change 3), as the first acceptance said.

## 2 Feature smoke test

The walk-through an operator does: take `vm/setup.sh` from their checkout, run that copy, have its environment file read by the factory, start the unit, place the secrets the guide names, rebuild as the guide says, and see a fault stop the instance. It is one script, `smoke.sh`, run from the checkout root against the real entry points: the script itself, its own heredoc and its own `sed` reads of `vm/Dockerfile`, `read_settings`, `login_paths` of the agent runtimes, the guide's text, the unit through `configparser`, and the console script `factory-run`. It runs no podman, zfs or systemctl, as `feature.md` requires.

```sh
cd /work/checkout && d=$(mktemp -d) && trap 'rm -rf "$d"' EXIT && mkdir "$d/s" "$d/w" && cat > "$d/s/smoke.sh" <<'SH' ... SH
sh "$d/s/smoke.sh" "$d/w"
# smoke.sh, in short:
#  1 cp vm/setup.sh $d/home/setup.sh; cd there; sh -n, --help, no arguments, --runtime gpt, as non-root;
#    count the paths in it that are relative to a checkout (a copy must work from any folder)
#  2 base=$d/srv/factory/vm; vm/Dockerfile copied to $base/factory/vm; the script's factory.env heredoc
#    (from env_file= to its EOF) evaluated with the script's own variables and sed reads, $(id -u factory) as $(id -u)
#  3 read_settings(factory.env); login_paths(LoginFiles(...)) of the claude runtime; the guide's table of
#    "The service" against the file's variables; "The two passes" and GCP step 8 on the three secrets;
#    the rebuild's root commands; the three ARG pins of both Dockerfiles
#  4 configparser over vm/factory.service with %i=vm
#  5 . factory.env with FACTORY_CHECKOUT inside the workspace; factory-run; list $FACTORY_STATE
```

Output, with the temporary path shown as `<tmp>`:

```text
== 1 the operator's copy of the script, run from a folder outside any checkout
sh -n: ok
--help: exit 0
no arguments: exit 2 (setup.sh: --device is required)
bad runtime: exit 2 (setup.sh: --runtime is claude or opencode, not gpt)
as uid 1001: exit 2 (setup.sh: run as root)
relative paths in the script (a copy must not need the checkout as its folder): 0
== 2 the environment file, from the script's own heredoc and the pins of vm/Dockerfile
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
== 3 the factory reads it as a container instance; the guide says the same
stage_environment: container | checkout: <tmp>/srv/factory/vm/repo | state: <tmp>/srv/factory/vm/state | image id read: True
login files the claude runtime mounts: ['claude-token', 'anthropic-api-key'] | token file: hosting-token
variables in the file but not in the guide's table: none | in the table but not the file: none
the two passes: names ['hosting-token', 'claude-token', 'anthropic-api-key'] | 'must exist': True
rebuild, root runs: ['sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \\'] | runs a checkout file as root: False
rebuild, says to stop the service or wait for no claim before the pull: False
pin CLAUDE_CODE_VERSION: 2.1.296 in both Dockerfiles
pin OPENCODE_VERSION: 1.19.3 in both Dockerfiles
pin UV_VERSION: 0.9.2 in both Dockerfiles
== 4 the unit points at the script's layout
User = factory ok
WorkingDirectory = /srv/factory/vm ok
EnvironmentFile = /srv/factory/vm/factory.env ok
ExecStart = /srv/factory/vm/factory/.venv/bin/factory-run ok
TimeoutStopSec: unset (systemd's default, 90 s)
== 5 an invalid setting stops into the state directory the file names
2026-10-25T09:01:53Z settings invalid: FACTORY_CHECKOUT: <tmp>/srv/factory/vm/work/repo lies inside FACTORY_WORKSPACE
factory.log
health.json
{"stops":[{"scope":"machine","reason":"preflight_failed","detail":"FACTORY_CHECKOUT: <tmp>/srv/factory/vm/work/repo lies inside FACTORY_WORKSPACE","at":"2026-10-25T09:01:53.398887Z"}]}
```

Two lines of the first run were faults of my script, not of the feature, and I reran both. It looked for step 8 in the first numbered list of the chapter (*The steps*), so I reran that check scoped to *On GCP, step by step*. It also printed the exit status of the `sed` that its output went through, so I reran `factory-run` with its output going to a file:

```text
GCP step 8: names ['hosting-token', 'claude-token', 'anthropic-api-key'] | 'must exist': True | 'means no key: podman': False
factory-run: exit 2
2026-10-25T09:02:03Z settings invalid: FACTORY_INSTANCE: missing
factory.log
health.json
```

(The rerun's `env -i` left `FACTORY_INSTANCE` out, so the fault it names differs. The exit status and the stop in `FACTORY_STATE` are the point.) The smoke test is green on every promise. What S0007 and S0008 changed holds against the code. The claude runtime mounts both login files the environment file sets, so all three secret files must exist, as both passages now say. The rebuild runs only the operator's copy as root, and that copy needs no checkout as its folder. The one line that reports a gap is `rebuild, says to stop the service or wait for no claim before the pull: False`, together with the unit's unset `TimeoutStopSec` (check 5). The real-machine half (packages, pool, delegation, image build, `factory@vm` up, a story built end to end) is the human's change 4, recorded in `docs/runs/2026-10-12-overnight/night-log.md` (06:48 to 07:30). The VM has since built S0006, the first acceptance, S0007 and S0008 (08:11 to 08:55).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **S0007 and S0008 noticed nothing.** Their coders, reviewers and documenters each wrote "nothing" or "none". S0007's smoke tester saw that *The stage image* still points to *Update the pins*, now "for the shared ones" only. That is correct, because the other pins are shared. Not a finding.
- **Still open from the first acceptance, and unchanged.** `make secrets` on `main` is still red. `detect-secrets-hook --baseline .secrets.baseline` over `F0023-A0001`, `F0023-A0002` and `F0042-A0002` exits 1 today. Claude Code 2.1.296 still runs on Debian's Node 18 in both images. The reviewers' test-hygiene notes, and the stale v1.1 sentence at `README.md:12` ("An instance runs in the container"), are left for F0044. None of these is proposed again. The first acceptance placed them with the human or with F0044, and nothing since has changed that.
- **New, found in check 5: the rebuild pulls under a running instance.** I traced it in the code. `install_stop_handlers` (`src/factory/entry/run.py:63`) only sets a flag, which the loop reads between ticks. `vm/factory.service` has no `TimeoutStopSec`, so systemd kills a factory still in a stage after 90 s. At its first look the restart takes its own claim for a crash (`docs/operator-guide.md:1856`). The night log shows the human stopping with no claim held (08:12). Proposed as F0043-S0009.
- **Under opencode only `anthropic-api-key` is mounted** (`opencode_runtime.py:593`). The guide's "all three must exist whatever the runtime" is therefore stricter than the code needs for opencode. It is never wrong, so it is no finding.

## 5 The documentation as a whole

I read `README.md` and the chapter `## The machine` (`docs/operator-guide.md:393-719`) from the top, and the decision-log entry "The factory runs on the host, and the stage image carries the tools alone". The contradictions the first acceptance found are gone. *The two passes*, step 8 and decision 10 now agree on all three secrets, and step 8 gives its two facts as two sentences. *The stage image* names the seven packages and the right pytest command, which I ran: `uv run pytest tests/test_stage_image.py tests/test_image.py` gave `125 passed`. *The rebuild after a merge* runs the operator's own copy, and `docs/decisions.md:1047` says why. The variable table matches the script. The steps, exit statuses and usage lines match the script as well.

One section still misleads, *The rebuild after a merge* (`:696`), in three ways:

1. **It changes the code under a running instance.** It runs `git pull` and `uv sync` in `/srv/factory/vm/factory` while `factory@vm` runs, and then `systemctl restart factory@vm`. A restart during a stage is a kill after 90 s and a counted crash, and `crash_cap` is 2. The failure is recoverable and it is loud, so I weigh it as a story, not a refusal.
2. **One block runs on two machines.** It holds `gcloud compute scp` and `gcloud compute ssh`, which run on the operator's computer, then `sudo sh setup.sh` and `systemctl`, which run on the VM. The block before it ends on the VM with `exit`. A reader who goes on in place runs `gcloud` on the VM.
3. **It is written for GCP only.** *On any Ubuntu 24.04 VM* covers the first install "from step 6 on, without `gcloud`", but not the rebuild.

All three are in F0043-S0009. Nothing else is missing.

## 6 Decisions taken for the human

For the human to accept or revisit:

- `feature.md` decisions 1 to 18, as the first acceptance listed them, with the same notes. Decisions 17 and 18, and decision 17's test leave, were given by Claude for the human under the order to go on unattended.
- **S0007**: no question and no default. The human started it as the first acceptance proposed it.
- **S0008**: the first acceptance left open how the rebuild gets a trusted `setup.sh`. Criterion 3 settles it as option (a), a copy from the operator's own checkout of the ref, as in step 6. Intake took that as settled because the human started the story (entry 3). The reviewer then removed the Description's "or from the reviewed merge" and its "the human's to refine" (entry 9). So option (a) was decided by starting the story, not by an answer. Accept or revisit.
- **Still open, from the first acceptance**: `make secrets` red on `main` (a `.secrets.baseline` update, or a rewrite of the three finished reports, both yours); Node 18 under Claude Code 2.1.296; the unwalked GCP path (change 3); the agent's first step, which nothing times.
- **New, open**: should a stop let the running stage finish? Option (a): the operator stops between two stages, as F0043-S0009 writes it (I would choose this for now: no code change, and the human already works this way). Option (b): `vm/factory.service` gets `TimeoutStopSec=` beyond the lease (for example `65min`), so `systemctl stop` waits for the stage. That changes the unit, and a stop could then take up to an hour. Option (c): the factory itself gives up the claim on `SIGTERM`. That changes code, and the work belongs to a feature of its own.

Earlier tests changed: S0007 and S0008 changed none (each reviewer's "Earlier tests: none"). The list for S0001 to S0006 is the first acceptance's, and every change there has its leave named. No earlier test was changed without a leave.

## 7 The slow checks

The project offers nothing beyond `make check` but `make duplicates` (a record) and `make mutants` (check 3). There is no image scan and no SBOM. `make duplicates` stayed at `11 new, 36 known, 2 gone` in both new stories, and neither changed `src/factory`. My run of `make check` was green: `test: green (194.5 s)`, coverage 99.20 %, 7849 tests. The slowest tests in `.reports/junit.xml` lie outside this feature. They are the two rows of `test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`, 11.5 s each, then `test_process_session::test_process_the_kill_cannot_reach_does_not_hold_the_call[ended-in-between]` and `test_time_limit_ends_every_process_of_the_session[run_streaming-own-group]`, 10.1 s each. The feature's slowest test is `test_container_sync_origin::test_a_branch_deleted_on_the_host_is_gone_from_local_and_origin_refs`, at 0.1 s.

Disk, against the previous record (the first acceptance's): `/srv/factory/vm` 1.1 GB used, `state` and `/tmp` 0.0 GB used, all three unchanged. Free space on the shared filesystem fell from 53.0 to 52.9 GB. That is 0.1 GB outside the measured paths over the two stories' twelve runs and this one (caches and `make check`), and rounding covers part of it. No growth that needs explaining.

## 8 Cost

91 runs, 145.2 min, 749 turns, $31.47 for eight stories:

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

S0003 still stands out, at 54 % of the cost and 45 % of the minutes. Its journal says why: a root script writing into a folder another user owns drew one privilege-path finding per review round, each with a human answer and a new test row. The two new stories are the cheapest of the feature. They are documents only, and each went through every stage in one round, with no finding and no question. A test run of about 195 s is most of their minutes.

Human interventions: 9 questions answered (7 questions and 2 round caps), and the stories waited 4.6 h for them. These are the same figures as at the first acceptance: S0007 and S0008 asked nothing. S0003 needed the human most, 5 of the 9 (entries 4, 26, 37, 49 and 60). Its second round cap, from 01:42 to 05:50, is most of the 4.6 h.

## Proposed stories

- `F0043-S0009-the-rebuild-stops-the-instance-between-two-stages-and-says-where-each-command-runs.md`: *The rebuild after a merge* pulls and syncs the code under a running instance and restarts it, which counts a crash when a stage runs. Its one block mixes commands for the operator's computer and for the VM, and it covers GCP only. The fix is documents only. Whether the unit should wait for a stage instead is left to the human (6, open).

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 1 story proposed (F0043-S0009)

   1 Scope: every scope item is built. S0007 and S0008, the first acceptance's proposals, are documents-only changes inside the chapter "The machine" and touch nothing Out of scope. feature.md's Stories list does not name them (the human's file). The GCP path is still unwalked (change 3).
   2 Feature smoke test: green. The operator's copy of vm/setup.sh works from any folder (no path relative to a checkout). Its environment file is read as a container instance and matches the guide's table exactly. The claude runtime mounts both login files, so all three secrets must exist, as the guide now says everywhere. The rebuild runs no checkout file as root. The unit matches the layout. factory-run exits 2 and writes the stop into FACTORY_STATE. Gap: the rebuild never stops the service before the pull, and the unit leaves TimeoutStopSec unset.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0007 and S0008 noticed nothing. Still open from A0001: make secrets is red on main (detect-secrets exit 1 on the three reports), Node 18, test hygiene and README:12 for F0044. New: SIGTERM only sets a flag, and systemd kills after 90 s, so a restart during a stage is a counted crash.
   5 Docs: A0001's contradictions are fixed, and the pytest command S0007 added runs (125 passed). "The rebuild after a merge" pulls and syncs under a running instance and then restarts it. One block mixes commands for the operator's computer and the VM, and the section covers GCP only. All three are in F0043-S0009.
   6 Decisions: feature decisions 1–18 as in A0001. S0008's "how" (option a, the operator's copy) was settled by starting the story, not by an answer. Still open: make secrets on main, Node 18, the GCP walk, the untimed first step. New and open: stop between stages (a, my choice), TimeoutStopSec beyond the lease (b), or the claim released on SIGTERM (c). No earlier test was changed without a leave.
   7 Slow checks: nothing beyond make check, which is green (194.5 s, 99.20 %, 7849 tests). The slowest tests are 11.5 s time-limit tests outside the feature; the feature's slowest is 0.1 s. Disk use is unchanged (1.1 GB), and free space fell 0.1 GB, which the runs and caches explain.
   8 Cost: $31.47 in 91 runs. S0003 is 54 % of the cost and drew 5 of the 9 human answers, and its round cap wait is most of the 4.6 h. S0007 ($0.81) and S0008 ($0.89) each took one round with no question.
