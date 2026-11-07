---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 636
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T12:53:07.765734Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T12:53:07.773191Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-07T12:53:39.103633Z'
  stage: intake
  run: 0ce00804ad524f8ba09e3b96104c90cf
  blocked: question
---

# The tests say how they are laid out

## Description

This story writes the READMEs of `tests/`, `tests/support/` and `tests/guards/`, in the form of feature decision 2: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. Each is added to `docs/checked-documents.txt`, so that its names and links are checked from now on, and the guard of the folder READMEs turns green for these folders. The facts come from the code and from the files' own docstrings and header comments, not from memory. No code and no test changes.

## Interface

- New files, each in the form of feature decision 2 (`docs/project-guide/style.md`, *Folder READMEs*):
  - `tests/README.md`
  - `tests/support/README.md`
  - `tests/guards/README.md`
- `tests/README.md` says that the tests mirror the package (`tests/<area>/<layer>/`), names each special folder in one line (`support/`, `guards/`, `agent_files/`, `entry/`, `operator_scripts/`, `vm/`) and each area folder in one line, and links to `CLAUDE.md`, *Tests*. `tests/support/README.md` says in one sentence that the folder holds the shared test helpers and links to `docs/project-guide/README.md`, *Shared test helpers*, which keeps the full list of modules and fixtures (feature decision 4). `tests/guards/README.md` says in one sentence that the folder holds the guards and links to the project guide's section on the guards. Neither lists its modules: a module line is no part of the form, and the detail stays in the guide.
- `docs/checked-documents.txt` gains each new path.
- No code changes, and no test changes but this one leave of the human's: an earlier guard whose only failure is a `README.md` of this story standing in its folder may add that README to the entries it expects, keeping its name's purpose; the entry names each such test. The story takes the docs route.

## Acceptance criteria

1. Each file of the Interface exists, opens with one sentence on what its folder holds, links to at least one guide page or document that explains it, and names every direct subfolder of its folder in one line ``- `<name>/` <one sentence>.`` (no colon, as the guard and the style page write it). The guard `tests/guards/test_folder_readmes.py` passes for each and skips none of them.
2. Every name, path and link in these files exists (the document check finds nothing), and each file is on `docs/checked-documents.txt`.
3. `make documents` ends with `documents ok (<seconds> s)`.
4. `make check` stays green.
5. docs: the files of the Interface. `docs/project-guide/README.md` keeps its list of shared test helpers unchanged. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: 1. Route conflict with the test change. `tests/guards/test_tests_layout.py::test_the_root_holds_only_conftest_and_packages` asserts that the files in `tests/` are exactly `["conftest.py"]`, so the new `tests/README.md` makes it fail. The Interface grants a leave to change such a guard, but the story takes the docs route, which has no tests stage, and the documenter's write paths (`factory/pipeline.yml`) hold no `tests/*` path beyond the three READMEs. Nobody on that route can make the change, so `make check` cannot go green. Options: (a) route the story `tests`: the tester adds `README.md` to the expected entries of that one test, and the criteria and Interface drop "docs route" (I would choose this); (b) the human changes the test in the story's branch before it starts. Please also say whether the same guard has other checks that trip on a `README.md` in `tests/`, `tests/support/` or `tests/guards/`. I looked only at the root-files test.
   2. The Interface says `tests/guards/README.md` links to "the project guide's section on the guards", but `docs/project-guide/README.md` has no such section. The guards are described in a bullet under *The files* (line 66) and in the paragraphs after it. The document check resolves heading references (S0006), so the link needs a heading that exists. Which one should it be: *The files*, or a new *Guards* section? A new section would be a docs change that criterion 5 doesn't name, since it says the guide's list stays unchanged. I would choose linking *The files*.
   3. Criterion 1 requires at least one link to a guide page, and it says `tests/support/README.md` links to *Shared test helpers*. That heading exists, so this part is fine. The criteria never name which heading `tests/README.md` links to besides `CLAUDE.md`, *Tests*. Please confirm that link target alone is enough.

   Findings of the form check: none (passed). The other checks look fine. The Interface is concrete, the smoke test is runnable, and `addopts` doesn't matter because the smoke test doesn't call pytest. The docs criterion dictates no sentences. The architecture and the scope fit feature decisions 2, 4 and 6.
