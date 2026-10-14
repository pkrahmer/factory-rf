# Project guide

The guide for agents working on `factory-rf`: how the code is laid out, where a change belongs, which conventions the checks do not catch, and what to read first. It grows with each story: the documenter stage fills it in from the stories' docs criteria. `CLAUDE.md` holds the rules every change follows.

## Errors

`factory.domain.errors.FactoryError` is the root of every error the factory raises on purpose. Later stories add their error types under it. `InjectedKill` (below) is deliberately not one.

`BoundaryError` (a `FactoryError`) is the root of the errors for an outside party that failed. `HostingServiceError(operation, detail)` is its first subtype: every implementation of the hosting-service interface raises it for every failing call, and its message is `hosting service <operation> failed: <detail>`. `operation` and `detail` are attributes.

`GitError(command, exit_status, output_tail)` is its second subtype, for the git wrapper. `command` is `git ` and the arguments (`git fetch --prune origin`); `exit_status` is `None` when git could not be started or hit its time limit; `output_tail` is the last 30 lines of the output, stdout and stderr merged (all of it when shorter). The message is `<command> failed (exit <status>): <tail>`, or `failed (no exit status)` when the status is `None`. `FetchFailed` is a `GitError` that `fetch` raises for every failure. `NothingToCommit` is a `GitError` that `commit` raises when nothing is staged.

`ProjectCommandError(command, detail)` is its third subtype, for the project commands: it is raised only when a command cannot be started (an invalid name, or an executable the operating system cannot start). The message is `project command <command> failed: <detail>`; `command` and `detail` are attributes. A red command is a result, not this error.

`AgentRuntimeError(detail)` is its fourth subtype, for the agent runtime. The message is `agent runtime failed: <detail>`; `detail` is an attribute. A run that dies, hits its `time_limit` or runs out of budget is a result, not this error (see *The agent runtime*).

`PushFailed(branch, outcome)` is a `FactoryError` for a push that did not reach the remote; `outcome` is the git wrapper's `PushOutcome` other than `"pushed"` (`rejected`, `unreachable`), and the message names the branch and the outcome. The claim service raises it (see *The claim service*).

`WorkItemFormatError(fault, path=None)` is a `FactoryError` for a work item file that cannot be read (see *The data of a work item*).

`CostRecordFormatError(line, fault)` is a `FactoryError` for a cost record file that cannot be read or written; `line` is counted from 1 and the message is `line <line>: <fault>`.

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

## Identity, order and places of work items

Two pure domain modules give a work item its identity, its order and its place. Neither reads a file, the clock or a process (a test parses their imports). `factory.domain.identifiers` holds the ids; `factory.domain.paths` holds the names of the project's `factory/` tree.

### Ids and names

- `WorkItemId` is `F0001-S0001` (a story) or `F0001-A0001` (an acceptance); `FeatureId` is `F0001`; `Name` is lower-case letters, digits and hyphens, starting with a letter. The patterns `FEATURE_ID`, `STORY_ID` and `ACCEPTANCE_ID` are the unanchored regular expressions.
- A work item file is `<id>.md` or `<id>-<slug>.md`; a feature directory is `<id>` or `<id>-<slug>`. A slug is lower-case segments of letters and digits joined by single hyphens (`2fa` and `a-b` are slugs; `Bad`, `a-`, `-a` and `a--b` are not). `parse_work_item_file_name` and `parse_feature_directory_name` return a `WorkItemFileName` or `FeatureDirectoryName` (frozen, `id` and `slug`, the slug `None` when absent), or `None` for any other string; they never raise.
- `is_acceptance`, `feature_of`, `work_item_order` and `branch_name` take a `WorkItemId` and raise `ValueError` for a string that is not one.
- The branch of a work item is `work-item/<id>` (`branch_name`), never the file name, so a slug cannot change it. `work_item_of_branch` gives the id back for exactly that form and `None` for anything else. `BRANCH_PREFIX` is defined in `identifiers` (to avoid an import cycle) and re-exported by `paths`.

### Order

`work_item_order(id)` is the sort key `(feature id, 0 for a story or 1 for an acceptance, id)`. Sorted by it, the features come in plain string order, and inside a feature every story (in plain string order) comes before the acceptances. Plain string order alone would put `F0002-A0001` before `F0002-S0001`. The slug is not part of the id, so it never changes the order. Plain string order of the ids is otherwise the human's only priority; use this key wherever work items are listed or picked. Why it is a key: see `docs/decisions.md`.

### The tree

All spellings are constants in `factory.domain.paths`:

| Constant | Value |
| --- | --- |
| `FACTORY_DIRECTORY` | `factory` |
| `PIPELINE_DEFINITION_FILE` | `factory/pipeline.yml` |
| `STORY_FORM_FILE`, `FEATURE_FORM_FILE` | `factory/story-form.md`, `factory/feature-form.md` |
| `FEATURES_DIRECTORY` | `factory/features` |
| `FEATURE_FILE_NAME` | `feature.md` |
| `LIFECYCLE_FOLDERS` | `backlog`, `in-progress`, `done` (in that order) |
| `COST_RECORDS_SUFFIX` | `.costs.jsonl` |
| `BRANCH_PREFIX` | `work-item/` |
| `LABEL_PREFIX` | `stage:` |
| `REMOTE`, `MAIN_BRANCH` | `origin`, `main` |

- `work_item_path(feature_directory, folder, file_name)` is `factory/features/<feature_directory>/<folder>/<file_name>`.
- `cost_records_path(path)` replaces the final `.md` with `.costs.jsonl`, so the sidecar sits beside the work item; a path not ending in `.md` is a `ValueError`.
- `folder_of(path)` returns the lifecycle folder of a work item path and `None` for anything else. A work item path has exactly the shape `factory/features/<feature directory>/<folder>/<file>`, where the directory parses as a feature directory name, the folder is a lifecycle folder and the file parses as a work item file name (an acceptance file too). So a sidecar, a `.gitkeep`, a `README.md`, a folder such as `drafts` or `ongoing` and a path one level too deep or too shallow all give `None`.

```bash
uv run python -c "
from factory.domain.identifiers import parse_work_item_file_name, work_item_order
ids = [parse_work_item_file_name(n).id for n in ['F0002-A0001.md', 'F0002-S0002-2fa.md', 'F0002-S0001.md', 'F0001-S0010-x.md']]
print(sorted(ids, key=work_item_order))
"
```

prints `['F0001-S0010', 'F0002-S0001', 'F0002-S0002', 'F0002-A0001']`.

## The data of a work item

A work item file is a front matter and a body. Three pure domain modules hold the front matter's data as frozen Pydantic models that refuse unknown fields; none reads or writes a file. Every rule with one right answer is a validation of these types, so the reader and the writer only translate.

### The state

`factory.domain.work_item.WorkItemState` is the front matter. Its fields, in the order they are written, with their initial values:

| Field | Type | Initial |
|---|---|---|
| `stage` | `Name` | the first stage (no default) |
| `blocked` | `question`, `attempts_cap`, `round_cap`, `crash_cap`, `send_back` or `None` | `None` |
| `round` | integer ≥ 0 | 0 |
| `attempts` | integer ≥ 0 | 0 |
| `crashes` | integer ≥ 0 | 0 |
| `pull_request` | integer ≥ 1 or `None` | `None` |
| `comments_read` | ids of the comments already read | `[]` |
| `handed_over` | `Name` or `None` (the hand-over marker) | `None` |
| `claim` | `Claim` or `None` | `None` |
| `journal` | list of `JournalRecord` | `[]` |

`initial_state(first_stage)` is the state of a story just started: `WorkItemState(stage=first_stage)`. A `first_stage` that is not a `Name` raises `pydantic.ValidationError`.

Rules the state enforces:

- `comments_read` ascends with no repeats.
- A `claim` is for the state's own `stage`.
- The `journal`'s numbers are 1, 2, 3 up to n in order.

The first two are validations of their own field, so their error is located at that field (`("comments_read",)`, `("journal",)`). The claim rule spans two fields, so its error has an empty location (`()`). The work item reader names a fault by that location.

### The claim

`Claim` is an instance's hold on a work item: `instance` and `stage` (both `Name`), `started_at` and `lease_duration` in minutes (at least 1). `started_at` must carry a time zone and is stored in UTC.

### The journal's data

`factory.domain.journal.JournalRecord` is the one element the front matter lists for each journal entry: `number` (≥ 1), `speaker` (a `Name`; `HUMAN` is `"human"` and `FACTORY` is `"factory"`) and `kind`. So the speaker and kind of every entry are data in the front matter, beside the entry text in the body. `JournalKind` is one of `created`, `started`, `result`, `question`, `comment`, `close`, `stall`, `crash`, `expiry`, `move_back`, `send_back`, `done`.

### The journal's entries

The journal is two halves that always match. The visible half is Markdown in the body under `## Journal`; the data half is the front matter's `journal` list. `append_entry(document, NewEntry(...))` writes both in one call, so the number of records equals the number of entries. The input document is not changed; the result ends with a newline exactly when the body did.

- **Format.** An entry is `<number>. <speaker>: <text>`. Only the human's entries are dated: `<number>. <YYYY-MM-DD> human: <text>`; `NewEntry` requires `on` for the speaker `human` and refuses it for any other. The text is stripped and must not be blank. Lines after the first are indented by the width of `"<number>. "` (3 spaces for 1 to 9, 4 for 10 to 99, 5 for 100 to 999); a blank line stays empty. An entry whose text leaves a code block open gets one more line that closes it: the indent and the opening run, the same character and count, without the info string (a text ending in an unclosed four-backtick `python` block gets a closing line of four backticks). The numbered first line opens no block, so a fence there does not count. Without that line an open fence would hide the later entries and the sections after the journal, and the form check would report a valid work item as damaged. `NewEntry.text` and the journal records stay as given. Entries follow one another with no blank line between them, directly after the last non-blank line of the section (or one blank line under the heading when the section is empty), so a section after the journal keeps its blank line.
- **Speaker and kind are data.** Code that needs to know who spoke or what kind an entry is reads the state: `last_record(document, speaker=..., kind=...)` returns the last record that matches every filter given, or `None`. Nothing reads them from the text, so changing how a speaker is displayed (`intake:` to `Intake Agent:`) changes no record. `entry_text(document, number)` returns an entry's text as rendered, a closing fence line included (without its indent), for display only: it finds the line that starts with `"<number>. "` at column 0 and ends the entry at the next line that starts with a number at column 0, so an indented `2. ...` inside a text is not an entry.
- **Restore.** `restore_state_and_journal(current, baseline)` is how the factory undoes an agent's tampering with state and journal. It returns the current document with the baseline's whole state and the baseline's `Journal` section (from its heading to its last non-blank line) put in place of the current one; edits elsewhere in the body, the blank lines before the next section and the current `ignored_keys` stay. If the current body has no `Journal` section, the baseline's is added at the end after one blank line.
- **Faults** are `WorkItemFormatError`: `the document has no state` (for `append_entry`, `last_record` and a baseline without state), `missing section: ## Journal` and, for `entry_text`, `no journal entry <number>`.
- **Imports.** `factory.domain.work_item` imports `JournalRecord` from `factory.domain.journal`, so the journal module imports `work_item` only under `TYPE_CHECKING` and builds documents with `model_copy`. Either module can be imported first.

```bash
uv run python -c "
from datetime import date
from factory.domain.journal import NewEntry, append_entry, entry_text, last_record
from factory.domain.work_item import WorkItemDocument, initial_state
doc = WorkItemDocument(state=initial_state('intake'), body='# T\n\n## Journal\n')
doc = append_entry(doc, NewEntry(speaker='human', kind='created', text='created.', on=date(2026, 10, 12)))
doc = append_entry(doc, NewEntry(speaker='intake', kind='result', text='accepted\nEvery criterion is testable.'))
print(doc.body, end='')
print(last_record(doc, speaker='intake'))
print(entry_text(doc, 2))
"
```

prints the body (`# T`, an empty line, `## Journal`, an empty line, `1. 2026-10-12 human: created.`, `2. intake: accepted`, `   Every criterion is testable.`), then `number=2 speaker='intake' kind='result'`, then `accepted` and `Every criterion is testable.`.

### The document and its error

`WorkItemDocument(state, body, ignored_keys=[])` pairs a state with the body text. `state` is required but may be `None`, for a file read as a specification. `ignored_keys` lists front matter keys the reader did not use.

