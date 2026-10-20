# The documents say what the factory's kill of make mutants leaves

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0030's `feature.md` (*The human's changes*, point 1, and *Out of scope*) says that the `mutants` recipe's temporary folder stays after the factory's kill, and that this sentence is in S0001's docs criterion. It is not there, and the project guide does not say it. *The temporary folder* in `docs/project-guide/processes-and-checks.md` says the recipe's `EXIT` trap removes the folder "also after a stop and after a failed run", and is silent on a kill. F0030's acceptance ran the recipe's form through `MakeProjectCommands.run` with a time limit: every process of the session was gone, and the folder that `mktemp -d` made stayed, because SIGKILL runs no trap. Also, the decision log's entry *Mutation testing per story* still says in its decision (4) that the factory's kill "does not reach mutmut". That entry is superseded for other reasons, and F0030's own entry says that it corrects decision 4, but the old line points nowhere, unlike the entry of 2026-10-18, which S0001 gave a line naming the new entry. The human's real check with mutmut (F0030's change 2, 2026-10-20) answered the feature's decision 14. `make mutants`, killed by the factory at 50 s during mutmut's stats run, lost all of `make`'s session. But a fake `claude` that `tests/adapters/test_claude_runtime.py::test_call_over_its_time_limit_is_killed_with_unknown_measures` started outlived the kill for up to its 60 s, in a session of its own: the runtime under test starts its command line through `run_process`, which uses `start_new_session`. This story writes these facts. No code, test, `Makefile` or `README.md` changes.

## Interface

None: documents only (`docs/project-guide/processes-and-checks.md`, `docs/decisions.md`). No module under `src/factory/` and no test changes.

## Acceptance criteria

1. Nothing under `src/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/project-guide/processes-and-checks.md`, *Mutation testing*, the paragraph *The temporary folder*: a run that the factory kills at its time limit (`MakeProjectCommands.run`, *Killing a session*) ends with SIGKILL, which runs no `EXIT` trap. mutmut and every process still in `make`'s session are gone, but the temporary folder stays, with the words `the temporary folder stays`; it is under the `TMPDIR` of the caller of `make`, and the operator removes it by hand. A process that one of mutmut's tests started through `factory.adapters.process` is not in that session: the code under test starts every command in a session of its own (`start_new_session`), so the kill does not reach it, and it runs on until it ends by itself, with the words `runs on until it ends by itself`. The paragraph names the case seen on 2026-10-20: `make mutants` killed by the factory at 50 s, during mutmut's stats run, left the fake `claude` of `tests/adapters/test_claude_runtime.py::test_call_over_its_time_limit_is_killed_with_unknown_measures` running for up to its 60 s. A stop by `MUTANTS_SECONDS` still runs the trap. `docs/decisions.md`: in the entry *Mutation testing per story*, decision (4) gains, right after "does not reach mutmut", `(since F0030-S0001 the factory's kill reaches mutmut; see *A command stopped at its time limit loses every process of its session*)`. In the entry *A command stopped at its time limit loses every process of its session*, the Decision bullet gains, after its sentence on `setsid`, one sentence: a test that mutmut runs can start such a process, because `factory.adapters.process` starts every command with `start_new_session`, and that process ends by itself (seen on 2026-10-20 in the real check with mutmut, which answers F0030's decision 14). `README.md`: none, nothing a newcomer does changes.

## Smoke test

```bash
grep -c "the temporary folder stays" docs/project-guide/processes-and-checks.md
```
Expect: `1`

```bash
grep -c "since F0030-S0001 the factory's kill reaches mutmut" docs/decisions.md
```
Expect: `1`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
