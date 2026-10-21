---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 380
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T00:37:50.291940Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T00:37:50.297495Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T00:38:08.449695Z'
  stage: intake
  run: 092eee53fe364b64afb8874b79da699f
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T00:38:29.132556Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T00:40:46.609588Z'
  stage: tests
  run: 196a44b2b471460ea99f81d5631c88e6
---

# The duplicates report holds no standing finding of the runtimes or the clock

## Description

Since F0020, every coder entry records `duplicates: 5 new`: four blocks of similar code shared by `factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime`, and the class `ManualWaiter` in `src/factory/adapters/clock.py`, which vulture reports as unused. A finding that is reported as new on every story hides the next real one, so each of the five is settled once (the feature's decision 12). One is merged by S0001: the reading of the refusals at the end of a call (`refusal = call_refusal(`) moves into `read_call_end`. Three are accepted, because what stays similar after S0001 is the runtimes' own process calls, which the decision log's entry *What the agent runtimes share lies in one module* keeps in each runtime: the call of `<executable> --version` before `version_printed`, the start of the leftovers program and of the folder removal (`_end_leftovers`, `_remove_temporary_folder`), and the lines of `_call` that call them. Their words and their readers already lie in `factory.adapters.agent_launch`, so a fix of what they mean reaches both runtimes. `ManualWaiter` is accepted like `ManualClock` and the fakes beside it: it is a fake the tests use, and it lives in `factory.adapters` as the fakes do. The human writes the accepted findings into `security/duplicates-baseline.txt` and removes the two lines that no finding has any more, `ManualClock` and its `advance` (the feature's *The human's changes*, before this story starts). This story records the decision in the decision log and in the project guide. No code and no test changes.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The documenter checks the text against `security/duplicates-baseline.txt` as the human's change leaves it, against `docs/decisions.md`, *What the agent runtimes share lies in one module*, and against the output of `make duplicates` on the story's branch.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/decisions.md`, the entry *What the agent runtimes share lies in one module*: one line, dated with the story, that the similar code `make duplicates` still finds in the two runtimes is the process calls the entry keeps in each runtime (the version call, the start of the leftovers program and of the folder removal, and the lines of `_call` that call them), accepted in `security/duplicates-baseline.txt` for the entry's own reason, and that the reading of a call's end was merged by F0039-S0001. `docs/project-guide/processes-and-checks.md`, *The baseline*: one sentence that the baseline accepts the runtimes' own process calls (decision log, *What the agent runtimes share lies in one module*) and the fakes of `factory.adapters` that only the tests use (`ManualClock`, `ManualWaiter`, `FakeAgentRuntime`, `FakeHostingService`), so a new finding there is a copy that the decision does not cover. `README.md` and `docs/operator-guide.md`: none, since nothing an operator or a newcomer sees changes.

## Smoke test

The block runs the steps of `make duplicates` with their reports in a temporary directory, because the smoke tester may not write `.reports/`.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
PYLINTHOME="$d" uv run pylint --disable=all --enable=duplicate-code --output-format=json --exit-zero src/factory > "$d/similar-code.json"
uv run vulture src/factory --min-confidence 60 --ignore-decorators "@field_validator,@model_validator" --ignore-names model_config > "$d/dead-code.txt" || true
uv run python -m factory.entry.check_duplicates --baseline security/duplicates-baseline.txt "$d/similar-code.json" "$d/dead-code.txt" | grep -E '^(new|gone) ' | grep -c -E 'claude_runtime|opencode_runtime|adapters/clock\.py'
```
Expect: `0` (on `main` of 2026-10-20, before S0001 and the human's change, `7`: four `new` similar-code lines of the runtimes, `new` for `ManualWaiter` and `gone` for `ManualClock` and `advance`)

```bash
grep -c -E "ManualWaiter|return version_printed\(|started = due_leftovers_launch" security/duplicates-baseline.txt
```
Expect: `3`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: no module under `src/factory/` changes and no test module is written. The Interface names the documents to check against: `security/duplicates-baseline.txt`, `docs/decisions.md` (*What the agent runtimes share lies in one module*, present at line 662) and the output of `make duplicates`. That fits a docs-only story.
   - Criteria: there are two, and both are meaningful. Criterion 1 is `make check` staying green. Criterion 2 is the docs criterion, which names the exact entry and section for each edit, the content of each, and the files that stay untouched. No code behaviour or Interface rule exists, so there is no rule whose failing side needs a criterion. The tester has nothing to build, as the feature says.
   - Smoke test: both blocks are runnable. The first runs the steps of `make duplicates` in `$TMPDIR` and counts `new`/`gone` lines for the runtimes and `clock.py`, and `Expect: 0` can be checked against that count. It passes no `-q` to pytest. The second block greps the baseline, and `Expect: 3` is checkable. I ran its grep logic against the baseline already on the branch: it holds the `ManualWaiter`, `return version_printed(` and `started = due_leftovers_launch` lines (33 to 36), and `ManualClock` is gone, so the human's change is in.
   - Architecture: this changes only `docs/decisions.md` and `docs/project-guide/processes-and-checks.md` (*The baseline*, present at line 158), which the documenter writes. The accepted fakes stay in `factory.adapters`, as `CLAUDE.md` places them.
   - Scope: this is S0007 of F0039, which lists it and decision 12 in its Scope. Nothing it does falls under Out of scope. Decision 13 sets the order after S0001 and the baseline change, and the baseline change is done.
4. factory: started tests as self.
5. tester: No tests written. The Interface says no module under `src/factory/` changes and the tester writes no test module, so neither criterion maps to a test function.
   - criterion 1 (`make check` stays green): no test function. The factory's own check is the test.
   - criterion 2 (docs: `docs/decisions.md` and `docs/project-guide/processes-and-checks.md`): no test function. The documenter checks the text, and so does the docs stage's `make documents`.

   Files created: none. Every module imported, since no new test exists.

   I ran `make test` once and it ended with `test: green (61.6 s)` at 99.14 % coverage. No red test was expected, because no behaviour changes. `make lint` is green.

   Nothing is open for the coder: their work is the docs criterion, which the documenter stage writes.

   `lint`: lint: green (0.5 s)
   `test`: test: green (60.5 s)
