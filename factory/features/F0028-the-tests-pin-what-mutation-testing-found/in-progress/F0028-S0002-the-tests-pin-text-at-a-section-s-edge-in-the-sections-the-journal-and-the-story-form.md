---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 313
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-20T01:39:06.729105Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T01:26:59.736860Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T01:26:59.742643Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T01:27:19.968405Z'
  stage: intake
  run: 4fd899352ddf48b7acfa9f0ff62261ba
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T01:27:41.154801Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T01:29:39.335978Z'
  stage: tests
  run: c0bcf80516a1406482af751d23fe8f40
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T01:29:59.714867Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T01:31:47.335665Z'
  stage: doing
  run: 2b3222460d1349bdb057de7b7402c48d
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T01:32:08.858923Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T01:32:50.900415Z'
  stage: review
  run: 2aace54dd999463a89d244885da995e8
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T01:33:11.476192Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-20T01:33:22.691166Z'
  stage: doing
  run: 4d10ab4bb0dd4a14bc86cbcbf1a081cf
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T01:33:43.882534Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-20T01:35:25.889550Z'
  stage: tests
  run: ec55b5a1c2a446d696b022e2bfe7097a
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-20T01:35:46.199991Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-20T01:37:31.309603Z'
  stage: doing
  run: 1d901092d1ce49e081837fd6397f1b80
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-20T01:37:51.807075Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-20T01:38:14.394750Z'
  stage: review
  run: 292b8bc234d8468ebeb884430258792c
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-20T01:38:34.749096Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-10-20T01:38:46.304212Z'
  stage: docs
  run: 94c47c56aa2143278a3858c2e6f54cfb
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-20T01:39:06.729105Z'
  stage: smoke-test
---

# The tests pin text at a section's edge in the sections, the journal and the story form

## Description

The mutation sweep of 2026-10-19 found the same gap in three readers of a work item's Markdown: every test leaves a blank line between a `## ` heading and the first text under it, and none puts a numbered line right above a heading. So a reader that started one line late (missing the first line under the heading) or one line early (taking the line above the heading for part of the section) would pass. The readers are `section_text` of `factory.domain.sections`, the journal's `entry_text` of `factory.domain.journal` and the story form's numbered items of `factory.domain.story_form` (the acceptance criteria and the journal entries `check_story_form` counts). The sweep also found that no test has an empty fenced block, whose closing fence stands on the line right after the opening one. The sweep's line numbers of these modules are today's. This story pins these edges as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003. The sweep's `_item_text` survivor is not pinned: on today's code it is equivalent (decision 3 of `feature.md`).

## Interface

No module under `src/factory/` changes. The behaviour pinned (`domain`):

- `factory.domain.sections.section_text(body, heading)`: the text under the heading starts on the line right after it, whether or not a blank line stands between.
- `factory.domain.sections.code_blocks(lines)`: a closing fence on the line right after the opening one closes the block there.
- `factory.domain.journal.entry_text(document, number)`: entry 1 is found on the line right after `## Journal`, and a numbered line right above `## Journal` is never an entry.
- `factory.domain.story_form.check_story_form(document, form, folder=...)`: a criterion or a journal entry on the line right after its heading counts, and a numbered line right above `## Acceptance criteria` or `## Journal` is never a criterion or an entry.

Tests (the tester writes them): `tests/domain/test_section_edges.py` (the `sections` and `journal` rows) and `tests/domain/test_story_form_edges.py` (the story form rows). Their bodies are written out as literal texts, since `_body` of `tests/domain/test_story_form.py` always puts a blank line under a heading. Documents with a state are built with `initial_state("intake")` of `factory.domain.work_item`, and a started story's state as `_state` of `tests/domain/test_story_form.py` builds it (`WorkItemState(stage="done", journal=[JournalRecord(number=1, speaker="factory", kind="result")])`). No earlier test changes.

