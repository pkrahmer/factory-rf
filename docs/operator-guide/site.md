# An operator's site and machine

A topic of the [operator guide](README.md). It is for the operator of an [instance](../project-guide/glossary.md). You run the factory as a Cloud Run job or on a machine of your own, and you do not read the code.

The page explains the one file that holds your site's values and the commands that read it. It shows how to take a new machine to a running job and how to repeat a trial.

Words the factory gave its own meaning, such as [work item](../project-guide/glossary.md) and [stop](../project-guide/glossary.md), are explained in the [glossary](../project-guide/glossary.md). Kumpel is the product the factory is one component of. The skill is Kumpel's `kumpel` skill, which lets an agent run an instance with you; its folder and its map are in [`operator/README.md`](../../operator/README.md).

Exact detail (every exit status, every message, every built-in rule) is in the *Reference* at the end.

## The site file

The values that belong to one site live in one plain file, `site.env`. They are a project, a region, a proxy, the names of secrets, two repositories and a token command. One loader, `operator/lib/site.sh`, reads the file for every operator script. [`operator/site.env.example`](../../operator/site.env.example) is the file with every key. The file holds company values, so it lies outside every repository.

`operator/job/job.sh` reads it for the job (*Creating the job* in [cloud-run.md](cloud-run.md)). The skill's scripts use the hosting library (*The token source*).

### Its place

The path is the first of these that exists as a setting:

1. `$FACTORY_SITE`, when it is set and not empty.
2. `$XDG_CONFIG_HOME/kumpel/site.env`.
3. `$HOME/.config/kumpel/site.env`, the folder the skill's `settings.json` already uses.

`site path` prints it. Keep the file in your own configuration folder, never in a checkout. The loader refuses a file that lies inside a git work tree, and `site init` refuses to write one there.

### The format

The file is a list of lines. Each line is blank, a comment (the first non-blank character is `#`) or `SITE_NAME=value`.

