---
stage: done
pr: 21
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0001-S0001, F0001-S0002, F0001-S0003, F0001-S0004, F0001-S0005, F0001-S0006, F0001-S0007, F0001-S0008, F0001-S0009, F0001-S0010, F0001-S0011, F0001-S0012, F0001-S0013, F0001-S0014, F0001-S0015, F0001-S0016, F0001-S0017, F0001-S0018, F0001-S0019]
outcome: accepted
---
# Acceptance of Boundaries

## Verdict

**Accepted with drafts.** This is the second acceptance. The five stories since the first (S0015–S0019) did what the first report asked:

- Option-like refs are refused.
- Git runs in the C locale.
- A reply with a negative measure is `died`.
- The four open failing sides are pinned.
- The stale documentation is repaired.
- The four interfaces are abstract base classes that their six implementations inherit.

The feature demo is green end to end, and `make check` is green (99.49 % branch coverage).

One finding of weight remains, of the same kind as last time: **`GitCli.push("+main")` still force-pushes over another writer's commit.** Git reads the leading `+` of a refspec as force, and `push(":keep")` deletes a remote branch. S0015's rule refuses only a leading `-`. So "a push is never forced", which the project guide and `docs/decisions.md` now state outright, is still false at an edge that no caller reaches yet. I rate it the way the first acceptance rated `--force`: not a broken promise of the feature, because no caller exists and the factory's branch names cannot take that form. Draft F0001-S0020 closes it and should be promoted before any feature that pushes (F0005, F0007). If you read the documented guarantee as the promise, refuse this pull request instead.

## 1 Scope

**None missing.** The first acceptance mapped every scope item to S0001–S0014, and that mapping still holds. The five new stories stay inside the scope:

- **S0015** tightens the git wrapper (R9).
- **S0016** tightens the `claude -p` runtime (R12, decision 12).
- **S0017** adds tests only (R9–R11).
- **S0018** changes documentation only.
- **S0019** changes the interface form across all four boundaries (CLAUDE.md, decided by you on 2026-10-13).

None of them touches an "Out of scope" line:

- `factory-guard` is still unbuilt.
- `os_user` is unused.
- `factory.entry` is empty.
- There are no kill-point recovery tests.

The Goal's "done when" conditions all hold again in section 2:

- Each of the four boundaries is callable through its interface. The interfaces are now abstract base classes with 19, 10, 1 and 2 operations.
- The hosting service and the agent runtime each have a fake.
- Git is tested against a real bare remote.
- Each kill point is armed and reached.
- The searches find each outside tool in one module.

The remark from last time stands: the hosting interface's ten operations are wider than R10's seven (under 6).

## 2 Feature demo

**Green.** One work item goes through every boundary:

- real git against a bare remote in a temp directory, with the operator's locale set to German;
- a real Makefile through make;
- the fake hosting service, and the PyGithub client against a failing stand-in;
- a stand-in executable in place of `claude -p`, because a real call needs the operator's login.

Beyond the first acceptance's walk-through, it checks:

- the four interfaces and their six implementations (step 0);
- a budget-stop reply with a negative measure (step 2);
- the force push of last time, `--force`, together with `--all`, `--detach` and `--hard` (step 6b);
- that no module mentions `Protocol` (step 9).

`after-push` is not armed here; S0006's tests cover it.

Saved as `/tmp/fdemo2/demo.py` and run from the repository root with `uv run python /tmp/fdemo2/demo.py`:

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

# 6b the force push the first acceptance found: refused before git or a kill point
factory.checkout("main")
(root / "factory/README.md").write_text("diverged\n")
factory.commit("factory's, diverged")
before = kp.reached(KillPoint.BEFORE_PUSH)
print("6b plain push:", factory.push("main"))
for call in (lambda: factory.push("--force"), lambda: factory.delete_remote_branch("--all"),
             lambda: factory.checkout("--detach"), lambda: factory.reset_to("--hard")):
    try:
        call()
    except ValueError as error:
        print("6b refused:", error)
factory.fetch()
print("6b remote main still the human's:", factory.log("origin/main")[0].subject,
      "| before-push reached by refusals:", kp.reached(KillPoint.BEFORE_PUSH) - before - 1)
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
6b remote main still the human's: human edit | before-push reached by refusals: 0
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

- **Last time's finding is fixed.** `push("--force")` and the other option-like values are refused before git or a kill point runs, and the human's commit stays the remote's tip.
- **Negative measures are a dead run.** A budget-stop reply with `num_turns` -1 is `died`, with no measures and no resume.
- **The German locale changes nothing** (the push outcomes are read in English).
- **Deletion is repeatable.** Deleting an already-deleted remote branch again is `pushed`.
- **Stray literals are not calls.** The literal `"git"` in `domain/git.py` is the default of `GitOptions.executable`. `'claude'` appears in no module, because the runtime takes the executable as a parameter.

