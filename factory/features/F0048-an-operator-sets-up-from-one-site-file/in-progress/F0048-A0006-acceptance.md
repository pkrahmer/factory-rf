---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 525
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-03T13:39:40.184371Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-11-03T13:42:24.984463Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-11-03T13:42:26.586276Z'
  stage: acceptance
- number: 4
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-03T13:46:46.566115Z'
  stage: acceptance
  run: 1b6b6a35703f4ecda795946bfda762d7
stories: [F0048-S0001, F0048-S0002, F0048-S0003, F0048-S0004, F0048-S0005, F0048-S0006, F0048-S0007, F0048-S0008, F0048-S0009, F0048-S0010, F0048-S0011, F0048-S0012, F0048-S0013, F0048-S0014, F0048-S0015, F0048-S0016, F0048-S0017, F0048-S0018, F0048-S0019, F0048-S0020, F0048-S0021, F0048-S0022]
outcome: null
---

# Acceptance of An operator sets up from one site file

## Recommendation

**accepted.** All 21 scope bullets of `feature.md` are built, `make check` is green, and the feature's walk-through is green end to end. It runs A0005's whole walk unchanged and then checks S0022's documenter lesson. S0022, the one story since A0005, does what A0005 proposed it for: decision 27's rule is now written where the next documenter reads it. What is left is bookkeeping for the human, not a broken promise. `feature.md` names S0022 in neither its Scope nor its Stories. A0005's proposal did not foresee the earlier test that pins the documenter's lessons, which cost one question. I propose no story.

## 1 Scope

The 21 scope bullets are built. A0001 to A0005 checked S0001 to S0021 in the code, and the walk below repeats their checks. One story is new since A0005:

- **S0022**, proposed by A0005 for decision 27. The merge `3fed3bd31` changes these files:
  - `claude/agents/documenter.md`: one bullet in `## Lessons`, line 75.
  - `docs/decisions.md`: one new entry, "The decision log holds only the human's reasons".
  - `docs/project-guide/agents.md`: the `## Lessons` paragraph, line 260.
  - `tests/test_claude_agent_texts_decision_log.py`: new.
  - `tests/test_claude_agent_texts.py`: one entry added to `LESSONS["documenter"]`, under the human's leave.

  The bullet matches the story's Interface word for word, and it stands between the project guide's bullet and the temporary-directory bullet. No other shipped agent carries it. No module under `src/factory/` changed, which is what Out of scope asks.

There is one gap in bookkeeping only. `feature.md` lists S0022 in neither its Scope nor its Stories. Decision 27 names S0021 alone. The story is within decision 27's purpose, so it is not a story outside the scope in substance. `feature.md` is the human's file (R14), so this goes under 6, and no story is proposed for it.

The Goal is reached. The walk starts from `site.env.example` with `site init`, fills in the values and gets `site: ready`. From there it drives the job and the skill's scripts.

## 2 Feature smoke test

This is a walk-through as an operator on a new machine, with an empty `HOME`.
- **A0004's script (163 lines, unchanged).** I extracted it from `done/F0048-A0004-acceptance.md`, section *2 Feature smoke test*, lines 17 to 179. It covers:
  - `site init` and `site check`, including the `job` line's three cases.
  - The job's whole life through `job.sh`, and the log sanitised and proved clean.
  - The skill's scripts through `SITE_TOKEN_CMD`, with `-I` tested against a planted `json.py`.
  - Every key of the example removed in turn.
  - The died line and the unit's stop line.
  - The real `vm/job-start.sh` on the tests' stand-ins.
  - The guide's passages and S0019's index.
- **A0005's six lines, unchanged.** They check S0021's decision log reasons.
- **One new part.** It checks S0022.

Stand-ins replace only `gcloud` and `curl` (decision 10). git is real: the checkout is a clone, and `SITE_CODE_URL` is this repository.

Command, run from the checkout's root with `w=$(mktemp -d)` and `trap 'rm -rf "$w"' EXIT`. The script is assembled from the two reports and the new part:

