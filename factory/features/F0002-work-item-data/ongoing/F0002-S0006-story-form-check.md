---
stage: review
pr: 33
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
# Story form check

## Assignment (as of log entry 1)

Build the check of a story's form that code runs before and after every agent run and that the human can run on a draft (kept thing 9: a story is specified first, and its form is checked by code). It returns one finding for each rule a story breaks, each with a fixed message and, where it applies, the line of the body. The rules are v1's: a title line, every section of the project's own story form, criteria numbered 1 to n, the two closing criteria (the second-to-last contains `make check` and `green`, the last starts with `docs:`), a smoke test whose every code block is followed by an `Expect:` line, and a numbered journal. Because the sections come from F0002-S0004, a heading or a `# comment` inside a fenced block can no longer hide a section or fake the title, which v1's form check could not tell apart. Four findings are new in v1.1 and follow from the work item's data: a backlog story that carries front matter, a backlog story whose `Journal` already holds entries (the opening writes entry 1, so a second entry 1 would follow), a story in progress or done that has no state, and a journal whose data and text disagree in their number of entries (SI1.1 keeps both halves in step). The check of the file's place and the command for the human are the last story of this feature. The story is pure domain code.

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
10. With `folder` `backlog` and one entry or more found in rule 6: `a backlog story carries no journal entries`, on the line of the first entry. A backlog story has no journal: the opening (F0005-S0002) writes entry 1 into the `Journal` section, which the human leaves without entries.

Rules 7 and 10 are the checks of the human's file in the backlog. Rules 8 and 9 are for the factory's own calls, on a document that belongs to a work item's branch; a caller that holds only the specification of a started story (the text on `main` has no front matter) names the folder `backlog`, so that rules 8 and 9 are not asked of a document that cannot have a state (F0002-S0008).

The sections `Acceptance criteria`, `Smoke test` and `Journal` are the constants of `factory.domain.sections`. A rule that needs a section does nothing when the body has no such section; rule 2 reports it when the form requires it.

Tests: `tests/domain/test_story_form.py`. A test that constructs a model with an unknown field does so through a variable typed `type[BaseModel]`, and one that assigns to a frozen field does so with `setattr` (`CLAUDE.md`, Tests).

## Acceptance criteria

