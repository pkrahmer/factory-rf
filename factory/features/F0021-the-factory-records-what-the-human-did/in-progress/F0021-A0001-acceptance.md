---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 241
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T00:13:59.795137Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T00:51:50.397853Z'
  stage: acceptance
  run: 346616f95ebf454d8317809c11bbf2a5
stories: [F0021-S0001, F0021-S0002, F0021-S0003, F0021-S0004, F0021-S0005, F0021-S0006]
outcome: null
---

# Acceptance of The factory records what the human did

## Recommendation

Accepted with stories. Every scope item has its story and its code. The feature smoke test is green end to end: it reads this feature's own archived stories and sidecars, validates them against the generated contract, publishes stop records to a real bare remote and regenerates the schemas byte for byte. `make check` is green. What the parts left behind is all repair: five stale or wrong passages in the documents (one is a wrong cell in the table of the factory's own questions, a table this feature extended), the preflight follow-up that decision 1 deferred to "a later story", and two untested sides of the contract command.

## 1 Scope

None. Each scope bullet of `feature.md` maps to an archived story and to code:

- The cause on the record (S0001): `JournalRecord.blocked` and `.reason` with their kind rule are in `src/factory/domain/journal.py`. Every writer the scope means passes the field: `stage.py:310,313` (agent question, rule 1 and rule 4), `stalls.py:126`, `handlers/questions.py:61` (`attempts_cap`), `recovery.py:226` (`crash_cap`) and `handlers/closed.py:116` (`send_back`). A grep for `kind="question"` and `kind="stall"` under `src/factory` finds no other writer. `crash` and `expiry` carry no reason (decision 4).
- The human's waits and their line (S0002): `src/factory/domain/human_waits.py`. `cost_table_post(table, human)` is used by `HandOverHandler` and `AcceptanceHandOver`. The facts line is `AcceptanceFacts.human_line`, and this run's prompt carries it.
- The stops on GitHub (S0003): `StopService` appends `raised` and `cleared`, `StopPublisher.publish` pushes to `factory/stops.jsonl`, `Tick.run` publishes right after the restore, and `build_boundaries` wires `records/stops.jsonl`.
- The run record's refusals (S0004): `PermissionDenial.path`, and `CostRecord.denials` and `denied_paths`, left out of the line when `None`.
- The texts (S0005): `claude/agents/reviewer.md` (`Notes:` from round 1 on, `criterion <n> added`), `coder.md` step 2, `tester.md` step 0, the acceptance reviewer's cost section, and `docs/operator-guide.md` "Never edit a running work item on main".
- The contract (S0006): `factory.domain.contract` and `factory.entry.contract`, plus five schemas under `src/factory/contract/` at `x-records-contract: "1.0"`. A test compares them with the committed files, and the operator guide's "The records contract" covers them. No stage, role or reader is named.

No story goes outside the scope, and the out-of-scope items stay out. `factory/stops.jsonl` does not exist on `origin/main` yet. No stop of the repository or the machine has been raised since S0003's image rebuild, so the publish has not been seen in production; the smoke test below covers it.

## 2 Feature smoke test

The walk-through of the feature's purpose: a reader outside the factory reads the records alone. The script below does five things:

