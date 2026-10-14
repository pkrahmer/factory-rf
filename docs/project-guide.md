# Project guide

The guide for agents working on `factory-rf`: how the code is laid out, where a change belongs, which conventions the checks do not catch, and what to read first. It grows with each story: the documenter stage fills it in from the stories' docs criteria. `CLAUDE.md` holds the rules every change follows.

## Errors

`factory.domain.errors.FactoryError` is the root of every error the factory raises on purpose. Later stories add their error types under it. `InjectedKill` (below) is deliberately not one.

`BoundaryError` (a `FactoryError`) is the root of the errors for an outside party that failed. `HostingServiceError(operation, detail)` is its first subtype: every implementation of the hosting-service interface raises it for every failing call, and its message is `hosting service <operation> failed: <detail>`. `operation` and `detail` are attributes.

`GitError(command, exit_status, output_tail)` is its second subtype, for the git wrapper. `command` is `git ` and the arguments (`git fetch --prune origin`); `exit_status` is `None` when git could not be started or hit its time limit; `output_tail` is the last 30 lines of the output, stdout and stderr merged (all of it when shorter). The message is `<command> failed (exit <status>): <tail>`, or `failed (no exit status)` when the status is `None`. `FetchFailed` is a `GitError` that `fetch` raises for every failure. `NothingToCommit` is a `GitError` that `commit` raises when nothing is staged.

`ProjectCommandError(command, detail)` is its third subtype, for the project commands: it is raised only when a command cannot be started (an invalid name, or an executable the operating system cannot start). The message is `project command <command> failed: <detail>`; `command` and `detail` are attributes. A red command is a result, not this error.

`AgentRuntimeError(detail)` is its fourth subtype, for the agent runtime. The message is `agent runtime failed: <detail>`; `detail` is an attribute. A run that dies, hits its `time_limit` or runs out of budget is a result, not this error (see *The agent runtime*).

`PushFailed(branch, outcome)` is a `FactoryError` for a push that did not reach the remote; `outcome` is the git wrapper's `PushOutcome` other than `"pushed"` (`rejected`, `unreachable`), and the message names the branch and the outcome. The claim service raises it (see *The claim service*).

`CannotHandle(kind, reason)` is a `FactoryError` that a handler raises when it cannot do its work, so the dispatcher counts it as an error; `kind` is the event's kind, and the message is `cannot handle <kind>: <reason>`.

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

Every post the factory makes ends with two lines: the marker `<!-- factory -->` and a key comment `<!-- factory key=<work item>:<kind>:<n> -->`, for example `<!-- factory key=F0001-S0001:question:7 -->`. `n` is lowercase hex and not empty; the key is made from the recorded journal entry's number, so a repeat or a restart posts nothing (see "Asking the human"); `kind` is one of `question`, `attempts_cap`, `round_cap`, `crash_cap`, `send_back`, `stall`, `expiry`, `correction`, `error`, `cost_table`.

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
- With a guard only: `guard-<session>.json` (the `GuardSettings` as JSON) and `hooks-<session>.json`, a `PreToolUse` hook on `Edit|Write` whose command is `factory-guard --settings <guard file, shell-quoted>`. The command is described in "The guard command".

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

### The remote's work items

`WorkItemSnapshot` and `StoryFile` (`factory.domain.work_item`, frozen, no unknown keys) are what the remote shows. `StoryFile(id, path, feature_directory, file_name, folder)` is one story file on `origin/main`. `WorkItemSnapshot(id, path, folder, branch, branch_commit, document)` is one work item: `branch` is `branch_name(id)`, `branch_commit` the head of `origin/<branch>` or `None` when the branch does not exist, and `document` the state and body.

`RemoteWorkItems(git, reader)` (`factory.application.work_items`) reads only remote-tracking refs through `Git.list_files`, `resolve` and `show_file`; never a local branch and never the work tree. It does not fetch: the caller does, first.

- `list_stories(folder)` lists the story files of one lifecycle folder on `origin/main`, in `work_item_order`, then path. A story file is a path for which `folder_of` is not `None`, whose file name's feature id equals its directory's, and whose id is not an acceptance. Anything else (`.gitkeep`, `feature.md`, deeper files, `ongoing/`, `drafts/`) is ignored.
- `read(definition)` returns one snapshot per story file in `in-progress/`, in the same order; two files with one id give two snapshots. `backlog/` and `done/` are never read.
- With a branch, the document is `reader.parse` of the story file at `origin/work-item/<id>`, even when that branch is an ancestor of `origin/main` (see `docs/decisions.md`). A stale local branch of the same name has no influence.
- Without a branch, the story has just been started by the human's move into `in-progress/`: its document is `initial_state(definition.first_stage())` with the body and `ignored_keys` of `parse_specification` on `origin/main`. State fields in that file (`stage`, `attempts`, ...) are not applied; they are listed in `ignored_keys`.
- A story file missing at its branch tip, or a text the reader refuses on the branch or on `origin/main`, raises `WorkItemFormatError` with `path` set to the story's path. `GitError` from `Git` passes through.

## The evaluation

The watcher turns what the remote shows into one `Event`. The evaluation keeps no memory: the same facts give the same event, so a `run` event the dispatcher has capped is still the first one on the next evaluation.

`Watcher(boundaries, instance).evaluate(definition)` (`factory.application.watcher`) reads `origin/main`'s head and `RemoteWorkItems.read(definition)`, builds an `EvaluationInput(definition, snapshots, main_commit, illegal_changes)` (the illegal changes come from the move rule, below) and calls the pure `evaluate(facts, lookup, claim_status)` (`factory.domain.evaluation`). Like `RemoteWorkItems`, it does not fetch; the caller does, first. `GitError` passes through, also when `origin/main` does not resolve (its message names `origin/main`), and so does `WorkItemFormatError`. The `lookup` it hands over calls `get_pull_request`, and `list_comments` only while the pull request is open. `claim_status` is `ClaimService(...).status`.

### The event

`Event` (`factory.domain.events`, frozen, no unknown keys) has `kind`, `work_item` (a `WorkItemSnapshot`), `pull_request` (the view of the one lookup, when it succeeded), `feature`, `remote_state` and `detail`. `detail` is for display; no code reads it back. `key` is `<kind>:<work item id>`, else `<kind>:<feature id>`, else `<kind>:-`.

`idle` and `acceptance_due` take no work item; every other kind needs one. `feature` is set for `acceptance_due` and only for it. A violation raises `ValidationError`. `remote_state` is the snapshot's `branch_commit`, else the head of `origin/main`; an event with no work item carries `origin/main`'s head.

