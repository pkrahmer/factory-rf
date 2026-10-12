# Work item data

## Goal

A work item's parts are data with one reader and one writer each: identifiers and paths that sort, state in the YAML front matter, a journal in the body whose entries keep speaker and kind as data, sections found without regard to headings inside code fences, the story form check, and the cost records in a sidecar file. Done when a story can be read, checked against the project's form, edited and written back with its key order, its journal can be read back by speaker and kind without parsing the text, a heading inside a code fence is never taken as a section, and cost records round-trip through the sidecar file with unknown cost and tokens kept unknown.

## Scope

- Identifier patterns, story and feature ids, branch names, the paths of the lifecycle folders and plain string order, with an acceptance sorting after the stories of its feature (kept thing 15)
- The state in the front matter (R15): stage, blocked, round, attempts, crashes, pull request, ids of comments read, the hand-over marker, the claim and the journal's data; fixed key order; initial values
- One reader and one writer for the work item file (R13): front matter by python-frontmatter and ruamel.yaml, validated into Pydantic DTOs, errors that name the fault
- Sections (SI1.3): the title, the `## ` sections, the required sections taken from the project's story form, inserting a paragraph under a heading, code fences respected
- The journal (SI1.1): numbered, append-only entries with speaker and kind kept as data, continuation indent, only the human's entries dated, putting one version's journal into another (for the restore)
- The story form check (kept thing 9) and its command for the human, `factory-check-story`
- The cost-record sidecar format (R15): one JSON line per record, a reader and a writer, unknown cost and tokens kept unknown

## Out of scope

- Which state a stage writes and when: F0005 and F0007
- The acceptance report's extra fields (`stories`, `outcome`) and the feature form's reader: F0009
- When a cost record is written and how bills are summed: F0005
- The order in which an acceptance becomes due against its stories: F0009 (ST6.3); this feature only provides the sort key
- The pipeline definition's reader and the agent definitions' reader: F0003
- The hand-over, the pull request description and every post: F0003 and F0007
- Writing the console script entry for `factory-check-story` in `pyproject.toml`: the human adds it, because that file is outside every write path

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

## Decisions taken for the human

Product decisions taken while writing the stories, for the human to review in one place. Each names where it was taken.

1. The sort key `work_item_order` puts an acceptance after every story of its feature by a stated rule, not by the alphabet; a branch is named by the work item's id alone, so a slug can change without moving a branch. (S0001, story text)
2. A path is a work item's only in the exact shape `factory/features/<feature>/<folder>/<file>.md` with the folder `backlog`, `in-progress` or `done`; v1's folders `drafts` and `ongoing`, a sidecar file and a `.gitkeep` are not work items. (S0001, story text)
3. Only `stage` is required in a work item's front matter; every other key has its initial value. A key that the state does not know, v1's `comments_seen` included, makes the file unreadable and the error names the key. (S0002, S0003, story text)
4. The front matter is written in one fixed notation: `null` for nothing, a flow list for comment ids, the start time of a claim as UTC text ending in `Z`, the journal's data as a block list. The reader normalises the body: no leading blank lines and exactly one final newline. (S0003, story text)
5. A heading is a line that starts with `## ` at column 0 outside a code fence; a fence is opened and closed as in CommonMark and an unclosed one runs to the end; a heading is found by its exact text, with no parenthesised note ignored as v1 did. (S0004, story text)
6. A paragraph inserted under a heading goes first, with one blank line on each side. (S0004, story text)
7. An entry's text is trimmed of surrounding whitespace; a new entry goes after the last non-blank line of the `Journal` section; the restore replaces the first `Journal` section of the current body with the baseline's and appends it when the current body has none. (S0005, story text)
8. The story form check keeps v1's rules, including that the two closing criteria are checked only when a story has two criteria or more. It adds three findings that v1 did not make: a backlog story that carries front matter, a story in progress or done without state, and a journal whose data and text disagree in their number of entries. (S0006, story text)
9. A finding's line is a line of the body, counted from 1 after the front matter. (S0006, story text)
10. A cost record's cost is a JSON string, never a number, so no rounding can enter; blank lines in the sidecar are ignored; two records with one run id are refused; the sidecar is always written whole. (S0007, story text)
11. The check command prints `<path>: ok` for a clean story and `<path>[:<line>]: <message>` for each finding, exits 0 when every story is clean, 1 when any has a finding and 2 when it cannot run (no arguments, no story form, an unreadable file). (S0008, story text)
12. The journal story comes after the sections story, because appending an entry needs the section finder; the story form check comes after both. (S0004, S0005, S0006, story order)
