# The tiny story's findings

## Goal

v1.1 ran its first real work item on 2026-10-18: the tiny story F0099-S0001 on `pkrahmer/factory-demo-todo`, as instance `shakedown` under Docker Desktop, on an image built from factory-rf `7432a942` (the night log, `docs/runs/2026-10-12-overnight/night-log.md`, the rows of 05:46, 05:56 and 06:09). It went through every stage to the approval and was sent back twice. On the second send-back the coder's 1-minute `time_limit` killed its run under `sudo`: a stall, then a retry that passed. The run found three things. (1) Every agent run's id, 32 random hexadecimal characters in the work item's `.costs.jsonl`, is read by detect-secrets as a high-entropy secret, so `make secrets`, and with it `make check`, is red on every work item of every project set up from the template. (2) The killed run leaves a zombie, `[claude] <defunct>` of `agent`, whose parent is PID 1, the factory's Python, which reaps nothing it did not start. One or more zombies pile up with every time limit until the container restarts. (3) The coder saw the work item's `.costs.jsonl` modified in the working tree. This feature fixes (1) in the template and the todo demo's source and (2) in the compose file. It writes (3) into the guides as expected behaviour, because the code shows it is harmless (decision 9). It is built by v1 before the shakedown run (plan step 4, `planning/overnight/restructure-after-f0011.md`), whose eight stories would otherwise each stall on a red check, and whose many time limits would otherwise fill the container with zombies. It is for the human, who runs the shakedown next, and for every operator after. Done when every story below is merged and `make check` is green. At that point the template's `make secrets` and the todo demo's leave out the factory's cost records, a test keeps the two `secrets` recipes equal, the container's first process is the container runtime's init, and the guides explain all three findings.

## Scope

- The cost records are left out of a project's secrets scan (finding 1). The template's `make secrets` filter gains `.*\.costs\.jsonl`, the human's fix of the live todo demo (`83eaa11`). The todo demo's source gets the same line as the human's change. A test of the template's `make secrets` covers both sides of the rule, and a test keeps the demo's `secrets` recipe equal to the template's (S0001).
- The container's init reaps orphans (finding 2): `init: true` on the service `factory` in `image/compose.yml`, a test of the compose file and of the entrypoint's hand-over to the factory, and the guide's paragraph and morning observation (S0002).
- The running run's cost record in the guides (finding 3, documentation only). From `begin` to the stage's commit, the sidecar holds the running run's `started` record and is not committed. An agent's `git status` therefore shows it, which is expected and harmless (S0003).

## Out of scope

- A new form of the run id (a prefix, or an id that is not hexadecimal). The run ids stay 32 lowercase hexadecimal characters (decision 1).
- The run id in the work item's own journal (`run`, since F0014-S0007). The front matter writer writes it as a plain YAML value. detect-secrets reads high-entropy strings only in quotes, and the tiny story's `make secrets` was green on the work item's `.md` once the sidecars were left out (`83eaa11`, checked on the branch). The writer quotes a value only when YAML would read it as a number, which for a random 32-character hexadecimal id is rarer than one in a million. Not built; named here so it is not mistaken for an oversight.
- `template/CLAUDE.md`'s description of `make secrets`. The file is pinned byte for byte by `tests/test_claude_files.py` (`TEMPLATE_RULES_LINES`), and an agent needs no rule for a filter it never touches. The project guide and the operator guide say it instead.
- A project's secret scanners other than the template's `make secrets` (a pre-commit hook, a CI job): the operator guide says that any such scan must leave out `*.costs.jsonl` (S0001's docs criterion). The factory checks nothing about it.
- The factory reaping processes itself, and an init installed in the image (decision 6). A test in `make test` that a killed run's orphan is reaped: the reaping is done by the container runtime's init, which exists only in a running container, and `make test` starts none (decision 7). It is a morning observation of the shakedown.
- v1's own compose file (`pkrahmer/factory`), which has no `init` either. v1 is not changed by this feature. The human may give it the same line.
- A rule in the shipped agents about the dirty sidecar (decision 9).
- The operator guide's "(or above the agent's last commit, when the agent committed)" in *What a stage run shows*. The agent cannot commit since F0014-S0006 sealed the checkout's `.git`, so the parenthesis is stale. That is a separate fault and not this feature's. S0003's documenter may correct it during its cross-read, as stale text it finds.

