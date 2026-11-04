---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 548
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs
  started_at: '2026-11-04T21:46:46.354987Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T21:38:34.081571Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T21:38:34.088778Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-04T21:38:56.801994Z'
  stage: intake
  run: 1d92dce72c6345c9b8d3e2d4c08c9d9b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-04T21:39:02.398880Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-04T21:40:39.079413Z'
  stage: tests
  run: 1576e4240f634e239192a60ef811434a
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-04T21:40:44.798176Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-04T21:45:42.013287Z'
  stage: doing
  run: fd0d47a027f54e75afd764bb46a51fa3
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-04T21:45:50.197034Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-04T21:46:37.690386Z'
  stage: review
  run: f522917f60964c5e8327aca1381f9ede
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-04T21:46:46.354987Z'
  stage: docs
---

# A push's reason keeps the server's words

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

S0008 put git's reason into every failed push. The reason is git's last three non-empty lines, after git's advice lines are left out. The factory pushes with `--porcelain` (`src/factory/adapters/git_cli.py:294`), so git's output ends with the porcelain summary: a `To <url>` line, one status line per ref, and `Done`. Two of the three lines are then the frame of that summary. The server's own message, the `remote: ...` lines git prints before it, is cut. The feature's acceptance walked a stage against a remote whose `pre-receive` hook refuses with `Internal Server Error`. Each retry line read `push: retry 1 of 3 in 5 s: To /tmp/.../remote.git | !<TAB>refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001<TAB>[remote rejected] (pre-receive hook declined) | Done`. The server's line did not appear. This story leaves the porcelain frame out of the reason too: the line `Done` and a line that starts with `To `. It also writes a tab inside a kept line as one space, so the log line is one plain line. Which pushes are retried, and how many lines and characters the reason keeps, do not change.

## Interface

- `factory.domain.git` (domain), unchanged signature:

  ```python
  def push_reason(output: str) -> str: ...
  ```

  - Before it takes the last three lines, it leaves out, besides git's advice lines (S0008), every line that is exactly `Done` after stripping, and every line that starts with `To ` after stripping.
  - A line that holds more than that (`remote: Done`, `remote: To be retried`) is kept.
  - In a kept line, every run of whitespace (tabs included) becomes one space.
  - Three lines at most, joined with ` | `, cut at the end to 300 characters, as today.
- `push_is_retried` is unchanged: it reads git's whole output, not the reason.
- Tests: new rows go into a new module, `tests/domain/test_push_reason_porcelain.py`. S0008's `tests/domain/test_push_reason.py` stays as it is, and its rows still pass, since none of them ends in `Done`. The coder checks this, and the tester names any row that does.

## Acceptance criteria

1. For the output `remote: Internal Server Error`, `To /srv/project.git`, `!<TAB>refs/heads/b:refs/heads/b<TAB>[remote rejected] (pre-receive hook declined)`, `Done`, the reason is `remote: Internal Server Error | ! refs/heads/b:refs/heads/b [remote rejected] (pre-receive hook declined)`.
2. Rows for the frame: `Done` with leading spaces is left out; `To https://github.com/o/r.git` is left out; `remote: Done` and `remote: To be retried` are kept.
3. A tab inside a kept line, and two spaces, each become one space. A line of tabs only counts as empty.
4. An output with five reason lines after the frame is left out keeps the last three, and a reason over 300 characters is cut at the end to 300. These are S0008's limits, with the frame present in each row.
5. A stage whose result push is refused by a `pre-receive` hook that prints `Internal Server Error` writes retry lines whose reason holds `remote: Internal Server Error` and `[remote rejected]`, and no `Done`.
6. `make check` stays green.
7. docs: `docs/operator-guide.md`, where S0008 wrote that the reason in a push error is git's own: the porcelain frame (`To <url>`, `Done`) is left out, so the server's `remote:` lines stay. `docs/decisions.md`: none. `README.md` and the project guide: none.

## Smoke test

```bash
uv run python -c '
from factory.domain.git import push_reason
print(push_reason("remote: Internal Server Error\nTo /srv/project.git\n!\trefs/heads/b:refs/heads/b\t[remote rejected] (pre-receive hook declined)\nDone\n"))'
```

Expect: `remote: Internal Server Error | ! refs/heads/b:refs/heads/b [remote rejected] (pre-receive hook declined)`.

```bash
uv run pytest tests/domain -k push_reason 2>&1 | tail -1
```

Expect: a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: `factory.domain.git.push_reason(output: str) -> str` exists with this signature (src/factory/domain/git.py:153). The story names the module, the signature, and the new exclusions (exact `Done`, lines starting `To `, whitespace collapse). It names the new test module and keeps S0008's.
   - Criteria: every Interface clause has a criterion. Criterion 1 is the full example. Criterion 2 has the rows for the dropped lines (`Done` with leading spaces, `To <url>`) and the kept lines (`remote: Done`, `remote: To be retried`). Criterion 3 covers whitespace collapse and a tab-only line counting as empty. Criterion 4 covers the 3-line and 300-character limits with the frame present. Criterion 5 is the end-to-end retry-line case with a pre-receive hook. Each can be tested by one function, and the failing sides (dropped vs kept) are both covered. One small gap: nothing tests a `To ` line with leading spaces. The Interface says "after stripping", and the Done row already shows that stripping applies, so I did not ask.
   - Smoke test: both commands are runnable. pyproject's `addopts` already has `-q`, and the pytest command passes none. The Expects are checkable (an exact string, and a trailing `passed` with no `failed`).
   - Architecture: the change is in the domain layer, a pure function with no I/O. `push_is_retried` stays untouched.
   - Scope: it fits F0050's S0008 follow-up (S0011 is listed in feature.md, from A0001). It is not in the Out of scope list. Retry rules and limits do not change.
4. factory: started tests as vm.
5. tester: Tests written. They fail for the right reason: `push_reason` still keeps the porcelain frame and the tabs.

   - criterion 1: tests/domain/test_push_reason_porcelain.py::test_the_reason_keeps_the_servers_line_and_the_refused_ref
   - criterion 2: tests/domain/test_push_reason_porcelain.py::test_the_reason_leaves_out_the_porcelain_frame_only (rows: indented `Done` left out, `To https://github.com/o/r.git` left out, `remote: Done` kept, `remote: To be retried` kept)
   - criterion 3: tests/domain/test_push_reason_porcelain.py::test_whitespace_in_a_kept_line_becomes_one_space (rows: a tab inside, two spaces, a mixed run, a line of tabs only counted as empty)
   - criterion 4: tests/domain/test_push_reason_porcelain.py::test_the_reason_keeps_the_last_three_lines_after_the_frame (3, 4 and 5 lines, with `To ` and `Done` around them) and ::test_a_reason_with_the_frame_is_cut_at_300_characters (300 kept, 301 cut, with the frame)
   - criterion 5: tests/application/test_push_retry_reason.py::test_a_retry_line_holds_the_servers_message_and_no_porcelain_done. A stage's result push is refused four times by the `pre-receive` hook that prints `Internal Server Error`. Every retry line holds `remote: Internal Server Error` and `[remote rejected]`, and no `Done`.
   - criteria 6 and 7: no test (`make check`, docs).

   Files created: tests/domain/test_push_reason_porcelain.py, tests/application/test_push_retry_reason.py, tests/push_retry_support.py.

   Earlier test file changed under the standing leave to move a shared test helper: tests/application/test_push_retry.py. Criterion 5 needs that module's push setup. I moved `RecordingGit`, `PushCase` (with its `arm` hook and `retry_lines`), `RETRY`, `_result_push` and `_record_push` (now `result_push` and `record_push`) to tests/push_retry_support.py. I also added a builder, `open_push_case`, which holds the body of the old `case` fixture. The `case` fixture stays in test_push_retry.py and now calls `open_push_case`. Every earlier test keeps its name and checks the same thing, and they all still pass.

   S0008's tests/domain/test_push_reason.py is unchanged. None of its rows ends in `Done`. Its rows with runs of spaces (`[rejected]        main`) only check for a substring or hold single spaces, so the whitespace rule leaves them passing.

   Run: `uv run pytest -q` on the two new modules, test_push_reason.py, test_push_retry.py and tests/test_shared_imports.py. Result: 13 failures, all in the two new modules; the earlier tests pass. The criterion 5 failure shows the current reason: `To /tmp/.../remote.git | !\trefs/heads/...\t[remote rejected] (pre-receive hook declined) | Done`. The two `remote: ...` kept rows of criterion 2 pass already, as they should. Every module imported, so there is no import error. `make lint` is green.

   Open: none. As intake noted, no row has a `To ` line with leading spaces; the Interface does not need one.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Implemented. `push_reason` now leaves out the frame that `--porcelain` puts around its summary, and it writes each run of whitespace in a kept line as one space. `make check` is green: test green (117.3 s), coverage 99.25 %, check: green.

   - What I built, in `src/factory/domain/git.py`:
     - Two new constants, `PUSH_PORCELAIN_DONE = "Done"` and `PUSH_PORCELAIN_TARGET_PREFIX = "To "`, each with a comment on why they are left out.
     - `_is_reason_line` (it gets lines already stripped) now refuses a line that is exactly `Done`, and a line that starts with `To ` or `hint:`. A line such as `remote: Done` or `remote: To be retried` is kept, because only the exact `Done` and the `To ` prefix count.
     - A new private helper, `_one_space_apart`, does `" ".join(line.split())` on each kept line. A line of tabs only is empty after the strip, so the existing empty-line rule leaves it out.
     - The line count, the separator and the 300-character cut are unchanged, and so is `push_is_retried`. The docstring now says all of this.
   - Main choice: I collapse the whitespace after the line passes the filter, so the filter still reads the stripped line exactly as S0008's rules read it. I rejected collapsing before the filter. It would have changed what the advice-line comparison sees, and it would have done work on lines that are thrown away.
   - Checked as the Interface asks: S0008's `tests/domain/test_push_reason.py` and `tests/application/test_push_retry.py` pass unchanged, next to the new `tests/domain/test_push_reason_porcelain.py` and `tests/application/test_push_retry_reason.py`.
   - Refactor: I made one pass. I replaced a double assignment to `lines` with a generator of stripped lines, and put the collapse in `_one_space_apart`. No other change was needed.
   - Journal: no entry changed what the task means, so I did not rewrite the Description.
   - Noticed, not touched: as intake and the tester both said, no test has a `To ` line with leading spaces. The code strips before it checks the prefix, so such a line is left out.

   `check`: check: green
   `duplicates`: duplicates: 4 new, 41 known, 2 gone
