---
stage: done
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 283
comments_read: [6276582165]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T20:10:04.741670Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T20:10:04.748603Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T20:10:25.801506Z'
  stage: intake
  run: c94bfdc941c44d6591ff0f5f6a55030f
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T20:10:46.284107Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T20:15:02.032367Z'
  stage: tests
  run: cf763da2b0584cc38d0beb4686043da9
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T20:15:22.868290Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T20:17:15.323801Z'
  stage: doing
  run: dfa7691c53fc41f1878cbab8315f6fcc
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T20:17:36.458297Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T20:18:24.905114Z'
  stage: review
  run: 0487b3ff7124422cab2639789af1477b
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T20:18:46.703804Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-19T20:19:00.793806Z'
  stage: doing
  run: 05ac47803e69479ebe13fc10a4ece436
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T20:19:21.332672Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-19T20:21:09.660825Z'
  stage: tests
  run: 869ebbcaad2c43e693e9bf52b41e7f97
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T20:21:30.711930Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-19T20:23:27.047308Z'
  stage: doing
  run: 17f1c7fb90b64302957e331d745745c7
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-19T20:23:47.999988Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-19T20:24:13.341413Z'
  stage: review
  run: 7f4b55bc7db14a69b5e5548f397f92e6
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-19T20:24:33.921018Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-10-19T20:24:48.023835Z'
  stage: docs
  run: 9010406901a9444aa51a4def0a17c617
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-19T20:25:08.457788Z'
  stage: smoke-test
- number: 21
  speaker: smoke-tester
  kind: question
  at: '2026-10-19T20:25:54.956094Z'
  stage: smoke-test
  run: 723eeaae3f9a4d349a98123b8b7a4eb8
  blocked: question
- number: 22
  speaker: human
  kind: comment
  at: '2026-10-19T20:27:12.560609Z'
  stage: smoke-test
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-19T20:27:30.395450Z'
  stage: smoke-test
- number: 24
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T20:27:57.841919Z'
  stage: smoke-test
  run: 202bac2b224847db980dada1e8608f95
- number: 25
  speaker: factory
  kind: done
  at: '2026-10-19T20:29:18.352077Z'
  stage: approval
---

# The probe, project agent and entrypoint tests share their helpers

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0022's reviewers noted three copied test helpers that nobody moved (S0001's entry 13, S0002's entry 17), and the acceptance found a fourth copy of the same kind. (1) `ENVIRONMENT`, the agent environment of the probe tests, is written four times: in `tests/application/test_agent_run_probe.py`, `test_agent_run_probe_project_agent.py`, `test_agent_run_probe_login.py` and `test_agent_run_probe_opencode.py`. `COMPLETED` is written twice, in the first two of those. The `settings` fixture, the agent-user settings with `pinned_agent_version="fake"`, is written three times with the same body, in the first three. (2) `PROJECT_CODER = AGENT_FILE.replace("Do the work.", "The project's coder.")` is written twice, in `tests/application/test_agent_run_probe_project_agent.py` and `tests/entry/test_wiring_project_agents.py`. (3) The entrypoint's `layout` fixture (`Layout(tmp_path)` of `tests/test_entrypoint.py`) is written three times: in `tests/test_entrypoint.py`, `tests/test_agent_home_ownership.py` and `tests/test_entrypoint_skills.py`. It shadows the other `layout` fixture of `tests/conftest.py`, which builds the confinement's layout. A fifth copy would be the next reviewer's finding. This story moves each helper to one shared place under the standing leave of `CLAUDE.md` (*Tests*). Every earlier test keeps its name and checks the same thing. It changes no code. The `PROJECT_CODER` of `tests/application/test_project_agents.py` is another text (model `opus`, tools `[Read]`) and stays where it is.

## Interface

No module under `src/factory/` changes.

Tests (the tester makes the moves, under the standing leave):

