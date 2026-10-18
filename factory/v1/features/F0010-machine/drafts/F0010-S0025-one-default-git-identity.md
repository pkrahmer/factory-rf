# One default git identity

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

The factory's default commit identity `factory <factory@noreply.invalid>` is written twice in `src/`. It is `DEFAULT_GIT_IDENTITY` in `src/factory/domain/settings.py` (F0010-S0001), and it is also the literal default of `GitOptions.identity` in `src/factory/domain/git.py` (F0001). The two agree today, but nothing keeps them together: if one of them changed, a `GitCli` built without options and an instance with no `GIT_USER_NAME` and `GIT_USER_EMAIL` would commit under different names. Each of F0010's three feature acceptances listed this as a noticed item that nobody owned.

This story moves the constant into `factory.domain.git`, beside `GitIdentity`. `GitOptions.identity` defaults to it, and `factory.domain.settings` imports it from there. Behaviour does not change: both defaults stay `factory <factory@noreply.invalid>`, and `GIT_USER_NAME` and `GIT_USER_EMAIL` still override each half on its own.

## Interface

- `factory.domain.git.DEFAULT_GIT_IDENTITY: GitIdentity`, equal to `GitIdentity(name="factory", email="factory@noreply.invalid")`. It is the one place in `src/factory` that holds the string literal `"factory@noreply.invalid"`.
- `GitOptions.identity` defaults to `DEFAULT_GIT_IDENTITY`.
- `factory.domain.settings` imports `DEFAULT_GIT_IDENTITY` from `factory.domain.git`, and `factory.domain.settings.DEFAULT_GIT_IDENTITY` stays importable as the same object. `InstanceSettings.git_identity` and `read_settings` keep their present defaults and overrides.
- No layer changes: both modules are in `factory.domain`, and `settings` already imports `git`.

## Acceptance criteria

1. `factory.domain.git.DEFAULT_GIT_IDENTITY == GitIdentity(name="factory", email="factory@noreply.invalid")`.
2. `GitOptions().identity is DEFAULT_GIT_IDENTITY`, and `factory.domain.settings.DEFAULT_GIT_IDENTITY is factory.domain.git.DEFAULT_GIT_IDENTITY`.
3. The string literal `"factory@noreply.invalid"` occurs exactly once among the string literals of the modules under `src/factory` (read with `tests/source_search.py`), and that occurrence is in `factory.domain.git`. A second copy anywhere in `src/factory` fails this criterion.
4. `read_settings` with neither `GIT_USER_NAME` nor `GIT_USER_EMAIL` set still gives `git_identity == DEFAULT_GIT_IDENTITY`. With only `GIT_USER_NAME=Ann` set, it still gives `GitIdentity(name="Ann", email="factory@noreply.invalid")`.
5. `make check` stays green.
6. docs: none. The project guide's `GitOptions` table, the operator guide's settings table and `docs/decisions.md` already state the default as `factory <factory@noreply.invalid>`, and the default does not change.

## Demo

```bash
uv run python -c "
from factory.domain import git, settings
print(git.GitOptions().identity is git.DEFAULT_GIT_IDENTITY, settings.DEFAULT_GIT_IDENTITY is git.DEFAULT_GIT_IDENTITY, git.DEFAULT_GIT_IDENTITY)
"
grep -rn --include='*.py' 'factory@noreply.invalid' src/factory
```
Expect: the first command prints `True True name='factory' email='factory@noreply.invalid'`. The second prints exactly one line, in `src/factory/domain/git.py`.

## Log (append only)

1. 2026-10-16 human: created.
