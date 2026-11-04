"""The transcript folder on the factory's own disk, or on a bucket mounted as one."""

import hashlib
import os
from pathlib import Path

from factory.application.transcripts import TranscriptStore

_OWNER_ONLY = 0o600
_OWNER_ONLY_FOLDER = 0o700


class FileTranscriptStore(TranscriptStore):
    """Writes transcripts as files under one folder, each readable by its owner alone."""

    def __init__(self, folder: Path) -> None:
        """Write under `folder`, created with its subfolders when missing."""
        self._folder = folder

    def write(self, path: str, data: bytes) -> str:
        """Write `data` to `path` under the folder with mode `0600` and return its SHA-256."""
        target = self._folder / path
        target.parent.mkdir(mode=_OWNER_ONLY_FOLDER, parents=True, exist_ok=True)
        # Opened owner-only from the start, so the text is never readable by others, not even
        # for a moment; `chmod` sets the mode of a file an earlier copy already made.
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, _OWNER_ONLY)
        with os.fdopen(descriptor, "wb") as file:
            file.write(data)
        target.chmod(_OWNER_ONLY)
        return hashlib.sha256(data).hexdigest()
