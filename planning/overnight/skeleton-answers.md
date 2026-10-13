# Working answers to the skeleton's open questions

> 2026-10-13 morning, the human's decision, binding on everything below and on every later story: interfaces are abstract base classes and the factory's implementations inherit them (`CLAUDE.md`, Architecture; `interfaces.md`, Amendments). Where an answer below says "protocol", read "abstract base class".

> 2026-10-13, reviewed by the human in questionnaire 1 (`planning/questionnaires/01-working-answers.md`, Answers): every answer below stands except skeleton answer 2 (no run record: drop it), skeleton answer 11 (no v1 recognition at all: v1.1 starts fresh), and F0001 round 1's "F0010's preflight checks that the identity is set" (no preflight item; the default identity stands). The questionnaire's answers win over this file.

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

## Answers during drafting

- **Console scripts (F0004's question 3).** Before the first story starts, the human (the session) adds every console script of the sheet's `factory.entry` table to `pyproject.toml` in one setup commit, each as `<name> = "factory.entry.<module>:main"`: `factory-check-story`, `factory-guard`, `factory-bill`, `factory-watch`, `factory-run`, `factory-health`. Every entry module's entry function is therefore `main() -> int`. F0004-S0004's `run` becomes `main`.

## Answers for F0001's round 1 (00:45)

- **Commit identity.** `GitCli` takes the commit identity (name and email) as a constructor argument, which comes from the instance's settings (`GIT_USER_NAME`, `GIT_USER_EMAIL`, R25). It is not fixed in code. F0010's preflight checks that it is set (kept thing 18).
- **Git credentials.** `GitCli` ignores global and system configuration, and it takes an optional extra environment from the factory process (for example `GIT_ASKPASS` or a credential-helper setting passed with `-c`). That is how the factory's own pushes get the token (WE3.5, R33). The agent run never receives it. S0004 or S0005 states this as a rule with a criterion.
- **`claude -p` flags.** Only flags that v1's book gives (the extraction `v1-04-08.md`, chapter 8 "Starting the agent") are used. A flag not in that chapter is not invented. (Corrected at 01:00: `--permission-prompts none` is in that chapter and stays; the first version of this answer dropped it by mistake.)
- **Budget stop.** The end reason is decided from the result's `subtype` (`error_max_budget_usd`) before the exit status, so that a budget stop always reaches the one resume.
- **Size.** A story above 22 criteria with several mechanisms is split (S0004 and S0008 at least), with consecutive ids, and the later stories are renumbered.

## Answers to cross-check round 1's blockers (00:55)

1. **Production wiring.** `factory.entry.wiring` grows with each feature: `build_boundaries(settings)` and `build_dispatcher(boundaries, definition)`. F0006 creates `build_dispatcher` with the kinds it handles, and registers `StageRunner` as the handler of `run` events. Every later story that adds a handler also registers it there, with a criterion. One test checks that every event kind built so far has a handler, so `factory-run` never meets an unhandled kind of its own making. F0010-S0001 completes `build_boundaries` from `InstanceSettings`.
2. **`crashes` reset on a forward move.** F0005 builds it from the start: a forward move resets `crashes` to 0, beside rounds and attempts, with its criterion. F0008 drops its change to F0005's rules and only tests that the reset holds after a crash.
3. **Git configuration.** `GitCli` keeps ignoring the system and global configuration. It gets the commit identity as a constructor argument (from `GIT_USER_NAME`, `GIT_USER_EMAIL`) and the credential through an extra environment or `-c` settings given by the factory process (F0001's answers above). F0010 passes the token to the factory's own git this way, never through a system `credential.helper`. `core.sharedRepository`, if F0010 needs it for the second OS user, is passed the same way.

## Answers for F0001's round 2 (01:09)

- **Default identity.** `GitCli` without a given identity commits as `factory <factory@noreply.invalid>`, v1's compose default. The instance's settings override it (R25), and F0010's preflight reports an unset identity. So every `GitCli(work)` in a Demo can commit.
- **Constructor size.** `GitCli`'s optional settings go into one frozen Pydantic model `GitOptions(identity: GitIdentity, environment: Mapping[str, str] = {}, kill_points: KillPoints | None = None, ...)` in `factory.domain.git`. The constructor becomes `GitCli(work: Path, options: GitOptions = GitOptions())`, within ruff's five arguments and with no `noqa`.
- **Size.** Up to 26 criteria is allowed (the plan's limit); the answer's 22 was a target, not a rule. No further splits for size alone.
- **S0004's demo.** The child flushes after each write (`flush=True`), so the merged order is fixed.
- **S0007 and nested make.** The make class runs `make --no-print-directory <target>` and removes `MAKELEVEL`, `MAKEFLAGS` and `MFLAGS` from the child's environment, so a run under `make check` gives the same output as a run on its own.
- **S0010, a resumed call that reaches the `time_limit`.** The whole run's cost and tokens are unknown (`None`), its turns too. Its duration is measured by the factory and its end reason is `time_limit`. This follows R24, which allows no partial or estimated figures.
- **S0002's garbled lines.** The rule and criterion 9 are rewritten with the escapes written as text: `"\r"` and `"\r\n"` in backticks, never as real line breaks.
