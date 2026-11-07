# Project guide

The guide for agents working on `kumpel-factory`: how the code is laid out, where a change belongs, which conventions the checks do not catch, and what to read first. It is this index, one file per area of `src/factory/` and `operator.md` for the operator's scripts: read the index, then the files of the areas your story touches. It grows with each story: the documenter stage fills it in from the stories' docs criteria. `CLAUDE.md` holds the rules every change follows.

A file of the guide is split by the same rule before it passes about 600 lines: its sections go by subject to a new file, and the new file is named here.

## The code's layout

Under `src/factory/` the seven areas, `entry` and `contract` hold all modules. An area is a subject that holds its modules in three layers (`domain`, `application`, `adapters`) inside its own package, and `tests/guards/test_areas.py` lists every area's modules in one table. The area `shared` (`factory.shared.domain`, `factory.shared.application`, `factory.shared.adapters`) holds what every other area uses: errors, times, identifiers, paths, settings, the records contract, the document and duplicate checks, the kill points, the file ports, the clock, atomic files and processes. The area `hosting` (`factory.hosting.domain`, `factory.hosting.application`, `factory.hosting.adapters`) holds git, the hosting service, pushes, the hand-over and the opening of pull requests. The area `work` (`factory.work.domain`, `factory.work.application`, `factory.work.adapters`) holds the work items, their journal, the story form, answers, decisions, send-backs, the archive and the feature acceptance. The area `agents` (`factory.agents.domain`, `factory.agents.application`, `factory.agents.adapters`) holds the agent runs: the two runtimes and the fake one, the agent files, prompts, write paths, tool uses, provider limits and tokens. The area `watching` (`factory.watching.domain`, `factory.watching.application`, `factory.watching.adapters`) holds what shows the factory and what it costs: cost records, bills, the machine measures, human waits, transcripts, the board, the watcher, the factory log and the health file. The area `pipeline` (`factory.pipeline.domain`, `factory.pipeline.application`, `factory.pipeline.adapters`) holds the pipeline definition, the stages, the checks, the tick and its handlers, claims, leases, stops, stalls, recovery and the boundaries. The area `machine` (`factory.machine.domain`, `factory.machine.application`, `factory.machine.adapters`) holds containers, images, the stage environment, snapshots, disks, the preflight, the project's commands and the machine's power.

Each area's package names its page: the docstring of `src/factory/<area>/__init__.py` ends with the line `Guide: docs/project-guide/<area>.md`, and that of `src/factory/entry/__init__.py` names this index. `tests/guards/test_area_guides.py` fails when a line is missing or names a file that does not exist. The modules' own docstrings carry no such line.

## The files

Each file starts with a title and a sentence on what it covers.

A guard (`tests/guards/test_project_guide_files.py`) requires every page of the folder to be named in this section and every area to have its page. It reads a list item in this section as a page entry when the item starts with a name in backticks and goes on to a sentence that ends in a full stop. Every other list item in this section starts with a word, plain or in italics. A list item that starts with a name in backticks, such as `## The files`, is read as a page, and the guard fails when no such page exists. Headings are free except these, which keep their names, because a check or a script finds them by name:

- The heading `## The files` in this index: the guard reads the pages named under it, so renaming it leaves every page unnamed.
- *Kill points* and *Fault-injection paths* in this index, *Install* and *Configuration* in `docs/operator-guide/install.md`, and *The stops* in `docs/operator-guide/stops.md`: the document check (`make documents`) requires them.
- *Replaced from v1*, wherever it stands: the document check exempts it from its search for v1 words. It may be removed, as the style page's rules 1 and 7 ask in the rewrite, but not renamed.
- *The machine* and *The rebuild after a merge* in `docs/operator-guide/machine.md`: `operator/vm/setup.sh` names them in its messages.

The folder holds these pages:

