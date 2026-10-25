---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 441
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-25T09:28:36.467973Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-25T09:36:21.079108Z'
  stage: acceptance
  run: 9e2fff5f75324ed1bab253b648306f2c
stories: [F0043-S0001, F0043-S0002, F0043-S0003, F0043-S0004, F0043-S0005, F0043-S0006, F0043-S0007, F0043-S0008, F0043-S0009]
outcome: null
---

# Acceptance of The machine and the stage image

## Recommendation

**Accepted with stories.** All nine stories are built, and `make check` is green as I found it. The feature's smoke test passes. It now covers the rebuild as F0043-S0009 rewrote it: wait for no claim, stop, pull, sync, build, renew `image-id`, copy and run the operator's own `setup.sh`, start. Every command and option the section names exists in the script, the Dockerfile or the package. One finding remains, documentation of the same kind as S0009's, and no broken promise. Step 12 of *On GCP, step by step* still stops the VM with no word on a running stage. A VM stop kills a stage after 90 s, and the next start counts it as a crash. This is proposed as F0043-S0010.

## 1 Scope

Every scope item of `feature.md` has its story and its code, as the two earlier acceptances found (F0043-A0001, F0043-A0002). S0009 is the one new story. It is the proposal of F0043-A0002, which the human started, and it changes only `### The rebuild after a merge` in `docs/operator-guide.md`. Its reviewer and smoke tester found the branch diff limited to that file and the work item. So it lies inside S0004's scope item (the chapter "The machine") and touches nothing Out of scope names: no `vm/` file, no code, no test. `feature.md`'s *Stories* list still ends at S0004 and names none of S0007 to S0009. That file is the human's, so this is a note, not a finding. The goal is reached on the local VM, where the human's change 4 is recorded in the night log. The GCP path of the chapter (change 3) has still not been walked.

## 2 Feature smoke test

The walk-through an operator does: take `vm/setup.sh` from their own checkout and run that copy from a folder outside any checkout. Then have the factory read its environment file, check the unit against the layout, follow the rebuild after a merge as the guide now writes it, and see a fault stop the instance. It is one script, `smoke.sh`, run from the checkout root in a `mktemp -d` folder removed on exit. It runs against the real entry points: the script itself, its own `factory.env` heredoc and `sed` reads of `vm/Dockerfile`, `read_settings`, `vm/factory.service` through `configparser`, the guide's section, and the console script `factory-run`. It runs no podman, zfs, systemctl or gcloud, as `feature.md` requires.

```sh
cd /work/checkout && d=$(mktemp -d) && trap 'rm -rf "$d"' EXIT && mkdir "$d/s" "$d/w" && cat > "$d/s/smoke.sh" <<'SH' ... SH
sh "$d/s/smoke.sh" "$d/w"
# smoke.sh, in short:
#  1 cp vm/setup.sh to $w/home; cd there; sh -n, --help, no arguments, --runtime gpt, as non-root
#  2 base=$w/srv/factory/vm with vm/Dockerfile and an image-id; the script's claude_version..opencode_models
#    lines and its factory.env heredoc evaluated with its own variables, $(id -u factory) as $(id -u)
#  3 read_settings(factory.env, read_file)
#  4 configparser over vm/factory.service with %i=vm
#  5 the section "The rebuild after a merge": the first line of each step in order, no restart,
#    every option it passes to setup.sh in the script's usage, FACTORY_IMAGE an ARG of vm/Dockerfile,
#    its uv the script's $base/tools/bin/uv, factory-watch a console script, the crash text it cites
#  6 . factory.env with FACTORY_CHECKOUT inside the workspace; factory-run; list $FACTORY_STATE
```

Output, with the temporary path shown as `<tmp>`. The usage text after each argument fault is cut to its first line here:

```text
== 1 the operator's copy of the script, run from a folder outside any checkout
sh -n: ok
--help: exit 0
no arguments: exit 2 (setup.sh: --device is required
usage: setup.sh --device <path> --repository-url <url> [--instance <name>] ... [--sudoers] [--help]
bad runtime: exit 2 (setup.sh: --runtime is claude or opencode, not gpt
usage: setup.sh --device <path> --repository-url <url> [--instance <name>] ... [--sudoers] [--help]
as uid 1001: exit 2 (setup.sh: run as root)
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
== 3 the factory reads it as a container instance
stage_environment: container | checkout ends factory/vm/repo | state ends state | image id read: True
== 4 the unit points at the script's layout
User = factory ok
WorkingDirectory = /srv/factory/vm ok
EnvironmentFile = /srv/factory/vm/factory.env ok
ExecStart = /srv/factory/vm/factory/.venv/bin/factory-run ok
TimeoutStopSec: unset (systemd's default, 90 s)
== 5 the rebuild after a merge, as the guide writes it
steps in order (watch, stop, pull, sync, build, image-id, copy, setup, start): yes
restart lines: 0
options the section passes: --build-arg --device --ff-only --frozen --no-dev --ref --repository-url --tags --tunnel-through-iap --zone 
  --device: in setup.sh's usage
  --repository-url: in setup.sh's usage
  --ref: in setup.sh's usage
--build-arg FACTORY_IMAGE: an ARG of vm/Dockerfile
the section's uv is the script's $base/tools/bin/uv
factory-watch: a console script of the package
factory-watch prints the claim per row: False
the crash text the section points at: 1
== 6 an invalid setting stops into the state directory the file names
factory-run: exit 2
2026-10-25T09:33:32Z settings invalid: FACTORY_CHECKOUT: <tmp>/srv/factory/vm/work/repo lies inside FACTORY_WORKSPACE
factory.log
health.json
{"stops":[{"scope":"machine","reason":"preflight_failed","detail":"FACTORY_CHECKOUT: <tmp>/srv/factory/vm/work/repo lies inside FACTORY_WORKSPACE","at":"2026-10-25T09:33:32.522236Z"}]}
```

The one `False` line was a fault of my script, not of the feature. It searched `factory.entry.watch` for the claim column, but the board row is rendered in `factory.domain.board`. I reran that check against the real code:

```text
$ uv run python -I -c '... inspect.getsource(watch.run_watch) ... inspect.getsource(board._work_item_line) ...'
factory-watch writes render_board: True
each work-item row carries claim=<instance>: True
```

So the rebuild's "wait until no work item is held by `vm`" can be done with the tool it names. The smoke test is green on every promise. The real-machine half (packages, pool, delegation, image build, `factory@vm` up, a story built end to end) is the human's change 4, recorded in `docs/runs/`. The VM has since built every story up to S0009, and this acceptance runs as `vm` too.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **S0009**: the coder's "noticed but not touched" and the documenter's and smoke tester's entries all name the same thing: whether `vm/factory.service` should set a `TimeoutStopSec` beyond the lease, so that a stop lets a stage finish. It stays open for the human under 6. The reviewer had no remarks beyond the findings. The documenter's "stale text noticed": none.
- **Still open from the earlier acceptances, unchanged.** `make secrets` on `main` is still red: `detect-secrets-hook --baseline .secrets.baseline` over every tracked acceptance report exits 1 today. Claude Code 2.1.296 still runs on Debian's Node 18 in both images. The reviewers' test-hygiene notes and the v1.1 sentence at `README.md:12` ("An instance runs in the container") are left for F0044. None of these is proposed again. The earlier acceptances placed them with the human or with F0044, and nothing since has changed that.
- **New, found in check 5: step 12 stops the VM under a running stage.** It is the same gap S0009 closed for the rebuild. S0009 was told to change no other section, and so it did not.

## 5 The documentation as a whole

