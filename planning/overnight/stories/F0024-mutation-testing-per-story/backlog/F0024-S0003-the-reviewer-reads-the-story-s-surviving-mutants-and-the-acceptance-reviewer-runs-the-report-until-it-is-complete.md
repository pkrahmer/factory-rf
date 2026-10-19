# The reviewer reads the story's surviving mutants, and the acceptance reviewer runs the report until it is complete

## Description

With the feature's changes, the factory runs `make mutants` as a report after the coder. The coder's entry then ends with a line such as `` `mutants`: mutants: 1653 killed, 65 survived, ... ``, and the survivors of the story's modules stay in `mutants/` in the checkout. Nobody reads them yet: the reviewer's text says nothing of a mutation report, and the acceptance reviewer's text runs `make mutants` once. This story changes the two shipped agent texts. The reviewer reads the survived and timed-out mutants of the modules the diff changed, in the way the project's `CLAUDE.md` names. A survivor in a line the diff added or changed that breaks a rule the work item states is a finding under item 1, so the tester adds the test while the story is open. An equivalent survivor, a changed message text, a line the diff did not change, and a `partial` line are notes for the feature's acceptance. The reviewer never runs the report itself. The acceptance reviewer runs `make mutants` again while its last line says `partial`, at most three runs in all, reports the score of the last line and whether it is partial, and tells the survivors the stories' reviews passed on from new ones. Both texts stay true for a project whose `mutants` target is still the feature-level one, or that has none. The `Makefile` and `CLAUDE.md` lines the reviewer relies on are the human's change 1, which comes before this story.

## Interface

`claude/agents/reviewer.md` (the coder writes it), section `## Role`: right after the checklist's item 6, and before the paragraph that begins `Write findings as a numbered list in your entry`, one new paragraph, exactly:

```markdown
When the coder's latest entry has the line of a mutation report (`` `mutants`: ``), read the survived and timed-out mutants of the modules the diff changed as part of item 1, listing and showing them as the project's `CLAUDE.md` says; do not run the report yourself, the factory ran it after the coder. A survivor in a line the diff added or changed, whose change breaks a rule the work item states, is a finding under item 1: name the mutant, the rule, and the test that would notice it. A survivor that changes no behaviour, changes only a message text, or sits in a line the diff did not change is a note, at any round: one line per group under `Notes:`, for the feature's acceptance. A report line that says `partial` is a note too, never a pass of the mutants it did not reach.
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
   - `docs/operator-guide.md`, *What a stage run shows*, point 3: the coder's `mutants` line with an example, complete and partial, and that a partial one is a failed report that never stalls the stage. A new subsection of *The project's make targets*, with the heading line exactly `### The mutation report of a story`: the time it takes (about 3 to 11 minutes for factory-rf's stories, a fixed 165 s plus 0.13 to 0.25 s per mutant, measured on 2026-10-19), what the reviewer does with the survivors, and what the acceptance re-runs. It also gives the repair when the line reads `Permission denied`: `MSYS_NO_PATHCONV=1 docker exec -u root factory-self-factory-1 chmod -R g+w /work/checkout/mutants`.
   - `docs/decisions.md`: an entry *Mutation testing per story*, dated with the story, superseding *Mutation testing is limited to one feature's modules*, with the feature's decisions 1, 2, 4 to 7 and 13 and the rejected alternatives: running only the changed functions, every unchecked mutant of the package, a longer lease, the report's whole output in the journal, and a gentler stop in the process module.

## Smoke test

```bash
grep -c 'When the coder.s latest entry has the line of a mutation report' claude/agents/reviewer.md
grep -c 'A report line that says `partial` is a note too, never a pass of the mutants it did not reach.' claude/agents/reviewer.md
grep -c 'and run it again while its last line says `partial`, at most three runs in all' claude/agents/acceptance-reviewer.md
grep -c 'Report the score from the last run.s last line, say whether it is partial, and give the groups.' claude/agents/acceptance-reviewer.md
grep -cx '### The mutation report of a story' docs/operator-guide.md
```

Expect: five lines, each `1`.

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
