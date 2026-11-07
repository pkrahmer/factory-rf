---
stage: docs-review
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 638
comments_read: [6707873070]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T13:57:33.067854Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T13:57:33.075344Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-07T13:57:54.282307Z'
  stage: intake
  run: c9cccc5f2a584650a680f57c2223c858
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-07T13:59:40.479661Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-07T13:59:42.854596Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-07T14:00:02.882984Z'
  stage: intake
  run: 6b82ed978aba45938b9c82b14bf02a48
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T14:00:08.086216Z'
  stage: docs-only
- number: 8
  speaker: documenter
  kind: result
  at: '2026-11-07T14:05:49.297825Z'
  stage: docs-only
  run: 153b93e798aa49fdafbbc504c38cae14
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-07T14:05:54.330244Z'
  stage: docs-review
- number: 10
  speaker: reviewer
  kind: result
  at: '2026-11-07T14:06:45.786591Z'
  stage: docs-review
  run: 40189e18bd5e4a6f8dfa2f262d09a538
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-07T14:06:50.747586Z'
  stage: docs-only
- number: 12
  speaker: documenter
  kind: result
  at: '2026-11-07T14:11:14.255009Z'
  stage: docs-only
  run: 768a5c9f736b4c699f214568d1ea3dd1
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-07T14:11:19.553967Z'
  stage: docs-review
- number: 14
  speaker: reviewer
  kind: result
  at: '2026-11-07T14:11:57.848833Z'
  stage: docs-review
  run: 364612c3987241758f48cc622788e116
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-07T14:12:02.844826Z'
  stage: docs-only
- number: 16
  speaker: documenter
  kind: result
  at: '2026-11-07T14:17:25.974922Z'
  stage: docs-only
  run: 285a5495a5564b49b871196842923b53
---

# The top folders say what they hold

## Description

This story writes the READMEs of `docs/` and `security/`, and the root `README.md`'s list of folders, in the form of feature decision 2: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. Each is added to `docs/checked-documents.txt`, so that its names and links are checked from now on, and the guard of the folder READMEs turns green for these folders. The facts come from the code and from the files' own docstrings and header comments, not from memory. No code and no test changes.

## Interface

- New files, each in the form of feature decision 2 (`docs/project-guide/style.md`, *Folder READMEs*):
  - `docs/README.md`
  - `security/README.md`
- `docs/README.md` names the four documents and who reads which (the operator guide, the project guide, the decision log, the operator playbook) and names `runs/` as the human's. `security/README.md` says what the baselines and the semgrep rules are for and links to `CLAUDE.md`, *Checks*. The root `README.md` gains a short list of the top folders, one line each with a link to its README where one exists.
- `docs/checked-documents.txt` gains each new path.
- No code changes, and no test changes but this one leave of the human's: an earlier guard whose only failure is a `README.md` of this story standing in its folder may add that README to the entries it expects, keeping its name's purpose; the entry names each such test. The story takes the docs route.

## Acceptance criteria

