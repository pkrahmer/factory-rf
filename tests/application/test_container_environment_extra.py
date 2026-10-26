"""The sync container gets the operator's extras; with neither setting no container changes."""

from collections.abc import Callable
from pathlib import Path

import pytest

from container_extra_support import (
    CA_NAMES,
    PROXY,
    agent_words,
    check_words,
    env_words,
    sync_words,
    volume,
    without_pairs,
    write_bundle,
)
from container_support import Dataset
from factory.adapters.claude_runtime import SWITCHES
from factory.adapters.make_commands import CHECK_ENVIRONMENT
from factory.application.stage_environment import SYNC_ENVIRONMENT
from factory.domain.containers import WORK_HOME, extra_environment
from factory.domain.settings import InstanceSettings

NEITHER = InstanceSettings(repository_url="/srv/project.git", instance="factory-1")
HOST = {"HTTPS_PROXY": PROXY, "PATH": "/host/bin"}

Words = Callable[[Dataset, Path, dict[str, str]], list[str]]


def _agent(_dataset: Dataset, tmp_path: Path, extra: dict[str, str]) -> list[str]:
    return agent_words(tmp_path / "agent", "claude", extra=extra, bundle=None)


def _sync(dataset: Dataset, _tmp_path: Path, extra: dict[str, str]) -> list[str]:
    return sync_words(dataset, extra=extra, bundle=None)


def _check(dataset: Dataset, _tmp_path: Path, extra: dict[str, str]) -> list[str]:
    return check_words(dataset, extra=extra, bundle=None)


def _agent_today(tmp_path: Path) -> dict[str, str]:
    stand_in_bin = tmp_path / "agent" / "bin"
    return {
        "HOME": WORK_HOME,
        "LANG": "C.UTF-8",
        "PATH": f"{stand_in_bin}:/usr/bin:/bin",
        **SWITCHES,
    }


@pytest.mark.parametrize(
    ("words_of", "today"),
    [
        pytest.param(_agent, _agent_today, id="agent"),
        pytest.param(_sync, lambda _: SYNC_ENVIRONMENT, id="sync"),
        pytest.param(_check, lambda _: CHECK_ENVIRONMENT, id="check"),
    ],
)
def test_with_neither_setting_the_containers_are_those_of_today(
    dataset: Dataset,
    tmp_path: Path,
    words_of: Words,
    today: Callable[[Path], dict[str, str]],
) -> None:
    extra = extra_environment(NEITHER, HOST)

    words = words_of(dataset, tmp_path, extra)

    assert extra == {}
    assert env_words(words) == today(tmp_path)
    assert not any(word.endswith(".pem:ro") for word in words)


@pytest.fixture
def bundle(tmp_path: Path) -> Path:
    """The operator's CA bundle file."""
    return write_bundle(tmp_path)


SyncOrCheck = Callable[..., list[str]]


@pytest.mark.parametrize(
    ("words_of", "constants"),
    [
        pytest.param(sync_words, SYNC_ENVIRONMENT, id="sync"),
        pytest.param(check_words, CHECK_ENVIRONMENT, id="check"),
    ],
)
@pytest.mark.parametrize(
    ("container_env", "with_bundle", "added"),
    [
        pytest.param(("HTTPS_PROXY",), False, {"HTTPS_PROXY": PROXY}, id="listed-name"),
        pytest.param((), True, None, id="bundle"),
        pytest.param(("PATH",), False, {}, id="path-stays-the-constant"),
    ],
)
def test_the_sync_and_check_containers_hold_the_extras_and_the_bundle(
    dataset: Dataset,
    bundle: Path,
    *,
    words_of: SyncOrCheck,
    constants: dict[str, str],
    container_env: tuple[str, ...],
    added: dict[str, str] | None,
    with_bundle: bool,
) -> None:
    settings = NEITHER.model_copy(
        update={"container_env": container_env, "ca_bundle": bundle if with_bundle else None}
    )
    extra = extra_environment(settings, HOST)
    expected = dict(added) if added is not None else dict.fromkeys(CA_NAMES, str(bundle))
    today = words_of(dataset, extra={}, bundle=None)

    words = words_of(dataset, extra=extra, bundle=settings.ca_bundle)

    assert env_words(words) == {**constants, **expected}
    assert env_words(words)["PATH"] == constants["PATH"]
    pairs = {f"{name}={value}" for name, value in expected.items()}
    stripped = without_pairs(words, "--env", pairs)
    if with_bundle:
        assert volume(bundle) in words
        stripped = without_pairs(stripped, "--volume", {volume(bundle)})
    else:
        assert volume(bundle) not in words
    assert stripped == today
