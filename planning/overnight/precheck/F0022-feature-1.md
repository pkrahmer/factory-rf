# Pre-check F0022, round 1: the feature, its human's changes and its decisions

The feature `F0022-a-project-brings-its-own-skills-and-agents`, its two stories and the drafter's brief, checked against v1.1's roles and forms, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml`, `image/` (the Dockerfile, compose, entrypoint, sudoers), the code the stories touch, F0020's drafted stories (S0004, S0006, S0008 above all) and F0021's state (S0001 to S0003 done, S0004 in progress, S0005 and S0006 in the backlog). Both stories were prototyped in a copy of the repository and the whole test suite run in a throwaway container of v1.1's image. The stories' own results are in `F0022-S0001-1.md` and `F0022-S0002-1.md`.

## The stories in short

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 a project's agent file replaces the shipped one | question (2) | the coder stops on two unleaved tests; three edits |
| S0002 the agents load skills, the agent's home gets none | accepted | three small edits (an owner row, two docs wordings) |

## Order and sizing

- The order is right: S0002's R15 and its docs name `factory/agents/` from S0001. Each story is independent in its code.
- Time is no risk (F0021's slowest runs took minutes against a 40-minute `time_limit`). Money: S0001's tester gets 8 modules and 13 behavioural criteria at a 2 USD budget; F0021's testers spent 1.19 to 1.57 USD on stories of that size. It fits, with little room; no split. S0002 is small.
- Leaves: decision 14 is exact for S0002 (the prototype breaks nothing else) and incomplete for S0001. Adding `parse` to `AgentDefinitionReader` also turns two tests of `tests/application/test_agent_definition_reader.py` red, which pin the interface's methods as `{"names", "read"}`. Without that leave the coder ends with `question` (fix below).

## The human's changes

- Write paths: correct as stated. The coder's `src/*`, `claude/*`, `image/*`; the tester's `tests/*`; the documenter's `README.md`, `docs/*`. No `Makefile`, `pyproject.toml`, `CLAUDE.md`, `factory/` or `security/` change; `[tool.mutmut]` needs none (the structural test `tests/test_agent_home_wiring.py` still finds one call, nested in the new one, seen).
- Change 1 (old `skills`/`commands` on a reused `claude-home`): needed, and safe in the common case. The home is `3775 factory:factory-work` (seen in the image). A folder an agent made is group `factory-work` and group-writable (the sudoers `umask 0002`, the setgid bit), so `factory`, whose group is `factory-work`, removes it. `rm -rf` fails only on a folder the agent made without group write, such as `0700` from `mkdtemp` or a `chmod`. Then `set -e` ends the entrypoint before its log line, and `restart: unless-stopped` restarts it in a loop. There `docker exec` no longer works on a container that keeps restarting. Add the fallback through the volume (text below); the volumes are `factory-self_claude-home` and `factory-shakedown_claude-home` (seen).
- Change 2 (the proof run): three faults.
  - It does not say which instance runs the demo. `self` builds factory-rf, so the demo needs its own instance from the same `main`, as for the shakedown run.
  - Step 4's expected `drwxr-xr-x` is wrong. In the image the two folders inherit the home's setgid bit, and GNU `chmod 0755` keeps it on a directory: `ls -ld` shows `drwxr-sr-x factory factory-work` (seen in a container of v1.1's image: `2755 drwxr-sr-x`). The agent still cannot write there or rename them.
  - Step 5's "Stop the instance afterwards" must name the demo's instance, never `self`.
- After S0001 is merged no rebuild is needed for factory-rf (it has no `factory/agents/`). After S0002 the rebuild of change 2 is what brings the texts and the entrypoint into effect, as the change says.

## The decisions

1. Replaces whole, `origin/main` only: right. Every read after the tick's fetch sees the same ref as the pipeline definition. A running stage keeps the agent it started with.
2. A project may add a role: right; criterion 8 pins the four kinds of file that are left out.
3. One rule set, one stop, no fallback: right; the stop's detail `coder: factory/agents/coder.md at origin/main: <fault>` comes from the loader's format unchanged (prototype).
4. `parse` on the interface: right, but "no test double changes" is not the whole story: the interface's own structural tests pin its two methods (fix in decision 14).
5. The eleventh protected path: right. `fnmatchcase` gives criterion 2's rows; it collides with no work item (under `factory/features/`), no factory write (`factory/stops.jsonl`, the journals, the cost records) and no role's write path in factory-rf's, the template's or the demo's pipeline definition.
6. The probe runs the project's coder once per image: right. The preflight runs after the tick's fetch and load, and the instance clones before its first tick, so the new reader's `GitError` never comes earlier than the load's own.
7. `Skill` for all seven agents: right. It is pinned through `tests/shipped_agents.py`, and costs nothing where a project has no skills.
8. `Skill` in `allow`: right. With `--permission-mode auto` it may not be needed; it costs nothing.
9. R15 in the Rules: right. The text uses no banned word, R14 stays word for word and the anchors stay (prototype: every text test passes).
10. The home closed by the entrypoint: right, and the route is real. The home is the factory's with the sticky bit, so the agent cannot rename or remove the folders. The folders are the factory's and not group-writable, so the agent cannot write into them. Two precisions: the mode in the image is `2755`, not `0755` (above), and `rm -rf` under `set -e` can stop the start on a reused volume (change 1 and its fallback). A planted symbolic link named `skills` is removed as a link, not followed.
11. opencode leaves `Skill` out: right against F0020-S0004 as drafted. `tools` maps through `TOOL_NAMES` and refuses the rest, the configuration sets every name of `OPENCODE_TOOLS`, and the constructor and the events of S0002's smoke block 3 are S0004's own. S0004's criterion 2 names no example tool, so the conditional leave of decision 14 is the right form. One sentence goes too far: F0020's configuration sets only the twelve names of `OPENCODE_TOOLS`. A skill tool of opencode's own, if 1.19.3 has one, keeps opencode's default, so "only Claude Code's runs load skills" is not known. Reword (below); the entrypoint's empty `skills/` protects that case too.
12. Skills from the checkout: right for `.claude/skills/` at the root. One open route to record: if Claude Code 2.1.296 discovers nested `.claude/skills/` in subfolders (newer versions do, for monorepos; not checked here), a coder or tester could add `src/.claude/skills/...` or `tests/.claude/skills/...` inside its own write paths. `.claude/*` protects only the root (it does not match `src/.claude/x`). Later stages of the same work item would then load that skill, and every run after the merge. The reviewer and the human's merge see it in the diff. Recommended: record it in this decision as open, and let the proof run look; a later story may add `*/.claude/*` as a protected path. Not recommended now: a twelfth pattern in S0001, which would reword decision 5, its test's name and several texts for a route not yet seen.
13. The factory does not check skills: right.
14. The leaves: S0002's are exact. S0001's lacks `tests/application/test_agent_definition_reader.py` (text below).
15. Testing: right; no story or smoke test makes a paid call (checked: block 3 uses a stand-in).
16. Where F0022 touches F0020: right as far as it goes. Two more points:
    - F0020-S0008's `installed_models(boundaries)` reads `names()` and `read()`. After S0001 these read git, so `installed_models` must stay inside the lazy item (as `agent_run_probe_item` is, a `lambda` in `machine_extras`). An eager call at wiring time, before the clone, would raise `GitError` at the instance's start. Its "`[]` when the agent definitions cannot be read" catches `AgentDefinitionError`, not `GitError`.
    - After F0020 is merged, look in its new tests for `build_boundaries(...)` followed by `agent_definitions.names()` or `read()` on settings without a cloned checkout. Such a test turns red under S0001 like `test_the_built_agent_definitions_are_read_from_the_agent_home`, and needs the same leave.

## Where F0022 touches F0020 and F0021

- F0020 (built before F0022): S0002 changes one thing of the opencode runtime (decision 11); S0001 changes the wiring line beside S0008's choice of runtime. The notes above go into decision 16; no F0020 story needs to change.
- F0021: S0005 changes `claude/agents/reviewer.md`'s `## Role` only. S0002 adds `Skill` to the reviewer's `tools` and R15 to its `## Rules`, other lines, so the edits do not overlap and no test pins both. S0004 (in progress, the refused tool calls) and S0006 (the records contract) touch nothing of F0022; F0022 changes no model of the contract. No story needs a note.

## Points for the human, with recommended answers

1. The leave of `tests/application/test_agent_definition_reader.py` for S0001: (a) add it; (b) keep `parse` off the interface. Recommended: (a) (see `F0022-S0001-1.md`).
2. The proof run's instance: (a) the demo runs on its own instance (the shakedown instance, rebuilt from the same `main`), and step 4 checks `self`'s rebuilt container; (b) `self` is pointed at the demo for the proof. Recommended: (a): `self` keeps building factory-rf.
3. Nested project skills (decision 12): (a) record the route as open and look in the proof run; (b) add `*/.claude/*` in S0001 now. Recommended: (a).
4. opencode and skills (decision 11): (a) reword as below; (b) as drafted. Recommended: (a).

## Verdict

Feature accepted with edits: extend decision 14's S0001 leave (required: the coder stops without it). Fix change 2's instance, its expected mode and its stop. Add change 1's fallback. Reword decisions 10 and 11, extend decisions 12 and 16.

Edit, decision 14, the S0001 bullet: insert before "Both keep their names.":

```markdown
`tests/application/test_agent_definition_reader.py`: in `test_agent_definition_reader_is_abstract_with_names_and_read` the expected `__abstractmethods__` becomes `{"names", "parse", "read"}`, and in `test_agent_definition_reader_methods_are_their_docstrings_alone` the expected sorted names become `["names", "parse", "read"]`.
```

and change "Both keep their names." to "All four keep their names."

Edit, *The human's changes*, change 1, append after the second code block:

```markdown
   If the rebuilt instance does not start (it restarts, and `docker logs factory-self-factory-1` shows `rm: cannot remove ...`), remove the two folders through the volume and start it again:

   ```sh
   MSYS_NO_PATHCONV=1 docker run --rm -u root -v factory-self_claude-home:/h alpine rm -rf /h/skills /h/commands
   ```

   The same for every other reused volume, such as `factory-shakedown_claude-home`.
```

Edit, change 2, replace its first line "After S0002 is merged: rebuild `self`, then one short smoke run on the todo demo, which proves both halves once (the plan's "prove it once", about one story's cost on the subscription)." with:

```markdown
2. After S0002 is merged: rebuild `self`, and build the demo's own instance from the same `main` (as for the shakedown run: `FACTORY_INSTANCE=shakedown`, its repository URL the repository of step 1; never `self`, which keeps building factory-rf). Then one short smoke run on the todo demo on that instance, which proves both halves once (the plan's "prove it once", about one story's cost on the subscription).
```

Edit, change 2, step 4, replace "shows `drwxr-xr-x` and the owner `factory`." with:

```markdown
shows `drwxr-sr-x` (mode `2755`: the home's setgid bit is inherited), the owner `factory` and the group `factory-work`.
```

Edit, change 2, step 5, replace "Stop the instance afterwards." with "Stop the demo's instance afterwards (not `self`)."

Edit, decision 10, replace "empty, owned by `factory`, mode `0755`, at every start," with:

```markdown
empty, owned by `factory`, mode `0755` (`2755` in the image, where the home's setgid bit is inherited), at every start,
```

and append: `A folder an agent made there is group-writable and is removed; one it made without group write (mode 0700) stops the entrypoint under set -e before the instance starts, which the human's change 1 prevents on a reused volume.`

Edit, decision 11, append:

```markdown
F0020's configuration sets only the names of `OPENCODE_TOOLS`; a tool of opencode's own outside them, a skill tool among them if 1.19.3 has one, keeps opencode's default. So the factory gives no opencode run the `Skill` tool, but whether opencode loads skills by itself is not known; the empty `skills/` of the agent's home holds for it as well, and F0020's proof run (its change 6) can look.
```

Edit, decision 12, append:

```markdown
Open: `.claude/*` protects only the root. If Claude Code discovers nested `.claude/skills/` in subfolders, a stage could add one inside its own write paths (`src/.claude/skills/...`), which later stages of the work item and, after the merge, every run would load; the review and the human's merge see it in the diff. The proof run looks; a later story may protect `*/.claude/*`.
```

Edit, decision 16, append:

```markdown
F0020-S0008's `installed_models(boundaries)` reads the agent definitions, which after S0001 read git: it stays inside the lazy `opencode` item, never called at wiring time before the checkout is cloned. A test F0020 adds that calls `names()` or `read()` on `build_boundaries(...)` without a cloned checkout turns red under S0001 like `test_the_built_agent_definitions_are_read_from_the_agent_home`; S0001's tester names it, and it gets the same leave (the clone of the `remote` fixture first).
```