## Stories

The build order is S0001, S0002, S0003. S0001 and S0002 are independent: they change different files. Only S0001 depends on the human's changes below. S0003 is documentation only, but it starts only after S0001 is merged, because its project-guide passage says the cost records are left out of a project's secrets scan, which is true only once S0001's template line is on `main` (decision 11). S0002 may start before S0001 if it is the only story moved to `ongoing/`.

- S0001 — The cost records are left out of the secrets scan
- S0002 — The container's init reaps a killed run's processes
- S0003 — The running run's cost record, in the guides (documentation only), started only after S0001 is merged

## The human's changes

Two before S0001, both outside every write path of v1's `factory/stages.yml` (checked on 2026-10-18: the coder writes `src/*`, `image/*`, `template/*`, `claude/*`; the tester `tests/*`; the documenter `README.md`, `docs/*`; no stage writes `demo/*` or `pyproject.toml`):

1. `demo/todo-service/project/Makefile`, in the target `secrets`, the line

   ```
   	files=$$(printf '%s\n' $$files | grep -vE '^(uv\.lock|\.secrets\.baseline)$$' || true)
   ```

   becomes (one tab at the start, as before)

   ```
   	files=$$(printf '%s\n' $$files | grep -vE '^(uv\.lock|\.secrets\.baseline|.*\.costs\.jsonl)$$' || true)
   ```

   This is the line of `83eaa11` on `pkrahmer/factory-demo-todo`. With it, the source file is byte for byte the live demo's `Makefile`: the session compared the two through the GitHub API on 2026-10-18, and this line was the only difference. S0001's new test reads this file, so the test is red until this change is in.
2. `pyproject.toml`, `[tool.mutmut]`: the line

   ```
   also_copy = ["claude/", "docs/", "factory/", "image/", "security/", "template/", "README.md", "Makefile", "pyproject.toml", "uv.lock", ".secrets.baseline"]
   ```

   becomes

   ```
   also_copy = ["claude/", "demo/", "docs/", "factory/", "image/", "security/", "template/", "README.md", "Makefile", "pyproject.toml", "uv.lock", ".secrets.baseline"]
   ```

   S0001's new test reads `demo/todo-service/project/Makefile` from the repository root. mutmut runs the tests in its own copy, which holds only the folders `also_copy` names, so the test would fail there on the unmutated code and stop `make mutants` at the acceptance of every later feature that changes a module under `src/factory`. F0015's own acceptance runs no mutmut: its stories change no such module, so `make mutants` ends with `mutants: no module under src/factory changed by F0015`. The comment above the line ("The tests read these from the repository root; mutmut runs them in its own copy.") stays true. `tests/test_demos.py` finds the demos in mutmut's copy too, where today it finds none and passes on an empty list.

One before the handover (plan step 5), which may be made together with the two above:

3. factory-rf's own `Makefile`, in the target `secrets`, the line

   ```
   	files=$$(printf '%s\n' $$files | grep -vE '^(uv\.lock|\.secrets\.baseline|planning/.*|docs/runs/.*)$$' || true)
   ```

   becomes

   ```
   	files=$$(printf '%s\n' $$files | grep -vE '^(uv\.lock|\.secrets\.baseline|planning/.*|docs/runs/.*|.*\.costs\.jsonl)$$' || true)
   ```

   v1 writes no `.costs.jsonl` into factory-rf (the repository holds none today), so factory-rf's `make check` is green without this line. Once v1.1 builds factory-rf, every work item gets a sidecar, and without the line the first agent run of each turns `make check` red, as on the demo. If you like, `CLAUDE.md`'s `make secrets` parenthesis can say "over the files changed against `origin/main` but the factory's cost records". No test reads that file.

No dependency, no `Makefile` target, no `factory/stages.yml` change, no `security/*` entry and no `.secrets.baseline` entry. S0002 and S0003 need no change of the human's.