- `README.md` (this index): what holds for all code. Sections: *The code's layout*, *The files*, *Shared test helpers*, *Errors*, *The models' configuration*, *Kill points*, *Fault-injection paths*, *The demos* (`factory.entry.check_demos`).
- `style.md`: how the documents read: the rules for all documents, and for the operator guide, the project guide and the README, each with its reader and an example. The documenter and the reviewer judge by it.
- `glossary.md`: the words the factory gives its own meaning, one entry each, sorted alphabetically.
- `shared.md`: the area `shared` (`src/factory/shared/`), as far as it starts processes and runs this repository's checks. It describes the one module that starts processes (`factory.shared.adapters.process`) and the commands behind `make duplicates` and `make documents` (`factory.shared.domain.duplicates`, `factory.shared.domain.documents`, `factory.entry.check_duplicates`, `factory.entry.check_documents`). The rest of the area is described where it is used: identifiers, paths, sections and the records contract in `work.md`, the settings in `hosting.md` and `machine.md`, errors and kill points in this index. Sections: *Starting a process*, *The duplicates report*, *The document check* (with *The name check* and *The settings check*). `factory.shared.domain.settings.SETTINGS` is the table of every setting `read_settings` reads.
- `hosting.md`: the area `hosting` (`src/factory/hosting/`), git and the hosting service. It describes the hosting-service interface with its PyGithub and fake implementations (`factory.hosting.application.hosting`, `factory.hosting.adapters.pygithub_hosting`, `factory.hosting.adapters.fake_hosting`, `factory.hosting.domain.hosting`) and the git wrapper (`factory.hosting.application.git`, `factory.hosting.adapters.git_cli`, `factory.hosting.domain.git`). It also names `factory.shared.domain.settings`. Sections: *The hosting service*, *The git wrapper*.
- `work.md`: the area `work` (`src/factory/work/`), the identity, data, files, sections and form of a work item. It describes `factory.shared.domain.identifiers`, `factory.shared.domain.paths`, `factory.work.domain.work_item`, `factory.work.domain.journal`, `factory.shared.domain.sections`, `factory.work.domain.story_form`, `factory.work.adapters.work_item_markdown` and `factory.entry.check_story`. It also names `factory.work.application.acceptance`, `factory.work.application.acceptance_reading`, `factory.shared.application.files`, `factory.work.application.work_items`, `factory.work.domain.acceptance`, `factory.shared.domain.contract`, `factory.shared.domain.times`, `factory.entry.contract`. Sections: *Identity, order and places of work items*, *The data of a work item*, *Reading and writing a work item file*, *Sections of a Markdown body*, *The form check of a story*, *Reference*. Subsections other files refer to: *The records contract*, *The feature acceptance*.
- `agents.md`: the area `agents` (`src/factory/agents/`), the agent runtime, the agent files, the shipped agents, the template and the write paths. It describes the agent-runtime interface and its implementations (`factory.agents.application.agent_runtime`, `factory.agents.adapters.claude_runtime`, `factory.agents.adapters.agent_launch`, `factory.agents.domain.agent_runs`), the agent files reader (`factory.agents.adapters.agent_files`), the files under `agents/` and the write paths (`factory.agents.application.write_paths`, `factory.agents.domain.write_paths`). It also names `factory.agents.adapters.fake_agent_runtime`, `factory.agents.adapters.opencode_runtime`, `factory.shared.adapters.validation_faults`, `factory.agents.application.project_agents`, `factory.agents.domain.provider_limits`. Sections: *The agent runtime*, *The agent definition reader*, *The shipped agents, settings and template*, *Replaced in v1.2*, *Replaced from v1*, *The write paths*, and the write paths' *Replaced in v1.2*. Subsections other files refer to: *The opencode runtime*, *The agent's home*.
- `watching.md`: the area `watching` (`src/factory/watching/`), what shows the factory and what it costs: the evaluation, the board, cost records, bills, the human's waits, transcripts and the machine's readings. It describes `factory.pipeline.domain.evaluation`, `factory.watching.application.watcher`, `factory.work.domain.move_rule`, `factory.entry.watch` (`factory-watch`), `factory.watching.domain.board`, `factory.watching.application.board`, `factory.watching.domain.cost_records`, `factory.watching.adapters.cost_records_jsonl`, `factory.watching.application.costs`, `factory.watching.domain.bills`, `factory.watching.domain.human_waits`, `factory.entry.bill` (`factory-bill`), `factory.watching.application.transcripts` and the machine readings (`factory.watching.domain.machine`, `factory.watching.application.machine`). It also names their adapters (`factory.watching.adapters.transcript_files`, `factory.watching.adapters.machine_files`, `factory.watching.adapters.factory_log`, `factory.watching.adapters.health_file`, `factory.watching.adapters.record_log_jsonl`). Sections: *The evaluation*, *Cost records*, *Bills*, *The factory log and the health file*, *No code reads data from the journal's text*, *Reference*. Subsections other files refer to: *The move rule*, *The board*, *Cost records* (*When a record is created, completed and committed*, *Transcripts and the machine's readings*), *The bill command*, *The watcher's command line*.
- `machine.md`: the area `machine` (`src/factory/machine/`), the environment a stage runs in, behind interfaces: the stage environment itself and the dataset and containers under it, and the project commands. It describes `factory.machine.application.stage_environment`, `factory.machine.application.snapshots`, `factory.machine.application.containers`, `factory.pipeline.application.take`, `factory.machine.domain.containers`, `factory.machine.adapters.zfs_snapshots`, `factory.machine.adapters.podman_runs`, `factory.shared.adapters.printed_output`, `factory.machine.adapters.fake_snapshots` and `factory.machine.adapters.fake_containers`, and the project-commands interface and its make implementation (`factory.machine.application.project_commands`, `factory.machine.adapters.make_commands`). It also names `factory.shared.domain.settings` and `factory.entry.wiring` for the stage environment's settings and wiring, and `factory.watching.adapters.record_log_jsonl`, `factory.machine.application.disk_records`, `factory.pipeline.application.known_results`, `factory.machine.application.preflight`, `factory.pipeline.domain.checks`, `factory.machine.domain.command_records`, `factory.machine.domain.disk`, `factory.pipeline.domain.known_results`, `factory.entry.inputs`. Sections: *The cycle*, *The snapshots*, *The container runs*, *The copy snapshots*, *The fakes*, *The ZFS adapter*, *The podman adapter*, *The stage environment*, *The container environment*, *The sync command*, *The agent's container*, *The take*, *The checks*, *The settings and the wiring*, *The project's stage image*, *The preflight*, *Project commands*, *Known results*, *Mutation testing* (`make mutants`, the sweep form), and a *Reference* with the exact commands, faults and settings.
- `pipeline.md`: the area `pipeline` (`src/factory/pipeline/`), the pipeline definition, a stage from the claim to the result commit, the take's rule, the tick, its handlers, the stops and the boundaries. It describes `factory.pipeline.application.claims`, `factory.pipeline.domain.lease`, `factory.pipeline.domain.pipeline_definition`, `factory.pipeline.application.pipeline_loading`, `factory.pipeline.application.task`, `factory.agents.domain.prompts`, `factory.hosting.application.opening`, `factory.pipeline.application.stage`, `factory.pipeline.application.stalls`, the rule in `factory.pipeline.application.take`, `factory.pipeline.application.tick`, `factory.pipeline.application.handlers`, `factory.pipeline.application.recovery`, `factory.pipeline.domain.stops`, `factory.pipeline.application.stops`, `factory.pipeline.application.boundaries` and `factory-run`, `factory-health`. It also names `factory.pipeline.adapters.pipeline_yaml`, `factory.agents.application.provider_limits`, `factory.work.domain.decisions`, `factory.shared.domain.errors`, `factory.work.domain.labels`, `factory.hosting.domain.post_texts`, `factory.shared.adapters.atomic_file`, `factory.shared.adapters.clock`, `factory.machine.adapters.disk_space`, `factory.watching.adapters.factory_log`, `factory.watching.adapters.health_file`, `factory.machine.adapters.preflight_stamp_file`, `factory.watching.application.board`, `factory.pipeline.application.dispatcher`, `factory.machine.adapters.power_off`, `factory.pipeline.application.idle_shutdown`, `factory.watching.application.machine`, `factory.pipeline.application.scheduler`, the modules of `factory.pipeline.application.handlers` (`closed`, `comments`, `hand_over`, `lookups`, `merged`, `questions`, `recording`, `reject`, `run`, `run_gate`), `factory.work.domain.answers`, `factory.work.domain.archive`, `factory.watching.domain.board`, `factory.pipeline.domain.events`, `factory.hosting.domain.hand_over`, `factory.machine.domain.preflight`, `factory.pipeline.domain.recovery`, `factory.work.domain.send_back`, `factory.pipeline.domain.stop_table`, `factory.pipeline.domain.tick_status`, `factory.entry.health`, `factory.entry.run`, `factory.entry.wiring`. Sections: *The claim service*, *The pipeline definition*, *The prompt and the request for a stage*, *Opening a work item*, *Starting a stage*, *Stalls*, *After the agent run*, *The decision rules*, *The stage protocol*, *The take's rule*, *The tick*, *The handlers of the events*, *The stop records* (with *The clock, the log and the stores*), *Boundaries*, *The idle shutdown*. Sections other files refer to: *Boundaries* and *The idle shutdown*.
- `operator.md`: the operator's scripts under `operator/` and their tests. It describes the site file and its loader (`operator/lib/site.sh`, `operator/bin/site`), the hosting client (`operator/lib/hosting.sh`), `operator/job/job.sh`, the sanitiser (`operator/bin/sanitise`) and the skill's scripts (`operator/skill/kumpel/scripts/`). Sections: *The layout*, *The site file and its loader*, *The hosting client*, *`job.sh`*, *The sanitiser*, *The skill's scripts*, *Tests of the scripts*.

