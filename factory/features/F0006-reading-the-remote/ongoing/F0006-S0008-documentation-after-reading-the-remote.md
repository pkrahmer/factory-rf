---
stage: docs
pr: 80
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Documentation after reading the remote

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance of F0006 read `README.md` and `docs/` from the top. The F0006 sections of the project guide match the code. Each story documented its own part, though, and seven things fell between them or went stale:

- **The summaries of what is built stop before F0006.** `README.md` still says "nothing starts a stage before F0006". The operator guide's opening paragraph names neither the evaluation, the tick, the dispatcher nor the run handler, and says "there is nothing else to start". Both should say what is true now: a tick can run a stage, but no command runs ticks before F0010. Neither warns that the declared console scripts `factory-run` and `factory-health` end with `ModuleNotFoundError` until then.
- **The way out of an unreadable work item file is wrong.** The operator guide, under "The stops of the tick", says the tick fails "until a human repairs the file … or closes the pull request". `RemoteWorkItems.read` reads every story in `in-progress/` on `origin/main` before any pull request is looked at, so closing the pull request changes nothing. The ways out are to repair the file or to move the story out of `in-progress/` on `main`.
- **A `reject` is not "only recorded".** "A stage changed by hand" says so, but the event has no handler before F0007-S0006. It is a counted error, reported once on the pull request after three ticks and then capped, and a capped event holds back all new work.
- **The kinds without a handler are not explained.** "An event that keeps failing" says that a kind without a handler counts. It does not say which kinds those are today (`NOT_YET_HANDLED` in `factory.entry.wiring`) or what follows. The first work item that reaches an approval stage gives `hand_over`, a merge gives `merged`, a question waiting to be posted gives `ask` and the human's answer to it `comment`, and an own claim left on the remote gives `crash`. Each becomes one error report and then holds back all new work, until F0007 and F0008 register their handlers.
- **`StopService.post` is called now.** "Stops of one work item" says it is something "which nothing built calls yet". The dispatcher's error report calls it, and opens a draft pull request when the work item has none. The same section says that the factory records the number of a pull request it opened; the dispatcher does not (F0006 decision 9), and a later stop finds the draft by its branch.
- **The attempts cap.** "A stall: the stall note" and "A stall by a red check" say the evaluation "arrives with F0006". It has arrived. At the cap it makes `ask` with the detail `attempts cap`, which is a counted error until F0007's handler.
- **A branch made by hand.** "A stage changed by hand" exempts the opening commit, but it does not say the consequence: the stage a work item branch created by hand starts with is never judged, whatever it is; later stage changes on that branch are judged. Its first commit is the opening commit, and a later commit above main's text without front matter has a previous version that cannot be read. The feature acceptance listed this for the human (section 6, item A). This story documents today's behaviour; a later change of the rule documents its own.

This story is documentation only: the tester writes no tests and the coder has nothing to build; the documenter writes it from the docs criterion. The human may prefer to make the edit by hand.

## Interface

None: no code changes. Files: `README.md`, `docs/operator-guide.md`. `docs/project-guide.md` and `docs/decisions.md` are read for consistency and changed only where they contradict the new text.

## Acceptance criteria

1. make check stays green.
2. docs: this story is the documentation. `README.md` and `docs/operator-guide.md` change; `docs/project-guide.md` and `docs/decisions.md` change only where they contradict the new text. Afterwards:
   - The summary of what is built, in `README.md` and in the opening paragraph of `docs/operator-guide.md`, names reading the remote, the evaluation, the tick with its stops, the dispatcher with the run handler, and `factory-watch`. It summarises rather than lists, as the human decided on 2026-10-14 (F0003-S0010). It says that no command runs ticks yet and that this arrives with F0010. It no longer says "nothing starts a stage before F0006".
   - `README.md` and the opening paragraph of `docs/operator-guide.md` say that `factory-run` and `factory-health` are declared but not built, and that both end with an error (`ModuleNotFoundError`) until F0010. `README.md` still names the four commands that exist.
   - Under "The stops of the tick", the paragraph on an unreadable work item file names two ways out: repair the file (on its branch, or on `main` for a started story without a branch), or move the story out of `in-progress/` on `main`. It no longer names closing the pull request.
   - "A stage changed by hand" says what happens to a `reject` until F0007-S0006 handles it: a counted error, one report on the pull request after three ticks, then capped, holding back all new work. A push to the work item's branch makes the factory try again, and the `reject` returns as long as the newest commit beyond `origin/main` that touched the story's file is the illegal change. It no longer says the event is only recorded. It also says that the stage a work item branch created by hand starts with is never judged, whatever it is: the first commit that gives the file its front matter is the opening commit or has a previous version that cannot be read. Later stage changes on such a branch are judged like any other.
   - "An event that keeps failing" names the kinds still without a handler, as `NOT_YET_HANDLED` lists them. It says what the common ones lead to today: `hand_over` when a work item reaches an approval stage, `merged` after the human merges a waiting work item's pull request, `ask` while a question (an agent's `question`, the attempts cap) waits to be posted, `comment` when the human answers on the pull request, and `crash` when the instance finds its own claim on the remote (after a rejected result push or another boundary error after the stage-start commit, or after a restart when the process died during a stage). Each ends in the one report of its work item and remote state and then holds back all new work, until F0007 and F0008 register their handlers. It still says that a push to the branch makes the factory try again.
   - "Stops of one work item" no longer says that nothing calls `StopService.post`. It says the dispatcher's error report uses it, and that the dispatcher does not record the number of a pull request it opens in the work item's state; a later stop finds that pull request by its branch.
   - The cap paragraph of "A stall: the stall note" and the cap bullet of "A stall by a red check" say that the evaluation makes `ask` (`attempts cap`) at the cap, and that this is a counted error until F0007 asks the question. They keep what the operator does once F0007 arrives.
   - Every quoted text in the changed sections matches what the code prints today: `error_report_text` in `factory.domain.post_texts`, the `reject` detail in `factory.domain.evaluation`, and `factory-watch: no instance settings are wired yet`.

