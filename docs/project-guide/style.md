# Style of the documents

How the factory's documents read. The documenter writes to this page, and the reviewer judges the documents by it. It holds the rules for all documents, then one section for each document: the operator guide, the project guide and the README.

## Rules for all documents

1. **Write for the reader who never saw the factory's history.** Use no feature or story IDs, no version names and no "replaced in" notes. The history lives in [decisions.md](../decisions.md); a guide may point there in one line.
2. **One idea per sentence.** Split a sentence of more than about 25 words. Use at most one parenthesis per sentence, and none inside another.
3. **Explain a factory word once.** The words the factory gave its own meaning are explained in the [glossary](glossary.md) and linked at their first use in a file. Use no other private words.
4. **Say what to do, or what happens, first.** The details come after. Put the rule before its exceptions and the common case before the rare one.
5. **Round numbers where exactness does not matter.** Write "about two minutes", not "117.5 s".
6. **Examples are real and were run.** Put commands in code blocks, each followed by what it prints.
7. **Write the current truth only.** Write no changelog, no "since" and no "no longer". A removed behaviour goes from the text, with one line in the decision log.
8. **Link a file of the repository by a relative link.** Write `[process.py](../../src/factory/shared/adapters/process.py)`, never a GitHub URL and never a link to a line (`#L42`). A code block holds no links, so link the file it shows once, above the block. Write a path in this repository from its root (`tests/support/time_limits.py`, never a path that starts below the root), and start a path of another repository, such as the project the factory runs on, with a placeholder (`<project>/factory/agents/`), so that the name check reads it right.

## Runnable examples

`make documents` runs the examples that a document marks as runnable. It is the check of the docs stage; `make check` does not run it. The marked examples cover the README and every file of the operator guide and the project guide.

A runnable example is a fenced block whose info string is `console`. The blocks below are `console` blocks, so `make documents` runs them. A line that starts with `$ ` is a command. The lines below it, up to the next `$ ` line, are what it must print. Standard error counts as output.

```console
$ echo one
one
$ printf 'a\nb\n'
a
b
```

The commands of one document run in order in one new folder, so a file that the first block writes is there for the next one. Each command runs under `sh -c` with a fixed environment (`PATH`, `HOME` as an empty temporary folder, `TZ=UTC`, `LANG=C.UTF-8`) and nothing else. The folder is removed when the document is done. A command that runs past 60 seconds stops the document.

A wrong example fails `make documents` only in a file listed in `docs/checked-documents.txt`; in any other file it is printed under `Report (not checked yet):`. The test suite runs the examples of every document the check reads, so there a wrong example fails whether its file is listed or not. Every example must be right wherever it stands.

The expected output must match line by line. Two placeholders loosen it:

- `<name>` stands for any text inside one line. Use it for a time, an id or a path that changes from run to run.
- A line that holds only `...` stands for any number of lines, none included.

```console
$ echo "took $((40 + 2)) s"
took <seconds> s
$ seq 1 100
1
...
100
```

A finding says `<document>:<line>: the example printed <line>`, where the line is the first one that differs, or `the example printed nothing more` when the command printed fewer lines than the block holds.

### The fixture

The info string may name the starting point of the folder: `console fixture=<name>`. There are two. A name that does not exist is a finding, `no fixture <name>`. The commands never run in the real checkout or the real state.

- `checkout` is the default: a copy of the repository's tracked files at the checked commit.
- `instance` is a valid instance, built fresh for each document, named `docs` (`FACTORY_INSTANCE=docs`, `FACTORY_SNAPSHOTS=copy`). Its folder holds a settings file (named factory.env, one `NAME=value` line for each variable), a state folder with a healthy health file, a bare remote of the checkout and empty folders for the agent home, the workspace and the copy base. Every setting the fixture makes is in the environment of the block's commands, and every path lies in the document's temporary folder, so `$FACTORY_STATE` names a state in which `factory-health --state-directory "$FACTORY_STATE"` prints `healthy`. Set a variable on the command, such as `FACTORY_INSTANCE=Factory-1 factory-run`, to see the refusal that setting gives. The stage image and its id are placeholders that the settings check accepts; an example cannot start a container.

