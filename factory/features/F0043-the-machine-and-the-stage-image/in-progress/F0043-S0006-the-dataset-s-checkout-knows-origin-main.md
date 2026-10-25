---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-10-25T07:31:02.891950Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T07:31:02.886621Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T07:31:02.891950Z'
  stage: intake
---

# The dataset's checkout knows origin/main

## Description

The sync container (F0042's S0007) brings the dataset's checkout to the stage's commit by fetching every branch of the host's repository as a local branch (`git fetch -q --prune --update-head-ok "$3" '+refs/heads/*:refs/heads/*'` in `_SYNC_SCRIPT` of `factory.application.stage_environment`). The checkout so has `main` and the work item's branch, but no remote-tracking ref `origin/main`. The project's `make secrets` reads `origin/main` to limit itself to the files a branch changed; without it, it scans every tracked file. On the first stage on the VM (2026-10-25, F0043-S0004 on #434, the instance `vm`), the coder's `make check` stopped at `make secrets` on "Hex High Entropy String" findings in finished acceptance reports the branch never touched (`F0023-A0001`, `F0023-A0002`, `F0042-A0002`), and the coder reported `git diff origin/main` failing with "unknown revision". Every stage on a `container` instance would end the same way, the factory's own check after a stage included, since it runs `make check` in a check container on the same dataset. This story makes the sync also fetch the host's branches as the remote-tracking refs of `origin`, so the dataset's checkout knows `origin/main` (and `origin/<branch>` for every branch) at the host's commit, as a clone of the host's repository would; the `make secrets` of a branch then scans only its changed files, as on `self`. What stays: the local branches are fetched as today, `--prune` removes a branch gone from the host from both, the checkout and the reset to the stage's commit are unchanged, the script's text names no container path (every path comes as an argument), and nothing changes for an `inline` instance. Decision 18 of `feature.md`.

## Interface

`factory.application.stage_environment` (`application`): `_SYNC_SCRIPT`'s fetch line becomes one `git fetch -q --prune --update-head-ok "$3"` with two refspecs, `'+refs/heads/*:refs/heads/*'` and `'+refs/heads/*:refs/remotes/origin/*'`. The comment above the script says why the second one is there (the project's commands read `origin/main`). Nothing else in the script or the module changes.

Tests (the tester writes them): new rows in a new test module, for example `tests/application/test_container_sync_origin.py`, running `ContainerEnvironment.prepare` on `FakeSnapshots` and `FakeContainerRuns` over a real host repository, as `tests/application/test_container_environment.py` runs it. No earlier test changes.

## Acceptance criteria

1. After `prepare` at a work item's branch whose host repository has `main` and that branch, in the dataset's checkout `git rev-parse origin/main` equals the host's `main` commit and `git rev-parse origin/<branch>` equals the host's branch commit, and `git rev-parse main` equals the host's `main` commit as before (rows of one parametrized test).
2. A branch deleted on the host between two `prepare` calls is gone after the second from both `refs/heads/` and `refs/remotes/origin/` of the dataset's checkout (one test).
3. After `prepare`, `git merge-base HEAD origin/main` in the dataset's checkout succeeds and names the host's `main` commit when the branch was made from it (one test): the condition `make secrets` uses to scan only the changed files.
4. `_SYNC_SCRIPT` holds both refspecs on its one fetch line, and no container path (`/work`, `/upstream`) (one test).
5. `make check` stays green.
6. docs: `docs/project-guide/stage-environment.md`, the section on the sync container: one sentence that the sync also fetches the host's branches as `origin/<branch>`, because the project's commands (`make secrets`) read `origin/main`, and what happened on the first VM stage without it. `docs/decisions.md`: none. `README.md`: none.

## Smoke test

```bash
grep -c "'+refs/heads/\*:refs/remotes/origin/\*'" src/factory/application/stage_environment.py
```
Expect: `1`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as vm.
