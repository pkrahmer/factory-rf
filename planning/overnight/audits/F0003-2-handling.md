# Handling of precheck\F0003-1.md (Phase 3/4)

Report: `planning/overnight/precheck/F0003-1.md`. Rows follow its findings table in order. "Report row" is the row's position in that table (1 to 23). Story numbers are F0003's.

| Report row | Severity | Handling | What changed |
|---|---|---|---|
| 1. S0001 Rules (`read` bullet), c22 | blocker | fixed | Rules bullet: "cannot be read" now reads "cannot be read (an `OSError`, such as a directory at the path, or bytes that are not UTF-8)". c22 old: "... for a file that holds `not json`, for one that holds `{"stops": [], "extra": 1}` and for an empty file; a `write` afterwards replaces the file, and `read()` then returns what was written (one test, three cases)." New: adds the bytes `b"\xff\xfe"` and the directory at the path as cases, "(one test, five cases)". |
| 2. S0001 c11 | should fix | fixed | c11 old: "`ManualClock(start).now()` equals `start` converted to UTC until `advance`, ..." New: "`ManualClock(start).now()`, for a `start` with an offset of two hours east of UTC, is the same instant with `utcoffset()` equal to zero until `advance`, ...". |
| 3. S0001 c16 (clock read once) | note (optional) | deferred | Optional preference; the Demo and c16 already cover the rule with the stated clock. No criterion added. |
| 4. S0002 c1, c2, Tests line | blocker | fixed | Tests line: after "so a later story that adds a required field changes only this fixture." added the `Callable[..., Boundaries]` variable for the keyword-only test and `setattr(boundaries, field, value)` for the frozen test, with the `mypy --strict` reasons. Criteria 1 and 2 keep their wording. |
| 5. S0002 c8 | should fix | fixed | c8 old: "... raises the `OSError` of the log (its `filename` lies below the log's regular file, not the health file's)." New: "... raises the `OSError` of the log: its `filename` is the log's regular file or a path below it, not the health file's or one below that." |
| 6. S0003 Rules last bullet, `GitError` | blocker | fixed | New c22 (inserted before `make check`): a `GitError` from reading the remote branch propagates from `post`, no pull request exists afterwards. `make check` is now c23, docs c24. |
| 7. S0003 c12 setup | note | fixed | Tests line: appended the `run_git(... "origin/main:refs/heads/<branch>")` plus `checkout.fetch()` recipe for the branch at the tip of `main`. |
| 8. S0003 brief check (fake and real client) | note | none needed | Report gives no change. |
| 9. S0004 Tests line, S0007 Tests | blocker | fixed | S0004 Tests line: the sentence "so that the rules of S0007 do not refuse it: a lease of 1 is given together with a `time_limit` of 1, and a `round_cap` is given to the stage `doing`." replaced by the report's text (accepting cases keep the load-time rules; the accepted lease of 1 goes on the minimal text with a coder `time_limit` of 1). S0007 needs no change: its "No test of S0004 changes" now holds. |
| 10. S0004 Interface `contract` comment | should fix | fixed | Comment old: `# required, "<major>.<minor>"`. New: `# required, quoted text; its form "<major>.<minor>" and its major are checked by S0007`. |
| 11. S0004 c16 / S0006 multi-line problem | note (optional) | deferred | Optional; no criterion is wrong ("starts with", "contains"). Taking only the first line of ruamel's message would change what the detail holds; left for the human. |
| 12. S0004 / S0005 wrong story attributions | note | fixed | S0004 Interface: "adds to F0002-S0002's module" is now "adds to F0002-S0003's module". S0005 Interface: "adds to F0001-S0007's module" is now "adds to F0001-S0008's module". |
| 13. S0004 `position` of an unknown stage | note (optional) | deferred | Optional; the Interface states no rule and the report offers no required text. Would add a `KeyError` rule and a case to c4. |
| 14. S0005 rule 6 (`key` of the first fault) | note | none needed | Report gives no change. |
| 15. S0006 Rules, ordering of agents after the text | blocker | fixed | New c16 (before `make check`): a definition without `contract` on `origin/main` with `<agent_home>/agents` missing is refused with `missing key: contract` alone, and the stop's detail is that fault. `make check` is now c17, docs c18. |
| 16. S0006 c9 (`GitError`) | should fix | fixed | c9 old: "A `GitError` from reading the file (a ref that does not exist) propagates from `load`, and no stop is raised." New: propagates and raises no stop and writes no line, both for `load()` with a failing `git` (a `GitCli` on a missing directory, via `dataclasses.replace`) and for `load("origin/nowhere")`. |
| 17. S0006 / S0007 Tests (agent helper) | note | fixed | S0006 Tests: "where a helper writes a valid agent file for each role" is now "where the helper `install_agents(agent_home, roles)` of `tests/git_support.py` writes a valid agent file for each role (S0007's loader tests use it too)". |
| 18. S0006 `clear_stop` failing on success | note (optional) | deferred | Optional; the Interface comment "OSError from the stop's writes" already implies that it raises. |
| 19. S0007 order inside rules 6 to 9 | note (optional) | deferred | Optional; no criterion uses a text that depends on it. Would extend c13. |
| 20. All stories, size | note | none needed | S0001 and S0007 stay at 26 criteria after the changes (S0001 unchanged in count; S0007 unchanged). S0003 is at 24 and S0006 at 18; no split. |
| 21. Order and names | note | none needed | Report gives no change. |
| 22. `Boundaries` (brief check) | note | none needed | Report gives no change. |
| 23. Handling rows 1 to 32 of the earlier round | note | none needed | Rows 7, 9 and 11 were incomplete and are closed by report rows 9, 1 and 6 above. |

Renumbering: S0003 c22 `make check` to c23, docs c23 to c24. S0006 c16 `make check` to c17, docs c17 to c18. No cross-reference named those numbers; FEATURE.md names no criterion numbers and is unchanged. No story grew past 26 criteria.

Needs interfaces.md: none.
