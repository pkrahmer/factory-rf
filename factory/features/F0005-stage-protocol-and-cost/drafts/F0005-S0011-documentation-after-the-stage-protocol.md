# Documentation after the stage protocol: the README, the operator guide's opening and what a stage shows

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance of F0005 read `README.md` and `docs/` from the top. The F0005 sections of the project guide are current and match the demo. Each story documented its own part, though, and four things fell between them:

- The opening lists of `README.md` and `docs/operator-guide.md` stop at F0004 and "the stall with its note". They name neither the stage protocol, the decision rules with the factory's questions, the checks and reports, nor the cost records.
- No section tells the operator what a stage run looks like on the remote and the pull request. That covers the draft pull request opened at the first stage (titled `<id>: <title>`, with the work item's text as its description), the `factory: started <stage> as <instance>.` entry and the claim pushed first, the agent's entry and the check lines, one factory commit per stage, and the `stage:` label.
- "Stops of one work item" states that for "a question, a stall, a cap reached" a missing pull request is opened with the description `The factory opened this draft pull request to report a stop …`, and that a recorded pull request is posted on even when closed. A stall does neither. `StallService` goes through `WorkItemOpening.ensure_pull_request`, which reuses only an open pull request and opens a new draft with the work item's text.
- "A stall: the stall note" names four causes in its first sentence and nine in its list. Its cap paragraph says "The factory does not run the stage again until you have", and the note says "the factory asks you next". Nothing built so far stops a stage at the cap or asks the attempts-cap question: the evaluation is F0006's and the question is F0007's.

This story is documentation only and changes no code and no test. The human may prefer to make the edit by hand.

## Interface

None: no code changes. Files: `README.md`, `docs/operator-guide.md`. `docs/project-guide.md` and `docs/decisions.md` are read for consistency and changed only where they contradict the new text.

## Acceptance criteria

1. `README.md`'s summary of what is built names the stage protocol (one stage run from the pushed claim to the result commit, with stalls and v1's decision rules), the cost records and the bill. It summarises rather than lists, as the human decided on 2026-10-14 (F0003-S0010), and it still says that the pipeline does not run on its own yet (nothing starts a stage before F0006).
2. The opening paragraph of `docs/operator-guide.md` names the same built parts as criterion 1 and the three commands `factory-check-story`, `factory-bill` and `factory-guard`.
3. `docs/operator-guide.md` has a section on what a stage run shows. It covers the draft pull request the first stage opens (title `<id>: <title>`, the work item's text as description, only an open pull request reused) and the claim pushed in the stage-start commit with the journal entry `factory: started <stage> as <instance>.` before any agent runs. It also covers the agent's entry (speaker and kind written by code), the `` `<command>`: <last line> `` lines of green checks and reports, the one commit the factory adds per stage, and the `stage:<stage>` label written after a result commit. Each statement matches `docs/project-guide.md`'s "Opening a work item", "Starting a stage" and "The stage protocol".
4. "Stops of one work item" says which stops its pull-request rules apply to, and no longer says that a stall's pull request gets the stop description or that a stall is posted on a closed pull request. The stall's own rule (an open pull request reused, otherwise a new draft with the work item's text) is stated where stalls are described.
5. The first sentence of "A stall: the stall note" no longer lists fewer causes than the list below it. It either names all nine or points to the list.
6. The cap paragraph of "A stall: the stall note" says that stopping at the attempts cap and asking the attempts-cap question are not built yet, and names where they arrive (F0006's evaluation, F0007's question). It keeps what the operator does once they arrive.
7. Every example and quoted text in the changed sections matches what the code prints today: the note texts of `factory.domain.post_texts`, the label `stage:<stage>` and the journal's `started` entry.
8. make check stays green.
9. docs: this story is the documentation: `README.md` and `docs/operator-guide.md` as criteria 1 to 7 say. `docs/project-guide.md` and `docs/decisions.md` need no change unless they contradict the new text.

## Demo

```bash
grep -n -i "stage protocol\|decision rules\|cost record\|bill" README.md
```
Expect: at least one line of the built-parts summary names the stage protocol or the decision rules, and one names the cost records or the bill.

```bash
grep -n "opened this draft pull request\|started <stage> as\|stage:<stage>" docs/operator-guide.md
```
Expect: the line about the stop description no longer counts a stall among the stops it applies to, and the new section has the lines with `started <stage> as` and `stage:<stage>`.
