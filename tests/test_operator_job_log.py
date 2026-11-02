"""The operator's job script: an execution's log and the job's status, read through `gcloud`."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from factory.adapters.process import ProcessResult
from git_support import write_executable
from operator_support import ROOT, operator_environment, run_script
from recording_stand_in_support import read_records

JOB_SCRIPT = ROOT / "operator" / "job" / "job.sh"
JOB = "factory-job"
BARE = {"SITE_PROJECT": "p1", "SITE_REGION": "europe-west3", "SITE_JOB": JOB}
IMPERSONATE = "deployer@p1.iam.gserviceaccount.com"
LOG_FORMAT = '--format=value(timestamp.date("%H:%M:%S"),textPayload)'
LOG_FLAGS = {"--order=asc", "--limit=4000", "--freshness=2d", LOG_FORMAT}
RULE = r"corp\.example\.invalid => <company-host>"
TOOL_RULE = r"tool:uv => tool:<tool>"
TOKEN = "ghp_" + "a" * 30
NO_LINES = "job: no log lines yet; Cloud Logging arrives one to two minutes late"
NO_STOP = "factory: no stop in the last 200 lines"
STOP_TEXT = "stop machine preflight_failed: tool:uv: uv is not on the PATH"
STOP_LINE = f"10:00:03\t2026-11-02T10:00:03Z {STOP_TEXT}"
STOP_SANITISED = "stop machine preflight_failed: tool:<tool>: uv is not on the PATH"
FILLER = "10:00:04\tSetting up libfoo1 (1.0-1) ..."
# A time zone far from UTC, so a time printed in local time shows.
FAR_ZONE = "XYZ-9"

# A stand-in for gcloud: it records its arguments. `logging read` prints the file
# STAND_IN_LOG; `executions list` reads the JSON list in STAND_IN_EXECUTIONS, keeps `--limit`
# of it and prints it as `--format` asks (json, the names, or names and running counts);
# `execute` prints STAND_IN_EXECUTION. The verb in STAND_IN_FAIL writes STAND_IN_FAIL_TEXT to
# standard error and exits 1.
GCLOUD_STAND_IN = r"""
import json, os, sys

arguments = sys.argv[1:]
with open(os.environ["STAND_IN_RECORD"], "a", encoding="utf-8") as record:
    record.write(json.dumps(arguments) + "\n")
words = [word for word in arguments if not word.startswith("-")]
flags = dict(word[2:].partition("=")[::2] for word in arguments if word.startswith("--"))
if words[:2] == ["logging", "read"]:
    verb = "logging read"
elif words[:4] == ["run", "jobs", "executions", "list"]:
    verb = "executions list"
else:
    verb = " ".join(words[:3])
if verb == os.environ.get("STAND_IN_FAIL"):
    sys.stderr.write(os.environ.get("STAND_IN_FAIL_TEXT", ""))
    sys.exit(1)
if verb == "logging read" and os.path.exists(os.environ.get("STAND_IN_LOG", "")):
    with open(os.environ["STAND_IN_LOG"], encoding="utf-8") as source:
        sys.stdout.write(source.read())
if verb == "executions list":
    executions = []
    if os.path.exists(os.environ.get("STAND_IN_EXECUTIONS", "")):
        with open(os.environ["STAND_IN_EXECUTIONS"], encoding="utf-8") as source:
            executions = json.load(source)
    if "limit" in flags:
        executions = executions[: int(flags["limit"])]
    shape = flags.get("format", "")
    if shape == "json":
        sys.stdout.write(json.dumps(executions, indent=2) + "\n")
    elif shape == "value(metadata.name)":
        sys.stdout.write("".join(row["metadata"]["name"] + "\n" for row in executions))
    else:
        for row in executions:
            count = row.get("status", {}).get("runningCount", "")
            sys.stdout.write(f"{row['metadata']['name']}\t{count}\n")
if verb == "run jobs execute":
    sys.stdout.write(os.environ.get("STAND_IN_EXECUTION", "") + "\n")
