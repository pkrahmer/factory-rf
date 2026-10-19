# Pre-check F0025, round 1: the feature, its human's changes and its decisions

I checked the feature `F0025-the-project-guide-split-by-domain`, its one story and the drafter's brief against these sources:

- v1.1's roles and forms (`claude/agents/*.md`, `factory/story-form.md`, `factory/feature-form.md`), `factory/pipeline.yml`, `CLAUDE.md` and the `Makefile`;
- the plan's step 8 and *The project guide split by domain* (`planning/overnight/restructure-after-f0011.md`);
- the night plan of 2026-10-19;
- the code the story touches (`factory.domain.documents`, `factory.domain.sections`, `factory.entry.check_documents`) and its tests;
- `docs/project-guide.md` (1,905 lines, 41 sections), `docs/operator-guide.md`, `docs/decisions.md` and `README.md`;
- the drafted stories and `feature.md` of F0020, F0022, F0023 and F0024.

The story's own result is in `F0025-S0001-1.md`. The story's code was prototyped and its tests run in throwaway containers of v1.1's image (no network, no volume, no secret). A move script written from criterion 8 was run on a copy of today's guide, and the three smoke-test blocks ran against that copy. A stub `git` printed the saved old guide, so no git command was used.

## The story in short

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 the index, eight files, the check of every file | question (2) | four edits, one optional. Without edit 2 the coder stops; without edit 3 the documenter likely stops. |

## Order and sizing

- One story is right (decision 1). The constant and the move must land together. The coder runs no `documents` check, so the doing and review stages stay green with the old guide in place, and the docs stage's `documents` reads the index the documenter has just made (seen with the prototype).
- Size: the coder's part is a constant, a ten-line function and a reading loop. The tester writes two modules and changes one earlier module. The documenter's move is a script that runs in under a second. All three fit their 40 minutes and a few dollars. The documenter's $1.50 is the tight one (see the story's pre-check).
- No story touches the git interface's operations, `tests/application/test_interfaces.py`, the pipeline definition or its load tests, the stage finisher, the records contract or `tests/test_model_configuration.py` (the story adds no model). No structural test reads the source, so `[tool.mutmut]` stays as it is. Fixture order does not matter: the new tests use only `tmp_path` and `capsys`.

## When to build it

The guide has 1,905 lines today. F0021 is archived, and the night plan builds F0020 next: eight stories, whose docs criteria add *The opencode runtime*, the shared start module, the streaming process function and the waits to the guide. They would very likely take it past 2,000 lines, the file tool's default read, during F0020 (the pre-checks of F0023 and F0024 drew the line at about 1,950). "Before F0023" is too late: F0020 and F0022 come first. After the split, the largest file F0020 writes into, `agents.md`, holds 246 lines, so it has room. **Build F0025 now, before F0020.** The night plan's step 2 already sends one fix agent over F0020's stories before F0020 starts. Change 2's F0020 bullets can go into that same pass.

## The human's changes

- Write paths: right as stated. The coder writes `src/*`, the tester `tests/*` and the documenter `docs/*` and `README.md`. `docs/*` matches `docs/project-guide/README.md` (`fnmatch`'s `*` also matches `/`), and the kernel's folder target `docs` covers the new folder and the deletion of the old file. Nothing touches `Makefile`, `pyproject.toml`, `security/`, `.secrets.baseline`, `image/` or `template/`.
- The factory's checks after the docs stage stay green (seen on the moved copy). `documents ok`. The secret scan reads the nine new files and finds nothing (detect-secrets with the baseline's plugins and filters: 0 results; the baseline has no entry for any document). No test reads the real guide, so `make test` does not change.
- Change 1, `CLAUDE.md` and `factory/story-form.md` right after the merge: every anchor exists verbatim (`CLAUDE.md` lines 3, 42 and 51; `story-form.md` line 15). No test pins either file's text (`tests/test_claude_files.py` pins only `template/CLAUDE.md`, which stays). The form's headings do not change, so `factory-check-story` gives the same findings. The timing is right: before the merge, the story's own agents would read an index that is not there yet. After the docs stage, only that story's smoke tester and the human read a `CLAUDE.md` that names a deleted file, which is harmless.
- Change 2, the drafted stories' docs criteria: complete and right. `grep` over F0020, F0022, F0023 and F0024 finds `docs/project-guide.md` in exactly the criteria listed: F0020-S0001 (22), S0002 (14), S0003 (12), S0004 (19), S0005 (20), S0006 (15), S0007 (18), S0009 (10, deferred); F0022-S0001 (16), S0002 (8); F0023-S0001 (10), S0002 (15); F0024-S0001 (13), S0002 (4), S0003 (its Interface sentence and criterion 6). The four `feature.md` Scope bullets are listed too. F0020-S0008's docs criterion names only the operator guide, so it needs nothing. The target files fit the table's domains.
- Change 2, every other place that names the guide (`grep -rn` over the repository). `CLAUDE.md` (3) and `factory/story-form.md` are covered by change 1. `src/factory/domain/documents.py` and `tests/entry/test_check_documents.py` are covered by the story; for the test, see fault 1 below. The operator guide's five references are in criterion 8. The decision log's entry *The project guide lives in `docs/`* gets its sentence, and its dated F0011-S0005 entry rightly stays. *The write paths*' sentence is in criterion 8. `template/CLAUDE.md`, `tests/test_claude_files.py` and the demo stay, per decision 7. `factory/v1/`, the archived features, `docs/runs/` and `planning/` are history. **One place is missing**: `README.md`'s opening paragraph ends "`docs/project-guide.md` describes each part.", and only *Where to look next* is named (fault 2). No shipped agent text under `claude/` names the path. The documenter's lesson already describes the index and the domain files.
- Change 3, the check after the feature: right, at no cost.

