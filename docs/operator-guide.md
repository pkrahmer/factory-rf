# Operator guide

The guide for the person who runs the factory this repository implements: how to install it, how to configure it, which stops it can reach and what to do about each. Parts are built: the wrappers for git, the build commands and the `claude -p` runtime, the hosting-service client, the factory log and the health status file, the stops of the repository, the machine and a work item, the pipeline definition with its reader, rules and loader, the agent definition reader, the claim of a stage with its lease, the write paths with the guard and the undo, the stage protocol (one stage run from the pushed claim to the result commit, with stalls, checks and reports, and v1's decision rules with the factory's own questions), and the cost records with the bill. The commands to run so far are `factory-check-story` and `factory-bill` (you run them) and `factory-guard` (the agent runtime runs it); there is nothing else to start; the sections below describe what the built parts expect of your machine and your project. The documenter stage extends this from each story's docs criterion.

## The project's make targets

The factory runs a project's build through make and calls three targets: `check` (the full gate, which must be green before a stage hands forward), `lint` (run after the tester stage) and `test`. A project must define them in the Makefile at the root of its checkout. Each is judged by its exit status alone, and a target that does not exist counts as a failed command. A target that runs past its time limit is killed and counts as failed for that reason; the factory reads only the exit status, the last line and the last 30 lines of the output.

## The agent runtime

The factory runs each agent as a `claude -p` call under your own `claude` login: it needs the `claude` program and a session you have already logged in to, and it holds no API key of its own. The call gets only the environment the run's request gives, with no variable inherited from the factory. The flags are those of v1 and have not yet been checked against the pinned `claude` version. If a call fails at once, check them first. The factory asks `claude --version` and takes the first word of its output (for example `2.1.289`). The pinned version is the one the flags were written for; the preflight that compares it arrives with F0010, and until then nothing checks it.

A run whose budget is spent is not lost: the factory resumes the same session once with a quarter of the budget (at least 0.50 USD) and asks the agent to finish with its decision, `question` if the work is not done. That costs up to that extra amount, and the cost and tokens of both calls are added up. If the resume is also over budget, the run stops as a stall; there is no third call. A run that dies, runs past its time limit or returns no usable decision stops the work item as a stall. One `time_limit` covers both calls: the resume gets what is left. A run the `time_limit` ends is killed, is not resumed, and shows its cost, tokens and turns as unknown.

### `factory-guard` on the agent run's `PATH`

The write-path guard is the command `factory-guard`, installed with the factory like `factory-check-story`. The runtime registers it as a Claude Code hook that refuses an agent's `Edit` or `Write` outside the stage's write paths. The runtime adds no `PATH` to the call, so the `PATH` of the agent run's environment must contain `factory-guard`. If it does not, the hook cannot start, and what Claude Code does then is not the guard's refusal; F0010's preflight will probe for it, until then nothing does. The guard reads only the settings file the runtime wrote for the run and exits 2 (a refusal, shown to the agent) for a write outside the write paths, a missing option or an unreadable settings file. A payload it cannot read is allowed. The details are in the project guide, "The guard command".

## The factory log and the health status file

Both live in the factory's state directory. Nothing starts the factory yet, so this describes what the built parts write; the next section says when a stop is written and when it goes away.

### The factory log

`TimestampedFactoryLog` writes every line twice: to standard output and, appended, to a file (UTF-8, lines end in `\n`). A line is `<stamp> <text>`. The stamp is `YYYY-MM-DDTHH:MM:SSZ`: UTC, whole seconds (a fraction is cut off, not rounded). One call can hold several lines, and they all carry one stamp, because the clock is read once per call:

```text
2026-10-12T12:00:07Z first
2026-10-12T12:00:07Z second
2026-10-12T12:00:12Z third
```

Missing parent directories are created. If the file cannot be written, the line has still reached standard output, and the write fails with an `OSError`.

### The health status file

`health.json` in the state directory holds the stops in force for the repository or the machine, as one JSON object: `{"stops": [{"scope": ..., "reason": ..., "detail": ..., "at": ...}]}`. The container's health check will read it; an empty `stops` list is healthy.

