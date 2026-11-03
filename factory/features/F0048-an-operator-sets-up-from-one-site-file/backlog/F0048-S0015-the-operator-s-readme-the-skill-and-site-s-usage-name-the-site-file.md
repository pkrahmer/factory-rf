# The operator's README, the skill and site's usage name the site file

<!-- proposed by feature acceptance of 2026-11-03; refine before starting -->

## Description

Three texts in `operator/` still describe the setup from before the site file. `operator/README.md`'s *Installing* says that "the first act of the skill asks for the repository and the checkout and writes `~/.config/kumpel/settings.json`", and its *Needs* asks for "`gh` logged in". Since S0001 and S0004, though, the site file gives the repository and the checkout, and `SITE_TOKEN_CMD` replaces the `gh` login. The guide's step 9 (*Setting up an operator's machine*) sends the reader to exactly this *Installing* section. `operator/skill/kumpel/SKILL.md` (*Before anything*, step 1) tells the agent to ask the human for the repository and the checkout and does not name the site file. And `operator/bin/site` accepts `check` (S0009) while its usage line still reads `usage: site path | init | show | get SITE_X`. This story brings the three in line with what the commands do. It changes no other line of the skill, its references or its switches, and no behaviour of `site` except the usage text. Open for refinement: criterion 3 changes the `USAGE` constant of `tests/test_operator_site.py`, which S0001 wrote. That needs the human's leave in `feature.md` (*The human's changes*); without it, drop criterion 3 and the usage line from the Interface.

## Interface

`operator/bin/site`: the usage line becomes `usage: site path | init | show | get SITE_X | check`, printed to standard error with exit 2 in every case where it is printed today. `site check` with an argument keeps `usage: site check`.

`operator/README.md`:

- *Installing* says, in this order: write the site file (`sh operator/bin/site init`, fill in the values, `sh operator/bin/site check`); install the skill and the command as today. When the site file gives `SITE_REPOSITORY` and `SITE_CHECKOUT`, `settings.json` holds only the switches (`sh scripts/settings.sh init` takes no argument); otherwise the skill asks for both. It names `docs/operator-guide.md`, *Setting up an operator's machine*.
- *Needs* names `git`, `curl`, `python3` and a POSIX shell, and a token from `SITE_TOKEN_CMD` or, without it, a `gh` login; `gcloud` for an instance in a Cloud Run job. The words "`gh` logged in for the project's GitHub" go.

`operator/skill/kumpel/SKILL.md`, *Before anything*, step 1: `sh scripts/settings.sh show` answers the repository and the checkout from the site file first (`SITE_REPOSITORY`, `SITE_CHECKOUT`). When it has no settings, run `sh scripts/settings.sh init` if the site file gives both. Otherwise ask the human for the two values and suggest putting them into the site file. Every other line of `SKILL.md` stays.

Tests: `tests/test_operator_site.py` (the `USAGE` constant, with the leave named above) and a new `tests/test_operator_texts.py` over the two texts.

## Acceptance criteria

1. `operator/README.md`'s *Installing* section contains `site init` and `site check`, and contains no sentence saying that the skill's first act asks for the repository and the checkout. A row with today's text fails.
2. `operator/README.md`'s *Needs* section contains `SITE_TOKEN_CMD` and does not contain `` `gh` logged in ``.
3. `sh operator/bin/site` with no command, with `bogus`, and with `get` alone each print `usage: site path | init | show | get SITE_X | check` on standard error and exit 2 (rows of S0001's usage test); `site check extra` still prints `usage: site check` and exits 2.
4. `operator/skill/kumpel/SKILL.md`'s *Before anything* step 1 names `SITE_REPOSITORY`, `SITE_CHECKOUT` and the site file. The other numbered steps and the loop are word for word as before, which the test checks against a copy of today's text after step 1.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, *The `site` command*: the usage line with `check`. Step 9 of *Setting up an operator's machine* stays true as written. `README.md`, the project guide and `docs/decisions.md`: none, because nothing changes for them.

## Smoke test

```bash
sh operator/bin/site 2>&1; echo "exit $?"
grep -c 'site init' operator/README.md
```

Expect: `usage: site path | init | show | get SITE_X | check`, then `exit 2`, then a number of at least `1`.

## Journal
