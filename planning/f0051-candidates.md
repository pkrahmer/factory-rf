# F0051 candidates: what F0050's run showed

Collected on 2026-11-04 from the eval of every F0050 story (`planning/f0050-eval.md`), the analysis of GitHub's outage (`planning/outage-2026-11-04.md`) and the human's questions during the run. Each item says how often it was seen, what it cost, and the smallest fix. Nothing here is decided; it is the input for planning F0051. Ordered by the saving per story.

## Routing and repeated checks

1. **A coder run that only relays a test change.** Seen in every story but S0001's first rounds (S0002, S0008, S0003, S0004, S0005, S0006, S0007). The review stage can go only to `docs` or `doing` (`factory/pipeline.yml`), and the tester's change after a review goes back through `doing`; the coder then changes nothing. About $0.20 to $1.10 and 4 to 9 minutes per story. Fix: `review` may also go to `tests` when every finding is a test finding; `tests` may go to `review` when its change leaves `check` green, with `check` as its gate. (The human asked why the reviewer did not send S0007 straight to the tester.)
2. **`make check` twice on the same files.** The coder runs it inside its run, and the factory runs it again as the gate, because an agent's own result is never reused (F0023). After a relay the tree is new to the full check, so both run, about 100 s each. Fix, smallest first: a coder that changed no file ends without its own `make check`; or item 1 removes the relay. (The human asked why `make check` runs when no file changed.)

## Questions that the story or the intake could have answered

3. **Seams not named in the story.** S0002 (two tester questions), S0008, S0004, S0005 asked for them; about $0.60 and up to 19 minutes of human wait each time. When the human named every seam at the intake (S0003, S0006), the tester and the coder asked nothing. Fix: the story form and the intake require the Interface to name modules, functions and signatures for every new behaviour.
4. **Earlier tests in the way of a new signature, found one by one.** S0004 (three coder questions: six doubles, then a seventh, then a pinned docstring), S0005 (six stand-ins and a pin), S0002. About $0.70 to $1.00 and 10 to 20 minutes each. Up-front leaves (S0006) removed them. Fix: the intake greps for overrides, stand-ins, replacements and pinned texts of what the story changes and lists them; a standing leave in `CLAUDE.md` for a test change that only follows a new signature (the signature and passing it on, nothing else); and the coder runs `make check` once and puts every red test into one question.
5. **Behaviour sentences without a criterion.** S0003's two extra rounds ($3.03) and S0008's second round came from an Interface sentence with no criterion, often one the reviewer itself added. Fix: the intake checks that every behaviour sentence of the Interface has a criterion; a reviewer that adds an Interface sentence adds its criterion too.
6. **Open points noted instead of asked.** S0003: a point the tester called "left open by the Interface" and the coder listed as "noticed" became a later round. Fix: an observable open point ends the stage with a question, not a note.

## Rules the agents already have but broke

7. **The tester skips `make types`.** `claude/agents/tester.md` says to skip the type check; untypable tests reached the coder in S0001, S0004 and S0008. Fix: the tester runs `make types` and tolerates only missing-module errors.
8. **Copied test helpers and the sides of one rule as separate tests.** S0005 (four of eight findings, $2.08 round), S0006 (`_records`), S0007 (finding 2), S0004 (helper copies). Fix: the tester checks its new tests against those two rules before it ends; or a duplicate check in the tests stage.
9. **Rare-input rounds.** S0006: three review rounds, each one more rare input (mixed offsets, deep nesting, U+2028), $3.81, half the story, and a round cap. Fix: the reviewer puts a rare input that breaks no criterion in normal runs under `Notes:`; the tester writes the usual rows at once for any parser (wrong-shape input, empty input, U+2028/2029/0085).
10. **The coder's criterion edits are lost.** `coder.md` R5 tells the coder to edit criteria, but its write paths exclude the work item; S0002 lost an edit and a round ($0.53). Fix: the coder asks, and the reviewer edits under leave; change R5.

## Time and tokens

