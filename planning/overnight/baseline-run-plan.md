# The baseline todo run (step 10): the plan

Step 10 of "The order of the work after F0011" (`planning/overnight/restructure-after-f0011.md`): v1.1, as it stands after every step before, builds `demo/todo-service` into a new empty repository under the strict rules, while a Claude Code session plays the human. Disk records are taken at the start and at the end. The run passes when:

1. every story and acceptance is accepted;
2. no fix to `factory-rf` is made during the run;
3. every stop reached the human;
4. the cost and the agent minutes of each story that is first-pass in both runs are within the band of run 4's (section 1; the band's direction is open point Q1).

Start-to-archive minutes are recorded, not compared. The run is the baseline v2 is measured against.

Written on 2026-10-19 from the records named in each section. "The v1.1 repository" means `pkrahmer/factory-rf`, or `pkrahmer/factory` after the rename of step 9. Every command runs in Git Bash on the human's PC unless it says otherwise.

## 1. The numbers to compare against

### Sources

- **Run 4** (v1, 2026-10-05, 16:49 to 19:36 UTC, on `pkrahmer/factory-demo-todo`, since renamed `pkrahmer/factory-v1-demo-todo`). The data is the first 59 lines of `docs/reference/data/demo-dispatches.jsonl` in v1's repository (local clone `C:/Dev/Projects/factory`, at `f8bc9d2`). Each line is one agent run: `seconds` is the run's wall clock, summed over a budget resume, and `cost` is in USD. The summary table is in `demo/todo-service/README.md`, "What a run looks like". Recomputed from the records for this plan, it matches to the cent.
  - The models, from the run's transcripts (`session-logs/container/-work-factory-demo-todo/`, messages dated 16:49 to 19:37 UTC): `claude-opus-5-5` (429 messages) and `claude-sonnet-5-5` (100), under Claude Code 2.1.289.
- **The shakedown run** (step 4; v1.1 at image `0f617cde`, instance `shakedown`, Docker Desktop, the subscription; 2026-10-18 05:45 to 07:53 UTC, on the new `pkrahmer/factory-demo-todo`). The data is the cost sidecars `factory/features/*/done/*.costs.jsonl` on that repository's `main`, read with `gh api`. Agent minutes are the sum of `duration_seconds` over the `completed` records, and cost is the sum of `cost_usd`. The night log's result table (`docs/runs/2026-10-12-overnight/night-log.md`, "the shakedown run (plan step 4): result") matches.
  - The models are not recorded (gap G2). The image pinned Claude Code 2.1.296 (`b642dd31`), and the agent files name the same aliases as v1's (`opus` for tester, coder, reviewer, smoke tester and acceptance reviewer; `sonnet` for intake and documenter; the same efforts).

### First-pass, defined

**A story is first-pass in a run when each of its six stages ran exactly once, with no question to the human, no send-back and no retry.** In v1 those stages are intake, tester, coder, reviewer, documenter and demo; in v1.1 they are intake, tests, doing, review, docs and smoke-test. So a first-pass story has six completed agent runs, and the run's journal holds no blocking question, no stall, no crash and no `closed` round before its approval. The story's numbers are then all of its runs up to its first approval hand-over.

**The comparison set is the stories that are first-pass both in run 4 and in the baseline run.** Run 4's first-pass stories are F0001-S0002, F0001-S0003, F0002-S0002, F0002-S0003 and F0003-S0001. The shakedown is shown for information only, because it ran on the demo's earlier texts (see section 4).

The rejected alternative: count the runs up to the first approval, minus the runs that a human's answer caused. Three reasons:

- The two runs cannot be cut at the same place. In v1 a question ends the stage, and the answer reruns it. In v1.1, round 2 and later reviewer notes go forward instead of back (F0021-S0005), and a standing leave removes the helper questions (F0016). So "the runs an answer caused" is a different set in each run.
- Most of the shakedown's extra runs came from review rounds the agents started, not from answers. The cost of a send-back is not the human's doing, but it is not first-pass either.
- The definition above needs only the stage list of the cost records, which both runs have. It is also the one `demo/todo-service/README.md` already states.

Stories that are not first-pass, and the three acceptances, are recorded in the report beside run 4's numbers, but they are not judged.

### The table

Band = run 4's value ± 25 %. Unrounded values; minutes are agent minutes (the sum of the runs' wall clock).