## Shared test helpers

The root of `tests/` holds `conftest.py` and folders, each a package:

- `support/`: the shared helpers, imported as `support.<name>` (`from support.bill_support import completed_records`). `tests/` is on `sys.path` (pytest's rootdir import; mypy names the files the same way), so no relative import is needed.
- `guards/`: the structural guards: searches over the source (`test_*_search.py`), `test_*_removed.py`, `test_shared_*.py`, `test_no_*.py`, `test_suite_*.py`, `test_layers.py`, `test_areas.py`, `test_test_names.py`, `test_model_configuration.py`, the umask guard, the layout guard `test_tests_layout.py`, and the tests of the helpers themselves.
- `operator_scripts/`: the tests of the operator's scripts under `operator/` (not `operator/`: a package of that name would hide the standard library's).
- `vm/`: the tests of the files under `operator/vm/` (`test_vm_*.py`, `test_stage_image*.py`).
- `agent_files/`: the tests of the files under `agents/` and `operator/template/`.
- `<area>/<layer>/` and `entry/`: the tests of the modules of `factory.<area>.<layer>` and of `factory.entry`, mirroring `src/factory`. A test module that imports no `factory` module but a helper or a source text sits in `guards/`.

`tests/guards/test_tests_layout.py` fails when the root holds anything but `conftest.py` and packages, when a helper exists outside `support/`, when a module imports a helper by its bare name, and when a test module sits outside the folder of its name's pattern.

A guard that a module stays removed names the module at the path it had (for example `factory.adapters.landlock`) and checks it with `module_exists_anywhere` of `tests/support/module_names.py`, so that the module is not found in any area either; `tests/guards/test_removal_guards_search.py` fails when a test module with an old layer path calls `module_exists`.

A helper that more than one test module uses lives in `tests/support/` (a fixture, in `tests/conftest.py`), and a test module imports it from there; `CLAUDE.md`'s standing leave to move a shared test helper intends this. Before writing a helper, look here: the reviewer counts a copy as a finding. The guards `tests/guards/test_shared_*.py` fail on a copy of a shared helper, and `test_shared_bodies.py` finds a copy of `log_lines`, `pushed`, `pushed_state`, `remote_document` and `push_state` by its body under any name. A story that adds such a module names it in this list through its docs criterion. A story that adds a fixture to either conftest names it in that conftest's line through its docs criterion.

No module under `tests/` imports a test module (a module whose file name begins with `test_`), in any form: `from x.test_y import ...`, `import x.test_y`, `from x import test_y`. Such an import runs the other module's setup at import and makes a removed or renamed test module fail tests of something else. What two test modules share lives in a support module, a new one named `*_support.py`, or, for a fixture, in `tests/conftest.py`. The guard `tests/guards/test_shared_imports.py` reads every `*.py` file under `tests/` with `ast` and fails with one line `<file>:<line>: <module>` for each such import. Modules that exist under other names (`human_clone.py`, `recording_log.py` and the rest below) keep them.

Support modules added for this rule, each holding what test modules once imported from each other:

