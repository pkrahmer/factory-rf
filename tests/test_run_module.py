"""The instance's run module, read as source: how `python -m` enters it."""

import ast

from source_search import SRC


def test_the_run_module_ends_by_exiting_with_the_status_of_main() -> None:
    source = (SRC / "entry" / "run.py").read_text(encoding="utf-8")

    last = ast.parse(source).body[-1]

    assert ast.unparse(last) == "if __name__ == '__main__':\n    raise SystemExit(main())"
