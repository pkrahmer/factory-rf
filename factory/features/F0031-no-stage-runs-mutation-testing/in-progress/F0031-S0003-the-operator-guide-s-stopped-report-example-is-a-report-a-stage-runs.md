---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 301
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T23:29:18.068013Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T23:29:18.073844Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T23:29:33.865711Z'
  stage: intake
  run: 33125197a51c45ea8df2a14394ff5f88
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T23:29:54.255632Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T23:30:47.264736Z'
  stage: tests
  run: 09f2fa45dee24f39aab0a45212617bdd
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T23:31:07.855420Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T23:32:10.160645Z'
  stage: doing
  run: febb99ae723048739bc57d53c7fcbd0d
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T23:32:31.146184Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T23:32:50.551621Z'
  stage: review
  run: 1ffb8c4a37484ea984f5791cc2265db8
---

# The operator guide's stopped-report example is a report a stage runs

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0031 made the documents say that no stage and no agent runs `make mutants` (`docs/operator-guide.md`, *Mutation testing by sweep*). The same guide's *What a stage run shows*, point 3, still shows a report stopped at its time limit with the example `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) ``. That is the line the coder's old `mutants` report wrote. Today no stage has a `mutants` report (`factory/pipeline.yml`), so an operator who reads the example is shown a line no entry can hold, two screens after being told that no stage runs the target. The reports a stage still runs are the tests stage's `test` (time limit 10 minutes, 600 s) and the coder's `duplicates`. This story replaces the example with a stopped `test` report. It is documentation only: the tester and the coder change nothing. These stay as they are: the rule the example illustrates (the note ` (stopped at its time limit after <seconds> s)`, rounded down), every other passage of the guide, and the tests that use `mutants` as sample data of a stopped command (`tests/domain/test_command_line_time_limit.py`, `tests/application/test_stage_time_limited_report.py`), which F0031's decision 7 keeps.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes one example in `docs/operator-guide.md`, *What a stage run shows*, point 3.

Old: ``for example `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) ``.``
New: ``for example `` `test`: ........ [ 87%] (stopped at its time limit after 600 s) `` (the tests stage's `make test`, stopped at its 10 minutes).``

- `make test` runs pytest with `-q`, so the last line it printed before a stop is a progress line of dots and a percentage; the example shows one.
- No other line of `docs/operator-guide.md` changes.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in `docs/operator-guide.md`, *What a stage run shows*, point 3, the example of a report stopped at its time limit is the Interface's new text: `` `test`: ........ [ 87%] (stopped at its time limit after 600 s) `` occurs exactly once in the guide, and `` `mutants`: `` occurs 0 times. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c -F '`mutants`: ' docs/operator-guide.md || true
```
Expect: `0`

```bash
grep -c -F '`test`: ........ [ 87%] (stopped at its time limit after 600 s)' docs/operator-guide.md
```
Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names the one passage (`docs/operator-guide.md`, *What a stage run shows*, point 3, line 703) with the exact old and new text; the old text is present there once, `test` is a stage report in `factory/pipeline.yml` (time_limit 10 = 600 s); no signature involved, and the Interface states no behaviour beyond the replaced example.
   Criteria: 1 (nothing outside docs changes), 2 (`make check` green) and 3 (new string occurs exactly once, `` `mutants`: `` zero times, `check_documents` prints `documents ok`) are each checkable by grep or a command. The story states no rule with a failing side. Grep shows `` `mutants`: `` occurs only at line 703, so zero is reachable.
   Smoke test: three runnable commands (two greps, one `uv run`), each with an `Expect:` line checkable against the output (`0`, `1`, `documents ok`).
   Architecture: documentation only, no layer touched; consistent with CLAUDE.md, where the documenter owns `docs/`.
   Scope: within F0031's goal (documents say no stage runs mutation testing). The tests that use `mutants` as sample data stay, as feature decision 7 says. Nothing is in its "Out of scope".
4. factory: started tests as self.
5. tester: No tests written: the story is documentation only. Its Interface says no module under `src/factory/` and no test changes, and criterion 1 says the tester changes nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` and says so in its entry. This is that entry.
   criterion 1: no test. It is a constraint on the diff, and this stage changed no file under `src/`, `tests/`, `image/`, `template/` or `claude/`.
   criterion 2: no test. The factory's `make check` covers it.
   criterion 3: no test. It is the docs criterion, which the documenter fulfils and the smoke test checks with its two greps and `check_documents`. A pytest test pinning the guide's wording would itself be a change under `tests/`, which criterion 1 forbids.
   Files created: none. Modules the test run could not import: none, because no test was added. I did not run `make test`, since without new tests there is no red to confirm. `make lint` is green.
   Rejected: a test that greps `docs/operator-guide.md`, because criterion 1 forbids it.
   Open: nothing. The coder has nothing to implement either; the documenter makes the change.

   `lint`: lint: green (0.0 s)
   `test`: test: green (38.3 s)
6. factory: started doing as self.
7. coder: Built nothing. This story only changes documentation. Its Interface changes no module under `src/factory/` and no test, and criterion 1 says the coder changes nothing under `src/`, `tests/`, `image/`, `template/` or `claude/`. This entry confirms that: this stage changed no file at all.
   Main choice: I left `docs/operator-guide.md` alone, because the documenter makes the one change, from the docs criterion, and CLAUDE.md says the coder does not write the guides. Rejected: changing the example in *What a stage run shows*, point 3, myself, which would take the documenter's work.
   No refactor, since there is no diff to read. The journal did not change what the task means, so `## Description` stays as it is.
   `make check` is green (`check: green`; `test: green (41.0 s)`, coverage 99.13 %).
   Noticed but did not touch: nothing.

   `check`: check: green (not run again: passed on tree 5006d1b6db9a at 2026-10-19T23:02:45Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I read: the work item and `git diff main...HEAD -- . ':!factory'`. The diff is empty: the branch changes only this work item's `.md` file and adds its `.costs.jsonl` sidecar under `factory/`.
   1. Acceptance criteria: criterion 1 holds, because nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changed, and both the tester (entry 5) and the coder (entry 7) say so. Criterion 2: the coder's entry records `check: green` (coverage 99.13 %). Criterion 3 is the docs criterion and is still open for the documenter. The story states no rule with a failing side, so no test is missing.
   2–4. Architecture, security and quality: there is no code to check. The `duplicates: 5 new` in entry 7 cannot come from this branch, because the branch changes no code.
   5. Work item hygiene: the docs criterion still matches the guide. `docs/operator-guide.md:703` (*What a stage run shows*, point 3) holds the old example `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) ``, and it is the only `` `mutants`: `` in the guide. The new example is accurate: `factory/pipeline.yml` lists `test` among the tests stage's `reports`, with `time_limit: 10`, which is 600 s.
   6. Earlier tests: none changed. The diff changes, renames or deletes no test file.
