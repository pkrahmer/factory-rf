---
stage: tests
pr: 141
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The documentation after the machine

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance of F0010 read `README.md` and `docs/` from the top and found sentences that each story's documenter left as "stale but not touched, outside this story", plus one that nobody owned. Three of them contradict what the code does today, and the first misleads a newcomer about the feature's own health check:

- `README.md` says `factory-health` "is declared in `pyproject.toml` but not built: it ends with a `ModuleNotFoundError` until F0010", and that "five commands exist so far". `uv run factory-health` prints `healthy` and exits 0, and the operator guide lists it.
- `docs/operator-guide.md` says the agent runs "under your own `claude` login" ("The agent runtime"). The same guide says, under "Log in once as `agent`", that the agent runs under `agent`'s own login once `FACTORY_AGENT_USER` is set, and the image sets it.
- `docs/project-guide.md` says `compose` fills `os_user=None` and that "scrubbing is F0010's". `TaskComposer` names `boundaries.settings.agent_user`, and `production_environment()` scrubs.

The others are announcements of work that is now done. The operator guide says the second user is one "that the image does not have yet", and "Nothing starts the factory yet". The project guide says the runtime's flags are "not yet checked against the pinned `claude`", "F0010 probes the `PATH` and completes `build_boundaries`", "nothing builds `FrontmatterWorkItemWriter` yet", `Boundaries` wiring "does not do so yet", the cost record's "`image` stays `None` until F0010", the PyGithub wiring comes "(F0002 onward, token in F0010)", and that the string `"make"` "appears in no other module under `src/factory`". That last one is no longer true: `factory.application.preflight` holds it too, and `tests/test_make_search.py` allows it. In "The `claude -p` runtime" the project guide also gives `ClaudeCodeRuntime`'s signature without `sudo_executable=SUDO_EXECUTABLE`, says the call runs "under the operator's own login", and ends its environment paragraph with "`request.os_user` is not used yet"; and its "Boundaries" paragraph lists the fields of `Boundaries` without `settings`.

The operator guide's paragraph on a `sudo` that refuses says "when the call ends without a usable reply"; since F0010-S0022, a call that reached its time limit also counts as one without a usable reply, even when it printed a reply first, and the guide does not say so.

The project guide has no description of the runtime's call as another operating-system user. That is the `sudo -n -u <user> -- env -i` prefix, the run files written with mode `0640`, and the rule that turns a `sudo:` line into `AgentRuntimeError`. The operator guide and `docs/decisions.md` hold this, but the agents' guide does not.

This story is documentation only: the tester writes no tests and the coder has nothing to build; the documenter writes it from the docs criterion and rewrites these sentences to say what is built. F0010-S0019 is merged before this story starts, so the README's sentence on status 2 is written as S0019 left it, without a condition on the image.

## Interface

No code. The files that change are `README.md`, `docs/operator-guide.md` and `docs/project-guide.md`. Each sentence named in the Assignment is rewritten or removed. The project guide's section "The `claude -p` runtime" gains one paragraph on `request.os_user`, in place of "`request.os_user` is not used yet":

- with `os_user` set, the call is `<sudo_executable> -n -u <os_user> -- env -i NAME=value ... <executable> <arguments>`, started with an empty environment of its own; `sudo_executable` defaults to `SUDO_EXECUTABLE` (`/usr/bin/sudo`);
- the instructions, the guard settings and the hook settings are written with `RUN_FILE_MODE` (`0o640`), for every request;
- when a call as `os_user` reached its `time_limit`, or printed no reply that parses, a standard-error line starting with `sudo:` raises `AgentRuntimeError`, whose detail holds the line;
- a reply that parses, from a call within its `time_limit`, is a reply even when a `sudo:` warning came with it.

The paragraph also says that `TaskComposer` takes the user from `boundaries.settings.agent_user`, and that `agent_run_environment` sets `HOME` to the parent of `agent_home` when `settings.agent_user` is set.

## Acceptance criteria

1. `make check` stays green.
2. docs: this story is the documentation; `README.md`, `docs/operator-guide.md` and `docs/project-guide.md` change. Afterwards:
   - `README.md` names `factory-health` among the built commands, says what it prints (`healthy`, or one line per stop in force) and how it exits (0 or 1), and no longer mentions a `ModuleNotFoundError`. The count of commands matches the commands it lists.
   - `docs/operator-guide.md`, "The agent runtime", says that with `FACTORY_AGENT_USER` set (as the image sets it) the call runs under that user's `claude` login, and under the factory user's own login only without it.
   - `docs/operator-guide.md` no longer says that the image has no second user, or that nothing starts the factory.
   - `docs/operator-guide.md`, the paragraph on a `sudo` that refuses, says that a call that reached its time limit counts as ending without a usable reply, so a `sudo:` line then stops the run with the error that holds it.
   - `docs/project-guide.md`, "The request", says that `os_user` is `boundaries.settings.agent_user`, or `None` without settings, and that the environment is scrubbed at its source, `production_environment()`.
   - `docs/project-guide.md` no longer announces as future work any of the things the Assignment names: the flag check, the `PATH` probe, the work item writer, the wiring of `Boundaries`, the cost record's `image`, the token of the PyGithub wiring, `"make"` in one module, and `request.os_user`. Each is described as built, or the sentence is removed. The `ClaudeCodeRuntime` signature names `sudo_executable`, and the field list of `Boundaries` names `settings`.
   - `docs/project-guide.md`, "The `claude -p` runtime", describes the call as another user as the Interface lists it.
   - The documenter reads the README and both guides from the top afterwards, rewrites any other sentence that announces F0010 work as still to come, and names each in its entry.

## Demo

```bash
grep -n -E 'ModuleNotFoundError|until F0010|does not have yet|Nothing starts the factory yet|scrubbing is F0010|not yet checked against|nothing builds .FrontmatterWorkItemWriter. yet|does not do so yet|os_user. is not used yet|token in F0010|F0010 probes' README.md docs/operator-guide.md docs/project-guide.md; echo "exit=$?"
```
Expect: no matching line, then `exit=1`.

```bash
uv run factory-health --state-directory "$(mktemp -d)"; echo "exit=$?"
```
Expect: `healthy`, then `exit=0`, as the README now says.

```bash
grep -c -F 'env -i' docs/project-guide.md; grep -c -E 'RUN_FILE_MODE|0o?640' docs/project-guide.md
```
Expect: two numbers, each at least 1 (both were 0 before this story).

## Log (append only)

1. 2026-10-16 human: created.
2. intake: accepted
   - Interface: no code. The story names the three files that change (`README.md`, `docs/operator-guide.md`, `docs/project-guide.md`) and lists the content of the new `os_user` paragraph. Each behaviour in that paragraph (the `sudo -n -u … -- env -i` prefix, the `0o640` mode, the `sudo:` line rule and its exception) is existing code behaviour, and the docs criterion lists them, so nothing is left undefined.
   - Criteria: there are only the two closing ones. The story says it is documentation only, so the tester writes no tests and the coder has nothing to build. The docs criterion lists each rewrite as an observable statement about a file, which the documenter checks with the Demo greps. No rule has a failing side without a criterion, because the story adds no rule.
   - Demo: all three commands are runnable. Each `Expect:` line is checkable against the output: no matching line with `exit=1`, `healthy` with `exit=0`, and two counts of at least 1.
   - Architecture: no layer or module is touched. The project guide paragraph is consistent with `CLAUDE.md`'s wrapper and runtime rules.
   - Scope: the story fits F0010, appears in `FEATURE.md` as S0018, and touches nothing under "Out of scope". It depends on S0019 being merged, which the Assignment states.