| Story | Title | Run 4 runs | Run 4 cost | Run 4 min | Cost band | Minutes band | Shakedown runs | Shakedown cost | Shakedown min | Shakedown vs run 4 |
| :- | :- | -: | -: | -: | :-: | :-: | -: | -: | -: | :- |
| F0001-S0002 | Service layer with filtering | 6 | 1.314 | 2.47 | 0.99–1.64 | 1.85–3.08 | 6 | 0.858 | 2.96 | cost −35 %, min +20 % |
| F0001-S0003 | HTTP API | 6 | 1.536 | 4.05 | 1.15–1.92 | 3.04–5.06 | 12 | 2.350 | 7.61 | not first-pass (question, review round) |
| F0002-S0002 | Version command | 6 | 0.853 | 2.08 | 0.64–1.07 | 1.56–2.60 | 6 | 0.568 | 2.20 | cost −33 %, min +6 % |
| F0002-S0003 | Todo statistics | 6 | 1.124 | 2.23 | 0.84–1.40 | 1.68–2.79 | 14 | 2.287 | 6.69 | not first-pass (two review rounds) |
| F0003-S0001 | Title search | 6 | 0.998 | 2.30 | 0.75–1.25 | 1.72–2.88 | 6 | 0.785 | 2.63 | cost −21 %, min +14 % |

Recorded but not compared (not first-pass in run 4):

| Item | Run 4 runs / cost / min | Shakedown runs / cost / min |
| :- | :- | :- |
| F0001-S0001 Domain model and in-memory repository | 11 / 2.846 / 6.10 (a review gap, a question) | 6 / 1.520 / 3.86 (first-pass) |
| F0001-S0004 SQLite repository and persistence switch | 8 / 1.944 / 5.00 (one review rework) | 23 / 4.214 / 12.94 |
| F0002-S0001 Health endpoint | 7 / 1.356 / 2.77 (intake question) | 6 / 0.740 / 2.62 (first-pass) |
| F0001-A0001 acceptance | 1 / 1.588 / 5.03 | 1 / 2.247 / 8.12 |
| F0002-A0001 acceptance | 1 / 1.466 / 4.97 | 1 / 1.208 / 4.26 |
| F0003-A0001 acceptance | 1 / 0.867 / 3.15 | 1 / 1.087 / 3.96 |
| Total | 59 / 15.89 / 40.1 | 82 / 17.88 / 57.9 |

**What the shakedown already shows.** On the three stories that were first-pass in both runs:

- **Cost.** v1.1 was 21 to 35 % cheaper. The cost fell in every stage: intake −48 %, tests −33 %, doing −21 %, review −27 %, docs −27 %, smoke test −31 %, summed over the three stories. So the cause is the runtime (Claude Code 2.1.289 against 2.1.296, its caching or price table) or the shorter v1.1 prompts, not one story. Under a two-sided band, two of the three stories would fail on cost for being cheaper.
- **Agent minutes.** v1.1 was 6 to 20 % slower, again in every stage but intake (intake −19 %, the others +7 % to +36 %). One cause seen is the run start through `sudo` and the login shell. The confinement of F0019 adds its own step after the shakedown.

### Gaps, and how the run measures them instead

- **G1. Run 4's per-stage end reasons and journal causes.** v1's records hold `ok` only. First-pass in run 4 is read from the stage sequence (six runs, one per agent), which the README's "What happened" column confirms. Nothing more is needed.
- **G2. The model behind the alias in the shakedown and in the baseline.** v1.1's cost record has no model field. The baseline records it from the agent's transcripts in the instance's `claude-home` volume: at the end, the session counts the `message.model` and `version` fields, read-only, as was done for run 4 above. If the model behind `opus` or `sonnet` is not `claude-opus-5-5` or `claude-sonnet-5-5`, the report says so first, and the cost comparison is marked "model changed". The minutes comparison is marked the same way.
- **G3. Pricing on the subscription.** Both runs ran on the subscription, so the cost is Claude Code's own `total_cost_usd` estimate, not a bill. It stays comparable only while the price table of the pinned Claude Code is the same. The report names the Claude Code version of each run.
- **G4. The shakedown's disk records.** None were taken for step 4. The bound in section 2 is therefore set from the self-build's acceptance records (`/state/records/disk.jsonl`) and the night log's host records, and the baseline's own records become the reference for v2.
- **G5. The provider limit and the spend window (F0020).** A run that ends with `provider_limit` and is resumed is a new kind of run. If it occurs in a compared story, the story's minutes are the sum of the run parts without the wait. The report lists such a story, and it is judged only if that sum is clear from the records. Otherwise it is recorded as "not comparable".

