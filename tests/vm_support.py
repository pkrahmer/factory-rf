"""The machine's setup script and service unit: their paths, the steps and the script's texts."""

import re
from pathlib import Path

from dockerfile_support import _uncommented
from factory.adapters.process import ProcessRequest, ProcessResult, run_process

ROOT = Path(__file__).parent.parent
SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"
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
