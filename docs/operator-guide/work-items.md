# Work items: acceptances, approvals, merges, closes and leases

A topic of the [operator guide](README.md). It is for the operator of an [instance](../project-guide/glossary.md).

It tells you what the factory does with a [work item](../project-guide/glossary.md) after the agents have worked on it: how a feature's [acceptance](../project-guide/glossary.md) becomes due, what the hand-over at the [approval](../project-guide/glossary.md) shows you, and what your merge or close of a pull request makes the factory do. It also covers what the factory does after a [crash](../project-guide/glossary.md) or an expired [lease](../project-guide/glossary.md). Your acts on a work item are on its pull request: comment, close or merge. Exact texts, commit subjects and error names are in *Reference* at the end.

The [stops](../project-guide/glossary.md) and the questions that these sections name are in [stops.md](stops.md).

## When a feature acceptance is due

The factory starts a [feature](../project-guide/glossary.md)'s acceptance when the feature is complete and no recorded report covers exactly its archived stories. It reads only the files on `origin/main` and the remote acceptance branches, never your checkout. Without an `acceptance_stage` in the [pipeline definition](../project-guide/glossary.md) nothing is ever due.

A feature is complete when it has at least one [story](../project-guide/glossary.md) file in `done` and no story file waits in the [backlog](../project-guide/glossary.md) (`backlog/`) or in `in-progress`.

- Only story files count (named `<feature id>-S<n>-<slug>.md`), and only directly in `backlog/`, `in-progress/` or `done/` of the feature. A story file in a subfolder, such as `done/old/`, neither archives a story nor keeps the feature incomplete.
- A `.gitkeep`, a `README.md`, a note and an acceptance's report beside the stories never keep a feature incomplete and never make it complete.

A report covers the archived stories when it is at `done` on `main` and its `stories` list equals the set of archived stories. A report with fewer or more stories does not cover them. So a story archived after an acceptance makes the feature due again.

The status of a feature is the first row of this table that applies:

| Status | Meaning |
| --- | --- |
| `in_flight` | A report is on its own remote branch `work-item/<acceptance id>` and not yet on `main`. |
| `merged_unrecorded` | A report is on `main` but not at `done`: the acceptance was merged and its result is not recorded yet. |
| `incomplete` | The feature has no archived story, or a story file waits in `backlog` or `in-progress`. A recorded result does not stand while a story file waits. |
| `accepted` or `refused` | A report at `done` covers exactly the archived stories; this is its outcome. With several covering reports the highest id decides. |
| `due` | None of the above: the acceptance is waiting to be started. |

Three cases are ignored or refused:

- A remote branch `work-item/<acceptance id>` without a report file in `in-progress/`, and the branch of a story, are ignored.
- A report on `main` whose front matter cannot be read as an acceptance's is a format error that names the report's path.
- If two folders share a feature id, the first in name order counts.

### What the acceptance reviewer is told

The acceptance reviewer cannot read the factory's state directory, so the factory puts the disk into its prompt. When it composes the prompt, it records the disk with the occasion `acceptance` and adds two lines after the cost line:

- `Disk now: ...`
- `Disk at the previous record: ...`

The second line is the latest earlier record of any occasion, such as the instance's start or an earlier acceptance. A rerun of the acceptance compares with its own earlier record. Without an earlier record the line says `none`. The report compares the two and names growth that the feature's changes do not explain. Without the disk, the record log or the settings the lines are left out.

The prompt also has the line `Human interventions of the stories: ...` right after `Cost of the stories: ...`. It is your line of the cost table (see "The cost table" in [records.md](records.md)) summed over the archived stories, not over earlier acceptances or stories still in `backlog`. A damaged archived story file adds nothing.

### The order of the work

