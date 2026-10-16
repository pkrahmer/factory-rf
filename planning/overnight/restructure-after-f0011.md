# Grouping the modules by domain within each layer (after F0011)

Decided by the human on 2026-10-14, in the session's discussion of the package tree. Built as one housekeeping story after F0011 is accepted, not before: F0008 to F0011's drafts name exact module paths, and a move in the middle of them would break those names.

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

## Further findings to weigh (collected 2026-10-16, before the session's context was compacted)

- Ceremony per tool: an ABC, a real class, a fake and DTOs per boundary. Kept where a fake makes tests deterministic (git, hosting, agent runtime, the clock, the health file, the factory log). Fold an interface away only where the duplicate-and-dead-code report shows one with a single implementation that no test swaps; measure, do not guess.
- Test data validity: about ten stories lost a round to fixtures that broke a rule already built (a work item text without `## Journal`, a claim of another stage, a folder git dropped, a constant typed too wide, a request without `question`, a full path compared with a file name, an unchanged push). The rule is a row of `planning/lessons-for-the-skills.md` and in the shipped tester agent; add it to `factory-rf`'s own `CLAUDE.md` Tests too.
- Agents still wait on background `make` runs (F0010-S0006's documenter used `until … ! pgrep -x make`, which works but breaks the foreground rule). The time per story keeps rising (coder runs of 20 to 30 minutes in three turns): measure where a long agent run waits, from the transcripts in `session-logs/container/`.
- The shared test helpers that exist now (`tests/conftest.py`, `git_support.py`, `crash_support.py`, `acceptance_walk.py`, `shipped_agents.py`, `dockerfile_support.py`, `source_search.py`, `human_clone.py`, `bill_support.py`): move them into one `tests/support/` package with the restructure.
- F0010-S0016's optional criterion for one `GUARD_COMMAND` definition was not placed (pre-check 5, note 8).
- The run record of F0009-S0007's early stages was lost with the corrupt checkout of 2026-10-15; its cost table on #109 undercounts.
- At the end of the build: run `session-logs/refresh.sh` and copy `/work/factory-rf/.git/factory-dispatches.jsonl` and the factory log again into `session-logs/metrics/`.

## For the human, outside the build (collected 2026-10-16)

- The machine: drive C: ran full on 2026-10-15 (the root cause of two Docker hangs and the corrupt checkout); move Docker Desktop's disk image to D: (Settings → Resources → Advanced). Update Docker Desktop (4.38.0) and WSL (`wsl --update`). Windows Update's active hours or a pause while a run goes; Docker Desktop's "Start when you sign in".
- Leftovers in v1's container, to delete by hand: `/work/factory-rf.corrupt-2026-10-15` (its run record is copied), `/work/hatch-*`, `/work/dur-*`, `/tmp/fc-*`, `/tmp/ap-*`, `/tmp/approve-*`; on the host, the approval clones in the user's temp folder (`approve-*`).
- Parked drafts: F0003-S0011 (an unreadable YAML fault on one log line), F0008-S0007 (the defensive callers of `require_state`).
- Decisions the session took for the human, to confirm: F0008 decision 19 (stale-branch cleanup also for `done/`), F0009 decision 22 group 3 (the board-reader test), F0010 decision 37 (the `SETTINGS` lists and the `Step` field), F0011 decision 19 (S0004 changes F0006's reader for a duplicate id), F0010-S0022's default (a timed-out run with a `sudo:` warning is an `AgentRuntimeError`).
- Open: F0010 decision 30 (the kill of an agent run under `sudo` is not enforced) and F0010's morning observations on the real machine (the image build, `sudo`, the second user, the token mount): the first real run of v1.1.
- Old items: the scratch repository `pkrahmer/factory-night-scratch` and the branch `ccr-cf8b451b-yugt27` of `factory-rf`.
