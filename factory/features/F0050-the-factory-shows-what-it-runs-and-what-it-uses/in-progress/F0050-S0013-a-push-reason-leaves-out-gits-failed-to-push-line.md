---
stage: docs
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 552
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T23:30:50.417849Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T23:30:50.424604Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-04T23:31:08.402856Z'
  stage: intake
  run: 5cfc8757a2de43a5b69b0a3aef923592
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-04T23:31:13.846629Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-04T23:32:01.433783Z'
  stage: tests
  run: 3f89554aae9f4427aceb1586557d9d49
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-04T23:32:06.910898Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-04T23:36:54.746911Z'
  stage: doing
  run: 700f611199504461becf6fcbfe45a142
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-04T23:37:02.291895Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-04T23:37:45.666888Z'
  stage: review
  run: ecd44f4b80434cb3a28e97ed1952f847
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-04T23:37:50.921571Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-04T23:38:08.702732Z'
  stage: doing
  run: 89ba15dd52fa4926a4213a398aa9c7f3
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-04T23:38:13.724549Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-11-04T23:38:52.413895Z'
  stage: tests
  run: bfd7644605bb45e1916d89280e108c44
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-04T23:38:57.486731Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-11-04T23:43:29.873345Z'
  stage: doing
  run: cd592342125a456098acdb46b84c2937
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-04T23:43:34.922787Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-11-04T23:44:00.640398Z'
  stage: review
  run: 5d3c838035f5435e854b5aeafb1c5bb1
---

# A push reason leaves out git's "failed to push some refs" line

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

S0011 made `push_reason` leave out the porcelain frame (`To <url>`, `Done`), so that the server's own `remote:` lines stay among the three lines a reason keeps. Real git output for a refused push has one more line that S0011's examples did not hold. Git 2.39 writes `error: failed to push some refs to '<url>'` on its error stream after the summary. The feature's acceptance walk-through (F0050-A0002, a `pre-receive` hook that prints `Internal Server Error`) logged the reason `remote: Internal Server Error | error: failed to push some refs to '<url>' | ! refs/heads/<b>:refs/heads/<b> [remote rejected] (pre-receive hook declined)`. That line says nothing that the ref line does not already say, and it takes one of the three places. A server that writes two `remote:` lines (a message and a request id, for example) therefore loses its first one, and the remote URL takes up part of the 300 characters. This story leaves that one line out as well. Every other `error:` line stays, because it can be the only cause (`error: src refspec main does not match any`), and so do the three-line and 300-character limits. Retries and `push_is_retried` stay as they are.

## Interface

- `factory.domain.git` (domain), unchanged signature:

  ```python
  def push_reason(output: str) -> str: ...
  ```

  - Besides git's advice lines, `hint:` lines and the porcelain frame, a line that starts with `error: failed to push some refs to ` after stripping is left out before the last three lines are taken.
  - Any other line that starts with `error:` is kept, and so is a line that only holds those words further in (`remote: error: failed to push some refs to x`).
  - Three lines at most, joined with ` | `, cut at the end to 300 characters, as today.
- `push_is_retried` is unchanged: it reads git's whole output, not the reason.
- Tests: new rows go into a new module, `tests/domain/test_push_reason_summary_line.py`, and the end-to-end row into a new module, `tests/application/test_push_retry_server_lines.py`. S0008's and S0011's test modules stay as they are.

## Acceptance criteria

1. For the output `remote: Internal Server Error`, `error: failed to push some refs to '/srv/project.git'`, `To /srv/project.git`, `!<TAB>refs/heads/b:refs/heads/b<TAB>[remote rejected] (pre-receive hook declined)`, `Done`, the reason is `remote: Internal Server Error | ! refs/heads/b:refs/heads/b [remote rejected] (pre-receive hook declined)`.
2. Rows for the rule: `error: failed to push some refs to 'https://github.com/o/r.git'` is left out, with and without leading spaces. `error: src refspec main does not match any` is kept, and so is `remote: error: failed to push some refs to x`.
3. With two `remote:` lines (`remote: Internal Server Error`, `remote: request id 1234`), the ref line and the `error: failed to push some refs to` line, the reason holds both `remote:` lines and the ref line, in that order.
4. A stage whose result push is refused by a `pre-receive` hook that prints two lines (`Internal Server Error`, `request id 1234`) writes retry lines whose reason holds `remote: Internal Server Error`, `remote: request id 1234` and `[remote rejected]`, and not `failed to push some refs`.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, the paragraph on the reason in a `PushFailed`: git's line `error: failed to push some refs to '<url>'` is left out too, and other `error:` lines stay. `docs/project-guide/git-and-hosting.md`, the `last_push_output()` / `push_reason` paragraph: the same rule. `docs/decisions.md`: none, because the push-retry entry's "advice lines left out" still holds. `README.md`: none.

