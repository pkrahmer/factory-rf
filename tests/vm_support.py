"""The machine's setup script and service unit: their paths, the steps and the script's texts."""

import os
import re
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from dockerfile_support import _uncommented
from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from time_limits import ROOMY_LIMIT

ROOT = Path(__file__).parent.parent
SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"
SETUP = ROOT / "vm" / "setup.sh"
SERVICE = ROOT / "vm" / "factory.service"
HELPER = ROOT / "vm" / "git-credential-factory"
EXAMPLE_VALUE = "example-value"
STEPS = (
    "packages",
    "pool",
    "user",
    "linger",
    "datasets",
    "delegation",
    "sudoers",
    "caches",
    "poweroff",
    "folders",
    "image-id",
    "checkout",
    "tools",
    "environment",
    "service",
)
FUNCTION = re.compile(r"(?ms)^(\w+)\(\)\s*\{(.*?)^\}")
REQUIRED = ["--device", "/dev/null", "--repository-url", "https://example.invalid/r.git"]
VALUE_END = r"(?![\w/.:{$-])"
ENVIRONMENT = (
    ("FACTORY_INSTANCE", re.escape("$instance") + VALUE_END),
    ("FACTORY_REPOSITORY_URL", re.escape("$repository_url") + VALUE_END),
    ("FACTORY_AGENT_RUNTIME", re.escape("$runtime") + VALUE_END),
    ("FACTORY_DATASET", re.escape("$pool/factory/$instance") + VALUE_END),
    ("FACTORY_WORKSPACE", re.escape("$base/work") + VALUE_END),
    ("FACTORY_STAGE_IMAGE", re.escape("$image") + VALUE_END),
    ("FACTORY_ZFS", r"\$"),
    ("FACTORY_CHECKOUT", re.escape("$base/repo") + VALUE_END),
    ("FACTORY_STATE", re.escape("$base/state") + VALUE_END),
    ("FACTORY_IMAGE_ID_FILE", re.escape("$base/image-id") + VALUE_END),
    ("FACTORY_CLAUDE_HOME", re.escape("$base/factory/claude") + VALUE_END),
    ("FACTORY_TOKEN_FILE", re.escape("/home/factory/.secrets/hosting-token") + VALUE_END),
    ("FACTORY_CLAUDE_LOGIN_FILE", re.escape("/home/factory/.secrets/claude-token") + VALUE_END),
    ("FACTORY_API_LOGIN_FILE", re.escape("/home/factory/.secrets/anthropic-api-key") + VALUE_END),
    ("FACTORY_CLAUDE_VERSION", r"\$(?P<pin>[A-Za-z_]\w*)" + VALUE_END),
    ("FACTORY_OPENCODE_VERSION", r"\$(?P<pin>[A-Za-z_]\w*)" + VALUE_END),
    ("FACTORY_OPENCODE_MODELS", r"\$(?P<pin>[A-Za-z_]\w*)" + VALUE_END),
    (
        "PATH",
        re.escape("/srv/factory/")
        + r"\S*"
        + re.escape("/tools/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"),
    ),
    ("XDG_RUNTIME_DIR", re.escape("/run/user/$(id -u factory)") + VALUE_END),
)
COMPARISONS = re.compile(r"(?<![\w-])(?:cmp|diff|grep\s+(?:-\w*x\w*\s+|.*\s-\w*x))")


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


def write_helpers(code: str) -> list[str]:
    """The names of the script's functions whose body writes with `cat >` through `as_factory`."""
    return [
        name
        for name, body in FUNCTION.findall(code)
        if "cat >" in body and re.search(r"(?<![\w-])as_factory(?![\w-])", body)
    ]


def function_text(code: str, name: str) -> str:
    """The text of the script's function `name`, from its first line to its closing brace."""
    found = next(match for match in FUNCTION.finditer(code) if match.group(1) == name)
    return found.group(0)


