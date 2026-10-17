# The write guard by the kernel: Landlock (probe of 2026-10-17)

The human asked whether the write guard (today `factory-guard`, a Claude Code PreToolUse hook on Edit and Write, with the undo after the run as the backstop for every other route) could be enforced by the file system instead, without walking every file.

Landlock (Linux 5.13+) lets an unprivileged process restrict itself, and every child it starts, to writing only under named paths. The kernel of both runtimes on this machine (WSL2 6.18.54.1, shared by Docker Desktop and the Podman machine) reports Landlock ABI version 7. The probe (`planning/overnight/landlock_probe.py`, Python with ctypes, about 40 lines, run in v1.1's container `factory-shakedown-factory-1`) restricted writes to one folder and one file and then tried: a new file in the allowed folder (allowed), an append to the allowed file (allowed), a file in another folder (refused), a file at the root (refused), a rename of the allowed file (refused, its folder is not allowed), a child Python process writing elsewhere (refused, inherited), a delete of the allowed file (refused).

## The design for later (the human's discussion, 2026-10-17)

- Each agent run starts through a wrapper that applies the stage's write paths as Landlock rules (folders for folder patterns, single existing files for file patterns such as the story file), plus the agent's home, `/tmp` and the project's `.venv`, then executes the runtime (`claude`, later `opencode`). No chmod, no ownership changes, no walk over the tree, no root helper.
- It covers every tool and child process and every runtime, so the hook and an opencode guard plugin become unnecessary. `.git` is never a write path, so S0006's sealing becomes a second line.
- The undo stays as the backstop and record-keeper. The preflight gains an item: Landlock available, ABI 3 or higher; without it the factory stops (or falls back to the hook, to be decided).
- Order: a feature v1.1 builds after the handover; keep the hook for one shakedown-sized run as a cross-check, then remove it; then opencode as the second runtime.
- Open: a path that does not exist when the run starts cannot be named (patterns are expanded at the start); the exact access rights per ABI version; what the agent sees on refusal (`Permission denied`), which the stage prompt explains.
