---
stage: accept
pr: 189
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# What the probe observed, in the documents

<!-- proposed by feature acceptance of 2026-10-17; refine before promoting -->

## Assignment (as of log entry 1)

The probe of 2026-10-17 (`planning/overnight/podman-probe-2026-10-17.md`), F0013's input, built v1.1's image under rootless Podman 5.8.3 on Windows (in a throwaway clone, the pins left out, because they were placeholders then), started it, and saw the entrypoint install the agents, the disk record written, the stop `repository_unavailable` reached and the health check run (`starting`, then the stop's text, exit 1). F0013-S0005 wrote this into the new section *Container runtimes* ("The image and the compose file run under Docker Desktop and under rootless Podman"). Four older sentences still say that nothing was observed, and so contradict it for a newcomer who reads from the top: `README.md` ("a real container is not yet observed"), the operator guide's introduction (the same words), its section *Build it* ("A real build is not yet observed: v1's container has no Docker ... Treat the first build as the morning observation") and *The health check and the restart policy* ("A real running container has not been observed yet"). The heading *Replace the placeholders before the first build* is stale too: the human's commit `b642dd31` pinned the image, and the section's own text already says so. This story is documentation only: nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes; the tester and the coder each end with an entry saying so. The docs criterion carries the text.

## Interface

None: no code, no image file and no test changes. The documents the documenter changes are `README.md` and `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `README.md` and the operator guide's introduction say, in place of "a real container is not yet observed", that the image was built and started once under rootless Podman (the probe of 2026-10-17, without the pins) up to the stop `repository_unavailable`, and that a run against a real repository with a token is not observed yet. *Build it* says the same of the build (42 s under Podman, without the pins) and keeps a build with the pins of `image/Dockerfile` as the morning observation. *The health check and the restart policy* says that the probe saw the health check run under Podman and report the stop's text with exit 1, and keeps `docker compose ps` over a container with a stop standing as the morning observation. The heading *Replace the placeholders before the first build* becomes *Update the pins*, its text unchanged. No other document changes, the guide uses no word the document check refuses, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -c "not yet observed\|not been observed\|Replace the placeholders" README.md docs/operator-guide.md
```
Expect: two lines, `README.md:0` and a count for `docs/operator-guide.md` that is lower than 4 (only the observations still open, such as the restart service on a Linux host, may remain).

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-17 feature acceptance of F0013: proposed.
2. intake: accepted
   - Interface: "None", which is right for a documentation-only story. It names the two documents that change (`README.md`, `docs/operator-guide.md`) and no code, image file or test. It states no behaviour, so no Interface comment needs a criterion.
   - Criteria: each is checkable by a person or a command. 1 is a diff check on `src/`, `image/`, `template/`, `claude/` and `tests/`. 2 is `make check`. 3 (docs) names each sentence and heading to change, and `documents ok` checks the guide. The story states no limit, validation or error, so no failing side is missing.
   - Demo: both commands run. I ran the grep on the current tree: `README.md:1` and `docs/operator-guide.md:4` (lines 3, 147, 149 and 248 of the guide). The Expect line is checkable: README 0, and the guide below 4 once the four stale sentences and the heading change. The second command prints `documents ok`.
   - Architecture: nothing under `src/` changes, so the layers are untouched. The documenter's write paths cover `README.md` and `docs/*`.
   - Scope: it is the F0013 documentation follow-up from the probe of 2026-10-17. It is not in the feature's Out of scope, and it follows decision 16's order (S0006 and S0007 are built before the second acceptance).
3. tester: no test written, as criterion 1 requires. This story only changes documents: its Interface is "None", and the only thing that changes is the text of `README.md` and `docs/operator-guide.md`.
   - criterion 1 (nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes): I changed nothing in those folders. Before I ended, `git status` showed a clean working tree.
   - criterion 2 (`make check` stays green): the factory checks this itself. No test needed.
   - criterion 3 (docs): the documenter's criterion. `python -m factory.entry.check_documents` and the Demo grep check it, not a pytest test.
   Files created: none. Modules the test runner could not import: none, because no new test exists. I did not run `make test`: no test was added, so none can fail for this story. `make lint`: green.
   Rejected: a test that greps the docs for the stale sentences. Criterion 1 forbids changes under `tests/`, and the document check already covers the docs.
   Open: nothing for the coder to implement. The coder ends with an entry saying nothing under the five folders changed, and the documenter writes criterion 3.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (28.1 s)
4. coder: nothing implemented and no commit, because criterion 1 says so. This story only changes documents, its Interface is "None", and the tester added no test.
      - criterion 1: I left `src/`, `image/`, `template/`, `claude/` and `tests/` untouched. `git status` showed a clean working tree when I finished.
      - criterion 2: I ran `make check` on the branch and it ended with `check: green` (test: green, coverage 99.50 %).
      - criterion 3 (docs) belongs to the documenter. It needs: README.md and the operator guide's introduction, *Build it*, *The health check and the restart policy*, and the heading *Replace the placeholders before the first build* renamed to *Update the pins*.
      Refactor: no diff, so nothing to clean up.
      Rejected: making the documentation edits myself. The coder does not write `README.md` or `docs/` (CLAUDE.md, Docs).
      Open: nothing for the reviewer in code. The documenter does criterion 3.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Scope: `git diff main...HEAD -- . ':!factory'` is empty. Its `--stat` lists no file, so the branch only changes the ticket.
      - 1. Acceptance criteria: criterion 1 holds because nothing changed under `src/`, `image/`, `template/`, `claude/` or `tests/`. The tester's and the coder's entries both say so. Criterion 2: the coder's entry records `make check` ending with `check: green` and `duplicates: 0 new`. The Interface is "None" and states no rule or limit, so no test is owed and no failing side is missing. Criterion 3 (docs) is the documenter's work next.
      - 2. Architecture, 3. Security, 4. Quality: no code changed, so nothing to judge.
      - 5. Ticket hygiene: the log gives the main decision (documentation only, no test and no code) and what was rejected (a grep test under `tests/`, and the coder writing the documents). The Assignment matches what was built, which is nothing outside the ticket. The docs criterion names each sentence and heading the documenter changes: README and the guide's introduction, *Build it*, *The health check and the restart policy*, and the heading becoming *Update the pins*. It also says that `documents ok` must still print.
      Open: the documenter writes criterion 3. The Demo grep then expects `README.md:0` and a count below 4 for `docs/operator-guide.md`.
6. documenter: wrote criterion 3; documents only, so I did not run `make check` (the factory runs it).
   Files changed:
   - `README.md`: "a real container is not yet observed" now says the image was built and started once under rootless Podman (probe of 2026-10-17, without the pins) up to the stop `repository_unavailable`, and that a run against a real repository with a token is not observed yet.
   - `docs/operator-guide.md`, introduction: the same replacement.
   - `docs/operator-guide.md`, *Build it*: the probe's build took 42 s under Podman 5.8.3 without the pins. A build with the pins of `image/Dockerfile` stays the morning observation. I dropped the "v1's container has no Docker" sentence because it is no longer true.
   - `docs/operator-guide.md`, *The health check and the restart policy*: the probe saw the health check run under Podman, report `starting`, then the stop's text, exit 1. `docker compose ps` over a container with a stop standing stays the morning observation.
   - `docs/operator-guide.md`: the heading *Replace the placeholders before the first build* is now *Update the pins*, and its text is unchanged. Nothing else in the repository linked to the old heading.
   Checks: the Demo grep gives `README.md:0` and `docs/operator-guide.md:0`, which meets "lower than 4". `uv run python -m factory.entry.check_documents` prints `documents ok`.
   Cross-read: the *Container runtimes* section and the remaining "Morning observation" paragraphs (the second user and sudo rule, the agent run, the Linux `podman-restart.service`) are current and still open, so I left them. The code contradicts nothing. No findings, and no unrelated stale prose seen.

   `make check`: check: green
   `make documents`: documents ok
7. demo: both commands ran from the repository root and both met their `Expect:` lines. No findings.

   1. `grep -c "not yet observed\|not been observed\|Replace the placeholders" README.md docs/operator-guide.md`
   ```
   README.md:0
   docs/operator-guide.md:0
   ```
   Met: two lines, `README.md:0`, and the guide's count of 0 is below 4.

   2. `uv run python -m factory.entry.check_documents`
   ```
   documents ok
   ```
   Met.

   Criteria checked against `git diff main...HEAD`:
   - Criterion 1 holds. Besides the ticket, the diff touches only `README.md` (1 line) and `docs/operator-guide.md` (4 lines). Nothing changes under `src/`, `image/`, `template/`, `claude/` or `tests/`, and the tester's and coder's entries both say so.
   - Criterion 2: the coder's and documenter's entries record `check: green`, and the factory runs `make check` again after this stage. I did not run it here.
   - Criterion 3:
     - README and the guide's introduction now say the image was built and started once under rootless Podman (the probe of 2026-10-17, without the pins) up to the stop `repository_unavailable`. They also say a run against a real repository with a token is not observed yet.
     - *Build it* gives 42 s under Podman 5.8.3 without the pins, and keeps a build with the pins as the morning observation.
     - *The health check and the restart policy* says the probe saw the health check run under Podman: `starting`, then the stop's text, exit 1. It keeps `docker compose ps` over a container with a stop standing as the morning observation.
     - The heading is now *Update the pins*, and its text is unchanged (only the heading line is in the diff).
     - No other document changed, and the document check still prints `documents ok`.

   The demo contradicts no criterion. Open: nothing.
