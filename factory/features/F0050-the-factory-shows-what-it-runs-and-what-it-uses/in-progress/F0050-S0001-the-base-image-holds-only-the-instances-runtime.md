---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 538
comments_read: [6626791280]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-04T09:06:03.619975Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T08:44:32.295901Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T08:44:32.302759Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T08:44:58.986388Z'
  stage: intake
  run: feb756dad20f40b2a511e1f4301703ac
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T08:57:10.111349Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T08:57:13.517346Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T08:57:37.894708Z'
  stage: intake
  run: 61b1d822b1104c51ad6ec00cae167234
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T08:57:44.016290Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-04T09:05:56.907760Z'
  stage: tests
  run: d34ce2cc26cb43a8a4f75b4990d5b790
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-04T09:06:03.619975Z'
  stage: doing
---

# The base image holds only the instance's runtime, with nothing left from its install

## Description

`vm/Dockerfile` installs both agent runtimes with the factory's Node, and everything that install used stays in the image: npm's download cache (441 MB), the Node itself (201 MB), and opencode's second, "baseline" executable (178 MB), next to the one opencode runs. An instance runs only the runtime `FACTORY_AGENT_RUNTIME` names. This story builds the base image for one runtime, named by the new build argument `AGENT_RUNTIME`, which has no default. The download of Node and the install of the runtime happen in a first build stage; the image takes from it only what the chosen runtime runs, so it holds no Node, no npm, no npm cache and no executable of the other runtime. The small cleanups of the remaining stages go too: apt's and debconf's caches, the install logs and anything left in `/tmp`. The pins move to Claude Code 2.1.318 and opencode 1.19.5 (feature decision 3). Both version settings stay in the image, as today, so that `vm/setup.sh` and `vm/job-start.sh` read them unchanged. How the factory calls a runtime does not change: `/usr/local/bin/<runtime>` execs the native executable, and the image has no command for the other runtime.

## Interface

- `vm/Dockerfile`:
  - `ARG AGENT_RUNTIME`, without a default; a build with an empty or unknown value fails with a message that names `AGENT_RUNTIME` and the two values.
  - A first build stage downloads and checks Node as today, and installs only the chosen runtime at its pinned version. The final stage copies only what that runtime runs; the coder decides what that is, and opencode's unused CPU build is not part of it.
  - The final stage holds no `/opt/factory/node`, no `node` or `npm` anywhere on the `PATH`, no `/root/.npm`, no other runtime, nothing in `/tmp`, and no apt lists.
  - `CLAUDE_CODE_VERSION=2.1.318`, `OPENCODE_VERSION=1.19.5`; the `ENV FACTORY_CLAUDE_VERSION` and `ENV FACTORY_OPENCODE_VERSION` lines and `FACTORY_OPENCODE_MODELS` stay.
  - The first line names the build command with `--build-arg AGENT_RUNTIME=<claude|opencode>`.
- `vm/job-start.sh`: its image build passes `--build-arg AGENT_RUNTIME=$FACTORY_AGENT_RUNTIME`.
- `vm/setup.sh` does not change.

## Acceptance criteria

