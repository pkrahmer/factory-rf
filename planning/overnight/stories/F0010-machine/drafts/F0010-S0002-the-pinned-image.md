# The pinned image

## Assignment (as of log entry 1)

Write the machine's image so that nothing in its build floats, and record on every cost record which image the agent run ran on. The Dockerfile pins the base image by digest, Claude Code by exact version with its auto-update off, every Debian package that is a tool by exact version, `uv` by exact version, and installs the factory's own dependencies from `uv.lock` alone. The build takes the image's identity as a build argument without a default and carries it into the container, where it is read as a setting and copied into each cost record. The Dockerfile also creates the two operating-system users and the shared directories that later stories rely on. This covers ST5.1 (as a static check of the build files), ST5.2, ST5.4 and SI3.3 and implements R29 and R4 for the image. A real image build needs Docker, which v1's container does not have, so ST5.1 and the build itself are a morning observation. The digest of the base image and the Debian package versions cannot be looked up without a network: the Dockerfile carries the placeholders given below, which have the right form and make the check pass, and the human replaces them before the first build. The Dockerfile copies files that later stories of this feature create (`image/entrypoint.sh`, `claude/`, `template/`); the build is only meaningful once they exist.

## Interface

`image/Dockerfile` has these instructions, in this order (comment lines are allowed in the real file):

```dockerfile
ARG BASE_IMAGE=python:3.12-slim-bookworm@sha256:0000000000000000000000000000000000000000000000000000000000000000
FROM ${BASE_IMAGE}
ARG CLAUDE_CODE_VERSION=2.1.289
ARG UV_VERSION=0.9.2
ARG FACTORY_IMAGE
RUN test -n "${FACTORY_IMAGE}"
RUN apt-get update \
 && apt-get install -y --no-install-recommends git=0~unpinned make=0~unpinned curl=0~unpinned ca-certificates=0~unpinned procps=0~unpinned sudo=0~unpinned \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==${UV_VERSION}
RUN groupadd --gid 1002 factory-work \
 && useradd --uid 1000 --gid factory-work --create-home --shell /bin/sh factory \
 && useradd --uid 1001 --gid factory-work --create-home --shell /bin/sh agent \
 && mkdir -p /work /state /home/agent/.claude \
 && chown factory:factory-work /work /state \
 && chown agent:factory-work /home/agent/.claude \
 && chmod 2775 /work /state /home/agent/.claude
RUN mkdir -p /opt/claude-code \
 && HOME=/opt/claude-code sh -c 'curl -fsSL https://claude.ai/install.sh | bash -s -- "${CLAUDE_CODE_VERSION}"' \
 && ln -s /opt/claude-code/.local/bin/claude /usr/local/bin/claude
WORKDIR /opt/factory
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
COPY claude ./claude
COPY template ./template
COPY image/entrypoint.sh ./entrypoint.sh
RUN sed -i 's/\r$//' entrypoint.sh && chmod 0755 entrypoint.sh
ENV PATH=/opt/factory/.venv/bin:$PATH \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    DISABLE_AUTOUPDATER=1 \
    FACTORY_IMAGE=${FACTORY_IMAGE} \
    FACTORY_CLAUDE_VERSION=${CLAUDE_CODE_VERSION} \
    FACTORY_CLAUDE_HOME=/home/agent/.claude
USER factory
WORKDIR /work
ENTRYPOINT ["/opt/factory/entrypoint.sh"]
```

`src/factory/domain/settings.py` (extends `InstanceSettings`)

```python
IMAGE_VARIABLE = "FACTORY_IMAGE"

class InstanceSettings(BaseModel):
    ...
    image: str | None = None                  # the value of FACTORY_IMAGE; unset or blank is None
```

`src/factory/application/boundaries.py` (extends `Boundaries`)

```python
@dataclass(frozen=True)
class Boundaries:
    ...
    settings: InstanceSettings | None = None  # last field, so existing constructions stay valid
```

`factory.entry.wiring.build_boundaries(settings)` passes `settings=settings` (wiring only: the real hosting client it builds needs a token and a network, so no test runs it). Wherever `factory.application.costs` builds the `CostRecord` of an agent run that starts, it sets `image` to `boundaries.settings.image`, or to `None` when `boundaries.settings` is `None`.

What the checks of the build files treat as a floating reference (the check is a function `floating_references(dockerfile: str) -> list[str]` in `tests/test_image.py`, one finding per floating item):

- a `FROM` image reference, after the `ARG` defaults before the first `FROM` are substituted, without `@sha256:` followed by 64 hexadecimal digits (no tag at all, `latest` and a tag without digest included);
- an `ARG CLAUDE_CODE_VERSION` whose default is not three dot-separated numbers (`latest`, `stable`, `2.1`, empty);
- a package after `apt-get install` that is not written `name=version`, or whose version is `*`; `apt-get upgrade` and `apt-get dist-upgrade`;
- a requirement after `pip install` that is not written `name==version`;
- `uv tool install`, `pip install .`, and `uv sync` without `--frozen` or `--locked`;
- the word `latest` on any line that is not a comment.

