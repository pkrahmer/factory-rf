# Housekeeping

## Goal

Make v1.1 ready for its first real start and for the todo run, the baseline that v2 is measured against. After eleven features built one story at a time, step 1 of the human's plan (`planning/overnight/restructure-after-f0011.md`, "The order of the work after F0011", items 1.1 to 1.10) collects the small fixes that stand in the way: a `make check` that takes three minutes, copies of code that nobody owns, no mutation testing, nothing that measures the todo run (disk, project commands, model time), per-model tests that only test Pydantic, a round cap that cannot grant one more round, a compose file that collides with v1's, no frame for the shipped demos, a time limit that `sudo` defeats, a document check that nothing runs, and three of F0010's open points. It is for the human, who starts v1.1 on the real machine next, and for the agents of every later story, which run `make check` many times each. Done when every story below is merged, `make check` is green and faster than the 177 s `make test` of 2026-10-17, `make duplicates` reports against its baseline, `make mutants FEATURE=F0012` runs, and `python -m factory.entry.check_documents` prints `documents ok`.

## Scope

- 1.1 `make check` faster: pytest-xdist over all cores and `make secrets` over the changed files (the human's change before S0001), one prepared git remote copied per test (S0001).
- 1.2 `make duplicates`: the report against a baseline (S0002) and its target, baseline and record (the human's change before S0003); the findings known today fixed (S0003 to S0005), and the parked drafts F0003-S0011 and F0008-S0007 taken in (S0006, S0007).
- 1.3 `make mutants` with mutmut, limited to the modules one feature changed (the human's change before S0008), and the parked draft F0011-S0007 taken in (S0008).
- 1.4 What the todo run must measure: the low-disk machine stop (S0009, S0010), no temporary files left (S0011 and the human's change before S0001), the record of every project command with each target's time (S0012, S0013), the model's time of every agent run (S0014, S0015), and the disk record (S0016, S0017).
- 1.5 One test of the models' own configuration replacing the per-model tests that only test Pydantic (S0018 to S0020), and an answer at the round cap that grants more rounds (S0021).
- 1.6 One compose project per instance (S0022).
- 1.7 The `demo/` frame: the demo check and its test in `make check` (S0023), and the index README (the human's change after S0023).
- 1.8 The kill of an agent run under `sudo` at its time limit (S0024).
- 1.9 The document check as a check of the docs stage: `make documents` and the docs stage's `checks` (the human's change before S0003); the documents say so (S0003's docs criterion). No story of its own: nothing under a write path changes but the documents.
- 1.10 Three of F0010's open points: the agent cannot rewrite its agents and settings (S0025), a missing health file reads as not healthy (S0026), a standing `main_branch_failing` is cleared when `main` moves while the machine items fail (S0027).

## Out of scope

- Steps 2 to 8 of the plan: the todo demo's content, the first start on the real machine, the todo run, the handover, a project's own skills and agents, the restructure (the tree by domain, `tests/support/`, the project guide split by domain, `entry` renamed), the rename of the repositories.
- A project's own skills (`Skill` in the agents' tools) and a project's own agents (`factory/agents/<role>.md`): built by v1.1 itself, step 6.
- v1.1's own pipeline definition for this repository: it replaces `factory/stages.yml` at the handover (step 5), and only then gets `documents` as a check and `duplicates` as a report of its own.
- The token file's default only in the image's `ENV`, and the template's write paths: they stay as built (the human's answer of 2026-10-17).
- Host-side disk numbers (the free space of the host drive, the size of Docker's disk image, `docker system df`): the container cannot see them; the session records them by hand, as now.
- A generic tracing system and sampling of `docker stats` (the human's word, "Telemetry in v1.1").
- Folding an interface away where the duplicates report shows one with a single implementation: measured from the first report, not built here.

## Stories

The order is the story numbers. A later number may start first if it is the only one moved to `ongoing/`.

- S0001 — One prepared remote per test session
- S0002 — The duplicates report
- S0003 — One default identity, one way to find sudo, one way to read the arguments (takes in F0010-S0025)
- S0004 — One conversion to UTC for the models' times
- S0005 — The proof's test helpers, one copy each
- S0006 — The fault of an unreadable pipeline definition on one line (takes in F0003-S0011)
- S0007 — The no-state refusals of require_state's callers (takes in F0008-S0007)
- S0008 — The document check's v1 words and required sections, pinned in full, and `make mutants` described (takes in F0011-S0007)
- S0009 — The free space of a path, and its setting
- S0010 — The low-disk stop at every tick
- S0011 — The shipped agents leave no temporary files and read the test times
- S0012 — Each target's time in a check's result
- S0013 — A record of every project command
- S0014 — The model's time in an agent run's record
- S0015 — The model's minutes in the cost table
- S0016 — The disk record at an instance's start
- S0017 — The disk record told to the acceptance reviewer
- S0018 — One test of the models' configuration, and the per-model tests of adapters and application removed
- S0019 — The per-model configuration tests of the domain removed, part one
- S0020 — The per-model configuration tests of the domain removed, part two
- S0021 — An answer at the round cap starts the count of rounds over
- S0022 — One compose project per instance
- S0023 — The demo check
- S0024 — The kill of an agent run under sudo at its time limit
- S0025 — The agent cannot rewrite its agents and settings
- S0026 — A missing health file reads as not healthy
- S0027 — A standing main_branch_failing cleared when main moves

## The parked drafts and where they go

| Parked draft | Taken in by | How |
|---|---|---|
| `F0003-stops-and-pipeline-definition/drafts/F0003-S0011-unreadable-yaml-fault-on-one-line.md` | S0006 | whole, unchanged in substance; its five faults were checked against ruamel.yaml 0.19.1 on 2026-10-17 |
| `F0008-crash-recovery/drafts/F0008-S0007-the-no-state-refusals-of-require-states-callers.md` | S0007 | whole; its five messages were checked against today's code |
| `F0010-machine/drafts/F0010-S0025-one-default-git-identity.md` | S0003 | whole, as its first part |
| `F0011-proof-and-documents/drafts/F0011-S0007-document-check-word-list-and-sections-pinned.md` | S0008 | its criteria 1 to 3; its docs repair ("F0011, decision 13") moves to S0003's docs criterion, which rewrites that sentence for `make documents` |

The parked files stay where they are; the human deletes each when the story that takes it in is merged.

## The human's changes

Files outside every write path of v1's `factory/stages.yml` (checked on 2026-10-17: intake, reviewer and demo write only the story; tester also `tests/*`; coder also `src/*`, `image/*`, `template/*`, `claude/*`; documenter also `README.md`, `docs/*`). So `Makefile`, `pyproject.toml`, `uv.lock`, `.gitignore`, `CLAUDE.md`, `factory/stages.yml`, `security/*` and `demo/*` change only by these commits, which the session makes between two stories. `image/*` and `claude/*` are inside the coder's write paths, so S0022, S0024 and S0025 (`image/`) and S0011 and S0017 (`claude/agents/`) need no human change. Each change is followed by `make check` in v1's container before it is pushed; versions are pinned with `==` at what `uv add --dev` resolves that day.

### H1, before S0001: tests on every core, timed targets, secrets over the changed files, a JUnit report

Reason: 1.1 (`make test` is 88 % of `make check`, `secrets` 11 %), and 1.4 (each target's time, read by S0012; the time per test; no pytest leftovers in `/tmp`).

- `pyproject.toml`, `[dependency-groups] dev`: add `"pytest-xdist==<resolved>"`; `uv lock`.
- `pyproject.toml`, `[tool.pytest.ini_options]`: add `junit_family = "xunit1"` (so `record_property` reaches the report; F0011's acceptance) and `tmp_path_retention_policy = "failed"` (pytest keeps only the folders of failed tests).
- `.gitignore`: add `.reports/`.
- `Makefile`: after `.SILENT:` add

  ```make
  # One shell per recipe, stopped by its first failing line, so that a recipe can time itself.
  SHELL := /bin/bash
  .SHELLFLAGS := -eu -o pipefail -c
  .ONESHELL:

  # `$(start)` opens a recipe and `$(green)` ends it with "<target>: green (<seconds> s)",
  # the line the factory's records of project commands read.
  start = started=$$(date +%s%N)
  green = tenths=$$(( ($$(date +%s%N) - started) / 100000000 )); echo "$@: green ($$((tenths / 10)).$$((tenths % 10)) s)"
  ```

  and in each of `lint`, `types`, `layers`, `sast`, `secrets`, `licenses` and `test` put `$(start)` as the first recipe line and replace the closing `echo "<target>: green"` by `$(green)`. `check` keeps `echo "check: green"`.
- `Makefile`, `secrets` becomes:

  ```make
  # Secrets beyond the reviewed baseline, in the files changed against origin/main (committed,
  # staged, unstaged or new); every tracked file on main itself or without origin/main.
  secrets:
  	$(start)
  	if [ "$$(git rev-parse HEAD)" != "$$(git rev-parse --verify --quiet origin/main || true)" ] && base=$$(git merge-base HEAD origin/main 2>/dev/null); then
  	  files=$$( { git diff --name-only --diff-filter=d "$$base"; git ls-files --others --exclude-standard; } | sort -u)
  	else
  	  files=$$(git ls-files)
  	fi
  	files=$$(printf '%s\n' $$files | grep -vE '^(uv\.lock|\.secrets\.baseline|planning/.*|docs/runs/.*)$$' || true)
  	if [ -n "$$files" ]; then uv run detect-secrets-hook --baseline .secrets.baseline $$files; fi
  	$(green)
  ```
- `Makefile`, `test` becomes:

  ```make
  test:
  	$(start)
  	mkdir -p .reports
  	uv run pytest -q --no-header --tb=short -p no:cacheprovider -n auto --dist loadscope \
  	  --junit-xml=.reports/junit.xml --cov --cov-report=term-missing:skip-covered
  	$(green)
  ```

  `--dist loadscope` keeps a module's tests on one worker, so the module-scoped fixtures of `tests/test_kill_points.py` are built once; measure `load` against it once and keep the faster.
- `CLAUDE.md`, *Checks*: each target ends with `<target>: green (<seconds> s)`; `make test` runs on every core and writes `.reports/junit.xml`; `make secrets` scans the files changed against `origin/main`, every tracked file on `main`.
- Before pushing: `uv run pytest -n auto -p no:cacheprovider` once; a test that fails only in parallel is reported to the human, and `-n auto` waits.

### H2, before S0002: pylint and vulture

Reason: 1.2; the report reads their output. `pyproject.toml`, `[dependency-groups] dev`: add `"pylint==<resolved>"` and `"vulture==<resolved>"`; `uv lock`. (`make licenses` checks production dependencies only.)

### H3, before S0003: the duplicates target, its baseline and record; the documents target and the docs stage's check

Reason: 1.2 (a lasting report whose findings reach the reviewer) and 1.9 (the document check as a check of the docs stage; F0011 decision 13 superseded for that stage).

- `Makefile`: add `duplicates documents` to `.PHONY` and

  ```make
  # Similar code (pylint's duplicate-code) and dead code (vulture) in src/factory, against the
  # accepted findings in security/duplicates-baseline.txt; a record, never a check.
  duplicates:
  	mkdir -p .reports
  	uv run pylint --disable=all --enable=duplicate-code --output-format=json --exit-zero src/factory > .reports/similar-code.json
  	uv run vulture src/factory --min-confidence 60 --ignore-decorators "@field_validator,@model_validator" --ignore-names model_config > .reports/dead-code.txt || [ $$? -eq 3 ]
  	uv run python -m factory.entry.check_duplicates --baseline security/duplicates-baseline.txt .reports/similar-code.json .reports/dead-code.txt

  # The four documents against the document check: a check of the docs stage, not of `check`.
  documents:
  	uv run python -m factory.entry.check_documents
  ```
- `security/duplicates-baseline.txt`: written by running the two tools as above and then `uv run python -m factory.entry.check_duplicates --baseline security/duplicates-baseline.txt --write-baseline .reports/similar-code.json .reports/dead-code.txt`. Before writing it, the session compares the tools' real output with the formats S0002 parses (pylint's JSON message lines `==<module>:[<start>:<end>]`, vulture's `<path>:<line>: <message> (<n>% confidence)`); a difference is a question for the human before S0003 starts. The findings S0003 to S0005 fix are in the baseline and show as `gone` once fixed (H4).
- `factory/stages.yml`, stage `doing`: add `records: [duplicates]`; stage `docs`: `checks: [check, documents]`.
- `CLAUDE.md`, *Checks*: `make duplicates` (a record after the coder, findings against the baseline) and `make documents` (a check of the docs stage); the pipeline knows `check`, `lint`, `test`, `duplicates` and `documents`.

### H4, after S0007: the baseline pruned

Reason: the fixed findings. Remove from `security/duplicates-baseline.txt` every key that `make duplicates` lists as `gone`; any `new` finding of the first report that no story fixed is either added (an accepted finding, with a `#` comment saying why) or becomes a story the human drafts.

### H5, before S0008: mutmut and `make mutants`

Reason: 1.3; the feature acceptance runs `make mutants` when the project has it (v1's acceptor, check 3).

- `pyproject.toml`, `[dependency-groups] dev`: add `"mutmut==<resolved>"`; `uv lock`; and

  ```toml
  [tool.mutmut]
  paths_to_mutate = ["src/factory/"]
  tests_dir = ["tests/"]
  # The tests read these from the repository root; mutmut runs them in its own copy.
  also_copy = ["claude/", "docs/", "factory/", "image/", "security/", "template/", "README.md", "Makefile", "pyproject.toml", "uv.lock", ".secrets.baseline"]
  ```
- `Makefile`: add `mutants` to `.PHONY` and

  ```make
  # Mutation testing of the modules under src/factory that one feature's commits changed:
  # `make mutants FEATURE=F0012`. Slow, so not part of `check`; the feature acceptance runs it.
  MUTATED = $(wildcard $(shell git log --format= --name-only -E --grep='^(ticket|work item) $(FEATURE)-S[0-9]{4}:' origin/main -- 'src/factory/*.py' | sort -u))
  mutants:
  	if [ -z "$(FEATURE)" ]; then echo "mutants: set FEATURE, as in make mutants FEATURE=F0012"; exit 2; fi
  	if [ -z "$(MUTATED)" ]; then echo "mutants: no module under src/factory changed by $(FEATURE)"; exit 0; fi
  	uv run mutmut run $(foreach module,$(MUTATED),"$(subst /,.,$(patsubst src/%.py,%,$(module))).*")
  	uv run mutmut results
  ```
- `.gitignore`: add `mutants/`.
- `CLAUDE.md`, *Checks*: `make mutants FEATURE=<id>`, outside `make check`.
- Verified once before pushing with `make mutants FEATURE=F0011` (the mutant names under a `src/` layout, the `also_copy` list); what differs is fixed in this change, not in S0008.

### H6, after S0023: the demo index

Reason: 1.7; S0023's check requires `demo/README.md` once `demo/` exists. `demo/README.md`:

```markdown
# Demos

Each folder is one demo: a project of one kind that v1.1 builds from an empty repository, with the stories a session starts while it plays the human. `python -m factory.entry.check_demos` checks every folder, and `make check` runs that check.

Every demo holds:

- `README.md`: what it builds, what it needs, the prompt for the session that plays the human, what a run looks like and costs;
- `project/`: the empty project the factory builds into, with its `CLAUDE.md`, `Makefile`, `pyproject.toml` and lock file, `factory/pipeline.yml` and `factory/story-form.md`;
- `features/`: the features and their stories in v1.1's work item form, `features/<F0001-slug>/feature.md` and `features/<F0001-slug>/backlog/<F0001-S0001-slug>.md`.

| Demo | Kind | Stack | What it builds | Stories | Baseline of |
|---|---|---|---|---|---|
```

(The todo demo of step 2 adds the row `` `todo-service/` ``.)

## Decisions taken for the human

Product decisions taken while writing the stories, for the human to review in one place. Each names where it was taken.

The human's answers (2026-10-17, `planning/overnight/restructure-after-f0011.md`):

1. Step 1 of the plan is this feature, built by v1, in the plan's order 1.1 to 1.10; steps 2 to 8 are not. (Section "The order of the work after F0011")
2. pytest-xdist, one prepared remote copied per test and `make secrets` over the changed files are granted. (Item 1.1; "The time `make check` takes")
3. `make duplicates` is a lasting report of pylint's R0801 and vulture against a baseline, with pylint and vulture as development dependencies, and its findings are fixed here: F0010-S0025's identity, F0011-S0001's `_rerun_seconds` and `_opening_text`, the redundant `tests/test_fault_path_names.py`, `_rerun` and `_branch_state`, the argv redundancy of `check_documents.main`, the two ways of finding `sudo`, F0002's copies of the UTC validator. (Item 1.2; "Duplicates and dead code"; "Further findings")
4. `make mutants` with mutmut, limited to the modules a feature changed and run by the acceptance stage, is granted; it takes in F0011-S0007. (Item 1.3)
5. The parked drafts F0003-S0011 and F0008-S0007 fold into item 1.2. (The human's answer under item 1.10)
6. The todo run must measure the low-disk machine stop, no temporary files left, the records of the project commands and of model against tool time, and the disk record; not a generic tracing system, not `docker stats`. (Item 1.4; "Disk space"; "Telemetry")
7. One test of the models' own configuration replaces the per-model tests of unknown, wrong-typed and assigned fields that only test Pydantic. (Item 1.5; "Tests of the DTOs' own configuration")
8. An answer at the send-back cap can grant more rounds. (Item 1.5; "Further findings", v1 past the cap)
9. The compose project is named per instance, `factory-${FACTORY_INSTANCE}`. (Item 1.6; "Renaming the repositories")
10. `demo/` holds one folder per demo and an index README, and one test in `make check` walks every demo. (Item 1.7; "The demo, shipped with v1.1")
11. The kill under `sudo` is `timeout --signal=KILL <limit>` inside the `sudo` call, exit status 137 read as `time_limit`, a grace time on the outer call; F0010 decision 30 is decided this way. (Item 1.8)
12. The document check is a check of the docs stage only, through `make documents`, in v1's `factory/stages.yml` now; F0011 decision 13 is superseded for the docs stage. (Item 1.9)
13. Three of F0010's open points are fixed (the agent files and `settings.json` read-only to the agent, a missing health file not healthy, a standing `main_branch_failing` cleared); the token file's default in the image's `ENV` and the template's write paths stay as built. (Item 1.10)

Taken by the session for the human, to confirm (2026-10-17, story texts):

14. `make duplicates` is a record of the `doing` stage, not of `review`: v1 runs a stage's `records` after its agent and writes their last line into that agent's entry, so on `review` the line would follow the review it should inform; on `doing` it is in the coder's entry, which the reviewer reads. (H3)
15. The duplicates baseline holds line-independent keys (`similar-code <modules>: <first line>`, `dead-code <path>: <message>`), so a moved block stays known and a changed block is new; `--write-baseline` writes it, and a baseline key no longer found is reported as `gone`. The report exits 1 with new findings, which v1 logs like any record. (S0002)
16. Item 1.9 has no story: the human's change H3 wires the check, and S0003's docs criterion rewrites the documents' sentence about it. (S0003)
17. `sudo` is found one way: on the `PATH`, as the preflight's `tool:sudo` item finds it; the runtime starts what `which("sudo")` finds, and `/usr/bin/sudo` only when nothing is found (the preflight then stops the machine anyway). (S0003)
18. The shared UTC type is `factory.domain.times.UtcDatetime`, a new domain module, used by the five fields that convert today. (S0004)
19. The two uncovered lines of `claude_runtime.py` (384: a resume with no time left, which needs an injected clock; 408 to 409: a write fault in an existing state directory, which a root user does not get) are not tested here. (S0003)
20. The low-disk stop is a new reason `disk_low` of scope `machine`, a fifteenth row `disk-low` of `STOP_TABLE` with v1's limit `L64` (the machine's own stops), checked once at the start of every tick before the fetch, which covers the preflight inside it; it watches the free space of the work directory (the checkout's parent) and of the state directory against `FACTORY_MIN_FREE_GB` (default 5, gigabytes of 10^9 bytes); a free space that cannot be read is a stop too. Tests that tick through `build_boundaries` (`tests/entry/test_run.py`) read the real free space of their `tmp_path`, far above 5 GB in v1's container. (S0009, S0010)
21. The records of project commands and the disk records are JSON lines in the state directory, `records/project-commands.jsonl` and `records/disk.jsonl`: telemetry beside the factory log, not work item state, so not in git; a line that does not parse is skipped on reading, because a kill can tear the last one. (S0013, S0016)
22. The model's time of a run is the reply's `duration_api_ms`; the rest of the run's time is the tools' and the factory's. The time per tool command inside a run is not recorded, because the single JSON reply does not carry it (it needs `claude`'s streamed events). The cost table gets a column `model min`; the board, which shows no cost today, is unchanged. The count of `make check` runs per commit is read from the records of the project commands, with no counter of its own. (S0013 to S0015)
23. The disk record is written at an instance's start and whenever an acceptance reviewer's prompt is composed; the prompt carries the record of now and the one of the previous acceptance. (S0016, S0017)
24. "No temporary files left": the factory's own code makes none that it does not remove (checked on 2026-10-17: only `atomic_file.replace_text`, which removes its file on failure); the smoke tester, the acceptance reviewer and the documenter get a lesson to work in a temporary directory that removes itself, and pytest keeps only the folders of failed tests (H1). The acceptance reviewer also gets a lesson to read the JUnit report's time per test. (S0011)
25. The models that read a tool's own output keep `extra="ignore"` and are the exceptions of the configuration test: `_ToolInput` and `_Payload` in `factory.adapters.claude_guard`, `_Usage`, `_Denial`, `_StructuredOutput` and `_Reply` in `factory.adapters.claude_runtime`. Removed are only tests that check nothing but a refused assignment, a refused unknown key, a round trip or a refused plain wrong type; a test that also checks a pattern, a `Literal`, a limit or a rule stays. The removal is split over three stories (S0018 to S0020) to keep each tester's run small. `Boundaries` is a dataclass, not a Pydantic model, so its assignment test stays. (S0018 to S0020)
26. An answer to a `round_cap` wait sets `round` to 0, as an answer to the other two caps resets its counter, so the human's answer grants the cap's rounds again; the question says so. Closing the pull request still discards the work item. (S0021)
27. Under `sudo`, the inner limit is the time limit in whole seconds rounded up, and the outer limit adds a grace of 30 seconds; a call with an operating-system user that ends killed by `SIGKILL` (exit status 137, or -9 as Python reports a signal) after at least its time limit is `time_limit`, with no measures. (S0024)
28. The agent home `/home/agent/.claude` belongs to `factory`, group `factory-work`, mode `3775` (the sticky bit, so the agent can add its own files there, its login among them, but cannot rename or delete the factory's); `agents/` is `0755` and the agent files and `settings.json` are `0644`, written by the entrypoint. The home's mount point keeps the agent from renaming the folder itself. F0010 decision 21 is superseded for these files. (S0025)
29. `factory-run` writes an empty health status when none exists, at the start of the instance; `factory-health` prints `no health status: <path> is missing` and exits 1 when the file is missing. A damaged file still reads as healthy (every stop is raised again while its fault lasts). (S0026)
30. While the machine items fail, a standing `main_branch_failing` whose failing commit is no longer `origin/main` is cleared, because the stop no longer describes `main`; the new `main` is probed when the machine passes again. (S0027)
31. The demo check is a command, `python -m factory.entry.check_demos`, and its test in `make check` runs it on this repository; a demo's stories are backlog stories, checked as specifications at the path they will have in the project (`factory/features/...`); the index must name every demo folder in backticks. (S0023)
32. The human's leave for F0012-S0001 (taken by the session for the human, to confirm): its tester changes `tests/git_support.py` (a new `copy_remote`), `tests/conftest.py` (a session fixture `remote_template`; the fixtures `remote` and `world` copy it) and `tests/proof_support.py` (`build_world` takes a template), without changing what any test asserts. (S0001, story text)
33. The human's leave for F0012-S0005 (taken by the session for the human, to confirm): its tester replaces `_rerun_seconds` in `tests/test_kill_points.py` by a public `rerun_seconds` in `tests/proof_support.py`, which `_kill_to_rerun_recorded` uses too, and adds to `test_the_rerun_starts_five_seconds_after_the_kill` the check `kill-to-rerun-recorded`; renames `_opening_text` to `_opening_document`; makes `_rerun` call `rerun`; replaces `_branch_state` in `tests/test_fault_paths_7_to_13.py` by a public `branch_state` in `tests/proof_support.py`; deletes `tests/test_fault_path_names.py`, whose two tests `tests/test_fault_paths_table.py` holds for all thirteen paths. (S0005, story text)
34. The human's leave for F0012-S0010 (taken by the session for the human, to confirm): its tester adds the row `disk-low` to `ROWS` and renames `test_the_table_holds_the_fourteen_stops_in_order` to `test_the_table_holds_the_fifteen_stops_in_order` in `tests/domain/test_stop_table.py`; gives `disk_low` the scope `machine` in `test_repository_stop_reaches_the_health_status_and_the_factory_log` of `tests/test_stop_table.py`; adds the row `("disk_low", "machine")` to `SCOPES` in `tests/domain/test_stops.py`; adds `disk_low` to the parametrization of `test_every_stop_reason_makes_the_check_fail_until_it_is_cleared` in `tests/entry/test_health.py`. (S0010, story text)
35. The human's leave for F0012-S0011 (taken by the session for the human, to confirm): its tester adds the new lessons to `LESSONS` in `tests/test_claude_agent_texts.py` for `smoke-tester`, `acceptance-reviewer` and `documenter`. (S0011, story text)
36. The human's leave for F0012-S0013 (taken by the session for the human, to confirm): its tester changes `isinstance(boundaries.project_commands, MakeProjectCommands)` in `test_build_boundaries_picks_the_concrete_adapters_and_writes_nothing` of `tests/entry/test_wiring_boundaries.py` to `RecordingProjectCommands`. (S0013, story text)
37. The human's leave for F0012-S0014 (taken by the session for the human, to confirm): its tester adds `"model_seconds":41.5` to `COMPLETED_LINE` and `"model_seconds":null` to `STARTED_LINE` in `tests/adapters/test_cost_records_jsonl.py`, at the place the writer puts the key, and the matching value to `COMPLETED`. (S0014, story text)
38. The human's leave for F0012-S0015 (taken by the session for the human, to confirm): its tester changes the expected table of `test_the_cost_table_of_the_demo_stage_bills` in `tests/domain/test_bills.py` to the new column. (S0015, story text)
39. The human's leave for F0012-S0018, S0019 and S0020 (taken by the session for the human, to confirm): their testers remove exactly the tests each story lists, and the helpers and imports that only those tests used. (S0018 to S0020, story text)
40. The human's leave for F0012-S0021 (taken by the session for the human, to confirm): its tester moves the `round_cap` row out of `test_unblock_clears_the_wait_and_changes_nothing_else` in `tests/domain/test_answers.py` into the new test of the reset, and changes the expected text of `test_the_round_cap_question_names_the_rounds_and_the_cap` in `tests/domain/test_question_texts.py`. (S0021, story text)
41. The human's leave for F0012-S0024 (taken by the session for the human, to confirm): its tester changes the expected head of the `sudo` call in `test_with_a_user_sudo_gets_the_user_env_i_the_environment_and_the_executable` of `tests/adapters/test_claude_runtime_os_user.py`. (S0024, story text)
42. The human's leave for F0012-S0025 (taken by the session for the human, to confirm): its tester removes the row `/home/agent/.claude` from `test_the_shared_directories_are_writable_by_the_work_group` in `tests/test_image.py`; the new test of the agent home holds that path. (S0025, story text)
43. The human's leave for F0012-S0026 (taken by the session for the human, to confirm): its tester turns `test_a_state_directory_without_a_health_file_is_healthy` in `tests/entry/test_health.py` into the test of the missing file, and writes an empty status for the healthy row of `test_the_module_run_as_a_process_exits_with_the_health_status`. (S0026, story text)
44. For the human, outside the stories: the project guide is 1,641 lines and this feature adds to it; the session checks its length after each story, and if it passes about 1,800 lines, the split planned for the restructure is brought forward as a human commit between two stories (with `PROJECT_GUIDE` in `src/factory/domain/documents.py` repointed by a story). The lessons file (`planning/lessons-for-the-skills.md`) gets the rows of S0011's two lessons.