- `support/agent_definition_support.py`: `COMPLETED`, the completed agent run of the agent-definition tests.
- `support/agent_login_support.py`: `API_LOGIN` and `SUBSCRIPTION`, the two stand-in logins, and `_utf_16`, which writes a file in UTF-16.
- `support/before_approval_support.py`: `ROLES`, `FIXTURE` and `without_approval`, the definitions of the tests of `is_before_approval`.
- `support/check_documents_support.py`: `MISSING_LINES` (the document check's output for a missing guide file), the output filters (`without_report_lines`, `findings_from`, `line_of`), `append_block` for a block added to a document, and `write_checked_list`, which writes the list of checked documents and commits only a change.
- `support/claude_reply_support.py`: `LOGIN` and `BUDGET_STOP`, the stand-in login and the reply of a run stopped by its budget.
- `support/claude_resume_support.py`: the resume tests' reply builders (`_reply`, `_budget_reply`), request and runtime (`_request`, `_runtime`), `_after` (the argument after a flag) and `LIMIT`.
- `support/contract_login_support.py`: `committed` (the parsed committed schema file of a name) and `values` (the values a schema allows). Its schema folder is `SCHEMAS` of `contract_support.py`, assigned nowhere else.
- `support/cost_image_support.py`: the cost tests' launch and settings with an image (`_launch`, `_settings`, `MAKEFILE`).
- `support/cost_records_support.py`: cost record texts and builders (`COMPLETED_LINE`, `STARTED_LINE`, `REQUIRED`, `STARTED_AT`, `STARTED_AT_TEXT`, `_completed`, `_started`).
- `support/git_interface_support.py`, `support/hosting_interface_support.py`: `OPERATIONS`, the operations the git and hosting interfaces name.
- `support/known_results_support.py`: the known-results rig (`Rig`, `_rig`, `_answering`, `_result`, `DEFINITION_YAML`, `TIME_LIMIT`).
- `support/opencode_events_support.py`, `support/opencode_resume_support.py`: `WAIT_SECONDS`, how long the opencode stand-ins wait; `tests/guards/test_time_limits.py` reads them here.
- `support/probe_login_support.py`: `LOGIN_FILE` and `HINT` of the login probe tests.
- `support/sections_support.py`: `TICKS`, three backticks, for fenced text in section tests.
- `support/two_routes_support.py`: `TWO_ROUTES`, a pipeline definition of two routes to two approval stages, in the shipped order.
- `support/stage_image_support.py`: what the project image tests share: `BASE_IDENTITY` (the base image's identity, `"sha256-base"`), `FIRST` and `SECOND` (two stage files that satisfy the rule), `StageSeen` (what one tick ran with: image, identity, `PATH`, builds asked for) and `built_path` (the project image's `PATH` after a given build).
- `support/story_form_support.py`: `FORM`, `SMOKE` and `_state`, a story form's text and a state at a stage.

Every module of `tests/support/` (imported as `support.<name>`), and the two conftests:

- `support/conftest.py`: the fixtures of the whole suite. Every test: `reopened_tmp_path` (autouse; after a test that uses `tmp_path`, gives its owner back every folder and file under it). Doubles and time: `kill_points` (inert kill points), `agent_runtime` and `hosting` (the fakes, on those kill points), `clock` (a manual clock at noon UTC on 2026-10-12). Git: `remote_template` (session-wide; one remote that each test's remote copies), `remote` (a bare repository whose `main` holds a small factory layout and a `Makefile` whose `sync` target succeeds and prints nothing, `@:`, because every stage on the fixture runs `make sync`), `checkout` (a `GitCli` on a fresh clone of `remote`), `human` (the human's own `HumanClone`). Paths and settings: `agent_home` (a path in `tmp_path`; nothing is created), `local_settings` (instance settings whose checkout, state and agent home lie in `tmp_path`), `disk_settings` (settings whose checkout and state directory lie under `tmp_path`), `disk_records` (the disk record log in `tmp_path`), `versioned_podman` and `listing_zfs` (the stand-in `podman` and `zfs` of the container-extras tests), `hosted_environment` (a valid environment with token and image identity files in `tmp_path`), `base_identity_settings` (the instance settings with `BASE_IDENTITY` as the image identity) and `base_image` (the base image those settings name). The factory on those: `boundaries` (the interfaces on the test's checkout, fakes and clock, as an instance does: `FakeSnapshots` and `FakeContainerRuns` over `<tmp_path>/workspace` with an empty base, so stages run in `ContainerEnvironment`, while the project commands stay `MakeProjectCommands` on the host checkout), `definition` (the remote's parsed pipeline definition, with the acceptance stage `acceptance`), `installed_agents` (a valid agent file for every role of that definition), `minimal` (the minimal documents of the document check under `tmp_path / "root"`), `walk` (an `AcceptanceWalk` over the feature `F0002-todo`, due with two archived stories). The recovery proof: `world` (a world built under `tmp_path`), `work_item` (a story started in that world). Runtime tests: `layout` (a checkout with `src` and `other`, a home and a temporary root), `records` (the stop records in the test's state directory), `recorder` (replaces the runtime's `run_process` with a `Recorder`).
- `pipeline/application/handlers/conftest.py`: the fixtures of the handlers' tests under `tests/pipeline/application/handlers/` only: `snapshot_of` (builds a snapshot, not on the remote, holding a given state), `state_with` (builds a state at `doing` with one journal record and the pull request), `event_of` (builds an event of a kind about a snapshot), `pull_request` (the number of an open draft pull request of the work item's branch), `work_item` (the snapshot of a work item the human pushed to its branch, fetched locally: a published work item of the handlers' tests, not the root's started story).
- `support/acceptance_support.py`: `report_of`, a feature's acceptance report whose journal holds given entries.
- `support/acceptance_walk.py`: `AcceptanceWalk`, a walk of one feature's acceptances over real ticks with the human's acts between, and its constants.
- `support/bill_support.py`: `completed_records` and `sidecar_text`, completed cost records and the text of their sidecar.
- `support/branch_reading.py`: the work item on a work item's branch and the factory's posts on its pull request (`remote_document`, `error_posts`, `push_state`).
- `support/run_layout_support.py`: the run layout and the request of the tests that run a stand-in agent (`build_layout`, `write_script`, `read_records`, `run_request`), and `run_end(runtime, layout)`, which runs a stand-in agent and gives `(detail, end_reason)`; the Claude and the opencode runtime tests share it.
- `support/container_support.py`: the container environment's rig: `fake_dataset(root)` (the fakes on `<root>/workspace` with an empty base `<root>/workspace-base`; the `boundaries` fixture and the recovery world use it), `container_dataset` (the dataset of the `boundaries` fixture with its fakes, the base removed when `with_base` is false), `push_main`, `sync_makefile`, `dataset_git`, `local_branches`, `timing_lines`, `WorkspaceRuntime`, `FIVE_MINUTES` (the time limit the container tests share), `TIMING_PREFIX` and `RESET_PREFIX` (`"stage environment: reset"`, the log line that the reset writes; `test_suite_fixtures.py` and `test_stage_on_container_fakes.py` import it), and the whole stage on that dataset: `whole_stage` (the agent writes `INSIDE` and `NOTES`, which `stage_run_support.py` holds; `project_commands` picks the stage's project commands, the host's by default) and `assert_taken_and_pushed` (its five assertions).
- `support/contract_support.py`: `SCHEMAS` (the committed schema folder), the contract command's output lines and `MainRow`, a row of `main`'s cases, and `committed_is_generated(entry, version=None)`, which checks the committed schemas against the generated ones and, when given a `version`, that version's text.
- `support/crash_support.py`: a work item claimed by this instance, ready to crash (`claim`, `expired_claim`, `crash_event`, `handler`), for the crash-cap tests.
- `support/definition_support.py`: `pipeline_definition`, the test remote's pipeline definition read through the boundaries' reader, which the `definition` fixture returns too, for helpers that take no fixtures.
- `support/disk_support.py`: `FakeDiskSpace`, a fake of the disk-space interface that answers per path.
- `support/dockerfile_support.py`: readers of a Dockerfile's text and the pins' forms, for the tests of `operator/vm/Dockerfile` (`tests/vm/test_stage_image.py`, `tests/guards/test_pins.py`): its instructions and commands (`_instructions`, `_commands`), the `ARG` defaults and `ENV` values (`_arg_defaults`, `_env`), the `FROM` references, `floating_references` (what floats: a `FROM` without a digest, a package without a version, `latest`, a download piped into a shell) and the patterns `DIGEST` and `THREE_NUMBERS`.
- `support/document_texts.py`: builders for the four documents' texts, clean unless a test asks for a fault (`readme`, `operator_guide`, `project_guide`, `decision_log`, `clean_texts`, `write_documents`). They read the code's tables when called, so a test can extend one with `monkeypatch`.
- `support/minimal_documents_support.py`: `minimal_documents` (a git repository with the smallest documents the check accepts) and `add_and_commit`; the document check's tests run on them.
- `support/evaluation_support.py`: the shared inputs of the evaluation's tests (a pipeline definition, snapshots, lookups, claims).
- `support/function_support.py`: `functions` (the top-level functions of a source text, read with `ast`) and `without_docstring` (a body's statements, a leading docstring left aside).
- `support/git_support.py`: helpers for tests against real git: isolated runs, the bare remote and its copies, stand-in executables, agent files (`run_git`, `make_remote`, `copy_remote`, `clone`, `commit_all`, `install_agents`). `REMOTE_FILES` holds a `Makefile` with the target `sync` (recipe `@:`); a test that pushes its own `Makefile` before a stage or a probe gives it the same target, or the stage's `prepare` fails.
- `support/human_clone.py`: `HumanClone`, a second clone of the test remote that acts as the human: starts stories, pushes, merges.
- `support/log_support.py`: `log_lines`, the factory log a test's state directory holds.
- `support/module_names.py`: asks whether a module of the factory still defines a name.
- `support/observing_runtime.py`: `ObservingRuntime`, an agent runtime that records what the remote and the hosting fake hold when a run starts.
- `support/podman_support.py`: the stand-in `podman` and its plan; `IMAGE`, the stage image name `"factory-stage:1"`, which every test that names it imports from here.
- `support/preflight_support.py`: the preflight's rig: `Rig`, its recording stand-ins (`RecordingWhich`, `RecordingCommands`), the constants the preflight tests share (`IMAGE`, `OTHER_IMAGE`, `MAKEFILE`, `TOOLS`, `ROLES`), the fixtures `rig` and `red_main` (a test module binds them with `rig = preflight_support.rig`; they are not in `conftest.py` because two other rigs carry that name), and `fail_once` and `failed_once`, the rig after one probe of a red main.
- `support/probe_support.py`: the agent environment, the completed run and the opencode texts (`opencode_died`, `opencode_sso_hint`) of the probe tests.
- `support/process_support.py`: real child processes in tests (`python_argv`, `Recorder`, `is_gone`).
- `support/project_command_support.py`: `raising`, the answers for a recording stand-in of the project commands.
- `support/proof_support.py`: the recovery proof, described under *Kill points* and *Fault-injection paths*.
- `support/recording_stand_in_support.py`: `recording_stand_in` (a stand-in program that appends its arguments to a `calls` file beside it and prints a given text) and `recorded_calls` (the argument lists it recorded), for the wiring tests.
- `support/record_support.py`: `UnwritableRecordLog`, a record log that cannot be written.
- `support/recording_log.py`: `RecordingLog`, a factory log that keeps the lines written to it.
- `support/run_process_recorder.py`: `Recorder`, a stand-in for the runtime's `run_process` that keeps each request.
- `support/root_support.py`: `AS_ROOT`, the pytest mark that skips a test needing a folder that root could still write in.
- `support/agent_run_support.py`: the agent runs' completed result and request, and `RecordingRun` (a run function that records its request).
- `support/search_support.py`: searches of the test modules under `tests`: `modules_matching` (the modules that match a pattern), `modules_assigning` (the sorted modules that assign a given value at top level) and `top_level_copies` (the names a top-level assignment in a source text gives a value, plain or annotated). `tests/guards/test_shared_constants.py` and `tests/guards/test_shared_stage_constants.py` call them; a later guard calls `modules_assigning` instead of walking the modules again.
- `support/settings_support.py`: `BASE`, the environment with the two required settings, `AGENT_HOME` (the absolute agent home that `BASE` and the tests' `InstanceSettings` give), `NOT_A_NAME` and `SET_BY_FACTORY` (the two fault texts of `container_env`), `CONTAINER` (the three-key container environment of the settings tests) and `raising`, for the tests that read settings.
- `support/shipped_agents.py`: `SHIPPED_AGENTS` and `ShippedAgent`, the seven shipped agents' front matter values and the opening of their bodies.
- `support/source_search.py`: reads the modules under `src/factory` with `ast`: `modules`, `imports`, `string_literals`, `reads_os_environ`.
- `support/stage_run_support.py`: builders for whole stage runs: a story started on `main`, its branch, a Makefile and a run (`open_story`, `run_stage`, `stage_makefile`), and the work item at the head of the remote's branch (`pushed`, `pushed_state`), and `INSTANCE`, the instance name `"factory-1"` that every test module naming that instance imports from here; `INSIDE`, the path `"tests/test_a.py"`, and `NOTES`, the path `"notes.md"`, the two paths a stage test's agent writes; and `ENVIRONMENT`, the environment the stage-run tests pass. `tests/guards/test_shared_constants.py` fails on another top-level assignment of the instance name, and `tests/guards/test_shared_stage_constants.py` on another of `INSIDE` or `NOTES`. A test module imports them from here, not from `container_support.py`.
- `support/stall_support.py`: the helpers of the stall tests: a work item opened on its branch, a launch and a context (`open_work_item`, `launched_stage`, `launch_stage`, `started_stage`, `stall_context`), `SwitchingRuntime`, and the stories, paths and records they share (`STORY`, `BRANCH_BODY`, `CREATED`, `OUTSIDE`, `ELSEWHERE`, `COMMITTED_ELSEWHERE`, `WRITES`, `DIED`).
- `support/template_make_support.py`: runs of the template's Makefile in a copy of it, with a stand-in `uv` on the `PATH` (`MAKEFILE`, `makefile_lines`, `green_line`, `template_project`, `stand_in_uv`, `run_make`).
- `support/take_support.py`: the take's datasets and runs (`make_dataset`, `write_dataset`, `run_take`, `tree`) and constants: `AGENT_TEXT`, the text `"written by the agent\n"` that every stage test's agent writes, and `BROKEN_FRONT_MATTER`, a work item whose front matter cannot be read. `take_support.py` is the one module that assigns `AGENT_TEXT`: `tests/guards/test_shared_stage_constants.py` fails on a second top-level assignment of its value, under any name, and a test module imports it from here.
- `support/tick_support.py`: `handlers_of` and `Failing`, the tick's handler factory and a handler that records each event and raises the error it is given, `ValueError("boom")` by default.
- `support/time_limits.py`: `ROOMY_LIMIT` (ten seconds) and `ROOMY_BOUND_SECONDS`, the time limit and the bound on the elapsed time for a test whose child must act before the limit kills it.
- `support/tmp_path_support.py`: `reopen`, which gives the owner back every folder and file under a test's `tmp_path` so that pytest can remove it.
- `support/torn_record_support.py`: known-result records and the torn lines a kill during an append leaves behind (`KEY`, `result_record`, `line_of`, `torn_inside`).
- `support/undo_support.py`: a claimed stage start on a work item's branch (`start_stage`, `pipeline_text`), and `without_work_item` and `with_broken_work_item`, which make the work item absent or unreadable at the stage start.
- `support/vm_support.py`: the paths of `operator/vm/setup.sh` and `operator/vm/factory.service` (`SETUP`, `SERVICE`), the fifteen step names (`STEPS`), the script's text without its comment lines (`setup_code`) and cut into its steps (`step_texts`), a run of the script in a folder (`run_setup`), `entries` (the paths under a folder), and `in_order` and `lines_with`, which the three `operator/vm/setup.sh` text modules share. It also runs `operator/vm/job-start.sh` (the Cloud Run job's command, tested in `tests/vm/test_vm_job_start.py`) with stand-in executables in place of its tools: `JOB_START`, `JOB_STAND_INS` and `run_job_start`, which writes the stand-ins through `git_support.write_executable`.
- `support/watch_support.py`: the watcher's shared data: a claimed story, the due `F0002-todo`, its acceptance (`push_story_claim`, `open_acceptance`, `aged_claim`).
- `support/command_words_support.py`: `value_after`, the word that follows an option in a recorded command line.
- `support/container_extra_support.py`: the tests of the containers' extra environment: `WordsRuns` (a container-runs fake that records the words of each call), `write_bundle`, `env_words`, `volume`, `without_pairs`, and `sync_words`, `check_words` and `agent_words`, which build the words expected of a call.
- `support/opencode_provider_support.py`: `PROVIDER` and `CONFIGURATION`, a complete opencode provider file and the configuration it gives, `KEY_ENV` and `write_provider`.
- `support/operator_job_support.py`: the job script's tests: `JOB`, `IMPERSONATE`, `BARE` and `INSTANCE` (site values), `words` (the words of a recorded gcloud call), `WRAPPER` and `START` (the start wrapper's pattern and command) and `GCLOUD_STAND_IN`, the `gcloud` stand-in.
- `support/operator_skill_support.py`: the skill scripts' tests: `SKILL` and `SCRIPTS` (their folders), `Request` and `recorded_requests` (what the `curl` stand-in saw), `Operator` and `make_operator` (a machine with a site and answers), `make_bare_remote` and `pull`.
- `support/operator_support.py`: the site scripts' tests: `ROOT`, the paths of the loader, the command, the example and the hosting library, `INTERFACE_KEYS`, `operator_environment` and `run_script`, `run_site`, `run_library`, `run_hosting` and `load_site`.
- `support/power_support.py`: `CountingPower`, a power switch that counts its calls, and the tick outcomes the idle shutdown tells apart (`IDLE`, `WAITS`, `OTHER`, `STOPPED`, `IDLE_ERROR`).
- `support/scripted_tick_support.py`: `ScriptedTick`, a tick that follows a script on the manual clock, `installed`, `scripted`, `run_loop` and `run_main` with `MainRun`, runs of the loop and of `main` over it.
- `support/site_check_support.py`: `site check`'s tests: `Machine` (a machine in `tmp_path` with stand-ins), `Setup`, the site values (`NAMES`, `REPOSITORY`, `JOB`, `REF`, `IMPERSONATE` and others) and the readers `check_lines`, `line_of`, `gcloud_words` and `git_command`.
- `support/token_support.py`: the token tests: `ScriptedTokenSource`, `scripted`, `never_sleep`, `answer`, `http_error`, `unreadable_http_error`, `RecordingOpener` and the constants `ENDPOINT`, `HIDDEN` and `ISSUED`.
- `support/wiring_support.py`: `record_get_repo` (records the arguments of every `Github.get_repo` call; two wiring test modules import it), `every_tool`, `ENVIRONMENT` (the environment the handler and wiring tests pass) and the constants the wiring and preflight tests share. `tests/guards/test_shared_environments.py` fails on another top-level assignment of either `ENVIRONMENT` value, this one or `stage_run_support.py`'s.
- `support/zfs_support.py`: the stand-in `zfs` and its plan; `DATASET`, the dataset name `"tank/factory/vm"`, which every test that names it imports from here.
- `support/work_item_support.py`: `put_work_item`, `created_state` and `checkout_text`, for tests that put a work item on its branch.
- `support/write_path_support.py`: `stage_start` and `push_definition`, for the write-path service tests.

