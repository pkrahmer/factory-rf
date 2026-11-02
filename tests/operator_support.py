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


# A stand-in for curl: it records its arguments and its standard input, reads its configuration
# the way curl does (url, request, header, data, output, write-out) and answers as the
# environment says, or, when `STAND_IN_CURL_ROUTES` names a JSON file, with that file's body for
# the URL's path and query (else its path alone) and 404 for any other; a failed transfer writes
# `000` as its status, as curl does.
CURL_STAND_IN = r"""
import json, os, re, sys

QUOTED = {"\\": "\\", '"': '"', "n": "\n", "r": "\r", "t": "\t", "v": "\v"}


def unquote(text):
    if not text.startswith('"'):
        return text.split()[0] if text.split() else ""
    out, index = [], 1
    while index < len(text) and text[index] != '"':
        if text[index] == "\\" and index + 1 < len(text):
            index += 1
            out.append(QUOTED.get(text[index], text[index]))
        else:
            out.append(text[index])
        index += 1
    return "".join(out)


def config_options(text):
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"-{0,2}([A-Za-z0-9-]+)\s*[=:]?\s*(.*)$", line)
        if match:
            yield match.group(1), unquote(match.group(2))


arguments = sys.argv[1:]
standard_input = ""
options = []
index = 0
while index < len(arguments):
    name = arguments[index].lstrip("-")
    if name in ("silent", "s", "show-error", "S"):
        index += 1
        continue
    value = arguments[index + 1] if index + 1 < len(arguments) else ""
    if name in ("config", "K") and value == "-":
        standard_input = sys.stdin.read()
        options.extend(config_options(standard_input))
    else:
        options.append((name, value))
    index += 2

with open(os.environ["STAND_IN_RECORD"], "a", encoding="utf-8") as record:
    record.write(json.dumps({"argv": arguments, "stdin": standard_input}) + "\n")

exit_status = int(os.environ.get("STAND_IN_CURL_EXIT", "0"))
status = os.environ.get("STAND_IN_CURL_STATUS", "200") if exit_status == 0 else "000"
body = os.environ.get("STAND_IN_CURL_BODY", "") if exit_status == 0 else ""
routes_file = os.environ.get("STAND_IN_CURL_ROUTES")
if routes_file and exit_status == 0:
    with open(routes_file, encoding="utf-8") as source:
        routes = json.load(source)
    url = next((value for name, value in options if name == "url"), "")
    route = re.sub(r"^[a-z]+://[^/]*", "", url)
    answer = routes.get(route, routes.get(route.split("?")[0]))
    status, body = ("200", answer) if answer is not None else ("404", '{"message": "Not Found"}')
output_file = next((value for name, value in options if name in ("output", "o")), None)
write_out = next((value for name, value in options if name in ("write-out", "w")), None)

if output_file and output_file != "-":
    with open(output_file, "w", encoding="utf-8") as output:
        output.write(body)
else:
    sys.stdout.write(body)
    sys.stdout.flush()

sys.stderr.write(os.environ.get("STAND_IN_CURL_ERROR", ""))
sys.stderr.flush()

if write_out is not None:
    if write_out.startswith("@"):
        with open(write_out[1:], encoding="utf-8") as source:
            write_out = source.read()
    for escape, character in (("\\n", "\n"), ("\\r", "\r"), ("\\t", "\t")):
        write_out = write_out.replace(escape, character)
    target = sys.stdout
    for part in re.split(r"(%output\{[^}]*\}|%\{[a-z_]+\})", write_out):
        if part.startswith("%output{"):
            path = part[len("%output{") : -1]
            mode = "a" if path.startswith(">>") else "w"
            target = open(path.removeprefix(">>"), mode, encoding="utf-8")
        elif part in ("%{http_code}", "%{response_code}"):
            target.write(status)
        elif part == "%{stdout}":
            target = sys.stdout
        elif part == "%{stderr}":
            target = sys.stderr
        else:
            target.write(part)
        target.flush()
sys.exit(exit_status)
"""


def hosting_env(
    tmp_path: Path, site_file: Path, records: Path, temporary: Path, bin_folder: Path, **values: str
) -> dict[str, str]:
    """The environment of a run: the stand-ins first on the `PATH`, no `gh` of the machine."""
    system_path = [
        entry for entry in os.environ["PATH"].split(os.pathsep) if not (Path(entry) / "gh").exists()
    ]
    return {
        **operator_environment(tmp_path),
        "PATH": os.pathsep.join([str(bin_folder), *system_path]),
        "FACTORY_SITE": str(site_file),
        "TMPDIR": str(temporary),
        "GIT_CONFIG_NOSYSTEM": "1",
        "STAND_IN_RECORD": str(records / "curl.jsonl"),
        "STAND_IN_GH_RECORD": str(records / "gh.jsonl"),
        **values,
    }