- The next acceptance id of a feature is one above the highest acceptance id among its reports on `main` and on remote acceptance branches. `factory-watch` and the board command use the same rule.
- A running acceptance is a work item like a story and is picked in the same order, by id. A waiting work item and a held [claim](../project-guide/glossary.md) come first, as for stories.
- A due acceptance is not started before the feature's own stories. The next event is `acceptance_due:<feature>` only when no story of that feature or of an earlier feature can run. It still comes before the stories of a later feature.
- `factory-watch` shows the event as `event: acceptance_due:<feature>  acceptance of <feature> is due`.

## The hand-over at the approval

When a work item reaches an approval [stage](../project-guide/glossary.md), the factory shows you on its pull request what to decide. It does this when it handles the `hand_over` event, in this order:

1. **It replaces the pull request description.** What you or the factory wrote there before is gone. The new description has these sections, each headed `## <name>`:
   - Description and Acceptance criteria: the story's own sections, verbatim.
   - Tests, Review, Documentation and Smoke test: the text of the latest `result` entry of the tester, reviewer, documenter and smoke tester.
   - Commits: a code block with one line per commit beyond `main`, the first seven characters of the id and the subject.
   - A closing paragraph: a merge accepts the story, and a close with a comment sends it back.

   A story section that is missing or empty, and a report whose [role](../project-guide/glossary.md) never recorded a `result`, show `none`. The reviewer's entry under Review ends with the earlier tests the story changed and the leave for each. The reports are found by the [journal](../project-guide/glossary.md)'s data (speaker and kind), never by the text of an entry.
2. **It marks the pull request ready for review.** A draft says the factory works; ready says you decide.
3. **It posts the cost table**, headed `Cost of this work item so far`, read from the [cost records](../project-guide/glossary.md) committed on the work item's branch (see *What a work item cost: `factory-bill`* in [records.md](records.md)). The `Human:` line follows it (see "The cost table" in [records.md](records.md)). The post is keyed by the number of the latest `result` entry, so a repeat does not post it twice.
4. **It records `handed_over = <stage>`** in the work item and pushes, in one commit. This comes last.

The stage that reaches the approval writes the description first, before its push. The hand-over on the next [tick](../project-guide/glossary.md) writes it again, unchanged, then marks the pull request ready and posts the cost table. If the stage's write failed, the log says `pull request #<number>: description not written before the push` and the hand-over writes it.

A work item whose `handed_over` already equals its stage is left alone: no description change, no post, no commit. A stage that is not an approval, or a work item without a pull request, cannot be handed over; the factory changes nothing.

### The hand-over of an acceptance

When a feature's acceptance reaches its approval stage, you see the same steps on its pull request: the draft turns ready, the description is replaced, the cost table is posted once and `handed_over = <stage>` is recorded in the report. No agent writes the description. The cost table is the one of the acceptance's own cost records, keyed by the number of the latest `result` entry as for a story.

The description has four parts, joined by an empty line:

1. `## Recommendation`: the report's own `## Recommendation` section.
2. `## Findings in short`: the text of the acceptance reviewer's latest `result` entry, without its `<speaker>: ` prefix.
3. `## Proposed stories`: the report's `## Proposed stories` section.
4. A closing text that says what you can do.

A part whose section is missing or empty, and findings with no `result` entry of the reviewer, show `none`. The closing text names no merge method; any method the hosting service offers works.

### What your act does to an acceptance

The result is yours, whatever the acceptance reviewer recommended: a merge of an acceptance that recommended `not accepted` still books it accepted.

- **Merge** accepts. The report moves from the feature's `in-progress/` folder to its `done/` folder with its cost records file. Its state says `done` and `accepted`, and its journal gets one `done` entry, `done (pull request merged); cost: <the acceptance's own cost>`. The factory deletes the acceptance's branch, on the remote and locally. It does all this in one tick.
  - The proposed stories your merge brought into the feature's backlog stay there untouched. You refine them before you start any. While they wait, the feature is `incomplete` and not due. Once you have started and archived them it is due again, and a new acceptance follows.
  - A merge that brought no proposed stories leaves the feature `accepted`.
- **Close**, with a comment saying why, refuses. It works at any stage: while the reviewer works or asks, at the approval, or after a failed hand-over. The factory does it in one tick.
  - The report is written to `main` at `done` as refused, and `blocked` is cleared.
  - The proposed stories are discarded, because they were only on the branch.
  - The feature counts as not accepted until another story is archived and a new acceptance runs.
  - The report has `Refused by the human on <date>: <your comment>` as the first paragraph under its `## Recommendation`, and a `done` entry `done (pull request closed by the human); cost: <cost>`. Its cost records file is copied beside it.
  - Your reason is your comments written after the reviewer's last result, each stripped of surrounding whitespace, blank ones skipped, joined with one space and otherwise copied unchanged. The factory never interprets them. With no comment the reason is `no reason given`.