In criterion 4, `CRITERIA` is `1. It works.\n2. make check stays green.\n3. docs: none.` and `SMOKE` is `` ```bash\nuv run factory\n```\nExpect: it works. ``, the form is the `FORM` of `tests/domain/test_story_form.py` (`# Story form\n\n## Description\n\n## Interface\n\n## Acceptance criteria\n\n## Smoke test\n\n## Journal\n`), and every body starts `# A story\n\n## Description\n\nText.\n\n## Interface\n\n`.

## Acceptance criteria

1. `section_text` at the heading's edge (rows of one parametrized test): `section_text("# T\n## A\nfirst\nsecond\n## B\n", "A")` is `"first\nsecond"`, and `section_text("# T\n\n## A\n\nfirst\nsecond\n\n## B\n", "A")` is `"first\nsecond"` as well.
2. An empty fenced block (rows of one parametrized test; `TICKS` is three backticks, as in `tests/domain/test_sections.py`): `code_blocks([TICKS, TICKS])` is `[CodeBlock(start=0, end=1)]`, and `code_blocks([TICKS, TICKS, "text", TICKS])` is `[CodeBlock(start=0, end=1), CodeBlock(start=3, end=None)]`.
3. The journal at its heading's edge (rows of one parametrized test, each a `WorkItemDocument(state=initial_state("intake"), body=<body>)`):
   - Body `# T\n\n## Journal\n1. 2026-10-12 human: created.\n2. intake: accepted.\n`: `entry_text(document, 1)` is `"created."` and `entry_text(document, 2)` is `"accepted."`.
   - Body `# T\n\n## Smoke test\n\n1. a numbered line\n## Journal\n\n1. 2026-10-12 human: created.\n`: `entry_text(document, 1)` is `"created."`, and `entry_text(document, 2)` raises `WorkItemFormatError` whose fault is `no journal entry 2`.
4. The story form at a section's edges (rows of one parametrized test; each row the body after the common start, the folder and the state):
   - `None.\n\n## Acceptance criteria\n` + `CRITERIA` + `\n\n## Smoke test\n\n` + `SMOKE` + `\n\n## Journal\n` (criterion 1 right under its heading), folder `backlog`, no state: `[]`.
   - `1. a numbered line\n## Acceptance criteria\n\n` + `CRITERIA` + `\n\n## Smoke test\n\n` + `SMOKE` + `\n\n## Journal\n` (a numbered line right above the criteria), folder `backlog`, no state: `[]`.
   - `None.\n\n## Acceptance criteria\n\n` + `CRITERIA` + `\n\n## Smoke test\n\n` + `SMOKE` + `\n1. a numbered line\n## Journal\n\n1. human: created.\n` (a numbered line right above the journal), folder `done`, the started state with one record: `[]`.
   - `None.\n\n## Acceptance criteria\n\n` + `CRITERIA` + `\n\n## Smoke test\n\n` + `SMOKE` + `\n\n## Journal\n1. human: created.\n` (entry 1 right under its heading), folder `done`, the started state with one record: `[]`; the same body in folder `backlog`, no state: exactly `[FormFinding(line=25, message="a backlog story carries no journal entries")]`.
5. `make check` stays green.
6. docs: none. `docs/project-guide/` already describes these readers and the story form check, and this story changes neither.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.domain.journal import entry_text
from factory.domain.sections import code_blocks, section_text
from factory.domain.work_item import WorkItemDocument, initial_state

