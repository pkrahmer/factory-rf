# Story form check

## Assignment (as of log entry 1)

Build the check of a story's form that code runs before and after every agent run and that the human can run on a draft (kept thing 9: a story is specified first, and its form is checked by code). It returns one finding for each rule a story breaks, each with a fixed message and, where it applies, the line of the body. The rules are v1's: a title line, every section of the project's own story form, criteria numbered 1 to n, the two closing criteria (the second-to-last contains `make check` and `green`, the last starts with `docs:`), a smoke test whose every code block is followed by an `Expect:` line, and a numbered journal. Because the sections come from F0002-S0004, a heading or a `# comment` inside a fenced block can no longer hide a section or fake the title, which v1's form check could not tell apart. Three findings are new in v1.1 and follow from the work item's data: a backlog story that carries front matter, a story in progress or done that has no state, and a journal whose data and text disagree in their number of entries (SI1.1 keeps both halves in step). The check of the file's place and the command for the human are the last story of this feature. The story is pure domain code.

## Interface

`src/factory/domain/story_form.py`

```python
class FormFinding(BaseModel):
    line: PositiveInt | None          # a line of the body, counted from 1
    message: str

def check_story_form(
    document: WorkItemDocument, form: str, *, folder: LifecycleFolder
) -> list[FormFinding]: ...
```

`form` is the text of the project's story form (`factory/story-form.md`). `FormFinding` is frozen and forbids unknown fields. The findings are returned in the order of the rules below, all of them and not only the first. The rules, with the message and the line of each finding; every rule has a criterion below:

1. No line outside the code blocks starts with `# `: `the story has no title line`, no line.
2. A heading of `required_sections(form)` is not a section of the body, one finding per missing heading in the form's order: `missing section: ## <heading>`, no line. A heading that occurs only inside a code block is missing.
3. Criteria are the lines at column 0, outside code blocks, in the `Acceptance criteria` section that start with digits and `". "`; an item runs to the line before the next item or the end of the section. Their numbers must be 1, 2, 3 and so on. At the first item whose number differs, one finding: `criterion numbered <found> where <expected> is expected`, on the line of that item. No criteria is no finding.
4. With two criteria or more: when the second-to-last item does not contain both `make check` and `green`, `the second-to-last criterion must contain "make check" and "green"` on its line; when the text of the last item after its number does not start with `docs:`, `the last criterion must start with "docs:"` on its line. With fewer than two criteria nothing is checked.
5. In the `Smoke test` section, when it exists: no code block gives `the Smoke test has no code block` on the heading's line; a code block whose closing line is followed, within the section, by a first non-blank line that does not start with `Expect:`, or that is never closed, or that is followed by nothing, gives `the code block opened at line <n> is not followed by an "Expect:" line` on the line of the opening of the block. Every block is judged by itself.
6. In the `Journal` section, when it exists: the entries are the lines at column 0 that start with digits and `". "`. Their numbers must be 1, 2, 3 and so on; at the first that differs, one finding `journal entry numbered <found> where <expected> is expected` on its line. No entry is no finding.
7. With `folder` `backlog` and `document.ignored_keys` not empty: `a backlog story carries no front matter: <the keys joined by ", ">`, no line.
8. With another folder and `document.state` `None`: `the story has no state`, no line.
9. With another folder and a state: when `len(state.journal)` differs from the number of entries found in rule 6 (0 without a `Journal` section), `the journal data lists <n> entries but the text shows <m>`, no line.

The sections `Acceptance criteria`, `Smoke test` and `Journal` are the constants of `factory.domain.sections`. A rule that needs a section does nothing when the body has no such section; rule 2 reports it when the form requires it.

Tests: `tests/domain/test_story_form.py`.

## Acceptance criteria

