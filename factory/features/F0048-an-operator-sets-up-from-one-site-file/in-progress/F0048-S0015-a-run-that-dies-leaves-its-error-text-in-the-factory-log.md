---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-03T08:05:18.433430Z'
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
