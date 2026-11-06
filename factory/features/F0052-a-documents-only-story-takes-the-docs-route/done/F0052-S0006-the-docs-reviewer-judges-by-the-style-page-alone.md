---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 579
comments_read: []
handed_over: approval
claim: null
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
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T00:51:03.971598Z'
  stage: intake
  run: 71ab526ab9ea4ca589b70a3b8a26b860
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T00:51:08.875378Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-06T00:51:39.983695Z'
  stage: tests
  run: 37566ac325c54748a8e0d5d515e45fdb
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T00:51:45.056456Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-06T00:57:13.444224Z'
  stage: doing
  run: 301fbff40ff44ac19f75cbda996f556e
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T00:57:18.722456Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-06T00:57:45.700080Z'
  stage: review
  run: b631747d208f467db9186b5dd366ff75
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T00:57:50.877536Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-11-06T00:58:10.384031Z'
  stage: docs
  run: d3a15cb39f2b49669fb626a4fb4245e8
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T00:58:15.898779Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-11-06T00:58:41.504594Z'
  stage: smoke-test
  run: de69386ca5e54eafb3fe7b493fa7f3f8
- number: 14
  speaker: factory
  kind: done
  at: '2026-11-06T01:02:34.663475Z'
  stage: approval
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
3. intake: accepted
   - Interface: it names the concrete file `agents/agents/reviewer.md`, `### docs-review` step 3, with the exact replacement sentence. It also names the test module `tests/agent_files/test_claude_agent_texts_docs_route.py` with what goes (`STYLE_RULES`, `test_the_reviewer_in_docs_review_lists_each_style_rule_once`) and what is added. Feature decision 8 gives the leave for that test change.
   - Criteria: criterion 1 is one parametrized test, with one row for the sentence (count 1) and rows with count 0 for `until` and each of the seven old rules. Criterion 2 points at the existing rows of the docs-review test, which stay green. The `make check` and `docs:` criteria close the list. The only rule is the removal, and it has both sides: the sentence present, and the old text absent.
   - Smoke test: the three commands are runnable. The pytest command adds no `-q`, and `addopts` in `pyproject.toml` already sets `-q`, so the last line is the summary line that `grep -c " passed"` counts. Each `Expect:` line is a count that can be checked.
   - Architecture: the change touches agent text and a test under `tests/agent_files/`, which is where agent file tests belong. It adds no code and no layer.
   - Scope: the story falls within F0052's goal and decision 8. It touches nothing in "Out of scope". The operator guide is explicitly left to the next feature.
   Route: `tests`. `agents/agents/reviewer.md` is not a path the documenter may write.
4. factory: started tests as vm.
5. tester: I wrote the test for criterion 1 and changed the earlier docs-route test module as the Interface says. Feature decision 8 gives the leave for that change.

   Criterion → test:
   - criterion 1: `tests/agent_files/test_claude_agent_texts_docs_route.py::test_the_reviewer_in_docs_review_judges_the_writing_by_the_style_page_alone`. It is one parametrized test with nine rows. The Interface sentence has count 1 (`style-page-sentence`). `until` and each of the seven old rules have count 0 (`no-until`, `no-old-rule-*`). The old rules are written into the rows themselves, because `STYLE_RULES` goes.
   - criterion 2: `tests/agent_files/test_claude_agent_texts_docs_route.py::test_the_reviewer_in_docs_review_reads_the_documents_diff_and_approves_or_sends_back`. This is the existing test with its rows unchanged; I did not touch it.
   - criterion 3: no test; the factory's `make check` covers it.
   - criterion 4 (docs): no test; it is the documenter's.

   Files: I created none. I changed the earlier story's test module `tests/agent_files/test_claude_agent_texts_docs_route.py`:
   - I removed `STYLE_RULES` and `test_the_reviewer_in_docs_review_lists_each_style_rule_once`.
   - I added `STYLE_PAGE_SENTENCE` and the new test in their place.
   - Nothing else in the module changed.

   Run: `uv run pytest -q` over the module shows 9 failed rows, all in the new test. The current `reviewer.md` still has the "until … exists" fallback and the seven rules, and lacks the new sentence: that is a wrong result, the right reason to fail. All the other tests in the module pass. Every module imported; there were no import errors. `make lint` is green.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: I rewrote step 3 of `### docs-review` in `agents/agents/reviewer.md`. It is now the one sentence from the Interface: "Judge the writing against `docs/project-guide/style.md`: its rules for all documents and the section for the kind of document the diff changes." The fallback clause ("until … exists") and the seven-item list under it are gone. Steps 1, 2 and 4 and the rest of the file are unchanged. That is the whole diff: one line added, eight removed. I changed no tests.

   Main choice: I replaced the step in place and kept its number 3, so steps 1, 2 and 4 keep theirs. The alternative I rejected was folding the style page into step 2. That would have changed the numbering and the existing subsection that the rest-of-body test excludes, beyond what the Interface asks.

   Refactor: nothing to change; the diff is the one sentence.

   `make check`: green (test: green (141.2 s), check: green).

   Noticed but not touched: `docs/project-guide/agents.md:295` still says "Until the style page exists, the reviewer's subsection lists the seven style rules itself." Criterion 4 gives that change to the documenter. The journal changed nothing in the Description.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 40 known, 3 gone
