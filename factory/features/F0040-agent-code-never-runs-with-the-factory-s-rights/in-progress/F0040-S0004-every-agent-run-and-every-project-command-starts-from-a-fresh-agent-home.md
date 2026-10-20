---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 365
comments_read: [6301863943, 6302567860, 6302831658]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T21:26:22.202832Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T21:26:22.208766Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-20T21:26:44.840502Z'
  stage: intake
  run: 8be7a808014e42b3804a43ff0c745088
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-20T21:28:03.828993Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-20T21:28:21.937855Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-20T21:28:44.654397Z'
  stage: intake
  run: f46befcc54994c30b7c410e4f1cd3e69
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-20T21:29:05.176417Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-20T21:34:24.801464Z'
  stage: tests
  run: 574b3ee09f054dc58f3907a7dd327276
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-20T21:34:45.521313Z'
  stage: doing
- number: 10
  speaker: factory
  kind: crash
  at: '2026-10-20T21:56:45.235257Z'
  stage: doing
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-20T21:56:47.518383Z'
  stage: doing
- number: 12
  speaker: factory
  kind: crash
  at: '2026-10-20T22:05:33.875549Z'
  stage: doing
- number: 13
  speaker: factory
  kind: question
  at: '2026-10-20T22:05:33.875549Z'
  stage: doing
  blocked: crash_cap
- number: 14
  speaker: human
  kind: comment
  at: '2026-10-20T22:05:57.745354Z'
  stage: doing
- number: 15
  speaker: human
  kind: comment
  at: '2026-10-20T22:06:53.134612Z'
  stage: doing
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-20T22:07:11.304125Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-10-20T22:10:28.938261Z'
  stage: doing
  run: af9ef3a9390e4522a3f5c82248ed0379
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-20T22:10:49.560171Z'
  stage: tests
- number: 19
  speaker: tester
  kind: result
  at: '2026-10-20T22:13:25.766291Z'
  stage: tests
  run: 5c7fc4a9021b427397103dd8bcacec49
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-20T22:13:46.887984Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-10-20T22:16:42.557342Z'
  stage: doing
  run: 3fc368b879e74076a1a746c46f90f1da
- number: 22
  speaker: factory
  kind: started
  at: '2026-10-20T22:17:03.588186Z'
  stage: review
- number: 23
  speaker: reviewer
  kind: result
  at: '2026-10-20T22:18:40.275746Z'
  stage: review
  run: 0580084891864710992cd41d356e9a49
- number: 24
  speaker: factory
  kind: started
  at: '2026-10-20T22:19:02.099363Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-10-20T22:19:23.255457Z'
  stage: doing
  run: c3050a69108c46ad92ef585ed1301b0d
- number: 26
  speaker: factory
  kind: started
  at: '2026-10-20T22:19:43.795650Z'
  stage: tests
- number: 27
  speaker: tester
  kind: result
  at: '2026-10-20T22:22:22.141635Z'
  stage: tests
  run: 55288076fd7148dba4a4c7a715bd3f17
- number: 28
  speaker: factory
  kind: started
  at: '2026-10-20T22:22:42.840459Z'
  stage: doing
- number: 29
  speaker: coder
  kind: result
  at: '2026-10-20T22:25:25.689578Z'
  stage: doing
  run: b45b1e0adc6049dea606bf120ebab1e8
---

# Every agent run and every project command starts from a fresh agent home

## Description

S0003 built the program that clears the agent's home of what the agent made. This story starts it, as the agent's user, before every agent run and before every project command, so that no run reads what an earlier one did (its transcripts, opencode's sessions) and no run finds a file an earlier one planted (a user `CLAUDE.md`, a `rules/` folder, a cache other than uv's). A new application interface, `AgentHome`, has one operation, `reset`. Its implementation, `SudoAgentHome`, runs `sudo -n -u <agent> -- timeout --signal=KILL 60s env -i <python> -I -B -m factory.entry.fresh_home --home /home/agent --keep <path>...` from `/` (`-B`, so the agent's user writes no bytecode beside the factory's source: `-I` ignores `PYTHONDONTWRITEBYTECODE`), built by `launch` as an agent run's call is, so the agent's own `timeout` ends it at 60 seconds, and raises `AgentRuntimeError` when the program fails, so no run starts in a home the factory could not clear. `run_sealed` resets the home after the seal and before the run, once per stage run: a run resumed after a provider limit or its budget keeps its session, because those resumes happen inside the one run. The preflight's probe goes through `run_sealed` and is reset the same way. `SealedProjectCommands` (S0002) resets the home after the seal and before each command, so a check never runs in what the agent run before it left. The kept paths are the two login files the image mounts (`FACTORY_CLAUDE_LOGIN_FILE`, `FACTORY_API_LOGIN_FILE`), the login each runtime keeps in the home when an operator logged in by hand (Claude Code's `~/.claude/.credentials.json`, opencode's `~/.local/share/opencode/auth.json`), the folders of `FACTORY_OPENCODE_FOLDERS`, and uv's package cache `~/.cache/uv` (`UV_CACHE_FOLDER`), which the agent's user writes in runs and project commands and which every later run and check reads: a small channel from one run to the next check that the human accepted (the feature's decision 9). The factory's own files there (agents, `settings.json`, `skills/`, `commands/`, `.config/opencode`) are not the agent's and stay. Without an agent user nothing is reset, as nothing runs as a second user. The image, the entrypoint, the compose file and the volume `claude-home` stay as they are.

## Interface

`factory.application.agent_home` (`application`, new):

```python
class AgentHome(ABC):
    """The agent user's home, which every agent run and project command starts from fresh."""

    @abstractmethod
    def reset(self) -> None:
        """Remove what earlier runs left in the home, the kept paths aside.

        `AgentRuntimeError` when the home cannot be cleared.
        """
```

`factory.application.boundaries` (`application`): `Boundaries` gains `agent_home: AgentHome | None = None`, last, so every construction written before it stays valid.

`factory.application.sealed_runs` (`application`):

```python
def run_sealed(boundaries, request, *, run=None) -> SealedRun: ...  # signature unchanged


class SealedProjectCommands(ProjectCommands):
    def __init__(
        self, inner: ProjectCommands, git: Git, log: FactoryLog, home: AgentHome | None = None
    ) -> None: ...
```

- `run_sealed`: `git.seal()`, then `boundaries.agent_home.reset()` when `agent_home` is set, then the run and what follows it as today. A reset that raises propagates before the run starts; the run is not started, and the seal is not checked (nothing ran). `run_sealed` resets once, however often the given `run` calls the runtime.
- `SealedProjectCommands.run`: `git.seal()`, then `home.reset()` when `home` is set, then the command and what follows it as in S0002. A reset that raises `AgentRuntimeError` raises `ProjectCommandError(command, <its detail>)` from it, and the command is not run: so the preflight's probe on `main`, which catches `ProjectCommandError`, stops with `preflight_failed`, and a stage's check counts an error, as for a refused `sudo` (S0001). Without `home` it behaves exactly as S0002 built it.

`factory.adapters.agent_home` (`adapters`, new):

```python
FRESH_HOME_TIME_LIMIT = timedelta(seconds=60)


class SudoAgentHome(AgentHome):
    """Clears the agent's home by running the fresh-home program as the agent's user."""

    def __init__(
        self,
        home: Path,
        kept: Sequence[str],
        *,
        os_user: str,
        sudo_executable: str,
        program: Sequence[str],
    ) -> None: ...

    @property
    def home(self) -> Path: ...

    @property
    def kept(self) -> list[str]: ...

    @property
    def os_user(self) -> str: ...

    @property
    def program(self) -> list[str]: ...

    @override
    def reset(self) -> None: ...
```

- `reset` starts, through `run_process` with `cwd` `/`, the `Launch` that `launch([*program, "--home", str(home), "--keep", <path>, ...], {}, os_user=os_user, sudo_executable=sudo_executable, time_limit=FRESH_HOME_TIME_LIMIT)` gives (one `"--keep", <path>` pair for each kept path, in order; `FRESH_HOME_TIME_LIMIT` read at each call): `[<sudo>, "-n", "-u", <os_user>, "--", "timeout", "--signal=KILL", "60s", "env", "-i", *program, "--home", <home>, ...]`, `env` `{}`, the time limit plus 30 seconds.
- Exit status 0 returns. A call that reached the limit (the factory's kill, or `killed_at_limit` true for its exit status and duration) raises `AgentRuntimeError("cannot reset the agent's home <home>: no end within <seconds> s")`, the seconds of `FRESH_HOME_TIME_LIMIT` as a whole number (`60` by default). Any other status raises `AgentRuntimeError("cannot reset the agent's home <home>: <line>")`, where `<line>` is the first line of standard error that starts with `FRESH_HOME_PREFIX`; without one, the last non-blank line of standard error; without one, `exit status <n>`. A program that cannot be started (`OSError`) raises `AgentRuntimeError("cannot reset the agent's home <home>: <strerror>")`.

`factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime` (`adapters`): each gains the constant `LOGIN_STATE_FILE`, the login the runtime keeps in the home after a login by hand: `".claude/.credentials.json"` and `".local/share/opencode/auth.json"`. Nothing else in them changes.

`factory.entry.wiring` (`entry`):

```python
FRESH_HOME_MODULE = "factory.entry.fresh_home"
UV_CACHE_FOLDER = ".cache/uv"


def fresh_home_command() -> list[str]:
    """The words that start the fresh-home program with this interpreter, isolated."""


def agent_home_of(settings: InstanceSettings, sudo_executable: str) -> SudoAgentHome | None:
    """The agent's home of the instance, or `None` when its agents run as no second user."""
```

- `fresh_home_command()` is `[sys.executable, "-I", "-m", FRESH_HOME_MODULE]`.
- `agent_home_of` is `None` without `settings.agent_user`. Otherwise its `home` is `settings.agent_home.parent`, its `os_user` the agent user, its `program` `fresh_home_command()`, and its `kept` `kept_paths(home, login_files=[settings.claude_login_file, settings.api_login_file], state_files=[claude LOGIN_STATE_FILE, opencode LOGIN_STATE_FILE], folders=[UV_CACHE_FOLDER, *settings.opencode_folders])`, whatever the instance's runtime.
- `build_boundaries` builds `agent_home_of(settings, <the sudo which finds, or SUDO_EXECUTABLE>)` once, sets it as `Boundaries.agent_home`, and passes the same object as `home` to the `SealedProjectCommands` it builds (S0002).

Tests (the tester writes them): `tests/application/test_agent_home_resets.py` (with a recording `AgentHome` of the test's own that inherits the interface, the fake agent runtime and a real clone, as `tests/application/test_sealed_runs.py` builds them), `tests/adapters/test_sudo_agent_home.py` (a stand-in `sudo` that records its arguments and working directory and runs what follows `--`, or exits with a planned status and standard error; the real program on a home under `tmp_path`), `tests/entry/test_wiring_agent_home.py`. No test resets a real home (the human's change 1). Under the leave of the feature's decision 14, `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module` expects `factory.adapters.agent_home` among the importers of `factory.adapters.process`; nothing else in that test changes.

## Acceptance criteria

1. `AgentHome` is an abstract base class whose abstract methods are exactly `{"reset"}`, and `SudoAgentHome` inherits it.
2. `run_sealed` with a recording home: the home records one `reset`, during which `.git` is already sealed (not group-writable), and the fake runtime receives the request after it. With a `run` that calls the runtime twice, the home still records one `reset`, before the first call.
3. A reset that raises `AgentRuntimeError("x")` in `run_sealed`: the error propagates, the fake runtime receives no request, and `check_seal` is not reached (rows of one parametrized test with criterion 2's case: with `agent_home` `None` the run happens as today).
4. `SealedProjectCommands(inner, git, log, home)` (rows of one parametrized test): the home records one `reset` per `run`, after the seal and before the inner command; a reset that raises `AgentRuntimeError("x")` raises `ProjectCommandError` whose `command` is the command run and whose `detail` is `x`, and the inner command is not called; without `home` the inner command runs as in S0002.
5. `SudoAgentHome(home, [".claude-token", ".config/sso"], os_user="agent", sudo_executable=<stand-in>, program=[sys.executable, "-I", "-m", "factory.entry.fresh_home"])` over a home under `tmp_path` holding `.claude/CLAUDE.md`, `.claude-token` and `.config/sso/login`: the stand-in records the arguments `["-n", "-u", "agent", "--", "timeout", "--signal=KILL", "60s", "env", "-i", <python>, "-I", "-m", "factory.entry.fresh_home", "--home", <home>, "--keep", ".claude-token", "--keep", ".config/sso"]` in the working directory `/`; afterwards `.claude/CLAUDE.md` is gone and the two kept paths are there; `reset` returns.
6. The faults of `reset` (rows of one parametrized test, the stand-in exiting with a planned status and standard error, running nothing): 1 with `sudo: unable to resolve host x` then `factory-fresh-home: .cache/a: Permission denied` raises `AgentRuntimeError` whose `detail` is `cannot reset the agent's home <home>: factory-fresh-home: .cache/a: Permission denied`; 1 with `sudo: a password is required` gives `...: sudo: a password is required`; 3 with nothing gives `...: exit status 3`; standard error `a`, `b` and a blank line, none starting with `FRESH_HOME_PREFIX`, gives `...: b`. A `sudo_executable` that does not exist gives `cannot reset the agent's home <home>: ` followed by the operating system's message.
7. The time limit (rows of one parametrized test): `FRESH_HOME_TIME_LIMIT` is 60 seconds. With the limit set to 3 seconds for the test (`monkeypatch.setattr` on the module) and `program` a stand-in that sleeps 60 seconds, run by the stand-in `sudo` through the real `timeout`, `reset` raises `AgentRuntimeError` whose `detail` is `cannot reset the agent's home <home>: no end within 3 s`, after at least 3 and less than 25 seconds; with a `program` that ends at once with status 0 under the same limit, `reset` returns.
8. `LOGIN_STATE_FILE` is `.claude/.credentials.json` in `factory.adapters.claude_runtime` and `.local/share/opencode/auth.json` in `factory.adapters.opencode_runtime`.
9. `agent_home_of` (rows of one parametrized test): settings with `agent_user="agent"`, `agent_home=/home/agent/.claude`, `claude_login_file=/home/agent/.claude-token`, `api_login_file=/home/agent/.anthropic-api-key` and `opencode_folders=[".config/sso"]`, with `/usr/bin/sudo`, give a `SudoAgentHome` whose `home` is `/home/agent`, `os_user` `agent`, `program` `fresh_home_command()` and `kept` `[".claude-token", ".anthropic-api-key", ".claude/.credentials.json", ".local/share/opencode/auth.json", ".cache/uv", ".config/sso"]`; with `api_login_file` `/run/key` (outside the home) `kept` lacks `.anthropic-api-key`; with `FACTORY_AGENT_RUNTIME` set to opencode the same `kept`; without `agent_user` the result is `None`.
10. `build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())` with `agent_user="agent"`: `boundaries.agent_home` is a `SudoAgentHome` equal in `home`, `kept`, `os_user` and `program` to `agent_home_of(settings, ...)`, and the `SealedProjectCommands` inside `boundaries.project_commands` holds that same object; with no `sudo` on `PATH`, it is built with `SUDO_EXECUTABLE`; without `agent_user`, `boundaries.agent_home` is `None`. `fresh_home_command()` is `[sys.executable, "-I", "-m", "factory.entry.fresh_home"]`, and `UV_CACHE_FOLDER` is `.cache/uv`.
11. The `Launch` that `reset` starts has `env` empty and a time limit of `FRESH_HOME_TIME_LIMIT` plus `SUDO_GRACE` (90 seconds by default), observed in one test through a seam of the tester's choice (the stand-in `sudo` may record its environment).
12. A call that the factory itself ended at its limit (`run_process` replaced through the seam of criterion 11 by one that returns `timed_out` true, `exit_status` `None`, standard error empty): `reset` raises `AgentRuntimeError` whose `detail` is `cannot reset the agent's home <home>: no end within 60 s`.
13. `make check` stays green.
14. docs: `docs/operator-guide.md`, *The agent runs as a second user*: the paragraph on the agent's home is rewritten. Before every agent run and every project command the factory runs `sudo -n -u agent -- timeout --signal=KILL 60s env -i /opt/factory/.venv/bin/python -I -m factory.entry.fresh_home --home /home/agent --keep ...` from `/`, which removes every file and folder `agent` made in `/home/agent`: the transcripts of earlier runs in `~/.claude/projects/`, `.claude.json`, opencode's sessions, the caches in `~/.cache` other than uv's and in `~/.semgrep`, and any `CLAUDE.md`, `rules/` or other file a run planted. It keeps the two mounted login files, `~/.claude/.credentials.json` and `~/.local/share/opencode/auth.json` (a login made by hand), the folders of `FACTORY_OPENCODE_FOLDERS` and uv's package cache `~/.cache/uv`, and it never touches the factory's own files. The last run's transcript stays until the next agent run or project command starts, for the operator to read: after a run that moves the work item forward, that is the stage's own checks right after it; after a run that asks, stalls or fails, it is the next run. A failure before an agent run stops it with `agent runtime failed: cannot reset the agent's home /home/agent: <line>` (at the preflight's agent-run probe, `preflight_failed`); before a project command it is `project command <command> failed: cannot reset the agent's home /home/agent: <line>` (a counted error at a stage, `preflight_failed` at the preflight's `lint` on `main`). The first reset after the upgrade removes what the volume `claude-home` gathered so far (on `self`, about 222 MB of transcripts); copy them out before the rebuild if you want them. The paragraphs on the manual login (the login is kept), on *What opencode keeps in the agent's home* (now: nothing but `auth.json` and the folders of `FACTORY_OPENCODE_FOLDERS` survives a run) and the `FACTORY_OPENCODE_FOLDERS` row of the settings table (a named folder is kept between runs, and a run can write it) say the same. A row in the morning observations: after a run that ended with a question (no checks follow it), `ls -A /home/agent/.claude` lists only the factory's files, the kept login and what that one run made; after a forward move and its checks, only the factory's files and the kept login. `docs/project-guide/agents.md`, *The fresh home*: who starts the program, when (after the seal, before the run, once per stage run, and before each project command), `AgentHome`, `SudoAgentHome`, its faults, the kept paths, `LOGIN_STATE_FILE` and `UV_CACHE_FOLDER`, and that the kept uv cache is the one thing a run leaves that a later run or check reads. `docs/project-guide/processes-and-checks.md`: `SealedProjectCommands`' `home`. `docs/project-guide/watching.md`, *Boundaries*: `Boundaries.agent_home` and `agent_home_of`. `docs/decisions.md`: a new entry *Every agent run and every project command starts from a fresh agent home*, dated with the story, with the reasons of the feature's decisions 8 to 13, and the sentence *The agent's home stays writable by the agent (L69) ... Left for v2* in the entry of 2026-10-16 marked closed by it.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run python - "$d" <<'EOF'
import sys
from pathlib import Path

from factory.adapters.agent_home import SudoAgentHome
from factory.domain.errors import AgentRuntimeError

d = Path(sys.argv[1])
home = d / "home"
(home / ".claude" / "projects").mkdir(parents=True)
(home / ".claude" / "CLAUDE.md").write_text("steer\n", encoding="utf-8")
(home / ".claude" / "projects" / "t.jsonl").write_text("{}\n", encoding="utf-8")
(home / ".claude-token").write_text("stand-in\n", encoding="utf-8")
sudo = d / "sudo"
sudo.write_text(f"#!{sys.executable}\nimport os, sys\nat = sys.argv.index('--')\nos.execvp(sys.argv[at + 1], sys.argv[at + 1:])\n", encoding="utf-8")
sudo.chmod(0o755)
program = [sys.executable, "-I", "-m", "factory.entry.fresh_home"]
SudoAgentHome(home, [".claude-token"], os_user="agent", sudo_executable=str(sudo), program=program).reset()
print(sorted(path.relative_to(home).as_posix() for path in home.rglob("*")))
try:
    SudoAgentHome(Path("relative"), [], os_user="agent", sudo_executable=str(sudo), program=program).reset()
except AgentRuntimeError as error:
    print(error.detail)
EOF
```
Expect: two lines, `['.claude-token']`, then `cannot reset the agent's home relative: factory-fresh-home: --home relative is not an absolute folder other than /`

```bash
uv run python - <<'EOF'
from pathlib import Path

from factory.domain.settings import InstanceSettings
from factory.entry.wiring import agent_home_of

settings = InstanceSettings(repository_url="/srv/project.git", instance="factory-1", agent_user="agent", agent_home=Path("/home/agent/.claude"), claude_login_file=Path("/home/agent/.claude-token"), api_login_file=Path("/home/agent/.anthropic-api-key"), opencode_folders=[".config/sso"])
home = agent_home_of(settings, "/usr/bin/sudo")
print(home.home if home else None, home.kept if home else None)
EOF
```
Expect: `/home/agent ['.claude-token', '.anthropic-api-key', '.claude/.credentials.json', '.local/share/opencode/auth.json', '.cache/uv', '.config/sso']`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: Questions (the format check passed; the Interface, architecture and scope otherwise fit, but these clauses have no criterion):

   1. Criterion 6 does not pin every clause of the `<line>` rule. The first row has a `FRESH_HOME_PREFIX` line after a non-prefix line, so that clause is covered. The second row has one line of standard error, so "the last non-blank line" cannot be told from "the first line", and nothing covers trailing blank lines or several lines where none starts with the prefix. Should I add a row of standard error `a`, `b`, a blank line, with the expected detail `...: b`? I would choose yes.
   2. The Interface says `reset` passes `env` `{}` and a call time limit of `FRESH_HOME_TIME_LIMIT` plus 30 seconds (`SUDO_GRACE`). Criterion 5 checks only the stand-in's arguments and working directory, so a wrong `env` or a wrong factory-side limit would pass every test. Should a criterion cover the `Launch` fields (`env` empty, time limit 90 s by default)? I would choose yes, one test function that calls `launch` with the same arguments and compares, or that observes the `run_process` call through an injected seam. Please name the seam.
   3. Criterion 9 says `kept` holds both runtimes' `LOGIN_STATE_FILE` "whatever the instance's runtime", but its table has no row with the opencode runtime. Should a row set `FACTORY_AGENT_RUNTIME` to opencode and expect the same `kept`? I would choose yes.
   4. Criterion 10 does not cover three Interface statements. `build_boundaries` uses "the sudo which finds, or `SUDO_EXECUTABLE`". Building starts no process. The criterion for the same object also lacks a case with no `sudo` found. Should I add a row with `sudo` absent from `PATH` and `SudoAgentHome` built with `SUDO_EXECUTABLE`? I would choose yes. The "starts no process" clause I would drop as untestable, unless you want it kept.
   5. Criterion 7's upper bound of 25 seconds is checkable, but the lower bound of 3 seconds with a 60-second sleeper relies on the real `timeout`. That is fine if `timeout` is in the test environment. Please confirm that `make check` machines have it. If not, say so.
4. 2026-10-20 human: Answers (2026-10-21):
   1. Yes: a row with standard error `a`, `b`, a blank line, expecting the detail `...: b`.
   2. Yes: one test pins the `Launch` fields, `env` empty and the call's time limit `FRESH_HOME_TIME_LIMIT` plus `SUDO_GRACE` (90 s by default). The seam is the tester's and the coder's choice; the stand-in `sudo` of the existing tests, which records its environment, may serve for `env`.
   3. Yes: a row with `FACTORY_AGENT_RUNTIME` set to opencode and the same `kept`.
   4. Yes: a row with no `sudo` on `PATH`, so `SudoAgentHome` is built with `SUDO_EXECUTABLE`. Drop "building starts no process" from the Interface.
   5. Confirmed: GNU `timeout` (coreutils 9.1) is at `/usr/bin/timeout` in the image where `make check` runs.
5. factory: started intake as self.
6. intake: accepted. I carried the human's answers (journal entry 4) into the story and changed nothing else.

   - Interface: it names concrete modules and signatures: `factory.application.agent_home`, `boundaries`, `sealed_runs`, `factory.adapters.agent_home`, the two `LOGIN_STATE_FILE` constants and `factory.entry.wiring`. Per answer 4, I removed "Building starts no process." from the `build_boundaries` bullet. Every behaviour stated there now has a criterion, including the `Launch` fields (answer 2).
   - Criteria: each is testable by one test function, and each rule has its failing side.
     - Criteria 2 to 4 cover the reset before the run, once per stage run, and the error that propagates and starts nothing.
     - Criterion 6 covers the `<line>` clauses. Per answer 1 I added a row with standard error `a`, `b` and a blank line, expecting `...: b`.
     - Criterion 7 covers both sides of the time limit.
     - Criterion 9 covers every kept path. Per answer 3 I added the opencode-runtime row, and the existing rows keep the `api_login_file` outside the home and the missing `agent_user`.
     - Criterion 10 now has a row with no `sudo` on `PATH`, built with `SUDO_EXECUTABLE` (answer 4).
     - New criterion 11 pins the `Launch` fields: empty `env` and a limit of `FRESH_HOME_TIME_LIMIT` plus `SUDO_GRACE` (answer 2). The seam is left to the tester. The closing criteria are renumbered 12 (`make check`) and 13 (`docs:`), and both stay last.
   - Smoke test: both blocks are runnable. They call no pytest, so the `-q` rule does not apply. Each `Expect:` line is checkable against the printed output. Answer 5 confirms GNU `timeout` is at `/usr/bin/timeout` in the image where `make check` runs, which criterion 7 relies on.
   - Architecture: `AgentHome` is an ABC in `application`, `SudoAgentHome` is in `adapters` and starts its process through `process`, and the wiring is in `entry`. The `tests/test_wrapper_search.py` leave is named, and decision 14 of the feature grants it.
   - Scope: the story is within the feature's Scope and Stories list (S0004) and touches nothing in its Out of scope.
7. factory: started tests as self.
8. tester: I wrote the tests for criteria 1 to 11. They are red on purpose: the three new test modules cannot import their modules yet, and the wrapper-search test now expects the new importer. `make lint` is green. I skipped the type check, as this stage allows.

   Criterion → test:
   - criterion 1: tests/adapters/test_sudo_agent_home.py::test_the_agent_home_interface_has_reset_alone_and_sudo_agent_home_implements_it
   - criterion 2: tests/application/test_agent_home_resets.py::test_the_home_is_reset_after_the_seal_and_before_the_run (row `reset-then-run`) and ::test_a_run_that_calls_the_runtime_twice_resets_the_home_once_before_the_first_call
   - criterion 3: tests/application/test_agent_home_resets.py::test_the_home_is_reset_after_the_seal_and_before_the_run (rows `reset-raises` and `no-home`). The raising home opens `.git` again before it raises. If `check_seal` were reached, `RepositoryUnsealed` would replace the `AgentRuntimeError`, so the test asserts the exact type.
   - criterion 4: tests/application/test_agent_home_resets.py::test_the_home_is_reset_after_the_seal_and_before_each_project_command
   - criterion 5: tests/adapters/test_sudo_agent_home.py::test_reset_runs_the_fresh_home_program_through_sudo_from_the_root_and_keeps_the_kept
   - criterion 6: tests/adapters/test_sudo_agent_home.py::test_a_failed_reset_raises_with_the_line_that_says_why. A missing `sudo` is one of its rows and expects `os.strerror(ENOENT)`.
   - criterion 7: tests/adapters/test_sudo_agent_home.py::test_a_reset_that_reaches_its_time_limit_raises
   - criterion 8: tests/entry/test_wiring_agent_home.py::test_each_runtime_names_the_login_it_keeps_in_the_home
   - criterion 9: tests/entry/test_wiring_agent_home.py::test_the_agent_home_of_the_settings_keeps_the_logins_the_uv_cache_and_the_folders. The opencode row sets `agent_runtime="opencode"` on the settings, which is the field `FACTORY_AGENT_RUNTIME` fills.
   - criterion 10: tests/entry/test_wiring_agent_home.py::test_the_built_boundaries_hold_one_agent_home_shared_with_the_project_commands and ::test_the_fresh_home_program_runs_with_this_interpreter_isolated_and_uv_s_cache_is_named
   - criterion 11: tests/adapters/test_sudo_agent_home.py::test_the_reset_call_has_no_environment_and_the_limit_plus_the_sudo_grace

   Seams the coder has to respect:
   - Criterion 11 replaces `factory.adapters.agent_home.run_process` with the shared `Recorder` (monkeypatch). So `factory.adapters.agent_home` must call `run_process` by that module-level name.
   - Criterion 10 uses the `which` parameter of `build_boundaries` for "no sudo on PATH", as tests/entry/test_wiring_project_command_user.py does.
   - The Interface gives no property for the sudo executable. So criterion 10 checks that the built `SudoAgentHome` holds the expected `sudo` string among `vars(...)`, and finds the shared object inside `SealedProjectCommands` the same way that existing test does.

   Files created:
   - tests/application/test_agent_home_resets.py. It reuses `ProbeCommands` and `PASSED` from tests/application/test_sealed_project_commands.py and `RecordingLog` from tests/application/test_checkout_preparer_seal.py, by import; I did not change either file.
   - tests/adapters/test_sudo_agent_home.py
   - tests/entry/test_wiring_agent_home.py

   Earlier test changed, under the leave the Interface names (the feature's decision 14): tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module now also expects `factory.adapters.agent_home`. Nothing else in it changed.

   Modules the test run could not import (collection errors): `factory.application.agent_home`, `factory.adapters.agent_home`, and the new names in `factory.entry.wiring` (`UV_CACHE_FOLDER`, `agent_home_of`, `fresh_home_command`). The `make test` run ended with the wrapper-search failure and these three collection errors, and nothing else failed.

   `lint`: lint: green (0.5 s)
   `test`: ERROR tests/entry/test_wiring_agent_home.py - ImportError while importing test module '/work/checkout/tests/entry/test_wiring_agent_home.py'.
9. factory: started doing as self.
10. factory: crash 1: the run of stage doing ended without a result. Its work is discarded back to commit 21fd3807889fa6bf762ec01334b91bf35bd687bc.
11. factory: started doing as self.
12. factory: crash 2: the run of stage doing ended without a result. Its work is discarded back to commit 4d52128a80c2fda680856cf61e34e6b71521ab75.
13. factory: Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
14. 2026-10-20 human: Note from the human's side (2026-10-21), for the coder and the reviewer: at 21:36 UTC this stage's tests left `src/factory/{,entry,domain,adapters}/__pycache__` at mode 755 (owner `agent`), and the factory's `git clean -X` after the run failed with `checkout_restore_failed` (repaired by hand). The cause is a child started as `[sys.executable, "-I", "-m", "factory.entry.fresh_home"]`: in the tests `sys.executable` is the checkout's Python, and `-I` ignores `PYTHONDONTWRITEBYTECODE`, so under the tests' umask 022 it writes bytecode into `src/`. Start the program with `-I -B` (the command this story builds, and any test that starts it), as F0027-S0004 did for the test helpers.
15. 2026-10-20 human: Rerun (2026-10-21). Both crashes were the restore's `git clean -X` failing on `src/**/__pycache__` written at mode 755 by a test child started with `-I` and no `-B`, which also discarded the run's uncommitted work. The checkout's folders now carry a default ACL that keeps new entries group-writable, so the restore no longer fails. Still start the program with `-I -B` (the command this story builds and any test that starts it), as the earlier note says.
16. factory: started doing as self.
17. coder: I built everything in the Interface, and `make check` is green against the tests as they stand now. But the human's notes (entries 14 and 15) ask that the fresh-home program start with `-I -B`, and two tests pin `-I` without `-B`. So I am sending the work item to the tests stage for one test change.

    **The test change:** in `tests/adapters/test_sudo_agent_home.py` and `tests/entry/test_wiring_agent_home.py`, add `"-B"` after `"-I"` wherever the fresh-home command is spelled out. That is three places: `PROGRAM`, the expected arguments in `test_reset_runs_the_fresh_home_program_through_sudo_from_the_root_and_keeps_the_kept`, and the expected `fresh_home_command()` in `test_the_fresh_home_program_runs_with_this_interpreter_isolated_and_uv_s_cache_is_named`. Nothing else changes.

    **What the journal changes:** the notes change the task's meaning. `fresh_home_command()` becomes `[sys.executable, "-I", "-B", "-m", "factory.entry.fresh_home"]`, and the same `-B` goes into the sudo command line in the Description, criteria 5, 10 and 13, and the smoke test's `program`. I tried to rewrite `## Description` to say so, but the work item is outside my write paths (`Permission denied`), so I left it alone; the next stage should carry this change into the Description. `fresh_home_command()` still builds `-I` only so that `make check` stays green. When the work item comes back, the change in the code is one word in `src/factory/entry/wiring.py`.

    **What I built:**
    - `src/factory/application/agent_home.py`: the `AgentHome` interface.
    - `src/factory/adapters/agent_home.py`:
      - `SudoAgentHome` and `FRESH_HOME_TIME_LIMIT`.
      - `reset` builds the call through `launch`, starts it through the module-level `run_process` from `/`, and reads the limit at each call.
      - Faults: the `FRESH_HOME_PREFIX` line, else the last non-blank line, else `exit status <n>`. A kill at the limit (`timed_out` or `killed_at_limit`) gives `no end within <s> s`. An `OSError` gives its `strerror`.
    - `LOGIN_STATE_FILE` in `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py`.
    - `Boundaries.agent_home`, last, in `src/factory/application/boundaries.py`.
    - In `src/factory/application/sealed_runs.py`:
      - `run_sealed` resets after `git.seal()` and before the `try`, so a failed reset neither starts the run nor checks the seal.
      - `SealedProjectCommands` takes `home` and turns an `AgentRuntimeError` into `ProjectCommandError(command, detail)` before the command runs.
    - In `src/factory/entry/wiring.py`: `FRESH_HOME_MODULE`, `UV_CACHE_FOLDER`, `fresh_home_command`, and `agent_home_of`, which uses the existing `kept_paths` from `factory.domain.agent_home`. `build_boundaries` builds the home once and gives the same object to `Boundaries` and to `SealedProjectCommands`. `_project_commands` takes it as a keyword-only argument (ruff's PLR0917).

    **Main choice:** the reset in `run_sealed` and in `SealedProjectCommands.run` comes before the `try`/`finally`, not inside it. A failed reset ran nothing, so there is no seal to check and nothing to clean up afterwards, which is what the Interface says. I rejected putting it inside the `try`: in the test where the home opens `.git` before it raises, the seal check would then raise `RepositoryUnsealed` and hide the reset's error. For the error line I wrote a small `_failure_line`. I did not reuse `make_commands._last_line`, because it filters out make's own messages, which this rule must not do.

    **Refactor:** I read my diff once and found nothing to change.

    **Noticed, not touched:** the tests' `PROGRAM` currently starts the real program with `-I` and no `-B`. Until the test change lands, `make test` can still write `__pycache__` into `src/`. The checkout's new default ACL keeps that from breaking the restore.
18. factory: started tests as self.
19. tester: tester (a test change the human approved): I made the test change that the coder named in journal entry 17. It follows the human's notes in entries 14 and 15, which say the fresh-home program starts with `-I -B`. I added `"-B"` after `"-I"` in the three places where the tests spell out the command, and nothing else changed:
    - `tests/adapters/test_sudo_agent_home.py`, line 24: `PROGRAM` is now `[sys.executable, "-I", "-B", "-m", "factory.entry.fresh_home"]`. Tests that start the real program no longer write `__pycache__` into `src/`.
    - `tests/adapters/test_sudo_agent_home.py::test_reset_runs_the_fresh_home_program_through_sudo_from_the_root_and_keeps_the_kept`: `"-B"` now follows `"-I"` in the expected sudo arguments (line 123).
    - `tests/entry/test_wiring_agent_home.py::test_the_fresh_home_program_runs_with_this_interpreter_isolated_and_uv_s_cache_is_named`: it now expects `fresh_home_command()` to be `[sys.executable, "-I", "-B", "-m", "factory.entry.fresh_home"]`.

    `make test` has one failure, and it is the expected one: `test_the_fresh_home_program_runs_with_this_interpreter_isolated_and_uv_s_cache_is_named` fails because `src/factory/entry/wiring.py` still builds `-I` without `-B`. That one-word change is the coder's to make. All other tests pass and coverage is 99.14 %. `make lint` is green.

    Still open: the `## Description` (sudo command line, criteria 5, 10 and 13, and the smoke test's `program`) still says `-I` without `-B`. I did not edit it, because this mode allows only the named test change. A stage that may write the work item should add `-B` there.

    Files changed: `tests/adapters/test_sudo_agent_home.py` and `tests/entry/test_wiring_agent_home.py`, both written by this story's tests stage. No new files. Every module imported in the test run.

    `lint`: lint: green (0.5 s)
    `test`: FAILED tests/entry/test_wiring_agent_home.py::test_the_fresh_home_program_runs_with_this_interpreter_isolated_and_uv_s_cache_is_named - AssertionError: assert ['/work/check...y.fresh_home'] == ['/w...
20. factory: started doing as self.
21. coder: I made the one-word change that was still open in the code. `fresh_home_command()` in `src/factory/entry/wiring.py` now returns `[sys.executable, "-I", "-B", "-m", "factory.entry.fresh_home"]`, as the human's notes (entries 14 and 15) ask. The tester has already changed the tests to match (entry 19). I added a comment saying why the `-B` is there: `-I` ignores `PYTHONDONTWRITEBYTECODE`, so without `-B` the agent's user writes bytecode into `src/`, and the restore cannot remove it. `make check` is green: coverage is 99.14 % and `check: green`. `git status` shows no `__pycache__` under `src/`.

    Everything else in this story was built in entry 17 and is unchanged: `src/factory/application/agent_home.py`, `src/factory/adapters/agent_home.py`, `LOGIN_STATE_FILE` in `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py`, `Boundaries.agent_home` in `src/factory/application/boundaries.py`, the resets in `src/factory/application/sealed_runs.py`, and `agent_home_of` and `build_boundaries` in `src/factory/entry/wiring.py`.

    Main choice (from entry 17, kept): the reset comes before the `try`/`finally` in `run_sealed` and in `SealedProjectCommands.run`, not inside it. A reset that fails has run nothing, so there is no seal to check. I rejected putting it inside the `try` because the seal check would then hide the reset's own error.

    Refactor: I read the diff once more and found nothing to change.

    What the journal changed: entries 14 and 15 add `-B` to the command. The sudo command line in `## Description`, criteria 5, 10 and 13, and the smoke test's `program` still say `-I` without `-B`. The work item is outside my write paths, so I left it as it is; a stage that may write it should add `-B` there.

    Noticed, not touched: `leftovers_command()` in the same file also starts its program with `-I` and no `-B`, so it could write bytecode into `src/` the same way. That is outside this story.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 33 known, 3 gone
22. factory: started review as self.
23. reviewer: Review, round 0. I read the work item and `git diff main...HEAD -- . ':!factory'`. Groups 2 to 4 hold. The layers are respected. `AgentHome` is an ABC whose body is its docstring alone. `SudoAgentHome` reaches its process only through `launch` and `run_process`, under the leave of the feature's decision 14. There are no silencing markers. No existing helper covers `_failure_line` (`make_commands._last_line` filters make's own lines, and `hosting.parse_post_key` parses a key). Criteria 1 to 11 each have a passing test that checks what the criterion says. Group 1 fails on two points:

    1. `src/factory/adapters/agent_home.py:80` (`result.timed_out or killed_at_limit(...)`): the Interface names two ways a call reaches its limit, "the factory's kill, or `killed_at_limit`". Criterion 7 tests only the agent's own `timeout`. Nothing tests the factory's kill (`timed_out` true). That is a gap in the story, and it needs no change under `src/`. criterion 12 added: it needs its test. It uses the `run_process` seam of criterion 11, returning `timed_out` true, `exit_status` `None` and empty standard error, and expects `cannot reset the agent's home <home>: no end within 60 s`. The closing criteria are now numbered 13 (`make check`) and 14 (`docs:`).
    2. The work item's `## Interface` (`fresh_home_command()` is `[sys.executable, "-I", "-m", FRESH_HOME_MODULE]`), criteria 5 and 10, docs criterion 14 (`... python -I -m factory.entry.fresh_home ...`) and the first smoke test's `program` still give the command as `-I` without `-B`. The human's entries 14 and 15 changed the command to `-I -B`, and the code (`src/factory/entry/wiring.py:340`) and the tests follow them. As it stands, the documenter would write the wrong command into the operator guide, and the smoke test would start the program without `-B`. Fix: add `-B` after `-I` in those five places. The coder cannot write the work item (entries 17 and 21), so the next review round should make this correction, or the human should, unless the human says otherwise. The Description correction below is the only part I could make myself.

    description corrected: `... env -i <python> -I -m factory.entry.fresh_home ...` -> `... env -i <python> -I -B -m factory.entry.fresh_home ...` from `/` (`-B`, so the agent's user writes no bytecode beside the factory's source: `-I` ignores `PYTHONDONTWRITEBYTECODE`). This follows the human's entries 14 and 15.

    Earlier tests:
    - tests/test_wrapper_search.py: the human's leave, the feature's decision 14, named in the story's Interface. The only change adds `factory.adapters.agent_home` to the expected importers, which is within that leave.
24. factory: started doing as self.
25. coder: Round 1. The reviewer added criterion 12 (entry 23, finding 1). It needs only a test, so I changed no code and am sending the work item to the tests stage.

    **The test to write:** add one test to `tests/adapters/test_sudo_agent_home.py` for criterion 12, the factory's own kill at the limit:
    - Replace `factory.adapters.agent_home.run_process` through the same seam criterion 11 uses (monkeypatch with the shared `Recorder`). Make it return `timed_out` true, `exit_status` `None` and empty standard error.
    - Expect `reset` to raise `AgentRuntimeError` whose `detail` is `cannot reset the agent's home <home>: no end within 60 s`.

    The code already covers this case: `src/factory/adapters/agent_home.py:80` checks `result.timed_out or killed_at_limit(...)`. Today no test reaches the `timed_out` side. I checked: the file's test functions cover criteria 1, 5, 6, 7 and 11, and none returns `timed_out` true.

    **Finding 2** (`-B` is missing in the work item's `## Interface`, criteria 5 and 10, the docs criterion and the first smoke test's `program`): this needs no change to code or tests. The code (`src/factory/entry/wiring.py`, `fresh_home_command()`) and the tests already use `-I -B`. The fix is in the work item, which is outside my write paths (entries 17 and 21), so I did not touch it. A stage that can write the work item, or the human, should add `-B` after `-I` in those five places.

    **What the journal changed:** criterion 12 is new, and the closing criteria are now 13 and 14. The reviewer already carried both into the Description.

    **Not run:** I did not run `make check` this round because nothing in the working tree changed. The last green run is entry 21's.

    **Built earlier and unchanged:**
    - `src/factory/application/agent_home.py`
    - `src/factory/adapters/agent_home.py`
    - `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py` (`LOGIN_STATE_FILE`)
    - `src/factory/application/boundaries.py`
    - `src/factory/application/sealed_runs.py`
    - `src/factory/entry/wiring.py`

    The main choice, kept from entry 17: the reset comes before the `try`/`finally`, so a failed reset neither starts the run nor checks the seal. I rejected putting it inside the `try`, because the seal check could then hide the reset's own error.

    **Noticed, not touched:** `leftovers_command()` in `src/factory/entry/wiring.py` still starts its program with `-I` and no `-B`. That is outside this story.
26. factory: started tests as self.
27. tester: Test change the human approved (coder's entry 25): I wrote the test for criterion 12, which the reviewer added in entry 23. It needed only a test, no code change.

    - criterion 12: `tests/adapters/test_sudo_agent_home.py::test_a_reset_the_factory_ended_at_its_limit_raises`. It replaces `factory.adapters.agent_home.run_process` with the shared `Recorder`, which returns `timed_out` true, `exit_status` `None` and empty standard error. It expects `AgentRuntimeError` with the detail `cannot reset the agent's home <home>: no end within 60 s`.

    The criterion-11 test (`test_the_reset_call_has_no_environment_and_the_limit_plus_the_sudo_grace`) set up the same seam, so I moved that setup into a new fixture, `recorder`, in the same file. That test keeps its name and still checks the same thing. This story's tests stage wrote that file, so no other story's test was touched.

    `make test` is green: the test passes as soon as it is written, because `src/factory/adapters/agent_home.py:80` already handles `result.timed_out`. Coverage is 99.14 %. `make lint` is green.

    Files changed: `tests/adapters/test_sudo_agent_home.py`. No files created. Every module imported in the test run.

    Still open (reviewer's finding 2): the work item still says `-I` without `-B` in five places: the `## Interface` (`fresh_home_command()`), criteria 5 and 10, docs criterion 14, and the first smoke test's `program`. This mode lets me make only the named test change, so I left them as they are. The next review round or the human should correct them.

    `lint`: lint: green (0.6 s)
    `test`: test: green (62.2 s)
28. factory: started doing as self.
29. coder: Round 1, after the tester's entry 27. Both findings from the reviewer's entry 23 are now dealt with, and no code changed this round.

    - **Finding 1:** the test for criterion 12 is `tests/adapters/test_sudo_agent_home.py::test_a_reset_the_factory_ended_at_its_limit_raises`. It passes against the existing branch in `src/factory/adapters/agent_home.py`, which checks `result.timed_out or killed_at_limit(...)`. Nothing in the source needed to change.
    - **Finding 2:** this is a fix to the work item's text, not to code or tests. The code (`fresh_home_command()` in `src/factory/entry/wiring.py`) and the tests already use `-I -B`. Five places in the work item still have `-I` without `-B`: the `## Interface` bullet for `fresh_home_command()`, criteria 5 and 10, docs criterion 14, and the first smoke test's `program`. Earlier coder runs got `Permission denied` when writing the work item (entries 17 and 21), so I left it alone. As the reviewer suggested, the next review round or the human should add `-B` after `-I` in those five places before the documenter writes the operator guide from criterion 14.

    What the story built is unchanged since entries 17 and 21:
    - `src/factory/application/agent_home.py`
    - `src/factory/adapters/agent_home.py`
    - `LOGIN_STATE_FILE` in `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py`
    - `Boundaries.agent_home` in `src/factory/application/boundaries.py`
    - the resets in `src/factory/application/sealed_runs.py`
    - `FRESH_HOME_MODULE`, `UV_CACHE_FOLDER`, `fresh_home_command`, `agent_home_of` and `build_boundaries` in `src/factory/entry/wiring.py`

    The main choice is unchanged: the reset happens before the `try`/`finally`, so a failed reset never starts the run and never checks the seal. I rejected putting it inside the `try`, because there the seal check (`RepositoryUnsealed`) would hide the reset's own error.

    Refactor: there was nothing new to read, and nothing needed changing.

    What the journal changed: criterion 12 is new and the closing criteria are now 13 and 14. The reviewer already carried this into the Description. The `-B` correction is still open, as described above.

    Noticed but not touched: `leftovers_command()` in `src/factory/entry/wiring.py` still starts its program with `-I` and no `-B`, so it can write bytecode into `src/` the same way. That is outside this story.

    `check`: check: green (coverage 99.14 %)

    `check`: check: green
    `duplicates`: duplicates: 6 new, 33 known, 3 gone
