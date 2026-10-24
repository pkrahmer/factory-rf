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
    "seal",
    "check_seal",
    "discard",
    "remove_nested_repositories",
    "work_tree_id",
    "remove_ignored",
    "ignored",
}


def test_git_has_exactly_the_twenty_six_operations_and_git_cli_has_each() -> None:
    public = {name for name, _ in inspect.getmembers(Git, callable) if not name.startswith("_")}

    assert public == OPERATIONS
    assert [name for name in sorted(OPERATIONS) if not hasattr(GitCli, name)] == []
