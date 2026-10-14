---
stage: demo
pr: 51
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
2. intake: accepted
   - Interface: "None: no code changes" is consistent with a documentation-only story. No Interface comment states a behaviour, so no criterion is missing.
   - Criteria: only `make check` green and the `docs:` criterion. The docs criterion names the concrete checks: the example parses with `RuamelPipelineDefinitionReader().parse`, the keys with their defaults, the `done` stage, contract major 1, the lease rule, strict YAML types, blank write paths, `next` and a role or approval, the pointer to the faults list, the `agent_definitions` field order, and `WritePathService` removed. No rule states a limit, so there is no failing side to cover. The documenter judges the docs criterion, and the tester has nothing to write.
   - Demo: all three commands are runnable (sed/grep over existing files), and each Expect line is checkable by a count or a matching line. The README count of at least 2 is loose but checkable.
   - Architecture: no code, no layer touched. The edits are confined to README.md, docs/operator-guide.md and docs/project-guide.md, which the documenter owns.
   - Scope: within F0003 (listed as S0010 in FEATURE.md) and outside no "Out of scope" item. The decision on the README summary is recorded as decision 20.
3. tester: no tests written, by design. This story only changes documentation: the Interface is "None: no code changes", and the Assignment says the tester writes no tests.
   - criterion 1 (`make check` stays green): the factory checks this itself. No test is needed, and there is no new code to make one fail.
   - criterion 2 (docs): the documenter judges it from the docs criterion, and the Demo's sed/grep commands check it. It describes no runtime behaviour, so pytest cannot test it.
   Files created: none. Modules the test runner could not import: none. Nothing was added, so `make test` is unchanged from main and was not run for a red state. `make lint` is green and the working tree is clean.
   Rejected: tests that grep README.md or docs/ for the required sections or names. They would turn prose into a test contract, which is beyond what the Assignment asks for, and they would put criteria in the tests (R4). Open: nothing. The coder has nothing to build, so the work goes on to the documenter.

   `make lint`: lint: green
   `make test`: test: green
4. coder: nothing to build, by design. This story only changes documentation: the Interface is "None: no code changes", the tester wrote no tests, and the Assignment gives the work to the documenter (README.md, docs/operator-guide.md, docs/project-guide.md). The coder does not write those files.
      - No source or test changes and no commits. I ran `make check` on the unchanged branch and it is green (coverage 99.72 %).
      - No refactor: there is no diff to read.
      - Rejected: editing the three docs files here. They are outside the coder's lane, and CLAUDE.md gives them to the documenter stage.
      Open: everything in the docs criterion, for the documenter. That covers the operator guide's section on the pipeline definition and its pointer from `pipeline_definition_invalid`, the F0003 parts in the opening list, `agent_definitions` in the project guide's "Boundaries", `WritePathService` removed from "The pipeline loader", and the README status summary.

      `make check`: check: green

   `make check`: check: green
5. reviewer: no findings.
      - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the ticket. That matches a documentation-only story, whose Interface is "None: no code changes".
      - Acceptance criteria: criterion 1 (`make check` stays green) is met. The coder's entry says `make check` is green on the unchanged branch (coverage 99.72 %), and the factory recorded green after the coder. Criterion 2 (docs) is the documenter's to write next. No pytest test can cover it, and the tester explained why it wrote none. The Interface states no rule or limit, so no failing side goes untested.
      - Architecture, security and quality: nothing to judge, because no code, tests, dependencies or check markers changed.
      - Ticket hygiene: the tester and coder entries both explain the main decision (no tests and no code, by design) and what they rejected (prose-grepping tests, and the coder editing docs outside its lane). The Assignment matches what was built, which is nothing yet. The docs criterion still says everything the documenter must write: the operator guide's pipeline-definition section with an example that parses, the keys and defaults, the `done` stage, contract major 1, the lease rule, strict YAML types, blank write paths, `next` plus a role or approval, the pointer to the faults list and the `pipeline_definition_invalid` pointer; the F0003 parts in the opening list; `agent_definitions` in "Boundaries" in the dataclass's order; `WritePathService` removed from "The pipeline loader"; and the README status summary.
      Open: the whole docs criterion, for the documenter.
6. documenter: wrote the three repairs; no findings against the code. `make check` is green (coverage 99.72 %).
   - `docs/operator-guide.md`: added "The pipeline definition", before "The agent files". It has an example that `RuamelPipelineDefinitionReader().parse` accepted when I ran it, the keys with their defaults, and the stage and role fields. It also states the rules an operator meets: `done: {}`, contract major 1, `next` plus a role or `approval: true`, the lease arithmetic (40+10+10=60 fits, 70 does not), strict YAML types, a write path that is not blank, unknown keys refused, and `project_commands` replacing the default set. It points to the project guide's "The rules of the definition" for the full list of faults. The `pipeline_definition_invalid` table row now points to the new section. The opening list of built parts now names the F0003 parts: factory log, health file, the stops, the pipeline definition with its reader, rules and loader, and the agent definition reader.
   - `docs/project-guide.md`: "Boundaries" now lists `…, cost_reader, cost_writer, pipeline_reader, agent_definitions, clock, …`, the dataclass's order (it had `pipeline_reader` before the cost fields). In "The pipeline loader", `WritePathService.at` is replaced by a sentence that F0004's write paths will parse the definition directly with `pipeline_reader`. The loader paragraph also points to the rules section.
   - `README.md`: the status sentence is now a summary of the built parts. It names the stops, the factory log and health status file, and the pipeline definition with its agent files. It points to `docs/project-guide.md`, as decision 20 says.
   - Cross-read and found current: the rest of the operator guide (agent files, stops, story check) and the project guide's pipeline definition and agent reader sections, against `boundaries.py` and the pipeline YAML example.
   - Ran the three demo commands: `agent_definitions` count in Boundaries is 1, the new section heading is present, and the README match count is 2.
   - Stale but not touched: the README and operator guide still describe `factory-check-story` as the only command, which is true. The guide's line "The documenter stage extends this" is unrelated and left as is.

   `make check`: check: green
