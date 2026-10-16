---
stage: accept
pr: 116
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The documents say the acceptance is wired

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance found three places in the documents that still describe F0009 as unfinished, or leave it out, and a fourth says the same of `AcceptanceDueHandler`. They contradict the code and the other documents.

1. `docs/project-guide.md`, section "Events", the paragraph that lists the kinds, ends with "`build_handlers` registers every kind except `acceptance_due`, which belongs to F0009 (see *The handlers of the events*)". The section it points to says, as the code does, that `build_handlers` returns the handlers of all thirteen kinds and that `NOT_YET_HANDLED` is empty.
2. `docs/project-guide.md`, section "The feature acceptance", the item on `SplitByWorkItemKind`, ends with "It is registered for `hand_over`, `merged` and `closed` in `build_handlers` by F0009-S0010; until then it is not in `build_handlers`." It is registered now, and the code names no story.
3. `docs/project-guide.md`, section "The feature acceptance", the item **Opening**, ends with "`AcceptanceDueHandler` runs `open` for the feature of an `acceptance_due` event (…); it is not yet in `build_handlers`." It is registered for `acceptance_due`.
4. `README.md` lists what is built so far: the stage protocol, the reading of the remote, the handlers of the human's acts, crash recovery. It does not mention the feature acceptance at all. A newcomer cannot tell that a feature whose stories are all archived gets an acceptance of its own, that an agent reviews it, and that the human's merge or close of its pull request books it accepted or refused.

This story is documentation only: the tester writes no tests and the coder has nothing to build; the documenter writes it from the docs criterion. The human may prefer to make the edit by hand.

## Interface

None: no code changes. Files: `docs/project-guide.md` ("Events", the paragraph that begins "The kinds:"; "The feature acceptance", the items **Opening** and `SplitByWorkItemKind`) and `README.md` (the first paragraph, which says what is built so far). `docs/operator-guide.md` is read for consistency and changed only where it contradicts the new text.

## Acceptance criteria

1. make check stays green.
2. docs: this story is the documentation. `docs/project-guide.md` and `README.md` change; `docs/operator-guide.md` changes only where it contradicts the new text. Afterwards:
   - The paragraph of `docs/project-guide.md` that begins "The kinds:" says that `build_handlers` registers a handler for every kind, `acceptance_due` included, and still points to *The handlers of the events*. It no longer says that any kind is left out of `build_handlers`.
   - The item **Opening** under "The feature acceptance" says that `AcceptanceDueHandler` is registered for `acceptance_due` in `build_handlers`. It no longer says "not yet".
   - The item on `SplitByWorkItemKind` says that it is registered for `hand_over`, `merged` and `closed` in `build_handlers`, and that the `RunGate` holds the same `closed` and `merged` instances. It no longer says "until then" or names a story.
   - `grep -n "except \`acceptance_due\`\|not yet in \`build_handlers\`\|until then it is not in" docs/project-guide.md` finds nothing, and `grep -n "F0009-S00" docs/project-guide.md README.md docs/operator-guide.md` finds nothing.
   - The first paragraph of `README.md` names the feature acceptance among what is built, in one sentence: a feature whose stories are all archived becomes due, an acceptance reviewer runs on its own work item, and the human's merge of its pull request books it accepted while a close books it refused. The sentence points to the operator guide's "When a feature acceptance is due" for the details, and uses the glossary's names (no v1 word such as "acceptor").
   - The operator guide's acceptance sections, cross-read against these places, say the same thing.

## Demo

```bash
grep -c "except \`acceptance_due\`\|not yet in \`build_handlers\`\|until then it is not in" docs/project-guide.md; grep -c "F0009-S00" docs/project-guide.md README.md docs/operator-guide.md
```
Expect: `0` on the first line, then each file with `:0`.

```bash
grep -n -i "acceptance" README.md
```
Expect: at least one line from the first paragraph that names the feature acceptance.

## Log (append only)

1. 2026-10-16 human: created.
2. intake: accepted
   - Interface: "None, no code changes" is right for a docs-only story; it names the exact files and sections (project-guide "Events" paragraph "The kinds:", items Opening and SplitByWorkItemKind, README first paragraph, operator guide read-only). I checked that these sections exist in the files.
   - Criteria: criterion 2 is checkable by the two greps and by reading the named paragraphs. Criterion 1 is `make check`. The docs criterion has no failing side because no rule is stated. The story says the tester writes no tests, and I take that as the human's decision.
   - Demo: both commands are runnable. The first grep -c prints a count and the second prints per-file counts. Both Expect lines can be checked against that output. The operator guide anchor "When a feature acceptance is due" exists (docs/operator-guide.md line 423).
   - Architecture: documentation only, no layer is touched. The README sentence is to use the glossary's names.
   - Scope: this is within F0009 (it is listed in FEATURE.md as S0013, proposed by the feature acceptance) and not in its Out of scope. FEATURE.md decision 5 says the "acceptance_due" handlers are registered. The story is consistent with that.
3. tester: no tests written, as the Assignment says. This story only changes documentation and the human chose that the tester writes no tests (intake confirmed this).
   - criterion 1 (make check stays green): no test of its own. The factory's checks cover it. `make lint` is green with the tree unchanged.
   - criterion 2 (docs): the documenter checks this with the two greps and by reading the paragraphs the criterion names. It is not an executable test in `tests/`. A test that greps the docs would put a ticket's wording into the test suite, and I decided against that.
   Files created: none. Modules the test runner could not import: none, because no new tests exist. The coder has nothing to build and can hand straight on.

   `make lint`: lint: green
   `make test`: test: green
