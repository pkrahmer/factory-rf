---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 286
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-19T21:00:20.059729Z'
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
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T20:50:27.935593Z'
  stage: intake
  run: 6dedcc08f3dc416a855ead9a8ad44429
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T20:50:48.736600Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T20:53:24.236936Z'
  stage: tests
  run: 980123cff2644e24ba046a9ecdcb0181
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T20:53:45.980015Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T20:56:13.755388Z'
  stage: doing
  run: 31ef9302986d4f93a6e31131d13aaf75
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T20:56:35.011750Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T20:57:03.904444Z'
  stage: review
  run: 524c2a0cc4dd485b8e802f1836f3346d
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T20:57:24.472810Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-19T20:57:38.230068Z'
  stage: doing
  run: 3ffd636478c14af4b2e9487a1d9744fd
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T20:57:58.897017Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-19T20:59:59.343504Z'
  stage: tests
  run: 30993873f9b648aab5f3122338dd9c25
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T21:00:20.059729Z'
  stage: doing
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
3. intake: accepted
   - Interface: no module under `src/` changes. It names four exact files (`claude/agents/acceptance-reviewer.md`, `claude/agents/reviewer.md`, `template/CLAUDE.md`, `template/Makefile`) and gives the old and new text of every passage. I found the old passages in the acceptance reviewer: check 7 is on line 59, step 1 on line 72 and step 3 on line 74. The template's Makefile still has the old comment line.
   - Criteria: each is testable by a parametrized text-presence or text-count test. The rules have both sides. The new texts are present (1), the old texts occur 0 times and check 3 occurs once as the third numbered check (2), and the reviewer holds no `mutant`, `mutmut` or `mutation` plus the blank-line layout (3). The template's CLAUDE.md line and Makefile line are present once, and the old wording is gone (4). The unchanged tests still pass (5). Every behaviour in the Interface comments has a criterion. The changes to existing tests carry the human's leave under the feature's decision 7.
   - Smoke test: the commands are runnable greps. I checked the first one: its four patterns sit on four separate lines (check 3, check 7, step 1, step 3), so `4` is right. The second block's four expected lines (`0`, `0`, `template/CLAUDE.md:0`, `template/Makefile:0`) match grep -c output for two files. Each `Expect:` line can be checked against the output.
   - Architecture: only shipped agent texts and template files change, in `claude/` and `template/`. Those are the coder's write paths and the tests are the tester's. No layer, dependency or suppression marker is involved.
   - Scope: it is within the feature's Scope. It leaves alone the Out-of-scope items (the `mutants` target, `src/`, the pipeline files and the todo demo). The pipeline file and the demo changes stay the human's, as the feature says.
