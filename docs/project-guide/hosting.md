# Git and the hosting service

This file covers the area `hosting`: git and the hosting service. Read the index, [README.md](README.md), first. The exact detail (every option, outcome and limit) is in the *Reference* at the end.

## The hosting service

The factory reaches the hosting service, meaning pull requests and their comments, only through one interface. It is the abstract base class `HostingService` in [hosting.py](../../src/factory/hosting/application/hosting.py), module `factory.hosting.application.hosting`. The application layer knows no concrete client. Two classes implement it: the PyGithub client in [pygithub_hosting.py](../../src/factory/hosting/adapters/pygithub_hosting.py) and the one fake in [fake_hosting.py](../../src/factory/hosting/adapters/fake_hosting.py).

    HostingService.create_pull_request(branch, title, body, *, draft) -> PullRequestView
    HostingService.find_open_pull_request(branch) -> PullRequestView | None
    HostingService.get_pull_request(number) -> PullRequestView
    HostingService.list_comments(number) -> list[PullRequestComment]
    HostingService.post_comment(number, text, key) -> PostOutcome
    HostingService.close(number) -> None
    HostingService.reopen(number) -> None
    HostingService.set_draft(number, draft) -> None
    HostingService.set_description(number, body) -> None
    HostingService.set_labels(number, labels) -> None

- Nothing else may call the hosting service.
- Build a comment from the service's data with `PullRequestComment.from_body`, so that `by_factory` and `key` always agree with the body.
- Labels are a projection of the [stage](glossary.md): they are written and never read back. No operation returns them and `PullRequestView` has no label field.
- `LABEL_PREFIX` (`"stage:"`) in [paths.py](../../src/factory/shared/domain/paths.py) is the prefix of those labels, and `MAIN_BRANCH` there is `"main"`.
- `post_comment` returns `"already_posted"` when the key is already on the pull request.

See also: *The marker and the post key* below, and *Asking the human* in [pipeline.md](pipeline.md).

### The PyGithub client

`PyGithubHostingService` implements the ten operations on a PyGithub `Repository`. It is built by `pygithub_service(repository, token)` in the same module, which [wiring.py](../../src/factory/entry/wiring.py) calls with the repository's `owner/name` and the token read from the token file.

    PyGithubHostingService(repository, kill_points=None)
    pygithub_service(repository: str, token: str) -> PyGithubHostingService
    hosting_retry() -> GithubRetry

- The constructor reads nothing from the repository, so building the service sends no request.
- `pygithub_service` builds a lazy `github.Github` (`lazy=True`) with `retry=hosting_retry()`, and wraps its `Repository` in the service.
- Every failing call raises `HostingServiceError(operation, detail)`. A `github.GithubException` or an `OSError` (a connection error is one) inside any of the ten operations is re-raised with the operation's name and `str(error)` as detail, chained to the original. Any other exception, and `InjectedKill`, passes through unchanged.
- `hosting_retry()` is the one place the retry is built: a `GithubRetry` with `total=5`, `backoff_factor=2` and `allowed_methods` the default methods plus `PATCH`, so a write that sets a whole state (a label set, a close, a ready mark) is tried again too. A call that still fails after the retries is a `HostingServiceError`.
- `post_comment` lists the comments first and returns `"already_posted"` without posting when one has the same key. Otherwise it posts `render_post(text, key)`, reaches `KillPoint.AFTER_POST` and returns `"posted"`.
- `find_open_pull_request` asks for open pull requests with head `<owner login>:<branch>`.
- A view's `state` is `merged` when PyGithub says merged, else `open` or `closed`. `merge_commit` is set only for a merged pull request, even though GitHub reports a test-merge commit for an open one.
- `list_comments` sorts by id, oldest first, and reads a naive `created_at` as UTC.
- `set_labels` keeps the labels that do not start with `LABEL_PREFIX` and adds the given ones. The names it read are never returned.
- `github` is imported by this module only. No module in `src/factory` imports another route to the hosting service (`requests`, `httpx`, `aiohttp`, `urllib3`, `urllib.request`, `http.client`, `socket`, `git`, `pygit2`, `dulwich`, `githubkit`) or contains the string `"gh"`. [test_hosting_search.py](../../tests/guards/test_hosting_search.py) checks it.

Tests do not call PyGithub.

- [test_pygithub_hosting.py](../../tests/hosting/adapters/test_pygithub_hosting.py) uses the recording stand-ins of PyGithub's objects in [pygithub_stand_ins.py](../../tests/support/pygithub_stand_ins.py), passed in with `typing.cast`.
- [test_pygithub_retry.py](../../tests/hosting/adapters/test_pygithub_retry.py) reads the `retry` the built client was given, without a network.
- Use a low-entropy literal such as `"a" * 40` for a commit id in a test, so that `make secrets` stays green.

### The fake

Tests use `FakeHostingService` through the `hosting` fixture in [conftest.py](../../tests/conftest.py), built with the test's `kill_points`, and nothing else in place of the hosting service. It inherits `HostingService`, so Python refuses a fake that leaves an operation out.

    FakeHostingService(kill_points=None)
    add_human_comment(number, body, *, author="human") -> int
    delete_comment(number, comment_id) -> None
    close_by_human(number) -> None
    merge_by_human(number, merge_commit) -> None
    fail_next(operation, *, times=1) -> None
    factory_posts(number) -> list[PullRequestComment]
    labels(number) -> list[str]
    description(number) -> str
    pull_requests() -> list[PullRequestView]

- [test_hosting_fake_search.py](../../tests/guards/test_hosting_fake_search.py) checks that only the fake and the PyGithub client define `post_comment`, and that no test class does.
- It behaves as the PyGithub client does where a test can see it: a repeated post key returns `"already_posted"` and adds nothing, `merge_commit` is set only for a merged pull request, and every failing call raises `HostingServiceError`.
- `set_labels` replaces only the labels that start with `LABEL_PREFIX`. Others keep their order and the given ones come after.
- `post_comment` reaches `KillPoint.AFTER_POST` after a `"posted"`, and not for `"already_posted"`.
- Numbering is predictable: pull requests from 1, comment ids from 1 across all pull requests, the url of pull request `n` is `https://fake.invalid/pull/<n>`, and the `created_at` of comment `i` is 2026-10-12 UTC plus `i` seconds.
- A number that does not exist raises `HostingServiceError` from every operation that takes one.
- `add_human_comment` adds a comment as written and returns its id.
- `delete_comment` removes a comment. An unknown id raises `HostingServiceError`, and so does the id of a comment on another pull request, which is left alone.
- `close_by_human` sets the state `"closed"`. `merge_by_human` sets `"merged"` with that `merge_commit`.
- `fail_next` makes the next `times` calls of one of the ten operations raise `HostingServiceError(operation, "injected failure")` before any effect. An unknown name or `times` below 1 raises `ValueError`.
- `factory_posts` gives the comments with `by_factory` true, in order. It is how a test counts posts.
- `pull_requests` gives every pull request, whatever its state, by number.

```python
pull = hosting.create_pull_request("work-item/F0001-S0001", "title", "body", draft=True)
hosting.post_comment(pull.number, "Which option?", key)   # "posted"
hosting.add_human_comment(pull.number, "(a)")
assert len(hosting.factory_posts(pull.number)) == 1
```

### Data

The models are in [hosting.py](../../src/factory/hosting/domain/hosting.py) (`factory.hosting.domain.hosting`). They are frozen, forbid unknown keys, and hold aware datetimes converted to UTC.

    PullRequestView(number, branch, title, state, draft, merge_commit, url)
    PullRequestComment(id, author, body, created_at, by_factory, key)

- `state` is `open`, `closed` or `merged`.
- `merge_commit` is a 40-character lowercase hex commit id exactly when the state is `merged`, otherwise `None`.

### The marker and the post key

Every post the factory makes ends with two lines, so that a repeat or a restart posts nothing. The first is the marker `<!-- factory -->`. The second is a key comment made from the recorded [journal](glossary.md) entry's number. The code is in the same module as the models.

    render_post(text: str, key: PostKey) -> str
    parse_post_key(body: str) -> PostKey | None

