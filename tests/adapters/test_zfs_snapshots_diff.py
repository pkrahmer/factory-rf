"""The ZFS adapter's reading of `zfs diff -FH` into changed paths, and its faults."""

from pathlib import Path

import pytest

from factory.domain.errors import SnapshotError
from factory.domain.git import ChangedPath
from zfs_support import DATASET, Answer, snapshots_on, write_zfs

DIFF = ["diff", "-FH", f"{DATASET}@base"]
WORK = "/srv/factory/vm/work"

DIFF_LINES = [
    f"M\t/\t{WORK}/checkout",
    f"+\t/\t{WORK}/checkout/newdir",
    f"M\tF\t{WORK}/checkout/src/a.py",
    f"+\tF\t{WORK}/checkout/new.txt",
    f"-\tF\t{WORK}/home/.claude.json",
    f"R\tF\t{WORK}/checkout/old.md\t{WORK}/checkout/renamed.md",
    f"-\tF\t{WORK}/checkout/renamed.md",
    f"+\t@\t{WORK}/checkout/link",
    f"+\tF\t{WORK}/checkout/with\\040space.txt",
    f"+\tF\t{WORK}/checkout/caf\\303\\251.txt",
    f"+\tF\t{WORK}/checkout/back\\134slash.txt",
    f"M\tF\t{WORK}/home/.cache/uv/w\t(+1)",
]


@pytest.mark.parametrize(
    ("stdout", "expected"),
    [
        pytest.param(
            "".join(f"{line}\n" for line in DIFF_LINES),
            [
                ChangedPath(path="checkout/back\\slash.txt", change="added"),
                ChangedPath(path="checkout/café.txt", change="added"),
                ChangedPath(path="checkout/link", change="added"),
                ChangedPath(path="checkout/new.txt", change="added"),
                ChangedPath(path="checkout/old.md", change="deleted"),
                ChangedPath(path="checkout/renamed.md", change="added"),
                ChangedPath(path="checkout/src/a.py", change="modified"),
                ChangedPath(path="checkout/with space.txt", change="added"),
                ChangedPath(path="home/.cache/uv/w", change="modified"),
                ChangedPath(path="home/.claude.json", change="deleted"),
            ],
            id="lines",
        ),
        pytest.param(
            f"M\t/\t{WORK}\nM\tF\t{WORK}/checkout/a.py\n",
            [ChangedPath(path="checkout/a.py", change="modified")],
            id="mount-point",
        ),
        pytest.param(
            f"M\tF\t{WORK}/checkout/a.py\n\n  \n",
            [ChangedPath(path="checkout/a.py", change="modified")],
            id="blank-lines",
        ),
        pytest.param(
            f"-\tF\t{WORK}/checkout/x.txt\n+\tF\t{WORK}/checkout/x.txt\n",
            [ChangedPath(path="checkout/x.txt", change="added")],
            id="removed-then-added",
        ),
        pytest.param("", [], id="empty"),
    ],
)
def test_changed_paths_reads_the_diff_relative_to_the_mount_point(
    tmp_path: Path, stdout: str, expected: list[ChangedPath]
) -> None:
    zfs = write_zfs(tmp_path, {"diff": Answer(stdout=stdout)})

    assert snapshots_on(zfs).changed_paths() == expected
    assert zfs.arguments() == [DIFF]


@pytest.mark.parametrize(
    ("answer", "detail"),
    [
        pytest.param(
            Answer(stdout="M\tF\t/elsewhere/a.py\n"),
            f"/elsewhere/a.py is outside {WORK}",
            id="outside",
        ),
        pytest.param(
            Answer(stdout=f"M\tF\t{WORK}x/a\n"), f"{WORK}x/a is outside {WORK}", id="sibling"
        ),
        pytest.param(
            Answer(stdout=f"X\tF\t{WORK}/a\n"),
            f"cannot read the line X\tF\t{WORK}/a",
            id="unknown-change",
        ),
        pytest.param(Answer(stdout="M\tF\n"), "cannot read the line M\tF", id="short"),
        pytest.param(
            Answer(stdout=f"R\tF\t{WORK}/a\n"),
            f"cannot read the line R\tF\t{WORK}/a",
            id="short-rename",
        ),
        pytest.param(
            Answer(stdout=f"R\tF\t{WORK}/a\t/elsewhere/b\n"),
            f"/elsewhere/b is outside {WORK}",
            id="rename-outside",
        ),
        pytest.param(
            Answer(stdout=f"+\tF\t{WORK}/bad\\377\n"),
            f"cannot read the line +\tF\t{WORK}/bad\\377",
            id="not-utf-8",
        ),
        pytest.param(
            Answer(stderr=f"cannot open '{DATASET}@base': dataset does not exist\n", exit_status=1),
            f"cannot open '{DATASET}@base': dataset does not exist",
            id="fails",
        ),
    ],
)
def test_a_diff_it_cannot_read_is_a_fault(tmp_path: Path, answer: Answer, detail: str) -> None:
    zfs = write_zfs(tmp_path, {"diff": answer})

    with pytest.raises(SnapshotError) as raised:
        snapshots_on(zfs).changed_paths()

    assert raised.value.command == zfs.command(*DIFF)
    assert raised.value.detail == detail
