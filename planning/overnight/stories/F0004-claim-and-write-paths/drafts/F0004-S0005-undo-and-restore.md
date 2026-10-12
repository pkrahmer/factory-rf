# Undo and restore after an agent run

## Assignment (as of log entry 1)

Build the undo that follows an agent run (kept thing 5: the guard refuses, the undo reverts). `UndoService.undo` takes the stage start (S0001) and, with the guard's own settings from `WritePathService.at` (S0003), puts the work tree back wherever the agent left a mark it may not leave: every path changed since the stage-start commit that is outside the write paths, or protected, is checked out from that commit or deleted if it did not exist there; every other work item in progress is undone whatever the write paths say; and the work item's own state and journal are restored from the stage-start commit while the agent's edits to its sections stay. A work item the agent deleted or broke is restored whole. Because the write paths come from the stage-start commit, an agent that rewrites the pipeline definition widens nothing (WE2.1), and an invalid rewrite does not make the undo raise (WE2.2); the guard (S0004) and the undo read the same source (WE2.3). Covers WE2.1, WE2.2, WE2.3; keeps kept things 5 and 17. When the undo runs (after an agent run, after a stall, whatever ended the run) and what is written into the entry about it are F0005's. Writes to ignored paths and outside the checkout are not seen by the undo and stay as they are (left for v2, handover section 8). Morning observation: none.

## Interface

`src/factory/application/undo.py`

```python
class UndoReport(BaseModel):
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
- A path is refused when `refusal(path, settings)` is not `None`, or when it lies in an `in-progress` folder (`factory.domain.paths.folder_of(path) == "in-progress"`) and is not `work_item_path`. The second rule undoes every other work item in progress, and the work item's own cost-record file, whatever the write paths say. The guard does not know this second rule.
- The candidates are the paths of `boundaries.git.changed_paths(stage_start.commit)`: commits since the stage-start commit, the work tree and untracked files, ignored paths excluded. Each refused path whose change is `added` is listed in `deleted`, each other refused path in `reverted`, and one call `boundaries.git.revert_paths(stage_start.commit, <all refused paths>)` puts them back or removes them. With no refused path the call is not made. Both lists are sorted ascending without repeats.
- Then the work item's own file. The baseline is `boundaries.git.show_file(stage_start.commit, work_item_path)` parsed with `boundaries.work_item_reader.parse`; a baseline that is absent or unreadable raises `WorkItemFormatError` naming the path. The current file is read with `boundaries.work_item_reader.read(boundaries.checkout / work_item_path)`. When it is readable, `restore_state_and_journal(current, baseline)` is written back with `boundaries.work_item_writer` if it differs from `current`; the agent's edits to the other sections stay. When it is missing or unreadable (`WorkItemFormatError`), the file is checked out whole from the stage-start commit with `revert_paths`. `restored_work_item` is true exactly when one of these two writes happened; it is false when the file already equalled the restore.
- The undo makes no commit and no push. A commit the agent made itself stays in the history; only the work tree is put back.

Tests: `tests/application/test_undo.py`, with the shared fixtures `remote`, `checkout`, `human`, `clock` and `boundaries`. Each test pushes a pipeline definition whose roles give the write paths it needs (`human.push_file("main", "factory/pipeline.yml", text)`), claims a stage with `ClaimService` (S0001), lets a "fake agent" write into `boundaries.checkout`, and calls `undo`.

## Acceptance criteria

1. A tracked file outside the write paths that the agent modified in the work tree is back to its content at the stage-start commit and is listed in `reverted`.
2. A new untracked file outside the write paths is removed from the work tree and listed in `deleted`, not in `reverted`.
3. A tracked file outside the write paths that the agent deleted is restored and listed in `reverted`.
4. A file outside the write paths that the agent changed in a commit of its own has the content of the stage-start commit in the work tree afterwards and is listed in `reverted`; the agent's commit is still in the log, and `undo` made no commit (`HEAD` is the same before and after).
5. Files inside the write paths, one modified and one new, are untouched and are listed in neither `reverted` nor `deleted`.
6. A protected path is reverted although a write path matches it: with a role whose write paths are `["*"]`, a changed `factory/story-form.md` is put back (listed in `reverted`), a new `pyproject.toml` is removed (listed in `deleted`), and a new `src/a.py` stays.
7. Every other work item in progress is undone whatever the write paths say: with a role whose write paths are `["factory/features/*/in-progress/*.md"]`, a changed other work item is reverted, a new `.costs.jsonl` file beside the work item (its cost-record file) is deleted, and the work item's own file keeps its section edit.
8. When the agent changed the work item's own state (`attempts` raised) and its journal, `undo` puts both back from the stage-start commit, keeps the agent's edit of another section, and reports `restored_work_item` true.
9. When the agent edited only a section of its own work item, the file is as the agent left it and `restored_work_item` is false.
10. When the agent deleted its own work item and the role may write it, the file is back with exactly its text at the stage-start commit and `restored_work_item` is true.
11. When the agent left its own work item with front matter that cannot be read, the file is back with exactly its text at the stage-start commit, `restored_work_item` is true, and `undo` raises nothing.
12. When the role may not write the work item (the fixture's `coder`) and the agent edited it, the whole file is put back, it is listed in `reverted`, the edit is gone, and `restored_work_item` is false.
13. When the agent rewrites `factory/pipeline.yml` in the work tree so that its role may write `*`, and writes `docs/extra.md`, the file `docs/extra.md` is still deleted and the pipeline definition is back to its text at the stage-start commit (WE2.1).
14. When the agent replaces `factory/pipeline.yml` with text that is not valid YAML and also writes `docs/extra.md`, `undo` raises nothing, the pipeline definition is back to its text at the stage-start commit, and `docs/extra.md` is deleted (WE2.2).
15. For the paths `src/a.py`, `docs/a.md`, `tests/t.py`, `pyproject.toml` and `factory/pipeline.yml` written by the agent in the coder's stage, the guard (`judge` with `WritePathService.at`'s settings) refuses exactly those that `undo` reverts or deletes (WE2.3).
16. `reverted` and `deleted` are sorted ascending without repeats, and a second `undo` right after the first returns empty lists and `restored_work_item` false.
17. `undo` raises `WorkItemFormatError` naming the path when the stage-start commit does not contain the work item, and when the work item at the stage-start commit has front matter that cannot be read.
18. make check stays green.
19. docs: `docs/project-guide.md` explains the undo (what it undoes and why from the stage-start commit, that other work items in progress are undone whatever the write paths say, that the work item's state and journal are restored and a deleted or broken work item is restored whole, that it makes no commit, and the limits: ignored paths, writes outside the checkout, an agent's own commit stays in the history); `docs/decisions.md` records that the undo and the guard read the write paths from the stage-start commit (WE2) and that a work item the agent breaks is restored whole.

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
from factory.adapters.run_record_file import JsonRunRecordFile
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
b = Boundaries(git=git, hosting=FakeHostingService(), agent_runtime=FakeAgentRuntime(), project_commands=MakeProjectCommands(work), work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(), cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(), clock=clock, log=TimestampedFactoryLog(root / 'factory.log', clock), health=JsonHealthStatusFile(root / 'health.json'), pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(root / 'claude'), run_record=JsonRunRecordFile(root / 'run-record.json'), checkout=work)
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
