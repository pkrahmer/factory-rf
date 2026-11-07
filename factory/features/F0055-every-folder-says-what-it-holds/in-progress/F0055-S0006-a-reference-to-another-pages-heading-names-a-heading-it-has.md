---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 633
comments_read: [6706186597]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-07T11:40:57.608858Z'
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
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-07T11:34:17.106602Z'
  stage: doing
  run: 5cd4b0d1dbaf4084ae2b9eda7e191642
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-07T11:34:22.322716Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-07T11:35:43.458237Z'
  stage: review
  run: 4436660754b94cdca7a2af14be4c379d
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-07T11:35:48.648536Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-07T11:36:07.027902Z'
  stage: doing
  run: 03d0e3eb0796498fbc4dac9f0c5f200c
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-07T11:36:12.008837Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-07T11:36:37.144745Z'
  stage: tests
  run: d293f9c974014d938e5a65530b49e376
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-07T11:36:42.039894Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-07T11:40:52.605786Z'
  stage: doing
  run: af5c72b8f9974a2c91f1d656a4f6bbdc
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-07T11:40:57.608858Z'
  stage: review
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

1. `heading_references` finds a reference in each form, with its line, heading and resolved target. Rows: italics with `in`, quotes with `of`, a closing `)` before `in`, a `,` before `in`, a heading with asterisks inside, a reference to the document's own file (no reference), a heading with backticks, a link in a subfolder (`../`), and no reference for a link with a `#` anchor, a link to a file that is not `.md`, a heading text without `in` or `of` after it, plain text that is neither in italics nor in quotes before `in` and the link (`See the guide in [machine.md](machine.md).`), and another mark than `)` or `,` between the heading and `in` (`*The two passes*; in [machine.md](machine.md)`); and for two italic spans on one line (`*one* and *The two passes* in [machine.md](machine.md)`) only the span right before `in` is the reference.
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
10. coder: The document check now looks up each reference to another page's heading in that page's headings. `make check` is green, and the tester's two test files pass.

    Built:
    - `src/factory/shared/domain/heading_references.py` (new) holds `HeadingReference`, `heading_references`, `page_headings` and `unresolved_headings`.
      - One regular expression finds a reference: a heading in italics or double quotes, an optional `)` or `,`, then `in` or `of` and a Markdown link.
      - The heading may not start or end with a space. Without that rule, the text between two separate italic spans could be taken as a heading.
      - A target is dropped when it has a `#`, does not end in `.md`, or resolves to the document's own file.
      - Headings lose only their backticks and asterisks.
    - `src/factory/shared/domain/documents.py`: I made two private helpers public so the new module reuses them instead of copying them.
      - `_link_name` is now `link_name`; it resolves a link against the document's folder and drops the fragment.
      - `_checked_lines` is now `checked_lines`; it gives the lines outside fenced blocks and the exempt sections.
      - Both got docstrings, and their uses there were renamed. Behaviour is unchanged.
    - `src/factory/entry/check_documents.py`: the new `_heading_findings` reads every named document once and builds each one's headings with `page_headings`. `headings(target)` is that map's `.get`, so a page that is no document of the check gives `None` and no finding. The findings become `GatedFinding`s next to the name check's, so they block in a listed document and are reported in any other.

    Main choice: reuse the name check's link resolution and line selection. The alternative I rejected was writing the heading check's own path joining and fence skipping, which would have copied existing helpers and could drift from the name check.

    Refactor pass: I read the diff and found nothing to change.

    Noticed, not touched:
    - `make documents` on the repository now blocks on three of the four references the story names: `install.md:121`, `work-items.md:66` and the project guide's `machine.md:487`. The docs stage of this story fixes those (criteria 4 and 6).
    - The fourth, `agent-runtime.md:407`, reads "The stage environment" under *Configuration* in [install.md](install.md). In the checked form only *Configuration* comes right before `in` and the link, and `install.md` has that heading, so the check gives no finding there. The quoted paragraph name is not checked. The documenter fixes it by hand, as criterion 6 says.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