## Errors

`factory.shared.domain.errors.FactoryError` is the root of every error the factory raises on purpose. Later stories add their error types under it. `InjectedKill` (below) is deliberately not one.

`BoundaryError` (a `FactoryError`) is the root of the errors for an outside party that failed. `HostingServiceError(operation, detail)` is its first subtype: every implementation of the hosting-service interface raises it for every failing call, and its message is `hosting service <operation> failed: <detail>`. `operation` and `detail` are attributes.

`GitError(command, exit_status, output_tail)` is its second subtype, for the git wrapper. `command` is `git ` and the arguments (`git fetch --prune origin`); `exit_status` is `None` when git could not be started or hit its time limit; `output_tail` is the last 30 lines of the output, stdout and stderr merged (all of it when shorter). The message is `<command> failed (exit <status>): <tail>`, or `failed (no exit status)` when the status is `None`. `FetchFailed` is a `GitError` that `fetch` raises for every failure. `NothingToCommit` is a `GitError` that `commit` raises when nothing is staged.

`ProjectCommandError(command, detail)` is its third subtype, for the project commands: it is raised only when a command cannot be started (an invalid name, or an executable the operating system cannot start). The message is `project command <command> failed: <detail>`; `command` and `detail` are attributes. A red command is a result, not this error.

