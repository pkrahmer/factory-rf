---
stage: accept
pr: 25
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0001-S0001, F0001-S0002, F0001-S0003, F0001-S0004, F0001-S0005, F0001-S0006, F0001-S0007, F0001-S0008, F0001-S0009, F0001-S0010, F0001-S0011, F0001-S0012, F0001-S0013, F0001-S0014, F0001-S0015, F0001-S0016, F0001-S0017, F0001-S0018, F0001-S0019, F0001-S0020, F0001-S0021]
---
# Acceptance of Boundaries

## Verdict

**Accepted.** This is the fourth acceptance, and S0021 closed the two edges the third one left. `delete_remote_branch("v1")` now leaves a tag `v1` alone. `push` of `^main`, `HEAD`, `@`, a local tag or any name git would not take as a branch is now refused (a `ValueError`, or a `GitError` for the tag) instead of returning `"pushed"` with no `origin/<branch>` afterwards. `make check` is green (99.50 % branch coverage), and the feature demo is green end to end. Compared against git itself over 3,061 names, `check_branch_name` accepts nothing git refuses.

No finding has weight. One mutant survives (a control-character boundary with no test), and the older open points are listed under 6. These are for you to accept or revisit; none is a broken promise, so I propose no draft.

## 1 Scope

**None missing.** S0001–S0020 map to the scope as the first three acceptances found. S0021 stays inside the git wrapper's scope (R9, decision 23) and touches nothing under "Out of scope": `factory-guard` is unbuilt, `factory.entry` is empty, and there are no kill-point recovery tests.

The Goal's "done when" conditions all hold (section 2):

- Each of the four boundaries is callable through its interface, an abstract base class with 19, 10, 1 and 2 operations.
- The hosting service and the agent runtime each have a fake.
- Git is tested against a real bare remote.
- Each kill point is armed and reached.
- The searches find each outside tool in one module.

The remark from every earlier acceptance stands: the hosting interface's ten operations are more than R10's seven (under 6).

## 2 Feature demo

**Green.** It is the third acceptance's walk-through: one work item goes through every boundary.

- Real git against a bare remote in a temp directory, with the operator's locale set to German.
- A real Makefile through make.
- The fake hosting service, and the PyGithub client against a failing stand-in.
- A stand-in executable in place of `claude -p`, because a real call needs your login.

The new step is 6c. It tries the third acceptance's edges against the real remote, which holds a tag `v1` pushed by the human, while the factory's checkout holds a local-only tag `t2`.

Saved as `/tmp/fdemo4/demo.py` and run from the repository root with `uv run python /tmp/fdemo4/demo.py`:

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

# 6c the third acceptance's edges: a tag is never pushed or deleted as a branch, aliases are refused
from factory.domain.errors import GitError
def remote_refs():
    return run_process(ProcessRequest(argv=["git", "for-each-ref", "--format=%(refname)"], cwd=root / "remote.git")).stdout.split()
run_process(ProcessRequest(argv=["git", "tag", "v1"], cwd=root / "human"))
run_process(ProcessRequest(argv=["git", "push", "-q", "origin", "v1"], cwd=root / "human"))
run_process(ProcessRequest(argv=["git", "tag", "t2"], cwd=root / "factory"))
before_refs = remote_refs()
before = kp.reached(KillPoint.BEFORE_PUSH)
for name in ("^main", "HEAD", "@", "main~1", "a..b", "x.lock", "feature/.x", "x*y"):
    try:
        factory.push(name)
    except ValueError as error:
        print("6c refused:", error)
try:
    factory.push("t2")
except GitError as error:
    print("6c local tag t2:", type(error).__name__, str(error).splitlines()[0][:90])
print("6c delete branch named like the tag:", factory.delete_remote_branch("v1"))
print("6c remote refs unchanged:", remote_refs() == before_refs, remote_refs(),
      "| before-push reached by refusals:", kp.reached(KillPoint.BEFORE_PUSH) - before - 1)

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
6c refused: not a branch name git takes: '^main'
6c refused: not a branch name git takes: 'HEAD'
6c refused: not a branch name git takes: '@'
6c refused: not a branch name git takes: 'main~1'
6c refused: not a branch name git takes: 'a..b'
6c refused: not a branch name git takes: 'x.lock'
6c refused: not a branch name git takes: 'feature/.x'
6c refused: not a branch name git push takes literally: 'x*y'
6c local tag t2: GitError git push --porcelain --set-upstream origin refs/heads/t2 failed (exit 1): error: src refsp
6c delete branch named like the tag: pushed
6c remote refs unchanged: True ['refs/heads/main', 'refs/heads/scratch', 'refs/heads/work-item/F0001-S0001', 'refs/tags/v1'] | before-push reached by refusals: 0
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

