# Decisions

The log of lasting decisions: what was decided, why, and what was rejected. Newest last. The first entries are the seed's choices (2026-10-12); the stories' decisions follow. Older entries cite the planning records by code: the requirement numbers R1 to R34 (`CLAUDE.md` names R3, R5 to R13 and R17; an R14 or R15 beside an agent's rule is that rule's number in the agents' `## Rules`), the codes WE, L and Q, the kept things and v1's features F0001 to F0017. Those records are kept at the tag `planning-history-2026-10-19`.

## The package is `factory`, in four layers

The code is one package, `src/factory/`, with the layers `factory.domain`, `factory.application`, `factory.adapters` and `factory.entry`. A higher layer may import a lower one (import-linter, `make layers`, part of `make check`). The project is named `factory-rf`; the package carries the factory's own name.

## Three top-level paths for the product beyond `src/` and `tests/`

`image/` (Dockerfile, compose file, entrypoint), `template/` (v1.1's own project template) and `claude/` (the agent and skill files v1.1 ships). The coder's write paths in the pipeline definition (`factory/pipeline.yml`; v1's `factory/stages.yml` until the handover of 2026-10-18) name them; the folders are created by the stories that need them. `Makefile`, `pyproject.toml`, `uv.lock`, the import-linter configuration, `CLAUDE.md` and `factory/` stay outside every write path.

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## No `mutants` target, no mutmut

Superseded by *Mutation testing is limited to one feature's modules*.

The acceptance reviewer runs `make mutants` only when it exists. Over the whole package it could outgrow the 60-minute lease in later features, and a timeout is a stall. So the seed has neither the target nor the dependency.

## The licence allow list has one LGPL entry and one dual-licence entry

PyGithub is LGPL-3.0, and `pip-licenses` reports it as `GNU Library or Lesser General Public License (LGPL)`, which is now on the allow list. `cryptography` (a transitive runtime dependency, through PyGithub) is reported as `Apache-2.0 OR BSD-3-Clause`, which is also allowed. The template's list is otherwise unchanged.

## The project guide lives in `docs/`

`docs/project-guide/` is the guide for agents (R17). It is in `docs/` and not in `CLAUDE.md` so that the documenter, whose write paths are `README.md` and `docs/*`, can keep it true; `CLAUDE.md` stays the human's, and points to the guide. Since F0025-S0001 the guide is an index and one file per domain (see *The project guide is an index and one file per domain*).

## The one module that starts processes may carry four markers

Date: 2026-10-13. Every command-line tool is reached through one wrapper class (R5), and the wrappers share one function that starts a process, in `src/factory/adapters/process.py`. ruff's S404 and S603 and bandit's B404 and B603 flag any `subprocess` use, and `CLAUDE.md` puts `nosec` markers under "Not without asking". So exactly that module may carry those four markers, on its import and its one `Popen` call. Alternatives rejected: a per-file ignore in `pyproject.toml` (bandit has none, and it would hide the exception from the reader of the code); lowering bandit's severity (loosens the whole package). There are no other markers anywhere under `src/factory`: a second one would be a second place that quietly weakens the checks. `tests/test_process_search.py` fails on any marker (`noqa`, `nosec`, `nosemgrep`, `pragma: allowlist secret`) other than these four on those two lines, and on any other route to a process, so the exception cannot grow unnoticed.

- The `os.execvpe` call and its markers went with the wrapper, v1.2 F0044-S0002; the two on `subprocess` and `Popen` stay.

## `InjectedKill` is a `BaseException`

Date: 2026-10-12. An armed kill point stands in for the factory dying at that moment (WE6.3). A real death runs no handler, so the injected one must not be caught by any either. If `InjectedKill` were an `Exception`, an `except Exception` in a wrapper or a stage would swallow it and the test would show recovery from an error, not from a crash. As a `BaseException` it passes every `except Exception`; only a test's `pytest.raises(InjectedKill)` or a bare `except BaseException` sees it. It is also not a `FactoryError`, which is an `Exception`. Alternatives rejected: an `Exception` subclass (swallowed by the handlers the test is meant to bypass); `os._exit` or a signal (kills the test process and cannot be asserted on).

## A post carries a key, and the marker tells the factory's posts apart

Date: 2026-10-12. Every post the factory makes ends with the marker `<!-- factory -->` and a key comment `<!-- factory key=<work item>:<kind>:<n> -->`. The key makes a post idempotent: a factory that died between posting and recording it (WE6.3) can look at the comments, find the key and not post twice. The marker, not the author, says a comment is the factory's (R34): the factory posts under the operator's own login, so the author is also the human's, and a human's comment must never be taken for the factory's or the other way round. The key is read only from the last non-blank line, so a key quoted in a sentence or followed by more text is not a key. Alternatives rejected: telling posts apart by author (the login is shared); a key anywhere in the body (a quoted key would suppress a real post); a key without a work item (the same kind and number of two work items would collide).

## PyGithub behind the interface, with one error type; not `gh`, a git library or plain httpx

Date: 2026-10-12. The hosting service is reached through one client on PyGithub (R9), and every failing call, whether GitHub answers with an error or cannot be reached, surfaces as `HostingServiceError`. Callers handle one type and never learn PyGithub's or the network's. A search test keeps it so: only the client imports `github`, no other route to the API is imported, and no module names the `gh` tool. Why not the others: `gh` is a second program whose output has to be parsed and whose login is outside our control; GitPython-style wrappers (GitPython, pygit2, dulwich) wrap git, not the hosting service, and git has its own wrapper; githubkit and plain httpx would mean writing and maintaining the request and response handling that PyGithub already has. The client is tested against stand-ins of PyGithub's objects, with no network (WE6.3).

## Global and system git configuration are ignored

Date: 2026-10-13. Every git command of the wrapper runs with `GIT_CONFIG_NOSYSTEM=1` and `GIT_CONFIG_GLOBAL` set to the null device, after the process environment and the options' extra environment, so that nothing can lift them. Git then behaves the same on every machine and in every test: an operator's `insteadOf` rewrite, credential helper, hooks path or default branch cannot change what the factory does, and a crash test (WE6.3) replays the same git. Credentials are not lost: they come from the factory process's environment (`GIT_ASKPASS`, or `GIT_CONFIG_COUNT` with `GIT_CONFIG_KEY_<n>` and `GIT_CONFIG_VALUE_<n>`) and the options' `environment`, which is how the factory's own pushes get the token while the agent run never does. The token is never put in a URL, because git may print one. Alternatives rejected: trusting the user's configuration (the result depends on the machine); a private `HOME` (still reads a file the operator did not write, and breaks other tools that read `HOME`); credentials in the remote URL (printed in errors and logs).

## A push is never forced, and a rejection is a value

Date: 2026-10-13. `GitCli.push` never forces and returns `"pushed"`, `"rejected"` or `"unreachable"` instead of raising for the last two (WE6.3). A push is the only way the remote learns anything, and the factory may die on either side of it (kill points `before-push` and `after-push`); a rejected push (another writer got there first, or a remote hook declined) and an unreachable remote are ordinary results of that uncertainty, which the caller decides on (retry later, ask the human, stop), not failures of the wrapper. Forcing would overwrite what the human or an earlier run pushed and make a rerun after a crash destructive. Anything git did not report as one of those (an unknown local branch, a timeout) stays a `GitError`. Alternatives rejected: raising on rejection (every caller would catch it to do the same thing); `--force-with-lease` (still overwrites a state the factory has not looked at); classifying by git's wording alone (rejection is read from the `!` ref line of `--porcelain`, unreachability only with exit 128).

## A dead, timed-out or over-budget agent run is a result, not an error

Date: 2026-10-13. `AgentRuntime.run` returns an `AgentRunResult` with an end reason (`no_result`, `time_limit`, `budget` or `died`) when the agent did not finish; it raises `AgentRuntimeError` only when the runtime itself cannot be used (WE6.3). These ends are ordinary outcomes of running an agent: the stage handles them the same way, as a stall, and a crash test replays them without special cases. An exception would be caught by every caller to do the same thing, and the measures gathered so far (duration, turns, tokens, cost) would be lost with it. `decision` and `entry` exist only on a `completed` result, so a partial run can never be mistaken for an answer. Measures the runtime did not report are `None`, never 0, so a total never counts a guess. Alternatives rejected: raising for each end reason (callers would convert them back into stalls); a `decision` on a run that ended early (a half-written answer would look final).

## Interfaces are abstract base classes that the factory's own implementations inherit

Date: 2026-10-13, decided by the human. `Git`, `HostingService`, `ProjectCommands` and `AgentRuntime` derive from `abc.ABC`, every operation is an `@abstractmethod` whose body is its docstring alone, and every implementation the factory writes, the fakes included, inherits its interface (`class GitCli(Git):`). The class then says what it implements, and Python refuses to construct one that leaves an operation out; before, the six implementations fitted `typing.Protocol` classes by shape only, and nothing at the class checked the fit. `typing.Protocol` is kept for shapes of code the factory does not own, such as a stand-in for a third-party object in a test. Alternatives rejected: keeping the protocols and checking the fit with a mypy-only assignment in a test (the class itself stays silent, and nothing fails at run time); a shared base with default behaviour (an interface has no state and no public member besides its operations).

## Option-like values are refused, not passed after `--end-of-options`

Date: 2026-10-13. `GitCli` refuses a ref, branch, start point, commit or url that is empty or starts with `-`, with `ValueError` from `check_git_argument` before git runs or a kill point is reached. Found by the acceptance of F0001: `push("--force")` ran `git push --porcelain --set-upstream origin --force` and force-pushed over another writer's commit, against "a push is never forced". No ref, branch name or remote url starts with a dash, so the rule costs nothing. Alternative rejected: passing such values after `--end-of-options` (or `--`). `git reset` refuses the marker after `--hard`, `clone` wants `--` instead, and a refused value would come back as a `GitError` or even `"unreachable"` (exit 128) depending on the command; one rule in the domain is simpler to state and to test. The same story sets `LC_ALL=C` on every git command, last, so that the English messages the push outcomes are read from do not depend on the operator's locale.

## A pushed branch is never read as a refspec

Date: 2026-10-13, decided by the human (decision 22 of F0001). `GitCli.push` and `GitCli.delete_remote_branch` call `check_branch_name`, which refuses what `check_git_argument` refuses and also a value that starts with `+` or contains `:` or `*`, with `ValueError` before git runs or a kill point is reached. Found by the second acceptance of F0001: `git push` reads its branch as a refspec, so `push("+main")` force-pushed over a diverged `main`, `push(":keep")` deleted a remote branch and returned `"pushed"`, `push("HEAD:refs/heads/other")` created a branch with no local counterpart, and `delete_remote_branch("+main")` returned `"pushed"` while `main` was still there. A pattern with `*` pushes every matching local branch, or nothing. This breaks "a push is never forced". It refuses `+main`, a name `git check-ref-format --branch` accepts; the factory's names never take that form, and a plus inside a name (`a+b`) is still pushed. The local operations keep `check_git_argument`, since git reads no refspec there. Alternative rejected: pushing the explicit refspec `refs/heads/<b>:refs/heads/<b>`, which cannot force but turns `:keep` into a `GitError` and leaves the `delete_remote_branch` case to a separate rule; one refusal in the domain stays one rule to state and test, like the argument rule.

## A pushed branch is named as a branch, `refs/heads/<branch>`

Date: 2026-10-13, decided by the human (decision 23 of F0001), after decision 22 above. The third acceptance found that git still read other values in `branch` as something else. `delete_remote_branch("v1")` deleted a tag `v1`; `push("^main")` (a negative refspec) pushed nothing, `push("@")` and `push("HEAD")` pushed the checked-out branch under its own name and `push("v1")` pushed a local tag, all returning `"pushed"` with no `origin/<branch>` afterwards. So `check_branch_name` also refuses `HEAD`, `@` and whatever `git check-ref-format --branch` refuses, and both operations name `refs/heads/<branch>`, the source only. Rejected: refusing names alone (a tag sharing a branch's name would still be deleted), and documenting the edges. This is not the explicit refspec decision 22 rejected: only the source is qualified, there is no `:<dst>`, and `:keep` stays a `ValueError`.

## An acceptance sorts last through a sort key, not through the alphabet

Date: 2026-10-13. Plain string order of work item ids is the human's only priority, but it puts `F0002-A0001` before `F0002-S0001` (`A` < `S`), and an acceptance must come after every story of its feature (F0009 relies on it). `work_item_order` returns `(feature id, 0 or 1, id)`, and callers sort with it as the key. The rule is a property of the ordering, not of the alphabet: the letters `S` and `A` cannot be changed to make it so, because they are the glossary's and are in every existing file name. Alternatives rejected: renaming the acceptance letter to one that sorts last (breaks the spelling of existing ids, and the order would then depend on a letter); sorting by the file name (the slug is free text and could reorder stories or an acceptance); a special case in each caller (the rule would be repeated and one place would forget it). `BRANCH_PREFIX` is defined in `identifiers` and re-exported by `paths`, because `branch_name` needs it there and `folder_of` in `paths` needs the parsers in `identifiers`; the other way round is an import cycle.

## A heading inside a code fence is not a heading

Date: 2026-10-13 (SI1.3). `factory.domain.sections` finds headings, the title and the ends of fenced blocks outside code fences only, so a line such as `## start the server` in a fenced block never splits a section, and a `# comment` in one is never the title. v1 did not do this: its form check took any line starting with `## ` as a heading, which was a listed limit of that check. The fence rules are in one function, `code_blocks`, and headings are found by filtering lines by block index, so the story form check and the journal read the same rules; a section's text keeps the fenced block whole. Alternative rejected: a single scanner that tracks fence state while it looks for headings (the fence rules would be repeated for the title, the sections and the form check). A block that is never closed hides everything after it, which is the safer reading of a half-written story.

## The journal's speaker and kind are data in the front matter, not read from the text

Date: 2026-10-13 (SI1.1). Each journal entry has a record `{number, speaker, kind}` in the front matter's `journal` list, and its visible text in the body under `## Journal`. v1 read the speaker and kind back out of the entry's text, so changing how a speaker is shown (a display name, a label) changed what the code believed, and an agent could forge an attribution by typing it. Now `append_entry` is the one writer of both halves, `last_record` reads only the data, and `entry_text` returns text for display and reads neither speaker nor kind. Because the data is separate, the factory can also undo an agent's tampering exactly: `restore_state_and_journal` puts back the baseline's whole state and `Journal` section and keeps every other edit. Alternatives rejected: parsing the text with a stricter pattern (display and meaning stay tied, and the pattern becomes a format to keep forever); keeping the data only in the text with a checksum (the forgery is detected, not prevented, and every reader still parses). `factory.domain.journal` imports `factory.domain.work_item` only under `TYPE_CHECKING`, because `work_item` needs `JournalRecord`; the module builds documents with `model_copy`, so neither module has to be imported first. Later, journal records gained a time, a stage and a run: see "Journal records say when, in which stage and from which run; cost records on which instance".

## The story form check makes four findings that v1 did not

Date: 2026-10-13 (SI1.1, SI1.3). v1's form check took any `## ` line as a heading. `factory.domain.story_form` takes the sections from the project's story form and reads them through `factory.domain.sections`, so code blocks are respected. Four findings are new because the work item has data: a backlog story that carries front matter (the human's file has none), a backlog story whose `Journal` already has entries (the opening writes entry 1, so a second entry 1 would follow), a story in progress or done without a state, and a journal whose data and text differ in the number of entries (SI1.1 keeps both halves in step). The folder is an argument, so a caller that holds only a started story's specification on `main` names `backlog` and is not asked for a state. Alternative rejected: reading the journal's entries from the data alone; the text is what the human reads, and the check exists to find the two out of step.

## A cost is a string in the cost record file

Date: 2026-10-13 (F0002-S0007). `cost_usd` is a `Decimal` in the record and a JSON string (`"0.3450"`) in the file, and a JSON number is refused as `invalid cost_usd`. A JSON number is read as a float by most tools, so a cost written as `0.345` could come back as `0.34500000000000003`, and a bill summed from such values would drift; a string keeps every digit the runtime reported. The file is also strict JSON: `NaN` and `Infinity` are `not valid JSON`, and a duration is finite, so `render` never writes a line another reader would refuse. Alternatives rejected: a JSON number (the rounding above); an integer count of micro-dollars (it fixes the digits the runtime may report and invents a unit). An unknown measure is `null`, never 0, as for the agent runtime (R24).

## A journal entry closes the code block its text leaves open

Date: 2026-10-13 (F0002-S0009). The journal counts an entry up to the next number at column 0, but the form check counts numbered lines outside code blocks only. An agent's result that quotes a tail of output may open a fence and never close it; then the check saw fewer entries than the data, reported a valid work item as damaged, and the open fence also hid every section after the journal. `render_entry`, the one place that writes entries, now adds a closing line (the indent and the opening run, without the info string) when the rendered lines leave a block open. It reads the lines as they will stand in the body, so the closing line comes from the same `code_blocks` rule as the form check; the numbered first line opens no block. `NewEntry.text` and the journal records stay as given. Alternatives rejected: `NewEntry` refusing such a text (every caller, in F0005 the agent runner, would repair an agent's output); the form check counting entries inside code blocks (the hidden sections stay hidden, and the human decided that entries are counted only outside code blocks).

## A damaged health file reads as healthy, and the file is replaced atomically

Date: 2026-10-13 (F0003-S0001). `JsonHealthStatusFile.read` returns an empty `HealthStatus` for a file that is missing, unreadable, not UTF-8, not JSON or not a valid status. Every stop is raised again while its fault lasts, so a lost or hand-edited file costs one cycle at most and never stops the factory from reporting; refusing to start on a damaged file would add a second stop for the sake of the first. `write` stores the JSON in a temporary file in the same directory and moves it over the target with `os.replace`, so the health check, which reads at any time, sees the old file or the new one and never half a file; a failed write removes its temporary file. Alternatives rejected: writing the target in place (a reader can see half a file); raising on a damaged file (see above).

## Both destinations of a stop are tried, and one failing never loses the stop

Date: 2026-10-13 (F0003-S0002). `StopService.raise_stop` writes the log line and the health status each in its own `try`, so a log file that cannot be written does not keep the stop out of the health status, and a health file that cannot be written does not keep the line out of the log. The first `OSError` is raised after both were tried, the log's when both fail, so the caller still learns of the fault. The two places serve different readers (the operator reads the log, the container's health check reads the status), and a stop that reached neither is invisible. `clear_stop` is ordered the other way: the status first, then the line, so no line says a stop is cleared while it is still in force; a failed health write stops there. Alternatives rejected: stopping at the first failure (the other destination loses the stop); swallowing the error (a machine that cannot write its state would look fine); also posting the stop to a pull request (a stop of the repository or the machine belongs to no work item).

## A stop of a work item is a keyed post, and its branch is checked before the pull request is opened

Date: 2026-10-13 (F0003-S0003). `StopService.post` puts a work item's stop on its pull request as a keyed post and does nothing of its own to avoid a repeat: the hosting service's keyed `post_comment` turns the same key into a no-op. So the order of the post and the write of the pull request number into the state does not matter. A kill after the post and before the write, or a failed post after the pull request was opened, is repaired by posting again: `find_open_pull_request` finds the pull request, the key finds the comment, and there is one of each. Before it creates a pull request, `post` checks the remote-tracking refs the last fetch left: `origin/<branch>` must exist and must not be an ancestor of `origin/main`. The real hosting service refuses a pull request without a commit beyond `main`, and the fake must not be kinder than production, so both fail the same way (`HostingServiceError("create_pull_request", ...)`). The check reads refs only; `post` makes no git write and writes no state (R22). When the stop already carries a pull request number, nothing is looked up, whatever state that pull request is in. Alternatives rejected: listing the comments first to find an earlier post (duplicates what the key guarantees and adds a call that can fail); writing the number from inside the service (the state belongs to the caller); creating the pull request without the check (the fake would accept what production refuses).

## The pipeline definition schema forbids unknown keys

Date: 2026-10-13 (F0003-S0004). Every model of the pipeline definition (`PipelineDefinition`, `StageDefinition`, `RoleDefinition`, `ProjectCommandDefinition`) is frozen and refuses a key it does not define, at every level. A misspelt optional key (`lease_minutes`, `attempts_capp`) would otherwise be dropped and the default would apply without a word, so the project would run on a setting it never chose. The refusal names the path (`unknown key: roles.coder.lanes`) and `all_faults` reports it first. Alternatives rejected: ignoring unknown keys, as the work item reader does for the keys of a backlog story (that file is the human's free text, while this one is configuration); warning and going on (the factory has no channel for a warning short of a stop).

## Agent files: the four keys are applied, every other key is refused at load

Date: 2026-10-16 (F0010-S0011, FEATURE.md decision 28; replaces F0003-S0005's "not interpreted until F0010"). In print mode Claude Code ignores an agent file, so the runner builds its flags and its prompt from `model`, `tools`, `effort` and `budget_usd` itself (`APPLIED_AGENT_KEYS`). Any other key reads as if it did something and does nothing; v1's agent files carried such keys (`name`, `description`, `permissionMode`, `hooks`, `background`, `skills`). So `FrontmatterAgentDefinitionReader` refuses a file with another key, compared as written, naming the first one in the file's order, and it does so before it validates the applied keys. `PipelineLoader` reads every role's file when it loads the definition and raises the stop `agent_definition_invalid` at `origin/main`, clearing it on a good load; the tick ends and `factory-watch` reports the refusal without a stop. Alternatives rejected: ignoring the key (the dead-key problem again), a warning (the factory has no channel for one short of a stop), refusing in the runner only at the stage (the fault would show late, on a started story). The reported `key` of a validation fault comes from `first_error`, the same error `first_fault` formats, so the key and the fault never name different problems.

## The stop `pipeline_definition_invalid` belongs to the definition on `origin/main`

Date: 2026-10-13 (F0003-S0006). `PipelineLoader.load` raises the stop on a refusal and clears it on a success only when the ref is `origin/main`. A load at another ref (the human's look at a branch, a stage-start commit) raises the same `PipelineDefinitionInvalid` but touches neither the health status nor the log. The health status says whether the factory can run, and the factory runs on `main`; a refused branch would otherwise raise a stop that the next load of `main` clears at once, or clear one that `main` still earns. Only the loader raises and clears the stop, so there is one rule for both. Agents are checked only when the text is valid, so the stop names one cause. Alternatives rejected: a stop for every ref (the status would follow whoever looked last); each caller raising the stop (the ref rule would be repeated and could be missed).

## The rules of the pipeline definition refuse at load, and the faults of one text are reported together

Date: 2026-10-13 (F0003-S0007). The rules that look across keys (contract major, `next` names, write paths, reserved names, command names, `time_limit`s against `lease_duration`, the acceptance stage) are one after-validator of `PipelineDefinition`, so a definition that is well formed but cannot work is refused when it loads and becomes the stop `pipeline_definition_invalid`, not a failure when a stage first reaches the fault. The validator collects every fault and raises once, so the operator fixes a text in one pass instead of one fault per cycle. It runs only when every field is valid (pydantic skips an after-validator otherwise), so field faults come first and alone. Alternatives rejected: checking at the stage that uses the value (the fault surfaces mid-run, possibly on a lease already lost); stopping at the first fault (one cycle and one stop per fault).

## The push is the claim, and a rejected push leaves the local commit to the next tick

Date: 2026-10-14 (F0004-S0001). `ClaimService.claim` writes the claim and a "started" journal entry, commits them as the stage-start commit and pushes it; the push is the claim (R19, R20). Two instances that try the same stage race on the remote's branch: git accepts one push and rejects the other, so no lock, lease file or extra service is needed, and the result is visible to everyone from what is on the remote. A push that is rejected or cannot reach the remote raises `PushFailed` and the caller starts no agent run, because an instance that did not win must not work on the stage.

After a failed push the local commit stays on the local branch. `claim` does not reset it: a reset is a second writer of the checkout that could itself fail, and the next tick's restore (F0006) already returns every local branch to what the remote holds. The remote is unchanged, so the state of the work item is not affected by the leftover commit. The lease is copied from the definition the caller gave the service, not read again, so the claim and the commit hold one reading of it.

## The pipeline definition validates in strict mode

Date: 2026-10-14 (F0003-S0008). The four models of the pipeline definition validate in pydantic's strict mode, and a write path must hold a non-whitespace character. A value is taken only in the type YAML gives it: `time_limit: true`, `'30'` and `30.0` are refused, as are `approval: 'yes'`, `'off'`, `1` and `0`. Lax mode turned these into settings without a word (`true` became 1 minute), the same harm decision "The pipeline definition schema forbids unknown keys" refuses: the factory would run on a setting the project did not choose. Each refusal is the usual field fault, `invalid <path>: <message>`, and at load the stop `pipeline_definition_invalid`. Alternative rejected: lax mode with a warning (nothing would show the warning to the operator).

## A stage other than done must be able to move

Date: 2026-10-14 (F0003-S0009). The validator of the pipeline definition refuses a stage other than `done` with an empty `next` (rule 10), and one with neither a role nor `approval: true` (rule 11). A work item entering either would sit there with no stop to say why: the agent's forward outcome or the human's approval has nowhere to go, or nobody works or decides there. No kind of stage in the schema lets the factory work without an agent (`factory` is a reserved name, not a stage kind), so neither shape is meant; a later story that needs one adds it and relaxes rule 11 deliberately. Both rules run only when a stage named `done` exists: without it the fault `stages must hold a stage named done` is the one that matters, and it stays the only one. Alternative rejected: applying the rules always, which adds two faults for a definition without `done`.

## Expiry compares the recorded start time with the checking instance's own clock

Date: 2026-10-14 (F0004-S0002). A claim expires when the checking instance's clock minus the claim's recorded `started_at` reaches the claim's own `lease_duration`. There is no heartbeat, server time or shared clock service: the claim is one commit, and the lease is a number in it. The price is that instances need a synchronised clock (stated in the operator guide); skew shortens or lengthens a lease by the skew, and a `now` before the start is never expired. The claim's own `lease_duration` is used, not the definition's, so a later change of the definition never shortens a running claim (R21). An instance's own claim is recognised whatever its age (R20), so a restart under the same name reruns at once. `ClaimService` is the only module that judges claims, which two source-search tests enforce. Alternatives rejected: reading the lease from the current definition (a definition change would end running claims); judging expiry by the push time on the remote (needs a hosting-service call and gives no better precision).

## The protected paths are fixed, and the write paths are read at the stage-start commit by a direct parse

Date: 2026-10-14 (F0004-S0003). The protected paths (the project's Claude Code directory, `CLAUDE.md`, the make file, the manifest and lock file, the pipeline definition, the two forms and every `feature.md`) are a fixed list in the engine, outside every write path; a project cannot change them in v1.1, so no pipeline definition can open the files that define the pipeline. The write paths are read from `factory/pipeline.yml` at the stage-start commit (R32), never from the work tree, so an agent that rewrites the definition widens nothing and an invalid rewrite breaks nothing. `WritePathService` parses the definition directly with `pipeline_reader`; `PipelineLoader` stays the one place that loads it for the tick, with the agent-file check and the stop. Reading at a commit is a read for another purpose: the undo must not fail on an agent file removed since the load, and a read of a branch must not change the health status. Alternatives rejected: a project-declared protected list (a mistake there would unprotect the pipeline); going through the loader at a commit (it would repeat the agent-file check and blur the one-loader rule).

## The guard reads only the settings file taken at the stage-start commit, and reads the payload as v1 does

Date: 2026-10-14 (F0004-S0004). `factory-guard` reads one file, the `GuardSettings` the runtime wrote from `WritePathService.at` at the stage-start commit, and no pipeline definition, so an agent that rewrites `factory/pipeline.yml` in the work tree changes no verdict (R32). The verdict is the domain's `refusal`, applied to the real path of the file, so the guard and the undo share one rule. A payload the guard cannot read (not JSON, no `tool_input`, no or an empty `file_path`) is allowed: it fails open, as v1 does, because there is no path to judge and a refusal would block tools that write nothing; the handover leaves a stricter reading for v2. A settings file the guard cannot read refuses with status 2, since the guard then has no rules. Alternatives rejected: reading the definition from the work tree (the agent could widen its own paths); failing closed on unreadable payloads (blocks tools without paths, a change of behaviour not asked for); argparse (it exits by itself with its own usage text, against "status 2, never an exception").
- Superseded in part by "The Claude Code hook is removed; the kernel and the undo are the write guard": the hook `factory-guard` this entry describes is removed.
- The guard went with the hook, F0044-S0009 removed its last user, the undo; the take keeps the rule that the write paths are read at the stage-start commit.

## The undo reads the write paths at the stage-start commit, and a work item the agent breaks is restored whole

Date: 2026-10-14 (F0004-S0005). The undo takes its write paths from `WritePathService.at`, that is from the pipeline definition at the stage-start commit, the source the guard uses (WE2), so an agent that rewrites the definition widens nothing and an invalid rewrite does not make the undo raise. It also undoes, whatever the write paths say, every other file directly in an `in-progress` folder of a feature (other work items, cost records, notes); the test is on the path string, because `folder_of` knows only work items. The own work item's state and journal are restored from the stage-start commit while the agent's edits to its sections stay; a work item the agent deleted or left unreadable has no sections worth keeping and is checked out whole. The baseline is read before any path changes, so a missing or unreadable baseline raises with the work tree as the agent left it. Alternatives rejected: reverting the whole work item file (loses the agent's legitimate section edits); repairing a broken file in place (guesses at what the agent meant); making a commit (the commit and the entry are F0005's).
- The take keeps this rule; the undo went with v1.2 F0044-S0009.

## The prompt, the request and the validation share one list of decisions

Date: 2026-10-14 (F0005-S0001). `allowed_decisions(stage.next)` is computed once per task and its result is used three times: the prompt's `Allowed decisions:` line, `AgentRunRequest.allowed_decisions` (from which the runtime builds its outcome schema) and, in the stage protocol, the check of the agent's decision. Three copies could drift, and the agent would be told one thing and held to another. `question` is last and always present, so every stage can ask the human; `stuck` of v1 is not a decision, because an agent that cannot finish asks. The Mode line is decided from the speaker of the last `result` record, not from entry text (text is free-form and a copied comment could forge it) and not from the last record (a stall or comment would hide the test change). The story form is read at `origin/main` so an agent cannot weaken the check it is held to. Alternatives rejected: each part deriving its own list; reading `coder:` in the entry text; reading the form from the work tree.

## The local branch is reset to the remote's, and the recorded pull request is checked first

Date: 2026-10-14 (F0005-S0002). When a work item has a branch, `WorkItemOpening.prepare` checks it out with `start_point="origin/<branch>"`, which resets the local branch to the remote's whatever it held, and then merges `origin/main` (R18). The remote is the truth (kept thing 3), so v1's fast-forward stall, which arose when a local branch had diverged, does not exist. A merge conflict is aborted and reported, not resolved. For the pull request, the number recorded in the state is read with `get_pull_request` before the branch lookup, because a branch can hold several open pull requests and `find_open_pull_request` alone could return the wrong one. Alternatives rejected: fast-forwarding the local branch (stalls on a divergent one); relying on the branch lookup alone.

## The pull request number travels with the stage's next commit, and no local run record is kept

Date: 2026-10-14 (F0005-S0003). `StageLauncher.launch` pushes the claim before it ensures the pull request, so the stage-start commit cannot hold the number of a pull request that does not exist yet; it carries `None` for a new work item and the recorded number otherwise, and the stage's next commit records the number found or created. A stage start also writes no local run record: the claim's `started_at` on the remote is the only start the board and the recovery read, so there is no second copy to disagree with the remote (kept thing 3). A boundary error after the claim leaves the claim pushed; F0008 handles it as a crash. Alternatives rejected: creating the pull request first (a lost claim would leave a draft for an instance that does not work); a local run record (a second source of the start time).

## The sidecar is rewritten from memory after every undo, and a crashed stage's records are discarded with it

Date: 2026-10-14 (F0005-S0008). A cost record is created when the agent run starts and completed when it ends (R24), but it is not pushed on its own: it travels in the stage's next commit, the result commit or the stall commit. The sidecar lies outside every write path, so the undo reverts or deletes it; the records are therefore kept in memory in a `CostRun` and written to the sidecar again after every undo, in `AfterAgent.process` and in `StallService.stall`. What the agent did to the file changes nothing. Records of a stage that crashes before any commit are discarded with the stage (F0008), so no run is counted that left no commit. A reported zero stays zero and an unreported measure stays `None`, never estimated. Alternatives rejected: pushing the started record before the run (a second commit per stage, and a crash would leave a record without a result); reading the sidecar back from the work tree after the undo (the agent could have changed it); keeping a separate local cost file (a second copy beside the commit). While an agent runs, it therefore sees the sidecar modified, holding the running run's `started` record, and that stays so, because the alternative, pushing the started record before the run, is the one rejected above (first noticed by an agent on 2026-10-18).
- The take keeps this rule; the undo went with v1.2 F0044-S0009.

## A branch that is an ancestor of `origin/main` is still read

Date: 2026-10-14 (F0006-S0001). `RemoteWorkItems.read` reads a story's state from `origin/work-item/<id>` whenever the branch exists, also when its tip is an ancestor of `origin/main`. After the human merges with a merge commit, the story file may still be in `in-progress/`; the branch tip holds its latest state, while the file on `main` is the specification the human moved. Treating a merged branch as absent would read the story as a new start and run it again from the first stage (kept thing 2: a story starts only by the human's move). A story without a branch is read as a new start, so the hosting setting that deletes branches on merge must be off (operator guide). Alternatives rejected: an ancestry check that ignores merged branches (restarts a finished story); reading the file on `main` (it carries no state).

## A stall note fences multi-line output, and the stall writes the stage label

Date: 2026-10-14 (F0005-S0010). GitHub renders a comment as Markdown, so the output of a red check posted inline lost `<module>` and turned `__init__` bold, and the follow-up sentence stuck to make's error line. `stall_note` puts the detail's first line in the sentence and the remaining lines in a `text` fence one backtick longer than the longest backtick run of three or more in them, so the output can never close its own block. The journal's stall entry keeps the tail as continuation lines. A stall also writes `labels_for(<the stalled state>)` after the note, because only the result commit wrote the label and a work item whose first stage stalls had a draft pull request without one; the label is written for `already_posted` too and is never read back. Alternatives rejected: labelling when the draft is created (misses a pull request the stall itself had to create); escaping the output character by character (fragile, and the text is no longer the output); an indented code block (cannot carry a language and breaks on lines that start like a list).

## Errors are counted per event and remote state, and the report is keyed

Date: 2026-10-14 (F0006-S0003). The dispatcher counts a handler's errors per event key and remote state (`ErrorCount`), and at three it posts one report and does not try that event on that state again. The remote state is in the count because a push to the work item's branch is what could cure the fault: it starts the count again at 1 (GH5.4), while a count per event alone would silence an event for ever and a count per tick would retry a hopeless one for ever. Another state for the same key replaces the key's entries, so the status does not grow. The report's key is `PostKey(work_item, "error", remote_state[:12])`, not the event's: a restart empties the counts, which are only a local cache, and the next three failures then find the report already on the pull request and post nothing; two events of one work item on one state share the key and so the one report. A report that fails to post leaves the entry unreported and uncounted and is made again on the next dispatch, without calling the handler. Alternatives rejected: persisting the counts (a second copy beside the remote, kept thing 3); a key per event (one comment for each failing event of a work item); retrying with a delay (the cause is mostly in the branch, and the human is told).

## The report of a work item without a branch on the remote is a log line

Date: 2026-10-14 (F0006-S0003). `StopService` opens a draft pull request only for a branch on the remote with a commit beyond `main`. When the report fails with a `HostingServiceError` and the snapshot's `branch_commit` is `None`, no later tick could change that, and retrying would make the report fail for ever and the event never reach `capped`. The report then becomes the line `error cap reached on <event>: <last error>` in the factory log and the entry is marked reported, which is also the report of an event with no work item. Any other failure of the report is retried. Alternatives rejected: retrying for ever (a hopeless report on every tick); dropping the report silently (the operator would not learn of the cap).

## The checkout is disposable and restored to `origin/main` at the start of every tick

Date: 2026-10-14 (F0006-S0004). The tick fetches, loads the definition, and then resets the checkout to `main` at `origin/main`: uncommitted changes and untracked files are removed (one log line names them), and the local branches of the work items are deleted. The remote is the only truth, so a local commit that a rejected push left behind, a half-finished stage or a stray file must not decide anything. Rejected: repairing local state case by case (a second writer of the checkout that could itself fail), and keeping a local record of what the last tick did (a second truth that a fresh clone lacks). A restore that fails is the repository stop `checkout_restore_failed`; the load of the definition comes before the restore, so an invalid definition leaves the checkout alone.

The seal, the re-clone and the removal of ignored paths went with v1.2 F0044-S0006; the restore stays.

## A stale branch is deleted by the tick, not by the discard handler

Date: 2026-10-14 (F0008-S0004). A kill between the push of a discard's move to `backlog/` and the deletion of the branch leaves `work-item/<id>` on the remote, and no event is raised again for a story in `backlog/`, so the closed handler never runs for it. The same holds for a merged story whose branch outlives the archive in `done/`. The tick therefore deletes the branch of any story found in `backlog/` or `done/` on `origin/main`, after the restore and before the evaluation, so that the human need not delete it and a story started again does not find the old state and bill (F0007 decision 21). Rejected: retrying in the handler (it is never called again after the kill), and a hosting-service lookup (the remote's branches and `origin/main` are enough, and the hosting service stays out). An id that also has a file in `in-progress/` keeps its branch, because that is the `duplicate` case. A refused deletion is a log line, not a stop: the tick would otherwise stop all work for a refusal that only concerns a leftover.

## A capped event holds back all new work

Date: 2026-10-14 (F0006-S0004). The evaluation keeps no memory, so a work item whose `run` event the dispatcher has capped is still the first runnable one on every later tick, and the tick dispatches it as `capped` instead of starting the next work item. This is the same rule as for a waiting work item: while the first work item needs a human (here, a push to its branch), no new work starts. Rejected: skipping a capped event to run the next work item, which would let work pile up behind a failure nobody has seen.

## The handlers are built from the loaded definition on every tick, and a constant lists the kinds still unhandled

Date: 2026-10-14 (F0006-S0007). The handlers take the pipeline definition, and the definition can change on `main` between ticks. The tick therefore receives a handler factory (`handler_factory`) and builds its handlers after each load, so a stage never runs under a stale definition. Rejected: handlers built once at start (a changed definition would need a restart, and the old one would run until then), and handlers that load the definition themselves (a second reader of `main`, which could disagree with the tick's).

`NOT_YET_HANDLED` is a constant in `factory.entry.wiring`, not a list a test derives. A test that computed the unhandled kinds from `build_handlers` would pass whatever the wiring did, and a new event kind would go unnoticed. With the constant, a test compares it with `unhandled_kinds(build_handlers(...))`, so a new kind without a handler, or a handler registered without shrinking the constant, fails a test. An unhandled kind stays a counted error (`UnhandledEvent`), never silence.

Date: 2026-10-21 (F0039-S0005). The constant was removed once every kind had a handler: the comparison of the handlers' keys with every `EventKind` (`test_every_kind_has_a_handler_and_acceptance_due_opens_the_acceptance`) catches a new kind without one, so the constant no longer added a check.

## The close at the approval is recorded before the pull request is reopened

Date: 2026-10-14 (F0007-S0005). The closed handler pushes the human's close (their unread comments, a `close` entry, `handed_over` cleared) first, then reopens the pull request as a draft, then pushes the decision. The close is the human's act, and the work item is the truth (R1): if the reopen fails or the factory dies after it, the close is already recorded, and the retry finishes the send-back without a second `close` entry (a `close` numbered after the latest `result` counts as recorded). The comments travel in the same commit as the close (`CommentCopier.append`, not `copy`, which pushes alone and records nothing when there are no comments), so a kill cannot leave comments recorded without the close. Rejected: reopening first (a failed record would leave an open draft and no trace of the close), and one commit for close and decision (the reopen sits between them and may fail). Whether the reason was given is read from the journal's records, never from the comment's text.

## Every event goes through the error cap, comment events included

Date: 2026-10-14 (F0007-S0007). `CommentHandler` catches nothing: a failing `list_comments`, a failing push or a work item without a pull request leaves `handle` by raising, and the dispatcher counts it per event and remote state, tries it up to `ERROR_CAP` (3) times and reports it once (F0006-S0003). A comment is the human's answer, so a handler that swallowed its failure would leave a question unanswered with nobody told; the cap makes it one of the four ways a work item does not move forward, with a report the human can read. The bound is proved for `comment` and for `ask` through the dispatcher, including that a restart does not report twice. Rejected: a retry loop inside the handler (a second counter beside the dispatcher's) and recording the failure and carrying on (the wait would end, or stay, without the human seeing why). The wait ends only from data: the post's key and ids, so a comment written before the question was posted, while the stages worked, cannot answer a question the human has not seen.

## A crash is charged only to a held claim, and the stage is rerun in the same call

Date: 2026-10-14 (F0008-S0001). The `crash` handler acts only when the claim is this instance's own (`ClaimService.status` is `own`); a claim of another name is `held` or `expired`, belongs to that instance's lease, and is refused with `CannotHandle`. So a crash is never charged to a stage another live instance may still be running. The handler discards the dead stage's work back to the remote's head (`WorkItemRecorder.check_out`), records the crash in one commit (claim cleared, `crashes` + 1, `attempts` unchanged, a `crash` entry), pushes it and calls the `run` handler in the same `handle` call, so the stage restarts at the first look, with no wait for the lease or an idle pause. The rerun is the `RunGate` registered for `run`, so it reads the pull request first. Rejected: committing the leftovers with `git add -A` (v1: it kept a killed run's half-written files), charging an attempt (v1: a restart is not the stage's failure and would drain `attempts_cap`), and returning after the record to let the next tick rerun (an idle pause and a second look for nothing; the record is on the remote already, so a failing rerun does not lose the crash). Nothing is posted: an own crash is the factory's business, and the human sees it in the journal.

## The crash cap keeps its counter across rework and stalls, and a lost question without a pull request is not posted again

Date: 2026-10-14 (F0008-S0002). `crashes` is reset only by a forward move and by the human's answer to the crash-cap question; a rework move and a stall keep it, so the cap counts the crashes since the last forward move and a story that crashes, is sent back and crashes again still reaches it. At the cap the crash and the question are recorded in one commit and pushed before the question is posted, so a kill never leaves a crash with no question or a question with no crash; the post is keyed `crash_cap` with the question's journal number, the same body and key the `ask` handler uses, so a repeat is a no-op. A boundary error after a pushed claim is a crash on the next tick, so an error that repeats ends at this question and not in the dispatcher's error report. Rejected: resetting on every rework move (a story that keeps crashing would never ask). Known gap: when the question is recorded but the post is lost and the work item has no pull request, the `ask` handler cannot post it, and it is not posted again; the report of a question with no pull request is the visible result.

## An expiry is a crash of a gone holder: it costs no attempt, and its note says "retrying" only when a rerun follows

Date: 2026-10-14 (F0008-S0003). When the lease of another instance's claim has run out, `RecoveryHandler` handles `expired` like `crash`: the same discard, the same single commit (claim cleared, `crashes` + 1, `attempts` unchanged) with an `expiry` entry, and the same crash cap. The holder is gone, so what it did is lost exactly as in a restart, and charging an attempt would drain `attempts_cap` for a failure that is not the stage's. One handler instance serves both kinds (`build_handlers` registers it twice) instead of an `ExpiryHandler`, because everything but the guard, the entry and the note is shared. Unlike an own crash, an expiry posts a note after the push, because the human has not seen a restart and cannot otherwise tell that another instance's run was abandoned; a note whose post fails is not posted again. The note says "retrying" only below the cap (`expiry_note`, and `stall_note` likewise), and a test searches the source so no other string says it. This replaces v1, which charged an attempt and posted "Retrying." even when the next tick asked the human. Lease expiry compares clocks across instances, so instances need synchronised clocks (see the decision on expiry).

## Each acceptance has its own report and its own cost records

Date: 2026-10-15 (F0009-S0005). An acceptance is a work item with its own id (`F0001-A0001`, then `A0002`), its own report and its own cost records sidecar, and the merge books its `done` entry from `bill(<those records>)` read at `HEAD`, not through `BillService`. A feature accepted twice, or refused and accepted later, therefore shows what each acceptance cost and nothing of the other, and a refusal's cost is not lost when the next acceptance runs (kept thing 20). The result is the human's act: `book_merge` sets `accepted` and `book_refusal` sets `refused` whatever the recommendation says (kept thing 19), and the human's text is copied into the report, never interpreted. `AcceptanceMerged` follows `MergedHandler` step for step (shared `move_with_cost_records`, move before write because `git mv` onto an existing file fails), but unlike it books nothing when the report is already in `done/`, so a rerun after a kill only deletes the branch. Rejected: one report per feature appended to by each acceptance (a refused result and an accepted one could not both stand, and costs would mix), and counting the cost from remote-tracking refs (the same commit, but a second reader of the checkout's truth). A body without a `## Recommendation` or `## Journal` section gets an empty journal after the new recommendation so that the entry has a place; `append_entry` stays strict for every other caller.

## A merge before the approval is booked like any merge, and a repeated acceptance is a new work item

Date: 2026-10-15 (F0009-S0006). A human's merge of an acceptance before its approval stage is booked `accepted` like every merge (the merge is the human's decision), with the entry `done (pull request merged before approval); cost: ...`. `AcceptanceMerged` asks `is_before_approval(definition, stage)` of the report's stage on `main` and passes the result to `book_merge`; the domain booking takes a flag because it has no definition. v1 alternated forever between `merged` and `reject` here, because its report kept one file whose stage had to change. Here the report moves to `done/` as a new file, so no stage change is judged, and the proposed stories the merge brought make the feature `incomplete`, not due. A repeated acceptance needs no rule of its own for the same reason: each acceptance is a work item (`next_acceptance_id`) with its own report and cost records, and `acceptance_status` compares the archived stories with the recorded reports, so the earlier report is never rewritten and a recorded repeat ends the due state. Rejected: a second booking function for the early merge (repeats the booking), and judging the stage inside `book_merge` (it would need the definition).

## The run gate holds the acceptance splits, not the story's handlers

Date: 2026-10-15 (F0009-S0010). `build_handlers` builds `closed` and `merged` once, each a `SplitByWorkItemKind` of the story's handler and the acceptance's, and gives those same instances to the `RunGate` and to the keys `closed` and `merged`. A due stage whose pull request the human closed or merged reaches the gate as a `run` event; if the gate held `ClosedHandler` and `MergedHandler` and only the mapping's values were split, an acceptance would go to the story's handlers, which archive it as `done` with no outcome (a state the acceptance reader refuses on every tick after) or move it back to `backlog/`. Rejected: a branch on the work item's kind inside the gate (it would know a second kind of work item, and the split already is that place). The wiring has no branch on `acceptance_stage` either: the acceptance handlers refuse their events themselves when the definition has none.

## One instance runs one project, and the settings can name no second one

Date: 2026-10-16 (F0010-S0001). `InstanceSettings` holds one `repository_url`, and `read_settings` refuses a value with whitespace or a comma (R2). v1's list of repositories (`REPOS`) is gone; a test searches `src/factory` for it. One instance, one project keeps the checkout, the state and the lease of an instance unambiguous; a second project is a second instance. The checkout and the state directory are constants, never read from the environment, so no variable can point an instance at another place (superseded in part by *The checkout and the state directory are settings*, below). A URL with a password is refused too (the human, 2026-10-14): git would keep it in the shared checkout's `.git/config`, which the agent can read, so the token belongs in the token file. A user name alone and the scp form are accepted. Rejected: a list with a separator (v1's shape, which the single-project rule removes) and stripping the password from the URL (it would hide that the operator's setup is wrong).

## The commit identity has a default and no preflight item

Date: 2026-10-16 (F0010-S0001; questionnaire 1, Q18; F0001 decision 10). `GIT_USER_NAME` and `GIT_USER_EMAIL` override `GitIdentity`'s default `factory <factory@noreply.invalid>`, each half on its own, and a blank value counts as unset. No preflight item checks them: the default is a valid identity, so there is nothing to be missing. Rejected: requiring the two variables (every instance would need configuration that has a sensible default) and checking them in the preflight (it could only confirm a value that cannot be wrong). Known duplicate: the default is also spelled in `GitOptions` (`domain/git.py`); settled on 2026-10-17 (F0012-S0003), below.

## The image identity is read from a file the image build generates

Date: 2026-10-16 (F0010-S0001; the human, 2026-10-14). The settings hold the identity of the image the instance runs on, read from `/opt/factory/image-id` (or the file named by `FACTORY_IMAGE_ID_FILE`). A build argument alone would be the same after a rebuild with the same argument and could keep an old preflight stamp valid (ST4.3); a generated file changes with every build. The reader is a parameter of `read_settings`, so `factory.domain` does no I/O, and without a reader the identity is `None`. A missing, unreadable or blank file is refused. `FACTORY_IMAGE` is never the identity. Open: a `FACTORY_IMAGE_ID_FILE` that is set but blank falls back to the default path.

Since v1.2 F0045-S0005 `FACTORY_IMAGE_ID_FILE` is required and absolute; the default `/opt/factory/image-id` and the open point on a blank value went.

## A checkout whose clone was killed half-way is not recognised

Update (F0014-S0006): the factory now removes and clones again a checkout whose `.git` fails the seal check (see "The factory alone writes the checkout's `.git`"); a folder with no `.git` is still refused.

Date: 2026-10-16 (F0010-S0002). `CheckoutPreparer.prepare` clones when `checkout/.git` is missing and does nothing else; it does not check that an existing clone is whole. The checkout is disposable (R18) and a clone killed half-way is rare, so the operator deletes the directory (see "The loop and its pauses" in the operator guide). A directory with files but no `.git` is refused by git itself, as a `GitError` that the scheduler logs and counts as idle. Rejected: probing the clone's health on every iteration (a git call per tick to cover a rare case) and deleting a directory the factory did not clone (it could destroy what the operator put there). `pause_after` doubles step by step to the cap instead of computing `FIRST_PAUSE * 2 ** n`, which overflows `timedelta` after about 43 idle ticks.

Replaced by the dataset's rollback, v1.2 F0044-S0006.

## Git gets its credential helper and shared group through `GitOptions.environment`

Date: 2026-10-16 (F0010-S0003; F0001 decision 7). The git wrapper ignores system and global configuration, so nothing can be set there. `git_environment()` hands the credential helper (the only route by which git reaches the token) and `core.sharedRepository` to git (`group` here, `0640` since F0014-S0006, see "The factory alone writes the checkout's `.git`") as `GIT_CONFIG_COUNT` and `GIT_CONFIG_KEY_n`/`GIT_CONFIG_VALUE_n` entries of `GitOptions.environment`, so they hold for every git call of the wrapper and for no other git. Rejected: writing the checkout's `.git/config` (the agent can read it, and a recloned checkout would lose it) and a global `~/.gitconfig` (git does not read it here). Also rejected: `urllib.parse` for the repository URL; it does not understand `git@host:owner/name`, so it needed a second code path next to the regex.

The shared group went with the second user, v1.2 F0044-S0005; the credential helper and the hooks stay.

## The services read the instance's settings from `Boundaries.settings`

Date: 2026-10-16 (F0010-S0003). `Boundaries` gains `settings`, filled by `build_boundaries`, so a service that needs a setting (the image identity, the agent user) reads it from the object it already holds, and no story adds a parameter or a second route for it. The field was optional, `None` by default, so a `Boundaries` built by hand in a test stayed valid. Rejected: passing `InstanceSettings` to each service next to the boundaries (every wiring site would grow a parameter per story) and reading environment variables in the services (the settings are validated once, in `read_settings`). Open: the default token path of F0010 decision 18 (`/run/secrets/hosting-token`) is not implemented; `token_file` defaults to `None` until a later story adds it.

Date: 2026-10-21 (F0039-S0006; F0039 decision 8). `settings` and the five fields that were optional after it (`disk`, `disk_records`, `stop_records`, `waiter`, `result_records`) became required once `build_boundaries` set them all, because an optional collaborator let a construction drop a stop silently: the suite ran with the low-disk stop, the records and the provider-limit waits switched off, and nothing failed. A test that needs a feature off replaces its collaborator with one of its own.

## One `Tick` serves the whole run, and only a handled event that is not `idle` is activity

Date: 2026-10-16 (F0010-S0004; F0006 decision 11, kept thing 16). `run_instance` builds one `Tick` with `build_tick` and hands the scheduler `activity_tick(tick)`, which calls that same object every iteration. The tick's status (the counts of repeated errors) lives in memory only, so a `Tick` made per iteration would forget it and never reach a cap or a repeat. `activity(outcome)` is true only for `dispatch == "handled"` with an event whose kind is not `idle`. A tick that ended at a standing repository stop, a capped event, an error and a reported event are idle: they repeat on every tick, and counting them as activity would hold the pause at 15 seconds while nothing changes. Rejected: a `Tick` per iteration (loses the status) and counting any dispatch as activity (a standing stop would keep the instance polling at the fastest rate). `main` turns a `SettingsInvalid` into status 2, a log line and a `preflight_failed` machine stop written directly, since no boundaries exist yet; it reuses `HealthStatus.with_stop`, the rule `StopService` uses, instead of a second copy.

## Every tool of the machine's image is pinned, and its identity is generated at build

Date: 2026-10-16 (F0010-S0006; R29; the human, 2026-10-14). The Dockerfile pins the base image by digest, Claude Code and `uv` by exact version, the eight Debian tools by `name=version`, and installs the factory from `uv.lock` with `--frozen`, so two builds of one commit run the same tools and a changed result has a cause in git. `tests/test_image.py` rejects a floating reference. The image's identity is a uuid the build writes to `/opt/factory/image-id`; the build argument `FACTORY_IMAGE` is only a label. A build argument can be passed again unchanged and a rebuild would keep a stale preflight stamp valid (ST4.3); a generated id changes with every build that changes an earlier layer. Rejected: the argument as identity, and a hash of the build context (it ignores the base image and the packages). Every cost record carries the identity (`CostRecorder.begin` takes it from the instance's settings), so a cost can be traced to the image. The digest and the Debian versions are placeholders until the first build with a network.

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## `/state` is read-only for the agent; `/state/runs` is readable by it

Date: 2026-10-16 (F0010-S0006; the human, 2026-10-14). `/state` is `0755` owned by `factory`: the agent can read the health file, the log and the stamp, and cannot rewrite them, so an agent cannot hide a stop or forge the preflight stamp. The files the agent must read for its run go to `/state/runs` (`2750`, group `factory-work`), which the agent can read and not write. Rejected: making `/state` group-writable (the agent could alter the factory's own status) and giving the agent no access (it could not read its run's input).

## The entrypoint sets no git configuration and starts in `/opt/factory`

Date: 2026-10-16 (F0010-S0007; questionnaire 1, Q17, Q18, Q23; F0001 decision 7). The entrypoint runs no `git config`: the factory's git gets the commit identity and the credential helper through `GitOptions` only, so no global file in the container holds them and a token never lands on disk through git. The entrypoint changes into `/opt/factory` before it starts the factory, so that `claude --version` (the preflight's probe) runs in a fixed directory and not in whatever `/work` holds; the Dockerfile's `WORKDIR /work` is only the default for a shell in the container. The waiter fetches only when `origin/main` is not ready, because the tick already fetches and a ready checkout must cost no second fetch.

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## The stamp is keyed to the image build, the probe runs `lint` on `main` only, and a red `main` is remembered

Date: 2026-10-16 (F0010-S0009; ST4.1, ST4.3, ST4.5; kept things 16 and 18). `preflight-stamp.json` holds the image identity the machine's items passed on and the commit of `origin/main` whose `lint` passed or failed. No timer expires it: only a new image build can change what the machine's items find, so a clock would repeat the checks for nothing; a new build also forgets what was probed. The probe runs `lint` on `main` at `origin/main` and never on a work item's branch, because a red branch is that work item's concern and must not stop the machine. It runs only when `origin/main` has moved. A red `main` is remembered by its commit (`main_failed`), so an idle tick runs no project command (kept thing 16) while the human has not yet pushed a fix; if the stop was lost from `health.json`, it is raised again without running `lint`. The probe's `time_limit` is a constant of 10 minutes, the default of every project command, so that `Preflight` needs no pipeline definition and its memory does not depend on one. A probe that cannot run (git or `make` fails) is a machine stop `preflight_failed` and changes no stamp: it says nothing about `main`. Rejected: a time-to-live on the stamp (repeats work, and a stale pass hides nothing a rebuild would not), probing the work item's branch (blames the machine for the work item), and a `time_limit` from the pipeline definition (a broken definition would then hide the stop of the machine). The atomic write both JSON files use is one function, `replace_text` in `factory.adapters.atomic_file`, extracted from the health file. Open: the preflight does not fetch, and a `main_branch_failing` stop stays when the machine's items fail; the tick story decides both.

## The preflight runs after the restore, not before the load

Date: 2026-10-16 (F0010-S0010; F0006 decision 10; ST4.2, kept thing 18). The tick is fetch, load, restore, preflight, clean up, evaluate, dispatch. The preflight must come after the fetch, because it probes `origin/main` and a fix the human pushed must be seen at once; and it must come after the restore, because the probe puts the checkout on `main` and a leftover change would otherwise be probed or lost. It cannot come before the load: F0006 decision 10 has the tick load the definition before it restores the checkout, so that an invalid definition leaves the checkout alone, and the preflight needs the restored checkout. An invalid definition therefore ends the tick before the preflight, and raises no `preflight_failed`. A reason the preflight returns ends the tick with `TickOutcome(stopped=<reason>)` and the tick writes no stop itself, since `Preflight.run` raises and clears its own (a stop the tick wrote would have the wrong scope for `preflight_failed`, which is a machine stop). A stopped tick skips the cleanup too, so a red `main` leaves stale branches on the remote until it is fixed. `build_tick` takes `which` (default `shutil.which`) so a test can answer for the tools; the later machine items join through `build_preflight`'s `extra`. Rejected: running the preflight before the load (it would restore or probe a checkout the definition rule says to leave alone) and a tick that runs the cleanup despite a red `main` (a stopped tick should do nothing else).

## The credential helper reads a file, not the environment

Date: 2026-10-16 (F0010-S0013; R33; WE3.2, WE3.5). Git gets the token from `git-credential-factory`, which reads the file `FACTORY_TOKEN_FILE` names and prints nothing and fails when it cannot. The token is in no environment variable, no `ENV` or `ARG` of the image, no compose `environment` and no git configuration file, so there is no value to inherit: a child process sees the token only if it can read a file that only the factory's user may read. The agent's environment is an allow list of six names applied once at its source (`production_environment`), not a deny list of known token names, so a variable nobody thought of is dropped too. Rejected: the token in the environment of the factory's git (any child that inherits the environment, a hook or a script, would carry it), `credential.helper store` and a `.git-credentials` file (the token on disk in a file the shared group can read), and scrubbing again in `TaskComposer` or `ClaudeCodeRuntime` (a second copy of the rule; F0005 decision 23 keeps the composer a pass-through).

## The project commands first ran as the factory's user; replaced

Replaced by *The project commands run as the agent user, with the git folder sealed*.

Date: 2026-10-16 (F0010-S0013; the human, 2026-10-14). `make check`, `lint`, `test` and the preflight's `lint` run code that agents wrote, as the factory's user, who can read the token file; a test can print the token into the output tail the factory writes into the journal. This is not built now. Running them as a user who cannot read the file, or filtering their output, is work for v2. Until then the operator guide says so, and the second operating-system user of F0010 covers the agent run only.

The user they ran as went in F0044-S0005: a check runs in a container of its own on the rolled-back base, which cannot read the token.

## The agent is started through `sudo -n -u agent -- env -i`, and a run's files are `0640`

Date: 2026-10-16 (F0010-S0014; R32, R33; WE2, WE3.1; the human, 2026-10-14). Every agent runs as the second user `agent`. The runtime calls `sudo -n -u agent -- env -i <NAME=value>... <claude> ...` with an empty environment of its own. `-n` turns a missing rule into an error instead of a prompt. `env -i` is needed because `sudo` keeps or adds variables of its own by policy; with it the agent has exactly the request's environment and the three switches. The composer puts the user in the request (`os_user`), the setting is `FACTORY_AGENT_USER`, and the wiring gives the agent the `HOME` of the agent user. Rejected: `su` or `setpriv` (they need root or add a second tool), and a `sudo` rule that keeps the environment (the factory's variables would come along).

