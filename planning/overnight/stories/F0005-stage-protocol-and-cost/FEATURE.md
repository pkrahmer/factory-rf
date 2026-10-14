# Stage protocol and cost

## Goal

Every stage runs the same steps in the same order around one agent run: open or prepare the work item's branch and its draft pull request, push the claim, compose the prompt from the pipeline definition, run the agent, apply the undo and the restore, write the journal entry by code, check the form again, decide by v1's seven rules, run the checks and the reports, and commit and push the result. Any result the factory cannot keep is a stall that costs an attempt. Every agent run has a cost record from its start, committed with the stage's next commit, and the bill of a stage and of a story is computed from the cost records alone. Done when a stage starts only after its claim is pushed, a stage moves, stalls or asks exactly as v1's decision rules say, a stall costs an attempt with the undo and the restore applied whatever ended the run, and the cost table and cost line of a stage and a story are read from the cost records in the repository and from nothing else.

## Scope

- Agent definitions read from the agent home, the prompt's lines, the allowed decisions (the stage's `next` plus `question`, one source for the prompt, the request and the validation), the environment of the agent run passed on as the caller gives it, and the story form check run before and after the agent
- Opening the work item's branch with initial state (the backlog file's own state fields dropped) and entry 1, preparing a later stage (the branch reset to the remote, the main branch merged in, a conflict aborted), the draft pull request (only an open one reused)
- The stage start: the claim pushed first through the claim service, no agent run without it (GH1.1), the guard settings from the stage-start commit, the `time_limit` and the budget
- Stalls (GH2.5): attempts + 1, the stall entry, partial work inside the write paths committed, undo and restore applied whatever ended the run, the claim released, the stall note with attempt and reason
- After the agent: the branch test, undo and restore, the entry written by code with speaker and kind, the form checked again, only a new finding stalls
- Decision rules 1 to 7: forward move, form findings turned into a question, questions, rework rounds and their caps, the round-cap question, checks in order with the red tail, reports after green; the result commit and push; labels written as a projection of the stage
- Cost records (GH4.1, GH4.2, R24): created at agent run start, completed at its end, committed with the stage's next commit; unknown cost and tokens never invented
- Bills (SI1.2, GH4.5, SI1.4): per stage and per story from the records; the cost table and the cost line; the command that prints them; a search that no code reads data from journal text

## Out of scope

- The hand-over at the approval and the cost table posted there: F0007
- Reading the pull request's state before the agent run, the merge and close handlers, the recorded questions posted on the pull request: F0007
- The word "retrying" in the expiry note and the rerun after a crash: F0008 (ST1.4); the crash discard and the crash counter's increment: F0008 (its reset on a forward move is S0007's, decision 17)
- The image recorded in each cost record: F0010 (ST5.4); the content of an agent run's environment (F0006's wiring supplies it, F0010 scrubs it and probes `PATH` and `HOME`) and the second OS user: F0010
- The acceptance reviewer's facts, the acceptance branch and an acceptance's own cost line: F0009
- Dispatching the `run` event to the stage runner and the tick: F0006

## Stories

- S0001 — Agent definitions, the prompt and the allowed decisions
- S0002 — Opening the work item's branch and its draft pull request
- S0003 — The stage starts with the pushed claim, then the agent run
- S0004 — Stalls
- S0005 — After the agent: the branch, the undo, the entry, the form again
- S0006 — The decision rules: questions, rework rounds and caps
- S0007 — Checks, reports and the stage's result commit
- S0008 — Cost records at agent run start and end
- S0009 — Bills from the cost records

## Decisions taken for the human

Product decisions taken while writing the stories, for the human to review in one place. Each names where it was taken.