## Demo

```bash
grep -n "F0006\|factory-run\|factory-health" README.md
```
Expect: no line says "nothing starts a stage before F0006"; at least one line names `factory-run` as not built yet.

```bash
grep -n "closes the pull request\|the event is only recorded\|which nothing built calls yet\|arrives with F0006" docs/operator-guide.md
```
Expect: no printed line names closing the pull request as a way out of an unreadable work item file, and none of the other three phrases is printed.

```bash
grep -n "NOT_YET_HANDLED\|hand_over\|created by hand" docs/operator-guide.md
```
Expect: at least one line names `NOT_YET_HANDLED` or lists the unhandled kinds, one names `hand_over`, and one says that the stage a work item branch created by hand starts with is not judged.

## Log (append only)

1. 2026-10-14 human: created.
2. intake: accepted
   - Interface: "None", no code changes. The files are named (`README.md`, `docs/operator-guide.md`), and `project-guide.md` and `decisions.md` change only where they contradict the new text. There is nothing to specify further. The Interface states no rule or behaviour needing its own criterion.
   - Criteria: criterion 1 is the `make check` gate. Criterion 2 is the docs criterion, split into seven bullets. Each bullet names the sections and the exact claims to add or remove, so the documenter and a reviewer can check it by reading. No code rule is stated, so there is no failing side to cover. The story says the tester writes no tests, and the tester stage should respect that.
   - Demo: the three commands are runnable `grep`s on the two files. Each `Expect:` line is checkable against the output: absent phrases, `factory-run` named as not built, `NOT_YET_HANDLED`, `hand_over` and "created by hand" present.
   - Architecture: no layer or module is touched, so there is no conflict with `CLAUDE.md`. The docs follow the documenter's four-file rule, and the story leaves `docs/decisions.md` alone unless it contradicts the new text.
   - Scope: the story is within F0006's goal. It is the feature acceptance's proposed documentation story, listed in `FEATURE.md`. It documents today's behaviour and does not change the rules (F0007, F0008 and F0010 stay out of scope).
3. tester: no tests written, on purpose. This is a documentation-only story. The Interface is "None: no code changes", and the Assignment says the tester writes no tests. Criterion 1 is the `make check` gate. Criterion 2 is the docs criterion, which the reader checks against `README.md` and `docs/operator-guide.md`. It states no code behaviour a test could check. I did not add tests that grep the docs: the Demo already does that, and such tests would guess at wording the documenter has not written. No files were created or changed. No modules failed to import. I did not run `make test` because no new tests exist. `make lint` is green. For the coder: there is nothing to build, so hand on to the documenter.

   `make lint`: lint: green
   `make test`: test: green
4. coder: nothing built, on purpose. This story only changes documentation. The Interface is "None: no code changes" and the tester wrote no tests, so the coding stage has no work to do. I made no commits and changed no files under `src/` or `tests/`. I skipped the refactor step because there is no diff of my own to review. The documentation changes in criterion 2 (`README.md` and `docs/operator-guide.md`) belong to the documenter stage. Under CLAUDE.md the coder does not write those files, so I did not touch them. `make check` is green on the branch as checked out (coverage 99.35 %).

   `make check`: check: green
5. reviewer: no findings.
      - Scope: `git diff main...HEAD -- . ':!factory'` has no changes under `src/`, `tests/`, `README.md` or `docs/` apart from `docs/runs/`. Every changed file is under `planning/` or `docs/runs/`. They come from the human's commit 5f50f94 ("Night log: F0010 …"), which reached the branch through 802caad ("merge main"). The local `main` ref has not caught up with it yet. These are the human's files, not this ticket's work, so I did not review them.
      - Acceptance criteria: the Interface is "None: no code changes" and states no rule or limit, so no failing side needs a test. The tester wrote no tests and the coder built nothing, both on purpose and as the Assignment says. Criterion 1: the coder's entry records `make check` green (coverage 99.35 %). Criterion 2 is the docs criterion, which the documenter writes next. Its seven bullets name the sections, the phrases to remove and the texts to match (`error_report_text`, the `reject` detail, `factory-watch: no instance settings are wired yet`), so the documenter can write it and a later reader can check it.
      - Architecture, security, quality: no code or configuration changed, and no suppression markers were added.
      - Ticket hygiene: the log gives the main decision (documentation only, no tests, nothing to build) and what was rejected (tests that grep the docs). `Assignment` matches what was built, which is nothing yet. The docs criterion still describes what the reader must know after this story.
