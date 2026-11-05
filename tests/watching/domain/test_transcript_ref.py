"""The cost record's reference to its transcript: a relative `.gz` path and the file's SHA-256."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.watching.domain.cost_records import TranscriptRef

RUN = "a" * 32
PATH = f"F0001-S0001/{RUN}.jsonl.gz"
SHA = "b" * 64


@pytest.mark.parametrize(
    ("path", "sha256", "accepted"),
    [
        pytest.param(PATH, SHA, True, id="well-formed"),
        pytest.param(PATH, "b" * 63, False, id="sha-63-digits"),
        pytest.param(PATH, "B" * 64, False, id="sha-upper-case"),
        pytest.param(PATH, "g" + "b" * 63, False, id="sha-non-hex"),
        pytest.param(f"/srv/transcripts/{PATH}", SHA, False, id="path-absolute"),
        pytest.param(f"F0001-S0001/../{RUN}.jsonl.gz", SHA, False, id="path-with-dots"),
        pytest.param(f"F0001-S0001/{RUN}.jsonl", SHA, False, id="path-not-gz"),
    ],
)
def test_a_transcript_ref_takes_only_a_relative_gz_path_and_a_lowercase_sha256(
    path: str, sha256: str, accepted: bool
) -> None:
    model: type[BaseModel] = TranscriptRef

    if not accepted:
        with pytest.raises(ValidationError):
            model(path=path, sha256=sha256)
        return
    ref = model(path=path, sha256=sha256)
    assert isinstance(ref, TranscriptRef)
    assert (ref.path, ref.sha256) == (path, sha256)