8. factory: started review as vm.
9. reviewer: no findings

   What I checked:
   - Group 1, criteria: the diff covers criterion 1 with `tests/agent_files/test_claude_agent_texts_docs_route.py::test_the_reviewer_in_docs_review_judges_the_writing_by_the_style_page_alone`. It is one parametrized test with nine rows. The Interface sentence must appear exactly once. `until` and each of the seven old rules, written out in full, must appear zero times. The story's only rule is a removal, and the test checks both sides of it. For criterion 2, `test_the_reviewer_in_docs_review_reads_the_documents_diff_and_approves_or_sends_back` is unchanged in the diff. The new step 3 still names `docs/project-guide/style.md`, and steps 1 and 4 still hold the documents diff command, `docs-approval` and `docs-only`. For criterion 3, the coder's entry 7 records `make check` green. Criterion 4 is the documenter's: `docs/project-guide/agents.md:295` still holds the sentence it removes.
   - Group 2, architecture: the diff touches only the agent text `agents/agents/reviewer.md` and a test under `tests/agent_files/`. It adds no code and no imports.
   - Group 3, security: no secrets, no markers that silence a check, no code.
   - Group 4, quality: in `agents/agents/reviewer.md:86`, step 3 is now exactly the Interface sentence, and steps 1, 2 and 4 are unchanged. No other copy of the fallback text remains outside the human's `docs/runs/` and the work item; the docs page is criterion 4's. The test adds the constant `STYLE_PAGE_SENTENCE` just above the test that uses it. That is where the removed `STYLE_RULES` test sat, and it is not worth a finding.
   - Group 5, work item hygiene: the journal records the main choice and the rejected option: step 3 is replaced in place, and folding the style page into step 2 was rejected. The Description matches what was built. The docs criterion still says what the documenter must write.

   Earlier tests:
   - `tests/agent_files/test_claude_agent_texts_docs_route.py`: changed under the human's leave, feature decision 8 (the human, 2026-11-06), which the story's Interface names. The change stays within the leave. It removes `STYLE_RULES` and `test_the_reviewer_in_docs_review_lists_each_style_rule_once`, and adds the one test that criterion 1 names, with its constant. Every other test in the module is unchanged.
10. factory: started docs as vm.
11. documenter: I changed one file: `docs/project-guide/agents.md`, *The docs route*. I removed the sentence "Until the style page exists, the reviewer's subsection lists the seven style rules itself." In its place the paragraph now says that on `docs-review` the reviewer judges the writing against `docs/project-guide/style.md` alone (its rules for all documents and the section for the kind of document the diff changes), and that the subsection holds no list of rules of its own. This is criterion 4. The table row above it already said the reviewer judges against the style page, so it stays.

    Cross-read and found current: the rest of `docs/project-guide/agents.md`, and a search of `README.md` and `docs/` (leaving out the human's `docs/runs/`) for other copies of the fallback text. There are none. I checked the diff to `agents/agents/reviewer.md` step 3 against the new paragraph and they agree.

    `docs/decisions.md`: I wrote nothing, as criterion 4 says, because the fallback was a stopgap and not a decision. I added no "Why" or "Rejected" line.

    Not touched, stale but not mine: the operator guide's "once it exists" in *The docs route*. The Description leaves it to the rewrite of `pipeline.md` in the next feature.

    I changed only documents, so I did not run `make check`; the factory's checks follow. No findings for the coder.

    `check`: check: green (not run again: passed on tree 2503ea5b3c55 at 2026-11-06T00:54:40Z)
    `secrets`: secrets: green (0.5 s)
    `documents`: documents ok
12. factory: started smoke-test as vm.
13. smoke-tester: Smoke test: I ran all three commands from the repository root, exactly as written and in order. Each one met its `Expect:` line. I fixed nothing.

    1. Count of the old fallback text in `### docs-review`:
    ```
    0
    ```
    Expect: `0`. Met.

    2. Count of the new step 3 sentence in `### docs-review`:
    ```
    1
    ```
    Expect: `1`. Met.

    3. pytest over the docs-route and review-groups agent-text modules, piped to `grep -c " passed"`:
    ```
    1
    ```
    Expect: `1`. Met. I reran the same pytest command without the grep to see the summary line: `34 passed in 0.03s`.

    Checking the acceptance criteria against what I saw:
    - Criterion 1: the subsection holds the Interface sentence once (command 2) and none of the old text (command 1). A whole-word `grep -c -w until` over the subsection also gives `0`.
    - Criterion 2: the existing docs-review rows pass inside the 34 passed in command 3.
    - Criterion 3: the smoke test does not touch it. The coder's entry 7 records `check: green`, and the factory's check after docs reused that result.
    - Criterion 4: `grep -c "Until the style page exists" docs/project-guide/agents.md` gives `0`. Line 295 of that file now says that on `docs-review` the reviewer judges the writing against `docs/project-guide/style.md` alone.

    Nothing in the run contradicts any criterion.

    Findings: none.
14. factory: done (pull request merged); cost: 6 runs, 4.5 min, 30 turns, 99513 tokens in (458163 more from cache), 8787 out, $0.90
