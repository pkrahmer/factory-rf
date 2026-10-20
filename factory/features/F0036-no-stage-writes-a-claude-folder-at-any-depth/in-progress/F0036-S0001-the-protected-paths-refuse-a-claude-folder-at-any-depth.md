# The protected paths refuse a .claude folder at any depth

## Description

On 2026-10-19 the human decided that no agent writes any `.claude/` folder, at any depth. Today `PROTECTED_PATHS` holds `.claude/*`, which protects the repository's root `.claude/` only. F0022's acceptance walked the guard and found `src/.claude/skills/x/SKILL.md -> allowed` under the write path `src/*`. This story adds the pattern `*/.claude/*` to `PROTECTED_PATHS`, right after `.claude/*`. `refusal` then refuses a nested `.claude/` with the text it gives the root one: `<path> is owned by the human; a change there is a question.` The Claude Code hook and the undo after every run both judge a path through `refusal`, and neither changes, so both refuse a nested `.claude/` from now on: criterion 3 pins the verdict they share, and criterion 4 the undo's removal of a new file. A path whose `.claude` is not a whole segment (`src/.claudex/a`, `src/x.claude/a`), `claude/` without the dot, and a path that only ends in `.claude` stay as they are. The kernel's targets stay as they are (the feature's decision 2). The other eleven patterns, the refusal texts and their order (checkout, protected, write paths) stay as they are.

## Interface

`src/factory/domain/write_paths.py` (`domain`):

```python
PROTECTED_PATHS: tuple[str, ...] = (
    ".claude/*",
    "*/.claude/*",
    "CLAUDE.md",
    "Makefile",
    "pyproject.toml",
    "uv.lock",
    PIPELINE_DEFINITION_FILE,
    STORY_FORM_FILE,
    FEATURE_FORM_FILE,
    FEATURE_FILE_NAME,
    "*/" + FEATURE_FILE_NAME,
    f"{PROJECT_AGENTS_DIRECTORY}/*",
)
```

- `matches_any(path, PROTECTED_PATHS)` is true for a path with a whole segment `.claude` and at least one segment after it, at the root or at any depth. It is false for a segment that only contains `.claude` (`.claudex`, `x.claude`), for `claude` without the dot, and for a path whose last segment is `.claude`.
- `refusal(path, guard)`, with `guard.protected_paths` the twelve patterns, returns `<path> is owned by the human; a change there is a question.` for such a path, also when a write path matches it. Unchanged: `refusal`, `matches_any`, `is_writable`, `expand_write_paths`, `factory.application.write_paths`, `factory.application.undo`, `factory.adapters.claude_guard` and `factory.domain.confinement`.

Tests (the tester writes them):

- `tests/domain/test_write_paths.py`: `test_the_protected_paths_are_the_engines_eleven_patterns` becomes `test_the_protected_paths_are_the_engines_twelve_patterns`, its tuple with `"*/.claude/*"` as the second item, under the leave of the feature's decision 3. Nothing else in the module changes.
- `tests/domain/test_nested_claude_paths.py` (new): the pattern and the refusal.
- `tests/application/test_undo_nested_claude.py` (new): the undo, against a real local bare remote as `tests/application/test_undo.py` sets it up. The tester may move that module's `_pipeline`, `_start` and `_undo` to a shared module under the standing leave of `CLAUDE.md` (*Tests*).

## Acceptance criteria

1. The protected paths are twelve: `PROTECTED_PATHS` equals the tuple of the Interface, with `"*/.claude/*"` second (the renamed `test_the_protected_paths_are_the_engines_twelve_patterns`).
2. A `.claude` folder is protected at any depth and only as a whole segment (rows of one parametrized test of `matches_any(path, PROTECTED_PATHS)`). True for `.claude/settings.json`, `.claude/skills/x/SKILL.md`, `src/.claude/skills/x/SKILL.md`, `src/factory/.claude/commands/c.md`, `docs/.claude/settings.json` and `a/b/c/.claude/d`. False for `src/.claudex/a`, `src/x.claude/a`, `src/claude/a`, `claude/agents/coder.md`, `src/.claude` and `.claudex/a`.
3. The guard's verdict on a nested `.claude/` (rows of one parametrized test of `refusal(path, guard)`, the guard with root `/work`, write paths `["src/*"]` and `list(PROTECTED_PATHS)`). `src/.claude/skills/x/SKILL.md` gives `src/.claude/skills/x/SKILL.md is owned by the human; a change there is a question.`. `src/factory/.claude/settings.json` gives `src/factory/.claude/settings.json is owned by the human; a change there is a question.`. `src/.claudex/a.md` gives `None`, and `src/a.py` gives `None`.
4. The undo removes a nested `.claude/` and keeps the rest. A stage with the write paths `["src/*"]` starts, and the agent writes `src/.claude/skills/x/SKILL.md`, `src/.claudex/notes.md` and `src/a.py` (all three new). After `UndoService` runs, `src/.claude/skills/x/SKILL.md` is gone, the other two hold the agent's text, and the report's `deleted` is `["src/.claude/skills/x/SKILL.md"]`.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, *A project's own skills*. The sentences from "The protection covers the repository's root `.claude/` only" to "so the review and your merge see it in the diff." become the rule. `.claude/` is protected at any depth (`.claude/*` and `*/.claude/*`), so no stage writes a `.claude/` folder anywhere in the repository (the human, 2026-10-19). The hook refuses the edit in a Claude Code run, and the undo removes the write after every run. The kernel's guard cannot refuse it inside a folder a write path opens. `docs/project-guide/write-guard.md`, *Protected paths and the refusal*: "eleven patterns" becomes "twelve patterns", and the list gains `*/.claude/*` after `.claude/*`. It says that a `.claude` segment is protected at any depth and only as a whole segment, and that the kernel's targets do not change. `docs/decisions.md`: an entry *No stage writes a .claude folder at any depth*, dated with the story, from the feature's decisions 1, 2 and 4. Its reasons: the human's decision of 2026-10-19, and F0022's decision 12 with its acceptance's guard walk. It rejects a Landlock rule (Landlock only allows) and a rewording of R14. The F0022 entry that leaves the nested `.claude/skills/` open gets one line naming the new entry. `README.md`: none.

## Smoke test

```bash
uv run python -c 'from pathlib import Path; from factory.domain.agent_runs import GuardSettings; from factory.domain.write_paths import PROTECTED_PATHS, refusal; g = GuardSettings(root=Path("/work"), write_paths=["src/*"], protected_paths=list(PROTECTED_PATHS)); [print(p, "->", refusal(p, g) or "allowed") for p in (".claude/skills/x/SKILL.md", "src/.claude/skills/x/SKILL.md", "src/.claudex/a.md", "src/a.py")]'
```
Expect: four lines, `.claude/skills/x/SKILL.md -> .claude/skills/x/SKILL.md is owned by the human; a change there is a question.`, `src/.claude/skills/x/SKILL.md -> src/.claude/skills/x/SKILL.md is owned by the human; a change there is a question.`, `src/.claudex/a.md -> allowed`, `src/a.py -> allowed`

## Journal