print(repr(section_text("# T\n## A\nfirst\nsecond\n## B\n", "A")))
print(code_blocks(["```", "```"]))
body = "# T\n\n## Smoke test\n\n1. a numbered line\n## Journal\n1. 2026-10-12 human: created.\n"
print(entry_text(WorkItemDocument(state=initial_state("intake"), body=body), 1))
EOF
```

Expect: three lines, `'first\nsecond'`, `[CodeBlock(start=0, end=1)]` and `created.`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: it names concrete functions in `factory.domain.sections`, `journal` and `story_form` (`section_text`, `code_blocks`, `entry_text`, `check_story_form`). It also names the test modules, the literal bodies and the state builders. No signature changes, and each comment states one behaviour.
   - Criteria: each is testable by one parametrized test with literal inputs and outputs. Each behaviour in the Interface has a criterion: text on the line after a heading, the empty fenced block, entry 1 right under `## Journal`, and a numbered line above a heading. Each rule has its failing side: entry 2 raises `WorkItemFormatError` with `no journal entry 2`, a numbered line above a heading yields no criterion or entry, and the backlog row yields the `FormFinding`. I counted lines for the `FormFinding(line=25, ...)` row: the common start is 8 lines, the entry lands on line 25, and `line` is `start + 1`.
   - Smoke test: the heredoc is runnable with `uv run -q python`. The `Expect:` line names three outputs that can be compared exactly.
   - Architecture: nothing under `src/` changes. The tests sit in `tests/domain/`, mirroring `factory.domain`, and the story follows the standing leave and tests-only rules in `CLAUDE.md`. It changes no earlier test.
   - Scope: it matches S0002 in `feature.md`. The `_item_text` survivor is left out as equivalent (decision 3), and no out-of-scope item is touched.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 4 as parametrized tests, one per criterion, with the literal bodies from the Interface. I changed no earlier test.
   - criterion 1: tests/domain/test_section_edges.py::test_section_text_starts_on_the_line_right_after_the_heading
   - criterion 2: tests/domain/test_section_edges.py::test_an_empty_fenced_block_closes_on_the_line_after_its_opening
   - criterion 3: tests/domain/test_section_edges.py::test_the_journal_starts_right_after_its_heading_and_not_above_it
   - criterion 4: tests/domain/test_story_form_edges.py::test_items_count_from_the_line_right_after_their_heading_and_not_above_it
   - criterion 5 (`make check` green): the factory's check after the coder. It needs no test function.
   - criterion 6 (docs: none): needs no test.

   Files created: tests/domain/test_section_edges.py and tests/domain/test_story_form_edges.py.

   Modules the test run could not import: none. Unlike a usual tests stage, the new tests pass now (`make test`: green, coverage 99.14 %). That is expected, because the Description says the code already behaves this way and the coder has nothing to change. `make lint` is green.

   The started state is `WorkItemState(stage="done", journal=[JournalRecord(number=1, speaker="factory", kind="result")])`, as the Interface says. I copied `FORM`, `TICKS`, `CRITERIA` and `SMOKE` into the new modules as constants. I did not import them from the earlier test modules, because this story's `CRITERIA` ("3. docs: none.") differs from the one in test_story_form.py.

   Nothing is open.

   `lint`: lint: green (0.0 s)
   `test`: test: green (38.8 s)
6. factory: started doing as self.
7. coder: I built nothing, as the Description and Interface say ("No module under `src/factory/` changes"). The tester's new tests (`tests/domain/test_section_edges.py`, `tests/domain/test_story_form_edges.py`) already pass against today's `section_text`, `code_blocks`, `entry_text` and `check_story_form`. I ran `make check` and it is green: check: green, coverage 99.14 %.
      - Main choice: leave the source untouched. I rejected touching the readers in `factory.domain.sections`, `journal` or `story_form` to "harden" them, because that is beyond scope and the tests pin behaviour that already holds.
      - Refactor: nothing to refactor, because my diff against main holds no source change.
      - The journal did not change the meaning of the task, so I left the Description as it is.
      - Noticed, not touched: the tester copied `FORM` and `TICKS` from the earlier test modules (`tests/domain/test_story_form.py`, `tests/domain/test_sections.py`) as constants. Their entry gives the reason for `CRITERIA`, which differs. `FORM` and `TICKS`, though, are identical copies. Under CLAUDE.md's standing leave the tester could move them to one shared place, so the reviewer may want to judge that.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: Review, round 0. I read the work item and `git diff main...HEAD -- . ':!factory'`, which adds two test files and changes nothing under `src/`. Groups 1 to 3 pass. Each of criteria 1 to 4 is covered by one parametrized test whose rows match the literal inputs and outputs in the criteria. The rows would catch a reader that starts one line late or one line early, and both failing sides are tested: entry 2 raises `no journal entry 2`, and the backlog row gives `FormFinding(line=25, ...)`. The coder's journal entry 7 says the factory's `make check` was green, and nothing touches the architecture or security. Group 4 (quality) fails. Because this is round 0, copies inside a test file the diff adds are findings, not notes.

   1. `tests/domain/test_story_form_edges.py:10-13` and `:16`: `FORM` and `SMOKE` are character-for-character copies of `FORM` and `SMOKE` in `tests/domain/test_story_form.py:11-14` and `:20`. Fix: import them, e.g. `from domain.test_story_form import FORM, SMOKE`, as `tests/domain/test_contract_provider_limit.py:3` already imports from another test module. Only `CRITERIA` differs ("3. docs: none."), so the new module keeps its own `CRITERIA`, and no earlier test changes.
   2. `tests/domain/test_story_form_edges.py:17-19`: `STARTED` builds by hand the same state that the existing helper `_state` in `tests/domain/test_story_form.py:59` gives for `_state(1, "done")`. The Interface says to build the state the way `_state` does. Fix: import `_state` and set `STARTED = _state(1, "done")`.
   3. `tests/domain/test_section_edges.py:10`: `TICKS = "`" * 3` is a copy of `TICKS` in `tests/domain/test_sections.py:23`, which criterion 2 names as the source. Fix: `from domain.test_sections import TICKS`.

   What I rejected: moving these constants to a shared module under `tests/`. The standing leave would allow it, but the story says "No earlier test changes", and importing them needs no change to an earlier test. These findings are for the tester; the coder hands them on and touches no test (R9).

   Earlier tests: none changed. The diff only adds `tests/domain/test_section_edges.py` and `tests/domain/test_story_form_edges.py`, both with status `A`.