- `NAME` is capitals, digits and `_`, at least one character. A space or a tab before the `=` or directly after it is a fault, because `SITE_PROXY= http://p` would carry a leading space into the value. A space inside a value, or at its end, is kept.
- The value is everything after the first `=`, with trailing whitespace removed. One pair of single or double quotes around the whole value is removed, and the whitespace inside stays. A quote that is not matched stays.
- A value is stored literally. `$`, a backtick, `;` and `\` mean nothing, and the file is never executed. `SITE_A=$(touch x)` is the text `$(touch x)`.
- A variable that is already set in the environment, even to the empty string, keeps its value. Of a key that appears twice, the first line wins.
- A line of another kind, or a key that is not `SITE_` followed by a name, is a fault. Nothing is exported from the file, the message `site: <path>:<line>: ...` goes to standard error, and the status is 2.

### The `site` command

Run it as `sh operator/bin/site`.

| Command | What it does |
|---|---|
| `site path` | prints the path |
| `site init` | makes the folder and writes `operator/site.env.example` to the path, mode 0600; it never overwrites (status 1) |
| `site show` | prints `SITE_X=set` or `SITE_X=unset` for each key of the example, in its order; a key set to the empty string is `unset`; it never prints a value |
| `site get SITE_X` | prints the value; when it is unset or empty, it prints `site: SITE_X is not set` and exits 1 |
| `site check` | runs the read-only checks of a machine, one line each (see *Setting up an operator's machine*) |

To write a site file and look at it:

Run the commands from the root of your clone of this repository. The example files go to a folder outside it, `$HOME/site-example`, because the loader refuses a site file inside a git work tree.

1. Point the commands at a file with `FACTORY_SITE`. Write the file from the example; it prints the path to edit:

   ```console
   $ FACTORY_SITE="$HOME/site-example/site.env" sh operator/bin/site init | sed "s|$HOME|<home>|"
   site: wrote <home>/site-example/site.env; edit it, then run: site check
   ```

2. See which keys are set. The first three:

   ```console
   $ FACTORY_SITE="$HOME/site-example/site.env" sh operator/bin/site show | head -3
   SITE_REPOSITORY=set
   SITE_CHECKOUT=set
   SITE_API_URL=set
   ```

3. Read one value:

   ```console
   $ FACTORY_SITE="$HOME/site-example/site.env" sh operator/bin/site get SITE_REPOSITORY
   owner/repo
   ```

### The keys

[`operator/site.env.example`](../../operator/site.env.example) holds every key with a comment and a made-up value. It is the first place to look. The table gives the same by name. A test keeps the example's comments true to what `operator/lib/site.sh` and `operator/job/job.sh` do.

A key marked *required for a job* may stay unset when you do not run the job; `SITE_REPOSITORY` and `SITE_CHECKOUT` are always required.

| Name | What it does | Default | Example |
|---|---|---|---|
| `SITE_REPOSITORY` | the repository the factory works on, `owner/repo` | required | `owner/repo` |
| `SITE_CHECKOUT` | the local checkout of that repository | required | `/path/to/checkout` |
| `SITE_API_URL` | the hosting service's API | GitHub's public API | `https://api.example.invalid` |
| `SITE_TOKEN_CMD` | the command that prints a hosting-service token | `gh auth token` | `/path/to/token-command` |
| `SITE_PROXY` | the proxy for the job and its tools | required for a job | `http://proxy.example.invalid:3128` |
| `SITE_NO_PROXY` | hosts reached without the proxy, comma-separated | required for a job | `localhost,192.0.2.10` |
| `SITE_PROJECT` | the cloud project of the job | required for a job | `example-project` |
| `SITE_REGION` | the cloud region of the job | required for a job | `example-region1` |
| `SITE_IMPERSONATE` | the service account the operator's cloud commands impersonate | your own login | `operator@example-project.example.invalid` |
| `SITE_RUN_AS` | the service account the job runs as | required for a job | `job@example-project.example.invalid` |
| `SITE_CONNECTOR` | the network connector the job's traffic leaves through | required for a job | `example-connector` |
| `SITE_JOB` | the name of the job | required for a job | `example-factory` |
| `SITE_INSTANCE` | the instance's name in the job: letters, digits, `.`, `_` and `-` | required for a job | `example-instance` |
| `SITE_REPOSITORY_URL` | the clone URL of the factory's repository | required for a job | `https://git.example.invalid/owner/repo.git` |
| `SITE_CODE_URL` | the clone URL of the factory's own code | required for a job | `https://git.example.invalid/owner/code.git` |
| `SITE_CODE_REF` | the branch or tag of the code the job runs | required for a job | `main` |
| `SITE_HOSTING_SECRET` | the secret that holds the hosting-service token | required for a job | `example-hosting-token` |
| `SITE_MODEL_SECRET` | the secret that holds the model provider's key | required for a job | `example-model-key` |
| `SITE_MODEL_BASE_URL` | the model provider's API | required for a job | `https://models.example.invalid/v1` |
| `SITE_MODEL` | the model the agents run on | required for a job | `example-model` |
| `SITE_MODEL_INPUT_COST` | price per million input tokens, in dollars | `0` | `1.00` |
| `SITE_MODEL_OUTPUT_COST` | price per million output tokens, in dollars | `0` | `5.00` |
| `SITE_LOGIN_URL` | the login service that issues the provider's tokens | required for a job | `https://login.example.invalid/oauth2/token` |
| `SITE_LOGIN_SCOPE` | the scope asked of the login service | required for a job | `example-scope` |
| `SITE_LOGIN_CLIENT_ID` | the client id given to the login service | required for a job | `example-client-id` |
| `SITE_CPU` | the job's CPUs | 4 | `4` |
| `SITE_MEMORY` | the job's memory | 16Gi | `16Gi` |
| `SITE_TIMEOUT` | the job's task timeout, as `gcloud run jobs --task-timeout` takes it: seconds, or a duration such as `4h` | 86400 (24 hours) | `24h` |
| `SITE_IDLE_MINUTES` | idle minutes after which the job ends itself | 30 | `30` |
| `SITE_RESET_REPOSITORY` | the repository a trial resets, `owner/repo`; `reset-to-tag.sh` acts only when it equals `SITE_REPOSITORY` (see *Repeating a trial*) | none | `owner/trial-repo` |
| `SITE_SANITISE_RULES` | the file of rules that sanitise what leaves the site | `sanitise.rules` beside the site file | `/path/to/sanitise-rules` |

The skill's scripts live in `operator/skill/kumpel/scripts/`. They read `SITE_REPOSITORY` and `SITE_CHECKOUT` from the site file, or from the environment when it sets them. Only then do they look at the skill's `settings.json`.

- When the site gives both, `settings.json` holds only the switches (`merge`, `answer`, `start_next`) and `settings.sh init` takes no argument.
- When the site gives one or none, `settings.sh init` needs `<owner/name> <checkout>`, and the JSON file keeps them.
- A missing or faulty site file does not stop `settings.sh`. The JSON file answers, and a faulty file's message goes to standard error.

The scripts reach the API and git only through `hosting_repo_api` and `hosting_git`.

| What you see | What it means | What you do |
|---|---|---|
| `hosting: the token command failed; see SITE_TOKEN_CMD in the site file` | the script has neither a token command nor a `gh` login | set `SITE_TOKEN_CMD` in the site file, or log in with `gh auth login` |

### The token source

`operator/lib/hosting.sh` is the shell library that talks to the code host. It offers the REST API (`hosting_api`, and `hosting_repo_api` for `/repos/$SITE_REPOSITORY...`) and git over HTTPS (`hosting_git`). Source it after `operator/lib/site.sh`; it loads the site file itself when no `SITE_` value is loaded yet. It replaces the `gh` program for those two uses, because `gh` uses the person's own login, which may not see the project's repository.

The token comes from one of two sources:

1. `SITE_TOKEN_CMD`, when it is set and not empty. It is a command that prints a token (a secret store, a keychain, any program) and runs as `sh -c "$SITE_TOKEN_CMD"`. The first line of its output is the token, with surrounding whitespace and a trailing carriage return removed. Its standard error is discarded.
2. Otherwise `gh auth token`, so a home setup with a logged-in `gh` needs no entry.

If the command fails, prints nothing, or neither a command nor `gh` exists, the library prints the message above and returns 4. The message never repeats what the command printed, because that may be an error text that holds a secret.

The token is never in an argument list, where `ps` shows it to every user of the machine, and it is written to no file.

- The API call gives `curl` its URL and headers, the token among them, as a configuration on standard input (`--config -`).
- `hosting_git` gives git a `http.extraHeader` and an empty `credential.helper` through the `GIT_CONFIG_*` environment variables, and sets `GIT_TERMINAL_PROMPT=0`. The header is sent to every http(s) remote that git call contacts.
- `curl` 7.63 or later is needed; Debian 12 has 7.88.

`SITE_API_URL` is the base of the API calls (default `https://api.github.com`; a trailing `/` is removed). Set it for a GitHub Enterprise server.

To see the token command at work, with a command that prints a token with blanks around it:

```console
$ mkdir -p "$HOME/site-example"
$ printf 'SITE_TOKEN_CMD=printf "  abc  "\n' > "$HOME/site-example/token.env"
$ FACTORY_SITE="$HOME/site-example/token.env" sh -c '. operator/lib/site.sh; . operator/lib/hosting.sh; hosting_token'
abc
```

The return codes of `hosting_api`, `hosting_repo_api` and `hosting_git` are in the *Reference*.

### Sanitising what leaves the machine

