---
stage: doing
pr: 124
blocked: null
comments_seen: 2
round: 1
attempts: 0
---
# The pinned image

## Assignment (as of log entry 1)

Write the machine's image so that nothing in its build floats, and record on every cost record which image the agent run ran on. The Dockerfile pins the base image by digest, Claude Code by exact version (installed from its npm package, with its auto-update off), every Debian package that is a tool by exact version, `uv` by exact version, and installs the factory's own dependencies from `uv.lock` alone. The image's identity is a fresh id that the build generates and writes to `/opt/factory/image-id` (the human's decision of 2026-10-14: a build argument could be reused by a rebuild and keep a stale preflight stamp valid, ST4.3); the settings read the identity from that file (the first story of this feature builds the reader), and the build argument `FACTORY_IMAGE` is only a label. The Dockerfile also creates the two operating-system users and the shared directories that later stories rely on, with the modes the human decided: `/state` stays `0755` for the factory's user, and the files the agent must read go to a separate directory `/state/runs` (`2750`, group `factory-work`) that the agent can read but not write. This covers ST5.1 (as a static check of the build files), ST5.2, ST5.4 and SI3.3 and implements R29 and R4 for the image. A real image build needs Docker, which v1's container does not have, so ST5.1 and the build itself are a morning observation. The digest of the base image and the Debian package versions cannot be looked up without a network: the Dockerfile carries the placeholders given below, which have the right form and make the check pass, and the human replaces them before the first build. The Dockerfile copies files that later stories of this feature create (`image/entrypoint.sh`, `claude/`, `template/`); the build is only meaningful once they exist. The build backend is pinned too, but `pyproject.toml` lies outside the coder's write paths: the human changed it on `main` in a commit of their own to `requires = ["hatchling==1.32.4"]` (the version uv resolved, finding 22 of the first round, answered "as recommended" on 2026-10-14), and criterion 21 checks the result.

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
2. intake: accepted
   - Interface: `image/Dockerfile` is given in full, in order. `floating_references(dockerfile: str) -> list[str]` has its signature and a rule list. `CostRecorder.begin` is named with `boundaries.settings.image`, which exists (`Settings.image: str | None`, and `CostRecord.image` in `domain/cost_records.py`).
   - Criteria: criteria 2 and 3 are table cases, one per row. Each rule has its failing side (criterion 2) and its accepted side (criterion 3). The `image` rules have both sides too: set (18) and `None`, or no settings (19). Criterion 10 compares three values. Criteria 4 to 17 and 20 to 21 are static checks of the Dockerfile, `pyproject.toml` or `template/`. Each can be written as one test function.
   - Demo: all three commands are runnable. Each `Expect:` line is checkable: `True` and `True`, `True`, and `37`.
   - Architecture: `costs.py` is in the application layer and reads the domain settings. `tests/test_image.py` is at the `tests/` root, which suits a file outside the layers. The test file for the cost image is separate from F0005's, as the story says.
   - Scope: the story sits inside "The pinned image" in `FEATURE.md`. It follows decisions 6, 7 and 8 and nothing in "Out of scope". The placeholders and the morning build observation are stated openly.
