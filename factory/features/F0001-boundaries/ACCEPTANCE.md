---
stage: accept
pr: 15
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0001-S0001, F0001-S0002, F0001-S0003, F0001-S0004, F0001-S0005, F0001-S0006, F0001-S0007, F0001-S0008, F0001-S0009, F0001-S0010, F0001-S0011, F0001-S0012, F0001-S0013, F0001-S0014]
---
# Acceptance of Boundaries

## Verdict

**accepted with drafts.** Every scope item has a story. The feature demo takes one work item through all four boundaries against real git, real make and a stand-in `claude`, and it is green. `make check` is green (99 % branch coverage). There is one finding of weight. `GitCli.push("--force")` really force-pushes the checked-out branch and overwrites another writer's commit, because git reads a branch name that starts with `-` as an option. That contradicts "a push is never forced" (FEATURE.md decision 10, `docs/decisions.md`). I did not rate it a broken promise of the feature, for two reasons: no caller exists yet, and the branch names the factory will build cannot start with `-`. F0001-S0015 should still be promoted before any feature that pushes. If you read the documented guarantee as the promise, refuse this pull request instead.

## 1 Scope

None missing. I checked each scope item against the archived stories:

- Kill points and the error root: S0001.
- Hosting interface, DTOs, marker and key: S0002.
- PyGithub client with one error type: S0003.
- The one fake: S0014.
- Git wrapper: S0004 (process), S0005, S0006, S0011, S0012 and S0013. Together they give all nineteen operations, and `tests/application/test_git_protocol.py` pins that set.
- Project commands and the make class with a generic `CheckResult`: S0007.
- Agent-runtime interface, DTOs and fake: S0008.
- `claude -p` with resume, `time_limit` and version: S0009 and S0010.
- Boundary searches:
  - `tests/test_hosting_search.py`
  - `tests/test_process_search.py`
  - `tests/test_wrapper_search.py`
  - `tests/test_make_search.py`
  - `tests/test_no_untyped_dicts.py`
  - `tests/test_hosting_fake_search.py`

No story goes outside the scope. The out-of-scope lines hold:

- The guard settings are only written, and the hook command `factory-guard` does not exist.
- `os_user` is accepted and not used.
- `factory.entry` is empty, so there is no wiring.
- There are no kill-point recovery tests.

The Goal's "done when" conditions are all met (section 2, steps 1–9). One remark on breadth: the `HostingService` protocol has ten operations. R10 lists only seven of them; the other three (`find_open_pull_request`, `set_draft`, `set_description`) were added by S0002 from R22 and kept thing 11. They are justified in the story, but they widen R10, so they are listed under 6.

## 2 Feature demo

**Green.** One work item goes through every boundary: real git against a bare remote in a temp directory, a real Makefile through make, and `claude -p` replaced by a stand-in executable, because a real call needs the operator's login. Three of the four kill points are armed and fire. The fourth, `after-push`, is covered by S0006's tests. The last step reruns the boundary searches over `src/factory`.

The script below was saved as `/tmp/fdemo/demo.py` and run from the repository root with `uv run python /tmp/fdemo/demo.py`:

```python
import ast, json, sys, tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from github import GithubException

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.process import ProcessRequest, run_process
from factory.adapters.pygithub_hosting import PyGithubHostingService
from factory.application.agent_runtime import AgentRuntime
from factory.application.git import Git
from factory.application.hosting import HostingService
from factory.application.project_commands import ProjectCommands
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.errors import HostingServiceError
from factory.domain.git import GitOptions
from factory.domain.hosting import PostKey
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints

root = Path(tempfile.mkdtemp())
kp = KillPoints()
run_process(ProcessRequest(argv=["git", "init", "-q", "--bare", "-b", "main", str(root / "remote.git")], cwd=root))
url = str(root / "remote.git")

# 1 git: the factory's checkout and the human's clone, real git, real bare remote
factory: Git = GitCli(root / "factory", GitOptions(kill_points=kp))
human: Git = GitCli(root / "human")
factory.clone(url)
(root / "factory/Makefile").write_text("check:\n\t@echo 'check: green'\n")
(root / "factory/README.md").write_text("base\n")
factory.commit("seed")
print("1 seed push:", factory.push("main"), factory.remote_branches()[0].name)
human.clone(url)

# 2 the work item's branch, an agent run through `claude -p` (a stand-in executable)
branch = "work-item/F0001-S0001"
factory.checkout(branch, start_point="origin/main")
claude = root / "bin/claude"
claude.parent.mkdir()
claude.write_text(f"""#!{sys.executable}
import json, pathlib, sys
if sys.argv[1:] == ["--version"]:
    print("2.1.289 (Claude Code)"); sys.exit()
pathlib.Path("feature.txt").write_text("built by the agent\\n")
print(json.dumps({{"subtype": "success", "is_error": False, "num_turns": 4, "total_cost_usd": 0.42,
  "usage": {{"input_tokens": 100, "output_tokens": 20}},
  "structured_output": {{"decision": "review", "entry": "built feature.txt"}}}}))
""")
claude.chmod(0o755)
runtime: AgentRuntime = ClaudeCodeRuntime(str(claude), root / "state", kp)
agent = AgentDefinition(name="coder", model="opus", tools=["Edit"], budget_usd=Decimal("2"), instructions="Build it.")
request = AgentRunRequest(agent=agent, prompt="go", allowed_decisions=["review", "question"],
                          time_limit=timedelta(seconds=30), working_directory=root / "factory")
result = runtime.run(request)
print("2 agent:", runtime.version(), result.end_reason, result.decision, result.turns, result.cost_usd,
      result.tokens.input if result.tokens else None, sorted(p.name for p in (root / "state").iterdir()))

kp.arm(KillPoint.AGENT_RUN)
(root / "factory/feature.txt").unlink()
try:
    runtime.run(request)
except InjectedKill as kill:
    print("2 killed:", kill, "| write on disk:", (root / "factory/feature.txt").exists(),
          "| run files left:", list((root / "state").iterdir()))

# 3 the project's check through make
commands: ProjectCommands = MakeProjectCommands(root / "factory")
check = commands.run("check", time_limit=timedelta(seconds=30))
print("3 check:", check.status, check.exit_status, repr(check.last_line))

# 4 commit and push, with a crash injected between the commit and its push
print("4 changed:", [(c.path, c.change) for c in factory.changed_paths("origin/main")])
commit = factory.commit("feature")
kp.arm(KillPoint.BEFORE_PUSH)
try:
    factory.push(branch)
except InjectedKill as kill:
    factory.fetch()
    print("4 killed:", kill, "| remote has:", [b.name for b in factory.remote_branches()])
print("4 rerun:", factory.push(branch), factory.resolve(f"origin/{branch}") == commit)

# 5 the pull request on the fake, a post killed after it landed, the rerun posts nothing
hosting: HostingService = FakeHostingService(kp)
pull = hosting.create_pull_request(branch, "F0001-S0001", "story", draft=True)
key = PostKey(work_item="F0001-S0001", kind="question", n="1")
kp.arm(KillPoint.AFTER_POST)
try:
    hosting.post_comment(pull.number, "Which option?", key)
except InjectedKill as kill:
    print("5 killed:", kill)
print("5 rerun:", hosting.post_comment(pull.number, "Which option?", key),
      [(c.author, c.by_factory) for c in hosting.list_comments(pull.number)])
hosting.set_labels(pull.number, ["stage:review"])
hosting.set_draft(pull.number, False)

# 6 the human moves main meanwhile (a clean merge), and pushes a conflicting branch
(root / "human/README.md").write_text("base\nhuman line\n")
human.commit("human edit")
human.push("main")
factory.fetch()
print("6 merge main:", factory.merge("origin/main"))
human.checkout("scratch", start_point="origin/main")
(root / "human/feature.txt").write_text("the human's version\n")
human.commit("conflicting edit")
human.push("scratch")
factory.fetch()
print("6 merge scratch:", factory.merge("origin/scratch"), factory.status().changes)
print("6 push:", factory.push(branch))

# 7 the human merges the pull request; the factory sees it and cleans up
human.fetch()
human.checkout("main")
print("7 human merge:", human.merge(f"origin/{branch}"), human.push("main"))
fake = hosting  # the fake's test operations act as the human
assert isinstance(fake, FakeHostingService)
fake.merge_by_human(pull.number, human.resolve("HEAD") or "")
merged = hosting.get_pull_request(pull.number)
factory.fetch()
print("7 pull request:", merged.state, merged.draft, fake.labels(pull.number),
      factory.is_ancestor(commit, merged.merge_commit or ""), repr(factory.show_file("origin/main", "feature.txt")))
print("7 log:", [c.subject for c in factory.log("origin/main", since=commit)])
factory.checkout("main")
print("7 delete:", factory.delete_remote_branch(branch), factory.delete_remote_branch("scratch"))
factory.delete_branch(branch)
(root / "factory/junk.txt").write_text("left by a crash\n")
factory.reset_to("origin/main")
st = factory.status()
print("7 after reset:", st.branch, st.head == merged.merge_commit, st.changes, [b.name for b in factory.remote_branches()])

# 8 the PyGithub client: every failing call is the one HostingServiceError (no network here)
class Repo:
    def get_pull(self, number: int) -> None:
        raise GithubException(503, {"message": "unavailable"}, None)
try:
    PyGithubHostingService(Repo()).get_pull_request(1)
except HostingServiceError as error:
    print("8 pygithub:", type(error).__name__, error.operation, error.detail)

# 9 the boundaries hold: who imports what, who names which tool
def offenders(test):
    hits = []
    for path in sorted(Path("src/factory").rglob("*.py")):
        tree = ast.parse(path.read_text())
        if any(test(node) for node in ast.walk(tree)):
            hits.append(path.name)
    return hits
def imports(name):
    return lambda n: (isinstance(n, ast.Import) and any(a.name.split(".")[0] == name or a.name == name for a in n.names)) or (isinstance(n, ast.ImportFrom) and (n.module or "").startswith(name))
print("9 subprocess:", offenders(imports("subprocess")))
print("9 github:", offenders(imports("github")))
print("9 run_process:", offenders(imports("factory.adapters.process")))
print("9 'make':", offenders(lambda n: isinstance(n, ast.Constant) and n.value == "make"))
print("9 'git':", offenders(lambda n: isinstance(n, ast.Constant) and n.value == "git"))
```