The kinds: `run`, `comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `crash`, `expired`, `duplicate`, `pull_request_lookup`, `acceptance_due`, `idle`. `evaluate` makes all of them except `acceptance_due` (F0009). `reject` is an illegal stage change (see *The move rule*); handling it, the move back, belongs to F0007-S0006. Handlers are registered only for `idle` and `run` so far (`AskHandler` is built but not yet registered); the others belong to later features.

### The four tiers

The first tier that matches decides.

1. **Integrity.** Two snapshots with one id: `duplicate` for the first such id in id order, carrying the first snapshot; `detail` is `<id> at <path> and <path>`.
   - Then, after the validation below and the pull request lookup, `reject`: see *The move rule*. It comes before everything else in tier 2 and below.
2. **The human.** Only the first work item that waits, in id order, is looked at. A work item waits when `blocked` is set or its stage is an approval stage.
   - No pull request: `ask` (`no pull request`), without a lookup.
   - The lookup raises `HostingServiceError`: `pull_request_lookup`, with the error's text.
   - Merged: `merged`. Closed: `closed`.
   - Open, at an approval stage and not yet `handed_over` for it: `hand_over`.
   - Open, with a comment that is not the factory's and whose id is not in `comments_read`: `comment` (`<n> new comments`).
   - Open, blocked, and no factory post answers the latest `question` record in the journal: `ask`. A later record of another kind does not change which question is the latest.
   - Otherwise `idle`, its `detail` naming the work item, and nothing below tier 2 is reached.
3. **The agent at work.** The first work item with a claim decides by `claim_status`: `own` is `crash`, `expired` is `expired`, `held` is `idle` (the `detail` names the work item and the instance).
4. **New work.** The first work item, in id order, whose stage has a role and which does not wait: `run`, or `ask` (`attempts cap`) when `attempts` has reached `attempts_cap`. A stage without a role (`done`) is skipped.

Nothing matched: `idle` at `origin/main`'s head.

Three rules follow. A waiting work item holds back all new work, so one never starts while another waits for the human; and while a claim is held, nothing else runs, so only one agent runs at a time. At most one pull request lookup is made per evaluation, so an idle tick costs at most one.

`evaluate` first checks every snapshot against the definition, after tier 1 and before any lookup: a work item with no state raises `ValueError("work item <id> has no state")`, and one in a stage the definition lacks raises `ValueError("work item <id>: stage <stage> is not in the pipeline definition")`. An unknown stage therefore never reaches the definition's accessors.

### The move rule

A stage changes only through the pipeline. `factory.domain.move_rule` holds the rule; every model in it is frozen and forbids unknown keys.

- `StageChange(from_stage, to_stage, correction=False)`: a change read from git. `correction` is true when the same commit appended a journal record of kind `move_back`. The factory's own correction is marked by that journal kind, never by a commit message.
- `is_legal_change(definition, change)` is true when `correction` is set, when the stage is unchanged, when `to_stage` is in `from_stage`'s `next`, or when `to_stage` is `done` and `from_stage` is an approval stage (the human's merge accepts, even when that stage's `next` does not list `done`). A stage the definition lacks is never a legal side.
- `factory_moves(definition)` lists every `FactoryMove(from_stage, to_stage)` the factory may make: every name in every stage's `next`, in stage order, then each approval stage to `done`, no pair twice. All of them are legal under `is_legal_change`. A handler that moves a work item must take its target from the definition, or this proof does not hold.

`RemoteWorkItems.last_stage_change(snapshot)` reads the change from git: `Git.log("origin/<branch>", since="origin/main", path=<story file>)`, so only commits not reachable from `origin/main` count, and the newest of them, `C`, decides. Only the last commit that touched the file is judged; an older illegal change that a later commit buried is not seen. The result is `None` when:

- the snapshot has no branch, or the log is empty;
- `C` is a merge commit (more than one parent);
- `C` is the opening commit: its parent is reachable from `origin/main` (the text the human started, which may say any stage);
- the file does not exist at `C` (deleted) or at its parent (added), or the parent's text cannot be parsed;
- the stage is the same at `C` and at its parent.

Otherwise it is a `StageChange`; `correction` is true only when `C`'s journal is longer than the parent's and its last record has kind `move_back`.

`Watcher.evaluate` fills `illegal_changes` with an `IllegalChange(work_item, change)` for each snapshot, in snapshot order, whose change is not legal.

**The pull request is read first.** After a merge by any method (merge commit, squash, rebase) the branch's commits may still be beyond `origin/main` and show a stage change nobody made by hand. So `evaluate` makes its one lookup (for the first waiting work item `W`, exactly when it did before) before it decides on `reject`. It returns `reject` for the first illegal change in snapshot order, with `remote_state` the snapshot's `branch_commit` and `detail` `stage changed from <from> to <to>, which the pipeline definition does not allow`. It skips the change of `W` only when the lookup returned a merged pull request; the next illegal change, if any, is then considered. A failed lookup skips nothing. The lookup is made at most once and not at all when no work item waits.

`waiting(state, definition)` and `question_posted(snapshot, comments)` are public in `factory.domain.evaluation` for the handlers that come later.

### The watcher's command line

`factory.entry.watch` (`factory-watch`, see the operator guide) shows the event of one evaluation and the board. `run_watch(boundaries, instance, out, err)` resolves `origin/main` (`GitError` when it does not), loads the definition with `PipelineLoader(boundaries).load(<that commit>)` (a commit id, not the ref, so no stop is raised or cleared), evaluates once with `Watcher` and writes `render_event(event)`, a blank line and `render_board(...)`. It returns 0, or 1 with `factory-watch: <fault>` on `err` for `PipelineDefinitionInvalid`. It fetches and writes nothing. `main(argv, *, boundaries, instance, out, err)` parses `argv` first with an `ArgumentParser(prog="factory-watch")` without options, so `--follow` or any other option is `SystemExit(2)`; with no boundaries or instance it writes `factory-watch: no instance settings are wired yet` and returns 2 (F0010-S0001 replaces that with the production wiring).

The board is `factory.domain.board` (`BoardRow`, `FeatureRow`, `work_item_row`, `feature_rows`, `render_board`, all pure) and `BoardReader(boundaries).read(definition)` in `factory.application.board`, which returns a `BoardView`. The reader takes the story files of the three folders from `RemoteWorkItems.list_stories`, the feature titles from `Git.show_file("origin/main", ".../feature.md")` and the rows from `RemoteWorkItems.read`. It reads the remote-tracking refs a second time next to the `Watcher`; it does not share the watcher's snapshots, so `Watcher.evaluate` still returns one event. `FeatureRow.acceptance` is always `None` until F0009-S0001.

## The tick

`Tick(boundaries, instance, handlers, status=None).run()` (`factory.application.tick`) is one pass, in this order. The order matters: the remote is the only truth, so nothing is read before the fetch.

1. **Fetch** (`Git.fetch`). `FetchFailed` raises the repository stop `fetch_failed` (detail: the error's text) and ends the tick; success clears it.
2. **Load** the pipeline definition with `PipelineLoader` from `origin/main`. `PipelineDefinitionInvalid` ends the tick; the loader raised the stop `pipeline_definition_invalid` and clears it on a later success, the tick does neither.
3. **Restore** the checkout: one line `discarded uncommitted changes: <path>, <path>` (the paths in the order of `Git.status()`) when there are changes, then `reset_to("HEAD")`, `checkout("main", start_point="origin/main")`, and `delete_branch` for every `work-item/<id>` of an id that has `origin/work-item/<id>` or a story in `in-progress/` on `origin/main`. Other local branches stay. A `GitError` here raises the stop `checkout_restore_failed` and ends the tick; success clears it.
4. **Evaluate** with `Watcher(boundaries, instance).evaluate(definition)`.
5. **Dispatch**: `handlers(definition)` is built now, because the handlers take the loaded definition, and a `Dispatcher` with the tick's status handles the event. The tick keeps the dispatcher's status for the next run.

`run` returns `TickOutcome(stopped=..., event=..., dispatch=...)`: `stopped` is set and the others are `None` when the tick ended at a stop. `WorkItemFormatError`, `ValueError` from the evaluation and a `GitError` outside the fetch and the restore are not caught; no stop exists for them. The tick reads and writes no run record and no lock. `IdleHandler` does nothing and is the handler of `idle`.

Because the checkout is rebuilt every tick and no local state is read, a rejected push leaves no trace: the next tick judges the remote. The dispatcher's count of errors per event and remote state is the only memory, and it is in the `TickStatus`. A push to the work item's branch changes the remote state and so retries a capped event. `HandlerFactory` is `Callable[[PipelineDefinition], Mapping[EventKind, Handler]]`; the production factory is `handler_factory` (see "The handlers of the events").

## The handlers of the events

`factory.entry.wiring.build_handlers(boundaries, definition, instance, environment)` is the one place that registers a handler (R5, nothing else wires); production code never builds a `Dispatcher` from a hand-written mapping. It returns `{"idle": IdleHandler(), "run": RunHandler(boundaries, instance, definition, environment)}`. `handler_factory(boundaries, instance, environment)` returns the `HandlerFactory` the tick takes: a function of the loaded definition that calls `build_handlers`, so the handlers always hold the definition the tick has just loaded. No command builds a `Tick` yet; `factory-run` will.

`NOT_YET_HANDLED` is a tuple of the event kinds that have no handler in `build_handlers`, in the order of `EventKind`: `comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `crash`, `expired`, `duplicate`, `pull_request_lookup`, `acceptance_due`. It and the keys of `build_handlers`' result partition `EventKind`. A story that registers a handler adds it to `build_handlers` and removes its kinds from `NOT_YET_HANDLED`. Until then the dispatcher counts an event of such a kind as an error (`UnhandledEvent: no handler for event kind <kind>`), never silence.

