"""The runtime builds its rules against the checkout root; a missing root file gives no target."""

import pytest

from adapters.claude_stand_in import Step, write_stand_in
from adapters.test_claude_runtime_os_user import REPLY
from confine_support import (
    ConfineCall,
    Layout,
    confined_runtime,
    read_records,
    run_request,
    write_confine,
)
from factory.domain.confinement import Confinement


@pytest.mark.parametrize(
    ("write_path", "folder", "file"),
    [
        pytest.param("NOTES.md", None, None, id="missing-root-file"),
        pytest.param("docs/new.md", "docs", None, id="missing-file-below-the-root"),
        pytest.param("README.md", None, "README.md", id="existing-root-file"),
    ],
)
def test_a_write_path_at_the_root_never_gives_the_checkout_as_a_folder(
    layout: Layout, *, write_path: str, folder: str | None, file: str | None
) -> None:
    (layout.checkout / "README.md").write_text("# Project\n", encoding="utf-8")
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout)

    confined_runtime(layout, claude, str(confine)).run(
        run_request(layout, write_paths=(write_path,))
    )

    [confined] = read_records(layout.confine_bin / "confine-calls.jsonl", ConfineCall)
    rules = Confinement.model_validate_json(confined.rules_text)
    checkout = layout.checkout
    assert checkout not in rules.folders
    assert checkout / "NOTES.md" not in rules.files
    if folder is not None:
        assert checkout / folder in rules.folders
    if file is not None:
        assert checkout / file in rules.files


@pytest.mark.parametrize("target", ["NOTES.md", "other.md"])
def test_through_the_wrapper_a_missing_root_write_path_allows_no_write_at_the_root(
    layout: Layout, *, target: str
) -> None:
    path = layout.checkout / target
    claude = write_stand_in(layout.stand_in, [Step(writes={str(path): "x\n"}, stdout=REPLY)])

    result = confined_runtime(layout, claude).run(run_request(layout, write_paths=("NOTES.md",)))

    assert result.end_reason == "died"
    assert not path.exists()
