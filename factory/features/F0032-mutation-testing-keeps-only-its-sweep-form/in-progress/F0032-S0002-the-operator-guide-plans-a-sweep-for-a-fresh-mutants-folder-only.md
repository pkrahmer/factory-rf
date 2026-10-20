---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 310
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T00:45:06.469893Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T00:45:06.475085Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T00:45:23.180804Z'
  stage: intake
  run: 1d563ba381564419a9c0bb21a8ca5c60
---

# The operator guide plans a sweep for a fresh `mutants/` folder only

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0032-S0001 rewrote `docs/operator-guide.md`, *Mutation testing by sweep*, for the sweep form of `make mutants`, where every run removes `mutants/` first. Two of its paragraphs still read as if `mutants/` could be kept between runs. *How long it takes* gives the fixed 165 s twice. It also keeps the per-story measurement of F0019 and F0021, and a measurement "with the stats kept in `mutants/mutmut-stats.json`" (31 mutants in 12 s), which `make mutants` can no longer produce. *A run that never gets past mutmut's stats* names a change of `[tool.mutmut]`'s test arguments or a fresh `mutants/` as the cause, and says that mutmut keeps the stats only when the run ends and that a larger `MUTANTS_SECONDS` "repairs it". Under the sweep form every run is fresh, so nothing is left to repair. A `MUTANTS_SECONDS` below the stats simply checks no mutant, and the run fails with the stop line. This story is for the human and the helpers who plan a sweep's `MUTANTS_SECONDS`. It changes only those two paragraphs. The `Makefile`, the code, the tests and the other documents stay as they are. It changes no behaviour, so it has no criterion of its own beyond the two closing ones.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The `Makefile`'s `mutants` recipe (the human's change 1 of F0032) is the reference the documenter checks against, and it stays as it is.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/operator-guide.md`, *Mutation testing by sweep*. *How long it takes* gives the cost of one run of the sweep form once: mutmut's stats (165 s on 20 cores, 4.5 to 19 minutes on two cores in the sweeps of 2026-10-19) plus 0.13 to 0.25 s per mutant on 20 cores. It no longer gives the measurement with the stats kept in `mutants/mutmut-stats.json`, and it no longer gives the per-story minutes of F0019 and F0021. *A run that never gets past mutmut's stats* says that every run starts with mutmut's stats over the whole suite in one process. It says that a `MUTANTS_SECONDS` below the stats checks no mutant, and that the run then fails with `mutants: stopped after <n> s, so the mutants it did not reach are not checked`. It says that a `MUTANTS_SECONDS` must cover the stats plus the mutants' time, and it keeps the example `make mutants MODULES=<module> MUTANTS_SECONDS=1500`. It no longer says that a larger value "repairs" a run, or that mutmut keeps the stats when a run ends. `README.md`, the project guide and `docs/decisions.md`: none, because their mutation passages already describe the fresh `mutants/` (F0032-S0001).

## Smoke test

```bash
g=docs/operator-guide.md
grep -c -F -e 'mutmut-stats.json' -e 'repairs it' -e 'keeps them only when that run ends' "$g" || true
grep -o -F '165 s' "$g" | wc -l
```
Expect: `0`, then `1` (the kept-stats wording is gone, and the guide gives the 165 s once)

```bash
g=docs/operator-guide.md
for s in 'make mutants MODULES=<module> MUTANTS_SECONDS=1500' 'mutants: stopped after' 'make mutants MODULES=factory.application MUTANTS_SECONDS=7200 MUTANTS_CHILDREN=2'; do grep -qF -e "$s" "$g" && echo found || echo "missing: $s"; done
```
Expect: three lines `found` (the example, the stop line and the sweep's command are in the guide; no command here runs `make mutants`)

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: no module under src/ changes and the tester writes no test module. The Makefile `mutants` recipe (the human's change 1 of F0032) is named as the reference. Nothing to sign, so nothing is missing.
   - Criteria: only the two closing ones exist, and the story says so on purpose. The docs criterion states each required wording and each removal. The failing sides are the removals, which the first smoke test checks: no `mutmut-stats.json`, no "repairs it", no "keeps them only when that run ends". The story states no Interface rule or comment, so no behaviour lacks a criterion.
   - Smoke test: both blocks are plain grep and shell commands, and neither runs `make mutants`. I checked the guide as it stands now. It has the "repairs it" and "keeps them only" wording at line 92, so the first block would fail today and pass after the rewrite. The example (line 95) and the sweep command (line 85) are already there. Each `Expect:` line can be checked against the output. `grep -c ... || true` prints 0 when nothing matches, which is the expected `0`.
   - Architecture: documents only, with no layer or code touched. It stays within the documenter's write paths (`docs/*`).
   - Scope: it fits F0032's goal, the documents describing the sweep form. It touches only the operator guide's two paragraphs, which F0032-S0001 left stale. Nothing from the feature's "Out of scope" is changed. It is a follow-up to S0001, proposed by the acceptance, and the human started it.
