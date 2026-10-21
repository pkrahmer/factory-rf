# The decision log records the human's answer on F0037's decision 4

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

`docs/decisions.md` has the entry *A record line that is not UTF-8 is skipped* (F0037-S0001). It ends with "Open (decision 4): a record appended after a torn line lands on the torn line's line and is skipped with it. A later story may start a new line first." The human answered decision 4 on 2026-10-20, after that entry was written: it is left, and no later feature makes `append` start on a new line after a torn one. The answer is in F0037's `feature.md` (decision 4) and nowhere in the documents. An agent that reads the decision log before it changes the record log would find the point still open and might propose the change the human turned down. This story replaces the entry's open point with the answer and its reason: before each append the writer would have to read the file's last byte, which two writers can race, and the loss is one telemetry record per kill. It changes no code and no test. The project guide's sentence that a record appended after a torn line shares its line and is skipped with it stays as it is, because it is still true.

## Interface

None: no module under `src/factory/` changes and no test is written. The documenter changes `docs/decisions.md` only.

## Acceptance criteria

1. Nothing under `src/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/decisions.md`, the entry *A record line that is not UTF-8 is skipped*. The bullet "Open (decision 4): …" becomes a bullet that starts with "Answered (decision 4, the human, 2026-10-20):". It says that a record appended after a torn line still lands on the torn line's line and is skipped with it, and that no later feature changes `append`. Its reason is that the writer would need to read the file's last byte before each append, which two writers can race, while the loss is one telemetry record per kill. The entry's date line names decision 4 beside 1, 2, 3 and 5. No other entry and no other document changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "A later story may start a new line first" docs/decisions.md; grep -c "Answered (decision 4, the human, 2026-10-20)" docs/decisions.md
```
Expect: `0`, then `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal
