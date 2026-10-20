# The playbook and the project guide say the reviewer corrects a stale Description

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0034-S0001 gave the shipped reviewer the rule to rewrite a stale `## Description` itself (`claude/agents/reviewer.md:70`). Its docs criterion named one line of `docs/operator-playbook.md` (section 3, check 2 at approval). Three other places in the playbook still say the edit does not exist yet. Section 3, *Never edit a running story's work item*, says "Until a story gives the reviewer that edit, the correction goes into your answer". The table of section 5 says "the reviewer is to rewrite a stale Description (a story to draft)". The table of section 7 lists "A stale Description corrected through the journal" with the state "a small story to draft". The docs criterion also said the project guide does not describe the reviewer's checklist. Yet `docs/project-guide/agents.md`, *The seven agents*, says "Three passages are v1.1's own text and not v1's", and its renaming table repeats "the three passages". The reviewer's *Role* now holds three more passages of v1.1's own: the `Notes:` paragraph from round 1 on and the added-criterion paragraph (both F0021-S0005), and the Description paragraph (F0034-S0001). This story is for the operator, who reads the playbook at a question, and for the agent who reads the guide before changing an agent text. It brings those five places in line with the shipped reviewer. The agent texts, the tests, the operator guide, the decision log and the playbook's list *What changed against the draft* (a record of the draft, item 17) stay as they are. It changes no behaviour, so it has no criterion beyond the two closing ones.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The documenter checks the text against `claude/agents/reviewer.md`, section *Role* (the paragraphs from `From round 1 on` to `when no stage can fix it.`), and against `docs/decisions.md`, *The reviewer corrects a stale Description*.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/operator-playbook.md`. In section 3, *Never edit a running story's work item*, the bullet on a stale Description says the reviewer rewrites it when the human's answers, the Interface or the criteria settle what it should say (F0034), and names each correction in its entry as `description corrected:`. An answer that settles the meaning is therefore enough; it no longer says "Until a story gives the reviewer that edit". In the table of section 5, the row "A push to a work item's branch, to fix its Description, refused" ends with "the reviewer rewrites a stale Description (F0034)" in place of "(a story to draft)". In the table of section 7, the row "A stale Description corrected through the journal" has the state `built (F0034, the reviewer may correct a stale story Description)`. Item 17 of *What changed against the draft* stays as it is. `docs/project-guide/agents.md`, *The seven agents*: the sentence "Three passages are v1.1's own text and not v1's" names, beside the three it lists, the reviewer's three *Role* paragraphs of v1.1's own: the `Notes:` from round 1 on and the added criterion (F0021-S0005), and the correction of a stale Description (F0034-S0001). The renaming table's "except the three passages" gives the same count. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, since F0034-S0001 already wrote them.

## Smoke test

```bash
p=docs/operator-playbook.md
for s in 'Until a story gives the reviewer that edit' '(a story to draft) |' 'corrected through the journal | the reviewer may rewrite a stale Description | a small story to draft'; do grep -qF -e "$s" "$p" && echo "still: $s" || echo gone; done
```
Expect: three lines `gone`

```bash
grep -c -F 'built (F0034, the reviewer may correct a stale story Description)' docs/operator-playbook.md
```
Expect: `1`

```bash
grep -c -F 'Three passages are v1.1' docs/project-guide/agents.md; grep -c -F 'F0034-S0001' docs/project-guide/agents.md
```
Expect: two lines, `0` (the count of three is gone) and a number of at least `1` (the guide names the Description paragraph's story)

## Journal
