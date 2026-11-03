---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 523
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-03T12:53:17.717261Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-03T12:57:42.768734Z'
  stage: acceptance
  run: cbbd14bcbb51424ea78752130415b5b8
stories: [F0048-S0001, F0048-S0002, F0048-S0003, F0048-S0004, F0048-S0005, F0048-S0006, F0048-S0007, F0048-S0008, F0048-S0009, F0048-S0010, F0048-S0011, F0048-S0012, F0048-S0013, F0048-S0014, F0048-S0015, F0048-S0016, F0048-S0017, F0048-S0018, F0048-S0019, F0048-S0020, F0048-S0021]
outcome: null
---

# Acceptance of An operator sets up from one site file

## Recommendation

**accepted.** Every scope bullet of `feature.md` has its archived story and its code. `make check` is green. The feature's walk-through is green end to end: it runs A0004's whole walk unchanged and then checks S0021's repaired decision log entries. A0004's one finding is settled by S0021. What is left is one noticed item, not a broken promise. The rule behind decision 27, that the decision log holds only the human's reasons, is written in no agent's text, so the next documenter can repeat S0019's slip. F0048-S0022 proposes it as one lesson for the shipped documenter.

## 1 Scope

All 21 scope bullets are built. A0001 to A0004 checked S0001 to S0020 in the code, and the walk below repeats their checks. One story is new since A0004:

- **S0021** (decision 27). The merge `fc03e8998` changes only `docs/decisions.md` (9 insertions, 9 deletions). It touches four of the seven F0048 entries S0019 wrote. I read the four against the story's docs criterion and against `feature.md`:
  - *The site file is data ...* (`docs/decisions.md:1378`): its "Why" names the typo or pasted secret and the one folder, with `~/.local/state/kumpel/`. Its "Rejected" names the one-pass collection and its delimiter. The ignored-file option carries `(the human, 2026-11-03)`, and "a second source of defaults" is replaced by the given wording.
  - *The hosting token ...* (`:1386`): its "Why" names `gh`'s login, the home setup and the real `git`. The stored-token option carries `(the human, 2026-11-03)`.
  - *`job.sh` ...* (`:1394`): its "Decision" names `create`'s refusal and the wrapper that only hands over. Its "Why" names the platform that cannot cancel. Its "Rejected" names `SITE_CODE_REF` and `python3` in `debian:trixie-slim`.
  - *A reset to a tag ...* (`:1402`): its "Why" names the factory's own repository. The prompt option carries `(the human, 2026-11-03)`.
  
  Each statement matches the code it names: `create` refuses an existing job and the job's sizes default to 4 and 16Gi (`operator/job/job.sh:192-193`).

I found no story outside the scope and no scope bullet without a story. The Goal is reached: "copies `site.env.example`, fills in the values, runs `site check`, and is ready". The walk goes exactly that way.

## 2 Feature smoke test

This is a walk-through as an operator on a new machine, with an empty `HOME`. The first 163 lines are A0004's script, unchanged. I extracted them from `done/F0048-A0004-acceptance.md`, section *2 Feature smoke test*, and they cover these steps:
- `site init`, then `site check` with the `job` line's three cases.
- The job's whole life through `job.sh`, and its log sanitised and proved clean.
- The skill's scripts through `SITE_TOKEN_CMD`, and `-I` against a planted `json.py`.
- Every key of the example removed in turn.
- The died line and the unit's stop line.
- The real `vm/job-start.sh` on the tests' stand-ins: the build, the prune and the `runc` folder.
- The guide's corrected passages and S0019's index.

Stand-ins replace only `gcloud` and `curl` (decision 10). git is real: the checkout is a clone, and `SITE_CODE_URL` is this repository. The new last part checks S0021's decision log.

Command, run from the checkout's root: `sh "$w/feature-smoke.sh"`, with `w=$(mktemp -d)` and `trap 'rm -rf "$w"' EXIT`. The script is A0004's, followed by:

```sh
echo '$ the decision log gives the feature'\''s own reasons (S0021)'
for p in 'pasted secret' 'what one machine knows' 'did not see the project' 'home setup' 'cannot cancel' 'trixie-slim' 'delimiter' "factory's own repository must never"; do printf '%s: %s\n' "$p" "$(grep -c -- "$p" "$repo/docs/decisions.md")"; done
printf 'a second source of defaults: %s\n' "$(grep -c -- 'a second source of defaults' "$repo/docs/decisions.md")"
printf '(the human, 2026-11-03) in the F0048 entries: %s\n' "$(sed -n '/^## The site file is data/,/^## The sanitiser/p' "$repo/docs/decisions.md" | grep -c -- '(the human, 2026-11-03)')"
printf 'the log says job.sh has defaults for the sizes: %s; job.sh has them: %s\n' "$(grep -c 'only the cpu, memory, timeout and idle minutes have defaults' "$repo/docs/decisions.md")" "$(grep -c 'SITE_CPU:-4\|SITE_MEMORY:-16Gi' "$repo/operator/job/job.sh")"
printf 'job.sh create refuses an existing job (log): %s\n' "$(grep -c '`create` refuses a job that exists' "$repo/docs/decisions.md")"
```

