"""The work item file: YAML front matter for the state, Markdown for the body."""

from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import override

import frontmatter
from frontmatter.default_handlers import YAMLHandler
from pydantic import ValidationError
from pydantic_core import ErrorDetails
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import YAMLError
from ruamel.yaml.nodes import ScalarNode
from ruamel.yaml.representer import RoundTripRepresenter
from ruamel.yaml.scalarstring import SingleQuotedScalarString

from factory.application.files import WorkItemReader, WorkItemWriter
from factory.domain.errors import WorkItemFormatError
from factory.domain.work_item import WorkItemDocument, WorkItemState

# Words a YAML 1.1 or 1.2 reader takes for null or a boolean; written quoted, they stay text.
_AMBIGUOUS_WORDS = frozenset({"null", "true", "false", "yes", "no", "on", "off", "y", "n"})
_NULL_TAG = "tag:yaml.org,2002:null"
# Wide enough that no value is ever folded onto a second line.
_LINE_WIDTH = 4096
# The rank of each kind of validation fault; the lowest is reported.
_UNKNOWN_KEY, _MISSING_KEY, _INVALID_VALUE, _INVALID_STATE = range(4)


class _NullAsWordRepresenter(RoundTripRepresenter):
    # The round-trip representer writes None as nothing (`claim:`); the notation says `null`.
    @override
    def represent_none(self, data: None) -> ScalarNode:
        return self.represent_scalar(_NULL_TAG, "null")


_NullAsWordRepresenter.add_representer(type(None), _NullAsWordRepresenter.represent_none)


class RuamelYamlHandler(YAMLHandler):
    """python-frontmatter's YAML handler, reading and writing the YAML with ruamel.yaml."""

    def __init__(self) -> None:
        """Prepare a safe loader and a dumper for the factory's notation."""
        super().__init__()
        self._loader = YAML(typ="safe")
        self._dumper = YAML(typ="rt")
        self._dumper.Representer = _NullAsWordRepresenter
        self._dumper.width = _LINE_WIDTH

    @override
    def load(self, fm: str, **kwargs: object) -> dict[str, object]:
        """The front matter as a mapping with text keys in file order; nothing gives `{}`."""
        try:
            loaded: object = self._loader.load(fm)
        except YAMLError as error:
            raise WorkItemFormatError("front matter is not valid YAML") from error
        if loaded is None:
            return {}
        if not isinstance(loaded, dict):
            raise WorkItemFormatError("front matter is not a mapping")
        return {str(key): value for key, value in loaded.items()}

    @override
    def export(self, metadata: dict[str, object], **kwargs: object) -> str:
        """The front matter in the factory's notation, without a final newline."""
        output = StringIO()
        self._dumper.dump(_notation(metadata), output)
        return output.getvalue().removesuffix("\n")


def _notation(value: object) -> object:
    if isinstance(value, dict):
        mapping = CommentedMap()
        for key, item in value.items():
            mapping[key] = _notation(item)
        return mapping
    if isinstance(value, list):
        return _sequence([_notation(item) for item in value])
    if isinstance(value, datetime):
        utc_text = value.astimezone(UTC).isoformat().removesuffix("+00:00") + "Z"
        return SingleQuotedScalarString(utc_text)
    if isinstance(value, str) and value in _AMBIGUOUS_WORDS:
        return SingleQuotedScalarString(value)
    return value


def _sequence(items: list[object]) -> CommentedSeq:
    sequence = CommentedSeq(items)
    if not any(isinstance(item, dict) for item in items):
        sequence.fa.set_flow_style()
    return sequence


def _normalised_body(body: str) -> str:
    stripped = body.strip()
    return f"{stripped}\n" if stripped else ""


def _key_path(location: tuple[int | str, ...]) -> str:
    path = ""
    for part in location:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}" if path else part
    return path


def _rank(error: ErrorDetails) -> int:
    if error["type"] == "extra_forbidden":
        return _UNKNOWN_KEY
    if error["type"] == "missing":
        return _MISSING_KEY
    if error["loc"]:
        return _INVALID_VALUE
    return _INVALID_STATE


def _fault(error: ErrorDetails) -> str:
    path = _key_path(error["loc"])
    rank = _rank(error)
    if rank == _UNKNOWN_KEY:
        return f"unknown key: {path}"
    if rank == _MISSING_KEY:
        return f"missing key: {path}"
    if rank == _INVALID_VALUE:
        return f"invalid {path}: {error['msg']}"
    return f"invalid state: {error['msg']}"


def _first_fault(validation_error: ValidationError) -> str:
    # `min` keeps the first of equal rank, and pydantic lists errors in the order of the fields.
    return _fault(min(validation_error.errors(), key=_rank))


class FrontmatterWorkItemReader(WorkItemReader):
    """Reads a work item file with python-frontmatter and ruamel.yaml."""

    def __init__(self) -> None:
        """Prepare the YAML handler."""
        self._handler = RuamelYamlHandler()

    @override
    def parse(self, text: str) -> WorkItemDocument:
        split = self._split(text)
        if split is None:
            raise WorkItemFormatError("no front matter")
        front_matter, body = split
        values = self._handler.load(front_matter)
        try:
            state = WorkItemState.model_validate(values)
        except ValidationError as error:
            raise WorkItemFormatError(_first_fault(error)) from error
        return WorkItemDocument(state=state, body=_normalised_body(body))

    @override
    def parse_specification(self, text: str) -> WorkItemDocument:
        split = self._split(text)
        if split is None:
            return WorkItemDocument(state=None, body=_normalised_body(text))
        front_matter, body = split
        ignored_keys = list(self._handler.load(front_matter))
        return WorkItemDocument(state=None, body=_normalised_body(body), ignored_keys=ignored_keys)

    @override
    def read(self, path: Path) -> WorkItemDocument:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise WorkItemFormatError(f"cannot read: {error}", str(path)) from error
        try:
            return self.parse(text)
        except WorkItemFormatError as error:
            raise WorkItemFormatError(error.fault, str(path)) from error

    def _split(self, text: str) -> tuple[str, str] | None:
        # The handler's own `detect` and `split`, not `frontmatter.parse`: given a handler,
        # that skips `detect`, returns an unclosed text whole and drops a non-mapping silently.
        prepared = text.replace("\r\n", "\n").strip()
        if not self._handler.detect(prepared):
            return None
        try:
            return self._handler.split(prepared)
        except ValueError:
            return None


class FrontmatterWorkItemWriter(WorkItemWriter):
    """Writes a work item file with python-frontmatter and ruamel.yaml."""

    def __init__(self) -> None:
        """Prepare the YAML handler."""
        self._handler = RuamelYamlHandler()

    @override
    def render(self, document: WorkItemDocument) -> str:
        if document.state is None:
            raise WorkItemFormatError("the document has no state")
        values: dict[str, object] = document.state.model_dump()
        post = frontmatter.Post(document.body.strip(), None, **values)
        return frontmatter.dumps(post, handler=self._handler) + "\n"

    @override
    def write(self, path: Path, document: WorkItemDocument) -> None:
        path.write_text(self.render(document), encoding="utf-8", newline="\n")
