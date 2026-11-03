---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 514
comments_read: [6598577655]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-03T08:10:17.786100Z'
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
---

# A run that dies leaves its error text in the factory log

<!-- written by the human on 2026-11-03 after two runs at the subscription's limit ended as died (decision 19) -->

## Description

A run ends as `died` when the agent's process exits non-zero, gives no reply, or gives an error reply that is not a provider limit. The cost record then says `died` and nothing more, and the factory log has no line for it. On 2026-11-02 two documenter runs of S0008 met the subscription's usage limit. The provider-limit rule (`FACTORY_PROVIDER_LIMIT_MESSAGE`) did not match the text they saw, so they ended as `died`, and because nothing kept the text, nobody can learn what the pattern must match. The same holds for every other cause of a `died` run.

This story makes a `died` run leave its error text behind: one line in the factory log that names the run and quotes what the agent runtime gave as the reason. The text is the error reply's text when there is one, otherwise the last lines of standard error, otherwise the process's exit status alone. It is cut to a short length and put on one line. The agent's own answer text is never quoted, as the provider-limit rule never searches it. Both runtimes do this. Nothing else about how a run ends, is retried or is recorded changes.

## Interface

- When a run ends with `end_reason` `died`, the factory log gets one line: `run <run id> of <work item> (<stage>) died: <text>`.
- `<text>` is, in this order of preference: the error reply's result text; the last non-empty lines of standard error; `exit <status>`. Line breaks become ` / `, and the text is cut to its first 300 characters, with `…` at the end when it was cut.
- The agent's own reply text (a reply that is not an error) is never quoted.
- The cost record and its contract stay unchanged.
- Both the `claude -p` runtime and the `opencode run` runtime write the line.

## Acceptance criteria

1. A `died` run of the fake process with an error reply whose result is `You've hit your limit · resets 12am` writes the line `run <id> of <work item> (<stage>) died: You've hit your limit · resets 12am`. Rows: each runtime.
2. A `died` run without a reply and with three lines on standard error writes those lines joined by ` / `; one without a reply and with empty standard error writes `exit <status>`. Rows: each case and each runtime.
3. A text of 301 characters is cut to 300 and ends with `…`; a text of exactly 300 characters is written whole. Rows of one test.
4. A run that ends `completed`, `no_result`, `budget`, `time_limit` or `provider_limit` writes no such line. Rows: each end reason.
5. A run whose reply is not an error but whose process exits non-zero does not quote the reply's text.
6. `make check` stays green.
7. docs: `docs/operator-guide.md`, where it describes a run that ends as `died` and the provider-limit rule: one paragraph saying that the factory log names the died run and quotes its error text, and that this text is what `FACTORY_PROVIDER_LIMIT_MESSAGE` must match when a provider's limit is the cause. `docs/decisions.md`, `README.md` and the project guide: none.

## Smoke test

```bash
grep -rn 'died: ' src/factory | head -1 | cut -d: -f1
```

Expect: the path of the module that writes the line.

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
