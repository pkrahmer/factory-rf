# Documentation after the proof: the document check for agents, the restart's proof for the operator

<!-- proposed by feature acceptance of 2026-10-17; refine before promoting -->

## Assignment (as of log entry 1)

F0011's feature acceptance read the four documents from the top. The document check passes on them, but three things fell between the stories:

- **The project guide never mentions the document check.** Only the README and the decision log name `python -m factory.entry.check_documents`. `make check` does not run it (decision 13 of F0011). So a later story can add a stop to `STOP_TABLE`, a case to `KILL_POINT_CASES` or a path to `FAULT_PATHS`, or reword a guide, and break `documents ok` without anyone noticing. The agent who reads the guide finds the tables, but not the rule that keeps them complete.
- **A section name is stale.** `docs/project-guide.md`, in "Stops, the clock and the factory log", cites the operator guide section "Stops of one work item". Since F0011-S0004 that section has been "The stops of one work item", under "The stops".
- **The operator is not pointed to the proof.** F0011's Goal names the operator as the reader who must trust a restart. The operator guide's "A restart during a stage" says what a restart does, but not that it is proved by injection, or where the proof is. The proof lives only in the project guide's *Kill points* and *Fault-injection paths* sections.

This story is documentation only: the tester writes no tests and the coder has nothing to build. The documenter writes it from the docs criterion. The human may prefer to make the edit by hand.

## Interface

None: no code changes. Files: `docs/project-guide.md` and `docs/operator-guide.md`. `README.md` and `docs/decisions.md` are read for consistency and changed only where they contradict the new text.

## Acceptance criteria

1. `make check` stays green.
2. docs: this story is the documentation. `docs/project-guide.md` and `docs/operator-guide.md` change. Afterwards:
   - The project guide describes the document check. It names the command `uv run python -m factory.entry.check_documents`, its output (`documents ok`, or one finding per line, exit 1), and the pure rule `factory.domain.documents.check_documents`. It states what the check requires:
     - the operator guide's sections *Install*, *Configuration* and *The stops*, with a table row for each row of `STOP_TABLE` that holds the stop's id in backticks and its destination in words;
     - the project guide's sections *Kill points* and *Fault-injection paths*, with a table row for each case and each path, each with its id or test in backticks;
     - none of the phrases of `REPLACED_PHRASES` and none of the v1 words of `GLOSSARY_FORBIDDEN` outside a `## Replaced from v1` section;
     - the decision log is exempt from both lists.

     It says that `make check` does not run the check. A story that adds a row to one of the three tables, or changes one of the four documents, runs the check and ends with `documents ok`.
   - The project guide's reference in "Stops, the clock and the factory log" names the operator guide section "The stops of one work item".
   - The operator guide's "A restart during a stage" says, in a sentence or two, that recovery is proved by injection tests. Each of the six kill points is killed against a real local bare remote and restarted, and v1's thirteen fault-injection paths are each walked with one kill or stall. It names the command that runs them and points to the project guide's *Kill points* and *Fault-injection paths* sections for the cases and paths.
   - `uv run python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -n "check_documents" docs/project-guide.md
```
Expect: at least one line, naming `python -m factory.entry.check_documents`.

```bash
grep -n "Stops of one work item" docs/project-guide.md docs/operator-guide.md
```
Expect: no output (the grep is case-sensitive, so "The stops of one work item" does not match).

```bash
grep -n -i "kill point\|fault-injection" docs/operator-guide.md
```
Expect: at least one line in the section "A restart during a stage" that points to the project guide's *Kill points* or *Fault-injection paths*.

```bash
uv run python -m factory.entry.check_documents
```
Expect: the single line `documents ok`.

## Log (append only)

1. 2026-10-17 human: created.