A log, a result or a note that goes from your machine into a repository must not carry the site's names: its domain, its project, its repository, a token. `sh operator/bin/sanitise` removes them and proves that a file has none left. It needs the site file; without one it prints the site's own message and exits 2.

It has two calls, `sh operator/bin/sanitise < raw > clean` and `sh operator/bin/sanitise check FILE...`. The first writes standard input to standard output with the rules applied. The second prints `sanitise: clean` and exits 0, or names `file:line` and exits 1; its other statuses are in the *Reference*. Any other call prints `usage: sanitise < raw > clean | sanitise check FILE...` and exits 2.

#### The rules file

The rules file is `$SITE_SANITISE_RULES` when that is set, in the environment (which wins) or in the site file. Otherwise it is `sanitise.rules` in the folder of the site file. A relative path is relative to the site file's folder.

The patterns are your company's names, so the file is the site's. Keep it beside the site file and never put it into a repository. The repository holds the mechanism only.

Each line is blank, a comment (`#`) or one of three rules:

| Line | Meaning |
|---|---|
| `PATTERN => REPLACEMENT` | replace every match of the pattern |
| `drop: PATTERN` | remove every line that matches |
| `leak: PATTERN` | the check reports a match; the filter leaves the text alone |

A pattern is a Python regular expression, applied with `re.sub`, case sensitive. The first ` => ` of a line splits it, and whitespace around both parts is removed. The replacement is literal text, except that `\1` to `\99` stand for that group of the pattern. Two digits are one number, and a group that took no part in the match gives empty text. Every other backslash stays a backslash.

```
# the company's names
corp\.example\.invalid => <company-host>
(\d+)-secret => \1-x
drop: ^DEBUG
leak: internal-project
```

Rules are numbered from 1 in file order, counting rule lines only, not blank lines or comments.

| What you see | What it means | What you do |
|---|---|---|
| `sanitise: <path>:<line>: <reason>`, status 2 | a line of another kind, an empty pattern, a pattern that is not a regular expression, or a replacement that names a group the pattern lacks | fix the line the message names; `check` stops the same way before it reads any file |
| `sanitise: no rules file at <path>; only the built-in rules apply` on standard error | the filter found no rules file and goes on with the built-in rules | write the file at that path if the site has names to hide |

#### The filter

The filter applies the built-in rules first, then the site's in file order, line by line. The order of lines is kept, every line ends with a newline, and empty input gives empty output. The built-in rules remove terminal escape sequences and hide JSON web tokens and hosting-service tokens; the *Reference* lists them.

#### The check

`sanitise check FILE...` tests every line of every file against the built-in token patterns and every pattern of the rules file (the left side of `=>`, `drop:` and `leak:`). For each line and rule that matches it prints `<file>:<line>: <n>` once. `<n>` is the rule's number, or `builtin-1`, `builtin-2` or `builtin-3`.

It never prints the matched text, so its report is no leak. A filtered file passes the check against the same rules, unless a replacement itself matches a pattern. The exit statuses are in the *Reference*.

To try both on a file with one line to hide:

```console
$ mkdir -p "$HOME/site-example"
$ printf 'SITE_PROJECT=p\n' > "$HOME/site-example/san.env"
$ printf 'corp\\.example\\.invalid => <company-host>\n' > "$HOME/site-example/sanitise.rules"
$ printf 'one\nat corp.example.invalid\n' > "$HOME/site-example/raw.txt"
$ FACTORY_SITE="$HOME/site-example/san.env" sh operator/bin/sanitise < "$HOME/site-example/raw.txt" > "$HOME/site-example/clean.txt"; cat "$HOME/site-example/clean.txt"
one
at <company-host>
$ FACTORY_SITE="$HOME/site-example/san.env" sh operator/bin/sanitise check "$HOME/site-example/raw.txt" | sed "s|$HOME|<home>|"
<home>/site-example/raw.txt:2: 1
$ FACTORY_SITE="$HOME/site-example/san.env" sh operator/bin/sanitise check "$HOME/site-example/clean.txt"
sanitise: clean
```

