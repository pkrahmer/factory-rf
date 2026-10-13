---
stage: done
pr: 23
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0001-S0001, F0001-S0002, F0001-S0003, F0001-S0004, F0001-S0005, F0001-S0006, F0001-S0007, F0001-S0008, F0001-S0009, F0001-S0010, F0001-S0011, F0001-S0012, F0001-S0013, F0001-S0014, F0001-S0015, F0001-S0016, F0001-S0017, F0001-S0018, F0001-S0019, F0001-S0020]
outcome: accepted
---
# Acceptance of Boundaries

## Verdict

**Accepted with drafts.** This is the third acceptance; the one story since the second, S0020, did what the second report asked. `push("+main")`, `push(":keep")`, `push("HEAD:refs/heads/other")`, a `*` pattern and `delete_remote_branch("+main")` are now refused before git and before `BEFORE_PUSH`, and "a push is never forced" holds in the feature demo. `make check` is green (99.49 % branch coverage) and the demo is green end to end.

What is left is smaller than in the last two rounds: nothing forces a push, and nothing loses a branch. Two edges remain, and neither has a caller yet. First, `delete_remote_branch("v1")` deletes a **tag** named `v1` and returns `"pushed"`. Second, `push("^main")`, `push("@")` and `push("HEAD")` return `"pushed"` although no `origin/^main`, `origin/@` or `origin/HEAD` exists afterwards, so the project guide's "afterwards `origin/<branch>` … is the pushed commit" is false there. Draft F0001-S0021 closes both. It needs your choice first, because one of its options is close to the alternative you rejected in decision 22 (section 6). You could also accept the feature and leave the draft unpromoted until F0007, which is the first feature that deletes remote branches.

## 1 Scope

**None missing.** The first acceptance mapped every scope item to S0001–S0014 and the second mapped S0015–S0019; both mappings still hold. S0020 stays inside the git wrapper's scope (R9, decision 22) and touches nothing listed under "Out of scope":

- `factory-guard` is still unbuilt;
- `factory.entry` is still empty;
- there are no kill-point recovery tests.

The Goal's "done when" conditions all hold (section 2):

- Each of the four boundaries is callable through its interface. The interfaces are abstract base classes with 19, 10, 1 and 2 operations.
- The hosting service and the agent runtime each have a fake.
- Git is tested against a real bare remote.
- Each kill point is armed and reached.
- The searches find each outside tool in one module.

The remark from both earlier acceptances stands: the hosting interface's ten operations are more than R10's seven (listed under 6).

## 2 Feature demo

**Green.** It is the second acceptance's walk-through: one work item goes through every boundary.

- Real git against a bare remote in a temp directory, with the operator's locale set to German.
- A real Makefile through make.
- The fake hosting service, and the PyGithub client against a failing stand-in.
- A stand-in executable in place of `claude -p`, because a real call needs your login.

Step 6b now also tries every refspec form S0020 refuses (`+main`, `:scratch`, `HEAD:refs/heads/other`, `refs/heads/x*`, and `delete_remote_branch` of `+main` and `main:x`), then pushes and deletes a branch named `a+b`, which must still work.

Saved as `/tmp/fdemo3/demo.py` and run from the repository root with `uv run python /tmp/fdemo3/demo.py`:

