# A project brings its own skills and agents

## Goal

Today every project the factory builds gets the same seven agents, from v1.1's `claude/agents/` in the agent's home, and none of them can load a skill: each agent passes its tools to the runtime explicitly, and none lists `Skill`. A project of a different kind cannot bring its own coder in its repository, and it cannot bring its know-how as skills, which v1 could. This feature lets a project bring both. For each role the factory reads `factory/agents/<role>.md` from the project's `origin/main` first, as it reads the pipeline definition, and uses the shipped agent only when the project has none. A project agent replaces the shipped one whole; it never extends it. It is checked by the same rules at the same points, every tick's load and the preflight's probe, and a faulty file stops with `agent_definition_invalid` and names the project file. `factory/agents/*` becomes a protected path. Every shipped agent gets the `Skill` tool and one rule: a project's skills under `.claude/skills/` are the human's files, and where a skill contradicts the agent's own instructions, the instructions win. No agent run can add a skill or command to the agent's home that later runs would load. The factory does not check what a skill says. It is for the human who runs the factory on a project of another kind, and for the archetypes of v2, which start here, small. Done when every story below is merged and `make check` is green. The real test, a skill and a project agent each seen in a run of the todo demo, comes after the feature (the human's change 2).

## Scope

- `src/factory/domain/identifiers.py`: `is_name`, the check of an agent's name, moved out of the agent file reader (S0001).
- `src/factory/domain/paths.py`: `PROJECT_AGENTS_DIRECTORY` and `project_agent_file` (S0001).
- `src/factory/domain/write_paths.py`: `factory/agents/*` as the eleventh protected path (S0001).
- `src/factory/application/agent_runtime.py`: `AgentDefinitionReader.parse`, the definition of an agent file's text (S0001).
- `src/factory/adapters/agent_files.py`: `FrontmatterAgentDefinitionReader.parse`; `read` built on it (S0001).
- `src/factory/application/project_agents.py` (new): `ProjectAgentDefinitions`, the project's agents at `origin/main` first, the installed ones otherwise (S0001).
- `src/factory/entry/wiring.py`: the boundaries' agent definitions become the project's over the installed ones (S0001).
- `claude/agents/*.md`: `Skill` in every agent's tools, and the rule R15 on a project's skills and agents (S0002).
- `claude/settings.json`: `Skill` in the allowed tools (S0002).
- `image/entrypoint.sh`: the agent's home gets empty `skills/` and `commands/` folders of the factory's, read-only to the agent (S0002).
- `src/factory/adapters/opencode_runtime.py` (F0020's): `Skill` is left out of an opencode run instead of refused (S0002).
- The tests each story names, under `tests/`, and the earlier test modules named in decision 14.
- `README.md`, `docs/operator-guide.md`, `docs/project-guide/` and `docs/decisions.md`, from each story's docs criterion.

## Out of scope

- Extending a shipped agent: no include, no section that overrides one section of the shipped file, no merge of front matter. A project agent is a whole agent file (decision 1).
- A project's own `settings.json` (its permissions and environment): every agent run, a project agent's too, gets the shipped settings. A later story, if a project kind needs other permissions.
- Skills under the opencode runtime: in this feature only Claude Code's runs load skills; the opencode runtime leaves `Skill` out (decision 11).
- Checking what a skill says, a skill's form or its frontmatter: the skills are the human's, and Claude Code reads them (decision 13).
- The project's own `CLAUDE.md`, plugins, MCP servers, hooks and slash commands of the project: unchanged. Claude Code reads the project's `CLAUDE.md` as today.
- The other files the agent can still add to its home that `claude` reads (a user `CLAUDE.md`, `.claude.json`): the open point of the decision log stays as it is; this feature closes only the two folders that the `Skill` tool would load from (decision 10).
- A project agent per branch: the factory reads `origin/main` only, so a work item's branch never changes its own agent (decision 1).
- The demos: `demo/todo-service/project/` gets no `factory/agents/` and no `.claude/skills/`. The proof run adds them to its own seeded repository, not to `demo/` (the human's change 2); a later demo of another kind brings its own.
- The template (`template/`): unchanged; a project adds `factory/agents/` and `.claude/skills/` by hand.
- Every paid call: no story and no smoke test makes one; the proof is the human's change 2.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: A project's own agent file replaces the shipped one for its role
- S0002: The agents load a project's skills, and no run can add one to the agent's home
- S0003: The opencode runtime leaves out Skill wherever it stands in an agent's tools (proposed by an acceptance)
- S0004: The documents name a nested skills folder and the upgrade of a reused agent home (proposed by an acceptance)
- S0005: The probe, project agent and entrypoint tests share their helpers (proposed by an acceptance)
- S0006: The documents record the proof run of a project's skill and coder (proposed by an acceptance)
- S0007: The entrypoint tests take their layout from a support module (proposed by an acceptance)

## The human's changes

Checked against `factory/pipeline.yml`: the coder writes `src/*`, `image/*`, `template/*` and `claude/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`. Both stories stay inside those write paths. No new dependency, no `.secrets.baseline` entry, no `security/` change, no suppression marker, no `CLAUDE.md` or `factory/` change, no `Makefile` or `pyproject.toml` change: no story adds a structural test that reads the source, so `[tool.mutmut]` stays as it is (the one that exists, `tests/test_agent_home_wiring.py`, still finds one call of the reader, with `settings.agent_home`).

1. Before the first image built after S0002 is merged, on every instance whose `claude-home` volume is reused (`self` above all): look for `skills` or `commands` in the agent's Claude home that an agent run made earlier. The new entrypoint removes and remakes both as the factory user, and a folder the agent made with files in it may not be removable by `factory`. The entrypoint then stops with `set -e` before the instance starts.

   ```sh
   MSYS_NO_PATHCONV=1 docker exec factory-self-factory-1 ls -la /home/agent/.claude
   ```

   If either is listed, remove it as root before the rebuild:

   ```sh
   MSYS_NO_PATHCONV=1 docker exec -u root factory-self-factory-1 rm -rf /home/agent/.claude/skills /home/agent/.claude/commands
   ```

   If the rebuilt instance does not start (it restarts, and `docker logs factory-self-factory-1` shows `rm: cannot remove ...`), remove the two folders through the volume and start it again:

   ```sh
   MSYS_NO_PATHCONV=1 docker run --rm -u root -v factory-self_claude-home:/h alpine rm -rf /h/skills /h/commands
   ```

   The same for every other reused volume, such as `factory-shakedown_claude-home`.

2. After S0002 is merged: rebuild `self`, and build the demo's own instance from the same `main` (as for the shakedown run: `FACTORY_INSTANCE=shakedown`, its repository URL the repository of step 1; never `self`, which keeps building factory-rf). Then one short smoke run on the todo demo on that instance, which proves both halves once (the plan's "prove it once", about one story's cost on the subscription).
   1. A new empty repository, `pkrahmer/factory-demo-skills` (created 2026-10-19; the demo token must cover it), seeded from `demo/todo-service/` as for the shakedown run. Before the first story starts, add two files to that repository on `main` (not to `demo/` in factory-rf):
      - `.claude/skills/journal-marker/SKILL.md`:

        ```markdown
        ---
        name: journal-marker
        description: Use whenever you write your journal entry for this project.
        ---
        End your journal entry with the line `skill: journal-marker`.
        ```

      - `factory/agents/coder.md`: a copy of `claude/agents/coder.md` with one sentence added at the end of its second paragraph (the entry sentence): "Begin your entry with the words `project coder:`."
   2. Start one story of the demo (its first) and let it run through the coder's stage.
   3. Expected: the coder's journal entry begins with `project coder:`; at least one journal entry of a shipped agent (the intake or the tester) ends with `skill: journal-marker`; the factory log shows no `agent_definition_invalid`. If no entry ends with the line, read the run's transcript in `/home/agent/.claude/projects/` for a `Skill` call: no call means the skill was not offered (the tools or the settings), a call without the line means the model set it aside.
   4. In the rebuilt container: `MSYS_NO_PATHCONV=1 docker exec -u agent factory-self-factory-1 mkdir /home/agent/.claude/skills/planted` fails with `Permission denied`, and `ls -ld /home/agent/.claude/skills /home/agent/.claude/commands` shows `drwxr-sr-x` (mode `2755`: the home's setgid bit is inherited), the owner `factory` and the group `factory-work`.
   5. Then remove `factory/agents/coder.md` on that repository's `main`; the next stage of the coder gets the shipped coder again (its entry no longer begins with `project coder:`). Stop the demo's instance afterwards (not `self`).

## Decisions taken for the human

1. **A project agent replaces the shipped one whole, read from `origin/main` only.** `ProjectAgentDefinitions` reads `factory/agents/<role>.md` at `origin/main` (the pipeline definition's ref, `PIPELINE_REF`) for every read and falls back to the installed `<agent home>/agents/<role>.md` only when that file does not exist there. A branch, or a file the agent left in the work tree, never changes its own agent, for the same reason the pipeline definition is read from `origin/main`. "Replaces, never extends": the engine learns no agent's text and no section names, so a project agent that drops the shipped rules runs without them; that is the project's choice, and the decision log records it. Chosen over a merge of sections or front matter, which would need the engine to know the agent files' structure and would make two files the source of one agent. (S0001)
2. **A project may add a role.** `names()` is the union of the installed names and the names of the project's files directly in `factory/agents/` at `origin/main` (a name as the agent reader accepts it; a `README.md`, a file with another suffix or one in a subfolder is not an agent). So a role in the pipeline definition whose only agent is the project's loads, and the loader's fault `role <role>: agent is not installed` comes only when neither has it. A project agent for a role the pipeline definition does not name is listed and never run. (S0001)
3. **One rule set, one stop.** A project agent is parsed by the same reader (`parse`, the text of `read` without the file), so the applied keys, the budget and the refusals are exactly a shipped agent's; the faults of a project file name it: `factory/agents/coder.md at origin/main: <fault>`, raised as `AgentDefinitionInvalid` with the same key. At `origin/main` the loader raises and clears `agent_definition_invalid` as today, with the detail `coder: factory/agents/coder.md at origin/main: <fault>`; the tick ends there. A faulty project file never falls back to the shipped one: the human meant the project's. No new stop, no new setting. (S0001)
4. **`parse` joins the reader's interface** rather than a second reader for texts: the one implementation of `AgentDefinitionReader` gains it, and no fake implements the interface (none exists), so no test double changes. `ProjectAgentDefinitions` is an application class over the `Git` interface and the installed reader, wired once in `factory.entry.wiring`; the loader, the task composer and the preflight's probe reach it through `boundaries.agent_definitions` and change nothing. (S0001)
5. **`factory/agents/*` is the eleventh protected path**, last in `PROTECTED_PATHS`. The hook and the undo refuse and undo a write there as for `factory/pipeline.yml`; the kernel's guard allows only the write paths, and no role of factory-rf's or the template's pipeline definition reaches `factory/agents/`. The agents' rule text R14 stays as it is (it is pinned word for word by `tests/test_claude_agent_refusal.py`); S0002's new rule R15 names `factory/agents/` as the human's. (S0001, S0002)
6. **The preflight's probe runs the project's coder when it runs**: its agent is `boundaries.agent_definitions.read("coder")`, so a project coder is probed. The machine items run once per image (the preflight stamp), so a project agent added to `main` later is checked by every tick's load, not by a new probe. Chosen over clearing the stamp when `factory/agents/` changes, which would tie the stamp, a machine fact, to a project file. (S0001)
7. **`Skill` for all seven shipped agents.** The plan named the tester, coder, reviewer and documenter and left the intake, the smoke tester and the acceptance reviewer to decide. A project's skill may hold what each of them needs too (how the project's architecture reads for the intake, how to run the project for the smoke tester, the project's quality bar for the acceptance reviewer), and one rule for every agent keeps the texts and their tests uniform. It is appended last to each `tools` list. (S0002)
8. **`Skill` in the shipped settings' `allow` list**, right after `Grep`: a run has no permission prompts (`--permission-prompts none`), so a tool that needs a permission and is not allowed would be refused silently and no skill would load. Whether Claude Code 2.1.296 needs the entry is the proof run's to show (change 2); the entry costs nothing if it does not. (S0002)
9. **The rule on skills is R15 in the `## Rules` section**, one line, the same in all seven files, right after R14: the `## Lessons` bullets and R14 are pinned exactly by earlier tests, and a rule that applies to every agent belongs with the rules. Its text: the project's skills (`.claude/skills/`) and agents (`factory/agents/`) are the human's files; load a skill whose description fits the work when the tools include `Skill`; where a skill contradicts these instructions, these instructions win, and the entry names the skill and the step set aside. (S0002)
10. **No run can add a skill or a command to the agent's home.** With `Skill` in the tools, Claude Code loads user skills from `$CLAUDE_CONFIG_DIR/skills/` (the agent's `/home/agent/.claude`) and user commands from `commands/` beside it, and the confinement allows the runtime's own folder `<HOME>/.claude` (F0019). One run could then plant a skill that every later run, of every stage, loads. The entrypoint now removes and remakes both folders, empty, owned by `factory`, mode `0755` (`2755` in the image, where the home's setgid bit is inherited), at every start, as it installs `agents/`; the folder's sticky bit keeps the agent from renaming them. Chosen over `--setting-sources project`, which would also drop the shipped `settings.json` (a user setting), and over leaving it open, which turns the decision log's open point into a working route. The log line of the entrypoint stays as it is. A folder an agent made there is group-writable and is removed; one it made without group write (mode 0700) stops the entrypoint under set -e before the instance starts, which the human's change 1 prevents on a reused volume. (S0002)
11. **opencode and skills: only Claude Code's runs load skills in this feature.** F0020's opencode runtime maps the agent file's tools through `TOOL_NAMES` and refuses any other (`the opencode runtime has no tool for <tool>`), so `Skill` in every shipped agent would end every opencode run before it starts. Whether opencode 1.19.3 has a skill tool and reads `.claude/skills/` was not seen in the probe of 2026-10-17. So the opencode runtime gets `LEFT_OUT_TOOLS = frozenset({"Skill"})`: such a tool turns on no opencode tool and is not refused; every other tool outside `TOOL_NAMES` is refused as before. A later story maps `Skill` once a real opencode run shows its tool. A project agent works under opencode unchanged: the runtime builds its configuration from the same `AgentDefinition`, and F0020's preflight item `opencode` reads the agents' models through the same `boundaries.agent_definitions`, so a project agent's model is checked there too. F0020's configuration sets only the names of `OPENCODE_TOOLS`; a tool of opencode's own outside them, a skill tool among them if 1.19.3 has one, keeps opencode's default. So the factory gives no opencode run the `Skill` tool, but whether opencode loads skills by itself is not known; the empty `skills/` of the agent's home holds for it as well, and F0020's proof run (its change 6) can look. (S0002)
12. **The project's skills are read from the checkout, not from `origin/main`.** Claude Code finds `.claude/skills/` in its working directory, the work item's branch; the factory does not copy or read them. A branch differs from `main` there only by the human's own commit, because `.claude/*` is protected (the hook refuses, the undo puts it back). Chosen over copying `origin/main`'s skills into the checkout before each run, a second mechanism for a case the protection already covers. Open: `.claude/*` protects only the root. If Claude Code discovers nested `.claude/skills/` in subfolders, a stage could add one inside its own write paths (`src/.claude/skills/...`), which later stages of the work item and, after the merge, every run would load; the review and the human's merge see it in the diff. The proof run looks; a later story may protect `*/.claude/*`. (Feature)
13. **The factory does not check what a skill says.** The operator guide says so: a project's skills are its human's, like `CLAUDE.md`; a skill that contradicts the agent's instructions loses by R15, and the review and the human's approval see the result. (S0002)
14. The leaves to change tests other stories wrote, beyond the standing leave of `CLAUDE.md`; the tester makes exactly these changes and nothing else in those modules:
    - S0001: `tests/domain/test_write_paths.py`, the test `test_the_protected_paths_are_the_engines_ten_patterns`, renamed `test_the_protected_paths_are_the_engines_eleven_patterns`, whose expected tuple gains `"factory/agents/*"` as its last entry (no `[tool.mutmut]` entry names it). `tests/entry/test_wiring_boundaries.py`: in `test_build_boundaries_picks_the_concrete_adapters_and_writes_nothing`, the line that expects `FrontmatterAgentDefinitionReader` expects `ProjectAgentDefinitions`; `test_the_built_agent_definitions_are_read_from_the_agent_home` clones the `remote` fixture of `tests/conftest.py` into `settings.checkout` (with `GitCli`) before it builds the boundaries, because the names are now read at `origin/main` too, and it checks the same names. `tests/application/test_agent_definition_reader.py`: in `test_agent_definition_reader_is_abstract_with_names_and_read` the expected `__abstractmethods__` becomes `{"names", "parse", "read"}`, and in `test_agent_definition_reader_methods_are_their_docstrings_alone` the expected sorted names become `["names", "parse", "read"]`. All four keep their names.
    - S0002: `tests/shipped_agents.py`, the lists `_ALL_TOOLS` and `_TOOLS_WITHOUT_WRITE`, which gain `"Skill"` as their last entry; `tests/test_claude_files.py`, the dict `SETTINGS`, whose `allow` list gains `"Skill"` right after `"Grep"`. If F0020-S0004's test of a tool outside `TOOL_NAMES` uses `Skill` as its example, that one row's tool becomes `NotebookEdit` and its expected text with it.
    - S0003: `tests/adapters/test_opencode_left_out_tools.py`, the test `test_skill_is_left_out_and_every_other_tool_without_an_opencode_name_is_refused`, gains the four rows of S0003's criterion 1, after its three; it keeps its name and its three rows, and nothing else in the module changes.
    - S0007: `tests/test_shared_test_helpers.py`, the test `test_the_image_layout_fixture_returns_the_entrypoints_layout`, whose expected import line becomes `"from entrypoint_support import Layout as ImageLayout
"`; it keeps its name, and nothing else in the module changes. (The human, 2026-10-20.)
15. **Testing, and what only the real run shows.** The stories are tested with the factory's fakes, real local git remotes, the entrypoint in a temporary layout and the stand-ins of F0020, with no paid call; the smoke tests do the same in v1.1's container. Only the proof run (change 2) shows that Claude Code offers and loads a project skill with `--tools ...,Skill` under the shipped settings, that a model follows it, and that the agent cannot write the two folders in the real image. (Feature)
16. **Where F0022 touches F0020.** F0020 is built first. S0002 changes one thing of F0020's runtime (decision 11) and nothing of the login, the launch, the streaming or the provider limit; S0001 changes only the wiring line of `agent_definitions`, beside F0020-S0008's choice of runtime in `build_boundaries`, which it leaves as it is. F0020-S0008's `installed_models(boundaries)` reads the agent definitions, which after S0001 read git: it stays inside the lazy `opencode` item, never called at wiring time before the checkout is cloned. A test F0020 adds that calls `names()` or `read()` on `build_boundaries(...)` without a cloned checkout turns red under S0001 like `test_the_built_agent_definitions_are_read_from_the_agent_home`; S0001's tester names it, and it gets the same leave (the clone of the `remote` fixture first). (Feature)
17. The human's answers of 2026-10-19 morning: all pre-check edits applied; Skill for all seven agents and in allow kept as drafted; the proof run on the demo's own instance; nested .claude/skills/ open, checked in the proof run.
