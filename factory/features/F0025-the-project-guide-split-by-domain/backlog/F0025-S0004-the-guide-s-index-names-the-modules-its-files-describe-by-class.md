# The guide's index names the modules its files describe by class

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0025 made the project guide an index, `docs/project-guide/README.md`, and one file per domain. The index's section *The files* is how an agent whose story touches a module finds the file to read. F0025-S0002 put on each file's line every module that the file names by its full dotted name. Three modules are described in `watching.md` only by their classes, so no index line names them: `factory.application.dispatcher` (`Dispatcher`, the dispatch step of the tick and the error count, `watching.md` lines 84 to 94), `factory.domain.tick_status` (`TickStatus`, the same paragraphs) and `factory.adapters.preflight_stamp_file` (`JsonPreflightStampFile`, the JSON stores in *Stops, the clock and the factory log*). An agent that searches the index for one of these module names finds nothing. Separately, the decision log's *The project guide lives in `docs/`* now says the same thing twice. F0025-S0002 changed its first sentence to name `docs/project-guide/`, but its last sentence still reads "Since F0025-S0001 the guide is the folder `docs/project-guide/`". This story adds the three modules to the `watching.md` line and rewords that one last sentence. It changes no code, no test, no `## ` heading and no other passage. `factory.entry.health` (`factory-health`) is described in the operator guide and in no file of the project guide; describing it there would be new content, which this story leaves to a story that changes the module.

## Interface

None: no module under `src/factory/`, no test, no image, template, demo or agent file changes. The documenter changes one line of `docs/project-guide/README.md` (*The files*, the `watching.md` line) and one sentence of `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/project-guide/README.md`, *The files*, the `watching.md` line: its sentence "It also names ..." gains `factory.adapters.preflight_stamp_file`, `factory.application.dispatcher` and `factory.domain.tick_status`, each in backticks. The line keeps its domain, its existing modules, its `Sections:` list and its `Subsections other files refer to:` list as they are. No other line of the index changes.
   - `docs/decisions.md`, *The project guide lives in `docs/`*: the sentence "Since F0025-S0001 the guide is the folder `docs/project-guide/` (see *The project guide is an index and one file per domain*)." reads "Since F0025-S0001 it is an index and one file per domain (see *The project guide is an index and one file per domain*)." The section's first sentence and the dated F0011-S0005 entry stay as they are.
   - No file of the guide passes 600 lines. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
uv run -q python - <<'EOF'
import re
from pathlib import Path

index = Path("docs/project-guide/README.md").read_text(encoding="utf-8")
the_files = index.split("## The files")[1].split("\n## ")[0]
lines = {m.group(1): line for line in the_files.splitlines() if (m := re.match(r"- `([^` ]+)`", line))}
wanted = ("factory.adapters.preflight_stamp_file", "factory.application.dispatcher", "factory.domain.tick_status")
print(all(f"`{m}`" in lines["watching.md"].split("Sections:")[0] for m in wanted))
print(sum(f"`{m}`" in line for m in wanted for name, line in lines.items() if name != "watching.md"))
print(max(len(p.read_text(encoding="utf-8").splitlines()) for p in Path("docs/project-guide").glob("*.md")) <= 600)
EOF
```

Expect: three lines, `True`, `0` and `True`

```bash
grep -c "Since F0025-S0001 it is an index and one file per domain" docs/decisions.md; grep -c "Since F0025-S0001 the guide is the folder" docs/decisions.md
```

Expect: two lines, `1` and `0`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l
```

Expect: `0`

```bash
uv run -q python -m factory.entry.check_documents
```

Expect: `documents ok`

## Journal
