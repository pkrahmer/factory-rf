"""The environment the operator's settings add to every container."""

from pathlib import Path

import pytest

from factory.domain.containers import extra_environment
from factory.domain.settings import InstanceSettings

_PROXY = "http://proxy.example.invalid:3128"
_BUNDLE = "/etc/ca.pem"


def _settings(container_env: tuple[str, ...], ca_bundle: Path | None) -> InstanceSettings:
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        container_env=container_env,
        ca_bundle=ca_bundle,
    )


@pytest.mark.parametrize(
    ("container_env", "ca_bundle", "source", "expected"),
    [
        pytest.param((), None, {"HTTPS_PROXY": _PROXY}, [], id="nothing-set"),
        pytest.param(
            ("NO_PROXY", "HTTPS_PROXY"),
            None,
            {"HTTPS_PROXY": _PROXY, "NO_PROXY": "localhost", "OTHER": "x"},
            [("NO_PROXY", "localhost"), ("HTTPS_PROXY", _PROXY)],
            id="listed-in-order",
        ),
        pytest.param(
            ("HTTPS_PROXY", "MISSING"),
            None,
            {"HTTPS_PROXY": _PROXY},
            [("HTTPS_PROXY", _PROXY)],
            id="missing-skipped",
        ),
        pytest.param(
            (),
            Path(_BUNDLE),
            {},
            [
                ("NODE_EXTRA_CA_CERTS", _BUNDLE),
                ("SSL_CERT_FILE", _BUNDLE),
                ("REQUESTS_CA_BUNDLE", _BUNDLE),
            ],
            id="bundle",
        ),
        pytest.param(
            ("SSL_CERT_FILE",),
            Path(_BUNDLE),
            {"SSL_CERT_FILE": "/host/certs.pem"},
            [
                ("SSL_CERT_FILE", _BUNDLE),
                ("NODE_EXTRA_CA_CERTS", _BUNDLE),
                ("REQUESTS_CA_BUNDLE", _BUNDLE),
            ],
            id="bundle-wins-over-listed-name",
        ),
    ],
)
def test_the_extra_environment_holds_the_listed_names_and_the_bundle(
    container_env: tuple[str, ...],
    ca_bundle: Path | None,
    source: dict[str, str],
    expected: list[tuple[str, str]],
) -> None:
    extra = extra_environment(_settings(container_env, ca_bundle), source)

    assert dict(extra) == dict(expected)
    listed = [name for name in extra if name in container_env]
    assert listed == [name for name in container_env if name in extra]
