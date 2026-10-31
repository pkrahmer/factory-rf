# Approving a story

A story at `stage:approval` has passed every stage. Gather the facts with `sh scripts/approval.sh <pr> <id>`, then judge the six checks.

## The six checks

1. **Write paths.** Every changed file lies in a write path of a role that ran (`factory/pipeline.yml`, `roles:`), or is the work item and its cost record.
2. **Earlier tests.** A test file another story wrote (`M` in the list) changed only under a leave: the standing leave to move a shared helper (every test keeps its name and what it checks, the tester's entry names the file) or a leave you or the human gave in an answer. Read its diff when in doubt: an assertion that changed meaning is a finding.
3. **The journal's end.** The smoke test ran, met every `Expect:` line, and found nothing; no finding is left open.
4. **The `Expect:` lines.** They match what the smoke tester reports.
5. **Markers.** No new `noqa`, `type: ignore`, `pragma: no cover`, skip or xfail, unless the same marker already stands on `main` for the same reason.
6. **The cost.** Plausible for the story's size; a cost far above its kind is worth a line to the human.

Read the code of the story's main change once yourself: the six checks are about the process; a wrong behaviour slips through them.

## Then

- **All green, switch `merge` on:** `gh pr merge <n> --repo <owner/name> --merge`. Wait until `main` holds the factory's archive commit (`work item <id>: merged, archived`), then log it.
- **All green, switch `merge` off:** post the verdict as a comment that starts with `Operator: ready to merge.`, the six checks in one line each, and ends with `<!-- operator verdict -->`; tell the human. The wait script stops reporting the approval once your verdict is the newest comment.
- **A small finding** (a document slip, a false positive for a baseline): merge or recommend merging, then fix it on `main` yourself and log it. Do not send the story back for it.
- **A real finding:** a comment that names it, for the human.

## After a merge

- When the merge changed the factory's own code and the factory runs from that repository (its self-build), the instance needs the new code: on a VM the operator guide's rebuild, in a job its next execution. A project's merge never needs it.
- With `start_next` on, start the next story of the feature's build order (`sh scripts/start-story.sh <id>`) once the archive commit is on `main`.
