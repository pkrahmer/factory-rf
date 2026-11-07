---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 619
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T02:26:18.704425Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T02:26:18.712083Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T02:26:34.915531Z'
  stage: intake
  run: 28486f415358463cb254047a9233ada2
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T02:26:39.711230Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T02:31:16.047462Z'
  stage: docs-only
  run: 4cad78abdee1490794204e6ab1560f82
---

# The operator guide's index reads for the operator

## Description

`docs/operator-guide/README.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/README.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/README.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/README.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/README.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/README.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: it changes only `docs/operator-guide/README.md` and `docs/checked-documents.txt`, both under `docs/*`, so the story takes the docs route. It names no code, test or agent file, and says that none changes. Links to changed headings are covered.
   - Criteria: criteria 1 and 2 are judged by the reviewer against the style guide and the code, which is how the feature's decision 2 defines them for this route. Criterion 3 is checked by `make documents` printing `documents ok` and by the list entry. Criterion 4 is a link check. Criterion 5 is `make check`. The Interface's one-line list entry and its heading-link rule are covered by criteria 3 and 4. No rule here has a failing side that needs its own criterion.
   - Smoke test: `grep -cx "docs/operator-guide/README.md" docs/checked-documents.txt` is runnable and has no pytest options. Its `Expect: 1` is checkable against the output.
   - Docs criterion: it names what the reader must know (criteria 1 to 4), not sentences to write. It says `docs/decisions.md` gets no change.
   - Architecture: it touches no code, so the layers are not affected. It leaves out the playbook, `decisions.md` and `docs/runs/`, which `CLAUDE.md` keeps for the human.
   - Scope: it is S0011 of F0054 and matches the story list in `feature.md`. It is not in "Out of scope".
4. factory: started docs-only as vm.
5. documenter: Files changed:
   - `docs/operator-guide/README.md`: rewritten for the operator.
     - It now opens with what the guide is for and what the machine is, then a numbered "Where to start" list, then a table of the ten topic files, then a pointer to `decisions.md`.
     - The two "Replaced" sections are gone, with their feature and story IDs and version names (style rules 1 and 7). The facts that are still true are in a new *Reference* section at the end: the containers are the only stage environment; the three required variables; a setting file that holds an unread variable is harmless; the container runs as `factory` with `--userns=keep-id` and mounts the dataset only; the token stays on the host; the agent's home is `home/` and the rollback clears it; the take, and the journal line `The factory left out changes outside the write paths: ...`; a pipeline definition with `tool_paths` is refused; the stage image and the credential helper paths; `factory-watch` has no follow mode; and where the planning history is kept (the tag `planning-history-2026-10-19`).
     - I checked these claims against the code: `src/factory/machine/application/stage_environment.py`, `src/factory/machine/adapters/podman_runs.py`, `src/factory/work/domain/decisions.py`, `src/factory/pipeline/domain/pipeline_definition.py` (every model is `extra="forbid"`), `src/factory/shared/domain/settings.py`, `operator/vm/setup.sh` and `src/factory/entry/wiring.py`. I did not run `tool_paths` through the loader. "Refused" rests on the `extra="forbid"` models and on the old text.
     - Each glossary word is linked at its first use.
   - `docs/checked-documents.txt`: added `docs/operator-guide/README.md`.
   - `README.md` (line 28): it pointed to *Replaced in v1.2* in the guide's index, which no longer exists. It now says the guide's index is `docs/operator-guide/README.md`. This is the link fix the Interface asks for (criterion 4).

   Dropped on purpose, for the reviewer (criterion 2):
   1. The document check (`REPLACED_PHRASES` and `GLOSSARY_FORBIDDEN` in `src/factory/shared/domain/documents.py`) flags outside an exempt section `factory-last-line`, `factory-run.json`, `factory-tick.lock` and `stage table`. The check blocked them as `describes a replaced behaviour`, so I left them out. The three v1 files in `.git/` and the `factory-last-line` file are no longer named; the follow-mode statement stays without the literal option name.
   2. Pure history of removed things, which the code no longer has and style rule 7 forbids: `factory-confine`/Landlock, the `agent` user and its `sudo` chain, `FACTORY_AGENT_USER`, `factory.entry.leftovers`, `factory.entry.fresh_home`, the checkout seal and the `nested_repository` stop, `UndoService`, the Docker image and compose file, `docker exec`, and the records contract rising to `3.0`. The decision log already records the replacement (`docs/decisions.md`, the "Replaced in v1.2" entry). The story says `docs/decisions.md` gets no change, so I wrote nothing there.
   3. The v1.1 pointer (tag `v1.1`) and the "v1.2" and "v1.1" names.

   `make documents` ends with `documents ok (13.6 s)`. The file has no `console` example blocks, so none ran. I did not run `make check`, because I changed only documents.

   Cross-read and found current: the links from `work-items.md` and `health.md` to the index, and the other nine files of the guide, which link back to `README.md` as a whole.

   Stale text seen, not touched:
   - `README.md` (root) still has a "Replaced from v1" section and v1.1 history in "How it is built". It is not this story's.
   - `docs/project-guide/README.md` line 21 and `docs/project-guide/shared.md` line 97 describe the document check's exemption of the *Replaced* sections. They are still accurate for the code. They would change only if a later story removes those exemptions.
   - `docs/project-guide/machine.md` and `agents.md` have "Replaced in v1.2" sections, and the *Not checked yet* report lists unresolved names in the project guide. These belong to the stories for those files.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (13.7 s)
