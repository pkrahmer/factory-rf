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
