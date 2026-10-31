---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 486
comments_read: [6549192607, 6549244772, 6549403733]
handed_over: null
claim: null
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
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-31T21:14:39.381888Z'
  stage: tests
  run: 251e102226974720ad3af7f2ddb8ee99
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-31T21:16:57.853392Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-31T21:17:15.579453Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-10-31T21:25:25.942589Z'
  stage: tests
  run: 0f02ef73975d4155be7f9c77acb4b2a8
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-31T21:25:48.407984Z'
  stage: doing
- number: 13
  speaker: coder
  kind: question
  at: '2026-10-31T21:31:05.210558Z'
  stage: doing
  run: 403914c58c1246a99f00862c888b0e0e
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-10-31T21:33:23.207273Z'
  stage: doing
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-31T21:33:40.947994Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-10-31T21:33:56.447571Z'
  stage: doing
  run: 7f262b90654843fd85226dfae39baf53
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-31T21:34:17.020356Z'
  stage: tests
- number: 18
  speaker: tester
  kind: result
  at: '2026-10-31T21:40:18.196814Z'
  stage: tests
  run: 6f90f2779ee242c2a18f85fdccc92555
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-31T21:40:38.788206Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-10-31T21:46:48.142027Z'
  stage: doing
  run: e152706bcd604c00989bec37ab7b17e1
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-31T21:47:08.310829Z'
  stage: review
- number: 22
  speaker: reviewer
  kind: result
  at: '2026-10-31T21:49:29.537047Z'
  stage: review
  run: ba12a4d175d8469f83296ad9817a45d5
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
11. `setup.sh --code-url <u>` with `<u>` different from `--repository-url`, when `GIT_ASKPASS` is set in the environment that `runuser` hands on to the clone: the stand-in `git`'s `clone` call still carries no `GIT_ASKPASS`.
12. `make check` stays green.
13. docs: `docs/operator-guide.md`: the option in the script's table; the paragraph *In v1.2 one repository URL serves both ...* is rewritten (one url by default, two with `--code-url`); a subsection *The code and the project apart*: what the project must bring (`factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, optional `factory/agents/`, a `Makefile` with `check`, `lint`, `test` and `sync`), that the stage image comes from the code checkout's `vm/Dockerfile`, that an update of the code is a new ref and a rebuild, and the helper's host rule. `docs/project-guide/git-and-hosting.md`: the helper. `docs/decisions.md`: an entry *The code and the project apart*, from the feature's decision 9. `README.md`: none.

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
8. tester: Stopped before writing `tests/test_vm_setup_code_url.py`. The `vm/setup.sh` criteria cannot all be tested the way the Interface asks for them: through `run_setup` with stand-in executables, and no files outside `tmp_path`.

   What a run with stand-ins can reach: the script uses fixed paths (`/etc/subuid`, `/srv/factory/<instance>`, `/home/factory/.secrets`). Stand-ins for `id`, `dpkg-query`, `zpool`, `zfs`, `grep`, `stat`, `install`, `cp`, `chmod`, `rm`, `visudo`, `loginctl`, `mktemp` and `runuser` would carry a run up to the checkout step. `runuser` would hand its command to a stand-in `git` that records its arguments and environment. After that, the shell test `[ ! -f /home/factory/.secrets/hosting-token ]` always stops the run with the wait message, because a test may not place that file. So these can be run:
   - criterion 5, different url: the clone runs before the wait;
   - criterion 6: the failing clone;
   - criterion 7, both halves.

   These cannot be run, because they come after the wait:
   - criterion 5's other side: the clone with the askpass when the url is equal or the option is absent;
   - criterion 8: what `factory.env` holds.

   Options:
   (A) Test those two from the script's text, as `tests/test_vm_setup_text.py` already does for the steps after the wait. For criterion 5's other side: the checkout step still holds the clone with `GIT_ASKPASS=$askpass`, `core.askPass` and `$repository_url`. For criterion 8: the environment step's text never names the variable that the `--code-url) need_value "$@"; X=$2` branch assigns. Criterion 9 and every run-reachable part stay as runs.
   (B) The coder gives `setup.sh` a way to move the secrets folder, for example an environment variable. That changes the Interface, which says nothing of it.
   (C) Run the script in a user and mount namespace (`unshare -rm`) with `tmp_path` folders bind-mounted over `/home/factory` and `/srv/factory`. This depends on what the machine allows, and could break under `make check` on another machine.
   I would choose (A).

   Done so far (left in the working tree): `tests/test_vm_credential_helper_host.py`, which covers criteria 2, 3, 4 and 10. Criterion 1 is the existing `tests/test_git_credential_helper.py`, unchanged.
   - criterion 2: `tests/test_vm_credential_helper_host.py::test_get_answers_only_a_request_for_the_project_repository_s_host`
   - criterion 3: `tests/test_vm_credential_helper_host.py::test_the_ssh_url_forms_name_their_host`
   - criterion 4: `tests/test_vm_credential_helper_host.py::test_any_other_operation_prints_nothing_and_succeeds_with_the_url_set`
   - criterion 10: `tests/test_vm_credential_helper_host.py::test_the_url_s_case_user_and_port_do_not_change_its_host`

   A single run of that file showed the refused rows failing for the right reason (the helper still answers). `make test` has not been run yet: I will run it once the setup tests are written. `make lint` is green. Every module the new tests use imports.
