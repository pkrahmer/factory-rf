# The documents describe the stage environment

## Description

Every story of this feature left its part in the documents through its docs criterion: the new guide file `docs/project-guide/stage-environment.md` grew section by section, the operator guide gained the settings and the preflight items of a `container` instance, the decision log its entry, the write-guard guide its sentence on the undo. This story is the sweep at the end, as the brief's requirement 10 asks for: the documenter reads the four documents and the guide file against the code as it is after S0011 and makes them whole and true in one pass: the guide file has the sections in the order of the cycle, with the settings and the preflight at the end; the operator guide's sections say the same as the code; the decision entry names the date, the design, what the take keeps from the undo and what F0044 will remove; and `README.md`, written for the newcomer, says in one paragraph that the factory runs in two stage environments. No code and no test changes; `make documents` passes. What stays: every sentence that is already true.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template or an agent file. The documenter changes `README.md`, `docs/operator-guide.md`, `docs/project-guide/README.md`, `docs/project-guide/stage-environment.md`, `docs/project-guide/write-guard.md` and `docs/decisions.md`, as the docs criterion says. The tester writes `tests/test_documents_stage_environment.py`, which reads the documents (as `tests/domain/test_documents_guide_files.py` reads them) and pins criteria 1 to 4.

## Acceptance criteria

1. `docs/project-guide/stage-environment.md` has exactly these `##` sections, in this order: *The cycle*, *The snapshots*, *The container runs*, *The fakes*, *The ZFS adapter*, *The podman adapter*, *The stage environment*, *The container environment*, *The agent's container*, *The take*, *The checks*, *The sync command*, *The settings and the wiring*, *The preflight*; its first line is a `#` title and its second non-blank line a sentence that names what it covers; and it names the words `inline` and `container`, `FACTORY_STAGE_ENVIRONMENT`, `/work`, `@base`, `TakeReport`, `stage_environment_of` and the timing line `stage environment: reset` at least once each.
2. `docs/project-guide/README.md`, *The files*, has one bullet for `stage-environment.md` that names every module the file describes: `factory.application.snapshots`, `factory.application.containers`, `factory.application.stage_environment`, `factory.application.take`, `factory.domain.containers`, `factory.adapters.fake_snapshots`, `factory.adapters.fake_containers`, `factory.adapters.zfs_snapshots`, `factory.adapters.podman_runs`, and its fourteen section names; and the bullet of `write-guard.md` says that the undo is the inline environment's take.
3. `docs/operator-guide.md` has, in *Configuration*, one table row for each of `FACTORY_STAGE_ENVIRONMENT`, `FACTORY_DATASET`, `FACTORY_WORKSPACE`, `FACTORY_STAGE_IMAGE`, `FACTORY_PODMAN` and `FACTORY_ZFS`; in *The preflight's items*, one table row for each of `podman`, `zfs`, `dataset` and `stage-image`; in *The factory log*, the line `stage environment: reset`; and no sentence that says the contract is three targets.
4. `docs/decisions.md` has the section *One snapshot instead of many layers*, which names `2026-10-24`, `planning/v1.2-plan.md`, `StageEnvironment`, `InlineEnvironment`, `ContainerEnvironment`, the refusal rule (`refusal`), `restore_state_and_journal` and `F0044`; and `README.md` names `FACTORY_STAGE_ENVIRONMENT` once in a paragraph for the newcomer.
5. Nothing under `src/`, `tests/` (but the one new test module), `image/`, `template/` or `claude/` changes; the coder ends with an entry saying so.
6. `make check` stays green.
7. docs: the documenter makes criteria 1 to 4 true and reads the whole guide file and the operator guide's sections *Configuration*, *The agent runtime*, *The preflight's items* and *The factory log* against the code after S0011, correcting any sentence that is no longer true (the inline environment's items and chain stay as they are: F0044 removes them, not this story); `docs/project-guide/README.md`, *The files*: the bullet of `stage-environment.md` complete as criterion 2 says; `docs/decisions.md`: the entry as criterion 4 says, and no other entry changes; `README.md`: one paragraph for the newcomer, that an instance runs its stages `inline` (in its own container, v1.1's way) or in a `container` environment (throwaway containers on a ZFS dataset, v1.2's way, set by `FACTORY_STAGE_ENVIRONMENT`), pointing to the operator guide. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c '^## ' docs/project-guide/stage-environment.md; grep -c 'stage-environment.md' docs/project-guide/README.md; grep -c 'three targets' docs/operator-guide.md docs/project-guide/processes-and-checks.md || true
```
Expect: four lines, `14`, `1`, `docs/operator-guide.md:0`, `docs/project-guide/processes-and-checks.md:0`

```bash
grep -cE '^\| `(FACTORY_STAGE_ENVIRONMENT|FACTORY_DATASET|FACTORY_WORKSPACE|FACTORY_STAGE_IMAGE|FACTORY_PODMAN|FACTORY_ZFS)` \|' docs/operator-guide.md; grep -cE '^\| `(podman|zfs|dataset|stage-image)` \|' docs/operator-guide.md; grep -c '^## One snapshot instead of many layers' docs/decisions.md; grep -c 'FACTORY_STAGE_ENVIRONMENT' README.md
```
Expect: four lines, `6`, `4`, `1`, `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
