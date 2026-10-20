---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 344
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T08:32:30.147688Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T08:32:30.154147Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T08:32:55.098749Z'
  stage: intake
  run: 666dcf1c80fe48529683aa97ad662cf0
---

# The kill at a time limit ends every process of the command's session

## Description

The factory starts every command in a session of its own and, at the command's time limit, kills the command's process group with SIGKILL (`_kill_group` in `factory.adapters.process`). A descendant that takes a process group of its own is not in that group, and nothing kills it. GNU `timeout` does exactly that unless it is given `--foreground`, and the `mutants` recipe, when `MUTANTS_SECONDS` is set, runs `timeout $(MUTANTS_SECONDS) uv run mutmut run ...`, so F0024's acceptance saw `MakeProjectCommands.run("mutants")` return `time_limit` after 3 s while `timeout`, `uv run mutmut run` and mutmut's Python went on in `timeout`'s own group, writing `mutants/`. The factory also returned at once: it waits only for its child, `make`, and for the end of its pipe, and mutmut writes into `tee`'s pipe, not the factory's. A descendant that leaves the group keeps the session, though: `timeout` calls `setpgid`, not `setsid`, and a session cannot be left except by `setsid`. This story makes the kill at a time limit, at a callback's stop and at a callback's error end every process of the child's session that the factory may signal, and return only when none of them is left. The pure part, reading one line of the kernel's process table and choosing what is left to kill, is a new domain module, so that each of its rules is a row of a test. The group kill stays first, as it is, with its `PermissionError` under `sudo` (decision log, 2026-10-17); a process of the session that the factory may not signal (root's `sudo`, the agent's own processes) is left to the agent's own `timeout` and not waited for. A process that left the session with `setsid` stays outside the rule. The `Makefile`, every caller of `run_process` and `run_streaming`, and the result of a killed command (`exit_status=None`, `timed_out=True`, the output written so far) stay as they are.

## Interface

`factory.domain.sessions` (domain; new):

```python
ENDED_STATES: Final[frozenset[str]] = frozenset({"Z", "X"})


class ProcessEntry(BaseModel):
    """One process of the kernel's table: its id, its session and whether it has ended."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pid: PositiveInt
    session: NonNegativeInt
    ended: bool


def parse_stat(pid: int, stat: str) -> ProcessEntry:
    """The entry of the text of `/proc/<pid>/stat`, whose name in parentheses may hold anything."""


def left_to_kill(
    entries: Iterable[ProcessEntry], *, session: int, refused: Collection[int]
) -> list[int]:
    """The ids, in ascending order, of the session's processes that have not ended and were not refused."""
```

- `parse_stat` reads the fields after the last `)` of the text: the first is the state, the fourth the session. `ended` is true when the state is in `ENDED_STATES` (a zombie, `Z`, or a dead process, `X`), false for every other state.
- `parse_stat` raises `ValueError` for a text with no `)`, with fewer than four fields after the last `)`, or whose fourth field is not a non-negative integer.
- `left_to_kill` keeps an entry when its `session` is `session`, it has not `ended`, and its `pid` is not in `refused`; it leaves every other entry out. The ids come in ascending order, each once.

`factory.adapters.process` (adapters; changed):

- `_kill_group(process)` becomes `_kill_session(process)`, called where `_kill_group` is called today: in `run_process` at the time limit, and in `run_streaming` at the time limit, at a stop by `on_line` and when `on_line` raises.
- It first kills the child's process group with SIGKILL exactly as today: `os.killpg(process.pid, signal.SIGKILL)`, a `ProcessLookupError` suppressed, a `PermissionError` raised as today.
- Then, in rounds: it reads every numeric folder of `/proc` into a `ProcessEntry` with `parse_stat` (a folder whose `stat` can no longer be read, an `OSError`, is skipped: that process has ended), takes `left_to_kill(entries, session=process.pid, refused=refused)`, and sends each of those ids SIGKILL with `os.kill`. A `ProcessLookupError` is skipped; a `PermissionError` adds the id to `refused` (another user's process, such as root's `sudo` or the agent's own, ended by the agent's own `timeout`). It waits 0.05 s between rounds and returns when a round finds nothing left to kill.
- So a process that took a group of its own and stayed in the session is gone, ended or a zombie, when `run_process` or `run_streaming` returns. The child itself is not yet reaped while the rounds run, so its id, the session's id, cannot be taken by an unrelated process.
- A process that called `setsid` is in another session and is not killed. The rounds have no time limit of their own: SIGKILL cannot be refused, and a process that does not end after it would hold `communicate()` today as well.
- Unchanged: `ProcessRequest`, `ProcessResult`, `_start` (`start_new_session=True`, the one `subprocess.Popen(` line), `replace_process`, the module's suppression markers, `factory.adapters.make_commands` and every runtime.

Tests (the tester writes them): `tests/domain/test_sessions.py` and `tests/adapters/test_process_session.py` (new). A test whose child must start a grandchild and write its pid file before the kill runs it with `ROOMY_LIMIT` and bounds the elapsed time by `ROOMY_BOUND_SECONDS`, both from `tests/time_limits.py` (F0029-S0002), and reads the end with `is_gone(pid, within=0)` from `tests/process_support.py`: the rule is that the process is gone when the call returns, not some seconds later. A grandchild writes to `/dev/null`, not to the child's pipe, as mutmut writes into `tee`'s pipe and not into the factory's, so that only the kill can end it before the call returns. Earlier tests changed: none.

## Acceptance criteria

1. One status line read (rows of one parametrized test of `parse_stat`): `"4242 (make) S 1 4242 4242 0 -1"` with pid 4242 gives `ProcessEntry(pid=4242, session=4242, ended=False)`. A name with a space and parentheses, `"77 (a) (b c) R 1 70 70 0"`, gives session 70. State `Z` and state `X` give `ended=True`; states `S`, `R`, `D` and `T` give `ended=False`. A text without `)`, one with only three fields after it (`"5 (x) S 1 5"`), one whose fourth field is `x` (`"5 (x) S 1 5 x 0"`), and one whose fourth field is `-1` (`"5 (x) S 1 5 -1 0"`) raise `ValueError` (pydantic's `ValidationError` is one).
2. The entry's limits (rows of one parametrized test, built through a variable typed `type[BaseModel]`): `pid` 0 is refused and 1 accepted; `session` -1 is refused and 0 accepted.
3. What is left to kill (rows of one parametrized test of `left_to_kill` with `session=10`): an entry of session 10 that has not ended is kept; one of session 11, one that has ended, and one whose pid is in `refused` are left out. Entries with pids 30, 12 and 20 of session 10 give `[12, 20, 30]`; the same entry twice gives its pid once; no entries give `[]`.
4. At the time limit (rows of one parametrized test over `run_process` and `run_streaming`, with a callback that never stops, and `ROOMY_LIMIT`): the child starts a grandchild, writes its pid to a file, prints `started` and sleeps 60 s; the grandchild sleeps 60 s with its streams on `/dev/null`. Row `group`: the grandchild stays in the child's group. Row `own-group`: the child starts the grandchild with `subprocess.Popen(..., process_group=0)`, so it is in a group of its own before the pid file is written, as `timeout` puts itself in one. In each of the four rows the result has `timed_out=True` and `exit_status=None`, the call returns within `ROOMY_BOUND_SECONDS`, and `is_gone(pid, within=0)` is true for the grandchild when the call has returned. Row `own-session` (both runners): the child starts the grandchild with `start_new_session=True` instead; when the call has returned it is still running (`is_gone(pid, within=0)` false), and the test then kills it itself.
5. At a stop and at an error of the callback (rows of one parametrized test over `run_streaming`, with `ROOMY_LIMIT`, and a grandchild that the child starts with `subprocess.Popen(..., process_group=0)`, so that it has a group of its own before the child writes its pid file and prints `started`; a grandchild that called `os.setpgid` itself would still be in the child's group when `started` arrives, and the stop's group kill alone would end it): row `stop`, the callback returns `True` on the line `started`: the result has `stopped=True`. Row `raise`, the callback raises `RuntimeError` on that line: the error propagates. In both rows the grandchild is gone when the call has returned or raised (`is_gone(pid, within=0)`), well before `ROOMY_LIMIT`.
6. The `mutants` recipe's form (rows of one parametrized test of `MakeProjectCommands.run` on a `Makefile` written in `tmp_path`, with `SHELL := /bin/bash`, `.SHELLFLAGS := -eu -o pipefail -c` and a target `slow` whose one line is `timeout <flag> 60 sh -c 'echo $$$$ > grandchild.pid; exec sleep 60' 2>&1 | tee run.txt`, and `ROOMY_LIMIT`): row `own-group`, without a flag, as the recipe runs mutmut; row `foreground`, with `--foreground`. In both rows the result's status is `time_limit`, the call returns within `ROOMY_BOUND_SECONDS`, and the process whose pid `grandchild.pid` holds is gone when it has returned (`is_gone(pid, within=0)`).
7. The runs under `sudo` are unchanged: `tests/adapters/test_claude_runtime_sudo_time_limit.py`, `tests/adapters/test_claude_runtime_os_user.py`, `tests/adapters/test_process.py` and `tests/adapters/test_process_streaming.py` pass unchanged.
8. `make check` stays green.
9. docs: `docs/project-guide/processes-and-checks.md`. *Starting a process*: at the `time_limit`, at a stop and at an error of the callback, the factory kills the child's process group and then every process of the child's session that it may signal, in rounds, until none is left, and only then returns. The session holds what the command started even when a descendant took a group of its own (as `timeout` without `--foreground` does). A process that called `setsid` is outside it, and another user's process (root's `sudo`, the agent's under `sudo`) is left to the agent's own `timeout`. Name `factory.domain.sessions` and its tests. *Project commands*, the line "the process group is killed": every process of its session is killed. *Mutation testing*, the paragraph on the stop at `MUTANTS_SECONDS`: a `make mutants` run through the factory's project commands (`MakeProjectCommands.run`) and killed at its time limit leaves no mutmut running, as it stays in the session; a caller that kills `make` itself, such as a shell's `timeout`, reaches only `make`'s group. `docs/decisions.md`: an entry *A command stopped at its time limit loses every process of its session*, dated with the story, saying that it corrects F0024 decision 4 ("the factory waits until `timeout` ends it"). Reasons: `timeout` moves mutmut into a group of its own, and the factory waited only for its child and its pipe (F0024's acceptance, section 2); a session survives a new group and a dead parent, which a walk of parent ids does not. Rejected: `timeout --foreground` in the recipe alone (it mends one recipe, and every other project command keeps the fault); a cgroup per command (not available to the factory's user under rootless Podman); the factory as subreaper (`PR_SET_CHILD_SUBREAPER`: it would reap every orphan of every run); a time limit of the rounds' own (no process outlives SIGKILL except in the kernel, and that would hold the call already). The entry *The container runtime's init reaps the processes a killed run leaves* (2026-10-18), whose cause ends with a project command that `run_process` "kills the group and waits only for its child", gets a line naming the new entry; the init still reaps what the kill leaves. `README.md`: none, nothing a newcomer does changes.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SHELL := /bin/bash\n.SHELLFLAGS := -eu -o pipefail -c\nslow:\n\ttimeout 77 sh -c %s 2>&1 | tee run.txt\n' "'echo \$\$\$\$ > grandchild.pid; exec sleep 77'" > "$d/Makefile"
uv run -q python - "$d" <<'EOF'
import sys
from datetime import timedelta
from pathlib import Path
from factory.adapters.make_commands import MakeProjectCommands
d = Path(sys.argv[1])
result = MakeProjectCommands(d).run("slow", time_limit=timedelta(seconds=10))
pid = (d / "grandchild.pid").read_text().strip()
try:
    state = (Path("/proc") / pid / "stat").read_text().rpartition(")")[2].split()[0]
except FileNotFoundError:
    state = "gone"
print(result.status, "gone" if state in {"gone", "Z", "X"} else f"running ({state})")
EOF
ps -eo args | grep -c '^sleep 77$' || true
```
Expect: two lines, `time_limit gone` and `0` (the recipe's form, `timeout` without `--foreground` and its output through `tee`, killed at a 10-second limit, leaves no process running; before this story the same block printed `time_limit running (S)` and `1`)

```bash
uv run -q python -c 'from factory.domain.sessions import parse_stat; print(parse_stat(77, "77 (a) (b c) Z 1 70 70 0"))'
```
Expect: `pid=77 session=70 ended=True`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names `factory.domain.sessions` (`ENDED_STATES`, `ProcessEntry`, `parse_stat`, `left_to_kill`) with signatures, and `_kill_group` → `_kill_session` in `factory.adapters.process` with the call sites, the rounds, the 0.05 s wait and the unchanged parts. Concrete enough for two coders to build the same thing.
   - Criteria: each is testable by a parametrized test function. Every `parse_stat` rule has a row on both sides (the state set, the last `)`, the missing `)`, three fields, `x`, `-1`). `left_to_kill` has a row per clause (session, ended, refused, ordering, duplicates, empty). The `ProcessEntry` limits are tested at 0 and 1 for `pid`, and at -1 and 0 for `session`. The time-limit, stop and error paths are covered for both runners, with the `setsid` edge pinned. The sudo paths are pinned by existing tests (criterion 7). Three adapter clauses have no row of their own: the suppressed `ProcessLookupError`, the skipped unreadable `/proc` folder, and the `refused` handling of a `PermissionError`. All three need a mock or a second user, and the story says so for `refused`, so I accepted them as covered by the end-to-end rows.
   - Smoke test: the commands are runnable. Neither block runs pytest, so the `-q` in `addopts` does not matter. Each `Expect:` is checkable against the output (`time_limit gone` and `0`; `pid=77 session=70 ended=True`).
   - Architecture: the pure parsing and selection sit in the domain with no I/O. The `/proc` reading and the signals sit in the adapter, which is the only module that starts processes, and no new wrapper, dependency or suppression marker is added.
   - Scope: within F0030's Scope. It touches none of the Out-of-scope items (the `Makefile` recipe, the TERM before the KILL, `setsid` processes, other users' processes, the pipeline file). It changes no earlier test.