- **A comment** is not answered while the acceptance waits; it goes into the report's journal.

Each acceptance has its own report and its own cost records, so the cost on its `done` entry counts only that acceptance's runs, never an earlier one's.

**Merged before its approval.** You may merge an acceptance's pull request while the reviewer still works or the acceptance waits with a question. The merge is still your decision: the acceptance is booked `accepted` as above, a waiting question is cleared, and the `done` entry says `done (pull request merged before approval); cost: <the acceptance's own cost>`. A merge at the approval stage, before the hand-over, gets the ordinary entry. The merge brought the proposed stories into the feature's backlog, so the feature is `incomplete` and not due until you have refined and archived them.

**Accepted again.** When another story is archived after an acceptance, no report covers the stories any more and the feature is due again. The next acceptance is a new work item with its own branch, report and cost records; the earlier report and its cost records stay as they were. Until the new merge is recorded, the feature is `merged_unrecorded`. After it, the feature is `accepted` if the merge brought no proposed stories and `incomplete` if it brought some. After a refusal the same happens once another story is archived.

**No loop.** Whatever stage an acceptance has reached, your merge or close is booked in one tick, without an agent run. The stage run sees the merged or closed pull request and hands it to the acceptance's own handler, never to a story's. Once the booking is on `main`, further ticks find nothing to do and yield `idle`: no commit, no post. A refused feature stays not due until another story is archived. An accepted one stays not due unless the set of archived stories changes.

**What a close records first.** Before the booking, your unread comments are copied into the report's journal on the acceptance's branch. One `close` entry follows (speaker `human`, text `closed the pull request.`, dated today in UTC), and the factory pushes it. An acceptance ends at its first close: a report that already holds a `close` entry of yours gets no second one. The branch is deleted last, on the remote and locally.

**A close or a merge handled again.** A kill at any point is harmless. The recorded close is not recorded twice, a report already in `done/` is not booked twice, and a rerun after the branch is gone only finds the report in `done/`. After a kill only the branch deletion of a merge is repeated.

- If the branch is gone and the report is in neither place, the factory changes nothing and counts an error. A close names it `no report on the branch or the main branch`; a merge names it `no report on the main branch`, which it raises when the report is in neither `in-progress/` nor `done/` on `main`.
- If `main` moved since the last fetch, the push is rejected and the event is retried. A rejected close push comes after the close is recorded, and the branch stays until the booking is pushed.
- If the remote refuses to delete the branch, the booking is already pushed. The branch stays, and the error is counted.

These errors are counted and reported as in "An event that keeps failing" in [stops.md](stops.md).

A hand-edited report with neither a `## Recommendation` nor a `## Journal` section gets a `## Recommendation` section at the end of its body, followed by an empty `## Journal` that holds the `done` entry. Reports the factory writes always have a journal.

### When the hand-over fails or is killed

Every step before the record can be repeated safely, for a story and for an acceptance alike, and nothing is recorded until they have all happened. A failure or a kill anywhere leaves `handed_over` unset. The hosting service may be down, or the factory may die after the post. The factory raises the event again on the next tick and completes the hand-over. You do nothing, and the cost table is never posted twice.

A hand-over that fails every time is a counted error like any other. It is tried on three ticks, then one report is posted on the pull request and the event is capped (see "An event that keeps failing" in [stops.md](stops.md)).

