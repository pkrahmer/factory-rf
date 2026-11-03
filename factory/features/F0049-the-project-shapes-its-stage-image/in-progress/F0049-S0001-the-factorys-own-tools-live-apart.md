---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 526
comments_read: [6617813159]
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
