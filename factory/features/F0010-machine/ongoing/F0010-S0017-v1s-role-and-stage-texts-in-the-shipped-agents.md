---
stage: review
pr: 135
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# v1's role and stage texts in the shipped agents

## Assignment (as of log entry 1)

Carry v1's role and stage texts into the seven shipped agents, in the glossary's words (questionnaire 1, Q29: v1's texts, renamed, so that the baseline run compares with v1's run on the same instructions). The shipped agent bodies of the earlier story hold only each role's boundary sentence and entry sentence; this story adds after them what v1 preloaded into each agent as skills: the pipeline rules every stage agent works under, the role's text where v1 had one, and the stage's text. The source is `planning/v1-texts/`, the verbatim copy of v1's `claude/` tree (pkrahmer/factory at `f8bc9d2`: the files `agents/*.md` and `skills/*/SKILL.md`, in the same relative paths) that the human added on 2026-10-15 (`FEATURE.md` decision 32); the copy lies in the human's directory, outside every write path, and no stage edits or cross-reads it. The coder reads it and writes only under `claude/`. The text is renamed with the table below, and `stuck` becomes `question` (F0005 decision 24: v1.1 has no `stuck`; an agent that cannot finish asks). Sentences that describe v1's own mechanics are rewritten to what v1.1 does or dropped when v1.1 does it in code: the factory commits, pushes and moves the work item (the prompt's end line), so no agent commits or pushes; the promotion of a story, the round caps and the pipeline files are the factory's and the human's. The acceptance reviewer's text names the report sections that F0009 reads. This story covers no condition of its own; it finishes R30's shipped agents and keeps kept thing 6. A run of the real agents is the morning observation (the baseline run). After v1's texts each body ends with a section `## Lessons` of v1.1's own: the general rows of `planning/lessons-for-the-skills.md` (`FEATURE.md` decision 36). No skill file is shipped (the runner applies no `skills` key).

## Interface

Each `claude/agents/<role>.md` keeps its front matter and its first two paragraphs (the boundary sentence and the entry sentence of the earlier story), and then has these `## ` sections in this order and no other `## ` heading:

- `## Rules`: v1's pipeline rules `factory-rules` carries. R1 to R4, R6, R8, R9 and R11 are carried with the rename table; R2 is rewritten to the v1.1 contract: the agent ends with a decision, one of the `Allowed decisions` its prompt lists, which always include `question`, and with a journal entry. R5, R7, R10 and R12 to R15 describe v1's tickets, stage table, commit conventions, round caps and pipeline files: they are rewritten in the glossary's words to what the prompt, the pipeline definition and the write paths say, or dropped when v1.1 does them in code. The section says that the factory commits, pushes and moves the work item, and that the agent never pushes, checks out, switches, merges, pulls or calls `gh`.
- `## Role`: v1's role skill, for the roles that had one: `tester` (`role-tester`), `coder` (`role-coder`), `reviewer` (`role-reviewer`), `documenter` (`role-documenter`) and `acceptance-reviewer` (`role-acceptor`). `intake` and `smoke-tester` have no `## Role` section.
- `## Stage`: v1's stage skill: `intake` (`stage-intake`), `tester` (`stage-tests`), `coder` (`stage-doing`), `reviewer` (`stage-review`), `documenter` (`stage-docs`), `smoke-tester` (`stage-demo`) and `acceptance-reviewer` (`stage-feature`).
- `## Lessons`: v1.1's own part, after v1's texts: the general rows of `planning/lessons-for-the-skills.md` (the human, 2026-10-14), one bullet each, in this order and verbatim, in the bodies of the roles named. Every body starts the section with the first bullet; `smoke-tester` and `acceptance-reviewer` have only that one.

The bullets, by role, exactly as they go into the files (each line that starts with `- ` is one bullet of the section; the other lines are labels):

```text
every role (the first bullet of each body):
- Run `make check` and every other make target in the foreground and read its output. Never start one in the background, and never wait for a process with `pgrep -f`: it matches its own command line, so the wait never ends.

intake (after the first):
- Every clause of an Interface rule has its own criterion, on both sides: an ordering, the second branch of an "or", a "when longer than", the value for every kind an enum names, an exact value beyond its first part. A clause without one is a question.
- Every behaviour that the Description, the Interface or a decision of the feature states has its own criterion; one without is a question.
- A story that changes a test another story wrote names that test and has the human's word; one that does not is a question.

tester (after the first):
- Every stated limit is tested on both sides, also when no criterion spells out the refused side. The sides of one rule are rows of one parametrized test, not separate test functions, and setup that several tests share is a fixture.
- The test data you build (a work item text, a state, a pipeline definition, a push) is valid under the readers and validators already built, unless the test is about that rule.
- You change a test another story wrote only when the story names that test and the human has given their word; you make that change, the coder never does.

coder (after the first):
- Before you write a helper, search the code for one that does the same, and reuse or extend it; the reviewer counts a second copy of an existing helper as a finding.
- You never change a test, not even one the story names as changed with the human's word: the tester makes that change.

reviewer (after the first):
- Count a second copy of an existing helper as a finding, and name the helper it copies.
- Count as a finding a stated limit tested on one side only, and the sides of one rule written as separate test functions instead of rows of one parametrized test.

documenter (after the first):
- The project guide is an index plus one file for each domain, each well under the 2,000 lines the file tool reads by default; split a file before it grows past that.

smoke-tester, acceptance-reviewer: the first bullet only.
```

The rename table, applied to every carried text:

| v1 | v1.1 |
|---|---|
| ticket | work item |
| log | journal |
| `drafts/` | `backlog/` |
| `ongoing/` | `in-progress/` |
| promote | start |
| `stages.yml`, stage table | the pipeline definition (`factory/pipeline.yml`) |
| lane | write paths |
| gate, the stage `accept` | approval |
| demo (the stage and the agent) | smoke test |
| acceptor | acceptance reviewer |
| outcome (of an agent) | decision |
| verdict | recommendation |
| `max_rounds` | `round_cap` |
| `stuck` | `question` |
| `Assignment`, `## Assignment` (the story's section) | `Description`, `## Description` |
| `## Log (append only)` | `## Journal` |
| `## Demo`, Demo (the story's section) | `## Smoke test`, smoke test |

The row `log` has no criterion of its own: `git log`, which the texts keep, holds the word. The other rows are tested by criteria 3 and 4.

The decisions each body names, from the stage's `next` in `template/factory/pipeline.yml` and `question`: `intake` ends with `tests` or `question`; `tester` with `doing` or `question`; `coder` with `review`, `tests` or `question`; `reviewer` with `docs`, `doing` or `question`; `documenter` with `smoke-test`, `doing` or `question`; `smoke-tester` with `approval`, `doing` or `question`; `acceptance-reviewer` with `approval` or `question`.

The acceptance reviewer's body names the report sections `## Recommendation` and `## Proposed stories` (which F0009-S0001 and S0004 read; named inline, never at the start of a line), the three recommendations `accepted`, `accepted with stories` and `not accepted`, and says that proposed stories are written into the feature's `backlog/`.

Anchors, phrases that must appear in the body after the rename (they show that the text was carried, not summarised): in `## Rules` of every body `Git is the only truth.`, ``To ask the human, end with `question` `` and ``one of the `Allowed decisions` your prompt lists`` (the R2 rewrite); `intake` `Check that the story is buildable before anyone spends tokens on it.`; `tester` `You write tests, not code.` and ``Run `make test 2>&1 | tail -5` once``; `coder` `You make the failing tests pass without changing them` and `Refactor, once.`; `reviewer` `You review a diff against a work item.` and `You do not edit code, and you do not write any`; `documenter` `You write for the reader who was not there` and `Run every example you wrote or changed.`; `smoke-tester` `You run the smoke test, record what happened and judge it against the work item. You do not fix anything.`; `acceptance-reviewer` `You judge and you propose; you build nothing.` and `Do the eight checks`. Four more phrases are tested by criteria 7, 10, 11 and 12: in `## Rules` of every body ``The factory commits, pushes and moves the work item.`` and ``You never push, check out, switch, merge, pull or call `gh`.``; in `acceptance-reviewer` ``Write the proposed stories into the feature's `backlog/`.``; in `smoke-tester` ``compare the output with its `Expect:` line`` and `its trimmed output in a fenced block`; in `coder` `A test that cannot pass against the work item` and ``end with `tests` and an entry naming the test and the change``.

Tests: `tests/test_claude_agent_texts.py` (reads `claude/agents/*.md` and `template/factory/pipeline.yml` from the repository root; a file of its own, so that the earlier story's `tests/test_claude_files.py` stays as it is).

## Acceptance criteria

1. The body of each of the seven files still starts with its boundary sentence, a blank line and its entry sentence, exactly as in the table of the earlier story.
2. After those two paragraphs the `## ` headings of each body are, in order, `## Rules`, `## Role`, `## Stage` and `## Lessons`, with no `## Role` for `intake` and `smoke-tester` and no other `## ` heading.
3. No body contains the word `stuck`.
4. No body contains, as a whole word and in any case, any of `ticket`, `lane`, `gate`, `demo`, `acceptor`, `verdict`, `outcome` (also in the plural), `drafts`, `ongoing`, `promote`, `max_rounds` or `stages.yml`; and no body contains `Assignment` or `(append only)`: v1.1's story has a `## Description` and a `## Journal`.
5. Each body names every decision of its stage in inline code, as listed under the decisions each body names: for example the body of `coder` contains `` `review` ``, `` `tests` `` and `` `question` ``, the decisions derived from the `next` of the role's stage in `template/factory/pipeline.yml`.
6. The `## Rules` section of each body contains the anchors `Git is the only truth.`, ``To ask the human, end with `question` `` and ``one of the `Allowed decisions` your prompt lists``.
7. The `## Rules` section of each body contains `The factory commits, pushes and moves the work item.` and ``You never push, check out, switch, merge, pull or call `gh`.``
8. The `## Role` and `## Stage` sections of each body contain the anchors listed for its role (one test case for each role).
9. The body of `acceptance-reviewer` names `## Recommendation` and `## Proposed stories`, and each of `accepted`, `accepted with stories` and `not accepted`.
10. The body of `acceptance-reviewer` contains ``Write the proposed stories into the feature's `backlog/`.``
11. The body of `smoke-tester` contains ``compare the output with its `Expect:` line`` and `its trimmed output in a fenced block`.
12. The body of `coder` contains `A test that cannot pass against the work item` and ``end with `tests` and an entry naming the test and the change``.
13. The `## Lessons` section, the last of each body, holds exactly the bullets the Interface lists for its role, verbatim and in that order (one test case for each role).
14. make check stays green.
15. docs: `docs/project-guide.md` says that each shipped agent's body carries v1's rules, role and stage texts renamed with the table above after its two sentences, lists the rename table, and says where an agent's text is changed (`claude/agents/`), and says that the last section, `## Lessons`, is v1.1's own, after v1's texts, and holds the lessons of v1.1's build for each role; `docs/decisions.md` records why v1's texts were carried over and renamed (questionnaire 1, Q29: the baseline run compares with v1's run on the same instructions) and that `stuck` does not exist in v1.1.

## Demo

```bash
uv run python -c "
import re
from pathlib import Path
for path in sorted(Path('claude/agents').glob('*.md')):
    print(path.stem, re.findall(r'^## .*', path.read_text(), re.M))
"
```
Expect: seven lines, one for each agent in sorted order. The lists are `['## Rules', '## Stage', '## Lessons']` for `intake` and `smoke-tester`, and `['## Rules', '## Role', '## Stage', '## Lessons']` for the other five.

```bash
uv run python -c "
import re
from pathlib import Path
banned = re.compile(r'\b(ticket|lane|gate|demo|acceptor|verdict|outcome|stuck)s?\b', re.I)
print(sum(len(banned.findall(path.read_text())) for path in Path('claude/agents').glob('*.md')))
"
```
Expect: one line, `0`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete files (`claude/agents/<role>.md`), the exact section order, the rename table, per-role bullets verbatim and the decisions per body. These match `next` in `template/factory/pipeline.yml` (intake→tests; tests→doing; doing→review/tests; review→docs/doing; docs→smoke-test/doing; smoke-test→approval/doing; acceptance→approval). The source files exist under `planning/v1-texts/` (agents, skills). The seven target agent files exist.
   - Criteria: each is testable by one function, with parametrised cases per role. Every stated behaviour has a criterion: the section order and absence of `## Role` (2), the rename table's banned words and `stuck` (3, 4), the decisions (5), the anchors (6 to 12) and the lessons (13). The failing sides are covered as negative checks: no extra heading, no `## Role` for intake and smoke-tester, no banned word, and exactly the listed bullets.
   - Demo: both commands are runnable with `uv run python -c`. Each `Expect:` line is checkable: seven lines with the heading lists, then `0`.
   - Architecture: the story only touches `claude/agents/` and a root-level test file, which CLAUDE.md allows for modules outside the layers. It adds no dependency and no code in `src/`.
   - Scope: it is within F0010's scope ("shipped agents with v1's role and stage texts renamed ... v1.1's own lessons", decisions 16, 32 and 36). It stays out of the skill files and the story forms.
3. tester: Wrote the red tests for the agent texts in one new file, `tests/test_claude_agent_texts.py`. It uses `tests/shipped_agents.py` (`SHIPPED_AGENTS`, `front_matter_and_body`, `ROOT`) and reads the decisions from `template/factory/pipeline.yml` through `RuamelPipelineDefinitionReader`. `tests/test_claude_files.py` is unchanged.

   - criterion 1: tests/test_claude_agent_texts.py::test_body_still_opens_with_the_boundary_and_the_entry_sentence (one case per agent)
   - criterion 2: tests/test_claude_agent_texts.py::test_body_has_rules_role_stage_and_lessons_sections_in_order (every line starting with `## ` in the body must equal the expected list; there is no `## Role` for intake and smoke-tester)
   - criterion 3: tests/test_claude_agent_texts.py::test_body_never_says_stuck (`\bstuck\b`, any case)
   - criterion 4: tests/test_claude_agent_texts.py::test_body_uses_no_word_the_rename_table_replaces (whole words in any case, with a plural only for `outcome` as the criterion says; plus the substrings `Assignment` and `(append only)`)
   - criterion 5: tests/test_claude_agent_texts.py::test_body_names_every_decision_of_its_stage_in_inline_code (the role's stage `next` from the template plus `question`, each in backticks)
   - criterion 6: tests/test_claude_agent_texts.py::test_rules_section_carries_the_pipeline_rules_with_the_decision_contract (agent × the three anchors, looked for in the `## Rules` section)
   - criterion 7: tests/test_claude_agent_texts.py::test_rules_section_leaves_commit_push_and_move_to_the_factory (agent × the two anchors, in `## Rules`)
   - criterion 8: tests/test_claude_agent_texts.py::test_role_and_stage_sections_carry_the_texts_of_the_role (one case per role; the anchors are looked for in `## Role` and `## Stage` together)
   - criterion 9: tests/test_claude_agent_texts.py::test_acceptance_reviewer_names_the_report_sections_and_recommendations (the five phrases are matched as plain text, because the criterion does not require inline code here, unlike criterion 5)
   - criterion 10: tests/test_claude_agent_texts.py::test_acceptance_reviewer_writes_proposed_stories_into_the_backlog
   - criterion 11: tests/test_claude_agent_texts.py::test_smoke_tester_compares_with_expect_and_records_trimmed_output
   - criterion 12: tests/test_claude_agent_texts.py::test_coder_sends_a_wrong_test_back_to_the_tester
   - criterion 13: tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets (one case per role; `## Lessons` must be the last heading, and its non-blank lines must equal the Interface's bullets verbatim and in order)
   - criteria 14 and 15: these are not tested here; they are the `make check` gate and the documenter's work.

   Run: `make test` fails as intended. The new tests fail on assertions because the bodies do not yet have the sections. There is no import error, since every module they import already exists. `make lint` passes.

   Open: nothing. Two reading choices are noted above: plurals for `outcome` only in criterion 4, and plain text in criterion 9. Both follow the criteria's wording, and the smoke-test command still bans plurals of every word.

   `make lint`: lint: green
   `make test`: FAILED tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets[acceptance-reviewer]
4. coder: Built: I carried v1's pipeline rules, role skills and stage skills into the seven shipped agents, `claude/agents/{intake,tester,coder,reviewer,documenter,smoke-tester,acceptance-reviewer}.md`, in commit 830029c. Each file keeps its front matter and its two sentences. After them come `## Rules` (from `factory-rules`), `## Role` (except intake and smoke-tester), `## Stage` (from the matching `stage-*` skill) and `## Lessons`. The lessons are the Interface's bullets, verbatim and in order. Nothing changed under `src/` or `tests/`. `make check` is green, all of `tests/test_claude_agent_texts.py` passes, and both smoke-test commands print what the `Expect:` lines say: the seven heading lists, then `0`.

   Main decision: I applied the rename table and rewrote each v1 mechanic as what v1.1 actually does, using the project guide as the source.
   - R2 now uses the `Allowed decisions` contract, and "cannot finish" becomes `question`.
   - R10 says the factory commits, pushes and moves the work item, and that no agent commits. So the coder's commit steps became "leave the work in the working tree", and the refactor step reads `git diff main` plus `git status --short` instead of `main...HEAD`.
   - R7 points to the stage's `next` and `checks` in `factory/pipeline.yml`, and R12 to `round_cap`.
   - R14 (commit subjects) is dropped because code writes them. R15 became R14 and talks about write paths, with `{work_item}` as the agent's own work item.
   - Paths use v1.1's names: `feature.md`, `factory/story-form.md`, `backlog/`, `in-progress/`, and the acceptance report `in-progress/<id>-acceptance.md`.
   - The acceptance-reviewer's report names `## Recommendation`, `## 1 Scope` to `## 8 Cost` and `## Proposed stories`, always inline so none of them becomes a heading. Its recommendations are `accepted`, `accepted with stories` and `not accepted`.

   Rejected: rewriting the texts in my own words. That would break the baseline comparison with v1's run on the same instructions, so changes stay at the level of words and mechanics. I also rejected keeping the coder's v1 commit steps, which contradict the factory's commit and the Description.

   Noticed, not touched:
   1. In `template/factory/pipeline.yml` the coder's and tester's write paths do not include `{work_item}`. So the coder's step "rewrite `## Description`" can only work where a project adds it. The text says so ("and your write paths include the work item").
   2. The texts still mention `make mutants` and `docs/openapi.json` "if the project has" them, as v1's did.
   3. `docs/` is the documenter's work under criterion 15.

   `make check`: check: green
