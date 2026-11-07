# Project guide

This guide is for an agent or developer about to change `kumpel-factory`. Read this index first: it shows how the code is laid out, where a change belongs and which conventions the checks do not catch. Then read the page of each area your [story](glossary.md) touches. [`CLAUDE.md`](../../CLAUDE.md) holds the rules every change follows, and [`docs/project-guide/style.md`](style.md) says how the pages read.

A page is split by subject into a new file before it passes about 600 lines, and the new file is named in *The files*.

## The code's layout

The code under `src/factory/` has seven areas, plus `entry` and `contract`. An area is a subject that keeps its modules in three layers inside its own package, and [`tests/guards/test_areas.py`](../../tests/guards/test_areas.py) lists every area's modules in one table.

    factory.<area>.domain
    factory.<area>.application
    factory.<area>.adapters

- `shared` holds what every other area uses: errors, times, identifiers, paths, settings, the records contract, the document and duplicate checks, the kill points, the file ports, the clock, atomic files and processes.
- `hosting` holds git, the hosting service, pushes, the hand-over and the opening of pull requests.
- `work` holds the [work items](glossary.md), their [journal](glossary.md), the story form, answers, decisions, send-backs, the archive and the [feature](glossary.md) [acceptance](glossary.md).
- `agents` holds the agent runs: the two runtimes and the fake one, the agent files, prompts, [write paths](glossary.md), tool uses, provider limits and tokens.
- `watching` holds what shows the factory and what it costs: [cost records](glossary.md), bills, the machine measures, human waits, transcripts, the board, the watcher, the factory log and the health file.
- `pipeline` holds the [pipeline definition](glossary.md), the [stages](glossary.md), the checks, the [tick](glossary.md) and its handlers, [claims](glossary.md), [leases](glossary.md), [stops](glossary.md), [stalls](glossary.md), recovery and the boundaries.
- `machine` holds containers, images, the [stage environment](glossary.md), snapshots, disks, the preflight, the project's commands and the machine's power.

Each area names its page:

- The docstring of `src/factory/<area>/__init__.py` ends with the line `Guide: docs/project-guide/<area>.md`, and that of [`src/factory/entry/__init__.py`](../../src/factory/entry/__init__.py) names this index.
- [`tests/guards/test_area_guides.py`](../../tests/guards/test_area_guides.py) fails when a line is missing or names a file that does not exist.
- The modules' own docstrings carry no such line.

See also: *The files* for the page of each area, and *Shared test helpers* for the tests' layout.

## The files

Each page starts with a title and a sentence on what it covers.

A guard, [`tests/guards/test_project_guide_files.py`](../../tests/guards/test_project_guide_files.py), requires every page of the folder to be named in this section and every area to have its page. It reads a list item as a page entry when the item starts with a name in backticks and goes on to a sentence that ends in a full stop. A list item that is no page entry starts with a plain or an italic word. An item that starts with a name in backticks that is no page fails the guard.

Headings are free except these, which keep their names, because a check or a script finds them by name:

- The heading `## The files` in this index: the guard reads the pages named under it, so renaming it leaves every page unnamed.
- *Kill points* and *Fault-injection paths* in this index, *Install* and *Configuration* in [`docs/operator-guide/install.md`](../operator-guide/install.md), and *The stops* in [`docs/operator-guide/stops.md`](../operator-guide/stops.md): the document check (`make documents`) requires them.
- *The machine* and *The rebuild after a merge* in [`docs/operator-guide/machine.md`](../operator-guide/machine.md): [`operator/vm/setup.sh`](../../operator/vm/setup.sh) names them in its messages.

The folder holds these pages:

