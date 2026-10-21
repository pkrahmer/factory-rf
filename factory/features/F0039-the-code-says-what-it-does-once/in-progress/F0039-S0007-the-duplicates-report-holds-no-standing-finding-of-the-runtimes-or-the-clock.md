---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 380
comments_read: []
handed_over: approval
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
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T00:41:07.052536Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T00:43:42.651505Z'
  stage: doing
  run: 398670a91d1e4c8aaac770e73e0f82b1
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T00:44:03.166734Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T00:44:17.820308Z'
  stage: review
  run: 945fc4137d5d494f87b529f35db4ad74
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T00:44:38.096077Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-21T00:44:59.885736Z'
  stage: docs
  run: c69b9f13ca7e48a2b949093b1b62846b
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-21T00:45:20.598270Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-21T00:45:46.848154Z'
  stage: smoke-test
  run: e1e7549d733a431589ef5842b9b5eeab
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
6. factory: started doing as self.
7. coder: Built nothing. The Interface says no module under `src/factory/` changes and no test module is written. The only change in this story is the docs criterion, which the documenter writes (`docs/decisions.md`, *What the agent runtimes share lies in one module*, and `docs/project-guide/processes-and-checks.md`, *The baseline*). A coder does not write those files.
      - Verified on the branch as it stands. `make check` ends with `check: green` (coverage 99.14 %). `make duplicates` prints `duplicates: 0 new, 38 known, 0 gone`, so the human's baseline change already settles the four runtime findings and `ManualWaiter`, and the `ManualClock` and `advance` lines are gone.
      - Main choice: I left the code untouched. The rejected alternative was to merge the remaining similar process calls of `claude_runtime` and `opencode_runtime` into `agent_launch`. The description and the decision log entry keep those calls in each runtime, so a merge would go beyond the story.
      - Refactor: there is no diff of mine to refactor.
      - Noticed but did not touch: none. The journal did not change the meaning of the task, so the Description stays as it is.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The only changes on the branch are the work item and its `.costs.jsonl` sidecar. That fits the Interface, which says no module under `src/factory/` changes and the tester writes no test module.
   - Criterion 1: the coder's entry 7 records `check: green` and `duplicates: 0 new, 38 known, 0 gone`. Criterion 2 (docs) is the documenter's job next, and it still describes what the reader must know.
   - Baseline as the Description expects it: `security/duplicates-baseline.txt` has the `return version_printed(` line (33), the `started = due_leftovers_launch(` line (35) and the `ManualWaiter` line (36), and no longer has `ManualClock` or `advance`. So the human's change is in, and the smoke test's second block should print `3`.
   - Hygiene: the coder's journal gives the main choice (leave the code untouched) and what was rejected (merging the runtimes' remaining process calls into `agent_launch`, which the decision log entry rules out). The Description matches what was built.
   - Earlier tests: none. The diff changes, renames or deletes no test file.
10. factory: started docs as self.
11. documenter: Docs written for the docs criterion; no findings. The diff outside docs is empty, so no code contradicts the Interface.

    Files changed:
    - `docs/decisions.md`: one new bullet at the end of *What the agent runtimes share lies in one module*, dated F0039-S0007. It says the similar code `make duplicates` still finds in the runtimes is the process calls the entry keeps in each runtime. It lists them: the version call, the start of the leftovers program and of the folder removal, and the lines of `_call` that call them. It says they are accepted in the baseline for the entry's own reason, and that F0039-S0001 merged the reading of a call's end.
    - `docs/project-guide/processes-and-checks.md`: one paragraph at the end of *The baseline*. The baseline accepts the runtimes' own process calls (pointing to the decision log entry) and the test-only fakes of `factory.adapters` (`ManualClock`, `ManualWaiter`, `FakeAgentRuntime`, `FakeHostingService`). A new finding there is a copy the decision does not cover.

    Checked:
    - I read `security/duplicates-baseline.txt`. It holds the `return version_printed(`, `leftovers_error = self._end_leftovers(request)` and `started = due_leftovers_launch(` lines, plus `ManualWaiter`. `ManualClock` and `advance` are gone, as the Description says. The text I wrote matches it.
    - The coder's entry records `duplicates: 0 new, 38 known, 0 gone`. I did not rerun `make duplicates` or the smoke test blocks myself.
    - `uv run python -m factory.entry.check_documents` prints `documents ok`.
    - I did not run `make check`, because I changed only documents.

    Cross-read and found current: `README.md` and `docs/operator-guide.md` need no change, as the criterion says. The rest of *The baseline* and *The output and the exit status* already describe the key format and the report correctly.

    Stale text noticed but not touched: none.

    `check`: check: green (not run again: passed on tree 6d9d2794d8ce at 2026-10-21T00:42:31Z)
    `secrets`: secrets: green (1.4 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test run from the repository root, both blocks as written and in order. No findings.

    Block 1 (the steps of `make duplicates`, with their reports in a temporary directory, counting `new`/`gone` lines for the runtimes and `adapters/clock.py`):
    ```
    Using CPython 3.12.15 interpreter at: /usr/local/bin/python3.12
    Creating virtual environment at: .venv
    warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
             If the cache and target directories are on different filesystems, hardlinking may not be supported.
             If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.
    Installed 106 packages in 93ms
    Bytecode compiled 4164 files in 357ms
    Bytecode compiled 4164 files in 71ms
    Bytecode compiled 4164 files in 96ms
    0
    ```
    Met `Expect: 0`. The block exits with status 1 because `grep -c` exits 1 when it counts zero matches. That status belongs to the expected result and is not an error. The lines before the count are uv's stderr from building the fresh `.venv`, which is git-ignored.

    Block 2:
    ```
    3
    ```
    Met `Expect: 3`.

    I read the acceptance criteria again against these results:
    - Criterion 1 (`make check` stays green): nothing in the smoke test contradicts it. The coder's entry 7 and the documenter's entry 11 record `check: green`. I did not run it again, because this stage runs the smoke test and the factory runs the checks.
    - Criterion 2 (docs): `git diff main...HEAD -- docs` has one dated bullet (F0039-S0007) at the end of *What the agent runtimes share lies in one module* in `docs/decisions.md`. It names the version call, the start of the leftovers program and of the folder removal, and the lines of `_call`. It says they are accepted in the baseline for the entry's own reason and that F0039-S0001 merged the reading of a call's end. It also has one sentence in *The baseline* of `docs/project-guide/processes-and-checks.md` that names the runtimes' process calls and the four test-only fakes. `README.md` and `docs/operator-guide.md` are unchanged, as the criterion says they should be. Block 1's `0` confirms that the baseline these docs describe settles all of the runtime and clock findings.

    Open: nothing.
