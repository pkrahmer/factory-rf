# Brief: improve feature F0010 after audits\F0010-1.md (Phase 3/4)

## Goal

Fix every finding of the reports below in feature F0010's files, or defer it with a reason, and record each in a handling table.

## Inputs (read these; nothing else unless a finding names it)

- The reports: `C:\Dev\Projects\factory-rf\planning\overnight\audits\F0010-1.md`, all findings, including its section on questionnaire answers to apply (applied in full) and any exact replacement texts.
- The feature folder: `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0010-machine\`.
- `C:\Dev\Projects\factory-rf\planning\overnight\interfaces.md` and `skeleton.md`.
- `C:\Dev\Projects\factory-rf\planning\overnight\briefs\draft-template.md`: the format rules a story must keep (sections "The format v1 requires", "What makes a story pass v1", "From conditions to criteria").
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`, the sections a finding cites.
- The human's answers that win over the working answers: `C:\Dev\Projects\factory-rf\planning\questionnaires\01-working-answers.md` (section "Answers") and `C:\Dev\Projects\factory-v2\planning\decisions\008-v1-1-starts-fresh.md`. The interface sheet's last section of changes wins over its body.
- What earlier features built or will build, which the feature must import and never redefine, in the built spelling: `C:\Dev\Projects\factory-rf\src\factory\` (the modules a finding names), `tests\conftest.py`, `docs\project-guide.md`, and every earlier feature's folder under `C:\Dev\Projects\factory-rf\factory\features\` (its `FEATURE.md` and its stories; their names and story numbers are binding). `pyproject.toml` already declares the console scripts, each `factory.entry.<module>:main` with `main() -> int` and every argument defaulted.
- `C:\Dev\Projects\factory-rf\CLAUDE.md` (Architecture: interfaces are ABCs their implementations inherit; Tests: `mypy --strict`, `type[BaseModel]` for refused fields, low-entropy hex, every limit tested on both sides).

## Output

- The changed files in the feature folder (FEATURE.md, drafts/).
- `C:\Dev\Projects\factory-rf\planning\overnight\audits\F0010-1-handling.md`: a table, one row per finding: report and number, severity, "fixed" with the story and criterion numbers changed (old wording → new wording for every changed criterion), or "deferred" with the reason.

## Rules

- Keep every rule of the format: the two closing criteria, numbering 1 to n without gaps, `Expect:` after every Demo block, no headings in fences, the log line `1. 2026-10-12 human: created.`, no front matter.
- Never weaken a criterion below its handover condition to make a finding go away.
- A story that grows beyond 26 criteria is split into two stories with consecutive ids; renumber the later stories of the feature and update `FEATURE.md`'s Stories list.
- Names only from the interface sheet and the glossary. If a finding needs a change to the interface sheet, defer it with "needs interfaces.md: <what>".

## Not

- No git commands. No file outside the feature folder and the handling file.

## Reply

At most 15 lines: counts fixed and deferred, every criterion whose meaning changed (story and number), and every "needs interfaces.md" item.

Model: sonnet.

## The human's answers of 2026-10-14 (win over the report's options)

The human answered the four findings the audit left for them. Apply each in full, record each as a decision in F0010's `FEATURE.md` ("the human, 2026-10-14"), and give each its criteria on both sides:

- Finding 19 (`/state`): `/state` stays `0755 factory:factory`. The run files the agent must read (instructions, guard settings, hook settings) go to a separate directory that the agent can read but not write, for example `/state/runs`, mode `2750`, group `factory-work`; `ClaudeCodeRuntime` gets that directory as its state directory. Static criteria for both modes.
- Finding 33 (project commands as the factory's user): not built now. Record the gap as left for v2 in `docs/decisions.md` and in the operator guide (the docs criterion): the project commands run agent-written code as the factory's user, which can read the token file.
- Finding 34 (`FACTORY_AGENT_USER` unset): the preflight fails with an item `agent-user` when `agent_user` is `None` and the token file exists; it passes when the agent user is set, and when no token file exists (tests, local runs). Criteria for all three.
- Finding 18 (image identity): the Dockerfile writes a fresh generated id at build time (for example from `/proc/sys/kernel/random/uuid`) to `/opt/factory/image-id`; the settings read the image identity from that file, and `FACTORY_IMAGE` becomes a label only. Criteria: the identity is read from the file; a missing or empty file is refused.
- Finding 44 (`image/secrets/` in `.gitignore`): done by the human; the operator guide says the token file there is ignored by git.
