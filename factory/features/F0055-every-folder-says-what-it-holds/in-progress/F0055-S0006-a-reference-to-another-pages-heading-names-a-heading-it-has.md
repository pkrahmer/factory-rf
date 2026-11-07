---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 633
comments_read: [6706186597]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-07T11:27:08.786140Z'
  lease_duration: 60
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
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-07T11:25:13.178242Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-07T11:25:15.787107Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-07T11:25:35.500075Z'
  stage: intake
  run: bf31b02245b24720845868917064be44
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T11:25:40.502563Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-07T11:27:03.874740Z'
  stage: tests
  run: 2e0d117107b343a992fb901ceee80787
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-07T11:27:08.786140Z'
  stage: doing
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
  - `page_headings(text: str) -> set[str]` (public, same module): the headings of one page's heading lines with only the code marks stripped (backticks and asterisks), nothing else; `factory.entry.check_documents` builds `headings(target)` from it. `StageFinisher.finish` is not `StageFinisher.finish(aftermath)`.
  - `HeadingReference` is a frozen model with `document`, `line`, `heading` and `target`. The heading text loses its backticks and asterisks.
  - `headings(target)` gives the set of headings of the linked page, with backticks and asterisks removed, or `None` when the page is no document of the check. A reference to such a page gives no finding.
  - A finding reads `<document>:<line>: <heading> is no heading of <target>`.
- `factory.entry.check_documents`: the findings of `unresolved_headings` join the name check's findings, so they block in a listed document and are reported in any other.
- Tests: `tests/shared/domain/test_heading_references.py` (new) and rows in the entry tests of the name check, on documents the tests write (`tests/support/minimal_documents_support.py`), never on the real documents. Adding rows to those earlier modules needs no further leave; no earlier row changes its expected result, and if one would, that is a question.
- The real documents: any reference this check finds broken in a listed document is fixed in the docs stage of this story, so that `make documents` stays green. A fix names the heading as the target page writes it, or names the paragraph and the heading it stands under; no heading is renamed.

## Acceptance criteria

1. `heading_references` finds a reference in each form, with its line, heading and resolved target. Rows: italics with `in`, quotes with `of`, a closing `)` before `in`, a `,` before `in`, a heading with asterisks inside, a reference to the document's own file (no reference), a heading with backticks, a link in a subfolder (`../`), and no reference for a link with a `#` anchor, a link to a file that is not `.md`, and a heading text without `in` or `of` after it.
2. `unresolved_headings` gives one finding for a heading the linked page does not have, none for one it has, and none for a link to a page that is no document of the check; the finding reads exactly `<document>:<line>: <heading> is no heading of <target>`. Rows of one parametrized test.
   `page_headings` strips backticks and asterisks only: a heading with backticks matches the reference without them, one with asterisks matches too, and `StageFinisher.finish` does not match `StageFinisher.finish(aftermath)`. Rows of one parametrized test.
