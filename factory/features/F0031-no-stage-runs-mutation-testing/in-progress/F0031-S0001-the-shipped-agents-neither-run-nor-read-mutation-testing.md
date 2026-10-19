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
  started_at: '2026-10-19T20:50:05.454416Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T20:50:05.447263Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T20:50:05.454416Z'
  stage: intake
---

# The shipped agents neither run nor read mutation testing

## Description

On 2026-10-19 the human decided that mutation testing runs only as sweeps outside the factory (night log, `docs/runs/2026-10-12-overnight/night-log.md`, the row of 22:20). Earlier that day the `mutants` report left the coder's stage (`factory/pipeline.yml`). The shipped acceptance reviewer still runs `make mutants` in its check 3, "Mutation score", up to three times, and every acceptance of 2026-10-19 spent one to four runs of 540 s there. The shipped reviewer still has a paragraph on reading a mutation report from the coder's entry, and no stage writes that report any more. The project template still says that the feature acceptance runs `make mutants`. This story changes these texts so that no shipped agent runs or reads mutation testing. Check 3 keeps its number and becomes *Mutation testing*: the acceptance runs neither `make mutants` nor mutmut, and writes `By sweep, not run here.` under that heading. So the report keeps its eight sections, `## 1 Scope` to `## 8 Cost`. The acceptance's entry loses its `make mutants <killed>/<total>` part. The slow checks no longer name `make mutants` as a check the acceptance runs. The reviewer's paragraph goes. The template's `CLAUDE.md` and `Makefile` say that `make mutants` is for a sweep by hand, never run by a stage. These stay as they are: the `mutants` target of every `Makefile`, `python -m factory.entry.check_mutants`, `factory.domain.mutants`, every module under `src/`, the other checks, rules and lessons of both agents, and the template's `factory/pipeline.yml`. factory-rf's own `CLAUDE.md`, `factory/pipeline.yml` and the todo demo are the human's (the feature's *The human's changes*).

## Interface

No module under `src/factory/` changes. The coder changes four files under `claude/` and `template/`, each replacement exact and nothing else in those files.

`claude/agents/acceptance-reviewer.md`, the section *Role*:

- Check 3, the whole line. Old: ``3. **Mutation score.** Run `make mutants` if the project has the target, and run it again while its last line says `partial`, at most three runs in all; read the survivors (`uv run mutmut show <id>` for a few of each kind). A survivor is a line the tests would not notice breaking; group survivors by module and rule into missing acceptance criteria. When the coder entries of the archived stories carry the line of a mutation report, their reviews have read the survivors of their own modules already: say which groups those reviews passed on as notes and which are new. Report the score from the last run's last line, say whether it is partial, and give the groups.`` New:

  ```markdown
  3. **Mutation testing.** Not run here: mutation testing runs only as sweeps outside the factory. Never run `make mutants` or mutmut, whatever the project offers; write `By sweep, not run here.` under this check's heading and nothing more.
  ```

- Check 7, its first two sentences. Old: ``7. **The slow checks.** Whatever the project offers beyond `make check` and `make mutants` (an image scan, an SBOM); today usually nothing.`` New: ``7. **The slow checks.** Whatever the project offers beyond `make check` (an image scan, an SBOM), but not `make mutants` (check 3); today usually nothing.`` The rest of the line, from `Say so.` to its end, stays as it is.
- The recommendation's paragraph. Old: `` `accepted` (no finding of weight; proposed stories at most for survivors and noticed items)``. New: `` `accepted` (no finding of weight; proposed stories at most for noticed items)``.
- The proposals' paragraph. Old: `a documentation repair — not one per mutant and not one per remark.` New: `a documentation repair — not one per remark.`

`claude/agents/acceptance-reviewer.md`, the section *Stage*:

- Step 1. Old: ``Run the feature's smoke test and `make mutants` for real; paste what they printed.`` New: `Run the feature's smoke test for real; paste what it printed.`
- Step 3. Old: ``the entry `<recommendation>; <n> stories proposed; make mutants <killed>/<total>`, followed by`` New: ``the entry `<recommendation>; <n> stories proposed`, followed by``

`claude/agents/reviewer.md`, the section *Role*: the paragraph that begins ``When the coder's latest entry has the line of a mutation report (`` `mutants`: ``)`` and ends `never a pass of the mutants it did not reach.` goes, with one of the two blank lines around it. Item 6 is then followed by one blank line and the paragraph `Write findings as a numbered list in your entry: ...`.

`template/CLAUDE.md`, *Checks*, the bullet on `make lint` and `make test`. Old: ``and lists the surviving mutants: run by the feature acceptance, never part of `make check`;`` New: ``and lists the surviving mutants: for a sweep by hand, never run by a stage and never part of `make check`;``

`template/Makefile`, the comment above `FEATURE ?=`. Old: ``# `make mutants FEATURE=F0001`. Slow, so not part of `check`; the feature acceptance runs it,`` New: ``# `make mutants FEATURE=F0001`. Slow, so not part of `check`; a sweep by hand runs it, never a stage,`` The next comment line (`# and on an acceptance's branch ...`) and the recipe stay.

Unchanged: the boundary and entry sentences of both agents (`tests/shipped_agents.py`), their front matter, the acceptance reviewer's other checks (*Do the eight checks* stays, and check 7 still starts `7. **The slow checks.**` and ends with the Disk sentence that `tests/test_acceptance_reviewer_disk.py` pins), every lesson, `template/factory/pipeline.yml` (`mutants/*` stays in its `tool_paths`), and the `mutants` recipe of `template/Makefile`.

Tests (the tester writes them): `tests/test_claude_agent_texts_mutants.py` is rewritten, and `TEMPLATE_RULES_LINES` of `tests/test_claude_files.py` takes the new template sentence. Both are earlier tests changed under the leave of the feature's decision 7. `tests/test_claude_agent_texts.py`, `tests/test_acceptance_reviewer_disk.py` and `tests/test_template_makefile.py` pass unchanged.

## Acceptance criteria

