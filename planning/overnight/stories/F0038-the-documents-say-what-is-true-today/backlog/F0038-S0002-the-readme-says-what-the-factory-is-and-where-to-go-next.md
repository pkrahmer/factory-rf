# The README says what the factory is, that an instance runs in the container, and where to go next

## Description

`README.md` is for the newcomer: what it is, how to run it, where to look next (`CLAUDE.md`, *Docs*). Its first paragraph is a build inventory of about 3,000 characters on one line. It says the repository "is under construction" and that "what is built so far is the groundwork the pipeline will run on", then lists some 30 parts and dated observations ("the probe of 2026-10-17"). Since the handover of 2026-10-18 v1.1 builds this repository itself, so "groundwork" is stale, and a newcomer cannot tell what the factory is. Its *Getting started* paragraph lists the six console commands with their exit statuses in one sentence of about 1,200 characters and tells the newcomer to run `uv run factory-run`, while an instance runs in the container (its checkout is `/work/checkout` and its state `/state`); the exit statuses are the operator guide's. *Where to look next* does not name `docs/operator-playbook.md`, the fifth document. This story makes those three passages short and true (findings H2, M10 and M11 of the documentation review of 2026-10-20). The paragraph on `python -m factory.entry.contract` and `check_documents` keeps its text but its first words, which still count seven console commands from before F0041 removed `factory-guard`; *How it is built* and *Replaced from v1* stay as they are. The full rewrite of the README (the review's structural proposal S3) is the human's to decide and not part of this story.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `README.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `README.md`, and no other file:
   - The paragraph under the title becomes exactly: "The factory takes a feature, split into stories, through tests, code, review, documentation and a smoke test, one agent at a time (on Claude Code, or on opencode when the operator chooses it for an instance), and the human approves each story on its pull request. This repository is its second implementation, v1.1. The first (github.com/pkrahmer/factory) built it until the handover of 2026-10-18; since then v1.1 builds this repository itself (see *How it is built*). `docs/project-guide/README.md` maps every part of the code." The words "under construction", "groundwork" and "probe of 2026-10-17" no longer occur in the file.
   - *Getting started*: the code block and the sentence "When it works, `make check` ends with the line `check: green`." stay. The rest of that paragraph becomes one sentence, "An instance runs in the container: see *The container: compose, entrypoint and health check* in `docs/operator-guide.md`, which also gives the exit statuses of the commands you run.", and then a table with the header `| Command | What it does |` and exactly six rows, in this order, each starting `` | `factory-<name> ``: `factory-run` (runs one instance, one tick per iteration, until a signal stops it), `factory-check-story <path>...` (checks a story against the story form before it starts), `factory-bill [<work item id>]` (shows what a work item cost), `factory-watch` (shows what the next tick would do and the board of features and work items; it changes nothing), `factory-health` (prints `healthy`, or one line per stop in force), `factory-confine` (run by the agent runtime: starts every agent run with its writes confined by the kernel). No exit status is named in the table.
   - The paragraph that begins "Beside the seven console commands" begins "Beside the six console commands"; the rest of it stays.
   - *Where to look next* gains one bullet after the `docs/decisions.md` bullet: "`docs/operator-playbook.md`: how the human runs the factory day to day".
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -F -e 'under construction' -e 'groundwork' -e 'probe of 2026-10-17' -e 'seven console commands' -e 'factory-guard' README.md || true
grep -c '^| `factory-' README.md
grep -c -F -e '- `docs/operator-playbook.md`: how the human runs the factory day to day' -e 'see *The container: compose, entrypoint and health check* in `docs/operator-guide.md`' README.md
awk 'NR == 3 { print length($0) <= 700 }' README.md
```
Expect: four lines, `0`, `6`, `2` and `1` (no inventory, no count of seven and no `factory-guard`, six command rows, the playbook bullet and the container sentence, and a first paragraph of at most 700 characters)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `README.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
