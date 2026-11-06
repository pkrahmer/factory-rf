# F0052 eval

F0052 (a documents-only story takes the docs route), evaluated on 2026-11-06. The figures come from the 88 cost records in `factory/archive/F0052-a-documents-only-story-takes-the-docs-route/done/`, the journals of the 13 work items, the 89 transcripts in `session-logs/vm-f0052/` and the night log `docs/runs/2026-11-05-f0052/log.md`. Dollar values are the cost records' `cost_usd`. Where I split a cost into its parts, I used prices fitted to the transcripts' own cost lines: on Opus, cache creation is about half of the cost, cache reads about 30 percent and output about 20 percent; on Sonnet, cache creation is about two thirds. An Opus token costs about 1.9 times a Sonnet token. Every run wrote its cache with the one-hour lifetime. I found no key, token or credential in the transcripts.

## 1. Totals

### Per work item

"Run time" is the sum of the agent runs' durations. "Elapsed" is the time from the first to the last journal entry.

| Work item | Runs | Turns | Input | Output | Cache read | Cache creation | Cost | Run time | Model time | Elapsed |
|---|---|---|---|---|---|---|---|---|---|---|
| S0001 (a story can take a second route to a second approval) | 10 | 88 | 152 | 37,446 | 2,582,123 | 321,480 | $3.53 | 854 s | 494 s | 21.6 min |
| S0002 (the agents know the docs route) | 19 | 127 | 210 | 49,259 | 2,668,427 | 400,721 | $4.40 | 1,233 s | 607 s | 44.0 min |
| S0003 (the documents have a style page and a glossary) | 10, and 1 crashed run with no record | 61 | 96 | 26,797 | 1,178,413 | 209,594 | $1.96 | 472 s | 303 s | 28.8 min |
| A0001 (the first acceptance) | 1 | 50 | 96 | 37,439 | 4,564,873 | 141,022 | $2.79 | 578 s | 428 s | 11.7 min |
| S0005 (a guide rewrite may rename its headings and add a page) | 7 | 47 | 72 | 18,895 | 946,024 | 163,315 | $1.56 | 374 s | 215 s | 13.4 min |
| S0004 (an acceptance merged at its review stage says so on every route) | 14 | 115 | 196 | 48,277 | 3,069,349 | 324,833 | $3.93 | 1,386 s | 610 s | 37.6 min |
| A0002 (the second acceptance) | 1 | 45 | 84 | 31,166 | 3,381,138 | 111,735 | $2.19 | 536 s | 355 s | 13.0 min |
| S0006 (the docs reviewer judges by the style page alone) | 6 | 30 | 46 | 8,787 | 458,163 | 99,467 | $0.90 | 271 s | 108 s | 11.8 min |
| S0007 (the project guide names the headings a check still requires) | 6 | 38 | 54 | 9,111 | 608,640 | 130,522 | $0.94 | 126 s | 113 s | 9.5 min |
| A0003 (the third acceptance) | 1 | 38 | 66 | 35,948 | 2,602,940 | 111,820 | $2.13 | 555 s | 395 s | 13.3 min |
| S0008 (the operator guide says the check reads the documents) | 5 | 31 | 48 | 12,814 | 543,679 | 94,585 | $0.82 | 158 s | 148 s | 10.0 min |
| S0009 (the project guide says which index lines name a page) | 7 | 35 | 50 | 10,132 | 494,627 | 119,224 | $0.95 | 153 s | 137 s | 13.2 min |
| A0004 (the fourth acceptance) | 1 | 27 | 50 | 20,602 | 1,412,700 | 76,013 | $1.30 | 388 s | 228 s | 10.8 min |
| **F0052** | **88** | **732** | **1,220** | **346,673** | **24,511,096** | **2,304,331** | **$27.41** | **7,083 s (118 min)** | **4,141 s (69 min)** | **4 h 17 min** |

The night log gives the feature's total as $18.99 and 84 runs. That is the stories alone. The four acceptances add $8.41 and 4 runs, so the real total is $27.41, and the acceptances are 31 percent of it. The crashed documenter run of S0003 (`40bfc91b`, about $0.16) has no cost record and is not in the sums.