What it printed (the temporary folder is shown as `<d>`):

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
$ the decision log gives the feature's own reasons (S0021)
pasted secret: 1
what one machine knows: 1
did not see the project: 1
home setup: 1
cannot cancel: 1
trixie-slim: 1
delimiter: 1
factory's own repository must never: 1
a second source of defaults: 0
(the human, 2026-11-03) in the F0048 entries: 3
the log says job.sh has defaults for the sizes: 1; job.sh has them: 2
job.sh create refuses an existing job (log): 1
```

The walk is green. The part from A0004 prints what it printed then, line for line. The new part finds each reason S0021 added, and the "second source of defaults" that contradicted `job.sh` is gone. The log's statement on the sizes agrees with `job.sh`, which has those defaults. I sharpened two of the story's own probes: `did not see the project` counts the new sentence alone, where `did not see` already counted 1 on `main`. After my `make check` and the walk, no `/tmp/tmp.*` folder was left on the machine other than my own.

Not walked:
- S0010's ten-minute exit and S0013's pause rule need a running loop and a clock. Their tests cover them.
- A real container stop (S0016) and a real `podman image prune` (S0018) are the human's checks on `vm`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

A0001 to A0004 collected S0001 to S0020. New from S0021:
- **Intake, reviewer, documenter and smoke tester** all noticed that the story's `did not see` probe already counted 1 on `main`, so it proved little. That cannot be fixed now that the story is merged. My walk uses `did not see the project`, which counts the new sentence alone. No story.
- **The coder** (entry 7) built nothing and left criterion 2 to the documenter. **The tester** (entry 5) wrote no test. For a story of documents only, that is four stages (intake, tests, doing, review) that find nothing to do. It is cheap: S0021 cost $0.85 in all. The stages a story runs are the pipeline definition's, so this is the human's to weigh (see 8). No story.
- **The rule behind S0021 is not written where agents read it.** Decision 27 says "the decision log holds only the human's reasons". S0021 repaired the entries, but the shipped `claude/agents/documenter.md` says nothing on where a decision entry's reasons come from. Its stage forbids it to read `feature.md`, which is how S0019's documenter came to read its reasons from the code. Nothing stops the next feature's documenter from doing the same. This is F0048-S0022: one lesson in the documenter's text, pinned by a text test, the way S0017 wrote the human's notes rule into the reviewer.
- **The hosting token entry's "Why"** now also says that the tests use the real `git`, read back through `git config` (`docs/decisions.md:1390`). That is a test practice, not a reason. The criterion allowed it in "Decision" or "Why", so it is a note only.

Still standing from A0003 and A0004, as notes, with no story:
- gcloud's real wording for a missing job is unconfirmed (`is_not_found` in `operator/bin/site`).
- `pyproject.toml:65` names a work item in a comment. That file is the human's.
- Test-side copies that S0019 left on purpose: `gcloud_words` beside `words`, and `JOB` and `IMPERSONATE` in both `tests/site_check_support.py` and `tests/operator_job_support.py`.
- `src/factory/adapters/opencode_runtime.py:480` is still uncovered, as it was before this feature.

## 5 Documentation as a whole

I read the four entries S0021 changed, and the other three F0048 entries beside them, as a newcomer would. The entries now agree with `feature.md` and with each other:
- The site file entry's rejected "defaults for the site's names" and the `job.sh` entry's "only the cpu, memory, timeout and idle minutes have defaults" now say the same thing. Before S0021, "a second source of defaults" contradicted the second.
- No entry contradicts the scripts or the operator guide. The guide is unchanged since A0004, which read it whole.
- The examples I ran are current.

Three entries keep rejected options that S0021 did not touch, because A0004 had found no gap in them: the sanitiser's, the died line's and the image's. Two of them have a source in `feature.md`: "pruning with `-a`" against decision 24's tagged images, and "quoting the agent's answer" against decision 19's "the agent's own answer is never quoted". The sanitiser's "patterns kept in the repository" is decision 9's own reason. No finding.

`README.md`, `operator/README.md` and the project guide are unchanged since A0004, which read them whole. A0004's note on `docs/operator-guide.md:884` (the prune and the layer cache's intermediate images) is still unconfirmed on `vm`. It is kept under 6.

## 6 Decisions taken for the human

The 27 decisions of `feature.md` stand as built. I found no story that departs from one. A0002's seven additional items and A0003's three are unchanged, and are the human's to accept or revisit. A0003's third item is still open: whether `podman image prune` without `-a` removes the layer cache's intermediate images on a machine. One `podman images -a` before and after a prune on `vm` settles it.

A0004's item 1 was settled by decision 27: the five options are kept, reworded or folded as the human chose.

New from S0021:
1. **The real `git` in the tests went into the token entry's "Why"** (documenter, entry 11). The criterion allowed it there or in "Decision". Leave it, or move it to the "Decision" line in a later documents change.
2. **The coder did not write the decision log entries** (coder, entry 7). It rejected writing them because `CLAUDE.md` gives the log to the documenter.
3. **For F0048-S0022, if the human takes it:** where the story names no rejected option, the proposed lesson writes no "Rejected" line. A0004 had proposed `Rejected: none recorded.` instead. The choice is the human's before the story starts, and the story's Interface names the wording to change.

Earlier tests changed by S0021: none. Its merge `fc03e8998` changes only `docs/decisions.md`, besides the work item. Every earlier test changed in F0048 has its leave named (A0001 to A0004).

## 7 Slow checks

There is nothing to run. The `Makefile` offers no image scan or SBOM beyond `make check`. `duplicates` is the reviewer's record: S0021 recorded 0 new, 42 known, 0 gone. `documents` is the docs stage's check, and the walk ran it green. `mutants` falls under 3.

My `make check` was green: `test: green (83.5 s)`, with total coverage at 99.56 %. Its JUnit report (`.reports/junit.xml`) holds 8629 tests, which sum to 709.2 s. The slowest single tests take 10.0 s each, and all of them are `ROOMY_LIMIT` tests outside this feature, the slowest being `tests/adapters/test_podman_timeout_status.py::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run` and `tests/adapters/test_opencode_budget.py`. The slowest modules are `tests/adapters/test_process_session.py` (61.1 s) and `test_claude_runtime_resume.py` (52.5 s), also outside the feature. The feature's slowest modules are unchanged since A0004:
- `tests/test_operator_site_check.py`: 10.9 s
- `tests/test_vm_job_start.py`: 7.1 s
- `tests/test_operator_job.py`: 6.1 s

S0021 added no test.

Disk: at the previous record (`disk acceptance`, the start of this acceptance) all three paths had 43.7 GB free, and now they have 43.6 GB. The instance's own use is unchanged: 1.3 GB for `/srv/factory/vm`, 0.0 GB for its state and for `/tmp`. The 0.1 GB less free space is not in the instance's paths. It fits one `make check` and the walk's `uv` runs on the shared disk. No growth to explain.

## 8 Cost

The stories cost 265 runs, 353.3 minutes, 2203 turns and $92.72 (8.00 M tokens in, 58.85 M more from cache, 1.23 M out). Since A0004, one story was added:
- S0021: 6 runs, 3.8 minutes, $0.85, with no rework.

As item 4 notes, four of its six runs had nothing to do in a story of documents only. Over the whole feature, S0005 ($9.15), S0001 ($8.48) and S0003 ($7.92) still stand out. As A0001 found, each of their reviews stopped at the first failing group until S0011.

Human interventions: 38 questions answered (34 `question`, 1 `attempts_cap`, 3 `round_cap`), and the stories waited 5.5 h for them. That is unchanged since A0004: S0021 asked nothing, because the human wrote decision 27's answers into it before it started. The story that needed the human most is still S0001, with four answers, one of them a round cap. A third of all questions were leaves for earlier tests or the notes rule, which S0017 has since written down.

## Proposed stories

- `F0048-S0022-the-documenter-writes-only-the-story-s-reasons-into-the-decision-log.md`: one lesson in the shipped documenter's text, pinned by a text test. It writes decision 27's rule where the next documenter reads it, so that S0019's unsourced "Rejected" options do not come back. `factory-check-story` says `ok`. Before it starts, the human chooses between no "Rejected" line and `Rejected: none recorded.` (6, item 3).

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 1 story proposed
   1 Scope: all 21 scope bullets are built. S0021, the only story since A0004, changes only four F0048 entries of `docs/decisions.md` (merge `fc03e8998`), as its criterion asks. No story is outside the scope.
   2 Feature smoke test: green. The walk runs A0004's 163-line script unchanged, from `site init` to `site: ready`, through the job's whole life, the skill's scripts and `vm/job-start.sh` on stand-ins, then checks S0021's reasons in the log. Output is pasted in the report, and no `/tmp/tmp.*` folder is left.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0021's `did not see` probe proved little; my walk uses a sharper one. The four stages before docs had nothing to do in a story of documents only, which cost $0.85 in all. The token entry's "Why" holds a test practice, a note only. Decision 27's rule is in no agent's text, so it goes to F0048-S0022.
   5 Documentation: the F0048 log entries now agree with `feature.md`, with each other and with `job.sh`'s size defaults. The rest is unchanged since A0004. The prune note at `docs/operator-guide.md:884` is still unconfirmed on vm.
   6 Decisions: the 27 decisions stand as built. A0004's item is settled by decision 27. Three new items: the real-git sentence placed in "Why", the coder leaving the log to the documenter, and for S0022 no "Rejected" line versus `Rejected: none recorded.`. S0021 changed no earlier test.
   7 Slow checks: nothing beyond `make check`, which is green: 83.5 s, 99.56 % coverage, 8629 tests summing to 709.2 s. The slowest tests are ROOMY_LIMIT tests outside the feature. Free disk fell from 43.7 to 43.6 GB with the instance's use unchanged at 1.3 GB, so there is no growth to explain.
   8 Cost: 265 runs, 353.3 min, $92.72. S0021 cost 6 runs, 3.8 min, $0.85 with no rework. S0005, S0001 and S0003 still stand out. 38 questions were answered and the stories waited 5.5 h, unchanged since A0004; S0001 needed the human most.
