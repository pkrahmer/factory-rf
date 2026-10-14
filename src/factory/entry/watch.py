"""The watcher's command line: the event the next tick would handle and the board."""

import argparse
import sys
from collections.abc import Sequence
from typing import TextIO

from factory.application.board import BoardReader
from factory.application.boundaries import Boundaries
from factory.application.pipeline_loading import PIPELINE_REF, PipelineLoader
from factory.application.watcher import Watcher
from factory.domain.board import render_board
from factory.domain.errors import GitError, PipelineDefinitionInvalid
from factory.domain.events import Event
from factory.domain.identifiers import Name

_PROGRAM = "factory-watch"
_OK = 0
_INVALID_DEFINITION = 1
_NOT_WIRED = 2


def render_event(event: Event) -> str:
    """The event's line: its key, and its detail after two spaces when it has one."""
    line = f"event: {event.key}"
    return f"{line}  {event.detail}" if event.detail else line


def run_watch(boundaries: Boundaries, instance: Name, out: TextIO, err: TextIO) -> int:
    """Evaluate the last fetch once as `instance`, write the event and the board, and return.

    Raises `GitError` when origin/main does not resolve.
    """
    commit = boundaries.git.resolve(PIPELINE_REF)
    if commit is None:
        raise GitError(f"resolve {PIPELINE_REF}", None, f"{PIPELINE_REF} does not resolve")
    try:
        # Loading at the commit rather than the ref keeps the watcher from touching the stop.
        definition = PipelineLoader(boundaries).load(commit)
    except PipelineDefinitionInvalid as error:
        err.write(f"{_PROGRAM}: {error.fault}\n")
        return _INVALID_DEFINITION
    event = Watcher(boundaries, instance).evaluate(definition)
    view = BoardReader(boundaries).read(definition)
    out.write(f"{render_event(event)}\n\n{render_board(view.features, view.rows)}")
    return _OK


def main(
    argv: Sequence[str] | None = None,
    *,
    boundaries: Boundaries | None = None,
    instance: Name | None = None,
    out: TextIO | None = None,
    err: TextIO | None = None,
) -> int:
    """Parse the arguments, `argv` or the command's, then watch with the boundaries given."""
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.parse_args(sys.argv[1:] if argv is None else argv)
    if boundaries is None or instance is None:
        (sys.stderr if err is None else err).write(
            f"{_PROGRAM}: no instance settings are wired yet\n"
        )
        return _NOT_WIRED
    return run_watch(
        boundaries, instance, sys.stdout if out is None else out, sys.stderr if err is None else err
    )


if __name__ == "__main__":
    raise SystemExit(main())