- One stop per reason. `scope` is `machine` for `preflight_failed` and `repository` for every other reason; `detail` names the fault and is never blank; `at` is in UTC.
- The reasons are `fetch_failed`, `checkout_restore_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `repository_unavailable`, `main_branch_failing` and `preflight_failed`.
- A file that is missing, cannot be read, is not JSON or is not a valid status reads as healthy (no stops). Do not repair it by hand: the next stop that is raised replaces the whole file, and a fault that lasts is raised again.
- A write goes to a temporary file in the same directory and replaces `health.json` in one step, so a reader never sees half a file. If `health.json` is a directory, the write fails with an `OSError` and leaves nothing behind.

## Stops of the repository or the machine

When the factory finds a fault of the repository or the machine (a failed fetch, a checkout it cannot restore, an invalid pipeline definition, a failing preflight), it raises a stop in two places, and tries both: a line in the factory log and an entry in the health status file. A stop of this kind never goes to a pull request; look in the log and in `health.json`.

The line when a stop is raised:

```text
2026-10-12T12:00:07Z stop repository fetch_failed: origin unreachable
```

That is `stop <scope> <reason>: <detail>`, after the stamp. `scope` is `repository` or `machine`; `reason` is one of the reasons listed under the health status file.

The line when the fault is gone:

```text
2026-10-12T12:00:12Z stop cleared fetch_failed
```

That is `stop cleared <reason>`. It is written only when the stop was in the health status; clearing a reason that is not stopped writes nothing.

- The health status holds one stop per reason. A stop raised again for a reason already there replaces the earlier one where it stood (with the new detail and time); it is not added twice. A new reason is added at the end. A fault that lasts is raised every cycle, so the log repeats the line and the status does not grow.
- A stop is removed from the health status, then the cleared line is written, when the factory finds the fault gone. You never clear one by hand; deleting `health.json` only hides it until the next cycle raises it again.
- One failing destination never loses the stop. If the log file cannot be written, the stop is still put into the health status; if the health status cannot be written, the line still reaches standard output and the log file. In both cases the factory then reports the write error (an `OSError`); when both fail, it is the log's error. If the health status cannot be written while a stop is cleared, the stop stays in force and no cleared line is written. If the log cannot be written while a stop is cleared, the stop is already removed.

## Stops of one work item

A stop of one work item (a question, a cap reached) is meant to appear as one comment on that work item's pull request. Today a question is only recorded: a journal entry of kind `question`, with `blocked` set. Posting it on the pull request arrives with F0007. The rules below are those of `StopService.post`, which nothing built calls yet. A stall does not follow them: it has its own rule, given under "A stall: the stall note". A posted comment says what each possible answer will do, and it ends with the factory's marker and the stop's key:

```
<!-- factory -->
<!-- factory key=F0001-S0001:stall:3 -->
```

- If the work item has no pull request yet, `StopService.post` opens a draft pull request first, on the work item's branch (`work-item/<id>`), and posts the stop there. The description says: "The factory opened this draft pull request to report a stop on <work item>. The stop is the comment below."
- It opens one only when the branch is on the remote with a commit beyond `main`. Otherwise it opens nothing, posts nothing and reports a `create_pull_request` error: `branch <branch> is not on the remote with a commit beyond main`. The factory pushes the branch before it can report a stop, so you see this only if the remote branch was removed or reset.
- If the work item's branch already has an open pull request, the factory posts on that one. A pull request you closed or merged is not reused for a new one; but when the work item's state records a pull request number, the stop is posted there even if you have since closed it.
- A restart never repeats a stop. The key identifies the stop: if the factory died after posting and before recording it, the next attempt finds the key on the pull request and posts nothing. The same key with another text is still a repeat; a different kind or number is a new stop and a new comment.
- The factory records the pull request's number in the work item's state when it opened or found the pull request; the posting itself writes no state.

## What a stage run shows

One stage run leaves these traces on the remote and the pull request, in this order:

1. **The draft pull request.** The first stage of a work item opens it, titled `<id>: <title>`, with the work item's text as the description. Only an open pull request is reused; a closed or merged one never is, and a new draft is opened instead.
2. **The stage-start commit.** It is pushed before any agent runs. It holds the claim and one journal entry, speaker `factory`, kind `started`, with the text `factory: started <stage> as <instance>.` (for example `factory: started doing as factory-1.`). If this push fails, no agent runs.
3. **The agent's entry.** The speaker is the agent's role and the kind is `result`, or `question` when the agent asked; code writes both, the agent writes the words. For each green check and each report the entry ends with one line `` `<command>`: <last line of its output> ``, for example `` `check`: 12 passed ``.
4. **One commit by the factory**, above the stage-start commit (or above the agent's last commit, when the agent committed): the result commit, or the stall commit after a stall. It holds the whole work tree.
5. **The label** `stage:<stage>` (written so, for example `stage:review`) on the pull request. It is written after the result commit is pushed, and after a stall's note is posted. It is a projection of the stage and is never read back.

If the push of the result commit fails, no label is written. If the hosting service fails at the label, the commit stays pushed.

## A stall: the stall note

A stall is a stage that ended without a result the factory can keep. The causes are the nine listed below; the first ones are an agent run that died, ran past its time limit, spent its budget (and the resume too), or gave no valid decision and entry. A stall costs one attempt of the work item and is never a crash. The factory keeps what the agent wrote inside the stage's write paths, undoes the rest, releases the claim and pushes one commit with a `stall` entry in the journal. Only then does it post the stall note on the pull request and write the pull request's `stage:` label for the stalled stage, so a work item whose first stage stalls has its label too. The note's key is `<work item>:stall:<n>`, where `n` is the number of the stall entry.

The note reads:

```text
Stalled (attempt 1 of 2): the agent run died without a result. Retrying on the next tick.
```

- `attempt n of m`: `n` is the work item's attempts after this stall; `m` is `attempts_cap` of the pipeline definition.
- The cause is one sentence. The reasons are: the agent run died without a result; it reached its time limit; it spent its budget, and the resume too; the agent gave no valid decision and entry; the agent's decision is not an allowed one; the agent left the work item's branch; the work item's form broke during the stage; a check is red after the stage; merging the main branch conflicts and the merge was aborted. A detail, such as the name of a red check, follows the sentence after a colon. A detail of several lines (the output of a red check) puts its first line in the sentence and the other lines in a code block below it; see "A stall by a red check".
- The note says "Retrying on the next tick." only while `n` is below `m`. Nothing for you to do then; the next tick runs the stage again from what the stall kept.
- At the cap the note ends `The attempts cap is reached; the factory asks you next.` and says nothing about retrying. Stopping the stage at the cap and asking the attempts-cap question are not built yet: the evaluation arrives with F0006 and the question with F0007. Until then the note only counts. Once they arrive, you read the cause and the stall entries in the work item's journal, fix what stops the stage (the agent, the stage's time limit or budget, the pipeline definition, the project's checks, a conflict with `main`), and answer on the pull request; the factory does not run the stage again until you have.
- The stall's pull request: an open pull request of the work item is reused; otherwise the stall opens a new draft titled `<id>: <title>` with the work item's text as description. It does not use the stop description, and it does not post on a closed pull request.

If the hosting service fails while the note is posted, the stall commit is already on the remote, no note is posted and no label is written. If it fails while the label is written, the note is posted and the label is missing. The error is reported, and the work item shows the stall in its file and journal.

## A stall by a red check

When the agent decides to move forward and the stage has checks, the factory runs them itself, in the order of the pipeline definition, and stops at the first that is red. A check is green only when its make target exits 0. A red check is a stall that costs one attempt; the stage, the round and the crash count stay. On the pull request you see the stall note with the cause `a check is red after the stage` and, after a colon, the check's name; below the sentence, in a code block, come the last 15 lines of its output (all of them when it printed fewer). The block keeps GitHub from rendering the output as Markdown. A note looks like this:

````text
Stalled (attempt 1 of 2): a check is red after the stage: `check`. Retrying on the next tick.

```text
  File "x.py", line 1, in <module>
