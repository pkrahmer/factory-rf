# Feature acceptance

## Goal

When a feature is complete, an acceptance reviewer judges the whole feature, and the human's merge or close of the acceptance's pull request decides the result. An acceptance is a work item of its own, with one agent stage (the acceptance reviewer's) and one approval; it has its own report file, its own cost records and an id of the form `F0001-A0001`. It becomes due by counting the feature's story files only, it sorts after its feature's stories whatever the feature folder's slug, its cost line counts only its own records, and an acceptance merged before its approval, or repeated after more stories were archived, is decided without a loop. Done when a feature with archived stories and a `.gitkeep` becomes due, an acceptance sorts after its stories for a slug that starts with a digit and for a missing slug, a merge books it accepted and a close books it refused with the human's reason, a merge before the approval is booked accepted with an entry that says so, and a repeated acceptance neither trips `reject` nor stays due.

## Scope

- The acceptance's id (`F0001-A0001`), its report file name, and its state in the front matter (`AcceptanceState`: `stories` and `outcome` beside the work item's state), read and written by the work item reader and writer
- When an acceptance is due: story files only, the six statuses (incomplete, due, in flight, merged and not yet recorded, accepted, refused), the due event in the watcher's evaluation, the order after the feature's stories, and the board's acceptance column
- The acceptance stage: opening the acceptance's branch with the report's head, the acceptance reviewer's facts (archived stories, next free story number, the stories' cost from their records), its write paths, and the acceptance's own cost line
- At the approval: the description built by code (recommendation, findings, proposed stories, closing text), the pull request ready for review, the cost table posted once, and the hand-over retried from state
- The human's result: a merge books `accepted` and keeps the proposed stories in the backlog; a close books `refused` with the human's reason first under the recommendation and drops the proposed stories
- A merge before the approval and repeated acceptances (ST2.1, ST2.2, R31), and the dispatcher wiring of the acceptance's handlers

## Out of scope

- Validating the report's sections and the proposed stories' form (left for v2)
- A stopping rule for follow-up stories, and parked backlog stories that hold an acceptance back (left for v2)
- Preventing the reviewer from overwriting an existing backlog story (the write paths allow the feature's whole backlog, as v1's lane did)
- The acceptance reviewer's instructions and the shipped agent files: F0010
- The story's own hand-over, merge, close and send-back: F0007; the claim, the stage protocol and the cost bill: F0004 and F0005

## Stories

- S0001 — The acceptance report as data, and its place in the order
- S0002 — When a feature acceptance is due
- S0003 — The acceptance stage and the acceptance reviewer's facts
- S0004 — The hand-over at the acceptance's approval
- S0005 — A merge accepts, a close refuses
- S0006 — Merged before its approval, and repeated acceptances

## Decisions taken for the human

1. Every acceptance is a work item of its own with the id `F0001-A0001`, numbered per feature (the highest number plus one, a gap never filled), with its own report file `F0001-A0001-acceptance.md` and its own cost records, instead of one report file that each new acceptance overwrites. It sits in `in-progress/` while it is in flight and moves to `done/` when it is booked. (S0001, story text)
2. `AcceptanceState` adds two keys to a work item's front matter, `stories` (the archived stories the report covers, ascending) and `outcome` (`accepted` or `refused`, set exactly when the stage is `done`); the work item reader and writer of F0002 are grown to know them. (S0001, story text)
3. Only story files count when a feature is judged complete: a name that reads as a story id, directly in `backlog/`, `in-progress/` or `done/`. A `.gitkeep`, a note or an acceptance's report never keeps a feature incomplete. (S0002, story text)
4. The status is the first that applies of: in flight, merged and not yet recorded, incomplete, the recorded result (accepted or refused) when its report covers exactly the archived stories, and due. A consequence: after an accepted merge that brought proposed stories, the feature shows as incomplete until the human has started and archived them, and then it is due again. (S0002, story text)
5. A pipeline definition without an `acceptance_stage` has no acceptances: nothing is ever due and the board's acceptance column stays empty. (S0002, story text)
6. Opening an acceptance pushes the report's head on a branch `work-item/F0001-A0001` and nothing else: no `created` entry of a human (its journal starts with the stage protocol's `started` entry), no claim and no pull request; the stage protocol takes the acceptance from there like any other work item. (S0003, story text)
7. The next free story number counts every story file in the feature's backlog, in progress and done, and is written with four digits. (S0003, story text)
8. The acceptance reviewer's facts are three lines appended to its prompt: `Archived stories: ...`, `Next free story number: ...` and `Cost of the stories: ...`, the cost computed from the archived stories' cost records only. (S0003, story text)
9. The pull request's description at the approval has four parts, `## Recommendation`, `## Findings in short`, `## Proposed stories` and the closing text; a part the report lacks reads `none`. The findings are the reviewer's last `result` entry as written. (S0004, story text)
10. The closing text names no merge method (a merge commit, a squash or a rebase all work), and says that comments written while the acceptance waits are only recorded in its journal. (S0004, story text)
11. The cost table is posted once on the acceptance's pull request at the hand-over, with a key, so a retry posts it no second time. (S0004, story text)
12. A merge books the acceptance `accepted` whatever the recommendation says. (S0005, story text)
13. The reason of a refusal is the human's comments after the reviewer's last result, unchanged and joined with one space (`no reason given` when there are none); it becomes the first paragraph under the recommendation, as `Refused by the human on <date>: <reason>`. (S0005, story text)
14. A refusal keeps the report and its cost records on the main branch at `done/` and drops the proposed stories, which were only on the branch; a merge keeps them in the feature's backlog. The report is added with a `## Recommendation` section when the reviewer wrote none. (S0005, story text)
15. An acceptance merged before its approval is booked `accepted` with the journal entry `done (pull request merged before approval); cost: ...`; "before approval" means a stage before the first stage with `approval: true`. (S0006, story text)
16. A repeated acceptance is a new work item `F0001-A0002`; the earlier report and its cost records stay as they were. (S0006, story text)
