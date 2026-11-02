# An operator sets up from one site file

## Goal

Running the factory in a Cloud Run job, and driving it as the human in the loop, works since F0047, but the session of 2026-11-02 that built F0001 on the todo demo needed about thirty values (the project, the region, the connector, the proxy, three secret names, the model API's addresses, the repositories) and about two hundred lines of shell that held them: a job creation script, a GitHub helper, a log reader, a sanitiser and a runbook. All of it sat in a folder outside the repository, because the values are the company's, and the whole is lost with the machine. The skill's scripts also call `gh`, whose login did not see the project's repository at work. This feature moves everything that is not a value into the repository and leaves one file outside it: `site.env`, a plain list of `SITE_` values that no code ever executes. A new session on a new machine copies `site.env.example`, fills in the values, runs `site check`, and is ready: `job.sh create` and `job.sh execute` start the factory in a job, the skill's scripts drive it through a token command the site names (a secret store, `gh`, anything that prints a token), and the logs of a run are read and sanitised by a command, not by an incantation. It also fixes the two defects of the job profile that the session found (the `PATH` and the token's folder, S0002) so that no workaround stands in the job's configuration, and ends a job whose machine stop cannot be fixed (S0010). Done when every story below is merged and `make check` is green.

## Scope

- The site file: its format, its place, one loader, an example and the command `site` (`show`, `get`, `init`, `check`) (S0001, S0009).
- `vm/job-start.sh`: its own `PATH`, a private copy of the hosting token, the four proxy spellings (S0002).
- A hosting client in shell with a token source named by the site: `hosting_token`, `hosting_api`, `hosting_git`, the token never in an argument list (S0003).
- The skill's scripts (`status.sh`, `wait.sh`, `approval.sh`, `settings.sh`, `start-story.sh`, `next-story.sh`) use that client instead of `gh`, and read the repository and the checkout from the site (S0004).
- `operator/job/job.sh`: `create`, `update`, `execute`, `delete` for the factory's job, from the site's values alone (S0005).
- A sanitiser with the site's own rules and a leak check (S0006).
- `job.sh log` and `job.sh status`: the run's log and its state, sanitised (S0007).
- `merge.sh` and `reset-to-tag.sh` for the person or agent who drives a run (S0008).
- `site check`, the one command that says whether a machine is ready, and the operator guide's chapter on setting a machine up (S0009).
- In a job, a machine stop that stands for ten minutes ends the factory's process with status 1 (S0010).

## Out of scope

- Making the job's own surroundings: the project, the secrets, the connector, the service account, the network, the bot user of the code host. They are the platform's and the operator's; `site check` only says whether they can be seen.
- The judgment of the operator skill (answering, approving), its switches and its references: unchanged.
- Moving the skill to a repository of its own, and any other operating system than Linux and macOS with a POSIX shell and `python3`.
- The factory's own code under `src/factory/`: nothing here changes it, except S0010's rule for a machine stop in a job.
- Any company value in this repository, a test or a document: the example file, the tests and the documents use made-up names (`example.invalid`, `owner/repo`).

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: A site file holds an operator's own values and one loader reads it
- S0002: The job script sets its own PATH, keeps the token in a private folder and exports all four proxy spellings
- S0003: A hosting client in shell takes its token from a command the site names
- S0004: The skill's scripts use the hosting client and the site instead of gh
- S0005: One script creates, updates, runs and deletes the factory's job from the site's values
- S0006: A sanitiser with the site's own rules and a leak check
- S0007: The job's log and state are read and sanitised by one command
- S0008: Merging an approved story and resetting a trial repository to a tag are commands
- S0009: One command says whether a machine is ready, and the guide says how to get there
- S0010: In a job a machine stop that stands for ten minutes ends the factory's process

## The human's changes

One, before S0001: in `factory/pipeline.yml` the coder's write paths gain `"operator/*"`, so that the line reads `coder: {write_paths: ["src/*", "template/*", "claude/*", "vm/*", "operator/*"], time_limit: 40, lease_duration: 60}`. Everything else lies inside the write paths: the coder writes `operator/*` and `vm/*` (S0002), the tester `tests/*`, the documenter `README.md` and `docs/*`. `operator/README.md` belongs to the coder with the rest of `operator/`. No story touches `Makefile`, `pyproject.toml`, `security/`, `CLAUDE.md` or `.secrets.baseline`; if the scripts' tests need a stand-in helper module, it lies under `tests/`.

