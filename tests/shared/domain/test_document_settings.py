"""The guide's settings tables and refusals are compared with the settings code."""

from pathlib import Path

import pytest

from factory.shared.domain import settings as settings_module
from factory.shared.domain.documents import (
    OPERATOR_INSTALL,
    SETTINGS_SECTION,
    GuideTable,
    guide_tables,
    refusal_findings,
    settings_findings,
)
from factory.shared.domain.settings import SETTINGS, SettingDoc
from support.operator_support import ROOT

_VARIABLE_HEADER = ("Variable", "Required", "Meaning")
_DEFAULT_HEADER = ("Name", "Required", "Default")
_REFUSALS = "The refusals"
_NO_SETTINGS_TABLE = "no settings table (first column Name or Variable) in Configuration"
_SOURCE = (
    'raise SettingsInvalid(variable, "is neither zfs nor copy")\n'
    'return f"holds {name}, which the factory sets itself"\n'
)


def _setting(name: str, default: str | None = None) -> SettingDoc:
    return SettingDoc(name=name, required="no", default=default)


def _table(header: tuple[str, ...], *rows: tuple[str, ...]) -> GuideTable:
    return GuideTable(heading="Configuration", header=header, rows=rows)


_SETTING_TABLE = _table(("Setting", "Meaning"), ("`FACTORY_A`", "A."))


@pytest.mark.parametrize(
    ("table", "settings", "named"),
    [
        pytest.param(
            _table(_VARIABLE_HEADER, ("`FACTORY_A`", "no", "A.")),
            (_setting("FACTORY_A"), _setting("FACTORY_B")),
            "FACTORY_B",
            id="omitted-by-the-guide",
        ),
        pytest.param(
            _table(_VARIABLE_HEADER, ("`FACTORY_A`", "no", "A."), ("`FACTORY_C`", "no", "C.")),
            (_setting("FACTORY_A"),),
            "FACTORY_C",
            id="not-read-by-the-code",
        ),
        pytest.param(
            _table(_DEFAULT_HEADER, ("`FACTORY_A`", "no", "5")),
            (_setting("FACTORY_A", "6"),),
            "FACTORY_A",
            id="default-differs",
        ),
        pytest.param(
            _table(_DEFAULT_HEADER, ("`FACTORY_A`", "no", "5")),
            (_setting("FACTORY_A"),),
            "FACTORY_A",
            id="default-where-the-code-has-none",
        ),
        pytest.param(
            _table(_DEFAULT_HEADER, ("`FACTORY_A`", "no", "5")),
            (_setting("FACTORY_A", "5"),),
            None,
            id="default-equal",
        ),
        pytest.param(
            _table(_DEFAULT_HEADER, ("`FACTORY_A`", "no", "")),
            (_setting("FACTORY_A"),),
            None,
            id="no-default-as-an-empty-cell",
        ),
        pytest.param(
            _table(_DEFAULT_HEADER, ("`FACTORY_A`", "no", "none")),
            (_setting("FACTORY_A"),),
            None,
            id="no-default-as-none",
        ),
        pytest.param(
            _table(_VARIABLE_HEADER, ("`FACTORY_A`", "no", "Default 5.")),
            (_setting("FACTORY_A", "6"),),
            None,
            id="no-default-column",
        ),
    ],
)
def test_name_and_default_mismatches_are_findings(
    table: GuideTable, settings: tuple[SettingDoc, ...], named: str | None
) -> None:
    findings = settings_findings([table], settings)

    if named is None:
        assert findings == []
    else:
        assert len(findings) == 1
        assert named in findings[0]


@pytest.mark.parametrize(
    ("first_column", "counted"),
    [
        pytest.param("Name", True, id="name"),
        pytest.param("Variable", True, id="variable"),
        pytest.param("Setting", False, id="another"),
    ],
)
def test_table_with_another_first_column_is_ignored(first_column: str, counted: bool) -> None:
    table = _table((first_column, "Meaning"), ("`FACTORY_C`", "C."))

    findings = settings_findings([table], ())

    assert len(findings) == (1 if counted else 0)


@pytest.mark.parametrize(
    ("table", "named"),
    [
        pytest.param(
            _SETTING_TABLE,
            (_NO_SETTINGS_TABLE,),
            id="no-settings-table",
        ),
        pytest.param(
            _table(_VARIABLE_HEADER, ("`FACTORY_A`", "no", "A.")),
            ("FACTORY_B", "FACTORY_C"),
            id="a-settings-table",
        ),
    ],
)
def test_guide_without_a_settings_table_gives_no_settings_finding(
    table: GuideTable, named: tuple[str, ...]
) -> None:
    settings = (_setting("FACTORY_A"), _setting("FACTORY_B"), _setting("FACTORY_C"))

    findings = settings_findings([table], settings)

    assert len(findings) == len(named)
    for name in named:
        assert any(name in finding for finding in findings)


