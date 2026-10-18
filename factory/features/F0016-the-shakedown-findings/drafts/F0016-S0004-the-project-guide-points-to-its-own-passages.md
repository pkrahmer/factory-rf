# The project guide points to its own passages and says what make mutants lists

<!-- proposed by feature acceptance of 2026-10-18; refine before promoting -->

## Assignment (as of log entry 1)

F0016's acceptance read `docs/project-guide.md` from the top and found three passages that say something untrue. Two are S0002's: in *The seven agents* (under *The shipped agents, settings and template*), the paragraph that starts `The texts come from v1` names the three passages that are v1.1's own text and then says "(described below):". But they are described above it, in the `## Role` bullet. The colon introduces nothing, because the next line is the parenthesis `(the table of renamed words is under "Replaced from v1")`. And the opening sentence of `## Replaced from v1` says again that "the sentences are not rewritten in other words", without the exception the earlier paragraph names. A reader who starts at that section takes the reviewer's sixth item for v1's text. The third passage is older, in `## Mutation testing`: "The target lists only the mutants it checked, not the thousands of other modules' mutants that mutmut leaves as not checked." The target does drop mutmut's `not checked` lines, but it also lists every survivor and timeout that `mutants/` keeps from earlier runs. At F0016's acceptance that meant `settings`, `git_cli`, `claude_runtime` and other modules of earlier features, which F0016 did not change. An acceptance that reads the list as its own feature's survivors misreads it. This story repairs the three passages. It is documentation only. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes, and the tester and the coder each end with an entry saying so. The decision log's entry *Mutation testing is limited to one feature's modules* records what was decided then and stays as it is.

## Interface

None: no code, image file, template file, agent file or test changes. The documenter changes one document, `docs/project-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in `docs/project-guide.md`, *The seven agents*:
   - The sentence that names the three passages of v1.1's own text points to where they are described, the `## Role` bullet above it. It no longer says `described below`, and it no longer ends with a colon before the parenthesis about the table.
   - The opening sentence of `## Replaced from v1` names the same exception: the sentence before the `reviewer`'s checklist, the checklist's sixth item and the `acceptance-reviewer`'s added sentence in its check 6. It may name them, or point to *The seven agents* for them.
   - `## Mutation testing` no longer says the target lists only the mutants it checked. It says that the target drops mutmut's `not checked` lines and lists every survivor and timeout that `mutants/` holds, including those that earlier runs left for earlier features' modules (the words `earlier features' modules` appear there). It says that the acceptance therefore reads the survivors of its own feature's modules by their module name, for example `uv run mutmut results | grep 'factory.application.stage\.'`.
   - No other document changes. The documents use no word that the document check refuses outside a `## Replaced from v1` section, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -c "described below" docs/project-guide.md
```
Expect: `0`.

```bash
grep -c "lists only the mutants it checked" docs/project-guide.md
```
Expect: `0`.

```bash
grep -c "earlier features' modules" docs/project-guide.md
```
Expect: a number of at least `1`.

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-18 human: created.