def name_positions(code: str, name: str) -> list[int]:
    """Where the script assigns `name=`, leaving out the Dockerfile's `ENV` lines it reads."""
    return [
        found.start()
        for found in re.finditer(rf"(?<![A-Za-z_]){name}=", code)
        if not code[: found.start()].endswith("ENV ")
    ]


def lines_with(text: str, word: str) -> list[str]:
    """The lines of `text` that hold `word`."""
    return [line for line in text.splitlines() if word in line]


def in_order(text: str, words: list[str]) -> bool:
    """Whether every word is in `text` and their first places come in the words' order."""
    positions = [text.find(word) for word in words]
    return -1 not in positions and positions == sorted(positions)


def indent(line: str) -> int:
    """The number of blanks before the line's first word."""
    return len(line) - len(line.lstrip())


def enclosing_if(lines: list[str], index: int) -> int | None:
    """The index of the `if` line the line at `index` is indented under, if it is an `if`."""
    for earlier in range(index - 1, -1, -1):
        line = lines[earlier]
        if line.strip() and indent(line) < indent(lines[index]):
            return earlier if line.lstrip().startswith("if ") else None
    return None


def compares(code: str, line: str, path: str) -> bool:
    """Whether the line compares `path`, in itself or in the script's function it calls."""
    if path not in line:
        return False
    if COMPARISONS.search(line):
        return True
    for name in re.findall(r"(?<![\w-])([a-z_]\w*)\s", line):
        try:
            body = function_text(code, name)
        except StopIteration:
            continue
        if COMPARISONS.search(body):
            return True
    return False


def writes_path(line: str, path: str) -> bool:
    """Whether the line writes `path` with `install`, `cp`, `mv`, `tee` or a redirection."""
    return path in line and (
        re.search(r"(?<![\w-])(?:install|cp|mv|tee)\s", line) is not None
        or re.search(rf">\s*[\"']?{re.escape(path)}", line) is not None
    )


JOB_START = ROOT / "vm" / "job-start.sh"
JOB_STAND_INS = (
    "apt-get",
    "curl",
    "sha256sum",
    "install",
    "nft",
    "mount",
    "git",
    "python3",
    "uv",
    "podman",
)
JOB_INSTANCE = "night"
JOB_CODE_URL = "https://example.invalid/factory.git"
JOB_CODE_REF = "v9.9.9"
HIDDEN_TEXT = "s3cret-token-text"
MISSING_REF = "no-such-ref"
_STAND_IN = """
import json, os, sys
name = {name!r}
argv = sys.argv[1:]
checked = ""
if name == "sha256sum" and "-c" in argv:
    files = [word for word in argv if not word.startswith("-")]
    checked = sys.stdin.read() if not files else "".join(open(each).read() for each in files)
record = {{"name": name, "argv": argv, "env": dict(os.environ), "ppid": os.getppid(),
          "checked": checked}}
with open({log!r}, "a", encoding="utf-8") as file:
    file.write(json.dumps(record) + "\\n")
if name == "curl":
    for flag in ("-o", "--output"):
        if flag in argv:
            with open(argv[argv.index(flag) + 1], "w", encoding="utf-8") as out:
                out.write("a downloaded binary\\n")
if name == "git" and "clone" in argv:
    os.makedirs(argv[-1], exist_ok=True)
if name == "git" and any({missing!r} in word for word in argv):
    sys.exit(1)
if name == "python3" and argv[:2] == ["-m", "venv"]:
    os.makedirs(os.path.join(argv[-1], "bin"), exist_ok=True)
    for each in ("python", "python3", "pip"):
        os.symlink({tools_stand_in!r}, os.path.join(argv[-1], "bin", each))
    os.symlink({uv_stand_in!r}, os.path.join(argv[-1], "bin", "uv"))
if name == "uv" and "sync" in argv:
    os.makedirs({venv_bin!r}, exist_ok=True)
    for each, source in (("python", {python_stand_in!r}), ("factory-run", {run_stand_in!r})):
        os.symlink(source, os.path.join({venv_bin!r}, each))
if name == "factory-python" and "--once" not in argv and os.path.exists({fifo!r}):
    open({fifo!r}, "w").close()
if name == "factory-run" and os.path.exists({fifo!r}):
    open({fifo!r}).close()
if name in {failing!r} and (name != "factory-python" or "--once" in argv):
    sys.exit(1)
"""