- **The third acceptance's findings are fixed.** In 6c, `^main`, `HEAD`, `@`, `main~1`, `a..b`, `x.lock`, `feature/.x` and `x*y` are each refused before git runs, and none reaches `BEFORE_PUSH`. `push("t2")` of a local-only tag is a `GitError` from git (`src refspec refs/heads/t2 does not match any`), not `"pushed"`. `delete_remote_branch("v1")` returns `"pushed"` (no branch `v1` exists, which counts as already gone) and the remote's `refs/tags/v1` survives. The remote's refs are the same before and after the step.
- **The rest is unchanged** from the third acceptance:
  - the ABCs;
  - the agent run, and the negative budget reply that ends `died`;
  - the kill points `AGENT_RUN`, `BEFORE_PUSH` and `AFTER_POST`, each followed by a rerun;
  - the English push outcomes under a German locale;
  - the merge conflict that is aborted;
  - the refusals of S0015 and S0020;
  - `a+b`, which is still pushed and deleted;
  - the human's merge and the cleanup;
  - the one `HostingServiceError`;
  - one module for each outside tool.

**A comparison with git's own rule finds no difference.** S0021 ported `git check-ref-format --branch` into the domain by hand. The script `/tmp/fdemo4/diff.py` compares the port with git 2.39.5 on two sets of names. The first is 61 hand-picked edges: `@{-1}`, `x/@`, `a/./b`, `refs/heads/x`, `é`, `a\x1f`, `FETCH_HEAD` and others. The second is 3,000 random names over `ab.-/@{}^~:?*[\ +` plus DEL and the letters of `HEAD` and `.lock`. A name counts as a difference in two cases:

- the port accepts it, and git refuses or rewrites it;
- the port refuses it, git accepts it, and it is not one of the refusals made on purpose (`+`, `:`, `*`, `HEAD`, `@`).

Run with `uv run python /tmp/fdemo4/diff.py`:

```
git version 2.39.5
names: 3061 | differences: 1
('we accept, git refuses/expands', '\xa0', '')
```

The one difference is a mistake in the probe, not in the port. The script strips git's output, and Python's `strip()` removes a no-break space. Run directly, `git check-ref-format --branch $'\xc2\xa0'` exits 0 and prints the name back, so git accepts it as the port does.

## 3 Mutation score

**There is no `make mutants`.** The Makefile has no `mutants` target, and `docs/decisions.md` ("No `mutants` target, no mutmut") records that choice. Earlier acceptances tried hand mutants on a copy of the repository, and the session refused that. This time I mutated in process instead: `/tmp/fdemo4/mutants.py` patches the attributes of `factory.domain.git` (the three private helpers and the three rule constants S0021 added), runs `pytest tests/domain/test_git.py` against each patch, and restores the module. No file changes. With the patches removed, the run is green.

Run with `uv run python /tmp/fdemo4/mutants.py`:

```
killed   control chars dropped
SURVIVED control bound 0x20 -> 0x10
killed   DEL dropped
killed   char '^' dropped
killed   char '~' dropped
killed   char '?' dropped
killed   char '[' dropped
killed   char '\\' dropped
killed   char ' ' dropped
killed   sequence '..' dropped
killed   sequence '@{' dropped
killed   sequence '//' dropped
killed   alias 'HEAD' dropped
killed   alias '@' dropped
killed   component leading . dropped
killed   component .lock dropped
killed   component .lock endswith -> in
killed   component leading . -> == '.'
killed   ref name lead/ dropped
killed   ref name trail/ dropped
killed   ref name trail. dropped
killed   ref name all -> any
baseline exit 0; 21/22 killed
```

- **21 of 22 mutants are killed.** One of them is last time's survivor, `*` only at the end, which the `x*y` row of criterion 2 now kills.
- **One survives: the control-character bound.** The only control character criterion 1 tests is `\t` (0x09), so narrowing `ord(c) < 0x20` to `< 0x10` goes unnoticed. The code itself is right: the comparison with git refuses `a\x1f` exactly as the port does. This is the one survivor group: control characters 0x10–0x1f in `check_branch_name`. It is a single test row (`"a\x1fb"`). The factory's names never contain a control character, so I propose no story for it. A future story that touches `tests/domain/test_git.py` can add the row.
- **The wrapper side was checked by reading the tests.** Going back to the unqualified `branch` on either command line would be killed by criterion 6 (a local tag would be pushed) or criterion 7 (the remote tag would be deleted). Removing `check_branch_name` from either operation would be killed by criteria 4, 5 and 10.
- **Coverage is 99.50 %** (99.49 % before S0021). The same three lines of `claude_runtime.py` are uncovered, along with `git_cli.py:121` and the partial branch `66->68`. Only the `git_cli.py` line numbers moved, because S0021 removed `ALREADY_DELETED_MARKER`. Each uncovered line is deliberate (timing, permissions) or defensive parsing; none is a missing criterion.

