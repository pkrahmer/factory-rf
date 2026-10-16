# What the board shows after an accepted merge

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

The operator guide's account of a merged acceptance does not say what the feature's status becomes, and in one place it says the wrong thing. In "The hand-over of an acceptance" the **Merge** bullet says that the proposed stories the merge brought stay in the feature's backlog, but not that this makes the feature `incomplete`. The paragraph **Accepted again** then says: "Once the new acceptance's merge is recorded, the feature is `accepted` and not due". That holds only for a merge that brought no proposed stories. The code follows decision 4 of the feature (a waiting story file comes before a recorded result), and so do the status table in "When a feature acceptance is due" and the paragraph **Merged before its approval**. The feature acceptance's demo shows it: after `F0002-A0001` was merged with one proposed story and booked, `factory-watch` showed `acceptance=incomplete`, not `accepted`. An operator who reads the Merge bullet and **Accepted again** expects `accepted` on the board, and the board shows `incomplete`.

This story is documentation only. The tester writes no tests, the coder has nothing to build, and the documenter writes the change from the docs criterion. The human may prefer to make the edit by hand.

## Interface

None: no code changes. The file is `docs/operator-guide.md`, section "The hand-over of an acceptance", the **Merge** bullet and the paragraph **Accepted again**. `docs/project-guide.md` ("The feature acceptance", the item **Status**) is read for consistency and changed only where it contradicts the new text.

## Acceptance criteria

1. `make check` stays green.
2. docs: this story is the documentation, and only `docs/operator-guide.md` changes. Afterwards:
   - The **Merge** bullet says that a merge that brought proposed stories leaves the feature `incomplete` (and not due) until the human has started and archived them. Then the feature is due again, and a new acceptance follows. A merge without proposed stories leaves the feature `accepted`.
   - The paragraph **Accepted again** says that a recorded merge makes the feature `accepted` only when the merge brought no proposed stories, and otherwise `incomplete`. It no longer states `accepted` without that condition.
   - Both places agree with the status table in "When a feature acceptance is due" and with the paragraph **Merged before its approval**, which are left as they are.

## Demo

```bash
awk '/^### /{s=($0=="### The hand-over of an acceptance")} s && /^- \*\*Merge\*\*/' docs/operator-guide.md | grep -c "incomplete"
```
Expect: `1`.

```bash
awk '/^### /{s=($0=="### The hand-over of an acceptance")} s && /^\*\*Accepted again\.\*\*/' docs/operator-guide.md
```
Expect: one line, containing both `accepted` and `incomplete`, and saying when each applies.

## Log (append only)

1. 2026-10-16 human: created.
