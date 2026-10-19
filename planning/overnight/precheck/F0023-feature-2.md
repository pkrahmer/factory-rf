# Pre-check F0023, round 2: the feature after its edits

`feature.md` and both stories were checked against today's `main` (`cfc40e6a`; F0020-S0001 to S0005 and F0025 merged), the split project guide (`docs/project-guide/README.md` and its eight files), `factory/pipeline.yml`, `CLAUDE.md` and the drafted F0020-S0006 to S0008, F0022, F0024 and F0026. Both stories were prototyped again and the suite run in throwaway containers: see `F0023-S0001-2.md` and `F0023-S0002-2.md`.

## The stories

| Story | Intake (predicted) | Findings |
|---|---|---|
| S0001 | accepted; a possible question on the `{`/`}` and blank rows | `is_inside_checkout` re-export fails `mypy --strict` (required); three rows; the provider-limit test of the contract leave; one docstring |
| S0002 | accepted | the split guide's *Boundaries* field list and index line missing from the docs criterion; S0001's "does nothing yet"; two docstrings |

## Checked and right

- Round 1's feature edits are all in: change 1's `not_read` list and reason, change 3's wording, and decisions 3, 10, 12, 14, 15 and 16.
- Change 1 against today's `factory/pipeline.yml`: the `project_commands` block it replaces is exactly today's five commands. The leases hold: docs 40 + 15 + 3 + 2 = 60, doing 40 + 15 + 5 = 60. `docs/*.md` covers the split guide's files under `docs/project-guide/`, since `*` crosses `/`. `docs/runs/` holds only `.md` files today.
- Change 2 against today's `CLAUDE.md`: both sentences it replaces are there word for word. Change 3's three expected lines match the targets' last lines (`check: green`, `secrets: green (<s> s)`, `documents ok`).
- The order with the other features: no drafted story of F0020, F0022, F0024 or F0026 raises the records contract, adds a git operation, or changes `CheckResult`, `ProjectCommandDefinition` or `StageFinisher`'s checks. So `"1.3"` and "twenty-fourth" hold. F0024 builds on `command_line` and `known-results.jsonl` after this feature, consistently.
- No decision contradicts a story.

## Findings

1. Decision 14 still says "`"1.0"` today". Today `main` holds `"1.2"`.
2. Decision 15 (S0001) names `tests/entry/test_contract.py`, which holds no version literal, and not `tests/domain/test_contract_provider_limit.py`, which holds two. That test is named `..._at_version_1_2` (see S0001, edit 3).
3. *Scope* misses S0001's changes to `src/factory/domain/write_paths.py` and `src/factory/domain/confinement.py` (the move of `is_inside_checkout`, S0001's edit 1).

## Verdict

Ready to build after the stories' edits (S0001: 1 to 4; S0002: 1 and 2) and these three feature edits. None of them needs a decision of the human.

Edit, decision 14: replace "by F0021's decision 15: `"1.0"` today, `"1.2"` after F0020-S0001 and S0005, so `"1.3"`." with "by F0021's decision 15: `"1.2"` on `main` since F0020-S0001 and S0005, so `"1.3"`."

Edit, decision 15, the S0001 bullet: replace "In the test modules of F0021-S0006 (`tests/domain/test_contract.py`, `tests/entry/test_contract.py`) and of any later story that pins the records contract's version as a literal, each such literal becomes the new value; nothing else changes there." with:

```markdown
In `tests/domain/test_contract.py` (F0021-S0006, one `"1.2"`), `tests/domain/test_contract_provider_limit.py` (F0020-S0005, two `"1.2"`) and any later test module that pins the records contract's version as a literal, each such literal becomes `"1.3"`; the test names and module docstrings that say `1.2` stay, as they name the version that brought `provider_limit`; nothing else changes there.
```

Edit, *Scope*, after the `pipeline_definition.py` bullet, insert:

```markdown
- `src/factory/domain/write_paths.py` and `src/factory/domain/confinement.py`: `is_inside_checkout` imported from `factory.domain.pipeline_definition`, where it moves (S0001).
```