1. The prompt's lines are `Work item:`, `Id:`, `Stage:`, `Allowed decisions:`, `Branch:`, `Pull request:`, `Round:`, then `Mode:` and `Format check:` when they apply, then one closing line; v1's `Ticket:` and `Allowed outcomes:` carry the glossary's names. (S0001, story text)
2. The `Format check` line goes to the first stage of the pipeline definition, whatever its role is called; v1 gave it to intake only because intake was the first stage. (S0001, story text)
3. The `Mode:` line for the tester after the coder asked for a test change is decided from the journal's last `result` record (speaker `coder`), never from the entry's text; a stall, a crash or a human comment after it does not hide it. (S0001, story text)
4. A started work item's entry 1 (`human`, `created`) is dated with the day the factory opens it, because the backlog file carries no date; a backlog story's own front matter and journal are dropped. Its `## Journal` section is expected to be empty: a story without that section gets an empty one added at the end of the body before entry 1, and entries already in the section are left for the form check to report to intake. (S0002, story text)
5. The draft pull request is titled `<id>: <title>` and its description is the work item's whole text at the start; the hand-over (F0007) replaces it. (S0002, story text)
6. A pull request found in the state or by branch is reused only while it is open; a closed or merged one is never reused. (S0002, story text)
7. The pull request number is recorded in the stage's next commit (result or stall), not in the stage-start commit, because that commit is pushed before the pull request can exist for a new branch. (S0003, story text)
8. A boundary error after the claim is pushed (`HostingServiceError`, `AgentRuntimeError`, `ProjectCommandError`, `GitError`, or a rejected result push) leaves the claim on the remote: F0005 builds no release for it. The next tick sees an own claim and F0008 reruns the stage as a crash, so a boundary error that repeats reaches F0008's crash cap and ends with the question "crashed". F0008 states and tests that path. This is chosen, not a gap. (S0003, S0007, story text)
9. A stall releases the claim in its own commit, so the next tick does not take a stalled stage for a crash. (S0004, story text)
10. The stall note is posted after the stall commit is pushed; a kill between the two loses the note and keeps the stall. (S0004, story text)
11. A stall note names the attempt, the cause and, until the cap, says it retries; it does not name the stage (the label and the journal do). (S0004, story text)
12. When the agent left the work item's branch, nothing it left is kept: the checkout goes back to the stage-start commit and the stall is committed there. (S0004, story text)
13. Only a form finding that was not there before the agent run stalls the stage (`form_invalid`); a finding already present, or one the agent fixed, does not. (S0005, story text)
14. An entry that is blank after the factory removes a leading `<role>:` or `<stage>:` is a stall with reason `no_result`. (S0005, story text)
15. When the factory undid paths, its paragraph `The factory undid changes outside the write paths: <paths>.` is added to the agent's entry. (S0005, story text)
16. A forward decision while the form has findings after the run becomes a question to the human (rule 1), with the findings in a `factory` entry of kind `question`; the round-cap question (rule 4) is such an entry too. A first stage that fixes every finding and decides forward moves by rule 6. (S0006, S0007, story text)
17. A forward move (rule 6 with every check green) resets `crashes` to 0 (R23); every other move and every stall leave it as it is. The function `decide` says nothing about `crashes`; the result commit sets it. (S0006, S0007, story text)
18. A red check is a stall whose note carries the last 15 lines of the check's output as the project command reports it (make's own error line included); a red report holds nothing; a label that cannot be written raises after the result commit is pushed and keeps the commit. (S0007, story text)
19. Each green check and each report adds a line `` `<command>`: <last line> `` below the agent's entry in the journal. (S0007, story text)
20. The sidecar file of cost records is rewritten from memory after every undo, because the undo reverts every path outside the write paths and the sidecar is such a path. (S0008, story text)
21. The cost line reads `<n> runs, <m> min, <t> turns, <i> tokens in (<c> more from cache), <o> out, $<usd>`, with cost rounded half up to two decimals and minutes to one; "in" is new input plus tokens written to the cache; a run whose cost is unknown adds `+ <n> unknown` after the dollars. (S0009, story text)
22. The cost table has the columns `stage | runs | min | turns | in | cached | out | USD` and a `**total**` row last. (S0009, story text)
23. The agent run's environment is the caller's: `TaskComposer`, `StageLauncher` and `StageRunner` take it as `environment: Mapping[str, str]` and F0005 passes it unchanged into the request. F0006's wiring supplies it with a `PATH` that holds `factory-guard` and a `HOME` (F0001 decision 17); F0010 scrubs it and its preflight probes `PATH` and `HOME`. (S0001, S0003, S0007, story text)
24. v1's decision `stuck` does not exist in v1.1: an agent that cannot finish ends with `question`, as F0001's budget resume text does. F0010-S0007 renames `stuck` in the carried texts. (S0001, story text)
25. The local branch of a work item that has a remote branch is reset to the remote's (R18), so v1's stall "cannot fast-forward to origin/<branch>" does not exist. (S0002, story text)
26. A "rework" is a decision other than the first entry of the stage's `next` (S0006). The interface sheet's `PipelineDefinition.position` (a move to a lower index) is not used for counting rounds; F0006's move rule must not count by position. (S0006, story text)
27. The undo reverts the work item's own cost-record file, which the factory itself rewrites; the entry's paragraph about what was undone leaves that file out, so an agent that wrote only inside its write paths gets an entry without the paragraph. (S0005, S0008, story text)
28. A form finding is "the same as before" when its message is equal after every run of digits is replaced by `#`, counted by occurrences: a message that occurs more often after the run than before is new. The messages carry line numbers that move when the agent edits above them. (S0005, story text)
29. A `HostingServiceError` during a stall propagates: raised while the pull request is ensured, nothing has been written yet; raised while the note is posted, the stall commit is already pushed and stays. (S0004, story text)
30. The factory adds exactly one commit (the stall or the result commit) above the stage-start commit or, when the agent committed itself, above the agent's last commit; the agent's own commits stay in the history (F0004 decision 15). (S0004, S0007, story text)
31. The result commit holds everything in the work tree: a file a check creates is committed unless the project's `.gitignore` covers it. The operator guide says so. (S0007, story text)
32. The stage's next commit holds the completed cost record only; the started record is replaced in place, so GH4.1's "both states in the next commit" means that neither is pushed before it. (S0008, story text)
