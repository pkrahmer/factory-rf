---
stage: review
blocked: null
round: 1
attempts: 1
crashes: 0
pull_request: 586
comments_read: [6675609802, 6675672524]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-06T07:16:50.900299Z'
  lease_duration: 60
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
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T03:00:57.953996Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-06T03:03:29.701779Z'
  stage: tests
  run: e925fd185fac4606b8cb728fa76e0aed
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T03:03:34.833748Z'
  stage: doing
- number: 13
  speaker: factory
  kind: crash
  at: '2026-11-06T03:15:21.530305Z'
  stage: doing
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-06T03:15:23.586691Z'
  stage: doing
- number: 15
  speaker: factory
  kind: stall
  at: '2026-11-06T03:19:16.912274Z'
  stage: doing
  run: 42cb92791ae745458b940a175da86565
  reason: died
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-06T07:03:55.173901Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-06T07:08:40.255775Z'
  stage: doing
  run: 3cf70e9220c74a60b2c1f9ec6ab3d036
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-06T07:08:48.139654Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-06T07:10:43.968304Z'
  stage: review
  run: ebef2ac1db4c487da7aa1e4b163b75c8
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-06T07:10:49.293339Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-06T07:11:10.877092Z'
  stage: doing
  run: 9864e686a3bf4043b4819f858d1d28d4
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-06T07:11:16.170784Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-11-06T07:12:33.913041Z'
  stage: tests
  run: d117d9e4ddfa4a3cb726bc79c9b5949b
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-06T07:12:39.267319Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-11-06T07:16:45.426079Z'
  stage: doing
  run: 65cdd356331a4916a4146afef5e983cb
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-06T07:16:50.900299Z'
  stage: review
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
6. A guide with no settings table (no table whose first column is `Name` or `Variable`) gives no settings finding, also when the code reads settings.
7. `make check` stays green.
8. docs: `docs/project-guide/shared.md`: `SETTINGS` and the settings check. `docs/operator-guide/install.md`: none yet (the rewrite adds the file to the checked files).

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
10. factory: started tests as vm.
11. tester: Wrote the tests from the Interface and criteria, with the human's answer in entry 9: `GuideTable.heading`, a separate `refusal_findings(guide_tables, settings_source)`, `guide_tables(text, section)` with a test of its own, and criterion 5 run on a copy in `tmp_path`.

    Criteria to test functions:
    - criterion 1: tests/shared/domain/test_settings_table.py::test_settings_table_names_what_read_settings_reads (a recording `Mapping` notes every key `read_settings` looks up; the environment is `BASE` from `tests/support/settings_support.py` plus `FACTORY_IMAGE_ID_FILE`, with a file reader, so every read is reached; the names in `SETTINGS` must equal the noted keys, each name once)
    - criterion 2: tests/shared/domain/test_document_settings.py::test_name_and_default_mismatches_are_findings (rows: omitted by the guide, not read by the code, default differs, a default where the code has none, default equal, `None` as an empty cell, `None` as `none`, no `Default` column so no default finding)
    - criterion 3: tests/shared/domain/test_document_settings.py::test_table_with_another_first_column_is_ignored (rows: `Name` and `Variable` are counted, `Setting` is ignored)
    - criterion 4: tests/shared/domain/test_document_settings.py::test_refusal_texts_are_checked_against_the_settings_source (rows: held, not held, placeholder with its pieces held, placeholder with a piece not held, a two-character piece not checked, a three-character piece checked, a `Refusal` table under another heading, a table under `The refusals` with another first column); the parser rule from entry 9: tests/shared/domain/test_document_settings.py::test_guide_tables_keep_their_nearest_heading
    - criterion 5: tests/entry/test_check_documents_settings.py::test_settings_findings_are_printed_without_changing_the_exit_status (on the copy, with the `FACTORY_ZFS` row present no printed line names it; with the row dropped one does, and the exit status is unchanged)

    Test data: settings rows build `GuideTable` directly with raw cells, so names are backticked as in the guide (`` `FACTORY_A` ``) and default cells are plain (`5`, empty, `none`). A refusal is the backticked text of the first cell. A finding must be one string that contains the setting's name or the refusal text.

    Not tested: criterion 1's "with their defaults". The Interface defines the table test as a comparison of names, and nothing pins how a default is written as text, so the test checks names and that each appears once. The Description still predates entry 9 (`heading`, `refusal_findings`, `guide_tables`); I left it unchanged and the tests follow entry 9.

    Files created: tests/shared/domain/test_settings_table.py, tests/shared/domain/test_document_settings.py, tests/entry/test_check_documents_settings.py.
    Earlier test files changed under the standing leave to move a shared helper: the `documents` fixture moved from tests/entry/test_check_documents_operator_guide.py to tests/conftest.py, with the same name and body. The earlier test module lost its local copy and the now-unused `shutil` import and `ROOT`; its tests keep their names and checks.

    One run, `uv run pytest -q` on the files above plus the changed one: collection was interrupted by 2 errors, in test_settings_table.py and test_document_settings.py, because `factory.shared.domain.documents` has no `GuideTable` (and `factory.shared.domain.settings` has no `SETTINGS`/`SettingDoc` yet). The interruption meant the entry test and the changed operator-guide test did not run. The entry test imports only existing code, so it will fail on its assertion until the check exists. `make lint`: green.

    Modules the runner could not import: the names `GuideTable`, `guide_tables`, `settings_findings`, `refusal_findings` from `factory.shared.domain.documents`, and `SETTINGS`, `SettingDoc` from `factory.shared.domain.settings`.

    `lint`: lint: green (0.2 s)
