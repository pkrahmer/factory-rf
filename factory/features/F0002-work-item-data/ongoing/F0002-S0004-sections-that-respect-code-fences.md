---
stage: doing
pr: 31
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Sections that respect code fences

## Assignment (as of log entry 1)

Build the one place that finds the title and the `## ` sections of a Markdown body: pure functions over text that know code fences, so that a line such as `## start the server` inside a fenced block is never taken as a section heading and a `# comment` in a fenced block is never taken as the title (SI1.3; the hazard v1 listed as a limit of its form check). The module also finds the fenced blocks themselves, because the story form check needs their ends, takes a section's text, inserts a paragraph first under a heading (used later for the human's reason under a recommendation), and reads the required sections from the project's story form. The project's form names the sections, so the factory's code knows only three of them as constants: `Acceptance criteria`, `Smoke test` and `Journal`. The story covers SI1.3 and keeps kept thing 9 (the form is checked by code, from the project's own form). It is pure domain code; nothing reads a file.

## Interface

`src/factory/domain/sections.py`

```python
ACCEPTANCE_CRITERIA = "Acceptance criteria"
SMOKE_TEST = "Smoke test"
JOURNAL = "Journal"

class Section(BaseModel):
    heading: str                  # the text after "## ", stripped
    start: NonNegativeInt         # index of the heading line
    end: NonNegativeInt           # index after the section's last line

class CodeBlock(BaseModel):
    start: NonNegativeInt         # index of the opening line
    end: NonNegativeInt | None    # index of the closing line; None when the block is never closed

def split_lines(body: str) -> list[str]: ...
def code_blocks(lines: Sequence[str]) -> list[CodeBlock]: ...
def title(body: str) -> str | None: ...
def sections(body: str) -> list[Section]: ...
def section_text(body: str, heading: str) -> str | None: ...
def insert_paragraph(body: str, heading: str, paragraph: str) -> str: ...
def required_sections(form: str) -> list[str]: ...
```

`Section` and `CodeBlock` are frozen and forbid unknown fields. The rules; each has a criterion below:

- `split_lines(body)` splits at `"\n"` and drops the last element when it is empty, so a final newline gives no extra line; `""` gives `[]`. Every index in this module is an index into this list.
- A code block opens at a line that starts, after optional leading spaces or tabs, with three or more backticks or three or more tildes (an info string may follow the run). It closes at the first later line that consists, after optional leading spaces or tabs, of the same character repeated at least as many times as the opening run, followed by nothing but whitespace. A line of the other character, a shorter run, or a run followed by text does not close it. A block that is never closed runs to the end of the lines and has `end` `None`. A line is in a block from its opening line to its closing line inclusive.
- A heading is a line outside every block that starts with `## ` at column 0. `### x`, an indented `## x`, `##x`, `##` and `# x` are not headings. A section runs from its heading line to the next heading line, or to the end of the lines; lines before the first heading belong to no section.
- The title is the text, stripped, after `# ` of the first line outside every block that starts with `# ` at column 0; there is none when no such line exists. `#x` and `## x` are not titles.
- `section_text(body, heading)` finds the first section whose heading equals `heading` exactly (case-sensitive) and returns its lines after the heading line joined with `"\n"`, without leading and trailing blank lines; `""` for a section without text; `None` when there is no such section.
- `insert_paragraph(body, heading, paragraph)` puts the paragraph (it may have several lines) directly under the heading line of the first such section, with one blank line between the heading and the paragraph and one blank line between the paragraph and what the section held before, whose own leading blank lines are dropped; nothing follows the paragraph when the rest of the body is empty. The result ends with a newline exactly when `body` did. It raises `WorkItemFormatError` with the fault `missing section: ## <heading>` when no section has the heading, a heading that appears only inside a block included, and `ValueError` when the paragraph is blank.
- `required_sections(form)` is the headings of `sections(form)` in order, so a project that adds a `## ` section to its form makes that section required.

Tests: `tests/domain/test_sections.py`. A test that constructs a model with an unknown field does so through a variable typed `type[BaseModel]`, and one that assigns to a frozen field does so with `setattr` (`CLAUDE.md`, Tests).

## Acceptance criteria

