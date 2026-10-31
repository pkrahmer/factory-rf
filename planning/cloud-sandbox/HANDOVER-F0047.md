# Hand-over: making the factory run in a managed cloud sandbox (F0047)

For the factory instance that builds this repository, and for the human who starts its stories. Written
2026-10-31. Read this first, then `factory/features/F0047-the-factory-runs-in-a-cloud-run-job/feature.md`
(goal, scope, decisions), then the story you are given. The evidence for every number is in this folder
(`capabilities.md`, `variants.md`, `recommendations.md`, `results/`); a story cites its probe as `P<n>`.

## What the work is

Run one factory instance inside a Cloud Run job where there is no ZFS, no rootless Podman, a memory-backed
root filesystem, no direct internet and a metadata server a container can reach. Seven stories, one at a
time, in this order; each is off by default so the VM path never changes:

| Story | Builds | Needs from an earlier story |
|---|---|---|
| S0001 | `CopySnapshots` (`FakeSnapshots` becomes its subclass) | none |
| S0002 | `FACTORY_CONTAINER_PROFILE=job` for `PodmanRuns` | none |
| S0003 | preflight item `metadata-block` | S0002 (the profile) |
| S0004 | token refresher `python -m factory.entry.refresh_token` | none |
| S0005 | `setup.sh --code-url`, credential helper host check | none |
| S0006 | `vm/job-start.sh` and the operator guide chapter | S0001 to S0005 |
| S0007 | opencode lockdown switches with a provider file | F0046 (merged) |

## Rules that bind this work

- **No company value anywhere in the repository**: no host name, project id, account, tenant, client id,
  token URL, proxy address or model catalogue. Tests and documents use `example.invalid`, made-up ids and
  `<placeholders>`. If a story seems to need one, end with `question`.
- **The factory cannot reach the cloud project and must not try.** No story, test or smoke test calls `gcloud`,
  a cloud API, a model API or a real token endpoint. Everything is tested with the fakes and stand-ins the
  suite already has (`FakeSnapshots`, `FakeContainerRuns`, the stand-in `podman`, injected `open_url`).
  Whether it works in the job is shown later by the human's probes, not by a stage.
- **`planning/` is read-only for every stage** (outside all write paths). Read it, never edit it.
- **No new dependency.** The refresher uses the standard library's `urllib`, which honours `https_proxy` and
  `no_proxy` from the environment.
- **Secrets**: the client secret and every token appear in no log line, error message, journal entry,
  test output or child environment. S0004 has a criterion that checks it.
- Everything else in `CLAUDE.md` applies (layers, `mypy --strict`, one wrapper per tool, the tests rules,
  `make check` in the foreground with the long timeout).

## Facts a stage would otherwise have to guess (all measured; the probe is in brackets)

- Podman 5.4 with **runc** (not crun: the cgroup layout is hybrid and crun refuses it), as root, on the host
  network, runs every flag the factory uses; `--timeout` ends a container with exit status **255**, which the
  adapter already reads as the time limit (P2, P3).
- Podman copies the job's proxy variables into containers unless `--http-proxy=false` is given (P2).
- `--userns=keep-id` fails as root; rootless is impossible (`NoNewPrivs`); slirp4netns and pasta need
  `/dev/net/tun`, which does not exist; the default bridge has no outbound path (P2, P2b).
- Podman's overlay storage needs `fuse-overlayfs` as mount program on this root (P2, P11).
- A container can read the job's token from the metadata server; a rule rejecting TCP port 80 to
  `169.254.169.254` stops it, and the chain must not be named `fwd` (a keyword in nft) (P2b).
- Copy of a 1 GiB tree of 20000 files: reset 1.6 s, diff 0.2 s with rsync (P4).
- The model API wants a bearer JWT from an OAuth2 client-credentials grant (form-encoded POST), valid
  about an hour; the stored client secret is not itself a bearer (P10).
- The API's internal host must be in `no_proxy`; through the proxy opencode hangs for over a minute (P10).
- opencode reports cost 0 without `cost` in the provider block; the catalogue's prices are dollars per
  million tokens (P10, P13).
- A small model sometimes writes `entry: <text>` on one line, which the strict result block parser refuses
  (`no_result`); this is the parser's rule, not something to change in these stories (P13).

## Where a stage is likely to stumble

- **S0001**: `FakeSnapshots` has six users in the tests. Moving its body to `CopySnapshots` must leave
  `tests/adapters/test_fake_snapshots.py` unchanged and green. Compare files in chunks of at most 1 MiB; do
  not read whole files.
- **S0002**: the global podman options come before the subcommand, for `run`, `--version` and `image exists`
  alike. The default profile's words must stay exactly as they are.
- **S0003**: curl prints `000` when it cannot connect; read the last non-blank line of the output, not the exit
  status.
- **S0004**: `urllib` raises `HTTPError` for a 4xx answer; its body holds the error and a description with
  carriage returns; cut it to one line and mask the secret in every message. Waits and the clock are injected,
  no test sleeps.
- **S0005**: the shell helper runs under `sh` (POSIX): no `[[`, no arrays. Host matching is case-insensitive
  and ignores port and user.
- **S0006**: a POSIX `sh` script tested with stand-in executables on `PATH` and two prefix variables
  (`FACTORY_JOB_ROOT`, `FACTORY_JOB_PREFIX`) so that no test writes outside `tmp_path`. The `nft` file must be
  written by the script and loaded with `-f`.
- **S0007**: only with a provider file; without one the configuration and environment are byte-identical.

## What the human does around the stories

- Moves one story at a time to `in-progress/`, reads the pull request, merges.
- After S0006, tries it in the real sandbox (the job, its secrets, its connector are the human's and the
  platform's; the operator guide's chapter *On Cloud Run*, written by S0006, lists what the job needs).
- Then re-runs the probe a finding depends on if the platform changed (the section *Reproducing a probe* of this folder's `README.md`).
- Runs the startup-contact probe for S0007 (what opencode contacts with the switches set), which is not a
  story.

## If you are unsure

End with `question` and say which of these you could not settle: a value that looks company-specific, a
behaviour only the real sandbox can show, a conflict with an earlier test, or a probe number that does not
match what you see. Do not guess a cloud behaviour: `capabilities.md` says what was measured and what was not
("untested" rows are untested).