1. Each file of the Interface exists, opens with one sentence on what its folder holds, links to at least one guide page or document that explains it, and names every direct subfolder of its folder in one line ``- `<name>/` <one sentence>.`` (no colon, as the guard and the style page write it). The guard `tests/guards/test_folder_readmes.py` passes for each and skips none of them.
2. Every name, path and link in these files exists (the document check finds nothing), and each file is on `docs/checked-documents.txt`.
3. `make documents` ends with `documents ok (<seconds> s)`.
4. `docs/README.md` names the operator guide, the project guide, the decision log and the operator playbook, and says that `docs/runs/` is the human's.
5. `security/README.md` says what the baselines and the semgrep rules are for and links to `CLAUDE.md`, *Checks*.
6. The root `README.md` has a new section `## The folders`, placed after `## Where to read next` and before `## Reference`, in the subfolder-line form of `docs/project-guide/style.md`, *Folder READMEs*. It lists the ten top folders (`agents/`, `demo/`, `docs/`, `factory/`, `operator/`, `planning/`, `security/`, `session-logs/`, `src/`, `tests/`), one line each, links to each folder's README that exists, and says in their lines that `factory/`, `planning/` and `session-logs/` are the human's. `## Where to read next` is unchanged.
7. `make check` stays green.
8. docs: the files of the Interface. A newcomer who opens `docs/` or `security/` on GitHub knows which document to read for which need, who owns `docs/runs/`, and what the baselines and the semgrep rules in `security/` are for; the root README's `## The folders` points them to each folder's README. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed, no findings):

   1. The Interface states behaviours that no criterion covers. (a) `docs/README.md` names the four documents and who reads which (operator guide, project guide, decision log, operator playbook) and names `runs/` as the human's. (b) `security/README.md` says what the baselines and the semgrep rules are for and links to `CLAUDE.md`, *Checks*. (c) The root `README.md` lists the top folders, one line each, with a link to its README where one exists. Criterion 1 only covers shape (opening sentence, a link, subfolder lines) and criterion 2 only that names and links exist. Two documenters could satisfy both and still leave out (a), (b) or (c). Proposal: add a criterion per item. For (a), `docs/README.md` names the operator guide, the project guide, the decision log and the operator playbook, and says `docs/runs/` is the human's. For (b), `security/README.md` says what the baselines and the semgrep rules are for and links to `CLAUDE.md`. For (c), the root `README.md` lists every top folder (`agents/`, `demo/`, `docs/`, `factory/`, `operator/`, `planning/`, `security/`, `src/`, `tests/`) and links to each README that exists. Please confirm the exact set of top folders for (c). I would choose the list above.

   2. The docs criterion (5) names only files. It does not say what the reader must know afterwards. Proposal: a newcomer who opens `docs/` or `security/` on GitHub knows which document to read for which need, and who owns `docs/runs/`. They also know what the baselines and the semgrep rules in `security/` are for, and that the root README's folder list points them to each folder's README. Please confirm or reword.

   3. The root `README.md` is a docs-route path the documenter may write, but the Interface does not say where the folder list goes or how it relates to any existing folder list in it. Is it a new section, or does it replace an existing one?

   The rest checks out. The smoke test runs the document check, which exists. The Interface changes only paths on the documenter's write paths (`docs/*`, `README.md`, `security/README.md`). `docs/README.md` and `security/README.md` are already on the folder list in `folder_readmes.py`. `docs/` has three subfolders (`operator-guide/`, `project-guide/`, `runs/`) and `security/` has one (`semgrep/`). The scope fits the feature, and the story is not in "Out of scope" because `docs/runs/` is only named in the README, not written.
4. 2026-11-07 human: 1. Yes, one criterion each for (a), (b) and (c). For (c) the top folders are agents/, demo/, docs/, factory/, operator/, planning/, security/, session-logs/, src/ and tests/: ten folders, one line each, with a link to each README that exists. Say in their lines that factory/, planning/ and session-logs/ (and docs/runs/ in docs/README.md) are the human's.
   2. Confirmed as you wrote it.
   3. A new section, ## The folders, placed after ## Where to read next and before ## Reference. The root README has no folder list today; Where to read next stays as it is and the new section does not repeat it. The root README is not on FOLDER_READMES and keeps its own form; its new section follows the subfolder-line form of style.md, *Folder READMEs*.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) carried into the story.
   - Interface: names `docs/README.md`, `security/README.md` and the root `README.md` (new section `## The folders`, after `## Where to read next`, before `## Reference`, per entry 4 answer 3). Every path is one the documenter may write, so the route is docs-only. The existing test-leave sentence is the human's own and stays.
   - Criteria: I added criteria 4, 5 and 6, one each for (a) docs/README.md, (b) security/README.md and (c) the root folder list, from entry 4 answer 1: ten top folders, links to each README that exists, and factory/, planning/ and session-logs/ named as the human's. Criteria 7 (`make check`) and 8 (`docs:`) now close the list. Criterion 1 covers the shape and the subfolder lines, which cover the failing side too, since the guard fails on a missing or extra line. Each criterion is testable.
   - Smoke test: `uv run python -m factory.entry.check_documents | tail -1` runs no pytest, so there is no `-q` problem. Its `Expect:` is checkable.
   - Docs criterion: criterion 8 now says what the reader must know (entry 4 answer 2) and dictates no sentences.
   - Architecture: nothing is changed in code. The files are READMEs on the folder list.
   - Scope: this is S0005 of F0055. `docs/runs/` is only named, not written, and the story is not in the feature's Out of scope. The Description did not change.