### Per stage and role

| Stage (role, model) | Runs | Cost | Cost per run | Turns | Output | Cache creation | Run time | Model time |
|---|---|---|---|---|---|---|---|---|
| acceptance (acceptance reviewer, Opus) | 4 | $8.42 | $2.10 | 160 | 125,155 | 440,590 | 2,057 s | 1,406 s |
| tests (tester, Opus) | 14 | $5.04 | $0.36 | 137 | 62,189 | 374,805 | 962 s | 776 s |
| review (reviewer, Opus) | 11 | $4.74 | $0.43 | 92 | 58,929 | 380,225 | 704 s | 680 s |
| doing (coder, Opus) | 19 | $3.42 | $0.18 | 109 | 29,478 | 300,409 | 2,429 s | 452 s |
| docs-review (reviewer, Opus) | 7 | $1.70 | $0.24 | 36 | 17,773 | 153,017 | 227 s | 215 s |
| smoke-test (smoke tester, Opus) | 6 | $1.22 | $0.20 | 31 | 7,263 | 121,784 | 148 s | 112 s |
| docs-only (documenter, Sonnet) | 10 | $1.08 | $0.11 | 72 | 18,608 | 192,207 | 248 s | 223 s |
| intake (intake, Sonnet) | 11 | $0.90 | $0.08 | 57 | 14,508 | 174,009 | 167 s | 147 s |
| docs (documenter, Sonnet) | 6 | $0.88 | $0.15 | 38 | 12,770 | 167,285 | 142 s | 130 s |

### Where the 4 h 17 min went

- Agent runs: 7,083 s (46 percent). Model time is 4,141 s of it. About 2,600 s of it is `make check` run by the agents themselves: 12 coder runs at about 150 s each (1,953 s) and the four acceptances at about 150 s each.
- The factory's checks and steps between an agent's result and the next stage: 3,265 s (21 percent). Nearly all of it is the gate's `make check`: 1,537 s after `doing` and 1,189 s after `docs-only`.
- The human's answers to 8 questions: 1,369 s (9 percent), each wait 110 s or 230 s.
- The human's approvals (the six checks and the merge): 2,190 s (14 percent), 50 to 250 s per work item.
- Between work items (the pipeline change and the image rebuilds on factory-vm): 1,106 s (7 percent).

`make check` ran for about 5,300 s in all, about 88 minutes or 34 percent of the elapsed time.

### The two routes, side by side

| Story | Route | Runs | Cost | Elapsed | First pass (intake, writer, first review) | Rounds after it |
|---|---|---|---|---|---|---|
| S0007 (the project guide names the headings a check still requires) | docs | 6 | $0.94 | 9.5 min | $0.66, with one stall | 1 round, $0.27 |
| S0008 (the operator guide says the check reads the documents) | docs | 5 | $0.82 | 10.0 min | $0.48 | 1 round, $0.34 |
| S0009 (the project guide says which index lines name a page) | docs | 7 | $0.95 | 13.2 min | $0.38 | 2 rounds, $0.58 |
| S0006 (the docs reviewer judges by the style page alone) | code | 6 | $0.90 | 11.8 min | - | none |
| F0051-S0013 (the push error example, a documents-only story) | code | 6 | $0.75 | - | - | none |

The docs route works, but it is not yet cheaper than the code route for a one-paragraph change. Its first pass costs $0.38 to $0.66. The review rounds then add 44 percent ($1.19 of $2.71), and since the third acceptance the gate's `make check` after each `docs-only` run adds about 150 s per run. In S0009 the gate took 452 s of the story's 793 s. The dearest stage is `docs-review`: $1.70 of the three stories' $2.71 (63 percent), at $0.17 to $0.35 per run against $0.07 to $0.15 for the documenter. The reviewer runs on Opus with high effort; about 60 percent of a `docs-review` run's cost is cache creation, and 10,000 tokens of that is the fixed start of every run (finding 1). The documenter runs on Sonnet.