make: *** [Makefile:6: check] Error 1
```
````

In the work item's journal the agent's entry comes first, ending with one line per check that was green, and the `factory` stall entry follows.

What to do:

- Below the attempts cap nothing: the next tick runs the stage again, and the agent sees the journal.
- At the cap, read the 15 lines and run the target yourself (`make check`) on the work item's branch. Fix what is wrong (the code, the target, or a tool missing on the machine), then answer on the pull request. Stopping at the cap and asking the attempts-cap question are not built yet (F0006's evaluation, F0007's question); the answer is what the operator does once they are.
- Reports (the stage's `reports`) run after all checks are green. They are recorded and never hold a move. Every report that ran adds one line `` `<command>`: <last line of its output> `` to the agent's entry, passed or failed; the line has the same form either way, so only its last line shows whether the report passed. A failing report holds nothing and stops nothing.

The result commit of every stage holds the whole work tree. Make sure the project's `.gitignore` covers whatever its checks create (build output, caches, coverage files); otherwise the factory commits it.

## The factory's own questions

Besides an agent's `question`, the factory asks you itself in two cases. Today each question (the agent's, the findings question and the round-cap question) is recorded as a journal entry of kind `question`, and the work item's `blocked` is set until you answer. Posting it as a comment on the pull request arrives with F0007. Once it does, each is a comment on the pull request.

- **The form has findings.** The agent decided to move forward, but the work item's form still has findings after the run. The comment reads: `The work item's form has findings, so the stage cannot move forward: 1. <message> 2. <message>. What should happen? Answer with a comment; the stage then runs again. Close the pull request to discard the work item.` The stage stays where it is and the round is not counted. Answer with a comment (say how to fix the form, or that the finding is wrong); the stage then runs again. Closing the pull request discards the work item.
- **The round cap is passed.** A stage with `round_cap` sent the work item back once more than the cap allows. The comment reads: `This work item has now been sent back <n> times, more than <cap>. What should happen? Answer with a comment; close the pull request to discard the work item.` The stage stays where it is and the round shows the count. Answer with a comment; closing the pull request discards the work item.