`RunHandler(boundaries, instance, definition, environment)` (`factory.application.handlers.run`) turns a `run` event into one stage: it builds `StageRunner(boundaries, instance, definition, environment)` and calls `run(work_item.id, work_item.path)`. Any other kind is a `ValueError`. The `StageReport` is dropped, because a stall is already recorded by the stage; whatever `StageRunner.run` raises (a `HostingServiceError`, for example) propagates and is a counted error of the dispatcher. The handler adds nothing to the environment and takes nothing from it.

### Asking the human

`AskHandler(boundaries, definition)` (`factory.application.handlers.questions`) handles `ask`. A question is recorded before it is posted, and every post carries `PostKey(work_item, <the blocked value>, str(<the question record's number>))`. The handler never checks whether it already posted: `HostingService.post_comment` treats a key the pull request holds as a no-op, so a repeat or a restart posts nothing twice.

- `handle` takes `target_of(event)` and `require_pull_request(target, "ask")` (no pull request: `CannotHandle`).
- `blocked` set: the question is the latest `question` record (`last_record`), whatever records follow it (the human's comments are recorded after a question that waits to be posted). The text is `<speaker>: <entry_text>`. No commit is made. A `blocked` value with no `question` record is `CannotHandle`. This covers the agent's question, `round_cap`, `send_back` and `crash_cap`, which other code records.
- `blocked` unset and `attempts >= definition.attempts_cap`: the handler records, then posts. It checks out the branch with `WorkItemRecorder`, takes the text of the latest `stall` entry (none: `CannotHandle`, nothing recorded), appends a `factory` `question` entry with `attempts_cap_question(stage, attempts, last_stall)` (`factory.domain.post_texts`), sets `blocked="attempts_cap"` and records with the subject `work item <id>: attempts cap question recorded`. Then it posts the new entry with kind `attempts_cap`.
- `blocked` unset below the cap: `CannotHandle`.
- Failures (`HostingServiceError`, `GitError`, `PushFailed`) propagate; a recorded entry stays recorded, and the next attempt posts it without a second entry.

`question_posted` compares the post's `n` with the number of the latest `question` record, so a comment recorded after the question does not raise `ask` again. Tests: `tests/application/handlers/test_questions.py`, `tests/domain/test_question_post_texts.py`.

### Recording the human's act

A handler that answers an act of the human on a pull request first records the act in the work item's branch and pushes it, and only then posts, reopens or checks out anything else (kept thing 3). If the factory dies after the push, the act is already in the journal and the next tick does not repeat it. `factory.application.handlers.recording` holds what the handlers share:

- `target_of(event)` returns `Target(snapshot, state, pull_request)` for the event's work item. It raises `CannotHandle` (kind: the event's) for an event with no work item (`the event names no work item`) and for a work item whose document has no state (`work item <id> has no state`). `require_pull_request(target, kind)` returns the pull request number, or raises `CannotHandle` of `kind` (`work item <id> has no pull request`).
- `commit_subject(work_item, text)` gives `work item <id>: <text>`. Nothing parses commit subjects.
- `WorkItemRecorder(boundaries)` does the git work. `check_out(branch)` resets to `HEAD`, switches to the branch at `origin/<branch>` and resets to it, so whatever a killed handler left (uncommitted changes, untracked files, an unpushed commit) is gone. It does not fetch: the caller must have fetched, as the tick does. `read` and `write` use the work item reader and writer on a path in the checkout. `publish(branch, subject)` commits and pushes, and raises `PushFailed` for any outcome but `pushed`. `record(branch, path, document, subject)` is `write` then `publish`.

### Comments are copied by id

`CommentCopier(boundaries)` (`factory.application.handlers.comments`) copies the human's comments on a pull request into the journal.

- Only the marker tells the factory's comments from the human's: `unread(state, pull_request)` lists the comments, drops those with `by_factory` and those whose id is in `state.comments_read`, and keeps the listed order. The author is never looked at, and a body starting with `factory:` counts as the human's.
- Comments are tracked by id, never by count, so a factory post in between, or a deleted comment, neither hides nor repeats another one.
- `append(document, comments)` adds, for each comment with a non-blank body, a `human` entry of kind `comment`, dated with `created_at` in UTC; `\r\n` in the body becomes `\n`, and the edges are stripped as for any entry. A blank comment gets no entry. Every given id joins `comments_read`, which stays sorted without repeats.
- `copy(snapshot, pull_request, adjust=None)` checks out the branch, reads the work item, appends the unread comments and records them with the subject `work item <id>: comments from the pull request`. It returns `CopyResult(recorded, commit)`: the new ids and the pushed commit, or `([], None)` with nothing written when nothing was unread. `adjust(document, comments)`, when given, changes the appended document and lands in the same commit; it is not called when nothing is unread. A push that fails raises `PushFailed`, and the next `copy` records the same comments once. A work item without a state raises `ValueError`; callers pass `target_of` first, which refuses it with `CannotHandle`.

No handler is registered with this yet: the comment handler and the send-back use `CommentCopier`.

