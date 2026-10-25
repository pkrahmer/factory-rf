---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 434
comments_read: [6394738591, 6394846270]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T06:48:13.935214Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T06:48:13.940918Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T06:48:30.650010Z'
  stage: intake
  run: 8b2f6c251d904cdc93ca1669de54d7b8
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T06:48:50.696492Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T06:52:15.693944Z'
  stage: tests
  run: dcb88821a34b44729da009829a096ce7
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T06:52:37.054408Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-10-25T06:57:36.409465Z'
  stage: doing
  run: 077334feb3184ef680714cd0336d2784
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-10-25T07:11:18.750497Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-25T07:11:38.002296Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-25T07:18:42.979596Z'
  stage: doing
  run: d5a0811606124bcc9787b648950a679a
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-25T07:19:03.339648Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-25T07:19:28.651031Z'
  stage: review
  run: 8b0d0641d4dc4df492cc85d0501e54bc
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-25T07:19:49.080669Z'
  stage: docs
- number: 14
  speaker: documenter
  kind: question
  at: '2026-10-25T07:22:06.192969Z'
  stage: docs
  run: 538377f2e6e44e1a9fb74b15ba2f37d6
  blocked: question
- number: 15
  speaker: human
  kind: comment
  at: '2026-10-25T07:24:25.731661Z'
  stage: docs
---

# The operator guide's chapter "The machine"

## Description

An operator who has never seen v1.1's container must take a fresh Ubuntu 24.04 VM to a running `container` instance in under an hour of their own time with the operator guide alone (`planning/v1.2-plan.md`, F0043's goal). S0001 and S0003 left the sections *The stage image*, *The script* and *The service* in a chapter `## The machine` of `docs/operator-guide.md`; this story completes the chapter from the runbook (`planning/overnight/gcp-runbook-2026-10-24.md`) and the plan, and the documenter reads the whole chapter against the code once: GCP in numbered steps (the project and the budget alert, NAT and IAP, the data disk, the VM with no service account and no external address, the SSH through IAP, the script with its arguments and its second run, the secrets by hand, the image build, the first start, the board and the health over SSH, the rebuild after a merge); the same for any Ubuntu 24.04 VM with a spare disk, and what the script needs that `podman machine` and WSL 2 do not give; what the container can and cannot see; the costs with the plan's numbers; the metadata server; where the logs are. It also writes the decision-log entry of the machine. No code, no test and no image change; the smoke test and `make documents` check the chapter. What stays: every sentence of the three earlier sections that is still true; the chapters of v1.1's image and container, which F0044 (the layers go) removes.

## Interface

