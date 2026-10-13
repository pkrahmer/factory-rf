# Project guide

The guide for agents working on `factory-rf`: how the code is laid out, where a change belongs, which conventions the checks do not catch, and what to read first. It grows with each story: the documenter stage fills it in from the stories' docs criteria. `CLAUDE.md` holds the rules every change follows.

## Errors

`factory.domain.errors.FactoryError` is the root of every error the factory raises on purpose. Later stories add their error types under it. `InjectedKill` (below) is deliberately not one.

`BoundaryError` (a `FactoryError`) is the root of the errors for an outside party that failed. `HostingServiceError(operation, detail)` is its first subtype: every implementation of the hosting-service interface raises it for every failing call, and its message is `hosting service <operation> failed: <detail>`. `operation` and `detail` are attributes.

`GitError(command, exit_status, output_tail)` is its second subtype, for the git wrapper. `command` is `git ` and the arguments (`git fetch --prune origin`); `exit_status` is `None` when git could not be started or hit its time limit; `output_tail` is the last 30 lines of the output, stdout and stderr merged (all of it when shorter). The message is `<command> failed (exit <status>): <tail>`, or `failed (no exit status)` when the status is `None`. `FetchFailed` is a `GitError` that `fetch` raises for every failure.

`ProjectCommandError(command, detail)` is its third subtype, for the project commands: it is raised only when a command cannot be started (an invalid name, or an executable the operating system cannot start). The message is `project command <command> failed: <detail>`; `command` and `detail` are attributes. A red command is a result, not this error.

`AgentRuntimeError(detail)` is its fourth subtype, for the agent runtime. The message is `agent runtime failed: <detail>`; `detail` is an attribute. A run that dies, hits its `time_limit` or runs out of budget is a result, not this error (see *The agent runtime*).

## The hosting service

The factory reaches the hosting service (pull requests and their comments) only through the `HostingService` interface (an abstract base class) in `factory.application.hosting`. Nothing else may call it, and the application layer knows no concrete client. `PyGithubHostingService` (`factory.adapters.pygithub_hosting`) is the one client; `FakeHostingService` (`factory.adapters.fake_hosting`) is the one fake. Build comments from the service's data with `PullRequestComment.from_body`, so that `by_factory` and `key` always agree with the body.

The ten operations:

| Operation | Returns | Purpose |
|---|---|---|
| `create_pull_request(branch, title, body, *, draft)` | `PullRequestView` | open a pull request, as draft or ready |
| `find_open_pull_request(branch)` | `PullRequestView \| None` | the open pull request of a branch |
| `get_pull_request(number)` | `PullRequestView` | read state, draft flag and merge state |
| `list_comments(number)` | `list[PullRequestComment]` | comments with id and author |
| `post_comment(number, text, key)` | `PostOutcome` | post with the marker; `"already_posted"` if the key is already there |
| `close(number)`, `reopen(number)` | `None` | change the state |
| `set_draft(number, draft)` | `None` | mark draft or ready |
| `set_description(number, body)` | `None` | replace the description (the one projection of the work item) |
| `set_labels(number, labels)` | `None` | write the labels |

Labels are a projection of the stage: they are written and never read back, so no operation returns them and `PullRequestView` has no label field. `LABEL_PREFIX` (`"stage:"`) in `factory.domain.paths` is the prefix of those labels, and `MAIN_BRANCH` is `"main"`.

### The PyGithub client

`PyGithubHostingService(repository, kill_points=None)` implements the ten operations on a PyGithub `Repository`. It inherits `HostingService`, an abstract base class. The constructor reads nothing from the repository. Wiring that builds the `Repository` from the token comes with `factory.entry.wiring` (F0002 onward, token in F0010).

- Every failing call raises `HostingServiceError(operation, detail)`: a `github.GithubException` or an `OSError` (a connection error is one) inside any of the ten operations is re-raised with the operation's name and `str(error)` as detail, chained to the original. Any other exception, and `InjectedKill`, passes through unchanged.
- `post_comment` lists the comments first and returns `"already_posted"` without posting when one has the same key; otherwise it posts `render_post(text, key)`, reaches `KillPoint.AFTER_POST` and returns `"posted"`.
- `find_open_pull_request` asks for open pull requests with head `<owner login>:<branch>`. A view's `state` is `merged` when PyGithub says merged, else `open` or `closed`; `merge_commit` is set only for a merged pull request, even though GitHub reports a test-merge commit for an open one.
- `list_comments` sorts by id, oldest first, and reads a naive `created_at` as UTC.
- `set_labels` keeps the labels that do not start with `LABEL_PREFIX` and adds the given ones; the names it read are never returned.
- `github` is imported by this module only. No module in `src/factory` imports another route to the hosting service (`requests`, `httpx`, `aiohttp`, `urllib3`, `urllib.request`, `http.client`, `socket`, `git`, `pygit2`, `dulwich`, `githubkit`) or contains the string `"gh"`; `tests/test_hosting_search.py` checks it.

Tests do not call PyGithub. `tests/adapters/test_pygithub_hosting.py` uses the recording stand-ins of PyGithub's objects in `tests/adapters/pygithub_stand_ins.py`, passed in with `typing.cast`. A real call is first seen by the baseline run. Use a low-entropy literal such as `"a" * 40` for a commit id in a test, so that `make secrets` stays green.

