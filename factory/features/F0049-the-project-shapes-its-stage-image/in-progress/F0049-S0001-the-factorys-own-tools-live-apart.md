---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 526
comments_read: [6617813159, 6618142948]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T23:08:03.984617Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T23:08:03.991582Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-03T23:08:41.551828Z'
  stage: intake
  run: 719fab3b9e864bae8547bb92006006d6
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-03T23:09:30.682173Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-03T23:09:33.753676Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-03T23:09:55.267111Z'
  stage: intake
  run: 21ff42fc4d3848b086c69f439bafde48
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-03T23:10:01.221004Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-03T23:12:54.206398Z'
  stage: tests
  run: 7608e5a52b7e477d8e8d4e97f0486593
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-03T23:13:00.248970Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-03T23:17:35.189087Z'
  stage: doing
  run: fe3fd48e6b404b18b3706fc62ce65b16
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-03T23:17:41.379020Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-03T23:19:32.875013Z'
  stage: review
  run: 3466c01ca6d94bdd9b9795ed0a059712
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-03T23:19:38.752220Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-03T23:19:55.713639Z'
  stage: doing
  run: 95715bd6b25745028951cd3a2aa667e3
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-03T23:20:02.815485Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-03T23:20:47.749473Z'
  stage: tests
  run: 41fac88b478148e984794fb7a34c9c22
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-03T23:20:53.829779Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-03T23:24:23.159147Z'
  stage: doing
  run: 0578edd142c64b90978486eef9f81d01
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-03T23:24:29.321055Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-11-03T23:25:28.952186Z'
  stage: review
  run: 47c03b8530374815b8c2bd1649f9afd1
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-03T23:25:34.554016Z'
  stage: docs
- number: 22
  speaker: documenter
  kind: result
  at: '2026-11-03T23:26:10.279779Z'
  stage: docs
  run: 00be12f4a49d443991efa52fa64cfa0f
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-03T23:26:16.183485Z'
  stage: smoke-test
- number: 24
  speaker: smoke-tester
  kind: result
  at: '2026-11-03T23:26:48.253437Z'
  stage: smoke-test
  run: d0b7a6700b4a47e697d795e874566f01
- number: 25
  speaker: human
  kind: comment
  at: '2026-11-03T23:30:45.056244Z'
  stage: approval
- number: 26
  speaker: human
  kind: close
  at: '2026-11-03T23:30:45.056456Z'
  stage: approval
---

# The factory's own tools live apart under /opt/factory, with a Node of their own

## Description

The stage image installs Debian's `nodejs` and `npm` (Node 18.20.4 on bookworm) and puts Claude Code and opencode into npm's global folder, so the agent runtimes run on whichever `node` comes first on the `PATH`. Claude Code 2.1.296 already asks for Node 22: every build of the image prints npm's `EBADENGINE` warning. And once a project adds its own layer (S0002), a project that installs another Node would change the factory's runtime with it. This story moves the factory's own tools apart. The image downloads Node 22, pinned by its version and its SHA-256, into `/opt/factory/node`, installs Claude Code and opencode with that Node under `/opt/factory`, and puts two small commands, `claude` and `opencode`, on the `PATH` that run the runtimes with the factory's Node by its full path, whatever `node` a project installs. The factory's Node itself is not on the `PATH`. Debian's `nodejs` and `npm` leave the image, so the base holds no Node for projects: a project that needs one brings its own (S0002). `uv`, git, make and Python stay where they are. How the factory calls the runtimes, and their versions, do not change.

## Interface

- `vm/Dockerfile`:
  - Two new pins, `ARG NODE_VERSION=22.<the current 22.x release>` and `ARG NODE_SHA256=<the SHA-256 of node-v<NODE_VERSION>-linux-x64.tar.xz>` from nodejs.org's `SHASUMS256.txt`.
  - The download of that archive with `curl`, checked with `sha256sum -c` before it is unpacked into `/opt/factory/node`; a mismatch fails the build. No download is piped into a shell.
  - Claude Code and opencode installed by `/opt/factory/node/bin/npm` with `--prefix /opt/factory`, at their existing pinned versions.
  - `/usr/local/bin/claude` and `/usr/local/bin/opencode`: each runs the runtime's installed command with `/opt/factory/node/bin/node` named by its full path, passing its arguments on unchanged. Nothing else of `/opt/factory` is on the `PATH`, and `/usr/local/bin/node` and `/usr/local/bin/npm` do not exist in the image.
  - The `apt-get install` line names `git`, `make`, `curl`, `ca-certificates`, `procps` and `xz-utils` (for the archive), and no longer `nodejs` and `npm`.