None: nothing changes under `src/factory/`, in any test, under `vm/`, `image/`, `template/` or `claude/`. The documenter changes `docs/operator-guide.md`, `docs/decisions.md`, `docs/project-guide/README.md` (if a section name of the guide index must follow) and `README.md`, as the docs criterion says. No test reads the documents: `make check` runs at `doing`, before the documenter, and its `not_read` in `factory/pipeline.yml` leaves out `README.md` and `docs/*.md`; the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: the documenter writes the chapter from the runbook (`planning/overnight/gcp-runbook-2026-10-24.md`) and the plan, reads *The stage image*, *The script* and *The service* against `vm/Dockerfile`, `vm/setup.sh` and `vm/factory.service` and corrects any sentence that is no longer true, and makes the following true; the smoke test and `make documents` check them, no test does:
   - `docs/operator-guide.md` has one chapter `## The machine`, placed before `## The machine's image`, whose `###` sections are exactly, in this order: *What it is*, *The stage image*, *The script*, *The service*, *On GCP, step by step*, *On any Ubuntu 24.04 VM*, *What the container can and cannot see*, *The costs*, *The metadata server*, *Where the logs are*, *The rebuild after a merge*; and the list at the top of the guide names "The machine" right before "The machine's image".
   - *What it is*: the host (the factory as `factory@<instance>` under the user `factory`, the hosting token on the host and nowhere else), the dataset (`<pool>/factory/<instance>` at `/srv/factory/<instance>/work`, `/work` in every container, its base `@base`), the container (the stage image, `--rm`, `--userns=keep-id`, `--timeout`), one user and no second one; that `factory` has no `sudo` right but the four `zfs` commands of the optional `--sudoers` fallback, and that the steps that need root (the script, `systemctl`, the install of the secrets) run from the operator's own account with `sudo`; that in v1.2 one repository URL serves both the factory's own code and the project: `--repository-url` is the clone of `/srv/factory/<instance>/factory` and `FACTORY_REPOSITORY_URL`, so an instance builds the repository it runs from; and the layout of `/srv/factory/<instance>` (`work`, `repo`, `state`, `factory`, `tools`, `factory.env`, `image-id`, `askpass`).
   - *On GCP, step by step*: a numbered list of at least ten items: the runbook's sections 1 to 3 with their commands (its section 4 is what the script does; on a VM the prototype prepared, the script finds those steps done), then the script copied with `gcloud compute scp --tunnel-through-iap` and its first run as root with `--device /dev/disk/by-id/google-factory-data --repository-url https://github.com/pkrahmer/factory-rf.git --ref <the tag or branch to run>`, the three secrets placed by hand from the operator's account (`sudo install -m 0600 -o factory -g factory <file> /home/factory/.secrets/<name>` for `hosting-token`, `claude-token` and `anthropic-api-key`, the copy removed afterwards, never pasted into a chat or an agent's prompt; all three files must exist, and an empty `anthropic-api-key` means no key, because podman refuses to mount a missing file and every agent run would stop with exit status 125: decision 10), the script's second run with the same arguments, the image build as `factory` in `/srv/factory/vm/factory` (`podman build -f vm/Dockerfile -t factory-stage:vm --build-arg FACTORY_IMAGE=<ref> /srv/factory/vm/factory`), the first start (`sudo systemctl start factory@vm`), the board as `factory` with the environment file loaded (`set -a; . /srv/factory/vm/factory.env; set +a`, then `/srv/factory/vm/factory/.venv/bin/factory-watch`) and the health (`/srv/factory/vm/factory/.venv/bin/factory-health --state-directory /srv/factory/vm/state`; the console scripts live in the factory's virtual environment, which the environment file's `PATH` does not name), and `gcloud compute instances stop` when the machine is not used. The list names, in this order of first occurrence, `gcloud billing budgets create` with `120`, `gcloud compute routers nats create`, `gcloud compute disks create`, `--no-service-account`, `--no-address`, `--tunnel-through-iap`, `gcloud compute scp`, `vm/setup.sh`, `/home/factory/.secrets`, `podman build -f vm/Dockerfile`, `systemctl start factory@vm`, `factory-watch` and `factory-health --state-directory`.
   - *On any Ubuntu 24.04 VM*: the same from the script on, what the script needs (a kernel with the ZFS module, a spare block device, rootless Podman with a sub-id range for `factory`, outbound network for apt, npm, GitHub and the Anthropic API), and that `podman machine`, WSL 2 and the workplace's Podman Desktop are not hosts for it (the plan's question 7).
   - *What the container can and cannot see*: the dataset at `/work` with the checkout and the agent's home, the read-only mounts (the host repository's `.git` at `/upstream` in the sync container, the login and instructions files at their paths), the network (the API, npm, GitHub through NAT), and not the hosting token, the host's files, the next stage, or anything of the metadata server worth having.
   - *The costs*: a table with one row each for the VM, the disk and NAT, with the plan's numbers (`e2-standard-2` about $50 to $55 a month, `e2-standard-4` about $100, the 50 GB `pd-balanced` disk about $5, Cloud NAT about $1 a month plus traffic), the budget alert at $120 with its three thresholds, and a sentence that a stopped VM costs its disks.
   - *The metadata server*: `169.254.169.254`, what a container gets from it with `--no-service-account --no-scopes` (instance metadata, no token), and the `Metadata-Flavor: Google` header.
   - *Where the logs are*: `journalctl -u factory@vm` (what `factory-run` prints; the `systemctl` commands stay in *The service*), `/srv/factory/vm/state/factory.log` with the `stage environment:` lines and how to read the plan's measures from them, `health.json` through `factory-health`, and `podman ps` for a running stage container.
   - *The rebuild after a merge*: as `factory`, `git -C /srv/factory/vm/factory pull --ff-only` (or `git fetch --tags` and `git checkout <tag>` for a tagged ref), `uv sync --frozen --no-dev` with the tools' `uv`, `podman build ...` in `/srv/factory/vm/factory`, a new uuid into `/srv/factory/vm/image-id` (`cat /proc/sys/kernel/random/uuid > /srv/factory/vm/image-id`); then from the operator's account `sudo sh vm/setup.sh <the same arguments>` after every merge (it is idempotent: it carries over a changed pin of `vm/Dockerfile`, a changed `vm/factory.service` and a changed `image/git-credential-factory`, rewrites the environment file and reports the rest found), then `sudo systemctl restart factory@vm`. The section names, in this order, `git pull`, `uv sync --frozen --no-dev`, `podman build`, `image-id`, `vm/setup.sh` and `systemctl restart factory@vm`.
   - The chapter names each of `e2-standard-2`, `europe-west3`, `pd-balanced`, `50`, `$120`, `169.254.169.254`, `Metadata-Flavor`, `journalctl -u factory@vm`, `/srv/factory/vm/state/factory.log`, `stage environment:`, `zfs allow`, `--sudoers`, `--userns=keep-id`, `podman machine`, `WSL`, `hosting-token`, `claude-token`, `anthropic-api-key` and `Cloud NAT`.
   - `docs/decisions.md` has one section `## The factory runs on the host, and the stage image carries the tools alone`, dated 2026-10-24, that names `2026-10-24`, `planning/v1.2-plan.md`, `F0043`, `systemd`, `factory@`, `zfs allow`, `sudoers`, `/etc/factory/claude`, `FACTORY_IMAGE_ID_FILE` and `F0044`, with the human's decisions 1, 3, 6 and 8 of the plan, the reasons (one user, the token on the host, the delegation first and the `sudoers` fallback second, the image without the factory so that the factory's code and the tools change apart, the identity file the operator renews), what was rejected (the factory in a container with the podman socket, the factory as root, the stage container pushing), and that F0044 removes the Docker path; no other entry changes.
   - `README.md` names `vm/setup.sh` once, in one sentence for the newcomer: an instance of v1.2 runs on a VM prepared by `vm/setup.sh`, pointing to the chapter.
   - `docs/project-guide/README.md`: none, unless a guide file names a chapter of the operator guide that moved.
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
awk '/^## The machine$/{on=1; next} /^## /{on=0} on && /^### /' docs/operator-guide.md
```
Expect: eleven lines: `### What it is`, `### The stage image`, `### The script`, `### The service`, `### On GCP, step by step`, `### On any Ubuntu 24.04 VM`, `### What the container can and cannot see`, `### The costs`, `### The metadata server`, `### Where the logs are`, `### The rebuild after a merge`

