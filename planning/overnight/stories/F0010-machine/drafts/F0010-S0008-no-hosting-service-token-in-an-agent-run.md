# No hosting-service token in an agent run

## Assignment (as of log entry 1)

Keep the hosting-service token out of every agent run. The token lives in one file that only the factory's own user can read; the factory process reads it once and hands it to PyGithub, and git gets it from a credential helper that reads the same file and fails for anyone who cannot. The environment of an agent run is built from an allow list, so nothing the factory process holds reaches it, and every agent run request is composed in one place. The factory's own pushes and posts keep working. This covers WE3.2 and WE3.5, implements R33 and keeps kept thing 5's rule that agents do not push, switch branches or call the hosting service. WE3.3 and WE3.4 are covered here by tests of the files and of the helper plus a morning observation: a real agent run that tries to read the token file and the token, to run `git -C . push origin main` and to call the API, all of which must fail, needs Docker and a second operating-system user, which v1's container does not have. The second user itself, and the call that runs the agent as that user (WE3.1), are the next story. If `make secrets` flags a line of this story's files, rephrase the line; a new entry in the secrets baseline is not allowed.

## Interface

`src/factory/domain/settings.py` (extends the module)

```python
TOKEN_FILE_VARIABLE = "FACTORY_TOKEN_FILE"

class InstanceSettings(BaseModel):
    ...
    token_file: Path | None = None            # the value of FACTORY_TOKEN_FILE; missing or blank is None
```

`src/factory/domain/agent_runs.py` (extends the module)

```python
ALLOWED_ENVIRONMENT_NAMES: frozenset[str] = frozenset({"PATH", "LANG", "LC_ALL", "TERM", "TZ"})

def scrub_environment(source: Mapping[str, str]) -> dict[str, str]: ...
```

`src/factory/entry/wiring.py` (extends the module)

```python
def read_hosting_token(path: Path | None) -> str: ...
```

`src/factory/application/preflight.py` (extends the module)

```python
def token_file_item(path: Path | None, *, uid: int) -> PreflightItem: ...
```

`image/git-credential-factory` is a POSIX `sh` script, git's credential helper. `image/Dockerfile` and `image/compose.yml` gain the lines below, inserted before the Dockerfile's `USER factory` and into the compose service:

```dockerfile
COPY image/git-credential-factory /usr/local/bin/git-credential-factory
RUN chmod 0755 /usr/local/bin/git-credential-factory \
 && git config --system credential.helper /usr/local/bin/git-credential-factory
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
- The composer of agent run requests, `factory.application.task`, puts into `AgentRunRequest.environment` only the result of `scrub_environment` applied to the mapping it is given, plus the names it sets itself; it never reads `os.environ`, and nothing in `factory.domain`, `factory.application` or `factory.adapters.claude_runtime` does. `AgentRunRequest(` is called nowhere else in `src/factory`.
- `ClaudeCodeRuntime` runs the agent with exactly `request.environment` as its environment, whatever the factory process holds.
- `read_hosting_token(path)` returns the content of the file without surrounding whitespace. A `None` path, a missing or unreadable file, and a blank content raise `SettingsInvalid` with `variable == "FACTORY_TOKEN_FILE"`. `build_boundaries` obtains the token with it and gives it to PyGithub; the token is held by the factory process only.
- `token_file_item(path, uid=...)` is the item `token-file`. It passes when the file exists, belongs to `uid`, and its mode has no bit for group or others (`mode & 0o077 == 0`). It fails, with a detail that names the path and the fault, for a `None` path, a missing file, an owner other than `uid`, and any bit for group or others. `run_instance` passes `lambda: token_file_item(settings.token_file, uid=os.getuid())` to `MachineChecks` as an extra item.
- The helper answers git's `get` operation: it reads standard input, then prints `username=x-access-token` and a line with the key `password` and the content of the file named by `FACTORY_TOKEN_FILE` as its value, written with `printf '%s=%s\n'` so that no line of the script reads as an assignment of a password. When the variable is unset or the file cannot be read it prints nothing to standard output and exits with status 1. For `store`, `erase` and any other operation it prints nothing and exits 0.
- The Dockerfile sets no `ENV` or `ARG` whose name contains `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL` except `FACTORY_TOKEN_FILE`, and writes no `.git-credentials` file and no `credential.helper store`. The compose service has no environment entry with such a name either, and no `env_file`.

Tests: `tests/domain/test_settings.py`, `tests/domain/test_agent_runs.py`, `tests/application/test_task_environment.py`, `tests/test_agent_run_request_search.py` (the search, with `ast`), `tests/adapters/test_claude_runtime_environment.py` (the stand-in executable of F0001-S0008 that dumps its environment), `tests/entry/test_wiring_token.py`, `tests/application/test_token_file_item.py` (files created in `tmp_path` with `chmod`), `tests/test_git_credential_helper.py` (runs the script with `sh`), `tests/test_image_credentials.py` (the Dockerfile and compose file).

## Acceptance criteria

1. `read_settings` sets `token_file` to the path in `FACTORY_TOKEN_FILE`, and to `None` when the variable is missing or blank.
2. `scrub_environment` keeps `PATH`, `LANG`, `LC_ALL`, `TERM` and `TZ` with their values, returns a new dict, and leaves `source` as it was.
3. `scrub_environment` drops every other name, one test case each: `GH_TOKEN`, `GITHUB_TOKEN`, `FACTORY_TOKEN_FILE`, `GIT_ASKPASS`, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_COUNT`, `SSH_AUTH_SOCK`, `ANTHROPIC_API_KEY`, `HOME`, `MY_OWN_VARIABLE` and the lower-case `path`.
4. A request composed by `factory.application.task` while the given environment holds `GH_TOKEN`, `GITHUB_TOKEN`, `FACTORY_TOKEN_FILE`, `GIT_ASKPASS` and `PATH` has an `environment` with `PATH` and with none of the other four names (WE3.2).
5. A search with `ast` over `src/factory` finds `AgentRunRequest(` called only in `factory.application.task`, and no use of `os.environ` in `factory.domain`, `factory.application` or `factory.adapters.claude_runtime`.
6. `ClaudeCodeRuntime`, run against the stand-in executable that dumps its environment while the test process has `GH_TOKEN` set, hands the stand-in exactly `request.environment` and nothing of the process's own environment.
7. `read_hosting_token` returns `example-value` for a file that holds `example-value` and a newline.
8. `read_hosting_token` raises `SettingsInvalid` naming `FACTORY_TOKEN_FILE` for a `None` path, a missing file, and a file that holds only whitespace.
9. `token_file_item` passes for a file of the test's own `uid` with mode 0600 and with mode 0400, and its name is `token-file`.
10. `token_file_item` fails, naming the path in its detail, for modes 0640, 0604, 0644 and 0660 (a bit for group or others, both sides of the limit with criterion 9).
11. `token_file_item` fails for a file whose owner is not the given `uid` (the test passes `os.getuid() + 1`), for a missing file, and for a `None` path.
12. The helper, given the operation `get`, a readable token file named by `FACTORY_TOKEN_FILE` holding `example-value`, and a git request on standard input, prints exactly two lines: `username=x-access-token` and a line whose key is `password` and whose value is `example-value`, and exits 0.
13. The helper with `FACTORY_TOKEN_FILE` set to a file the user cannot read (mode 0000), to a missing file, or unset, prints nothing to standard output and exits with status 1, so a process that cannot read the file gets no credential (WE3.4, the helper's side).
14. The helper given `store` or `erase` prints nothing and exits 0, and never prints the token.
15. The Dockerfile copies the helper to `/usr/local/bin/git-credential-factory`, sets it as the system `credential.helper` and sets `ENV FACTORY_TOKEN_FILE=/run/secrets/hosting-token`, all before `USER factory`; and it has no `ENV` or `ARG` with a name that contains `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL` other than `FACTORY_TOKEN_FILE`, no `.git-credentials` and no `credential.helper store`.
16. The compose file declares the top-level secret `hosting_token` from `./secrets/hosting-token`, mounts it into the service as `hosting-token` with uid `1000` and mode 0400 (the user `factory` of the Dockerfile, WE3.1), and the service has no environment entry whose name contains `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL`, and no `env_file`.
17. The factory's own work still functions after an agent run in the same test: after `ClaudeCodeRuntime` has run an agent with a scrubbed environment, a `GitCli.push` to the real local bare remote returns `pushed` and `FakeHostingService.post_comment` returns `posted`, and the test process's own environment is unchanged (WE3.5).
18. `make check` stays green.
19. docs: `docs/operator-guide.md` explains where the token goes (a file `secrets/hosting-token` beside `image/compose.yml`, owner uid 1000, mode 0400), that the factory process and git's credential helper are the only readers, that the agent's environment is an allow list of five names, the preflight item `token-file` and what the operator does when it fails, and the morning observation of WE3.3 and WE3.4; `docs/decisions.md` records why the helper reads a file instead of the environment.

## Demo

```bash
uv run python -c "
from factory.domain.agent_runs import scrub_environment
print(sorted(scrub_environment({'PATH': '/usr/bin', 'GH_TOKEN': 'x', 'HOME': '/root', 'LANG': 'C', 'GIT_ASKPASS': 'y'})))
"
```
Expect: one line, `['LANG', 'PATH']`.

```bash
uv run python -c "
import os, tempfile, pathlib
from factory.application.preflight import token_file_item
f = pathlib.Path(tempfile.mkdtemp()) / 'token'
f.write_text('example-value\n')
f.chmod(0o600)
print(token_file_item(f, uid=os.getuid()).passed)
f.chmod(0o640)
print(token_file_item(f, uid=os.getuid()).passed)
"
```
Expect: two lines, `True` and `False`.

```bash
d=$(mktemp -d) && printf 'example-value\n' > "$d/token" && chmod 600 "$d/token" && printf 'protocol=https\nhost=github.com\n\n' | FACTORY_TOKEN_FILE="$d/token" sh image/git-credential-factory get; echo "status $?"; chmod 000 "$d/token"; printf 'protocol=https\n\n' | FACTORY_TOKEN_FILE="$d/token" sh image/git-credential-factory get; echo "status $?"
```
Expect: the first run prints `username=x-access-token`, then a line that starts with the key `password` and ends with `example-value`, then `status 0`; the second run prints only `status 1`.

## Log (append only)

1. 2026-10-12 human: created.
