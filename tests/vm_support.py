"""The machine's setup script and service unit: their paths, the steps and the script's texts."""

from pathlib import Path

from dockerfile_support import _uncommented
from entrypoint_support import ROOT, SYSTEM_PATH
from factory.adapters.process import ProcessRequest, ProcessResult, run_process

SETUP = ROOT / "vm" / "setup.sh"
SERVICE = ROOT / "vm" / "factory.service"
STEPS = (
    "packages",
    "pool",
    "user",
    "linger",
    "datasets",
    "delegation",
    "sudoers",
    "folders",
    "image-id",
    "checkout",
    "tools",
    "environment",
    "service",
)
REQUIRED = ["--device", "/dev/null", "--repository-url", "https://example.invalid/r.git"]


def setup_code() -> str:
    """The setup script's text with its comment lines dropped."""
    return _uncommented(SETUP.read_text(encoding="utf-8"))


def step_texts(code: str) -> dict[str, str]:
    """Each step's text: from the end of the previous step's last line to its own last line."""
    texts: dict[str, str] = {}
    start = 0
    for step in STEPS:
        marker = code.rfind(f"setup: {step}: ")
        assert marker >= 0, f"no 'setup: {step}: ' text"
        end = code.find("\n", marker)
        end = len(code) if end < 0 else end
        texts[step] = code[start:end]
        start = end
    return texts


def run_setup(cwd: Path, words: list[str], path: str = SYSTEM_PATH) -> ProcessResult:
    """Run the setup script with `sh` in `cwd` with the given words and `PATH`."""
    return run_process(ProcessRequest(argv=["sh", str(SETUP), *words], cwd=cwd, env={"PATH": path}))


def entries(root: Path) -> set[Path]:
    """Every path under `root`."""
    return set(root.rglob("*"))
