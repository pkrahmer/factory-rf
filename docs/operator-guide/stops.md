# Stops, stalls and questions

A topic of the [operator guide](README.md). It is for the operator of an [instance](../project-guide/glossary.md).

It tells you what to do when the factory stops, [stalls](../project-guide/glossary.md) or asks you a question. A [stop](../project-guide/glossary.md) is the factory refusing to go on and saying why. It also describes what a [stage](../project-guide/glossary.md) run leaves on the pull request, so that you can tell a normal run from a broken one. Exact texts, limits and rules are in *Reference* at the end.

## The stops

Every stop has one destination. A stop of the repository or the machine goes to the health status and to a line of the factory log. A stop of one [work item](../project-guide/glossary.md) goes once on that work item's pull request. One case, a [backlog](../project-guide/glossary.md) [story](../project-guide/glossary.md) that names a later stage in its own file, has no stop. Every line about a stop in the factory log is time-stamped (see "The factory log" in [health.md](health.md)).

Find your stop in the table, then read the section it names.

| Stop | Destination | What you do |
|---|---|---|
| `fetch-failed` | health status and factory log | `git fetch` failed, an expired or revoked token included. The fetch before the [tick](../project-guide/glossary.md) raises it too. Fix the network, the address or the credentials; see "The stops of the tick". |
| `checkout-restore-failed` | health status and factory log | The checkout cannot be put on `origin/main` (the dirty main branch). Fix the cause or delete the checkout and clone again; see "The stops of the tick". |
| `pipeline-definition-invalid` | health status and factory log | `factory/pipeline.yml` on `origin/main` (the [pipeline definition](../project-guide/glossary.md)) fails its validation, an agent that is not installed included. See "The stop `pipeline_definition_invalid`". |
| `agent-definition-invalid` | health status and factory log | An agent file holds a key the runner does not apply. See "The stop `agent_definition_invalid`". |
| `repository-unavailable` | health status and factory log | The tick waits for a repository that is empty or has no pipeline definition. Push `main` with `factory/pipeline.yml`; see "The wait for a repository that is not ready" in [health.md](health.md). |
| `main-branch-failing` | health status and factory log | `lint` fails on the main branch. Push a fix to `main`; see "The stamp and the probe of the main branch" in [health.md](health.md). |
| `preflight-failed` | health status and factory log | A preflight item fails, or the settings are invalid. Fix what the detail names; see "The preflight's items" in [health.md](health.md) and "When the process refuses to start" in [install.md](install.md). When the state directory cannot be written, `factory-run` still ends with status 2 but writes no stop: the settings fault reaches standard error as two lines without a stamp. Check the `state` volume. |
| `disk-low` | health status and factory log | The work or the state directory has less free space than `FACTORY_MIN_FREE_GB` asks for, or its free space cannot be read. Make room on the file system the detail names, and nothing more: the next tick clears the stop. |
| `stage-image-failed` | health status and factory log | The project's `<project>/factory/stage.Containerfile` on `main` breaks the rule or does not build. No stage starts. Fix the file on `main`: the fix takes effect before the next stage, with no restart; see "The project's stage file" in [machine.md](machine.md). |
| `duplicate` | pull request | Two work items have one id. Keep one file and rename or delete the other; see "Stops that cannot be done". |
| `pull-request-lookup` | pull request | The one pull request lookup fails. Fix the cause named after the colon; see "Stops that cannot be done". |
| `ask-without-pull-request` | pull request | A question is recorded for a work item that has no pull request. Open one for the branch or push a commit to it; see "Stops that cannot be done". |
| `handler-error` | pull request | A handler fails on the same event and state three times. See "An event that keeps failing". |
| `hand-over-error` | pull request | A hand-over fails every time, three ticks in a row. See "When the hand-over fails or is killed" in [work-items.md](work-items.md) and "An event that keeps failing". |
| `push-rejected` | pull request | A push is rejected, for example by a hook of the remote. No agent is run while it lasts. See "An event that keeps failing"; fix the remote's rule or push to the branch to start the count again. |
| `later-stage-in-backlog-file` | no stop | A backlog story whose own file names a later stage in its front matter. The start rule removes it: the work item starts at the first stage with [`round`](../project-guide/glossary.md), `attempts` and `crashes` at 0, and nothing is reported. |

The reasons in the health status are the same words with underscores.

### The stops of the repository or the machine

**You see** a line in the factory log and an entry in the health status file (`health.json`). Look there: a stop of this kind never goes to a pull request. The line reads:

```text
2026-10-12T12:00:07Z stop repository fetch_failed: fatal: unable to access 'https://github.com/example/project.git/': Could not resolve host: github.com
```

That is `stop <scope> <reason>: <detail>`, after the stamp. `scope` is `repository` or `machine`; `reason` is one of the reasons the health status file lists. When the fault is gone the factory writes:

```text
2026-10-12T12:00:12Z stop cleared fetch_failed
```