```bash
c=$(awk '/^## The machine$/{on=1; next} /^## /{on=0} on' docs/operator-guide.md); for w in 'e2-standard-2' 'europe-west3' '169.254.169.254' 'journalctl -u factory@vm' 'systemctl start factory@vm' '--tunnel-through-iap' 'podman build -f vm/Dockerfile' 'factory-health --state-directory'; do printf '%s\n' "$c" | grep -c -F -- "$w"; done | awk '$1>0{n++} END{print n}'
grep -c '^## The factory runs on the host, and the stage image carries the tools alone$' docs/decisions.md; grep -c 'vm/setup.sh' README.md
```
Expect: three lines: `8`, `1`, `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: "None" is right for a documents-only story. It names the files the documenter changes (`docs/operator-guide.md`, `docs/decisions.md`, `README.md`, and `docs/project-guide/README.md` only if needed), and all of them are within the documenter's write paths. The Interface states no behaviour, so no rule is missing a criterion.
   Criteria: the criteria are checkable by the smoke test and `make documents`, as the story says, not by tests. Criterion 1 (nothing outside the docs changes) and criterion 2 (`make check` stays green) are testable. Criterion 3 is a docs criterion with concrete, checkable bullets: the exact list and order of `###` sections, the named strings and their order of first occurrence, the numbered list of at least ten items, the decision-log section title and the words it names, and one `vm/setup.sh` sentence in `README.md`. This is a documents story, so there is no failing side to cover.
   Smoke test: all three blocks are runnable. The first prints the eleven `###` lines. The second counts eight present words, then prints 1 for the decision title and 1 for `vm/setup.sh` in `README.md`, which matches `8`, `1`, `1`. The third is `make documents | tail -n 1` and expects `documents ok`. None runs pytest, so the `-q` rule does not apply. Every `Expect:` line is checkable against the output.
   Architecture: no layer is touched. The files are the human-facing docs that `CLAUDE.md` assigns to the documenter. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes.
   Scope: it matches the feature's Scope bullet for the operator guide's chapter and the decision-log entry, and it is the last story in the feature's build order. It touches nothing in "Out of scope": no GCP calls, no change to `image/`, and no code for the stage environment.
