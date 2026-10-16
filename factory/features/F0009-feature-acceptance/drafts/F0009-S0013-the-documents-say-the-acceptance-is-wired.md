# The documents say the acceptance is wired

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance found three places in the documents that still describe F0009 as unfinished, or leave it out. They contradict the code and the other documents.

1. `docs/project-guide.md`, section "Events", the paragraph that lists the kinds, ends with "`build_handlers` registers every kind except `acceptance_due`, which belongs to F0009 (see *The handlers of the events*)". The section it points to says, as the code does, that `build_handlers` returns the handlers of all thirteen kinds and that `NOT_YET_HANDLED` is empty.
2. `docs/project-guide.md`, section "The feature acceptance", the item on `SplitByWorkItemKind`, ends with "It is registered for `hand_over`, `merged` and `closed` in `build_handlers` by F0009-S0010; until then it is not in `build_handlers`." It is registered now, and the code names no story.
3. `README.md` lists what is built so far: the stage protocol, the reading of the remote, the handlers of the human's acts, crash recovery. It does not mention the feature acceptance at all. A newcomer cannot tell that a feature whose stories are all archived gets an acceptance of its own, that an agent reviews it, and that the human's merge or close of its pull request books it accepted or refused.

This story is documentation only. It touches no code and no test.

## Interface

None. The documents and their sections:

- `docs/project-guide.md`: "Events" (the paragraph that begins "The kinds:") and "The feature acceptance" (the item on `SplitByWorkItemKind`).
- `README.md`: the first paragraph, which says what is built so far.

## Acceptance criteria

1. The paragraph of `docs/project-guide.md` that begins "The kinds:" no longer says that any kind is left out of `build_handlers`. It says that `build_handlers` registers a handler for every kind, `acceptance_due` included, and it still points to *The handlers of the events*.
2. The item on `SplitByWorkItemKind` in `docs/project-guide.md` says that it is registered for `hand_over`, `merged` and `closed` in `build_handlers`, and that the `RunGate` holds the same `closed` and `merged` instances. It no longer says "until then" or names a story.
3. `grep -n "except \`acceptance_due\`" docs/project-guide.md` finds nothing, and `grep -n "F0009-S00" docs/project-guide.md README.md docs/operator-guide.md` finds nothing.
4. The first paragraph of `README.md` names the feature acceptance among what is built, in one sentence: a feature whose stories are all archived becomes due, an acceptance reviewer runs on its own work item, and the human's merge of its pull request books it accepted while a close books it refused. The sentence points to the operator guide's "When a feature acceptance is due" for the details.
5. `make check` stays green.
6. docs: this story is the docs. The documenter cross-reads the operator guide's acceptance sections against the two changed places, so that the three documents say the same thing.

## Demo

```bash
grep -c "except \`acceptance_due\`" docs/project-guide.md; grep -c "F0009-S00" docs/project-guide.md README.md docs/operator-guide.md
```
Expect: `0` on the first line, then each file with `:0`.

```bash
grep -n -i "acceptance" README.md
```
Expect: at least one line from the first paragraph that names the feature acceptance.

## Log (append only)

1. 2026-10-16 human: created.
