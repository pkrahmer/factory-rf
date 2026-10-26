# The project guide and the decision log agree with the feature's constructors and its login rule

<!-- proposed by feature acceptance of 2026-10-26; refine before starting -->

## Description

Each story of F0046 kept its own passages true, and four places outside them are still stale. They are documents for agents and for the human, and no story could see them from inside its own diff. First, `docs/project-guide/agents.md` gives the constructors of `ClaudeCodeRuntime` and `OpencodeRuntime` without the keywords `extra_environment` and `ca_bundle` that S0002 added. The same file's container paragraph already describes both keywords. Second, the wiring table in `docs/project-guide/stage-environment.md` builds `ContainerMakeCommands(snapshots, containers, git, checkout=settings.checkout)` without those keywords. Nothing in the project guide says that `build_boundaries` computes the extras once and carries them on `Boundaries.container_extra_environment`, where `stage_environment_of` reads them. Third, the decision entry *The agent runtime is chosen per instance* (F0020) still says the preflight asks for no API key because a build may log in through single sign-on, and that `FACTORY_OPENCODE_FOLDERS` lets a build keep its login in the agent's home. *A company's provider for opencode* (S0001) says that only the API login works on the machine, and `src/factory` no longer reads `FACTORY_OPENCODE_FOLDERS`. The old entry carries no `Superseded in part` bullet, unlike the log's other superseded entries. Fourth, S0004's documenter wrote that the completed probe's `none` detail appears "when no login file is set". It appears when a login file is named but holds no login. With no login file set at all, the login shell is not started and the detail is empty. Also, *Behind a proxy* lacks a comma, noted by S0005's smoke tester. This story changes these documents only. The behaviour stays as it is, and so do the other sections. Whether a probe with no login file at all should say more than an empty detail is a product question, and this story leaves it to the human.

## Interface

None: nothing changes under `src/factory/`, in any test, or under `vm/`, `template/` or `claude/`. The documenter changes `docs/project-guide/agents.md`, `docs/project-guide/stage-environment.md`, `docs/decisions.md` and `docs/operator-guide.md` only. No test reads the documents. The smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/` changes, and the tester and the coder each end with an entry that says so.
2. `make check` stays green.
3. docs: the smoke test and `make documents` check these, and no test does:
   - `docs/project-guide/agents.md`: the signature of `ClaudeCodeRuntime` ends `containers=None, extra_environment={}, ca_bundle=None)`. The signature of `OpencodeRuntime` ends `containers=None, extra_environment={}, ca_bundle=None, provider_file=None)`. Both are as in `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py`.
   - `docs/project-guide/stage-environment.md`, the wiring table: `ContainerMakeCommands(snapshots, containers, git, checkout=settings.checkout, extra_environment=extra, ca_bundle=settings.ca_bundle)`. One sentence below the table says three things. `build_boundaries` computes `extra = extra_environment(settings, os.environ)` once. It hands the same mapping to the agent runtime, to `ContainerMakeCommands` and to `Boundaries.container_extra_environment`. `stage_environment_of` builds the sync's `ContainerEnvironment` from that field and from `settings.ca_bundle`.
   - `docs/decisions.md`, *The agent runtime is chosen per instance*: one bullet `- Superseded in part by "A company's provider for opencode": ...` after its last bullet, in the form of the log's other superseded entries. It says that a login kept in the agent's home does not survive the rollback to the base, that only the API login works on the machine, and that `FACTORY_OPENCODE_FOLDERS` is no longer read. The entry's other bullets stay as written.
   - `docs/operator-guide.md`, *The probe of the agent run*: the completed probe's two `none` texts are named for the case where a login file is named but holds no login (missing or blank), not "when no login file is set". One sentence adds that with no login file set at all the detail is empty.
   - `docs/operator-guide.md`, *Behind a proxy*: a comma before `and list their names`.
   - No other section of the four documents changes, and `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -F 'extra_environment={}, ca_bundle=None' docs/project-guide/agents.md
```
Expect: `2`

```bash
grep -c -F 'ca_bundle=settings.ca_bundle' docs/project-guide/stage-environment.md
```
Expect: a number of at least `1`

```bash
awk '/^## The agent runtime is chosen per instance$/{on=1; next} /^## /{on=0} on' docs/decisions.md | grep -c 'Superseded in part by "A company.s provider for opencode"'
```
Expect: `1`

```bash
grep -c 'when no login file is set' docs/operator-guide.md
```
Expect: `0`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