`AgentRuntimeError(detail)` is its fourth subtype, for the agent runtime. The message is `agent runtime failed: <detail>`; `detail` is an attribute. A run that dies, hits its `time_limit` or runs out of budget is a result, not this error (see *The agent runtime*).

`PowerOffError(detail)` is a further `BoundaryError` for the idle shutdown's power-off: the machine could not be asked, or refused. The message is `power off failed: <detail>` (see *The idle shutdown*, `pipeline.md`).

`SnapshotError(command, detail)` and `ContainerError(command, detail)` are further `BoundaryError`s beside `ProjectCommandError`, for the snapshots and the container runs: a command that failed, could not start or reached its time limit. The messages are `snapshot command <command> failed: <detail>` and `container command <command> failed: <detail>` (see *The stage environment*, `machine.md`).

`PushFailed(branch, outcome, reason="")` is a `FactoryError` for a push that did not reach the remote; `outcome` is the git wrapper's `PushOutcome` other than `"pushed"` (`rejected`, `unreachable`), and the message names the branch and the outcome, followed by `: <reason>` when git's reason is known (`push_reason` of `Git.last_push_output()`, see *The git wrapper*). The claim service raises it (see *The claim service*).

`CannotHandle(kind, reason)` is a `FactoryError` that a handler raises when it cannot do its work, so the dispatcher counts it as an error; `kind` is the event's kind, and the message is `cannot handle <kind>: <reason>`.