```python
import ast, inspect, json, os, sys, tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from github import GithubException

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
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

# 0 the four interfaces are ABCs and the six implementations inherit them
impls = [(GitCli, Git), (PyGithubHostingService, HostingService), (FakeHostingService, HostingService),
         (MakeProjectCommands, ProjectCommands), (ClaudeCodeRuntime, AgentRuntime), (FakeAgentRuntime, AgentRuntime)]
print("0 abc:", [inspect.isabstract(i) for i in (Git, HostingService, ProjectCommands, AgentRuntime)],
      all(issubclass(c, i) for c, i in impls),
      [len(i.__abstractmethods__) for i in (Git, HostingService, ProjectCommands, AgentRuntime)])

# 1 git: the factory's checkout (operator locale German) and the human's clone
os.environ["LC_ALL"] = "de_DE.UTF-8"
factory: Git = GitCli(root / "factory", GitOptions(kill_points=kp, environment={"LC_ALL": "de_DE.UTF-8"}))
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
import json, os, pathlib, sys
if sys.argv[1:] == ["--version"]:
    print("2.1.289 (Claude Code)"); sys.exit()
if os.environ.get("REPLY") == "negative":
    print(json.dumps({{"subtype": "error_max_budget_usd", "is_error": True, "num_turns": -1}})); sys.exit(1)
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
bad = runtime.run(request.model_copy(update={"environment": {"REPLY": "negative"}}))
print("2 negative budget reply:", bad.end_reason, bad.turns, bad.cost_usd, bad.tokens)

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

# 6b the force pushes the first two acceptances found: refused before git or a kill point
factory.checkout("main")
(root / "factory/README.md").write_text("diverged\n")
factory.commit("factory's, diverged")
before = kp.reached(KillPoint.BEFORE_PUSH)
print("6b plain push:", factory.push("main"))
for call in (lambda: factory.push("--force"), lambda: factory.delete_remote_branch("--all"),
             lambda: factory.checkout("--detach"), lambda: factory.reset_to("--hard"),
             lambda: factory.push("+main"), lambda: factory.push(":scratch"),
             lambda: factory.push("HEAD:refs/heads/other"), lambda: factory.push("refs/heads/x*"),
             lambda: factory.delete_remote_branch("+main"), lambda: factory.delete_remote_branch("main:x")):
    try:
        call()
    except ValueError as error:
        print("6b refused:", error)
factory.fetch()
print("6b remote main still the human's:", factory.log("origin/main")[0].subject,
      "| before-push reached by refusals:", kp.reached(KillPoint.BEFORE_PUSH) - before - 1,
      "| remote:", [b.name for b in factory.remote_branches()])
factory.checkout("a+b", start_point="origin/main")
print("6b plus inside a name:", factory.push("a+b"), factory.delete_remote_branch("a+b"))
factory.checkout("main")
factory.delete_branch("a+b")
factory.reset_to("origin/main")

# 7 the human merges the pull request; the factory sees it and cleans up
human.fetch()
human.checkout("main")
print("7 human merge:", human.merge(f"origin/{branch}"), human.push("main"))
fake = hosting
assert isinstance(fake, FakeHostingService)
fake.merge_by_human(pull.number, human.resolve("HEAD") or "")
merged = hosting.get_pull_request(pull.number)
factory.fetch()
print("7 pull request:", merged.state, merged.draft, fake.labels(pull.number),
      factory.is_ancestor(commit, merged.merge_commit or ""), repr(factory.show_file("origin/main", "feature.txt")))
factory.reset_to("origin/main")
print("7 delete:", factory.delete_remote_branch(branch), factory.delete_remote_branch(branch),
      factory.delete_remote_branch("scratch"))
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
    PyGithubHostingService(Repo()).get_pull_request(1)  # type: ignore[arg-type]
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
print("9 'claude':", offenders(lambda n: isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("claude")))
print("9 Protocol:", offenders(lambda n: isinstance(n, ast.Name) and n.id == "Protocol"))
```

Output (exit 0):

```
0 abc: [True, True, True, True] True [19, 10, 1, 2]
1 seed push: pushed main
2 agent: 2.1.289 completed review 4 0.42 100 []
2 negative budget reply: died None None None
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
6b plain push: rejected
6b refused: not a git ref, branch or url: '--force'
6b refused: not a git ref, branch or url: '--all'
6b refused: not a git ref, branch or url: '--detach'
6b refused: not a git ref, branch or url: '--hard'
6b refused: not a branch name git push takes literally: '+main'
6b refused: not a branch name git push takes literally: ':scratch'
6b refused: not a branch name git push takes literally: 'HEAD:refs/heads/other'
6b refused: not a branch name git push takes literally: 'refs/heads/x*'
6b refused: not a branch name git push takes literally: '+main'
6b refused: not a branch name git push takes literally: 'main:x'
6b remote main still the human's: human edit | before-push reached by refusals: 0 | remote: ['main', 'scratch', 'work-item/F0001-S0001']
6b plus inside a name: pushed pushed
7 human merge: fast_forwarded pushed
7 pull request: merged False ['stage:review'] True 'built by the agent\n'
7 delete: pushed pushed pushed
7 after reset: main True [] ['main']
8 pygithub: HostingServiceError get_pull_request 503 {"message": "unavailable"}
9 subprocess: ['process.py']
9 github: ['pygithub_hosting.py']
9 run_process: ['claude_runtime.py', 'git_cli.py', 'make_commands.py']
9 'make': ['make_commands.py']
9 'git': ['git_cli.py', 'git.py']
9 'claude': []
9 Protocol: []
```