4. factory: started tests as vm.
5. tester: No tests written: this is a documents-only story. Its Interface says nothing changes in any test, and it says no test reads the documents.
   criterion 1: no test. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` was changed by this stage; `git status --short` is empty.
   criterion 2: no new test; `make check` covers it (the coder runs it at `doing`, the factory at `docs`).
   criterion 3 (docs): no test, as the criterion says. The smoke test and `make documents` check it.
   Files created: none. Modules the test run could not import: none, because no new tests exist. I did not run `make test`: there are no new red tests to confirm, and the factory runs it after this stage. `make lint`: green.
   Open: nothing.

   `lint`: lint: green (0.2 s)
   `test`: test: green (186.4 s)
6. factory: started doing as vm.
7. coder: I built nothing, and I stopped before handing on because `make check` is red. This is a documents-only story: nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changed in this stage, and `git status --short` is empty (criterion 1). Compared with `main`, the branch changes only this work item's `.md` and `.costs.jsonl`.

   What is red: `make check` stops at `make secrets` (`make: *** [Makefile:61: secrets] Error 1`). detect-secrets flags "Hex High Entropy String" in finished acceptance reports that this branch does not touch:
   - `factory/features/F0023-a-known-result-is-not-checked-again/done/F0023-A0001-acceptance.md:84`
   - `factory/features/F0023-a-known-result-is-not-checked-again/done/F0023-A0002-acceptance.md:99` (four times)
   - `factory/features/F0042-the-stage-environment-behind-one-interface/done/F0042-A0002-acceptance.md:62`
   - `factory/features/F0042-the-stage-environment-behind-one-interface/done/F0042-A0002-acceptance.md:68`

   The likely cause: this checkout has no remote and no `origin/main` ref (`git branch -a` shows only `main` and the work-item branch; `git diff origin/main` fails with "unknown revision"). So `make secrets` cannot limit itself to the files changed against `origin/main`, and it appears to scan every tracked file instead. These findings are outside this work item and I did not touch them.

   Every other target of `make check`, run one by one in the foreground, is green: `lint: green (0.1 s)`, `types: green (0.2 s)`, `layers: green (0.1 s)`, `sast: green (1.9 s)`, `licenses: green (0.1 s)`, `test: green (187.3 s)`.

   Refactor step: there is no diff, so nothing to refactor. The journal did not change the meaning of the task, so `## Description` stays as it is.

   Question: how should this go forward? The options I see:
   (a) Provide `origin/main` in the stage's checkout (a remote, or the ref fetched into the dataset), so `make secrets` scans only the changed files, then run `doing` again.
   (b) Fix the old acceptance reports' high-entropy values, or add them to `.secrets.baseline`, in a separate story or by your own commit. A new baseline entry needs your leave under "Not without asking".
   (c) Accept that the factory's own check after this stage runs where `origin/main` exists, and let me end with `review` on the next run, since this story changes no file that `make secrets` would check.
   I would choose (a): the red comes from the missing ref, not from this branch's changes. I would then run (b) as its own story if a full scan on `main` shows the same findings.
