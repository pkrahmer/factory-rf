"""The contract command: it writes the records' JSON Schemas into a folder."""

import sys
from collections.abc import Sequence
from pathlib import Path

import factory
from factory.domain.contract import CONTRACT, contract_schema, schema_file_name

CONTRACT_FOLDER = Path(factory.__file__).parent / "contract"

_USAGE = "usage: python -m factory.entry.contract [<folder>]"
_OK = 0
_USAGE_ERROR = 2


def write_contract(folder: Path) -> list[Path]:
    """Write every schema of `CONTRACT` into `folder`, creating it; return the paths in order."""
    folder.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for entry in CONTRACT:
        path = folder / schema_file_name(entry)
        path.write_text(contract_schema(entry), encoding="utf-8")
        paths.append(path)
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    """Write the schemas into the folder given, or `CONTRACT_FOLDER`; print one line; 0."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) > 1:
        print(_USAGE, file=sys.stderr)
        return _USAGE_ERROR
    folder = Path(arguments[0]) if arguments else CONTRACT_FOLDER
    paths = write_contract(folder)
    print(f"contract: {len(paths)} schemas written")
    return _OK


if __name__ == "__main__":
    raise SystemExit(main())
