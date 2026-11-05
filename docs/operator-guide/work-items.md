# Acceptances, approvals, merges and leases

A topic of the [operator guide](README.md).

## When a feature acceptance is due

A feature's acceptance is due when the feature is complete and no recorded report covers exactly its archived stories. This is worked out from the files on `origin/main` (and the remote acceptance branches) alone, never from the checkout's work tree or a local branch. It applies only when the pipeline definition has an `acceptance_stage`; without one nothing is ever due.

A feature is complete when:

- it has at least one story file in `done`, and
- no story file waits in `backlog` or `in-progress`.

Only story files count (`F0001-S0001-name.md`), and only directly in `backlog/`, `in-progress/` or `done/`: a story file in a subdirectory (`done/old/F0001-S0001-name.md`) neither archives a story nor keeps the feature incomplete. A `.gitkeep`, a `README.md`, a note and an acceptance's report beside the stories never keep a feature incomplete, and never make it complete.

A report covers the archived stories when it is at `done` on `main` and its `stories` list equals the set of archived stories. A report that lists fewer or more stories does not cover them, so a story archived after an acceptance makes the feature due again.

The status of a feature is the first of these that applies:

| Status | Meaning |
| --- | --- |
| `in_flight` | A report is on its own remote branch `work-item/<F0001-A0001>` and not yet on `main`. |
| `merged_unrecorded` | A report is on `main` but not at `done`: the acceptance was merged and its result is not recorded yet. |
| `incomplete` | The feature has no archived story, or a story file waits in `backlog` or `in-progress`. A recorded result does not stand while a story file waits. |
| `accepted` or `refused` | A report at `done` covers exactly the archived stories; this is its outcome. With several covering reports the highest id decides. |
| `due` | None of the above: the acceptance is waiting to be started. |

A remote branch `work-item/F0001-A0001` without a report file in `in-progress/`, and the branch of a story, are ignored. A report on `main` whose front matter cannot be read as an acceptance's is a format error naming the report's path. If two directories share a feature id (`F0002-a`, `F0002-b`), the first in name order counts.

