---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 252
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T06:30:52.641193Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T06:30:52.646885Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T06:31:35.571848Z'
  stage: intake
  run: f825ff04273b4127a65b62265f11490c
---

# The project guide becomes an index and one file per domain, and the document check reads them all

## Description

`docs/project-guide.md` has 1,905 lines, and every agent run is told to read it whole before it changes anything. The file tool reads 2,000 lines by default, so the next features would push the guide past what an agent sees in one read. This story moves the guide into the folder `docs/project-guide/`: an index, `README.md`, holds what every story needs, and eight files hold one domain each, so that an agent reads the index and then only the files of the domains its story touches. It is a move, not a rewrite: every `## ` section keeps its heading and its words and goes whole to the file the feature's table names. Only the index and two kinds of line are new: every mention of the old path, and the section *The document check*, which describes this story's change. The document check follows the guide: it reads the index as the project guide, with the sections and table rows it checks today. It also checks every other `.md` file directly in the folder for the v1 words and the replaced phrases, so that no moved section leaves the check. The coder changes the check; the documenter makes the move at the docs stage, where `make documents` then reads the index. The rest stays as it is: the operator guide and the decision log stay single files, the template and the todo demo keep their single `docs/project-guide.md`, and no code moves. `CLAUDE.md` and the story form name the new paths through the human's change 1, right after the merge.

## Interface

`factory.domain.documents` (`domain`):

```python
PROJECT_GUIDE: Final = "docs/project-guide/README.md"
PROJECT_GUIDE_FOLDER: Final = "docs/project-guide"


def is_guide_file(path: str) -> bool:
    """Whether `path` is a file of the project guide beside its index: `<folder>/<name>.md`."""


def check_documents(texts: Mapping[str, str | None]) -> list[DocumentFinding]:
    """The findings of the four documents, in their order, then of the guide's other files."""
```

- `PROJECT_GUIDE` is the guide's index; `DOCUMENT_PATHS` keeps its order with the new value. `PROJECT_GUIDE_SECTIONS` and the rules on the index (its two sections, a table row for each kill-point case and each fault-injection path, the wording) are unchanged.
- `is_guide_file(path)` is true exactly when `path` is `PROJECT_GUIDE_FOLDER`, a `/` and a name that fully matches `[^/]+\.md`, and `path` is not `PROJECT_GUIDE`. It is case-sensitive, so `X.MD` is no guide file.
- `check_documents` gives the findings of the four documents first, as today. After them come the keys of `texts` that `is_guide_file` accepts, in plain string order of the keys. Each gets `missing` for `None`, `empty` for a blank text, and otherwise the findings of the replaced phrases and the v1 words, with a `## Replaced from v1` section exempt: the same messages as for `README.md`. The section and table-row rules are not asked of a guide file. Every other key is ignored, as today.

`factory.entry.check_documents` (`entry`):

- `main(argv)` reads the four `DOCUMENT_PATHS` as today. It also reads every regular file directly in `<root>/docs/project-guide/` whose key `docs/project-guide/<name>`, written with `/`, `is_guide_file` accepts, as UTF-8. A folder (also one named `x.md`), a file in a subfolder and a missing folder add nothing. The output and the exit status follow the findings as today.