11. **Hung test runs.** S0004: 1,431 s, 53% of its run time, from a test double that broke the factory's loop (`iteration failed` and the loop went on). Fix: a pytest timeout (`pytest-timeout` in `pyproject.toml`), and `timeout 120 pytest ...` with "never poll" in the agent files.
12. **The work item in full, several times per run.** 45% to 50% of all tool output in every story; about $0.30 to $1.00 per story. Fix: the factory puts the Description-to-Smoke-test slice and the last few journal entries into the prompt; the agents read the rest only when needed.
13. **The reviewer reads the whole diff in every round.** About $0.10 per round. Fix: from round 1 on, the diff since the last review plus the stat.
14. **A flaky process-runner test.** `tests/adapters/test_process_streaming.py::test_callback_saying_stop_on_standard_output_kills_the_group_at_once[before-a-sleep]`, `OSError: [Errno 22]`, stalled S0003 once ($0.16, 220 s). Also in `planning/v1.2-candidates.md`.

## Stability (from `planning/outage-2026-11-04.md`)

15. **A crash is charged for a stage in which no agent ran**, when the hosting service fails after the claim. Pinned by S0008's strict `xfail` in `tests/application/test_hosting_failure_after_claim.py`. Fix: read or create the pull request before the claim, or release the claim on that error.
16. **A capped event never tries again** (the hand-over during the outage; also the merged and the crash events). The human kept the cap of three tries (2026-11-04); a restart or a new commit wakes it. Revisit only if outages longer than the S0008 retries recur.
17. **An answer posted before the question it answers is lost.** S0005: the human's answer came a minute before the tester's repeated question was posted, so it did not count (about 12 minutes). Fix: the factory reads the pull request's comments once more right before it posts a question, and takes a comment newer than the question's journal entry as the answer.
18. **A paused machine.** The PC slept and the Multipass VM was paused for 1.5 hours; the VM's clock then lagged and was stepped by timesyncd. Nothing broke (time limits use a monotonic clock), but the records' wall times around the step look odd. Worth a line in the operator guide; no code.

## Smaller

19. The `job` container profile's cgroup may not be the factory user's slice, so `machine`'s memory and CPU values may be empty or another slice's there (noted in S0002's docs).
20. The memory peak is a boot-wide value and cannot say which run needed the memory; a per-run peak would need sampling (F0050 decision 4).
21. Apt's `update-alternatives` warnings are left out of the warning count; other harmless warnings may need the same treatment once seen.
22. `vm/setup.sh` and `vm/job-start.sh`: none known after S0007.

## Added after a check against every eval finding (2026-11-04)

23. **A decision posted while a stage runs waits for the next stage start.** S0007 passed review and reached approval before the human's decision was read (it entered the journal only at approval), so it had to be sent back by closing the pull request. Fix: the factory copies new comments into the journal before each stage it starts *and* tells a running review or docs stage; or the human's decision gives leave to the stage that sees it first, and approval refuses while an unread human comment stands.
24. **The story's own smoke test was wrong** (S0001: one `ARG` line where Docker needs one per stage; S0002: a doubled `-q`). Found only after review and docs. Fix: the coder runs the `## Smoke test` commands once before it ends with `review`.
25. **The reviewer, not the tester, found missing tests** (S0002: the wiring in `build_boundaries`, adapter tests, begin-then-complete; S0005 too). About $1.50 a round. Fix: a tester rule to write, for every new seam, one test that fails when its wiring is removed.
26. **A run that crashes leaves no cost record** (S0001's documenter, S0002's two testers: about $1 unrecorded). By design (F0005-S0008: no record without a commit), and S0008's retries make it rarer. Keep, or record the cost of a crashed run in the stop records instead.
27. **Long waits inside a run for full test suites** (S0002's first coder: 706 s; S0003: a `make check` for an approach it then threw away). Fix: the agents run the tests of the files they touched first and `make check` once at the end.
28. **Denied compound commands** (S0008: `cd $(mktemp -d) && ...` refused twice, one retry each). Fix: one line in the agent files on the allowed form.
29. **A restart after a cap answer is a full run** (S0006: the reviewer re-read everything to apply one decided fix). Fix: the cap answer's run reads only the diff since the last review.
30. **The first tester run is the most expensive single run** (S0001 $1.95, S0006: 25 turns). It is the price of good tests and seams; no fix, but it is where a token budget would bite first.

## Added from the feature's sum (S0007's eval, 2026-11-04)

31. **A human's close at approval counts toward `round_cap`.** S0007's send-back by closing #545 was its second send-back, so the next reviewer finding hit the cap and cost a stop. Fix: a human's send-back does not count as a round, or it resets the count as a cap answer does.
32. **A send-back or cap answer cannot name the stage to go to.** S0007's narrow round had to go through `doing` again. Fix: the human's answer may name the next stage (for example `tests` or `docs`).
33. **A behaviour the coder adds on its own is found rounds later.** S0007: the coder wrote the link refusal in its first run; the reviewer found it untested in round 2 ($1.22, 603 s). Fix: the coder names every behaviour it added beyond the Interface in its entry, and the reviewer checks those first.
34. **`make duplicates` does not see shell**, and the coder runs the full Python suite (88 s) for a diff with no Python, where the relevant tests take 6 s. Fix: the coder's check follows what the diff touches; a duplicates check for `vm/*.sh`.
35. **What worked: a leave that lists the reviewer's exact edits.** S0007: three edits made exactly, against about 24 in S0005. Keep it as the playbook's way to change a running story.

## For the morning of 2026-11-05: compare the CPU wait

36. **The CPU limit as a test of `cpu_wait_seconds`.** From 21:3x UTC on 2026-11-04 the factory user's slice on factory-vm is limited to 6 of 12 cores (`CPUQuota=600%`, runtime only), because the PC's fan was loud during `make check`. Baseline before the limit, over the 111 F0050 runs that carry `machine`: 22,612 s of CPU, 84.8 s of CPU wait (0.38 % of the CPU time), 1.72 cores on average per run, the largest wait 4.8 s (S0006's doing at 18:55). In the morning: the same numbers for the runs after the limit, the `make check` times before and after, and whether the measure shows the throttle clearly enough to judge a machine's size. Note: a cgroup quota throttles rather than queues, so the throttle may show more in `cpu.stat`'s `throttled_usec` than in `cpu.pressure`; if the wait stays near zero, that field is the candidate to add.

37. **Intake questions that the human only confirms.** S0009 (and S0003, S0006, S0008): every intake question was answered "as you propose", at 235 s of human wait and about $0.06 each time. Fix to decide: the intake adds a missing criterion row for a rule the Interface already states (the other side of a two-sided rule, an exact limit) by itself and names it in its entry, and asks only where a real choice is open.

44. **A hosting outage after the claim adds two commits per tick to the branch.** S0010 releases the claim on `HostingServiceError`; the release moves the branch head, so the error count starts again at 1 every tick and never reaches the cap (the human's answer (A), 2026-11-04). A long outage that leaves git working therefore adds a claim and a release commit per tick and never stops. Fix to decide: key a run event's count on the commit before the claim, or wait longer between such ticks.

## The repository is easier to navigate (the human, 2026-11-04)

38. **`claude/` becomes `agents/`.** It holds the factory's agent files and `settings.json` in Claude Code's format, which the opencode runtime translates per run (decision of 2026-10-19, F0020-S0004); the name says one runtime. Touches `vm/Dockerfile`, the wiring, the coder's write paths in `factory/pipeline.yml`, the docs and tests.
39. **Finished features move out of `factory/features/`.** 33 features and 702 files, one open. An archive folder, or a tag and removal; first check how the factory finds work items and the next feature number.
40. **`planning/overnight` (160 files) and `planning/cloud-sandbox` (63) go to a tag**, as the planning history did on 2026-10-19 (`planning-history-2026-10-19`).
41. **The root of `tests/` is sorted**: 200 modules, 72 of them `*_support.py`; the helpers move to a `tests/support/` package and the structural guards to `tests/guards/`. Mechanical, but many imports; `CLAUDE.md`'s test rules change with it.
42. **`docs/operator-guide.md` (2,603 lines) becomes a folder**, one file per topic, like `docs/project-guide/`; the document check and the docs criteria name the new files.
43. **The run log starts again per run or per week**; `docs/runs/2026-10-12-overnight/night-log.md` has 1,574 lines since 2026-10-12.
