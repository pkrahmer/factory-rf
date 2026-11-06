# F0053 eval

F0053 (the documents are checked against the code), evaluated on 2026-11-06. The figures come from the 213 cost records in `factory/archive/F0053-the-documents-are-checked-against-the-code/done/`, the journals of the 23 work items, the 213 transcripts in `session-logs/vm-f0053/` (one per run; the file name is the run id, so every transcript matched its cost record), the night log `docs/runs/2026-11-05-f0052/log.md` and the agent files and pipeline definition named below. Dollar values are the cost records' `cost_usd`. Where I give a dollar value for tokens alone, I use the rate the F0052 eval fitted. I searched every transcript for the usual key and token patterns and found no key, token or credential.

## 1. Totals

### Per work item

The rows are in build order. "Run time" is the sum of the agent runs' durations. "Elapsed" is the time from the first run's start to the last run's end.

| Work item | Runs | Turns | Input | Output | Cache read | Cache creation | Cost | Run time | Model time | Elapsed |
|---|---|---|---|---|---|---|---|---|---|---|
| S0001 (every name a document writes in backticks exists) | 14 | 108 | 176 | 57,335 | 2,496,614 | 369,832 | $4.27 | 1,485 s | 651 s | 40.1 min |
| S0002 (the operator guide's settings agree with the settings code) | 13, one of them killed by the pause with no cost | 93 | 152 | 47,204 | 2,441,656 | 390,289 | $4.18 | 1,087 s | 609 s | 267.5 min (3 h 45 min of it the pause) |
| S0003 (a document's marked examples are run by the check) | 26 | 253 | 436 | 139,692 | 7,589,688 | 815,724 | $10.23 | 2,711 s | 1,685 s | 79.5 min |
| S0006 (the examples start from a known instance) | 14 | 110 | 188 | 44,419 | 2,808,041 | 330,452 | $3.76 | 1,058 s | 588 s | 30.0 min |
| S0004 (the checks block the listed files and report on the others) | 14 | 127 | 214 | 64,816 | 3,497,068 | 369,561 | $4.63 | 1,348 s | 750 s | 33.8 min |
| S0005 (the agents write and review documents against the code) | 19 | 163 | 280 | 70,685 | 4,005,778 | 495,748 | $5.86 | 1,576 s | 956 s | 66.5 min |
| S0007 (each area names its guide page) | 6 | 32 | 50 | 10,686 | 491,675 | 120,015 | $1.05 | 259 s | 133 s | 8.9 min |
| A0001 (the first acceptance) | 1 | 54 | 94 | 43,101 | 3,946,291 | 133,278 | $2.72 | 639 s | 501 s | 10.6 min |
| S0008 (a runnable example in the documents keeps the suite green) | 14 | 101 | 170 | 42,559 | 2,312,913 | 280,125 | $3.18 | 856 s | 581 s | 27.5 min |
| S0010 (the name check reads log files and git addresses) | 10 | 65 | 102 | 24,305 | 1,230,421 | 199,022 | $2.11 | 588 s | 331 s | 16.9 min |
| S0009 (a configuration section without its settings table is a finding) | 10 | 64 | 106 | 25,685 | 1,339,937 | 212,975 | $2.29 | 629 s | 372 s | 17.6 min |
| S0012 (the example runner's tests use the roomy limit) | 7 | 40 | 60 | 15,274 | 698,321 | 131,338 | $1.25 | 345 s | 190 s | 10.4 min |
| S0011 (the guides say what shapes the checks read), docs route | 5 | 34 | 54 | 16,905 | 666,524 | 142,940 | $1.26 | 198 s | 187 s | 7.8 min |
| A0002 (the second acceptance) | 1 | 42 | 80 | 30,286 | 2,846,655 | 110,482 | $2.06 | 497 s | 346 s | 8.3 min |
| S0013 (the settings check reads a backticked default and a refusal with its variable) | 10 | 48 | 74 | 16,598 | 789,494 | 176,647 | $1.72 | 454 s | 210 s | 14.8 min |
| A0003 (the third acceptance) | 1 | 49 | 94 | 36,476 | 3,390,775 | 95,421 | $2.17 | 653 s | 483 s | 10.9 min |
| S0014 (a skipped block or a checkout example keeps the suite green) | 11 | 89 | 148 | 37,303 | 1,935,455 | 316,244 | $3.23 | 1,090 s | 668 s | 327.3 min (4 h 54 min of it the sleeping PC) |
| A0004 (the fourth acceptance) | 1 | 46 | 86 | 34,758 | 3,130,267 | 116,426 | $2.25 | 814 s | 431 s | 13.6 min |
| S0015 (listing a right document keeps the suite green) | 10 | 56 | 90 | 25,549 | 1,077,201 | 204,125 | $2.16 | 640 s | 334 s | 17.9 min |
| A0005 (the fifth acceptance) | 1 | 37 | 64 | 26,667 | 1,965,916 | 84,979 | $1.61 | 762 s | 320 s | 12.7 min |
| S0016 (a page already listed keeps the document tests green) | 10 | 57 | 90 | 24,172 | 1,083,866 | 196,675 | $2.08 | 851 s | 337 s | 21.6 min |
| S0017 (the document checks' tests run on documents they write) | 14 | 140 | 242 | 72,419 | 4,734,509 | 403,744 | $5.19 | 1,364 s | 887 s | 36.2 min |
| A0006 (the sixth acceptance) | 1 | 35 | 66 | 32,096 | 2,170,410 | 111,128 | $1.97 | 579 s | 351 s | 9.6 min |
| **F0053** | **213** | **1,843** | **3,116** | **938,990** | **56,649,475** | **5,807,170** | **$71.22** | **20,485 s (5.7 h)** | **11,899 s (3.3 h)** | **19.6 h** |

The night log gives the feature's total as $58.44 and 207 runs. As in F0052, that is the stories alone. The six acceptances add $12.77 and 6 runs, so the real total is $71.22, and the acceptances are 18 percent of it. The stories that the acceptances proposed (S0008 to S0016) and S0017 cost $24.47, so the acceptance loop as a whole is $37.24, or 52 percent of the feature. The seven planned stories cost $33.98.

### Per stage and role

| Stage (role) | Runs | Cost | Cost per run | Turns | Output | Cache read | Cache creation | Run time | Model time |
|---|---|---|---|---|---|---|---|---|---|
| review (reviewer) | 37 | $17.14 | $0.46 | 320 | 215,345 | 9,311,416 | 1,371,039 | 2,634 s | 2,539 s |
| tests (tester) | 42 | $16.45 | $0.39 | 425 | 234,490 | 12,265,264 | 1,163,203 | 3,497 s | 2,965 s |
| doing (coder) | 63 | $15.38 | $0.24 | 431 | 158,720 | 10,630,171 | 1,260,110 | 8,353 s | 2,158 s |
| acceptance (acceptance reviewer) | 6 | $12.77 | $2.13 | 263 | 203,384 | 17,450,314 | 651,714 | 3,945 s | 2,431 s |
| smoke-test (smoke tester) | 16 | $3.24 | $0.20 | 96 | 22,306 | 1,496,765 | 311,834 | 478 s | 370 s |
| docs (documenter) | 19 | $3.03 | $0.16 | 152 | 48,660 | 3,544,480 | 546,578 | 770 s | 683 s |
| intake (intake) | 26 | $2.01 | $0.08 | 127 | 40,500 | 1,337,973 | 373,849 | 626 s | 579 s |
| docs-review (reviewer) | 2 | $0.90 | $0.45 | 17 | 10,415 | 392,889 | 76,987 | 112 s | 109 s |
| docs-only (documenter) | 2 | $0.28 | $0.14 | 12 | 5,170 | 220,203 | 51,856 | 72 s | 66 s |

The coder's run time is four times its model time: 5,533 s of its 8,353 s was `make check`, which 45 of its 63 runs ran themselves.

### Where the wall time went

The feature ran from 02:07 to 21:41, 19.6 hours. The pause on the human's word (3 h 45 min, inside S0002) and the sleeping PC (4 h 54 min, inside S0014) leave about 10.9 hours of active time.

- Agent runs: 20,485 s (5.7 h, 52 percent of the active time). Model time is 11,899 s of it. About 6,260 s of the runs is `make check` run by the agents themselves: 5,533 s in 45 coder runs and 687 s in the six acceptances.
- The factory's gate between a run and the next stage: about 6,860 s (1.9 h, 17 percent): 4,433 s after `doing` (`make check` and the duplicates report), 2,177 s after `docs` (`make check`, `make secrets` and `make documents`) and 251 s after `docs-only`.
- The human's answers: 3,553 s for 20 questions (median 116 s) and 1,822 s for the two round caps (S0003 606 s, S0005 1,216 s), together 1.5 h or 14 percent.
- Between work items (the approvals, the merges, the VM moves): 5,005 s (1.4 h, 13 percent), about 250 s per work item.

`make check` ran for about 12,700 s in all (in the runs and in the gates), about 3.5 hours or 32 percent of the active time.

## 2. Findings, ordered by saving

### Finding 1: one cause, tests that run on copies of the real documents, made five of the six acceptances and five repair stories

- **What.** Four acceptances found a right document that turned `make check` red, each time through a different test that ran on a copy of the real documents or read the real checked list. Each acceptance proposed one repair for the case it found. Only the human's question at S0016 led to S0017, which removed the cause.

| Acceptance | Cost, elapsed | What it found | Its stories |
|---|---|---|---|
| A0001 (the first acceptance) | $2.72, 10.6 min | one `console` block in a real document fails five rows, because the `documents` copy is no git repository; and four smaller gaps | S0008 $3.18 (the same cause), S0010 $2.11, S0009 $2.29, S0012 $1.25, S0011 $1.26 |
| A0002 (the second acceptance) | $2.06, 8.3 min | a backticked default and a refusal with its variable are false findings | S0013 $1.72 |
| A0003 (the third acceptance) | $2.17, 10.9 min | a `console vm` block and a `checkout` example fail nine rows (the same cause) | S0014 $3.23 |
| A0004 (the fourth acceptance) | $2.25, 13.6 min | listing a right page fails nine rows of four tests that read the real checked list (the same cause) | S0015 $2.16 |
| A0005 (the fifth acceptance) | $1.61, 12.7 min | S0015's own new test lists an already listed page twice (the same cause) | S0016 $2.08 |
| (the human) | - | the cause itself, feature decision 10 | S0017 $5.19 |
| A0006 (the sixth acceptance) | $1.97, 9.6 min | accepted | none |

- **Evidence.** The cause was visible early, three times. A0001's own report names it: the shared fixture "copies the real documents into a folder that is no git repository". The reviewer of S0010 (the name check reads log files and git addresses), run `033da3ee` in round 0, named the coupling for one test: it runs the whole command "on the real repository once for each of its three rows ... its cost grows with every example the documents gain". And S0003's and S0008's documenters each stalled on it at the gate (S0003 journal 56, S0008 journal 12). The feature smoke tests then grew one step per acceptance: A0003 added a `vm` block and a `checkout` example, A0004 listed `install.md`, A0005 listed three pages, and A0006 listed every page with no finding and ran the document tests. A0006 was the first green one; the same script at A0001 would have shown all four cases at once. The class cost $15.84 in stories (S0008, S0014, S0015, S0016, S0017) and $6.03 in the three acceptances A0003 to A0005, about $21.9 in all. From A0003's merge (14:04) to S0017's start (20:52) took about 1 h 50 min of active time.
- **Saving.** If A0003 had named the class, S0014, S0015, S0016, A0004 and A0005 would not have run: $11.33 and about 1 h 50 min. If A0001 had, A0003 and most of S0008 would also have gone: about $15 and 2.5 hours for this feature. Every feature whose stories add a check over repository files can fall into the same loop.
- **Change.**
  1. A rule in `agents/agents/acceptance-reviewer.md`, check 2 (the feature smoke test): "When the next feature's stories will change files that this feature's code reads, the feature smoke test makes all their kinds of change at once in a clone (every page they list, one block or example of each kind, every table shape the style page names) and runs `make test` there, not only the feature's own command."
  2. A rule in `acceptance-reviewer.md`, under Proposals: "When an earlier test fails on a right input, find its class before you propose a repair: grep `tests/` for every test that reads the repository's real files (the fixture, `ROOT`, `Path(__file__).parents`, `git ls-files`). Propose one story that removes the dependence, or name each test of the class in one story; never one story per test."
  3. A project rule in `CLAUDE.md`, *Tests* (feature decision 10 made general): "A test of a check over repository files runs on files the test writes, never on a copy of the real files or the real lists; the real files are checked by the project command alone." The new guard `tests/guards/test_document_tests_write_their_documents.py` keeps it for the document check; the rule carries it to the next check.

### Finding 2 (confirms F0052 finding 3, with larger numbers): 42 of 62 coder runs changed nothing, and 25 of them ran `make check` again

- **What.** Every review finding that is only about tests goes review, then `doing` (the coder relays it), then `tests`, then `doing` again (the coder runs `make check` on the tester's tree), then review. Six stories changed nothing under `src/` at all, yet each had two to five coder runs.
- **Evidence.** I matched each coder entry to its run. 42 of the 62 coder runs with a result say they changed nothing ("I changed no code", "I wrote no code", "I built nothing", or a test change written out for the tester). They cost $7.07 and took 4,020 s. 17 of them were pure relays without `make check` ($2.94). 25 ran `make check` themselves for 2,952 s in all ($4.13), and the gate then ran it again on the same tree. The six test-only stories, S0008 (a runnable example in the documents keeps the suite green), S0012 (the example runner's tests use the roomy limit), S0014, S0015, S0016 and S0017, had 18 coder runs for $3.08 and 1,966 s. S0016's coder `181aae48` wrote: "I wrote no code. Everything this story changes is test code".
- **Saving.** About $5 to $7 and about 1 hour per feature of this size (the gate's `make check` moves to the tests stage and stays).
- **Change.** As F0052 proposed, now with this evidence for the human's decision: in `factory/pipeline.yml`, `tests: next: [doing, review]` and `review: next: [docs, doing, tests]`, with `check` as a check of the `tests` stage on its forward move to `review`. In `agents/agents/tester.md`, step 5: "End with `review` when the Interface changes nothing in the coder's write paths, or when you made test changes for review findings and the coder's last entry says the code is in place." In `agents/agents/reviewer.md`: "When every finding is in `tests/`, end with `tests`." In `coder.md`, R11: "When you changed no file since the journal's last green `check`, do not run `make check`; the factory runs it."

### Finding 3 (new): copied test helpers and constants sent five stories into a second review round on their own

- **What.** The reviewer counts a copied helper or constant in a test file as a finding at round 0 (`reviewer.md`, the paragraph before the added-criterion rule). The tester has no step that searches for one before it ends, and `make duplicates` reads only `src/factory`. So copies reached the review in 11 of the 16 code-route stories, and in five of them they were the only reason for round 1.
- **Evidence.** Round-0 reviews that named a copy: S0001 (`REPLACED_SECTION` written again), S0003 (`FENCE` in three modules, `_line_of`), S0004 (`ROOT`), S0006 (`INSTANCE_FIXTURE`, then `SETTINGS_FILE`), S0009 (`GuideTable` built by hand), S0014 (`copy_of` copies `clone`, `_append_block`), S0015 (three path constants), S0016 (`_list_newly` copies `_append_to_list`), S0017 (`minimal_documents_support.py` copies builders of `document_texts.py`). In S0009, S0014, S0015, S0016 and S0017 round 1 had no other finding of weight; those rounds cost $0.77, $1.06, $0.90, $0.73 and $1.52, $4.98 in 20 runs, plus five gate runs of `make check` (about 10 minutes). S0015's review `3716b833` opened with "`CHECKED_LIST = "docs/checked-documents.txt"` copies `CHECKED_DOCUMENTS`".
- **Saving.** About $1 and 5 minutes per affected story, $4 to $5 per feature of this size.
- **Change.**
  1. A step in `agents/agents/tester.md`, before step 5: "For every module-level constant, helper and fixture you defined, grep `src/factory` and `tests/support/` for the same value or body; import or move the existing one under the standing leave, and say so in your entry."
  2. A code change: let `make duplicates` also read the test files changed against `origin/main`, and add it as a report of the `tests` stage, so the tester's entry and the reviewer see the copies.
  3. Together with finding 2, a round that is left needs two runs (tester, reviewer) instead of four.

### Finding 4 (new): the leaves for earlier tests cost seven questions and about 15 runs, and none after they were written into the Interface

- **What.** Seven of the 20 questions asked for the human's leave to change an earlier test. All seven came in S0001 to S0008. From S0009 on, the operator copied the wide leave sentence of feature decision 6 into each story's Interface, and no story asked again.
- **Evidence.** The seven: S0001 coder `d0cdf849` (entry 10), S0003 tester `b81caa3c` and `9f0fd318` (entries 8 and 11), S0003 coder `bc040921` (entry 16), S0004 coder `625cd5fb` (entry 10), S0005 coder `657966f1` (entry 10), and S0008 tester `1936cc9a` (entry 18). A coder's leave question costs three extra runs: a relay to the tester, the tester's change, and one more coder run with `make check` (S0001 $0.53, S0003 $0.72, S0004 $0.72, S0005 $0.52); the tester's questions cost $0.51 (S0003) and $0.20 (S0008). Together about $3.2, 15 runs, 879 s of waiting and about six more gate runs (about 12 minutes). S0008's tester asked although decision 6 covered it, because it may not read `feature.md` (`tester.md`, step 1); it wrote: "I can't tell whether the existing leave covers" the change. After the copy, S0009, S0012, S0014, S0015, S0016 and S0017 changed earlier tests under the leave in their Interface with no question. The leaves caused neither round cap: by `src/factory/work/domain/decisions.py`, only a send back from a stage with a `round_cap` (review, docs, smoke-test) counts a round, and `doing → tests` has none. The night log's note at 10:56Z, that an answer sending a story back to tests counts a round, does not hold; S0005's cap came from three review rounds on the wording of the agent files.
- **Saving.** About $3 and 25 minutes per feature whose stories touch earlier tests.
- **Change.**
  1. A rule in `factory/story-form.md`, *Interface*: "Before a story starts, the Interface names every earlier test that reads a file the story changes (found by a grep of `tests/`), and quotes the leave for it word for word; a reference to `feature.md` alone does not reach the agents."
  2. The same rule for the proposals in `agents/agents/acceptance-reviewer.md`, which already write such leaves into `feature.md`.
  3. A code change, as candidate 54 asks: the factory puts the feature's *Decisions taken for the human* that name the story into the prompt of every stage.

### Finding 5 (new, with F0052 candidate 5): reviewers added 13 criteria in 8 reviews, and in S0003 they came in three waves

- **What.** When the diff builds a behaviour no criterion names, the reviewer adds a criterion (`reviewer.md`). In S0003 the coder's fixes for real faults built new error paths, and each review added criteria for them, so the story reached the round cap with only tests missing.
- **Evidence.** Criteria added: S0001 one, S0002 one, S0003 two at round 0, three at round 2 and one at round 3, S0004 two, S0006 two, S0013 one. In S0003 (a document's marked examples are run by the check) the round-2 review `584feca9` had only added criteria; it hit the cap, the human waited 606 s, the review ran again (`a57e15a5`, $0.72) and the round after it cost $2.02 in all. S0013's (the settings check reads a backticked default and a refusal with its variable) only round-1 finding was one added criterion ($0.59). The log says of S0003 that round 3 "asked only for two tests of built behaviour".
- **Saving.** About $2.5 and 15 minutes per feature with one large story.
- **Change.**
  1. In `agents/agents/coder.md`: "When a fix builds a behaviour no criterion names (an error path, a default, a guard), name it in your entry under `Built beyond the criteria:`, so the reviewer adds all its criteria in one review."
  2. In `agents/agents/reviewer.md`, after the added-criterion paragraph: "From round 1 on, add a criterion only for code changed since the last review; read the whole diff for missing criteria at round 0."

### Finding 6 (new): nine of 17 stories stopped at the intake, and six answers began with "Yes" to the intake's own proposal

- **What.** The intake asked in S0001, S0002, S0003, S0004, S0005, S0006, S0012, S0014 and S0017: 52 numbered points. Six of the seven planned stories stopped (only S0007 did not), but only three of the ten proposed ones.
- **Evidence.** The planned stories lacked what the story form already asks for: "the classes and functions ... with their signatures in a code block". S0001's first point was "The Interface does not define `Reference`"; S0003 and S0006 asked where a new adapter lives and what it returns. The acceptance's stories asked for criteria of behaviours their Interface named (S0012: criteria for the imported constants; S0014: one criterion that every test gets its own copy). The answers of S0001, S0004, S0005, S0012, S0014 and S0017 began with "Yes" to the intake's proposals. The questions cost little ($0.60 in second intake runs), but the waits were 2,273 s, 38 minutes, of the 3,553 s all questions waited.
- **Saving.** About 35 minutes of wall time per feature, and the story starts at once.
- **Change.**
  1. A pipeline step for the human: run the intake over every story of a feature's backlog when the feature starts (for example `factory-check-story --intake`), so that all questions come in one sitting before the night.
  2. In `agents/agents/acceptance-reviewer.md`, Proposals: "Check each proposed story by the intake's steps 2 and 3 before you write it: every behaviour of its Interface has a criterion with both sides, and every new class has its signature and its module."
  3. F0052 finding 4.1 again: the intake may add a criterion for a behaviour the Interface states, and say so in its entry, instead of asking.

### Finding 7 (new): an answer at the round cap makes the reviewer run again before the work goes on

- **What.** After the human's answer at a round cap, the work item stays at `review` (`src/factory/work/domain/answers.py` only resets `round`), so the reviewer runs once more and repeats its findings before the coder or tester acts.
- **Evidence.** S0003 review `a57e15a5` ($0.72, 13 turns, 130 KB of tool output) and S0005 review `f825670d` ($0.30) ran right after the answers to the caps; both ended with `doing` and the findings the previous review had already listed.
- **Saving.** About $0.5 and 2 minutes per round cap.
- **Change.** A code change: an answer at a round cap moves the work item to the stage of the decision that hit the cap (`doing` here), with the round reset, as if the decision had been allowed.

### Finding 8 (new): the tester skips the type check, also when no module under `src/` changes

- **What.** `tester.md`, step 3, says to skip the type check because it "cannot pass while the modules under test do not exist". In a test-only story the modules exist, and the type errors reached the coder, who may not fix tests.
- **Evidence.** S0017 (the document checks' tests run on documents they write): the coder `54516e30` ran `make check`, found that the tests failed `make types`, and asked (entry 10). The question cost the coder run ($0.25, 150 s), a relay ($0.09), the tester's fix ($0.23), one more coder run with `make check` ($0.21, 247 s), 116 s of waiting and two gate runs: about $0.80 and 12 minutes. The `tests` stage's checks are `[lint]` in `factory/pipeline.yml`.
- **Saving.** About $0.8 and 12 minutes for each test-only story that has a type error; six of the 16 code-route stories here were test-only.
- **Change.** In `agents/agents/tester.md`, step 3: "When the Interface says no module under `src/` changes, run `make types` as well; it must be green." Or, in `factory/pipeline.yml`, `tests: checks: [lint, types]` once a `types` project command exists, which needs the human.

## 3. Carried over

Carried over: this feature confirms F0052 finding 1 (163 of 213 runs wrote their first message, about 10,140 tokens, into the cache again: 1.95 million tokens, about $11 at that report's rate, the largest single saving still open), finding 2 (the acceptances again read the previous report and every new story in full, 44 percent of their 883 KB of tool output, and each ran `make check` on a passed tree, 687 s in all), finding 3 (finding 2 above), finding 4 (finding 6 above; the intake still does not grep the tests that read what a story changes, which finding 4 above measures), finding 7 (work-item text is 48 percent of the 8.0 MB of tool output: 93 percent for the intake, 85 percent for the smoke tester, 56 percent for the coder) and finding 8 (16 smoke-test runs on Opus, $3.24, every one of them ending with `approval` and no finding), and candidates 5 (finding 5 above), 28 (20 sandbox denials, 8 of them `rm -rf` of an agent's own `mktemp` folder and 4 in S0014's smoke test, which cost $0.34 against a median of $0.21), 47, 54 (finding 4 above) and 64; it neither confirms nor refutes F0052 findings 5 and 6, since only S0011 (the guides say what shapes the checks read) took the docs route ($1.26, one round, no sentence-length finding), and finding 9 did not recur (the one run without a cost record, S0002's coder `42cb9279`, was killed by the pause on purpose); and it refutes the night log's note at 10:56Z that an answer sending a story back to tests counts a round (finding 4 above).
