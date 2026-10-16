---
stage: done
pr: 136
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0010-S0001, F0010-S0002, F0010-S0003, F0010-S0004, F0010-S0005, F0010-S0006, F0010-S0007, F0010-S0008, F0010-S0009, F0010-S0010, F0010-S0011, F0010-S0012, F0010-S0013, F0010-S0014, F0010-S0015, F0010-S0016, F0010-S0017]
outcome: accepted
---
# Acceptance of The machine

## Verdict

**not accepted**, as a recommendation. Two drafts repair it: F0010-S0018 for the documentation, F0010-S0019 for `factory-run`. The code does what `FEATURE.md` promised:

- The end-to-end feature demo (section 2) is green, from the settings through the loop, the preflight with its stamp and probe, the stops and the health check, to the agent run as `agent` with no token in its environment.
- `make check` is green.
- A hand mutation pass killed 22 of 24 mutants.

But the README contradicts the feature's own behaviour in a way that misleads a newcomer:

- It says `factory-health` "is declared in `pyproject.toml` but not built: it ends with a `ModuleNotFoundError` until F0010". The command prints `healthy` and exits 0.
- It says that `factory-run` with an invalid environment "ends with status 2 and a machine stop". Run the way the README's getting-started section runs it, outside the image, it ends with two tracebacks and status 1, because `/state` cannot be created.

The project guide also still says `os_user=None` and "scrubbing is F0010's". The role's rule makes a misleading contradiction between documentation and behaviour a `not accepted`. Each finding is small, and five drafts repair them or pin what the mutation pass left open. If the human holds the README's sentences to be low weight, `accepted with drafts` is the verdict for the same report.

## 1 Scope

None. Every scope item has its stories and its code, and the Goal's conditions are each shown by a test or, for Docker, root and the second user, by a static test of the files plus the morning observations the operator guide lists:

| Scope item | Stories | Code |
|---|---|---|
| One instance, one project: settings, URL without a password, fixed checkout, reclone, loop and pauses | S0001, S0002, S0004 | `src/factory/domain/settings.py` (`read_settings`, `_holds_password`), `src/factory/application/scheduler.py` (`pause_after`, `Scheduler`, `CheckoutPreparer`), `src/factory/entry/run.py` (`main`, `run_instance`, `activity`) |
| The boundaries: `build_boundaries`, the token read once, `owner/name`, the git options, the run, `factory-watch` | S0003, S0004, S0005 | `src/factory/entry/wiring.py` (`build_boundaries`, `repository_name`, `read_hosting_token`, `git_environment`, `git_options`, `boundaries_from_environment`), `src/factory/entry/watch.py` |
| The pinned image, the identity at build, the identity in each cost record | S0006 | `image/Dockerfile`, `src/factory/application/costs.py` (`CostRecorder._image`), `tests/test_image.py` (`floating_references`) |
| The health check and the entrypoint's stops | S0007 | `src/factory/entry/health.py`, `image/compose.yml`, `image/entrypoint.sh`, `RepositoryWaiter` in `scheduler.py` |
| The preflight's items | S0008, S0013, S0015, S0016 | `src/factory/application/preflight.py` (`MachineChecks`, `tool_item`, `token_file_item`, `agent_user_item`, `agent_environment_item`, `agent_run_probe_item`), `machine_extras` in `wiring.py` |
| The probe on main and the stamp | S0009, S0010 | `Preflight` in `preflight.py`, `src/factory/adapters/preflight_stamp_file.py`, `build_preflight` and `build_tick` in `wiring.py` |
| Agent files without dead keys; the shipped agents, settings and template | S0011, S0012, S0017 | `APPLIED_AGENT_KEYS` in `src/factory/domain/agent_runs.py`, `src/factory/adapters/agent_files.py`, the pipeline loader; `claude/agents/*.md`, `claude/settings.json`, `template/` |
| No token in an agent run; agent runs as a second user | S0013, S0014, S0015 | `scrub_environment`, `production_environment`, `agent_run_environment`, `image/git-credential-factory`, `image/sudoers-factory-agent`, `ClaudeCodeRuntime` (`sudo -n -u … -- env -i`, `RUN_FILE_MODE`) |

No story went outside the scope. Out of scope stayed out:

- There is no watchdog, and no preflight check of the project's setup or of the token's expiry.
- There is no sandbox.
- The project commands still run as `factory` (decision 24).
- No `time_limit` is enforced under `sudo` (decision 30, open).
- No skill file is shipped.

One thing is a near-miss rather than a gap. The shipped `claude/settings.json` carries v1's `git add` and `git commit` permissions, while the shipped agent texts say no agent commits. "Each key with an effect" holds only loosely there (draft F0010-S0020).