8. factory: started review as vm.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (src/factory/domain/git.py, tests/domain/test_push_reason_porcelain.py, tests/application/test_push_retry_reason.py, tests/push_retry_support.py, tests/application/test_push_retry.py) against the work item. I read the code and did not rely on the journal's account of it.

   no findings

   - Acceptance criteria: each criterion has a test that checks what it is named after.
     - Criterion 1: exact equality on the full example.
     - Criterion 2: four parametrized rows covering both sides of the frame rule (indented `Done` and `To <url>` left out; `remote: Done` and `remote: To be retried` kept).
     - Criterion 3: tab, two spaces, a mixed run, and a line of tabs only.
     - Criterion 4: 3, 4 and 5 lines, and 300 and 301 characters, so both sides of each limit, with the frame present in every row.
     - Criterion 5: a real bare remote whose `pre-receive` hook refuses four times. Every retry line is checked for `remote: Internal Server Error`, `[remote rejected]` and no `Done`.
     - The coder's `make check` was green (journal entry 7).
     - S0008's tests/domain/test_push_reason.py is unchanged and contains no `Done` row.
   - Architecture: the change is pure domain code with no I/O. `push_is_retried` is untouched.
   - Security: no strings built into commands, no markers that silence a check, no secrets.
   - Quality: the constants carry a why-comment, and the `push_reason` docstring is updated. `_one_space_apart` is the only whitespace collapse in src/factory, so it is not a second copy of a helper. The tester's moved helpers live once, in tests/push_retry_support.py.
   - Work item: the Description matches what was built. The journal names the main choice (collapse after the filter) and the option it rejected. The docs criterion still describes what the operator guide needs to say.

   Notes:
   - tests/domain/test_push_reason_porcelain.py::test_the_reason_leaves_out_the_porcelain_frame_only: no row for an indented `To ` line (e.g. `"  To https://github.com/o/r.git"` left out). The code handles it as the Interface says: src/factory/domain/git.py:163 strips each line before `_is_reason_line` checks the `To ` prefix.

   Earlier tests:
   - tests/application/test_push_retry.py (M): changed under the standing leave to move a shared test helper.
     - Moved to tests/push_retry_support.py: `RecordingGit`, `PushCase`, `RETRY`, and the result/record push builders.
     - The `case` fixture's body moved there as `open_push_case`. The fixture keeps its name and its params.
     - The test functions below the fixture are unchanged, and each keeps its name and what it checks.
10. factory: started docs as vm.