## 2. Findings, ordered by saving

### Finding 1 (new): every run writes the same 10,000 tokens into the cache again, because the run's own prompt sits at the end of the cached block

- **What.** The system prompt and the tools (about 11,000 tokens) are read from the cache in every run. The first user message is not. It holds `CLAUDE.md` (20 KB), a system message with the environment and the account's skill listing (8.5 KB, skills such as dataviz that no agent uses), and then the factory's prompt with the work item, the stage, the round and the pull request. The prompt differs from run to run, so the whole first message, about 10,000 tokens, is written to the cache again, at twice the input price.
- **Evidence.** In S0002 (the agents know the docs route), every run whose prompt was word for word the same as an earlier run's (the same stage and the same round) read 20,114 tokens from the cache on its first turn and created none: coder runs `6affa672`, `41e72df8`, `99dd4707`, `2aafdddb`. Every run whose round differed created about 10,150 tokens on its first turn: `b516ff97`, `f51166b4`, `79a1ac03`. The three `docs-review` runs of S0009 (the project guide says which index lines name a page) each created 10,153 tokens on their first turn. Over the feature, 72 of 89 runs paid this start: 852,000 tokens of first-turn cache creation, about $4.9 or 18 percent of the feature. No run called the `Skill` tool.
- **Saving.** About $2.5 to $3 per feature (9 to 11 percent), about $0.03 to $0.04 per run, if most runs of a role within the cache's hour hit. No time saving.
- **Change.** A code change in the factory's run start: make the first prompt the same for every run of a role (for example "Your run's facts are in `<file>`"), and put the run's lines (work item, stage, allowed decisions, branch, pull request, round) in that file, which the agent reads with the work item in its first command. Second, turn off the account's skills in the stage image and drop `Skill` from the agent files' tools until a project skill exists (saves about 2,000 tokens per run either way). Confirm the hit with one test run before the change is built; the cost record's first-turn cache creation shows it.

### Finding 2 (new): the acceptance loop cost 64 percent of the feature, and a shorter loop would have found the same things

- **What.** The three first stories cost $9.89. After them came four acceptances ($8.41) and six proposed stories ($9.10). Each further acceptance read the previous acceptance and every new story in full, ran `make check` on a tree the gate had passed, and wrote a new feature smoke test.

| Acceptance | Cost | Elapsed | What it found | Its stories |
|---|---|---|---|---|
| A0001 (the first acceptance) | $2.79 | 11.7 min | a real bug (an early-merged acceptance loses its entry) and a need of the next feature | S0004 $3.93, S0005 $1.56 |
| A0002 (the second acceptance) | $2.19 | 13.0 min | a stopgap that had run out, and a missing sentence in the index | S0006 $0.90, S0007 $0.94 |
| A0003 (the third acceptance) | $2.13 | 13.3 min | a real gate hole: `make check` was reused after a documents-only change, though tests read the documents | S0008 $0.82, S0009 $0.95 |
| A0004 (the fourth acceptance) | $1.30 | 10.8 min | one stale sentence, which the operator fixed on `main` instead of a story | none |

- **Evidence.** The gate hole was there from the start, but A0001's feature smoke test walked the docs route only through the stages and never asked whether `check` reran after a documents-only change. A0003 found it only because S0007's broken guard was caught by an image change. S0009 is one sentence in `docs/project-guide/README.md`, a file that F0054's rewrite rewrites anyway. The acceptances' tool output was 683 KB, and 334 KB of it (49 percent) was work-item text: A0002 read A0001's report (19.5 KB) and S0004 and S0005 in full (63.7 KB). Each acceptance ran `make check` for about 150 s (A0001 call: `make check 2>&1 | grep -E "green|red|FAILED|..."`). The cache reads, which grow with every turn of a long context, were about 44 percent of the acceptances' cost (11.96 million tokens).
- **Saving.** About $3 and 35 minutes per feature of this kind: one acceptance fewer ($1.30 to $2.19, about 11 minutes), one document story fewer ($0.95, 13 minutes), and about $0.15 and 150 s per acceptance from the two input changes below.
- **Change.**
  1. A rule in `agents/agents/acceptance-reviewer.md`, check 2: "When the feature adds a stage or a route, the feature smoke test also checks every project command the new stages run, and whether a known result is reused there." This is the test that would have found A0003's hole at A0001.
  2. A rule in `acceptance-reviewer.md`, under Proposals: "A proposed story that only rewords a document which a later feature's backlog already rewrites goes into that feature's backlog as a note, not into this feature. A one-sentence correction of a document is listed for the human, not proposed as a story." The operator already did this by hand for S0010.
  3. A further acceptance reads the previous report's Recommendation and Proposed stories sections only, and for each new story its Description, Interface, criteria and the last review entry. The factory can put this digest in the prompt. It also gives the gate's known result (candidate 47), so the acceptance runs `make check` only when the tree has changed since.

