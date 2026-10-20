# Paths the group cannot write after `make test` as `agent` (2026-10-20)

Status: investigation only. Nothing in the repository was changed and nothing was committed.
The note describes main at `e19ac233`.

## The question

Since F0027-S0003 the factory runs `git clean -ffdX` as the user `factory` after every agent run
and at the restore. Twice today (15:38 and 16:45 UTC) the instance stopped with
`checkout_restore_failed`. In both cases the only paths were
`.venv/lib/python3.12/site-packages/__pycache__/` (`drwxr-sr-x agent`) and
`_virtualenv.cpython-312.pyc` inside it (`-rw-r--r-- agent`), each time during an
acceptance-reviewer's run. Which process writes them, and how do we stop it?

## Short answer

The writer is the test suite, run by the acceptance-reviewer itself. Its instructions tell it to
run `make check` at the start of its work (R11 and step 1 of its run), and `make check` ends with
`make test`. Inside the suite, a group of tests starts a stand-in program whose first line is
`#!{sys.executable}` (the checkout's `.venv` Python), with an environment that the code under test
or the test itself replaces completely. PYTHONDONTWRITEBYTECODE is then missing. At start-up, that
Python processes `_virtualenv.pth` and imports `_virtualenv`, so it writes
`site-packages/__pycache__/_virtualenv.cpython-312.pyc`. The test process runs under the umask
`0o022` that `tests/conftest.py` sets (F0033), so the folder is created as `drwxr-sr-x`. The
factory's `git clean` cannot remove a file inside a folder the group cannot write, so it fails.

The modes are the signature of this cause. An agent shell runs under umask 0002 (checked below), and
under that umask the folder would have been `drwxrwsr-x`, which `git clean` can empty. Only a process
under umask 022, which here means pytest after `conftest.py` has run, produces `drwxr-sr-x`.

Three lines in the test helpers explain all of it. If each gets `-B`, the full suite leaves nothing
that `git clean` cannot remove (verified below).

## How it was reproduced

- I made a copy of HEAD with `git -c core.autocrlf=false archive` (without `image/secrets`).
- I used throwaway containers of the image `factory-self-factory:latest`, one at a time, with
  `--cpus 8`. The running instance and its `.venv` were not touched.
- The checkout was `/work/fr` on a Docker volume. `/work` was setgid and owned by
  `factory:factory-work`.
- As `factory` under umask 002, I extracted the copy, ran `git init` with one commit, and ran
  `uv sync`. Network was used only to fill the uv cache once. Every later container ran with
  `--network none` and did a fresh `uv sync --offline`.
- I ran `make test` as `agent` through `sudo -n -u agent -- env -i PATH=... HOME=/home/agent
  LANG=C.UTF-8 PYTHONDONTWRITEBYTECODE=1 CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
  CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1 bash -c 'umask 002; make test'`. This is the agent
  runtime's environment.

The full run gave this result. `make test` was green (99.17 % coverage, 95 s). Afterwards
`find . -path ./.git -prune -o ! -perm -g+w` showed these paths:

```
drwxr-sr-x agent ./.venv/lib/python3.12/site-packages/__pycache__
-rw-r--r-- agent ./.venv/lib/python3.12/site-packages/__pycache__/_virtualenv.cpython-312.pyc
-rw-r--r-- agent ./.reports/junit.xml
-rw-r--r-- agent ./.reports/.coverage
```

`git clean -ffdX` as `factory` then failed:
`warning: failed to remove .venv/lib/python3.12/site-packages/__pycache__/_virtualenv.cpython-312.pyc: Permission denied`
(exit 1). This is exactly the instance's stop.

The two `.reports/` files are not a problem. Removing a file needs write permission on its folder,
not on the file, and `.reports/` itself was created by `make` under umask 002 (group-writable).
`git clean` removed them. Only a non-empty folder that the group cannot write blocks the clean.

## Bisection

I ran each of the 117 test modules alone, each in a fresh, freshly synced checkout. Thirteen modules
leave the folder, all in `tests/adapters/`:

| Module | Tests that write (run one by one) |
|---|---|
| `test_agent_launch_login.py` | all 8 cases of the two login-shell tests |
| `test_claude_runtime_api_login.py` | `..._no_result[user]` |
| `test_claude_runtime_confinement.py` | 7 tests with a user (sudo stand-in) |
| `test_claude_runtime_leftovers.py` | all 9 |
| `test_claude_runtime_login.py` | the 3 cases with a user |
| `test_claude_runtime_os_user.py` | 8 tests with a user |
| `test_claude_runtime_sudo_time_limit.py` | all 4 |
| `test_opencode_confinement.py` | `..._removed_through_sudo` |
| `test_opencode_runtime_launch.py` | 6 tests with an agent user |
| `test_opencode_runtime_leftovers.py` | all 5 |
| `test_opencode_sudo_time_limit.py` | all 4 |
| `test_process.py` | `test_given_env_is_the_whole_environment` |
| `test_process_streaming.py` | `test_child_starts_as_run_process_starts_it[environment]` |

In total, 59 single tests write the file. Any one of them is enough, because the first writer
creates the folder.

## The causes, with exact lines

### 1. The `sudo` stand-in, started with an empty environment (most of the list)

The production code starts `sudo` with `env={}`. That is correct: `env -i` follows `sudo`, and the
switches, PYTHONDONTWRITEBYTECODE among them, are handed to the agent after `env -i`. See
`src/factory/adapters/agent_launch.py` 216-224 (`launch`), 350-355 (`leftovers_launch`) and
410 (`cleanup_launch`). In the tests, though, `sudo` is a stand-in Python script, and its own
interpreter starts with nothing in its environment:

- `tests/adapters/test_claude_runtime_os_user.py:81`
  `path.write_text(f"#!{sys.executable}\n{SUDO_SCRIPT}", ...)`. This is `_write_sudo`, which
  `test_claude_runtime_api_login`, `_login`, `_sudo_time_limit`, `test_opencode_confinement`,
  `test_opencode_runtime_launch` and `test_opencode_sudo_time_limit` import.
- `tests/confine_support.py:114`
  `path.write_text(f"#!{sys.executable}\n{script}", ...)` in `write_script`. This writes the
  `sudo` stand-ins of `test_claude_runtime_confinement.py:185` and
  `tests/leftovers_runtime_support.py:89`, the leftovers program stand-in
  (`leftovers_runtime_support.py:81`) and the probe and confine stand-ins.

The agent stand-in behind `env -i` is not the writer, because it gets the switches.

### 2. The login shell's command, with a narrow test environment

`tests/adapters/test_agent_launch_login.py:58-67` (`_launch`) writes its command with
`write_script` (the same `confine_support.py:114`). It runs the command through the login shell
with `env={"PATH": ..., API_LOGIN_VARIABLE: ..., LOGIN_VARIABLE: ...}`, which has no
PYTHONDONTWRITEBYTECODE.

### 3. `python -c` with a replaced environment

`tests/process_support.py:29` `return [sys.executable, "-c", code, *args]`. This is `python_argv`,
and two tests use it with a whole replacement environment:

- `tests/adapters/test_process.py:66` with `env={"FACTORY_TEST_GIVEN": "given"}`
- `tests/adapters/test_process_streaming.py:262-267` with the parameter `environment`, which has
  the same environment.

## The smallest fix

Add `-B` in three places. Linux passes one argument on a `#!` line, so `#!/path/python -B` works.

1. `tests/confine_support.py:114`: `f"#!{sys.executable} -B\n{script}"`
2. `tests/adapters/test_claude_runtime_os_user.py:81`: `f"#!{sys.executable} -B\n{SUDO_SCRIPT}"`
3. `tests/process_support.py:29`: `[sys.executable, "-B", "-c", code, *args]`

I verified this. With these three edits in a fresh copy, the full `make test` as `agent` was green
(99.17 %). Only the two harmless `.reports/` files lacked group write, and `git clean -ffdX` as
`factory` exited 0.

Adding PYTHONDONTWRITEBYTECODE to each child's environment would also work for cause 3. It does not
work for causes 1 and 2, because there the empty or narrow environment is what the tests check.
`-B` is independent of the environment, so it is the better fix everywhere.

For robustness, the same `-B` could also go on the other `#!{sys.executable}` writers that do not
leak today because their environment still carries the variable:
`tests/adapters/claude_stand_in.py:83`, `tests/adapters/opencode_stand_in.py:83` and `:270`,
`test_claude_runtime_file_modes.py:52`, `test_claude_runtime_provider_limit.py:164`,
`git_support.py:165`, and the two git hooks in `test_git_cli_branches.py:104` and
`test_git_cli_writing.py:290`. This is optional.

A related note on production, not on the checkout: `src/factory/entry/wiring.py:296` starts the
leftovers program as `[sys.executable, "-I", "-m", ...]`. `-I` ignores PYTHONDONTWRITEBYTECODE,
and its interpreter is `/opt/factory/.venv`, so it can only write there, and only if that venv is
writable by the agent. `tests/entry/test_leftovers.py:213` already uses `-I -B`. Adding `-B` in
wiring.py, and in `COMMAND` of `tests/entry/test_wiring_leftovers.py:14`, would make the two
agree. This is not needed for the stop.

## The coordinator's clue: an agent-start process?

The 16:45 files were written about a minute after the reviewer's start (16:44:37). This fits the
test suite. The reviewer runs `make check` early. `lint`, `types`, `layers`, `sast`, `secrets` and
`licenses` take tens of seconds, then `test` starts, and the stand-in tests run within its first
seconds.

I checked the launch chain itself in a throwaway container. It was `factory` under umask 002, then
`sudo -n -u agent -- timeout --signal=KILL 30s env -i PATH=... HOME=/home/agent
PYTHONDONTWRITEBYTECODE=1 <script>`. The results:

- In the agent's process, the umask is 0002. The sudoers file `umask=0002` and `umask_override`
  take effect.
- The umask is also 0002 in a login shell (`bash -l`) and in an interactive shell (`bash -i`).
  `/home/agent/.profile` only has `#umask 022` as a comment, and `/etc/profile` sets none.
- PYTHONDONTWRITEBYTECODE=1 reaches the agent's process.

So nothing at the start of the run creates a folder under umask 022. A writer there would leave
`drwxrwsr-x`, which does not block the clean. I did not start a real `claude -p` (it needs a login).
Claude Code's Bash tool inherits the process's umask and environment, and nothing shown here
suggests it changes them. The modes on the instance point to pytest under the conftest umask.

## Would `UV_COMPILE_BYTECODE` or a Makefile export help?

- **A Makefile export** of `PYTHONDONTWRITEBYTECODE=1` does not help. The agent's environment
  already has it. The leaking children are exactly the ones whose environment is replaced
  (`env={}` or a test's own dict), so an exported variable never reaches them.
- **`UV_COMPILE_BYTECODE=1`** on the factory's `uv sync` would hide this case. I tried it. The sync
  created `site-packages/__pycache__/` as `drwxrwsr-x factory` with `_virtualenv.cpython-312.pyc`
  inside. After the writer tests ran as `agent`, `git clean` exited 0: the bytecode was already
  fresh, and the folder is group-writable anyway. It does not remove the cause, though. Any test
  that imports another module of the venv without `-B` could still create a new `__pycache__`
  folder under umask 022. It also compiles every installed package on each sync. I would use `-B`,
  not this.

## A structural test to keep it from coming back (sketch only)

There are two options, and the cheap one is enough.

1. **A text rule (cheap).** A test that reads every `tests/**/*.py` and fails on two patterns:
   `#!{sys.executable}` not followed by ` -B`, and an argv literal that starts with
   `sys.executable` and lacks `"-B"` in the next few words. A better way is to have one helper
   (for example `python_shebang()` in a shared support module) and forbid the literal elsewhere.
   This catches the pattern, not the effect.
2. **A guard on the effect.** A `pytest_sessionfinish` hook in `tests/conftest.py`, active only
   when PYTHONDONTWRITEBYTECODE was set at session start (as in the factory), that fails the run
   if a `__pycache__` folder appeared during the session under the checkout or under
   `sysconfig.get_paths()["purelib"]`. The hook records the existing folders in
   `pytest_sessionstart`. Under xdist it must run in the controller only. This catches any
   future writer, whatever its form, at the cost of a walk over `.venv` at the start and end.
