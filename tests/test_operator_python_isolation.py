"""The operator's scripts start Python isolated, so a `json.py` in the working folder never runs."""

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.process import ProcessResult
from operator_job_support import TAG, job_runner, make_job_repository
from operator_skill_support import PREFIX, make_operator, pull, status_routes
from operator_support import ROOT, SITE_EXAMPLE
from site_check_support import Machine, link_system

PLANTED = 'open(__file__.replace("json.py", "imported"), "w").close()\n'
SCRIPTS = ROOT / "operator" / "skill" / "kumpel" / "scripts"
FILES = [
    ROOT / "operator" / "bin" / "site",
    ROOT / "operator" / "job" / "job.sh",
    *(SCRIPTS / f"{name}.sh" for name in ("status", "settings", "approval", "comment", "merge")),
    SCRIPTS / "reset-to-tag.sh",
]
# `python3` as a command: at a line's start, or after a pipe, `$(`, `(`, `;` or `&&`.
PYTHON_COMMAND = re.compile(r"(?:^\s*|[|(;&]\s*)python3\b(?P<rest>.*)")

Run = Callable[[Path], ProcessResult]


def settings_show(root: Path) -> ProcessResult:
    return make_operator(root).run("settings.sh", "show")


def settings_init(root: Path) -> ProcessResult:
    return make_operator(root).run("settings.sh", "init")


def status(root: Path) -> ProcessResult:
    operator = make_operator(root)
    operator.answer(
        status_routes([pull(7, "work-item/F0001-S0001", ["stage:doing"])], {7: ["Hi."]})
    )
    return operator.run("status.sh")


def comment(root: Path) -> ProcessResult:
    operator = make_operator(root)
    operator.answer({f"{PREFIX}/issues/7/comments": {"id": 1}})
    text = root / "text.md"
    text.write_text("A comment.\n", encoding="utf-8")
    return operator.run("comment.sh", "7", str(text))


def site_check(root: Path) -> ProcessResult:
    system = root / "system"
    system.mkdir()
    return Machine(root, link_system(system)).run()


def job_dry_run(root: Path) -> ProcessResult:
    lines = SITE_EXAMPLE.read_text(encoding="utf-8").splitlines()
    pairs = (line.partition("=") for line in lines if line.startswith("SITE_"))
    values = {key: value for key, _, value in pairs}
    run = job_runner(root, make_job_repository(root / "repo"), root / "gcloud.jsonl")
    return run(["create", "--dry-run"], values, SITE_CODE_REF=TAG)


@pytest.mark.parametrize(
    "run",
    [
        pytest.param(settings_show, id="settings-show"),
        pytest.param(settings_init, id="settings-init"),
        pytest.param(status, id="status"),
        pytest.param(comment, id="comment"),
        pytest.param(site_check, id="site-check"),
        pytest.param(job_dry_run, id="job-create-dry-run"),
    ],
)
def test_a_json_module_in_the_working_folder_is_never_imported(tmp_path: Path, run: Run) -> None:
    plain, planted = tmp_path / "plain", tmp_path / "planted"
    plain.mkdir()
    planted.mkdir()
    (planted / "json.py").write_text(PLANTED, encoding="utf-8")

    expected = run(plain)
    result = run(planted)

    assert not (planted / "imported").exists()
    assert result.exit_status == expected.exit_status, result.stderr
    assert result.stdout.replace(str(planted), "<root>") == expected.stdout.replace(
        str(plain), "<root>"
    )


@pytest.mark.parametrize("path", [pytest.param(path, id=path.name) for path in FILES])
def test_every_python_start_passes_isolated_mode_first(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [
        match.group("rest")
        for line in lines
        if not line.lstrip().startswith("#") and (match := PYTHON_COMMAND.search(line))
    ]

    assert starts
    assert [rest for rest in starts if not rest.startswith(" -I ")] == []