## 4 What the stories noticed

The only new log is S0021's. For S0001–S0020, see the first three acceptances: their items are fixed, carried below, or listed under 6.

- **Coder:** the explicit leading and trailing `/` checks "overlap a little" with the component split, and were kept for clarity. They do not overlap: an empty component passes `_is_valid_component`, so without them `/x` and `x/` would be accepted, and the mutants `ref name lead/` and `ref name trail/` confirm both checks are needed. Nothing to do.
- **Tester:** criteria 8 and 9 may already pass on the old code. They guard the `refs/heads/<branch>` change, which is a good guard.
- **Reviewer:** no remarks beyond the findings.
- **Documenter:** nothing stale outside the story. The documenter did not run the demo; the demo stage did, and it matched its `Expect:` line.
- **Still open from earlier acceptances (under 6):**
  - `RemoteBranch` is still the only result model that is not frozen (`src/factory/domain/git.py:23`).
  - `set_labels` reads label names.
  - The pinned `claude` version is unnamed.
  - `version()` runs in the current directory.
  - `tests/application/test_git_protocol.py` and `test_hosting_protocol.py` still carry "protocol" in their names.
  - `merge` checks its ref twice: once directly (`src/factory/adapters/git_cli.py:307`) and again through `is_ancestor`.

## 5 Documentation as a whole

I read `README.md`, `docs/operator-guide.md`, `docs/project-guide.md` (357 lines) and `docs/decisions.md` from the top.

