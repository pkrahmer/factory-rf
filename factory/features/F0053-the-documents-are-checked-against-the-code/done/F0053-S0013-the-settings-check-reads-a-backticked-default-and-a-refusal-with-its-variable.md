---
stage: done
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 599
comments_read: []
handed_over: approval
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
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-06T13:38:50.324345Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-11-06T13:42:52.972178Z'
  stage: doing
  run: b9f58bb0ad084bef8ddd2680d55199a4
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-06T13:43:00.655268Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-11-06T13:43:32.794501Z'
  stage: review
  run: eebbd792a725438b905b1767f54189c5
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-06T13:43:38.338135Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-11-06T13:45:58.631262Z'
  stage: docs
  run: ba5b63f52cd2471286a55fcf71d4c667
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-06T13:46:04.288459Z'
  stage: smoke-test
- number: 21
  speaker: smoke-tester
  kind: result
  at: '2026-11-06T13:46:23.565101Z'
  stage: smoke-test
  run: 18863897ac5e4650abc37e1a661274f1
- number: 22
  speaker: factory
  kind: done
  at: '2026-11-06T13:48:15.811425Z'
  stage: approval
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
14. factory: started doing as vm.
15. coder: Round 1. I changed no code. The reviewer's finding was criterion 4. In entry 13 the tester added its row, `frame-at-both-ends`, to `tests/shared/domain/test_document_settings.py::test_refusal_pieces_are_checked_without_their_colons_and_spaces`. That row passes against `_is_held` in `src/factory/shared/domain/documents.py` as it stands, because `_is_held` already strips whitespace and `:` from both ends of each piece. `make check` is green.

    - **Main choice:** unchanged from entry 7. The `Default` cell is read through the existing `_backticked_or_plain` helper. I rejected writing a second backtick reader for it.
    - **Refactor:** the diff is the same as in round 0, and I found nothing to change.
    - **Description:** the reviewer's entry 9 added criterion 4 and renumbered the closing criteria to 5 and 6. The Description already shows that, and nothing else changed.
    - **Noticed, not touched:** the docs criterion (`style.md`, `shared.md`) is the documenter's.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
16. factory: started review as vm.
17. reviewer: Round 1. I reviewed `git diff main...HEAD -- . ':!factory'` against the work item. The diff changes `src/factory/shared/domain/documents.py` and `tests/shared/domain/test_document_settings.py`.

    no findings

    What I checked:
    - **Group 1, acceptance criteria:**
      - Criterion 1: `test_backticked_default_is_read_through_its_backticks` covers it with the rows `backticked-equal`, `plain-equal` and `backticked-differs`. The last row checks the full finding text, which quotes the cell as written (`{cell!r}` at `documents.py:251`).
      - Criteria 2 and 4: `test_refusal_pieces_are_checked_without_their_colons_and_spaces` covers both. The rows `message-held`, `message-not-held` (full text) and `stripped-piece-of-two-unchecked` are criterion 2. The row `frame-at-both-ends` is criterion 4 and would fail under a left-only strip.
      - Criterion 3: `test_real_settings_written_with_backticks_and_variable_give_no_finding` uses the real `SETTINGS` and the source file of `factory.shared.domain.settings`.
      - The three-character limit is tested on both sides: `qz` is shorter and not checked, and the earlier row `piece-of-three-checked` is checked.
      - The empty cell and `none` keep their earlier rows, and every earlier row is unchanged.
      - The coder's `make check` was green (entry 15), and the tester ran 37 tests on that file, all passing (entry 13).
    - **Group 2, architecture:** the change is pure rules in the shared domain layer, with no I/O and no new import.
    - **Group 3, security:** nothing relevant, and no markers that silence a check.
    - **Group 4, quality:**
      - The `Default` cell reuses `_backticked_or_plain` (`documents.py:247`) instead of copying it.
      - `_PIECE_EDGES` has a comment that says why.
      - The docstrings of `settings_findings` and `refusal_findings` state the new rules.
      - A two-line code change cannot account for the 6 new findings of `make duplicates`.
    - **Group 5, work item hygiene:**
      - The journal names the main choice (reusing the helper) and what was rejected (stripping only the `": "` after a placeholder).
      - The Description matches what was built.
      - The docs criterion (now 6) still says what the reader of `style.md` and `shared.md` must learn.
      - A backticked `` `none` `` also counts as no default, as the coder noted. That follows from the Interface, which reads the cell's backticked text and treats `none` as no default, so I did not add a criterion for it.

    Earlier tests:
    - `tests/shared/domain/test_document_settings.py`: no leave was needed. The change adds three tests and two imports (`Path`, `settings_module`), and every earlier test is as it was.
18. factory: started docs as vm.
19. documenter: I changed two documents to match the code in `src/factory/shared/domain/documents.py`, which I read first. No finding for the coder. `make documents` ends with `documents ok (0.6 s)`. I ran no other examples, because I wrote none. I did not run `make check`, since I changed only documents.

    Files changed:
    - `docs/project-guide/style.md`, *The operator guide*: a default may be written in backticks or as plain text, as the name cell is. A refusal is written as the message `<variable>: <fault>`, with the variable as a placeholder. The check removes the whitespace and colons around each piece between the placeholders before it looks the piece up.
    - `docs/project-guide/shared.md`, *The settings check*: the same two rules as the check applies them. A `Default` cell is read as its first backticked text, or the whole cell if it has none, and a finding quotes the cell as written. Each refusal piece loses the whitespace and colons at both ends, so `<variable>: <fault>` looks up the fault alone.

    Cross-read and found current: the rest of `shared.md` and `style.md`, in particular the `none`/empty rule and the three-character rule.

    Stale text I saw but did not touch, because it is unrelated to this story: the `make documents` report lists two lines of the form `<path> does not exist`. They are `docs/project-guide/machine.md:362` (`factory/stage.Containerfile`) and `docs/project-guide/work.md:13` (`factory/agents`). They are not findings, since `documents ok` still ends the run. They look like paths in another repository or a path outside the checkout.

    `docs/decisions.md`: unchanged. The story names no lasting reason and no rejected option for it.

    `check`: check: green
    `secrets`: secrets: green (0.5 s)
    `documents`: documents ok (0.6 s)
20. factory: started smoke-test as vm.
21. smoke-tester: Ran the one smoke-test command from the repository root exactly as written.

    Command 1: `uv run python -c "…settings_findings / refusal_findings…" 2>&1 | tail -1`

    ```
    0 []
    ```

    Met its `Expect:` line (`0 []`). A `Name | Default` table that names every setting in the real `SETTINGS`, with each default in backticks or `none`, gives 0 settings findings. A refusal table holding `` `<variable>: is not an absolute path` `` gives no refusal finding when checked against the source of `factory.shared.domain.settings`.

    I read the acceptance criteria again. The output agrees with criterion 3, which is the one the command targets, and contradicts none of the others. Criteria 1, 2 and 4 are table rows that the smoke test does not run. Criterion 5 (`make check`) is the factory's gate, and criterion 6 (docs) is a document criterion that the command does not read.

    Findings: none. I fixed nothing, and nothing is open.
22. factory: done (pull request merged); cost: 10 runs, 7.6 min, 48 turns, 176721 tokens in (789494 more from cache), 16598 out, $1.72
