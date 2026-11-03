"""The skill scripts on an operator's machine in `tmp_path`: site, `curl` stand-in, answers."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from factory.adapters.process import ProcessResult
from git_support import commit_all, run_git, write_executable, write_files
from operator_support import CURL_STAND_IN, ROOT, hosting_env, run_script

SCRIPTS = ROOT / "operator" / "skill" / "kumpel" / "scripts"
REPOSITORY = "owner/repo"
PREFIX = f"/repos/{REPOSITORY}"
API_URL = "https://api.example.invalid"
# The command builds the token, so its text is in no file the test writes.
ACCESS_COMMAND = "printf 'tok%s\\n' 123"
GIT_VARIABLES = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_AUTHOR_NAME": "Operator",
    "GIT_AUTHOR_EMAIL": "operator@example.invalid",
    "GIT_COMMITTER_NAME": "Operator",
    "GIT_COMMITTER_EMAIL": "operator@example.invalid",
}


@dataclass(frozen=True)
class Operator:
    """The operator's machine in `tmp_path`: a site file, the `curl` stand-in and a checkout."""

    tmp_path: Path
    site_file: Path
    records: Path
    temporary: Path
    bin_folder: Path
    routes_file: Path
    settings_file: Path
    checkout: Path

    def write_site(self, **values: str) -> None:
        """Write the site file with exactly `values`."""
        lines = [f"{name}={value}\n" for name, value in values.items()]
        self.site_file.write_text("# the site of a test\n" + "".join(lines), encoding="utf-8")

    def answer(self, routes: dict[str, object]) -> None:
        """Let the `curl` stand-in answer each path (with or without its query) with its JSON."""
        bodies = {route: json.dumps(value) for route, value in routes.items()}
        self.routes_file.write_text(json.dumps(bodies), encoding="utf-8")

    def run(self, script: str, *arguments: str) -> ProcessResult:
        """Run the skill's `script` with `arguments` on this machine."""
        env = hosting_env(
            self.tmp_path,
            self.site_file,
            self.records,
            self.temporary,
            self.bin_folder,
            STAND_IN_CURL_ROUTES=str(self.routes_file),
            KUMPEL_SETTINGS=str(self.settings_file),
            **GIT_VARIABLES,
        )
        return run_script([str(SCRIPTS / script), *arguments], self.tmp_path, env)

    def urls(self) -> list[str]:
        """The path and query of every URL the `curl` stand-in was asked for, in order."""
        path = self.records / "curl.jsonl"
        if not path.exists():
            return []
        found = []
        for line in path.read_text(encoding="utf-8").splitlines():
            configuration = str(json.loads(line)["stdin"])
            match = re.search(r'^url = "([^"]*)"$', configuration, re.MULTILINE)
            if match:
                found.append(match.group(1).removeprefix(API_URL))
        return found


def make_operator(tmp_path: Path) -> Operator:
    """The operator's machine with a full site file (a token command, no `gh`) and no answers."""
    folders = {name: tmp_path / name for name in ("site", "records", "tmp", "bin")}
    for folder in folders.values():
        folder.mkdir()
    write_executable(folders["bin"], CURL_STAND_IN, name="curl")
    machine = Operator(
        tmp_path=tmp_path,
        site_file=folders["site"] / "site.env",
        records=folders["records"],
        temporary=folders["tmp"],
        bin_folder=folders["bin"],
        routes_file=tmp_path / "routes.json",
        settings_file=tmp_path / "settings" / "settings.json",
        checkout=tmp_path / "checkout",
    )
    machine.write_site(
        SITE_REPOSITORY=REPOSITORY,
        SITE_CHECKOUT=str(machine.checkout),
        SITE_API_URL=API_URL,
        SITE_TOKEN_CMD=ACCESS_COMMAND,
    )
    machine.answer({})
    return machine


def make_bare_remote(root: Path, files: dict[str, str]) -> tuple[Path, Path]:
    """A bare remote `root/remote.git` whose `main` holds `files`, and the seed that pushes."""
    root.mkdir(parents=True, exist_ok=True)
    run_git(root, "init", "-q", "--initial-branch=main", "seed")
    seed = root / "seed"
    write_files(seed, files)
    commit_all(seed, "seed")
    run_git(root, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
    remote = root / "remote.git"
    run_git(seed, "remote", "add", "origin", str(remote))
    run_git(seed, "push", "-q", "origin", "main")
    return remote, seed


def pull(number: int, branch: str, labels: list[str]) -> dict[str, object]:
    """One pull request as the API lists it."""
    return {
        "number": number,
        "state": "open",
        "head": {"ref": branch},
        "labels": [{"name": name} for name in labels],
    }


def comment_routes(number: int, bodies: list[str]) -> dict[str, object]:
    """The issue of pull request `number` with its comment count, and its newest comment."""
    routes: dict[str, object] = {
        f"{PREFIX}/issues/{number}": {"number": number, "comments": len(bodies)}
    }
    if bodies:
        page = f"{PREFIX}/issues/{number}/comments?per_page=1&page={len(bodies)}"
        routes[page] = [{"id": len(bodies), "body": bodies[-1]}]
    return routes


def commits(*messages: str) -> dict[str, object]:
    """The route of the newest commits on `main`, newest first."""
    return {f"{PREFIX}/commits?per_page=20": [{"commit": {"message": text}} for text in messages]}


ARCHIVE = "work item F0001-S0000: merged, archived"


def status_routes(
    pulls: list[dict[str, object]], bodies: dict[int, list[str]]
) -> dict[str, object]:
    """The answers `status.sh` needs: the open pull requests, their comments, the commits."""
    routes: dict[str, object] = {f"{PREFIX}/pulls?state=open&per_page=50": pulls}
    for number, texts in bodies.items():
        routes.update(comment_routes(number, texts))
    routes.update(commits(ARCHIVE))
    return routes
