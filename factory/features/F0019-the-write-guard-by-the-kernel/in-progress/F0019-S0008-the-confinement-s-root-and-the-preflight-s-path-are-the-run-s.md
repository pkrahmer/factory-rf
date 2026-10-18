---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 228
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T19:17:54.642710Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T19:17:54.648362Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T19:18:09.078104Z'
  stage: intake
  run: 618320dcf8ac4b9da9a4f3cc9e9dd7aa
---

# The runtime's rules and the preflight's wrapper search use the run's own root and PATH

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

F0019's `make mutants` found two lines of the guard whose breaking no test would notice. In `ClaudeCodeRuntime`, the rules are built with `confinement_of(..., root=guard.root, ...)` (`src/factory/adapters/claude_runtime.py`, `_confinement`). The mutant that drops `root` survives, and with it a write path naming a file at the checkout's root that does not exist yet would widen to the whole checkout: the one target F0019's decision 6 rules out. `confinement_of` has a domain test for this, but no runtime test passes such a write path through. In `factory.entry.wiring`, the preflight items `confinement` and `agent-environment` search for `factory-confine` and `factory-guard` through `_which_on(name, path)`. The mutant that drops `path=path`, so the search uses the factory process's own `PATH` instead of the agent run's, survives. This story adds the criteria that pin both lines. The code is expected to pass them as it is: the coder changes nothing unless a test shows a fault. The domain rules, the wrapper and the hook stay as they are.

## Interface

No module under `src/factory/` is expected to change. The pinned behaviour:

- `ClaudeCodeRuntime.run` (`adapters`), with `confine_executable` set, builds the run's rules against the request's checkout root (`GuardSettings.root`). A write path naming a file at the root that does not exist gives no target, neither the file nor the root folder. A write path naming a missing file below the root gives its folder. An existing root file gives a file rule.
- `machine_extras(boundaries, settings, which, environment)` (`entry`): the items `confinement` and `agent-environment` search for their command on the `PATH` of `environment` (the agent run's), never on the factory process's own `PATH`.

Test modules (new): `tests/adapters/test_claude_runtime_confinement_root.py`, `tests/entry/test_wiring_extras_path.py`. Helpers of `tests/adapters/test_claude_runtime_confinement.py` and `tests/entry/test_wiring_extras.py` that the new tests need move to a shared place under the standing leave of `CLAUDE.md`.

## Acceptance criteria

1. Through a stand-in confine executable that records the rules file, a request whose checkout holds `README.md` gives these rules (rows of one parametrized test):
   - Write paths `["NOTES.md"]` (missing): no folder equal to the checkout and no file `NOTES.md`.
   - Write paths `["docs/new.md"]` (missing): the folder `<checkout>/docs` and no folder equal to the checkout.
   - Write paths `["README.md"]` (existing): the file `<checkout>/README.md` and no folder equal to the checkout.
2. Through the real wrapper, with write paths `["NOTES.md"]` and the file missing, a stand-in step that writes `<checkout>/NOTES.md` ends the run `died` and leaves no such file. A step that writes `<checkout>/other.md` does the same (rows of one parametrized test).
3. The `PATH` searched (rows of one parametrized test, each with `HOME` an existing folder and the kernel's real ABI):
   - `confinement`, with an agent run `PATH` that holds an executable `factory-confine` and a test process `PATH` that does not (`monkeypatch.setenv`): the item passes.
   - `confinement`, with an agent run `PATH` that does not hold `factory-confine` and a test process `PATH` that does: the item fails with the detail `factory-confine is not on the agent run's PATH <path>`.
   - `agent-environment`, the same two rows with `factory-guard`: it passes, then fails with its existing detail for a missing `factory-guard`.
4. `make check` stays green.
5. docs: none. The documents already say that the runtime never allows the root and that both items search the agent run's `PATH` (`docs/operator-guide.md`, *The kernel refuses every other write* and the preflight's items); the story only adds tests.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/checkout" "$d/home" "$d/runs" "$d/tmp"
cat > "$d/claude" <<'EOF2'
#!/bin/sh
r=refused; { echo x > NOTES.md; } 2>/dev/null && r=written
printf '{"type": "result", "subtype": "success", "is_error": false, "num_turns": 1, "total_cost_usd": 0.01, "usage": {"input_tokens": 1, "output_tokens": 1}, "permission_denials": [], "structured_output": {"decision": "question", "entry": "root file %s"}}\n' "$r"
EOF2
chmod +x "$d/claude"
uv run -q python -c '
import os, sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, GuardSettings
d = Path(sys.argv[1])
runtime = ClaudeCodeRuntime(str(d / "claude"), d / "runs", confine_executable="factory-confine", temporary_root=d / "tmp")
agent = AgentDefinition(name="coder", model="sonnet", tools=["Bash"], budget_usd=Decimal("1"), instructions="Probe.")
guard = GuardSettings(root=d / "checkout", write_paths=["NOTES.md"], protected_paths=[])
request = AgentRunRequest(agent=agent, prompt="Probe.", allowed_decisions=["question"], time_limit=timedelta(minutes=1), working_directory=d / "checkout", environment={"PATH": os.environ["PATH"], "HOME": str(d / "home")}, guard=guard)
result = runtime.run(request)
print(result.end_reason, "|", result.entry, "|", (d / "checkout" / "NOTES.md").exists())
' "$d"
```
Expect: `completed | root file refused | False`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures (`ClaudeCodeRuntime.run` with `confine_executable` and `GuardSettings.root`; `machine_extras(boundaries, settings, which, environment)` in `factory.entry.wiring`), plus the two new test modules and the helper move under the standing leave. No `src/` change is expected.
   Criteria: each is testable by one parametrized test. Criterion 1 has a row for each of the three Interface cases: a missing root file, a missing file below the root, and an existing root file. Criterion 2 runs the real wrapper, with a step that writes the missing root file and one that writes another root file, so the refused side is covered. Criterion 3 has a pass row and a fail row for `confinement` and for `agent-environment`, and the failing detail is given. There is no rule without a failing side.
   Smoke test: it is runnable as written. It uses a stand-in `claude` and a temporary directory. The `Expect:` line `completed | root file refused | False` can be checked against the printed output.
   Architecture: tests only, in `tests/adapters` and `tests/entry`, mirroring the package. The layers are untouched, and moving the shared helpers is covered by the standing leave.
   Scope: it is inside F0019 (decision 6, the preflight items) and outside none of its "Out of scope" entries. The criteria add tests and do not change the domain rules, the wrapper or the hook.