8. 2026-10-25 human: (a). The red comes from the missing `origin/main` in the dataset's checkout, not from this branch. The sync now also fetches the host's branches as `origin/<branch>` (story F0043-S0006; this instance already runs that one-line change), so `make secrets` scans only the changed files again. Run `doing` again as a documents-only round: nothing outside the docs changes, and `make check` should end green. (b), the old acceptance reports' values, is not this story's: it is raised for the human.
9. factory: started doing as vm.
10. coder: I built nothing. This is a documents-only story: the documenter writes the chapter and the decision-log entry. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changed in this stage, and `git status --short` is empty (criterion 1).

    `make check` is now green and ends with `check: green` (`test: green (193.3 s)`, total coverage 99.20 %) (criterion 2). As the human's answer in entry 8 said, the checkout now has `origin/main` (`git branch -a` lists `remotes/origin/main`), so `make secrets` scans only the changed files again. Last round it went red on the done acceptance reports of F0023 and F0042; this round it no longer does.

    Main choice: I kept to the human's answer and handed the story on with no change. The alternative I rejected was touching the old acceptance reports or `.secrets.baseline`: the human said that is not this story's work (option (b)).

    Refactor step: there is no diff, so there was nothing to refactor. The journal did not change the meaning of the task, so `## Description` stays as it is.

    Noticed, not touched: the high-entropy values in `F0023-A0001-acceptance.md`, `F0023-A0002-acceptance.md` and `F0042-A0002-acceptance.md` are still there. A full scan on `main` will flag them again; the human has taken that up.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 36 known, 2 gone