## 2. The setup, step by step

### Before the day ([H] = the human's hands)

1. **[H] The new repository.** Create `pkrahmer/factory-baseline-todo`: private, empty (no README, no licence, no `.gitignore`).
   - Settings: allow merge commits, and turn "Automatically delete head branches" off (`demo/todo-service/README.md`, "What you need").
   - Check, read-only: `gh api repos/pkrahmer/factory-baseline-todo --jq '{allow_merge_commit,delete_branch_on_merge}'` must give `true`, `false`.
2. **[H] A checkout of v1.1 for this run only.** Clone it at the tagged commit the run measures, beside the others: `git clone https://github.com/pkrahmer/<v1.1 repo>.git C:/Dev/Projects/factory-baseline`, then `git -C C:/Dev/Projects/factory-baseline checkout baseline-v1.1`. The tag is set on `main` when section 4 holds, and pushed. Why a checkout of its own:
   - `image/compose.yml` mounts `image/secrets/hosting-token` beside itself into every instance. In `factory-rf` that file holds `self`'s token, limited to `factory-rf`.
   - A separate checkout gives the baseline its own token without touching `self`.
   - It also fixes the code the image is built from: the strict rule "no fix during the run" can be checked with `git -C C:/Dev/Projects/factory-baseline status` and `rev-parse HEAD` at the end.
   - The alternative is open point Q3.
3. **[H] The three host files** in `C:/Dev/Projects/factory-baseline/image/secrets/`:
   - `hosting-token`: a new fine-grained token limited to `pkrahmer/factory-baseline-todo`, with Contents, Pull requests and Issues read and write, and Metadata read (`planning/overnight/first-start-checklist.md`, "2. The token").
   - `claude-token`: a copy of the subscription token that `self` uses (`claude setup-token`; the same account and the same usage windows).
   - `anthropic-api-key`: an empty file, `: > image/secrets/anthropic-api-key`. Compose refuses to start without it (F0020 change 1), and an empty file means "no key", so the runs use the subscription.
   - The session never opens, prints or copies any of the three. It checks only `test -s` on the first two and `test -e` on the third.
4. **[H] The target's local clone**: `git clone https://github.com/pkrahmer/factory-baseline-todo.git C:/Dev/Projects/factory-baseline-todo` (empty; git warns of an empty repository).

### Seeding the repository (the session; the same way as the shakedown's `0885fef`)

Commands run in `C:/Dev/Projects/factory-baseline-todo`, with v1.1's commands taken from the baseline checkout: `V11=C:/Dev/Projects/factory-baseline`.

1. Copy everything in `$V11/demo/todo-service/project/` into the clone's root, `.gitignore`, `.secrets.baseline` and `security/` included: `cp -r "$V11/demo/todo-service/project/." .`
2. `uv sync`, then `make check`. It must end with `check: green`.
3. `git add -A && git commit -m "Set up the repository for the factory" && git push -u origin main`. The commit's id goes into the run log.
4. Copy F0001 only (`demo/todo-service/README.md`, "Put the stories in"):
   - `mkdir -p factory/features && cp -r "$V11/demo/todo-service/features/F0001-todo-service" factory/features/`
   - Check it: `uv run --project "$V11" factory-check-story factory/features/F0001-todo-service/backlog/*.md`. Every line must end in `: ok`.
   - Commit `F0001: add the feature and its stories` and push.
   - F0002 and F0003 follow only when the feature before them is accepted, as in run 4 and the shakedown.

### The instance

From `C:/Dev/Projects/factory-baseline`, in one shell kept for every compose command of the run:

```bash
export FACTORY_REPOSITORY_URL=https://github.com/pkrahmer/factory-baseline-todo.git
export FACTORY_INSTANCE=baseline
export FACTORY_IMAGE=$(git rev-parse --short=12 HEAD)
docker compose -f image/compose.yml up -d --build
docker compose -f image/compose.yml exec factory python -m factory.entry.health   # must print: healthy
```

