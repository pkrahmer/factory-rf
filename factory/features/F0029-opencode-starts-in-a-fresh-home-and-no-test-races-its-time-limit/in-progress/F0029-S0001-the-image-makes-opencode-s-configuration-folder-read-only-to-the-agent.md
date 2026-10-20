---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 309
comments_read: [6280599340]
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-20T00:43:08.420957Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T00:32:46.082400Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T00:32:46.087951Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T00:33:01.188605Z'
  stage: intake
  run: ad4b8eacad1a43309cb95065c996ed5e
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T00:33:21.749225Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T00:35:20.950070Z'
  stage: tests
  run: d5fe32a6e12d450b98d793585e0229df
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T00:35:41.461005Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T00:37:35.112441Z'
  stage: doing
  run: 0c46743232bb424ea87995dc14b668b4
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T00:37:55.917014Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T00:38:36.219675Z'
  stage: review
  run: 84e911b752d7472ab6ba18f36198bec7
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T00:38:56.687297Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T00:39:24.527507Z'
  stage: docs
  run: 9e1d5df0f5e34ed981cbe50d9d5624e0
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T00:39:45.100168Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: question
  at: '2026-10-20T00:40:31.321297Z'
  stage: smoke-test
  run: 915e795973264a59885bcd8c92f7e733
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-10-20T00:42:50.141058Z'
  stage: smoke-test
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-20T00:43:08.420957Z'
  stage: smoke-test
---

# The image makes opencode's configuration folder, read-only to the agent

## Description

opencode 1.19.3 makes `~/.config/opencode` on its first run. The kernel's write guard refuses that `mkdir`, because a run's rules allow opencode's three folders (`RUNTIME_FOLDERS`) and nothing under `.config`, on purpose. So in every new container of an instance on opencode, the first preflight probe ends `died` and the instance stops. The agent's home outside `.claude` is no volume, so every recreated container has a fresh home. This story makes the image create `/home/agent/.config/opencode`, owned by `factory` with mode `0755`. opencode then finds its configuration folder. It cannot write into it: the agent is in the group `factory-work`, and the folder grants that group no write. Its failed write of a default `opencode.jsonc` is one opencode ignores. `/home/agent/.config` stays the agent's, so `factory-confine` can still make the folders an operator names in `FACTORY_OPENCODE_FOLDERS` (such as `.config/sso-opencode`). `RUNTIME_FOLDERS`, the run's rules, `image/entrypoint.sh` and every module under `src/` stay as they are. The check on a recreated instance is the human's change 1 after this story.

## Interface

