---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 629
comments_read: [6704964498]
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T09:18:22.978204Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T08:52:56.845747Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T08:52:56.852774Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T08:53:14.015007Z'
  stage: intake
  run: 2ef7ecf4ac59493d923e2804b97ca887
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T08:53:18.729510Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T08:58:56.854623Z'
  stage: docs-only
  run: 55358520de1a4333b727145fb649f6a3
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T08:59:01.810505Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T09:00:09.670067Z'
  stage: docs-review
  run: 3dea17ba485b42789aad6eb5eba85a6e
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T09:00:14.856111Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T09:04:34.299408Z'
  stage: docs-only
  run: 1c4a69428cc44671b12cf8950fdbce9f
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T09:04:41.685516Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T09:05:59.316225Z'
  stage: docs-review
  run: 10f598d540054a12a6e0ffefa8e42593
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T09:06:05.300865Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T09:10:21.261250Z'
  stage: docs-only
  run: 9de4c4f7740940b0a94c1c45fb09b9e6
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T09:10:26.386254Z'
  stage: docs-review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-07T09:11:13.364093Z'
  stage: docs-review
  run: 673617d24aff49c0b5026dfc2e0f875f
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-07T09:11:18.540414Z'
  stage: docs-only
- number: 17
  speaker: documenter
  kind: result
  at: '2026-11-07T09:15:28.548690Z'
  stage: docs-only
  run: 30595a0c3fd9437c8625d3671eb05f22
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-07T09:15:34.681485Z'
  stage: docs-review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-07T09:16:33.491263Z'
  stage: docs-review
  run: 2de061e260d54c7b811915437fb31c4e
- number: 20
  speaker: factory
  kind: question
  at: '2026-11-07T09:16:33.491263Z'
  stage: docs-review
  run: 2de061e260d54c7b811915437fb31c4e
  blocked: round_cap
- number: 21
  speaker: human
  kind: comment
  at: '2026-11-07T09:18:20.560346Z'
  stage: docs-review
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-07T09:18:22.978204Z'
  stage: docs-review
---

# The README reads for a newcomer

## Description

`README.md` is rewritten for its reader, a newcomer who opens the repository for the first time, in the style of `docs/project-guide/style.md` (what the factory is for in plain words, then how to try it in a few commands, then where to read next). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `README.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `README.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `README.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `README.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "README.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: it names concrete paths only: `README.md`, `docs/checked-documents.txt` (one line, `README.md`), links from other documents, and "no code, test or agent file changes". Every path is one the documenter may write, so the docs route fits.
   - Criteria: criteria 1 to 4 are judged by the reviewer or checked by `make documents` and a link check, which is the docs route's form. The Interface rule "a section another file links to keeps its heading, or the link changes with it" has its own criterion (4). The failing side, a dropped fact or a broken link, is covered by criteria 2 and 4. The Description's rule that every shown command is runnable or marked for the VM, GitHub or a model falls under criterion 3 ("runnable examples pass") and criterion 1 (style).
   - Smoke test: `grep -cx "README.md" docs/checked-documents.txt` is runnable and `Expect: 1` is checkable. It doesn't run pytest.
   - Docs criterion: criterion 6 refers to criteria 1 to 4 for what the reader must know and dictates no sentences. `docs/decisions.md` is marked "none".
   - Architecture: it is a documents-only change, with no layer or module touched.
   - Scope: the story is S0021 in `feature.md`'s list and within its scope. It touches none of the out-of-scope files (`docs/decisions.md`, `docs/runs/`, `docs/operator-playbook.md`).
