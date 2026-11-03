# The site file's example names the required keys and the defaults that job.sh uses

<!-- proposed by feature acceptance of 2026-11-03; refine before starting -->

## Description

`operator/site.env.example` is the operator's first copy of the site file (`site init` writes it) and, by `docs/operator-guide.md` (*The keys*), "the first place to look". Its comments were S0001's reading of the key names before any story used the keys, and no later story confirmed them. Today they contradict the code and the guide in two ways. First, eight keys that `site_job_keys` in `operator/lib/site.sh` requires, so that `job.sh create` refuses without them and `site check` fails `keys`, are marked `Optional`: `SITE_PROXY`, `SITE_NO_PROXY`, `SITE_INSTANCE`, `SITE_CODE_REF`, `SITE_MODEL_BASE_URL`, `SITE_LOGIN_URL`, `SITE_LOGIN_SCOPE` and `SITE_LOGIN_CLIENT_ID`. Second, six defaults are not the ones `job.sh` uses: CPU 4 (`job.sh` uses 8), memory 16Gi (32Gi), timeout 24h (14400), idle minutes 30 (60), and the two prices "no cost record" (`0`). The `SITE_SANITISE_RULES` comment also says "the default is none", where `sanitise` reads `sanitise.rules` beside the site file. An operator who deletes an "optional" line gets a job of another size without a word. This story rewrites those comments so that each says what the code does, and pins the agreement with a test. The example's values stay as they are. So do the other comments and the code. Open for refinement: the example's `SITE_TIMEOUT=24h` against the guide's "in seconds". Confirm that `gcloud run jobs create --task-timeout` takes a duration such as `24h`; if it does not, the example's value becomes `86400`.

## Interface

`operator/site.env.example` (the comments only; every `SITE_*=value` line stays):

- Each key's comment line is the line directly above it. Its last sentence is one of: `Required.` (`SITE_REPOSITORY`, `SITE_CHECKOUT`); `Required for a job.` (exactly the 18 keys of `site_job_keys` in `operator/lib/site.sh`); or `Optional; the default is <default>.` (every other key).
- The new comment lines, word for word:
  - `# The proxy through which the job and its tools reach the network. Required for a job.`
  - `# The hosts reached without the proxy, comma-separated: the model API's host, never a code host. Required for a job.`
  - `# The factory instance's name in the job: letters, digits, '.', '_' and '-'. Required for a job.`
  - `# The branch or tag of the factory's code the job runs. Required for a job.`
  - `# The model provider's API. Required for a job.`
  - `# The login service that issues the model provider's tokens. Required for a job.`
  - `# The scope asked of the login service. Required for a job.`
  - `# The client id given to the login service. Required for a job.`
  - `# The model's price per million input tokens, in dollars. Optional; the default is 0.`
  - `# The model's price per million output tokens, in dollars. Optional; the default is 0.`
  - `# The job's CPUs. Optional; the default is 8.`
  - `# The job's memory. Optional; the default is 32Gi.`
  - `# The job's task timeout, as gcloud takes it (seconds, or a duration such as 4h). Optional; the default is 14400.`
  - `# The idle minutes after which the job ends itself. Optional; the default is 60.`
  - `# The file of rules that sanitise what leaves the site, absolute or relative to the site file's folder. Optional; the default is sanitise.rules beside the site file.`

Tests: `tests/test_operator_site_example.py`, with the helpers of `tests/operator_support.py` and `tests/operator_job_support.py`. The list of required keys is read from `operator/lib/site.sh` by sourcing it (`$site_job_keys`), not copied into the test.

## Acceptance criteria

1. The last sentence of each key's comment line in `operator/site.env.example`, as rows of one parametrized test over every key of the example: `Required.` for `SITE_REPOSITORY` and `SITE_CHECKOUT`; `Required for a job.` for each key of `site_job_keys`; and a sentence that starts with `Optional; the default is` for each of the other 11 keys (`SITE_API_URL`, `SITE_TOKEN_CMD`, `SITE_IMPERSONATE`, `SITE_MODEL_INPUT_COST`, `SITE_MODEL_OUTPUT_COST`, `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT`, `SITE_IDLE_MINUTES`, `SITE_RESET_REPOSITORY`, `SITE_SANITISE_RULES`). A key of `site_job_keys` whose comment says `Optional` fails its row, and so does an optional key whose comment says `Required for a job.`.
2. The default named in the comment of `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT` and `SITE_IDLE_MINUTES` equals what `job.sh create --dry-run` puts in its call when the key's line is left out of a site file copied from the example: `--cpu=8`, `--memory=32Gi`, `--task-timeout=14400` and `FACTORY_IDLE_SHUTDOWN_MINUTES=60` in the env list. One row per key; a comment that names another value fails its row.
3. The default named in the comments of `SITE_MODEL_INPUT_COST` and `SITE_MODEL_OUTPUT_COST` (`0`) equals the price in the `provider.json` that the job's wrapper writes when the key's line is left out, read back as S0005's tests read it. One row per key.
4. The comment of `SITE_SANITISE_RULES` names `sanitise.rules beside the site file` as its default.
5. Every `SITE_*=value` line of the example is unchanged: `site show` on a copy of the example prints `=set` for every key, in the same order as before.
6. `make check` stays green.
7. docs: `docs/operator-guide.md`, *The site file*: drop "the stories to come make the other keys live" from its intro. In *The keys*, replace "The defaults are those of the example's comments and are confirmed as the stories that read each key land" with a sentence saying that the example's comments and this table name the same required keys and defaults. Make the `SITE_TIMEOUT` row say what format the value takes (seconds, or a duration as gcloud takes it). `README.md`, the project guide and `docs/decisions.md`: none, because nothing changes for them.

## Smoke test

```bash
grep -c 'Required for a job\.$' operator/site.env.example
grep -E "^# The job's (CPUs|memory)\." operator/site.env.example
```

Expect: `18`, then the two lines `# The job's CPUs. Optional; the default is 8.` and `# The job's memory. Optional; the default is 32Gi.`

## Journal