11. factory: started review as vm.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (5 files) and the work item. I read the new module, the entry wiring, the two helpers made public in `documents.py`, and both test files, checking them against criteria 1 to 3 and the Interface. I also ran `make duplicates` (a report). Its 6 new findings are all outside this diff (`claude_runtime`/`opencode_runtime`, `hand_over`/`acceptance`, `folder_readmes.readme_problems`, `cost_records`), so they are not counted against this story.

    Findings:
    1. criterion 1 extended: it needs its test. Location: `## Acceptance criteria` 1, and `tests/shared/domain/test_heading_references.py::test_a_reference_to_another_pages_heading_is_found_with_its_line_heading_and_target`. The Interface's rule "a heading text in italics or in double quotes, then optional `)` or `,`" had no row for its failing side, so no test pins that it is enforced. Missing were plain text before `in [x.md]`, and a mark other than `)` or `,`. Plain text is the most common prose in the documents (`described in [machine.md](machine.md)`). The coder's own rule that a heading may not start or end with a space (journal entry 10) had no row either: on a line with two italic spans, only the span right before `in` counts. The code handles all three as stated (`_REFERENCE` in `src/factory/shared/domain/heading_references.py:11`), so no change under `src/` is needed. I wrote three rows into criterion 1's row list: plain text gives no reference, `;` gives no reference, and two italic spans give only the second. This is a gap in the story, not the tester's. Fix: the tester adds these three rows to that parametrized test, with no new test function.

    Checked and in order:
    - Criteria 1 to 3: every listed row is present, and each test checks what its criterion names. Criterion 1 has all 11 rows. Criterion 2 pins the exact finding text and the three `page_headings` rows. Criterion 3 runs on minimal documents with the four rows. The factory's `make check` after the coder was green (entry 10).
    - Architecture: the new module is pure, in `shared/domain`. It reuses `link_name` and `checked_lines` rather than copying them. The file reading stays in `factory.entry.check_documents`.
    - Security: no strings passed to a shell, no markers that silence a check, no secrets.
    - Quality: names and docstrings fit what they describe. `_FRAGMENT = "#"` repeats a private constant from `documents.py`, which is trivial and not worth a round.
    - Hygiene: the journal states the main choice (reuse the name check's link resolution) and what was rejected. The Description matches what was built.
      - The fourth reference (`agent-runtime.md:407`) is not caught by the form the check reads. The coder says so in entry 10, and criterion 6 gives the hand fix to the documenter.
      - The docs criterion still says what the reader must learn.
    - Documents: the diff changes none.

    Earlier tests:
    - `tests/entry/test_check_documents_checked_files.py`: none needed. It only adds constants and one test at the end, and every earlier test is unchanged. The story's Interface also allows rows in this module.
13. factory: started doing as vm.
14. coder: No code changed. The reviewer's finding (entry 12) extends criterion 1 with three rows, and those rows need only a test change. The code already handles all three: `_REFERENCE` in `src/factory/shared/domain/heading_references.py` gives no reference for plain text or for a mark other than `)` or `,`, and takes only the span right before `in`.

    The tester should add three rows to the existing parametrized test `tests/shared/domain/test_heading_references.py::test_a_reference_to_another_pages_heading_is_found_with_its_line_heading_and_target`, with no new test function:
    - **Plain text, no reference:** `See the guide in [machine.md](machine.md).`
    - **Another mark, no reference:** `*The two passes*; in [machine.md](machine.md)`
    - **Two italic spans:** `*one* and *The two passes* in [machine.md](machine.md)` gives exactly one reference, with the heading `The two passes`.

    I checked that the test has none of these rows yet (its current ids run from italics-in to neither-in-nor-of). The Description already lists the three rows in criterion 1, so it needs no rewrite.

    Noticed, not touched: nothing beyond entry 10. `make documents` still blocks on `install.md:121`, `work-items.md:66` and the project guide's `machine.md:487` until the docs stage fixes them. The check does not catch the fourth reference, `agent-runtime.md:407`, so the documenter fixes it by hand.
15. factory: started tests as vm.
16. tester: Made the test change that the reviewer's finding (entry 12) and the coder's entry 14 call for. I changed no other test and added no new test function.

    Change: `tests/shared/domain/test_heading_references.py::test_a_reference_to_another_pages_heading_is_found_with_its_line_heading_and_target` has three new rows on criterion 1's refused side and on the two-span case:
    - plain-text: `See the guide in [machine.md](machine.md).` gives no reference.
    - another-mark-before-in: `*The two passes*; in [machine.md](machine.md)` gives no reference.
    - two-italic-spans: `*one* and *The two passes* in [machine.md](machine.md)` gives exactly one reference, heading `The two passes`, target `docs/project-guide/machine.md`.

    Criterion mapping (unchanged apart from the new rows):
    - criterion 1: tests/shared/domain/test_heading_references.py::test_a_reference_to_another_pages_heading_is_found_with_its_line_heading_and_target (now 14 rows)
    - criterion 2: tests/shared/domain/test_heading_references.py::test_a_reference_to_a_heading_the_linked_page_does_not_have_is_one_finding and ::test_a_pages_headings_lose_their_code_marks_and_nothing_else
    - criterion 3: tests/entry/test_check_documents_checked_files.py::test_a_reference_to_another_pages_heading_it_lacks_blocks_in_a_listed_file_only

    Files: I changed `tests/shared/domain/test_heading_references.py` (this story's own file) and created none. The test runner could import every module.

    Run: `uv run pytest -q tests/shared/domain/test_heading_references.py` passed all 20 tests, so the existing code already handles the new rows, as the coder said. `make lint` is green.

    `lint`: lint: green (0.2 s)
17. factory: started doing as vm.
18. coder: No code changed this round. The tester's three new criterion-1 rows (entry 16: plain-text, another-mark-before-in, two-italic-spans) pass against the existing code. I ran `make check` and it is green, coverage 99.21 %.

    What was built is unchanged from entry 10:
    - `src/factory/shared/domain/heading_references.py` (new) holds `HeadingReference`, `heading_references`, `page_headings` and `unresolved_headings`.
    - `src/factory/shared/domain/documents.py`: `link_name` and `checked_lines` are now public so the new module can reuse them.
    - `src/factory/entry/check_documents.py`: `_heading_findings` adds the heading findings to the name check's, so they block in a listed document and are reported in any other.

    Main choice (as in entry 10): reuse the name check's link resolution and line selection. I rejected a separate copy of path joining and fence skipping.

    Refactor pass: nothing to change. This round's diff touches only the tester's file.

    The Description already lists the three rows, so it needs no rewrite.

    Noticed, not touched (as in entry 14):
    - `make documents` still blocks on `install.md:121`, `work-items.md:66` and the project guide's `machine.md:487` until the docs stage fixes them.
    - The check does not catch `agent-runtime.md:407`, so the documenter fixes it by hand.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
19. factory: started review as vm.