`image/Dockerfile` (the coder's; no module under `src/factory/` changes):

```dockerfile
# opencode makes its configuration folder in the agent's home on its first run and dies when the
# write guard refuses that; made here and read-only to the agent, so that no run can write what
# the next run reads. The folder above stays the agent's, for the folders of FACTORY_OPENCODE_FOLDERS.
RUN mkdir -p /home/agent/.config/opencode \
 && chown agent:factory-work /home/agent/.config \
 && chown factory:factory-work /home/agent/.config/opencode \
 && chmod 0755 /home/agent/.config /home/agent/.config/opencode
```

- The `RUN` above is its own instruction, with its comment, right after the `RUN` that adds the users (`useradd ... agent`) and before `WORKDIR /opt/factory`; so it comes after the users exist and before `USER factory`.
- `/home/agent/.config/opencode` is owned by `factory:factory-work` with mode `0755`: no write bit for the group or for others, so the agent cannot write it, under the guard or without it.
- `/home/agent/.config` is owned by `agent:factory-work` with mode `0755`: the agent can make a folder in it, as `factory-confine` does for each folder of a run's rules before it confines the run.
- Each `chown` names one owner and its paths without `-R`, as the Dockerfile's other `chown`s do, so `_path_settings` of `tests/test_image.py` reads it.

Unchanged: `RUNTIME_FOLDERS` and its comment in `src/factory/adapters/opencode_runtime.py` (the three folders, nothing under `.config`), `FACTORY_OPENCODE_FOLDERS`, `image/entrypoint.sh`, `image/compose.yml`, every other instruction of the Dockerfile.

Tests (the tester writes them): `tests/test_opencode_config_folder.py`, which reads the Dockerfile with `_commands` and `_path_settings` of `tests/test_image.py` (as `tests/test_agent_home_ownership.py` imports `_path_settings`) and `dockerfile_instructions` of `tests/dockerfile_support.py`. `tests/adapters/test_opencode_runtime_folders.py` already pins `RUNTIME_FOLDERS` as the three; it is not changed.

## Acceptance criteria

1. The folders and their owners (rows of one parametrized test over the Dockerfile): a `mkdir -p` names `/home/agent/.config/opencode`. Row `configuration`: the last `chown` of `/home/agent/.config/opencode` is `factory:factory-work`, its last `chmod` is `0755`, and that mode has no group or other write bit (`int(mode, 8) & 0o022 == 0`), so the agent cannot write it. Row `parent`: the last `chown` of `/home/agent/.config` is `agent:factory-work` and its last `chmod` is `0755`, so the agent can make a folder in it.
2. The order (one test over `dockerfile_instructions()`): exactly one `RUN` instruction holds `mkdir -p /home/agent/.config/opencode`. It is the instruction right after the `RUN` that holds `useradd` for `agent`, so it comes before `WORKDIR /opt/factory` and before `USER factory`.
3. `RUNTIME_FOLDERS` is still `(".local/share/opencode", ".local/state/opencode", ".cache/opencode")`, none of them under `.config`: the `default` row of `test_the_rules_allow_each_runtime_folder_in_the_home_in_order` in `tests/adapters/test_opencode_runtime_folders.py` passes unchanged.
4. `make check` stays green.
5. docs: `docs/operator-guide.md`, *What opencode keeps in the agent's home*: the image makes `/home/agent/.config/opencode`, owned by `factory` and read-only to the agent. opencode 1.19.3 makes that folder on its first run and dies (`EACCES ... mkdir`, the probe ends `died`) when it cannot. With the folder in place, it starts and leaves the folder empty. Naming `.config/opencode` in `FACTORY_OPENCODE_FOLDERS` is not needed, and the folder's owner refuses the write anyway; `/home/agent/.config` stays the agent's, so folders such as `.config/sso-opencode` still work. *The preflight's items*, where the guide explains `agent-run-probe` ending `died`: on opencode, an image built before this story stops each new container this way; rebuild it. `docs/project-guide/agents.md`, *opencode's folders*: the image makes `.config/opencode` read-only to the agent, so opencode's first run in a fresh home does not die, and `.config` itself stays the agent's for `FACTORY_OPENCODE_FOLDERS`. `docs/decisions.md`: an entry *opencode's configuration folder is made by the image, read-only to the agent*, dated with the story, with these reasons and rejected alternatives. The folder must exist, but a run must not write it: opencode reads `opencode.jsonc` there on every run, beside `OPENCODE_CONFIG`. Rejected: `.config/opencode` in `RUNTIME_FOLDERS` (one run could change what the next run is told). Rejected: the entrypoint making it (it runs as `factory`, could make it only through `sudo -u agent` as an agent-owned folder, and at every start). Rejected: `XDG_CONFIG_HOME` in the run's temporary folder (it moves every tool's configuration and an operator's single sign-on login).

## Smoke test

```bash
grep -c -F -e 'mkdir -p /home/agent/.config/opencode' -e 'chown factory:factory-work /home/agent/.config/opencode' -e 'chown agent:factory-work /home/agent/.config ' image/Dockerfile
```
Expect: `3`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/fresh" "$d/made/.config/opencode" "$d/w"
chmod 0555 "$d/made/.config/opencode"
for home in fresh made; do
  printf '{"folders":["%s/w","%s/%s/.local/share/opencode","%s/%s/.local/state/opencode","%s/%s/.cache/opencode"],"files":["/dev/null"],"temporary_directory":"%s/t-%s"}' "$d" "$d" "$home" "$d" "$home" "$d" "$home" "$d" "$home" > "$d/rules-$home.json"
  HOME="$d/$home" XDG_CONFIG_HOME= factory-confine --rules "$d/rules-$home.json" -- sh -c 'cd "$1" && exec opencode debug config' sh "$d/w" >/dev/null 2>"$d/err-$home"
  echo "$home $?"
done
grep -c "EACCES: permission denied, mkdir '$d/fresh/.config'" "$d/err-fresh"
```
Expect: three lines, `fresh 1`, `made 0`, `1` (the image's opencode under the write guard dies in a home without its configuration folder, and starts in one whose folder exists and is read-only; this shows the mechanism with the image the smoke test runs in, not the rebuilt one, which the human's change 1 checks)

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names `image/Dockerfile` with the exact `RUN`, its position (after the `useradd ... agent` RUN, before `WORKDIR /opt/factory` and `USER factory`), owners and modes of both folders, and the `chown` form that `_path_settings` of `tests/test_image.py` reads. No `src/` module changes. It has no behaviour comment without a criterion.
   Criteria: each fits one test function. Criterion 1 is one parametrized test with a row per folder, `configuration` and `parent`. Both rows check owner and mode, and the no-write-bit check is stated as `int(mode, 8) & 0o022 == 0`. Criterion 2 is the order, criterion 3 pins `RUNTIME_FOLDERS` through an existing test, 4 is `make check`, and 5 is the docs. The failing side (the agent cannot write the configuration folder) is covered by the mode check. The parent folder staying the agent's is covered by the `parent` row.
   Smoke test: the first block is a `grep -c` that the Dockerfile text will match with `Expect: 3`. The second block runs `opencode debug config` under `factory-confine` in two temporary homes. Its expectation is three checkable lines, `fresh 1`, `made 0` and `1`.
   Architecture: this is an image-only change. It leaves the layers, the write guard and `RUNTIME_FOLDERS` alone, and the feature's decisions 1 to 3 give the reasons. The test goes in `tests/` at its root, like the other image tests.
   Scope: it matches the feature's Scope, S0001 first. The story does not touch anything in the feature's Out of scope: `RUNTIME_FOLDERS`, the entrypoint and S0002's tests. It changes no test another story wrote.
4. factory: started tests as self.
5. tester: Wrote the tests for the image's opencode configuration folder. The tests read `image/Dockerfile` through `_commands` and `_path_settings` of `tests/test_image.py` and `dockerfile_instructions` of `tests/dockerfile_support.py`, as the Interface says.

   - criterion 1: tests/test_opencode_config_folder.py::test_the_image_makes_the_configuration_folder_read_only_and_leaves_its_parent_the_agents, with rows `configuration` and `parent`. Each row checks that a `mkdir -p` names `/home/agent/.config/opencode`, the last `chown` and last `chmod` of the path, and `int(mode, 8) & 0o022 == 0`. That last check also holds for the parent's `0755`, since it follows from the mode.
   - criterion 2: tests/test_opencode_config_folder.py::test_the_configuration_folder_is_made_right_after_the_agent_is_added. Exactly one `RUN` holds `mkdir -p /home/agent/.config/opencode`, and exactly one `RUN` holds `useradd ... agent`. The mkdir `RUN` is the instruction right after the useradd `RUN` and comes before `WORKDIR /opt/factory` and `USER factory`.
   - criterion 3: tests/adapters/test_opencode_runtime_folders.py::test_the_rules_allow_each_runtime_folder_in_the_home_in_order[default], which already exists and is not changed. No new test.
   - criteria 4 and 5: `make check` and docs, no test.

   Files created: tests/test_opencode_config_folder.py. No earlier test file was changed.

   Modules the test runner could not import: none. The three new test cases fail on missing Dockerfile settings and the wrong instruction order, the right reasons. `make lint` is green.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/test_opencode_config_folder.py::test_the_image_makes_the_configuration_folder_read_only_and_leaves_its_parent_the_agents[configuration]
6. factory: started doing as self.
7. coder: Built: `image/Dockerfile`. Added the Interface's `RUN` with its comment as a separate instruction. It sits right after the `RUN` that adds the users (`useradd ... agent`) and before `WORKDIR /opt/factory`. It makes `/home/agent/.config/opencode` owned by `factory:factory-work` and `/home/agent/.config` owned by `agent:factory-work`, both with mode `0755`. Each `chown` names one owner and has no `-R`. No module under `src/` changed.

   Main choice: a new `RUN` of its own, as the Interface and criterion 2 require. I rejected putting the lines into the existing user-adding `RUN`, next to the `.claude` folder. That would keep the image one layer smaller, but the test needs the mkdir to be a separate instruction right after the `useradd` one.

   Checks: `make check` is green (`check: green`). The first smoke-test grep prints `3`. I did not run the second smoke-test block (`factory-confine` with opencode); it tests the image the smoke test runs in.

   Refactor: the diff is the Interface's text exactly, so nothing needed changing. The journal did not change the meaning of the task.

   Noticed but not touched: the docs criterion (operator guide, `agents.md`, `decisions.md`) belongs to the docs stage.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'`, which covers `image/Dockerfile` (+7) and `tests/test_opencode_config_folder.py` (new), against the work item.
   - Acceptance criteria:
     - Criterion 1 is one test parametrized over the rows `configuration` and `parent`. Each row checks the `mkdir -p`, the last `chown` and `chmod` through `_path_settings` of `tests/test_image.py`, and `int(mode, 8) & 0o022 == 0`. The Dockerfile gives `factory:factory-work` / `0755` to `/home/agent/.config/opencode` and `agent:factory-work` / `0755` to `/home/agent/.config`. These match the test.
     - Criterion 2 checks over `dockerfile_instructions()` that there is exactly one mkdir `RUN`. That `RUN` comes right after the one `useradd ... agent` `RUN` and before both `WORKDIR /opt/factory` and `USER factory`. The Dockerfile has the new `RUN` at lines 35–38, right after the user `RUN` that ends at line 31, and `WORKDIR` follows at line 39.
     - Criterion 3 rests on the existing `[default]` row of `tests/adapters/test_opencode_runtime_folders.py`, which this diff leaves alone. Nothing under `src/` changes.
     - Journal entry 7 records the factory's `make check` as `check: green`.
     - The Interface sets no limit on an input and names no refused input. The one rule it states (no group or other write bit) is a property of the image, pinned by the mode check.
   - Architecture: this is an image-only change, and no layer, wrapper or `RUNTIME_FOLDERS` changes. `image/entrypoint.sh` and `image/compose.yml` are unchanged, and neither touches `/home/agent/.config`.
   - Security: no marker that silences a check, no secret, no shell built from strings. The configuration folder is not writable by the agent's group or by others, and `factory` is in `factory-work` as its primary group.
   - Quality: the new test reuses `_commands`, `_path_settings`, `DOCKERFILE` and `dockerfile_instructions` and copies no existing helper. The Dockerfile comment explains why the folder exists.
   - Work item hygiene:
     - The coder's entry gives the main choice (a `RUN` of its own) and what was rejected (merging it into the user-adding `RUN`).
     - The Description matches what was built.
     - The docs criterion still says what the operator guide, `agents.md` and `decisions.md` must state after this story.

   Earlier tests: none. The diff only adds `tests/test_opencode_config_folder.py` and changes, renames or deletes no test file that `main` holds.
10. factory: started docs as self.
11. documenter: no findings. Only documents changed, so I did not run `make check`; the factory's checks decide.

    Files changed:
    - `docs/operator-guide.md`: in *What opencode keeps in the agent's home*, the image makes `/home/agent/.config/opencode`, read-only to the agent. It says why: opencode 1.19.3 makes it on its first run and dies (`EACCES ... mkdir`, probe `died`) when it cannot. It also says that naming it in `FACTORY_OPENCODE_FOLDERS` is not needed and that `/home/agent/.config` stays the agent's. In *The probe of the agent run*, an image built before this story stops each new opencode container with `died`; rebuild it. I put that note there because the criterion's "The preflight's items" has no passage on `died` apart from the probe's section.
    - `docs/project-guide/agents.md`: *opencode's folders* now says the image makes `.config/opencode` read-only to the agent, that `RUNTIME_FOLDERS` does not list it, and that `.config` stays the agent's.
    - `docs/decisions.md`: new entry *opencode's configuration folder is made by the image, read-only to the agent*, with the reasons and the three rejected alternatives from the criterion.

    Cross-read and found current against the diff (`image/Dockerfile` +7 lines, plus the test file): the `FACTORY_OPENCODE_FOLDERS` row of the settings table, the "Running on opencode" login passage, and the Dockerfile description in the operator guide. None of them contradicts the diff.

    Code against Interface: the Dockerfile `RUN` matches the Interface exactly (owners, modes, position after the `useradd` RUN, before `WORKDIR`).

    Stale text not touched: none seen. I did not run the smoke test's second block, which needs the image's opencode and `factory-confine`.

    `check`: check: green (not run again: passed on tree e77b3d64b793 at 2026-10-20T00:36:47Z)
    `secrets`: secrets: green (1.6 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: The smoke test is not finished: the first command ran and passed, but the second one was never run. Claude Code's safety check blocked it in this session, so I have no result to judge it on. I stopped there and did not try to get around the check.

    Command 1 met its `Expect:` line (`3`):
    ```
    $ grep -c -F -e 'mkdir -p /home/agent/.config/opencode' -e 'chown factory:factory-work /home/agent/.config/opencode' -e 'chown agent:factory-work /home/agent/.config ' image/Dockerfile
    3
    ```

    Command 2 (`factory-confine` running `opencode debug config` in a `fresh` home and in a `made` one) did not run, so I cannot say whether it met its `Expect:` line. It was blocked twice:
    - Run as written, Claude Code's built-in check refused it: "This command passes a shell -c script that runs rm, and Claude Code could not check the script for dangerous removals." It flags the `trap 'rm -rf "$d"' EXIT` line, and the `sh -c '... exec opencode debug config'` inside the loop seems to make it unable to check the script. Only a person can approve that, and no prompt was possible here.
    - The check's message says to finish the task without the removal, so I tried once more with only the `trap` line left out (`mktemp -d` puts the folder in `$TMPDIR`, which the factory removes). It was refused with the same message. The check says not to try again by splitting or rewriting the command, so I stopped. Nothing was run and nothing was left behind.

    Not a finding: I have nothing that contradicts an acceptance criterion. Command 1 confirms the Dockerfile lines behind criterion 1. Criteria 2 to 4 rest on the tests and `make check`, which the earlier stages recorded as green. I did not run `make check` again, because the smoke test does not include it.

    Question: how should command 2 be run? Options:
    (a) The human runs command 2 as written in the image (or approves it in an interactive session) and posts its output; the smoke test then runs again, and I judge that output against `fresh 1`, `made 0`, `1`.
    (b) The human changes the `## Smoke test` so the safety check can read it, for example a script file run with `bash <file>`, or no `trap rm -rf` (the stage's `$TMPDIR` is removed anyway), and the stage runs again.
    (c) The human accepts command 1 alone for this story and leaves the mechanism to change 1 on a recreated instance, which the story already names as the human's.
    I would choose (b): the smoke test stays repeatable by the pipeline. As far as this run shows, the `trap` line plus the `sh -c` is what the check refuses.
14. 2026-10-20 human: (a). I ran command 2 exactly as written (the block saved unchanged to a file and run with bash), as the agent user, in a throwaway container of today's image `factory-self-factory` (`docker run --rm --network none -u agent`, without the story's Dockerfile change, as the Expect line says). Its output:

    ```
    fresh 1
    made 0
    1
    ```

    exit 0. Judge it against the Expect line; command 1 stands as you ran it.
15. factory: started smoke-test as self.
