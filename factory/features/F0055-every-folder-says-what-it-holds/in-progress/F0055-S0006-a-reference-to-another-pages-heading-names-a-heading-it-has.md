---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 633
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T11:21:05.914714Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T11:21:05.922101Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-07T11:21:24.041594Z'
  stage: intake
  run: 859689049c09499790470f159007ff87
  blocked: question
---

# A reference to another page's heading names a heading it has

## Description

The documents point the reader to a section of another page in one form: a heading in italics or quotes, then `in` or `of`, then a relative link to the page, for example `see *The two passes* in [machine.md](machine.md)`. The name check resolves the link to the file but not the heading, so a page that renames a heading leaves dangling references behind. After the rewrite, four such references pointed to headings that do not exist (the human, 2026-11-07, and F0054's acceptance): `docs/operator-guide/install.md:121` (*In a job* in `machine.md`, a bold paragraph under *The idle shutdown*), `docs/operator-guide/work-items.md:66` ("What a work item cost" in `records.md`, whose heading is *What a work item cost: `factory-bill`*), `docs/project-guide/machine.md:487` (*`StageFinisher.finish`* in `pipeline.md`, whose heading is *`StageFinisher.finish(aftermath)`*) and `docs/operator-guide/agent-runtime.md:407` ("The stage environment" under *Configuration* in `install.md`, a bold paragraph that now stands under *Reference*). This story makes the document check resolve each such reference against the headings of the linked page. A reference to a heading the page does not have is a finding of the name check, so it blocks in a listed document and is reported in any other. References within one page, and links with a `#` anchor, stay as they are.

## Interface

- `factory.shared.domain.heading_references` (domain, new):

  ```python
  def heading_references(document: str, text: str) -> list[HeadingReference]:
      """The references of one document to a heading of another page, with their lines."""

  def unresolved_headings(references: list[HeadingReference], headings: Callable[[str], set[str] | None]) -> list[str]:
      """One finding per reference whose heading the linked page does not have."""
  ```

  - A reference is a heading text in italics (`*...*`) or in double quotes, then optional `)` or `,`, then `in` or `of`, then a Markdown link to a `.md` file without a `#` anchor. The link is resolved against the document's folder, as the name check resolves links.
  - `HeadingReference` is a frozen model with `document`, `line`, `heading` and `target`. The heading text loses its backticks and asterisks.
  - `headings(target)` gives the set of headings of the linked page, with backticks and asterisks removed, or `None` when the page is no document of the check. A reference to such a page gives no finding.
  - A finding reads `<document>:<line>: <heading> is no heading of <target>`.
- `factory.entry.check_documents`: the findings of `unresolved_headings` join the name check's findings, so they block in a listed document and are reported in any other.
- Tests: `tests/shared/domain/test_heading_references.py` (new) and rows in the entry tests of the name check, on documents the tests write (`tests/support/minimal_documents_support.py`), never on the real documents. Adding rows to those earlier modules needs no further leave; no earlier row changes its expected result, and if one would, that is a question.
- The real documents: any reference this check finds broken in a listed document is fixed in the docs stage of this story, so that `make documents` stays green. A fix names the heading as the target page writes it, or names the paragraph and the heading it stands under; no heading is renamed.

## Acceptance criteria

1. `heading_references` finds a reference in each form, with its line, heading and resolved target. Rows: italics with `in`, quotes with `of`, a closing `)` before `in`, a heading with backticks, a link in a subfolder (`../`), and no reference for a link with a `#` anchor, a link to a file that is not `.md`, and a heading text without `in` or `of` after it.
2. `unresolved_headings` gives one finding for a heading the linked page does not have, none for one it has, and none for a link to a page that is no document of the check. Rows of one parametrized test.
3. On minimal documents, `main(["--root", ...])` reports a broken reference in an unlisted page and blocks on it in a listed one (rows of one test).
4. `make documents` on the repository ends with `documents ok (<seconds> s)`.
5. `make check` stays green.
6. docs: `docs/project-guide/shared.md`, the name check: the reader learns which references to another page's heading are checked, in which form, and what the finding says. `docs/project-guide/style.md`, rule 8: the reader learns to write a reference to another page's section in this form, so that it is checked. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: 1. Interface rule: the reference may have `)` or `,` between the heading and `in`/`of`. Criterion 1 has a row for `)` but none for `,`. Please add a `,` row. I would choose that.
   2. Interface rule: "A finding reads `<document>:<line>: <heading> is no heading of <target>`". Criterion 2 only says "one finding", so no test pins the text. Please state the exact finding text in criterion 2, or add a criterion for it. I would choose to add it to criterion 2.
   3. Interface rule: the heading text loses its backticks and asterisks. Criterion 1 has a backtick row but none for asterisks, which are the italics markers and may also appear inside the heading. Please say whether a row for a heading with asterisks inside is wanted. I would choose to add one. Also say whether `headings(target)` must strip backticks and asterisks from the linked page's headings (the Interface says so). If it must, which module does that, and which criterion tests it? As written, the real-document case, *`StageFinisher.finish`* against the heading *`StageFinisher.finish(aftermath)`*, has no test, and neither does a match against a heading that has backticks.
   4. Description: "References within one page, and links with a `#` anchor, stay as they are." The anchor case has a row in criterion 1. The within-one-page case has no criterion at all. Please add a row or remove the sentence. I would choose to add a row, such as a reference to the document's own file, which gives no finding.
   5. Criterion 3 reports and blocks on "a broken reference". Please also require, in the same test, that a document with a valid reference gives no finding, and that a reference to a page that is no document of the check gives no finding in `main`. Otherwise the `None` branch of `headings` is only tested in the domain function.
   6. Criterion 4 requires fixing the four real references. Criterion 6 (docs) names only `shared.md` and `style.md`. Please list `install.md`, `work-items.md`, `machine.md` and `agent-runtime.md` as pages the documenter must fix, and say what the reader must be able to do afterwards: find each referenced section under the name the target page writes.
