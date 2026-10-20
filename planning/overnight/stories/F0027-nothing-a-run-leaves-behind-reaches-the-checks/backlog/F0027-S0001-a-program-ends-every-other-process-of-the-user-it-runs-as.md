# A program ends every other process of the user it runs as

## Description

A process that an agent run starts in a new session outlives the run: neither the end of the call nor the time limit's kill of its process group reaches it, and it keeps writing with its run's rules while later stages run, are undone and are checked. This story builds the program that ends such processes: `python -I -m factory.entry.leftovers --user <name>`. It is meant to run as the agent's user (through the one `sudo` rule, S0002). It refuses to run as root and refuses unless it runs as the user `--user` names, both before its first signal. Otherwise it sends `SIGKILL` to every process its user may signal (`kill(-1)`, which spares the program itself) and reads the process table under `/proc` until no process of its user is left but itself, zombies not counted. It signals again each round, at most 50 rounds with 0.1 s between them, and ends 0 when none is left and 1 with the process ids when some are. Every fault is one line on standard error that starts `factory-leftovers:`, with status 1. The process table, the signal, the identity and the pause are injected for tests. No test calls the real signal (`signal_every_other`), and no test or smoke test runs the program as the user it names: it would end the run that runs it (the feature's human's change 1). Nothing starts the program yet; the runtimes call it in S0002.

## Interface

`factory.domain.leftovers` (`domain`, new):

```python
LEFTOVERS_PREFIX = "factory-leftovers:"
LEFTOVER_ROUNDS = 50
LEFTOVER_PAUSE_SECONDS = 0.1


class ProcessEntry(BaseModel):
    """One process of the process table: its id, its real user id and the letter of its state."""

    pid: PositiveInt
    uid: NonNegativeInt
    state: Annotated[str, StringConstraints(pattern=r"^[A-Za-z]$")]


class Identity(BaseModel):
    """Who a process runs as: its user id, that user's name, and its own process id."""

    uid: NonNegativeInt
    user: Annotated[str, StringConstraints(min_length=1)]
    pid: PositiveInt


def leftover_pids(entries: Sequence[ProcessEntry], identity: Identity) -> list[int]: ...
def leftovers_refusal(identity: Identity, user: str) -> str | None: ...
```

- Both models are frozen and forbid unknown keys.
- `leftover_pids`: the `pid` of every entry whose `uid` is `identity.uid`, whose `pid` is not `identity.pid` and whose `state` is neither `Z` (zombie) nor `X` (dead), in ascending order, without repeats. Every other state counts (`R`, `S`, `D`, `T`, `t`, `I`, and any other letter).
- `leftovers_refusal`: `refuses to run as root` when `identity.uid` is 0, whatever `user` is; otherwise `runs as <identity.user>, not <user>` when `user` differs from `identity.user` (case-sensitive); otherwise `None`.

`factory.adapters.own_processes` (`adapters`, new):

```python
PROC = Path("/proc")


def own_identity() -> Identity: ...
def list_processes(proc: Path = PROC) -> list[ProcessEntry]: ...
def signal_every_other(signal_number: int) -> None: ...
```

