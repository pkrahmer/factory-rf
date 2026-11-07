# Every folder says what it holds

## Goal

A reader who browses the repository on GitHub sees each folder's `README.md` below its file list. Today only a few folders have one, so a newcomer opens files to learn what a folder is for (the human, 2026-11-07). This feature gives every folder a reader would ask about a short README: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. A guard keeps each README's list of subfolders true, and the document check reads the READMEs like the guides, so their names and links stay true too. The feature also puts the factory's new license, Apache 2.0, into every file of code and every script as an `SPDX-License-Identifier` line (S0007). Done when every story below is merged, every README on the list exists and is on `docs/checked-documents.txt`, and `make check` is green.

## Before it starts

F0054 (the documents are rewritten for their readers) is merged, so the style page and the guides the READMEs link to are in their final form.

## Scope

- The list of folders that have a README, as one constant in the code, and a guard over it (S0001).
- The document check reads those READMEs, so they can go on the checked list (S0001).
- The documenter may write them, so the stories that write them take the docs route (S0001, with the human's change).
- The READMEs themselves, in four groups (S0002 to S0005).
- The document check resolves references to another page's heading (S0006, the human, 2026-11-07).
- The license header in every Python module under `src/factory/` and every script under `operator/` outside `operator/template/`, with a guard (S0007, the human, 2026-11-07).

## Out of scope

- The layer folders of each area (`domain`, `application`, `adapters`) and the test folders that mirror them: they all look alike, and the area's README explains its three layers in one line each.
- Folders that hold one kind of file or generated files: `agents/agents/`, `security/semgrep/`, `src/factory/contract/`, `operator/skill/kumpel/` (its `SKILL.md` explains it), `operator/template/factory/`, the commands folders of `operator/claude/` and `operator/opencode/`, and every feature folder and run folder.
- The READMEs of the human's folders, `factory/`, `factory/features/` and `docs/runs/`: no stage writes there. The human writes them after S0005.
- `planning/` and `session-logs/`, which keep their own READMEs as the human's.
- Any change to the code beyond S0001, and the area packages' docstrings, which keep naming their guide page for agents and editors.

## Out of scope for the license header (S0007)

- The tests under `tests/` (the human, 2026-11-07), `operator/template/` (its files belong to the project made from it), `demo/`, Markdown, YAML, JSON, the generated schemas and the agent files under `agents/`.
- A copyright line in each file: the copyright and the author stand once, in `NOTICE` (decision 8).

## Stories

- S0001: The folders that have a README are listed and checked
- S0006: A reference to another page's heading names a heading it has (runs right after S0001)
- S0007: Every file of code and every script names its license (runs after S0006)
- S0002: The package and its areas say what they hold
- S0003: The tests say how they are laid out
- S0004: The operator's folders say what they hold
- S0005: The top folders say what they hold

## The human's changes

- **At S0001's merge:** `factory/pipeline.yml`, the documenter's `write_paths` gain the 23 README paths of S0001's list, one exact path per entry, as `operator/README.md` stands there today (for example `"src/factory/agents/README.md"`). No folder pattern such as `src/*` or `*/README.md`: the documenter may write these READMEs and nothing else in their folders, so it can never change code, a test or a script on the docs route. Check the new entries against the write-path rules before pushing.
- **After S0005's merge:** the human writes `factory/README.md`, `factory/features/README.md` and `docs/runs/README.md` in the same form and adds them to the list and the checked list.

- **Before S0007:** done on 2026-11-07: `LICENSE` holds the Apache License 2.0 text from apache.org, `NOTICE` names the product and its copyright, and `pyproject.toml` has `license = "Apache-2.0"` and `license-files = ["LICENSE", "NOTICE"]`.

## Decisions taken for the human

1. **A README where a reader would ask "what is this?"** (the human, 2026-11-07, from the folder tree shown in chat). Not in folders that mirror another, hold generated files or hold one kind of file; their parent explains them in one line.
2. **The form of a folder README.** First one sentence on what the folder holds and why. Then links to the guide pages that explain it. Then one line per subfolder, ``- `<name>/` <one sentence>.`` (no colon, as the guard and the style page write it), in the order of the folder listing. No other sections. It follows `docs/project-guide/style.md`.
3. **The list of folders is code, not convention.** One constant names every folder that has a README; the guard and the document check both read it, so a folder added to the list cannot be forgotten by either.
4. **The shared test helpers' list stays in the project guide** (the human, 2026-11-07, changed from moving it). The list names about 50 modules and 53 fixtures with their rules, which the agents rely on, and the shape limits of decision 6 would never allow it in a README. `tests/support/README.md` and `tests/guards/README.md` are pointers to the guide's sections (S0003). Rejected: moving the list and exempting `tests/support/README.md` from the limits, which would make it the one long README the limits prevent.
5. **A leave for S0001** (the human, 2026-11-07). The tester may change the earlier tests that pin `agents/agents/documenter.md` only so far as the one sentence naming the folder READMEs requires, and any other earlier test whose only failure is that sentence. Every changed test keeps its name and what it checks. The story's Interface holds the same words.
6. **A README stays a pointer** (the human, 2026-11-07, worried that the documenter would document everything in the READMEs). The guard checks its shape, not only its list: no section but the title, no code block, an opening of at most two sentences, at least one relative link, one sentence of at most 25 words per subfolder, nothing else, and at most 10 lines plus one per subfolder. The style page and the documenter's text say the same in words: what needs explaining goes into the guide page the README links to. Rejected: a length rule in words only, which nothing checks.
7. **Apache 2.0 instead of MIT** (the human, 2026-11-07), for its explicit patent grant. The dependencies' licenses are unchanged; the Makefile's allow list is about them, not about the factory's own license.
8. **The header is one line, `SPDX-License-Identifier: Apache-2.0`** (the human, 2026-11-07), as a comment in the file's own syntax: the first line of a Python module, and the line after the shebang of a script. The copyright and the author stand once, in `NOTICE`. Rejected: `SPDX-FileCopyrightText` with the author's name in every file, which would carry the name into every project that copies a file, whatever that project is; and the same line with a project name (`The Kumpel Authors`).
9. **Code and scripts, not the tests** (the human, 2026-11-07).
10. **A new area cannot come without a README** (the human, 2026-11-07). The guard also checks that every package directly under `src/factory/` is on the list (S0001). Other folders still join the list by hand; a new subfolder of a listed folder already fails the guard until its parent's README names it.
11. **`operator/template/` has no README** (the human, 2026-11-07). An operator copies that folder into a new project, so its README would land in the project's root or overwrite the project's own. `operator/README.md` explains the folder in its subfolder line, and S0004 takes the path off the list (22 paths). Rejected: keeping it with a warning in the guide, which nothing enforces.
