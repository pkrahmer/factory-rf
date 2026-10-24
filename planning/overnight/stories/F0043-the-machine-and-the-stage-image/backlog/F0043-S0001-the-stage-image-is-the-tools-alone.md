# The stage image is the tools alone

## Description

Every container of a v1.2 stage (the sync, the agent, the checks; `planning/v1.2-plan.md`, "The stage image") starts from one image that holds the tools and nothing of the factory: the pinned base image, git, make, curl, ca-certificates, procps, nodejs and npm at Debian's pinned versions, `uv`, Claude Code and opencode at the pinned versions, and the agent files (`claude/agents`, `claude/settings.json`) at `/etc/factory/claude`, read-only, which F0042's sync container copies into the dataset's `/work/home/.claude` before the base moves (this image only carries them). This story adds that image as `vm/Dockerfile`, with the label `factory.image` as today and the runtimes' environment as today (`DISABLE_AUTOUPDATER`, `UV_LINK_MODE`, `PYTHONDONTWRITEBYTECODE`, the two version records and the opencode model ids), and without everything that served the long-lived container: no second user and no group, no `sudo` and no `sudoers`, no entrypoint, no `/etc/gitconfig`, no `USER`, `WORKDIR`, `ENTRYPOINT` or `CMD`, no `/opt/factory`, no `COPY src`, no `uv sync`, no image-id file, no login or token paths. The image is built on the VM, as the user `factory`, with `podman build -f vm/Dockerfile -t <FACTORY_STAGE_IMAGE> .` from a checkout; nothing in this repository's checks builds it. The tests are of the kind `tests/test_image*.py` are today, on `vm/Dockerfile`, and they pin that the two Dockerfiles carry the same pins until F0044 (the layers go) removes `image/`. What stays: `image/Dockerfile`, `image/compose.yml`, `image/entrypoint.sh` and every test that pins them, unchanged.

## Interface