4. factory: started tests as self.
5. tester: Wrote the tests for the shipped agents' and the template's mutation-testing texts. The tests are red on purpose until the coder changes the four files under `claude/` and `template/`.

   - criterion 1: tests/test_claude_agent_texts_mutants.py::test_acceptance_reviewer_leaves_mutation_testing_to_sweeps (rows check-3, check-7, recommendation, proposals in *Role*; step-1, step-3 in *Stage*, through `section_text(agent_body("acceptance-reviewer"), ...)`)
   - criterion 2: tests/test_claude_agent_texts_mutants.py::test_acceptance_reviewer_holds_no_old_mutation_text (seven old texts 0 times, `3. **Mutation testing.**` once) and tests/test_claude_agent_texts_mutants.py::test_acceptance_reviewer_mutation_testing_is_the_third_check (the next line starts `4. **What the stories noticed.**`)
   - criterion 3: tests/test_claude_agent_texts_mutants.py::test_reviewer_names_no_mutation_testing (rows mutant, mutmut, mutation over the lowercased body) and tests/test_claude_agent_texts_mutants.py::test_reviewer_item_6_is_followed_by_the_findings_paragraph (one blank line, then `Write findings as a numbered list in your entry`)
   - criterion 4: tests/test_claude_files.py::test_template_rules_file_is_the_python_project_text (`TEMPLATE_RULES_LINES` now holds the new template sentence) and tests/test_claude_agent_texts_mutants.py::test_template_makefile_leaves_mutants_to_a_sweep_by_hand (rows: the new comment line occurs once, `the feature acceptance runs it` occurs 0 times)
   - criterion 5: no new test. tests/test_claude_agent_texts.py, tests/test_acceptance_reviewer_disk.py, tests/test_claude_agent_texts_review_leave.py, tests/test_template_makefile.py and the rest of tests/test_claude_files.py are left as they were.
   - criterion 6: `make check`, which the factory runs. criterion 7 is the docs stage's work.

   Files: I created no new file.
   - I rewrote `tests/test_claude_agent_texts_mutants.py`, an earlier test, as the story says. The old tests there pinned the texts that this story removes, so they are replaced by the tests above.
   - I changed `TEMPLATE_RULES_LINES` in `tests/test_claude_files.py`, an earlier test. Only the string pieces that hold the sentence changed. The joined text is otherwise the same as before; the literal pieces after it are split differently only to keep lines within 100 characters.
   - Both earlier files were changed under the leave of the feature's decision 7, which the story names.

   Import failures: none. No module under `src/` is involved, so every test module was collected.

   `make test` (one run) fails only in the new and changed tests. The texts are still the old ones, so the tail showed, among others, `test_reviewer_item_6_is_followed_by_the_findings_paragraph`, both rows of `test_template_makefile_leaves_mutants_to_a_sweep_by_hand` and `test_template_rules_file_is_the_python_project_text`. `make lint` is green.

   Open: nothing.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/test_claude_files.py::test_template_rules_file_is_the_python_project_text
6. factory: started doing as self.
7. coder: Replaced the mutation-testing texts in the four shipped files named by the Interface. Each replacement is the exact old/new pair from the Interface, and nothing else in those files changed.
   - `claude/agents/acceptance-reviewer.md`: in *Role*, check 3 is now *Mutation testing* ("By sweep, not run here."). Check 7 now starts "beyond `make check` (...), but not `make mutants` (check 3)", and the rest of that line is unchanged. The recommendation no longer names survivors, and the proposals no longer say "one per mutant". In *Stage*, step 1 no longer runs `make mutants`, and step 3's entry no longer has the `make mutants <killed>/<total>` part.
   - `claude/agents/reviewer.md`: removed the mutation-report paragraph together with one of its blank lines. Item 6 is now followed by one blank line and then the findings paragraph.
   - `template/CLAUDE.md`: the `make mutants` sentence now says "for a sweep by hand, never run by a stage and never part of `make check`".
   - `template/Makefile`: the comment above `FEATURE ?=` now says "a sweep by hand runs it, never a stage,". The next comment line and the recipe are unchanged.

   Main choice: I made the replacements with a throwaway script that asserts each old text occurs exactly once before it replaces it. That way no partial or doubled edit could slip through. I rejected hand-editing the very long lines with Edit, because exact matching on them is fragile.

   Refactor: nothing to change. The diff only swaps text.

   Checks: `make check` is green (coverage 99.12 %). All three smoke-test blocks print what they expect: `4`; `0`, `0`, `template/CLAUDE.md:0`, `template/Makefile:0`; and `1`.

   Seen but not touched: line 4 of `template/Makefile` still calls `duplicates` and `mutants` "reports outside `check`". The Interface keeps that line, and it is still true, but the word "reports" reads more like a stage report than a sweep. That could be a later wording story. The docs criterion (7) is the documenter's.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: Findings:

   1. `tests/test_claude_agent_texts_mutants.py:1`: the module docstring goes beyond the leave this file was changed under. Decision 7 of `feature.md` says the tester makes exactly the listed changes and nothing else, and it sets the docstring to `"""No shipped agent runs or reads mutation testing; the acceptance's check 3 says it is done by sweep."""`. The tester wrote `"""No shipped agent runs or reads mutation testing; the template leaves it to a sweep by hand."""` instead. Fix: the tester sets the docstring to decision 7's exact text. The coder hands this on with `tests`. If the human prefers the tester's wording because the module now also holds the Makefile test, that is the human's call to make in an answer.

   Everything else checked clean:
   - The four files under `claude/` and `template/` match the Interface's old and new pairs exactly. The reviewer's paragraph is gone with one of its blank lines, and check 7's rest and the Disk sentence are unchanged.
   - Criteria 1 to 4 each have a test that checks what the criterion names. Every count has a 0 row and a once row, and the sides are rows of parametrized tests.
   - The coder's journal reports the factory's `make check` as green.
   - No module under `src/` changed and there are no suppression markers, so architecture and security are clean.

   Earlier tests:
   - `tests/test_claude_agent_texts_mutants.py`: the human's leave, decision 7 of the feature, which the story names (rewritten; see finding 1 for the docstring that goes beyond it).
   - `tests/test_claude_files.py`: the human's leave, decision 7 of the feature, which the story names. Only `TEMPLATE_RULES_LINES` changed: the sentence was replaced and the strings around it were wrapped again, and every other line and test is as it was.