## A stale branch is deleted by the tick

After the restore of the checkout and before it looks at any work item, every tick deletes stale branches `work-item/<id>` on the remote:

- The branch of each story whose file is in `backlog/` on `origin/main`. It is the leftover of a discard (see "A close before the approval discards the story") that was killed after it pushed the move, or whose deletion the remote refused.
- The branch of each story whose file is in `done/`. It is the leftover of a merge (see "A merge archives the story") that was killed or refused between the archive and the deletion.

You do nothing after a kill. The factory logs `deleted stale branch <name>: its story is back in the backlog`, or `its story is done` for a merged story.

- **A pull request still open on the branch** is closed by the hosting service when the branch goes. GitHub does so. The factory makes no call to the hosting service and posts nothing. A pull request that is already closed stays as it is.
- **A refused or unreachable deletion** is no stop. The log gets `could not delete stale branch <name>: rejected` (or `unreachable`), and the next tick tries again.
- **Start the story again only after the tick has deleted the branch.** A story you start before that finds the old branch with its old state and bill, and is discarded again. If the remote refuses deletions, lift the refusal and wait for a tick. The log line confirms it.
- **A branch is kept** when the same id also has a story file in `in-progress/` (two work items with one id are reported as a duplicate), and when no story file of its id is in `backlog/` or `done/` on `origin/main`. A move to `backlog/` that is not pushed to `main` deletes nothing. Branches that are not `work-item/<id>`, such as `main` and your own, are never touched.

## A merge archives the story

A merge of a story's pull request, by any method (merge commit, squash or rebase), accepts the story as it is, at whatever stage it has reached: working, waiting for you, or at an approval stage. The factory then archives it on `main` in one commit:

- The story file moves from `in-progress/` to `done/` of its feature. Its cost records (`<story>.costs.jsonl`) move beside it when it has them.
- Its stage becomes `done`, with no wait and no claim, whoever held the claim. Its counters and journal stay as they were.
- One journal entry is added, from `factory`, kind `done`: `done (pull request merged); cost: <the bill>`. The bill counts every cost record of the story, a died run and an unknown cost included. A story with no cost records gets the bill of none.

The factory posts nothing on the pull request. After the archive is pushed it deletes the work item's branch, on the remote and in its checkout. A branch that is already gone, because the hosting service deleted it, is no error. The factory trusts the merge: it asks nothing and checks nothing.

A merge found when the story's stage is due to run is handled first. The factory reads the pull request before every agent run, so a story you merged while its stage waited is archived without that run.

When it goes wrong, you do nothing in any of these cases:

- **The push of the archive is rejected**, because `main` moved since the checkout. Nothing is archived and the branch is kept. The next tick fetches and archives the story then.
- **The factory dies before the push.** `main` and the branch are as they were, and the story is archived once on the next tick.
- **The factory dies after the push, or the remote refuses to delete the branch**, for example when the remote forbids deletions. The archive stays on `main` and the story is under `done/`, so no event is raised for it again. The branch `work-item/<id>` is left on the remote, and nothing in the factory reads it meanwhile. The next tick deletes it (see "A stale branch is deleted by the tick"). An unreachable remote during the deletion leaves the branch in the same way.

## A close before the approval discards the story

When you close a story's pull request while the story is at any stage that is not an approval stage, you have said you do not want this version. The factory discards the story on `main` in one commit:

- The story file moves from `in-progress/` back to `backlog/` of its feature. It is moved, not rewritten: it is the text you wrote on `main`, whatever the work item's branch held.
- The commit changes nothing else.

After that push the factory deletes the work item's branch, on the remote and in its checkout, and with it the branch's journal and cost records. So a story you start again begins with an empty bill. A branch that is already gone is no error. The factory posts nothing, and the pull request stays closed.

A close at an approval stage is a send-back, not a discard; see the next section.

A close found when the story's stage is due to run is handled first. The factory reads the pull request before every agent run, so a story you closed while its stage waited is discarded without that run.

