# The base image holds only the instance's runtime, with nothing left from its install

## Description

`vm/Dockerfile` installs both agent runtimes with the factory's Node, and everything that install used stays in the image: npm's download cache (441 MB), the Node itself (201 MB), and opencode's second, "baseline" executable (178 MB), next to the one opencode runs. An instance runs only the runtime `FACTORY_AGENT_RUNTIME` names. This story builds the base image for one runtime, named by the new build argument `AGENT_RUNTIME`, which has no default. The download of Node and the install of the runtime happen in a first build stage; the image takes from it only what the chosen runtime runs, so it holds no Node, no npm, no npm cache and no executable of the other runtime. The small cleanups of the remaining stages go too: apt's and debconf's caches, the install logs and anything left in `/tmp`. The pins move to Claude Code 2.1.318 and opencode 1.19.5 (feature decision 3). Both version settings stay in the image, as today, so that `vm/setup.sh` and `vm/job-start.sh` read them unchanged. How the factory calls a runtime does not change: `/usr/local/bin/<runtime>` execs the native executable, and the image has no command for the other runtime.

## Interface

- `vm/Dockerfile`:
  - `ARG AGENT_RUNTIME`, without a default; a build with an empty or unknown value fails with a message that names `AGENT_RUNTIME` and the two values.
  - A first build stage downloads and checks Node as today, and installs only the chosen runtime at its pinned version. The final stage copies only what that runtime runs; the coder decides what that is, and opencode's unused CPU build is not part of it.
  - The final stage holds no `/opt/factory/node`, no `node` or `npm` anywhere on the `PATH`, no `/root/.npm`, no other runtime, nothing in `/tmp`, and no apt lists.
  - `CLAUDE_CODE_VERSION=2.1.318`, `OPENCODE_VERSION=1.19.5`; the `ENV FACTORY_CLAUDE_VERSION` and `ENV FACTORY_OPENCODE_VERSION` lines and `FACTORY_OPENCODE_MODELS` stay.
  - The first line names the build command with `--build-arg AGENT_RUNTIME=<claude|opencode>`.
- `vm/job-start.sh`: its image build passes `--build-arg AGENT_RUNTIME=$FACTORY_AGENT_RUNTIME`.
- `vm/setup.sh` does not change.

## Acceptance criteria

1. The stage-image test refuses a Dockerfile in which `AGENT_RUNTIME` has a default, and one whose final stage takes Node, npm, npm's cache or the other runtime's install from the first stage.
2. The final stage installs no runtime by npm and runs no `npm`; only the first stage does, and it installs exactly one runtime, chosen by `AGENT_RUNTIME`, at its pinned version.
3. The pins are `CLAUDE_CODE_VERSION=2.1.318` and `OPENCODE_VERSION=1.19.5`; Node's pins do not change.
4. `vm/job-start.sh` builds with `--build-arg AGENT_RUNTIME=$FACTORY_AGENT_RUNTIME`; its test row shows the argument.
5. `make check` stays green. No test builds the image. The human builds it on factory-vm for each runtime and checks: the build without `AGENT_RUNTIME` fails with its message; with `claude`, `claude --version` reports 2.1.318, `command -v opencode node npm` finds nothing, and the image is under 0.7 GB; with `opencode`, `opencode --version` reports 1.19.5, `command -v claude node npm` finds nothing, and the image is under 0.6 GB; neither image has `/root/.npm` or `/opt/factory/node`; the preflight and its agent-run probe pass on the `claude` image.
6. docs: `docs/operator-guide.md`: in *The stage image*, the build command with `AGENT_RUNTIME`, that the image holds only that runtime and must match the instance's `FACTORY_AGENT_RUNTIME`, that a runtime change needs a rebuild and a new `image-id`, and the new pins. `docs/decisions.md`: one entry with feature decisions 1 and 2 and their reasons. `README.md` and the project guide: none.

## Smoke test

```bash
grep -cE '^ARG AGENT_RUNTIME$' vm/Dockerfile
grep -cE '^ARG CLAUDE_CODE_VERSION=2\.1\.318$|^ARG OPENCODE_VERSION=1\.19\.5$' vm/Dockerfile
grep -c 'AGENT_RUNTIME=\$FACTORY_AGENT_RUNTIME' vm/job-start.sh
uv run pytest tests/test_stage_image.py tests/test_vm_job_start.py 2>&1 | tail -1
```

Expect: `1`, `2`, `1`, then a line that ends in `passed` with no `failed`.

## Journal
