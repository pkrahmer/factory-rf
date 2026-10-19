# A project keeps the ignored folders it names

## Description

Build this story only on the answer A of the feature's decision 3. S0003 removes every git-ignored path after every agent run and at every restore. F0024's mutation report needs `mutants/` from the doing stage to the review and from story to story. This story adds the optional key `kept_ignored` to the pipeline definition: a list of `<folder>/*` patterns in the checkout, the tool paths' first form, refused at load in any other form. The removal keeps every ignored entry that is a kept folder or lies beneath one. Every other ignored entry is still removed, a kept folder inside a larger ignored entry included. `StageLauncher` hands the definition's kept folders to `run_sealed`, and the tick's restore takes them from the definition it loaded. The preflight's probe run keeps nothing, since the preflight knows no pipeline definition. The default, no key, behaves as S0003. The key is a new optional field of the pipeline definition, so the records contract's minor goes up by one. factory-rf's own `kept_ignored: ["mutants/*"]` is the human's change 3 after this story.

## Interface

`factory.domain.pipeline_definition` (`domain`):

```python
class PipelineDefinition(BaseModel):
    ...
    kept_ignored: list[WritePath] = []


def kept_folders(patterns: Sequence[str]) -> list[str]: ...
```

- `kept_ignored` defaults to `[]`. A load rule (one more in `_RULES`, its faults reported with the others, joined by `; `) refuses each pattern for which `tool_path_folder(pattern)` is `None` or that starts with `~/`. The fault is `kept ignored path <pattern>: must be <folder>/*`. So `mutants/*` and `demo/todo-service/project/.ruff_cache/*` load. `~/.cache/*`, `mutants`, `mutants/**`, `*/x/*`, `./mutants/*`, `../x/*`, `a//b/*` and `/abs/*` are refused.
- `kept_folders`: the folder of each pattern (`tool_path_folder`), in order, a repeat left out: `["mutants/*", "a/b/*", "mutants/*"]` gives `["mutants", "a/b"]`. Its callers pass loaded patterns only.

`factory.application.git` and `factory.adapters.git_cli`:

```python
class Git(ABC):
    @abstractmethod
    def remove_ignored(self, kept: Sequence[str] = ()) -> None:
        """Remove every untracked path the ignore rules match, but the folders `kept` names.

        ... (S0003's rules). An ignored entry that is a kept folder or lies beneath one stays.
        """
```

- Each kept folder is checked by `check_repository_path` before any git command: an empty, absolute or `..` path raises `ValueError` and nothing is removed.
- With `kept` empty, the behaviour and the command are S0003's (`git clean --quiet --force --force -d -X`).
- With `kept` not empty, `GitCli` lists the ignored entries with `git ls-files -z --others --ignored --exclude-standard --directory` (a folder git lists whole ends with `/`). It leaves out each entry whose path, without the trailing `/`, is a kept folder or lies beneath one, compared by path segments (`mutants-old` is not beneath `mutants`). It removes the rest with one `git --literal-pathspecs clean --quiet --force --force -d -X -- <entries>`, so a name holding `*`, `[` or `:` is taken literally. With no entry left, it runs no `clean`. An entry that holds a kept folder (`a/` when `a/b` is kept) is not left out, and is removed whole. A kept folder that git does not list, because no rule ignores it or it does not exist, changes nothing.
- The interface's count of operations does not change.

`factory.application.sealed_runs` (`application`):

- `run_sealed(boundaries, request, *, run=None, kept_ignored: Sequence[str] = ())` calls `git.remove_ignored(kept_ignored)` where S0003 calls `remove_ignored()`.

`factory.application.stage` (`application`):

- `StageLauncher.launch` calls `run_sealed(..., kept_ignored=kept_folders(self._definition.kept_ignored))`.

`factory.application.tick` (`application`):

- The restore calls `remove_ignored(kept_folders(definition.kept_ignored))`, with the definition the tick's load step returned.

Unchanged: `agent_run_probe_item` (it calls `run_sealed` without `kept_ignored`, so the probe keeps nothing), `tool_paths`, the kernel's targets, the undo.

`factory.domain.contract` and `src/factory/contract/*.schema.json`: regenerated with `uv run python -m factory.entry.contract`. `RECORDS_CONTRACT`'s minor goes up by one from the value it holds when the story starts (the feature's decision 14).

Tests (the tester writes them): `tests/domain/test_kept_ignored.py`, `tests/adapters/test_git_cli_kept_ignored.py`, `tests/application/test_sealed_runs_kept.py`, `tests/application/test_stage_run_kept.py`, `tests/application/test_tick_kept.py`, as S0003's tests build theirs. Changed under the feature's decision 16, by the tester only and nothing else in those modules: the records contract's version literals in `tests/domain/test_contract.py`, `tests/domain/test_contract_provider_limit.py` and any later module that pins one.

## Acceptance criteria