7. factory: started docs-only as vm.
8. documenter: Files changed:
   - `docs/README.md` (new): opening sentence, a link to the project guide, one line each for `operator-guide/`, `project-guide/` and `runs/`. It names `decisions.md` and `operator-playbook.md` and says `runs/` is the human's.
   - `security/README.md` (new): says the semgrep rules serve `make sast` and `duplicates-baseline.txt` serves `make duplicates`. It links `CLAUDE.md`, *Checks*, and has one line for `semgrep/`. The baseline text is in the opening because the form allows no other prose; my first draft had an extra paragraph and the guard failed on it ("line 7 is no part of the form").
   - `README.md`: new section `## The folders` between `## Where to read next` and `## Reference`. It has ten lines in the subfolder-line form, with links to the READMEs that exist (agents, demo, docs, operator, planning, security, src/factory, tests). `factory/`, `planning/` and `session-logs/` are marked as the human's. `## Where to read next` is untouched, and its existing `agents/` line also stays.
   - `docs/checked-documents.txt`: added `docs/README.md` and `security/README.md`.

   Checks: `make documents` ends with `documents ok (58.8 s)`. `uv run pytest -q tests/guards/test_folder_readmes.py` passes, so the guard is green for both new folders. I did not run `make check`, because I changed only documents. I changed no tests and no code.

   Cross-read and found current: the root `README.md` and `docs/project-guide/style.md` (*Folder READMEs*), against the code of `folder_readmes.py`, the `Makefile` targets `sast` and `duplicates`, and the contents of `security/`.

   Open or noted:
   - `session-logs/` does not exist on this branch. `.gitignore` excludes it, as "Local copies of the session transcripts (the human, 2026-10-15)". The root line is written without a link. The name check did not flag it.
   - Stale text, not touched because it is unrelated to this story: the `agents/` line in `## Where to read next` of the root README now duplicates the new `## The folders` line. Criterion 6 says to leave `## Where to read next` unchanged, so I left it.
   - `docs/decisions.md` is untouched, as the docs criterion says.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (60.1 s)
9. factory: started docs-review as vm.
10. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md` and the work item. I also read `security/README.md`, because criteria 1, 2 and 5 name it. I checked the facts against `src/factory/shared/domain/folder_readmes.py`, the `Makefile` targets `sast` and `duplicates`, the contents of `security/`, `docs/`, `docs/runs/` and `.gitignore`, the READMEs the root section links to, and the human's own files `CLAUDE.md` and `planning/README.md`. I checked the writing against `docs/project-guide/style.md`, *Folder READMEs*.

    Findings:
    1. `security/README.md:3` ("The vendored semgrep rules"): the rules in `security/semgrep/python.yml` are this project's own (ids `factory-no-eval-exec`, `factory-no-subprocess-shell`). They are not copied from an outside source, and line 5 of the same README calls them "The semgrep rules of this project". "Vendored" is a word of the demo project (`demo/todo-service/README.md:9`), not of this one. Fix: drop "vendored", e.g. "The semgrep rules that `make sast` applies".
    2. `docs/README.md:7` ("The human's records of finished runs and sweeps"): `docs/runs/` holds run logs and reports only (`2026-10-12-overnight`, `2026-10-19-baseline-todo`, `2026-11-04-f0050`, `2026-11-05-f0052`). The mutation sweep reports are in `planning/` (`planning/README.md:3`). Fix: "The human's logs and reports of finished runs".
    3. `docs/README.md:7` ("no stage reads or writes them"): `CLAUDE.md`, *The human's files*, says only that no stage edits `docs/runs/` and that it is outside every write path. Nothing keeps a stage from reading it; `not_read` in `factory/pipeline.yml` is about what `make check` reads, not what agents read. Fix: "no stage writes them", as `CLAUDE.md` says.

    Checked and found true: the root `## The folders` section sits between `## Where to read next` (unchanged) and `## Reference`. It has ten lines in the subfolder-line form, and links to the six READMEs that exist (`src/` links to `src/factory/README.md`; `src/` itself has no README). It names `factory/`, `planning/` and `session-logs/` as the human's, and `session-logs/` is ignored in `.gitignore:15-16`. `docs/README.md` names all four documents and has a line for each of the three subfolders. `security/README.md` matches the `sast` and `duplicates` targets and links `CLAUDE.md`, *Checks*. `docs/checked-documents.txt` gains both paths. The trailing link sentence of `docs/README.md` passes the guard (`_read_line` takes any line with a link) and serves criterion 8; I left it as it is.
