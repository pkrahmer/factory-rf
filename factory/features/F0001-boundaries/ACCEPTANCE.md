---
stage: accept
pr: 27
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0001-S0001, F0001-S0002, F0001-S0003, F0001-S0004, F0001-S0005, F0001-S0006, F0001-S0007, F0001-S0008, F0001-S0009, F0001-S0010, F0001-S0011, F0001-S0012, F0001-S0013, F0001-S0014, F0001-S0015, F0001-S0016, F0001-S0017, F0001-S0018, F0001-S0019, F0001-S0020, F0001-S0021, F0001-S0022]
---
# Acceptance of Boundaries

## Verdict

**Accepted.** This is the fifth acceptance. The only new story, S0022, fixed the five items you chose from the fourth acceptance (Q27):

- `RemoteBranch` is frozen.
- Every `GitCli` operation checks each argument exactly once per call.
- The control-character survivor is killed.
- The two `*_protocol.py` test modules are renamed.
- The four stale or dense places in the documents are fixed.

`make check` is green at 99.50 % branch coverage. The feature demo is green end to end. All 35 in-process mutants are killed, the 22 of last round and 13 new ones against S0022's refactor.

What remains is small. Decision 22's rejected alternative sits in decision 23's entry since the split, and the project guide does not state the new "public operations do not call each other" convention. Older points still wait for your decision (under 6). None is a broken promise, so I propose no draft.

## 1 Scope

**None missing.** S0001–S0021 map to the scope as the four earlier acceptances found. S0022 is housekeeping inside R7 and R9 (decision 24) and touches nothing under "Out of scope":

- `src/factory/entry/` holds only `__init__.py`.
- There is no `factory-guard`.
- There are no kill-point recovery tests.

The Goal's done-when conditions all hold (section 2):

- Each of the four boundaries is callable through its abstract base class (19, 10, 1 and 2 operations).
- The hosting service and the agent runtime each have a fake.
- Git is tested against a real bare remote.
- Each kill point can be armed and is reached.
- The searches find each outside tool in one module.

As in every earlier acceptance, the hosting interface has ten operations, more than R10's list (under 6).

## 2 Feature demo

**Green, exit 0.** It is the fourth acceptance's walk-through, unchanged, plus one new step, 6d. One work item goes through every boundary:

- real git against a bare remote in a temp directory, under a German operator locale;
- a real Makefile through make;
- the fake hosting service, and the PyGithub client against a failing stand-in;
- a stand-in executable for `claude -p`, because a real call needs your login.

Step 6d checks S0022 on the factory's real checkout:

- a `RemoteBranch` that `remote_branches()` returned refuses assignment;
- `check_branch_name` refuses 0x10, 0x1f and 0x20 and accepts `a!b`;
- `merge`, `reset_to`, `revert_paths` and `delete_branch` call `check_git_argument` once each;
- the public `resolve`, `is_ancestor` and `show_file` still refuse `-x`.

Saved as `/tmp/fdemo5/demo.py` and run from the repository root with `uv run python /tmp/fdemo5/demo.py`:

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

# 6d the fourth acceptance's housekeeping: RemoteBranch is frozen, each argument is checked once
import factory.adapters.git_cli as git_cli_module
from pydantic import ValidationError
from factory.domain.git import check_branch_name
rb = factory.remote_branches()[0]
try:
    rb.name = "other"
except ValidationError:
    print("6d remote branch frozen:", rb.name)
for value in ("a\x10b", "a\x1fb", "a b"):
    try:
        check_branch_name(value)
    except ValueError:
        print("6d refused:", hex(ord(value[1])))
check_branch_name("a!b")
real_check = git_cli_module.check_git_argument
calls: list[str] = []
def counting(value: str) -> None:
    calls.append(value)
    real_check(value)
git_cli_module.check_git_argument = counting
try:
    for name, call in (("merge", lambda: factory.merge("origin/main")), ("reset_to", lambda: factory.reset_to("origin/main")),
                       ("revert_paths", lambda: factory.revert_paths("HEAD", ["README.md", "gone.txt"])),
                       ("delete_branch", lambda: factory.delete_branch("never-was"))):
        calls.clear()
        outcome = call()
        print("6d checks:", name, outcome, len(calls))
    for call in (lambda: factory.resolve("-x"), lambda: factory.is_ancestor("HEAD", "-x"), lambda: factory.show_file("-x", "a")):
        try:
            call()
        except ValueError as error:
            print("6d public read still refuses:", error)
