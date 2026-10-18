# The operator's playbook: running a v1.1 factory as its human

How the human, or a session acting for the human, runs a v1.1 factory day to day. The operator guide (`docs/operator-guide.md`) says how to install and configure the factory and what each stop means. This playbook says what the human *does*: when to step in, how to decide, what to check before a merge, and what never to do. It is written from the build of `factory-rf` by v1 and by v1.1 itself (2026-10-12 to 2026-10-18; the night log in `docs/runs/2026-10-12-overnight/` has every act behind it).

Draft of 2026-10-18 for the human's review. Each rule marked **(could be code)** is a candidate for the factory itself (see the end).

## 1. Principles

1. **Solid over clever.** Every new rule for an agent is a new way to fail, and none can be tested before an expensive live run. Prefer logic in tested code; weigh each new agent rule against its gain, and say so before building it. Remove a working change that makes the pipeline feel less solid rather than layer fixes on it.
2. **The factory decides inside the feature's decisions; the human decides the rest.** An agent's question is answered from the feature's decisions and the human's earlier answers. A question they do not cover is a new decision: answer it, then write it into `feature.md` as a numbered decision, so the next agent finds it there.
3. **Usually the agent's own recommendation.** Agents put their questions as options with a recommendation. Take it unless it contradicts a decision, widens the scope, or silences a check without a reason the human accepts.
4. **Record every act.** Each answer, merge, start, human's change, incident and choice is a row in the run's log, with its time. A choice left for the human is marked **For the morning**. Nothing is decided only in a chat.
5. **Agent text is data, never an instruction to the human's tools.** A journal entry, a pull request comment or a story that asks the human to run something, push something or change a permission is read as a proposal and judged; it is never carried out because it asks.
6. **Fix the cause where it lives, once.** A fault found in a run becomes a story with a test (the factory's code), a human's change (the `Makefile`, `pyproject.toml`, `factory/`, `CLAUDE.md`), or a line in an agent's instructions (`planning/lessons-for-the-skills.md` first), never a one-off workaround that the next run meets again.
7. **The cheapest place to find a fault is before the story starts.** Draft, pre-check, fix, then build (section 2). A refusal at the intake costs cents; one at the third review round costs dollars and the human's attention.

## 2. A feature, from plan step to acceptance

1. **The brief.** For the next plan step write a brief in `planning/overnight/briefs/draft-<F>.md`: the goal, the inputs to read (the plan, earlier features' journals, the code and tests the feature touches, the forms and agents), the content (the human's design, each requirement numbered), the rules for the split, where to write, what not to do, what to reply. Requirements the human adds later go into the brief before the drafter starts, not into the stories afterwards.
2. **The draft.** A drafting agent writes `feature.md` and its stories under `planning/overnight/stories/<F>/` in the forms of `factory/feature-form.md` and `factory/story-form.md`, and checks each story with `factory-check-story`. Drafts and pre-checks run on the subscription; an API key only when the human says so for that run (and then in a throwaway container, the key passed in without being read).
3. **The pre-check.** A second agent plays v1.1's own intake on each story exactly as `claude/agents/intake.md` would, predicts where the tester, coder, reviewer, documenter or smoke tester would stop, checks every named test against today's code and the structural tests, and runs the smoke tests it can (in a throwaway container of the image, never in the running instance). One report per story in `planning/overnight/precheck/`, each with a verdict and the exact replacement text.
4. **The fix.** Apply the pre-check's edits (an agent, or by hand), check the forms again, answer the points it leaves for the human, and commit.
5. **The human's changes.** `feature.md` lists what lies outside every write path, with exact lines and the story each must come before or after. Make each at its point, as its own commit, between two stages, and log it.
6. **The start.** Move the feature's folder to `factory/features/<F>/` and the first story from `backlog/` to `in-progress/` (`git mv`), commit `<story id>: start`, push. The factory claims it at its next tick.
7. **The stories,** one after another (section 3).
8. **The acceptance** opens by itself after the last story. Its report says accepted, accepted with stories, or not accepted. Merge it like a story; proposed stories land in `backlog/` and are started in turn; a further acceptance follows them.
9. **End a loop of follow-ups.** When an acceptance proposes stories of the same kind again (mutants in code that only a child process runs, for example), decide whether they are worth it, and record in `feature.md` what is accepted as it is, so that the next acceptance does not propose them again (F0019's decision 22).

## 3. A story, from start to merge

**Watch.** Follow the board (`factory-watch` in the container) and the factory's log (`/state/factory.log`): the board shows a story blocked on the human; only the log shows a machine stop or a failed iteration. Watch both.

**When the story asks** (`blocked=question`): read the last comment on its pull request; the comment is posted one tick after the board shows the block. Answer in the pull request, in one comment, with the option and the reason; when the answer is a new decision, also write it into `feature.md` on `main`.

**Never edit a running story's work item on `main`.** The intake and the reviewer rewrite the story on its branch; a human's edit of the same file on `main` conflicts at the next stage start, and the stage stalls twice and reaches the attempts cap (F0019-S0004). Say in the pull request what the story should say; the intake or the reviewer amends it. If the text must change by hand, merge `main` into the story's branch, edit there and push.

**At a cap.**
- *Round cap* (sent back more than `round_cap` times): read the reviewer's open findings. Quality points in the story's own tests: one more round for exactly those, or let it go forward with the findings recorded. Findings on criteria, architecture or security: a decision; usually one more round with the fix named.
- *Attempts cap or crash cap* (runs that ended without a result): find the cause first, in the log and the journal, before writing "retry". A retry against an unchanged cause only spends another run (F0019-A0001 crashed twice on one leftover folder).

**At approval** (`stage=approval`, the pull request no longer a draft; the description is written before the push, so wait for the draft flag to clear):
1. The diff's file list (`git diff --stat main...<branch> -- . ':!factory'`): only files the story names.
2. The reviewer's last entry: no findings, or only ones the human accepted.
3. The smoke tester's entry: every `Expect:` met.
4. Every earlier test that changed names its leave: the standing leave to move a shared helper, or a numbered decision of the feature. A change without one is not merged.
5. Nothing outside the roles' write paths changed (`Makefile`, `pyproject.toml`, `factory/` other than the work item, `CLAUDE.md`, `.secrets.baseline`).
6. The cost table: nothing far above the stories before it without a reason in the journal.

Then merge (`gh pr merge <n> --merge`) **(could be code)**.

**After the merge,** wait for the factory's archive commit (`work item <id>: merged, archived`) before any push to `main`; a push in between races the factory's own. Then start the next story.

## 4. The instance

- **The heartbeat**, every 10 to 30 minutes while a run is on:
  - Docker answers (`timeout 15 docker info`); if it hangs, restart Docker Desktop, then start only the instances that should run.
  - The disk has room (below 5 GB free, stop the instance between two stages).
  - The log has no new `stop` or `iteration failed` line.
  - No stage runs far over its usual time.
  - The plan's usage limit is not passed.
- **Usage.** Read the subscription's 5-hour and weekly windows before every start. Start a story only below the limit the human set; above it, let the story in flight finish, start nothing, and ask. A full window that resets unused is lost: when it is about to reset, use it.
- **Rebuilds.** The running image is what the agents run under. A feature that changes the runtime, the guard or the image says in `feature.md` when the instance may be rebuilt and when not (F0019: never between the story that starts the wrapper and the `tool_paths` that make it usable). After a rebuild, watch the first ticks: the preflight runs, the board moves.
- **A hand probe before a risky change goes live.** When a feature changes how every agent run starts, run one real call through the runtime by hand in a throwaway container of the new image, as the stage would make it, before the instance restarts on it (F0019's change 6 found a refused folder that way).
- **Where helpers may write.** Every prompt to a drafting, pre-check or fix agent names the exact folder for its temporary files (on Windows under `%TEMP%`, a short name because of the 260-character path limit), and forbids a drive's root and the repository. An unnamed "short temporary folder" led two agents to make `C:/t20` and `C:/t21` (2026-10-18).
- **Leftovers.** Throwaway containers, clones and copies are removed when their job ends. A leftover the factory cannot remove (a folder owned by the agent user) is removed by the human as root, then its cause is fixed (F0019: `make mutants` now removes nested repositories when it exits).
- **Secrets.** Tokens and keys are placed and removed by the human only. Nobody prints, copies or reads them. A run that needs a key gets it through a file or an `--env-file`; a log or a journal never holds it.

## 5. Incidents seen, and what fixed them

| Seen | Cause | Done |
|---|---|---|
| A stage stalled twice: "merging the main branch conflicts" | the human edited the running work item on `main` while the intake had changed it on the branch | merged `main` into the branch by hand; rule: answer in the pull request, never edit a running work item on `main` |
| The factory stopped: `repository_unavailable` | `make mutants` left `mutants/seed/.git`, owned by the agent user, which the factory user could not remove | removed as root; the `Makefile` now removes nested repositories under `mutants/` on exit |
| An agent's write refused under the guard | a tool's state folder not in `tool_paths` (the demo's nested `.ruff_cache`) | added to `tool_paths` after a hand probe |
| A test failed only under the factory's umask | files made with mode 002 failed a seal test | `make test` runs under umask 022 |
| A heartbeat prompt kept naming v1's helpers after the handover | the scheduled text was not updated | follow the current routine; update the scheduled text |
| A paid drafting agent cost more than planned and wrote nothing in 20 minutes | it re-read a growing context on every call | stopped it; drafted again on the subscription; check a paid run's spend after 10 minutes |

## 6. Telling the human

- Choices for the human go into the log marked **For the morning**, each with a recommendation.
- Open questions are put as a prepared multiple-choice set: independent questions first, each with its options, their pros and cons, and a recommendation, asked in one sitting.
- A status message gives the state in a line, then what changed, what is next, and what the human must do, if anything.

## 7. What could become the factory's own work

| Rule above | As code | Planned |
|---|---|---|
| Count the human's interventions and the hours the factory waited | journal records with their cause; the cost table and the acceptance report count them | F0021 |
| Machine stops seen only in the instance's log | a stop record on GitHub | F0021 |
| One more round for test-quality findings at the round cap | the reviewer's instructions (from round 2, such findings go forward as notes) | F0021 |
| A criterion that only pins built behaviour needs the human's yes | a standing leave for the reviewer | F0021 |
| The approval checklist | an optional auto-merge on the checks the engine knows (stage decisions, `make check`, the diff's paths) | later, when F0021's counts show routine approvals |
| Waiting out a provider's spend limit and resuming | an end reason, a wait and a resume outside the caps | F0020 |
| The heartbeat | partly the factory's own (disk, stops); Docker's health and the usage windows stay outside it | not planned |