## Repeating a trial

A trial repository can be set back to a starting point, so that a run is repeated from the same state.

1. Tag the starting point once: `git tag starting-point <commit>`.
2. Push the tag: `git push origin starting-point`.
3. Name the trial repository in the site file: `SITE_RESET_REPOSITORY` must equal `SITE_REPOSITORY`.
4. Run the skill's script without `--yes`. It prints the plan and exits 1.
5. Run it again with `--yes` to do it.

The two outputs below need GitHub, which the document check cannot reach. They are not copied from a run: they are the lines the script's code prints, with made-up counts and commit.

```console github
$ sh operator/skill/kumpel/scripts/reset-to-tag.sh starting-point
would close 2 open work-item pull request(s)
would delete 3 work-item branch(es)
would move main to 1a2b3c4
run again with --yes
$ sh operator/skill/kumpel/scripts/reset-to-tag.sh starting-point --yes
closed #12
closed #13
deleted work-item/F0001-S0001
moved main to 1a2b3c4
```

The script works through the hosting API alone and needs no checkout. It resolves the tag, and an annotated tag is followed to its commit. Then, in this order, it does three things:

1. It closes every open pull request whose head branch starts with `work-item/` (`closed #<n>`).
2. It deletes every branch under `work-item/` (`deleted <branch>`).
3. It moves `main` to the tag's commit by force (`moved main to <7 characters>`).

Nothing else is touched: no other branch, no tag, no other pull request. Without `--yes` it prints the counts and the target (`would close 2 open work-item pull request(s)`, `would delete 3 work-item branch(es)`, `would move main to <commit>`). Then it prints `run again with --yes` and exits 1. A reset that finds nothing to close or delete still moves `main`.

The force-push cannot be undone. The commits `main` held are no longer on any branch, and the closed pull requests and deleted branches are not restored.

It refuses to run in these cases:

| What you see | What it means | What you do |
|---|---|---|
| `usage: reset-to-tag.sh <tag> [--yes]`, exit 2 | the arguments are not `<tag>` or `<tag> --yes` | give the tag, and `--yes` to do the reset |
| `reset-to-tag.sh: <repository> is not the site's resettable repository`, exit 1 | `SITE_RESET_REPOSITORY` differs from `SITE_REPOSITORY`; only a repository that both keys name is reset | set both to the trial repository |
| `site: missing SITE_RESET_REPOSITORY in <file>`, exit 2 | the key is unset; this is the site loader's message | set `SITE_RESET_REPOSITORY` |
| `reset-to-tag.sh: no tag <tag>`, exit 1 | the tag does not exist | create and push the tag |
| the hosting client's message, exit 1 | another failure of the tag lookup | read the message; fix the cause |

A failing call stops the script at that call with the hosting client's message and exit 1, so a half reset is visible: the lines printed so far are what was done. Run it again with `--yes` after fixing the cause. Only the first 100 open pull requests are listed, with no paging.

### Merging a story from the skill

The same skill folder merges a [story](../project-guide/glossary.md): `merge.sh <pr> <id>` (see *A merge archives the story* in [work-items.md](work-items.md)). It merges with a merge commit. Then it polls the latest 20 commits of `main` for `work item <id>: merged, archived`. It polls every `KUMPEL_POLL_SECONDS` seconds (15), for at most `KUMPEL_ARCHIVE_WAIT` seconds (300). It prints `merged #<pr>` and `archived <id>` and exits 0. Start the next story only after `archived`.

| What you see | What it means | What you do |
|---|---|---|
| `merge.sh: #<pr> is not open`, exit 1 | the pull request is closed or merged | check the number; nothing was merged |
| `merge.sh: #<pr> is a draft`, exit 1 | the factory has not handed the pull request over | wait for the factory; nothing was merged |
| `merge.sh: #<pr> is not at stage:approval`, exit 1 | the work item has not reached the approval | wait for the label `stage:approval`; nothing was merged |
| `merge.sh: #<pr> is not the pull request of <id>`, exit 1 | the pull request's branch is not `work-item/<id>` | give the right number and id; nothing was merged |
| `merge.sh: merged, but no archive commit for <id> after <N> s`, exit 1 | the pull request is merged, but the archive commit did not appear in time | look at the history of `main` and the factory's log; do not start the next story until `archived` shows |

### Telling Kumpel's acts from the human's

The skill acts with the human's own token, so GitHub shows the human's account on everything it does. Kumpel therefore signs each act:

- **A comment** ends with a blank line, the line `— Kumpel, for the human who owns this project` and the marker `<!-- kumpel -->`. The skill posts only through `comment.sh <pr> <file>`. That script adds the signature once, posts a text that already ends with it as it is, and prints `commented #<pr>`.
  The factory copies a comment's text into the [journal](../project-guide/glossary.md), so the signature line is there too. A journal entry of the human that ends with it was written by Kumpel.
  A verdict is recognised by `<!-- kumpel verdict -->` anywhere in the newest comment. The signature after it does not hide it from `status.sh`.
- **A start commit** (`start-story.sh`) has the author and committer `Kumpel <kumpel@noreply.invalid>`. The checkout's own `user.name` and `user.email` are not changed.
- **A merge commit** (`merge.sh`) has the title `Merge pull request #<pr> from <branch>` and the message `Merged by Kumpel after the six approval checks.`

`git log --format='%an: %s'` shows the author of each commit. A comment, commit or merge without these marks is the human's.

## Setting up an operator's machine

This chapter takes a machine with nothing on it to a factory job that runs and a skill that drives it. Follow the steps in order. Each says what it proves and what its failure means. The commands are in `operator/`, and all read the site file (*The site file*). [`operator/README.md`](../../operator/README.md) is the map of the folder.

### What the platform must provide first

The operator's scripts create the job and nothing around it. Before step 1 you need, from whoever runs the platform:

- the cloud project and region, and a network connector whose proxy reaches the code host and the model API (*What the job needs* in [cloud-run.md](cloud-run.md));
- the service account the job runs as, and, when you work through another account, one you may impersonate (`SITE_IMPERSONATE`);
- two secrets, one holding the hosting-service token and one the model provider's key; only their names go into the site file;
- the code host's bot user (the owner of the hosting token) with push access to the project's repository, and read access to the factory's code repository.

A missing piece shows up in step 5 or later as a failed check, not as a message of its own.

### The steps

1. **Install the tools.** Put `gcloud`, `git`, `curl` and `python3` on the `PATH`, and have a POSIX shell. This proves nothing yet; check 3 of step 5 names whichever is missing.
2. **Get the repository.** Clone this repository. The scripts run from its `operator/` folder as `sh operator/bin/site ...`. The checkout you name in the site file is the factory's *project* repository, which may be another one.
3. **Write the site file.** Run `sh operator/bin/site init`. It writes `operator/site.env.example` to the path `site path` prints, mode 0600, and never overwrites. Edit the file: every key is in the table of *The keys*, and a job needs all that table marks required. `init` fails in two ways: `site: <path> exists; not overwritten` (status 1), and the refusal to write inside a git work tree (status 3).
4. **Check the file.** Run `sh operator/bin/site show`. It lists which keys are set, without a value. Use it to find what you forgot before the next step. Here the loader first reads the file: no file is status 1, a fault in a line status 2, and a file inside a git work tree status 3 (the *Reference* lists them).
5. **Check the machine.** Run `sh operator/bin/site check` (see *The checks*). It reads and writes nothing in any system, and ends with `site: ready` (status 0) or `site: <n> failed` (status 1). Repeat until it is ready; do not go on with a `FAIL`.
6. **Create the job.** Run `sh operator/job/job.sh create`. It proves that the project, region, connector and run-as account accept the job. A refusal is `gcloud`'s own text and its status (*Creating the job* in [cloud-run.md](cloud-run.md)).
7. **Start it.** Run `sh operator/job/job.sh execute`. It prints the execution's name. The job needs a few minutes to install, clone and build before the factory runs (*Starts, restarts and the end of an execution* in [cloud-run.md](cloud-run.md)).
8. **Watch it.** Run `sh operator/job/job.sh log` and `sh operator/job/job.sh status` (*Watching the job* in [cloud-run.md](cloud-run.md)). Read a stop the factory printed with [stops.md](stops.md). `site check` does not test the model API's login, since that needs the secret's value. The job's preflight proves it at the first start, and its failure shows in the log.
9. **Drive a story.** Install the skill (*Installing* in [`operator/README.md`](../../operator/README.md)) and start `/kumpel`. The first story shows that the whole chain works: the factory opens its pull request, and you or the skill answer and approve it.
10. **Take the job away.** Run `sh operator/job/job.sh delete --yes`. It deletes the job and stops a running execution. Leave out `--yes` to see what it would do.

