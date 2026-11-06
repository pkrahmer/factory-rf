# The project guide names the headings a check still requires

## Description

`docs/project-guide/README.md`, *The files*, says that the guard `tests/guards/test_project_guide_files.py` requires every page to be named in that section and every area to have its page, "and that headings are free". That is true of the two guide guards since their heading tables went, but not of the guides as a whole. The guard finds the index's pages under the heading `## The files` itself, so renaming it leaves every page unnamed. The document check (`make documents`, `factory.shared.domain.documents`) requires the sections *Kill points* and *Fault-injection paths* in this index, *Install* and *Configuration* in `docs/operator-guide/install.md` and *The stops* in `docs/operator-guide/stops.md`. It also exempts a section *Replaced from v1* from its search for v1 words. And `operator/vm/setup.sh` points to *The machine* and *The rebuild after a merge* in `docs/operator-guide/machine.md`, a file the documenter may not change. A documenter of the next feature's rewrite who trusts "headings are free" renames one of them, and the check or a dangling pointer sends the story off the docs route. This story makes the sentence say which headings stay. It changes only that section; the code and the checks stay as they are.

## Interface

- `docs/project-guide/README.md`, `## The files`: the sentence on the guard keeps its first half, and "headings are free" becomes: headings are free except these, which keep their names: `## The files` in this index (the guard reads it); *Kill points* and *Fault-injection paths* in this index, *Install* and *Configuration* in `docs/operator-guide/install.md` and *The stops* in `docs/operator-guide/stops.md` (the document check requires them); *Replaced from v1* wherever it stands, which may be removed but not renamed (the document check exempts it from its search for v1 words, and the style page's rules 1 and 7 ask for its removal in the rewrite); and *The machine* and *The rebuild after a merge* in `docs/operator-guide/machine.md` (`operator/vm/setup.sh` names them). The wording and the form are the documenter's, by the style page; a list is allowed.
- No code and no test changes.

## Acceptance criteria

1. `docs/project-guide/README.md`, *The files*, names each of the nine headings of the Interface together with the file it stands in, or with "wherever it stands" for *Replaced from v1* together with "may be removed but not renamed", and the reason it keeps its name: the guard, the document check or the script.
2. The section no longer says that headings are free without these exceptions.
3. Every heading the section names exists today in the file it names: `## The files` and `## Kill points` and `## Fault-injection paths` in `docs/project-guide/README.md`, `## Install` and `## Configuration` in `docs/operator-guide/install.md`, `## The stops` in `docs/operator-guide/stops.md`, and the two headings of `machine.md`.
4. `make documents` prints `documents ok`.
5. `make check` stays green.
6. docs: `docs/project-guide/README.md`, *The files*, as above. `docs/decisions.md`: none, since nothing is decided. `docs/operator-guide/`: none, because the operator does not run the guards.

## Smoke test

```bash
sed -n '/^## The files/,/^## /p' docs/project-guide/README.md | grep -c "Kill points\|Fault-injection paths\|Configuration\|The stops\|Replaced from v1\|The rebuild after a merge"
```
Expect: a number of at least `1`; the section names the headings it keeps.

```bash
make documents 2>&1 | tail -1
```
Expect: `documents ok`

## Journal
