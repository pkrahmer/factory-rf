"""The rule of a project's stage file, its digest and the identity of its layer."""

import hashlib

import pytest

from factory.domain.stage_layer import STAGE_FILE, StageLayerRefused, project_image_tag, stage_layer

BASE_IDENTITY = "sha256-base"
TEMPLATE = (
    "ARG FACTORY_BASE\n"
    "FROM ${FACTORY_BASE}\n"
    "RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake"
    " && rm -rf /var/lib/apt/lists/*\n"
)
LIMIT = 64 * 1024


def _padded(size: int) -> str:
    # A comment after the FROM fills the file to `size` bytes of UTF-8.
    head = "FROM ${FACTORY_BASE}\n# "
    return head + "x" * (size - len(head) - 1) + "\n"


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


ACCEPTED = [
    pytest.param(TEMPLATE, id="template"),
    pytest.param("FROM ${FACTORY_BASE}\n", id="from-alone"),
    pytest.param("from $FACTORY_BASE\n", id="lower-case"),
    pytest.param("# tools\n\nARG FACTORY_BASE\nFROM ${FACTORY_BASE}\n", id="comment-and-blank"),
    pytest.param(_padded(LIMIT), id="64-kib"),
]
REFUSED = [
    pytest.param("FROM debian:bookworm\n", id="other-image"),
    pytest.param("ARG FACTORY_BASE\nFROM ${FACTORY_BASE} AS build\n", id="as-name"),
    pytest.param("ARG FACTORY_BASE\nFROM --platform=linux/amd64 ${FACTORY_BASE}\n", id="platform"),
    pytest.param(
        "ARG FACTORY_BASE\nFROM ${FACTORY_BASE}\nFROM ${FACTORY_BASE}\n", id="second-from"
    ),
    pytest.param("ARG FACTORY_BASE\nRUN true\n", id="no-from"),
    pytest.param("RUN true\nFROM ${FACTORY_BASE}\n", id="run-before-from"),
    pytest.param("ARG OTHER\nFROM ${FACTORY_BASE}\n", id="other-arg-before-from"),
    pytest.param(_padded(LIMIT + 1), id="one-byte-over-64-kib"),
    # Bytes that are not UTF-8 reach the rule as U+FFFD, the reader's replacement.
    pytest.param("FROM ${FACTORY_BASE}\n# \ufffd\n", id="not-utf-8-or-u-fffd"),
]


@pytest.mark.parametrize(
    ("text", "accepted"),
    [
        *(pytest.param(*case.values, True, id=case.id) for case in ACCEPTED),
        *(pytest.param(*case.values, False, id=case.id) for case in REFUSED),
    ],
)
def test_a_stage_file_is_accepted_or_refused_by_its_rule(text: str, *, accepted: bool) -> None:
    if not accepted:
        with pytest.raises(StageLayerRefused) as refusal:
            stage_layer(text, BASE_IDENTITY)
        assert str(refusal.value)
        return

    layer = stage_layer(text, BASE_IDENTITY)

    assert layer.text == text
    assert layer.digest == _digest(text)
    assert layer.identity == f"{BASE_IDENTITY}+{_digest(text)}"


def test_each_broken_rule_gives_its_own_reason() -> None:
    reasons: list[str] = []
    for case in REFUSED:
        [text] = case.values
        with pytest.raises(StageLayerRefused) as refusal:
            stage_layer(str(text), BASE_IDENTITY)
        reasons.append(str(refusal.value))

    assert len(set(reasons)) == len(reasons)


def test_the_padded_files_lie_on_both_sides_of_64_kib() -> None:
    assert [len(_padded(size).encode("utf-8")) for size in (LIMIT, LIMIT + 1)] == [65536, 65537]


def test_the_digest_follows_every_byte_and_the_identity_is_stable() -> None:
    other = TEMPLATE.replace("cmake", "cmakf")

    first = stage_layer(TEMPLATE, BASE_IDENTITY)
    second = stage_layer(TEMPLATE, BASE_IDENTITY)
    changed = stage_layer(other, BASE_IDENTITY)

    assert (first.digest, first.identity) == (second.digest, second.identity)
    assert changed.digest != first.digest
    assert len(first.digest) == 12
    assert all(character in "0123456789abcdef" for character in first.digest)
    assert first.identity == f"{BASE_IDENTITY}+{first.digest}"


def test_the_stage_file_and_the_project_image_tag_are_named_once() -> None:
    assert STAGE_FILE == "factory/stage.Containerfile"
    assert project_image_tag("factory-stage:vm") == "factory-stage:vm-project"
