# The project guide split by domain

## Goal

`CLAUDE.md` tells every agent run to read `docs/project-guide.md` before it changes anything. The guide has 1,905 lines and 41 `## ` sections (2026-10-19), and the drafted features F0020 to F0024 each add to it. The file tool reads 2,000 lines by default, and the documenter's lesson says to split the guide before it gets there; the pre-checks of F0023 and F0024 recommend doing it before it passes about 1,950. A story about cost records also pays for reading the hosting service, the kernel's write guard and the thirteen fault paths. This feature splits the guide by domain, the human's step 8 of the order after F0011 (2026-10-18). `docs/project-guide/README.md` becomes the index: what every story needs (the errors, the models' configuration, the kill points and the fault-injection paths) and a list of the files. Eight files hold one domain each, read when a story touches that domain, so that every agent run reads less. It is a move, not a rewrite: each section keeps its heading and its words, and the smoke test checks the move against the old guide on `origin/main`. The document check follows the guide to its index and checks the words of every file of it. The code tree is not moved; the restructure stays deferred. Done when the story below is merged, `make check` is green and the human's change 1 is on `main`.

## Scope

- `src/factory/domain/documents.py`: `PROJECT_GUIDE` names the index, `PROJECT_GUIDE_FOLDER`, `is_guide_file`, and `check_documents` over the guide's other files (S0001).
- `src/factory/entry/check_documents.py`: reads the files beside the index (S0001).
- The tests S0001 names, and the one earlier test module named in decision 9.
- `docs/project-guide.md` moved into `docs/project-guide/`: `README.md` and the eight files of decision 2 (S0001's docs criterion).
- `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: the references to the guide, and the decision entry (S0001's docs criterion).

## Out of scope

- The move of the code tree (domains at the top, `tests/support/`, `entry` renamed `entrypoints`): deferred by the human on 2026-10-18 and not dropped. The domain files follow today's modules.
- Rewording, merging or shortening the guide's sections: a move only (decision 4). A later story that finds a section stale fixes it in its own docs criterion.
- Splitting the operator guide or the decision log: they stay single files (the human's plan).
- The template's and the todo demo's `docs/project-guide.md`: a small project keeps one file. `template/CLAUDE.md` and `tests/test_claude_files.py`, which pins it, stay as they are (decision 7).
- A lasting test of the guide's layout or of a file's length (decision 3).
- The documenter's lesson in `claude/agents/documenter.md`. It already says that the guide is an index plus one file per domain, each well under 2,000 lines, so it stays as it is.
- Every paid call: no story and no smoke test makes one.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The project guide becomes an index and one file per domain, and the document check reads them all

## The human's changes

Checked against `factory/pipeline.yml`: the coder writes `src/*`, `image/*`, `template/*` and `claude/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`. S0001 stays inside them: the code under `src/factory/`, the tests under `tests/`, the move under `docs/` (the documenter's `docs/*` holds `docs/project-guide/*`, and the kernel's folder target `docs` lets it make the folder and delete the old file). `make documents` needs no change, because it calls the command and the command reads the new path. No new dependency, no `Makefile` or `pyproject.toml` change, no `.secrets.baseline` entry, no `security/` change, no suppression marker; no structural test that reads the source, so `[tool.mutmut]` stays. The secret scan of the docs stage reads the moved text, which `make secrets` passes on `main` today. Outside the write paths:

1. Right after S0001 is merged and before the next story is started, one commit on `main` (`CLAUDE.md` and `factory/story-form.md` are protected paths). Until then the next run's agents would read a `CLAUDE.md` that names a file that is gone.
   - `CLAUDE.md`, the opening paragraph: the sentence `` `docs/project-guide.md` is the guide for agents: read it before you change anything. `` becomes:

     ```markdown
     `docs/project-guide/README.md` is the guide for agents: read it, then the files it names for the domains your story touches, before you change anything.
     ```

   - `CLAUDE.md`, *Tests*, the bullet on a pipeline definition written in a test: `` (see `docs/project-guide.md`, the pipeline definition) `` becomes `` (see `docs/project-guide/stages.md`, *The pipeline definition*) ``.
   - `CLAUDE.md`, *Docs*, the first bullet: `` `docs/project-guide.md` is the project guide for agents (R17). `` becomes:

     ```markdown
     `docs/project-guide/` is the project guide for agents (R17): the index `README.md` and one file per domain, which a story reads when it touches that domain.
     ```

   - `factory/story-form.md`, *Acceptance criteria*: `` (`README.md`, `docs/operator-guide.md`, `docs/project-guide.md`, `docs/decisions.md`) `` becomes:

     ```markdown
     (`README.md`, `docs/operator-guide.md`, the project guide under `docs/project-guide/` (its index `README.md` and its files by domain), `docs/decisions.md`)
     ```

     The headings of the form stay, so `factory-check-story` gives the same findings.
2. Before each of these drafted stories is started, its docs criterion names the file of the guide instead of `docs/project-guide.md` (the human, or a fix agent). The file follows from the index's list. A story already merged before S0001 needs nothing, because its sections move with the guide. A section a story adds goes to the file of its domain.
   - F0020-S0001, criterion 22: `docs/project-guide/agents.md` (`factory.adapters.agent_launch`, the login shell's report line, `AgentRunResult.login`). The records contract's version and `login` among the cost record's fields go to `docs/project-guide/work-items.md`, *The records contract*.
   - F0020-S0002, criterion 14: `docs/project-guide/agents.md`.
   - F0020-S0003, criterion 12: `docs/project-guide/processes-and-checks.md`, *Starting a process*.
   - F0020-S0004, criterion 19: `docs/project-guide/agents.md`, a new section *The opencode runtime* after *The agent runtime*, named in the index.
   - F0020-S0005, its docs criterion: `docs/project-guide/agents.md`.
   - F0020-S0006, criterion 15: `docs/project-guide/agents.md`, *The opencode runtime*.
   - F0020-S0007, its docs criterion: `docs/project-guide/stages.md`, *Starting a stage* (`PatientRuns`, the `Waiter` interface and its two implementations). `run_sealed`'s `run` goes to `docs/project-guide/watching.md`, under *Boundaries* in *Stops, the clock and the factory log*.
   - F0020-S0009 (deferred), its docs criterion: `docs/project-guide/watching.md`, *Boundaries* (`factory.domain.spend` and the spend records in the boundaries).
   - F0022-S0001, its docs criterion: `docs/project-guide/agents.md`, *The agent definition reader* (`ProjectAgentDefinitions` and its wiring, `AgentDefinitionReader.parse`). `is_name` and `PROJECT_AGENTS_DIRECTORY` go to `docs/project-guide/work-items.md`, *Identity, order and places of work items*. `PROTECTED_PATHS` as eleven patterns goes to `docs/project-guide/write-guard.md`, *Protected paths and the refusal*.
   - F0022-S0002, its docs criterion: `docs/project-guide/agents.md`, *The seven agents*.
   - F0023-S0001, criterion 10: `docs/project-guide/git-and-hosting.md`, *The git wrapper* and *Which feature uses which operation*. The pipeline definition's model goes to `docs/project-guide/stages.md`, *The pipeline definition*.
   - F0023-S0002, its docs criterion: `docs/project-guide/processes-and-checks.md`, *Project commands*. Where `StageFinisher` uses them goes to `docs/project-guide/stages.md`, *The stage protocol*.
   - F0024-S0001, criterion 13: `docs/project-guide/processes-and-checks.md`, *Mutation testing* and *The duplicates report*.
   - F0024-S0002, criterion 4: `docs/project-guide/processes-and-checks.md`, *Project commands*.
   - F0024-S0003, the sentence that lists the documents the documenter writes, and its docs criterion: `docs/project-guide/processes-and-checks.md`, *Mutation testing*.
   - The *Scope* bullets of F0020, F0022, F0023 and F0024 that name `docs/project-guide.md` name `docs/project-guide/` instead.
3. The check after the feature, at no cost: at the next ordinary story, the journal entries show that the agents read the index and the files of the story's domains (the documenter's entry names the files it changed). After each later acceptance, `wc -l docs/project-guide/*.md` shows each file's length. A file near 600 lines is split by the same rule in a docs criterion, and its section moves into a new file named in the index.

## Decisions taken for the human

1. **One story, not two.** The constant, the check of the guide's files and the move have to land in one story. The docs stage's `make documents` reads the path the coder names: a constant without the move makes it red at that story's docs stage, and the move without the constant makes it red at the next one. The coder's part is small (a constant, one function, a loop in the command). The move is a script, so it fits the documenter's 40 minutes. (S0001)
2. **The domains: the index and eight files, each a domain of today's code, filled by the sections whose code they describe.** The index holds what every story needs and what the document check reads there. The other sections go by the modules they describe: the outside tools (git and the hosting service), the processes and the project commands with this repository's checks, the agents, the write guard, the work items and their files, the costs, the stages from the claim to the result commit, and the watching (the evaluation, the tick, its handlers, the stops and the boundaries). Inside a file the sections keep the old guide's order, so no order is chosen by judgement. *Stops, the clock and the factory log*, which holds *Boundaries*, goes to `watching.md` and not to the index, to keep the index short: the index names *Boundaries* in its list. *Replaced from v1* goes with the agents, whose texts it renames; the document check exempts it there as it does today. Fewer files were weighed (git, processes and agents in one file of 567 lines; costs inside the work items, 458 lines) and rejected: a story about one domain would read again what it does not touch. More files were rejected too: the handlers, the pipeline definition and the stops each have one to three sections. The table (lines counted on 2026-10-19, a section's heading to the line before the next heading):

   | File | Domain | Sections | Lines |
   |---|---|---|---|
   | `README.md` | the index: what holds for all code | 4 | 125 and the index's own text |
   | `git-and-hosting.md` | git and the hosting service | 2 | 194 |
   | `processes-and-checks.md` | processes, project commands and this repository's checks | 6 | 131 |
   | `agents.md` | the agent runtime, the agent files, the shipped agents and template | 4 | 242 |
   | `write-guard.md` | write paths, the guard, the undo, the kernel's guard, the start wrapper | 5 | 181 |
   | `work-items.md` | identity, data, files, sections and form of a work item | 5 | 372 |
   | `costs.md` | cost records and bills | 2 | 86 |
   | `stages.md` | the pipeline definition and a stage from claim to result commit | 9 | 297 |
   | `watching.md` | evaluation, tick, handlers, stops and boundaries | 4 | 273 |

   Each section of today's guide, by its first line there:

   | Section | Line | Lines | File |
   |---|---|---|---|
   | Errors | 5 | 22 | `README.md` |
   | The models' configuration | 27 | 6 | `README.md` |
   | The hosting service | 33 | 78 | `git-and-hosting.md` |
   | The git wrapper | 111 | 116 | `git-and-hosting.md` |
   | Project commands | 227 | 36 | `processes-and-checks.md` |
   | Starting a process | 263 | 24 | `processes-and-checks.md` |
   | The agent runtime | 287 | 84 | `agents.md` |
   | Identity, order and places of work items | 371 | 46 | `work-items.md` |
   | The data of a work item | 417 | 135 | `work-items.md` |
   | The evaluation | 552 | 67 | `watching.md` |
   | The tick | 619 | 20 | `watching.md` |
   | The handlers of the events | 639 | 154 | `watching.md` |
   | Reading and writing a work item file | 793 | 99 | `work-items.md` |
   | Cost records | 892 | 51 | `costs.md` |
   | Bills | 943 | 35 | `costs.md` |
   | Sections of a Markdown body | 978 | 38 | `work-items.md` |
   | The form check of a story | 1016 | 54 | `work-items.md` |
   | Stops, the clock and the factory log | 1070 | 32 | `watching.md` |
   | The claim service | 1102 | 26 | `stages.md` |
   | The pipeline definition | 1128 | 91 | `stages.md` |
   | The write paths | 1219 | 56 | `write-guard.md` |
   | The guard command | 1275 | 28 | `write-guard.md` |
   | The undo | 1303 | 29 | `write-guard.md` |
   | The kernel's write guard | 1332 | 35 | `write-guard.md` |
   | The start wrapper | 1367 | 33 | `write-guard.md` |
   | The agent definition reader | 1400 | 54 | `agents.md` |
   | The shipped agents, settings and template | 1454 | 81 | `agents.md` |
   | The prompt and the request for a stage | 1535 | 39 | `stages.md` |
   | Opening a work item | 1574 | 19 | `stages.md` |
   | Starting a stage | 1593 | 24 | `stages.md` |
   | Stalls | 1617 | 30 | `stages.md` |
   | After the agent run | 1647 | 15 | `stages.md` |
   | The decision rules | 1662 | 24 | `stages.md` |
   | The stage protocol | 1686 | 29 | `stages.md` |
   | Kill points | 1715 | 58 | `README.md` |
   | Fault-injection paths | 1773 | 39 | `README.md` |
   | The duplicates report | 1812 | 31 | `processes-and-checks.md` |
   | The document check | 1843 | 10 | `processes-and-checks.md` |
   | The demos | 1853 | 20 | `processes-and-checks.md` |
   | Mutation testing | 1873 | 10 | `processes-and-checks.md` |
   | Replaced from v1 | 1883 | 23 | `agents.md` |

   The 41 sections hold 1,901 lines; the title and the opening paragraph (lines 1 to 4) become the index's own text. Sections that F0020 to F0024 add before S0001 starts go to the file whose code they describe (for example *The opencode runtime* to `agents.md`), and the smoke test checks them like the others. (S0001)
3. **The size limit: about 600 lines a file, checked once by the smoke test, not by a lasting test.** The largest file is 372 lines today, so F0020 to F0024 have room (F0020 adds mostly to `agents.md`, F0023 to `git-and-hosting.md` and `processes-and-checks.md`). 600 lines is under a third of what the file tool reads, and short enough that a story reads its domain in one call. A lasting test of the length in `make check` was rejected. A documenter who lets a file grow past it would stall at the factory's `check` after the docs stage, with nothing in the story to fix. The lesson of `claude/agents/documenter.md` and the human's look after each acceptance (change 3) keep it instead. A lasting test of the layout (every file named in the index, every heading in one file) was rejected for the same reason: the move is checked once, where it happens. (S0001)
4. **A move, byte for byte.** Each `## ` section keeps its heading and its lines, so the change can be checked as a move. The smoke test cuts the old guide on `origin/main` and every new file at their headings with `factory.domain.sections`. It checks that every old section is in exactly one file and unchanged, and that no file but the index has a section the old guide lacked. It also checks that the index names every file and every section, and that no file passes 600 lines. Two exceptions, both named in S0001's docs criterion: every `` `docs/project-guide.md` `` in the text becomes `` `docs/project-guide/` `` (today one sentence of *The write paths*), and *The document check* is rewritten for the story's change. The guide refers to sections by name ("see *The agent definition reader*") and holds no Markdown link. So the references stay as they are, and the index's list leads from a name to its file; adding links was rejected as a rewrite of every such reference, with nothing to check them. Each new file gets a title line and one sentence of its own, outside every section. (S0001)
5. **The documenter moves the text with a script, not by retyping it.** An agent that writes 1,900 lines out again can change words without noticing, and spends its budget on it. A short script in `$TMPDIR` that cuts at the headings and writes the lines unchanged makes the move exact. The smoke test would find a retyped change. (S0001)
6. **The document check reads the index as the project guide and checks the words of every other file of it.** `PROJECT_GUIDE` names `docs/project-guide/README.md`, which keeps *Kill points* and *Fault-injection paths* and their rows, as the human's plan says. Pointing the check at the index alone was rejected: it would stop checking the v1 words and the replaced phrases in every file but the index, which F0011 put under the check. So every `.md` file directly in `docs/project-guide/` gets the wording rules of `README.md`, with *Replaced from v1* exempt as before, and its findings follow the four documents in path order. The engine learns no file of the guide by name beyond the index, and no subfolder is read: the guide is one flat folder. Keeping the index at `docs/project-guide.md` beside the folder (no code change) was weighed and rejected: the human's plan names `docs/project-guide/README.md`, a folder with its index inside is one place to look, and the wording rule needs the code change anyway. A stub at the old path was rejected too: two files would name the guide, and the human's change 1 points every agent at the index. (S0001)
7. **The template and the todo demo keep a single `docs/project-guide.md`.** A new project starts small. `template/CLAUDE.md` and `demo/todo-service/project/CLAUDE.md` name that file, and `tests/test_claude_files.py` pins the template's sentence. A project splits its guide when it grows, as factory-rf does now. (Feature)
8. **The rest of the documents follow the move in the same story.** `README.md`'s *Where to look next* names the index, and the last sentence of its opening paragraph ("`docs/project-guide.md` describes each part.") names `docs/project-guide/`. Each reference of the operator guide to a section of the project guide names its file: *The guard command*, *The rules of the definition* (twice), *The form check of a story*, and *Kill points* with *Fault-injection paths*. The decision log gets an entry, and one sentence in *The project guide lives in `docs/`*. The decision log's dated entries that name `docs/project-guide.md` (F0011-S0005's) are history and stay as they are. (S0001)
9. The leave to change a test another story wrote, beyond the standing leave of `CLAUDE.md`; the tester makes exactly this change and nothing else in that module:
   - S0001: `tests/entry/test_check_documents.py` (F0011-S0005's), whose `MISSING_LINES` holds `docs/project-guide/README.md: missing` in place of `docs/project-guide.md: missing`, and whose `test_each_finding_prints_one_line_in_order_and_returns_one` expects `docs/project-guide/README.md: section 'Kill points' is missing` in place of `docs/project-guide.md: section 'Kill points' is missing`. Every other test of the document check uses the constants (`PROJECT_GUIDE`, `DOCUMENT_PATHS`) and `tests/document_texts.py`, whose `write_documents` makes the folder, so they stay as they are.
10. **Where F0025 touches F0020 to F0024.** It can be built before or after any of them. A feature built first adds sections to the single file, and they move with the rest. A feature built after it writes into the domain files, once its docs criteria are reworded (the human's change 2). No code of F0025 is touched by them: `factory.domain.documents` and `factory.entry.check_documents` are in none of their scopes. F0023's human change 1 gives `documents` 2 minutes at the docs stage. The check reads nine small files in place of one large one and takes about as long (0.2 s today). (Feature)
11. **Testing.** The check is tested with texts and files in `tmp_path`. The move is checked by the smoke test in v1.1's container, against the old guide on `origin/main` while the story is open, with no paid call. That `git show` is one of the read-only git commands the agents' settings allow. (Feature)
12. The human's answers of 2026-10-19 morning: build F0025 now, before F0020-S0005; the pre-check's edits 1 to 5 and A, B applied; after the merge a fix agent rewords the drafted stories' docs criteria (change 2).