1. The stage-image test refuses a Dockerfile in which `AGENT_RUNTIME` has a default, and one whose final stage takes Node, npm, npm's cache or the other runtime's install from the first stage.
2. The final stage installs no runtime by npm and runs no `npm`; only the first stage does, and it installs exactly one runtime, chosen by `AGENT_RUNTIME`, at its pinned version. The stage-image test checks the text: every `npm` line lies before the final stage's `FROM`; there is exactly one `npm install`; the package it installs is chosen from `${AGENT_RUNTIME}` (for example a shell `case` mapping `claude` to `@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}` and `opencode` to `opencode-ai@${OPENCODE_VERSION}`). Rows: an `npm` line after the final `FROM`, two `npm install` lines, an install whose package does not depend on `${AGENT_RUNTIME}`.
3. The pins are `CLAUDE_CODE_VERSION=2.1.318` and `OPENCODE_VERSION=1.19.5`; Node's pins do not change.
4. `vm/job-start.sh` builds with `--build-arg AGENT_RUNTIME=$FACTORY_AGENT_RUNTIME`; its test row shows the argument, and a row refuses a build line without it.
5. The stage-image test requires the Dockerfile to check `AGENT_RUNTIME` before any install (empty, and neither `claude` nor `opencode`) and to fail there with a message that contains `AGENT_RUNTIME`, `claude` and `opencode`. Rows: the file as built, the check missing, a message without one of the three words.
6. The stage-image test checks the final stage's text for its cleanups, one row per clause: it leaves nothing in `/tmp`; it removes apt's lists; it removes debconf's cache and the install logs (`/var/cache/debconf/*-old`, `/var/log/*.log` or wider); its `COPY --from` lines take only the chosen runtime's files; and no `COPY --from` of the final stage names a path that contains `baseline`.
7. The stage-image test requires the `ENV FACTORY_CLAUDE_VERSION`, `ENV FACTORY_OPENCODE_VERSION` and `ENV FACTORY_OPENCODE_MODELS` lines to stay. Rows: each line removed is refused.
8. The stage-image test requires the Dockerfile's first line to name the build command with `--build-arg AGENT_RUNTIME=<claude|opencode>`. Row: a first line without it is refused.
9. `make check` stays green. No test builds the image. The human builds it on factory-vm for each runtime and checks: the build without `AGENT_RUNTIME` fails with its message; with `claude`, `claude --version` reports 2.1.318, `command -v opencode node npm` finds nothing, and the image is under 0.7 GB; with `opencode`, `opencode --version` reports 1.19.5, `command -v claude node npm` finds nothing, and the image is under 0.6 GB; neither image has `/root/.npm` or `/opt/factory/node`; the preflight and its agent-run probe pass on the `claude` image.
10. docs: `docs/operator-guide.md`: in *The stage image*, the build command with `AGENT_RUNTIME`, that the image holds only that runtime and must match the instance's `FACTORY_AGENT_RUNTIME`, that a runtime change needs a rebuild and a new `image-id`, and the new pins. `docs/decisions.md`: one entry with feature decisions 1 and 2 and their reasons. `README.md` and the project guide: none.

## Smoke test

```bash
grep -cE '^ARG AGENT_RUNTIME$' vm/Dockerfile
grep -cE '^ARG CLAUDE_CODE_VERSION=2\.1\.318$|^ARG OPENCODE_VERSION=1\.19\.5$' vm/Dockerfile
grep -c 'AGENT_RUNTIME=\$FACTORY_AGENT_RUNTIME' vm/job-start.sh
uv run pytest tests/test_stage_image.py tests/test_vm_job_start.py 2>&1 | tail -1
```

