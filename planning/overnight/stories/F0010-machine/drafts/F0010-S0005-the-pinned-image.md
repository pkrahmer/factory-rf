# The pinned image

## Assignment (as of log entry 1)

Write the machine's image so that nothing in its build floats, and record on every cost record which image the agent run ran on. The Dockerfile pins the base image by digest, Claude Code by exact version (installed from its npm package, with its auto-update off), every Debian package that is a tool by exact version, `uv` by exact version, and installs the factory's own dependencies from `uv.lock` alone. The image's identity is a fresh id that the build generates and writes to `/opt/factory/image-id` (the human's decision of 2026-10-14: a build argument could be reused by a rebuild and keep a stale preflight stamp valid, ST4.3); the settings read the identity from that file (the first story of this feature builds the reader), and the build argument `FACTORY_IMAGE` is only a label. The Dockerfile also creates the two operating-system users and the shared directories that later stories rely on, with the modes the human decided: `/state` stays `0755` for the factory's user, and the files the agent must read go to a separate directory `/state/runs` (`2750`, group `factory-work`) that the agent can read but not write. This covers ST5.1 (as a static check of the build files), ST5.2, ST5.4 and SI3.3 and implements R29 and R4 for the image. A real image build needs Docker, which v1's container does not have, so ST5.1 and the build itself are a morning observation. The digest of the base image and the Debian package versions cannot be looked up without a network: the Dockerfile carries the placeholders given below, which have the right form and make the check pass, and the human replaces them before the first build. The Dockerfile copies files that later stories of this feature create (`image/entrypoint.sh`, `claude/`, `template/`); the build is only meaningful once they exist. The build backend is pinned too, but `pyproject.toml` lies outside the coder's write paths: before F0010 starts, the human changes it in a commit of their own to `requires = ["hatchling==1.32.4"]` (the version uv resolved, finding 22 of the first round, answered "as recommended" on 2026-10-14), and criterion 21 checks the result.

## Interface

`image/Dockerfile` has these instructions, in this order (comment lines are allowed in the real file):

```dockerfile
ARG BASE_IMAGE=python:3.12-slim-bookworm@sha256:0000000000000000000000000000000000000000000000000000000000000000
FROM ${BASE_IMAGE}
ARG CLAUDE_CODE_VERSION=2.1.289
ARG UV_VERSION=0.9.2
ARG FACTORY_IMAGE=unlabelled
LABEL factory.image="${FACTORY_IMAGE}"
RUN apt-get update \
 && apt-get install -y --no-install-recommends git=0~unpinned make=0~unpinned curl=0~unpinned ca-certificates=0~unpinned procps=0~unpinned sudo=0~unpinned nodejs=0~unpinned npm=0~unpinned \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==${UV_VERSION}
RUN npm install --global --no-audit --no-fund @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}
RUN groupadd --gid 1000 factory \
 && groupadd --gid 1002 factory-work \
 && useradd --uid 1000 --gid factory-work --create-home --shell /bin/sh factory \
 && useradd --uid 1001 --gid factory-work --create-home --shell /bin/sh agent \
 && mkdir -p /work /state/runs /home/agent/.claude \
 && chown factory:factory /state \
 && chown factory:factory-work /work /state/runs \
 && chown agent:factory-work /home/agent/.claude \
 && chmod 0755 /state \
 && chmod 2750 /state/runs \
 && chmod 2775 /work /home/agent/.claude
WORKDIR /opt/factory
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
COPY claude ./claude
COPY template ./template
COPY image/entrypoint.sh ./entrypoint.sh
RUN sed -i 's/\r$//' entrypoint.sh && chmod 0755 entrypoint.sh
RUN cat /proc/sys/kernel/random/uuid > /opt/factory/image-id
ENV PATH=/opt/factory/.venv/bin:$PATH \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    DISABLE_AUTOUPDATER=1 \
    FACTORY_CLAUDE_VERSION=${CLAUDE_CODE_VERSION} \
    FACTORY_CLAUDE_HOME=/home/agent/.claude
USER factory
WORKDIR /work
ENTRYPOINT ["/opt/factory/entrypoint.sh"]
```

`src/factory/application/costs.py`: `CostRecorder.begin(started, role)` (F0005-S0008) sets the `image` of the `CostRecord` it creates to `boundaries.settings.image`, or to `None` when `boundaries.settings` is `None`. `_completed` keeps it, because it copies the record's fields.

