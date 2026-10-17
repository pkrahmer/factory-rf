---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# What the first start observed, in the guide

## Assignment (as of log entry 1)

The first start of 2026-10-17 (`planning/overnight/first-start-checklist.md`, "Results", fault 4) found two places where the operator guide is wrong or silent. A folder an agent makes in the checkout is `2775`, not `775`: `/work` is setgid (`2775`), so a new folder inherits the bit and its group `factory-work`, and `stat -c %a` prints `2775`; a file is `664` as written. And under Podman on Windows, the operator's shell (PowerShell) may not see the saved connection of the Podman machine: a `podman` command then fails with `connection "podman-machine-default" not found`; `podman system connection list`, in a shell that sees it, shows the connection's URI and identity file, and `--url` and `--identity` on the command name them directly. The place of the agent's login, the third point of fault 4, belongs to S0004's text, which rewrites that paragraph. This story is documentation only: nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes; the tester and the coder each end with an entry saying so. The docs criterion carries the text. It is built after S0004, which rewrites the paragraphs around it; S0007 and S0008 follow it.

## Interface

None: no code, no image file and no test changes. The document the documenter changes is `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in the operator guide's morning observations of *The agent runs as a second user*, the row "The mode of what an agent makes" expects "`2775` for the directory, `664` for the file", written so, and says why: `/work` is setgid, so a folder made in it keeps the bit and the group `factory-work` (seen at the first start of 2026-10-17 under Docker Desktop and Podman). *Podman: the commands* (under *Container runtimes*) gets a paragraph: on Windows a shell may not see the Podman machine's saved connection, and a command then fails with `connection "podman-machine-default" not found` (seen at the first start in PowerShell); `podman system connection list`, run where the connection is seen, shows its URI and identity file; give them on each command with `podman --url <URI> --identity <identity file> ...`, for example `podman --url <URI> --identity <identity file> ps`; whether `podman compose` hands them on to its Compose provider is not observed, so run `compose` from a shell that sees the connection. No other document changes, the guide uses no word the document check refuses, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -o '`2775` for the directory\|podman-machine-default\|podman system connection list\|--identity' docs/operator-guide.md | sort -u
```
Expect: four lines, one per term, in any order: the text 2775 in backticks followed by ` for the directory`, `podman-machine-default`, `podman system connection list` and `--identity`.

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-17 human: created.
