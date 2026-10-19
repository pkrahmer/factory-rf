---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 301
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-19T23:29:54.255632Z'
  lease_duration: 60
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