finally:
    git_cli_module.check_git_argument = real_check

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
6d remote branch frozen: main
6d refused: 0x10
6d refused: 0x1f
6d refused: 0x20
6d checks: merge up_to_date 1
6d checks: reset_to None 1
6d checks: revert_paths None 1
6d checks: delete_branch None 1
6d public read still refuses: not a git ref, branch or url: '-x'
6d public read still refuses: not a git ref, branch or url: '-x'
6d public read still refuses: not a git ref, branch or url: '-x'
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

- **S0022 holds on the real checkout.** In 6d, the frozen `RemoteBranch` raises `ValidationError` and keeps `main`. All three control characters are refused. Each of the four operations checks its argument once and returns what it did before (`up_to_date`, `None`). The three public reads still refuse an option-like ref before git runs.
- **The rest is unchanged from the fourth acceptance:**
  - the abstract base classes;
  - the agent run, and the negative budget reply that ends `died`;
  - the kill points `AGENT_RUN`, `BEFORE_PUSH` and `AFTER_POST`, each followed by a rerun;
  - the English push outcomes under a German locale;
  - the merge conflict, which is aborted;
  - the refusals of S0015, S0020 and S0021, none of which reaches `BEFORE_PUSH`;
  - the remote tag `v1`, which survives `delete_remote_branch("v1")`;
  - the human's merge and the cleanup;
  - the one `HostingServiceError`;
  - one module for each outside tool, and no `Protocol` in `src`.

## 3 Mutation score

**There is no `make mutants`.** The Makefile has no such target, and `docs/decisions.md` ("No `mutants` target, no mutmut") records why. As in the fourth acceptance, I mutated in process: each script patches a module attribute or a `GitCli` method, runs pytest, and restores it, with no file changes.

`uv run python /tmp/fdemo5/mutants_domain.py` reruns the fourth acceptance's 22 mutants of `check_branch_name`'s rules against `tests/domain/test_git.py`:

```
killed   control chars dropped
killed   control bound 0x20 -> 0x10
killed   DEL dropped
...  (19 more, all killed)
baseline exit 0; 22/22 killed
```

Last round's one survivor, the control-character bound, is now killed by S0022's `"a\x10b"` and `"a\x1fb"` rows.

`uv run python /tmp/fdemo5/mutants_cli.py` covers S0022's refactor. Each mutant recompiles one `GitCli` method from its source, with one edit, against the module's own globals, so the counting test's monkeypatch still sees it. The script runs `tests/adapters` and `tests/domain/test_git.py`:

```
baseline before: 0
killed   resolve: check dropped
killed   show_file: check dropped
killed   is_ancestor: 2nd check dropped
killed   merge: public is_ancestor
killed   merge: check dropped
killed   merge: 2nd public is_ancestor
killed   delete_branch: public resolve
killed   revert_paths: public show_file
killed   _merge_diverged: public resolve
killed   _resolve_or_raise: public resolve
killed   _resolve_unchecked: ANSWER_NO -> 0
killed   _is_ancestor_unchecked: == 0 -> != 0
baseline exit 0; 12/12 killed
```

The thirteenth mutant is `RemoteBranch` unfrozen (`model_config["frozen"] = False` and a rebuild). It is killed when run on its own. In the combined run, its undo left the final baseline red: pydantic caches the setattr handler, so restoring `frozen` did not take. I therefore ran it alone and kept it out of the combined run, so the baselines above are clean.

- **35 of 35 are killed; there are no survivor groups.**
- **Coverage is 99.50 %**, the same as last round. The uncovered lines are still `claude_runtime.py` 360 and 381–382, and in `git_cli.py` line 124 and the partial branch 69->71. These are last round's 121 and 66->68, moved three lines by the new `__all__`. Each is deliberate (timing, permissions) or defensive parsing; none is a missing criterion.

## 4 What the stories noticed

The only new logs are S0022's. For S0001–S0021, see the earlier acceptances; their items are fixed, carried below, or listed under 6.

