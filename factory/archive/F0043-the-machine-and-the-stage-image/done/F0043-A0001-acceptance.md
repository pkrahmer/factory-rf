---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 436
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-25T08:11:54.783527Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-25T08:21:47.201874Z'
  stage: acceptance
  run: 04e77f4f767945a9aac08bb3c345e1ae
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-25T08:23:07.275725Z'
  stage: done
stories: [F0043-S0001, F0043-S0002, F0043-S0003, F0043-S0004, F0043-S0005, F0043-S0006]
outcome: accepted
---

# Acceptance of The machine and the stage image

## Recommendation

**Accepted with stories.** All six stories are built, `make check` is green, and the feature's own smoke test passes: the environment file `vm/setup.sh` writes is read by the factory's settings as a `container` instance, the unit points at the script's layout, and an invalid setting stops into the state directory that the file names. The proof `feature.md` asks for is in the night log: the first stage on the (local) VM ran F0043-S0004 from intake to merge on `vm`, and every reset took 0.1 s against the 2 s target. Two findings are documentation, and neither is a broken promise. The chapter "The machine" contradicts itself on which secrets must exist, and its rebuild step runs `vm/setup.sh` as root from the checkout that `factory` owns, which undoes the rule S0003 built. Both are proposed as stories.

## 1 Scope

Every scope item has its story and its code. `vm/Dockerfile` and `tests/test_stage_image.py` (S0001). `FACTORY_CHECKOUT` and `FACTORY_STATE` in `factory.domain.settings`, with the stop of invalid settings going to `FACTORY_STATE` in `factory.entry.run` (S0002). `vm/setup.sh` with its thirteen steps, `vm/factory.service` as `factory@.service`, and the tests `tests/test_vm_setup*.py` and `tests/test_vm_service*.py` (S0003). The chapter `## The machine` with its eleven sections, and the decision-log entry "The factory runs on the host, and the stage image carries the tools alone" (S0004). Two stories were added during the build, each recorded in `feature.md` (decisions 17 and 18). S0005 fixed a bug that ended every first run of the script at the `checkout` step. S0006 made the sync fetch `origin/*`, without which every `container` stage ended red at `make secrets`. S0006 touches `factory.application.stage_environment`, which Out of scope gives to F0042; it is a one-line fix found by this feature's proof, and decision 18 records it, so I count it as within the feature. Nothing under `image/` changed. The goal ("a fresh Ubuntu 24.04 VM to a running `container` instance with one script and one guide chapter") is reached on a local Multipass VM (night log 06:48 to 07:30). The GCP steps of the chapter have not been walked yet; `feature.md` gives that to the human (change 3).

## 2 Feature smoke test

The script runs from the checkout root, in a temporary directory that removes itself. It drives the real entry points: `vm/setup.sh` itself, the environment file produced from the script's own heredoc and its own `sed` reads of `vm/Dockerfile`, then `read_settings`, the unit parsed with `configparser`, and the console script `factory-run`. It runs no podman, zfs or systemctl, as `feature.md` requires.

```sh
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; sh "$d/smoke.sh" "$d"
# smoke.sh, in short:
#  1 sh -n vm/setup.sh; --help; no arguments; --runtime gpt; a run as non-root
#  2 base=$d/srv/factory/vm; copy vm/ to $base/factory/vm; take setup.sh from `env_file=` to its EOF,
#    with `$(id -u factory)` as `$(id -u)`, set instance=vm pool=tank image=factory-stage:vm
#    runtime=claude zfs_command=zfs repository_url=... base checkout dockerfile, stage() { cat; },
#    drop the write guard lines, run it: that is factory.env; write a uuid to $base/image-id
#  3 read_settings(factory.env, read_file); compare the three ARG pins of vm/ and image/Dockerfile
#  4 configparser over vm/factory.service with %i=vm against the script's base and checkout
#  5 . factory.env; FACTORY_CHECKOUT=$base/work/repo .venv/bin/factory-run; list $base/state
```

