# The stage image of every stage's containers, the tools alone; build: podman build -f vm/Dockerfile -t <FACTORY_STAGE_IMAGE> .
# Every tool that shapes a result is pinned; Debian's packages follow the base image's release (docs/decisions.md).
ARG BASE_IMAGE=python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
FROM ${BASE_IMAGE}
ARG CLAUDE_CODE_VERSION=2.1.296
ARG OPENCODE_VERSION=1.19.3
ARG UV_VERSION=0.9.2
# The factory's own Node, apart from any a project installs; both from nodejs.org's SHASUMS256.txt.
ARG NODE_VERSION=22.23.4
ARG NODE_SHA256=1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce
# Only a label: the settings read the image's identity from a file the operator renews.
ARG FACTORY_IMAGE=unlabelled
LABEL factory.image="${FACTORY_IMAGE}"
RUN apt-get update \
 && apt-get install -y --no-install-recommends git make curl ca-certificates procps xz-utils \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==${UV_VERSION}
RUN curl -fsSL -o /tmp/node.tar.xz https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz \
 && echo "${NODE_SHA256}  /tmp/node.tar.xz" | sha256sum -c - \
 && mkdir -p /opt/factory/node \
 && tar -xJf /tmp/node.tar.xz -C /opt/factory/node --strip-components=1 \
 && rm /tmp/node.tar.xz
# npm and the runtimes' install scripts find node through the PATH, for this step alone.
RUN export PATH=/opt/factory/node/bin:${PATH} \
 && /opt/factory/node/bin/npm install --global --prefix /opt/factory --no-audit --no-fund @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}
RUN export PATH=/opt/factory/node/bin:${PATH} \
 && /opt/factory/node/bin/npm install --global --prefix /opt/factory --no-audit --no-fund opencode-ai@${OPENCODE_VERSION}
# The runtimes are native executables: the factory's Node serves only the npm step, so the commands exec them directly.
RUN printf '#!/bin/sh\nexec /opt/factory/bin/claude "$@"\n' > /usr/local/bin/claude \
 && chmod 0755 /usr/local/bin/claude
RUN printf '#!/bin/sh\nexec /opt/factory/bin/opencode "$@"\n' > /usr/local/bin/opencode \
 && chmod 0755 /usr/local/bin/opencode
# The agent files, read-only; the sync container copies them into the dataset's home.
COPY claude /etc/factory/claude
RUN chmod 0755 /etc/factory/claude /etc/factory/claude/agents && find /etc/factory/claude -type f -exec chmod 0644 {} +
ENV UV_LINK_MODE=copy
ENV PYTHONDONTWRITEBYTECODE=1
ENV DISABLE_AUTOUPDATER=1
# The versions the preflight compares with what the installed runtimes report.
ENV FACTORY_CLAUDE_VERSION=${CLAUDE_CODE_VERSION}
ENV FACTORY_OPENCODE_VERSION=${OPENCODE_VERSION}
# opencode's provider/model ids for the model aliases the agent files name.
ENV FACTORY_OPENCODE_MODELS=opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5