A stage without `round_cap` sends back without limit and never asks. Sending back counts rounds; a stall counts attempts (see "A stall"), and the two caps are separate.

## The stop `pipeline_definition_invalid`

The pipeline definition is `factory/pipeline.yml` as it stands on `origin/main`, never the file in the work tree. The factory loads it each cycle, and a load that refuses it raises the stop `pipeline_definition_invalid` (scope `repository`): a line in the factory log and an entry in the health status, nothing on a pull request.

```text
2026-10-12T12:00:07Z stop repository pipeline_definition_invalid: missing key: contract
```

The detail is the fault. The faults the load reports:

| Fault | Cause and what to do |
|---|---|
| `factory/pipeline.yml is missing at origin/main` | the file is not on `main`; merge it |
| a fault of the text, such as `missing key: contract`, `unknown key: <path>`, `invalid <path>: <message>`, `not valid YAML: <problem>` | fix `factory/pipeline.yml` on `main`; several faults are joined by `; ` |
| a fault of the rules across keys, such as `stage doing: next names unknown stage ship`, `contract major 2 is not supported (this factory reads major 1)`, `role coder: write_paths is empty`, `role coder at stage doing: 61 min exceed lease_duration 60 min` | fix `factory/pipeline.yml` on `main`; see "The pipeline definition" for the rules you meet most often and the project guide, "The rules of the definition", for the full list |
| `role <role>: agent is not installed` | the role has no file `<agent home>/agents/<role>.md`; install it. Every missing role is named, in the order of `roles`, joined by `; ` |
| `agent home unavailable: <fault>` | `<agent home>/agents` is missing or is not a directory (see "The agent files") |

The agents are checked only when the text itself is valid, so a broken file and a missing agent home show the file's fault alone until it is fixed. A key with a default may be left out and takes it; a key without one that is missing is a fault.

