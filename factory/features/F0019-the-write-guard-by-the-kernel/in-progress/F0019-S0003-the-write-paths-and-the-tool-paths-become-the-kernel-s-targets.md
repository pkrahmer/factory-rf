---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-18T15:12:15.858536Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T15:12:15.852400Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T15:12:15.858536Z'
  stage: intake
---

# The write paths and the tool paths become the kernel's targets

## Description

The kernel allows writes beneath folders and on existing files, while a stage's write paths are `fnmatch` patterns, and an agent run also writes the project's tool state (`.venv`, caches, reports), which no write path names. This story gives the pipeline definition an optional key `tool_paths`, folder patterns written by every role's agent run (`<folder>/*` in the checkout, `~/<folder>/*` in the agent's home; feature decision 8), carries them in the guard settings the write-path service returns, and adds two pure functions to the domain: `write_targets` turns a run's write paths and tool paths into folders and files of the kernel, and `confinement_of` turns those targets, with the files that exist and the runtime's own paths, into the `Confinement` of S0002. A path the kernel cannot name exactly is widened to the nearest folder it can, never to the checkout's root, and the undo narrows it after the run (feature decision 6). The hook and the undo keep judging the write paths as they do; the tool paths reach neither. Nothing uses the targets yet: the runtime does in S0004. factory-rf's own `factory/pipeline.yml` gets its `tool_paths` from the human once the image runs this code (the feature's change 5).

## Interface

`factory.domain.pipeline_definition` (`domain`):

```python
class PipelineDefinition(BaseModel):
    ...
    tool_paths: list[WritePath] = []
```

- A new load-time rule in `_RULES`: every tool path must match `<folder>/*` or `~/<folder>/*`, where `<folder>` is one or more `/`-separated segments, each non-empty, none `..`, none holding `*`, `?` or `[`, and `<folder>` does not start with `/`. A tool path that does not is the fault `f"tool path {path}: must be <folder>/* or ~/<folder>/*"`, one per such path, joined with the other rules' faults as today.
- An absent key is `[]`; the key is strict like the others (a string instead of a list is refused by the model).

`factory.domain.agent_runs` (`domain`):

```python
class GuardSettings(BaseModel):
    ...
    tool_paths: list[str] = []
```

`factory.application.write_paths` (`application`):

- `WritePathService.at` returns `GuardSettings` with `tool_paths` the definition's `tool_paths` at the stage-start commit, unchanged (no placeholder is expanded in them); `write_paths` and `protected_paths` are as before.

`factory.domain.confinement` (`domain`):

```python
TargetKind = Literal["folder", "file"]

class WriteTarget(BaseModel):
    """One path the kernel may allow: a folder and everything beneath it, or one file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: AbsolutePath
    kind: TargetKind

def write_targets(guard: GuardSettings, *, home: Path | None) -> list[WriteTarget]:
    """The kernel's targets of the write paths, then the tool paths, of `guard`."""

def confinement_of(
    targets: Sequence[WriteTarget],
    *,
    root: Path,
    existing_files: Collection[Path],
    extras: Sequence[WriteTarget],
    temporary_directory: Path,
) -> Confinement:
    """The rules of one run: the targets as the files that exist allow them, and the extras."""
```

- `write_targets`, for each write path `p` of `guard.write_paths`, in order, relative to `guard.root`:
  - `p` empty, starting with `/`, or holding a `..` segment: no target.
  - `p` ending in `/*` with no `*`, `?` or `[` before it: the folder `root / p[:-2]`.
  - `p` holding none of `*`, `?`, `[`: the file `root / p`.
  - any other `p`: the folder of the segments before the first segment that holds `*`, `?` or `[`; no target when there is none (a pattern at the root, such as `*.md`).
- then for each tool path `t` of `guard.tool_paths`, in order: `~/<folder>/*` is the folder `home / <folder>`, and no target when `home` is `None`; `<folder>/*` is the folder `root / <folder>`; any other `t` gives no target.
- A target equal to an earlier one is left out; the order is otherwise kept.
- `confinement_of`: a folder target goes to `folders`; a file target in `existing_files` goes to `files`; a file target not in `existing_files` puts its parent folder in `folders`, unless that parent is `root`, in which case it gives nothing. The `extras` are taken as they are, never widened and never checked against `existing_files`: their folders follow the targets' folders and their files the targets' files, each in the order given. A path equal to an earlier one of the same list is left out. `temporary_directory` is taken as given.

Tests (the tester writes them): `tests/domain/test_tool_paths.py` (the rule, through `PipelineDefinition` or the YAML reader), `tests/domain/test_write_targets.py`, `tests/domain/test_confinement_of.py`, `tests/application/test_write_paths_tool_paths.py`. A pipeline definition written in a test passes every other load-time rule (`CLAUDE.md`, *Tests*).

## Acceptance criteria

1. A pipeline definition with `tool_paths: [".venv/*", "a/b/*", "~/.cache/*"]` loads with those three in order, and one without the key loads with `tool_paths == []` (rows of one parametrized test).
2. Each of `"*.log"`, `".venv"`, `"/var/cache/*"`, `"../x/*"`, `"a/../b/*"`, `"a/*/b/*"`, `"a/b?/*"`, `"a/[b]/*"`, `"~/*"`, `"~/../x/*"` and `"a//b/*"` alone in `tool_paths` makes the definition invalid with the fault `tool path <path>: must be <folder>/* or ~/<folder>/*`; two of them give two faults; and `tool_paths: ".venv/*"`, a string instead of a list, makes it invalid with `invalid tool_paths: Input should be a valid list` (rows of one parametrized test).
3. `WritePathService.at` returns the definition's `tool_paths` at the stage-start commit, `[".venv/*", "~/.cache/*"]`, unchanged, and `[]` for a definition without the key; a `tool_paths` pushed after the stage-start commit is not in the result (rows of one parametrized test).
4. With `root` `/work/checkout` and `home` `/home/agent`, `write_targets` gives for each write path (rows of one parametrized test): `src/*` the folder `/work/checkout/src`; `a/b/*` the folder `/work/checkout/a/b`; `README.md` the file `/work/checkout/README.md`; `factory/features/F0001-x/in-progress/F0001-S0001-y.md` that file; `docs/*.md` the folder `/work/checkout/docs`; `a/b*/c` the folder `/work/checkout/a`; `a/b?/c` the folder `/work/checkout/a`; `a/[bc]/d` the folder `/work/checkout/a`; `*.md` nothing; `*` nothing; `""` nothing; `/etc/*` nothing; `../x/*` nothing; `src/../x` nothing.
5. With the same `root`, `write_targets` gives for each tool path (rows of one parametrized test): `.venv/*` the folder `/work/checkout/.venv`; `~/.cache/*` with `home` `/home/agent` the folder `/home/agent/.cache`; `~/.cache/*` with `home` `None` nothing; `*.log`, of neither form, nothing.
6. `write_targets` keeps the order write paths first, then tool paths, and leaves out a repeated target: write paths `["src/*", "docs/*", "src/*"]` and tool paths `[".venv/*", "src/*"]` give the folders `src`, `docs`, `.venv`, in that order.
7. `confinement_of` with `root` `/w` (rows of one parametrized test): a folder target `/w/src` is in `folders`; a file target `/w/README.md` that is in `existing_files` is in `files`; a file target `/w/docs/openapi.json` that is not gives the folder `/w/docs`; a file target `/w/NEW.md` that is not gives nothing; a file target `/w/a/b/c.md` that is not gives the folder `/w/a/b`.
8. `confinement_of` puts the folder extras after the targets' folders and the file extras after the targets' files, in their order, takes a file extra as given even when it is not in `existing_files`, leaves out a path already in the same list (a missing file whose folder is also a folder target gives that folder once; a folder extra equal to a target's folder is left out), and returns `temporary_directory` as given.
9. `GuardSettings` built without `tool_paths` has `tool_paths == []`, and the verdict `refusal`, which the hook and the undo share, ignores the tool paths: with write paths `["src/*"]` and tool paths `[".venv/*"]`, `.venv/x` is refused as outside the write paths and `src/x` is allowed (rows of one parametrized test).
10. `make check` stays green.
11. docs: `docs/project-guide.md`, section *The pipeline definition*, names `tool_paths`, its form and its fault; section *The write paths* gains a subsection *The kernel's targets*: the rules of `write_targets` and `confinement_of` with the widening of a missing file and of a wildcard pattern to a folder, never the root, and that the undo narrows the rest. `docs/operator-guide.md`, section *The pipeline definition*, names `tool_paths` with an example (`[".venv/*", ".reports/*", "~/.cache/*"]`) and says that a project's tools that write elsewhere are refused once the guard is live. `docs/decisions.md` gets an entry *The kernel's targets of the write paths and the tool paths*, dated 2026-10-18 (F0019-S0003), with the reasons of the feature's decisions 6, 8 and 15.

## Smoke test

```bash
uv run -q python -c '
from pathlib import Path
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
text = Path("template/factory/pipeline.yml").read_text(encoding="utf-8").rstrip() + "\n"
reader = RuamelPipelineDefinitionReader()
print(reader.parse(text + "tool_paths: [\".venv/*\", \"~/.cache/*\"]\n").tool_paths)
try:
    reader.parse(text + "tool_paths: [\"*.log\"]\n")
except PipelineDefinitionInvalid as error:
    print(error)
'
```
Expect: two lines, `['.venv/*', '~/.cache/*']` and then `tool path *.log: must be <folder>/* or ~/<folder>/*`

```bash
uv run -q python -c '
from pathlib import Path
from factory.domain.agent_runs import GuardSettings
from factory.domain.confinement import write_targets
guard = GuardSettings(root=Path("/work/checkout"), write_paths=["src/*", "README.md", "docs/*.md", "*.md"], protected_paths=[], tool_paths=[".venv/*", "~/.cache/*"])
for target in write_targets(guard, home=Path("/home/agent")):
    print(target.kind, target.path)
'
```
Expect: five lines, `folder /work/checkout/src`, `file /work/checkout/README.md`, `folder /work/checkout/docs`, `folder /work/checkout/.venv` and `folder /home/agent/.cache`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
