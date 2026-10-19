# No stage writes a .claude folder at any depth

## Goal

A project's skills under `.claude/skills/`, and everything else under `.claude/`, are the human's files, like `CLAUDE.md` (rule R15). Today the protection covers only the repository's root `.claude/`. `PROTECTED_PATHS` in `src/factory/domain/write_paths.py` holds `.claude/*`, which matches no nested folder. So a stage may write a `.claude/` inside its own write paths, for example `src/.claude/skills/x/SKILL.md` under the coder's `src/*`. F0022's acceptance showed it (`F0022-A0002-acceptance.md`, its guard walk, line 8: `src/.claude/skills/x/SKILL.md -> allowed`) and left it open as decision 12. The operator guide states it as an open point (*A project's own skills*: "The protection covers the repository's root `.claude/` only"). Whether Claude Code loads such a nested folder was never checked. The human decided on 2026-10-19 that no agent writes any `.claude/` folder, at any depth. This feature adds one pattern, `*/.claude/*`, to the protected paths. Every check that refuses the root `.claude/` today then refuses a nested one with the same words. That is the Claude Code hook (`factory-guard`, through `refusal`), and the undo after every run (`UndoService`, through `refusal`). It is for the human, whose files these are, and for the operator, whose open point becomes a rule. Done when every story below is merged and `make check` is green.

## Scope

- `src/factory/domain/write_paths.py`: `PROTECTED_PATHS` gains `*/.claude/*` (S0001).
- `tests/domain/test_write_paths.py`: the test of the protected paths' list, under decision 3 (S0001).
- `tests/domain/test_nested_claude_paths.py` and `tests/application/test_undo_nested_claude.py` (new): the pattern on both sides, the refusal and the undo (S0001).
- `docs/operator-guide.md`, `docs/project-guide/write-guard.md` and `docs/decisions.md`, from the story's docs criterion (S0001).

## Out of scope

- The kernel's write guard (`factory-confine`, `factory.domain.confinement`): Landlock only allows. Inside a folder that a write path opens, it cannot refuse a subfolder. So `src/.claude/` stays writable to the kernel under `src/*`, as `src/feature.md` is today, and the hook and the undo refuse it (decision 2).
- The agent's own Claude home, `~/.claude` (`/home/agent/.claude`): the image and the entrypoint already make it read-only to the agent (F0012-S0025, F0022).
- The shipped agents' rule R14, which names `.claude/` among the pipeline's own files: its words already cover every `.claude/`, and `tests/test_claude_agent_refusal.py` pins them (decision 4).
- A file or link named `.claude` itself, with nothing under it: the root's `.claude` is not protected that way either (decision 1).
- `claude/` without the dot, the shipped agents' folder in this repository: it stays the coder's.
- Every paid call: no story and no smoke test makes one.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The protected paths refuse a .claude folder at any depth

## The human's changes

None. Checked against `factory/pipeline.yml`: the coder writes `src/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`. No file under a nested `.claude/` exists in this repository (searched on 2026-10-19, `.venv`, `mutants` and `.git` left out), so no stage loses a file it writes today.

## Decisions taken for the human

1. The pattern is `*/.claude/*`, beside `.claude/*`, after the model of `feature.md` and `*/feature.md`. `matches_any` lets `*` cross `/`, so it matches a `.claude` segment at any depth below the root and only a whole segment. `src/.claudex/a`, `src/x.claude/a` and `claude/agents/coder.md` stay unprotected. A path that ends in `.claude` with nothing below it is not matched, as the root's `.claude` is not (S0001).
2. The kernel's targets stay as they are: Landlock cannot refuse inside an allowed folder. For a nested `.claude/` the refusal is the hook's for Claude Code runs and the undo's for every run, opencode's included. That is the same as for the root `.claude/` under a write path `*` today (S0001).
3. The leave to change `tests/domain/test_write_paths.py` (F0019 and earlier) beyond the standing leave: `test_the_protected_paths_are_the_engines_eleven_patterns` becomes `test_the_protected_paths_are_the_engines_twelve_patterns`, and its tuple gains `"*/.claude/*"` as the second item. Every other test in the module keeps its name and what it checks (S0001).
4. R14 in the seven shipped agents keeps its words. Its "and `.claude/`" names the folder without a place, and an agent that writes a nested one gets the refusal's own text: `<path> is owned by the human; a change there is a question.` (S0001).
