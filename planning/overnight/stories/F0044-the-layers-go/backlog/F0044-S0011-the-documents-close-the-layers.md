# The documents close the layers

## Description

Every story of this feature left its part in the documents through its docs criterion: each removed section replaced by one line, each decision-log entry of a removed layer closed by one line. This story is the sweep at the end, as F0042-S0012 (the documents describe the stage environment) and F0043-S0004 (the operator guide's chapter "The machine") were for theirs: the documenter reads the four documents and the project guide's files against the code after S0010 (the Docker path and the host's process table are removed) and makes them whole and true in one pass. The operator guide describes the machine of v1.2 only; the project guide names no module that is gone; every decision-log entry whose decision a story of this feature removed ends with one line that says what replaced it, and the entry "One snapshot instead of many layers" gains the paragraph *What went*, which lists the layers and the story that removed each. No code and no test changes; `make documents` passes. What stays: every entry of the decision log (closed, never deleted), every sentence that is still true, the history in `docs/runs/` and in `docs/operator-playbook.md`'s incidents table (decision 15 of `feature.md`).

## Interface

None: nothing changes under `src/factory/`, in any test, under `vm/`, `template/` or `claude/`. The documenter changes `README.md`, `docs/operator-guide.md`, `docs/project-guide/` (the index and the files it names) and `docs/decisions.md`, as the docs criterion says. No test reads the documents: `make check` runs at `doing`, before the documenter, and its `not_read` in `factory/pipeline.yml` leaves out `README.md` and `docs/*.md`; the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: the documenter reads the whole of `README.md`, `docs/operator-guide.md`, `docs/project-guide/README.md` and every file it names against the code after S0010 and corrects every sentence that is no longer true, and makes the following true; the smoke test and `make documents` check them, no test does:
   - `docs/operator-guide.md` and the files under `docs/project-guide/` hold none of the words `factory-confine`, `Landlock`, `tool_paths`, `FACTORY_AGENT_USER`, `sudo -n -u`, `env -i`, `factory.entry.leftovers`, `factory.entry.fresh_home`, `SudoAgentHome`, `RepositoryUnsealed`, `nested_repository`, `remove_ignored`, `InlineEnvironment`, `FACTORY_STAGE_ENVIRONMENT`, `UndoService`, `docker compose`, `compose.yml`, `entrypoint.sh` outside a section named *Replaced in v1.2* or *Replaced from v1*; each such section holds one line per removed part, naming what replaced it.
   - `docs/project-guide/README.md`, *The files*: one bullet per file, each naming the sections the file has; no bullet names a module that does not exist under `src/factory/`; *Shared test helpers* names no helper module that does not exist under `tests/`.
   - `docs/decisions.md`: every entry whose decision named the kernel's guard, the tool paths, the second user, `sudo`, the leftovers program, the fresh home, the seal, the removal of ignored files or nested repositories, the re-clone, the tests' umask, the inline environment, the undo, the image, compose, the entrypoint or the init ends with one line that begins `Replaced` or `The take keeps` and names `F0044` and the story; the entry "One snapshot instead of many layers" gains the paragraph *What went*, one line per story of this feature (its id, its short name, what it removed), and one line on what the acceptance measures (decision 27 of `feature.md`); the entry "The Claude Code hook is removed; the kernel and the undo are the write guard" gains its closing line too.
   - `README.md`: the newcomer's paragraph says that the factory runs as a service on a Linux VM with ZFS and rootless Podman, every stage in throwaway containers on one dataset, prepared by `vm/setup.sh`, and points to `docs/operator-guide.md`, `## The machine`; it names no `docker compose`, no `image/` and no `FACTORY_STAGE_ENVIRONMENT`.
   - `docs/operator-playbook.md`: none (its incidents and its rule on F0019's rebuild are history; decision 15).
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -cE 'factory-confine|Landlock|tool_paths|FACTORY_AGENT_USER|sudo -n -u|InlineEnvironment|FACTORY_STAGE_ENVIRONMENT|UndoService|docker compose' README.md || true
```
Expect: `0`

```bash
grep -c '^## One snapshot instead of many layers' docs/decisions.md; grep -c 'What went' docs/decisions.md
```
Expect: two lines: `1`; `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