When it goes wrong, you do nothing in any of these cases:

- **The push of the move is rejected**, because `main` moved since the checkout. Nothing is discarded and the branch is kept. The next tick fetches and discards the story then.
- **The factory dies before the push.** `main` and the branch are as they were, and the story is discarded once on the next tick.
- **The factory dies after the push, or the remote refuses or cannot be reached for the deletion.** The story is under `backlog/` on `main`, so no event is raised for it again, and the branch `work-item/<id>` is left on the remote. The next tick deletes it (see "A stale branch is deleted by the tick"). If the remote keeps refusing, lift the refusal; the tick tries again every tick.

## A close at the approval sends the story back

When you close the pull request of a story that waits at an approval stage, you have said "not like this". The factory sends the story back to the second stage in the approval's `next`, which is `doing` in the usual pipeline.

An approval with only one stage in `next` cannot be sent back. The same holds for a story without a pull request number. In both cases the factory changes nothing and records nothing.

The factory works in this order, and each step that changes the work item is pushed on its own:

1. **It records the close.** Your unread comments are copied into the journal, a `close` entry (speaker `human`, text `closed the pull request.`, dated today in UTC) is added, and `handed_over` is cleared. A story that already holds a `close` entry since its latest `result` gets no second one, so a retry does not close twice. After an earlier send-back and a new stage result, a new close is recorded again.
2. **It reopens the pull request, as a draft.**
3. **It records the decision.** A `send_back` entry (`sent back to doing, round 3.`) is added, `stage` is set to the target, [`round`](../project-guide/glossary.md) goes up by one and the claim is released. When a question is needed, a `question` entry is added with `blocked` set to `send_back`.
4. **It rewrites the labels** of the pull request to the new stage, so it does not keep `stage:approval`.

The factory posts nothing itself in these steps. A question is posted by the `ask` handler, like the others in "The factory's own questions" in [stops.md](stops.md).

### The reason and the round cap

A comment of yours counts as the reason when it was written after the latest `result` of the story, whether copied earlier or at the close. The factory reads only the journal's records, never what you wrote, so the text of the comment does not matter.

With a reason, and with the new round within the [round cap](../project-guide/glossary.md) (`round_cap`) of the stage that hands over to the approval, the story simply goes back to work with your comments as the findings. That stage is the first one in the pipeline definition that has a cap.

Otherwise the factory asks, and `blocked` is `send_back`. The question starts with one of these texts and goes on with the options below:

- You closed without a comment: `The pull request was closed without a comment. `
- The new round is past the cap: `This story has now been sent back <n> times, more than <cap>. ` Past the cap this text wins, with or without a reason.

The question has three options, all of them things you can already do:

1. Comment what should change; the story is reworked with exactly that.
2. Close the pull request again to discard the story: it goes back to the backlog as you wrote it, and its branch is deleted.
3. If closing was a mistake: mark the pull request ready for review and merge it, which accepts the story as it is.

### When something fails or is killed

- **The reopen fails.** The close stays recorded, and the failure is a counted error. The next attempt reopens and records the decision without a second `close` entry. A comment you write in between is copied then and counts as the reason.
- **The push of the decision is rejected**, because you pushed to the branch after the reopen. The close and your commit stay on the branch. The next attempt sends the story back once.
- **The labels cannot be set.** The decision stays recorded. The label is stale until the next stage's result commit rewrites it.
- **The factory is killed between the reopen and the recording of the decision.** The pull request is open again as a draft, but the story is still at the approval, so it is handed over again there and you have to repeat the close. Because the close is already recorded, the repeat adds no second `close` entry.

## Branch deletion on merge must be off

The factory reads a work item's state from its branch `origin/work-item/<id>`. A story in `in-progress/` on `main` with no such branch is read as a new start: it is at the first stage with fresh counters, whatever its file says.

With the hosting setting that deletes head branches on merge turned on, a merged story whose file is still in `in-progress/` loses its branch and starts again. Turn it off. On GitHub (marked for GitHub; not run here):

