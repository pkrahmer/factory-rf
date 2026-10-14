# Handling of pre-check F0009-1

Report: `planning/overnight/precheck/F0009-1.md`, 14 findings (5 predicted refusals, 5 should-fixes, 4 notes). The refusals and should-fixes are applied with the report's replacement text; the notes need no edit or are outside the drafts. The human's leave for the two allow-list edits of decision 22 is given by the session, acting for the human on 2026-10-14.

| Story and criterion | Severity | Handling | Criterion changed |
|---|---|---|---|
| F0009-S0008 c17 | blocker | Fixed: the first line now carries the detail that F0006-S0006's `render_event` appends. | S0008 c17 reworded |
| F0009-S0008 c5 | blocker | Fixed: the setup uses feature `F0002-todo`, which `origin/main` holds without a report, so decision 3 and the directory lookup agree. | S0008 c5 reworded |
| F0009-S0003 `open`, push failure | blocker | Fixed: new criterion for the rejected push; the closing criteria moved to 25 and 26 (26 criteria, the maximum). | S0003 new c24; make check c25, docs c26 |
| F0009-S0005 `AcceptanceMerged.handle`, rejected main push and refused deletion | blocker | Fixed: two new criteria; the closing criteria moved to 21 and 22. | S0005 new c19 and c20; make check c21, docs c22 |
| F0009-S0007 steps 3 and 4, rejected main push and refused deletion | blocker | Fixed: two new criteria; the closing criteria moved to 14 and 15. | S0007 new c12 and c13; make check c14, docs c15 |
| FEATURE decision 22; S0003 and S0004 rules | should fix | Fixed: the leave is recorded in the three texts and the two allow-list edits are named as `ALLOWED["JOURNAL"]` and `ALLOWED["entry_text"]`. Decision 22's first sentence ("the human's leave covers only the first group") said the opposite and now reads "in two groups, each with the human's leave". | none (FEATURE decision 22, S0003 `acceptance_head` rule, S0004 rule) |
| F0009-S0003 `AcceptanceFacts.next_story`; c22 | should fix | Fixed: a Rules bullet states the validator that c22 already tests. | none (S0003 Rules, new bullet after `acceptance_facts`) |
| F0009-S0002 c24 | should fix | Fixed: the typed fields `feature`, `id`, `next_acceptance`, `status` are named with both sides. | S0002 c24 reworded |
| F0009-S0008 c4 | should fix | Fixed: the waiting work item is defined by its stage, `handed_over` and an open pull request with no unread human comment. | S0008 c4 reworded |
| F0009-S0007 c8; decision 19's blocked case | should fix | Fixed: c8 now covers the close at the stage `acceptance` with `blocked == "question"`; decision 19's text already states the case and is unchanged. | S0007 c8 reworded |
| F0009-S0004 last step of `handle`, `PushFailed` of the branch push | note (optional) | Not applied: the report calls it optional, F0007-S0001 tests the behaviour, and the instructions name the refusals and the should-fixes only. | none |
| F0009-S0011 (all), S0006 c9 to c12 | note | Not applied: no change asked (walks that are green at once are the accepted precedent). | none |
| F0009-S0003 size | note | Not applied: no change asked. With the new criterion S0003 has 26 criteria, the maximum; no further criterion can be added to it. | none |
| Sheet: F0006-S0006 `FeatureRow.acceptance` comment | note | Not applied: the file lies outside F0009's drafts. For the sheet items: replace the comment with `# filled by F0009-S0002 (fill_board) through BoardReader.read (F0009-S0008)`. | none |

## Criteria per story after the edits

S0001 25, S0002 26, S0003 26, S0004 21, S0005 22, S0006 14, S0007 15, S0008 20, S0009 11, S0010 10, S0011 15. Each numbering runs without gaps, `make check stays green.` is second to last and `docs:` last. No other draft cites a renumbered criterion.
