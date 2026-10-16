# Handling of precheck/F0011-3.md (improve round 3)

Report: `planning/overnight/precheck/F0011-3.md`. The findings are numbered 1 to 12 in the order of the report's table. Edits are in `planning/overnight/stories/F0011-proof-and-documents/`; the session copies them to `factory/features/`.

| # | Story and criterion | Severity | Handling |
|---|---|---|---|
| 1 | S0003 Interface row 8; c9 | blocker | **Fixed.** Row 8's `test`: `test_attempts_cap_run_stalls_twice_asks_human_without_retrying_and_retries_on_comment` → `test_attempts_cap_run_stalls_twice_asks_human_without_a_rerun_and_reruns_on_comment` (83 characters). Added after "...not a validation of `FaultPath`.": " No `test` contains the word `retrying`: `tests/test_retrying_wording.py` refuses it in any string under `src/factory` outside the post texts." c9 (the table of thirteen rows) now reads the new name through the table; its wording is unchanged. |
| 2 | S0004 scenario `duplicate`; c9 | blocker | **Fixed, with the code fix (not the alternative).** New paragraph after the scenario list: "This story changes `RemoteWorkItems.read` (`src/factory/application/work_items.py`, F0006): a story file in `in-progress/` whose id an earlier file of the list already has is read from `origin/main` as a started story (as `_started_document` reads it), never from the work item's branch, which holds only the first file. Today `_branch_document` raises `WorkItemFormatError` (`missing on branch`) for it, the tick raises before the dispatcher, and the duplicate reaches only the factory log." New criterion 16 (old 16 "make check" → 17, old 17 "docs" → 18): "16. `RemoteWorkItems.read` on a remote whose `main` holds two in-progress files of one id and whose branch of that id holds only the first returns two snapshots, the second with the state `initial_state(<the first stage>)` and its body from `origin/main`; when the only in-progress file of an id is missing on that id's branch, it still raises `WorkItemFormatError`." Tests line: added "`tests/application/test_work_items_duplicate.py` (criterion 16)". `FEATURE.md` decision 19 added (see below). c9's wording is unchanged. |
| 3 | S0004 c8 | should fix | **Fixed.** c8: "...in some module under `src/factory/application` or `src/factory/entry`: production code can raise every stop of the table." → "...in some module under `src/factory/application` or `src/factory/entry` (read with `modules()` and `string_literals()` of `tests/source_search.py`): production code can raise every stop of the table." Meaning unchanged; the helper to reuse is named. |
| 4 | S0004 c3 | note | **Fixed** (exact text given). c3: "the limits include each of `L11`, `L19`, `L26`, `L33`, `L55`, `L58`, `L64` and `L65`" → "... `L11`, `L19`, `L26`, `L30`, `L33`, `L55`, `L58`, `L64` and `L65`" (`L30` added; nine limits). |
| 5 | S0004 c15 | note | **Fixed** (exact fragment given). c15: "is started and ticked once; its branch exists" → "is started and ticked once with a question run queued; its branch exists". |
| 6 | S0003 Interface (`work_item_path`) | note | **Fixed.** The helper is renamed `work_item_file(world, work_item)` in the Interface (signature and bullet) and in c3 (`work_item_path` → `work_item_file`). Meaning unchanged; the clash with `factory.domain.paths.work_item_path` is gone. |
| 7 | S0005 c6 | note | **Fixed.** Appended to c6: ", and one whose only row for it is indented (``  \| `fetch-failed` \| health status and factory log \|``)". |
| 8 | S0005 c3 | note | **Fixed.** c3: "A text of only whitespace gives exactly one finding for that document, with the message `empty`." → "For each of the four documents, a text of only whitespace (and, separately, the empty string) gives exactly one finding for that document, with the message `empty`." The criterion now holds for each document, and the empty string is a second input. |
| 9 | S0005 c23 | note | **Deferred.** The report gives no replacement text ("None"); the encoding is checked by the reviewer against the Interface. |
| 10 | S0005 c22 | note | **Fixed.** Appended to c22: "(run through `run_process`, as `tests/entry/test_health.py` runs `factory.entry.health`)". |
| 11 | S0005, after the split of the project guide | note | **Deferred.** The report says "None for F0011": the housekeeping story (`restructure-after-f0011.md`) must make `PROJECT_GUIDE` become `docs/project-guide/README.md` and keep the sections *Kill points* and *Fault-injection paths* with their tables in that index. |
| 12 | S0001 (size, tester) | note | **Deferred.** The report says "None (deferred since round 1)": every scenario already passes on today's code, so the coder's share is one domain module. |

## `FEATURE.md`: decision 19 added

"19. A second in-progress file of an id that already has a branch is read from the main branch, so that the duplicate reaches the pull request instead of failing every tick. This changes F0006's code (`RemoteWorkItems.read`), not its tests. Taken by the session for the human, to confirm. (S0004, story text)"

The report's text of decision 19 is kept; the sentence on F0006's tests and the "taken by the session for the human, to confirm" mark are the session's additions.

## Counts

Fixed: 9 (rows 1 to 8 and 10); deferred: 3 (rows 9, 11, 12). "Needs interfaces.md": none.

Meaning changed: S0003 c9 (via row 8's `test` name), S0004 c3 (adds `L30`), S0004 c8 (names the helper), S0004 new c16 (old 16 and 17 are now 17 and 18), S0005 c3 (per document, plus the empty string), S0005 c6 (one more case).
