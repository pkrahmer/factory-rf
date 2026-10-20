# The factory's machine. Every reference is pinned (docs/decisions.md): the digest and the
# Debian package versions were read from the official image on 2026-10-17 (Debian 12.15).
ARG BASE_IMAGE=python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
FROM ${BASE_IMAGE}
ARG CLAUDE_CODE_VERSION=2.1.296
ARG OPENCODE_VERSION=1.19.3
ARG UV_VERSION=0.9.2
# Only a label: the image's identity is generated below.
ARG FACTORY_IMAGE=unlabelled
LABEL factory.image="${FACTORY_IMAGE}"
RUN apt-get update \
 && apt-get install -y --no-install-recommends git=1:2.39.5-0+deb12u3 make=4.3-4.1 curl=7.88.1-10+deb12u15 ca-certificates=20250419~deb12u1 procps=2:4.0.2-3 sudo=1.9.13p3-1+deb12u4 nodejs=18.20.4+dfsg-1~deb12u3 npm=9.2.0~ds1-1 \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==${UV_VERSION}
RUN npm install --global --no-audit --no-fund @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}
RUN npm install --global --no-audit --no-fund opencode-ai@${OPENCODE_VERSION}
# /state is the factory user's alone; the agent reads its run's files in /state/runs.
RUN groupadd --gid 1000 factory \
 && groupadd --gid 1002 factory-work \
 && useradd --uid 1000 --gid factory-work --create-home --shell /bin/sh factory \
 && useradd --uid 1001 --gid factory-work --create-home --shell /bin/sh agent \
 && mkdir -p /work /state/runs /home/agent/.claude /home/factory/.secrets \
 && chown factory:factory /state \
 && chown factory:factory /home/factory/.secrets \
 && chown factory:factory-work /work /state/runs \
 && chown factory:factory-work /home/agent/.claude \
 && chmod 0755 /state \
 && chmod 0700 /home/factory/.secrets \
 && chmod 2750 /state/runs \
 && chmod 2775 /work \
 && chmod 3775 /home/agent/.claude
# opencode makes its configuration folder in the agent's home on its first run and dies when the
# write guard refuses that; made here and read-only to the agent, so that no run can write what
# the next run reads. The folder above stays the agent's, for the folders of FACTORY_OPENCODE_FOLDERS.
RUN mkdir -p /home/agent/.config/opencode \
 && chown agent:factory-work /home/agent/.config \
 && chown factory:factory-work /home/agent/.config/opencode \
 && chmod 0755 /home/agent/.config /home/agent/.config/opencode
WORKDIR /opt/factory
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
COPY claude ./claude
COPY template ./template
COPY image/entrypoint.sh ./entrypoint.sh
RUN sed -i 's/\r$//' entrypoint.sh && chmod 0755 entrypoint.sh
COPY image/git-credential-factory /usr/local/bin/git-credential-factory
RUN sed -i 's/\r$//' /usr/local/bin/git-credential-factory && chmod 0755 /usr/local/bin/git-credential-factory
# The agent's git trusts the checkout the factory owns; the factory's git does not read this file.
COPY image/gitconfig /etc/gitconfig
RUN sed -i 's/\r$//' /etc/gitconfig && chmod 0644 /etc/gitconfig
# The token is a mounted file; only its path is set, in a folder only the factory's user can enter.
ENV FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token
# The factory's user may become the agent's user, so no agent can read the token.
COPY image/sudoers-factory-agent /etc/sudoers.d/factory-agent
RUN sed -i 's/\r$//' /etc/sudoers.d/factory-agent && chmod 0440 /etc/sudoers.d/factory-agent && visudo -cf /etc/sudoers.d/factory-agent
ENV FACTORY_AGENT_USER=agent
# The agent's login, a token from `claude setup-token` that Compose mounts; each agent run's shell reads it.
ENV FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token
# The agent's API key, which Compose mounts; each agent run's shell reads it, and an empty file is no key.
ENV FACTORY_API_LOGIN_FILE=/home/agent/.anthropic-api-key
# A fresh id per build, so a rebuild never keeps a stale preflight stamp valid.
RUN cat /proc/sys/kernel/random/uuid > /opt/factory/image-id
ENV PATH=/opt/factory/.venv/bin:$PATH \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    DISABLE_AUTOUPDATER=1 \
    FACTORY_CLAUDE_VERSION=${CLAUDE_CODE_VERSION} \
    FACTORY_CLAUDE_HOME=/home/agent/.claude
# The opencode version the preflight compares with what the installed opencode reports.
ENV FACTORY_OPENCODE_VERSION=${OPENCODE_VERSION}
# opencode's provider/model ids for the model aliases the agent files name.
ENV FACTORY_OPENCODE_MODELS=opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5
USER factory
WORKDIR /work
ENTRYPOINT ["/opt/factory/entrypoint.sh"]
