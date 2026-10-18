---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 225
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T17:09:40.571619Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T17:09:40.577308Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T17:09:58.504010Z'
  stage: intake
  run: 64e6fc2a36e84a77af5bf10a96488ff5
---

# The agents' instructions explain a refused write

## Description

Under the kernel's write guard (S0004) an agent that writes outside its write paths, by any tool or command, gets the system's `Permission denied`, and one that writes to `/tmp` itself gets it too. Its instructions today say only that a hook refuses an edit and that the factory undoes other writes, so an agent may read the refusal as a fault of the machine and work around it, or end the stage `question` about a broken `/tmp`. This story rewrites the closing sentence of rule R14 in all seven shipped agents (`claude/agents/*.md`): the kernel refuses every other write, the hook still refuses an edit (it stays as the cross-check, feature decision 16), the factory undoes the rest; a refused write is `Permission denied` and the guard, never retried another way, and a `question` when the work needs that path; temporary files go to `$TMPDIR`, the run's own folder (feature decision 14). The first sentence of R14 and every other rule stay as they are; the hook's clause goes with the hook, in the later feature that removes it.

## Interface

No module under `src/factory/` changes. The coder changes the seven files `claude/agents/acceptance-reviewer.md`, `coder.md`, `documenter.md`, `intake.md`, `reviewer.md`, `smoke-tester.md` and `tester.md`: in each, the text of R14 after "You write only within your write paths in the pipeline definition (`{work_item}` there is your own work item, outside its front matter and journal), nothing else: " is replaced, so that R14 reads in full:

```markdown
R14. The pipeline's own files — `factory/pipeline.yml`, `factory/story-form.md`, every feature's `feature.md`, `backlog/`, `done/` and `.claude/` — change only with the human's commit or on their explicit instruction. You write only within your write paths in the pipeline definition (`{work_item}` there is your own work item, outside its front matter and journal), nothing else: the kernel refuses every other write, by any tool and any command you run, a hook also refuses an edit outside the write paths, and the factory undoes any other write after the stage. A refused write fails with `Permission denied` (`EACCES`, `PermissionError: [Errno 13]`, `cannot create ...: Permission denied`): that is the write guard, not a fault of the machine; never retry it by another route, and when the work needs that path, end with `question` and name it. Make temporary files only in `$TMPDIR` (`mktemp`, `tempfile`), the run's own folder, which the factory removes after the run; `/tmp` itself is refused.
```

- The paragraph is one line in each file, as R14 is today; nothing else in the files changes.

Tests (the tester writes them): `tests/test_claude_agent_refusal.py`, reading the shipped agents through `tests/shipped_agents.py`.

## Acceptance criteria

1. The `Rules` section of each of the seven shipped agents holds the R14 paragraph of the Interface exactly, as one line (seven rows of one parametrized test over the shipped agents' names).
2. No shipped agent's body holds the old ending "a hook refuses an edit outside the write paths, and the factory undoes any other write after the stage." (seven rows of one parametrized test).
3. Each shipped agent's body holds the line that starts `R14. ` exactly once (seven rows of one parametrized test).
4. `make check` stays green.
5. docs: `docs/project-guide.md`, section *The shipped agents, settings and template*, says in one sentence that R14 tells every agent what a refused write looks like (`Permission denied`), that it is the guard and a `question` when the work needs the path, and that temporary files belong in `$TMPDIR`.

## Smoke test

```bash
grep -l 'A refused write fails with `Permission denied`' claude/agents/*.md | wc -l
```
Expect: `7`

```bash
grep -L 'a hook refuses an edit outside the write paths, and the factory undoes any other write after the stage' claude/agents/*.md | wc -l
```
Expect: `7`

```bash
grep -c 'Make temporary files only in `$TMPDIR`' claude/agents/coder.md
```
Expect: `1`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names the seven concrete files under `claude/agents/` and gives the full R14 paragraph verbatim, as one line. No `src/` module changes. `tests/shipped_agents.py` exists, and each agent has exactly one `R14. ` line today.
   - Criteria: 1 pins the full paragraph exactly, so every clause of it is covered: the kernel refusing, the hook staying, the undo, `Permission denied` and its three spellings, no retry by another route, `question` naming the path, `$TMPDIR`, and `/tmp` refused. 2 covers the failing side: the old ending is gone. 3 says R14 appears exactly once. Each of the three is a parametrized test over seven agents. 4 is `make check` and 5 is the docs criterion. Each is testable by one test function.
   - Smoke test: the three `grep` commands can be run as written. The expected values (`7`, `7`, `1`) can be checked against the output.
   - Architecture: this is prompt text only, in the coder's `claude/*` write path. Nothing crosses a layer, and the first sentence of R14 and the other rules stay as they are.
   - Scope: matches the feature's scope line for `claude/agents/*.md` (S0006) and decision 14. It does not remove the hook, which is out of scope.