Expect: `1`, `2`, `1`, then a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: Questions (format check: passed). The story is within F0050's scope and fits the architecture, since it touches only `vm/` and docs. Interface rules lack criteria, though.

   1. The Interface says a build with an empty or unknown `AGENT_RUNTIME` fails with a message that names `AGENT_RUNTIME` and the two values. No criterion tests the failing side. Criterion 5 only has the human build without the argument. An empty value and an unknown value are not covered at all. Should a criterion say the stage-image test requires the Dockerfile to check the value (empty, and neither `claude` nor `opencode`) and to fail with a message that contains `AGENT_RUNTIME`, `claude` and `opencode`? I would add it.

   2. Criterion 1 covers Node, npm, npm's cache and the other runtime's install. The Interface also says the final stage holds nothing in `/tmp`, no apt lists, and no install logs (the Description adds debconf's cache). It also says opencode's unused CPU build is not part of the final stage. Which of these does the stage-image test check? I would add one criterion per clause. Is the baseline executable a clause with its own row?

   3. The Interface says `ENV FACTORY_CLAUDE_VERSION`, `ENV FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` stay. The Interface also says the first line names the build command with `--build-arg AGENT_RUNTIME=<claude|opencode>`. Neither has a criterion. Should each get one? Criterion 3 covers only the `ARG` pins.

   4. Criterion 2 says only the first stage installs, and installs exactly one runtime chosen by `AGENT_RUNTIME`. How is the test to see that? For example, must the install line use `${AGENT_RUNTIME}` to pick the package, so the test checks the text? Please name the check. As written, two testers could read it two ways.

   5. Criterion 4 is clear. Is the criterion 4 test also meant to refuse a `job-start.sh` build line without the argument? The "refused side" is implicit.
4. 2026-11-04 human: Answers of the human:

   1. Yes. Add a criterion: the stage-image test requires the Dockerfile to check `AGENT_RUNTIME` before any install (empty, and neither `claude` nor `opencode`) and to fail there with a message that contains `AGENT_RUNTIME`, `claude` and `opencode`. Rows: the file as built, the check missing, a message without one of the three words.

   2. One criterion with one row per clause, all checks of the Dockerfile's text: the final stage leaves nothing in `/tmp`; it removes apt's lists; it removes debconf's cache and the install logs (`/var/cache/debconf/*-old`, `/var/log/*.log` or wider); and the final stage's `COPY --from` lines take only the chosen runtime's files. Yes, the baseline executable is a row of its own: no `COPY --from` of the final stage names a path that contains `baseline`.

   3. Yes, one criterion each: the `ENV FACTORY_CLAUDE_VERSION`, `ENV FACTORY_OPENCODE_VERSION` and `ENV FACTORY_OPENCODE_MODELS` lines stay (rows: each line removed is refused); and the first line names the build command with `--build-arg AGENT_RUNTIME=<claude|opencode>` (row: a first line without it is refused).

   4. The check is: every `npm` line lies before the final stage's `FROM`; there is exactly one `npm install`, and the package it installs is chosen from `${AGENT_RUNTIME}` (for example a shell `case` that maps `claude` to `@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}` and `opencode` to `opencode-ai@${OPENCODE_VERSION}`). The test checks the text: rows for an `npm` line after the final `FROM`, two `npm install` lines, and an install whose package does not depend on `${AGENT_RUNTIME}`.

   5. Yes: the test refuses a `job-start.sh` build line without `--build-arg AGENT_RUNTIME=$FACTORY_AGENT_RUNTIME`.
5. factory: started intake as vm.
6. intake: accepted. The human's answers (journal entry 4) are carried into the story as their edit, not as my improvement: criterion 2 now names the text check and its three rows (answer 4); criterion 4 adds the refused side (answer 5); new criteria 5 (AGENT_RUNTIME check and message, answer 1), 6 (cleanups and `COPY --from` rows, including `baseline`, answer 2), 7 (the three ENV lines, answer 3) and 8 (first line names the build command, answer 3). The closing two criteria are now 9 (`make check`) and 10 (`docs:`), still last. The Description's meaning did not change.
   - Interface: names concrete files and lines (`vm/Dockerfile` ARG, stages, pins, ENVs, first line; `vm/job-start.sh` build argument; `vm/setup.sh` unchanged). Every stated behaviour now has a criterion: the AGENT_RUNTIME failure (5), the final-stage contents (1, 2, 6), the pins (3), the ENV lines (7), the first line (8), the job-start argument (4).
   - Criteria: each is testable as one parametrized test over the Dockerfile's or script's text, and each rule has its failing side as rows (default present, check missing, message missing a word, npm after the final FROM, two installs, an install independent of the runtime, each ENV removed, first line without the argument, job-start line without the argument). Criterion 5 for `make check` and the image build is the human's manual check, as the story says.
   - Smoke test: the grep and pytest commands are runnable. pytest gets no `-q`, and the `Expect:` ends in `passed` with no `failed`, which the output can be checked against, provided the project's `addopts` keep a summary line. I did not check that.
   - Architecture: the story touches only `vm/`, tests and docs, with no layer involved.
   - Scope: within F0050's scope (S0001 items). The feature's leave covers changing `tests/test_stage_image.py` and the build-command row of `tests/test_vm_job_start.py`, and nothing else in that module.
7. factory: started tests as vm.
8. tester: Wrote the stage-image and job-start tests from the criteria. I changed only `tests/test_stage_image.py` and the build-command row of `tests/test_vm_job_start.py`, under the feature's leave that intake recorded. I created no new files.

   Criteria → tests:
   - criterion 1: tests/test_stage_image.py::test_the_runtime_build_argument_has_no_default (as-built, `=claude`, `=` empty) and tests/test_stage_image.py::test_the_final_stage_takes_only_the_chosen_runtime_from_the_first_stage (rows node, node-executable, npm, npm-cache, whole-prefix, opencode-install, claude-install)
   - criterion 2: tests/test_stage_image.py::test_the_first_stage_installs_the_one_runtime_its_name_chooses (as-built, npm-in-final, two-installs, package-without-the-runtime)
   - criterion 3: tests/test_stage_image.py::test_each_install_pin_has_its_value (NODE_SHA256 is compared as its decimal number, because the hex literal failed `make secrets`)
   - criterion 4: tests/test_vm_job_start.py::test_the_stage_image_is_built_on_a_tmpfs_with_the_job_options (now shows `AGENT_RUNTIME=opencode` and compares the rest of the argv as before) and tests/test_vm_job_start.py::test_the_stage_image_is_built_for_the_instance_runtime (as-written, without-the-runtime)
   - criterion 5: tests/test_stage_image.py::test_the_runtime_build_argument_is_checked_before_any_install (as-built, no-check, message-without-AGENT_RUNTIME/claude/opencode)
   - criterion 6: tests/test_stage_image.py::test_the_final_stage_leaves_no_install_rest (rows tmp, apt lists, debconf, logs) and tests/test_stage_image.py::test_the_final_stage_takes_only_the_chosen_runtime_from_the_first_stage (rows for the other runtime's literal paths and baseline)
   - criterion 7: tests/test_stage_image.py::test_the_version_settings_stay_in_the_image
   - criterion 8: tests/test_stage_image.py::test_the_first_line_names_the_build_command_with_the_runtime (replaces test_the_first_line_names_the_build_command)
   - criteria 9 and 10: no test (`make check`, the human's build, docs).

   How the text checks work:
   - The final stage is everything after the last `FROM`.
   - The runtime check must come before the first install command: `apt-get install`, `pip install`, `npm install` or `curl`. Before it, the file must reference `${AGENT_RUNTIME}`, have an `exit` with a non-zero status, and have an `echo` or `printf` whose message (with variables taken out) holds the three words. The test does not check the empty case separately; a `case` with `*)` covers it.
   - An install "depends on the runtime" when its one package word still holds a `$` after the ARG defaults are put in, and its RUN references `AGENT_RUNTIME` and holds both pinned packages.
   - The cleanups are `rm` arguments that cover `/tmp/*`, `/var/lib/apt/lists/*`, `/var/cache/debconf/*-old` and `/var/log/*.log` (a glob or a parent directory). They must come after the final stage's last `apt-get` or `/tmp` use.
   - A COPY --from source is refused when it holds a `node`, `npm` or `.npm` path segment, lies above or below `/opt/factory/node` or `/root/.npm`, or holds a runtime name not written as `${AGENT_RUNTIME}`. It is also refused when any word of the instruction contains `baseline`.

   Earlier tests in tests/test_stage_image.py that the two-stage, one-runtime file must break, changed under the leave:
   - The floating-reference test and the two npm-install tests now apply each runtime's package to the one install (`_for_runtime`).
   - The floating-reference test ignores the final stage's default-less `ARG CLAUDE_CODE_VERSION`.
   - The base-image test now wants the final FROM to be `${BASE_IMAGE}` and two digest-pinned references.
   - test_the_stage_image_has_one_instruction_of_each_kind became test_the_stage_image_has_its_count_of_each_instruction: two FROM, one LABEL, one COPY without `--from`.
   - The apt tests now read the final stage only.
   - The agent-files copy test ignores COPY --from.
   - The exec-wrapper test replaces `${AGENT_RUNTIME}` with each name.
   - test_opencode_is_installed_after_claude_code is removed, because the story asks for exactly one install.

   Check: with a sample two-stage Dockerfile and job-start line, both modules passed in full. I then restored `vm/` from HEAD, and `git status` shows only the two test files changed.

   Red run: `uv run pytest -q tests/test_stage_image.py tests/test_vm_job_start.py` fails on the current files with wrong results (for example `[as-built]` rows and the job-start build rows). There were no import errors; no module was missing. `make lint` green, `make secrets` green. No project skill was used.

   The factory left out changes outside the write paths: vm/Dockerfile, vm/job-start.sh.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