- The key comment is `<!-- factory key=<work item>:<kind>:<n> -->`, for example `<!-- factory key=F0001-S0001:question:7 -->`.
- `n` is lowercase hex and not empty.
- `kind` is one of `question`, `attempts_cap`, `round_cap`, `crash_cap`, `send_back`, `stall`, `expiry`, `correction`, `error`, `cost_table`.
- `render_post` gives `text` without trailing whitespace, a blank line, the marker, and the key comment. Nothing follows.
- `parse_post_key` reads only the last non-blank line, which must be exactly a valid key comment. Trailing whitespace and `\r` are ignored. Anything else gives `None`.
- `PullRequestComment.from_body` sets `by_factory` when the body contains the marker, whoever the author is, and `key` to the parsed key when it is by the factory.

Why: see [decisions.md](../decisions.md). See also: *Asking the human* in `pipeline.md`.

## The git wrapper

Git is reached only through the abstract base class `Git` in [git.py](../../src/factory/hosting/application/git.py) (`factory.hosting.application.git`) and its one implementation `GitCli` in [git_cli.py](../../src/factory/hosting/adapters/git_cli.py), which inherits it. Every command goes through `run_process` (see [shared.md](shared.md)); no other module starts git. The models and the pure rules are in [git.py](../../src/factory/hosting/domain/git.py) (`factory.hosting.domain.git`).

    GitCli(directory, options=None)
    GitOptions(identity, environment, kill_points, executable, time_limit)

`GitCli` works in `directory`. `options` is a `GitOptions`, and `None` means `GitOptions()`. The wrapper reads, writes the first things (clone, checkout, commit, push), deletes and merges branches, and restores the checkout (reset, revert, move).

- The operations are 22. [test_git_interface.py](../../tests/hosting/application/test_git_interface.py) checks that the interface has exactly these and that `GitCli` has each. They are listed in the *Reference*.
- Any failure of a command (non-zero exit, cannot be started, `time_limit` reached) is a `GitError`, unless an operation says otherwise.
- A missing ref or path is told apart from a failure by exit status and by `ls-tree -z` listings, never by git's wording.
- Rename detection is off everywhere, so a rename is a deletion of the old path plus an addition of the new one.
- Git is isolated: no user or system configuration reaches it, and the identity comes from the options (see *Identity and isolation* below).
- The three reads `changed_paths`, `status` and `work_tree_id` describe what the checkout holds. Nothing is decided from them without the remote. The [tick](glossary.md) looks at `status()` before it restores the checkout.

`wiring.py` fills `identity` from the [instance](glossary.md) settings `GIT_USER_NAME` and `GIT_USER_EMAIL`. It fills `environment` with `git_environment()`: the credential helper for the factory's own pushes, `core.hooksPath` set to the null device and `core.fsmonitor` set to `false`. The helper reads the token file. The token itself is never in the environment, so the agent run never receives it.

The helper is [git-credential-factory](../../operator/vm/git-credential-factory) (`operator/vm/git-credential-factory`, shell). It answers `get` only for the host of `FACTORY_REPOSITORY_URL` when that variable is set, and prints nothing and exits 1 otherwise. Why: the code may come from another repository on another host ([setup.sh](../../operator/vm/setup.sh) with `--code-url`), and the project's token must not reach it. The exact comparison is in the *Reference*.

See also: *The take* in [machine.md](machine.md), which uses `ignored`, and *The take's rule* in `pipeline.md`, which uses `revert_paths`.

### Pushing

Push never forces. It runs `git push --porcelain --set-upstream origin refs/heads/<branch>`. The outcome is a value, because the caller decides what a refusal means.

    GitCli.push(branch) -> PushOutcome
    GitCli.last_push_output() -> str
    push_reason(output: str) -> str
    push_is_retried(outcome: PushOutcome, output: str) -> bool

