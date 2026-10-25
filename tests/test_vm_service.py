"""The machine's systemd template unit for the factory."""

import configparser

import pytest

from vm_support import SERVICE


class _CaseKeeping(configparser.ConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr


def _unit() -> configparser.ConfigParser:
    parser = _CaseKeeping(strict=False, interpolation=None)
    parser.read_string(SERVICE.read_text(encoding="utf-8"))
    return parser


@pytest.mark.parametrize(
    ("section", "expected"),
    [
        pytest.param(
            "Unit",
            [("After", "network-online.target zfs.target"), ("Wants", "network-online.target")],
            id="unit",
        ),
        pytest.param(
            "Service",
            [
                ("User", "factory"),
                ("Group", "factory"),
                ("WorkingDirectory", "/srv/factory/%i"),
                ("EnvironmentFile", "/srv/factory/%i/factory.env"),
                ("ExecStart", "/srv/factory/%i/factory/.venv/bin/factory-run"),
                ("Restart", "always"),
                ("RestartSec", "15"),
            ],
            id="service",
        ),
        pytest.param("Install", [("WantedBy", "multi-user.target")], id="install"),
    ],
)
def test_each_section_holds_exactly_its_keys(section: str, expected: list[tuple[str, str]]) -> None:
    items = list(_unit()[section].items())

    if section == "Unit":
        description = dict(items).pop("Description", "")
        assert "%i" in description
        assert sorted(key for key, _ in items) == ["After", "Description", "Wants"]
        items = [item for item in items if item[0] != "Description"]
    assert items == expected


def test_the_unit_has_three_sections_and_no_environment_pre_start_or_type() -> None:
    assert _unit().sections() == ["Unit", "Service", "Install"]
    text = SERVICE.read_text(encoding="utf-8")
    assert [key for key in ("Environment=", "ExecStartPre=", "Type=") if key in text] == []
