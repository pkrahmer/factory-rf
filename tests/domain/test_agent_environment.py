"""The agent run's environment: an allow list of names, everything else dropped."""

import pytest

from factory.domain.agent_runs import ALLOWED_ENVIRONMENT_NAMES, scrub_environment

ALLOWED = {
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "HOME": "/home/factory",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "TERM": "xterm",
    "TZ": "UTC",
}


def test_the_allowed_names_are_kept_with_their_values_in_a_new_dict() -> None:
    source = dict(ALLOWED)

    scrubbed = scrub_environment(source)

    assert frozenset({"PATH", "HOME", "LANG", "LC_ALL", "TERM", "TZ"}) == ALLOWED_ENVIRONMENT_NAMES
    assert scrubbed == ALLOWED
    assert scrubbed is not source
    assert source == ALLOWED


@pytest.mark.parametrize(
    "name",
    [
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "FACTORY_TOKEN_FILE",
        "GIT_ASKPASS",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_COUNT",
        "SSH_AUTH_SOCK",
        "ANTHROPIC_API_KEY",
        "MY_OWN_VARIABLE",
        "path",
    ],
)
def test_a_name_outside_the_allow_list_is_dropped(name: str) -> None:
    scrubbed = scrub_environment({"PATH": "/usr/bin", name: "example-value"})

    assert scrubbed == {"PATH": "/usr/bin"}
