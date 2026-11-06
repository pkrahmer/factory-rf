# The agents write and review documents against the code

## Description

The checks catch names, settings and examples; the rest of a document's truth depends on how the agents work. Today a documenter writes from the story and the old text, and a reviewer reads the diff of the code, not the documents. This story changes their instructions: the documenter reads the code it describes before it writes a sentence about it, writes every command it shows as a runnable example (or marks it for the VM, GitHub or a model, and then copies it from a real run and says where it ran), runs `make documents`, and keeps exact detail in a *Reference* section rather than cutting it. The reviewer reads the changed documents against the code, and counts a claim it cannot find in the code, and a command shown without a runnable or marked example, as findings. The style rules of `planning/doc-style-drafts.md` (rules 8 to 10) become theirs.

## Interface

- `agents/agents/documenter.md`: one rule each for: read the code first; examples are runnable, or marked and copied from a real run that the text names; keep detail in *Reference*; run `make documents` and end only on `documents ok`.
- `agents/agents/reviewer.md`: in its checklist, an item *Documents*: the changed documents' claims against the code, and examples runnable or marked; a failure is a finding.
- `agents/agents/intake.md`: a docs criterion that dictates sentences is a question; it should name what the reader must know.
- Tests of the agent texts: `tests/agent_files/test_claude_agent_texts_documents.py`, one row per rule. The human's leave (2026-11-05): the tester may change the earlier tests that pin an agent file's whole text (such as `test_the_rest_of_the_reviewer_body_is_unchanged` in `tests/agent_files/test_claude_agent_texts_review_groups.py`) so that they leave out the new rules' lines, as F0052-S0002 did for its `### docs-review` subsection; each keeps its name and pins the rest as before.

## Acceptance criteria

1. `agents/agents/documenter.md` holds the four rules of the Interface.
2. `agents/agents/reviewer.md` holds the *Documents* item, naming the claims against the code and the examples.
3. `agents/agents/intake.md` holds the rule on a docs criterion that dictates sentences, .
4. `make check` stays green.
5. docs: `docs/project-guide/agents.md`: how the documenter and the reviewer treat documents. `docs/decisions.md`: an entry, naming F0053 and the human's concern of 2026-11-05 that the stages' documents were not reliably true.

## Smoke test

```bash
grep -c "make documents" agents/agents/documenter.md | awk '{print ($1 >= 1) ? "named" : "missing"}'
```
Expect: `named`

## Journal