Unchanged: the other constants of `factory.domain.documents` (`REPLACED_PHRASES`, `GLOSSARY_FORBIDDEN`, the operator guide's rules), `make documents` and the pipeline definition.

Tests (the tester writes them): `tests/domain/test_documents_guide_files.py` and `tests/entry/test_check_documents_guide_files.py`. They use `clean_texts` and `write_documents` of `tests/document_texts.py` as they are.

Changed under the feature's decision 9, by the tester only, nothing else in that module: `tests/entry/test_check_documents.py`, whose `MISSING_LINES` holds `docs/project-guide/README.md: missing` in place of `docs/project-guide.md: missing`, and whose `test_each_finding_prints_one_line_in_order_and_returns_one` expects `docs/project-guide/README.md: section 'Kill points' is missing` in place of `docs/project-guide.md: section 'Kill points' is missing`. Each test keeps its name and what it checks.

## Acceptance criteria

1. `PROJECT_GUIDE == "docs/project-guide/README.md"`, `PROJECT_GUIDE_FOLDER == "docs/project-guide"` and `DOCUMENT_PATHS == ("README.md", "docs/operator-guide.md", "docs/project-guide/README.md", "docs/decisions.md")`.
2. `is_guide_file` (rows of one parametrized test): `docs/project-guide/agents.md` and `docs/project-guide/a.b.md` give `True`. `docs/project-guide/README.md`, `docs/project-guide/sub/x.md`, `docs/project-guide/notes.txt`, `docs/project-guide/.md`, `docs/project-guide/X.MD`, `docs/project-guide.md`, `docs/project-guidex/a.md`, `docs/a.md` and `docs/project-guide/` give `False`.
3. A guide file is checked for its words only (rows of one parametrized test; each row is `clean_texts()` with one more key, `docs/project-guide/agents.md`). The text `# Agents\n\nThe factory runs agents.\n` gives `[]`, although it has no `## Kill points` and no table row. `# Agents\n\nEach ticket moves on.\n` gives exactly `[DocumentFinding(document="docs/project-guide/agents.md", message="uses the v1 word 'ticket'")]`. `# Agents\n\nThe run record is gone.\n` gives the one finding `describes a replaced behaviour: 'run record'`. `"  \n"` gives `empty` and `None` gives `missing`. `# Agents\n\n## Replaced from v1\n\n| ticket | work item |\n` gives `[]`.
4. The order and the keys: `clean_texts()` with `docs/decisions.md` set to `"  \n"`, then the keys `docs/project-guide/b.md`, `docs/project-guide/a.md`, `docs/other.md` and `docs/project-guide/sub/c.md` added in that order, each `A ticket.\n`, gives exactly three findings, in this order: `docs/decisions.md` `empty`, `docs/project-guide/a.md` `uses the v1 word 'ticket'`, `docs/project-guide/b.md` `uses the v1 word 'ticket'`.
5. The command reads the files beside the index (rows of one parametrized test, each a root with `write_documents(root, clean_texts())`). With `docs/project-guide/stages.md` holding `# Stages\n\nEach ticket waits.\n`, `main(["--root", <root>])` prints exactly `docs/project-guide/stages.md: uses the v1 word 'ticket'\n` and returns 1. With `docs/project-guide/stages.md` holding `# Stages\n\nThe stages run.\n`, `docs/project-guide/notes.txt` and `docs/project-guide/old/x.md` each holding `A ticket.\n`, and an empty folder `docs/project-guide/empty.md/`, it prints `documents ok\n` and returns 0. With `docs/project-guide/stages.md` holding `# Stages\n\nThe café opens — every day.\n`, written as UTF-8 bytes, it prints `documents ok\n` and returns 0.
6. The old path is not read (rows of one parametrized test): a root with `README.md`, `docs/operator-guide.md` and `docs/decisions.md` from `clean_texts()`, and the clean project guide's text at `docs/project-guide.md` instead of the index, prints exactly `docs/project-guide/README.md: missing\n` and returns 1. An empty root prints `MISSING_LINES` of `tests/entry/test_check_documents.py` (decision 9) and returns 1.
7. `make check` stays green.
8. docs: the project guide moves from `docs/project-guide.md` into the folder `docs/project-guide/`, and the old file is deleted. Each `## ` section goes whole to one file, by this table (file: its domain; its sections, in the old guide's order):
   - `README.md`: the index, what holds for all code; *Errors*, *The models' configuration*, *Kill points*, *Fault-injection paths*.
   - `git-and-hosting.md`: git and the hosting service; *The hosting service*, *The git wrapper*.
   - `processes-and-checks.md`: processes, project commands and this repository's checks; *Project commands*, *Starting a process*, *The duplicates report*, *The document check*, *The demos*, *Mutation testing*.
   - `agents.md`: the agent runtime, the agent files, the shipped agents and the template; *The agent runtime*, *The agent definition reader*, *The shipped agents, settings and template*, *Replaced from v1*.
   - `write-guard.md`: the write paths, the guard, the undo, the kernel's guard and the start wrapper; *The write paths*, *The guard command*, *The undo*, *The kernel's write guard*, *The start wrapper*.
   - `work-items.md`: the identity, data, files, sections and form of a work item; *Identity, order and places of work items*, *The data of a work item*, *Reading and writing a work item file*, *Sections of a Markdown body*, *The form check of a story*.
   - `costs.md`: cost records and bills; *Cost records*, *Bills*.
   - `stages.md`: the pipeline definition and a stage from the claim to the result commit; *The claim service*, *The pipeline definition*, *The prompt and the request for a stage*, *Opening a work item*, *Starting a stage*, *Stalls*, *After the agent run*, *The decision rules*, *The stage protocol*.
   - `watching.md`: the evaluation, the tick, its handlers, the stops and the boundaries; *The evaluation*, *The tick*, *The handlers of the events*, *Stops, the clock and the factory log*.
   Move the text with a script, not by retyping it. Cut the old guide at its `## ` headings with `factory.domain.sections.sections`, so a heading inside a code block is no cut. Write each section's lines unchanged to the file the table names, in the old guide's order, and keep the script in `$TMPDIR`. A section the guide gained after the table was drawn goes to the file whose code it describes, by the index's list. Each file but the index starts with a title line `# <its domain>` and one sentence: what the file covers, and to read the index first. The index, `docs/project-guide/README.md`, starts with the title `# Project guide` and the guide's opening paragraph, changed to say that the guide is this index and one file per domain: read the index, then the files of the domains the story touches. It also says that a file of the guide is split by the same rule before it passes about 600 lines, its new file named in the index. A section `## The files` follows. It names each file in backticks, with its domain as the table gives it, the packages, modules and commands its sections describe, and each of its `## ` sections by its heading. Then come the sections *Errors*, *The models' configuration*, *Kill points* and *Fault-injection paths*, which the document check reads there. A moved section changes in nothing else, with two exceptions. First, every `` `docs/project-guide.md` `` in the guide's text becomes `` `docs/project-guide/` ``; today that is one sentence of *The write paths*, which then reads `` `docs/project-guide/` is not protected; the documenter keeps it. ``. Second, *The document check* is rewritten for this story's change. It says that the check reads the index as the project guide, with its sections *Kill points* and *Fault-injection paths*. It also checks the v1 words and the replaced phrases of every other `.md` file directly in `docs/project-guide/`, whose findings follow those of the four documents in path order. And a story that changes a file of the guide runs the check. No file of the guide passes 600 lines. `README.md`, *Where to look next*: `docs/project-guide/README.md`, the guide for agents, an index of its files by domain; and the opening paragraph's last sentence, "`docs/project-guide.md` describes each part.", names `docs/project-guide/` instead. `docs/operator-guide.md`: each reference to the project guide names the file that holds the section it names. "The guard command" is in `docs/project-guide/write-guard.md`. "The rules of the definition" is in `docs/project-guide/stages.md` (two places). "The form check of a story" is in `docs/project-guide/work-items.md`, in place of `docs/project-guide.md`. *Kill points* and *Fault-injection paths* are in `docs/project-guide/README.md`. `docs/decisions.md`: an entry *The project guide is an index and one file per domain*, dated with the story, with the reasons of the feature's decisions 1 to 6. The entry *The project guide lives in `docs/`* gets one sentence, that the guide is the folder `docs/project-guide/` since this story.

## Smoke test

```bash
uv run -q python - <<'EOF'
import subprocess
from collections import Counter
from pathlib import Path

from factory.domain.sections import sections, split_lines


def parts(text):
    lines = split_lines(text)
    return [(found.heading, "\n".join(lines[found.start : found.end]).rstrip()) for found in sections(text)]


old = subprocess.run(
    ["git", "show", "origin/main:docs/project-guide.md"], capture_output=True, encoding="utf-8", check=True
).stdout.replace("`docs/project-guide.md`", "`docs/project-guide/`")
files = {path.name: path.read_text(encoding="utf-8") for path in sorted(Path("docs/project-guide").glob("*.md"))}
index = files.get("README.md", "")
new = {name: dict(parts(text)) for name, text in files.items()}
problems = []
for name, text in files.items():
    counts = Counter(heading for heading, _ in parts(text))
    problems += [f"{name}: {heading} twice" for heading, count in counts.items() if count > 1]
    if len(split_lines(text)) > 600:
        problems.append(f"{name}: over 600 lines")
    if name != "README.md" and f"`{name}`" not in index:
        problems.append(f"{name}: not named in the index")
for heading, text in parts(old):
    holders = [name for name, found in new.items() if heading in found]
    if len(holders) != 1:
        problems.append(f"{heading}: in {len(holders)} files")
    elif heading != "The document check" and new[holders[0]][heading] != text:
        problems.append(f"{heading}: changed")
    if heading not in index:
        problems.append(f"{heading}: not named in the index")
headings = {heading for heading, _ in parts(old)}
problems += [
    f"{name}: {heading} is not a section of the old guide"
    for name, found in new.items()
    if name != "README.md"
    for heading in found
    if heading not in headings
]
print(Path("docs/project-guide.md").exists(), problems)
EOF
```
Expect: `False []`

```bash
uv run -q python -m factory.entry.check_documents; echo "exit $?"
```
Expect: two lines, `documents ok` and `exit 0`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/docs"
cp README.md "$d/"
cp -r docs/operator-guide.md docs/decisions.md docs/project-guide "$d/docs/"
printf '# Notes\n\nEach ticket moves on.\n' > "$d/docs/project-guide/notes.md"
mkdir -p "$d/docs/project-guide/old"
printf '# Old\n\nA ticket.\n' > "$d/docs/project-guide/old/x.md"
uv run -q python -m factory.entry.check_documents --root "$d"; echo "exit $?"
```
Expect: two lines, `docs/project-guide/notes.md: uses the v1 word 'ticket'` and `exit 1`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: concrete. It names `factory.domain.documents` (`PROJECT_GUIDE`, `PROJECT_GUIDE_FOLDER`, `is_guide_file(path) -> bool`, `check_documents(texts)`) and `factory.entry.check_documents.main(argv)`. It also states the exact rule for `is_guide_file` and the order of the findings.
   Criteria: each one can be tested by one test function. Every clause of the Interface has a criterion, and each rule has both its passing and its failing side.
   - Criterion 1: the constants and `DOCUMENT_PATHS`.
   - Criterion 2: the `is_guide_file` rows, covering the case-sensitive `X.MD`, the index itself, a subfolder, a non-`.md` name, `.md` alone, the old path, a sibling folder and the bare folder.
   - Criterion 3: clean text, the v1 word, the replaced phrase, blank, `None`, and the exempt `## Replaced from v1` section.
   - Criterion 4: finding order, plus ignored keys.
   - Criterion 5: the command reads a guide file, ignores a `.txt` file, a subfolder file and a folder named `x.md`, and reads UTF-8.
   - Criterion 6: a missing folder and the old path not being read.
   - Criterion 9 of the feature gives the leave to change the two named tests.
   Smoke test: the three blocks are runnable. The first needs the move to have been made, which the docs stage does. Each `Expect:` line is checkable against the output (`False []`, `documents ok` with `exit 0`, the `notes.md` finding with `exit 1`).
   Architecture: the change fits the layering. The rules and constants go in `domain.documents`, and the folder reading goes in `entry.check_documents`, the only place that touches the filesystem. There is no new dependency or package.
   Scope: the story stays inside the feature's Scope. Its Out of scope list (template, todo demo, operator guide and decision log staying single files, no code tree move) is respected.
