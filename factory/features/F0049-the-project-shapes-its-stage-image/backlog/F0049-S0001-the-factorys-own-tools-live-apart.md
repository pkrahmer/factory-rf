# The factory's own tools live apart under /opt/factory, with a Node of their own

## Description

The stage image installs Debian's `nodejs` and `npm` (Node 18.20.4 on bookworm) and puts Claude Code and opencode into npm's global folder, so the agent runtimes run on whichever `node` comes first on the `PATH`. Claude Code 2.1.296 already asks for Node 22: every build of the image prints npm's `EBADENGINE` warning. And once a project adds its own layer (S0002), a project that installs another Node would change the factory's runtime with it. This story moves the factory's own tools apart. The image downloads Node 22, pinned by its version and its SHA-256, into `/opt/factory/node`, installs Claude Code and opencode with that Node under `/opt/factory`, and puts two small commands, `claude` and `opencode`, on the `PATH` that run the runtimes with the factory's Node by its full path, whatever `node` a project installs. The factory's Node itself is not on the `PATH`. Debian's `nodejs` and `npm` leave the image, so the base holds no Node for projects: a project that needs one brings its own (S0002). `uv`, git, make and Python stay where they are. How the factory calls the runtimes, and their versions, do not change.

## Interface

- `vm/Dockerfile`:
  - Two new pins, `ARG NODE_VERSION=22.<the current 22.x release>` and `ARG NODE_SHA256=<the SHA-256 of node-v<NODE_VERSION>-linux-x64.tar.xz>` from nodejs.org's `SHASUMS256.txt`, beside the existing pins.
  - The download of that archive with `curl`, checked with `sha256sum -c` before it is unpacked into `/opt/factory/node`; a mismatch fails the build. No download is piped into a shell.
  - Claude Code and opencode installed by `/opt/factory/node/bin/npm` with `--prefix /opt/factory`, at their existing pinned versions.
  - `/usr/local/bin/claude` and `/usr/local/bin/opencode`: each runs the runtime's installed command with `/opt/factory/node/bin/node` named by its full path, passing its arguments on unchanged. Nothing else of `/opt/factory` is on the `PATH`, and `/usr/local/bin/node` and `/usr/local/bin/npm` do not exist in the image.
  - The `apt-get install` line names `git`, `make`, `curl`, `ca-certificates`, `procps` and `xz-utils` (for the archive), and no longer `nodejs` and `npm`.
- `vm/setup.sh` and `vm/job-start.sh` read the new pins as they read the others, if they need them; the `ENV FACTORY_CLAUDE_VERSION` and `ENV FACTORY_OPENCODE_VERSION` lines stay.
- `tests/test_stage_image.py` (under the feature's leave): its rows follow the new package list, the two new pins and their form (a version `22.<n>.<n>`, a SHA-256 of 64 lowercase hex digits), the checked download, and the two commands.

## Acceptance criteria

1. `vm/Dockerfile` pins `NODE_VERSION` as `22.<n>.<n>` and `NODE_SHA256` as 64 lowercase hex digits; rows: the file as built, a version `20.1.0`, a version `22.1`, a checksum of 63 digits and one in upper case are each refused by the stage-image test.
2. The archive's download is checked with `sha256sum -c` against `NODE_SHA256` before it is unpacked, and no line pipes a download into a shell (`| sh`, `| bash`); the stage-image test refuses a Dockerfile in which either is broken.
3. The `apt-get install` line names exactly `git`, `make`, `curl`, `ca-certificates`, `procps` and `xz-utils`; a line with `nodejs` or `npm` added is refused.
4. Claude Code and opencode are installed by `/opt/factory/node/bin/npm` with `--prefix /opt/factory`, at the versions of `CLAUDE_CODE_VERSION` and `OPENCODE_VERSION`, and the Dockerfile creates `/usr/local/bin/claude` and `/usr/local/bin/opencode`, each naming `/opt/factory/node/bin/node`.
5. `make check` stays green. No test builds the image: the tests run inside a check container. The human builds it on the VM after the merge and checks that `claude --version` and `opencode --version` report the pinned versions, that `command -v node` finds nothing, and that the build prints no `EBADENGINE` warning.
6. docs: `docs/operator-guide.md`: in *The stage image*, the package list becomes six names, and one paragraph says that the agent runtimes run on a Node of their own under `/opt/factory`, pinned by version and checksum, that the image has no Node for projects, and how a Node pin is changed (both `ARG`s, from nodejs.org's `SHASUMS256.txt`). `docs/decisions.md`: one entry that the factory's tools live apart under `/opt/factory` with their own Node, why (Claude Code asks for Node 22, Debian has 18, and a project's layer must not change the runtime; feature decision 2), and that it supersedes the seven packages of "Debian's packages follow the base image's release" for `nodejs` and `npm`. `README.md` and the project guide: none.

## Smoke test

```bash
grep -cE '^ARG NODE_VERSION=22\.[0-9]+\.[0-9]+$' vm/Dockerfile
grep -cE '^ARG NODE_SHA256=[0-9a-f]{64}$' vm/Dockerfile
grep -c 'sha256sum -c' vm/Dockerfile
grep -cE 'install .*\b(nodejs|npm)\b' vm/Dockerfile
uv run pytest tests/test_stage_image.py 2>&1 | tail -1
```

Expect: `1`, `1`, `1`, `0`, then a line that ends in `passed` with no `failed`.

## Journal