The acceptance reviewer cannot read the factory's state directory, so the factory tells it the disk in its prompt. When an acceptance's prompt is composed, the factory records the disk with occasion `acceptance` and adds two lines after the cost line: `Disk now: ...` and `Disk at the previous record: ...`. The second is the latest earlier record of any occasion (the instance's start or an earlier acceptance; a rerun of the acceptance compares with its own earlier record), or `none`. The report compares them and names growth that the feature's changes do not explain. Without the disk, the record log or the settings the lines are left out.

The prompt also carries the line `Human interventions of the stories: ...` right after `Cost of the stories: ...`: the human's line (see "The cost table" in [records.md](records.md)) summed over the archived stories, not over earlier acceptances or stories still in `backlog`. A damaged archived story file adds nothing.

The next acceptance id of a feature is one above the highest acceptance id among its reports on `main` and on remote acceptance branches. The watcher's evaluation and the board command use the same rule.

A running acceptance is a work item like a story and is picked by the same order, by id. A due acceptance is not started before the feature's own stories: the next event is `acceptance_due:<feature>` only when no story of that feature (or of an earlier feature) can run; it still comes before the stories of a later feature. A waiting work item and a held claim come first, as for stories. `factory-watch` shows the event as `event: acceptance_due:F0002  acceptance of F0002 is due`.

## The hand-over at the approval

When a work item reaches an approval stage, the factory shows you on its pull request what to decide. The factory does this when it handles the `hand_over` event.

The description is written first by the stage that reaches the approval, before its push, and again, unchanged, by the hand-over on the next tick, which then marks the pull request ready and posts the cost table. The same holds for an acceptance. If the stage's write failed, the factory logs `pull request #<number>: description not written before the push` and the hand-over writes it.

It does these things, in this order:

1. **Replaces the pull request description.** What you or the factory wrote there before is gone. The new description has these sections, in this order, each headed `## <name>`: Description and Acceptance criteria (the story's own sections, verbatim), Tests, Review, Documentation and Smoke test (the text of the latest `result` entry of the tester, reviewer, documenter and smoke tester), and Commits (a code block with one line per commit beyond `main`: the first seven characters of the id and the subject). A story section that is missing or empty, and a report whose role never recorded a `result`, show `none`. The reviewer's entry under Review ends with the earlier tests the story changed and the leave for each. The reports are found by the journal's data (speaker and kind), never by the text of an entry. The description ends with a paragraph saying that a merge accepts the story and that a close with a comment sends it back.
2. **Marks the pull request ready for review.** A draft says the factory works; ready says you decide.
3. **Posts the cost table**, headed `Cost of this work item so far`, read from the cost records committed on the work item's branch (see "What a work item cost"), followed by the `Human:` line (see "The cost table" in [records.md](records.md)). The post is keyed by the number of the latest `result` entry, so a repeat does not post it twice.
4. **Records `handed_over = <stage>`** in the work item and pushes, in one commit with the subject `work item <id>: handed over at <stage>`. This comes last.

A work item whose `handed_over` already equals its stage is left alone: no description change, no post, no commit. A stage that is not an approval, or a work item without a pull request, is a `CannotHandle` for `hand_over` and changes nothing.

### The hand-over of an acceptance

When a feature's acceptance reaches its approval stage, you see the same steps on its pull request: the draft turns ready for review, the description is replaced, the cost table is posted once and `handed_over = <stage>` is recorded in the report with the commit subject `work item <id>: handed over at <stage>`. The factory does it when it handles the acceptance's `hand_over` event. No agent writes the description. The cost table is the one of the acceptance's own cost records, keyed by the number of the latest `result` entry as for a story.

The description has four parts, joined by an empty line:

1. `## Recommendation`: the report's own `## Recommendation` section.
2. `## Findings in short`: the text of the acceptance reviewer's latest `result` entry, without its `<speaker>: ` prefix. The reviewer is found by the journal's data (speaker and kind), not by the text.
3. `## Proposed stories`: the report's `## Proposed stories` section.
4. A closing text that says what you can do.

A part whose section is missing or empty, and findings with no `result` entry of the reviewer, show `none`. The closing text names no merge method; any method the hosting service offers works.

What your act does. The result is yours, whatever the acceptance reviewer recommended: a merge of an acceptance that recommended `not accepted` still books it accepted.

- **Merge** accepts. The report moves from the feature's `in-progress/` folder to its `done/` folder with its cost records file, its state says `done` and `accepted`, and its journal gets one `done` entry, `done (pull request merged); cost: <the acceptance's own cost>`. The proposed stories your merge brought into the feature's backlog stay there untouched; you refine them before starting any. While they wait, the feature is `incomplete` and not due; once you have started and archived them it is due again, and a new acceptance follows. A merge that brought no proposed stories leaves the feature `accepted`. The acceptance's branch is then deleted, on the remote and locally. The commit changes only the report and its cost records file (subject `work item <id>: merged, archived`). The factory does it in one tick.
- **Close**, with a comment saying why, refuses, at any stage: while the reviewer works or asks, at the approval, or after a failed hand-over. The report is written to the main branch at `done` as refused, `blocked` is cleared, the proposed stories are discarded (they were only on the branch), and the feature counts as not accepted until another story is archived and a new acceptance runs. The report has `Refused by the human on <date>: <your comment>` as the first paragraph under its `## Recommendation`, and a `done` entry `done (pull request closed by the human); cost: <cost>`; its cost records file is copied beside it. The commit changes only these two files (subject `work item <id>: closed, refused`). Your reason is your comments written after the reviewer's last result, each stripped of surrounding whitespace, blank ones skipped, joined with one space and otherwise copied unchanged; the factory never interprets them. With no comment the reason is `no reason given`. The factory does it in one tick.
- **A comment** is not answered while the acceptance waits; it goes into the report's journal.

Each acceptance has its own report and its own cost records, so the cost on its `done` entry counts only that acceptance's runs, never an earlier one's.

**Merged before its approval.** You may merge an acceptance's pull request while the reviewer still works or the acceptance waits with a question, before it reached its approval stage. The merge is still your decision: the acceptance is booked `accepted` exactly as above (a waiting question is cleared), and its `done` entry says so: `done (pull request merged before approval); cost: <the acceptance's own cost>`. A merge at the approval stage, before the hand-over, gets the ordinary entry. The merge brought the proposed stories into the feature's backlog, so the feature is `incomplete`, not due, until you have refined and archived them. Nothing loops: the report moves to `done/` as a new file, and the next tick finds it recorded.

**Accepted again.** When another story is archived after an acceptance, the stories no report covers any more and the feature is due again. The next acceptance is a new work item (`F0001-A0002`) with its own branch, report and cost records; the earlier report and its cost records stay as they were. Once the new acceptance's merge is recorded, the feature is `accepted` and not due if the merge brought no proposed stories, and `incomplete` if it brought some; until then it is `merged_unrecorded`. After a refusal the same happens once another story is archived.

**No loop.** Whatever stage an acceptance has reached, your merge or close of its pull request is booked in one tick, without an agent run: the stage run sees the merged or closed pull request and hands it to the acceptance's own handler, never to a story's. Once the booking is on `main` (accepted or refused), further ticks find nothing to do and yield `idle`: no commit, no post. A refused feature stays not due until another story is archived; an accepted one stays not due unless the set of archived stories changes.

**What a close records first.** Before the booking, your unread comments are copied into the report's journal on the acceptance's branch, followed by one `close` entry (speaker `human`, text `closed the pull request.`, dated today in UTC), and that is pushed with the subject `work item <id>: close recorded`. An acceptance ends at its first close: a report that already holds a `close` entry of yours gets no second one. The branch is deleted last, on the remote and locally.

**A close handled again.** A kill at any point is harmless: the recorded close is not recorded twice, a report already in `done/` is not booked twice, and a rerun after the branch is gone only finds the report in `done/`. If the branch is gone and the report is in neither place, the handler raises `CannotHandle` (`no report on the branch or the main branch`) and changes nothing. If the main branch moved since the last fetch, the push is rejected (`PushFailed`) after the close is recorded, and the branch stays; if the remote refuses to delete the branch, the refusal is already pushed and the branch stays. Both are counted and retried as in "An event that keeps failing" in [stops.md](stops.md).

A merge can be handled again after a kill: a report already in `done/` is not booked a second time, and only the branch deletion is repeated. If the main branch moved since the factory last fetched, the push is rejected and the event is retried (see "An event that keeps failing" in [stops.md](stops.md)); the branch stays on the remote until the booking is pushed. If the remote refuses to delete the branch, the booking is already pushed and the error is counted and reported the same way.

A hand-edited report with neither a `## Recommendation` nor a `## Journal` section gets a `## Recommendation` section at the end of the body, followed by an empty `## Journal` that holds the `done` entry. Reports the factory writes always have a journal.

### When the hand-over fails or is killed

Every step before the record can be repeated safely (for a story and for an acceptance alike), and nothing is recorded until they have all happened. A failure or a kill anywhere (the hosting service is down, the factory dies after the post) leaves `handed_over` unset, so the factory raises the event again on the next tick and completes the hand-over. You do nothing; there is never a second cost table post.

A hand-over that fails every time is a counted error like any other: it is tried on three ticks, and then one report is posted on the pull request and the event is capped (see "An event that keeps failing" in [stops.md](stops.md)).

## A stale branch is deleted by the tick

After the restore of the checkout and before it looks at any work item, every tick deletes the remote branch `work-item/<id>` of each story whose file is in `backlog/` on `origin/main`. That is the leftover of a discard (see "A close before the approval discards the story") that was killed after it pushed the move, or whose deletion the remote refused. The branch of a story whose file is in `done/` is deleted the same way: it is the leftover of a merge (see "A merge archives the story") that was killed or refused between the archive and the deletion. Nothing for you to do after a kill.

- **A pull request still open on the branch** is closed by the hosting service when the branch goes (GitHub does so). The factory itself makes no call to the hosting service and posts nothing; a pull request that is already closed stays as it is.
- **A refused or unreachable deletion** is no stop. The factory log gets `could not delete stale branch <name>: rejected` (or `unreachable`), and the next tick tries again. A deletion is logged as `deleted stale branch <name>: its story is back in the backlog` (`its story is done` for a merged story).
- **Start the story again only after the tick has deleted the branch.** A story you start before that still finds the old branch with its old state and bill, and is discarded again. If the remote refuses deletions, lift the refusal and wait for a tick (the log line confirms it) before you start.
- **A branch is kept** when the same id also has a story file in `in-progress/` (two work items with one id are reported as a duplicate), and when no story file of its id is in `backlog/` or `done/` on `origin/main`. A move to `backlog/` that is not pushed to `main` deletes nothing. Branches that are not `work-item/<id>` (`main`, your own) are never touched.

## A merge archives the story

A merge of a story's pull request, by any method (merge commit, squash or rebase), accepts the story as it is, at whatever stage it has reached: working, waiting for you, or at an approval stage. The factory then archives it on `main`, in one commit with the subject `work item <id>: merged, archived`:

- the story file moves from `in-progress/` to `done/` of its feature, and its cost records (`<story>.costs.jsonl`) move beside it when it has them;
- its stage becomes `done`, with no wait and no claim, whoever held the claim; its counters and journal stay as they were;
- one journal entry is added, from `factory`, kind `done`: `done (pull request merged); cost: <the bill>`. The bill counts every cost record of the story, a died run and an unknown cost included; a story with no cost records gets the bill of none.

The handler posts nothing on the pull request. After the archive is pushed it deletes the work item's branch, on the remote and in the factory's checkout. A branch that is already gone (the hosting service deleted it) is no error. The handler trusts the merge: it asks nothing and checks nothing.

A merge found when the story's stage is due to run is handled first: the factory reads the pull request before every agent run, so a story you merged while its stage waited to run is archived as above, without that run.

When it goes wrong:

- **The push of the archive is rejected** (`PushFailed`, outcome `rejected`): `main` moved since the checkout. Nothing is archived and the branch is kept. The next tick fetches, and the story is archived then; do nothing.
- **The factory dies before the push**: `main` and the branch are as they were, and the story is archived once on the next tick.
- **The factory dies after the push, or the remote refuses to delete the branch** (`PushFailed` naming the branch, outcome `rejected`, for example when the remote forbids deletions): the archive stays on `main` and the story is under `done/`, so no event is raised for it again. The branch `work-item/<id>` is left on the remote. The next tick deletes it (see "A stale branch is deleted by the tick"); nothing in the factory reads it meanwhile. An unreachable remote during the deletion leaves the branch in the same way.

## A close before the approval discards the story

When you close a story's pull request while the story is at any stage that is not an approval stage, you have said you do not want this version. The factory then discards the story on `main`, in one commit with the subject `work item <id>: closed before the approval, back in the backlog`:

- the story file moves from `in-progress/` back to `backlog/` of its feature. It is moved, not rewritten: it is the text you wrote on `main`, whatever the work item's branch held;
- the commit changes nothing else.

After that push the handler deletes the work item's branch, on the remote and in the factory's checkout, and with it the branch's journal and cost records. So a story you start again begins with an empty bill. A branch that is already gone is no error. The handler posts nothing, and the pull request stays closed.

A close at an approval stage is a send-back, not a discard; see the next section.

A close found when the story's stage is due to run is handled first: the factory reads the pull request before every agent run, so a story you closed while its stage waited to run is discarded as above, without that run.

When it goes wrong:

- **The push of the move is rejected** (`PushFailed`, outcome `rejected`): `main` moved since the checkout. Nothing is discarded and the branch is kept. The next tick fetches and discards then; do nothing.
- **The factory dies before the push**: `main` and the branch are as they were, and the story is discarded once on the next tick.
- **The factory dies after the push, or the remote refuses or cannot be reached for the deletion** (`PushFailed` naming the branch, for example when the remote forbids deletions): the story is under `backlog/` on `main`, so no event is raised for it again, and the branch `work-item/<id>` is left on the remote. You do nothing: the next tick deletes it (see "A stale branch is deleted by the tick"). If the remote keeps refusing, lift the refusal; the tick tries again every tick.

## A close at the approval sends the story back

When you close the pull request of a story that waits at an approval stage, you have said "not like this". The factory then sends the story back to the second stage in the approval's `next` (`doing` in the usual pipeline). An approval with only one stage in `next` cannot be sent back: the factory raises `CannotHandle` for `closed` and records nothing. The same holds for a story without a pull request number.

The handler works in this order, and each step that changes the work item is pushed on its own:

1. **The close is recorded.** Your unread comments are copied into the journal, a `close` entry (speaker `human`, text `closed the pull request.`, dated today in UTC) is added, and `handed_over` is cleared. The subject is `work item <id>: close recorded`. A story that already holds a `close` entry since its latest `result` gets no second one, so a retry does not close twice; after an earlier send-back and a new stage result, a new close is recorded again.
2. **The pull request is reopened, as a draft.**
3. **The decision is recorded**, subject `work item <id>: sent back`: a `send_back` entry (`sent back to doing, round 3.`), `stage` set to the target, `round` raised by one, the claim released and, when a question is needed, a `question` entry with `blocked` set to `send_back`.
4. **The labels** of the pull request are rewritten to the new stage, so it does not keep `stage:approval`.

The handler itself posts nothing. A question is posted by the `ask` handler, like the others in "The factory's own questions" in [stops.md](stops.md).

### The reason and the round cap

A comment of yours counts as the reason when it was written after the latest `result` of the story: either copied earlier or copied at the close. The factory reads only the journal's records, never what you wrote, so the text of the comment does not matter. With a reason, and with the new round within the `round_cap` of the stage that hands over to the approval (the first one in the pipeline definition that has a cap), the story simply goes back to work with your comments as the findings.

Otherwise the factory asks, and `blocked` is `send_back`:

- You closed without a comment: `The pull request was closed without a comment. ` and the question below.
- The new round is past the cap: `This story has now been sent back <n> times, more than <cap>. ` and the question below. Past the cap the cap text wins, with or without a reason.

The question has three options, all of them things you can already do:

1. Comment what should change; the story is reworked with exactly that.
2. Close the pull request again to discard the story: it goes back to the backlog as you wrote it, and its branch is deleted.
3. If closing was a mistake: mark the pull request ready for review and merge it, which accepts the story as it is.

### When something fails or is killed

- **The reopen fails.** The close stays recorded (`HostingServiceError` is the counted error). The next attempt reopens and records the decision without a second `close` entry. A comment you write in between is copied then, and counts as the reason.
- **The push of the decision is rejected** (you pushed to the branch after the reopen). The close and your commit stay on the branch; the next attempt sends the story back once.
- **The labels cannot be set.** The decision stays recorded; the label is stale until the next stage's result commit rewrites it.
- **The factory is killed between the reopen and the recording of the decision.** The pull request is open again as a draft, but the story is still at the approval, so it is handed over again there and you have to repeat the close. Because the close is already recorded, the repeat adds no second `close` entry.

## Branch deletion on merge must be off

The factory reads a work item's state from its branch `origin/work-item/<id>`. A story in `in-progress/` on `main` with no such branch is read as a new start: it is at the first stage with fresh counters, whatever its file says. So turn off the hosting setting that deletes head branches when a pull request is merged ("Automatically delete head branches" on GitHub). With it on, a merged story whose file is still in `in-progress/` loses its branch and starts again.

## An idle tick that is not empty

When the factory does nothing, the evaluation may still have a reason. An `idle` result names it in its detail:

- A work item waits for the human (blocked, or at an approval stage) and its pull request is open with nothing new. While one waits, no new work starts, even if other work items could run. Answer, comment or merge on its pull request.
- Another instance holds a claim whose lease has not run out. Only one agent runs at a time, so the factory waits for that instance or for the lease to expire.

Neither is a fault. With neither, an idle tick means no work item has anything to do.

## A stage changed by hand

The factory changes a work item's stage only along the `next` lists of the pipeline definition (and archives to `done` from an approval stage). If someone edits `stage` in a work item's file on its branch to another one, the factory notices on its next tick and reports the change as a `reject` event: "stage changed from `<from>` to `<to>`, which the pipeline definition does not allow". What it looks at is the last commit on the branch, beyond `origin/main`, that touched the story's file. The factory puts the stage back as described below. A push to the work item's branch makes the factory try again, and the `reject` returns for as long as the newest commit beyond `origin/main` that touched the story's file is the illegal change.

### What the factory does when it moves a stage back

The factory corrects the change on the work item's branch, and only there; `main` is never written. It makes one new commit on top of the branch's head (also when later commits touched only other files) that:

- sets `stage` back to the one before the illegal change (`from`);
- clears the claim, since a claim belongs to the stage at the head and `to` is no longer it;
- appends a journal entry from `factory` of kind `move_back`: `illegal stage change <from> -> <to>, moved back.`

The commit's subject is `work item <id>: stage <to> -> <from>, moved back`; search the branch's history for `moved back` to find the corrections. When the work item has a pull request, the factory also posts one note there, `The stage was changed from <from> to <to>, which factory/pipeline.yml does not allow; it is back at <from>.`, and sets the `stage:<from>` label again, so the label does not keep the illegal stage.

If the factory is killed in the middle, do nothing: the note is posted first and keyed by the number of the entry to come, so the next tick makes the correction again from the same event and posts no second note. A failing label call after the push is an error of the event; the correction stays on the branch. A `reject` that cannot be corrected (the newest commit is a merge commit, changed no stage, has a parent without the story's file or with an unreadable one, or is itself a correction) is refused with `CannotHandle` and writes and posts nothing.

Not counted as such a change:

- the opening commit, whose parent is the story as you started it (a story started at `review` is not rejected). So the stage a work item branch you created by hand starts with is never judged, whatever it is: the first commit that gives the file its front matter is the opening commit, or has a previous version that cannot be read. Later stage changes on such a branch are judged like any other;
- a merge commit on the branch;
- the factory's own correction, which moves the stage back and appends a journal entry of kind `move_back`;
- a merge of the pull request by any method: merge commit, squash or rebase. The factory reads the pull request first, and a merged pull request is `merged`, never an illegal change.

A hand-made change that a later commit on the branch buried is not seen: only the newest commit that touched the file is judged.

### Never edit a running work item on main

Do not edit the file of a work item in `in-progress/` on `main`. Answer in its pull request instead: the agents amend the story on its branch (the description, the criteria), and your edit on `main` changes the same file. At the next stage start the factory merges `main` into the branch, the merge conflicts, and the stage stalls with the reason `merge_conflict`. When it has happened, revert the edit on `main`; the stage then starts again from the branch's story.

## A restart during a stage

If the factory dies while a stage runs and is started again with the same instance name, it finds its own claim on the work item's branch at its first look and treats it as a crash. It does not wait for the lease.

What it does, in one call:

- It throws away everything the dead stage did that is not on the remote: uncommitted and untracked files, commits that were never pushed, and the cost records of the discarded agent runs. Records of earlier stages stay.
- It records the crash in one commit on top of the remote's head: the claim is cleared, `crashes` goes up by one, and the journal gets an entry of kind `crash`: "crash 1: the run of stage doing ended without a result. Its work is discarded back to commit <commit>."
- It reruns the stage at once, unless the crash cap is reached (see "The crash cap"). `attempts` is not raised: a crash is not charged as a failed attempt.
- Below the cap it posts nothing on the pull request.

A commit that you pushed to the branch while the stage ran is on the remote, so it stays; the journal entry names the commit the discard went back to. The stage-start commit and its `started` entry stay in the history too.

Recovery is proved by injection tests: each of the six kill points is killed against a real local bare remote and the factory restarted, and v1's thirteen fault-injection paths are each walked with one kill or stall (`uv run pytest tests/hosting/domain/test_kill_points.py tests/shared/domain/test_fault_paths.py tests/shared/domain/test_fault_paths_7_to_13.py`). The cases and paths are listed in the sections *Kill points* and *Fault-injection paths* of `docs/project-guide/README.md`.

If the push of the crash commit is rejected (someone pushed in between), the event is a counted error as under "An event that keeps failing" in [stops.md](stops.md); a push to the branch makes the factory look again. A claim of another instance name is handled only once its lease has expired (see "An expired lease").

### The crash cap

`crash_cap` in the pipeline definition (default 2) is the number of crashes after which the factory asks you instead of rerunning. The count is `crashes` in the work item's state; it is reset by a forward move of the stage and by your answer, and kept by a rework move and by a stall, so it counts the crashes since the last forward move.

When a crash brings `crashes` up to the cap, the stage is not rerun. The same commit that records the crash records a question by `factory` and sets `blocked` to `crash_cap`; the commit is pushed, and only then is the question posted on the pull request, once. If the work item has no pull request yet, a draft is opened for it first. The question reads:

```text
Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
```

- A comment you write after the question was posted ends the wait: `crashes` goes back to 0, `attempts` stay, and the stage runs again.
- Closing the pull request discards the story.
- A boundary error after the factory pushed its claim (hosting service, agent runtime, project command, git, a rejected result push) leaves the claim on the remote. The next look treats it as a crash and reruns the stage. If that fails again, it is the second crash and ends here with this question, not in the error report of "An event that keeps failing" in [stops.md](stops.md), because each rerun is a new event on a new remote state.
- If posting fails, the question stays recorded and pushed; the failure is a counted error of the event. A question lost between its record and its post is posted again by the `ask` handler when the work item has a pull request; for a work item without one it is not posted again.

## An expired lease

When an instance finds a claim of another name whose lease has run out (the claim's age is at least its `lease_duration`, 60 minutes by default), it treats the holder as gone and takes the stage over. Before that, the claim is waited for and nothing is touched.

What it does, in one call, is what a restart does (see "A restart during a stage"):

- It throws away what is not on the remote and records the expiry in one commit: the claim is cleared, `crashes` goes up by one, and the journal gets an entry of kind `expiry`: "expiry 1: the lease of stage doing ran out. Its work is discarded back to commit <commit>."
- `attempts` is not raised. An expiry is a crash, not a failed attempt, and it counts toward the crash cap.
- After the push it posts a note on the pull request (a draft is opened for it if there is none): "The run that held this stage ended without finishing: its lease expired (crash 1 of 2). Retrying."
- Then it reruns the stage itself. At the crash cap it does not: the note reads "... (crash 2 of 2). The factory does not rerun it and asks you instead." and is followed by the question of "The crash cap", on the same pull request.

The notes of the factory say "retrying" only where a rerun follows. A note without it means the factory has stopped and waits for you.

If the post of the note fails, the expiry stays recorded and pushed, the failure is a counted error of the event, and the note is not posted again. The stage is not rerun in that call; the next look finds no claim.

Your own claim is never an expiry, however old it is: that is the restart case. A claim whose lease has not run out is refused.

## Claims, leases and the clock

An instance claims a stage by pushing the stage-start commit; the claim records the instance's name, the start time and the role's `lease_duration` (60 minutes unless the pipeline definition says otherwise, per role). The claim keeps the value it was made with: changing `lease_duration` in the definition affects new claims only, never one that is running.

- Your own claim is recognised whatever its age. After a restart with the same instance name, the instance reruns its stage at once and does not wait for the lease. Only `factory-watch` judges it by the lease, as a look from outside: within the lease it shows the claim as held, since the tick may be running that stage.
- Another instance's claim is waited for until its lease has run out (the age reaches `lease_duration`); then it counts as expired and the factory handles it as above.
- Instances need a synchronised clock (NTP). Expiry compares the start time recorded by the claiming instance with the checking instance's own clock, so a clock that is off by minutes makes a lease end early or late.