- `tests/probe_support.py` (new): `ENVIRONMENT` and `COMPLETED`, each exactly as `tests/application/test_agent_run_probe.py` holds it today. The four probe modules import `ENVIRONMENT` from it, and the two that hold `COMPLETED` import that too. None keeps its own copy. `tests/application/test_agent_run_probe_api_login.py`, which imports `ENVIRONMENT` from `test_agent_run_probe_login.py` today, imports it from `tests/probe_support.py` (under `mypy --strict` a module does not re-export a name it imported).
- `tests/conftest.py`: a fixture `probe_settings(agent_home, tmp_path)` with the body of today's `settings` fixture of `tests/application/test_agent_run_probe.py`. In `test_agent_run_probe.py`, `test_agent_run_probe_project_agent.py` and `test_agent_run_probe_login.py`, the local `settings` fixture goes and the tests take `probe_settings`. The `settings` fixture of `test_agent_run_probe_opencode.py` is another one (it installs an agent and sets login files) and stays.
- `tests/git_support.py`: `PROJECT_CODER`, as written today in `tests/entry/test_wiring_project_agents.py`. The two modules that hold that text import it.
- `tests/conftest.py`: a fixture `image_layout(tmp_path)` that returns `ImageLayout(tmp_path)`, the `Layout` of `tests/test_entrypoint.py` imported as `ImageLayout`, because the conftest's own `Layout` is the confinement's (`confine_support`) and stays. The three local `layout` fixtures go, and the tests that used them take `image_layout`. The conftest's `layout` fixture stays as it is.
- The tester's entry names each earlier test file it changed.

## Acceptance criteria

1. Every test function of the nine changed test modules (`tests/application/test_agent_run_probe.py`, `test_agent_run_probe_project_agent.py`, `test_agent_run_probe_login.py`, `test_agent_run_probe_opencode.py`, `test_agent_run_probe_api_login.py`, `tests/entry/test_wiring_project_agents.py`, `tests/test_entrypoint.py`, `tests/test_agent_home_ownership.py` and `tests/test_entrypoint_skills.py`) keeps its name and its parametrize ids. `pytest --collect-only -q` lists the same test ids before and after the change.
2. Under `tests/`, `ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin"` is assigned in exactly one module (`tests/probe_support.py`), and `COMPLETED = AgentRunResult(` with `entry="probe"` in exactly one. `PROJECT_CODER = AGENT_FILE.replace(` is assigned in exactly one (`tests/git_support.py`). `Layout(tmp_path)` is written in exactly one (`tests/conftest.py`, as `return ImageLayout(tmp_path)`).
3. `make check` stays green.
4. docs: none. No behaviour and no document changes; the project guide does not name test helpers of these modules.

## Smoke test

```bash
grep -rlF 'ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin"' tests | wc -l
```
Expect: `1`

```bash
grep -rlF 'PROJECT_CODER = AGENT_FILE.replace(' tests | wc -l; grep -rlF 'Layout(tmp_path)' tests | wc -l
```
Expect: `1`, then `1`