- `"pushed"`: git exited 0. Afterwards `origin/<branch>` in the checkout is the pushed commit.
- `"rejected"`: the remote refused the update, a non-fast-forward or a remote hook that declined it (git marks the ref with `!`).
- `"unreachable"`: exit 128 with `Could not read from remote repository`, `does not appear to be a git repository`, `unable to access` or `Could not resolve host` in the output.
- Any other failure, such as an unknown local branch, is a `GitError`. A tag of the branch's name does not count as that branch: `push("v1")` with a local tag `v1` and no local branch `v1` is a `GitError` and pushes nothing.
- `last_push_output()` returns git's whole output of the latest `push` or `delete_remote_branch` that failed (`""` before one). It is how git's own reason crosses the interface without changing the `PushOutcome` return type.
- `push_reason(output)` turns that output into a short reason; the *Reference* lists what it leaves out.
- `push_is_retried(outcome, output)` says whether a wait may cure the failure: `unreachable`, or `rejected` with `[remote rejected]` (a refusal by the server) in the output. A `[rejected]` with `non-fast-forward` or `fetch first` is never retried.
- `KillPoint.BEFORE_PUSH` is reached once per call, before git runs (between a commit and its push, so nothing reaches the remote). `KillPoint.AFTER_PUSH` is reached only after a push that returned `"pushed"`. A rejected or unreachable push reaches only the first. A `GitCli` without kill points pushes normally.

### Deleting and merging branches

A merge or a discard of a work item removes its branch from the remote and from the checkout. Preparing a stage merges the main branch into the work item's branch. Both return a value for the outcomes a caller must decide on, and raise `GitError` for the rest.

    GitCli.delete_remote_branch(branch) -> PushOutcome
    GitCli.delete_branch(branch) -> None
    GitCli.merge(ref, *, fast_forward_only=False) -> MergeOutcome

`delete_remote_branch` runs `git push --porcelain origin --delete refs/heads/<branch>`. It returns the push outcomes with these meanings.

- `"pushed"`: the branch is gone from the remote afterwards, also when it was already gone. Git exits 0 for a qualified name, so that is a plain success and the remote only warns. A tag of the same name on the remote is left alone.
- `"rejected"`: the remote refuses the deletion, for example a hook.
- `"unreachable"`: under the same conditions as `push`.
- A name git would refuse, such as `a..b`, is a `ValueError` before git runs (see *The argument and branch rules*). Any other failure is a `GitError`.
- After `"pushed"` the remote-tracking ref `origin/<branch>` is gone from the checkout too, even when the remote branch was already gone and the checkout held a stale one.
- It reaches no kill point.

`merge` merges `ref` into the checked-out branch and returns a `MergeOutcome`, decided from the ancestry of the two commits, not from git's messages.

- `"up_to_date"`: `ref` is already contained in `HEAD`. Nothing changes, also with `fast_forward_only`.
- `"fast_forwarded"`: `HEAD` is contained in `ref`. The branch moves to `ref` without a merge commit, also with `fast_forward_only`.
- `"not_fast_forward"`: the two have diverged and `fast_forward_only` is true. Nothing changes.
- `"merged"`: diverged without conflict. A merge commit with git's default message (no editor, unsigned), `HEAD` and `ref` as parents, and the identity of the options as author and committer.
- `"conflict"`: the merge conflicts. It is aborted before the call returns, so `HEAD`, the index and the work tree are as they were and no merge is in progress.
- An unknown `ref`, and any other refusal that leaves no merge in progress (for example local changes the merge would overwrite), is a `GitError` and changes nothing.
- `delete_branch` deletes the local branch even when it is not merged. The checked-out branch is a `GitError` and stays. A branch that does not exist is no error and changes nothing.

Who uses them: preparing a stage merges the main branch into a [work item](glossary.md)'s branch. A merge or a discard deletes branches, remote and local.

### Restoring the checkout

These three make the checkout disposable: whatever a stage or a [crash](glossary.md) left behind can be put back.

    GitCli.reset_to(ref) -> None
    GitCli.revert_paths(commit, paths) -> None
    GitCli.move(source, destination) -> None

- `reset_to(ref)` resolves `ref` to a commit, runs `git reset --hard` on it, then `git clean --force -d`. Tracked files, staged or not, go back to `ref` and the current branch points at it. Untracked files and directories are removed. Ignored paths (a file named in `.gitignore`) stay.
- An unknown `ref` is a `GitError` and nothing changes. The ref is resolved first, so git only ever sees a commit id (`reset` takes no `--end-of-options`). An option-like `ref` is refused earlier by the argument rule.
- `revert_paths(commit, paths)` brings each path to its content at `commit`, in the work tree and in the index. A path that does not exist at `commit` (added later, only staged, or untracked) is deleted from both. A path that exists nowhere is skipped without an error. Paths that were not given are not touched.
- An unknown `commit` is a `GitError`. A path that is a directory is not supported: git then fails with a `GitError`.
- `move(source, destination)` creates the destination's parent folders and runs `git mv`. The move is staged as a rename, but `status()` and `changed_paths()` still show it as a deletion plus an addition.
- A `source` that is not tracked, or a `destination` that exists, is a `GitError`.

Who uses them: a [stall](glossary.md) or a crash reverts or resets. The tick resets the checkout to the remote. The take's restore of a broken work item is `revert_paths`. A merge or a discard moves the [story](glossary.md) file.

### The argument and branch rules

Three rules keep an argument from being read as an option or a refspec. They run in the domain, before git starts and before any kill point, so a refused call starts no process and changes nothing.

    check_repository_path(path: str) -> None
    check_git_argument(value: str) -> None
    check_branch_name(value: str) -> None

- `check_repository_path` serves `revert_paths` (every path) and `move` (both arguments). It raises `ValueError` for an empty path, an absolute path or one with a `..` segment, before anything is changed or created. So `revert_paths` changes no path of a call that holds one bad path, and `move` creates no folder outside the checkout. A path is relative to the repository, with forward slashes.
- `check_git_argument` serves every ref, branch, start point, commit and url. It raises `ValueError` for an empty value and for one that starts with `-`, because git would read it as an option (`push("--force")` would force-push). No git ref, branch name or remote url starts with a dash, so nothing valid is lost. A hyphen inside a name (`work-item/F0001-S0001`) is fine.
- `check_branch_name` serves `push` and `delete_remote_branch` instead, because `git push` reads its branch as a refspec. It refuses everything `check_git_argument` refuses, and the other cases in the *Reference*. The remote is untouched by a refusal.
- The local operations (`checkout`, `delete_branch`, `merge`, and the others) keep `check_git_argument`, because git reads no refspec there.
- The branch is also named `refs/heads/<branch>` on git's command line, as the source only, with no `:<dst>`. Without it git matches any ref of that name, so `delete_remote_branch("v1")` would delete a tag `v1` and `push("v1")` would push a local tag. With it a tag is never pushed or deleted as a branch.
- Inside an operation, git is read through the private `_resolve_unchecked`, `_is_ancestor_unchecked` and `_blob`, never through another public operation, so each argument is checked once.

Examples of paths:

```text
accepted:  a/b.txt
refused:   ../x      a/../../x      (empty)      (absolute)
```

Why not `--end-of-options`, and why not an explicit `refs/heads/<b>:refs/heads/<b>` refspec: see `decisions.md`.

### Identity and isolation

Every call sets `GIT_AUTHOR_NAME`, `GIT_COMMITTER_NAME`, `GIT_AUTHOR_EMAIL` and `GIT_COMMITTER_EMAIL` from `options.identity`, over the process environment and `options.environment`. No user or system configuration can change it, and `commit.gpgsign` is ignored. A `GitCli` built without options commits as `factory <factory@noreply.invalid>`.

- The environment of a call is the process environment, then `options.environment`, then the identity, then `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL` set to the null device, and `LC_ALL=C`. The last three come last, so `options.environment` cannot lift them.
- `GitCli` also sets `GIT_CEILING_DIRECTORIES` to the working copy's parent, so git never looks for a repository above the working copy.
- `LC_ALL=C` keeps git's messages English. The push outcome `"unreachable"` and an already-deleted remote branch are recognised by them, and an operator's locale must not turn them into a `GitError`. It does not change how paths are read: the `-z` listings are the paths' bytes and `run_process` decodes them as UTF-8.
- Credentials reach git only through the environment (for example `GIT_ASKPASS`, or `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_<n>`, `GIT_CONFIG_VALUE_<n>`), never through global or system configuration, and never inside a URL, because git may print a URL.