`WorkItemFormatError(fault, path=None)` is a `FactoryError` for a work item file that cannot be read (see *The data of a work item*).

`CostRecordFormatError(line, fault)` is a `FactoryError` for a cost record file that cannot be read or written; `line` is counted from 1 and the message is `line <line>: <fault>`.

## The models' configuration

Every Pydantic model under `src/factory` is frozen and refuses unknown keys (`frozen=True`, `extra="forbid"`). `tests/guards/test_model_configuration.py` checks that for all of them at once: it imports every module of the package and tests each model defined there, private ones included. A new model therefore needs no test of its own for an assignment or an unknown key. A test of a pattern, a `Literal`, a limit or a rule across fields is still the story's.

A model that reads a tool's own output declares `extra="ignore"`, so that a field the tool adds later does not break the factory. It joins the `EXCEPTIONS` list of that test by its dotted name. There are twelve: `_Usage`, `_Denial`, `_StructuredOutput` and `_Reply` in `factory.agents.adapters.claude_runtime`, and `_Event`, `_Part`, `_Tokens`, `_CacheTokens`, `_ToolState`, `_Span`, `_Error` and `_ErrorData` in `factory.agents.adapters.opencode_runtime`. The test also checks that each exception is a model that ignores unknown keys, so an exception that becomes closed must leave the list.

## Kill points

