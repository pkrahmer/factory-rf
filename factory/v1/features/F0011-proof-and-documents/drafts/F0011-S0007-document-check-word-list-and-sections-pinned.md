# The document check's v1 words and required sections, pinned in full

<!-- proposed by feature acceptance of 2026-10-17; refine before promoting -->

## Assignment (as of log entry 1)

F0011's second feature acceptance ran a hand mutation pass over the feature's code. Seven new mutations of `src/factory/domain/documents.py` went in, and six of them survived. They show the same gap that F0011-S0006 closed for `REPLACED_PHRASES`, this time in the two lists that S0006 did not touch:

- The S0005 Interface gives `GLOSSARY_FORBIDDEN` as eighteen entries in a fixed order. Tests reach only three of them: `ticket`, `lane` and `drafts/`. Removing `max_rounds`, `promote`, `stages.yml`, `control surface` or `ongoing/` from the tuple passes every test. A v1 word dropped from the list would then go unflagged in the guides.
- The S0005 Interface gives `PROJECT_GUIDE_SECTIONS` as `("Kill points", "Fault-injection paths")`. The section tests run one case per name over the constant itself, so if a name is removed, its test case goes too. Removing `Fault-injection paths` passes every test. `OPERATOR_GUIDE_SECTIONS` is held today only because two tests happen to name `"Install"`.

This story pins the three tuples and tests every v1 word on its own. No production code change is expected: every criterion pins behaviour already built and passes on today's code. The tests are new functions, and no earlier test changes. The docs criterion also repairs one reference in the project guide: it names a feature's decision number where the lasting reason is in the decision log.

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
5. docs: in the project guide's section *The document check*, the sentence saying that `make check` does not run the check gives its reason by pointing to the decision log's entry of 2026-10-17 (F0011-S0005), not to "F0011, decision 13". No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

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
grep -c "decision 13" docs/project-guide.md; uv run python -m factory.entry.check_documents
```
Expect: two lines, `0` and then `documents ok`.

## Log (append only)

1. 2026-10-17 human: created.