1. A complete story gives no finding: a title, the sections `Description`, `Interface`, `Acceptance criteria` (three items; the second-to-last `make check stays green.`, the last `docs: none, nothing changes.`), `Smoke test` (one fenced block followed by an `Expect:` line) and `Journal` (a heading and no entries, as a backlog story has), checked against a form that requires those five sections, with the folder `backlog` and no front matter.
2. `FormFinding(line=0, message="x")` raises `ValidationError`; `line=None` and `line=1` are valid; a `FormFinding` is frozen and refuses an unknown field with `ValidationError` (constructed through a variable typed `type[BaseModel]`).
3. A body without a `# ` line gives `the story has no title line` and a body whose only `# ` line is inside a fenced block gives it too.
4. Each section of the form that is missing gives `missing section: ## <heading>` in the form's order; a form with an added `## Notes` makes `Notes` required; a section whose heading occurs only inside a fenced block is reported as missing.
5. Criteria numbered 1, 2, 4 give the single finding `criterion numbered 4 where 3 is expected` on the line of the item `4.`; criteria starting at 2 give `criterion numbered 2 where 1 is expected`; criteria 1, 1 give `criterion numbered 1 where 2 is expected`; an `Acceptance criteria` section without items gives no finding.
6. A second-to-last criterion that lacks `make check`, or lacks `green`, gives `the second-to-last criterion must contain "make check" and "green"` on its line; one that has both, in a text spread over two lines of the item, gives none.
7. A last criterion whose text does not start with `docs:` (`Docs: x`, `done`) gives `the last criterion must start with "docs:"` on its line; `docs: none` gives none.
8. Exactly two criteria are checked: with the two items `1. a` and `2. b` both closing findings are given; with one item `1. a` and with no item no closing finding is given.
9. A `Smoke test` section without a code block gives `the Smoke test has no code block` on the heading's line.
10. A code block followed by prose, by the end of the section, or never closed gives `the code block opened at line <n> is not followed by an "Expect:" line` with `n` the line of its opening; blank lines between the block and `Expect:` are allowed; with two blocks only the one without `Expect:` is reported.
11. A smoke test block that contains the lines `## start the server` and `# comment` leaves the section whole: neither line is read as a heading or a title, and a story that is otherwise complete gives no finding.
12. Journal entries numbered 1, 3 give `journal entry numbered 3 where 2 is expected` on the line of the entry `3.` (checked with the folder `done` and a state whose journal lists two records, so that no rule about the state fires); indented lines in an entry are not entries; a `Journal` section without entries gives no finding.
13. With the folder `backlog` and `ignored_keys` equal to `["stage", "attempts"]` the finding is `a backlog story carries no front matter: stage, attempts`; with no ignored keys there is none.
14. With the folder `in-progress` or `done` and a document without state the finding is `the story has no state`; with a state there is none, and a backlog story without state gives none.
15. With the folder `in-progress`, a state whose `journal` lists 2 records and a body with 3 entries give `the journal data lists 2 entries but the text shows 3`; a state whose `journal` lists 2 records and a body without a `Journal` section give `the journal data lists 2 entries but the text shows 0`; equal numbers give no finding; the backlog folder gets no finding about the journal data.
16. With the folder `backlog` and a `Journal` section that holds the entries 1 and 2, the single journal finding is `a backlog story carries no journal entries`, on the line of entry 1; a `Journal` section without entries and a body without a `Journal` section give none; the same body with the folder `in-progress` and a state whose journal lists two records gives no such finding.
17. A story that breaks several rules gets all its findings, in the order of the rules: title, missing sections, criteria numbering, closing criteria, smoke test, journal numbering, then the rules about front matter, state and journal (7 to 10).
18. make check stays green.
19. docs: `docs/project-guide.md` lists the rules of the form check with their messages, says that the sections come from the project's story form and that code blocks are respected, and says that a backlog story's `Journal` has no entries because the opening writes entry 1; `docs/decisions.md` records the four findings that v1 did not make.

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
body = '# S\n\n## Journal\n'
for folder in ('in-progress', 'backlog'):
    print(folder, [f.message for f in check_story_form(WorkItemDocument(state=None, body=body), '', folder=folder)])