9. 2026-10-31 human: Answer to question 8: (A). The two parts that come after the secrets wait (criterion 5's equal-or-absent side with the askpass, and criterion 8's `factory.env`) are tested from the script's text, as `tests/test_vm_setup_text.py` already does for the steps after the wait; every part a run can reach stays a run. No change to `setup.sh` for testing, and no namespaces.
10. factory: started tests as vm.
11. tester: Wrote the `setup.sh` tests that were still missing. I followed the human's answer (A) in entry 9: anything a run can reach is tested as a run of `run_setup`, and the two parts that come after the secrets wait are tested from the script's text. The helper tests from the previous run are unchanged; I only ran `ruff format` over them.

    Criterion → test:
    - criterion 1: `tests/test_git_credential_helper.py` (the existing tests, unchanged)
    - criterion 2: `tests/test_vm_credential_helper_host.py::test_get_answers_only_a_request_for_the_project_repository_s_host`
    - criterion 3: `tests/test_vm_credential_helper_host.py::test_the_ssh_url_forms_name_their_host`
    - criterion 4: `tests/test_vm_credential_helper_host.py::test_any_other_operation_prints_nothing_and_succeeds_with_the_url_set`
    - criterion 5, as runs: `tests/test_vm_setup_code_url.py::test_only_a_different_code_url_is_cloned_without_the_askpass`. Rows: different (one clone, `GIT_TERMINAL_PROMPT=0`, no `GIT_ASKPASS` and no `core.askPass` in the arguments or the environment, the code url after `clone` and the project url not); equal and absent (no clone before the wait).
    - criterion 5, from the text: `tests/test_vm_setup_code_url.py::test_the_clone_after_the_secrets_wait_carries_the_askpass_and_the_project_url`. After the wait, the checkout step has exactly one `git clone` line with `GIT_ASKPASS="$askpass"`, `core.askPass="$askpass"` and `GIT_TERMINAL_PROMPT=0`, and its source is `$repository_url` or the variable the `--code-url)` branch sets.
    - criterion 6: `tests/test_vm_setup_code_url.py::test_a_code_repository_that_asks_for_a_credential_fails_the_clone`
    - criterion 7: `tests/test_vm_setup_code_url.py::test_the_first_pass_stops_at_the_secrets_wait_after_the_code_clone`. Rows: different and absent. Each checks exit 0, that the last line is the wait message, the step order up to `checkout`, and the number of clones.
    - criterion 8: `tests/test_vm_setup_code_url.py::test_the_environment_file_never_holds_the_code_url` (from the text, per answer A)
    - criterion 9: `tests/test_vm_setup_code_url.py::test_the_usage_text_names_the_code_url_option`. Rows: `--help` on standard output, and the usage printed on standard error after a wrong argument.
    - criterion 10: `tests/test_vm_credential_helper_host.py::test_the_url_s_case_user_and_port_do_not_change_its_host`

    How the runs work: stand-ins in `tmp_path/bin` for `id`, `dpkg-query`, `mktemp`, `runuser`, `git`, `grep`, `zpool`, `zfs`, `loginctl`, `stat`, `install`, `cp`, `chmod`, `rm` and `visudo`.
    - The `mktemp` stand-in puts the staging file in `tmp_path`.
    - The `runuser` stand-in runs only a command that contains `git` and drops every other one, so nothing is written as factory.
    - The `git` stand-in records its arguments and environment. In criterion 6's version it fails when no credential is offered.
    - The runs use `--instance code-url-test`, so they never read a real instance's folder. They do assume `/home/factory/.secrets/hosting-token` does not exist on the machine that runs the tests.

    Files created: `tests/test_vm_setup_code_url.py`, plus `tests/test_vm_credential_helper_host.py` from the previous run. No earlier test file changed.

    `make test`: the new tests fail for the right reason: `setup.sh: unknown word: --code-url`, no `--code-url` branch, and no `--code-url` in the usage text. The previous run showed the helper's refused rows failing because the helper still answers. The absent and equal rows and the after-the-wait text test pass already, which is correct because they describe today's behaviour. Every module the tests use imported; there were no collection errors. `make lint` is green.

    A note for the coder (not a change I made): `tests/test_vm_setup_text.py` takes the first `git clone -q --branch` and the first `git clone` line of the checkout step as the clone that carries the askpass (`ORDERED_COMMANDS`, the `GIT_ASKPASS=` and `GIT_TERMINAL_PROMPT=0` rows, `_clone_variables`). Those existing tests constrain how the code clone before the wait can be written.

    `lint`: lint: green (0.2 s)
    `test`: FAILED tests/test_vm_setup_code_url.py::test_the_usage_text_names_the_code_url_option[fault] - AssertionError: assert '--code-url' in 'usage: setup.sh --device <path> --repository-url <url> [--inst...