The stop clears itself at the next load of `origin/main` that succeeds, with the line `stop cleared pipeline_definition_invalid`; stops of other reasons are not touched. Only the load of `origin/main` raises or clears this stop: a look at the definition on another branch can be refused, but it changes neither the health status nor the log. A git failure while reading (an unreachable repository, an unknown ref) is not a fault of the definition and raises no stop. If the health status cannot be written, the load reports an `OSError` and not the fault; the log line has been written. What the cycle does while the stop stands is described with the tick.

## The stops of the tick

A tick works from the remote alone: the checkout is disposable. It fetches first, loads the pipeline definition from `origin/main`, puts the checkout back on `main` at `origin/main`, and only then looks at the work items. Three repository stops end a tick before it looks at any work item; each is a log line and a health status entry, never a comment on a pull request. The next tick tries again and clears the stop when the fault is gone.

| Stop | Meaning | What to do |
|---|---|---|
| `fetch_failed` | `git fetch` failed; the detail is git's message. | Fix the network, the remote's address or the credentials. An expired or revoked token shows as `fetch_failed` too: renew the token. Nothing is lost; the next tick after a successful fetch carries on. |
| `pipeline_definition_invalid` | `factory/pipeline.yml` on `origin/main` is refused. | See "The stop `pipeline_definition_invalid`". The tick does not touch the checkout while this stop holds. |
| `checkout_restore_failed` | The factory could not put the checkout on `origin/main` (for example, an untracked file or directory it cannot remove); the detail is git's message. | Fix the cause in the checkout, such as a path's permissions, or delete the checkout and clone again. |

The restore throws away every uncommitted change and every untracked file in the checkout (ignored paths stay) and deletes the local branches of the work items, so that a stage starts from the remote's branch. When it throws changes away it writes one line to the log, `discarded uncommitted changes: <path>, <path>`. Do not keep work in the factory's checkout.

A work item file that cannot be read is not a stop. The tick ends with the error, naming the file's path, and does so on every tick until a human repairs the file on its branch (or on `main`, for a story that has not started) or closes the pull request. A work item in a stage that the pipeline definition lacks fails the same way.

v1's leftover files in `.git/` (`factory-run.json`, `factory-tick.lock`, `factory-tick.json`) are neither read nor written; they change nothing and can be deleted.

## The pipeline definition

`factory/pipeline.yml` is the project's configuration: its stages, the roles that work in them and the limits. The factory reads it only as it stands on `origin/main`, so a change takes effect when it is merged. This definition loads:

```yaml
contract: '1.0'
roles:
  tester:
    write_paths: ['tests/*', '{work_item}']
  coder:
    write_paths: ['src/*', '{work_item}']
stages:
  testing: {role: tester, next: [doing], checks: [lint]}
  doing: {role: coder, next: [review], checks: [check]}
  review: {approval: true, next: [done, doing], round_cap: 3}
  done: {}
```

The keys, with what a left-out key takes:

| Key | Meaning | Default |
|---|---|---|
| `contract` | the contract version, quoted: `'1.0'` | required |
| `stages` | name to stage; the order in the file is the pipeline's order | required |
| `roles` | name to role; the name is also the agent file's name | required |
| `project_commands` | name to `time_limit` in minutes | `check`, `lint` and `test`, each 10 |
| `attempts_cap` | attempts before the human is asked | 2 |
| `crash_cap` | crashes before the human is asked | 2 |
| `acceptance_stage` | the stage of the feature acceptance | none |

A stage has `role` (none: no agent runs), `next` (the first name is the forward move), `approval` (the human decides), `checks` (project commands that must pass after the agent), `reports` (project commands run after green and only recorded) and `round_cap` (none: no cap). A role has `write_paths` (required), `lease_duration` (60 minutes) and `time_limit` (40 minutes, one agent run). A write path may hold `{work_item}`, the work item's own file, and `{feature}`, its feature's path (`factory/features/F0004-x`). The engine's protected paths (`factory/pipeline.yml`, the forms, `feature.md`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `.claude/`) are outside every write path. Every limit is a positive whole number.

The rules you meet most often:

- The stage `done` must exist, with no role and no `next`. Write it `done: {}`; `done:` alone is refused.
- The contract major must be 1. Any minor is read.
- Every stage other than `done` needs a non-empty `next` and either a role or `approval: true`; every name in `next` must be a stage.
- The lease: for each stage with a role, the role's `time_limit` plus the `time_limit` of every command in the stage's `checks` and `reports` must be at most the role's `lease_duration`. With the defaults, 40 + 10 (one check) + 10 (one report) = 60 fits; a stage with two checks and a report adds up to 70 and is refused. Raise the `lease_duration` or lower a limit.
- Values are taken only in their YAML type: a limit is an integer (not `'30'`, `30.0` or `true`), `approval` is `true` or `false` (not `'yes'` or `1`), names and write paths are text. A write path must hold a character that is not whitespace.
- A key that is not listed is refused, so a misspelt key is never ignored. A given `project_commands` replaces the default set as a whole: list `check`, `lint` and `test` again if you still want them.
- Every role needs an agent file (see "The agent files").

A refused definition raises the stop `pipeline_definition_invalid`, described above. The project guide, "The rules of the definition", lists every fault.

## The agent files

An agent is a file `<agent home>/agents/<name>.md`. The name is lowercase letters, digits and hyphens, starting with a letter (`coder`); `README.md` and `Coder.md` are not agents, nor is a file with another suffix or one in a subdirectory. Every role of the pipeline definition needs an agent file of the same name.

The file is YAML front matter between two lines of three hyphens, then the agent's instructions:

```
---
model: sonnet
tools: [Read, Write]
effort: low
budget_usd: 0.1
---
The agent's instructions.
```

| Key | Meaning |
|---|---|
| `model` | required, text |
| `tools` | required, a list of texts; `[]` is allowed |
| `effort` | optional, text |
| `budget_usd` | required, a number greater than 0 |

The body, without the whitespace around it, is the instructions; a line of hyphens inside it belongs to it. Any other front matter key is ignored for now: which ones the agent runtime applies is decided with F0010.

The reader reports these faults. `read` names the agent; a fault with a key names that key.

| Fault | When |
|---|---|
| `no agents directory at <path>` | `<agent home>/agents` is absent or not a directory |
| `not an agent name: <name>` | the name is not a valid name, so no file is looked up |
| `no agent file <path>` | the file is absent or is a directory |
| `cannot read: <reason>` | the file cannot be read or is not UTF-8 |
| `no front matter` | the file does not start with front matter that is closed |
| `front matter is not valid YAML` | the YAML does not load |
| `front matter is not a mapping` | it loads as a list or a scalar |
| `missing key: <key>` | `model`, `tools` or `budget_usd` is left out |
| `budget_usd must be greater than 0` | zero, negative, text or a boolean |
| `invalid <key>: <reason>` | any other value of the wrong type |

When a file has several faults, the first is reported: a missing key before an invalid value.

## Checking a story before it starts

`factory-check-story` checks story files against where they sit and against your project's `factory/story-form.md`. Run it from the root of a checkout, with the paths relative to that root. The checkout must be laid out the v1.1 way: `factory/story-form.md`, a `feature.md` in each feature's directory, and the stories in `backlog`, `in-progress` or `done`.

This repository's own `factory/` tree is v1's (`drafts/`, `ongoing/`, `FEATURE.md`, `TICKET.md`), so the command does not apply to it: run here it prints `cannot read factory/story-form.md: ...` and exits 2. That holds until this repository moves to v1.1's layout.

In a project laid out the v1.1 way (the paths are placeholders):

```bash
uv run factory-check-story factory/features/F0001-example/backlog/F0001-S0001-example-story.md
```

prints `factory/features/F0001-example/backlog/F0001-S0001-example-story.md: ok` and exits 0 when the story fits the form.