11. factory: started docs-only as vm.
12. documenter: Fixed the reviewer's three findings and nothing else.

    Files changed:
    - `security/README.md`: finding 1. "The vendored semgrep rules that `make sast` applies" is now "The semgrep rules that `make sast` applies". The rules are this project's own.
    - `docs/README.md`: findings 2 and 3. The `runs/` line now reads "The human's logs and reports of finished runs; no stage writes them." This matches `CLAUDE.md`, *The human's files*, and the run logs and reports that `docs/runs/` actually holds.

    `make documents` ends with `documents ok (61.1 s)`. I changed only documents, so I did not run `make check`. The factory runs it after this stage.

    Cross-read and found current: the root `README.md` section `## The folders`, which the reviewer had already checked against the code.

    Open:
    - `session-logs/` does not exist on this branch (`.gitignore` excludes it). The root line for it has no link.
    - The `agents/` line in the root `## Where to read next` now duplicates its line in `## The folders`. Criterion 6 says to leave `## Where to read next` unchanged, so I did not touch it.

    `check`: check: green
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok (59.7 s)
13. factory: started docs-review as vm.
14. reviewer: Reviewed the work item and `git diff main...HEAD -- README.md docs operator/README.md`. I also read `security/README.md`, because criteria 1, 2 and 5 name it. I checked the facts against `planning/README.md`, `agents/README.md`, `demo/README.md`, `operator/README.md`, `src/factory/README.md`, the contents of `docs/` and `security/`, and the glossary. I checked the writing against `docs/project-guide/style.md`: *Rules for all documents*, *Folder READMEs* and *The README*.

    Findings:
    1. `README.md:40`, the `factory/` line of `## The folders`: "pipeline definition" is a glossary word (`docs/project-guide/glossary.md:18`), and this line is its first use in the root README. It has no link, which breaks rule 3 of *Rules for all documents* in `style.md`. Every other glossary word in this README is linked at its first use (stories, feature, instance, stops, tick, work item, stage, dataset). Fix: link it, e.g. "the [pipeline definition](docs/project-guide/glossary.md), the forms and ...".

    Checked and found true:
    - The round-0 findings are fixed. `security/README.md:3` no longer says "vendored". The `runs/` line in `docs/README.md:7` reads "logs and reports of finished runs; no stage writes them", which matches `CLAUDE.md`, *The human's files*.
    - The `planning/` line ("no stage reads or writes") matches `planning/README.md:3`, the human's own file.
    - `docs/README.md` names the four documents and says `runs/` is the human's (criterion 4).
    - `security/README.md` names the semgrep rules and the duplicates baseline and links to `CLAUDE.md`, *Checks* (criterion 5).
    - `## The folders` sits between an unchanged `## Where to read next` and `## Reference`. It has ten lines in the subfolder-line form and links to the eight READMEs that exist. It names `factory/`, `planning/` and `session-logs/` as the human's (criterion 6).
    - `docs/checked-documents.txt` gains both paths. The documenter's last run ended `documents ok`.
15. factory: started docs-only as vm.
16. documenter: Fixed the reviewer's one finding (round 2) and nothing else.

    Files changed:
    - `README.md`: the `factory/` line of `## The folders` now links "pipeline definition" to `docs/project-guide/glossary.md` at its first use in the root README, as rule 3 of *Rules for all documents* in `style.md` asks. (My first edit hit the wrong line and changed nothing; I checked and applied it to line 40.)

    `make documents` ends with `documents ok (58.3 s)`. I changed only a document, so I did not run `make check`; the factory runs it after this stage.

    Cross-read and found current: `docs/README.md`, `security/README.md` and the rest of `## The folders`, which the reviewer already checked.

    Open or noted, not mine to fix:
    - `session-logs/` does not exist on this branch (`.gitignore` excludes it), so its root line has no link.
    - The `agents/` line in `## Where to read next` duplicates its line in `## The folders`. Criterion 6 says to leave `## Where to read next` unchanged.

    `check`: check: green
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok (58.9 s)
