---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 295
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-19T22:37:49.377902Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T22:37:12.252821Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T22:37:12.258996Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T22:37:29.049172Z'
  stage: intake
  run: 06f44ed3ae40476786d76baed81414d9
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T22:37:49.377902Z'
  stage: tests
---

# The guide's index names the project agents and the patient runs modules

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0025 made the project guide an index, `docs/project-guide/README.md`, and one file per domain. The index's section *The files* is how an agent whose story touches a module finds the file to read. F0025-S0002 and F0025-S0004 put every module a file names by its full dotted name on that file's line. Two stories of other features have since written two modules into domain files without adding them to the index. F0022-S0001 wrote `factory.application.project_agents` (`ProjectAgentDefinitions`) into `agents.md`, *The agent definition reader*. F0020-S0007 wrote `factory.application.provider_limits` (`PatientRuns`) into `stages.md`, *Starting a stage*. An agent that searches the index for either module name finds nothing. This story adds the two modules to the lines of their files and changes nothing else. Whether a lasting check should keep the index complete is the human's question, listed in F0025-A0003, and this story does not settle it.

## Interface

None: no module under `src/factory/`, no test, no image, template, demo or agent file changes. The documenter changes two lines of `docs/project-guide/README.md`, *The files*: the `agents.md` line and the `stages.md` line.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/project-guide/README.md`, *The files*, the `agents.md` line: its sentence "It also names ..." gains `factory.application.project_agents` after `factory.adapters.validation_faults`, in backticks, so that the list keeps its order (adapters, then application, then domain).
   - The same section, the `stages.md` line: its sentence "It also names ..." gains `factory.application.provider_limits` after `factory.adapters.pipeline_yaml`, in backticks.
   - Each of the two lines keeps its domain, its existing modules, its `Sections:` list and its `Subsections other files refer to:` list as they are. No other line of the index changes, and no other file of the guide changes.
   - No file of the guide passes 600 lines. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
uv run -q python - <<'EOF'
import re
from pathlib import Path

index = Path("docs/project-guide/README.md").read_text(encoding="utf-8")
the_files = index.split("## The files")[1].split("\n## ")[0]
lines = {m.group(1): line for line in the_files.splitlines() if (m := re.match(r"- `([^` ]+)`", line))}
print("`factory.application.project_agents`" in lines["agents.md"].split("Sections:")[0])
print("`factory.application.provider_limits`" in lines["stages.md"].split("Sections:")[0])
print(sum(f"`factory.application.{m}`" in line for m in ("project_agents", "provider_limits") for line in the_files.splitlines()))
print(max(len(p.read_text(encoding="utf-8").splitlines()) for p in Path("docs/project-guide").glob("*.md")) <= 600)
EOF
```

Expect: four lines, `True`, `True`, `2` and `True`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- docs README.md
```

Expect: two lines, `0` and `docs/project-guide/README.md`

```bash
uv run -q python -m factory.entry.check_documents
```

Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is right for a docs-only story. It names exactly the two lines of `docs/project-guide/README.md`, *The files*, that change (`agents.md` at line 14, `stages.md` at line 18). I checked that both lines exist, and that `factory.application.project_agents` and `factory.application.provider_limits` exist under `src/factory/application/`. No comment in the Interface states a behaviour.
   Criteria: the three are testable and each is verified by a command. Criterion 1 is checked by the `git diff --name-only` smoke test, 2 by `make check`, and 3 by the smoke test and `check_documents`. The ordering rule (adapters, then application, then domain) fits the current `agents.md` line: `validation_faults`, then the new `project_agents`, then `domain.provider_limits`. On the `stages.md` line the new module goes after `pipeline_yaml` as stated. The "keeps as they are" clauses and the 600-line limit have a check each. There is no failing-side rule to test, because the story adds no code.
   Smoke test: the commands are runnable. The Python snippet prints four lines and its `Expect:` states them (`True`, `True`, `2`, `True`). The second block expects `0` and `docs/project-guide/README.md`. The third expects `documents ok`.
   Architecture: it fits. The documenter writes only `docs/*`, and no layer is touched.
   Scope: it is inside F0025's purpose, the index naming each module of the guide's files. It is not in "Out of scope", because it adds no lasting test and no rewording. The story leaves the question of a lasting check of the index's completeness open for the human (F0025-A0003).
4. factory: started tests as self.
