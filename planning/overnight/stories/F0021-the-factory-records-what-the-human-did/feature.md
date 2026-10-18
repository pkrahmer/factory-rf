# The factory records what the human did

## Goal

The factory should one day run alone instead of under an LLM on watch, and nobody can say how far it is from that while the human's part is only prose. This feature makes that part data:

- every question that blocks a work item records its cause, and every stall its reason;
- the cost table on the pull request and the acceptance's facts count the questions the human answered and the hours the work item waited for them;
- every stop of the repository or the machine reaches `main` as a record;
- every agent run's record counts the tool calls the agent runtime refused.

Everything new lives in the work item's front matter (YAML) or in a JSON-lines file. A contract of generated JSON Schemas says what a reader outside the factory may rely on: the status-map viewer (`planning/overnight/restructure-after-f0011.md`, "The status map") first, a separate repository later. Such a reader computes everything from those records and never parses prose.

Two agent texts change as well, so that two recurring questions no longer reach the human. The reviewer passes test-quality points on as notes from round 1 on and may add a criterion that pins behaviour already built. The operator guide says never to edit a running work item on `main`.

The feature is built before F0020, so that F0020 adds its spend-limit waits to a run record that already has room for them. Done when every story below is merged and `make check` is green.

## Scope

- The cause on the record: a journal record of kind `question` gains an optional `blocked` (the block it opened), and a record of kind `stall` an optional `reason` (the stall reason the code already distinguishes). Every place that records a blocking question or a stall writes it. Old records without the fields stay valid (S0001).
- The human's waits, computed from those records: one wait per blocking question, from its `at` to the `at` of the next record the human spoke, with its cause. They give the line `<n> questions answered (<cause> <count>, ...), <hours> h waited` (S0001).
- That line under the cost table the hand-over posts on the pull request, for a story and for an acceptance, and as a line of the acceptance reviewer's facts, summed over the archived stories (S0001).
- The stops on GitHub (S0002, decisions 1 to 3):
  - each stop of the repository or the machine writes a `raised` record when it is first raised and a `cleared` record when it clears, first to `records/stops.jsonl` in the state directory;
  - every tick after a successful fetch pushes the records `main` does not hold yet to `factory/stops.jsonl` on `main`.
- Room in the run record: the cost record of a completed run gains `denials` (how many tool calls the agent runtime refused, whatever refused them) and `denied_paths` (the files they named). Both are optional and left out of the sidecar line when unknown (S0002, decision 8). F0020 adds its spend-limit waits to the same line, as optional fields again (decision 9).
- The texts (S0003):
  - the reviewer's notes from round 1 on and its leave to add a criterion;
  - the coder's hand-on of such a criterion to the tester;
  - the acceptance reviewer's use of the new facts line;
  - the operator guide's rule never to edit a running work item on `main`.
- The records contract (S0004):
  - JSON Schema files generated with Pydantic's `model_json_schema` from the models that validate each record: the work item's state and an acceptance's state with their journal records, one cost record line, one stop record line, and the pipeline definition;
  - committed under `src/factory/contract/` with the records contract's version `1.0`;
  - a command that regenerates them, and a test that fails when they differ from the models;
  - an operator-guide section on what a reader outside the factory may rely on.

  The contract names no stage, no role and no reader.

## Out of scope