Output (exit 0):

```
1 seed push: pushed main
2 agent: 2.1.289 completed review 4 0.42 100 []
2 killed: injected kill at agent-run | write on disk: True | run files left: []
3 check: passed 0 'check: green'
4 changed: [('feature.txt', 'added')]
4 killed: injected kill at before-push | remote has: ['main']
4 rerun: pushed True
5 killed: injected kill at after-post
5 rerun: already_posted [('factory', True)]
6 merge main: merged
6 merge scratch: conflict []
6 push: pushed
7 human merge: fast_forwarded pushed
7 pull request: merged False ['stage:review'] True 'built by the agent\n'
7 log: ["Merge remote-tracking branch 'origin/main' into work-item/F0001-S0001", 'human edit']
7 delete: pushed pushed
7 after reset: main True [] ['main']
8 pygithub: HostingServiceError get_pull_request 503 {"message": "unavailable"}
9 subprocess: ['process.py']
9 github: ['pygithub_hosting.py']
9 run_process: ['claude_runtime.py', 'git_cli.py', 'make_commands.py']
9 'make': ['make_commands.py']
9 'git': ['git_cli.py', 'git.py']
```

Every line is what the feature promises:

- A crash before the push leaves the remote untouched, and the rerun pushes.
- A crash after a post leaves the post in place, and the rerun posts nothing.
- An agent killed by `agent-run` leaves its writes on disk and no run files behind.
- A conflict is aborted with a clean work tree.
- The literal `"git"` in `domain/git.py` is only the default of `GitOptions.executable`, not a call.