Output (the temporary path shown as `<tmp>`):

```text
== 1 the script parses, and its argument faults and root check run
sh -n: ok
--help: exit 0
no arguments: exit 2 (setup.sh: --device is required)
bad runtime: exit 2 (setup.sh: --runtime is claude or opencode, not gpt)
as uid 1001: exit 2 (setup.sh: run as root)
== 2 the environment file the script writes, evaluated with its own text and pins
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
== 3 the factory reads that file as a container instance
stage_environment: container
workspace: <tmp>/srv/factory/vm/work checkout: <tmp>/srv/factory/vm/repo state: <tmp>/srv/factory/vm/state
image id read: True
FACTORY_CLAUDE_VERSION = 2.1.296
FACTORY_OPENCODE_VERSION = 1.19.3
FACTORY_OPENCODE_MODELS = opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5
pin CLAUDE_CODE_VERSION: 2.1.296 in both Dockerfiles
pin OPENCODE_VERSION: 1.19.3 in both Dockerfiles
pin UV_VERSION: 0.9.2 in both Dockerfiles
== 4 the unit points at the script's layout
User = factory ok
WorkingDirectory = /srv/factory/vm ok
EnvironmentFile = /srv/factory/vm/factory.env ok
ExecStart = /srv/factory/vm/factory/.venv/bin/factory-run ok
After = network-online.target zfs.target
setup.sh: base, checkout and the uv sync that makes .venv/bin/factory-run: ok
== 5 an invalid setting stops into the state directory the file names
2026-10-25T08:18:42Z settings invalid: FACTORY_CHECKOUT: <tmp>/srv/factory/vm/work/repo lies inside FACTORY_WORKSPACE
factory-run: exit 2
factory.log
health.json
{"stops":[{"scope":"machine","reason":"preflight_failed","detail":"FACTORY_CHECKOUT: <tmp>/srv/factory/vm/work/repo lies inside FACTORY_WORKSPACE","at":"2026-10-25T08:18:42.087109Z"}]}
2026-10-25T08:18:42Z settings invalid: FACTORY_CHECKOUT: <tmp>/srv/factory/vm/work/repo lies inside FACTORY_WORKSPACE
```