The agent run's environment is made by `agent_environment(scripts, home)`: exactly `PATH` = `<scripts>:/usr/local/bin:/usr/bin:/bin` and `HOME` = `str(home)`. `production_environment()` calls it with the directory of `sys.executable` (where the `factory-guard` console script is installed) and `Path.home()`. F0010 scrubs the environment, probes the `PATH` and completes `build_boundaries` from the instance settings.

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

One agent run is one cost record: a JSON line in the sidecar file beside the work item, `cost_records_path(path)` (`<work item>.costs.jsonl`, see *Identity, order and places of work items*). The format is `CostRecord` (`factory.domain.cost_records`), the interfaces `CostRecordReader` and `CostRecordWriter` (`factory.application.files`), and `JsonLinesCostRecordReader` and `JsonLinesCostRecordWriter` (`factory.adapters.cost_records_jsonl`). How a bill is summed is in *Bills*; a crashed stage's records are discarded with the stage (F0008).

### When a record is created, completed and committed

`CostRecorder` (`factory.application.costs`) keeps the records of one run in a `CostRun` (frozen, no unknown keys): `path` (the sidecar), `run` (the record's id) and `records` (every record of the work item, this run's last).

- **Created at the start.** `StageLauncher.launch` calls `CostRecorder.begin` after it composes the request and right before the agent runtime runs. `begin` reads the sidecar in the work tree (a missing file is no records), adds a `started` record (a new `uuid4` hex `run`, the stage, the stage's role from the pipeline definition, `attempt` equal to the state's `attempts`, `started_at` from the clock, every measure and `image` `None`) and writes the file.
- **Completed at the end.** Right after the runtime returns, `complete` replaces that record with a `completed` one: the duration in seconds, the end reason, and `turns`, `tokens` and `cost_usd` exactly as the runtime reported them. Unknown stays `None`, never 0 and never estimated; a reported zero stays zero (R24). A run that failed (`ok` false) has its record like any other. `image` stays `None` until F0010.
- **Committed with the next commit, never pushed alone.** The stage-start commit holds the records of earlier stages only. The new records travel in the stage's next commit: the result commit, or the stall commit of a stall (a died or timed-out run, a red check).
- **Rewritten after every undo.** The undo reverts every file outside the write paths, and the sidecar is one. So the records are kept in memory (`CostRun`), and `CostRecorder.write` puts them back right after the undo: in `AfterAgent.process`, and in `StallService.stall` when its `StallContext.cost` is set. An agent that overwrites or deletes the sidecar changes nothing in the commit. The factory's own rewrite is not named in the journal entry's paragraph about undone changes.
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

## Bills

A bill is a sum of cost records and nothing else. The cost line a `done` journal entry carries is display text: no code reads it back, and a bill never depends on it.

`factory.domain.bills` is pure. `Bill` (frozen, no unknown keys) holds `runs`, `runs_cost_unknown`, `duration`, `turns`, `tokens` and `cost_usd`; `StageBill` pairs a `Name` with a `Bill`.

- `bill(records)` counts every record in `runs`, whatever its status and end reason, so a failed run is in the bill. `runs_cost_unknown` counts the records whose `cost_usd` is `None`. `duration`, `turns`, `tokens` (field by field) and `cost_usd` sum the known values; a `None` is skipped, never zero.
- `bills_by_stage(records)` gives one `StageBill` per stage in the order of its first record; a stage that runs again joins its first group. `total(stage_bills)` sums them field by field.
- `cost_line(bill)` and `cost_table(stage_bills)` build the text the operator guide describes. Minutes and dollars are rounded half up with `Decimal.quantize`; the minutes are computed from `Decimal(str(seconds))` to avoid float half-way errors.

`BillService(git, cost_reader)` (`factory.application.costs`) builds a `WorkItemBill` (`work_item`, `total`, `stages`, `line`, `table`). `for_work_item` reads only remote-tracking refs: `origin/<branch>` when it exists, else `origin/main`. It finds the first `.md` file under the features directory whose name parses to the id (none gives `None`), and reads that file's sidecar with `show_file` (no sidecar means no records). A local commit that was not pushed, and the contents of the `work` volume, have no influence, so a fresh clone shows the same bill. The service never fetches; the caller does. `in_flight()` returns the ids of the remote branches named like work item branches, sorted with `work_item_order`.

`factory.entry.bill` is the command `factory-bill` (`run(argv, service, out)` returns the exit status; `main` builds the service with `build_bill_service` from `factory.entry.wiring`, the only adapter import of the entry layer).

### No code reads data from the journal's text

The journal's text is for people; its data is the front matter and the sidecar. `tests/test_no_journal_reading.py` parses every module under `src/factory` (`modules()` of `tests/source_search.py`) and fails when:

- `entry_text` is referenced (imported, used as a name or as an attribute) outside `factory.domain.journal`, `factory.application.handlers.hand_over` and `factory.application.handlers.questions`;
- `JOURNAL` of `factory.domain.sections` is referenced outside `factory.domain.sections`, `factory.domain.journal`, `factory.domain.story_form`, `factory.adapters.work_item_markdown` and `factory.application.opening`;
- a string literal equal to `Journal` or `## Journal` stands outside `factory.domain.sections`.

A local variable named like a forbidden name counts too. To read something from a journal entry, put it in the front matter or a sidecar instead; do not add the module to the list.

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
- A load at any other ref raises the same refusal but raises and clears no stop, so a read of a branch never changes the health status. `WritePathService` ("The write paths" below) reads the definition at another commit and parses it directly with `pipeline_reader`, not through the loader.
- A `GitError` propagates and raises no stop. An `OSError` of the stop's writes propagates in place of `PipelineDefinitionInvalid`.
- Tests: `tests/application/test_pipeline_loading.py`, with `human.push_file` and `checkout.fetch()` for other versions of the file and `install_agents(agent_home, roles)` in `tests/git_support.py` for the agent files.

## The write paths

What an agent may write is decided in one place, for the guard hook and for the undo of a stage alike.

### Where they come from

`WritePathService(boundaries).at(stage_start, work_item_path)` (`factory.application.write_paths`) returns the `GuardSettings` of the claimed stage. It reads `factory/pipeline.yml` at `stage_start.commit` with `git.show_file` and parses it with `pipeline_reader`; it never reads the work tree's copy, so an agent that rewrites the pipeline definition widens nothing and an invalid rewrite breaks nothing. The write paths are those of the role of `stage_start.claim.stage`, expanded; `root` is `boundaries.checkout`; `protected_paths` is `PROTECTED_PATHS`.

It parses the definition itself and does not use `PipelineLoader`, which stays the one place that loads the definition for the tick. This read has another purpose: it checks no installed agent file and raises or clears no stop.

Errors: `ValueError` when `work_item_path` is not `factory/features/<feature directory>/<lifecycle folder>/<work item file name>`. `PipelineDefinitionInvalid`, naming the fault, when the definition is absent or invalid at the commit, when the stage is not in it or has no role, and when a write path holds a placeholder other than the two below.

### Matching and placeholders

