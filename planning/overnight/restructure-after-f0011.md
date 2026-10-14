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
- For v2: a project command that runs both, wired as a pipeline report (recorded, never blocking) whose findings reach the reviewer and the acceptance reviewer. It needs a new make target and two development dependencies, both for the human to grant then.
