---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-20T00:16:58.421375Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T00:16:58.415666Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T00:16:58.421375Z'
  stage: intake
---

# The mutation report command is removed and the documents describe the sweep form of `make mutants`

## Description

On 2026-10-19 the human decided that mutation testing runs only as sweeps outside the factory, with `mutants/` made anew for every run (night log, `docs/runs/2026-10-12-overnight/night-log.md`, the row of 22:20). The human's change 1 of this feature rewrites the `Makefile`'s `mutants` recipe into its sweep form before this story starts. Every run removes `mutants/` first. The modules come from `MODULES` given by hand or from `FEATURE`, and an optional `MUTANTS_SECONDS` and `MUTANTS_CHILDREN` set the stop and the workers. The run ends with mutmut's own listing of the mutants it did not kill. The recipe no longer calls `python -m factory.entry.check_mutants`. That command and its rules, `factory.domain.mutants` (F0024-S0001), filtered the survivors of earlier runs out of a kept `mutants/`, named the mutants still to run in it, and marked a run `partial` for the factory's report. A fresh `mutants/` leaves none of those jobs, and no stage and no sweep calls the command. This story removes the two modules and their tests, and makes the documents describe the sweep form. These stay as they are: `factory.entry.inputs`, which `check_duplicates` uses, and its tests; `[tool.mutmut]`; `command_line`'s suffix for a command stopped at its time limit; the template's and the demo's `mutants` recipes; and every other module under `src/`.

## Interface

The coder removes two modules and changes nothing else under `src/factory/`:

- `src/factory/entry/check_mutants.py` (`entry`): removed whole.
- `src/factory/domain/mutants.py` (`domain`): removed whole, with `MutantStatus`, `MutantName`, `MutantResult`, `MutationReport`, `parse_results`, `mutation_report` and `rerun_names`.
- Unchanged: `src/factory/entry/inputs.py` (`read_input`, `UnreadableInput`) and `src/factory/entry/check_duplicates.py`, which imports both from it. No other module imports either removed module.

Tests (the tester writes them):

- `tests/entry/test_check_mutants.py` and `tests/domain/test_mutants.py` (F0024-S0001) are removed whole, under the leave of the feature's decision 9.
- `tests/entry/test_mutation_report_removed.py` (new): one parametrized test over `importlib.util.find_spec`. It reads no source file, so `[tool.mutmut]` needs no new deselected test.
- Unchanged, and they must pass: `tests/entry/test_inputs.py`, `tests/entry/test_check_duplicates.py`, `tests/domain/test_command_line_time_limit.py`, `tests/application/test_stage_time_limited_report.py`, `tests/test_template_makefile.py` and `tests/test_claude_agent_texts_mutants.py`.

## Acceptance criteria