## Decisions taken for the human

Product decisions taken while writing the stories, for the human to review in one place. Each names where it was taken. Source of all: the drafting brief `planning/overnight/briefs/draft-F0015.md` (the session's proposals, to be confirmed by the human) and the night log's rows of 2026-10-18.

1. The run ids stay as they are, and the projects' secrets scans leave out the cost records (finding 1; S0001). A cost record holds run metadata (ids, the stage, times, counts, the cost), never a secret, so leaving the file out of the scan loses nothing. It also holds for any id the factory may write later and for any other scanner.
   - Rejected: a prefix on the run id (`run-` and the hexadecimal digits). It would get below detect-secrets' entropy limits today, but only as a side effect of that one tool's thresholds, not because of any rule. `RunId` (`src/factory/domain/cost_records.py`, pattern of 32 lowercase hexadecimal characters) is also the journal's `run` (F0014-S0007) and is in every sidecar already written. A new form needs a reader for both forms or a migration, and every test that builds a run id with `"a" * 32` changes.
   - Rejected: a `.secrets.baseline` entry per finding. Every run adds a new id, so the baseline would grow with every run and every project would have to keep it.
   - Rejected: a `pragma: allowlist secret` written into each line. The factory would write markers into its own data, and `CLAUDE.md` puts every new pragma behind a question.
2. The pattern is the human's, `.*\.costs\.jsonl` (`83eaa11` on the live demo), in the same line in the template and in the demo's source (S0001). It leaves out a file ending `.costs.jsonl` in any folder, the factory's `COST_RECORDS_SUFFIX`. A project file elsewhere with that ending is unlikely, and if one exists it holds the same kind of data. A path that only contains the suffix (`docs/a.costs.jsonl.txt`) or has no dot before it (`costs.jsonl`) is still scanned (a test row).
   - Rejected: the narrower `factory/features/.*\.costs\.jsonl`, the only place the factory writes sidecars. It would make the template's line differ from the live demo's, which the human has already set, and it would then need a second change there.
3. A test keeps the todo demo's `secrets` recipe equal to the template's (S0001), because the drift between the two is how the template's fault reached the demo source. Only that recipe is pinned. The other targets of the demo differ on purpose (the `openapi` target, the filled-in placeholders). The test needs `demo/` in mutmut's copy (the human's change 2).
4. The human's leave for F0015-S0001 (taken by the session for the human, to confirm). Its tester changes one test of an earlier story: `test_secrets_scans_the_changed_files_or_every_tracked_file` of `tests/test_template_makefile.py` (F0012-S0029) gains four rows, `sidecar-on-main`, `sidecars-on-branch`, `sidecar-only` and `look-alikes`. The module gains two constants for the sidecar paths and four setup functions beside the existing ones (`_on_main`, `_branch`, ...). The test's name, signature and body and its five existing rows stay. The rows belong in that test because the sides of one rule are rows of one parametrized test, and the file list of `make secrets` is that test's rule. Any other change to an earlier test is a question. (S0001, story text)
5. factory-rf's own `Makefile` gets the same exclusion as the human's change 3, before the handover rather than before S0001, because only v1.1 writes sidecars into factory-rf. (S0001)
6. The container runtime's init reaps the orphans: `init: true` on the service (finding 2; S0002). As this session reads coreutils' `timeout` (not run here): at the limit it sends `SIGKILL` to `claude` and then to its own process group. A `SIGKILL` cannot be caught, so `timeout` itself dies before it can wait for `claude`. `claude` and whatever it started are re-parented to PID 1. `sudo` waits only for `timeout`, and the factory's Python waits only for `sudo`. With `init: true`, Docker runs its `docker-init` (tini) as PID 1, and Podman, through the docker-compose provider, runs `catatonit`. Either one starts the entrypoint, forwards the stop signal and reaps every orphan. The fix also covers the processes of a project command killed at its time limit: `run_process` kills the whole group but waits only for its own child.
   - Rejected: the factory as the reaper (PID 1 calling `waitpid(-1)`, or a child subreaper). It would also reap the children that `run_process` waits for through `subprocess`, which would then find no exit status. That is a race with every project command and agent run, in the module that starts every process.
   - Rejected: tini installed in the image as its `ENTRYPOINT`. It would be one more pinned package, and both runtimes already ship an init. It would also work with a plain `docker run`, but the guide starts the container only through Compose, and the guide's paragraph names `--init` for a start without it.
   - Rejected: `timeout --foreground`. `timeout` would then wait for `claude` and reap it, but it would no longer kill `claude`'s own children, so they would run on past the limit.
7. No test in `make test` that a killed child's orphan is reaped (S0002). The reaper is the container runtime's init, which exists only in a running container, and `make test` starts none. A test that made its own subreaper would test the kernel, not the factory. The tests pin what the factory ships: the compose file's `init: true`, and the entrypoint's last line `exec python -m factory.entry.run`, which makes the factory the init's direct child, so that `docker stop`'s `SIGTERM`, which the init forwards, reaches the factory itself. The real reaping is the morning observation that S0002's docs criterion writes, run at the shakedown under Docker Desktop and under Podman. (S0002)
8. S0002 needs no leave: it adds a new test module. No test pins the set of the service's keys: `tests/test_compose.py`, `test_compose_project.py`, `test_image_credentials.py`, `test_claude_token_mount.py` and `test_token_folder.py` each read the keys they name. (S0002)
9. Finding 3 is expected and harmless, so it is documentation only (S0003). What the code shows:
   - `StageLauncher.launch` calls `CostRecorder.begin` right before the agent runs. `begin` writes the sidecar with the running run's `started` record into the work tree, uncommitted. The record travels in the stage's next commit, the result commit or the stall commit (`src/factory/application/stage.py`, `costs.py`; the decision log's "The sidecar is rewritten from memory after every undo"). So while the agent runs, `git status` shows the work item's `.costs.jsonl` as modified, or as untracked on a work item's first run.
   - Nothing can treat it as the agent's write. The sidecar lies outside every write path, and the undo reverts every cost-record file in an `in-progress` folder whatever the write paths say. After the undo, the factory writes the records again from memory (`AfterAgent.process`, `StallService.stall`), so an agent that changes or deletes the file changes nothing in the commit. `AfterAgent._entry` leaves the sidecar out of the journal's list of undone paths. The agent cannot commit the file, since the checkout's `.git` is the factory's alone (F0014-S0006), and the guard is not asked about a file the agent does not write.
   - The one real effect was finding 1: the agent's own `make check` scans uncommitted files too, and found the new run id. S0001 removes that.
   - The other way, pushing the `started` record before the run, was rejected by F0005-S0008 (a second commit per stage, and a crash would leave a record without a result) and stays rejected.
   - No rule is added to the shipped agents. The coder noticed the file, said so and did nothing to it. A rule would cost tokens on every run of every agent, for a note that harmed nothing.
10. Three stories, one per finding, and S0003 on its own rather than in S0001's docs criterion. S0001's docs criterion already changes three documents, and S0003's text concerns the stage protocol, not the template. A documentation-only story costs one short run per stage. S0003's tester and coder change nothing and end with an entry that says so. (All stories)
11. The human's answers of 2026-10-18 to the pre-check's points (source: the human, after the pre-check; taken by the session for the human, to confirm).
   - (1) The human's change 1 (the demo source line) is pushed to `main` before S0001 moves to `ongoing/`: v1 cuts the story's branch from `main` at intake and the coder cannot write `demo/`, so a later change never reaches the branch. (S0001)
   - (2) S0003 starts only after S0001 is merged, so "a later story may start first" does not apply to S0003. (S0003)
   - (3) At the Podman shakedown the operator checks `ps -eo pid,ppid,user,stat,args` right after `up -d`. PID 1 must be the runtime's init. The operator reports it if it is not, or if the container does not start. (S0002)
   - (4) Decisions 1 to 10 stand as written.
   - (5) v1's own compose file (`C:/Dev/Projects/factory`, the human's) is not changed by this feature: whether it gets `init: true` is the human's own choice, outside F0015.