1. A complete story gives no finding: a title, the sections `Description`, `Interface`, `Acceptance criteria` (three items; the second-to-last `make check stays green.`, the last `docs: none, nothing changes.`), `Smoke test` (one fenced block followed by an `Expect:` line) and `Journal` (entry 1), checked against a form that requires those five sections, with the folder `backlog` and no front matter.
2. `FormFinding(line=0, message="x")` raises `ValidationError`; `line=None` and `line=1` are valid; a `FormFinding` is frozen.
3. A body without a `# ` line gives `the story has no title line` and a body whose only `# ` line is inside a fenced block gives it too.
4. Each section of the form that is missing gives `missing section: ## <heading>` in the form's order; a form with an added `## Notes` makes `Notes` required; a section whose heading occurs only inside a fenced block is reported as missing.
5. Criteria numbered 1, 2, 4 give the single finding `criterion numbered 4 where 3 is expected` on the line of the item `4.`; criteria starting at 2 give `criterion numbered 2 where 1 is expected`; criteria 1, 1 give `criterion numbered 1 where 2 is expected`; an `Acceptance criteria` section without items gives no finding.
6. A second-to-last criterion that lacks `make check`, or lacks `green`, gives `the second-to-last criterion must contain "make check" and "green"` on its line; one that has both, in a text spread over two lines of the item, gives none.
7. A last criterion whose text does not start with `docs:` (`Docs: x`, `done`) gives `the last criterion must start with "docs:"` on its line; `docs: none` gives none.
8. Exactly two criteria are checked: with the two items `1. a` and `2. b` both closing findings are given; with one item `1. a` and with no item no closing finding is given.
9. A `Smoke test` section without a code block gives `the Smoke test has no code block` on the heading's line.
10. A code block followed by prose, by the end of the section, or never closed gives `the code block opened at line <n> is not followed by an "Expect:" line` with `n` the line of its opening; blank lines between the block and `Expect:` are allowed; with two blocks only the one without `Expect:` is reported.
11. A smoke test block that contains the lines `## start the server` and `# comment` leaves the section whole: neither line is read as a heading or a title, and a story that is otherwise complete gives no finding.
12. Journal entries numbered 1, 3 give `journal entry numbered 3 where 2 is expected` on the line of the entry `3.`; indented lines in an entry are not entries; a `Journal` section without entries gives no finding.
13. With the folder `backlog` and `ignored_keys` equal to `["stage", "attempts"]` the finding is `a backlog story carries no front matter: stage, attempts`; with no ignored keys there is none.
14. With the folder `in-progress` or `done` and a document without state the finding is `the story has no state`; with a state there is none, and a backlog story without state gives none.
15. With the folder `in-progress`, a state whose `journal` lists 2 records and a body with 3 entries give `the journal data lists 2 entries but the text shows 3`; equal numbers give no finding; no finding is given for the backlog folder.
16. A story that breaks several rules gets all its findings, in the order of the rules: title, missing sections, criteria numbering, closing criteria, smoke test, journal numbering, then the three rules about state.
17. make check stays green.
18. docs: `docs/project-guide.md` lists the rules of the form check with their messages and says that the sections come from the project's story form and that code blocks are respected; `docs/decisions.md` records the three findings that v1 did not make.

## Demo

```bash
uv run python -c "
from factory.domain.story_form import check_story_form
from factory.domain.work_item import WorkItemDocument
form = '# Form\n\n## Description\n\n## Acceptance criteria\n\n## Smoke test\n\n## Journal\n'
body = '# S\n\n## Description\n\nText.\n\n## Acceptance criteria\n\n1. It works.\n3. make check stays green.\n4. done.\n\n## Smoke test\n\nNo block here.\n'
for finding in check_story_form(WorkItemDocument(state=None, body=body), form, folder='backlog'):
    print(finding.line, finding.message)
"
```
Expect: four lines, in this order: `None missing section: ## Journal`, `10 criterion numbered 3 where 2 is expected`, `11 the last criterion must start with "docs:"`, `13 the Smoke test has no code block`.

```bash
uv run python -c "
from factory.domain.story_form import check_story_form
from factory.domain.work_item import WorkItemDocument
body = '# S\n\n## Journal\n\n1. 2026-10-12 human: created.\n'
for folder in ('in-progress', 'backlog'):
    print(folder, [f.message for f in check_story_form(WorkItemDocument(state=None, body=body), '', folder=folder)])
"
```
Expect: two lines: `in-progress ['the story has no state']` and `backlog []`.

## Log (append only)

1. 2026-10-12 human: created.
