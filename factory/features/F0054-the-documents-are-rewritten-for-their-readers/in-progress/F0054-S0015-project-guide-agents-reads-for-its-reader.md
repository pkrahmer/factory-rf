---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 623
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T04:20:27.799744Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T04:12:31.267176Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T04:12:31.274946Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T04:12:45.946559Z'
  stage: intake
  run: f9c96d4ca24f45e6a60fd82371ed819b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T04:12:50.736910Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T04:20:22.931582Z'
  stage: docs-only
  run: 5c566db6360b4027b5dcf3c149fc0cba
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T04:20:27.799744Z'
  stage: docs-review
---

# The project guide's page on the agents area reads for the developer

## Description

`docs/project-guide/agents.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/agents.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/agents.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/agents.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/agents.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/agents.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/agents.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only (`docs/project-guide/agents.md`, `docs/checked-documents.txt` with its one line), and says no code, test or agent file changes. Every path it changes is one the documenter may write.
   - Criteria: on the docs route there are no tests, so criteria 1 and 2 are judged by the reviewer against `docs/project-guide/style.md` and the code. Criteria 3 to 5 are checked by `make documents` (`documents ok`, no broken link) and by the link rule. Criterion 6 is `make check`. The failing side is covered: a dropped fact, a broken link and a missing checked-list entry each fail a criterion.
   - Smoke test: `grep -cx "docs/project-guide/agents.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked against its output. It does not run pytest.
   - Docs criterion (7): says docs are as criteria 1 to 5 and `docs/decisions.md` is unchanged. It names what the reader must know and dictates no sentences.
   - Architecture: a documents-only change to the project guide's page on the agents area. It touches nothing in `factory/`, `src/` or `tests/`, and the story does not use the `.claude/` or `planning/` paths.
   - Scope: within F0054's scope (S0015 is listed, one file per story). It touches nothing in the feature's out-of-scope list (`decisions.md`, `docs/runs/`, the operator playbook, behaviour changes).

   Route: docs-only.
4. factory: started docs-only as vm.
5. documenter: Changed files:
   - `docs/project-guide/agents.md`: rewritten for its reader in the style of `docs/project-guide/style.md`.
     - Each section now opens with the idea in two or three sentences, then a block of names and signatures, then one rule per bullet, then See also.
     - Exact detail moved into a *Reference* section at the end. It has nine parts: request and result, the login shell, the `claude` call, a resumed run, the opencode call, the opencode configuration (including the result block, provider file and lockdown switches).
     - Modules are linked once, by relative links.
     - The section heading *The agent definition reader* is kept, because `work.md` links to it.
     - I read the code to check these names and facts: `agent_launch.py`, the `AgentRuntime` and `AgentDefinitionReader` interfaces, `PROTECTED_PATHS`, the seven agent files' front matter, `agents/settings.json` and the template folder.
     - One fact I corrected: `AgentRuntime` also has `tool_uses(transcript)`, which the old page left out. It is now listed.
     - The `.claude`, `agents` and path examples that `make documents` flagged as missing files are now runnable `console` blocks. They also use the `<project>/factory/agents/` placeholder.
     - The old `bash` example for the agent reader is now a `console` example. It prints the last line of the error and uses `<message>` for the part of the error text that varies.
   - `docs/checked-documents.txt`: added the line `docs/project-guide/agents.md`.

   Removed on purpose, because the style page forbids history (rule 1 and rule 7):
   - The two sections *Replaced in v1.2*.
   - The v1-to-v1.1 rename table *Replaced from v1*. The renamed words stay in the text as the current vocabulary.
   - Story and feature IDs (F00xx-S00xx) and "v1 / v1.1 / v1.2" provenance sentences, including "the texts come from v1 at commit f8bc9d2 so the baseline run compares". That sentence gave a reason, not a fact about the current code. The reviewer should confirm whether a line in `docs/decisions.md` should hold it; I wrote nothing there, since the story says `decisions.md` is untouched.
   - The remark that `FINISH_MESSAGE` asks for `question` "where v1 asked for `stuck`" is now "`question`, not a decision named `stuck`".
   - The remark "(a later story)" on waiting out a provider limit is now "until the application layer waits the limit out".
   - The sentence about the tiny story of 2026-10-18 (`.costs.jsonl` and `make secrets`) is shortened to the standing reason.

   Checks:
   - `make documents` ends with `documents ok (13.1 s)`.
   - I did not run `make check`: every changed file is a document, and the factory runs the checks after this stage.

   Cross-read:
   - `work.md` links to the heading *The agent definition reader*, and that heading still exists.
   - A grep for `agents.md#` found no other link into this page.

   Stale text I noticed and did not touch:
   - `docs/project-guide/README.md` and `docs/project-guide/machine.md` give "does not exist" findings in the unchecked-documents report. They are outside this story.
   - I could not check the correctness of every sentence moved verbatim into the Reference against the code. The reviewer should compare `claude_runtime.py` and `opencode_runtime.py` against the Reference.

   `check`: check: green
   `secrets`: secrets: green (0.5 s)
   `documents`: documents ok (13.3 s)
6. factory: started docs-review as vm.
