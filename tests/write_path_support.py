"""Shared helpers of the write-path service tests: a stage start and a pushed definition."""

from datetime import UTC, datetime

from factory.adapters.git_cli import GitCli
from factory.application.claims import StageStart
from factory.domain.work_item import Claim
from human_clone import HumanClone

PIPELINE_FILE = "factory/pipeline.yml"


def stage_start(checkout: GitCli, stage: str) -> StageStart:
    """A claim of `stage` whose stage-start commit is the checkout's `origin/main`."""
    commit = checkout.resolve("origin/main")
    assert commit is not None
    claim = Claim(
        instance="factory-1",
        stage=stage,
        started_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
        lease_duration=30,
    )
    return StageStart(commit=commit, claim=claim)


def push_definition(human: HumanClone, checkout: GitCli, text: str) -> None:
    """Push `text` as the pipeline definition on `main` and fetch it into the checkout."""
    human.push_file("main", PIPELINE_FILE, text)
    checkout.fetch()