"""


@dataclass(frozen=True)
class JobWorld:
    """The `gcloud` stand-in, the site file, its rules file and the state folder in `tmp_path`."""

    tmp_path: Path
    bin_folder: Path
    site_file: Path
    records: Path

    @property
    def rules_file(self) -> Path:
        """The sanitiser's rules file beside the site file."""
        return self.site_file.parent / "sanitise.rules"

    @property
    def state_file(self) -> Path:
        """The file `job.sh execute` saves the execution's name in."""
        return self.tmp_path / "state" / "kumpel" / "last-execution"

    def save_execution(self, name: str) -> None:
        """Write `name` as the last execution, as `job.sh execute` does."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(f"{name}\n", encoding="utf-8")

    def run(
        self,
        job_words: list[str],
        *,
        values: dict[str, str] | None = None,
        log: list[str] | None = None,
        executions: list[dict[str, object]] | None = None,
        **extra: str,
    ) -> ProcessResult:
        """Run `job.sh` with `job_words`, the site `values`, the log `log` and `executions`."""
        site = BARE if values is None else values
        self.site_file.write_text(
            "".join(f"{key}={value}\n" for key, value in site.items()), encoding="utf-8"
        )
        log_file = self.tmp_path / "log.txt"
        log_file.write_text("".join(f"{line}\n" for line in log or []), encoding="utf-8")
        executions_file = self.tmp_path / "executions.json"
        executions_file.write_text(json.dumps(executions or []), encoding="utf-8")
        env = operator_environment(
            self.tmp_path,
            PATH=os.pathsep.join([str(self.bin_folder), os.environ["PATH"]]),
            FACTORY_SITE=str(self.site_file),
            XDG_STATE_HOME=str(self.tmp_path / "state"),
            STAND_IN_RECORD=str(self.records),
            STAND_IN_LOG=str(log_file),
            STAND_IN_EXECUTIONS=str(executions_file),
            TZ=FAR_ZONE,
            **extra,
        )
        return run_script([str(JOB_SCRIPT), *job_words], self.tmp_path, env)

    def calls(self) -> list[list[str]]:
        """The calls the stand-in recorded, oldest first."""
        return read_records(self.records)

    def log_reads(self) -> list[list[str]]:
        """The recorded `gcloud logging read` calls."""
        return [call for call in self.calls() if words(call)[:2] == ["logging", "read"]]


@pytest.fixture
def world(tmp_path: Path) -> JobWorld:
    """A `gcloud` stand-in first on the `PATH` and a site folder with a rules file."""
    bin_folder = tmp_path / "bin"
    bin_folder.mkdir()
    write_executable(bin_folder, GCLOUD_STAND_IN, name="gcloud")
    site_folder = tmp_path / "site"
    site_folder.mkdir()
    (site_folder / "sanitise.rules").write_text(f"{RULE}\n{TOOL_RULE}\n", encoding="utf-8")
    return JobWorld(tmp_path, bin_folder, site_folder / "site.env", tmp_path / "gcloud.jsonl")


def words(call: list[str]) -> list[str]:
    """The words of a call that are no flag, in order."""
    return [word for word in call if not word.startswith("-")]


def log_filter(name: str) -> str:
    """The Cloud Logging filter of the execution `name`."""
    return f'resource.type=cloud_run_job AND labels."run.googleapis.com/execution_name"={name}'


def execution(name: str, **status: object) -> dict[str, object]:
    """An execution as `gcloud run jobs executions list --format=json` gives it."""
    return {"metadata": {"name": name}, "status": status}


def numbered(count: int) -> list[str]:
    """`count` log lines, `line 1` to `line <count>`, each with its own time."""
    return [f"10:{index // 60:02}:{index % 60:02}\tline {index}" for index in range(1, count + 1)]


def test_log_reads_the_named_execution_and_prints_its_lines_in_order(world: JobWorld) -> None:
    lines = ["10:00:01\tjob-start: inputs", "10:00:02\tfactory: tick", "10:00:03\tdone"]
    result = world.run(["log", "--execution", "e1"], log=lines)
    assert result.exit_status == 0, result.stderr
    reads = world.log_reads()
    assert len(reads) == 1
    assert words(reads[0]) == ["logging", "read", log_filter("e1")]
    assert set(reads[0]) >= LOG_FLAGS
    assert result.stdout.splitlines() == lines


@pytest.mark.parametrize(
    ("flag", "saved", "newest", "expected"),
    [
        pytest.param("e-flag", "e-saved", "e-newest", "e-flag", id="option-over-state-file"),
        pytest.param(None, "e-saved", "e-newest", "e-saved", id="state-file-over-newest"),
        pytest.param(None, None, "e-newest", "e-newest", id="newest"),
        pytest.param(None, None, None, None, id="none"),
    ],
)
def test_log_chooses_the_execution(
    world: JobWorld, flag: str | None, saved: str | None, newest: str | None, expected: str | None
) -> None:
    if saved is not None:
        world.save_execution(saved)
    executions = [execution(newest, succeededCount=1)] if newest is not None else []
    options = ["--execution", flag] if flag is not None else []
    result = world.run(["log", *options], log=["10:00:01\tline"], executions=executions)
    if expected is None:
        assert result.exit_status == 1
        assert f"job: no execution of {JOB} found" in result.stdout + result.stderr
        assert world.log_reads() == []
    else:
        assert result.exit_status == 0, result.stderr
        assert [words(call)[2] for call in world.log_reads()] == [log_filter(expected)]


@pytest.mark.parametrize(
    ("count_words", "available", "expected"),
    [
        pytest.param(["3"], numbered(10), numbered(10)[-3:], id="three-of-ten"),
        pytest.param([], numbered(60), numbered(60), id="sixty-of-sixty"),
        pytest.param([], numbered(61), numbered(61)[-60:], id="sixty-of-sixty-one"),
        pytest.param(["0"], numbered(10), [], id="zero"),
    ],
)
def test_log_prints_the_last_n_lines(
    world: JobWorld, count_words: list[str], available: list[str], expected: list[str]
) -> None:
    result = world.run(["log", *count_words, "--execution", "e1"], log=available)
    assert result.exit_status == 0, result.stderr
    assert result.stdout.splitlines() == expected


@pytest.mark.parametrize(
    ("rules", "line", "expected"),
    [
        pytest.param(
            True,
            "10:00:01\tcloning https://corp.example.invalid/x",
            "10:00:01\tcloning https://<company-host>/x",
            id="site-pattern",
        ),
        pytest.param(
            True, f"10:00:01\tkey {TOKEN} end", "10:00:01\tkey ***TOKEN*** end", id="token"
        ),
        pytest.param(
            False,
            f"10:00:01\tkey {TOKEN} end",
            "10:00:01\tkey ***TOKEN*** end",
            id="no-rules-file",
        ),
    ],
)
def test_log_passes_its_lines_through_the_sanitiser(
    world: JobWorld, *, rules: bool, line: str, expected: str
) -> None:
    if not rules:
        world.rules_file.unlink()
    result = world.run(["log", "--execution", "e1"], log=[line, "10:00:02\tmore"])
    assert result.exit_status == 0, result.stderr
    assert result.stdout.splitlines() == [expected, "10:00:02\tmore"]
    warnings = [line for line in result.stderr.splitlines() if "no rules file" in line]
    assert len(warnings) == (0 if rules else 1), result.stderr


NOISE = [
    "10:00:01\tSelecting previously unselected package curl.",
    "10:00:01\tPreparing to unpack .../curl_8.deb ...",
    "10:00:01\tUnpacking curl (8.0-1) ...",
    "10:00:01\tSetting up curl (8.0-1) ...",
    "10:00:01\tGet:1 http://deb.debian.org/debian trixie InRelease",
    "10:00:01\tFetched 9 MB in 2s (4 MB/s)",
    "10:00:01\tProcessing triggers for libc-bin (2.41-1) ...",
    "10:00:01\tdebconf: unable to initialize frontend: Dialog",
    "10:00:01\tCopying blob sha256:abc",
    "10:00:01\tCopying config sha256:abc",
    "10:00:01\tWriting manifest to image destination",
    "10:00:01\tlogin: token refreshed: expires in 3600 s",
]
KEPT = "10:00:09\tfactory: tick"
MIDDLE = "10:00:01\tnote: Setting up the machine"


@pytest.mark.parametrize(
    ("lines", "quiet", "expected"),
    [
        *(
            pytest.param([noise, KEPT], True, [KEPT], id=f"drops-{noise.split(chr(9))[1][:12]}")
            for noise in NOISE
        ),
        pytest.param([MIDDLE, KEPT], True, [MIDDLE, KEPT], id="keeps-prefix-in-the-middle"),
        pytest.param([*NOISE, KEPT], False, [*NOISE, KEPT], id="keeps-all-without-quiet"),
    ],
)
def test_quiet_drops_the_noise(
    world: JobWorld, lines: list[str], *, quiet: bool, expected: list[str]
) -> None:
    options = ["--quiet"] if quiet else []
    result = world.run(["log", "--execution", "e1", *options], log=lines)
    assert result.exit_status == 0, result.stderr
    assert result.stdout.splitlines() == expected


def test_a_failing_logging_read_is_shown(world: JobWorld) -> None:
    result = world.run(
        ["log", "--execution", "e1"],
        log=["10:00:01\tline"],
        STAND_IN_FAIL="logging read",
        STAND_IN_FAIL_TEXT="ERROR: (gcloud.logging.read) PERMISSION_DENIED\nsecond line\n",
    )
    assert result.exit_status == 1
    assert result.stdout == ""
    assert (
        "job: gcloud logging read failed: ERROR: (gcloud.logging.read) PERMISSION_DENIED"
        in result.stderr.splitlines()
    )


def test_an_empty_answer_says_the_log_is_late(world: JobWorld) -> None:
    result = world.run(["log", "--execution", "e1"], log=[])
    assert result.exit_status == 0, result.stderr
    assert NO_LINES in (result.stdout + result.stderr).splitlines()


FAILED_MESSAGE = "Task factory-job-e4-task0 failed: the container exited with code 1."
SIX_EXECUTIONS: list[dict[str, object]] = [
    execution("e6", startTime="2026-11-02T12:00:10.123456Z", runningCount=1),
    execution(
        "e5",
        startTime="2026-11-02T11:00:10.123456Z",
        completionTime="2026-11-02T11:30:20.123456Z",
        succeededCount=1,
    ),
    execution(
        "e4",
        startTime="2026-11-02T10:00:10.123456Z",
        completionTime="2026-11-02T10:40:20.123456Z",
        failedCount=1,
        conditions=[
            {"type": "ResourcesAvailable", "status": "True"},
            {"type": "Completed", "status": "False", "reason": "Failed", "message": FAILED_MESSAGE},
        ],
    ),
    execution("e3", startTime="2026-11-02T09:05:30.123456Z"),
    execution(
        "e2",
        startTime="2026-11-02T08:00:10.123456Z",
        completionTime="2026-11-02T08:15:20.123456Z",
        succeededCount=1,
    ),
    execution(
        "e1",
        startTime="2026-11-02T07:00:10.123456Z",
        completionTime="2026-11-02T07:15:20.123456Z",
        succeededCount=1,
    ),
]


def test_status_lists_the_five_newest_executions(world: JobWorld) -> None:
    result = world.run(["status"], log=["10:00:01\tline"], executions=SIX_EXECUTIONS)
    listings = [call for call in world.calls() if "--format=json" in call]
    assert len(listings) == 1
    assert words(listings[0]) == ["run", "jobs", "executions", "list"]
    assert {f"--job={JOB}", "--limit=5"} <= set(listings[0])
    assert result.stdout.splitlines()[:5] == [
        "e6 running started 12:00",
        "e5 succeeded started 11:00 ended 11:30",
        f"e4 failed started 10:00 ended 10:40: {FAILED_MESSAGE}",
        "e3 waiting started 09:05",
        "e2 succeeded started 08:00 ended 08:15",
    ], result.stderr
    assert "e1" not in result.stdout.split()


PREFLIGHT_LINE = "10:00:05\t2026-11-02T10:00:05Z preflight: tool:uv: found"


@pytest.mark.parametrize(
    ("lines", "stopped"),
    [
        pytest.param(["10:00:01\tjob-start: inputs", STOP_LINE], True, id="stopped"),
        pytest.param(["10:00:01\tjob-start: inputs", "10:00:02\tfactory: tick"], False, id="none"),
        pytest.param([STOP_LINE, PREFLIGHT_LINE], False, id="preflight-after-stop"),
    ],
)
def test_status_shows_the_factory_s_stop(
    world: JobWorld, lines: list[str], *, stopped: bool
) -> None:
    result = world.run(["status"], log=lines, executions=[execution("e1", runningCount=1)])
    last = result.stdout.splitlines()[-1]
    if stopped:
        assert last.startswith("factory: stopped: "), result.stdout
        assert last.endswith(STOP_SANITISED), result.stdout
    else:
        assert last == NO_STOP, result.stdout


@pytest.mark.parametrize(
    ("fail", "fail_text", "message"),
    [
        pytest.param("", "", f"job: no execution of {JOB} found", id="no-execution"),
        pytest.param(
            "executions list",
            "ERROR: (gcloud.run.jobs.executions.list) PERMISSION_DENIED\nsecond line\n",
            "job: gcloud run jobs executions list failed: "
            "ERROR: (gcloud.run.jobs.executions.list) PERMISSION_DENIED",
            id="executions-list-fails",
        ),
        pytest.param(
            "logging read",
            "ERROR: (gcloud.logging.read) PERMISSION_DENIED\nsecond line\n",
            "job: gcloud logging read failed: ERROR: (gcloud.logging.read) PERMISSION_DENIED",
            id="logging-read-fails",
        ),
    ],
)
def test_status_shows_a_missing_execution_and_gcloud_failures(
    world: JobWorld, fail: str, fail_text: str, message: str
) -> None:
    executions = [execution("e1", runningCount=1)] if fail else []
    result = world.run(
        ["status"],
        log=["10:00:01\tline"],
        executions=executions,
        STAND_IN_FAIL=fail,
        STAND_IN_FAIL_TEXT=fail_text,
    )
    assert result.exit_status == 1
    shown = result.stderr if fail else result.stdout + result.stderr
    assert message in shown.splitlines()


@pytest.mark.parametrize("command", [["log"], ["status"]])
def test_log_and_status_read_the_execution_job_execute_saved(
    world: JobWorld, command: list[str]
) -> None:
    others = [execution("e-other", succeededCount=1)]
    saved = world.run(["execute"], executions=others, STAND_IN_EXECUTION="e-saved")
    assert saved.exit_status == 0, saved.stderr
    assert world.state_file.read_text(encoding="utf-8").strip() == "e-saved"
    result = world.run(command, log=["10:00:01\tline"], executions=others)
    assert result.exit_status == 0, result.stderr
    assert [words(call)[2] for call in world.log_reads()] == [log_filter("e-saved")]


@pytest.mark.parametrize(
    ("count_words", "expected"),
    [
        pytest.param([], ["10:00:01\ta", "10:00:03\tb", "10:00:05\tc"], id="all"),
        pytest.param(["2"], ["10:00:03\tb", "10:00:05\tc"], id="two"),
    ],
)
def test_log_leaves_out_empty_lines(
    world: JobWorld, count_words: list[str], expected: list[str]
) -> None:
    lines = ["10:00:01\ta", "", "10:00:03\tb", "", "", "10:00:05\tc", ""]
    result = world.run(["log", *count_words, "--execution", "e1"], log=lines)
    assert result.exit_status == 0, result.stderr
    assert result.stdout.splitlines() == expected


@pytest.mark.parametrize("command", [["log"], ["status"]])
def test_every_gcloud_call_carries_the_impersonation(world: JobWorld, command: list[str]) -> None:
    result = world.run(
        command,
        values={**BARE, "SITE_IMPERSONATE": IMPERSONATE},
        log=["10:00:01\tline"],
        executions=[execution("e1", runningCount=1)],
    )
    assert result.exit_status == 0, result.stderr
    calls = world.calls()
    assert {" ".join(words(call)[:2]) for call in calls} >= {"logging read", "run jobs"}
    for call in calls:
        assert f"--impersonate-service-account={IMPERSONATE}" in call, call


@pytest.mark.parametrize("command", [["log"], ["status"]])
@pytest.mark.parametrize("missing", ["SITE_PROJECT", "SITE_REGION", "SITE_JOB"])
def test_a_missing_site_value_is_refused(world: JobWorld, command: list[str], missing: str) -> None:
    values = {key: value for key, value in BARE.items() if key != missing}
    result = world.run(command, values=values, log=["10:00:01\tline"])
    assert result.exit_status == 2
    assert f"site: missing {missing} in {world.site_file}" in result.stderr.splitlines()
    assert world.calls() == []


def test_status_names_running_before_failed(world: JobWorld) -> None:
    executions = [execution("e1", startTime="2026-11-02T12:00:10Z", runningCount=1, failedCount=1)]
    result = world.run(["status"], log=["10:00:01\tline"], executions=executions)
    assert result.stdout.splitlines()[0].startswith("e1 running "), result.stdout


@pytest.mark.parametrize(
    ("after", "stopped"),
    [
        pytest.param(199, True, id="200th-from-the-end"),
        pytest.param(200, False, id="201st-from-the-end"),
    ],
)
def test_status_looks_for_the_stop_in_the_last_200_lines(
    world: JobWorld, after: int, *, stopped: bool
) -> None:
    lines = ["10:00:01\tjob-start: inputs", STOP_LINE, *[FILLER] * after]
    world.save_execution("e1")
    executions = [execution("e1", runningCount=1)]
    result = world.run(["status"], log=lines, executions=executions)
    world.run(["log"], log=lines, executions=executions)
    status_read, log_read = world.log_reads()
    assert status_read == log_read
    last = result.stdout.splitlines()[-1]
    if stopped:
        assert last.startswith("factory: stopped: "), result.stdout
        assert last.endswith(STOP_SANITISED), result.stdout
    else:
        assert last == NO_STOP, result.stdout


def test_only_the_stop_form_counts_as_a_stop(world: JobWorld) -> None:
    lines = ["10:00:01\tjob-start: inputs", "10:00:02\tjob: stop requested by user"]
    result = world.run(["status"], log=lines, executions=[execution("e1", runningCount=1)])
    assert result.stdout.splitlines()[-1] == NO_STOP, result.stdout


def test_quiet_that_leaves_no_line_prints_nothing(world: JobWorld) -> None:
    result = world.run(["log", "--execution", "e1", "--quiet"], log=NOISE)
    assert result.exit_status == 0, result.stderr
    assert result.stdout == ""
    assert NO_LINES not in result.stderr


@pytest.mark.parametrize(
    "job_words",
    [
        pytest.param(["log", "many"], id="n-not-a-number"),
        pytest.param(["log", "-1"], id="n-negative"),
        pytest.param(["log", "--bogus"], id="log-unknown-option"),
        pytest.param(["status", "--bogus"], id="status-unknown-option"),
    ],
)
def test_a_wrong_argument_prints_the_usage(world: JobWorld, job_words: list[str]) -> None:
    result = world.run(job_words, log=["10:00:01\tline"])
    assert result.exit_status == 2
    assert any(line.startswith("usage: job.sh") for line in result.stderr.splitlines())