- `README.md` (this index): what holds for all code. Sections: *The code's layout*, *The files*, *Shared test helpers*, *Errors*, *The models' configuration*, *Kill points*, *Fault-injection paths*, *The demos* ([`factory.entry.check_demos`](../../src/factory/entry/check_demos.py)).
- `style.md`: how the documents read: the rules for all documents, and for the operator guide, the project guide and the README, each with its reader and an example. The documenter and the reviewer judge by it.
- `glossary.md`: the words the factory gives its own meaning, one entry each, sorted alphabetically.
- `shared.md`: the area `shared` (`src/factory/shared/`), as far as it starts processes and runs this repository's checks. It describes the one module that starts processes, [`factory.shared.adapters.process`](../../src/factory/shared/adapters/process.py). It also describes the commands behind `make duplicates` and `make documents`: [`factory.shared.domain.duplicates`](../../src/factory/shared/domain/duplicates.py), [`factory.shared.domain.documents`](../../src/factory/shared/domain/documents.py), [`factory.entry.check_duplicates`](../../src/factory/entry/check_duplicates.py), [`factory.entry.check_documents`](../../src/factory/entry/check_documents.py). The rest of the area is described where it is used. Identifiers, paths, sections and the records contract are in [`work.md`](work.md), the settings are in [`hosting.md`](hosting.md) and [`machine.md`](machine.md), and errors and kill points are in this index. Sections: *Starting a process*, *The duplicates report*, *The document check* (with *The name check* and *The settings check*), *Reference*. [`factory.shared.domain.settings.SETTINGS`](../../src/factory/shared/domain/settings.py) is the table of every setting `read_settings` reads.
- `hosting.md`: the area `hosting` (`src/factory/hosting/`), git and the hosting service. It describes the hosting-service interface with its PyGithub and fake implementations: [`factory.hosting.application.hosting`](../../src/factory/hosting/application/hosting.py), [`factory.hosting.adapters.pygithub_hosting`](../../src/factory/hosting/adapters/pygithub_hosting.py), [`factory.hosting.adapters.fake_hosting`](../../src/factory/hosting/adapters/fake_hosting.py), [`factory.hosting.domain.hosting`](../../src/factory/hosting/domain/hosting.py). It describes the git wrapper in [`factory.hosting.application.git`](../../src/factory/hosting/application/git.py), [`factory.hosting.adapters.git_cli`](../../src/factory/hosting/adapters/git_cli.py), [`factory.hosting.domain.git`](../../src/factory/hosting/domain/git.py). It also names `factory.shared.domain.settings`. Sections: *The hosting service*, *The git wrapper*, *Reference*.
- `work.md`: the area `work` (`src/factory/work/`), the identity, data, files, sections and form of a work item. It describes [`factory.shared.domain.identifiers`](../../src/factory/shared/domain/identifiers.py), [`factory.shared.domain.paths`](../../src/factory/shared/domain/paths.py), [`factory.work.domain.work_item`](../../src/factory/work/domain/work_item.py), [`factory.work.domain.journal`](../../src/factory/work/domain/journal.py), [`factory.shared.domain.sections`](../../src/factory/shared/domain/sections.py), [`factory.work.domain.story_form`](../../src/factory/work/domain/story_form.py), [`factory.work.adapters.work_item_markdown`](../../src/factory/work/adapters/work_item_markdown.py) and [`factory.entry.check_story`](../../src/factory/entry/check_story.py). It also names [`factory.work.application.acceptance`](../../src/factory/work/application/acceptance.py), [`factory.work.application.acceptance_reading`](../../src/factory/work/application/acceptance_reading.py), [`factory.shared.application.files`](../../src/factory/shared/application/files.py), [`factory.work.application.work_items`](../../src/factory/work/application/work_items.py), [`factory.work.domain.acceptance`](../../src/factory/work/domain/acceptance.py), [`factory.shared.domain.contract`](../../src/factory/shared/domain/contract.py), [`factory.shared.domain.times`](../../src/factory/shared/domain/times.py), [`factory.entry.contract`](../../src/factory/entry/contract.py). Sections: *Identity, order and places of work items*, *The data of a work item*, *Journal*, *Reading and writing a work item file*, *Sections of a Markdown body*, *The form check of a story*, *Reference*. Subsections other files refer to: *The records contract*, *The feature acceptance*.
- `agents.md`: the area `agents` (`src/factory/agents/`), the agent runtime, the agent files, the shipped agents, the template and the write paths. It describes the agent-runtime interface and its implementations: [`factory.agents.application.agent_runtime`](../../src/factory/agents/application/agent_runtime.py), [`factory.agents.adapters.claude_runtime`](../../src/factory/agents/adapters/claude_runtime.py), [`factory.agents.adapters.agent_launch`](../../src/factory/agents/adapters/agent_launch.py), [`factory.agents.domain.agent_runs`](../../src/factory/agents/domain/agent_runs.py). It describes the agent files reader, [`factory.agents.adapters.agent_files`](../../src/factory/agents/adapters/agent_files.py). It describes the files under `agents/` and the write paths: [`factory.agents.application.write_paths`](../../src/factory/agents/application/write_paths.py), [`factory.agents.domain.write_paths`](../../src/factory/agents/domain/write_paths.py). It also names [`factory.agents.adapters.fake_agent_runtime`](../../src/factory/agents/adapters/fake_agent_runtime.py), [`factory.agents.adapters.opencode_runtime`](../../src/factory/agents/adapters/opencode_runtime.py), [`factory.shared.adapters.validation_faults`](../../src/factory/shared/adapters/validation_faults.py), [`factory.agents.application.project_agents`](../../src/factory/agents/application/project_agents.py), [`factory.agents.domain.provider_limits`](../../src/factory/agents/domain/provider_limits.py). Sections: *The agent runtime*, *The agent definition reader*, *The shipped agents, settings and template*, *The write paths* and *Reference*. Subsections other files refer to: *The opencode runtime*, *The agent's home*.
- `watching.md`: the area `watching` (`src/factory/watching/`), what shows the factory and what it costs: the evaluation, the board, cost records, bills, the human's waits, transcripts and the machine's readings. It describes the evaluation and the watcher: [`factory.pipeline.domain.evaluation`](../../src/factory/pipeline/domain/evaluation.py), [`factory.watching.application.watcher`](../../src/factory/watching/application/watcher.py) and [`factory.work.domain.move_rule`](../../src/factory/work/domain/move_rule.py). It describes the command `factory-watch` in [`factory.entry.watch`](../../src/factory/entry/watch.py). It describes the board: [`factory.watching.domain.board`](../../src/factory/watching/domain/board.py) and [`factory.watching.application.board`](../../src/factory/watching/application/board.py). It describes the cost records: [`factory.watching.domain.cost_records`](../../src/factory/watching/domain/cost_records.py), [`factory.watching.adapters.cost_records_jsonl`](../../src/factory/watching/adapters/cost_records_jsonl.py) and [`factory.watching.application.costs`](../../src/factory/watching/application/costs.py). It describes the bills: [`factory.watching.domain.bills`](../../src/factory/watching/domain/bills.py) and [`factory.watching.domain.human_waits`](../../src/factory/watching/domain/human_waits.py). It describes the command `factory-bill` in [`factory.entry.bill`](../../src/factory/entry/bill.py). It describes the transcripts in [`factory.watching.application.transcripts`](../../src/factory/watching/application/transcripts.py). It describes the machine readings: [`factory.watching.domain.machine`](../../src/factory/watching/domain/machine.py) and [`factory.watching.application.machine`](../../src/factory/watching/application/machine.py). It also names their adapters: [`factory.watching.adapters.transcript_files`](../../src/factory/watching/adapters/transcript_files.py), [`factory.watching.adapters.machine_files`](../../src/factory/watching/adapters/machine_files.py), [`factory.watching.adapters.factory_log`](../../src/factory/watching/adapters/factory_log.py), [`factory.watching.adapters.health_file`](../../src/factory/watching/adapters/health_file.py) and [`factory.watching.adapters.record_log_jsonl`](../../src/factory/watching/adapters/record_log_jsonl.py). Sections: *The evaluation*, *Cost records*, *Bills*, *The factory log and the health file*, *No code reads data from the journal's text*, *Reference*. Subsections other files refer to: *The move rule*, *The board*, *Cost records* (*When a record is created, completed and committed*, *Transcripts and the machine's readings*), *The bill command*, *The watcher's command line*.
- `machine.md`: the area `machine` (`src/factory/machine/`), the environment a stage runs in, behind interfaces: the stage environment itself and the [dataset](glossary.md) and containers under it, and the [project commands](glossary.md). It describes [`factory.machine.application.stage_environment`](../../src/factory/machine/application/stage_environment.py), [`factory.machine.application.snapshots`](../../src/factory/machine/application/snapshots.py), [`factory.machine.application.containers`](../../src/factory/machine/application/containers.py), [`factory.pipeline.application.take`](../../src/factory/pipeline/application/take.py), [`factory.machine.domain.containers`](../../src/factory/machine/domain/containers.py), [`factory.machine.adapters.zfs_snapshots`](../../src/factory/machine/adapters/zfs_snapshots.py), [`factory.machine.adapters.podman_runs`](../../src/factory/machine/adapters/podman_runs.py), [`factory.shared.adapters.printed_output`](../../src/factory/shared/adapters/printed_output.py), [`factory.machine.adapters.fake_snapshots`](../../src/factory/machine/adapters/fake_snapshots.py) and [`factory.machine.adapters.fake_containers`](../../src/factory/machine/adapters/fake_containers.py), and the project-commands interface and its make implementation ([`factory.machine.application.project_commands`](../../src/factory/machine/application/project_commands.py), [`factory.machine.adapters.make_commands`](../../src/factory/machine/adapters/make_commands.py)). It also names `factory.shared.domain.settings` and [`factory.entry.wiring`](../../src/factory/entry/wiring.py) for the stage environment's settings and wiring, and `factory.watching.adapters.record_log_jsonl`, [`factory.machine.application.disk_records`](../../src/factory/machine/application/disk_records.py), [`factory.pipeline.application.known_results`](../../src/factory/pipeline/application/known_results.py), [`factory.machine.application.preflight`](../../src/factory/machine/application/preflight.py), [`factory.pipeline.domain.checks`](../../src/factory/pipeline/domain/checks.py), [`factory.machine.domain.command_records`](../../src/factory/machine/domain/command_records.py), [`factory.machine.domain.disk`](../../src/factory/machine/domain/disk.py), [`factory.pipeline.domain.known_results`](../../src/factory/pipeline/domain/known_results.py), [`factory.entry.inputs`](../../src/factory/entry/inputs.py). Sections: *The cycle*, *The snapshots*, *The container runs*, *The copy snapshots*, *The fakes*, *The ZFS adapter*, *The podman adapter*, *The stage environment*, *The container environment*, *The sync command*, *The agent's container*, *The take*, *The checks*, *The settings and the wiring*, *The project's stage image*, *The preflight*, *Project commands*, *Known results*, *Mutation testing* (`make mutants`, the sweep form), and a *Reference* with the exact commands, faults and settings.
- `pipeline.md`: the area `pipeline` (`src/factory/pipeline/`), the pipeline definition, a stage from the claim to the result commit, the [take](glossary.md)'s rule, the tick, its handlers, the stops and the boundaries. It describes [`factory.pipeline.application.claims`](../../src/factory/pipeline/application/claims.py), [`factory.pipeline.domain.lease`](../../src/factory/pipeline/domain/lease.py), [`factory.pipeline.domain.pipeline_definition`](../../src/factory/pipeline/domain/pipeline_definition.py), [`factory.pipeline.application.pipeline_loading`](../../src/factory/pipeline/application/pipeline_loading.py), [`factory.pipeline.application.task`](../../src/factory/pipeline/application/task.py), [`factory.agents.domain.prompts`](../../src/factory/agents/domain/prompts.py), [`factory.hosting.application.opening`](../../src/factory/hosting/application/opening.py), [`factory.pipeline.application.stage`](../../src/factory/pipeline/application/stage.py), [`factory.pipeline.application.stalls`](../../src/factory/pipeline/application/stalls.py), the rule in `factory.pipeline.application.take`, [`factory.pipeline.application.tick`](../../src/factory/pipeline/application/tick.py), [`factory.pipeline.application.handlers`](../../src/factory/pipeline/application/handlers/__init__.py), [`factory.pipeline.application.recovery`](../../src/factory/pipeline/application/recovery.py), [`factory.pipeline.domain.stops`](../../src/factory/pipeline/domain/stops.py), [`factory.pipeline.application.stops`](../../src/factory/pipeline/application/stops.py), [`factory.pipeline.application.boundaries`](../../src/factory/pipeline/application/boundaries.py) and `factory-run`, `factory-health`. It also names [`factory.pipeline.adapters.pipeline_yaml`](../../src/factory/pipeline/adapters/pipeline_yaml.py), [`factory.agents.application.provider_limits`](../../src/factory/agents/application/provider_limits.py), [`factory.work.domain.decisions`](../../src/factory/work/domain/decisions.py), [`factory.shared.domain.errors`](../../src/factory/shared/domain/errors.py), [`factory.work.domain.labels`](../../src/factory/work/domain/labels.py), [`factory.hosting.domain.post_texts`](../../src/factory/hosting/domain/post_texts.py), [`factory.shared.adapters.atomic_file`](../../src/factory/shared/adapters/atomic_file.py), [`factory.shared.adapters.clock`](../../src/factory/shared/adapters/clock.py), [`factory.machine.adapters.disk_space`](../../src/factory/machine/adapters/disk_space.py), `factory.watching.adapters.factory_log`, `factory.watching.adapters.health_file`, [`factory.machine.adapters.preflight_stamp_file`](../../src/factory/machine/adapters/preflight_stamp_file.py), `factory.watching.application.board`, [`factory.pipeline.application.dispatcher`](../../src/factory/pipeline/application/dispatcher.py), [`factory.machine.adapters.power_off`](../../src/factory/machine/adapters/power_off.py), [`factory.pipeline.application.idle_shutdown`](../../src/factory/pipeline/application/idle_shutdown.py), `factory.watching.application.machine`, [`factory.pipeline.application.scheduler`](../../src/factory/pipeline/application/scheduler.py), the modules of `factory.pipeline.application.handlers` (`closed`, `comments`, `hand_over`, `lookups`, `merged`, `questions`, `recording`, `reject`, `run`, `run_gate`), [`factory.work.domain.answers`](../../src/factory/work/domain/answers.py), [`factory.work.domain.archive`](../../src/factory/work/domain/archive.py), `factory.watching.domain.board`, [`factory.pipeline.domain.events`](../../src/factory/pipeline/domain/events.py), [`factory.hosting.domain.hand_over`](../../src/factory/hosting/domain/hand_over.py), [`factory.machine.domain.preflight`](../../src/factory/machine/domain/preflight.py), [`factory.pipeline.domain.recovery`](../../src/factory/pipeline/domain/recovery.py), [`factory.work.domain.send_back`](../../src/factory/work/domain/send_back.py), [`factory.pipeline.domain.stop_table`](../../src/factory/pipeline/domain/stop_table.py), [`factory.pipeline.domain.tick_status`](../../src/factory/pipeline/domain/tick_status.py), [`factory.entry.health`](../../src/factory/entry/health.py), [`factory.entry.run`](../../src/factory/entry/run.py), `factory.entry.wiring`. Sections: *The claim service*, *The pipeline definition*, *The prompt and the request for a stage*, *Opening a work item*, *Starting a stage*, *Stalls*, *After the agent run*, *The decision rules*, *The stage protocol*, *The take's rule*, *The tick*, *The handlers of the events*, *The stop records* (with *The clock, the log and the stores*), *Boundaries*, *The idle shutdown*. Sections other files refer to: *Boundaries* and *The idle shutdown*.
- `operator.md`: the operator's scripts under `operator/` and their tests. It describes the site file and its loader: [`operator/lib/site.sh`](../../operator/lib/site.sh) and [`operator/bin/site`](../../operator/bin/site). It describes the hosting client, [`operator/lib/hosting.sh`](../../operator/lib/hosting.sh), and the script [`operator/job/job.sh`](../../operator/job/job.sh). It describes the sanitiser, [`operator/bin/sanitise`](../../operator/bin/sanitise), and the skill's scripts in `operator/skill/kumpel/scripts/`. Sections: *The layout*, *The site file and its loader*, *The hosting client*, *`job.sh`*, *The sanitiser*, *The skill's scripts*, *Tests of the scripts*, *Reference*.