1. The report command and its rules are gone, and the shared reader stays (rows of one parametrized test, each a module name and whether `importlib.util.find_spec(name)` finds it): `factory.entry.check_mutants`, not found (`None`); `factory.domain.mutants`, not found; `factory.entry.inputs`, found; `factory.entry.check_duplicates`, found.
2. The earlier tests named in the Interface as unchanged pass with their names and their checks as they are, and `tests/entry/test_check_mutants.py` and `tests/domain/test_mutants.py` no longer exist.
3. `make check` stays green.
4. docs: `docs/project-guide/processes-and-checks.md`, *Mutation testing*, as F0031 left it, is rewritten for the sweep form, in the `Makefile`'s own terms. No stage and no agent runs `make mutants`, and sweeps do. Every run removes `mutants/` first, so mutmut makes it anew, copies the other files under `src/` afresh and runs its stats again; nothing is kept between runs. The modules come from `MODULES` (dotted modules or packages, each run by its pattern `<name>.*`, for example `MODULES='factory.domain.disk factory.application'`) or from `FEATURE=<id>` (the modules the feature's story commits on `origin/main` changed, which needs a checkout with its history). `MODULES` wins when both are given. With neither, it prints `mutants: set MODULES or FEATURE, as in make mutants MODULES=factory.domain.disk or make mutants FEATURE=F0012` and fails; with no module changed by the feature, it prints `mutants: no module under src/factory changed by <id>` and exits 0. `MUTANTS_SECONDS` stops mutmut by `timeout` after that many seconds (no stop when unset), and the run then fails with `mutants: stopped after <n> s, so the mutants it did not reach are not checked`. `MUTANTS_CHILDREN` passes `--max-children`, because mutmut's default is every core the machine reports, also in a container limited to fewer. The recipe keeps its own `TMPDIR` from `mktemp -d`, its `EXIT` trap that removes that folder, and `umask 022`. It ends with `uv run mutmut results` without the `not checked` lines, which then lists only this run's mutants that mutmut did not kill (and none that a stop left unreached). To read one survivor: `uv run mutmut show <name>`. The story-branch form, the `--names` rerun, the reason of the two users of one group for `chmod -R g+w mutants`, the removal of `.git` folders, the copy into an existing `mutants/src`, and "`mutants/` holds the latest run of each module" go. The subsection *The report of a mutation run* goes whole. `docs/project-guide/README.md`, the index line of `processes-and-checks.md`, no longer names `factory.domain.mutants`, `factory.entry.check_mutants` or *The report of a mutation run*, and still names `factory.entry.inputs`. `docs/operator-guide.md`, *Mutation testing by sweep* (F0031's): the target stays for the sweeps, and `check_mutants` is no longer named there. It gives a sweep's command, `make mutants MODULES=factory.application MUTANTS_SECONDS=7200 MUTANTS_CHILDREN=2`, and says that every run pays mutmut's stats: 165 s on 20 cores; 4.5 to 19 minutes on two cores in the sweeps of 2026-10-19. *How long it takes* no longer says that the recipe stops mutmut after 540 s or that the largest runs end `partial`. *A run that never gets past mutmut's stats* says that a `MUTANTS_SECONDS` below the stats checks no mutant, and its example `make mutants MUTANTS_SECONDS=1500` gains `MODULES=<module>`. After the story, neither `docs/operator-guide.md` nor `docs/project-guide/` names `check_mutants` or `factory.domain.mutants`. `docs/decisions.md`: an entry *The mutants target keeps only its sweep form*, dated with the story, from the feature's decisions 1 to 7. Its decisions are a fresh `mutants/` by `rm -rf mutants`, `MODULES` or `FEATURE`, no stop unless asked, `MUTANTS_CHILDREN`, and the report command removed with `factory.entry.inputs` kept. Its reasons are the human's decisions of 2026-10-19 and that a fresh `mutants/` leaves the command no job. It rejects keeping `check_mutants` for its summary line, refusing a run while `mutants/` exists, and 540 s as the default stop. *A mutation run's report is a line of its own, and a partial run is never complete*, *make mutants runs under a temporary root of its own* and *Mutation testing runs only as sweeps outside the factory* (whose decision says that `factory.entry.check_mutants` stays for the sweeps) each get a line naming the new entry. `README.md`: none, it does not name mutation testing.

## Smoke test

```bash
uv run -q python -c "import importlib.util as u; print([u.find_spec(m) is None for m in ('factory.entry.check_mutants', 'factory.domain.mutants', 'factory.entry.inputs')])"
```
Expect: `[True, True, False]` (the two modules are gone, the shared reader stays)

```bash
ls src/factory/entry/check_mutants.py src/factory/domain/mutants.py tests/entry/test_check_mutants.py tests/domain/test_mutants.py 2>&1 | grep -c 'No such file'
grep -c -F -e check_mutants -e factory.domain.mutants docs/operator-guide.md docs/project-guide/processes-and-checks.md docs/project-guide/README.md Makefile CLAUDE.md || true
```
Expect: `4`, then five lines, `docs/operator-guide.md:0`, `docs/project-guide/processes-and-checks.md:0`, `docs/project-guide/README.md:0`, `Makefile:0`, `CLAUDE.md:0`

```bash
p=docs/project-guide/processes-and-checks.md
for s in 'mutants: set MODULES or FEATURE' 'mutants: stopped after' 'MUTANTS_CHILDREN' 'uv run mutmut show'; do grep -qF -e "$s" "$p" && echo found || echo "missing: $s"; done
grep -qF 'make mutants MODULES=factory.application MUTANTS_SECONDS=7200 MUTANTS_CHILDREN=2' docs/operator-guide.md && echo found || echo 'missing: the sweep command'
grep -c -F 'The report of a mutation run' "$p" docs/project-guide/README.md || true
```
Expect: five lines `found`, then two lines, `docs/project-guide/processes-and-checks.md:0` and `docs/project-guide/README.md:0` (the guide describes the sweep form, the operator guide gives the sweep's command, and the report's subsection is gone; no command here runs `make mutants`)

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
