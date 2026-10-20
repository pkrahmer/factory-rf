---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 370
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-20T23:19:46.233770Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T23:17:18.803537Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T23:17:18.809188Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T23:17:41.930418Z'
  stage: intake
  run: d65e6712d1194de1a83ae0e3facf57b7
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T23:18:02.794422Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T23:19:25.268417Z'
  stage: tests
  run: cd12312e9ca446d4bd8aa33bd28f45db
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T23:19:46.233770Z'
  stage: doing
---

# The documents say what the factory's kill of make mutants leaves

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0030's `feature.md` (*The human's changes*, point 1, and *Out of scope*) says that the `mutants` recipe's temporary folder stays after the factory's kill, and that this sentence is in S0001's docs criterion. It is not there, and the project guide does not say it. *The temporary folder* in `docs/project-guide/processes-and-checks.md` says the recipe's `EXIT` trap removes the folder "also after a stop and after a failed run", and is silent on a kill. F0030's acceptance ran the recipe's form through `MakeProjectCommands.run` with a time limit: every process of the session was gone, and the folder that `mktemp -d` made stayed, because SIGKILL runs no trap. Also, the decision log's entry *Mutation testing per story* still says in its decision (4) that the factory's kill "does not reach mutmut". That entry is superseded for other reasons, and F0030's own entry says that it corrects decision 4, but the old line points nowhere, unlike the entry of 2026-10-18, which S0001 gave a line naming the new entry. The human's real check with mutmut (F0030's change 2, 2026-10-20) answered the feature's decision 14. `make mutants`, killed by the factory at 50 s during mutmut's stats run, lost all of `make`'s session. But a fake `claude` that `tests/adapters/test_claude_runtime.py::test_call_over_its_time_limit_is_killed_with_unknown_measures` started outlived the kill for up to its 60 s, in a session of its own: the runtime under test starts its command line through `run_process`, which uses `start_new_session`. This story writes these facts. No code, test, `Makefile` or `README.md` changes.

## Interface

None: documents only (`docs/project-guide/processes-and-checks.md`, `docs/decisions.md`). No module under `src/factory/` and no test changes.

## Acceptance criteria

1. Nothing under `src/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/project-guide/processes-and-checks.md`, *Mutation testing*, the paragraph *The temporary folder*: a run that the factory kills at its time limit (`MakeProjectCommands.run`, *Killing a session*) ends with SIGKILL, which runs no `EXIT` trap. mutmut and every process still in `make`'s session are gone, but the temporary folder stays, with the words `the temporary folder stays`; it is under the `TMPDIR` of the caller of `make`, and the operator removes it by hand. A process that one of mutmut's tests started through `factory.adapters.process` is not in that session: the code under test starts every command in a session of its own (`start_new_session`), so the kill does not reach it, and it runs on until it ends by itself, with the words `runs on until it ends by itself`. The paragraph names the case seen on 2026-10-20: `make mutants` killed by the factory at 50 s, during mutmut's stats run, left the fake `claude` of `tests/adapters/test_claude_runtime.py::test_call_over_its_time_limit_is_killed_with_unknown_measures` running for up to its 60 s. A stop by `MUTANTS_SECONDS` still runs the trap. `docs/decisions.md`: in the entry *Mutation testing per story*, decision (4) gains, right after "does not reach mutmut", `(since F0030-S0001 the factory's kill reaches mutmut; see *A command stopped at its time limit loses every process of its session*)`. In the entry *A command stopped at its time limit loses every process of its session*, the Decision bullet gains, after its sentence on `setsid`, one sentence: a test that mutmut runs can start such a process, because `factory.adapters.process` starts every command with `start_new_session`, and that process ends by itself (seen on 2026-10-20 in the real check with mutmut, which answers F0030's decision 14). `README.md`: none, nothing a newcomer does changes.

## Smoke test

```bash
grep -c "the temporary folder stays" docs/project-guide/processes-and-checks.md
```
Expect: `1`

```bash
grep -c "since F0030-S0001 the factory's kill reaches mutmut" docs/decisions.md
```
Expect: `1`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None: documents only" names the two files, `docs/project-guide/processes-and-checks.md` and `docs/decisions.md`, and says no module under `src/factory/` changes. Nothing to sign, which is right for a documents-only story. I checked the target text: the decision (4) line in the entry *Mutation testing per story* (`docs/decisions.md:814`) and the entry *A command stopped at its time limit loses every process of its session* (`docs/decisions.md:900`) both exist.
   - Criteria: criterion 1 (nothing under `src/` or `tests/` changes) can be checked by a diff of those folders. Criterion 2 is `make check`. Criterion 3 is the docs criterion and is the only place the new text is stated. It fixes the wording the smoke test greps (`the temporary folder stays`, `runs on until it ends by itself`) and the exact parenthetical for decision (4). It also fixes where each sentence goes. Each sentence is one unit of text with a stated location, so it can be checked without further decisions. The story states no limit, validation or error, so there is no failing side to cover.
   - Smoke test: both commands are plain `grep -c` calls with no pytest. Today the first prints 0 and the second prints 0, because the exact phrase `since F0030-S0001 the factory's kill reaches mutmut` is absent (line 506 has a different "since F0030-S0001"). So both `Expect: 1` lines can only be met after the edit. Neither `Expect:` line is met yet. One gap: the phrase `runs on until it ends by itself` has no grep of its own. The criterion states it, so the docs check and the reviewer cover it. I did not treat this as a question.
   - Architecture: documents only. The documenter writes `docs/*`, and `README.md` is correctly left alone. No layer is touched, and no `src/` or `tests/` file.
   - Scope: this is S0003 in the feature's Stories and Scope list ("documents only", proposed by the acceptance). It follows the feature's *The human's changes* and decision 14, which the human answered on 2026-10-20. It does not touch the `Makefile`'s `mutants` recipe, `factory/pipeline.yml` or the TERM question, which are in *Out of scope*.
4. factory: started tests as self.
5. tester: No tests written. This story only changes documents. Its Interface says "None: documents only" and that no test changes. Criterion 1 says nothing under `src/` or `tests/` changes.
   - criterion 1 (nothing under `src/` or `tests/` changes): no test function. I left `src/` and `tests/` alone, so the tester's part of this criterion is met. `git status` shows no change of mine.
   - criterion 2 (`make check` stays green): no test function. This is the stage check the coder and the documenter run.
   - criterion 3 (docs): no test function. The docs stage writes the text. The story's smoke test (`grep -c` on the two phrases) checks it, along with `make documents` and the reviewer.
   Files created: none. Modules the test runner could not import: none. Since there are no new tests, there is no red test that `make test` needed to show failing, so I did not run it. `make lint`: green. Nothing for the coder to implement against: the coder's entry should also say that nothing under `src/` or `tests/` changed.

   `lint`: lint: green (0.5 s)
   `test`: test: green (63.0 s)
6. factory: started doing as self.