Every line is what the feature promises:

- **Last time's finding is fixed.** None of the ten refused calls reached `BEFORE_PUSH`. The remote's `main` is still the human's commit, `scratch` is still there, and no `other` branch exists.
- **`a+b` still works.** A plus inside a name is pushed and deleted normally.
- **The rest is unchanged** from the second acceptance: the ABCs, the negative budget reply (`died`), the kill points, the English push outcomes under a German locale, and one module for each outside tool.

**A probe of the remaining push and delete edges found two left.** It uses the same entry points. Saved as `/tmp/fdemo3/probe.py`:

```python
import tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.adapters.process import ProcessRequest, run_process

root = Path(tempfile.mkdtemp())
run_process(ProcessRequest(argv=["git", "init", "-q", "--bare", "-b", "main", str(root / "remote.git")], cwd=root))
url = str(root / "remote.git")
factory, human = GitCli(root / "factory"), GitCli(root / "human")
factory.clone(url)
(root / "factory/a.txt").write_text("one\n"); factory.commit("one"); factory.push("main")
human.clone(url)
human.checkout("keep", start_point="origin/main"); human.push("keep")
run_process(ProcessRequest(argv=["git", "tag", "v1"], cwd=root / "human"))
run_process(ProcessRequest(argv=["git", "push", "-q", "origin", "v1"], cwd=root / "human"))
def refs():
    r = run_process(ProcessRequest(argv=["git", "for-each-ref", "--format=%(refname)"], cwd=root / "remote.git"))
    return r.stdout.split()
print("remote:", refs())
for name, call in [("push('^main')", lambda: factory.push("^main")),
                   ("push('@')", lambda: factory.push("@")),
                   ("push('HEAD')", lambda: factory.push("HEAD")),
                   ("push('main~0')", lambda: factory.push("main~0")),
                   ("push('refs/tags/v1')", lambda: factory.push("refs/tags/v1")),
                   ("delete_remote_branch('v1')", lambda: factory.delete_remote_branch("v1")),
                   ("delete_remote_branch('HEAD')", lambda: factory.delete_remote_branch("HEAD")),
                   ("delete_remote_branch('refs/heads/keep')", lambda: factory.delete_remote_branch("refs/heads/keep")),
                   ]:
    try:
        print(name, "->", call(), refs())
    except Exception as e:
        print(name, "->", type(e).__name__, str(e).splitlines()[0][:150])
```

Output (exit 0):

```
remote: ['refs/heads/keep', 'refs/heads/main', 'refs/tags/v1']
push('^main') -> pushed ['refs/heads/keep', 'refs/heads/main', 'refs/tags/v1']
push('@') -> pushed ['refs/heads/keep', 'refs/heads/main', 'refs/tags/v1']
push('HEAD') -> pushed ['refs/heads/keep', 'refs/heads/main', 'refs/tags/v1']
push('main~0') -> GitError git push --porcelain --set-upstream origin main~0 failed (exit 128): fatal: invalid refspec 'main~0'
push('refs/tags/v1') -> GitError git push --porcelain --set-upstream origin refs/tags/v1 failed (exit 1): error: src refspec refs/tags/v1 does not match any
delete_remote_branch('v1') -> pushed ['refs/heads/keep', 'refs/heads/main']
delete_remote_branch('HEAD') -> pushed ['refs/heads/keep', 'refs/heads/main']
delete_remote_branch('refs/heads/keep') -> pushed ['refs/heads/main']
```

What this shows:

- **A branch deletion deletes a tag.** `delete_remote_branch("v1")` removed `refs/tags/v1` from the remote and returned `"pushed"`. The cause is that `git push origin --delete v1` matches any ref named `v1`, not only a branch (`src/factory/adapters/git_cli.py:292`).
- **`"pushed"` without a matching `origin/<branch>`.** `push("^main")` is a negative refspec, so git pushes nothing and exits 0. `push("@")` and `push("HEAD")` push the checked-out branch under its own name. All three return `"pushed"`, yet no `origin/^main`, `origin/@` or `origin/HEAD` exists afterwards, against the project guide's meaning of `"pushed"`.
- **Pushing a tag as a branch.** A second probe (`/tmp/fdemo3/probe2.py`) showed that `push("v1")`, with `v1` a local tag and no local branch `v1`, returns `"pushed"` and leaves no `origin/v1` behind.
- **The cases that fail are harmless.** `main~0` and other names git refuses come back as a `GitError` from git itself, which is safe.

The same second probe also checked the fix the draft proposes. `git push --porcelain origin --delete refs/heads/v1` exited 0 ("deleting a non-existent ref") and left the tag `refs/tags/v1` alone. And `git check-ref-format --branch` (git 2.39.5) refuses `HEAD`, `^main`, `main~0`, `a..b`, `x.lock`, `a b` and `a@{1}`, while it accepts `@` (it expands `@` to the current branch) and `+main`.

Nothing here forces a push or deletes a branch that was not named, and the factory's own names (`main`, `work-item/<id>`) never take these forms. That is why the verdict does not rest on it. Draft F0001-S0021.

## 3 Mutation score

**Not run.** There is no `mutants` target, and `docs/decisions.md` ("No `mutants` target, no mutmut") makes that a deliberate choice.

- **A hand sample was denied again.** I tried ten hand mutants of S0020's code on a copy of the repository under `/tmp`, and the session refused the command, as it did in the second acceptance. I did not retry.
- **Reading the tests instead.** I went through the mutants I would have run against S0020's tests (`tests/domain/test_git.py`, `tests/adapters/test_git_cli_arguments.py`):
  - Removing the `+`, `:` or `*` check is killed by `"+main"`, `":main"` and `"refs/heads/x*"`.
  - `startswith("+")` → `"+" in value` is killed by the accepted `"a+b"`.
  - `":" in value` → `startswith(":")` is killed by `"main:other"`.
  - Dropping the inner `check_git_argument` call is killed by `""` and `"-x"`.
  - Moving the check after `_reach(BEFORE_PUSH)` is killed by criterion 3's count of 0.
  - `delete_remote_branch` going back to `check_git_argument` is killed by criterion 6.
  - `delete_branch` switching to `check_branch_name` is killed by criterion 8.
  - **One would survive:** `"*" in value` → `value.endswith("*")`. The only `*` case is `refs/heads/x*`, and no wrapper-level `*` test exists (intake accepted that). It goes into F0001-S0021 as one row of its refusal table (`x*y`).
- **Coverage is the substitute.** It is unchanged at 99.49 %. The same four lines and three partial branches are uncovered; only the line numbers moved, because S0020 added an import line to `git_cli.py`:
  - `claude_runtime.py:360`: the resume skipped when no time is left.
  - `claude_runtime.py:381–382`: a run file that cannot be written.
  - `git_cli.py:123`: a porcelain entry kind other than `?`, `1` or `u`.
  - `git_cli.py:68->70`: a log listing without a trailing NUL.

  All of them are deliberate (timing, permissions) or defensive parsing. None is a missing criterion.
- **One group without a failing side:** push and delete arguments that git reads as something other than a branch: `^`, `@`, `HEAD`, a tag name (section 2, F0001-S0021).

## 4 What the stories noticed

The only new log is S0020's. For S0001–S0019, see the first two acceptances; their items are fixed, carried below, or listed under 6.

