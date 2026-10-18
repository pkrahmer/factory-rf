---
stage: done
pr: 201
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0014-S0001, F0014-S0002, F0014-S0003, F0014-S0004, F0014-S0005, F0014-S0006, F0014-S0007, F0014-S0008, F0014-S0009, F0014-S0010]
outcome: accepted
---
# Acceptance of The first start's findings

## Verdict

**Accepted with drafts.** Every scope item of `FEATURE.md` has a story that built it. The feature demo is green: a hostile agent run went through the real wiring, `run_sealed`, `ClaudeCodeRuntime` and `GitCli`. The factory's git ran no hook and no `core.fsmonitor`. The nested repository was removed, an opened `.git` was refused, and the token reached `claude` through no argument. The new records carry their stamps. No finding breaks a promise. One rule was promised and no test pins it: the nested-repository walk does not follow symbolic links. There is one stamp no test pins: the done entry of an acceptance merged before approval. And four places in the documents are stale. Each of these has a draft.

## 1 Scope

None. Each scope bullet maps to a story:
- the hooks (S0001);
- the `.git` seal, in its git half (S0006) and its run half (S0009);
- the nested repositories (S0010);
- the image's trust (S0002);
- the token file, in its factory half (S0003) and its image half (S0004);
- the guide (S0004's docs criterion, S0005);
- the stamps (S0007, S0008).

No story is outside the scope. I checked FEATURE.md's "Done when" against the code:
- `git_environment()` returns nine entries: `core.sharedRepository=0640`, `core.hooksPath=/dev/null` and `core.fsmonitor=false` (`src/factory/entry/wiring.py:138`).
- `run_sealed` seals, runs, then calls `check_seal()` and `remove_nested_repositories()` in its `finally` (`src/factory/application/sealed_runs.py`).
- `image/gitconfig` holds exactly `safe.directory=/work/checkout`, and the Dockerfile copies it to `/etc/gitconfig` with mode `0644`.
- `ENV FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token` is set, and the compose file mounts `./secrets/claude-token` there.
- Every `append_entry`, `book_merge` and `book_refusal` call in `src/factory` passes `at=`. I grepped all 21 call sites.
- `CostRecorder.begin` sets `instance`.

The out-of-scope items stayed out. These are the API key, the gitlink refusal, the clone's parent folder, the project commands, the status map itself and a `run` on `crash` and `expiry`. One change came from outside the stories. The human took `planning/` out of ruff (a5c2f55a) to unblock S0001's tests stage. It is not a story, and it is not in scope.

## 2 The feature demo

The walk-through is a single script, `/tmp/f0014-acceptance/feature_demo.py`, outside the repository. It goes through the real entry points:
- the settings come from `read_settings`, as an instance reads its environment, with `checkout` and `state_directory` moved to a temporary folder;
- the boundaries come from `factory.entry.wiring.build_boundaries`, with the `FakeHostingService` in place of PyGithub;
- the remote is a real bare one.

The agent is a stand-in `claude` executable that behaves like a hostile agent:
- It records whether `CLAUDE_CODE_OAUTH_TOKEN` is in its environment and whether the token is in its argument list.
- It writes `.git/hooks/pre-commit`, sets `core.fsmonitor` in `.git/config`, and makes a repository at `notes` with its own `core.fsmonitor`. Every one of these commands leaves a marker file when it runs.
- In a second run it opens `.git` to its group.

The request's own `CLAUDE_CODE_OAUTH_TOKEN=from-request` must be dropped. The demo runs as one user, so the agent can write `.git` as the owner. The second user is the image's and plan step 4's. What the demo shows is everything the factory does around the run.

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

```
$ uv run python /tmp/f0014-acceptance/feature_demo.py
1. run_sealed: the agent writes a hook, core.fsmonitor and a nested repository
   end: completed doing
   agent saw: {"token": "demo-login-token", "token_in_argv": false}
   nested repositories removed: ['notes/.git']
   .git entries open to group or others after the seal: 0
2. the factory's git commits the agent's work
   status paths: ['notes/a.txt', 'result.txt']
   committed: ['notes/a.txt', 'result.txt']
   markers after the factory's git: []
   markers after a plain git commit: ['fsmonitor-2', 'hook-pre-commit']
3. an agent that opens .git to its group
   RepositoryUnsealed: seal failed (no exit status): /tmp/f0014-demo-ytvjpdce/checkout/.git is writable by its group or by others
4. a login file written as UTF-16
   AgentRuntimeError: agent runtime failed: cannot read the agent's login file /tmp/f0014-demo-ytvjpdce/claude-token: not ASCII text
5. the cost record names its instance; the journal record its time, stage and run
   {"run":"<run id>","work_item":"F0099-S0001","stage":"doing","role":"coder","attempt":0,"status":"started","started_at":"2026-10-18T01:32:51.391530Z","duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":null,"instance":"demo-instance"}
   journal:
   - number: 1
     speaker: coder
     kind: result
     at: '2026-10-18T01:32:51.391735Z'
     stage: doing
     run: <run id>
```

Green. The run id, 32 hex digits, is shown as `<run id>`, since `make secrets` refuses it as a high-entropy string. What each step shows:
- The token comes from the file and is in no argument. The request's own value is dropped.
- The nested repository is gone, and its file `notes/a.txt` is committed as an ordinary file, as decision 31 says.
- The factory's `status` and `commit` started neither the hook nor either `core.fsmonitor`. A plain git commit in the same checkout then ran both the hook and the checkout's `core.fsmonitor`, so the attack was real.
- An opened `.git` raises `RepositoryUnsealed` after the run.
- A UTF-16 login file stops the run with the guide's message.
- The cost line ends with `"instance":"demo-instance"`, and the journal record carries `at`, `stage` and the run's id.

The image half:
```
$ git config --file image/gitconfig --list
safe.directory=/work/checkout
$ grep -n 'gitconfig\|CLAUDE_LOGIN_FILE\|claude-token' image/Dockerfile image/compose.yml
image/Dockerfile:41:COPY image/gitconfig /etc/gitconfig
image/Dockerfile:42:RUN sed -i 's/\r$//' /etc/gitconfig && chmod 0644 /etc/gitconfig
image/Dockerfile:50:ENV FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token
image/compose.yml:27:        source: ./secrets/claude-token
image/compose.yml:28:        target: /home/agent/.claude-token
```

`make check` was green as I found it (`check: green`, total coverage 99.47 %).

## 3 Mutation score

`make mutants FEATURE=F0014` selects 30 modules with 6,996 mutants. It ran twice, and both runs ended with `mutants: stopped after 540 s; the results below are partial, run it again to go on`:
- The first run checked mutants up to `4007/12230` (12,230 is mutmut's count over the whole package).
- The second run spent its 540 s on one mutant (`4008/12230`). This is the same stall F0012's acceptance reported.

So I ran `uv run mutmut run` on F0014's own module selections, within 520 s each:
- `domain.journal`, `adapters.cost_records_jsonl` and `adapters.work_item_markdown`: completed.
- `domain.decisions`, `domain.errors`, `application.costs` and `application.opening`: completed.
- the handlers, `claims`, `stalls`, `recovery` and both `acceptance` modules: stopped by the timeout.

The counts come from mutmut's `.meta` files over the 30 modules:
- **4,487 killed, 244 survived and 4 timeouts, out of 4,735 checked (94.8 %).**
- 2,261 are unchecked. Most are in modules the whole suite reaches: `git_cli` 705, `stage` 552, `claude_runtime` 393, `claims` 139, `domain.acceptance` 123, `acceptance` 116, `wiring` 116 and `recovery` 58.

**The survivors overstate the gaps.** Mutmut kept its cached test map in `mutants/mutmut-stats.json` and re-collected it only for new tests. A function that S0010 split out of an older one, `AfterAgent._early_stall`, is mapped to 5 tests, and the older tests that call it are missing. Three of its "survivors" (`_early_stall__mutmut_6`, `_9` and `_12`) die in the mutated tree when I run `PYTHONPATH=src MUTANT_UNDER_TEST=<id> pytest tests/application/test_after_agent.py` from `mutants/`. I therefore re-ran each survivor in a function F0014 wrote or changed this way, against its test modules. These survive for real:
- **The nested-repository walk** (`git_cli._nested_repositories`, S0010):
  - `os.walk(root, followlinks=True)` and dropping `followlinks` both survive. Decision 31 says the walk "does not follow symbolic links", and no row has a symbolic link to a folder that holds a `.git`. If the walk followed such a link, it would remove that repository's `.git` through the link, even the checkout's own `.git` through a link to `.`.
  - Pruning `.git` from the walk (`".git" in folders` → `"XX.gitXX"`) also survives: no row has a `.git` inside a `.git`.
- **The list of paths in three messages** (S0010): `", ".join(...)` → `"XX, XX".join(...)` survives in the stage's stall detail (`stage.AfterAgent._early_stall`), the probe item's detail (`preflight.agent_run_probe_item`) and the preparer's log line (`scheduler.CheckoutPreparer._keep_or_clone_again`). Every test removes exactly one repository.
- **The stamp of an acceptance merged before approval** (S0007): in `domain.acceptance.book_merge`, `at` → `None` survives on the `before_approval` branch. Criterion 6 of S0007 was tested only on the plain branch, so that done entry could lose its `at` and `stage` unnoticed.
- **Near-equivalent, no draft:**
  - `_login_refusal`'s `_parse_reply(None)` (S0003). It differs only for a run that printed a good reply and also a `factory-login:` line, which the login shell prints only when it does not start `claude`.
  - `discard`'s error detail `str(error)` → `None` (S0006).
  - `cost_records_jsonl._line_of_record`'s `model_dump(mode=...)` (S0008). Every field that is not JSON is overwritten on the next lines.

The other survivors are in lines older than F0014; I checked the blame of the samples. They fall into the groups earlier acceptances named:
- no-state messages (`require_state(..., None)`, `ValueError(None)`): the handlers, `costs.begin` and `merged._archived`;
- wiring pass-throughs (`build_boundaries`, `run_instance`);
- `settings` helpers;
- the stall context's `pull_request` and `undo`.

No new draft for these.

A finding for the human, not a story, because the `Makefile` and `mutants/` are outside the stage's lane. As it stands, `make mutants` reuses a test map that is stale for functions split out of older ones, and it stalls on one mutant. The F0013 acceptance moved `mutants/` aside to get a true count. A fresh `mutants/` per feature acceptance would give true survivors. So would a target that sets mutmut to re-collect its stats. It still would not finish 30 modules in 540 s.

## 4 What the stories noticed

- S0003, the documenter: "the criterion asks the entry to give the API key's reason for being left out, and the story records none". FEATURE.md's "Out of scope" does give it. → Draft S0013.
- S0006, the coder: `scheduler.py` in `factory.application` now imports `os` for `os.path.lexists`, so that a dangling link at `.git` counts as existing. The reviewer accepted it. There is no layer rule against `os`, so no draft.
- S0007, the coder: `CommentCopier.append` reads the clock once per comment, so comments copied in one tick may differ in `at` by microseconds. This matches the Interface. No draft.
- S0003, intake: no row for a login file without read permission, because root ignores permissions. The folder row takes the same branch of the script.
- FEATURE decision 22: `test_an_existing_clone_is_kept_without_calling_git` clones under the test run's umask. Under `0002` (inside the container) the preparer would clone again. Whoever runs `make test` in the image should know this.
- Mine: a row of `tests/adapters/test_git_cli_seal.py::test_seal_takes_the_group_and_others_write_bits_and_keeps_every_other_bit` leaves a `.git` of mode `020`. pytest cannot remove it, and each run leaves a `garbage-*` folder under `/tmp/pytest-of-<user>` with an `rm_rf` `PytestWarning`. I saw it in the mutation runs. It is harmless and small. A fixture that restores the mode would end it, and it could ride along with the next story that touches that module. No draft of its own.
- S0001: `make lint` was red over the human's `planning/` scripts. The human fixed it. The S0003 and S0010 coders noted the human's `docs/runs/` night log arriving with a merge. Nothing further.

## 5 The documentation as a whole

`make documents` prints `documents ok`. Reading as a newcomer, I found four stale places, none of which misleads an operator into a wrong action. → Draft S0013.
- `docs/decisions.md`, "The agent's login is a token from a file": "the reason for the API key's absence is not recorded in the story". FEATURE.md gives it: subscription against usage billing, and Claude Code prefers an API key it finds, so a stray key file would change who pays.
- `docs/decisions.md`, "The factory's git runs no hooks": "Now `git_environment` returns seven entries … `GIT_CONFIG_COUNT=3`". Since S0006 and S0010 it returns nine and `4`. The F0010-S0003 entry got a "since F0014-S0006" note; this one did not. The project guide is right ("exactly nine entries").
- `docs/operator-guide.md`, "The agent runtime", first sentence: "it needs the `claude` program and a session you have already logged in to". Since S0004 the login is the token file, and a session is only the fallback when the file is empty. The section's second paragraph says so, so the first sentence contradicts it.
- `docs/operator-guide.md`, "The agent runs as a second user": the command line is still `sudo -n -u agent -- timeout --signal=KILL <limit>s env -i NAME=value ... claude ...`. Since S0003 a login shell (`/bin/sh -c <script> factory-login <file>`) stands before `claude`. `docs/project-guide.md:300` has it right.
- `README.md`'s status paragraph still ends with the Podman probe "up to the stop `repository_unavailable`; a run against a real repository with a token is not observed yet". The first start of 2026-10-17 (both instances healthy on the todo demo's project, as FEATURE.md's Goal records) is not mentioned. This is small and goes in the same draft.

## 6 Decisions taken for the human

To accept or revisit. These are from FEATURE.md, "taken by the session for the human, to confirm":
- 5 and 29: the story count and build order (ten stories); S0007 and S0008 split for size.
- 6: `/dev/null` as the hooks path, kept in `git_environment` and not in `GitCli`.
- 7, 14, 23, 27 and 32: the leaves to change earlier tests in S0001, S0004, S0006, S0007 and S0010.
- 8: `image/gitconfig`, `root:root` `0644`, one `safe.directory` entry.
- 9 as changed by 30 (c): the token is read by the call's own shell, the allow list keeps six names, and a request's value is dropped.
- 10 and 33: the file's states; the ASCII rule refuses UTF-16; an empty host file keeps the manual login.
- 12: the variable's name and the container path; `1001:1002` `0440` on Linux.
- 13: the probe's detail names the file, with no preflight item of its own.
- 16 and 18: S0005 is docs only, and S0002 and S0003 need no leave.
- 20, 21 and 22: `0640` plus a seal that does not rest on git's internals; the seal at every iteration and around every run; a failed check removes and clones again rather than stopping; tests without a second user, and the real check left to step 4.
- 24: S0006 split into S0006 and S0009.
- 26: `at` and `run` are optional keywords of `append_entry`; the stage is read from the state; unset fields are left out.
- 28: `instance` is set by `CostRecorder.begin` from the settings; the key is left out when unset, while `image` stays `null`.
- 31: the removal is one `Git` operation with no git process; it stalls `nested_repository`, and the probe fails its item.

These are from the story logs:
- S0001 entry 5: `planning/` is out of ruff (the human's change).
- S0003 entry 5: the probe test builds a `completed` result with its decision.
- S0003 entry 9: `PLR0913` is ignored per file for `claude_runtime.py` in `pyproject.toml`, in place of a `noqa`.
- S0006 entry 3: a criterion for `GIT_CEILING_DIRECTORIES` that no `GitOptions.environment` can lift, and the per-entry owner rule dropped from the Interface.
- S0006 entry 7: the `cloned` test helper takes `group_umask`.
- S0007 entry 5: a `move_back` entry carries the stage the human set (`approval`).
- S0007 entry 13: the demo's second command was rewritten.
- S0009 entry 5: `outcome: str` in the dispatcher test.
- S0010 entries 3 and 7: eight test rows, and the note checked with `in`.

These were taken by agents without asking, and they are recorded in the decision log:
- The S0007 coder wrote the journal records with `model_dump(exclude_none=True)`, so every future optional field of a record is also left out when unset. The decision log says so.
- The S0003 documenter wrote "not recorded" for the API key's reason (see 5).

## 7 The slow checks

- `make duplicates`: `duplicates: 0 new, 39 known, 0 gone`.
- `make documents`: `documents ok`.
- The project offers no image scan or SBOM target.
- The observations F0014 left for plan step 4 cannot run here, because they need the real image and two users:
  - `git status` as `agent`;
  - the `.git` seal as `agent`, with three `Permission denied`;
  - the probe passing on a new instance with only the token file;
  - `grep "cloning the checkout again" /state/factory.log` once after the upgrade.

  They are in the operator guide's morning observations, for the human's shakedown.

## 8 Cost

The feature cost 87 runs, 87.1 min and $23.01 in total. Per story:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 8 | 6.3 | $1.39 |
| S0002 | 6 | 3.5 | $0.97 |
| S0003 | 12 | 13.1 | $4.16 |
| S0004 | 6 | 3.4 | $1.04 |
| S0005 | 6 | 1.6 | $0.54 |
| S0006 | 10 | 14.1 | $3.18 |
| S0007 | 14 | 18.8 | $5.04 |
| S0008 | 6 | 4.3 | $1.10 |
| S0009 | 9 | 7.2 | $1.74 |
| S0010 | 10 | 14.8 | $3.85 |

S0007 stands out, and S0003 next. Both are large by design: S0007 changed 14 source modules and 26 earlier tests. Both also went through two questions that came from the story text, not from the work:
- S0007's Interface and a test disagreed on the `move_back` stage, and its demo named a test module that the tester never made.
- S0003's demo row built a `completed` result the domain refuses. The `noqa` that FEATURE decision 33's story text accepted then broke a structural test, which the human solved in `pyproject.toml`.

S0010 had the same kind of question: the note was compared by equality against a post that always carries the marker. Six of the feature's nine human answers fixed a contradiction in the drafted text. A pre-check that runs the drafted tests and demos against pinned behaviour would have saved about a run or two each. S0001's extra two runs were the `planning/` lint block.

## Proposed stories

- `drafts/F0014-S0011-the-nested-repository-walks-untested-sides.md`: decision 31's "does not follow symbolic links" and "does not enter a `.git`", and the list of two or more paths in the stall, probe and log texts. These are real survivors, one of them a removal through a link.
- `drafts/F0014-S0012-the-stamp-of-an-acceptance-merged-before-approval.md`: the `before_approval` branch of `book_merge` drops `at` unnoticed, which is S0007's criterion 6 on its other branch.
- `drafts/F0014-S0013-the-login-and-git-environment-in-the-documents.md`: documentation only. It covers the API key's recorded reason, the hooks entry's stale count, the operator guide's "a session you have already logged in to" and the `sudo` command line without the login shell, and README's status paragraph.

## Log (append only)

1. acceptor: accepted with drafts; 3 drafts proposed; make mutants 4487/6996 (partial: 4735 checked, 244 survived, 4 timeouts, 2261 unchecked)
   1. Scope: none. Every scope bullet has its story, and FEATURE.md's "Done when" is in the code: nine git environment entries, `run_sealed`, `image/gitconfig`, the token mount, all 21 `append_entry`/`book_*` calls passing `at=`, and `instance` set in `CostRecorder.begin`. Nothing out of scope was built.
   2. Feature demo: green. One script uses the real wiring (`read_settings` and `build_boundaries` with the fake hosting service) and a hostile stand-in `claude`:
      - The token came from the file, in no argument, and the request's own token was dropped.
      - The hook and both `core.fsmonitor` commands did not run under the factory's git. A plain git commit afterwards ran them, so the attack was real.
      - The nested `.git` was removed.
      - An opened `.git` raised `RepositoryUnsealed`, and a UTF-16 login file raised "not ASCII text".
      - The cost line carries `instance`, and the journal record carries `at`, `stage` and `run`.
   3. Mutants: `make mutants` stopped twice at 540 s. The second run stalled on one mutant, as in F0012. I ran the rest on module selections by hand. mutmut's cached test map is stale for functions split out of older ones: three `_early_stall` "survivors" die when re-run by hand. Re-run that way, the real F0014 survivors are:
      - the nested walk following symbolic links, and entering `.git` (→ S0011);
      - the `", "` path list in three texts (→ S0011);
      - `book_merge`'s `before_approval` branch dropping `at` (→ S0012);
      - three near-equivalent ones.
      The Makefile and cache finding is for the human.
   4. Noticed: the S0003 documenter wrote that the API key's reason was "not recorded", but FEATURE.md gives it (→ S0013). `os.path.lexists` in the application layer and the per-comment clock reads are accepted and need no draft. New: a seal test row leaves an unremovable mode-`020` `.git` in pytest's temporary folder, which gives an `rm_rf` warning; no draft.
   5. Docs: `documents ok`, but five places are stale (→ S0013):
      - the API key's reason in `decisions.md`;
      - the hooks entry's "seven entries";
      - the operator guide's "a session you have already logged in to";
      - the `sudo` command line without the login shell;
      - the README's status paragraph, which predates the first start.
   6. Decisions: FEATURE decisions 5–33 that are marked "to confirm", ten answers from the story logs, and two choices agents made without asking (`exclude_none` for every future field; "not recorded").
   7. Slow checks: duplicates 0 new / 39 known, documents ok, and no image scan or SBOM target. The observations as `agent` are left to the shakedown.
   8. Cost: 87 runs, 87.1 min, $23.01. S0007 ($5.04, 14 runs) and S0003 ($4.16, 12 runs) stand out: both are large, and both had two questions caused by contradictions in the drafted story text. Six of the nine human answers in the feature were of that kind.
   Note: I replaced the pasted run id with `<run id>`, because `make secrets` refused it as a high-entropy hex string. The demo script is in `/tmp/f0014-acceptance/feature_demo.py` and is also pasted in the report.
2. done (pull request merged); cost: 1 runs, 57.4 min, 92 turns, 205k tokens in (9971k more from cache), 68k out, $4.99