No module under `src/factory/` changes. The coder adds one file, `vm/Dockerfile` (the human's change 1 of `feature.md` makes `vm/*` a write path of the coder first).

`vm/Dockerfile`:

- One `FROM`, of `BASE_IMAGE`, whose default is the same reference with its `@sha256:` digest that `image/Dockerfile` names. Four build arguments with defaults, `CLAUDE_CODE_VERSION`, `OPENCODE_VERSION`, `UV_VERSION` (each three numbers) and `FACTORY_IMAGE=unlabelled`; `LABEL factory.image="${FACTORY_IMAGE}"`; `FACTORY_IMAGE` appears in the `ARG` and the `LABEL` only, never in an `ENV`.
- One `apt-get install` of exactly `git`, `make`, `curl`, `ca-certificates`, `procps`, `nodejs` and `npm`, each as `name=version` (no `sudo`), with `--no-install-recommends`, followed by the removal of `/var/lib/apt/lists`; one `pip install --no-cache-dir uv==${UV_VERSION}`; one `npm install --global --no-audit --no-fund @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}` and, after it, one `npm install --global --no-audit --no-fund opencode-ai@${OPENCODE_VERSION}`. `floating_references` of `tests/test_image.py` finds nothing in the file.
- `COPY claude /etc/factory/claude` without `--chown` and `--chmod`, followed directly by `RUN chmod 0755 /etc/factory/claude /etc/factory/claude/agents && find /etc/factory/claude -type f -exec chmod 0644 {} +`, with a comment directly above the `COPY` that says the sync container copies them into the dataset's home. No other `COPY`, and no `chown` anywhere in the file.
- Each `ENV` instruction sets one name on a line of its own (`ENV NAME=value`, the form `vm/setup.sh` of S0003 reads); `ENV` sets exactly `UV_LINK_MODE=copy`, `PYTHONDONTWRITEBYTECODE=1`, `DISABLE_AUTOUPDATER=1`, `FACTORY_CLAUDE_VERSION=${CLAUDE_CODE_VERSION}`, `FACTORY_OPENCODE_VERSION=${OPENCODE_VERSION}` and `FACTORY_OPENCODE_MODELS=<the value image/Dockerfile sets>`; no `PATH`, and no name that holds `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL`.
- The file holds none of the words `useradd`, `groupadd`, `sudo`, `sudoers`, `visudo`, `USER`, `WORKDIR`, `ENTRYPOINT`, `CMD`, `gitconfig`, `/opt/factory`, `src`, `pyproject.toml`, `uv.lock`, `uv sync`, `image-id`, `entrypoint`, `/home/agent`, `/home/factory`, `FACTORY_AGENT_USER`, `FACTORY_CLAUDE_HOME`, `FACTORY_TOKEN_FILE`, `FACTORY_CLAUDE_LOGIN_FILE`, `FACTORY_API_LOGIN_FILE`, `latest` outside a comment.
- The first line is a comment that names the image's purpose and the build command, `podman build -f vm/Dockerfile -t <FACTORY_STAGE_IMAGE> .`.
- The defaults of `BASE_IMAGE`, `CLAUDE_CODE_VERSION`, `OPENCODE_VERSION` and `UV_VERSION`, and the value of `FACTORY_OPENCODE_MODELS`, equal those of `image/Dockerfile`, read from both files by the test.

Tests (the tester writes them): `tests/test_stage_image.py` (and further `tests/test_stage_image*.py` modules at the tester's choice), reading `vm/Dockerfile` with the readers of `tests/test_image.py` (`floating_references`, the instruction, command, `ENV` and path-mode readers), which the tester may move into `tests/dockerfile_support.py` under the standing leave (decision 15 of `feature.md`); `tests/test_image*.py` keep their names and assertions. A test row that names a word the file must not hold reads the file with its comment lines dropped first.

## Acceptance criteria

1. `floating_references(<the text of vm/Dockerfile>)` is `[]`; the one `FROM` is `FROM ${BASE_IMAGE}`, after the `ARG BASE_IMAGE=` line, and its reference with that default substituted ends in `@sha256:` and 64 hexadecimal digits; and the file has exactly one `FROM`, one `LABEL` and one `COPY` instruction (rows of one parametrized test over the counts).
2. The pins agree: the `ARG` defaults of `BASE_IMAGE`, `CLAUDE_CODE_VERSION`, `OPENCODE_VERSION` and `UV_VERSION` in `vm/Dockerfile` equal the ones in `image/Dockerfile`, each of the three versions matches `^\d+\.\d+\.\d+$`, and the `ENV` value of `FACTORY_OPENCODE_MODELS` equals `image/Dockerfile`'s (rows of one parametrized test, one per name).
3. The Debian packages of the one `apt-get install` are exactly `git`, `make`, `curl`, `ca-certificates`, `procps`, `nodejs` and `npm`, each `name=version` with a version that is not `*` and equals the version `image/Dockerfile` pins for that package (rows of one parametrized test, one per package); `sudo` is not among them; the command holds `--no-install-recommends` and the same `RUN` removes `/var/lib/apt/lists`.
4. The installs (rows of one parametrized test): exactly one `pip install` and its one requirement is `uv==${UV_VERSION}` with `--no-cache-dir`; exactly one `npm install` of `@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}` and exactly one of `opencode-ai@${OPENCODE_VERSION}`, the opencode one after the Claude Code one, both with `--global --no-audit --no-fund`; no `npx`, no `uv sync`, no `uv tool install`.
5. The agent files: the one `COPY` is `COPY claude /etc/factory/claude` (no `--chown`, no `--chmod`), the instruction directly after it is `RUN chmod 0755 /etc/factory/claude /etc/factory/claude/agents && find /etc/factory/claude -type f -exec chmod 0644 {} +`, the line directly above the `COPY` is a comment, and the file holds no `chown`.
6. The environment (rows of one parametrized test): the `ENV` names are exactly `UV_LINK_MODE`, `PYTHONDONTWRITEBYTECODE`, `DISABLE_AUTOUPDATER`, `FACTORY_CLAUDE_VERSION`, `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS`, with `UV_LINK_MODE=copy`, `PYTHONDONTWRITEBYTECODE=1`, `DISABLE_AUTOUPDATER=1`, `FACTORY_CLAUDE_VERSION=${CLAUDE_CODE_VERSION}` and `FACTORY_OPENCODE_VERSION=${OPENCODE_VERSION}`; no `ENV` or `ARG` name holds `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL`; `FACTORY_IMAGE` has the default `unlabelled`, is used by the `LABEL factory.image="${FACTORY_IMAGE}"` and by no other instruction.
7. The absent words (rows of one parametrized test, one per word, over the file with comment lines dropped): none of `useradd`, `groupadd`, `sudo`, `sudoers`, `visudo`, `USER`, `WORKDIR`, `ENTRYPOINT`, `CMD`, `gitconfig`, `/opt/factory`, `src`, `pyproject.toml`, `uv.lock`, `image-id`, `entrypoint`, `/home/agent`, `/home/factory`, `FACTORY_AGENT_USER`, `FACTORY_CLAUDE_HOME`, `FACTORY_TOKEN_FILE`, `FACTORY_CLAUDE_LOGIN_FILE`, `FACTORY_API_LOGIN_FILE` and `latest` appears; and the first line of the file is a comment that holds `podman build -f vm/Dockerfile`.
8. The old image is untouched: `tests/test_image.py`, `tests/test_image_credentials.py`, `tests/test_image_gitconfig.py`, `tests/test_image_users.py`, `tests/test_opencode_image.py`, `tests/test_compose*.py` and `tests/test_entrypoint*.py` are unchanged in their names and assertions and green, and `image/Dockerfile`, `image/compose.yml` and `image/entrypoint.sh` are byte-for-byte as on `main` (the coder's entry says so; the reviewer checks the diff).
9. `make check` stays green.
10. docs: `docs/operator-guide.md` gains the chapter `## The machine` (placed before `## The machine's image`) with its first section `### The stage image`: what the image holds and what it does not (the list of the Description), where the agent files are and who copies them (F0042's sync container, decision 9 of `feature.md`), the build on the VM as the user `factory` (`podman build -f vm/Dockerfile -t <FACTORY_STAGE_IMAGE> <the checkout>`, with `--build-arg FACTORY_IMAGE=<ref>` for the label), that the label is not the identity: the settings read the identity from the file `FACTORY_IMAGE_ID_FILE` names, which the operator renews after every build (decision 6 of `feature.md`; S0003's documenter adds how `vm/setup.sh` makes that file), and how to update a pin (the same lines as *Update the pins* of `## The machine's image`, and that `tests/test_stage_image.py` holds the two files to the same pins until F0044); one sentence under `## The machine's image` saying that `vm/Dockerfile` is the stage image of v1.2 and `image/Dockerfile` the machine of v1.1 until F0044. `docs/project-guide/README.md`, *Shared test helpers*: the line of `dockerfile_support.py` names what it offers after this story (and any module the tester added). `docs/decisions.md`: none (S0004 writes the entry of the machine).

## Smoke test

```bash
grep -c '^FROM ' vm/Dockerfile; grep -cE '^(USER|WORKDIR|ENTRYPOINT|CMD) ' vm/Dockerfile || true; grep -v '^#' vm/Dockerfile | grep -cE 'sudo|/opt/factory|COPY src|uv sync|useradd|/home/agent' || true; sed -n '1p' vm/Dockerfile | grep -c 'podman build -f vm/Dockerfile'
```
Expect: four lines, `1`, `0`, `0`, `1`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
grep -E '^ARG (BASE_IMAGE|CLAUDE_CODE_VERSION|OPENCODE_VERSION|UV_VERSION)=' image/Dockerfile | sort > "$d/old"
grep -E '^ARG (BASE_IMAGE|CLAUDE_CODE_VERSION|OPENCODE_VERSION|UV_VERSION)=' vm/Dockerfile | sort > "$d/new"
cmp -s "$d/old" "$d/new" && echo same-pins; grep -c '^ARG ' "$d/new"
grep -E '^COPY ' vm/Dockerfile; grep -cE 'LABEL factory\.image="\$\{FACTORY_IMAGE\}"' vm/Dockerfile
```
Expect: four lines, `same-pins`, `4`, `COPY claude /etc/factory/claude`, `1`

```bash
uv run pytest tests/test_stage_image*.py tests/test_image.py tests/test_image_users.py tests/test_opencode_image.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

## Journal
