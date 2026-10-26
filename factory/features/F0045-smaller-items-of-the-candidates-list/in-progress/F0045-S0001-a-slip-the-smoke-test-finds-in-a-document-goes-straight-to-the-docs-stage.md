---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 466
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T18:32:18.656094Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T18:32:18.662234Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-26T18:32:42.714680Z'
  stage: intake
  run: 8b48783db0ae4f6f8ebe887c8146bbd6
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-26T18:33:03.252271Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-26T18:39:23.392862Z'
  stage: tests
  run: cee8c926e26041eabab92fd0dad1c867
---

# A slip the smoke test finds in a document goes straight to the docs stage

## Description

When the smoke tester finds that a document says something the code does not (an `Expect:` that reads `README.md` or a file under `docs/` and finds a wrong sentence, or a `docs:` criterion the documents do not meet), it can only end with `doing` today. The coder may not write `docs/`, so the coder hands on to review, the reviewer to docs, and the documenter fixes the sentence before the smoke test runs again: four extra runs each in F0038-S0007 and S0009 (F0038-A0001, note 8). The decision rules already count every `next` entry after the first as a rework against the stage's `round_cap`, so the short way needs no code: the human's change 1 of `feature.md` adds `docs` to the smoke test's `next` in `factory/pipeline.yml` and the demo's definition, and this story adds it to `template/factory/pipeline.yml` and teaches the agents: the smoke tester ends with `docs` when every finding is such a slip and the code does what the work item says, and with `doing` otherwise; the documenter, on such a round, fixes exactly those findings and ends with `smoke-test`; R12, the rule on rework rounds that every shipped agent carries, names the new rework (decision 6 of `feature.md`). What stays: every other stage's `next`, the round cap and its count, the smoke tester's other steps, and every decision of the other agents.

## Interface

No module under `src/factory/` changes.

`template/factory/pipeline.yml`: the line of the stage `smoke-test` becomes (two spaces of indentation, the round cap unchanged):

```yaml
  smoke-test: {role: smoke-tester, next: [approval, doing, docs], round_cap: 3}
```

`claude/agents/*.md` (the seven shipped agents): in the line that begins `R12.`, the words `smoke-test → doing,` become `smoke-test → doing, smoke-test → docs,`; nothing else of the line changes, so it reads, word for word:

