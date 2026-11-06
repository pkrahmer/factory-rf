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
