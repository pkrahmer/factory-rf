---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 586
comments_read: [6675609802]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T02:53:34.315847Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T02:53:34.322800Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T02:54:00.207246Z'
  stage: intake
  run: 1f3e43bef03b46e48ac227b8fd9a22e0
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T02:57:51.287330Z'
  stage: intake
---

# The operator guide's settings agree with the settings code

## Description

The operator guide lists the instance's settings, their defaults and the messages that refuse a bad value. Those facts live in the settings code (`factory.shared.domain.settings`), and the guide's copy drifts. This story makes the code the one source: it gives the settings code a table of every setting it reads (name, whether it is required, its default), and the document check compares the guide's settings tables with it. Every setting the code reads appears in the guide with the same default; the guide names no setting the code does not read. The refusal messages the guide quotes must be texts the settings code holds. Until S0004 the findings are only printed.

## Interface

- `factory.shared.domain.settings`: `SETTINGS: tuple[SettingDoc, ...]`, one entry per variable `read_settings` reads: `name`, `required` (`yes`, `no`, or a condition such as `with zfs`), `default` (its text as the guide shows it, or `None`). A test keeps the table equal to what `read_settings` reads.
- `factory.shared.domain.documents`: `settings_findings(guide_tables, settings) -> list[str]`, pure, comparing the rows of the operator guide's settings tables (in `docs/operator-guide/install.md`, the section *Configuration*; a table whose first column is `Name` or `Variable`) with `SETTINGS`.
- Refusal texts: every backticked text in the guide's *Reference: the refusals* table (or today's equivalent) must occur in the settings module's source.
- Tests: `tests/shared/domain/test_settings_table.py`, `tests/shared/domain/test_document_settings.py`.

## Acceptance criteria

1. `SETTINGS` names exactly the variables `read_settings` and the boundaries read (one row per variable), with their defaults.
2. A setting the code reads and the guide omits, a setting the guide names and the code does not read, and a default that differs each give one finding, naming the setting (rows of one test).
3. A quoted refusal text the settings code does not hold gives one finding.
4. Today's guide gives findings that the command prints, without changing its exit status until S0004.
5. `make check` stays green.
6. docs: `docs/project-guide/shared.md`: `SETTINGS` and the settings check. `docs/operator-guide/install.md`: none yet (the rewrite adds the file to the checked files).

## Smoke test

```bash
uv run python -c "from factory.shared.domain.settings import SETTINGS; print(len(SETTINGS) > 30)"
```
Expect: `True`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: 1. Format check passed, so these are the checks it cannot make. The story cannot be built as written, for five reasons.
   1. **Default extraction (Interface, criterion 2).** The guide's settings tables (`docs/operator-guide/install.md`, *Configuration*) are `Variable | Required | Meaning`. There is no default column: defaults sit in free prose ("Default `/state`; unset or blank gives the default", "Default 5", "No default", "`poweroff` (unset, blank, the default)", "Unset … or `0` is off, the default"). `settings_findings` has no rule for reading a default out of the Meaning text, so the "default that differs" finding cannot be tested. Options: (a) the story adds a `Default` column to the guide's tables, which means editing install.md and conflicts with criterion 6 ("install.md: none yet"); (b) the rule is "the Meaning contains `Default <text>`"; (c) drop the default comparison. I would choose (a), with the column text compared exactly to `SettingDoc.default`.
   2. **`required` is not compared.** Guide values such as "yes, for `factory-run` and `factory-watch`", "no, but the preflight fails without it under Claude Code" and "with `zfs`" do not match the `SETTINGS` values (`yes`, `no`, or a condition). No criterion says whether `required` is compared, or how. Options: compare only the first word, or do not compare it. I would choose not to compare it, and to say so in the Interface.
   3. **Signature types.** `guide_tables` has no type (for example `list[SettingsTable]` with rows as `tuple[str, ...]`) and `SettingDoc` is not defined (a frozen Pydantic model? its fields). Name the concrete types, and say which module parses the markdown tables and where it lives.
   4. **Refusal texts (criterion 3).** The guide has no section *Reference: the refusals*, and the Interface says "or today's equivalent". In the table the refusals are scattered through the Meaning cells and the section "When the process refuses to start". Name the exact section or table and how backticked texts are picked out. Many backticked items are not refusal messages (`poweroff`, `Exit`, `2.5`). Say what "occur in the settings module's source" means for texts the code builds from a format string.
   5. **Scope of "SETTINGS".** Criterion 1 says `SETTINGS` names the variables "`read_settings` and the boundaries read". The Interface says only the variables `read_settings` reads. Variables read in the boundaries code (`FACTORY_DATASET` and `FACTORY_STAGE_IMAGE` are "refused when the boundaries are built") are not in `read_settings`. State which module's reads the keeping test compares with, and how the test finds them. It cannot compare to the source reliably without a rule.
   Also: criterion 4 should name the command (`factory.entry.check_documents` through `make documents`), and a criterion is missing for the failing side of the table-selection rule (a table whose first column is neither `Name` nor `Variable` is ignored).
4. 2026-11-06 human: 1. Neither (a) nor (b): `settings_findings` compares a default only in a table that has a `Default` column, exactly against `SettingDoc.default` (`None` against an empty cell or `none`). Today's tables have no such column, so on today's guide only the names are compared. The rewrite of `install.md` in the next feature brings the style page's table (name, what it does, default, example), and then the defaults are checked. `install.md` stays unchanged here, as criterion 6 says. Criterion 2's row for a differing default uses a table with a `Default` column; add a row showing that a table without one gives no default finding.
   2. Not compared. `SettingDoc` keeps `required` for the guide's writer; the Interface says it is not compared.
   3. `SettingDoc` is a frozen Pydantic model in `factory.shared.domain.settings` with `name: str`, `required: str` and `default: str | None`. `guide_tables` is `list[GuideTable]`, a frozen model in `factory.shared.domain.documents` with `header: tuple[str, ...]` and `rows: tuple[tuple[str, ...], ...]`, parsed there from the Markdown by a pure function that extends the table reading the document check already has (`_table_rows`), not a second copy. A table counts when its first column is `Name` or `Variable`; a table with another first column is ignored (one row, as you say).
   4. Refusal texts are checked only in a table under a heading `The refusals` whose first column is `Refusal`; today's guide has none, so nothing is checked yet, and the rewrite adds it. A refusal's text is the backticked text of that first column. Its parts between placeholders in angle brackets (`<value>`) are cut out, and each remaining piece of three characters or more must occur in the source of `factory.shared.domain.settings`. That handles texts built from a format string. Rows: a held text (none), a text not held (one finding), a text with a placeholder whose pieces are held (none).
   5. Only `read_settings`: every variable it reads, `FACTORY_DATASET` and `FACTORY_STAGE_IMAGE` included (both are read there). The keeping test calls `read_settings` with a recording mapping that notes every key looked up, on an environment valid enough to reach every read, and compares the noted keys with the names in `SETTINGS`. Criterion 1 reads "the variables `read_settings` reads".
   Also yes: criterion 4 names `factory.entry.check_documents` through `make documents`.