1. The acceptance reviewer's new texts (rows of one parametrized test, each text in the named section of `agent_body("acceptance-reviewer")` through `section_text`). In *Role*: the whole new line of check 3, and ``7. **The slow checks.** Whatever the project offers beyond `make check` (an image scan, an SBOM), but not `make mutants` (check 3); today usually nothing. Say so.``, and ``(no finding of weight; proposed stories at most for noticed items)``, and `a documentation repair — not one per remark.` In *Stage*: `Run the feature's smoke test for real; paste what it printed.` and ``the entry `<recommendation>; <n> stories proposed`, followed by the eight findings in short``.
2. The acceptance reviewer's old texts are gone and check 3 is there once (rows of one parametrized test, a count over `agent_body("acceptance-reviewer")`). Each of these occurs 0 times: `3. **Mutation score.**`, ``Run `make mutants` if the project has the target``, ``and `make mutants` for real``, `make mutants <killed>/<total>`, `mutmut show`, `one per mutant`, `for survivors`. `3. **Mutation testing.**` occurs exactly once, and the line that starts with it is the third of the numbered checks: the line after it starts `4. **What the stories noticed.**`.
3. The reviewer neither runs nor reads mutation testing (rows of one parametrized test over `agent_body("reviewer")`, lowercased): `mutant`, `mutmut` and `mutation` each occur 0 times. The line `6. **Earlier tests**: ...` is followed by one blank line and then the line that starts `Write findings as a numbered list in your entry`.
4. The template's texts: `test_template_rules_file_is_the_python_project_text` of `tests/test_claude_files.py` passes with `TEMPLATE_RULES_LINES` holding ``and lists the surviving mutants: for a sweep by hand, never run by a stage and never part of `make check`;`` where it held ``run by the feature acceptance, never part of `make check`;``, and the rest of its lines unchanged. One test reads `template/Makefile`: the line ``# `make mutants FEATURE=F0001`. Slow, so not part of `check`; a sweep by hand runs it, never a stage,`` occurs once, and `the feature acceptance runs it` occurs 0 times.
5. Unchanged texts still hold: `tests/test_claude_agent_texts.py` (*Do the eight checks* among its anchors), `tests/test_acceptance_reviewer_disk.py`, `tests/test_claude_agent_texts_review_leave.py`, `tests/test_template_makefile.py` and the rest of `tests/test_claude_files.py` pass unchanged.
6. `make check` stays green.
7. docs: `docs/operator-guide.md`. The section *The mutation report of a story* becomes *Mutation testing by sweep*. It says that no stage and no agent runs `make mutants`: mutation testing runs only as sweeps outside the factory, which the human starts on a fresh copy in a throwaway container, with `mutants/` made anew for every run (the human's decision of 2026-10-19). The `mutants` target and `python -m factory.entry.check_mutants` stay for those sweeps, a coder's entry has no `mutants` line, and the acceptance's check 3 says `By sweep, not run here.` *How long it takes* keeps its measures. Its sentences on the stories that end `partial`, on the reviewer and on the acceptance go. It gains the runs measured at F0024's acceptance on 2026-10-19: with a fresh `mutants/`, a run of 4 mutants of one module took 439 s, nearly all of it mutmut's stats; with the stats kept in `mutants/mutmut-stats.json`, a run of 31 mutants took 12 s. So a sweep, which starts with a fresh `mutants/`, pays the stats every time. *What the reviewer does*, *What the acceptance does* and the `Permission denied` paragraph with its repair go: no factory user writes `mutants/` any more. *A run that never gets past mutmut's stats* stays. *What a stage run shows*, item 3: the paragraph that begins ``The `mutants` report of a story`` goes; the example of a report stopped at its time limit stays, as the form of such a line. `docs/project-guide/processes-and-checks.md`, *Mutation testing*. Its first paragraph says that no stage runs the target and sweeps do, and the two forms (a story's branch, `FEATURE=<id>`) stay as what the target takes. The paragraph on the stop at `MUTANTS_SECONDS` keeps the recipe's own stop and `--stopped-after 540`. Its sentences on the agent's shell tool, the report's `time_limit` and the factory's KILL of the report go. The paragraph on the `EXIT` trap no longer gives the factory's report and the agents' runs as the reason for `chmod -R g+w mutants`, and no longer points to the operator guide's repair. One sentence is added there: before each run with an existing `mutants/src`, the recipe copies the other files under `src/` (every file that is not Python, outside `__pycache__`) into `mutants/src`, because mutmut copies them only on its first run, so a changed contract schema is not tested in its old form. `docs/project-guide/agents.md`, the bullet on `template/Makefile`: ``mutants` is run by the feature acceptance`` becomes that `mutants` is for a sweep by hand and never run by a stage. `docs/decisions.md`: an entry *Mutation testing runs only as sweeps outside the factory*, dated with the story, the human's decision of 2026-10-19, which supersedes *Mutation testing per story*. Reasons: every acceptance of 2026-10-19 ran `make mutants` one to four times at up to 540 s each, and every large feature still ended partial (F0019 to F0023). A sweep in idle time, on a fresh copy, needs neither a stage's time limit nor `mutants/` shared by two users. Rejected: a longer limit for the acceptance; the report after the coder (taken out the same day); check 3 dropped and the checks renumbered, because the eight sections, check 7's pinned start and the reports already written keep their numbers. *Mutation testing per story* gets a line naming the new entry. `README.md`: none, it does not name mutation testing.

## Smoke test

```bash
grep -c -F -e '3. **Mutation testing.** Not run here' -e 'beyond `make check` (an image scan, an SBOM), but not `make mutants` (check 3)' -e "Run the feature's smoke test for real; paste what it printed." -e 'the entry `<recommendation>; <n> stories proposed`, followed by' claude/agents/acceptance-reviewer.md
```
Expect: `4` (check 3, check 7, step 1 and step 3 each hold their new text)

```bash
grep -c -F -e 'Mutation score' -e 'make mutants <killed>/<total>' -e 'mutmut show' -e 'one per mutant' -e 'for survivors' claude/agents/acceptance-reviewer.md || true
grep -c -i -e mutant -e mutmut -e mutation claude/agents/reviewer.md || true
grep -c -F -e 'run by the feature acceptance' -e 'the feature acceptance runs it' template/CLAUDE.md template/Makefile || true
```
Expect: four lines, `0`, `0`, `template/CLAUDE.md:0`, `template/Makefile:0` (no old text is left in the shipped agents or the template)

```bash
grep -c -F 'for a sweep by hand, never run by a stage and never part of `make check`' template/CLAUDE.md
```
Expect: `1`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