- **Coder:** S0022 added `__all__ = ["GitCli", "check_git_argument"]` to `src/factory/adapters/git_cli.py`, the first `__all__` in `src/factory`. Without it, criterion 4's monkeypatch of `git_cli.check_git_argument` fails mypy's no-implicit-reexport. The reviewer accepted it. It is listed under 6 because it shapes a module's public surface for a test's sake.
- **Reviewer:** no remarks beyond the findings.
- **Documenter:** "(WE6.3)" is still cited in `docs/decisions.md`: in six entries (lines 31, 35, 39, 43, 47 and 51), not the five the documenter counted. The decision log cites requirement tags (R9, R34) throughout, so a planning tag there reads as a source rather than as noise. I leave it.
- **Demo:** there are stale `test_*_protocol*.pyc` files in the local `__pycache__`. They are untracked and git-ignored, so this is nothing.
- **Still open from earlier acceptances (under 6):**
  - `set_labels` reads label names.
  - The pinned `claude` version is unnamed.
  - `version()` runs in the current directory.

## 5 Documentation as a whole

I read `README.md`, `docs/operator-guide.md`, `docs/project-guide.md` and `docs/decisions.md` from the top.

**S0022's document changes are in and true:**

- The README links the project guide without "(partly written)".
- The guide's intro says it grows with each story and that `CLAUDE.md` holds the rules.
- The guide's sentence on frozen result models names four models, `RemoteBranch` among them; the demo confirms it.
- The guide names `test_git_interface.py`.
- The operator guide no longer carries "(WE6.3)".

The argument rule's paragraph (project guide, line 178) is still exact after the refactor: "`GitCli` checks before it starts git and before any kill point".

**Two small findings, neither of which misleads a user:**

- **The split of decisions 22 and 23 moved decision 22's rejected alternative.** `docs/decisions.md`, "A pushed branch is never read as a refspec" (line 63), now has no rejected alternative. The rejection of the explicit refspec `refs/heads/<b>:refs/heads/<b>`, which FEATURE.md decision 22 records as 22's, closes the next entry (line 67). Two phrases there then point the wrong way: "the explicit refspec below" points to the same paragraph, and "like the one above" points to the entry above. S0022's criterion 10 asked that each entry keep its rejected alternatives. The fix is to move the entry's last sentence, "Alternative rejected: pushing the explicit refspec … like the one above.", back to the end of line 63, and to drop "This is not the explicit refspec below: …" from line 67 or rephrase it.
- **S0022's convention is not written down.** S0022 made it a rule that public `GitCli` operations do not call each other: inner reads go through `_resolve_unchecked`, `_is_ancestor_unchecked` and `_blob`. Criterion 4's test counts the checks only for the four operations it names, so a new operation that calls the public `resolve` would pass the checks. The project guide exists for exactly the conventions the checks do not catch. The fix is one sentence after line 178, for example: "Inside an operation, git is read through the private `_resolve_unchecked`, `_is_ancestor_unchecked` and `_blob`, never through another public operation, so each argument is checked once."

**No example fails, and no section is missing.**

## 6 Decisions taken for the human

FEATURE.md's 24 decisions are built as written. The demo exercises 1, 2, 4, 7, 10, 12, 13, 15 and 20–24 directly. FEATURE.md decision 16's "fourteen" stays historic, as decision 24 says.

**Taken in S0022 without asking:**

- **`__all__` in `git_cli.py`.** The adapter module exports `check_git_argument`, a domain function, so that a test can monkeypatch it under that name. The alternatives the coder rejected needed a `noqa` or a test change, which were not allowed. To revisit, criterion 4 could count through `factory.domain.git.check_git_argument`. The counting would then miss calls through `git_cli`'s own binding, so the criterion itself would have to change.

**Fixed by S0022, no longer open:**

- `RemoteBranch` frozen.
- The `*_protocol.py` test names.
- `merge`'s double check.
- The control-character row.
- The four stale or dense places in the documents.

**Still open, for you to accept or revisit:**

- `set_labels` reads label names, beside R10's "never read back" (decision 5).
- The hosting interface is wider than R10's list (`find_open_pull_request`, `set_draft`, `set_description`).
- The pinned `claude` version, for the operator guide.
- `version()` runs in the factory's current directory.
- Whether `git rm --cached` in `changed_paths` should get an exact kind.
- The unsourced defaults of decision 19: git's 5 minutes, `version()`'s 30 seconds, and the 0.50 minimum for the resume.
- Decisions 17 and 18, which F0005 and F0010 must honour (`PATH`, `HOME`, and the preflight probe of the flags).
- The hand-ported branch-name rules (S0021), which follow git 2.39.5 and would not follow a later git that tightens them.