1. `split_lines` gives `["a", "b"]` for `"a\nb\n"` and for `"a\nb"`, `[]` for `""`, `[""]` for `"\n"` and `["a", ""]` for `"a\n\n"`.
2. `code_blocks` of the lines `x`, three backticks followed by `python`, `a`, three backticks, `y`, three tildes, `b`, three tildes gives the blocks `(start=1, end=3)` and `(start=5, end=7)`; an opening and a closing line that are indented are recognised too.
3. A block opened by four backticks is not closed by a line of three backticks and is closed by four or five; a tilde line does not close a backtick block; a closing run followed by text does not close; a block that is never closed has `end` `None` and holds every later line.
4. `sections` of the body `# T`, a blank line, `intro`, a blank line, `## A`, a blank line, `text`, a blank line, `## B` (lines 0 to 8) gives `Section(heading="A", start=4, end=8)` and `Section(heading="B", start=8, end=9)`; the lines before `## A` belong to no section.
5. A `## ` line inside a block opened by backticks, inside one opened by tildes and inside one that is never closed is not a heading: for the lines `## A`, three backticks, `## B`, three backticks, `## C`, `sections` lists `A` from 0 to 4 and `C` from 4 to 5; with an unclosed block after `## A` only `A` is listed and it runs to the end.
6. `### x`, ` ## x` (indented), `##x`, `##` and `# x` are not headings, and a heading's text is stripped of trailing whitespace.
7. `title` returns the stripped text of the first `# ` line outside the blocks, `None` for a body without one, and ignores a `# comment` line inside a fenced block, `#x` and `## x`.
8. `section_text` returns the text of a section without its heading and without leading and trailing blank lines, keeps the blank lines and fenced blocks inside it, returns `""` for a heading with no text, `None` for a missing heading and for a heading spelled in another case, and the first section when a heading occurs twice.
9. `section_text` of a section that contains a fenced block with the lines `## x` and `# y` returns the whole section including the block, and `section_text` of a heading that occurs only inside a fenced block is `None`.
10. `insert_paragraph("## Verdict\n\nAccepted.\n", "Verdict", "Reason.")` is `"## Verdict\n\nReason.\n\nAccepted.\n"`.
11. `insert_paragraph` into an empty last section, `"## A\n"`, gives `"## A\n\nX\n"`; into an empty section before another, `"## A\n\n## B\n"`, gives `"## A\n\nX\n\n## B\n"`; a body without a final newline, `"## A\n\nold"`, gives `"## A\n\nX\n\nold"`.
12. `insert_paragraph` puts a paragraph of several lines in whole under the first matching heading and leaves every line outside the insertion as it was.
13. `insert_paragraph` raises `WorkItemFormatError` with the fault `missing section: ## Verdict` when no section is called `Verdict`, also when `## Verdict` occurs only inside a fenced block.
14. `insert_paragraph` raises `ValueError` for the paragraphs `""` and `"  \n"`.
15. `required_sections` of a form with a title, a comment line, the headings `## Description`, `## Interface`, a `### Sub` heading, a fenced block that holds `## Hidden`, and `## Journal` is `["Description", "Interface", "Journal"]`.
16. `ACCEPTANCE_CRITERIA`, `SMOKE_TEST` and `JOURNAL` are `"Acceptance criteria"`, `"Smoke test"` and `"Journal"`; `Section` and `CodeBlock` are frozen and refuse an unknown field with `ValidationError`.
17. make check stays green.
18. docs: `docs/project-guide.md` explains how sections are found (outside code fences, exact heading text, the three constants) and says that every module that needs a heading or a fenced block uses `factory.domain.sections`; `docs/decisions.md` records that headings inside fences are ignored, which v1 did not do.

## Demo

