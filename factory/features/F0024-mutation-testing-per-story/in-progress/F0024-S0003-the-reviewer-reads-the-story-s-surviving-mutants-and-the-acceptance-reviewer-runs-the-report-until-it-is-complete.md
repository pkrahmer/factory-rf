---
stage: smoke-test
blocked: null
round: 0
attempts: 1
crashes: 0
pull_request: 272
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-19T16:44:05.985233Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T16:35:34.963938Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T16:35:34.971046Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T16:36:00.543746Z'
  stage: intake
  run: 4b5ee6a1361b49d38646f03253a710da
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T16:36:21.320217Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T16:38:18.286387Z'
  stage: tests
  run: 1e49b017accd4bbeac1aa4412eeb5a29
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T16:38:39.080881Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T16:40:39.182990Z'
  stage: doing
  run: 1e40c42d66bd4a0d989673bd01590c10
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T16:40:59.688554Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T16:41:30.123393Z'
  stage: review
  run: ad0d652d967c4397930e691f2279d959
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T16:41:50.714028Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T16:42:54.656436Z'
  stage: docs
  run: bc21f9430fe24ac1b5a6068635d85a26
- number: 12
  speaker: factory
  kind: stall
  at: '2026-10-19T16:42:54.683251Z'
  stage: docs
  run: bc21f9430fe24ac1b5a6068635d85a26
  reason: check_red
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-19T16:43:17.962858Z'
  stage: docs
- number: 14
  speaker: documenter
  kind: result
  at: '2026-10-19T16:43:45.108230Z'
  stage: docs
  run: 09c8447f091840b9834071fc89321250
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-19T16:44:05.985233Z'
  stage: smoke-test
---

# The reviewer reads the story's surviving mutants, and the acceptance reviewer runs the report until it is complete

## Description

With the feature's changes, the factory runs `make mutants` as a report after the coder. The coder's entry then ends with a line such as `` `mutants`: mutants: 1653 killed, 65 survived, ... ``, and the survivors of the story's modules stay in `mutants/` in the checkout. Nobody reads them yet: the reviewer's text says nothing of a mutation report, and the acceptance reviewer's text runs `make mutants` once. This story changes the two shipped agent texts. The reviewer reads the survived and timed-out mutants of the modules the diff changed, in the way the project's `CLAUDE.md` names. A survivor in a line the diff added or changed that breaks a rule the work item states is a finding under item 1, so the tester adds the test while the story is open. An equivalent survivor, a changed message text, a line the diff did not change, and a `partial` line are notes for the feature's acceptance. The reviewer never runs the report itself. The acceptance reviewer runs `make mutants` again while its last line says `partial`, at most three runs in all, reports the score of the last line and whether it is partial, and tells the survivors the stories' reviews passed on from new ones. Both texts stay true for a project whose `mutants` target is still the feature-level one, or that has none. The `Makefile` and `CLAUDE.md` lines the reviewer relies on are the human's change 1, which comes before this story.

## Interface

`claude/agents/reviewer.md` (the coder writes it), section `## Role`: right after the checklist's item 6, and before the paragraph that begins `Write findings as a numbered list in your entry`, one new paragraph, exactly:

```markdown
When the coder's latest entry has the line of a mutation report (`` `mutants`: ``), read the survived and timed-out mutants of the modules the diff changed as part of item 1, listing and showing them as the project's `CLAUDE.md` says; do not run the report yourself, the factory ran it after the coder. A survivor in a line the diff added or changed, whose change breaks a rule the work item states, is a finding under item 1: name the mutant, the rule, and the test that would notice it. A survivor that changes no behaviour, changes only a message text, or sits in a line the diff did not change is a note, at any round: one line per group under `Notes:`, for the feature's acceptance. A report line that says `partial`, or that the factory stopped the report at its time limit, is a note too, never a pass of the mutants it did not reach.
```

`claude/agents/acceptance-reviewer.md` (the coder writes it), section `## Role`, check 3: the item that begins `3. **Mutation score.**` becomes exactly:

```markdown
3. **Mutation score.** Run `make mutants` if the project has the target, and run it again while its last line says `partial`, at most three runs in all; read the survivors (`uv run mutmut show <id>` for a few of each kind). A survivor is a line the tests would not notice breaking; group survivors by module and rule into missing acceptance criteria. When the coder entries of the archived stories carry the line of a mutation report, their reviews have read the survivors of their own modules already: say which groups those reviews passed on as notes and which are new. Report the score from the last run's last line, say whether it is partial, and give the groups.
```

- No other line of the two files changes. The `## Lessons` sections stay exactly as `tests/test_claude_agent_texts.py` pins them, every anchor that test names for the two roles stays, and no new text uses a word that test bans.

`docs/operator-guide.md`, `docs/project-guide/processes-and-checks.md` and `docs/decisions.md` (the documenter writes them, from the docs criterion).

Test module (new): `tests/test_claude_agent_texts_mutants.py`, reading the bodies through `agent_body` of `tests/shipped_agents.py` and the sections through `section_text` of `factory.domain.sections`. No earlier test changes.

## Acceptance criteria

1. Rows of one parametrized test, each a text that the body of an agent holds in its `Role` section (`section_text`): the reviewer's new paragraph, and the acceptance reviewer's new check 3, each exactly as the Interface gives it.
2. The reviewer's new paragraph comes after the line that begins `6. **Earlier tests**:` and before the paragraph that begins `Write findings as a numbered list in your entry` (one test on the positions in the body).
3. The acceptance reviewer's body no longer holds ``Run `make mutants` if the project has the target; read the survivors``, and holds `3. **Mutation score.**` exactly once (rows of one parametrized test).
4. Every test of `tests/test_claude_agent_texts.py` passes unchanged, the lessons, the anchors and the banned words of the reviewer and the acceptance reviewer included.
5. `make check` stays green.
6. docs:
   - `docs/project-guide/processes-and-checks.md`, *Mutation testing*: the section rewritten for the human's `mutants` recipe. On a story's branch it takes the modules the branch changes against `origin/main`, the work tree included, and runs all their mutants. With `FEATURE` or on an acceptance's branch it runs by name only the mutants of the feature's modules that are not killed, and a module with no mutant yet by its pattern. Then: why (mutmut 3.8 runs again every mutant a name selects, so a stopped story's run starts over and each acceptance run shortens its list), the 540 s stop inside the report's 10 minutes, the last line from `check_mutants` with its exit statuses, the `EXIT` trap's `chmod -R g+w mutants`, and how to list and show the survivors of one module.
   - `docs/operator-guide.md`, *What a stage run shows*, point 3: the coder's `mutants` line with an example, complete and partial, and that a partial one is a failed report that never stalls the stage. A new subsection of *The project's make targets*, with the heading line exactly `### The mutation report of a story`: the time it takes (a fixed 165 s plus 0.13 to 0.25 s per mutant, measured on 2026-10-19: 3 to 11.5 minutes of mutmut for factory-rf's stories, so the recipe's stop after 540 s ends the largest of them `partial`, about four in twelve), what the reviewer does with the survivors, and what the acceptance re-runs. It also says that after a change of `[tool.mutmut]`'s test arguments, or with a fresh `mutants/`, the first run spends its time on mutmut's stats over the whole suite, and that one run by hand with a larger `MUTANTS_SECONDS` while the factory is idle repairs a run that never gets past them. It also gives the repair when the line reads `Permission denied`: `docker exec -u root <container> chmod -R g+w /work/checkout/mutants` (`podman exec` under Podman).
   - `docs/decisions.md`: an entry *Mutation testing per story*, dated with the story, superseding *Mutation testing is limited to one feature's modules*, with the feature's decisions 1, 2, 4 to 7 and 13 and the rejected alternatives: running only the changed functions, every unchecked mutant of the package, a longer lease, the report's whole output in the journal, and a gentler stop in the process module.

## Smoke test

```bash
grep -c 'When the coder.s latest entry has the line of a mutation report' claude/agents/reviewer.md
grep -c 'A report line that says `partial`, or that the factory stopped the report at its time limit, is a note too, never a pass of the mutants it did not reach.' claude/agents/reviewer.md
grep -c 'and run it again while its last line says `partial`, at most three runs in all' claude/agents/acceptance-reviewer.md
grep -c 'Report the score from the last run.s last line, say whether it is partial, and give the groups.' claude/agents/acceptance-reviewer.md
grep -cx '### The mutation report of a story' docs/operator-guide.md
```

Expect: five lines, each `1`.

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names concrete files and sections. The reviewer's `## Role` gets the new paragraph between item 6 (line 60) and `Write findings as a numbered list` (line 62). The acceptance reviewer's check 3 (line 55) is replaced. Both give the exact text, and the test module and its helpers (`agent_body`, `section_text`) are named. I read the new texts against the banned-word regex in `tests/test_claude_agent_texts.py` and found none of its words.
   - Criteria: criterion 1 pins both texts exactly. Criterion 2 pins the reviewer paragraph's position. Criterion 3 pins both sides of the old and new acceptance-reviewer text: the old sentence is absent and the new heading appears once. Criterion 4 covers the existing lessons, anchors and banned words. Every behaviour the Interface comments state (the finding rule, the notes at any round, partial as a note, at most three runs, the score and partial report) sits in the exact text, which criterion 1 pins. The failing side is covered by the notes sentence and by the old-text-absent row. Each criterion is one test function. The docs criterion is the documenter's.
   - Smoke test: five grep commands, runnable from the repo root, each with a `Expect:` of five lines of `1`. Two use `.` for an apostrophe, which matches. They are checkable against the files.
   - Architecture: the change touches only the shipped agent texts (coder write path `claude/*`) and a new test at the `tests/` root, which is right for a module outside the layers. It adds no source module and no layer change.
   - Scope: it matches the feature's Scope (S0003: the two agent files, a test module, docs) and decisions 6 and 11. Nothing in "Out of scope" is touched, and no earlier test changes. The Makefile and CLAUDE.md lines it relies on are the human's change 1.
4. factory: started tests as self.
5. tester: I wrote the tests for criteria 1 to 3 in one new module. Criterion 4 is covered by the existing tests, which I left unchanged.

   - criterion 1: tests/test_claude_agent_texts_mutants.py::test_agent_role_holds_the_mutation_report_text (rows `reviewer-mutants` and `acceptance-score`: each is the exact Interface text, checked inside `section_text(agent_body(name), "Role")`)
   - criterion 2: tests/test_claude_agent_texts_mutants.py::test_reviewer_mutants_paragraph_sits_between_item_6_and_the_findings_paragraph (it takes the line indices in the reviewer body of `6. **Earlier tests**:`, of the new paragraph and of `Write findings as a numbered list in your entry`, and checks they come in that order)
   - criterion 3: tests/test_claude_agent_texts_mutants.py::test_acceptance_reviewer_holds_the_mutation_score_check_once (rows `old-sentence-gone`, a count of 0 for ``Run `make mutants` if the project has the target; read the survivors``, and `heading-once`, a count of 1 for `3. **Mutation score.**`)
   - criterion 4: every test of tests/test_claude_agent_texts.py, unchanged; it gets no new test.
   - criteria 5 and 6: `make check` is the factory's gate and the docs are the documenter's, so they get no test.

   File created: tests/test_claude_agent_texts_mutants.py. I changed no earlier test file.

   Modules the test run could not import: none. The module is plain text checks on the shipped agent files, so it imports fine.

   One run of `make test`: 4 tests fail for the right reason, because the new texts are not in `claude/agents/reviewer.md` and `claude/agents/acceptance-reviewer.md` yet. The positions test fails at `lines.index` because the paragraph is missing. The `heading-once` row passes already, because the current check 3 has that heading once; the row stays to pin that the rewrite keeps it once. `make lint` is green. I skipped the type check, as the stage says.

   Open: nothing. I interpreted no criterion.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/test_claude_agent_texts_mutants.py::test_acceptance_reviewer_holds_the_mutation_score_check_once[old-sentence-gone]
6. factory: started doing as self.
7. coder: I changed the two shipped agent texts exactly as the Interface gives them.

   - `claude/agents/reviewer.md`, `## Role`: added the new mutation-report paragraph after item 6 (`6. **Earlier tests**:`) and before `Write findings as a numbered list in your entry`, with one blank line on each side.
   - `claude/agents/acceptance-reviewer.md`, `## Role`: replaced check 3 (`3. **Mutation score.**`) with the new text.

   No other line of either file changed. The `## Lessons` sections and the anchors are as they were.

   Main choice: I made the edit with a short script that replaces each anchor and the old check 3 as literal strings, and asserts first that each appears exactly once. That keeps the backticks and the double-backtick span in the new texts byte for byte as the Interface has them. I rejected typing the texts in by hand, because that risks a small difference the exact-text tests would catch only after a full run.

   Refactor: I read the diff and nothing needed changing; it is two text edits. `make check` is green, the new tests in `tests/test_claude_agent_texts_mutants.py` and every test of `tests/test_claude_agent_texts.py` included.

   What the journal changed: nothing. The `## Description` stays as it is.

   Noticed, not touched: the five smoke-test greps depend on the docs criterion. The last one (`### The mutation report of a story` in `docs/operator-guide.md`) will print `0` until the documenter writes that subsection.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I checked:
   - Acceptance criteria: I took the two `markdown` blocks out of the Interface and matched them against the files. Each appears exactly once as a whole line, in `claude/agents/reviewer.md` and `claude/agents/acceptance-reviewer.md`. The diff changes three lines in those two files: one line replaced in check 3, plus the new paragraph and its blank line. The Lessons sections and the anchors are untouched.
   - Tests: `tests/test_claude_agent_texts_mutants.py` covers criterion 1 with one parametrized test of two rows (exact text inside `section_text(..., "Role")`). Criterion 2 is one test on the line positions in the body: item 6, then the paragraph, then `Write findings`. Criterion 3 is one parametrized test with two rows: the old sentence counted 0 times and the heading counted once, so both sides are covered. Criterion 4 is the existing `tests/test_claude_agent_texts.py`, which the diff leaves unchanged. The factory's `make check` after the coder was green (journal entry 7).
   - Helpers: the module uses `agent_body` from `tests/shipped_agents.py` and `section_text` from `factory.domain.sections`, as the Interface says. It copies no helper.
   - Architecture and security: the diff changes nothing under `src/` and adds no marker that silences a check.
   - Mutation report: the coder's latest entry has no `mutants` line, and the diff changes no module under `src/factory`, so there were no survivors to read.
   - Work item hygiene: the journal explains the scripted literal replacement and why typing the texts by hand was rejected. The Description matches what was built. The docs criterion still says what the documenter must write. The coder rightly noted that the fifth smoke-test grep waits for the docs stage.

   Earlier tests: none. The diff only adds `tests/test_claude_agent_texts_mutants.py` (status `A`).
10. factory: started docs as self.
11. documenter: I wrote the three documents the docs criterion asks for and found no finding for the coder. Only documents changed, so I did not run `make check`; the factory's check after this stage decides. I ran no example. The `make mutants MUTANTS_SECONDS=1500` and `docker exec` commands are repair commands for an operator and are not run here.

    Files changed:
    - `docs/project-guide/processes-and-checks.md`, *Mutation testing*: rewritten for the human's recipe.
      - It covers the two forms (a story's branch takes all mutants by pattern; `FEATURE` or an acceptance's branch takes by name only the mutants that are not killed) and why mutmut 3.8 needs them.
      - It covers the 540 s stop inside the report's 10 minutes, the `EXIT` trap with `chmod -R g+w mutants`, the last line's exit statuses, and how to list and show the survivors of one module.
      - In *The report of a mutation run* I changed one sentence. It said the recipe would call `check_mutants` "after the story"; it now says the recipe calls it, for the report and for `--names`.
    - `docs/operator-guide.md`:
      - *What a stage run shows*, point 3: added the coder's `mutants` line with a complete and a partial example, and that a partial report is a failed report that never stalls the stage.
      - New `### The mutation report of a story` in *The project's make targets*: the time it takes, what the reviewer does, what the acceptance re-runs, the stats case with the repair by hand, and the `Permission denied` repair for Docker and Podman.
    - `docs/decisions.md`:
      - New entry *Mutation testing per story*, with feature decisions 1, 2, 4 to 7 and 13 and the rejected alternatives.
      - I added "Superseded by *Mutation testing per story*." to the date line of the older entry *Mutation testing is limited to one feature's modules*.

    Checked against the diff and found current: `claude/agents/reviewer.md` and `claude/agents/acceptance-reviewer.md` match the Interface text. The smoke-test greps for the docs file and the agent files should each print 1. Also found current: `CLAUDE.md`'s *Checks* paragraph on `make mutants`, `README.md`, and the other project-guide files, which mention mutants only in passing.

    Stale text noticed and left alone: none.

    Not mine: the work item's `.costs.jsonl` shows as modified in the work tree; that is the factory's file.

    `check`: check: green (not run again: passed on tree 3cf1f2b13373 at 2026-10-19T16:39:50Z)
    `secrets`: secrets: green (1.7 s)
12. factory: Stage docs stalled (attempt 1 of 2): a check is red after the stage: `documents`
    docs/project-guide/processes-and-checks.md: uses the v1 word 'ticket'
    make: *** [Makefile:93: documents] Error 1
13. factory: started docs as self.
14. documenter: I fixed the one failure left by the last docs run, which stalled on `make documents`: `docs/project-guide/processes-and-checks.md` used the v1 word 'ticket'. I have now run `make documents` and it passes (`documents ok`). Only documents changed, so I did not run `make check`.

    Files changed this round:
    - `docs/project-guide/processes-and-checks.md`, *Mutation testing*, the `FEATURE` bullet: the commit subjects it matches are now written as `work item <id>-S<nnnn>:`. The Makefile's `FEATURE_MODULES` pattern also matches v1's older subject form, so the text points the reader to that pattern instead of spelling the old word out.

    Files changed in round 0 (entry 11) and still in place:
    - `docs/project-guide/processes-and-checks.md`: *Mutation testing* rewritten for the human's recipe.
    - `docs/operator-guide.md`: point 3 of *What a stage run shows*, and the new `### The mutation report of a story`.
    - `docs/decisions.md`: new entry *Mutation testing per story*. The older entry is marked superseded.

    Cross-read and found current: `claude/agents/reviewer.md` and `claude/agents/acceptance-reviewer.md` against the Interface, `CLAUDE.md`'s *Checks* paragraph, `README.md`, and the other project-guide files.

    Findings for the coder: none.

    Stale text I saw but did not touch: none. The work item's `.costs.jsonl` shows as modified in the work tree; that is the factory's file.

    `check`: check: green (not run again: passed on tree 3cf1f2b13373 at 2026-10-19T16:39:50Z)
    `secrets`: secrets: green (1.7 s)
    `documents`: documents ok
15. factory: started smoke-test as self.