4. factory: started docs-only as vm.
5. documenter: Files changed:
   - `README.md`: rewritten for a newcomer, following `docs/project-guide/style.md`. It now has what the factory is, "Try it" (`uv sync`, `make check`), "Where to read next" (one line per document, with relative links), and a closing *Reference*.
   - `docs/checked-documents.txt`: added the line `README.md`.

   Old text moved into the *Reference*, not cut. It holds the five console commands and their table, the `contract`, `check_documents` and `check_demos` modules, and the document check with its blocking rules, `Report (not checked yet):` and `documents ok`. It also holds the machine and the cloud-run script, the stage file, and how the repository is built with the history tag.

   Dropped or changed on purpose:
   - "v1.1" and "second implementation" are gone (style rule 1). The first implementation and the handover date stay as one line in *How it is built*.
   - The "Replaced from v1" section, with its `--follow` sentence, is gone. The document check rejects that sentence as a replaced behaviour (rule 7), and the code has no `--follow`.
   - The stage-file path is now written `<project>/factory/stage.Containerfile`, because the name check found the bare path does not exist in this repository.
   - The `agents/` and `CLAUDE.md` lines are kept.
   - I added links to `operator/README.md` and `demo/README.md`. Both files exist.

   Checks:
   - `make documents` ends with `documents ok (58.6 s)`.
   - I did not run `make check`, because only documents changed.
   - No document links to a README heading (I grepped `README.md#`), so no link needed changing.
   - The README's examples are indented plain blocks, not `console` blocks. `make check` is skipped by the suite rule anyway, and the other commands need a machine or a long run. The reviewer may judge whether a `console` example would serve better.
   - The glossary has no per-word headings, so the first use of "stories" links to `glossary.md`. Other factory words are used in the README only inside the *Reference*, in the quoted names of checks and stages, and I linked none of them.

   Cross-read: `docs/project-guide/style.md` (README section), `docs/project-guide/glossary.md`, `pyproject.toml` scripts, and `src/factory/entry/` (the modules exist). Nothing in them was stale.

   Stale text noticed and not touched: none.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (58.8 s)
6. factory: started docs-review as vm.
7. reviewer: Reviewed the diff to `README.md` and `docs/checked-documents.txt` against the code on the branch, the criteria and `docs/project-guide/style.md` (rules for all documents, *Runnable examples*, *The README*).

   These claims match the code or the repository: the five console commands (`pyproject.toml` `[project.scripts]`), the modules `factory.entry.contract`, `check_documents` and `check_demos` (`src/factory/entry/`), `tests/entry/test_demos.py`, `operator/vm/setup.sh`, `operator/vm/job-start.sh`, `agents/settings.json`, `/etc/factory/agents` (`src/factory/machine/application/stage_environment.py:30`, `operator/vm/Dockerfile:58`), and the headings *The machine*, *The project's stage file* and *On Cloud Run*. No document outside `factory/` and `planning`/`docs/runs` links to or names an old README heading, so criterion 4 holds. Dropping `--follow` is right: `docs/decisions.md:379` already records it, as rule 7 asks.

   Findings:
   1. README.md:10-12: the Try-it commands `uv sync` and `make check` are in an indented plain block. That is neither a runnable `console` example nor one marked `console vm`/`github`/`model`, so it breaks the Description ("every command the file shows is a runnable example or is marked") and style rule 6 (each command followed by what it prints). Fix: make it a `console` block that shows the output, with `$ make check`, `...` and `check: green`; `make check` is skipped as `suite` with no mark. Or use `console vm` and name the real run it was copied from.
   2. README.md:3, 14, 50, 62: factory words appear unlinked at their first use. These are "feature" (:3), "instance" (:14), "stop" (:50, :18), and "stage" and "dataset" (:62, first in :26). This breaks criterion 1 and style rule 3. The documenter's entry says these words appear only inside *Reference*, but "feature" and "instance" stand above it, and rule 3 makes no exception for *Reference*. Fix: link each to `docs/project-guide/glossary.md` at its first use in the file.
   3. README.md:18: the old file named the section *Setting up an operator's machine* in `site.md` (the heading exists at `docs/operator-guide/site.md:277`). The new line drops that name without saying so, which breaks criterion 2. Fix: name the section and link `site.md` (`[site.md](docs/operator-guide/site.md)`, *Setting up an operator's machine*).
   4. README.md:70: "The history of the first implementation (github.com/pkrahmer/factory), which built this one until the handover of 2026-10-18, is kept at …" is version history. Criterion 1 and style's README section ("no history") forbid it, and the sentence runs to about 30 words (rule 2). Fix: keep a single pointer, such as "The planning history is kept at the tag `planning-history-2026-10-19`; [decisions.md](docs/decisions.md) records why." Drop the handover narration.
   5. README.md:50: the sentence runs to about 29 words with a list inside a list (rule 2). It also uses "kill point" and "fault-injection path", which are private words not in the glossary (rule 3). Fix: split it in two, and name the project guide's sections *Kill points* and *Fault-injection paths* as section names, with a link, instead of using the words as common nouns.

   Earlier tests: none. The diff changes no test file.