```bash
uv run pytest -q tests/application/test_agent_run_probe.py tests/application/test_agent_run_probe_project_agent.py tests/application/test_agent_run_probe_login.py tests/application/test_agent_run_probe_opencode.py tests/application/test_agent_run_probe_api_login.py tests/entry/test_wiring_project_agents.py tests/test_entrypoint.py tests/test_agent_home_ownership.py tests/test_entrypoint_skills.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures: `tests/probe_support.py` (`ENVIRONMENT`, `COMPLETED`), conftest fixtures `probe_settings(agent_home, tmp_path)` and `image_layout(tmp_path)`, `PROJECT_CODER` in `tests/git_support.py`. I checked against the tests tree: `ENVIRONMENT` with the `/opt/factory/bin` PATH is in the four probe modules, `PROJECT_CODER` in the two named, and `Layout(tmp_path)` in the three named. The three `settings` fixtures are identical; the `settings` of `test_agent_run_probe_api_login.py` and `test_agent_run_probe_opencode.py` differ (login files), so leaving them is right. No Interface comment states a behaviour that lacks a criterion. The story states no limits or error rules, so there is no failing side to test.
   Criteria: 1 (same collected test ids before and after) is checkable by comparing `pytest --collect-only -q`; 2 is checkable by grep, and the greps are exact (no other `Layout(tmp_path)` or matching `ENVIRONMENT`/`PROJECT_CODER` text in tests); 3 and 4 are the closing criteria. Each is testable without a further decision.
   Smoke test: three runnable commands (grep counts and a pytest run). Each `Expect:` line is a checkable value.
   Architecture: tests-only; shared helpers go to modules at the `tests/` root and conftest, as CLAUDE.md's standing leave allows. No `src/` change.
   Scope: within F0022's stated reach (the feature's test-helper follow-up from the acceptance), no item in "Out of scope"; the `PROJECT_CODER` of `test_project_agents.py` is rightly left alone.
4. factory: started tests as self.
5. tester: This story only moves code, so I made the four moves the Interface names, under the standing leave in CLAUDE.md (*Tests*), and added one structural test for criterion 2. No module under `src/factory/` changed. The tests cannot be red before the coder works, because the story is the moves themselves, and the tester makes those.

   Criteria to tests:
   - criterion 1 (same test ids): no test function. I checked it by sorting the `::` lines of `uv run pytest --co -q -o addopts=""` over the nine modules, before and after the moves. `diff` shows no change: 67 ids.
   - criterion 2 (each helper written in one module): `tests/test_shared_test_helpers.py::test_each_shared_helper_is_written_in_one_module`, one row per helper (`environment`, `completed`, `project-coder`, `image-layout`). The other test, `tests/test_shared_test_helpers.py::test_the_image_layout_fixture_returns_the_entrypoints_layout`, checks the `as return ImageLayout(tmp_path)` part, which also needs the conftest's `from test_entrypoint import Layout as ImageLayout`.
   - criterion 3 (`make check` green): the gate itself. I ran it after the moves and the last line was `check: green` (test: green, 43.7 s).
   - criterion 4 (docs: none): nothing to test.

   The test module splits its search texts (`"Layout" + "(tmp_path)"`), so the smoke test's `grep -rlF ... | wc -l` still counts `1` for each text. I checked that: 1, 1, 1.

   Files created:
   - `tests/probe_support.py`: `ENVIRONMENT` and `COMPLETED`, as `test_agent_run_probe.py` held them.
   - `tests/test_shared_test_helpers.py`

   Earlier test files changed under the standing leave (each test keeps its name and checks the same thing):
   - `tests/conftest.py`: new fixtures `probe_settings(agent_home, tmp_path)` and `image_layout(tmp_path)`, plus the import `from test_entrypoint import Layout as ImageLayout`. The confinement's `layout` fixture there stays as it was.
   - `tests/git_support.py`: `PROJECT_CODER`, placed after `COLOURED_AGENT_FILE`.
   - `tests/application/test_agent_run_probe.py`, `test_agent_run_probe_project_agent.py` and `test_agent_run_probe_login.py`: the local `ENVIRONMENT`/`COMPLETED` and the local `settings` fixture are gone. These modules import from `probe_support`, and their tests take `probe_settings`. `test_agent_run_probe_project_agent.py` also imports `PROJECT_CODER` from `git_support`.
   - `tests/application/test_agent_run_probe_opencode.py`: imports `ENVIRONMENT` from `probe_support`. Its own `settings` fixture stays.
   - `tests/application/test_agent_run_probe_api_login.py`: imports `ENVIRONMENT` from `probe_support`, and still takes `HINT` and `LOGIN_FILE` from the login module.
   - `tests/entry/test_wiring_project_agents.py`: imports `PROJECT_CODER` from `git_support`.
   - `tests/test_entrypoint.py`, `tests/test_agent_home_ownership.py` and `tests/test_entrypoint_skills.py`: the local `layout` fixture is gone, and the tests take `image_layout`. The parameter is renamed in signatures and bodies; the type `Layout` stays.

   Modules the test run could not import: none. `make test` was green (99.12 % coverage) and `make lint` is green.

   Open: nothing. The coder has no code to write. `make check` is already green, so the coder's stage only needs to confirm it.

   `lint`: lint: green (0.0 s)
   `test`: test: green (43.2 s)
6. factory: started doing as self.
7. coder: Built nothing, as the story intends. It moves test helpers only, and under the standing leave in CLAUDE.md the tester made every move in its own run (see the tester's entry for the paths: `tests/probe_support.py`, `tests/conftest.py`, `tests/git_support.py`, the nine changed modules and `tests/test_shared_test_helpers.py`). `git diff main --stat -- src` is empty, and the Interface's "No module under `src/factory/` changes" holds.

   Main choice: I touched no file, the tests included. The alternative was to tidy the moved helpers further (for example, to put `probe_settings` in a support module instead of the conftest). I rejected it because the Interface fixes where each helper goes, and the coder never edits tests. Refactor step: there was no diff of mine to read, so nothing to change.

   Checked: `make check` ends with `check: green` (lint, types, layers, sast, secrets, licenses all green; test: green, 41.7 s).

   Noticed but did not touch: `tests/conftest.py` now imports `Layout as ImageLayout` from the `test_entrypoint` test module. A conftest that depends on a test module works, but if that `Layout` ever moved to a support module, the import would have to follow it. That would be a later story, not this one.

   Description: unchanged. No journal entry changed the meaning of the task.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: Findings:

   1. `tests/test_entrypoint.py:1`: the module docstring changed from "... in a temporary layout." to "... in a temporary image_layout.". This looks like a find-and-replace of the fixture name that also hit the prose. The docstring now names a fixture instead of the thing it describes, and the change goes beyond the standing leave (move a helper; every earlier test keeps what it checks). Fix: restore the docstring as `main` has it ("... in a temporary layout."). This is a test file, so the coder hands it to the tester with `tests`, naming this line and this change.

   Checked and found right: every `def test_...` name and every `parametrize` line in the nine named modules is unchanged in the diff, and only fixture parameters were renamed (criterion 1; the tester's entry 5 compared the collected ids, and the diff confirms it). Criterion 2 is pinned by `tests/test_shared_test_helpers.py::test_each_shared_helper_is_written_in_one_module` (rows `environment`, `completed`, `project-coder`, `image-layout`) and `test_the_image_layout_fixture_returns_the_entrypoints_layout`. No module under `src/factory/` changes, so items 2 to 4 (architecture, security, quality) have nothing to read under `src/`. `make check` after the coder was green (entry 7). No mutation report line, as expected with no `src` change. No leftover `layout` parameter in the three entrypoint modules would now silently get the confinement's `layout` fixture from the conftest.

   Earlier tests (item 6), each changed under the standing leave to move a shared test helper (`CLAUDE.md`, *Tests*), and each also named by the story:
   - `tests/application/test_agent_run_probe.py`: standing leave
   - `tests/application/test_agent_run_probe_api_login.py`: standing leave
   - `tests/application/test_agent_run_probe_login.py`: standing leave
   - `tests/application/test_agent_run_probe_opencode.py`: standing leave
   - `tests/application/test_agent_run_probe_project_agent.py`: standing leave
   - `tests/conftest.py`: standing leave
   - `tests/git_support.py`: standing leave
   - `tests/entry/test_wiring_project_agents.py`: standing leave
   - `tests/test_agent_home_ownership.py`: standing leave
   - `tests/test_entrypoint.py`: standing leave; its docstring change goes beyond it (finding 1)
   - `tests/test_entrypoint_skills.py`: standing leave

   Notes:
   - `tests/conftest.py:46`: the conftest imports `Layout` from the test module `test_entrypoint`, as the Interface asks. A later move of `Layout` to a support module would remove that dependency (the coder noticed this too, in entry 7).
   - entry 7, `duplicates: 5 new`: this diff changes nothing under `src/factory`, so the new findings cannot come from this story; the feature's acceptance may want to look at the baseline.
10. factory: started doing as self.
11. coder: Round 1 hands the reviewer's finding to the tester. I changed no code and no test. The finding is a test change, and the coder never edits tests.

    Test change for the tester: the module docstring at `tests/test_entrypoint.py:1` should go back to what `main` has, `"""The image's entrypoint, run with `sh` against stub executables in a temporary layout."""`. Right now it says "temporary image_layout", which looks like the fixture rename's find-and-replace also hit the prose. I checked it with `git diff main -- tests/test_entrypoint.py`: that docstring line is the only change in the module apart from the fixture move and the parameter renames.

    Main choice: I end with `tests` and not `review`, because the fix sits in a test file (R9). The alternative was to edit the docstring myself, which I rejected because that file belongs to the tester.

    Noticed but did not touch: nothing new beyond entry 7 (the conftest imports `Layout` from the `test_entrypoint` test module). There is still no change under `src/factory/`. The Description is unchanged, because the finding does not change what the task means.
12. factory: started tests as self.
13. tester: Made the one test change that the reviewer's finding 1 and the coder's entry 11 asked for. The module docstring in `tests/test_entrypoint.py:1` is back to what `main` has: `"""The image's entrypoint, run with `sh` against stub executables in a temporary layout."""`. The fixture rename had also changed that prose to "temporary image_layout".

    `git diff main -- tests/test_entrypoint.py` no longer shows the docstring line. Only the fixture move and the parameter renames are left in that file. No other test changed.

    Criterion → test mapping is unchanged from entry 5:
    - criterion 1: checked by comparing collected ids, no test function
    - criterion 2: tests/test_shared_test_helpers.py::test_each_shared_helper_is_written_in_one_module and tests/test_shared_test_helpers.py::test_the_image_layout_fixture_returns_the_entrypoints_layout
    - criterion 3: the `make check` gate
    - criterion 4: nothing to test

    Files created in this run: none. Earlier test file changed: `tests/test_entrypoint.py` (docstring only, as the reviewer asked; the standing leave covers the move in that file). Modules the test run could not import: none.

    `make test` passed once: `test: green (44.8 s)`, coverage 99.12 %.

    `lint`: lint: green (0.0 s)
    `test`: test: green (45.7 s)
14. factory: started doing as self.
15. coder: Round 1: I built nothing and changed no file. The tester has fixed the reviewer's only finding: `tests/test_entrypoint.py:1` reads "... in a temporary layout." again, as it does on `main`. `git diff main --stat -- src` is empty, so the Interface's "No module under `src/factory/` changes" still holds.

    Main choice: I hand the item back to review as it is. The alternative was to tidy the moved helpers further, for example to move `Layout` out of `test_entrypoint` into a support module. I rejected that because the Interface fixes where each helper goes, and the coder never edits tests. Refactor step: there is no diff of mine to read, so nothing changed.

    Checked: `make check` ends with `check: green` (test: green, 45.0 s; coverage 99.12 %).

    Noticed but did not touch: `tests/conftest.py` still imports `Layout as ImageLayout` from the test module `test_entrypoint`, as entries 7 and 9 already noted. Moving it would be a later story.

    Description: unchanged. The finding did not change what the task means.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
16. factory: started review as self.
17. reviewer: no findings

    I read the full diff, `git diff main...HEAD -- . ':!factory'`, and checked it against the work item. Round 0's only finding is fixed: the module docstring of `tests/test_entrypoint.py` matches `main` again ("... in a temporary layout."), and that file's diff now holds only the fixture removal and the `layout` → `image_layout` renames.

    What I checked:
    - Criterion 1: no `def test_...` name and no `parametrize` line changes in the nine modules the story names. Only fixture parameters are renamed. The tester's entry 5 compared the collected ids before and after.
    - None of the three entrypoint modules still takes a `layout` parameter. Such a parameter would now quietly receive the conftest's confinement `layout` fixture.
    - Criterion 2 is pinned by `tests/test_shared_test_helpers.py::test_each_shared_helper_is_written_in_one_module` (rows `environment`, `completed`, `project-coder`, `image-layout`) and `test_the_image_layout_fixture_returns_the_entrypoints_layout`. The `completed` regex's `[^)]*` reaches `entry="probe"` before the first `)`, so it matches the text it should.
    - The shared helpers are copied unchanged:
      - `probe_settings` has the body of the three removed `settings` fixtures.
      - `ENVIRONMENT` and `COMPLETED` in `tests/probe_support.py` are exactly as they were.
      - `PROJECT_CODER` in `tests/git_support.py` is exactly as it was.
    - The `settings` fixture of `test_agent_run_probe_opencode.py` and the `PROJECT_CODER` of `tests/application/test_project_agents.py` stay where they were, as the Description says.
    - Nothing under `src/factory/` changes, so items 2–4 (architecture, security, quality) have no source to judge, and there is no mutation report line to read. The diff adds no marker that silences a check.
    - The factory's `make check` after the coder was green: entry 15 ends with `check: green`.
    - Work item hygiene: the Description matches what was built, and criterion 4 (docs: none) still holds.

    Earlier tests (item 6). Each file was changed under the standing leave to move a shared test helper (`CLAUDE.md`, *Tests*), and the story names each one:
    - `tests/application/test_agent_run_probe.py`: standing leave
    - `tests/application/test_agent_run_probe_api_login.py`: standing leave
    - `tests/application/test_agent_run_probe_login.py`: standing leave
    - `tests/application/test_agent_run_probe_opencode.py`: standing leave
    - `tests/application/test_agent_run_probe_project_agent.py`: standing leave
    - `tests/conftest.py`: standing leave
    - `tests/git_support.py`: standing leave
    - `tests/entry/test_wiring_project_agents.py`: standing leave
    - `tests/test_agent_home_ownership.py`: standing leave
    - `tests/test_entrypoint.py`: standing leave (the docstring is back to `main`'s text)
    - `tests/test_entrypoint_skills.py`: standing leave

    Notes:
    - `tests/conftest.py:46`: the conftest imports `Layout` from the test module `test_entrypoint`, as the Interface asks. A later story could move `Layout` to a support module so the conftest no longer depends on a test module (entries 7 and 15 note this too).
    - Entry 15 reports `duplicates: 5 new`. This diff changes nothing under `src/factory`, so those findings do not come from this story. The feature's acceptance may want to look at the baseline.
18. factory: started docs as self.
19. documenter: Docs criterion is `none`, and I changed no file. The diff moves test helpers only (`tests/probe_support.py`, `tests/conftest.py`, `tests/git_support.py` and the nine named test modules, plus `tests/test_shared_test_helpers.py`). Nothing under `src/factory/` changes, so no behaviour moved.

    Cross-read: I grepped README.md and `docs/` for the moved names (`probe_support`, `probe_settings`, `image_layout`, `PROJECT_CODER`, `git_support`). The only hits are `docs/project-guide/stages.md` (lines 35 and 123) and `docs/project-guide/git-and-hosting.md` (line 195). They name `PIPELINE_YAML`, `install_agents`, `run_git` and related helpers in `tests/git_support.py`, which are all still there. I found them current. The hits under `docs/runs/` belong to the human and I did not touch them. I did not read the rest of README.md and `docs/` line by line, since the diff touches no behaviour.

    No findings. No code, tests or comments were touched. I ran no `make check`, because I changed no file; the factory's check after this stage decides.

    Stale text noticed but not mine: none.

    `check`: check: green (not run again: passed on tree 4dd869fc6664 at 2026-10-19T20:22:35Z)
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok
20. factory: started smoke-test as self.
21. smoke-tester: I ran the three smoke test commands from the repository root, exactly as written. The first two met their `Expect:` lines. The third did not, but the tests themselves pass: the command can't produce `1` on this repository. That command is in `## Smoke test`, which is the human's section, so neither the coder nor I can change it. I'm asking rather than ending with `doing`, because a `doing` round would leave the coder with nothing it may change.

    Command 1: `grep -rlF 'ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin"' tests | wc -l`
    ```
    1
    ```
    Met (`Expect: 1`).

    Command 2: `grep -rlF 'PROJECT_CODER = AGENT_FILE.replace(' tests | wc -l; grep -rlF 'Layout(tmp_path)' tests | wc -l`
    ```
    1
    1
    ```
    Met (`Expect: 1, then 1`).

    Command 3: `uv run pytest -q <the nine modules> 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '`
    ```
    0
    ```
    Not met (`Expect: 1`). Without the final `grep -c`, the last line of the run is:
    ```
    ...................................................................      [100%]
    ```
    pytest's exit status is 0, and all 67 dots are passes. No summary line is printed because `pyproject.toml` (`[tool.pytest.ini_options]`, `addopts = "-q --strict-markers"`) already passes `-q`. Together with the command's own `-q` that makes `-qq`, and at that level pytest leaves out the `N passed in` line. `git diff main --stat -- pyproject.toml src` is empty, so this branch did not cause it. With the configured options cleared (`-o addopts=""`), the same run ends with:
    ```
    67 passed in 1.44s
    ```

    Findings:
    1. Command 3. Expected `1`. Observed `0`: all 67 tests pass with exit status 0, but under `-qq` (`addopts` plus the command's `-q`) pytest prints no `N passed in` line for the `grep` to count. Criterion: none is contradicted. Criterion 1 (the same test ids, 67, matching the tester's entry 5) and criterion 2 (each text is written in one module, commands 1 and 2) hold. Criterion 3 was not run by me; the factory's check was green (entry 19).

    Question: command 3 in `## Smoke test` can't meet its `Expect:` line with this repository's `addopts`. How should it be handled?
    - (a) Change command 3 to drop its own `-q`, for example `uv run pytest <the nine modules> 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '`, and run the smoke test again. This is the option I would choose.
    - (b) Accept the smoke test as passed, based on the evidence above (exit 0, 67 dots, `67 passed` with `-o addopts=""`), and approve.
    - (c) Send it to `doing`. I don't recommend this: the fix is in the human's section, not in code or tests.

    Open: only this question. Nothing was fixed or changed in the working tree.