`uv run python -m factory.entry.check_story <path>...` does the same. For each path, in the order given, it prints `<path>: ok`, or one line per finding: `<path>:<line>: <message>` where the finding has a line (a line of the story's text after the front matter, counted from 1), and `<path>: <message>` where it has none. Findings about where the file sits come first, then those about its content.

| Status | Meaning |
|---|---|
| 0 | every file is ok |
| 1 | at least one file has a finding |
| 2 | the command could not do its job: no path (it prints `usage: factory-check-story <path>...`), `factory/story-form.md` unreadable, or a file that does not exist or is not UTF-8 (`cannot read <path>: <reason>`). Nothing more is checked after such a file; what was printed before stays. |

A path must be `factory/features/<feature directory>/<backlog|in-progress|done>/<file>.md`. Otherwise the only line is `not a work item location: ...` and the file is not read (it need not exist). `drafts` and `ongoing` are v1's folders and not work item locations, so they are not accepted.

How a file is read depends on its folder and on whether it has front matter. A story in `backlog` is read as a specification: front matter there is a finding. A story in `in-progress` or `done` with front matter is read as a work item and its state is checked too. A story there with no front matter is a started story as you moved it on `main`, where the state lives on the work item's branch; it is checked like a backlog story, with no complaint about missing state.

Findings about the place, and what to do:

| Finding | What to do |
|---|---|
| `the file name "<name>" is not F0000-S0000[-slug].md` | rename the file; an acceptance's name is not a story's |
| `the feature directory "<directory>" is not F0000[-slug]` | rename the directory |
| `the story <id> is in the directory of feature <id>` | move the story to its own feature's directory, or fix its id |
| `the feature file feature.md is missing in factory/features/<directory>` | add the feature's `feature.md` |

Findings about the content follow the form check (`docs/project-guide.md`, "The form check of a story"):

| Finding | What to do |
|---|---|
| `the story has no title line` | start the story with a `# Title` line |
| `missing section: ## <heading>` | add the section your story form lists |
| `criterion numbered <n> where <m> is expected` | renumber the criteria 1, 2, 3 |
| `the second-to-last criterion must contain "make check" and "green"`; `the last criterion must start with "docs:"` | make those the two closing criteria |
| `the Smoke test has no code block`; `the code block opened at line <n> is not followed by an "Expect:" line` | give each block of the smoke test an `Expect:` line after it |
| `journal entry numbered <n> where <m> is expected` | renumber the journal entries |
| `a backlog story carries no front matter: <keys>`; `a backlog story carries no journal entries` | remove the front matter or the entries; the factory writes them when the story starts |
| `the story has no state`; `the journal data lists <n> entries but the text shows <m>` | for a file with front matter in `in-progress` or `done`: the state is damaged, so restore the file from its work item's branch |
| a reader fault such as `unknown key: <key>` or `front matter is not valid YAML` | fix the front matter; no form findings are given until it reads |

## What a work item cost: `factory-bill`

Every agent run writes a cost record beside its work item. `factory-bill` adds the records up and prints the bill. Run it from a checkout of your project:

```bash
uv run factory-bill F0001-S0001
uv run factory-bill
```

With an id it prints the cost table, an empty line and `Cost: <line>`. With no argument it does that for every work item in flight, each block headed by its id and separated from the next by an empty line. A work item in flight is one that has a branch `work-item/<id>` on the remote.

The command reads the remote-tracking refs only (`origin/<the work item's branch>`, or `origin/main` for an archived work item), never your working tree and never the journal. It does not fetch: run `git fetch` first to see the latest records. Two checkouts that have fetched the same remote show the same bill.

| Exit status | Meaning |
|---|---|
| 0 | the bill was printed (with no argument, also when nothing is in flight) |
| 1 | `no work item <id>`: no file of that id on the remote |
| 2 | `not a work item id: <argument>`, or more than one argument (`usage: factory-bill [<work item id>]`) |

A work item with a file but no cost records has a bill of 0 runs and $0.00.

### The cost table

```
| stage | runs | min | turns | in | cached | out | USD |
| :-- | --: | --: | --: | --: | --: | --: | --: |
| tests | 1 | 1.0 | 7 | 62 | 1000 | 300 | 0.35 |
| doing | 2 | 2.5 | 5 | 10 | 500 | 100 | 1.20 + 1 unknown |
| **total** | 3 | 3.5 | 12 | 72 | 1500 | 400 | 1.55 + 1 unknown |
```

One row per stage, in the order the stage first ran; a stage that runs again (`doing`, `review`, `doing`) is one row. The last row is the total.

| Column | Meaning |
|---|---|
| runs | agent runs, every one counted whatever its end: a run that died, ran past its time limit or spent its budget is in the bill |
| min | the runs' duration in minutes, one decimal |
| turns | the turns the runtime reported |
| in | input tokens plus cache-creation tokens |
| cached | tokens read from the cache |
| out | output tokens |
| USD | the cost in dollars, two decimals |

Figures are rounded half up.

### The cost line

The line under the table sums the same figures: `3 runs, 3.5 min, 12 turns, 72 tokens in (1500 more from cache), 400 out, $1.55 + 1 unknown`.

### An unknown cost

A run whose cost the runtime did not report (a run that died, or one the time limit ended) has an unknown cost. It is not counted as $0.00: it is left out of the sum and shown as `+ <n> unknown` after the dollars, where `<n>` is the number of such runs. Unknown turns and tokens are left out of their sums in the same way, without a mark; so the figures are a lower bound when `unknown` is shown.

## Branch deletion on merge must be off

The factory reads a work item's state from its branch `origin/work-item/<id>`. A story in `in-progress/` on `main` with no such branch is read as a new start: it is at the first stage with fresh counters, whatever its file says. So turn off the hosting setting that deletes head branches when a pull request is merged ("Automatically delete head branches" on GitHub). With it on, a merged story whose file is still in `in-progress/` loses its branch and starts again.

## An idle tick that is not empty

When the factory does nothing, the evaluation may still have a reason. An `idle` result names it in its detail:

- A work item waits for the human (blocked, or at an approval stage) and its pull request is open with nothing new. While one waits, no new work starts, even if other work items could run. Answer, comment or merge on its pull request.
- Another instance holds a claim whose lease has not run out. Only one agent runs at a time, so the factory waits for that instance or for the lease to expire.

Neither is a fault. With neither, an idle tick means no work item has anything to do.

## An event that keeps failing

The dispatcher hands each event to its handler and counts what goes wrong, per event and per remote state (the commit the work item's branch is at). Any error from the handler counts, an event kind without a handler included. The tick calls the dispatcher once per pass.

After three errors on one event and one remote state, the factory posts one report on the work item's pull request and stops retrying that event. The report reads: "The factory failed 3 times on `<event>` and has stopped retrying it. Last error: <error>. A new commit on the work item's branch (now at <12 characters of the commit>) makes the factory try again." It is posted once: a restart does not post it again, because the report carries a key that the pull request already holds. If the work item has no pull request, the factory opens a draft one for the report first, as under "Stops of one work item".

What to do about it:

- Read the last error in the report and fix its cause (a broken checkout, a missing tool, a bad file on the branch).
- Push a commit to the work item's branch. That is a new remote state: the count starts again at 1 and the event is tried again. Nothing else restarts it; comments do not.
- Two different events of one work item on one remote state share one report; the one that reached three errors first posts it, and the other is not tried again either.
- A success clears the event's count.

The counts are kept in memory only. After a restart they begin at zero, so the event is tried up to three more times; the report is not posted twice.

If the work item's branch is not on the remote, no pull request can be opened for the report and no later tick would change that. The report is then one line in the factory log, `error cap reached on <event>: <last error>`, written once; so is the report of an event that belongs to no work item. If the report cannot be posted for another reason (the hosting service is down), the factory tries to post it again on the next tick, without counting that as an error.

## Claims, leases and the clock

An instance claims a stage by pushing the stage-start commit; the claim records the instance's name, the start time and the role's `lease_duration` (60 minutes unless the pipeline definition says otherwise, per role). The claim keeps the value it was made with: changing `lease_duration` in the definition affects new claims only, never one that is running.

- Your own claim is recognised whatever its age. After a restart with the same instance name, the instance reruns its stage at once and does not wait for the lease.
- Another instance's claim is waited for until its lease has run out (the age reaches `lease_duration`); then it counts as expired.
- Instances need a synchronised clock (NTP). Expiry compares the start time recorded by the claiming instance with the checking instance's own clock, so a clock that is off by minutes makes a lease end early or late.
