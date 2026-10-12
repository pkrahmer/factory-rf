# Boundaries

## Goal

Every outside party is reached through one boundary: the git command-line tool through one wrapper class, the hosting service through an interface with a PyGithub implementation and one fake, the project commands through an interface with a make-based class, and the agent runtime through an interface with a `claude -p` implementation and a fake. Their inputs and outputs are Pydantic DTOs shaped by what the factory needs, not by the tool, and named kill points in the wrappers let later tests inject a crash. The feature is useful on its own: everything that comes after it calls only these interfaces. Done when each of the four boundaries has its first implementation and is callable through its interface, a fake exists for the hosting service and for the agent runtime, the git wrapper is tested against a real local bare remote, each kill point can be armed and is reached by its wrapper, and a search finds no call to an outside tool (git, the hosting service, make, claude) outside the wrappers.

## Scope

- Named kill points: an injection seam, inert unless a test arms it, and the root of the factory's error hierarchy (R36).
- The hosting-service interface (R10) with its DTOs, the marker and the post key; the PyGithub implementation with its one error type (SI2.1, SI2.2); the one fake (SI2.3).
- The git wrapper with DTOs (R9): one place that starts a subprocess, fetch with prune, remote-tracking branches, resolving refs, a file at a commit, files under a directory, ancestry, log, changed paths, status, clone, check out, commit, push with its outcome, delete branches, merge with abort on a conflict, reset and clean, revert paths, move.
- The project-commands interface and the make class (R11), with a generic check result that has no layer names (R8).
- The agent-runtime interface, its DTOs and the fake; the `claude -p` implementation with the budget resume, the `time_limit` and the version query (R12).
- Searches in the tests that prove the boundaries: only one module imports `github`, only one starts a subprocess, only one names `make`, no `dict[str, Any]` crosses a function boundary (R5, R7).

## Out of scope

- The write-path guard hook command and what it refuses: F0004. The guard settings file is only written here.
- Reading agent files from disk and composing the prompt: F0005; the keys an agent file may hold: F0010.
- Scrubbing the agent's environment and running as a second OS user: F0010. The runtime here uses exactly the environment a request gives it.
- When to post, what to post, and idempotent posting as a rule of the handlers: F0003 and F0007. The interface only offers the key.
- Wiring that builds the PyGithub `Repository` from the token and picks the concrete adapters: F0002 onward (`factory.entry.wiring`), F0010 for the token.
- The kill-point tests themselves: F0011 (F0008 uses the seam too).

## Stories

- S0001 — Kill points in the wrappers
- S0002 — The hosting-service interface and its DTOs
- S0003 — The PyGithub hosting client and its one error type
- S0004 — The git wrapper: process, fetch and refs
- S0005 — The git wrapper: clone, checkout, commit and push
- S0006 — The project-commands interface and the make class
- S0007 — The agent-runtime interface, its DTOs and the fake
- S0008 — The claude agent runtime
- S0009 — The git wrapper: history and work tree
- S0010 — The git wrapper: branches, merge, reset and revert
- S0011 — The hosting-service fake

## Decisions taken for the human

Product and design decisions taken while writing the stories, for the human to review in one place. Each names where it was taken.

