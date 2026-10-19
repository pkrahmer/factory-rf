---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 275
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-19T17:46:06.086777Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T17:39:46.681908Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T17:39:46.689564Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T17:40:02.255072Z'
  stage: intake
  run: 1d0368e5687b46c991e7c32e181c83c3
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T17:40:23.060880Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T17:43:17.724949Z'
  stage: tests
  run: 6c64ca6592c543b5bcaf2d9ccfbbb8de
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T17:43:37.949415Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T17:45:45.068008Z'
  stage: doing
  run: 57c2627496f7419b8dde38fb0229f8bd
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T17:46:06.086777Z'
  stage: review
---

# The claim service's refusals name their cause

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

`ClaimService` (`factory.application.claims`) refuses, with `ValueError` and before it writes anything, in these cases: a name that is no instance name; a claim for a stage other than the work item's; a stage the pipeline definition does not have; a stage without a role; a branch that is not the work item's own; a path that is no work item's file; and a checkout on another branch. When a tick meets one of these, its message is what the factory log's line of the failed iteration shows the operator. The tests in `tests/application/test_claims.py` match the message with `r".+"` or `r".*"`, which `"None"` also passes, so F0026's mutation run left seven mutants alive that replace a message with `None`. This story pins each message's text with new tests and changes no code. The refusals themselves, their order and the claim are unchanged, and so is `tests/application/test_claims.py`.

## Interface

No module under `src/factory/` changes. The behaviour pinned is that of `ClaimService(boundaries, instance, definition)` and `ClaimService.claim(branch, path, document, stage)` in `factory.application.claims` (application), as they are. Each refusal is a `ValueError` whose `str` is:

- a bad instance name `<name>`: `not an instance name: '<name>'` (the name's `repr`);
- a document at stage `<state stage>` claimed for `<stage>`: `the work item is in stage <state stage>, not <stage>`;
- a stage that is not in the definition: `<stage> is not a stage of the pipeline definition`;
- a stage without a role: `stage <stage> has no role to claim it for`;
- a branch other than the work item's own: `<branch> is not the work item's branch <own branch>`;
- a path whose file name is no work item's: `<path> is not a work item's file`;
- a checkout on another branch: `the checkout is on <checked-out branch>, not on <branch>`.

Tests (the tester writes them): `tests/application/test_claims_refusals.py` (new), on the `boundaries` fixture and the test remote's pipeline definition (`definition` in `tests/conftest.py`), whose `approval` stage has no role. No earlier test changes.

## Acceptance criteria

1. `ClaimService(boundaries, name, definition)` (rows of one parametrized test): `"Factory-1"` raises `ValueError` whose `str` is `not an instance name: 'Factory-1'`, and `""` raises one whose `str` is `not an instance name: ''`. `"factory-1"` is accepted.
2. `claim("work-item/F0001-S0001", <F0001-S0001's in-progress path>, document, stage)`, with the checkout on `work-item/F0001-S0001` (rows of one parametrized test, one per refusal; each row also checks that the remote and the working tree are as before):
   - a document at `doing` claimed for `review` gives `the work item is in stage doing, not review`;
   - a document at `nosuch` claimed for `nosuch` gives `nosuch is not a stage of the pipeline definition`;
   - a document at `approval` claimed for `approval` gives `stage approval has no role to claim it for`;
   - the branch `work-item/F0001-S0002` gives `work-item/F0001-S0002 is not the work item's branch work-item/F0001-S0001`;
   - the path `factory/features/F0001-example/in-progress/notes.md` gives `factory/features/F0001-example/in-progress/notes.md is not a work item's file`;
   - the checkout on `main` gives `the checkout is on main, not on work-item/F0001-S0001`.
3. `make check` stays green.
4. docs: none. The project guide's *The claim service* already says that `claim` refuses with `ValueError` before writing anything. The texts are for the log and are not described anywhere.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python - "$d" <<'EOF'
import subprocess
import sys
from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.application.claims import ClaimService
from factory.domain.settings import InstanceSettings
from factory.domain.work_item import WorkItemDocument, WorkItemState
from factory.entry.wiring import build_boundaries

d = Path(sys.argv[1])
subprocess.run(["git", "init", "-q", "--initial-branch=main", str(d / "checkout")], check=True)
settings = InstanceSettings(repository_url="https://github.com/example/project.git", instance="self", checkout=d / "checkout", state_directory=d / "state", agent_home=d / "agents-home")
boundaries = build_boundaries(settings, "unused", hosting=FakeHostingService())
definition = boundaries.pipeline_reader.parse('contract: "1.0"\nproject_commands:\n  check: {time_limit: 10}\nroles:\n  coder: {write_paths: ["src/*"]}\nstages:\n  doing: {role: coder, next: [approval], checks: [check]}\n  approval: {approval: true, next: [done]}\n  done: {}\n')
story = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"


def refusal(make) -> None:
    try:
        make()
    except ValueError as error:
        print(error)


refusal(lambda: ClaimService(boundaries, "Factory-1", definition))
service = ClaimService(boundaries, "self", definition)
at = lambda stage: WorkItemDocument(state=WorkItemState(stage=stage), body="# First story\n")
refusal(lambda: service.claim("work-item/F0001-S0001", story, at("doing"), "approval"))
refusal(lambda: service.claim("work-item/F0001-S0001", story, at("nosuch"), "nosuch"))
refusal(lambda: service.claim("work-item/F0001-S0001", story, at("approval"), "approval"))
refusal(lambda: service.claim("work-item/F0001-S0002", story, at("doing"), "doing"))
refusal(lambda: service.claim("work-item/F0001-S0001", "factory/features/F0001-example/in-progress/notes.md", at("doing"), "doing"))
refusal(lambda: service.claim("work-item/F0001-S0001", story, at("doing"), "doing"))
EOF
```
Expect: seven lines, `not an instance name: 'Factory-1'`, `the work item is in stage doing, not approval`, `nosuch is not a stage of the pipeline definition`, `stage approval has no role to claim it for`, `work-item/F0001-S0002 is not the work item's branch work-item/F0001-S0001`, `factory/features/F0001-example/in-progress/notes.md is not a work item's file` and `the checkout is on main, not on work-item/F0001-S0001`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: no src change; the seven refusal texts are stated exactly and match the f-strings in `src/factory/application/claims.py` (lines 43, 91, 95, 98, 103, 106, 131). The new test module and its fixtures (`boundaries`, `definition`) are named.
   Criteria: each is testable by one parametrized test function; every refusal text has a row, and criterion 1 covers the accepted side (`factory-1`) as well as both refused names; each claim row also checks that the remote and working tree are unchanged. Interface texts without a failing side: none.
   Smoke test: runnable as a heredoc with real wiring and a fake hosting service; the Expect line lists seven checkable lines, in the order of the script's calls.
   Architecture: tests only, in the application test folder; no layer is touched, and no earlier test changes.
   Scope: inside F0026's goal of killing the survived mutants in claims.py; no listed out-of-scope item is touched. Note: feature.md's Scope and Stories list only S0001, while this story was proposed by the feature acceptance. This is the human's to start, so I did not question it.
4. factory: started tests as self.
5. tester: Wrote the tests that pin the text of each `ValueError` refusal from `ClaimService`. Each row checks `str(caught.value)` for equality with the exact message.

   - criterion 1: tests/application/test_claims_refusals.py::test_service_refusal_of_an_instance_name_quotes_the_name. It has three rows: `"Factory-1"` and `""` are refused with the quoted name, and `"factory-1"` is accepted.
   - criterion 2: tests/application/test_claims_refusals.py::test_claim_refusal_names_its_cause_and_writes_nothing. It has six rows: other-stage, unknown-stage, stage-without-role, other-branch, no-work-item-file and checkout-on-main.
     - The `prepared` fixture puts the work item at `doing` on its own pushed branch, `work-item/F0001-S0001`. The checkout stays on that branch unless the row is checkout-on-main.
     - Each row compares a snapshot taken before and after the claim: git status, the text of the work item file and of `notes.md`, and the remote's branch commit.
     - The tests use the `boundaries` and `definition` fixtures from `tests/conftest.py`.
   - criterion 3 (`make check` stays green) and criterion 4 (docs: none) need no test.

   Files created: tests/application/test_claims_refusals.py. No earlier test file was changed.

   Modules the test run could not import: none. The story changes no code, so these tests pass already: `make test` was green, and these tests are not red for the coder. The coder has only to keep `make check` green. Whether the seven mutants in `claims.py` are now killed is for the `mutants` report to show.

   `make lint` is green. I ran `ruff format` on the new file to fix its line wrapping.

   One choice I made: the new module keeps its own small `_snapshot` and `_file_text` helpers rather than sharing the ones in `tests/application/test_claims.py`. The story says that file stays unchanged, so I did not move them to a shared place under the standing leave.

   `lint`: lint: green (0.0 s)
   `test`: test: green (48.6 s)
6. factory: started doing as self.
7. coder: I built nothing. The story says no module under `src/factory/` changes, and the tester's `tests/application/test_claims_refusals.py` already passes against `src/factory/application/claims.py` as it is. I changed no file under `src/` or `tests/`. I ran `make check` in the foreground and it ended with `check: green` (`test: green (47.7 s)`, total coverage 99.07 %).

   Main choice: I left the seven refusal messages in `claims.py` exactly as they are, because the story pins their current text. The alternative I rejected was moving them into named constants or one message helper: that would be a restructuring the story rules out, and the tests compare the text, not where it is defined.

   Refactor: the diff contains no code of mine, so there was nothing to refactor.

   Description: no journal entry changed what the task means, so I left `## Description` as it is.

   Noticed but did not touch:
   - The tester's own `_snapshot` and `_file_text` helpers in `test_claims_refusals.py` repeat the ones in `tests/application/test_claims.py`. The tester explained in their entry why they kept the copies. Moving them to one shared place would be the tester's job under the standing leave, and only if the reviewer asks for it.
   - Whether the seven mutants in `claims.py` are now killed is for the `mutants` report to show; I did not run it.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
