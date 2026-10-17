---
stage: accept
pr: 198
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# What the first start observed, in the guide

## Assignment (as of log entry 1)

The first start of 2026-10-17 (`planning/overnight/first-start-checklist.md`, "Results", fault 4) found two places where the operator guide is wrong or silent. A folder an agent makes in the checkout is `2775`, not `775`: `/work` is setgid (`2775`), so a new folder inherits the bit and its group `factory-work`, and `stat -c %a` prints `2775`; a file is `664` as written. And under Podman on Windows, the operator's shell (PowerShell) may not see the saved connection of the Podman machine: a `podman` command then fails with `connection "podman-machine-default" not found`; `podman system connection list`, in a shell that sees it, shows the connection's URI and identity file, and `--url` and `--identity` on the command name them directly. The place of the agent's login, the third point of fault 4, belongs to S0004's text, which rewrites that paragraph. This story is documentation only: nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes; the tester and the coder each end with an entry saying so. The docs criterion carries the text. It is built after S0004, which rewrites the paragraphs around it; S0007 and S0008 follow it.

## Interface

None: no code, no image file and no test changes. The document the documenter changes is `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in the operator guide's morning observations of *The agent runs as a second user*, the row "The mode of what an agent makes" expects "`2775` for the directory, `664` for the file", written so, and says why: `/work` is setgid, so a folder made in it keeps the bit and the group `factory-work` (seen at the first start of 2026-10-17 under Docker Desktop and Podman). *Podman: the commands* (under *Container runtimes*) gets a paragraph: on Windows a shell may not see the Podman machine's saved connection, and a command then fails with `connection "podman-machine-default" not found` (seen at the first start in PowerShell); `podman system connection list`, run where the connection is seen, shows its URI and identity file; give them on each command with `podman --url <URI> --identity <identity file> ...`, for example `podman --url <URI> --identity <identity file> ps`; whether `podman compose` hands them on to its Compose provider is not observed, so run `compose` from a shell that sees the connection. No other document changes, the guide uses no word the document check refuses, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -o '`2775` for the directory\|podman-machine-default\|podman system connection list\|--identity' docs/operator-guide.md | sort -u
```
Expect: four lines, one per term, in any order: the text 2775 in backticks followed by ` for the directory`, `podman-machine-default`, `podman system connection list` and `--identity`.

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: "None" is correct for a documentation-only story; the only file changed is `docs/operator-guide.md`, and the row (line 134, now `775`) and the section `### Podman: the commands` (line 341, under `## Container runtimes`) that criterion 3 names both exist.
   - Criteria: 1 (no change under src/image/template/claude/tests) and 2 (`make check`) are the pipeline's usual closing and scope criteria. Criterion 3 gives the exact text, the reason, and the exact command shapes, so the documenter has no decision left. The story states no code rule, so there is no failing side to cover. The format check passed, so I did not check form again.
   - Demo: the grep and `check_documents` commands are runnable. Each Expect line is checkable: four terms (`2775` for the directory, `podman-machine-default`, `podman system connection list`, `--identity`) and `documents ok`.
   - Architecture: no layer is touched, so no architecture rule applies.
   - Scope: it is within F0014's scope, which lists S0005 as documentation only with the `2775` fix and the Podman connection on Windows. The login's place is left to S0004, as the feature says.
3. tester: no tests written; nothing under `tests/` (or `src/`, `image/`, `template/`, `claude/`) changed, as criterion 1 asks.
   - Criterion 1 (nothing under src/image/template/claude/tests changes): kept by writing nothing; the working tree is clean.
   - Criterion 2 (`make check` stays green): the factory's gate. I ran `make lint` and it is green.
   - Criterion 3 (docs: the `2775`/`664` row and the Podman connection paragraph in `docs/operator-guide.md`): this is the documenter's text. The document check (`python -m factory.entry.check_documents`) and the demo's grep cover it. A pytest test on the guide's wording would change `tests/`, which criterion 1 forbids.
   - Files created: none. Modules the test runner could not import: none, since there are no new tests. I did not run `make test` because there are no new red tests to confirm.
   - Open: nothing for the coder to implement. The coder ends with an entry saying nothing changed, and the documenter writes criterion 3.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (30.3 s)
4. coder: nothing implemented. This story is documentation only, and nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changed (criterion 1). I made no commit.
   - Criterion 1: kept, because I wrote nothing. The working tree is clean.
   - Criterion 2: I ran `make check` on the branch as it stands, and it ended with `check: green` (`test: green (30.0 s)`, coverage 99.46 %).
   - Criterion 3 is the documenter's: the `2775`/`664` row in *The agent runs as a second user* and the Podman connection paragraph in *Podman: the commands*, both in `docs/operator-guide.md`. The coder does not write docs.
   - Refactor: no diff, so nothing to refactor.
   - Open: the documenter writes criterion 3's text.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Diff: `git diff main...HEAD -- . ':!factory'` is empty. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changed, and the tester's and the coder's entries both say so (criterion 1).
      - Criterion 2: the coder's entry records `make check` as `check: green` on the unchanged branch, and `make duplicates` reported 0 new findings.
      - Criterion 3 is the docs stage's job. Its text names the row ("The mode of what an agent makes"), the expected value (`2775` for the directory, `664` for the file) and the reason (setgid `/work`, group `factory-work`). It also gives the whole Podman connection paragraph for *Podman: the commands*, including the unobserved `compose` case, so the documenter has nothing left to decide.
      - Architecture, security and quality: no code changed, so none of these rules applies.
      - Ticket hygiene: `Assignment` matches what was built, which is nothing yet. The log explains why the tester and the coder wrote nothing, and the docs criterion still says what the operator must know.
6. documenter: changed only `docs/operator-guide.md`.
   - Row "The mode of what an agent makes" (*The agent runs as a second user*): expects `2775` for the directory, `664` for the file, with the reason (setgid `/work`, group `factory-work`, seen at the first start of 2026-10-17 under Docker Desktop and Podman).
   - *Podman: the commands*: new paragraph on the Podman machine's connection not being seen from a Windows shell (`connection "podman-machine-default" not found`), `podman system connection list`, `--url`/`--identity` with an example, and the unobserved `podman compose` case.
   - `uv run python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check` because I changed only docs. I could not run the Podman example, because there is no Podman here. Its text is the criterion's.
   - Cross-read: the rest of the guide against an empty code diff, found current. Nothing stale seen. No findings.

   `make check`: check: green
   `make documents`: documents ok
7. demo: both commands met their Expect lines, and no criterion is contradicted.

   1. `grep -o '`2775` for the directory\|podman-machine-default\|podman system connection list\|--identity' docs/operator-guide.md | sort -u`
   ```
   --identity
   `2775` for the directory
   podman system connection list
   podman-machine-default
   ```
   Met: four lines, one for each term.

   2. `uv run python -m factory.entry.check_documents`
   ```
   documents ok
   ```
   Met.

   Criteria check:
   - Criterion 1 holds. `git diff --stat main...HEAD` lists only `docs/operator-guide.md` (4 +-) and the ticket. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changed.
   - Criterion 2: the coder and the documenter both recorded `check: green`. The factory runs the gate again after this stage.
   - Criterion 3 holds. Line 134 of the guide (row "The mode of what an agent makes") expects "`2775` for the directory, `664` for the file" and gives the setgid/`factory-work` reason for the 2026-10-17 first start. Line 345, in *Podman: the commands*, has the Windows connection paragraph with the error text, `podman system connection list`, the `--url`/`--identity` form with the `ps` example, and the unobserved `compose` caveat. The document check prints `documents ok`.

   No findings.