- reads the six archived stories and their sidecars through the real reader;
- validates every front matter and every cost line against the committed schemas (with `jsonschema`, which is already in the virtual environment as another tool's dependency; nothing is declared);
- computes the waits and the facts line;
- raises and clears a stop through the boundaries `build_boundaries` wires, publishes it to a temporary bare remote, and validates what `main` then holds;
- regenerates the contract into a temporary folder.

Command, from the root of the checkout: `uv run python -I "$TMPDIR/smoke/feature_smoke.py"`. The script:

```python
import json, os, subprocess, sys, tempfile
from datetime import UTC, datetime
from pathlib import Path
import frontmatter, jsonschema
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.application.stops import StopPublisher, StopService
from factory.domain.bills import bills_by_stage, cost_table
from factory.domain.human_waits import human_line, human_waits
from factory.domain.paths import STOP_RECORDS_FILE
from factory.domain.post_texts import cost_table_post
from factory.domain.settings import InstanceSettings
from factory.domain.stops import RepositoryStop, parse_stop_records
from factory.entry.wiring import build_boundaries

root = Path.cwd()
contract = root / "src/factory/contract"
schema = {p.name.removesuffix(".schema.json"): json.loads(p.read_text()) for p in contract.glob("*.schema.json")}
feature = next((root / "factory/features").glob("F0021-*"))
# 1: every archived story's front matter and sidecar against the contract; waits per story and summed
#    (the per-story loop prints one line each; then the acceptance report's front matter
#    against acceptance-state, and S0004's hand-over post's last line)
# 2: InstanceSettings(repository_url=..., instance="smoke", checkout=<clone of a bare remote>,
#    state_directory=<tmp>) -> build_boundaries(..., hosting=FakeHostingService(), confine_executable=None);
#    raise_stop(fetch_failed) twice, publish, clear_stop, publish, publish; then git show main:factory/stops.jsonl
#    and validate each line against stop-record
# 3: python -m factory.entry.contract <tmp>; compare every file with src/factory/contract
```

Output:

```
1. the archived stories: causes on the records, the human's waits, the contract
   F0021-S0001: front matter valid; 0 waits; 0 questions answered, 0.0 h waited; 15 cost lines valid, 0/15 completed with denials (sum 0)
   F0021-S0002: front matter valid; 1 waits; 1 questions answered (question 1), 0.0 h waited; 11 cost lines valid, 0/11 completed with denials (sum 0)
   F0021-S0003: front matter valid; 3 waits; 3 questions answered (question 3), 0.1 h waited; 13 cost lines valid, 0/13 completed with denials (sum 0)
   F0021-S0004: front matter valid; 3 waits; 3 questions answered (question 3), 0.1 h waited; 15 cost lines valid, 0/15 completed with denials (sum 0)
   F0021-S0005: front matter valid; 0 waits; 0 questions answered, 0.0 h waited; 6 cost lines valid, 6/6 completed with denials (sum 0)
   F0021-S0006: front matter valid; 0 waits; 0 questions answered, 0.0 h waited; 6 cost lines valid, 6/6 completed with denials (sum 0)
   causes seen: {'blocked': ['question'], 'reason': []}
   facts line over the feature: 7 questions answered (question 7), 0.2 h waited
   the acceptance report's front matter is valid against acceptance-state
   the hand-over's post for S0004 ends with: Human: 3 questions answered (question 3), 0.1 h waited
2. the stops reach main as records
2026-10-19T00:45:52Z stop repository fetch_failed: git: fatal https://x
2026-10-19T00:45:52Z stop repository fetch_failed: again
   published: ['raised fetch_failed']
2026-10-19T00:45:52Z stop cleared fetch_failed
   published: ['cleared fetch_failed']
   published again: []
   main's factory/stops.jsonl lines valid against stop-record: 2
   detail published: False
   subjects on main: ['stops', 'recorded', 'stops', 'recorded', 'seed']
   records: [('raised', 'smoke'), ('cleared', 'smoke')]
3. the contract regenerates to the committed files
   contract: 5 schemas written
   identical to src/factory/contract: True ['acceptance-state.schema.json', 'cost-record.schema.json', 'pipeline-definition.schema.json', 'stop-record.schema.json', 'work-item-state.schema.json']
   versions: ['1.0']
```

Green. The facts line computed from the records equals this run's prompt line. A stop raised twice gives one `raised` record. The detail (which held a URL) does not reach `main`, a second publish pushes nothing, and both schemas validate real records. The records also show where the data begins. S0001's own questions predate its image rebuild and carry no `blocked`, so its round-cap answer (journal entry 27) is not counted (decision 6). Denials appear from S0005 on, the first story run after S0004's rebuild.

## 3 Mutation score

`make check` was green before the runs (`check: green`, `test: green (38.4 s)`, coverage 99.06 %). `make mutants` (feature F0021, 28 modules) was run three times in the foreground:

1. The first run spent its whole 540 s in "Running clean tests" and ended with `mutants: stopped after 540 s; the results below are partial, run it again to go on`. mutmut also warned that 23 non-Python files had changed since the last full run, so it kept its cached results.
2. The second run reached `2806/13226  🎉 2658 🫥 0  ⏰ 2  🤔 0  🙁 146  🔇 0  🧙 0` and stopped at 540 s.
3. The third run stayed at `2806/13226  🎉 2657 🫥 0  ⏰ 2  🤔 0  🙁 147  🔇 0  🧙 0`, with one mutant flipping from killed to survived, and stopped at 540 s.

Score over the checked mutants of the feature's modules: **2657 killed, 2 timeouts, 147 survived, of 2806 checked**. Another 2947 are still `not checked`. Two modules were not reached at all (`domain.journal` 251, `domain.paths` 24), and most of `application.stage` (581), `claude_runtime` (480) and `acceptance_reading` (281) is unchecked. The score is partial, as in F0019's acceptances.

The survivors, grouped (`uv run mutmut show` read for each group):

- **The feature's own new code, survivors worth a criterion:**
  - `factory.entry.contract.main`: `sys.argv[1:]` → `sys.argv[2:]`, and the `argv is None` branch removed. The tests always pass `argv`, so the command as `python -m` runs it (arguments from `sys.argv`) is not pinned.
  - `factory.entry.contract.write_contract`: `mkdir(parents=True)` → `parents=False`. No test writes into a folder whose parent is missing. Proposed as S0009.
- **The feature's own code, equivalent or not observable:**
  - `human_waits._answered_at`: `>` → `>=`. The question record itself is never spoken by `human`, so this is equivalent.
  - `contract_schema`: `indent=2` → `indent=3` or none. The byte-for-byte test is deselected in mutmut runs by human change 1, and a test that compares parsed JSON cannot see indentation. Equivalent in mutmut's copy.
  - `AcceptanceService._waits`: the `document.state is None` branch. `FrontmatterWorkItemReader.parse` never returns a document without a state, so the guard is for the type checker only.
  - `stops._require_scope_of_reason`, `cost_records_jsonl._refuse_constant`, `StopService._require_commit_beyond_main`, `AskHandler._record_attempts_cap_question`: error message texts set to `None`. These are messages, not behaviour.
- **Code the feature touched but did not write** (mostly F0005 to F0019 code in the same modules):
  - `recovery` (24): `_note_expiry`, `_record_pull_request`, `_remote_head`.
  - `closed`, `hand_over` and `questions` (6 to 13 each): `_no_state()` arguments and commit subjects.
  - `domain.acceptance` (12): `refusal_reason`, `is_before_approval`.
  - `application.acceptance` (19): `AcceptanceClosed._book` and `_record_close`.
  - `entry.wiring` (19).
  - `claude_runtime._resume` and `_resumed_result` (16). Among them: a resume that the time limit ends drops the first call's denials, which changes only the detail of a time-limit stall (`stage._first_denial`). The cost record leaves `denials` `None` for a `time_limit` run anyway.

  These are older code. Following earlier acceptances' practice, they are not proposed here.

## 4 What the stories noticed

- S0001 coder (entries 7, 15, 19, 23): `AskHandler` writes the literal `"attempts_cap"` twice (on the record and on the state). The handler tests' `pull_request` fixture stays separate from `crash_support.open_pull_request`, as the tester chose. Both are small; no story.
- S0001 coder: running pytest directly in the sandbox fails 8 tests with `RepositoryUnsealed`, because of group-writable folders. `make test` sets `umask 022` and passes. This is known and handled by the Makefile.
- S0002 coder and documenter: `human_waits._hours` repeats the seconds-to-`Decimal` step of `bills._minutes`; the reviewer accepted it. `make duplicates` reports "3 gone" in every story (the unused `close` methods in `fake_hosting.py`, `pygithub_hosting.py` and `application/hosting.py`). `security/duplicates-baseline.txt` is the human's, so updating it is theirs.
- S0003 coder: a `raise_stop` without a readable health status appends no record. The human decided that (entry 15), and it is now criterion 16 and in `docs/decisions.md`.
- S0003 documenter (entry 28): the project guide's `Boundaries` field list leaves out `disk`, `disk_records` and `stop_records`. The documenter also wrote the decision entry's "Rejected" line without reading `feature.md`, and it differs from decision 1. Both go into S0007.
- S0004 coder (entries 10, 17, 25, 28): `tests/application/test_watcher_move_rule.py::test_every_factory_move_is_no_reject[tests-doing]` failed once under the full parallel run. It did not fail again, neither in this acceptance's `make check` nor in the later stories'. One flake, not reproduced; no story.
- S0004 smoke tester: the human's smoke test gave two cost records the same `run`, and the duplicate-run check refused it. The human fixed it (entry 26). Not a defect of the code.
- S0005 coder: the tester's step 0 places the added-criterion sentence after "Skip the steps below." It reads oddly but is correct; no story.
- S0005 documenter (entry 11): in `docs/operator-guide.md`, *The factory's own questions*, the "Comment reads" cell of "The form has findings" and of "The round cap" says `no claude process of agent; see "A time_limit under sudo" above`. That is a stray cell from F0012-S0024 (`f950da6f`) and wrong: the comment reads `factory: ` and the question's text. The table now also has the feature's `blocked` column, so a reader of the feature meets it. Goes into S0007.
- S0006 documenter: the operator guide's opening paragraph, which lists the built parts, names neither the stop records nor the records contract. Goes into S0007.
- S0006 coder: the schemas say `additionalProperties: false`, while readers are told to ignore unknown properties. The operator guide's "Unknown properties" paragraph explains this. Nothing open.

## 5 The documentation as a whole

`README.md` (30 lines) needs nothing from this feature. In `docs/`, the feature's sections agree with each other and with the code: the journal's data, the cost table's `Human:` line, refused tool calls, the stop records and "The stops", the records contract, and the acceptance facts. The decision entries of S0001, S0003, S0005 and S0006 are present. Findings:

1. **An example that no longer prints what the guide says.** `docs/project-guide.md:496` says the journal example prints `number=2 speaker='intake' kind='result' at=None stage=None run=None`. Run now, it prints `number=2 speaker='intake' kind='result' at=None stage=None run=None blocked=None reason=None`, since S0001 added the two fields.
2. **A wrong cell** in the operator guide's table of the factory's own questions (lines 601 and 602), as under 4.
3. **An incomplete field list.** The project guide's *Boundaries* (line 1084) lists the fields up to `settings` and leaves out `disk`, `disk_records` and `stop_records`. Other paragraphs describe each of them, but the list is the one a newcomer reads.
4. **A decision entry that differs from the feature's decision.** "The stops reach main as raised and cleared records" (`docs/decisions.md`) gives its own reason for leaving out the detail ("the detail is the instance's"). The feature's decision 2 names `make secrets` on `main`: a git error's text can hold a commit id or a URL. Its "Rejected" line also leaves out the feature's rejected GitHub issue or comment (R10: the hosting-service interface does pull requests only).
5. **An opening summary without the feature.** The operator guide's opening paragraph names neither the stop records on `main` nor the records contract.

None of these misleads a user about behaviour in a way that loses data. Finding 2 tells the operator the wrong comment text for two questions. Together they are one documentation story (S0007).

## 6 Decisions taken for the human

From `feature.md` (decisions 1 to 16, each "this feature's draft" unless noted). For the human to accept or revisit:

1. Stops are published to `factory/stops.jsonl` on `main`, after the restore. The human answered on 2026-10-18. The accepted effect: while `preflight_failed` stands, a `stops recorded` commit clears `main_branch_failing` although `main` is still red. The feature says "a later story may make that rule ignore a commit that changes only `factory/stops.jsonl`", and S0008 is that story, proposed for the human to take or drop.
2. No `detail` in the published record.
3. Two events per stop, `raised` and `cleared`.
4. No reason on `crash` or `expiry` records.
5. A wait ends at the human's next record, a comment or a close.
6. Only a `question` with `blocked` is a wait. In practice this left S0001's round-cap answer uncounted (section 2), so the feature's own facts line says 7 where the human answered 8 times.
7. The factory's form-findings question and the agent's question share `blocked: question`; `speaker` tells them apart.
8. Refused tool calls: what is counted, `None` for a run with no reply. Worded by the human on 2026-10-18.
9. F0020 adds its spend-limit waits as optional fields. The human's word.
10. "From round 1 on" means the second review on. The human's answer.
11. The reviewer's added criterion goes through `doing` and counts a round.
12. The operator guide's rule is pinned by a smoke-test `grep`, not by pytest.
13. and 14. Leaves to change earlier tests (below).
15. The contract's place and version rule.
16. No validator library.

Decisions taken in the stories' journals:

- S0001, entry 27 (the human, after the round cap): `append_entry` keeps `**causes: Unpack[JournalCauses]` instead of two keyword parameters, because ruff's `PLR0913` refuses six arguments and the per-file ignore is in `pyproject.toml`.
- S0003, entries 15 and 24 (the human): without a readable health status no `raised` record is appended. The reviewer had leave for exactly three edits to the work item.
- S0004, entry 4 (the human): a row for `file_path` that is not a string falling back to `notebook_path`. Entry 11: leave for `tests/application/test_costs.py`, plus valid decisions in two rows of the new test. Entry 26: the smoke test's two records get distinct `run` values, and the reviewer had leave to make that edit.
- S0006, tester's defaults: a schema without `required` counts as an empty list; "exactly one newline" is checked as text ending in `}\n`.

Earlier tests changed, each with its leave as the reviewers' entries name it. Every change was found in `git log` of the story commits, and none lacks a leave:

- `tests/application/handlers/test_questions.py`, `tests/application/test_stalls.py`: decision 13 (S0001).
- `tests/application/test_recovery_cap.py`, `tests/application/test_recovery_expiry.py`: decision 13 (S0001), plus the standing leave to move a shared test helper (helpers moved to `tests/crash_support.py`).
- `tests/application/test_stage_run.py`: the standing leave to move a shared test helper (helpers moved to `tests/stage_run_support.py`, S0001).
- `tests/application/handlers/test_hand_over.py`, `tests/application/test_stage_run_acceptance.py`, `tests/application/test_task_acceptance.py`: decision 13 (S0002).
- `tests/adapters/test_claude_runtime_resume.py`: decision 14 (S0004).
- `tests/application/test_costs.py`: the human's answer in S0004 entry 11, point 2.

## 7 The slow checks

The project offers nothing beyond `make check` and `make mutants`: no image scan and no SBOM target. The disk is unchanged: `Disk now` (acceptance) and the previous record (start) both read `/work 985.7 GB free, 0.5 GB used; /state 0.0 GB used; /tmp 0.0 GB used`. There is no growth to explain.

`make test` took 38.4 s. Its slowest tests (`.reports/junit.xml`):

- `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s.
- `tests/test_fault_paths_7_to_13.py::test_acceptance_container_lost_in_review_reruns_once_and_books_result[refused]`: 3.2 s.
- Three `tests/adapters/test_claude_runtime_confinement.py` time-limit tests: 3.0 s each.

`make mutants` cannot finish within its 540 s limit for a feature of 28 modules. Its first run spent the whole limit on mutmut's clean test run, and its third made no progress past 2806. Partial scores have become the rule, not the exception (see F0019).

## 8 Cost

66 runs, 75.3 min, $20.63 for six stories. Per story (from the sidecars):

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 15 | 20.0 | $6.04 |
| S0002 | 11 | 12.4 | $3.74 |
| S0003 | 13 | 18.8 | $5.13 |
| S0004 | 15 | 14.1 | $3.24 |
| S0005 | 6 | 4.2 | $1.03 |
| S0006 | 6 | 5.7 | $1.45 |

S0001 stands out: 5 doing and 4 review runs. Its reviewer sent it back three times over the quality of its own new tests: copied helpers in round 0, then a merge of two tests into one parametrized test, then the `append_entry` signature. That reached the round cap, and the human answered (entry 27). This is exactly the recurring question S0005 then removed, with notes from round 1 on. S0005 and S0006, the stories after it, each ran once per stage.

S0003 is the second most expensive: one question on `raise_stop` without a readable status, then the reviewer's leave to edit the work item.

S0004 had the most rework outside review. A smoke test whose data the code refused (duplicate `run`) cost a doing run and a second docs and smoke-test pass.

Human interventions: 7 questions answered (question 7), 0.2 h waited. S0003 and S0004 each account for 3 counted answers, S0002 for 1. The story that needed the human most is S0001, although it counts 0. Its round-cap question was recorded by the image before S0001's own rebuild, so it has no `blocked` (decision 6). Its wait therefore appears in neither figure.

## Proposed stories

- `F0021-S0007-the-documents-repair-what-the-feature-s-stories-left-stale.md`: the five documentation findings of section 5 (an example's output, a wrong table cell, a field list, a decision entry against the feature's decisions 1 and 2, the opening summary). It is one documents-only story.
- `F0021-S0008-the-preflight-keeps-main-failing-across-a-stops-recorded-commit.md`: the follow-up decision 1 left to "a later story". While the machine's items fail, a commit that changes only `factory/stops.jsonl` no longer clears `main_branch_failing`.
- `F0021-S0009-the-contract-command-reads-its-arguments-and-creates-its-folder.md`: the surviving mutants of `factory.entry.contract`, namely the arguments from `sys.argv` and the creation of a missing parent folder.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 3 stories proposed; make mutants 2657/2806 (147 survived and 2 timed out; 2947 of the feature's mutants were not reached in three 540 s runs, so the score is partial)
   1 Scope: no gap. Every scope bullet has its story and code; a grep finds no question or stall writer without the field. factory/stops.jsonl is not on origin/main yet because no stop has been raised since S0003's image rebuild.
   2 Feature smoke test: green. It ran on the six archived stories and their sidecars through the real reader, plus one stop raised, cleared and published to a temporary bare remote through build_boundaries, plus a regeneration of the contract. Every record validates against the committed schemas. The facts line it computes equals the prompt's: 7 questions answered (question 7), 0.2 h waited.
   3 Mutants: the gaps in the feature's own code are factory.entry.contract (main reading sys.argv, write_contract with a missing parent folder), proposed as S0009. The rest are equivalent mutants, error texts, or older code in the touched modules (recovery, closed, acceptance, wiring, claude_runtime._resume).
   4 Noticed: five stale document passages flagged by S0003, S0005 and S0006, taken into S0007. Also: one test_watcher_move_rule flake seen once and not reproduced; the duplicates baseline reports "3 gone" (the human's file); the "attempts_cap" literal written twice (small, no story).
   5 Docs: the project guide's journal example now also prints blocked=None reason=None; two wrong "Comment reads" cells in the table of the factory's own questions; the Boundaries field list stops at settings; the stop-records decision entry differs from feature decisions 1 and 2; the opening summary names neither the stop records nor the contract. All five go into S0007.
   6 Decisions: feature decisions 1 to 16 and the journal answers listed for the human. Decision 6 leaves S0001's round-cap answer uncounted (8 answers, 7 counted). Every earlier test change has its leave (decisions 13 and 14, the standing helper move, S0004 entry 11). S0008 is the follow-up that decision 1 left to a later story.
   7 Slow checks: nothing beyond make check and make mutants. Disk unchanged (0.5 GB used at start and now). make test took 38.4 s; the slowest test, the time-limited resume, took 5.0 s. make mutants cannot finish 28 modules within its limit.
   8 Cost: 66 runs, 75.3 min, $20.63. S0001 stands out ($6.04, 15 runs): three send-backs over its own tests' quality, then the round cap. That is the human's real intervention, though it counts 0 by decision 6, and it is the question S0005 removed. S0005 and S0006 ran once per stage. 7 questions answered, 0.2 h waited, 3 each in S0003 and S0004.
