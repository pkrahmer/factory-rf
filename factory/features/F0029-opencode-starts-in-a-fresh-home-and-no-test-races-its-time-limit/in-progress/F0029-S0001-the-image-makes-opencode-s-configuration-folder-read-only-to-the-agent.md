---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 309
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-20T00:33:21.749225Z'
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
