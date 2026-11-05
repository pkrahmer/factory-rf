# A documents-only story takes the docs route

## Before it starts

Not started (the human, 2026-11-05): first a discussion of how versatile routes should be, so that this route is one case of a general rule and not a special one. Possible outcomes: routes chosen by the intake from a list in the pipeline definition, a route per kind of story, or this route as it stands. The stories below may change with it.

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
  docs-only: {role: documenter, next: [docs-review], checks: [check, secrets, documents]}
  docs-review: {role: reviewer, next: [docs-approval, docs-only], round_cap: 2}
  docs-approval: {approval: true, next: [done, docs-only]}   # the human: a merge accepts, a close sends back to the documenter
  ```

  and `intake: {role: intake, next: [tests, docs-only]}`. `tests` stays the intake's forward decision; `docs-only` is the other one.
- **At S0003's start:** nothing; S0003 is the first story the intake may send down the new route.

## Decisions taken for the human

1. **A route of its own, not shortcuts on the old one.** The documents-only stories get three stages of their own (`docs-only`, `docs-review`, `docs-approval`) that reuse the documenter and reviewer roles. Rejected: letting the intake jump to `docs` and the documenter jump to `review`, because those moves would count as rework in the old stages' rounds, and a close at `approval` would send the story to a coder who cannot write documents.
2. **The review comes after the writing.** On the docs route the reviewer reads the finished text, judges it against the style page and the docs criterion, and may send it back to the documenter within the round cap of two.
3. **No smoke test on the docs route.** The document check (`make documents`) and `make secrets` run after the documenter, and `make check` reuses its result when only documents changed. A smoke test of prose adds nothing.
4. **The intake decides, by the Interface.** A story goes down the docs route when every path its Interface changes is one the documenter may write (`README.md`, `docs/*`, `operator/README.md`). Anything else takes the old route.