What the checks of the build files treat as a floating reference (the check is a function `floating_references(dockerfile: str) -> list[str]` in `tests/test_image.py`, one finding per floating item):

- a `FROM` image reference, after the `ARG` defaults before the first `FROM` are substituted, without `@sha256:` followed by 64 hexadecimal digits (no tag at all, `latest` and a tag without digest included);
- an `ARG CLAUDE_CODE_VERSION` whose default is not three dot-separated numbers (`latest`, `stable`, `2.1`, empty);
- a package after `apt-get install` that is not written `name=version`, or whose version is `*`; `apt-get upgrade` and `apt-get dist-upgrade`;
- a requirement after `pip install` that is not written `name==version`;
- a package after `npm install` or `npm i` that does not end in `@` and three dot-separated numbers once the `ARG` defaults are substituted, and any use of `npx`;
- a download piped into a shell: `curl` or `wget` whose output goes to `sh` or `bash` (an installer fetched at build time floats);
- `uv tool install`, `pip install .`, and `uv sync` without `--frozen` or `--locked`;
- the word `latest` on any line that is not a comment.

Placeholders the human replaces before the first build: the digest of `BASE_IMAGE` (64 zeros) and the eight `0~unpinned` package versions. The Claude Code version `2.1.289` and the `uv` version `0.9.2` are the ones v1's last build used.

Tests: `tests/test_image.py` (reads `image/Dockerfile`, `pyproject.toml`, `uv.lock` and `template/` from the repository root), `tests/application/test_cost_image.py` (a file of its own: `tests/application/test_costs.py` is F0005's; it makes a real stage start on the fixtures as F0005-S0008's tests do, to get a `StartedStage`, and reads the record `CostRecorder.begin` and `complete` write).

## Acceptance criteria

