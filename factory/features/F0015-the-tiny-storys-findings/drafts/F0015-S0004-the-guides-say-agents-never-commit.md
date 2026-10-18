# The guides say that agents never commit, and why the factory reaps nothing

<!-- proposed by feature acceptance of 2026-10-18; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance of F0015 read the documentation as a whole and found two passages that no story owned. (1) Three passages still describe a commit by the agent. The operator guide's *What a stage run shows*, item 4, says "(or above the agent's last commit, when the agent committed)". The project guide says "above the agent's last commit when it did (those commits stay in the history)" after the stall's steps and "above the agent's last commit when it did" after the result commit's rules. Since F0014-S0006 the factory alone writes the checkout's `.git`, and the decision log says that agents never commit ("The factory alone writes the checkout's `.git`"). F0015-S0003's new project-guide bullet also says that the agent cannot commit. The guides therefore contradict each other, and the older passages describe a case that no code handles. FEATURE F0015 named the operator guide's parenthesis as a separate fault, out of its scope, and S0003's documenter did not correct it. (2) The decision log's entry "The container runtime's init reaps the processes a killed run leaves" rejects the factory as the reaper because "it would own PID 1's duties". It leaves out the reason FEATURE F0015 decision 6 gives, which is the one that matters to a later story: a PID 1 that reaps every child with `waitpid(-1)` would also reap the children `run_process` waits for through `subprocess`, and those would then find no exit status. That is a race with every project command and agent run. This story is documentation only. The documenter makes both repairs, and the tester and the coder each end with an entry that says they changed nothing.

## Interface

None: no code, no image file, no template file, no agent file and no test changes. The documents the documenter changes are `docs/operator-guide.md`, `docs/project-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: the operator guide's *What a stage run shows*, item 4, says that the factory's one commit, the result commit or the stall commit, lies directly above the stage-start commit, with no parenthesis about an agent's commit. In the project guide, the paragraph after the stall's steps and the paragraph after the result commit's rules each say that the run adds one commit above the stage-start commit, without "when the agent committed nothing" or "above the agent's last commit". Where a sentence gives a reason, it is that the agent cannot commit because the checkout's `.git` is the factory's alone (see the decision log's "The factory alone writes the checkout's `.git`"). Neither guide uses the words "agent's last commit" or "when the agent committed" any more. In the decision log's entry "The container runtime's init reaps the processes a killed run leaves", the rejected alternative "the factory as the reaper" gives the reason of FEATURE F0015 decision 6. A PID 1 that reaps every child (`waitpid(-1)`, or a child subreaper) would also reap the children that `run_process` waits for through `subprocess`, and those would then find no exit status. That is a race with every project command and agent run, in the module that starts every process. The entry's other reasons stay. No other document changes, the documents use no word the document check refuses, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -c "agent's last commit\|when the agent committed" docs/operator-guide.md docs/project-guide.md
```
Expect: two lines, `docs/operator-guide.md:0` and `docs/project-guide.md:0`.

```bash
grep -c "find no exit status" docs/decisions.md
```
Expect: `1` (or more).

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-18 human: created.
