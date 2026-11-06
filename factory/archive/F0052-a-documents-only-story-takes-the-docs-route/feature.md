# A documents-only story takes the docs route

## Before it starts

Decided with the human on 2026-11-05: routes stay branches of the stage graph. The intake's `next` names the first stage of each route, and a route that can be sent back ends in an approval stage of its own. A later route is new lines in `factory/pipeline.yml`, not new code. Nothing else waits; the feature starts when the spending cap allows.

## Goal

Every story takes the same route today: intake, tests, doing, review, docs, smoke test, approval. A story that changes only documents pays for a tester and a coder who have nothing to do, and a test over documents cannot even pass, because the check after `doing` runs before the documenter has written anything. In F0051 that cost about half of every documents-only story and one stall (`planning/f0051-candidates.md`, items 46 and 59). This feature gives such a story a route of its own: intake, then the documenter, then a reviewer who judges the writing, then the human's approval. A close at that approval sends the story back to the documenter, not to a coder. It also writes down how the documents are written, in a style page with a glossary, so that the documenter and the reviewer judge by the same rules (the human's choice of 2026-11-05, `planning/doc-style-drafts.md`). The rewrite of the guides to that style is the next feature, and it will take this route. Done when every story below is merged and `make check` is green.

## Scope

- The factory carries a story along a second route to a second approval stage, and a close there sends it back along that route (S0001).
- The intake sends a story whose Interface changes only documents to the docs route; the documenter and the reviewer know their stages on it (S0002).
- The style page and the glossary, which the documenter and the reviewer read (S0003, the first story on the new route).

## Out of scope

- The rewrite of the guides and the README to the new style: the next feature.
- The docs route in the project template (`operator/template/factory/pipeline.yml`): a project adds it when it wants it.
- A check of the style by a tool: the reviewer judges it.
- Any change to the route of a story that changes code.

## Stories

The build order: the route must work before the agents choose it, and S0003 is the route's first real use.

- S0001: A story can take a second route to a second approval
- S0002: The agents know the docs route
- S0003: The documents have a style page and a glossary

## The human's changes

- **At S0002's merge:** `factory/pipeline.yml` gets the docs route, placed after `smoke-test` and before `acceptance`:

  ```yaml
  docs-only: {role: documenter, next: [docs-review, tests], checks: [check, secrets, documents]}
  docs-review: {role: reviewer, next: [docs-approval, docs-only], round_cap: 2}
  docs-approval: {approval: true, next: [done, docs-only]}   # the human: a merge accepts, a close sends back to the documenter
  ```

  and `intake: {role: intake, next: [tests, docs-only]}`. `tests` stays the intake's forward decision; `docs-only` is the other one.
- **At S0003's start:** nothing; S0003 is the first story the intake may send down the new route.
- **Before S0008's start** (the human, 2026-11-06, from the third acceptance): `check`'s `not_read` in `factory/pipeline.yml` loses `"README.md"` and `"docs/*.md"` and gains `"docs/runs/*"`, which no test reads. The guide guards and other tests under `make test` read the documents, so a documents-only change must run `make check` again instead of reusing an earlier pass. Rejected: moving those tests into `make documents`, which is more work for the same gate; and keeping the reuse, which lets a broken guard through.

## Decisions taken for the human

1. **A route of its own, not shortcuts on the old one.** The documents-only stories get three stages of their own (`docs-only`, `docs-review`, `docs-approval`) that reuse the documenter and reviewer roles. Rejected: letting the intake jump to `docs` and the documenter jump to `review`, because those moves would count as rework in the old stages' rounds, and a close at `approval` would send the story to a coder who cannot write documents.
2. **The review comes after the writing.** On the docs route the reviewer reads the finished text, judges it against the style page and the docs criterion, and may send it back to the documenter within the round cap of two.
3. **No smoke test on the docs route.** `make check`, the document check (`make documents`) and `make secrets` run after the documenter. `make check` runs again after a documents-only change, because tests read the documents (the human's change before S0008). A smoke test of prose adds nothing.
4. **The intake decides, by the Interface.** A story goes down the docs route when every path its Interface changes is one the documenter may write (`README.md`, `docs/*`, `operator/README.md`). Anything else takes the old route.
5. **Routes are branches of the stage graph** (the human, 2026-11-05). Rejected: a route as a list of stages that the intake writes into the work item, because the factory would have to keep a route per story and count rounds against it, for a need seen once; it stays possible later. Also rejected: sending a documents-only story from the intake to the existing `docs` stage, with a third way out of `docs` to `docs-approval`. That skips the review of the finished text, and since only `next[0]` is a forward move, the way to `docs-approval` would count as a round of rework: with the round cap of 2, the human could send such a story back only once.
6. **A way back to the code route** (the human, 2026-11-05). A documenter at `docs-only` that finds the story needs a change outside the documents ends with `tests` and names that change. The story then takes the code route to `approval`, and a close there sends it to `doing`. `docs-only` has no round cap, so the move counts no round. What the documenter already wrote stays on the branch, and the `docs` stage of the code route finishes it.
7. **Leaves for the acceptance's two stories** (the human, 2026-11-05). In S0004 the tester may change the row `acceptance` of `tests/pipeline/application/test_docs_route.py::test_only_the_docs_routes_working_stages_lie_before_the_approval` from `False` to `True`, and nothing else in that module. In S0005 the tester may remove the `HEADINGS` tables and the tests that read them from `tests/guards/test_project_guide_files.py` and `tests/guards/test_operator_guide_files.py`, and merge the two index tests of the project guide's guard into the one test the Interface names; nothing else in those modules. Each entry names the earlier test files it changed. Reason: the headings may change in the rewrite of the guides, and the docs route must stay open for it.
8. **A leave for the second acceptance's story S0006** (the human, 2026-11-06). The tester may remove `STYLE_RULES` and `test_the_reviewer_in_docs_review_lists_each_style_rule_once` from `tests/agent_files/test_claude_agent_texts_docs_route.py` and add the one test that criterion 1 names; nothing else in that module. The entry names the change. Reason: the style page exists, so the reviewer's own copy of the rules is a stopgap that has run out.
