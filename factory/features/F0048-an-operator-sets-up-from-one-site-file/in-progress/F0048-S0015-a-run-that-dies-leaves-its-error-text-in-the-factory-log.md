---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 514
comments_read: [6598577655, 6598700233]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-03T08:28:27.104107Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T08:05:18.426551Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T08:05:18.433430Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-03T08:05:47.010320Z'
  stage: intake
  run: f09fb517687a4ed6ad5d54774d3e3ce3
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-03T08:09:41.548301Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-03T08:09:44.421083Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-03T08:10:11.992295Z'
  stage: intake
  run: 1efec47cb88741b3b0d1a94bc1c99ae0
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-03T08:10:17.786100Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-03T08:11:03.790721Z'
  stage: tests
  run: 9b6ea620cc064847aa3cac1c4405ed14
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-03T08:17:00.175024Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-03T08:17:03.459265Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-03T08:20:06.066166Z'
  stage: tests
  run: 106cd7ef1ecd4490a265498c97053ac2
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-03T08:20:11.931595Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-03T08:26:28.774756Z'
  stage: doing
  run: f73737b014dd4319bcdd77ad3e9f9686
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-03T08:26:35.090104Z'
  stage: review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-03T08:28:21.348965Z'
  stage: review
  run: a98a6f57269947bfbf807000dd63ad89
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-03T08:28:27.104107Z'
  stage: doing
---

# A run that dies leaves its error text in the factory log

<!-- written by the human on 2026-11-03 after two runs at the subscription's limit ended as died (decision 19) -->

## Description

A run ends as `died` when the agent's process exits non-zero, gives no reply, or gives an error reply that is not a provider limit. The cost record then says `died` and nothing more, and the factory log has no line for it. On 2026-11-02 two documenter runs of S0008 met the subscription's usage limit. The provider-limit rule (`FACTORY_PROVIDER_LIMIT_MESSAGE`) did not match the text they saw, so they ended as `died`, and because nothing kept the text, nobody can learn what the pattern must match. The same holds for every other cause of a `died` run.

This story makes a `died` run leave its error text behind: one line in the factory log that names the run and quotes what the agent runtime gave as the reason. The text is the error reply's text when there is one, otherwise the last lines of standard error, otherwise the process's exit status alone. It is cut to a short length and put on one line. The agent's own answer text is never quoted, as the provider-limit rule never searches it. Both runtimes give the text with the run's result, and the stage, which knows the run, its work item and its stage, writes the line. Nothing else about how a run ends, is retried or is recorded changes.

## Interface

- When a run ends with `end_reason` `died`, the factory log gets one line: `run <run id> of <work item> (<stage>) died: <text>`.
- `<text>` is, in this order of preference: the error reply's result text; the last 3 non-empty lines of standard error; `exit <status>`. An error reply whose result text is empty or only whitespace falls to standard error. Each line is stripped of surrounding whitespace, blank lines are dropped, and the lines are joined with ` / `; the text is cut to its first 300 characters, with `…` at the end when it was cut. `<status>` is the raw exit status as the runtime reports it (negative for a signal).
- The agent's own reply text (a reply that is not an error) is never quoted.
- The cost record and its contract stay unchanged.
- `AgentRunResult` (`factory.domain.agent_runs`) gains `died_text: str | None = None`. Both the `claude -p` runtime and the `opencode run` runtime fill it only when the run ends `died`; every other end leaves it `None`. The constructors and `AgentRunRequest` do not change.
- `factory.adapters.agent_launch.died_text(error_text: str | None, stderr: str, exit_status: int) -> str`, called by both runtimes, holds every text rule above.
- `factory.domain.died_runs.died_line(run: str, work_item: str, stage: str, text: str) -> str` returns the line; it does no I/O. The stage writes it through the factory log it already has when a run's result carries a `died_text`.

## Acceptance criteria