12. factory: started doing as vm.
13. factory: crash 1: the run of stage doing ended without a result. Its work is discarded back to commit df6343e7ddca4349c3708f34958ec6be5a0308fe.
14. factory: started doing as vm.
15. factory: Stage doing stalled (attempt 1 of 2): the agent run died without a result
16. factory: started doing as vm.
17. coder: The code was already in the commit the factory made when the earlier doing run stalled (5247baea2). I checked it against the tests and the Interface, refactored it once, and `make check` is green (`check: green`, coverage 99.21 %).

    What is built:
    - `src/factory/shared/domain/settings.py`:
      - `SettingDoc` is a frozen model with `name`, `required` and `default: str | None`.
      - `SETTINGS` has one row for each of the 36 variables `read_settings` reads, `FACTORY_DATASET` and `FACTORY_STAGE_IMAGE` included.
      - Defaults come from the module's own constants (paths, `DEFAULT_GIT_IDENTITY`, the first entry of each choice tuple, minutes from the timedeltas), not from copied literals. So the table cannot drift from the code that applies the defaults.
    - `src/factory/shared/domain/documents.py`:
      - `GuideTable` (`heading`, `header`, `rows`).
      - `guide_tables(text, section)` finds the tables of a section, each with its nearest heading.
      - `settings_findings` compares names, and compares a default only in a table that has a `Default` column.
      - `refusal_findings(guide_tables, settings_source)` cuts out the placeholders and checks each piece of three characters or more against the source.
      - The existing `_table_rows` now shares `_is_table_row` and the block handling with the new parser, so there is no second copy.
    - `src/factory/entry/check_documents.py`: reads the *Configuration* section of `docs/operator-guide/install.md`. It prints the settings and refusal findings after the name findings, prefixed with the guide's path, and leaves the exit status unchanged.

    Main choice: the checks are pure functions in the domain layer, and the command passes them the source text of the settings module (`Path(settings.__file__)`). I rejected having `refusal_findings` read the module itself, because that would make the domain impure.

    Refactor this round, with behaviour unchanged:
    - `guide_tables` had its own `_section_range`, which duplicated the existing `_section_lines`. It now uses `_section_lines` and `_section_range` is gone.
    - `refusal_findings` used an assignment expression inside a comprehension. That became a small helper, `_quoted_refusal`.

    The journal changed nothing in the meaning of the task beyond what the Description already says. Entry 9 added `GuideTable.heading`, `refusal_findings` and `guide_tables`, and the Description does not name them. I am not allowed to edit the work item, so it is unchanged.

    Noticed, not touched:
    - Today's guide gives no settings findings: every name agrees, and there is no `Default` column and no refusal table. So `make documents` on the repository prints no settings line. Criterion 5 is tested on a copy in `tmp_path` with one row dropped, as entry 9 agreed.
    - `make documents` reports name findings in the project guide, for example `docs/project-guide/README.md:111: support/settings_support.py does not exist`. A few of these are older, but `settings_support.py` may be the docs stage's to fix.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 40 known, 3 gone
