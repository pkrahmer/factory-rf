---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 573
comments_read: [6670865186, 6670958330]
handed_over: null
claim: null
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-05T22:09:21.098293Z'
  stage: intake
  run: e4f95fe29d414628983fab6a841727b7
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-05T22:13:11.138299Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-05T22:13:13.808251Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-05T22:13:30.821812Z'
  stage: intake
  run: 2e242e9bacaf4333802d8ca9d8749c84
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T22:13:36.125816Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-05T22:14:22.493010Z'
  stage: tests
  run: e03f3375198742c7bf1055f83e5cb99e
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-05T22:16:12.185609Z'
  stage: tests
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

1. `agents/agents/intake.md` holds the routing rule of the Interface, naming `docs-only`, `tests` and the three documenter paths, with the "otherwise `tests`" clause and the statement that a docs-route story has no tests stage and no doing stage, so its criteria are about documents only.
2. `agents/agents/documenter.md` has a section for the stage `docs-only` that names `make documents`, ends with `docs-review`, or ends with `tests` when the story needs a change outside the documents, its entry then naming that change.
3. `agents/agents/reviewer.md` has a section for the stage `docs-review` that names the command `git diff main...HEAD -- README.md docs operator/README.md` and the work item, names `docs/project-guide/style.md`, ends with `docs-approval`, or with `docs-only` and numbered findings, and lists the seven style rules for as long as the style page is missing.
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
3. intake: Questions (the format check passed; the Interface, architecture and scope are fine, but the criteria leave Interface behaviours untested):

   1. The Interface says the documenter in `docs-only` runs `make documents`, but no criterion covers it. Criterion 2 mentions only the two decisions. Should criterion 2 also require that the section names `make documents`? I would add that.
   2. The Interface says the reviewer in `docs-review` reads `git diff main...HEAD -- README.md docs operator/README.md` and the work item, and that it judges facts against the code and the criteria. No criterion covers any of this. Should criterion 3 require that the section names that diff command and the work item? I would add that.
   3. The Interface says the reviewer ends with `docs-only` and numbered findings. Criterion 3 requires `docs-only` but not the numbered findings. Should criterion 3 require that the section says the findings are numbered? I would add that.
   4. Intake rule: criterion 1 only requires that `docs-only`, `tests` and the three paths are named. The "otherwise `tests`" side (any path outside the documenter's paths) and the sentence "a story on the docs route has no tests stage and no doing stage, so its criteria are about documents only" are not required. Should criterion 1 require the "otherwise `tests`" clause and the statement that docs-route criteria are about documents only? I would add both.
   5. The documenter's section says that when it ends with `tests`, its entry names the change so the tester and coder see why. Criterion 2 says "the change it needs", which is close, but it should say the entry names that change. I would reword it that way.
4. 2026-11-05 human: Yes to all five, as you propose: (1) criterion 2 names `make documents`; (2) criterion 3 names the diff command and the work item; (3) criterion 3 says the findings are numbered; (4) criterion 1 requires the "otherwise `tests`" clause and that docs-route criteria are about documents only; (5) criterion 2 says the entry names that change.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: concrete files and sections (intake.md stage section, documenter.md `docs-only`, reviewer.md `docs-review`) and the new test module `tests/agent_files/test_claude_agent_texts_docs_route.py`; no signatures needed.
   - Criteria: carried in the human's answer (journal 4, all five points) into criteria 1 to 3: the "otherwise `tests`" clause and the documents-only statement, `make documents`, the entry naming the outside change, the diff command and work item, and numbered findings. Each is now checkable by one test, and each rule has both sides (`docs-only` vs `tests`; `docs-review` vs `tests` for the documenter; `docs-approval` vs `docs-only` for the reviewer).
   - Smoke test: the grep/awk command is runnable and `named` is checkable.
   - Architecture: only agent text files and tests under `tests/agent_files/`; no runtime change, matches CLAUDE.md.
   - Scope: within F0052 scope (S0002), touches nothing in Out of scope; the pipeline.yml change is the human's at merge.
7. factory: started tests as vm.
8. tester: Questions before writing `tests/agent_files/test_claude_agent_texts_docs_route.py`. No test files are written yet. Criterion 1 is clear: the test checks the Interface's quoted routing rule word for word, exactly once, in the `## Stage` section of `agents/agents/intake.md`.

   1. What form does "a section for the stage `docs-only`" (criterion 2) and "for the stage `docs-review`" (criterion 3) take? `tests/agent_files/test_claude_agent_texts.py::test_body_has_rules_role_stage_and_lessons_sections_in_order` pins every shipped agent's `## ` headings to exactly Rules, Role, Stage, Lessons. So a new `## docs-only` heading would turn that test red, and the coder may not change it. Options:
      (a) a `### docs-only` subsection inside `## Stage` of `documenter.md`, and a `### docs-review` subsection inside `## Stage` of `reviewer.md`. The test reads the text from that heading to the next heading.
      (b) a paragraph inside `## Stage` that opens with "In `docs-only`:" or "In `docs-review`:". The test reads that paragraph.
      (c) a new `## ` heading, with your leave to change the heading-order test.
      I would choose (a).

   2. "Lists the seven style rules" (criterion 3): I may not read `feature.md`, and the work item doesn't give the seven rules. Options:
      (a) you add the seven one-line rules, word for word, to the Interface. The test checks that each appears exactly once in the `docs-review` section.
      (b) the test checks only the shape: a numbered list of exactly seven items (rows for 6, 7 and 8) in that section, after a sentence naming `docs/project-guide/style.md`.
      (c) the rules stay untested.
      I would choose (a).

   3. "For as long as the style page is missing": `docs/project-guide/style.md` doesn't exist yet. Options:
      (a) the test checks the seven rules unconditionally, and S0003 changes this test, with your leave, when it adds the page.
      (b) the test checks them only while the page is missing.
      I would choose (a).
9. 2026-11-05 human: 1. (a): a `### docs-only` subsection in `## Stage` of `documenter.md`, and a `### docs-review` subsection in `## Stage` of `reviewer.md`; the test reads from that heading to the next.

   2. (a), with the rules given here; this answer stands as the Interface's list. The seven rules, one line each, word for word:
      1. Write for a reader without the history: no feature or story IDs, no version names.
      2. One idea per sentence, at most about 25 words, at most one parenthesis.
      3. Explain each factory word once, in the glossary.
      4. What to do comes first, the details after.
      5. Round numbers.
      6. Examples are real and were run.
      7. Only the current truth.
      The test checks that each appears exactly once in the `docs-review` subsection.

   3. (a), but without a later change: the test checks the seven rules unconditionally. S0003 takes the docs route and changes no agent file and no test, so the list stays in `reviewer.md` as the fallback the section names ("until `docs/project-guide/style.md` exists"), and the test stays green.