**A second walk-through found the remaining force push.** It used the same entry points, and was saved as `/tmp/fdemo2/plus.py`:

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
(root / "factory/a.txt").write_text("one\n")
factory.commit("one")
factory.push("main")
human.clone(url)
(root / "human/a.txt").write_text("human\n")
human.commit("human's")
human.push("main")
(root / "factory/a.txt").write_text("factory\n")
factory.commit("factory's, diverged")
print("plain push:", factory.push("main"))
print("push('+main'):", factory.push("+main"))
human.fetch()
print("remote main:", [c.subject for c in human.log("origin/main")])
human.checkout("keep", start_point="origin/main")
human.push("keep")
print("push(':keep'):", factory.push(":keep"))
human.fetch()
print("remote branches:", [b.name for b in human.remote_branches()])
print("push('HEAD:refs/heads/other'):", factory.push("HEAD:refs/heads/other"))
human.fetch()
print("remote branches:", [b.name for b in human.remote_branches()])
```

Output (exit 0):

```
plain push: rejected
push('+main'): pushed
remote main: ["factory's, diverged", 'one']
push(':keep'): pushed
remote branches: ['main']
push('HEAD:refs/heads/other'): pushed
remote branches: ['main', 'other']
```

What this shows:

- **`+main` force-pushes.** The human's commit is gone from the remote.
- **`:keep` deletes.** `push(":keep")` deleted a remote branch through `push`, and its `AFTER_PUSH` would fire as for a real push.
- **A refspec can create any ref.** `HEAD:refs/heads/other` created a branch with no local counterpart.

The cause is `GitCli.push` (`src/factory/adapters/git_cli.py:279–281`). It checks `branch` only with `check_git_argument`, which refuses a leading `-`, and then passes the value as a refspec. `git check-ref-format --branch +main` accepts `+main` as a name, so this is not covered by "no git ref, branch name or url starts with a dash".

A related case in `delete_remote_branch`: by hand, `delete_remote_branch("+main")` returns `"pushed"` while `main` is still on the remote, because git looked for a ref literally named `+main`. `delete_remote_branch("main:x")` is a `GitError`.

The local operations (`checkout`, `delete_branch`, `merge`) read no refspec, and git refuses a `:` in a branch name there. Draft F0001-S0020.

## 3 Mutation score

**Not run.** There is no `mutants` target, and `docs/decisions.md` ("No `mutants` target, no mutmut") says so on purpose.

- **A hand sample was denied.** I tried twelve hand mutants of S0015–S0019's code on a copy of the repository under `/tmp`, and the session refused the command. I did not retry.
- **Coverage is the substitute.** `make check`'s branch coverage is 99.49 %. Four lines and three partial branches are uncovered:
  - `claude_runtime.py:360`: the resume skipped when no time is left.
  - `claude_runtime.py:381–382`: a run file that cannot be written into an existing state directory.
  - `git_cli.py:122`: a porcelain entry kind other than `?`, `1` or `u`. With renames off, git writes no `2` entries.
  - `git_cli.py:67->69`: a log listing without a trailing NUL.
- **None of these is a missing criterion.** The two runtime lines need sleeps or permission tricks, and S0016's coder left them out on purpose. The two git lines are defensive parsing that git never triggers.
- **Last time's survivors are now pinned.** The first acceptance named them: the resumed sums, negative measures, `"check\n"`, an unsafe `move` source, an unmerged `status()` entry, and the fake's cross-pull-request `delete_comment`. S0016 and S0017 test them all (criteria 6 and 8 of S0016; 1–4 of S0017).
- **One new group.** Refspec syntax in `push` and `delete_remote_branch` has no failing side, so a test cannot notice it (section 2, F0001-S0020).

## 4 What the stories noticed

Collected from the five new logs. For S0001–S0014, see the first acceptance; its items are either fixed by S0015–S0018 or listed under 6.

- **S0015.**
  - The reviewer noted that `merge` checks `ref` twice, the second time through its own `is_ancestor`. Harmless. No draft.
  - Nobody noticed refspec syntax. Found here; F0001-S0020.
- **S0016.** The coder left `claude_runtime.py` lines 360 and 381–382 uncovered on purpose (section 3). No draft.
- **S0017.**
  - The coder named the uncovered `git_cli.py:122` and `67->69`, both defensive.
  - The reviewer saw that the unmerged-merge test repeats the isolated environment dict of `test_committed_at_is_the_committer_date_in_utc` instead of sharing a helper. Moving it would change a test that story did not write. That is a test-tidiness item for whichever story next touches both tests. No draft.
- **S0018.** The documenter left two items:
  - The README's "(partly written)" on the project guide is vague but not wrong.
  - "Comes from F0005/F0010" in the hosting and project-commands sections is still correct.

  No draft.
- **S0019.** The documenter kept the test file names `tests/application/test_git_protocol.py` and `test_hosting_protocol.py`. Those files now check the operations of abstract base classes, not protocols. A rename changes tests nobody of a later story wrote, so it is your call. No draft.
- **Still open from the first acceptance, for you (under 6):**
  - `RemoteBranch` is still the only result model that is not frozen (`src/factory/domain/git.py:23`).
  - `set_labels` reads label names.
  - The pinned `claude` version is unnamed.
  - `version()` runs in the current directory.

## 5 Documentation as a whole

I read `README.md`, `docs/operator-guide.md`, `docs/project-guide.md` and `docs/decisions.md` from the top. S0018 repaired every item the first acceptance listed:

- The kill-point paragraph and the `AGENT_RUN` row.
- The README status sentence and its link.
- The operator guide's intro and its doubled paragraph.

S0019's documenter removed every "structurally, does not inherit" wording. The examples I ran (the fake hosting example and the project-commands example, through demo steps 3 and 5) work.

What is left:

1. **"Push never forces" is false for `push("+main")`.** It appears in the project guide (*The git wrapper*, "Push never forces: it runs `git push --porcelain --set-upstream origin <branch>`") and in `docs/decisions.md` ("A push is never forced"). The argument rule's "so nothing valid is lost … `push("--force")` would force-push" reads as if it closed the force path, and it closes only one. No user acts on this wrongly yet, because no caller exists. F0001-S0020's docs criterion repairs it together with the fix.
2. **Planning tags in the operator guide.** It cites "(WE6.3)" for the unchecked flags. `docs/decisions.md` cites WE6.3, R9, R24 and others throughout, and those tags live in `planning/`, which a newcomer cannot connect to anything. The decision log is for agents and you, so the tags fit there. In the operator guide one tag is minor. No draft.
3. **The project guide's intro says it twice.** It is "filled in story by story" and "the documenter stage fills this in …; until then `CLAUDE.md` holds the rules". The second half is stale now that the guide is 350 lines. Minor. No draft.
4. **No missing section.** Nothing this feature made necessary is missing.

## 6 Decisions taken for the human

FEATURE.md's 21 decisions are built as written, with one exception: **decision 10's "a push is never forced" fails for `push("+main")`** (section 2; F0001-S0020).

The decisions added since the first acceptance:

- **20.** Interfaces are abstract base classes; `typing.Protocol` only for code the factory does not own. Your decision, built by S0019: the demo's step 0, and no `Protocol` left in `src`.
- **21.** Your answers to the first acceptance's drafts, all built:
  - option-like values are refused with `ValueError`, not passed after `--end-of-options`;
  - git always runs with `LC_ALL=C`;
  - a negative cost is a reply that does not parse, and a budget stop with a negative measure is not resumed;
  - an unmerged path stays `"modified"`;
  - the documentation repair ran through the pipeline.

Your answer recorded in a story log since then:

- S0016: the budget-stop criterion, the removed "unless the `time_limit` ended it", and the criterion for the reverse resume direction.

Taken by coders without asking:

- S0015 checks arguments in each public method rather than centrally in `_run`, because the central layer runs after `BEFORE_PUSH` and after `clone`'s `mkdir`.
- S0016 puts the bounds on the private parse models (`NonNegativeInt`, `NonNegativeFloat`) rather than in a check after parsing.

Taken in this report, in the draft:

- F0001-S0020 proposes refusing a leading `+` and any `:` in the branch of `push` and `delete_remote_branch`. That refuses `+main`, which `git check-ref-format` allows as a branch name.
- The alternative is an explicit `refs/heads/<b>:refs/heads/<b>` refspec. The draft names both; I would choose the refusal.

Still open from the first acceptance:

- `set_labels` reads label names beside R10's "never read back" (decision 5).
- The hosting interface is wider than R10's list (`find_open_pull_request`, `set_draft`, `set_description`).
- The pinned `claude` version for the operator guide.
- Whether `git rm --cached` in `changed_paths` should get an exact kind.
- Whether `RemoteBranch` should be frozen.
- The unsourced defaults of decision 19: git's 5 minutes, `version()`'s 30 s, the 0.50 resume minimum.
- Decisions 17 and 18, which F0005 and F0010 must honour (`PATH`, `HOME`, the preflight probe of the flags).

New:

- Whether to rename `test_git_protocol.py` and `test_hosting_protocol.py` now that the interfaces are not protocols (section 4).

## 7 Slow checks

**None exist.** The Makefile has only `check` and its parts (lint, types, layers, sast, secrets, licenses, test):

- There is no `image/`, so there is no image scan or SBOM.
- There is no `mutants` target (section 3).

`make check` was run in full on this branch before any change: `check: green`, 99.49 % branch coverage.

## 8 Cost

**137 runs, 104.7 min, $30.60 for nineteen stories.** That is about 7.2 runs and $1.61 per story.

- **The first fourteen** cost 106 runs, 86.4 min and $25.39; the first acceptance discussed them.
- **The five since then** cost 31 runs, 18.3 min and $5.21, about $1.04 per story:
  - S0015: 6 runs, $1.50.
  - S0016: 7 runs, $0.97. One intake round for your answer on three missing criteria.
  - S0017: 6 runs, $0.80.
  - S0018: 6 runs, $0.49.
  - S0019: 6 runs, $1.45.
- **Two of them were partly idle.** S0017 and S0018 had nothing to build in two or three of their stages, so their tester, coder and reviewer runs mostly confirmed there was nothing to do. A test-only or documentation-only story still pays six runs. That is cheap here ($0.49–$0.80), and it is the pipeline's shape, not a story's fault.
- **No story stands out.** The first acceptance itself cost $2.74 on top of the stories, outside this sum.

## Proposed stories

- `drafts/F0001-S0020-push-refspec-arguments.md`: `push` and `delete_remote_branch` refuse a branch that starts with `+` or contains `:`, before git runs or a kill point is reached. This closes the remaining force push (`push("+main")`), the deletion through `push(":keep")` and pushes to arbitrary refs. It is the one finding of weight; promote it before any feature that pushes.

## Log (append only)

1. acceptor: accepted with drafts; 1 draft proposed; make mutants not run (no target, by decision)/—
      1 Scope: nothing is missing. S0015–S0019 stay within the scope: they tighten the git wrapper and the `claude -p` runtime, add tests and repair docs, and S0019 turns the interfaces into ABCs as you decided. The Goal's done-when conditions hold again. One remark carries over: the hosting interface is wider than R10's list (listed under 6).
      2 Feature demo: green. One work item goes through real git with a German locale, real make, a stand-in `claude` and both hosting implementations. Steps check that the four interfaces are ABCs that six classes inherit, that a negative budget reply is `died` and not resumed, and that `--force`, `--all`, `--detach` and `--hard` are refused before git runs. The searches find one module each for subprocess, github and make, and no `Protocol`. A second walk-through found the remaining finding of weight. `push("+main")` force-pushes over the human's commit, because git reads the leading `+` as force. `push(":keep")` deletes a remote branch, and `push("HEAD:refs/heads/other")` creates a ref. That contradicts "a push is never forced". Draft F0001-S0020.
      3 Mutation: there is no target (`docs/decisions.md`). A hand-mutant sample on a copy was denied by the session and not retried. Coverage is 99.49 %. The four uncovered lines and three partial branches are deliberate (timing, permissions) or defensive parsing. Last time's survivors are now pinned by S0016 and S0017. One new group: refspec syntax in push and delete_remote_branch (S0020).
      4 Noticed: `merge` checks its ref twice (S0015, harmless). Uncovered runtime and git lines (S0016, S0017). A duplicated test environment dict (S0017). Vague "(partly written)" in the README (S0018). Test files still named `*_protocol.py` (S0019). Carried over: an unfrozen `RemoteBranch`, `set_labels` reading labels, no pinned `claude` version.
      5 Docs: S0018 and S0019 repaired everything listed last time. "Push never forces" in the project guide and `decisions.md` is false for `+main`, and S0020's docs criterion repairs it. Minor items: a WE6.3 planning tag in the operator guide, and the guide's stale "until then `CLAUDE.md` holds the rules".
      6 Decisions: all 21 are built. The exception is decision 10, broken at the `+` and `:` edge. Since last time: your S0016 answer and the coders' own choices (per-method argument checks, bounds on the parse model). The S0020 refusal versus an explicit-refspec alternative is yours to choose. Older open points are still open, plus the test-file rename.
      7 Slow checks: none exist (no image, SBOM or mutants target). `make check` is green at 99.49 %.
      8 Cost: 137 runs, 104.7 min, $30.60, about $1.61 per story. The five new stories cost 31 runs and $5.21. S0016 had one intake round for your answer. S0017 and S0018 paid six runs for test-only and docs-only work, which is the pipeline's shape. No story stands out.
2. done (pull request merged); cost: 2 runs, 12.2 min, 61 turns, 287k tokens in (4142k more from cache), 72k out, $4.57
