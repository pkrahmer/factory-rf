---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 471
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T22:19:14.863330Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T22:19:14.869672Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-26T22:19:36.280313Z'
  stage: intake
  run: b4e4d0e251484311822f38277e51780a
---

# The settings model refuses what the reading refuses

## Description

`InstanceSettings` is built by `read_settings` for every instance and directly by the suite. Two of its rules hold only in the reading. The field `agent_home` still defaults to `/home/agent/.claude`, the second user's home of v1.1, after S0005 (the agent files' folder and the image identity file are required settings) made `FACTORY_CLAUDE_HOME` required and absolute in `read_settings`; the human chose to remove the model's default too (the answers of 2026-10-25, decision 32 (b) of `feature.md`). And the names of `container_env` (F0046-S0002) are checked only in `read_settings`, so a model built in code accepts `container_env=("HOME",)`, a name the factory sets itself, while `ca_bundle` and `opencode_provider_file` are checked by the model as well (F0046-A0001, note 9). This story moves both rules into the model (decisions 14 and 18): `agent_home` is a required field that must be absolute, and the model checks every name of `container_env` with the reading's rule and the reading's texts. `read_settings` keeps raising `SettingsInvalid` naming its variable for the same faults, before the model is built. What stays: every other field and its default, the reading's faults and their texts, the containers' use of the names.

## Interface

`factory.domain.settings` (`domain`):

- `AGENT_HOME_DEFAULT` goes. `InstanceSettings.agent_home: Path` has no default; it is checked by the same validator as `checkout` and `state_directory`, so a relative path is refused with `is not an absolute path`.
- `InstanceSettings.container_env: tuple[str, ...] = ()` is checked by the model, name by name, in order, with the rule `read_settings` applies to `FACTORY_CONTAINER_ENV`: a name that is not a variable name (`[A-Za-z_][A-Za-z0-9_]*`) is refused with `holds <name>, which is not a variable name`; a name in `RESERVED_CONTAINER_NAMES` or beginning with `RESERVED_CONTAINER_PREFIX` with `holds <name>, which the factory sets itself`; a name given twice with `names <name> twice`. The rule is written once and used by both.
- `read_settings` is unchanged in behaviour: a fault of `FACTORY_CONTAINER_ENV` or `FACTORY_CLAUDE_HOME` raises `SettingsInvalid` naming the variable, never a `ValidationError`.

Tests (the tester writes and changes them; the leave is decision 26 of `feature.md`): new tests at the tester's choice, for example `tests/domain/test_settings_model_rules.py`. Earlier tests: every construction of `InstanceSettings` under `tests/` that gives no `agent_home` (on 2026-10-26 thirty-eight constructions in thirty-three modules, among them the fixtures `local_settings` and `disk_settings` of `tests/conftest.py`, `tests/proof_support.py` and `tests/application/test_checkout_preparer_seal.py`) gains an absolute `agent_home`, a path under `tmp_path` where the test reads the agent files and otherwise one shared constant the tester places in `tests/settings_support.py`; each test keeps its name and its assertions; the tester names each changed module in its entry.

## Acceptance criteria

1. The field is required and absolute (rows of one parametrized test, the model built through a variable typed `type[BaseModel]`, with `repository_url` and `instance` given): without `agent_home` it raises `ValidationError` naming `agent_home`; `agent_home="agents"` raises `ValidationError` holding `is not an absolute path`; `agent_home="/srv/agents"` gives `agent_home == Path("/srv/agents")`.
2. The names of `container_env` in the model (rows of one parametrized test, the model built as in criterion 1 with `agent_home="/srv/agents"`): `()`, `("HTTPS_PROXY",)` and `("HTTPS_PROXY", "NO_PROXY", "_X1")` are accepted and kept in order; `("HOME",)`, `("ANTHROPIC_API_KEY",)` and `("FACTORY_X",)` raise `ValidationError` holding `holds <name>, which the factory sets itself`; `("1A",)` and `("A-B",)` raise it holding `holds <name>, which is not a variable name`; `("A", "A")` raises it holding `names A twice`.
3. The reading names its variable (rows of one parametrized test over `read_settings` of `BASE` of `tests/settings_support.py` with `FACTORY_CONTAINER_ENV` set to `HOME`, `1A` and `A,A`): each raises `SettingsInvalid` (not `ValidationError`) with variable `FACTORY_CONTAINER_ENV` and the fault text of criterion 2 for that name.
4. The old default is gone (rows of one parametrized test): `AGENT_HOME_DEFAULT` is no attribute of `factory.domain.settings`; no module under `src/factory` holds the string `/home/agent`.
5. `make check` stays green.
6. docs: `docs/project-guide/watching.md`, where it lists the fields of `InstanceSettings`: `agent_home` required and absolute, and the model's check of `container_env` with its three faults; `docs/project-guide/README.md`, the line of `tests/settings_support.py` under *Shared test helpers*: the constant the tester added, if any. `docs/decisions.md`: the entry of `FACTORY_CONTAINER_ENV` (F0046-S0002) gains one closing line: "Since v1.2 F0045-S0006 the settings model checks the names too, with the same rule and texts." `docs/operator-guide.md`, `README.md`: none (no setting changes).

## Smoke test

```bash
uv run python - <<'EOF'
from pydantic import ValidationError
from factory.domain import settings
from factory.domain.settings import InstanceSettings
print(hasattr(settings, "AGENT_HOME_DEFAULT"))
for extra in ({}, {"agent_home": "/srv/agents", "container_env": ("HOME",)}, {"agent_home": "/srv/agents"}):
    try:
        print(InstanceSettings(repository_url="/srv/project.git", instance="vm", **extra).agent_home)
    except ValidationError as error:
        first = error.errors()[0]
        print(first["type"], "which the factory sets itself" in first["msg"])
EOF
```
Expect: four lines: `False`; `missing False`; `value_error True`; `/srv/agents`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `factory.domain.settings`, `AGENT_HOME_DEFAULT` (still at line 49 of `src/factory/domain/settings.py`, the only `/home/agent` under `src/factory`), the field `agent_home: Path` (line 106), the validator that already covers `checkout` and `state_directory`, and the reading's rule at lines 280-297 whose three texts the story quotes. Every behaviour it states has a criterion: required and absolute (1), the three name faults and the accepted order (2), the reading's `SettingsInvalid` (3), the removal (4).
   - Criteria: each is one parametrized test with concrete rows. Both sides are covered: accepted and refused for `agent_home`, and for `container_env` the accepted lists, reserved names, the `FACTORY_` prefix, bad names and a duplicate. Criterion 3 covers the reading, with the variable and fault text per row. Criterion 4 covers the constant and the string. Criteria 5 and 6 close the list, and the docs criterion names its files and the exact closing line.
   - Smoke test: runnable with `uv run python -`, no pytest, so the `-q` rule does not apply. I traced it against the code. `InstanceSettings` with only `repository_url` and `instance` gives `missing` first, whose message lacks the text, so `False`. `HOME` gives `value_error True`. The valid case prints `/srv/agents`. The `Expect:` line gives four lines that can be checked exactly.
   - Architecture: both rules live in `factory.domain`, a pure model with no I/O, and `read_settings` stays in the same module. The story writes the rule once and uses it from both.
   - Scope: within S0006 of `feature.md` (decisions 14 and 18, the human's answer 32 (b)). The leave for the earlier tests is decision 26, which the story cites. It changes no test beyond that leave and has nothing from "Out of scope".
