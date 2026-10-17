---
stage: accept
pr: 187
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0013-S0001, F0013-S0002, F0013-S0003, F0013-S0004, F0013-S0005]
---
# Acceptance of Podman and the token

## Verdict

**accepted with drafts.** Every scope item has a merged story. The feature demo is green: the image, the compose file, the factory's token reading, the preflight item and git's credential helper agree on the token's folder, and a user who cannot enter the folder gets no credential even from a `0777` file. The two findings worth a story are not broken promises. One is a set of preflight details that the tests check only in part. The other is four older sentences, in the README and the operator guide, that still say no container was observed, which contradicts the new *Container runtimes* section.

## 1 Scope

None. Every Scope bullet of `FEATURE.md` has its story, and nothing was built outside it:
- The token's folder, the bind mount and the path: S0001 (`image/Dockerfile:20-26,41`, `image/compose.yml:22-30`).
- The preflight item on the folder: S0002 (`src/factory/application/preflight.py:82-124`).
- F0012's two drafts: S0003, a new test module only, and S0004 (`src/factory/entry/check_demos.py:14,24,71`).
- Podman's restart, the provider, the runtimes and the disk: S0005, documents only.
- The stale header comment of `image/entrypoint.sh`: S0001, whose lines 4-5 now name `/work`.

The Goal's "done when" holds: `make check` is green (below); the folder and the mount are in the image and the compose file; the preflight checks the folder; and the operator guide has *Container runtimes*, which names the runtimes and says how to run under Podman.

The Out of scope items stayed out: the image pins (the human pinned them in `b642dd31`, outside the stories), the hand tests at the first start, `keep-id`, `:z`, `podman-compose`, and the project commands' route to the token.

`make check` as found: `check: green`, coverage 99.50 %.

## 2 Feature demo

No container runtime is on this machine (`which docker podman sudo` finds none, and there is no `agent` user), so the demo runs the real entry points without a container:
- the image files as Compose and the build read them;
- `boundaries_from_environment` and `machine_extras` of `factory.entry.wiring`, which the factory's start and its preflight use;
- `image/git-credential-factory` as git calls it.

The token's folder is a stand-in in a temporary directory. A folder without its search bit stands in for what the agent meets in a `0700` folder it does not own. The script is `/tmp/f0013-demo/demo.py`, outside the repository.

```
$ uv run python /tmp/f0013-demo/demo.py; echo "exit $?"
== 1. the image and the compose file
ENV FACTORY_TOKEN_FILE      = /home/factory/.secrets/hosting-token
bind mount target           = /home/factory/.secrets/hosting-token read_only True create_host_path False
target == ENV               = True
folder made, owned, 0700    = True True True
compose secrets left        = False False
uids factory/agent          = 1000 1001
== 2. the factory starts, reads the token and runs the preflight item
settings.token_file         = <tmp>/.secrets/hosting-token
preflight item, file 0777   = token-file True 
preflight item, folder 0755 = token-file False <tmp>/.secrets/hosting-token: the folder <tmp>/.secrets has mode 0755; make it 0700
== 3. git's credential helper: the user who may enter the folder, then one who may not
folder 0700, may enter      : exit 0 username=x-access-token | password=example-value | 
folder no x, file 0777      : exit 1 ''
exit 0
```

Green. The purpose holds end to end, as far as it can be shown without a container:
- the mount's target is the path the image sets;
- the factory reads the token through it;
- the preflight passes a file with the host's `0777` mode and refuses a folder others can enter;
- whoever cannot enter the folder gets nothing from the helper.

What the demo cannot show is the folder's owner and mode inside a running container under each runtime. That stays the morning observation of the operator guide, as `FEATURE.md` puts it out of scope.

Also run: `make documents` printed `documents ok`; `make duplicates` printed `duplicates: 0 new, 39 known, 0 gone`; `uv run python -m factory.entry.check_demos` printed `demos ok`.

## 3 Mutation score

