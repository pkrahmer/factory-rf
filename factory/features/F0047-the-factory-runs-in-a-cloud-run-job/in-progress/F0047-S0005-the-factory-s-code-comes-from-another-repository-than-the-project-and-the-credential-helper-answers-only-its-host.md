---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-10-31T21:10:34.754390Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-31T21:10:34.748703Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-31T21:10:34.754390Z'
  stage: intake
---

# The factory's code comes from another repository than the project, and the credential helper answers only its host

## Description

Today `vm/setup.sh` takes one `--repository-url`: the factory runs its code from that clone and works on the same repository, and the credential helper `vm/git-credential-factory` hands the hosting token to whatever host git asks. At a company that works on its own enterprise host, and runs the factory's public code from a public repository (the enterprise host allows no fork of a public repository), those are two repositories on two hosts. This story separates them. `vm/setup.sh` gains `--code-url`, the repository the factory's code and its stage image's `vm/Dockerfile` come from: it is cloned without any credential (the code must be reachable without a token), while `--repository-url` stays the project the instance builds and the value of `FACTORY_REPOSITORY_URL`. The helper learns to refuse: it answers only when git asks for the host of `FACTORY_REPOSITORY_URL`, so the project's token is never offered to the code repository's host or to any other. Unchanged: a call of `setup.sh` without `--code-url` (the code comes from `--repository-url`, with the token, as today); the helper when `FACTORY_REPOSITORY_URL` is not set (it answers as today); every other step and variable. Left to later stories: the job's start script (S0006), which uses the same split.

## Interface

No module under `src/factory/` changes. The coder changes `vm/setup.sh` and `vm/git-credential-factory`.

`vm/git-credential-factory` (shell): after reading git's request from standard input, for the operation `get`:

- With `FACTORY_REPOSITORY_URL` set, the helper takes the host of that URL (`https://[user@]host[:port]/...` and `ssh://[user@]host[:port]/...` and `[user@]host:path` forms; lower-cased, user and port removed) and the `host=` line of the request (lower-cased, port removed); it answers (the two lines it prints today) only when they are equal and prints nothing and exits 1 otherwise. A request with no `host=` line is refused.
- With `FACTORY_REPOSITORY_URL` unset: as today.
- Every other operation, and the checks on `FACTORY_TOKEN_FILE`, are as today.

`vm/setup.sh` (shell): the option `--code-url <url>` (usage text and the option table of the operator guide), default the value of `--repository-url`.

- With `--code-url` equal to `--repository-url` or absent: the checkout step is as today.
- With a different `--code-url`: the clone of `/srv/factory/<instance>/factory` runs with `GIT_TERMINAL_PROMPT=0` and without `GIT_ASKPASS` and `core.askPass`, so a code repository that asks for a credential fails the clone with the message `setup: checkout: cannot clone <url> without a credential; the code repository must be readable without a token`, exit 1. That clone happens before the wait for the secrets, so the first pass stops later, at `waiting for /home/factory/.secrets/hosting-token` (exit 0), as today.
- `factory.env` holds `FACTORY_REPOSITORY_URL=<--repository-url>` as today; it never holds the code url.
- Everything else (the thirteen step names and order, the secrets, the unit) is unchanged.

Tests (the tester writes them): `tests/test_vm_credential_helper_host.py` (the helper run with a made-up environment and requests on standard input), `tests/test_vm_setup_code_url.py` (through `tests/vm_support.py`'s `run_setup` with stand-in executables).

## Acceptance criteria

1. With `FACTORY_REPOSITORY_URL` unset the helper answers exactly as before this story (the existing tests pass unchanged).
2. With `FACTORY_REPOSITORY_URL=https://git.example.invalid/o/r.git` and a readable token file: a request `protocol=https` / `host=git.example.invalid` gets the two lines `username=x-access-token` and `password=<the file's text>`; `host=GIT.EXAMPLE.INVALID` and `host=git.example.invalid:443` get them too; `host=github.com`, `host=git.example.invalid.evil.example` and a request without a `host=` line get no output and exit status 1.
3. The URL forms: `ssh://git@git.example.invalid:22/o/r.git` and `git@git.example.invalid:o/r.git` both mean the host `git.example.invalid`.
4. A request for another operation (`store`, `erase`) prints nothing and exits 0, as before.
5. `setup.sh --code-url <u>` with `<u>` different from `--repository-url`: the stand-in `git`'s `clone` call carries `GIT_TERMINAL_PROMPT=0`, no `GIT_ASKPASS` and no `core.askPass`, and names `<u>` as its source; with `<u>` equal to `--repository-url` or no option, it carries the askpass as before.
6. A stand-in `git clone` that fails when no credential is offered makes `setup.sh` print `setup: checkout: cannot clone <url> without a credential; the code repository must be readable without a token` to standard error and exit 1.
7. With a different `--code-url` and no `hosting-token`, the clone still runs and the script then prints `setup: checkout: waiting for /home/factory/.secrets/hosting-token; place the secrets and run this script again` and exits 0; without `--code-url` the order and the message are as before.
8. `factory.env` made by a run with a different `--code-url` holds `FACTORY_REPOSITORY_URL` with the project's url and no line with the code url.
9. `setup.sh --help` and the usage text name `--code-url`.
10. `make check` stays green.
11. docs: `docs/operator-guide.md`: the option in the script's table; the paragraph *In v1.2 one repository URL serves both ...* is rewritten (one url by default, two with `--code-url`); a subsection *The code and the project apart*: what the project must bring (`factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, optional `factory/agents/`, a `Makefile` with `check`, `lint`, `test` and `sync`), that the stage image comes from the code checkout's `vm/Dockerfile`, that an update of the code is a new ref and a rebuild, and the helper's host rule. `docs/project-guide/git-and-hosting.md`: the helper. `docs/decisions.md`: an entry *The code and the project apart*, from the feature's decision 9. `README.md`: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'secret-text' > "$d/token"
printf 'protocol=https\nhost=git.example.invalid\n\n' | FACTORY_TOKEN_FILE="$d/token" FACTORY_REPOSITORY_URL=https://git.example.invalid/o/r.git sh vm/git-credential-factory get
```
Expect: two lines, `username=x-access-token` and `password=secret-text`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'secret-text' > "$d/token"
printf 'protocol=https\nhost=github.com\n\n' | FACTORY_TOKEN_FILE="$d/token" FACTORY_REPOSITORY_URL=https://git.example.invalid/o/r.git sh vm/git-credential-factory get; echo "exit $?"
```
Expect: one line, `exit 1`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-31 human: created.
2. factory: started intake as vm.
