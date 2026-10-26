"""The factory's one default git identity: its value, its one home and its overrides."""

from factory.domain import git, settings
from factory.domain.git import DEFAULT_GIT_IDENTITY, GitIdentity, GitOptions
from factory.domain.settings import read_settings
from settings_support import BASE
from source_search import modules, string_literals

DEFAULT_EMAIL = "factory@noreply.invalid"


def test_the_default_identity_is_factory_at_noreply_invalid() -> None:
    assert GitIdentity(name="factory", email=DEFAULT_EMAIL) == DEFAULT_GIT_IDENTITY


def test_git_options_and_settings_share_the_one_default_identity() -> None:
    assert GitOptions().identity is git.DEFAULT_GIT_IDENTITY
    assert settings.DEFAULT_GIT_IDENTITY is git.DEFAULT_GIT_IDENTITY


def test_the_default_email_is_written_once_in_src_in_the_git_domain_module() -> None:
    holders = [
        name
        for name, tree in modules().items()
        for literal in string_literals(tree)
        if literal == DEFAULT_EMAIL
    ]
    assert holders == ["factory.domain.git"]


def test_read_settings_defaults_the_identity_and_overrides_each_half_alone() -> None:
    assert read_settings(BASE).git_identity == DEFAULT_GIT_IDENTITY
    named = read_settings({**BASE, "GIT_USER_NAME": "Ann"})
    assert named.git_identity == GitIdentity(name="Ann", email=DEFAULT_EMAIL)
