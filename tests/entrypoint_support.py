"""The entrypoint tests' layout: its directories, its stub executables and its stamped lines."""

import re
from pathlib import Path

from factory.adapters.process import ProcessRequest, ProcessResult, run_process

ROOT = Path(__file__).parent.parent
ENTRYPOINT = ROOT / "image" / "entrypoint.sh"
STAMP = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ "
STAMPED = re.compile(rf"{STAMP}(?P<text>.*)")
SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"
AGENT_TEXT = "---\nmodel: sonnet\n---\nDo the work.\n"
SETTINGS_TEXT = '{"permissions": {}}\n'


class Layout:
    """The directories of one entrypoint run under `tmp_path`, and stubs that record calls."""

    def __init__(self, root: Path) -> None:
        self.opt = root / "opt"
        self.home = root / "user-home"
        self.claude_home = root / "claude-home"
        self.state = root / "state"
        self.bin = root / "bin"
        self.records = root / "records"
        for directory in (self.opt / "claude" / "agents", self.home, self.bin, self.records):
            directory.mkdir(parents=True)
        (self.opt / "claude" / "agents" / "coder.md").write_text(AGENT_TEXT, encoding="utf-8")
        (self.opt / "claude" / "settings.json").write_text(SETTINGS_TEXT, encoding="utf-8")
        self._stub(
            "python",
            f"printf '%s\\n' \"$@\" > '{self.records}/python-args'\npwd > '{self.records}/cwd'",
        )
        self._stub("git", f"printf '%s\\n' \"$*\" >> '{self.records}/git-calls'")

    def _stub(self, name: str, body: str) -> None:
        path = self.bin / name
        path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        path.chmod(0o755)

    def environment(
        self, *, claude_home: bool = True, instance: str | None = None
    ) -> dict[str, str]:
        environment = {
            "PATH": f"{self.bin}:{SYSTEM_PATH}",
            "HOME": str(self.home),
            "FACTORY_OPT": str(self.opt),
            "FACTORY_STATE": str(self.state),
        }
        if claude_home:
            environment["FACTORY_CLAUDE_HOME"] = str(self.claude_home)
        if instance is not None:
            environment["FACTORY_INSTANCE"] = instance
        return environment

    def run(self, environment: dict[str, str] | None = None) -> ProcessResult:
        return run_process(
            ProcessRequest(
                argv=["sh", str(ENTRYPOINT)],
                cwd=self.home,
                env=self.environment() if environment is None else environment,
            )
        )

    def python_args(self) -> list[str] | None:
        path = self.records / "python-args"
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else None


def texts(output: str) -> list[str]:
    texts = []
    for line in output.splitlines():
        match = STAMPED.fullmatch(line)
        assert match is not None, f"line without a time stamp: {line!r}"
        texts.append(match["text"])
    return texts
