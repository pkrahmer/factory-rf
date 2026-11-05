# An operator's site and machine

A topic of the [operator guide](README.md).

## The site file

The values that belong to one site (a project, a region, a proxy, the names of secrets, two repositories, a token command) live in one plain file, `site.env`, and one loader, `operator/lib/site.sh`, reads it for every operator script. The file is where company values go, so it lies outside every repository. `operator/job/job.sh` reads it for the job (*Creating the job*), and the skill's scripts use the hosting library (*The token source*).

### Its place

The path is `$FACTORY_SITE` when that is set and not empty, else `$XDG_CONFIG_HOME/kumpel/site.env`, else `$HOME/.config/kumpel/site.env` (the folder the skill's `settings.json` already uses). `site path` prints it.

The loader refuses a file that lies inside a git work tree (status 3), and `site init` refuses to write one there. Keep the file in your own configuration folder, never in a checkout.

### The format

The file is a list of lines, each blank, a comment (the first non-blank character is `#`) or `SITE_NAME=value`:

- `NAME` is capitals, digits and `_`, at least one character. A space or a tab before the `=` or directly after it is a fault (`SITE_PROXY= http://p` would otherwise carry a leading space into the value); a space inside a value, or at its end, is kept as before.
- The value is everything after the first `=`, with trailing whitespace removed. One pair of single or double quotes around the whole value is removed and keeps the whitespace inside; a quote that is not matched stays.
- A value is stored literally: `$`, a backtick, `;` and `\` mean nothing, and the file is never executed. `SITE_A=$(touch x)` is the text `$(touch x)`.
- A variable that is already set in the environment, even to the empty string, keeps its value. Of a key that appears twice, the first line wins.
- A line of another kind, or a key that is not `SITE_` followed by a name, is a fault: nothing is exported from the file, the message `site: <path>:<line>: ...` goes to standard error, and the status is 2.

### The `site` command

Run it as `sh operator/bin/site`:

| Command | What it does |
|---|---|
| `site path` | prints the path |
| `site init` | makes the folder and writes `operator/site.env.example` to the path, mode 0600; it never overwrites (status 1) |
| `site show` | one line `SITE_X=set` or `SITE_X=unset` for each key of the example, in its order; a key set to the empty string is `unset`; never a value |
| `site get SITE_X` | prints the value; when it is unset or empty, `site: SITE_X is not set` and status 1 |
| `site check` | the read-only checks of a machine, one line each (see *Setting up an operator's machine*) |

`show` and `get` load the file first and pass on the loader's failure: status 1 for a missing file (`run: site init`), 2 for a fault, 3 for a file in a git work tree. Any other command line prints `usage: site path | init | show | get SITE_X | check` and exits 2; `site check` with an argument prints `usage: site check` and exits 2. `site init` prints `site: wrote <path>; edit it, then run: site check`.

```bash
export FACTORY_SITE="$HOME/.config/kumpel/site.env"
sh operator/bin/site init
sh operator/bin/site show | head -3
sh operator/bin/site get SITE_REPOSITORY
```

### The keys

`operator/site.env.example` holds every key with a comment and a made-up value; it is the first place to look. The table gives the same by the use that reads it. The example's comments and this table name the same required keys and the same defaults, and a test keeps them equal to what `operator/lib/site.sh` and `operator/job/job.sh` do.

| Key | Meaning | Default |
|---|---|---|
| `SITE_REPOSITORY` | the factory's repository, `owner/repo` | required |
| `SITE_CHECKOUT` | the local checkout of that repository | required |
| `SITE_API_URL` | the hosting service's API | GitHub's public API |
| `SITE_TOKEN_CMD` | the command that prints a hosting-service token | `gh auth token` |
| `SITE_PROXY` | the proxy for the job and its tools | required for a job |
| `SITE_NO_PROXY` | hosts reached without the proxy, comma-separated | required for a job |
| `SITE_PROJECT` | the cloud project of the job | required for a job |
| `SITE_REGION` | the cloud region of the job | required for a job |
| `SITE_IMPERSONATE` | the service account the operator's cloud commands impersonate | your own login |
| `SITE_RUN_AS` | the service account the job runs as | required for a job |
| `SITE_CONNECTOR` | the network connector the job's traffic leaves through | required for a job |
| `SITE_JOB` | the name of the job | required for a job |
| `SITE_INSTANCE` | the instance's name in the job | required for a job |
| `SITE_REPOSITORY_URL` | the clone URL of the factory's repository | required for a job |
| `SITE_CODE_URL` | the clone URL of the factory's own code | required for a job |
| `SITE_CODE_REF` | the branch or tag of the code the job runs | required for a job |
| `SITE_HOSTING_SECRET` | the secret that holds the hosting-service token | required for a job |
| `SITE_MODEL_SECRET` | the secret that holds the model provider's key | required for a job |
| `SITE_MODEL_BASE_URL` | the model provider's API | required for a job |
| `SITE_MODEL` | the model the agents run on | required for a job |
| `SITE_MODEL_INPUT_COST` | price per million input tokens, in dollars | `0` |
| `SITE_MODEL_OUTPUT_COST` | price per million output tokens, in dollars | `0` |
| `SITE_LOGIN_URL` | the login service that issues the provider's tokens | required for a job |
| `SITE_LOGIN_SCOPE` | the scope asked of the login service | required for a job |
| `SITE_LOGIN_CLIENT_ID` | the client id given to the login service | required for a job |
| `SITE_CPU` | the job's CPUs | 4 |
| `SITE_MEMORY` | the job's memory | 16Gi |
| `SITE_TIMEOUT` | the job's task timeout, as `gcloud run jobs --task-timeout` takes it: seconds, or a duration such as `4h` | 86400 (24 hours) |
| `SITE_IDLE_MINUTES` | idle minutes after which the job ends itself | 30 |
| `SITE_RESET_REPOSITORY` | the repository a trial resets, `owner/repo`; `reset-to-tag.sh` acts only when it equals `SITE_REPOSITORY` (see *Repeating a trial*) | none |
| `SITE_SANITISE_RULES` | the file of rules that sanitise what leaves the site | `sanitise.rules` beside the site file |

The skill's scripts (`operator/skill/kumpel/scripts/`) read `SITE_REPOSITORY` and `SITE_CHECKOUT` from the site file, or from the environment when it sets them, before they look at the skill's `settings.json`. When the site gives both, `settings.json` holds only the switches (`merge`, `answer`, `start_next`) and `settings.sh init` takes no argument; when it gives either one short, `init` needs `<owner/name> <checkout>` and the JSON file keeps them. A missing or faulty site file does not stop `settings.sh`: the JSON file answers, and a faulty file's message goes to standard error. The scripts reach the API and git only through `hosting_repo_api` and `hosting_git`, so a script with neither a token command nor a `gh` login stops with `hosting: the token command failed; see SITE_TOKEN_CMD in the site file`.

### The token source

`operator/lib/hosting.sh` is the shell library that talks to the code host: the REST API (`hosting_api`, and `hosting_repo_api` for `/repos/$SITE_REPOSITORY...`) and git over HTTPS (`hosting_git`). Source it after `operator/lib/site.sh`; it loads the site file itself when no `SITE_` value is loaded yet. It replaces the `gh` program for those two uses, whose login is the person's own and may not see the project's repository.

The token comes from one of two sources:

1. `SITE_TOKEN_CMD`, when it is set and not empty: a command that prints a token (a secret store, a keychain, any program). It runs as `sh -c "$SITE_TOKEN_CMD"`. The first line of its output is the token, with surrounding whitespace and a trailing carriage return removed. Its standard error is discarded.
2. Otherwise `gh auth token`, so a home setup with a logged-in `gh` needs no entry.

When the command exits non-zero, prints nothing (or only blank lines), or there is neither a command nor `gh`, the library prints `hosting: the token command failed; see SITE_TOKEN_CMD in the site file` and returns 4. The message never repeats what the command printed, because that may be an error text that holds a secret.

The token is never in an argument list, where `ps` shows it to every user of the machine. The API call gives `curl` its URL and headers, the token among them, as a configuration on standard input (`--config -`). `hosting_git` gives git a `http.extraHeader` and an empty `credential.helper` through the `GIT_CONFIG_*` environment variables, and sets `GIT_TERMINAL_PROMPT=0`. The header is sent to every http(s) remote that git call contacts. The token is written to no file. `curl` 7.63 or later is needed; Debian 12 has 7.88.

`SITE_API_URL` is the base of the API calls (default `https://api.github.com`; a trailing `/` is removed), for a GitHub Enterprise server.

Return codes of `hosting_api`: 0 for an HTTP status from 200 to 299 (the body is printed); 22 for any other status, with `hosting: <METHOD> <PATH>: <status> <message>` on standard error (the body's JSON `message`, else its first 100 characters), or `no answer` when `curl` gave no status; 4 when there is no token. `hosting_repo_api` returns 2 when `SITE_REPOSITORY` is unset. `hosting_git` returns git's own status, or 4 without running git.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_TOKEN_CMD=printf "  abc  "\n' > "$d/site.env"
FACTORY_SITE="$d/site.env" sh -c '. operator/lib/site.sh; . operator/lib/hosting.sh; hosting_token'
```

This prints `abc`.

### Sanitising what leaves the machine

A log, a result or a note that goes from your machine into a repository must not carry the site's names: its domain, its project, its repository, a token. `sh operator/bin/sanitise` removes them and proves that a file has none left. It needs the site file (without one it prints the site's own message and exits 2).

```sh
sanitise                    # standard input to standard output, rules applied
sanitise check FILE...      # exit 0 and "sanitise: clean", or 1 naming file:line, or 3
```

Any other call prints `usage: sanitise < raw > clean | sanitise check FILE...` and exits 2.

#### The rules file

The rules file is `$SITE_SANITISE_RULES` when that is set (in the environment, which wins, or in the site file), else `sanitise.rules` in the folder of the site file. A relative path is relative to the site file's folder. The patterns are your company's names, so the file is the site's: keep it beside the site file and never put it into a repository. The repository holds the mechanism only.

Each line is blank, a comment (`#`) or one of three rules:

| Line | Meaning |
|---|---|
| `PATTERN => REPLACEMENT` | replace every match of the pattern |
| `drop: PATTERN` | remove every line that matches |
| `leak: PATTERN` | the check reports a match; the filter leaves the text alone |

A pattern is a Python regular expression, applied with `re.sub`, case sensitive. The first ` => ` of a line splits it, and whitespace around both parts is removed. The replacement is literal text, except that `\1` to `\99` stand for that group of the pattern (two digits are one number; a group that took no part in the match gives empty text). Every other backslash stays a backslash.

```
# the company's names
corp\.example\.invalid => <company-host>
(\d+)-secret => \1-x
drop: ^DEBUG
leak: internal-project
```

A line of another kind, an empty pattern, a pattern that is not a regular expression, or a replacement that names a group the pattern lacks stops the command with `sanitise: <path>:<line>: <reason>` and status 2. `check` stops the same way before it reads any file. Rules are numbered from 1 in file order, counting rule lines only, not blank lines or comments.

#### The filter

The filter applies the built-in rules first, then the site's in file order, line by line. The order of lines is kept, every line ends with a newline, and empty input gives empty output. The built-in rules are:

1. `builtin-1`: terminal escape sequences (`\x1b[31m` and the like) are removed.
2. `builtin-2`: `eyJ` followed by two more dot-separated base64url parts, each at least 10 characters, becomes `***JWT***`.
3. `builtin-3`: `ghp_`, `gho_`, `ghu_`, `ghs_` or `ghr_` followed by 20 or more letters or digits, and `github_pat_` followed by 20 or more letters, digits or `_`, become `***TOKEN***`.

Without a rules file the filter prints `sanitise: no rules file at <path>; only the built-in rules apply` to standard error once and goes on.

#### The check

`sanitise check FILE...` tests every line of every file against the built-in token patterns and every pattern of the rules file (the left side of `=>`, `drop:` and `leak:`). For each line and rule that matches it prints `<file>:<line>: <n>` once, where `<n>` is the rule's number, or `builtin-1`, `builtin-2` or `builtin-3`. It never prints the matched text, so its report is no leak. The exit status is:

| Status | Meaning |
|---|---|
| 0 | `sanitise: clean` |
| 1 | at least one match was reported |
| 2 | a rules-file fault, a wrong call, or a named file that does not exist (`sanitise: <file>: no such file`, and nothing else on standard output) |
| 3 | no rules file (`sanitise: no rules file at <path>; nothing to check against`) |

A filtered file passes the check against the same rules, unless a replacement itself matches a pattern.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_PROJECT=p\n' > "$d/site.env"
printf 'corp\\.example\\.invalid => <company-host>\n' > "$d/sanitise.rules"
export FACTORY_SITE="$d/site.env"
printf 'one\nat corp.example.invalid\n' > "$d/raw.txt"
sh operator/bin/sanitise < "$d/raw.txt" > "$d/clean.txt"; cat "$d/clean.txt"
sh operator/bin/sanitise check "$d/raw.txt" | sed "s|$d|<d>|"
sh operator/bin/sanitise check "$d/clean.txt" | sed "s|$d|<d>|"
```

This prints `one`, `at <company-host>`, then `<d>/raw.txt:2: 1`, then `sanitise: clean`.

## Repeating a trial

A trial repository can be set back to a starting point, so that a run is repeated from the same state. Tag the starting point once (`git tag starting-point <commit>` and push the tag), then run the skill's script:

```bash
sh operator/skill/kumpel/scripts/reset-to-tag.sh starting-point          # prints the plan, exits 1
sh operator/skill/kumpel/scripts/reset-to-tag.sh starting-point --yes    # does it
```

The script works through the hosting API alone and needs no checkout. It resolves the tag (an annotated tag is followed to its commit), then, in this order, closes every open pull request whose head branch starts with `work-item/` (`closed #<n>`), deletes every branch under `work-item/` (`deleted <branch>`) and moves `main` to the tag's commit by force (`moved main to <7 characters>`). Nothing else is touched: no other branch, no tag, no other pull request. Without `--yes` it prints the counts and the target (`would close 2 open work-item pull request(s)`, `would delete 3 work-item branch(es)`, `would move main to <commit>`), then `run again with --yes`, and exits 1. A reset that finds nothing to close or delete still moves `main`.

It refuses to run unless all three hold:

1. **`--yes` is given.** Anything else as the second argument is a usage error (exit 2).
2. **The site names the repository as resettable.** `SITE_RESET_REPOSITORY` is set and equals `SITE_REPOSITORY`, the repository the commands work on. The factory's own repository can therefore never be the target: it is not the trial repository. A difference exits 1 with `reset-to-tag.sh: <repository> is not the site's resettable repository`; an unset key exits 2 with the site loader's message (`site: missing SITE_RESET_REPOSITORY in <file>`).
3. **The tag exists.** A missing tag exits 1 with `reset-to-tag.sh: no tag <tag>`. Any other failure of the lookup prints the hosting client's message.

The force-push cannot be undone: the commits `main` held are no longer on any branch, and the closed pull requests and deleted branches are not restored. A failing call stops the script at that call with the hosting client's message and exit 1, so a half reset is visible: the lines printed so far are what was done. Run it again with `--yes` after fixing the cause. Only the first 100 open pull requests are listed (no paging).

The same skill folder merges a story: `merge.sh <pr> <id>` (see *A merge archives the story*). It refuses a pull request that is not open, is a draft, is not labelled `stage:approval` or is not `work-item/<id>`; merges with a merge commit; then polls the latest 20 commits of `main` for `work item <id>: merged, archived` every `KUMPEL_POLL_SECONDS` seconds (15) for at most `KUMPEL_ARCHIVE_WAIT` seconds (300). It prints `merged #<pr>` and `archived <id>` and exits 0; if the archive commit does not come in time it exits 1 with `merge.sh: merged, but no archive commit for <id> after <N> s`. Start the next story only after `archived`.

### Telling Kumpel's acts from the human's

The skill acts with the human's own token, so GitHub shows the human's account on everything it does. Kumpel therefore signs each act:

- **A comment** ends with a blank line, the line `— Kumpel, for the human who owns this project` and the marker `<!-- kumpel -->`. The skill posts only through `comment.sh <pr> <file>`, which adds the signature (once; a text that already ends with it is posted as it is) and prints `commented #<pr>`. The factory copies a comment's text into the journal, so the signature line is there too: a journal entry of the human that ends with it was written by Kumpel. A verdict is recognised by `<!-- kumpel verdict -->` anywhere in the newest comment, so the signature after it does not hide it from `status.sh`.
- **A start commit** (`start-story.sh`) has the author and committer `Kumpel <kumpel@noreply.invalid>`. The checkout's own `user.name` and `user.email` are not changed.
- **A merge commit** (`merge.sh`) has the title `Merge pull request #<pr> from <branch>` and the message `Merged by Kumpel after the six approval checks.`

`git log --format='%an: %s'` shows the author of each commit. A comment, commit or merge without these marks is the human's.

## Setting up an operator's machine

This chapter takes a machine with nothing on it to a factory job that runs and a skill that drives it. Follow the steps in order; each says what it proves and what its failure means. The commands are in `operator/` (its `README.md` is the map of the folder), and all read the site file (*The site file*).

### What the platform must provide first

The operator's scripts create the job and nothing around it. Before step 1 you need, from whoever runs the platform:

- the cloud project and region, and a network connector whose proxy reaches the code host and the model API (*What the job needs*);
- the service account the job runs as, and, when you work through another account, one you may impersonate (`SITE_IMPERSONATE`);
- two secrets, one holding the hosting-service token and one the model provider's key; only their names go into the site file;
- the code host's bot user (the owner of the hosting token) with push access to the project's repository, and read access to the factory's code repository.

A missing piece shows up in step 5 or later as a failed check, not as a message of its own.

### The steps

1. **Install the tools.** `gcloud`, `git`, `curl` and `python3` on the `PATH`, and a POSIX shell. Proves nothing yet; check 3 of step 5 names whichever is missing.
2. **Get the repository.** Clone this repository; the scripts run from its `operator/` folder as `sh operator/bin/site ...`. The checkout you name in the site file is the factory's *project* repository, which may be another one.
3. **Write the site file.** `sh operator/bin/site init` writes `operator/site.env.example` to the path `site path` prints, mode 0600, and never overwrites. Edit the file: every key is in the table of *The keys*, and a job needs all that table marks required. A failure here is the loader's: no file (status 1), a fault in a line (status 2), a file inside a git work tree (status 3).
4. **Check the file.** `sh operator/bin/site show` lists which keys are set, without a value. Use it to find what you forgot before the next step.
5. **Check the machine.** `sh operator/bin/site check`. See *The checks* below. It reads and writes nothing in any system, and ends with `site: ready` (status 0) or `site: <n> failed` (status 1). Repeat until it is ready; do not go on with a `FAIL`.
6. **Create the job.** `sh operator/job/job.sh create`. Proves that the project, region, connector and run-as account accept the job. A refusal is `gcloud`'s own text and its status (*Creating the job*).
7. **Start it.** `sh operator/job/job.sh execute`. It prints the execution's name. The job needs a few minutes to install, clone and build before the factory runs (*Starts, restarts and the end of an execution*).
8. **Watch it.** `sh operator/job/job.sh log` and `sh operator/job/job.sh status` (*Watching the job*). A stop the factory printed is read with *The stops*. The model API's login is not tested by `site check`, since that needs the secret's value: the job's preflight proves it at the first start, and its failure shows in the log.
9. **Drive a story.** Install the skill (`operator/README.md`, *Installing*) and start `/kumpel`. The first story shows that the whole chain works: the factory opens its pull request, you or the skill answer and approve it.
10. **Take the job away.** `sh operator/job/job.sh delete --yes` deletes the job and stops a running execution. Leave out `--yes` to see what it would do.

### The checks

`site check` runs eleven checks in this order and prints `ok <name>` or `FAIL <name>: <detail>` for each. The detail is one line of names and statuses and never a secret's value. A check whose keys are not set prints `FAIL <name>: needs <keys>` and does not run; the rest still do. If the site file does not load, nothing else runs.

| Check | It proves | What a `FAIL` means |
|---|---|---|
| `site file` | the file loads | the loader's message: run `site init`, or fix the line it names |
| `keys` | every key a job needs, and `SITE_REPOSITORY` and `SITE_CHECKOUT`, is set | the detail names the missing keys |
| `tools` | `gcloud`, `curl`, `git` and `python3` are on the `PATH` | the detail names those that are not |
| `token` | the token command (`SITE_TOKEN_CMD`, else `gh auth token`) prints a token | the hosting client's message, for instance an empty output |
| `repository` | `GET /repos/$SITE_REPOSITORY` answers 200 and the token may push | `hosting: GET /repos/owner/repo: 404 Not Found` (wrong name, or a token that cannot see it), or `the token has no push permission` |
| `checkout` | `SITE_CHECKOUT` is a git work tree whose `origin` names `SITE_REPOSITORY` (the `https` and the `git@host:` forms, with or without `.git`) | the detail says which part: not a work tree, no origin, or another repository |
| `identity` | `gcloud run jobs list` works for your login or `SITE_IMPERSONATE` | the first line of `gcloud`'s error |
| `secrets` | `gcloud secrets describe` finds `SITE_HOSTING_SECRET` and `SITE_MODEL_SECRET`; it never reads a version | the detail names the secret that failed: wrong name, or your identity cannot see it |
| `code` | `git ls-remote $SITE_CODE_URL` through `SITE_PROXY`, with no credential, works, and `SITE_CODE_REF` is listed as a branch or tag (a 40-digit commit id is taken without a lookup) | the proxy does not reach the code host, the repository needs a credential, or the ref does not exist |
| `no_proxy` | `SITE_NO_PROXY` covers the model API's host and none of the hosts of `SITE_CODE_URL`, `SITE_REPOSITORY_URL` and `SITE_API_URL` | the detail names the host and the rule. A domain `d` covers `d` and every host ending in `.d`, a leading `.` ignored. The job cannot resolve a code host itself, so it must go through the proxy; a model host that is not covered makes opencode wait for the proxy to answer for an internal host |
| `job` | informational: `ok job: <name> exists`, `ok job: <name> does not exist yet` (gcloud answered that the job is not found) or `ok job: <name> cannot be read: <first line of gcloud's error>` (any other failure, for instance `PERMISSION_DENIED`; `gcloud run jobs describe failed` when gcloud printed nothing) | only a missing `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB`. The line never fails, even when the job cannot be read; read its text, because a rights problem otherwise shows only when `job.sh` runs |

A check that depends on a failed tool or token fails with it, so one fault can print several `FAIL` lines: a missing `gcloud` fails `tools`, `identity` and `secrets` (`site: 3 failed`), and an empty token fails `token` and `repository`. Fix the first line and run it again.

```bash
sh operator/bin/site check
```

Run on a machine without a site file it prints, and exits 1:

```text
FAIL site file: site: no site file at <path>; run: site init
site: 1 failed
```