- The compose project is `factory-baseline`, so the container is `factory-baseline-factory-1` and the volumes are `factory-baseline_work`, `_state` and `_claude-home`. Nothing is shared with `self`, the shakedown or v1.
- **The runtime: Claude Code on the subscription**, as run 4 and the shakedown. `FACTORY_AGENT_RUNTIME` stays unset (its default is `claude`, F0020 decision 16), and so does `FACTORY_SPEND_WINDOW`: no throttling, as in run 4. The opencode run of F0020's change 6 is a separate comparison, not this baseline.
- **Docker Desktop**, not Podman, for comparability with run 4 (step 1b).
- The login: the token file is injected (F0014), so no interactive login is needed. If the preflight's `agent-run-probe` fails, that is a fault to stop on (section 3), not a login to repair by hand.

### The disk records, at the start (before the first story starts) and at the end (after the last acceptance is archived)

Host side, by the session:

```bash
df -h /c
ls -l "$LOCALAPPDATA/Docker/wsl/disk/docker_data.vhdx"
timeout 60 docker system df
```

Container side, read-only:

```bash
MSYS_NO_PATHCONV=1 docker exec factory-baseline-factory-1 sh -c 'df -h / /work /state /tmp; du -sh /tmp /work /state 2>/dev/null; ls /tmp | wc -l'
MSYS_NO_PATHCONV=1 docker exec factory-baseline-factory-1 tail -n 3 /state/records/disk.jsonl
```

- v1.1 writes its own disk record (`occasion` `start` and `acceptance`); the session's numbers go beside it.
- **The bound** (open point Q4, recommended): from start to end, the container's `/tmp` grows by at most 100 MB, `/work` by at most 2 GB (one checkout with its `.venv`, `mutants/` and `.reports/`), and Docker's disk image by at most 5 GB beyond the image build. Any growth the run does not explain is a finding. The first-time image build is measured separately: one record after `up --build`, one before the first story.

### Pacing

- The session starts one story at a time, the next once the one before is archived. A feature is copied in once its acceptance is merged.
- The shakedown took 2 h 08 min of wall clock and about 3 % of the weekly window. Plan for three hours, and start below 70 % of the weekly window and below 50 % of the 5-hour window.
- **`self` stays idle for the whole run**: no story in progress, no planning agent. Two instances on one subscription share its windows, and the shakedown showed `pytest -n auto` spikes of 12 to 19 cores, which would lengthen the other instance's agent minutes. Recommended: `docker compose -p factory-self stop` before the start and `start` after the end. The volumes stay.

## 3. The session's rules as the human

The session follows `demo/todo-service/README.md`, "For the session: how to run the demo", and `planning/operator-playbook.md`, with these stricter rules.

**What it may answer, and how.**

