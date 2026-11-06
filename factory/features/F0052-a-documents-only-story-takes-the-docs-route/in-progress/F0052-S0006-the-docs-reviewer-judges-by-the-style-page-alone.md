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
  started_at: '2026-11-06T00:50:47.404242Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T00:50:47.397675Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T00:50:47.404242Z'
  stage: intake
---

# The docs reviewer judges by the style page alone

## Description

The reviewer's `### docs-review` subsection in `agents/agents/reviewer.md` says, in its step 3, to judge the writing against `docs/project-guide/style.md` and, "until `docs/project-guide/style.md` exists", against seven rules it lists word for word. The page has existed since the style page story, so the fallback is dead text. It is also out of step with the page: the page has eight rules (rule 8, relative links) and a section for each kind of document, and the list has seven, in other words. A reviewer that reads both may judge by the shorter list. This story drops the fallback, so step 3 names the style page as the one source of the rules. The other steps of the subsection, the documenter's `### docs-only` subsection and the rest of `reviewer.md` stay as they are. The project guide's sentence on the fallback goes with it. The operator guide's "once it exists" in *The docs route* is left to the rewrite of that page in the next feature.

## Interface

- `agents/agents/reviewer.md`, `## Stage`, `### docs-review`, step 3: becomes the one sentence `Judge the writing against \`docs/project-guide/style.md\`: its rules for all documents and the section for the kind of document the diff changes.` The words `until` and the seven-item list under it go. Steps 1, 2 and 4 are unchanged. The rest of the body is unchanged, so `tests/agent_files/test_claude_agent_texts_review_groups.py::test_the_rest_of_the_reviewer_body_is_unchanged`, which leaves this subsection out, stays green unchanged.
- `tests/agent_files/test_claude_agent_texts_docs_route.py`, an earlier story's test: `STYLE_RULES` and `test_the_reviewer_in_docs_review_lists_each_style_rule_once` go, and one test is added in their place, named in the criteria. Nothing else in the module changes. Feature decision 8 gives the leave.

## Acceptance criteria

1. The `### docs-review` subsection of the shipped `reviewer.md` holds the sentence of the Interface exactly once, and holds neither the word `until` nor any of the seven old rules (`Write for a reader without the history: no feature or story IDs, no version names.` to `Only the current truth.`). One parametrized test: one row for the sentence (count 1) and one row for each of the seven old rules and for `until` (count 0).
2. The `### docs-review` subsection still names `docs/project-guide/style.md`, `docs-approval`, `docs-only` and the documents diff command: the existing rows of `test_the_reviewer_in_docs_review_reads_the_documents_diff_and_approves_or_sends_back` stay green unchanged.
3. `make check` stays green.
4. docs: `docs/project-guide/agents.md`, *The docs route*: the sentence "Until the style page exists, the reviewer's subsection lists the seven style rules itself." goes, and the paragraph says that the reviewer on `docs-review` judges the writing against the style page. `docs/decisions.md`: none, because the fallback was a stopgap, not a decision. `docs/operator-guide/`: none, left to the rewrite of `pipeline.md`.

## Smoke test

```bash
sed -n '/^### docs-review/,/^## /p' agents/agents/reviewer.md | grep -c "until \`docs/project-guide/style.md\` exists\|Only the current truth\."
```
Expect: `0`

```bash
sed -n '/^### docs-review/,/^## /p' agents/agents/reviewer.md | grep -c "Judge the writing against \`docs/project-guide/style.md\`: its rules for all documents and the section for the kind of document the diff changes."
```
Expect: `1`

```bash
uv run pytest tests/agent_files/test_claude_agent_texts_docs_route.py tests/agent_files/test_claude_agent_texts_review_groups.py 2>&1 | tail -1 | grep -c " passed"
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
