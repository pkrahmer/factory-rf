---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 586
comments_read: [6675609802, 6675672524]
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
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T02:57:53.733863Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T02:58:14.943540Z'
  stage: intake
  run: dd348d42c5184fb4b0820ad3257fa586
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T02:58:20.069603Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-06T02:59:06.021521Z'
  stage: tests
  run: c86e053805c24193a32f60118b22394b
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-06T03:00:55.495035Z'
  stage: tests
---

# The operator guide's settings agree with the settings code

## Description

The operator guide lists the instance's settings, their defaults and the messages that refuse a bad value. Those facts live in the settings code (`factory.shared.domain.settings`), and the guide's copy drifts. This story makes the code the one source: it gives the settings code a table of every setting it reads (name, whether it is required, its default), and the document check compares the guide's settings tables with it. Every setting the code reads appears in the guide with the same default; the guide names no setting the code does not read. The refusal messages the guide quotes must be texts the settings code holds. Until S0004 the findings are only printed.

## Interface

- `factory.shared.domain.settings`: `SettingDoc`, a frozen Pydantic model with `name: str`, `required: str` (`yes`, `no`, or a condition such as `with zfs`; kept for the guide's writer, never compared) and `default: str | None`. `SETTINGS: tuple[SettingDoc, ...]`, one entry per variable `read_settings` reads (`FACTORY_DATASET` and `FACTORY_STAGE_IMAGE` included). A test keeps the table equal to what `read_settings` reads: it calls `read_settings` with a recording mapping that notes every key looked up, on an environment valid enough to reach every read, and compares the noted keys with the names in `SETTINGS`.
- `factory.shared.domain.documents`: `GuideTable`, a frozen model with `header: tuple[str, ...]` and `rows: tuple[tuple[str, ...], ...]`, parsed from the Markdown by a pure function that extends the existing `_table_rows`, not a second copy. `settings_findings(guide_tables: list[GuideTable], settings: tuple[SettingDoc, ...]) -> list[str]`, pure, comparing the rows of the operator guide's settings tables (in `docs/operator-guide/install.md`, the section *Configuration*; a table counts when its first column is `Name` or `Variable`, any other table is ignored) with `SETTINGS`. Names are always compared. A default is compared only in a table that has a `Default` column, exactly against `SettingDoc.default` (`None` against an empty cell or `none`). Today's tables have no such column, so only names are compared.
- Refusal texts: checked only in a table under a heading `The refusals` whose first column is `Refusal`; a refusal's text is the backticked text of that first column. Its parts between placeholders in angle brackets (`<value>`) are cut out, and each remaining piece of three characters or more must occur in the source of `factory.shared.domain.settings`. Today's guide has none, so nothing is checked yet.
- Tests: `tests/shared/domain/test_settings_table.py`, `tests/shared/domain/test_document_settings.py`.

## Acceptance criteria

1. `SETTINGS` names exactly the variables `read_settings` reads (one row per variable), with their defaults.
2. A setting the code reads and the guide omits, a setting the guide names and the code does not read, and, in a table with a `Default` column, a default that differs each give one finding, naming the setting (rows of one test); a table without a `Default` column gives no default finding.
3. A table whose first column is neither `Name` nor `Variable` is ignored (no finding).
4. A quoted refusal text, in a table under `The refusals` with first column `Refusal`, gives no finding when it is held by the settings source, one finding when it is not, and none when it has a `<placeholder>` and its remaining pieces of three characters or more are held.
5. Today's guide gives findings that `factory.entry.check_documents` (through `make documents`) prints, without changing its exit status until S0004.
6. `make check` stays green.
7. docs: `docs/project-guide/shared.md`: `SETTINGS` and the settings check. `docs/operator-guide/install.md`: none yet (the rewrite adds the file to the checked files).

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
5. factory: started intake as vm.
6. intake: accepted, with the human's answer (journal entry 4) carried into the story. I rewrote the Interface and criteria to match it and added no requirement of my own.
   - Interface: `SettingDoc`, `GuideTable` and the `settings_findings` signature now have concrete types. `required` is not compared. A default is compared only in a table with a `Default` column. The keeping test uses a recording mapping on `read_settings`. The refusal rule is stated: a table under `The refusals` with first column `Refusal`, placeholders cut out, pieces of three characters or more checked against the settings source. The Interface changes only source and tests, so the route is `tests`.
   - Criteria: seven now, each testable by one parametrized test. They cover omitted, extra and differing names or defaults, no default finding without a `Default` column, an ignored table, the three refusal rows, and the printed findings without an exit-status change (criterion 5 names `factory.entry.check_documents` through `make documents`). `make check` and `docs:` are last. Criteria 1, 2, 3 and 4 are new or reworded from entry 4; I did not reword the rest.
   - Smoke test: the command is runnable and the `Expect: True` line is checkable.
   - Architecture: the models sit in the shared domain layer, the functions are pure, and nothing needs I/O.
   - Scope: the story is inside the feature's settings check and not in its Out of scope. `install.md` stays unchanged.
7. factory: started tests as vm.
8. tester: stopped before writing any test. I can't write the tests against the Interface as it stands without guessing at names and signatures, so I wrote no files and did not run `make test` or `make lint`.

   1. **How a refusal table is recognised and checked (criterion 4).** `GuideTable` has only `header` and `rows`. It does not record the heading it sits under, so `settings_findings(guide_tables, settings)` cannot tell whether a `Refusal` table is under `The refusals`. The signature also takes no settings source, so a pure function cannot check pieces against `factory.shared.domain.settings`. Options:
      (a) Add `heading: str` to `GuideTable` and a third parameter, `settings_source: str`, to `settings_findings`. The tests pass the source text, or a fake one.
      (b) A separate pure function, `refusal_findings(guide_tables: list[GuideTable], settings_source: str) -> list[str]`. The parser keeps only the tables under `The refusals`.
      (c) `settings_findings` reads the module source itself, which would make it impure.
      I would choose (a). Then criterion 4's rows construct `GuideTable(heading="The refusals", header=("Refusal", …), rows=…)` with a small fake source, and a table under another heading gives no finding.
   2. **The Markdown parser has no public name.** The Interface says `GuideTable` is "parsed from the Markdown by a pure function" but does not name it or its signature. No criterion tests the parser directly, but criterion 4's heading rule depends on it. I would name it `guide_tables(text: str, section: str) -> list[GuideTable]`: the tables inside the section `section` and its subsections, each with its nearest heading. It is fine to leave it untested beyond criterion 5 if you prefer.
   3. **The form of a finding (criteria 2, 4, 5).** The tests would check only that each finding is one string that contains the setting's name (or the refusal text). Criterion 5 would build a copy of the docs in `tmp_path` whose install.md drops one setting's row, run `factory.entry.check_documents.main(["--root", …])`, and check two things: a printed line names that setting, and the exit status is the same as with the row present. Tell me if criterion 5 should instead run on the repository's own guide. Today it may give no settings finding at all, so a test of "today's guide gives findings" could not be checked.

   Criteria 1 to 3 are clear. Once 1 and 2 are answered, they map to `tests/shared/domain/test_settings_table.py::test_settings_table_names_what_read_settings_reads` and `tests/shared/domain/test_document_settings.py::{test_name_and_default_mismatches_are_findings, test_table_with_another_first_column_is_ignored, test_refusal_texts_are_checked_against_the_settings_source}`, plus a `tests/entry/` test for criterion 5.
9. 2026-11-06 human: 1. (b), with the heading: `GuideTable` gets `heading: str`, the nearest heading above it, and `refusal_findings(guide_tables: list[GuideTable], settings_source: str) -> list[str]` is a separate pure function that checks the tables headed `The refusals` with first column `Refusal`. `settings_findings(guide_tables, settings)` keeps its signature and checks only the settings tables. The command passes the source text of `factory.shared.domain.settings`; the tests pass a small fake source. A `Refusal` table under another heading gives no finding (one row).
   2. Yes: `guide_tables(text: str, section: str) -> list[GuideTable]`, the tables inside `section` and its subsections, each with its nearest heading. Give it one test of its own: two tables under two headings come back with their headings.
   3. Yes, as you propose: a finding is one string containing the setting's name or the refusal text. Criterion 5 runs on a copy in `tmp_path` whose `install.md` drops one setting's row, and checks that a printed line names that setting and that the exit status is the same as with the row present.
