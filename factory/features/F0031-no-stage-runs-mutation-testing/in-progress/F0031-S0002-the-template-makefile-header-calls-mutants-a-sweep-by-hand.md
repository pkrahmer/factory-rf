---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 294
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-19T22:27:58.433108Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T22:27:21.782684Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T22:27:21.788167Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T22:27:37.523959Z'
  stage: intake
  run: 4ee8082d05cc4e27b5384b24ca7ecf92
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T22:27:58.433108Z'
  stage: tests
---

# The template's Makefile header calls mutants a sweep by hand

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0031-S0001 changed the template's words on `make mutants`: `template/CLAUDE.md` and the comment above `FEATURE ?=` (`template/Makefile:103`) now say that `mutants` is for a sweep by hand and never run by a stage. The header of the same `Makefile`, line 4, still says "`duplicates` and `mutants` are reports outside `check`". In the factory, a report is a command that a stage runs after its agent (`reports:` in the pipeline definition). `duplicates` can be one, and the template's `CLAUDE.md` tells a project how. `mutants` can no longer be one. So a new project's `Makefile` contradicts itself on its fourth line. The coder, the reviewer and the documenter of S0001 each noticed this, and the story's Interface left it out. This story changes line 4 only. These stay as they are: every other line of `template/Makefile`, its `mutants` recipe, `template/CLAUDE.md`, `template/factory/pipeline.yml` and every module under `src/`. The todo demo's `Makefile:4` holds the same line. It is outside every write path, and its change is the human's, if the human wants the demo to follow the template.

## Interface

No module under `src/factory/` changes. The coder changes one line of `template/Makefile` and nothing else in it.

`template/Makefile`, line 4. Old: ``# `duplicates` and `mutants` are reports outside `check`. A Python example with a src layout.`` New, two lines in its place:

```make
# `duplicates` is a report outside `check`; `mutants` is for a sweep by hand, never a stage.
# A Python example with a src layout.
```

- The new line 4 has 92 characters, within the 95 of the header's longest comment line, so the sentence moves to a line of its own. Lines 1 to 3 do not change, and every later line moves down by one. No test reads a line of this file by its number.

Tests (the tester writes them): a new module, `tests/test_template_makefile_header.py`, that reads `template/Makefile` through `ROOT` of `tests/shipped_agents.py`. It changes no earlier test. `tests/test_template_makefile.py` and `tests/test_claude_agent_texts_mutants.py` pass unchanged.

## Acceptance criteria

1. The template's `Makefile` header no longer calls `mutants` a report. The test has rows of one parametrized test, each counting a text over `template/Makefile`:
   - ``# `duplicates` is a report outside `check`; `mutants` is for a sweep by hand, never a stage.`` occurs exactly once, as the file's line 4.
   - `` `duplicates` and `mutants` are reports`` occurs 0 times.
   - `# A Python example with a src layout.` is the file's line 5.
2. Nothing else in the template changed: `tests/test_template_makefile.py`, `tests/test_claude_agent_texts_mutants.py` and `tests/test_claude_files.py` pass unchanged.
3. `make check` stays green.
4. docs: none. `docs/project-guide/agents.md` already says that `duplicates` is a report outside `check` and that `mutants` is for a sweep by hand and never run by a stage, and no document quotes the header line.

## Smoke test

```bash
grep -c -F '`duplicates` is a report outside `check`; `mutants` is for a sweep by hand, never a stage.' template/Makefile
```
Expect: `1`

```bash
grep -c -F '`duplicates` and `mutants` are reports' template/Makefile || true
```
Expect: `0`

```bash
sed -n '4,5p' template/Makefile
```
Expect: two lines, ``# `duplicates` is a report outside `check`; `mutants` is for a sweep by hand, never a stage.`` and `# A Python example with a src layout.`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: one line of `template/Makefile` (line 4) is replaced by two exact lines; no module under `src/` changes. I checked the old line 4 against the file and it matches. The new line is 92 characters, and the header's longest line is 95, as the story says.
   Criteria: criterion 1 has three rows, each a countable text with an exact value (once as line 4, 0 occurrences of the old phrase, line 5 exact). That covers both the new text and the removal of the old. Criterion 2 names the tests that must pass unchanged. Criterion 3 is `make check`; criterion 4 is `docs: none`, with a reason. The Interface states no limit, validation or error, so no failing side is missing.
   Smoke test: all three commands (`grep -c -F`, with `|| true` for the 0 case, and `sed -n '4,5p'`) run as written, and each `Expect:` line is checkable against the output.
   Architecture: the change is to a template file in the coder's write path (`template/*`). The new test module goes under `tests/` and reads the file through `ROOT` of `tests/shipped_agents.py`. It is at the `tests/` root, which fits a module outside the layers. No dependency is added.
   Scope: the change is in F0031's goal (the template's words on `make mutants`). The story leaves out the other lines, the `mutants` recipe, `template/CLAUDE.md`, `template/factory/pipeline.yml` and the todo demo. No earlier test is changed.
4. factory: started tests as self.
