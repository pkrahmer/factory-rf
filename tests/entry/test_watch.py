"""The watcher's command line: one evaluation and the board, read from the last fetch only."""

import io
import sys
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.application.board import BoardReader
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.pipeline_loading import PipelineLoader
from factory.application.tick import IdleHandler, Tick
from factory.application.watcher import Watcher
from factory.domain.board import render_board
from factory.domain.errors import GitError, PipelineDefinitionInvalid
from factory.domain.events import Event, EventKind
from factory.domain.git import GitOptions
from factory.domain.hosting import PullRequestComment, PullRequestView
from factory.domain.identifiers import branch_name
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemState
from factory.entry.watch import main, render_event, run_watch
from git_support import PIPELINE_YAML, TEST_IDENTITY, run_git
from human_clone import HumanClone
from source_search import SRC

INSTANCE = "factory-1"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"
BODY = "# First story\n"


class _CountingHosting(FakeHostingService):
    """The fake hosting service, recording every operation but the posting."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def create_pull_request(
        self, branch: str, title: str, body: str, *, draft: bool
    ) -> PullRequestView:
        self.calls.append("create_pull_request")
        return super().create_pull_request(branch, title, body, draft=draft)

    def find_open_pull_request(self, branch: str) -> PullRequestView | None:
        self.calls.append("find_open_pull_request")
        return super().find_open_pull_request(branch)

    def get_pull_request(self, number: int) -> PullRequestView:
        self.calls.append("get_pull_request")
        return super().get_pull_request(number)

    def list_comments(self, number: int) -> list[PullRequestComment]:
        self.calls.append("list_comments")
        return super().list_comments(number)

    def close(self, number: int) -> None:
        self.calls.append("close")
        super().close(number)

    def reopen(self, number: int) -> None:
        self.calls.append("reopen")
        super().reopen(number)

    def set_draft(self, number: int, draft: bool) -> None:
        self.calls.append("set_draft")
        super().set_draft(number, draft)

    def set_description(self, number: int, body: str) -> None:
        self.calls.append("set_description")
        super().set_description(number, body)

    def set_labels(self, number: int, labels: Sequence[str]) -> None:
        self.calls.append("set_labels")
        super().set_labels(number, labels)


pytestmark = pytest.mark.usefixtures("installed_agents")


def _definition(boundaries: Boundaries) -> PipelineDefinition:
    return boundaries.pipeline_reader.parse(PIPELINE_YAML)


def _push_state(human: HumanClone, state: WorkItemState) -> None:
    text = FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body=BODY))
    human.push_file(BRANCH, PATH, text)


def _waiting(boundaries: Boundaries, human: HumanClone) -> _CountingHosting:
    hosting = _CountingHosting()
    number = hosting.create_pull_request(BRANCH, "First story", "", draft=False).number
    human.start(BACKLOG_PATH)
    _push_state(human, WorkItemState(stage="approval", pull_request=number, handed_over="approval"))
    boundaries.git.fetch()
    hosting.calls.clear()
    return hosting


def _watch(boundaries: Boundaries) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    status = run_watch(boundaries, INSTANCE, out, err)
    return status, out.getvalue(), err.getvalue()


def _file_text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _idle_handlers(_definition: PipelineDefinition) -> Mapping[EventKind, Handler]:
    return {"idle": IdleHandler(), "run": IdleHandler()}


@pytest.mark.parametrize(
    ("detail", "line"),
    [("", "event: idle:-"), ("nothing to do", "event: idle:-  nothing to do")],
    ids=["without-detail", "with-detail"],
)
def test_an_event_is_written_as_its_key_and_its_detail(detail: str, line: str) -> None:
    event = Event(kind="idle", work_item=None, remote_state="a" * 40, detail=detail)

    assert render_event(event) == line


def test_run_watch_writes_the_event_a_blank_line_and_the_board(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.start(BACKLOG_PATH)
    boundaries.git.fetch()

    status, out, err = _watch(boundaries)

    definition = _definition(boundaries)
    event = Watcher(boundaries, INSTANCE).evaluate(definition)
    view = BoardReader(boundaries).read(definition)
    assert status == 0
    assert out == f"{render_event(event)}\n\n{render_board(view.features, view.rows)}"
    assert out.startswith(f"event: run:{WORK_ITEM}")
    assert err == ""


def test_run_watch_evaluates_once(boundaries: Boundaries, human: HumanClone) -> None:
    hosting = _waiting(boundaries, human)

    _watch(replace(boundaries, hosting=hosting))

    assert sorted(hosting.calls) == ["get_pull_request", "list_comments"]


def test_run_watch_writes_nothing(
    boundaries: Boundaries, human: HumanClone, checkout: GitCli, remote: Path, tmp_path: Path
) -> None:
    hosting = _waiting(boundaries, human)
    status_before = checkout.status()
    branches_before = run_git(remote, "for-each-ref")
    pulls_before = hosting.pull_requests()
    health, log = tmp_path / "state" / "health.json", tmp_path / "state" / "factory.log"
    health_before, log_before = _file_text(health), _file_text(log)

    _watch(replace(boundaries, hosting=hosting))

    assert checkout.status() == status_before
    assert run_git(remote, "for-each-ref") == branches_before
    assert hosting.pull_requests() == pulls_before
    for pull in hosting.pull_requests():
        assert hosting.factory_posts(pull.number) == []
        assert hosting.labels(pull.number) == []
    assert _file_text(health) == health_before
    assert _file_text(log) == log_before


def test_run_watch_fetches_nothing(
    boundaries: Boundaries, human: HumanClone, checkout: GitCli
) -> None:
    human.start(BACKLOG_PATH)
    _push_state(human, WorkItemState(stage="tests"))
    checkout.fetch()
    before = checkout.resolve(f"origin/{BRANCH}")
    _push_state(human, WorkItemState(stage="doing"))

    _, out, _ = _watch(boundaries)

    assert "  stage=tests  " in out
    assert "stage=doing" not in out
    assert checkout.resolve(f"origin/{BRANCH}") == before


def test_an_invalid_definition_is_reported_without_a_stop(
    boundaries: Boundaries, human: HumanClone, checkout: GitCli
) -> None:
    human.push_file("main", "factory/pipeline.yml", PIPELINE_YAML.replace('contract: "1.0"\n', ""))
    checkout.fetch()
    commit = checkout.resolve("origin/main")
    assert commit is not None
    with pytest.raises(PipelineDefinitionInvalid) as refused:
        PipelineLoader(boundaries).load(commit)

    status, out, err = _watch(boundaries)

    assert status == 1
    assert err == f"factory-watch: {refused.value.fault}\n"
    assert out == ""
    reasons = [stop.reason for stop in boundaries.health.read().stops]
    assert "pipeline_definition_invalid" not in reasons


def test_run_watch_without_origin_main_raises_git_error(
    boundaries: Boundaries, tmp_path: Path
) -> None:
    run_git(tmp_path, "init", "-q", "--bare", "--initial-branch=main", "empty.git")
    run_git(tmp_path, "clone", "-q", str(tmp_path / "empty.git"), "empty-clone")
    git = GitCli(tmp_path / "empty-clone", GitOptions(identity=TEST_IDENTITY))

    with pytest.raises(GitError):
        _watch(replace(boundaries, git=git))


def test_follow_is_an_unknown_option(
    boundaries: Boundaries, capsys: pytest.CaptureFixture[str]
) -> None:
    hosting = _CountingHosting()
    out = io.StringIO()

    with pytest.raises(SystemExit) as exited:
        main(
            ["--follow"],
            boundaries=replace(boundaries, hosting=hosting),
            instance=INSTANCE,
            out=out,
            err=io.StringIO(),
        )

    assert exited.value.code == 2
    assert "--follow" in capsys.readouterr().err
    assert out.getvalue() == ""
    assert hosting.calls == []


def test_the_console_script_refuses_follow_from_sys_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["factory-watch", "--follow"])

    with pytest.raises(SystemExit) as exited:
        main()

    assert exited.value.code == 2


def test_help_names_no_follow_mode(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exited:
        main(["--help"])

    assert exited.value.code == 0
    help_text = capsys.readouterr().out
    assert "usage: factory-watch" in help_text
    assert "follow" not in help_text


def test_no_tick_and_no_watch_run_writes_a_last_line_file(
    boundaries: Boundaries, human: HumanClone, tmp_path: Path
) -> None:
    human.start(BACKLOG_PATH)

    Tick(boundaries, INSTANCE, _idle_handlers).run()
    _watch(boundaries)

    assert list(tmp_path.rglob("factory-last-line")) == []


def _names_the_replaced_phrases(root: Path, path: Path) -> bool:
    # The document check's list of replaced phrases has to name them to reject them.
    return path == root / "domain" / "documents.py"


def _files_naming(root: Path, text: bytes) -> list[Path]:
    """The Python sources under `root` that hold `text`, the document check's list left out."""
    return [
        path
        for path in root.rglob("*.py")
        if path.is_file()
        and not _names_the_replaced_phrases(root, path)
        and text in path.read_bytes()
    ]


@pytest.mark.parametrize("text", [b"--follow", b"factory-last-line"])
def test_no_source_file_knows_the_follow_mode(text: bytes) -> None:
    assert _files_naming(SRC, text) == []


@pytest.mark.parametrize(
    ("name", "mode", "found"),
    [
        pytest.param("entry/run.py", 0o644, True, id="python-source"),
        pytest.param("domain/documents.py", 0o644, False, id="document-check"),
        pytest.param("domain/__pycache__/watch.cpython-312.pyc", 0o000, False, id="bytecode"),
        pytest.param("entry/notes.txt", 0o644, False, id="text-file"),
        pytest.param("entry/run.py.140000", 0o644, False, id="temporary-name"),
    ],
)
def test_the_follow_mode_scan_reads_only_python_sources(
    tmp_path: Path, name: str, mode: int, found: bool
) -> None:
    root = tmp_path / "src" / "factory"
    path = root / name
    path.parent.mkdir(parents=True)
    path.write_bytes(b'FLAG = "--follow"\n')
    path.chmod(mode)

    assert _files_naming(root, b"--follow") == ([path] if found else [])
