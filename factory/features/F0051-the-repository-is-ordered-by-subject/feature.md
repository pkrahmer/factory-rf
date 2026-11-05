# The repository is ordered by subject

## Goal

`src/factory/` is ordered by layer today: `domain` (57 modules), `application` (41) and `adapters` (34), so one subject, the hosting service for example, is spread over three folders between unrelated neighbours, and a reader sees how the code is layered but not what the factory is made of. The rest of the repository has grown the same way: the root of `tests/` holds about 200 modules, `docs/operator-guide.md` has 2,603 lines, the agent files sit in a folder named after one of the two runtimes, and the VM's files and the project template sit at the root beside the operator's other tools. This feature orders the repository by subject, without changing what the factory does: the code moves into seven areas with the three layers inside each, the tests follow the code and the root of `tests/` is sorted, the project guide gets one file per area, the operator guide becomes a folder of topics, `claude/` becomes `agents/`, and `vm/` and `template/` move into `operator/`. Done when every story below is merged and `make check` is green.

## Scope

- The seven areas `shared`, `hosting`, `work`, `agents`, `watching`, `machine` and `pipeline` under `src/factory/`, each with its `domain`, `application` and `adapters` inside, one story per area; `entry/` and `contract/` stay where they are (S0001 to S0007).
- The layer rule (domain below application below adapters, entry on top) holds inside every area and across areas, and blocks in `make check` for each area from its move on (feature decision 3).
- The tests mirror the areas; the root of `tests/` holds only `conftest.py` and folders (S0001 to S0008).
- The project guide has one file per area (S0009).
- The operator guide is a folder of topic files, and the document check follows it (S0010).
- `claude/` becomes `agents/`, and `/etc/factory/claude` becomes `/etc/factory/agents` (S0011).
- `vm/` becomes `operator/vm/`, and `template/` becomes `operator/template/` (S0012).

## Out of scope

- Untangling the areas: the code imports across areas in both directions (432 imports cross areas on 2026-11-04, most through `Boundaries`), so a rule of which area may use which can only report for now (feature decision 3). Splitting `Boundaries` per area and cutting the cycles is a later feature.
- Any change of behaviour, of a test's checks, of a name of a module, class or function, or of the records contract.
- `docs/decisions.md`'s old entries: the log is history and keeps the old paths.
- `demo/`: it stays at the root (the human, 2026-11-04).
- `operator/claude/` and `operator/opencode/`: the operator's commands for each runtime keep their names.
- Everything else in `planning/f0051-candidates.md`: routing, seams, agent rules, context size and stability are postponed (the human, 2026-11-04).

## Stories

The build order: S0013 first, a docs repair carried over from F0050 (F0050-A0003 proposed it as F0050-S0015), because its smoke test imports `factory.domain.git`, which S0002 moves. Then the area with the most users first, then from the smallest to the largest, the pipeline last, because it holds `Boundaries`, which nearly every other area imports.

- S0013: The operator guide's push error example shows the ref line the factory writes (from F0050-A0003)
- S0001: The shared area holds what every area uses
- S0002: The hosting area holds git and the hosting service
- S0003: The work area holds the work items
- S0004: The agents area holds the agent runs
- S0005: The watching area holds what shows the factory and what it costs
- S0006: The machine area holds containers, images and disks
- S0007: The pipeline area holds the stages and the tick
- S0008: The root of `tests/` holds only its folders
- S0009: The project guide has one file per area
- S0010: The operator guide is a folder of topics
- S0011: The agent files live in `agents/`
- S0012: The VM's files and the project template live in `operator/`

## The human's changes

