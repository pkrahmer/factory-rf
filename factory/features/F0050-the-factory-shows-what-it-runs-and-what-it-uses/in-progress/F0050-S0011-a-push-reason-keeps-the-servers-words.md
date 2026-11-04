---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 548
comments_read: []
handed_over: null
claim: null
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