- **Intake** accepted a story with no wrapper-level `*` test. That leaves the one surviving mutant from section 3, which goes into F0001-S0021.
- **Tester** wrote criterion 8's test (`delete_branch` of `+x` and `x:y`) knowing it would already pass. It guards against `check_branch_name` spreading to the local operations. That is a good guard, nothing to do.
- **Coder** had nothing noticed and no refactor.
- **Reviewer** made no remarks beyond the findings.
- **Documenter** noted that "pushed when the branch is gone from the remote" became true for `+x`, because that call is now refused. The remaining exceptions to it are a tag name and `HEAD` (section 2).
- **Still open from earlier acceptances, for you (under 6):**
  - `RemoteBranch` is still the only result model that is not frozen (`src/factory/domain/git.py:23`).
  - `set_labels` reads label names.
  - The pinned `claude` version is unnamed.
  - `version()` runs in the current directory.
  - The test files `tests/application/test_git_protocol.py` and `test_hosting_protocol.py` still carry "protocol" in their names.
  - `merge` checks its ref twice.

## 5 Documentation as a whole

I read `README.md`, `docs/operator-guide.md`, `docs/project-guide.md` and `docs/decisions.md` from the top.

- **S0020's text is consistent.** The new decision entry ("A pushed branch is never read as a refspec") and the project guide's branch rule agree with each other, with the earlier option-like-values entry, and with the code. The demo's step 6b confirms every example they give (`+main`, `:keep`, `HEAD:refs/heads/other`, `a+b`).
- **Two sentences of the project guide are false at the edges of section 2.** No user acts on them wrongly yet, because the wrapper has no caller.
  1. *The git wrapper*: "`"pushed"`: git exited 0; afterwards `origin/<branch>` in the checkout is the pushed commit." This is false for `push("^main")`, `push("@")`, `push("HEAD")` and `push("<a tag>")`.
  2. *Deleting and merging branches*: "`"pushed"` when the branch is gone from the remote afterwards." This is true literally, but `delete_remote_branch("v1")` also deletes a tag `v1`, which nothing in the documentation warns about.

  F0001-S0021's docs criterion repairs both together with the fix.
- **Minor items carried over a second time, with no draft:**
  - the WE6.3 planning tag in the operator guide;
  - the project guide's intro, "until then `CLAUDE.md` holds the rules", which is stale for a 355-line guide;
  - the README's "(partly written)".

  These are each one line, best fixed by your own commit or by the next documenter that touches those files.
- **No missing section.** Nothing this feature made necessary is missing, and no example I ran fails.

## 6 Decisions taken for the human

FEATURE.md's 22 decisions are built as written; the demo exercises 1, 2, 4, 7, 10, 12, 13, 15, 20, 21 and 22 directly. Decision 22 (refuse `+`, `:` and `*` rather than push an explicit refspec) is built by S0020, including the `*` that the pre-check added.

Taken in S0020 without asking: the coder made `check_branch_name` call `check_git_argument` rather than repeat its checks, so it stays "one rule with a stricter push-side extension". No story log since the second acceptance records an answer from you.

New, for F0001-S0021. The draft names three options; I recommend A.

- **A. Branch names only, and qualified refs.** Extend `check_branch_name` to git's branch-name rules plus `HEAD` and `@`. Have `push` and `delete_remote_branch` name `refs/heads/<branch>` on the command line (source only, no `:<dst>`), so that no tag is ever pushed or deleted as a branch. This comes close to the alternative you rejected in decision 22, but it is not the same: the refusal of `+`, `:` and `*` stays, and only the source is qualified, so `:keep` is still a `ValueError` and not a `GitError`.
- **B. Branch names only.** Extend the name rule, but do not qualify. A tag that shares a branch's name is still deleted, and the guide must say so.
- **C. Nothing in code.** Only document the edges, since the factory's own names never hit them.

Still open from the earlier acceptances:

- `set_labels` reads label names, beside R10's "never read back" (decision 5).
- The hosting interface is wider than R10's list (`find_open_pull_request`, `set_draft`, `set_description`).
- The pinned `claude` version, for the operator guide.
- Whether `git rm --cached` in `changed_paths` should get an exact kind.
- Whether `RemoteBranch` should be frozen.
- The unsourced defaults of decision 19: git's 5 minutes, `version()`'s 30 seconds, the 0.50 minimum for the resume.
- Decisions 17 and 18, which F0005 and F0010 must honour (`PATH`, `HOME`, the preflight probe of the flags).
- Whether to rename `test_git_protocol.py` and `test_hosting_protocol.py`.

