# SPDX-License-Identifier: Apache-2.0
"""Runs a document's examples as processes, each document in a temporary folder of its own."""

import os
import tempfile
from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path

from factory.shared.adapters.process import ProcessRequest, run_process
from factory.shared.application.document_examples import ExampleRunner, Fixture
from factory.shared.domain.documents import Command, Example, first_difference
from factory.shared.domain.errors import FixtureError
from factory.shared.domain.sections import split_lines

EXAMPLE_TIME_LIMIT = timedelta(seconds=60)
_FALLBACK_PATH = "/usr/local/bin:/usr/bin:/bin"
_WORK_FOLDER = "work"
_HOME_FOLDER = "home"
_NOTHING_MORE = "nothing more"


def _fixed_environment(home: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", _FALLBACK_PATH),
        "HOME": str(home),
        "TZ": "UTC",
        "LANG": "C.UTF-8",
    }


def _env_arguments(environment: Mapping[str, str]) -> list[str]:
    return [f"{name}={value}" for name, value in environment.items()]


class _DocumentRun:
    """The folder, the home, the prepared fixtures and the findings of one document's examples."""

    def __init__(self, document: str, scratch: Path, fixtures: Mapping[str, Fixture]) -> None:
        self._document = document
        self._fixtures = fixtures
        self._folder = scratch / _WORK_FOLDER
        self._home = scratch / _HOME_FOLDER
        self._folder.mkdir()
        self._home.mkdir()
        self._prepared: dict[str, dict[str, str]] = {}
        self._unprepared: set[str] = set()
        self.findings: list[str] = []

    def add_finding(self, line: int, message: str) -> None:
        self.findings.append(f"{self._document}:{line}: {message}")

    def environment(self, example: Example) -> dict[str, str] | None:
        """The environment of the block's commands, or None when its fixture is not there."""
        fixture = example.fixture
        # A fixture that failed once is reported once; the document's later blocks on it are
        # left out without a finding of their own.
        if fixture in self._unprepared:
            return None
        if fixture not in self._fixtures:
            self.add_finding(example.line, f"no fixture {fixture}")
            return None
        # Every block of the document shares the folder, so a fixture is prepared at most once.
        if fixture not in self._prepared:
            try:
                self._prepared[fixture] = self._fixtures[fixture].prepare(self._folder)
            except FixtureError:
                self._unprepared.add(fixture)
                self.add_finding(example.line, f"fixture {fixture} could not be prepared")
                return None
        # The fixed environment comes last, so that no fixture can lift it.
        return {**self._prepared[fixture], **_fixed_environment(self._home)}

    def request(
        self, command: Command, environment: Mapping[str, str], limit: timedelta
    ) -> ProcessRequest:
        argv = ["env", "-i", *_env_arguments(environment), "sh", "-c", command.command]
        return ProcessRequest(argv=argv, cwd=self._folder, time_limit=limit, merge_stderr=True)


def _difference(command: Command, output: str) -> str | None:
    printed = split_lines(output)
    index = first_difference(command.expected, printed)
    if index is None:
        return None
    shown = printed[index] if index < len(printed) else _NOTHING_MORE
    return f"the example printed {shown}"


class ProcessExampleRunner(ExampleRunner):
    """Runs each command through `sh -c` under `env -i`, its output compared with the expected."""

    def __init__(self, time_limit: timedelta = EXAMPLE_TIME_LIMIT) -> None:
        """Give each command at most `time_limit`."""
        self._time_limit = time_limit

    def run_document(
        self, document: str, examples: list[Example], fixtures: Mapping[str, Fixture]
    ) -> list[str]:
        """Run the blocks in order in one new folder; a command past its limit ends the document."""
        with tempfile.TemporaryDirectory() as scratch:
            run = _DocumentRun(document, Path(scratch), fixtures)
            for example in examples:
                environment = run.environment(example)
                if environment is None:
                    continue
                for command in example.commands:
                    result = run_process(run.request(command, environment, self._time_limit))
                    if result.timed_out:
                        run.add_finding(command.line, self._no_end())
                        return run.findings
                    message = _difference(command, result.stdout)
                    if message is not None:
                        run.add_finding(command.line, message)
            return run.findings

    def _no_end(self) -> str:
        return f"the example did not end in {self._time_limit.total_seconds():g} s"
