---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 568
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-05T09:47:24.152737Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-05T09:59:00.133527Z'
  stage: acceptance
  run: e2a6428d2e9347d98c90ca665cc73420
stories: [F0051-S0001, F0051-S0002, F0051-S0003, F0051-S0004, F0051-S0005, F0051-S0006, F0051-S0007, F0051-S0008, F0051-S0009, F0051-S0010, F0051-S0011, F0051-S0012, F0051-S0013]
outcome: null
---

# Acceptance of The repository is ordered by subject

## Recommendation

**Accepted with stories.** Every scope item has a merged story, `make check` is green, and the feature's walk-through is green end to end: seven areas with three layers each, the layer rule enforced and the area rule only reported, a sorted `tests/`, both guides split into files, `agents/` and `operator/{vm,template}/`, and an unchanged records contract and CLI. The two findings worth stories do not break any promise the feature made. The removal guards of earlier features still look for their removed modules at the old layer paths, which can no longer exist, so they now check nothing (S0014). The VM setup's hints and one skill reference name "the operator guide" without its topic file (S0015). A short list of the human's own follow-ups is under 4 and 6.

## 1 Scope

None. Every scope line has its story under `done/`, and the code holds what they describe:

- The seven areas: S0001 to S0007. `src/factory/` holds only `__init__.py`, the seven areas, `entry` and `contract`, and each area has `domain`, `application` and `adapters` with docstrings. The old layer packages cannot be imported (`tests/guards/test_old_layer_packages_removed.py`).
- The layer rule blocks, the area rule reports: the forbidden contracts in `pyproject.toml` (`make layers` green), and `make areas` (`.importlinter-areas`, which reports `BROKEN` and is not in `check:`).
- The tests mirror the areas, and the root holds only `conftest.py`: S0001 to S0008, with `tests/guards/test_tests_layout.py`.
- The project guide has one file per area: S0009.
- The operator guide is a folder, and the document check follows it: S0010.
- `claude/` → `agents/`: S0011. `vm/`, `template/` → `operator/`: S0012. S0013 is the docs repair carried over from F0050-A0003.

No story is outside the scope. Out of scope holds: the regenerated contract equals the committed one (check 2), `demo/` stays at the root, `operator/claude/` and `operator/opencode/` keep their names, and `docs/decisions.md` keeps its old paths.

## 2 Feature smoke test

Green. The walk-through is what a contributor does after this feature. They look at the package and its layers, run the layer rule and the area report, look at `tests/` and both guides, find the agent, VM and template files, and check that the factory still does what it did: the same records contract, and two console commands run against archived stories. The script lived in a `mktemp -d` folder that removes itself. Step 1's last three lines failed because of a bug in my script (`import importlib` without `importlib.util`), not in the factory. The rerun of that step follows the output.

Command: `sh "$d/smoke.sh"` (run from `/work/checkout`)

```
== 1 the package holds the seven areas, entry and contract, each area its three layers
['__init__.py', 'agents', 'contract', 'entry', 'hosting', 'machine', 'pipeline', 'shared', 'watching', 'work']
shared domain/application/adapters = [12, 1, 5]
hosting domain/application/adapters = [4, 4, 3]
work domain/application/adapters = [10, 3, 1]
agents domain/application/adapters = [8, 5, 6]
watching domain/application/adapters = [6, 5, 6]
machine domain/application/adapters = [5, 8, 11]
pipeline domain/application/adapters = [11, 24, 1]
Traceback (most recent call last):
  File "<stdin>", line 13, in <module>
AttributeError: module 'importlib' has no attribute 'util'
== 2 the layer rule blocks (make layers), the area rule only reports (make areas)
layers: green (0.2 s)
Areas, from the top: pipeline, watching, agents, machine, work, hosting, shared BROKEN
Contracts: 0 kept, 1 broken.
Makefile lines naming areas: 3
check: lint types layers sast secrets licenses test
== 3 the root of tests holds only conftest.py and folders
tests/conftest.py
== 4 the project guide has one file per area; the operator guide is a folder
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
== 5 the agent files, the VM's files and the template
claude absent
vm absent
template absent
agents/agents present
operator/vm present
operator/template present
== 6 behaviour unchanged: the records contract, the CLI
contract: generated schemas equal the committed ones
factory/features/F0051-the-repository-is-ordered-by-subject/done/F0051-S0013-the-operator-guides-push-error-example-shows-the-porcelain-ref-line.md: ok
check-story exit 0
| **total** | 6 | 3.8 | 1.5 | 27 | 87646 | 369997 | 6286 | 0.75 |

Cost: 6 runs, 3.8 min, 27 turns, 87646 tokens in (369997 more from cache), 6286 out, $0.75
bill exit 0
```

The rerun of the old-layer step:

```
$ uv run --quiet python -c "import importlib.util; ..."
old layer domain importable: False
old layer application importable: False
old layer adapters importable: False
```

`make areas` reports `BROKEN` as feature decision 3 intends: the areas still import each other both ways. The `|| true` in the recipe keeps it a report, and `check:` does not name it. `make check` as I found it: `test: green (130.9 s)`, `check: green`, coverage 99.26 %.

An aside on the contract step: an earlier call of mine, `python -m factory.entry.contract --help`, wrote the five schemas into a folder named `--help`. The command takes its first argument as the output folder. I compared that folder with `src/factory/contract/`, found it identical, and removed it. Nothing of it is left in the tree.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Collected from the coder, reviewer, documenter and smoke-tester entries, each checked against `main` as it is now:

- **Closed on `main` since:** the frontmatter guard's module filter (S0001 to S0002). `tests/work/adapters/test_work_item_markdown.py::_layer` now reads both forms. Also closed: `CLAUDE.md`'s `factory.domain.contract.CONTRACT` and `src/factory/adapters/process.py` (S0001, S0004), the old per-file-ignores in `pyproject.toml` (S0004, S0006), the mutmut `--deselect` paths (S0007, S0008; every path in `pyproject.toml` exists), `CLAUDE.md`'s "root of `tests/`" sentence (S0008), and the project guide's "the operator guide, *Section*" references without a file (S0010; none left in `docs/project-guide/`).
- **The removal guards look at old paths (new here, not noticed by any story; S0014).** S0007's leave lets `module_exists` count a missing parent package as "gone". With the old layer packages removed, every guard that names a removed module at `factory.domain.*`, `factory.application.*` or `factory.adapters.*` is now always true. A removed module brought back inside an area would pass. The affected names: `sessions` (`tests/guards/test_docker_path_removed.py:61`), `sealed_runs` (`test_checkout_hygiene_removed.py:43`), `agent_home` and `home_files` (`test_home_reset_removed.py:21-24`), `claude_guard` (`test_hook_removed.py:27`), `landlock` and `confinement` (`test_kernel_guard_removed.py:14`, `test_wrapper_out_of_the_call_path.py:7-8`), `leftovers` (`test_leftovers_program_removed.py:23`), `undo` (`test_undo_removed.py:32`, `tests/pipeline/application/test_stall_environment.py:139`) and `mutants` (`tests/entry/test_mutation_report_removed.py:12`).
- **Pointers to "the operator guide" without a file (S0010's documenter; S0015).** `operator/vm/setup.sh:405,453,476` and `operator/skill/kumpel/references/approving.md:25`, quoted in `docs/operator-guide/machine.md:284,295-296`. `src/factory/entry/wiring.py:746` ("in the operator guide's order") is a docstring and is left out of S0015.
- **The human's files, still naming old paths:** `Makefile:109` and `:120`, the `make mutants` comment and usage message, give `MODULES=factory.domain.disk`, which now matches nothing. S0007's answer gave `factory.machine.domain.disk` for the docs. `demo/todo-service/README.md:15` names `template/factory/pipeline.yml` (now `operator/template/`), and `:27` names `docs/operator-guide.md` (now `docs/operator-guide/machine.md`). `demo/` is in no role's write paths. `docs/operator-playbook.md:82` names "the operator guide's `fstrim` and `compact vdisk` steps" without a file.
- **The take loses a renamed directory's unedited files (S0011, S0012).** Already the human's candidate 63 in `planning/f0051-candidates.md`, so no story is proposed.
- **`security/duplicates-baseline.txt`:** no old path is left. `make duplicates` now gives `5 new, 40 known, 3 gone`. Two of the new lines are known pairs whose key changed: the `hand_over`/`acceptance` pair in the other order, and the claude/opencode pair keyed on `version_launch` instead of `finished_run`. Three are `cost_records.py`'s machine fields, new since F0050. The one extra gone line is `fake_containers.calls`. This is a record, not a check, and the file is the human's.
- **Guards that got narrower but are covered elsewhere:** `tests/guards/test_layers.py` now checks only `factory.pipeline.domain`'s imports. The forbidden contracts of `make layers` cover every area, so this needs no story. Remark only.
- **The project guide's per-area files describe some modules of other areas:** for example, `watching.md` describes `factory.pipeline.domain.evaluation`, `work.md` describes `factory.shared.domain.paths`, and `machine.md` describes `factory.pipeline.application.take`. This follows S0009's rule (by subject), and the index names each module's file. Remark only.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide/README.md` and `docs/project-guide/README.md` from the top, and checked every repository path the guides and `CLAUDE.md` name in backticks. All exist, apart from placeholder examples (`src/a/b.py`, `tests/<area>/<layer>/`). `make documents` gives `documents ok`. No two stories contradict each other. The layout described in `README.md`, the project guide's *The code's layout* and *Shared test helpers*, and `CLAUDE.md`'s *Architecture* and *Tests* agree with the tree. The one stale part is outside the two guides: the hints of `operator/vm/setup.sh`, quoted word for word in `docs/operator-guide/machine.md:284,295-296`, send the operator to "the operator guide" as if it were still one file (S0015). The demo README's two dead paths and the Makefile's mutants example are the human's (check 4). No section is missing.

## 6 Decisions taken for the human

To accept or revisit:

1. Feature decisions 1 to 8 as `feature.md` lists them: areas with layers inside, the seven-area map, the layer rule blocks while the area rule reports, moves without shims, the tester's leave per move, one story per area, the new top-level packages, and the intake's standing answers.
2. S0007 (answer 8): `module_exists` counts a `ModuleNotFoundError` of a missing parent as "gone". This made the removal guards true by construction once the old layers were gone (check 4, S0014).
3. S0008 (answers 4, 23): test placement by name rules, then by the area a module imports most, or second most when the name is taken. Test modules that import nothing of `factory` go to `guards/`. Two modules keep their places rather than being renamed. `operator_scripts/` instead of `operator/`.
4. S0009 (answers 4, 9) and S0010 (answers 4, 9, 14): a section goes to the area of the first module it names. Placement and pointers are the reviewer's judgement, not a test. One heading count per heading, and `docs/runs/` and `docs/decisions.md` are left out of the searches.
5. **The temporary write paths are still in force.** S0009 (answer 17) let the coder write `docs/project-guide/*`, `docs/operator-guide.md`, `docs/operator-guide/*` and `README.md` "for the rest of F0051 only". `factory/pipeline.yml:24` still holds them, together with the old `vm/*` and `template/*` and the gone `docs/operator-guide.md`. With F0051 done, the human decides whether they go.
6. S0011 (answers 11, 23) and S0012 (answer 17): `FACTORY_CLAUDE_HOME` keeps its name and now names `factory/agents`. A removed folder is checked by `git ls-files`, not by its existence. The human's steps on factory-vm (rebuild of `factory-stage:vm`, renewal of `image-id`, the installed unit and helper checked against their new sources) are recorded as the human's and cannot be verified from here.
7. Earlier tests changed: every reviewer entry lists them, each under feature decision 5, a story's Interface (the `AREAS` rows), or a named answer of the human (S0007 entry 8, S0009 entry 9, S0010 entries 9 and 14, S0011 entries 11 and 23, S0012 entry 17). I found no earlier test changed without a leave.

## 7 The slow checks

The project offers nothing beyond `make check` today, apart from `make mutants` (check 3) and the records `make duplicates` and `make areas` (both read above). In the JUnit report of my `make check`, the 10,637 tests took 1,157 s summed over the workers (130.9 s wall). The slowest are the time-limit tests at about 10 s each (`ROOMY_LIMIT`), for example `tests/machine/adapters/test_podman_timeout_status.py::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run[137-at-the-limit]` (10.1 s), `tests/watching/adapters/test_opencode_events.py::test_a_call_past_its_time_limit_ends_by_time_limit_without_measures` and `tests/shared/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_streaming-group]` (10.0 s each). Disk: at the start, `/srv/factory/vm` had 24.1 GB free and 1.4 GB used. Now it has 23.3 GB free and 1.4 GB used, and `state` and `/tmp` are at 0.0 GB used in both. All three share one pool, so the 0.8 GB less free space lies outside the instance's datasets. The stage image rebuild that S0011 asked of the human (`factory-stage:vm`) is a likely cause. A move of files cannot grow the used space, and it did not.

## 8 Cost

The 13 stories cost 139 runs, 273.8 min and $49.55. That is about $3.80 and 21 min per story, and S0013, a docs-only repair, cost $0.75. Three stories stand out:

- **S0010** ($6.94, 17 runs) is the most expensive. It had a review round 1 over italic references in the new topic files, and the coder wrote the split itself under the temporary write paths.
- **S0001** ($5.63, 13 runs) was the first move. Its coder's test changes were dropped from the take, so its first `doing` stalled. That stall gave feature decision 5 its last sentence (the tester makes all test changes first).
- **S0011** (18 runs) and **S0012** each reached the attempts cap. The take drops a renamed directory's unedited files (candidate 63), and a test checked a folder's existence where git tracks files.

The human answered 19 questions (17 questions, 2 attempts caps) and waited 2.1 h in all. S0008 needed the human most, with four answers: the placement rules for about 200 root modules (entries 4 and 23) and two rewordings of lines that detect-secrets flagged in its own journal (entries 15 and 18). S0010 and S0011 follow with three answers each.

## Proposed stories

- `backlog/F0051-S0014-the-removal-guards-look-for-a-removed-module-in-every-area.md`: the removal guards of earlier features name their modules at old layer paths that cannot exist now, so they check nothing. A shared helper looks in every area, and the guards use it (check 4). A tests-only story, which needs the human's leave in `feature.md` for the guards it changes.
- `backlog/F0051-S0015-the-setup-hints-name-the-operators-guide-topic-file.md`: `operator/vm/setup.sh`'s three hints and the skill's approving reference say "the operator guide" without the topic file that S0010 created, and the operator guide quotes those hints (checks 4 and 5).

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 2 stories proposed (F0051-S0014, F0051-S0015). `make check` was green as found. The feature's walk-through is green end to end, and no promise is broken.
   1 Scope: none. Every scope item has its merged story: the seven areas with three layers each, the layer rule blocking, `make areas` reporting outside `check`, `tests/` sorted, both guides split into files, `agents/`, `operator/vm/` and `operator/template/`. No story is outside the scope, and Out of scope holds.
   2 Smoke test: green. The package holds the seven areas, `entry` and `contract`, and the old layers cannot be imported. `make layers` is green, and `make areas` reports BROKEN, as intended. The root of `tests/` holds only `conftest.py`. The guide files exist, and `make documents` gives `documents ok`. The old folders are gone. The regenerated contract equals the committed one, and `factory-check-story` and `factory-bill` work. One script bug of mine was rerun. A stray `--help/` folder I wrote by mistake was compared (identical) and removed.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: most items are closed on `main`. The removal guards of earlier features still name their modules at old layer paths, which can no longer exist, so they now check nothing (S0014). `setup.sh`'s hints and the skill's approving reference name "the operator guide" without its file (S0015). The human's files still have old paths: the `Makefile`'s mutants example, `demo/todo-service/README.md:15,27` and the playbook's line 82. The take's directory-rename bug is already the human's candidate 63. The duplicates baseline drift is now 5 new, 3 gone.
   5 Documentation: the guides agree with the tree and with each other, and every path they name exists. The one stale part is the setup hints, which the operator guide quotes.
   6 Decisions: feature decisions 1 to 8, and the human's answers in S0007 to S0012. Among them, the coder's temporary doc write paths "for the rest of F0051 only" are still in `factory/pipeline.yml:24`, beside the old `vm/*`, `template/*` and `docs/operator-guide.md`. I found no earlier test changed without a leave.
   7 Slow checks: nothing beyond `make check`. The slowest tests are the time-limit tests at about 10 s each. Used disk is unchanged at 1.4 GB. The pool has 0.8 GB less free space, outside the instance's datasets, likely S0011's stage image rebuild.
   8 Cost: 139 runs, 273.8 min, $49.55. S0010 cost the most ($6.94, a review round over references). S0001 stalled first because the coder's test changes were dropped from the take. S0011 and S0012 reached the attempts cap through the take's directory-rename gap. The human answered 19 questions (17 questions, 2 attempts caps) and waited 2.1 h. S0008 needed the human most, with four answers: placement rules and two detect-secrets rewordings.