The runtime writes a run's instructions, guard settings and hook settings with mode `0640`, whatever the umask. The agent reads them through the group `factory-work`; it cannot rewrite them, and `/state/runs` is not writable by it, so a run cannot widen its own write paths. A `sudo:` line on standard error is a refusal, an error, only when the call gave no usable reply; before a good reply it is a warning (`unable to resolve host`) and is ignored.

The agent's home stays writable by the agent (L69): its login and `.claude` live there. Closed by *Every agent run and every project command starts from a fresh agent home*. The kill of a timed-out agent under `sudo` was settled later: see *The agent's own `timeout` kills a run under `sudo` at its time limit*.

Replaced by the throwaway container, v1.2 F0044-S0005.

## The factory's user may become `agent` for one command only, and a missing agent user is a stop

Date: 2026-10-16 (F0010-S0015; R33; WE3.1; the human, 2026-10-14). One `sudo` rule in a file of its own lets `factory` run commands as `agent` and nothing else: no `root`, no `ALL=(ALL`, no right for `agent`. A wider rule would turn the second user into a way to the first.

The sudoers file sets the umask and no pseudo-terminal because `sudo`'s defaults break two things. Its own umask (`0022` joined with the caller's) makes agent-made files `644` and directories `755`, so the factory's `git clean -fd` cannot remove an agent-made directory (`checkout_restore_failed`); `umask=0002` with `umask_override` keeps them group-writable, and the entrypoint's `umask 002` makes the factory's files the same. Debian's `use_pty` would put the command in a new session; `!use_pty` leaves it in the factory's.

