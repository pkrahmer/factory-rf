---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 498
comments_read: [6579796948]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-02T14:36:36.012272Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-02T13:59:55.897168Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-02T13:59:55.903371Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-02T14:00:26.870091Z'
  stage: intake
  run: 39b8ba91cb804b94abdf8b4d47be9552
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-02T14:35:34.389241Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-02T14:35:52.476184Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-02T14:36:15.112672Z'
  stage: intake
  run: 63ffc82feb864f459b70b4a35ca8ed39
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-02T14:36:36.012272Z'
  stage: tests
---

# A site file holds an operator's own values and one loader reads it

## Description

Everything an operator needs to run the factory in a job and to drive it is a value that belongs to one site: a project, a region, a proxy, the names of secrets, two repositories, a token command. This story gives those values one home, a plain file `site.env` outside every repository, and one loader that every later script uses. The file is a list of `SITE_NAME=value` lines that is only ever read, never executed; its place is `$FACTORY_SITE`, else the operator's configuration folder; the loader refuses a file that lies inside a git repository, and `site init` refuses to write one there, because the file is where company values go. The story adds `operator/site.env.example` (every key with a made-up value and a comment), the loader `operator/lib/site.sh`, and the command `operator/bin/site` with `path`, `init`, `show` and `get`. It does not read the file for any job or hosting purpose (S0003 to S0008 do), does not add `site check` (S0009), and changes no existing script.

## Interface

`operator/lib/site.sh` (POSIX `sh`, sourced; no output of its own on success)

```sh
site_path             # prints the site file's path
site_load             # reads the file; exports every SITE_ value; exit 0, 1, 2 or 3
site_require NAME...  # exit 0, or 2 naming every NAME that is unset or empty
```