Why: see `decisions.md`.

### Which part uses which operation

| Operation | Used by |
|---|---|
| `changed_paths` | the preflight and the make-based [project commands](glossary.md): the paths changed since a commit |
| `revert_paths` | the take: puts a deleted or unreadable work item back from the stage-start commit |
| `merge` | the stage's preparation: merges the main branch into the work item's branch |
| `ignored` | the take: which changed paths of the [dataset](glossary.md) the host's own ignore rules ignore (see *The take*, `machine.md`) |
| `status`, `reset_to` | the tick: looks at the checkout and resets it to the remote; `status` is also read by the claim and by the stall handling |
| `reset_to` | also the stage's preparation and the crash recovery: a stall or a crash |
| `delete_remote_branch`, `delete_branch`, `move` | the merge and the discard |
| `work_tree_id` | the known results: the key of a known project-command result is the tree the command would read |
| `fetch`, `remote_branches`, `resolve`, `show_file`, `list_files`, `is_ancestor`, `log`, `clone`, `checkout`, `commit`, `push` | the pipeline's reads and writes, used by the tick, the stages and the [claim](glossary.md), and `clone` by the checkout preparer |

### Testing with real git

Git is not faked. Tests use real git on a bare remote in `tmp_path`, and check results with plain git through `run_git`, not through other `GitCli` methods.

- The `remote` fixture is a bare repository with the [pipeline definition](glossary.md), the story form and one [feature](glossary.md) with one story on `main`.
- `make_remote` builds it once per session, once per pytest-xdist worker, as the `remote_template` fixture. Each test gets a copy of the whole folder, seed and bare repository, made by `copy_remote(template, root)` without a git process, so what a test pushes stays its own. A test that needs a remote of its own layout builds it with `make_remote`.
- `checkout` is a `GitCli` on a clone of it, with the identity `TEST_IDENTITY`.
- [git_support.py](../../tests/support/git_support.py) has the helpers: `run_git` (through `run_process`, same isolation, author `Test Author`), `write_executable` for a stand-in `executable`, and `remote_commit(remote, branch)`, which reads a branch of the bare remote with plain git and gives `None` when it is absent.
- The autouse fixture `reopened_tmp_path` in `tests/conftest.py` calls `reopen(tmp_path)` from [tmp_path_support.py](../../tests/support/tmp_path_support.py) after every test that uses `tmp_path`, after the test's own teardowns. It gives the owner read, write and search permission on every folder and read and write on every other entry, links not followed. So a test that closes a folder, or a mutant of the seal that closes `.git`, leaves nothing pytest cannot remove, and a test need not open what it closed for that reason.
- The `human` fixture (`HumanClone` in [human_clone.py](../../tests/support/human_clone.py)) is a second clone of `remote`, the writer a push test needs besides `checkout`. It is built with `TEST_IDENTITY` and drives `GitCli`. Every push it makes must return `"pushed"`.
- `human.start(path)` moves a story file from the [backlog](glossary.md) (`backlog/`) to `in-progress/` on `main`, commits and pushes.
- `human.push_file(branch, path, text)` writes the file on that branch (created from `origin/main` if the remote has none), commits and pushes.
- `human.merge(branch, method)` brings `origin/<branch>` into `main` and pushes it. `"merge"` makes a merge commit, `"squash"` makes one ordinary commit that leaves the branch tip outside the history of `main`, and `"rebase"` replays the branch's commits with no merge commit.

## Reference

Exact detail that the sections above summarise.

### The options of `GitCli`

| Field | Default | Meaning |
|---|---|---|
| `identity` | `GitIdentity(name="factory", email="factory@noreply.invalid")` | author and committer of the factory's commits; non-empty name and email. The default is `DEFAULT_GIT_IDENTITY` (`factory.hosting.domain.git`), the one place that spells it; `factory.shared.domain.settings` re-exports the same object, and an unset instance setting falls back to it |
| `environment` | `{}` | extra environment for git; each `GitOptions` has its own dict. `GitCli` adds `GIT_CEILING_DIRECTORIES` and `GIT_CONFIG_NOSYSTEM` after it, which no `environment` can lift |
| `kill_points` | `None` | reached by `push` |
| `executable` | `"git"` | the program to run (tests give a stand-in) |
| `time_limit` | `GIT_TIME_LIMIT` (5 minutes) | per command |

