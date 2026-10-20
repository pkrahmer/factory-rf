---
stage: done
blocked: null
round: 2
attempts: 1
crashes: 0
pull_request: 344
comments_read: []
handed_over: approval
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
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T08:33:16.751420Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T08:39:42.082635Z'
  stage: tests
  run: 929b95205b9d44c9bfeacfb879bb3808
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T08:40:03.193981Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T08:45:49.323049Z'
  stage: doing
  run: ec48030279c84c5197d76126431f0ba0
- number: 8
  speaker: factory
  kind: stall
  at: '2026-10-20T08:45:49.348476Z'
  stage: doing
  run: ec48030279c84c5197d76126431f0ba0
  reason: check_red
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-20T08:46:12.632571Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-20T08:51:55.871090Z'
  stage: doing
  run: 906e68e991d84bef8d8476a4ea567a9a
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-20T08:52:16.816482Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-20T08:53:55.882229Z'
  stage: review
  run: 34c2194e5880482e9707cc99b7e85400
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-20T08:54:16.740346Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-20T08:54:33.642183Z'
  stage: doing
  run: 5483606cbdb640c2be49271dbead69c2
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-20T08:54:54.206036Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-20T09:00:28.227572Z'
  stage: tests
  run: 46fbb358a62c4a6589846ebb159b3210
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-20T09:00:49.409526Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-20T09:06:19.872041Z'
  stage: doing
  run: e12c15da521645ffa40812aff95a462c
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-20T09:06:40.419006Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-20T09:08:11.383537Z'
  stage: review
  run: 1e6ad97c27c7494487e2c5d245e6d764
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-20T09:08:32.984523Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-10-20T09:08:55.435880Z'
  stage: doing
  run: dc5620972eb047f189573c96a84a2961
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-20T09:09:16.109511Z'
  stage: tests
- number: 24
  speaker: tester
  kind: result
  at: '2026-10-20T09:15:09.223580Z'
  stage: tests
  run: a80ca2e6fb17452b9af47730b2734f73
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-20T09:15:30.935519Z'
  stage: doing
- number: 26
  speaker: coder
  kind: result
  at: '2026-10-20T09:21:32.013641Z'
  stage: doing
  run: 7abcce01948746daab48114a8eaf0b3c
- number: 27
  speaker: factory
  kind: started
  at: '2026-10-20T09:21:52.976299Z'
  stage: review
- number: 28
  speaker: reviewer
  kind: result
  at: '2026-10-20T09:22:25.786802Z'
  stage: review
  run: b2aaeddedac14b709ee4a35cf7ce0e89
- number: 29
  speaker: factory
  kind: started
  at: '2026-10-20T09:22:46.618552Z'
  stage: docs
- number: 30
  speaker: documenter
  kind: result
  at: '2026-10-20T09:23:39.736294Z'
  stage: docs
  run: ccb1df347d224b208064a983e1437fe9
- number: 31
  speaker: factory
  kind: started
  at: '2026-10-20T09:24:00.756180Z'
  stage: smoke-test
- number: 32
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T09:24:36.116108Z'
  stage: smoke-test
  run: 3768366f4bd74485b60babb31f33b950
- number: 33
  speaker: factory
  kind: done
  at: '2026-10-20T09:25:55.988543Z'
  stage: approval
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
8. A process of the session that the factory may not signal is left, not waited for (one test of `run_process` with criterion 4's child, the grandchild in a group of its own, and `ROOMY_LIMIT`; `os.kill` replaced for the call through `monkeypatch` by a stand-in that raises `PermissionError` for the grandchild's id and calls the real `os.kill` for every other id): the call returns within `ROOMY_BOUND_SECONDS` with `timed_out=True`, and the grandchild is still running when it has returned (`is_gone(pid, within=0)` false); the test undoes the replacement and then kills it itself.
9. A process of the session that ends between the read of `/proc` and its kill is skipped (a row beside criterion 8's in one parametrized test of `run_process`, with the same child, grandchild and `ROOMY_LIMIT`; the stand-in for `os.kill` calls the real `os.kill` for the grandchild's id and then raises `ProcessLookupError`, as if it had ended in between, and calls the real `os.kill` for every other id): the call returns, raising nothing, within `ROOMY_BOUND_SECONDS` with `timed_out=True`, and the grandchild is gone when it has returned (`is_gone(pid, within=0)`).
10. `make check` stays green.
11. docs: `docs/project-guide/processes-and-checks.md`. *Starting a process*: at the `time_limit`, at a stop and at an error of the callback, the factory kills the child's process group and then every process of the child's session that it may signal, in rounds, until none is left, and only then returns. The session holds what the command started even when a descendant took a group of its own (as `timeout` without `--foreground` does). A process that called `setsid` is outside it, and another user's process (root's `sudo`, the agent's under `sudo`) is left to the agent's own `timeout`. Name `factory.domain.sessions` and its tests. *Project commands*, the line "the process group is killed": every process of its session is killed. *Mutation testing*, the paragraph on the stop at `MUTANTS_SECONDS`: a `make mutants` run through the factory's project commands (`MakeProjectCommands.run`) and killed at its time limit leaves no mutmut running, as it stays in the session; a caller that kills `make` itself, such as a shell's `timeout`, reaches only `make`'s group. `docs/decisions.md`: an entry *A command stopped at its time limit loses every process of its session*, dated with the story, saying that it corrects F0024 decision 4 ("the factory waits until `timeout` ends it"). Reasons: `timeout` moves mutmut into a group of its own, and the factory waited only for its child and its pipe (F0024's acceptance, section 2); a session survives a new group and a dead parent, which a walk of parent ids does not. Rejected: `timeout --foreground` in the recipe alone (it mends one recipe, and every other project command keeps the fault); a cgroup per command (not available to the factory's user under rootless Podman); the factory as subreaper (`PR_SET_CHILD_SUBREAPER`: it would reap every orphan of every run); a time limit of the rounds' own (no process outlives SIGKILL except in the kernel, and that would hold the call already). The entry *The container runtime's init reaps the processes a killed run leaves* (2026-10-18), whose cause ends with a project command that `run_process` "kills the group and waits only for its child", gets a line naming the new entry; the init still reaps what the kill leaves. `README.md`: none, nothing a newcomer does changes.

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
4. factory: started tests as self.
5. tester: I wrote the tests for every acceptance criterion. Each limit is tested on both sides, and every rule's cases are rows of one parametrized test.

   - criterion 1: tests/domain/test_sessions.py::test_status_line_gives_the_entry (the readable lines and the states Z, X, S, R, D, T) and tests/domain/test_sessions.py::test_unreadable_status_line_is_refused (no `)`, three fields, fourth field `x`, fourth field `-1`, all raising `ValueError`). They are two functions because one checks a returned value and the other a raised error.
   - criterion 2: tests/domain/test_sessions.py::test_entry_limits (pid 0 and 1, session -1 and 0, built through `type[BaseModel]`)
   - criterion 3: tests/domain/test_sessions.py::test_what_is_left_to_kill (rows: kept, other-session, ended, refused, ascending, twice, none, all with `session=10`)
   - criterion 4: tests/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_session (`run_process` and `run_streaming` × group, own-group and own-session; the own-session rows expect `is_gone(pid, within=0)` to be false)
   - criterion 5: tests/adapters/test_process_session.py::test_stop_and_error_of_the_callback_end_every_process_of_the_session (rows stop and raise; the call must return in less than `ROOMY_LIMIT`)
   - criterion 6: tests/adapters/test_process_session.py::test_time_limit_of_a_make_target_ends_what_timeout_started (rows own-group and foreground)
   - criterion 7: no new test. It is met by the existing tests/adapters/test_claude_runtime_sudo_time_limit.py, test_claude_runtime_os_user.py, test_process.py and test_process_streaming.py, which I did not change.
   - criterion 8 (`make check`) and criterion 9 (docs): no test, as neither is a test's to check.

   Files created: tests/domain/test_sessions.py and tests/adapters/test_process_session.py. I changed no earlier test file.

   A fixture, `pid_file`, kills any grandchild still running when a test ends; this covers the own-session rows and any row that fails. The child gets the grandchild's placement as `Popen` keyword arguments in its argv: `{}`, `{'process_group': 0}` or `{'start_new_session': True}`.

   One run of `make test`:
   - tests/domain/test_sessions.py cannot be collected because `factory.domain.sessions` does not exist yet (ImportError). That is the only module the run could not import.
   - The rows where the grandchild has a group of its own fail as intended, because today's group kill leaves the grandchild running. The visible failures were callback stop, callback raise and the make own-group row. `tail -5` cut off the rest of the list, so I have not seen whether the two own-group rows of the time-limit test failed too.
   - The rows that today's group kill already handles (group, foreground) are expected to pass.

   `make lint` is green. I skipped `make types`, as the stage says to while the module under test does not exist.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/domain/test_sessions.py - ImportError while importing test module...
6. factory: started doing as self.
7. coder: Built the session kill. `make check` is green: 99.13 % coverage, and `test: green (137.4 s)`.

   - `src/factory/domain/sessions.py` (new) holds `ENDED_STATES`, `ProcessEntry`, `parse_stat` and `left_to_kill`, as the Interface names them.
     - `parse_stat` splits the text at its last `)`. It raises `ValueError` itself when there is no `)` or there are too few fields. The `int()` of the fourth field raises `ValueError` for `x`, and `NonNegativeInt` raises a `ValidationError` for `-1`.
     - `left_to_kill` sorts a set of the matching ids.
     - The Interface's one-line docstring for `left_to_kill` is longer than ruff's 100 columns. It is now a summary line plus a sentence about `refused`.
   - `src/factory/adapters/process.py`: `_kill_group` is now `_kill_session`, called at the same three places. It still kills the group first, exactly as before, so the `PermissionError` under `sudo` is still raised. Then it runs rounds until nothing is left to kill: it reads the process table, kills what `left_to_kill` returns, and sleeps `_ROUND_PAUSE_SECONDS` (0.05 s) between rounds. Two private helpers do the work:
     - `_read_process_table` reads every numeric folder under `/proc` and skips one whose `stat` gives an `OSError`. It reads bytes and decodes them with the existing `_decode`, so a non-UTF-8 process name cannot raise.
     - `_kill_one` skips a `ProcessLookupError` and adds the id to `refused` on a `PermissionError`.
     - The docstrings of `run_process` and `run_streaming` and the comment after the kill now say "session" instead of "group".

   Main choice: the session's processes are read fresh from `/proc` on every round, and the loop ends when a round finds nothing to kill. I rejected collecting the targets once and then waiting on each one: a process that is forking at that moment would be missed. The rounds also make the call return only once every target is ended or a zombie, which is what the tests check with `is_gone(pid, within=0)`.

   Refactor pass: I read the diff and found nothing to change.

   Not run: the story's smoke-test commands. This stage's permissions refused the command, so the smoke-test stage has to run them.

   Noticed, not touched:
   - Lines 75–79 of `process.py` have no test: the `ProcessLookupError` and `PermissionError` branches of `_kill_one`. Intake already accepted them as covered by the end-to-end rows.
   - If an exception from `on_line` arrived after the child had already been reaped, the session's id could in theory belong to another process by the time the rounds run. Today's code cannot get there, because no line is passed after the wait.
8. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
   src/factory/entry/check_story.py                   92      1     18      1    98%   161
   src/factory/entry/confine.py                       70      1      8      1    97%   110
   src/factory/entry/contract.py                      28      1      6      1    94%   41
   src/factory/entry/guard.py                         37      1     10      1    96%   56
   src/factory/entry/health.py                        33      1     10      1    95%   48
   src/factory/entry/run.py                           71      1      4      1    97%   170
   src/factory/entry/watch.py                         52      1      6      1    97%   87
   -------------------------------------------------------------------------------------------
   TOTAL                                            8968     60   1840     28    99%

   110 files skipped due to complete coverage.
   Required test coverage of 90.0% reached. Total coverage: 99.13%
   =========================== short test summary info ============================
   FAILED tests/adapters/test_git_cli_work_tree.py::test_the_work_tree_id_is_the_tree_a_commit_records[tracked-ignored-file]
   make: *** [Makefile:75: test] Error 1
9. factory: started doing as self.
10. coder: Second run of the doing stage after the stall. I changed no code: the first run's work is committed (b54c626c) and `make check` is green now (`test: green (137.4 s)`, `check: green`).

    What is built (from the first run, read again for this entry):
    - `src/factory/domain/sessions.py` (new): `ENDED_STATES`, `ProcessEntry`, `parse_stat` (splits at the last `)`) and `left_to_kill` (a sorted set of the matching ids).
    - `src/factory/adapters/process.py`: `_kill_group` is now `_kill_session`, called at the same three places. It kills the group first, exactly as before. Then it runs rounds: `_read_process_table` reads `/proc` and skips a folder that raises `OSError`, `_kill_one` skips `ProcessLookupError` and adds a `PermissionError` id to `refused`, and there is a 0.05 s pause between rounds until a round finds nothing.
    - Main choice: the table is read fresh on every round. Rejected: collecting the targets once and then waiting for them, which would miss a process forked meanwhile.

    The stall: `tests/adapters/test_git_cli_work_tree.py::test_the_work_tree_id_is_the_tree_a_commit_records[tracked-ignored-file]` failed once under `make check`. It passed when run alone (14 passed) and in a full `make check` this round. The factory's stall output gives no `E` lines and no `file:line`, so I cannot quote the failure. It does not touch processes or sessions.
    - Likely cause (noticed, not touched, outside this work item): `GitCli.work_tree_id` (`src/factory/adapters/git_cli.py:420`) copies the own index with `shutil.copyfile`, which gives the copy a fresh mtime. Git's racy-entry check compares a file's mtime with the index file's mtime. So when `kept.log` goes from `one\n` to `two\n` (same size) within the timestamp granularity of the last index write, git can trust the stale stat data and skip the rehash, and the tree comes out stale.
    - `shutil.copy2`, which keeps the mtime, would likely fix it. That is a separate story for the human to decide on.

    Refactor pass: I read the diff again and found nothing to change.

    Not run: the story's smoke-test blocks. The first run's permissions refused them, and I did not try again.

    Noticed, not touched: the `ProcessLookupError` and `PermissionError` branches of `_kill_one` have no test of their own. Intake accepted that.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
11. factory: started review as self.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (src/factory/domain/sessions.py, src/factory/adapters/process.py, tests/domain/test_sessions.py, tests/adapters/test_process_session.py) against the work item. The architecture holds: the domain module is pure and the adapter imports it downward. No suppression markers were added, and no secret or string-built command is present. The 5 new findings of `make duplicates` are all in claude_runtime/opencode_runtime/clock.py, outside this diff. Criteria 2 to 7 are met by their tests.

    Findings:
    1. tests/domain/test_sessions.py::test_status_line_gives_the_entry: the Interface's limit "fewer than four fields after the last `)`" is tested only on the refused side ("5 (x) S 1 5", three fields). Every accepted row has five or more fields, so an off-by-one (`len(fields) <= 4`) would still pass. Fix: add the row "5 (x) S 1 5 5" (exactly four fields), giving `ProcessEntry(pid=5, session=5, ended=False)`.
    2. tests/domain/test_sessions.py::test_status_line_gives_the_entry and ::test_unreadable_status_line_is_refused: criterion 1 asks for the rules of `parse_stat` as rows of one parametrized test, but the tester split the accepted and refused sides into two functions. Fix: merge them into one parametrized test where each row carries either the expected entry or the expected `ValueError` (e.g. `contextlib.nullcontext()` vs `pytest.raises(ValueError)`).
    3. criterion 8 added: it needs its test. The Interface's rule "a `PermissionError` adds the id to `refused`" in `_kill_one` (src/factory/adapters/process.py) has no test, and the coder's journal reports those lines uncovered. Without that rule the rounds would never end on a process they cannot signal. Intake accepted it as covered by the end-to-end rows, but those rows do not reach it. It can be pinned without a change under `src/` by replacing `os.kill` through `monkeypatch` for the call, as the new criterion 8 describes. Criteria 8 and 9 (`make check`, docs) are renumbered 9 and 10.

    Earlier tests: none changed. The diff only adds test files (tests/domain/test_sessions.py, tests/adapters/test_process_session.py).

    Not raised: the `ProcessLookupError` branch of `_kill_one` and the skipped unreadable `/proc` folder are race branches. A stand-in that raises `ProcessLookupError` for a live process would make the rounds loop forever, so they stay uncovered, as intake accepted.
13. factory: started doing as self.
14. coder: Round 1. All three of the reviewer's findings (entry 12) are test changes. None of them needs a code change, so I changed nothing under `src/` and am handing the work item to the tester.

    The tester should make these changes:
    1. Criterion 1, the accepted side of the field-count limit: add the row `"5 (x) S 1 5 5"` with pid 5. It has exactly four fields after the last `)` and should give `ProcessEntry(pid=5, session=5, ended=False)`.
    2. Criterion 1, one parametrized test: merge `tests/domain/test_sessions.py::test_status_line_gives_the_entry` and `::test_unreadable_status_line_is_refused` into one parametrized test of `parse_stat`. Each row should carry either the expected entry or the expected `ValueError`.
    3. The new criterion 8 needs its test. Add one test of `run_process` to `tests/adapters/test_process_session.py`, using criterion 4's child with the grandchild in a group of its own (`process_group=0`) and `ROOMY_LIMIT`. It should replace `os.kill` through `monkeypatch` with a stand-in that raises `PermissionError` for the grandchild's id and calls the real `os.kill` for every other id. The test then checks four things:
       - the call returns within `ROOMY_BOUND_SECONDS`;
       - the result has `timed_out=True`;
       - `is_gone(pid, within=0)` is false for the grandchild;
       - after undoing the replacement, the test kills the grandchild itself.

    Built: nothing new this round. The code from entries 7 and 10 stays as it is: `src/factory/domain/sessions.py` and `_kill_session`, `_read_process_table` and `_kill_one` in `src/factory/adapters/process.py`.

    Main choice: I end with `tests` and leave the code alone. `_kill_one` (`src/factory/adapters/process.py`) already adds the id to `refused` on a `PermissionError`, and the rounds already exclude refused ids through `left_to_kill`, so the new criterion should pass once its test exists. I rejected a speculative code change, since no failing test asks for one.

    The journal changed the meaning of the task: the reviewer added criterion 8 and renumbered `make check` and docs as 9 and 10. The `## Description` already holds that text, so I did not rewrite it.

    Noticed, not touched: the possible racy-index cause of the `tests/adapters/test_git_cli_work_tree.py` flake, described in entry 10, outside this work item.
15. factory: started tests as self.
16. tester: Round 1, a test change approved by the human. I made the three changes the coder named in entry 14 from the reviewer's findings in entry 12, and nothing else.

    Changes:
    1. Criterion 1, the accepted side of the field-count limit: added the row `"5 (x) S 1 5 5"` with pid 5, id `four-fields`. It has exactly four fields after the last `)` and expects `ProcessEntry(pid=5, session=5, ended=False)`.
    2. Criterion 1 as one parametrized test: merged `test_status_line_gives_the_entry` and `test_unreadable_status_line_is_refused` in `tests/domain/test_sessions.py` into `test_status_line_is_read`.
       - Each row carries `expected: ProcessEntry | None`, and `None` means `parse_stat` must raise `ValueError`.
       - The old two tests' rows are all kept, and the four-fields row is added.
    3. Criterion 8 (new): added `test_process_the_factory_may_not_signal_is_left_not_waited_for` to `tests/adapters/test_process_session.py`.
       - It runs `run_process` with criterion 4's child, the grandchild in a group of its own, and `ROOMY_LIMIT`.
       - Through `monkeypatch`, `os.kill` is replaced by a stand-in that raises `PermissionError` for the grandchild's id and calls the real `os.kill` for every other id.
       - It asserts that the call returns within `ROOMY_BOUND_SECONDS`, that `timed_out` is true, and that `is_gone(grandchild, within=0)` is false.
       - It then calls `monkeypatch.undo()` and kills the grandchild itself. The `pid_file` fixture would also kill it if an assertion failed first.

    How the criteria map to tests now:
    - criterion 1: tests/domain/test_sessions.py::test_status_line_is_read
    - criterion 2: tests/domain/test_sessions.py::test_entry_limits (unchanged)
    - criterion 3: tests/domain/test_sessions.py::test_what_is_left_to_kill (unchanged)
    - criterion 4: tests/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_session (unchanged)
    - criterion 5: tests/adapters/test_process_session.py::test_stop_and_error_of_the_callback_end_every_process_of_the_session (unchanged)
    - criterion 6: tests/adapters/test_process_session.py::test_time_limit_of_a_make_target_ends_what_timeout_started (unchanged)
    - criterion 7: no new test. The existing sudo and process test files cover it, and I did not change them.
    - criterion 8: tests/adapters/test_process_session.py::test_process_the_factory_may_not_signal_is_left_not_waited_for
    - criteria 9 (`make check`) and 10 (docs): no test.

    Files changed: tests/domain/test_sessions.py and tests/adapters/test_process_session.py, both written by this story's tests stage. I created no files and changed no earlier test file.

    One run of `make test`: `test: green (147.2 s)`, 99.16 % coverage. The code already exists, so the new and changed tests pass, as the coder expected. No module failed to import. `make lint`: green. I ran it in the foreground with too short a timeout, so the tool moved it to the background; I waited for that one run to finish and did not start it again.

    `lint`: lint: green (0.0 s)
    `test`: test: green (147.2 s)
17. factory: started doing as self.
18. coder: Round 1, after the tester's changes (entry 16). I changed no code. The three findings in entry 12 were all test changes, and the tester has made them: the `four-fields` row, the merged `test_status_line_is_read`, and `test_process_the_factory_may_not_signal_is_left_not_waited_for` for criterion 8. All of them pass against the existing code. `make check` is green: `test: green (148.3 s)`, 99.16 % coverage, `check: green`.

    What is built (from entries 7 and 10, unchanged):
    - `src/factory/domain/sessions.py`: `ENDED_STATES`, `ProcessEntry`, `parse_stat` (splits the text at its last `)`) and `left_to_kill` (a sorted set of the matching ids).
    - `src/factory/adapters/process.py`: `_kill_session` replaces `_kill_group` at the same three call sites. It kills the group first, exactly as before. Then it works in rounds, with a 0.05 s pause between them, until a round finds nothing left to kill:
      - `_read_process_table` reads `/proc` and skips a folder whose `stat` raises `OSError`.
      - `_kill_one` skips a `ProcessLookupError` and adds the id to `refused` on a `PermissionError`.

    Main choice: the process table is read fresh on every round. I rejected collecting the targets once and then waiting for them, because a process forked in between would be missed. Criterion 8's new test now covers the `PermissionError` → `refused` branch of `_kill_one`.

    Refactor pass: I read `git diff main -- src` again and found nothing to change.

    The journal's change of meaning (criterion 8 added, `make check` and docs renumbered 9 and 10) is already in `## Description`, so I did not rewrite it.

    Noticed, not touched:
    - The `ProcessLookupError` branch of `_kill_one` and the skipped unreadable `/proc` folder are race branches and stay untested, as intake and the reviewer accepted.
    - The possible racy-index cause of the flaky `tests/adapters/test_git_cli_work_tree.py` test (entry 10) is outside this work item.
    - I did not run the smoke-test blocks; the smoke-test stage runs them.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
19. factory: started review as self.
20. reviewer: Round 1 review of `git diff main...HEAD -- . ':!factory'`, which covers `src/factory/domain/sessions.py`, `src/factory/adapters/process.py`, `tests/domain/test_sessions.py` and `tests/adapters/test_process_session.py`, against the work item.

    All three findings from entry 12 are fixed:
    - The `four-fields` row is in.
    - The two `parse_stat` functions are merged into `test_status_line_is_read`.
    - Criterion 8 is pinned by `test_process_the_factory_may_not_signal_is_left_not_waited_for`.

    Criteria 1 to 8 each have a test that checks what the criterion says. The factory's `make check` after the coder was green (entry 18).

    Architecture holds:
    - `factory.domain.sessions` is pure.
    - The adapter imports it downward.
    - Reading `/proc` and sending signals stay in `process.py`, the one module that starts processes.
    - No new suppression marker under `src/`.
    - No existing helper reads `/proc` or kills a pid, so nothing is copied.

    Findings:
    1. criterion 9 added: it needs its test. The Interface says that in the rounds of `_kill_session` "a `ProcessLookupError` is skipped" (`_kill_one`, src/factory/adapters/process.py:73-76). No test reaches that path: if the `except ProcessLookupError` were removed, every test would still pass, and `run_process` would raise when a process ends between the `/proc` read and the kill. It can be pinned without a change under `src/`, the same way as criterion 8. The `os.kill` stand-in calls the real `os.kill` for the grandchild's id and then raises `ProcessLookupError`. The call must return without raising, within `ROOMY_BOUND_SECONDS`, with `timed_out=True` and the grandchild gone. It is a row beside criterion 8's in one parametrized test. The old criteria 9 (`make check`) and 10 (docs) are now 10 and 11. Entry 12 left this branch out on the grounds that such a stand-in would loop forever. That holds only for a stand-in that always raises for a live process. One that kills first and then raises ends in the next round.

    Not raised: the skipped unreadable `/proc` folder (the `OSError` in `_read_process_table`). Pinning it would mean replacing `Path.read_bytes` or the module's private `_PROCESS_TABLE`, which comes close to mocking the code under test.

    Notes:
    - tests/domain/test_sessions.py:41: `# noqa: PT011` silences ruff's broad-`pytest.raises` rule. It is the only such marker under `tests/`. Giving each refused row a `match` pattern would make the marker unnecessary.

    Earlier tests: none changed. The diff only adds test files (`tests/domain/test_sessions.py`, `tests/adapters/test_process_session.py`).
21. factory: started doing as self.
22. coder: Round 2. I changed no code. The reviewer's one finding (entry 20) adds a test for the new criterion 9. The tester should add criterion 9's row beside criterion 8's in `tests/adapters/test_process_session.py` and make the two one parametrized test of `run_process`:
    - The child, the grandchild in a group of its own (`process_group=0`) and `ROOMY_LIMIT` are the same as criterion 8's.
    - The `os.kill` stand-in calls the real `os.kill` for the grandchild's id and then raises `ProcessLookupError`. It calls the real `os.kill` for every other id.
    - The test asserts that the call raises nothing, that it returns within `ROOMY_BOUND_SECONDS`, that the result has `timed_out=True`, and that `is_gone(grandchild, within=0)` is true.
    - Criterion 8's row keeps its assertions: the grandchild is still running, and the test kills it itself after `monkeypatch.undo()`.

    Built: nothing new this round. The code from entries 7 and 10 stays as it is:
    - `src/factory/domain/sessions.py`
    - `_kill_session`, `_read_process_table` and `_kill_one` in `src/factory/adapters/process.py`

    Main choice: I end with `tests` and leave the code alone. `_kill_one` (`src/factory/adapters/process.py:72-79`) already catches the `ProcessLookupError`, and the real kill ends the grandchild. The next round finds nothing left, so the new row should pass against the existing code. I rejected a speculative code change because no failing test asks for one.

    The journal changed the meaning of the task: the reviewer added criterion 9 and renumbered `make check` to 10 and docs to 11. `## Description` already holds that text, so I did not rewrite it.

    Noticed, not touched:
    - The reviewer's note on `# noqa: PT011` at `tests/domain/test_sessions.py:41` is a test change. The marker could go if each refused row gave `pytest.raises` a `match` pattern. That is for the tester to take up if the reviewer wants it; the reviewer listed it as a note, not a finding.
    - The racy-index cause of the flaky `tests/adapters/test_git_cli_work_tree.py` test (entry 10) is outside this work item.
    - I did not run `make check` this round because nothing changed since entry 18's green run.
23. factory: started tests as self.
24. tester: Round 2, a test change the human approved. Coder's entry 22 asked for a test of criterion 9, which the reviewer added in entry 20. I changed one file, `tests/adapters/test_process_session.py`. This story's tests stage wrote it, so I changed no earlier test file and created no files.

    What changed: criterion 8's test `test_process_the_factory_may_not_signal_is_left_not_waited_for` is now one parametrized test of `run_process`, `test_process_the_kill_cannot_reach_does_not_hold_the_call`, with two rows:
    - `may-not-signal` (criterion 8): the `os.kill` stand-in raises `PermissionError` for the grandchild's id. The grandchild is still running when the call returns. The test then undoes the replacement and kills it itself, as before.
    - `ended-in-between` (criterion 9): the stand-in calls the real `os.kill` for the grandchild's id and then raises `ProcessLookupError`. The call raises nothing and the grandchild is gone (`is_gone(pid, within=0)`).

    Both rows use the same child, a grandchild in a group of its own (`OWN_GROUP`), and `ROOMY_LIMIT`. Both assert that the call returns within `ROOMY_BOUND_SECONDS` with `timed_out=True`. Every other id goes to the real `os.kill`.

    One parameter, `ended`, drives two things: whether the stand-in kills first, and whether the grandchild is expected gone. I first wrote these as two parameters, but `make lint` refused six positional arguments (PLR0917). The two values are equal in both rows, so I merged them.

    Mapping (unchanged apart from criteria 8 and 9):
    - criterion 8: tests/adapters/test_process_session.py::test_process_the_kill_cannot_reach_does_not_hold_the_call[may-not-signal]
    - criterion 9: tests/adapters/test_process_session.py::test_process_the_kill_cannot_reach_does_not_hold_the_call[ended-in-between]

    One run of `make test`: `test: green (157.4 s)`, 99.17 % coverage. As the coder expected, the new row passes against the existing code. No module failed to import. That run was before the PLR0917 rename, which changed parameter names only, not what the test does. `make lint`: green after the rename.

    Not taken up: the reviewer's note on `# noqa: PT011` at `tests/domain/test_sessions.py:41`. It is a note, not a finding, and not part of the change asked for.

    `lint`: lint: green (0.0 s)
    `test`: test: green (159.0 s)
25. factory: started doing as self.
26. coder: Round 2, after the tester's change (entry 24). I changed no code. The reviewer's one finding (entry 20) was a missing test for criterion 9. The tester has added it as the `ended-in-between` row of `tests/adapters/test_process_session.py::test_process_the_kill_cannot_reach_does_not_hold_the_call`, beside criterion 8's `may-not-signal` row. Both rows pass against the existing code. I ran `make check` after the merge of `origin/main` (52883299): `test: green (158.5 s)`, 99.17 % coverage, `check: green`.

    What is built (from entries 7 and 10, unchanged):
    - `src/factory/domain/sessions.py`: `ENDED_STATES`, `ProcessEntry`, `parse_stat` (splits the text at its last `)`) and `left_to_kill` (a sorted set of the matching ids).
    - `src/factory/adapters/process.py`: `_kill_session` replaces `_kill_group` at the same three call sites. It kills the group first, exactly as before. Then it kills in rounds, 0.05 s apart, until a round finds nothing left:
      - `_read_process_table` reads `/proc` and skips a folder whose `stat` raises `OSError`.
      - `_kill_one` skips a `ProcessLookupError` and adds the id to `refused` on a `PermissionError`.

    Main choice: I read the process table again on every round. I rejected collecting the targets once and then waiting for them, because that would miss a process forked in between.

    Refactor pass: I read `git diff main -- src` again and found nothing to change.

    The journal changed the meaning of the task: the reviewer added criterion 9 and renumbered `make check` to 10 and docs to 11. `## Description` already holds that text, so I did not rewrite it.

    Noticed, not touched:
    - The reviewer's note on `# noqa: PT011` at `tests/domain/test_sessions.py:41` is a test matter and was a note, not a finding.
    - The skipped unreadable `/proc` folder (the `OSError` branch of `_read_process_table`) stays untested, as the reviewer accepted.
    - The racy-index cause of the flaky `tests/adapters/test_git_cli_work_tree.py` test (entry 10) is outside this work item.
    - I did not run the smoke-test blocks; the smoke-test stage runs them.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
27. factory: started review as self.
28. reviewer: Round 2 review of `git diff main...HEAD -- . ':!factory'` against the work item. The diff covers `src/factory/domain/sessions.py`, `src/factory/adapters/process.py`, `tests/domain/test_sessions.py` and `tests/adapters/test_process_session.py`.

    The finding from entry 20 is fixed. `tests/adapters/test_process_session.py::test_process_the_kill_cannot_reach_does_not_hold_the_call` is now one parametrized test of `run_process` with two rows:
    - `may-not-signal` (criterion 8).
    - `ended-in-between` (criterion 9). Its `os.kill` stand-in kills the grandchild for real and then raises `ProcessLookupError`. The `except ProcessLookupError` in `_kill_one` (`src/factory/adapters/process.py`) is what keeps the call from raising, so removing it would fail this row.

    Criteria 1 to 9 each have a test that checks what the criterion says:
    - Every limit in the Interface is tested on both sides: the field count, with the `four-fields` and `three-fields` rows; `pid` at 0 and 1; `session` at -1 and 0.
    - The sides of each rule are rows of one parametrized test.
    - Criterion 7 is met because none of the four named test files is changed.
    - The factory's `make check` after the coder was green (entry 26).
    - `make duplicates` still reports 5 new findings, none of them in this diff.

    Architecture holds. `factory.domain.sessions` is pure, and the adapter imports it downward. Reading `/proc` and sending signals stay in `process.py`, which reuses the existing `_decode`. No suppression marker was added under `src/`.

    Quality and hygiene:
    - Private helpers carry no docstrings.
    - The comments explain why.
    - The Description still matches what was built.
    - The docs criterion (11) still describes what the reader must know.

    No findings.

    Notes:
    - `tests/domain/test_sessions.py:41`: `# noqa: PT011` remains. A `match` pattern on each refused row would make the marker unnecessary. This is carried over from entry 20 and is not a finding.

    Earlier tests: none changed. The diff only adds test files (`tests/domain/test_sessions.py`, `tests/adapters/test_process_session.py`).
29. factory: started docs as self.
30. documenter: docs, round 2. I found no code that contradicts the Interface or the criteria, so there are no findings. I changed documents only, so I did not run `make check`. The factory's checks run after this stage. The docs criterion (11) was not yet written, so I wrote it.

    Files changed:
    - `docs/project-guide/processes-and-checks.md`:
      - The *Project commands* line now says every process of the session is killed, not the process group.
      - *Starting a process* now says the kill at the time limit, at a stop and at a callback error reaches the child's group and then its session.
      - A new paragraph, *Killing a session*, covers the rounds, the 0.05 s pause, and why a session and not a group. It also covers the limits: `setsid` is outside the rule, another user's process is left to the agent's own `timeout`, and an ended or unreadable process is skipped. It names `factory.domain.sessions` and its tests.
      - *Mutation testing*, the `MUTANTS_SECONDS` bullet: a `make mutants` run through `MakeProjectCommands.run` that is killed at its time limit leaves no mutmut running. A shell's `timeout` on `make` reaches only make's group.
    - `docs/decisions.md`:
      - New entry *A command stopped at its time limit loses every process of its session*. It corrects F0024 decision 4 and gives the reasons and the rejected options from the criterion.
      - The cause line of *The container runtime's init reaps the processes a killed run leaves* now names the new entry and says the init still reaps what the kill leaves.
    - `README.md`: unchanged, as the criterion says (nothing a newcomer does changes).

    Cross-read and found current: `docs/operator-guide.md` ("A `time_limit` under `sudo`": the `PermissionError` and agent `timeout` path is unchanged), `docs/project-guide/write-guard.md` (the wrapper keeps its process group), and the line on `replace_process` in `processes-and-checks.md`.

    I did not run the examples I wrote. They are prose with no commands. The story's smoke test block belongs to the smoke-test stage.

    Stale text I saw but did not touch: none.

    `check`: check: green (not run again: passed on tree fd1fd5adbafa at 2026-10-20T09:18:43Z)
    `secrets`: secrets: green (1.0 s)
    `documents`: documents ok
31. factory: started smoke-test as self.
32. smoke-tester: Smoke test, round 2. From the repository root I ran both commands under `## Smoke test` as written, in order. Neither starts a server. I changed nothing.

    Command 1: the `mutants` recipe's form in a temporary `Makefile`, which is `timeout 77` without `--foreground` with its output piped through `tee`, killed by `MakeProjectCommands.run("slow", time_limit=10 s)`, followed by a count of `sleep 77` processes. I ran the block in one bash shell so that its `trap` removes the temporary directory.

    ```
    time_limit gone
    0
    ```

    Met its `Expect:` line (two lines, `time_limit gone` and `0`). The grandchild was in `timeout`'s own group and was gone when the call returned, and no `sleep 77` was left running.

    Command 2: `parse_stat` on a name holding a space and parentheses, in state `Z`.

    ```
    pid=77 session=70 ended=True
    ```

    Met its `Expect:` line (`pid=77 session=70 ended=True`).

    Against the acceptance criteria: nothing the smoke test showed contradicts any of them. Command 1 matches criterion 6's `own-group` row and the story's main rule, and command 2 matches criterion 1's row for a name with parentheses and the `Z` state. The smoke test does not cover criteria 7–11 (sudo runs, permission and race handling, `make check`, docs), and it shows nothing against them.

    Findings: none. Open: nothing.
33. factory: done (pull request merged); cost: 15 runs, 28.6 min, 118 turns, 461684 tokens in (2506379 more from cache), 56358 out, $4.94
