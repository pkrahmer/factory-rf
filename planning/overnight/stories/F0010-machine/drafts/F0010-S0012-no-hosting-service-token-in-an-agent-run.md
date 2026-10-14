# No hosting-service token in an agent run

## Assignment (as of log entry 1)

Keep the hosting-service token out of every agent run. The token lives in one file that only the factory's own user can read; the factory process reads it once (the boundaries story) and hands it to PyGithub, and git gets it from a credential helper that reads the same file and fails for anyone who cannot, reached through `GitOptions.environment` only (the boundaries story). The environment of an agent run is made from an allow list at its source, `production_environment()` of F0006-S0007, so nothing the factory process holds reaches it besides the allowed names; `TaskComposer` passes the environment it is given unchanged, as F0005 decision 23 has it. The factory's own pushes and posts keep working. This covers WE3.2 and WE3.5, implements R33 and keeps kept thing 5's rule that agents do not push, switch branches or call the hosting service. WE3.3 and WE3.4 are covered here by tests of the files and of the helper plus a morning observation: a real agent run that tries to read the token file and the token, to run `git -C . push origin main` and to call the API, all of which must fail, needs Docker and a second operating-system user, which v1's container does not have. The second user itself, and the call that runs the agent as that user (WE3.1), are the next stories. The project commands (`make check`, `lint`, `test`, and the preflight's `lint`) run code that agents wrote, as the factory's user, who can read the token file: a test can print the token into the output tail that the factory writes into the journal. The human decided on 2026-10-14 that this is not built now; it is left for v2 and recorded in `docs/decisions.md` and the operator guide (the docs criterion). The human also added `image/secrets/` to `.gitignore`, so the token file there is ignored by git. If `make secrets` flags a line of this story's files, rephrase the line; a new entry in the secrets baseline is not allowed.

## Interface

`src/factory/domain/agent_runs.py` (extends the module)

```python
ALLOWED_ENVIRONMENT_NAMES: frozenset[str] = frozenset({"PATH", "HOME", "LANG", "LC_ALL", "TERM", "TZ"})

def scrub_environment(source: Mapping[str, str]) -> dict[str, str]: ...
```

`src/factory/entry/wiring.py` (extends F0006-S0007's `production_environment`)

```python
def production_environment() -> dict[str, str]: ...
    # scrub_environment({**os.environ, **agent_environment(Path(sys.executable).parent, Path.home())})
```

`src/factory/application/preflight.py` (extends the module)

```python
def token_file_item(
    path: Path | None, *, uid: int, stat: Callable[[Path], os.stat_result]
) -> PreflightItem: ...
```

`image/git-credential-factory` is a POSIX `sh` script, git's credential helper. `image/Dockerfile` and `image/compose.yml` gain the lines below, inserted before the Dockerfile's `RUN` that writes `/opt/factory/image-id` (which stays after the last `COPY`, F0010-S0005 criterion 12), and into the compose service:

```dockerfile
COPY image/git-credential-factory /usr/local/bin/git-credential-factory
RUN chmod 0755 /usr/local/bin/git-credential-factory
ENV FACTORY_TOKEN_FILE=/run/secrets/hosting-token
```

```yaml
    secrets:
      - source: hosting_token
        target: hosting-token
        uid: "1000"
        gid: "1002"
        mode: 0400
secrets:
  hosting_token:
    file: ./secrets/hosting-token
```

The second block is two fragments: the first four lines go under `services.factory`, the last three at the top level.

Rules:

- `scrub_environment` returns a new dict holding the entries of `source` whose name is in `ALLOWED_ENVIRONMENT_NAMES`, compared as written, and nothing else.
- `production_environment()` keeps `PATH` and `HOME` as F0006-S0007 builds them, adds the entries of `LANG`, `LC_ALL`, `TERM` and `TZ` that the factory process has, and nothing else of the process's environment. `TaskComposer` is not changed: it puts the mapping it is given, unchanged, into `AgentRunRequest.environment` (F0005 decision 23), and it never reads `os.environ`; nothing in `factory.domain`, `factory.application` or `factory.adapters.claude_runtime` does. `AgentRunRequest(` is called in `factory.application.task` and in no module other than that and `factory.application.preflight` (the probe of an agent run, a later story).
- `ClaudeCodeRuntime` runs the agent with the environment `request.environment` plus its own `SWITCHES` (F0001: auto memory and git instructions off, no bytecode) and nothing of the factory process's own environment, whatever the factory process holds. The stand-in's Python may add `LC_CTYPE` of its own, which is not the runtime's doing.
- `token_file_item(path, uid=..., stat=...)` is the item `token-file`. It passes when the file exists, belongs to `uid`, and its mode has no bit for group or others (`mode & 0o077 == 0`). It fails, with a detail that names the path and the fault, for a `None` path, a missing file, an owner other than `uid`, and any bit for group or others. It reads the file's facts only through `stat`; the wiring passes `os.stat`.
- The helper answers git's `get` operation: it reads standard input, then prints `username=x-access-token` and a line with the key `password` and the content of the file named by `FACTORY_TOKEN_FILE` as its value, written with `printf '%s=%s\n'` so that no line of the script reads as an assignment of a password. When the variable is unset or the file cannot be read it prints nothing to standard output and exits with status 1. For `store`, `erase` and any other operation it prints nothing and exits 0.
- The Dockerfile sets no `ENV` or `ARG` whose name contains `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL` except `FACTORY_TOKEN_FILE`, writes no `.git-credentials` file and no `credential.helper store`, and sets no `credential.helper` in any git configuration (the factory's git gets the helper through `GitOptions.environment`, the agent's git gets none). The compose service has no environment entry with such a name either, and no `env_file`.

Tests: `tests/domain/test_agent_environment.py` (a file of its own: `tests/domain/test_agent_runs.py` is F0001's), `tests/entry/test_wiring_environment.py`, `tests/test_agent_run_request_search.py` (the search, with `ast`), `tests/adapters/test_claude_runtime_environment.py` (the stand-in executable of `tests/adapters/claude_stand_in.py` that records its environment), `tests/application/test_token_file_item.py` (files created in `tmp_path` with `chmod`, `os.stat` as `stat`), `tests/test_git_credential_helper.py` (runs the script with `sh`, and `git credential fill` with the environment `GitCli` builds), `tests/test_image_credentials.py` (the Dockerfile and compose file).

## Acceptance criteria

1. `ALLOWED_ENVIRONMENT_NAMES` is exactly `PATH`, `HOME`, `LANG`, `LC_ALL`, `TERM` and `TZ`; `scrub_environment` keeps those names with their values, returns a new dict, and leaves `source` as it was.
2. `scrub_environment` drops every other name, one test case each: `GH_TOKEN`, `GITHUB_TOKEN`, `FACTORY_TOKEN_FILE`, `GIT_ASKPASS`, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_COUNT`, `SSH_AUTH_SOCK`, `ANTHROPIC_API_KEY`, `MY_OWN_VARIABLE` and the lower-case `path`.
3. With `GH_TOKEN`, `GITHUB_TOKEN`, `FACTORY_TOKEN_FILE` and `GIT_ASKPASS` set in the process's environment (through `monkeypatch`), `production_environment()` has none of those four names, and has a `PATH` that starts with the directory of `sys.executable` and a `HOME` equal to `str(Path.home())` (WE3.2).
4. `production_environment()` keeps `LANG`, `LC_ALL`, `TERM` and `TZ` with the process's values when the process has them, and has none of the four when it has none.
5. WE3.2 over a whole tick: a `Tick` built with `handler_factory(boundaries, "factory-1", production_environment())` over a remote with one started story, while the process's environment holds `GH_TOKEN`, `GITHUB_TOKEN`, `FACTORY_TOKEN_FILE` and `GIT_ASKPASS`, makes an agent request whose `environment` has none of the four names.
6. A search with `ast` over `src/factory` finds `AgentRunRequest(` called in `factory.application.task` and in no module other than `factory.application.task` and `factory.application.preflight` (the probe of a later story), and no use of `os.environ` in `factory.domain`, `factory.application` or `factory.adapters.claude_runtime`.
7. `ClaudeCodeRuntime`, run against the stand-in executable that records its environment while the test process has `GH_TOKEN` set, hands the stand-in the entries of `request.environment` and of `SWITCHES` and nothing of the process's own environment (apart from the `LC_CTYPE` the stand-in's Python adds).
8. `token_file_item` passes for a file of the test's own `uid` with mode 0600 and with mode 0400, and its name is `token-file`.
9. `token_file_item` fails, naming the path in its detail, for modes 0640, 0604, 0644 and 0660 (a bit for group or others, both sides of the limit with criterion 8).
10. `token_file_item` fails for a file whose owner is not the given `uid` (the test passes `os.getuid() + 1`), for a missing file, and for a `None` path.
11. `token_file_item` reads the file only through `stat`: with a `stat` stub that answers an `os.stat_result` with the given `uid` and the mode `0o100600` for a path that does not exist, it passes.
12. The helper, given the operation `get`, a readable token file named by `FACTORY_TOKEN_FILE` holding `example-value`, and a git request on standard input, prints exactly two lines: `username=x-access-token` and a line whose key is `password` and whose value is `example-value`, and exits 0.
13. The helper with `FACTORY_TOKEN_FILE` set to a file the user cannot read (mode 0000, a case skipped when the tests run as root, which reads it regardless), to a missing file, or unset, prints nothing to standard output and exits with status 1, so a process that cannot read the file gets no credential (WE3.4, the helper's side).
14. The helper given `store` or `erase` prints nothing and exits 0, and never prints the token.
15. WE3.5, the factory's side: `git credential fill` run with the environment that `GitCli` builds (`os.environ`, the entries of `git_environment(<a copy of the helper made executable in tmp_path>)`, `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL` at the null device, `GIT_TERMINAL_PROMPT=0`) and `FACTORY_TOKEN_FILE` set to a file holding `example-value`, for the request `protocol=https` and `host=github.com`, prints `password=example-value`; with the token file missing it exits non-zero and prints no password.
16. The Dockerfile copies the helper to `/usr/local/bin/git-credential-factory` and sets `ENV FACTORY_TOKEN_FILE=/run/secrets/hosting-token`, both before `USER factory`; it has no `ENV` or `ARG` with a name that contains `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL` other than `FACTORY_TOKEN_FILE`, no `.git-credentials`, no `credential.helper` at all and no `credential.helper store`.
17. The compose file declares the top-level secret `hosting_token` from `./secrets/hosting-token`, mounts it into the service as `hosting-token` with the uid `"1000"` and the `mode` written `0400` (ruamel.yaml reads it as the integer `400`, Docker Compose as octal) (the user `factory` of the Dockerfile, WE3.1), and the service has no environment entry whose name contains `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL`, and no `env_file`.
18. The factory's own work still functions after an agent run in the same test: after `ClaudeCodeRuntime` has run an agent with a scrubbed environment, a `GitCli.push` to the real local bare remote returns `pushed` and `FakeHostingService.post_comment` returns `posted`, and the test process's own environment is unchanged (WE3.5).
19. make check stays green.
20. docs: `docs/operator-guide.md` explains where the token goes (a file `secrets/hosting-token` beside `image/compose.yml`, which git ignores; the host file is made owner uid 1000 and mode 0400 with `chown 1000` and `chmod 0400`, because Docker Compose without swarm may keep the host file's owner and mode and ignore the `uid`, `gid` and `mode` of the secret), that the factory process and git's credential helper are the only readers, that the agent's environment is an allow list of six names, the preflight item `token-file` and what the operator does when it fails, the morning observation of WE3.3 and WE3.4 (and of the ownership of the mounted file), and that the project commands run as the factory's user, who can read the token file, which is left for v2; `docs/decisions.md` records why the helper reads a file instead of the environment and why the project commands as the factory's user are left for v2 (the human, 2026-10-14).

## Demo

```bash
uv run python -c "
from factory.domain.agent_runs import scrub_environment
print(sorted(scrub_environment({'PATH': '/usr/bin', 'GH_TOKEN': 'x', 'HOME': '/root', 'LANG': 'C', 'GIT_ASKPASS': 'y'})))
"
```
Expect: one line, `['HOME', 'LANG', 'PATH']`.

```bash
uv run python -c "
import os, tempfile, pathlib
from factory.application.preflight import token_file_item
f = pathlib.Path(tempfile.mkdtemp()) / 'token'
f.write_text('example-value\n')
f.chmod(0o600)
print(token_file_item(f, uid=os.getuid(), stat=os.stat).passed)
f.chmod(0o640)
print(token_file_item(f, uid=os.getuid(), stat=os.stat).passed)
"
```
Expect: two lines, `True` and `False`.

```bash
d=$(mktemp -d) && printf 'example-value\n' > "$d/token" && chmod 600 "$d/token" && printf 'protocol=https\nhost=github.com\n\n' | FACTORY_TOKEN_FILE="$d/token" sh image/git-credential-factory get; echo "status $?"; chmod 000 "$d/token"; printf 'protocol=https\n\n' | FACTORY_TOKEN_FILE="$d/token" sh image/git-credential-factory get; echo "status $?"
```
Expect: the first run prints `username=x-access-token`, then a line that starts with the key `password` and ends with `example-value`, then `status 0`; the second run prints only `status 1`.

## Log (append only)

1. 2026-10-12 human: created.