**A second walk-through found the force push.** It ran against the same entry points, through a script saved as `/tmp/fdemo/force.py`. Two clones diverge on `main`, and the factory's clone pushes:

```
plain push: rejected
push('--force'): pushed
human's commit still on remote: ["factory's, diverged", 'one']
```

The human's commit is gone from the remote. `GitCli.push` builds `git push --porcelain --set-upstream origin <branch>` (`src/factory/adapters/git_cli.py:266`) and git reads `--force` as its option. I only reproduced the push case. By reading the code, these also pass a caller's string where git accepts options:

- `delete_remote_branch` (`:275`)
- `checkout` (`:248`, `:250`)
- `delete_branch` (`:287`)
- `clone` (`:242`, the url)
- `show_file` and `list_files` (the `ls-tree` ref)
- `is_ancestor` (`merge-base`)

`log`, `changed_paths` and `merge` already use `--end-of-options`; `reset_to` and `revert_paths` resolve the ref first. The S0012 reviewer saw this and noted it as harmless; the force case shows it is not. Draft F0001-S0015.

## 3 Mutation score

**Not run.** The project has no `mutants` target, and `docs/decisions.md` ("No `mutants` target, no mutmut") records that on purpose. As the nearest substitute I read what `make check`'s branch coverage leaves uncovered (99.00 %, 7 lines and 3 partial branches). I also collected every behaviour that a story log names as untested. Grouped by module:

- **`claude_runtime`, the resumed sums:**
  - `_add` and `_add_tokens` (lines 237, 245) are never exercised with a first call that reported measures and a second that reported none. A mutant that returns `second` there would survive.
- **`claude_runtime`, failing sides:**
  - The resume skipped for lack of time (line 350).
  - A run file that cannot be written into an existing state directory (lines 371–372).
  - A reply with a negative `num_turns` or token count. I reproduced it: `run` raises a raw `pydantic_core.ValidationError` instead of returning `died`. That breaks FEATURE.md decision 12, which says a dead run is a result and not an exception.
  - Draft F0001-S0016 covers the sums and the negative reply. The two timing and permission branches are left out, because they cannot be tested without sleeps or root-sensitive permissions.
- **`git_cli`:**
  - An unmerged (`u`) porcelain entry in `status()` (line 109).
  - A `status` header that is absent (line 120).
  - A log listing without a trailing NUL (65→67).
  - The first is a documented behaviour with no test. The other two are defensive parsing.
- **Failing sides named in logs but never tested:**
  - `MakeProjectCommands.run("check\n")` (S0007; the code was fixed with `fullmatch`, but there is no test).
  - `GitCli.move` with an unsafe *source* (S0013; only the destination is tested).
  - `FakeHostingService.delete_comment` with the id of another pull request's comment (S0014).
  - Draft F0001-S0017 pins these and the unmerged `status()` entry.

## 4 What the stories noticed

Every "noticed but not touched" item, reviewer remark and documenter note from the fourteen logs, each with where it stands now:

- **S0001.** The intake gap (arming one point leaves an armed other point) was closed by criterion 16. Nothing open.
- **S0002.** A `PullRequestComment` built directly does not check `by_factory` and `key` against `body`. Mitigated: both implementations build through `from_body`, and the project guide says to. No draft.
- **S0004.** After the kill, the second `communicate()` is unbounded, and a grandchild that holds stdout makes a normal exit wait. Both are documented as known limits in the project guide. No draft.
- **S0005.**
  - `merge_stderr=True` mixes git warnings into output that `remote_branches` and `resolve` parse. Nothing has been observed. No draft.
  - `RemoteBranch` is not frozen. It is the only result model that is not, which is minor. No draft; listed for the human.