See also: [glossary.md](glossary.md), [style.md](style.md), [shared.md](shared.md), [hosting.md](hosting.md), [work.md](work.md), [agents.md](agents.md), [watching.md](watching.md), [machine.md](machine.md), [pipeline.md](pipeline.md) and [operator.md](operator.md).

## Shared test helpers

The tests share their helpers through one folder, so that no test module imports another and no helper exists twice. Look here before you write a helper.

The root of `tests/` holds `conftest.py` and folders, each a package:

- `tests/support/`: the shared helpers, imported as `support.<name>` (`from support.bill_support import completed_records`). `tests/` is on `sys.path` (pytest's rootdir import; mypy names the files the same way), so no relative import is needed.
- `tests/guards/`: the structural guards: searches over the source (`tests/guards/test_*_search.py`), `tests/guards/test_*_removed.py`, `tests/guards/test_shared_*.py`, `tests/guards/test_no_*.py`, `tests/guards/test_suite_*.py`, `tests/guards/test_layers.py`, `tests/guards/test_areas.py`, `tests/guards/test_test_names.py`, `tests/guards/test_model_configuration.py`, the umask guard, the layout guard `tests/guards/test_tests_layout.py`, and the tests of the helpers themselves.
- `tests/operator_scripts/`: the tests of the operator's scripts under `operator/`. The folder is not named `operator`, because a package of that name would hide the standard library's module.
- `tests/vm/`: the tests of the files under `operator/vm/` (`test_vm_*.py`, `test_stage_image*.py`).
- `tests/agent_files/`: the tests of the files under `agents/` and `operator/template/`.
- `tests/<area>/<layer>/` and `tests/entry/`: the tests of the modules of `factory.<area>.<layer>` and of `factory.entry`, mirroring `src/factory`. A test module that imports no `factory` module but a helper or a source text sits in `tests/guards/`.

[`tests/guards/test_tests_layout.py`](../../tests/guards/test_tests_layout.py) fails when the root holds anything but `conftest.py` and packages, when a helper exists outside `tests/support/`, when a module imports a helper by its bare name, and when a test module sits outside the folder of its name's pattern.

A guard that a module stays removed names the module at the path it had and checks it with `module_exists_anywhere` of [`tests/support/module_names.py`](../../tests/support/module_names.py). The module is then found in no area either. [`tests/guards/test_removal_guards_search.py`](../../tests/guards/test_removal_guards_search.py) fails when a test module with an old layer path calls `module_exists`.

A helper that more than one test module uses lives in `tests/support/`, and a shared fixture lives in [`tests/conftest.py`](../../tests/conftest.py). A test module imports it from there. `CLAUDE.md`'s standing leave to move a shared test helper intends this. Before writing a helper, look here: the reviewer counts a copy as a finding. The guards `tests/guards/test_shared_*.py` fail on a copy of a shared helper. `tests/guards/test_shared_bodies.py` finds a copy of `log_lines`, `pushed`, `pushed_state`, `remote_document` and `push_state` by its body under any name. A story that adds such a module names it in this list through its docs criterion. A story that adds a fixture to either conftest names it in that conftest's line through its docs criterion.

No module under `tests/` imports a test module (a module whose file name begins with `test_`), in any form: `from x.test_y import ...`, `import x.test_y`, `from x import test_y`. Such an import runs the other module's setup at import and makes a removed or renamed test module fail tests of something else. What two test modules share lives in a support module, a new one named `*_support.py`, or, for a fixture, in `tests/conftest.py`. The guard [`tests/guards/test_shared_imports.py`](../../tests/guards/test_shared_imports.py) reads every `*.py` file under `tests/` with `ast` and fails with one line `<file>:<line>: <module>` for each such import. Modules that exist under other names (`tests/support/human_clone.py`, `tests/support/recording_log.py` and the rest below) keep them.

Support modules hold what test modules share, so that none imports another. They are:

- [`tests/support/agent_definition_support.py`](../../tests/support/agent_definition_support.py): `COMPLETED`, the completed agent run of the agent-definition tests.
- [`tests/support/agent_login_support.py`](../../tests/support/agent_login_support.py): `API_LOGIN` and `SUBSCRIPTION`, the two stand-in logins, and `_utf_16`, which writes a file in UTF-16.
- [`tests/support/before_approval_support.py`](../../tests/support/before_approval_support.py): `ROLES`, `FIXTURE` and `without_approval`, the definitions of the tests of `is_before_approval`.
- [`tests/support/check_documents_support.py`](../../tests/support/check_documents_support.py): `MISSING_LINES` is the document check's output for a missing guide file. The output filters are `without_report_lines`, `findings_from` and `line_of`. `append_block` adds a block to a document, and `write_checked_list` writes the list of checked documents and commits only a change.
- [`tests/support/claude_reply_support.py`](../../tests/support/claude_reply_support.py): `LOGIN` and `BUDGET_STOP`, the stand-in login and the reply of a run stopped by its budget.
- [`tests/support/claude_resume_support.py`](../../tests/support/claude_resume_support.py): the resume tests' helpers. The reply builders are `_reply` and `_budget_reply`, and the request and the runtime are `_request` and `_runtime`. `_after` gives the argument after a flag. The module also holds `LIMIT`.
- [`tests/support/contract_login_support.py`](../../tests/support/contract_login_support.py): `committed` parses the committed schema file of a name. `values` gives the values a schema allows. Its schema folder is `SCHEMAS` of `tests/support/contract_support.py`, assigned nowhere else.
- [`tests/support/cost_image_support.py`](../../tests/support/cost_image_support.py): the cost tests' launch and settings with an image (`_launch`, `_settings`, `MAKEFILE`).
- [`tests/support/cost_records_support.py`](../../tests/support/cost_records_support.py): cost record texts and builders (`COMPLETED_LINE`, `STARTED_LINE`, `REQUIRED`, `STARTED_AT`, `STARTED_AT_TEXT`, `_completed`, `_started`).
- [`tests/support/git_interface_support.py`](../../tests/support/git_interface_support.py), [`tests/support/hosting_interface_support.py`](../../tests/support/hosting_interface_support.py): `OPERATIONS`, the operations the git and hosting interfaces name.
- [`tests/support/known_results_support.py`](../../tests/support/known_results_support.py): the known-results rig (`Rig`, `_rig`, `_answering`, `_result`, `DEFINITION_YAML`, `TIME_LIMIT`).
- [`tests/support/opencode_events_support.py`](../../tests/support/opencode_events_support.py), [`tests/support/opencode_resume_support.py`](../../tests/support/opencode_resume_support.py): `WAIT_SECONDS`, how long the opencode stand-ins wait; [`tests/guards/test_time_limits.py`](../../tests/guards/test_time_limits.py) reads them here.
- [`tests/support/probe_login_support.py`](../../tests/support/probe_login_support.py): `LOGIN_FILE` and `HINT` of the login probe tests.
- [`tests/support/sections_support.py`](../../tests/support/sections_support.py): `TICKS`, three backticks, for fenced text in section tests.
- [`tests/support/two_routes_support.py`](../../tests/support/two_routes_support.py): `TWO_ROUTES`, a pipeline definition of two routes to two [approval](glossary.md) stages, in the shipped order.
- [`tests/support/stage_image_support.py`](../../tests/support/stage_image_support.py): what the project image tests share. `BASE_IDENTITY` is the base image's identity, `"sha256-base"`. `FIRST` and `SECOND` are two stage files that satisfy the rule. `StageSeen` is what one tick ran with: image, identity, `PATH` and builds asked for. `built_path` is the project image's `PATH` after a given build.
- [`tests/support/story_form_support.py`](../../tests/support/story_form_support.py): `FORM`, `SMOKE` and `_state`, a story form's text and a state at a stage.

The two conftests are below. After them come the modules of `tests/support/` (imported as `support.<name>`) that no earlier list holds; the page names every module of `tests/support/` and every fixture of `tests/conftest.py`.

- `tests/conftest.py`: the fixtures of the whole suite, by group.
  - Every test (autouse):
    - `without_agent_login` removes the agent's login variables from the environment, so no child process sees them.
    - `reopened_tmp_path`: after a test that uses `tmp_path`, it gives its owner back every folder and file under it.
  - Doubles and time:
    - `kill_points` are inert kill points, and `agent_runtime` and `hosting` are the fakes, on those kill points.
    - `clock` is a manual clock at noon UTC on 2026-10-12.
    - `on_the_manual_clock` gives the boundaries that `run_instance` builds the test's clock and a log on it.
  - Git:
    - `remote_template` is session-wide and is one remote that each test's `remote` copies.
    - `remote` is a bare repository whose `main` holds a small factory layout and a `Makefile`. Its `sync` target succeeds and prints nothing (`@:`), because every stage on the fixture runs `make sync`.
    - `checkout` is a `GitCli` on a fresh clone of `remote`, and `human` is the human's own `HumanClone`.
  - Paths and settings:
    - `agent_home` is a path in `tmp_path`, and nothing is created.
    - `local_settings` are [instance](glossary.md) settings whose checkout, state and agent home lie in `tmp_path`.
    - `disk_settings` are settings whose checkout and state directory lie under `tmp_path`, and `disk_records` is the disk record log in `tmp_path`.
    - `instance_settings` are settings on `remote`, the idle shutdown at one minute, everything in `tmp_path`.
    - `probe_settings` are settings whose agents run as the user `agent`, the state in `tmp_path`.
    - `base_identity_settings` are the instance settings with `BASE_IDENTITY` as the image identity, and `base_image` is the base image those settings name.
    - `image_file` is an image identity file in `tmp_path` that holds `build-7`.
    - `environment` is a valid environment whose image identity file and agent home lie in `tmp_path`; `hosted_environment` is a valid environment with token and image identity files in `tmp_path`.
    - `run_environment` is the agent runs' environment: a path and a home in `tmp_path`.
    - `token` is a token file in `tmp_path`, readable by its owner alone.
  - Stand-in programs:
    - `versioned_podman` and `listing_zfs` are the stand-in `podman` and `zfs` of the container-extras tests.
    - `podman` is a stand-in `podman` in `tmp_path`, planned to exit 0 silently, and `runs` is a `PodmanRuns` over it, its dataset at a fixed host path.
    - `podman_recorder` replaces the podman adapter's `run_process` with a `Recorder`.
    - `sudo_stand_in` puts a `sudo` stand-in first on `PATH` that exits 0, and gives the file in which it records the words of each call.
    - `code` is the setup script's text without its comment lines.
    - `operator` is the operator's machine with a full site file (a token command, no `gh`) and no answers.
    - `secret_file` is the mounted client secret of the token refresher, `login_file` the login file it keeps fresh, and `environ` a complete environment of the refresher.
  - Processes and signals:
    - `holder_file` is a holder's pid file; a holder still running after the test is killed.
    - `restored_signals` puts back the handlers of `SIGTERM` and `SIGINT` that the test found.
  - The factory on those:
    - `boundaries` are the interfaces on the test's checkout, fakes and clock, as an instance has them. Its `FakeSnapshots` and `FakeContainerRuns` stand over `<tmp_path>/workspace` with an empty base, so stages run in `ContainerEnvironment`. The project commands stay `MakeProjectCommands` on the host checkout.
    - `installed` is the boundaries with the coder's agent file installed in the test's agent home, and `installed_agents` installs a valid agent file for every [role](glossary.md) of the remote's definition.
    - `definition` is the remote's parsed pipeline definition, with the acceptance stage `acceptance`.
    - `workspace` is the folder the fake container runs play `/work` as, with `checkout/` and `home/` made, and `fake` is fake container runs on it.
    - `dataset` is an empty dataset with an empty base, its fakes set in the boundaries.
    - `minimal` is the minimal documents of the document check under `tmp_path / "root"`.
    - `walk` is an `AcceptanceWalk` over a due todo feature with two archived stories.
    - `result_case` is a story opened at `tests`, ready to push its stage's result.
  - The recovery proof:
    - `world` is a world built under `tmp_path`, and `work_item` is a story started in that world.
    - `failed_after_claim` is that world after a first tick that claimed the work item and then met a hosting failure.
  - Runtime tests:
    - `layout` is a checkout with `src` and `other`, a home and a temporary root.
    - `records` are the stop records in the test's state directory.
    - `recorder` replaces the runtime's `run_process` with a `Recorder`.
- [`tests/pipeline/application/handlers/conftest.py`](../../tests/pipeline/application/handlers/conftest.py): the fixtures of the handlers' tests under `tests/pipeline/application/handlers/` only. `snapshot_of` builds a snapshot holding a given state; the snapshot is not on the remote. `state_with` builds a state at `doing` with one journal record and the pull request. `event_of` builds an event of a kind about a snapshot. `pull_request` is the number of an open draft pull request of the work item's branch. `work_item` is the snapshot of a work item the human pushed to its branch, fetched locally. It is a published work item of the handlers' tests, not the root's started story.
- [`tests/support/acceptance_support.py`](../../tests/support/acceptance_support.py): `report_of`, a feature's acceptance report whose journal holds given entries.
- [`tests/support/acceptance_walk.py`](../../tests/support/acceptance_walk.py): `AcceptanceWalk`, a walk of one feature's acceptances over real ticks with the human's acts between, and its constants.
- [`tests/support/bill_support.py`](../../tests/support/bill_support.py): `completed_records` and `sidecar_text`, completed cost records and the text of their sidecar.
- [`tests/support/branch_reading.py`](../../tests/support/branch_reading.py): the work item on a work item's branch and the factory's posts on its pull request (`remote_document`, `error_posts`, `push_state`).
- [`tests/support/run_layout_support.py`](../../tests/support/run_layout_support.py): the run layout and the request of the tests that run a stand-in agent (`build_layout`, `write_script`, `read_records`, `run_request`), and `run_end(runtime, layout)`, which runs a stand-in agent and gives `(detail, end_reason)`; the Claude and the opencode runtime tests share it.
- [`tests/support/container_support.py`](../../tests/support/container_support.py): the container environment's rig. `fake_dataset(root)` puts the fakes on `<root>/workspace` with an empty base `<root>/workspace-base`, and the `boundaries` fixture and the recovery world use it. `container_dataset` is the dataset of the `boundaries` fixture with its fakes, and it removes the base when `with_base` is false. The module also holds `push_main`, `sync_makefile`, `dataset_git`, `local_branches`, `timing_lines` and `WorkspaceRuntime`. `FIVE_MINUTES` is the time limit the container tests share. `TIMING_PREFIX` and `RESET_PREFIX` are log-line prefixes, and `RESET_PREFIX` is `"stage environment: reset"`, the line that the reset writes. [`tests/guards/test_suite_fixtures.py`](../../tests/guards/test_suite_fixtures.py) and [`tests/pipeline/application/test_stage_on_container_fakes.py`](../../tests/pipeline/application/test_stage_on_container_fakes.py) import it. The whole stage on that dataset: `whole_stage` has the agent write `INSIDE` and `NOTES`, which `tests/support/stage_run_support.py` holds. Its `project_commands` picks the stage's project commands, the host's by default. `assert_taken_and_pushed` checks that the pushed commit holds `INSIDE` and not `NOTES`, that the journal names `NOTES`, that the log holds one timing line, and that the checkout is clean.
- [`tests/support/contract_support.py`](../../tests/support/contract_support.py): `SCHEMAS` (the committed schema folder), the contract command's output lines and `MainRow`, a row of `main`'s cases, and `committed_is_generated(entry, version=None)`, which checks the committed schemas against the generated ones and, when given a `version`, that version's text.
- [`tests/support/crash_support.py`](../../tests/support/crash_support.py): a work item claimed by this instance, ready to [crash](glossary.md) (`claim`, `expired_claim`, `crash_event`, `handler`), for the crash-cap tests.
- [`tests/support/definition_support.py`](../../tests/support/definition_support.py): `pipeline_definition`, the test remote's pipeline definition read through the boundaries' reader, which the `definition` fixture returns too, for helpers that take no fixtures.
- [`tests/support/disk_support.py`](../../tests/support/disk_support.py): `FakeDiskSpace`, a fake of the disk-space interface that answers per path.
- [`tests/support/dockerfile_support.py`](../../tests/support/dockerfile_support.py): readers of a Dockerfile's text and the pins' forms, for the tests of [`operator/vm/Dockerfile`](../../operator/vm/Dockerfile) ([`tests/vm/test_stage_image.py`](../../tests/vm/test_stage_image.py), [`tests/guards/test_pins.py`](../../tests/guards/test_pins.py)). Its readers are `_instructions` and `_commands` for the instructions and commands, `_arg_defaults` for the `ARG` defaults, `_env` for the `ENV` values and the `FROM` references. `floating_references` finds what floats: a `FROM` without a digest, a package without a version, `latest`, a download piped into a shell. The patterns are `DIGEST` and `THREE_NUMBERS`.
- [`tests/support/document_texts.py`](../../tests/support/document_texts.py): builders for the four documents' texts, clean unless a test asks for a fault (`readme`, `operator_guide`, `project_guide`, `decision_log`, `clean_texts`, `write_documents`). They read the code's tables when called, so a test can extend one with `monkeypatch`.
- [`tests/support/minimal_documents_support.py`](../../tests/support/minimal_documents_support.py): `minimal_documents` (a git repository with the smallest documents the check accepts) and `add_and_commit`; the document check's tests run on them.
- [`tests/support/evaluation_support.py`](../../tests/support/evaluation_support.py): the shared inputs of the evaluation's tests (a pipeline definition, snapshots, lookups, claims).
- [`tests/support/function_support.py`](../../tests/support/function_support.py): `functions` gives the top-level functions of a source text, read with `ast`. `without_docstring` gives a body's statements, a leading docstring left aside.
- [`tests/support/git_support.py`](../../tests/support/git_support.py): helpers for tests against real git: isolated runs, the bare remote and its copies, stand-in executables, agent files (`run_git`, `make_remote`, `copy_remote`, `clone`, `commit_all`, `install_agents`). `REMOTE_FILES` holds a `Makefile` with the target `sync` (recipe `@:`); a test that pushes its own `Makefile` before a stage or a probe gives it the same target, or the stage's `prepare` fails.
- [`tests/support/human_clone.py`](../../tests/support/human_clone.py): `HumanClone`, a second clone of the test remote that acts as the human: starts stories, pushes, merges.
- [`tests/support/log_support.py`](../../tests/support/log_support.py): `log_lines`, the factory log a test's state directory holds.
- `tests/support/module_names.py`: asks whether a module of the factory still defines a name.
- [`tests/support/observing_runtime.py`](../../tests/support/observing_runtime.py): `ObservingRuntime`, an agent runtime that records what the remote and the hosting fake hold when a run starts.
- [`tests/support/podman_support.py`](../../tests/support/podman_support.py): the stand-in `podman` and its plan; `IMAGE`, the stage image name `"factory-stage:1"`, which every test that names it imports from here.
- [`tests/support/preflight_support.py`](../../tests/support/preflight_support.py): the preflight's rig. It holds `Rig`, its recording stand-ins `RecordingWhich` and `RecordingCommands`, and the constants the preflight tests share: `IMAGE`, `OTHER_IMAGE`, `MAKEFILE`, `TOOLS` and `ROLES`. The fixtures `rig` and `red_main` are not in `conftest.py`, because two other rigs carry that name; a test module binds them with `rig = preflight_support.rig`. `fail_once` and `failed_once` give the rig after one probe of a red main.
- [`tests/support/probe_support.py`](../../tests/support/probe_support.py): the agent environment, the completed run and the opencode texts (`opencode_died`, `opencode_sso_hint`) of the probe tests.
- [`tests/support/process_support.py`](../../tests/support/process_support.py): real child processes in tests (`python_argv`, `Recorder`, `is_gone`).
- [`tests/support/project_command_support.py`](../../tests/support/project_command_support.py): `raising`, the answers for a recording stand-in of the project commands.
- [`tests/support/proof_support.py`](../../tests/support/proof_support.py): the recovery proof, described under *Kill points* and *Fault-injection paths*.
- [`tests/support/recording_stand_in_support.py`](../../tests/support/recording_stand_in_support.py): `recording_stand_in` is a stand-in program that appends its arguments to a `calls` file beside it and prints a given text. `recorded_calls` gives the argument lists it recorded. Both serve the wiring tests.
- [`tests/support/record_support.py`](../../tests/support/record_support.py): `UnwritableRecordLog`, a record log that cannot be written.
- [`tests/support/recording_log.py`](../../tests/support/recording_log.py): `RecordingLog`, a factory log that keeps the lines written to it.
- [`tests/support/run_process_recorder.py`](../../tests/support/run_process_recorder.py): `Recorder`, a stand-in for the runtime's `run_process` that keeps each request.
- [`tests/support/root_support.py`](../../tests/support/root_support.py): `AS_ROOT`, the pytest mark that skips a test needing a folder that root could still write in.
- [`tests/support/agent_run_support.py`](../../tests/support/agent_run_support.py): the agent runs' completed result and request, and `RecordingRun` (a run function that records its request).
- [`tests/support/search_support.py`](../../tests/support/search_support.py): searches of the test modules under `tests`. `modules_matching` gives the modules that match a pattern. `modules_assigning` gives the sorted modules that assign a given value at top level. `top_level_copies` gives the names that a top-level assignment in a source text gives a value, plain or annotated. [`tests/guards/test_shared_constants.py`](../../tests/guards/test_shared_constants.py) and [`tests/guards/test_shared_stage_constants.py`](../../tests/guards/test_shared_stage_constants.py) call them; a later guard calls `modules_assigning` instead of walking the modules again.
- [`tests/support/settings_support.py`](../../tests/support/settings_support.py): for the tests that read settings. `BASE` is the environment with the two required settings, and `AGENT_HOME` is the absolute agent home that `BASE` and the tests' `InstanceSettings` give. `NOT_A_NAME` and `SET_BY_FACTORY` are the two fault texts of `container_env`. `CONTAINER` is the three-key container environment of the settings tests. `raising` completes the set.
- [`tests/support/shipped_agents.py`](../../tests/support/shipped_agents.py): `SHIPPED_AGENTS` and `ShippedAgent`, the seven shipped agents' front matter values and the opening of their bodies.
- [`tests/support/source_search.py`](../../tests/support/source_search.py): reads the modules under `src/factory` with `ast`: `modules`, `imports`, `string_literals`, `reads_os_environ`.
- [`tests/support/stage_run_support.py`](../../tests/support/stage_run_support.py): builders for whole stage runs. `open_story`, `run_stage` and `stage_makefile` make a story started on `main`, its branch, a Makefile and a run. `pushed` and `pushed_state` give the work item at the head of the remote's branch. `INSTANCE` is the instance name `"factory-1"` that every test module naming that instance imports from here. `INSIDE` is the path `"tests/test_a.py"` and `NOTES` is the path `"notes.md"`, the two paths a stage test's agent writes. `ENVIRONMENT` is the environment the stage-run tests pass. [`tests/guards/test_shared_constants.py`](../../tests/guards/test_shared_constants.py) fails on another top-level assignment of the instance name. [`tests/guards/test_shared_stage_constants.py`](../../tests/guards/test_shared_stage_constants.py) fails on another of `INSIDE` or `NOTES`. A test module imports them from here, not from `tests/support/container_support.py`.
- [`tests/support/stall_support.py`](../../tests/support/stall_support.py): the helpers of the stall tests. A work item opened on its branch, a launch and a context come from `open_work_item`, `launched_stage`, `launch_stage`, `started_stage` and `stall_context`. The module also holds `SwitchingRuntime`. The stories, paths and records the tests share are `STORY`, `BRANCH_BODY`, `CREATED`, `OUTSIDE`, `ELSEWHERE`, `COMMITTED_ELSEWHERE`, `WRITES` and `DIED`.
- [`tests/support/template_make_support.py`](../../tests/support/template_make_support.py): runs of the template's Makefile in a copy of it, with a stand-in `uv` on the `PATH` (`MAKEFILE`, `makefile_lines`, `green_line`, `template_project`, `stand_in_uv`, `run_make`).
- [`tests/support/take_support.py`](../../tests/support/take_support.py): the take's datasets and runs (`make_dataset`, `write_dataset`, `run_take`, `tree`). `AGENT_TEXT` is the text `"written by the agent\n"` that every stage test's agent writes. `BROKEN_FRONT_MATTER` is a work item whose front matter cannot be read. `tests/support/take_support.py` is the one module that assigns `AGENT_TEXT`. `tests/guards/test_shared_stage_constants.py` fails on a second top-level assignment of its value, under any name. A test module imports it from here.
- [`tests/support/tick_support.py`](../../tests/support/tick_support.py): `handlers_of` and `Failing`, the tick's handler factory and a handler that records each event and raises the error it is given, `ValueError("boom")` by default.
- [`tests/support/time_limits.py`](../../tests/support/time_limits.py): `ROOMY_LIMIT` (ten seconds) and `ROOMY_BOUND_SECONDS`, the time limit and the bound on the elapsed time for a test whose child must act before the limit kills it.
- [`tests/support/tmp_path_support.py`](../../tests/support/tmp_path_support.py): `reopen`, which gives the owner back every folder and file under a test's `tmp_path` so that pytest can remove it.
- [`tests/support/torn_record_support.py`](../../tests/support/torn_record_support.py): known-result records and the torn lines a kill during an append leaves behind (`KEY`, `result_record`, `line_of`, `torn_inside`).
- [`tests/support/undo_support.py`](../../tests/support/undo_support.py): a claimed stage start on a work item's branch (`start_stage`, `pipeline_text`), and `without_work_item` and `with_broken_work_item`, which make the work item absent or unreadable at the stage start.
- [`tests/support/vm_support.py`](../../tests/support/vm_support.py): the helpers for `operator/vm/setup.sh` and [`operator/vm/factory.service`](../../operator/vm/factory.service). `SETUP` and `SERVICE` are their paths, and `STEPS` holds the fifteen step names. `setup_code` is the script's text without its comment lines, and `step_texts` cuts it into its steps. `run_setup` runs the script in a folder, and `entries` gives the paths under a folder. `in_order` is imported by the `tests/vm/test_vm_setup_*.py` modules and by `tests/operator_scripts/test_operator_merge_reset.py`; `lines_with` by `tests/vm/test_vm_setup_idle_shutdown.py`, `tests/vm/test_vm_setup_text.py` and `tests/vm/test_vm_job_start_image.py`. The module also runs [`operator/vm/job-start.sh`](../../operator/vm/job-start.sh), the Cloud Run job's command, with stand-in executables in place of its tools. They are `JOB_START`, `JOB_STAND_INS` and `run_job_start`, which writes the stand-ins through `git_support.write_executable`. [`tests/vm/test_vm_job_start.py`](../../tests/vm/test_vm_job_start.py) tests that script.
- [`tests/support/watch_support.py`](../../tests/support/watch_support.py): the watcher's shared data: a claimed story, the due todo feature, its acceptance (`push_story_claim`, `open_acceptance`, `aged_claim`).
- [`tests/support/command_words_support.py`](../../tests/support/command_words_support.py): `value_after`, the word that follows an option in a recorded command line.
- [`tests/support/container_extra_support.py`](../../tests/support/container_extra_support.py): the tests of the containers' extra environment: `WordsRuns` (a container-runs fake that records the words of each call), `write_bundle`, `env_words`, `volume`, `without_pairs`, and `sync_words`, `check_words` and `agent_words`, which build the words expected of a call.
- [`tests/support/opencode_provider_support.py`](../../tests/support/opencode_provider_support.py): `PROVIDER` and `CONFIGURATION`, a complete opencode provider file and the configuration it gives, `KEY_ENV` and `write_provider`.
- [`tests/support/operator_job_support.py`](../../tests/support/operator_job_support.py): the job script's tests. `JOB`, `IMPERSONATE`, `BARE` and `INSTANCE` are site values. `words` gives the words of a recorded gcloud call. `WRAPPER` and `START` are the start wrapper's pattern and command. `GCLOUD_STAND_IN` is the `gcloud` stand-in.
- [`tests/support/operator_skill_support.py`](../../tests/support/operator_skill_support.py): the skill scripts' tests. `SKILL` and `SCRIPTS` are their folders. `Request` and `recorded_requests` hold what the `curl` stand-in saw. `Operator` and `make_operator` give a machine with a site and answers. The module also holds `make_bare_remote` and `pull`.
- [`tests/support/operator_support.py`](../../tests/support/operator_support.py): the site scripts' tests: `ROOT`, the paths of the loader, the command, the example and the hosting library, `INTERFACE_KEYS`, `operator_environment` and `run_script`, `run_site`, `run_library`, `run_hosting` and `load_site`.
- [`tests/support/power_support.py`](../../tests/support/power_support.py): `CountingPower`, a power switch that counts its calls, and the tick outcomes the idle shutdown tells apart (`IDLE`, `WAITS`, `OTHER`, `STOPPED`, `IDLE_ERROR`).
- [`tests/support/scripted_tick_support.py`](../../tests/support/scripted_tick_support.py): `ScriptedTick`, a tick that follows a script on the manual clock, `installed`, `scripted`, `run_loop` and `run_main` with `MainRun`, runs of the loop and of `main` over it.
- [`tests/support/site_check_support.py`](../../tests/support/site_check_support.py): `site check`'s tests. `Machine` is a machine in `tmp_path` with stand-ins. `Setup` and the site values `NAMES`, `REPOSITORY`, `JOB`, `REF`, `IMPERSONATE` and others are here too. The readers are `check_lines`, `line_of`, `gcloud_words` and `git_command`.
- [`tests/support/token_support.py`](../../tests/support/token_support.py): the token tests: `ScriptedTokenSource`, `scripted`, `never_sleep`, `answer`, `http_error`, `unreadable_http_error`, `RecordingOpener` and the constants `ENDPOINT`, `HIDDEN` and `ISSUED`.
- [`tests/support/claude_stand_in.py`](../../tests/support/claude_stand_in.py), [`tests/support/opencode_stand_in.py`](../../tests/support/opencode_stand_in.py): the stand-ins for `claude` and `opencode`, executables that record each call and play scripted steps (`write_stand_in` with `Step` and `read_calls`; `write_opencode` with the event builders such as `step_start` and `step_finish`). [`agents.md`](agents.md) describes them.
- [`tests/support/container_runtime_support.py`](../../tests/support/container_runtime_support.py): what the runtime tests in a container share: `make_workspace`, `container_environment`, `read_only`, `files_in`, `container_request`, `make_state` and `run_folders`.
- [`tests/support/guide_files_support.py`](../../tests/support/guide_files_support.py): `lines_outside_fences`, `index_problems` (a guide folder against its index) and `searched_files`, the files a guard searches for a name.
- [`tests/support/machine_readings_support.py`](../../tests/support/machine_readings_support.py): `FakeMachineReadings`, a fake of the machine-readings interface that is told what each reading answers, and `UNREAD`.
- [`tests/support/push_retry_support.py`](../../tests/support/push_retry_support.py): a push case, a story opened at `tests` and a remote whose hook refuses a number of pushes (`PushCase`, `open_push_case`, `result_push`, `record_push`, `RecordingGit`, `RETRY`); the `result_case` fixture uses it.
- [`tests/support/pygithub_stand_ins.py`](../../tests/support/pygithub_stand_ins.py): stand-ins for the PyGithub objects the hosting client uses, which record every call. [`hosting.md`](hosting.md) describes them.
- [`tests/support/remote_outage_support.py`](../../tests/support/remote_outage_support.py): `RemoteOutage`, a remote renamed away and back (`go_away`, `come_back`), `move_remote_away` and `fetch_failed`, which picks the fetch stops out of a list.
- [`tests/support/sized_images.py`](../../tests/support/sized_images.py): `SizedImages`, fake images that answer each image's size, with `sized_by_tag`, `BASE_BYTES` and `PROJECT_BYTES`, for the tests of the stage image's log lines.
- [`tests/support/tool_use_support.py`](../../tests/support/tool_use_support.py): transcript lines of tool calls (`Call`, `claude_lines`, `opencode_lines`, `transcript_of`), in Claude Code's session form and in opencode's stream form.
- [`tests/support/transcript_support.py`](../../tests/support/transcript_support.py): `sha256_of`, the hash of a file, for the transcript tests.
- [`tests/support/wiring_support.py`](../../tests/support/wiring_support.py): `record_get_repo` records the arguments of every `Github.get_repo` call, and two wiring test modules import it. `every_tool` is here too. `ENVIRONMENT` is the environment the handler and wiring tests pass. The constants the wiring and preflight tests share are here as well. [`tests/guards/test_shared_environments.py`](../../tests/guards/test_shared_environments.py) fails on another top-level assignment of either `ENVIRONMENT` value, this one or that of `tests/support/stage_run_support.py`.
- [`tests/support/zfs_support.py`](../../tests/support/zfs_support.py): the stand-in `zfs` and its plan; `DATASET`, the dataset name `"tank/factory/vm"`, which every test that names it imports from here.
- [`tests/support/work_item_support.py`](../../tests/support/work_item_support.py): `put_work_item`, `created_state` and `checkout_text`, for tests that put a work item on its branch.
- [`tests/support/write_path_support.py`](../../tests/support/write_path_support.py): `stage_start` and `push_definition`, for the write-path service tests.

See also: *Kill points* and *Fault-injection paths*, which use `tests/support/proof_support.py`, and [`CLAUDE.md`](../../CLAUDE.md), *Tests*, for the rules a test follows.

## Errors

Every error the factory raises on purpose derives from one root, so a caller can catch the factory's own errors and nothing else. [`factory.shared.domain.errors`](../../src/factory/shared/domain/errors.py) defines them all, and this section describes each class.

```text
FactoryError
├── BoundaryError
│   ├── HostingServiceError
│   ├── GitError
│   │   ├── FetchFailed
│   │   └── NothingToCommit
│   ├── ProjectCommandError
│   ├── SnapshotError
│   ├── PowerOffError
│   ├── ContainerError
│   ├── AgentRuntimeError
│   ├── TokenError
│   └── FixtureError
├── PushFailed
├── WorkItemFormatError
├── CostRecordFormatError
├── PipelineDefinitionInvalid
├── AgentDefinitionError
│   ├── AgentDefinitionMissing
│   └── AgentDefinitionInvalid
├── UnhandledEvent
├── CannotHandle
├── SettingsInvalid
└── MachineStopStood
```

- `FactoryError` is the root of every error the factory raises on purpose. `InjectedKill` (see *Kill points*) is deliberately not one.
- `BoundaryError` is the root of the errors for an outside party that failed.
- `HostingServiceError(operation, detail)` is a `BoundaryError`. Every implementation of the hosting-service interface raises it for every failing call, and its message is `hosting service <operation> failed: <detail>`. `operation` and `detail` are attributes.
- `GitError(command, exit_status, output_tail)` is a `BoundaryError` for the git wrapper. `command` is `git ` and the arguments (`git fetch --prune origin`).
- `GitError.exit_status` is `None` when git could not be started or hit its time limit. `output_tail` is the last 30 lines of the output, stdout and stderr merged (all of it when shorter).
- The message of a `GitError` is `<command> failed (exit <status>): <tail>`, or `failed (no exit status)` when the status is `None`.
- `FetchFailed` is a `GitError` that `fetch` raises for every failure. `NothingToCommit` is a `GitError` that `commit` raises when nothing is staged.
- `ProjectCommandError(command, detail)` is a `BoundaryError` for the project commands. It is raised only when a command cannot be started (an invalid name, or an executable the operating system cannot start). The message is `project command <command> failed: <detail>`; `command` and `detail` are attributes. A red command is a result, not this error.
- `AgentRuntimeError(detail)` is a `BoundaryError` for the agent runtime. The message is `agent runtime failed: <detail>`; `detail` is an attribute. A run that dies, hits its `time_limit` or runs out of budget is a result, not this error (see *The agent runtime*).
- `PowerOffError(detail)` is a `BoundaryError` for the idle shutdown's power-off: the machine could not be asked, or refused. The message is `power off failed: <detail>` (see *The idle shutdown*, [`pipeline.md`](pipeline.md)).
- `SnapshotError(command, detail)` and `ContainerError(command, detail)` are `BoundaryError`s for the snapshots and the container runs: a command that failed, could not start or reached its time limit. The messages are `snapshot command <command> failed: <detail>` and `container command <command> failed: <detail>` (see *The stage environment*, [`machine.md`](machine.md)).
- `TokenError(detail)` is a `BoundaryError`: a bearer token could not be requested or written. The message is `token request failed: <detail>` (see *The bearer token* in [`agents.md`](agents.md)).
- `FixtureError(detail)` is a `BoundaryError`: a fixture could not build the starting point of a document's examples. The message is `fixture could not be prepared: <detail>` (see *The examples* in [`shared.md`](shared.md)).
- `PushFailed(branch, outcome, reason="")` is a `FactoryError` for a push that did not reach the remote. `outcome` is the git wrapper's `PushOutcome` other than `"pushed"` (`rejected`, `unreachable`).
- The message of a `PushFailed` names the branch and the outcome, followed by `: <reason>` when git's reason is known (`push_reason` of `Git.last_push_output()`, see *The git wrapper*). The claim service raises it (see *The claim service*).
- `CannotHandle(kind, reason)` is a `FactoryError` that a handler raises when it cannot do its work, so the dispatcher counts it as an error. `kind` is the event's kind, and the message is `cannot handle <kind>: <reason>`.
- `UnhandledEvent(kind)` is a `FactoryError` for an event kind without a handler. The message is `no handler for event kind <kind>`.
- `WorkItemFormatError(fault, path=None)` is a `FactoryError` for a work item file that cannot be read (see *The data of a work item*).
- `CostRecordFormatError(line, fault)` is a `FactoryError` for a cost record file that cannot be read or written. `line` is counted from 1 and the message is `line <line>: <fault>`.
- `PipelineDefinitionInvalid(fault)` is a `FactoryError`: the pipeline definition cannot be read. `fault` joins every fault and is the whole message (see *The pipeline definition* in [`pipeline.md`](pipeline.md)).
- `AgentDefinitionError(name, fault)` is a `FactoryError`: the agent files cannot be read. `name` is the agent, or `""` for all of them. The message is `agent <name>: <fault>`, or the fault alone when `name` is empty.
- `AgentDefinitionMissing` is an `AgentDefinitionError` for an agent that is not installed. `AgentDefinitionInvalid(name, fault, key)` is one for an agent file that does not define an agent; `key` is the key at fault, `""` for the file (see *The agent definition reader* in [`agents.md`](agents.md)).
- `SettingsInvalid(variable, fault)` is a `FactoryError`: the instance's settings cannot be read. The message is `<variable>: <fault>`.
- `MachineStopStood` is a `FactoryError` for a job in which a machine stop stood long enough to end the factory's process.

See also: *The agent runtime* in [`agents.md`](agents.md), *The git wrapper* in [`hosting.md`](hosting.md), *The stage environment* in [`machine.md`](machine.md) and *The claim service* in [`pipeline.md`](pipeline.md).

## The models' configuration

Every Pydantic model under `src/factory` is frozen and refuses unknown keys, and one guard checks that for all of them at once.

```python
model_config = ConfigDict(frozen=True, extra="forbid")
```

- [`tests/guards/test_model_configuration.py`](../../tests/guards/test_model_configuration.py) imports every module of the package and tests each model defined there, private ones included.
- A new model needs no test of its own for an assignment or an unknown key. A test of a pattern, a `Literal`, a limit or a rule across fields is still the story's.
- A model that reads a tool's own output declares `extra="ignore"`, so that a field the tool adds later does not break the factory. It joins the `EXCEPTIONS` list of that test by its dotted name.
- `EXCEPTIONS` holds twelve models. `_Usage`, `_Denial`, `_StructuredOutput` and `_Reply` are in [`factory.agents.adapters.claude_runtime`](../../src/factory/agents/adapters/claude_runtime.py). `_Event`, `_Part`, `_Tokens`, `_CacheTokens`, `_ToolState`, `_Span`, `_Error` and `_ErrorData` are in [`factory.agents.adapters.opencode_runtime`](../../src/factory/agents/adapters/opencode_runtime.py).
- The test also checks that each exception is a model that ignores unknown keys, so an exception that becomes closed must leave the list.

See also: *Errors* for the errors a model's validation raises, and [`agents.md`](agents.md) for the two runtimes.

## Kill points

A test that must show the factory survives its own death arms a kill point. The seam is [`factory.shared.domain.kill_points`](../../src/factory/shared/domain/kill_points.py).

The recovery tests arm two of the points. [`tests/pipeline/application/test_recovery_crash.py`](../../tests/pipeline/application/test_recovery_crash.py) arms `BEFORE_PUSH`, a kill before the crash commit's push. [`tests/pipeline/application/test_tick_stale_branch.py`](../../tests/pipeline/application/test_tick_stale_branch.py) arms `AFTER_PUSH`, a discard killed after its push. [`tests/hosting/domain/test_kill_points.py`](../../tests/hosting/domain/test_kill_points.py) covers all four points (below).

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

`InjectedKill` is a `BaseException`; the reason is in [`docs/decisions.md`](../decisions.md).

### The kill-point cases

`tests/hosting/domain/test_kill_points.py` proves recovery by injection. Each case drives a real work item through the real `Tick`. The tick runs against a real local bare remote, the fake hosting service and the fake agent runtime. The case kills it at the kill point, restarts with the same instance name and checks the result after three ticks. The cases are data: `KILL_POINT_CASES` in [`factory.shared.domain.kill_point_cases`](../../src/factory/shared/domain/kill_point_cases.py), each a closed, frozen `KillPointCase`. Other tests and the document check name the same ids.

| Id | What dies | Class | Charges a crash |
|---|---|---|---|
| `agent-run-tick` | the tick, at `AGENT_RUN` | crash | yes |
| `agent-run-dies` | the agent run; the tick lives | stall | no |
| `commit-push` | the tick, at `BEFORE_PUSH` (between the result commit and its push) | crash | yes |
| `post-record` | the tick, at `AFTER_POST` (between a post and its record) | crash | no |
| `tick-other` | the tick, at `AFTER_PUSH` (after the claim's push) | crash | yes |
| `container` | the container: `agent-run-tick` restarted on an empty disk | crash | yes |

A crash case has a kill point; a stall has none and never charges a crash. A crash is charged exactly when a stage was in flight at the kill: its stage-start commit was pushed and its result commit was not. That is why `post-record`, killed after the result was pushed, charges none.

The checks live in `tests/support/proof_support.py`, which no production module imports. Its names and signatures for the cases are these:

```python
SCENARIOS: dict[str, Callable[[World], CaseResult]]
KILL_TO_RERUN: timedelta
def run_case(case: KillPointCase, root: Path) -> CaseResult: ...
def violations(result: CaseResult, case: KillPointCase, conditions: Sequence[str]) -> list[str]: ...
def build_world(root: Path, *, template: Path | None = None) -> World: ...
def start_story(world: World, title: str = "Example") -> WorkItemId: ...
def run_ticks(world: World, count: int = 1) -> None: ...
def restart(world: World, *, empty_disk: bool = False) -> World: ...
def rerun(world: World, *, empty_disk: bool = False) -> World: ...
def work_item_file(world: World, work_item: WorkItemId) -> str: ...
```

`SCENARIOS` holds one script per id, `run_case` plays it, and `violations` names the conditions that do not hold. The conditions come from `CRASH_CONDITIONS` or `STALL_CONDITIONS`.

`CRASH_CONDITIONS` are these: the run resumes at the first tick, and the rerun's claim comes five seconds after the kill. No post or step is repeated, and no commit holds a write of the interrupted run. The stage-start commit is kept, no cost record is discarded, and the counters are right.

`STALL_CONDITIONS` are these: an attempt is charged, and writes inside the write paths are kept. Writes outside the write paths are left out of the result commit, the state is restored, and the cost record is kept. The take does not copy a write outside the write paths, so nothing is undone.

Two further tests pin the caps. Two kills in one stage reach the crash cap of 2, and two died runs reach `attempts_cap` 2. Each ends with exactly one post and no further request.

Run the cases with the two tests of this section, [`tests/hosting/domain/test_kill_points.py`](../../tests/hosting/domain/test_kill_points.py) and [`tests/shared/domain/test_kill_point_cases.py`](../../tests/shared/domain/test_kill_point_cases.py):

```console
$ uv run pytest -q tests/hosting/domain/test_kill_points.py tests/shared/domain/test_kill_point_cases.py 2>&1 | tail -1
<name>[100%]
```

The `world` fixture (`tests/conftest.py`) returns `build_world(tmp_path, template=remote_template)`, the world on a copy of that remote, for a test of your own. `build_world(root)` without a template makes its own remote. `start_story`, `run_ticks` and `restart` are the steps a scenario is made of.

The time from kill to rerun is read on the `ManualClock`. A scenario advances it by `KILL_TO_RERUN`, which is 5 seconds, between the kill and the restart. `rerun(world, empty_disk=False)` does both.

The `work_item` fixture (`tests/conftest.py`) returns `start_story(world)`. `work_item_file(world, work_item)` is the work item's `.md` file on its remote branch, and its `.costs.jsonl` sidecar beside it is not counted.

See also: *Fault-injection paths*, which walk the same cases, and *Shared test helpers*, where `world` and `work_item` come from.

## Fault-injection paths

A fault-injection path is a behaviour path of the factory with one kill or one stall added at the step the path adds. There are thirteen: a question, a rework, a cap, a close and a hand edit among them.

[`tests/shared/domain/test_fault_paths.py`](../../tests/shared/domain/test_fault_paths.py) walks paths 1 to 6 and [`tests/shared/domain/test_fault_paths_7_to_13.py`](../../tests/shared/domain/test_fault_paths_7_to_13.py) walks paths 7 to 13. A test runs the path against a real local bare remote, the fake hosting service and the fake agent runtime, with the cases and helpers of `tests/support/proof_support.py`.

The paths are data, `FAULT_PATHS` in [`factory.pipeline.domain.fault_paths`](../../src/factory/pipeline/domain/fault_paths.py). This guide and the document check name the same tests. The names and signatures are these, the first two from that module and the last two from `tests/support/proof_support.py`:

```python
FAULT_PATHS: tuple[FaultPath, ...]
class FaultPath(BaseModel):  # closed and frozen
    number: int
    title: str
    case: str
    test: str
def rerun_seconds(result: CaseResult) -> float: ...
def branch_state(world: World, work_item: WorkItemId) -> WorkItemState | None: ...
```

| Path | Title | Case | Test |
|---|---|---|---|
| 1 | intake asks: a behaviour without a criterion | `agent-run-tick` | `test_intake_question_tick_killed_during_intake_run_reruns_free_and_asks_once` |
| 2 | intake asks for an edge case | `commit-push` | `test_intake_edge_case_question_killed_between_commit_and_push_reruns_intake_and_posts_once` |
| 3 | the tester finds a criterion against the interface | `post-record` | `test_tester_question_killed_between_post_and_record_posts_once` |
| 4 | a review rework | `agent-run-dies` | `test_review_rework_after_reviewer_run_dies_charges_one_attempt_then_one_round` |
| 5 | a documenter finding | `tick-other` | `test_docs_finding_tick_killed_after_move_back_push_counts_round_once_and_next_stage_starts` |
| 6 | a smoke test finding | `agent-run-dies` | `test_smoke_test_finding_after_run_reaches_time_limit_charges_one_attempt_then_moves_back` |
| 7 | the [round cap](glossary.md) | `post-record` | `test_round_cap_question_killed_between_post_and_record_posts_once_and_waits` |
| 8 | the [attempts cap](glossary.md) and its retry | `agent-run-dies` | `test_attempts_cap_run_stalls_twice_asks_human_without_a_rerun_and_reruns_on_comment` |
| 9 | `reject` after a stage change by hand | `commit-push` | `test_reject_killed_before_push_reverts_once_and_leaves_main_clean` |
| 10 | two work items in progress | `tick-other` | `test_two_items_in_progress_tick_killed_after_claim_push_reruns_lower_id_and_other_waits` |
| 11 | a close at the approval | `tick-other` | `test_close_at_approval_tick_killed_after_close_recorded_reopens_once_and_asks_once` |
| 12 | a feature acceptance refused, or merged | `container` | `test_acceptance_container_lost_in_review_reruns_once_and_books_result` |
| 13 | a test change the human approves | `agent-run-tick` | `test_test_change_approved_tick_killed_during_tester_run_reruns_tests_without_round` |

The case names the kill point the path arms (see *The kill-point cases*). The path's own crash charge may differ from the case's. Path 5 arms `AFTER_PUSH` after the result's push, which charges no crash, although its case `tick-other` does. Paths 4 and 6 use `agent-run-dies`, whose stall is a scripted result and not an armed point. Path 9 walks `reject` with the kill between the correction's commit and its push (`BEFORE_PUSH`). The rerun reverts the hand-made stage change once, and `origin/main` and the checkout stay clean. Path 12 is one test run for both results, `refused` and `accepted`, and restarts on an empty disk. Path 1 has a second half: a smoke test without an `Expect:` line is caught by `check_story_form`, not by an agent.

Four further paths are not rows:

- the restart during a stage: needs no row, because the claim and the crash rules cover it; paths 1 and 13 walk it;
- the close while the stages work: the factory records it first; it has no test of its own;
- the discarded story started again: needs no row, because its bill is empty at the start;
- the merge while the move-back question is open: no test names it.

A path that fails is a defect to fix under `src/`, never a test to bend. Run the paths with their five tests, the two files linked above, [`tests/pipeline/domain/test_fault_paths_table.py`](../../tests/pipeline/domain/test_fault_paths_table.py), [`tests/pipeline/domain/test_fault_paths.py`](../../tests/pipeline/domain/test_fault_paths.py) and [`tests/pipeline/domain/test_fault_paths_all_rows.py`](../../tests/pipeline/domain/test_fault_paths_all_rows.py):

```console
$ uv run pytest -q tests/shared/domain/test_fault_paths.py tests/shared/domain/test_fault_paths_7_to_13.py tests/pipeline/domain/test_fault_paths_table.py tests/pipeline/domain/test_fault_paths.py tests/pipeline/domain/test_fault_paths_all_rows.py 2>&1 | tail -1
<name>[100%]
```

`rerun_seconds` gives the time from the kill to the rerun's claim. `branch_state` gives a work item's state on its branch, or `None` when there is no branch. The paths use both instead of reading git a second way.

See also: *Kill points*, whose cases the paths use, and [`pipeline.md`](pipeline.md), *The stage protocol*.

## The demos

`demo/` holds the demos the repository ships, one folder per demo `demo/<name>/`, for different kinds of project. A demo has three parts:

- [`demo/todo-service/README.md`](../../demo/todo-service/README.md), as an example: what the demo is.
- `demo/<name>/project/`: the project as the factory would find it. It holds the pipeline definition, [`demo/todo-service/project/factory/pipeline.yml`](../../demo/todo-service/project/factory/pipeline.yml), and the story form, [`demo/todo-service/project/factory/story-form.md`](../../demo/todo-service/project/factory/story-form.md), here as the example's.
- `demo/<name>/features/`: the features and stories the factory is given, as `demo/<name>/features/<feature>/feature.md` and `demo/<name>/features/<feature>/backlog/<story>.md`. They stand beside `demo/<name>/project/` and not under `demo/<name>/project/factory/features/`, because the demo is the input of a run and the stories are not part of the project yet.

[`demo/README.md`](../../demo/README.md) is the index and names each demo as its folder in backticks, such as `` `todo-service/` ``, on a line of its own text.

The command `python -m factory.entry.check_demos` prints `demos ok` and exits 0, or prints one finding per line, demos in name order, and exits 1. `--root <path>` names another root; the default is the current directory.

```console
$ uv run python -m factory.entry.check_demos
...
demos ok
```

```python
def check_demos(root: Path) -> list[str]: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

`check_demos(root)` of [`factory.entry.check_demos`](../../src/factory/entry/check_demos.py) returns the findings. `main` is the command's entry. It finds, in this order:

- no `demo/` folder: nothing; a `demo/` without `README.md`: `demo/README.md: missing`;
- for each folder of `demo/` (loose files and folders that start with `.` are skipped): an index that does not name it; a missing `README.md`, `project/` or `features/`; a missing or refused `demo/<name>/project/factory/pipeline.yml`; a missing `demo/<name>/project/factory/story-form.md`, after which no story is checked;
- each file under `features/`, in path order: any file that is not a `feature.md` directly in a feature folder or a `.md` file in its `backlog/` folder is a finding.

`RuamelPipelineDefinitionReader` reads the pipeline definition, through `build_pipeline_definition_reader()` of `factory.entry.wiring`.

A demo's stories are [backlog](glossary.md) stories checked at the path they will have in the project, `factory/features/<feature>/backlog/<story>.md`. The story check's own rules apply (see *The form check of a story*). `check_demos` calls `backlog_story_findings` and `finding_line` of `factory.entry.check_story`, the same code `factory-check-story` runs for a backlog story. So a demo story and a project story give the same findings. A finding is `demo/<name>/features/<rest>: <message>`, with `:<line>` before the message when it has a line. The story form is the demo's own.

`make check` runs the check through [`tests/entry/test_demos.py`](../../tests/entry/test_demos.py), which expects `main` to return 0 for this repository, so a demo that goes stale fails the build. The code knows no demo by name (the reason is in `docs/decisions.md`); a new demo is a new folder and a line in the index.

See also: *The form check of a story* in [`work.md`](work.md) and *Boundaries* in [`pipeline.md`](pipeline.md).
