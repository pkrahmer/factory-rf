"""The wiring gives every ZFS adapter the one cache drop command, run through `sudo`."""

import ast
from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.zfs_snapshots import DROP_CACHES_COMMAND
from factory.entry.wiring import boundaries_from_environment

SOURCE = Path(__file__).parent.parent.parent / "src" / "factory"
WIRING = SOURCE / "entry" / "wiring.py"


def _constructions(path: Path) -> list[ast.Call]:
    calls = [
        node
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Call)
    ]
    return [
        call
        for call in calls
        if (isinstance(call.func, ast.Name) and call.func.id == "ZfsSnapshots")
        or (isinstance(call.func, ast.Attribute) and call.func.attr == "ZfsSnapshots")
    ]


def _drop_caches_keyword(call: ast.Call) -> str | None:
    for keyword in call.keywords:
        if keyword.arg == "drop_caches":
            return ast.unparse(keyword.value)
    return None


def test_every_reset_of_the_wired_instance_drops_the_cache_through_sudo(
    sudo_stand_in: Path,
    hosted_environment: dict[str, str],
    hosting: FakeHostingService,
) -> None:
    record = sudo_stand_in

    _, boundaries = boundaries_from_environment(hosted_environment, hosting=hosting)
    built_calls = record.exists()
    boundaries.snapshots.reset()

    assert DROP_CACHES_COMMAND == ("sudo", "-n", "/usr/local/bin/factory-drop-caches")
    assert built_calls is False
    assert record.read_text(encoding="utf-8").splitlines() == [
        "-n /usr/local/bin/factory-drop-caches"
    ]
    constructed = {
        path.relative_to(SOURCE).as_posix(): [_drop_caches_keyword(call) for call in calls]
        for path in sorted(SOURCE.rglob("*.py"))
        if (calls := _constructions(path))
    }
    assert list(constructed) == [WIRING.relative_to(SOURCE).as_posix()]
    assert set(constructed[WIRING.relative_to(SOURCE).as_posix()]) == {"DROP_CACHES_COMMAND"}
