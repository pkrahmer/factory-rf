# The factory's machine. Every reference is pinned (docs/decisions.md): the
# digest and the Debian package versions are placeholders to replace before
# the first build.
ARG BASE_IMAGE=python:3.12-slim-bookworm@sha256:0000000000000000000000000000000000000000000000000000000000000000
FROM ${BASE_IMAGE}
ARG CLAUDE_CODE_VERSION=2.1.289
ARG UV_VERSION=0.9.2
# Only a label: the image's identity is generated below.
ARG FACTORY_IMAGE=unlabelled
LABEL factory.image="${FACTORY_IMAGE}"
RUN apt-get update \
 && apt-get install -y --no-install-recommends git=0~unpinned make=0~unpinned curl=0~unpinned ca-certificates=0~unpinned procps=0~unpinned sudo=0~unpinned nodejs=0~unpinned npm=0~unpinned \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==${UV_VERSION}
RUN npm install --global --no-audit --no-fund @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}
# /state is the factory user's alone; the agent reads its run's files in /state/runs.
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
COPY image/git-credential-factory /usr/local/bin/git-credential-factory
RUN sed -i 's/\r$//' /usr/local/bin/git-credential-factory && chmod 0755 /usr/local/bin/git-credential-factory
# The token is a mounted secret; only its path is set, and only the factory's user can read it.
ENV FACTORY_TOKEN_FILE=/run/secrets/hosting-token
# The factory's user may become the agent's user, so no agent can read the token.
COPY image/sudoers-factory-agent /etc/sudoers.d/factory-agent
RUN sed -i 's/\r$//' /etc/sudoers.d/factory-agent && chmod 0440 /etc/sudoers.d/factory-agent && visudo -cf /etc/sudoers.d/factory-agent
ENV FACTORY_AGENT_USER=agent
# A fresh id per build, so a rebuild never keeps a stale preflight stamp valid.
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