- **A question** is answered in one comment on the pull request: the option and its reason. The answer must stay inside the demo's product. It is taken from the feature's "Decisions taken for the human" in the target's `feature.md`, the README's "as a sensible single-user to-do service would", or the agent's own recommendation when that widens nothing.
- **A new product decision** is written into the target's `feature.md` as a numbered decision, in a commit on the target's `main` (never in a running work item; playbook section 3). This is a human's act inside the demo, not a fix to `factory-rf`. Each one is counted.
- **At approval**: the six checks of the playbook (section 3), then `gh pr merge <n> --merge`. A story that does something wrong is commented and closed (a send-back). That is a human's act, counted, and allowed.
- **At a cap**, as the playbook says. One more round with the findings named is allowed. Silencing a check, or widening the scope, is not.
- **An acceptance** is merged when its recommendation is fair. Its proposed stories stay in `backlog/` and are not started (the demo's rule).

**What counts as a fix, and fails the run.** Any of these, during the run:

- a commit to the v1.1 repository that the run caused, or any change in `C:/Dev/Projects/factory-baseline` (its tree must stay at `baseline-v1.1`);
- a rebuild of the instance's image;
- a change to the agent files, `settings.json` or anything in the instance's volumes;
- an edit, as root, inside the container (removing a leftover, changing a mode);
- a change to the target's `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `factory/pipeline.yml`, `factory/story-form.md`, `.secrets.baseline` or `security/`: they are v1.1's demo, so a change there is a fix to v1.1;
- a change to a story text that is not the intake's or the reviewer's;
- a stage's command run by hand to help a story;
- a push to a `work-item/` branch;
- an edit of a running work item on `main`;
- a change to an operator setting while the instance runs.

A fault found during the run is recorded with where it sat. The run then either stops (next paragraph) or goes on unaided. It is never repaired.

**What to do at a stop.** A stop is a stop in force in `python -m factory.entry.health`, a `stop` or `iteration failed` line in `/state/factory.log`, or a `blocked=` on the board.

- **Read before acting.** Note whether the stop reached GitHub: a comment or a label on the pull request, or the `stops recorded` commit and its line in `factory/stops.jsonl` on the target's `main` (F0021-S0003). "Every stop reached the human" fails for each machine or repository stop that the log shows and `factory/stops.jsonl` does not, and for each blocked work item whose question never appeared on its pull request.
- **A story's stop** (question, cap) is answered as above.
- **A machine stop** the playbook covers without a fix (low disk, Docker not answering):
  - It is cleared from outside, by the human's machine, never inside the container: free space on C:, or restart Docker Desktop once and then `start` only the `baseline` instance.
  - It is logged as an intervention, and the run goes on.
  - The story in flight is then marked "interrupted" and is not compared.
- **Any other stop**, the same stall twice, or a stage that cannot finish: the run **stops**. Leave the pull request as it is, take the end disk record, and write the report with the verdict "failed: <fault>". A baseline that needed a fix is no baseline. The fix goes into the v1.1 repository afterwards, as a story, and step 10 is repeated from section 2 with a new repository.
- **Stop and ask the human** also when:
  - the 5-hour window passes 95 % (let the story in flight finish, and start the next after the reset);
  - the weekly window passes 90 %;
  - a story costs more than twice its run 4 cost with no reason in its journal;
  - the run passes 40 USD;
  - the run passes five hours.

**The watcher and the heartbeat.**

- **The watcher.** A copy of the shakedown's `demo_follow.sh`, placed in the run's own folder (section 5), not in a session scratchpad, which is lost with the session. Run it with `FOLLOW_CONTAINER=factory-baseline-factory-1`, with the Monitor tool or in the background, for each story in flight.
  - It polls `factory-watch` every 45 s, prints each change, and ends on `stage=approval`, a `blocked=` that is not `-`, an empty board after work, or its own timeout (60 min).
  - The board only: it is the tool the human has.
- **The heartbeat**, every 20 minutes while the run is on. Each is one line in the log; "nothing to do" when nothing changed.
  - `timeout 15 docker info`;
  - `df -h /c` (stop below 5 GB);
  - the last ten lines of `/state/factory.log` (a new `stop` or `iteration failed` line);
  - the health status;
  - a stage running more than twice its run 4 time, or over its `time_limit`;
  - the two usage windows.

**What it logs, and where.**

- **The run log**: `docs/runs/<date>-baseline-todo/run-log.md` in the v1.1 checkout the human works in (`C:/Dev/Projects/factory-rf`), the human's folder (outside every write path).
  - One row per act, with its local and UTC time: setup steps and their commit ids, each start, question and answer (its cause, from the journal), new decision, merge, close, heartbeat, stop and intervention, and the disk records.
  - It stays uncommitted until the run has ended, so that nothing lands on the v1.1 repository during the run. It is then committed with the report.
- **The data**, copied read-only at the end into the same folder:
  - the target's `factory/features/*/done/*.costs.jsonl` and `*.md`, and `factory/stops.jsonl`;
  - `/state/records/disk.jsonl` and `/state/records/project-commands.jsonl` (`docker cp`, or `docker exec … cat`);
  - the tail of `/state/factory.log` from the run's start;
  - the model and version counts of G2.

## 4. What must be true before it starts

### The steps before step 10, and what each changes in the numbers

| Step | What it changes for a todo story | Effect on cost / agent minutes of a first-pass story |
| :- | :- | :- |
| F0016 (v1, after the shakedown) | the standing leave to move a shared test helper; the reviewer names every earlier test it sees changed; the approval's description written before its push | fewer questions and send-backs (more first-pass stories); the reviewer's list adds a little; none on a first-pass story |
| The demo's texts (F0016 change 1, `planning/overnight/demo-fixes-F0016.md`) | more criteria in all eight stories (every rule side the shakedown found untested; F0001 decisions 12 to 17, F0002 7 to 9, F0003 3 to 4) | more test rows for the tester and the coder: a small rise in both, and fewer questions. This is the main reason the shakedown cannot stand in for the baseline |
| F0017, F0018 | `make mutants` under its own `TMPDIR`; documents | none |
| F0019 (the kernel's write guard) | every agent run starts through `factory-confine` under `sudo` | a fixed start cost per run (seconds); a write refused by the kernel can cost a retry; the hook `factory-guard` is still there until its cross-check is done |
| F0020 (opencode; the Claude Code runtime's streaming, `provider_limit`, the spend window) | the Claude Code runtime's output streamed; a wait and resume on a provider limit; change 5: the demo's `Makefile` moves its root report files into `.reports/`, and its pipeline definition names tool paths | none intended on the subscription with `FACTORY_SPEND_WINDOW` unset; a provider limit is G5 |
| F0021 (the human's acts recorded) | causes in the journals; the cost table counts the human; stop records; the reviewer's round 2 notes and its leave for a criterion that pins built behaviour | none on a first-pass story; fewer later rounds; the counts feed the report |
| F0022 (a project's own skills and agents) | `Skill` in every agent's tools, rule R15 in every agent text, empty factory-owned `skills/` and `commands/` in the agent's home; the demo gets no agents or skills | a slightly longer system prompt in every run: a cent-level rise |
| F0023 (a known result is not checked again) | opt-in by `not_read` in the pipeline definition; the demo's pipeline definition gets none (its decision 13) | none on agent minutes: the factory's own project commands are not agent runs. If the demo were opted in, the docs stage's check would be skipped: shorter start-to-archive, the same agent minutes |
| F0024 (mutation testing per story) | the demo keeps the feature-level `mutants` (its decision 12); the reviewer's text gains "read the story's surviving mutants"; the acceptance reviewer reruns `make mutants` while it is partial | the reviewer's new paragraph, when no mutants record exists, should cost nothing but its reading; the acceptances may run longer; acceptances are not compared |
| F0025 (the project guide split) | `factory-rf`'s own guide only; the demo keeps one `docs/project-guide.md` (its decision 7) | none |
| Step 9, the rename | repository names, remotes, `FACTORY_REPOSITORY_URL` of `self` | none; the baseline checkout clones the renamed repository |

**What keeps it fair:**

- The demo is built as shipped. No `not_read` is added, and no per-story mutants record or project agent: the opt-ins of F0023 and F0024 stay off. The baseline then measures v1.1's engine and agents on the same demo, not a tuned demo.
- A later run with the opt-ins on is a separate measure for v2, compared against this baseline, not against run 4.
- The Claude Code pin stays at what the image carries at the tag. A newer pin is a human's choice made before the tag, named in the report.

### The 25 % band: recommendation

Apply it to both cost and agent minutes, as the human said, but as an upper bound only: **a compared story passes when its cost and its agent minutes are each at most 125 % of run 4's.** Below 75 % is recorded and explained, but does not fail. Reasons:

- The shakedown, on the same subscription, already ran 21 to 35 % below run 4 on cost in every stage. That is the runtime's doing. A two-sided band would fail a cheaper v1.1, which is not what the baseline is for.
- Agent minutes ran 6 to 20 % above run 4, and F0019's confinement and F0022's longer prompts add a little. The upper bound on minutes is the real test, and it should stay.
- On cost, the upper bound is loose given the shakedown's offset, but a story that costs more than run 4 plus 25 % despite that offset is a real regression.
- The alternative (open point Q1, option B) keeps the band two-sided but compares against the shakedown's ratio, not run 4's. It is more exact, but it has three numbers to stand on.

The rule stays per story, as the human's answer says. The report also gives the sum over the compared stories, which is less noisy at 0.85 to 1.54 USD per story.

**If no story is first-pass in both runs**, the rule cannot be applied. The report says so, and the run's comparison is "not measured", not "passed". Expected: three to five stories, since the demo's texts are now clearer than in the shakedown.

### The checklist, true at the tag `baseline-v1.1`

1. F0020, F0022, F0023, F0024 and F0025 merged and accepted on the v1.1 repository. Every acceptance's proposed stories are either built or recorded as deferred in their `feature.md`. No work item is in progress, and no pull request is open.
2. The rename of step 9 done. `self` runs on the renamed repository, healthy.
3. `make check` green on `main` at the tag, and `tests/test_demos.py` among it, so the demo's texts and pipeline definition load in v1.1 as tagged.
4. F0020's change 5 is in `demo/todo-service/project/` (the `.reports/` files and the tool paths). Without it, the kernel's guard refuses the demo's tools.
5. F0019's decision 16 (the hook's cross-check) settled. Whether `factory-guard` is still in the image is named in the report.
6. The Claude Code pin in `image/Dockerfile` noted (2.1.296 today).
7. C: has at least 50 GB free; Docker Desktop and WSL as on 2026-10-17 or newer (named in the report).
8. The weekly window below 70 %.

## 5. The report

`docs/runs/<date>-baseline-todo/report.md`, committed with the run log and the copied data once the run has ended. Sections:

1. **Verdict.** Passed or failed, and against which condition:
   - all accepted;
   - no fix during the run;
   - every stop reached the human;
   - every compared story within the band.

   One line for each, with its evidence.
2. **What ran.**
   - The v1.1 commit and tag, the image label, and the Claude Code version.
   - The models used (G2), with message counts per model.
   - The runtime and login (from the cost records' `login`), the Docker Desktop and WSL versions.
   - The target repository, its setup commit, and the wall clock from start to end.
3. **The comparison** (the judged table):

   | Story | Run 4 cost | Baseline cost | Δ % | Run 4 min | Baseline min | Δ % | First-pass in baseline | Within band |
   | :- | -: | -: | -: | -: | -: | -: | :- | :- |

   Then the sum over the compared stories, and the shakedown's column beside it for information.
4. **Every work item** (recorded, not judged):

   | Item | Runs | Agent min | Model min | Cost | Start to approval | Start to archive | Questions (cause) | Rounds | Stalls / crashes | Run 4 cost / min | Shakedown cost / min |
   | :- | -: | -: | -: | -: | -: | -: | :- | -: | :- | :- | :- |

   - Model minutes come from `model_seconds`.
   - The questions, waits and rounds come from F0021's journal records and the facts line.
   - Totals per feature and for the run.
5. **Per stage**: runs, agent minutes and cost per stage over the compared stories, for run 4, the shakedown and the baseline. This shows where a difference sits.
6. **The human's part.**
   - Every question with its cause and the answer.
   - Every new product decision (its number in the target's `feature.md`).
   - Every send-back, every intervention, and the hours waited.
7. **Stops.** Every stop from the factory log, with its time and whether and where it reached GitHub (`factory/stops.jsonl`, the pull request).
8. **Disk.** The start and end records, host and container side by side, their growth, and the bound with its verdict.
9. **Project commands.** From `project-commands.jsonl`: count, total and mean time per command and target, and the count of `make check` per commit (the F0023 lever measured on a project that did not opt in).
10. **Findings,** each with where it sat (agent, pipeline definition, engine, template, demo, machine) and the story or human's change it proposes. Proposed only: nothing is fixed during or as part of the run.
11. **For v2:** the numbers v2 is measured against: the comparison table, the per-item table, the totals and the disk growth, in one place.

## Open points for the human

| | Question | Options | Recommended |
| :- | :- | :- | :- |
| Q1 | The direction of the 25 % band | A: an upper bound only, cost and agent minutes each at most 125 % of run 4's; B: two-sided, against run 4 scaled by the shakedown's runtime offset; C: two-sided against run 4 as written (the shakedown would already fail two of three stories on cost for being cheaper) | **A**: the runtime made cost cheaper in every stage, and a cheaper v1.1 is no regression |
| Q2 | The definition of first-pass | A: six stages once each, no question, send-back or retry, in both run 4 and the baseline; B: the runs up to the first approval minus the runs an answer caused | **A**: measurable from both runs' records alone; B cannot be cut at the same place in v1 and v1.1 |
| Q3 | The hosting token and the instance's checkout | A: a separate clone `C:/Dev/Projects/factory-baseline` at the tag, with its own new token for the baseline repository only; B: one token covering both `factory-rf` and the baseline repository, run from the normal checkout (the checkout must then stay at the tag for the run) | **A**: `self` is untouched, and "no fix during the run" can be checked on the tree |
| Q4 | The disk bound | as in section 2 (`/tmp` +100 MB, `/work` +2 GB, Docker's disk image +5 GB beyond the build), or other numbers | the numbers of section 2; the run's own records then set v2's bound |
| Q5 | `self` during the run | A: stopped; B: idle but running; C: building on | **A**: no shared usage windows or CPU, and nothing that could look like a fix |
| Q6 | The repository's name | `pkrahmer/factory-baseline-todo`, or another | `factory-baseline-todo` |
| Q7 | The opt-ins of F0023 and F0024 for the demo | A: off (the demo as shipped); B: on | **A** for the baseline; B later, as v2's first comparison against it |
