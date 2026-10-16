# The documentation after the machine

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance of F0010 read `README.md` and `docs/` from the top and found sentences that each story's documenter left as "stale but not touched, outside this story", plus one that nobody owned. Three of them contradict what the code does today, and the first misleads a newcomer about the feature's own health check:

- `README.md` says `factory-health` "is declared in `pyproject.toml` but not built: it ends with a `ModuleNotFoundError` until F0010", and that "five commands exist so far". `uv run factory-health` prints `healthy` and exits 0, and the operator guide lists it.
- `docs/operator-guide.md` says the agent runs "under your own `claude` login" ("The agent runtime"). The same guide says, under "Log in once as `agent`", that the agent runs under `agent`'s own login once `FACTORY_AGENT_USER` is set, and the image sets it.
- `docs/project-guide.md` says `compose` fills `os_user=None` and that "scrubbing is F0010's". `TaskComposer` names `boundaries.settings.agent_user`, and `production_environment()` scrubs.

The others are announcements of work that is now done. The operator guide says the second user is one "that the image does not have yet", and "Nothing starts the factory yet". The project guide says the runtime's flags are "not yet checked against the pinned `claude`", "F0010 probes the `PATH` and completes `build_boundaries`", "nothing builds `FrontmatterWorkItemWriter` yet", `Boundaries` wiring "does not do so yet", and that the string `"make"` "appears in no other module under `src/factory`". That last one is no longer true: `factory.application.preflight` holds it too, and `tests/test_make_search.py` allows it.

The project guide has no description of the runtime's call as another operating-system user. That is the `sudo -n -u <user> -- env -i` prefix, the run files written with mode `0640`, and the rule that turns a `sudo:` line into `AgentRuntimeError`. The operator guide and `docs/decisions.md` hold this, but the agents' guide does not.

This story is documentation only: the documenter rewrites these sentences to say what is built. No code or test changes. The behaviour of `factory-run` when the state directory cannot be written is a separate draft (F0010-S0019). Until that draft lands, the README sentence about status 2 holds inside the image only.

## Interface

No code. The files that change are `README.md`, `docs/operator-guide.md` and `docs/project-guide.md`. Each sentence named in the Assignment is rewritten or removed. The project guide's section on the agent runtime (`ClaudeCodeRuntime`) gains one paragraph on `request.os_user`:

- the call is prefixed by `<sudo_executable> -n -u <os_user> -- env -i NAME=value ...`;
- the instructions, the guard settings and the hook settings are written with `RUN_FILE_MODE` (`0o640`);
- when the process ends without a result, a standard-error line starting with `sudo:` raises `AgentRuntimeError`;
- a reply that comes with a `sudo:` warning is a reply.

The paragraph also says that `TaskComposer` takes the user from `boundaries.settings.agent_user`, and that `agent_run_environment` sets `HOME` to the parent of `agent_home`.

## Acceptance criteria

1. `README.md` names `factory-health` among the built commands, says what it prints (`healthy`, or one line per stop in force) and how it exits (0 or 1), and no longer mentions a `ModuleNotFoundError`. The count of commands matches the commands it lists.
2. `docs/operator-guide.md`, "The agent runtime", says that with `FACTORY_AGENT_USER` set (as the image sets it) the call runs under that user's `claude` login, and under the factory user's own login only without it.
3. `docs/operator-guide.md` no longer says that the image has no second user, or that nothing starts the factory.
4. `docs/project-guide.md`, "The request", says that `os_user` is `boundaries.settings.agent_user`, or `None` without settings, and that the environment is scrubbed at its source, `production_environment()`.
5. `docs/project-guide.md` no longer announces as future work any of the five things named in the Assignment (the flag check, the `PATH` probe, the work item writer, the wiring of `Boundaries`, `"make"` in one module). Each is described as built, or the sentence is removed.
6. `docs/project-guide.md` describes the runtime's call as another user, as the Interface lists it.
7. `make check` stays green.
8. docs: this story is the documentation. The documenter reads the README and both guides from the top afterwards, and names in the log any other sentence that announces F0010 work as still to come.

## Demo

```bash
grep -n -E 'ModuleNotFoundError|until F0010|does not have yet|Nothing starts the factory yet|scrubbing is F0010|not yet checked against|nothing builds .FrontmatterWorkItemWriter. yet|does not do so yet' README.md docs/operator-guide.md docs/project-guide.md; echo "exit=$?"
```
Expect: no matching line, then `exit=1`.

```bash
uv run factory-health --state-directory "$(mktemp -d)"; echo "exit=$?"
```
Expect: `healthy`, then `exit=0`, as the README now says.

```bash
grep -n -c 'sudo' docs/project-guide.md
```
Expect: a number of at least 2 (the new paragraph names the `sudo` prefix and the `sudo:` refusal).

## Log (append only)

1. 2026-10-16 human: created.
