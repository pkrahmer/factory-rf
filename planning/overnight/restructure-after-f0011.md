# Grouping the modules by domain within each layer (after F0011)

Decided by the human on 2026-10-14, in the session's discussion of the package tree. Built as one housekeeping story after F0011 is accepted, not before: F0008 to F0011's drafts name exact module paths, and a move in the middle of them would break those names.

## The order of the work after F0011 (the human's word, 2026-10-17)

The single order; the sections below hold the detail of each step.

0. Finish the unattended build: F0011 accepted (2026-10-17, second acceptance); `session-logs/refresh.sh`, the run record and the factory log copied into `session-logs/metrics/`, the summary for the human.
1. The small fixes, built by v1 as one housekeeping feature:
   1. `make check` faster: pytest-xdist over the 20 cores, one prepared git remote copied per test, `make secrets` over the changed files (granted).
   2. `make duplicates` as a lasting report (pylint R0801, vulture) against a baseline, a `records:` entry on the review stage, and its findings fixed: F0010-S0025's identity, F0011-S0001's `_rerun_seconds` and `_opening_text`, the redundant `tests/test_fault_path_names.py`, and the others listed below (granted).
   3. `make mutants` with mutmut, limited to the modules a feature changed, run by the acceptance stage; it takes in the parked draft F0011-S0007 (pin `GLOSSARY_FORBIDDEN` and the two section tuples, six hand mutants survived) (granted).
   4. What the todo run must measure: the low-disk machine stop, no temporary files left, the project-command and model-versus-tool records, the disk record.
   5. One test of the DTOs' own configuration; an answer at the send-back cap that can grant one more round.
   6. The compose project name per instance (`name: factory-${FACTORY_INSTANCE}`), so v1 and v1.1 cannot collide.
   7. The `demo/` frame: the index README and the one test in `make check` that walks every demo.
   8. The kill of an agent run under `sudo` at its time limit (F0010 decision 30, the human's answer of 2026-10-17): `timeout --signal=KILL <limit>` inside the `sudo` call, exit status 137 read as `time_limit`, a grace time on the outer call; observed for real in step 3.
   9. The document check as a check of the docs stage only (the human's answer of 2026-10-17): a `make documents` target, in v1's `factory/stages.yml` now (the human's change between two stories) and in v1.1's pipeline definition; F0011 decision 13 is superseded for the docs stage.
   10. Three of F0010's open points fixed (the human's answer of 2026-10-17): the agent cannot rewrite the agent files and `settings.json` in its home (owned by the factory, read-only to the agent); a missing health file after the start period reads as not healthy; a standing `main_branch_failing` is cleared when `main` is green again. The other two stay as built, by the human's decision: the token file's default only in the image's `ENV`, and the template's write paths.
   11. The lessons since F0010-S0017 in what v1.1 ships (the human's word, 2026-10-17): every row of `planning/lessons-for-the-skills.md` added after F0010-S0017 goes into the shipped agents' `## Lessons` (`claude/agents/`), and the Python rows into `template/CLAUDE.md` (F0012-S0028).
   12. A `Makefile` in `template/` for Python projects (the human's word, 2026-10-17): the three targets of the contract with H1's pattern (`<target>: green (<seconds> s)`, pytest-xdist, a JUnit report, `make secrets` over the changed files), the starting point of the todo demo's `Makefile` (F0012-S0029).
   The parked drafts F0003-S0011 and F0008-S0007 fold into 1.2 (the human's answer).
2. The first start on the real machine: the image pinned (base digest, the Debian versions), built, the one login as `agent`; the morning observations (`sudo`, the umask, the token mount, the time limit under `sudo`, F0010 decision 30); fixes found here go in through v1 before the run.
3. The todo demo prepared: run 4's eight stories and three features rewritten by hand into `demo/todo-service/` in v1.1's form, checked by 1.7's test; its `Makefile` prints `<target>: green (<seconds> s)` and writes a JUnit report like `factory-rf`'s after F0012's H1, so that the todo run records target times and the acceptance reviewer has a report to read (F0012 pre-check).
4. A short smoke run on the todo demo (its first story, on a new empty repository): the proof that v1.1 runs, and the condition of the handover in place of the full todo run, which comes last (the human's word, 2026-10-17).
5. The handover of `factory-rf` to v1.1, one human commit while no v1 story is in progress (see "v1.1 builds itself").
6. Built by v1.1 itself: a project's own skills and agents; then a new image and a short smoke run on the todo demo.
7. Built by v1.1 itself: the engine skips a project command whose result for that commit is already known (the docs stage's `make check` on code the documenter cannot change); then a new image and a short smoke run.
8. Built by v1.1 itself: the restructure (the tree chosen by the human on 2026-10-17: domains at the top, each with `domain/` and `application/` and its own ports, adapters grouped by tool, as simulated in the session; `tests/support/`, the project guide split by domain, `entry` renamed `entrypoints`); then `make check` and a short smoke run.
9. The rename, after a few clean self-built stories: v1's compose file gets `name: factory` first (the session may make that edit in `pkrahmer/factory`, the human's leave of 2026-10-17); `factory` becomes `factory-v1` and `factory-rf` becomes `factory`; the four lines of text; the remotes, `REPOS` and `FACTORY_REPOSITORY_URL` set again.
10. The todo run, at the very end (the human's word, 2026-10-17): v1.1 builds `demo/todo-service` into a new empty repository, a session plays the human, disk records at start and end. It passes when everything is accepted with no fix to `factory-rf` during the run, every stop reached the human, and cost and time per first-pass story are within 25 % of run 4's. It is the baseline v2 is measured against. It measures v1.1 as it stands after every step above.

At any time, the human's: Docker's disk image was compacted on 2026-10-17 (340.5 GB to 57.3 GB after `fstrim` and `diskpart compact vdisk`); updated the same day to Docker Desktop 4.95.0 (engine 29.8.2) and WSL 3.0.3; no disk limit exists under the WSL 2 backend; the disk image stays on C:, the much faster drive (the human, 2026-10-17), guarded by the heartbeat's `df -h /c`, by leaving no clones behind and by the trim-and-compact recipe; delete the scratch repository `pkrahmer/factory-night-scratch` and the branch `ccr-cf8b451b-yugt27`. The decisions taken for the human during the build were all confirmed on 2026-10-17.

## The decision

- The four layers stay at the top (`domain`, `application`, `adapters`, `entry`), and import-linter's layers contract stays as it is.
- Within each layer, the modules are grouped by domain in subpackages. Module names stay; only folders are added (`git mv`, so history follows).
- `tests/` mirrors the new tree. The whole-code searches, the helpers and `conftest.py` stay at the `tests/` root.
- `CLAUDE.md` Architecture gains one line: "Within each layer, modules are grouped by domain in subpackages."

Rejected for v1.1: domains at the top with layers inside, and role-named files (`models.py`, `ports.py`, `service.py` per domain). That layout reads more like the architecture, but the layer check would become a hand-kept list of about 90 modules, or a weaker rule. It is kept as an idea for v2, if v2 splits the factory into separate parts.

## The tree (simulated on 2026-10-14; entries marked ? to be checked against their contents)

```text
src/factory/
├── domain/
│   ├── shared/           errors.py, identifiers.py, paths.py ?
│   ├── git/              git.py
│   ├── work_items/       work_item.py, journal.py, sections.py, story_form.py, archive.py
│   ├── pipeline/         pipeline_definition.py, decisions.py, move_rule.py, labels.py, checks.py ?
│   ├── stages/           prompts.py, agent_runs.py, write_paths.py, lease.py, kill_points.py
│   ├── watching/         events.py, evaluation.py, tick_status.py, board.py
│   ├── pull_requests/    hosting.py, post_texts.py, answers.py, send_back.py, hand_over.py
│   ├── stops/            stops.py
│   ├── recovery/         recovery.py
│   └── costs/            cost_records.py, bills.py
├── application/
│   ├── ports/            boundaries.py, git.py, hosting.py, agent_runtime.py,
│   │                     project_commands.py, files.py ?
│   ├── work_items/       work_items.py, opening.py, claims.py, undo.py
│   ├── pipeline/         pipeline_loading.py
│   ├── stages/           stage.py, task.py, stalls.py, machine.py ?, write_paths.py
│   ├── watching/         watcher.py, tick.py, dispatcher.py, board.py
│   ├── handlers/         run.py, run_gate.py, recording.py, comments.py, questions.py,
│   │                     merged.py, closed.py, reject.py, hand_over.py, lookups.py
│   ├── stops/            stops.py
│   ├── recovery/         recovery.py
│   └── costs/            costs.py
├── adapters/
│   ├── git/              git_cli.py
│   ├── hosting/          pygithub_hosting.py, fake_hosting.py
│   ├── agent_runtime/    claude_runtime.py, claude_guard.py, agent_files.py, fake_agent_runtime.py
│   ├── project_commands/ make_commands.py, process.py
│   ├── files/            work_item_markdown.py, pipeline_yaml.py, cost_records_jsonl.py,
│   │                     health_file.py, factory_log.py, validation_faults.py
│   └── clock.py
└── entry/                bill.py, check_story.py, guard.py, watch.py, wiring.py
```

The modules F0008 to F0011 add are placed by the same rule when the story is drafted.

## What the move touches besides the files

- The whole-code searches that name modules by full path: the `ALLOWED` sets in `tests/test_no_journal_reading.py`, the one process module in `tests/test_process_search.py`, and the other search tests.
- `CLAUDE.md`'s one exception for `src/factory/adapters/process.py` (the path only).
- The module lists in `docs/project-guide.md` and `docs/operator-guide.md`.
- `pyproject.toml`'s console scripts point at `factory.entry.*`, which does not move.
- Estimate: one mechanical story, $3 to $5; `make check` catches every broken import.

## Duplicates and dead code (added 2026-10-14, the human's decision)

- Now: `CLAUDE.md` Architecture asks the coder to search for an existing helper before writing one, and the reviewer to count a second copy as a finding.
- In this housekeeping story: run pylint's duplicate-code check (R0801) and vulture once over `src/factory`, and fold their findings (similar blocks, unused functions and classes, such as F0002's four copies of the UTC validator) into the story. Both are run ad hoc (`uvx`), not added as dependencies.
- In v1.1 (this version, the human's word of 2026-10-14, not v2): a project command `make duplicates` that runs both over `src/factory` against a baseline of today's findings, wired as a non-blocking record (`records:` in v1's `factory/stages.yml` on the review stage, and as a report in v1.1's own pipeline definition), whose findings reach the reviewer and the acceptance reviewer. It needs a make target, a `factory/` change made between two stories, and two development dependencies (pylint, vulture), each for the human to grant when it is built.

## Tests of the DTOs' own configuration (added 2026-10-14, the human's decision)

- Kept: every limit tested on both sides (`CLAUDE.md`); from 2026-10-14 the sides of one rule are rows of one parametrized test.
- In this housekeeping story: one test that walks every Pydantic model under `src/factory` and checks `frozen` and `extra="forbid"` where the model declares them, replacing the per-model tests of unknown, wrong-typed and assigned fields that only test Pydantic.

## The project guide split by domain (added 2026-10-14, the human's decision)

- In this housekeeping story: `docs/project-guide.md` becomes `docs/project-guide/` with a `README.md` index (what holds for all code: layers, errors, kill points, test rules) and one file per domain, mirroring the new code tree (work items, pipeline, stages, watching, handlers, stops, recovery, costs, tools). `CLAUDE.md` then says: read the index, then the files of the domains the story touches. The operator guide and the decision log stay single files.
- Earlier, as its own human commit between two stories, if the guide passes about 1,800 lines before F0011 is accepted (the file tool reads 2,000 lines by default); then the docs criteria of the remaining drafts are reworded to the new paths. The session checks its length after each feature acceptance.

- F0011-S0005's document check reads `PROJECT_GUIDE = "docs/project-guide.md"`: the split points it at `docs/project-guide/README.md` and keeps the sections it checks (`Kill points`, the fault-path table) in that index (F0011 pre-check 3).

## The time `make check` takes (added 2026-10-16, from the metrics of v1 building v1.1)

- Measured over 794 agent runs (22.7 h of agent wall time, `session-logs/metrics/README.md`): `make check` inside agent runs is 446 calls, 7.7 h, 34 %, 62 s on average; `make test` 1.1 h, 5 %. Not counted: the factory's own `check` after the doing and docs stages and the session's approval check per story.
- Levers to weigh in this housekeeping story: run the tests in parallel (pytest-xdist, a development dependency for the human to grant); skip a `make check` on a commit whose result is already known (the coder's, the documenter's and the factory's runs on the same commit); let agents run the story's own tests while they work and the full check once at the end; and record the duration of every project command in v1.1's own records.
- Timed on 2026-10-16 with `pytest --durations`: no single test is slow (the slowest take 1 to 2 s, on purpose, to test time limits), so the time is the full suite with coverage, run several times per story, plus the model itself.
- Each target timed once on 2026-10-17 in v1's container (main at a2cde4b, 2,148 tests, 20 cores, warm caches): `lint` 0.1 s, `types` 0.4 s, `layers` 0.2 s, `sast` 2.6 s, `secrets` 22.6 s, `licenses` 0.3 s, `test` 177.4 s. So `test` is 88 % of `make check` and `secrets` 11 %. Without coverage the tests take 148 s of test time on one core (99.8 s in the calls, 48.4 s in the fixtures' setup, mostly real git remotes and clones per test).
- The levers in that order: pytest-xdist over the 20 cores (the 148 s of test time spread out; a development dependency for the human to grant); a session-scoped template remote that each test copies instead of building one (the 48 s of setup); `make secrets` over the files changed against `main` instead of every tracked file (22.6 s). Measure again after each.

## Further findings to weigh (collected 2026-10-16, before the session's context was compacted)

- Ceremony per tool: an ABC, a real class, a fake and DTOs per boundary. Kept where a fake makes tests deterministic (git, hosting, agent runtime, the clock, the health file, the factory log). Fold an interface away only where the duplicate-and-dead-code report shows one with a single implementation that no test swaps; measure, do not guess.
- Test data validity: about ten stories lost a round to fixtures that broke a rule already built (a work item text without `## Journal`, a claim of another stage, a folder git dropped, a constant typed too wide, a request without `question`, a full path compared with a file name, an unchanged push). The rule is a row of `planning/lessons-for-the-skills.md` and in the shipped tester agent; added to `factory-rf`'s own `CLAUDE.md` Tests on 2026-10-16, after F0011-S0001 lost a round to it.
- Agents still wait on background `make` runs (F0010-S0006's documenter used `until … ! pgrep -x make`, which works but breaks the foreground rule). The time per story keeps rising (coder runs of 20 to 30 minutes in three turns): measure where a long agent run waits, from the transcripts in `session-logs/container/`.
- The shared test helpers that exist now (`tests/conftest.py`, `git_support.py`, `crash_support.py`, `acceptance_walk.py`, `shipped_agents.py`, `dockerfile_support.py`, `source_search.py`, `human_clone.py`, `bill_support.py`): move them into one `tests/support/` package with the restructure.
- F0010-S0016's optional criterion for one `GUARD_COMMAND` definition was not placed (pre-check 5, note 8).
- F0011-S0001's review round 2, let through at the cap: `tests/test_kill_points.py::_rerun_seconds` is a second copy of `tests/proof_support.py`'s claim-commit logic (`_claim_commits`, `_state_at`), so the `kill-to-rerun-recorded` check in `violations` is reached by no test; one public `rerun_seconds(result)` helper replaces both. `_opening_text` returns a `WorkItemDocument` and becomes `_opening_document`.
- F0011's acceptance, for this story: `tests/test_fault_path_names.py` is redundant beside the later table tests; `_rerun` calling `rerun`; `_branch_state`; the argv redundancy in `check_documents.main`; `record_property` reaches no report under junit's default `xunit2` family (set `junit_family` if the kill-to-rerun seconds should land in the junit report of the telemetry above). Open for the human: whether the document check joins `make check` or the pipeline definition (F0011 decision 13 keeps it outside).
- v1 past the send-back cap: the human's answer resumes the stage that asked, so "one more round" makes the reviewer send back again and ask again (`factory/src/factory/stage.py`, `_rework`). v1.1's answer to a cap question should be able to grant one more round (or reset the count) explicitly; check what v1.1's own cap does before the end-to-end run.
- F0010's third acceptance: parked draft F0010-S0025 (one default git identity: `DEFAULT_GIT_IDENTITY` in `domain/settings.py` and the literal default of `GitOptions.identity` in `domain/git.py`) folds into this story's duplicates work; the two ways of finding `sudo` likewise; two uncovered lines of `claude_runtime.py` (384, 408-409, F0001 code); a `make mutants` target (needs `mutmut`, the human's dependency call).
- The run record of F0009-S0007's early stages was lost with the corrupt checkout of 2026-10-15; its cost table on #109 undercounts.
- At the end of the build: run `session-logs/refresh.sh` and copy `/work/factory-rf/.git/factory-dispatches.jsonl` and the factory log again into `session-logs/metrics/`.

## Disk space, fixed in v1.1 (the human's word, 2026-10-17)

Drive C: ran full a second time on 2026-10-16 at about 21:45 UTC: Docker's disk image `docker_data.vhdx` had grown to 340 GB while the container used 97 GB, and `docker exec` hung for four hours. Inside the container, `df` showed 860 GB free, because the disk image's virtual size is 1 TB: nothing in the container could see that the host was full. Most of it was the session's own approval checks (one clone of `factory-rf` with its `.venv`, about 470 MB, per story, never removed; fixed on 2026-10-17 by reusing one checkout). Also seen: `/tmp/pytest-of-factory` at 8.4 GB (pytest keeps the last three runs), and 153 directories that the acceptances' and the project guide's `tempfile.mkdtemp()` examples left in `/tmp` (185 MB). In v1.1, built after the housekeeping story:

- A machine stop for low disk space: the preflight and every tick check the free space of the work directory and the state directory against a setting (a default of a few GB), and the factory stops with a reason the health status and the factory log show, instead of hanging on a write.
- The operator guide says what the container cannot see. Docker Desktop's WSL 2 backend has no disk limit (Docker Desktop 4.95: "resource limits are managed by Windows"; `.wslconfig` caps memory, CPU and swap, and its `defaultVhdSize` applies only to new distributions), so inside the container `df` shows the virtual 1 TB and the stop above fires only on a Linux host or a real limit. Under Docker Desktop the host drive is watched from outside, the disk image belongs on a drive with room (Settings, Resources, Advanced, "Disk image location" where offered), and the space comes back with `fstrim -v /mnt/docker-desktop-disk` in the `docker-desktop` distribution followed by `diskpart` `compact vdisk` with Docker stopped (done on 2026-10-17: 340.5 GB to 57.3 GB).
- The factory's own temporary files: every clone, check and walk the factory makes in a temporary directory is removed when it ends, and the examples in the documents and the acceptance demos use `tempfile.TemporaryDirectory()` (or the state directory), not `mkdtemp()` without a removal.

- A watch at the end of every major change (the human's word, 2026-10-17): disk use must not grow without bound. At each feature acceptance and at the start and end of the end-to-end run, record the host drive's free space, the size of Docker's disk image, `docker system df`, and the container's `df` and the size of its `/tmp` and work directory. The acceptance reviewer compares them with the last record and reports a growth that the change does not explain; the end-to-end run passes only if its growth stays within a stated bound (to be set from the first records). Until v1.1 records this itself, the session writes the numbers into the night log at each acceptance.

## Telemetry in v1.1 (the human's word, 2026-10-17)

The human asked whether more telemetry helps; the session measured the split of `make check` once by hand (above) instead of changing every agent's `make check` output, and v1.1 gets the records itself:

- Every project command the factory runs is a record: command, target, commit, duration, exit status. Where the command is `make check`, the record holds each target's duration (the `Makefile` prints `<target>: green (<seconds> s)`), and pytest writes a junit report with a time per test, which the acceptance reviewer reads.
- The agent runtime reads `claude`'s streamed events and records, per run, the seconds spent in the model and in tools (and in which command), next to the cost; the board and the cost table show the split per stage.
- The count of `make check` runs on one commit, so that the lever "skip a check whose result for that commit is known" can be measured.
- The disk record of the watch above.
- Not: a generic tracing system, or sampling `docker stats`.

## A project's own skills (the human's word, 2026-10-17)

Today no agent of v1.1 can load a skill: Claude Code finds a project's `.claude/skills/` (the agent runs in the project's checkout and v1.1 does not turn the project's settings off), but each shipped agent in `claude/agents/` passes its tools to `claude -p` explicitly, and none lists `Skill`. v1 delivered its own rules as skills; F0010-S0017 folded them into the agent files (F0010 decision 36), and no story kept the tool, so a project lost a way v1 had to bring its own know-how. In v1.1, as a small story after the housekeeping story (or in it):

- `Skill` joins the tools of the agents that work on the project (tester, coder, reviewer, documenter; the intake, the smoke tester and the acceptance reviewer to be decided in the story), and `tests/test_claude_files.py` follows.
- Each agent file says that its own rules come first where a project skill contradicts them (for example a skill that runs `make check` in the background).
- `.claude/*` stays a protected path: the project's skills are the human's files, like `CLAUDE.md`, and no stage writes them.
- The operator guide says that a project may bring skills under `.claude/skills/`, that the agents load them where they apply, and that the factory does not check what they say.
- Prove it once: an agent run in a test project with one skill, and the skill's effect seen in the run (the morning observation of the real machine can hold it).

## A project's own agents (the human's word, 2026-10-17)

Today a project's pipeline definition names its roles, their write paths and which role works each stage, but the agent file of a role is always `<agent_home>/agents/<role>.md`, filled from v1.1's `claude/agents/` (`FrontmatterAgentDefinitionReader`). A project of a very different kind cannot bring its own coder in its repository; the operator can only replace the file in the instance's agent home, outside the project's history and lost with the volume. In v1.1, in the same small story as the project's skills:

- For each role the factory reads `factory/agents/<role>.md` from the project's `origin/main` first (like the pipeline definition, so a branch never changes its own agent), and the shipped agent only when the project has none. A project agent replaces the shipped one whole; it does not extend it.
- `factory/agents/*` becomes a protected path: the human's files, which no stage writes.
- The preflight and every tick check a project agent as they check a shipped one (the applied keys, the budget, the tools, the refusals); a faulty file stops with its reason.
- The operator guide says how to replace a role's agent and how to add a role with its own agent; the decision log records "replaces, never extends".
- Proved in a test project: a project agent for `coder` is the text the run gets, and without it the shipped one is.
- Close to v2's archetypes (a kind of project with its own agents and rules); built small in v1.1, revisited there.

## The demo, shipped with v1.1 (the human's word, 2026-10-17)

v1 ships `demo/` (the to-do service: `project/` with its `CLAUDE.md`, `Makefile` with `mutants`, `pyproject.toml` and lock file; `features/` with the three features and eight stories; a `README.md` with the prompt for the session that plays the human). v1.1 ships its own demos, in v1.1's forms and words, one folder per demo, because there will be demos of different project kinds (the human's word, 2026-10-17):

```text
demo/
├── README.md               the index: one line per demo (kind, stack, what it builds,
│                           stories, the run it is the baseline of), and what every demo holds
└── todo-service/           the first: run 4's to-do service (Python, FastAPI, SQLite)
    ├── README.md           what it builds, what it needs, the prompt for the session
    │                       that plays the human, what a run looks like and costs
    ├── project/            the empty project the factory builds into: CLAUDE.md,
    │                       Makefile (check, lint, test, mutants), pyproject.toml, uv.lock,
    │                       factory/pipeline.yml (and later factory/agents/ and
    │                       .claude/skills/ where the kind needs its own)
    └── features/           the features and their stories, in v1.1's work item form
```

The todo service is the input of the todo run (step 3): rewriting run 4's stories by hand lands in `demo/todo-service/`, not in a separate repository. A demo's name is its folder; nothing in the code knows the list. One test in `make check` walks every folder under `demo/`: it requires the three parts, runs v1.1's own story check over its `features/` and loads its `project/factory/pipeline.yml`, so every demo stays valid as v1.1 changes, and a new demo is checked from the day it is added. A later demo of another kind (a Spring Boot service, a CLI, a library) proves the kind's own agents and skills of the section below.

## Renaming the repositories (the human's plan, 2026-10-17)

The human will rename `pkrahmer/factory` to `factory-v1` and `factory-rf` to `factory`. Searched on 2026-10-17:

- The code never names `factory-rf` (the package is `factory`; the `rf"…"` hits are Python raw f-strings). Four lines of text do: the titles of `README.md` and `CLAUDE.md`, the project guide's first sentence, and one sentence of `docs/decisions.md`. Two name v1 as `pkrahmer/factory` and become `factory-v1`: `CLAUDE.md`'s first sentence and the project guide's "The texts come from v1 (pkrahmer/factory at `f8bc9d2`)". The template's "Built by the factory (github.com/pkrahmer/factory)" (and `tests/test_claude_files.py::TEMPLATE_RULES_LINES`) stays right after the rename. History (`factory/features/`, `planning/`, `docs/runs/`) keeps its names.
- Do it after v1's last story on this repository, as one human commit; GitHub's redirect from the old name of `pkrahmer/factory` ends once `factory-rf` takes that name, so every clone's remote, v1's `REPOS` setting and v1.1's `FACTORY_REPOSITORY_URL` are set again by hand.
- Before the first start of v1.1 (step 2), and independent of the rename: v1.1's `image/compose.yml` says `name: factory`, with the service `factory` and the volumes `work` and `claude-home`; v1's `compose.yml` in the folder `factory` has the same project name, service and volume names. `docker compose -f image/compose.yml up` would replace v1's running container and mount v1's `factory_work` and `factory_claude-home` volumes (v1's checkout and v1's own `claude` login) into v1.1. Fix: v1.1's project name per instance, `name: factory-${FACTORY_INSTANCE:?…}`, so each instance gets its own container and volumes, and a second instance on one machine cannot collide either; renaming the folder `factory` to `factory-v1` also changes v1's project name and so its volumes, unless v1's compose file gets `name: factory` first.

## v1.1 builds itself (the human's word, 2026-10-17)

Once v1.1 has run on the real machine and passed a short smoke run on the todo demo (its first story), v1.1 takes over `factory-rf`; the full todo run comes at the very end (the human's word, 2026-10-17) and builds its own fixes and extensions; the rename waits until a few self-built stories have gone through cleanly, and v1 stays the fallback until then.

- Safe enough: the container runs a built image, so what v1.1 merges takes effect only when the human builds a new image after an accepted story; the previous image is the way back, and v1 can still build a fix that v1.1 cannot.
- Needs, in order: the compose project name per instance (v1 and v1.1 side by side); the first start and the smoke run passed; the handover of `factory-rf` as one human commit while no v1 story is in progress: v1.1's own pipeline definition and forms replace `factory/stages.yml`, `TICKET.md` and `FEATURE.md`, `CLAUDE.md`'s vocabulary rule turns to v1.1's words, and v1's eleven features stay as history where v1.1 does not read them (decision 008: v1.1 reads no v1 work item, so none may be left in progress).
- The first self-built story is small: a project's own skills and agents. The restructure can follow as the strongest test, v1.1 moving its own code under its own `make check`.
- After each new image of a self-built change to the pipeline itself (the stage rules, the claim, recovery), a short smoke run on the todo demo before v1.1 takes its next own story.
- The order above changes accordingly: steps 1 to 3 with v1; then the handover; steps 4 and 5 built by v1.1; the rename last.

## For the human, outside the build (collected 2026-10-16)

- The machine: drive C: ran full on 2026-10-15 and again on 2026-10-16 (the root cause of three Docker hangs and the corrupt checkout). The disk image `docker_data.vhdx` is 340 GB on C: while Docker uses about 50 GB (`docker system df` on 2026-10-17): compact it (quit Docker Desktop, `wsl --shutdown`, then in an administrator PowerShell `Optimize-VHD -Path $env:LOCALAPPDATA\Docker\wsl\disk\docker_data.vhdx -Mode Full`), set a virtual disk limit, and move it to D: (Settings → Resources → Advanced). Update Docker Desktop (4.38.0) and WSL (`wsl --update`). Windows Update's active hours or a pause while a run goes; Docker Desktop's "Start when you sign in".
- Leftovers in v1's container, to delete by hand: `/work/factory-rf.corrupt-2026-10-15` (its run record is copied), `/work/hatch-*`, `/work/dur-*`, `/tmp/fc-*`, `/tmp/ap-*`, `/tmp/approve-*`; on the host, the approval clones in the user's temp folder (`approve-*`).
- Parked drafts: F0003-S0011 (an unreadable YAML fault on one log line), F0008-S0007 (the defensive callers of `require_state`), F0010-S0025 (one default git identity, folded into the housekeeping story).
- Decisions the session took for the human, to confirm: F0008 decision 19 (stale-branch cleanup also for `done/`), F0009 decision 22 group 3 (the board-reader test), F0010 decisions 37 and 38 (the `SETTINGS` lists, the `Step` field, S0024's replaced refusal test), F0011 decision 19 (S0004 changes F0006's reader for a duplicate id), F0010-S0022's default (a timed-out run with a `sudo:` warning is an `AgentRuntimeError`).
- Open: F0010 decision 30 (the kill of an agent run under `sudo` is not enforced) and F0010's morning observations on the real machine (the image build, `sudo`, the second user, the token mount): the first real run of v1.1.
- Old items: the scratch repository `pkrahmer/factory-night-scratch` and the branch `ccr-cf8b451b-yugt27` of `factory-rf`.
