"""The operator's site scripts: their paths, a run with a given environment and its exports."""

import os
import re
from pathlib import Path

from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from git_support import run_git

ROOT = Path(__file__).parent.parent
SITE_LIBRARY = ROOT / "operator" / "lib" / "site.sh"
SITE_COMMAND = ROOT / "operator" / "bin" / "site"
SITE_EXAMPLE = ROOT / "operator" / "site.env.example"
HOSTING_LIBRARY = ROOT / "operator" / "lib" / "hosting.sh"
KEY_LINE = re.compile(r"^(SITE_[A-Z0-9_]+)=")


def operator_environment(tmp_path: Path, **values: str) -> dict[str, str]:
    """An environment with `HOME` in `tmp_path`, the test's `PATH` and the given variables."""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    return {"PATH": os.environ["PATH"], "HOME": str(home), **values}


def run_script(argv: list[str], cwd: Path, env: dict[str, str]) -> ProcessResult:
    """Run `argv` with `sh` in `cwd` with exactly the environment `env`."""
    return run_process(ProcessRequest(argv=["sh", *argv], cwd=cwd, env=env))


def run_site(words: list[str], cwd: Path, env: dict[str, str]) -> ProcessResult:
    """Run the `site` command with `words`."""
    return run_script([str(SITE_COMMAND), *words], cwd, env)


def run_library(code: str, cwd: Path, env: dict[str, str]) -> ProcessResult:
    """Source the site library in `sh`, then run `code`."""
    return run_script(["-c", f'. "{SITE_LIBRARY}"\n{code}'], cwd, env)


def run_hosting(code: str, cwd: Path, env: dict[str, str], *, load: bool = True) -> ProcessResult:
    """Source the site library, `site_load` when `load`, then the hosting library; run `code`."""
    loading = 'site_load || exit "$?"\n' if load else ""
    return run_library(f'{loading}. "{HOSTING_LIBRARY}"\n{code}', cwd, env)


def load_site(cwd: Path, env: dict[str, str]) -> ProcessResult:
    """Run `site_load`, then print the environment; the run exits with the load's status."""
    return run_library('site_load\nstatus=$?\nenv\nexit "$status"\n', cwd, env)


def exported(stdout: str) -> dict[str, str]:
    """The `SITE_` variables in the output of `env`."""
    pairs = (line.partition("=") for line in stdout.splitlines() if line.startswith("SITE_"))
    return {name: value for name, _, value in pairs}


def example_keys() -> list[str]:
    """The `SITE_` keys of the example file, in its order."""
    lines = SITE_EXAMPLE.read_text(encoding="utf-8").splitlines()
    return [match.group(1) for line in lines if (match := KEY_LINE.match(line))]


def make_work_tree(directory: Path) -> Path:
    """Make `directory` a fresh git work tree."""
    directory.mkdir(parents=True, exist_ok=True)
    run_git(directory, "init", "-q")
    return directory