The models are frozen and forbid unknown keys.

The settings `FACTORY_CHECKOUT` and `FACTORY_STATE` (`CHECKOUT_VARIABLE`, `STATE_VARIABLE` in `factory.shared.domain.settings`) fill the fields `InstanceSettings.checkout` and `InstanceSettings.state_directory`. They default to `CHECKOUT_PATH` and `STATE_DIRECTORY`. A relative one is `SettingsInvalid(<variable>, "is not an absolute path")`, and the validator of `InstanceSettings` refuses it with a `ValidationError`. The settings of the [stage environment](glossary.md) (`FACTORY_DATASET`, `FACTORY_WORKSPACE`, `FACTORY_STAGE_IMAGE` and the others) are in *The settings and the wiring* in `machine.md`.

### The credential helper

`operator/vm/git-credential-factory` takes the host of `FACTORY_REPOSITORY_URL` (`https://`, `ssh://` or `[user@]host:path`, lower-cased, user and port removed) and the host of the request's `host=` line (lower-cased, port removed). It prints nothing and exits 1 unless they are equal, and also when the request has no `host=` line.

### The 22 operations of `Git`

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
| `push(branch)` | `PushOutcome`: `"pushed"`, `"rejected"` or `"unreachable"` |
| `last_push_output()` | git's whole output of the latest failed `push` or `delete_remote_branch`, `""` before one |
| `delete_remote_branch(branch)` | `PushOutcome` |
| `delete_branch(branch)` | `None` |
| `merge(ref, *, fast_forward_only=False)` | `MergeOutcome` |
| `reset_to(ref)` | `None`; `git reset --hard` then `git clean -fd` |
| `ignored(paths)` | `list[str]`: those of `paths` that the checkout's ignore rules ignore, in the order given; `[]` for no paths, without running git; a path that is absolute or holds a `..` segment raises `ValueError` before git runs. `git check-ignore --verbose --non-matching -- <paths...>`, one call per group of at most `IGNORE_GROUP` paths, which is 1,000. The option `-z` is not used, because it needs `--stdin`, which is not fed. It prints one line per path, in the paths' order: `<source>:<line>:<pattern><TAB><path>`, or `::<TAB><path>` for a path no rule matches and for a tracked path. A path is ignored when the text before the tab is not `::` and its pattern does not start with `!` (a negation). Exit status 0 and 1 are both answers; any other status, and a call that printed more or fewer lines than it had paths, is `GitError` |
| `revert_paths(commit, paths)` | `None` |
| `move(source, destination)` | `None` |
| `log(ref, *, since=None, path=None)` | `list[CommitInfo(commit, parents, subject, author, committed_at)]`: the commits reachable from `ref`, newest first, a commit always before its parents (a merge commit has two). `commit` and `parents` are full ids, `subject` is the first line of the message, `author` the author's name, `committed_at` the committer date in UTC. With `since`, only commits not reachable from it (`since == ref` gives `[]`); with `path`, only commits that changed that file or anything under that directory. An unknown `ref` or `since` is a `GitError` |
| `changed_paths(since)` | `list[ChangedPath(path, change)]`: the net difference between the commit `since` and the work tree, whether committed, staged, unstaged or untracked. Untracked files that are not ignored count, as `"added"`; ignored paths do not. A path added and deleted again, or changed and restored, is not listed. Sorted by path in plain string order. An unknown `since` is a `GitError` |
| `work_tree_id(left_out=())` | `TreeId` (`factory.hosting.domain.git`, 40 lower-case hex characters, the pattern of `CommitId`): the id of the tree a commit of the work tree would record now, less the paths that match `left_out` (`matches_any`, as for [write paths](glossary.md): case-sensitive, `*` also crosses `/`). Tracked files count with their content in the work tree, untracked files that are not ignored count, deleted and ignored files do not; a tracked file that `.gitignore` matches still counts, as in a commit. The tree is built in a temporary index, which is set through `GIT_INDEX_FILE` and removed afterwards. The index is a copy of the checkout's own, made with `shutil.copy2` so that it keeps the modification time. Git's racily-clean rule therefore applies to the copy as to the own index, and git rehashes a file changed in the tick of the last index write. The steps are `add --all`, then `update-index --force-remove --` for the left-out paths (literal paths, never pathspecs), then `write-tree`. The checkout's index, `HEAD`, refs and work tree stay as they are; the tree object itself is written to the object store. Any git failure is a `GitError` |
| `status()` | `WorkTreeStatus(branch, head, changes)`: `branch` is `None` when HEAD is detached, `head` is `None` in a repository without commits (`branch` then names the unborn branch). `changes` has one `ChangedPath` per path that differs from HEAD, staged, unstaged or untracked, listed once and sorted by path. A deleted path is `"deleted"`, a path HEAD lacks (untracked or newly staged, even if edited again) is `"added"`, anything else `"modified"`. Ignored paths are never listed |

