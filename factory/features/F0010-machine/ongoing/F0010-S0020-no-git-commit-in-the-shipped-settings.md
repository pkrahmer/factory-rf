# No git commit in the shipped settings

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

The shipped agents and their shared settings contradict each other on one point. F0010-S0017 carried v1's pipeline rules into every shipped agent and rewrote v1's R10 for v1.1: "You do not commit either: leave your changes in the working tree for the factory's commit" (`claude/agents/*.md`, `## Rules`). The factory makes the result commit itself. But `claude/settings.json`, shipped by F0010-S0012 with v1's permissions, still allows `Bash(git add *)` and `Bash(git commit *)`, and `docs/project-guide.md` describes them as "the read and commit git commands".

The documenters of S0017 (entries 10 and 12) and S0012 noted this and did not touch it, because it lies outside their lane. An allowed command that the instructions forbid is a key with no effect, or one with the wrong effect: FEATURE.md promised settings where "each key [has] an effect". In a real image the agent user has no git identity, so its `git commit` fails or makes a commit under an identity nobody chose. The commit then sits between the claim and the factory's result commit.

This story takes `git add` and `git commit` out of the allow list and puts them on the deny list. The model then gets a refusal from the runtime, not a commit.

This changes `tests/test_claude_files.py::SETTINGS`, which F0010-S0012's tester wrote. Under `CLAUDE.md` that needs the human's permission. The human gives it by promoting this story: the tester changes exactly the two lists in `SETTINGS`, and nothing else in that file.

## Interface

`claude/settings.json`:

- `permissions.allow` drops `Bash(git add *)` and `Bash(git commit *)` and keeps every other entry, in the same order.
- `permissions.deny` gains `Bash(git add*)` and `Bash(git commit*)` after `Bash(git branch -D*)`.
- `env` stays `{"CLAUDE_CODE_FORK_SUBAGENT": "0"}`.

No code changes. `tests/test_claude_files.py::SETTINGS` is changed to match, as the Assignment allows.

## Acceptance criteria

1. `claude/settings.json` parses as JSON. Its `permissions.allow` holds no entry that starts with `Bash(git add` or `Bash(git commit`, and still holds `Bash(git status*)`, `Bash(git diff*)`, `Bash(git log*)`, `Bash(git show*)` and `Bash(git rev-parse*)`.
2. Its `permissions.deny` holds `Bash(git add*)` and `Bash(git commit*)`, and still holds `Bash(git push*)` and `Bash(gh *)`.
3. The settings equal `tests/test_claude_files.py::SETTINGS` after the tester's change (`settings == SETTINGS`, so each list keeps its order).
4. The `## Rules` of every shipped agent still holds the sentence ``You do not commit either``.
5. `make check` stays green.
6. docs: `docs/project-guide.md`, "The settings", lists the git commands an agent may run (`status`, `diff`, `log`, `show`, `rev-parse`) and names `add` and `commit` among the denied ones, with the reason: the factory makes the result commit (R10). `docs/operator-guide.md`, "The shipped agents and settings", names `git add` and `git commit` among the denied commands, with the same reason.

## Demo

```bash
uv run python -c "import json; s = json.load(open('claude/settings.json')); print([a for a in s['permissions']['allow'] if a.startswith('Bash(git')]); print([d for d in s['permissions']['deny'] if 'add' in d or 'commit' in d])"
```
Expect: `['Bash(git status*)', 'Bash(git diff*)', 'Bash(git log*)', 'Bash(git show*)', 'Bash(git rev-parse*)']`, then `['Bash(git add*)', 'Bash(git commit*)']`.

```bash
grep -c 'You do not commit either' claude/agents/*.md
```
Expect: seven lines, each ending in `:1`.

## Log (append only)

1. 2026-10-16 human: created.
