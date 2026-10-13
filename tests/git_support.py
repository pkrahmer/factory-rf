"""Helpers for tests against real git: isolated runs, stand-in executables, the remote."""

import os
import sys
from pathlib import Path

from factory.adapters.process import ProcessRequest, run_process
from factory.domain.git import GitIdentity

CHECKOUT = "checkout"

TEST_IDENTITY = GitIdentity(name="Test Author", email="test@example.invalid")

PIPELINE_YAML = """\
contract: "1.0"
attempts_cap: 2
crash_cap: 2
acceptance_stage: acceptance
project_commands:
  check: {time_limit: 10}
  lint: {time_limit: 5}
  test: {time_limit: 10}
roles:
  intake: {write_paths: ["{work_item}"]}
  tester: {write_paths: ["tests/*"]}
  coder: {write_paths: ["src/*"]}
  reviewer: {write_paths: ["{work_item}"]}
  documenter: {write_paths: ["README.md", "docs/*"]}
  smoke-tester: {write_paths: ["{work_item}"]}
  acceptance-reviewer: {write_paths: ["{work_item}", "{feature}/backlog/*"]}
stages:
  intake: {role: intake, next: [tests]}
  tests: {role: tester, next: [doing], checks: [lint], reports: [test]}
  doing: {role: coder, next: [review, tests], checks: [check]}
  review: {role: reviewer, next: [docs, doing], round_cap: 3}
  docs: {role: documenter, next: [smoke-test, doing], checks: [check], round_cap: 3}
  smoke-test: {role: smoke-tester, next: [approval, doing], round_cap: 3}
  acceptance: {role: acceptance-reviewer, next: [approval]}
  approval: {approval: true, next: [done, doing]}
  done: {}
"""

STORY_FORM = """\
# Story title

## Description

## Interface

## Acceptance criteria

## Smoke test

## Journal
"""

REMOTE_FILES = {
    "factory/pipeline.yml": PIPELINE_YAML,
    "factory/story-form.md": STORY_FORM,
    "factory/features/F0001-example/feature.md": "# Example feature\n",
    "factory/features/F0001-example/backlog/F0001-S0001-first.md": "# First story\n",
}


def _environment() -> dict[str, str]:
    return {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": TEST_IDENTITY.name,
        "GIT_AUTHOR_EMAIL": TEST_IDENTITY.email,
        "GIT_COMMITTER_NAME": TEST_IDENTITY.name,
        "GIT_COMMITTER_EMAIL": TEST_IDENTITY.email,
    }


def run_git(directory: Path, *args: str) -> str:
    """Run real git in `directory` without user or system configuration; return its stdout."""
    result = run_process(
        ProcessRequest(argv=["git", *args], cwd=directory, env=_environment(), merge_stderr=True)
    )
    assert result.exit_status == 0, f"git {' '.join(args)} failed: {result.stdout}"
    return result.stdout


def write_files(directory: Path, files: dict[str, str]) -> None:
    """Write each text file under `directory` byte for byte as UTF-8."""
    for name, text in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))


def commit_all(directory: Path, message: str) -> str:
    """Commit everything in the work tree of `directory` and return the new commit id."""
    run_git(directory, "add", "-A")
    run_git(directory, "commit", "-q", "-m", message)
    return run_git(directory, "rev-parse", "HEAD").strip()


def clone(remote: Path, target: Path) -> Path:
    """Clone `remote` into `target` and return `target`."""
    run_git(target.parent, "clone", "-q", str(remote), target.name)
    return target


def make_remote(root: Path) -> Path:
    """Create the bare remote `root/remote.git` whose `main` holds `REMOTE_FILES`."""
    root.mkdir(parents=True, exist_ok=True)
    run_git(root, "init", "-q", "--initial-branch=main", "seed")
    seed = root / "seed"
    write_files(seed, REMOTE_FILES)
    commit_all(seed, "seed")
    run_git(root, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
    remote = root / "remote.git"
    run_git(seed, "push", "-q", str(remote), "main")
    return remote


def write_executable(directory: Path, body: str) -> Path:
    """Write a Python script with `body` that runs as an executable and return its path."""
    path = directory / "stand-in-git"
    path.write_text(f"#!{sys.executable}\n{body}\n", encoding="utf-8")
    path.chmod(0o755)
    return path