3. On minimal documents, `main(["--root", ...])` reports a broken reference in an unlisted page and blocks on it in a listed one, gives no finding for a valid reference and none for a reference to a page that is no document of the check (rows of one test).
4. `make documents` on the repository ends with `documents ok (<seconds> s)`.
5. `make check` stays green.
6. docs: `docs/project-guide/shared.md`, the name check: the reader learns which references to another page's heading are checked, in which form, and what the finding says. `docs/project-guide/style.md`, rule 8: the reader learns to write a reference to another page's section in this form, so that it is checked. The documenter also fixes the four broken references, in `docs/operator-guide/install.md`, `docs/operator-guide/work-items.md`, `docs/project-guide/machine.md` and `docs/operator-guide/agent-runtime.md`: the reader finds each referenced section under the name the target page writes, or as a named paragraph under the heading it stands in. `docs/decisions.md`: none.

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
4. 2026-11-07 human: Yes to all six, as you propose.
   1. Add a ',' row to criterion 1.
   2. Criterion 2 states the exact finding text: '<document>:<line>: <heading> is no heading of <target>'.
   3. Add a row with asterisks inside the heading. Yes, the linked page's headings lose their backticks and asterisks too. factory.entry.check_documents builds headings(target) from the target's heading lines and strips them there, through a small public function in factory.shared.domain.heading_references (for example page_headings(text) -> set[str]) with its own parametrized rows: a heading with backticks matches the reference without them, and a heading with asterisks matches too. The real case is no match and stays a finding: 'StageFinisher.finish' is not 'StageFinisher.finish(aftermath)'; only the code marks are stripped, nothing else, and the documenter fixes the reference.
   4. Add a row: a reference to the document's own file gives no reference (references within one page stay as they are).
   5. Yes: criterion 3's test also has a row with a valid reference (no finding) and a row with a reference to a page that is no document of the check (no finding).
   6. Yes: criterion 6 names install.md, work-items.md, machine.md (the project guide's) and agent-runtime.md as pages the documenter fixes; afterwards the reader finds each referenced section under the name the target page writes, or as a named paragraph under the heading it stands in.
5. factory: started intake as vm.
6. intake: accepted, with the human's answer (journal entry 4) written into the story.
   - Interface: concrete. `factory.shared.domain.heading_references` has `heading_references`, `unresolved_headings` and, from entry 4, `page_headings(text) -> set[str]`. I added the `page_headings` line to the Interface, and `factory.entry.check_documents` builds `headings(target)` from it. Every path it changes is code, so the route is tests, not docs-only.
   - Criteria: I added what entry 4 asked for.
     - Criterion 1 gains rows for `,`, for asterisks inside a heading and for a reference to the document's own file.
     - Criterion 2 states the exact finding text, and gains `page_headings` rows (backticks, asterisks, and `StageFinisher.finish` not matching `StageFinisher.finish(aftermath)`).
     - Criterion 3 gains the valid-reference row and the row for a page that is no document of the check.
     - Each criterion is testable by one parametrized test, and the failing side of every rule has a row.
   - Smoke test: `uv run python -m factory.entry.check_documents | tail -1` is runnable. It does not call pytest, so the `-q` rule does not apply. Its Expect line `documents ok (<seconds> s)` can be checked.
   - Docs criterion: it names what the reader must know about `shared.md` and `style.md`. I added the four pages the documenter fixes (`install.md`, `work-items.md`, `machine.md`, `agent-runtime.md`), with the reader finding each section under the name the target page writes. It dictates no sentences.
   - Architecture: the new module is in `shared/domain` and is pure. The entry wiring stays in `factory.entry.check_documents`.
   - Scope: it fits the feature's scope ("The document check resolves references to another page's heading (S0006)"). No earlier test changes, and the story states that no earlier row changes its result.
7. factory: started tests as vm.
8. tester: Tests written from the Interface and the criteria. They are red on purpose.
   - criterion 1: tests/shared/domain/test_heading_references.py::test_a_reference_to_another_pages_heading_is_found_with_its_line_heading_and_target. It has 11 rows: italics-in, quotes-of, closing-parenthesis-before-in, comma-before-in, asterisks-inside, own-file (no reference), backticks, other-folder (`../`), anchor (none), not-a-markdown-file (none), neither-in-nor-of (none).
   - criterion 2, `unresolved_headings`: tests/shared/domain/test_heading_references.py::test_a_reference_to_a_heading_the_linked_page_does_not_have_is_one_finding. Rows: missing-heading, which must give the exact text `<document>:<line>: <heading> is no heading of <target>`; existing-heading; no-document-of-the-check (`headings` returns `None`).
   - criterion 2, `page_headings`: tests/shared/domain/test_heading_references.py::test_a_pages_headings_lose_their_code_marks_and_nothing_else. Rows: backticks, asterisks, and only-code-marks-are-stripped (`StageFinisher.finish` does not match `StageFinisher.finish(aftermath)`).
   - criterion 3: tests/entry/test_check_documents_checked_files.py::test_a_reference_to_another_pages_heading_it_lacks_blocks_in_a_listed_file_only. It runs on minimal documents. Rows:
     - broken-not-listed: the finding comes under the report heading, exit 0.
     - broken-listed: the finding blocks, exit 1, no report.
     - valid: no finding.
     - no-document-of-the-check: a link to `docs/runs/a-run.md`, no finding.
   - criteria 4 to 6 (`make documents`, `make check`, docs): no test. The documenter and the factory's checks cover them.

   Files:
   - Created: tests/shared/domain/test_heading_references.py.
   - Changed: tests/entry/test_check_documents_checked_files.py. I added constants and one test at the end of it, as the story allows. No earlier row changed.

   Run of the two files: tests/shared/domain/test_heading_references.py fails at collection with `ModuleNotFoundError: No module named 'factory.shared.domain.heading_references'`, the module the runner could not import. In the entry test, the broken-not-listed and broken-listed rows fail on the assert, because no heading finding is printed yet. The valid and no-document rows pass already, as their side requires. I ran the entry module twice: once with the first try, which `make lint` refused (an f-string without placeholders, too many arguments), and once after the fix.

   `make lint` is green.

   `lint`: lint: green (0.2 s)
9. factory: started doing as vm.
