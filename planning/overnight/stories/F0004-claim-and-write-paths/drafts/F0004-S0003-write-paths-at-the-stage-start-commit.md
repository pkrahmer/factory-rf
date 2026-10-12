# Write paths and protected paths read at the stage-start commit

## Assignment (as of log entry 1)

Build the one source of what an agent may write. The domain gets the matching rule (a write path is a glob in which `*` also crosses `/`, as in v1), the expansion of the two placeholders `{work_item}` and `{feature}`, the engine's list of protected paths that no write path can reach, and `refusal`, the single verdict that the guard hook (S0004) and the undo (S0005) both apply. The application gets `WritePathService.at`, which reads the pipeline definition at the stage-start commit with `Git.show_file` and never from the work tree, so an agent that rewrites the pipeline definition widens nothing (R32, WE2.1) and an invalid rewrite breaks nothing (WE2.2). Covers R32, WE2.1 (the source), WE2.3 (one source for the guard and the undo); keeps kept thing 17 (protected paths are outside every write path). Nothing here is observable only in the morning.

## Interface

`src/factory/domain/write_paths.py`

```python
PROTECTED_PATHS: tuple[str, ...] = (
    ".claude/*",
    "CLAUDE.md",
    "Makefile",
    "pyproject.toml",
    "uv.lock",
    "factory/pipeline.yml",
    "factory/story-form.md",
    "factory/feature-form.md",
    "feature.md",
    "*/feature.md",
)

def matches_any(path: str, patterns: Sequence[str]) -> bool: ...
def is_writable(path: str, write_paths: Sequence[str]) -> bool: ...
def expand_write_paths(patterns: Sequence[str], *, work_item_path: str, feature_directory: str) -> list[str]: ...
def refusal(path: str, guard: GuardSettings) -> str | None: ...
```

`src/factory/application/write_paths.py`

```python
class WritePathService:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def at(self, stage_start: StageStart, work_item_path: str) -> GuardSettings: ...
```

`GuardSettings` is `factory.domain.agent_runs.GuardSettings` (`root`, `write_paths`, `protected_paths`); `StageStart` is the DTO of `factory.application.claims`; paths are repository-relative POSIX strings.

Rules:

