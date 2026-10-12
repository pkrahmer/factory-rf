# Brief: the skeleton of v1.1's features (Phase 2, serial step 1)

## Goal

Write the list of features v1.1 is built in, in build order, with what each covers and a proposed story list, so that parallel drafters can write each feature's stories without overlap and v1 can build them in plain id order.

## Inputs (read these; nothing else)

- `C:\Dev\Projects\factory-v2\planning\v1.1\overnight-run-plan.md`, section 5 ("Phase 2, features and stories") in full: the dependency table, the starting order of ten features, the split of SI1, and the rules for ids and slugs. Your specification.
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`, sections 2 to 5 and 8, and the appendix (names).
- `C:\Dev\Projects\factory-v2\planning\01-discovery\kept-from-v1.md` (the 21 kept things with evidence).
- For v1's base behaviour, as needed to see what each feature must rebuild: `C:\Dev\Projects\factory-v2\planning\01-discovery\v1-04-08.md`, `v1-09-11.md`, `v1-12-15.md` (extractions of the book's chapters 4 to 15). Use the book itself (`C:\Dev\Projects\factory\docs\reference\<NN-name>\README.md`) only to settle a doubt.
- `C:\Dev\Projects\factory-rf\CLAUDE.md` (the architecture: package `factory`, layers domain ← application ← adapters ← entry; product paths `src/`, `tests/`, `image/`, `template/`, `claude/`).

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\skeleton.md`, with these headings:

- `## Summary` (at most ten lines).
- `## Build order`: a table, one row per feature: id and slug (`F000N-slug`; the slug starts with a letter), title, goal (one sentence with "Done when …"), and the items and condition ids it carries (for example `GH1.1–GH1.5`, `SI1.1`, `R13`).
- `## Features`: one subsection per feature with: Goal (a paragraph with a "Done when" sentence); Scope (bullets); Out of scope (bullets, naming the feature that does it instead); the kept things of handover section 3 it keeps (by number); the rules R1 to R38 it obeys or implements; the base behaviour of v1 it rebuilds (with the extraction file and section); and a **proposed story list**: `S0001 — <title>` lines, each with the condition ids and kept behaviour it builds and a size estimate in criteria (no story above 26 criteria; aim for 8 to 18). Stories are in dependency order inside the feature.
- `## Dependencies`: the plan's dependency table checked against your order, one row per item: needs, the features where those are built, and "holds" or the reason it cannot hold.
- `## Not tonight`: WE1.4, WE4, WE5 and R35's rewrite, with the reason (they need the finished v1.1 or another repository), and anything else that cannot be built by v1 inside its container.
- `## Open questions`: what you could not decide from the inputs.
- `## Sources`: file and section per decision you took.

## Rules

- Start from the plan's ten features and their splits. You may change the order or the split only to keep a dependency or to fix a gap you name, never to break a dependency in the table.
- Ids are `F0001` to `F00NN`, contiguous; numbering is a topological order (no story may need a story with a higher id). A feature's stories may only need stories of lower features or lower numbers in the same feature.
- v1.1 is v1's whole behaviour rebuilt plus the 23 changes, not the changes alone. A mechanism that a change replaces is built the v1.1 way from the start.
- The first feature must be useful on its own and small enough to be built first tonight (the boundaries: wrappers and interfaces with their DTOs and the fake).
- Use the glossary's names (handover appendix) for everything that becomes code, documentation or a v1.1 file format.
- Every acceptance condition of handover section 5 (ST1.1 to WE6.5) appears exactly once in the build order table or under "Not tonight". Every kept thing of section 3 appears in at least one feature or is marked "configuration in the seed".
- Conditions that need Docker, root, a second OS user or a real image build (parts of ST3.3, ST5.1, WE3.1, WE3.3) become a static test of the files in the story plus a "morning observation": say so in the story line.

## Not

- No git commands. Do not write any file other than the output.
- Do not write the stories themselves, the interfaces or the DTOs: a later step does.
- Do not invent behaviour that neither the handover nor v1's book gives; when you need it, put it under Open questions.

## Reply

The Summary and the Open questions, nothing else.

Model: opus.
