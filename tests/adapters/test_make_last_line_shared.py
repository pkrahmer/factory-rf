"""The make adapter uses the domain's last-line rule and keeps no copy of its own."""

from factory.adapters import make_commands
from factory.domain import checks


def test_the_make_adapter_uses_the_domains_last_line_rule() -> None:
    assert vars(make_commands)["last_line"] is checks.last_line
    assert not hasattr(make_commands, "_last_line")
    assert not hasattr(make_commands, "_MAKE_MESSAGE_PREFIXES")