`make mutants FEATURE=F0013` selected two modules, `src/factory/application/preflight.py` and `src/factory/entry/check_demos.py`, and finished in 27 s, a fresh run. mutmut's results do not print the killed mutants, so the counts come from mutmut's `.meta` files (`exit_code_by_key`):
- `preflight`: 379 killed of 394, 15 survived.
- `check_demos`: 170 killed of 173, 3 survived.
- Together: **549 killed of 567 (96.8 %), 18 survived, no timeouts.**

Every mutant of `token_file_item`, `_token_file_fault` and `_token_folder_fault`, the code S0002 rewrote, is killed. So is every mutant of `_story_findings`, which S0004 changed. All 18 survivors are in code this feature did not change. Read with `mutmut show`, they fall into these groups:
- **Preflight details checked only in part** (11): `"; ".join(faults)` becomes `"XX; XX"` in `agent_environment_item`. The texts of `_path_fault` and `_home_fault` are upper-cased or wrapped in `XX`. `agent_user or 'the factory user'` becomes `and`, and the fallback text changes, in `agent_run_probe_item`. The hints `check the token and the network` and `rebuild the image or change the pinned version` change. The tests assert parts of these details with `in`. The operator reads the details in the stop, and the operator guide quotes them. Draft S0006.
- **Arguments the fakes do not see** (3): `find_open_pull_request(None)` in `MachineChecks._hosting_service`, because the fake answers any branch and the item ignores the answer. `git.checkout(MAIN_BRANCH, start_point=None)` and the dropped `start_point` in `Preflight._run_probe`, because the `reset_to(_MAIN_REF)` that follows puts the checkout at `origin/main` anyway. These are near-equivalent, so there is no draft.
- **Equivalent or cosmetic** (3, in `check_demos`): `read_text(encoding="UTF-8")` and `encoding=None`, which are equal under a UTF-8 locale, and `ArgumentParser(prog=None)`. No draft.

F0012's acceptance counted 19 preflight survivors in a partial run. This run counts 15, and none is new.

## 4 What the stories noticed

- **S0001**:
  - The coder found that detect-secrets flags a criterion's own text: the YAML of the bind mount in criterion 3. The criterion was then reworded as prose. The coder's log entry quoted the flagged fragment, so it was flagged again, and the human added a `.secrets.baseline` entry for both the `ongoing/` and `done/` paths (log entries 4-8). This cost two extra runs (section 8). A story text that quotes a compose mount of a file named `*secret*` will meet the hook again. That is for the human's lessons, not a story.
  - The documenter saw that the `agent-user` text still says the factory's user "can read the token file". That is still true.
- **S0002**: the coder renamed a constant to `_MISSING_FILE_FAULT` because ruff's S105 flagged `_NO_TOKEN_FILE`. That is fine.
- **S0003**: the coder noted that `AcceptanceMerged._book` runs `git mv` in the checkout before the state check. The Interface left that out, and the tick's restore at the next tick undoes it. Nothing to do.
- **S0004**: nothing.
- **S0005**: the documenter left two things to the first Podman run. *The disk record* still speaks of "Docker's disk image" and `docker system df`. *What the container cannot see* gives only Docker Desktop's way to reclaim space (`fstrim`, `diskpart`). Neither is wrong for Docker, and Podman's way was not probed. No draft until a Podman run shows it.

The acceptance noticed three more things:
- `image/compose.yml:1` still says "Docker restarts it", which is untrue under Podman after a machine restart. This is a one-word comment fix for the next story that touches `image/`.
- `docs/decisions.md:255` still lists the default path `/run/secrets/hosting-token` as "Open". The F0013-S0001 entry (`:411`) supersedes it by name, so it is not a contradiction.
- F0012's two drafts that S0003 and S0004 took in are still under `factory/features/F0012-housekeeping/drafts/`. `FEATURE.md` says the human deletes each once its story is merged, and both are merged now.

## 5 The documentation as a whole

I read `README.md` and the operator guide from the top, and the token, preflight and runtime parts of the project guide and the decision log.

