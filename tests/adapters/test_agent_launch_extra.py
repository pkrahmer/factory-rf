"""The agent's container gets the operator's extra names and CA bundle, in both runtimes."""

from pathlib import Path

import pytest

from adapters.container_runtime_support import container_environment
from container_extra_support import (
    OTHER,
    PROXY,
    agent_words,
    env_words,
    volume,
    write_bundle,
)
from factory.adapters.agent_launch import API_LOGIN_VARIABLE
from factory.domain.containers import CA_BUNDLE_NAMES, extra_environment
from factory.domain.settings import InstanceSettings
from settings_support import AGENT_HOME


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
@pytest.mark.parametrize(
    ("with_bundle", "listed_path"),
    [
        pytest.param(False, False, id="names"),
        pytest.param(True, False, id="bundle"),
        pytest.param(False, True, id="path-stays-the-request-s"),
    ],
)
def test_the_agent_s_container_holds_the_listed_names_and_the_bundle(
    tmp_path: Path, runtime: str, *, with_bundle: bool, listed_path: bool
) -> None:
    bundle = write_bundle(tmp_path) if with_bundle else None
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        agent_home=AGENT_HOME,
        container_env=("HTTPS_PROXY", "PATH") if listed_path else ("HTTPS_PROXY",),
        ca_bundle=bundle,
    )
    extra = extra_environment(settings, {"HTTPS_PROXY": PROXY, "PATH": "/host/bin", OTHER: "x"})

    words = agent_words(
        tmp_path,
        runtime,
        extra=extra,
        bundle=bundle,
        request_environment={API_LOGIN_VARIABLE: "request-key"},
    )

    environment = env_words(words)
    assert environment["HTTPS_PROXY"] == PROXY
    assert OTHER not in environment
    assert API_LOGIN_VARIABLE not in environment
    assert environment["PATH"] == container_environment(tmp_path / "bin")["PATH"]
    if bundle is None:
        assert not any(name in environment for name in CA_BUNDLE_NAMES)
        return
    assert volume(bundle) in words
    assert words[words.index(volume(bundle)) - 1] == "--volume"
    assert {name: environment[name] for name in CA_BUNDLE_NAMES} == dict.fromkeys(
        CA_BUNDLE_NAMES, str(bundle)
    )
