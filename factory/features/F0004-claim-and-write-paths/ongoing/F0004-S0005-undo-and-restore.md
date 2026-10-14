---
stage: tests
pr: 56
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# Undo and restore after an agent run

## Assignment (as of log entry 1)

Build the undo that follows an agent run (kept thing 5: the guard refuses, the undo reverts). `UndoService.undo` takes the stage start (S0001) and, with the guard's own settings from `WritePathService.at` (S0003), puts the work tree back wherever the agent left a mark it may not leave: every path changed since the stage-start commit that is outside the write paths, or protected, is checked out from that commit or deleted if it did not exist there; every other work item in progress is undone whatever the write paths say; and the work item's own state and journal are restored from the stage-start commit while the agent's edits to its sections stay. A work item the agent deleted or broke is restored whole. Because the write paths come from the stage-start commit, an agent that rewrites the pipeline definition widens nothing (WE2.1), and an invalid rewrite does not make the undo raise (WE2.2); the guard (S0004) and the undo read the same source (WE2.3). Covers WE2.1, WE2.2, WE2.3; keeps kept things 5 and 17. When the undo runs (after an agent run, after a stall, whatever ended the run) and what is written into the entry about it are F0005's. Writes to ignored paths and outside the checkout are not seen by the undo and stay as they are (left for v2, handover section 8). Morning observation: none.

## Interface

`src/factory/application/undo.py`

```python
class UndoReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    reverted: list[str]  # paths put back to their content at the stage-start commit, ascending
    deleted: list[str]  # paths that did not exist at the stage-start commit and were removed, ascending
    restored_work_item: bool  # the work item's state or journal, or the whole file, was put back

class UndoService:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def undo(self, stage_start: StageStart, work_item_path: str) -> UndoReport: ...
```

`StageStart` is the DTO of `factory.application.claims`; `work_item_path` is the work item's repository-relative POSIX path. The undo uses `WritePathService.at`, `refusal` (S0003), `Git.changed_paths`, `Git.show_file` and `Git.revert_paths`, `restore_state_and_journal` and the work item reader and writer (F0001, F0002).

Rules:

- `undo` first gets `settings = WritePathService(boundaries).at(stage_start, work_item_path)`; it never reads the pipeline definition from the work tree.
- Then the baseline, before any path is changed: `boundaries.git.show_file(stage_start.commit, work_item_path)` parsed with `boundaries.work_item_reader.parse`. A baseline that is absent or unreadable raises `WorkItemFormatError` naming the path, and the work tree is then as the agent left it.
- A path is refused when `refusal(path, settings)` is not `None`, or when it lies directly in an `in-progress` folder of a feature (`factory/features/<directory>/in-progress/<file>`, any file name, tested on the string with `factory.domain.paths.FEATURES_DIRECTORY` and the segment `in-progress`, not with `folder_of`) and is not `work_item_path`. The second rule undoes every other work item in progress, every cost-record file (`.costs.jsonl`) and any other file in an `in-progress` folder, whatever the write paths say, the own work item's cost-record file (`cost_records_path(work_item_path)`) with them. `folder_of` cannot serve here: it is `None` for a cost-record file and for any file that is no work item. The guard does not know this second rule.
- The candidates are the paths of `boundaries.git.changed_paths(stage_start.commit)`: commits since the stage-start commit, the work tree and untracked files, ignored paths excluded. Each refused path whose change is `added` is listed in `deleted`, each other refused path in `reverted`, and `boundaries.git.revert_paths(stage_start.commit, <the refused paths>)` puts them back or removes them. Both lists are sorted ascending without repeats.
- Then the work item's own file, after the refused paths are put back. The current file is read with `boundaries.work_item_reader.read(boundaries.checkout / work_item_path)`. When it is readable, `restore_state_and_journal(current, baseline)` is written back with `boundaries.work_item_writer` if it differs from `current`; the agent's edits to the other sections stay. When it is missing or unreadable (`WorkItemFormatError`), the file is checked out whole from the stage-start commit with `revert_paths`. `restored_work_item` is true exactly when one of these two writes happened; it is false when the file already equalled the restore. A work item restored whole in this step is not listed in `reverted` (it was not refused); `restored_work_item` reports it. A work item that was refused and put back with the other refused paths is listed in `reverted` and does not set `restored_work_item`.
- The undo makes no commit and no push. A commit the agent made itself stays in the history; only the work tree is put back.

