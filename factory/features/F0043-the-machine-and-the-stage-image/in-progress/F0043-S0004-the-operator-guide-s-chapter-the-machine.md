---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 434
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-10-25T06:48:50.696492Z'
  lease_duration: 60
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