### The result models

- `ChangedPath.change` is `"added"`, `"modified"` or `"deleted"` (`ChangeKind`); there is no `"renamed"`.
- The four result models (`ChangedPath`, `CommitInfo`, `WorkTreeStatus`, `RemoteBranch`, in `factory.hosting.domain.git`) are frozen and forbid unknown keys. `committed_at` must be timezone-aware, and commit ids are 40 lowercase hexadecimal characters.
- Two edge cases are not exact. A path removed from the index with `git rm --cached` but still on disk shows as `"modified"` in `changed_paths` even when its content is unchanged. Unmerged paths in `status()` are `"modified"`.

### What `push_reason` leaves out

`push_reason(output)` leaves out:

- git's advice lines: exactly `Please make sure you have the correct access rights`, exactly `and the repository exists.`, and any line that starts with `hint:`;
- the frame of the `--porcelain` summary: every line that is exactly `Done` and every line that starts with `To ` (`remote: Done` is kept);
- the summary line `PUSH_SUMMARY_PREFIX` (`error: failed to push some refs to `), matched on the stripped line. Any other `error:` line, and `remote: error: failed to push some refs to x`, is kept.

Of what is left, the last three non-empty lines are kept (stripped, every run of whitespace written as one space, joined with ` | `), and the whole is cut at the end to 300 characters.

### What `check_branch_name` refuses

Besides everything `check_git_argument` refuses, it refuses:

- a value that starts with `+`, which forces (`push("+main")` overwrites a diverged `main`);
- a value that contains `:`, which names another ref or deletes one (`push(":keep")` deletes `keep`, `push("HEAD:refs/heads/other")` creates `other`);
- a value that contains `*`, a pattern that pushes every matching branch, or none;
- the whole values `HEAD` and `@`, because git pushes the checked-out branch under its own name;
- anything `git check-ref-format --branch` would refuse, applied in the domain without calling git: `^`, `~`, `?`, `[`, `\`, space and control characters, `..`, `@{`, a leading, trailing or doubled `/`, a trailing `.`, and a component that starts with `.` or ends with `.lock`. `push("^main")` is a negative refspec that pushes nothing yet exits 0.

A plus or an `@` inside a name (`a+b`, `a@b`) and `feature/HEAD` are fine. The refusal is a `ValueError` before git and before `BEFORE_PUSH`. It refuses a name git itself allows (`+main`); the factory's names (`main`, `work-item/<id>`) never take that form.

### Where `check_git_argument` applies

`resolve(ref)`, `show_file(ref, …)`, `list_files(ref, …)`, `is_ancestor` (both), `log` (`ref`, and `since` when given), `changed_paths(since)`, `clone(url)`, `checkout` (`branch`, and `start_point` when given), `push`, `delete_remote_branch`, `delete_branch`, `merge(ref)`, `reset_to(ref)` and `revert_paths(commit, …)`. `push` and `delete_remote_branch` use `check_branch_name`, which includes it.
