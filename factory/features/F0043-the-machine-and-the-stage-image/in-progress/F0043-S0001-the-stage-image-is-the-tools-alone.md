---
stage: tests
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 430
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T23:40:50.646017Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T23:40:50.651792Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T23:41:10.937405Z'
  stage: intake
  run: 27856411ac394dd1b90cd1d595a1fb8a
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T23:41:30.922600Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T23:45:44.432262Z'
  stage: tests
  run: ebec7778843b414b897543179b9638ef
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T23:46:05.548953Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-24T23:49:08.758717Z'
  stage: doing
  run: 12225bd6eed24b8ca21a897153dbd148
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-24T23:49:29.431914Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-24T23:51:03.505628Z'
  stage: review
  run: ed3c85a95744421194735fafeff354e5
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-24T23:51:24.006921Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-24T23:51:44.210461Z'
  stage: doing
  run: 330ccc8a90b84620b9d8d968b7661606
---

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
6. The environment (rows of one parametrized test): the `ENV` names are exactly `UV_LINK_MODE`, `PYTHONDONTWRITEBYTECODE`, `DISABLE_AUTOUPDATER`, `FACTORY_CLAUDE_VERSION`, `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS`, with `UV_LINK_MODE=copy`, `PYTHONDONTWRITEBYTECODE=1`, `DISABLE_AUTOUPDATER=1`, `FACTORY_CLAUDE_VERSION=${CLAUDE_CODE_VERSION}` and `FACTORY_OPENCODE_VERSION=${OPENCODE_VERSION}`; no `ENV` or `ARG` name holds the word TOKEN, SECRET, PASSWORD or CREDENTIAL (upper case, as a part of the name); `FACTORY_IMAGE` has the default `unlabelled`, is used by the `LABEL factory.image="${FACTORY_IMAGE}"` and by no other instruction.
7. The absent words (rows of one parametrized test, one per word, over the file with comment lines dropped): none of `useradd`, `groupadd`, `sudo`, `sudoers`, `visudo`, `USER`, `WORKDIR`, `ENTRYPOINT`, `CMD`, `gitconfig`, `/opt/factory`, `src`, `pyproject.toml`, `uv.lock`, `image-id`, `entrypoint`, `/home/agent`, `/home/factory`, `FACTORY_AGENT_USER`, `FACTORY_CLAUDE_HOME`, `FACTORY_TOKEN_FILE`, `FACTORY_CLAUDE_LOGIN_FILE`, `FACTORY_API_LOGIN_FILE` and `latest` appears; and the first line of the file is a comment that holds `podman build -f vm/Dockerfile`.
8. The old image is untouched: `tests/test_image.py`, `tests/test_image_credentials.py`, `tests/test_image_gitconfig.py`, `tests/test_image_users.py`, `tests/test_opencode_image.py`, `tests/test_compose*.py` and `tests/test_entrypoint*.py` are unchanged in their names and assertions and green, and `image/Dockerfile`, `image/compose.yml` and `image/entrypoint.sh` are byte-for-byte as on `main` (the coder's entry says so; the reviewer checks the diff).
9. Each `ENV` instruction of `vm/Dockerfile` sets exactly one name, as `ENV NAME=value` on one line of the file with no continuation (the form S0003's `vm/setup.sh` reads): every line of the file that starts with `ENV ` holds one `NAME=value` pair after the keyword and does not end in `\`, and the number of `ENV` lines equals the number of `ENV` names (six).
10. `make check` stays green.
11. docs: `docs/operator-guide.md` gains the chapter `## The machine` (placed before `## The machine's image`) with its first section `### The stage image`: what the image holds and what it does not (the list of the Description), where the agent files are and who copies them (F0042's sync container, decision 9 of `feature.md`), the build on the VM as the user `factory` (`podman build -f vm/Dockerfile -t <FACTORY_STAGE_IMAGE> <the checkout>`, with `--build-arg FACTORY_IMAGE=<ref>` for the label), that the label is not the identity: the settings read the identity from the file `FACTORY_IMAGE_ID_FILE` names, which the operator renews after every build (decision 6 of `feature.md`; S0003's documenter adds how `vm/setup.sh` makes that file), and how to update a pin (the same lines as *Update the pins* of `## The machine's image`, and that `tests/test_stage_image.py` holds the two files to the same pins until F0044); one sentence under `## The machine's image` saying that `vm/Dockerfile` is the stage image of v1.2 and `image/Dockerfile` the machine of v1.1 until F0044. `docs/project-guide/README.md`, *Shared test helpers*: the line of `dockerfile_support.py` names what it offers after this story (and any module the tester added). `docs/decisions.md`: none (S0004 writes the entry of the machine).

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

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: concrete. It names one file, `vm/Dockerfile`, and states each instruction's form: the one FROM, the four ARGs, the apt, pip and npm installs, the COPY and chmod RUN, the six ENV names and values, the forbidden words, and the first-line comment. No `src/` module changes. `vm/*` is already in the coder's write paths in `factory/pipeline.yml`, so human change 1 is done.
   - Criteria: criteria 1 to 7 are each testable by one parametrized test function, and they cover every Interface clause. The pass and fail sides are both covered: the absent words, `sudo` not among the packages, `FACTORY_IMAGE` used only in the LABEL, the exact ENV set, and the pins equal to `image/Dockerfile`. Criterion 8 (old image untouched) is covered by the unchanged tests plus the reviewer's diff. Criteria 9 and 10 are the closing `make check` and `docs:` criteria, in the right order.
   - Smoke test: the commands are runnable with grep, sed, cmp and pytest. Each `Expect:` line is checkable against the output. The pytest command passes no `-q`, and `addopts` in `pyproject.toml` already sets `-q`, so the `N passed in` summary line exists as the Expect assumes.
   - Architecture: no layer is touched. The file lives under `vm/`, which the feature's change 1 makes a coder write path. The tests read the file as text, as `tests/test_image*.py` do. The shared readers move to `tests/dockerfile_support.py` only under the standing leave in CLAUDE.md and decision 15 of `feature.md`.
   - Scope: within `feature.md`'s S0001 scope. Nothing under `image/` changes, and no story step runs podman, apt or the like. Out-of-scope items are not touched.
4. factory: started tests as self.
5. tester: Wrote the tests for `vm/Dockerfile` in one new module, `tests/test_stage_image.py`. It reads the file with the readers `tests/test_image.py` already has (`floating_references`, `_instructions`, `_arg_defaults`, `_env`, `_commands`, `_after`, `_pipelines`, `_from_references`, `DIGEST`, `THREE_NUMBERS`, `DOCKERFILE`). Four earlier modules already import those readers from `test_image` the same way.

   - criterion 1: tests/test_stage_image.py::test_the_stage_image_has_no_floating_reference, ::test_the_one_base_image_is_the_pinned_build_argument, ::test_the_stage_image_has_one_instruction_of_each_kind[FROM|LABEL|COPY]
   - criterion 2: tests/test_stage_image.py::test_the_stage_image_carries_the_machine_images_pins[BASE_IMAGE|CLAUDE_CODE_VERSION|OPENCODE_VERSION|UV_VERSION|FACTORY_OPENCODE_MODELS]
   - criterion 3: tests/test_stage_image.py::test_each_debian_package_is_pinned_as_the_machine_image_pins_it[one row per package], ::test_the_one_apt_install_is_the_tools_without_recommends (exactly the seven packages, so no `sudo`; `--no-install-recommends`; the same RUN removes `/var/lib/apt/lists`)
   - criterion 4: tests/test_stage_image.py::test_each_tool_is_installed_once_at_its_pinned_version[uv|claude-code|opencode], ::test_opencode_is_installed_after_claude_code, ::test_no_other_install_is_made[npx|uv sync|uv tool install]
   - criterion 5: tests/test_stage_image.py::test_the_agent_files_are_copied_read_only_to_their_place
   - criterion 6: tests/test_stage_image.py::test_the_environment_names_are_the_runtimes_alone, ::test_each_runtime_setting_has_its_value[five rows], ::test_no_setting_or_build_argument_names_a_secret[TOKEN|SECRET|PASSWORD|CREDENTIAL], ::test_the_image_build_argument_is_only_the_label
   - criterion 7: tests/test_stage_image.py::test_nothing_of_the_long_lived_container_is_left[one row per word, comment lines dropped first, substring match], ::test_the_first_line_names_the_build_command
   - criterion 8: no new test. The existing `tests/test_image*.py`, `tests/test_opencode_image.py`, `tests/test_compose*.py` and `tests/test_entrypoint*.py` cover it, and the reviewer checks the diff. I changed no earlier test file.
   - criteria 9 and 10: `make check` and docs; not mine to test.

   Rejected: moving the readers into `tests/dockerfile_support.py` under the standing leave. The Interface makes the move optional. Making it would mean changing `test_image.py` and the four modules that import from it, because `mypy --strict` refuses implicit re-exports. So the documenter's line for `dockerfile_support.py` stays as it is (`dockerfile_instructions` only).

   Check before handing over: I ran a temporary copy of the module against a draft `vm/Dockerfile` written from the Interface, kept in `$TMPDIR`. All 62 cases passed, and I removed the copy afterwards.

   Run: `make test` fails as intended. Every case of `tests/test_stage_image.py` errors with `FileNotFoundError: ... /work/checkout/vm/Dockerfile`, because the file does not exist yet. No module failed to import (`test_image` imports fine). `make lint` is green.

   Files created: tests/test_stage_image.py.

   `lint`: lint: green (0.5 s)
   `test`: ERROR tests/test_stage_image.py::test_the_first_line_names_the_build_command - FileNotFoundError: [Errno 2] No such file or directory: '/work/checkout/vm/Dockerfile'
6. factory: started doing as self.
7. coder: Built `vm/Dockerfile`, the stage image, and nothing else. No module under `src/factory/` changed and no test changed. `image/Dockerfile`, `image/compose.yml` and `image/entrypoint.sh` are byte-for-byte as on `main`: `git diff main -- image` is empty.

   What the file does:
   - The first line is a comment that names the image's purpose and the build command `podman build -f vm/Dockerfile -t <FACTORY_STAGE_IMAGE> .`.
   - It has the same `BASE_IMAGE` default, with its digest, as `image/Dockerfile`. It also has the same `CLAUDE_CODE_VERSION`, `OPENCODE_VERSION` and `UV_VERSION` defaults, and the `ARG FACTORY_IMAGE=unlabelled` / `LABEL factory.image="${FACTORY_IMAGE}"` pair.
   - One `apt-get install` of the seven packages, at `image/Dockerfile`'s versions and without `sudo`.
   - The pip install of uv and the two npm installs, as in the machine image.
   - `COPY claude /etc/factory/claude`, with a comment directly above it, followed directly by the chmod/find `RUN` the Interface gives. `claude/` holds only the folder `agents`, so the two folder modes cover every folder.
   - Six `ENV` lines, one name each.

   Main choice: I wrote the file fresh from the Interface, so each `ENV` is on its own line, the form S0003's `vm/setup.sh` will read. I rejected copying `image/Dockerfile` and cutting it down: that would keep its multi-name `ENV` block and its comments about the long-lived container. I kept the explanatory comments that still hold: the label is not the identity, why the version records exist, and what the model ids are.

   Refactor: the diff is one new file that the tests pin line by line. Nothing needed changing.

   `make check` is green. `tests/test_stage_image.py` passes all 62 cases.

   Noticed, not touched: `vm/Dockerfile` repeats the seven Debian package versions of `image/Dockerfile` by hand. The pin tests keep the two files in agreement until F0044 removes `image/`. No other `vm/` file exists yet; S0003 adds `vm/setup.sh`.

   `check`: check: green
   `duplicates`: duplicates: 11 new, 36 known, 2 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`. It adds two files, `vm/Dockerfile` and `tests/test_stage_image.py`; nothing else changed. I read both against the Description, the Interface and every criterion.

   What holds:
   - `vm/Dockerfile` matches each Interface clause: one digest-pinned `FROM ${BASE_IMAGE}`, the pins of `image/Dockerfile`, the seven packages, the pip and npm installs, `COPY claude /etc/factory/claude` with the chmod RUN and a comment above it, six one-name `ENV` lines, none of the forbidden words, and the first-line build comment.
   - `image/` is untouched: the name-status lists no file under it.
   - Criteria 1 to 7 each have tests that check what the criterion says.
   - The coder's journal records `make check` green.

   Findings:
   1. criterion 9 added: it needs its test. The Interface's rule "Each `ENV` instruction sets one name on a line of its own" (the form S0003's `vm/setup.sh` reads) had no criterion and no test.
      - Why the current tests miss it: `_env` (tests/test_image.py:200) splits multi-name `ENV` instructions, so `test_the_environment_names_are_the_runtimes_alone` and `test_each_runtime_setting_has_its_value` (tests/test_stage_image.py:263-282) pass for `ENV UV_LINK_MODE=copy PYTHONDONTWRITEBYTECODE=1`, or for a `\`-continued `ENV`.
      - Fix: the tester writes the test for the new criterion 9. It checks the file's raw `ENV ` lines: one `NAME=value` pair each, no trailing `\`, and six lines for six names. Its refused side is rows of one parametrized test.
      - The closing criteria are renumbered to 10 (`make check`) and 11 (docs).
   2. tests/test_stage_image.py:285-293 copies existing code from tests/test_image_credentials.py:12-26:
      - the parametrize list `["TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"]` is a second copy of `SECRET_WORDS`;
      - the inline collection of `ENV` and `ARG` names is a second copy of `_declared_names`.
      - Fix: under the standing leave, the tester moves `SECRET_WORDS` and `_declared_names` into `tests/dockerfile_support.py`, has tests/test_image_credentials.py import them from there (its test keeps its name and assertions), and uses them in the new test.
   3. tests/test_stage_image.py:95-101: `_apt_packages` copies the package comprehension of `test_every_debian_package_is_pinned_and_the_set_is_the_tools` (tests/test_image.py:319-324).
      - Fix: under the standing leave, the tester moves `_apt_packages` to the shared readers (`tests/dockerfile_support.py`) and has that earlier test use it, keeping its name and assertions.
      - The same holds for `_uncommented` (tests/test_stage_image.py:86-87). It repeats the comment-dropping line of `_instructions` (tests/test_image.py:34) and of `dockerfile_instructions` (tests/dockerfile_support.py:12). Move it there too.
      - The docs criterion (now 11) already makes the documenter list what `dockerfile_support.py` offers.

   Rejected as findings:
   - `_pins` in the new module shares its name with `_pins()` in tests/test_image.py. It is a different, module-private function and is not imported.
   - `uv sync` is missing from criterion 7's list of words. Criterion 4's `test_no_other_install_is_made` pins it.
   - The duplicates record ("11 new") covers `src/factory`, which the diff does not touch.

   Earlier tests: none changed. The diff's only test file is the new `tests/test_stage_image.py` (status `A`).

   Next: the coder hands finding 1 to the tester (criterion 9 needs its test), and the tester makes the moves in findings 2 and 3 under the standing leave. `vm/Dockerfile` needs no change.
10. factory: started doing as self.
11. coder: Round 1: I changed no code and no test. Every finding of the review (entry 9) is a change to tests, so this round goes to the tester.

    - Finding 1, criterion 9, the one-name `ENV` lines: the criterion needs only its test. `vm/Dockerfile` already meets it. `grep '^ENV' vm/Dockerfile` shows six lines (20, 21, 22, 24, 25, 27), each holding one `NAME=value` pair, none ending in `\`. The tester writes the test for criterion 9: it reads the raw `ENV ` lines, checks one pair per line with no trailing `\`, and checks six lines for six names. The refused side is rows of one parametrized test.
    - Finding 2, the standing leave: the tester moves `SECRET_WORDS` and `_declared_names` from `tests/test_image_credentials.py` into `tests/dockerfile_support.py`. `tests/test_image_credentials.py` then imports them from there, and `tests/test_stage_image.py` uses them in `test_no_setting_or_build_argument_names_a_secret`.
    - Finding 3, the standing leave: the tester moves `_apt_packages` and `_uncommented` from `tests/test_stage_image.py` into `tests/dockerfile_support.py`.
      - `test_every_debian_package_is_pinned_and_the_set_is_the_tools` in `tests/test_image.py` then uses the shared `_apt_packages`.
      - The comment-dropping line in `_instructions` (`tests/test_image.py`) and in `dockerfile_instructions` uses the shared `_uncommented`.
      - Every earlier test keeps its name and assertions.

    The `## Description` is unchanged, because the journal did not change what the task means. Criterion 9 and the renumbered closing criteria (10 and 11) are already in the work item.

    `image/` is still byte-for-byte as on `main`. Refactor: nothing to change, because this round has no code diff. I did not run `make check`, since nothing changed since round 0, where it was green.
