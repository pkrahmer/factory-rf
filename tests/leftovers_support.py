"""The process table entries the tests of the process table build."""

from factory.domain.sessions import ProcessEntry


def process_entry(pid: int, uid: int = 1001, *, ended: bool = False) -> ProcessEntry:
    """A process table entry of `pid` in a session of its own, owned by `uid`."""
    return ProcessEntry(pid=pid, session=pid, ended=ended, uid=uid)