class StandInCall(BaseModel):
    """One call of a stand-in: its name, its arguments, its environment, its parent's pid."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    argv: list[str]
    env: dict[str, str]
    ppid: int
    checked: str


class JobRun(BaseModel):
    """What a run of the job start script left: its result and the stand-ins' calls in order."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    result: ProcessResult
    calls: list[StandInCall]
    root: Path
    prefix: Path

    def named(self, name: str) -> list[StandInCall]:
        """The calls of the stand-in `name`, oldest first."""
        return [call for call in self.calls if call.name == name]


def _write_stand_in(path: Path, name: str, fields: dict[str, object]) -> Path:
    path.write_text(
        f"#!{sys.executable} -B\n" + _STAND_IN.format(name=name, **fields), encoding="utf-8"
    )
    path.chmod(0o755)
    return path


def run_job_start(
    tmp_path: Path,
    inputs: dict[str, str | None] | None = None,
    *,
    failing: frozenset[str] = frozenset(),
    background: bool = False,
) -> JobRun:
    """Run `vm/job-start.sh` with every required input, changed by `inputs` (`None` removes one).

    The stand-ins of `JOB_STAND_INS` lie first on `PATH`; `failing` names those that exit 1
    (`factory-python` fails only its `--once` call). With `background`, `factory-run` waits
    until the refresher started without `--once` has run.
    """
    root, prefix, stand_ins = tmp_path / "root", tmp_path / "prefix", tmp_path / "stand-ins"
    for folder in ("etc/apt/apt.conf.d", "usr/local/bin", "var/lib/containers"):
        (prefix / folder).mkdir(parents=True, exist_ok=True)
    stand_ins.mkdir()
    (tmp_path / "home").mkdir()
    token = tmp_path / "secrets" / "hosting-token"
    token.parent.mkdir()
    token.write_text(HIDDEN_TEXT + "\n", encoding="utf-8")
    fifo = tmp_path / "refresher-started"
    if background:
        os.mkfifo(fifo)
    fields: dict[str, object] = {
        "log": str(tmp_path / "calls.jsonl"),
        "missing": MISSING_REF,
        "failing": sorted(failing),
        "fifo": str(fifo),
        "venv_bin": str(root / "factory" / ".venv" / "bin"),
        "tools_stand_in": str(stand_ins / "tools-python"),
        "uv_stand_in": str(stand_ins / "uv"),
        "python_stand_in": str(stand_ins / "factory-python"),
        "run_stand_in": str(stand_ins / "factory-run"),
    }
    for name in (*JOB_STAND_INS, "tools-python", "factory-python", "factory-run"):
        _write_stand_in(stand_ins / name, name, fields)
    defaults: dict[str, str | None] = {
        "PATH": f"{stand_ins}:{SYSTEM_PATH}",
        "HOME": str(tmp_path / "home"),
        "FACTORY_INSTANCE": JOB_INSTANCE,
        "FACTORY_REPOSITORY_URL": "https://example.invalid/project.git",
        "FACTORY_CODE_URL": JOB_CODE_URL,
        "FACTORY_CODE_REF": JOB_CODE_REF,
        "FACTORY_TOKEN_FILE": str(token),
        "FACTORY_JOB_ROOT": str(root),
        "FACTORY_JOB_PREFIX": str(prefix),
    }
    environment = defaults | (inputs or {})
    result = run_process(
        ProcessRequest(
            argv=["sh", str(JOB_START)],
            cwd=tmp_path,
            env={name: value for name, value in environment.items() if value is not None},
            time_limit=ROOMY_LIMIT,
        )
    )
    log = tmp_path / "calls.jsonl"
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return JobRun(
        result=result,
        calls=[StandInCall.model_validate_json(line) for line in lines],
        root=root,
        prefix=prefix,
    )
