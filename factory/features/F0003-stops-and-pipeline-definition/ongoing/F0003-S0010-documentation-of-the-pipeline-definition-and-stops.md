---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Documentation after stops and the pipeline definition

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

This story repairs what F0003's stories left in the documentation, read as a whole. Each documenter wrote their own story's part correctly and judged the rest current for that story. Read as a whole, though, three things are missing or wrong. This is a documentation-only story: no code and no test changes. The tester writes no tests, the coder has nothing to build, and the work is the documenter's, from the docs criterion. F0002's acceptance noted that such a story still pays for every stage. If the human would rather make these edits by hand, or fold them into S0008 or S0009 when refining those drafts, this draft can be dropped.

What to repair:

- **`docs/operator-guide.md` has no section on the file the operator configures.** `factory/pipeline.yml` is the project's configuration (kept thing 7), but its keys and defaults are only in `docs/project-guide.md`, the guide for agents. That covers the quoted `contract`, `done: {}`, unknown keys refused, a given `project_commands` replacing the default set, the placeholders `{work_item}` and `{feature}`, the lease rule with its default arithmetic, every agent file a role needs, and `origin/main` as the only place it is read. Add a section "The pipeline definition" to the operator guide, beside "The agent files", for the person who writes the file:
  - a short example definition that loads,
  - the table of keys with their defaults,
  - the rules an operator most often meets (the stage `done`, the contract major, the lease rule),
  - a pointer to the project guide for the full list of faults.

  The section "The stop `pipeline_definition_invalid`" then points to this new section instead of the project guide for what to fix. The project guide keeps the code-facing parts (classes, methods, tests).
- **`docs/project-guide.md`, "Boundaries", lists the fields without `agent_definitions`,** which S0005 added (`src/factory/application/boundaries.py`). The section "The agent definition reader" names `Boundaries.agent_definitions`, so the two sections disagree. Add it to the list, in the dataclass's order.
- **`docs/project-guide.md`, "The pipeline loader", names `WritePathService.at`,** a class of F0004's draft S0003 that does not exist yet. Say instead that a reader of the definition at another commit (F0004's write paths) will parse it directly, without the loader, or drop the sentence until F0004 builds it.
- **`README.md`'s status sentence and the operator guide's opening list of built parts name nothing of F0003.** Add the stops of the repository, the machine and a work item, the factory log and the health status file, the pipeline definition with its reader, rules and loader, and the agent definition reader. Decided by the human on 2026-10-14, as the pre-check recommended: rather than growing the README's enumeration again, the README summarises the built parts instead of listing them, and the summary still names the stops and the health status file and points to the project guide (F0002's acceptance suggested this).

## Interface

None: no code changes.

## Acceptance criteria

1. `make check` stays green.
2. docs:
   - `docs/operator-guide.md` has a section on the pipeline definition, for its author. It gives an example definition that `RuamelPipelineDefinitionReader().parse` accepts, the keys with their defaults, the stage `done`, the contract major 1, the lease rule, that values are taken only in their YAML type and a write path must not be blank, that every stage other than `done` needs a `next` and a role or `approval: true`, and the pointer to the project guide's list of faults. The `pipeline_definition_invalid` section points to that new section, and the guide's opening list of built parts includes the F0003 parts.
   - `docs/project-guide.md`'s "Boundaries" list names `agent_definitions`, in the dataclass's order (`…, cost_reader, cost_writer, pipeline_reader, agent_definitions, clock, …`), and "The pipeline loader" no longer names `WritePathService`, which does not exist yet.
   - `README.md`'s status names the stops, the health status file and the pipeline definition, or summarises the built parts and points to the project guide.

## Demo

```bash
sed -n '/^### Boundaries/,/^## /p' docs/project-guide.md | grep -c agent_definitions
```
Expect: one line, a number of at least `1`.

```bash
grep -n "^## " docs/operator-guide.md | grep -i "pipeline definition"
```
Expect: at least one line naming a section on the pipeline definition, besides "The stop `pipeline_definition_invalid`".

```bash
grep -ci "health\|pipeline definition\|project.guide" README.md
```
Expect: one line, a number of at least `2`: the status names the health status file or the pipeline definition, or points to the project guide, beside the existing `docs/project-guide.md` line under "Where to look next".

## Log (append only)

1. 2026-10-14 human: created.