**It means** the factory found a fault of the repository or the machine and tries both destinations, the log and the health status. It removes the stop from the health status, then writes the cleared line, when it finds the fault gone.

**You do** what the table says for the stop, and wait for the next tick. You never clear a stop by hand: deleting `health.json` only hides it until the next cycle raises it again.

- A stop's detail always says why. An empty or blank detail is replaced by `no detail given`, for every reason, in the log, the health status and the records.
- A machine stop does not end the factory on a VM; it waits for your fix. In a job, a machine stop that has stood for ten minutes ends `factory-run` with status 1. A job is an instance with the idle shutdown on and the action `exit` (see *In a job* under *The idle shutdown* in [machine.md](machine.md)).
- The health status holds one stop per reason. A stop raised again for the same reason replaces the earlier one and takes the newest detail and time; it is not added twice. A new reason is added at the end.
- A fault that lasts is raised every cycle, but the log line is written only when the stop does not stand yet or stands with another detail or scope. A raise after a clear writes the line again.
- `stop cleared <reason>` is written only when the stop was in the health status. Clearing a reason that is not stopped writes nothing.
- One failing destination never loses the stop. If the log file cannot be written, the stop still goes to the health status. If the health status cannot be written, the line still reaches standard output and the log file. The factory then reports the write error (an `OSError`). When both fail, it reports the log's error.
- If the health status cannot be written while a stop is cleared, the stop stays in force and no cleared line is written. If the log cannot be written, the stop is already removed.

### The stop records on main

Every raise and every clear of a stop of the repository or the machine is also a record (see "The stop records" in [health.md](health.md)). Each tick restores the checkout, and right after that, before the preflight, it pushes the records that `origin/main` does not hold. They go to `factory/stops.jsonl` on `main`, as a commit with the subject `stops recorded`. The records carry the event, scope, reason, time and instance, without the detail, which stays in the factory log.

1. Pull `main` before you push to it. The factory pushes `main` after a stop event as well as after an archive. If you push first, the factory's push is refused and succeeds on the next tick. If the factory pushes first, yours is refused until you pull.