### The checks

`site check` runs eleven checks in this order and prints `ok <name>` or `FAIL <name>: <detail>` for each. The detail is one line of names and statuses and never a secret's value. A check whose keys are not set prints `FAIL <name>: needs <keys>` and does not run; the rest still do. If the site file does not load, nothing else runs.

Each row below reads as: what you see, what it means, and what you do.

| What you see | What it means | What you do |
|---|---|---|
| `FAIL site file: ...` | the file does not load | run `site init`, or fix the line the loader's message names |
| `FAIL keys: ...` | a key a job needs, `SITE_REPOSITORY` or `SITE_CHECKOUT` is unset; the detail names them | set the keys named |
| `FAIL tools: ...` | `gcloud`, `curl`, `git` or `python3` is not on the `PATH`; the detail names it | install it |
| `FAIL token: ...` | the token command (`SITE_TOKEN_CMD`, else `gh auth token`) printed no token; the detail is the hosting client's message, for instance an empty output | fix `SITE_TOKEN_CMD`, or log in with `gh auth login` |
| `FAIL repository: hosting: GET /repos/owner/repo: 404 Not Found` | `GET /repos/$SITE_REPOSITORY` did not answer 200: the name is wrong, or the token cannot see the repository | correct `SITE_REPOSITORY`, or use a token that can see it |
| `FAIL repository: ... the token has no push permission` | the repository answers, but the token may not push | use the bot user's token with push access |
| `FAIL checkout: ...` | `SITE_CHECKOUT` is not a git work tree, has no `origin`, or its `origin` names another repository than `SITE_REPOSITORY` (`https` and `git@host:` forms, with or without `.git`, are accepted); the detail says which | point `SITE_CHECKOUT` at a clone of `SITE_REPOSITORY` |
| `FAIL identity: ...` | `gcloud run jobs list` fails for your login or `SITE_IMPERSONATE`; the detail is the first line of `gcloud`'s error | log in with `gcloud`, or correct `SITE_IMPERSONATE` |
| `FAIL secrets: ...` | `gcloud secrets describe` does not find `SITE_HOSTING_SECRET` or `SITE_MODEL_SECRET` (it never reads a version); the detail names the secret | correct the name, or ask for rights to see the secret |
| `FAIL code: ...` | `git ls-remote $SITE_CODE_URL` through `SITE_PROXY`, with no credential, failed, or `SITE_CODE_REF` is not listed as a branch or tag (a 40-digit commit id is taken without a lookup) | check that the proxy reaches the code host, that the repository needs no credential, and that the ref exists |
| `FAIL no_proxy: ...` | `SITE_NO_PROXY` does not cover the model API's host, or covers a host of `SITE_CODE_URL`, `SITE_REPOSITORY_URL` or `SITE_API_URL`; the detail names the host and the rule | change `SITE_NO_PROXY` by the rule below |
| `FAIL job: needs ...` | `SITE_PROJECT`, `SITE_REGION` or `SITE_JOB` is unset; the `job` check never fails otherwise (see below) | set the keys named |

