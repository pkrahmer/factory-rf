"""The documents command reports the names, paths and links its documents name that do not exist."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.shared.domain.documents import (
    DECISION_LOG,
    OPERATOR_INSTALL,
    PROJECT_GUIDE,
    README,
)
from support.check_documents_support import REPORT_HEADING, line_of
from support.document_texts import (
    clean_texts,
    decision_log,
    operator_file,
    operator_install,
    project_guide,
    readme,
    write_documents,
)

FINDING_END = " does not exist"
SCRIPT = "operator/vm/setup.sh"
OPERATOR_TOPIC = "docs/operator-guide/machine.md"


def _name_findings(output: str) -> list[str]:
    return [line for line in output.splitlines() if line.endswith(FINDING_END)]


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    """A temporary checkout with clean documents and one script under `operator/`."""
    root = tmp_path / "checkout"
    script = root / SCRIPT
    script.parent.mkdir(parents=True)
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    return root


def _finding(planted: str, name: str) -> list[str]:
    line = line_of(project_guide(suffix=planted), planted)
    return [f"{PROJECT_GUIDE}:{line}: {name}{FINDING_END}"]


@pytest.mark.parametrize(
    ("planted", "expected"),
    [
        pytest.param(
            "`factory.shared.domain.nothing_here`",
            _finding("`factory.shared.domain.nothing_here`", "factory.shared.domain.nothing_here"),
            id="missing-module",
        ),
        pytest.param(
            "`factory.shared.domain.documents.nothing_here`",
            _finding(
                "`factory.shared.domain.documents.nothing_here`",
                "factory.shared.domain.documents.nothing_here",
            ),
            id="missing-attribute",
        ),
        pytest.param(
            "`operator/vm/nothing.sh`",
            _finding("`operator/vm/nothing.sh`", "operator/vm/nothing.sh"),
            id="missing-path",
        ),
        pytest.param(
            "`operator/nothing_here/`",
            _finding("`operator/nothing_here/`", "operator/nothing_here/"),
            id="missing-top-level-path-without-extension",
        ),
        pytest.param(
            "[x](../../src/factory/nothing.py)",
            _finding("[x](../../src/factory/nothing.py)", "src/factory/nothing.py"),
            id="missing-link",
        ),
        pytest.param(
            "[x](a.md#h)",
            _finding("[x](a.md#h)", "docs/project-guide/a.md"),
            id="missing-link-with-fragment",
        ),
        pytest.param(
            "[x](../README.md)",
            _finding("[x](../README.md)", "docs/README.md"),
            id="link-resolved-from-folder-missing",
        ),
        pytest.param("`factory.shared.domain.documents`", [], id="existing-module"),
        pytest.param(
            "`factory.shared.domain.documents.named_references`", [], id="existing-attribute"
        ),
        pytest.param(f"`{SCRIPT}`", [], id="existing-path"),
        pytest.param(f"[x](../../{SCRIPT})", [], id="link-resolved-from-folder"),
        pytest.param(
            "[x](../operator-guide/install.md#install)", [], id="existing-link-with-fragment"
        ),
        pytest.param("[x](https://example.org/a.md)", [], id="web-address"),
        pytest.param("[x](#a-heading)", [], id="heading-alone"),
    ],
)
def test_each_missing_name_path_or_link_target_gets_one_finding(
    checkout: Path, capsys: pytest.CaptureFixture[str], planted: str, expected: list[str]
) -> None:
    texts = clean_texts()
    texts[PROJECT_GUIDE] = project_guide(suffix=planted)
    write_documents(checkout, texts)

    main(["--root", str(checkout)])

    assert _name_findings(capsys.readouterr().out) == expected


MISSING = "`factory.nothing_here`"
STILL_MISSING = "`factory.still_missing`"
AFTER_REPLACED = f"## Replaced in v1.2\n\n{MISSING}\n\n## Later\n\n{STILL_MISSING}"


def _in_decision_log(root: Path, texts: dict[str, str | None]) -> None:
    del root
    texts[DECISION_LOG] = decision_log(suffix=MISSING)


def _in_runs(root: Path, texts: dict[str, str | None]) -> None:
    del texts
    run = root / "docs" / "runs" / "a-run.md"
    run.parent.mkdir(parents=True)
    run.write_text(f"# A run\n\n{MISSING}\n", encoding="utf-8")


def _in_guide(suffix: str) -> Callable[[Path, dict[str, str | None]], None]:
    def plant(root: Path, texts: dict[str, str | None]) -> None:
        del root
        texts[PROJECT_GUIDE] = project_guide(suffix=suffix)

    return plant


@pytest.mark.parametrize(
    ("plant", "expected"),
    [
        pytest.param(_in_decision_log, [], id="decision-log"),
        pytest.param(_in_runs, [], id="runs"),
        pytest.param(_in_guide(f"## Replaced from v1\n\n{MISSING}"), [], id="replaced-from-v1"),
        pytest.param(_in_guide(f"## Replaced in v1.2\n\n{MISSING}"), [], id="replaced-in-v1.2"),
        pytest.param(
            _in_guide(AFTER_REPLACED),
            [
                f"{PROJECT_GUIDE}:{line_of(project_guide(suffix=AFTER_REPLACED), STILL_MISSING)}: "
                f"factory.still_missing{FINDING_END}"
            ],
            id="after-the-replaced-section",
        ),
    ],
)
def test_the_decision_log_runs_and_replaced_sections_are_not_checked(
    checkout: Path,
    capsys: pytest.CaptureFixture[str],
    plant: Callable[[Path, dict[str, str | None]], None],
    expected: list[str],
) -> None:
    texts = clean_texts()
    plant(checkout, texts)
    write_documents(checkout, texts)

    main(["--root", str(checkout)])

    assert _name_findings(capsys.readouterr().out) == expected


README_NAME = "`factory.readme_missing`"
OPERATOR_NAME = "`factory.operator_missing`"
GUIDE_NAME = "`factory.guide_missing`"
INSTALL_FINDING = f"{OPERATOR_INSTALL}: section 'Install' is missing"


@pytest.mark.parametrize(
    ("today", "exit_status"),
    [
        pytest.param(None, 0, id="no-finding-today"),
        pytest.param(INSTALL_FINDING, 1, id="one-today"),
    ],
)
def test_name_findings_follow_todays_findings_and_leave_the_exit_status(
    checkout: Path, capsys: pytest.CaptureFixture[str], today: str | None, exit_status: int
) -> None:
    texts = clean_texts()
    planted = {
        README: (readme(suffix=README_NAME), README_NAME),
        OPERATOR_TOPIC: (operator_file(OPERATOR_TOPIC, suffix=OPERATOR_NAME), OPERATOR_NAME),
        PROJECT_GUIDE: (project_guide(suffix=GUIDE_NAME), GUIDE_NAME),
    }
    for path, (text, _) in planted.items():
        texts[path] = text
    if today is not None:
        texts[OPERATOR_INSTALL] = operator_install(sections=["Configuration"])
    write_documents(checkout, texts)

    status = main(["--root", str(checkout)])

    lines = capsys.readouterr().out.splitlines()
    findings = _name_findings("\n".join(lines))
    assert sorted(findings) == sorted(
        f"{path}:{line_of(text, name)}: {name.strip('`')}{FINDING_END}"
        for path, (text, name) in planted.items()
    )
    assert status == exit_status
    if today is not None:
        assert lines[: len(lines) - len(findings)] == [today, REPORT_HEADING]