## 2 Feature demo

**Green.** The walk is the operator's: the environment of the image, the settings read from it, one instance's loop through `Scheduler`, `RepositoryWaiter`, `CheckoutPreparer` and one `build_tick` tick for the whole run (as `run_instance` builds them), and the container's health check after each step. It runs against a real bare remote with a human clone, the shipped agents copied from `claude/` into the agent home, the template's pipeline definition, the production `build_boundaries` (with `FakeHostingService` given as `hosting`) and `FakeAgentRuntime` in place of `claude -p`. The settings' fixed `/work/checkout` and `/state` are moved into a temporary directory, as the tests do. The script is in the details block below. The guard refuses files outside the repository's lanes, so it was written to `/tmp/f10demo/demo.py` and run from the repository root:

```bash
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 uv run python /tmp/f10demo/demo.py | sed "s|/tmp/tmp[a-z0-9_]*|<tmp>|g"
```

```text
== 1. settings from the environment ==
instance: factory-1 | checkout: /work/checkout | state: /state | image: build-1 | agent user: agent
git environment: {'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_0': 'credential.helper', 'GIT_CONFIG_VALUE_0': '/usr/local/bin/git-credential-factory', 'GIT_CONFIG_KEY_1': 'core.sharedRepository', 'GIT_CONFIG_VALUE_1': 'group'}
== 2. the loop: reclone, preflight, a stage, idle, red main, fix, dead key, reclone ==
   tick 1: event=run dispatch=handled stopped=None -> activity=True
   sleep 15 s
   requests so far: [('coder', 'agent', datetime.timedelta(seconds=120)), ('intake', 'agent', datetime.timedelta(seconds=2400))]
   stage run environment names: ['HOME', 'LANG', 'PATH'] | token in it: False
   stamp: {"image":"build-1","main_probed":"<the 40-character commit of main>","main_failed":null}
   tick 2: event=ask dispatch=handled stopped=None -> activity=True
   sleep 15 s
   -- human pushes a red lint to main --
2026-10-16T15:54:03Z stop repository main_branch_failing: lint is red on main at 385546b1ab98: E501 line too long
   tick 3: event=None dispatch=None stopped=main_branch_failing -> activity=False
   sleep 30 s
   factory-health exit 1: 'main_branch_failing (repository): lint is red on main at 385546b1ab98: E501 line too long (since 2026-10-16T15:54:03Z)'
   -- human pushes the fix --
2026-10-16T15:54:03Z stop cleared main_branch_failing
   tick 4: event=idle dispatch=handled stopped=None -> activity=False
   sleep 60 s
   factory-health exit 0: 'healthy'
   -- operator's coder.md gains a dead key `skills: [x]` --
2026-10-16T15:54:03Z stop repository agent_definition_invalid: coder: key not applied by the agent runtime: skills
   tick 5: event=None dispatch=None stopped=agent_definition_invalid -> activity=False
   sleep 120 s
   factory-health exit 1: 'agent_definition_invalid (repository): coder: key not applied by the agent runtime: skills (since 2026-10-16T15:54:03Z)'
   -- coder.md restored; the checkout is deleted --
2026-10-16T15:54:03Z stop cleared agent_definition_invalid
   tick 6: event=idle dispatch=handled stopped=None -> activity=False
   sleep 120 s
   checkout recloned: True | factory-health exit 0: 'healthy'
pauses: [15, 15, 30, 60, 120, 120] | agent runs: ['coder', 'intake']
== 3. a new image build: the machine items run again; sudo missing ==
2026-10-16T15:54:03Z stop machine preflight_failed: tool:sudo: sudo is not on the PATH; add it to the image
   stopped: preflight_failed | agent runs started by the preflight: 1
   factory-health exit 1: 'preflight_failed (machine): tool:sudo: sudo is not on the PATH; add it to the image (since 2026-10-16T15:54:03Z)'
2026-10-16T15:54:04Z stop cleared preflight_failed
   with sudo: stopped: None | factory-health exit 0: 'healthy'
== 4. factory-run and factory-watch with an invalid environment ==
   factory-run exit: 2 | factory-health exit 1: 'preflight_failed (machine): FACTORY_INSTANCE: missing (since 2026-10-16T15:54:04Z)'
   log tail: 2026-10-16T15:54:04Z settings invalid: FACTORY_INSTANCE: missing
   factory-watch exit: 2 | stderr: factory-watch: settings invalid: FACTORY_INSTANCE: missing
```

What the walk shows, step by step:

- **Settings.** They come from the environment, and the git environment carries the credential helper and the shared group.
- **The first iteration.** It clones the missing checkout and runs at once. The preflight runs its twelve items and probes `lint` on `main`, and the stamp records the image and the probed commit. The preflight's probe and the intake stage both run as `agent`, the probe with its 2-minute limit, and the stage's environment holds only `HOME`, `LANG` and `PATH`, without the token.
- **Idle ticks.** They start no agent run and probe no unchanged main: the list of agent runs stays at two.
- **A red main.** It is the stop `main_branch_failing`, and `factory-health` exits 1 with its line. The fix clears it.
- **A dead key.** The operator's `coder.md` with `skills:` is the stop `agent_definition_invalid` naming the agent and the key, and it clears when the file is restored.
- **A deleted checkout.** It is recloned.
- **The pauses.** They follow activity: 15, 15, then doubling to 120.
- **A new image identity.** It runs the machine items again. A missing `sudo` is the machine stop `preflight_failed` naming `tool:sudo`, and `sudo` back on the `PATH` clears it.
- **An invalid environment.** `factory-run`'s `main` returns 2 with a time-stamped line and a machine stop, and `factory-watch` returns 2 with `settings invalid` on standard error.

The same commands outside the image, from a shell with an empty environment:

```bash
env -i PATH="$PATH" HOME="$HOME" uv run factory-run; echo "factory-run exit=$?"
env -i PATH="$PATH" HOME="$HOME" uv run factory-watch; echo "factory-watch exit=$?"
env -i PATH="$PATH" HOME="$HOME" uv run factory-health; echo "factory-health exit=$?"
```

```text
2026-10-16T15:54:04Z settings invalid: FACTORY_REPOSITORY_URL: missing
Traceback (most recent call last):
  File "/work/factory-rf/src/factory/entry/run.py", line 122, in main
    settings = read_environment_settings(os.environ if environ is None else environ)
  ...
factory.domain.errors.SettingsInvalid: FACTORY_REPOSITORY_URL: missing

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  ...
  File "/work/factory-rf/src/factory/entry/run.py", line 132, in _stop_the_machine
    machine_log(state_directory, clock).line(f"settings invalid: {error}")
  File "/work/factory-rf/src/factory/adapters/factory_log.py", line 29, in line
    self._path.parent.mkdir(parents=True, exist_ok=True)
PermissionError: [Errno 13] Permission denied: '/state'
factory-run exit=1
factory-watch: settings invalid: FACTORY_REPOSITORY_URL: missing
factory-watch exit=2
healthy
factory-health exit=0
```

Inside the image `/state` belongs to `factory`, so the promise holds there. The traceback is what a newcomer gets from the README's getting-started path, and what an operator gets from a `state` volume mounted with the wrong owner (draft F0010-S0019). `factory-health` here prints `healthy`, contrary to the README's `ModuleNotFoundError` (draft F0010-S0018).

<details><summary>The demo script (<code>/tmp/f10demo/demo.py</code>)</summary>

