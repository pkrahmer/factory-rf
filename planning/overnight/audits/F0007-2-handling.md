# Handling of the pre-check of F0007, round 1

Report: `planning/overnight/precheck/F0007-1.md`. Files changed: `FEATURE.md` and drafts S0002, S0005, S0006, S0007, S0008 and S0009 of `planning/overnight/stories/F0007-human-on-the-pull-request/`. Criterion numbers did not move and no criterion was added or removed; no story is near 26 criteria.

Counts: 17 findings (the report's table rows, in order) and 1 suggestion from its Feature section; 7 fixed, 5 optional notes and the suggestion not applied (left for the morning), 5 need no change.

| # | Finding | Handling |
|---|---|---|
| 1 | S0006 rule (`claim`) and c8: the kept-claim case cannot be built (blocker, predicted tester refusal) | fixed: the `claim` clause now sets `claim` to `None` with the reason (a claim is always for the current stage, `new` at the head of the branch); c8 is now one case: a claim held at the illegal stage is cleared, and the file at the new commit has `claim` unset and the restored `stage`. |
| 2 | S0005 `send_back_cap`, c4: an uncapped stage before the capped one is not tested (should fix) | fixed: c4 has three cases, one test (fixture; fixture with `acceptance` placed before `smoke-test`; no stage with a `round_cap`). |
| 3 | S0005 `reason_given`, c1: a comment with no `result` record is not tested (should fix) | fixed: c1 adds the case of a `comment` and no `result` record (two cases, one test). |
| 4 | S0002 c5: "the same event" is ambiguous (should fix) | fixed: c5 starts "With `blocked == "question"` and its question already posted". |
| 5 | S0008 Tests, c6: the test needs `checkout.fetch()` (should fix) | fixed: Tests gets the sentence about the fetch after the push and `branch_commit` taken from the remote-tracking ref. |
| 6 | S0009 c10: the key's `n` with no `result` record is not tested (should fix) | fixed: criterion 10 now ends "; for a work item with no `result` record the key's `n` is `0`." |
| 7 | S0002 Interface paragraph, S0007 last rule bullet, `FEATURE.md` Out of scope bullet 2: stale "pending change" wording (note) | fixed: S0002 and S0007 now state the `question_posted` rule as F0006-S0002 states it; `FEATURE.md` reads "F0007 depends on one rule of F0006-S0002's evaluation:". |
| 8 | S0005 step 1: a `close` record with no `result` record is untested (optional note) | not applied: optional, and unreachable at an approval, where a `result` record always exists. |
| 9 | S0005 c19, `FEATURE.md` decision 13: a rejected push of the decision after the reopen (optional note) | not applied: optional, outside the edits asked for; decision 13 stays as it is. |
| 10 | S0003 c17, S0004 c12: `unreachable` is untested (optional note) | not applied: optional; `rejected` covers the failing side and F0001 tests `unreachable` on the wrapper. |
| 11 | S0006 c12: the merge must differ from both parents for `git log -- <path>` (optional note) | not applied: optional, outside the edits asked for. A tester who builds a merge that takes one side's file will not see it listed; consider adding the Tests sentence in the morning. |
| 12 | Demos with `SimpleNamespace` boundaries (note) | no change: the report names none. |
| 13 | S0010 test names; F0008 will change c13 again (optional note) | not applied: optional; belongs in F0008's writer. |
| 14 | Handling rows #1 to #7 of round 1 (note) | no change: each holds as worded. |
| 15 | Handling rows #8 to #37 of round 1 (note) | no change: checked, with the S0005 and S0006 gaps handled above. |
| 16 | Order, names, size, checks (note) | no change. |
| 17 | Demos (note) | no change: every Demo prints what its `Expect:` says once the code exists. |
| - | Feature section: add "except the two cases of decisions 13 and 21" to the Goal's last sentence (suggestion, no replacement text) | not applied: the report gives no text, and the Goal is the human's to word. |