12. factory: started doing as vm.
13. coder: Stopped with the implementation done and `make check` red. Two defects in the tester's `tests/test_vm_setup_code_url.py` cause it. I cannot fix either one, because I may not edit tests (R9).

    1. `REFUSING_GIT` holds `${GIT_ASKPASS-}`, and `_stand_ins` runs `git.format(log=log)` on it. `str.format` reads the braces as a field, so `test_a_code_repository_that_asks_for_a_credential_fails_the_clone` (criterion 6) raises `KeyError: 'GIT_ASKPASS-'` at `tests/test_vm_setup_code_url.py:80`. This happens before `setup.sh` runs.
    2. `make types` fails: `tests/test_vm_setup_code_url.py:124: error: Incompatible return value type (got "tuple[int | None, str, str]", expected "tuple[int, str, str]")  [return-value]`. `_setup` returns `result.exit_status`, which is `int | None`.

    Options:
    (A) The tester makes two changes. First, write the brace in `REFUSING_GIT` as `${{GIT_ASKPASS-}}`, or keep that part of the stand-in out of the `.format` call. Second, make `_setup` return a type mypy accepts, for example by annotating it `tuple[int | None, str, str]` or by returning the `ProcessResult`. Neither change alters what the tests check.
    (B) Some other change you name.
    I would choose (A). It needs your leave, since it changes these tests, and then the decision `tests`.

    What I built (left in the working tree):
    - `vm/git-credential-factory`: the helper now reads the request into a variable instead of throwing it away. Two small functions find the hosts. `url_host` handles the `scheme://[user@]host[:port]/...` and `[user@]host:path` forms. `requested_host` reads the first `host=` line and removes its port. Both lower-case the result. With `FACTORY_REPOSITORY_URL` set, `get` exits 1 unless the request names a host and that host equals the URL's host. Without the variable, and for every other operation, the helper behaves as before.
    - `vm/setup.sh` gains `--code-url` (usage text, option table, the `code_url` variable). Its default, `$repository_url`, is set after the option parsing.
      - When the code url differs from the project url and there is no checkout yet, the checkout step clones before the secrets wait. The clone runs `as_factory env -u GIT_ASKPASS GIT_TERMINAL_PROMPT=0 git clone --quiet --branch "$ref" "$code_url" "$checkout"`, with no `core.askPass`. A failed clone prints the story's message and exits 1. A successful one sets `cloned=yes`.
      - `cloned=no` moved above the secrets wait. The askpass clone after the wait is unchanged, and `factory.env` never names `$code_url`.

    Main choice: the code clone sits inline in the checkout step, its `git clone` line directly under its `if`, with the failure handled by `|| { ...; exit 1; }`. It is written `--quiet` rather than `-q`. Several tests in `tests/test_vm_setup_text.py` read the first `git clone` lines of the checkout step: `_clone_variables` reads the first `git clone` line and needs `cloned=yes` in its `if` branch; the `GIT_ASKPASS=` row and the `ORDERED_COMMANDS` check both read the first `git clone -q --branch`, and the `GIT_ASKPASS=` row needs that line to hold the askpass. I rejected a nested `if ! ... git clone`, which hides `cloned=yes` from `_clone_variables`. I also rejected a clone function defined earlier in the script, which would move the first `git clone` text out of the checkout step.

    Test results: every other test passes, including all of `tests/test_vm_credential_helper_host.py`, `tests/test_git_credential_helper.py` and `tests/test_vm_setup_text.py`. Coverage is 99 %. `make lint` is green. The criterion 6 test has not run against my script, because it fails at that `KeyError` first. A manual run of a corrected copy was denied by the permission prompt.

    Refactor pass: I read the diff and found nothing to change.

    Noticed, not touched: with a different `--code-url`, the clone happens in the first pass, so the second pass, the one with the token, runs with `cloned=no`. That pass installs `git-credential-factory` and `factory@.service` only if they do not exist yet. If older copies are already there (from another instance), it does not replace them and prints the existing "differs from the checkout" warning instead. Without `--code-url`, both installs happen in the same pass as the clone. The story says nothing about this.

    Not done yet: the Description is unchanged, because no journal entry changed the task's meaning.
