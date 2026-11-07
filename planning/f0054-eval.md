# F0054 eval

F0054 (the documents are rewritten for their readers): 22 rewrite stories on the docs route, one code story (F0054-S0023, the check reads an indented example and one without a command) and one acceptance (F0054-A0001). The data are the 24 cost files in `factory/archive/F0054-the-documents-are-rewritten-for-their-readers/done/`, the 242 transcripts in `session-logs/vm-f0054/`, the journals, the branch history in git, and the run log `docs/runs/2026-11-05-f0052/log.md`. Every cost record has a transcript of the same run id, so the match is exact. I found no key, token or credential in the transcripts (a pattern scan over all 242 files).

The prices behind the dollar figures are fitted from the cost records (the error is under one cent over all runs). On Opus a million output tokens cost $20, a million cache reads $0.20 and a million cache writes $8. On Sonnet the three are $10, $0.10 and $4. Every cache write in all 242 runs is a one-hour write; the client sets this, and I did not check whether the factory can choose the five-minute kind.

## 1. Totals

The feature ran 242 runs with 2,596 turns. They used 4,454 input tokens, 1,642,163 output tokens, 93,837,489 cache reads and 9,421,761 cache writes, and cost $98.26. The run log's $96.69 and 241 runs leave out the acceptance's own run ($1.57). The runs took 20,513 s (5.7 h), of which the model took 15,628 s (4.3 h).

Cache writes are 60 percent of the cost ($58.89), output is 25 percent ($24.24) and cache reads are 15 percent ($14.95).

### Per stage and role

| Stage (role, model) | Runs | Turns | Input | Output | Cache read | Cache write | Cost | Run time | Model time |
|---|---|---|---|---|---|---|---|---|---|
| docs-review (reviewer, Opus, high effort) | 109 | 1,352 | 2,386 | 736,843 | 52,454,954 | 5,049,086 | $65.63 | 8,697 s | 8,431 s |
| docs-only (documenter, Sonnet) | 103 | 1,057 | 1,806 | 835,731 | 37,253,961 | 3,757,899 | $27.28 | 10,681 s | 6,420 s |
| intake (intake, Sonnet) | 24 | 98 | 104 | 22,695 | 806,075 | 324,848 | $1.61 | 256 s | 211 s |
| acceptance (acceptance reviewer, Opus) | 1 | 33 | 62 | 23,058 | 1,788,097 | 94,060 | $1.57 | 449 s | 270 s |
| tests (tester, Opus) | 1 | 24 | 44 | 10,590 | 822,790 | 52,726 | $0.80 | 137 s | 132 s |
| doing (coder, Opus) | 1 | 13 | 24 | 5,077 | 390,430 | 45,643 | $0.54 | 182 s | 66 s |
| review (reviewer, Opus) | 1 | 7 | 12 | 5,546 | 152,958 | 37,604 | $0.44 | 68 s | 63 s |
| smoke-test (smoke tester, Opus) | 1 | 4 | 6 | 887 | 41,571 | 22,366 | $0.21 | 17 s | 15 s |
| docs (documenter, Sonnet) | 1 | 8 | 10 | 1,736 | 126,653 | 37,529 | $0.18 | 25 s | 21 s |

The review costs 2.4 times the writing. `docs-review` is 67 percent of the feature ($65.63) and `docs-only` 28 percent ($27.28). A review run costs $0.60 on average and a documenter run $0.26.

Per run, a review writes about 46,000 tokens into the cache and reads about 481,000; a documenter run writes about 36,000 and reads about 362,000. In the reviews, cache writes are $40.39 of $65.63 (62 percent): nearly every review loads its whole context fresh, because only the system prompt and the tools (about 11,000 tokens) come from an earlier run's cache. The first turn alone wrote 2,067,570 tokens over the feature (mean 8,544 per run), about $12.1 or 12 percent of the cost; F0052 finding 1 describes the cause.

