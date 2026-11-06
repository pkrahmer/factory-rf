---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 599
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T13:31:30.924334Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T13:31:30.930836Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T13:31:47.849521Z'
  stage: intake
  run: bf3916bd899548a49f4b7b36986fd745
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T13:31:53.286415Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-06T13:32:29.269541Z'
  stage: tests
  run: cfe056b2d43a40eab45615a6d501df5b
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T13:32:34.897807Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-06T13:36:57.635408Z'
  stage: doing
  run: b849402869e6417392e8f82deae8b459
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T13:37:03.050583Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-06T13:37:58.349073Z'
  stage: review
  run: 477f09ff0035416285c34b61a1a9dcf1
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T13:38:04.245700Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-06T13:38:16.640911Z'
  stage: doing
  run: 805e4910b447447c923f305f149a0d12
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T13:38:21.925671Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-11-06T13:38:44.869028Z'
  stage: tests
  run: c7f4c2bd58514ae8af425f5fbbaa9876
---

# The settings check reads a backticked default and a refusal with its variable
## Description

The rewrite will write the operator guide's settings tables by `docs/project-guide/style.md`, and the settings check compares them with `SETTINGS`. Two of the shapes a writer naturally uses give false findings today. First, a name cell is read through its backticks (`` `GIT_USER_NAME` ``), but a `Default` cell is compared exactly as written. A default written as code, `` `factory` ``, as today's `docs/operator-guide/install.md` writes every default (`` Default `/work/checkout` ``), is reported as `setting GIT_USER_NAME has the default '`factory`' in the guide, 'factory' in the settings code`. A table naming every setting with its default in backticks gives 17 such findings, all false. Second, the style page asks for "the message in backticks, with a `<placeholder>` for what varies", and `install.md` says the message is `<variable>: <fault>`. But a refusal written that way, `` `<variable>: is not an absolute path` ``, is a finding, because the piece after the placeholder, `: is not an absolute path`, keeps its colon and occurs nowhere in the settings code. Only the bare fault text passes. The feature acceptance found both in its walk-through. This story reads a `Default` cell through its backticks, as the name cell is read, and strips the whitespace and colons around each piece of a refusal before it looks the piece up. Everything else of the settings check stays as built: which tables count, `none` and the empty cell as no default, the three-character rule, and the finding texts.

## Interface

- `factory.shared.domain.documents.settings_findings(guide_tables, settings)` (domain): in a table with a `Default` column, the cell compared with `SettingDoc.default` is the cell's first backticked text when it has one, and the whole cell otherwise, as for the name cell. An empty cell or `none` is no default, as today. A finding still quotes the cell as written.
- `factory.shared.domain.documents.refusal_findings(guide_tables, settings_source)` (domain): each piece between the `<placeholder>`s has its leading and trailing whitespace and `:` removed before it is checked. A piece shorter than three characters after that is not checked. A piece that is not in `settings_source` is still a finding, with today's text.
- Tests: rows in `tests/shared/domain/test_document_settings.py`. Every earlier row keeps its expected result; if one does not, that is a question, since no leave covers it.

## Acceptance criteria

