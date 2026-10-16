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

## The time `make check` takes (added 2026-10-16, from the metrics of v1 building v1.1)

- Measured over 794 agent runs (22.7 h of agent wall time, `session-logs/metrics/README.md`): `make check` inside agent runs is 446 calls, 7.7 h, 34 %, 62 s on average; `make test` 1.1 h, 5 %. Not counted: the factory's own `check` after the doing and docs stages and the session's approval check per story.
- Levers to weigh in this housekeeping story: run the tests in parallel (pytest-xdist, a development dependency for the human to grant); skip a `make check` on a commit whose result is already known (the coder's, the documenter's and the factory's runs on the same commit); let agents run the story's own tests while they work and the full check once at the end; and record the duration of every project command in v1.1's own records.