## 7 Slow checks

**None exist.** The Makefile has only `check` and its parts (lint, types, layers, sast, secrets, licenses, test). There is no `image/`, so no image scan and no SBOM, and no `mutants` target (section 3).

I ran `make check` in full on this branch before any change. It ended with `check: green`, at 99.49 % branch coverage.

## 8 Cost

**143 runs, 107.9 min, $31.78 for twenty stories**, about 7.2 runs and $1.59 per story.

- **S0001–S0019** cost 137 runs, 104.7 min and $30.60. The first two acceptances discussed them.
- **S0020** cost 6 runs, 3.2 min and $1.18: one pass through every stage with no rework round and no question. That is in line with S0015 ($1.50) and S0019 ($1.45), the other one-rule git and interface stories.
- **No story stands out.** The three acceptances themselves cost extra and are not in this sum.

## Proposed stories

- `drafts/F0001-S0021-remote-branch-operations-name-branches-only.md`: `push` and `delete_remote_branch` refuse what git would not take as a branch name (including `^`, `HEAD` and `@`), and name `refs/heads/<branch>`, so that a tag is never pushed or deleted as a branch and `"pushed"` always means what the guide says. It also pins the one surviving `*` mutant. It needs your choice of A, B or C (section 6) before you promote it; promote it before F0007, the first feature that deletes remote branches.

## Log (append only)

1. acceptor: accepted with drafts; 1 draft proposed; make mutants not run (no target, by decision)/—
      1 Scope: nothing is missing. S0020 stays inside the git wrapper's scope (R9, decision 22), and the Goal's done-when conditions all still hold. The remark from the earlier acceptances carries over: the hosting interface is wider than R10's list (listed under 6).
      2 Feature demo: green. One work item runs through real git (with a German locale), real make, a stand-in `claude` and both hosting implementations. Step 6b now tries `+main`, `:scratch`, `HEAD:refs/heads/other`, `refs/heads/x*`, and `delete_remote_branch` of `+main` and `main:x`. All are refused before git and before `BEFORE_PUSH`, the human's `main` survives, and `a+b` still pushes. A probe found two edges left, neither with a caller: `delete_remote_branch("v1")` deletes a tag, and `push` of `^main`, `@`, `HEAD` or a local tag returns "pushed" with no `origin/<branch>` afterwards. Draft F0001-S0021.
      3 Mutation: there is no target (`docs/decisions.md`). A hand-mutant run on a /tmp copy was denied by the session again, and I did not retry. Instead I read S0020's tests: they kill every mutant I would have run except `"*" in value` → `endswith("*")`, which the draft pins with `x*y`. Coverage is unchanged at 99.49 %; the same deliberate or defensive lines are uncovered.
      4 Noticed: there is no wrapper-level `*` test (intake accepted that). The documenter's note on "pushed when gone" now fails only for a tag name and `HEAD`. Carried over: an unfrozen `RemoteBranch`, `set_labels` reading label names, the unnamed pinned `claude` version, the `*_protocol.py` test names, and the double ref check in `merge`.
      5 Docs: S0020's text is consistent with itself and with the code. Two project-guide sentences on what "pushed" means are false at the edges in 2, and the draft's docs criterion repairs them. Three one-line minor items carry over: the WE6.3 tag, the guide intro's stale "until then CLAUDE.md…", and the README's "(partly written)".
      6 Decisions: all 22 are built, and decision 22 is confirmed by the demo. New for the human: the draft's options. A extends the name rule and qualifies `refs/heads/<branch>` as the source only, which is near decision 22's rejected alternative but keeps the refusal; I recommend it. B is the name rule only. C is docs only. The older open points are still open.
      7 Slow checks: none exist (no image, SBOM or mutants target). `make check` is green at 99.49 %, both before and after this report.
      8 Cost: 143 runs, 107.9 min, $31.78, about $1.59 per story. S0020 cost 6 runs, 3.2 min and $1.18 with no rework, in line with the other one-rule stories. No story stands out.
2. done (pull request merged); cost: 3 runs, 18.5 min, 93 turns, 383k tokens in (5683k more from cache), 103k out, $6.26