- `site_path` prints `$FACTORY_SITE` when it is set and not empty, else `$XDG_CONFIG_HOME/kumpel/site.env` when `XDG_CONFIG_HOME` is set and not empty, else `$HOME/.config/kumpel/site.env` (the folder the skill's `settings.json` already uses: one folder for the machine's own values, feature decision 11).
- The file's lines are blank, a comment (first non-blank character `#`), or `SITE_NAME=value`. `NAME` is capitals, digits and `_`, at least one character; there is no space around the `=`. The value is everything after the first `=`, with trailing whitespace removed; one pair of single or double quotes around the whole value is removed and keeps the whitespace inside. A quote that is not matched stays in the value.
- A value is stored literally: `$`, a backtick, `;` and `\` have no meaning, and nothing in the file is ever executed.
- A line that is none of the three kinds, or whose key is not `SITE_` followed by the name, is a fault: `site_load` exports nothing from the file, prints `site: <path>:<line>: not a KEY=value line` or `site: <path>:<line>: <key> is not a SITE_ key` to standard error and returns 2.
- A variable that is already set in the environment keeps its value (the file does not override it); a variable the file sets is exported.
- A missing file: `site: no site file at <path>; run: site init` and 1. A file inside a git work tree (`git -C <its folder> rev-parse --is-inside-work-tree` answers true): `site: <path> lies in a git repository; keep the site file outside every repository` and 3.
- `site_require A B` prints `site: missing SITE_A, SITE_B in <path>` (only those that are unset or empty, in the order given) and returns 2.

`operator/bin/site` (`sh`, runs `site.sh`)

```sh
site path             # prints the path
site init             # writes the example to the path, mode 0600
site show             # one line per key of the example: SITE_X=set or SITE_X=unset
site get SITE_X       # prints the value
```

- `site show` loads the site and prints, in the example's order, `SITE_X=set` or `SITE_X=unset` for every key the example names; a key set to the empty string is `unset`. It never prints a value.
- `site get SITE_X` prints the value and a newline; when it is unset or empty it prints `site: SITE_X is not set` to standard error and exits 1.
- `site init` makes the file's folder, copies the example to the path with mode 0600 and prints `site: wrote <path>; edit it, then run: site check`; when the file exists it prints `site: <path> exists; not overwritten` to standard error and exits 1.
- `site show` and `site get` print `site_load`'s message to standard error, nothing to standard output, and exit with its status (1, 2 or 3).
- `site init` for a path inside a git work tree (same test as the loader's) prints `site: <path> lies in a git repository; keep the site file outside every repository` to standard error, writes nothing (no folder, no file) and exits 3.
- Any other command, `site get` with no name and `site get` with a name that does not start with `SITE_` included, prints `usage: site path | init | show | get SITE_X` to standard error and exits 2.

`operator/site.env.example`: the keys below, in this order, each with a comment line of one or two sentences directly above it that says what it is, whether it is required and its default, and a made-up value (a URL uses `example.invalid`, a repository `owner/repo`, a path `/path/to/...`). Later stories add keys at the end; none changes the first thirty-one.

`SITE_REPOSITORY`, `SITE_CHECKOUT`, `SITE_API_URL`, `SITE_TOKEN_CMD`, `SITE_PROXY`, `SITE_NO_PROXY`, `SITE_PROJECT`, `SITE_REGION`, `SITE_IMPERSONATE`, `SITE_RUN_AS`, `SITE_CONNECTOR`, `SITE_JOB`, `SITE_INSTANCE`, `SITE_REPOSITORY_URL`, `SITE_CODE_URL`, `SITE_CODE_REF`, `SITE_HOSTING_SECRET`, `SITE_MODEL_SECRET`, `SITE_MODEL_BASE_URL`, `SITE_MODEL`, `SITE_MODEL_INPUT_COST`, `SITE_MODEL_OUTPUT_COST`, `SITE_LOGIN_URL`, `SITE_LOGIN_SCOPE`, `SITE_LOGIN_CLIENT_ID`, `SITE_CPU`, `SITE_MEMORY`, `SITE_TIMEOUT`, `SITE_IDLE_MINUTES`, `SITE_RESET_REPOSITORY`, `SITE_SANITISE_RULES`.

Tests: `tests/test_operator_site.py` (the scripts are outside the layers), running the scripts as child processes in `tmp_path` with `FACTORY_SITE`, `XDG_CONFIG_HOME` and `HOME` set to folders there; a shared helper that runs a script with a given environment lives in a new `tests/operator_support.py`.

## Acceptance criteria

1. `site_path` prints the path in the order of the Interface, as rows of one parametrized test: `FACTORY_SITE` set; unset with `XDG_CONFIG_HOME` set; both unset (under `$HOME/.config`); `FACTORY_SITE` empty with `XDG_CONFIG_HOME` set (the empty one is ignored).
2. `site_load` exports `SITE_A=x` for the line `SITE_A=x`, skips blank lines, comment lines and an indented comment line, and returns 0.
3. Values, as rows of one parametrized test: `SITE_A=a b` gives `a b`; `SITE_A="a b "` gives `a b ` (quotes removed, inner whitespace kept); `SITE_A='x'` gives `x`; `SITE_A=a  ` (trailing spaces) gives `a`; `SITE_A="x` gives `"x`; `SITE_A=` gives the empty string; `SITE_A=a=b` gives `a=b`.
4. A value is never interpreted: the lines `SITE_A=$(touch MARK)`, `` SITE_A=`touch MARK` `` and `SITE_A=$HOME;touch MARK` export those exact texts and no file `MARK` exists afterwards (three rows).
5. A faulty file exports nothing and returns 2, as rows of one parametrized test: a file whose first line is good and whose second is `plain text` (message `not a KEY=value line` with the line number 2); `OTHER=1` (`OTHER is not a SITE_ key`); `site_a=1` (lower case); `SITE_A = 1` (spaces around the `=`); `SITE_=1` (a key with no name).
6. A variable already in the environment keeps its value: with `SITE_A=env` exported and the line `SITE_A=file`, `SITE_A` is `env` and another key of the file is exported.
7. A missing file returns 1 with `site: no site file at <path>; run: site init`.
8. A file inside a git work tree (`git init` in a folder of `tmp_path`, the file in it) returns 3 with the message of the Interface; the same file in a folder that is not a work tree loads.
9. `site_require` with `SITE_A` and `SITE_B` set returns 0 and prints nothing; with `SITE_B` unset and `SITE_C` empty it prints `site: missing SITE_B, SITE_C in <path>` and returns 2; the names come in the order given.
10. `site show` prints one line per key of `operator/site.env.example` in its order, `set` for a key with a non-empty value and `unset` for an absent key and for a key set to the empty string; a value that contains the text `SECRETMARK` never appears in its output.
11. `site get SITE_A` prints the value and exits 0 for a set key; for an unset key and for an empty one it prints `site: SITE_A is not set` to standard error, nothing to standard output, and exits 1.
12. `site init` into a folder that does not exist makes the folder, writes a file equal to the example with mode 0600 and prints the line of the Interface; a second `site init` leaves the file byte for byte as it was, prints `site: <path> exists; not overwritten` and exits 1.
13. `site` with no argument, with `frobnicate`, with `get` and no name, and with `get HOME` print the usage line to standard error, nothing to standard output, and exit 2 (four rows).
14. The example file: it loads without a fault; every `SITE_` key line has a comment line directly above it; its keys, in order, begin with the thirty-one of the Interface; no value contains a string that is not made up (a test over its text: every `://` is followed by a host that ends in `example.invalid`, `localhost` or an IP address of `192.0.2.`).
15. `site show` and `site get SITE_A` with a failing load, as rows of one parametrized test (two commands by three loads): a missing file (status 1), a faulty file (status 2) and a file in a git work tree (status 3) print the loader's message of the Interface to standard error, nothing to standard output, and exit with that status.
16. `site init` for a path inside a git work tree prints the message of the Interface to standard error, creates neither the folder nor the file, and exits 3; for the same path outside a work tree it writes the file (the two sides as rows of one parametrized test).
17. `make check` stays green.
18. docs: `docs/operator-guide.md` gets a section *The site file* (what it is, its place and `FACTORY_SITE`, the format and that it is never executed, the rule that it lies outside every repository, `site init`, `show` and `get`, and the keys by the use that reads them as far as the stories to come make them known: a table of key, meaning, default); `README.md` and the other documents: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_PROJECT=demo-project\n# a comment\nSITE_REGION="us-example1"\n' > "$d/site.env"
FACTORY_SITE="$d/site.env" sh operator/bin/site show | sed -n '1p;7p;8p;9p'
```

Expect: four lines, `SITE_REPOSITORY=unset`, `SITE_PROJECT=set`, `SITE_REGION=set` and `SITE_IMPERSONATE=unset`.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
FACTORY_SITE="$d/new/site.env" sh operator/bin/site init
stat -c %a "$d/new/site.env"
FACTORY_SITE="$d/new/site.env" sh operator/bin/site init; echo "exit $?"
```