18. factory: started review as vm.
19. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (src/factory/shared/domain/settings.py, src/factory/shared/domain/documents.py, src/factory/entry/check_documents.py and the four test files) against the work item and the human's answers in entries 4 and 9. The coder's `make check` was green (entry 17). I read `make duplicates`: its 5 new findings are all in modules this diff does not touch (claude_runtime/opencode_runtime, hand_over/acceptance, cost_records).

    Findings:
    1. tests/shared/domain/test_settings_table.py: criterion 1 asks for `SETTINGS` "with their defaults", but nothing tests the defaults (the tester says so in entry 11). Only the names are compared. Any `SettingDoc.default` in src/factory/shared/domain/settings.py:126-179 could be wrong and the suite would stay green, for example the literal `"0"` for `FACTORY_IDLE_SHUTDOWN_MINUTES`, or `_SNAPSHOTS[0]`. Fix: the tester adds one parametrized test with a row per setting, pinning its `default` (`FACTORY_STATE` -> `/state`, `FACTORY_MIN_FREE_GB` -> `5`, `FACTORY_IDLE_SHUTDOWN_MINUTES` -> `0`, a setting with no default -> `None`, and so on) against the value `read_settings` applies when the variable is unset. If the human does not want that test, the coder asks (R8) to drop "with their defaults" from criterion 1.
    2. criterion 6 added: it needs its test. src/factory/shared/domain/documents.py, `settings_findings`, `if not tables: return []`: when the guide has no settings table, it gives no finding, not even the "missing from the guide" findings that criterion 2 describes. No criterion named this. It keeps the earlier entry tests green (tests/entry/test_check_documents.py `clean_texts`, whose install.md has no settings table, expects `documents ok`). I wrote it as criterion 6, before the two closing ones, now 7 and 8. Fix: the coder hands it to the tester for one row. Two cases are needed: a table with another first column and a non-empty `settings` gives no finding, and a `Variable` table with one row names every other setting. Be aware: under this rule a guide whose settings table loses its `Variable`/`Name` header passes silently. Raise that with S0004's gate if it matters.

    Open, not a finding: the `## Interface` still predates entry 9. It does not name `GuideTable.heading`, `guide_tables(text, section)` or `refusal_findings(guide_tables, settings_source)`, and it still says refusals are checked by `settings_findings`. The code and tests follow entry 9. The Description's sentences are still true of what was built, so there is no description correction. I may correct only the Description, and the coder may not write the work item, so the Interface can be brought up to date only by the human or an intake rerun.

    Rejected: `_RecordingEnviron` is not a copy (no other recording Mapping exists under tests/ or src/). The refusal and table tests are parametrized rows as the rules ask. `guide_tables` reuses `_section_lines`, and `_table_rows` now shares `_is_table_row`, so there is no second copy of the table reading.

    Earlier tests:
    - tests/conftest.py: the standing leave to move a shared test helper (the `documents` fixture moved here with the same name and body).
    - tests/entry/test_check_documents_operator_guide.py: the standing leave to move a shared test helper (its local `documents` fixture, `ROOT` and the `shutil` import removed; its tests keep their names and checks).
20. factory: started doing as vm.
21. coder: Round 1. I changed no code: both of the reviewer's findings in entry 19 need only tests, and the code already does what each one asks.

    1. Criterion 1, "with their defaults": the tester adds one parametrized test to tests/shared/domain/test_settings_table.py. It has a row per setting and pins each `SettingDoc.default` against the value `read_settings` applies when that variable is unset. A setting with no default gets `None`. Examples: `FACTORY_STATE` -> `/state`, `FACTORY_MIN_FREE_GB` -> `5`, `FACTORY_IDLE_SHUTDOWN_MINUTES` -> `0`.
    2. Criterion 6, added by the reviewer: the tester adds its test to tests/shared/domain/test_document_settings.py, as rows of one test:
       - A guide whose only table has another first column, given a non-empty `settings`, gives no finding.
       - A `Variable` table with one row gives a finding for every other setting.

       `settings_findings` in src/factory/shared/domain/documents.py already returns `[]` when no table counts, so both rows should pass against the code as it is.

    Rejected: asking the human to drop "with their defaults" from criterion 1. The criterion is clear and the test can be written, so I saw no reason to narrow it.

    Description: I made no rewrite, because the coder's write paths do not include the work item. Entry 9 added `GuideTable.heading`, `guide_tables(text, section)` and `refusal_findings(guide_tables, settings_source)`. The `## Interface` still predates that answer and still has `settings_findings` checking refusals. The code and tests follow entry 9. Bringing the Interface up to date is left to the human or an intake rerun.

    Noticed, not touched: under criterion 6, a settings table that loses its `Variable`/`Name` header passes silently. The reviewer suggested raising this with S0004's gate.

    I did not run `make check` this round, since nothing I could change has changed.
