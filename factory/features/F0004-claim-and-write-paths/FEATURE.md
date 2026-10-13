# Claim and write paths

## Goal

A stage is claimed by pushing its stage-start commit. The commit carries a "started" journal entry and the `claim` in the work item's state, which name the instance and the start time, and the push decides who owns the stage: a rejected or unreachable push is no claim. One service, `ClaimService`, creates, reads, recognises and expires claims, and no other module builds or judges one. What an agent may write is read from the pipeline definition as it stood at that same commit, never from the work tree the agent can change: the protected paths that no write path can reach are the engine's own list, and the guard hook that refuses a write during the agent run and the undo that reverts one afterwards judge every path with the same `refusal` over the same settings (the undo also undoes the other files in an `in-progress` folder, decision 13). Done when a claim exists on the remote only after its push, an own claim, a claim held by another instance and an expired claim are told apart by that one service, and a rewrite of the pipeline definition in the work tree widens no write path for the guard or the undo and breaks neither.

## Scope

- The stage-start commit with its "started" entry and the claim in the state, pushed; a rejected or unreachable push raises `PushFailed` and leaves no claim on the remote (R19, R20)
- The lease clock as pure functions, `ClaimService.status` and `ClaimService.release`, `lease_duration` per role copied into the claim (R21), and the search tests that make `ClaimService` the only owner of claims (GH1.2)
- The matching rule for write paths, the placeholders `{work_item}` and `{feature}`, the engine's list of protected paths, the one refusal verdict, and `WritePathService`, which reads the pipeline definition at the stage-start commit (R32)
- The guard hook command `factory-guard --settings <file>` that refuses Edit and Write outside the write paths, reading only the settings file (WE2.1, WE2.3)
- The undo and restore after an agent run: paths changed since the stage-start commit outside the write paths reverted or deleted, other work items in progress undone, the work item's state and journal restored, a deleted or broken work item restored (WE2.1, WE2.2, WE2.3)

## Out of scope

- Starting the agent run after the claim, and refusing to start it when the push failed: F0005 (GH1.1)
- When the undo runs (after an agent run, after a stall), the note about it in the entry, and writing the cost-record file at the right time: F0005
- Recognising a claim at the tick's first look and the events for it: F0006; rerunning a stage after a crash or an expired lease: F0008
- Validating that the agent run's and the checks' `time_limit`s fit inside `lease_duration`: F0003 (GH1.4)
- Writing the guard settings file and registering the hook with the agent runtime: F0001-S0009 (`ClaudeCodeRuntime`, built)
- Reading the protected paths from a project's configuration, a guard that fails closed for a payload it cannot read, a sandbox for agent runs, and the undo of writes to ignored paths or outside the checkout: left for v2 (handover section 8)

## Stories

- S0001 — The stage-start commit is the claim
- S0002 — One service for claim, expiry and recognition
- S0003 — Write paths and protected paths read at the stage-start commit
- S0004 — The write-path guard hook
- S0005 — Undo and restore after an agent run

## Decisions taken for the human

1. The "started" journal entry reads `started <stage> as <instance>.`, and the instance and the start time are data in the state's `claim`, not parsed from the text. The commit's subject is `<stage> starts as <instance>`. (S0001, story text)
2. A claim is made only on the work item's own branch (the branch named for the id in the file name of the work item's path) while it is checked out, and only for a stage that has a role; claiming a stage without a role (an approval, done), a document whose stage differs from the stage, or an instance name outside `^[a-z][a-z0-9-]*$` is a programming error, a `ValueError`, and writes nothing. (S0001, story text)
3. Claiming a document that already carries a claim replaces the claim and appends a second "started" entry; whether to claim at all is the caller's judgement through `status`. (S0001, story text)
4. After a rejected or unreachable push the local stage-start commit stays on the local branch; the remote is unchanged, so there is no claim, and the next tick's restore discards the commit. (S0001, story text)
5. A lease has run out when the claim's age is at least its `lease_duration`, so a claim is still held 59 minutes and 59 seconds into a 60-minute lease and expired at exactly 60 minutes. A negative age, from clock skew, is never expired. (S0002, story text)
6. An own claim is "own" however old it is, so a restart with the same instance name reruns at once; expiry compares the recorded start time with the checking instance's own clock, and the operator guide says that instances need a synchronised clock. (S0002, story text)
7. The expiry uses the `lease_duration` stored in the claim, not the pipeline definition's current value; a later change of the definition never shortens a running claim. (S0002, story text)
8. The protected paths are a fixed list of ten patterns in the engine (`feature.md` and `*/feature.md` count as two), not read from the pipeline definition: `.claude/*`, the project's `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, and a file named `feature.md` at any depth. The project guide, `docs/project-guide.md`, is not protected: the documenter keeps it. `.git/` and `.gitignore` are not on the list, as in v1. They are refused before the write paths, so no write path can reach them. (S0003, story text)
9. A path with a `..` segment, an absolute path or an empty path is never writable, and the refusal texts are `<path> is owned by the human; a change there is a question.`, `<path> is outside the write paths of this stage.`, `<path> is not a path inside the checkout.` and, in the guard, `<path> is outside the checkout.` (S0003, S0004, story text)
10. A write-path pattern may contain only the placeholders `{work_item}` and `{feature}`; any other `{name}` is a `ValueError` naming it. (S0003, story text)
11. The guard refuses with exit status 2 and the message on standard error, which is how Claude Code blocks a tool call. It judges the real path (`..` and symbolic links resolved) of the file a tool call names, and a path outside the checkout is refused. (S0004, story text)
12. The guard keeps v1's fail-open reading of the payload: a payload that is not JSON, or names no `file_path`, is allowed (handover section 8 leaves a guard that fails closed for v2). A settings file that is missing or invalid is the opposite: the guard refuses everything with status 2 and names the file. (S0004, story text)
13. The undo undoes everything else directly in an `in-progress` folder of a feature whatever the write paths say: every other work item in progress, every cost-record file (the work item's own included) and any other file there. The rule is a test on the path's shape, because `folder_of` is `None` for a cost-record file. The guard does not know that rule and may allow such a write during the run. F0005-S0008 writes the run's cost record after the undo, from the values it holds, so the undo never loses a record the factory wrote (GH4.1). (S0005, story text)
14. A work item that the agent deleted or whose front matter it broke is restored whole from the stage-start commit; its edits to its sections are lost in that case. When the front matter is readable, the state and the journal are restored and the section edits stay. (S0005, story text)
15. The undo changes the work tree only: it makes no commit, and a commit the agent made itself stays in the history. (S0005, story text)
16. `WritePathService.at` parses the pipeline definition at the stage-start commit directly and does not go through `PipelineLoader`. The loader (F0003-S0006) is the one place that loads the definition for the tick, with its stops and its check of installed agent files; the guard's settings and the undo read only the write paths at a commit, so that the undo cannot fail on an agent file removed since the load. F0003's `FEATURE.md` is to say the same. (S0003, story text)
17. Whatever the caller left uncommitted in the work tree becomes part of the stage-start commit, because `commit` stages every change: for a new branch, the opening is the first stage's claim, one commit. (S0001, story text)
18. The lease copied into a claim comes from the definition the caller loaded and gave to `ClaimService` (normally the load of `origin/main`, which the stage-start commit contains); the write paths come from the definition as the stage-start commit holds it. (S0001, story text)