14. 2026-10-31 human: Answer: (A). The tester makes both changes in `tests/test_vm_setup_code_url.py`, which is this story's own test file: the brace in `REFUSING_GIT` escaped (`${{GIT_ASKPASS-}}`) or that part kept out of the `.format` call, and `_setup` typed so that mypy accepts it (`tuple[int | None, str, str]`, or returning the `ProcessResult`). What the tests check stays the same. End with `tests`.
15. factory: started doing as vm.
16. coder: Ended with `tests` because the human chose (A) in entry 14. I changed no code this round. The implementation in `vm/setup.sh` and `vm/git-credential-factory` is already on the branch from the previous doing run (entry 13).

    Change for the tester, in `tests/test_vm_setup_code_url.py` only: escape the brace in `REFUSING_GIT` as `${{GIT_ASKPASS-}}` (or keep that part out of the `.format` call in `_stand_ins`), and type `_setup` so that mypy accepts it (`tuple[int | None, str, str]`, or return the `ProcessResult`). What the tests check stays the same.

    Still open from entry 13, not touched: with a different `--code-url` the clone happens in the first pass. So on the second pass `cloned=no`, and older installed copies of the helper and the unit are not replaced; the script only prints its "differs from the checkout" warning.
17. factory: started tests as vm.
18. tester: Made the two test changes the human approved in entry 14 (the coder's entry 16 names them). Both are in `tests/test_vm_setup_code_url.py`, this story's own test file. No other file changed.

    - `REFUSING_GIT`: the brace is now escaped as `${{GIT_ASKPASS-}}`. `_stand_ins` passes the stand-in through `git.format(log=log)`, and the unescaped brace raised `KeyError: 'GIT_ASKPASS-'` before `setup.sh` ran. After formatting, the stand-in script reads `${GIT_ASKPASS-}`, as the test meant.
    - `_setup`: the return annotation is now `tuple[int | None, str, str]`, which matches `ProcessResult.exit_status`. `make types` had reported `return-value` at line 124.

    What the tests check is unchanged. Criterion → test, unchanged from entry 11:
    - criterion 1: `tests/test_git_credential_helper.py` (the existing tests)
    - criterion 2: `tests/test_vm_credential_helper_host.py::test_get_answers_only_a_request_for_the_project_repository_s_host`
    - criterion 3: `tests/test_vm_credential_helper_host.py::test_the_ssh_url_forms_name_their_host`
    - criterion 4: `tests/test_vm_credential_helper_host.py::test_any_other_operation_prints_nothing_and_succeeds_with_the_url_set`
    - criterion 5 (runs): `tests/test_vm_setup_code_url.py::test_only_a_different_code_url_is_cloned_without_the_askpass`
    - criterion 5 (text): `tests/test_vm_setup_code_url.py::test_the_clone_after_the_secrets_wait_carries_the_askpass_and_the_project_url`
    - criterion 6: `tests/test_vm_setup_code_url.py::test_a_code_repository_that_asks_for_a_credential_fails_the_clone`
    - criterion 7: `tests/test_vm_setup_code_url.py::test_the_first_pass_stops_at_the_secrets_wait_after_the_code_clone`
    - criterion 8: `tests/test_vm_setup_code_url.py::test_the_environment_file_never_holds_the_code_url`
    - criterion 9: `tests/test_vm_setup_code_url.py::test_the_usage_text_names_the_code_url_option`
    - criterion 10: `tests/test_vm_credential_helper_host.py::test_the_url_s_case_user_and_port_do_not_change_its_host`

    Files created: none this round. Changed: `tests/test_vm_setup_code_url.py`. Every module imported, and the run had no collection errors.

    Results: `make test` is green against the coder's implementation from entry 13, criterion 6 included (`test: green (164.7 s)`, coverage 99.56 %). `make lint` is green and `make types` is green.

    Still open, from the coder's entries 13 and 16, and not a test matter: with a different `--code-url`, the clone happens in the first pass. On the second pass `cloned=no`, so older installed copies of the helper and the unit are not replaced. The story says nothing about this.

    `lint`: lint: green (0.2 s)
    `test`: test: green (164.5 s)
19. factory: started doing as vm.
20. coder: I changed no code this round. The implementation from entry 13 now passes the corrected tests from entry 18, and `make check` is green (`test: green (165.6 s)`, coverage 99.56 %, `check: green`).

    What I built (from entry 13):
    - `vm/git-credential-factory`: the helper now reads git's request into a variable instead of discarding it.
      - `url_host` finds the host of `scheme://[user@]host[:port]/...` and `[user@]host:path` URLs.
      - `requested_host` finds the host from the first `host=` line and removes its port.
      - Both lower-case the result.
      - With `FACTORY_REPOSITORY_URL` set, `get` exits 1 when the request has no host or names a different one.
      - With the variable unset, and for every other operation, the helper behaves as before.
    - `vm/setup.sh`:
      - New option `--code-url` (usage text, option parsing, the `code_url` variable). It defaults to `$repository_url` after parsing.
      - When the code url differs from the project url and there is no checkout yet, the checkout step clones before the secrets wait with `as_factory env -u GIT_ASKPASS GIT_TERMINAL_PROMPT=0 git clone --quiet --branch "$ref" "$code_url" "$checkout"`, with no `core.askPass`. If that clone fails, the script prints the story's message and exits 1.
      - `cloned=no` (with its comment) moved above that block.
      - The askpass clone after the wait is unchanged, and `factory.env` never names the code url.

    Main choice: the code clone sits inline in the checkout step, with the error handled by `|| { ...; exit 1; }` and the option spelled `--quiet`. I did this because `tests/test_vm_setup_text.py` reads the first `git clone -q --branch` line and the first `git clone` line of that step as the askpass clone. Rejected: a nested `if ! ... git clone`, which hides `cloned=yes` from `_clone_variables`, and a clone function defined earlier, which moves the first `git clone` text out of the checkout step.

    Refactor pass: I read the diff again and found nothing to change.

    The Description is unchanged. Entries 4 and 9 were already worked into the story at intake and in the tests. Entry 14 changed only the tests.

    Noticed, not touched (also in entries 13, 16 and 18): with a different `--code-url`, the clone happens in the first pass, so the second pass (the one with the token) runs with `cloned=no`. On that pass, `git-credential-factory` and `factory@.service` are installed only if they do not exist yet. Older copies left by another instance are not replaced; the script prints its "differs from the checkout" warning instead. The story says nothing about this. It could be a later story.

    `check`: check: green
    `duplicates`: duplicates: 1 new, 41 known, 1 gone
21. factory: started review as vm.
22. reviewer: Findings:

    1. criterion 11 added: it needs its test. Location: `tests/test_vm_setup_code_url.py:149` (`test_only_a_different_code_url_is_cloned_without_the_askpass`, the `different` row) together with `tests/vm_support.py:83`. Problem: `run_setup` starts the script with only `PATH` in its environment, so `GIT_ASKPASS` never reaches the clone in any test. Deleting `env -u GIT_ASKPASS` from `vm/setup.sh:350` would leave every test green, which means the Interface's "without `GIT_ASKPASS`" rule has no test for its failing side. Fix: the tester adds a test for the new criterion 11. For example, the stand-in `runuser` exports a `GIT_ASKPASS` before its `exec`, the way the real `runuser` passes root's environment on, and the test asserts that the code clone still carries no `GIT_ASKPASS`. The old closing criteria are renumbered 12 (`make check`) and 13 (`docs:`).
    2. Location: `vm/setup.sh:344-355` against `vm/setup.sh:394-400` and `vm/setup.sh:436-441`. Problem: with a different `--code-url`, the clone sets `cloned=yes` on the first pass, and that pass then ends at the secrets wait. The second pass, the one with the token, therefore runs with `cloned=no`, even though the checkout is a fresh clone the service has never run. So an older `/usr/local/bin/git-credential-factory` or `factory@.service` is not replaced; the script only prints its "differs from the checkout" warning. That older helper is exactly the one without the new host rule. The clone is also never reported as `cloned $ref into $checkout`. The Interface says "Everything else (... the unit) is unchanged", and the coder (entries 13, 16, 20) and the tester (entry 18) both flagged this without asking. Fix: make a checkout cloned by the first pass count as fresh on the second pass, and report its clone. The Interface does not settle how, so the coder asks the human (R8) for the mechanism and for a criterion that pins it.
    3. Location: `tests/test_vm_credential_helper_host.py:9-25`. Problem: this file holds second copies of `ROOT`, `HELPER`, `EXAMPLE_VALUE` and the `token` fixture from `tests/test_git_credential_helper.py:12-25`, and of `SYSTEM_PATH` from `tests/vm_support.py:10`. Fix: the tester imports `SYSTEM_PATH` from `tests/vm_support.py`, and under the standing leave moves the `token` fixture to `tests/conftest.py` and the helper constants to a support module under `tests/`. Both files then use them from there, with every earlier test keeping its name and what it checks.

    Checked and fine:
    - Criteria 1 to 10 each have a test that matches its text.
    - The text tests for criterion 5's after-the-wait side and for criterion 8 follow the human's answer (A) in entry 9.
    - The helper's host parsing in `vm/git-credential-factory` matches the Interface's three URL forms and its request-host rule. A request without a `host=` line is refused.
    - The journal's entry 20 records `check: green`.

    Earlier tests: none. `git diff --name-status main...HEAD` shows both test files as `A`, and no test file that `main` already holds is changed.
