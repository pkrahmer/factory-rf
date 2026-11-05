# The setup's hints name the operator guide's topic file
<!-- proposed by feature acceptance of 2026-11-05; refine before starting -->

## Description

F0051-S0010 split the operator guide into a folder of topic files. Three lines that `operator/vm/setup.sh` prints still send the operator to "the operator guide" with a section name and no file, as if the guide were still one file. These are the two hints for an installed file that differs from the checkout, and the closing `setup: done:` line. The skill's approving reference (`operator/skill/kumpel/references/approving.md`) names "the operator guide's rebuild" the same way. An operator who reads such a line now has to search eleven files. This story makes each of these four places name `docs/operator-guide/machine.md`, which holds both sections, *The machine* and *The rebuild after a merge*. The setup's steps, its exit statuses and the rest of its wording stay as they are. Three things are left out. The docstring of `src/factory/entry/wiring.py:746` ("in the operator guide's order") is not an operator's text. `docs/operator-playbook.md:82`, `demo/todo-service/README.md` and the `Makefile`'s `make mutants` example are the human's files. The two tests that pin the old hint texts are changes to tests other stories wrote, so they need the human's leave in `feature.md`.

## Interface

`operator/vm/setup.sh` (the operator's VM script), three lines:

- The `tools` step's hint ends with `(docs/operator-guide/machine.md, "The rebuild after a merge")` in place of `(operator guide, "The rebuild after a merge")`. The `service` step's hint ends the same way. Both stay on stderr (`>&2`).
- The last line reads `setup: done: build the stage image and start factory@<instance>; see "The machine" in docs/operator-guide/machine.md`.

`operator/skill/kumpel/references/approving.md`, *After a merge*: "on a VM the operator guide's rebuild" becomes "on a VM the rebuild of `docs/operator-guide/machine.md`, *The rebuild after a merge*".

The tests that pin the old texts change only their expected strings, with the leave the human gives in `feature.md`:

- `tests/vm/test_vm_setup_install_hint.py` (`HINTS`)
- `tests/vm/test_vm_setup_text.py`, the row `done-line`

New test module: `tests/guards/test_operator_guide_pointers_search.py` (criterion 3).

## Acceptance criteria

1. Each of the two differing-file hints (rows `tools` and `service`) ends with `(docs/operator-guide/machine.md, "The rebuild after a merge")`, appears exactly once in its step, and goes to stderr. No line of `operator/vm/setup.sh` holds `(operator guide, `.
2. The closing line of `operator/vm/setup.sh` is printed as `setup: done: build the stage image and start factory@%s; see "The machine" in docs/operator-guide/machine.md`. No line of the script holds `see the operator guide, `.
3. No line of a file under `operator/vm/` or `operator/skill/` that says `operator guide` lacks a path under `docs/operator-guide/` on the same line. Rows:
   - The files as they are after the story give an empty list.
   - The made-up line `see the operator guide, "The machine"` is caught.
   - The made-up line `see "The machine" in docs/operator-guide/machine.md` is not caught.
   - The made-up line `the operator guide (docs/operator-guide/README.md)` is not caught.
   - Every `docs/operator-guide/<name>.md` that such a line names exists.
4. `make check` stays green.
5. docs: `docs/operator-guide/machine.md` quotes the three new lines word for word, where it now quotes the old ones (lines 284, 295 and 296). The project guide's `operator.md`: none, because the script's layout does not change. `README.md` and `docs/decisions.md`: none, because no decision changes.

## Smoke test

```bash
grep -c 'docs/operator-guide/machine.md, "The rebuild after a merge")' operator/vm/setup.sh
```
Expect: `2`

```bash
grep -c 'operator guide, "' operator/vm/setup.sh
```
Expect: `0`

```bash
grep -c 'docs/operator-guide/machine.md' operator/skill/kumpel/references/approving.md
```
Expect: `1`

```bash
uv run pytest tests/vm/test_vm_setup_install_hint.py tests/guards/test_operator_guide_pointers_search.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal
