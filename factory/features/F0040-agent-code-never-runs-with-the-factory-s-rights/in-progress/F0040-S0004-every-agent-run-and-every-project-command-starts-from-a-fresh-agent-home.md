---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 365
comments_read: [6301863943]
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
---

# Every agent run and every project command starts from a fresh agent home

## Description

S0003 built the program that clears the agent's home of what the agent made. This story starts it, as the agent's user, before every agent run and before every project command, so that no run reads what an earlier one did (its transcripts, opencode's sessions) and no run finds a file an earlier one planted (a user `CLAUDE.md`, a `rules/` folder, a cache other than uv's). A new application interface, `AgentHome`, has one operation, `reset`. Its implementation, `SudoAgentHome`, runs `sudo -n -u <agent> -- timeout --signal=KILL 60s env -i <python> -I -m factory.entry.fresh_home --home /home/agent --keep <path>...` from `/`, built by `launch` as an agent run's call is, so the agent's own `timeout` ends it at 60 seconds, and raises `AgentRuntimeError` when the program fails, so no run starts in a home the factory could not clear. `run_sealed` resets the home after the seal and before the run, once per stage run: a run resumed after a provider limit or its budget keeps its session, because those resumes happen inside the one run. The preflight's probe goes through `run_sealed` and is reset the same way. `SealedProjectCommands` (S0002) resets the home after the seal and before each command, so a check never runs in what the agent run before it left. The kept paths are the two login files the image mounts (`FACTORY_CLAUDE_LOGIN_FILE`, `FACTORY_API_LOGIN_FILE`), the login each runtime keeps in the home when an operator logged in by hand (Claude Code's `~/.claude/.credentials.json`, opencode's `~/.local/share/opencode/auth.json`), the folders of `FACTORY_OPENCODE_FOLDERS`, and uv's package cache `~/.cache/uv` (`UV_CACHE_FOLDER`), which the agent's user writes in runs and project commands and which every later run and check reads: a small channel from one run to the next check that the human accepted (the feature's decision 9). The factory's own files there (agents, `settings.json`, `skills/`, `commands/`, `.config/opencode`) are not the agent's and stay. Without an agent user nothing is reset, as nothing runs as a second user. The image, the entrypoint, the compose file and the volume `claude-home` stay as they are.

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
12. `make check` stays green.
13. docs: `docs/operator-guide.md`, *The agent runs as a second user*: the paragraph on the agent's home is rewritten. Before every agent run and every project command the factory runs `sudo -n -u agent -- timeout --signal=KILL 60s env -i /opt/factory/.venv/bin/python -I -m factory.entry.fresh_home --home /home/agent --keep ...` from `/`, which removes every file and folder `agent` made in `/home/agent`: the transcripts of earlier runs in `~/.claude/projects/`, `.claude.json`, opencode's sessions, the caches in `~/.cache` other than uv's and in `~/.semgrep`, and any `CLAUDE.md`, `rules/` or other file a run planted. It keeps the two mounted login files, `~/.claude/.credentials.json` and `~/.local/share/opencode/auth.json` (a login made by hand), the folders of `FACTORY_OPENCODE_FOLDERS` and uv's package cache `~/.cache/uv`, and it never touches the factory's own files. The last run's transcript stays until the next agent run or project command starts, for the operator to read: after a run that moves the work item forward, that is the stage's own checks right after it; after a run that asks, stalls or fails, it is the next run. A failure before an agent run stops it with `agent runtime failed: cannot reset the agent's home /home/agent: <line>` (at the preflight's agent-run probe, `preflight_failed`); before a project command it is `project command <command> failed: cannot reset the agent's home /home/agent: <line>` (a counted error at a stage, `preflight_failed` at the preflight's `lint` on `main`). The first reset after the upgrade removes what the volume `claude-home` gathered so far (on `self`, about 222 MB of transcripts); copy them out before the rebuild if you want them. The paragraphs on the manual login (the login is kept), on *What opencode keeps in the agent's home* (now: nothing but `auth.json` and the folders of `FACTORY_OPENCODE_FOLDERS` survives a run) and the `FACTORY_OPENCODE_FOLDERS` row of the settings table (a named folder is kept between runs, and a run can write it) say the same. A row in the morning observations: after a run that ended with a question (no checks follow it), `ls -A /home/agent/.claude` lists only the factory's files, the kept login and what that one run made; after a forward move and its checks, only the factory's files and the kept login. `docs/project-guide/agents.md`, *The fresh home*: who starts the program, when (after the seal, before the run, once per stage run, and before each project command), `AgentHome`, `SudoAgentHome`, its faults, the kept paths, `LOGIN_STATE_FILE` and `UV_CACHE_FOLDER`, and that the kept uv cache is the one thing a run leaves that a later run or check reads. `docs/project-guide/processes-and-checks.md`: `SealedProjectCommands`' `home`. `docs/project-guide/watching.md`, *Boundaries*: `Boundaries.agent_home` and `agent_home_of`. `docs/decisions.md`: a new entry *Every agent run and every project command starts from a fresh agent home*, dated with the story, with the reasons of the feature's decisions 8 to 13, and the sentence *The agent's home stays writable by the agent (L69) ... Left for v2* in the entry of 2026-10-16 marked closed by it.

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