### Finding 3 (confirms candidates 1 and 2, new numbers; new: three stories had no work for a coder at all)

- **What.** 13 of the 19 coder runs changed nothing: they relayed a test change, said there was nothing to build, or ran `make check` on the tester's tree. Eight of them ran `make check` themselves for about 150 s, and the gate then ran it again on the same tree.
- **Evidence.** S0001 (a story can take a second route to a second approval) and S0005 (a guide rewrite may rename its headings and add a page) change only tests and documents, and S0003 (the documents have a style page and a glossary) came to the coder by the way back from `docs-only`. Their coder runs `a66fb417`, `d7de45b2` and `584f96e3` each built nothing ($0.22, $0.16, $0.17, about 160 s each). S0003's coder wrote: "I built nothing, because there was nothing to build." The relays are `7b341a9c` and `db3000ac` (S0001), `6affa672`, `41e72df8`, `99dd4707`, `79a1ac03` and `2aafdddb` (S0002), and `5ddac77f`, `b51faaff` and `883f7347` (S0004). Together the 13 runs cost $1.86 and took 1,416 s of run time.
- **Saving.** About $1.5 to $1.9 and 23 minutes per feature of this size.
- **Change.** In `factory/pipeline.yml`: `tests: next: [doing, review]` and `review: next: [docs, doing, tests]`, so a story whose Interface changes nothing in the coder's write paths goes from `tests` to `review`, and a review whose findings are all in `tests/` goes back to `tests`. The gate's `check` moves onto `tests` for that forward move. In `agents/agents/intake.md` and `tester.md`: the intake names this case as it names the docs route, and the tester ends with `review` when the Interface gives the coder nothing. In `coder.md`, R11: "When you changed no file since the last green check that the journal names, do not run `make check`; the factory runs it." This needs the human's decision, because it changes the stage graph.

### Finding 4 (confirms candidates 37, 60 and 64; new: all eight questions had a cause that an earlier role could have removed)

- **What.** The eight questions cost about $2.1 in reruns and relays and 1,369 s of waiting. Three came from the first acceptance's two stories.

| Question | Asked by | What the human said | Who could have prevented it | Cost of rerun and relays; wait |
|---|---|---|---|---|
| S0002 entry 3 | intake | "Yes to all five, as you propose" (five criteria for behaviours the Interface named) | the story form already says "every behaviour named here has its own criterion"; the intake may add such criteria itself and note them | $0.04; 230 s |
| S0002 entry 8 | tester | (a), (a), (a): the tester's own first options; the seven style rules had to be quoted in the answer, because the tester may not read `feature.md` | the story: quote every list it refers to | $0.24; 110 s |
| S0002 entry 13 | coder | (a), a leave for an earlier CRC test of `reviewer.md` | the intake: grep the tests that read the files the Interface changes | $0.42; 234 s |
| S0003 entry 10 | tester | (a), after the `docs-only` stall: the guard expects an exact list of files in `docs/project-guide/` | the intake: grep `tests/` for the folder a new file goes into | $0.41 with the stall; 232 s |
| S0003 entry 17 | reviewer | (b): end with `docs`, the documenter fixes five document findings | `reviewer.md`: findings only in documents go forward to `docs` with the list | $0.15; 110 s |
| S0004 entry 7 | coder | (a): the new test in `tests/work/application/` must import from `factory.work` (the area guard) | the acceptance's story or the tester: run `tests/guards` on new test modules | $0.42; 111 s |
| S0004 entry 18 | coder | (a), a leave: `PipelineDefinition.position` lost its last caller | the acceptance: A0001 grepped `\.position(` and saw that the only caller was the function S0004 replaces, but its story did not say the method goes | $0.35; 232 s |
| S0005 entry 3 | intake | four points "as the intake proposed" (the forms of an index line) | the acceptance's story: give the accepted and refused forms, as the story form asks | $0.06; 110 s |