1. In a table headed `Name | Required | Default` and a setting `FACTORY_A` with the default `5`, the cell `` `5` `` and the cell `5` give no finding, and the cell `` `6` `` gives the one finding ``setting FACTORY_A has the default '`6`' in the guide, '5' in the settings code`` (rows of one test).
2. In a table under `The refusals` with the first column `Refusal`, and a source that holds `is not a colour`, the refusal `` `<variable>: is not a colour` `` gives no finding, and `` `<variable>: is not a shade` `` gives the one finding ``refusal `<variable>: is not a shade` is not held by the settings code``. The refusal `` `<a>: qz<b>` `` gives no finding, since `qz` is shorter than three characters once its colon and space are removed (rows of one test).
3. With the real `SETTINGS` and the source of `factory.shared.domain.settings`, a `Name | Default` table naming every setting, with its default in backticks or `none`, gives no settings finding. A refusal table holding `` `<variable>: is not an absolute path` `` gives no refusal finding.
4. In the table and with the source of criterion 2, which holds `is not a colour` and no colon after it, the refusal `` `<variable>: is not a colour: <value>` `` gives no finding, since the piece between the placeholders loses its trailing colon and space as well as its leading ones (a row of criterion 2's test).
5. `make check` stays green.
6. docs: `docs/project-guide/style.md`, *The operator guide*: the reader learns that a default may be written in backticks, and that a refusal is written as the message `<variable>: <fault>` with the variable as a placeholder. `docs/project-guide/shared.md`, *The settings check*: the reader learns the same two rules as the check applies them.

## Smoke test

```bash
uv run python -c "
from pathlib import Path
from factory.shared.domain import settings
from factory.shared.domain.documents import GuideTable, refusal_findings, settings_findings
d = GuideTable(heading='Configuration', header=('Name', 'Default'), rows=tuple((f'\`{s.name}\`', 'none' if s.default is None else f'\`{s.default}\`') for s in settings.SETTINGS))
r = GuideTable(heading='The refusals', header=('Refusal',), rows=(('\`<variable>: is not an absolute path\`',),))
print(len(settings_findings([d], settings.SETTINGS)), refusal_findings([r], Path(settings.__file__).read_text()))
" 2>&1 | tail -1
```
Expect: `0 []`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete functions, `factory.shared.domain.documents.settings_findings(guide_tables, settings)` and `refusal_findings(guide_tables, settings_source)`, both in the domain layer, plus the test file `tests/shared/domain/test_document_settings.py`. The rules are stated: first backticked text or whole cell, `none` and empty as no default, strip whitespace and colons, the three-character rule, and a finding that still quotes the cell as written.
   - Criteria: each is testable by one parametrized test. 1 covers the backticked default, the plain default, and the failing side (`6`) with its exact finding text. 2 covers a stripped piece that is found, one that is missing with its exact text, and a piece shorter than three characters after stripping. 3 checks the real `SETTINGS` and the real source. 4 is `make check`. Behaviour kept "as today" (empty cell and `none` as no default) is an unchanged earlier row, and the Interface says every earlier row keeps its result.
   - Smoke test: runnable with `uv run python -c`, no pytest, so the `-q` rule does not apply. `Expect: 0 []` can be checked against the last output line.
   - Docs criterion: names what the reader must know in `style.md` (*The operator guide*) and `shared.md` (*The settings check*): a default may be in backticks, and a refusal is the message `<variable>: <fault>`. It dictates no sentences.
   - Architecture: the changes are in the shared domain's `documents` module, which is pure rules and data with no I/O, and the docs are in the guides. Both are where they belong.
   - Scope: this is the settings check of S0002, which the feature's scope covers. It does not touch the Out of scope items. Routed to `tests` because the Interface changes Python code.
4. factory: started tests as vm.
5. tester: I added three tests to `tests/shared/domain/test_document_settings.py`. Every earlier row is unchanged and still passes.

   - criterion 1: tests/shared/domain/test_document_settings.py::test_backticked_default_is_read_through_its_backticks (rows `backticked-equal`, `plain-equal`, `backticked-differs`; the differing row checks the full finding text)
   - criterion 2: tests/shared/domain/test_document_settings.py::test_refusal_pieces_are_checked_without_their_colons_and_spaces (rows `message-held`, `message-not-held`, `stripped-piece-of-two-unchecked`; the not-held row checks the full finding text)
   - criterion 3: tests/shared/domain/test_document_settings.py::test_real_settings_written_with_backticks_and_variable_give_no_finding (real `SETTINGS` in a `Name | Default` table, with backticked defaults or `none`; the refusal is checked against the text of `factory.shared.domain.settings`'s file)
   - criterion 4 (`make check`) and criterion 5 (docs) have no test of mine.

   Files: I created none and changed `tests/shared/domain/test_document_settings.py`, the file the Interface names. Modules the test runner could not import: none, because both functions already exist.

   One run of `uv run pytest -q` on that file failed four tests on wrong results, as expected: `backticked-equal`, `message-held`, `stripped-piece-of-two-unchecked` and the real-settings test. `plain-equal`, `backticked-differs` and `message-not-held` already pass with today's code. `make lint`: green.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: I made the tester's new rows in `tests/shared/domain/test_document_settings.py` pass by changing one file, `src/factory/shared/domain/documents.py`. Every earlier row passes unchanged. `make check` is green and the smoke test prints `0 []`.

   - **Defaults:** `_default_findings` now reads a `Default` cell through the existing `_backticked_or_plain` helper, the same one used for the name cell. It applies the `none`/empty rule to the text it read. A finding still quotes the cell as written.
   - **Refusals:** `_is_held` now strips whitespace and `:` from both ends of each piece between placeholders (new constant `_PIECE_EDGES`, with a why-comment) before the three-character rule and the lookup. The finding text is unchanged.
   - **Docstrings:** I updated the docstrings of `settings_findings` and `refusal_findings` to state the two rules.

   Main choice: I reused `_backticked_or_plain` for the default cell instead of writing a second backtick reader just for defaults. One side effect: a backticked `` `none` `` also counts as no default. I judged that consistent with the Interface ("as for the name cell").

   Rejected: stripping only the `": "` that comes right after a placeholder. The Interface asks for whitespace and colons at both ends of every piece, and the simpler strip does that.

   Refactor: I read my diff and found nothing to change.

   Description: no journal entry changed the meaning of the task, so I left it as written.

   Noticed, not touched: the docs criterion (`style.md`, `shared.md`) is the documenter's.

   `check`: check: green
   `duplicates`: duplicates: 6 new, 39 known, 4 gone
8. factory: started review as vm.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`, which changes `src/factory/shared/domain/documents.py` and `tests/shared/domain/test_document_settings.py`, against the work item.

   1. criterion 4 added: it needs its test. Location: `## Acceptance criteria` of the work item, and `tests/shared/domain/test_document_settings.py::test_refusal_pieces_are_checked_without_their_colons_and_spaces`. The problem: the Interface says each piece loses its leading and trailing whitespace and `:`, but every new row (`message-held`, `message-not-held`, `stripped-piece-of-two-unchecked`) only has the frame at the start of a piece. A `lstrip` in place of `strip` in `_is_held` (`src/factory/shared/domain/documents.py:305`) would pass every test. The fix: I added criterion 4, `<variable>: is not a colour: <value>` against the source `is not a colour` gives no finding. It is one more row of criterion 2's test. The closing criteria are renumbered to 5 (`make check`) and 6 (docs).

   Checked with nothing found:
   - **Group 1:**
     - Criterion 1 is pinned by `backticked-equal`, `plain-equal` and `backticked-differs`, which checks the full text and so the cell quoted as written.
     - Criterion 2 is pinned by the three refusal rows. The three-character limit is tested on both sides: `qz` is not checked after stripping, and the earlier row `piece-of-three-checked` is checked.
     - Criterion 3 is pinned by the real `SETTINGS` test. `_NOT_ABSOLUTE` at `settings.py:94` holds the text it looks for.
     - The empty cell and `none` keep their earlier rows, and every earlier row is unchanged.
     - The coder's `make check` was green (journal entry 7).
   - **Group 2:** the change stays in the shared domain layer, with no I/O.
   - **Group 3:** nothing relevant to security and no silencing markers.
   - **Group 4:**
     - `_default_findings` reuses `_backticked_or_plain` instead of copying it.
     - `_PIECE_EDGES` has a comment that says why.
     - Both docstrings now state the new rules.
     - The 6 new findings from `make duplicates` cannot come from this diff of two code lines.
   - **Group 5:**
     - The journal names the main choice (reusing the helper) and what was rejected (stripping only the `": "`).
     - The Description matches what was built.
     - The docs criterion still says what the reader must learn.

   Earlier tests:
   - `tests/shared/domain/test_document_settings.py`: none needed. The change only adds three tests and two imports, and every earlier test is as it was.
10. factory: started doing as vm.
11. coder: The reviewer added criterion 4, and only its test is missing: one more row in `tests/shared/domain/test_document_settings.py::test_refusal_pieces_are_checked_without_their_colons_and_spaces`. The row is the refusal `<variable>: is not a colour: <value>` against the source that holds `is not a colour`, and it expects no finding.

    I changed no code. `_is_held` in `src/factory/shared/domain/documents.py` already strips whitespace and `:` from both ends of each piece, so the new row should pass once the tester adds it. Description: the reviewer's entry added criterion 4 and renumbered the last two criteria to 5 and 6; nothing else about the task changed.
12. factory: started tests as vm.
13. tester: I added the one test row the reviewer's criterion 4 needs, as the coder's entry 11 asked. No other test changed.

    - criterion 4: tests/shared/domain/test_document_settings.py::test_refusal_pieces_are_checked_without_their_colons_and_spaces, new row `frame-at-both-ends`. It checks the refusal `<variable>: is not a colour: <value>` against the source `is not a colour` and expects no finding. The colon and space sit at both ends of the piece here, so the row would fail if `_is_held` stripped only the left end.
    - criteria 1 to 3 keep the tests named in entry 5. Criteria 5 (`make check`) and 6 (docs) have no test of mine.

    Files: I created none and changed `tests/shared/domain/test_document_settings.py`, a test this story wrote. Modules the test runner could not import: none.

    One run of `uv run pytest -q` on that file passed all 37 tests, the new row included. That fits, because the coder's code already strips both ends. `make lint`: green.

    `lint`: lint: green (0.1 s)