## 7 Slow checks

**None exist.** The Makefile has only `check` and its parts (lint, types, layers, sast, secrets, licenses, test). There is no image, so no image scan and no SBOM, and there is no `mutants` target (section 3).

I ran `make check` on this branch before writing anything. It ended with `check: green` at 99.50 % branch coverage over 66 source files for mypy, with the layer contract kept. This report changes no code.

## 8 Cost

**155 runs, 118.4 min, $34.47 for twenty-two stories**, about 7.0 runs and $1.57 per story.

- **S0022** cost 6 runs, 5.6 min and $1.54. It went once through every stage with no rework round and no question, in line with S0020 ($1.18) and S0021 ($1.15).
- **No story stands out.** The most expensive is still S0001, at $2.41.
- **The acceptances are not in this sum.** The first three cost $13.57 together; the fourth's cost is not in my task. This fifth round finds only two document sentences and no code edge. Once those two sentences are fixed, the feature has nothing left that another acceptance round could pay for.

## Proposed stories

None. The two document findings under 5 are one moved sentence and one new sentence, each written out above. A story would cost about $1.50 to make the same edit, so I recommend fixing them in your own commit, or leaving them to the next documenter who touches `docs/decisions.md` or the git section of the project guide. The open points under 6 are your decisions, not stories.

## Log (append only)

1. acceptor: accepted; 0 drafts proposed; make mutants not run (no target, by decision)/—; in-process hand mutants 35/35 (22 of S0021's rules again, 13 against S0022's refactor)
      1 Scope: nothing is missing. S0022 is housekeeping inside R7 and R9 (decision 24) and touches nothing out of scope. The Goal's done-when conditions all hold. As before, the hosting interface is wider than R10's list (under 6).
      2 Feature demo: green, exit 0. It is the fourth acceptance's walk-through plus a new step 6d on the real checkout. A `RemoteBranch` from `remote_branches()` refuses assignment. `check_branch_name` refuses 0x10, 0x1f and 0x20 and accepts `a!b`. `merge`, `reset_to`, `revert_paths` and `delete_branch` each call `check_git_argument` once. The public `resolve`, `is_ancestor` and `show_file` still refuse `-x`.
      3 Mutation: there is no `mutants` target (`docs/decisions.md`). All 22 mutants of the branch-name rules are killed, including last round's control-bound survivor. 12 mutants that recompile `GitCli` methods are all killed, and `RemoteBranch` unfrozen is killed when run alone (pydantic's setattr cache spoiled its undo in the combined run). There are no survivor groups. Coverage is 99.50 %.
      4 Noticed: the coder added the first `__all__` in `src/factory` so the test can monkeypatch `check_git_argument` (listed under 6). "(WE6.3)" is still in six entries of `docs/decisions.md`, not five; I leave it there, beside the R-tags. Stale `.pyc` files are untracked. Carried over: `set_labels` reads label names, the pinned `claude` version is unnamed, and `version()` runs in the current directory.
      5 Docs: S0022's five doc changes are in and true. Two small findings. First, the split moved decision 22's rejected alternative (the explicit refspec) to the end of decision 23's entry (`docs/decisions.md` lines 63 and 67), against S0022's criterion 10. Second, the project guide does not state that public `GitCli` operations never call each other, and the test covers only four operations. The report gives the exact sentences for both fixes.
      6 Decisions: all 24 are built. New, taken without asking: `__all__` exports a domain function from an adapter for a test's sake. Fixed by S0022: `RemoteBranch` frozen, the protocol test names, the double check, the control-character row, the four stale or dense places in the documents. Still open: `set_labels` reads labels, the wide hosting interface, the pinned `claude` version, `version()`'s working directory, the kind for `git rm --cached`, decision 19's defaults, decisions 17 and 18 for F0005 and F0010, and the hand-ported git rules.
      7 Slow checks: none exist (no image, no SBOM, no mutants target). `make check` is green before and after the report.
      8 Cost: 155 runs, 118.4 min, $34.47, about $1.57 per story. S0022 cost $1.54 with no rework. No story stands out. Only two document sentences are left, so I recommend your own commit over another story or acceptance round.