1. `floating_references` of the shipped `image/Dockerfile` is the empty list (ST5.1, as a static check of the build files).
2. `floating_references` reports a finding for each of these floating items, one test case each: `FROM python:3.12-slim-bookworm`, `FROM python`, `FROM python:latest`, `ARG CLAUDE_CODE_VERSION=latest`, `ARG CLAUDE_CODE_VERSION=2.1`, `apt-get install -y git`, `apt-get install -y git=*`, `apt-get upgrade -y`, `pip install uv`, `pip install uv>=0.9`, `npm install --global @anthropic-ai/claude-code`, `npm install --global @anthropic-ai/claude-code@latest`, `npm install --global @anthropic-ai/claude-code@2.1`, `npx claude-code`, `RUN curl -fsSL https://example.invalid/install.sh | bash`, `RUN wget -qO- https://example.invalid/install.sh | sh`, `uv tool install /opt/factory`, `uv sync`, `apt-get dist-upgrade -y`, `npm i -g @anthropic-ai/claude-code`, `pip install .`, `ARG CLAUDE_CODE_VERSION=stable`, `ARG CLAUDE_CODE_VERSION=` and a line `RUN echo latest`.
3. `floating_references` reports nothing for the accepted side of each rule, one test case each: `FROM python:3.12-slim-bookworm@sha256:` followed by 64 `a`s, `ARG CLAUDE_CODE_VERSION=2.1.289`, `apt-get install -y git=1:2.39.5-0+deb12u2`, `pip install uv==0.9.2`, `npm install --global @anthropic-ai/claude-code@2.1.289`, `uv sync --frozen --no-dev`, `uv sync --locked --no-dev`, `RUN curl -fsSL https://example.invalid/file -o /opt/file` (a download that is not piped into a shell) and the comment line `# latest`.
4. Every `FROM` reference of the shipped Dockerfile, after the `ARG` defaults are substituted, ends in `@sha256:` and 64 hexadecimal digits (R29).
5. `CLAUDE_CODE_VERSION` has a default of three dot-separated numbers, and the Claude Code install command is `npm install` of `@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}`.
6. `ENV DISABLE_AUTOUPDATER=1` is set, so the pinned Claude Code does not update itself.
7. Every package of every `apt-get install` in the shipped Dockerfile is written `name=version` with a non-empty version, and the eight packages are exactly `git`, `make`, `curl`, `ca-certificates`, `procps`, `sudo`, `nodejs` and `npm`.
8. Every requirement after `pip install` in the shipped Dockerfile is written `name==version`.
9. The factory's own dependencies are installed by `uv sync --frozen --no-dev` after `pyproject.toml` and `uv.lock` are copied in (ST5.2).
10. For each production dependency of `pyproject.toml` (`pydantic`, `PyGithub`, `ruamel.yaml`, `python-frontmatter`), the version in `uv.lock` equals the version of the distribution installed in the test environment, and equals the `==` pin in `pyproject.toml` (ST5.2: the installed versions equal the locked ones).
11. `ARG FACTORY_IMAGE` has a default and is used by one `LABEL` only: no `ENV` copies it into the container, so the build argument is a label and not the identity.
12. The Dockerfile writes the image identity with `RUN cat /proc/sys/kernel/random/uuid > /opt/factory/image-id`, after the last `COPY` and before `USER factory`, so that every build that changes an earlier layer generates a new id (ST4.3, ST5.4).
13. `ENV FACTORY_CLAUDE_VERSION=${CLAUDE_CODE_VERSION}` is set, so the pinned version is readable at run time by the preflight.
14. The Dockerfile creates the user `factory` with uid 1000 and the user `agent` with uid 1001, both with the primary group `factory-work`, and its only `USER` instruction is `USER factory`, placed after the last `RUN` and `COPY` (the container does not run as root).
15. The Dockerfile makes `/state` mode `0755` and owned by `factory:factory`, so that the agent can read the health file, the log and the stamp but not write them (the human's decision of 2026-10-14; the group `factory` is created with gid 1000 and has no member).
16. The Dockerfile creates `/state/runs` with mode `2750`, owner `factory` and group `factory-work`, so that the agent can read the files of its run but not write them (the human's decision of 2026-10-14).
17. The Dockerfile makes `/work` and `/home/agent/.claude` mode `2775` and group `factory-work`.
18. A cost record created at the start of an agent run has `image == "build-7"` when the boundaries' settings carry that image, and a completed record keeps it (ST5.4).
19. A cost record created when the boundaries have no settings, or settings with `image=None`, has `image is None`, not an empty string.
20. No file named `.gitkeep` and no directory named `tasks` exists anywhere under `template/` (SI3.3); the check passes when `template/` does not exist yet.
21. Every requirement in `[build-system] requires` of `pyproject.toml` is written `name==version` (`hatchling==1.32.4`), so the build backend that `uv sync --frozen` builds the factory with does not float (R29).
22. make check stays green.
23. docs: `docs/operator-guide.md` explains how to build the image (the optional build argument `FACTORY_IMAGE` is a label; the identity is generated at build and kept in `/opt/factory/image-id`, so every rebuild invalidates the preflight stamp), that the digest and the eight package versions in `image/Dockerfile` are placeholders to replace before the first build and how to update any pin, that Claude Code is installed from its npm package at the pinned version and names the pinned version, 2.1.289, and that a maintenance feature after v1.1 updates it (questionnaire 1, Q21), and that a real build is the morning observation; `docs/decisions.md` records why every tool is pinned (R29), why the image identity is generated at build and not passed in, and why `/state` is read-only for the agent while `/state/runs` is readable by it.

## Demo

```bash
uv run python -c '
import re, pathlib
text = pathlib.Path("image/Dockerfile").read_text()
print(re.search(r"^ARG BASE_IMAGE=\S+@sha256:[0-9a-f]{64}\s*$", text, re.M) is not None)
print(re.findall(r"^FROM (\S+)", text, re.M) == ["${BASE_IMAGE}"])
'
```
Expect: two lines, `True` and `True`: the base image is a name with a digest and the only `FROM` uses it.

```bash
uv run python -c "
import tomllib, importlib.metadata as m
lock = tomllib.load(open('uv.lock', 'rb'))
locked = {p['name']: p['version'] for p in lock['package']}
print(all(m.version(n) == locked[n] for n in ('pydantic', 'pygithub', 'ruamel-yaml', 'python-frontmatter')))
"
```
Expect: one line, `True`: the installed versions equal the locked ones.

```bash
cat /proc/sys/kernel/random/uuid | wc -c
```
Expect: one line, `37`: the identity the Dockerfile writes is a 36-character uuid and a newline.

## Log (append only)

1. 2026-10-12 human: created.
