# The documents are checked against the code

## Goal

The documents the stages wrote are hard to read, and some of what they say is no longer true: the operator guide said `setup.sh` "makes the VM" when it prepares a fresh machine, and the acceptances of F0050 and F0051 found stale references and contradictions. Today only the tables of stops, kill points and fault paths are checked against the code. This feature makes most of what a document claims checkable, inside `make documents`, which the docs stages already run (the human, 2026-11-05):

- every code name and repository path a document writes in backticks exists;
- the settings, their defaults and their refusal messages in the operator guide agree with the settings code;
- a marked example (a command and its output) is run by the check, like a notebook that the test runner executes;
- the agents write and review documents by these rules.

Prose about behaviour stays the reviewer's to judge against the code. Today's documents will fail many of the new checks, so the checks report on every file but block only the files on a list of checked files; the rewrite (the next feature) adds each file to the list as it rewrites it. Done when every story below is merged and `make check` is green.

## Scope

- The name check: every backticked dotted name under `factory.` and every backticked repository path in the documents resolves (S0001).
- The settings check: the operator guide's settings tables agree with the settings code (S0002).
- Runnable examples: a marked block's commands run like notebook cells, in order, from a fresh fixture per document, and their output is compared (S0003); the fixture `instance` (S0006).
- The checked-files list, and a report of every file's findings (S0004).
- The agents' rules: the documenter reads the code it describes and writes runnable examples; the reviewer judges facts against the code and counts an unchecked claim as a finding (S0005).

## Out of scope

- Rewriting the documents: the next feature.
- Checking prose about behaviour by a tool.
- Examples that need the VM, GitHub or a model: they are marked as such and not run.
- `docs/decisions.md` and `docs/runs/`: history, never checked for current truth.

## Stories

The build order: S0006 comes right after S0003, since the operator guide's examples need its fixtures. S0007 comes last; it is independent of the others.

- S0001: Every name a document writes in backticks exists
- S0002: The operator guide's settings agree with the settings code
- S0003: A document's marked examples are run by the check
- S0006: The examples start from a known instance
- S0004: The checks block the listed files and report on the others
- S0005: The agents write and review documents against the code
- S0007: Each area names its guide page

## The human's changes

- **At S0005's merge:** `factory/story-form.md`, the docs criterion: it names what the reader must know afterwards, not the sentences to write.

## Decisions taken for the human

1. **Checks live in `make documents`.** The docs stages already run it, and `make check` stays fast.
2. **Report everywhere, block where rewritten.** A list of checked files (`docs/checked-documents.txt`, a document so that a docs-route story can extend it) decides which findings fail the check; the others are printed as a report. Rejected: blocking at once, which would stop every docs stage until all files are rewritten.
3. **An example says where it runs.** A marked block runs in a check container, in a temporary folder its fixture prepared (`checkout` or `instance`); the blocks of one document run in order and share it, like notebook cells, and each document starts fresh (the human, 2026-11-05). A block marked for the VM, GitHub or a model, and a block that runs the test suite, is skipped by the check and listed in the report; nobody runs them routinely, since the name and settings checks and the scripts' own tests already catch most of what they would (the human, 2026-11-05). A `vm` example is copied from a real run and says where it ran.
4. **History is exempt.** `docs/decisions.md` and `docs/runs/` keep old names and paths on purpose.
5. **Links between the documents and the code** (the human, 2026-11-05). The documents link to files by relative links, which the name check of S0001 resolves; never a GitHub URL or a line anchor, which would go stale. The way back is one line per area, in the area package's docstring (S0007), not one per module. Rewriting the module docstrings for readability is left for later (`planning/f0051-candidates.md`, item 67).
6. **Leaves for the acceptance's stories S0008, S0009 and S0012** (the human, 2026-11-06, given before they start so that no story stops for one). In each, the tester may change the earlier tests that its Interface names, in the way the Interface says, and any other earlier test whose only failure is the effect the Interface describes: in S0008 the `documents` fixture becomes a git repository and the tests that change a copied document commit the change; in S0009 a guide without a settings table gives one finding, so the earlier texts without one get a settings table; in S0012 the example runner's tests take `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS`, and repeated constants are imported. Every changed test keeps its name and what it checks, and the entry names each test it changed. Nothing else in those modules changes.
7. **A leave for the third acceptance's story S0014** (the human, 2026-11-06, given before it starts). The tester may change the `documents` fixture of `tests/conftest.py` so that it holds the repository's tracked files, built once per session; `test_the_operator_guide_folder_is_checked_per_file` so that it leaves out the `not run (<reason>)` lines; and any other earlier test whose only failure is that effect. Every changed test keeps its name and what it checks.
8. **A leave for the fourth acceptance's story S0015** (the human, 2026-11-06, given before it starts). The tester may change the four earlier tests its Interface names so that each writes its own checked list into its copy, and any other earlier test whose only failure is that the repository's list names a page. Every changed test keeps its name and what it checks.
9. **A leave for the fifth acceptance's story S0016** (the human, 2026-11-06, given before it starts). The tester may change the fixture `listed`, the helper `write_checked_list`, and any other earlier test whose only failure is that the repository's checked list already names a page the rewrite lists. Every changed test keeps its name and what it checks. Reason: the rewrite lists one page per story, and no listing of a right page may turn `make check` red.
