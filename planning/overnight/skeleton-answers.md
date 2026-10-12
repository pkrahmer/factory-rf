# Working answers to the skeleton's open questions

The main session's answers, taken unattended on 2026-10-12 under the plan's rule: take the plan's default or the simplest reading consistent with the handover and decisions 001 to 007, and list each for the morning. They bind the interface sheet and the drafters. Numbers follow `skeleton.md`'s open questions.

1. **Expiry of another instance's lease** is handled as a crash: the stage reruns from its stage-start commit, no attempt is charged, `crashes` rises by one. It posts a note on the work item's pull request. The note says "retrying" only when the rerun will happen, and never at the crash cap, where it asks the human (ST1.4). A crash of the instance's own stage (same name) posts no note; it adds a journal entry with the rerun's stage-start commit.
2. **Run record and lock.** v1.1 keeps a local run record only as a cache for display (the board's "running since"). It keeps no tick lock: one instance runs one process, and ticks run one after another in the entrypoint loop. GH1.5 tests that deleting the run record changes nothing the next tick does.
3. **Dirty main branch.** At the start of every tick the factory restores its checkout to the remote-tracking refs and discards uncommitted changes (R18: machine state is disposable), and writes one time-stamped line saying what it discarded. ST3.3's "dirty main branch" stop is the case where that restore fails. The health check then fails and the line names the failure.
4. **Keyed posts.** Every post the factory makes carries a hidden key derived from state: `<!-- factory key=<work item id>:<kind>:<n> -->`, after the marker. Before posting, the hosting client lists the pull request's comments and does not post when a comment with the same key exists. The state write may then come before or after the post. GH3.4 and ST1.1 rest on the key. Reading comments is the human's channel, not state read back as truth (R22).
5. **Exact names in v1.1's files** are fixed by the interface sheet, in the glossary's words: lifecycle folders, branch prefixes, story headings, journal prefix (decision 007, question 2), state keys and pipeline definition keys.
6. **Lease clock:** decision 007, question 4.
7. **Write paths for `image/`, `template/` and `claude/`.** In `factory-rf`, the coder writes them (already in the seed's `factory/stages.yml`). The agent, skill and settings files v1.1 ships are written by F0010's stories in the glossary's names, not copied by the seed.
8. **Order of the stage-start commit.** It is the last commit before the agent run, after every preparation step (opening the branch, merging the main branch). It is the undo's and restore's baseline. For the first stage, the commit that opens the branch is that stage's stage-start commit.
9. **WE6.3** is checked by the cross-feature check over the stories (every story's last criterion names the documents it touches) and traced as an observation. It is not a code test. F0011-S0004 drops it, unless it holds other conditions.
10. **PyGithub client tests** use stand-ins of PyGithub's objects, with no network. A real API call is a morning observation, and the baseline run proves it.
11. **R26 detection.** A v1 work item is a file in a v1 lifecycle folder `ongoing/` under the features root, or a work item whose front matter carries a v1-only state key (`comments_seen`). Either one triggers the refusal stop that names it.
12. **Per-condition dependencies:** confirmed. The dependency table holds per condition: a feature may come before part of an item it depends on when it does not use that part.
13. **Size of F0001:** keep eight stories. Each story is small, and the build starts story by story; the feature need not finish first tonight before its stories are useful.
14. **Tick status across a restart.** The tick status is a local cache and may reset on a restart. The error-cap report is keyed (answer 4), so a restart cannot post it twice. A restart may reset the retry count of an error, which the morning report notes.
15. **Hand-over state.** The work item's front matter gets one more state field, `handed_over`: the stage whose hand-over completed. The watcher raises a hand-over event while `stage` differs from `handed_over`, and the hand-over writes the field when it completes.
16. **Docker, root and a second OS user inside v1's container:** checked on the PC at 23:46. The container runs as uid 1000 `factory` with no `sudo`, no `docker` command and no Docker socket (`useradd` exists but needs root). ST3.3, WE3.1, WE3.3 and WE3.4 stay a static test plus a morning observation.

## Answers to the interface sheet's open questions

Taken by the main session on 2026-10-13 at 00:05; they bind the drafters. Numbers follow `interfaces.md`'s open questions.

1. Acceptance ids stay `F000N-A000M`, ordered by `work_item_order` (a stated rule).
2. The spellings chosen in the sheet stand: the glossary's word where it renames v1's, the sheet's choice elsewhere. For the morning.
3. Default `time_limit`s stay at 40 minutes for an agent run and 10 minutes for a project command. ST8.5 refuses a definition where they do not fit, and a project may set them.
4. The five values of `blocked` stay.
5. Only the human's journal entries carry a date, as in v1.
6. `Claim.lease_duration` is accepted.
7. The write-path placeholders `{work_item}` and `{feature}` are accepted.
8. The pipeline definition has a reader and no writer: no story writes it. For the morning, since R13 says "one reader and writer class".
9. `AgentDefinition` keys as in the sheet; F0010 may change them with its finding.
10. `ERROR_CAP` stays the constant 3. For the morning.
11. Four kill points, as in the sheet.
12. `HostingService.close` stays, because R10 is exact.
13. `Boundaries` as a frozen dataclass is accepted: it holds interfaces, not data.
14. F0006's drafter checks the event kinds against `v1-04-08.md`, chapter 7.
