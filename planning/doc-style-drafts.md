# Style guides for the three documents (chosen 2026-11-05)

The human chose one style per document on 2026-11-05, from three samples each: numbered steps for the operator guide, idea first and then the API for the project guide, and "what it is for, then try it" for the README. Each guide has rules common to all three documents and rules of its own, with the chosen sample as its example. Next: the guides go into the repository (a style page the documenter reads), and a later feature rewrites the documents to them, one story per file.

## Rules for all three documents

Rules 8 to 10 came from the human's review of the first samples on 2026-11-05: they read well, but their examples were not run, some examples were invented, and some facts an operator or an agent needs were cut.

1. **Write for the reader who never saw the factory's history.** No feature or story IDs (F0049, S0003), no "v1", "v1.1" or "replaced in v1.2", no "decision 6". The history lives in `docs/decisions.md`; a guide may point there in one line.
2. **One idea per sentence.** A sentence of more than about 25 words is split. At most one parenthesis per sentence, and none inside another.
3. **Explain a factory word once.** The words the factory gave its own meaning (work item, stage, take, base, dataset, stall, stop, lease, claim, round cap, write paths) are explained in one glossary and linked at their first use in a file. No other private words (no "relay", "lean route", "gate").
4. **Say what to do or what happens first, the details after.** The rule before its exceptions; the common case before the rare one.
5. **Round numbers where exactness does not matter** ("about two minutes", not "117.5 s").
6. **Examples are real and were run.** Commands in code blocks, each followed by what it prints.
7. **The current truth only.** No changelog, no "since", no "no longer". A removed behaviour goes, with one line in the decision log.
8. **Facts come from the code, not from the old text.** A rewrite reads the code it describes. Every name, command, setting and rule of the old text is still in the new one, or moved on purpose to a reference section; the reviewer compares both texts and the code, not only the style.
9. **Keep the detail, move it.** Exact messages, limits, orders and edge cases are not cut for brevity. The main text says what matters to most readers; a section called *Reference* at the end of the file holds the rest.
10. **Every example was run, and shows where.** A command is run as shown, on the machine the text names (the VM, a laptop, a temporary directory), and its output is copied, not written by hand. Example values are real ones from this repository or the VM, or clearly marked as placeholders (`<your repository>`). Times say where they were measured.

## The operator guide (`docs/operator-guide/`)

The reader runs an instance: installs it, configures it, watches it and fixes its stops. They know Linux, git and a terminal; they do not read the code.

- Tasks are numbered steps, each step one action with its command; the reason, if needed, in one sentence after the step.
- Every stop has the same three parts: what you see, what it means, what you do.
- Settings are tables: name, what it does, default, example.
- No module or class names (`TakeService`), no source paths except the files the operator edits or runs.

Example (the chosen style):

```markdown
## Install

1. Install the factory's packages:

       uv sync

2. Check the installation. The last line must be `check: green`:

       make check

3. Prepare the VM with `operator/vm/setup.sh`. It creates the VM, installs the factory and its service, and builds the image the agents run in. See "The machine".

4. Set the instance's settings, as "Configuration" describes.

Use a repository that the older factory never worked in: the factory does not recognise the older factory's work items.
```

## The project guide (`docs/project-guide/`)

The reader is an agent (or a developer) about to change the code of one area. They need exact names, but they also need to know what a part is for before they read its API.

- Each section starts with two or three plain sentences: what this part does and why it exists.
- Then the names: the module, the class and its main function, in a code block with the signature.
- Then the rules, one per bullet, each a sentence a test could check.
- Then "See also", with links to the sections it depends on.
- Code names stay exact; the prose around them follows the common rules.

Example (the chosen style):

```markdown
## The take

After an agent's run, the factory copies back only what the agent's role may write. The agent works on its own copy of the repository (the dataset), and everything else it changed is dropped. This copy step is the take.

    TakeService(boundaries, mount_point).take(stage_start, work_item_path, changed_paths) -> TakeReport

- A path goes back when the role's write paths allow it and no protected path forbids it.
- `changed_paths` come from `Snapshots.changed_paths()`, relative to `mount_point`.
- The work item's state and journal are restored from the stage-start commit.

See also: *The take's rule* (`pipeline.md`), *The container environment*.
```

## The README

The reader opens the repository for the first time and decides whether to go on.

- First: what the factory is and what it is for, in three or four sentences a non-developer could follow.
- Then: how to try it, in at most five commands.
- Then: where to read next, one line per document.
- No settings, no exceptions, no history; those belong in the guides.

Example (the chosen style):

```markdown
# kumpel-factory

kumpel-factory builds software from stories. You describe a feature as a few short stories. The factory hands each story to AI agents in turn: one writes the tests, one the code, one reviews it, one updates the docs. Then it opens a pull request, and you approve it or send it back.

It runs on a Linux VM or as a Cloud Run job, with Claude Code or opencode as the agents.

## Try it

    uv sync
    make check     # ends with check: green
```
