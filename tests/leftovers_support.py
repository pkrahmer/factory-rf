"""The identity and the process entries the tests of the leftovers program build."""

from factory.domain.leftovers import Identity
from factory.domain.sessions import ProcessEntry

AGENT = Identity(uid=1001, user="agent", pid=11)


def process_entry(pid: int, uid: int = 1001, *, ended: bool = False) -> ProcessEntry:
    """A process table entry of `pid` in a session of its own, owned by `uid`."""
    return ProcessEntry(pid=pid, session=pid, ended=ended, uid=uid)
