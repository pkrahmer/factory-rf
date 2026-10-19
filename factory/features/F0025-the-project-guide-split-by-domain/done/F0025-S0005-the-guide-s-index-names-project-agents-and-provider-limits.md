---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 295
comments_read: []
handed_over: approval
claim: null
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
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T22:38:53.368946Z'
  stage: tests
  run: 455fd3c2a2784ad18cee3080c1bf90b1
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T22:39:13.813057Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T22:41:10.029802Z'
  stage: doing
  run: 0e7fc979e4754e1b812425b73d7639cd
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T22:41:30.432793Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T22:41:54.803027Z'
  stage: review
  run: 9c27616d6cf94b85a18b4a865b732f76
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T22:42:14.966939Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T22:42:32.512280Z'
  stage: docs
  run: 276bca75576a49dc8590ca476655a01b
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T22:42:52.643338Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T22:43:15.057097Z'
  stage: smoke-test
  run: d47e08e6943a43d0aae639746c65eac5
- number: 14
  speaker: factory
  kind: done
  at: '2026-10-19T22:44:33.208919Z'
  stage: approval
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
5. tester: No tests written: this is a docs-only story. Its Interface says no test changes, and criterion 1 forbids changes under `tests/`.
   Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. I created no files and left the working tree untouched; the factory's own `.costs.jsonl` sidecar is the only modified file.
   criterion 1 (nothing under src/, tests/, image/, template/, demo/, claude/ changes): no test function. This is a constraint on the diff; the smoke test's `git diff --name-only` checks it, and this entry states it as the criterion asks.
   criterion 2 (`make check` stays green): no test function; the factory's gate after the coder and docs stages checks it.
   criterion 3 (docs: the `agents.md` and `stages.md` lines of `docs/project-guide/README.md`, *The files*): no test function. Adding a test would break criterion 1. The smoke test and `python -m factory.entry.check_documents` check it after the docs stage.
   Modules the test run could not import: none. No test was added, so there is nothing red for the coder. The coder's job is also only to confirm that nothing changes; the documenter makes the two-line edit.
   I did not run `make test`, because there was no new test to see fail. `make lint` is green.

   `lint`: lint: green (0.0 s)
   `test`: test: green (49.0 s)
6. factory: started doing as self.
7. coder: Nothing built. This story only changes docs. Its Interface says no module under `src/factory/` and no test changes, and the only change is two lines of `docs/project-guide/README.md`, *The files*. That edit belongs to the documenter, not the coder.
   Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. I left the working tree as I found it: the factory's `.costs.jsonl` sidecar is the only modified file.
   Main choice: I left `docs/project-guide/README.md` alone, even though the edit is only two lines. CLAUDE.md, *Docs*, says the documenter keeps the guide true and the coder does not write it. I rejected making the edit here because it would cross that split.
   Refactor: there is no diff, so nothing needed changing.
   `make check` is green (`check: green`, coverage 99.12 %).
   Noticed and not touched: nothing.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'` is empty. The only files the branch changes are the work item and its `.costs.jsonl` sidecar, both under `factory/`. This is what a docs-only story should look like at this point: the Interface rules out any change under `src/`, `tests/`, `image/`, `template/`, `demo/` and `claude/`, and the documenter makes the two-line edit next.
   1. Acceptance criteria: criterion 1 limits what the diff may touch. It holds, and the tester (entry 5) and the coder (entry 7) each said so, as the criterion asks. Criterion 2: the factory's `make check` after the coder was green (entry 7, `check: green`). Criterion 3 is the docs criterion. The story adds no code, so there is no rule whose failing side would need a test.
   2-4. Architecture, security, quality: there is no code in the diff to judge. The coder's `duplicates: 5 new` cannot come from this branch, which changes nothing under `src/factory`.
   5. Work item hygiene: entries 5 and 7 explain why nothing was built (the documenter owns `docs/project-guide/`, under CLAUDE.md *Docs*) and what was rejected (the coder making the edit). The docs criterion still matches the repository. The `agents.md` line (README.md:14) lists `factory.adapters.validation_faults` and then `factory.domain.provider_limits`, so `project_agents` goes between them. The `stages.md` line (README.md:18) lists `factory.adapters.pipeline_yaml` first among "It also names". Both modules exist: `src/factory/application/project_agents.py` and `src/factory/application/provider_limits.py`.
   6. Earlier tests: none. No test file is changed, renamed or deleted.
10. factory: started docs as self.
11. documenter: Files changed: `docs/project-guide/README.md`, *The files*, two lines only. The `agents.md` line now names `factory.application.project_agents` after `factory.adapters.validation_faults` and before `factory.domain.provider_limits`. The `stages.md` line now names `factory.application.provider_limits` after `factory.adapters.pipeline_yaml`. Both are in backticks in the "It also names ..." sentence, as the docs criterion asks. Each line keeps its domain, its existing modules, its `Sections:` list and its `Subsections other files refer to:` list. No other line or file of the guide changed.

    Checked: `uv run -q python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, because I changed only a document under `docs/`. The factory's checks after this stage decide. I did not run the work item's other smoke-test commands either.

    Cross-read and found current: the rest of `docs/project-guide/README.md`, the `agents.md` and `stages.md` lines as they were, and the diff against `main`. That diff touches nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`, so no other document can have gone stale from it.

    Stale text noticed and not touched: nothing.

    Findings for the coder: none.

    `check`: check: green (not run again: passed on tree 4b0c868681a6 at 2026-10-19T22:40:16Z)
    `secrets`: secrets: green (0.2 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test run from the repository root. I ran the three commands exactly as written, in order. All three met their `Expect:` lines, and there are no findings.

    Command 1 (the Python check of the index's *The files*):
    ```
    True
    True
    2
    True
    ```
    Expect: four lines, `True`, `True`, `2` and `True`. Met.

    Command 2 (`git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- docs README.md`):
    ```
    0
    docs/project-guide/README.md
    ```
    Expect: two lines, `0` and `docs/project-guide/README.md`. Met.

    Command 3 (`uv run -q python -m factory.entry.check_documents`):
    ```
    documents ok
    ```
    Expect: `documents ok`. Met.

    Acceptance criteria, read again against the results:
    1. Command 2 shows nothing changed under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The tester (entry 5) and the coder (entry 7) each said so in their entries.
    2. `make check` was green after the coder (entry 7), and the factory's gate reused that result after the docs stage (entry 11). The smoke test does not contradict it.
    3. Docs: I also read `git diff origin/main -- docs`. Exactly two lines of `docs/project-guide/README.md` change.
       - The `agents.md` line gains `factory.application.project_agents` between `factory.adapters.validation_faults` and `factory.domain.provider_limits`.
       - The `stages.md` line gains `factory.application.provider_limits` right after `factory.adapters.pipeline_yaml`.
       - Both are in backticks. Each line's domain, its existing modules, its `Sections:` list and its `Subsections other files refer to:` list are unchanged.
       - No other line or file of the guide changes. No guide file is over 600 lines, and `documents ok` was printed.

    I fixed nothing and created no files. Nothing is open.
14. factory: done (pull request merged); cost: 6 runs, 2.4 min, 26 turns, 93910 tokens in (341160 more from cache), 5993 out, $0.76
