# Handling of pre-check F0008-1

12 findings: 8 fixed (1 blocker, 7 should fix), 4 notes not applied. Numbering below is the new one. The report is `precheck/F0008-1.md`; its rows are taken in order.

Criterion map. S0001: 1-21 keep their number (12 is reworded); new 22 (`crash_entry_text`); the old 22 and 23 become 23 and 24 (24 criteria). S0002: 1-16 keep their number (10 is extended); new 17 (`asking_crash_cap`); the old 17 and 18 become 18 and 19 (19 criteria). S0003: 1-19 keep their number (15 is extended; 19 criteria). S0004: 1-11 keep their number; new 12 (repository stop); the old 12 and 13 become 13 and 14 (14 criteria).

| # | Severity | Handling |
|---|---|---|
| 1 | blocker | Fixed. F0008-S0001 new criterion 22: `crash_entry_text("doing", 1, "a" * 40)` equals the exact text of the Interface. Inserted before `make check stays green.`; the two closing criteria are now 23 and 24. |
| 2 | should fix | Fixed. F0008-S0001 Assignment: "changes four tests" is now "changes up to five tests". Interface: the sentence "The test of its criterion 10 checks the values of the ten kinds it names, each by its key, and no other value of the mapping." follows the criterion 13 clause. Follow-on edit to keep the story consistent: the Tests paragraph's "the four changed tests named above" is now "the changed tests named above". |
| 3 | should fix | Fixed. F0008-S0001 criterion 12 replaced with the report's text: the `factory-2` refusal is tested both at the claim's time (`held`) and 60 minutes later (`expired`), two cases in one test. |
| 4 | should fix | Fixed. F0008-S0002 new criterion 17: `asking_crash_cap` keeps every other field (from `crashes` 2, `attempts` 1, `round` 1 and a pull request number) and leaves its argument unchanged. Inserted before `make check stays green.`; the closing criteria are now 18 and 19. |
| 5 | should fix | Fixed. F0008-S0002 criterion 10 extended with the title fallback: for a story whose body has no title line the pull request's title is `<id>` alone (two cases, one test). |
| 6 | should fix | Fixed. F0008-S0003 criterion 15 extended with the same fallback (`<id>` alone for a story whose body has no title line; two cases, one test). |
| 7 | should fix | Fixed. F0008-S0004 Tests paragraph: `agent_home` is added to the fixtures, and the tick tests install the agents with `install_agents(agent_home, ...)` from `tests/git_support.py`, because `PipelineLoader` ends the tick with `pipeline_definition_invalid` when an agent is missing. |
| 8 | should fix | Fixed. F0008-S0004 new criterion 12: a tick that ends at a repository stop (agent home left empty, so `pipeline_definition_invalid`) deletes nothing. Inserted before `make check stays green.`; the closing criteria are now 13 and 14. |
| 9 | note | Not applied. The instruction was to apply the predicted refusal and the seven should-fixes only. The inexact sentence ("These forms hold for S0003 and F0009 as well") in F0008-S0001 stays; it does not stop the story. |
| 10 | note | Not applied (same reason). The `branch_commit` and `remote_state` of the `run` event after step 4b stay unstated in F0008-S0003 step 5; the gate and `RunHandler` read neither. |
| 11 | note | Not applied (same reason; the report calls it optional). Demo 3 of S0001 and S0003 keeps `build_handlers(SimpleNamespace(), ...)`. |
| 12 | note | Not applied (same reason; the report calls it optional). F0008-S0004 criterion 4 does not test a story moved to `backlog/` in the work tree only. |
