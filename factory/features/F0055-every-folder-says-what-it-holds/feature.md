# Every folder says what it holds

## Goal

A reader who browses the repository on GitHub sees each folder's `README.md` below its file list. Today only a few folders have one, so a newcomer opens files to learn what a folder is for (the human, 2026-11-07). This feature gives every folder a reader would ask about a short README: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. A guard keeps each README's list of subfolders true, and the document check reads the READMEs like the guides, so their names and links stay true too. Done when every story below is merged, every README on the list exists and is on `docs/checked-documents.txt`, and `make check` is green.

## Before it starts

F0054 (the documents are rewritten for their readers) is merged, so the style page and the guides the READMEs link to are in their final form.

## Scope

- The list of folders that have a README, as one constant in the code, and a guard over it (S0001).
- The document check reads those READMEs, so they can go on the checked list (S0001).
- The documenter may write them, so the stories that write them take the docs route (S0001, with the human's change).
- The READMEs themselves, in four groups (S0002 to S0005).

## Out of scope

- The layer folders of each area (`domain`, `application`, `adapters`) and the test folders that mirror them: they all look alike, and the area's README explains its three layers in one line each.
- Folders that hold one kind of file or generated files: `agents/agents/`, `security/semgrep/`, `src/factory/contract/`, `operator/skill/kumpel/` (its `SKILL.md` explains it), `operator/template/factory/`, the commands folders of `operator/claude/` and `operator/opencode/`, and every feature folder and run folder.
- The READMEs of the human's folders, `factory/`, `factory/features/` and `docs/runs/`: no stage writes there. The human writes them after S0005.
- `planning/` and `session-logs/`, which keep their own READMEs as the human's.
- Any change to the code beyond S0001, and the area packages' docstrings, which keep naming their guide page for agents and editors.

## Stories

- S0001: The folders that have a README are listed and checked
- S0002: The package and its areas say what they hold
- S0003: The tests say how they are laid out
- S0004: The operator's folders say what they hold
- S0005: The top folders say what they hold

## The human's changes

- **At S0001's merge:** `factory/pipeline.yml`, the documenter's `write_paths` gain the README paths of S0001's list, so that S0002 to S0005 take the docs route. Check the new entries against the write-path rules before pushing.
- **After S0005's merge:** the human writes `factory/README.md`, `factory/features/README.md` and `docs/runs/README.md` in the same form and adds them to the list and the checked list.

## Decisions taken for the human

1. **A README where a reader would ask "what is this?"** (the human, 2026-11-07, from the folder tree shown in chat). Not in folders that mirror another, hold generated files or hold one kind of file; their parent explains them in one line.
2. **The form of a folder README.** First one sentence on what the folder holds and why. Then links to the guide pages that explain it. Then one line per subfolder, ``- `<name>/`: <one sentence>.``, in the order of the folder listing. No other sections. It follows `docs/project-guide/style.md`.
3. **The list of folders is code, not convention.** One constant names every folder that has a README; the guard and the document check both read it, so a folder added to the list cannot be forgotten by either.
4. **The shared test helpers' list moves to `tests/support/README.md`.** It sits beside the files it lists, and the project guide's index links to it instead of holding it (S0003).
5. **A leave for S0001** (the human, 2026-11-07). The tester may change the earlier tests that pin `agents/agents/documenter.md` only so far as the one sentence naming the folder READMEs requires, and any other earlier test whose only failure is that sentence. Every changed test keeps its name and what it checks. The story's Interface holds the same words.
6. **A README stays a pointer** (the human, 2026-11-07, worried that the documenter would document everything in the READMEs). The guard checks its shape, not only its list: no section but the title, no code block, an opening of at most two sentences, at least one relative link, one sentence of at most 25 words per subfolder, nothing else, and at most 10 lines plus one per subfolder. The style page and the documenter's text say the same in words: what needs explaining goes into the guide page the README links to. Rejected: a length rule in words only, which nothing checks.
