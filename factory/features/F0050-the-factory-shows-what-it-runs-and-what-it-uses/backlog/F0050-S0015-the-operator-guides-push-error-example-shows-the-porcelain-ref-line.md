# The operator guide's push error example shows the ref line the factory writes

<!-- proposed by feature acceptance of 2026-11-05; refine before starting -->

## Description

The operator guide's example of a counted handler error (`docs/operator-guide.md:2487`, written by F0050-S0008) reads `... PushFailed: push of work-item/F0001-S0001 failed: rejected: remote: Internal Server Error | ! [remote rejected] work-item/F0001-S0001 -> work-item/F0001-S0001 (Internal Server Error)`. That is git's human-readable ref line (`! [remote rejected] <from> -> <to> (<reason>)`). The factory never gets that form, because it pushes with `git push --porcelain` (`GitCli.push`), and `push_reason` turns the porcelain ref line `!<tab>refs/heads/<b>:refs/heads/<b><tab>[remote rejected] (<reason>)` into `! refs/heads/<b>:refs/heads/<b> [remote rejected] (<reason>)`. The feature acceptance F0050-A0003 shows that form in every retry line of its walk-through. An operator who searches the factory log for the example's `-> work-item/` finds nothing. The sentence two paragraphs further on, "a refusal by the server (git's `! [remote rejected]`, ...)", names a string that does not occur in the factory's reasons either: the `!` and `[remote rejected]` are separated by the refs. This story rewrites the example line in the porcelain form and names the marker as `[remote rejected]`, the text `push_is_retried` looks for (`SERVER_REFUSAL`). The rule, the code and the decision log's entries, which are history, stay as they are.

## Interface

- No module under `src/factory/` changes, and no test is written.
- `docs/operator-guide.md`, the example under the handler-error lines: the ref line becomes `! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (Internal Server Error)`, and the rest of the line stays as it is.
- `docs/operator-guide.md`, *A refused push is tried again*: "git's `! [remote rejected]`" becomes "git's `[remote rejected]` on the refused ref's line".

## Acceptance criteria

1. The handler-error example in `docs/operator-guide.md` reads `2026-11-04T09:40:41Z handler error <event key> 2 of 3: PushFailed: push of work-item/F0001-S0001 failed: rejected: remote: Internal Server Error | ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (Internal Server Error)`, and no line of the guide holds `-> work-item/` any more.
2. The paragraph *A refused push is tried again* names the server's refusal as git's `[remote rejected]` on the refused ref's line, and `docs/operator-guide.md` no longer holds the string `` `! [remote rejected]` ``.
3. No other paragraph of `docs/operator-guide.md` changes, and `docs/decisions.md` does not change.
4. `make check` stays green.
5. docs: `docs/operator-guide.md` as criteria 1 to 3 say. `README.md`, the project guide and `docs/decisions.md`: none. The project guide already describes the porcelain form (`docs/project-guide/git-and-hosting.md`), and the decision log's entries are history.

## Smoke test

```bash
grep -c '! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 \[remote rejected\] (Internal Server Error)' docs/operator-guide.md
```

Expect: `1`.

```bash
grep -c -e '-> work-item/' -e '`! \[remote rejected\]`' docs/operator-guide.md
```

Expect: `0`.

```bash
uv run python -c 'from factory.domain.git import push_reason; print(push_reason("!\trefs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001\t[remote rejected] (Internal Server Error)\nDone\n"))'
```

Expect: `! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (Internal Server Error)`, the ref line of criterion 1's example.

## Journal