- A tick that ends before the restore succeeded (`disk_low`, `fetch_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `checkout_restore_failed`) publishes nothing. The records wait in the state directory for the next tick that gets past the restore, so a `fetch_failed` is published after the fetch works again.
- A failed push (for example a rule of the remote that refuses `main`), any other git error or a file that cannot be written leaves the records where they are. The factory writes one line, `cannot publish the stop records: <error>`, goes on with the tick and tries again next tick. Nothing is lost and nothing is pushed twice.
- The stop records note the first raise and the clear only. A raise with another detail while the stop stands adds no record.

### The stops of one work item

**You see** one comment on the work item's pull request. A question is first recorded (a [journal](../project-guide/glossary.md) entry of kind `question`, with `blocked` set, committed and pushed) and then posted; see "The factory's own questions". The comment says what each possible answer will do, and it ends with the factory's marker and the stop's key:

```text
<!-- factory -->
<!-- factory key=<work item>:stall:3 -->
```

**It means** the factory stopped one work item and needs you or a fix. The factory's error report for an event posts in this form (see "An event that keeps failing"). A stall has its own rule, given under "A stall: the stall note".

**You do** what the comment says. The rules of where it is posted:

- If the work item has no pull request yet, the factory opens a draft pull request first, on the work item's branch (`work-item/<id>`), and posts the stop there. The description says: "The factory opened this draft pull request to report a stop on <work item>. The stop is the comment below."
- It opens one only when the branch is on the remote with a commit beyond `main`. Otherwise it opens nothing, posts nothing and reports a `create_pull_request` error: `branch <branch> is not on the remote with a commit beyond main`. You see this only if the remote branch was removed or reset, because the factory pushes the branch before it reports a stop.
- If the work item's branch already has an open pull request, the factory posts on that one. A pull request you closed or merged is not reused for a new one. But when the work item's state records a pull request number, the stop is posted there even if you have since closed it.
- A restart never repeats a stop. The key identifies the stop: if the factory died after posting and before recording it, the next attempt finds the key on the pull request and posts nothing. The same key with another text is still a repeat; a different kind or number is a new stop and a new comment.
- The posting writes no state. In particular the factory does not record the number of a pull request it opened for an error report; a later stop finds that pull request by its branch.
- Two files with one id are both read. The second is read from `origin/main` as a started story, because the id's branch holds only the first file. So the duplicate is reported on the first work item's pull request and does not end the tick.

## What a stage run shows

A normal stage run leaves these traces on the remote and the pull request, in this order. If one is missing, the run did not get that far.

1. **The draft pull request.** The first stage of a work item opens it, titled `<id>: <title>`, with the work item's text as the description. Only an open pull request is reused; a closed or merged one never is, and a new draft is opened instead.
2. **The stage-start commit.** It is pushed before any agent runs. It holds the [claim](../project-guide/glossary.md) and one journal entry, speaker `factory`, kind `started`, with the text `factory: started <stage> as <instance>.` (for example `factory: started doing as factory-1.`). If this push fails, no agent runs.
3. **The agent's entry.** The speaker is the agent's [role](../project-guide/glossary.md) and the kind is `result`, or `question` when the agent asked. Code writes both; the agent writes the words. Its last lines are described below.
4. **One commit by the factory**, directly above the stage-start commit: the result commit, or the stall commit after a stall. It holds the whole work tree. The agent cannot commit, because the checkout's `.git` is the factory's alone (see "The factory alone writes the checkout's `.git`" in [decisions.md](../decisions.md)). A stage that moves the work item to an [approval](../project-guide/glossary.md) also writes the pull request's description. It does so after the result commit and before its push, so the description is complete when the board first shows the approval. If that push fails, the description may already show the reports while the work item stays at its stage.
5. **The label** `stage:<stage>` (for example `stage:review`) on the pull request. It is written after the result commit is pushed, and after a stall's note is posted. It is a projection of the stage and is never read back.

The agent's entry has these lines at its end:

- When the [take](../project-guide/glossary.md) left out changes outside the role's [write paths](../project-guide/glossary.md), the last paragraph says `The factory left out changes outside the write paths: <paths>.`, the paths sorted and joined by `, `. The work item's own `.costs.jsonl` is never named.
- For each green check and each report the entry ends with one line `` `<command>`: <last line of its output> ``, for example `` `check`: 12 passed ``.
- A result the factory took instead of running the command names the run it took and says that the command did not run: `` `check`: check: green (not run again: passed on tree 0123456789ab at 2026-10-18T15:20:01Z) ``. The tree is its first 12 characters, and the time is the start of that run in UTC. See "The known results" in [health.md](health.md).
- A report stopped at its time limit gets ` (stopped at its time limit after <seconds> s)` at the end of its line, for example `` `test`: ........ [ 87%] (stopped at its time limit after 600 s) ``. That is the tests stage's `make test`, stopped at its 10 minutes. The line is then only what the report printed last, and the records hold `time_limit`.

While an agent runs, the work item's `.costs.jsonl` is modified in the work tree and not committed: it holds the running run's record, which the result commit or the stall commit carries. An agent that mentions it in its entry has seen the factory's file, not made a change of its own.

If the push of the result commit fails, no label is written. If the hosting service fails at the label, the commit stays pushed.

## A stall: the stall note

**You see** a comment on the pull request:

```text
Stalled (attempt 1 of 2): the agent run died without a result. Retrying on the next tick.
```

**It means** a stall: a stage ended without a result the factory can keep. A stall costs one attempt of the work item and is never a [crash](../project-guide/glossary.md). The factory keeps what the agent wrote inside the stage's write paths. The take does not copy the rest from the [dataset](../project-guide/glossary.md). The factory releases the claim and pushes one commit with a `stall` entry in the journal. Only then does it post the note. It also writes the pull request's `stage:` label for the stalled stage, so a work item whose first stage stalls has its label too. The note's key is `<work item>:stall:<n>`, where `n` is the number of the stall entry.

**You do** nothing while the note says "Retrying on the next tick.": the next tick runs the stage again from what the stall kept. The note says so only while `n` is below `m`.

- `attempt n of m`: `n` is the work item's attempts after this stall; `m` is the [attempts cap](../project-guide/glossary.md), `attempts_cap` in the pipeline definition.
- At the cap the note ends `The attempts cap is reached; the factory asks you next.` and says nothing about retrying. The factory then records the attempts-cap question and posts it (see "The factory's own questions"). Read the cause and the stall entries in the work item's journal. Fix what stops the stage: the agent, the stage's time limit or budget, the pipeline definition, the project's checks, or a conflict with `main`. Then answer on the pull request. The factory does not run the stage again until you have.
- The cause is one sentence, then a detail after a colon when there is one, such as the name of a red check. A detail of several lines puts its first line in the sentence and the other lines in a code block below it; see "A stall by a red check". The nine causes are in *Reference*.
- The cause `the provider's spend limit lasted past the waiting ceiling` (`provider_limit`) means the factory waited out the provider's limit for the whole ceiling and the limit was still there. There is nothing to do for one such stall: the next tick tries again. If it repeats, see "A provider's spend limit" in [agent-runtime.md](agent-runtime.md), "What to do at the ceiling".
- The stall's pull request: an open pull request of the work item is reused. Otherwise the stall opens a new draft titled `<id>: <title>` with the work item's text as description. It does not use the stop description, and it does not post on a closed pull request.
- If the hosting service fails while the note is posted, the stall commit is already on the remote, no note is posted and no label is written. If it fails while the label is written, the note is posted and the label is missing. The error is reported, and the work item shows the stall in its file and journal.

## A stall by a red check

**You see** a stall note with the cause `a check is red after the stage` and the check's name after a colon. Below the sentence, a code block holds the last 15 lines of the check's output, or all of them when it printed fewer. The block keeps GitHub from rendering the output as Markdown.

````text
Stalled (attempt 1 of 2): a check is red after the stage: `check`. Retrying on the next tick.

```text
  File "x.py", line 1, in <module>
make: *** [Makefile:6: check] Error 1
```
````

**It means** the agent decided to move forward and the stage has checks. The factory runs them itself, in the order of the pipeline definition, and stops at the first that is red. A check is green only when its make target exits 0. A red check costs one attempt; the stage, the round and the crash count stay. In the work item's journal the agent's entry comes first, ending with one line per check that was green, and the `factory` stall entry follows.

**You do:**

Below the attempts cap there is nothing to do: the next tick runs the stage again, and the agent sees the journal. At the cap:

1. Read the 15 lines and run the target yourself (`make check`) on the work item's branch.
2. Fix what is wrong: the code, the target, or a tool missing on the machine.
3. Answer on the pull request. The factory has asked, so the attempts-cap question described under "The factory's own questions" is there, and your comment answers it.

Reports (the stage's `reports`) run after all checks are green. They are recorded and never hold a move. Every report that ran adds one line `` `<command>`: <last line of its output> `` to the agent's entry, passed or failed. The line has the same form either way, so only its last line shows whether the report passed. A report stopped at its time limit is the exception: its line ends with the stop note (see "What a stage run shows"). A failing report holds nothing and stops nothing.

The result commit of every stage holds the whole work tree. Make sure the project's `.gitignore` covers whatever its checks create (build output, caches, coverage files); otherwise the factory commits it.

## The factory's own questions

**You see** a comment on the pull request that is a question. Besides an agent's `question`, the factory asks you itself.

**It means** the work item waits for you. Every question reaches you in two steps. It is recorded first, as a journal entry of kind `question` in the work item's file, committed and pushed with `blocked` set. Only then is it posted as one comment on the pull request. If the factory dies or the post fails between the two, the question is already recorded and the next attempt posts it once. The comment's key is made from the recorded entry's number, and a post whose key the pull request already holds does nothing. The factory does both steps.

**You do** what the table says for the question you meet:

| Question | `blocked` | Comment reads | A comment | Closing the pull request |
| --- | --- | --- | --- | --- |
| An agent's | `question` | `<role>: <the agent's words>` | answers it; the stage runs again | discards the story |
| The form has findings | `question` | `factory: ` and the findings question (`The work item's form has findings, so the stage cannot move forward: ...`) | answers it; the stage runs again | discards the story |
| The [round cap](../project-guide/glossary.md) | `round_cap` | `factory: ` and the round-cap question (`This work item has now been sent back <n> times, more than <cap>. ...`) | answers it; the count of rounds starts over at 0 | discards the story |
| The attempts cap | `attempts_cap` | `factory: ` and the text below | the attempts go back to 0 and the stage runs again | discards the story: it goes back to the backlog as you wrote it, and its branch and bill are deleted |
| The send-back | `send_back` | see "A close at the approval sends the story back" in [work-items.md](work-items.md) | answers it | discards the story: it goes back to the backlog as you wrote it, and its branch and bill are deleted (option 2 of the question). The send-back has already moved the story out of the approval, so a close cannot send it back again |
| The crash cap | `crash_cap` | `factory: ` and the crash-cap question, quoted under "The crash cap" in [work-items.md](work-items.md) | the crash counter goes back to 0 and the stage runs again | discards the story: it goes back to the backlog as you wrote it, and its branch and bill are deleted |

The attempts-cap question is recorded by the factory itself, when a work item has used all its attempts: an entry by `factory` of kind `question`, and `blocked` set to `attempts_cap`. It reads:

```text
Stage doing stalled 2 times. The last time: Stage doing stalled (attempt 2 of 2): the agent gave no valid decision and entry

Comment anything to retry: the attempts go back to 0 and the stage runs again. Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
```

The last time is the text of the work item's latest `stall` entry. A work item at the cap with no stall entry cannot be asked about, and is a counted error. Comments you write while a question waits to be posted are recorded after it; the post stays keyed to the question's own entry.

- **The form has findings.** The agent decided to move forward, but the work item's form still has findings after the run. The comment reads: `The work item's form has findings, so the stage cannot move forward: 1. <message> 2. <message>. What should happen? Answer with a comment; the stage then runs again. Close the pull request to discard the work item.` The stage stays where it is and the round is not counted. Answer with a comment (say how to fix the form, or that the finding is wrong). Closing the pull request discards the work item.
- **The round cap is passed.** A stage with `round_cap` sent the work item back once more than the cap allows. The comment reads: `This work item has now been sent back <n> times, more than <cap>. What should happen? Answer with a comment, which starts the count of rounds over; close the pull request to discard the work item.` The stage stays where it is and the round shows the count. Answer with a comment: `round` goes back to 0 and the stage gets its rounds again.

A stage without `round_cap` sends back without limit and never asks. Sending back counts rounds; a stall counts attempts (see "A stall: the stall note"), and the two caps are separate.

### Which comment answers a question

A comment answers a question when it was written after the factory posted that question. The factory handles a `comment` like this for a work item that waits (`blocked` is set):

- Your comments are copied into the journal and, in the same commit, the wait ends. The answer is read from ids and keys, never from what you wrote; a blank comment is marked read but does not answer.
- A comment written before the question was posted is only recorded and the wait stays. The same holds when the question is recorded but not posted yet, and when the only post on the pull request belongs to an earlier question. Comment again once the question is on the pull request.
- Each answer clears the wait and resets only what belongs to that wait: `attempts` go back to 0 for the attempts cap, `crashes` go back to 0 for the crash cap, `round` goes back to 0 for the round cap, nothing else.
- The round cap's answer starts the count of rounds over, and that count also holds the send-backs of the approval. The factory does not read your words, so an answer cannot grant exactly one more round.
- An answer to any other wait keeps `round`: after the approval's send-back question (`send_back`) the count stays, so the next send-back past the cap asks the round cap question once more.
- A comment on a work item that does not wait for you, at an approval stage for instance, is only recorded; `stage`, `round`, `attempts`, `crashes` and the hand-over are untouched.
- A comment event that keeps failing is tried three times on the same remote state and then reported once on the pull request, like every other event (see "An event that keeps failing"). The factory's own comments (those with its marker) never answer.

### The reviewer's notes and added criteria

Three things in a reviewer's entry are not findings in the usual sense. Read them at the approval.

- **Notes.** From round 1 on, a point that is only about the quality of a test file the story adds (a copied helper, a name, a duplicate test) goes under `Notes:` after the findings, one line each with its location. The notes do not send the story back. The first review, at round 0, still sends such a point back. A point on a criterion, the architecture, security or `src/` is a finding at every round.
- **An added criterion.** The diff may build a behaviour that no criterion names, where pinning it needs no code. The reviewer then writes the criterion into the story itself. It names the criterion in its entry as `criterion <n> added: it needs its test`. The coder changes no code and the tester writes the test. That is a send-back like any other and counts a round, so the round cap may still ask you afterwards.
- **A corrected description.** A story's Description may have gone stale against what it built. If the human's answers, the Interface or the criteria settle what it should say, the reviewer rewrites the stale sentences itself. Its entry names each correction as `description corrected: <what it said> -> <what it says now>`, one line each. That is not a send-back and counts no round. A Description the code contradicts with nothing to settle it still comes back as a finding or a question.

## The stop `pipeline_definition_invalid`

**You see** a line in the factory log and an entry in the health status, nothing on a pull request:

```text
2026-10-12T12:00:07Z stop repository pipeline_definition_invalid: missing key: contract
```

**It means** the pipeline definition, `factory/pipeline.yml` as it stands on `origin/main` (never the file in the work tree), is refused when the factory loads it each cycle. The detail is the fault. Several faults are joined by `; `.

**You do** what the table says for the fault, on `main`:

| Fault | Cause and what to do |
|---|---|
| `factory/pipeline.yml is missing at origin/main` | the file is not on `main`; merge it |
| a fault of the text, such as `missing key: contract`, `unknown key: <path>`, `invalid <path>: <message>`, `not valid YAML: <problem> (line <l>, column <c>)` | fix `factory/pipeline.yml` on `main`; several faults are joined by `; `. A YAML fault is one line with a 1-based position, for example `not valid YAML: found duplicate key "done" with value "{}" (original value: "{}") (line 27, column 3)` (a stage key written twice; the factory refuses a repeated key on purpose) |
| a fault of the rules across keys, such as `stage doing: next names unknown stage ship`, `contract major 2 is not supported (this factory reads major 1)`, `role coder: write_paths is empty`, `role coder at stage doing: 61 min exceed lease_duration 60 min` | fix `factory/pipeline.yml` on `main`; see "The pipeline definition" in [pipeline.md](pipeline.md) for the rules you meet most often and `docs/project-guide/pipeline.md`, "The rules of the definition", for the full list |
| `role <role>: agent is not installed` | the role has neither a file `factory/agents/<role>.md` on `origin/main` nor a file `<agent home>/agents/<role>.md`; add one of them. Every missing role is named, in the order of `roles`, joined by `; ` |
| `agent home unavailable: <fault>` | `<agent home>/agents` is missing or is not a directory (see "The agent files" in [agent-runtime.md](agent-runtime.md)) |

The agents are checked only when the text itself is valid, so a broken file and a missing agent home show the file's fault alone until it is fixed. A key with a default may be left out and takes it; a key without one that is missing is a fault.

The stop clears itself at the next load of `origin/main` that succeeds, with the line `stop cleared pipeline_definition_invalid`; stops of other reasons are not touched.

- Only the load of `origin/main` raises or clears this stop. A look at the definition on another branch can be refused, but it changes neither the health status nor the log.
- A git failure while reading (an unreachable repository, an unknown ref) is not a fault of the definition and raises no stop.
- If the health status cannot be written, the load reports an `OSError` and not the fault; the log line has been written.
- What the cycle does while the stop stands is described with the tick, under "The stops of the tick".

## The stop `agent_definition_invalid`

**You see** a line in the factory log and an entry in the health status. The detail is `<agent name>: <fault>`, and the first refused role is named:

```text
2026-10-16T12:00:07Z stop repository agent_definition_invalid: coder: key not applied by the agent runtime: permissionMode
```

**It means** that the pipeline definition on `origin/main` is valid, and the factory then reads the agent file of every role, in the order of `roles`. A file it refuses raises this stop (scope `repository`). Most often the file holds a key the agent runtime does not apply (see "The agent files" in [agent-runtime.md](agent-runtime.md)). The tick ends there: no stage is started and no event is handled.

**You do** one of two things, by whose file it is:

1. For a shipped agent, edit `<agent home>/agents/<agent name>.md` and remove or correct the key the detail names.
2. For a project's own agent, the detail names the file and the ref, `<agent name>: factory/agents/<agent name>.md at origin/main: <fault>`. Fix it with a commit on `main`: a branch's copy is never read, and the installed agent does not stand in for a faulty project file.

The next tick loads again and clears the stop with the line `stop cleared agent_definition_invalid`. A role whose agent is not installed is a fault of the definition and shows as `pipeline_definition_invalid`, because the other checks come first. As for that stop, only the load of `origin/main` raises or clears this one.

## The stops of the tick

A tick works from the remote alone: the checkout is disposable. It does these steps in order:

1. It reads the free space, before the fetch (see "The low disk").
2. It fetches.
3. It loads the pipeline definition from `origin/main`.
4. It puts the checkout back on `main` at `origin/main`.
5. It publishes the stop records (see "The stop records on main").
6. Only then does it look at the work items.

Four repository stops, and the machine stop `disk_low`, end a tick before it looks at any work item. Each is a log line and a health status entry, never a comment on a pull request. The next tick tries again and clears the stop when the fault is gone. The four are `fetch_failed`, `pipeline_definition_invalid`, `agent_definition_invalid` and `checkout_restore_failed`; "The stops" says what to do about each. The tick does not touch the checkout while `pipeline_definition_invalid` or `agent_definition_invalid` stands.

### `fetch_failed`

**You see** `fetch_failed` in the health status, with git's message as the detail. An expired or revoked token shows this way, and nothing is lost: the next tick after a successful fetch carries on.

**It means** `factory-run` fetches once in an iteration, before the tick, and the tick does not fetch again. That fetch compares the project's stage file on `origin/main` with the one in use. When it fails, it raises the same stop: scope `repository`, git's message as its detail. No tick runs in that iteration. The image, its identity and its `PATH` stay as they were. Any other git error in that fetch is not this stop: the iteration fails with an `iteration failed` line in the log.

**You do** fix the network, the address or the credentials. The next fetch that passes clears the stop and compares the stage file as usual.

### `checkout_restore_failed`

**You see** `checkout_restore_failed` in the health status; its detail is git's message.

**It means** the checkout cannot be put back on `origin/main`, for example because of an untracked file or directory the factory cannot remove. On the VM only the factory's own git and the take write the checkout, and both run as `factory`. No agent runs there. Such a path is therefore one made by hand, as root or as another user. The stop ends the tick before any stage is dispatched, so it records no crash and does not count toward the crash cap.

**You do** remove the path git's message names, as `factory` (`sudo -iu factory`) or, when `factory` cannot remove it, as root. The next tick runs the restore again and clears the stop once it succeeds.

The restore throws away every uncommitted change and every untracked file that no ignore rule matches. It also deletes the local branches of the work items, so that a stage starts from the remote's branch. When it throws changes away it writes one line to the log, `discarded uncommitted changes: <path>, <path>`. Ignored paths (`.venv`, the caches) stay. Do not keep anything in the factory's checkout.

### A work item file that cannot be read

This is not a stop. The tick ends with an error that names the file's path. It does so on every tick until a human repairs the file or moves the story out of `in-progress/` on `main`. Repair it on its branch, or on `main` for a started story without a branch. Closing the pull request changes nothing: the tick reads every story in `in-progress/` before it looks at any pull request. A work item in a stage that the pipeline definition lacks fails the same way.

### The low disk

**You see** the machine stop `disk_low`, and the tick ends; nothing is fetched or written after it. The detail names each short directory with its free space, the work directory first. A free space that cannot be read is the same stop, with the detail `cannot read the free space of <path>: <error>`, and no later path is read.

**It means** that at the start of every tick, before the fetch, the factory read the free space of the work directory and of the state directory. The work directory is the checkout's parent. The stop stands when one has less than `FACTORY_MIN_FREE_GB`; exactly the minimum is enough. The preflight runs inside the tick, so this one check covers it.

**You do** make room on the file system the detail names. The first tick that finds enough room clears the stop.

- A checkout that is missing is cloned before the first check, by the iteration's preparation (see "The checkout is cloned when it is missing" in [install.md](install.md)). A clone onto a full disk therefore fails as `repository_unavailable` first.
- On a full disk the stop's own writes (`health.json`, the factory log) can fail with an `OSError`. The iteration then ends with the `iteration failed` line (see "The loop and its pauses" in [install.md](install.md)) and the next one tries again.

### The preflight in the tick

**You see** `main_branch_failing` or `preflight_failed` in the health status and the log. The tick does nothing else: no stale branch is deleted, no work item is read, no agent is started and no pull request is touched.

**It means** the tick ran the preflight (see "The preflight's items" and "The stamp and the probe of the main branch" in [health.md](health.md)) after the fetch, the load and the restore. It runs before the cleanup of stale branches and before any work item is looked at. The probe therefore sees the `origin/main` the tick has just fetched. An invalid pipeline definition ends the tick earlier, so it does not raise `preflight_failed`.

**You do** what the table says for the stop. A fix you push is probed on the next tick, and a commit that broke `lint` stops that same tick.

## An event that keeps failing

**You see** one comment on the work item's pull request:

> The factory failed 3 times on `<event>` and has stopped retrying it. Last error: <error>. A new commit on the work item's branch (now at <12 characters of the commit>) makes the factory try again.

**It means** the factory counts what goes wrong with each event, per event and per remote state. The remote state is the commit the work item's branch is at. Any error counts, an unknown kind of event included. After three errors on one event and one remote state, the factory posts the report once and stops retrying that event. A restart does not post it again, because the report carries a key that the pull request already holds. If the work item has no pull request, the factory opens a draft one for the report first, as under "The stops of one work item".

**You do:**

1. Read the last error in the report and fix its cause (a broken checkout, a missing tool, a bad file on the branch).
2. Push a commit to the work item's branch. That is a new remote state: the count starts again at 1 and the event is tried again. Nothing else restarts it; comments do not.

- Two different events of one work item on one remote state share one report. The one that reached three errors first posts it, and the other is not tried again either.
- A success clears the event's count.
- The counts are kept in memory only. After a restart they begin at zero, so the event is tried up to three more times; the report is not posted twice.
- If the work item's branch is not on the remote, no pull request can be opened for the report and no later tick would change that. The report is then one line in the factory log, `error cap reached on <event>: <last error>`, written once; so is the report of an event that belongs to no work item.
- A report can fail to post for another reason. The hosting service may be down, or git may fail in the factory's checkout while the report resolves the branch. The factory then tries to post it again on the next tick, without counting an error.

Every counted error also writes one line to the factory log, so that the first two errors, which post nothing, can be read:

```text
2026-11-04T09:40:41Z handler error <event key> 2 of 3: PushFailed: push of work-item/<id> failed: rejected: remote: Internal Server Error | ! refs/heads/work-item/<id>:refs/heads/work-item/<id> [remote rejected] (Internal Server Error)
```

The line reads `handler error <event key> <n> of <cap>: <exception type>: <text>`. The text is on one line (line breaks become spaces) and at most 300 characters.

### A refused push is tried again

The factory tries a push again after a wait when the remote may take it then. This holds for the push of a stage's result and for the push of a change the factory records. Those changes are a crash, an expiry, the hand-over's record and the archive of a merge. Only two failures count: a refusal by the server (git's `[remote rejected]` on the refused ref's line, for example `Internal Server Error`) and a remote that cannot be reached.

- The factory waits 5 s and pushes again, then 15 s, then 45 s. Each wait writes `push: retry <n> of 3 in <s> s: <reason>` to the factory log.
- The push is the same command each time, on the same commit: no force, no rebase, no new commit.
- If the fourth push fails too, `PushFailed` is raised, and the stage's crash or the event's error is counted.
- A rejection with `! [rejected]` (`non-fast-forward`, `fetch first`) is not tried again: the remote moved, and a wait does not change that. It fails at once, as does the push of a stall, which is never tried again.

The reason in a `PushFailed` is git's own. The rules that shape it are in *Reference*. The reason is in every report and log line that names the error, for example `push of work-item/<id> failed: unreachable: fatal: unable to access 'https://...': Could not resolve host: github.com`.

### During an outage of the hosting service

The factory stops nothing and leaves nothing half-written on the remote during an outage of the hosting service. What it does:

- The hosting client (PyGithub) retries a failing call up to five times with a backoff (factor 2), writes by `PATCH` included. A short outage ends inside the call.
- A refused or unreachable push of a result or a recorded change is tried again after 5, 15 and 45 s (see above), so an outage of up to about a minute ends without a crash.
- A longer outage makes the stage a crash, rerun at the next look (see "A restart during a stage" in [work-items.md](work-items.md)). An event is a counted error, and after three the factory posts one report. Each counted error is in the log with its reason.
- A report that cannot be posted is tried again on the next tick without a count.
- A hosting failure right after a stage's claim (the pull request cannot be opened or found, so no agent has run) releases the claim. The factory commits `<id>: claim released: hosting failed` on the work item's branch and pushes it, with the retries above. The next tick starts the stage afresh, and no crash is charged for a stage in which no agent ran. The journal gets no entry from the release; attempts, round and the crash count do not change.
- Because the release moves the branch, each failing tick counts its error from 1 again (`handler error <event key> 1 of 3: HostingServiceError: ...`). Such an outage therefore never reaches the error cap and posts no error stop: the factory tries again every tick until the service is back.
- If the release itself cannot be pushed (the retries spent), the log says `claim release not pushed: ...`, the claim stands, and the next tick records a crash.
- An error other than a hosting failure after the claim releases nothing.

**You do:** read the log for `push: retry` and `handler error`; do nothing while they pass. When an event is capped, push a commit to the branch once the service is back (see "An event that keeps failing").

## Stops that cannot be done

**You see** a report on the work item's pull request, as under "An event that keeps failing". Its last error starts with `cannot handle`, as in the table below.

**It means** the factory met one of three situations it has no work for. Each is a counted error, never a silent success. The factory tries the event three times and then posts one report. It opens a draft pull request for the report first when there is none. A restart posts no second report. Apart from the report, the factory writes, posts and changes nothing for these events.

**You do** what the last column says.

| Stop | Last error in the report | What to do |
|---|---|---|
| A work item that exists twice | `cannot handle duplicate: two work items share the id <id>`, followed by `: <the files>` when they are named | Two files carry the same id. Keep one, and rename or delete the other on `main` (or on its branch); the factory does not choose for you. |
| A failed pull request lookup | `cannot handle pull_request_lookup: the pull request lookup for <branch> failed`, followed by `: <cause>` when there is one | The hosting service could not say whether the branch has a pull request (rate limit, outage, token). Fix the cause named after the colon. A push to the branch starts the count again; nothing else does. |
| A question with no pull request to post it on | `cannot handle ask: work item <id> has no pull request` | The question is recorded in the journal but has nowhere to go. Open a pull request for the work item's branch, or push a commit to the branch so the factory tries again; the report itself opened a draft if the branch was on the remote. |

## Reference

### The causes of a stall

A stall note gives one of nine causes. The reason in the journal is in brackets where the guide names it.

| Cause sentence | What happened |
|---|---|
| the agent run died without a result | The agent's process ended with no result. |
| the agent run reached its time limit | The run passed the role's `time_limit`. |
| the agent run spent its budget, and the resume too | The run used its budget and so did the resume. |
| the provider's spend limit lasted past the waiting ceiling (`provider_limit`) | The provider's limit was still there after the whole ceiling. |
| the agent gave no valid decision and entry | The run ended without a decision and an entry the factory can read. |
| the agent's decision is not an allowed one | The decision is not in the stage's allowed list. |
| the work item's form broke during the stage | The work item file no longer follows its form. |
| a check is red after the stage | A check of the stage exited with a status other than 0; its name follows the colon. |
| merging the main branch conflicts and the merge was aborted | The merge of `origin/main` into the branch conflicted. |

### The reason of a failed push

The reason in a `PushFailed` is built from git's output in these steps:

- It is the last non-empty lines of git's output, at most three, joined with ` | ` and cut to 300 characters in all.
- Git's advice lines are left out: `Please make sure you have the correct access rights`, `and the repository exists.` and any line that starts with `hint:`.
- The frame of the porcelain summary the factory asks git for is left out: a line `To <url>` and the line `Done`. The server's own `remote:` lines stay, so `remote: Done` is kept.
- Git's line `error: failed to push some refs to '<url>'` is left out, because it only repeats what the ref line says and names the remote.
- Any other `error:` line stays, because it can be the only cause (`error: src refspec main does not match any`). So does a line that holds those words further in (`remote: error: failed to push some refs to x`).
- Every run of whitespace in a kept line, a tab included, becomes one space, so the reason is one plain line.

### The wording of a failing probe

A probe of `main` that fails without printing anything names the command and how it ended, for example `lint ended by signal 15 and printed nothing on main at <commit>` or `lint ended with exit status 2 and printed nothing on main at <commit>`.

### The events the factory handles

Every kind of event has a handler, so an event is never refused for lack of one. The kinds are `comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `duplicate`, `pull_request_lookup`, `crash`, `expired` and `acceptance_due`, together with the events of a stage run. A `crash` is explained under "A restart during a stage" and an `expired` under "An expired lease", both in [work-items.md](work-items.md).