## Decisions taken for the human

1. **The site file is data, never code.** It is read by a loader that stores every value literally: no `source`, no expansion, no command substitution. Reason: it holds the operator's names, and a file the operator edits by hand must not run anything (S0001). The one value that is a command, `SITE_TOKEN_CMD`, is run by the hosting client alone, with `sh -c`, and only on request (S0003).
2. **The site file lies outside every repository.** The loader refuses a file inside a git work tree. Reason: the whole point is that no company value reaches a repository; the check makes the mistake loud (S0001).
3. **Every key is `SITE_<NAME>`, and the environment wins over the file.** A name that is not a `SITE_` key is refused with its line number, so a typo or a pasted secret does not pass silently. An exported `SITE_X` keeps its value over the file's, which is how a test or a one-off run overrides one value (S0001).
4. **The token is never in an argument list.** `ps` shows the arguments of every process on a machine; the client passes its authorization to `curl` through the configuration on standard input and to `git` through `GIT_CONFIG_*` variables of the environment, and tests look at the stand-ins' arguments for it (S0003).
5. **The token source is a command, with `gh` as the fallback.** `SITE_TOKEN_CMD` can be `gcloud secrets versions access ...`, a keychain call or a script; unset, the client asks `gh auth token`, which keeps the home setup as it is. A command that fails or prints nothing stops with a message that never includes its output (S0003).
6. **The job's wrapper only writes the provider file and hands over to `vm/job-start.sh`.** The two workarounds of 2026-11-02 (the `PATH`, the private token folder) go into the script itself (S0002), so the job's arguments carry no logic and the guide's recipe is true as written (S0005).
7. **`job.sh` never guesses a project, a region or a job's name, and never runs two executions of one job at once.** `create` refuses a job that exists, `execute` refuses while an execution runs; a platform that cannot cancel an execution makes an overlap expensive (S0005).
8. **A reset to a tag needs three things:** `--yes`, a repository the site names as resettable (`SITE_RESET_REPOSITORY`) that equals the repository the commands work on, and a tag that exists. Reason: a force-push to `main` is the one act of these scripts that cannot be undone, and the factory's own repository must never be its target (S0008).
9. **The sanitiser's rules are the site's.** The repository holds the mechanism and the leak check; the patterns (a company's domain, a project id) are values and live in the site's folder. Reason: the sanitiser's own rules would otherwise be the leak (S0006).
10. **A story's test of a script uses stand-ins on the `PATH`, as `tests/vm_support.py` does for `vm/job-start.sh`.** No test calls `gcloud`, `gh`, `curl` or a real `git` remote; the code host is a stand-in `curl` and a local bare repository (this feature's decision; `CLAUDE.md` *Tests*).
11. **The machine's own values live in `~/.config/kumpel/`.** The site file, its sanitiser rules and the skill's `settings.json` share one folder, and the state file of `job.sh` lies in `~/.local/state/kumpel/`. Reason: Kumpel is the product, and one folder holds what one machine knows (the human, 2026-11-02; S0001, S0005).
12. **The job runs the start script of the code it clones.** `job.sh` takes `vm/job-start.sh` from `SITE_CODE_REF` with `git show`, not from the working tree, so the script and the code it installs are of one commit (the master's review, 2026-11-02; S0005).
13. **In a job a machine stop that stands for ten minutes ends the process with status 1.** A job's machine cannot be fixed in place, and a stop that holds it costs its CPUs until the task timeout and shows the execution as running; ending it shows the failure where the operator looks. A VM keeps waiting for the fix. Ten minutes, fixed, leave room for a preflight item that passes on a later tick (the human, 2026-11-02; S0010).
14. **Tests of the scripts use the real `git`** (`CLAUDE.md` *Tests*); what `hosting_git` gives git is read back through `git config` and git's own trace, not through a stand-in (the master's review, 2026-11-02; S0003, S0004).
