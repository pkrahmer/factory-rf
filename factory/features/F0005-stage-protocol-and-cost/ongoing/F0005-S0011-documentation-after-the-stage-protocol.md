---
stage: demo
pr: 70
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Documentation after the stage protocol: the README, the operator guide's opening and what a stage shows

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance of F0005 read `README.md` and `docs/` from the top. The F0005 sections of the project guide are current and match the demo. Each story documented its own part, though, and five things fell between them:

- The opening lists of `README.md` and `docs/operator-guide.md` stop at F0004 and "the stall with its note". They name neither the stage protocol, the decision rules with the factory's questions, the checks and reports, nor the cost records.
- No section tells the operator what a stage run looks like on the remote and the pull request. That covers the draft pull request opened at the first stage (titled `<id>: <title>`, with the work item's text as its description), the `factory: started <stage> as <instance>.` entry and the claim pushed first, the agent's entry and the check lines, one factory commit per stage, and the `stage:` label.
- "Stops of one work item" states that for "a question, a stall, a cap reached" a missing pull request is opened with the description `The factory opened this draft pull request to report a stop …`, and that a recorded pull request is posted on even when closed. A stall does neither. `StallService` goes through `WorkItemOpening.ensure_pull_request`, which reuses only an open pull request and opens a new draft with the work item's text.
- "A stall: the stall note" names four causes in its first sentence and nine in its list. Its cap paragraph says "The factory does not run the stage again until you have", and the note says "the factory asks you next". Nothing built so far stops a stage at the cap or asks the attempts-cap question: the evaluation is F0006's and the question is F0007's.
- "The factory's own questions" says that each of its questions "is a comment on the pull request", and "Stops of one work item" counts a question among the stops posted there. Today a question (the agent's `question`, rule 1's findings, rule 4's round cap) is only recorded: a journal entry of kind `question`, and `blocked` set. Posting it on the pull request is F0007's (F0007-S0002).

This story is documentation only: the tester writes no tests and the coder has nothing to build; the documenter writes it from the docs criterion. The human may prefer to make the edit by hand.

## Interface

None: no code changes. Files: `README.md`, `docs/operator-guide.md`. `docs/project-guide.md` and `docs/decisions.md` are read for consistency and changed only where they contradict the new text.

## Acceptance criteria

1. make check stays green.
2. docs: this story is the documentation. `README.md` and `docs/operator-guide.md` change; `docs/project-guide.md` and `docs/decisions.md` change only where they contradict the new text. Afterwards:
   - `README.md`'s summary of what is built names the stage protocol (one stage run from the pushed claim to the result commit, with stalls and v1's decision rules), the cost records and the bill. It summarises rather than lists, as the human decided on 2026-10-14 (F0003-S0010), and it still says that the pipeline does not run on its own yet (nothing starts a stage before F0006).
   - The opening paragraph of `docs/operator-guide.md` names the same built parts and still names the three commands `factory-check-story`, `factory-bill` and `factory-guard`.
   - `docs/operator-guide.md` has a section on what a stage run shows. It covers the draft pull request the first stage opens (title `<id>: <title>`, the work item's text as description, only an open pull request reused); the stage-start commit that pushes the claim, with the journal entry `factory: started <stage> as <instance>.`, before any agent runs; the agent's entry (speaker and kind written by code) with one line `` `<command>`: <last line> `` per green check and report; the one commit, the result or the stall commit, that the factory adds above the stage-start commit (or above the agent's last commit); and the label `stage:<stage>`, written literally so, after the result commit is pushed and after a stall's note. Each statement matches `docs/project-guide.md`'s "Opening a work item", "Starting a stage", "Stalls" and "The stage protocol".
   - "Stops of one work item" says that its pull-request rules are those of `StopService.post`, which nothing built calls yet, and no longer says that a stall's pull request gets the stop description or that a stall is posted on a closed pull request. Where stalls are described, the stall's own rule is stated: an open pull request is reused, otherwise a new draft titled `<id>: <title>` with the work item's text.
   - "The factory's own questions" and the opening of "Stops of one work item" say that a question (the agent's `question`, the findings question, the round-cap question) is recorded today as a journal entry of kind `question` with `blocked` set, and that posting it on the pull request arrives with F0007. The quoted question texts stay as `factory.domain.post_texts` gives them.
   - The first sentence of "A stall: the stall note" names all nine causes or points to the list below it.
   - The cap paragraph of "A stall: the stall note" and the cap bullet of "A stall by a red check" say that stopping at the attempts cap and asking the attempts-cap question are not built yet, and name where they arrive (F0006's evaluation, F0007's question). They keep what the operator does once they arrive.
   - Every example and quoted text in the changed sections matches what the code prints today: the note texts of `factory.domain.post_texts`, the label `stage:<stage>` and the journal's `started` entry.

## Demo

```bash
grep -n -i "stage protocol\|decision rules\|cost record\|bill" README.md
```
Expect: at least one line of the built-parts summary names the stage protocol or the decision rules, and one names the cost records or the bill.

```bash
grep -n "stop of one work item\|opened this draft pull request\|started <stage> as\|stage:<stage>" docs/operator-guide.md
```
Expect: no printed line counts a stall among the stops that get the stop description or are posted on a closed pull request, at least one printed line has `started <stage> as`, and at least one has `stage:<stage>`.

## Log (append only)

1. 2026-10-14 human: created.
2. intake: accepted
   - Interface: "None: no code changes", with the files named (`README.md`, `docs/operator-guide.md`; `docs/project-guide.md` and `docs/decisions.md` only where they contradict). There is no behaviour in an Interface comment to test.
   - Criteria: criterion 1 is `make check`. Criterion 2 is the docs criterion, which the documenter works from. Its bullets say exactly which statements each file must make and which texts must match the code. This is a documentation-only story, so the tester has no test functions to write, and the Assignment says so. There is no rule with a failing side.
   - Demo: both commands are runnable `grep`s. The first Expect line is checkable against its output. The second Expect line is checkable too, but its pattern `stop of one work item` does not match the heading "Stops of one work item" (the "s" breaks it). The other three patterns still print the lines the Expect line needs. I left the pattern as the human wrote it and did not improve the story.
   - Architecture: no code or layer is touched. The files are the ones `CLAUDE.md` assigns to the documenter stage.
   - Scope: it fits F0005. S0011 is listed in FEATURE.md as a story proposed by the feature acceptance. It documents only what F0005 built and says plainly what F0006 and F0007 will add. Nothing in "Out of scope" is brought in.
3. tester: no tests written. This story only changes documentation. The Interface says "None: no code changes", and the Assignment says the tester writes no tests.
   - criterion 1 (make check stays green): no test of its own. The factory's `make check` covers it.
   - criterion 2 (docs): the documenter works from it. Its demo `grep`s check it, and no pytest test does.
   - Files created: none. There are no new red tests and no modules the test runner could not import. I did not run `make test`, because no tests were added.
   - `make lint`: green.

   `make lint`: lint: green
   `make test`: test: green
4. coder: nothing to build. This story changes documentation only. The Interface says "None: no code changes", and the Assignment says "the coder has nothing to build; the documenter writes it from the docs criterion".
      - Code changed: none, and no commits. There were no failing tests to make pass, because the tester added none.
      - Refactor: none, because there is no diff to read.
      - Writing `README.md` and `docs/operator-guide.md` is left to the documenter stage. That follows criterion 2 and `CLAUDE.md` ("the coder does not write them").
      - The intake already noted that the second demo's pattern `stop of one work item` does not match the heading "Stops of one work item". It is still open and harmless.

      `make check`: check: green (coverage 99.35 %)

   `make check`: check: green
5. reviewer: no findings.
      - Diff: `git diff main...HEAD -- . ':!factory'` is empty. The branch has only the factory's stage commits (9c458c5, ddd0c29, a322f82, a900dc4) and no code, test or docs change. That is what this story asks for: the Interface says "None: no code changes", and the Assignment hands all the writing to the documenter.
      - Criterion 1 (`make check` stays green): the coder's entry records the factory's `make check` as green (coverage 99.35 %). Nothing changed since that run.
      - Criterion 2 (docs): this is the documenter's work, which comes next. The bullets name each statement `README.md` and `docs/operator-guide.md` must make, and the texts that must match the code (`factory.domain.post_texts`, `stage:<stage>`, `factory: started <stage> as <instance>.`). It still describes what the reader must know after this story.
      - Architecture, security, quality: nothing to judge, because no code changed.
      - Ticket hygiene: the log says why there are no tests and no code. The Assignment matches the empty diff.
      - Open: the second demo's pattern `stop of one work item` does not match the heading "Stops of one work item". The intake and the coder both noted this. The other three patterns still print the lines the Expect needs, so it is harmless. Changing it is the human's call.
6. documenter: documented the stage protocol, the stage-run traces and the stop corrections. `make check` is green.

   Files changed:
   - `README.md`: the built-parts summary now names the stage protocol (claim to result commit, stalls, v1's decision rules) and the cost records with the bill. It still says nothing starts a stage before F0006.
   - `docs/operator-guide.md`, opening: names the same built parts and still names `factory-check-story`, `factory-bill` and `factory-guard`.
   - `docs/operator-guide.md`, new section "What a stage run shows": the draft pull request (title `<id>: <title>`, the work item's text as description, only an open pull request reused), the stage-start commit with the entry `factory: started <stage> as <instance>.` pushed before any agent, the agent's entry with one `` `<command>`: <last line> `` line per green check and report, the single factory commit, and the label `stage:<stage>`. Checked against the project guide's "Opening a work item", "Starting a stage", "Stalls" and "The stage protocol".
   - `docs/operator-guide.md`, "Stops of one work item": says its rules are those of `StopService.post`, which nothing built calls yet, and that a question is recorded today and posted from F0007. A stall is no longer counted among the stops that get the stop description or are posted on a closed pull request.
   - `docs/operator-guide.md`, "A stall: the stall note": the first sentence points to the nine causes below it. The cap paragraph says stopping at the cap and the attempts-cap question are not built yet (F0006's evaluation, F0007's question), and keeps what the operator does once they are. A new bullet gives the stall's own pull-request rule: reuse an open pull request, otherwise a new draft with the work item's text.
   - `docs/operator-guide.md`, "A stall by a red check": the cap bullet got the same "not built yet" note.
   - `docs/operator-guide.md`, "The factory's own questions": a question is today a journal entry of kind `question` with `blocked` set, and posting it on the pull request arrives with F0007. The quoted texts are unchanged and match `factory.domain.post_texts`.

   Cross-read and found current: `docs/project-guide.md` ("Opening a work item", "Starting a stage", "Stalls", "The stage protocol", the decision rules) and `docs/decisions.md`. Neither contradicts the new text, so I left both alone.

   Not touched: the second demo `grep` pattern `stop of one work item` does not match the heading "Stops of one work item" (already noted by intake and the reviewer). The other patterns still print the needed lines. I did not re-run the demo greps after editing; the changed sections contain `started <stage> as` and `stage:<stage>`.

   No findings for the coder.

   `make check`: check: green