```bash
uv run python -c "
from factory.domain.sections import insert_paragraph, section_text, sections, title
fence = chr(96) * 3
body = '# Story\n\n## Demo\n\n' + fence + 'bash\n## start the server\necho ok\n' + fence + '\nExpect: ok\n\n## Journal\n\n1. 2026-10-12 human: created.\n'
print(title(body))
print([s.heading for s in sections(body)])
print(repr(section_text(body, 'Demo')))
print(insert_paragraph(body, 'Journal', 'Note.').split('\n')[10:])
"
```
Expect: four lines: `Story`; `['Demo', 'Journal']` (the `## start the server` line inside the fence is not a heading); one quoted string that still contains `## start the server` and `Expect: ok` (the whole Demo section, fence included); and `['## Journal', '', 'Note.', '', '1. 2026-10-12 human: created.', '']`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `src/factory/domain/sections.py` names the constants, the two frozen models and seven functions with signatures. Every behaviour in its comments (line splitting, fence open/close, heading and title rules, `section_text` trimming, `insert_paragraph` blank-line layout and trailing newline, `required_sections`) is stated as a rule. `WorkItemFormatError` already exists in `factory.domain.errors` (fault, path).
   - Criteria: 1–16 are each testable by one test function from the examples given. Each rule has its failing side: not a heading (6), not a title (7), no matching section gives `None` (8, 9), a missing section raises `WorkItemFormatError` (13), a blank paragraph raises `ValueError` (14), a fence that is not closed (3, 5), and models that refuse unknown fields (16). 17 and 18 close the list as required.
   - Demo: one runnable `uv run python -c` command. Its `Expect:` line gives four checkable outputs, including the exact list for the `Journal` insert.
   - Architecture: pure domain code in `factory.domain`, with no I/O and no imports from higher layers. It matches the layer rules in `CLAUDE.md`.
   - Scope: this covers the "Sections (SI1.3)" scope item of F0002 and decisions 5 and 6 of `FEATURE.md`. Nothing is taken from "Out of scope". The journal and the form check are left to S0005 and S0006.
3. tester: red tests written for criteria 1–16 in the new file `tests/domain/test_sections.py`.
   - criterion 1: tests/domain/test_sections.py::test_split_lines_drops_only_an_empty_last_element (all five cases)
   - criterion 2: ::test_backtick_and_tilde_blocks_are_found, ::test_indented_opening_and_closing_lines_are_recognised (space-indented opening line, tab-indented closing line)
   - criterion 3: ::test_a_block_closes_only_at_a_run_of_its_own_character_at_least_as_long. Cases: four backticks not closed by three and closed by four or five; a tilde line inside a backtick block; a closing run followed by text; a run followed by trailing whitespace still closes; an unclosed block gives `end=None`.
   - criterion 4: ::test_sections_run_from_heading_to_next_heading
   - criterion 5: ::test_a_heading_inside_a_fenced_block_is_not_a_heading (backticks and tildes), ::test_a_heading_after_an_unclosed_block_is_not_a_heading
   - criterion 6: ::test_lines_that_are_not_level_two_headings_open_no_section, ::test_a_heading_text_is_stripped_of_trailing_whitespace
   - criterion 7: ::test_the_title_is_the_first_level_one_heading_outside_blocks (includes a `# comment` line inside a closed fence and inside an unclosed fence)
   - criterion 8: ::test_section_text_is_the_trimmed_text_under_the_first_matching_heading (inner blank lines and a fence kept, empty section gives `""`, missing heading or another case gives `None`, a repeated heading gives the first one)
   - criterion 9: ::test_section_text_keeps_a_fenced_block_with_heading_lines_whole
   - criterion 10: ::test_a_paragraph_goes_first_under_the_heading
   - criterion 11: ::test_a_paragraph_in_an_empty_section_or_a_body_without_final_newline
   - criterion 12: ::test_a_paragraph_of_several_lines_goes_whole_under_the_first_heading (the body has another section before the target and a second `## Verdict` after it, and checks the exact full result)
   - criterion 13: ::test_inserting_under_a_missing_heading_is_a_format_error (no such heading; heading only inside a fence)
   - criterion 14: ::test_a_blank_paragraph_is_refused
   - criterion 15: ::test_required_sections_are_the_form_headings_in_order (the "comment line" is an HTML comment `<!-- comment -->`)
   - criterion 16: ::test_the_three_known_section_names, ::test_section_and_block_are_frozen_and_refuse_unknown_fields (construction through `type[BaseModel]`, assignment through `setattr`)

   Interpretations: where a criterion leaves a detail open, the test applies the rule stated in the Interface:
   - criterion 3: a closing run followed only by whitespace closes the block.
   - criterion 7: an unclosed fence hides a later `# ` line.

   Neither adds behaviour beyond the stated rules, so I raised no question.

   `make test` fails at collection, as expected: `ModuleNotFoundError: No module named 'factory.domain.sections'` is the one module that could not be imported. `make lint` is green after `ruff format`.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