- `matches_any` is `fnmatch.fnmatchcase` over the patterns: case-sensitive, and `*` also matches `/`. It looks at the string only.
- `is_writable(path, write_paths)` is true when `path` is safe and `matches_any(path, write_paths)`. A path is unsafe when it is empty, begins with `/`, or has a segment equal to `..`; an unsafe path is never writable, whatever the patterns (`src/../factory/pipeline.yml` does not match `src/*`).
- `expand_write_paths` replaces `{work_item}` with `work_item_path` and `{feature}` with `feature_directory` wherever they occur in a pattern, keeps the order, and leaves a pattern without a placeholder as it was. Any other `{name}` in a pattern (lowercase letters and underscores between braces) raises `ValueError` whose message names the placeholder.
- `PROTECTED_PATHS` holds exactly the ten patterns above: v1's lists in v1.1's names (the project's Claude Code directory, the manifest and lock file, the make file, the project guide, the pipeline definition, the two forms) and a feature file named `feature.md` at any depth. They are outside every write path: `refusal` checks them before the write paths.
- `refusal(path, guard)` returns `None` when the write is allowed, otherwise the text of the refusal, checked in this order: an unsafe path gives `<path> is not a path inside the checkout.`; a path matching `guard.protected_paths` gives `<path> is owned by the human; a change there is a question.`; a path that is not writable under `guard.write_paths` gives `<path> is outside the write paths of this stage.`
- `WritePathService.at` reads `factory/pipeline.yml` at `stage_start.commit` with `boundaries.git.show_file` and parses it with `boundaries.pipeline_reader`. It looks up the role of `stage_start.claim.stage` and returns `GuardSettings(root=boundaries.checkout, write_paths=expand_write_paths(<the role's write paths>, work_item_path=work_item_path, feature_directory=<the feature directory of work_item_path>), protected_paths=list(PROTECTED_PATHS))`. The feature directory is the directory above the work item's lifecycle folder (`factory/features/F0004-x` for `factory/features/F0004-x/in-progress/F0004-S0001-y.md`). It never reads the work tree's copy of the pipeline definition.
- `at` raises `ValueError` when `work_item_path` is not `factory/features/<feature directory>/<lifecycle folder>/<file>`. It raises `PipelineDefinitionInvalid`, naming the fault, when the pipeline definition is absent at the commit, when the reader rejects it, and when the claim's stage is not in the definition or has no role.

Tests: `tests/domain/test_write_paths.py` and `tests/application/test_write_paths.py` (shared fixtures `remote`, `checkout`, `human`, `boundaries`; a later commit on `main` is made with `human.push_file("main", "factory/pipeline.yml", text)` and `checkout.fetch()`; a `StageStart` is built from `checkout.resolve("origin/main")` and a `Claim`).

## Acceptance criteria

1. `is_writable` is true for a path that matches a write path, and `*` crosses `/`: `src/factory/domain/x.py` is writable under `src/*`, `tests/a.py` under `tests/*`, and a path differing only in case (`SRC/a.py`) is not writable under `src/*`.
2. `is_writable` is false for a path that matches no write path, and false for any path when the list of write paths is empty.
3. `is_writable` is false for an empty path, a path beginning with `/` and a path with a `..` segment, even when a pattern matches it (`src/../factory/pipeline.yml` under `src/*`).
4. `expand_write_paths(["{work_item}", "{feature}/backlog/*", "tests/*"], work_item_path=W, feature_directory=D)` returns `[W, "D/backlog/*", "tests/*"]`: both placeholders replaced, the order kept, the pattern without a placeholder unchanged.
5. `expand_write_paths` raises `ValueError` whose message names `{stage}` for the pattern `{stage}/*`.
6. `PROTECTED_PATHS` is exactly the ten patterns of the Interface, in that order.
7. Each protected pattern protects: `matches_any` is true for `.claude/settings.json`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, `feature.md`, `factory/features/F0004-x/feature.md` and `docs/feature.md` against `PROTECTED_PATHS`, and false for `docs/CLAUDE.md`, `src/pyproject.toml`, `.claudex/a`, `docs/myfeature.md` and `src/feature.md.bak`.
8. `refusal` returns `None` for a safe path that is writable and not protected.
9. `refusal` returns `<path> is outside the write paths of this stage.` for a safe, unprotected path that no write path matches.
10. `refusal` returns `<path> is owned by the human; a change there is a question.` for a protected path even when a write path matches it (write paths `["*"]`, path `pyproject.toml`).
11. `refusal` returns `<path> is not a path inside the checkout.` for an unsafe path, also when the path would match a protected pattern or a write path.
12. `WritePathService.at` returns `GuardSettings` with `root == boundaries.checkout`, `protected_paths == list(PROTECTED_PATHS)` and `write_paths` equal to the write paths of the claim's stage's role with `{work_item}` expanded: `["tests/*"]` for the fixture's `tester` and the work item's own path for `intake`.
13. `at` expands `{feature}` to the feature directory of the work item's path: for the fixture's `acceptance-reviewer` the write paths are the work item's path and `<feature directory>/backlog/*`.
14. `at` reads the pipeline definition as it was at the stage-start commit: after a later commit on `main` has widened the role's write paths, `at` for the earlier stage start still returns the original write paths, and `at` for a stage start at the later commit returns the widened ones.
15. `at` ignores the work tree's pipeline definition: after `factory/pipeline.yml` in the work tree is rewritten with wider write paths, replaced by text that is not valid YAML, and deleted, `at` returns the same `GuardSettings` each time and raises nothing.
16. `at` raises `PipelineDefinitionInvalid` whose message names `factory/pipeline.yml` when the file is absent at the stage-start commit.
17. `at` raises `PipelineDefinitionInvalid` when the pipeline definition at the stage-start commit is not valid (a stage whose `next` names an unknown stage).
18. `at` raises `PipelineDefinitionInvalid` naming the stage when the claim's stage is not in the definition at the commit, and when it is a stage without a role (the fixture's `approval`).
19. `at` raises `ValueError` for a work item path that is not under `factory/features/<feature directory>/<lifecycle folder>/` (for example `docs/a.md` and `factory/features/F0004-x/other/a.md`).
20. make check stays green.
21. docs: `docs/project-guide.md` explains where the write paths come from (the pipeline definition at the stage-start commit, never the work tree), the two placeholders, the list of protected paths and that they are outside every write path, and the refusal texts; `docs/decisions.md` records that the protected paths are the engine's fixed list (a project cannot change them in v1.1) and that the write paths are read at the stage-start commit (R32).

## Demo

```bash
uv run python - <<'EOF'
from pathlib import Path
from factory.domain.agent_runs import GuardSettings
from factory.domain.write_paths import PROTECTED_PATHS, expand_write_paths, refusal

work_item = 'factory/features/F0004-demo/in-progress/F0004-S0001-demo.md'
print(expand_write_paths(['{work_item}', '{feature}/backlog/*', 'tests/*'], work_item_path=work_item, feature_directory='factory/features/F0004-demo'))
guard = GuardSettings(root=Path('/work'), write_paths=['*'], protected_paths=list(PROTECTED_PATHS))
for path in ['tests/test_a.py', 'pyproject.toml', 'factory/features/F0004-demo/feature.md', 'src/../factory/pipeline.yml']:
    print(path, '->', refusal(path, guard))
print(len(PROTECTED_PATHS))
EOF
```
Expect: six lines. The list `['factory/features/F0004-demo/in-progress/F0004-S0001-demo.md', 'factory/features/F0004-demo/backlog/*', 'tests/*']`; `tests/test_a.py -> None`; `pyproject.toml -> pyproject.toml is owned by the human; a change there is a question.`; `factory/features/F0004-demo/feature.md -> factory/features/F0004-demo/feature.md is owned by the human; a change there is a question.`; `src/../factory/pipeline.yml -> src/../factory/pipeline.yml is not a path inside the checkout.`; and `10`.

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
from factory.application.write_paths import WritePathService
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, initial_state
from factory.domain.write_paths import refusal

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

service = WritePathService(b)
settings = service.at(start, PATH)
print(settings.write_paths == ['src/*', PATH], settings.root == work, len(settings.protected_paths))
(work / 'factory' / 'pipeline.yml').write_text(PIPELINE.replace('src/*', '*'))
again = service.at(start, PATH)
print(again == settings)
print(refusal('docs/extra.md', again))
EOF
```
Expect: three lines. `True True 10`; `True` (rewriting the pipeline definition in the work tree changed nothing); `docs/extra.md is outside the write paths of this stage.`

## Log (append only)

1. 2026-10-12 human: created.
