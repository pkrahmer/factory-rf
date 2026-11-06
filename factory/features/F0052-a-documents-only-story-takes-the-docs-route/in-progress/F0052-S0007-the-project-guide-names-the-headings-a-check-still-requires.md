---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 580
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T01:04:23.755626Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T01:04:23.762263Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T01:04:39.265523Z'
  stage: intake
  run: 77da8bd4626f4feab22947f9ebb9f5f1
---

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

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names one document, `docs/project-guide/README.md` (*The files*, the sentence at line 15 that says "headings are free"), with the nine headings and their files spelled out; no code, no test. The documenter may write it.
   - Criteria: criterion 1 (nine headings, each with its file and reason), criterion 2 (the unqualified "headings are free" is gone), criterion 3 (each named heading exists today; I checked the eight present ones, and *Replaced from v1* has no section now, which the story allows with "wherever it stands" and "may be removed") and criterion 4 (`make documents` prints `documents ok`) are each testable by one check. This is a failing-side rule: criterion 2 covers the old wording being removed. Criterion 5 and the `docs:` criterion close the list.
   - Smoke test: both commands run as written. `make documents` is not pytest, so the `-q` rule does not apply. Each `Expect:` can be checked (a count of at least 1; `documents ok`). The first Expect is weak, since it counts matching lines and not all nine headings, but it is checkable.
   - Architecture: documents only, no layer or area is touched.
   - Scope: within F0052's goal (the docs route and the guide's rewrite). It is the proposed S0007 from the acceptance, and it is not in "Out of scope". Route: docs-only, because the only path the Interface changes is `docs/project-guide/README.md`.