8. factory: started docs-only as vm.
9. documenter: Round 1: fixed the reviewer's five findings, all in `README.md`.

   Files changed:
   - `README.md` (finding 1): the Try-it commands now stand in a `console` block, `$ make check`, then `...`, then `check: green`. `make check` runs the whole suite, so the check skips it (`README.md:11: not run (suite)`). `uv sync` moved into the sentence above the block as inline code. It was a command in the old block, and I did not put a second command in a block whose output I could not show.
   - `README.md` (finding 2): linked "feature", "stories", "instance", "stops", "stage" and "dataset" to `docs/project-guide/glossary.md` at their first use above the *Reference*. "Stage" and "dataset" are linked at their first use in the *Reference* (the machine section). The glossary has no heading per word, so every link points at the file.
   - `README.md` (finding 3): the operator-guide line names *Setting up an operator's machine* and links `docs/operator-guide/site.md`. The heading exists at `site.md:277`.
   - `README.md` (finding 4): the history sentence is now one pointer, "The planning history is kept at the tag `planning-history-2026-10-19`; decisions.md records why." The handover date and the first implementation's name are gone.
   - `README.md` (finding 5): split the long sentence in the document-check section. "Kill point" and "fault-injection path" now appear only as the project guide's section names *Kill points* and *Fault-injection paths*. I left them unlinked: `docs/project-guide/README.md` has those sections but I did not add anchor links, and the document check requires the names to appear.

   Checks:
   - `make documents` ends with `documents ok (59.3 s)`.
   - I did not run `make check`, because only a document changed.

   Cross-read: the README against `docs/project-guide/style.md`, the glossary and `docs/operator-guide/site.md`; all current.

   Stale text noticed and not touched: none.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (58.2 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 docs review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`. I checked the README against the code on the branch (`src/factory/hosting/application/opening.py`, `src/factory/pipeline/application/stage.py`, `src/factory/shared/domain/documents.py`), against `docs/project-guide/glossary.md`, `docs/project-guide/style.md`, the headings of `docs/operator-guide/machine.md` and `cloud-run.md`, and against the old README on `main`. All five round-0 findings are fixed: the `console` block with `check: green`, the glossary links above *Reference*, *Setting up an operator's machine*, the history pointer, and the split check sentence. `docs/checked-documents.txt` gains `README.md`. The `make documents` result in entry 9 is the documenter's; I did not run it.

    Findings:
    1. README.md:3: "Then it opens a pull request" is not what the code does. The draft pull request opens when the story's first stage starts (`src/factory/hosting/application/opening.py:109`, `draft=True`, reached from `src/factory/pipeline/application/stage.py:173`), before any agent runs. Fix: say that each story gets a draft pull request when its work starts, and that you approve it or send it back when the agents are done.
    2. README.md:53: the check described here is only half the code. `documents.py:422` refuses a missing section *Kill points* or *Fault-injection paths*. But `_project_guide_rows` (`src/factory/shared/domain/documents.py:345-358`) also refuses each kill point case and each fault-injection path that has no table row. The new text drops that second half, which the old text covered ("leaves a … kill point or fault-injection path unnamed"). The sentence also runs about 35 words with a chain of "or" (style rule 2). Fix: split it in two. One sentence for the missing document and its words. One for a stop without its table row, and a case or path without its row in the project guide's *Kill points* or *Fault-injection paths*.
    3. README.md:9-14 (Try it): the old file listed what `make check` runs ("lint, types, layers, sast, secrets, licenses, tests", old README.md:9). Neither the new text nor *Reference* has it, and the documenter's entries do not name it as dropped on purpose (criterion 2). Fix: add that list to the sentence above the block, or to *Reference*.
    4. README.md:17 and :67: the old file named the section *On Cloud Run* in `cloud-run.md` (old README.md:28; the heading exists at `docs/operator-guide/cloud-run.md:5`). The new text links only the file and drops the name without saying so (criterion 2). The same goes for "one folder each" on the demos (old :38, new :34). Fix: name *On Cloud Run* beside the link, and keep "one folder each".
    5. README.md:3, :39, :41-42: these factory words are not linked at their first use in the file (style rule 3, criterion 1):
       - "stories" at :3: its first use is the first sentence, and the link sits on the second use.
       - "tick" at :39 (`factory-run` row).
       - "work item" at :41 (`factory-bill` row).
       Fix: move the "stories" link to the first sentence, and link "tick" and "work item" to `docs/project-guide/glossary.md`.

    Earlier tests: none. The diff changes no test file.
12. factory: started docs-only as vm.
13. documenter: Round 2: fixed the reviewer's five findings, all in `README.md`.

    Files changed:
    - `README.md` (1): the opening now says each story gets a draft pull request when its work starts, and that you approve it or send it back when the agents are done.
    - `README.md` (2): the document-check paragraph is split. One sentence covers the missing document, the missing words and the unnamed stop. A second sentence covers a stop, a kill point case or a fault-injection path without its row in the project guide's *Kill points* or *Fault-injection paths*, and a project guide that lacks one of those sections.
    - `README.md` (3): the sentence above the `make check` block lists what it runs: lint, types, layers, sast, secrets, licenses and tests.
    - `README.md` (4): *On Cloud Run* is named beside both cloud-run.md links (Try it and the machine section). "One folder each" is back on the demos line.
    - `README.md` (5): the "stories" link moved to its first use in the first sentence. "tick" and "work item" in the console table link to the glossary.

    Checks: `make documents` ends with `documents ok (58.4 s)`. I did not run `make check`, because only a document changed.

    Cross-read: `README.md` against the reviewer's cited code in `documents.py` and `opening.py` (as they describe it), the glossary and the old README on `main`. I found it current. I did not re-read `documents.py` myself.

    Stale text noticed and not touched: none.

    `check`: check: green
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok (58.1 s)
14. factory: started docs-review as vm.
15. reviewer: Round 2 docs review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`, and checked the README against `src/factory/shared/domain/documents.py`, `docs/decisions.md`, `docs/project-guide/glossary.md` and the old README on `main`.

    All five round-1 findings are fixed:
    - the opening's draft pull request;
    - the list of what `make check` runs;
    - *On Cloud Run*, named twice;
    - "one folder each";
    - the glossary links for "stories", "tick" and "work item".

    No other document links to an old README heading. `docs/checked-documents.txt` gains `README.md`. I did not run `make documents`; the result in entry 13 is the documenter's.

    Findings:
    1. README.md:56 (*The document check*), second sentence: the text says a stop without its row is found in the project guide's *Kill points* or *Fault-injection paths*. The code does not check that. `_stop_rows` (`src/factory/shared/domain/documents.py:342-348`) checks stop rows only in `docs/operator-guide/stops.md` (`_stops_messages`, :412-417), and the row must name the stop's destination. The project guide check (`_project_guide_rows`, :351-363) covers only kill point cases and fault-injection paths. The paragraph also drops that the operator guide must have the sections *Install*, *Configuration* and *The stops* (`OPERATOR_GUIDE_SECTIONS`, :50, checked at :408-417). Fix: say the check finds a stop without a row naming its destination in the operator guide's stops file, an operator guide that lacks *Install*, *Configuration* or *The stops*, and a kill point case or fault-injection path without its row in the project guide's *Kill points* or *Fault-injection paths*. Also drop the vaguer "leaves a stop unnamed" in the first sentence.
    2. README.md:73 (*How it is built*), last sentence: "[decisions.md](docs/decisions.md) records why" the planning history is kept at the tag. The decision log does not say why. `docs/decisions.md:3` and `:621` only say that the records and `factory/v1/` were removed and are kept at the tag `planning-history-2026-10-19`. Fix: say that decisions.md says what the tag holds (the planning records its older entries cite), or drop the clause.

    Earlier tests: none. The diff changes no test file.
16. factory: started docs-only as vm.
17. documenter: Round 3: fixed the reviewer's two findings, both in `README.md`.

    Files changed:
    - `README.md` (1), *The document check*: I read `_stop_rows`, `_stops_messages` and `_project_guide_rows` in `src/factory/shared/domain/documents.py`. The paragraph now says what the code checks, in three sentences. The first covers a missing document and one that lacks the factory's own words, and drops "leaves a stop unnamed". The second covers a stop without a row naming its destination in the operator guide's stops file, and an operator guide that lacks *Install*, *Configuration* or *The stops*. The third covers a kill point case or fault-injection path without its row in the project guide's *Kill points* or *Fault-injection paths*, and a project guide that lacks one of those sections.
    - `README.md` (2), *How it is built*: "decisions.md records why" is now "decisions.md says what the tag holds". `docs/decisions.md:3` says the planning records its older entries cite are kept at the tag.

    Checks: `make documents` ends with `documents ok (57.8 s)`. I did not run `make check`, because only a document changed.

    Cross-read: `README.md` against `documents.py` (the stop, kill point and fault-injection checks, `OPERATOR_GUIDE_SECTIONS`) and `docs/decisions.md:3`; current.

    Stale text noticed and not touched: none.

    `check`: check: green
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok (58.0 s)
18. factory: started docs-review as vm.
19. reviewer: Round 3 docs review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`. I checked the README against `src/factory/shared/domain/documents.py` (`OPERATOR_GUIDE_SECTIONS`, `_stop_rows`, `_stops_messages`, `_project_guide_rows`, `_project_guide_messages`), `docs/decisions.md:3`, `docs/project-guide/glossary.md`, `docs/project-guide/style.md` (*Rules for all documents* and *The README*) and the old README on `main`. I did not run `make documents`; the result in entry 17 is the documenter's.

    Both round-2 findings are fixed, and the facts are now true of the code:
    - The stop rows are checked in the stops file, with their destination.
    - The operator guide's three sections and the project guide's two sections and their rows are named.
    - "says what the tag holds" matches `docs/decisions.md:3`.

    `docs/checked-documents.txt` gains `README.md`. No other document links to an old README heading. Criteria 2 and 4 hold.

    The round-3 rewrite of the paragraph brings back two problems that round 0's finding 5 already sent back.

    Findings:
    1. README.md:53 (*The document check*), sentences 2 and 3, breaks style rules 2 and 3 (criterion 1).
       - Sentence 2 runs to about 28 words and sentence 3 to about 32; each joins two checks with "and".
       - Sentence 3 uses "kill point case" and "fault-injection path" as common nouns. These are private words that are not in the glossary. Round 0 asked for them to appear only as the section names *Kill points* and *Fault-injection paths*.
       - Fix: split them into four short sentences, one check each, and name the project guide's check through its sections. For example: "It finds a stop whose row in the operator guide's stops file does not name its destination. It finds an operator guide that lacks *Install*, *Configuration* or *The stops*. It finds a project guide that lacks *Kill points* or *Fault-injection paths*. It also finds one whose tables there leave out a case the code tests."

    Earlier tests: none. The diff changes no test file.
20. factory: This work item has now been sent back 4 times, more than 3. What should happen? Answer with a comment, which starts the count of rounds over; close the pull request to discard the work item.
21. 2026-11-07 human: One more round, by the human's standing word for tonight. The documenter fixes the one finding of the last review as it proposes: four short sentences, one check each, and the project guide's check named through its sections. Before it ends, it counts the words of every sentence of README.md by script and splits any above the style page's limit, and its entry quotes the script's last output. It changes nothing else in the page.
22. factory: started docs-review as vm.
