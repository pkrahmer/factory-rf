# The operator guide lists each stop in one table

## Description

`docs/operator-guide.md` describes one stop in up to three tables: *The stops you will see here* (six rows, under *The container: compose, entrypoint and health check*), *The stops* (all fifteen rows, the one `make documents` pins) and *The stops of the tick* (four rows). `checkout_restore_failed` and `pipeline_definition_invalid` are each in all three, and each also has a section of its own. An operator who looks up a stop cannot tell which table is complete, and the wordings drift: three rows of the first table only say "See ..." and "As there". This story makes *The stops* the one table of stop ids, destinations and what to do (finding M1 of the documentation review of 2026-10-20). The six-row table gives way to one sentence that points there, and the facts its rows hold that no other passage holds move into the sections *The stops* already points to. The four-row table gives way to a short paragraph that keeps only what *The stops* lacks: the tick does not touch the checkout while `pipeline_definition_invalid` or `agent_definition_invalid` stands, an expired or revoked token shows as `fetch_failed` and nothing is lost, and what can make `checkout_restore_failed`. The merge of all stop material into one reference and a contents list per stop (the review's structural proposal S1) are the human's to decide; the table of *Stops that cannot be done* (its last errors) stays.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, and no other file:
   - The subsection *The stops you will see here*, its heading and its table, is replaced by one sentence at the end of *The health check and the restart policy*: the stops this container can show in its health status are in "The stops", with what to do about each.
   - What its rows say that the guide says nowhere else is kept in the section the matching row of *The stops* points to: the details `confinement: ...` and `the probe on main could not run: <message>` of `preflight_failed` in "The preflight's items"; the detail forms `lint is red on main at <12 characters of the commit>: <last line of the output>` and `lint reached its time_limit on main at <commit>` of `main_branch_failing` in "The stamp and the probe of the main branch"; and the four detail forms of `repository_unavailable` (`cannot prepare the checkout: <git's message>`, `cannot fetch: <git's message>`, `the repository has no main branch yet`, `origin/main has no factory/pipeline.yml yet`) in "The wait for a repository that is not ready". A detail already written there is not written twice.
   - In *The stops of the tick*, the table is replaced by a paragraph that names the four stops in backticks (`fetch_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `checkout_restore_failed`), points to "The stops" for what to do, and keeps: an expired or revoked token shows as `fetch_failed`, and nothing is lost; the sentence "The tick does not touch the checkout while `pipeline_definition_invalid` or `agent_definition_invalid` stands."; `checkout_restore_failed` comes, for example, from an untracked file or directory the factory cannot remove, and its detail is git's message.
   - *The stops*, its table of fifteen rows and every other section stay as they are, and no citation of a removed heading is left: no passage cites "The stops you will see here". `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -F -e '| Stop | Meaning | What to do |' -e 'The stops you will see here' -e '| As there. |' docs/operator-guide.md || true
grep -c -F '| Stop | Destination | What you do |' docs/operator-guide.md
```
Expect: two lines, `0` and `1`

```bash
for s in 'the probe on main could not run' 'lint reached its time_limit on main' 'origin/main has no factory/pipeline.yml yet' 'cannot prepare the checkout' 'The tick does not touch the checkout while'; do grep -q -F -e "$s" docs/operator-guide.md && echo found || echo "missing: $s"; done
```
Expect: five lines `found`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/operator-guide.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