- **Saving.** About $1.5 to $2 and 20 minutes of waiting per feature. The acceptance's part is about $0.8 and 7.5 minutes.
- **Change.**
  1. In `agents/agents/intake.md` (F0051 finding 1, still not built): grep the tests that read every file the Interface changes or adds to, and name each earlier test that must change; when the Interface names a behaviour without a criterion, add the criterion and say so in the entry instead of asking.
  2. In `agents/agents/acceptance-reviewer.md`, Proposals: "For each function a proposed story changes, grep its callers and the tests that pin it. Name in the Interface each method that loses its last caller and each earlier test that must change, and ask the human for the leave in the report, so that it is in `feature.md` before the story starts. Give each new test module's area import." This extends candidate 64.
  3. In `factory/story-form.md`: "A story quotes every list, rule or name it relies on; a story's agents may not read `feature.md` or `planning/`."
  4. In `agents/agents/reviewer.md`: "On the code route, findings that are all in the documenter's write paths go forward with `docs` and the numbered list; they need no question."

### Finding 5 (new): on the docs route, the gate runs the whole suite after every documenter run

- **What.** Since the human's change before S0008, `check` is no longer reused after a documents-only change, which is right. But `docs-only` now runs the full `make check` (about 150 s) after every documenter run, also in every round. Only the tests that read the documents can turn red from a documents-only change. A0003 listed them: the guide guards under `tests/guards/` and a few agent-file tests.
- **Evidence.** S0008 (the operator guide says the check reads the documents) had 2 `docs-only` runs and S0009 (the project guide says which index lines name a page) had 3; the gate ran after each one, about 750 s in all. In S0009 the `docs-only` stage took 506 s from start to result, of which the documenter's three runs took 54 s. The documenters' own runs of the guide guard took under 5 s.
- **Saving.** About 130 s per `docs-only` run, so 4 to 6 minutes per docs story with one or two rounds. F0054 rewrites the guides in about 20 docs stories, so there it is about 1.5 to 2 hours. No token saving.
- **Change.** A project command `guides` (pytest over the tests that read the real documents, chosen by a marker or a folder) and, in `factory/pipeline.yml`, `docs-only: checks: [guides, secrets, documents]`. Add a guard test that every test which reads a document from the repository root carries the marker, so that A0003's hole cannot open again. The full `check` still runs on the merged tree. This is the human's change and needs his decision.

### Finding 6 (new): S0009 spent both of its review rounds on sentence lengths, and the second long sentence came from the reviewer's own fixes

- **What.** S0009 used its whole round cap. Round 0 had two findings, a 55-word sentence and a rule that the italic list items below it seemed to break. Each finding proposed a fix, and the documenter put both fixes into one sentence of 35 words. Round 1 flagged that sentence. Round 2 accepted a sentence of about 27 words. In S0008 two of the three round-0 findings were sentence lengths as well; the third was a real fact error, so that round would have happened anyway.
- **Evidence.** S0009 rounds 1 and 2 cost $0.58 (documenter `d1e45b24` and `b1b29fa9`, reviewer `43c1f635` and `a3b68ead`) and about 6.5 minutes, 300 s of it the gate. Every `docs-review` run read `docs/project-guide/style.md` again (8 reads of 5 KB in 7 runs). Round 1's entry: "It has about 35 words and three ideas".
- **Saving.** About $0.6 and 7 minutes in this feature, and more in F0054, where every story is prose.
- **Change.** In `agents/agents/documenter.md`, `### docs-only`: "Before you end, list the sentences of more than 25 words in the lines you changed, with a one-line script, and split each one or say in your entry why it stays." In `agents/agents/reviewer.md`, `### docs-review`, step 4: "For a writing finding, write the replacement sentences in full and within the style rules; the documenter uses them as given." A later code story could let `make documents` print the long sentences of the changed lines as a warning.

