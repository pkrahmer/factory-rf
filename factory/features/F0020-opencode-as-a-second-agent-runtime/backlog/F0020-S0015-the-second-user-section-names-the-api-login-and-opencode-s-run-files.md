# The second-user section names the API login and opencode's run files

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

S0014 fixed three passages of `docs/operator-guide.md` that spoke only of Claude Code. Its documenter noticed one more in the section *The agent runs as a second user*, and it was not one of the story's three. Two paragraphs of that section are still written for Claude Code on the subscription only, and one sentence now contradicts the guide's own section on the login shell:

- The `sudo` paragraph says that `env -i` passes the runtime's "three switches and, from the login shell, `CLAUDE_CODE_OAUTH_TOKEN`". It also says "The login shell is there only when `FACTORY_CLAUDE_LOGIN_FILE` is set; it `exec`s `claude`". Since S0001 the login shell also starts when `FACTORY_API_LOGIN_FILE` is set, and it then hands over `ANTHROPIC_API_KEY`. The guide's list of login-shell points says this, as does `docs/project-guide/agents.md`, which also says that an opencode run's login shell comes from the API login file only. Under opencode, the call's environment holds `OPENCODE_CONFIG` and one switch (`PYTHONDONTWRITEBYTECODE`), not Claude Code's three.
- The paragraph on the files of a run names `instructions-<session>.md`, `guard-<session>.json` and `hooks-<session>.json`. An opencode run writes `opencode-<run>.json` (its per-run configuration, mode `0640`) beside its confinement rules instead.

An operator who sets up an opencode instance on an API key would read in this section that the key cannot reach the agent. This story corrects these two paragraphs. It changes no code and no test, and adds no section.

## Interface

None. No module under `src/factory/` changes, and no test, image, template or agent file. The documenter changes `docs/operator-guide.md` only.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, section *The agent runs as a second user*:
   - The sentence on what `env -i` lets through names, from the login shell, `CLAUDE_CODE_OAUTH_TOKEN`, or `ANTHROPIC_API_KEY` when an API key is in force. It names the switches as the runtime's own: Claude Code's three, or, under opencode, `PYTHONDONTWRITEBYTECODE` with `OPENCODE_CONFIG`.
   - The sentence "The login shell is there only when `FACTORY_CLAUDE_LOGIN_FILE` is set; it `exec`s `claude`" is replaced. The new text says the login shell is there when `FACTORY_CLAUDE_LOGIN_FILE` or `FACTORY_API_LOGIN_FILE` is set (under opencode, only the API login file counts), and that it `exec`s the runtime's executable, so `timeout`'s kill still reaches it.
   - The paragraph on the files of a run says that an opencode run writes `opencode-<run>.json` (its per-run configuration, mode `0640`) in place of the instructions, guard and hooks files (see "Running on opencode").
   - The documenter checks each claim against `docs/project-guide/agents.md` (*The shared launch module*, *The opencode runtime*), `SWITCHES` and `CONFIG_VARIABLE` in `factory.adapters.opencode_runtime`, and `login_argv` in `factory.adapters.agent_launch`.
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c 'The login shell is there only when `FACTORY_CLAUDE_LOGIN_FILE` is set;' docs/operator-guide.md
```
Expect: `0`

```bash
s=$(sed -n '/^### The agent runs as a second user/,/^### The kernel refuses every other write/p' docs/operator-guide.md); printf '%s\n' "$s" | grep -c 'FACTORY_API_LOGIN_FILE'; printf '%s\n' "$s" | grep -c 'ANTHROPIC_API_KEY'; printf '%s\n' "$s" | grep -c 'opencode-<run>.json'
```
Expect: three lines, each a number of at least `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal
