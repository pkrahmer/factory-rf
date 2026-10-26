# GCP trial at work, 2026-10-26: one page

The steps are the operator guide's `docs/operator-guide.md`, *The machine*, "On GCP, step by step". This page gives their order, the traps found on the local VM, and what to look at. It is a trial: one small story, then stop the VM.

## Before you start

- [ ] **A GCP project you may use**, with billing, and the budget alert (step 1) set before anything costs money. Expect about $120 a month at most, much less with the VM stopped.
- [ ] **A fine-grained GitHub token** for exactly the repository the trial runs on, with contents and pull requests (read and write). Not your full token.
- [ ] **The agent's login:** `claude setup-token` (subscription) or an API key. With the `claude` runtime and a token, the key file stays empty, but it must exist.
- [ ] **Which repository.** The instance works on and runs from the same repository (`--repository-url`). For the trial that is factory-rf, or a fork of it at work. It cannot point at an unrelated project yet.

## The order (the guide's steps)

1. Project, billing, budget (step 1).
2. Router and Cloud NAT (step 2): the VM has no external address.
3. Firewall: SSH from IAP's range only (step 3).
4. The data disk, 50 GB (step 4), then the VM without a service account (step 5).
5. **Copy `vm/setup.sh` with Unix line endings.** A Windows checkout gives CRLF, and the script stops with `set: Illegal option -`. Use `git show HEAD:vm/setup.sh > setup.sh` first, then `gcloud compute scp ... setup.sh factory-vm:` (step 6).
6. The script, first pass (step 7). It stops at `waiting for /home/factory/.secrets/hosting-token`, with status 0. That is expected.
7. The three secret files, made by hand on the VM, never pasted into a chat (step 8).
8. The script, second pass (step 9), the stage image (step 10), the start (step 11).

## What to look at after the start

- **The preflight** in `/srv/factory/vm/state/factory.log`: `podman`, `zfs`, and `agent-run-probe: the agent runs log in with ...`. A probe that fails at once usually means NAT or the login.
- **The health:** `factory-health` prints `healthy`, or one line per stop.
- **The board:** `factory-watch` (step 11). The first stage's line `stage environment: reset ... sync ... advance ... take ...` shows the timings; locally each was under 1 s.
- **The first `make sync` in the sync container** downloads Python packages through NAT; it is the slowest step the first time.

## Known risks

- **Files that end in zero bytes** (seen once on the local VM on 2026-10-25). The sign: `main_branch_failing` with lint or syntax errors that `main` does not have. Check the dataset's files against git (`git hash-object --no-filters` against `git ls-files -s` in `/srv/factory/vm/work/checkout`), repair with `rm .git/index; git reset --hard` as `factory`, then move `@base` (`zfs destroy tank/factory/vm@base; zfs snapshot tank/factory/vm@base`).
- **Node 18 in the stage image.** Claude Code asks for Node 22 or newer and prints `EBADENGINE`; it runs today, but an update may break it.
- **Not tried on GCP before:** NAT, IAP, the VM without a service account, the metadata server.

## F0046's options and the page-cache fix (added 2026-10-26, after F0046)

Put your own settings in `/srv/factory/<instance>/factory.local.env`; `vm/setup.sh` never writes it, and a value there wins over `factory.env` (if the script reports the unit "differs from the checkout; not installed", install `vm/factory.service` as `/etc/systemd/system/factory@.service` by hand and run `systemctl daemon-reload`). The operator guide's *A company's provider* and *Behind a proxy* give the details and an example provider file.

```
FACTORY_OPENCODE_PROVIDER_FILE=/home/factory/provider.json
FACTORY_OPENCODE_MODELS=opus=<id>/<model>,sonnet=<id>/<model>,haiku=<id>/<model>
HTTPS_PROXY=...
NO_PROXY=...
FACTORY_CONTAINER_ENV=HTTPS_PROXY,NO_PROXY
FACTORY_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
```

- The CA bundle must hold the public certificates and the company's: add the company CA to the VM's store (`update-ca-certificates`) and name the store's bundle, which also serves the factory's own git and GitHub calls.
- Run `setup.sh` with `--runtime opencode`. The key stays in `/home/factory/.secrets/anthropic-api-key`; the provider file names it as `"api_key_env": "ANTHROPIC_API_KEY"`.
- The page-cache fix (the zero-byte fault's cause: a page written through `mmap` survives `zfs rollback`) is built in since F0045-S0002: the reset drops the cache through `/usr/local/bin/factory-drop-caches`, which `vm/setup.sh`'s step `caches` installs with its sudoers rule. Nothing to do by hand.

## At the end

- [ ] Wait until `factory-watch` shows no work item held by `vm`, then `sudo systemctl stop factory@vm` on the VM, then `gcloud compute instances stop factory-vm --zone=europe-west3-a` (step 12). A stopped VM costs only its disks and NAT.
- [ ] Bring home: `factory.log`, `health.json`, the board's output, and anything that surprised you.
