# Work item data

## Goal

A work item's parts are data with one reader and one writer each: identifiers and paths that sort, state in the YAML front matter, a journal in the body whose entries keep speaker and kind as data, sections found without regard to headings inside code fences, the story form check, and the cost records in a sidecar file. Done when a story can be read, checked against the project's form, edited and written back with its key order, its journal can be read back by speaker and kind without parsing the text, a heading inside a code fence is never taken as a section, and cost records round-trip through the sidecar file with unknown cost and tokens kept unknown.

## Scope

- Identifier patterns, story and feature ids, branch names, the paths of the lifecycle folders and plain string order, with an acceptance sorting after the stories of its feature (kept thing 15)
- The state in the front matter (R15): stage, blocked, round, attempts, crashes, pull request, ids of comments read, the hand-over marker, the claim and the journal's data; fixed key order; initial values
- One reader and one writer for the work item file (R13): the file split by python-frontmatter and its front matter read and written with ruamel.yaml through a python-frontmatter handler, validated into Pydantic DTOs, errors that name the fault
- Sections (SI1.3): the title, the `## ` sections, the required sections taken from the project's story form, inserting a paragraph under a heading, code fences respected
- The journal (SI1.1): numbered, append-only entries with speaker and kind kept as data, continuation indent, only the human's entries dated, putting one version's journal into another (for the restore)
- The story form check (kept thing 9) and its command for the human, `factory-check-story` (its console script is already declared in `pyproject.toml`)
- The cost-record sidecar format (R15): one JSON line per record, a reader and a writer, unknown cost and tokens kept unknown

## Out of scope

- Which state a stage writes and when: F0005 and F0007
- The acceptance report's extra fields (`stories`, `outcome`) and the feature form's reader: F0009
- When a cost record is written and how bills are summed: F0005
- The order in which an acceptance becomes due against its stories: F0009 (ST6.3); this feature only provides the sort key
- When a cost record changes from started to completed: F0005, which completes a record by replacing its line in the sidecar file, because S0007 refuses two records with one run id
- The pipeline definition's reader and the agent definitions' reader: F0003
- The hand-over, the pull request description and every post: F0003 and F0007

## Stories

The order is the story numbers. A later number may start first if it is the only one moved to `ongoing/`.

- S0001 — Identifiers, paths and order
- S0002 — Work item state
- S0003 — Reading and writing work items
- S0004 — Sections that respect code fences
- S0005 — Journal with speaker and kind as data
- S0006 — Story form check
- S0007 — Cost record sidecar format
- S0008 — The story check command
- S0009 — Journal entries close their code fences (proposed by the feature acceptance)
- S0010 — Documentation after work item data (proposed by the feature acceptance)

## Decisions taken for the human

Product decisions taken while writing the stories, for the human to review in one place. Each names where it was taken.

