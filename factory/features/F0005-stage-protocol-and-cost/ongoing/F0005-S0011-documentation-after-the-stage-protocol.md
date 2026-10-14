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