- `vm/setup.sh` and `vm/job-start.sh` do not change; the `ENV FACTORY_CLAUDE_VERSION` and `ENV FACTORY_OPENCODE_VERSION` lines stay.
- `tests/test_stage_image.py` (under the feature's leave): its rows follow the new package list, the two new pins and their form (a version `22.<n>.<n>`, a SHA-256 of 64 lowercase hex digits), the checked download, and the two commands.

## Acceptance criteria

1. `vm/Dockerfile` pins `NODE_VERSION` as `22.<n>.<n>` and `NODE_SHA256` as 64 lowercase hex digits; rows: the file as built, a version `20.1.0`, a version `22.1`, a checksum of 63 digits and one in upper case are each refused by the stage-image test.
2. The archive's download is checked with `sha256sum -c` against `NODE_SHA256` before it is unpacked, and no line pipes a download into a shell (`| sh`, `| bash`); the archive is downloaded with `curl` and unpacked into `/opt/factory/node`; the stage-image test refuses a Dockerfile in which any of these is broken (rows: no `sha256sum -c`, a check after the unpack, a pipe into a shell, a download without `curl`, another unpack target).
3. The `apt-get install` line names exactly `git`, `make`, `curl`, `ca-certificates`, `procps` and `xz-utils`; a line with `nodejs` or `npm` added is refused.
4. Claude Code and opencode are installed by `/opt/factory/node/bin/npm` with `--prefix /opt/factory`, at the versions of `CLAUDE_CODE_VERSION` and `OPENCODE_VERSION`, and the Dockerfile creates `/usr/local/bin/claude` and `/usr/local/bin/opencode`, each naming `/opt/factory/node/bin/node` and passing its arguments on with `"$@"`; the stage-image test refuses a wrapper without `"$@"`.
5. The stage-image test refuses a Dockerfile that creates or links `node` or `npm` in `/usr/local/bin`, or that puts `/opt/factory` on an `ENV PATH` line.
6. `make check` stays green. No test builds the image: the tests run inside a check container. The human builds it on the VM after the merge and checks that `claude --version` and `opencode --version` report the pinned versions, that `command -v node` finds nothing, and that the build prints no `EBADENGINE` warning.
7. docs: `docs/operator-guide.md`: in *The stage image*, the package list becomes six names, and one paragraph says that the agent runtimes run on a Node of their own under `/opt/factory`, pinned by version and checksum, that the image has no Node for projects, and how a Node pin is changed (both `ARG`s, from nodejs.org's `SHASUMS256.txt`). `docs/decisions.md`: one entry that the factory's tools live apart under `/opt/factory` with their own Node, why (Claude Code asks for Node 22, Debian has 18, and a project's layer must not change the runtime; feature decision 2), and that it supersedes the seven packages of "Debian's packages follow the base image's release" for `nodejs` and `npm`. `README.md` and the project guide: none.

## Smoke test

```bash
grep -cE '^ARG NODE_VERSION=22\.[0-9]+\.[0-9]+$' vm/Dockerfile
grep -cE '^ARG NODE_SHA256=[0-9a-f]{64}$' vm/Dockerfile
grep -c 'sha256sum -c' vm/Dockerfile
grep -cE 'install .*\b(nodejs|npm)\b' vm/Dockerfile
uv run pytest tests/test_stage_image.py 2>&1 | tail -1
```

Expect: `1`, `1`, `1`, `0`, then a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: Questions (format check passed; no findings from it). The Interface states behaviours that have no criterion, so two coders could read them two ways and both pass:
   1. The Interface says each of `/usr/local/bin/claude` and `/usr/local/bin/opencode` passes its arguments on unchanged. Criterion 4 only checks that the commands exist and name `/opt/factory/node/bin/node`. Proposal: add to criterion 4 a row that refuses a wrapper that does not forward its arguments (for example, one with no `"$@"`).
   2. The Interface says `/usr/local/bin/node` and `/usr/local/bin/npm` do not exist and nothing else of `/opt/factory` is on the `PATH`. No criterion tests either. The smoke test greps only the `install` line, and the human's `command -v node` check in criterion 5 happens after the merge. Proposal: a criterion that the stage-image test refuses a Dockerfile that links or creates `node` or `npm` in `/usr/local/bin`, or that puts `/opt/factory` in an `ENV PATH` line.
   3. The Interface says the archive is unpacked into `/opt/factory/node` and that the download uses `curl`. Criterion 2 checks only the `sha256sum -c` ordering and that nothing is piped into a shell. Proposal: add rows for the unpack target and the `curl` download, or drop those clauses from the Interface.
   4. The Interface says `vm/setup.sh` and `vm/job-start.sh` read the new pins "if they need them". A coder cannot tell whether they need them, and no criterion covers it. Proposal: state that neither script changes, or name what each must read.
   5. The Interface says the two new `ARG`s sit "beside the existing pins". No criterion tests the placement. Proposal: drop the placement or accept that it is untested.
   I would choose the proposals in 1 and 2, and for 3 to add the two rows. For 4, state that neither script changes. For 5, drop the placement.

   The other checks found nothing:
   - The smoke test commands are runnable and each `Expect:` is checkable. The `pytest` line has no `-q`, which is right because `addopts` already sets one.
   - The architecture is fine: only `vm/` and `tests/test_stage_image.py` change.
   - The scope matches S0001 in `feature.md`, and the test change falls under the feature's leave for S0001.
4. 2026-11-03 human: Yes to all five, as you recommend: 1 and 2 become criteria (a wrapper without "$@" is refused; a Dockerfile that creates or links node or npm in /usr/local/bin, or puts /opt/factory on an ENV PATH line, is refused); 3 gets the two rows (the unpack target /opt/factory/node and the curl download); 4: neither vm/setup.sh nor vm/job-start.sh changes; 5: drop the placement.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) written into the story. They are the human's edit carried in, not mine.
   - Interface: concrete files and signatures: the `vm/Dockerfile` pins, `ARG`s, wrappers, `apt-get` line and `tests/test_stage_image.py`. Per entry 4 I wrote that `vm/setup.sh` and `vm/job-start.sh` do not change, and removed the "beside the existing pins" placement clause.
   - Criteria: each is testable by one parametrized test, and each rule has a refused side. Criterion 1 has the pin rows, criterion 2 the checksum order, the pipe into a shell, `curl` and the unpack target, criterion 3 the package list, and criterion 4 the `"$@"` row. Per entry 4 I added the `"$@"` row to criterion 4 and the `curl` and unpack-target rows to criterion 2. I added a new criterion 5: node or npm in `/usr/local/bin`, or `/opt/factory` on an `ENV PATH` line, is refused. The closing two are now 6 (`make check`) and 7 (`docs:`).
   - Smoke test: the commands are runnable. The pytest line has no `-q`, which is right because `addopts` already sets one. Each `Expect:` value is checkable against the output.
   - Architecture: only `vm/` and `tests/test_stage_image.py` change, and the docs criterion names `docs/operator-guide.md` and `docs/decisions.md`. This fits the layers.
   - Scope: this is S0001 of `feature.md`. The test change falls under the feature's leave for S0001, which covers the Debian package, Node and npm install rows and the places of `claude`, `opencode` and `uv`. Open: that leave names those rows only. The new pin-form, checksum, `curl`, wrapper and `PATH` rows are additions to the module. I read them as inside the leave's purpose ("to the image S0001 describes").
7. factory: started tests as vm.
8. tester: Wrote the tests for the stage image's own Node under /opt/factory. They are all in `tests/test_stage_image.py`, which I changed under the feature's leave. I created no new files.

   Criterion → test:
   - criterion 1: tests/test_stage_image.py::test_the_factory_node_is_pinned_by_version_and_checksum. Rows: the file as built, `20.1.0`, `22.1`, a checksum of 63 digits, and one in upper case.
   - criterion 2: tests/test_stage_image.py::test_the_node_archive_is_checked_before_it_is_unpacked. Rows: as built, no `sha256sum -c`, the check after the unpack, a pipe into a shell, a download without `curl`, and another unpack target.
     - The download is any command with a word holding `nodejs.org`, and its program must be `curl`.
     - The check is a `sha256sum -c` command whose RUN names `NODE_SHA256`. It must come before a `tar` command whose target word ends in `/opt/factory/node`.
   - criterion 3: tests/test_stage_image.py::test_the_apt_install_names_exactly_the_six_packages. Rows: as built, `nodejs` added, `npm` added. The changed `STAGE_PACKAGES` also drives the earlier tests `test_each_debian_package_is_installed_by_name_alone` and `test_the_one_apt_install_is_the_tools_without_recommends`.
   - criterion 4 (the installs): tests/test_stage_image.py::test_each_tool_is_installed_once_at_its_pinned_version (rows claude-code and opencode). These now expect `/opt/factory/node/bin/npm install` with `--prefix /opt/factory`, `--no-audit` and `--no-fund`, in place of `--global`. tests/test_stage_image.py::test_opencode_is_installed_after_claude_code now uses the same program.
   - criterion 4 (the two commands): tests/test_stage_image.py::test_each_runtime_command_runs_on_the_factory_node. It checks claude and opencode, each as built and with no `"$@"`. A RUN that names `/usr/local/bin/<name>` must name `/opt/factory/node/bin/node` and `"$@"`.
   - criterion 5: tests/test_stage_image.py::test_the_factory_node_stays_off_the_path. Rows: as built, an `ln -s` of node to `/usr/local/bin/node`, an `ln -s` of npm into `/usr/local/bin/`, an npm script created by `printf` in `/usr/local/bin/npm`, and `ENV PATH=/opt/factory/node/bin:${PATH}`.
   - criteria 6 and 7: no test. They are `make check` and docs.

   Other changes to the earlier rows of `tests/test_stage_image.py`, all for the image this story describes:
   - `/opt/factory` left `ABSENT_WORDS`.
   - The floating-reference row `eighth-package` is now `seventh-package`.
   - `test_the_stage_image_has_no_floating_reference` now changes the text it gives `floating_references`. It replaces `/opt/factory/node/bin/npm` with `npm`, and `--prefix /opt/factory` with `--prefix=_`. Without that, the shared helper in `tests/dockerfile_support.py` would miss npm called by its full path, so the opencode row would pass silently. It would also report `/opt/factory` as an unpinned npm package.
   - I left `tests/dockerfile_support.py` unchanged, because it is outside the feature's leave.

   Checks:
   - `uv run pytest -q tests/test_stage_image.py`: the new and changed rows for the as-built file fail, as they should. They fail on wrong results, not on import errors.
   - `make lint`: green.
   - Every module imported.

   I also wrote, outside the repository in a mktemp folder, a sample Dockerfile with the change applied: curl, `sha256sum -c`, `tar -C /opt/factory/node`, npm with `--prefix`, and printf wrappers. All 93 rows of the module passed against it, so a straightforward implementation can turn the suite green.

   Open, for the coder:
   - Each wrapper must be written by a RUN that names `/usr/local/bin/claude` or `/usr/local/bin/opencode` literally. A loop over the names would not satisfy the test.
   - The Node archive must be unpacked by `tar` straight into `/opt/factory/node`, not unpacked elsewhere and then moved.
   - The existing one-COPY rule still holds, so a `COPY <<EOF` heredoc cannot be used for the wrappers.

   `lint`: lint: green (0.2 s)
9. factory: started doing as vm.
10. coder: Built the image in `vm/Dockerfile`, the only file I changed. All rows of `tests/test_stage_image.py` pass and `make check` is green (ends with `check: green`). The image itself was not built (criterion 6: the human builds it on the VM after the merge).

    - Two new pins: `ARG NODE_VERSION=22.23.4` and `ARG NODE_SHA256=1805bcd3…e9ce`.
      - Both values come from `https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt` as it stood today (the line for `node-v22.23.4-linux-x64.tar.xz`).
      - I could not check the checksum against the archive itself: downloading the archive was refused in this stage. The human's build after the merge is the first real `sha256sum -c`.
    - The `apt-get install` line now names `git make curl ca-certificates procps xz-utils`; `nodejs` and `npm` are gone.
    - One RUN does the whole Node install:
      - downloads the archive with `curl -fsSL -o /tmp/node.tar.xz`;
      - checks it with `echo "${NODE_SHA256}  /tmp/node.tar.xz" | sha256sum -c -`;
      - then runs `mkdir -p /opt/factory/node`, unpacks with `tar -xJf … -C /opt/factory/node --strip-components=1`, and removes the archive.
    - Claude Code and opencode are installed by `/opt/factory/node/bin/npm install --global --prefix /opt/factory --no-audit --no-fund` at their existing pins, one RUN each, Claude Code first.
    - Each RUN for those installs starts with `export PATH=/opt/factory/node/bin:${PATH} &&`. npm's own shebang (`#!/usr/bin/env node`) and opencode's install script find `node` through the PATH, so without this the step fails. The export holds for that build step only; the image's `ENV` lines have no PATH.
    - `/usr/local/bin/claude` and `/usr/local/bin/opencode` are written by `printf` in a RUN of their own each, then `chmod 0755`.
      - Each runs `exec /opt/factory/node/bin/node /opt/factory/bin/<name> "$@"`.
      - Node follows the npm bin link to the package's entry script.
    - The `ENV FACTORY_*_VERSION` lines, `vm/setup.sh` and `vm/job-start.sh` are unchanged.

    Main choice: the commands start the runtimes through npm's bin links under `/opt/factory/bin`, called by `/opt/factory/node/bin/node`.
    - Rejected: naming each package's entry file (`lib/node_modules/@anthropic-ai/claude-code/cli.js`, `opencode-ai/bin/opencode`). That ties the commands to the inner layout of each package, which can change between versions.
    - Rejected: `--global` alone with `/opt/factory/bin` on the PATH. The Interface forbids it.
    - Kept `--global` beside `--prefix` so npm uses its standard `bin/` and `lib/node_modules/` layout under `/opt/factory` and not `/opt/factory/node_modules/.bin`; the tests allow either.

    Refactor: I read the diff once and found nothing to change.

    Noticed, not touched:
    - If a future Claude Code release ships its `claude` bin as a native binary and not a Node script, `node /opt/factory/bin/claude` would fail. The human's `claude --version` check after the build covers it.
    - The header comment's "Debian's packages follow the base image's release" still points at the decision entry the docs stage will update.
    - The journal changed nothing in the Description.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
11. factory: started review as vm.
12. reviewer: Review, round 0. I read the work item, the change to `vm/Dockerfile` and the change to `tests/test_stage_image.py`, and checked the tests against criteria 1 to 5 and the Interface. The Dockerfile does what the Interface asks:
    - Node 22 is pinned by version and SHA-256 and downloaded with `curl`.
    - `sha256sum -c -` runs before `tar -C /opt/factory/node`, and nothing is piped into a shell.
    - The `apt-get` line holds the six packages.
    - Both runtimes are installed by `/opt/factory/node/bin/npm --prefix /opt/factory`.
    - The `printf` wrappers start `/opt/factory/node/bin/node` with `"$@"`.
    - No `ENV PATH` line and nothing named `node` or `npm` is placed in `/usr/local/bin`. The `export PATH` lasts for its build step only.

    The coder's `make check` was green (entry 10). Architecture, security, quality and hygiene: nothing to report. Group 1 has three gaps. In each one the code handles the refused side correctly, but the rule is not a limit, so the missing row is a finding and not a note.

    1. tests/test_stage_image.py:540 (`test_each_runtime_command_runs_on_the_factory_node`): the helper requires that each wrapper exists and names `/opt/factory/node/bin/node` (Interface; criterion 4), but no row fails either check. The only refused row drops `"$@"`. Fix: add two rows expected `False`. `bare-node` replaces `/opt/factory/node/bin/node /opt/factory/bin/` with `node /opt/factory/bin/`. `no-command` drops the wrapper's `RUN`.
    2. tests/test_stage_image.py:254 (`test_each_tool_is_installed_once_at_its_pinned_version`): the Interface says the runtimes are installed by `/opt/factory/node/bin/npm` with `--prefix /opt/factory` (criterion 4), but the test only has rows for the file as built. Nothing shows that a bare `npm install` or another `--prefix` is refused. Fix: one parametrized test of the npm install with rows `as-built` (accepted), `bare-npm` (`/opt/factory/node/bin/npm` replaced by `npm`) and `other-prefix` (`--prefix /usr/local`), both refused.
    3. tests/test_stage_image.py:480 (`test_the_node_archive_is_checked_before_it_is_unpacked`): criterion 2 says the check runs "against `NODE_SHA256`", and `_node_archive_is_checked` tests that through `checked_runs`. But no row has a `sha256sum -c` that does not name `NODE_SHA256`. Fix: add a row expected `False` that replaces `${NODE_SHA256}` in the check with a literal low-entropy value (`"a" * 64`).

    Not raised:
    - The floating-reference test rewrites the npm path and the `--prefix` before it calls `floating_references`. That works around the shared helper in `tests/dockerfile_support.py`, which is outside the leave. The tester stated the reason, and the test still checks the npm pins.
    - The coder could not verify `NODE_SHA256` against the archive itself. That check is the human's build after the merge (criterion 6).
    - If a future release ships `/opt/factory/bin/claude` or `/opt/factory/bin/opencode` as something other than a Node script, the wrappers would fail. The Interface asks for exactly these wrappers, and the human's `--version` check after the build covers it.

    Earlier tests:
    - tests/test_stage_image.py: under the feature's leave for S0001 (feature.md, "A leave, for S0001"). Changed: the Debian package rows (`STAGE_PACKAGES`, the id `eighth-package` renamed `seventh-package`); the npm install rows (`NPM_FLAGS`, the `FACTORY_NPM` rows, the opencode-after-Claude-Code order); the place of the runtimes (`/opt/factory` taken out of `ABSENT_WORDS`); and the floating-reference test's rewrite of the npm path and the prefix, which keeps that test checking the npm pins. The new test functions are additions and need no leave.
13. factory: started doing as vm.
14. coder: Round 1: no code change. The reviewer's three findings (entry 12) each ask only for test rows, and the reviewer says `vm/Dockerfile` already handles each side those rows refuse. Under R9 the tester adds them; I did not touch the tests and did not run `make check`, because nothing changed.

    For the tester, the three changes, all in `tests/test_stage_image.py`:
    1. `test_each_runtime_command_runs_on_the_factory_node`: add two rows expected `False`.
       - `bare-node`: replace `/opt/factory/node/bin/node /opt/factory/bin/` with `node /opt/factory/bin/`.
       - `no-command`: drop the wrapper's `RUN`.
    2. A parametrized test of the npm install for both runtimes, with three rows:
       - `as-built`: accepted.
       - `bare-npm`: `/opt/factory/node/bin/npm` replaced by `npm`; refused.
       - `other-prefix`: `--prefix /usr/local`; refused.
    3. `test_the_node_archive_is_checked_before_it_is_unpacked`: add a row expected `False` in which the `sha256sum -c` check uses a literal low-entropy value (`"a" * 64`) instead of `${NODE_SHA256}`.

    Built: nothing new this round. `vm/Dockerfile` is as round 0 left it (entry 10).

    Main choice: end with `tests` and change no code. Rejected: adding to `vm/Dockerfile` to address the findings, since the code already refuses each side, and anything added would go beyond the description.

    Noticed, not touched:
    - Entry 10's open points still stand. `NODE_SHA256` is checked against the real archive only when the human builds the image. A runtime whose bin is not a Node script would break its wrapper.
    - The journal did not change the Description.
15. factory: started tests as vm.
16. tester: Approved test change, round 1. I added the three changes the coder named in entry 14 (from the reviewer's findings in entry 12). All of them are in `tests/test_stage_image.py`, the only file I changed. That file was already changed for this story under the feature's leave; the changes this round only add tests.

    1. `test_each_runtime_command_runs_on_the_factory_node` (criterion 4) has two new rows, both expected `False`, for `claude` and for `opencode`:
       - `bare-node`: `/opt/factory/node/bin/node /opt/factory/bin/` is replaced by `node /opt/factory/bin/`.
       - `no-command`: the wrappers' RUNs are dropped. A new helper, `_drop_lines_with`, drops the joined lines that write to `/usr/local/bin/`. A row's change does not know which name its test case checks, so it drops both wrappers; each name's check then fails on its own missing wrapper.
    2. `test_the_runtimes_are_installed_by_the_factory_npm_into_its_prefix` (criterion 4, Interface) is a new parametrized test over Claude Code and opencode, using a new helper `_installed_by_the_factory_npm`. Its rows:
       - `as-built`: accepted.
       - `bare-npm`: `/opt/factory/node/bin/npm` replaced by `npm`; refused.
       - `other-prefix`: `--prefix /usr/local`; refused.
    3. `test_the_node_archive_is_checked_before_it_is_unpacked` (criterion 2) has a new row, `literal-checksum`, expected `False`. In the `sha256sum -c` line, `${NODE_SHA256}` is replaced by `"a" * 64`.

    `uv run pytest -q tests/test_stage_image.py` passes in full (104 tests). That is expected: the reviewer said `vm/Dockerfile` already refuses every side these rows add, so they pin behaviour that already holds and are not red. `make lint`: lint: green. Every test module imported.

    Files created: none.

    `lint`: lint: green (0.1 s)
17. factory: started doing as vm.
18. coder: Round 1, after the tester's added rows (entry 16): no code change. `vm/Dockerfile` stays as round 0 left it (entry 10). The rows the tester added for the reviewer's three findings (entry 12) test behaviour that `vm/Dockerfile` already has. Those rows are the bare-node and no-command wrapper rows, the npm install test's bare-npm and other-prefix rows, and the literal-checksum row.

    I ran `make check` on the committed tree with the new tests, and it ended with `check: green`.

    Built: nothing new this round. The paths are the same as in round 0: `vm/Dockerfile`.

    Main choice: change no code and send the work item to review. The alternative I rejected was touching `vm/Dockerfile` to make the new rows "count": they pass against the file as it is, and any change would go beyond the description.

    Refactor: there is no diff of mine this round, so there was nothing to change.

    Noticed, not touched (still open from entry 10):
    - `NODE_SHA256` is first checked against the real archive when the human builds the image after the merge.
    - A future runtime release whose bin is not a Node script would break its wrapper. The human's `--version` check after the build would show it.

    The journal did not change the Description.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
19. factory: started review as vm.
20. reviewer: Review, round 1. No findings, so the story passes to docs.

    I read the work item, the diff stat and the diff of `vm/Dockerfile` and `tests/test_stage_image.py`. I also read the helpers the tests use in `tests/dockerfile_support.py`.

    **Criteria 1 to 5:** each one now has a parametrized test with rows for both sides.
    - Criterion 1: `test_the_factory_node_is_pinned_by_version_and_checksum` has the rows as-built, node-20, two-numbers, 63-digits and upper-case. The as-built checksum contains letters, so the upper-case row really changes the text.
    - Criterion 2: `test_the_node_archive_is_checked_before_it_is_unpacked` has the rows no-check, check-after-unpack, piped-into-a-shell, not-curl, another-target and literal-checksum.
    - Criterion 3: `test_the_apt_install_names_exactly_the_six_packages` has the nodejs and npm rows.
    - Criterion 4, the commands: `test_each_runtime_command_runs_on_the_factory_node` has the rows no-arguments, bare-node and no-command, each for claude and opencode.
    - Criterion 4, the installs: `test_the_runtimes_are_installed_by_the_factory_npm_into_its_prefix` has the rows bare-npm and other-prefix. Together with `test_each_tool_is_installed_once_at_its_pinned_version` it checks the pinned versions.
    - Criterion 5: `test_the_factory_node_stays_off_the_path` has the rows node-link, npm-link, npm-created and env-path.

    The round-0 findings (entry 12) are fixed by the rows the tester added in entry 16. The coder's `make check` was green (entry 18).

    **`vm/Dockerfile` does what the Interface asks:**
    - Node 22.23.4 is pinned with its SHA-256, downloaded with `curl -fsSL -o`, and checked with `sha256sum -c -` before `tar -C /opt/factory/node`. Nothing is piped into a shell.
    - The `apt-get` line names the six packages.
    - Both runtimes are installed by `/opt/factory/node/bin/npm --prefix /opt/factory` at their existing pins.
    - The `printf` commands exec `/opt/factory/node/bin/node` with `"$@"`.
    - There is no `ENV PATH` line and no `node` or `npm` in `/usr/local/bin`. The `export PATH` only lasts for its own build step.
    - The `ENV FACTORY_*_VERSION` lines are unchanged.

    **Architecture and security:** only `vm/` and tests changed. There are no secrets: the checksum is public, and the diff adds no baseline entry and no check-silencing marker. The download is verified before it is used.

    **Quality and hygiene:** the comments explain why. The journal gives the main decision (start the runtimes through npm's bin links under `/opt/factory/bin`) and what was rejected (naming each package's entry file; `/opt/factory/bin` on the PATH). The Description matches what was built, and criterion 7 still says what the documenter must write.

    **Not raised:**
    - `test_each_tool_is_installed_once_at_its_pinned_version` repeats the `--prefix` value check that `_installed_by_the_factory_npm` now makes. This is a small overlap in a changed test, not a separated rule.
    - Two risks stay open until the human's build (criterion 6). First, `NODE_SHA256` has not yet been checked against the real archive. Second, a runtime release whose bin is not a Node script would break its wrapper. The human's `--version` check after the build would show it.

    Earlier tests:
    - tests/test_stage_image.py: changed under the feature's leave for S0001 (feature.md, "A leave, for S0001"). The changes are:
      - the Debian package rows (`STAGE_PACKAGES`, `eighth-package` renamed `seventh-package`);
      - the npm install rows (`NPM_FLAGS`, `FACTORY_NPM` in the install and order tests, the `--prefix` value);
      - the places of the runtimes (`/opt/factory` taken out of `ABSENT_WORDS`);
      - the floating-reference test's rewrite of the npm path and prefix, which keeps it checking the npm pins.
      
      The new test functions are additions; none needed.
21. factory: started docs as vm.
22. documenter: Docs round 1. Only documents changed, so I did not run `make check`; the factory's checks run right after this stage.

    Files changed:
    - `docs/operator-guide.md`, *The stage image*:
      - The package list now has six names, with `xz-utils` named as the one for the Node archive.
      - The "installs seven Debian packages" paragraph says six, and the sentence on what the test reports says "those six names".
      - The pinned-tools sentence now includes Node.
      - One new paragraph covers the criterion 7 points: the runtimes run on their own Node under `/opt/factory`, pinned by version and checksum and checked with `sha256sum -c` before unpacking. It also says that the image has no Node for projects, and how to change the pin (both `ARG`s, from nodejs.org's `SHASUMS256.txt`).
      - *Update the pins* gained a line for the Node pin.
    - `docs/decisions.md`: one new entry at the end, "The factory's tools live apart, under `/opt/factory`, with their own Node". It says that it supersedes the seven packages of "Debian's packages follow the base image's release" for `nodejs` and `npm`. Its Why comes from the Description and criterion 7: Claude Code asks for Node 22, Debian has 18, and a project's layer must not change the runtime. The story names no rejected option, so the entry has no "Rejected" line.

    I read `vm/Dockerfile` against the Interface and found no mismatch, so there are no findings for the coder.

    Cross-read and found current: `README.md`, `docs/project-guide/` (the grep found no Node or image-package text), and the rest of `docs/operator-guide.md` that mentions the image or the runtimes. I ran no commands. The examples I wrote are prose, and the human's build checks (criterion 6) are not run in this stage.

    Stale text I saw and left alone: the entry "Every tool of the machine's image is pinned" in `docs/decisions.md` (around line 287) still says "eight Debian tools". It is a dated history entry that the 2026-11-01 entry already supersedes, and it is not this story's.

    `check`: check: green (not run again: passed on tree b60c7ccd56bc at 2026-11-03T23:22:45Z)
    `secrets`: secrets: green (2.3 s)
    `documents`: documents ok
23. factory: started smoke-test as vm.
24. smoke-tester: Ran the five smoke-test commands from the repository root, exactly as written and in order. Each one met its `Expect:` line.

    1. `grep -cE '^ARG NODE_VERSION=22\.[0-9]+\.[0-9]+$' vm/Dockerfile`
    ```
    1
    ```
    Expected `1`: met.

    2. `grep -cE '^ARG NODE_SHA256=[0-9a-f]{64}$' vm/Dockerfile`
    ```
    1
    ```
    Expected `1`: met.

    3. `grep -c 'sha256sum -c' vm/Dockerfile`
    ```
    1
    ```
    Expected `1`: met.

    4. `grep -cE 'install .*\b(nodejs|npm)\b' vm/Dockerfile` (exit status 1, which is grep's status when nothing matches)
    ```
    0
    ```
    Expected `0`: met.

    5. `uv run pytest tests/test_stage_image.py 2>&1 | tail -1`
    ```
    104 passed in 0.10s
    ```
    Expected a line that ends in `passed` with no `failed`: met.

    Checked against the acceptance criteria by reading `vm/Dockerfile`, `docs/operator-guide.md` and `docs/decisions.md`. Nothing the smoke test showed contradicts a criterion:
    - Criteria 1 and 2: the pins are `NODE_VERSION=22.23.4` and a 64-digit lowercase SHA-256. `curl -fsSL -o` saves the archive to a file, and `sha256sum -c -` checks it before the `tar -xJf … -C /opt/factory/node`. No download is piped into a shell.
    - Criterion 3: the `apt-get install` line names exactly `git make curl ca-certificates procps xz-utils`.
    - Criterion 4: both runtimes are installed by `/opt/factory/node/bin/npm install --global --prefix /opt/factory` at `${CLAUDE_CODE_VERSION}` and `${OPENCODE_VERSION}`. The scripts `/usr/local/bin/claude` and `/usr/local/bin/opencode` each run `exec /opt/factory/node/bin/node /opt/factory/bin/<runtime> "$@"`.
    - Criterion 5: nothing creates `node` or `npm` in `/usr/local/bin`, and no `ENV PATH` line exists. The `export PATH=/opt/factory/node/bin:…` inside the two npm `RUN` steps applies to those steps only.
    - Criterion 7: the operator guide lists six packages and has the paragraph on the factory's own Node and how to change its pin. `docs/decisions.md` has the entry "The factory's tools live apart, under `/opt/factory`, with their own Node", which supersedes the seven-package entry for `nodejs` and `npm`.

    Findings: none.

    Open, and not a finding: criterion 6 leaves building the image to the human on the VM. The scripts run `/opt/factory/bin/claude` and `/opt/factory/bin/opencode` as Node scripts, and that only works if npm's installed commands are JavaScript entry points. Only that build can show it, together with `claude --version`, `opencode --version`, `command -v node` and the missing `EBADENGINE` warning. I did not run `make check`; the factory runs it as this stage's check.
25. 2026-11-03 human: Sent back after a real build on factory-vm (podman build of this branch): the build passes with no EBADENGINE, but both wrappers fail. Claude Code 2.1.296 and opencode 1.19.3 install native executables (/opt/factory/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe, and opencode-ai/bin/opencode.exe, an ELF file), so running them with /opt/factory/node/bin/node gives ERR_UNKNOWN_FILE_EXTENSION and a SyntaxError. The human's correction (feature decision 6): the runtimes need Node only for npm's install, not to run. /usr/local/bin/claude and /usr/local/bin/opencode each exec the installed command under /opt/factory/bin directly, passing "$@" on; they do not name /opt/factory/node/bin/node. Criterion 4 changes accordingly: each wrapper execs /opt/factory/bin/<runtime> with "$@"; a wrapper that names a node binary is refused. Everything else stays: Node 22 under /opt/factory/node for the install, no node or npm on the PATH, the six packages. After the fix I build it again on the VM and check claude --version and opencode --version.
26. 2026-11-03 human: closed the pull request.
