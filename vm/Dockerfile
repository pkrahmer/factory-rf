# The stage image of every stage's containers, the tools alone; build: podman build -f vm/Dockerfile -t <FACTORY_STAGE_IMAGE> .
# Every reference is pinned (docs/decisions.md), to the same pins as image/Dockerfile.
ARG BASE_IMAGE=python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
FROM ${BASE_IMAGE}
ARG CLAUDE_CODE_VERSION=2.1.296
ARG OPENCODE_VERSION=1.19.3
ARG UV_VERSION=0.9.2
# Only a label: the settings read the image's identity from a file the operator renews.
ARG FACTORY_IMAGE=unlabelled
LABEL factory.image="${FACTORY_IMAGE}"
RUN apt-get update \
 && apt-get install -y --no-install-recommends git=1:2.39.5-0+deb12u3 make=4.3-4.1 curl=7.88.1-10+deb12u15 ca-certificates=20250419~deb12u1 procps=2:4.0.2-3 nodejs=18.20.4+dfsg-1~deb12u3 npm=9.2.0~ds1-1 \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==${UV_VERSION}
RUN npm install --global --no-audit --no-fund @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}
RUN npm install --global --no-audit --no-fund opencode-ai@${OPENCODE_VERSION}
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