`factory.domain.errors.WorkItemFormatError(fault, path=None)` is the `FactoryError` for a work item file that cannot be read. Both are attributes; the message is `fault`, or `<path>: <fault>` with a path.

```bash
uv run python -c "
from factory.domain.work_item import initial_state
print(initial_state('intake').model_dump())
"
```

prints `{'stage': 'intake', 'blocked': None, 'round': 0, 'attempts': 0, 'crashes': 0, 'pull_request': None, 'comments_read': [], 'handed_over': None, 'claim': None, 'journal': []}`.

## Reading and writing a work item file

Every file format the factory owns has one reader class and one writer class in `factory.adapters`, behind an interface in `factory.application`, and validates into Pydantic DTOs; no other module parses or renders that format. For the work item file the interfaces are `WorkItemReader` and `WorkItemWriter` (`factory.application.files`) and the classes are `FrontmatterWorkItemReader` and `FrontmatterWorkItemWriter` (`factory.adapters.work_item_markdown`). That module is the only one that imports `frontmatter` (python-frontmatter) or `ruamel.yaml`. Wiring uses the reader and not yet the writer: `factory.entry.wiring.build_work_item_reader` returns `FrontmatterWorkItemReader` for the check command, and nothing builds `FrontmatterWorkItemWriter` yet.

| Operation | Does |
|---|---|
| `reader.parse(text)` | `WorkItemDocument` with the state and the normalised body; the state is required |
| `reader.parse_specification(text)` | `WorkItemDocument` with `state=None`, the body, and `ignored_keys`: for a file whose front matter the factory does not own (a story in the backlog), so its own `stage` can never skip a stage |
| `reader.read(path)` | `parse` of the file read as UTF-8 |
| `writer.render(document)` | the file text |
| `writer.write(path, document)` | `render` written as UTF-8 with `\n` line ends, replacing an existing file |

### The layout

A file is a boundary line, the front matter, a boundary line and the body, split as python-frontmatter splits it. The reader first turns `\r\n` into `\n` and strips the whitespace around the whole text. A boundary line is three or more `-` and nothing else but whitespace (`---`, `----`, `--- `); `--- x`, `- - -` and an indented ` ---` are not. Front matter exists only when the text starts with a boundary line and a later line is one. Two `---` lines further down a body are thematic breaks, not front matter.

The writer always writes all ten keys of `WorkItemState`, in field order:

```yaml
---
stage: doing
blocked: question
round: 1
attempts: 2
crashes: 0
pull_request: 12
comments_read: [4, 9]
handed_over: approval
claim:
  instance: factory-1
  stage: doing
  started_at: '2026-10-13T09:00:00Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
- number: 2
  speaker: factory
  kind: started
---
```

The notation:

- A missing value is `null`, an empty list `[]`, a non-empty `comments_read` a flow list, `claim` is `claim: null` when absent, `journal` a block list of mappings.
- `started_at` is single-quoted UTC text in `isoformat()` form with the offset written as `Z`.
- A name a YAML reader could take for null or a boolean (`null`, `true`, `false`, `yes`, `no`, `on`, `off`, `y`, `n`) is single-quoted (`handed_over: 'true'`), so it reads back as the same text. Every other scalar is unquoted.

`RuamelYamlHandler` subclasses python-frontmatter's `YAMLHandler` and overrides only `load` (ruamel.yaml's safe loader, keys converted with `str`) and `export`. The reader calls the handler's `detect`, `split` and `load` itself (the split is the module function `split_front_matter(handler, text)`, which the agent definition reader calls too) rather than `frontmatter.loads`, which would take two later `---` lines for front matter, return an unclosed text whole, drop front matter that is not a mapping and refuse a key named `content`.

### The body

`render` writes `---`, the front matter, `---`, an empty line, the body stripped of the whitespace around it, and a final `\n`; an empty body ends the text at the closing `---` and `\n`. `parse` and `parse_specification` strip the body the same way and add one final newline; an empty or blank body is `""`. So `parse(render(document))` equals `document` when the body is normalised.

### Faults

`parse` raises `WorkItemFormatError` with a `fault` that is, or starts with, one of these. A `<path>` is the top-level key, then nested keys after dots, and a list position in brackets: `attempts`, `claim.extra`, `comments_read[0]`, `journal[1].kind`.

| Fault | When |
|---|---|
| `no front matter` | no opening boundary line, or front matter never closed |
| `front matter is not valid YAML` | the YAML does not load |
| `front matter is not a mapping` | it loads as a list or a scalar (empty, blank, comment-only or `null` front matter is an empty mapping) |
| `unknown key: <path>` | a key `WorkItemState`, `Claim` or `JournalRecord` does not define |
| `missing key: <path>` | `stage`, or a required key of a claim or journal record |
| `invalid <path>: <reason>` | a value the model refuses; the first in the order of the state's fields |
| `invalid state: <reason>` | every value is valid but a rule across keys is broken (the claim's stage differs from the state's) |

The agent files have their own reader and faults: see *The agent definition reader*. When several faults exist, the first in this order is reported: structure, unknown key, missing key, invalid value, rule across keys. `parse_specification` raises only `front matter is not valid YAML` and `front matter is not a mapping`; a text with no front matter is a body with no ignored keys. `read` raises `WorkItemFormatError` with `path` set to `str(path)`: `cannot read: <reason>` for a file that is missing or not UTF-8, otherwise the fault of `parse`. `render` raises `the document has no state` for a document whose `state` is `None`.

```bash
uv run python -c "
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.domain.errors import WorkItemFormatError
reader = FrontmatterWorkItemReader()
try:
    reader.parse('---\nstage: tests\ncolour: 2\n---\n# T\n')
except WorkItemFormatError as error:
    print(error.fault)
spec = reader.parse_specification('---\nstage: tests\nattempts: 1\n---\n\n\n# T\n')
print(spec.state, spec.ignored_keys, repr(spec.body))
"
```

prints `unknown key: colour` and then `None ['stage', 'attempts'] '# T\n'`.

## Cost records

One agent run is one cost record: a JSON line in the sidecar file beside the work item, `cost_records_path(path)` (`<work item>.costs.jsonl`, see *Identity, order and places of work items*). The classes cover the format only: `CostRecord` (`factory.domain.cost_records`), the interfaces `CostRecordReader` and `CostRecordWriter` (`factory.application.files`), and `JsonLinesCostRecordReader` and `JsonLinesCostRecordWriter` (`factory.adapters.cost_records_jsonl`). When a record is created, completed or discarded, and how a bill is summed, come later (F0005). Wiring does not use the classes yet.

