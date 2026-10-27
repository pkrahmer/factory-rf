# The project guide names every module that starts a process

<!-- proposed by feature acceptance of 2026-10-27; refine before starting -->

## Description

`docs/project-guide/processes-and-checks.md`, *Starting a process*, opens with "The git wrapper, the make class and the `claude -p` runtime each reach their tool through `run_process(request) -> ProcessResult`; no other module calls a command-line tool." That was true before F0042. Since then the opencode runtime (through `run_streaming`), `PodmanRuns`, `ZfsSnapshots`, `SystemctlPowerOff` (F0045-S0008) and the fake container runs used by the tests also start their programs through `factory.adapters.process`. Since F0045-S0013, three of them do so through `run_or_raise`. `tests/test_wrapper_search.py` pins the true list of eight modules. An agent who reads the guide's first sentence before touching a wrapper learns a list that is three modules long, and the paragraph on `run_or_raise` four paragraphs further down contradicts it. S0013's documenter noticed the sentence and left it as unrelated (journal entry 21). F0045-S0014's smoke tester noticed a missing comma in the line on `vm_support.py` of `docs/project-guide/README.md`, *Shared test helpers*, between "(`run_setup`)" and "`entries`" (journal entry 27). This story repairs both passages and nothing else. No code, test, decision or operator-visible text changes. The name of `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`, which checks eight modules, is the same stale count. Renaming it needs the human's leave, so it is left to the human when this story is refined.

## Interface

None under `src/factory/`, `vm/`, `template/` or `claude/`, and no test changes: documents only.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/project-guide/processes-and-checks.md`, `## Starting a process`, first paragraph: it names the modules that import `factory.adapters.process`, as `tests/test_wrapper_search.py` lists them. These are `git_cli`, `make_commands`, `claude_runtime` and `opencode_runtime`, `podman_runs`, `zfs_snapshots`, `power_off`, and `fake_containers` for the tests. For each it says whether the module reaches `run_process`, `run_streaming` or `run_or_raise`. It keeps "no other module calls a command-line tool". `docs/project-guide/README.md`, *Shared test helpers*: the `vm_support.py` line gets a comma after "(`run_setup`)". `README.md`, `docs/operator-guide.md`, `docs/decisions.md`: none, because nothing an operator sees changes and nothing new is decided.

## Smoke test

```bash
grep -c 'The git wrapper, the make class and the `claude -p` runtime each reach their tool' docs/project-guide/processes-and-checks.md
for m in git_cli make_commands claude_runtime opencode_runtime podman_runs zfs_snapshots power_off fake_containers; do sed -n '/^## Starting a process/,/^`ProcessRequest`/p' docs/project-guide/processes-and-checks.md | grep -c "$m"; done | sort -u
grep -c '(`run_setup`), `entries`' docs/project-guide/README.md
```
Expect: three lines: `0`; `1` (every one of the eight module names is found in the first paragraph of *Starting a process*, so the only count is 1); `1`

## Journal
