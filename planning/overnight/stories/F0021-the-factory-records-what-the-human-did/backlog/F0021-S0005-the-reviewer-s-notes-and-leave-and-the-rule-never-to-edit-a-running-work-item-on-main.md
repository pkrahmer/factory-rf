# The reviewer's notes and leave, and the rule never to edit a running work item on main

## Description

Two questions keep reaching the human. The first: at every review round, the reviewer sends a story back for points that are only the quality of the story's own new tests (a copied helper, a name, a duplicate test), and the round cap then asks the human whether to go on. The second: a review finds behaviour the diff already builds that no criterion names, and the reviewer asks the human for a criterion that needs no code at all. This story changes the shipped agent texts so that, from round 1 on, such test-quality points go forward as notes in the reviewer's entry instead of back, while a point on a criterion, the architecture, security or `src/` still sends the story back; and so that the reviewer may itself add a criterion that only pins behaviour already built, writing it into the work item and naming it in its entry, the coder handing it on to the tester without a code change and the tester writing the test (the feature's decisions 10 and 11). The tester's step 0 gains one sentence, so that it writes that test without a human's answer to edit. The acceptance reviewer's cost check names the new facts line of S0002. A further text is the operator's: `docs/operator-guide.md` says never to edit a running work item on `main`, but to answer in its pull request, since the agents amend the story on its branch and a human's edit on `main` conflicts with the branch at the next stage start, as F0019-S0004 showed. Every other text of the agents stays as it is, the lessons sections included.

## Interface

`claude/agents/reviewer.md` (the coder writes it), section `## Role`:

- The paragraph that begins `Your recommendation is your decision:` and ends `Never both, never "pass with remarks": a remark worth writing is a finding.` becomes exactly:

  ```markdown
  Your recommendation is your decision: `docs` passes, `doing` sends the work item back. Never both, and never "pass with remarks": a remark worth writing is a finding, except for the notes from round 1 on below.
  ```

- Right after it, two new paragraphs, exactly:

  ```markdown
  From round 1 on (your prompt names the round; the first review, at round 0, still sends such a point back), a point that is only about the quality of a test file the diff adds (a copied helper, a name, a duplicate test) is a note, not a finding: write the notes under `Notes:` after the findings, or after `no findings`, one line each with its location; they do not send the work item back. This holds for the copied helper and the separate test functions your lessons count as findings, when they are in a test file the diff adds. A point on an acceptance criterion (an untested side of a stated limit among them), the architecture, security or anything under `src/` is still a finding and sends it back with `doing`.

  When the diff builds a behaviour that no criterion names, and pinning it needs no change under `src/`, add the criterion yourself instead of asking the human: write it into the work item's `## Acceptance criteria` before the two closing ones and renumber those, name it in your entry as the finding `criterion <n> added: it needs its test`, and end with `doing`. The coder hands it to the tester, who writes the test. A criterion that needs a code change stays a finding or a question.
  ```

`claude/agents/coder.md`, section `## Stage`, step 2: one sentence appended at its end, exactly:

```markdown
When the reviewer's latest entry adds a criterion that needs only its test, change no code: end with `tests` and an entry naming the criterion.
```

`claude/agents/tester.md`, section `## Stage`, step 0: one sentence appended at its end, exactly:

```markdown
When the coder's entry names a criterion the reviewer added that needs only its test, there is no test to edit: write the test of that criterion as the role section describes, run `make test` once, and end with `doing`.
```

`claude/agents/acceptance-reviewer.md`, section `## Role`, check 8 (**Cost.**): one sentence appended at its end, exactly:

```markdown
Your prompt's `Human interventions of the stories` line counts the questions the human answered, by cause, and the hours the stories waited for them: give both in the cost section, and name the story that needed the human most when its journal shows why.
```

- No other line of the four files changes; the `## Lessons` sections stay exactly as `tests/test_claude_agent_texts.py` pins them, and no new text uses a word that test bans.

`docs/operator-guide.md` (the documenter writes it, from the docs criterion).

Test module (new): `tests/test_claude_agent_texts_review_leave.py`, reading the bodies through `agent_body` of `tests/shipped_agents.py`. No earlier test changes.

## Acceptance criteria

1. Rows of one parametrized test, each a text that the body of an agent holds in the named section (`section_text`): the reviewer's new recommendation paragraph, its paragraph of notes from round 1 on and its paragraph of the added criterion, each exactly as the Interface gives it, in `Role`; the coder's sentence in `Stage`; the tester's sentence in `Stage`; the acceptance reviewer's sentence in `Role`.
2. The reviewer's body no longer holds `Never both, never "pass with remarks": a remark worth writing is a finding.`, and its three paragraphs of criterion 1 follow each other in the order the Interface gives them (rows of one parametrized test on the position of each paragraph).
3. Every test of `tests/test_claude_agent_texts.py` passes unchanged, its exact lessons of the reviewer, the coder and the acceptance reviewer included.
4. `make check` stays green.
5. docs:
   - `docs/operator-guide.md`, *A stage changed by hand*: a new subsection with the heading line exactly `### Never edit a running work item on main`. It says: do not edit the file of a work item in `in-progress/` on `main`; answer in its pull request, and the agents amend the story on its branch; an edit on `main` conflicts with the branch when the next stage start merges `main` into it, and the stage stalls with the reason `merge_conflict` (F0019-S0004 showed it); and, when it has happened, revert the edit on `main`.
   - `docs/operator-guide.md`, *The hand-over at the approval* or *The factory's own questions*: one paragraph on the reviewer's notes from round 1 on and its added criterion, so that the human reading a review entry knows what `Notes:` and `criterion <n> added` mean, and that an added criterion is a send-back that counts a round, so the round cap may still ask the human afterwards.
   - `docs/decisions.md`: a new entry, "The reviewer passes test-quality points on as notes from round 1 on, and may add a criterion that needs no code", with the reason (two recurring questions to the human; the factory's way from an LLM on watch to running alone) and the rejected alternatives: raising the round cap, and leaving every criterion to the human.

## Smoke test

```bash
grep -cx '### Never edit a running work item on main' docs/operator-guide.md
```

Expect: `1`

```bash
grep -c 'From round 1 on (your prompt names the round; the first review, at round 0, still sends such a point back), a point that is only about the quality of a test file the diff adds' claude/agents/reviewer.md
grep -c 'criterion <n> added: it needs its test' claude/agents/reviewer.md
grep -c 'When the reviewer.s latest entry adds a criterion that needs only its test, change no code' claude/agents/coder.md
grep -c 'there is no test to edit: write the test of that criterion' claude/agents/tester.md
grep -c 'Human interventions of the stories' claude/agents/acceptance-reviewer.md
```

Expect: five lines, each `1`.

## Journal