- **S0006.** A branch created from `origin/main` tracks `origin/main` until its first push. Harmless. No draft.
- **S0007.** No test for `"check\n"`. F0001-S0017.
- **S0009.** A reply with a negative number gives a raw `ValidationError`. Reproduced. F0001-S0016.
- **S0010.**
  - The no-time-left resume branch is untested (section 3).
  - `version()` runs in the process's current directory, which the Interface does not name.
  - The operator guide names no pinned `claude` version. Under 6.
- **S0011.** `git rm --cached` of an unchanged file shows as `modified` in `changed_paths`, and unmerged paths show as `modified` in `status()`. Both are documented. The second is pinned by F0001-S0017; the first is under 6.
- **S0012.**
  - `delete_remote_branch` and `push` pass the branch without `--end-of-options`. **Not harmless: it allows a force push.** F0001-S0015.
  - The "already deleted" and "unreachable" detection reads git's English text. `GitCli` sets no locale, so an operator whose environment selects translated git messages would get a `GitError` where `"unreachable"` or `"pushed"` is due. By reading, not reproduced. F0001-S0015 adds `LC_ALL=C`.
- **S0013.**
  - `revert_paths` of a directory path gives a `GitError` (documented).
  - No test covers `move` with an unsafe source. F0001-S0017.
  - The documenter could not name a user feature for eleven git operations. Under 6.
- **S0014.** `delete_comment` with another pull request's comment id is untested. F0001-S0017.
- **Process.** Three of the five human questions asked during the stories came from tests that could not pass `make check` once the code existed:
  - `assert f() is None` against `mypy --strict` (S0001).
  - A direct unknown-keyword constructor call (S0008).
  - High-entropy hex literals against `make secrets` (S0011).

  The tester stage cannot run `mypy` before the code exists. `CLAUDE.md`'s Tests section now carries all three rules, so this is closed.

## 5 Documentation as a whole

I read `README.md` and `docs/` from the top as a newcomer. Nothing contradicts the code in a way that would make a user act wrongly. Five things are stale or doubled:

1. **`docs/project-guide.md`, section *Kill points*:**
   - "This story built only the seam. A wrapper calls `kill_points.reach(point)` at its point in its own story; until then nothing reaches a point." This is false now: all four points are reached. It is also ticket language in the docs. S0006's documenter wrote that they had fixed it, but the sentence is still there.
   - The table says `AGENT_RUN` is reached "while an agent runs". The runtime sections say "after the last call and the result" and "after the writes". Someone writing F0011's crash tests needs the latter.
2. **`README.md`:**
   - The status sentence leaves out the project commands (the make class) entirely.
   - It describes the git wrapper as "reading, clone, checkout, commit and push", leaving out the branch, merge, reset, revert and move operations.
   - "Where to look next" still calls `docs/operator-guide.md` "not yet written".
3. **`docs/operator-guide.md`, intro:** "Nothing is built yet, so there is nothing to install or configure". S0007's documenter saw this and left it. The accurate statement is that there is no command to run yet.
4. **`docs/operator-guide.md`, *The agent runtime*:**
   - The last paragraph repeats the stall rule and the unknown cost of a timed-out run, which the paragraph before it already states.
   - It says the stall "stops the story", where `CLAUDE.md`'s vocabulary asks for "work item".
5. **No section is missing that this feature made necessary.**
   - Once F0001-S0015 lands, the push and argument rule needs a line in the git wrapper section. That is that story's own docs criterion.
   - Every example in the guide that I ran works: the fake hosting example via demo step 5, and the project-commands example via step 3.

Draft F0001-S0018 collects items 1–4. They are a handful of sentences, so you may prefer to fix them in a commit of your own and drop the draft.

## 6 Decisions taken for the human

FEATURE.md's nineteen decisions are all built as written. I checked each against the code, the demo and the guide, and each still stands for you to accept or revisit:

1. Kill points fire once, `after` counts from the arming, re-arming replaces.
2. `InjectedKill` is a `BaseException`.
3. Three domain modules are created partially here and finished in F0002.
4. A post's key comes from the last non-blank line only, and the marker alone, not the author, makes a comment the factory's.
5. The PyGithub client:
   - It gives a merge commit only when merged.
   - Only `GithubException` and `OSError` become `HostingServiceError`.
   - `set_labels` reads the label names internally, which sits beside R10's "labels are never read back". **Still open.**
6. The fake's numbering, url, dates and authors, and its leniency where GitHub would refuse.
7. Git ignores user and system configuration, has a 5-minute `time_limit`, reports a 30-line tail, and gets credentials only from the environment.
8. Edge rules for `show_file`, `list_files` and `run_process`.
9. The four suppression markers in `process.py`.
10. `GitOptions`, the default identity, and that a push is never forced. **The last is broken for an option-like branch: F0001-S0015.**
11. The `CheckResult` and make rules.
12. A dead run is a result, not an exception. **Broken for a reply with negative numbers: F0001-S0016.**
13. The `claude -p` flags, the resume message asking for `question`, and the resume budget rule.
14. The `changed_paths` and `status` semantics.
15. The branch, merge, reset and revert rules.
16. The split into fourteen stories.
17. `factory-guard` is found through the request's `PATH`, and no `HOME` is added. F0005 and F0010 must supply both.
18. The `claude -p` flags are unverified. That is a morning observation for F0010's preflight.
19. Unsourced defaults: the git `time_limit` of 5 minutes, `version()` at 30 s, and a minimum resume budget of 0.50.

Answers and defaults recorded in the story logs:

- **Your answers during the stories:**
  - S0001: tests call `reach` as a statement, and a criterion was added for an armed other point.
  - S0008: refused fields are tested through `type[BaseModel]`, with no `type: ignore`.
  - S0009: two criteria were added (the cache counts default to 0, and a denial's detail has sorted keys).
  - S0011: low-entropy hex literals in tests.
  - S0013: `move` follows `revert_paths`' path rule.
- **The hosting protocol is wider than R10's list** (section 1). `find_open_pull_request`, `set_draft` and `set_description` were added from R22 and kept thing 11. Accept, or say R10 should name them.
- **Taken by coders without asking:**
  - `checkout` uses `git switch --force-create`, which is equivalent to `checkout -B`.
  - Rename detection is off everywhere, so a rename is a deletion plus an addition.
  - `merge` decides from ancestry and `MERGE_HEAD`.
  - `delete_remote_branch` reads git's English "remote ref does not exist".
  - `version()` runs in the process's current directory with the inherited environment.
- **Left open by the stories, yours to decide:**
  - Which pinned `claude` version the operator guide should name (S0010 documenter).
  - Whether `git rm --cached` in `changed_paths` and unmerged paths in `status()` should stay `modified` or get exact kinds (S0011). F0001-S0017 pins the current `status()` behaviour, as documented.
  - Which feature uses each of eleven git operations (S0013 documenter). The guide says no story names one yet.
  - Whether `RemoteBranch` should be frozen like every other result model (S0005 coder).
- **Taken in this report, in the drafts:**
  - F0001-S0015 refuses option-like refs with `ValueError` rather than passing them after `--end-of-options`.
  - F0001-S0016 lets a negative `total_cost_usd` count as `died` too.
  - Both are marked for you to refine.

## 7 Slow checks

None. The Makefile has only `check` and its parts (lint, types, layers, sast, secrets, licenses, test). There is no image yet (`image/` does not exist), so there is no image scan or SBOM, and no `mutants` target (section 3). `make check` was run in full on this branch: `check: green`, 99.00 % branch coverage.

## 8 Cost

106 runs, 86.4 min, $25.39 for fourteen stories. That is about 7.6 runs and $1.81 per story, and the sum of the fourteen cost lines matches.

- **Most runs: S0001**, with 14 runs and $2.41. It needed two of your answers: the mypy-incompatible test, and the missing criterion for an armed other point. That meant two extra tester and coder rounds for a 60-line domain module.
- **Next: S0013**, with 11 runs and $2.03. That is the `move` path-rule question and its rework round.
- **Then S0008 and S0011**, with 9 runs each. Each had one question caused by a test that failed `make check` (`type[BaseModel]`; high-entropy literals).
- **The single-pass stories** cost 6 runs and $1.19–$2.27 each. The dearest of them is S0005, with 25 criteria and the first git fixtures.

No story stands out beyond what its questions explain. Four of the five extra-round causes were test conventions now written into `CLAUDE.md`, so later features should not pay them again.

## Proposed stories

- `drafts/F0001-S0015-git-option-like-arguments.md`: refuse a ref, branch, start point or url that starts with `-` before git runs, and run git with `LC_ALL=C`. This stops a caller-given name from turning into `--force` and keeps the English markers readable. The one finding of weight.
- `drafts/F0001-S0016-claude-reply-negative-measures.md`: a reply with negative turns, tokens or cost is `died` and not a raw `ValidationError`, and the sums of a resumed run are pinned when only the first call reported measures. Restores decision 12.
- `drafts/F0001-S0017-open-failing-sides.md`: tests for four built behaviours the stories named as untested: the make name with a newline, an unsafe `move` source, an unmerged `status()` entry, and the fake's `delete_comment` with another pull request's comment id. Kills the surviving branches of section 3 cheaply.
- `drafts/F0001-S0018-documentation-repair.md`: the stale kill-point paragraph and `AGENT_RUN` row, the README status sentence and link, the operator guide's intro and doubled paragraph. Optional if you fix them yourself.

## Log (append only)

1. acceptor: accepted with drafts; 4 drafts proposed; make mutants not run (no target, by decision)/—
   1 Scope: every scope item has a story and none goes outside the scope. The Goal's done-when conditions are all met. The hosting protocol is wider than R10's list (`find_open_pull_request`, `set_draft`, `set_description`), which is listed under 6.
   2 Feature demo: green. One work item went through real git with a bare remote, real make, a stand-in `claude` and the fake hosting service. The `agent-run`, `before-push` and `after-post` kill points fired. The rerun boundary searches found one module each for subprocess, github and make. A second walk-through found the one finding of weight: `GitCli.push("--force")` force-pushes and overwrote the human's commit, which contradicts "a push is never forced". Draft F0001-S0015.
   3 Mutation: no `make mutants` target (`docs/decisions.md`). The substitute reading covered 7 uncovered lines and 3 partial branches, plus untested sides named in the logs. A reply with negative measures makes `ClaudeCodeRuntime.run` raise a raw `ValidationError` (reproduced; breaks decision 12). Drafts F0001-S0016 and F0001-S0017.
   4 Noticed: about 20 items collected. These go to drafts: option-like branch names (S0012), English-only push markers with no locale set (S0012), negative measures (S0009), and four untested failing sides (S0007, S0011, S0013, S0014). The rest are documented limits or listed under 6.
   5 Docs: nothing misleads a user. Stale or doubled: the project guide's kill-point paragraph ("until then nothing reaches a point") and the `AGENT_RUN` row; the README status sentence (no project commands, half the git wrapper) and its "not yet written" link; the operator guide's intro and a repeated paragraph. Draft F0001-S0018, optional.
   6 Decisions: FEATURE.md's 19 decisions, with 10 and 12 broken at their edges. Also listed: five human answers, coder defaults (`switch --force-create`, renames off, English git markers, `version()` cwd), and open questions (pinned `claude` version, `rm --cached` and unmerged kinds, users of eleven git operations, frozen `RemoteBranch`, `set_labels` reading labels).
   7 Slow checks: none exist (no image, SBOM or mutants target). `make check` is green with 99.00 % coverage.
   8 Cost: 106 runs, 86.4 min, $25.39, about $1.81 per story. S0001 (14 runs) and S0013 (11 runs) stand out, from two answers and one answer with rework. Four of the five extra-round causes were test conventions, now in `CLAUDE.md`.