10. factory: started doing as self.
11. coder: Round 1: all three of the reviewer's findings in entry 9 are test changes. The source under `src/factory/` needs no change, so I changed nothing and am sending the work item back to the tester (R9). The tester should make these changes and no others:
       1. `tests/domain/test_story_form_edges.py`: remove the copied `FORM` and `SMOKE` and import them with `from domain.test_story_form import FORM, SMOKE`. Keep this module's own `CRITERIA`.
       2. `tests/domain/test_story_form_edges.py`: replace the hand-built `STARTED` with `_state(1, "done")`, imported from `domain.test_story_form`.
       3. `tests/domain/test_section_edges.py`: remove the copied `TICKS` and import it with `from domain.test_sections import TICKS`.
       - No earlier test module changes. The reviewer rejected moving these into a shared module, and I agree, because importing them is enough.
       - What I built: nothing. No paths changed in this round.
       - Main choice: send the work back with `tests` and touch neither the code nor the tests. I rejected making the edits myself, because the coder never edits tests (R9).
       - Noticed, not touched: nothing new.
12. factory: started tests as self.
13. tester: Round 1, the test change approved in the coder's entry 11 (the reviewer's findings in entry 9). I made those three changes and nothing else:
       1. `tests/domain/test_story_form_edges.py`: I removed the copied `FORM` and `SMOKE` and now import them from `domain.test_story_form`. The module keeps its own `CRITERIA`.
       2. `tests/domain/test_story_form_edges.py`: `STARTED` is now `_state(1, "done")`, imported from `domain.test_story_form`. I dropped the import of `JournalRecord`, which nothing uses now.
       3. `tests/domain/test_section_edges.py`: I removed the copied `TICKS` and now import it from `domain.test_sections`.

    No earlier test module changed, and no test was renamed or now checks something different. The criterion → test mapping is the same as in entry 5:
       - criterion 1: tests/domain/test_section_edges.py::test_section_text_starts_on_the_line_right_after_the_heading
       - criterion 2: tests/domain/test_section_edges.py::test_an_empty_fenced_block_closes_on_the_line_after_its_opening
       - criterion 3: tests/domain/test_section_edges.py::test_the_journal_starts_right_after_its_heading_and_not_above_it
       - criterion 4: tests/domain/test_story_form_edges.py::test_items_count_from_the_line_right_after_their_heading_and_not_above_it
       - criteria 5 and 6: these need no test function.

    Files changed: tests/domain/test_section_edges.py and tests/domain/test_story_form_edges.py. I created no new files. Modules the test run could not import: none.

    `make lint` is green. `make test` is green with 99.14 % coverage; the tests pass now because the code already behaves this way. Nothing is open.

    `lint`: lint: green (0.0 s)
    `test`: test: green (38.4 s)
