---
stage: accept
pr: 205
blocked: null
comments_seen: 1
round: 0
attempts: 1
stories: [F0014-S0001, F0014-S0002, F0014-S0003, F0014-S0004, F0014-S0005, F0014-S0006, F0014-S0007, F0014-S0008, F0014-S0009, F0014-S0010, F0014-S0011, F0014-S0012, F0014-S0013]
---
# Acceptance of The first start's findings

## Verdict

**Accepted.** Every scope item of `FEATURE.md` has its story, and the ten stories the first acceptance found sound still stand. The feature demo is green against the real wiring again, now with the cases S0011 pinned: two nested repositories, and links to an outside repository and to the checkout itself. The three follow-up stories closed what that acceptance found. The nested walk's link and `.git` survivors are dead or equivalent, `book_merge`'s `before_approval` stamp is pinned, and the five stale document places are fixed. What is left is one stale sentence in the operator guide's opening, which S0013's documenter saw and was not allowed to touch. I wrote one small documentation draft for it.

## 1 Scope

None. The first acceptance (merged in pull request 201) mapped every scope bullet to S0001–S0010 and checked FEATURE.md's "Done when" against the code. Since then only three stories have been added, and they changed no source:
- S0011 added rows and one test function for the nested-repository walk (`tests/adapters/test_git_cli_nested.py`, `tests/application/test_nested_repositories.py`).
- S0012 added a row and one test function for the `before_approval` stamp (`tests/domain/test_journal_stamps.py`, `tests/application/test_acceptance_merged_before_approval.py`).
- S0013 changed `README.md`, `docs/decisions.md` and `docs/operator-guide.md` only.

All three are named under "Stories" in FEATURE.md and covered by decisions 34–36. Nothing out of scope was built.

## 2 The feature demo

Green. This is the first acceptance's script (`/tmp/f0014-acceptance/feature_demo.py`), copied to `/tmp/f0014-acceptance-2/feature_demo.py`. In S0011's cases, the hostile stand-in agent now does three more things. It makes a second repository at `b` after the one at `notes`, so the sort is exercised. It links `mirror` to a repository outside the checkout. And it links `self` to `.`. Everything goes through the real entry points:
- settings from `read_settings`;
- boundaries from `build_boundaries`, with the fake hosting service;
- a real bare remote, `run_sealed`, `ClaudeCodeRuntime` and `GitCli`.

```
$ uv run python /tmp/f0014-acceptance-2/feature_demo.py
1. run_sealed: the agent writes a hook, core.fsmonitor and a nested repository
   end: completed doing
   agent saw: {"token": "demo-login-token", "token_in_argv": false}
   nested repositories removed: ['b/.git', 'notes/.git']
   outside repository kept: True | own .git kept: True | links kept: True True
   .git entries open to group or others after the seal: 0
2. the factory's git commits the agent's work
   status paths: ['mirror', 'notes/a.txt', 'result.txt', 'self']
   committed: ['mirror', 'notes/a.txt', 'result.txt', 'self']
   markers after the factory's git: []
   markers after a plain git commit: ['fsmonitor-2', 'hook-pre-commit']
3. an agent that opens .git to its group
   RepositoryUnsealed: seal failed (no exit status): /tmp/f0014-demo-btueqrnh/checkout/.git is writable by its group or by others
4. a login file written as UTF-16
   AgentRuntimeError: agent runtime failed: cannot read the agent's login file /tmp/f0014-demo-btueqrnh/claude-token: not ASCII text
5. the cost record names its instance; the journal record its time, stage and run
   {"run":"<run id>","work_item":"F0099-S0001","stage":"doing","role":"coder","attempt":0,"status":"started","started_at":"2026-10-18T03:34:11.236887Z","duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":null,"instance":"demo-instance"}
   journal:
   - number: 1
     speaker: coder
     kind: result
     at: '2026-10-18T03:34:11.237091Z'
     stage: doing
     run: <run id>
```

