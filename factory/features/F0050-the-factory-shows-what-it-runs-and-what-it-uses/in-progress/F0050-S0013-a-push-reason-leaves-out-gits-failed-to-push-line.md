---
stage: doing
blocked: null
round: 0
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