22. factory: started tests as vm.
23. tester: Mode: a test change the human approved. I made the two test additions that coder entry 21 names, which come from the reviewer's findings in entry 19. I changed no existing test.

    - criterion 1, the "with their defaults" part: tests/shared/domain/test_settings_table.py::test_settings_table_holds_the_default_read_settings_applies. It is one parametrized test with a row for each of the 36 settings. Each row pins the expected `SettingDoc.default` as a literal, for example `FACTORY_STATE` -> `/state`, `FACTORY_MIN_FREE_GB` -> `5`, `FACTORY_IDLE_SHUTDOWN_MINUTES` -> `0`, `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` -> `10`, and `None` for a setting with no default. For every setting that has a default, the row also checks that `read_settings(BASE)` applies that same value when the variable is unset. Durations are compared as whole minutes.
    - criterion 6: tests/shared/domain/test_document_settings.py::test_guide_without_a_settings_table_gives_no_settings_finding. It has two rows:
      - a guide whose only table has another first column (`Setting`), with three settings in the code, gives no finding;
      - a `Variable` table with one row gives one finding for each of the other two settings.

    The criterion-1 name test stays as it was (`test_settings_table_names_what_read_settings_reads`).

    Files changed: tests/shared/domain/test_settings_table.py and tests/shared/domain/test_document_settings.py. No files were created.

    One run of `uv run pytest -q` on the two files: all passed. The code already exists, so these tests are not red, as entry 21 expected. Every module imported. `make lint`: green.

    I skipped the type check as the stage says. A `mypy --strict` run on just these two files outside the project's configuration failed with `import-untyped` on `factory.shared.domain.settings`. That comes from the stand-alone setup, not from the tests, so the coder's `make check` is the real type check.

    `lint`: lint: green (0.2 s)
24. factory: started doing as vm.
25. coder: Round 1. The two tests from the reviewer's findings in entry 19 are in place (tester entry 23). They pass against the existing code, so I changed no code this round.
    - tests/shared/domain/test_settings_table.py::test_settings_table_holds_the_default_read_settings_applies covers criterion 1, "with their defaults".
    - tests/shared/domain/test_document_settings.py::test_guide_without_a_settings_table_gives_no_settings_finding covers criterion 6.

    What is built is unchanged from entry 17:
    - src/factory/shared/domain/settings.py: `SettingDoc` and `SETTINGS`.
    - src/factory/shared/domain/documents.py: `GuideTable`, `guide_tables`, `settings_findings` and `refusal_findings`.
    - src/factory/entry/check_documents.py: prints the settings and refusal findings and leaves the exit status unchanged.

    Main choice, unchanged: the checks are pure domain functions, and the command passes them the source text of the settings module. I rejected having `refusal_findings` read the module itself, because that would make the domain impure.

    Refactor: nothing to change. The diff did not change this round, and entry 17 already refactored it.

    `make check`: green (`check: green`, coverage 99.21 %).

    Description: not rewritten, because my write paths do not include the work item. The `## Interface` still predates the human's answer in entry 9. It does not name `GuideTable.heading`, `guide_tables(text, section)` or `refusal_findings(guide_tables, settings_source)`, and it still has refusals checked by `settings_findings`. The code and tests follow entry 9.

    Noticed, not touched:
    - Under criterion 6, a settings table that loses its `Variable`/`Name` header passes silently. The reviewer suggested raising this with S0004's gate.
    - `make documents` reports older name findings in the project guide (for example `docs/project-guide/README.md:111: support/settings_support.py does not exist`).

    `check`: check: green
    `duplicates`: duplicates: 5 new, 40 known, 3 gone
26. factory: started review as vm.