## Smoke test

```bash
uv run python -c '
from factory.domain.git import push_reason
print(push_reason("remote: Internal Server Error\nremote: request id 1234\nerror: failed to push some refs to '"'"'/srv/project.git'"'"'\nTo /srv/project.git\n!\trefs/heads/b:refs/heads/b\t[remote rejected] (pre-receive hook declined)\nDone\n"))'
```

Expect: `remote: Internal Server Error | remote: request id 1234 | ! refs/heads/b:refs/heads/b [remote rejected] (pre-receive hook declined)`.

```bash
uv run pytest tests/domain tests/application -k "push_reason or push_retry" 2>&1 | tail -1
```

Expect: a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: `factory.domain.git.push_reason(output: str) -> str` is named with an unchanged signature. The rule is concrete: a line that starts with `error: failed to push some refs to ` after stripping is left out. It also gives the contrast cases (other `error:` lines kept, `remote: error: failed to push...` kept). The test modules are named. `push_is_retried` is stated as unchanged.
   - Criteria: each one is testable by one test function. Criterion 1 is the full example. Criterion 2 covers both sides of the rule (left out with and without leading spaces; `error: src refspec` kept; `remote: error: failed...` kept). Criterion 3 covers the ordering with two `remote:` lines. Criterion 4 covers the end-to-end case through the retry log lines. The three-line and 300-character limits and `push_is_retried` are kept as they are and tested by the earlier stories, so no new criterion is needed. `make check` and `docs:` are last.
   - Smoke test: both commands are runnable. The first calls `push_reason` directly and its Expect line is an exact string. The second runs pytest with no `-q`, which is correct because `pyproject.toml` addopts already sets `-q`. Its Expect line (ends in `passed`, no `failed`) can be checked against `tail -1`.
   - Architecture: the change sits in `factory.domain.git`, a pure function with no I/O, which is the right layer. The new tests go in `tests/domain/` and `tests/application/`, mirroring the package. No other test module is changed, so no leave is needed.
   - Scope: the story is inside feature F0050's scope, as a follow-up of the S0008 and S0011 push-reason work, and it is listed in the feature's stories (from A0002). It touches nothing under Out of scope.
