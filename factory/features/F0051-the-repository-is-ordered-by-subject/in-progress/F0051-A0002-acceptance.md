---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 571
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-05T11:12:16.230428Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-05T11:17:55.816701Z'
  stage: acceptance
  run: 7067c97c013a43629ca0c6671294e5a9
stories: [F0051-S0001, F0051-S0002, F0051-S0003, F0051-S0004, F0051-S0005, F0051-S0006, F0051-S0007, F0051-S0008, F0051-S0009, F0051-S0010, F0051-S0011, F0051-S0012, F0051-S0013, F0051-S0014, F0051-S0015]
outcome: null
---

# Acceptance of The repository is ordered by subject

## Recommendation

**Accepted.** This is the second acceptance of F0051. It was due because S0014 and S0015, the two stories F0051-A0001 proposed, are now merged. Every scope item has its merged story, and `make check` is green as I found it. The feature's walk-through is green end to end, and it now also covers what the two new stories promised: a removed module brought back inside an area is found again, and the setup's hints name `docs/operator-guide/machine.md`. What is still left over is only remarks or the human's own files (`demo/`, the playbook, the duplicates baseline, the decision log's history), so I propose no story.

## 1 Scope

None. The scope lines and their stories, all under `done/`:

- The seven areas, each with `domain`, `application` and `adapters`: S0001 to S0007. `src/factory/` holds only `__init__.py`, the seven areas, `entry` and `contract`.
- The layer rule blocks and the area rule only reports: the forbidden contracts in `pyproject.toml`, and `make areas`, which is not in `check:`.
- `tests/` mirrors the areas, and its root holds only `conftest.py`: S0001 to S0008.
- The project guide has one file per area: S0009.
- The operator guide is a folder of topics: S0010.
- `agents/`: S0011. `operator/vm/` and `operator/template/`: S0012.
- The repairs: S0013 (from F0050-A0003), S0014 and S0015 (both from A0001). `feature.md` lists all three, and each stays inside the goal.

No story is outside the scope, and Out of scope holds:

- No name of a module, class or function changed, and the records contract is unchanged (check 2).
- `demo/` stays at the root, and `operator/claude/` and `operator/opencode/` keep their names.
- The old entries of `docs/decisions.md` keep their paths.

S0014 and S0015 changed no module under `src/`.

## 2 Feature smoke test

Green. The walk-through is what a contributor does after the feature:

- look at the package and its layers;
- run the layer rule and the area report;
- look at `tests/` and both guides;
- find the agent, VM and template files;
- check that a removed module stays removed in every area (S0014);
- read the setup's pointers to the operator guide (S0015);
- check that the factory still does what it did.

The script ran from `/work/checkout` and lived in a `mktemp -d` folder that removes itself. The tree stayed clean (`git status --short` printed nothing afterwards).

Command: `sh "$d/smoke.sh"`

```
== 1 the package holds the seven areas, entry and contract, each area its three layers
__init__.py agents contract entry hosting machine pipeline shared watching work 
shared: domain=12 application=1 adapters=5
hosting: domain=4 application=4 adapters=3
work: domain=10 application=3 adapters=1
agents: domain=8 application=5 adapters=6
watching: domain=6 application=5 adapters=6
machine: domain=5 application=8 adapters=11
pipeline: domain=11 application=14 adapters=1
factory.domain importable: False
factory.application importable: False
factory.adapters importable: False
== 2 the layer rule blocks, the area rule only reports
layers: green (0.2 s)
Contracts
Areas, from the top: pipeline, watching, agents, machine, work, hosting, shared BROKEN
Contracts: 0 kept, 1 broken.
check: lint types layers sast secrets licenses test
== 3 the root of tests holds only conftest.py and folders
tests/conftest.py
== 4 the guides: one project-guide file per area, the operator guide a folder
project-guide/shared.md
project-guide/hosting.md
project-guide/work.md
project-guide/agents.md
project-guide/watching.md
project-guide/machine.md
project-guide/pipeline.md
operator-guide.md gone
README.md agent-runtime.md cloud-run.md health.md install.md machine.md pipeline.md records.md site.md stops.md work-items.md 
documents ok
== 5 agents/, operator/vm/, operator/template/
claude gone
vm gone
template gone
agents/agents present
operator/vm present
operator/template present
operator/vm/Dockerfile:58:COPY agents /etc/factory/agents
operator/vm/Dockerfile:59:RUN chmod 0755 /etc/factory/agents /etc/factory/agents/agents && find /etc/factory/agents -typ
== 6 a removed module brought back in an area is caught (S0014)
old path of a live module found: True
removed module found: False
import of it in an area named: True
168 passed, 2426 deselected in 2.07s
== 7 the setup's hints name the topic file (S0015)
2
see "The machine" in docs/operator-guide/machine.md
5:## The machine
== 8 behaviour unchanged: the records contract, two console commands
contract: generated schemas equal the committed ones
factory/features/F0051-the-repository-is-ordered-by-subject/done/F0051-S0015-the-setup-hints-name-the-operators-guide-topic-file.md: ok
check-story exit 0
not a work item id: factory/features/F0051-the-repository-is-ordered-by-subject
bill exit 0
```

