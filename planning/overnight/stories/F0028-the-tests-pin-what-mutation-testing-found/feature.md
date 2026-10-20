# The tests pin what mutation testing found

## Goal

The mutation sweeps of 2026-10-19 left behaviour alive that no test pins: the code does the right thing today, and a change that broke it would still pass `make check`. The first sweep (`planning/overnight/mutation-sweep-2026-10-19.md`) ran mutmut over `factory.domain` and left 129 of its checked mutants alive, 74 of them behaviour no test pins. The second and third (`mutation-sweep-2026-10-19-part2.md` and `-part3.md`) ran over most of `factory.application` and left 94 such mutants: 24 behaviours, 23 commit subjects and 47 messages. By the human's decision of 2026-10-19 (22:20) the feature takes both layers. It turns into criteria the first sweep's 40 behaviours and the settings messages an operator reads (its stories 1 to 4):

- the edges of the repository URL's password rule and the operator's settings messages;
- text right at a section's edge in the sections, the journal and the story form;
- the acceptance refusal's reason and body, and the board's absent and blocked values;
- seven small rules, each on both sides.

It also turns into criteria 21 of the application's 24 behaviours, its 23 commit subjects and 3 messages an operator reads (the later reports' stories 3, 6 and 7, and the third's S0008):

- the acceptance reviewer's role at the hand-over and the close, and the close's commit subjects;
- the subjects of a story's recovery and handler commits;
- the expiry note's key at the crash cap and the stalls at their edges;
- the stage's aftermath, the opening and the tick at their edges;
- the dispatcher, the board and the preflight at their edges.

The other three behaviours turned out equivalent (decision 10). Every story adds tests only. The code already behaves as the criteria say, so the coder has nothing to change, as in F0025-S0003. It is for whoever changes these modules next: the change that breaks one of these rules now turns a test red. Done when every story below is merged and `make check` is green. The check after the feature is the human's (see *The human's changes*): by the same decision of 22:20 `make mutants` runs in no acceptance (F0031), so a hand run of mutmut over the feature's modules shows the kills.

## Scope

- `tests/domain/test_settings_url_edges.py`: the password rule at the URL's edges and the settings' messages, of `factory.domain.settings` (S0001).
- `tests/domain/test_section_edges.py` and `tests/domain/test_story_form_edges.py`: text at a heading's edge in `factory.domain.sections`, `factory.domain.journal` and `factory.domain.story_form` (S0002).
- `tests/domain/test_acceptance_refusal_edges.py` and `tests/domain/test_board_absent_values.py`: the refusal reason and body of `factory.domain.acceptance`, the absent and blocked values of `factory.domain.board` (S0003). `tests/acceptance_support.py` (new), where `_document` of `tests/domain/test_acceptance_booking.py` moves under the standing leave (S0003).
- `tests/domain/test_tick_status_mark.py`, `test_provider_limits_one_second.py`, `test_resumed_result_time_limit.py`, `test_duplicates_skipped_lines.py`, `test_errors_agent_definition.py`, `test_send_back_records.py` and `test_evaluation_details.py`: seven small rules of `factory.domain` on both sides (S0004). `tests/evaluation_support.py` (new), where the helpers of `tests/domain/test_evaluation.py` move under the standing leave (S0004).
- `tests/application/test_acceptance_reviewer_role.py`: the reviewer's role at the hand-over and the close of `factory.application.acceptance`, and the close's two commit subjects (S0005).
- `tests/application/test_recovery_subjects.py` and `tests/application/handlers/test_handler_subjects.py`: the commit subjects of `factory.application.recovery`, `handlers.closed`, `handlers.comments` and `handlers.reject` (S0006).
- `tests/application/test_recovery_expiry_key.py` and `tests/application/test_stall_edges.py`: the expiry note's key in `factory.application.recovery`; the stalls without a detail, the branch started again after the agent left it, and the red check's undo, in `factory.application.stalls` and `stage` (S0007).
- `tests/application/test_after_agent_edges.py`, `test_opening_journal_edges.py` and `test_tick_stop_details.py`: the empty entry and the counted form findings of `factory.application.stage`, the journal of `opening`, the stop details and the error cap's log line of `tick` (S0008).
- `tests/application/test_dispatcher_without_state.py`, `test_board_in_progress.py` and `test_agent_run_probe_factory_user.py`: the error stop of a work item without a state in `factory.application.dispatcher`, the stories in progress in `board`, the opencode login hint without an agent user in `preflight` (S0009).