- `own_identity()`: `Identity(uid=os.getuid(), user=<pwd.getpwuid(os.getuid()).pw_name>, pid=os.getpid())`.
- `list_processes(proc)`: one entry for each folder of `proc` whose name is decimal digits only and whose `status` file holds a `State:` line and a `Uid:` line. `uid` is the first number after `Uid:`, the real user id. `state` is the first character after `State:` and its white space. Entries are sorted by `pid`. A folder whose `status` cannot be read (any `OSError`: the process ended meanwhile), that lacks either line, or whose values do not parse into a `ProcessEntry`, is left out. A name that is not digits only (`self`, `sys`, `12a`) is left out. An `OSError` from listing `proc` itself propagates.
- `signal_every_other(signal_number)`: `os.kill(-1, signal_number)`. A `ProcessLookupError` (no process to signal) is no error; every other `OSError` propagates. It is called by no test and no smoke test (the feature's decision 10).

`factory.entry.leftovers` (`entry`, new):

```python
USAGE = "usage: python -m factory.entry.leftovers --user <name>"


def main(
    argv: Sequence[str] | None = None,
    *,
    stderr: TextIO | None = None,
    identity: Callable[[], Identity] | None = None,
    kill: Callable[[int], None] | None = None,
    processes: Callable[[], list[ProcessEntry]] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> int:
    """End every other process of the user this program runs as; 0 once none is left."""
```

- `None` means `sys.argv[1:]`, `sys.stderr`, `own_identity`, `signal_every_other`, `list_processes` and `time.sleep`, each read at the call. The module ends with `if __name__ == "__main__": sys.exit(main())`. It writes nothing to standard output.
- Every fault writes one line, `factory-leftovers: <fault>` and a newline, to `stderr` and returns 1. No later step runs.
- Step 1, the arguments: exactly `--user` and one non-empty name. Anything else is the fault `<USAGE>`, before `identity` is called.
- Step 2: `leftovers_refusal(identity(), name)`. A refusal is the fault, before the first `kill`.
- Step 3, the rounds, for round 1 to `LEFTOVER_ROUNDS`: `kill(signal.SIGKILL)`, then `leftover_pids(processes(), <the identity of step 2>)`. An empty list returns 0 and writes nothing. Otherwise, when the round is not the last, `sleep(LEFTOVER_PAUSE_SECONDS)`. So there is one `kill` and one `processes()` per round, and one pause fewer than rounds.
- An `OSError` from `kill` is the fault `cannot signal the processes: <error>`, before `processes()` of that round. An `OSError` from `processes()` is the fault `cannot list the processes: <error>`.
- After the last round, with processes left: the fault `<n> processes left after 50 rounds: <the ids of the last round, joined by ", ">`.

Tests (the tester writes them): `tests/domain/test_leftovers.py`, `tests/adapters/test_own_processes.py` (fake process tables as folders under `tmp_path`), `tests/entry/test_leftovers.py` (`main` in-process with every call injected; one row runs the real module in a child process through `factory.adapters.process.run_process`, naming a user it does not run as, with `-I -B`: `-I` ignores `PYTHONDONTWRITEBYTECODE`, and under the tests' umask `022` (`tests/conftest.py`) the bytecode it would write into `src/factory` makes folders of mode `755` that the factory's removal of ignored paths (S0003) cannot remove). No test calls `signal_every_other` or runs the program as the user it names. Changed under the feature's decision 16, by the tester only and nothing else in that module: `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer`, whose expected set gains `"factory.entry.leftovers"` (it imports `factory.adapters.own_processes` for its defaults, as `factory.entry.confine` imports its adapters); its name and every other line stay.

## Acceptance criteria

1. `leftover_pids` (rows of one parametrized test, `Identity(uid=1001, user="agent", pid=11)`): an entry `(7, 1001, "S")` gives `[7]`. The own process `(11, 1001, "S")` gives `[]`. Another user's `(9, 1000, "R")` gives `[]`. A zombie `(8, 1001, "Z")` and a dead `(6, 1001, "X")` give `[]`. Each of the states `R`, `D`, `T`, `t` and `I` of uid 1001 gives that pid. The unsorted table `(10, 1001, "D")`, `(3, 1001, "S")`, `(11, 1001, "R")`, `(9, 1000, "S")`, `(7, 1001, "T")`, `(8, 1001, "Z")` gives `[3, 7, 10]`. Two entries `(7, 1001, "S")` and `(7, 1001, "R")` give `[7]`.
2. `leftovers_refusal` (rows of one parametrized test): uid 0, user `root`, with `root` and with `agent` both give `refuses to run as root`. Uid 1001, user `agent`, gives `runs as agent, not factory` with `factory`, `runs as agent, not Agent` with `Agent`, and `None` with `agent`.
3. The models' limits (rows of one parametrized test, each built through a variable typed `type[BaseModel]`): `ProcessEntry` refuses `pid` 0 and accepts 1, refuses `uid` -1 and accepts 0, refuses `state` `""`, `"SS"` and `"1"` and accepts `"S"`. `Identity` refuses `user` `""` and accepts `"a"`, refuses `pid` 0 and accepts 1, refuses `uid` -1 and accepts 0.
4. `list_processes(<a folder under tmp_path>)` (rows of one parametrized test, each row one folder `<name>/status` holding the text given): `7` with `Name:\tx\nState:\tS (sleeping)\nUid:\t1001\t1002\t1003\t1004\n` gives `[ProcessEntry(pid=7, uid=1001, state="S")]`, the real uid and the state's first letter. `8` with `State:\tZ (zombie)\nUid:\t0\t0\t0\t0\n` gives the entry with uid 0 and state `Z`. The name `self` with a valid status gives `[]`. So does `12a`. A digit folder without a `status` file, a status without a `Uid:` line, a status without a `State:` line, and a `Uid:` line whose first field is `x`, each give `[]`. Folders `10`, `2` and `33`, each with a valid status, give the entries in the order 2, 10, 33.
5. `list_processes(<a path under tmp_path that does not exist>)` raises `FileNotFoundError`.
6. `own_identity()` gives `uid` `os.getuid()`, `user` `pwd.getpwuid(os.getuid()).pw_name` and `pid` `os.getpid()`.
7. The arguments of `main` (rows of one parametrized test, with injected recorders for `kill`, `processes` and `sleep` and an `identity` of uid 1001, user `agent`, pid 11): `[]`, `["--user"]`, `["--user", ""]`, `["--name", "agent"]`, `["--user", "agent", "extra"]` and `["agent"]` each return 1, write exactly `factory-leftovers: usage: python -m factory.entry.leftovers --user <name>\n`, and call `identity` and `kill` never. `["--user", "agent"]` with a process table that is empty at once returns 0, writes nothing and calls `kill` once with `signal.SIGKILL`.
8. The refusals of `main` (rows of one parametrized test, `processes` returning `[]`): identity uid 0 user `root` with `["--user", "root"]` returns 1 and writes `factory-leftovers: refuses to run as root\n`. Uid 1001 user `agent` with `["--user", "factory"]` returns 1 and writes `factory-leftovers: runs as agent, not factory\n`. In both rows `kill`, `processes` and `sleep` are never called.
9. The rounds of `main` (rows of one parametrized test, identity uid 1001 user `agent` pid 11, `processes` returning scripted tables in turn, `["--user", "agent"]`). None left after round 1 returns 0, with `kill` called once and `sleep` never. One left after round 1 and none after round 2 returns 0, with `kill` twice and `sleep` once with 0.1. Left after rounds 1 to 49 and none after round 50 returns 0, with `kill` 50 times and `sleep` 49 times. `(7, 1001, "S")` and `(10, 1001, "D")` left after every round returns 1, with `kill` 50 times and `sleep` 49 times, and writes `factory-leftovers: 2 processes left after 50 rounds: 7, 10\n`. A table holding only the own pid, a zombie and another user's process counts as empty and returns 0 after round 1. Nothing is written in the rows that return 0.
10. The faults of `main` (rows of one parametrized test, `["--user", "agent"]`, identity uid 1001 user `agent`): `kill` raising `PermissionError(1, "Operation not permitted")` returns 1, writes `factory-leftovers: cannot signal the processes: [Errno 1] Operation not permitted\n` and never calls `processes`. `processes` raising `OSError("no table")` on its first call returns 1, writes `factory-leftovers: cannot list the processes: no table\n`, and `kill` was called once.
11. The real module in a child process (`[sys.executable, "-I", "-B", "-m", "factory.entry.leftovers", "--user", "factory-test-nobody"]`, through `run_process`, working directory `tmp_path`): the exit status is 1, standard output is empty, and standard error is `factory-leftovers: runs as <pwd.getpwuid(os.getuid()).pw_name>, not factory-test-nobody\n` (or `factory-leftovers: refuses to run as root\n` when the tests run as uid 0). The same child (`-I -B`) with no arguments exits 1 with the usage line.
12. `make check` stays green.
13. docs: `docs/project-guide/write-guard.md`: a new section after *The start wrapper*, *The end of a run's processes*. It holds the command line, the three steps and their fault lines, the rounds (50, 0.1 s, a signal each round, zombies and dead entries not counted, the program itself spared by `kill(-1)`), the two refusals and why (root would end the container; a stand-in `sudo` that does not switch users makes it refuse), the reading of `/proc/<pid>/status` (the real uid, the state's letter, a vanished entry left out), and why it never waits with `kill -0 -1` (Linux counts a target it may not signal as found). It names the tests and says that no test calls `signal_every_other` or runs the program as the user it names. `docs/project-guide/README.md`, *The files*: `write-guard.md` also describes `factory.domain.leftovers`, `factory.adapters.own_processes` and `factory.entry.leftovers`, and its section list gains *The end of a run's processes*. `docs/decisions.md`: an entry *A run's leftover processes are ended by a program that runs as the agent*, dated with the story, with the reasons of the feature's decisions 8 to 10. `docs/operator-guide.md`: none in this story, since nothing starts the program yet (S0002 documents its use).

