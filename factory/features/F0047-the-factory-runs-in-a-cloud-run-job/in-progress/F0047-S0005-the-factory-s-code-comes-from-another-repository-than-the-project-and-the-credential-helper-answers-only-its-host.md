---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 486
comments_read: [6549192607]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-10-31T21:13:11.099638Z'
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-31T21:10:57.659095Z'
  stage: intake
  run: 7617dd7925b947ea9ac12753f37ef99c
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-31T21:12:15.470309Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-31T21:12:33.240933Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-31T21:12:50.668024Z'
  stage: intake
  run: 86005898b4ff4e35b9630bc8011e192e
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-31T21:13:11.099638Z'
  stage: tests
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
10. The URL rows of the helper, each against the request `host=git.example.invalid`: `FACTORY_REPOSITORY_URL=https://GIT.EXAMPLE.INVALID/o/r.git` (upper case), `https://user@git.example.invalid:8443/o/r.git` (user and port together) and `https://git.example.invalid:8443/o/r.git` (a port only) get the two lines; `https://user@other.example.invalid/o/r.git` gets no output and exit status 1.
11. `make check` stays green.
12. docs: `docs/operator-guide.md`: the option in the script's table; the paragraph *In v1.2 one repository URL serves both ...* is rewritten (one url by default, two with `--code-url`); a subsection *The code and the project apart*: what the project must bring (`factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, optional `factory/agents/`, a `Makefile` with `check`, `lint`, `test` and `sync`), that the stage image comes from the code checkout's `vm/Dockerfile`, that an update of the code is a new ref and a rebuild, and the helper's host rule. `docs/project-guide/git-and-hosting.md`: the helper. `docs/decisions.md`: an entry *The code and the project apart*, from the feature's decision 9. `README.md`: none.

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
3. intake: 1. The Interface says the host of `FACTORY_REPOSITORY_URL` is taken "lower-cased, user and port removed" from three forms (`https://[user@]host[:port]/...`, `ssh://[user@]host[:port]/...`, `[user@]host:path`). Criteria 2 and 3 cover only these URLs: `https://host/...` (no user, no port), `ssh://git@host:22/...` and `git@host:path`. Nothing tests these clauses: (a) a URL host in upper case (`https://GIT.EXAMPLE.INVALID/o/r.git` answering for `host=git.example.invalid`); (b) the `https://user@host:port/...` form, with user and port together; (c) a `https://` URL with a port only. Two coders could read these differently and both pass. Option: add one criterion that lists these URL rows. I would choose that.
   2. Criterion 5 says that with a different `--code-url` the clone carries `GIT_TERMINAL_PROMPT=0` and no askpass, and that with an equal url or no option it carries the askpass. The default is stated twice, "absent" and "equal". Criterion 5 tests both ("equal" and "no option"), so this is fine. But the stated rule that the clone with a different `--code-url` happens before the wait for the secrets is tested only through criterion 7's message. I read criterion 7 as enough, so this is not a question.
   3. The Interface says a request without a `host=` line is refused, but only with `FACTORY_REPOSITORY_URL` set. Criterion 2 tests it only with the variable set to an `https` URL. If you want a criterion for the unset case, which is "as today" and so answers, say so. I would not add one, because criterion 1 covers it.
   4. The format check passed. The smoke test commands are runnable, and each `Expect:` line can be checked against the output. The architecture and scope are fine: only `vm/` changes, which is inside the coder's write paths, and the story is within feature decision 9.

   Only question 1 blocks acceptance.
4. 2026-10-31 human: Answers to question 3:

   1. Yes: one new criterion, rows of one test, each answering for `host=git.example.invalid`: `FACTORY_REPOSITORY_URL=https://GIT.EXAMPLE.INVALID/o/r.git` (upper case), `https://user@git.example.invalid:8443/o/r.git` (user and port together), `https://git.example.invalid:8443/o/r.git` (a port only); and one refused row, `https://user@other.example.invalid/o/r.git` against `host=git.example.invalid`.
   2. Agreed: criterion 7 is enough.
   3. Agreed: no criterion for the unset case; criterion 1 covers it.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: names concrete files (`vm/setup.sh`, `vm/git-credential-factory`), the `--code-url` option with its default, the exact error message and exit codes, and the helper's host rule with the three URL forms. No module under `src/factory/` changes.
   - Criteria: each is testable by one test function. Every rule has both sides: the helper answers or refuses (2, 10), the clone carries or omits the askpass (5), the clone fails with the message (6), the wait message appears with and without `--code-url` (7). The URL-form clauses (lower case, user, port) are covered by the new criterion 10. I added that criterion from the human's answer in journal entry 4, question 1: three answering rows and one refused row. It sits before the two closing criteria, which are now 11 (`make check`) and 12 (`docs:`). Entry 4's answers 2 and 3 change nothing in the story.
   - Smoke test: both commands are runnable with `sh` and a temp token file. The `Expect:` lines (two named lines; `exit 1` alone) can be checked against the output. Neither runs pytest.
   - Architecture: only `vm/` shell scripts change, so no layer is touched. They are within the coder's write paths.
   - Scope: within feature decision 9 and the scope item for S0005. It does not touch S0006's start script or any "Out of scope" item. It changes no earlier story's test.
7. factory: started tests as vm.