Placeholders the human replaces before the first build: the digest of `BASE_IMAGE` (64 zeros) and the six `0~unpinned` package versions. The Claude Code version `2.1.289` and the `uv` version `0.9.2` are the ones v1's last build used.

Tests: `tests/test_image.py` (reads `image/Dockerfile`, `pyproject.toml`, `uv.lock` and `template/` from the repository root), `tests/domain/test_settings.py`, `tests/application/test_boundaries.py`, `tests/application/test_costs.py`.

## Acceptance criteria

1. `floating_references` of the shipped `image/Dockerfile` is the empty list (ST5.1, as a static check of the build files).
2. `floating_references` reports a finding for each of these floating items, one test case each: `FROM python:3.12-slim-bookworm`, `FROM python`, `FROM python:latest`, `ARG CLAUDE_CODE_VERSION=latest`, `ARG CLAUDE_CODE_VERSION=2.1`, `apt-get install -y git`, `apt-get install -y git=*`, `apt-get upgrade -y`, `pip install uv`, `pip install uv>=0.9`, `uv tool install /opt/factory`, `uv sync`, and a line `RUN echo latest`.
3. Every `FROM` reference of the shipped Dockerfile, after the `ARG` defaults are substituted, ends in `@sha256:` and 64 hexadecimal digits (R29).
4. `CLAUDE_CODE_VERSION` has a default of three dot-separated numbers, and the Claude Code install command in the Dockerfile passes `${CLAUDE_CODE_VERSION}` to the installer.
5. `ENV DISABLE_AUTOUPDATER=1` is set, so the pinned Claude Code does not update itself.
6. Every package of every `apt-get install` in the shipped Dockerfile is written `name=version` with a non-empty version, and the six packages are exactly `git`, `make`, `curl`, `ca-certificates`, `procps` and `sudo`.
7. Every requirement after `pip install` in the shipped Dockerfile is written `name==version`.
8. The factory's own dependencies are installed by `uv sync --frozen --no-dev` after `pyproject.toml` and `uv.lock` are copied in (ST5.2).
9. For each production dependency of `pyproject.toml` (`pydantic`, `PyGithub`, `ruamel.yaml`, `python-frontmatter`), the version in `uv.lock` equals the version of the distribution installed in the test environment, and equals the `==` pin in `pyproject.toml` (ST5.2: the installed versions equal the locked ones).
10. `ARG FACTORY_IMAGE` has no default, `RUN test -n "${FACTORY_IMAGE}"` follows it, and `ENV` copies it into the container as `FACTORY_IMAGE`, so a build without an identity fails and the identity is readable at run time.
11. `ENV FACTORY_CLAUDE_VERSION=${CLAUDE_CODE_VERSION}` is set, so the pinned version is readable at run time by the preflight.
12. The Dockerfile creates the user `factory` with uid 1000 and the user `agent` with uid 1001, both in the group `factory-work`, makes `/work`, `/state` and `/home/agent/.claude` mode 2775 and group `factory-work`, and its only `USER` instruction is `USER factory`, placed after the last `RUN` and `COPY` (the container does not run as root).
13. `read_settings` gives `image == "build-7"` for `FACTORY_IMAGE=build-7`, and `image is None` when the variable is missing, empty or only spaces.
14. A `Boundaries` built without `settings` has `settings is None`, and `dataclasses.replace(boundaries, settings=settings)` returns a `Boundaries` holding those settings.
15. A cost record created at the start of an agent run has `image == "build-7"` when the boundaries' settings carry that image (ST5.4).
16. A cost record created when the boundaries have no settings, or settings with `image=None`, has `image is None`, not an empty string.
17. No file named `.gitkeep` and no directory named `tasks` exists anywhere under `template/` (SI3.3); the check passes when `template/` does not exist yet.
18. `make check` stays green.
19. docs: `docs/operator-guide.md` explains how to build the image (the `FACTORY_IMAGE` build argument), that the digest and the six package versions in `image/Dockerfile` are placeholders to replace before the first build and how to update any pin, and that a real build is the morning observation; `docs/decisions.md` records why every tool is pinned (R29) and why the image identity is a build argument without a default.

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
uv run python -c "
from factory.domain.settings import read_settings
base = {'FACTORY_REPOSITORY_URL': '/srv/project.git', 'FACTORY_INSTANCE': 'factory-1'}
print(read_settings(base).image, read_settings({**base, 'FACTORY_IMAGE': 'build-7'}).image)
"
```
Expect: one line, `None build-7`.

## Log (append only)

1. 2026-10-12 human: created.