The first pass of the 22 rewrite stories (intake, the documenter's first run, the first review) cost $33.73. The rework rounds after it cost $60.79, 62 percent of the feature: $45.00 in 87 later reviews and $15.79 in 76 later documenter runs. A later review costs $0.52 on average and the documenter's fix before it $0.21. S0023 and the acceptance cost $3.84.

### Per story, against the length of its page

The words are those of the page on `main` today (`wc -w`, code blocks included). "Long at round 0" counts the sentences of the page, as the first review saw it, that have more than 25 words or more than one parenthesis outside code (my own script, described under finding 1).

| Story (page) | Words | Runs | Cost | Reviews | Rounds with findings | Round caps | Findings at round 0 | Long at round 0 | Long at merge | $ per 1,000 words |
|---|---|---|---|---|---|---|---|---|---|---|
| F0054-S0018 (project guide pipeline.md) | 16,937 | 22 | $13.56 | 11 | 10 | 2 | 18 | 169 | 11 | 0.80 |
| F0054-S0001 (operator guide install.md) | 4,187 | 18 | $7.15 | 9 | 8 | 2 | 10 | 14 | 12 | 1.71 |
| F0054-S0020 (project guide README.md) | 8,468 | 12 | $7.12 | 6 | 5 | 1 | 15 | 85 | 39 | 0.84 |
| F0054-S0017 (project guide machine.md) | 11,097 | 14 | $6.26 | 7 | 6 | 1 | 11 | 74 | 58 | 0.56 |
| F0054-S0003 (operator guide machine.md) | 10,188 | 13 | $6.21 | 7 | 5 | 1 | 15 | 100 | 32 | 0.61 |
| F0054-S0015 (project guide agents.md) | 10,241 | 9 | $5.27 | 4 | 3 | 0 | 10 | 100 | 93 | 0.51 |
| F0054-S0012 (project guide shared.md) | 4,700 | 9 | $4.16 | 4 | 3 | 0 | 13 | 27 | 7 | 0.89 |
| F0054-S0002 (operator guide site.md) | 5,280 | 9 | $3.77 | 4 | 3 | 0 | 13 | 18 | 7 | 0.71 |
| F0054-S0016 (project guide watching.md) | 5,397 | 8 | $3.71 | 3 | 2 | 0 | 13 | 22 | 21 | 0.69 |
| F0054-S0013 (project guide hosting.md) | 5,308 | 9 | $3.55 | 4 | 3 | 0 | 9 | 22 | 22 | 0.67 |
| F0054-S0005 (operator guide agent-runtime.md) | 6,126 | 9 | $3.44 | 4 | 3 | 0 | 12 | 20 | 22 | 0.56 |
| F0054-S0007 (operator guide stops.md) | 8,487 | 7 | $3.40 | 3 | 2 | 0 | 10 | 53 | 32 | 0.40 |
| F0054-S0009 (operator guide records.md) | 3,422 | 12 | $3.36 | 6 | 5 | 1 | 12 | 30 | 22 | 0.98 |
| F0054-S0014 (project guide work.md) | 7,622 | 8 | $3.23 | 3 | 2 | 0 | 13 | 36 | 36 | 0.42 |
| F0054-S0019 (project guide operator.md) | 1,936 | 12 | $3.21 | 6 | 5 | 1 | 9 | 4 | 6 | 1.66 |
| F0054-S0011 (operator guide README.md) | 729 | 14 | $2.86 | 7 | 6 | 1 | 5 | 1 | 0 | 3.92 |
| F0054-S0006 (operator guide health.md) | 6,485 | 7 | $2.80 | 3 | 2 | 0 | 14 | 26 | 21 | 0.43 |
| F0054-S0021 (README.md) | 839 | 12 | $2.64 | 6 | 5 | 1 | 5 | 2 | 0 | 3.15 |
| F0054-S0010 (operator guide work-items.md) | 6,953 | 7 | $2.45 | 3 | 2 | 0 | 5 | 37 | 39 | 0.35 |
| F0054-S0004 (operator guide cloud-run.md) | 4,089 | 7 | $2.44 | 3 | 2 | 0 | 8 | 7 | 9 | 0.60 |
| F0054-S0008 (operator guide pipeline.md) | 2,521 | 7 | $1.99 | 3 | 2 | 0 | 3 | 8 | 8 | 0.79 |
| F0054-S0022 (operator/README.md) | 1,124 | 9 | $1.88 | 3 | 2 | 0 | 7 | 2 | 0 | 1.68 |

A straight line through the 22 stories gives about $1.18 per story plus $0.52 per 1,000 words (correlation 0.78). The number of long sentences at round 0 predicts the cost better (correlation 0.85). The four small pages (S0011, S0019, S0021, S0022) cost $1.66 to $3.92 per 1,000 words, two to eight times the large pages. Their extra rounds were mostly mechanical: S0011's last four rounds and S0019's last three were about links, and S0021's last two about sentence length.

### Where the 12 h 18 min went

The feature ran from 21:44Z to 10:03Z, 44,288 s.

- Agent runs: 20,513 s (46 percent). The model took 15,628 s of it. Of the 4,885 s outside the model, the documenters' own `make documents` took 3,593 s in 200 calls.
- The factory's checks after each `docs-only` run: 13,722 s (31 percent), 136 s per run on average over 101 runs. This is the gate's `make check`, `secrets` and `documents`.
- The human's approvals (the checks and the merge of 22 pull requests): about 4,550 s (10 percent).
- The human's answers to 15 questions, 11 of them round caps: 2,375 s (5 percent).
- The rest, about 3,100 s (7 percent), is the factory's starts and the time between work items.

`make documents` took about 2 s at F0054-S0001 and grew as pages were listed. It jumped from about 18 s to about 60 s with the first `docs-only` run of F0054-S0020 (project guide README.md), whose page added `console` blocks that run `uv run pytest` over seven test modules and `check_demos`. I did not time the blocks one by one. Since then every documenter run and every gate pays about 60 s for it.

## 2. Findings, ordered by saving

### Finding 1: sentence length and link rules, judged by eye, made 16 rounds and four of the eleven round caps

- **What.** I sorted all 458 numbered findings of the 86 `docs-review` results that sent a page back into six kinds, by keywords, and checked a sample of 50 by hand (about one in seven was in a neighbouring kind, mostly fact against missing item). The kinds are: a false fact against the code (113), a missing item in a list that claims to be complete (29), an old fact dropped without being named, criterion 2 (26), links and glossary first use (93), sentence length or parentheses (89), and other style (108: private words, history, `sh` blocks that do not say where they run, steps with more than one action). I spread the cost of each round, the documenter's fix and the next review, over its findings. Fact $17.47, missing item $3.79, dropped fact $3.18, links $12.25, length $16.85 and other style $13.43, $66.97 in all. Sixteen rounds held only length and link findings; they cost $10.18 and about 70 minutes of wall time with their gates. Four of the eleven round caps came from such a round: F0054-S0011 (operator guide README.md), F0054-S0018 (project guide pipeline.md, its second cap), F0054-S0019 (project guide operator.md) and F0054-S0021 (README.md).
- **Evidence.** The cap review of F0054-S0019, `21fcd072`, wrote: "All four findings are link placements; no fact on the page is wrong". The second cap of F0054-S0018, `b2f2f103` ($1.32, 237 KB of tool output), held two findings, both rule 2, and listed a new batch of sentences. The link findings split into glossary words not linked at their first use (38), files linked twice or not at their first mention (26), files named but not linked or paths not from the root (24) and heading references (5). The by-eye judgment was also uneven. My counter, which drops code spans, link targets, code blocks, headings and tables, finds on `main` today 455 sentences of more than 25 words, 187 of more than 30 and 62 with more than one parenthesis outside code in the 22 pages. pipeline.md, which the human had checked by script, has 11 sentences of 26 to 30 words and none longer. agents.md has 42 sentences of more than 30 words, though its reviews raised only two length findings.
- **Saving.** About $10 to $12 and 70 minutes per feature of this kind: the 16 mechanical rounds, and the human's answers and the repeat reviews at four caps. The documenter would also meet every instance on the page in its first run, on Sonnet.
- **Change.** A check in code, in `make documents`, printed in the report for every checked document: a sentence of more than 30 words, or with more than one parenthesis outside code; a glossary word whose first use in the file is not a link to the glossary; a repository file named in backticks that is never linked, or linked more than once; a path that does not start at the repository root. It should start as a report on the lines the branch changed, as F0052 finding 6 proposed, and turn into findings once the pages are clean (today it would print about 190 long sentences). In `agents/agents/reviewer.md`, `### docs-review`, step 3: "Rule 2 and the link rules are the check's: do not count words or links by eye, and do not raise a point the check's report does not print." In `agents/agents/documenter.md`, `### docs-only`: "Fix every point of the report's style section in the lines you changed before you end."

### Finding 2: 46 percent of the late findings with a quote pointed at text that was already there in round 0

- **What.** The `docs-review` subsection replaces the review's checklist, and with it the code review's rule to list every gap of a group in one round. The docs reviewers named examples of a rule ("several sentences") and found more of the same in each later round. The documenter's rule, "fix exactly its numbered findings", then fixed only the lines named.
- **Evidence.** I took the reviews from the third on (53 rounds with findings, without the reviews that ran straight after a cap answer) and looked up each quoted phrase of a finding in the page as the first review saw it, from the branch's history. Of 130 late findings with a quote, 60 pointed at text that was already there at round 0, 25 at text that the documenter's own fixes wrote (13 of those are new false facts, such as a split sentence that lost its condition), and 5 repeated an open finding. In 20 late rounds ($13.05), every finding with a quote pointed at round-0 text. F0054-S0003 (operator guide machine.md), round-3 review `650042e6`: seven of its nine findings were sentences of 33 to 55 words, all in the round-0 page. F0054-S0016 (project guide watching.md), round-1 review `a2e88bf7`: three false facts, all in the round-0 page. The log of 06:48Z says of F0054-S0018 that each round brought "a new batch" of long sentences.
- **Saving.** About $6 to $9 per feature of this kind: half of the 20 rounds, less the three that finding 1 already removes.
- **Change.** In `agents/agents/reviewer.md`, `### docs-review`, a new step after step 3: "At round 0, read the whole page and list every finding of every kind, every instance of a rule, not examples; a point you could have named at round 0 and name later costs the work item a whole round. From round 1 on, judge the lines changed since your last review and the open findings, and raise a point on unchanged text only when it is a false fact." In `agents/agents/documenter.md`, `### docs-only`, the bullet on the reviewer's findings: "A finding that names a rule asks for every instance on the page: fix them all, and when you split or reword a sentence, keep every condition it held."

### Finding 3: a later review costs about $0.05 plus $0.006 for every kilobyte it reads, and it reads 80 KB

- **What.** From round 1 on, a review checks a few fixes, but it reads as much as the first one: the whole work item, the whole diff against `main` (for a rewrite, the old and the new page), the style page and the page again. The first command, which step 1 asks for, is often too large for one tool result, so the output is saved to a file and read again in parts.
- **Evidence.** Over the 87 later reviews, cost follows the bytes of tool output (correlation 0.93): about $0.047 per run plus $0.0059 per KB. They read 80 KB on average, 48 KB of it in results over 20 KB. 47 reviews read a saved tool output back (1.84 MB). Only 24 of the 87 used a diff since the last review, and they still read the whole page, so they cost about the same ($0.47 against $0.53). The work item alone is 14 percent of the reviews' cache writes, and 19 percent from round 1 on: F0054-S0018's work item grew from 11 KB at its first review to 82 KB at its eleventh. `style.md` (12 KB) was read in 73 of the 109 reviews and in 60 of the 103 documenter runs. The cheapest later reviews, for example `5841f4cd` of F0054-S0021 (README.md, $0.19), read 39 KB.
- **Saving.** About $8 per feature of this kind, if a later review reads about 40 KB instead of 80; about $0.2 per later review.
- **Change.** In `agents/agents/reviewer.md`, `### docs-review`, step 1 for a round above 0: "Read the work item from `## Description` to `## Smoke test` and its last two journal entries, `git diff <the commit your last review read>..HEAD` for the documents, and the code that the open findings name. Read the page in full only at round 0." The factory could name the last reviewed commit in the prompt, or candidate 12 of F0052 (a per-run slice of the work item) could provide it.

### Finding 4 (confirms F0052 finding 5, with this feature's numbers): the gate's `make check` after every `docs-only` run took 3.8 hours

- **What.** After each documenter run, the gate runs `make check`, `secrets` and `documents` before the review starts. For a change of documents only, only the guard tests that read documents can turn red.
- **Evidence.** 101 gate runs took 13,722 s, 136 s each, 31 percent of the feature's 12.3 hours. Four of them were red, and all four were guard tests that read the documents: `tests/guards/test_project_guide_files.py` in F0054-S0014 (project guide work.md) and F0054-S0018 (project guide pipeline.md), `tests/guards/test_root_operator_folders_removed.py` in F0054-S0022 (operator/README.md), and one in F0054-S0016 (project guide watching.md). The reruns cost $0.21.
- **Saving.** About 3 hours of wall time per feature of this kind (about 2 minutes per `docs-only` run), and no tokens.
- **Change.** As F0052 finding 5 proposed: a project command for the tests that read the real documents, and in `factory/pipeline.yml`, `docs-only: checks: [guides, secrets, documents]`, with a guard that keeps such tests marked. The full `check` still runs on the merged tree. This needs the human.

### Finding 5 (new): `make documents` now takes about 60 s, and both the documenter and the gate pay for it

- **What.** Since F0054-S0020 (project guide README.md), `make documents` takes about 60 s instead of about 18 s. The page's `console` blocks run test modules with `uv run pytest` and run `check_demos`; the style page skips only a block that runs the whole suite.
- **Evidence.** The documenter's own calls took 3 s on F0054-S0001 (operator guide install.md), about 18 s on F0054-S0019 (project guide operator.md), and 59 to 62 s from the first `docs-only` run of F0054-S0020 on (F0054-S0021 and F0054-S0022: 13 calls, 780 s). The journal's `documents ok` lines go from 1.9 s to 59.2 s. Documenters called it 200 times in this feature, about two times per run.
- **Saving.** About 80 s per `docs-only` run for every later feature (40 s in the documenter's call and 40 s in the gate's), about 2 hours for a feature with 100 such runs. No tokens.
- **Change.** Time the blocks of `docs/project-guide/README.md` once. If the pytest blocks are the cost, either mark them as not run (as `suite` blocks are), or let the check reuse a block's result while the files it runs are unchanged, as the gate reuses `check`. This is a code story and needs the human's word, since the style page decides which blocks run.

## 3. Carried over

- F0052 finding 1 (the run's first message is written into the cache again): confirmed. The first turn wrote 2.07 million tokens in 242 runs (192 runs over 5,000 tokens), about $12.1, 12 percent of the feature. It is still the largest single saving that is open.
- F0052 finding 2 (the acceptance loop): refuted for this feature. One acceptance ($1.57, 1 run) was enough, because the feature's decision let it propose stories only for false facts, broken links and examples that do not run.
- F0052 finding 3 and F0053 finding 2 (coder runs that change nothing): not tested. The only coder run, of F0054-S0023 (the check reads an indented example and one without a command), built code.
- F0052 finding 4 (questions an earlier role could have removed): partly confirmed. Of the four questions that were not round caps, F0054-S0023's intake question was answered "as the intake proposed".
- F0052 finding 5 (the gate after `docs-only` runs the whole suite): confirmed at scale, finding 4 above.
- F0052 finding 6 (review rounds on sentence length): confirmed at scale, finding 1 above: 89 length findings and 16 mechanical rounds.
- F0052 finding 7 (work-item text read in full): confirmed. The work item is 14 percent of the reviews' cache writes and 19 percent from round 1 on (finding 3 above).
- F0052 finding 8 (the smoke tester on Opus): neither confirmed nor refuted. One smoke test ran ($0.21).
- F0052 finding 9 (a run with a result recorded as a crash): did not recur. All 242 runs ended `completed`, and no crash was recorded.
- F0053 finding 1 (tests that run on copies of the real documents): did not recur. The acceptance's `make check` was green at once, though 22 pages were listed. The four red gates in finding 4 came from guard tests that read the real documents, a smaller cousin of the same coupling.
- F0053 findings 3, 4, 5 and 8 (copied test helpers, leaves for earlier tests, added criteria, the tester's type check): not tested. The docs route has no tester or coder.
- F0053 finding 6 (stories stopped at the intake): did not recur. The intake asked once in 23 stories (F0054-S0023).
- F0053 finding 7 (after a cap answer the reviewer runs again before the work goes on): confirmed. All 11 cap answers were followed by a review before any documenter run: 11 runs, $2.96. The reviews `390e7682` of F0054-S0003 (operator guide machine.md) and `0ac368b7` of F0054-S0019 (project guide operator.md) say that no documenter run came after the answer.
