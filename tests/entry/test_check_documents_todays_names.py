"""The documents command finds no missing name in today's log file and git addresses."""

import pytest

from factory.entry.check_documents import main
from support.operator_support import ROOT


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("factory.log", id="log-file"),
        pytest.param("git@github.com:owner/project.git", id="git-address-install"),
        pytest.param("git@host:owner/name.git", id="git-address-cloud-run"),
    ],
)
def test_todays_documents_give_no_finding_for_the_log_file_and_git_addresses(
    capsys: pytest.CaptureFixture[str], text: str
) -> None:
    main(["--root", str(ROOT)])

    lines = capsys.readouterr().out.splitlines()
    assert [line for line in lines if text in line] == []