The entrypoint's `umask 002` is also what `uv` syncs `.venv` under; see *The tests set their own umask, and uv syncs under the caller's*.

A missing agent user beside an existing token file is a stop (preflight item `agent-user`), decided by the human on 2026-10-14. Without it every agent would run as `factory`, who can read the token file, and no check would say so: WE3.1 and R33 would be silently off. With no token file (tests, local runs) there is nothing to protect and the item passes. Rejected: folding the check into `token-file`; the two answer different questions.

Replaced by the throwaway container, v1.2 F0044-S0005.

## The preflight runs the factory's own arguments once for each image build, and finds a refused `sudo` before any claim

Date: 2026-10-16 (F0010-S0016; questionnaire 1, Q22; F0001 decisions 17 and 18; WE3.1). The preflight's item `agent-run-probe` makes one `claude -p` call exactly as a stage does (the agent `coder`, a guard, the agent user, the agent run's environment), with a budget of 0.10 dollar, the decision `question` only and a time limit of 2 minutes. A flag the pinned `claude` rejects would otherwise end every real run `died` with no text that says why, and F0001 left that probe to a morning observation. It is a machine item, so the stamp skips it while the image is unchanged: it costs a few cents once for each image build. The item `agent-environment` checks the other half of F0001 decision 17: Claude Code treats a hook that cannot start as not blocking, so a `PATH` without `factory-guard` would let every write through, and `claude -p` finds its login in `HOME`.

A refused `sudo` (the misconfiguration behind WE3.1) surfaces in the probe as the runtime's `AgentRuntimeError`, which fails the item with its message. The probe is the first agent call of an instance, before any claim is pushed; an error after a claim would reach the crash path of F0008. Rejected: leaving the check to the first stage run, and a probe that only runs `claude --version` (it carries none of a stage's flags).
- Superseded in part by "The Claude Code hook is removed; the kernel and the undo are the write guard": its search for `factory-guard` is removed.
- Replaced in part: the `sudo` chain went with the second user (F0044-S0005) and the probe's guard with the wrapper (F0044-S0001, F0044-S0002); the probe `agent-run-probe` stays, and runs the agent in a throwaway container.

## The shipped agents carry v1's texts, renamed, and `stuck` does not exist

Date: 2026-10-16 (F0010-S0017; questionnaire 1, Q29; F0005 decision 24; F0010 decisions 32 and 36). Each shipped agent's body holds v1's pipeline rules, its role text and its stage text after the two sentences of the earlier story, with v1's words renamed to the glossary's. The reason is the baseline run: it compares v1.1 with v1's run on the same instructions, so the texts change at the level of words and of v1's mechanics, not in other words. Sentences about v1's own mechanics are rewritten to what v1.1 does: the factory commits, pushes and moves the work item, so no agent commits or pushes; round caps, promotion and the pipeline files are the factory's and the human's.

`stuck` is in no body because v1.1 has no `stuck`: an agent that cannot finish ends with `question`. After v1's texts each body ends with `## Lessons`, v1.1's own, kept apart so that v1's text stays recognisable. Rejected: a summary of v1's texts (the comparison would no longer be on the same instructions) and shipping skill files (the runner applies no `skills` key).

## Recovery is proved by injection only; a kill after the result is pushed charges no crash

Date: 2026-10-17 (F0011-S0001). The six kill-point cases kill the factory by arming a kill point (`InjectedKill`, see above), never by killing a process or a container. The container case is the same kill restarted on an empty disk and a new clone. The reason is that an injected kill is exact (it stops between two named steps and can be repeated), runs without a container runtime and leaves the rest of the machine alone. A real container kill is not part of the proof. The count of a crash follows what was in flight: a crash is charged only when the stage-start commit was pushed and the result commit was not, so the kill at `AFTER_POST` (`post-record`), which falls after the result is pushed, charges none, and a stall (a died run while the tick lives) charges an attempt, never a crash. The time from kill to rerun is measured on the manual clock: a scenario advances it by five seconds and the test reads the claim commit's time against it, because a real clock would make the test slow and its result unstable. Alternatives rejected: killing a real process (not repeatable at a chosen step); reading the wall clock (a sleep, and a flaky bound).

## Each fault-injection path is walked with one kill, by judgment

Date: 2026-10-17 (F0011-S0002; `fault-paths.md`). Each of v1's thirteen paths is walked with one kill or one stall added at the step the path adds, not with a kill at every step. The paths are behaviour paths and the mechanisms they exercise are already proved point by point by the kill-point cases; the walk shows that the two together hold, by judgment about where the path is most exposed, as `fault-paths.md` proposed. The case of a path names the kill point it arms, and the path's own crash charge may differ from the case's (path 5 arms `AFTER_PUSH` after the result's push, which charges none). No path is mapped to a removing item, since v1.1 keeps every mechanism. Rejected: a kill at every step of every path (the product of paths and points, most of it the same recovery again).

## Paths 7 to 13 are walked with one kill or one stall each, and path 9 walks `reject` with the kill between commit and push

Date: 2026-10-17 (F0011-S0003). The last seven paths follow the rule of the first six: one kill or one stall added at the step the path adds, chosen by judgment, not a kill at every step. Path 9 walks `reject`, which v1 never ran live, with `BEFORE_PUSH` on the correction's push: the rerun reverts the hand-made stage change once, posts one correction and leaves `origin/main` untouched. Selecting a work item's file in a test takes the `.md` file only, because its `.costs.jsonl` sidecar sits beside it and moves with it. Rejected: removing the sidecar from beside the work item to make a test simpler.

## The producers of the machine stops are proved by their own features; a later stage in a backlog file is removed, not stopped

Date: 2026-10-17 (F0011-S0004). `STOP_TABLE` lists the fourteen stops that v1 let reach only a log, with the destination v1.1 gives each. The seven stops of the repository or the machine are tested here only at their destination (the health status and the time-stamped line of the factory log, through the stop service) and by a search that production code names each reason; the code that detects the fault is proved by F0006 and F0010. The six stops of one work item are proved whole, from the fault through the tick and the dispatcher to the single post. The fourteenth row, a backlog story whose own file names a later stage, has no stop: the start rule removes the fault by starting the work item at the first stage with its counters at 0. Rejected: a stop for it (the file's stage is never read, so nothing is wrong to report) and re-proving every producer in this story. A later in-progress file of an id already read is read from `origin/main` as a started story, since the id's branch holds only the first file; this lets the duplicate reach the dispatcher and the pull request instead of ending the tick.

## The four documents are checked by a command, outside `make check`; v1's words live in one section

Superseded for the docs stage by *The document check runs in the docs stage; the default identity has one home*, and for the project guide's layout by *The project guide is an index and one file per domain*.

Date: 2026-10-17 (F0011-S0005). `python -m factory.entry.check_documents` reads `README.md`, `docs/operator-guide.md`, `docs/project-guide.md` and `docs/decisions.md` and prints `documents ok` or one finding per line (`factory.domain.documents.check_documents` is the pure rule). It requires the operator guide's *Install*, *Configuration* and *The stops* with a row for each stop of `STOP_TABLE`, and the project guide's *Kill points* and *Fault-injection paths* with a row for each case and each path, and it flags the phrases and v1 words of its two lists. It is a command and not a console script, and `make check` does not run it, because `pyproject.toml` and the Makefile are outside the coder's write paths; wiring it in is left to the human. The statements that a document must make about v1 (no `--follow` mode, v1's leftover files, this repository's own v1 tree, the renamed words) stand in a section `## Replaced from v1`, which the check exempts in every document; the decision log is exempt as a whole, because it records what was replaced and renamed. WE6.3 (every story's docs criterion names its documents) is not a test: the cross-feature check observes it across the stories. To keep the list of replaced phrases in `src/factory/domain/documents.py`, the human let the search of `tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode` skip that one file and its compiled form by name (F0011 decision 21); every other file under `src/` is still searched. Rejected: building the phrases at run time to get past the search (it meets the test's words and not its intent), and a data file outside `src/` (the Interface names the constants).

## The duplicates report keys findings without line numbers, and it is a record, not a check

Date: 2026-10-17 (F0012-S0002). A finding's key is `similar-code <modules>: <first code line>` or `dead-code <path>: <message>`, with no line number, because every edit above a finding moves its lines: a key with lines would turn the whole baseline into new findings after any unrelated change, and the human would learn to regenerate it without reading. The line numbers stay in the printed `where`. A pylint or vulture text out of form raises, and the command exits 2, so that a change in a tool's output is seen and not read as "nothing found". The report is a record: its last line goes into the coder's journal entry whatever the exit status, and `make check` does not run it. A new finding is a question for the reviewer, who judges whether the second copy is a real duplicate; pylint's similarity measure and vulture's confidence both produce findings a human rightly accepts, and a gate on them would be bypassed by a growing baseline. Rejected: keys with line numbers (churn), a failing check (it would block work on a judgment call), and a `baseline_text` function in the domain (only the command writes the file).

## The document check runs in the docs stage; the default identity has one home

Date: 2026-10-17 (F0012-S0003; F0012 decisions 3, 12, 16 and 17). This supersedes the F0011-S0005 entry for the docs stage: the human's `make documents` target is a check of the docs stage, so the check runs where the four documents are written, and a missing row or a v1 word is found before the human sees the pull request. `make check` still does not run it. Also: `DEFAULT_GIT_IDENTITY` now lives in `factory.domain.git`, beside `GitIdentity`, and is the one default: `GitOptions.identity` uses it and `factory.domain.settings` re-exports the same object (through `__all__`, because ruff refuses the `import ... as` form). That settles the "Known duplicate" of the 2026-10-16 identity entry. Behaviour is unchanged: `GIT_USER_NAME` and `GIT_USER_EMAIL` still override each half on its own. In the same story `build_boundaries` gives the agent runtime the `sudo` that the preflight's `tool:sudo` item finds on the `PATH` (`/usr/bin/sudo` only when there is none), and the three commands pass `argv` straight to `argparse`, which reads `sys.argv[1:]` itself when given `None`.

The runtime's `sudo` that this entry's check ran under went with the second user, F0044-S0005; the check in the docs stage and the identity's one home stay.

## The YAML fault of the pipeline definition is ruamel's problem and position on one line

Date: 2026-10-17 (F0012-S0006). `yaml_fault` in `factory.adapters.pipeline_yaml` reduces a YAML error to `not valid YAML: <problem> (line <l>, column <c>)`, the position 1-based. ruamel's text spans four to seven lines, and the time-stamped factory log stamps each, so a search for `stop repository` found only the context line; one stop now gives one log line, the same fault in the health status, the log and `PipelineDefinitionInvalid`. The context lines are dropped, and so is the hint `To suppress this check see: ...`, which advises switching off the repeated-key check that the factory wants (F0003 decision 11). A line break inside the problem (a repeated key with a block-scalar value is quoted in it) is written as the two characters `\n` or `\r`, chosen by the human. An error with no problem (a control character) gives the first non-blank line of its text. Rejected: cutting up `str(error)` (the problem's line differs from error to error) and collapsing whitespace (it hides where a value broke).

## Mutation testing is limited to one feature's modules

Date: 2026-10-17 (F0012-S0008; the human's change H5). Superseded by *Mutation testing per story*. This supersedes *No `mutants` target, no mutmut*: the target and mutmut exist now, because every acceptance had run its mutation pass by hand. `make mutants FEATURE=<id>` mutates only the modules under `src/factory` that the commits of one feature changed. A run over all of `src/factory` would take far longer than one acceptance (a trial over six modules of F0011 took 574 s and made 364 mutants), and a feature's acceptance can act only on its own survivors. The modules are found by the commit subjects on `origin/main` that start with `ticket <id>-S<nnnn>:` (v1's prefix) or `work item <id>-S<nnnn>:` (v1.1's prefix, which it writes on its handler records); a module changed under another subject is not found. The target is outside `make check` and lists only the mutants it checked. Rejected: a run over the whole package (the lease and the stall it risks) and mutating the files of the branch's diff (a feature's stories are many branches).

## The low-disk stop is read at the start of every tick, before the fetch

Date: 2026-10-17 (F0012-S0010; F0012 decisions 20 and 34). `Tick.run` reads the free space of the work directory (the checkout's parent) and of the state directory first and raises the machine stop `disk_low` (limit L64) when either has less than `FACTORY_MIN_FREE_GB`. Before the fetch, because the fetch and every later step write, and a write on a full disk can hang. One check per tick and not a preflight item, because the preflight runs inside the tick and only when the image build changed: a disk fills between builds. An unreadable free space stops too, with the error as the detail: an unknown free space is no proof of room (loud over lucky). The first clone of a missing checkout comes before the first check, since the checkout's preparation runs before the tick, so a clone onto a full disk fails as `repository_unavailable`. On a full disk the stop's own writes can raise an `OSError`; it is not caught, and the iteration ends with the scheduler's `iteration failed` line. The tick without `disk` or `settings` does nothing, so tests that build boundaries without them tick as before. By the human's leave, four earlier tests gained the new reason. Rejected: a preflight item (stale between builds), a separate `DiskCheck` service (wiring for one method) and treating an unreadable path as enough room.

## The records of project commands are telemetry in the state directory, not committed

Date: 2026-10-17 (F0012-S0013; F0012 decisions 21 and 22). `RecordingProjectCommands` appends one JSON line per run to `records/project-commands.jsonl` in the state directory. The records are not committed: they are measurements about the factory's own work, not a work item's state, and a commit per run would add a push and a diff to the pull request for every `make check`. The file survives the container (the `state` volume) and may be deleted; nothing decides on it. A record that cannot be written is logged and the result is returned, because telemetry must not lose a run's result. The `command` of a record is the caller's argument, which equals the result's `command` for every implementation. The log is one generic `RecordLog[R]`, not a reader and writer pair as for the cost records, because the disk record (F0012-S0016) uses it again. The records make the count of `check` runs on one commit measurable, the lever for skipping a check whose result for that commit is known. Rejected: committing the records with the work item, and a failing run when the record cannot be written.

## The time per tool command inside a run is not recorded

Date: 2026-10-17 (F0012-S0014; F0012 decision 22). A cost record holds the run's `duration_seconds` and `model_seconds` (the reply's `duration_api_ms`); the rest is the tools' and the factory's. The time of each tool command inside a run (`make check` above all) is not recorded, because the single JSON reply of `claude -p --output-format json` does not carry it: it needs `claude`'s streamed events. Rejected: estimating it from the difference, which mixes the tools with the factory's own work.

## The disk record is not committed and none is written at the end of a run

Date: 2026-10-17 (F0012-S0016). `DiskRecorder` appends one line to `records/disk.jsonl` in the state directory when an instance starts (and at each feature acceptance, F0012-S0017). The record is not committed, for the reason of the records of project commands: it measures the factory's own machine, not a work item's state, and a commit would add a push and a diff to a pull request for every start. No record is written at the end of a run: the last feature acceptance is near it, and the host's numbers (the drive's free space, Docker's disk image) cannot be seen from the container and are read by hand at the end. A failed append is logged and does not stop the instance.

