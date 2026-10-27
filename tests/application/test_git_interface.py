"""The git interface: exactly the operations the factory needs, all of them on `GitCli`."""

import inspect

from factory.adapters.git_cli import GitCli
from factory.application.git import Git
from git_interface_support import OPERATIONS


def test_git_has_exactly_the_twenty_one_operations_and_git_cli_has_each() -> None:
    public = {name for name, _ in inspect.getmembers(Git, callable) if not name.startswith("_")}

    assert public == OPERATIONS
    assert [name for name in sorted(OPERATIONS) if not hasattr(GitCli, name)] == []