4. factory: started tests as vm.
5. tester: Wrote the tests for the story's four testable criteria. They are red on purpose, against today's `push_reason`.

   - criterion 1: tests/domain/test_push_reason_summary_line.py::test_the_reason_leaves_out_gits_summary_line_of_a_refused_push
   - criterion 2: tests/domain/test_push_reason_summary_line.py::test_the_reason_leaves_out_only_the_summary_line (rows: summary-left-out, indented-summary-left-out, other-error-kept, words-further-in-kept)
   - criterion 3: tests/domain/test_push_reason_summary_line.py::test_two_server_lines_and_the_ref_line_fill_the_reason
   - criterion 4: tests/application/test_push_retry_server_lines.py::test_a_retry_line_holds_both_server_lines_and_no_summary_line
   - criteria 5 (`make check`) and 6 (docs): no test; they belong to the coder's check and the docs stage.

   Files created: tests/domain/test_push_reason_summary_line.py, tests/application/test_push_retry_server_lines.py. No earlier test file and no support module was changed.

   For criterion 4 the test uses `PushCase.arm` from `tests/push_retry_support.py`, then rewrites the armed `pre-receive` hook inside the new test module so that it prints the two lines `Internal Server Error` and `request id 1234`. A check in the test makes sure the line it replaces is still there.

   One run of `uv run pytest -q` on the two new files: 5 failed. The failing rows are criterion 1, the two left-out rows of criterion 2, criterion 3 and criterion 4. They fail because the reason is wrong (git's `error: failed to push some refs to` line is still kept), not because something could not be imported. The two kept-line rows of criterion 2 pass already, as they should. Every module the tests use imported. `make lint` is green.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: Made the tester's five failing tests pass. No test was changed. `make check` is green (coverage 99.26 %).

   What I built, all in `src/factory/domain/git.py`:
   - A new constant, `PUSH_SUMMARY_PREFIX = "error: failed to push some refs to "`. A comment beside it says why the line goes: it repeats what the ref line says and it names the remote.
   - `_is_reason_line` now drops any line whose stripped text starts with that prefix. It does this in the same `startswith` tuple that already drops `hint:` lines and the `To <url>` frame line.
   - The `push_reason` docstring now names the left-out line.

   The signature is unchanged, and so are the three-line limit, the 300-character cut and `push_is_retried`. Because the check runs on the stripped line, an indented summary line is dropped too. A line that only holds these words further in (`remote: error: failed to push ...`) is kept, and so is any other `error:` line.

   Main choice: a prefix match on the full phrase, `error: failed to push some refs to `. I rejected two alternatives:
   - dropping every `error:` line, which would lose real causes such as `error: src refspec main does not match any`;
   - a regular expression that also matches the quoted URL, which buys nothing over the prefix.

   Refactor pass: I read the diff and there was nothing more to change.

   Noticed but not touched: the doc updates the docs criterion names (`docs/operator-guide.md`, `docs/project-guide/git-and-hosting.md`) belong to the documenter.

   `check`: check: green
   `duplicates`: duplicates: 4 new, 41 known, 2 gone
8. factory: started review as vm.
9. reviewer: Findings:

   1. `tests/application/test_push_retry_server_lines.py:19-40`: the fixture `result_case` is a word-for-word copy of the `result_case` fixture in `tests/application/test_push_retry_reason.py:16-37`: same parameters, same docstring, same `open_push_case("result", ...)` call. At round 0 a second copy of an existing helper counts as a finding. Fix: under the standing leave to move a shared test helper, the tester moves `result_case` to `tests/conftest.py`, deletes both copies, and has both modules use the shared fixture. `test_push_retry_reason.py` keeps its test names and what they check. The coder passes this to the tester with `tests`; the coder does not edit the tests.

   Checked and found sound:
   - Group 1 (criteria):
     - Criterion 1: `test_the_reason_leaves_out_gits_summary_line_of_a_refused_push` uses the exact output the criterion gives and expects the exact reason.
     - Criterion 2: one parametrized test covers both sides of the rule. The summary line is left out, also with leading spaces. `error: src refspec` and `remote: error: failed to push...` are kept.
     - Criterion 3: the order of the two `remote:` lines and the ref line is checked against the exact reason string.
     - Criterion 4: the test runs end to end through `PushCase`. It rewrites the armed hook to print two lines and asserts first that the line it replaces is still there. Every retry line must hold both server lines and `[remote rejected]`, and must not hold `failed to push some refs`.
     - The three-line and 300-character limits are unchanged and stay pinned by S0008's and S0011's tests. Journal entry 7 records `check: green`.
   - Group 2 (architecture): the change stays in `factory.domain.git`, a pure function with no I/O.
   - Group 3 (security): no markers, secrets or strings that build commands.
   - Group 4 (code quality, `src/factory/domain/git.py`):
     - The constant `PUSH_SUMMARY_PREFIX` has a comment that says why the line goes.
     - The match runs on the stripped line, as the Interface says.
     - The `push_reason` docstring is updated.
     - `make duplicates` shows 4 new findings (claude_runtime/opencode_runtime similar code and three cost_records variables). None are in code this diff touches.
   - Group 5 (work item): the Description matches what was built. Entry 7 records the main choice, a prefix match on the full phrase. It rejects dropping every `error:` line and a regex. The docs criterion still says what the documenter must write.

   Earlier tests: none. Every test file in the diff is new (status `A`).
10. factory: started doing as vm.
11. coder: This round handles the reviewer's one finding (entry 9). It is a copied test helper, so it is a change to tests and not to code. I changed no code and no test.

    I checked the finding. The `result_case` fixture in `tests/application/test_push_retry_server_lines.py:19-40` is a word-for-word copy of the `result_case` fixture in `tests/application/test_push_retry_reason.py:16-37`: same parameters, same docstring, same `open_push_case("result", ...)` call. Neither `tests/conftest.py` nor any `tests/*_support.py` has a shared `result_case` yet.

    The change for the tester, under the standing leave to move a shared test helper in `CLAUDE.md`:
    - Move the `result_case` fixture into `tests/conftest.py`.
    - Delete both copies, the one in `tests/application/test_push_retry_server_lines.py` and the one in `tests/application/test_push_retry_reason.py`.
    - Both modules then use the shared fixture.
    - Every test in `test_push_retry_reason.py` keeps its name and checks the same thing.
    - The tester's entry names `tests/application/test_push_retry_reason.py` as the earlier test file it changed.

    Rejected: putting the fixture in `tests/push_retry_support.py`. That module holds plain helpers and `open_push_case`, and `CLAUDE.md` puts a shared fixture in `tests/conftest.py`.

    The code in `src/factory/domain/git.py` stays as it was in round 0, and so does the Description: the journal did not change what the task means. Noticed but not touched: the docs criterion (operator guide and git-and-hosting guide) is the documenter's work.
12. factory: started tests as vm.
13. tester: I moved the `result_case` fixture into `tests/conftest.py`. This is the change the coder named in entry 11, following the reviewer's finding in entry 9. It falls under the standing leave in `CLAUDE.md` to move a shared test helper.

    What changed:
    - `tests/conftest.py`: it now has the `result_case` fixture, with the same parameters, docstring and `open_push_case("result", ...)` call as the two copies. It also imports `PushCase` and `open_push_case` from `push_retry_support`.
    - `tests/application/test_push_retry_server_lines.py` (this story's file): I deleted its copy of `result_case`. `ruff --fix` then removed the imports it no longer needs, and the module now imports only `PushCase` from `push_retry_support`.
    - `tests/application/test_push_retry_reason.py`: this is an earlier story's test file, changed under the standing leave. I deleted its copy of `result_case` and removed the same unused imports. Its test keeps its name and checks the same thing.

    No other test and no code changed. The mapping from criteria to tests is still the one in entry 5:
    - criterion 1: tests/domain/test_push_reason_summary_line.py::test_the_reason_leaves_out_gits_summary_line_of_a_refused_push
    - criterion 2: tests/domain/test_push_reason_summary_line.py::test_the_reason_leaves_out_only_the_summary_line
    - criterion 3: tests/domain/test_push_reason_summary_line.py::test_two_server_lines_and_the_ref_line_fill_the_reason
    - criterion 4: tests/application/test_push_retry_server_lines.py::test_a_retry_line_holds_both_server_lines_and_no_summary_line

    Files created: none. Every module imported. One run of `uv run pytest -q` on the two changed test modules passed. `make lint` is green.

    `lint`: lint: green (0.1 s)

    `lint`: lint: green (0.1 s)
14. factory: started doing as vm.
15. coder: This round comes after the tester moved the copied `result_case` fixture into `tests/conftest.py` (entry 13). That move was the whole of the reviewer's finding in entry 9, so this round needed no code change. I changed nothing: no code and no test.

    - Code: `src/factory/domain/git.py` is as it was in round 0. `PUSH_SUMMARY_PREFIX` holds `error: failed to push some refs to `, and `_is_reason_line` drops a line whose stripped text starts with it.
    - Check: I ran `make check` on the current tree and it is green, with coverage at 99.26 %. That includes the moved fixture and the two test modules that now use it from `tests/conftest.py`.
    - Main choice: the same as entry 7. A prefix match on the full phrase, which keeps every other `error:` line. I rejected dropping every `error:` line, and a regular expression that also matches the URL.
    - Refactor: nothing to change. The diff in `src/` is the same as the one already reviewed.
    - Description: not rewritten. The journal changed where a test fixture lives, not what the task means.
    - Noticed but not touched: the docs criterion (`docs/operator-guide.md` and `docs/project-guide/git-and-hosting.md`) is the documenter's work.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 4 new, 41 known, 2 gone
16. factory: started review as vm.
17. reviewer: no findings

    Checked in this round (round 1), against the diff and the work item:
    - Group 1 (criteria). Criteria 1 to 3: the tests in `tests/domain/test_push_reason_summary_line.py` use the exact outputs the criteria give and check the exact reasons. Criterion 2 is one parametrized test that covers both sides of the rule: the summary line left out, with and without leading spaces, and `error: src refspec ...` and `remote: error: failed to push some refs to x` kept. Criterion 4: `tests/application/test_push_retry_server_lines.py` rewrites the armed `pre-receive` hook so it prints two lines. It first asserts that the line it replaces is still there. It then checks every retry line for both `remote:` lines and `[remote rejected]`, and for the absence of `failed to push some refs`. The three-line and 300-character limits are unchanged and still pinned by S0008's and S0011's tests. Journal entry 15 records `check: green`.
    - Group 2 (architecture). The only code change is in `src/factory/domain/git.py`, a pure function in the domain layer. The new prefix joins the existing `startswith` tuple in `_is_reason_line`, and the match runs on the stripped line, as the Interface says.
    - Group 3 (security). No markers, secrets or command strings in the diff.
    - Group 4 (quality). `PUSH_SUMMARY_PREFIX` carries a comment that says why the line goes, and the `push_reason` docstring names the left-out line. The round-0 finding is resolved: `result_case` now lives once, in `tests/conftest.py:571-592`, and every type that fixture uses was already imported there. The parametrized `case` fixture in `tests/application/test_push_retry.py` is a different fixture (it runs both `result` and `record`), so it is not a copy. `make duplicates` reports 4 new findings in entries 7 and 15, none of them in code this diff touches.
    - Group 5 (work item). The Description matches what was built. Entries 7 and 15 give the main choice, a prefix match on the full phrase, and what was rejected: dropping every `error:` line, and a regular expression. The docs criterion still says what the documenter must write.

    Earlier tests:
    - `tests/application/test_push_retry_reason.py`: under the standing leave to move a shared test helper. Only its copy of `result_case` and the imports that copy alone used were removed. Its one test keeps its name and checks the same thing.
    - `tests/conftest.py`: none needed. The change only adds the shared `result_case` fixture and the `push_retry_support` import, and every fixture the file already held is unchanged.