`factory.domain.write_paths`, all pure. `matches_any(path, patterns)` is `fnmatch.fnmatchcase`: case-sensitive, and `*` also matches `/` (`src/*` matches `src/a/b.py`; `SRC/a.py` does not match). `is_writable(path, write_paths)` adds a safety test: an empty path, a path beginning with `/` and a path with a `..` segment are never writable (`src/../factory/pipeline.yml` does not pass `src/*`); `src/..x/a.py` is safe. Callers pass normalised repository paths (POSIX separators, no `.` or empty segment, no trailing `/`).

`expand_write_paths(patterns, work_item_path=..., feature_path=...)` replaces `{work_item}` with the work item's path and `{feature}` with the feature's path, `factory/features/F0004-x` (the work item's path without its last two segments), keeps the order and leaves other patterns as they are. Any other `{name}` of lowercase letters and underscores raises `ValueError` naming it; a brace that is no such name (`{Feature}`, `{1}`) stays.

### Protected paths and the refusal

`PROTECTED_PATHS` is the engine's fixed list of ten patterns: `.claude/*`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, `feature.md` and `*/feature.md`. No write path can reach them, and a project cannot change the list. The patterns are anchored: `docs/CLAUDE.md` and `src/pyproject.toml` are not protected. `docs/project-guide.md` is not protected; the documenter keeps it.

`refusal(path, guard)` is the one verdict, `None` when the write is allowed, else a text, checked in this order:

1. `<path> is not a path inside the checkout.` (unsafe path, as above)
2. `<path> is owned by the human; a change there is a question.` (matches `guard.protected_paths`, even when a write path also matches)
3. `<path> is outside the write paths of this stage.` (matches no write path)

The guard hook resolves the path it judges to a real path relative to the root (see "The guard command"); the undo takes git's paths as they are.

Tests: `tests/domain/test_write_paths.py`, `tests/application/test_write_paths.py`; a later version of the definition is made with `human.push_file("main", "factory/pipeline.yml", text)` and `checkout.fetch()`.

## The guard command

`factory-guard --settings <file>` refuses an agent's `Edit` or `Write` outside its write paths while the agent runs. `pyproject.toml` registers it as `factory-guard = "factory.entry.guard:main"`; `python -m factory.entry.guard` does the same. `ClaudeCodeRuntime` registers it as a `PreToolUse` hook on `Edit|Write` (see "The `claude -p` runtime").

### What it reads

- The settings file named by `--settings`: the stage's `GuardSettings` as JSON, as `GuardSettings.model_dump_json()` wrote it, with an absolute `root`. The runtime writes it from `WritePathService.at`, that is from the definition at the stage-start commit. The guard reads no other file and takes no write path from the pipeline definition in the work tree, so rewriting that file changes no verdict.
- The hook payload on standard input: the JSON Claude Code sends. Only `tool_input.file_path` is looked at, whatever the tool.

### Verdict and exit status

`factory.adapters.claude_guard.judge(payload, settings)` returns a `GuardVerdict` (`allowed`, `message`) and never raises; `read_guard_settings(path)` returns the settings or raises `GuardSettingsInvalid(path, fault)`. `factory.entry.guard.main(argv, *, stdin, stderr)` returns the status; `None` means `sys.argv[1:]`, `sys.stdin` and `sys.stderr`, read at the call. The entry module reaches the adapter only through `factory.entry.wiring`.

- Exit 0, nothing written: the call is allowed.
- Exit 2, the message and a newline on standard error: the call is refused. Claude Code blocks the tool call on status 2 and shows standard error to the agent. Status 2 is also the answer when `--settings` is missing or has no value (`usage: factory-guard --settings <file>`) and when the settings file cannot be read (`guard settings <file>: <fault>`), so a broken setup refuses rather than allows. Nothing is written to standard output, and `main` never ends in an exception.

### Which path is judged

A relative `file_path` is taken relative to `root`. The guard takes `os.path.realpath`, so `..` segments and symbolic links are resolved before the verdict: `src/../pyproject.toml` is judged as `pyproject.toml`, and a link inside `src` to a file outside the checkout is outside. Containment is tested on path parts, not on a string prefix (`<root>-x/a.py` is outside `<root>`). A path outside the real root, or one whose real path cannot be computed (a NUL character), is refused with `<file_path as given> is outside the checkout.`. A path inside goes to `refusal` with its POSIX path relative to the real root; its text is the message.

### Failing open

A payload that is not JSON, not an object, has no `tool_input` object, no `file_path`, or an empty or non-string `file_path` is allowed, as in v1. The guard cannot judge what it cannot read, and a tool without a path (such as `Bash`) is not its concern. The payload is read through a private Pydantic model, so no `Any` is inspected by hand. A `file_path` that resolves to the root itself (`.`) reaches `refusal` with `.`.

Tests: `tests/adapters/test_claude_guard.py`, `tests/entry/test_guard.py` (the second runs the module in a subprocess).

## The undo

`UndoService(boundaries).undo(stage_start, work_item_path)` (`factory.application.undo`) puts the work tree back after an agent run. The guard refuses while the agent works; the undo reverts what got through (a tool the guard does not see, such as a shell command). It returns an `UndoReport` (frozen, no unknown fields): `reverted` and `deleted`, sorted ascending without repeats, and `restored_work_item`. `AfterAgent` runs it after every completed agent run (see "After the agent run").

### What it undoes

Everything is compared with the stage-start commit, not with the work tree as it was when the agent began, so a file the agent changed in the work tree or in a commit of its own ends with the content of the stage-start commit. `Git.changed_paths(stage_start.commit)` gives the candidates: commits since then, the work tree and untracked files; ignored paths are not in it.

A candidate is refused, and so undone, in two cases:

- `refusal(path, settings)` is not `None`: the path is outside the write paths of the stage or is protected (see "The write paths"). The settings come from `WritePathService.at`, that is from the pipeline definition at the stage-start commit, the same source the guard uses. An agent that rewrites `factory/pipeline.yml` to widen its role widens nothing, and an invalid rewrite does not make the undo raise; the pipeline definition itself is put back.
- The path lies directly in an `in-progress` folder of a feature (`factory/features/<feature>/in-progress/<file>`) and is not the stage's own work item. This undoes every other work item in progress, every cost-record file (`.costs.jsonl`), the stage's own included, and any other file there, whatever the write paths say. Nested files (`in-progress/sub/x`), other lifecycle folders and an `in-progress` folder outside `factory/features/` follow the write paths. The guard does not know this second rule.

A refused path that did not exist at the stage-start commit (`added`) is deleted and listed in `deleted`; any other is checked out from that commit with `Git.revert_paths` and listed in `reverted`. Paths allowed by the write paths are not touched.

### The work item

After the refused paths, the stage's own work item is handled separately. Its state and journal are restored from the stage-start commit with `restore_state_and_journal`; the agent's edits to its sections stay. `restored_work_item` is true when that changed the file. If the agent deleted the file or left front matter that cannot be read, the file is checked out whole from the stage-start commit and `restored_work_item` is true; it is not listed in `reverted`. A work item the role may not write at all is refused like any path: it is put back whole, listed in `reverted`, and `restored_work_item` is false.

The baseline is read first. When the stage-start commit does not hold the work item, or holds it unreadable, `undo` raises `WorkItemFormatError` naming the path before it changes anything.

### Limits

- The undo makes no commit and no push. A commit the agent made stays in the history; only the work tree is put back.
- Ignored paths and anything outside the checkout are not seen and stay as they are (left for v2).
- Git's paths are taken as they are; renames show as a deletion and an addition (see "The git wrapper").

Tests: `tests/application/test_undo.py`; a fake agent writes into `boundaries.checkout` between `ClaimService` and `undo`.

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

## The prompt and the request for a stage

Before a stage's agent runs, `TaskComposer` (`factory.application.task`) builds its `AgentRunRequest`; the caller gives it `Boundaries`, the `PipelineDefinition` and the `environment`, and each call a `TaskContext` (work item, path, stage, document, branch, pull request, the form findings, the `GuardSettings`). The pure rules are in `factory.domain.prompts`.

### The decisions

`allowed_decisions(next_stages)` returns the stage's `next` in their order, then `question`. It is computed once in `compose`, and the same list goes into the prompt's line and into `AgentRunRequest.allowed_decisions`; the runtime builds its outcome schema from it and the stage protocol validates the agent's decision against it. `question` is always allowed. `stuck` is not a decision here: an agent that cannot finish ends with `question`.

### The prompt

`compose_prompt(PromptFacts)` joins these lines with one newline, no trailing newline:

| Line | When |
|---|---|
| `Work item: <path>`, `Id: <work item>`, `Stage: <stage>` | always |
| `Allowed decisions: <decisions joined by ", ">` | always |
| `Branch: <branch>`, `Pull request: <number>`, `Round: <round>` | always; the round is the document state's |
| `Mode: a test change the human approved; the coder's journal entry <n> names it.` | only when `test_change_entry` is set |
| `Format check: passed`, or `Format check found: 1. <message> 2. <message>` | only when `findings` is set (an empty list is `passed`) |
| `END_LINE` | always |

The Format check line goes to the first stage of the pipeline definition only; every later stage has `findings=None` and no such line.

The Mode line is decided from the journal's data, never from an entry's text: at a stage whose role is `tester`, `last_record(document, kind="result")` is read, and when its speaker is `coder` the line names its number. The last `result` record is used, not the last record, so a later `stall`, `crash` or `comment` record does not hide the test change. A `result` record by the tester, no `result` record, or any other role gives no Mode line.

### The request

`compose` fills `AgentRunRequest` with the agent as given, the prompt, the decisions, `time_limit` (the role's minutes), `working_directory` (`boundaries.checkout`), `guard` (from the context) and `os_user=None`. `environment` is a copy of the mapping given to `TaskComposer`, passed on unchanged: nothing is added, removed or scrubbed here (the wiring supplies it; scrubbing is F0010's). `agent(stage)` reads the definition of the stage's role through `AgentDefinitionReader`; a stage without a role raises `ValueError` naming it, a missing file lets `AgentDefinitionMissing` through. A document without a state makes `compose` raise `WorkItemFormatError`.

### The story form check

`StoryFormChecker(boundaries).findings(document)` returns `check_story_form(document, form, folder="in-progress")`. The form is read with `Git.show_file("origin/main", STORY_FORM_FILE)`, never from the work tree, so nothing an agent writes there changes it; the checkout must have fetched to see a form the human pushed. A form absent at `origin/main` raises `WorkItemFormatError` with `path == "factory/story-form.md"`. A stage runs the check before and after the agent.

Tests: `tests/domain/test_prompts.py`, `tests/application/test_task.py`.

## Opening a work item

`WorkItemOpening` (`factory.application.opening`) runs before a stage is claimed. It is built with `Boundaries` and the `PipelineDefinition`. Neither method commits, pushes or fetches; the tick fetched before, so a commit pushed since is not seen. The claim makes the first commit, which for a new branch is also the opening commit.

### `prepare(work_item, path)`

`path` is the work item's file under its feature's `in-progress/` folder, the same on `main` and on its branch. The branch is `branch_name(work_item)`. When `prepare` returns, the checkout is on that branch with a clean work tree, and it returns a frozen `PreparedWorkItem` (work item, branch, path, document, `branch_existed`, `merge_conflict`).

- **No `origin/<branch>`: the work item is new.** The local branch is created at `origin/main` and the file is read from `origin/main`. An absent file raises `WorkItemFormatError` with `path` set. Only the body of the backlog file is used: whatever its own front matter says (`stage`, `attempts`, `blocked`, a `journal` list) is ignored. The state is `initial_state` of the definition's first stage. A body without a `## Journal` section gets an empty one at its end; entries already in that section are left as they are, and the form check reports the mismatch between the text and the one record of the state. Entry 1 (`human`, `created`, dated by the clock) is then appended by code.
- **`origin/<branch>` exists.** The local branch is reset to `origin/<branch>`, whatever a local branch of that name held, then `origin/main` is merged in. On a conflict the wrapper has already aborted the merge: `merge_conflict` is `True`, the head is the remote branch's and the document is the branch's. The document is read from the work tree after the merge.

Doing the merge here means the baseline of the undo, taken at the stage-start commit, comes after every preparation step.

### `ensure_pull_request(work_item, document)`

Returns, in this order: the pull request numbered in `document.state.pull_request` if it is open; the open pull request of the branch; a new draft titled `<id>: <title>` with the body as description. Only an open pull request is reused; a closed or merged one never is. The title is looked up only when a draft is created, and a body without a title line then raises `WorkItemFormatError`. A `HostingServiceError` propagates. No file changes.

Tests: `tests/application/test_opening.py`.

## Starting a stage

`StageLauncher(boundaries, instance, definition, environment)` (`factory.application.stage`) takes a `PreparedWorkItem` from `WorkItemOpening.prepare` and runs the stage's agent. `instance` and `definition` go to `ClaimService`; `environment` is the environment of the agent run and reaches `TaskComposer` unchanged, so the run holds exactly those entries.

`launch(prepared)` does these steps in this order. The claim in step 4 is the only write to the git remote.

1. Refuse a work item with `merge_conflict` set or without a state: `ValueError`, before anything is read or pushed.
2. Read the agent definition with `TaskComposer.agent`. A stage without a role (the approval stage) raises `ValueError` naming the stage; a missing agent file raises `AgentDefinitionMissing`. Both come before any push.
3. Take the story form findings from `prepared.document` (`StoryFormChecker`).
4. Push the claim: `ClaimService.claim(branch, path, document, stage)` makes the stage-start commit. A rejected push or an unreachable remote raises `PushFailed`.
5. Read the work item file back from the work tree. `StartedStage.document` is what the stage-start commit holds, not the document given to the claim.
6. `WorkItemOpening.ensure_pull_request`: find or create the pull request.
7. `WritePathService.at(stage_start, path)` gives the guard, from the definition at the stage-start commit.
8. `TaskComposer.compose` builds the request (prompt, guard, environment, allowed decisions).
9. `AgentRuntime.run`.

**No agent run precedes the pushed claim.** When `run` is called, `origin/<branch>` already holds the stage-start commit with the claim and the journal record (`factory`, `started`); when step 4 fails, no run starts. The stage-start commit is the last commit before the run: for a branch that existed it is one commit above the old head (the merge of `main` in `prepare` comes before it), for a new work item it is also the opening commit.

The stage-start commit does not change `pull_request`: it is `None` for a new work item and otherwise the number already recorded. The number of the pull request found or created in step 6 is in `StartedStage.pull_request` and in the prompt; the stage's next commit records it. No local run record is written; the claim's `started_at` says when the stage began.

`launch` returns a frozen `LaunchedStage`: `started` (a `StartedStage` with the work item, stage, branch, path, `stage_start`, `document`, `pull_request` and the form `findings` taken before the run), `request` and `result`. A run that dies, reaches its `time_limit` or its budget is a result. `PushFailed`, `AgentDefinitionMissing` and `AgentRuntimeError` propagate unchanged; after an `AgentRuntimeError` the claim stays pushed.

Tests: `tests/application/test_stage_launch.py`. `ObservingRuntime` (`tests/observing_runtime.py`) is an `AgentRuntime` that records the remote branch's head, the checkout's `HEAD` and the pull requests in the hosting fake at the moment `run` is called, then delegates to `FakeAgentRuntime`.

## Stalls

A stall is the one way a stage ends without a result the factory can keep. It costs one attempt and is a value, never an exception. `StallService.stall` (`factory.application.stalls`) does it; the later stories (the branch, the decision, the form, a red check, a merge conflict) call it with their reason.

### The reasons

`factory.domain.decisions.StallReason` is one of `died`, `time_limit`, `budget`, `no_result`, `decision_not_allowed`, `left_branch`, `form_invalid`, `check_red`, `merge_conflict`. `stall_reason_of(result)` maps the end reason of an `AgentRunResult` to the reason of the same name and `completed` to `None`.

`factory.domain.post_texts.stall_cause(reason, detail="")` gives the reason's sentence, and `<sentence>: <detail>` with a detail. `stall_note(reason, attempts, attempts_cap, *, detail="")` gives `Stalled (attempt <n> of <cap>): <cause>. ` and then `Retrying on the next tick.` when `attempts < attempts_cap`, otherwise `The attempts cap is reached; the factory asks you next.` The word "retry" appears only in the first case.

The detail's trailing line breaks are removed. A detail of one line is part of the sentence, as above. A detail of several lines puts its first line through `stall_cause` into the sentence, so the follow-up stays on that first line, and the remaining lines follow after an empty line in a fenced block: the fence `` ```text ``, the lines unchanged, the closing fence. GitHub renders a comment as Markdown, and unfenced output loses `<module>` and turns `__init__` bold. The fence is three backticks, or one more than the longest run of backticks in the remaining lines when that run is three or longer. The journal's stall entry is unchanged and keeps the detail as continuation lines.

### `StallService.stall(context, reason, detail="")`

`StallService(boundaries, instance, definition)`. `StallContext` (frozen, no unknown keys) holds `work_item`, `stage`, `branch`, `path`, `stage_start` (a `StageStart`, or `None` when the stage never started, for example a merge conflict at the preparation) and optionally the `document`, the `pull_request` and the `cost` (a `CostRun`) the caller already holds. The steps, in this order:

1. With a `stage_start`: when the checkout is not on `context.branch`, what the agent left on the other branch is discarded with `reset_to("HEAD")` (that branch keeps its head) and the branch is checked out at the stage-start commit. Then `UndoService.undo` runs, whatever the reason; its report is `StallResult.undo`. With a `context.cost`, the sidecar is written again right after the undo. Without a `stage_start` nothing is undone and `undo` is `None`.
2. The document is `context.document`, else the work item file read from the work tree.
3. The pull request is `context.pull_request`, else `WorkItemOpening.ensure_pull_request` (an open pull request of the branch, or a new draft).
4. The new state has `attempts` + 1, the claim released (`ClaimService.release`) and `pull_request` set; `stage`, `blocked`, `round`, `crashes`, `comments_read` and `handed_over` stay. One entry is appended: speaker `factory`, kind `stall`, text `Stage <stage> stalled (attempt <n> of <cap>): <cause>`.
5. The file is written, everything in the work tree is committed in one commit and pushed. Any push outcome but `pushed` raises `PushFailed`.
6. After the push, the note is posted with `PostKey(work_item, "stall", <the stall entry's number>)`.
7. Whether the note was `posted` or `already_posted`, `HostingService.set_labels(pull_request, labels_for(<the stalled state>))` writes the stage label, so a first-stage stall has its label before any result commit. Written, never read back.

So a stall keeps the writes inside the write paths (the undo reverts the rest) and releases the claim, which keeps a later tick from taking the stalled stage for a crash. The stall adds one commit: above the stage-start commit when the agent committed nothing, above the agent's last commit when it did (those commits stay in the history).

A `HostingServiceError` is not a stall and propagates unchanged: from step 3 before anything is written, committed or pushed, so the remote is unchanged; from step 6 after the push, so the stall commit stays on the remote, no note is posted and no label is written; from step 7, so the stall commit stays and the note stays posted. `StallResult` (frozen, no unknown keys) holds `reason`, `attempts`, `attempts_cap`, `commit` (the pushed head), `pull_request` (the last three at least 1), `note` (the `PostOutcome`) and `undo`.

Tests: `tests/domain/test_decisions.py`, `tests/domain/test_stall_texts.py`, `tests/domain/test_stall_note_block.py`, `tests/application/test_stalls.py`, `tests/application/test_stall_labels.py`. The last starts stages with `StageLauncher` and the fake agent runtime; its `SwitchingRuntime` (a subclass of `ObservingRuntime`) switches the checkout to another branch while it runs.

## After the agent run

The factory believes what it observes, not what the agent reports. `AfterAgent(boundaries, instance, definition).process(launched)` (`factory.application.stage`) takes the `LaunchedStage` that `StageLauncher` returns and goes through these steps in order. The first step that fails is a stall (see "Stalls"), which counts one attempt, and the later steps do not run.

1. **Branch.** The checkout must still be on the work item's branch, otherwise the stall `left_branch`.
2. **Result.** `stall_reason_of(result)` turns a run that died, ran out of budget or time, or gave no result into the stall of that reason; the detail is the first permission denial (`denied: <tool>: <detail>`), if any. A decision that is not one of the request's `allowed_decisions` is `decision_not_allowed`, with the decision and the allowed ones as detail.
3. **Undo and restore.** `UndoService.undo` reverts the changes outside the write paths. Then the stage-start state (the claim included) and the stage-start journal are put back, whatever the agent wrote there: **the agent's edits to state and journal are always discarded.** The rest of the body keeps the agent's changes when the role may write the work item; when it may not, the undo has put the whole file back and lists it in `reverted`.
4. **The entry.** `factory.domain.decisions.agent_entry(role=, stage=, decision=, text=, undone=)` builds it, and code decides everything but the words. The speaker is the role. The kind is `question` for the decision `question`, otherwise `result`. The text is the agent's text, stripped, with one leading `<role>:` or `<stage>:` removed (the colon directly after the name; the role is tried first). A blank text gives `None`, which `AfterAgent` stalls as `no_result`. When paths were undone, the text ends with a blank line and `The factory undid changes outside the write paths: <paths sorted, joined by ", ">.`. The work item's own cost-record file, which the factory rewrites after the undo, is never named there.
5. **The form again.** The story form is checked on the undone work item and compared with the findings from before the run (`StartedStage.findings`). Only a finding that was not there before stalls, as `form_invalid`, with the new messages joined by `; ` as detail. Findings are compared by message with every run of digits replaced by one mark, so a finding whose line number moved because the agent edited above it is the same finding. A kind that now occurs more often than before counts as new: of equal messages the earlier ones count as the old ones. Only in this stall is the entry appended (above the stall entry); otherwise it is built but not appended.

What comes back is an `AgentAftermath` (frozen, no unknown keys): `started`, `request`, `result`, `decision`, `document` (the work item after step 3, without the entry), `entry`, `undo` (the `UndoReport`) and `form_findings` (all findings after the run). The stage's result commit ("The stage protocol", below) appends the entry.

Tests: `tests/domain/test_agent_entry.py`, `tests/application/test_after_agent.py`. The latter starts stages with `StageLauncher` and the fake agent runtime, whose `ScriptedRun.writes` tampers with the work item, writes outside the write paths and breaks the form.

## The decision rules

`factory.domain.decisions.decide(definition, state, decision, findings=())` turns the agent's decision into a `StageMove` (frozen, no unknown keys): `rule`, `stage`, `blocked`, `round` and `question`. It is pure; `StageFinisher` ("The stage protocol", below) applies the move. It never touches `attempts` or `crashes`: a rework counts rounds, a stall counts attempts, and the two are kept apart.

"Forward" is a decision equal to `next[0]` of the state's stage; a "rework" is any other entry of `next`. This is the only rule for counting rounds, wherever in the pipeline definition the named stage sits. A stage missing from the definition, or a decision that is neither in `next` nor `question`, raises `ValueError` naming it.

The rules are tried in v1's order; rule 5 (a red check) is not decided here but by the checks after the move:

| Rule | When | Stage | `blocked` | `round` | `question` |
|---|---|---|---|---|---|
| 1 | forward, and `findings` is not empty | unchanged | `question` | unchanged | `findings_question(findings)` |
| 2 | decision `question` (findings do not matter) | unchanged | `question` | unchanged | `None`: the agent's own entry is the question |
| 3 | rework, stage has `round_cap`, `round + 1 <= round_cap` | the decision | `None` | `round + 1` | `None` |
| 4 | rework, stage has `round_cap`, `round + 1 > round_cap` | unchanged | `round_cap` | `round + 1` | `round_cap_question(round + 1, round_cap)` |
| 5 | forward, but a check is red | unchanged (a stall, see "The stage protocol") | | | |
| 6 | forward, no findings | `next[0]` | `None` | unchanged | `None` |
| 7 | rework, stage has no `round_cap` | the decision | `None` | unchanged | `None` |

Rules 3, 6 and 7 move, so they clear a `blocked` of `question`. `findings` matter only to a forward decision. Rule 6 only says the move; its checks run afterwards.

The factory's own question texts are in `factory.domain.post_texts`: `round_cap_question(rounds, cap)`, `findings_question(findings)` (the messages numbered from 1, joined by one space) and `attempts_cap_question(stage, attempts, last_stall)`. That module imports `StallReason` and `FormFinding` only under `TYPE_CHECKING`, because `decisions` imports it.

Tests: `tests/domain/test_decision_rules.py`, `tests/domain/test_question_texts.py`.

## The stage protocol

`StageRunner(boundaries, instance, definition, environment).run(work_item, path)` (`factory.application.stage`) is the one entry point that runs a stage from the claim to the result commit. It returns a frozen `StageReport`: `work_item`, `stage` (the stage that ran, from the state `prepare` read), `next_stage`, `rule` (the decision rule applied, 1 to 7, or `None` when the stage stalled before a decision), `commit` (the pushed head), `pull_request` and `stall`. `stall` is set exactly when the stage stalled; `next_stage` equals `stage` for a stall and for the rules that keep the stage (1, 2 and 4). A red check is rule 5.

`run` does these steps in this order; a `StallResult` from any step ends the run with a report whose `rule` is `None`:

1. `WorkItemOpening.prepare`. With `merge_conflict` set in the result, `StallService.stall` with reason `merge_conflict` and no stage start: no claim is pushed and no agent runs.
2. `StageLauncher.launch`: claim, pull request, agent run. `environment` is passed unchanged.
3. `AfterAgent.process`: branch, result, undo, entry, form.
4. `StageFinisher.finish`: decision, checks and reports, result commit.

### `StageFinisher.finish(aftermath)`

1. `decide` on the state of `aftermath.document`, with the form findings after the run. A first stage whose agent fixed the last finding therefore moves forward instead of asking.
2. Rule 6 only: each check of the stage's `checks`, in order, through `ProjectCommands.run` with the `time_limit` of the pipeline definition's project command. The first one that is not green ends the stage as a stall `check_red` (rule 5): the later checks and all reports do not run. The stall detail is the command's name and the last `STALL_TAIL_LINES` (15) lines of its output (all, when fewer). The journal then holds the agent's entry, ending with the lines of the checks that were green, directly above the `factory` stall record. The stall costs one attempt and changes neither the stage nor `crashes`. The checks see the work tree after the undo.
3. Rule 6 only, once every check is green: each report of the stage's `reports`, in order. A report that fails holds nothing; a report is recorded, never enforced.
4. The agent's entry gains, after a blank line, one line `` `<command>`: <last line of its output> `` for each green check and each report, in the order they ran (for example `` `check`: 12 passed ``). A stage with neither gets no such lines.
5. The entry is appended; when the move has a question (rules 1 and 4), a `factory` entry of kind `question` follows it.
6. The new state takes `stage`, `blocked` and `round` from the move and `pull_request` from the started stage, and the claim is released. `crashes` is reset to 0 on rule 6, a forward move, and unchanged otherwise; `attempts`, `comments_read` and `handed_over` never change.
7. The file is written, everything in the work tree is committed in one commit and pushed. Any push outcome but `pushed` raises `PushFailed`, and no label has been written.
8. Last, `HostingService.set_labels(pull_request, labels_for(new_state))`. `labels_for` (`factory.domain.labels`) gives `[LABEL_PREFIX + state.stage]`, for example `["stage:review"]`. Labels are a projection of the stage: they are written after the push and never read back. A `HostingServiceError` from this step propagates; the result commit stays pushed.

Rules 1, 2, 3, 4 and 7 run no check and no report.

A run adds exactly one commit of the factory's own on `origin/<branch>`: the result commit or the stall commit, above the stage-start commit when the agent committed nothing and above the agent's last commit when it did. It holds the whole work tree, so a file a check creates is committed unless `.gitignore` covers it.

Tests: `tests/domain/test_labels.py`, `tests/application/test_stage_finish.py`, `tests/application/test_stage_run.py`. The checks and reports are real `make` targets from a `Makefile` the tests push to `main`; the agent is `FakeAgentRuntime`, the hosting service its fake.

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