Expect: four lines: `site: wrote <the file's path>; edit it, then run: site check`, then `600`, then `site: <the file's path> exists; not overwritten` and `exit 1`.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_A=$(echo ran)\n' > "$d/site.env"
FACTORY_SITE="$d/site.env" sh operator/bin/site get SITE_A
```

Expect: one line, `$(echo ran)`.

## Journal

1. 2026-11-02 human: created.
2. factory: started intake as vm.
3. intake: Format check: passed. Three questions; everything else I checked is fine (see the end).

   1. `site show` and `site get SITE_X` call `site_load`, which can return 1 (missing file), 2 (faulty file) or 3 (file in a git work tree). The Interface does not say what these two commands do then, and no criterion tests it. Do they print `site_load`'s message to standard error and exit with its status? I would choose yes. I would add one criterion with rows for the three failing loads, for `show` and for `get`: the message of the Interface on standard error, nothing on standard output, and the status 1, 2 or 3. As written, two coders could read this two ways and both would pass the tests.

   2. `site get` with no name, or with a name that does not start with `SITE_` (for example `site get HOME`), is not specified. Should it print the usage line and exit 2, like any other malformed command? I would choose yes, and add the case as rows to criterion 13. Without this, `site get HOME` could print the value of an unrelated environment variable.

   3. `site path` and `site init` do not load the file, but `site init` may write inside a git work tree, and the loader will refuse that file later. Should `init` refuse a path inside a git work tree (message and exit status to be named, for example the loader's message and 3), or write it and leave the refusal to the loader? I would choose to refuse, because the example is the company's values-to-be. If you choose refuse, it needs a criterion with both sides: in a work tree it refuses and writes nothing, outside it writes.

   Checked and fine:
   - Interface: it names concrete files and functions. All 31 keys are counted and in order, and the smoke test positions 1, 7, 8 and 9 match REPOSITORY, PROJECT, REGION and IMPERSONATE.
   - Criteria: otherwise each is testable by one test, and the rules have both sides (the faulty-line kinds, env wins, missing file, git work tree or not, empty or unset, init twice).
   - Smoke test: the three blocks run as written. No pytest is involved, and each `Expect:` line is checkable.
   - Architecture: the scripts lie outside the layers, which the Interface says. `operator/*` is already in the coder's write paths in `factory/pipeline.yml`, as the feature asks.
   - Scope: the story stays within the feature's S0001 scope (site file, loader, example, `path`, `init`, `show` and `get`). It adds no `site check`, and no existing script or test changes.
4. 2026-11-02 human: 1. Yes, as you propose: `site show` and `site get` print `site_load`'s message to standard error, nothing to standard output, and exit with its status (1, 2 or 3). Add the criterion with rows for the three failing loads, for both commands.
   2. Yes: `site get` with no name, or with a name that does not start with `SITE_`, prints the usage line and exits 2; add the cases as rows of criterion 13.
   3. Refuse: `site init` for a path inside a git work tree prints the loader's message (`site: <path> lies in a git repository; keep the site file outside every repository`), writes nothing and exits 3 (decision 2). Add the criterion with both sides: in a work tree it refuses and writes nothing, outside it writes.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: concrete files and functions (`operator/lib/site.sh`: `site_path`, `site_load`, `site_require`; `operator/bin/site`: `path`, `init`, `show`, `get`). All 31 keys are named in order, and the smoke test's positions 1, 7, 8 and 9 match REPOSITORY, PROJECT, REGION and IMPERSONATE. I carried in the human's answers (journal entry 4) and wrote exactly those: `show` and `get` print the loader's message to stderr and exit with its status; `get` with no name or a non-`SITE_` name gives the usage line and exit 2; `init` in a git work tree prints the loader's message, writes nothing and exits 3. I also added half a clause to the Description (init refuses in a work tree).
   - Criteria: each is testable by one test function, and each rule has both sides. Criterion 13 now has four rows (the two new usage cases from answer 2). New criterion 15 covers show and get against the three failing loads (answer 1). New criterion 16 covers init inside and outside a work tree (answer 3). They stand before the closing two, which are now 17 (`make check`) and 18 (docs).
   - Smoke test: the three blocks run as written. No pytest is involved, and each `Expect:` line is checkable.
   - Architecture: the scripts lie outside the layers, as the Interface says. `operator/*` is already in the coder's write paths, as the feature asks. The tests go in `tests/test_operator_support.py`'s sibling `tests/test_operator_site.py` with the helper in `tests/operator_support.py`, which `CLAUDE.md` allows.
   - Scope: within the feature's S0001 scope. It adds no `site check` and changes no existing script or test.
7. factory: started tests as vm.