- The status-map viewer itself, and any reader of the new data besides the cost table post and the acceptance facts.
- A reason on a `crash` or `expiry` record: the factory records a crash when it finds its own claim without a run behind it, and it does not know then why the run ended (decision 4).
- Refusals that the agent runtime does not report as refused tool calls, such as the kernel's: they are only text in a tool's output (`Permission denied`, `EACCES`) inside the agent's transcript, and the factory does not parse them.
- F0020's spend-limit waits, and reading opencode's refused tool calls: F0020 adds both (its S0004 reads them from the runtime's events into the same `permission_denials`).
- The stop written by `factory-run` itself when the settings are invalid (`entry/run.py`, `_stop_the_machine`). It is written before any boundary exists and has no instance name, so it stays in the health status and the factory log only.
- The journal entry and the bill at `done` (`done_entry_text`): unchanged.
- A field for the agent's decision on a `result` record. Send-backs per stage are computed from the `stage` of consecutive records and the pipeline definition's `next` lists (the first entry forward, every other one a rework). The human's own send-back is a `send_back` record.
- The health status: a stop raised again keeps replacing the stop of the same reason, `at` included, as today.
- A JSON Schema validator library: no new dependency (decision 16).

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The journal records why a work item waited or stalled, and the cost table counts the human
- S0002: The stops and the refused tool calls reach the remote as records
- S0003: The reviewer's notes and leave, and the rule never to edit a running work item on main
- S0004: The records carry a contract of generated JSON Schemas

## The human's changes

Checked against `factory/pipeline.yml`:

- The coder writes `src/*`, `image/*`, `template/*` and `claude/*` (S0001 to S0004, including the agent texts of S0003 and the schema files under `src/factory/contract/` of S0004).
- The tester writes `tests/*`.
- The documenter writes `README.md` and `docs/*` (including the operator guide's sections of S0003 and S0004).

There is no new dependency (S0004 uses no validator library, decision 16) and no new console script (S0004's command runs as `python -m factory.entry.contract`). There is no `Makefile` target, no `security/` or `.secrets.baseline` change, and no change to `CLAUDE.md` or `factory/pipeline.yml`. `factory/stops.jsonl` on `main` is written by the factory process at run time (S0002), as it writes archived stories under `factory/features/`; no agent writes it and the human does not create it.

1. Before F0021's acceptance (its `make mutants`), recommended before S0004 starts: in `pyproject.toml`, `[tool.mutmut]`, `pytest_add_cli_args`, add a new line after the last `--deselect` line:

   ```toml
       "--deselect", "tests/entry/test_contract.py::test_the_committed_schemas_are_the_generated_ones",
   ```

   The test reads the committed schema files under `src/factory/contract/`, which mutmut's copy of the source may not hold. A test that fails on the unmutated copy stops the mutmut run. The line is harmless before the test exists: pytest ignores a deselection that matches nothing.

After S0002 is merged and the image rebuilt, expect one commit `stops recorded` on `main` after each stop that is raised or cleared (decision 1).

## Decisions taken for the human

1. Where the stops of the repository and the machine are recorded (S0002).
   - Recommended and built: `factory/stops.jsonl` on `main`, one JSON line per event, written by the factory. Each event is written first to `records/stops.jsonl` in the instance's state directory. Every tick after a successful fetch pushes to `main` the records `main` does not hold yet.
   - A stop can never be lost because git failed: the local record waits until a push works, and a record `main` already holds is never pushed twice.
   - Rejected:
     - a branch of its own, such as `factory-records`: the viewer would read a second ref, and the factory would keep a second branch alive beside the work items' branches;
     - a GitHub issue or a comment: the hosting-service interface does pull requests only (R10);
     - the instance's records alone: the viewer cannot reach `/state`.
   - The cost: one commit on `main` per stop event, and one run of the preflight's `lint` probe on that new commit, as after every archive.

   (This feature's draft.)
2. The published stop record holds no `detail` (S0002). The detail stays in the factory log and the health status. `make secrets` reads every tracked file on `main`, and a git error's text can hold a commit id or a URL; a red `make secrets` on `main` would raise `main_branch_failing`. (This feature's draft.)
3. Two events per stop, `raised` at the first raise and `cleared` at the clearing, instead of one record with both times at the clearing (S0002). The health status rewrites a standing stop's `at` on every tick that raises it again, so the first time is only known at the first raise. A standing stop also reaches `main` without waiting for its end. A raise whose record cannot be written (a full disk) leaves a `cleared` record without its `raised` one, and the viewer shows that stop's start as unknown. (This feature's draft.)
4. `crash` and `expiry` records carry no `reason` (S0001). A crash is the factory finding its own claim with no run behind it, after a restart or after an iteration that raised. The error type is a line `iteration failed: <type>: <error>` in the factory log, written at a moment when the work item cannot be written. The kind already tells a crash from an expiry. A later feature may record the failed iteration on the work item. (This feature's draft.)
5. A wait for the human ends at the next record the human spoke, a `comment` or a `close`, not only at a comment (S0001); the crash-cap question offers the close as the other answer. One rare case is counted as answered although the factory did not take it as the answer: a comment written after the question was recorded but before it was posted. The records cannot tell the two apart. (This feature's draft.)
6. Only a `question` record with a `blocked` value is a wait (S0001). A question the agent asked in a run that then stalled blocks nothing and gets no `blocked`. Records written before S0001 have no `blocked` and count as no wait; the viewer may show them as waits of unknown cause. (This feature's draft.)
7. The factory's question about form findings (rule 1) and the agent's own question (rule 2) share `blocked: question`; the record's `speaker` tells them apart. (This feature's draft.)
8. The refused tool calls in the run record (S0002).
   - What is counted: the tool calls the agent runtime reports as refused (`permission_denials`), whatever refused them: a permission or deny rule of the runtime's settings, or anything else the runtime reports there. Under opencode, F0020 fills the same list from its own permission rules.
   - `denials` counts them all. `denied_paths` lists the `file_path`, or else the `notebook_path`, of the refused calls that name one, each path once, in the order reported.
   - Both are `None`, and so left out of the line, for a run that ended `died` or `time_limit`, since the runtime gave no reply (R24: unknown is never 0).
   - One use of the count: F0019's decision 16 (the cross-check of the write guard) becomes a count over the sidecars.

   (This feature's draft, worded by the human on 2026-10-18.)
9. F0020 adds its spend-limit waits to the run record as optional fields left out of the line when absent, like `instance`, `denials` and `denied_paths`. (The human's word of 2026-10-18.)
10. "From round 1 on" (S0003): the reviewer passes test-quality points on as notes when its prompt names round 1 or higher, that is from the second review on; the first review (round 0) may still send them back once. (The human's answer of 2026-10-18 to this feature's draft.)
11. The reviewer's added criterion goes through `doing` (S0003). The review stage's `next` is `[docs, doing]`, so the reviewer ends with `doing`, the coder ends with `tests` without a code change, and the tester writes the test. One round is counted for it, like any send-back. (This feature's draft.)
12. The operator guide's rule is pinned by S0003's smoke test (a `grep` of its heading), not by a pytest test. The documenter writes it in the docs stage, after the doing stage's `make check`, and a pytest pin on `docs/` would turn that check red. The reviewer's and the coder's texts are pinned by pytest tests, as `tests/test_claude_agent_texts.py` pins the others. (This feature's draft.)
13. Leave to change tests other stories wrote (S0001). Each change only adds the new field or line to an expected value, and nothing else:
    - `tests/application/handlers/test_questions.py`: the two expected attempts-cap question records gain `blocked="attempts_cap"`.
    - `tests/application/test_stalls.py`: the two expected stall records gain the stall's `reason`.
    - `tests/application/test_recovery_cap.py` and `tests/application/test_recovery_expiry.py`: the expected crash-cap question record gains `blocked="crash_cap"`.
    - `tests/application/handlers/test_hand_over.py`: `_expected_post` passes the human line of the test's journal to `cost_table_post`.
    - `tests/application/test_stage_run_acceptance.py` and `tests/application/test_task_acceptance.py`: the prompt's last lines compared with `facts.lines()` grow by one, the facts' new line.
    - Any other assertion of an earlier test that compares a whole `question` or `stall` record, or the whole cost table post, gains the new field or line in the same way; the tester names each file in its entry.

    (This feature's draft.)
14. Leave to change a test another story wrote (S0002): in `tests/adapters/test_claude_runtime_resume.py`, the expected denial of the `Write` call with `{"file_path": "x"}` gains `path="x"`. Any other expected `PermissionDenial` of a call naming a `file_path` or `notebook_path` gains its `path` in the same way, and the tester names each file in its entry. (This feature's draft.)
15. The records contract's place and version (S0004).
    - Place: the schemas live under `src/factory/contract/`, in the coder's write path and shipped in the wheel. A reader in another repository fetches them from `main`. Rejected: a folder at the repository's root such as `contract/`, which needs the human to add it to a role's `write_paths` in `factory/pipeline.yml`, for no gain.
    - Version: each schema carries `x-records-contract: "1.0"`, the records contract's own version, separate from the pipeline definition's `contract`, which versions the file the human writes.
    - When it rises: the major on a field removed or renamed, a type narrowed, a value of a closed set removed, or a meaning changed. The minor never; an optional field added, or a value added to a closed set, keeps the version. A reader therefore ignores a property it does not know, although the generated schemas say `additionalProperties: false`, which states what this version of the factory writes. The reviewer checks the rule on every schema change; the test only catches a model change without regenerated schemas.
    - A Pydantic upgrade that changes the generated schemas fails the test as well; the regenerated files go into the same change.

    (This feature's draft, from the human's requirement of 2026-10-18.)
16. No JSON Schema validator library (S0004). `jsonschema` is in `uv.lock` only as another tool's dependency, and declaring it is a new dependency. The tests compare each schema's `required` and `properties` with the model's fields instead. (This feature's draft.)
