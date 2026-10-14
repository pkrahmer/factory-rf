# Handling of the pre-check of F0006, round 1

Report: `planning/overnight/precheck/F0006-1.md`. Stories are in `planning/overnight/stories/F0006-reading-the-remote/`. Numbers are story and criterion. Every replacement text is the report's, applied as written.

## Findings

| # | Severity | Finding | Handling |
|---|---|---|---|
| 1 | blocker | S0003 c16 and decision 8: two events of one work item on one remote state share one report key. | fixed. S0003 c16 was "Two different events (a `comment` and a `merged` event of one work item) that fail every time are each reported once at their third error, and further dispatches of either post nothing." and is now "Two different events of one work item on one remote state (a `comment` and a `merged` event) that fail every time each return `"reported"` at their third error; the two reports have the same key, so the pull request holds exactly one factory post, the report of the event that reached the cap first, and further dispatches of either return `"capped"` and post nothing." FEATURE decision 8 got the sentence on the shared key and the alternative of a key per event. |
| 2 | should fix | S0006 rule `main` and c20 name a story id in the message. | fixed. Rule `main` and S0006 c20 now use `factory-watch: no instance settings are wired yet` (was `... no instance settings; they are wired in F0010-S0001`). The Assignment and decision 13 keep the id. |
| 3 | should fix | The Tests sections count calls with a subclass that may override `post_comment`. | fixed in the Tests sections of S0002, S0004 and S0006 (no criterion changed). Each now says the counting subclass overrides every operation except `post_comment`, that `tests/test_hosting_fake_search.py` refuses a test class that defines it, and that posts are counted with `factory_posts`. S0004's sentence is appended, as the report words it. |
| 4 | should fix | S0002 `pull_request=view` is untested for `comment`, `hand_over` and `ask`. | fixed. S0002 c7 now ends "; the events `comment`, `hand_over` and `ask` made after a successful lookup carry the view in `pull_request` as well." |
| 5 | should fix | S0002 `question_posted` has no test for `blocked` `None` or an empty journal. | fixed. S0002 c13 now ends "; `question_posted` is false for a work item whose `blocked` is `None` and for one whose journal is empty, whatever the comments." |
| 6 | should fix | S0003 c17 does not test the title fallback to the id alone. | fixed. S0003 c17 now ends "; for a story whose body has no title line the pull request's title is `<id>` alone." |
| 7 | note (optional) | `PullRequestObservation.comments`: does the model validate "empty unless open"? | not applied: the report marks the comment as optional, and the task named only the Goal wording among the optional edits. |
| 8 | note (optional) | Typed fields without both sides (S0002 c24, S0005 c23, S0006 c24). | not applied: optional; the types are tested in F0001 and F0002, as accepted in F0005. |
| 9 | note (optional) | S0005 could break S0002 and S0004 tests that push two stage-changing commits on one branch. | not applied: optional; no criterion needs such a push. |
| 10 | note (optional) | S0005 `last_stage_change`: no criterion for a newest commit that deleted the file. | not applied: optional; the case is unreachable through the watcher. |
| 11 | note | S0004 c14: `\block\b` matches "lock" in a docstring. | not applied: the report gives no replacement; the failing test names the module. |
| 12 | note | S0007: `PATH` leaves out `/home/factory/.local/bin`. | not applied: the report gives no text for the story. For F0010-S0001: wire the runtime's executable as an absolute path, or probe `claude` on the agent `PATH`. |
| 13 | note | Handling rows 1 to 7 of round 1 hold. | none needed. |
| 14 | note | Handling rows 8 to 25 of round 1 hold. | none needed. |
| 15 | note | Handling rows 26 to 35 of round 1 hold. | none needed. |
| 16 | note | Order, names, size and checks hold. | none needed. |
| 17 | note | Every Demo prints what its `Expect:` says. | none needed. |
| 18 | note (optional) | FEATURE Goal reads "every event kind built so far has a handler", while 11 of 13 kinds stay in `NOT_YET_HANDLED`. | fixed. FEATURE Goal now ends "... and every handler built so far is registered in the production wiring, the kinds still without one listed in `NOT_YET_HANDLED`." The Scope bullet now reads "A test checks that every event kind without a handler is listed in `NOT_YET_HANDLED`, so a kind added later without one fails it." |

Form kept: criteria numbered without gaps, `make check stays green.` second to last, `docs:` last, no criterion added or removed, no change to a Demo or an `Expect:`.