A record has `run`, `work_item`, `stage`, `role`, `attempt`, `status` (`started` or `completed`), `started_at` (aware, stored in UTC), and the measures `duration_seconds`, `end_reason`, `turns`, `tokens` (`TokenCounts`), `cost_usd` and `image`. `CostRecord` is frozen and refuses unknown fields. `run` is 32 lowercase hexadecimal characters.

- A `started` record has no duration, end reason, turns, tokens or cost. A `completed` record has `duration_seconds` and `end_reason`; its `turns`, `tokens` and `cost_usd` may be unknown. The rule spans fields, so its error has no field location and `parse` reports it as `invalid record: <reason>`.
- A measure the runtime did not report is `null` in the file and `None` in the record, never 0 (a run the `time_limit` ended has `turns`, `tokens` and `cost_usd` unknown). A key that is absent when reading is `None` too.
- `duration_seconds` is at least 0 and finite. `cost_usd` is at least 0 and finite, and is a JSON **string** (`"0.3450"`), because a float would round it and a `Decimal` keeps its digits. A JSON number or boolean for `cost_usd` is `invalid cost_usd`.
- `ok` is true exactly when the status is `completed` and the end reason is `completed`.
- A `run` appears once in a file. A record is completed by replacing its `started` line with the `completed` one (read, replace the record, `write` the whole file), never by appending a second line for the run.

A line is one JSON object without spaces after `,` and `:`; keys are in field order, `tokens` in the order of `TokenCounts`, `started_at` ends in `Z`. The file is strict JSON: `NaN`, `Infinity` and `-Infinity` are `not valid JSON`. A completed line, then a started line:

```json
{"run":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","work_item":"F0002-S0007","stage":"tests","role":"tester","attempt":0,"status":"completed","started_at":"2026-10-12T00:00:00Z","duration_seconds":41.0,"end_reason":"completed","turns":7,"tokens":{"input":12,"output":3438,"cache_read":127336,"cache_creation":31343},"cost_usd":"0.3450","image":null}
{"run":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","work_item":"F0002-S0007","stage":"tests","role":"tester","attempt":0,"status":"started","started_at":"2026-10-12T00:00:00Z","duration_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":null}
```

| Operation | Does |
|---|---|
| `reader.parse(text)` | the records, in file order |
| `reader.read(path)` | `parse` of the file as UTF-8; `[]` when the file does not exist |
| `writer.render(records)` | one line per record, each ending in `\n`; `""` for none |
| `writer.write(path, records)` | `render` as UTF-8 with `\n` line ends, replacing the file whole |

`parse` ignores blank lines, which still count in line numbers. Of `run`, `work_item`, `stage`, `role`, `attempt`, `status` and `started_at`, each is required; the other keys may be absent. A fault is a `CostRecordFormatError(line, fault)` (a `FactoryError`; message `line <line>: <fault>`, both attributes), the line counted from 1, and the first fault ends the parse. The faults are `not valid JSON`, `not a JSON object`, `unknown key: <key>`, `missing key: <key>`, `invalid <key>: <reason>` and `invalid record: <reason>`; a key inside `tokens` is named after a dot (`tokens.output`). On one line they come in that order. Only a line with none of them can be `duplicate run: <run>`, the second line with a run seen before; `render` raises the same fault, with the line of the second record.

```bash
uv run python -c "
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader
from factory.domain.errors import CostRecordFormatError
try:
    JsonLinesCostRecordReader().parse('\n{not json}\n')
except CostRecordFormatError as error:
    print(error.line, error.fault, '|', error)
"
```

prints `2 not valid JSON | line 2: not valid JSON`.

## Sections of a Markdown body

`factory.domain.sections` is the one place that finds the title, the `## ` sections and the fenced code blocks of a Markdown body. It is pure: it works on text, and nothing reads a file. Every module that needs a heading or a fenced block uses it and does not look for `## ` itself.

Every index is an index into `split_lines(body)`, which splits at `"\n"` and drops an empty last element (`""` gives `[]`).

- A code block opens at a line that starts, after optional spaces or tabs, with three or more backticks or three or more tildes. It closes at the first later line that is the same character repeated at least as often, then nothing but whitespace. A shorter run, the other character or trailing text does not close it. A block never closed runs to the end and has `end=None`. A line starting with one or two backticks (inline code) opens nothing.
- A heading is a line outside every block that starts with `## ` at column 0. `### x`, an indented `## x`, `##x`, `##` and `# x` are not. A `Section` (`heading`, `start`, `end`) runs from its heading line to the next heading or the end; lines before the first heading belong to no section.
- The title is the stripped text of the first line outside every block that starts with `# ` at column 0, or `None`.
- A heading is matched by its exact text, case-sensitive, and the first section wins when it occurs twice. The code knows three names as constants: `ACCEPTANCE_CRITERIA` (`"Acceptance criteria"`), `SMOKE_TEST` (`"Smoke test"`) and `JOURNAL` (`"Journal"`). Every other section a story has comes from the project's own form: `required_sections(form)` is the headings of the form in order, so a section added to the form becomes required.

