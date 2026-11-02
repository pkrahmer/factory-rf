# A site file holds an operator's own values and one loader reads it

## Description

Everything an operator needs to run the factory in a job and to drive it is a value that belongs to one site: a project, a region, a proxy, the names of secrets, two repositories, a token command. This story gives those values one home, a plain file `site.env` outside every repository, and one loader that every later script uses. The file is a list of `SITE_NAME=value` lines that is only ever read, never executed; its place is `$FACTORY_SITE`, else the operator's configuration folder; the loader refuses a file that lies inside a git repository, because the file is where company values go. The story adds `operator/site.env.example` (every key with a made-up value and a comment), the loader `operator/lib/site.sh`, and the command `operator/bin/site` with `path`, `init`, `show` and `get`. It does not read the file for any job or hosting purpose (S0003 to S0008 do), does not add `site check` (S0009), and changes no existing script.

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
- Any other command prints `usage: site path | init | show | get SITE_X` to standard error and exits 2.

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
13. `site` with no argument and with `frobnicate` print the usage line to standard error and exit 2 (two rows).
14. The example file: it loads without a fault; every `SITE_` key line has a comment line directly above it; its keys, in order, begin with the thirty-one of the Interface; no value contains a string that is not made up (a test over its text: every `://` is followed by a host that ends in `example.invalid`, `localhost` or an IP address of `192.0.2.`).
15. `make check` stays green.
16. docs: `docs/operator-guide.md` gets a section *The site file* (what it is, its place and `FACTORY_SITE`, the format and that it is never executed, the rule that it lies outside every repository, `site init`, `show` and `get`, and the keys by the use that reads them as far as the stories to come make them known: a table of key, meaning, default); `README.md` and the other documents: none.

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