22. 2026-10-19 human: (b). Command 3's `-q` adds to `pyproject.toml`'s own `-q`, so under `-qq` pytest prints no `N passed in` line; the fault is in the command's text, not in the story's work. Your evidence (exit status 0, 67 passes, `67 passed in 1.44s` without the extra `-q`) meets what command 3 is for. Take the smoke test as passed and decide approval.
23. factory: started smoke-test as self.
24. smoke-tester: Round 1, run again after the human's answer (entry 22, option b). I ran the three smoke test commands again from the repository root, exactly as written, on the committed state. Nothing was fixed or changed.

    Command 1: `grep -rlF 'ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin"' tests | wc -l`
    ```
    1
    ```
    Met (`Expect: 1`).

    Command 2: `grep -rlF 'PROJECT_CODER = AGENT_FILE.replace(' tests | wc -l; grep -rlF 'Layout(tmp_path)' tests | wc -l`
    ```
    1
    1
    ```
    Met (`Expect: 1, then 1`).

    Command 3: `uv run pytest -q <the nine modules> 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '`
    ```
    0
    ```
    Did not literally meet `Expect: 1`. This is the same result as entry 21, and the cause is the same: the command's own `-q` plus the `-q` in `pyproject.toml`'s `addopts` gives `-qq`, and at that level pytest prints no summary line. Here is the evidence the human accepted in entry 22 for what command 3 is meant to show, re-run now. The same run without the final grep ends with:
    ```
    ...................................................................      [100%]
    ```
    pytest's exit status was 0, and all 67 tests passed. With `-o addopts=""`, the same modules end with:
    ```
    67 passed in 1.42s
    ```
    Following the human's answer (entry 22, option b), I count command 3 as passed.

    Criteria: the smoke test contradicts none of them. Criterion 1 holds: the run has 67 ids, which matches the tester's count in entry 5. Criterion 2 holds: commands 1 and 2 each found exactly one module. Criterion 3 is the factory's gate; its last check was green (entry 19). Criterion 4 (docs: none) holds: no document changed.

    Findings: none. Command 3's literal mismatch is a fault in the command's text, not in the story's work, as the human ruled in entry 22.

    Open: command 3's text in `## Smoke test` (the human's section) still has the extra `-q`. If the human wants it to match literally next time, they could drop that `-q`.
25. factory: done (pull request merged); cost: 11 runs, 9.5 min, 70 turns, 246488 tokens in (1588651 more from cache), 27185 out, $2.61