Tests: `tests/application/test_undo.py`, with the shared fixtures `remote`, `checkout`, `human`, `clock` and `boundaries`. Each test pushes a pipeline definition whose roles give the write paths it needs (`human.push_file("main", "factory/pipeline.yml", text)`), calls `checkout.fetch()` and `checkout.checkout(branch_name(id), start_point="origin/main")`, writes the work item with `initial_state(stage)`, journal entry 1 and a `## Journal` section at `factory/features/F0001-example/in-progress/F0001-S0001-first.md` (the fixture's backlog story has neither state nor journal section, so `claim` would raise `WorkItemFormatError` on it) and any other work item the test needs present at the stage-start commit, claims the stage with `ClaimService` (S0001), lets a "fake agent" write into `boundaries.checkout`, and calls `undo`. A helper in the test module does the setup. Criterion 18 builds the model through a variable typed `type[BaseModel]` and assigns with `setattr(instance, field, value)`, the field's name in a variable, as `CLAUDE.md` asks under *Tests*.

## Acceptance criteria

1. A tracked file outside the write paths that the agent modified in the work tree is back to its content at the stage-start commit and is listed in `reverted`.
2. A new untracked file outside the write paths is removed from the work tree and listed in `deleted`, not in `reverted`.
3. A tracked file outside the write paths that the agent deleted is restored and listed in `reverted`.
4. A file outside the write paths that the agent changed in a commit of its own has the content of the stage-start commit in the work tree afterwards and is listed in `reverted`; the agent's commit is still in the log, and `undo` made no commit (`HEAD` is the same before and after).
5. Files inside the write paths, one modified and one new, are untouched and are listed in neither `reverted` nor `deleted`.
6. A protected path is reverted although a write path matches it: with a role whose write paths are `["*"]`, a changed `factory/story-form.md` is put back (listed in `reverted`), a new `pyproject.toml` is removed (listed in `deleted`), and a new `src/a.py` stays.
7. Everything else in an `in-progress` folder is undone whatever the write paths say: with a role whose write paths are `["*"]`, a changed other work item present at the stage-start commit (`F0001-S0002-second.md`) is reverted, a new cost-record file beside the own work item (`cost_records_path(work_item_path)`) is deleted, a new cost-record file of another work item in progress is deleted, a new `in-progress/notes.txt` is deleted, and the own work item keeps its section edit.
8. When the agent changed the work item's own state (`attempts` raised) and its journal, `undo` puts both back from the stage-start commit, keeps the agent's edit of another section, and reports `restored_work_item` true.
9. When the agent edited only a section of its own work item, the file is as the agent left it and `restored_work_item` is false.
10. When the agent deleted its own work item and the role may write it, the file is back with exactly its text at the stage-start commit, `restored_work_item` is true, and the path is in neither `reverted` nor `deleted`.
11. When the agent left its own work item with front matter that cannot be read, the file is back with exactly its text at the stage-start commit, `restored_work_item` is true, the path is in neither `reverted` nor `deleted`, and `undo` raises nothing.
12. When the role may not write the work item (the fixture's `coder`) and the agent edited it, the whole file is put back, it is listed in `reverted`, the edit is gone, and `restored_work_item` is false.
13. When the agent rewrites `factory/pipeline.yml` in the work tree so that its role may write `*`, and writes `docs/extra.md`, the file `docs/extra.md` is still deleted and the pipeline definition is back to its text at the stage-start commit (WE2.1).
14. When the agent replaces `factory/pipeline.yml` with text that is not valid YAML and also writes `docs/extra.md`, `undo` raises nothing, the pipeline definition is back to its text at the stage-start commit, and `docs/extra.md` is deleted (WE2.2).
15. For the paths `src/a.py`, `docs/a.md`, `tests/t.py`, `pyproject.toml` and `factory/pipeline.yml` written by the agent in the coder's stage, the guard (`judge` with `WritePathService.at`'s settings) refuses exactly those that `undo` reverts or deletes (WE2.3).
16. `reverted` and `deleted` are sorted ascending without repeats, and a second `undo` right after the first returns empty lists and `restored_work_item` false.
17. `undo` raises `WorkItemFormatError` naming the path when the stage-start commit does not contain the work item, and when the work item at the stage-start commit has front matter that cannot be read; in both cases a file outside the write paths that the agent changed is still as the agent left it, because the baseline is read before any path is changed.
18. `UndoReport` is frozen and forbids unknown fields: assigning to `reverted` raises `ValidationError`, and building it with an unknown field `extra` raises `ValidationError`.
19. make check stays green.
20. docs: `docs/project-guide.md` explains the undo (what it undoes and why from the stage-start commit, that other work items in progress are undone whatever the write paths say, that the work item's state and journal are restored and a deleted or broken work item is restored whole, that it makes no commit, and the limits: ignored paths, writes outside the checkout, an agent's own commit stays in the history); `docs/decisions.md` records that the undo and the guard read the write paths from the stage-start commit (WE2) and that a work item the agent breaks is restored whole.

## Demo

```bash
uv run python - <<'EOF'
import os, subprocess, tempfile
from datetime import UTC, datetime
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.clock import ManualClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.undo import UndoService
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, initial_state

for name in ('GIT_AUTHOR_NAME', 'GIT_COMMITTER_NAME'):
    os.environ[name] = 'demo'
for name in ('GIT_AUTHOR_EMAIL', 'GIT_COMMITTER_EMAIL'):
    os.environ[name] = 'demo@example.com'

PIPELINE = """contract: "1.0"
stages:
  coder: {role: coder, next: [done]}
  done: {}
roles:
  coder: {write_paths: ["src/*", "{work_item}"]}
"""
BRANCH = 'work-item/F0004-S0001'
PATH = 'factory/features/F0004-demo/in-progress/F0004-S0001-demo.md'
BODY = '# Demo story\n\n## Description\n\nOriginal.\n\n## Journal\n\n1. 2026-10-12 human: created.\n'

root = Path(tempfile.mkdtemp())
remote, seed, work = root / 'remote.git', root / 'seed', root / 'work'

def sh(*args, cwd=None):
    subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True)

state = initial_state('coder').model_copy(update={'journal': [JournalRecord(number=1, speaker='human', kind='created')]})
sh('init', '--bare', '-b', 'main', str(remote))
sh('clone', str(remote), str(seed))
(seed / 'factory').mkdir()
(seed / 'factory' / 'pipeline.yml').write_text(PIPELINE)
(seed / PATH).parent.mkdir(parents=True)
(seed / PATH).write_text(FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body=BODY)))
sh('add', '-A', cwd=seed)
sh('commit', '-m', 'seed', cwd=seed)
sh('push', 'origin', 'HEAD:main', cwd=seed)
sh('push', 'origin', 'HEAD:refs/heads/' + BRANCH, cwd=seed)

clock = ManualClock(datetime(2026, 10, 12, tzinfo=UTC))
git = GitCli(work)
git.clone(str(remote))
git.checkout(BRANCH, start_point='origin/' + BRANCH)
b = Boundaries(git=git, hosting=FakeHostingService(), agent_runtime=FakeAgentRuntime(), project_commands=MakeProjectCommands(work), work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(), cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(), clock=clock, log=TimestampedFactoryLog(root / 'factory.log', clock), health=JsonHealthStatusFile(root / 'health.json'), pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(root / 'claude'), checkout=work)
definition = b.pipeline_reader.parse(PIPELINE)
start = ClaimService(b, 'factory-1', definition).claim(BRANCH, PATH, b.work_item_reader.read(work / PATH), 'coder')

(work / 'src').mkdir()
(work / 'src' / 'a.py').write_text('x = 1\n')
(work / 'docs').mkdir()
(work / 'docs' / 'extra.md').write_text('outside\n')
(work / 'factory' / 'pipeline.yml').write_text(PIPELINE.replace('src/*', '*'))
item = work / PATH
item.write_text(item.read_text().replace('attempts: 0', 'attempts: 7').replace('Original.', 'Changed by the agent.'))

report = UndoService(b).undo(start, PATH)
print(report.reverted, report.deleted, report.restored_work_item)
print((work / 'factory' / 'pipeline.yml').read_text() == PIPELINE)
print((work / 'src' / 'a.py').exists(), (work / 'docs' / 'extra.md').exists())
print(b.work_item_reader.read(item).state.attempts, 'Changed by the agent.' in item.read_text())
print(UndoService(b).undo(start, PATH))
EOF
```
Expect: five lines. `['factory/pipeline.yml'] ['docs/extra.md'] True`; `True` (the widened pipeline definition is gone); `True False` (`src/a.py` stays, `docs/extra.md` is deleted although the widened definition would have allowed it); `0 True` (the raised `attempts` is back to 0 and the agent's section edit stays); `reverted=[] deleted=[] restored_work_item=False` (a second undo finds nothing).

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `src/factory/application/undo.py` names `UndoReport` (frozen, extra forbidden) and `UndoService.__init__`/`undo` with signatures. It names the collaborators it uses (`WritePathService.at`, `refusal`, `Git.changed_paths`/`show_file`/`revert_paths`, `restore_state_and_journal`, the work item reader and writer). The rules give the order (settings, baseline, refused paths, own file) and the exact in-progress path test.
   - Criteria: every behaviour stated in the Interface has a criterion. Reverted/deleted lists are 1–5 and 16. Protected paths are 6. In-progress rules are 7. State and journal restore are 8–9. Deleted or broken work item is 10–11. A work item the role may not write is 12. Pipeline rewrites are 13–15. Baseline errors are 17. The frozen/extra model is 18. Each rule has its failing side: paths inside the write paths stay (5), a section-only edit means no restore (9), and a baseline error leaves the work tree untouched (17). Criterion 17 covers two cases (missing and unreadable baseline) and criterion 16 two assertions; both are fine as parametrized or paired tests, not a decision for the coder.
   - Demo: the script is runnable with the named adapters. Each of the five output lines in `Expect:` can be compared against the output.
   - Architecture: the use case sits in `factory.application` and reaches git only through the `Git` interface and the file formats through reader/writer interfaces. It takes `Boundaries` and has no concrete tool.
   - Scope: it matches the feature's undo and restore bullet (WE2.1–WE2.3) and decisions 13–15. When the undo runs and the note in the entry are left to F0005, as the feature's Out of scope says.
3. tester: wrote `tests/application/test_undo.py` (new file, the only file created). One helper, `_start`, does the setup. It pushes a pipeline definition (the fixture's `PIPELINE_YAML`, with the `intake` role's write paths replaced when a test needs other ones), checks out the work item's branch from `origin/main`, and commits `docs/guide.md`, `src/kept.py` and `F0001-S0002-second.md` together with the work item (`initial_state(stage)`, journal entry 1, a `## Journal` section). It then claims with `ClaimService`.
   - criterion 1: tests/application/test_undo.py::test_a_modified_tracked_file_outside_the_write_paths_is_reverted
   - criterion 2: tests/application/test_undo.py::test_a_new_untracked_file_outside_the_write_paths_is_deleted
   - criterion 3: tests/application/test_undo.py::test_a_deleted_tracked_file_outside_the_write_paths_is_restored
   - criterion 4: tests/application/test_undo.py::test_a_file_changed_in_the_agents_own_commit_is_reverted_without_a_new_commit
   - criterion 5: tests/application/test_undo.py::test_files_inside_the_write_paths_are_left_as_the_agent_wrote_them
   - criterion 6: tests/application/test_undo.py::test_protected_paths_are_undone_although_a_write_path_matches_them
   - criterion 7: tests/application/test_undo.py::test_everything_else_in_an_in_progress_folder_is_undone_whatever_the_write_paths_say
   - criterion 8: tests/application/test_undo.py::test_the_work_items_state_and_journal_are_restored_and_its_section_edit_kept
   - criterion 9: tests/application/test_undo.py::test_a_work_item_with_only_a_section_edit_is_left_as_the_agent_left_it
   - criterion 10: tests/application/test_undo.py::test_a_work_item_the_agent_deleted_is_restored_whole
   - criterion 11: tests/application/test_undo.py::test_a_work_item_the_agent_broke_is_restored_whole
   - criterion 12: tests/application/test_undo.py::test_a_work_item_the_role_may_not_write_is_reverted_whole (stage `doing`, the fixture's coder)
   - criterion 13: tests/application/test_undo.py::test_a_widened_pipeline_definition_in_the_work_tree_widens_nothing
   - criterion 14: tests/application/test_undo.py::test_an_invalid_pipeline_definition_in_the_work_tree_does_not_stop_the_undo
   - criterion 15: tests/application/test_undo.py::test_the_guard_refuses_exactly_what_the_undo_puts_back (`judge` from `factory.adapters.claude_guard` on a Write payload, with `WritePathService.at`'s settings)
   - criterion 16: tests/application/test_undo.py::test_the_lists_ascend_without_repeats_and_a_second_undo_finds_nothing
   - criterion 17: tests/application/test_undo.py::test_a_missing_or_unreadable_baseline_raises_before_any_path_is_changed. It is parametrized over two baselines. The missing one is a `StageStart` on `origin/main`, which does not contain the work item. The unreadable one is a commit whose work item has front matter that is not valid YAML.
   - criterion 18: tests/application/test_undo.py::test_the_undo_report_is_frozen and ::test_the_undo_report_forbids_unknown_fields
   - criteria 19 and 20 are not tests.

   Some assertions are exact lists, because each test's setup leaves no other changed path: `reverted == [GUIDE]` in criteria 1, 3 and 4, and `reverted == [PATH]` in criterion 12. Criterion 16 expects `reverted == [docs/guide.md, factory/pipeline.yml, src/kept.py]` and `deleted == [a.txt, docs/b.md, tests/z.py]`; in that test the work item's `attempts` is raised, so `restored_work_item` is true on the first undo. The second undo must equal `UndoReport(reverted=[], deleted=[], restored_work_item=False)`.

   `make test`: a collection error, `ModuleNotFoundError: No module named 'factory.application.undo'`, the expected red. `make lint` is green. The type check was not run, as this stage skips it. No criterion needed interpretation.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: implemented `src/factory/application/undo.py` (commit 4cfd5a1). It holds `UndoReport` and `UndoService.undo`, following the Interface's order. First it gets the settings from `WritePathService.at`. Then it reads the baseline before any path changes; an absent or unreadable baseline raises `WorkItemFormatError` with the path. Then it reverts the refused paths from `changed_paths` with one `revert_paths` call; a path is refused by `refusal`, or because it sits directly in `factory/features/<dir>/in-progress/` and is not the own work item, checked on the string. Last it restores the own work item. A readable work item gets `restore_state_and_journal` and is written only if it changed. A missing or unreadable one is checked out whole. `make lint`, `make types` and `make layers` are green. The ticket's Demo prints exactly the five expected lines.

   `make test` is red because of the test file, not the code. 15 of the 19 tests in `tests/application/test_undo.py` fail in the setup helper `_start` with `NothingToCommit: nothing to commit`, raised from `human.push_file("main", PIPELINE_FILE, text)`. When a test passes no `write_paths`, `_pipeline(None)` returns `PIPELINE_YAML`. That is the same text the `remote` fixture already has on `main` (`REMOTE_FILES` in `tests/git_support.py`). So the human's commit is empty, and `GitCli.commit` correctly refuses it. Only the tests that pass `write_paths` (criteria 5, 6, 7) and the two `UndoReport` model tests get past setup, and those pass. I did not touch the test, not even temporarily (R9).

   Options:
   (a) In `_start`, call `human.push_file` only when `text != PIPELINE_YAML` (still followed by `git.fetch()`). This changes only the test module and is my recommendation.
   (b) Make `HumanClone.push_file` skip the commit and push when nothing changed. This changes a shared test helper that other tests rely on.
   (c) Always push a definition that differs, e.g. by adding a trailing comment.

   With (a), the ticket goes back with `tests` and the tester makes that one-line change. I could not run the tests against my code beyond the four that already pass, but the Demo covers the main path (refused pipeline rewrite, deleted outside file, kept `src/` file, restored state with the section edit kept, idempotent second undo). Refactor step not yet done; it follows once `make check` can be green.
5. human (pull request comment, 2026-10-14): (a): in `_start`, call `human.push_file` only when `text != PIPELINE_YAML` (still followed by `git.fetch()`). Leave `HumanClone.push_file` as it is. End with `tests` and name exactly that change.
6. coder: the human answered (entry 5) with option (a), so this goes back to the tester for a change to the test module only. In `tests/application/test_undo.py`, the helper `_start` should call `human.push_file("main", PIPELINE_FILE, text)` only when `text != PIPELINE_YAML`, and still call `git.fetch()` afterwards. `HumanClone.push_file` stays as it is.

   Why: when a test passes no `write_paths`, the helper pushes the text that `main` already has. The commit is then empty and `GitCli.commit` raises `NothingToCommit`, which makes 15 of the 19 tests fail during setup.

   The implementation in `src/factory/application/undo.py` (commit 4cfd5a1) is unchanged. I made no code changes in this run, and the refactor step comes once `make check` can go green with the corrected test.