- **At S0001's start, once for all moves:** `pyproject.toml`'s import-linter contracts become four, tried on today's code and on a half-moved test package on 2026-11-05: `Layers` over the container `factory` with `entry` and the old layers marked optional; and three forbidden contracts with wildcards, which hold for every area as soon as it exists and for the old layers in the meantime: no `domain` (`factory.*.domain`, `factory.domain`) imports any `application`, `adapters` or `entry`; no `application` imports any `adapters` or `entry`; no area's `adapters` imports `entry`. So each area's layer rule blocks from the story that moves it, with no change per story. `CLAUDE.md`'s exception for `src/factory/adapters/process.py` names `src/factory/shared/adapters/process.py` as well, so that it holds before and after the move. The guards that `[tool.mutmut]` leaves out follow their test modules when those move (at each merge). At each merge, the paths of moved modules in `security/duplicates-baseline.txt` follow too, so that `make duplicates` does not report their accepted findings as new and gone.
- **At S0007's start:** `Layers` loses the optional old layers, which are gone after the story.
- **At S0007's merge:** a report of the area dependencies outside `make check`: a separate import-linter configuration with one `layers` contract over the areas in the order `pipeline`, `watching`, `agents`, `machine`, `work`, `hosting`, `shared`, run by a new target `make areas`, which is never part of `make check`. `CLAUDE.md`'s *Architecture* and *Tests* describe the areas and the new test folders.
- **At S0008's start:** `CLAUDE.md`'s *Tests* says that shared helpers live in `tests/support/` and names the other folders; a path that `pyproject.toml` needs for mypy or pytest, if the tester asks for one.
- **At S0010's merge:** `factory/story-form.md` and `CLAUDE.md`'s *Docs* name `docs/operator-guide/`; `docs/operator-playbook.md` follows.
- **At S0011's start:** the coder's write path `claude/*` in `factory/pipeline.yml` becomes `agents/*`; `CLAUDE.md` names `agents/agents/`. After its merge, on factory-vm: rebuild `factory-stage:vm`, renew `image-id`.
- **At S0012's start:** the write paths `vm/*` and `template/*` become `operator/vm/*` and `operator/template/*` (already covered by `operator/*` entries where they exist); `CLAUDE.md` and `Makefile` follow. After its merge, on factory-vm: the installed unit and the credential helper are checked against their new sources.

## Decisions taken for the human

1. **Areas with layers inside, not layers with areas inside.** A subject's domain, application and adapters sit side by side in `factory.<area>`, so a story that touches one subject touches one folder. Reason: the human, 2026-11-04, after the sketch of the split; the layers keep their rules.
2. **Seven areas, by a map checked against the imports.** The map is the table of each move story. A module goes to the area of its subject; the kill points of the fault tests (`kill_points`, `kill_point_cases`) go to `shared`, since the adapters of three areas use them; everything that shows what the factory does or what it costs goes to one area `watching` (the human, 2026-11-04). A module whose place turns out wrong in a story is named in the intake's question, not moved on the side.
3. **The layer rule blocks, the area rule only reports.** The layer rule blocks for each area from the story that moves it, through forbidden contracts with wildcards set once at S0001's start (the human, 2026-11-04). A rule of which area may use which cannot block yet, because the areas import each other both ways, mostly through `Boundaries`; it is written as a report outside `make check` (the human, 2026-11-04, when shown the 432 crossing imports).
4. **Moves only, nothing left behind.** A module keeps its name, its content and its docstring; only the import lines change. No re-export stays at the old path, so a missed import fails at once rather than later. Reason: a shim would hide a half-done move and stay for good.
5. **A leave for every move story's tester.** In each story of F0051, the tester may change, in any test module, the import lines and the module and file paths of the modules that the story moves, move test modules to their new folders with `git mv`, create the new test packages, and change the guards that pin the old layout (`tests/test_layers.py`, `tests/domain/test_hosting.py::test_domain_modules_import_only_stdlib_pydantic_and_domain`, `tests/module_names.py`, `tests/source_search.py` and the `*_search.py` guards) so that they check the same rule over the new layout; nothing else in those modules. Each entry names the earlier test files it changed. The coder moves the source files. The tester makes all these test changes in its first run, before the code moves (the tests are then red by design, as for any new test): the coder's write paths do not hold `tests/`, so a test change the coder makes is dropped from its take and the check after `doing` turns red (S0001, 2026-11-05).
6. **One story per area.** About twelve smaller runs rather than a few big ones: a move's diff stays small enough for a full review, a failure stops one area only, and a round repeats less (the human, 2026-11-04).
7. **The new top-level packages are allowed.** The seven areas are the new top-level packages that `CLAUDE.md` asks about; this feature is the human's leave for them, and for no other.
8. **The intake's standing answers for the move stories** (given on F0051-S0003's PR #558, 2026-11-05, for S0003 to S0007). Criterion 1 also checks that `AREAS` has the story's area as a key whose modules are exactly those of its table. The test packages' `__init__.py` files and the one-line form of a docstring are not tested. The areas moved before a story are those of the stories merged before it (S0013 moved none). Criterion 3 covers `import factory.x.y`, `from factory.x.y import z` and `from factory.x import y`, as `imports()` of `tests/source_search.py` reads them.