The `no_proxy` rule: a domain `d` covers `d` and every host ending in `.d`, a leading `.` ignored. The job cannot resolve a code host itself, so the code host must go through the proxy. A model host that is not covered makes opencode wait for the proxy to answer for an internal host.

The `job` check prints one of three lines:

- `ok job: <name> exists`.
- `ok job: <name> does not exist yet`, when gcloud answered that the job is not found.
- `ok job: <name> cannot be read: <first line of gcloud's error>`, for any other failure, for instance `PERMISSION_DENIED`. It reads `gcloud run jobs describe failed` when gcloud printed nothing.

The line never fails, even when the job cannot be read. Read its text, because a rights problem otherwise shows only when `job.sh` runs.

A check that depends on a failed tool or token fails with it, so one fault can print several `FAIL` lines. A missing `gcloud` fails `tools`, `identity` and `secrets` (`site: 3 failed`), and an empty token fails `token` and `repository`. Fix the first line and run it again.

On a machine without a site file (nothing set, an empty home) it prints, and exits 1:

```console
$ HOME=$PWD/none FACTORY_SITE= XDG_CONFIG_HOME= sh operator/bin/site check | sed "s|$PWD|<d>|"
FAIL site file: site: no site file at <d>/none/.config/kumpel/site.env; run: site init
site: 1 failed
```

## Reference

### Loader and `site` statuses

| Status | When |
|---|---|
| 1 | the site file is missing (`run: site init`); `site init` finds a file already there; `site get` finds the key unset or empty |
| 2 | a fault in a line of the file; or a command line that is not one of those above |
| 3 | the file lies inside a git work tree |

`show` and `get` load the file first and pass on the loader's failure. Any other command line prints `usage: site path | init | show | get SITE_X | check` and exits 2. `site check` with an argument prints `usage: site check` and exits 2.

### Return codes of the hosting library

| Function | Code | Meaning |
|---|---|---|
| `hosting_api` | 0 | an HTTP status from 200 to 299; the body is printed |
| `hosting_api` | 22 | any other status, with `hosting: <METHOD> <PATH>: <status> <message>` on standard error (the body's JSON `message`, else its first 100 characters), or `no answer` when `curl` gave no status |
| `hosting_api` | 4 | there is no token |
| `hosting_repo_api` | 2 | `SITE_REPOSITORY` is unset |
| `hosting_git` | git's own status | or 4, without running git, when there is no token |

### The built-in sanitiser rules

1. `builtin-1`: terminal escape sequences (`\x1b[31m` and the like) are removed.
2. `builtin-2`: `eyJ` followed by two more dot-separated base64url parts, each at least 10 characters, becomes `***JWT***`.
3. `builtin-3`: `ghp_`, `gho_`, `ghu_`, `ghs_` or `ghr_` followed by 20 or more letters or digits, and `github_pat_` followed by 20 or more letters, digits or `_`, become `***TOKEN***`.

### Exit statuses of `sanitise check`

| Status | Meaning |
|---|---|
| 0 | `sanitise: clean` |
| 1 | at least one match was reported |
| 2 | a rules-file fault, a wrong call, or a named file that does not exist (`sanitise: <file>: no such file`, and nothing else on standard output) |
| 3 | no rules file (`sanitise: no rules file at <path>; nothing to check against`) |

### Environment variables of the skill's scripts

| Name | What it does | Default | Example |
|---|---|---|---|
| `KUMPEL_POLL_SECONDS` | seconds between two looks for the archive commit in `merge.sh` | 15 | `15` |
| `KUMPEL_ARCHIVE_WAIT` | seconds `merge.sh` waits for the archive commit | 300 | `300` |
