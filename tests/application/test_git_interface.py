"""The git interface: exactly the operations the factory needs, all of them on `GitCli`."""

import inspect

from factory.adapters.git_cli import GitCli
from factory.application.git import Git

OPERATIONS = {
    "fetch",
    "remote_branches",
    "resolve",
    "show_file",
    "list_files",
    "is_ancestor",
    "log",
    "changed_paths",
    "status",
    "clone",
    "checkout",
    "commit",
    "push",
    "delete_remote_branch",
    "delete_branch",
    "merge",
    "reset_to",
    "revert_paths",
    "move",
    "work_tree_id",
    "ignored",
}


def test_git_has_exactly_the_twenty_one_operations_and_git_cli_has_each() -> None:
    public = {name for name, _ in inspect.getmembers(Git, callable) if not name.startswith("_")}

    assert public == OPERATIONS
    assert [name for name in sorted(OPERATIONS) if not hasattr(GitCli, name)] == []
