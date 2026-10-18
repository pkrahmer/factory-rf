# Brief: draft F0015, the tiny story's findings, for v1 to build

## Goal

Write the feature `F0015-the-tiny-storys-findings` and its stories so that v1 can fix, before the shakedown run (plan step 4), the three faults v1.1's first real run found on 2026-10-18. The run: the tiny story F0099-S0001 on `pkrahmer/factory-demo-todo`, instance `shakedown` under Docker Desktop, image built from factory-rf `7432a942`. It went through every stage to the approval, was sent back twice, and on the second send-back the coder's 1-minute `time_limit` killed its run under `sudo` (a stall, then a passing retry).

## Inputs (read these first)

- The night log's rows of 2026-10-18 from "Instances rebuilt" on: `C:/Dev/Projects/factory-rf/docs/runs/2026-10-12-overnight/night-log.md` (the three findings, verbatim).
- The plan: `C:/Dev/Projects/factory-rf/planning/overnight/restructure-after-f0011.md`, step 4.
- For finding 1: the cost records and their writer (`src/factory/domain/cost_records.py`, `src/factory/adapters/cost_records_jsonl.py`, `src/factory/application/costs.py`, how a run id is made), the project template (`template/`, its `Makefile` if any, and how a new project gets its make targets), the todo demo's source project (`demo/todo-service/project/Makefile`, its `secrets` target), factory-rf's own `Makefile` `secrets` target (the human's file), and `docs/project-guide.md` on the project commands and the cost records.
- For finding 2: `image/compose.yml`, `image/Dockerfile`, `image/entrypoint.sh`, `src/factory/adapters/process.py` (`run_process`), `src/factory/adapters/claude_runtime.py` (the `sudo ... timeout --signal=KILL` command line and the login shell), `tests/test_compose*.py`, `tests/test_image*.py`, and the operator guide's parts on the container and on a `time_limit` under `sudo`. What was seen: after the kill, `ps` in the container showed `[claude] <defunct>` owned by `agent`, its parent PID 1, which is `python -m factory.entry.run` (the image has no init process).
- For finding 3: the stage protocol (`src/factory/application/stage.py`, `costs.py`, the `begin` of a cost record and when the factory commits the sidecar `.costs.jsonl`), and the coder's words in the run: "the factory's cost log, `factory/features/F0099-tiny/in-progress/F0099-S0001-a-greeting.costs.jsonl`, shows as modified in the working tree." Find out from the code whether that is a fault (an agent sees a dirty file of the factory's, and the undo or the guard could treat it as the agent's write) or expected (the record of the running run, written before the agent starts and committed after). If it is expected and harmless, make it a documentation point and say so; if it is a fault, a story.
- The forms and rules v1 applies: `factory/TICKET.md`, `factory/FEATURE.md`, `factory/stages.yml` (write paths: the coder writes `src/*`, `image/*`, `template/*`, `claude/*`, and also check whether `demo/*` is in any write path; the tester `tests/*`; the documenter `README.md` and `docs/*`); v1's role files under `C:/Dev/Projects/factory/claude/skills/`; `CLAUDE.md`; `planning/lessons-for-the-skills.md`.
- How a feature passes: `factory/features/F0014-the-first-start-findings/FEATURE.md` and its stories in `done/`, and its `ACCEPTANCE.md`: six of its nine human answers fixed contradictions in the drafted text (a test the domain refuses, a demo naming a module nobody made, a `noqa` a structural test forbids, an equality against a post that always carries the marker). Check every drafted test and Demo against the built code before you finish.

## The content (the session's proposals, to be confirmed by the human)

1. The run ids must not turn a project's `make check` red. Prefer the solid fix: the projects the factory sets up leave out the factory's own `*.costs.jsonl` from their secrets scan (the template's and the todo demo's `secrets` target), since the file holds run metadata, not secrets; say whether the factory should also stop writing hex-only ids (for example a prefix), and recommend one. factory-rf's own `Makefile` is the human's: give its line as "The human's change", if it needs one. The todo demo on `pkrahmer/factory-demo-todo` already has the human's fix (`make secrets` leaves out `.*\.costs\.jsonl`); the demo's source in factory-rf should match it.
2. A killed agent run leaves no zombie: the container gets an init process that reaps orphans (`init: true` in `image/compose.yml` works under Docker and under Podman's docker-compose provider), or the factory reaps; recommend one, with a test of the compose file and, if it can run in the test suite, a test that a killed child's orphan is reaped. Say what the guide must add.
3. Finding 3 as the code shows it (see above).

## Rules for the split

- One story is one coder's work within $4 and a 60-minute lease. Documentation-only items may be one story whose coder changes nothing and whose docs criterion carries the text.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a Demo's `Expect:` met exactly by the built code, no doubled `-q`; every file a Demo or a test names exists or is made by the story.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/stages.yml`, `security/*`, and `demo/*` if no stage writes it) is "The human's change before S000N" in FEATURE.md, with exact lines.
- A story that changes tests another story wrote names them exactly, and FEATURE.md gives the leave as a decision.
- No word of `GLOSSARY_FORBIDDEN` outside a `## Replaced from v1` section in the documents. No secret-like key with a value in a story's text (detect-secrets scans it), and no 32-character hex value: give such values as prose.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0015-the-tiny-storys-findings/FEATURE.md` (Goal, Scope, Out of scope, Stories in build order, the human's changes, Decisions taken for the human with their source) and the stories under its `drafts/` as `F0015-S000N-<slug>.md`.

## Not

No git commands. No file outside `planning/overnight/stories/F0015-the-tiny-storys-findings/`. Do not start sub-agents. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and leave nothing behind.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human, what finding 3 turned out to be, and anything you could not place.