## Smoke test

```bash
uv run -q python -I -m factory.entry.leftovers; echo "status $?"
```
Expect: two lines, `factory-leftovers: usage: python -m factory.entry.leftovers --user <name>` and `status 1`

```bash
line=$(uv run -q python -I -m factory.entry.leftovers --user factory-smoke-nobody 2>&1); status=$?
[ "$line" = "factory-leftovers: runs as $(id -un), not factory-smoke-nobody" ] && echo "refused as expected, status $status"
```
Expect: `refused as expected, status 1`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python - "$d" <<'EOF'
import io
import sys
from pathlib import Path

from factory.adapters.own_processes import list_processes
from factory.domain.leftovers import Identity, ProcessEntry, leftover_pids
from factory.entry.leftovers import main

proc = Path(sys.argv[1])
for pid, uid, state in [(7, 1001, "S (sleeping)"), (8, 1001, "Z (zombie)"), (9, 1000, "R (running)"), (10, 1001, "D (disk sleep)"), (11, 1001, "S (sleeping)")]:
    (proc / str(pid)).mkdir()
    (proc / str(pid) / "status").write_text(f"Name:\tx\nState:\t{state}\nUid:\t{uid}\t{uid}\t{uid}\t{uid}\n", encoding="utf-8")
(proc / "self").mkdir()
(proc / "12").mkdir()
entries = list_processes(proc)
agent = Identity(uid=1001, user="agent", pid=11)
print([(entry.pid, entry.uid, entry.state) for entry in entries])
print(leftover_pids(entries, agent))

kills: list[int] = []
pauses: list[float] = []
tables = [[ProcessEntry(pid=7, uid=1001, state="S")], []]
err = io.StringIO()
status = main(["--user", "agent"], stderr=err, identity=lambda: agent, kill=kills.append, processes=lambda: tables.pop(0), sleep=pauses.append)
print(status, [int(number) for number in kills], pauses, repr(err.getvalue()))
EOF
```
Expect: three lines, `[(7, 1001, 'S'), (8, 1001, 'Z'), (9, 1000, 'R'), (10, 1001, 'D'), (11, 1001, 'S')]`, then `[7, 10]`, then `0 [9, 9] [0.1] ''`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