A test that must show the factory survives its own death arms a kill point. The seam is `factory.shared.domain.kill_points`; the recovery tests arm `BEFORE_PUSH` (`tests/pipeline/application/test_recovery_crash.py`, a kill before the crash commit's push) and `AFTER_PUSH` (`tests/pipeline/application/test_tick_stale_branch.py`, a discard killed after its push); `tests/hosting/domain/test_kill_points.py` covers all four points (below).

There are four points, the members of `KillPoint`:

| Point | Value | Reached by |
|---|---|---|
| `AGENT_RUN` | `agent-run` | the two agent runtimes: the fake after the run's writes, `claude -p` after the last call and its result |
| `BEFORE_PUSH` | `before-push` | the git wrapper, before a push |
| `AFTER_PUSH` | `after-push` | the git wrapper, after a push |
| `AFTER_POST` | `after-post` | the fake hosting service and the PyGithub client, after posting |

Each wrapper in the table calls `kill_points.reach(point)` at its point; no other code reaches one.

A new `KillPoints` is inert. In a test, use the `kill_points` fixture from `tests/conftest.py`, which returns a new `KillPoints()` for each test, and hand it to the wrapper under test:

```python
def test_push_dies_after_the_second_try(kill_points: KillPoints) -> None:
    kill_points.arm(KillPoint.BEFORE_PUSH, after=1)
    with pytest.raises(InjectedKill):
        ...  # code that reaches BEFORE_PUSH twice
    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 2
```

- `arm(point)` makes the next `reach(point)` raise `InjectedKill`. `arm(point, after=n)` lets `n` reaches pass first and raises on the next; `after` counts from the arming. A negative `after` raises `ValueError` and changes nothing.
- A point fires once and is then inert again. Arming an armed point replaces the earlier arming. Arming one point never changes another, armed or not.
- `reached(point)` counts every reach, the one that raises included, armed or not.
- Each `KillPoints` instance has its own state.
- `str(InjectedKill(point))` is `injected kill at <point value>`, and `.point` is the point that fired.

`InjectedKill` is a `BaseException`; see `docs/decisions.md`.

### The kill-point cases

`tests/hosting/domain/test_kill_points.py` proves recovery by injection. Each case drives a real work item through the real `Tick` against a real local bare remote, the fake hosting service and the fake agent runtime, kills it at the kill point, restarts with the same instance name and checks the result after three ticks. The cases are data, `KILL_POINT_CASES` in `factory.shared.domain.kill_point_cases` (a closed, frozen `KillPointCase`), so that other tests and the document check name the same ids.

| Id | What dies | Class | Charges a crash |
|---|---|---|---|
| `agent-run-tick` | the tick, at `AGENT_RUN` | crash | yes |
| `agent-run-dies` | the agent run; the tick lives | stall | no |
| `commit-push` | the tick, at `BEFORE_PUSH` (between the result commit and its push) | crash | yes |
| `post-record` | the tick, at `AFTER_POST` (between a post and its record) | crash | no |
| `tick-other` | the tick, at `AFTER_PUSH` (after the claim's push) | crash | yes |
| `container` | the container: `agent-run-tick` restarted on an empty disk | crash | yes |

A crash case has a kill point; a stall has none and never charges a crash. A crash is charged exactly when a stage was in flight at the kill: its stage-start commit was pushed and its result commit was not. That is why `post-record`, killed after the result was pushed, charges none.

The checks live in `tests/support/proof_support.py`, which no production module imports. `SCENARIOS` holds one script per id, `run_case(case, root)` plays it, and `violations(result, case, conditions)` names the conditions that do not hold, from `CRASH_CONDITIONS` (resumed at the first tick, the rerun's claim five seconds after the kill, no repeated post or step, no write of the interrupted run in any commit, stage-start commit kept, no discarded cost record, counters) or `STALL_CONDITIONS` (attempt charged, writes outside the write paths left out of the result commit (the take does not copy them; nothing is undone), state restored, writes inside kept, cost record kept). Two further tests pin the caps: two kills in one stage reach the crash cap of 2, and two died runs reach `attempts_cap` 2; each ends with exactly one post and no further request.

Run the cases with:

```bash
uv run pytest tests/hosting/domain/test_kill_points.py tests/shared/domain/test_kill_point_cases.py
```

The `world` fixture (`tests/conftest.py`) returns `build_world(tmp_path, template=remote_template)`, the world on a copy of that remote, for a test of your own (`build_world(root)` without a template makes its own remote); `start_story`, `run_ticks` and `restart` are the steps a scenario is made of. The time from kill to rerun is read on the `ManualClock`: a scenario advances it by `KILL_TO_RERUN` (5 seconds) between the kill and the restart; `rerun(world, empty_disk=False)` does both. The `work_item` fixture (`tests/conftest.py`) returns `start_story(world)`. `work_item_file(world, work_item)` is the work item's `.md` file on its remote branch; its `.costs.jsonl` sidecar beside it is not counted.

## Fault-injection paths

`tests/shared/domain/test_fault_paths.py` (paths 1 to 6) and `tests/shared/domain/test_fault_paths_7_to_13.py` (paths 7 to 13) walk v1's thirteen behaviour paths (a question, a rework, a cap, a close, a hand edit), each with one kill or one stall added at the step the path adds. A test runs the path against a real local bare remote, the fake hosting service and the fake agent runtime, with the cases and helpers of `tests/support/proof_support.py`. The paths are data, `FAULT_PATHS` in `factory.pipeline.domain.fault_paths` (a closed, frozen `FaultPath` with `number`, `title`, `case` and `test`), so that this guide and the document check name the same tests.

| Path | Title | Case | Test |
|---|---|---|---|
| 1 | intake asks: a behaviour without a criterion | `agent-run-tick` | `test_intake_question_tick_killed_during_intake_run_reruns_free_and_asks_once` |
| 2 | intake asks for an edge case | `commit-push` | `test_intake_edge_case_question_killed_between_commit_and_push_reruns_intake_and_posts_once` |
| 3 | the tester finds a criterion against the interface | `post-record` | `test_tester_question_killed_between_post_and_record_posts_once` |
| 4 | a review rework | `agent-run-dies` | `test_review_rework_after_reviewer_run_dies_charges_one_attempt_then_one_round` |
| 5 | a documenter finding | `tick-other` | `test_docs_finding_tick_killed_after_move_back_push_counts_round_once_and_next_stage_starts` |
| 6 | a smoke test finding | `agent-run-dies` | `test_smoke_test_finding_after_run_reaches_time_limit_charges_one_attempt_then_moves_back` |
| 7 | the round cap | `post-record` | `test_round_cap_question_killed_between_post_and_record_posts_once_and_waits` |
| 8 | the attempts cap and its retry | `agent-run-dies` | `test_attempts_cap_run_stalls_twice_asks_human_without_a_rerun_and_reruns_on_comment` |
| 9 | `reject` after a stage change by hand | `commit-push` | `test_reject_killed_before_push_reverts_once_and_leaves_main_clean` |
| 10 | two work items in progress | `tick-other` | `test_two_items_in_progress_tick_killed_after_claim_push_reruns_lower_id_and_other_waits` |
| 11 | a close at the approval | `tick-other` | `test_close_at_approval_tick_killed_after_close_recorded_reopens_once_and_asks_once` |
| 12 | a feature acceptance refused, or merged | `container` | `test_acceptance_container_lost_in_review_reruns_once_and_books_result` |
| 13 | a test change the human approves | `agent-run-tick` | `test_test_change_approved_tick_killed_during_tester_run_reruns_tests_without_round` |

The case names the kill point the path arms (see *The kill-point cases*); the path's own crash charge may differ from the case's. Path 5 arms `AFTER_PUSH` after the result's push, which charges no crash, although its case `tick-other` does. Paths 4 and 6 use `agent-run-dies`, whose stall is a scripted result and not an armed point. Path 9 walks `reject` with the kill between the correction's commit and its push (`BEFORE_PUSH`): the rerun reverts the hand-made stage change once, and `origin/main` and the checkout stay clean. Path 12 is one test run for both results, `refused` and `accepted`, and restarts on an empty disk. Path 1 has a second half: a smoke test without an `Expect:` line is caught by `check_story_form`, not by an agent.

No path is mapped to a removing item: the thirteen are behaviour paths, none of them a kill point, and v1.1 keeps every mechanism they exercise.

Four further paths that v1's run 1 walked are not rows:

- the restart during a stage: removed by the claim and the crash rules; walked by paths 1 and 13;
- the close while the stages work: recorded first, no test of its own;
- the discarded story started again: removed by the empty bill at start;
- the merge while the move-back question is open: no item names it.

A path that fails is a defect to fix under `src/`, never a test to bend. Run the paths with:

```bash
uv run pytest tests/shared/domain/test_fault_paths.py tests/shared/domain/test_fault_paths_7_to_13.py tests/pipeline/domain/test_fault_paths_table.py tests/pipeline/domain/test_fault_paths.py tests/pipeline/domain/test_fault_paths_all_rows.py
```

`rerun_seconds(result)` and `branch_state(world, work_item)` in `tests/support/proof_support.py` are the proof's helpers for the time from the kill to the rerun's claim and for a work item's state on its branch (`None` when there is no branch); the paths use them instead of reading git a second way.

## The demos

`demo/` holds the demos v1.1 ships, one folder per demo `demo/<name>/`, for different kinds of project. A demo has three parts:

- `README.md`: what the demo is.
- `project/`: the project as the factory would find it. It holds `factory/pipeline.yml` (the pipeline definition) and `factory/story-form.md` (the story form).
- `features/`: the features and stories the factory is given, as `features/<feature>/feature.md` and `features/<feature>/backlog/<story>.md`. They stand beside `project/` and not under `project/factory/features/`, because the demo is the input of a run and the stories are not part of the project yet.

`demo/README.md` is the index and names each demo as its folder in backticks, such as `` `todo/` ``, on a line of its own text.

`uv run python -m factory.entry.check_demos` (`--root <path>` names another root; the default is the current directory) prints `demos ok` and exits 0, or prints one finding per line, demos in name order, and exits 1. `check_demos(root)` returns the findings. It finds, in this order:

- no `demo/` folder: nothing; a `demo/` without `README.md`: `demo/README.md: missing`;
- for each folder of `demo/` (loose files and folders that start with `.` are skipped): an index that does not name it; a missing `README.md`, `project/` or `features/`; a missing or refused `project/factory/pipeline.yml` (`RuamelPipelineDefinitionReader` reads it, through `build_pipeline_definition_reader()` of `factory.entry.wiring`); a missing `project/factory/story-form.md`, after which no story is checked;
- each file under `features/`, in path order: any file that is not a `feature.md` directly in a feature folder or a `.md` file in its `backlog/` folder is a finding.

A demo's stories are backlog stories checked at the path they will have in the project, `factory/features/<feature>/backlog/<story>.md`, with the story check's own rules (see *The form check of a story*): `check_demos` calls `backlog_story_findings` and `finding_line` of `factory.entry.check_story`, the same code `factory-check-story` runs for a backlog story, so a demo story and a project story give the same findings. A finding is `demo/<name>/features/<rest>: <message>`, with `:<line>` before the message when it has a line. The story form is the demo's own.

`make check` runs the check through `tests/entry/test_demos.py`, which expects `main` to return 0 for this repository, so a demo that goes stale fails the build. The code knows no demo by name (see the decision log); a new demo is a new folder and a line in the index.