Faults:

1. **Decision 9's leave covers one of the two places where `tests/entry/test_check_documents.py` names the old path.** `MISSING_LINES` (line 23) is covered. The expected output of `test_each_finding_prints_one_line_in_order_and_returns_one` (line 58, `docs/project-guide.md: section 'Kill points' is missing`) is not, and that test fails as soon as `PROJECT_GUIDE` changes (seen). "Every other test of the document check uses the constants" is not true of that line. Without the fix, the coder stops with a question and a `tests` round follows (edit A).
2. **The README's opening paragraph** (edit B; see the story's edit 4).
3. **Criterion 8 points at "the feature's table", which the documenter may not read.** Its stage says "not `feature.md`". The table belongs in the criterion (the story's edit 3). Decision 2's table itself is right: every count matches today's guide, and the moved files come out at the table's lengths plus a four-line head.

## The decisions

1. One story: right (see *Order and sizing*).
2. The index and eight domains: right. Each file is one domain of today's code, filled in the old guide's order, so no order is chosen by judgement. The plan's index held "layers, errors, kill points, test rules"; layers and test rules live in `CLAUDE.md`, not the guide, so the index's four sections are the right reading. The plan's nine domains (work items, pipeline, stages, watching, handlers, stops, recovery, costs, tools) collapse sensibly: the pipeline into stages; handlers and stops into watching; recovery into the index's kill points and fault paths; tools into git-and-hosting and processes-and-checks. *Replaced from v1* belongs in `agents.md`: its table renames the shipped agents' texts. Lengths range from 89 to 375 lines (seen).
3. 600 lines, checked once: right as a choice. A lasting test would stall a documenter with nothing in its story to fix. Its weak point is that only the smoke test and the human's change 3 know the figure, while the documenter's lesson says 2,000. One sentence in the index would put 600 in front of every later documenter (the story's optional edit 5).
4. A move, byte for byte, with two exceptions: right, and checkable. The smoke test caught a one-word change in a moved section and a section written twice (seen). References by name with no links: right. The guide holds no Markdown link, and `### ` subsections stay inside their `## ` section (`sections` cuts only at `## `).
5. The move by script: right. A script written from criterion 8 alone made the exact move.
6. The check reads the index, plus the wording of every flat `.md` file: right, prototyped. The index keeps *Kill points* and *Fault-injection paths*, so `PROJECT_GUIDE_SECTIONS` and the row rules work unchanged.
7. The template and the demo keep one file: right.
8. The rest of the documents: right, except the README's opening paragraph (fault 2).
9. The leave: incomplete (fault 1, edit A).
10. Where F0025 touches F0020 to F0024: right. None of them touches `documents.py` or `check_documents.py`. Today's pipeline definition gives `documents` 5 minutes, not F0023's 2; either is ample for a 0.2 s check of nine files.
11. Testing: right. No paid call. `git show origin/main:docs/project-guide.md` is read-only, and `origin/main` holds the old guide while the story is open.

## Points for the human, with recommended answers

1. When to build (see *When to build it*): (a) now, before F0020, with change 2's F0020 bullets folded into the night plan's step-2 fix pass; (b) after F0020; (c) before F0023. Recommended: (a). F0020's eight docs criteria would push the single file past 2,000 lines partway through F0020.
2. The leave (fault 1, edit A): (a) widen it to the second line; (b) as drafted. Recommended: (a).
3. The README's opening paragraph (fault 2, edit B): (a) name it; (b) trust the cross-read. Recommended: (a).
4. The story's points: two intake questions and edits 1 to 4, with optional edit 5 (see `F0025-S0001-1.md`). All recommended (a).

## Verdict

Feature accepted with edits A and B. S0001 refused at intake as drafted, accepted with its edits 1 to 4 (5 optional).

Edit A, decision 9: replace the bullet's text after "`tests/entry/test_check_documents.py` (F0011-S0005's)," up to "so they stay as they are." with:

```markdown
 whose `MISSING_LINES` holds `docs/project-guide/README.md: missing` in place of `docs/project-guide.md: missing`, and whose `test_each_finding_prints_one_line_in_order_and_returns_one` expects `docs/project-guide/README.md: section 'Kill points' is missing` in place of `docs/project-guide.md: section 'Kill points' is missing`. Every other test of the document check uses the constants (`PROJECT_GUIDE`, `DOCUMENT_PATHS`) and `tests/document_texts.py`, whose `write_documents` makes the folder, so they stay as they are.
```

Edit B, decision 8: replace "`README.md`'s *Where to look next* names the index." with:

```markdown
`README.md`'s *Where to look next* names the index, and the last sentence of its opening paragraph ("`docs/project-guide.md` describes each part.") names `docs/project-guide/`.
```