3. tester: Wrote a test for every acceptance criterion. The tests for the missing work are red on purpose: they are the coder's specification.

   Criterion → test:
   - criterion 1: tests/test_image.py::test_the_shipped_dockerfile_has_no_floating_reference
   - criterion 2: tests/test_image.py::test_a_floating_item_is_reported (parametrized, the 24 lines of the criterion)
   - criterion 3: tests/test_image.py::test_a_pinned_item_is_not_reported (parametrized, the 9 lines of the criterion)
   - criterion 4: tests/test_image.py::test_every_base_image_is_pinned_by_digest
   - criterion 5: tests/test_image.py::test_claude_code_is_installed_from_npm_at_the_pinned_version
   - criterion 6: tests/test_image.py::test_claude_code_does_not_update_itself
   - criterion 7: tests/test_image.py::test_every_debian_package_is_pinned_and_the_set_is_the_tools
   - criterion 8: tests/test_image.py::test_every_pip_requirement_is_pinned
   - criterion 9: tests/test_image.py::test_the_factory_is_installed_from_the_lockfile_after_it_is_copied
   - criterion 10: tests/test_image.py::test_installed_versions_equal_the_locked_and_pinned_ones (parametrized over pydantic, PyGithub, ruamel.yaml, python-frontmatter)
   - criterion 11: tests/test_image.py::test_the_image_build_argument_is_only_a_label
   - criterion 12: tests/test_image.py::test_the_image_identity_is_generated_after_the_last_copy_and_before_the_user
   - criterion 13: tests/test_image.py::test_the_pinned_claude_code_version_is_readable_at_run_time
   - criterion 14: tests/test_image.py::test_the_container_runs_as_the_factory_user_and_both_users_share_the_work_group
   - criterion 15: tests/test_image.py::test_the_state_directory_is_the_factory_users_alone
   - criterion 16: tests/test_image.py::test_the_runs_directory_is_readable_but_not_writable_by_the_work_group
   - criterion 17: tests/test_image.py::test_the_shared_directories_are_writable_by_the_work_group (parametrized: /work, /home/agent/.claude)
   - criterion 18: tests/application/test_cost_image.py::test_a_cost_record_names_the_image_of_the_settings_and_keeps_it_when_completed
   - criterion 19: tests/application/test_cost_image.py::test_a_cost_record_has_no_image_when_the_settings_name_none (parametrized: no settings, and settings with image=None)
   - criterion 20: tests/test_image.py::test_the_template_has_no_placeholder_files_and_no_tasks_directory
   - criterion 21: tests/test_image.py::test_the_build_backend_is_pinned
   - criteria 22 and 23 have no test: they are make check and the docs.

   Files created: tests/test_image.py and tests/application/test_cost_image.py.

   How the Dockerfile is checked:
   - `floating_references(dockerfile: str) -> list[str]` lives in tests/test_image.py, as the Interface says.
   - It joins continuation lines, drops comment lines and substitutes the ARG defaults.
   - It reads shell commands from RUN instructions and also from bare lines, because criterion 2 lists bare lines such as `apt-get install -y git` and `uv sync`.
   - It splits commands on `&&`, `||`, `;` and `|`.

   I checked every static test against the Dockerfile in the Interface. I copied it to a temporary file outside the repository and ran the tests on it. `floating_references` returned `[]` and every assertion held.

   How the cost record is checked (criteria 18 and 19):
   - The tests start a real stage on the fixtures with `replace(boundaries, settings=...)` and take `launched.started`, as F0005-S0008's tests do.
   - They call `CostRecorder(...).begin` and `complete` on it, and also check the record the launch itself wrote.

   Result of `make test`:
   - Nothing is missing at import time: the test runner imported every module.
   - Every test that reads `image/Dockerfile` errors in its fixture with `FileNotFoundError`, because the file does not exist yet.
   - Criterion 18's test fails because `image` is `None` instead of `build-7`.

   Three tests already pass:
   - criterion 20, because template/ does not exist yet;
   - criterion 21, because the human pinned hatchling==1.32.4 on main;
   - criterion 19, because `begin` never sets `image` today.

   Against this stage's rules, I ran tests/application/test_cost_image.py a second time with `uv run pytest`, in the same command as `make test`. That command outran the two-minute foreground limit and went to the background; my wait loop on it was then stopped at its time limit. Neither changed anything here: both runs had already finished and their output was read.

   `make lint` is green. I skipped the type check, as this stage's skill says. Nothing is open.

   `make lint`: lint: green
   `make test`: ERROR tests/test_image.py::test_the_shared_directories_are_writable_by_the_work_group[/home/agent/.claude]
4. coder: Wrote the pinned image and put the image on every cost record. `make check` is green.

   What I built:
   - `image/Dockerfile`: the Interface's instructions, in its order, plus a few why-comments. They say that the digest and the Debian versions are placeholders and that `FACTORY_IMAGE` is only a label. They also explain the fresh id per build and why `/state` and `/state/runs` differ.
   - `src/factory/application/costs.py`: `CostRecorder.begin` now sets `image` from a private `_image()`. It returns `boundaries.settings.image`, or `None` when there are no settings. `_completed` already copies the record's fields, so a completed record keeps the image.

   Design decision: I put the settings lookup in a small private method on `CostRecorder`. The rejected alternative was an inline conditional expression in the `CostRecord(...)` call, which is harder to read.

   Refactor: I read my diff (51 lines over 2 files) and found nothing to change, so there is no refactor commit.

   Not touched:
   - The Dockerfile copies `claude/`, `template/` and `image/entrypoint.sh`, which later stories create. A real build needs them, and it needs the placeholder digest and the eight `0~unpinned` versions replaced. The build itself is the morning observation.
   - The docs criterion (23) is the documenter's.

   Commit: `ticket F0010-S0006: feat(image): pin the machine's image and record it on cost records`.

   `make check`: check: green
5. reviewer: one finding, in group 1 (acceptance criteria). I stopped there, so groups 2 to 5 were not checked.

   I read the whole diff (`image/Dockerfile`, `src/factory/application/costs.py`, `tests/test_image.py`, `tests/application/test_cost_image.py`) against the ticket:
   - The Dockerfile matches the Interface, instruction for instruction, in order. The only additions are why-comments.
   - `CostRecorder.begin` sets `image` from `boundaries.settings`, or `None` when there are no settings. `_completed` copies the record, so a completed record keeps the image.
   - Criteria 1 to 21 each have a test that checks what the criterion says.
   - The coder's entry reports `make check` green.

   Findings:
   1. `tests/test_image.py::test_a_floating_item_is_reported`: some limits the Interface states are tested on one side only, which CLAUDE.md (Tests) counts as a finding.
      - The base-image digest must be "`@sha256:` followed by 64 hexadecimal digits". The only refused case is a reference with no digest at all. Nothing tests a digest of 63 or 65 hex digits, or a 64-character digest that is not hex. A `DIGEST` loosened to `@sha256:\w+` would still pass every test.
      - Likewise, "three dot-separated numbers" (for `ARG CLAUDE_CODE_VERSION` and for the npm package) has its two-number side tested (`2.1`) but not its four-number side (for example `2.1.289.1`).
      - Fix: add rows to the parametrized test, for example `FROM python@sha256:` + `"a" * 63`, `FROM python@sha256:` + `"g" * 64`, `ARG CLAUDE_CODE_VERSION=2.1.289.1`, `npm install --global @anthropic-ai/claude-code@2.1.289.1`.
      - No criterion lists these rows, so this is a gap in the story's criterion 2, not a coder defect.
      - The coder may not edit tests (R9). This needs the human's go-ahead (as a `question`) before the tester adds the rows.

   Open: nothing else.
6. coder: coder (round 1): the one review finding is a gap in a test, so I cannot fix it (R9). I am asking before the tester changes anything.

   The finding: `tests/test_image.py::test_a_floating_item_is_reported` tests only one side of two limits the Interface states:
   - "`@sha256:` followed by 64 hexadecimal digits": nothing tests a digest that is too short, too long or not hex.
   - "three dot-separated numbers": `2.1` is tested, but four numbers is not.

   What I checked:
   - The patterns that `floating_references` uses are in the test file itself and are already anchored: `DIGEST = @sha256:[0-9a-f]{64}$`, `THREE_NUMBERS = ^\d+\.\d+\.\d+$`, `NPM_PINNED = @\d+\.\d+\.\d+$` (tests/test_image.py:16-18).
   - So the new rows would already pass. No production code changes, and there is nothing for me to commit this round.
   - The shipped `image/Dockerfile` and `src/factory/application/costs.py` stay as they were in 65c0b7c.

   Question: should the tester add these rows to `test_a_floating_item_is_reported`?
   - `FROM python@sha256:` + `"a" * 63`
   - `FROM python@sha256:` + `"a" * 65`
   - `FROM python@sha256:` + `"g" * 64`
   - `ARG CLAUDE_CODE_VERSION=2.1.289.1`
   - `npm install --global @anthropic-ai/claude-code@2.1.289.1`

   Options:
   - (a) Yes. Criterion 2 is then extended by these five rows. When your answer comes back, I end with `tests`, naming exactly this change.
   - (b) No. Criterion 2 stays as written, and the gap is accepted.

   I recommend (a). It is five table rows, it follows the CLAUDE.md rule that every stated limit is tested on both sides, and it closes the review finding.
7. human (pull request comment, 2026-10-16): (a): the tester adds exactly these five rows to `test_a_floating_item_is_reported` and criterion 2 is extended by them. End with `tests` and name exactly this change.