A command that needs the hosting service has no fixture: mark its block `console github`, and the check lists it and does not run it.

### Examples that are not run

Add a mark to the info string for an example that needs more than the check container has:

| Info string | The example needs |
| --- | --- |
| `console vm` | the factory's VM |
| `console github` | the hosting service |
| `console model` | an agent's model |

A `vm` example comes from a real run, and the text above it says where it ran. A block that runs the whole suite (`make check`, `make test`, or `pytest` without a test file, also after `uv run`) is skipped without a mark, so that the docs stage does not grow with the suite. `uv run pytest <file>` is run.

The report lists every skipped block as `<document>:<line>: not run (<kind>)`, with the kind `vm`, `github`, `model` or `suite`. A block with another info string, such as `markdown` or none, is never run.

## The operator guide

The guide is in `docs/operator-guide/`. Its reader runs an [instance](glossary.md): installs it, configures it, watches it and fixes its [stops](glossary.md). They know Linux, git and a terminal. They do not read the code.

- A task is a list of numbered steps. Each step is one action with its command. If the step needs a reason, give it in one sentence after the step.
- Every [stop](glossary.md) has the same three parts: what you see, what it means, what you do.
- Settings are tables with four columns: name, what it does, default, example.
- Name no module or class. Name a source path only if the operator edits or runs that file.

Example:

```markdown
## Install

1. Install the factory's packages:

       uv sync

2. Check the installation. The last line must be `check: green`:

       make check

3. Prepare the machine: run `sudo sh operator/vm/setup.sh --device <disk> --repository-url <url>` on a fresh Ubuntu 24.04 machine. It installs the packages, the ZFS pool, the factory and its service.

4. Set the instance's settings, as "Configuration" describes.
```

## The project guide

The guide is in `docs/project-guide/`. Its reader is an agent or a developer about to change the code of one area. They need exact names, but they must first know what a part is for.

- Each section starts with two or three plain sentences: what the part does and why it exists.
- Then come the names: the module, the class and its main function, in a code block with the signature.
- Then come the rules, one per bullet. Each is a sentence that a test could check.
- Then comes "See also", with links to the sections this one depends on.
- Code names stay exact. The prose around them follows the rules for all documents.

Example:

```markdown
## The take

After an agent's run, the factory copies back only what the agent's role may write. The agent works on its own copy of the repository (the dataset), and everything else it changed is dropped. This copy step is the take. It lives in [take.py](../../src/factory/pipeline/application/take.py), the module `factory.pipeline.application.take`.

    TakeService(boundaries, mount_point).take(stage_start, work_item_path, changed_paths) -> TakeReport

- A path goes back when the role's write paths allow it and no protected path forbids it.
- `changed_paths` come from `Snapshots.changed_paths()`, relative to `mount_point`.
- The work item's state and journal are restored from the stage-start commit.

See also: *The take's rule* in [pipeline.md](pipeline.md).
```

## The README

The reader opens the repository for the first time and decides whether to go on.

- First comes what the factory is and what it is for, in three or four sentences that a non-developer could follow.
- Then comes how to try it, in at most five commands.
- Then comes where to read next, one line per document.
- Put no settings, no exceptions and no history in it. Those belong in the guides.

Example:

```markdown
# kumpel-factory

kumpel-factory builds software from stories. You describe a feature as a few short stories. The factory hands each story to AI agents in turn: one writes the tests, one the code, one reviews it, one updates the docs. Then it opens a pull request, and you approve it or send it back.

It runs on a Linux VM or as a Cloud Run job, with Claude Code or opencode as the agents.

## Try it

    uv sync
    make check     # ends with check: green
```