## Out of scope

- Any change under `src/factory/`: no story removes or changes code. That includes the three domain guards the first sweep called dead (decision 4), the application's dead code (decision 11) and `Tick`'s unused `status` parameter (decision 12).
- The sweeps' optional story 5, the messages of internal guards: not behaviour a user sees. In the domain these are the `ValueError` and `KeyError` on a misuse in `acceptance`, `archive`, `duplicates`, `kill_points`, `sections` and `stops` (22 mutants). In the application (44 mutants) they are:
  - the `CannotHandle` reasons of the recovery, closed, hand-over, questions and reject handlers;
  - the `WorkItemFormatError` messages and paths of `acceptance`, `acceptance_reading`, `opening` and `work_items`;
  - `PushFailed`'s branch and outcome from `acceptance.open`, `StallService` and `StageFinisher`;
  - the `ValueError` messages of `pause_after` and `RunHandler`;
  - the detail of `StopService._require_commit_beyond_main`.
- The mutants the sweeps classed equivalent:
  - the first sweep's 52 (among them `stop_table`'s 22, built at import time, and `contract_schema`'s, pinned only by a deselected test) and the `_item_text` survivor this feature found equivalent (decision 3);
  - the second sweep's 71 (41 of them the handlers' no-state guards, which `target_of` makes unreachable) and the third's 28;
  - the three application survivors this feature found equivalent (decision 10).
- The mutants that timed out or crashed: the first sweep's 3 and the second's 1.
- What the sweeps did not reach: a later sweep.
  - In `factory.domain`, 650 mutants, and about 131 added since.
  - In `factory.application`, 1,202, the slowest of the layer.
  - `factory.entry` and `factory.adapters` as a whole.
- The documents: every story's docs criterion is `none`, since no behaviour and no message changes.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The settings tests pin the repository URL's edges and the operator's messages
- S0002: The tests pin text at a section's edge in the sections, the journal and the story form
- S0003: The tests pin the refusal reason after the role's own result, and the board's absent and blocked values
- S0004: The tests pin seven small rules on both sides
- S0005: The acceptance tests pin the reviewer's role and the close's commit subjects
- S0006: The tests pin the subjects of a story's recovery and handler commits
- S0007: The tests pin the expiry note's key at the crash cap and the stalls at their edges
- S0008: The tests pin the stage's aftermath, the opening and the tick at their edges
- S0009: The tests pin the dispatcher, the board and the preflight at their edges

## The human's changes