### The fake

Tests use `FakeHostingService(kill_points=None)` (`factory.adapters.fake_hosting`), through the `hosting` fixture in `tests/conftest.py` (built with the test's `kill_points`), and nothing else in place of the hosting service. It inherits `HostingService`, an abstract base class, so Python refuses a fake that leaves an operation out. `tests/test_hosting_fake_search.py` checks that only the fake and the PyGithub client define `post_comment`, and that no test class does.

It behaves as the PyGithub client does where a test can see it: a repeated post key returns `"already_posted"` and adds nothing, `merge_commit` is set only for a merged pull request, `set_labels` replaces only the labels that start with `LABEL_PREFIX` (others keep their order, the given ones come after), and every failing call raises `HostingServiceError`. `post_comment` reaches `KillPoint.AFTER_POST` after a `"posted"`, and not for `"already_posted"`.

Numbering is predictable: pull requests from 1, comment ids from 1 across all pull requests, the url of pull request `n` is `https://fake.invalid/pull/<n>`, and the `created_at` of comment `i` is 2026-10-12 UTC plus `i` seconds. A number that does not exist raises `HostingServiceError` from every operation that takes one.

The test operations act as the human or look at what the factory did:

| Operation | Purpose |
|---|---|
| `add_human_comment(number, body, *, author="human")` | add a comment as written; returns its id |
| `delete_comment(number, comment_id)` | remove a comment; an unknown id raises `HostingServiceError`; the id of a comment on another pull request counts as unknown, and that comment is left alone |
| `close_by_human(number)` | state `"closed"` |
| `merge_by_human(number, merge_commit)` | state `"merged"` with that `merge_commit` |
| `fail_next(operation, *, times=1)` | the next `times` calls of one of the ten operations raise `HostingServiceError(operation, "injected failure")` before any effect; an unknown name or `times` below 1 raises `ValueError` |
| `factory_posts(number)` | the comments with `by_factory` true, in order (how a test counts posts) |
| `labels(number)`, `description(number)` | what the factory wrote |
| `pull_requests()` | every pull request, whatever its state, by number |

```python
pull = hosting.create_pull_request("work-item/F0001-S0001", "title", "body", draft=True)
hosting.post_comment(pull.number, "Which option?", key)   # "posted"
hosting.add_human_comment(pull.number, "(a)")
assert len(hosting.factory_posts(pull.number)) == 1
```

### Data

The models in `factory.domain.hosting` are frozen, forbid unknown keys, and hold aware datetimes converted to UTC.

- `PullRequestView`: `number`, `branch`, `title`, `state` (`open`, `closed` or `merged`), `draft`, `merge_commit`, `url`. `merge_commit` is a 40-character lowercase hex commit id exactly when the state is `merged`, otherwise `None`.
- `PullRequestComment`: `id`, `author`, `body`, `created_at`, `by_factory`, `key`.

### The marker and the post key

Every post the factory makes ends with two lines: the marker `<!-- factory -->` and a key comment `<!-- factory key=<work item>:<kind>:<n> -->`, for example `<!-- factory key=F0001-S0001:question:7 -->`. `n` is lowercase hex and not empty; `kind` is one of `question`, `attempts_cap`, `round_cap`, `crash_cap`, `send_back`, `stall`, `expiry`, `correction`, `error`, `cost_table`.

- `render_post(text, key)` gives `text` without trailing whitespace, a blank line, the marker, and the key comment. Nothing follows.
- `parse_post_key(body)` reads only the last non-blank line, which must be exactly a valid key comment (trailing whitespace and `\r` are ignored). Anything else gives `None`.
- `PullRequestComment.from_body` sets `by_factory` when the body contains the marker, whoever the author is, and `key` to the parsed key when it is by the factory.

Why: see `docs/decisions.md`.

## The git wrapper

Git is reached only through the `Git` interface (`factory.application.git`, an abstract base class) and its one implementation `GitCli` (`factory.adapters.git_cli`), which inherits it. Every command goes through `run_process`; no other module starts git. It reads, and it writes the first things: clone, checkout, commit and push. It deletes branches and merges, and it restores the checkout: reset, revert and move (all below).

`GitCli(directory, options=None)` works in `directory`. `options` is a `GitOptions` (`factory.domain.git`; frozen, unknown keys forbidden), and `None` means `GitOptions()`:

| Field | Default | Meaning |
|---|---|---|
| `identity` | `GitIdentity(name="factory", email="factory@noreply.invalid")` | author and committer of the factory's commits; non-empty name and email. The default is only what an unset instance setting falls back to |
| `environment` | `{}` | extra environment for git; each `GitOptions` has its own dict |
| `kill_points` | `None` | reached by `push` (see below) |
| `executable` | `"git"` | the program to run (tests give a stand-in) |
| `time_limit` | `GIT_TIME_LIMIT` (5 minutes) | per command |

F0010's wiring fills `identity` from the instance settings `GIT_USER_NAME` and `GIT_USER_EMAIL`, and `environment` with the token for the factory's own pushes, so that the agent run never receives it.

The nineteen operations of the `Git` interface (`tests/application/test_git_interface.py` checks that the interface has exactly these and that `GitCli` has each):

| Operation | Returns |
|---|---|
| `fetch()` | `None`; runs `git fetch --prune origin`, so branches the remote deleted disappear; any failure is `FetchFailed` |
| `remote_branches()` | `list[RemoteBranch(name, commit)]` from `refs/remotes/origin/`, name without `origin/`, sorted by name, without `HEAD`; local branches are never listed |
| `resolve(ref)` | the 40-character commit id, or `None` when there is no such ref (also `HEAD` without commits) |
| `show_file(ref, path)` | the text exactly as committed, or `None` when `path` is absent or a directory; an unknown `ref` is a `GitError` |
| `list_files(ref, directory)` | full paths of all files under `directory` (no trailing slash), recursive, in string order; `[]` when the directory is absent; an unknown `ref` is a `GitError` |
| `is_ancestor(ancestor, descendant)` | whether `ancestor` is reachable from `descendant` (a commit is its own ancestor); an unknown ref is a `GitError` |
| `clone(url)` | `None`; runs `git clone <url> <directory>` from the parent of the bound directory and creates missing parents. The directory must be missing or empty, otherwise `GitError`. Afterwards the checkout is on the remote's default branch with `origin` set |
| `checkout(branch, *, start_point=None)` | `None`; switches to the local branch, or creates it at `origin/<branch>` when only the remote has it. With `start_point` it creates the branch there or resets an existing one to it (`git switch --force-create`, the same as `checkout -B`). An unknown branch or start point, or changes that stand in the way, is a `GitError` and leaves the branch and the changes as they were |
| `commit(message)` | the new commit id; stages every change (`add --all`, ignored paths stay out) and commits `message` verbatim, unsigned. Nothing staged raises `NothingToCommit` (a `GitError`) and commits nothing |
| `push(branch)` | `PushOutcome`: `"pushed"`, `"rejected"` or `"unreachable"` (below) |
| `delete_remote_branch(branch)` | `PushOutcome`; runs `git push --porcelain origin --delete refs/heads/<branch>` (below) |
| `delete_branch(branch)` | `None`; deletes the local branch even when it is not merged. The checked-out branch is a `GitError` and stays; a branch that does not exist is no error and changes nothing |
| `merge(ref, *, fast_forward_only=False)` | `MergeOutcome` (below) |
| `reset_to(ref)` | `None`; `git reset --hard` then `git clean -fd` (below) |
| `revert_paths(commit, paths)` | `None`; each path back to its content at `commit`, or deleted when it was not there (below) |
| `move(source, destination)` | `None`; `git mv` that creates the destination's folders (below) |
| `log(ref, *, since=None, path=None)` | `list[CommitInfo(commit, parents, subject, author, committed_at)]`: the commits reachable from `ref`, newest first, a commit always before its parents (a merge commit has two). `commit` and `parents` are full ids, `subject` is the first line of the message, `author` the author's name, `committed_at` the committer date in UTC. With `since`, only commits not reachable from it (`since == ref` gives `[]`); with `path`, only commits that changed that file or anything under that directory. An unknown `ref` or `since` is a `GitError` |
| `changed_paths(since)` | `list[ChangedPath(path, change)]`: the net difference between the commit `since` and the work tree, whether committed, staged, unstaged or untracked. Untracked files that are not ignored count, as `"added"`; ignored paths do not. A path added and deleted again, or changed and restored, is not listed. Sorted by path in plain string order. An unknown `since` is a `GitError` |
| `status()` | `WorkTreeStatus(branch, head, changes)`: `branch` is `None` when HEAD is detached, `head` is `None` in a repository without commits (`branch` then names the unborn branch). `changes` has one `ChangedPath` per path that differs from HEAD, staged, unstaged or untracked, listed once and sorted by path. A deleted path is `"deleted"`, a path HEAD lacks (untracked or newly staged, even if edited again) is `"added"`, anything else `"modified"`. Ignored paths are never listed |

`ChangedPath.change` is `"added"`, `"modified"` or `"deleted"` (`ChangeKind`); there is no `"renamed"`. Rename detection is off everywhere, so a rename is a deletion of the old path plus an addition of the new one. The four result models (`ChangedPath`, `CommitInfo`, `WorkTreeStatus`, `RemoteBranch`, in `factory.domain.git`) are frozen and forbid unknown keys; `committed_at` must be timezone-aware, and commit ids are 40 lowercase hexadecimal characters.

These three describe what the checkout holds; nothing is decided from them without the remote. Later features read recovery state from them: the undo compares the work tree with the stage-start commit (`changed_paths`), and the tick looks at `status()` before it restores the checkout.

Two edge cases are not exact: a path removed from the index with `git rm --cached` but still on disk shows as `"modified"` in `changed_paths` even when its content is unchanged, and unmerged paths in `status()` are `"modified"`.

Any other failure of a command (non-zero exit, cannot be started, `time_limit` reached) is a `GitError`. A missing ref or path is told apart from a failure by exit status and by `ls-tree -z` listings, never by git's wording.

Push never forces: it runs `git push --porcelain --set-upstream origin refs/heads/<branch>`. The outcome is a value, because the caller decides what a refusal means:

- `"pushed"`: git exited 0; afterwards `origin/<branch>` in the checkout is the pushed commit.
- `"rejected"`: the remote refused the update, a non-fast-forward or a remote hook that declined it (git marks the ref with `!`).
- `"unreachable"`: exit 128 with `Could not read from remote repository`, `does not appear to be a git repository`, `unable to access` or `Could not resolve host` in the output.
- Any other failure, such as an unknown local branch, is a `GitError`. A tag of the branch's name does not count as that branch: `push("v1")` with a local tag `v1` and no local branch `v1` is a `GitError` and pushes nothing.

The push kill points: `KillPoint.BEFORE_PUSH` is reached once per call, before git runs (between a commit and its push, so nothing reaches the remote); `KillPoint.AFTER_PUSH` is reached only after a push that returned `"pushed"`. A rejected or unreachable push reaches only the first. A `GitCli` without kill points pushes normally.

### Deleting and merging branches

`delete_remote_branch` returns the push outcomes with these meanings: `"pushed"` when the branch is gone from the remote afterwards, also when it was already gone (git exits 0 for a qualified name, so that is a plain success; the remote only warns). A tag of the same name on the remote is left alone; `"rejected"` when the remote refuses the deletion, for example a hook; `"unreachable"` under the same conditions as `push`. A name git would refuse, such as `a..b`, is a `ValueError` before git runs (see the branch rule below). Any other failure is a `GitError`. After `"pushed"` the remote-tracking ref `origin/<branch>` is gone from the checkout too, even when the remote branch was already gone and the checkout held a stale `origin/<branch>`. It reaches no kill point.

`merge` merges `ref` into the checked-out branch and returns a `MergeOutcome` (`factory.domain.git`), decided from the ancestry of the two commits, not from git's messages:

- `"up_to_date"`: `ref` is already contained in `HEAD`; nothing changes (also with `fast_forward_only`).
- `"fast_forwarded"`: `HEAD` is contained in `ref`; the branch moves to `ref` without a merge commit (also with `fast_forward_only`).
- `"not_fast_forward"`: the two have diverged and `fast_forward_only` is true; nothing changes.
- `"merged"`: diverged without conflict; a merge commit with git's default message (no editor, unsigned), `HEAD` and `ref` as parents, and the identity of the options as author and committer.
- `"conflict"`: the merge conflicts. It is aborted before the call returns, so `HEAD`, the index and the work tree are as they were and no merge is in progress. A conflict never leaves a merge half done.

An unknown `ref`, and any other refusal that leaves no merge in progress (for example local changes the merge would overwrite), is a `GitError` and changes nothing.

Who uses them: preparing a stage merges the main branch into a work item's branch (F0005); a merge or a discard deletes branches, remote and local (F0007).

### Restoring the checkout

These three make the checkout disposable: whatever a stage or a crash left behind can be put back.

- `reset_to(ref)` resolves `ref` to a commit, runs `git reset --hard` on it, then `git clean --force -d`. Tracked files, staged or not, go back to `ref` and the current branch points at it. Untracked files and directories are removed; ignored paths (a file named in `.gitignore`) stay. An unknown `ref` is a `GitError` and nothing changes. The ref is resolved first, so git only ever sees a commit id (`reset` takes no `--end-of-options`); an option-like `ref` is refused earlier by the argument rule below.
- `revert_paths(commit, paths)` brings each path to its content at `commit`, in the work tree and in the index. A path that does not exist at `commit` (added later, only staged, or untracked) is deleted from both. A path that exists nowhere is skipped without an error. Paths that were not given are not touched. An unknown `commit` is a `GitError`. A path that is a directory is not supported: the rules speak of files, and git then fails with a `GitError`.
- `move(source, destination)` creates the destination's parent folders and runs `git mv`; the move is staged as a rename (`status()` and `changed_paths()` still show it as a deletion plus an addition, see above). A `source` that is not tracked, or a `destination` that exists, is a `GitError`.

The path rule, for `revert_paths` (every path) and `move` (both arguments): a path is relative to the repository, with forward slashes. `factory.domain.git.check_repository_path` raises `ValueError` for an empty path, an absolute path or one with a `..` segment, and it runs before anything is changed or created. So `revert_paths` changes no path of a call that holds one bad path, and `move` creates no folder outside the checkout. `docs/a.txt` is fine, `../x` and `a/../../x` are not.

The argument rule, for every ref, branch, start point, commit and url: `factory.domain.git.check_git_argument` raises `ValueError` for an empty value and for one that starts with `-`, because git would read it as an option (`push("--force")` would force-push). No git ref, branch name or remote url starts with a dash, so nothing valid is lost; a hyphen inside a name (`work-item/F0001-S0001`) is fine. `GitCli` checks before it starts git and before any kill point, so a refused call starts no process, changes nothing and does not reach `BEFORE_PUSH`. The operations and arguments: `resolve(ref)`, `show_file(ref, …)`, `list_files(ref, …)`, `is_ancestor` (both), `log` (`ref`, and `since` when given), `changed_paths(since)`, `clone(url)`, `checkout` (`branch`, and `start_point` when given), `push`, `delete_remote_branch`, `delete_branch`, `merge(ref)`, `reset_to(ref)` and `revert_paths(commit, …)`. Why not `--end-of-options`: see `docs/decisions.md`. Inside an operation, git is read through the private `_resolve_unchecked`, `_is_ancestor_unchecked` and `_blob`, never through another public operation, so each argument is checked once.

The branch rule for pushing: `push` and `delete_remote_branch` call `factory.domain.git.check_branch_name` instead, because `git push` reads its branch as a refspec. It refuses everything `check_git_argument` refuses, and also a value that starts with `+` (it forces: `push("+main")` overwrites a diverged `main`), one that contains `:` (it names another ref or deletes one: `push(":keep")` deletes `keep`, `push("HEAD:refs/heads/other")` creates `other`) and one that contains `*` (a pattern that pushes every matching branch, or none). It also refuses the whole values `HEAD` and `@` (git pushes the checked-out branch under its own name) and anything `git check-ref-format --branch` would refuse, applied in the domain without calling git: `^`, `~`, `?`, `[`, `\`, space and control characters, `..`, `@{`, a leading, trailing or doubled `/`, a trailing `.`, and a component that starts with `.` or ends with `.lock`. `push("^main")` is a negative refspec that pushes nothing yet exits 0. A plus or an `@` inside a name (`a+b`, `a@b`) and `feature/HEAD` are fine. The refusal is a `ValueError` before git and before `BEFORE_PUSH`, and the remote is untouched. It refuses a name git itself allows (`+main`); the factory's names (`main`, `work-item/<id>`) never take that form.

The branch is also named `refs/heads/<branch>` on git's command line, as the source only, with no `:<dst>`. Without it git matches any ref of that name, so `delete_remote_branch("v1")` would delete a tag `v1` and `push("v1")` would push a local tag; with it a tag is never pushed or deleted as a branch. The local operations (`checkout`, `delete_branch`, `merge`, …) keep `check_git_argument`, because git reads no refspec there. Why not an explicit `refs/heads/<b>:refs/heads/<b>` refspec: see `docs/decisions.md`.

Who uses them: a stall or a crash reverts or resets (F0004, F0005, F0008); the tick resets the checkout to the remote (F0006); the undo's revert is this wrapper's, the rules for what to revert are F0004's; a merge or a discard moves the story file (F0007).

### Which feature uses which operation

| Operation | Used by |
|---|---|
| `changed_paths`, `revert_paths` | F0004: the undo compares the work tree with the stage-start commit and reverts chosen paths |
| `merge` | F0005: preparing a stage merges the main branch into the work item's branch |
| `status`, `reset_to` | F0006: the tick looks at the checkout and resets it to the remote |
| `reset_to` | also F0004, F0005 and F0008: a stall or a crash |
| `delete_remote_branch`, `delete_branch`, `move` | F0007: a merge or a discard |
| `fetch`, `remote_branches`, `resolve`, `show_file`, `list_files`, `is_ancestor`, `log`, `clone`, `checkout`, `commit`, `push` | the pipeline's reads and first writes; no story names a single user yet, they are the building blocks of the tick, the stages and the claim |

Identity: every call also sets `GIT_AUTHOR_NAME`, `GIT_COMMITTER_NAME`, `GIT_AUTHOR_EMAIL` and `GIT_COMMITTER_EMAIL` from `options.identity`, over the process environment and `options.environment`. No user or system configuration can change it, and `commit.gpgsign` is ignored. F0010 fills `identity` from `GIT_USER_NAME` and `GIT_USER_EMAIL`; a `GitCli` built without options commits as `factory <factory@noreply.invalid>`.

Configuration is isolated: each call runs with the process environment, then `options.environment`, then the identity, then `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL` set to the null device, and `LC_ALL=C`. The isolation, the identity and the locale come last, so `options.environment` cannot lift them. `LC_ALL=C` keeps git's messages English: the push outcomes `"unreachable"` and an already-deleted remote branch are recognised by them, and an operator's locale must not turn them into a `GitError`. It does not change how paths are read: the `-z` listings are the paths' bytes and `run_process` decodes them as UTF-8. Credentials therefore reach git only through the environment (for example `GIT_ASKPASS`, or `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_<n>`, `GIT_CONFIG_VALUE_<n>`), never through global or system configuration, and never inside a URL, because git may print a URL. Why: see `docs/decisions.md`.

Tests use real git. The `remote` fixture is a bare repository in `tmp_path` with the pipeline definition, the story form and one feature with one story on `main`, and `checkout` is a `GitCli` on a clone of it (identity `TEST_IDENTITY`). `tests/git_support.py` has the helpers: `run_git` (through `run_process`, same isolation, author `Test Author`) and `write_executable` for a stand-in `executable`, and `remote_commit(remote, branch)`, which reads a branch of the bare remote with plain git and gives `None` when it is absent. Git is not faked. Tests check results with plain git through `run_git`, not through other `GitCli` methods.

The `human` fixture (`HumanClone` in `tests/human_clone.py`) is a second clone of `remote`, the writer a push test needs besides `checkout`; it is built with `TEST_IDENTITY` and drives `GitCli`. `start(path)` moves a story file from `backlog/` to `in-progress/` on `main`, commits and pushes. `push_file(branch, path, text)` writes the file on that branch (created from `origin/main` if the remote has none), commits and pushes. `merge(branch, method)` brings `origin/<branch>` into `main` and pushes it: `"merge"` as a merge commit, `"squash"` as one ordinary commit that leaves the branch tip outside the history of `main`, `"rebase"` as the branch's commits replayed with no merge commit. Every push it makes must return `"pushed"`.

## Project commands

The factory reaches a project's build only through the `ProjectCommands` interface (an abstract base class, `factory.application.project_commands`). It has one operation, `run(command, *, time_limit) -> CheckResult`. `MakeProjectCommands(directory, kill_points=None, *, executable="make")` (`factory.adapters.make_commands`) is the first implementation. It inherits `ProjectCommands`. The string `"make"` appears in no other module under `src/factory`; `tests/test_make_search.py` checks it. The pipeline uses the results from F0005, the preflight's probe from F0010.

`run` starts `<executable> --no-print-directory <command>` in `directory` through `run_process`, with stderr merged into stdout. The environment is the current one less `MAKELEVEL`, `MAKEFLAGS` and `MFLAGS`. Without that, a run inside `make check` (where `MAKELEVEL` is set) would print `make[N]: Entering directory` lines that a run on its own does not. `directory` is where make finds the project's Makefile.

Rules of `run`:

- `time_limit` of zero or less raises `ValueError`.
- `command` must match `^[a-z][a-z0-9-]*$`, checked with a full match. Otherwise `ProjectCommandError` is raised before anything is started. So is an `executable` that cannot be started; the detail is the operating system's message.
- The exit status is the only judgment. 0 is `"passed"`, any other is `"failed"`, and a command ended by the `time_limit` is `"time_limit"` with `exit_status` `None`; the process group is killed. GNU make, not the recipe, sets the status: it exits 2 whenever a recipe fails, whatever status the recipe's command had, and when the target is missing. A missing target is therefore a failed command, not an error.
- `output_tail` is the last 30 lines (`OUTPUT_TAIL_LINES`) of the merged output, in the order written; all of it when shorter.
- `last_line` is the last line that is not blank and does not start with `make:` or `make[` (make's own messages); `""` when there is none.
- `duration` is the time the command ran.
- `kill_points` is accepted so that wiring builds every wrapper the same way; this wrapper reaches no kill point.

`CheckResult` (`factory.domain.checks`) is frozen, forbids unknown keys, and has the fields `command`, `status`, `exit_status`, `duration`, `last_line` and `output_tail`. `status` and `exit_status` must agree (`status_of(exit_status)` is the one mapping), or validation fails. `passed` is true only for `"passed"`. The result is generic: it carries no layer names (R8), and no identifier in the three modules contains `layer`.

A project declares its own layers and checks them with a project command of its own. To add the layers check, the project adds a make target (for example `layers`, which calls its tool through uv) to its Makefile and, where it belongs in the gate, makes `check` depend on it. The factory sees only that target's `CheckResult`: its status, `last_line` and `output_tail`.

```python
result = MakeProjectCommands(Path(".")).run("check", time_limit=timedelta(minutes=10))
if not result.passed:
    print(result.status, result.exit_status, result.last_line)
```

Tests write a Makefile into `tmp_path` and run the class against it; nothing is faked.

## Starting a process

`subprocess` is imported, and a process started, in `factory.adapters.process` only (R5). The git wrapper, the make class and the `claude -p` runtime each reach their tool through `run_process(request) -> ProcessResult`; no other module calls a command-line tool.

`ProcessRequest` (frozen, unknown keys forbidden) holds:

- `argv`: the program and its arguments, at least one element, passed as given. There is never a shell, so `$HOME; echo x` reaches the child as that text.
- `cwd`: the working directory.
- `env`: `None` lets the child inherit the current environment; a mapping is the child's whole environment, nothing is added.
- `time_limit`: `None` for no limit, otherwise greater than zero (a zero or negative value is a `ValidationError`).
- `merge_stderr`: the child's stderr goes into the same pipe as its stdout, in the order written, and `ProcessResult.stderr` is empty.

The child runs in its own session, with stdin closed. At the `time_limit` the whole process group is killed with SIGKILL, so what the command started ends too, and `run_process` returns with `exit_status=None`, `timed_out=True` and the output written so far. A child that ends in time gives its real exit status and `timed_out=False`; a non-zero status is returned, not raised. Output is decoded as UTF-8 with undecodable bytes replaced. A failure to start, such as `FileNotFoundError`, is an `OSError` and is not caught: the wrapper above decides what it means.

```python
result = run_process(ProcessRequest(argv=["git", "status"], cwd=repo, time_limit=timedelta(seconds=30)))
```

Known limits: after the kill, the output is read without a limit, so a descendant that left the group (by calling `setsid`) and still holds the pipe would block the call; and a child that exits normally but leaves a background process holding its stdout open makes the call wait for that process (bounded by `time_limit` if one is set).

`tests/test_process_search.py` keeps the boundary: only `process.py` imports `subprocess`; `shell=True`, `os.system`, `os.popen`, `os.exec*`, `os.spawn*`, `os.posix_spawn*` and `asyncio.create_subprocess_*` are used nowhere under `src/factory`; and the only suppression markers there are the four in `process.py` (`noqa: S404` and `nosec B404` on `import subprocess`, `noqa: S603` and `nosec B603` on the `subprocess.Popen(` line). Do not write those marker words in a comment or docstring in `src/factory`. Why: see `docs/decisions.md`. Tests run real child processes (Python one-liners through `sys.executable`) in `tmp_path`; nothing is faked.

## The agent runtime

The factory reaches an agent only through the `AgentRuntime` interface (an abstract base class, `factory.application.agent_runtime`): `run(request) -> AgentRunResult` and `version() -> str`. The DTOs are in `factory.domain.agent_runs`. All are frozen and forbid unknown keys. The `claude -p` implementation is `ClaudeCodeRuntime` (below); it inherits `AgentRuntime`. The fake is the other implementation.

`AgentRunRequest` holds:

- `agent`: an `AgentDefinition` (`name`, `model`, `tools`, `effort` or `None`, `budget_usd` greater than 0, `instructions`). `name` is a `Name` (`factory.domain.identifiers`): lower-case letters, digits and hyphens, starting with a letter.
- `prompt`, `time_limit` (greater than zero) and `working_directory` (absolute).
- `allowed_decisions`: must contain `QUESTION` (`"question"`) and have no repeats, so an agent can always ask the human. The validation error names `question`.
- `environment`: the run's whole environment, `{}` by default; `guard`: optional `GuardSettings` (absolute `root`, `write_paths`, `protected_paths`); `os_user`: optional.

`AgentRunResult` holds `end_reason`, `decision`, `entry`, `duration`, `turns`, `tokens` (`TokenCounts`: `input`, `output`, `cache_read`, `cache_creation`, none negative), `cost_usd` and `permission_denials`. `end_reason` is one of `completed`, `no_result`, `time_limit`, `budget` and `died`. `decision` and `entry` are set exactly when the run is `completed`, and `ok` is true exactly then. A measure the runtime did not report is `None`, never 0: unknown is unknown.

A run that dies, reaches its `time_limit` or exhausts its budget is a result with an end reason, not an exception; for the caller it is a stall. `AgentRuntimeError` is for a runtime that cannot be used at all. See `docs/decisions.md`.

### The `claude -p` runtime

`ClaudeCodeRuntime(executable, state_directory, kill_points=None, *, version_time_limit=VERSION_TIME_LIMIT)` (`factory.adapters.claude_runtime`) runs an agent as a `claude -p` call under the operator's own login; a call stopped by its budget is resumed once (below). It starts the process through `run_process`, and with `git_cli` and `make_commands` it is one of the three modules that import `factory.adapters.process` (`tests/test_wrapper_search.py`).

The arguments, in this order (`<session>` is a new `uuid4` per run):

```text
-p <prompt>  --model <model>  [--effort <effort>]  --tools <tools joined with commas>
--session-id <session>  --append-system-prompt-file <state_directory>/instructions-<session>.md
[--settings <state_directory>/hooks-<session>.json]  --permission-mode auto  --permission-prompts none
--strict-mcp-config  --max-budget-usd <budget as plain decimal>  --output-format json  --json-schema <schema>
```

`--effort` is left out when the agent has none; `--settings` when the request has no guard; `--tools` is always there, with an empty value for an empty list. The flags are v1's, not yet checked against the pinned `claude`. The schema asks for an object with `decision` (an enum of `allowed_decisions`, in the request's order) and `entry` (described by `ENTRY_DESCRIPTION`), both required, nothing else.

Files under `state_directory` (created with its parents when missing), written before the call and removed when the run ends, whether by a result, `InjectedKill` or `AgentRuntimeError`:

- `instructions-<session>.md`: the agent's instructions.
- With a guard only: `guard-<session>.json` (the `GuardSettings` as JSON) and `hooks-<session>.json`, a `PreToolUse` hook on `Edit|Write` whose command is `factory-guard --settings <guard file, shell-quoted>`. The `factory-guard` command itself is not built yet.

Environment: the call gets `request.environment` plus `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` and `PYTHONDONTWRITEBYTECODE=1`. Nothing is inherited from the factory's process and no `PATH` is added; `factory-guard` is found only if the request's own `PATH` holds it. The call runs in `request.working_directory`, and `request.os_user` is not used yet.

End reason, first rule that applies: `time_limit` when the time limit ended the call (it is killed with its children); `died` when the exit status is not 0, the output is not a JSON object with a string `subtype` and a boolean `is_error`, or `is_error` is true; `completed` when `structured_output` has a `decision` from `allowed_decisions` and a non-blank `entry`; otherwise `no_result`. A reply with `subtype` `error_max_budget_usd` is `budget`, checked right after `time_limit` and before the exit status, because `claude` may exit non-zero on a budget stop. The rules above describe one call; the resume below applies them to each call.

Measures: `duration` is what the factory measured around the call; the JSON's own durations are ignored. `turns`, `cost_usd` (`Decimal(str(total_cost_usd))`), `tokens` and `permission_denials` come from the JSON when it parses, and are `None` for any field it lacks, and for all of them after a `time_limit`. For a resumed run they are added up (below). `tokens` is known only when both `input_tokens` and `output_tokens` are present; the cache counts default to 0. A denial's `detail` is its `tool_input` as JSON with sorted keys. A reply with the wrong type in a field it carries does not parse and counts as `died`. So does a reply with a negative `num_turns`, token count or `total_cost_usd`: it counts as `died` and every measure is unknown (`None`); zero is valid. This holds for a budget-stop reply too, which is then not resumed.

Kill point: `KillPoint.AGENT_RUN` is reached once, after the last call and the result, whatever the end reason, and not when the call could not be started. A missing executable or an unwritable state directory raises `AgentRuntimeError` naming the cause.

The budget resume. When a call ends with `budget`, the same session is resumed once, so that an agent that ran out of money still gives its decision and entry. The arguments are the first call's, except `-p` is `FINISH_MESSAGE`, `--session-id <session>` becomes `--resume <session>`, and `--max-budget-usd` is `resume_budget(agent.budget_usd)`: a quarter of the budget, at least `MINIMUM_RESUME_BUDGET` (0.50), rounded half up to cents. The run's files are the same ones and are removed when the run ends. The resumed call's reply is read by the rules above; if it also ends with `budget`, so does the run. A third call is never made. `FINISH_MESSAGE` asks for `question` where v1 asked for `stuck`.

One `time_limit` counts across the run: the first call may take `request.time_limit`, the resume what is left of it, measured by the factory from the start of `run`. A first call ended by the time limit is never resumed. If nothing is left when the first call ends, the resume is skipped and the run ends as `time_limit`.

Measures of a resumed run: `turns`, `cost_usd` and each of the four token counts are the sums over both calls; a call that reported none adds nothing, and a measure is `None` only when neither call reported it. When the resumed call is ended by the time limit, `turns`, `cost_usd` and `tokens` are all `None` (R24: no partial figure; the first call's alone would be one). Permission denials are joined, the first call's first. `duration` is the factory's own, from the start of `run` to the end of the last call.

`version()` runs `<executable> --version` through `run_process` in the process's current directory, with its current environment and the limit `version_time_limit` (`VERSION_TIME_LIMIT`, 30 seconds). It returns the first word of the first non-blank line, so `2.1.289 (Claude Code)` gives `2.1.289`. It raises `AgentRuntimeError` when the call cannot be started, exits non-zero, reaches the limit or prints nothing.

Tests use a stand-in executable (`tests/adapters/claude_stand_in.py`: `write_stand_in(directory, steps)` and `read_calls(directory)`) written into `tmp_path`; the real `claude` is never run.

### The fake

`FakeAgentRuntime(kill_points=None, version="fake")` (`factory.adapters.fake_agent_runtime`) is what every stage test uses. It inherits `AgentRuntime`, an abstract base class. The `agent_runtime` fixture in `tests/conftest.py` builds one with the test's `kill_points`.

A test queues `ScriptedRun`s (`writes`: path to UTF-8 text, `deletes`, `result`, `kill`) with `queue`. Each `run` call:

1. records the request (`requests()` lists all, in order, also one that raised);
2. takes the oldest queued run, or raises `AgentRuntimeError` when none is queued;
3. checks every path, then writes (parent folders created, an existing file replaced) and deletes (a missing path is ignored) relative to `request.working_directory`. An absolute path or a `..` segment raises `AgentRuntimeError` before anything is written or deleted;
4. when `kill` is true and the fake has kill points, reaches `KillPoint.AGENT_RUN`, which raises `InjectedKill` if armed. The writes are already on disk, as after a real crash;
5. returns the scripted `result`.

```python
agent_runtime.queue(ScriptedRun(writes={"tests/test_a.py": "x = 1\n"}, result=result))
outcome = agent_runtime.run(request)
assert outcome.ok and agent_runtime.requests() == [request]
```

## Kill points: testing a crash

A test that must show the factory survives its own death arms a kill point. The seam is `factory.domain.kill_points`; the tests that use it to prove recovery come with the recovery features (F0008, F0011).

There are four points, the members of `KillPoint`:

| Point | Value | Reached by |
|---|---|---|
| `AGENT_RUN` | `agent-run` | the two agent runtimes: the fake after the run's writes, `claude -p` after the last call and its result |
| `BEFORE_PUSH` | `before-push` | the git wrapper, before a push |
| `AFTER_PUSH` | `after-push` | the git wrapper, after a push |
| `AFTER_POST` | `after-post` | the fake hosting service and the PyGithub client, after posting |

Each wrapper in the table calls `kill_points.reach(point)` at its point; no other code reaches one.

A new `KillPoints` is inert. In a test, use the `kill_points` fixture from `tests/conftest.py`, which returns a new `KillPoints()` for each test, and hand it to the wrapper under test:

```python
def test_push_dies_after_the_second_try(kill_points: KillPoints) -> None:
    kill_points.arm(KillPoint.BEFORE_PUSH, after=1)
    with pytest.raises(InjectedKill):
        ...  # code that reaches BEFORE_PUSH twice
    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 2
```

- `arm(point)` makes the next `reach(point)` raise `InjectedKill`. `arm(point, after=n)` lets `n` reaches pass first and raises on the next; `after` counts from the arming. A negative `after` raises `ValueError` and changes nothing.
- A point fires once and is then inert again. Arming an armed point replaces the earlier arming. Arming one point never changes another, armed or not.
- `reached(point)` counts every reach, the one that raises included, armed or not.
- Each `KillPoints` instance has its own state.
- `str(InjectedKill(point))` is `injected kill at <point value>`, and `.point` is the point that fired.

`InjectedKill` is a `BaseException`; see `docs/decisions.md`.
