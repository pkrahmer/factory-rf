---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 255
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T09:02:41.786324Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T09:02:41.792979Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T09:03:10.737618Z'
  stage: intake
  run: 0654c570856b4441b7f769fb39f561d6
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T09:03:31.276274Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T09:04:21.886143Z'
  stage: tests
  run: 9b1bca1350b743c2a965fb4d0ae66ed2
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T09:04:43.617564Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T09:06:33.508174Z'
  stage: doing
  run: 7ff02647df0c4f82bd54927357de0fb6
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T09:06:55.019595Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T09:07:13.406629Z'
  stage: review
  run: d636b66d75c44b74a30a0095a143543b
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T09:07:33.910840Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T09:09:05.935758Z'
  stage: docs
  run: 813371c09e464365b96040d5a2de49dd
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T09:09:26.821246Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T09:09:58.450625Z'
  stage: smoke-test
  run: 31052bf52f52474eaedcadf3263bb05d
---

# The guide's index names every module and subsection its files describe

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0025 split the project guide so that an agent reads the index, `docs/project-guide/README.md`, and then only the files of the domains its story touches. The index's section *The files* is how the agent picks those files. Each line was to name "the packages, modules and commands its sections describe" (S0001, criterion 8), but the line falls short: of the 114 modules under `src/factory/` that the eight domain files name, 62 appear on no index line of a file that names them. Among them are `factory.adapters.opencode_runtime`, `factory.application.preflight`, `factory.domain.settings`, the feature acceptance's modules, every module of `factory.application.handlers` and `factory.entry.wiring`. The index also names only the `## ` sections. The feature's decision 2 promised that it names *Boundaries*, a `### ` in `watching.md`, and it does not. It does not name *The records contract*, *The opencode runtime* or *The feature acceptance* either, the `### ` subsections that the human's change 2 sends later stories to. Three smaller passages need the same repair:
- One reference in `agents.md` ("see *The story form check*") points to a `###` in `stages.md`, without saying so, and its name is close to `work-items.md`'s *The form check of a story*.
- The decision-log entry *The project guide lives in `docs/`* still opens by calling `docs/project-guide.md` the guide.

This story repairs exactly these passages. It changes no code, no test, no `## ` heading and no other passage.

## Interface

None: no module under `src/factory/`, no test, no image, template, demo or agent file changes. The documenter changes `docs/project-guide/README.md` (*The files*), one sentence of `docs/project-guide/agents.md` and one sentence of `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/project-guide/README.md`, *The files*: every module under `src/factory/` that a file of the guide other than the index names (by its full dotted name, for example `factory.application.handlers.merged`) is named in backticks on the line of at least one file that names it. Where several files name a module, it goes on the line of the file that describes it. Each line keeps its domain, its existing modules and its `Sections:` list as they are.
   - The same section names four `### ` subsections, each on its file's line after the `Sections:` list, as `Subsections other files refer to:` followed by the names in italics:
     - *Boundaries* on the `watching.md` line;
     - *The records contract* and *The feature acceptance* on the `work-items.md` line;
     - *The opencode runtime* on the `agents.md` line.
   - `docs/project-guide/agents.md`, *The shipped agents, settings and template*: "(see *The story form check*)" reads "(see *The story form check* in `stages.md`)". Nothing else in a domain file changes.
   - `docs/decisions.md`, *The project guide lives in `docs/`*: the first sentence names `` `docs/project-guide/` `` in place of `` `docs/project-guide.md` ``. The sentence F0025-S0001 added stays. The dated F0011-S0005 entry stays as it is.
   - No file of the guide passes 600 lines. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
uv run -q python - <<'EOF'
import re
from pathlib import Path

guide = Path("docs/project-guide")
files = {p.name: p.read_text(encoding="utf-8") for p in sorted(guide.glob("*.md"))}
the_files = files["README.md"].split("## The files")[1].split("\n## ")[0]
lines = {m.group(1): line for line in the_files.splitlines() if (m := re.match(r"- `([^` ]+)`", line))}
modules = {str(p.relative_to("src"))[:-3].replace("/", ".").removesuffix(".__init__") for p in Path("src/factory").rglob("*.py")}
named_by = {}
for name, text in files.items():
    if name == "README.md":
        continue
    for found in set(re.findall(r"factory\.(?:domain|application|adapters|entry)(?:\.[a-z_]+)+", text)):
        while found not in modules and found.count(".") > 2:
            found = found.rsplit(".", 1)[0]
        if found in modules:
            named_by.setdefault(found, set()).add(name)
