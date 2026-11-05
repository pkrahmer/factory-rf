"""The rule of a project's stage file and the layer it adds to the stage image."""

import hashlib

from pydantic import BaseModel, ConfigDict

STAGE_FILE = "factory/stage.Containerfile"
STAGE_FILE_LIMIT_BYTES = 64 * 1024

_DIGEST_LENGTH = 12
_BASE_ARGUMENT = "FACTORY_BASE"
_BASE_REFERENCES = ("${FACTORY_BASE}", "$FACTORY_BASE")
# The reader decodes with replacement, so bytes that were not UTF-8 arrive as this character
# and cannot be told from one the file holds; both are refused alike.
_REPLACEMENT_CHARACTER = "�"


class StageLayerRefused(ValueError):
    """A stage file that breaks the rule; its text is the reason."""


class StageLayer(BaseModel):
    """A stage file within the rule: its text, its digest and the identity of its image."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    digest: str
    identity: str


def project_image_tag(stage_image: str) -> str:
    """The tag of the image a project's stage file builds on `stage_image`."""
    return f"{stage_image}-project"


def stage_layer(text: str, base_identity: str) -> StageLayer:
    """The layer of the stage file `text` on the base of `base_identity`.

    `StageLayerRefused` with the reason when the file breaks the rule.
    """
    _require_rule(text)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]
    return StageLayer(text=text, digest=digest, identity=f"{base_identity}+{digest}")


def _require_rule(text: str) -> None:
    size = len(text.encode("utf-8"))
    if size > STAGE_FILE_LIMIT_BYTES:
        raise StageLayerRefused(
            f"the stage file is {size} bytes, more than {STAGE_FILE_LIMIT_BYTES}"
        )
    if _REPLACEMENT_CHARACTER in text:
        raise StageLayerRefused(
            "the stage file holds U+FFFD or bytes that are not UTF-8, which read as U+FFFD"
        )
    instructions = [line.strip() for line in text.splitlines() if _is_instruction(line)]
    froms = [index for index, line in enumerate(instructions) if _keyword(line) == "FROM"]
    if not froms:
        raise StageLayerRefused("the stage file holds no FROM")
    if len(froms) > 1:
        raise StageLayerRefused(f"the stage file holds {len(froms)} FROM instructions, not one")
    for line in instructions[: froms[0]]:
        if _keyword(line) != "ARG" or line.split()[1:] != [_BASE_ARGUMENT]:
            raise StageLayerRefused(f"only ARG {_BASE_ARGUMENT} may come before the FROM: {line}")
    base = instructions[froms[0]]
    if base.split()[1:] not in [[reference] for reference in _BASE_REFERENCES]:
        raise StageLayerRefused(f"the FROM must be FROM ${{{_BASE_ARGUMENT}}} alone: {base}")


def _is_instruction(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def _keyword(line: str) -> str:
    return line.split(maxsplit=1)[0].upper()
