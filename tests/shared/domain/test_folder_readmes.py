"""What a folder's README and its subfolders disagree on, and the README's own form."""

from collections.abc import Sequence

import pytest

from factory.shared.domain.folder_readmes import readme_problems

FOLDER = "operator"
TITLE = "# The operator folder"
OPENING = "What the operator runs on the machine. Each folder holds one kind of file."
LINK = "The operator guide says more: [the operator guide](../docs/operator-guide/README.md)."
LINK_LINE = "- [The machine](../docs/operator-guide/machine.md) says how the machine is set up."


def _subfolder_line(name: str, sentence: str = "holds files of the operator.") -> str:
    return f"- `{name}/` {sentence}"


def _readme(
    *,
    title: str = TITLE,
    opening: Sequence[str] = (OPENING,),
    links: Sequence[str] = (LINK,),
    subfolders: Sequence[str] = ("bin", "lib"),
    extra: Sequence[str] = (),
) -> str:
    lines = [
        title,
        "",
        *opening,
        "",
        *links,
        "",
        *(_subfolder_line(name) for name in subfolders),
        *extra,
    ]
    return "\n".join(lines) + "\n"


def _words(count: int) -> str:
    return " ".join(["word"] * (count - 1) + ["end."])


@pytest.mark.parametrize(
    ("readme", "subfolders", "expected"),
    [
        pytest.param(None, ["bin"], [f"{FOLDER}: no README.md"], id="no-readme"),
        pytest.param(_readme(), ["bin", "lib"], [], id="every-subfolder-named"),
        pytest.param(
            _readme(subfolders=("bin",)),
            ["bin", "lib"],
            [f"{FOLDER}: lib/ is not named"],
            id="subfolder-not-named",
        ),
        pytest.param(
            _readme(subfolders=("bin", "lib")),
            ["bin"],
            [f"{FOLDER}: lib/ does not exist"],
            id="named-subfolder-missing",
        ),
        pytest.param(
            _readme(subfolders=("a", "b")),
            ["a", "c"],
            [f"{FOLDER}: b/ does not exist", f"{FOLDER}: c/ is not named"],
            id="both-sorted",
        ),
        pytest.param(
            _readme(subfolders=("bin",), extra=("- `x/`",)),
            ["bin", "x"],
            [f"{FOLDER}: x/ is not named"],
            id="line-without-a-sentence",
        ),
    ],
)
def test_a_readme_and_its_subfolders_give_what_they_disagree_on(
    readme: str | None, subfolders: list[str], expected: list[str]
) -> None:
    assert readme_problems(FOLDER, readme, subfolders) == expected


def _at_line_limit(extra_links: int) -> str:
    # Ten lines plus one per subfolder: the title, the opening, eight link lines and two
    # subfolder lines make twelve, with two subfolders.
    links = [LINK_LINE] * (8 + extra_links)
    return _readme(links=links)


FREE_PROSE = "This line says more than the form allows."


@pytest.mark.parametrize(
    ("readme", "problem", "count"),
    [
        pytest.param(
            _readme(extra=("", "## More")),
            f"{FOLDER}: has a section",
            1,
            id="section",
        ),
        pytest.param(
            _readme(extra=("", "```", "factory status", "```")),
            f"{FOLDER}: has a code block",
            1,
            id="code-block",
        ),
        pytest.param(
            _readme(opening=("One sentence. Two sentences.",)),
            f"{FOLDER}: the opening is longer than two sentences",
            0,
            id="opening-of-two-sentences",
        ),
        pytest.param(
            _readme(opening=("One sentence. Two sentences. Three sentences.",)),
            f"{FOLDER}: the opening is longer than two sentences",
            1,
            id="opening-of-three-sentences",
        ),
        pytest.param(
            _readme(links=()),
            f"{FOLDER}: links to no guide",
            1,
            id="no-relative-link",
        ),
        pytest.param(
            _readme(subfolders=("bin",), extra=(_subfolder_line("lib", _words(25)),)),
            f"{FOLDER}: lib/ has a long line",
            0,
            id="subfolder-line-of-25-words",
        ),
        pytest.param(
            _readme(subfolders=("bin",), extra=(_subfolder_line("lib", _words(26)),)),
            f"{FOLDER}: lib/ has a long line",
            1,
            id="subfolder-line-of-26-words",
        ),
        pytest.param(
            _readme(subfolders=("bin",), extra=(_subfolder_line("lib", "Holds. Runs."),)),
            f"{FOLDER}: lib/ has a long line",
            1,
            id="subfolder-line-of-two-sentences",
        ),
        pytest.param(
            _readme(extra=("", FREE_PROSE)),
            f"{FOLDER}: line 10 is no part of the form",
            1,
            id="free-prose-after-the-list",
        ),
        pytest.param(
            _at_line_limit(0),
            f"{FOLDER}: is longer than 12 lines",
            0,
            id="at-the-line-limit",
        ),
        pytest.param(
            _at_line_limit(1),
            f"{FOLDER}: is longer than 12 lines",
            1,
            id="one-line-past-the-line-limit",
        ),
        pytest.param(
            _readme(title="## A"),
            f"{FOLDER}: has a section",
            1,
            id="first-line-a-heading-other-than-the-title",
        ),
        pytest.param(
            _readme(title="What the folder holds."),
            f"{FOLDER}: line 1 is no part of the form",
            1,
            id="first-line-of-prose",
        ),
        pytest.param(
            _readme(extra=("", "~~~", "factory status", "~~~")),
            f"{FOLDER}: has a code block",
            1,
            id="tilde-fence",
        ),
        pytest.param(
            _readme(extra=("", "   ```", "   factory status", "   ```")),
            f"{FOLDER}: has a code block",
            1,
            id="fence-indented-by-spaces",
        ),
        pytest.param(
            _readme(links=("The guide is on the web: [the guide](https://example.org/guide).",)),
            f"{FOLDER}: links to no guide",
            1,
            id="only-link-a-web-address",
        ),
        pytest.param(
            _readme(links=("The guide is in [the guide](/docs/operator-guide/README.md).",)),
            f"{FOLDER}: links to no guide",
            1,
            id="only-link-root-absolute",
        ),
    ],
)
def test_a_readme_out_of_its_form_gives_one_line_per_rule(
    readme: str, problem: str, count: int
) -> None:
    problems = readme_problems(FOLDER, readme, ["bin", "lib"])

    assert problems.count(problem) == count, problems
