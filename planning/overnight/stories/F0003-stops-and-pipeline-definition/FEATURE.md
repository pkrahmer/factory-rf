# Stops and the pipeline definition

## Goal

Every stop of the factory has one destination, and the pipeline definition is checked when it loads. A stop of one work item is posted once on that work item's pull request, with the draft pull request opened first when it has none; a stop of the repository or the machine fails the container's health status and is written as a time-stamped line to the container's output and the factory log. The pipeline definition (`factory/pipeline.yml`) is a Pydantic schema with defaults, read with ruamel.yaml and validated when it loads, against the contract version, the rules across its keys and the installed agents; an invalid one is a reported stop that names the fault, not a crash on every tick. Done when a work item's stop reaches its pull request exactly once, also after a kill between the post and the write of its state; when a repository or machine stop sets the health status and writes a time-stamped line; and when each validation of the pipeline definition (a missing key without default, a `next` naming no stage, a role without write paths or without an installed agent, an unknown major contract version, `time_limit`s that do not fit inside `lease_duration`) refuses its case with a stop that names it.

## Scope

- The health status of the repository and the machine: `RepositoryStop` and `HealthStatus`, the file the health check will read, set and cleared by `StopService`, one stop per reason (ST3.4, R27).
- The clock, the factory log (every line carries a UTC time stamp) and `Boundaries`, the holder of the interfaces that wiring hands to services.
- A work item's stop posted on its pull request through the hosting service's keyed post, the draft pull request opened first when there is none, a repeat after a kill posting nothing (ST3.2, GH3.4, R27).
- The pipeline definition schema with its defaults (stages, roles with their write paths, `lease_duration` and `time_limit`, project commands, the attempts cap, the crash cap, the contract version) and its ruamel.yaml reader (R30, R13).
- Load-time validation (ST8.1 to ST8.5, GH1.4, R21): missing keys without default, unknown keys, a `next` naming no stage, a role without write paths or without an installed agent, an unknown major contract version, `time_limit`s that do not fit inside `lease_duration`; each refusal a reported stop through `StopService`.
- `PipelineLoader`, which reads the definition at a git ref, and the agent definition reader that tells which agents are installed.

## Out of scope

- The handlers that post questions, answers, notes and send-backs, and the texts of those posts: F0005 to F0009. This feature only posts the text a caller hands to `StopService`.
- The health check command, the container's restart policy, the entrypoint's own stops and the wiring of the concrete adapters: F0010 (ST3.3).
- The keys an agent file may hold and the refusal of keys the agent runtime does not apply: F0010 (SI4). The agent reader here reads `model`, `tools`, `effort` and `budget_usd` and ignores other keys.
- The table of all stops with their destinations: F0011 (ST3.5).
- Calling the loader at the start of a tick, and what the tick does after a refusal: F0006.
- A writer for the pipeline definition: no story writes it.

## Stories

The order is the story numbers. A later number may start first if it is the only one moved to `ongoing/`.

- S0001 — Repository and machine stops: health status and time-stamped lines
- S0002 — Work item stops on the pull request, posted once
- S0003 — The pipeline definition schema and its defaults
- S0004 — Loading the pipeline definition: installed agents and a reported stop
- S0005 — Load-time rules of the pipeline definition

## Decisions taken for the human

Product decisions taken while writing the stories, for the human to review in one place. Each names where it was taken.

1. The health status holds at most one stop per reason. Raising a stop whose reason is already there replaces it where it stood (the latest detail and time), a new reason is appended, and every raise writes one line. (S0001, story text)
2. A stop of the repository or the machine is written to both destinations, the health status and the time-stamped line, and the failure of one destination never loses the other: both are tried and the first `OSError` is raised afterwards. (S0001, story text)
3. Clearing a stop writes the line `stop cleared <reason>`; clearing a stop that is not there writes nothing, so a tick that finds the fault gone every time is silent. (S0001, story text)
4. The time stamp is `YYYY-MM-DDTHH:MM:SSZ` in UTC with whole seconds (the fraction is dropped), and a text of several lines gets the stamp on every line. (S0001, story text)
5. A stop of a work item with a blank title, branch or text is refused, so no stop is posted without saying what each possible answer will do. (S0002, story text)
6. A stop is a keyed post: the key alone decides whether it repeats. The same key never posts twice whatever the text; another kind or another `n` posts again. (S0002, story text)
7. A stop without a recorded pull request number reuses the open pull request of its branch, and opens a new draft pull request when the only one was closed. `opened` in the result is true whenever the number was not in the state, whether the call created the pull request or found it, so the caller records it. (S0002, story text)
8. The pull request opened for a stop says in its description that the factory opened it to report a stop, and is a draft: the factory's turn, not the human's. (S0002, story text)
9. The pipeline definition refuses unknown keys at every level, so a misspelt key is a fault and never silently ignored; a contract written as an unquoted number (`1.0`) is refused because YAML would read it as a number. (S0003, story text)
10. A `project_commands` given in the file replaces the default commands (`check`, `lint`, `test`, each 10 minutes) as a whole; it does not merge with them. (S0003, story text)
11. A text with several faults is refused once, and its `fault` lists all of them joined by `; `, so the operator fixes the definition in one pass. A key that repeats in the YAML is a fault, not a silent override. (S0003, story text)
12. Command names in `project_commands` use the same name pattern as stages and roles (`^[a-z][a-z0-9-]*$`). (S0003, story text)
13. The loader reads the definition at a git ref, `origin/main` by default, never from the work tree; a refusal goes only to the health status and the factory log, never to a pull request; a later successful load clears the stop. (S0004, story text)
14. The agent of every role in `roles` must be installed, also a role that no stage uses; an unavailable agents directory is the same stop, `pipeline_definition_invalid`, with the fault `agent home unavailable`. (S0004, story text)
15. An agent file needs `model`, `tools` and `budget_usd` (greater than 0); `effort` is optional. Other keys are ignored until F0010 decides which keys the runtime applies. (S0004, story text)
16. Any minor version of contract major 1 is read; the contract must look like `<digits>.<digits>`. A stage named `done` must exist, with no role and no `next`; the names `human`, `factory` and `question` are reserved for stages and roles. (S0005, story text)
17. A role's `time_limit` plus the `time_limit` of every listed check and every listed report (a command listed twice counts twice) must not exceed the role's own `lease_duration`; a total equal to the lease is accepted. With the defaults (40 minutes for an agent run, 10 for a project command), a stage with two checks and one report does not fit in 60 minutes, and a project must lower the limits or raise the lease. (S0005, story text)