10. factory: started doing as self.
11. coder: Round 1: the reviewer's only finding is about a test, so I changed no code. I'm passing it to the tester.

    - Test change: in `tests/test_claude_agent_texts_mutants.py`, line 1, set the module docstring to decision 7's exact text: `"""No shipped agent runs or reads mutation testing; the acceptance's check 3 says it is done by sweep."""`. It currently reads `"""No shipped agent runs or reads mutation testing; the template leaves it to a sweep by hand."""`. Nothing else in that file changes.
    - Code: the four files under `claude/` and `template/` stay as they were in entry 7. The reviewer found that they match the Interface exactly. No refactor was needed, and no other file changed.
    - Choice: I'm handing the change on with `tests` rather than raising a question. The reviewer's finding names decision 7's exact text, so nothing is left to decide unless the human prefers the tester's wording. The reviewer left that call to the human, and I have no reason to ask for it.
    - Noticed, not touched: what I reported in entry 7 still holds. Line 4 of `template/Makefile` calls `duplicates` and `mutants` "reports outside `check`", which could be a later wording story.
12. factory: started tests as self.
13. tester: Made the approved test change from coder entry 11 (reviewer finding 1, decision 7 of the feature). I changed only the module docstring of `tests/test_claude_agent_texts_mutants.py`.
    - Old: `"""No shipped agent runs or reads mutation testing; the template leaves it to a sweep by hand."""`
    - New: `"""No shipped agent runs or reads mutation testing; the acceptance's check 3 says it is done by sweep."""`

    On one line, the exact text is 105 characters, and `make lint` failed with E501 (line limit 100). So I split the source line inside the docstring with a backslash line continuation after `testing; `. The docstring's value is still decision 7's exact text on one line; I checked it with `ast.get_docstring`. I rejected two other fixes:
    - a `# noqa: E501` marker, because it would be a suppression;
    - a summary line plus a body, because it would change the text.

    Nothing else in the file changed. No other test file changed.

    Criterion mapping is unchanged from entry 5:
    - criterion 1: tests/test_claude_agent_texts_mutants.py::test_acceptance_reviewer_leaves_mutation_testing_to_sweeps
    - criterion 2: tests/test_claude_agent_texts_mutants.py::test_acceptance_reviewer_holds_no_old_mutation_text and ::test_acceptance_reviewer_mutation_testing_is_the_third_check
    - criterion 3: tests/test_claude_agent_texts_mutants.py::test_reviewer_names_no_mutation_testing and ::test_reviewer_item_6_is_followed_by_the_findings_paragraph
    - criterion 4: tests/test_claude_files.py::test_template_rules_file_is_the_python_project_text and tests/test_claude_agent_texts_mutants.py::test_template_makefile_leaves_mutants_to_a_sweep_by_hand
    - criterion 5: the unchanged earlier tests

    Files created: none. Earlier file changed: tests/test_claude_agent_texts_mutants.py, under decision 7's leave as the coder's entry passed it on. Import failures: none.

    Checks:
    - `make test`, run once before the line split: test: green (45.5 s), coverage 99.12 %.
    - `make lint` after the split: green.

    `lint`: lint: green (0.0 s)
    `test`: test: green (44.2 s)
14. factory: started doing as self.
