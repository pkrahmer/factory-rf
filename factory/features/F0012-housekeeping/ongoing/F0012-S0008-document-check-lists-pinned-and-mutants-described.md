---
stage: accept
pr: 160
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The document check's v1 words and required sections, pinned in full, and `make mutants` described

<!-- takes in the parked draft F0011-S0007 (proposed by F0011's feature acceptance of 2026-10-17), criteria 1 to 3 -->

## Assignment (as of log entry 1)

Every feature acceptance so far ran its mutation pass by hand, because the project had no `make mutants`; the human's change H5 (before this story) adds it: mutmut over the modules under `src/factory` that one feature's commits changed, `make mutants FEATURE=<id>`, outside `make check`, run by the feature acceptance. This story takes in what F0011's second hand pass found, the parked draft F0011-S0007, and makes the documents say how the target is used.

F0011's second acceptance put seven mutations into `src/factory/domain/documents.py`, and six survived. The S0005 Interface gives `GLOSSARY_FORBIDDEN` as eighteen entries in a fixed order, but tests reach only `ticket`, `lane` and `drafts/`: removing `max_rounds`, `promote`, `stages.yml`, `control surface` or `ongoing/` passes every test. It gives `PROJECT_GUIDE_SECTIONS` as `("Kill points", "Fault-injection paths")`, but the section tests run one case per name over the constant itself, so removing a name removes its case; `OPERATOR_GUIDE_SECTIONS` is held only because two tests happen to name `"Install"`.

This story pins the three tuples and tests every v1 word on its own. No production code change is expected: every criterion pins behaviour already built. The tests are new functions, and no earlier test changes. F0011-S0007's docs repair (the reference to "F0011, decision 13") is already done by F0012-S0003, which rewrote that sentence for `make documents`.

## Interface

`src/factory/domain/documents.py` does not change. Its constants and rule, as built and as the F0011-S0005 Interface gives them:

- `GLOSSARY_FORBIDDEN == ("ticket", "tickets", "lane", "lanes", "stage table", "stages.yml", "promote", "promoted", "acceptor", "demonstration", "control surface", "hardening", "memo", "lease_minutes", "max_attempts", "max_rounds", "drafts/", "ongoing/")`.
- `OPERATOR_GUIDE_SECTIONS == ("Install", "Configuration", "The stops")`.
- `PROJECT_GUIDE_SECTIONS == ("Kill points", "Fault-injection paths")`.
- For each entry of `GLOSSARY_FORBIDDEN`, an operator guide that is clean except for the line `It reads <entry> here.` gives exactly the one finding `uses the v1 word '<entry>'` for `docs/operator-guide.md`. No entry contains another entry with a word boundary on both sides, so each line gives one finding only.

Tests:

- New test functions in `tests/domain/test_documents.py`: one per tuple for criteria 1 and 2, and one parametrized over `GLOSSARY_FORBIDDEN` itself for criterion 3, with the entry as its id.
- The texts come from `tests/document_texts.py` (`operator_guide(suffix=...)`) through the module's `_with` and `_finding`. No new helper.
- No existing test changes. `test_a_v1_word_standing_alone_is_a_finding` keeps its rows, which test letter case and position.

## Acceptance criteria

1. `GLOSSARY_FORBIDDEN` equals the eighteen-entry tuple of the Interface, in that order.
2. `OPERATOR_GUIDE_SECTIONS` equals `("Install", "Configuration", "The stops")`, and `PROJECT_GUIDE_SECTIONS` equals `("Kill points", "Fault-injection paths")`, each in that order.
3. For each of the eighteen entries of `GLOSSARY_FORBIDDEN`, an operator guide that is clean except for the line `It reads <entry> here.` gives exactly the one finding `uses the v1 word '<entry>'` for `docs/operator-guide.md`. These are eighteen rows of one parametrized test. The same line in the operator guide's `## Replaced from v1` section gives no finding; that side is already tested by `test_the_replaced_section_is_exempt_from_both_lists`.
4. `make check` stays green.
5. docs: the project guide gets a short section *Mutation testing* after *The document check*: `make mutants FEATURE=<id>` runs mutmut over the modules under `src/factory` that the commits of that feature changed, found by the feature's id in the commit subjects on `origin/main`; it is not part of `make check`; the feature acceptance runs it and reads the survivors with `uv run mutmut results` and `uv run mutmut show <name>`; a feature without a changed module ends with `mutants: no module under src/factory changed by <id>`. The decision log records why it is limited to one feature's modules (a run over all of `src/factory` would take far longer than one acceptance, and a feature's acceptance can act only on its own survivors) and which commit subjects it reads (v1's and v1.1's prefixes). Outside a `## Replaced from v1` section no v1 word of the document check is used, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from factory.domain.documents import GLOSSARY_FORBIDDEN, OPERATOR_GUIDE_SECTIONS, PROJECT_GUIDE_SECTIONS
print(len(GLOSSARY_FORBIDDEN), GLOSSARY_FORBIDDEN[-1])
print(OPERATOR_GUIDE_SECTIONS)
print(PROJECT_GUIDE_SECTIONS)
"
```
Expect: three lines: `18 ongoing/`, `('Install', 'Configuration', 'The stops')` and `('Kill points', 'Fault-injection paths')`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/domain/test_documents.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

```bash
make mutants 2>/dev/null; echo "status $?"
```
Expect: two lines, `mutants: set FEATURE, as in make mutants FEATURE=F0012` and `status 2`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names concrete constants in `src/factory/domain/documents.py` with their exact values and order, the rule (`uses the v1 word '<entry>'`), and the test helpers (`_with`, `_finding`, `operator_guide(suffix=...)`), all of which exist. It states no behaviour without a criterion.
   - Criteria: 1 pins `GLOSSARY_FORBIDDEN`, 2 pins the two section tuples, 3 is one parametrized test over the eighteen entries. Each is testable by one function. The rule's passing side is criterion 3. Its exempt side (`## Replaced from v1`) is named as already tested by `test_the_replaced_section_is_exempt_from_both_lists`. Criterion 4 and the docs criterion 5 are the closing ones.
   - Demo: the three commands are runnable. Each `Expect:` line is checkable: `18 ongoing/` and the two tuples, a pytest summary line, and the two `make mutants` lines with status 2. That last one holds on a ticket branch, where FEATURE is empty.
   - Architecture: tests only, in `tests/domain/test_documents.py`, with no production change. The docs go in the project guide and the decision log, which the documenter keeps.
   - Scope: inside F0012's item 1.3 and the table row that takes in F0011-S0007's criteria 1 to 3. Nothing in "Out of scope".
3. tester: Wrote the tests for criteria 1 to 3. All new functions are in `tests/domain/test_documents.py`. No existing test changed and no new helper was added. `GLOSSARY_FORBIDDEN` was added to the module's import from `factory.domain.documents`.
   - criterion 1: tests/domain/test_documents.py::test_the_v1_words_are_the_eighteen_in_their_order
   - criterion 2: tests/domain/test_documents.py::test_the_operator_guide_sections_are_the_three_in_their_order and tests/domain/test_documents.py::test_the_project_guide_sections_are_the_two_in_their_order
   - criterion 3: tests/domain/test_documents.py::test_every_v1_word_alone_on_its_line_is_one_finding. It is parametrized over `GLOSSARY_FORBIDDEN` itself with the entry as its id, giving 18 rows. The text comes from `_with(operator=operator_guide(suffix="It reads <entry> here."))`, and the check expects exactly `[_finding(OPERATOR_GUIDE, "uses the v1 word '<entry>'")]`. The exempt side is already covered by `test_the_replaced_section_is_exempt_from_both_lists`, as the criterion says.
   Files created: none. Files changed: tests/domain/test_documents.py.
   Modules the test runner could not import: none. The tests are not red: they pin behaviour that already exists, and the Assignment expects no production change. `make test` passed (`test: green`) and `make lint` passed. For the coder this leaves only the docs criterion 5, which the documenter handles, and keeping `make check` green.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (26.7 s)
4. coder: No code change and no commit. The Assignment expects no production change: criteria 1 to 3 pin `GLOSSARY_FORBIDDEN`, `OPERATOR_GUIDE_SECTIONS` and `PROJECT_GUIDE_SECTIONS` and the v1-word rule in `src/factory/domain/documents.py`, which are already built. The tester's new functions in `tests/domain/test_documents.py` pass against the code as it is, so I left `src/factory/domain/documents.py` untouched.
      - Checked: I ran `make check` on the branch as committed and it ended with `check: green` (test: green, 28.3 s, coverage 99.51 %).
      - Refactor: there was no diff of mine to refactor, so I did none.
      - Rejected: I did not write the docs criterion 5 myself (the *Mutation testing* section in `docs/project-guide.md` and the decision-log entry). Per CLAUDE.md, the documenter stage writes those files and the coder does not.
      - Open: criterion 5 is still to do, for the docs stage.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: No findings.
   - Scope: the diff changes only `tests/domain/test_documents.py` (+39 lines). `src/factory/domain/documents.py` is unchanged, as the Assignment expects.
   - Criterion 1: `test_the_v1_words_are_the_eighteen_in_their_order` compares `GLOSSARY_FORBIDDEN` to the Interface's eighteen-entry tuple, in order.
   - Criterion 2: `test_the_operator_guide_sections_are_the_three_in_their_order` and `test_the_project_guide_sections_are_the_two_in_their_order` compare against the exact tuples. The values match `src/factory/domain/documents.py:19-20`.
   - Criterion 3: `test_every_v1_word_alone_on_its_line_is_one_finding` is one test with 18 rows, parametrized over `GLOSSARY_FORBIDDEN` with the entry as its id. The parametrization drops a row if an entry is removed, but criterion 1 pins the tuple, so the two tests together cover every entry. The test expects exactly `[_finding(OPERATOR_GUIDE, "uses the v1 word '<entry>'")]`.
     - I checked that the test line can be flagged at all: `operator_guide(suffix=...)` (`tests/document_texts.py:32-56`) puts the line after the default sections, and none of them is `Replaced from v1`.
     - The exempt side is left to `test_the_replaced_section_is_exempt_from_both_lists`, as the criterion says.
   - Existing tests: none changed. The tests reuse the existing `_with`, `_finding` and `operator_guide` helpers and add no new one.
   - Checks: according to the coder's entry, `make check` was green (coverage 99.51 %) and `make duplicates` reported 0 new findings.
   - Architecture and security: nothing to judge. The diff only adds tests and has no silencing markers.
   - Ticket hygiene: the coder's entry explains why there was no production change and why criterion 5 was left alone. Criterion 5 (the *Mutation testing* section in the project guide and the decision-log entry) is still open and is the documenter's work.
6. documenter: wrote the docs criterion; no findings. I ran only `uv run python -m factory.entry.check_documents`, which printed `documents ok`. I did not run `make check`, because I changed only documents.
   - `docs/project-guide.md`: new section *Mutation testing* after *The document check*, as the criterion asks. It covers `make mutants FEATURE=<id>`, how the modules are found, that it sits outside `make check`, and that the feature acceptance runs it. It also names `uv run mutmut results` and `uv run mutmut show <name>`, the branch-name fallback on v1's acceptance branch, and the two non-run outcomes (no `FEATURE` gives status 2; no changed module gives `mutants: no module under src/factory changed by <id>` and status 0). It uses no v1 word.
   - `docs/decisions.md`: new entry *Mutation testing is limited to one feature's modules*. It gives the reasons: a full run is too slow, and an acceptance can act only on its own survivors. It also records the subject prefixes read (v1's `ticket <id>-S<nnnn>:` and v1.1's `work item <id>-S<nnnn>:`), the 574 s trial, and the rejected alternatives. It marks the earlier *No `mutants` target, no mutmut* entry as superseded; I left that entry's text as it was.
   - Cross-read: the criterion's one-feature scope and the Makefile's `mutants` target match the new text, and the rest of `docs/project-guide.md` is untouched.
   - Not cross-read: `README.md` and `docs/operator-guide.md`. I found no mention of mutants in them, so they have nothing stale about it.
   - No contradiction between code and Interface: `src/factory/domain/documents.py` is unchanged and the tests pin its constants.

   `make check`: check: green
   `make documents`: documents ok
7. demo: I ran the three commands under `## Demo` from the repository root, in order. Each met its `Expect:` line, and there are no findings.

   1. The constants:
   ```
   18 ongoing/
   ('Install', 'Configuration', 'The stops')
   ('Kill points', 'Fault-injection paths')
   ```
   Met: the output is the three expected lines.

   2. `uv run pytest --no-header -p no:cacheprovider tests/domain/test_documents.py`:
   ```
   ........................................................................ [ 43%]
   ........................................................................ [ 87%]
   .....................                                                    [100%]
   165 passed in 0.19s
   ```
   Met: the last line is `<n> passed in <t>s`, with no failed, error or skipped count.

   3. `make mutants 2>/dev/null; echo "status $?"`:
   ```
   mutants: set FEATURE, as in make mutants FEATURE=F0012
   status 2
   ```
   Met: the two expected lines.

   Criteria re-read against the demo:
   - Criteria 1 and 2: command 1 shows the length of the tuple, its last entry and both section tuples. The full order is pinned by the tests that passed in command 2.
   - Criterion 3: its 18 rows are in the 165 passing tests.
   - Criterion 4: not re-run here. The factory runs `make check` after this stage.
   - Criterion 5 (docs): `docs/project-guide.md` has `## Mutation testing` right after `## The document check` (lines 1642 and 1652). `uv run python -m factory.entry.check_documents` printed `documents ok`.

   Nothing in the demo contradicts any criterion.
