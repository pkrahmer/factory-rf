"""What the tests of the operator's job script share: the job, its site values, a call's words."""

import base64
import gzip
import os
import re
import shutil
from collections.abc import Callable
from pathlib import Path

from factory.adapters.process import ProcessResult
from git_support import commit_all, run_git, write_executable
from operator_support import ROOT, operator_environment, run_script

JOB = "factory-job"
IMPERSONATE = "deployer@p1.iam.gserviceaccount.com"
# The site values every command of the job script needs.
BARE = {"SITE_PROJECT": "p1", "SITE_REGION": "europe-west3", "SITE_JOB": JOB}


def words(call: list[str]) -> list[str]:
    """The words of a call that are no flag, in order."""
    return [word for word in call if not word.startswith("-")]


TAG = "t1"
INSTANCE = "inst-x"
JOB_ROOT = f"/srv/factory/{INSTANCE}"
WRAPPER = re.compile(r"--args=-c,echo ([A-Za-z0-9+/=]+) \| base64 -d \| gzip -d \| sh")
START = "exec sh /tmp/job-start.sh"
START_SCRIPT = START.removeprefix("exec sh ")

# A stand-in for gcloud: it records its arguments; `describe` exits with STAND_IN_DESCRIBE
# (1, not found, by default) after writing STAND_IN_DESCRIBE_TEXT to standard error,
# `executions list` prints STAND_IN_EXECUTIONS, `execute` prints STAND_IN_EXECUTION;
# the verb STAND_IN_FAIL fails with STAND_IN_FAIL_STATUS and a text.
GCLOUD_STAND_IN = r"""
import json, os, sys

arguments = sys.argv[1:]
with open(os.environ["STAND_IN_RECORD"], "a", encoding="utf-8") as record:
    record.write(json.dumps(arguments) + "\n")
words = [word for word in arguments if not word.startswith("-")]
verb = "executions list" if words[2:4] == ["executions", "list"] else words[2]
if verb == os.environ.get("STAND_IN_FAIL"):
    sys.stderr.write("ERROR: (gcloud) FAILTEXT\n")
    sys.exit(int(os.environ.get("STAND_IN_FAIL_STATUS", "1")))
if verb == "describe":
    sys.stderr.write(os.environ.get("STAND_IN_DESCRIBE_TEXT", ""))
    sys.exit(int(os.environ.get("STAND_IN_DESCRIBE", "1")))
if verb == "executions list":
    sys.stdout.write(os.environ.get("STAND_IN_EXECUTIONS", ""))
if verb == "execute":
    sys.stdout.write(os.environ.get("STAND_IN_EXECUTION", "") + "\n")
"""

RunJob = Callable[..., ProcessResult]


def wrapper_of(call: list[str]) -> str:
    """The script the call's `--args` carries, decoded and un-gzipped."""
    arguments = [word for word in call if word.startswith("--args=")]
    assert len(arguments) == 1, call
    match = WRAPPER.fullmatch(arguments[0])
    assert match is not None, arguments[0]
    return gzip.decompress(base64.b64decode(match.group(1))).decode("utf-8")


def make_job_repository(folder: Path) -> Path:
    """A git repository in `folder` with `operator/` and `vm/` committed and tagged `t1`."""
    folder.mkdir()
    run_git(folder, "init", "-q")
    for name in ("operator", "vm"):
        shutil.copytree(ROOT / name, folder / name)
    commit_all(folder, "the operator's scripts")
    run_git(folder, "tag", TAG)
    return folder


def job_runner(tmp_path: Path, repository: Path, records: Path) -> RunJob:
    """Run `job.sh` of `repository` with `words`, a site file of `values` and extra variables.

    The names in `unset` are left out of the environment.
    """
    bin_folder = tmp_path / "bin"
    bin_folder.mkdir()
    write_executable(bin_folder, GCLOUD_STAND_IN, name="gcloud")
    site_folder = tmp_path / "site"
    site_folder.mkdir()
    site_file = site_folder / "site.env"

    def run(
        job_words: list[str], values: dict[str, str], *, unset: tuple[str, ...] = (), **extra: str
    ) -> ProcessResult:
        site_file.write_text(
            "".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8"
        )
        env = operator_environment(
            tmp_path,
            PATH=os.pathsep.join([str(bin_folder), os.environ["PATH"]]),
            FACTORY_SITE=str(site_file),
            XDG_STATE_HOME=str(tmp_path / "state"),
            GIT_CONFIG_NOSYSTEM="1",
            STAND_IN_RECORD=str(records),
            **extra,
        )
        for name in unset:
            del env[name]
        return run_script(
            [str(repository / "operator" / "job" / "job.sh"), *job_words], tmp_path, env
        )

    return run


def provider_text(tmp_path: Path, call: list[str]) -> str:
    """The `provider.json` the wrapper of `call` writes, run with its folders in `tmp_path`."""
    script = wrapper_of(call)
    root = tmp_path / "job-root"
    # The wrapper runs here with its two folders moved into tmp_path and without the hand-over.
    local = (
        script.replace(START, "exit 0")
        .replace(JOB_ROOT, str(root))
        .replace(START_SCRIPT, str(tmp_path / "job-start.sh"))
    )
    ran = run_script(["-c", local], tmp_path, operator_environment(tmp_path))
    assert ran.exit_status == 0, ran.stderr
    return (root / "provider.json").read_text(encoding="utf-8")