1. Open the repository's *Settings*, section *General*.
2. Under *Pull Requests*, clear *Automatically delete head branches*.

## An idle tick that is not empty

When the factory does nothing, the evaluation may still have a reason. An `idle` result names it in its detail:

- A work item waits for you (blocked, or at an approval stage) and its pull request is open with nothing new. While one waits, no new work starts, even if other work items could run. Answer, comment or merge on its pull request.
- Another instance holds a claim whose lease has not run out. Only one agent runs at a time, so the factory waits for that instance or for the lease to expire.

Neither is a fault. With neither, an idle tick means no work item has anything to do.

## A stage changed by hand

The factory changes a work item's stage only along the `next` lists of the pipeline definition, and archives to `done` from an approval stage. If someone edits `stage` in a work item's file on its branch to another one, the factory notices on its next tick. It reports a `reject` event: "stage changed from `<from>` to `<to>`, which the pipeline definition does not allow".

It judges the last commit on the branch, beyond `origin/main`, that touched the story's file. A hand-made change that a later commit on the branch buried is not seen. A push to the branch makes the factory try again, and the `reject` returns for as long as that newest commit is the illegal change.

### What the factory does when it moves a stage back

The factory corrects the change on the work item's branch, and only there; `main` is never written. It makes one new commit on top of the branch's head, also when later commits touched only other files. The commit:

- sets `stage` back to the one before the illegal change (`from`);
- clears the claim, since a claim belongs to the stage at the head and `to` is no longer it;
- appends a journal entry from `factory` of kind `move_back`: `illegal stage change <from> -> <to>, moved back.`

The commit's subject is `work item <id>: stage <to> -> <from>, moved back`. Search the branch's history for `moved back` to find the corrections. When the work item has a pull request, the factory also posts one note there and sets the `stage:<from>` label again, so the label does not keep the illegal stage. The note reads:

```text
The stage was changed from <from> to <to>, which factory/pipeline.yml does not allow; it is back at <from>.
```

If the factory is killed in the middle, do nothing. The note is posted first and keyed by the number of the entry to come, so the next tick makes the correction again from the same event and posts no second note. A failing label call after the push is an error of the event; the correction stays on the branch.

A `reject` that cannot be corrected is refused, and nothing is written or posted. That is the case when the newest commit:

- is a merge commit,
- changed no stage,
- has a parent without the story's file, or with an unreadable one,
- or is itself a correction.

These are not counted as an illegal change:

- The opening commit, whose parent is the story as you started it. A story started at `review` is not rejected. So the stage a work item branch you created by hand starts with is never judged, whatever it is. The opening commit is the first commit that gives the file its front matter, or one whose previous version cannot be read. Later stage changes on such a branch are judged like any other.
- A merge commit on the branch.
- The factory's own correction, which moves the stage back and appends a journal entry of kind `move_back`.
- A merge of the pull request by any method. The factory reads the pull request first, and a merged pull request is `merged`, never an illegal change.

### Never edit a running work item on main

Do not edit the file of a work item in `in-progress/` on `main`. Answer in its pull request instead. The agents amend the story on its branch (the description, the criteria), and your edit on `main` changes the same file. At the next stage start the factory merges `main` into the branch, the merge conflicts, and the stage [stalls](../project-guide/glossary.md) with the reason `merge_conflict`. When it has happened, revert the edit on `main`; the stage then starts again from the branch's story.

## A restart during a stage

If the factory dies while a stage runs and is started again with the same instance name, it finds its own claim on the work item's branch at its first look. It treats the claim as a crash and does not wait for the lease.

In one call, the factory:

- throws away everything the dead stage did that is not on the remote: uncommitted and untracked files, commits that were never pushed, and the cost records of the discarded agent runs. Records of earlier stages stay;
- records the crash in one commit on top of the remote's head: the claim is cleared, `crashes` goes up by one, and the journal gets an entry of kind `crash`: "crash 1: the run of stage doing ended without a result. Its work is discarded back to commit <commit>.";
- reruns the stage at once, unless the crash cap is reached (see "The crash cap"). `attempts` is not raised: a crash is not charged as a failed attempt;
- posts nothing on the pull request while it is below the cap.