| Function | Returns |
|---|---|
| `code_blocks(lines)` | the `CodeBlock`s (`start`, `end`) |
| `opening_fence(line)` | the run of backticks or tildes the line opens a block with, without indentation or info string, or `None` when it opens none |
| `lines_outside_blocks(lines)` | the indices of the lines outside every block (a block's fence lines count as inside) |
| `title(body)` | the title or `None` |
| `sections(body)` | the `Section`s in order |
| `section_text(body, heading)` | the text under the heading without its heading line and without leading and trailing blank lines (`""` when empty), or `None` when no section has the heading |
| `insert_paragraph(body, heading, paragraph)` | the body with the paragraph first under the heading, a blank line on each side; it ends with a newline exactly when `body` did |
| `required_sections(form)` | the heading texts of the form |

`insert_paragraph` raises `WorkItemFormatError` with the fault `missing section: ## <heading>` when no section has the heading (a heading only inside a fence counts as missing) and `ValueError` for a blank paragraph. `Section` and `CodeBlock` are frozen, refuse unknown fields, and take indices of 0 or more.

```bash
uv run python -c "
from factory.domain.sections import insert_paragraph, section_text, sections, title
fence = chr(96) * 3
body = '# Story\n\n## Demo\n\n' + fence + 'bash\n## start the server\necho ok\n' + fence + '\nExpect: ok\n\n## Journal\n\n1. 2026-10-12 human: created.\n'
print(title(body))
print([s.heading for s in sections(body)])
print(repr(section_text(body, 'Demo')))
print(insert_paragraph(body, 'Journal', 'Note.').split('\n')[10:])
"
```

prints `Story`, then `['Demo', 'Journal']` (the `## start the server` line in the fence is not a heading), then the whole Demo section as one quoted string, fence included, then `['## Journal', '', 'Note.', '', '1. 2026-10-12 human: created.', '']`.

## The form check of a story

`factory.domain.story_form` checks the form of a story: `check_story_form(document, form, *, folder)` returns a list of `FormFinding` (`line`, `message`), one for each rule the story breaks, all of them and in the order below. `line` is a line of the body counted from 1, or `None` when the finding has no line. `FormFinding` is frozen, refuses unknown fields and takes a `line` of 1 or more. The function is pure: `document` is a `WorkItemDocument`, `form` is the text of the project's story form (`factory/story-form.md`) and `folder` is the `LifecycleFolder` the story is in.

The sections come from the project's form, not from the code: `required_sections(form)` is what a story must have, so a `## Notes` added to the form makes `Notes` required. The code knows only the names `Acceptance criteria`, `Smoke test` and `Journal`, and a rule about one of them does nothing when the body has no such section (rule 2 reports it when the form requires it). Code blocks are respected: a `## heading`, a `# comment` or a numbered line inside a fenced block is never a heading, a title or an item, so it can neither hide a section nor fake the title. An item is a line at column 0 that starts with digits and `". "`, and it runs to the line before the next item or to the end of the section.

| # | Rule | Message | Line |
|---|---|---|---|
| 1 | no line outside the code blocks starts with `# ` | `the story has no title line` | none |
| 2 | a heading of the form is not a section (one finding each, in the form's order) | `missing section: ## <heading>` | none |
| 3 | the criteria are not numbered 1, 2, 3 and so on (the first one that differs) | `criterion numbered <found> where <expected> is expected` | that item |
| 4 | with two criteria or more: the second-to-last lacks `make check` or `green`; the last does not start with `docs:` after its number | `the second-to-last criterion must contain "make check" and "green"`; `the last criterion must start with "docs:"` | that item |
| 5 | `Smoke test` has no code block; a block is not followed, after blank lines, by an `Expect:` line (or is never closed, or ends the section) | `the Smoke test has no code block`; `the code block opened at line <n> is not followed by an "Expect:" line` | the heading; the opening of the block |
| 6 | the journal entries are not numbered 1, 2, 3 and so on (the first one that differs) | `journal entry numbered <found> where <expected> is expected` | that entry |
| 7 | `backlog` and the document has front matter keys | `a backlog story carries no front matter: <keys joined by ", ">` | none |
| 8 | another folder and the document has no state | `the story has no state` | none |
| 9 | another folder and the state's `journal` has a different number of records than the text has entries | `the journal data lists <n> entries but the text shows <m>` | none |
| 10 | `backlog` and the `Journal` section has entries | `a backlog story carries no journal entries` | the first entry |

Fewer than two criteria get no closing finding, and no criteria or no entries is no finding of rules 3 and 6. Every code block of the smoke test is judged by itself. A block that is never closed runs to the end of the body, so it hides a later `## Journal`; that is the safer reading of a half-written story.

Rules 7 and 10 are the checks of the human's file in the backlog; rules 8 and 9 are for the factory's own calls on a document that belongs to a work item's branch. A backlog story's `Journal` section has no entries: the opening writes entry 1 into it, so an entry already there would make a second entry 1. A caller that holds only the specification of a started story (the text on `main` has no front matter) names the folder `backlog`, so that rules 8 and 9 are not asked of a document that cannot have a state.

```bash
uv run python -c "
from factory.domain.story_form import check_story_form
from factory.domain.work_item import WorkItemDocument
form = '# Form\n\n## Description\n\n## Acceptance criteria\n\n## Smoke test\n\n## Journal\n'
body = '# S\n\n## Description\n\nText.\n\n## Acceptance criteria\n\n1. It works.\n3. make check stays green.\n4. done.\n\n## Smoke test\n\nNo block here.\n'
for finding in check_story_form(WorkItemDocument(state=None, body=body), form, folder='backlog'):
    print(finding.line, finding.message)
"
```

prints four lines: `None missing section: ## Journal`, `10 criterion numbered 3 where 2 is expected`, `11 the last criterion must start with "docs:"` and `13 the Smoke test has no code block`.

### Where a story sits

`check_story_place(path, *, feature_file_exists)` in the same module returns the findings against where a story file sits. It is pure: `path` is a repository-relative path with `/`, and `feature_file_exists` is whether `factory/features/<directory>/feature.md` exists, which the caller looks up. The findings have no line.

| # | Rule | Message |
|---|---|---|
| 1 | the path is not exactly `factory/features/<feature directory>/<folder>/<file>`, with the folder one of `LIFECYCLE_FOLDERS` (`ongoing` is not one); this is the only finding then | `not a work item location: expected factory/features/<feature>/<backlog\|in-progress\|done>/<file>.md` |
| 2 | the file name is not a story file name (`F0000-S0000.md`, with or without a slug; an acceptance's name is not one) | `the file name "<name>" is not F0000-S0000[-slug].md` |
| 3 | the feature directory is not `F0000` or `F0000-<slug>` | `the feature directory "<directory>" is not F0000[-slug]` |
| 4 | both parse and their feature ids differ | `the story <story id> is in the directory of feature <feature id>` |
| 5 | `feature_file_exists` is false | `the feature file feature.md is missing in factory/features/<directory>` |

After rule 1 passes, rules 2 to 5 are independent and reported in that order. `lifecycle_folder_of_location(path)` returns the folder of a path that passes rule 1 and `None` otherwise; the command uses it to decide whether to read the file and with which reader.

### The check command

`factory.entry.check_story` is the command behind `factory-check-story`; `main(argv=None, *, root=None)` returns the exit status (0, 1 or 2) and the module runs as `python -m factory.entry.check_story`. It reaches the work item reader only through `factory.entry.wiring.build_work_item_reader()`, the one entry module that imports from `factory.adapters`; a test parses the imports to hold that. A backlog file is read with `parse_specification`. A file in `in-progress` or `done` is read with `parse`, and when the reader's fault is `no front matter` it is read again with `parse_specification` and checked as `backlog`: on `main` a started story is the human's moved file and its state lives on the work item's branch. Any other reader fault becomes the only form finding of that file. The operator guide describes the output.

## Stops, the clock and the factory log

`factory.domain.stops` holds `RepositoryStop` (scope, reason, detail, `at`) and `HealthStatus` (`stops`, `healthy`); both are frozen and refuse unknown fields. The rules (blank detail, scope against reason, naive `at`, one stop per reason) are in the operator guide's formats and are `ValidationError`s. `at` is converted to UTC by a validator.

`factory.application.machine` holds the abstract `Clock` (`now()`, aware and UTC), `FactoryLog` (`line(text)`) and `HealthStatusStore` (`read()`, `write(status)`). Their first implementations are `SystemClock` and `ManualClock(start)` (tests; `advance(by)`; a naive start is a `ValueError`) in `factory.adapters.clock`, `TimestampedFactoryLog(path, clock)` in `factory.adapters.factory_log` and `JsonHealthStatusFile(path)` in `factory.adapters.health_file`. In tests use the `clock` fixture (a `ManualClock` at 2026-10-12 12:00 UTC).

`StopService(boundaries)` (`factory.application.stops`) raises and clears the stops of the repository or the machine; those never reach a pull request. `post(stop)` is the other kind: it puts a `WorkItemStop` (`key`, `branch` equal to `branch_name(key.work_item)`, `title`, `pull_request` or `None`, `text`; `branch`, `title` and `text` not blank) on the work item's pull request and returns `StopPosted(pull_request, opened, outcome)`. See the operator guide, "Stops of one work item", and the decision log for the rules. `raise_stop(stop)` writes the line `stop <scope> <reason>: <detail>` through `boundaries.log`, then writes the health status with the stop in it (a known reason is replaced where it stood, a new one appended). Each write is tried even if the other fails, and the first `OSError` is raised afterwards, the log's when both fail. `clear_stop(reason)` does nothing when the status holds no stop of that reason; otherwise it writes the status without it first and then the line `stop cleared <reason>`, so a failed health write leaves the stop in force and says nothing. The replace-or-append rule is private to `stops.py`. The operator guide describes the lines.

### Boundaries

`Boundaries` (`factory.application.boundaries`) is the frozen dataclass of the interfaces that wiring hands to services: `git`, `hosting`, `agent_runtime`, `project_commands`, `work_item_reader`, `work_item_writer`, `cost_reader`, `cost_writer`, `pipeline_reader`, `agent_definitions`, `clock`, `log`, `health`, and `checkout` (the checkout root, a `Path`). It is not a DTO. It takes keyword arguments only, so a positional call is a `TypeError`, and assigning to a field raises `FrozenInstanceError`. A later story that needs another interface adds a field. Building the concrete adapters is `factory.entry.wiring`'s; it does not do so yet.

In tests use the `boundaries` fixture in `tests/conftest.py`: the real git wrapper, project commands, readers, writers, `TimestampedFactoryLog` at `<tmp_path>/state/factory.log` and `JsonHealthStatusFile` at `<tmp_path>/state/health.json`, with the fakes for the hosting service and the agent runtime and the `clock` fixture. A test that needs other parts uses `dataclasses.replace(boundaries, health=...)` and never calls `Boundaries(...)`, so a story that adds a required field changes only the fixture. Only the test of the keyword-only rule calls it directly, through a variable typed `Callable[..., Boundaries]` (a positional call is a `mypy --strict` error); the test of the frozen rule assigns with `setattr` and the field's name in a variable. An unwritable destination is a `JsonHealthStatusFile` or `TimestampedFactoryLog` whose path lies below a regular file; read standard output with `capsys`.

## The claim service

`factory.application.claims.ClaimService(boundaries, instance, definition)` makes the first half of a claim: the stage-start commit. `instance` is the factory instance's name and must match `[a-z][a-z0-9-]*`, otherwise the constructor raises `ValueError`. `definition` is the `PipelineDefinition` the caller loaded (normally from `origin/main`); the lease is copied from it.

`claim(branch, path, document, stage)` returns a `StageStart(commit, claim)`. It does this, in order:

1. Checks the preconditions and writes nothing if one fails (`ValueError`): the document has a state; `stage` is the state's stage; `stage` is in the definition and has a role; `branch` is `branch_name` of the id in the file name of `path`, so a claim is made only on the work item's own branch; the checkout is on `branch`.
2. Builds the `Claim`: the instance's name, the stage, the start time from `boundaries.clock` (UTC) and the `lease_duration` of the stage's role, copied now. A claim already in the document is replaced.
3. Sets `state.claim` and appends one journal entry (speaker `factory`, kind `started`, text `started <stage> as <instance>.`, see `started_text`). Nothing else in the document changes.
4. Writes the work item at `boundaries.checkout / path` and commits with the subject `<stage> starts as <instance>`.
5. Pushes `branch`. Any outcome other than `"pushed"` raises `PushFailed`.

**The push is the claim.** Whoever pushes first owns the stage. A rejected or unreachable push is no claim: the remote is unchanged, and the caller starts no agent run. The local commit stays on the local branch; the next tick's restore brings the branch back to the remote. `InjectedKill` at `BEFORE_PUSH` is not caught.

**The stage-start commit is the last commit before the agent run.** The commit stages every change in the work tree, so whatever the caller left uncommitted is part of it; for a new branch that is the work item's opening. The commit is therefore the baseline for what the agent may write and for undoing it.

**Status.** `status(state)` returns a `ClaimStatus` (`factory.domain.lease`): `"none"` (no claim), `"own"` (the claim's `instance` is the service's, whatever its age, so a restarted instance with the same name reruns its stage at once, R20), `"held"` (another instance's claim, lease still running) or `"expired"` (another instance's, lease run out). It uses `boundaries.clock.now()` and the claim's own `lease_duration`, never the definition's, so a later change of the definition does not shorten a running claim (R21).

**The lease clock.** `lease_age(claim, now)` is `now - claim.started_at` (negative under clock skew); `lease_expired(claim, now)` is true when the age is at least `claim.lease_duration` minutes, and a negative age is never expired. Both are pure: `now` is passed in.

**Release.** `release(document)` returns the document with `state.claim` set to `None`, for the stage's result commit. Journal, other state fields and body are unchanged and no entry is appended. A document without a claim comes back equal; one without a state raises `ValueError`.

**`ClaimService` is the only module that builds or judges claims.** Only `factory.application.claims` imports `claim_status`, `lease_expired` or `lease_age`, and only it calls `Claim(...)`; `tests/test_claim_ownership.py` searches the source with `ast` and fails otherwise. Code that needs to know a claim's standing asks the service.

In tests, set the work item up on its branch before `claim` (a state, a journal entry and a `## Journal` section, or `append_entry` raises `WorkItemFormatError`); see `tests/application/test_claims.py`.

## The pipeline definition

The project's `factory/pipeline.yml` is read by `RuamelPipelineDefinitionReader.parse(text)` (`factory.adapters.pipeline_yaml`, the `PipelineDefinitionReader` interface in `factory.application.files`, `Boundaries.pipeline_reader`) into a `PipelineDefinition` (`factory.domain.pipeline_definition`). The reader is the only one of this format and nothing writes it. The text is loaded in ruamel.yaml's safe mode, so only plain data is built and a key repeated in one mapping is refused. `PIPELINE_YAML` in `tests/git_support.py` is the example definition.

| Key | Meaning | Default |
|---|---|---|
| `contract` | the contract version, a quoted text such as `'1.0'`; an unquoted `1.0` is a number and is refused | required |
| `stages` | name to `StageDefinition`; the order in the file is the pipeline's order | required |
| `roles` | name to `RoleDefinition`; a role's name is its agent definition's name | required |
| `project_commands` | name to `ProjectCommandDefinition` | `check`, `lint` and `test`, each with `time_limit` 10 |
| `attempts_cap` | attempts before the human is asked | 2 |
| `crash_cap` | crashes before the human is asked | 2 |
| `acceptance_stage` | the stage of the feature acceptance | none |

A stage has `role` (none: no agent runs there), `next` (`next[0]` is the forward move), `approval` (the human decides), `checks` (project commands run after the agent), `reports` (project commands run after green, recorded only) and `round_cap` (none: no cap). A role has `write_paths` (required; `{work_item}` is the work item's own file and `{feature}` its feature directory, the constants `WORK_ITEM_PLACEHOLDER` and `FEATURE_PLACEHOLDER`), `lease_duration` (60 minutes) and `time_limit` (40 minutes, the agent run's). A project command has `time_limit` (10 minutes). Every limit is a positive integer; stage, role and command names match `^[a-z][a-z0-9-]*$`.

- Values are taken only in their YAML type (strict mode): a limit is a YAML integer, so `true`, `'30'` and `30.0` are refused; `approval` is `true` or `false`, so `'yes'`, `'off'`, `1` and `0` are refused; names, `contract`, `checks`, `reports` and write paths are strings. A write path must hold at least one character that is not whitespace (`''` and `'  '` are refused at `roles.<role>.write_paths[<n>]`, with pydantic's message `String should match pattern '\S'`).
- A key with a default may be left out and takes it. A stage with nothing to say is written `done: {}`; `done:` alone is null and is refused (`invalid stages.done: ...`).
- Unknown keys are refused at every level, so a misspelt key is never ignored.
- A given `project_commands` replaces the default set as a whole; it does not merge. `lint: {}` takes `time_limit` 10.
- A name that breaks the pattern is reported at the path of its key: `invalid stages.<name>.[key]: ...`, likewise `roles.<name>.[key]` and `project_commands.<name>.[key]`.
- The methods: `first_stage()`, `role_of(stage)` (`None` for a stage without a role, `KeyError` for an unknown stage) and `position(stage)` (index in `stages`; `ValueError` for an unknown one, not specified).
- The rules that look across keys run at load, see "The rules of the definition" below. `first_stage()` is safe on a loaded definition, because rule 3 requires the stage `done`.

### Faults

`parse` raises only `PipelineDefinitionInvalid(fault)` (a `FactoryError`; the message is the fault). The faults are `not valid YAML: <problem>` (the repeated key is named in the problem; ruamel's problem text can span several lines), `the pipeline definition must be a mapping` (a list, a string or an empty text) and the spellings of `all_faults` in `factory.adapters.validation_faults`, the same module the work item reader uses: `unknown key: <path>`, `missing key: <path>` and `invalid <path>: <message>`. A `<path>` has dots between keys and `[n]` for a list position (`roles.coder.write_paths`). A text with several faults is refused once, with all of them joined by `; ` in the order unknown key, missing key, invalid value (`unknown key: x; missing key: contract`). The rules below run only when every field is valid, so the field faults come first and alone.

### The rules of the definition

`PipelineDefinition` has one validator that applies eleven rules, so every reader and every ref gets them. It collects the faults of all rules and refuses once, with the faults joined by `; ` in the order of the rules and, inside a rule, in the order of the stages or roles in the text. The reader reports the validator's message as the `fault`, without pydantic's `Value error, ` prefix.

**The contract.** `contract` is `<digits>.<digits>`. The major, compared as an integer, must be `CONTRACT_MAJOR` (1): `01.0` is read, `2.0`, `0.9` and `10.0` are not. Any minor is read (`1.0`, `1.7`, `1.10`).

**The lease.** For each stage with a role, the role's `time_limit` plus the `time_limit` of each command in the stage's `checks` and each in its `reports` must be at most the role's `lease_duration`. A command listed twice counts twice; a name that is no project command counts nothing; a stage without a role (an approval, `done`) is not measured. A role used by two stages is measured at each. With the defaults, 40 + 10 (one check) + 10 (one report) = 60 fits the lease of 60; a stage with two checks and a report adds up to 70 and does not.

The faults, in the order of the rules (`<s>` a stage, `<t>` a stage name, `<r>` a role, `<c>` a project command):

| Rule | Fault |
|---|---|
| 1 | `contract must look like <major>.<minor>, got '<contract>'` |
| 2 | `contract major <major> is not supported (this factory reads major 1)`, `<major>` as written |
| 3 | `stages must hold a stage named done`; `stage done must have no role and no next` |
| 4 | `stage <s>: next names unknown stage <t>`, once for each unknown name |
| 5 | in this order: `stage <s>: role <r> is not defined in roles`; `role <r>: write_paths is empty`; `stage <s>: an approval stage has no role` |
| 6 | `stage name <n> is reserved`; `role name <n> is reserved` (`human`, `factory`, `question`) |
| 7 | `stage <s>: check <c> is not a project command`; `stage <s>: report <c> is not a project command` |
| 8 | `role <r> at stage <s>: <total> min exceed lease_duration <lease> min` |
| 9 | `acceptance_stage <t> is not a stage with a role` |
| 10 | `stage <s>: next is empty` |
| 11 | `stage <s>: has neither a role nor approval` |

Rules 10 and 11 apply to every stage except `done`, and only when the stage `done` exists. Without it the end of the pipeline is unknown, and rule 3's fault is the one that matters. A stage with an empty `next` has nowhere to send a forward outcome or an approval; a stage with neither a role nor `approval: true` runs no agent and waits for no human. Rule 10's faults come before rule 11's, each in the order of the stages. A stage no `next` names (such as `acceptance`) is accepted: there is no rule on reachability.

Tests: `tests/adapters/test_pipeline_rules.py` (through the reader, comparing `fault`) and `tests/application/test_pipeline_loading_rules.py` (each refusal is one reported stop).

```bash
uv run python -c "
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
TEXT = '''contract: '1.0'
roles:
  coder: {write_paths: ['src/*']}
stages:
  doing: {role: coder, next: [done]}
  done: {}
'''
definition = RuamelPipelineDefinitionReader().parse(TEXT)
print(definition.first_stage(), definition.roles['coder'].lease_duration, sorted(definition.project_commands))
try:
    RuamelPipelineDefinitionReader().parse(TEXT.replace('contract', 'contrakt'))
except PipelineDefinitionInvalid as error:
    print(error.fault)
"
```

prints `doing 60 ['check', 'lint', 'test']` and then `unknown key: contrakt; missing key: contract`.

### The pipeline loader

`PipelineLoader(boundaries).load(ref=PIPELINE_REF)` (`factory.application.pipeline_loading`; `PIPELINE_REF` is `origin/main`) is the one place that loads the definition. It reads `PIPELINE_DEFINITION_FILE` at `ref` with `git.show_file` (never the work tree), parses it with `pipeline_reader`, and only when the text is valid checks with `agent_definitions.names()` that every role has an agent. Every refusal is `PipelineDefinitionInvalid(fault)`; the faults are listed in the operator guide, "The stop `pipeline_definition_invalid`", and the rules in "The rules of the definition" above.

- Only the loader raises and clears the stop `pipeline_definition_invalid`; no caller does. At `PIPELINE_REF` a refusal calls `StopService.raise_stop` before it raises, and a success calls `clear_stop` before it returns.
- A load at any other ref raises the same refusal but raises and clears no stop, so a read of a branch never changes the health status. A reader of the definition at another commit (F0004's write paths) will parse it directly with `pipeline_reader` and not go through the loader.
- A `GitError` propagates and raises no stop. An `OSError` of the stop's writes propagates in place of `PipelineDefinitionInvalid`.
- Tests: `tests/application/test_pipeline_loading.py`, with `human.push_file` and `checkout.fetch()` for other versions of the file and `install_agents(agent_home, roles)` in `tests/git_support.py` for the agent files.

## The agent definition reader

Every role of the pipeline definition needs an agent file of the same name, `<agent home>/agents/<name>.md`. `AgentDefinitionReader` (`factory.application.agent_runtime`, an abstract base class, `Boundaries.agent_definitions`) has two operations and `FrontmatterAgentDefinitionReader(agent_home)` (`factory.adapters.agent_files`) implements them. F0005 uses `read` to compose every task; `PipelineLoader` uses `names()` to check the roles.

| Operation | Does |
|---|---|
| `names()` | the sorted stems of the regular `.md` files directly in `agents/` whose stem is a `Name`; `[]` for an empty directory |
| `read(name)` | the `AgentDefinition` of the file; `name` is checked as a `Name` before any path is built |

The front matter is split as the work item reader splits it, with `split_front_matter`, and loaded with ruamel.yaml through `RuamelYamlHandler`, never PyYAML (so `model: on` is the text `on`). The body, stripped, is `instructions`. Only `model`, `tools`, `effort` and `budget_usd` are validated into `AgentDefinition`; other keys are left aside. `budget_usd` becomes a `Decimal` (`0.1` gives `Decimal("0.1")`). No variable in the module is named `yaml`, because the semgrep rule `factory-no-unsafe-yaml-load` matches any `yaml.load(...)`.

### Faults

`AgentDefinitionError(name, fault)` is a `FactoryError`. `names()` raises it with `name == ""` and `no agents directory at <path>`. `read` raises a subclass:

| Error | Fault |
|---|---|
| `AgentDefinitionMissing` | `not an agent name: <name>`, `no agent file <path>` |
| `AgentDefinitionInvalid` (`key` is `""`) | `cannot read: <reason>`, `no front matter`, `front matter is not valid YAML`, `front matter is not a mapping` |
| `AgentDefinitionInvalid` (`key` is the top-level key) | `missing key: <key>`, `budget_usd must be greater than 0`, `invalid <path>: <message>` |

Of several validation faults the first in the order of `first_fault` is reported (unknown key, missing key, invalid value); `first_error` in `factory.adapters.validation_faults` gives the error `first_fault` formats, so the `key` and the fault name the same problem. F0010-S0006 extends `AgentDefinitionInvalid` to refuse keys the runtime does not apply.

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.domain.errors import AgentDefinitionInvalid
home = Path(tempfile.mkdtemp())
(home / 'agents').mkdir()
(home / 'agents' / 'coder.md').write_text('---\nmodel: sonnet\ntools: Read\nbudget_usd: 1\n---\nGo.\n')
reader = FrontmatterAgentDefinitionReader(home)
print(reader.names())
try:
    reader.read('coder')
except AgentDefinitionInvalid as error:
    print(error.key, '|', error.fault)
"
```

prints `['coder']` and then a line that starts with `tools | invalid tools:`.

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