14. factory: started doing as self.
15. coder: Round 1, after the tester's changes in entry 13. Those changes cover all three of the reviewer's findings from entry 9: `FORM`, `SMOKE` and `_state` are now imported from `domain.test_story_form`, and `TICKS` from `domain.test_sections`.
       - What I built: nothing. No path under `src/factory/` changes, as the Interface says. The tests in `tests/domain/test_section_edges.py` and `tests/domain/test_story_form_edges.py` pass against today's `section_text`, `code_blocks`, `entry_text` and `check_story_form`. I ran `make check` myself and it ends with `check: green` (coverage 99.14 %).
       - Main choice: I handed the work item back to review with the code untouched. I rejected changing the readers, because the story pins behaviour the code already has, and any change there would go beyond the story's scope.
       - Refactor: there was nothing to refactor. My diff against main holds no source change.
       - The journal did not change the meaning of the task, so I left the Description as it is.
       - Noticed, not touched: nothing new.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
16. factory: started review as self.
17. reviewer: Review, round 1. I read the work item and `git diff main...HEAD -- . ':!factory'`. The diff adds two test files, `tests/domain/test_section_edges.py` and `tests/domain/test_story_form_edges.py`, and changes nothing under `src/`.

    no findings

    - **Group 1, the criteria:** each of criteria 1 to 4 has one parametrized test, and the rows use the criteria's literal inputs and outputs.
      - Criterion 1 has rows with and without blank lines.
      - Criterion 2 has two rows: the empty block alone, and the empty block followed by an open block.
      - Criterion 3 has two rows: entry 1 right under `## Journal`, and a numbered line right above it. The second row also tests the failing side: `entry_text(document, 2)` raises `WorkItemFormatError` with the fault `no journal entry 2`.
      - Criterion 4 has five rows. They include the backlog row, which gives exactly `FormFinding(line=25, ...)`.
      - These rows would fail a reader that starts one line late or one line early. Entry 15 records the factory's `make check` as green after the coder.
    - **Groups 2 and 3:** nothing under `src/` changes, so no architecture or security point arises. No marker silences a check.
    - **Group 4, quality:** the three findings from round 0 (entry 9) are fixed. `FORM`, `SMOKE` and `_state` are now imported from `domain.test_story_form`, and `TICKS` from `domain.test_sections`. That is the same import pattern as `tests/domain/test_contract_provider_limit.py:3`. The imports bring in no test functions, so pytest collects nothing twice. The module's own `CRITERIA` differs from the earlier one ("3. docs: none."), so keeping it is not a copy.
    - **Group 5, hygiene:** the Description and Interface match what was built (tests only, no source change). The journal records the main choice and what was rejected. The docs criterion ("docs: none") still holds, because no reader's behaviour changes.

    Earlier tests: none changed. Both files in the diff are new (status `A`).
18. factory: started docs as self.
19. documenter: Docs round 1. I changed no files. The docs criterion is `none`, and the diff holds only the two new test files, `tests/domain/test_section_edges.py` and `tests/domain/test_story_form_edges.py`. No file under `src/` changed. I did not run `make check`, because I changed no file.

    Cross-read and found current: `docs/decisions.md` (the entries on `code_blocks`, `section_text` and `entry_text`, and on the form check counting entries outside code blocks) and `docs/project-guide/costs.md` (the `entry_text` allow list). Neither mentions the line-after-heading edge cases these tests pin. Their descriptions of the readers are still true, because the tests pin behaviour the code already had.

    Stale text I noticed: none.

    No findings for the coder.

    `check`: check: green (not run again: passed on tree c419906f7254 at 2026-10-20T01:36:44Z)
    `secrets`: secrets: green (0.2 s)
    `documents`: documents ok
20. factory: started smoke-test as self.
