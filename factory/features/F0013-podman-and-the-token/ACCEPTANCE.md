---
stage: done
pr: 190
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0013-S0001, F0013-S0002, F0013-S0003, F0013-S0004, F0013-S0005, F0013-S0006, F0013-S0007]
outcome: accepted
---
# Acceptance of Podman and the token

## Verdict

**accepted.** This is F0013's second acceptance. It covers the five stories of the first one and the two that acceptance proposed (S0006, S0007), and both of its findings are closed. The feature demo is green from the token's folder to the preflight report the operator reads. The documents no longer contradict each other on what the probe observed. `make mutants` kills 561 of 567: the six survivors are the near-equivalent and cosmetic ones the first acceptance already judged not worth a story. Two one-line leftovers (section 4) are too small for a story of their own.

## 1 Scope

None. The first acceptance's mapping still holds: S0001 to S0005 cover every Scope bullet of `FEATURE.md`, and nothing was built outside the scope. S0006 and S0007 are the first acceptance's proposals, which the human promoted (decision 16 gives S0006's leave). Since that acceptance (`59221f98`), the diff outside `factory/` and `docs/runs/` is three test modules (S0006), `README.md` and `docs/operator-guide.md` (S0006, S0007). `src/` and `image/` did not change.

The Goal's "done when" holds:
- every story is merged and `make check` is green;
- the token's folder and mount are in the image and the compose file;
- the preflight checks the folder;
- *Container runtimes* names the runtimes and says how to run under Podman.

`make check` as found: `check: green`, coverage 99.50 %.

## 2 Feature demo

No container runtime is on this machine, so the demo runs the real entry points without one:
- the image files as Compose and the build read them;
- `boundaries_from_environment`, `machine_extras` and `MachineChecks`, which the factory's start and preflight use;
- `image/git-credential-factory` as git calls it;
- the README and the operator guide as a newcomer reads them.

The token's folder is a stand-in in a temporary directory. A folder without its search bit stands in for what the agent meets in a `0700` folder it does not own. Section 4 adds what S0006 and S0007 made a user-visible promise. A machine with one fault per item runs the whole preflight: the hosting service fails, the runtime reports a version other than the pin, the agent run has no environment, and the probe run dies. The demo prints the report the operator would read in `preflight_failed`, then checks that the guide quotes those details and no longer says that nothing was observed. Only the hosting service (`FakeHostingService`) and the agent runtime (`FakeAgentRuntime`) are fakes. The script is `/tmp/f0013-accept2/demo.py`, outside the repository.

```
$ uv run python /tmp/f0013-accept2/demo.py; echo "exit $?"
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
== 4. the preflight report the operator reads in preflight_failed, with one fault per item
agent user                  = None
  tool:git               pass 
  tool:uv                pass 
  tool:make              pass 
  tool:claude            pass 
  hosting-service        FAIL the hosting service failed find_open_pull_request: injected failure; check the token and the network
  agents                 pass 
  agent-runtime-version  FAIL the agent runtime reports 2.1.290, the image pins 2.1.289; rebuild the image or change the pinned version
  token-file             pass 
  agent-user             FAIL FACTORY_AGENT_USER is not set: every agent would run as the factory's user, who can read the token file
  agent-environment      FAIL the agent run has no PATH; the agent run has no HOME
  agent-run-probe        FAIL the probe run ended died; run claude -p by hand as the factory user to see why
== 5. what the guide quotes of those details, and what it says was observed
guide quotes 'the agent run has no PATH'                          True
guide quotes 'the agent run has no HOME'                          True
guide quotes 'check the token and the network'                    False
guide quotes 'rebuild the image or change the pinned version'     True
guide quotes 'the factory user'                                   True
guide quotes '/home/factory/.secrets/hosting-token'               True
guide quotes 'Container runtimes'                                 True
guide quotes 'Update the pins'                                    True
README 'not yet observed'/'not been observed' = 0 | 'repository_unavailable' = True
guide  'not yet observed'/'not been observed' = 0 | 'repository_unavailable' = True
exit 0
```

Green. The details are exactly the ones S0006's Interface table gives, and they are what the operator reads. The one `False` is not a gap. The guide's `hosting-service` row (`docs/operator-guide.md:269`) gives the hint as an instruction ("Check the token (`FACTORY_TOKEN_FILE`) and the network"), not as a quote. S0006's docs criterion left that row as it was.

What the demo cannot show is still the folder's owner and mode inside a running container. That stays the morning observation that `FEATURE.md` puts out of scope.

Also run: `uv run python -m factory.entry.check_demos` printed `demos ok`.

## 3 Mutation score

The `mutants/` cache from the first acceptance came from before S0006's tests, so I moved it aside (`/tmp/f0013-accept2/mutants-previous`). `make mutants FEATURE=F0013` then ran from scratch and finished without the `stopped after` line. It selected the same two modules. The counts come from mutmut's `.meta` files (`exit_code_by_key`):
- `src/factory/application/preflight.py`: 391 killed of 394, 3 survived (the first acceptance had 379 of 394).
- `src/factory/entry/check_demos.py`: 170 killed of 173, 3 survived (unchanged).
- Together: **561 killed of 567 (98.9 %), 6 survived, no timeouts.** The first acceptance had 549 of 567.

S0006 killed all 11 of the preflight detail survivors, the group it was written for, and one more. The make output lists six survivors, and `mutmut show` gives each one's change:
- **Arguments the fakes do not see** (3, `preflight`):
  - `MachineChecks._hosting_service__mutmut_1`: `find_open_pull_request(MAIN_BRANCH)` becomes `(None)`. The fake answers any branch, and the item ignores the answer.
  - `Preflight._run_probe__mutmut_3` and `__mutmut_5`: `git.checkout(MAIN_BRANCH, start_point=_MAIN_REF)` gets `start_point=None` or loses the argument. The `reset_to(_MAIN_REF)` that follows puts the checkout at `origin/main` anyway.
  - All three are near-equivalent. No draft, as the first acceptance decided.
- **Equivalent or cosmetic** (3, `check_demos`): `_read__mutmut_1` and `_3` (`read_text(encoding=None)` and `"UTF-8"`, equal under a UTF-8 locale), and `main__mutmut_2` (`ArgumentParser(prog=None)`). No draft.

## 4 What the stories noticed

From S0006 and S0007:
- **S0006**: the tester, coder and reviewer noticed nothing outside the story, and the documenter saw nothing stale. The coder's run confirmed only that `src/` already behaved as the Interface says. That was expected for a test-only story.
- **S0007**: the documenter cross-read the remaining "Morning observation" paragraphs (the second user and the `sudo` rule, the agent run, Linux `podman-restart.service`). They are still open and correct. The documenter dropped the *Build it* sentence "v1's container has no Docker" because it is no longer true. Nothing else.

What the first acceptance noticed, now:
- F0012's drafts S0031 and S0032 are gone: the human deleted them in `2346ffaf`. Closed.
- `image/compose.yml:1` still says "The factory's container: Docker restarts it". Under Podman on Windows nothing restarts it after a machine restart (the guide's *Podman: the restart*). No story of F0013 touched `image/` after S0001, so this one-word comment fix is still left for the next story that touches `image/`. Too small for a draft of its own.
- `docs/decisions.md:255` still lists `/run/secrets/hosting-token` as "Open". The F0013-S0001 entry supersedes it by name, so it is not a contradiction.
- Podman's disk reclaim is still not in the guide. It is left until a Podman run shows it, as before.

The acceptance noticed one more: the morning observation of the agent run (`docs/operator-guide.md:220`) says a real agent run "needs Docker and the image's second operating-system user". Since *Container runtimes*, "a container runtime" would be the accurate word. It is harmless, and it fits the same small text pass as `compose.yml:1`.

## 5 The documentation as a whole

I read `README.md` and the operator guide from the top, and the decision log's F0013 entries.

The first acceptance's finding is closed. `README.md:3`, the guide's introduction, *Build it* (`:147`) and *The health check and the restart policy* (`:248`) now all say what the probe of 2026-10-17 saw, and they say it the same way:
- built under rootless Podman without the pins, started, and stopped at `repository_unavailable`;
- the health check ran;
- a run with a real repository and token, and a build with the pins, are still open.

This agrees with *Container runtimes* (`:303`). `:248` also qualifies `restart: unless-stopped` with a pointer to *Podman: the restart*. The heading is now *Update the pins*; nothing linked to the old name, and its text matches the pinned `image/Dockerfile`.

S0006's sentence in "The probe of the agent run" (`:282`) matches the code: without `FACTORY_AGENT_USER` the detail names `the factory user`, which the demo prints. The other details in the table are quoted or described as the code produces them.

No contradiction found. The two leftover word fixes are in section 4. `make documents` printed `documents ok`.

## 6 Decisions taken for the human

These are listed for the human to accept or revisit. Nothing is decided here.

Unchanged since the first acceptance, still to confirm: `FEATURE.md` decisions 6 to 15, and the story-log decisions of S0001 to S0005 that the first report listed in its section 6:
- the reworded criterion and the `.secrets.baseline` entry;
- the folder made in the existing `RUN`;
- the handlers not reordered;
- `work_item_path` reused;
- where *Container runtimes* sits.

New since then:
- **Decision 16** (`FEATURE.md`): the human's leave for S0006 to change four earlier tests in three modules, with renames allowed. The tester stayed within it, and the reviewer checked that.
- **S0006, tester**: three tests renamed to say "with its detail":
  - `test_a_fault_in_the_environment_fails_with_its_detail`;
  - `test_a_probe_that_does_not_complete_fails_with_its_detail`;
  - `test_the_version_item_fails_with_its_detail_when_the_versions_differ`.

  `test_the_hosting_service_item_reports_a_failed_call` kept its name. The probe rows with no agent user are built through `settings.model_copy`.
- **S0006, documenter**: the `hosting-service` row of the guide is left as a description ("Check the token ... and the network") and does not quote the detail. The criterion allowed this.
- **S0007, documenter**: the sentence "v1's container has no Docker" is dropped from *Build it*. The build time is given as "42 s under Podman 5.8.3".
- **S0007, tester**: a test that greps the documents for the stale sentences was rejected. The document check and the demo cover them.
- **From this acceptance**: no draft for the two one-word leftovers (`image/compose.yml:1`, `docs/operator-guide.md:220`). If the human wants them fixed before the first start, a story for both is one coder and one documenter line.

## 7 The slow checks

The project offers nothing beyond `make check` and `make mutants`: no image scan and no SBOM. The `Makefile` targets are unchanged: `check lint types layers sast secrets licenses test duplicates documents mutants`.

Also run:
- `make documents`: `documents ok`;
- `make duplicates`: `duplicates: 0 new, 39 known, 0 gone`.

No image was built here: there is no runtime. The checks in a real container stay with the first start (plan step 2), as `FEATURE.md` says:
- the folder's owner and mode, and the agent's `Permission denied`;
- a build with the pins;
- the restart service on a Linux host.

## 8 Cost

7 stories, **44 runs, 22.7 min, $5.76**: $0.82 a story on average.

The two new stories cost little:
- S0006: 6 runs, 3.1 min, $0.76;
- S0007: 6 runs, 1.9 min, $0.55.

Neither had a rework round. Both coder runs changed nothing, as the stories expected, so those runs only confirmed `make check`. That is the fixed cost of a test-only or documentation-only story in this pipeline.

S0001 still stands out at 8 runs and $1.50, for the reasons the first acceptance gave: two coder runs went to `make secrets` on a criterion's quoted YAML. The first acceptance run itself ($2.25, 8.0 min) is not in the stories' sum.

## Proposed stories

None. The six mutation survivors are near-equivalent or cosmetic. The two leftovers (`image/compose.yml:1` "Docker restarts it", `docs/operator-guide.md:220` "needs Docker") are one word each and are listed in section 6 for the human to decide.

## Log (append only)

1. acceptor: accepted; 0 drafts proposed; make mutants 561/567

   This is F0013's second acceptance. It covers S0001 to S0007, and both findings of the first acceptance are closed: S0006 pinned the preflight's details and S0007 updated the documents.

   1. **Scope:** no finding. Every Scope bullet has its merged story. Since the first acceptance, only three test modules, `README.md` and `docs/operator-guide.md` changed; `src/` and `image/` did not. The Goal's "done when" holds, and `make check` was green as found (99.50 %).
   2. **Feature demo:** green. `/tmp/f0013-accept2/demo.py` runs the real wiring, `MachineChecks`, the credential helper and the documents. It shows that:
      - the image's ENV path equals the compose file's read-only bind target in the `0700` folder;
      - `token-file` passes a `0777` file and refuses a `0755` folder;
      - the helper gives the agent nothing (exit 1);
      - a machine with one fault per item prints exactly S0006's details, including `as the factory user`;
      - the guide quotes them, and neither the guide nor the README says "not yet observed" any longer.
      No container runtime is installed here.
   3. **Mutation score:** a fresh run (the old `mutants/` cache was moved to `/tmp`) killed 561 of 567 (98.9 %), up from 549. `preflight` 391/394, `check_demos` 170/173. S0006 killed all 11 detail survivors. The 6 left are near-equivalent (arguments the fakes do not see, a checkout that the following reset makes irrelevant) or cosmetic (an encoding argument, `prog`). No draft, as the first acceptance decided.
   4. **What the stories noticed:** S0006 and S0007 noticed nothing new. F0012's superseded drafts are gone (`2346ffaf`). Two one-word leftovers remain: `image/compose.yml:1` says "Docker restarts it", and `docs/operator-guide.md:220` says "needs Docker" where "a container runtime" is meant.
   5. **Documentation:** no contradiction. The probe's observations read the same way in the README, the guide's introduction, *Build it*, the health check section and *Container runtimes*. The heading *Update the pins* fits the pinned Dockerfile. `documents ok`.
   6. **Decisions for the human:** `FEATURE.md` decisions 6 to 16 and the story-log decisions of S0001 to S0005, as the first report listed them. New since then:
      - S0006's test renames under decision 16, and the `hosting-service` row left as a description;
      - S0007 dropped the "v1's container has no Docker" sentence and rejected a grep test;
      - this acceptance wrote no draft for the two one-word leftovers.
   7. **Slow checks:** none beyond `make check` and `make mutants`. `make documents` printed `documents ok`, and `make duplicates` printed `0 new, 39 known, 0 gone`. No image was built: there is no runtime here.
   8. **Cost:** 7 stories, 44 runs, 22.7 min, $5.76. S0006 ($0.76) and S0007 ($0.55) each took 6 runs with no rework. S0001 ($1.50) still stands out, because of the `make secrets` runs the first report explained.
2. done (pull request merged); cost: 2 runs, 16.8 min, 77 turns, 275k tokens in (5495k more from cache), 47k out, $3.42