```python
"""Feature demo of F0010: one instance, its loop, preflight, stops and health, end to end."""
import dataclasses, io, os, shutil, sys, tempfile
from contextlib import redirect_stdout, redirect_stderr
from datetime import timedelta
from pathlib import Path

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.scheduler import CheckoutPreparer, RepositoryWaiter, Scheduler
from factory.application.stops import StopService
from factory.domain.agent_runs import AgentRunResult
from factory.domain.settings import read_settings
from factory.entry import health, run, watch
from factory.entry.wiring import build_boundaries, build_tick, read_hosting_token
from git_support import make_remote, run_git
from human_clone import HumanClone

ROOT = Path(__file__).resolve().parents[0]
REPO = Path("/work/factory-rf")
tmp = Path(tempfile.mkdtemp())
remote = make_remote(tmp / "origin")
human = HumanClone(tmp / "human", remote)
assert (REPO / "template/factory/pipeline.yml").read_text() == run_git(remote, "show", "main:factory/pipeline.yml")
human.push_file("main", "Makefile", "lint:\n\ttrue\n")
story = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
human.push_file("main", story, "# First story\n\n## Description\n\nText.\n\n## Interface\n\nNone.\n\n## Acceptance criteria\n\n1. It works.\n2. make check stays green.\n3. docs: none.\n\n## Smoke test\n\n```bash\ntrue\n```\nExpect: nothing.\n\n## Journal\n")
human.start(story)

home = tmp / "home/agent/.claude"
shutil.copytree(REPO / "claude", home)
token = tmp / "hosting-token"; token.write_text("example-secret-token\n"); token.chmod(0o600)
image = tmp / "image-id"; image.write_text("build-1\n")
env = {"FACTORY_REPOSITORY_URL": str(remote), "FACTORY_INSTANCE": "factory-1",
       "FACTORY_IMAGE_ID_FILE": str(image), "FACTORY_TOKEN_FILE": str(token), "FACTORY_AGENT_USER": "agent",
       "FACTORY_CLAUDE_HOME": str(home), "FACTORY_CLAUDE_VERSION": "fake", "HOME": str(tmp / "home/agent")}

print("== 1. settings from the environment ==")
s = read_settings(env, read_file=Path.read_text)
print("instance:", s.instance, "| checkout:", s.checkout, "| state:", s.state_directory, "| image:", s.image, "| agent user:", s.agent_user)
s = s.model_copy(update={"checkout": tmp / "work/checkout", "state_directory": tmp / "state"})
hosting, runtime = FakeHostingService(), FakeAgentRuntime()
b = dataclasses.replace(build_boundaries(s, read_hosting_token(s.token_file), hosting=hosting), agent_runtime=runtime)
print("git environment:", {k: v for k, v in b.git._options.environment.items()} if hasattr(b.git, "_options") else "?")

def every_tool(name): return f"/usr/bin/{name}"
def hstatus():
    out = io.StringIO()
    with redirect_stdout(out): code = health.main([], store=b.health)
    return f"factory-health exit {code}: {out.getvalue().strip()!r}"

PROBE = AgentRunResult(end_reason="completed", decision="question", entry="probe", duration=timedelta(seconds=3))
ASK = AgentRunResult(end_reason="completed", decision="question", entry="Which user is meant?", duration=timedelta(minutes=1))
runtime.queue(ScriptedRun(result=PROBE)); runtime.queue(ScriptedRun(result=ASK))

tick = build_tick(b, s, every_tool)
outcomes = []
def counting_tick():
    o = tick.run(); outcomes.append(o)
    active = run.activity(o)
    print(f"   tick {len(outcomes)}: event={o.event.kind if o.event else None} dispatch={o.dispatch} stopped={o.stopped} -> activity={active}")
    return active
waiter = RepositoryWaiter(CheckoutPreparer(b.git, s), b, StopService(b))
coder = home / "agents/coder.md"; coder_text = coder.read_text()
def act(i):
    if i == 1:
        rq = runtime.requests()
        print("   requests so far:", [(r.agent.name if hasattr(r.agent, 'name') else '?', r.os_user, r.time_limit) for r in rq])
        envs = rq[-1].environment
        print("   stage run environment names:", sorted(envs), "| token in it:", any("example-secret-token" in v for v in envs.values()))
        print("   stamp:", (s.state_directory / "preflight-stamp.json").read_text().strip() if (s.state_directory / "preflight-stamp.json").exists() else sorted(p.name for p in s.state_directory.iterdir()))
    if i == 2:
        print("   -- human pushes a red lint to main --"); human.push_file("main", "Makefile", "lint:\n\t@echo 'E501 line too long'; false\n")
    if i == 3:
        print("  ", hstatus())
        print("   -- human pushes the fix --"); human.push_file("main", "Makefile", "lint:\n\ttrue\n")
    if i == 4:
        print("  ", hstatus())
        print("   -- operator's coder.md gains a dead key `skills: [x]` --"); coder.write_text(coder_text.replace("---\n", "---\nskills: [x]\n", 1))
    if i == 5:
        print("  ", hstatus())
        print("   -- coder.md restored; the checkout is deleted --"); coder.write_text(coder_text); shutil.rmtree(s.checkout)
    if i == 6:
        print("   checkout recloned:", (s.checkout / ".git").is_dir(), "|", hstatus())
sleeps = []
def sleep(sec):
    sleeps.append(int(sec)); print(f"   sleep {int(sec)} s"); act(len(sleeps))
print("== 2. the loop: reclone, preflight, a stage, idle, red main, fix, dead key, reclone ==")
Scheduler(prepare=waiter.prepare, tick=counting_tick, sleep=sleep, should_stop=lambda: len(sleeps) >= 6, log=b.log).run()
print("pauses:", sleeps, "| agent runs:", [r.agent.name for r in runtime.requests()])

print("== 3. a new image build: the machine items run again; sudo missing ==")
image.write_text("build-2\n")
s2 = read_settings(env, read_file=Path.read_text).model_copy(update={"checkout": s.checkout, "state_directory": s.state_directory})
b2 = dataclasses.replace(b, settings=s2)
before = len(runtime.requests())
runtime.queue(ScriptedRun(result=PROBE))
o = build_tick(b2, s2, lambda n: None if n == "sudo" else every_tool(n)).run()
print("   stopped:", o.stopped, "| agent runs started by the preflight:", len(runtime.requests()) - before)
print("  ", hstatus().replace(str(tmp), "<tmp>"))
runtime.queue(ScriptedRun(result=PROBE))
o = build_tick(b2, s2, every_tool).run()
print("   with sudo: stopped:", o.stopped, "|", hstatus())

print("== 4. factory-run and factory-watch with an invalid environment ==")
bad = {k: v for k, v in env.items() if k != "FACTORY_INSTANCE"}
err = io.StringIO()
with redirect_stderr(err), redirect_stdout(err): code = run.main(bad, state_directory=s.state_directory)
print("   factory-run exit:", code, "|", hstatus())
print("   log tail:", (s.state_directory / "factory.log").read_text().strip().splitlines()[-1][:120])
err = io.StringIO()
with redirect_stderr(err):
    saved = dict(os.environ); os.environ.clear(); os.environ.update(bad)
    code = watch.main([]); os.environ.clear(); os.environ.update(saved)
print("   factory-watch exit:", code, "| stderr:", err.getvalue().strip())
```