"
```
Expect: two lines: `in-progress ['the story has no state']` and `backlog []`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `src/factory/domain/story_form.py` names `FormFinding` and `check_story_form(document, form, *, folder)` with concrete signatures. All ten rules give message, line and order. `WorkItemDocument` (with `state` and `ignored_keys`), `required_sections` and the section constants exist in `factory.domain`, so the Interface can be built on them.
   - Criteria: each is testable by one test function. Criteria 1 and 17 are the whole-story and ordering checks. Every rule has its failing side: title 3, sections 4, numbering 5, closing 6-8, smoke test 9-10, journal numbering 12, front matter 13, state 14, journal data 15, backlog entries 16. Criterion 2 covers both sides of the line limit (0, None, 1).
   - Demo: both blocks run as written. I checked the line numbers of the first one by hand (10, 11 and 13) and the finding order matches the rules. Each `Expect:` line is checkable against the output.
   - Architecture: pure domain code in `factory.domain` that imports only other domain modules. No I/O, no wrapper, no new dependency.
   - Scope: this is kept thing 9 and decision 8 of the feature. The place check and the command stay with S0008, which is outside this story.
3. tester: red tests for the story form check written in `tests/domain/test_story_form.py` (new file). Every test builds a story body from five default sections, then replaces or drops one section. The form requires Description, Interface, Acceptance criteria, Smoke test and Journal. Line numbers are looked up in the body and counted from 1.
   - criterion 1: test_a_complete_backlog_story_gives_no_finding
   - criterion 2: test_a_finding_takes_no_line_or_a_positive_one (None, 1), test_a_finding_refuses_line_zero, test_a_finding_is_frozen_and_refuses_an_unknown_field (setattr per field; unknown field through `type[BaseModel]`)
   - criterion 3: test_a_body_without_a_title_line_has_no_title, test_a_title_line_inside_a_code_block_is_no_title
   - criterion 4: test_each_missing_section_of_the_form_is_reported_in_the_forms_order, test_a_section_added_to_the_form_is_required, test_a_heading_only_inside_a_code_block_is_a_missing_section
   - criterion 5: test_the_first_misnumbered_criterion_is_reported_on_its_line (1,2,4 / starting at 2 / 1,1), test_an_acceptance_criteria_section_without_items_gives_no_finding
   - criterion 6: test_a_second_to_last_criterion_without_make_check_and_green_is_reported (lacks each), test_a_second_to_last_criterion_spread_over_two_lines_is_read_whole
   - criterion 7: test_a_last_criterion_not_starting_with_docs_is_reported (`Docs: x`, `done`), test_a_last_criterion_starting_with_docs_gives_no_finding
   - criterion 8: test_two_criteria_are_checked_for_both_closing_criteria, test_fewer_than_two_criteria_get_no_closing_finding (one item, none)
   - criterion 9: test_a_smoke_test_without_a_code_block_is_reported_on_its_heading
   - criterion 10: test_a_code_block_without_an_expect_line_is_reported_on_its_opening (prose, end of section, never closed; the test keeps only the Expect findings because an unclosed block also hides `## Journal`), test_blank_lines_may_stand_between_a_code_block_and_its_expect_line, test_of_two_code_blocks_only_the_one_without_expect_is_reported
   - criterion 11: test_headings_and_comments_inside_a_smoke_test_block_leave_the_story_whole (the complete story gives []; without a real title, the only finding is the title finding, so `# comment` is not read as a title)
   - criterion 12: test_the_first_misnumbered_journal_entry_is_reported_on_its_line, test_indented_lines_in_a_journal_entry_are_no_entries, test_a_journal_without_entries_gives_no_finding (done, state with 0 records)
   - criterion 13: test_a_backlog_story_with_front_matter_is_reported_with_its_keys (the no-keys side is criterion 1's test)
   - criterion 14: test_a_started_story_without_state_is_reported, test_a_started_story_with_a_state_has_one (in-progress and done each); a backlog story without state is criterion 1's test
   - criterion 15: test_journal_data_and_text_that_disagree_are_reported (3 entries; no Journal section, against a form without Journal), test_journal_data_and_text_that_agree_give_no_finding, test_the_backlog_gets_no_finding_about_the_journal_data (backlog document with a 2-record state and no entries)
   - criterion 16: test_a_backlog_story_with_journal_entries_is_reported_on_the_first, test_a_backlog_story_without_a_journal_section_has_no_entries, test_a_started_story_may_carry_journal_entries (an empty Journal section is criterion 1's test)
   - criterion 17: test_a_backlog_story_gets_all_its_findings_in_the_order_of_the_rules (rules 1-7 and 10), test_a_started_story_gets_all_its_findings_in_the_order_of_the_rules (rules 1-6 and 9). No single story can break both rule 7/10 and rule 8/9, because they need different folders, so this criterion takes two tests.
   - criteria 18 and 19: not tested here (the check gate and the docs).
   `make test`: one collection error, `ModuleNotFoundError: No module named 'factory.domain.story_form'`. That module is the only one the test runner could not import. `make lint` is green.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: built the story form check. All tests in `tests/domain/test_story_form.py` pass and `make check` is green (coverage of the new module is 99 %).
      - `src/factory/domain/story_form.py` (new): `FormFinding` (frozen, forbids unknown fields, `line: PositiveInt | None`) and `check_story_form(document, form, *, folder)`.
        - The body is read once into a private `_Body`: its lines, its sections from `sections()`, and the set of lines outside fenced blocks.
        - Numbered items (`^\d+\. ` at column 0, outside blocks) are collected per section into `_Item` ranges. Criteria and journal entries share this collection and the numbering rule. Each item runs to the next item or to the end of the section, which is how the closing-criteria rule reads an item spread over several lines.
        - The rules run in the Interface's order. Rules 7 and 10 run for `backlog`; rules 8 and 9 for the other folders.
      - `src/factory/domain/sections.py`: renamed `_lines_outside_blocks` to the public `lines_outside_blocks` (with a docstring) so the form check reuses it. The only behaviour change is that the name is now public.
      - Main decision: build every rule on the section reader's view (sections, `code_blocks`, lines outside blocks). That way a heading, a `# ` line or a numbered line inside a fence can never count as structure. Rejected: a second line scanner with its own fence tracking inside story_form.py, which would duplicate `sections.py` and could drift from it.
      - Refactor commit 1582a83: dropped the docstrings on the private models, as `CLAUDE.md` asks. Nothing else needed changing.
      - Demo: both blocks print exactly the expected lines.
      - Noticed, not touched: an unclosed smoke-test block runs to the end of the body and hides any later `## Journal`. The Interface accepts this, and the tests allow for it.

   `make check`: check: green
5. reviewer: one finding, in group 1 (acceptance criteria). Criteria 1 to 17 each have a test that checks what the criterion names. The coder's entry records `make check` green. I read `src/factory/domain/story_form.py` against the ten rules of the Interface and found no difference in message, line or order.
   1. `tests/domain/test_story_form.py` (the criterion 5 tests): rule 3 says criteria are numbered lines "at column 0, outside code blocks", but no test checks the refused side of either limit in the `Acceptance criteria` section. `CLAUDE.md` (Tests) says "at column 0" gets an indented case, and the reviewer counts an untested side as a finding. `_items` is shared with the journal, but the journal test `test_indented_lines_in_a_journal_entry_are_no_entries` covers only rule 6's indentation, and no test anywhere puts a numbered line inside a fenced block. Fix: the tester adds a test where criteria such as `1. a`, an indented `   2. x`, a fenced block holding the line `3. y`, then `2. make check stays green.` and `3. docs: none.` give no finding. Gap in the story: criterion 5 does not spell out this refused side, so the human may want to add it there.
   Not a finding, noted for the human: rule 6 defines journal entries as numbered lines at column 0 but does not say "outside code blocks". The code also skips fenced lines in the `Journal` section (`_items` in `src/factory/domain/story_form.py`). That fits the Assignment's point that code blocks are respected, and the docs criterion says the same.
6. coder: coder (round 1): the reviewer's one finding is a missing test, not a code defect, so this goes to the tester. I did not touch the tests (R9). The test to add is in `tests/domain/test_story_form.py`, next to the criterion 5 tests. It should give an `Acceptance criteria` section holding `1. a`, an indented `   2. x`, a fenced block with the line `3. y`, then `2. make check stays green.` and `3. docs: none.`, and assert that `check_story_form` returns no finding. That covers the refused side of "at column 0" and of "outside code blocks" in rule 3.
      - The code already handles this case, so no code change is needed. `src/factory/domain/story_form.py` reads items only from lines outside fenced blocks and only at column 0. I ran exactly that body through `check_story_form` (folder `backlog`, empty form) and it returned `[]`.
      - Left open for the human, as the reviewer noted: rule 6 (journal entries) does not say "outside code blocks", but the code skips fenced lines there too. Criterion 5 could spell out the refused side the new test covers.
      - Unchanged since round 0: `make test` is green, total coverage 99.59 %.
7. tester: tester (round 1, approved test change): added the test from the coder's entry 6 (the reviewer's finding 1) as `test_indented_and_fenced_numbered_lines_are_no_criteria` in `tests/domain/test_story_form.py`, next to the criterion 5 tests. It is the refused side of rule 3's "at column 0, outside code blocks". The `Acceptance criteria` section holds `1. a`, an indented `   2. x`, a fenced block with the line `3. y`, then `2. make check stays green.` and `3. docs: none.`. The test asserts that `check_story_form` returns `[]`. Nothing else changed. The new test passes against the existing code, as the coder said it would.
      Still open for the human, carried over from entries 5 and 6: rule 6 (journal entries) does not say "outside code blocks", and criterion 5 could spell out the refused side this test now covers.

      `make test`: green, total coverage 99.59 %
      `make lint`: green

   `make lint`: lint: green
   `make test`: test: green
8. coder: coder (round 1): no code change this round. The reviewer had one finding (entry 5): rule 3 had no test for a numbered line that is indented or inside a fenced block. The tester covered it with `test_indented_and_fenced_numbered_lines_are_no_criteria` in `tests/domain/test_story_form.py` (entry 7). That test passes against the unchanged `src/factory/domain/story_form.py`, because `_items` reads only lines outside fenced blocks and at column 0.
      - I made no refactor and no commit. The diff is the same as round 0 (5195b77, 1582a83).
      - Still open for the human, carried over from entries 5 to 7: rule 6 (journal entries) does not say "outside code blocks", but the code skips fenced lines there too. Criterion 5 could also state the refused side that the new test covers.

      `make check`: check: green, total coverage 99.59 %

   `make check`: check: green
