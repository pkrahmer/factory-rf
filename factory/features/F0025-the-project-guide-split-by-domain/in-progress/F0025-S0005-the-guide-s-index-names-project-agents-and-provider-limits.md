---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-19T22:37:12.258996Z'
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
