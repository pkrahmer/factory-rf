---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 324
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-20T03:27:27.006774Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T03:23:42.725278Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T03:23:42.734186Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T03:23:58.352026Z'
  stage: intake
  run: e3b8550ffd324a878a0f60a647c856d5
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T03:24:18.843640Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T03:27:06.720805Z'
  stage: tests
  run: 6e1303b306d44e72b4e112e92d60f1fd
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T03:27:27.006774Z'
  stage: doing
---

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

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names `src/factory/domain/write_paths.py` and the full twelve-pattern `PROTECTED_PATHS` tuple. The unchanged modules are listed, and the three test files are named with their changes.
   - Criteria: each is testable by one test function or one parametrized test. Criterion 1 pins the tuple. Criterion 2 covers the pattern's true and false sides: the root, nested depths, `.claudex`, `x.claude`, `claude/` without the dot, and a path that only ends in `.claude`. Criterion 3 covers the refusal text on the refused side and `None` on the allowed side, with the write path `src/*` matching. Criterion 4 covers the undo's removal of a new nested file, the two kept files and the `deleted` list. The docs criterion lists every edit by file. `make check` is present.
   - Smoke test: one runnable `uv run python -c` command. Its Expect line gives four exact output lines that can be compared with the output.
   - Architecture: the change is a constant in `factory.domain`, and `refusal`, the hook, the undo and the kernel's confinement are not touched. That matches the layering in CLAUDE.md.
   - Scope: matches `feature.md`: the pattern, the tests under decision 3 and the three docs. The kernel guard, `~/.claude` and R14 are out of scope and untouched. The test rename has the human's leave through decision 3.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 4. They fail on purpose until `*/.claude/*` is added to `PROTECTED_PATHS`.

   - criterion 1: tests/domain/test_write_paths.py::test_the_protected_paths_are_the_engines_twelve_patterns (renamed from `..._eleven_patterns` under the feature's decision 3; `"*/.claude/*"` added as the tuple's second item; nothing else in the module changed)
   - criterion 2: tests/domain/test_nested_claude_paths.py::test_a_claude_folder_is_protected_at_any_depth_and_only_as_a_whole_segment (12 rows: 6 true, 6 false, as the criterion lists them)
   - criterion 3: tests/domain/test_nested_claude_paths.py::test_the_guard_refuses_a_nested_claude_folder_although_a_write_path_matches_it (4 rows; the guard has root `/work`, write paths `["src/*"]` and `list(PROTECTED_PATHS)`)
   - criterion 4: tests/application/test_undo_nested_claude.py::test_the_undo_removes_a_nested_claude_folder_and_keeps_the_rest (real bare remote; write paths `["src/*"]`)
   - criteria 5 and 6: not tests (`make check`, docs).

   Files created: tests/domain/test_nested_claude_paths.py, tests/application/test_undo_nested_claude.py, tests/undo_support.py.

   Earlier test files changed:
   - tests/domain/test_write_paths.py: the rename above, under the feature's decision 3.
   - tests/application/test_undo.py: moved under the standing leave in CLAUDE.md (*Tests*), as the Interface allows. Its `_pipeline`, `_start` and `_undo` now live in tests/undo_support.py as `pipeline_text`, `start_stage` and `undo_stage`. The constants they need moved with them (INSTANCE, BRANCH, IN_PROGRESS, PATH, SECOND, PIPELINE_FILE, GUIDE, GUIDE_TEXT, KEPT, KEPT_TEXT, BODY, INTAKE_ROLE, BASE_FILES), and test_undo.py imports them from there. Every test in that module keeps its name and checks the same thing, and all of them pass after the move.

   Run of `make test`: 8 failed of 6083 (taken from `.reports/junit.xml`), none of them collection errors, so no module failed to import. They fail on wrong results: the twelve-pattern tuple, the four nested true rows of criterion 2, the two refusal rows of criterion 3, and the undo test. The root `.claude/` rows and the false rows already pass. `make lint` is green. Type check skipped, as this stage says. No criterion needed interpreting.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/domain/test_nested_claude_paths.py::test_a_claude_folder_is_protected_at_any_depth_and_only_as_a_whole_segment[a/b/c/.claude/d-True]
6. factory: started doing as self.