- **The two sentences the third acceptance found false are now true, and the code agrees.**
  - The project guide says ``"pushed"`: git exited 0; afterwards `origin/<branch>` in the checkout is the pushed commit``. That holds for every name that passes `check_branch_name`: a local tag is now a `GitError` (demo 6c), and step 4's rerun resolves `origin/<branch>` to the pushed commit.
  - The `delete_remote_branch` paragraph now says that a tag of the same name is left alone and that `a..b` is a `ValueError`.
  - Git's `remote ref does not exist` message is no longer mentioned anywhere, and `ALREADY_DELETED_MARKER` is gone from the code.
- **The branch rule agrees across the code and the docs.** The project guide's branch rule (line 180), its `refs/heads/<branch>` paragraph (line 182), the operation table (lines 124–125) and the decision entry "A pushed branch is never read as a refspec" agree with each other and with the code. Every example they give is exercised in demo 6b and 6c.
- **The decision entry is long.** It is now one paragraph that holds decisions 22 and 23 and their rejected alternatives. It reads correctly but densely; a newcomer would follow it more easily as two entries. That is a matter of form, not a contradiction, so no draft.
- **Three one-line items carry over for the fourth time, with no draft:**
  - the WE6.3 planning tag in the operator guide;
  - the project guide's intro, "until then `CLAUDE.md` holds the rules", which is stale for a guide of 357 lines;
  - the README's "(partly written)".

  Each is best fixed by your own commit or by the next documenter that touches the file.
- **No missing section.** Nothing this feature made necessary is missing, and no example I ran fails.

## 6 Decisions taken for the human

FEATURE.md's 23 decisions are built as written. The demo exercises 1, 2, 4, 7, 10, 12, 13, 15 and 20–23 directly. S0021 built decision 23 as option A: git's branch-name rules plus `HEAD` and `@` in the domain, and `refs/heads/<branch>` as the source only. The refusal of `+`, `:` and `*` stays, and S0012's test `test_delete_remote_branch_of_an_invalid_ref_name_raises` was changed to `ValueError`, as decision 23 allows.

**Taken in S0021 without asking.** The coder ported git's rules by hand into the domain rather than calling `git check-ref-format` (the domain runs no tool, and a push would cost an extra process). The comparison in section 2 shows the port matches git 2.39.5. A later git that tightens its rules would not be followed automatically; the port would need a story.

FEATURE.md decision 16 still says "the feature has fourteen", and it has twenty-one. That is a historic statement in your file; I note it and leave it.

**Still open from the earlier acceptances**, for you to accept or revisit:

- `set_labels` reads label names, beside R10's "never read back" (decision 5).
- The hosting interface is wider than R10's list (`find_open_pull_request`, `set_draft`, `set_description`).
- The pinned `claude` version, for the operator guide.
- Whether `git rm --cached` in `changed_paths` should get an exact kind.
- Whether `RemoteBranch` should be frozen.
- The unsourced defaults of decision 19: git's 5 minutes, `version()`'s 30 seconds, and the 0.50 minimum for the resume.
- Decisions 17 and 18, which F0005 and F0010 must honour (`PATH`, `HOME`, and the preflight probe of the flags).
- Whether to rename `test_git_protocol.py` and `test_hosting_protocol.py`; that would change tests another stage wrote, so it is your call.

## 7 Slow checks

**None exist.** The Makefile has only `check` and its parts (lint, types, layers, sast, secrets, licenses, test). There is no `image/`, so no image scan and no SBOM, and there is no `mutants` target (section 3).

I ran `make check` in full on this branch before writing anything. It ended with `check: green` at 99.50 % branch coverage. This report changes no code.

## 8 Cost

**149 runs, 112.8 min, $32.93 for twenty-one stories**, about 7.1 runs and $1.57 per story.

- **S0001–S0020** cost 143 runs, 107.9 min and $31.78. The earlier acceptances discussed them; the most expensive story cost $2.41.
- **S0021** cost 6 runs, 4.9 min and $1.15. It went once through every stage with no rework round and no question, in line with S0020 ($1.18) and S0015 ($1.50).
- **No story stands out.** What stands out is the acceptances themselves, which are not in this sum. The first three cost $2.74, $4.57 and $6.26 ($13.57 together, about 41 % of the stories' cost), and each round cost more than the one before. Each found a smaller edge of the same two git operations: S0015, then S0020, then S0021. This fourth round finds none of weight, which is why I propose no draft: a fifth round over the same wrapper is unlikely to pay for itself before F0007 gives these operations a caller.

## Proposed stories

None. The one surviving mutant (a control-character row in `check_branch_name`'s tests) and the carried items do not amount to a story worth a run. They are listed under 3, 4 and 6 for you to fold into a later story or decide.

## Log (append only)

1. acceptor: accepted; 0 drafts proposed; make mutants not run (no target, by decision)/—; in-process hand mutants of S0021's rules 21/22
      1 Scope: nothing is missing. S0021 stays inside the git wrapper's scope (R9, decision 23). The Goal's done-when conditions all hold. As before, the hosting interface is wider than R10's list (listed under 6).
      2 Feature demo: green, exit 0. The new step 6c runs on the real bare remote: `^main`, `HEAD`, `@`, `main~1`, `a..b`, `x.lock`, `feature/.x` and `x*y` are refused before git and before `BEFORE_PUSH`. Pushing a local-only tag is a `GitError`. `delete_remote_branch("v1")` leaves the remote tag `v1` alone, and the remote's refs are unchanged. A comparison of `check_branch_name` with `git check-ref-format --branch` over 3,061 names finds no real difference; the one it reports comes from the probe's `strip()`.
      3 Mutation: there is no `mutants` target (`docs/decisions.md`). 22 in-process mutants of `factory.domain.git`, with no file changes: 21 killed. The survivor is the control-character bound: only `\t` is tested, and a row with `\x1f` would kill it. Coverage is 99.50 %; the uncovered lines are deliberate or defensive.
      4 Noticed: S0021's logs leave nothing open. The coder's "overlap" of the `/` checks is not an overlap; the mutants show both checks are needed. Carried over: `RemoteBranch` is not frozen, `set_labels` reads label names, the pinned `claude` version is unnamed, `version()` runs in the current directory, two test files are still named `*_protocol.py`, and `merge` checks its ref twice.
      5 Docs: the two project-guide sentences the third acceptance found false are now true. The branch rule, the operation table and the decision entry agree with the code. Three one-line items carry over for the fourth time: the WE6.3 tag, the stale intro of the guide, and the README's "(partly written)". The combined entry for decisions 22 and 23 is dense but correct.
      6 Decisions: all 23 are built. Decision 23 is built as option A. The coder ported git's branch-name rules by hand rather than calling git; it matches git 2.39.5, but a later git that tightens its rules would not be followed. FEATURE.md decision 16's "fourteen" is now historic. The older open points are still open.
      7 Slow checks: none exist (no image, no SBOM, no mutants target). `make check` is green at 99.50 %.
      8 Cost: the stories cost 149 runs, 112.8 min and $32.93, about $1.57 each. S0021 cost $1.15 with no rework. No story stands out. The three earlier acceptances cost $13.57 more, rising each round, which is why this round proposes no fifth.