@pytest.mark.parametrize(
    ("tables", "settings", "expected"),
    [
        pytest.param([], (_setting("FACTORY_A"),), [_NO_SETTINGS_TABLE], id="no-table-one-setting"),
        pytest.param(
            [],
            (_setting("FACTORY_A"), _setting("FACTORY_B")),
            [_NO_SETTINGS_TABLE],
            id="no-table-two-settings",
        ),
        pytest.param(
            [_SETTING_TABLE], (_setting("FACTORY_A"),), [_NO_SETTINGS_TABLE], id="setting-column"
        ),
        pytest.param([], (), [], id="no-table-no-settings"),
        pytest.param([_SETTING_TABLE], (), [], id="setting-column-no-settings"),
        pytest.param(
            [_SETTING_TABLE, _table(_VARIABLE_HEADER, ("`FACTORY_A`", "no", "A."))],
            (_setting("FACTORY_A"),),
            [],
            id="counting-table-beside-another",
        ),
    ],
)
def test_guide_without_a_counting_table_is_one_finding_when_there_are_settings(
    tables: list[GuideTable], settings: tuple[SettingDoc, ...], expected: list[str]
) -> None:
    assert settings_findings(tables, settings) == expected


def test_todays_install_guide_gives_no_settings_finding() -> None:
    text = (ROOT / OPERATOR_INSTALL).read_text(encoding="utf-8")

    findings = settings_findings(guide_tables(text, SETTINGS_SECTION), SETTINGS)

    assert findings == []


@pytest.mark.parametrize(
    ("heading", "first_column", "refusal", "found"),
    [
        pytest.param(_REFUSALS, "Refusal", "is neither zfs nor copy", False, id="held"),
        pytest.param(_REFUSALS, "Refusal", "is not a colour", True, id="not-held"),
        pytest.param(
            _REFUSALS,
            "Refusal",
            "holds <name>, which the factory sets itself",
            False,
            id="placeholder-pieces-held",
        ),
        pytest.param(
            _REFUSALS,
            "Refusal",
            "holds <name>, which nobody sets",
            True,
            id="placeholder-piece-not-held",
        ),
        pytest.param(_REFUSALS, "Refusal", "<a>qz<b>", False, id="piece-of-two-unchecked"),
        pytest.param(_REFUSALS, "Refusal", "<a>qzx<b>", True, id="piece-of-three-checked"),
        pytest.param("Configuration", "Refusal", "is not a colour", False, id="other-heading"),
        pytest.param(_REFUSALS, "Fault", "is not a colour", False, id="other-first-column"),
    ],
)
def test_refusal_texts_are_checked_against_the_settings_source(
    heading: str, first_column: str, refusal: str, found: bool
) -> None:
    table = GuideTable(
        heading=heading, header=(first_column, "Meaning"), rows=((f"`{refusal}`", "A fault."),)
    )

    findings = refusal_findings([table], _SOURCE)

    if found:
        assert len(findings) == 1
        assert refusal in findings[0]
    else:
        assert findings == []


def test_guide_tables_keep_their_nearest_heading() -> None:
    text = (
        "# Guide\n\n"
        "## Configuration\n\n"
        "| Variable | Meaning |\n"
        "|---|---|\n"
        "| `FACTORY_A` | A. |\n\n"
        "### The refusals\n\n"
        "| Refusal | Meaning |\n"
        "|---|---|\n"
        "| `is not a colour` | A fault. |\n\n"
        "## Elsewhere\n\n"
        "| Name | Meaning |\n"
        "|---|---|\n"
        "| `FACTORY_B` | B. |\n"
    )

    tables = guide_tables(text, "Configuration")

    assert [(table.heading, table.header[0]) for table in tables] == [
        ("Configuration", "Variable"),
        ("The refusals", "Refusal"),
    ]


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        pytest.param("`5`", [], id="backticked-equal"),
        pytest.param("5", [], id="plain-equal"),
        pytest.param(
            "`6`",
            ["setting FACTORY_A has the default '`6`' in the guide, '5' in the settings code"],
            id="backticked-differs",
        ),
    ],
)
def test_backticked_default_is_read_through_its_backticks(cell: str, expected: list[str]) -> None:
    table = _table(_DEFAULT_HEADER, ("`FACTORY_A`", "no", cell))

    assert settings_findings([table], (_setting("FACTORY_A", "5"),)) == expected


@pytest.mark.parametrize(
    ("refusal", "expected"),
    [
        pytest.param("<variable>: is not a colour", [], id="message-held"),
        pytest.param(
            "<variable>: is not a shade",
            ["refusal `<variable>: is not a shade` is not held by the settings code"],
            id="message-not-held",
        ),
        pytest.param("<a>: qz<b>", [], id="stripped-piece-of-two-unchecked"),
        pytest.param("<variable>: is not a colour: <value>", [], id="frame-at-both-ends"),
    ],
)
def test_refusal_pieces_are_checked_without_their_colons_and_spaces(
    refusal: str, expected: list[str]
) -> None:
    table = GuideTable(heading=_REFUSALS, header=("Refusal",), rows=((f"`{refusal}`",),))

    assert refusal_findings([table], "is not a colour") == expected


def test_real_settings_written_with_backticks_and_variable_give_no_finding() -> None:
    defaults = GuideTable(
        heading="Configuration",
        header=("Name", "Default"),
        rows=tuple(
            (f"`{setting.name}`", "none" if setting.default is None else f"`{setting.default}`")
            for setting in SETTINGS
        ),
    )
    refusals = GuideTable(
        heading=_REFUSALS,
        header=("Refusal",),
        rows=(("`<variable>: is not an absolute path`",),),
    )
    source = Path(settings_module.__file__).read_text(encoding="utf-8")

    assert settings_findings([defaults], SETTINGS) == []
    assert refusal_findings([refusals], source) == []
