# The documents describe the mutation report as it runs

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0024's acceptance ran `make mutants` for real, in this checkout and in a throwaway clone on a story-form branch, and read the documents against what it saw. Three passages are missing or say less than the run shows. First, the human's commit `6dacaef9` added a step to the `mutants` recipe after S0003's docs were written. When `mutants/src` exists, the step copies every file under `src/` that is not Python into it, because mutmut copies them only on its first run (the contract's schemas would otherwise be tested in their old form). `docs/project-guide/processes-and-checks.md`, *Mutation testing*, does not mention it. Second, a report that the factory kills at its time limit returns at that limit, while mutmut, which `timeout` runs in a process group of its own, goes on writing `mutants/` until the recipe's own stop. Its temporary folder stays too. Seen at the acceptance: `MakeProjectCommands.run("mutants", time_limit=3 s)` with `MUTANTS_SECONDS=60` returned `time_limit` after 3 s, and `timeout 60 uv run mutmut run ...` was still running afterwards. The documents say that the kill does not reach mutmut, but not that the next stage can start while mutmut still writes. Third, the operator guide's *How long it takes* gives a fixed 165 s per run. The acceptance measured 12 s in all for an acceptance run of 31 mutants, with mutmut's stats kept in `mutants/mutmut-stats.json`, and 439 s for a story run of 4 mutants of one module with a fresh `mutants/`, close to the 540 s stop. This story makes the three passages true. It is documentation only: the tester and the coder change nothing, and the `Makefile` stays as the human wrote it.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `docs/project-guide/processes-and-checks.md` and `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/project-guide/processes-and-checks.md`, *Mutation testing*: one sentence, in the paragraph on the recipe's temporary folder or right after it, that before each run with an existing `mutants/src` the recipe copies the other files under `src/` (every file that is not Python, outside `__pycache__`) into `mutants/src`, because mutmut copies them only on its first run, so a changed file such as a contract schema is not tested in its old form.
   - The same section, the paragraph on the stop at `MUTANTS_SECONDS`: a sentence that a report killed by the factory's time limit before the recipe's own stop returns at the limit, while mutmut goes on until its own stop and writes `mutants/` meanwhile, so the survivors a stage reads right after such a run can still change. The operator guide's *The mutation report of a story*, the `Permission denied` paragraph: the same fact in one sentence that also holds the words `goes on until its own stop`, and that the run's temporary folder under `TMPDIR` stays too.
   - `docs/operator-guide.md`, *The mutation report of a story*, *How long it takes*: after the sentence with the 165 s, the two runs measured at F0024's acceptance on 2026-10-19. With mutmut's stats kept in `mutants/mutmut-stats.json`, a run of 31 mutants of five modules took 12 s in all. With a fresh `mutants/`, a run of 4 mutants of one module took 439 s, nearly all of it mutmut's stats. And that the fixed cost is therefore small while the stats are kept and close to the 540 s stop when they are not (see *A run that never gets past mutmut's stats*).
   - No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "the other files under \`src/\`" docs/project-guide/processes-and-checks.md
```
Expect: a number of at least `1`

```bash
grep -c "mutmut-stats.json" docs/operator-guide.md; grep -c "439 s" docs/operator-guide.md
```
Expect: `1`, then `1`

```bash
grep -c "goes on until its own stop" docs/project-guide/processes-and-checks.md docs/operator-guide.md
```
Expect: `docs/project-guide/processes-and-checks.md:1` and `docs/operator-guide.md:1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