The container-path numbers (Docker's disk image) went with the Docker path, F0044-S0010; the rule stays: the record is not committed, and none is written at the end of a run.

## One test checks the configuration of every model; six models ignore unknown keys

Date: 2026-10-17 (F0012-S0018; the human, 2026-10-14; F0012 decisions 25 and 39). Every Pydantic model under `src/factory` is frozen and refuses unknown keys, and `tests/test_model_configuration.py` checks that once for all of them, replacing the per-model tests of an assignment and of an unknown key, which tested Pydantic and not the factory. A test that also checks something of the factory's own (a pattern, a `Literal`, a limit, a rule across fields) stays. The six exceptions read a tool's own output and declare `extra="ignore"` on purpose, so that a field the tool adds does not break the factory: `factory.adapters.claude_guard._ToolInput` and `_Payload`, and `factory.adapters.claude_runtime._Usage`, `_Denial`, `_StructuredOutput` and `_Reply`. They are listed by name in the test, which also checks that each still ignores. Rejected: a test per model (it grows with every story and checks the library) and a base class that sets the configuration (the exceptions would have to undo it, and a model could still forget to inherit).
- Superseded in part by "The Claude Code hook is removed; the kernel and the undo are the write guard": the two models of `factory.adapters.claude_guard` are removed, and the opencode runtime's eight join the list, twelve in all.

## An answer at the round cap starts the count of rounds over

Date: 2026-10-17 (F0012-S0021; the human's item 1.5; F0012 decisions 26 and 47). `unblock` sets `round` to 0 when the wait was `round_cap`, as an answer to the attempts cap resets `attempts` and one to the crash cap resets `crashes`. Before, `round` was kept, so the first send-back of the rerun passed the cap again and asked again: the answer "one more round" on F0011-S0001 could not work. Granting exactly one round would need the code to read the answer's words, and it reads none (see "The reason and the round cap"), so an answer can only reset the count or keep it; keeping it made more rounds impossible. The human who answers grants the cap's rounds again; the human who wants it to stop closes the pull request. The question says so. The count is shared with the approval's send-backs, so the reset covers them too, while an answer to the approval's send-back question keeps `round` and the next send-back past the cap asks the round cap question once more.

## The compose project is named after the instance

Date: 2026-10-17 (F0012-S0022; the human's item 1.6). `image/compose.yml` has `name: factory-${FACTORY_INSTANCE:?...}`, with the same `:?` message as the service's `FACTORY_INSTANCE`. It was `name: factory`, which is also v1's project name, service name and volume names: `docker compose up` for v1.1 would have replaced v1's container and mounted v1's volumes `factory_work` and `factory_claude-home` (v1's checkout and its `claude` login), and a second v1.1 instance would have taken the first one's. Now each instance has its own container and volumes (`factory-<instance>_work` and so on). The cost: renaming an instance means new, empty volumes. Rejected: a default instance name (`:-`), which lets two unnamed instances, or v1.1 and v1, share a project again.

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## The demo check knows no demo by name

Date: 2026-10-17 (F0012-S0023). `factory.entry.check_demos` checks every folder under `demo/` by the same rules (its three parts, its pipeline definition, its story form, its stories as backlog stories at the path they will have in the project, its line in the index) and holds no list of demos. A new demo needs a folder and an index line and no change to the code, and a demo cannot escape the check by being left out of a list. The check runs in `make check` through `tests/test_demos.py`; without a `demo/` folder it passes. Its stories go through the story check's `backlog_story_findings`, so a demo story and `factory-check-story` give the same findings; the pipeline definition reader is built in the wiring, the one entry module that imports adapters. Rejected: a table of demos in the code, and the check calling the domain's story rules itself (a second copy of the story check).

## The agent's own `timeout` kills a run under `sudo` at its time limit

Date: 2026-10-17 (F0012-S0024; the human's answer to F0010 decision 30, item 1.8). The factory's kill of a call's process group fails under `sudo`: the leader is root's `sudo`, which the factory's user may not signal, so the kill raised `PermissionError` and `claude` ran on. The call now has `timeout --signal=KILL <limit>s` inside the `sudo` call: `timeout` runs as the agent user, so the agent kills its own process tree and the factory needs no right over it. The end is read from the status: 137 or -9 after at least the limit is `time_limit` (marked `timed_out` once in `_call`, so the end reason, the measures and the `sudo:` rule need no change); the same status earlier is `died`. The outer call's limit is the limit plus `SUDO_GRACE` (30 s), so the factory's kill fires only when the inner one did not. Rejected: a `sudo` rule that lets `factory` run `kill` as `agent` (a second rule, wider than the one rule the image has) and a kill by the factory's own user through a group (the agent is not its child). Open: observed for real only at the first start.

Replaced by the throwaway container, v1.2 F0044-S0005.

## The agent home belongs to the factory; the agent adds files and cannot change the installed ones

Date: 2026-10-17 (F0012-S0025; the human's answer to F0010 decision 21, item 1.10). `/home/agent/.claude` is `factory:factory-work` with mode `3775`, and the entrypoint, which runs as `factory`, installs `agents/` as `0755`, each file in it as `0644` and `settings.json` as `0644`. This supersedes F0010 decision 21 for the agent files and the settings: one run can no longer rewrite what the factory and `claude` read on every later run. The agent, in the group, still creates its own files there (its login), and the sticky bit keeps it from renaming or deleting the factory's. The home is the mount point of the volume `claude-home`, so the folder itself cannot be renamed by the agent. The entrypoint uses `find -type f` for the files: a glob fails on an empty folder and skips dotfiles. Open: a volume made by an earlier image keeps its old owner and mode until it is replaced; the files of its own that the agent may add to `~/.claude` and `/home/agent/.claude.json` stay writable and `claude` reads them (a user `CLAUDE.md`, skills) (closed on 2026-10-20 by *Every agent run and every project command starts from a fresh agent home*); a subfolder inside `agents/` would keep its copied mode (the image has none); the sticky bit's effect is not tested, because it needs a container (the morning observation checks the settings file).

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## A missing health file is not healthy; `factory-run` writes an empty one at its start

Date: 2026-10-17 (F0012-S0026; the human's answer to F0010's open point 6, item 1.10). `factory-health` printed `healthy` for a state directory without `health.json`, so a container whose instance never wrote it, or whose check read another directory, looked healthy while `factory-run` had ended with status 2. Now `run_instance` writes `HealthStatus()` first, when there is no file (an existing file keeps its stops), and `factory-health` prints `no health status: <path> is missing` and exits 1 for a missing file. Docker's `start_period` (60 s) keeps that failure from counting while the instance starts. A damaged file still reads as healthy, because a stop that lasts is raised again. The check lives in `main`, not in the store's `read`: a given store is read as before, and the machine stop relies on `read()` of a missing file returning an empty status.

Docker's health check went with the Docker path, F0044-S0010; the rule stays: `factory-health` refuses a missing file, and `factory-run` writes an empty one at its start.

## A failed machine clears a main_branch_failing that names a commit no longer main

Date: 2026-10-17 (F0012-S0027; the human's answer to F0010's open point 5, item 1.10; answers the "Open:" of the F0010-S0009 entry about a stop that stays while the machine's items fail). When the machine's items fail (a new image without `make`, say), the preflight cannot run `lint`, so it cannot know whether the new `main` is green; it did return `preflight_failed` before the probe, and a `main_branch_failing` raised earlier stayed even after the human had pushed the fix. Now, before it returns `preflight_failed`, the preflight compares the `main_failed` commit of the stamp it started with to `origin/main`. When `main` is another commit, or gone, it clears `main_branch_failing`: the stop names a commit that is no longer `main`. The new `main` is probed as soon as the machine's items pass again, and a red one raises the stop anew. A stop whose commit is still `main` stays; so does a stop when the stamp has no `main_failed` or when git cannot resolve `origin/main` (nothing is known). The stamp is not rewritten on this path. Rejected: keeping the stop until a probe has run (a fixed `main` would look broken while the machine is the fault), and clearing it on any failure of the machine (hides a red `main` that has not moved).

## The factory's own commits on a work item's branch carry its id

Date: 2026-10-17 (F0012-S0030; the human, F0012 decision 51). A stage's start, its end, a stall and an acceptance's opening had subjects that named no work item (`<stage> starts as <instance>`, `<stage> ends: <next>`, `<stage> stalled`, `<id> opens`); only the handlers' and recovery's commits used `commit_subject`. Git links code to work items through the subject, and a project's `make mutants` finds a feature's modules by the subject `work item <feature>-S<nnnn>: ...`: the commit that carries a story's source is the stage's end, so it found none. The four commits now use `commit_subject`, so every commit made with `Git.commit` on a work item's branch begins `work item <id>: `. The agents' own commits keep the subjects the agent gave them. The merge of `origin/main` into a reopened branch keeps git's subject: it lists no files in `git log --name-only`, so `make mutants` does not need it. Rejected: adding the prefix inside the `Git` wrapper or `_commit_and_push` (it would also change the agents' commits and the handlers' subjects).

## The template's Makefile has no `documents` target and its `duplicates` has no baseline

Date: 2026-10-17 (F0012-S0029; F0012 decisions 50 and 53). `template/Makefile` carries what F0012 made of `factory-rf`'s own project commands, except two things that are `factory-rf`'s own modules: `make documents` runs the document check of this repository, which a project does not have, and the comparison of `make duplicates` with `security/duplicates-baseline.txt` is `factory-rf`'s own module too. The template's `duplicates` writes the similar and the dead code to `.reports/`, counts them on its last line and compares them with nothing; a project that wants a baseline adds one. Rejected: shipping a copy of either module (a second copy to keep true), and a `documents` target that does nothing (a name that promises a check).

## The token is a bind mount into a folder only the factory can enter

Date: 2026-10-17 (F0013-S0001; the human's answer to the probe's fault 1, `planning/overnight/podman-probe-2026-10-17.md`). The image makes `/home/factory/.secrets` as `factory:factory`, mode `0700`, and `image/compose.yml` bind-mounts the host file `./secrets/hosting-token` into it, read-only and with `create_host_path: false`; `FACTORY_TOKEN_FILE` is `/home/factory/.secrets/hosting-token`. The compose secret is gone. The probe printed the token with `sudo -u agent cat /run/secrets/hosting-token`, under Docker Desktop and Podman alike: Compose ignores a file secret's `uid`, `gid` and `mode` outside Swarm, so the file kept the host's owner and mode (on Windows `-rwxrwxrwx`, owner 0). The agent cannot enter the folder, whatever the file's mode. This supersedes the claim of F0010-S0013 that the factory's user alone reads the mounted secret, and the default path `/run/secrets/hosting-token`. The agent can write git's hooks in the shared checkout's `.git`, and the factory's git ran them as the factory's user, so the folder closed the direct read and not this indirect route; closed by "The factory's git runs no hooks" and "The factory alone writes the checkout's `.git`". Rejected: a compose secret with an absolute target (the same ignored keys), a `chown` or `chmod` in the entrypoint of a file whose owner and mode are the host's (a bind mount of a host file, read-only, and not the factory's to change), and Swarm mode (a cluster for one container).

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## The preflight checks the token's folder, not the file

Date: 2026-10-17 (F0013-S0002; F0013 decisions 10 and 11). The item `token-file` checked that the file belongs to the factory's user and has mode `0600` or `0400`. Since the token is a bind mount, its owner and mode are the host's (on Windows `-rwxrwxrwx`, owner 0), so the check would have stopped every start there, and it passed a `0600` file in a folder anyone can enter, which protects nothing when the file is replaced. What keeps the agent out is the folder, so the item now checks that: the file exists, and its folder belongs to the factory's user with no bit for group or others. The folder is read first, so a folder the factory's user cannot enter is still reported. Rejected: keeping both checks (the file's would still fail on a bind mount). The tests of F0010-S0013 were replaced by the human's leave.

## The runtimes are Docker Desktop and rootless Podman; on Windows the operator restarts the factory

Date: 2026-10-17 (F0013-S0005; the human's answers of 2026-10-17 from the probe `planning/overnight/podman-probe-2026-10-17.md`, faults 2, 3 and 4). The image and the compose file run under Docker Desktop and under rootless Podman (5.8.3, Windows) with the docker-compose v2 binary as the Compose provider; `podman-compose` 1.5.0 cannot build this compose file on Windows, so it is not a provider. The probe's build under Podman (Buildah behind the Docker-compatible API, the image's owners and modes as built) is the check of Buildah's defaults. On Windows nothing restarts the factory after a machine or host restart: `podman-restart.service` cannot be enabled in the machine (`Access denied`) and an `unless-stopped` container stayed stopped (tested), so the operator starts the machine and then Compose. The restart service on a Linux host (with linger) is the documented way and is untested; the first start on such a host observes it. Rancher Desktop is named untested because the probe did not run it. The team setup is one shared Linux host. The disk record sees the machine's virtual disk under both runtimes. Rejected: a restart task the factory installs (outside the container, not the factory's to own).

Replaced by the machine of v1.2: F0044-S0010 removed the image, the compose file and the Docker path; the factory runs on the VM as a service, under rootless Podman alone, and the service manager restarts it.

## The factory's git runs no hooks

Date: 2026-10-17 (F0014-S0001; the human's answer to the first start's fault 2, `planning/overnight/first-start-checklist.md`; closes the route F0013 decision 15 left open). At the first start the agent could write `/work/checkout/.git/hooks`, and the factory's git ran what it found there as `factory`, the user who can read the token. Now `git_environment` returns seven entries (nine with `GIT_CONFIG_COUNT=4` since F0014-S0010, see "No nested repository in the work tree"), a third pair `core.hooksPath` = the null device with `GIT_CONFIG_COUNT=3`. Git reads the `GIT_CONFIG_*` pairs as command-line configuration, which wins over the checkout's `.git/config`, so a `core.hooksPath` the agent writes there does not bring the hooks back. A bare remote's hooks still run: git drops the `GIT_CONFIG_*` variables for the receiving side of a local push, and the remote's `pre-receive` is the hosting service's rule, not the checkout's. Rejected: deleting or locking the hooks folder alone (the agent can write it, and the configuration too). Taking the agent's write access to `.git` away is a later story of F0014 and this stays as defence in depth.

## The factory alone writes the checkout's `.git`

Date: 2026-10-17 (F0014-S0006; F0014 decisions 20 to 23; the human's word, 2026-10-17, on the first start's fault 5, `planning/overnight/first-start-checklist.md`). A `core.fsmonitor` line written into `/work/checkout/.git/config` as `agent` made the factory's own `git status` run a command as `factory`, the user who can read the token. The hooks fix does not cover it: git also runs commands named in the configuration (`core.fsmonitor`, a filter or diff driver, `core.sshCommand`) and in `.git/info/attributes`. Now the factory alone writes `.git`; the agent can read it and cannot create, change, rename or remove anything in it. Agents never commit and the shipped settings deny git's writing commands, so nothing an agent does needs the write.

- `core.sharedRepository` is `0640`: git creates what it writes in `.git` readable and not writable by the group (directories `750`, `2750` under the setgid `/work`). The work tree is written under the umask alone and stays group-writable; `group` never served it.
- Git leaves some files outside that setting (`FETCH_HEAD`, `COMMIT_EDITMSG`, and during a conflict `MERGE_MSG`, `MERGE_HEAD`, `MERGE_MODE`, `AUTO_MERGE`; checked with git 2.39.5), so `Git.seal()` takes the group's and others' write permission from `.git` and every entry in it.
- The agent can still rename `.git`, because the work tree's root is group-writable, and put a folder of its own in its place. It cannot take the group's write bit from a folder of the factory's, so `Git.check_seal()` refuses such a `.git`. A `.git` that is not closed is refused and the checkout cloned again, never repaired: after an agent ran, the factory cannot tell what is in it.
- A folder of the factory's that the group cannot write, renamed into `.git`, would pass a check of the folder alone, and git would look for a repository further up, in `/work`, where the agent can place one. So `check_seal()` also wants a `HEAD` file, and the factory's git runs with `GIT_CEILING_DIRECTORIES` at the checkout's parent.
- The seal runs at the start of every iteration (`CheckoutPreparer.prepare`), which also repairs a checkout cloned before this change.
- The seal also runs around every agent run (F0014-S0009; F0014 decisions 19 to 21, 24 and 30): `run_sealed` seals right before the run and calls `check_seal()` right after it, in a `finally`, so the check also happens when the run fails, and then a `RepositoryUnsealed` wins over the run's error (kept as its `__context__`). The check follows the run because the run is the only time the agent can rename `.git`; no factory git command may run between the two, or it would run in a `.git` the agent chose. A failed check ends the tick: `Dispatcher.dispatch` re-raises `RepositoryUnsealed` and does not count it, since a counted error is retried on the same remote state and the capped report would hide a checkout that the next iteration's preparation removes and clones again anyway. A probe's `RepositoryUnsealed` ends the iteration the same way. The stage's run and the preflight's probe go through the one function.
- Left open (F0014 decision 21): an agent process that outlives its run and swaps `.git` after the check. The time limit ends the run's processes, which is the only closing of that window.

Rejected: a sticky bit on the checkout's root (it would stop the agent from renaming, removing or replacing any of the factory's files there, such as `uv.lock` and `.venv`); a git folder outside the work tree under `GIT_DIR`; a volume mounted at `.git`; a umask of `022` for git (it would close the work tree too); a check before every git command. Open, not planned (see *v2 is retired; nothing is left for v2*): the clone's working folder (the checkout's parent) and the process environment `GitCli` passes on first. The hooks fix stays as defence in depth. `make test` has no second user, so the tests use a mode bit and a changed effective user id; the real check as `agent` is one of the operator guide's checks on a running instance.

Replaced by the dataset's rollback, v1.2 F0044-S0006.

## No nested repository in the work tree

Date: 2026-10-17 (F0014-S0010; F0014 decisions 30 to 32). The seal keeps the checkout's own `.git` the factory's alone, but the agent can still make a git repository anywhere in the work tree it may write, for example with `uv run ...`. The pre-check found the route with git 2.39.5: the factory's commit (`git add --all`) adds such a repository as a gitlink with only a warning, and from then on the factory's `git status` and `git diff` start a child `git status` inside it, which reads that repository's own configuration. Its `core.fsmonitor` ran as `factory`, the user who can read the hosting token. A nested `.git` the agent makes itself may also pass git's ownership check, since the agent can rename one of the factory's group-writable folders into place. `diff.ignoreSubmodules=all` did not stop the child.

- After every agent run, right after `check_seal()` and before any git command, `run_sealed` calls `Git.remove_nested_repositories()`, which removes every entry named `.git` (folder, file or link) below the root other than the root's own, with no git process. The removal comes first because any git command that ran earlier would already have met the repository.
- The stage stalls with the reason `nested_repository` and the paths, rather than keeping the agent's work silently: the agent made a repository the factory cannot keep, and the stall tells it and the operator so. The files beside the removed `.git` stay and are judged by the undo and the write paths like any other.
- `core.fsmonitor=false` joins the factory's git environment pairs as a second line of defence: the child git inherits the `GIT_CONFIG_*` pairs, so even a nested repository the search missed cannot start its `core.fsmonitor`. Other keys of a nested configuration were not tried; the removal is what covers them.
- The same search runs at the start of every iteration on an existing checkout that passed the seal check, so a repository left by an older checkout or by a failed removal never meets a git command. One it cannot remove makes the preparer clone the checkout again, and when that fails the stop `repository_unavailable` follows. The agent-run probe fails its item with the paths instead of stalling.
- `git clean -f -d`, the restore, keeps a nested repository; only `-ff` would remove it. The removal does not use git for this, so it does not depend on either flag.

Left open: an index entry of mode `160000` without a repository behind it is not refused, since no child git starts for it; and a folder the factory cannot list is not searched, since its git cannot read it either.

Replaced by the dataset's rollback, v1.2 F0044-S0006.

## The agent's git trusts the shared checkout

Date: 2026-10-17 (F0014-S0002; the human's answer to the first start's fault 1, `planning/overnight/first-start-checklist.md`). `git status` as `agent` in `/work/checkout` failed with `detected dubious ownership in repository at '/work/checkout'`: the checkout belongs to `factory`, and git refuses a repository of another user unless a `safe.directory` names it. Every agent stage that reads a diff or a log was hit.

- The image installs a root-owned `/etc/gitconfig` (`0644`, from `image/gitconfig`) with one entry, `safe.directory = /work/checkout`. The agent can read it and cannot write it. The path is tied to the settings' `CHECKOUT_PATH` by a test.
- The factory's own git needs none: it owns the checkout, and its wrapper sets `GIT_CONFIG_NOSYSTEM=1`, so the file never reaches the factory's git commands. A project command's git (`make`, as `agent` since F0040-S0002) does read it, and a safe directory for the factory's own checkout changes nothing there.
- Git trusts only the exact work-tree path: not a trailing slash, not `.git` (checked with git 2.39.5). The entry is therefore `/work/checkout` exactly.
- The agent's git needs only read access to `.git`, which the `0640` of "The factory alone writes the checkout's `.git`" keeps; `git status` skips its index refresh when it cannot write.
- Rejected: `safe.directory=*`, which trusts every repository; a `.gitconfig` in the agent's home, which the agent can rewrite; a `GIT_CONFIG_*` name in the agent run's environment, which would widen its allow list.
- Observed only at the shakedown run: the tests cannot be a second user.

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## The agent's login is a token from a file

Date: 2026-10-17 (F0014-S0003; F0014 decisions 9 and 30; the human's answers to the first start's fault 3, `planning/overnight/first-start-checklist.md`). Every new instance needed an interactive `claude` login as `agent`: a new `claude-home` volume, and the Podman machine with its own volumes, each needed one. The human's answer: every credential is injected from outside, and no instance needs an interactive login.

- The login is a token made once with `claude setup-token`, kept in a file named by `FACTORY_CLAUDE_LOGIN_FILE`, and handed to each `claude -p` call only, as `CLAUDE_CODE_OAUTH_TOKEN`. Without the file, or with a blank one, the login in the agent's home is used as before.
- The name is Claude Code's, so it stays in `factory.adapters.claude_runtime` (R12). `ALLOWED_ENVIRONMENT_NAMES` keeps its six names: it filters what is copied from the factory's own environment, and the token never passes through that environment.
- The agent's own shell reads the file, as the user the call runs as, and `exec`s `claude`. The token thus stands on no command line. On a Linux host every host user's `ps` shows a container's processes with their arguments, unless `/proc` is mounted with `hidepid=2`, so a token in an argument would be seen beyond the container. The factory never holds it, and a file it cannot use stops the run with a message that names the path.
- The image mounts the file (F0014-S0004): `image/secrets/claude-token` on the host, bind-mounted read-only at `/home/agent/.claude-token`, with `create_host_path: false`, and `ENV FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token`. The place is the agent's home because it is the agent's own login, which it may read; it is outside the volume `claude-home`, so no mount nests in another, and outside `/home/factory/.secrets`, which the agent must not enter. A missing host file makes Compose refuse to start; an empty file is the operator's way to keep the manual login.
- Rejected: the factory reading the file and passing the token as an `env -i` assignment on the `sudo` command line (visible in `ps`, and the factory would hold the token).
- Left out: an API key (`ANTHROPIC_API_KEY`). This story builds only the token from `claude setup-token`; the reason is in F0014 decision 15 and F0014's `FEATURE.md` ("Out of scope"). The factory runs agents under the operator's own subscription login (R12), while an API key bills by use. Claude Code prefers an API key it finds over the subscription, so a stray key file would change who pays without a word. Nothing in v1.1 needs one, and a team setup that wants one gets its own story.

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## Journal records say when, in which stage and from which run; cost records on which instance

Date: 2026-10-18 (F0014-S0007; the human's word of 2026-10-17 for the status map, `planning/overnight/first-start-checklist.md`). The status map is a viewer that reads GitHub only. It could read a work item's place, state, claim and cost records, but not when a journal entry was written, in which stage, or from which agent run. The cost record's `instance` is F0014-S0008 (last bullets).

- `JournalRecord` gains `at`, `stage` and `run`, each optional when read, so every record written before this stays valid and no file is migrated.
- An unset field is left out of the file rather than written `null`: an old record is written back byte for byte, the pinned layout of the file stays, and a reader of old files sees no new key. The other fields of a record are never `None`, so the writer leaves out every `None` of a record (`model_dump(exclude_none=True)`), and a later optional field gets the same treatment.
- The time comes from the factory's `Clock` through `append_entry`'s `at` parameter, not from the domain, which has no clock; the claim's `started_at` stands for `started`. The stage comes from the document's state, so `append_entry` is still the one writer of both halves and no call site changes its order (hence a `move_back` entry carries the stage the human set, and a story's `done` entry the stage it was merged in).
- Only entries that came from an agent run carry a `run`: the role's entry and the factory's `question` of a stage's end, and the `stall` of a run with a cost record. A `crash` or `expiry` has no run to name; the human's and the factory's other entries come from none. `run` without `at` is refused.
- Rejected: a marker in the entry's text (the journal's text is display only, see "No code reads data from the journal's text") and a change to the pull request.
- A cost record gains `instance`, the name of the instance that ran the agent run, because two instances may work on one project and the status map reads GitHub only. It is optional when read, so no sidecar is migrated. `CostRecorder.begin` takes it from the instance's settings, as it takes `image`, and `complete` keeps it.
- Its key is left out when unset, while `image` is written `null`. `begin` rewrites the whole sidecar, so a line the writer of today wrote is written back unchanged, and the lines written before this story stay as they were. A `null` would change every old line the next time `begin` ran.
- An instance built before this story refuses a line with the key (`unknown key: instance`), so the instances of one project are upgraded together.

## A project's secrets scan leaves out the cost records; run ids stay hexadecimal

Date: 2026-10-18 (F0015-S0001; F0015 decisions 1 to 3; the tiny story F0099-S0001 on the todo demo). `CostRecorder.begin` writes each run's record into the sidecar `<work item>.costs.jsonl`. The record's `run` is a `uuid4` as 32 lowercase hexadecimal characters, which detect-secrets reads as a high-entropy secret, so the first agent run of every work item made the project's `make check` red.

- A cost record holds run metadata and no secret. The template's `make secrets` therefore leaves out every path that ends `.costs.jsonl`, in any folder, as it already leaves out `uv.lock` and `.secrets.baseline`. A rule on the path holds for any id and any scanner; a path that merely contains `.costs.jsonl` or is named `costs.jsonl` is still scanned.
- Rejected: a prefix on the run id (the id's form is the factory's and the status map reads it; a prefix would only suit one scanner's heuristics); a baseline entry per finding (every run writes a new id, so the baseline would grow without end); a pragma in each line (the factory writes the file and would have to put a marker into every record).
- Rejected: a narrower pattern limited to `factory/features/` (decision 2). The sidecar stands beside its work item wherever the project keeps it, and the suffix is the factory's `COST_RECORDS_SUFFIX`.
- The todo demo's `secrets` recipe is pinned to the template's by `tests/test_demo_makefile_secrets.py` (decision 3). The demo had its own copy of the line, and the two drifted apart once; a test is cheaper than a note.

## The container runtime's init reaps the processes a killed run leaves

Date: 2026-10-18 (F0015-S0002; F0015 decisions 6 and 7; the tiny story F0099-S0001). After the coder's `time_limit` killed its run under `sudo`, `ps` in the container showed `[claude] <defunct>` of `agent` with parent 1.

- Cause: `timeout --signal=KILL` kills `claude` and then its own process group, which ends `timeout` before it can wait for `claude`. `claude` and what it started go to PID 1, which was the factory's Python (the entrypoint `exec`s it) and reaps only its own children. A zombie is reaped only by its parent, so it stayed until the container restarted. A project command killed at its time limit leaves the same, because `run_process` kills the group and waits only for its child (since F0030-S0001 it kills the whole session; see *A command stopped at its time limit loses every process of its session*; the init still reaps what the kill leaves).
- Decision: `init: true` on the service in `image/compose.yml`. Docker runs `docker-init` (tini) and Podman, through its Compose provider, `catatonit`, as PID 1. It starts the entrypoint, forwards the stop signal and reaps every orphan. The entrypoint's last line stays `exec python -m factory.entry.run`, so the factory is the init's direct child and receives the forwarded signal.
- Rejected: the factory as the reaper (a PID 1 that reaps every child, with `waitpid(-1)` or as a child subreaper, would also reap the children that `run_process` waits for through `subprocess`, and those would then find no exit status: a race with every project command and agent run, in the module that starts every process; it would also own PID 1's other duties, such as reaping processes it never started, and signal forwarding, which the runtime's init already does); tini installed in the image (another pinned package or download, to do what the runtime ships); `timeout --foreground` (it changes which processes `timeout` signals, so the tree under `claude` may no longer be killed with it).
- No test in `make test` shows the reaping: the init exists only in a running container, and `make test` starts none. Tests pin the compose key and the entrypoint's `exec`; the reaping is a morning observation of the shakedown (operator guide, "A `time_limit` under `sudo`").

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## A standing leave to move a shared test helper

Date: 2026-10-18 (F0016-S0001; F0016 decisions 1 to 3 and 9). At the shakedown of 2026-10-18 on the todo demo, three of eight stories paid review rounds and questions for copied test helpers: $8.85 for the three, about $6 above three clean passes. A new test needed a helper, a constant or a fixture that an earlier story's test module held; copying it was a finding, changing the earlier module was a question. In one story the agents moved the helpers without asking, and nobody noticed.

- Decision: the template's `CLAUDE.md` gives a standing leave under *Tests*, and the `Not without asking` bullet points to it. A shared helper may be moved to one shared place under `tests/`, and the earlier tests changed to use it, without asking.
- Bounds: only a move of a shared helper; every earlier test keeps its name and checks the same thing; any other change to another story's test still asks; the tester alone makes the move, and its entry names each earlier test file it changed. When a reviewer finds a copy, the coder ends with `tests` and names the move.
- Rejected: a question every time (the cost above); the coder making the move (the coder never edits tests); a leave for any refactoring of earlier tests (too wide to judge "checks the same thing"); the leave in the shipped agents alone (it is a project's rule, and `CLAUDE.md` is where the project says what needs asking); a new prompt line for the tester (the existing `Mode: a test change the human approved` line serves, F0016 decision 2).

## The reviewer names every earlier test the diff changes

Date: 2026-10-18 (F0016-S0002; F0016 decisions 5, 6, 9 and 10). At the shakedown of 2026-10-18 on the todo demo, one story changed three earlier test files unasked. The changes were harmless, but neither its reviewer nor the feature's acceptance said so; the rule "a test another story wrote only with the human's leave" was held by the agents' reading alone.

- Decision: the reviewer's checklist gains a sixth item, *Earlier tests*, done in every review whichever group failed. It lists each test file that `main` holds and the diff changes, renames or deletes, with the leave for each: the standing leave to move a shared test helper (see "A standing leave to move a shared test helper"), the human's leave, or none needed when tests are only added. A change under none of them is a finding. The acceptance reviewer's check 6 gathers the reviewers' lists for the human and names an earlier test changed with no leave as a finding.
- Rejected: a check in code (the factory can list the files but cannot judge whether a test still checks the same thing); the same diff check over the whole feature by the acceptance reviewer (it repeats every reviewer's reading at every acceptance, for what the reviewers' lists already give); a change of the reviewer's entry sentence (F0016 decision 5: the entry keeps its shape, and the list follows the findings).

## An approval's description is written before the push that shows the approval

Date: 2026-10-18 (F0016-S0003; F0016 decisions 7, 8 and 9). At the shakedown of 2026-10-18 the board showed an acceptance at `approval` about 25 seconds before its pull request's description held the report, because the description came from the next tick's hand-over. Stories had the same gap: their pull request showed the text it was opened with, without reports and commits.

- Decision: `StageFinisher` writes the description of a move to an approval stage after the result commit and before its push, with the text the hand-over writes (`hand_over_description` for a story, `acceptance_description` for an acceptance). The ready flag, the cost table and `handed_over` stay the hand-over's on the next tick, which writes the description again with the same text. A `HostingServiceError` there is logged and the push goes on; the hand-over writes the description then.
- Rejected: the whole hand-over in the finisher (it would mix the stage's result with the human's hand-over, and a failure there would hold back the push); `handed_over` recorded in the result commit (the record must follow the effects it vouches for, so a failed write would be marked as done); the description written after the push in the same tick (the gap would only shrink, the board would still show the approval first); the board showing an approval only once it is handed over (a change to what the board reads, for a gap that a write order closes).

## The tests reopen their tmp_path after every test

Date: 2026-10-18 (F0017-S0001; F0017 decisions 1, 4 and 6). On 2026-10-18 v1's container held 10 `garbage-*` and 198 `pytest-*` folders, 5.4 GB, removed by hand as root.

- Cause: pytest keeps the base folders of its last three sessions and removes older ones at the start of a later session. Its removal handler adds read and write bits only after a failed `unlink` or `rmdir`, never for a folder it cannot open or list, so a folder closed to its owner stays as `garbage-*` and every later session fails on it again. `GitCli.seal()` itself takes only the group's and others' write bits; the `make mutants` mutant of `_close` that drops the `~` closes `.git` to `0o020` (a `.git` at `0o2775`), and the seal tests that fail on it left that folder behind.
- Decision: an autouse fixture, `reopened_tmp_path` in `tests/conftest.py`, calls `reopen(tmp_path)` (`tests/tmp_path_support.py`) after every test that uses `tmp_path` and after the teardowns of its other fixtures. `reopen` walks top down, opening each folder before listing it, adds the owner's bits only (every other bit stays) and does not follow links. A test needs no sudo and no second user, because every entry belongs to the test user.
- Rejected: a fixture on the seal tests alone (any other test that seals a checkout, and any later one, would leave the same folders); sealing a copy in each test (changes what the tests check); `sudo` or a second user (the container and the developer's machine need neither, and the owner may change the mode of its own entries); a sweep of `/tmp/pytest-of-<user>` at the start of a session (it removes the folders after the damage and from outside the test that caused it, and it cannot open a folder either without the same walk).
- The fixture cannot reach the `pytest-*` folders that a stopped run leaves locked, because a stopped process runs no teardown; those are handled by *make mutants runs under a temporary root of its own*.
- The seal this entry's cause names went with F0044-S0006; the fixture `reopened_tmp_path` stays, for the folders a test leaves closed to its owner.

## make mutants runs under a temporary root of its own

Date: 2026-10-18 (F0017, the human's change 1; F0017 decision 7). *The mutants target keeps only its sweep form* keeps the temporary root and drops the `chmod -R g+w mutants` and the removal of `.git` folders.

- Cause: mutmut stops a mutant's pytest at its time limit; a stopped process runs no teardown and leaves its numbered folder's `.lock`, and pytest removes a locked folder only when the lock is older than three days. On 2026-10-18 v1's container held 58 such folders, 2.4 GB.
- Decision: the `mutants` recipe runs mutmut with `TMPDIR` set to a folder made by `mktemp -d`, and the recipe's `EXIT` trap opens that folder for its owner and removes it when the recipe ends, also after `mutants: stopped after ...` and after a failed run.
- Rejected: `-o tmp_path_retention_policy=none` in mutmut's pytest arguments (each run's cleanup removes the numbered folders of the other workers still running); `--basetemp` (each run removes the given folder at its start, so parallel workers remove each other's); a sweep of `/tmp/pytest-of-<user>` at the start of a session (it works outside `tmp_path` and cannot tell a stopped run's locked folder from a running session's); `PYTEST_DEBUG_TEMPROOT` (pytest's debug variable, not a documented setting; `TMPDIR` is what `tempfile.gettempdir()` reads).

## factory-rf is built by v1.1 since the handover

Date: 2026-10-18 (commit `3bcee441`; F0018). Until then v1 built this repository from `factory/` in v1's layout. Since the handover v1.1 builds it from `factory/pipeline.yml`, `factory/story-form.md` and the features under `factory/features/`.

- Decision: v1's `stages.yml`, forms and features F0001 to F0017 moved to `factory/v1/`, and v1.1's features continue the numbers from F0018.
- On 2026-10-19 `factory/v1/` was removed with the planning history; both are kept at the tag `planning-history-2026-10-19`.
- Why v1's features left `factory/features/`: v1.1 reads no v1 work item, and v1's `done/` folders would have made each of v1's features count as due for an acceptance.
- Why the numbers continue from F0018: `make mutants` finds a feature's modules by its id in the commit subjects, and a reused id would match v1's commits.
- v1 is stopped, not removed, as the fallback.
- Rejected: leaving v1's features in place (each would be due for an acceptance); restarting the numbers at F0001 (the ids would clash with v1's commit subjects).

## The write guard by the kernel: Landlock through ctypes

Date: 2026-10-18 (F0019-S0001). The hook `factory-guard` sees two tools (`Edit` and `Write`) and the undo reverts the rest afterwards; a shell command writes wherever the agent's user may. Landlock makes the kernel refuse a write by every route, for the process and all its children, without privilege. S0001 builds the adapter (`factory.adapters.landlock`); the wrapper `factory-confine` and the runtime use it later.

- Decision: `ctypes` from the standard library calls the system calls directly, with every argument of the variadic `syscall` and `prctl` given an explicit C type. No dependency is added.
- Decision: the rules handle the twelve write rights of ABI 3 (refer and truncate included) and nothing else, so reading, executing and the network stay open. A folder rule allows all twelve beneath it; a file rule only writes and truncates the file in place. The minimum is ABI 3 because refer and truncate arrive with it; below it a rename across folders or a truncate could not be refused.
- Decision: fail closed. Every path is checked with `os.lstat` before the first system call (missing, symbolic link, wrong kind), so a refused rule leaves the process unrestricted and the caller sees a `ConfinementError` and not a half-made restriction.
- Rejected: a binding from PyPI (a dependency for four system calls, and a package to trust); changing modes or ownership over the tree (it needs the tree to be ours, races with the agent and is undone by any `chmod` the agent can run); a helper that runs as root (a privileged part to build and defend, where Landlock needs none).
- Replaced by the dataset's rollback and the take, v1.2 F0044-S0002.

## factory-confine replaces itself with the runtime

Date: 2026-10-18 (F0019-S0002). The kernel's restriction must be applied by the agent's own user, after `sudo` and before the runtime starts. `factory-confine` does that and then becomes the command.

- Decision: the wrapper ends in `os.execvpe` (`replace_process` in `factory.adapters.process`) and does not start a child. The command keeps the wrapper's process and process group, so the `timeout` around the runtime and the factory's kills of the process group still reach it, and no parent process is left to forward signals or an exit status.
- Decision: every fault before the replacement is one line starting `factory-confine:` and exit status 1; the command never starts (fail closed).
- Decision: the exception in `CLAUDE.md` widens by `os.execvpe` in `process.py`, with `noqa: S606` and `nosec B606` on that one line: six markers there in all. `factory.entry.confine` imports the landlock and process adapters directly (feature decision 19).
- Rejected: a child process under the wrapper (the group kill would need the wrapper to survive and pass on its signals, and the wrapper's own process would stay unrestricted beside it).
- Replaced by the dataset's rollback and the take, v1.2 F0044-S0002.

## The kernel's targets of the write paths and the tool paths

Date: 2026-10-18 (F0019-S0003). The kernel allows writes beneath folders and on existing files; a write path is an `fnmatch` pattern, and a run also writes tool state that no write path names.

- Decision: a pattern or a file still to be made is widened to the nearest folder the kernel can name, and never to the checkout's root, which would allow every write; the undo after the run narrows what the pattern does not match. A pattern at the root, and a new file at the root, have no target.
- Decision: the project's tool state is the optional key `tool_paths` of the pipeline definition, in two forms only, `<folder>/*` in the checkout and `~/<folder>/*` in the agent's home. It is read at the stage-start commit with the write paths and passed on unchanged. It reaches the kernel's targets only: the hook and the undo judge the write paths, so a tool path never lets a change into the work item.
- Decision: the functions are pure and in the domain (`write_targets`, `confinement_of`); the files that exist and the runtime's own paths are arguments, so the tests need no kernel. A path with a `.` or `..` segment gives no target, because pathlib would collapse it into the root or the folder above.
- Rejected: widening a missing root file to the root; a tool path with a wildcard in the middle or at the root (the kernel cannot name it); reading the tool paths from the work tree (an agent could widen its own run).
- Replaced by the dataset's rollback and the take, v1.2 F0044-S0002.

## Every agent run is confined by the kernel

Date: 2026-10-18 (F0019-S0004). The pieces (the Landlock adapter, the wrapper, the targets of the write paths) are joined: the `claude -p` runtime starts every call through `factory-confine`, and `build_boundaries` builds it so by default.

- Decision: the runtime's own folder in the agent's home is `<HOME>/.claude`, and the runtime sets `CLAUDE_CONFIG_DIR` to it. Claude Code saves `.claude.json` by replacing it, which a rule for one file refuses and only the whole home would allow. With the variable, Claude Code 2.1.296 wrote `.claude.json`, its backups and its other state under `<HOME>/.claude` and nothing at the home's root; without it, `~/.claude.json` was refused and never written, with no error. The home's root, `.bashrc` and `.profile` stay refused, so an agent cannot change the environment of later runs; inside `.claude` the agents and `settings.json` stay read-only by file permissions (F0012-S0025), since Landlock cannot exclude beneath an allowed folder.
- Decision: the device files `/dev/null`, `/dev/zero`, `/dev/full`, `/dev/random`, `/dev/urandom` and `/dev/tty` and the folder `/dev/shm` are allowed, each only when it exists. The `/dev/shm` literal carries `noqa: S108` and `nosec B108` on its one line, named in the exception list of `CLAUDE.md`. Chosen over a per-file ignore, which silences more than that line, and over leaving `/dev/shm` out, which drops the shared memory that Python's multiprocessing uses.
- Decision: one temporary folder per run, `<temporary root>/factory-run-<session>` (`/tmp` in the container), made by the wrapper as the run's user with mode `0700` and refused when it exists, with `TMPDIR` pointing to it. The runtime removes it after every call, also after a kill or an error, as the run's user (`chmod -R u+rwX`, then `rm -rf`). A resumed call gets it fresh. A removal that fails changes no result. It also ends the growth of `/tmp/pytest-of-agent` found by F0018's acceptance, since pytest follows `TMPDIR`.
- Decision: the runtime confines when it is built with `confine_executable`; `build_boundaries` passes `factory-confine` by default and the package's callers pass nothing else. A request without guard settings is confined too, with no path of the checkout. Tests that build the runtime directly pass nothing and keep their command lines.
- Rejected: leaving the confinement to a flag of the operator (an unconfined run would be one setting away); a fallback when the kernel is too old (the run stops with the wrapper's line instead); allowing the agent's whole home.
- Replaced by the dataset's rollback and the take, v1.2 F0044-S0001.

## No agent runs without the kernel's write guard

Date: 2026-10-18 (F0019-S0005). Every run starts through `factory-confine`, so a kernel without Landlock ABI 3, or a run whose `PATH` lacks the wrapper, would end every run in an error. The preflight finds it first with the machine item `confinement`, after `agent-environment` and before `agent-run-probe`.

- Decision: the item's failure is the existing machine stop `preflight_failed`, naming `confinement` and each fault, so no agent runs and no new stop reason exists. The factory does not fall back to the hook (feature decision 12).
- Reasons: the hook covers only `Edit` and `Write`, so a fallback would drop the guard for every other route on exactly the machine that lacks it; the hook is to go after the cross-check, and a fallback would keep it as a second code path; the kernels the factory runs on offer ABI 3 or higher (6.18 offers 7; WSL2 kernels are 6.6 or later, `wsl --update`).
- Alternative left to the human: an operator setting that falls back to the hook alone, with a warning on every tick.
- Superseded in part by "The Claude Code hook is removed; the kernel and the undo are the write guard": there is no hook to fall back to.
- Replaced by the dataset's rollback and the take, v1.2 F0044-S0001.

## The hook allows the run's temporary folder

Date: 2026-10-18 (F0019-S0011). R14 sends every agent to `$TMPDIR` for temporary files, and the kernel allows that folder, but the hook `factory-guard` refused an `Edit` or `Write` there with `<path> is outside the checkout.`. The agent then wrote the file through the shell, which R14 also forbids, and the cross-check of the hook against the kernel would have counted each such refusal as a disagreement.

- Decision: `GuardSettings` carries the run's temporary folder (`temporary_directory`, `None` by default), and `judge` allows a real path strictly beneath it, after the checkout is judged: a link into the checkout, or a checkout beneath the temporary folder, is still decided by the write paths. The runtime sets it only when it confines the run; without it the hook judges as before.
- Decision: the tool paths stay kernel-only.
- Rejected: telling the agents to write temporary files through the shell only (it contradicts R14's intent and leaves the hook and the kernel disagreeing); counting these refusals as expected in the cross-check (it hides real disagreements behind a known one).
- Superseded in part by "The Claude Code hook is removed; the kernel and the undo are the write guard": the hook is removed.
- Removed with the hook in F0044-S0002; the run's temporary folder went with the wrapper (F0044-S0001).

## A question records the block it opened, a stall its reason

Date: 2026-10-18 (F0021-S0001). A journal record said that a question was asked or that a stage stalled, but not why; the cause was only in the entry's text, which no code reads. The human's waits and the status map need the cause.

- Decision: a `question` record carries an optional `blocked` (`question`, `attempts_cap`, `round_cap`, `crash_cap`, `send_back`) and a `stall` record an optional `reason` (the stall reasons). Every place that records a blocking question or a stall writes the field; a record without it, every record written before this, stays valid and is written back without it. The model refuses `blocked` on any other kind and `reason` on any other kind.
- Reasons: the status map reads the front matter and never parses prose, so the cause has to be data; the types already existed (`Blocked`, `StallReason`) and moved to `factory.domain.journal` so that the record can name them without a circular import, kept by assignment where they were.
- Rejected: parsing the entry texts (a change of wording would change what the map reads); a reason on `crash` and `expiry` records (they are not stalls, and the question that follows the crash cap already carries `blocked: crash_cap`; the feature's decision 4).

## The stops reach main as raised and cleared records

Date: 2026-10-18 (F0021-S0003). A stop of the repository or the machine was a line in the factory log and an entry in the health status, both on the instance, where the status-map viewer cannot reach them.

- Decision: each stop is two events, `raised` when a stop of its reason is first raised and `cleared` when it clears, appended to `records/stops.jsonl` in the state directory by `StopService`. Every tick, right after the restore and before the preflight, `StopPublisher` pushes the records `main` does not hold to `factory/stops.jsonl`, as the commit `stops recorded`. A record holds the event, scope, reason, time and instance, never the detail. The detail stays out because `make secrets` reads every tracked file on `main`, a git error's text can hold a commit id or a URL, and a red `make secrets` on `main` would raise `main_branch_failing`.
- Decision: a failed publish only writes `cannot publish the stop records: <error>`; the records stay local and go with the next tick, so a stop is never lost because git was what failed. A tick that stops before the restore publishes nothing.
- Decision: the publish stands after the restore because the restore logs what a killed stage left behind before the publisher's checkout could discard it, and before the preflight so the records of an earlier tick reach `main` also when this preflight stops the tick.
- Decision: without a readable health status no `raised` record is appended (chosen by the human). The records stay paired with the status, so every `raised` gets one `cleared`. A stop that clears before the status is readable again is missing from the records; its log line remains.
- Reasons: the viewer reads `main` and the factory's state is the remote's (R1); a stop's events are facts of the repository, the detail is the instance's.
- Rejected: the health status file or the factory log as the published place (instance-local, rewritten or unstructured); a branch of its own for the records (the viewer would read two places); a GitHub issue or comment (the hosting-service interface does pull requests only, R10); a separate event per tick that the stop lasts (it would grow without telling more).
- Accepted effect, removed by F0021-S0008: a `stops recorded` commit is a new `main`, so the preflight used to clear `main_branch_failing` (and record a `cleared`) while `preflight_failed` stood, although `main` was still red. A `cleared` record for a `main` nobody fixed misleads the viewer of `factory/stops.jsonl`, so the stale-stop rule now keeps the stop when the only path that differs from the remembered failing commit is `factory/stops.jsonl`. The probe still runs once for such a commit when the machine's items pass; skipping it is left to a later story.

## The reviewer passes test-quality points on as notes from round 1 on, and may add a criterion that needs no code

Date: 2026-10-18 (F0021-S0005). Two questions kept reaching the human: the round cap, asked after the reviewer sent a story back at every round for the quality of its own new tests, and a request for a criterion that needs no code, for behaviour the diff already builds. Both are the factory's way from an LLM on watch to running alone.

- Decision: from round 1 on, a test-quality point in a test file the diff adds is a note under `Notes:` in the reviewer's entry and does not send the story back; at round 0 it still does. A point on a criterion, the architecture, security or `src/` stays a finding.
- Decision: the reviewer may add a criterion that only pins behaviour already built, writing it into the story and naming it as `criterion <n> added: it needs its test`. The coder ends with `tests` without a code change and the tester writes the test. A criterion that needs code stays a finding or a question.
- Reasons: the questions were about nothing the human decides; the added criterion is still a send-back, so the round cap keeps a limit.
- Rejected: raising the round cap (it only delays the same question); leaving every criterion to the human (the question needs no judgement and costs a wait).

## The records carry generated JSON Schemas under `src/factory/contract/`

Date: 2026-10-19 (F0021-S0006). Readers outside the factory, first a page that reads a factory's records from GitHub, read a work item's front matter, its `.costs.jsonl` lines, `factory/stops.jsonl` and the pipeline definition. Until now the only description of those records was the Pydantic models, so a reader learned of a change when it broke.

- Decision: five JSON Schema files, generated with `model_json_schema` from the models that validate the records, are committed in `src/factory/contract/`. Each carries `x-records-contract`, the records contract's version (`1.0` at first, `1.1` since F0020-S0001). A command regenerates them and a test compares them with the committed files, so a model change without a schema change fails `make check`. The major version rises for a change that can break a reader (a field removed or renamed, a type narrowed, a meaning changed), the minor for an added optional field or value.
- Reasons: a reader needs a description it can fetch without running the factory; a generated file that a test compares cannot drift from its model. Package data ships in the wheel and sits on `main`.
- Rejected: schemas written by hand (they drift from the models); a folder at the repository's root (it needs a write path of its own); the pipeline definition's `contract` as the records' version (it versions the definition's format and would tie two unrelated changes together).
- The records contract's version is `2.0` since F0044-S0002: it removed `tool_paths` from the pipeline definition's schema, a change that can break a reader.
- The records contract's version is `3.0` since F0044-S0006, which removed the stall reason `nested_repository`.
- The records contract's version is `4.0` since F0045-S0004, which removed the stall reason `left_branch`; no agent can cause it on the dataset.

## An agent run logs in with an API key when its file holds one

Date: 2026-10-19 (F0020-S0001; F0020 decisions 1 to 3). Every agent run logged in with the subscription token. opencode cannot use the subscription, and an instance at the human's work runs on an API key, while this repository's own build stays on the subscription.

- Decision: a second login file, named by `FACTORY_API_LOGIN_FILE`, which the image mounts at `/home/agent/.anthropic-api-key` from the host's `image/secrets/anthropic-api-key` or the file `FACTORY_API_KEY_FILE` names for the compose call. When it holds a key, the call's shell hands it to the run as `ANTHROPIC_API_KEY` and hands over no token; otherwise everything is as before.
- Decision: the file, not a variable, is the setting, so each instance on a machine has its own (an empty file for the subscription, a key for opencode) and a new key applies from the next call.
- Decision: the factory never reads the key. The run's own shell reads it at every call, so it reaches no argument, run file, result, journal, cost record or log, and not the factory's environment. The shell reports on standard error which login it handed over; the runtime turns that into the run's `login`, which the cost record keeps and the preflight's probe names in the factory log.
- Decision: the login shell moves to `factory.adapters.agent_launch`, so that the opencode runtime reuses it.
- Reasons: the file is the mechanism the token already uses, so the factory holds no secret; a file for each instance lets one machine mix both logins.

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## What the agent runtimes share lies in one module

Date: 2026-10-19 (F0020-S0002; F0020 decision 4). The opencode runtime starts its runs exactly as the Claude Code runtime does, and every helper for that was private to `factory.adapters.claude_runtime`, so a second runtime would have copied it.

- Decision: the words of a run's start (`sudo`, `timeout`, `env -i`, `factory-confine`), the rules, the removal of the run's folder, the readers of the `sudo:` and `factory-confine:` refusal lines and the resume share move into `factory.adapters.agent_launch`, beside the login. The adding up of a resumed run moves into the domain as `resumed_result` (`factory.domain.agent_runs`).
- Decision: `agent_launch` builds words and texts and imports no process module; each runtime keeps its own process calls. The names earlier tests import from or set on `claude_runtime` stay names of that module, read at the call.
- Reasons: one copy means a change of the start reaches both runtimes; `resumed_result` is a rule on data, so it belongs where the rules are; keeping the process calls in the runtimes leaves `process` the one module that starts processes (R5), and the unchanged tests of the Claude Code runtime prove that it behaves as before.
- Rejected: a base class for the runtimes (they differ in arguments, reply and files, and share only functions); copying the helpers into the opencode runtime (two copies drift).
- Decision (F0039-S0001; F0039 decisions 1 to 3): the reading of a call's end (`read_call_end`: the kill at the limit, then the refusals) and the state-directory error (`state_directory_error`) moved into `agent_launch` too. The process calls stay in each runtime for the reason above. The state directory differs between the runtimes on purpose: the Claude Code runtime creates it, the opencode runtime must find it, because the image creates `/state/runs`.
- Decision (F0039-S0007; F0039 decision 12): the similar code `make duplicates` still finds in the two runtimes is the process calls kept in each runtime by the decision above: the call of `<executable> --version` before `version_printed`, the start of the leftovers program and of the folder removal (`_end_leftovers`, `_remove_temporary_folder`), and the lines of `_call` that call them. They are accepted in `security/duplicates-baseline.txt` for that entry's own reason; their words and readers already lie in `agent_launch`. The reading of a call's end was merged by F0039-S0001.
- The module stays; the wrapper's rules and the `sudo`, `timeout` and `env -i` words left it (F0044-S0001, F0044-S0005), and the leftovers' calls with the leftovers program (F0044-S0003). The runtimes' process calls stay in each runtime.

## A run's output can be streamed by the one process module

Date: 2026-10-19 (F0020-S0003; F0020 decision 5). `run_process` hands a caller the output only when the process has ended. The opencode runtime has no budget flag, so it must add up the cost of each step as the events arrive and stop the run when it passes the budget, and a provider's spend limit may leave a run waiting for input until the stage's `time_limit`.

- Decision: `factory.adapters.process` gains `run_streaming(request, on_line)`. It starts the process as `run_process` does, passes every line of both streams to the callback while the process runs, and kills the process group when the callback returns `True`. `ProcessResult.stopped` says that the callback stopped the run.
- Decision: both functions start the child through one private `_start`, so the module keeps its one `subprocess.Popen(` line, its markers and the searches over the package. `run_process` is unchanged.
- Decision: the lines are read in a selector loop on the calling thread. After a stop or a timeout nothing more is read or passed.
- Reasons: the runtime acts on its output at once, which only a stream allows; one start keeps the isolation (own session, no shell, stdin from `/dev/null`) in one place; a single thread makes "one call at a time" and "no line after a stop" hold without locks.
- Rejected: a separate process module for streaming (a second `Popen` and new markers); reader threads feeding a queue (thread handoff and cleanup for no gain); having the runtime read the pipes itself (it would start processes outside R5).

## opencode's agent is generated per run from the shipped agent files

Date: 2026-10-19 (F0020-S0004; F0020 decisions 6, 7, 8 and 10). The pipeline's rules live in `claude/agents/*.md` and in the installed `settings.json`, written for Claude Code. opencode has its own agent format, tool names and permission syntax, and no flag for a structured reply.

- Decision: the runtime writes a configuration file for each run (`OPENCODE_CONFIG`) with one agent, whose prompt is the agent file's body, whose tools are the agent file's tools in opencode's names, and whose `bash` permission denies the patterns of the `Bash(...)` entries of `settings.json`. The file is removed after the run.
- Decision: the agent must end its last message with a fixed block, and the runtime reads the decision and the entry from it strictly; a missing or malformed block is `no_result`.
- Decision: the cost, tokens, turns, model time and refused calls are read from the `step_finish`, `step_start` and `tool_use` events; a line that does not validate is skipped, not repaired.
- Decision: the run's rules allow opencode's three folders in the agent's home and nothing under `.config`.
- Reasons: the agent files stay the one source of the pipeline's rules, so a change reaches both runtimes and none can drift; a generated file is the only place opencode lets a run define its prompt, tools and permissions; a strict block cannot be satisfied by a reply that merely mentions a decision; an agent that cannot write opencode's configuration folder cannot loosen its own permissions for the next run.
- Rejected: a hand-kept opencode agent file in the repository (a second copy of the rules); reading the decision from free text (guessing a decision); allowing the whole home or `.config` (the agent could rewrite its configuration).

## The project guide is an index and one file per domain

Date: 2026-10-19 (F0025-S0001). `docs/project-guide.md` had grown to 1,905 lines and every agent run reads the guide before it changes anything; the file tool reads 2,000 lines by default. The guide is now the folder `docs/project-guide/`: an index, `README.md`, with what every story needs and the sections the document check reads (*Errors*, *The models' configuration*, *Kill points*, *Fault-injection paths*), and eight files, one domain each (`git-and-hosting.md`, `processes-and-checks.md`, `agents.md`, `write-guard.md`, `work-items.md`, `costs.md`, `stages.md`, `watching.md`). An agent reads the index and then the files of the domains its story touches; the index lists each file with its sections.

- Why: one file for everything cannot grow with F0020 to F0024; a file of about 600 lines or less is read in one call, and a domain is the unit a story touches. A file is split by the same rule before it passes about 600 lines, and the index names the new file.
- A move, not a rewrite: each `## ` section kept its heading and its lines, so the change is checked as a move (every old section in exactly one file, unchanged). The only text changes are the path of the guide in the text and *The document check*. The documenter moved the text with a script, because an agent that writes 1,900 lines out again can change words without noticing.
- The document check reads the index as the project guide, with its sections and table rows, and checks the v1 words and the replaced phrases of every other `.md` file directly in the folder (`is_guide_file`), with *Replaced from v1* exempt; their findings follow the four documents in path order. The engine knows no file of the guide by name beyond the index, and reads no subfolder.
- Rejected: a lasting test of the layout or of a file's length (a documenter who lets a file grow would stall at the check after the docs stage, with nothing in the story to fix; the move is checked once, where it happens); keeping the index at `docs/project-guide.md` beside the folder, or a stub at the old path (two files would name the guide); links between the sections (the guide refers to sections by name, and nothing would check the links).
- The template and the todo demo keep their single `docs/project-guide.md`; the operator guide and this log stay single files.

## A provider's spend limit is its own end reason, and the session is kept

Date: 2026-10-19 (F0020-S0005; F0020 decisions 12 and 13). At the human's work the API gateway limits the spend per model in a rolling window; past it a call returns HTTP 428 with a message. Such a call ended the run `died`, which costs an attempt, and nothing could continue the run.

- Decision: `provider_limit` is an end reason and a stall reason of its own. The limit is recognized by a status (default 428, `FACTORY_PROVIDER_LIMIT_STATUS`) found as a whole number, or by an optional regular expression (`FACTORY_PROVIDER_LIMIT_MESSAGE`), in the error result or standard error of the call and never in the agent's own text. A message that names a wait gives the result's `limit_wait`.
- Decision: every result keeps the `session` of the run, and a request can name a `resume_session`: `claude -p --resume <session>`, `opencode run --session <session>`. The records contract's minor version rises to 1.2 for the added values.
- Reasons: the gateway's exact text is not known here, so the operator sets a pattern rather than the code guessing; the status alone is not enough proof to read from the agent's text, which could mention any number; a limit is not a death of the run, so it needs its own reason for the application layer to wait and continue the same session (a later story) instead of burning an attempt; the session is what makes continuing possible, and both runtimes already hold one.
- Rejected: matching the agent's own output (an agent writing "428" would end its run); treating the limit as `budget` (the budget resume would call the limited gateway at once); a fixed gateway message in the code.

## opencode's budget is kept by the factory while the run streams

Date: 2026-10-19 (F0020-S0006; F0020 decision 11). `claude -p` stops itself at `--max-budget-usd`; `opencode run` has no such flag, and behind the human's gateway a call past the spend limit returns HTTP 428 and plain opencode then waits for someone to type "continue", so a run would spend past its budget or hang until the stage's `time_limit`.

- Decision: the callback of `run_streaming` sums the `cost` of each `step_finish` as it arrives and stops the call when the sum is strictly greater than the call's budget. A budget stop with a known session is resumed once by `--session <id>` with `FINISH_MESSAGE` and `resume_budget` (a quarter, at least $0.50), within what is left of the time limit, as the Claude Code runtime does; the run files live until after the resume.
- Decision: the same callback recognizes the provider limit in an `error` event or a line of standard error and stops the call at once with `provider_limit`; it never reads a limit from `text` or `tool_use` events.
- Reasons: the cost is known only from the events, and only while they stream can the run be stopped before it spends more; reading the end reason from what stopped the call, not again from the output, keeps one rule; the Claude Code runtime's resume gives the agent room to finish with a decision.
- Cost: a run may pass its budget by the cost of one step, since a step is counted when it ends. Only a real run shows how far a real step overshoots.
- Rejected: a budget read after the run (it would spend all of it first), and a wrapper around opencode's own cost report (none is given before the step ends).

## The factory waits out a provider limit around a stage's run

Date: 2026-10-19 (F0020-S0007; F0020 decision 14). After S0005 and S0006 a run that met the provider's spend limit ended `provider_limit` with its session kept, but the stage still stalled it, counted an attempt and asked the human at the cap. At the human's work the limit passes within minutes, and the factory must run unattended.

- Decision: `PatientRuns`, in the application layer around the stage's run (not the preflight's probe, which reports a limit as a failed probe), waits after a `provider_limit` with no agent process running, then resumes the same session with a short continue prompt, the budget left and the time left. The wait is the one the message names, or `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` (default 10). The waits count toward neither the `time_limit` nor the attempts; the run is one cost record.
- Decision: when the waits reach `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` (default 120) the run ends `provider_limit` and the stage stalls with that reason, one attempt counted, its note on the pull request.
- Decision: waiting is the interface `Waiter` (`SleepingWaiter`, `ManualWaiter`), so tests advance a manual clock instead of sleeping.
- Decision: the claim stays held while waiting. The factory renews no lease, so a stage may hold its claim past `lease_duration` (about 180 minutes for the coder against 60), which only another instance on the same repository would act on; one repository has one instance. A stop or restart during a wait is a crash of the factory's own claim: the stage reruns at once and counts toward `crash_cap`, not the attempts. The human's answer of 2026-10-18.
- Reasons: the wait lies in the application layer so both runtimes share it and each only maps its own signal; a stall at the ceiling reaches the human through the usual note, with no new stop to clear.
- Rejected: a machine stop at the ceiling (it would need its own clearing rule, a stop that the next passing probe clears); lease renewal during the wait (not built in v1.1).

## The agent runtime is chosen per instance

Date: 2026-10-19 (F0020-S0008; F0020 decisions 9, 16 and 17). After S0004 to S0007 the opencode runtime existed but nothing built it, the image did not hold opencode, and the preflight checked Claude Code alone.

- Decision: one setting, `FACTORY_AGENT_RUNTIME` (`claude` by default, or `opencode`), chosen for the instance's compose calls; `build_boundaries` builds the runtime and `machine_extras` adds the item `opencode` for it. An instance without the setting is as before.
- Decision: the image installs opencode at a pinned version beside Claude Code and sets the pin and the three Anthropic ids; compose lets the operator replace the executable, the version, the models and the folders per call, each default equal to the image's value.
- Decision: the preflight checks the runtime in force (executable, pin) and, for opencode, a model for every alias the installed agents use. It asks for no API key: an operator's build may log in through single sign-on, which only the probe of a real run can show.
- Decision: `FACTORY_OPENCODE_FOLDERS` names extra folders in the agent's home that a run may write, so a build can keep and refresh its login there; the three folders of opencode stay the default.
- Reasons: the human's work instance runs an operator-built opencode behind single sign-on and this repository's build stays on Claude Code, so the choice cannot be global; one setting keeps an instance on one runtime; a missing model alias would otherwise show only as a failed run.
- Rejected: a runtime chosen per stage or per agent (two logins and two pins on one instance, and nothing needs it); a required API key for opencode (it would refuse the single sign-on build); allowing the whole home to a run (the agent could rewrite its configuration).
- Superseded in part by "A company's provider for opencode": on the machine the agent's home lies on the dataset and the rollback to the base clears it before every stage, so a login kept in the agent's home does not survive and only the API login works; `FACTORY_OPENCODE_FOLDERS` is no longer read.

## factory-watch judges its own instance's claim by the lease

Date: 2026-10-19 (F0026-S0001; F0026 decisions 1 to 4). `factory-watch` showed `event: crash:<work item>` for every stage its own instance was running, story or acceptance, though nothing had crashed. It ran the tick's evaluation as the container's instance, and an own claim is `own`, so a `crash`, whatever its age. The tick never looks while its own stage runs; `factory-watch` is a second process that does.

- Decision: `observed_claim_status` (`factory.domain.lease`, reached through `ClaimService.observed_status`) judges an own claim by its lease: `held` within it, `own` at and past it; every other claim as `claim_status` does. `Watcher` takes `observer` (`False` for the tick, `True` for `factory-watch`) and hands the evaluation the matching status function. The evaluation, the tick, recovery and the board's rows are unchanged.
- Reasons: the tick keeps `claim_status` because a restarted instance must rerun its dead stage at once, not after the lease (R20); the two judgements differ only in an own claim within its lease, so a keyword on `Watcher` is enough. A real crash still shows once the lease has run out, and within the lease the tick handles it at its first look after the restart.
- Cost: a live stage that uses every limit can show as a crash for about a minute past its lease, the margin another instance's `expired` already has. A stage that waits out a provider limit holds its claim past its lease (see the decision on the provider-limit wait), so it shows as a crash while it waits; the factory log's line of the wait tells the two apart.
- Rejected: a sign of life of the tick (heartbeat, lock or process lookup), a new mechanism for a window the tick closes at its first look; showing an own claim always as `held`, which would hide a crash for good.

## A project's agent replaces the shipped one, never extends it

Date: 2026-10-19 (F0022-S0001; F0022 decisions 1 to 6). The agent of a role was only `<agent home>/agents/<role>.md`, filled from the image; a project could not bring its own agent in its repository, only the operator could replace the file outside the project's history.

- Decision: for each role the factory reads `factory/agents/<role>.md` from `origin/main` first, and the installed agent only when the project has no such file. `ProjectAgentDefinitions`, in the application layer over the `Git` and `AgentDefinitionReader` interfaces, is wired in `build_boundaries`; the loader, the composer and the preflight are unchanged.
- Decision: a project agent replaces the installed one whole. Nothing is merged, so a project reads one file and sees the whole agent.
- Decision: the ref is `origin/main`, as for the pipeline definition, so a work item's branch can never change its own agent. `factory/agents/*` becomes the eleventh protected path.
- Decision: the project's file is parsed by the same reader (`parse`, added to `AgentDefinitionReader`) with the same rules, and checked at the same points: the load of every tick and the preflight's probe. A fault names the file and the ref, and the installed agent never stands in for a faulty project file.
- Decision: a project may add a role whose only agent is its own.
- Reasons: one place to read and one set of rules keep a project agent as safe as a shipped one; a fallback on a fault would hide the fault and run an agent the project did not mean.
- Rejected: merging a project file over the shipped one (which keys and which lines win would need a rule of its own); reading the work item's branch (the story could rewrite its own agent).

## The agents load a project's skills, and the agent's home gets none

Date: 2026-10-19 (F0022-S0002; F0022 decisions 7 to 13). No shipped agent could load a skill: each passes its tools to `claude -p` explicitly and none listed `Skill`. v1 delivered its rules as skills; when they were folded into the agent files no story kept the tool, so a project had no way to bring its own know-how.

- Decision: every shipped agent has the `Skill` tool, last in `tools`, and `claude/settings.json` allows it right after `Grep`. A project's skills sit under `.claude/skills/` in its checkout, the work item's branch.
- Decision: rule R15, right after R14 in every agent: a project's skills and agents are the human's files; an agent loads a skill whose description fits; where a skill contradicts the agent's instructions, the instructions win and the entry names the skill and the step set aside. `.claude/*` stays a protected path, and the factory does not check what a skill says.
- Decision: with the tool, Claude Code also loads the user skills and commands of the agent's own Claude home, which a run may write, so one run could plant a skill every later run loads. The entrypoint removes and remakes `skills/` and `commands/` there at every start, empty, owned by the factory and mode `0755`.
- Decision: the opencode runtime refuses a tool it cannot map, which would end every opencode run now. `LEFT_OUT_TOOLS` (`Skill`) is left out instead, in a set beside `TOOL_NAMES`; any other unmapped tool is refused as before. Only Claude Code's runs load skills in this feature.
- Reasons: a skill is a project's way to say how to work, and the instructions winning keeps the pipeline's rules (write paths, no commit, foreground checks) out of a skill's reach; the remade folders close the one route by which a run could change later runs.
- Rejected: a sentinel in `TOOL_NAMES` for the left-out tool (it mixes two kinds of tool and changes the type); checking what a skill says (no check can judge it); leaving the home's folders writable (the planted-skill route).
- Proven: the proof run of 2026-10-19, on the todo demo's own instance (`skills-demo`), gave a project coder's entry that began `project coder:`, and the intake's, tester's and coder's entries ended with the project skill's line `skill: journal-marker`. Once the project's coder was removed from that repository's `main`, the factory's reader gave the shipped coder again. In a container of the same image (`self`), the agent could not make a folder in the home's `skills/`.
- Open: a user `CLAUDE.md` and `.claude.json` in the home stay writable and are read by `claude` (closed on 2026-10-20 by *Every agent run and every project command starts from a fresh agent home*); whether opencode loads skills of its own is not checked; a stage may write a nested `.claude/skills/` inside its write paths (decision 12; for example `src/.claude/skills/`; closed by "No stage writes a .claude folder at any depth"), and whether Claude Code loads it is not known; the proof run did not check it. This entry supersedes "skills" in the open point of the entry dated 2026-10-17 (F0012-S0025).

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## A known result is not checked again

Date: 2026-10-19 (F0023-S0002). After an agent the factory ran every check and report of the stage, though it had run the same command on the same input minutes before; the docs stage's `check` on the coder's unchanged code is the plain case.

- Decision: the factory keeps the result of every check and report a stage runs in `records/known-results.jsonl` in the state directory, under a key: the command, the tree it reads (`work_tree_id` without the command's `not_read`), a digest of the pipeline definition and the image. When the last real run of the key passed, the command is not run again; the result comes back marked as reused, and the reuse is a record too.
- Reasons: the key is what the command reads, not the commit (the checks run before the stage's commit, and every commit carries a new journal entry) and not the stage (a docs stage's `check` on the coder's code is the same input).
- Decision: the project lists what the command does not read (`not_read`), not what it reads. A forgotten path costs one run, never a silenced check.
- Decision: a failed or timed-out result is never reused, and the last real run of a key decides. A flaky test is not hidden by an earlier pass.
- Decision: the store is a record log of its own in the state directory, not new fields on `CommandRecord`. No agent can write there, and `RecordingProjectCommands` sees no key.
- Decision: only the factory's own runs are known. An agent's own `make check` would be the agent's word.
- Rejected: a positive list of the paths a command reads; keying on the commit or the stage; fields on `CommandRecord`; counting an agent's run.

## A mutation run's report is a line of its own, and a partial run is never complete

Date: 2026-10-19 (F0024-S0001; F0024 decisions 2, 3 and 8). Superseded by *The mutants target keeps only its sweep form*, which removes the command and its rules. `make mutants` ended with mutmut's own listing of every survivor in `mutants/`, earlier features' modules included, and no line said how far the run got. The factory reads only the last line, and the acceptance reviewer worked out the score by hand.

- Decision: `python -m factory.entry.check_mutants` reads the text of `mutmut results --all true` and prints the survivors of the named modules only, then one last line that counts every status.
- Decision: a run is partial while a chosen mutant is `not checked` or the recipe stopped mutmut; the last line then says `partial`, and the exit status is 1, never 0. A partial run is not a pass and is not taken for a complete one.
- Decision: `--names` prints the chosen mutants that are not killed, and a pattern `<module>.*` for a module with no mutant, so a later run goes on with what is left by name.
- Decision: the rules are pure functions in `factory.domain.mutants`; the command reads the file through `factory.entry.inputs.read_input`, which `check_duplicates` now uses too.
- Reasons: the last line is the one the factory and the reader see, so it must hold the whole answer; the exit status carries completeness without a new kind of result.
- Rejected: a fourth check status for a partial run (the pipeline's statuses stay passed, failed and timed out); mutmut's own listing as the last line (it holds no count and no word for partial); the survivors of every module in the report (the reader would see other features' survivors and read them as the story's).

## The journal line of a command stopped at its time limit says so

Date: 2026-10-19 (F0024-S0002; F0024 decision 10). A command that reaches its time limit is killed, and its journal line showed whatever it printed last, for example a progress line of mutmut. The records hold `time_limit`, but the reviewer and the human read the journal, and a `mutants` run killed at its 10 minutes read like an ordinary result.

- Decision: `command_line` adds ` (stopped at its time limit after <whole seconds> s)` to the line of a `time_limit` result; the seconds are rounded down. A passed line, a reused line and a failed line stay as they are.
- Reasons: a green check is never `time_limit` and a red one stalls with its tail, so in practice only a report shows the note; no new status and no new record field are needed.
- Rejected: the suffix for failed results too (a failed report's own last line already says what it is, and `tests/application/test_stage_finish.py` pins one); a gentler stop in the process module (it would change how every command ends for the sake of one line).

## Mutation testing per story

Date: 2026-10-19 (F0024-S0003; superseded by *Mutation testing runs only as sweeps outside the factory*; F0024 decisions 1, 2, 4 to 7 and 13). This supersedes *Mutation testing is limited to one feature's modules*. `make mutants` ran only at a feature's acceptance, inside the agent's run, and a large feature ended partial in every run (F0021: 2,806 of about 5,750 mutants in three runs). Now the factory runs it as a report after the coder, the reviewer reads the survivors while the story is open, and the acceptance re-runs what the stories left.

- Decision (1): on a story's branch the `Makefile` takes the modules the branch changes against `origin/main`, the work tree and untracked modules included. The engine knows neither the target nor the branch form.
- Decision (2): a story's run takes every mutant of its modules by pattern. An acceptance's run, with `FEATURE` or on its branch, takes by name only the mutants that are not killed, and a module with no mutant yet by its pattern. mutmut 3.8 runs again every mutant a name selects, so a stopped run reaches the same mutants every time; only a list that loses its kills goes on.
- Decision (4): the recipe stops mutmut after 540 s inside the report's 10 minutes. The factory's KILL runs no `EXIT` trap and does not reach mutmut (since F0030-S0001 the factory's kill reaches mutmut; see *A command stopped at its time limit loses every process of its session*), so the recipe's own stop bounds the run, and the 60 s left are for the results, the last line and the trap.
- Decision (5): the leases stay. The room for the report's 10 minutes comes from `check` (15 to 8) and `duplicates` (5 to 2), whose measured maxima are 91.4 s and 4.6 s.
- Decision (6): the reviewer reads the survivors from mutmut's own results in `mutants/`, not from the journal, which holds only the last line. A survivor in a line the story added or changed that breaks a rule of the work item is a finding; an equivalent survivor, a message text, a line the story did not change and a partial line are notes for the acceptance. The acceptance runs the report again while it is partial, at most three runs, and tells the survivors the reviews passed on from new ones.
- Decision (7): a complete result is a known result like any report and is reused; a partial one exits 1, is never reused and runs again. `mutants` has no `not_read`.
- Decision (13): `mutants/` belongs to two users of one group, so the `EXIT` trap runs `chmod -R g+w mutants`. A run killed by the factory skips the trap, and the next run of the other user fails with `Permission denied`; the operator repairs it with `chmod -R g+w` as root.
- Rejected: running only the changed functions (mutmut resets their results while it runs, after the names are chosen); every unchecked mutant of the package (about 10,000); a longer lease; the report's whole output in the journal (a long list in every coder entry) or in a file of the factory's; a gentler stop (TERM before KILL) in the process module (all commands would be affected).

## Mutation testing runs only as sweeps outside the factory

Date: 2026-10-19 (F0031-S0001; the human's decision of 2026-10-19). This supersedes *Mutation testing per story*. No stage and no agent runs `make mutants` or mutmut: the shipped acceptance reviewer's check 3 says `By sweep, not run here.`, the reviewer no longer reads a mutation report, and the template's `CLAUDE.md` and `Makefile` name the target as a sweep by hand.

- Why: every acceptance of 2026-10-19 ran `make mutants` one to four times at up to 540 s each, and every large feature still ended partial (F0019 to F0023). A sweep in idle time, on a fresh copy, needs neither a stage's time limit nor a `mutants/` shared by two users.
- Decision: sweeps start with a fresh `mutants/` in a throwaway container. The `mutants` target and `factory.entry.check_mutants` stay for them. *The mutants target keeps only its sweep form* removes `factory.entry.check_mutants`; the target stays.
- Rejected: a longer limit for the acceptance; the report after the coder (taken out the same day); check 3 dropped and the checks renumbered, because the eight report sections, check 7's pinned start and the reports already written keep their numbers.

## The mutants target keeps only its sweep form

Date: 2026-10-20 (F0032-S0001; F0032 decisions 1 to 7; the human's decisions of 2026-10-19). This supersedes the story-branch form and the report of *Mutation testing per story* and *A mutation run's report is a line of its own, and a partial run is never complete*. Mutation testing runs only as sweeps outside the factory, with `mutants/` made anew for every run.

- Decision: the recipe removes `mutants/` with `rm -rf mutants` before mutmut starts. mutmut then makes it anew, copies the other files under `src/` afresh and runs its stats again.
- Decision: the modules come from `MODULES` (dotted modules or packages, each run by `<name>.*`) or from `FEATURE`; `MODULES` wins. There is no story-branch form.
- Decision: no stop unless asked. `MUTANTS_SECONDS` is empty by default; a given value stops mutmut by `timeout` and fails the run with `mutants: stopped after <n> s, ...`.
- Decision: `MUTANTS_CHILDREN` passes `--max-children`, because mutmut's default is every core the machine reports, also in a container limited to fewer.
- Decision: `factory.entry.check_mutants` and `factory.domain.mutants` are removed with their tests. `factory.entry.inputs` stays: `check_duplicates` reads its files through it.
- Reasons: the human decided on 2026-10-19 that nothing is kept between runs and that no stage runs mutation testing. A fresh `mutants/` leaves the command no job: there are no survivors of earlier runs to filter out, the rerun list is every module's pattern, and no stage reads `partial` any more; a stopped run says so in its own line, and mutmut's own listing, without the `not checked` lines, is this run's survivors.
- Rejected: keeping `check_mutants` for its summary line (it would need to match packages, and its `--names` would be dead); refusing a run while `mutants/` exists (a forgotten folder would stop a night's sweep with nothing done); 540 s as the default stop (it came from an agent's shell limit that no longer applies; the sweeps used 5,400 to 9,400 s).

## opencode's configuration folder is made by the image, read-only to the agent

Date: 2026-10-20 (F0029-S0001). opencode 1.19.3 makes `~/.config/opencode` on its first run. The write guard refuses that `mkdir`, so in every new container of an instance on opencode (the agent's home outside `.claude` is no volume) the first preflight probe ended `died` and the instance stopped.

- Decision: `image/Dockerfile` makes `/home/agent/.config/opencode`, owned by `factory:factory-work`, mode `0755`, and leaves `/home/agent/.config` to `agent:factory-work`, mode `0755`. The agent cannot write the folder, and still makes folders under `.config` (`FACTORY_OPENCODE_FOLDERS`, such as `.config/sso-opencode`). `RUNTIME_FOLDERS`, the run's rules and the entrypoint stay as they are.
- Reasons: the folder must exist, but a run must not write it: opencode reads `opencode.jsonc` there on every run, beside `OPENCODE_CONFIG`, so a writable folder would let one run change what the next run is told.
- Rejected: `.config/opencode` in `RUNTIME_FOLDERS` (one run could change what the next run is told); the entrypoint making it (it runs as `factory`, could make it only through `sudo -u agent` as an agent-owned folder, and at every start); `XDG_CONFIG_HOME` in the run's temporary folder (it moves every tool's configuration and an operator's single sign-on login).

Replaced by the machine of v1.2 (`vm/`), F0044-S0010.

## The tests set their own umask, and uv syncs under the caller's

Date: 2026-10-20 (F0033-S0001; F0033 decisions 1 and 2). On 2026-10-19 an agent's run, as `agent`, left `factory-0.1.0.dist-info` in `.venv` as `drwxr-sr-x` with `-rw-r--r--` files. `make test` ran `umask 022` before `uv run pytest`, and `uv run` syncs `.venv` first, so the reinstall ran under `022` as well. The factory's next `make lint`, as `factory`, could not remove the folder, and the instance stopped with `main_branch_failing`. The reverse failed too: the factory's own `make test` left `.venv` with factory-owned `644` files that an agent's `uv run` could not replace.

- Decision: `pytest_configure` in `tests/conftest.py` sets the process umask to `0o022` (`TESTS_UMASK`) for every pytest run, whatever umask it started under. The tests' checkouts stay not group-writable, as the seal requires, and a module run alone with `uv run pytest <module>` gets the same umask as `make test`.
- Decision: the `Makefile`'s `test` recipe sets no umask, so uv syncs `.venv` under the caller's umask: `002` in the container and under `sudo`. `make mutants` keeps its `umask 022`.
- Rejected: `UV_NO_SYNC` for agents (an agent's `make check` after a dependency change would test a stale environment); a repair of modes after every agent call (it fixes the symptom, needs a new step as `agent`, and misses the factory's own `644` files); a shell wrapper in the recipe, `uv run sh -c 'umask 022; exec pytest ...'` (a test module run on its own with `uv run pytest <module>` would not get the tests' umask, and the hook in `tests/conftest.py` makes the `Makefile` simpler).

Replaced by the dataset's rollback, v1.2 F0044-S0006.

## No stage writes a .claude folder at any depth

Date: 2026-10-20 (F0036-S0001; F0036 decisions 1, 2 and 4). `PROTECTED_PATHS` held `.claude/*`, which protects the repository's root `.claude/` only. F0022's decision 12 left a nested `.claude/` open, and its acceptance walked the guard and found `src/.claude/skills/x/SKILL.md -> allowed` under the write path `src/*`. On 2026-10-19 the human decided that no agent writes any `.claude/` folder, at any depth.

- Decision: `PROTECTED_PATHS` gains `*/.claude/*` right after `.claude/*`, twelve patterns in all. `refusal` refuses a nested `.claude/` with the text it gives the root one, also when a write path matches. The Claude Code hook and the undo after every run both judge a path through `refusal`, so neither changed and both refuse a nested `.claude/` now. A segment that only contains `.claude` (`.claudex`, `x.claude`), `claude/` without the dot and a path that only ends in `.claude` stay as they were.
- Decision: the kernel's targets stay as they are. Where a write path opens a folder, the kernel allows the nested `.claude/` and the undo removes what the agent wrote.
- Reasons: the human's decision of 2026-10-19, and F0022's decision 12 with its acceptance's guard walk, which showed the gap.
- Rejected: a Landlock rule (Landlock only allows, it cannot exclude a folder beneath an allowed one); a rewording of R14 (the rule already names `.claude/`, the pattern list was too narrow).
- The hook, the kernel's rules and the undo this entry names went (F0044-S0002, F0044-S0009); the take keeps the rule: a nested `.claude/` is refused, and left out of the work tree.

## The reviewer corrects a stale Description

Date: 2026-10-20 (F0034-S0001; F0034 decisions 1 to 3). A story's `## Description` can go stale against what the story built, and until now no later stage could fix it. F0019-S0003's reviewer asked the human. F0026-S0002's coder was refused the work item and asked. F0025-S0002 went to `done/` with "Three smaller passages" above a list of two, although four stages noted it.

- Decision: the shipped reviewer (`claude/agents/reviewer.md`, *Role*) rewrites the stale sentences of the Description itself when the human's answers in the journal, the Interface or the criteria already settle what they should say, and changes nothing else in the work item. It names each correction in its entry as `description corrected: <what it said> -> <what it says now>`. A correction is not a finding, so with no other finding the reviewer ends with `docs`. A Description the code contradicts while nothing settles which is right stays a finding, or a question when no stage can fix it. The work item was already in the reviewer's write paths; no other agent and nothing under `src/` changed.
- Reasons: the human's decision of 2026-10-19, and the stale Descriptions of F0019-S0003, F0025-S0002 and F0026-S0002.
- Rejected: giving the coder the work item (a second writer of the story's text); leaving it to the human (a question about nothing the human decides).

## A smoke test passes no -q that the pytest configuration already sets

Date: 2026-10-20 (F0035-S0001; F0035 decisions 1 to 4). This repository's `pyproject.toml` sets `addopts = "-q --strict-markers"`. A smoke test command that passes `-q` again runs pytest at `-qq`, which prints no summary line. On 2026-10-19 that alone failed the smoke tests of F0022-S0005 and F0023-S0004, with every test green, and cost a question each.

- Decision: intake's *Stage* step 2 (`claude/agents/intake.md`) gains the rule beside its check that the smoke test commands are runnable: a command that runs pytest passes no `-q` when the project's pytest configuration already sets one (`addopts` in `pyproject.toml`, `pytest.ini`, `setup.cfg` or `tox.ini`), and a command that does is a question. The rule is general, because the shipped intake serves every project. No other agent carries it.
- Decision: this repository's `factory/story-form.md` holds the same rule in this project's words, naming `pyproject.toml` (the human's change). `template/` is unchanged: it ships no pytest configuration and no story form.
- Reasons: the smoke tests of F0022-S0005 and F0023-S0004 on 2026-10-19; a question at intake costs nothing against a smoke test run paid for twice.
- Rejected: a check in code (`factory-check-story`; the factory knows no pytest, and a project's pytest configuration is the project's own); a line in intake's *Lessons* (`tests/test_claude_agent_texts.py` pins those lines exactly, and that would change another story's test).

## A record line that is not UTF-8 is skipped

Date: 2026-10-20 (F0037-S0001; F0037 decisions 1, 2, 3, 4 and 5). A kill during an append can cut the last line of a record file inside a multibyte character. `JsonLinesRecordLog.read` decoded the whole file, so it raised `UnicodeDecodeError`, and `KnownResults._read` caught only `OSError`: every check and report of every stage failed with an error until a human repaired `known-results.jsonl`.

- Decision: `JsonLinesRecordLog.read` reads the file's bytes, splits them at `b"\n"` alone and decodes each line on its own as strict UTF-8. A line that does not decode is skipped, like a blank line and a line that does not validate; every other line counts, in file order. Splitting at the line feed alone also keeps whole a record whose text holds U+2028, U+2029 or U+0085, which `str.splitlines` cut in two. An `OSError` of reading still propagates. `KnownResults`, `DiskRecorder` and `StopPublisher` are unchanged.
- Reasons: the fault is in the reader of the file, which serves all four record files, so one fix covers them.
- Rejected: a wider `except` in `KnownResults._read` (decision 2; it would fix one of the four callers and hide other faults); decoding with replacement (decision 3; a line cut or damaged inside a JSON string could then validate as a record with a wrong text).
- Answered (decision 4, the human, 2026-10-20): a record appended after a torn line still lands on the torn line's line and is skipped with it, and no later feature changes `append`. Reason: the writer would have to read the file's last byte before each append, which two writers can race, while the loss is one telemetry record per kill.

## A test whose child must act before its time limit gets ten seconds

Date: 2026-10-20 (F0029-S0002). `test_the_temporary_folder_is_empty_at_each_call_and_gone_after_the_run[time-limit]` failed under a loaded `make check` on 2026-10-19: its limit of 3 s killed the probe, which starts through `factory-confine` and then a Python stand-in, before the probe wrote its call record. Seventeen more tests give a child that must act before the kill one to five seconds.

- Decision: `tests/time_limits.py` holds `ROOMY_LIMIT` (ten seconds) and `ROOMY_BOUND_SECONDS` (25, the upper bound on the elapsed time of a run that `ROOMY_LIMIT` ends). Every test whose child must act before its limit (write a record or a pid file, print a line, finish a first call) uses them; a child that need not start to be killed keeps a shorter limit. The bound stays below every wait of the stand-ins the limit must end (30 or 60 s), so a missed kill fails.
- Reasons: three seconds failed under load; a runtime's kill is measured from its own start, so a killed run still ends near the limit.
- Rejected: waiting for the child's record before the limit counts (the limit is the runtime's own); five seconds (barely more than the three that failed); changing the shipped tester lesson now (the ten seconds are this repository's measure).

## A command stopped at its time limit loses every process of its session

Date: 2026-10-20 (F0030-S0001). This corrects F0024 decision 4 ("the factory waits until `timeout` ends it"). F0024's acceptance (section 2) saw `MakeProjectCommands.run("mutants")` return `time_limit` after 3 s while `timeout`, `uv run mutmut run` and mutmut's Python went on, writing `mutants/`.

- Decision: at a time limit, at a callback's stop and at a callback's error, `factory.adapters.process._kill_session` kills the child's process group and then, in rounds, every process of the child's session that the factory may signal, and returns only when none is left. The pure rules (reading one `/proc/<pid>/stat` line, choosing what is left) are `factory.domain.sessions`. A process that called `setsid` is outside the rule. A test that mutmut runs can start such a process, because `factory.adapters.process` starts every command with `start_new_session`, and that process ends by itself (seen on 2026-10-20 in the real check with mutmut, which answers F0030's decision 14). Another user's process (root's `sudo`, the agent's under `sudo`) is left to the agent's own `timeout` and not waited for.
- Reasons: `timeout` moves mutmut into a group of its own, and the factory waited only for its child and its pipe; mutmut writes into `tee`'s pipe, not the factory's. A session survives a new group and a dead parent, which a walk of parent ids does not.
- Rejected: `timeout --foreground` in the recipe alone (it mends one recipe, and every other project command keeps the fault); a cgroup per command (not available to the factory's user under rootless Podman); the factory as subreaper (`PR_SET_CHILD_SUBREAPER`: it would reap every orphan of every run); a time limit of the rounds' own (no process outlives SIGKILL except in the kernel, and that would hold the call already).

The process group is killed; no agent code runs on the host since v1.2, F0044-S0010.

## The Claude Code hook is removed; the kernel and the undo are the write guard

Date: 2026-10-20 (F0041-S0003; the feature's decisions 2, 3, 5 and 6 and F0019's decision 16). The Claude Code hook `factory-guard` is no longer registered (S0001), and its command, its adapter, `GUARD_COMMAND`, `GuardSettings.temporary_directory` and the preflight's search for it are removed (S0002). Every agent run, under either runtime, is guarded by the kernel (`factory-confine`, Landlock) during the run and by the undo after it. Nothing judges a tool call.

- Decision: a protected path inside a folder a write path opens is written and then reverted by the undo, since the kernel cannot exclude a path beneath an allowed folder (the feature's decision 6). The undo judges the exact write paths; the tool paths widen what the kernel allows only.
- Reasons: the cross-check of 2026-10-19 compared 405 transcripts and found no refusal by the hook in the 264 runs after the kernel guard went live; its one disagreement was fixed by F0019-S0011. The hook saw two tools only (`Edit` and `Write`), while the kernel refuses a write by any route. The opencode runs had no hook already, so the hook was a second code path for one runtime.
- Rejected: a reduced hook for the protected paths only (it keeps the command, its settings file and the `PATH` requirement for a rule the undo already enforces).
- Replaced in v1.2: the kernel's guard went with the wrapper in F0044-S0002 and the undo in F0044-S0009; the dataset's rollback and the take are the one boundary, and nothing judges a tool call, as before.

## A run's leftover processes are ended by a program that runs as the agent

Date: 2026-10-20 (F0027-S0001; the feature's decisions 8 to 10). A process that an agent run starts in a new session survives the end of the call and the kill of the run's process group, and goes on writing while later stages run, are undone and are checked. `_kill_session` (F0030-S0001) does not reach it: it is in another session.

- Decision: `python -I -m factory.entry.leftovers --user <name>` sends SIGKILL with `kill(-1)` and reads the process table until no other process of its user is left (not counting zombies and dead entries), in at most 50 rounds 0.1 s apart. It refuses to run as root and refuses unless it runs as the user `--user` names, both before its first signal. `own_identity` and `signal_every_other` are in `factory.adapters.process`, the one module that touches processes. No test calls the real signal and none runs the program as the user it names.
- Reasons: the agent's own user is the only boundary that holds the leftovers and nothing else; `kill(-1)` reaches them wherever their session, group or parent is, and spares the program. As root, or as a user a stand-in `sudo` did not switch, the same call would end the container or the factory, so the program refuses first. A test that ran it as its own user would end the run that runs it.
- Reuse: it reads the table through F0030-S0001's `ProcessEntry` and `read_process_table` (now public, sorted, with `uid` added) and not through a second reading of `/proc` (the human, 2026-10-20). The owner is the folder's, since a process that makes itself not dumpable gets root-owned files under its folder.
- Rejected: waiting with `kill -0 -1` (Linux counts a target the caller may not signal as found, so it never settles).
- Replaced by the end of the call's container, v1.2 F0044-S0003.

## Every agent call is followed by the end of the agent's leftover processes

Date: 2026-10-20 (F0027-S0002; the feature's decisions 10 to 12). S0001 built the program that ends every other process of the agent's user; this story makes both runtimes start it. It closes the window F0014 decision 21 left open: a process that swapped `.git` after the seal's check.

- Decision: after every call of a run with an operating-system user other than the factory's own, the runtime starts the program through the one `sudo` rule, from `/`, with an empty environment and a 30-second limit, inside `AgentRuntime.run`. It runs before the run's temporary folder is removed, and so before the seal's check, the removal of nested repositories, the undo and the checks. A resumed run runs it after each of its two calls, and it runs also after a call that `sudo`, the wrapper or the login shell refused. A runtime starts it only when built with the command (`leftovers`); `build_boundaries` builds it so by default (`end_leftovers=True`).
- Decision: when the program fails or does not end in time, the run raises `AgentRuntimeError` (`cannot end the agent's processes: <line>`), after the removal. The call's own refusal wins when there is one.
- Reasons: nothing the factory cannot vouch for may reach the undo and the checks, so a failure is an error and not a stall. Running it inside the runtime leaves no window between the call and the program. Never when the user is the factory's own: in an agent's `make test` that user is `agent`, and the program would end the run itself. A runtime a test builds has no command, so earlier runtime tests keep their calls.
- Rejected: running it from the stage code after `agent_runtime.run` (a window in which a process can still write); ignoring a failure (the checks would run on a tree the factory cannot vouch for).
- Replaced by the end of the call's container, v1.2 F0044-S0003.

## The factory removes the git-ignored paths after every agent run and at the restore

Date: 2026-10-20 (F0027-S0003; the feature's decisions 2 and 4 to 7). Nothing removed the git-ignored state of the checkout: the undo does not see it, the result commit does not hold it, and the restore's `git clean -f -d` keeps it. Whatever an agent left in `.venv`, `__pycache__`, a tool cache or behind a nested `.gitignore` reached every later `make check`, unseen in the pull request.

- Decision: `Git.remove_ignored()` (`git clean --quiet --force --force -d -X`) removes every untracked path the ignore rules match, folders whole. `run_sealed` calls it after the seal's check and the removal of nested repositories, only when the run returned; the tick's restore calls it after `reset_to("HEAD")` and before the switch to `main`. A path it cannot remove is a `GitError`, in the restore the stop `checkout_restore_failed`.
- Reasons: the call in `run_sealed` comes before the undo and the same stage's checks, and after the preflight's probe run, so no check reads what the agent hid. The restore removes a crashed stage's state, and it runs before the switch because a branch's own `.gitignore` names what it hid only while that branch is checked out. The second `--force` is needed for an ignored folder that holds a repository. The checks build what they need again (`uv run` creates `.venv` from `uv.lock`), which costs one download after an image rebuild. The removal runs in the factory's own code and not in `finally`, so a second git error cannot hide the run's own error, and a raised run is cleaned by the next restore.
- Rejected: keeping some ignored folder (no ignored folder is kept: mutation testing runs only as sweeps outside the factory, and `make mutants` makes `mutants/` anew each time); removing the paths from Python, as for nested repositories (git's own rules, nested `.gitignore` files and `.git/info/exclude` included, are the ones that count); changing `reset_to`, the undo or the result commit.
- Accepted: an agent can un-ignore a path inside its write paths (F0027 decision 7), and no rule is added against it. A nested `.gitignore` there with a negated rule (`!__pycache__/` in `src/`) makes a `.pyc` untracked and not ignored, so `remove_ignored()` keeps it. Nothing is hidden by that: the path is committed with the result and shows in the pull request's diff, where the reviewer and the human see it, and the undo removes it when it lies outside the stage's write paths. Inside the tool paths no `.gitignore` takes effect, because git does not read the rules of an ignored folder. An agent cannot write the root `.gitignore` or `.git/info/exclude`: the kernel's rules and the seal refuse it. A later story that finds an un-ignored file in a diff should not add a rule for it without asking.
- Test children (F0027-S0004): the tests' shared helpers (`write_script` in `tests/confine_support.py`, `python_argv` in `tests/process_support.py`) and every script the tests write for their own interpreter start it with `-B`, and `tests/test_test_children.py` scans `tests/` so that a shebang `#!{sys.executable}` without the flag fails. The tests run under umask `022`, so a bytecode folder a test child writes during an agent's `make check` is one the factory's removal cannot remove; that stopped F0027's acceptance twice on 2026-10-20.
- Seen on 2026-10-20: F0027's acceptance ran `make check` as `agent` and left `.venv/lib/python3.12/site-packages/__pycache__/` as `drwxr-sr-x`. The removal after the run raised `GitError`, the stage ended without a result, and it crashed twice (the second run hit the same folder) up to `crash_cap`. The human's quick fix is `export UV_COMPILE_BYTECODE := 1` in the `Makefile` (fd0fcd0b): uv writes `.venv`'s bytecode at its sync, group-writable, so the test children find it there and write none. It hides the cause and does not remove it: a child without `-B` still writes bytecode under the tests' umask `022` for a module that has none, and the test helpers' `-B` (S0004) removes the cause. The answer lies in how the files are written and not in a later repair: a fix of modes after every agent call was rejected (*The tests set their own umask, and uv syncs under the caller's*), so what an agent's commands write must be group-writable from the start.

Replaced by the dataset's rollback, v1.2 F0044-S0006.

## The project commands run as the agent user, with the git folder sealed

Date: 2026-10-20 (F0040-S0002; the feature's decisions 1 to 7). It replaces *The project commands first ran as the factory's user; replaced*. `make check`, `lint`, `test` and the other project commands ran code that agents wrote as `factory`, who can read the token file, and a test could print the token into the output tail the factory writes into the journal.

- Decision: with `FACTORY_AGENT_USER` set, `build_boundaries` builds the make class with a `CommandUser` for that user, the `sudo` the preflight checks, the agent run's environment plus `PYTHONDONTWRITEBYTECODE=1` and `UV_LINK_MODE=copy`, and the leftovers program. Every command of the instance, the preflight's `lint` on `main` included, then runs as `agent`. `SealedProjectCommands` seals the git folder before each command and checks the seal and removes nested repositories after it.
- Reasons: the user, not a filter on the output, closes the route: `agent` cannot enter the token's folder, so there is nothing to print. The seal is needed because the factory's own git writes group-writable files into `.git` between an agent run and its checks (the undo, the commit), and a command running as `agent` must find `.git` the factory's alone. The commands use the agent run's environment so that they see no more than an agent does, with no bytecode written (see the 2026-10-20 note under *The factory removes the git-ignored paths after every agent run and at the restore*) and `uv` copying.
- Left: the agent's own login files are readable by `agent` by design, so a test can still print the agent's login into the output tail. Clearing the agent's home before each command came with F0040-S0004.
- Rejected: a second implementation of the seal beside `run_sealed` was kept small instead of shared, because only the three git calls would be common (`run_sealed` also calls `remove_ignored` and builds a `SealedRun`).

Replaced by the throwaway container, v1.2 F0044-S0005.

## A call stops reading five seconds after its own process ended

Date: 2026-10-20 (F0040-S0005; the feature's decision 17). `run_process` read until both pipes closed and, after its kill, read again without a limit. A process that left the killed group and kept a pipe open held the call until it ended by itself: on 2026-10-20 a `sudo` call killed by its inner `timeout` at 3 seconds returned at 12 seconds. Under `sudo` no kill reaches such a process (the agent's `timeout` kills its own group, and the factory's kill leaves out what it may not signal), and once the project commands run as `agent` (S0002) that holds every check.

- Decision: `factory.adapters.process` notices the child's end while it reads and reads on for at most `PIPE_DRAIN` (5 seconds). Then it stops reading, closes the pipes and returns the child's own exit status, what it read. After its kill at the time limit, `run_process` reads for at most the same 5 seconds. A call whose pipes close in time is unchanged, and no caller changed.
- Reasons: the human chose it (answer B, against the pre-check's recommendation to leave it as a known limit). The rule is the module's, for every call: one rule is simpler than a switch, and no caller needs the old wait. A call under `sudo` now ends at most 5 seconds after its inner kill, and one that ended on its own keeps its real result. The end is detected with `os.waitid(..., WNOWAIT)` and not `poll()`, which would reap the child: a limit during the drain would then signal a process group id that an unrelated process could hold.
- Left: the holder is not killed by this module; the leftovers program after the call ends it. A line it writes after the drain is lost.
- Rejected: leaving it as a known limit; keeping `communicate()` with a timeout loop (it cannot notice the child's end while a pipe stays open).
- The `sudo` chain and the leftovers program this entry names went with F0044-S0005 and F0044-S0003; the rule stays in `factory.adapters.process`, for every call.
- The field `output_abandoned`, which no caller read, went with v1.2 F0045-S0007; the drain stays.

## Every agent run and every project command starts from a fresh agent home

Date: 2026-10-20 (F0040-S0004; the feature's decisions 8 to 13). It closes the sentence on the agent's writable home (L69) in *The agent is started through `sudo -n -u agent -- env -i`, and a run's files are `0640`*. The agent's home kept everything every run left there: transcripts, opencode's sessions, caches, and any file Claude Code reads on every later run (a user `CLAUDE.md`, a `rules/` folder). One run could so steer or read all later ones.

- Decision: `AgentHome.reset()` (`SudoAgentHome`) runs `factory.entry.fresh_home` as the agent's user through `sudo -n -u <agent> -- timeout --signal=KILL 60s env -i <python> -I -B -m ...` from `/`. `run_sealed` calls it after the seal, before the run, once per stage run; `SealedProjectCommands` calls it after the seal, before each command. The preflight's probe is reset like any run. It keeps the two mounted login files, the login each runtime keeps in the home (`.claude/.credentials.json`, `.local/share/opencode/auth.json`), the folders of `FACTORY_OPENCODE_FOLDERS` and uv's package cache `.cache/uv`. Without an agent user nothing is reset.
- Reasons: the program removes only what the agent's user owns, so the factory's own files stay without a list of them. Once per stage run, because a resume after a provider limit or the budget must keep its session. A failed reset raises before anything starts, so no run or check runs in a home the factory could not clear; at a stage that is an error, at the preflight `preflight_failed`. Clearing before the run, not after, leaves the last transcript for the operator to read. `-B` because `-I` ignores `PYTHONDONTWRITEBYTECODE` and bytecode beside the factory's source cannot be removed by the restore.
- Left: the kept uv cache is written by runs and commands and read by every later one, a small channel from a run to the next check that the human accepted (the feature's decision 9). The first reset after the upgrade removes what the volume `claude-home` gathered (on `self`, about 222 MB).
- Replaced by the dataset's rollback, v1.2 F0044-S0004.

## The work tree's id copies the index with its timestamps

Date: 2026-10-20 (F0030-S0002). `GitCli.work_tree_id` copied the checkout's index into its temporary index with `shutil.copyfile`, so the copy got the time of the copy as its modification time. Git trusts a file's cached stat data only when the file's modification time is older than the index's ("racily clean" otherwise, and it rehashes). With the copy's new time that guard was gone: a tracked file changed to the same size within the timestamp tick of the last index write kept matching stat data, and the id named the tree before the change.

- Decision: the temporary index is copied with `shutil.copy2`, keeping the index's modification time, so the racily-clean rule applies to the copy as it does to the own index. Nothing else in `work_tree_id` changed.
- Cause: `test_the_work_tree_id_is_the_tree_a_commit_records[tracked-ignored-file]` failed once under `make check` (F0030-S0001), and F0030's acceptance reproduced it with plain git: `copyfile` wrote the old tree, `copy2` the tree of the commit. A stale id is the key of a known result (F0023), so it could let the factory reuse a passed check for a tree that changed. `tests/adapters/test_git_cli_work_tree_tick.py` makes the race certain (`core.trustctime false`, one fixed modification time for the file and the index).
- Rejected: a fresh index filled by `git read-tree HEAD` (it would rehash every file on every call); `git update-index --really-refresh` on the copy (it rehashes every file as well).

## v2 is retired; nothing is left for v2

Date: 2026-10-21 (F0038-S0009).

- Decision: on 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009): v1.1 evolves, and nothing is left for a v2. Of the gaps the log and the guides left for v2, four are closed: the project commands ran as the factory's user (*The project commands run as the agent user, with the git folder sealed*), the agent's writable home (*Every agent run and every project command starts from a fresh agent home*), the git-ignored paths the undo did not see (*The factory removes the git-ignored paths after every agent run and at the restore*), and the guard's reading of a hook payload it cannot read, which went with the hook (*The Claude Code hook is removed; the kernel and the undo are the write guard*). One is open and not planned: the checkout's seal does not cover the clone's working folder (the checkout's parent) or the process environment `GitCli` passes on first (*The factory alone writes the checkout's `.git`*).
- Why: a gap named "left for v2" reads as planned work, and no v2 will come.
- Open: whether the open gap becomes v1.1 backlog is the human's decision.
- Rejected: keeping "left for v2" in the documents.

## One snapshot instead of many layers

Date: 2026-10-24 (F0042-S0005; the design is `planning/v1.2-plan.md`, the human's answers of the same day). v1.1 runs a stage in one long-lived container and protects the factory from the agent with many layers: a second user with `sudo`, a umask and a group, a sealed git folder, the kernel's write guard, the undo, the removal of ignored files and nested repositories, the end of leftover processes, the fresh agent home. The stops of the night of 2026-10-20 came from those layers meeting each other.

- Decision: v1.2 replaces the layers with one mechanism. The factory runs on a Linux VM with ZFS. A stage works on one ZFS dataset (a full clone with its `.venv`, the caches and the agent's home), brought up to date by a pull and the project's sync, and one base snapshot is moved forward to that state. Each step (the sync, the agent, every check) runs in a throwaway Podman container that mounts the dataset. The factory then takes from the dataset only what the role may write, and commits and pushes it with its own token. Everything else the container did dies with it, and the dataset is rolled back to the base.
- The human's decisions of 2026-10-24, one sentence each:
  1. The factory runs directly on the VM as a systemd service under `factory`, with rootless Podman and `zfs allow`.
  2. The factory on the host pushes, from the files it takes; no container holds the hosting token.
  3. `zfs allow` first, and one `sudoers` line for the four `zfs` commands that need root on the one dataset if the rollback needs it.
  4. Landlock goes with the other layers.
  5. The dataset holds a full clone, fetched from the host's repository through a read-only mount.
  6. The machine's files live in a new top-level `vm/`, added to the coder's write paths.
  7. One `Snapshots` adapter in v1.2, ZFS; the interface leaves room for another.
  8. The instance on the VM is `vm`, on an `e2-standard-2` in `europe-west3`, with a budget alert of $120 a month.
  9. The build order is add, switch, remove: F0042 and F0043 by `self` on Docker with the inline fallback, the first VM stage, then F0044 and F0045 by `vm`.
- What the take keeps from the undo: the refusal rule of the write paths applied the other way round (a path the role may not write stays out of the work tree and is named); the in-progress rule (a path directly in another work item's `in-progress/` folder is refused); the work item's restore (state and journal put back from the stage-start commit, the agent's edits to its sections kept); the journal's closing paragraph over the paths left. The restore is the undo's `restore_state_and_journal`, shared. The take reads the baseline first and raises `WorkItemFormatError` before it changes anything, as the undo does.
- The seam: the stage protocol calls `StageEnvironment` (`prepare`, `run_agent`, `take`), and no longer `run_sealed` or `UndoService`. `InlineEnvironment` is v1.1's way behind the interface and is the second implementation beside F0042-S0007's `ContainerEnvironment`, until F0044 removes it with the layers it uses. A stall takes through the environment too.
- The journal sentence stays `The factory undid changes outside the write paths: ...` until F0044 (decision 9 of the feature F0042). Since F0044-S0009 it is `The factory left out changes outside the write paths: ...`.
- The inline environment and its setting `FACTORY_STAGE_ENVIRONMENT` went with v1.2, in F0044-S0008: `ContainerEnvironment` is the only environment, and an instance without a dataset, a workspace and a stage image is refused when its boundaries are built.
- Rejected: a stage container that pushes with a token; the factory as root on the VM; keeping `factory-confine` inside the container as a second fence; a dataset with the work tree only (the agents would lose `git diff main`); a second snapshot adapter in v1.2.

*What went* (F0044, the layers of v1.1 one story each; the decision log keeps every entry that described them, closed by a line that says what replaced it):

- F0044-S0001, the wrapper's use: no agent call starts through the write guard's wrapper; the rules file, the run's temporary folder and `CLAUDE_CONFIG_DIR` went from both runtimes.
- F0044-S0002, the kernel's write guard: `factory-confine`, Landlock, `replace_process` and the pipeline definition's `tool_paths`; the records contract rose to `2.0`.
- F0044-S0003, the leftovers program: `factory.entry.leftovers` and the ending of leftover processes after a call.
- F0044-S0004, the fresh home: `factory.entry.fresh_home` and the reset of the agent's home.
- F0044-S0005, the second user: `sudo`, `env -i`, `FACTORY_AGENT_USER` and the shared mode of the factory's git.
- F0044-S0006, the checkout's hygiene: the seal, the removal of ignored paths and nested repositories, the re-clone and the stall reason `nested_repository`; the records contract rose to `3.0`.
- F0044-S0007, the suite: the stages' tests run on the container fakes; nothing of the product went.
- F0044-S0008, the inline environment: `InlineEnvironment` and `FACTORY_STAGE_ENVIRONMENT`.
- F0044-S0009, the undo: `UndoService`; the journal sentence now reads `The factory left out changes outside the write paths: ...`.
- F0044-S0010, the Docker path: `image/`, the compose instance, the entrypoint and the host's process table.
- F0044-S0011, the documents: this sweep.

What the acceptance measures (the feature's decision 27): the lines removed and added since the tag `v1.1`, apart for `src/factory`, `tests` and the documents, with the plan's target of three removed for one added; the running time of `make test` against `v1.1`'s; and that no value of `StallReason` or `RepositoryStopReason` names a removed layer. The acceptance report holds the numbers.

## Every container runs without rights and within limits

Date: 2026-10-24 (F0042-S0016, decision 23 of the feature F0042).

- Decision: every container of `PodmanRuns` is started with `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096` and `--memory=4g` (the constants `PIDS_LIMIT` and `MEMORY_LIMIT`). Every container keeps podman's default network. A container killed for its memory before its time limit is an ordinary failure with its exit status.
- Why: code in the checkout (a dependency's install script, a test, a file an agent was misled into writing) runs in these containers, and F0044 removes the second user and the kernel's write guard, so the container's own fence is what stays.
- Why the network stays: the check's `make sync` needs the package index after a change of `uv.lock` or `pyproject.toml`, the sync needs it as well, and the agent needs the model's API. Cutting it is a later step, for example an allow-list. The human chose this on 2026-10-24 over a check without network.
- Rejected: a `network` option on `ContainerRuns` that the check does not ask for.

## The checkout and the state directory are settings

Date: 2026-10-24 (F0043-S0002; `planning/v1.2-plan.md`, F0043).

- Decision: `FACTORY_CHECKOUT` and `FACTORY_STATE` set the factory's checkout and its state directory, each an absolute path, with `/work/checkout` and `/state` as defaults; a relative one is `SettingsInvalid`. On a `container` instance neither may be the `FACTORY_WORKSPACE` or lie inside it. `factory-run` writes the stop of invalid settings under the directory `FACTORY_STATE` names, else under `/state`.
- Why: on the VM of v1.2 the factory is a systemd service on the host under `/srv/factory/<instance>`, where `/work/checkout` and `/state` do not exist. Every rollback of the dataset would reset a checkout inside it, and the agent's container would reach the health file and the runs in a state directory inside it. A fault on the VM must land where `factory-health --state-directory` reads it.
- Superseded in part: the sentence "The checkout and the state directory are constants, never read from the environment" of *One instance runs one project, and the settings can name no second one*. The rest of that decision stands.
- Rejected: a second default for the VM (the instance's environment file sets both, and a compose instance that sets neither runs as before).

## The factory runs on the host, and the stage image carries the tools alone

Date: 2026-10-24 (F0043; the design and the human's answers are `planning/v1.2-plan.md`).

- Decision: on the VM of v1.2 the factory runs on the host as a `systemd` service, `factory@<instance>`, under the one user `factory`, with rootless Podman. `vm/setup.sh` makes the machine and `vm/factory.service` is the unit. The stage image (`vm/Dockerfile`) holds the tools alone: no factory source, no second user, no `sudo`, no entrypoint, no token; the agent files sit at `/etc/factory/claude`. The factory's code lives apart, in `/srv/factory/<instance>/factory`, built from the same repository.
- The human's decisions of the plan that shape it: 1 (the factory directly on the VM as a service under `factory`, rootless Podman, `zfs allow`), 3 (`zfs allow` first, one `sudoers` line for the four `zfs` commands that need root on the one dataset if the rollback needs it), 6 (the machine's files in a top-level `vm/`) and 8 (instance `vm`, `e2-standard-2`, `europe-west3`, a budget alert of $120 a month).
- Why one user and the token on the host: the agent's containers run without rights and mount the dataset only, so nothing but the host reads the hosting token, and the host alone pushes. A second user and `sudo` were layers that existed to protect the factory from the agent inside one container; with the factory outside, they have nothing to protect.
- Why the delegation first and the `sudoers` fallback second: `zfs allow` gives `factory` the rights it needs on the one dataset without root. The `--sudoers` option of the script writes the fallback, a file that lets `factory` run exactly `zfs snapshot`, `zfs destroy`, `zfs rollback -r` and `zfs diff -FH` on `<dataset>@base`, for a machine where the rollback of a mounted dataset needs root.
- Why the image without the factory: the factory's code and the tools change at different times. A merge rebuilds the factory's environment with `uv sync` and, when a pin changed, the image; neither drags the other along. The image's identity is not a label but a file, `FACTORY_IMAGE_ID_FILE`, which the operator renews after a build (`vm/setup.sh` makes it when it is missing). Root runs no file of the factory's checkout, which `factory` can write: the operator runs the setup script from their own copy.
- Rejected: the factory in a container with the podman socket (one more container and a socket that is nearly root, with no gain); the factory as root on the VM (a container escape would be root); a stage container that pushes with a token (the agent runs in that container).
- Open: F0044 removes the Docker path (`image/`, the compose instance and the long-lived container's layers), and with it the chapters of the operator guide that describe them.
- Done: F0044-S0010 removed the Docker path (`image/`, the compose instance and the long-lived container's layers) and the chapters of the operator guide that described them; the credential helper moved to `vm/git-credential-factory`.
- Since v1.2 F0045-S0003 a later run names the operator's own copy as the way to install a changed unit or helper; removing the installed file is no longer advised.

## A company's provider for opencode

Date: 2026-10-26 (F0046-S0001).

- Decision: `FACTORY_OPENCODE_PROVIDER_FILE` names a JSON file with one OpenAI-compatible provider (`@ai-sdk/openai-compatible`, base URL, the name of the key's environment variable, its models with optional limits and prices) and the `small_model`. The opencode runtime merges it into the configuration of every run, beside the existing keys and changing none. The agents use it through `FACTORY_OPENCODE_MODELS` (`opus=<id>/<model>`).
- Why a file and not settings: a provider has too many parts for one variable, and the file is validated into a model that refuses unknown keys, so a typo is a fault and not a silent default.
- Why the key is not in the file: it stays in `FACTORY_API_LOGIN_FILE`, which the run's login shell exports as `ANTHROPIC_API_KEY`; the file names that variable and the runtime writes `{env:<NAME>}`. Nothing the file holds is a secret, and a name that is not an environment variable name is refused.
- Why `small_model` is required and must be one of the models: opencode otherwise takes it from a service of its own, which a company proxy does not offer.
- Why the file is read at every run: a fault is then an `AgentRuntimeError` of that run, before any file is written, and the operator can fix the file without a restart. Reading it in `__init__` would make `build_boundaries` fail on a bad file.
- Why only the API login works: the agent's home is on the dataset and is rolled back before every stage, so a login that an operator's build keeps in the home does not survive to the next run.
- Consequence: a model without prices is costed at 0, so the factory's budget stop does not fire for it.
- Rejected: the key in the file; several providers in one file; reading the file once at start.
- Why the option is off by default: with `FACTORY_OPENCODE_PROVIDER_FILE` unset, the run's configuration file is byte-identical to the one written before the setting existed, so an instance that does not use a company's provider changes in nothing.
- How the provider is shown to work: no test runs the real opencode, so no test shows that the pinned opencode accepts the provider block. The preflight's `agent-run-probe` shows it on the machine: it makes one `opencode run` call as a stage makes it, with the provider merged in.

## The containers' environment stays closed except for the operator's list

Date: 2026-10-26 (F0046-S0002).

- Decision: `FACTORY_CONTAINER_ENV` lists names of the factory's own environment that the agent, sync and check containers also get, and `FACTORY_CA_BUNDLE` names a PEM file mounted read-only into the same containers at its own path and named by `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE`. `extra_environment` (`factory.domain.containers`) builds the extras once in `build_boundaries`, the only place that reads `os.environ`, and hands them to the runtimes, the container environment and the check commands.
- Why a list of names and not a pass-through: the closed environment keeps the hosting token and the factory's other values out of code an agent wrote. The operator names each variable they accept to expose; a name the environment lacks is skipped.
- Why the extras sit beneath the factory's own names: a listed `PATH` must not replace the container's `PATH`, which the stage image depends on. `HOME`, the two login names, `OPENCODE_CONFIG`, `GIT_ASKPASS` and `FACTORY_*` are refused when the settings are read, so the hosting token cannot be listed. The bundle's three variables win over a listed name of the same name.
- Why a file mounted at its own path: tools read the bundle from a path, and the path is then the same on the host and in the container.
- Consequence: `SSL_CERT_FILE` replaces Python's list of authorities, so the bundle must hold the public certificates beside the company's.
- Rejected: passing the whole environment; a fixed list of proxy names (mirrors and other names differ by company); computing the extras in the application layer (it would read the host's environment).
- Since v1.2 F0045-S0006 the settings model checks the names too, with the same rule and texts.

## The operator's own environment file

Date: 2026-10-26 (F0046-S0003).

- Decision: the unit `vm/factory.service` reads `/srv/factory/%i/factory.local.env` after `factory.env`, with the optional prefix (`EnvironmentFile=-`). A value in it wins, and its absence is no fault. `vm/setup.sh` never creates, changes, reads or removes the file, and says so in its closing line.
- Why a second file: the script rewrites `factory.env` at every run from its arguments and the pins of `vm/Dockerfile`, so an edit by hand there is lost. The values of F0046 (a model map, a provider file, the proxy names) have no place in the script's arguments.
- Why it is read second: systemd lets a later `EnvironmentFile=` override an earlier one, so the operator's value wins over the script's.
- Why optional: an instance that never needed the file starts as before.
- Rejected: a script option that writes the file (it would own the file again); merging the operator's values into `factory.env`.

## A slip the smoke test finds in a document goes straight to the docs stage

Date: 2026-10-26 (F0045-S0001).

- Decision: the smoke test's `next` is `approval`, `doing`, `docs` in the template (and in the factory's own and the demo's definitions, by the human's change). The smoke tester ends with `docs` when every finding is a slip in a document the documenter writes and the code does what the work item says, otherwise with `doing`; on a `docs` round the documenter fixes exactly those findings and ends with `smoke-test`. R12, in every shipped agent, names `smoke-test → docs` as a rework.
- Why: the coder may not write `docs/`, so a slip went smoke test, `doing`, review, docs, smoke test: four extra runs each in F0038-S0007 and S0009 (F0038-A0001, note 8).
- Why no code: `factory.domain.decisions.decide` already counts every `next` entry after the first as a rework against `round_cap`.
- Rejected: the coder passes a docs-only finding on with `review` and the reviewer with `docs` (the long way, shortened by nothing); a factory rule that reads the findings' paths (a new mechanism for a judgement an agent already makes). A reviewer marking the finding is not possible: none runs after the smoke test.

## The reset drops the page cache after the rollback

Date: 2026-10-26 (F0045-S0002; the cause was found and reproduced on `vm` on 2026-10-25 and 2026-10-26).

- Decision: `ZfsSnapshots.reset()` runs `sudo -n /usr/local/bin/factory-drop-caches` right after a rollback that exited 0, and a fault of that command is a `SnapshotError`. The wiring gives every `ZfsSnapshots` the command (`DROP_CACHES_COMMAND`); no setting names it. `vm/setup.sh` has the step `caches`, which writes the helper (`sync`, then `echo 1 > /proc/sys/vm/drop_caches`) and the one `sudoers` rule for it on every run, with or without `--sudoers` (decision 15 of F0045).
- Cause: a page a stage wrote through `mmap` survives `zfs rollback` in the page cache. The file then has the snapshot's size and the newer page's content, git's stat cache calls it clean, the sync does not repair it, and the fault reached `@base`. Dropping the clean cache after the rollback clears it.
- Why in the factory and the script: `vm` had the drop in a hand-made wrapper (`FACTORY_ZFS=/usr/local/bin/zfs-fresh`); a setting can be left out, the code cannot.
- Accepted: the drop is machine-wide, so the next sync reads from the disk.
- Rejected: the sync checks the content against git's stat cache (decision 16 of F0045; it would read every file on every stage and treat the symptom); keeping the wrapper behind `FACTORY_ZFS` (an operator's setting that can be missing).

## The machine powers itself off after an idle stretch, an option off by default

Date: 2026-10-27 (F0045-S0008; decisions 8 to 12 of the feature).

- Decision: `FACTORY_IDLE_SHUTDOWN_MINUTES` (unset, blank or `0` is off) turns on `IdleShutdown`. After an unbroken stretch of idle ticks of at least that many minutes, right after an idle tick, the factory logs a line that begins `idle shutdown: ` and `SystemctlPowerOff` runs `sudo -n /usr/bin/systemctl poweroff`. An idle tick is one that ran, ended at no stop and handled the event `idle`: nothing to start, the first waiting work item waits for the human, or another instance holds a claim. A stop or any other event ends the stretch; an iteration without a tick neither counts nor ends it.
- Why a story waiting for the human counts: a story that waits overnight for its merge would otherwise keep the VM running all night, the cost the option exists to save. Why a stop does not: it waits for a fix the operator may make on the machine.
- A failed power-off (no right, no `sudo`, the time limit) is one log line and a new stretch, not a stop: a stop would keep a machine running that the operator meant to save and stop no work. No preflight item checks the right.
- The right is one `sudoers` line for `/usr/bin/systemctl poweroff`, as for the `zfs` fallback and the cache drop; the setup script's option gives it.
- The right is one `sudoers` rule for `/usr/bin/systemctl poweroff` in `/etc/sudoers.d/factory-poweroff`, written only with the script's option `--idle-shutdown <minutes>` and removed by a run without it, so the right exists exactly while the option is used (F0045-S0009).
- Starting again is outside the factory: `gcloud compute instances start`, or an instance schedule made by hand that only starts the VM (`docs/operator-guide.md`, *The idle shutdown*).
- Rejected: every iteration without activity counts, stops included (the machine could power off while the operator fixes a low disk); a stage waiting for the human does not count (the VM runs all night); a polkit rule and a plain `systemctl poweroff` (not checked that `polkitd` is on the image, and the rule language is JavaScript); the factory as root; a stop for a failed power-off; a script or runbook commands that start the VM.

## Shared test code lives outside the test modules

Date: 2026-10-27 (F0045-S0010; F0039-A0002's note 4, decision 7 of `feature.md`).

- Decision: no module under `tests/` imports a test module (file name beginning with `test_`), in any of the three forms. What test modules share moves into a support module, a new one named `*_support.py`, or, for a fixture, into `tests/conftest.py`. `tests/test_shared_imports.py` is the guard and names each breach as `<file>:<line>: <module>`. Thirty-nine such imports in thirty-two modules were moved on 2026-10-26.
- Why: an import of a test module runs its setup, ties two stories' tests together, and turns a removed or renamed test module into failures elsewhere, as F0044's removals showed.
- Rejected: the candidates list's rule that shared test code lives only in `*_support.py` modules (it would rename `human_clone.py`, `recording_log.py`, `source_search.py` and others, some hundred imports, for no gain).
- The fixtures `rig` and `red_main` of the preflight tests went to `preflight_support.py`, not `conftest.py`: a root fixture `rig` would reach every module, and two other rigs carry that name.

## A snapshot adapter that copies a directory

Date: 2026-10-31 (F0047-S0001; decisions 1 and 2 of the feature).

- Decision: `FACTORY_SNAPSHOTS=copy` with `FACTORY_SNAPSHOT_BASE` chooses `CopySnapshots` in place of `ZfsSnapshots`, for a sandbox without ZFS (a Cloud Run job). `reset` empties the workspace and copies the base into it, `advance` replaces the base with a copy of the workspace, and `changed_paths` compares the two trees. The default is `zfs`; nothing changes for an instance that does not set the variable.
- The adapter is the suite's fake promoted, not a second implementation: its logic moved from `FakeSnapshots` to `CopySnapshots`, and `FakeSnapshots` is a subclass with the same constructor. The tests of the fake pass unchanged, and what they check is now the real adapter's behaviour.
- One change when the logic became real: files are compared in chunks of at most 1 MiB, never read whole, because the workspace may hold a gigabyte.
- The base must not overlap the workspace (a reset would empty it), the checkout or the state directory (the base would be copied over them): `read_settings` and the model validator both refuse it. An absent base is the wiring's fault, like an absent dataset. With `copy` the preflight's `zfs` and `dataset` items give way to one, `snapshots`, and the dataset is not read.
- Cost accepted: a reset takes about 1.6 s per GiB (a tree of 20000 files), and the comparison is slower than the 0.2 s of `rsync`.
- Rejected: `rsync` in the first version (a later one may use it if the cost shows); a base inside the workspace (a reset would delete it).

## A root container profile for a managed sandbox

Date: 2026-10-31 (F0047-S0002; decisions 3 to 5 of the feature).

- Decision: `FACTORY_CONTAINER_PROFILE=job` makes `PodmanRuns` start containers as the job's root, for a Cloud Run job. Three global options (`JOB_PODMAN_OPTIONS`: `--runtime=runc`, `--cgroup-manager=cgroupfs`, `--storage-driver=overlay`) go before every podman command, and `run` gets `--http-proxy=false --network=host` in place of `--userns=keep-id`. The default `rootless` keeps every word it had.
- Why: measured on 2026-10-31 (Podman 5.4, `planning/cloud-sandbox/`): the job's root has `NoNewPrivs`, so rootless cannot map a user; the hybrid cgroups are refused by `crun` and Podman 6 and accepted by `runc`; the overlay root cannot hold podman's overlay storage; no bridge reaches the outside; and podman copies the job's proxy variables into containers. With these words, `--timeout` (exit status 255), `--pids-limit`, `--memory`, `--security-opt=no-new-privileges`, bind mounts and `:ro` all worked.
- The container runs as root with `--cap-drop=all`; the job itself is the sandbox's boundary, and the container fence stays what it was.
- One class with a profile, not a subclass: a subclass would copy `launch`. The grace, the reading of exit statuses and the `ValueError` rules are shared.
- Rejected: changing the default profile (the VM's words must not move); a setting for each option (the words belong together and have one cause).
- Changed by F0047-S0009 (decision 19 of the feature): the fourth word, `--storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs`, is gone. With `fuse-overlayfs` `make test` took 601 s in a job of eight CPUs against 167 s on the VM, so `check`'s eight minutes would end every stage; with a tmpfs under podman's storage and the native overlay it took 182 s, and the image build 107 s instead of 199 s (`planning/cloud-sandbox/`, P15 and P16). The storage's place is the machine's (a tmpfs the start script mounts); the factory's words only keep `--storage-driver=overlay`, so podman refuses an unsuitable root.

## A container must not reach the metadata server

Date: 2026-10-31 (F0047-S0003; decision 6 of the feature).

- Decision: with `FACTORY_CONTAINER_PROFILE=job` the preflight gains the item `metadata-block`. One container runs `curl` against `http://169.254.169.254/computeMetadata/v1/instance/id` and the item passes only when curl prints `000` (no connection). A machine that fails it stops like any failed preflight item. The rule itself, a firewall reject of TCP port 80 to that address, is installed outside the factory (the start script).
- Why: in a Cloud Run job a container shares the job's network, and the server hands the job's service-account token to any process there (measured 2026-10-31, reachable from host-network and bridge containers, by address and by name). Rejecting port 80 stops it without touching DNS or the proxy.
- The probe proves the rule where it matters, from a container, and a timeout proves nothing: `timed_out` fails the item whatever the output was. Any other reading than `000` or three digits fails as "could not tell", never as a pass.
- The item takes a callable and the wiring holds the run's arguments (30 seconds, no mounts, empty environment), as `stage_image_item` does; the application layer knows no container details.
- Rejected: checking the rule's text or the firewall's state (it proves the file, not the effect); letting the item pass on a timeout (a hung probe is not a refusal); the item under `rootless` (the VM has no service account, so the server gives no token).

## A refresher keeps the bearer token fresh

Date: 2026-10-31 (F0047-S0004; decisions 7 and 8 of the feature).

- Decision: a separate process, `python -m factory.entry.refresh_token`, requests a token from an OAuth2 client-credentials endpoint and writes it atomically into the file `FACTORY_API_LOGIN_FILE` names. The runtimes already read that file at every call, so none of them changes.
- Interval: every ten minutes (the human, 2026-10-31), or half the token's life when that is shorter, never under thirty seconds. A container mounts the file when it starts and its login shell reads it once, so a run holds a token at least the token's life less ten minutes old. A half-life rule on a one-hour token would leave thirty minutes to a run that starts just before a refresh, short of a forty-minute stage; the fixed interval leaves fifty.
- A failed refresh keeps the old file and tries again after a minute; any fault of one refresh counts, so the process does not die while the old token is still valid.
- The client secret is read from a file that Secret Manager mounts, never from the environment, and appears in no log line, no error message and no child's environment: every detail is masked with `***`. The same holds for the token.
- The HTTP goes through the standard library (`urllib`), which honours `https_proxy` and `no_proxy`; no dependency is added. `factory.adapters.oauth_token` is the one module allowed to import `urllib.request` and `http.client`.
- Rejected: a refresh at half the token's life alone (see above); a change in the runtimes to fetch the token themselves (every runtime would need it); the secret in the environment (a child would inherit it).

## The code and the project apart

Date: 2026-10-31 (F0047-S0005; decision 9 of the feature).

- Decision: `vm/setup.sh` takes `--code-url`, the repository the factory's code and the stage image's `vm/Dockerfile` come from, default `--repository-url`. A different code url is cloned without any credential (`GIT_TERMINAL_PROMPT=0`, no `GIT_ASKPASS`, no `core.askPass`), and a clone that asks for one fails with a message. `FACTORY_REPOSITORY_URL` stays the project. The credential helper answers only a request for the host of `FACTORY_REPOSITORY_URL`.
- Why: a company on its own enterprise host runs the factory's public code from a public repository, which that host allows no fork of; code and project are then two repositories on two hosts, and the project's token must never be offered to the code's host.
- Rejected: a token for the code repository (the code must be public and readable without one); the helper trusting git to ask for the right host (git asks the helper for whatever host a remote names).

## In a job the idle shutdown ends the process

Date: 2026-10-31 (F0047-S0008; decision 18 of the feature).

- Decision: `FACTORY_IDLE_SHUTDOWN_ACTION` is `poweroff` (default, unchanged) or `exit`. With `exit`, `ProcessExit` calls the stop request of the loop instead of running `systemctl`: the same flag a `SIGTERM` sets, so the scheduler ends after the tick in progress and `factory-run` returns 0, which ends a job's execution. The idle rule, the log line (`powering the machine off`, also with `exit`) and every other setting are unchanged.
- Why: in a Cloud Run job `sudo` and `systemctl` do not exist, so an idle job would be billed until its task timeout. Ending the command is the job's equivalent of switching a VM off; the schedule or the operator starts it again.
- The choice is made in the entry wiring, with `ProcessExit` as one more `PowerOff`; the loop's event is passed in as `request_stop`, so `exit` without one is a `ValueError`.
- Rejected: a separate stop interface in the application layer (`PowerOff` already says what the idle shutdown needs); `exit` for every machine (a VM keeps `poweroff`); waking the job when work arrives (not in this feature).

## A bare job becomes an instance at start

Date: 2026-11-01 (F0047-S0006; decisions 10 to 12 of the feature).

- Decision: `vm/job-start.sh` is the command of a Cloud Run job. It installs, clones the code and builds the stage image at every start, and ends in `exec factory-run`. The job's environment is the instance's configuration; the script sets a derived variable only where the job gave none. `FACTORY_CODE_REF` is required and has no default (the human, 2026-10-31), so nothing pushed to the code repository's `main` reaches a job unseen; the operator moves the tag or commit deliberately.
- The runc release is the one measured in the job (P3). The script holds its SHA-256 as a constant and checks the download against it; a checksum downloaded beside the binary would check nothing, and `RUNC_VERSION` without `RUNC_SHA256` is refused for the same reason.
- The code is cloned with no credential, and the versions the preflight compares (`FACTORY_CLAUDE_VERSION`, `FACTORY_OPENCODE_VERSION`) are read from the cloned `vm/Dockerfile` the way `vm/setup.sh` reads its pins (the human, 2026-11-01). Podman's storage root is a tmpfs mounted at every start, since the job's root file system cannot carry the kernel's overlay (P16).
- A restart is a crash for the recovery, charged once, and after `crash_cap` crashes the work item waits for the human (accepted by the human, 2026-10-31). A stop between stages before the nightly restart is a candidate for later.
- Rejected: a default code ref such as `main`; the runc checksum fetched with the binary; copying `vm/setup.sh`'s `sed` lines into the script (they stay where they are).

## Debian's packages follow the base image's release

Date: 2026-11-01 (F0047-S0006; decision 17 of the feature; the human, 2026-10-31).

- Decision: the stage image's seven Debian packages (`git`, `make`, `curl`, `ca-certificates`, `procps`, `nodejs`, `npm`) are installed by name, without versions. The base image stays pinned by its digest, which fixes the Debian release, and `uv`, Claude Code and opencode keep their exact versions.
- This changes the rule of 2026-10-16 (*Every tool of the machine's image is pinned*) for the operating system's packages, and only for them.
- Why: a job rebuilds the image at every start, and Debian's mirror keeps only a package's current version, so an exact version breaks the build at the next point release. Within one stable release Debian ships only security and serious fixes. The three tools that shape a stage's result have registries that keep every version. A VM's next rebuild takes the current packages of the same release.
- `tests/test_stage_image.py` allows the findings of an `apt-get install` of exactly those seven names and still fails any other floating reference. A new Debian release is a deliberate change of the digest.
- Rejected: pinning the packages and refreshing the pins in every release (a broken start in between); dropping the digest (the release would float).
