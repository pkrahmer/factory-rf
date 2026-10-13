# Decisions

The log of lasting decisions: what was decided, why, and what was rejected. Newest last. The first entries are the seed's choices (2026-10-12); the stories' decisions follow.

## The package is `factory`, in four layers

The code is one package, `src/factory/`, with the layers `factory.domain`, `factory.application`, `factory.adapters` and `factory.entry`. A higher layer may import a lower one (import-linter, `make layers`, part of `make check`). The project is named `factory-rf`; the package carries the factory's own name.

## Three top-level paths for the product beyond `src/` and `tests/`

`image/` (Dockerfile, compose file, entrypoint), `template/` (v1.1's own project template) and `claude/` (the agent and skill files v1.1 ships). The coder's write paths in `factory/stages.yml` name them; the folders are created by the stories that need them. `Makefile`, `pyproject.toml`, `uv.lock`, the import-linter configuration, `CLAUDE.md` and `factory/` stay outside every write path.

## No `mutants` target, no mutmut

The acceptance reviewer runs `make mutants` only when it exists. Over the whole package it could outgrow the 60-minute lease in later features, and a timeout is a stall. So the seed has neither the target nor the dependency.

## The licence allow list has one LGPL entry and one dual-licence entry

PyGithub is LGPL-3.0, and `pip-licenses` reports it as `GNU Library or Lesser General Public License (LGPL)`, which is now on the allow list. `cryptography` (a transitive runtime dependency, through PyGithub) is reported as `Apache-2.0 OR BSD-3-Clause`, which is also allowed. The template's list is otherwise unchanged.

## The project guide lives in `docs/`

`docs/project-guide.md` is the guide for agents (R17). It is in `docs/` and not in `CLAUDE.md` so that the documenter, whose write paths are `README.md` and `docs/*`, can keep it true; `CLAUDE.md` stays the human's, and points to the guide.

## The one module that starts processes may carry four markers

Date: 2026-10-13. Every command-line tool is reached through one wrapper class (R5), and the wrappers share one function that starts a process, in `src/factory/adapters/process.py`. ruff's S404 and S603 and bandit's B404 and B603 flag any `subprocess` use, and `CLAUDE.md` puts `nosec` markers under "Not without asking". So exactly that module may carry those four markers, on its import and its one `Popen` call. Alternatives rejected: a per-file ignore in `pyproject.toml` (bandit has none, and it would hide the exception from the reader of the code); lowering bandit's severity (loosens the whole package). There are no other markers anywhere under `src/factory`: a second one would be a second place that quietly weakens the checks. `tests/test_process_search.py` fails on any marker (`noqa`, `nosec`, `nosemgrep`, `pragma: allowlist secret`) other than these four on those two lines, and on any other route to a process, so the exception cannot grow unnoticed.

## `InjectedKill` is a `BaseException`

Date: 2026-10-12. An armed kill point stands in for the factory dying at that moment (WE6.3). A real death runs no handler, so the injected one must not be caught by any either. If `InjectedKill` were an `Exception`, an `except Exception` in a wrapper or a stage would swallow it and the test would show recovery from an error, not from a crash. As a `BaseException` it passes every `except Exception`; only a test's `pytest.raises(InjectedKill)` or a bare `except BaseException` sees it. It is also not a `FactoryError`, which is an `Exception`. Alternatives rejected: an `Exception` subclass (swallowed by the handlers the test is meant to bypass); `os._exit` or a signal (kills the test process and cannot be asserted on).

## A post carries a key, and the marker tells the factory's posts apart

Date: 2026-10-12. Every post the factory makes ends with the marker `<!-- factory -->` and a key comment `<!-- factory key=<work item>:<kind>:<n> -->`. The key makes a post idempotent: a factory that died between posting and recording it (WE6.3) can look at the comments, find the key and not post twice. The marker, not the author, says a comment is the factory's (R34): the factory posts under the operator's own login, so the author is also the human's, and a human's comment must never be taken for the factory's or the other way round. The key is read only from the last non-blank line, so a key quoted in a sentence or followed by more text is not a key. Alternatives rejected: telling posts apart by author (the login is shared); a key anywhere in the body (a quoted key would suppress a real post); a key without a work item (the same kind and number of two work items would collide).

## PyGithub behind the interface, with one error type; not `gh`, a git library or plain httpx

Date: 2026-10-12. The hosting service is reached through one client on PyGithub (R9), and every failing call, whether GitHub answers with an error or cannot be reached, surfaces as `HostingServiceError`. Callers handle one type and never learn PyGithub's or the network's. A search test keeps it so: only the client imports `github`, no other route to the API is imported, and no module names the `gh` tool. Why not the others: `gh` is a second program whose output has to be parsed and whose login is outside our control; GitPython-style wrappers (GitPython, pygit2, dulwich) wrap git, not the hosting service, and git has its own wrapper; githubkit and plain httpx would mean writing and maintaining the request and response handling that PyGithub already has. The client is tested against stand-ins of PyGithub's objects, with no network (WE6.3).

## Global and system git configuration are ignored

Date: 2026-10-13. Every git command of the wrapper runs with `GIT_CONFIG_NOSYSTEM=1` and `GIT_CONFIG_GLOBAL` set to the null device, after the process environment and the options' extra environment, so that nothing can lift them. Git then behaves the same on every machine and in every test: an operator's `insteadOf` rewrite, credential helper, hooks path or default branch cannot change what the factory does, and a crash test (WE6.3) replays the same git. Credentials are not lost: they come from the factory process's environment (`GIT_ASKPASS`, or `GIT_CONFIG_COUNT` with `GIT_CONFIG_KEY_<n>` and `GIT_CONFIG_VALUE_<n>`) and the options' `environment`, which is how the factory's own pushes get the token while the agent run never does. The token is never put in a URL, because git may print one. Alternatives rejected: trusting the user's configuration (the result depends on the machine); a private `HOME` (still reads a file the operator did not write, and breaks other tools that read `HOME`); credentials in the remote URL (printed in errors and logs).
