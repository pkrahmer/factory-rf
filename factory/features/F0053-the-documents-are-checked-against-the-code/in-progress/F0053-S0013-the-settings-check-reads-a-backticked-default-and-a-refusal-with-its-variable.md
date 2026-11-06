---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 599
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-06T13:32:34.897807Z'
  lease_duration: 60
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
4. `make check` stays green.
5. docs: `docs/project-guide/style.md`, *The operator guide*: the reader learns that a default may be written in backticks, and that a refusal is written as the message `<variable>: <fault>` with the variable as a placeholder. `docs/project-guide/shared.md`, *The settings check*: the reader learns the same two rules as the check applies them.

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
