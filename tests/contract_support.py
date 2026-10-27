"""What the contract's tests share: the command's output, a row of `main`'s cases, schema checks."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from factory.domain.contract import CONTRACT_KEY, ContractEntry, contract_schema, schema_file_name
from source_search import SRC

SCHEMAS = SRC / "contract"

WRITTEN = "contract: 5 schemas written\n"
USAGE = "usage: python -m factory.entry.contract [<folder>]\n"


@dataclass(frozen=True)
class MainRow:
    """One case of the contract command: its arguments, where it writes, what it prints."""

    arguments: Callable[[Path], list[str]]
    written: Callable[[Path], Path] | None
    out: str
    err: str
    code: int


def committed_is_generated(entry: ContractEntry, version: str | None = None) -> Callable[[], None]:
    """A check that the committed schema of `entry` equals its generation, at `version` if given."""

    def check() -> None:
        text = (SCHEMAS / schema_file_name(entry)).read_text(encoding="utf-8")
        if version is not None:
            assert f'"{CONTRACT_KEY}": "{version}"' in text
        assert text == contract_schema(entry)

    return check


def schemas_naming(word: str) -> list[str]:
    """The names of the committed schemas whose text holds `word`, sorted."""
    return [
        path.name
        for path in sorted(SCHEMAS.glob("*.schema.json"))
        if word in path.read_text(encoding="utf-8")
    ]