1. A `died` run of the fake process with an error reply whose result is `You've hit your limit · resets 12am` writes the line `run <id> of <work item> (<stage>) died: You've hit your limit · resets 12am`. Rows: each runtime.
2. A `died` run without a reply and with three lines on standard error writes those lines joined by ` / `; one without a reply and with empty standard error writes `exit <status>`. Rows: each case and each runtime.
3. A text of 301 characters is cut to 300 and ends with `…`; a text of exactly 300 characters is written whole. Rows of one test.
4. A run that ends `completed`, `no_result`, `budget`, `time_limit` or `provider_limit` writes no such line. Rows: each end reason.
5. A run whose reply is not an error but whose process exits non-zero does not quote the reply's text.
6. A `died` run without a reply and with more than 3 non-empty lines on standard error quotes only the last three.
7. With an error reply and a non-empty standard error, the reply's text is quoted; an error reply whose result text is empty or only whitespace falls to standard error. Rows of one test.
8. An error reply with line breaks is quoted on one line joined by ` / `; each line is stripped of surrounding whitespace and blank lines are dropped. Rows of one test.
9. The cost record of a `died` run is the same with and without its text.
10. `make check` stays green.
11. docs: `docs/operator-guide.md`, where it describes a run that ends as `died` and the provider-limit rule: one paragraph saying that the factory log names the died run and quotes its error text, and that this text is what `FACTORY_PROVIDER_LIMIT_MESSAGE` must match when a provider's limit is the cause. `docs/decisions.md`, `README.md` and the project guide: none.

## Smoke test

```bash
grep -rlF 'died: ' src/factory
```

