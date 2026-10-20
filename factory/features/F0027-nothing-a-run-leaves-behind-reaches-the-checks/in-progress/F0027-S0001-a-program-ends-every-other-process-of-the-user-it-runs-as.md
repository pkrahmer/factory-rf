---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 351
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T12:01:46.134362Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T12:01:46.139950Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T12:02:14.610052Z'
  stage: intake
  run: 0eb8fd1c544642408534d74d69e21b40
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T12:02:35.836476Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T12:08:33.406031Z'
  stage: tests
  run: 77a64acd093c49c396bae566a1280561
---

# A program ends every other process of the user it runs as

## Description

A process that an agent run starts in a new session outlives the run: neither the end of the call nor the time limit's kill of its process group reaches it, and it keeps writing with its run's rules while later stages run, are undone and are checked. This story builds the program that ends such processes: `python -I -m factory.entry.leftovers --user <name>`. It is meant to run as the agent's user (through the one `sudo` rule, S0002). It refuses to run as root and refuses unless it runs as the user `--user` names, both before its first signal. Otherwise it sends `SIGKILL` to every process its user may signal (`kill(-1)`, which spares the program itself) and reads the process table through F0030-S0001's reader (`factory.adapters.process.read_process_table`: `/proc/<pid>/stat` and the owner of `/proc/<pid>`) until no process of its user is left but itself, ended processes (zombies and dead entries) not counted. It signals again each round, at most 50 rounds with 0.1 s between them, and ends 0 when none is left and 1 with the process ids when some are. Every fault is one line on standard error that starts `factory-leftovers:`, with status 1. The process table, the signal, the identity and the pause are injected for tests. No test calls the real signal (`signal_every_other`), and no test or smoke test runs the program as the user it names: it would end the run that runs it (the feature's human's change 1). Nothing starts the program yet; the runtimes call it in S0002.

## Interface

`factory.domain.sessions` (`domain`, changed: F0030-S0001's model and parser, reused):

```python
class ProcessEntry(BaseModel):
    """One process of the kernel's table: its id, its session, whether it has ended, its owner."""

    pid: PositiveInt
    session: NonNegativeInt
    ended: bool
    uid: NonNegativeInt


def parse_stat(pid: int, stat: str, *, uid: int) -> ProcessEntry: ...
```

- `ProcessEntry` gains the last field `uid`, the user id that owns the process's folder `/proc/<pid>`. `pid`, `session`, `ended`, `ENDED_STATES` and `left_to_kill` stay as F0030-S0001 built them.
- `parse_stat` gains the keyword `uid` and puts it into the entry unchanged. What it reads from the text, and the `ValueError` for text it cannot read, stay.

`factory.domain.leftovers` (`domain`, new):

```python
LEFTOVERS_PREFIX = "factory-leftovers:"
LEFTOVER_ROUNDS = 50
LEFTOVER_PAUSE_SECONDS = 0.1


class Identity(BaseModel):
    """Who a process runs as: its user id, that user's name, and its own process id."""

    uid: NonNegativeInt
    user: Annotated[str, StringConstraints(min_length=1)]
    pid: PositiveInt


def leftover_pids(entries: Sequence[ProcessEntry], identity: Identity) -> list[int]: ...
def leftovers_refusal(identity: Identity, user: str) -> str | None: ...
```

- `ProcessEntry` here is `factory.domain.sessions.ProcessEntry`. This module defines no process model of its own.
- `Identity` is frozen and forbids unknown keys.
- `leftover_pids`: the `pid` of every entry whose `uid` is `identity.uid`, whose `pid` is not `identity.pid` and whose `ended` is false (not a zombie, not dead), in ascending order, without repeats.
- `leftovers_refusal`: `refuses to run as root` when `identity.uid` is 0, whatever `user` is; otherwise `runs as <identity.user>, not <user>` when `user` differs from `identity.user` (case-sensitive); otherwise `None`.

`factory.adapters.process` (`adapters`, changed: F0030-S0001's reader made public, and the program's two calls added; there is no module `factory.adapters.own_processes`):

```python
def read_process_table(proc: Path = _PROCESS_TABLE) -> list[ProcessEntry]: ...
def own_identity() -> Identity: ...
def signal_every_other(signal_number: int) -> None: ...
```

- The module imports `Identity` from `factory.domain.leftovers`, beside what it imports from `factory.domain.sessions`. Its one `Popen` call and its one `os.execvpe` call stay its only ways to start a process.
- `read_process_table(proc)` is F0030-S0001's private `_read_process_table`, renamed, with the folder as a parameter (default `_PROCESS_TABLE`, `/proc`, unchanged). `_kill_session` calls it with no argument.
- For each folder of `proc` whose name is decimal digits only, it reads the file `stat` and the folder's owner (`<folder>.stat().st_uid`), and adds `parse_stat(<pid>, <the text>, uid=<the owner>)`. A folder whose `stat` or owner cannot be read (any `OSError`: the process ended meanwhile) is left out, as before, and so is a name that is not digits only (`self`, `12a`). A `ValueError` from `parse_stat` propagates, as before. An `OSError` from listing `proc` itself propagates. New: the entries are sorted by `pid`.
- The owner is the folder's, not a file's (the human, 2026-10-20): a process that makes itself not dumpable (`prctl(PR_SET_DUMPABLE, 0)`) gets root-owned files under `/proc/<pid>`, while its folder keeps its user (pre-check round 3, in the image: the folder `1001`, its `stat` file `0`).
- `own_identity()`: `Identity(uid=os.getuid(), user=<pwd.getpwuid(os.getuid()).pw_name>, pid=os.getpid())`.
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

- `None` means `sys.argv[1:]`, `sys.stderr`, and `own_identity`, `signal_every_other` and `read_process_table` of `factory.adapters.process`, and `time.sleep`, each read at the call. `ProcessEntry` in the signature is `factory.domain.sessions.ProcessEntry`. The module ends with `if __name__ == "__main__": sys.exit(main())`. It writes nothing to standard output.
- Every fault writes one line, `factory-leftovers: <fault>` and a newline, to `stderr` and returns 1. No later step runs.
- Step 1, the arguments: exactly `--user` and one non-empty name. Anything else is the fault `<USAGE>`, before `identity` is called.
- Step 2: `leftovers_refusal(identity(), name)`. A refusal is the fault, before the first `kill`.
- Step 3, the rounds, for round 1 to `LEFTOVER_ROUNDS`: `kill(signal.SIGKILL)`, then `leftover_pids(processes(), <the identity of step 2>)`. An empty list returns 0 and writes nothing. Otherwise, when the round is not the last, `sleep(LEFTOVER_PAUSE_SECONDS)`. So there is one `kill` and one `processes()` per round, and one pause fewer than rounds.
- An `OSError` from `kill` is the fault `cannot signal the processes: <error>`, before `processes()` of that round. An `OSError` or a `ValueError` (a `stat` text the reader cannot parse) from `processes()` is the fault `cannot list the processes: <error>`.
- After the last round, with processes left: the fault `<n> processes left after 50 rounds: <the ids of the last round, joined by ", ">`.

Tests (the tester writes them): `tests/domain/test_leftovers.py`, `tests/adapters/test_process_table.py` (`read_process_table` on fake process tables as folders under `tmp_path`, and `own_identity`), `tests/entry/test_leftovers.py` (`main` in-process with every call injected; one row runs the real module in a child process through `factory.adapters.process.run_process`, naming a user it does not run as, with `-I -B`: `-I` ignores `PYTHONDONTWRITEBYTECODE`, and under the tests' umask `022` (`tests/conftest.py`) the bytecode it would write into `src/factory` makes folders of mode `755` that the factory's removal of ignored paths (S0003) cannot remove). No test calls `signal_every_other` or runs the program as the user it names. Changed under the feature's decision 16, by the tester only and nothing else in that module: `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer`, whose expected set gains `"factory.entry.leftovers"` (it imports `factory.adapters.process` for its defaults, as `factory.entry.confine` imports its adapters); its name and every other line stay. And F0030-S0001's `tests/domain/test_sessions.py`: every `ProcessEntry(...)` it builds, in the rows of `test_status_line_is_read` and in `_entry`, gains `uid=1001`; both calls `parse_stat(pid, stat)` in `test_status_line_is_read` become `parse_stat(pid, stat, uid=1001)`; the `fields` of `test_entry_limits` gain `"uid": 0`. Every test there keeps its name, its rows and what it checks. The limits of `uid` are rows of criterion 3, in `tests/domain/test_leftovers.py`.

## Acceptance criteria

1. `leftover_pids` (rows of one parametrized test, `Identity(uid=1001, user="agent", pid=11)`; an entry is written `(pid, uid, ended)`, its `session` equal to its `pid`): an entry `(7, 1001, False)` gives `[7]`. The own process `(11, 1001, False)` gives `[]`. Another user's `(9, 1000, False)` gives `[]`. An ended `(8, 1001, True)` gives `[]`. The unsorted table `(10, 1001, False)`, `(3, 1001, False)`, `(11, 1001, False)`, `(9, 1000, False)`, `(7, 1001, False)`, `(8, 1001, True)` gives `[3, 7, 10]`. Two entries `(7, 1001, False)` and `(7, 1001, False)` give `[7]`. An empty table gives `[]`.
2. `leftovers_refusal` (rows of one parametrized test): uid 0, user `root`, with `root` and with `agent` both give `refuses to run as root`. Uid 1001, user `agent`, gives `runs as agent, not factory` with `factory`, `runs as agent, not Agent` with `Agent`, and `None` with `agent`.
3. The models' limits (rows of one parametrized test, each built through a variable typed `type[BaseModel]`): `ProcessEntry` (`pid` 1, `session` 0, `ended` false) refuses `uid` -1 and accepts 0; its other fields' limits stay with F0030-S0001's `test_entry_limits`. `Identity` refuses `user` `""` and accepts `"a"`, refuses `pid` 0 and accepts 1, refuses `uid` -1 and accepts 0.
4. `read_process_table(<a folder under tmp_path>)` (rows of one parametrized test, each row one folder `<name>/stat` holding the text given; the folders belong to the user the tests run as): `7` with `7 (x y) S 1 7 7 0\n` gives `[ProcessEntry(pid=7, session=7, ended=False, uid=os.getuid())]`. `8` with `8 (x) Z 1 8 8 0\n` gives the entry with `ended` true. The name `self` with a valid `stat` gives `[]`. So does `12a`. A digit folder without a `stat` file gives `[]`. Folders `10`, `2` and `33`, each with a valid `stat`, give the entries in the order 2, 10, 33. A folder `5` with `5 x S 1 5 5 0\n` (no closing parenthesis) raises `ValueError`.
5. `read_process_table(<a path under tmp_path that does not exist>)` raises `FileNotFoundError`.
6. `own_identity()` gives `uid` `os.getuid()`, `user` `pwd.getpwuid(os.getuid()).pw_name` and `pid` `os.getpid()`.
7. The arguments of `main` (rows of one parametrized test, with injected recorders for `kill`, `processes` and `sleep` and an `identity` of uid 1001, user `agent`, pid 11): `[]`, `["--user"]`, `["--user", ""]`, `["--name", "agent"]`, `["--user", "agent", "extra"]` and `["agent"]` each return 1, write exactly `factory-leftovers: usage: python -m factory.entry.leftovers --user <name>\n`, and call `identity` and `kill` never. `["--user", "agent"]` with a process table that is empty at once returns 0, writes nothing and calls `kill` once with `signal.SIGKILL`.
8. The refusals of `main` (rows of one parametrized test, `processes` returning `[]`): identity uid 0 user `root` with `["--user", "root"]` returns 1 and writes `factory-leftovers: refuses to run as root\n`. Uid 1001 user `agent` with `["--user", "factory"]` returns 1 and writes `factory-leftovers: runs as agent, not factory\n`. In both rows `kill`, `processes` and `sleep` are never called.
9. The rounds of `main` (rows of one parametrized test, identity uid 1001 user `agent` pid 11, `processes` returning scripted tables in turn, `["--user", "agent"]`). None left after round 1 returns 0, with `kill` called once and `sleep` never. One left after round 1 and none after round 2 returns 0, with `kill` twice and `sleep` once with 0.1. Left after rounds 1 to 49 and none after round 50 returns 0, with `kill` 50 times and `sleep` 49 times. The entries of pids 7 and 10 (uid 1001, not ended) left after every round returns 1, with `kill` 50 times and `sleep` 49 times, and writes `factory-leftovers: 2 processes left after 50 rounds: 7, 10\n`. A table holding only the own pid, a zombie and another user's process counts as empty and returns 0 after round 1. Nothing is written in the rows that return 0.
10. The faults of `main` (rows of one parametrized test, `["--user", "agent"]`, identity uid 1001 user `agent`): `kill` raising `PermissionError(1, "Operation not permitted")` returns 1, writes `factory-leftovers: cannot signal the processes: [Errno 1] Operation not permitted\n` and never calls `processes`. `processes` raising `OSError("no table")` on its first call returns 1, writes `factory-leftovers: cannot list the processes: no table\n`, and `kill` was called once. `processes` raising `ValueError("too few fields in the status line of 5")` on its first call returns 1 and writes `factory-leftovers: cannot list the processes: too few fields in the status line of 5\n`.
11. The real module in a child process (`[sys.executable, "-I", "-B", "-m", "factory.entry.leftovers", "--user", "factory-test-nobody"]`, through `run_process`, working directory `tmp_path`): the exit status is 1, standard output is empty, and standard error is `factory-leftovers: runs as <pwd.getpwuid(os.getuid()).pw_name>, not factory-test-nobody\n` (or `factory-leftovers: refuses to run as root\n` when the tests run as uid 0). The same child (`-I -B`) with no arguments exits 1 with the usage line.
12. `make check` stays green.
13. docs: `docs/project-guide/write-guard.md`: a new section after *The start wrapper*, *The end of a run's processes*. It holds the command line, the three steps and their fault lines, the rounds (50, 0.1 s, a signal each round, zombies and dead entries not counted, the program itself spared by `kill(-1)`), the two refusals and why (root would end the container; a stand-in `sudo` that does not switch users makes it refuse), the reading of the process table through F0030-S0001's `read_process_table` (`/proc/<pid>/stat` for `ended`, the owner of the folder `/proc/<pid>` as `uid` and why the folder's and not a file's, a vanished entry left out), and why it never waits with `kill -0 -1` (Linux counts a target it may not signal as found). It names the tests and says that no test calls `signal_every_other` or runs the program as the user it names. `docs/project-guide/processes-and-checks.md`, *Starting a process*, the paragraph *Killing a session* and the paragraph after it: the reader is `read_process_table(proc)`, public, sorted by `pid`, and also reads each folder's owner; `ProcessEntry` has the field `uid`, and `parse_stat` takes it as a keyword; the module also holds `own_identity` and `signal_every_other`, which only the program of `write-guard.md`, *The end of a run's processes*, uses; that program reuses the reader and the model. `docs/project-guide/README.md`, *The files*: `write-guard.md` also describes `factory.domain.leftovers` and `factory.entry.leftovers`, and names `factory.adapters.process` for `own_identity`, `signal_every_other` and `read_process_table`, and its section list gains *The end of a run's processes*. `docs/decisions.md`: an entry *A run's leftover processes are ended by a program that runs as the agent*, dated with the story, with the reasons of the feature's decisions 8 to 10, and why it reuses F0030-S0001's model and reader instead of a second reading of `/proc` (the human, 2026-10-20). `docs/operator-guide.md`: none in this story, since nothing starts the program yet (S0002 documents its use).

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
import os
import sys
from pathlib import Path

from factory.adapters.process import read_process_table
from factory.domain.leftovers import Identity, leftover_pids
from factory.domain.sessions import ProcessEntry
from factory.entry.leftovers import main

proc = Path(sys.argv[1])
for pid, state in [(7, "S"), (8, "Z"), (10, "D"), (11, "S")]:
    (proc / str(pid)).mkdir()
    (proc / str(pid) / "stat").write_text(f"{pid} (x y) {state} 1 {pid} {pid} 0\n", encoding="utf-8")
(proc / "self").mkdir()
(proc / "12").mkdir()
entries = read_process_table(proc)
me = Identity(uid=os.getuid(), user="agent", pid=11)
print([(entry.pid, entry.ended, entry.uid == os.getuid()) for entry in entries])
print(leftover_pids(entries, me))

agent = Identity(uid=1001, user="agent", pid=11)
kills: list[int] = []
pauses: list[float] = []
tables = [[ProcessEntry(pid=7, session=7, ended=False, uid=1001)], []]
err = io.StringIO()
status = main(["--user", "agent"], stderr=err, identity=lambda: agent, kill=kills.append, processes=lambda: tables.pop(0), sleep=pauses.append)
print(status, [int(number) for number in kills], pauses, repr(err.getvalue()))
EOF
```
Expect: three lines, `[(7, False, True), (8, True, True), (10, False, True), (11, False, True)]`, then `[7, 10]`, then `0 [9, 9] [0.1] ''`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: concrete modules and signatures are named for all four layers (`factory.domain.sessions` `uid` field and `parse_stat(..., *, uid)`, `factory.domain.leftovers`, `factory.adapters.process` `read_process_table`/`own_identity`/`signal_every_other`, `factory.entry.leftovers.main` with its injected calls). Every behaviour stated in the Interface comments (sorting by pid, the owner read from the folder, the order of the arguments, rounds and pauses, fault texts) has a criterion.
   Criteria: each can be tested by one parametrized test function. Each rule has its failing side: the root refusal and the user mismatch (2, 8), the limits of `uid`, `user` and `pid` at -1/0, ""/"a" and 0/1 (3), a bad name, a missing `stat` and an unparseable `stat` (4), a missing folder (5), usage faults (7), and the kill and list faults (10). The 50th-round failure is in 9. Not covered, by design: `signal_every_other`'s `ProcessLookupError` and the unreadable-owner `OSError`, which no test can reach safely or portably; the feature states that no test calls `signal_every_other`. The `None` defaults of `main` are only reached by criterion 11's child process.
   Smoke test: three runnable commands, with no pytest and so no `-q` problem. I traced the third by hand: the table gives 7, 8, 10, 11 in order, `[7, 10]` follows, and two rounds give `0 [9, 9] [0.1] ''`. Each Expect line can be checked against the output. The second command's expectation assumes a non-root user, which the story's own criterion 11 also notes.
   Architecture: matches CLAUDE.md. The domain modules are pure. `adapters.process` stays the one module that starts processes and reads `/proc`. `entry.leftovers` imports the adapters for its defaults, and the story names the wiring test change (decision 16). It reuses F0030's reader and model, so there is no second helper.
   Scope: within F0027's scope for S0001 (the listed modules and tests). The test changes to other stories' tests are the ones decision 16 names, with the human's leave. Nothing is out of scope: nothing starts the program, since S0002 wires it.
4. factory: started tests as self.
5. tester: Wrote the tests for every acceptance criterion. Each one is a single test function. Rules with several cases are rows of one parametrized test.

   - criterion 1: tests/domain/test_leftovers.py::test_leftover_pids_are_the_user_s_other_living_processes
   - criterion 2: tests/domain/test_leftovers.py::test_root_and_another_user_are_refused
   - criterion 3: tests/domain/test_leftovers.py::test_model_limits (each model is built through a parameter typed `type[BaseModel]`)
   - criterion 4: tests/adapters/test_process_table.py::test_process_table_is_read_from_the_folders
   - criterion 5: tests/adapters/test_process_table.py::test_missing_process_table_raises
   - criterion 6: tests/adapters/test_process_table.py::test_own_identity_is_the_running_process
   - criterion 7: tests/entry/test_leftovers.py::test_wrong_arguments_print_the_usage (the six bad argument lists) and tests/entry/test_leftovers.py::test_the_user_s_name_starts_the_rounds (`["--user", "agent"]` with a table that is empty at once)
   - criterion 8: tests/entry/test_leftovers.py::test_refusals_come_before_the_first_signal
   - criterion 9: tests/entry/test_leftovers.py::test_rounds_signal_until_none_is_left
   - criterion 10: tests/entry/test_leftovers.py::test_faults_of_signal_and_listing_end_the_program
   - criterion 11: tests/entry/test_leftovers.py::test_the_real_module_refuses_in_a_child_process (two rows: another user, which expects the root line when the tests run as uid 0, and no arguments; both run with `-I -B` through `run_process` in `tmp_path`)
   - criterion 12: the factory's `make check`
   - criterion 13: the docs stage

   Files created: tests/domain/test_leftovers.py, tests/adapters/test_process_table.py, tests/entry/test_leftovers.py.

   Earlier test files changed, each exactly as the Interface names under the feature's decision 16:
   - tests/domain/test_sessions.py: every `ProcessEntry(...)` gains `uid=1001`, both `parse_stat` calls gain `uid=1001`, and the `fields` of `test_entry_limits` gain `"uid": 0`. Test names, rows and what each test checks are unchanged.
   - tests/entry/test_wiring.py: the expected set of test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer gains `"factory.entry.leftovers"`.

   The injected calls of `main` are recorded by one `Recorder` dataclass inside tests/entry/test_leftovers.py. No test calls `signal_every_other`, and none runs the program as the user it names.

   One run of `make test`: it stopped at collection. tests/domain/test_sessions.py fails with a pydantic ValidationError because `ProcessEntry` has no field `uid` yet. The new test modules cannot import modules or names that do not exist yet:
   - `factory.domain.leftovers`
   - `factory.entry.leftovers`
   - `read_process_table` and `own_identity` from `factory.adapters.process`

   These failures are on purpose: they are the coder's specification. `make lint` is green. The type check was skipped, as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/entry/test_leftovers.py - ImportError while importing test module...