### Finding 7 (confirms candidate 12, with the share): about half of all tool output is work-item text

- **What.** The runs printed 3.1 MB of tool output, and 51 percent of it was work items, read in full. The share is 90 percent for the smoke tester, 81 percent for the intake, 66 percent for the coder, 56 percent for `docs-review` and 49 percent for the acceptances.
- **Evidence.** The smoke tester of S0003 (the documents have a style page and a glossary), `bb0beb1d`, read 29 KB of work item to run two commands. The reviewer of S0008 (the operator guide says the check reads the documents) read 13.6 KB in round 0 and 18.9 KB in round 1, though round 1 needed only the last two entries.
- **Saving.** About $0.05 to $0.10 per run that reads the work item twice or late, about $1 to $1.5 per feature. This overlaps with finding 1, since the text is cache creation.
- **Change.** As candidate 12 proposes: the factory puts the slice from Description to Smoke test and the last two journal entries into a file per run, and the agent files read that file instead of the whole work item.

### Finding 8 (new, a trial): the smoke tester runs on Opus for work that is mostly copying commands

- **What.** The six smoke-test runs cost $1.22, about $0.20 each, for 4 to 6 turns of running the story's commands and comparing the output with `Expect:`. On Sonnet, as the intake and the documenter run, the same runs would cost about $0.10 to $0.11.
- **Evidence.** The six runs `9b52232c`, `93002795`, `bb0beb1d`, `951f9792`, `c973cfc4`, `de69386c` each had 3 to 4 Bash calls and no finding.
- **Saving.** About $0.10 per code-route story, $0.6 in this feature.
- **Change.** `model: sonnet` in `agents/agents/smoke-tester.md` for one feature as a trial, with a check of the smoke test's results at each approval. Keep Opus for the reviewer: S0008's docs review found a real fact error (`docs/runs/` holds a `.json` and a `.log` file).

### Finding 9 (confirms candidate 26): a documenter run that ended with a result was recorded as a crash, and left no cost record

- **What.** The `docs` run `40bfc91b` of S0003 (the documents have a style page and a glossary) gave its structured result at 23:21:15. The factory wrote "crash 1: the run of stage docs ended without a result" at 23:25:16 and ran the stage again (`9a557d89`). The journal does not say why.
- **Saving.** About $0.16 and 4.5 minutes when it happens; the larger cost is that the record is missing.
- **Change.** Investigate why a run with a result counted as a crash (the log has no line for it). A crash entry should name what the factory saw, for example the exit code or the lease.

## 3. Carried over

Carried over: this feature confirms candidates 1 and 2 (13 coder runs that changed nothing, $1.86, finding 3), 5 (S0002's round 2 came from two criteria the reviewer added in round 1, $0.96), 12 (51 percent of tool output is work-item text, finding 7), 13 and 29 (each `docs-review` round read the whole diff and the style page again), 26 (finding 9), 28 (six denials, all in the acceptances, five of them a `rm -rf /tmp/...` cleanup), 37 (three of the eight questions only confirmed the agent's proposal), 47 (all four acceptances ran `make check`, about 150 s each), 60 and F0051 finding 1 (the intake still does not grep the tests that read what a story changes: S0002 entry 13, S0003 entry 10) and 64 (an acceptance's stories missed a removal and an area import); it refines candidate 46, because the docs route removes the three empty stages but its review rounds and the gate after each documenter run take most of that saving back; and it reverses F0051's note that the gate reuses a passed tree after the documenter, which is now gone on purpose (the human's change before S0008).
