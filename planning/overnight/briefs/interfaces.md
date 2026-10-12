# Brief: the interface sheet (Phase 2, serial step 2)

## Goal

Fix the module layout and the names and signatures of every DTO and interface operation that more than one feature uses, so that parallel story drafters copy names from one place and invent none across a feature boundary.

## Inputs (read these; nothing else)

- `C:\Dev\Projects\factory-rf\planning\overnight\skeleton.md`: the features, their scope and proposed stories. The sheet serves exactly these.
- `C:\Dev\Projects\factory-rf\planning\overnight\skeleton-answers.md`: the main session's answers to the skeleton's open questions. They bind you (for example: keyed posts, the `handed_over` field, no tick lock, the restore of the checkout).
- `C:\Dev\Projects\factory-rf\planning\overnight\fault-paths.md`: the injection test names, for the injection points the wrappers need.
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`, sections 2, 4 (R1 to R38) and 5, and the appendix (names).
- `C:\Dev\Projects\factory-v2\planning\decisions\005-v1-1-architecture-choices.md`, `006-v1-1-open-points.md`, `007-overnight-defaults.md`.
- `C:\Dev\Projects\factory-v2\planning\v1.1\v1-style-facts.md` (v1's code style, checks and data model: a reference for what fields v1's work item carries).
- `C:\Dev\Projects\factory-rf\CLAUDE.md` and `pyproject.toml` (package `factory`, the four layers, the dependencies already declared: pydantic, PyGithub, ruamel.yaml, python-frontmatter; nothing else may be assumed).
- `C:\Dev\Projects\factory-demo-todo\factory\features\F0001-todo-service\done\F0001-S0001-domain-model-and-in-memory-repository.md`: how an exact `## Interface` section looks.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\interfaces.md`, with:

- `## Summary` (at most ten lines).
- `## Package layout`: every module under `src/factory/` by layer (`factory.domain.*`, `factory.application.*`, `factory.adapters.*`, `factory.entry.*`), one line each: its purpose and the feature that creates it. Test modules mirror it under `tests/<layer>/`.
- `## DTOs`: every Pydantic model used by more than one feature, as Python code blocks with module path, class name, fields with types and defaults, and validators stated as rules in a comment. Include at least: the work item's state (front matter: stage, blocked, round, attempts, crashes, comment ids read, the journal entry list of decision 007 question 2, the claim's instance name and start time), a journal entry, a cost record (R24: started and completed states, duration, end reason, cost and tokens as known or unknown, image), the generic check result (R8), the pipeline definition (R30: contract version, stages, roles, write paths, caps, `lease_duration`, `time_limit`s, crash cap with defaults), the agent run request and result, the pull request view and comment (R10), the stop (R27: work-item stop against machine or repository stop).
- `## Interfaces`: each as a `typing.Protocol` or `abc.ABC` in `factory.application`, with every operation's exact signature, its DTOs and the error type it raises. The hosting service (R10, exactly its operations), the git wrapper, the agent runtime, the project commands (decision 007 question 1: only operations a story in the skeleton uses), and the readers and writers of R13 (one reader and writer class per format: pipeline definition YAML, work item Markdown with front matter, cost record JSON lines). Name the first implementation of each in `factory.adapters` and the one fake of the hosting service.
- `## Errors`: one hierarchy of exception types, with which layer raises each, and which are counted errors (R28), stalls and crashes (handover section 2).
- `## The journal`: the visible prefix `<number>. <date> <speaker>: <text>` and the data list in the front matter (decision 007, question 2).
- `## The lease clock`: decision 007, question 4, as the function signatures that implement it.
- `## Names`: a table of every name in the sheet that renames a v1 word (glossary appendix), so drafters can check.
- `## Open questions` and `## Sources`.

## Rules

- Glossary names only. No layer names of projects inside the factory's DTOs (R8). No `dict[str, Any]` across a function boundary (R7).
- Only what the skeleton's stories need; mark each operation with the feature that first needs it.
- Every operation's failing side is named (its error type), so the drafters can write a criterion for it.
- Interfaces live in `factory.application`; concrete classes in `factory.adapters`; wiring only in `factory.entry`.

## Not

- No git commands. No file other than the output. Do not write stories.

## Reply

The Summary and the Open questions, nothing else.

Model: opus.
