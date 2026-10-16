"""The entrypoint's umask: the factory's own files are group-writable, like the agent's."""

from pathlib import Path

from factory.adapters.process import ProcessRequest, ProcessResult, run_process

ROOT = Path(__file__).parent.parent
ENTRYPOINT = ROOT / "image" / "entrypoint.sh"
SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"


def _run_with_umask_stub(root: Path) -> tuple[ProcessResult, Path]:
    opt = root / "opt"
    agents = opt / "claude" / "agents"
    stubs = root / "bin"
    home = root / "home"
    for directory in (agents, stubs, home):
        directory.mkdir(parents=True)
    (agents / "coder.md").write_text("---\nmodel: sonnet\n---\nDo the work.\n", encoding="utf-8")
    (opt / "claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    recorded = root / "umask"
    python = stubs / "python"
    python.write_text(f"#!/bin/sh\numask > '{recorded}'\n", encoding="utf-8")
    python.chmod(0o755)
    result = run_process(
        ProcessRequest(
            argv=["sh", str(ENTRYPOINT)],
            cwd=home,
            env={
                "PATH": f"{stubs}:{SYSTEM_PATH}",
                "HOME": str(home),
                "FACTORY_OPT": str(opt),
                "FACTORY_CLAUDE_HOME": str(root / "claude-home"),
                "FACTORY_STATE": str(root / "state"),
            },
        )
    )
    return result, recorded


def test_the_entrypoint_sets_umask_002_after_set_eu_and_starts_the_instance_with_it(
    tmp_path: Path,
) -> None:
    lines = [line.strip() for line in ENTRYPOINT.read_text(encoding="utf-8").splitlines()]
    strict = lines.index("set -eu")

    result, recorded = _run_with_umask_stub(tmp_path)

    assert lines[strict + 1] == "umask 002"
    assert result.exit_status == 0
    assert recorded.read_text(encoding="utf-8").strip() == "0002"