A commit that you pushed to the branch while the stage ran is on the remote, so it stays. The journal entry names the commit the discard went back to. The stage-start commit and its `started` entry stay in the history too.

If the push of the crash commit is rejected because someone pushed in between, the event is a counted error as under "An event that keeps failing" in [stops.md](stops.md). A push to the branch makes the factory look again. A claim of another instance name is handled only once its lease has expired (see "An expired lease").

The recovery is proved by tests that kill the factory at each of its six kill points and walk each of the thirteen fault paths. They are listed in *Reference*.

### The crash cap

`crash_cap` in the pipeline definition (default 2) is the number of crashes after which the factory asks you instead of rerunning. The count is `crashes` in the work item's state. A forward move of the stage and your answer reset it, and a rework move and a stall keep it. So it counts the crashes since the last forward move.

When a crash brings `crashes` up to the cap, the stage is not rerun. The same commit that records the crash records a question by `factory` and sets `blocked` to `crash_cap`. The factory pushes the commit and only then posts the question on the pull request, once. If the work item has no pull request yet, it opens a draft first. The question reads:

```text
Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
```

- A comment you write after the question was posted ends the wait: `crashes` goes back to 0, `attempts` stay, and the stage runs again.
- Closing the pull request discards the story.
- A boundary error after the factory pushed its claim leaves the claim on the remote. Such an error is one of the hosting service, the agent runtime, a [project command](../project-guide/glossary.md), git or a rejected result push. The next look treats the claim as a crash and reruns the stage. If that fails again, it is the second crash and ends here with this question. It does not end in the error report of "An event that keeps failing" in [stops.md](stops.md), because each rerun is a new event on a new remote state.
- If posting fails, the question stays recorded and pushed, and the failure is a counted error of the event. The `ask` handler posts a question lost between its record and its post again when the work item has a pull request. For a work item without one it is not posted again.

## An expired lease

When an instance finds a claim of another name whose lease has run out, it treats the holder as gone and takes the stage over. The claim's age must be at least its `lease_duration`, 60 minutes by default. Before that, the factory waits for the claim and touches nothing.

In one call, it does what a restart does (see "A restart during a stage"):

- It throws away what is not on the remote and records the expiry in one commit. The claim is cleared, `crashes` goes up by one, and the journal gets an entry of kind `expiry`: "expiry 1: the lease of stage doing ran out. Its work is discarded back to commit <commit>."
- `attempts` is not raised. An expiry is a crash, not a failed attempt, and it counts toward the crash cap.
- After the push it posts a note on the pull request, and opens a draft for it if there is none: "The run that held this stage ended without finishing: its lease expired (crash 1 of 2). Retrying."
- Then it reruns the stage itself. At the crash cap it does not. The note then reads "... (crash 2 of 2). The factory does not rerun it and asks you instead." and the question of "The crash cap" follows on the same pull request.

The notes of the factory say "retrying" only where a rerun follows. A note without it means the factory has stopped and waits for you.

If the post of the note fails, the expiry stays recorded and pushed, the failure is a counted error of the event, and the note is not posted again. The stage is not rerun in that call; the next look finds no claim.

Your own claim is never an expiry, however old it is: that is the restart case. A claim whose lease has not run out is refused.

## Claims, leases and the clock

An instance claims a stage by pushing the stage-start commit. The [claim](../project-guide/glossary.md) records the instance's name, the start time and the role's `lease_duration`. That is 60 minutes unless the pipeline definition says otherwise, per role. The claim keeps the value it was made with: changing `lease_duration` in the definition affects new claims only, never one that is running.

