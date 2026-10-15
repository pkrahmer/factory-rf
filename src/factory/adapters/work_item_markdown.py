"""The work item file: YAML front matter for the state, Markdown for the body."""

from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import override

import frontmatter
from frontmatter.default_handlers import YAMLHandler
from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import YAMLError
from ruamel.yaml.nodes import ScalarNode
from ruamel.yaml.representer import RoundTripRepresenter
from ruamel.yaml.scalarstring import SingleQuotedScalarString

from factory.adapters.validation_faults import first_fault
from factory.application.files import WorkItemReader, WorkItemWriter
from factory.domain.acceptance import AcceptanceState
from factory.domain.errors import WorkItemFormatError
from factory.domain.work_item import WorkItemDocument, WorkItemState, require_state

# Words a YAML 1.1 or 1.2 reader takes for null or a boolean; written quoted, they stay text.
_AMBIGUOUS_WORDS = frozenset({"null", "true", "false", "yes", "no", "on", "off", "y", "n"})
_NULL_TAG = "tag:yaml.org,2002:null"
# Either key makes the front matter an acceptance's; a story's has neither.
_ACCEPTANCE_KEYS = frozenset(AcceptanceState.model_fields) - frozenset(WorkItemState.model_fields)
# Wide enough that no value is ever folded onto a second line.
_LINE_WIDTH = 4096


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


def split_front_matter(handler: RuamelYamlHandler, text: str) -> tuple[str, str] | None:
    """The front matter text and the body of `text`, or None when it has no front matter."""
    # The handler's own `detect` and `split`, not `frontmatter.parse`: given a handler,
    # that skips `detect`, returns an unclosed text whole and drops a non-mapping silently.
    prepared = text.replace("\r\n", "\n").strip()
    if not handler.detect(prepared):
        return None
    try:
        return handler.split(prepared)
    except ValueError:
        return None


def _state_model(values: dict[str, object]) -> type[WorkItemState]:
    if _ACCEPTANCE_KEYS.intersection(values):
        return AcceptanceState
    return WorkItemState


class FrontmatterWorkItemReader(WorkItemReader):
    """Reads a work item file with python-frontmatter and ruamel.yaml."""

    def __init__(self) -> None:
        """Prepare the YAML handler."""
        self._handler = RuamelYamlHandler()

    @override
    def parse(self, text: str) -> WorkItemDocument:
        split = split_front_matter(self._handler, text)
        if split is None:
            raise WorkItemFormatError("no front matter")
        front_matter, body = split
        values = self._handler.load(front_matter)
        try:
            state = _state_model(values).model_validate(values)
        except ValidationError as error:
            raise WorkItemFormatError(first_fault(error, "state")) from error
        return WorkItemDocument(state=state, body=_normalised_body(body))

    @override
    def parse_specification(self, text: str) -> WorkItemDocument:
        split = split_front_matter(self._handler, text)
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


class FrontmatterWorkItemWriter(WorkItemWriter):
    """Writes a work item file with python-frontmatter and ruamel.yaml."""

    def __init__(self) -> None:
        """Prepare the YAML handler."""
        self._handler = RuamelYamlHandler()

    @override
    def render(self, document: WorkItemDocument) -> str:
        state = require_state(document, WorkItemFormatError("the document has no state"))
        values: dict[str, object] = state.model_dump()
        post = frontmatter.Post(document.body.strip(), None, **values)
        return frontmatter.dumps(post, handler=self._handler) + "\n"

    @override
    def write(self, path: Path, document: WorkItemDocument) -> None:
        path.write_text(self.render(document), encoding="utf-8", newline="\n")