</details>

## 3 Mutation score

The project has no `make mutants` target. I ran a hand mutation pass instead: 24 mutants, one at a time, on the modules this feature wrote. Each mutant ran against the whole test suite (`uv run pytest -x --no-cov tests`). M1 to M6, M9 and M11 to M15 ran against the feature's own test modules and were killed there. M7, M8 and M18 survived that subset and were then killed by the whole suite. M16's first sed also hit `agent_run_environment`, so it ran again restricted to `machine_extras`, and the file was restored after each run. A file that the sed did not change counted as not applied; none were. **22 of 24 killed.**

| Mutant | Module | Result |
|---|---|---|
| M1 any stamp skips the machine items | `application/preflight.py` | killed |
| M2 an unknown image validates a stamp | `application/preflight.py` | killed |
| M3 a failed main is not remembered | `application/preflight.py` | killed |
| M4 a pass does not clear `preflight_failed` | `application/preflight.py` | killed |
| M5 the stop's detail names the full commit | `application/preflight.py` | killed |
| M6 the `time_limit` detail inverted | `application/preflight.py` | killed |
| M7 `token-file` allows group bits | `application/preflight.py` | killed |
| M8 `agent-user` fails without the token file existing | `application/preflight.py` | killed |
| M9 activity does not reset to the first pause | `application/scheduler.py` | killed |
| M10 `except Exception` narrowed to `except ValueError` | `application/scheduler.py` | **survived** |
| M11 an `idle` event counts as activity | `entry/run.py` | killed |
| M12 `factory-health` exits 0 with stops | `entry/health.py` | killed |
| M13 a URL with a password is allowed | `domain/settings.py` | killed |
| M14 whitespace in the URL is allowed | `domain/settings.py` | killed |
| M15 the agent's `HOME` is the `.claude` folder | `entry/wiring.py` | killed |
| M16 no `tool:sudo` item | `entry/wiring.py` | killed |
| M17 `sudo` without `-n` | `adapters/claude_runtime.py` | killed |
| M18 `skills` accepted in an agent file | `domain/agent_runs.py` | killed |
| M19 the probe runs as the factory's user | `application/preflight.py` | killed |
| M20 the probe runs without a guard | `application/preflight.py` | killed |
| M21 an existing directory without `.git` is not cloned into | `application/scheduler.py` | killed |
| M22 `core.sharedRepository` off | `entry/wiring.py` | killed |
| M23 a timed-out run as `agent` with a `sudo:` line is not a refusal | `adapters/claude_runtime.py` | **survived** |
| M24 the probe fails only on `died` | `application/preflight.py` | killed |

The surviving group is the scheduler's failure side. Criteria 7 and 8 of S0002 test one exception type, `ValueError`. The loop's real errors are `GitError`, `OSError`, `AgentRuntimeError` and library errors, and a narrowed handler would let any of them end the process with a traceback and a Docker restart loop (draft F0010-S0021). The second survivor is the runtime's refusal rule for a call that timed out. S0014's reviewer found it missing (entry 5, finding 1), and the coder added it in `0ebb835`, but no test pins it (`src/factory/adapters/claude_runtime.py:293`, draft F0010-S0022).

## 4 What the stories noticed

Collected from the coder, reviewer and documenter entries. Each item says where it now stands:

1. **S0001, coder.** `FACTORY_IMAGE_ID_FILE` set but blank falls back to `/opt/factory/image-id`, untested. It is harmless in the image, where the default is the real file. No draft.
2. **S0001, coder.** The default identity `factory <factory@noreply.invalid>` is written twice: `DEFAULT_GIT_IDENTITY` in `src/factory/domain/settings.py:18` and the default of `GitOptions.identity` in `src/factory/domain/git.py:46`. It is a second copy of a constant, and both copies agree today. A one-line refactor, too small for a draft of its own. A coder can take it with the next story that touches `domain/git.py`.
3. **S0003, coder.** The file names `factory.log` and `health.json` are literals in `build_boundaries`. `machine_log` and `health_store` share them, so there is one place each. No draft.
4. **S0003, coder.** The default token path of decision 18 is not in the settings (`token_file: Path | None = None`). It lives only in the image's `ENV FACTORY_TOKEN_FILE=/run/secrets/hosting-token`, and the operator guide says "No default". Listed under 6.
5. **S0004, coder.** `run.py` re-exports `build_tick` for a test's patch. Deliberate.
6. **S0007, coder and documenter.** The Dockerfile's `ENV` sets neither `FACTORY_OPT` nor `FACTORY_STATE`; the entrypoint's defaults cover both. No draft.
7. **S0008, S0013, S0014 and S0015, documenters.** Stale sentences: "seven items", the preflight "to come", "under your own `claude` login", and the `"make"` sentence of the project guide. "Seven items" and "next story" have since been repaired. The rest is in draft F0010-S0018, with the stale sentences I found myself (section 5).
8. **S0009 and S0010, coder and documenter.** When the machine items fail, a `main_branch_failing` stop already in force stays, even if `main` was fixed meanwhile. `docs/decisions.md` says "the tick story decides", and it did not. It clears at the next pass of the machine items, so it is stale for as long as the machine stop stands. Listed under 6.
9. **S0010, coder.** `Tick` and `build_preflight` each build their own `StopService`. Harmless: the service holds only the boundaries.
10. **S0011, coder.** `run_watch` returns 1 for both refusals, as its Interface says.
11. **S0012 and S0017, reviewers and documenter.** The template's coder and tester write paths hold no `{work_item}`, so the coder text's step "rewrite `## Description`" applies only where a project adds it. Also, a project from the template cannot have its coder write data files outside `src/`, as this feature's own S0012 coder did (`claude/`, `template/`). Listed under 6.
12. **S0012 and S0017, documenter.** `claude/settings.json` allows `git add` and `git commit`, against the agents' R10. Draft F0010-S0020.
13. **S0014, coder.** The `time_limit` under `sudo` (decision 30) is open and is a morning observation. Listed under 6.
14. **S0016, coder.** `tests/entry/test_wiring_preflight.py` fails at `tool:git` before it reaches the extras, so the extras are tested in `test_wiring_extras.py` instead. No gap: M16 was killed there.
15. **S0017, coder.** The shipped texts mention `make mutants` and `docs/openapi.json` "if the project has" them, as v1's do. This project has no `make mutants`.

Two more items I noticed myself:

- `ClaudeCodeRuntime` starts `sudo` at the fixed `SUDO_EXECUTABLE = "/usr/bin/sudo"`, while the preflight item `tool:sudo` looks for `sudo` on the `PATH`. In the image they are the same file. Elsewhere a mismatch shows only as a failed `agent-run-probe`, which goes through the real call, so nothing goes unseen.
- `factory-health` reads a missing health file as `healthy`. A container whose factory never wrote its state, as in the traceback of section 2, therefore reports healthy until Docker's restart policy acts on the exit. Combined with draft F0010-S0019, the stop would at least be on standard error. Whether a missing file should be unhealthy is the human's call; listed under 6.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md` and `docs/project-guide.md` from the top. The new sections agree with each other and with the code: settings, loop, image, users, token, health check, preflight items, stamp, probe, shipped agents. What is wrong are the sentences that earlier stories wrote about the future, plus one missing paragraph:

- **`README.md:12`.** "`factory-health` is declared in `pyproject.toml` but not built: it ends with a `ModuleNotFoundError` until F0010. Five commands exist so far." It is built (S0007) and prints `healthy` or the stops in force. This is a **contradiction with behaviour** and the reason for the verdict. The same line's "with an invalid environment it ends with status 2" holds only where `/state` can be written (section 2).
- **`docs/operator-guide.md:60`.** "The factory runs each agent as a `claude -p` call under your own `claude` login" contradicts `:92`, "The agent runs under `agent`'s own `claude` login, not yours".
- **`docs/operator-guide.md:195`.** "a second operating-system user that the image does not have yet": the image has `agent` (S0006, S0015).
- **`docs/operator-guide.md:279`.** "Nothing starts the factory yet": `factory-run` does (S0004).
- **`docs/project-guide.md:1377`.** "`compose` fills … `os_user=None` … (scrubbing is F0010's)". `TaskComposer._os_user` returns `boundaries.settings.agent_user`, and `production_environment()` scrubs. This is a **contradiction with behaviour** in the agents' own guide.
- **`docs/project-guide.md:215`.** "The string `"make"` appears in no other module under `src/factory`." `factory.application.preflight` holds it too (S0008, FEATURE decision 28 item 3).
- **`docs/project-guide.md:291, 726, 730, 990`.** "The flags are v1's, not yet checked against the pinned `claude`" (the `agent-run-probe` now runs them once for each image), "F0010 probes the `PATH` and completes `build_boundaries`", "nothing builds `FrontmatterWorkItemWriter` yet", and "Building the concrete adapters is `factory.entry.wiring`'s; it does not do so yet". All four are built.
- **Missing.** The project guide does not describe the runtime's call as another user: the `sudo -n -u <user> -- env -i` prefix, the `0640` run files, and the rule that turns a `sudo:` line into `AgentRuntimeError` when no reply came. S0014's docs criterion sent all of this to the operator guide and `docs/decisions.md`, so the agents' guide never got it.

Draft F0010-S0018 repairs all of these. No example in the docs failed when I ran it. I ran the settings table's variables through the demo and the `factory-health` and `factory-watch` commands as written.

## 6 Decisions taken for the human

`FEATURE.md` lists 36 decisions, and I found none of them contradicted by the code. Below, the ones to accept or revisit, with what the story logs added:

1. **Decisions 1 to 36 of `FEATURE.md`.** Accept as recorded. Decision 30 (`time_limit` under `sudo`) is still open, and neither repair is built. It needs the morning observation before a story can be written.
2. **Decision 18, the token file's default.** `/run/secrets/hosting-token` lives in the image's `ENV`, not in the settings, and outside the image an unset `FACTORY_TOKEN_FILE` is refused. Accept, or move the default into `InstanceSettings`.
3. **Decision 21, the agent home is writable by the agent.** In practice this means a run can rewrite `/home/agent/.claude/agents/*.md` and `settings.json`. The loader reads them on every tick, and the entrypoint replaces them only at start. So an agent can widen its own or another role's tools, budget or permissions for every later run until the container restarts. Revisit whether that waits for v2. One option: the loader reads `/opt/factory/claude`, or the files are `factory`-owned and `0644`.
4. **A standing `main_branch_failing` while the machine items fail** (section 4, item 8). The story that was to decide it did not. Accept that it stays until the machine passes, or ask for a clear.
5. **The template's write paths** (section 4, item 11). The coder has `src/*` only, and neither coder nor tester has `{work_item}`. Accept v1's lanes, or widen them in `template/factory/pipeline.yml`.
6. **The shipped `claude/settings.json` allows `git add` and `git commit`** while the texts forbid committing. Draft F0010-S0020 proposes denying them, which changes a test S0012's tester wrote. The draft asks for that permission by being promoted.
7. **A missing health file reads healthy** (section 4, last item). Accept, or make a missing file a stop.
8. **A timed-out run as `agent` with a harmless `sudo:` warning is an `AgentRuntimeError`, not the end reason `time_limit`.** This follows S0014's Interface and its fix of review finding 1. Draft F0010-S0022 pins it as it stands. Confirm that, or turn its first row around.
9. **Answers in the story logs, all already applied:**
   - S0003, entry 5: the probe-like request in `test_the_built_agent_runtime_keeps_its_run_files_under_runs` gets `allowed_decisions=["doing", "question"]`, and the domain rule stays.
   - S0004, entries 5, 8 and 10: the error count across ticks is shown with the agents installed and a run that raises inside the handler. The human replaced their own answer (b) by (a).
   - S0006, entry 7: five more floating-item rows in `test_a_floating_item_is_reported`.
   - S0013, entry 6: `token_file_item` is wired by S0016, which it was.
   - S0014, entry 7: a reply that comes with a `sudo:` warning on standard error is a reply, and a new criterion pins it.

## 7 The slow checks

None beyond `make check`. The project has no `make mutants`, no image scan and no SBOM target, so section 3 is a hand pass. The image build, a running container (`docker compose ps` healthy), the agent run as `agent` (WE3.1, WE3.3, WE3.4), the umask of agent-made files and the `time_limit` under `sudo` need Docker and a second user. They are the morning observations that `docs/operator-guide.md` lists with their commands, and they are not observed yet. The base image digest and the eight Debian versions are still placeholders (decision 6), so the first build also needs the human's pins.

## 8 Cost

135 runs, 405.4 minutes and $41.30 for 17 stories: about $2.43, 8 runs and 24 minutes each. The cheapest was S0002 ($1.14, 6 runs). The stories that stand out:

- **S0004, $3.97, 11 runs.** The human answered three times on one test (entries 5, 8 and 10), the last answer replacing the second.
- **S0014, $3.45, 43.5 minutes, 11 runs.** A review finding on the `sudo` refusal rule needed a new criterion from the human.
- **S0017, $3.37, 10 runs.** The longest texts, and a reviewer finding in test code.
- **S0003, $3.17, 11 runs.** A wrong test went to the human, then a duplicated helper went back to the coder.
- **S0006, 42.4 minutes.** Missing test rows needed the human's approval.

The common pattern: a review finding in test code costs a detour of four runs (coder → tester → coder → reviewer), seen in S0006, S0012, S0015 and S0017. No story's cost points to a fault of its own.

## Proposed stories

- `drafts/F0010-S0018-the-documentation-after-the-machine.md`: the README's `factory-health` and command count, the operator guide's login sentence and two "not yet" sentences, the project guide's `os_user=None`, the `"make"` sentence and four "not yet" sentences, and the missing paragraph on the runtime's call as another user. This repairs the finding that makes the verdict.
- `drafts/F0010-S0019-factory-run-without-a-writable-state-directory.md`: `factory-run` ends with status 2 and two lines on standard error, not a traceback, when the machine stop cannot be written.
- `drafts/F0010-S0020-no-git-commit-in-the-shipped-settings.md`: the shared settings deny `git add` and `git commit`, as the shipped texts say. Promoting it gives the permission to change S0012's `SETTINGS` test.
- `drafts/F0010-S0021-the-loop-survives-every-kind-of-error.md`: pins the scheduler's `except Exception` with `GitError`, `OSError`, `AgentRuntimeError` and `RuntimeError` rows. It kills the surviving mutant M10.
- `drafts/F0010-S0022-a-timed-out-run-as-the-agent-user.md`: pins the `sudo:` refusal for a call that reached its `time_limit`, which kills the surviving mutant M23. It also asks the human to confirm the rule.

## Log (append only)

1. acceptor: not accepted; 5 drafts proposed; make mutants 22/24 (hand pass: the project has no `make mutants` target)

   `make check` was green when I started and is green now. I replaced one commit id in the pasted demo output with a placeholder, because `make secrets` flagged it as a high-entropy string. I changed nothing under `src/`, `tests/` or `docs/`, and every mutant was reverted.

   The verdict is a recommendation. The code keeps every promise in FEATURE.md, but the README contradicts it: it says `factory-health` ends with a `ModuleNotFoundError` (it prints `healthy`), and that `factory-run` with a bad environment ends with status 2 (outside the image it ends with tracebacks and status 1). The role's rule makes that `not accepted`. If the human counts those sentences as low weight, `accepted with drafts` fits the same report.

   1. Scope: no finding. Every scope item has its stories and code, and out-of-scope items stayed out. One near-miss: `claude/settings.json` allows `git commit` although the shipped texts forbid it (S0020).
   2. Feature demo: green. The walk covered the settings from the environment, reclone, the preflight with its stamp and lint probe, runs as `agent` with no token, a red main, a dead agent key, a new image, a missing `sudo`, the health check and an invalid environment. The real `factory-run` outside the image tracebacks on `/state` (S0019).
   3. Mutation: 22 of 24 killed. Survivors: M10, the scheduler's `except Exception` narrowed to `ValueError` (S0021), and M23, the `sudo:` refusal on a timed-out run (S0022).
   4. Noticed by the stories: 15 items collected. Two copies of the default git identity (no draft); a `main_branch_failing` stop that stays while the machine items fail, left undecided; template write paths without `{work_item}`; stale docs (S0018); the `time_limit` under `sudo`, still open.
   5. Docs: the README's `factory-health` and command count; the operator guide's "your own login", "image does not have yet" and "Nothing starts the factory yet"; the project guide's `os_user=None`, "scrubbing is F0010's", the `"make"` sentence and four "not yet" sentences. The project guide also has no paragraph on the runtime's `sudo` call. All in S0018.
   6. Decisions: decisions 1 to 36 stand, and 30 is still open. To revisit: the token default lives only in the image; the agent can rewrite its own agent files and settings in its home (decision 21); the standing `main_branch_failing`; the template's write paths; `git commit` in the shipped settings; a missing health file reads as `healthy`; the timed-out `sudo` rule. Five log answers are listed.
   7. Slow checks: none beyond `make check`. The image build, the container and the second user are morning observations, and the base digest and Debian versions are still placeholders.
   8. Cost: 135 runs, 405.4 min, $41.30, about $2.43 per story. Highest are S0004 ($3.97: three human answers on one test) and S0014 ($3.45, 43.5 min). A review finding in test code costs four runs (S0006, S0012, S0015, S0017).
2. done (pull request merged); cost: 1 runs, 38.6 min, 87 turns, 189k tokens in (10138k more from cache), 60k out, $4.73
