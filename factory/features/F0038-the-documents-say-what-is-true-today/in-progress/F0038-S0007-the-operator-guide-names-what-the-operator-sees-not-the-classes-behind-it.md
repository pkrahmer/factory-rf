---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 395
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-21T07:45:16.471373Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T07:42:34.152866Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T07:42:34.159657Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T07:43:01.540025Z'
  stage: intake
  run: 387a1562423248168c291c53d318af9b
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T07:43:23.263174Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T07:44:55.517390Z'
  stage: tests
  run: 632751e6dd75406fa2ef13b53032d078
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T07:45:16.471373Z'
  stage: doing
---

# The operator guide names what the operator sees, not the classes behind it

## Description

`docs/operator-guide.md` names about twenty classes and modules that an operator never sees: `PatientRuns` and `factory.application.provider_limits`, `machine_extras`, `TimestampedFactoryLog`, `StopService.post`, `AskHandler`, `CommentHandler`, `AcceptanceReader` and `factory.application.acceptance_reading`, `HandOverHandler` and `factory.application.handlers.hand_over`, `AcceptanceHandOver`, `SplitByWorkItemKind`, `AcceptanceMerged`, `AcceptanceClosed`, `MergedHandler`, `ClosedHandler`, `DuplicateHandler`, `PullRequestLookupHandler` and `factory.application.handlers.lookups` (F0039-S0005 already removed `NOT_YET_HANDLED` and its clause). They make the guide longer and tie it to refactors, and the project guide already names every one of them for the agents. In *An event that keeps failing* stands a hypothetical case written into the current rule: "Should a future kind have none, the event leads to this:", followed by a paragraph that does not finish the thought, about a case that cannot happen today. This story takes those names out of the operator guide, keeping in each sentence what the operator sees (a log line, a comment, a commit subject, a stop id), and removes the hypothetical case (findings M2 and M3 of the documentation review of 2026-10-20). These names stay, because the operator reads them in a message or uses them to find a rule: the error names in reports and messages (`SettingsInvalid`, `CannotHandle`, `PushFailed`, `HostingServiceError`), `STOP_TABLE` in `factory.domain.stop_table`, and `factory.domain.settings.read_settings`. No passage moves to the project guide, and the stop tables are F0038-S0008's.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, and no other file:
   - None of these names occurs in the guide after the story: `PatientRuns`, `machine_extras`, `TimestampedFactoryLog`, `StopService`, `AskHandler`, `CommentHandler`, `AcceptanceReader`, `HandOverHandler`, `AcceptanceHandOver`, `SplitByWorkItemKind`, `AcceptanceMerged`, `AcceptanceClosed`, `MergedHandler`, `ClosedHandler`, `DuplicateHandler`, `PullRequestLookupHandler`, `NOT_YET_HANDLED`, and no module name that starts `factory.application.` or `factory.entry.wiring`.
   - Each sentence that held one of them keeps what it says the factory does, in the operator's terms: "The handler of `ask` (`AskHandler`) does both steps." becomes "The factory does both steps when it handles `ask`."; "The merged handler (`MergedHandler`) then archives it" becomes "The factory then archives it"; "The closed handler (`ClosedHandler`) then discards the story" becomes "The factory then discards the story"; "`ClosedHandler` then sends the story back" becomes "The factory then sends the story back"; a sentence that only says which class does a thing ("`AcceptanceMerged` (in `factory.application.acceptance`) does it, in one tick.") becomes "The factory does it in one tick.", or is removed where the paragraph already says so. The documenter writes the other sentences the same way.
   - In *An event that keeps failing*, the paragraph on the registered handlers ends "... are registered: every kind of event has a handler.". The sentence that follows those words in that paragraph, "Should a future kind have none, the event leads to this:", and the whole next paragraph ("It ends in the one report ... A push to the branch makes the factory try again.") are removed.
   - `SettingsInvalid`, `CannotHandle`, `PushFailed`, `HostingServiceError`, `STOP_TABLE` and `factory.domain.settings.read_settings` stay where they are. No heading changes. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -E 'PatientRuns|machine_extras|TimestampedFactoryLog|StopService|AskHandler|CommentHandler|AcceptanceReader|HandOverHandler|AcceptanceHandOver|SplitByWorkItemKind|AcceptanceMerged|AcceptanceClosed|MergedHandler|ClosedHandler|DuplicateHandler|PullRequestLookupHandler|NOT_YET_HANDLED|factory\.application\.|factory\.entry\.wiring|Should a future kind' docs/operator-guide.md || true
```
Expect: `0`

```bash
grep -c -F -e '`STOP_TABLE`' -e '`SettingsInvalid`' docs/operator-guide.md
grep -c -F 'every kind of event has a handler' docs/operator-guide.md
```
Expect: a number of at least `2`, then `1`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/operator-guide.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is right for a documents-only story. Nothing under `src/` changes and no signature is needed. The only file the documenter touches is `docs/operator-guide.md`.
   - Criteria: each is checkable. Criterion 3's first bullet is a name list that a grep checks. The second bullet gives example rewrites and says how to treat the rest. The third bullet gives exact text to cut. I confirmed in the guide that the paragraph ending "every kind of event has a handler. Should a future kind have none, the event leads to this:" exists (line 1469) and that the paragraph "It ends in the one report ... A push to the branch makes the factory try again." follows (line 1471). The kept names have their own check (`STOP_TABLE`, `SettingsInvalid` and the others stay). The Interface states no rule with a failing side, so there is nothing to test for one. Criterion 1 (nothing outside the docs changes) is checked by smoke test 3.
   - Smoke test: the commands run. The grep with `|| true` prints `0` when nothing matches. The `grep -c` of the kept names counts 2 lines today, which meets "at least 2". The `git diff --name-only` command is valid. No command runs pytest; the pytest `-q` addopts rule does not apply. `make documents` ends with `documents ok`, which `check_documents.py` prints. Each `Expect:` line can be checked against the output.
   - Architecture: this is a docs change only and respects the layers. It follows `CLAUDE.md`'s rule that the documenter keeps `docs/`. Nothing moves to the project guide, and the stop tables stay with S0008.
   - Scope: this is within F0038's scope, S0007 (findings M2 and M3), and does not touch "Out of scope" items. Decision 7 of the feature matches the names the story keeps.
4. factory: started tests as self.
5. tester: I wrote no tests. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` has changed, because criterion 1 forbids any change under `tests/` and the Interface is "None".
   - criterion 1 (nothing under src/, tests/, image/, template/, demo/, claude/ changes): no test function. Smoke test 3 checks it with `git diff --name-only origin/main`. This entry is the tester's half of the statement the criterion asks for.
   - criterion 2 (`make check` stays green): no test function. The factory's own `make check` covers it.
   - criterion 3 (docs: names removed from `docs/operator-guide.md`, hypothetical paragraph cut, kept names stay, `make documents` ends `documents ok`): no test function. A pytest test would be a change under `tests/`, which criterion 1 forbids. Smoke tests 1, 2 and 4 and the docs stage's `make documents` check it.
   Files created: none. Modules the test run could not import: none, since no new tests exist. I skipped the `make test` run that step 2 calls for: with no new tests there is no red test to confirm, and the factory runs `make test` after this stage. `make lint`: green (0.2 s). Nothing is open.

   `lint`: lint: green (0.7 s)
   `test`: test: green (66.6 s)
6. factory: started doing as self.