11. factory: started review as vm.
12. reviewer: no findings

    What I reviewed: `git diff main...HEAD -- . ':!factory'` is empty (0 lines). The branch changes only this work item's `.md` and its new `.costs.jsonl` sidecar, both under `factory/`.
    1. Acceptance criteria: criterion 1 holds, because nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes. The tester (entry 5) and the coder (entry 10) each end with an entry that says so. Criterion 2: the journal records that the factory's `make check` after the coder ended `check: green` (entry 10). Criterion 3 is the docs criterion: the documenter writes it next, and the smoke test and `make documents` check it. The Interface states no rule, so there is no failing side to test.
    2 to 4. Architecture, security, quality: no code, so nothing to judge. `duplicates: 11 new` in entry 10 is not from this branch, since nothing under `src/factory` changed.
    5. Work item hygiene: the journal gives the main decision (hand on with no change, after the human's answer in entry 8) and what was rejected (touching the old acceptance reports or `.secrets.baseline`). The `## Description` matches what was built so far: nothing. The documenter's chapter and decision-log entry still lie ahead. The docs criterion still says what the reader must know.
    6. Earlier tests: the diff changes no test file.

    Open, and not this story's: the high-entropy values in the done acceptance reports of F0023 and F0042 that a full `make secrets` scan flags. The human took them up in entry 8.
13. factory: started docs as vm.
14. documenter: I wrote the chapter and the decision-log entry, and I stop with one question because the docs criterion and `vm/setup.sh` disagree.

    Question: the criterion for *The rebuild after a merge* says `vm/setup.sh` "carries over ... a changed `vm/factory.service` and a changed `image/git-credential-factory`" after every merge. The code does not do that. `vm/setup.sh` lines 316-322 and 361-367 install `/usr/local/bin/git-credential-factory` and `/etc/systemd/system/factory@.service` only in the run that cloned, or when the installed file is missing. A later run that finds a different file prints `setup: ...: differs from the checkout; not installed` to standard error and leaves the file. The existing *The two passes* section says the same (S0003 chose this deliberately, so that root does not install files from a checkout `factory` can write). I took the code as right and wrote the chapter to match: after a merge that changes either file, the operator removes the installed file and runs the script again. Options:
    (a) Keep the code; the criterion's wording is corrected. This is the option I would choose.
    (b) The coder changes `vm/setup.sh` to install a changed file on later runs. Root would then copy a file from `factory`'s checkout into `/usr/local/bin` and `/etc/systemd/system`, which gives the `factory` user a way to run code as root. I advise against it.
    If (b), the *The rebuild after a merge* paragraph on the script and the section *The two passes* change after the fix.

    Files changed:
    - `docs/operator-guide.md`: the chapter `## The machine` now has the eleven `###` sections in the required order. I added *What it is*, *On GCP, step by step* (12 numbered steps from the runbook's sections 1 to 3, plus the script's runs, the secrets, the build, the start and the stop), *On any Ubuntu 24.04 VM*, *What the container can and cannot see*, *The costs*, *The metadata server*, *Where the logs are* and *The rebuild after a merge*. I replaced the chapter's opening sentence, and the opening paragraph of the guide, which called the machine's image "the usual way". The top list already named "The machine" before "The machine's image".
    - `docs/decisions.md`: I appended the section `## The factory runs on the host, and the stage image carries the tools alone` (2026-10-24, F0043). No other entry changed.
    - `README.md`: one added sentence naming `vm/setup.sh` and pointing to the chapter.

    Checks: the three smoke-test blocks give the eleven `###` lines, `8`, `1`, `1`, and `make documents` ends with `documents ok`. Every term the criterion lists for the chapter is present. I ran no `gcloud` command and did not run the chapter's examples: there is no GCP project or VM here. The commands are copied from the runbook, the criterion and `vm/setup.sh`. I ran no `make check`, because I changed only documents.

    Cross-read and found current: *The stage image*, *The script* (steps, options, exit statuses, environment file, `sudoers` fallback) and *The service* against `vm/Dockerfile`, `vm/setup.sh` and `vm/factory.service`; the environment-file table matches the script. The factory-log section's `stage environment:` line matches `src/factory/application/stage_environment.py`. `docs/project-guide/README.md` needs no change: no guide file names a chapter that moved.

    Open points:
    - The criterion cites "decision 10" for the empty `anthropic-api-key`. I wrote "decision 10 of the feature F0043" and did not read the feature's `feature.md`; check that this is the right reference.
    - The costs, the logs section and the container-limits sentence come from the plan and from `src/factory`. I took the NAT fee from the criterion and the runbook, and did not look it up.
    - I added `shred -u` for removing the secret copies; the criterion only says "the copy removed afterwards".

    Stale text noticed, not touched:
    - `README.md` line 12 still says "An instance runs in the container: see *The container: compose, entrypoint and health check*". That is v1.1's way and F0044 removes it.
    - `vm/Dockerfile` has a comment line with `podman build -f vm/Dockerfile -t <FACTORY_STAGE_IMAGE> .`. The build context there is the repository root, which is correct, but the chapter uses `/srv/factory/vm/factory`, the same thing.
15. 2026-10-25 human: (a). The code is right: S0003 decided that root installs the unit and the credential helper only in the run that cloned or when the file is missing, so that root never installs a file from a checkout `factory` can write. Read the criterion's *The rebuild after a merge* as: after a merge that changes `vm/factory.service` or `image/git-credential-factory`, the operator removes the installed file and runs the script again, as you wrote. Keep the chapter as it is. Decision 10 of F0043's `feature.md` is the right reference for the empty `anthropic-api-key`; `shred -u` for the secret copies is fine. Then end with `smoke-test`.