The token's story is told the same way everywhere:
- the guide's *The hosting-service token*, *The agent runs as a second user*, *Users and directories*, the `token-file` row and its four faults;
- the project guide's `token_file_item` sentence;
- decision entries `:411` and `:415`.

No text names `/run/secrets` as current.

One finding. Four sentences still say that no container or build was observed:
- `README.md:3`: "a real container is not yet observed";
- the operator guide's introduction (`docs/operator-guide.md:3`), in the same words;
- *Build it* (`:147`): "A real build is not yet observed … Treat the first build as the morning observation";
- *The health check and the restart policy* (`:248`): "A real running container has not been observed yet".

The new *Container runtimes* section (`:303-331`) says the image and the compose file run under Docker Desktop and Podman, from the probe. That probe built the image, started it, reached the stop `repository_unavailable` and saw the health check report it. A newcomer gets both claims.

The heading *Replace the placeholders before the first build* (`:149`) is stale as well: the human's `b642dd31` pinned the image, and the section's text already says so.

None of this misleads anyone about behaviour, but the documents contradict each other. Draft S0007.

The Podman restart text agrees with *The health check and the restart policy*, which now points to it. The examples I could run were run: the S0002 demo's snippet as the guide describes the item, and `check_demos`. The `docker`/`podman` commands need a runtime that is not here.

## 6 Decisions taken for the human

These are listed for the human to accept or revisit. Nothing is decided here.

From `FEATURE.md`, taken by the session for the human to confirm:
- **6**: two stories for the token, the image and the preflight separately.
- **7**: a read-only bind mount with `create_host_path: false`, not a compose secret with an absolute target. The folder is `factory:factory` `0700` at `/home/factory/.secrets`. A `chown`/`chmod` in the entrypoint and Swarm mode were rejected.
- **8**: the entrypoint comment fixed by S0001.
- **9** and **11**: the leaves to change four earlier test modules (S0001) and to replace the three tests of the token item (S0002).
- **10**: the item checks the folder and no longer the file's owner and mode. A missing folder reads `the token file does not exist`.
- **12**: S0003's stand-in `WorkItemReader`, because the real reader never gives a stateless document.
- **13**: one documentation-only story, under the section name *Container runtimes*, including fault 4.
- **14**: the host permissions per host. Only Windows was observed; the Linux Docker and rootless Podman commands are written from documentation.
- **15**: git's hooks are named beside the project commands as left for v2. The folder is checked before the file. Rancher Desktop is named untested, and the Mac is out of scope. The restart text is what was tested, so Windows has no automatic restart and the operator starts the machine and Compose, by hand or as a scheduled task.

From the story logs:
- S0001, the human's answers (entries 5 and 7): criterion 3 was reworded as prose, and there is a `.secrets.baseline` entry for the quoted fragment of the coder's log, on the story's `ongoing/` and `done/` paths.
- S0001, coder: the folder is made in the existing users-and-folders `RUN`, not in a layer of its own.
- S0003, coder: the handlers were not reordered to check the state before `_book`'s local `git mv`.
- S0004, coder: the domain's `work_item_path` was reused, not a local helper.
- S0005, documenter: *Container runtimes* is placed directly after the container section, and *What the container cannot see* now names both runtimes.

From this acceptance, for the human: whether S0006's test changes get the leave to change earlier tests (the draft asks for it), or the story is rewritten as a new module.

## 7 The slow checks

The project offers nothing beyond `make check` and `make mutants`: no image scan and no SBOM target. The `Makefile` targets are `check lint types layers sast secrets licenses test duplicates documents mutants`.

`make documents` (`documents ok`) and `make duplicates` (`0 new, 39 known, 0 gone`) were run above.

No image was built here: there is no runtime, and the build is the morning observation in the operator guide. The real-container checks of S0001 and S0005 are left to the first start (plan step 2), as `FEATURE.md` says:
- the folder's owner and mode, and the agent's `Permission denied`;
- the restart service on a Linux host.

## 8 Cost

5 stories, **32 runs, 17.7 min, $4.45**: $0.89 a story on average, below F0012's.