> R12. Rework rounds (review → doing, docs → doing, smoke-test → doing, smoke-test → docs, and the human's close at the approval) share the work item's `round`, capped by the stage's `round_cap` in the pipeline definition. Your prompt names the round; on a rework round the latest entries name the findings. When the cap is passed, the factory asks the human instead of looping.

`claude/agents/smoke-tester.md`, `## Stage`: step 5 becomes these two steps, word for word, and the steps after them are numbered on:

> 5. Findings that are each a slip in a document the documenter writes (`README.md` or a file under `docs/`: the command read that document and found a sentence the code contradicts, or the contradicted criterion is the `docs:` criterion), while the code does what the work item says: add them as a numbered list (command, expected, observed, criterion if any) and end with `docs`.
> 6. Any other findings: add them as a numbered list (command, expected, observed, criterion if any) and end with `doing`. When some findings are slips in a document and others are not, all of them go to `doing`.

`claude/agents/documenter.md`, `## Stage`: step 1 gains, after its last sentence, word for word:

> When the latest entry is the smoke tester's and it ended with `docs`, its numbered findings are slips in the documents: fix exactly those, run the commands they name again, and end with `smoke-test`.

Rules:

- The template's definition loads with the shipped roles, and its smoke test's `next` is exactly `approval`, `doing`, `docs`, in that order (`approval` stays the forward decision).
- Every shipped agent names every decision of its stage's `next` in the template, in inline code (the existing rule of `tests/test_claude_agent_texts.py`).

Tests (the tester writes them): new tests at the tester's choice, for example `tests/test_claude_agent_texts_docs_slip.py`, reading the shipped agents through `tests/shipped_agents.py` and the template through `RuamelPipelineDefinitionReader`, and one test of the decision rules in `tests/domain/`, for example `tests/domain/test_decide_docs_slip.py`. No earlier test changes (decision 21 of `feature.md`).

## Acceptance criteria

1. The template (one test): `template/factory/pipeline.yml` parses with `RuamelPipelineDefinitionReader`, and its stage `smoke-test` has `next == ["approval", "doing", "docs"]` and `round_cap == 3`; every other stage's `next` equals what it is on `main` before this story (`intake` `[tests]`, `tests` `[doing]`, `doing` `[review, tests]`, `review` `[docs, doing]`, `docs` `[smoke-test, doing]`, `acceptance` `[approval]`, `approval` `[done, doing]`).
2. R12 (rows of one parametrized test over the seven files under `claude/agents/`): each holds the R12 line of the Interface exactly once, and none holds the old line (the same text without `smoke-test → docs, `).
3. The smoke tester's text (rows of one parametrized test over `claude/agents/smoke-tester.md`, `## Stage`): it holds step 5 and step 6 of the Interface word for word, step 5 before step 6; it holds `` end with `docs` `` exactly once and `` end with `approval` `` once; the old sentence `Findings: add them as a numbered list (command, expected, observed, criterion if any) and end with `doing`.` is gone.
4. The documenter's text (one test over `claude/agents/documenter.md`, `## Stage`): step 1 ends with the sentence of the Interface, word for word, and `` end with `smoke-test` `` appears in it.
5. The decision rules take the short way (rows of one parametrized test over `factory.domain.decisions.decide` with the template's definition and a work item state at `smoke-test`): round 0 and decision `docs` moves to `docs` with round 1 (rule 3); round 2 and decision `docs` moves to `docs` with round 3 (at the cap of 3); round 3 and decision `docs` stays at `smoke-test`, blocked `round_cap`, round 4 (rule 4, the cap passed, as for `doing`); round 0 and decision `doing` moves to `doing` with round 1; decision `approval` moves to `approval` with the round unchanged; decision `review` raises `ValueError` (not in `next`).
6. `make check` stays green.
7. docs: `docs/operator-guide.md`, `## The pipeline definition`: the smoke test's line and one sentence that a slip only in a document goes from the smoke test to `docs` and counts as a rework round; `## The agent files`, *The shipped agents and settings*: the smoke tester's two ways out. `docs/project-guide/agents.md`, `## The shipped agents, settings and template`: the template's smoke test `next` and R12's new rework. `docs/decisions.md`: a new entry "A slip the smoke test finds in a document goes straight to the docs stage" (F0045-S0001; F0038-A0001's note 8, the four extra runs, decision 6 of `feature.md` with its rejected options). `README.md`: none (nothing a newcomer runs changes).

## Smoke test

```bash
uv run python - <<'EOF'
from pathlib import Path
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
text = Path("template/factory/pipeline.yml").read_text(encoding="utf-8")
print(RuamelPipelineDefinitionReader().parse(text).stages["smoke-test"].next)
EOF
```
Expect: `['approval', 'doing', 'docs']`

```bash
grep -l 'smoke-test → doing, smoke-test → docs, and' claude/agents/*.md | wc -l; grep -c 'end with `docs`' claude/agents/smoke-tester.md
```
Expect: two lines: `7`; `1`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: concrete. It names the exact template line, the R12 line word for word (the current line exists once in each of the seven agents, checked), smoke-tester steps 5 and 6 (the current step 5 is the old sentence), and the documenter's step 1 addition. No `src/` module changes.
   - Criteria: each is testable by one test function or one parametrized table. 1 covers the template's `next` and `round_cap` and every other stage. 2 to 4 cover the texts, with the old text gone. 5 covers `decide` on both sides: the cap passed, `doing`, `approval`, and `review` refused with `ValueError`. The Interface rules are covered. `make check` and `docs:` are last.
   - Smoke test: both commands are runnable from the repository root. No pytest command is used, so the `-q` check does not apply. Each `Expect:` is checkable: the printed list, and the two counts `7` and `1`. Today the template shows `['approval', 'doing']` and the count is 0, so both commands fail before the story is built and should pass after it.
   - Architecture: the change is only in `template/`, `claude/agents/` and tests, inside the coder's and tester's write paths. No layer or interface is touched.
   - Scope: this is S0001 of F0045, as decision 6 and the human's change 1 describe. `factory/pipeline.yml` already has `docs` in the smoke test's `next`. No earlier test changes, per decision 21.
4. factory: started tests as vm.
5. tester: Tests written from the acceptance criteria. They are red on purpose: the template, the R12 line and the agents' steps have not changed yet.

   - criterion 1: tests/test_claude_agent_texts_docs_slip.py::test_the_template_lets_the_smoke_test_hand_a_slip_to_docs_and_keeps_every_other_next
   - criterion 2: tests/test_claude_agent_texts_docs_slip.py::test_every_shipped_agent_names_the_smoke_test_to_docs_rework (one row per shipped agent from `SHIPPED_NAMES`)
   - criterion 3: tests/test_claude_agent_texts_docs_slip.py::test_the_smoke_tester_ends_with_docs_only_for_slips_in_a_document (rows: slip-step, other-findings-step, slip-step-first, docs-once, approval-once, old-step-gone; all read from the `## Stage` section)
   - criterion 4: tests/test_claude_agent_texts_docs_slip.py::test_the_documenter_fixes_the_slips_of_the_smoke_test_and_hands_back_to_it (the one `1. ` line of `## Stage` ends with the sentence and holds `end with `smoke-test``)
   - criterion 5: tests/domain/test_decide_docs_slip.py::test_the_smoke_test_sends_a_slip_in_a_document_to_docs_as_a_rework (rows: docs at round 0 → docs round 1; docs at round 2 → docs round 3; docs at round 3 → stays at smoke-test, blocked round_cap, round 4, question `round_cap_question(4, 3)`; doing at round 0 → doing round 1; approval at round 2 → approval round 2; review → ValueError)
   - criteria 6 and 7: `make check` and docs, nothing to test.

   Files created: tests/test_claude_agent_texts_docs_slip.py, tests/domain/test_decide_docs_slip.py. No earlier test changed.

   Both files read the template through `RuamelPipelineDefinitionReader`. The text tests read the agents through `tests/shipped_agents.py` and `section_text`. In criterion 1 the expected `next` of the other stages includes `done: []`, which is what `main` holds.

   No module failed to import. `make test` shows these failures:
   - the template test, the 7 R12 rows and 5 of the 6 smoke-tester rows: the texts and the template are not changed yet. The `approval-once` row already passes.
   - the documenter test.
   - the three `docs` rows of the decision test, each with `ValueError: decision 'docs' is not allowed at stage 'smoke-test'`, because the template's smoke test does not list `docs` yet.

   `make lint` is green.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/domain/test_decide_docs_slip.py::test_the_smoke_test_sends_a_slip_in_a_document_to_docs_as_a_rework[docs-past-the-cap] - ValueError: decision 'docs' is not allowed at stage 'smoke-test'