- Your own claim is recognised whatever its age. After a restart with the same instance name, the instance reruns its stage at once and does not wait for the lease. Only `factory-watch` judges it by the lease, as a look from outside: within the lease it shows the claim as held, since the tick may be running that stage.
- Another instance's claim is waited for until its lease has run out, when its age reaches `lease_duration`. Then it counts as expired and the factory handles it as in "An expired lease".
- Instances need a synchronised clock (NTP). Expiry compares the start time recorded by the claiming instance with the checking instance's own clock, so a clock that is off by minutes makes a lease end early or late.

## Reference

### Commit subjects

| Act | Subject |
| --- | --- |
| Hand-over recorded | `work item <id>: handed over at <stage>` |
| Merge archived, story or acceptance | `work item <id>: merged, archived` |
| Close at a stage before the approval | `work item <id>: closed before the approval, back in the backlog` |
| Close of an acceptance, refused | `work item <id>: closed, refused` |
| Close recorded, story at the approval or acceptance | `work item <id>: close recorded` |
| Story sent back | `work item <id>: sent back` |
| Illegal stage change corrected | `work item <id>: stage <to> -> <from>, moved back` |

The commits of a merge or a close change only the report and its cost records file (acceptance booking), the story file and its cost records file (story archive), or only the story file (discard at a close before the approval; its cost records go with the branch).

### Journal entries the factory writes

| Kind | Speaker | Text |
| --- | --- | --- |
| `done` | `factory` | `done (pull request merged); cost: <cost>`, or `done (pull request merged before approval); cost: <cost>` for an acceptance, or `done (pull request closed by the human); cost: <cost>` for a refused acceptance |
| `close` | `human` | `closed the pull request.` |
| `send_back` | `factory` | `sent back to <target>, round <n>.` |
| `move_back` | `factory` | `illegal stage change <from> -> <to>, moved back.` |
| `crash` | `factory` | `crash <n>: the run of stage <stage> ended without a result. Its work is discarded back to commit <commit>.` |
| `expiry` | `factory` | `expiry <n>: the lease of stage <stage> ran out. Its work is discarded back to commit <commit>.` |

### Error names

The factory counts these errors and reports them as in "An event that keeps failing" in [stops.md](stops.md). The log and the report name them as follows.

| Name | Where it arises |
| --- | --- |
| `CannotHandle` | A hand-over for a stage that is not an approval or a work item without a pull request. A close at an approval with one stage in `next`, or without a pull request number. An acceptance close when the report is on neither the branch nor `main` (`no report on the branch or the main branch`); an acceptance merge when the report is in neither `in-progress/` nor `done/` on `main` (`no report on the main branch`). A `reject` that cannot be corrected. |
| `PushFailed` | A push is rejected because `main` or the branch moved, or the remote refuses a branch deletion. The outcome is `rejected`. |
| `HostingServiceError` | The reopen of a pull request fails at a send-back. |

### Log lines

| Line | When |
| --- | --- |
| `pull request #<number>: description not written before the push` | The stage that reached the approval could not write the description; the hand-over writes it. |
| `deleted stale branch <name>: its story is back in the backlog` | A stale branch of a story in `backlog/` is deleted. |
| `deleted stale branch <name>: its story is done` | A stale branch of a story in `done/` is deleted. |
| `could not delete stale branch <name>: rejected` | The remote refused the deletion. It says `unreachable` when the remote could not be reached. |

### Settings and fields

| Name | What it does | Default | Example |
| --- | --- | --- | --- |
| `acceptance_stage` | Names the stage that runs a feature's acceptance. Without it nothing is ever due. | none | `acceptance` |
| `crash_cap` | The number of crashes after which the factory asks you instead of rerunning the stage. | 2 | `3` |
| `lease_duration` | Minutes after which a claim of another instance counts as expired. Set per role in the pipeline definition. | 60 | `90` |
| `round_cap` | The rounds a stage allows. The send-back compares the new round with the cap of the stage that hands over to the approval. | none | `3` |

### The recovery tests

The cases and paths of the recovery tests are listed in the sections *Kill points* and *Fault-injection paths* of [README.md](../project-guide/README.md).
