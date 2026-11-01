# The morning answer for F0047-S0006 (#488), prepared by Claude Code on 2026-11-01

Two steps for the human. Both are needed before the comment, because the comment ends the wait.

1. On GitHub, open `work-item/F0047-S0006`, the work item `factory/features/F0047-the-factory-runs-in-a-cloud-run-job/in-progress/F0047-S0006-one-script-turns-a-bare-job-into-a-running-instance.md`, and change the start of the journal line that begins `Secrets: \`make secrets\` is green` to `About the checksum: \`make secrets\` is green` (edit in the browser, commit on that branch). That is the only line `make secrets` flags; the script itself is clean.

2. Then post this comment on pull request 488:

---

Answer to question 25: (a). I reworded the journal line on the branch ("About the checksum: ..."). Future entries do not begin a line with a word the secrets scan reads as a key.

One more change in this round, from your own note: `vm/job-start.sh` sets `FACTORY_CLAUDE_VERSION` and `FACTORY_OPENCODE_VERSION` where the job gives none, from the `ARG CLAUDE_CODE_VERSION=` and `ARG OPENCODE_VERSION=` lines of the code checkout's `vm/Dockerfile`, read the way `vm/setup.sh` reads them; without them the preflight's `agent-runtime-version` item fails in every job. `FACTORY_OPENCODE_MODELS` stays the job's (a company provider names its own models). The tester adds a row to criterion 10: the two versions present in `factory-run`'s environment with the Dockerfile's values when the job gave none, and the job's values when it gave them; the stand-in checkout's `vm/Dockerfile` gets the two `ARG` lines for it.
