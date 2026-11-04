# The stage image of every stage's containers, the tools alone; build: podman build -f vm/Dockerfile --build-arg AGENT_RUNTIME=<claude|opencode> -t <FACTORY_STAGE_IMAGE> .
# Every tool that shapes a result is pinned; Debian's packages follow the base image's release (docs/decisions.md).
ARG BASE_IMAGE=python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
ARG CLAUDE_CODE_VERSION=2.1.318
ARG OPENCODE_VERSION=1.19.5

# The install: the factory's Node and npm, which the final stage leaves behind.
FROM ${BASE_IMAGE} AS install
ARG AGENT_RUNTIME
ARG CLAUDE_CODE_VERSION
ARG OPENCODE_VERSION
# The factory's own Node, apart from any a project installs; both from nodejs.org's SHASUMS256.txt.
ARG NODE_VERSION=22.23.4
ARG NODE_SHA256=1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce
RUN case "${AGENT_RUNTIME}" in \
      claude) ;; \
      opencode) ;; \
      *) echo "AGENT_RUNTIME must be claude or opencode, not '${AGENT_RUNTIME}'" >&2; exit 1 ;; \
    esac
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates xz-utils
RUN curl -fsSL -o /tmp/node.tar.xz https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz \
 && echo "${NODE_SHA256}  /tmp/node.tar.xz" | sha256sum -c - \
 && mkdir -p /opt/factory/node \
 && tar -xJf /tmp/node.tar.xz -C /opt/factory/node --strip-components=1 \
 && rm /tmp/node.tar.xz
# npm and the runtime's install script find node through the PATH, for this step alone.
RUN case "${AGENT_RUNTIME}" in \
      claude) package=@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} ;; \
      opencode) package=opencode-ai@${OPENCODE_VERSION} ;; \
    esac \
 && export PATH=/opt/factory/node/bin:${PATH} \
 && /opt/factory/node/bin/npm install --global --prefix /opt/factory --no-audit --no-fund "${package}"
# The runtime is one native executable: the final stage takes it alone, without the other CPU build beside it.
RUN mkdir -p /opt/runtime \
 && cp "$(readlink -f /opt/factory/bin/${AGENT_RUNTIME})" /opt/runtime/${AGENT_RUNTIME}

FROM ${BASE_IMAGE}
ARG AGENT_RUNTIME
ARG CLAUDE_CODE_VERSION
ARG OPENCODE_VERSION
ARG UV_VERSION=0.9.2
# Only a label: the settings read the image's identity from a file the operator renews.
ARG FACTORY_IMAGE=unlabelled
LABEL factory.image="${FACTORY_IMAGE}"
RUN apt-get update \
 && apt-get install -y --no-install-recommends git make curl ca-certificates procps xz-utils \
 && pip install --no-cache-dir uv==${UV_VERSION} \
 && rm -rf /var/lib/apt/lists/* /var/cache/debconf/*-old /var/log/*.log /var/log/apt/* /tmp/*
COPY --from=install /opt/runtime/${AGENT_RUNTIME} /opt/factory/bin/${AGENT_RUNTIME}
# The command execs the native executable; the image has none for the other runtime.
RUN case "${AGENT_RUNTIME}" in \
      claude) printf '#!/bin/sh\nexec /opt/factory/bin/claude "$@"\n' > /usr/local/bin/claude ;; \
      opencode) printf '#!/bin/sh\nexec /opt/factory/bin/opencode "$@"\n' > /usr/local/bin/opencode ;; \
    esac \
 && chmod 0755 /usr/local/bin/${AGENT_RUNTIME}
# The agent files, read-only; the sync container copies them into the dataset's home.
COPY claude /etc/factory/claude
RUN chmod 0755 /etc/factory/claude /etc/factory/claude/agents && find /etc/factory/claude -type f -exec chmod 0644 {} +
ENV UV_LINK_MODE=copy
ENV PYTHONDONTWRITEBYTECODE=1
ENV DISABLE_AUTOUPDATER=1
# The versions the preflight compares with what the installed runtime reports.
ENV FACTORY_CLAUDE_VERSION=${CLAUDE_CODE_VERSION}
ENV FACTORY_OPENCODE_VERSION=${OPENCODE_VERSION}
# opencode's provider/model ids for the model aliases the agent files name.
ENV FACTORY_OPENCODE_MODELS=opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5