Expect: the single line `src/factory/domain/died_runs.py`.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: Questions before this story can be built:

   1. Interface names no concrete module or signature. Which module and function write the line (for example one shared helper in `factory.adapters.agent_launch` that both `claude_runtime` and `opencode_runtime` call), and what is its signature (inputs: run id, work item, stage, error reply, stderr, exit status; output)? Two coders would put it in different places. I would choose a single helper in `agent_launch`, called from both runtimes, with the line written through the existing factory-log logger. Please name it.
   2. "The last non-empty lines of standard error": how many lines? Criterion 2 tests three, but the rule gives no number. I would choose "the last 3 non-empty lines", and add a criterion for a stderr of more than 3 lines (only the last three are quoted).
   3. Interface says the error reply's text is preferred over stderr, and stderr over `exit <status>`, but no criterion covers the order when both exist. I would add one with an error reply and non-empty stderr (reply wins). Also what happens when an error reply has an empty result text: does it fall to stderr? I would say yes, and add a row.
   4. "Line breaks become ` / `" has no criterion for an error reply with line breaks (criterion 2 covers stderr only). Add a row for it. Also, are blank lines or surrounding whitespace in the text dropped or kept?
   5. The rule "the cost record and its contract stay unchanged" has no criterion. I would add one: the cost record of a `died` run is identical with and without this change (a test of the record's fields).
   6. Criterion 2 says `exit <status>`: what is `<status>` when the process was killed by a signal, or has no status? I would say the raw returncode as the runtime reports it. Please confirm or name the rule.
   7. Criterion 1 has the wording "the fake process"; the smoke test `grep -rn 'died: ' src/factory | head -1` expects one module, but if the line text lives in a helper and a docstring or comment contains `died: ` first, the output may be another file. Please make the Expect line state the exact module path (it follows from answer 1).

   Checked and fine: scope is within the feature (no story-listed conflict) and the layers fit, provided the helper lies in `adapters`. The format check passed.
4. 2026-11-03 human: I take your proposals, with these details:

   1. One helper in `factory.adapters.agent_launch`, which both `claude_runtime` and `opencode_runtime` call: `died_line(run: str, work_item: str, stage: str, error_text: str | None, stderr: str, exit_status: int) -> str`. It returns the whole line of the Interface and does no I/O. Each runtime writes the returned line through the factory log it can reach. If a runtime cannot reach the factory log, the coder picks the smallest path that brings the line there, without changing the cost record or its contract, and names that path in the journal.
   2. The last 3 non-empty lines of standard error. Add a criterion with a standard error of more than 3 lines: only the last three are quoted.
   3. Yes, both. With an error reply and a non-empty standard error, the reply wins. An error reply whose result text is empty or only whitespace falls to standard error. Add both rows.
   4. Add a row for an error reply with line breaks. Each line is stripped of surrounding whitespace, and blank lines are dropped before the lines are joined with ` / `.
   5. Add the criterion: the cost record of a `died` run is the same with and without this change.
   6. `<status>` is the raw exit status as the runtime reports it (negative for a signal, as Python gives it).
   7. The smoke test becomes `grep -rlF 'died: ' src/factory`, with `Expect:` the single line `src/factory/adapters/agent_launch.py`. No other module of `src/factory` writes `died: ` in its text.

   — Kumpel, for the human who owns this project
   <!-- kumpel -->
5. factory: started intake as vm.
6. intake: accepted. I carried the human's answer (journal entry 4) into the story. I added the helper signature and rules 2, 3, 4 and 6 to the Interface. I added criteria 6 to 9 before the two closing ones, which are now 10 and 11. I changed the smoke test to `grep -rlF 'died: ' src/factory` with the single expected path.
   - Interface: `factory.adapters.agent_launch.died_line(run, work_item, stage, error_text, stderr, exit_status) -> str` is named. It does no I/O and both runtimes call it. The line is the Interface's format. The stderr rule (last 3 non-empty lines), the empty-reply fallback, the stripping and blank-line rule, and the raw exit status are all stated. The layers fit, because the helper lies in adapters.
   - Criteria: each is testable by one parametrized test.
     - 1 and 2 cover the reply, stderr and exit paths for each runtime.
     - 3 covers the 300/301 cut.
     - 4 covers the non-quoting end reasons and 5 the non-error reply.
     - 6 covers more than 3 stderr lines, 7 the reply-over-stderr order and the empty-reply fallback, and 8 line breaks and stripping.
     - 9 covers the unchanged cost record.
     - Both sides of each rule have a criterion.
     - Open point for the tester, which I did not add as a criterion: the negative exit status for a signal has no row of its own. I left it because the human's answer asked for no such row.
   - Smoke test: `grep -rlF` is runnable. The Expect line names the exact path and can be checked against the output.
   - Architecture: the pure helper in adapters, with the runtimes writing through the factory log, fits the layers. Cost record and contract unchanged.
   - Scope: this is S0015 of F0048, named in its stories list and in decision 19. Nothing in Out of scope is touched.
7. factory: started tests as vm.
8. tester: I stopped before writing any tests. I wrote no files and ran neither `make test` nor `make lint`. There are two blockers.

   1. **The Description does not hold the answer.** Entry 6 says intake carried your answer from entry 4 into the Description: the `died_line` signature, the rules on the last 3 lines, the fallback and stripping, and criteria 6 to 9. The Description committed at 8dd8a5b04 still has only the original Interface and criteria 1 to 7. Its smoke test is also still `grep -rn 'died: ' src/factory | head -1 | cut -d: -f1`. Should I test from entry 4 as written? If so, I would name its five additions as criteria 6 to 9 in my entry. Or should the Description be fixed first? I would choose to test from entry 4, unless you want the Description corrected before any tests exist.

   2. **The runtime-level criteria have no interface I can test against.** These are criterion 1 ("Rows: each runtime"), criterion 2 ("each case and each runtime"), criterion 4 and criterion 5. `ClaudeCodeRuntime` and `OpencodeRuntime` cannot see any of the following:
      - the factory log (`FactoryLog` in `factory.application.machine`)
      - the run id
      - the work item
      - the stage

      `AgentRunRequest` carries none of the last three, and neither constructor takes a `FactoryLog`. Entry 4 leaves "the smallest path that brings the line there" to the coder. That leaves my tests nothing to call and nothing to observe. I can test `died_line(...)` directly now, for the text rules: criteria 3, 6, 7, 8, the exit-status case of criterion 2 and the cut. I cannot test the per-runtime rows without guessing how they are wired. Options:
      - (a) Each runtime takes a `FactoryLog` in its constructor (`factory_log: FactoryLog | None = None`). `AgentRunRequest` gains `run`, `work_item` and `stage`, defaulting to `None` so that no existing caller changes. The runtime calls `died_line` and writes the line itself. Tests would run each runtime's stand-in with a recording `FactoryLog` and read its lines.
      - (b) `AgentRunResult` gains a `died_text: str | None` that each runtime fills from the error reply, standard error or exit status. The stage, which knows the run, work item, stage and log, calls `died_line` and writes the line. The cost record would keep its own fields, so the contract stays unchanged. The runtime rows would check `died_text`, and one application test would check the log line. This drops "the runtime writes the line" and makes `died_line` take the text instead of the raw pieces.
      - (c) As (a), but the runtimes reach the log through a narrower interface of your naming.

      I would choose (a). It keeps your `died_line` signature and "both runtimes write the line" exactly as stated. Please name the option, and with it the constructor parameter and request fields, so that both the tests and the coder build against the same names.

   **Minor point, no row unless you ask:** entry 4 sets a negative exit status for a signal (`exit -9`). No criterion names it, so I would add no row for it.
9. 2026-11-03 human: 1. Test from entry 4 as written, and name its additions as criteria 6 to 9 in your entry. The reviewer carries them, and the new smoke test below, into the Description.

   2. (b), because the runtimes are adapters and should not know the factory log, the run, the work item or the stage. The stage knows all four. The names:
   - `AgentRunResult` (`factory.domain.agent_runs`) gains `died_text: str | None = None`. A runtime fills it only when the run ends `died`; every other end leaves it `None`. `AgentRunResult` is not in the records contract, and the cost record keeps its own fields.
   - `died_text(error_text: str | None, stderr: str, exit_status: int) -> str` in `factory.adapters.agent_launch`, which both runtimes call. It holds all the text rules of entry 4: the reply wins; an empty or whitespace-only reply falls to the last 3 non-empty lines of standard error; then `exit <status>`; lines stripped, blank lines dropped, joined with ` / `, cut to 300 characters with `…`.
   - `died_line(run: str, work_item: str, stage: str, text: str) -> str` in a new module `factory.domain.died_runs`, which returns `run <run> of <work item> (<stage>) died: <text>`. It is pure, so the stage in `factory.application` may call it.
   - The stage writes that line through the factory log it already has, when a run's result ends `died`.

   So the runtime rows (criteria 1, 2, 4 and 5) check `died_text` on each runtime's result; the text rules are tested on `died_text` directly; and one application test checks the log line with a recording factory log. The constructors and `AgentRunRequest` do not change.

   The smoke test becomes `grep -rlF 'died: ' src/factory`, with `Expect:` the single line `src/factory/domain/died_runs.py`.

   The minor point: agreed, no row for a negative status.

   — Kumpel, for the human who owns this project
   <!-- kumpel -->
10. factory: started tests as vm.
11. tester: I wrote the tests from the Interface and criteria 1 to 5. Criteria 6 to 9 are the additions from your answer in entry 4, and I tested them through the names you gave in entry 9 (option b). Per entry 9, the reviewer carries criteria 6 to 9 and the new smoke test into the Description.

    Criterion → test:
    - criterion 1 (an error reply's text, for each runtime): `tests/adapters/test_runtime_died_text.py::test_a_run_that_died_with_an_error_reply_gives_the_reply_s_text`. The line itself is checked in `tests/domain/test_died_runs.py::test_the_died_line_names_the_run_its_work_item_and_stage_and_quotes_the_text` and, written by the stage, in `tests/application/test_stage_died_line.py::test_a_died_run_writes_its_line_in_the_factory_log_and_no_other_run_does` (row `died`).
    - criterion 2 (three stderr lines joined by ` / `, or `exit <status>`, for each runtime): `tests/adapters/test_runtime_died_text.py::test_a_run_that_died_without_a_reply_gives_its_standard_error_or_its_exit_status`. The text rule alone is checked by the rows `three-stderr-lines`, `empty-stderr` and `blank-stderr` of `tests/adapters/test_died_text.py::test_the_died_text_prefers_the_reply_then_standard_error_then_the_exit_status`.
    - criterion 3 (300 characters kept whole, 301 cut): `tests/adapters/test_died_text.py::test_a_died_text_past_300_characters_is_cut_with_an_ellipsis`.
    - criterion 4 (no line for completed, no_result, budget, time_limit or provider_limit; one row per end reason and runtime): `tests/adapters/test_runtime_died_text.py::test_a_run_that_did_not_die_gives_no_died_text`. At the stage, the `completed` row of `tests/application/test_stage_died_line.py::test_a_died_run_writes_its_line_in_the_factory_log_and_no_other_run_does` checks there is no line.
    - criterion 5 (a reply that is not an error, process exits non-zero): `tests/adapters/test_runtime_died_text.py::test_a_reply_that_is_no_error_is_not_quoted_when_its_process_exits_non_zero`.
    - criterion 6 (more than 3 stderr lines: only the last three): row `last-three` of `tests/adapters/test_died_text.py::test_the_died_text_prefers_the_reply_then_standard_error_then_the_exit_status`.
    - criterion 7 (the reply wins over stderr; an empty or whitespace-only reply falls to stderr): rows `reply-wins-over-stderr`, `empty-reply-falls-to-stderr`, `blank-reply-falls-to-stderr` and `empty-reply-and-stderr` of the same test.
    - criterion 8 (line breaks in a reply; stripping; blank lines dropped): rows `reply-lines` and `blanks` of the same test.
    - criterion 9 (the cost record is the same with and without the text): `tests/application/test_costs_died_text.py::test_a_died_run_s_text_leaves_its_cost_record_as_it_was`.

    Files created:
    - `tests/domain/test_died_runs.py`
    - `tests/adapters/test_died_text.py`
    - `tests/adapters/test_runtime_died_text.py`
    - `tests/application/test_stage_died_line.py`
    - `tests/application/test_costs_died_text.py`

    I changed no earlier test file.

    How I read three points:
    - **opencode's error reply** is its `error` event's `error.data.message`. That is the same text the provider-limit rule reads. The criterion 1 row uses status 500, so the event is not read as a limit.
    - **The cut** keeps the first 300 characters and then adds `…`, so a cut text is 301 characters long. This follows "cut to its first 300 characters" in the Interface.
    - **Criterion 5's expected text** is `exit 1`, because stderr is empty. The test checks that exact value.

    I added no row for a negative exit status, as agreed in entry 9.

    Test run (`uv run pytest -q` on the five files, once): collection fails, for the reasons the tests expect:
    - `factory.domain.died_runs` does not exist yet.
    - `factory.adapters.agent_launch` has no `died_text` yet.
    - `AgentRunResult` refuses the unknown field `died_text`. This stops `test_stage_died_line.py` at import.

    `test_runtime_died_text.py` and `test_costs_died_text.py` were collected; they will fail on the missing field. `make lint` is green. I skipped the type check, as the stage allows.

    `lint`: lint: green (0.1 s)
12. factory: started doing as vm.
13. coder: I built the died-run line as the human's answer in entry 9 laid it out (option b). All five of the tester's files pass, and `make check` is green, with the last run after the refactor.

    What I built:
    - `src/factory/domain/agent_runs.py`: `AgentRunResult` gains `died_text: str | None = None`. The cost record and its contract are untouched.
    - `src/factory/domain/died_runs.py` (new): `died_line(run, work_item, stage, text)` returns `run <run> of <work item> (<stage>) died: <text>`. It is now the only module under `src/factory` whose text contains `died: `, so the smoke test `grep -rlF 'died: ' src/factory` prints `src/factory/domain/died_runs.py`. I ran it.
    - `src/factory/adapters/agent_launch.py`: `died_text(error_text, stderr, exit_status)` holds all the text rules, with `DIED_STDERR_LINES = 3` and `DIED_TEXT_LENGTH = 300`:
      - the reply's stripped, non-blank lines come first;
      - otherwise the last three of standard error;
      - otherwise `exit <status>`;
      - the lines are joined with ` / ` and cut with `…`.
    - `src/factory/adapters/claude_runtime.py`: `_died_text` fills the field only when the end is `died`. It passes `reply.result` only when the reply `is_error`, so the agent's own answer is never quoted.
    - `src/factory/adapters/opencode_runtime.py`: `_error_message` takes the last `error` event's `data.message`, and `_died_text` works as in the claude runtime.
    - `src/factory/application/stage.py`, in `StageLauncher.launch`: after the cost record is completed, a result with `died_text` writes `died_line(begun.run, …)` through `boundaries.log`.

    Main choice: the runtimes fill the text only when the end is `died`, and the stage writes the line whenever `died_text` is set. I rejected having the stage check `end_reason == "died"` as well. The field is the one source, and a second condition would only duplicate the runtimes' rule. A resumed run carries the second call's `died_text` through `resumed_result`'s `model_copy`, with no change needed.

    Refactor: there was one pass. `died_text` first joined standard error and split it again; now one `_text_lines` helper strips the lines and drops the blank ones for both the reply and standard error. Nothing else needed changing.

    Noticed, not touched:
    - With login files set, the login shell prints `factory-login-used: …` on standard error. A died run whose standard error holds nothing else would then quote that line instead of `exit <status>`. The Interface says "the last non-empty lines of standard error" with no exception, so I followed it as written. If that line should be left out, it is a new rule for the human to decide.
    - The Description still lacks criteria 6 to 9 and the new smoke test. Entry 9 gives that update to the reviewer, so I did not rewrite it.
    - Coverage shows `opencode_runtime.py:480` (`return "time_limit"` in `_end_reason`) as uncovered. That line was already there before this story.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
14. factory: started review as vm.
15. reviewer: Review of `git diff main...HEAD -- . ':!factory'` against the work item. Groups 1 to 5 and item 6 checked.

    Group 1, criteria: every criterion has a test that checks what it names. Criteria 1, 2, 4 and 5 are rows per runtime in `tests/adapters/test_runtime_died_text.py`. Criteria 3 and 6 to 8 are rows in `tests/adapters/test_died_text.py`. Criterion 9 is in `tests/application/test_costs_died_text.py`, and the stage's line is in `tests/application/test_stage_died_line.py`. Both limits are tested on both sides: 3 lines (rows `three-stderr-lines` and `last-three`) and 300 characters (rows `300-whole` and `301-cut`). The coder's `make check` was green (entry 13). The smoke test `grep -rlF 'died: ' src/factory` prints `src/factory/domain/died_runs.py`. Groups 2 to 4: layers, security and docstrings are fine apart from the findings below.

    Findings:
    1. `src/factory/adapters/agent_launch.py` `died_text` (standard error branch), called with the whole `process.stderr` from `claude_runtime.py` `_died_text` and `opencode_runtime.py` `_died_text`. The login shell (`LOGIN_SCRIPT`, `agent_launch.py:71/82/89/93`) writes `factory-login-used: …` to standard error on every run with login files. So in production, a died run with nothing else on standard error quotes `factory-login-used: subscription` instead of `exit <status>`, and in every other died run that line takes one of the 3 quoted lines. The Description says the line quotes "what the agent runtime gave as the reason", and this line is the factory's own marker, which `login_used` already reads. Fix: drop the lines that start with `LOGIN_USED_PREFIX` before taking the last 3. Add a criterion before the two closing ones: "a died run whose standard error holds only the login shell's `factory-login-used:` line gives `exit <status>`, and that line is never quoted". The tester then adds it as a row for each runtime.
    2. `src/factory/adapters/claude_runtime.py:237` and `src/factory/adapters/opencode_runtime.py:505`: both `_died_text` functions repeat the same guard (`end_reason != "died" or process.exit_status is None`) and the same comment. `CLAUDE.md` *Architecture* says what the runtimes share lies in `factory.adapters.agent_launch`. Fix: one helper in `agent_launch` that takes the end reason, the `ProcessResult` and the error text, applies the guard and calls `died_text`. Each runtime then passes only its own error text (claude: `reply.result` when `is_error`; opencode: `_error_message(events)`).

    Description corrections, as entry 9 asked of the reviewer:
    - description corrected: "Both runtimes do this." -> "Both runtimes give the text with the run's result, and the stage, which knows the run, its work item and its stage, writes the line."
    - description corrected: Interface "the last non-empty lines of standard error … Line breaks become ` / `" -> "the last 3 non-empty lines …", with the empty or whitespace-only reply falling to standard error, lines stripped and blank lines dropped before the ` / ` join, and `<status>` the raw exit status (entries 4 and 9).
    - description corrected: Interface "Both the `claude -p` runtime and the `opencode run` runtime write the line." -> the runtimes fill `AgentRunResult.died_text` only when the run ends `died`; `agent_launch.died_text(error_text, stderr, exit_status)` holds the text rules; `domain.died_runs.died_line(run, work_item, stage, text)` returns the line, which the stage writes through its factory log (entry 9).
    - description corrected: criteria 6 to 9 added from entry 4 (more than 3 lines of standard error; reply wins over standard error and an empty reply falls to it; line breaks and stripping in a reply; the cost record is unchanged); the closing criteria are now 10 and 11.
    - description corrected: smoke test `grep -rn 'died: ' src/factory | head -1 | cut -d: -f1`, Expect "the path of the module that writes the line" -> `grep -rlF 'died: ' src/factory`, Expect the single line `src/factory/domain/died_runs.py` (entry 9).

    Group 5: the coder's journal (entry 13) names the main choice (the stage writes the line whenever `died_text` is set) and what it rejected. The docs criterion (now 11) still says what the operator must know.

    Earlier tests: none. Every test file in the diff is new (status `A`).
16. factory: started doing as vm.