1. A kill point fires once and is then disarmed; `after` counts the reaches from the arming, not from the start; the reach that fires is counted by `reached`; arming an armed point replaces the earlier arming. (S0001, story text)
2. `InjectedKill` is a `BaseException` and not a `FactoryError`, so that no `except Exception` in a handler survives it, as no handler survives a real death. (S0001, story text)
3. The interface sheet gives three modules to later stories that the hosting DTOs already need, and F0001 is built before F0002: S0002 creates the first part of `factory.domain.identifiers` (only `WorkItemId`), `factory.domain.git` (only `CommitId`) and `factory.domain.paths` (only `MAIN_BRANCH` and `LABEL_PREFIX`). S0004 adds `REMOTE` and `RemoteBranch`; S0007 adds `Name`. F0002-S0001 adds the rest of `identifiers` and `paths` and must not create them again. (S0002, story text)
4. A post's key is read only from the last non-blank line of a comment, and a comment counts as the factory's only when it carries the marker (the author is never consulted). A human who quotes a key line neither suppresses a post nor is taken for the factory. `render_post` removes the trailing whitespace of the text before the marker and key lines. (S0002, story text)
5. The PyGithub client gives a merge commit only for a merged pull request, although GitHub reports a test-merge commit for an open one. Only `github.GithubException` and `OSError` (which covers connection errors) become `HostingServiceError`; any other exception passes through as the factory's own bug. `set_labels` reads the pull request's label names to keep those that do not start with `stage:`; this read is internal and never returned. (S0003, story text)
6. The fake hosting service numbers pull requests and comments from 1, uses the url `https://fake.invalid/pull/<n>`, gives its comments the date 2026-10-12 in UTC plus one second per id, posts as the author `factory` and adds human comments as `human` by default. Where GitHub would refuse, the fake does not unless a criterion says so (for example it allows a second open pull request for one branch). (S0011, story text)
7. Every git call ignores the user's and the system's configuration (`GIT_CONFIG_NOSYSTEM`, `GIT_CONFIG_GLOBAL` at the null device), has a `time_limit` of 5 minutes by default, and reports its whole output in the error; every failure of `fetch` is a `FetchFailed`. (S0004, story text)
8. `show_file` of a directory is `None`, of an unknown ref a `GitError`; `list_files` of a missing directory is `[]`; `run_process` kills the whole process group at the `time_limit`. (S0004, story text)
9. Needs the human before the build: the one `subprocess.Popen` call in `src/factory/adapters/process.py` triggers ruff `S404` and `S603` and bandit `B404` and `B603`, and `pyproject.toml` is outside every write path. The story therefore carries exactly four suppression markers there (`noqa: S404`, `nosec B404`, `noqa: S603`, `nosec B603`) and a test that allows no others. CLAUDE.md lists a `nosec` marker under "Not without asking", and the reviewer treats a marker CLAUDE.md does not allow as a finding, so the human adds one line to CLAUDE.md allowing exactly these four in that file before S0004 starts. The alternative is to let S0004 stop with a question. (S0004, story text)
10. Every commit the factory makes has the author and committer `factory <factory@noreply.invalid>` (v1's default address); a push is never forced, and a rejected or unreachable push is a returned value, not an error; `commit` stages everything that is not ignored, untracked files included. (S0005, story text)
11. `CheckResult.last_line` skips make's own lines (those starting `make:` or `make[`), as v1 does when it writes a check's line into the journal; this refines the interface sheet's "last non-blank line". The output tail is the last 30 lines; a missing target is a failed command, not an error; a `time_limit` of zero or less is a `ValueError`. (S0006, story text)
12. A dead, timed-out or over-budget agent run is a result with an end reason, never an exception; `AgentRuntimeError` is only for a run that cannot be started. (S0007, story text)
13. In the `claude -p` runtime: the resume message reads "Finish now: give your decision (question if the work is not done) and your entry." (v1's `stuck` is gone, `question` replaces it); the resume budget is a quarter of the budget, at least 0.50, rounded to cents, and the resume is made once; one `time_limit` counts across both calls; a decision outside `allowed_decisions` makes the end reason `no_result`; `--tools` is always passed (an empty list gives an empty value, which turns the tools off); cost, turns and tokens are taken from the call's JSON in every case except a call ended by the `time_limit`; the factory measures the duration itself; a permission denial's detail is the sorted JSON of the tool input; the files under the state directory are removed when the run ends. (S0008, story text)
14. `changed_paths` is the net difference between the commit and the work tree (a path added and deleted again, or changed and restored, is not listed; a rename is a deletion plus an addition; untracked files count, ignored ones do not); `status` marks any deleted path as deleted, any untracked or newly staged path as added, and everything else as modified. (S0009, story text)
15. `delete_branch` of a branch that does not exist is not an error, and `delete_remote_branch` of a branch already gone from the remote returns `pushed` (as v1: a branch already gone is fine); a merge of diverged branches uses git's default message; a merge that conflicts is aborted before it returns; `reset_to` keeps ignored files (handover section 8); `revert_paths` refuses an absolute path or a `..` segment with `ValueError`. (S0010, story text)
16. The skeleton proposed eight stories; the feature has eleven. S0009 and S0010 split the git wrapper, and S0011 splits the fake from the hosting interface, so that every story stays within 26 criteria. S0001 to S0008 keep the meaning that the interface sheet gives them, except that `log`, `changed_paths` and `status` are built by S0009 and the rest of the git writing operations by S0010. The test fixtures `remote`, `checkout` (S0004) and `human` (S0005) are built where the first tests need them. (feature, story text)