Two lines are faults of my script, not of the factory. I reran both:

- In step 7, my `grep` looked for `## The rebuild after a merge`, but the heading is one level lower. `grep -n 'The rebuild after a merge' docs/operator-guide/machine.md` gives `570:### The rebuild after a merge`, so both sections the hints name exist.
- In step 8, I passed `factory-bill` a folder instead of a work item id. `uv run factory-bill F0051-S0015` gives `Cost: 10 runs, 9.0 min, 55 turns, 177888 tokens in (1031265 more from cache), 17074 out, $1.73`, exit 0.

Step 1 counts files flat, so pipeline's `application` shows 14. The 10 modules of `pipeline/application/handlers/` make it 24, as in A0001.

`make areas` reports `BROKEN`, as feature decision 3 intends. `make check` as I found it ended with `test: green (131.2 s)` and `check: green`, with coverage at 99.26 %.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

A0001 already collected S0001 to S0013. Since then, the human's follow-ups have closed most of the open items:

- `Makefile:109,120` now gives `factory.machine.domain.disk`.
- `demo/todo-service/README.md:15` now names `operator/template/`.
- The temporary write paths are gone from `factory/pipeline.yml:24`, and so are the old `vm/*` and `template/*`.

New from S0014 and S0015, or still open:

- **The wrapper guard still skips old names (S0014 coder and tester).** `tests/guards/test_wrapper_out_of_the_call_path.py:9` keeps `GUARD_MODULES` at old layer paths (`factory.adapters.landlock`, `factory.domain.confinement`), so the skip by name can never match. This makes the guard stricter, not weaker: a landlock brought back inside an area would be flagged twice. The import check goes through `names_the_module_anywhere`. Remark only.
- **The refused side of "`entry` and `contract` are not areas" has no row (S0014 reviewer, round 1 note).** The code handles it (`NOT_AREAS`, `tests/support/module_names.py:11`). This is a note, not a finding.
- **The pointer guard has nothing left to catch on `main` (S0015 coder, human's answer 11).** After the story, no line under `operator/vm/` or `operator/skill/` says `operator guide`, so the first row of `test_every_mention_of_the_operator_guide_names_its_path` checks an empty set. The guard still asserts that it read lines, and its made-up rows show that it catches a bare mention. Remark only.
- **The pointer guard keeps its own `ROOT` and `SETUP` (S0015 reviewer).** They match those in `tests/support/vm_support.py`, which a module of `tests/guards/` may not import. This is justified, so no finding.
- **The decision log has pointers without a file (S0015 documenter).** `docs/decisions.md:179` and `:572` say "(operator guide)", and `:1432` names `docs/operator-guide.md`. The log is history and is out of scope.
- **Pointers without a file in the human's files, and one docstring:**
  - `demo/todo-service/README.md:20,22,45` (`demo/` is out of scope, and those lines also describe the Docker path that F0044 removed);
  - `docs/operator-playbook.md:82` ("the operator guide's `fstrim` and `compact vdisk` steps");
  - `src/factory/entry/wiring.py:746`, a docstring ("in the operator guide's order"), which S0015 left out on purpose.

  None of these misleads an operator of the factory, so I propose no story.
- **`make duplicates` still drifts:** `5 new, 40 known, 3 gone`, the same five and three as in A0001.
  - Two lines are known pairs whose key changed: the `hand_over`/`acceptance` pair now comes in the other order, and the runtime pair is now keyed on `version_launch`.
  - Three are `cost_records.py`'s machine fields.
  - `security/duplicates-baseline.txt` is the human's file, and the output is a record, not a check.
- **The take loses a renamed directory's unedited files (S0011, S0012).** This is still the human's candidate 63.

## 5 The documentation as a whole

None. I read `README.md`, `docs/operator-guide/README.md` and `docs/project-guide/README.md` again from the top, and searched every tracked file outside the decision log, `docs/runs/`, `planning/` and the work items for "operator guide" without a path.

- The remaining hits are the human's files and one docstring (check 4).
- `docs/operator-guide/machine.md:284,295-296` now quotes `operator/vm/setup.sh:405,453,476` word for word. The *Shared test helpers* section of `docs/project-guide/README.md` now names `module_exists_anywhere` and the search guard (S0014).
- `make documents` gives `documents ok` (smoke step 4).
- No two stories contradict each other, and no section is missing.

## 6 Decisions taken for the human

To accept or revisit:

1. Feature decisions 1 to 8, as `feature.md` lists them, and the decisions A0001 gathered: S0007 to S0012, the placement rules, and `FACTORY_CLAUDE_HOME`, which keeps its name. A0001's item 5, the temporary write paths, is settled: `factory/pipeline.yml` no longer holds them (commit 8c889989e).
2. S0014: the human's leave in `feature.md` ("At S0014's start", journal 4) for ten earlier tests. Two choices the tester made, which the reviewer accepted:
   - An area is any package folder directly under `src/factory/` except `entry` and `contract` (`areas()`), not a fixed table.
   - An old layer path is `factory.<domain|application|adapters>.<rest>`, where every part of the rest is an identifier (`is_old_layer_path`, round 1).
3. S0015:
   - the human's leave in `feature.md` ("At S0015's start", journal 4) for two earlier tests;
   - answer 11: the topic-file names are collected from every searched line that holds `docs/operator-guide/`, and the non-empty assertion is kept, so the test cannot pass vacuously;
   - the Interface's texts stay as approved: the new hints drop the words "operator guide" (option (b) rejected).
4. Earlier tests changed, and the leave each was changed under:
   - **S0014:** `tests/entry/test_mutation_report_removed.py`, `tests/guards/test_checkout_hygiene_removed.py`, `test_docker_path_removed.py`, `test_home_reset_removed.py`, `test_hook_removed.py`, `test_kernel_guard_removed.py`, `test_leftovers_program_removed.py`, `test_undo_removed.py`, `test_wrapper_out_of_the_call_path.py`, and `tests/pipeline/application/test_stall_environment.py::test_the_stall_module_imports_no_name_of_the_undo`. All ten are under S0014's leave (journal 4).
   - **S0015:** `tests/vm/test_vm_setup_install_hint.py` (`HINTS`) and `tests/vm/test_vm_setup_text.py` (row `done-line`), both under S0015's leave (journal 4).

   The reviewers named every one. Together with A0001's list, I found no earlier test changed without a leave.

## 7 The slow checks

Nothing beyond `make check`. The project's other targets are `make mutants` (check 3) and two records, `make duplicates` and `make areas`, both read above.

The JUnit report of my `make check` holds 10,670 tests (33 more than at A0001, the tests of S0014 and S0015). They took 1,151 s summed over the workers and 131.2 s wall. The slowest are the time-limit tests at about 10 s each (`ROOMY_LIMIT`):

- `tests/machine/adapters/test_podman_timeout_status.py::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run[137-at-the-limit]` (10.1 s) and its `[255-at-the-limit]` row (10.0 s);
- `tests/agents/adapters/test_claude_runtime_resume.py::test_call_killed_by_the_time_limit_has_no_model_duration[nothing printed]` (10.0 s);
- `tests/shared/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_process-own-session]` (10.0 s).

Disk: at the previous record (`disk start`), `/srv/factory/vm` had 23.1 GB free and 1.4 GB used. Now it has 23.0 GB free and still 1.4 GB used, and `state` and `/tmp` are at 0.0 GB used in both. The 0.1 GB less free space lies outside the instance's datasets, in the shared pool. Nothing in the feature's changes needs to explain it: S0014 and S0015 change only text and tests, and used space did not grow.

## 8 Cost

The 15 stories cost 160 runs, 294.6 min, 1640 turns and $53.69, about $3.58 and 20 min per story.

- The two new stories were cheap: S0014 cost 11 runs, 11.9 min and $2.41, and S0015 cost 10 runs, 9.0 min and $1.73.
- S0014 had a review round on test-helper copies.
- S0015 had a question: its new guard demanded a non-empty set that the approved texts could not give, and it had a missing annotation.

The stories that stand out are those A0001 named:

- **S0010** ($6.94, 17 runs): a review round over references.
- **S0001** ($5.63, 13 runs): the first stall, when the coder's test changes were dropped from the take.
- **S0011** (18 runs, $4.99) and **S0012** ($3.06): both reached the attempts cap through the take's directory-rename gap.

Human interventions: the human answered 22 questions (20 questions and 2 attempts caps) and waited 2.4 h in all. S0014 and S0015 added 3 questions and about 0.3 h. Two of the three were the same missing leave in `feature.md` for changing earlier tests, which the acceptance's proposal named but could not grant. S0008 still needed the human most, with four answers: the placement rules for about 200 root modules (entries 4 and 23) and two rewordings for detect-secrets (entries 15 and 18).

## Proposed stories

None. Every open item is a remark, the human's own file (`demo/`, the playbook, `security/duplicates-baseline.txt`), out of scope (the decision log), or already the human's candidate (63).

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 0 stories proposed. `make check` was green as I found it: `check: green`, coverage 99.26 %. The feature's walk-through is green end to end, including the two stories that A0001 proposed (S0014, S0015).
   1 Scope: none. Every scope item has its merged story. S0013, S0014 and S0015 are repairs that `feature.md` lists. Out of scope holds: no names changed and the records contract is unchanged.
   2 Smoke test: green.
      - The package holds the seven areas with three layers each, and the old layer packages cannot be imported.
      - `make layers` is green. `make areas` reports BROKEN outside `check`, as intended.
      - The root of `tests/` holds only `conftest.py`.
      - Both guides are folders, and `make documents` gives `documents ok`. `agents/`, `operator/vm/` and `operator/template/` are in place.
      - A removed module brought back inside an area is found. The setup's hints name `docs/operator-guide/machine.md`.
      - The contract is unchanged, and `factory-check-story` and `factory-bill` work.
      - Two lines were faults in my script (a heading level, a wrong argument to `factory-bill`). I reran both, and both passed.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the human's follow-ups closed A0001's items in the Makefile, the demo's template path and the write paths. Open remarks only:
      - the wrapper guard's `GUARD_MODULES` still names old paths, which makes it stricter, not weaker;
      - the `entry` and `contract` refused side has no row, but the code handles it;
      - the new pointer guard has nothing left to catch on `main`, by design;
      - pointers without a file remain in `docs/decisions.md` (history), `demo/` and the playbook (the human's), and one docstring;
      - the duplicates drift is still 5 new, 3 gone (the human's baseline);
      - candidate 63 is still open.
   5 Documentation: none. The guides agree with the tree and with each other, and `machine.md` quotes the new setup lines word for word.
   6 Decisions: feature decisions 1 to 8 and A0001's list, whose temporary write paths are now settled. Also S0014's and S0015's leaves for earlier tests and S0015's answer 11. Every changed earlier test has its leave named.
   7 Slow checks: nothing beyond `make check`. 10,670 tests ran, 131.2 s wall. The slowest are the roughly 10 s time-limit tests. Used disk is unchanged at 1.4 GB, and free space is 0.1 GB lower, in the shared pool.
   8 Cost: 160 runs, 294.6 min, $53.69. S0014 ($2.41) and S0015 ($1.73) were cheap. S0010 ($6.94) is still the most expensive. The human answered 22 questions (20 questions, 2 attempts caps) and waited 2.4 h. Two of the three new questions were missing leaves in `feature.md` for changing earlier tests. S0008 needed the human most (four answers).