S0001 stands out: 8 runs, 6.3 min, $1.50, a third of the feature. Its log says why. Two coder runs ended on `make secrets`: detect-secrets flagged the YAML of the bind mount in criterion 3, and then the coder's own log entry that quoted it. The human answered twice (reword the criterion; a baseline entry) before the story went on (entries 4-8). Without those two runs it would have cost about what S0002 cost.

The other four stories had six runs each, no rework round, and cost $0.60–$0.90. S0003 and S0005 changed no code, so their coder runs only confirmed what was already true.

## Proposed stories

- `drafts/F0013-S0006-the-preflights-details-pinned-in-full.md`: pins the whole detail of `agent-environment`, `agent-run-probe` (with and without an agent user), `hosting-service` and `agent-runtime-version`, which the operator reads and the guide quotes. It kills the 11 text survivors of section 3. It is test-only and needs the human's leave to strengthen four earlier tests.
- `drafts/F0013-S0007-what-the-probe-observed-in-the-documents.md`: documentation only. It replaces the four "not yet observed" sentences of the README and the operator guide with what the probe saw, and renames the stale *Replace the placeholders* heading.

## Log (append only)

1. acceptor: accepted with drafts; 2 drafts proposed; make mutants 549/567

   1. **Scope:** no finding. Every Scope bullet has a merged story (S0001 to S0005), nothing was built outside the scope, and the Goal's "done when" holds. `make check` was green as I found it and is still green.
   2. **Feature demo:** green. `/tmp/f0013-demo/demo.py` runs through the real wiring (`boundaries_from_environment`, `machine_extras`) and `image/git-credential-factory`. It shows that:
      - the image's `ENV` path matches the compose file's read-only bind target, which sits in the `factory:factory` folder with mode `0700`;
      - the compose file has no secrets left;
      - the factory reads the token from that path;
      - `token-file` passes a `0777` file and refuses a `0755` folder;
      - the helper gives the token to a user who can enter the folder, and nothing (exit 1) to one who cannot.
      - No container runtime is installed here, so the folder inside a running container stays the morning observation.
   3. **Mutation score:** 549 of 567 mutants killed (96.8 %), a fresh run of 27 s. `preflight` 379/394, `check_demos` 170/173.
      - Every mutant in the code F0013 changed is killed. The 18 survivors are all in code F0013 did not touch.
      - 11 of them change preflight detail texts that the tests check only with `in`: draft S0006.
      - The other 7 are near-equivalent or cosmetic: no draft.
   4. **What the stories noticed:**
      - In S0001, detect-secrets flagged the criterion's YAML and then the log entry that quoted it. The human added a baseline entry. Worth a lesson for the skills, not a story.
      - Podman's disk reclaim is not in the guide, left until a Podman run shows it.
      - `image/compose.yml:1` still says "Docker restarts it".
      - F0012's drafts S0031 and S0032 are still in F0012's `drafts/`, for the human to delete.
   5. **Documentation:** the token text is consistent everywhere. The finding: four sentences still say no container or build was observed (README:3; operator guide :3, :147 and :248), which contradicts the new *Container runtimes* section and the probe. The heading *Replace the placeholders* is stale too. Draft S0007.
   6. **Decisions for the human:** FEATURE decisions 6 to 15, plus from the story logs:
      - S0001: criterion 3 reworded as prose and a baseline entry (the human's answers); the folder made in the existing `RUN`.
      - S0003: the handlers not reordered.
      - S0004: `work_item_path` reused.
      - S0005: where *Container runtimes* goes in the guide.
      - S0006 needs the human's leave to change four earlier tests.
   7. **Slow checks:** none beyond `make check` and `make mutants`. `make documents` printed `documents ok` and `make duplicates` printed `0 new, 39 known, 0 gone`. No image was built: there is no runtime here.
   8. **Cost:** 32 runs, 17.7 min, $4.45. S0001 stands out at 8 runs and $1.50: two coder runs went to `make secrets` and the human's two answers. The other four stories cost $0.60 to $0.90 each, with no rework.
