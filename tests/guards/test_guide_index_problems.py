"""A guide folder's index names every page of the folder, and every page it names exists."""

from pathlib import Path

import pytest

from support.guide_files_support import index_problems

PAGE = "# A page\n\nWhat the page covers.\n\n## A heading\n\nText.\n"


def _index(*lines: str, other: str = "") -> str:
    return (
        "# The guide\n\nWhat the guide is.\n\n## The files\n\n"
        + "".join(f"{line}\n" for line in lines)
        + "\n## Other\n\n"
        + other
    )


@pytest.mark.parametrize(
    ("files", "required", "expected"),
    [
        pytest.param(
            {
                "README.md": _index("- `README.md`: this index.", "- `page.md` covers a page."),
                "page.md": PAGE,
            },
            (),
            [],
            id="every-page-named",
        ),
        pytest.param(
            {"README.md": _index("- `page.md` covers a page."), "page.md": PAGE, "extra.md": PAGE},
            (),
            ["not in the index: extra.md"],
            id="page-not-named",
        ),
        pytest.param(
            {
                "README.md": _index("- `page.md` covers a page.", "- `gone.md` covers a page."),
                "page.md": PAGE,
            },
            (),
            ["missing: gone.md"],
            id="named-page-missing",
        ),
        pytest.param(
            {
                "README.md": _index("- `page.md` covers a page.", "- `shared.md` covers it."),
                "page.md": PAGE,
                "shared.md": PAGE,
            },
            ("shared.md",),
            [],
            id="required-present",
        ),
        pytest.param(
            {"README.md": _index("- `page.md` covers a page."), "page.md": PAGE},
            ("shared.md",),
            ["missing: shared.md"],
            id="required-missing",
        ),
        pytest.param(
            {"README.md": _index("- `page.md`"), "page.md": PAGE},
            (),
            ["not in the index: page.md"],
            id="line-without-sentence",
        ),
        pytest.param(
            {
                "README.md": _index("- `page.md` covers a page."),
                "page.md": PAGE.replace("## A heading", "## A renamed heading"),
            },
            (),
            [],
            id="heading-renamed",
        ),
        pytest.param(
            {"README.md": _index("- `page.md`: A sentence."), "page.md": PAGE},
            (),
            [],
            id="colon-after-name",
        ),
        pytest.param(
            {"README.md": _index("- `a.md` covers a page."), "z.md": PAGE},
            (),
            ["missing: a.md", "not in the index: z.md"],
            id="two-problems-sorted",
        ),
        pytest.param(
            {"README.md": _index("- `shared.md` covers it.")},
            ("shared.md",),
            ["missing: shared.md"],
            id="named-and-required-missing-once",
        ),
        pytest.param(
            {"README.md": _index(), "notes.txt": "Notes.\n"},
            (),
            [],
            id="index-and-non-markdown-ignored",
        ),
        pytest.param(
            {"README.md": _index(other="- `other.md` covers a page.\n"), "other.md": PAGE},
            (),
            ["not in the index: other.md"],
            id="named-outside-the-files",
        ),
    ],
)
def test_index_problems_name_what_index_and_folder_disagree_on(
    tmp_path: Path, files: dict[str, str], required: tuple[str, ...], expected: list[str]
) -> None:
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    assert index_problems(tmp_path, required) == expected