1. The load rule (rows of one parametrized test, a pipeline definition that passes every other rule, parsed with `RuamelPipelineDefinitionReader().parse`): `kept_ignored: ["mutants/*"]` loads with `kept_ignored == ["mutants/*"]`. `["demo/todo-service/project/.ruff_cache/*"]` loads. `[]` and a definition without the key both load with `[]`. Each of `~/.cache/*`, `mutants`, `mutants/**`, `*/x/*`, `./mutants/*`, `../x/*`, `a//b/*` and `/abs/*` raises `PipelineDefinitionInvalid` whose text holds `kept ignored path <pattern>: must be <folder>/*`. `["mutants", "~/x/*"]` gives both faults in one text, joined by `; `.
2. `kept_folders` (rows of one parametrized test): `[]` gives `[]`. `["mutants/*"]` gives `["mutants"]`. `["mutants/*", "a/b/*", "mutants/*"]` gives `["mutants", "a/b"]`.
3. `GitCli.remove_ignored(kept)` (rows of one parametrized test, a commit whose `.gitignore` holds `.venv/`, `mutants/`, `mutants-old/` and `*.log`, with the stand-ins `.venv/lib/standin.pth`, `mutants/src/mod.py`, `mutants-old/x`, `run.log` and `[a].log`). `["mutants"]` keeps `mutants/src/mod.py` and removes the other four. `[]` removes all five. `["mutants/src"]` removes all five (the kept folder lies inside the listed entry `mutants/`). `["absent"]` removes all five. `["notignored"]`, with an untracked `notignored/x` that no rule matches, removes all five stand-ins and keeps `notignored/x`. In every row the tracked files and `git status --porcelain` are unchanged.
4. Refused kept folders (rows of one parametrized test): `["/abs"]`, `["../x"]` and `[""]` each raise `ValueError`, and all five stand-ins of criterion 3 are still there.
5. `run_sealed` (rows of one parametrized test, a run that writes `.venv/lib/standin.pth` and `mutants/src/mod.py` into a checkout whose `.gitignore` holds `.venv/` and `mutants/`): with `kept_ignored=["mutants"]` only `mutants/src/mod.py` is left, and without `kept_ignored` neither is.
6. A stage (rows of one parametrized test, `StageRunner` as S0003's criterion 5 builds it, the agent's run writing `.venv/standin.pth` and `mutants/standin.txt`, `main_files={".gitignore": ".venv/\nmutants/\n"}`). With `kept_ignored: ["mutants/*"]` in the pushed pipeline definition, after the stage `mutants/standin.txt` is in the work tree and `.venv/standin.pth` is not. Without the key, neither is.
7. The restore (rows of one parametrized test, `Tick` with the idle handler, `.git/info/exclude` naming `mutants/` and `scratch.log`, both present). With `kept_ignored: ["mutants/*"]` on `origin/main`, after `tick.run()` `mutants/` is there and `scratch.log` is not. Without the key, neither is.
8. The records contract: `RECORDS_CONTRACT` is one minor above its value when the story started. The committed `pipeline-definition.schema.json` holds the property `kept_ignored`, and the earlier contract tests of the feature's decision 16 pass with exactly their version literals changed.
9. `make check` stays green.
10. docs: `docs/operator-guide.md`, *The pipeline definition*: the key `kept_ignored`, its form, its fault line, what it keeps and what it does not (a kept folder inside a larger ignored entry, the preflight's probe run once per image build), and that a kept folder is trusted across stages, so it must be one that no check runs or reads (factory-rf keeps `mutants/`, which no target of `make check` reads). *The records contract*: the new minor. `docs/project-guide/stages.md`, *The rules of the definition*: the rule and its fault. `docs/project-guide/git-and-hosting.md`, *Restoring the checkout*: `remove_ignored(kept)`, the listing, the literal pathspecs and the segment comparison. `docs/project-guide/watching.md`: the restore's and `run_sealed`'s kept folders. `docs/decisions.md`: an entry *A project keeps the ignored folders it names*, dated with the story, with the reasons of the feature's decisions 3, 13 and 14.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid

base = 'contract: "1.0"\nroles:\n  coder: {write_paths: ["src/*"]}\nstages:\n  doing: {role: coder, next: [done]}\n  done: {}\n'
for kept in ('["mutants/*"]', '["~/.cache/*"]', '["mutants"]'):
    try:
        definition = RuamelPipelineDefinitionReader().parse(base + f"kept_ignored: {kept}\n")
        print("loads", definition.kept_ignored)
    except PipelineDefinitionInvalid as error:
        print("refused", "kept ignored path" in str(error))
EOF
```
Expect: three lines, `loads ['mutants/*']`, `refused True`, `refused True`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git -C "$d" init -q -b main
printf '.venv/\nmutants/\n*.log\n' > "$d/.gitignore"
git -C "$d" add -A && git -C "$d" -c user.name=t -c user.email=t@example.com commit -q -m base
mkdir -p "$d/.venv/lib" "$d/mutants/src"
echo standin > "$d/.venv/lib/standin.pth"; echo standin > "$d/mutants/src/mod.py"; echo standin > "$d/[a].log"
uv run -q python - "$d" <<'EOF'
import sys
from pathlib import Path

from factory.adapters.git_cli import GitCli

root = Path(sys.argv[1])
GitCli(root).remove_ignored(["mutants"])
print(sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.relative_to(root).parts[0] != ".git"))
EOF
```
Expect: `['.gitignore', 'mutants/src/mod.py']`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
