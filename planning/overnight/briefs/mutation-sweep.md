# Brief: a full mutation sweep of factory-rf with triage (the human's word, 2026-10-19)

## Goal

No stage runs `make mutants` (F0031); mutation testing runs only as these sweeps, which the human starts when the machine is idle. Since F0032 a sweep may run `make mutants MODULES=factory.application MUTANTS_SECONDS=<s> MUTANTS_CHILDREN=2` in its copy instead of mutmut by hand; every run starts from a fresh `mutants/`, so two runs in one copy share no stats. Run mutmut over all of `src/factory/` once, then sort every surviving mutant (and every mutant that was not checked) into one of:

- **equivalent**: no test can tell it apart; say why in one line;
- **missing test**: a behaviour no test pins; name the module, the behaviour, and the test module it belongs in;
- **dead or redundant code**: the mutant survives because the code does nothing; name it;
- **slow or timed out**: say which, and whether it points at a real fault.

Group the missing tests into proposed stories, small enough for a coder's 40-minute `time_limit`, each one paragraph: the modules, the behaviours to pin as criteria, and the feature it fits (a new feature "the tests pin what mutation testing found" is fine).

## How

- Use a fresh copy of the repository in your temporary folder `C:/Users/pasca/AppData/Local/Temp/mutsweep`, with no `mutants/` folder copied in. A stale `mutants/` keeps an old `cost-record.schema.json` and fails `tests/domain/test_contract_login.py`; that is a known fault, not one to report. Leave out `image/secrets/`.
- Run mutmut as `pyproject.toml`'s `[tool.mutmut]` configures it (its `also_copy` and its deselected tests), with `paths_to_mutate` widened to `src/factory/`. Run it in a throwaway container of the image `factory-self-factory`: `MSYS_NO_PATHCONV=1 docker run --rm --network none --cpus 3 --entrypoint /bin/sh -v <copy>:/src factory-self-factory -c '...'`. Never use the running `factory-self-factory-1`, which is building a story beside you; mount no volume and no secret. Run as the image's own user; if `uv` needs a writable cache, point `UV_CACHE_DIR` into the copy.
- First count the mutants and time a sample module, then estimate the whole run. If the estimate is over 90 minutes, sweep the layers in the order `domain`, `application`, `contract`, `entry`, `adapters`, and stop at 90 minutes of mutmut. Say what was left.
- Use `mutmut results` and `mutmut show <name>` for the triage. Read the code and tests yourself; do not change them.

## Output

`C:/Dev/Projects/factory-rf/planning/overnight/mutation-sweep-2026-10-19.md`:
1. The run: the mutmut version, the modules swept, the time, and the counts by status per module.
2. A triage table: mutant, module and line, status, class, one-line reason.
3. The proposed stories.
4. What was not swept, and why.

## Not

No git commands in the repository; no network from your own commands; no sub-agents; no paid model call; no file other than the output and the temporary folder, which you remove at the end (if a removal is refused, say so); do not change the repository's code, tests or settings; never read a token or key file.

## Reply

The counts (killed, survived, not checked, timed out), the number of mutants per class, and the proposed stories in one line each.
