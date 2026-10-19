# Mutation sweep of factory-rf, 2026-10-19

The brief: `planning/overnight/briefs/mutation-sweep.md`. The copy was a fresh copy of factory-rf in `C:/Users/pasca/AppData/Local/Temp/mutsweep/repo`, with no `.git`, no `mutants/`, no `image/secrets/` and no `planning/`. Its `.venv` held the locked groups, so nothing was installed. Every run was a throwaway container of `factory-self-factory` (`--network none --cpus 3`, the image's own user `factory`, no volume but the copy). The copy has been removed.

## 1. The run

- **mutmut** 3.8.0, run as `pyproject.toml`'s `[tool.mutmut]` sets it up (its `source_paths` is already `src/factory/`, its `also_copy` and its 13 deselected tests). Each run used `--max-children 3`, `umask 022` and a `TMPDIR` of its own, and its `.git` folders under `mutants/` were removed afterwards, as `make mutants` does.
- **Count**: 14,714 mutants in 128 modules: domain 3,635, application 5,799, entry 1,367, adapters 3,913. `contract` has no Python module (only the `*.schema.json` files), so it has no mutants.
- **Sample**: `factory.domain.disk` (27 mutants) took 620 s in all. About 430 s of that was mutmut's one-off clean run and stats collection; the 27 mutants took about 20 s. The domain run then managed about 0.63 mutants a second, and fell to about 0.35 a second in the widely imported modules. At that rate the whole run would take at least 6.5 hours, so the sweep went by layers.
- **Time**: 620 s (sample) + 4,780 s (`factory.domain.*`, stopped by `timeout`) = **5,400 s, 90 minutes of mutmut**. The limit was reached inside `domain`; `application`, `entry` and `adapters` were not started.
- **One fix to the copy, not to the repository**: the copy came from a Windows checkout with CRLF line endings. Because of them, the first stats run failed in `tests/test_agent_home_ownership.py` (`image/entrypoint.sh: set: Illegal option -`). I converted the copy's 894 text files to LF, which is what git stores, and after that the whole suite passed (158 s with `-n 3`). Copy from a checkout with LF line endings next time.

Counts by status, `factory.domain` (the only layer swept):

| module | killed | survived | timeout | segfault | not checked |
|---|---|---|---|---|---|
| acceptance | 325 | 17 | | | |
| agent_runs | 64 | 2 | | | 2 |
| answers | 26 | | | | |
| archive | 10 | 1 | | | |
| bills | 166 | | | | |
| board | 103 | 6 | | | |
| checks | 22 | | | | |
| confinement | 123 | | | | |
| contract | 8 | 3 | | | |
| decisions | 131 | 1 | | | |
| disk | 27 | | | | |
| documents | 129 | | | | |
| duplicates | 107 | 9 | 1 | | |
| errors | 52 | 1 | | | 9 |
| evaluation | 346 | 16 | | | |
| git | | | | | 64 |
| hand_over | 78 | | | | |
| hosting | 27 | | | | |
| human_waits | 49 | 1 | | | |
| identifiers | 10 | 1 | | | 41 |
| journal | 98 | 4 | | | 149 |
| kill_points | 6 | 1 | | | 17 |
| labels | 1 | | | | |
| lease | 21 | | | | |
| move_rule | 20 | | | | |
| paths | | | | | 24 |
| pipeline_definition | 32 | | | | 81 |
| post_texts | 114 | 4 | | | |
| preflight | 29 | | | | |
| prompts | 24 | | | | |
| provider_limits | 37 | 1 | | | |
| recovery | 11 | | | | |
| sections | 79 | 8 | | 2 | 86 |
| send_back | 30 | 3 | | | |
| settings | 297 | 19 | | | |
| stop_table | | 22 | | | |
| stops | 24 | 1 | | | |
| story_form | 160 | 6 | | | 149 |
| tick_status | 45 | 2 | | | |
| times | | | | | 1 |
| work_item | | | | | 2 |
| write_paths | 22 | | | | 25 |
| **domain** | **2,853** | **129** | **1** | **2** | **650** |
| application, entry, adapters | | | | | 11,079 |
| **all** | **2,853** | **129** | **1** | **2** | **11,729** |


## 2. Triage

Of the 132 checked mutants that were not killed: **74 missing test** (34 of them only an unpinned error message), **52 equivalent**, **3 dead or redundant code**, **3 slow, timed out or crashed**. The 650 domain mutants that were not checked are classed together at the end. Rows that share a line and a reason are grouped; the mutant numbers are mutmut's (`mutmut show factory.domain.<module>.x_<function>__mutmut_<n>`).

Two causes explain 25 of the equivalent mutants, and neither is a gap in the tests:
- **Import time.** `stop_table.STOP_TABLE` is built when the module is imported, before mutmut switches a mutant on. Its 22 mutants cannot be killed under mutmut, although the tests of the table would catch them.
- **A deselected test.** The indent of `contract_schema` is pinned only by `tests/entry/test_contract.py::test_the_committed_schemas_are_the_generated_ones`, which `[tool.mutmut]` deselects.

| mutant | module:line | status | class | reason |
|---|---|---|---|---|
| acceptance_id 4 | acceptance:84 | survived | missing test (message) | the range message of `acceptance_id` is not pinned |
| acceptance_file_name 3 | acceptance:110 | survived | missing test (message) | "not an acceptance id" message not pinned |
| _acceptance_state 2, 3, 4 | acceptance:286 | survived | missing test (message) | message for a plain state not pinned |
| is_before_approval 2 | acceptance:305 | survived | missing test (message) | the `KeyError` does not have to carry the stage |
| is_before_approval 5, 6, 7 | acceptance:308 | survived | missing test (message) | "no approval stage" message not pinned |
| refusal_reason 3, 6 | acceptance:330 | survived | missing test | no test has a later `result` record by another role; the reason must start after *the role's* last result |
| refusal_reason 4, 7 | acceptance:330 | survived | missing test | no test has a later non-result record by the role (for example a question) after its last result |
| refusal_reason 16 | acceptance:332 | survived | dead or redundant code | `book_refusal` checks the acceptance state first, so `document.state is None` cannot happen here |
| refusal_reason 26 | acceptance:336 | survived | equivalent | the record numbered `after` is the role's own result, never a human comment |
| _with_recommendation 36 | acceptance:352 | survived | missing test | no test pins the exact body after the recommendation is inserted (its single trailing newline) |
| book_refusal 4 | acceptance:361 | survived | missing test | the same gap as refusal_reason 3: the role is never needed to tell results apart |
| resumed_result 16, 17 | agent_runs:218 | survived | missing test | a resume ended by `time_limit`, with a session only on the first call, must keep the first session |
| destination_path 3 | archive:9 | survived | missing test (message) | message not pinned |
| work_item_row 3, 24, 27, 33 | board:54, 59, 60, 63 | survived | missing test | no board test has a work item without a state (a backlog item): its row should read stage, blocked, claim and pull request as absent |
| _work_item_line 9 | board:116 | survived | equivalent | `astimezone(None)` is the local zone, and the test container runs in UTC |
| _work_item_line 12 | board:123 | survived | missing test | no board line shows a blocked work item (`blocked=<reason>`) |
| contract_schema 7, 9, 10 | contract:57 | survived | equivalent (under mutmut) | pinned only by the deselected committed-schemas test |
| agent_entry 26 | decisions:43 | survived | equivalent | `on=None` is the field's default |
| _pylint_messages 3, 5, 6, 7, 8, 11, 22 | duplicates:43, 45, 49, 54 | survived | missing test (message) | the messages for malformed pylint output are not pinned |
| _pylint_messages 16 | duplicates:51 | survived | missing test | no input has a message of another symbol *before* a duplicate-code message (`break` would drop it) |
| dead_code_findings 8 | duplicates:93 | survived | missing test | no vulture text has a blank line *before* a finding |
| _similar_code_finding 19 | duplicates:70 | timeout | slow or timed out | `index = 1` loops forever; the test's time limit caught it; no fault in the code |
| AgentDefinitionError.__init__ 3 | errors:152 | survived | missing test | the message without a name (`AgentDefinitionError("", fault)`, which `adapters/agent_files.py:59` raises) is not pinned; it would read "agent : …" |
| question_posted 2 | evaluation:66 | survived | dead or redundant code | the guard repeats the caller's: line 209 calls it only for a blocked state |
| evaluate 13, 16, 17 | evaluation:96 | survived | equivalent | `states` is built one per snapshot, so `strict` never matters |
| _reject 22 | evaluation:160 | survived | equivalent | an illegal stage change is seen on a branch, so `branch_commit` is set and `main_commit` is never used |
| _human_signal 19 | evaluation:176 | survived | equivalent | a waiting work item has a branch, so `main_commit` is never used |
| _signal_of_observation 6, 12, 17, 33 | evaluation:197–210 | survived | missing test | no test pins that the merged, closed, hand_over and ask events have an empty detail, which `entry/watch.py` prints |
| _signal_of_observation 34 | evaluation:211 | survived | equivalent | the caller replaces the detail when the kind is `None` |
| _agent_at_work 27 | evaluation:228 | survived | dead or redundant code | the claim exists and `held` has returned, so the status is `own` or `expired`, and `kind is None` never happens |
| _new_work 19, 21 | evaluation:244 | survived | equivalent | the sort keys are unique, so comparing the whole tuple gives the same minimum |
| _due_order 1, 2 | evaluation:261 | survived | equivalent | a due acceptance and that feature's acceptance work item never exist together |
| _answered_at 3 | human_waits:32 | survived | equivalent | the record numbered `question` is the question itself, never the human's |
| work_item_order 4 | identifiers:72 | survived | equivalent | rank 2 keeps the same order: story, then the due acceptance, then the acceptance |
| _entry_lines 2 | journal:222 | survived | missing test | no journal has a numbered line (`1. …`) just above its heading, which `start - 1` would take for entry 1 |
| _entry_lines 3 | journal:222 | survived | missing test | no journal has an entry right under its heading, without a blank line between |
| _entry_lines 24 | journal:229 | survived | equivalent | `next(..., None)` as a slice end is the same as `len(content)` |
| entry_text 26 | journal:241 | survived | equivalent | the first line always holds `": "`, so `[1]` is the same as `[-1]` |
| KillPoints.arm 4 | kill_points:41 | survived | missing test (message) | message not pinned |
| stall_note 4 | post_texts:57 | survived | missing test | no detail ends in trailing spaces; `rstrip(None)` would strip them from the last line |
| stall_note 6 | post_texts:57 | survived | equivalent (in practice) | it differs only for a detail that ends in `X` |
| _text_block 12, 13 | post_texts:73 | survived | equivalent | the joiner holds no backtick, and `max(3, …)` absorbs `default=1` |
| named_wait 26 | provider_limits:89 | survived | missing test | the boundary "in 1 second" (1 s gives a wait, 0 s gives none) is not tested, against the both-sides rule in CLAUDE.md |
| _closes 3, 5 | sections:48 | survived | equivalent (in practice) | they differ only for a fence indented with other whitespace or with `X` |
| _closes 10 | sections:49 | survived | equivalent | a fence is one repeated character, so `fence[1]` is `fence[0]` |
| _closing_index 3, 4 | sections:53 | segfault | slow or timed out (crashed) | the mutant crashes the test process, so it is caught; no fault in the code |
| _closing_index 6 | sections:53 | survived | missing test | no test has an empty fenced block (the closing fence right after the opening one) |
| section_text 10 | sections:132 | survived | missing test | no section has text right under its heading |
| insert_paragraph 2, 3, 4 | sections:140 | survived | missing test (message) | "the paragraph to insert is blank" message not pinned |
| _records 1 | send_back:9 | survived | missing test | `reason_given` on a document without a state is never tested (expected `False`) |
| recorded_since_latest_result 11 | send_back:18 | survived | missing test | no journal has a record numbered 1 of the asked kind and no result |
| recorded_since_latest_result 15 | send_back:19 | survived | equivalent | callers ask for `comment` or `close`, never `result`, so the result record itself never counts |
| _repository_url 11, 14, 15, 18, 21, 22 | settings:113, 116 | survived | missing test (message) | the operator-facing messages "names more than one repository" and "holds a password; use the token file" are not pinned |
| _holds_password 3 | settings:121 | survived | missing test | no URL holds a second `://` (for example in its path) |
| _holds_password 8, 11, 12, 13, 14 | settings:124 | survived | missing test | no URL has `user:x@` in its *path* (for example `https://host/a:b@c`), which must not count as a password |
| _holds_password 18 | settings:125 | survived | missing test | no URL has a user name that holds an `@` before the `:` (`https://u@x:y@host/`) |
| _provider_limit 20 | settings:157 | survived | missing test (message) | "is shorter than the cool-down" is matched only loosely |
| _name 3, 6, 7 | settings:203 | survived | missing test (message) | "is not a name" message not pinned |
| read_setting_file 4, 9 | settings:243, 245 | survived | missing test (message) | the "cannot read" and "is empty" messages are not pinned |
| _require_scope_of_reason 10 | stops:38 | survived | missing test (message) | message not pinned |
| _health 1–12 | stop_table:45 | survived | equivalent (under mutmut) | runs only at import time, when the table is built, before mutmut switches the mutant on |
| _pull_request 1–10 | stop_table:50 | survived | equivalent (under mutmut) | the same: import time only |
| _items 9 | story_form:87 | survived | missing test | no story has a numbered line just above a section, which `start - 1` would count as an item |
| _items 10 | story_form:87 | survived | missing test | no story has an item right under its section heading |
| _items 32, 35, 36 | story_form:94 | survived | equivalent | `ends` has one entry per start by construction |
| _item_text 2 | story_form:130 | survived | missing test | no test reads the text of an item that runs over several lines |
| mark_reported 3, 8 | tick_status:60 | survived | missing test | no status holds two entries; only the one with the key *and* the remote state must be marked |
| 650 domain mutants (see section 4) | git, journal, story_form, sections, pipeline_definition, identifiers, write_paths, paths, kill_points, errors, agent_runs, work_item, times | not checked | slow or timed out | not reached in the 90 minutes; these widely imported modules run many tests per mutant; no fault |

Per class: missing test 74 (40 behaviours + 34 messages), equivalent 52, dead or redundant 3, slow, timed out or crashed 3 (+ 650 not checked).

The three dead guards (`acceptance:332`, `evaluation:66`, `evaluation:228`) are defensive repeats of a check made just before them. Removing them is a change to the code, so it is listed here only; it is not a story.

## 3. Proposed stories

All belong to a new feature, "the tests pin what mutation testing found"; each fits a coder's 40-minute `time_limit` and changes tests only.

1. **Settings: passwords in the repository URL and the operator's messages.** `factory.domain.settings`, tests in `tests/domain/test_settings.py`. Criteria: a URL whose *path* holds `a:b@c` is not refused as holding a password; a URL whose path holds a second `://` is judged by its authority; a user name with an `@` before the `:` is refused; the exact `SettingsInvalid` messages "names more than one repository", "holds a password; use the token file", "is shorter than the cool-down", "is not a name", "cannot read <path>: …" and "<path> is empty" are pinned as rows of one parametrized test.
2. **Sections, journal and story form at the edges of a section.** `factory.domain.sections`, `factory.domain.journal`, `factory.domain.story_form`, tests in `tests/domain/test_sections.py`, `test_journal.py` and `test_story_form.py`. Criteria: text right under a heading (no blank line) is read in full by `section_text`, by the journal's entry 1 and by the first story item; a numbered line just above the journal heading or a story section is never taken for an entry or an item; an empty fenced block closes on the next line; the text of an item over several lines is returned line by line.
3. **Acceptance refusal and the board.** `factory.domain.acceptance` and `factory.domain.board`, tests in `tests/domain/test_acceptance_booking.py` and `tests/domain/test_board.py`. Criteria: the refusal reason takes the human's comments after *the role's* last `result`, not after a later result of another role, and not after the role's later question; the refused body ends in exactly one newline; the board row of a work item without a state shows stage, blocked, claim and pull request as absent; a blocked work item's line reads `blocked=<reason>`.
4. **Small rules, each on both sides.** `factory.domain.tick_status`, `provider_limits`, `agent_runs`, `duplicates`, `errors`, `send_back` and `evaluation`, tests in their `tests/domain/` modules. Criteria: `mark_reported` marks only the entry whose event key *and* remote state match; "in 1 second" gives a one-second wait and "in 0 seconds" none; a time-limited resume keeps the first call's session when the second has none; a non-duplicate-code pylint message before a duplicate-code message, and a blank vulture line before a finding, lose nothing; `AgentDefinitionError("", fault)` reads only the fault; `reason_given` is `False` for a document without a state, and a comment numbered 1 with no result counts; the merged, closed, hand_over and ask events carry an empty detail.
5. **(Low value) The messages of internal guards.** `factory.domain.acceptance`, `archive`, `duplicates`, `kill_points`, `sections`, `stops`, tests in their modules. Criteria: each `ValueError` and `KeyError` raised on a misuse carries its message (22 mutants). Take this story only if pinned messages are wanted; they are not behaviour a user sees.

## 4. What was not swept, and why

- **`factory.application` (5,799), `factory.entry` (1,367), `factory.adapters` (3,913)**: not started. The 90 minutes ran out inside `domain`.
- **650 mutants of `factory.domain`**, not checked: `git` 64, `journal` 149, `story_form` 149, `sections` 86, `pipeline_definition` 81, `identifiers` 41, `write_paths` 25, `paths` 24, `kill_points` 17, `errors` 9, `agent_runs` 2, `work_item` 2, `times` 1. mutmut runs these widely imported modules last, and many tests cover each of their mutants; that is where the speed fell to about 0.35 a second.
- **`factory.contract`**: holds no Python, so it has nothing to mutate.
- To finish the rest at the measured speed would take another 5 to 6 hours. The results stay in `mutants/` only within one copy, so the next sweep can run a layer a night, and can start with the 650 domain mutants that were left.
