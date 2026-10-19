---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 292
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-19T22:17:51.527921Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T22:13:35.506733Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T22:13:35.512982Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T22:13:56.109136Z'
  stage: intake
  run: f652d7693a714fdfbdebfcaad0594dc2
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T22:14:16.775852Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T22:16:08.496323Z'
  stage: tests
  run: 7a78d5eaab224c40909988148d41a6cd
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T22:16:28.924116Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T22:17:31.105626Z'
  stage: doing
  run: 2d4b3b3eca8640c480edc9b3698832c2
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T22:17:51.527921Z'
  stage: review
---

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
   - `docs/project-guide/README.md`, *The files*, the `watching.md` line: its sentence "It also names ..." gains `factory.adapters.preflight_stamp_file` after `factory.adapters.health_file`, `factory.application.dispatcher` after `factory.application.boundaries` and `factory.domain.tick_status` after `factory.domain.stop_table`, each in backticks, so the list keeps its order. The line keeps its domain, its existing modules, its `Sections:` list and its `Subsections other files refer to:` list as they are. No other line of the index changes.
   - `docs/decisions.md`, *The project guide lives in `docs/`*: the sentence "Since F0025-S0001 the guide is the folder `docs/project-guide/` (see *The project guide is an index and one file per domain*)." reads "Since F0025-S0001 the guide is an index and one file per domain (see *The project guide is an index and one file per domain*)." The section's first sentence and the dated F0011-S0005 entry stay as they are.
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
grep -c "Since F0025-S0001 the guide is an index and one file per domain" docs/decisions.md; grep -c "Since F0025-S0001 the guide is the folder" docs/decisions.md
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

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is right for a docs-only story. It names the two places that change (the `watching.md` line of `docs/project-guide/README.md`, one sentence of `docs/decisions.md`). I checked both exist as described (README line 19, decisions.md line 23).
   Criteria: criterion 1 (nothing under src/tests/image/template/demo/claude changes) and criterion 2 (`make check` green) are each checkable. The docs criterion gives the exact insertions, the exact replacement sentence, the lines that stay as they are, the 600-line limit and `documents ok`. The story states no limit, error or rejected input, so no failing side needs a criterion. The three module names are absent from the guide today, so the insertions are real.
   Smoke test: the commands are runnable and each Expect line is checkable (`True`/`0`/`True`; `1` and `0`; `0`; `documents ok`).
   Architecture: no code layer is touched, and the guide's index is where CLAUDE.md sends agents.
   Scope: it fits F0025, whose goal is the guide as index plus one file per domain. The story keeps the new `factory.entry.health` content out. Nothing in the feature's Out of scope is touched.
4. factory: started tests as self.
5. tester: No tests written. This story only changes docs, and its Interface says no test changes.
   criterion 1 (nothing under src/, tests/, image/, template/, demo/ or claude/ changes): no test function; the tester changed nothing under those folders, as this entry confirms. The smoke test's `git diff --name-only origin/main -- src tests ...` checks it.
   criterion 2 (`make check` stays green): no test function; the factory's checks cover it. I ran `make test` once and it was green, with no new red tests (coverage 99.12 %). `make lint` was green.
   criterion 3 (docs): no test function; the documenter does this, and the docs stage's `make documents` and the smoke test check it. A test of these doc sentences would be a change under `tests/`, which criterion 1 forbids.
   Files created: none. Modules the test runner could not import: none. The coder has no red tests to turn green on this branch.

   `lint`: lint: green (0.0 s)
   `test`: test: green (43.8 s)
6. factory: started doing as self.
7. coder: No code written. This story only changes docs. Its Interface says no module under `src/factory/` and no test changes, and the tester left no red tests. Following criterion 1, I changed nothing under src/, tests/, image/, template/, demo/ or claude/. The working tree holds only the factory's `.costs.jsonl` sidecar.
   Main choice: leave the two doc edits (the `watching.md` line of `docs/project-guide/README.md` and the sentence in `docs/decisions.md`) to the documenter, as the Interface and CLAUDE.md say. I rejected making them here, because the coder does not write the guide or the decision log.
   Refactor: no diff, so nothing to refactor.
   Noticed, not touched: nothing.
   `make check`: check: green (test: green, coverage 99.12 %).

   `check`: check: green (not run again: passed on tree 3523d622cd0b at 2026-10-19T21:56:48Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
