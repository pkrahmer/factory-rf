# The documents close the layers

## Description

Every story of this feature left its part in the documents through its docs criterion: each removed section replaced by one line, each decision-log entry of a removed layer closed by one line. This story is the sweep at the end, as F0042-S0012 (the documents describe the stage environment) and F0043-S0004 (the operator guide's chapter "The machine") were for theirs: the documenter reads the four documents and the project guide's files against the code after S0010 (the Docker path and the host's process table are removed) and makes them whole and true in one pass. The operator guide describes the machine of v1.2 only; the project guide names no module that is gone; every decision-log entry whose decision a story of this feature removed ends with one line that says what replaced it, and the entry "One snapshot instead of many layers" gains the paragraph *What went*, which lists the layers and the story that removed each. No code and no test changes; `make documents` passes. What stays: every entry of the decision log (closed, never deleted), every sentence that is still true, the history in `docs/runs/` and in `docs/operator-playbook.md`'s incidents table (decision 15 of `feature.md`).

## Interface

None: nothing changes under `src/factory/`, in any test, under `vm/`, `template/` or `claude/`. The documenter changes `README.md`, `docs/operator-guide.md`, `docs/project-guide/` (the index and the files it names) and `docs/decisions.md`, as the docs criterion says. No test reads the documents: `make check` runs at `doing`, before the documenter, and its `not_read` in `factory/pipeline.yml` leaves out `README.md` and `docs/*.md`; the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: the documenter corrects, against the code after S0010 (the Docker path and the host's process table are removed), every line the smoke test's first block finds, every passage named below, and any other sentence of `README.md`, `docs/operator-guide.md` and `docs/project-guide/` it finds untrue on the way; it reads those passages and their sections, not the whole of each document. It makes the following true; the smoke test and `make documents` check them, no test does:
   - `docs/operator-guide.md` and every file under `docs/project-guide/` hold none of these outside a section whose heading is `Replaced in v1.2` or `Replaced from v1` (the smoke test's first block is the check): `factory-confine`, `Landlock`, `FACTORY_AGENT_USER`, `sudo -n -u`, `env -i`, `factory.entry.leftovers`, `factory.entry.fresh_home`, `SudoAgentHome`, `RepositoryUnsealed`, `remove_ignored`, `InlineEnvironment`, `FACTORY_STAGE_ENVIRONMENT`, `UndoService`, the word `Docker` or `docker` (`Dockerfile` is allowed), the word `Compose`, `docker compose`, `podman compose`, a compose instance, call, file, override or project, `compose.yml`, `entrypoint` in any case, `image/`, `write guard`, `machine's image`, `kernel's targets`, the module name `` `confinement` ``, `/home/agent/.claude-token`, `/home/agent/.anthropic-api-key` and `/home/agent/.config`. `tool_paths` and `nested_repository` may stay where they stand: they occur only in true sentences (a definition that still holds `tool_paths` is refused, the records contract's version history, a test module's name). `FACTORY_CLAUDE_HOME`'s default `/home/agent/.claude` stays (decision 28). `docs/operator-guide.md` gains a chapter `## Replaced in v1.2` right before `## Replaced from v1`, named in the list at the guide's top, with one bullet per layer of this feature (the kernel's write guard, the second user, the leftovers program, the fresh home, the checkout's hygiene, the inline environment, the undo, the Docker path), each naming what replaced it and the story that removed it; a guide file that names a removed part does so in a section `## Replaced in v1.2`, one bullet per part. A `Replaced in v1.2` section holds no subheading.
   - `docs/project-guide/README.md`, *The files*: one bullet per file, each naming the sections the file has; no bullet names a module that does not exist under `src/factory/`; *Shared test helpers* names no helper module that does not exist under `tests/`, its `conftest.py` line names no `compose_service` and no `image_layout`, and its `dockerfile_support.py` line says what the module holds after S0010 (the readers of `vm/Dockerfile` moved from `tests/test_image.py`), without `DOCKERFILE`, `dockerfile_instructions` and `image/Dockerfile`.
   - `docs/operator-guide.md` and the files under `docs/project-guide/` name no test module `tests/<...>.py` that does not exist, the example `tests/test_a.py` aside.
   - `docs/operator-guide.md`: the opening paragraph and *Install* give the machine of v1.2 (`## The machine`) as the way to run an instance; *Configuration*: every row of the table that says what the image sets says what `vm/setup.sh`'s environment file `factory.env` sets (`FACTORY_TOKEN_FILE`, `FACTORY_CLAUDE_LOGIN_FILE` and `FACTORY_API_LOGIN_FILE` under `/home/factory/.secrets/`, `FACTORY_CLAUDE_VERSION` and `FACTORY_OPENCODE_VERSION` from the pins of `vm/Dockerfile`), and the paragraph on the image identity says the operator renews the file after a build (*The rebuild after a merge*); *The checkout is cloned when it is missing* names the checkout `FACTORY_CHECKOUT` names (`/srv/factory/<instance>/repo` on the VM) and no seal; *The records*, *The known results* and *The disk record* name their files in the state directory `FACTORY_STATE` names (`/srv/factory/<instance>/state` on the VM) in place of `/state`, and the disk record's examples and host numbers name no container path and no Docker; *The preflight's items*: the row `tool:git`, `tool:uv` tells the operator to install the tool on the VM (`vm/setup.sh`) and names the detail the code prints as it is; *Running on opencode*: the versions and models are the pins of `vm/Dockerfile` that `factory.env` carries, an operator's own build and its login are set in `factory.env` and made on the VM, with no `docker exec`, no compose call and no folder made by v1.1's image; *The shipped agents and settings*: the instance reads the agents from `FACTORY_CLAUDE_HOME` (`/srv/factory/<instance>/factory/claude`, the factory's own clone), so a change reaches it by a merge and *The rebuild after a merge*, with no entrypoint.
   - `docs/project-guide/processes-and-checks.md`: no heading names a removed layer (*Running as another user* goes; its removed parts become bullets of a `## Replaced in v1.2` section, and what stays true of it, the records, the disk record, the tests' umask, the login variables and *Known results*, stays under *Project commands*); *Mutation testing*: a `make mutants` that `MakeProjectCommands` kills at its time limit loses `make`'s process group only, so a mutmut that `timeout` put into a group of its own is not ended by that kill (since F0044-S0010), and every section the file cites by name exists.
   - `docs/project-guide/agents.md`: the `## Rules` bullet says of R14 what R14 says since F0044-S0001 (no `Permission denied` as a write guard, no `$TMPDIR` as the one temporary place, no refused `/tmp`), as the R14 bullet below it does.
   - `docs/decisions.md`: each of these fourteen entries ends with one closing line, a paragraph or a bullet, that names the story ids given here and says what replaced its decision or what of it stays: "The Claude Code hook is removed; the kernel and the undo are the write guard" (F0044-S0002, F0044-S0009); "The factory runs on the host, and the stage image carries the tools alone" (its "Open" is done: F0044-S0010); "The preflight runs the factory's own arguments once for each image build, and finds a refused `sudo` before any claim" (F0044-S0005, F0044-S0008; the probe stays); "The document check runs in the docs stage; the default identity has one home" (the runtime's `sudo`, F0044-S0005); "The runtimes are Docker Desktop and rootless Podman; on Windows the operator restarts the factory" (F0044-S0010); "A missing health file is not healthy; `factory-run` writes an empty one at its start" (Docker's health check, F0044-S0010; the rule stays); "The disk record is not committed and none is written at the end of a run" (F0044-S0010); "What the agent runtimes share lies in one module" (F0044-S0001, F0044-S0003, F0044-S0005; the module stays); "No stage writes a .claude folder at any depth" (F0044-S0002, F0044-S0009; the take keeps the rule); "A call stops reading five seconds after its own process ended" (F0044-S0003, F0044-S0005; the rule stays); "The hook allows the run's temporary folder" (F0044-S0002); "The guard reads only the settings file taken at the stage-start commit, and reads the payload as v1 does" (F0044-S0009; the take keeps the rule); "The tests reopen their tmp_path after every test" (F0044-S0006; the fixture stays); "The project commands first ran as the factory's user; replaced" (F0044-S0005). The entry "The records carry generated JSON Schemas under `src/factory/contract/`" ends with a line that the records contract's version is `3.0` since F0044-S0006, which removed the stall reason `nested_repository`. The closing lines S0001 to S0010 wrote stay as they are, and no other entry changes. The entry "One snapshot instead of many layers" gains the paragraph *What went* (the words appear once in the file), one line per story of this feature (its id, its short name, what it removed) and one line on what the acceptance measures (decision 27 of `feature.md`).
   - `README.md`: the newcomer's paragraph says that the factory runs as a service on a Linux VM with ZFS and rootless Podman, every stage in throwaway containers on one dataset, prepared by `vm/setup.sh`, and points to `docs/operator-guide.md`, `## The machine`; it names no `docker compose`, no `image/` and no `FACTORY_STAGE_ENVIRONMENT`.
   - `docs/operator-playbook.md`: none (its incidents and its rule on F0019's rebuild are history; decision 15).
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
for f in docs/operator-guide.md docs/project-guide/*.md; do awk '/^#+ /{skip=($0 ~ /^#+ Replaced (in v1\.2|from v1)$/)} !skip' "$f"; done | grep -cE 'factory-confine|[Ll]andlock|FACTORY_AGENT_USER|sudo -n -u|env -i|factory\.entry\.leftovers|factory\.entry\.fresh_home|SudoAgentHome|RepositoryUnsealed|remove_ignored|InlineEnvironment|FACTORY_STAGE_ENVIRONMENT|UndoService|[Dd]ocker\b|\bCompose\b|(docker|podman) compose|\bcompose (instance|call|file|override|project)|compose\.yml|[Ee]ntrypoint|image/|write guard|[Mm]achine.s image|[Kk]ernel.s targets|`confinement`|/home/agent/\.(claude-token|anthropic-api-key|config)' || true
```
Expect: `0`

```bash
while IFS= read -r t; do awk -v t="## $t" '$0==t{on=1; next} /^## /{on=0} on && NF{last=$0} END{print last}' docs/decisions.md | grep -c 'F0044-S00'; done <<'EOF' | grep -c '^0$'
The Claude Code hook is removed; the kernel and the undo are the write guard
The factory runs on the host, and the stage image carries the tools alone
The preflight runs the factory's own arguments once for each image build, and finds a refused `sudo` before any claim
The document check runs in the docs stage; the default identity has one home
The runtimes are Docker Desktop and rootless Podman; on Windows the operator restarts the factory
A missing health file is not healthy; `factory-run` writes an empty one at its start
The disk record is not committed and none is written at the end of a run
What the agent runtimes share lies in one module
No stage writes a .claude folder at any depth
A call stops reading five seconds after its own process ended
The hook allows the run's temporary folder
The guard reads only the settings file taken at the stage-start commit, and reads the payload as v1 does
The tests reopen their tmp_path after every test
The project commands first ran as the factory's user; replaced
EOF
awk '$0=="## The records carry generated JSON Schemas under `src/factory/contract/`"{on=1; next} /^## /{on=0} on && NF{last=$0} END{print last}' docs/decisions.md | grep -c 'F0044-S0006'
```
Expect: two lines: `0`; `1`

```bash
grep -ohE 'tests/[A-Za-z0-9_/]+\.py' docs/operator-guide.md docs/project-guide/*.md | sort -u | grep -vx 'tests/test_a.py' | while read -r p; do test -e "$p" || echo "$p"; done | wc -l; grep -cE 'factory-confine|Landlock|FACTORY_AGENT_USER|sudo -n -u|InlineEnvironment|FACTORY_STAGE_ENVIRONMENT|UndoService|docker compose|image/' README.md || true
```
Expect: two lines: `0`; `0`

```bash
grep -c '^## One snapshot instead of many layers' docs/decisions.md; grep -c 'What went' docs/decisions.md
```
Expect: two lines: `1`; `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