```sh
awk '/^## 2 Feature smoke test/,/^## 3 /' factory/features/F0048-*/done/F0048-A0004-acceptance.md | sed -n '17,179p' > "$w/feature-smoke.sh"
awk '/^## 2 Feature smoke test/,/^## 3 /' factory/features/F0048-*/done/F0048-A0005-acceptance.md | awk '/^```sh/{f=1;next} /^```/{f=0} f' >> "$w/feature-smoke.sh"
cat >> "$w/feature-smoke.sh" <<'EOF'
echo '$ the documenter writes only the story'\''s reasons (S0022)'
printf 'bullet in the shipped agents: %s\n' "$(grep -l 'write a "Why" or a "Rejected" only from what the story names' "$repo"/claude/agents/*.md | sed "s|$repo/||" | tr '\n' ' ')"
printf 'lessons order (documenter): %s\n' "$(sed -n '/^## Lessons/,$p' "$repo/claude/agents/documenter.md" | grep '^- ' | cut -c1-40 | tr '\n' '|')"
printf 'log entry: %s; Rejected lines in it: %s\n' "$(grep -c '^## The decision log holds only the human' "$repo/docs/decisions.md")" "$(sed -n '/^## The decision log holds only the human/,$p' "$repo/docs/decisions.md" | grep -c '^- Rejected')"
printf 'agents.md names the lesson: %s\n' "$(grep -c 'one lesson on the decision log' "$repo/docs/project-guide/agents.md")"
(cd "$repo" && uv run pytest -q tests/test_claude_agent_texts_decision_log.py tests/test_claude_agent_texts.py 2>&1 | tail -1)
EOF
sh "$w/feature-smoke.sh" 2>&1 | sed "s|/tmp/tmp\.[A-Za-z0-9]*|<d>|g"
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
$ the documenter writes only the story's reasons (S0022)
bullet in the shipped agents: claude/agents/documenter.md 
lessons order (documenter): - Run `make check` and every other make |- Give a project command that can take m|- The project guide is an index plus one|- In `docs/decisions.md`, write a "Why" |- Make every file you need outside the r|- When every file you changed is a docum|
log entry: 1; Rejected lines in it: 1
agents.md names the lesson: 1
................................                                         [100%]
```

The walk is green. The parts from A0004 and A0005 print what they printed then, line for line. The new part shows four things:
- Only the documenter carries the bullet.
- The bullet stands fourth of six, between the project guide's bullet and the temporary-directory bullet, and the documents-only lesson is still last.
- The log entry exists, with its one "Rejected" line.
- The project guide names the lesson.

The `pytest -q` line prints only dots, because `addopts` already sets `-q`. Run without `-q`, the same two modules print `104 passed in 0.10s`.

My first try at the walk piped into a `sed` with an empty pattern. The pipe killed the script before its `trap` ran, and that left one `/tmp/tmp.*` folder of the walk's own shape. I removed it, and when I ended no `/tmp/tmp.*` folder was left besides the walk's own self-removing one.

Not walked:
- S0010's ten-minute exit and S0013's pause rule need a running loop and a clock. Their tests cover them.
- A real container stop (S0016) and a real `podman image prune` (S0018) are the human's checks on `vm`.
- S0022's lesson changes what a later documenter does, which no walk can run. The walk checks its text, its place and its documentation.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

A0001 to A0005 collected S0001 to S0021. New from S0022:
- **A0005's proposal did not foresee an earlier test.** `tests/test_claude_agent_texts.py` pins each shipped agent's whole `## Lessons` list in its `LESSONS` table. The proposal's Interface named only the new test module. Intake accepted it without seeing the conflict (entry 3). The coder stopped at a red `make check` and asked for leave (entry 7), and the human gave it (entry 8). That cost one question, 4 minutes of waiting and two extra runs (the coder's second run and the tester's). This was my role's slip. A proposed story that changes a pinned text should name the pinning test and the leave it needs, as `feature.md` did for S0014 and S0017. One question in 22 stories does not need a story of its own. It is noted for the human (see 6).
- **The tester ran the test file a second time** (entry 12) after rewrapping a string to fix E501. That went against its one-run rule, and the tester said so. No story.
- **The coder's first run had one denied tool call** (`denials: 1`, no path, in `F0048-S0022-...costs.jsonl`). Its journal does not say what was denied. The run ended with a proper question, so this is a note only.
- **The documenter applied the new lesson to its own entry.** Every reason and the rejected option came from the story's Description and docs criterion (entry 18), which is the lesson working as meant.
- The reviewer, documenter and smoke tester noticed nothing else, and the coder noted "nothing" twice.

Still standing from A0003 to A0005, as notes, with no story:
- gcloud's real wording for a missing job is unconfirmed (`is_not_found` in `operator/bin/site`).
- `pyproject.toml:65` names a work item in a comment. That file is the human's.
- Test-side copies left on purpose: `gcloud_words` beside `words`, and `JOB` and `IMPERSONATE` in both `tests/site_check_support.py` and `tests/operator_job_support.py`.
- `src/factory/adapters/opencode_runtime.py:480` is still uncovered, as it was before this feature.
- The token entry's "Why" holds a test practice (the real `git`), as A0005 noted.

## 5 Documentation as a whole

I read S0022's two documentation changes against each other and against the agent's text.

- **`docs/decisions.md`, the new entry "The decision log holds only the human's reasons".** Its "Decision" matches the bullet at `claude/agents/documenter.md:75`. Its "Why" agrees with the S0021 entries before it on the numbers: seven entries, five unsourced options. Its "Rejected" line comes from the story's docs criterion. Its date line names the story and decision 27.
- **`docs/project-guide/agents.md:260`.** The paragraph now describes the documenter's lessons in their real order: the decision-log lesson, the temporary-directory lesson "before its last bullet", and the documents-only lesson last. The walk's order line agrees.
- **Wording note.** The paragraph says the documenter "has one lesson on the decision log", while `intake`, `tester`, `coder`, `reviewer` and `documenter` "have more". Both are true. The paragraph is now one 2,000-character line. It is still accurate, though a newcomer reads it with effort. This is a note, not a finding.

`README.md`, `operator/README.md`, `docs/operator-guide.md` and the rest of the project guide are unchanged since A0004, which read them whole. The walk's guide lines print as they did then, and `make documents` is green. A0004's note on `docs/operator-guide.md:884` (whether the prune removes the layer cache's intermediate images) is still unconfirmed on `vm`, and is kept under 6.

## 6 Decisions taken for the human

The 27 decisions of `feature.md` stand as built, and I found no story that departs from one. These items are unchanged:
- A0002's seven additional items and A0003's three are the human's to accept or revisit.
- A0003's third item is still open: whether `podman image prune` without `-a` removes the layer cache's intermediate images. One `podman images -a` before and after a prune on `vm` settles it.
- A0005's items 1 and 2 are unchanged.

A0005's item 3 was settled as the story was started. Where a story names no rejected option, the entry gets no "Rejected" line, and `Rejected: none recorded.` was not taken. The documenter names that entry in its journal.

New from S0022:
1. **`feature.md` does not name S0022.** It is in neither Scope nor Stories, and no decision gives its reason beyond decision 27, which names S0021. The human may add a scope bullet ("The shipped documenter writes only the story's reasons into the decision log (S0022, from the fifth acceptance, decision 27)") and a line in Stories. The file is the human's (R14).
2. **The leave for `LESSONS["documenter"]` was given during the build** (entry 8, option (a)), not before the story started. A0005's proposal should have named it. If the human wants this not to recur, a later story could add a lesson to the acceptance reviewer and to intake: a story that changes a pinned agent text names the pinning test and asks for its leave. I propose none, because one question in 22 stories does not justify a story's run cost (see 8).

Earlier tests changed by S0022: `tests/test_claude_agent_texts.py`, `LESSONS["documenter"]` gained one entry. The leave was the human's answer in S0022's entry 8, and the reviewer named it in entry 16. The test keeps its name and still pins the whole list. Every earlier test changed in F0048 has its leave named (A0001 to A0005).

## 7 Slow checks

There is nothing to run beyond `make check`. The `Makefile` offers no image scan and no SBOM. `duplicates` is the reviewer's record: S0022 recorded 0 new, 42 known, 0 gone. `documents` is the docs stage's check, and the walk ran it green. `mutants` falls under 3.

My `make check` was green, ending `test: green (83.8 s)` and `check: green`, with total coverage at 99.56 %. Its JUnit report (`.reports/junit.xml`) holds 8639 tests, ten more than at A0005, and they sum to 708.6 s.
- **Slowest single tests**, all outside this feature, each about 10.0 s: `tests/adapters/test_podman_timeout_status.py::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run[255-at-the-limit]`, the same test's `[137-at-the-limit]` row, and `tests/adapters/test_process_streaming.py::test_child_is_killed_at_the_time_limit_and_no_later_line_is_passed`. They are `ROOMY_LIMIT` tests.
- **Slowest modules**, also outside the feature: `tests/adapters/test_process_session.py` (61.1 s), `test_claude_runtime_resume.py` (52.5 s) and `test_process_drain.py` (32.5 s).
- **The feature's slowest modules** are unchanged: `tests/test_operator_site_check.py` (11.1 s), `tests/test_vm_job_start.py` (7.1 s) and `tests/test_operator_job.py` (6.0 s).
- **S0022's new module** takes 0.01 s.

Disk: at the previous record (`disk start`) all three paths had 45.9 GB free, and now they have 43.5 GB. The instance's own use is unchanged: 1.3 GB for `/srv/factory/vm`, and 0.0 GB for its state and for `/tmp`. So 2.4 GB less is free on the shared disk outside the instance's paths. The feature's changes since then do not explain it: S0022 added one line of an agent's text, one decision entry and a 43-line test. A `make check` and a walk took about 0.1 GB at A0005. This acceptance has run twice, a crash and this run, and each started a stage container. A stage image rebuild or an unpruned image in the shared storage is the likely cause, but I cannot see it from inside the stage. I name it for the human to check on `vm` with `podman system df`.

## 8 Cost

The stories cost 274 runs, 360.1 minutes, 2258 turns and $94.20 (8.15 M tokens in, 59.78 M more from cache, 1.24 M out). Since A0005, one story was added:
- **S0022:** 9 runs, 6.8 minutes, $1.48.

Of those nine runs, two came from the question about the earlier `LESSONS` test (see 4). Without it the story would have taken about seven runs and roughly $1.10. Over the whole feature, S0005 ($9.15), S0001 ($8.48) and S0003 ($7.92) still stand out. As A0001 found, each of their reviews stopped at the first failing group until S0011.

Human interventions: 39 questions answered (35 `question`, 1 `attempts_cap`, 3 `round_cap`), and the stories waited 5.6 h for them. S0022 added one question, the coder's request for leave to change `LESSONS["documenter"]`, which waited 4 minutes (13:21 to 13:25). The story that needed the human most is still S0001, with four answers, one of them a round cap. About a third of all questions were leaves for earlier tests or the notes rule. S0017 has since written the notes rule down, and S0022's question was another leave.

This acceptance's own first run crashed and its work was discarded (journal entry 2). It is not in the stories' cost.

## Proposed stories

None. The items left are the human's bookkeeping in `feature.md` and an open check on `vm` (see 6). The one slip of a proposal cost a single question, which is less than a story to prevent it would cost.

## Journal

1. factory: started acceptance as vm.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit 8597815d9d479c578cc961d779755abd461fba46.
3. factory: started acceptance as vm.
4. acceptance-reviewer: accepted; 0 stories proposed
   1 Scope: all 21 scope bullets are built. S0022, the only story since A0005, adds the decision-log lesson to `claude/agents/documenter.md:75`, plus its log entry, its project guide line and its tests (merge `3fed3bd31`). `feature.md` names S0022 in neither its Scope nor its Stories; this is bookkeeping for the human, listed under 6.
   2 Feature smoke test: green. The walk runs A0004's 163 lines and A0005's six lines unchanged, from `site init` to `site: ready`, then the job's whole life, the skill's scripts, `vm/job-start.sh` on stand-ins and S0021's reasons. A new part checks that only the documenter holds S0022's bullet, in its place, with its log entry and its guide line. The output is pasted in the report, and no `/tmp/tmp.*` folder is left.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: A0005's proposal missed the earlier `LESSONS` table in `tests/test_claude_agent_texts.py`, which cost one question and two runs; this was the acceptance reviewer's slip. The tester ran its tests a second time, against its one-run rule, and said so. The coder's first run had one denied tool call that its journal does not explain. The earlier notes still stand.
   5 Documentation: the new log entry and `docs/project-guide/agents.md:260` agree with the agent's text and with the S0021 entries. The guide paragraph is now very long, a note only. The prune note at `docs/operator-guide.md:884` is still unconfirmed on vm.
   6 Decisions: the 27 decisions stand as built. A0005's item 3 was settled: no "Rejected" line. New: add S0022 to `feature.md`, and the leave for `LESSONS["documenter"]` was given during the build (entry 8). The one earlier test changed has that leave named.
   7 Slow checks: nothing beyond `make check`, which is green: 83.8 s, 99.56 % coverage, 8639 tests summing to 708.6 s. The slowest tests are ROOMY_LIMIT tests outside the feature. Free disk fell from 45.9 to 43.5 GB while the instance's use stayed at 1.3 GB. The feature's changes do not explain that; the human can check it with `podman system df` on vm.
   8 Cost: 274 runs, 360.1 min, $94.20. S0022 cost 9 runs, 6.8 min and $1.48, two of those runs because of the leave question. 39 questions were answered and the stories waited 5.6 h; S0001 still needed the human most. This acceptance's first run crashed and is not counted.