I read `README.md` and the chapter `## The machine` (`docs/operator-guide.md:393-737`) from the top. *The rebuild after a merge* (`:696`) now reads well. It waits for no claim, gives the reason with a pointer to the crash text (`:1873`, which exists), and introduces each of its four blocks by the machine and the user it runs on. The `gcloud` and `sudo` commands are in separate blocks, and one sentence covers a VM outside GCP. Every step's command matches the script and the Dockerfile (check 2). The contradictions the first acceptance found stay fixed.

One section still misleads, in the same way the rebuild did. **Step 12 of *On GCP, step by step*** (`:648`) reads "When the machine is not used, stop it: `gcloud compute instances stop factory-vm ...`". That is the step an operator follows every evening to save cost (*The costs*). A VM stop shuts the VM down, systemd stops `factory@vm` with the same 90-second timeout, and the next start counts a running stage as a crash (`crash_cap` 2). The guide now says exactly this in the rebuild, but step 12 neither says to wait nor points there. So two sections of one chapter disagree about whether stopping the instance under a stage is safe. The result is recoverable and loud, a `crash_cap` block at worst, so I weigh it as a story, not a refusal. It is F0043-S0010, documents only, built the way S0009 was.

A smaller thing, not a finding: the rebuild runs `uv sync` as `factory` before `setup.sh`, which runs `uv sync` again (`vm/setup.sh`, the tools step). The repeat is harmless, and the first sync keeps the pull and the build together.

## 6 Decisions taken for the human

For the human to accept or revisit:

- `feature.md` decisions 1 to 18, as the first acceptance listed them, with the same notes. Decisions 17 and 18, and decision 17's test leave, were given by Claude for the human under the order to go on unattended.
- **S0008**: option (a), the operator's own copy of `setup.sh`, was settled by starting the story, not by an answer (F0043-A0002).
- **S0009**: option (a) of F0043-A0002's open question (the operator stops between two stages, documents only) was taken by starting the story, not by an answer. No question was asked and no default was taken during its run.
- **Still open**: should a stop let the running stage finish? Option (a), stopping by hand between stages, now holds in the rebuild and, with F0043-S0010, in step 12. It leaves a short window: a claim taken in the seconds between `factory-watch` and `systemctl stop` still ends as a crash. Option (b) is a `TimeoutStopSec=` beyond the lease in `vm/factory.service`. Option (c) is the factory giving up its claim on `SIGTERM`. Both (b) and (c) would cover the VM's own shutdown and reboot too, which no guide text can. I would keep (a) for now and take (b) or (c) up before the instance runs unattended for long.
- **Still open from the earlier acceptances**: `make secrets` red on `main` (a `.secrets.baseline` update, or a rewrite of the finished reports, both yours); Node 18 under Claude Code 2.1.296; the unwalked GCP path (change 3); the agent's first step, which nothing times.

Earlier tests changed: S0009 changed none (the reviewer's "Earlier tests: none", and the diff holds no test file). For S0001 to S0008 the list is the earlier acceptances'. Every change there has its leave named. No earlier test was changed without a leave.

## 7 The slow checks

The project offers nothing beyond `make check` except `make duplicates` (a record) and `make mutants` (check 3). There is no image scan and no SBOM. `make duplicates` stayed at `11 new, 36 known, 2 gone` in S0009, which changed no code. My run of `make check` was green: `test: green (196.3 s)`, coverage 99.20 %, 7849 tests in `.reports/junit.xml`. The slowest tests lie outside this feature. They are the two rows of `test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`, 11.5 s each, then `test_process_session::test_process_the_kill_cannot_reach_does_not_hold_the_call[may-not-signal]` and `test_time_limit_of_a_make_target_ends_what_timeout_started[own-group]`, 10.1 s each. The feature's slowest test is `test_container_sync_origin::test_a_branch_deleted_on_the_host_is_gone_from_local_and_origin_refs`, at 0.1 s.

Disk, against the previous record (the second acceptance's): `/srv/factory/vm` 1.1 GB used, `state` and `/tmp` 0.0 GB used, all unchanged. Free space on the shared filesystem fell from 52.9 to 52.8 GB. That is 0.1 GB outside the measured paths over S0009's six runs, the second acceptance's run and this one (caches and `make check`), and rounding covers part of it. No growth needs explaining.

## 8 Cost

97 runs, 153.8 min, 780 turns, $32.41 for nine stories:

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

S0003 still stands out, at 53 % of the cost and 42 % of the minutes. Its journal says why: a root script writing into a folder another user owns drew one privilege-path finding per review round, each with a human answer and a new test row. S0009 went through every stage in one round, with no finding and no question. 7 of its 8.7 minutes are the tester's and the coder's runs (206 s and 214 s, of which the model took 11 s and 12 s). That is `make test` and `make check` on a documents-only story, the same pattern as S0007 and S0008.

Human interventions: 9 questions answered (7 questions and 2 round caps), and the stories waited 4.6 h for them. The figures are the same as at both earlier acceptances, because S0007 to S0009 asked nothing. S0003 needed the human most, 5 of the 9 (entries 4, 26, 37, 49 and 60). Its second round cap, from 01:42 to 05:50, is most of the 4.6 h.

## Proposed stories

- `F0043-S0010-step-12-stops-the-instance-between-two-stages-before-it-stops-the-vm.md`: step 12 of *On GCP, step by step* stops the VM with no word on a running stage, so the operator's evening stop can count a crash. The rebuild now warns against exactly that. The fix is documents only, built the way S0009 was. Whether the unit should wait for a stage instead is left to the human (6, open).

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 1 story proposed (F0043-S0010)

   1 Scope: every scope item is built. S0009, the proposal of F0043-A0002, is a documents-only change to the rebuild section, inside S0004's scope item, and touches nothing Out of scope. feature.md's Stories list does not name S0007–S0009 (the human's file). The GCP path is still unwalked (change 3).
   2 Feature smoke test: green. The operator's copy of vm/setup.sh runs from any folder and refuses bad arguments with exit 2. Its environment file is read as a container instance. The unit matches the layout. The rebuild's steps are in order (watch, stop, pull, sync, build, image-id, copy, setup, start), with no restart, and every option, ARG, path and tool it names exists. factory-watch shows claim=<instance> per row. factory-run exits 2 and writes the stop into FACTORY_STATE. One False line was my script searching the wrong module; the rerun against factory.domain.board is True.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0009's coder, documenter and smoke tester all name the open TimeoutStopSec question, and nothing else. Still open from A0001/A0002: make secrets is red on main (detect-secrets exit 1 on the acceptance reports, rechecked), Node 18, test hygiene and README:12 for F0044. New: step 12 of the GCP steps.
   5 Docs: the rebuild section is now correct and says where each block runs. Step 12 (operator-guide.md:648) stops the VM with no word on a running stage. A VM stop kills a stage after 90 s, and the next start counts it as a crash, which contradicts the rebuild's own warning. Proposed as F0043-S0010 (documents only).
   6 Decisions: feature decisions 1–18 as in A0001. Both S0008's option (a) and S0009's option (a) were settled by starting the story, not by an answer. Still open: stop by hand between stages (a, which leaves a short window between factory-watch and the stop), TimeoutStopSec beyond the lease (b), or the claim released on SIGTERM (c). Only (b) and (c) cover a reboot. Also still open: make secrets on main, Node 18, the GCP walk, the untimed first step. No earlier test was changed without a leave; S0009 changed none.
   7 Slow checks: nothing beyond make check, which is green (196.3 s, 99.20 %, 7849 tests). The slowest tests are 11.5 s time-limit tests outside the feature; the feature's slowest is 0.1 s. Disk use is unchanged (1.1 GB), and free space fell 0.1 GB (52.9 to 52.8), which the runs and caches explain.
   8 Cost: $32.41 in 97 runs and 153.8 min. S0003 is 53 % of the cost and drew 5 of the 9 human answers; its second round cap is most of the 4.6 h waited. S0009 cost $0.94 in one round with no question; 7 of its 8.7 min are make test and make check runs.