I replaced the run id, a random hex string, with `<run id>` so that `make secrets` stays green. Here is what each step shows:
- **The token** reached `claude` from the file and in no argument, and the request's own `CLAUDE_CODE_OAUTH_TOKEN=from-request` was dropped.
- **The walk.** Both nested repositories were removed, sorted and `/`-separated. The walk did not follow `mirror` (the outside `.git` is kept) or `self` (the checkout's own `.git` is kept). The links themselves stay and are committed as links.
- **The factory's git** ran neither the agent's hook nor its `core.fsmonitor`. A plain `git commit` afterwards ran both, so the attack was real.
- **The seal.** An opened `.git` raised `RepositoryUnsealed`, and a UTF-16 login file raised "not ASCII text".
- **The records.** The cost record carries `instance`, and the journal record carries `at`, `stage` and `run`.

The demo runs as one user. The second user, and the observations as `agent`, belong to the shakedown run.

<details><summary>The script</summary>

```python
"""F0014 feature demo: a hostile agent run in a real checkout, through the factory's own wiring."""

import json
import os
import subprocess
import sys
import tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from factory.adapters.fake_hosting import FakeHostingService
from factory.application.costs import CostRecorder
from factory.application.sealed_runs import run_sealed
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.errors import AgentRuntimeError, RepositoryUnsealed
from factory.domain.journal import NewEntry, append_entry
from factory.domain.paths import cost_records_path
from factory.domain.settings import read_settings
from factory.domain.work_item import WorkItemDocument, initial_state
from factory.entry.wiring import build_boundaries

TOKEN = "demo-login-token"
REPLY = {
    "type": "result", "subtype": "success", "is_error": False, "num_turns": 1,
    "total_cost_usd": 0.1, "duration_ms": 100, "usage": {"input_tokens": 1, "output_tokens": 1},
    "permission_denials": [], "structured_output": {"decision": "doing", "entry": "Done."},
}
root = Path(tempfile.mkdtemp(prefix="f0014-demo-"))
markers = root / "markers"
markers.mkdir()


def git(*args: str, cwd: Path = root) -> str:
    plain = ["git", "-c", "user.name=h", "-c", "user.email=h@example.org"]
    return subprocess.run([*plain, *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


# A remote with one commit on main, as the human leaves it.
git("init", "-q", "--bare", "-b", "main", str(root / "remote.git"))
git("clone", "-q", str(root / "remote.git"), str(root / "seed"))
(root / "seed" / "README.md").write_text("project\n", encoding="utf-8")
git("add", ".", cwd=root / "seed")
git("commit", "-q", "-m", "seed", cwd=root / "seed")
git("push", "-q", "origin", "main", cwd=root / "seed")

git("init", "-q", str(root / "outside"))

# A command that leaves a marker when something runs it.
probe = root / "bin" / "leave-marker"
probe.parent.mkdir()
probe.write_text(f'#!/bin/sh\ntouch "{markers}/$(basename "$0")-$1"\n', encoding="utf-8")
probe.chmod(0o755)
for name in ("hook", "fsmonitor", "nested-fsmonitor"):
    (root / "bin" / name).symlink_to(probe)

# The stand-in `claude`: the agent. It reports what it got, then attacks the checkout.
claude = root / "bin" / "claude"
claude.write_text(f"""#!{sys.executable}
import json, os, subprocess, sys
from pathlib import Path
work = Path.cwd()
seen = {{"token": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"),
        "token_in_argv": any({TOKEN!r} in a for a in sys.argv)}}
Path({str(markers)!r}, "agent-saw.json").write_text(json.dumps(seen))
if os.environ.get("ATTACK") == "open":
    os.chmod(work / ".git", 0o2775)
else:
    hook = work / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\\nexec {root}/bin/hook pre-commit\\n")
    hook.chmod(0o755)
    subprocess.run(["git", "config", "--local", "core.fsmonitor", "{root}/bin/fsmonitor"], check=True)
    subprocess.run(["git", "init", "-q", str(work / "notes")], check=True)
    subprocess.run(["git", "-C", str(work / "notes"), "config", "core.fsmonitor", "{root}/bin/nested-fsmonitor"], check=True)
    (work / "notes" / "a.txt").write_text("a\\n")
    subprocess.run(["git", "init", "-q", str(work / "b")], check=True)
    os.symlink("{root}/outside", work / "mirror")
    os.symlink(".", work / "self")
    (work / "result.txt").write_text("the agent's work\\n")
print({json.dumps(REPLY)!r})
""", encoding="utf-8")
claude.chmod(0o755)

# The instance's settings, read as the factory reads its environment, then its own boundaries.
token_file = root / "claude-token"
token_file.write_text(TOKEN + "\n", encoding="ascii")
settings = read_settings({
    "FACTORY_REPOSITORY_URL": "https://github.com/owner/project.git",
    "FACTORY_INSTANCE": "demo-instance",
    "FACTORY_CLAUDE": str(claude),
    "FACTORY_CLAUDE_LOGIN_FILE": str(token_file),
}).model_copy(update={"checkout": root / "checkout", "state_directory": root / "state"})
boundaries = build_boundaries(settings, "hosting-token", hosting=FakeHostingService())
boundaries.git.clone(str(root / "remote.git"))
checkout = settings.checkout


def request(attack: str) -> AgentRunRequest:
    return AgentRunRequest(
        agent=AgentDefinition(name="coder", model="sonnet", tools=["Read"],
                              budget_usd=Decimal("1"), instructions="Write the code."),
        prompt="Stage: doing", allowed_decisions=["doing", "question"],
        time_limit=timedelta(seconds=60), working_directory=checkout,
        environment={"PATH": os.environ["PATH"], "ATTACK": attack, CLAUDE_VARIABLE: "from-request"},
    )


CLAUDE_VARIABLE = "CLAUDE_CODE_OAUTH_TOKEN"
print("1. run_sealed: the agent writes a hook, core.fsmonitor and a nested repository")
sealed = run_sealed(boundaries, request("write"))
print("   end:", sealed.result.end_reason, sealed.result.decision)
print("   agent saw:", (markers / "agent-saw.json").read_text())
print("   nested repositories removed:", sealed.nested_repositories)
print("   outside repository kept:", (root / "outside" / ".git").is_dir(), "| own .git kept:", (checkout / ".git").is_dir(),
      "| links kept:", (checkout / "mirror").is_symlink(), (checkout / "self").is_symlink())
open_bits = [p for p in [checkout / ".git", *(checkout / ".git").rglob("*")] if p.lstat().st_mode & 0o022]
print("   .git entries open to group or others after the seal:", len(open_bits))

print("2. the factory's git commits the agent's work")
status = boundaries.git.status()
commit = boundaries.git.commit("ticket F0099-S0001: the agent's work")
print("   status paths:", sorted(c.path for c in status.changes) if hasattr(status, "changes") else status)
print("   committed:", sorted(git("show", "--name-only", "--format=", commit, cwd=checkout).split()))
print("   markers after the factory's git:", sorted(p.name for p in markers.iterdir() if p.name != "agent-saw.json"))
git("commit", "-q", "--allow-empty", "-m", "plain", cwd=checkout)
print("   markers after a plain git commit:", sorted(p.name for p in markers.iterdir() if p.name != "agent-saw.json"))

print("3. an agent that opens .git to its group")
try:
    run_sealed(boundaries, request("open"))
    print("   no error")
except RepositoryUnsealed as error:
    print("   RepositoryUnsealed:", error)

print("4. a login file written as UTF-16")
token_file.write_bytes(TOKEN.encode("utf-16"))
subprocess.run(["rm", "-rf", str(checkout)], check=True)
boundaries.git.clone(str(root / "remote.git"))
try:
    run_sealed(boundaries, request("write"))
    print("   no error")
except AgentRuntimeError as error:
    print("   AgentRuntimeError:", error)

print("5. the cost record names its instance; the journal record its time, stage and run")
path = "factory/features/F0099-demo/ongoing/F0099-S0001-demo.md"
document = WorkItemDocument(state=initial_state("doing"), body="# Demo\n\n## Journal\n")
(checkout / path).parent.mkdir(parents=True)
started = SimpleNamespace(path=path, work_item="F0099-S0001", stage="doing", document=document)
cost_run = CostRecorder(boundaries).begin(started, "coder")  # type: ignore[arg-type]
print("  ", (checkout / cost_records_path(path)).read_text(encoding="utf-8").strip())
entry = NewEntry(speaker="coder", kind="result", text="Done.")
stamped = append_entry(document, entry, at=boundaries.clock.now(), run=cost_run.run)
text = boundaries.work_item_writer.render(stamped)
print("  ", text[text.index("journal:"):text.index("---", 4)].strip().replace("\n", "\n   "))
```

</details>

## 3 Mutation score

I ran `make mutants` (FEATURE=F0014, from the branch name). It selects the 30 modules that F0014's story commits changed, 6,996 mutants in all. It went on from the results kept in `mutants/` and ran for its 540 s (`real 9m0.7s`). These are the counts from mutmut's `.meta` files over the 30 modules:
- **5,179 killed, 263 survived, 4 timeouts and 1,550 unchecked.** That is 95.1 % of the 5,446 checked. The first acceptance had 4,487 killed of 4,735 checked.
- The unchecked mutants are in the large modules the whole suite reaches: `git_cli` 685, `claude_runtime` 260, `stage` 138, `domain.acceptance` 123, `acceptance` 116 and `wiring` 111.

What became of the survivors the first acceptance named, and what S0011 and S0012 were written to kill:
- **The walk following links** (`os.walk(root, followlinks=True)`) and **entering `.git`** (`"XX.gitXX"`) are no longer in the survivor list. The two `_nested_repositories` survivors that are left, `mutmut_3` (`followlinks=None`) and `mutmut_5` (the keyword dropped, so the default `False` applies), are **equivalent**: both mean "do not follow".
- **The `", "` path list.** The probe detail's (`preflight`) and the preparer log line's (`scheduler`) mutants are no longer in the list. Five `AfterAgent._early_stall` mutants still show as survived, but mutmut's test map for that function is stale, as the first acceptance found. I re-ran each one in the mutated tree with `MUTANT_UNDER_TEST=<id> PYTHONPATH=src pytest tests/application/test_after_agent.py tests/application/test_nested_repositories.py` from `mutants/`. Mutants 6, 7, 9 and 12 fail a test, for example `KeyError: 'XXleft_branchXX'` in `test_a_checkout_left_on_another_branch_stalls_as_left_branch`.
- **`_early_stall__mutmut_8`** survives the whole `tests/application/` run as well (`1210 passed`): `return "left_branch", ""` → `"XXXX"`. The left-branch stall's empty detail is pinned by no test. The rule comes from F0005-S0005 (blame `48b1e27d`) and S0010 only moved it into `_early_stall`. It is small and older than F0014, so I wrote no draft.
- **`book_merge`'s `at` on the `before_approval` branch** (`domain.acceptance`) is no longer in the survivor list. S0012 killed it.
- **Near-equivalent, as before, no draft:**
  - `claude_runtime._login_refusal__mutmut_1`;
  - `git_cli.discard__mutmut_5` and `_11` (the error's detail);
  - `cost_records_jsonl._line_of_record__mutmut_2` to `_4`.

The other survivors are in lines older than F0014; I checked the blame of the samples. Examples are `claude_runtime._resume`'s budget comparison `<=` → `<` and `_resumed_result`'s `permission_denials` update (F0001-S0010, `ae7e0dfe`). They fall into the groups earlier acceptances named: no-state messages in the handlers, wiring pass-throughs, the `settings` helpers, and the stall context. No draft.

The first acceptance's note for the human still holds. `mutants/` keeps a test map that is stale for functions split out of older ones. One run of 540 s does not finish 30 modules. Both are matters of the `Makefile` and `mutants/`, which are outside this stage's lane.

## 4 What the stories noticed

- **S0013, the documenter** (entry 6), repeated by the demo (entry 7): the opening paragraph of `docs/operator-guide.md` (line 3) still says "a run against a real repository with a token is not observed yet". The criterion said "no others", so it was left. → Draft S0014.
- **S0011's and S0012's demos**, and every `make test` today: pytest prints `PytestWarning: (rm_rf) error removing /tmp/pytest-of-factory/garbage-…/test_seal_takes_the_group_and_0`. The first acceptance blamed a test row for this, and I correct that here. The leftover `.git` folders have mode `020`. Only a mutated `seal` writes that (for example `mode & 0o022` in place of `& ~0o022`), and today's folders are dated with today's mutation run. The plain test run leaves none. pytest only fails to clean what mutmut's runs left. This is harmless, and the operator can clear it with `chmod -R u+rwx /tmp/pytest-of-factory/garbage-* && rm -rf /tmp/pytest-of-factory/garbage-*`. No draft.
- **The coders, reviewers and documenters of S0011 and S0012** noticed nothing else. The items from S0001–S0010 were collected by the first acceptance: `os.path.lexists` in the application layer, `CommentCopier`'s clock read per comment, and the umask note of decision 22. They need nothing new.

## 5 The documentation as a whole

`make documents` prints `documents ok`. All five edits of S0013 are in place:
- the API key's reason in `docs/decisions.md`;
- the hooks entry's "(nine with `GIT_CONFIG_COUNT=4` …)";
- the agent runtime's first sentence;
- the login shell in the `sudo` call;
- the README's status paragraph.

The token steps (`docs/operator-guide.md`, "The agent runtime") and the fallback login now read as one account. The project guide's `remove_nested_repositories()` row states the link and `.git` rules that S0011 pinned. One finding remains: the README's status and the operator guide's opening paragraph now disagree. The README says that the first start brought two instances up healthy, the probe agent run included. The guide still stops at the Podman probe's `repository_unavailable`, with "a run against a real repository with a token is not observed yet". This is stale rather than misleading, because nothing an operator does depends on it. → Draft S0014. The guide's other "not observed yet" notes, the build with the pins and the Linux host's restart service, are still true and stay.

## 6 Decisions taken for the human

New since the first acceptance, from FEATURE.md, "taken by the session for the human, to confirm":
- 34: the leave for S0011's tester to add rows to three tests of S0010. A symbolic link to a folder that holds a repository is not itself a nested repository, and the walk keeps both.
- 35: the leave for S0012's tester to add the `merge-before-approval` row to S0007's test.
- 36: the human's five answers to the pre-check of S0011–S0013. These are the leave, the link rule, the `a` and `a/.cache` row, the domain row, and S0013's README wording.

The decisions the first acceptance listed are still open for the human to accept or revisit:
- 5–33 in FEATURE.md, among them the story split, `/dev/null`, `0640` plus the seal, removing and cloning again, the login shell and its ASCII rule, and the stamps as optional keywords;
- the answers from the story logs;
- the two choices agents made without asking: `exclude_none` for every future journal field, and the "not recorded" that S0013 has since fixed.

The story logs of S0011–S0013 record no new answer or default: each went from intake to demo without a question.

## 7 The slow checks

- `make check`: `check: green`, with `test: green (32.4 s)` and coverage 99.47 %, as I found it.
- `make duplicates`: `duplicates: 0 new, 39 known, 0 gone`.
- `make documents`: `documents ok`.
- The project offers no image scan or SBOM target.
- The observations as `agent` are left to the shakedown run, as the operator guide's morning observations write them: `git status`, the `.git` seal with its three `Permission denied`, the probe with only the token file, and `grep "cloning the checkout again" /state/factory.log`.

## 8 Cost

105 runs, 95.7 min, $25.65 for the feature's thirteen stories. The first ten cost 87 runs, 87.1 min and $23.01, and the first acceptance discussed them: S0007 ($5.04) and S0003 ($4.16) stood out, by size and by questions caused by their drafted text. The three follow-up stories cost little:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0011 | 6 | 3.5 | $1.23 |
| S0012 | 6 | 3.0 | $0.74 |
| S0013 | 6 | 2.1 | $0.67 |

None stands out. Each took the minimum of six runs with no question, because their pre-checks had already settled the text (decision 36). The acceptances cost more than the stories that came from them. The first used 57.4 min and $4.99 in one run. This one's first attempt stalled at 60 min, mostly on `make mutants` and re-checking survivors. That is the cost of the mutation finding in 3.

## Proposed stories

- `drafts/F0014-S0014-the-operator-guides-opening-after-the-first-start.md`: documentation only. It brings the operator guide's opening paragraph up to the first start, in the README's words, which S0013's documenter saw stale and was not allowed to touch.

## Log (append only)

1. stage feature stalled: timed out after 60 min; partial work committed
2. acceptor: accepted; 1 draft proposed; make mutants 5179/6996 (partial: 5446 checked, 263 survived, 4 timeouts, 1550 unchecked)
      1. Scope: none. S0001–S0010 were mapped by the first acceptance (pull request 201). S0011 and S0012 added tests only, S0013 changed documents only, and all three are covered by FEATURE.md decisions 34–36. Nothing out of scope was built.
      2. Feature demo: green. I re-ran the first acceptance's script through `read_settings`, `build_boundaries`, `run_sealed`, `ClaudeCodeRuntime` and `GitCli`, extended with S0011's cases. Both nested repositories were removed, sorted (`b/.git`, `notes/.git`). The links to an outside repository and to `.` were not followed, and both `.git` folders were kept. The token came from the file and was in no argument. Neither the hook nor `core.fsmonitor` ran under the factory's git. An opened `.git` and a UTF-16 login file were each refused. The cost record carries `instance`, and the journal record carries `at`, `stage` and `run`.
      3. Mutants: one 540 s run, partial, 95.1 % of the checked mutants killed. S0011 and S0012 killed what they were written for. The two `_nested_repositories` survivors left (`followlinks=None` and the keyword dropped) are equivalent. Four of the five `_early_stall` "survivors" die when re-run by hand, because mutmut's test map for that function is stale. One real survivor remains, the left-branch stall's empty detail, which is older than F0014 (F0005-S0005); no draft. The stale map and the run that cannot finish in 540 s remain a note for the human.
      4. Noticed: S0013's documenter left the operator guide's opening line stale (→ S0014). Correcting the first acceptance: the pytest `rm_rf` garbage warnings come from mutmut runs, whose mutated `seal` leaves a `.git` of mode `020`, not from a test row. They are harmless, so no draft.
      5. Docs: `documents ok`, and all five of S0013's edits are in place. The operator guide's opening still says "a run against a real repository with a token is not observed yet", while the README now records the first start (→ S0014).
      6. Decisions: 34–36 are new (S0011's and S0012's leaves, and the human's five pre-check answers). 5–33 and the answers from the story logs, which the first acceptance listed, are still open for the human to confirm. S0011–S0013 asked no question.
      7. Slow checks: `make check` green (99.47 %), duplicates 0 new / 39 known, documents ok. There is no image scan or SBOM target. The observations as `agent` are left to the shakedown run.
      8. Cost: 105 runs, 95.7 min, $25.65. S0011–S0013 cost $2.64 together, six runs each with no question. No story stands out beyond S0007 and S0003, which the first acceptance already explained.
