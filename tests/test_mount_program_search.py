"""No file under `src/` names podman's overlay mount program."""

import pytest

from source_search import SRC

SOURCE_ROOT = SRC.parent


@pytest.mark.parametrize("name", ["fuse-overlayfs", "mount_program"])
def test_no_source_file_names_the_overlay_mount_program(name: str) -> None:
    naming = [
        str(path.relative_to(SOURCE_ROOT))
        for path in sorted(SOURCE_ROOT.rglob("*"))
        if path.is_file()
        and "__pycache__" not in path.parts
        and name in path.read_text(encoding="utf-8", errors="replace")
    ]

    assert naming == []
