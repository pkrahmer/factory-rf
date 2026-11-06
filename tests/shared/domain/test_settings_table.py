"""The table of the settings names every variable `read_settings` reads, once, with its default."""

from collections.abc import Callable, Iterator, Mapping
from datetime import timedelta
from pathlib import Path

import pytest

from factory.shared.domain.settings import SETTINGS, InstanceSettings, read_settings
from support.settings_support import BASE


class _RecordingEnviron(Mapping[str, str]):
    """An environment that notes every key looked up in it."""

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = dict(values)
        self.looked_up: set[str] = set()

    def __getitem__(self, key: str) -> str:
        self.looked_up.add(key)
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)


def _image_id(_path: Path) -> str:
    return "sha256:" + "a" * 64


def test_settings_table_names_what_read_settings_reads() -> None:
    environ = _RecordingEnviron({**BASE, "FACTORY_IMAGE_ID_FILE": "/srv/factory/image-id"})

    read_settings(environ, _image_id)

    names = [setting.name for setting in SETTINGS]
    assert len(names) == len(set(names))
    assert set(names) == environ.looked_up


_Applied = Callable[[InstanceSettings], object]


def _minutes(duration: timedelta) -> str:
    return str(int(duration.total_seconds()) // 60)


@pytest.mark.parametrize(
    ("name", "default", "applied"),
    [
        pytest.param("FACTORY_REPOSITORY_URL", None, None, id="repository-url"),
        pytest.param("FACTORY_INSTANCE", None, None, id="instance"),
        pytest.param("FACTORY_CHECKOUT", "/work/checkout", lambda s: s.checkout, id="checkout"),
        pytest.param("FACTORY_STATE", "/state", lambda s: s.state_directory, id="state"),
        pytest.param("GIT_USER_NAME", "factory", lambda s: s.git_identity.name, id="git-name"),
        pytest.param(
            "GIT_USER_EMAIL",
            "factory@noreply.invalid",
            lambda s: s.git_identity.email,
            id="git-email",
        ),
        pytest.param("FACTORY_IMAGE_ID_FILE", None, None, id="image-id-file"),
        pytest.param("FACTORY_CLAUDE_HOME", None, None, id="claude-home"),
        pytest.param("FACTORY_CLAUDE", "claude", lambda s: s.claude_executable, id="claude"),
        pytest.param("FACTORY_CLAUDE_VERSION", None, None, id="claude-version"),
        pytest.param("FACTORY_TOKEN_FILE", None, None, id="token-file"),
        pytest.param("FACTORY_CLAUDE_LOGIN_FILE", None, None, id="claude-login-file"),
        pytest.param("FACTORY_API_LOGIN_FILE", None, None, id="api-login-file"),
        pytest.param("FACTORY_MIN_FREE_GB", "5", lambda s: s.min_free_gb, id="min-free-gb"),
        pytest.param(
            "FACTORY_PROVIDER_LIMIT_STATUS",
            "428",
            lambda s: s.provider_limit.status,
            id="limit-status",
        ),
        pytest.param("FACTORY_PROVIDER_LIMIT_MESSAGE", None, None, id="limit-message"),
        pytest.param(
            "FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES",
            "10",
            lambda s: _minutes(s.provider_limit.cooldown),
            id="limit-cooldown",
        ),
        pytest.param(
            "FACTORY_PROVIDER_LIMIT_CEILING_MINUTES",
            "120",
            lambda s: _minutes(s.provider_limit.ceiling),
            id="limit-ceiling",
        ),
        pytest.param("FACTORY_AGENT_RUNTIME", "claude", lambda s: s.agent_runtime, id="runtime"),
        pytest.param(
            "FACTORY_OPENCODE", "opencode", lambda s: s.opencode_executable, id="opencode"
        ),
        pytest.param("FACTORY_OPENCODE_VERSION", None, None, id="opencode-version"),
        pytest.param("FACTORY_OPENCODE_MODELS", None, None, id="opencode-models"),
        pytest.param("FACTORY_OPENCODE_PROVIDER_FILE", None, None, id="opencode-provider-file"),
        pytest.param("FACTORY_DATASET", None, None, id="dataset"),
        pytest.param("FACTORY_WORKSPACE", None, None, id="workspace"),
        pytest.param("FACTORY_SNAPSHOTS", "zfs", lambda s: s.snapshots, id="snapshots"),
        pytest.param("FACTORY_SNAPSHOT_BASE", None, None, id="snapshot-base"),
        pytest.param("FACTORY_STAGE_IMAGE", None, None, id="stage-image"),
        pytest.param("FACTORY_PODMAN", "podman", lambda s: s.podman_executable, id="podman"),
        pytest.param(
            "FACTORY_CONTAINER_PROFILE",
            "rootless",
            lambda s: s.container_profile,
            id="container-profile",
        ),
        pytest.param("FACTORY_ZFS", "zfs", lambda s: s.zfs_executable, id="zfs"),
        pytest.param("FACTORY_CONTAINER_ENV", None, None, id="container-env"),
        pytest.param("FACTORY_CA_BUNDLE", None, None, id="ca-bundle"),
        pytest.param(
            "FACTORY_IDLE_SHUTDOWN_MINUTES",
            "0",
            lambda s: s.idle_shutdown_minutes,
            id="idle-shutdown-minutes",
        ),
        pytest.param(
            "FACTORY_IDLE_SHUTDOWN_ACTION",
            "poweroff",
            lambda s: s.idle_shutdown_action,
            id="idle-shutdown-action",
        ),
        pytest.param("FACTORY_TRANSCRIPT_DIR", None, None, id="transcript-dir"),
    ],
)
def test_settings_table_holds_the_default_read_settings_applies(
    name: str, default: str | None, applied: _Applied | None
) -> None:
    documented = {setting.name: setting.default for setting in SETTINGS}

    assert name in documented
    assert documented[name] == default
    if applied is not None:
        assert name not in BASE
        assert str(applied(read_settings(BASE))) == default