gap = sorted(m for m, names in named_by.items() if not any(f"`{m}`" in lines.get(n, "") for n in names))
subsections = [
    ("watching.md", "Boundaries"),
    ("work-items.md", "The records contract"),
    ("work-items.md", "The feature acceptance"),
    ("agents.md", "The opencode runtime"),
]
print(len(gap), all(f"*{s}*" in lines[f].split("Subsections other files refer to:")[-1] for f, s in subsections))
print(max(len(text.splitlines()) for text in files.values()) <= 600)
EOF
```

Expect: two lines, `0 True` and `True`

```bash
grep -c "see \*The story form check\* in \`stages.md\`" docs/project-guide/agents.md; grep -c "^\`docs/project-guide.md\` is the guide for agents" docs/decisions.md
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
   - Interface: "None" is right for a documentation-only story. It names the three files the documenter changes (`docs/project-guide/README.md` *The files*, one sentence of `agents.md`, one sentence of `docs/decisions.md`) and the four `### ` subsections with the file line each goes on. I checked these against the repository. The `###` headings exist: *Boundaries* (`watching.md:260`), *The feature acceptance* and *The records contract* (`work-items.md`), *The opencode runtime* (`agents.md:91`). The sentence "(see *The story form check*)" is at `agents.md:283`. The `decisions.md:23` sentence opens with `docs/project-guide.md` is the guide for agents. The F0011-S0005 entry at line 337 is the dated one that stays.
   - Criteria: every one can be tested from the repository's files. 1 (nothing outside docs changes), 2 (`make check`) and 3 (docs) cover each clause: the module coverage rule, the four subsections, the `agents.md` wording, the `decisions.md` wording, the 600-line limit and `documents ok`. There is no code rule with a failing side. The one rule-like clause, "the file that describes it", is bounded by "at least one file that names it", which the smoke test checks.
   - Smoke test: all four blocks are runnable. The index lines match the script's `- \`name\`` pattern. The `Expect:` lines are exact outputs (`0 True` and `True`; `1` and `0`; `0`; `documents ok`).
   - Architecture: nothing in `src/` changes, and the documenter writes only within `README.md` and `docs/*`.
   - Scope: it is inside F0025 (the guide split by domain), and nothing in its Out of scope is touched. The feature's decision 2 promised that the index names *Boundaries*, and this story repairs that.
   - One slip, not blocking: the Description says "Three smaller passages need the same repair" but lists two bullets. The criteria cover the same two passages (`agents.md` and `decisions.md`), so I left the text as it is.
4. factory: started tests as self.
5. tester: No tests written. This story only changes documentation. Criterion 1 forbids any change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`, and requires the tester's entry to say so. So for this stage, the specification is an unchanged `tests/`.
   - criterion 1 (nothing under src/, tests/, image/, template/, demo/ or claude/ changes): no test function. The tester changed nothing there. The smoke test's `git diff --name-only origin/main -- src tests image template demo claude | wc -l` checks this.
   - criterion 2 (`make check` stays green): no test function. The factory's checks cover it.
   - criterion 3 (docs): no test function. Its clauses are checked by the smoke test and by `python -m factory.entry.check_documents` in the docs stage. Adding a test of the index's contents would change `tests/`, which criterion 1 forbids.
   Files created: none. Modules the test runner could not import: none, because there are no new tests. I did not run `make test`: with no new tests there is no red result to confirm. `make lint` is green. The working tree holds no changes of mine.
   For the coder: there is no code to write. The work is the documenter's.

   `lint`: lint: green (0.0 s)
   `test`: test: green (34.3 s)
6. factory: started doing as self.
7. coder: No code written. This story only changes documentation. Criterion 1 forbids any change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`, and requires the coder's entry to say so. I changed nothing there, and nothing anywhere else either. My working tree holds no edits. The only modified file is the work item's `.costs.jsonl` sidecar, which the factory writes.
      - Main choice: I did not make the guide's edits in this stage. The rejected alternative was to edit `docs/project-guide/README.md`, `agents.md` and `decisions.md` now. The Interface gives those edits to the documenter, and CLAUDE.md says the coder does not write the docs.
      - Refactor: there is no diff, so there was nothing to refactor.
      - Description: the journal did not change the task's meaning, so I left the Description as it is.
      - Noticed, not touched: the slip intake noted is still in the Description. It says "Three smaller passages need the same repair" but lists two bullets (`agents.md` and `decisions.md`). The criteria cover the same two passages.
      - `make check`: green on the unchanged tree (`check: green`, test coverage 99.05 %).

   `check`: check: green
   `duplicates`: duplicates: 5 new, 35 known, 1 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar, both under `factory/`.
   - Criterion 1 holds: nothing changed under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The tester's entry (5) and the coder's entry (7) both say so, as the criterion asks.
   - Criterion 2 holds: the factory's `make check` after the coder was green (entry 7, `check: green`). `duplicates: 5 new` cannot come from this branch, which changed nothing under `src/factory`, so it is not part of this review.
   - Criterion 3 is the documenter's work, written from the docs criterion. It still describes what the reader must know: the module coverage rule for *The files*, the four `### ` subsections and the line each goes on, the `agents.md` and `decisions.md` sentences, the 600-line limit and `documents ok`.
   - Groups 2 to 4 (architecture, security, quality) have nothing to judge, because the diff is empty.
   - Group 5: the coder's entry gives the main decision, to leave the guide's edits to the documenter as the Interface says, and the rejected option of making them in the doing stage. The Description still says "Three smaller passages" above a list of two. Intake and the coder both noted this. I do not count it as a finding, because the docs criterion the documenter works from names the same two passages correctly.

   Earlier tests: none. No test file that `main` holds is changed, renamed or deleted (`git diff --name-status main...HEAD` lists only the work item and its sidecar).
10. factory: started docs as self.
11. documenter: Docs-only story; I changed three documents and no code, test or comment. I did not run `make check`, because the factory runs it right after this stage.

    Files changed:
    - `docs/project-guide/README.md`, *The files*: each file's line now has the modules that other guide files name but no index line listed. They are added as "It also names `…`." before `Sections:`. Each module sits on the line of the file that describes it. Where several files name one module, I picked the one that fits it best:
      - `factory.domain.errors` is on the `stages.md` line.
      - `factory.application.files` is on the `work-items.md` line.
      - `factory.entry.wiring` is on the `watching.md` line.
      - `factory.application.preflight` is on the `processes-and-checks.md` line.
      - The existing modules and `Sections:` lists are unchanged.
    - The same lines now end with "Subsections other files refer to:". Under it: *Boundaries* on the `watching.md` line, *The records contract* and *The feature acceptance* on the `work-items.md` line, *The opencode runtime* on the `agents.md` line.
    - `docs/project-guide/agents.md`: "(see *The story form check*)" now reads "(see *The story form check* in `stages.md`)".
    - `docs/decisions.md`, *The project guide lives in `docs/`*: the first sentence names `docs/project-guide/` instead of `docs/project-guide.md`. The F0025-S0001 sentence and the dated F0011-S0005 entry are untouched.

    Checks I ran:
    - The smoke test's coverage rule: a script using the smoke test's module-matching logic lists 62 gap modules before my edit and 0 after.
    - `uv run python -m factory.entry.check_documents` prints `documents ok`.
    - The longest guide file is `work-items.md` at 375 lines, under the 600-line limit.

    I did not run the smoke test's other blocks (the `grep` counts and the `git diff … | wc -l`).

    Cross-read: the other guide files and `docs/decisions.md` against this change. Only the index and the two sentences needed edits. There is no code diff, so no names or behaviour moved.

    Findings for the coder: none.

    Stale text noticed, not touched: the Description says "Three smaller passages" above a list of two. Intake, the coder and the reviewer already noted it. The Description is not mine to rewrite.

    `check`: check: green
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: No findings. I ran the four smoke test commands from the repository root exactly as written, in order. Each one met its `Expect:` line. I fixed nothing.

    Command 1 (the Python coverage script). Expect: two lines, `0 True` and `True`. Met.
    ```
    0 True
    True
    ```

    Command 2 (the two `grep -c` counts). Expect: two lines, `1` and `0`. Met.
    ```
    1
    0
    ```

    Command 3 (`git diff --name-only origin/main -- src tests image template demo claude | wc -l`). Expect: `0`. Met.
    ```
    0
    ```

    Command 4 (`uv run -q python -m factory.entry.check_documents`). Expect: `documents ok`. Met.
    ```
    documents ok
    ```

    I also read the acceptance criteria against `git diff origin/main -- docs`. Nothing contradicts any of them:
    - Criterion 1 holds: command 3 shows no change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`, and entries 5 and 7 both say so.
    - Criterion 2: the factory's `make check` after the docs stage was green (entry 11). I did not run it again here.
    - Criterion 3, the index: the `docs/project-guide/README.md` diff only adds text (a word diff shows no removed words). So each line keeps its domain, its existing modules and its `Sections:` list. On each of the `agents.md`, `work-items.md` and `watching.md` lines, `Subsections other files refer to:` comes after `Sections:` and lists the names the criterion asks for, in italics.
    - Criterion 3, the other two sentences:
      - `agents.md`: one line changed, the "(see *The story form check* in `stages.md`)" sentence.
      - `docs/decisions.md`: one line changed. Its first sentence now names `docs/project-guide/`, and the F0025-S0001 sentence is still in it. The dated F0011-S0005 entry is not in the diff, so it is unchanged.
    - Criterion 3, the limits: no guide file passes 600 lines (command 1, second line), and `documents ok` is printed (command 4).

    Still open, not a finding: the Description says "Three smaller passages" above a list of two. Intake, the coder, the reviewer and the documenter all noted this. The criteria name the right two passages.