None. Checked against `factory/pipeline.yml`: every story writes only under `tests/` (the tester's `tests/*`); the coder and the documenter have nothing to write. No new dependency, no `.secrets.baseline` entry (the URLs that hold `<user>:<password>@` are built by concatenation, decision 6), no `security/` change, no suppression marker, no `Makefile` or `pyproject.toml` change. No story adds a structural test that reads the source, so `[tool.mutmut]` stays as it is.

The check after the feature, outside the pipeline. By the human's decision of 2026-10-19 (22:20, F0031) `make mutants` runs in no acceptance, so the feature acceptance shows no kills. To see them, run mutmut by hand in a throwaway container, as the sweeps did (since F0032 this can be `make mutants MODULES='<the feature's modules>' MUTANTS_CHILDREN=<n>`, which starts from a fresh `mutants/`): a copy with LF line endings, `TMPDIR` inside the container, `--max-children` of the cores free. Run it over the feature's modules:

- in `factory.domain`, the thirteen modules `settings`, `sections`, `journal`, `story_form`, `acceptance`, `board`, `tick_status`, `provider_limits`, `agent_runs`, `duplicates`, `errors`, `send_back` and `evaluation`;
- in `factory.application`, the twelve modules `acceptance`, `stage`, `stalls`, `recovery`, `opening`, `tick`, `dispatcher`, `board`, `preflight`, `handlers.closed`, `handlers.comments` and `handlers.reject`.

The application's twelve modules hold about 3,600 mutants, `stage` and `preflight` alone about 1,300, and their slowest took most of the third sweep. So either give them a night, or pass mutmut the names of the survivors that decisions 2 and 9 target, as the third sweep passed names. Expected:

- The targeted mutants are killed.
- Still surviving: the sweeps' equivalent ones, the three domain guards' mutants of decision 4, `_item_text 2` (decision 3), the three application survivors of decision 10, the dead code of decision 11 and `Tick.__init__ 6` (decision 12).

## Decisions taken for the human

1. **Tests only.** Every story pins behaviour the code already has, so each says in its Description that the coder has nothing to change, as F0025-S0003 did; its tests are green when the tester ends. (Feature)
2. **Every domain criterion was re-checked against today's code.** The report does not hold mutmut's `show` output, so each survivor was rebuilt from the sweep's line, its reason and mutmut 3.8's operators, and every criterion was run in a throwaway container against a copy of today's `src/`: once on the code (the expected values in the criteria are what it printed), and once on a copy with each rebuilt mutant applied (each row the criterion is for gives another value or raises). The modules' lines are those of the sweep except `factory.domain.settings`, which has moved since the sweep's copy: its lines 113, 116, 121, 124, 125, 157, 203, 243 and 245 are today's 134, 137, 142, 145, 146, 231, 277, 317 and 319, with the same code. One settings variant found equivalent on the way: `rest.split("/", 2)[0]` gives the same authority as `rest.split("/", 1)[0]`. If mutmut numbers a mutant differently from the rebuilt one, the check after the feature (*The human's changes*) shows it. (S0001 to S0004)
3. **`story_form._item_text` 2 is equivalent, not a missing test.** The mutant is the joiner `"XX\nXX"` of the item's lines (the other mutants of that line raise, and every story check would kill them). Both readers of an item's text look for substrings without a line end (`make check`, `green`) or at the text's start (`docs:` after the number), and the mutant only adds characters at line ends, so it changes no finding. A copy with the mutant applied gives the same findings for every row of S0002, the two-line second-to-last criterion included. No criterion pins it. (S0002)
4. **The three guards the sweep called dead stay; two of them are pinned.** Recommended answer: keep all three, no story removes code.
   - `acceptance.py:332` (`journal = [] if document.state is None else document.state.journal` in `refusal_reason`): unreachable for every caller, not only through `book_refusal`. Line 330's `last_record` reads the state first and raises `WorkItemFormatError("the document has no state")` for a document without one, so the `[]` side never runs. Removing it still needs a narrowing for `mypy --strict`: `require_state(document, WorkItemFormatError("the document has no state")).journal`, which `tests/test_no_state_copies.py` allows. That would be a coder story whose only gain is one branch, with one more test of its own. Kept as it is; its mutant is recorded as equivalent. The alternative, if you want it gone: a fifth story, "`refusal_reason` reads the state once", with the line above and a row that a document without a state raises that error.
   - `evaluation.py:66` (`if state is None or state.blocked is None: return False` in `question_posted`): not dead. `question_posted` is public and tested directly; a snapshot without a state reaches the guard (the mutant `and` then raises `AttributeError`). Only its second half repeats the caller's check at line 209 and the key's kind comparison at line 76 (a post's kind is never `None`), so the guard documents the precondition. Kept and pinned: S0004, criterion 8.
   - `evaluation.py:228` (`return None if kind is None else _event(...)` in `_agent_at_work`): not dead in the domain. `ClaimStatusOf` may answer any `ClaimStatus`, `none` included, and only today's two implementations (`claim_status`, `observed_claim_status`) never answer `none` for a claim; `mypy` needs the narrowing of `CLAIM_EVENTS.get` anyway. Kept and pinned: S0004, criterion 9 (a claimed work item whose status is `none` is new work).
   (Feature)
5. **New test modules, no change to an earlier test.** Every story writes test modules of its own rather than adding tests to an earlier story's module. The only edits of earlier test modules are the standing leave's moves of shared helpers, which the tester makes and names in its entry: S0003 moves `_document` of `tests/domain/test_acceptance_booking.py` to `tests/acceptance_support.py`; S0004 moves `DEFINITION`, `_snapshot`, `_blocked`, `_at_approval`, `_claimed`, `_view`, `_factory_comment`, `_Lookup`, `_ClaimStatus` and `_evaluate` of `tests/domain/test_evaluation.py` to `tests/evaluation_support.py` (with what they need: `_id`, `_journal`, `_facts` and the constants `MAIN`, `BRANCH_COMMIT`, `MERGE_COMMIT`, `PULL_REQUEST`, `OTHER_INSTANCE`, `AT`). Each earlier test keeps its name and checks the same thing. S0005 to S0009 move nothing (decision 13). No other leave is needed. (S0003 to S0009)
6. **No secret in a test or a story.** A URL whose authority holds `<user>:<password>@` is built by concatenation in the tests and written as one in the stories (`"https://github.com/owner/x://u:" + "p@y.git"`), as `tests/domain/test_settings.py` already does, so detect-secrets' basic-auth pattern finds nothing in the test or in the work item, which `make secrets` scans. No constant's name holds `password`, `secret` or `token`. (S0001)
7. **The scope of the sweep's story 4.** Its seven modules are one story of seven small test modules and no code. Two rows come from decision 4, and the third half of `refusal_reason`'s gap, a later `result` of the role itself, is a row of S0003's criterion 1 so that both sides of "after the role's own last result" are tested. If S0004's tests stage nears its 40 minutes, its criteria 7 to 9 (the evaluation) are the part to split into a story of their own. (S0003, S0004)
8. **The application's stories, cut from the later reports.** The human widened the feature to `factory.application` on 2026-10-19 (22:20); its stories come after the domain's four.
   - S0005 is the application part of the reports' story 3, with the acceptance's eight commit subjects of story 6: both live in the close of one acceptance, so one module and the `walk` of `tests/conftest.py` hold them.
   - S0006 is story 6's other fifteen subjects.
   - Story 7, eight criteria with the third report's addition, is split in two: the recovery and the stalls (S0007), then the dispatcher, the board and the preflight (S0009).
   - S0008 is the third report's S0008 as it proposed it.
   - Story 5 stays out (*Out of scope*).

   The count of each story's targeted mutants: S0005 11, S0006 15, S0007 7, S0008 8, S0009 6. (S0005 to S0009)
9. **Every application criterion was re-checked against today's code** after F0022, F0023, F0024, F0026 and F0020's follow-ups were merged, in the same way as decision 2. The image has no pytest, so each criterion ran as a prototype test through a small stand-in for pytest's fixtures and parametrize. It ran once on a copy of today's `src/`, which printed the expected values in the criteria, and once per rebuilt mutant applied alone. All 39 rebuilt mutants the criteria target are killed by their story's prototype. Every other prototype row passes on the code as it is.
   - The lines are today's. The second report's `acceptance:399`, `dispatcher:135`, `stage:365` and `stage:416` are today's 400, 196, 362 and 413, with the same code; the third report's lines are today's.
   - The rows the reports proposed changed in three places. A completed run whose entry is `None` cannot be built (`AgentRunResult` refuses it), so S0008's empty entries are `""` and `tester:`. The opening's row of a body whose last line ends in spaces is equivalent (decision 10), so S0008 does not have it. An archived story without a state cannot be read (decision 10), so S0005 does not have it.

   (S0005 to S0009)
10. **Three application survivors are equivalent, not missing tests.** No criterion pins them.
    - `StageFinisher._description` 3 (`stage.py:413`, the reviewer's role at the stage finish): the description is built from the document the stage just appended the reviewer's own `result` to, so that is always the last `result` of any speaker, and passing no role gives the same findings. A copy with the role replaced by `None` passes `tests/application/test_stage_run_acceptance.py`, and no journal on the branch can change that.
    - `AcceptanceService._waits` 6 (`acceptance.py:188`, an archived story without a state): `FrontmatterWorkItemReader.parse` never returns a document without a state (a file without front matter or without `stage` raises `WorkItemFormatError`, which `_waits` turns into no waits), so the guard is the narrowing `mypy` needs and its other side never runs.
    - `_with_journal_section` 5 (`opening.py:33`, `rstrip(None)` for `rstrip("\n")`): the body comes from `parse_specification`, which strips it (`_normalised_body`), so it ends in one line end and nothing before it is blank. Both strips give the same text. A copy with the mutant gives S0008's body for a backlog text whose last line ends in two spaces as well. The variant `rstrip("XX\nXX")` is equivalent for the same reason.

    (S0005, S0008)
11. **The application's dead code stays.** The second report found two pieces. The `head is None` guard of `RecoveryHandler._remote_head` (`recovery.py:199`, five mutants) cannot fire, because the discard has just checked that ref out; it is there for the type. `StallResult.undo` (`stalls.py:49`, one mutant) is read by no code under `src/`. Recommended answer: keep both, as decision 4 keeps the domain's guards. (The human, 2026-10-19: keep both.) Removing either is a coder story whose gain is a line, in a feature of tests only. (Feature)
12. **`Tick`'s `status` parameter (`tick.py:73`), which no caller passes.** `entry/wiring.py:445`, `tests/acceptance_walk.py` and every test build `Tick` without it, so `self._status = TickStatus() if status is None else status` (line 83) is always `TickStatus()`, and its mutant `Tick.__init__ 6` survives every test. A rebuilt copy with the line reduced to `TickStatus()` passes the whole `tests/application/test_tick.py`. The tick's status lives in the instance, and a restart starts from one, which `test_the_tick_keeps_its_status_across_ticks_and_a_restart_counts_from_one` pins.
    - (a) Keep it: its mutant is recorded as dead. The parameter goes with the next story that changes `tick.py` anyway, where its removal is one line and one docstring.
    - (b) A tenth story, for the coder: "The tick takes no status". It removes the parameter and the `None` branch, with a criterion that `Tick(boundaries, instance, handlers)` and `Tick(..., preflight=...)` still build and `make check` stays green.
    - (c) A test that passes a status: it would pin an interface no caller uses.

    Recommended: (a). (The human, 2026-10-19: (a), keep it and remove it with the next story that changes `tick.py`.) F0028 changes no code (decision 1), the parameter misleads nobody who reads its one line, and (b) would cost a coder stage and a review for one line. (Feature)
13. **S0005 to S0009 move no helper and change no earlier test.** Each builds on what is shared already:
    - from `tests/conftest.py`, the fixtures `walk`, `kill_points` and `installed_agents`;
    - the support modules `tests/acceptance_walk.py`, `tests/crash_support.py`, `tests/stage_run_support.py` and `tests/log_support.py`;
    - the fixtures of `tests/application/handlers/conftest.py`.

    What a test needs beyond them is a small class of its own, not a copy of an earlier one: an agent runtime that leaves the branch, a git whose fetch or reset fails, a handler that raises. So no leave is needed. (S0005 to S0009)
14. **Sizes.** Each story fits a tester's 40 minutes. The largest is S0008, with five criteria in three modules; if its tests stage nears the limit, its criteria 4 and 5 (the tick) are the part to split into a story of their own, as the third report proposed. S0007's and S0008's tests run whole stages, a few seconds each, which `make test` spreads over its workers. (S0007, S0008)