4. coder: I built nothing and made no commit. This story only changes documentation. The Interface says "None: no code changes", and the tester wrote no tests. Under CLAUDE.md the coder does not write `README.md` or `docs/`, so I left all four edits in criterion 2 for the documenter: the "The kinds:" paragraph, the **Opening** item and the `SplitByWorkItemKind` item in `docs/project-guide.md`, and the first paragraph of `README.md`.
      - Rejected: writing the doc edits here. They are outside the coder's lane, and the docs stage is where they belong.
      - Refactor: there is no diff, so there was nothing to clean up.
      - `make check`: green on the unchanged tree (coverage 99.53 %).
      - Open: everything in criterion 2. The documenter does it.

   `make check`: check: green
5. reviewer: no findings.
      - Diff: `git diff main...HEAD -- . ':!factory'` is empty. This matches the Interface ("None: no code changes") and what the tester and coder report (entries 3 and 4).
      - Acceptance criteria: criterion 1 has no test of its own. The coder's entry records the factory's `make check` as green on the unchanged tree. Criterion 2 is the docs criterion and the documenter writes it next. The Interface states no rule or limit, so no failing side is missing a test.
      - Architecture, security, quality: none apply because no code, test or configuration changed. No suppression markers were added.
      - Ticket hygiene: the log explains the main decision (the tester writes no tests because the docs are not executable criteria, and the coder leaves the doc edits to the documenter's lane) and what was rejected. `Assignment` matches what was built, which is nothing. Criterion 2 still states exactly what the documenter must change: the "The kinds:" paragraph and the **Opening** and `SplitByWorkItemKind` items in `docs/project-guide.md`, the first paragraph of `README.md`, and the operator guide cross-read. It also gives the two greps that check the result.
      - Open: all of criterion 2, for the documenter.
6. documenter: wrote the four edits of criterion 2 and found no findings.
   - `docs/project-guide.md`, "Events": the paragraph "The kinds:" now says `build_handlers` registers a handler for every kind, `acceptance_due` included, and still points to *The handlers of the events*.
   - `docs/project-guide.md`, "The feature acceptance": the **Opening** item says `AcceptanceDueHandler` is registered for `acceptance_due` in `build_handlers`. The `SplitByWorkItemKind` item says it is registered for `hand_over`, `merged` and `closed`, and that the `RunGate` holds the same `closed` and `merged` instances. No story id and no "until then" remain in either item.
   - `README.md`, first paragraph: one sentence names the feature acceptance. A feature whose stories are all archived becomes due, an acceptance reviewer runs on the acceptance's own work item, and the human's merge of its pull request books it accepted while a close books it refused. The sentence points to "When a feature acceptance is due" in `docs/operator-guide.md` and uses the glossary's names.
   - Cross-read: `docs/operator-guide.md` (its intro, the acceptance sections, close, merged-before-approval, accepted-again and no-loop) and the "Handlers" wiring paragraph of `docs/project-guide.md` (`build_handlers`, 13 kinds, shared splits). Both agree with the new text, so I changed neither.
   - Checked: the first grep counts 0. The second finds no `F0009-S00` in `docs/project-guide.md`, `README.md` or `docs/operator-guide.md`. `docs/decisions.md` still cites F0009 story ids, but those are dated decision-log entries, outside this story's grep. `make check`: green.
   - Stale but untouched: nothing seen. The README and operator guide still say `factory-run` is unbuilt until F0010, which is true.

   `make check`: check: green
7. demo: both commands ran from the repository root. Both met their Expect lines, and I found nothing that contradicts a criterion.

   1. The stale-wording grep and the story-id grep:
   ```
   0
   docs/project-guide.md:0
   README.md:0
   docs/operator-guide.md:0
   ```
   Met: `0` on the first line, then `:0` for each of the three files.

   2. `grep -n -i "acceptance" README.md`:
   ```
   3:The factory, reimplemented by v1 of itself. … After a crash, a restart reruns the dead stage, an expired lease of another instance is taken over, the crash cap asks the human, and the tick deletes a stale branch. The feature acceptance is wired too: a feature whose stories are all archived becomes due, an acceptance reviewer runs on the acceptance's own work item, and the human's merge of its pull request books it accepted while a close books it refused (see "When a feature acceptance is due" in `docs/operator-guide.md`). The pipeline itself does not run on its own yet: … `docs/project-guide.md` describes each part.
   ```
   Met: line 3 is the first paragraph, and it names the feature acceptance.

   Cross-check against criterion 2:
   - `docs/project-guide.md:505` ("The kinds:") says "`build_handlers` registers a handler for every kind, `acceptance_due` included (see *The handlers of the events*)".
   - `docs/project-guide.md:457` (**Opening**) ends with "it is registered for `acceptance_due` in `build_handlers`." It no longer says "not yet".
   - `docs/project-guide.md:459` (`SplitByWorkItemKind`) says it is registered for `hand_over`, `merged` and `closed` in `build_handlers`, and that the `RunGate` holds the same `closed` and `merged` instances. It names no story and has no "until then".
   - That matches `docs/project-guide.md:579` (the `build_handlers` wiring, all thirteen kinds).
   - The README sentence uses the glossary's names; there is no "acceptor".

   I did not run `make check` (criterion 1). The factory runs it after this stage, and the documenter recorded it green.

   Open: nothing.
