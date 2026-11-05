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
  started_at: '2026-11-05T22:09:03.847414Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T22:09:03.840313Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T22:09:03.847414Z'
  stage: intake
---

# The agents know the docs route

## Description

Once the pipeline holds the docs route (the human adds it at this story's merge), three agents must know when and how to use it. The intake sends a story down it when every path its Interface changes is one the documenter may write (feature decision 4). The documenter in `docs-only` writes the whole change and ends with `docs-review`. When it finds that the story needs a change outside the documents, it ends with `tests` instead, naming the change, and the story takes the code route from there (feature decision 6). The reviewer in `docs-review` reads the finished documents against the docs criterion and the style page (`docs/project-guide/style.md`, written by S0003; until it exists, against the rules the stage section lists), and ends with `docs-approval` or sends the text back with `docs-only` and its findings. The agents' other stages do not change.

## Interface

- `agents/agents/intake.md`, its stage section: one rule: "Choose `docs-only` when every path the Interface changes is one the documenter may write (`README.md`, `docs/*`, `operator/README.md`); otherwise `tests`. A story on the docs route has no tests stage and no doing stage, so its criteria are about documents only."
- `agents/agents/documenter.md`: a stage section for `docs-only`: it does the whole change of the story, as its docs criterion says; it runs `make documents`; it ends with `docs-review`; when the story needs a change outside the documents, it ends with `tests` and its entry names that change, so the tester and the coder see why the story came to them.
- `agents/agents/reviewer.md`: a stage section for `docs-review`: it reads `git diff main...HEAD -- README.md docs operator/README.md` and the work item; it judges the facts against the code and the criteria, and the writing against `docs/project-guide/style.md` (when it exists) or, until then, the seven rules of the feature's style draft, which the section lists in one line each; it ends with `docs-approval`, or with `docs-only` and numbered findings.
- Tests of the agent texts: `tests/agent_files/test_claude_agent_texts_docs_route.py` (new), one row per rule above, reading the shipped files as the other `test_claude_agent_texts_*` modules do.
- The opencode runtime reads the same files; no runtime change.

## Acceptance criteria

1. `agents/agents/intake.md` holds the routing rule of the Interface, naming `docs-only`, `tests` and the three documenter paths.
2. `agents/agents/documenter.md` has a section for the stage `docs-only` that ends with `docs-review`, or with `tests` and the change it needs when the story needs a change outside the documents.
3. `agents/agents/reviewer.md` has a section for the stage `docs-review` that names `docs/project-guide/style.md`, ends with `docs-approval` or `docs-only`, and lists the seven style rules for as long as the style page is missing.
4. `make check` stays green.
5. docs: `docs/project-guide/agents.md`: the docs route and which agent does what on it. `docs/operator-guide/pipeline.md`: the route in the operator's words. `docs/decisions.md`: an entry for feature decisions 1 to 6, naming F0052.

## Smoke test

```bash
grep -c "docs-only" agents/agents/intake.md agents/agents/documenter.md agents/agents/reviewer.md | awk -F: '$2 < 1 {bad=1} END {print bad ? "missing" : "named"}'
```
Expect: `named`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
