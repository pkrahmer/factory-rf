---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 454
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-25T20:31:42.814691Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T20:20:13.100791Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T20:20:13.106456Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T20:20:32.815053Z'
  stage: intake
  run: c10ea9981ed54c3d9d2f8523a1b23771
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T20:20:53.145517Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T20:23:09.303308Z'
  stage: tests
  run: f5901fc611ca4dd9b7c68e7f54878f04
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T20:23:29.796510Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-25T20:26:02.703986Z'
  stage: doing
  run: 1e33581deb8c40339f02953e6e9f776d
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-25T20:26:23.329882Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-25T20:26:36.900312Z'
  stage: review
  run: 4db0a1fbd9094708a50db6200fb5092e
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-25T20:26:57.425422Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-25T20:31:21.937873Z'
  stage: docs
  run: 0c62bff217e440748205b65f96d8c9cd
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-25T20:31:42.814691Z'
  stage: smoke-test
---

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

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is right for a documents-only sweep; it names what may not change (src/, tests/, vm/, template/, claude/) and what the documenter changes (README.md, docs/operator-guide.md, docs/project-guide/, docs/decisions.md). Criterion 1 pins that nothing outside changes, and criterion 3 names the files and sections.
   Criteria: each can be judged by one check. The removed-layer terms, the fourteen decision entries, the single `What went` paragraph, the missing test-module paths and `documents ok` are each backed by a smoke command. The rest is named exactly (section names, which table rows change, which bullets move) for the reviewer. Each rule has its failing side: the grep must find 0 outside `Replaced` sections, and each of the fourteen entries must end with a line naming F0044-S00, which the loop counts as 0 failures. `nested_repository` and `tool_paths` are allowed where they remain true. No Interface behaviour is left without a criterion.
   Smoke test: every command uses awk, grep, a while loop or make, so all are runnable. Each `Expect:` is checkable: `0`; `0` and `1`; `0` and `0`; `1` and `1`; `documents ok`. No command runs pytest, so the `-q` rule does not apply. The `[Dd]ocker\b` pattern does not match `Dockerfile`, as the criterion allows.
   Architecture: documents and the decision log only, with no layer or interface touched. It keeps the documenter's write paths (`README.md`, `docs/*`). `docs/operator-playbook.md`, `docs/runs/` and `CLAUDE.md` are left alone, as decision 15 says.
   Scope: matches S0011 in feature.md (the decision log's closing lines and *What went*, the operator guide, the project guide, README). It adds no mechanism and touches nothing in "Out of scope". The format check passed, and no earlier test is changed.
4. factory: started tests as self.
5. tester: I wrote no tests and changed nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/`. This story only fixes documents. Its Interface is "None", and no test reads the documents: `not_read` leaves out `README.md` and `docs/*.md`.
   - criterion 1 (nothing under src/, tests/, vm/, template/ or claude/ changes): no test. This entry is the tester's statement that it holds; the working tree has no change of mine.
   - criterion 2 (`make check` stays green): no test of its own. The factory's checks cover it. `make test` passed in this stage (`test: green`, coverage 99.55 %) because no new test was added, so there is no red test on purpose. `make lint` passed.
   - criterion 3 (docs): no test, as the criterion itself says ("no test does"). The smoke test and `make documents` check it after the documenter.
   Files created: none. Modules the test run could not import: none.
   For the coder: there is no specification in tests. Hand the story on to the documenter without code changes.

   `lint`: lint: green (0.1 s)
   `test`: test: green (60.6 s)
6. factory: started doing as self.
7. coder: I built nothing and changed nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/`. This story only fixes documents, its Interface is "None", and the tester wrote no tests, so the code had nothing to fail against. The working tree has no change of mine; the one modified file is the work item's `.costs.jsonl`, which belongs to the factory.
   - Criterion 1: holds; this entry is the coder's statement of it.
   - Criterion 2: `make check` passed in this stage (`test: green (61.2 s)`, coverage 99.55 %, `check: green`).
   - Criterion 3 (docs): left to the documenter. `README.md`, `docs/operator-guide.md`, `docs/project-guide/` and `docs/decisions.md` are its files and not the coder's (CLAUDE.md, *Docs*).
   Main choice: hand on with no change. The alternative I rejected was editing the documents here: they are outside the coder's work, and the criterion gives them to the documenter.
   Refactor: there is no diff, so there was nothing to change.
   Description: the journal did not change what the task means, so I left it as it is.
   Noticed but not touched: nothing.

   `check`: check: green
   `duplicates`: duplicates: 8 new, 35 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I checked: `git diff main...HEAD -- . ':!factory'` is empty. `git diff --name-status main...HEAD` lists only the work item and its new `.costs.jsonl` sidecar, both under `factory/`. So nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/` changed.
   - Criterion 1 (no change outside the documents): holds. The diff confirms what the tester's entry (5) and the coder's entry (7) say.
   - Criterion 2 (`make check` stays green): holds. The coder's entry (7) records `check: green` from the factory's run.
   - Criterion 3 (docs) belongs to the documenter, as its own text says. The smoke test and `make documents` check it after the docs stage.
   - Interface: it is "None", with no rule that needs a failing-side test.
   - Architecture, security and quality: there is no code in the diff, so these groups have nothing to judge. The `duplicates: 8 new` in entry 7 cannot come from this story, because it changes nothing under `src/factory`.
   - Work item hygiene: the Description matches what was built (nothing yet, documents next), and the journal states the choice to hand on with no change. The docs criterion still says what the documenter must make true.

   Earlier tests: none. The diff changes, renames or deletes no test file.
10. factory: started docs as self.
11. documenter: No findings. I changed documents only and left `src/`, `tests/`, `vm/`, `template/` and `claude/` as they were. I did not run `make check`, as the stage allows when only documents change. `make documents` prints `documents ok`, and all five smoke-test blocks give their expected output: `0`; `0` and `1`; `0` and `0`; `1` and `1`; `documents ok`.

    Files changed, one line each:
    - `docs/decisions.md`: each of the fourteen named entries now ends with one closing line naming its F0044 stories and what replaced it or what stays. The records-contract entry ends with a line saying the version is `3.0` since F0044-S0006 (the code has `RECORDS_CONTRACT = "3.0"`). "One snapshot instead of many layers" gains *What went*: one line per story S0001 to S0011, and one line on what the acceptance measures (decision 27 of `feature.md`).
    - `docs/operator-guide.md`:
      - New chapter `## Replaced in v1.2` before `## Replaced from v1`, named in the list at the top, with one bullet for each of the eight layers.
      - The *Configuration* table rows now say what `factory.env` sets, and the state and checkout defaults name the VM paths.
      - The paragraph on the image identity points to *The rebuild after a merge*.
      - *The checkout is cloned when it is missing* names `FACTORY_CHECKOUT` and no seal.
      - The records sections use the `FACTORY_STATE` path in place of `/state`, and the disk record's example and host numbers no longer name a container path or Docker.
      - The `tool:git`, `tool:uv` row says to install the tool on the VM and keeps the detail the code prints.
      - *Running on opencode* says the pins come from `vm/Dockerfile` through `factory.env`, and that an own build is set in `factory.env`.
      - *The shipped agents and settings* says the agents come from `FACTORY_CLAUDE_HOME` and reach the instance by a merge and *The rebuild after a merge*.
      - The stage-image and stage-environment paragraphs lost the sentences about v1.1's container.
    - `docs/project-guide/README.md`: the *Sections* lists name the two new `Replaced in v1.2` sections, and `module_names.py` is added to the helper list. Its other lines already matched the criterion: no missing module or helper, no `compose_service`, `image_layout` or `DOCKERFILE`, and `dockerfile_support.py` already described the readers of `vm/Dockerfile`.
    - `docs/project-guide/agents.md`:
      - The `## Rules` bullet now states R14 as R14 reads since F0044-S0001.
      - The wrapper, `sudo`, `timeout` and `env -i` wording is gone from the shared-launch passages.
      - The entrypoint sentence is gone.
      - New `## Replaced in v1.2` section.
    - `docs/project-guide/processes-and-checks.md`: *Running as another user* is replaced by a `## Replaced in v1.2` bullet. The `make mutants` passage says a kill loses `make`'s process group only, since F0044-S0010. The cited section is *Killing a process group*, and *Container project commands* is now *The checks* in `stage-environment.md`. The umask-and-seal sentence is gone from the temporary-folder paragraph.
    - `docs/project-guide/watching.md`: the credential helper is `vm/git-credential-factory`. The test it names is `tests/test_git_credential_helper.py`, because `tests/test_image_credentials.py` does not exist. The `RepositoryUnsealed` sentence is gone, since the class is gone.
    - `docs/project-guide/write-guard.md`: removed the "The kernel's targets do not change" sentence.
    - `docs/project-guide/stage-environment.md`: removed the "under the write guard" example and the sentence about `FACTORY_STAGE_ENVIRONMENT` and `FACTORY_AGENT_USER`.
    - `docs/project-guide/stages.md`: `write_paths` imports `is_inside_checkout`; the module `confinement` no longer exists.
    - `README.md`: the newcomer's paragraph now says the factory runs as a service on a Linux VM with ZFS and rootless Podman, prepared by `vm/setup.sh`, and points to *The machine* and *Replaced in v1.2*.

    Cross-read and found current: `docs/project-guide/costs.md`, `git-and-hosting.md` and `work-items.md` (no removed-layer terms or missing test modules); the *Known results* subsection and the rest of `processes-and-checks.md`; the *Project commands* part that stays true.

    Not run: I cannot run the disk-record log example, so I wrote its paths from `domain/disk.py`'s `disk <occasion>: <folders>` format and the VM layout. The check will not catch a wrong path there.

    Stale text seen, not touched: I read only the passages the criterion names and the smoke test finds, so other long paragraphs of `operator-guide.md` (1,700 lines) may still hold older wording that no pattern matches. `docs/operator-playbook.md` and `docs/runs/` keep their history, as the criterion says.

    `check`: check: green (not run again: passed on tree 4f655f546fa7 at 2026-10-25T20:24:55Z)
    `secrets`: secrets: green (2.7 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
