"""The wiring gives the stages a transcript store on the folder the settings name, or none."""

from pathlib import Path

import pytest

from factory.entry.wiring import build_boundaries
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.shared.domain.settings import InstanceSettings
from factory.watching.adapters.transcript_files import FileTranscriptStore
from wiring_support import CREDENTIAL, with_dataset


@pytest.mark.parametrize("with_folder", [False, True], ids=["no-folder", "folder"])
def test_the_built_boundaries_hold_a_transcript_store_only_with_a_folder(
    tmp_path: Path, *, with_folder: bool
) -> None:
    root = tmp_path.resolve()
    folder = root / "transcripts" if with_folder else None
    settings = with_dataset(
        InstanceSettings(
            repository_url="/srv/project.git",
            instance="factory-1",
            checkout=root / "checkout",
            state_directory=root / "state",
            agent_home=root / "agents-home",
            transcript_dir=folder,
        ),
        tmp_path,
    )

    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    if folder is None:
        assert boundaries.transcripts is None
    else:
        assert isinstance(boundaries.transcripts, FileTranscriptStore)
