"""The opencode runtime's rules allow the runtime folders it is given in the agent's home."""

import pytest

from adapters.opencode_stand_in import (
    MODELS,
    REPLY,
    write_opencode,
)
from confine_support import ConfineCall, Layout, read_records, run_request, write_confine
from factory.adapters.opencode_runtime import RUNTIME_FOLDERS, OpencodeRuntime
from factory.domain.confinement import Confinement

OPENCODE_THREE = [".local/share/opencode", ".local/state/opencode", ".cache/opencode"]


@pytest.mark.parametrize(
    ("runtime_folders", "expected"),
    [
        pytest.param(
            (*RUNTIME_FOLDERS, ".config/sso-opencode"),
            [*OPENCODE_THREE, ".config/sso-opencode"],
            id="with-sso-folder",
        ),
        pytest.param(None, OPENCODE_THREE, id="default"),
    ],
)
def test_the_rules_allow_each_runtime_folder_in_the_home_in_order(
    layout: Layout, runtime_folders: tuple[str, ...] | None, expected: list[str]
) -> None:
    confine = write_confine(layout)
    executable = write_opencode(layout.stand_in, [REPLY])
    layout.state.mkdir(exist_ok=True)
    runtime = (
        OpencodeRuntime(
            str(executable),
            layout.state,
            models=MODELS,
            confine_executable=str(confine),
            temporary_root=layout.temporary_root,
        )
        if runtime_folders is None
        else OpencodeRuntime(
            str(executable),
            layout.state,
            models=MODELS,
            confine_executable=str(confine),
            temporary_root=layout.temporary_root,
            runtime_folders=runtime_folders,
        )
    )

    runtime.run(run_request(layout))

    [confined] = read_records(layout.confine_bin / "confine-calls.jsonl", ConfineCall)
    rules = Confinement.model_validate_json(confined.rules_text)
    home = layout.home
    in_home = [folder for folder in rules.folders if folder.is_relative_to(home)]
    assert in_home == [home / folder for folder in expected]
    checkout_index = max(
        index
        for index, folder in enumerate(rules.folders)
        if folder.is_relative_to(layout.checkout)
    )
    assert rules.folders.index(home / expected[0]) > checkout_index
