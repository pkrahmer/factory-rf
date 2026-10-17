---
stage: tests
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