1. The sort key `work_item_order` puts an acceptance after every story of its feature by a stated rule, not by the alphabet; a branch is named by the work item's id alone, so a slug can change without moving a branch. A slug follows v1's rule: lower-case segments of letters and digits joined by single hyphens, so no slug has a leading, trailing or doubled hyphen, and the two models refuse a slug that breaks it. (S0001, story text)
2. A path is a work item's only in the exact shape `factory/features/<feature>/<folder>/<file>.md` with the folder `backlog`, `in-progress` or `done`; a folder `drafts` or `ongoing` (v1's names, which v1.1 does not recognise), a sidecar file and a `.gitkeep` are not work items. (S0001, story text)
3. Only `stage` is required in a work item's front matter; every other key has its initial value. A key that the state does not know makes the file unreadable and the error names the key. Front matter that holds nothing (empty, only comments, or `null`) is an empty mapping: `parse` then says `missing key: stage` and `parse_specification` drops no keys; a file that is not UTF-8 is a file that cannot be read. (S0002, S0003, story text)
4. The front matter is written in one fixed notation: `null` for nothing, a flow list for comment ids, the start time of a claim as UTC text ending in `Z`, the journal's data as a block list, and a name that YAML would read back as null or a boolean (`true`, `no` and the like) in single quotes. python-frontmatter splits the file and ruamel.yaml reads and writes its YAML, through a python-frontmatter handler (R13). It splits as follows: `\r\n` is read as `\n`; the whitespace around the text is ignored, so blank lines before the opening `---` are allowed; a boundary line is three or more `-` followed only by whitespace; front matter exists only when the text starts with a boundary line and a later one closes it, so `---` lines further down a body are never front matter. The file is written in python-frontmatter's layout, with an empty line between the closing `---` and the body. The reader normalises the body as python-frontmatter does: no whitespace around it and exactly one final newline. A fault names its value by a path (`claim.lease_duration`, `journal[1].kind`), and a rule that spans keys is `invalid state`. (S0003, story text)
5. A heading is a line that starts with `## ` at column 0 outside a code fence; a fence is opened and closed as F0002-S0004 states it (any indentation before the fence characters, and any info string after an opening run) and an unclosed one runs to the end; a heading is found by its exact text, with no parenthesised note ignored as v1 did. (S0004, story text)
6. A paragraph inserted under a heading goes first, with one blank line on each side. (S0004, story text)
7. An entry's text is trimmed of surrounding whitespace; a new entry goes after the last non-blank line of the `Journal` section; the restore replaces the first `Journal` section of the current body with the baseline's and appends it when the current body has none. (S0005, story text)
8. The story form check keeps v1's rules, including that the two closing criteria are checked only when a story has two criteria or more. It adds four findings that v1 did not make: a backlog story that carries front matter, a backlog story whose `Journal` already holds entries (the opening writes entry 1 into an empty `Journal`; otherwise a second entry 1 would follow), a story in progress or done without state, and a journal whose data and text disagree in their number of entries. The two rules about the state are for the factory's own calls on a work item's branch; the command for the human reads a started story on `main`, which has no front matter, as a specification (decision 14). (S0006, story text)
9. A finding's line is a line of the body, counted from 1 after the front matter. (S0006, story text)
10. A cost record's cost is a JSON string, never a number, so no rounding can enter; blank lines in the sidecar are ignored; two records with one run id are refused, so F0005 completes a record by replacing its line; a cost is at least 0 and finite, as F0001 treats a negative cost from the runtime as a reply that does not parse; the sidecar is always written whole. (S0007, story text)
11. The check command prints `<path>: ok` for a clean story and `<path>[:<line>]: <message>` for each finding, exits 0 when every story is clean, 1 when any has a finding and 2 when it cannot run (no arguments, no story form, an unreadable file, a file that is not UTF-8). Place findings are printed first, then the reader's fault or the form findings. (S0008, story text)
12. The journal story comes after the sections story, because appending an entry needs the section finder; the story form check comes after both. (S0004, S0005, S0006, story order)
13. `factory.entry.wiring.build_work_item_reader` stays as a building block when `build_boundaries` arrives: `build_boundaries` calls it, so later stories add tests and change none of `tests/entry/test_wiring.py`. (S0008, story text)
14. The command reads a story by its folder and by whether the reader finds front matter in it. A story in `backlog` is read as a specification. A story in `in-progress` or `done` is read with `parse`. When `parse` reports `no front matter`, the story is read again as a specification and checked with the folder `backlog`. On `main` a started story is the human's moved file and has no front matter, because the state lives on the work item's branch (ST6.1). So the state rules (a story without state, a journal that disagrees with its data) are not asked of a file that cannot have a state. A story in `in-progress` or `done` with front matter is checked with the folder of its path, and any other fault of `parse` is its finding. Whether a text has front matter is the reader's rule (decision 4), not a test of the first line. (S0008, story text)
15. Journal entries are counted only at column 0 outside code blocks, and `render_entry` closes a code block that an entry's text leaves open. `NewEntry.text` and the journal record stay unchanged, and a text that ends with its own closing line gets one more, as CommonMark reads it. Decided by the human on 2026-10-13 after the feature acceptance. (S0009, story text)
16. `pydantic_core.ErrorDetails` is imported without a direct pin of `pydantic-core`: `pydantic` pins it exactly through `uv.lock`, and a second pin would have to move by hand with every pydantic upgrade. Decided by the human on 2026-10-13. (S0003, story text)
17. v1.1's file names (`factory/story-form.md`, `feature.md`) stand, so `factory-check-story` does not check factory-rf's own stories, which are in v1's tree (`TICKET.md`, `FEATURE.md`), until the tree moves to v1.1's layout. Decided by the human on 2026-10-13. (S0008, S0010, story text)