Green. The real-machine half of the walk-through (packages, pool, delegation, clone, image build, `factory@vm` up, preflight passed, a story built end to end) is the human's change 4, recorded in `docs/runs/2026-10-12-overnight/night-log.md` (06:48, 06:49, 07:30).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **`make secrets` on `main` is red.** S0004's coder, reviewer and documenter, S0006's description and decision 18 all noticed it. A full scan flags "Hex High Entropy String" seven times in three finished acceptance reports (`F0023-A0001` line 84, `F0023-A0002` line 99 four times, `F0042-A0002` lines 62 and 68). I confirmed it with `detect-secrets-hook --baseline .secrets.baseline` on the three files: exit 1. The repair lies under `done/` or in `.secrets.baseline`, both the human's, so no story is proposed (see 6).
- **Claude Code 2.1.296 asks for Node >= 22**, and both images carry Debian's Node 18.20.4. npm warns at build (night log 06:48). Nothing has failed so far. The change cannot be made in `vm/Dockerfile` alone: `tests/test_stage_image.py` holds both Dockerfiles to the same Debian versions (see 6).
- **"The two passes" contradicts step 8 on the secrets** (found in check 5): proposed as F0043-S0007.
- **The *Update the pins* list names `sudo`, which `vm/Dockerfile` does not have** (S0001's documenter, entry 19): folded into F0043-S0007.
- **Test hygiene, from the reviewers' notes, not proposed.** `tests/vm_support.py:5` imports the private `_uncommented`. The `chown-keeps-links` row of `tests/test_vm_setup_text.py` checks no line, because the script has no `chown`; it still guards a future one. `test_the_folders_step_refuses_a_link_at_state_or_repo` also covers `.secrets` without saying so in its name. Two side checks take unused arguments (`:539`, `:544`). `main_commit` in `tests/application/test_container_sync_origin.py:396` overlaps the fixture of `test_container_environment.py:43`. S0001's criteria 4 and 6 are spread over several functions. All of these are cosmetic. They change earlier tests and so need a leave, and F0044 rewrites `tests/dockerfile_support.py` when it removes `image/`, which is the better time.
- **Script idempotence assumptions** (S0003's coder, entries 10 and 14). `zfs get quota` may print `30720M` for `30G`, and `zfs allow`'s format is assumed. Either would only repeat a harmless set and report it as changed. The real double run on the VM found every step done (night log 06:48), so I see no finding.
- **Stale v1.1 text for F0044**: `README.md` line 12 ("An instance runs in the container"), and the *Configuration* rows "the image sets it to ..." for the login, token and image-id files (S0003 and S0004 documenters). F0044's work.
- **The VM ran a hand-patched checkout ahead of a merge** (night log 07:11, the S0006 refspec). After S0006's merge the VM's checkout is to drop the patch and pull; whether that has been done is not recorded.

## 5 The documentation as a whole

`README.md` reads correctly for a newcomer, apart from line 12, which still presents v1.1's container as *the* way, two paragraphs before the `container`/`vm/setup.sh` sentence. That is F0044's, as above. The chapter `## The machine` is complete (eleven sections in order) and matches the code on the layout, the options, the steps, the environment file (all twenty lines checked against `vm/setup.sh:331-353`), the unit and the log line. It has three faults:

1. *The script*, "The two passes" (`docs/operator-guide.md:493`), says to place "the token, and the login file for your runtime (`claude-token` or `anthropic-api-key`)". Step 8 (`:618`) and decision 10 say all three files must exist. The code agrees with step 8: the environment file sets all three paths, `login_paths` (`src/factory/adapters/agent_launch.py:139`) mounts every one that is set, and podman refuses a missing file. A reader who follows "The two passes" gets agent runs that stop at the mount. The GCP steps and *On any Ubuntu 24.04 VM* both say "the three secrets", so the main path is right, and the failure is loud. I therefore weigh it as a story, not a refusal. Step 8's own sentence also joins two facts with a wrong "because" ("An empty `anthropic-api-key` means no key: podman refuses to mount a missing file"). Both are in F0043-S0007.
2. *The stage image* (`:444`) sends the operator to *Update the pins*, whose list names eight packages including `sudo`; the stage image has seven. This is in F0043-S0007.
3. *The rebuild after a merge* (`:712`) runs `sudo sh /srv/factory/vm/factory/vm/setup.sh`, a script in the checkout that `factory` owns and can write, as root. S0003 spent three of the human's answers (entries 26, 37, 49, then 60) making sure root acts on nothing that `factory` can change unseen. The same chapter's step 6 already copies the script from the operator's own checkout. Proposed as F0043-S0008.

No example I ran is broken: the `setup.sh` usage, exit statuses and step lines in the chapter match the script, and `make documents` is part of every docs stage's gate.

## 6 Decisions taken for the human

For the human to accept or revisit:

- `feature.md` decisions 1 to 18, as written there. Notable among them: 1 (the checkout and state directory as settings, option A), 3 (the template unit), 4 (two passes, askpass), 6 (the image-id file the operator renews), 7 (the `sudoers` fallback with `diff -FH`), 8 (`uv` from `pip` in its own venv), 10 (all three secrets must exist).
- Decision 17, S0005, was **added by Claude for the human under the order to go on unattended**. Its leave to change `tests/test_vm_setup_text.py` (`_writes` and `_as_factory` also count a call of the write helper) was likewise given by Claude, not the human, on #433 (night log 06:27 and 06:30).
- Decision 18, S0006, was also **added without the human** (night log 07:00). The VM ran its one-line change by hand ahead of the merge (07:11).
- S0002, the intake's three added rows (entry 4, the human).
- S0003, the human's answers: the option defaults and the environment file values in the script's variable form (entry 4). Every write under `$base` as `factory`, and `chown -h` (entry 26). Install the unit and helper only in the run that cloned, and refuse a link at `state` and `repo` (entry 37). Refuse a link at `/home/factory/.secrets` (entry 49). Also install when the target is missing (entry 60).
- S0004: the red `make secrets` traced to the missing `origin/main` and fixed by S0006 (entry 8). The rebuild says to remove a differing installed unit or helper and rerun the script (entry 15).
- **Open, for the human:**
  - How the rebuild gets a trusted `vm/setup.sh`: (a) copied from the operator's own checkout, as in step 6 (I would choose this; it is F0043-S0008); (b) read with `git -C /srv/factory/vm/factory diff` and then run from there, a check by eye; (c) leave the rebuild as it is and accept that root runs `factory`'s checkout.
  - `make secrets` red on `main`: a `.secrets.baseline` update for the seven values, or a rewrite of the three finished reports. Both are yours (R14, "Not without asking").
  - Node 18 under Claude Code 2.1.296: keep it, since it has run so far, or move both images to a Node >= 22 source. The latter changes a pin S0001's test holds equal across both Dockerfiles, and it is a new package source.
  - The GCP path of the chapter is unwalked (change 3). The proof ran on a local Multipass VM.
  - The plan's "start of a stage to the agent's first step" is given in the log as reset + sync + advance (0.4 s). The agent's first step itself is not timed.

Earlier tests changed, each with its leave:

- S0001: `tests/test_image.py`, `tests/test_image_credentials.py` and `tests/dockerfile_support.py`, under the standing leave (helper moves).
- S0002: `tests/domain/test_settings.py`, under the human's leave in decision 15 (a renamed test, one entry removed). `tests/entry/test_run.py` and `tests/conftest.py`, under the standing leave.
- S0005: `tests/test_vm_setup_text.py`, under decision 17's leave (given by Claude for the human). `tests/vm_support.py`, under the standing leave.
- S0006: `tests/application/test_container_environment.py`, `tests/conftest.py` and `tests/container_support.py`, under the standing leave.
- S0003 and S0004 changed none.

No earlier test was changed without a leave named.

## 7 The slow checks

The project offers nothing beyond `make check` but `make duplicates` (a record) and `make mutants` (check 3). There is no image scan and no SBOM. `make duplicates` stayed at `11 new, 36 known, 2 gone` through every story; the reviewers place the 11 new findings outside the feature's diffs. Disk: the acceptance record (`/srv/factory/vm` 53.0 GB free, 1.1 GB used; state and `/tmp` 0.0 GB used) is identical to the start record. No growth.

`make check` here: `test: green (194.4 s)`, coverage 99.20 %, 7849 tests. The slowest tests are time-limit tests outside this feature: `test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login` (two rows, 11.5 s each), `test_process_session::test_process_the_kill_cannot_reach_does_not_hold_the_call[may-not-signal]` and `test_claude_runtime_confinement::test_the_temporary_folder_is_empty_at_each_call_and_gone_after_the_run[time-limit]` (10.1 s each). The feature's own tests are fast; the slowest, `test_container_sync_origin::test_a_branch_deleted_on_the_host_is_gone_from_local_and_origin_refs`, takes 0.09 s.

## 8 Cost

79 runs, 131.4 min, 687 turns, $29.77 for six stories:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 10 | 13.9 | $3.50 |
| S0002 | 11 | 14.0 | $3.68 |
| S0003 | 33 | 64.9 | $17.02 |
| S0004 | 8 | 12.8 | $1.62 |
| S0005 | 7 | 7.1 | $1.76 |
| S0006 | 10 | 18.7 | $2.19 |

S0003 stands out: 57 % of the cost and half of the minutes. Its journal says why. A root script that writes into a folder owned by another user drew one real privilege-path finding per review round: the `image-id` write through a link, the installs from a factory-writable checkout, `install -d` on a planted link at `state`/`repo` and then at `.secrets`, and a first run interrupted after the clone. Each finding led to a human answer and a new test row.

Human interventions: 9 questions answered (7 questions, 2 round caps), 4.6 h waited. S0003 needed the human most: 5 of the 9 (the intake question in entry 4, round caps in entries 26 and 49, and reviewer questions in entries 37 and 60). Its second round cap at 01:42 waited until 05:50, most of the 4.6 h. The other four were S0002 (1, intake), S0004 (2, the missing `origin/main` and the rebuild wording) and S0005 (1, the test leave, answered by Claude for the human).

## Proposed stories

- `F0043-S0007-the-chapter-the-machine-names-all-three-secrets.md`: "The two passes" tells the operator to place only the runtime's login file, against step 8, decision 10 and the code. It also corrects step 8's wrong "because" and the stage image's pin list, which names `sudo`.
- `F0043-S0008-the-rebuild-runs-the-operator-s-copy-of-the-setup-script.md`: the rebuild runs `vm/setup.sh` as root from the checkout `factory` owns, which undoes the rule S0003 built. Its "how" is for the human to refine (6, open).

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 2 stories proposed (F0043-S0007, F0043-S0008)

   1 Scope: all scope items are built (S0001–S0004). S0005 (the setup script's stdin write bug) and S0006 (the sync fetches origin/*) were added during the build and recorded as decisions 17 and 18. S0006 touches F0042's sync by one line; I count it as within the feature. The goal is reached on a local VM; the GCP path is unwalked (the human's change 3).
   2 Feature smoke test: green. The environment file built from vm/setup.sh's own text and the vm/Dockerfile pins is read by read_settings as a container instance (checkout and state outside the workspace, image id read). The unit's ExecStart, EnvironmentFile and WorkingDirectory match the script's layout. factory-run with a bad setting exits 2 and writes the stop into FACTORY_STATE. The script's argument faults and root check exit 2. The night log records the first stage on the VM: reset 0.1 s, sync 0.3 s.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: (a) make secrets on main is red, with 7 hex values in the finished reports F0023-A0001/A0002 and F0042-A0002; I confirmed it with detect-secrets; the fix is the human's. (b) Claude Code 2.1.296 asks for Node >= 22; both images carry Node 18. (c) The reviewers' test-hygiene notes are left for F0044. (d) Stale v1.1 text in the README and the Configuration rows is F0044's.
   5 Docs: "The two passes" says to place only the runtime's login file, against step 8, decision 10 and the code, which mounts every set login file. Step 8 joins two facts with a wrong "because". The stage image section points to a pin list that names sudo. The rebuild step runs vm/setup.sh as root from the checkout factory owns, which undoes S0003's rule.
   6 Decisions: feature decisions 1–18. S0005, S0006 and decision 17's test leave were given by Claude for the human. The human's answers in S0002, S0003 (entries 4, 26, 37, 49, 60) and S0004 (entries 8, 15) are listed in the report. Open for the human: how the rebuild gets a trusted setup.sh, the red make secrets on main, Node 18, the unwalked GCP path, and the agent's first step, which nothing times. Every changed earlier test has a leave named.
   7 Slow checks: nothing beyond make check. make check is green (194.4 s, 99.20 %, 7849 tests); the slowest tests are 11.5 s time-limit tests outside this feature. Disk is unchanged against the start record.
   8 Cost: $29.77 in 79 runs. S0003 took $17.02 and 33 runs, one privilege-path finding per round, and needed 5 of the 9 human answers. Its second round cap waited from 01:42 to 05:50, most of the 4.6 h.
3. factory: done (pull request merged); cost: 1 runs, 9.8 min, 40 turns, 138821 tokens in (3028084 more from cache), 29280 out, $2.30
