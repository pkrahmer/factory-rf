---
stage: tests
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 504
comments_read: [6587261348, 6587570081]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-02T20:34:04.382650Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-02T20:04:36.696111Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-02T20:04:36.702623Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-02T20:05:01.663391Z'
  stage: intake
  run: b04f9f96f8fb48c3a789600d25108ec6
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-02T20:09:25.712373Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-02T20:09:43.743123Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-02T20:10:13.545245Z'
  stage: intake
  run: a229b72d539e4b05923d31a1ac71e056
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-02T20:10:34.304319Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-02T20:13:51.241620Z'
  stage: tests
  run: 4e9af38edc36406b8962510ba0c6aec9
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-02T20:14:12.364738Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-02T20:18:32.728722Z'
  stage: doing
  run: e280ad32b241486c861b1e98c959b188
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-02T20:18:53.526540Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-02T20:20:51.562510Z'
  stage: review
  run: 18a354a5c4a947ebb882269be0039272
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-02T20:21:12.127407Z'
  stage: doing
- number: 14
  speaker: coder
  kind: question
  at: '2026-11-02T20:21:37.677414Z'
  stage: doing
  run: c41d5d4dfdd9454a9627b190124b53aa
  blocked: question
- number: 15
  speaker: human
  kind: comment
  at: '2026-11-02T20:22:57.233222Z'
  stage: doing
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-02T20:23:15.192379Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-02T20:23:32.986391Z'
  stage: doing
  run: 96af4b3b71d1488790a8d22edb6c4b59
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-02T20:23:53.692552Z'
  stage: tests
- number: 19
  speaker: tester
  kind: result
  at: '2026-11-02T20:26:11.710266Z'
  stage: tests
  run: 147aa77b13454612b0999f6bf14236fe
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-02T20:26:32.712085Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-02T20:30:05.485883Z'
  stage: doing
  run: c95a9691100e444abe8ee2c0b75cec68
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-02T20:30:26.560832Z'
  stage: review
- number: 23
  speaker: reviewer
  kind: result
  at: '2026-11-02T20:32:51.228059Z'
  stage: review
  run: 0074ec284f954ff2a76e2d6e5db1e398
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-02T20:33:11.902725Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-11-02T20:33:43.715171Z'
  stage: doing
  run: 130eea06e6414c70abb03ad956156942
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-02T20:34:04.382650Z'
  stage: tests
---

# A sanitiser with the site's own rules and a leak check

## Description

A log, a result or a note that leaves the operator's machine for a repository must not carry the site's names: its domain, its project, its repository, a token. The session of 2026-11-02 did this by a Python snippet pasted into every command, with the rules in the snippet. This story makes it one command, `operator/bin/sanitise`, with two uses: as a filter (`sanitise < raw > clean`) it applies the built-in rules (tokens, bearer JWTs, terminal escape codes) and then the site's own rules from a rules file, and `sanitise check FILE...` proves a file clean: it names every file and line where a rule's pattern still matches, never the text itself, so that a leak report is not a leak. The rules file is a value of the site (the patterns are the company's names), so it lies beside the site file, outside every repository; the repository holds the mechanism only. The story adds no use of the sanitiser (S0007 uses it for the job's log).

## Interface

`operator/bin/sanitise` (`sh` with `python3`; loads the site for `SITE_SANITISE_RULES` and the path of the site file)

```sh
sanitise                    # standard input to standard output, rules applied
sanitise check FILE...      # exit 0 and "sanitise: clean", or 1 naming file:line, or 3
```

- The rules file is `$SITE_SANITISE_RULES`, else `sanitise.rules` in the folder of the site file. Its lines are blank, a comment (`#`), `PATTERN => REPLACEMENT` (the pattern a Python regular expression, applied with `re.sub`, case sensitive; the replacement literal text except for `\1` to `\99`, each naming that group of the pattern (two digits read as one number; a group that took no part in the match gives empty text); every other backslash stays a literal backslash), `drop: PATTERN` (a line that matches is removed), or `leak: PATTERN` (a pattern that the check reports and the filter leaves alone). The first ` => ` of a line splits it; leading and trailing whitespace of both parts is removed. A line of another kind, a pattern that is empty (on any of the three kinds), a pattern that is not a valid regular expression, or a replacement that names a group higher than the pattern's group count (reason `replacement names group 2, the pattern has 1`), stops the command with `sanitise: <path>:<line>: <reason>` and status 2; `check` stops the same way, with the same message and status, before it reads any file. The rules are numbered 1-based in file order, counting only rule lines (`=>`, `drop:`, `leak:`), never blank or comment lines.
- The built-in rules, applied before the site's, in this order: remove ANSI escape sequences (`\x1b\[[0-9;]*[A-Za-z]`); replace `eyJ` followed by two further dot-separated base64url parts (each at least 10 characters) with `***JWT***`; replace `gh[pousr]_[A-Za-z0-9]{20,}` and `github_pat_[A-Za-z0-9_]{20,}` with `***TOKEN***`.
- A filter without a rules file prints `sanitise: no rules file at <path>; only the built-in rules apply` to standard error once and goes on. `check` without one prints `sanitise: no rules file at <path>; nothing to check against` and returns 3.
- `check` reads each file and, for every line, tests the built-in token patterns (before replacement) and every site pattern (each rule's left side, each `drop:` pattern and each `leak:` pattern; all three built-ins, `builtin-3` for both the `gh[pousr]_` and the `github_pat_` form). For each line that matches it prints `<file>:<line>: <n>` to standard output, `<n>` the number of the rule in the order of the file (a built-in is `builtin-1`, `builtin-2`, `builtin-3`), once per line and rule. It never prints a matched text. When nothing matched it prints `sanitise: clean` and returns 0; else 1. `check` makes sure every named file exists before it reads any: a missing file returns 2 with `sanitise: <file>: no such file` and nothing else on standard output.
- The filter keeps the order of the lines, applies the rules line by line, and ends every line with a newline (a last line without one gets one; an empty input gives an empty output).

Tests: `tests/test_operator_sanitise.py`, running the command as a child process with a site file and a rules file in `tmp_path`.

## Acceptance criteria

1. The built-in rules, as rows of one parametrized test over one input line each: a line with an escape sequence `\x1b[31mred\x1b[0m` becomes `red`; a line holding a three-part JWT (made of `eyJabcdefghij.abcdefghij1.abcdefghij2`) has it replaced by `***JWT***`; `ghp_` followed by 30 letters and `github_pat_` followed by 30 letters each become `***TOKEN***`; a text that only starts like a token (`ghp_short`, `eyJabc.def`) is unchanged; the size limits on both sides: a JWT whose second part has 9 characters, and one whose third part has 9, is unchanged, and each with that part at 10 is replaced; `ghp_` and `github_pat_` followed by 19 characters are unchanged, and by 20 replaced.
2. A site rule `corp\.example\.invalid => <company-host>` replaces every occurrence in a line; a rule with a group (`(\d+)-secret => \1-x`) keeps the group. As rows of one parametrized test of the filter: the match is case sensitive (`CORP.EXAMPLE.INVALID` is unchanged by the host rule); a rule `  spaced   =>   S  ` turns `spaced` into `S` (both parts trimmed); a rule `first => one => two` turns `first` into `one => two` (the first ` => ` splits); in the replacement, a backslash other than `\1` to `\99` stays literal (`tab => x\ty` gives `x\ty`, `zero => x\0y` gives `x\0y`), two digits are one group number (`(a)(b)(c)(d)(e)(f)(g)(h)(i)(j) => \100` turns `abcdefghij` into `j0`), and a group that took no part in the match gives empty text (`(a)|(b) => [\1\2]` turns `b` into `[b]`).
3. `drop:` removes the matching line from the output and keeps the other lines in their order; a `leak:` pattern does not change the filter's output.
4. The order: the built-ins are applied first, then the site's rules in the file's order, so that a site rule sees the text the built-ins left.
5. Faults of the rules file stop the filter with status 2 and nothing on standard output, as rows of one parametrized test: a line `no arrow here`, a pattern `[unclosed`, an empty pattern in each kind (`=> x`, `drop:`, `leak:`), a replacement naming a group the pattern lacks (`(\d+)-x => \2`, with the message `sanitise: <path>:<line>: replacement names group 2, the pattern has 1`, and `(\d+)-x => \10`, with `replacement names group 10, the pattern has 1`); each message names the path and the line number.
6. A missing rules file: the filter prints its warning to standard error once, applies the built-ins, and exits 0; `check` prints its message, runs no check and exits 3.
7. `SITE_SANITISE_RULES` in the site file (or the environment) names another rules file and wins over the default; a relative path is relative to the site file's folder.
8. `check` on a file with the line `host corp.example.invalid` (the rule of criterion 2) at line 3 prints `<file>:3: 1` and exits 1; on a file with a token at line 2 prints `<file>:2: builtin-3`; the printed lines contain neither the matched host nor the token.
9. `check` on a clean file prints `sanitise: clean` and exits 0; on two files, one clean and one not, it reports the one and exits 1; on a leaking file followed by a missing one it prints only `sanitise: <file>: no such file` (no report of the first) and exits 2.
10. A line that matches two rules is reported once for each rule; a rule that matches two lines is reported for both lines; a line that matches one rule twice (`alpha alpha`) is reported once, and a line holding both a `ghp_` and a `github_pat_` token is reported `builtin-3` once.
11. A sanitised output passes `check` against the same rules whenever the replacements do not themselves match a pattern (a test: a mixed input filtered, then checked: `sanitise: clean`).
12. `check` tests every built-in, as rows of one parametrized test: a line with an escape sequence is reported `builtin-1`, a JWT `builtin-2`, a `ghp_` token and a `github_pat_` token each `builtin-3`; a line holding only a near-token (a JWT with a 9-character part, `ghp_` or `github_pat_` with 19 characters) gives `sanitise: clean`.
13. Rule numbers in `check` count only rule lines: a rules file of a comment, a blank line, a `=>` rule, a comment, a blank line and a `drop:` rule reports a line matching the `drop:` pattern as `<file>:<line>: 2`; a `leak:` pattern is reported by number too.
14. A last line without a newline gets one in the output; an empty input gives an empty output.
15. A rules-file fault stops `check` with status 2, the same message as the filter's (path and line number), and no report of any file, over the same fault rows as criterion 5 (the group rows included, with their messages).
16. `SITE_SANITISE_RULES` in the environment wins over the one in the site file; a relative path in it is relative to the site file's folder.
17. A wrong call or a missing site file stops the command with status 2 and nothing on standard output, as rows of one parametrized test: an argument other than `check` and `check` without a file each print the usage line `usage: sanitise < raw > clean | sanitise check FILE...` to standard error; a missing site file prints the site's own message `site: no site file at <path>; run: site init` to standard error.
18. `make check` stays green.
19. docs: `docs/operator-guide.md`, in the site file's part: a section *Sanitising what leaves the machine* (the rules file's place and format, the built-in rules, `check`, and that the rules file is the site's and never goes into a repository); `README.md` and the other documents: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_PROJECT=p\n' > "$d/site.env"
printf '# rules\ncorp\\.example\\.invalid => <company-host>\ndrop: noise\n' > "$d/sanitise.rules"
printf 'a corp.example.invalid b\nnoise here\nlast\n' | FACTORY_SITE="$d/site.env" sh operator/bin/sanitise
```

Expect: two lines, `a <company-host> b` and `last`.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_PROJECT=p\n' > "$d/site.env"
printf 'corp\\.example\\.invalid => <company-host>\n' > "$d/sanitise.rules"
printf 'one\nat corp.example.invalid\n' > "$d/raw.txt"
FACTORY_SITE="$d/site.env" sh operator/bin/sanitise check "$d/raw.txt" > "$d/out"; echo "exit $?"
sed "s|$d|<d>|" "$d/out"
```

Expect: two lines, `exit 1` and `<d>/raw.txt:2: 1`.

## Journal

1. 2026-11-02 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. Questions on the Interface and the criteria:

   1. Rule numbering in `check`: "`<n>` the number of the rule in the order of the file". Does the count include only rule lines (`=>`, `drop:`, `leak:`), or also blank and comment lines? Does a `=>` rule count once? Does `drop:` count and get tested by `check`? The Interface lists "each rule's left side and each `leak:` pattern", which leaves `drop:` patterns out. I would choose: numbers count only rule lines, 1-based, in file order, and `drop:` patterns are tested like the others. Please state this in the Interface, and add a criterion with a `drop:` rule and a comment or blank line before the rule, so the numbering is tested.
   2. Built-ins in `check`: it "tests the built-in token patterns" and names `builtin-1..3`. Is `builtin-1` (ANSI escapes) tested by `check`, or only JWT (`builtin-2`) and tokens (`builtin-3`)? `builtin-3` covers two patterns (`gh[pousr]_` and `github_pat_`). Criterion 8 tests only `builtin-3` with one token form. I would choose: all three are tested. Please add criteria for `builtin-1` and `builtin-2`, and for both forms of `builtin-3`.
   3. "Ends every line with a newline" has no criterion. Add one with an input whose last line has no newline, and say whether an empty input gives empty output.
   4. Criterion 5 (faults) covers only the `drop:` empty pattern. An empty pattern on the left of `=>` (`=> x`) and an empty `leak:` pattern are not covered. Is an empty pattern a fault for all three kinds? I would choose yes, with a row for each. Also, does a rules-file fault stop `check` with status 2 and the same message? There is no criterion for that side of `check`.
   5. Criterion 9: for a missing file, does `check` print the reports of files read before it, or nothing? "does not read the others" is ambiguous about files that come before it. Please state which and test it.
   6. Criterion 7 has no row for the environment variable overriding the site-file value, which the Interface states ("or the environment") and decision 3 of the feature promises. Add one, and one for a relative path.

   The architecture is not a concern: it is a shell script under `operator/bin/`, as the feature scopes. The scope is within the feature (S0006, no use of the sanitiser yet). The smoke test commands are runnable and their `Expect:` lines are checkable.
4. 2026-11-02 human: 1. As you propose: numbers count only rule lines (`=>`, `drop:`, `leak:`), 1-based in file order, and `drop:` patterns are checked like the others; state it in the Interface and add the criterion with a comment and a blank line before a `drop:` rule.
   2. All three built-ins are checked; add criteria for `builtin-1` and `builtin-2` and rows for both forms of `builtin-3`.
   3. Yes, a criterion: a last line without a newline gets one; an empty input gives empty output.
   4. An empty pattern is a fault for all three kinds, a row each; a rules-file fault stops `check` too, with status 2 and the same message (a row).
   5. `check` makes sure every named file exists before it reads any: a missing file prints only its message, nothing else, and status 2. State it and test it with the missing file second.
   6. Yes, both rows: the environment's `SITE_SANITISE_RULES` wins over the site file's, and a relative path is relative to the site file's folder.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) carried into the story. I did not add anything of my own.
   - Interface: `operator/bin/sanitise` with its two forms. Written in from entry 4: the rule numbering (1-based, only `=>`, `drop:` and `leak:` lines), `drop:` patterns checked, all three built-ins checked (both forms of `builtin-3`), an empty pattern as a fault for all three kinds, a rules-file fault stopping `check` with status 2 and the same message, `check` testing that every named file exists before it reads any, and the trailing newline and empty-input behaviour.
   - Criteria: each is testable by one parametrized test or function. Every rule has its failing side. Criterion 5 gained the empty `=>` and `leak:` patterns. Criterion 9 now has the missing file second and prints only its message. New criteria 12 to 16 cover the built-ins in `check`, the numbering past comment and blank lines, the trailing newline, the rules-file fault in `check`, and the environment overriding the site file plus the relative path. The two closing criteria are now 17 and 18, still last.
   - Smoke test: both commands are runnable, and neither runs pytest. Each `Expect:` line is checkable against the output (two lines each).
   - Architecture: a shell script under `operator/bin/` with `python3`, as `feature.md` scopes it. It touches nothing in `src/factory`. The rules file lies beside the site file, outside any repository.
   - Scope: within S0006 of F0048. The story adds no use of the sanitiser (that is S0007), and nothing falls under "Out of scope".
7. factory: started tests as vm.
8. tester: Wrote the tests for `operator/bin/sanitise`. Each one runs the command as a child through `sh`, using `run_script` from `tests/operator_support.py`. The site file and the rules file sit in a folder under `tmp_path`, and `FACTORY_SITE` names the site file. The filter gets its standard input from a file through `sh -c`, because `ProcessRequest` has no stdin.

   - criterion 1: tests/test_operator_sanitise.py::test_built_in_rules_replace_escapes_jwts_and_tokens (rows: escape-sequence, jwt, ghp-token, github-pat-token, short-ghp, short-jwt)
   - criterion 2: tests/test_operator_sanitise.py::test_site_rule_replaces_every_occurrence_and_keeps_groups
   - criterion 3: tests/test_operator_sanitise.py::test_drop_removes_lines_and_leak_leaves_the_output_alone
   - criterion 4: tests/test_operator_sanitise.py::test_site_rules_see_the_text_the_built_ins_left_in_file_order
   - criterion 5: tests/test_operator_sanitise.py::test_rules_file_fault_stops_the_filter (rows: no-kind, invalid-pattern, and an empty pattern for `=>`, `drop:` and `leak:`; the fault is on line 3)
   - criterion 6: tests/test_operator_sanitise.py::test_missing_rules_file_warns_once_in_the_filter_and_stops_the_check
   - criterion 7: tests/test_operator_sanitise.py::test_named_rules_file_wins_over_the_default (rows: site-file-absolute, site-file-relative, environment-absolute)
   - criterion 8: tests/test_operator_sanitise.py::test_check_names_file_line_and_rule_but_never_the_text
   - criterion 9: tests/test_operator_sanitise.py::test_check_reports_clean_files_leaking_files_and_missing_files
   - criterion 10: tests/test_operator_sanitise.py::test_check_reports_once_per_line_and_rule
   - criterion 11: tests/test_operator_sanitise.py::test_sanitised_output_passes_the_check
   - criterion 12: tests/test_operator_sanitise.py::test_check_reports_every_built_in
   - criterion 13: tests/test_operator_sanitise.py::test_check_numbers_only_rule_lines
   - criterion 14: tests/test_operator_sanitise.py::test_filter_ends_every_line_with_a_newline
   - criterion 15: tests/test_operator_sanitise.py::test_rules_file_fault_stops_the_check_before_any_file (same fault rows as criterion 5)
   - criterion 16: tests/test_operator_sanitise.py::test_environment_rules_file_wins_over_the_site_file (rows: absolute, relative-to-site-folder)
   - criteria 17 and 18: not tests; they belong to `make check` and the docs stage.

   Some points the Interface does not settle, so the tests leave them open:
   - The Interface says which stream carries `check`'s messages only where it requires "nothing on standard output" or "nothing else". So for a missing rules file, a missing file and a rules-file fault in `check`, the tests look for the message in standard output and standard error together.
   - The filter's fault message is checked on standard error, since standard output must be empty.
   - The `<reason>` part of a fault message is not checked. Only the prefix `sanitise: <path>:<line>: ` is.

   Files created: `tests/test_operator_sanitise.py`. No earlier test file changed.

   Not importable or missing: `operator/bin/sanitise` does not exist yet, so the tests in the one run (`uv run pytest -q tests/test_operator_sanitise.py`) fail at run time, not at import. `make lint` is green.

   `lint`: lint: green (0.1 s)
   `test`: FAILED tests/test_operator_sanitise.py::test_environment_rules_file_wins_over_the_site_file[relative-to-site-folder] - AssertionError: assert 2 == 0
9. factory: started doing as vm.
10. coder: Built `operator/bin/sanitise` (a new file, executable). It is a `sh` wrapper that sources `operator/lib/site.sh`, runs `site_load` and works out the rules path. That path is `$SITE_SANITISE_RULES`, taken relative to the site file's folder unless it is absolute, or else `sanitise.rules` beside the site file. The environment wins over the site file because `site_load` never overwrites a variable that is already set. The wrapper then hands the mode, the rules path and the files to an inline `python3 -I -c` program, the same pattern as `operator/skill/kumpel/scripts/status.sh` and `operator/job/job.sh`.

    The program checks in this order:
    - A missing rules file: the filter warns once and applies only the built-ins; `check` stops with status 3.
    - Rules-file faults: status 2, `sanitise: <path>:<line>: <reason>`, with the physical line number.
    - For `check`, that every named file exists, before it reads any: status 2.

    After that it either filters line by line or scans: `<file>:<line>: <rule>` once per line and rule, then `sanitise: clean` / exit 0, or exit 1.

    Rules are numbered in file order, counting only `=>`, `drop:` and `leak:` lines. On a line, `drop:` and `leak:` are recognised by their prefix first; then the first ` => ` splits it. The line is padded with a space so that `=> x` still splits and its empty pattern is reported as a fault. Text is read as UTF-8 with surrogateescape, so binary bytes in a log pass through unchanged.

    Main choice: the Python is inline in the script, following the operator scripts' existing idiom. I rejected a separate `operator/lib/sanitise.py`. It would be a Python file outside `src/` that the project's ruff, mypy and structural checks were not designed for, and it would be a second way of embedding Python in the operator scripts.

    Refactor: the list of check patterns is now built once per run rather than once per line. Nothing else needed changing.

    Checks: all 38 tests in `tests/test_operator_sanitise.py` pass. Both smoke tests give the expected output (`a <company-host> b` and `last`; then `exit 1` and `<d>/raw.txt:2: 1`). `make check` is green.

    Noticed but not touched:
    - A `=>` replacement with a bad group reference (for example `\2` when the pattern has one group) is not refused when the rules are read. It fails with a Python traceback the first time it matches, because the Interface lists only empty and invalid patterns as faults. The traceback shows the replacement template, never the input line.
    - A missing or faulty site file makes `sanitise` exit 2 after `site_load`'s own message. The Interface does not say which status that case should have.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
11. factory: started review as vm.
12. reviewer: 1. criterion 18 added: it needs its test. It is new criterion 17 in `## Acceptance criteria`; the closing two are renumbered 18 and 19. `operator/bin/sanitise:12-15,147-152` exits 2 in two cases no criterion names. One is a wrong call (an argument other than `check`, or `check` without a file): it prints the usage line. The other is a missing site file (`site_load || exit 2`): it prints the site's own message. Fix: the tester adds one parametrized test with a row for each case: status 2, the message on standard error, nothing on standard output.
    2. `tests/test_operator_sanitise.py:76-77` and `:298-305` (criteria 1 and 12): the Interface's size limits are tested only on the accepted side.
       - JWT: the Interface says each part after `eyJ` has at least 10 characters. The only refused row, `eyJabc.def`, has no third part, so it passes whatever the limit is.
       - Tokens: no row tests `ghp_` or `github_pat_` at 19 versus 20 characters, and there is no short `github_pat_` row.
       - `check`: no near-token row shows that `check` stays clean.
       This is also a gap in the story: criterion 1 names only `ghp_short` and `eyJabc.def`. Fix: add these rows to the criterion 1 table, and the last one to the criterion 12 table:
       - a three-part JWT with a 9-character part, unchanged;
       - the same JWT with a 10-character part, replaced;
       - `ghp_` and `github_pat_` with 19 characters, unchanged;
       - `ghp_` and `github_pat_` with 20 characters, replaced;
       - a near-token line, reported `sanitise: clean`.
    3. `operator/bin/sanitise:62,88`: the `=>` replacement goes to `re.sub` as a template without any check.
       - A replacement escape such as `\t` becomes a tab, not the "literal text" the Interface promises.
       - A bad escape (`\d`) or a group the pattern lacks (`\2` with one group) fails only while filtering: a Python traceback on standard error and status 1, instead of `sanitise: <path>:<line>: <reason>` and status 2. Under S0007 that loses the job's log, and the traceback leaks the script's internals.
       This is also a gap in the story: the Interface states no failing side for a replacement. Fix:
       - check each replacement against its pattern when the rules are read, and refuse a bad one as a rules-file fault (status 2, path and line), in the filter and in `check`;
       - the coder asks the human to add this fault to the Interface, with a row in the fault tests of criteria 5 and 15;
       - either make the replacement truly literal apart from `\1`-style groups, or reword "literal text" in the Interface as a Python replacement template.

    Earlier tests: none. `tests/test_operator_sanitise.py` is the only test file in the diff, and it is new (status A).

    Groups 2 to 5 have no further findings:
    - The script lies under `operator/` and touches nothing under `src/`.
    - The Python program is a constant, run with `python3 -I -c`, and gets its values through argv.
    - No silencing marker.
    - No copied helper: `run_script` and `operator_environment` are reused from `tests/operator_support.py`.
    - The Description matches what was built, and the docs criterion still holds.
    - The journal states the main choice: Python inline in the script, rather than `operator/lib/sanitise.py`. One small correction: the precedents it cites, `status.sh` and `job.sh`, use `python3 -c` without `-I`.
13. factory: started doing as vm.
14. coder: Round 1. I read the review findings (entry 12) and `operator/bin/sanitise`. I changed nothing this round. Findings 1 and 2 are test changes for the tester:
    - the new criterion 17: wrong call and missing site file;
    - rows for the JWT and token size limits.

    Finding 3 needs a change to the Interface, which the reviewer asks me to put to you.

    Today, a `=>` rule's replacement goes to `re.sub` unchecked (`operator/bin/sanitise:60,88`). The Interface calls it "literal text with `\1`-style groups allowed", but `\t` turns into a tab. A bad escape (`\d`) or a group the pattern does not have (`\2` when there is one group) fails only when a line matches, with a Python traceback and status 1. Under S0007 that would lose the job's log.

    Question: what should a replacement be, and is a bad one a rules-file fault?

    - **A (my choice):** the replacement is truly literal except for `\1` to `\99`. Every other backslash stays a literal backslash. When the rules file is read, a group number higher than the pattern's group count is a fault, in the filter and in `check`: status 2, `sanitise: <path>:<line>: replacement names group 2, the pattern has 1`. The Interface gains that fault, and criteria 5 and 15 each gain a row (`(\d+)-x => \2` on line 3).
    - **B:** the replacement is a Python `re` replacement template (`\t`, `\g<name>` and so on work). The Interface's "literal text" changes to say so. A template Python refuses (a bad escape, a missing group) is a rules-file fault at read time, with the same rows in criteria 5 and 15.
    - **C:** leave it as it is and drop the finding. I advise against this: it leaves a traceback path open in the job's log.

    Once you answer, I will set the Interface and the criteria to match (I may write the work item). Then I will end with `tests`, naming three changes for the tester:
    - the criterion 17 test, one parametrized test: an argument other than `check`, and `check` without a file, each print the usage line; a missing site file prints the site's own message. All three have status 2 and nothing on standard output.
    - the size-limit rows of finding 2 in the criterion 1 and criterion 12 tables;
    - the new fault rows.

    I will then implement the code once those tests fail.

    I did not touch the reviewer's side note: the cited precedents `status.sh` and `job.sh` run `python3 -c` without `-I`, while `sanitise` uses `-I`.
15. 2026-11-02 human: A: a replacement is literal text except for `\1` to `\99`; every other backslash stays a literal backslash. A group number higher than the pattern's group count is a rules-file fault when the file is read, in the filter and in `check`: status 2, `sanitise: <path>:<line>: replacement names group 2, the pattern has 1`. This answer is the rule; add its rows to criteria 5 and 15 as you propose. Note: the work item is not in the coder's write paths, so leave its text to the next review (it may add criteria and correct the Interface sentence from this answer); end with `tests` naming the three changes.
16. factory: started doing as vm.
17. coder: Round 1, after the human's answer (entry 15). I changed no code and did not touch the work item, which is outside my write paths. The human's answer chose option A: a replacement is literal text except for `\1` to `\99`, and every other backslash stays a literal backslash. A group number higher than the pattern's group count is a rules-file fault at read time, in the filter and in `check`: status 2, `sanitise: <path>:<line>: replacement names group 2, the pattern has 1`. The next review may write this rule into the Interface and criteria 5 and 15.

    Three test changes for the tester:
    1. Criterion 17, one new parametrized test in `tests/test_operator_sanitise.py` with three rows:
       - an argument other than `check`;
       - `check` without a file;
       - a missing site file.
       Every row exits with status 2 and prints nothing on standard output. On standard error, the first two rows print the usage line `usage: sanitise < raw > clean | sanitise check FILE...`, and the third prints `site: no site file at <path>; run: site init`.
    2. Size-limit rows, from finding 2 of entry 12.
       In the criterion 1 table (`test_built_in_rules_replace_escapes_jwts_and_tokens`):
       - a three-part JWT with a 9-character part: unchanged;
       - the same JWT with a 10-character part: replaced by `***JWT***`;
       - `ghp_` and `github_pat_` each followed by 19 characters: unchanged;
       - `ghp_` and `github_pat_` each followed by 20 characters: replaced by `***TOKEN***`.
       In the criterion 12 table (`test_check_reports_every_built_in`), or beside it: a near-token line, which `check` reports as `sanitise: clean`.
    3. A new fault row in `test_rules_file_fault_stops_the_filter` (criterion 5) and in `test_rules_file_fault_stops_the_check_before_any_file` (criterion 15): the rule `(\d+)-x => \2` on line 3, status 2, the message prefixed `sanitise: <path>:3: `.
       The literal-backslash side of the rule may also get a filter row, for example `a => x\ty` gives a literal `x\ty`, not a tab. Without it, the replacement-literalness half of the answer has no test.

    Once those tests fail, I will implement them in `operator/bin/sanitise`:
    - a replacement function that expands only `\1` to `\99`;
    - a read-time check of each group number against `pattern.groups`.

    Still open: the reviewer's side note in entry 12. The precedents I cited, `status.sh` and `job.sh`, use `python3 -c` without `-I`. I left it as it is.
18. factory: started tests as vm.
19. tester: Round 1. I made the test change the coder named in entry 17, following the human's answer in entry 15 (option A). The only file changed is `tests/test_operator_sanitise.py`, and I created no files. Every earlier test keeps its name.

    1. Criterion 17 (wrong call or missing site file): `tests/test_operator_sanitise.py::test_wrong_call_or_missing_site_file_stops_the_command`. It is new, with three rows:
       - `other-argument`
       - `check-without-file`
       - `missing-site-file` (`FACTORY_SITE` names an absent file)

       Every row checks status 2 and empty standard output. On standard error it checks for the line `usage: sanitise < raw > clean | sanitise check FILE...` in the first two rows, and `site: no site file at <path>; run: site init` in the third.

    2. Size limits from finding 2 of entry 12:
       - **Criterion 1:** `::test_built_in_rules_replace_escapes_jwts_and_tokens` gains six rows. `jwt-part-of-9` (`eyJabcdefghij.abcdefghi.abcdefghij2`) stays unchanged, and `jwt-part-of-10` becomes `***JWT***`. `ghp-of-19` and `github-pat-of-19` stay unchanged, and `ghp-of-20` and `github-pat-of-20` become `***TOKEN***`.
       - **Criterion 12:** `::test_check_leaves_near_tokens_clean` is new and sits beside `test_check_reports_every_built_in`. It has three rows (the 9-character JWT, `ghp_`+19 and `github_pat_`+19), and each must give `sanitise: clean` and status 0.

    3. The new fault, `(\d+)-x => \2` on line 3:
       - **Criterion 5:** the shared `FAULTS` table gains a `missing-group` row, used by `::test_rules_file_fault_stops_the_filter`.
       - **Criterion 15:** the same row runs in `::test_rules_file_fault_stops_the_check_before_any_file`.

       Both tests check the prefix `sanitise: <path>:3: `, as the coder asked. They do not check the reason text `replacement names group 2, the pattern has 1`.

    4. The literal-backslash half of the answer (criterion 2, from entry 15): `::test_site_rule_replaces_every_occurrence_and_keeps_groups` gains a row, `other-backslash-literal`. The rules file gets a third rule, `tab => x\ty`, and the line `a tab` must give the literal `a x\ty`.

    One run, `uv run pytest -q tests/test_operator_sanitise.py`, gave three failures, all of the expected kind (wrong results, not import errors):
    - `[other-backslash-literal]`: the output has a real tab instead of the literal `\t`.
    - The two `[missing-group]` rows: status 1 instead of 2.

    The size-limit rows, the near-token rows and the criterion 17 rows already pass against the current script.

    `make lint`: green. No module failed to import.

    Open, for the next review:
    - The Interface sentence ("literal text with `\1`-style groups allowed") and criteria 5 and 15 do not yet state the human's rule from entry 15.
    - The reviewer's side note about `python3 -I` in the cited precedents is still open.

    `lint`: lint: green (0.1 s)
    `test`: FAILED tests/test_operator_sanitise.py::test_rules_file_fault_stops_the_check_before_any_file[missing-group] - AssertionError: assert 1 == 2
20. factory: started doing as vm.
21. coder: Round 1, implementing the human's answer (entry 15, option A) against the tester's changed tests (entry 19). The only file I changed is `operator/bin/sanitise`.

    What I built: a new function, `literal_replacement` in the embedded Python program, which replaces the raw template that went to `re.sub`.
    - When the rules are read, it splits a `=>` rule's replacement on `\1` to `\99`, and keeps every other backslash as literal text.
    - It checks each group number against `pattern.groups`. A number that is too high stops the command with `sanitise: <path>:<line>: replacement names group 2, the pattern has 1` and status 2. This happens in the filter and in `check` alike, because both read the rules through `parse_line` before they touch any input.
    - It returns a function that `pattern.sub` calls, which joins the literal pieces with the matched groups. A group that did not take part in the match gives the empty text, as `re.sub` does.

    Main choice: expand the groups myself with a function given to `re.sub`. I rejected escaping every backslash except `\N` and handing `re.sub` the escaped template. That needs a second, subtle escaping pass, and Python would still read `\10` its own way. Splitting the text once makes the read-time check and the expansion share one parse.

    Refactor: I read the diff and moved the split into literal text and group numbers out of the per-match function. Nothing else needed changing.

    `uv run pytest -q tests/test_operator_sanitise.py`: all 53 pass, including `[other-backslash-literal]` and both `[missing-group]` rows. `make check`: green.

    Noticed but not touched:
    - The Interface sentence ("literal text with `\1`-style groups allowed") and criteria 5 and 15 do not yet state the human's rule from entry 15. The work item is outside my write paths, so I left it for the next review, as the human said.
    - A two-digit reference reads greedily: `\10` names group 10, not group 1 followed by `0`. This follows "`\1` to `\99`" in the answer.
    - The reviewer's side note from entry 12 is still open. The precedents cited earlier, `status.sh` and `job.sh`, run `python3 -c` without `-I`.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
22. factory: started review as vm.
23. reviewer: Round 1 review of `operator/bin/sanitise` and `tests/test_operator_sanitise.py`, read against the work item. `make check` after the coder was green (entry 21).

    Work item corrected under the human's leave in entry 15, which says the review may "add criteria and correct the Interface sentence from this answer":
    - Interface: the replacement was "literal text with `\1`-style groups allowed". It now says "literal text except for `\1` to `\99` …; every other backslash stays a literal backslash". The fault list gains "a replacement that names a group higher than the pattern's group count (reason `replacement names group 2, the pattern has 1`)". It also states two behaviours the code already has: two digits are read as one group number, and a group that took no part in the match gives empty text.
    - Criteria 5 and 15 gain the group-fault rows with their messages. Criteria 1, 2, 10 and 12 gain the rows named below. All are test changes; nothing under `operator/` or `src/` needs to change.

    Findings (all group 1; the tester writes the tests, the code already behaves as stated):
    1. `tests/test_operator_sanitise.py:151,165,393` (criteria 5 and 15): the `missing-group` row checks only the prefix `sanitise: <path>:3: `, but entry 15 fixes the whole message. Fix: assert the full line `sanitise: <path>:3: replacement names group 2, the pattern has 1`. Also add a row `(\d+)-x => \10` with `replacement names group 10, the pattern has 1`, which pins the two-digit reading. Both rows run in both fault tests.
    2. `tests/test_operator_sanitise.py:100-120` (criterion 2): Interface rules with no test of their failing or other side:
       - "case sensitive": `CORP.EXAMPLE.INVALID` must stay unchanged;
       - whitespace of both parts trimmed: `  spaced   =>   S  ` gives `S`;
       - "the first ` => ` splits": `first => one => two` gives `one => two`;
       - the low edge of `\1`–`\99`: `zero => x\0y` gives `x\0y`;
       - the high edge: `(a)(b)(c)(d)(e)(f)(g)(h)(i)(j) => \100` turns `abcdefghij` into `j0`;
       - a group that took no part in the match: `(a)|(b) => [\1\2]` turns `b` into `[b]`.

       Fix: add these rows to the criterion 2 test, each row with its own rules file, since `(a)|(b)` would rewrite the other rows' lines.
    3. `tests/test_operator_sanitise.py:81-82` (criterion 1): the Interface says "each" of the two JWT parts has at least 10 characters, but only the second part's limit is tested; the third part has 11 characters in every row. Fix: add a 9-character third part (unchanged) and a 10-character third part (replaced). Add the 9-character third part to the near-token rows of criterion 12 (`:333-335`) too.
    4. `tests/test_operator_sanitise.py:273-282` (criterion 10): the Interface's "once per line and rule" is not tested for a line that matches one rule twice. Fix: add a line `alpha alpha`, reported once, and a line holding both a `ghp_` and a `github_pat_` token, reported `builtin-3` once.

    Groups 2 to 5 have no findings:
    - Architecture: a script under `operator/`, nothing under `src/`.
    - Security: the Python program is a constant run with `python3 -I -c`, and its values arrive through argv. There is no silencing marker, no traceback path is left for a bad replacement, and a report never prints the matched text.
    - Quality: the built-in patterns appear nowhere else in `operator/`, `src/` or `docs/`. `site_path` and `site_load` are reused from `operator/lib/site.sh`.
    - Work item hygiene: the journal states the main choice and what was rejected (entries 10 and 21). The Description matches what was built, and the docs criterion (19) still holds.

    Earlier tests: none. `tests/test_operator_sanitise.py` is the only test file in the diff, and it is new (status A).

    Notes:
    - `tests/test_operator_sanitise.py:338` `test_check_leaves_near_tokens_clean` is the refused side of the rule that `test_check_reports_every_built_in` (`:318`) tests. It could be rows of that one parametrized test (expected output `sanitise: clean`, status 0) instead of a separate function.
24. factory: started doing as vm.
25. coder: Round 2. I changed no code and no other file. The review in entry 23 left four findings, and each one is a test change against criteria that the reviewer already wrote into the work item. Following the stage rule, I end with `tests` and name them for the tester. All four are in `tests/test_operator_sanitise.py`:

    1. Criteria 5 and 15, in the shared `FAULTS` table used by `test_rules_file_fault_stops_the_filter` and `test_rules_file_fault_stops_the_check_before_any_file`:
       - The `missing-group` row should check the whole line `sanitise: <path>:3: replacement names group 2, the pattern has 1`, not only the prefix.
       - Add a row for `(\d+)-x => \10`, which must give `replacement names group 10, the pattern has 1`.
    2. Criterion 2, in `test_site_rule_replaces_every_occurrence_and_keeps_groups`: add one row for each of these, each with its own rules file:
       - `CORP.EXAMPLE.INVALID` stays unchanged under the host rule;
       - `  spaced   =>   S  ` turns `spaced` into `S`;
       - `first => one => two` turns `first` into `one => two`;
       - `zero => x\0y` gives `x\0y`;
       - `(a)(b)(c)(d)(e)(f)(g)(h)(i)(j) => \100` turns `abcdefghij` into `j0`;
       - `(a)|(b) => [\1\2]` turns `b` into `[b]`.
    3. Criterion 1, in `test_built_in_rules_replace_escapes_jwts_and_tokens`: add a JWT whose third part has 9 characters (unchanged) and one whose third part has 10 (replaced). Criterion 12: add the JWT with the 9-character third part to the near-token rows. Following the reviewer's note on entry 23, the near-token rows may become rows of `test_check_reports_every_built_in` (expected output `sanitise: clean`, status 0) instead of the separate `test_check_leaves_near_tokens_clean`.
    4. Criterion 10, in `test_check_reports_once_per_line_and_rule`: add a line `alpha alpha`, reported once, and a line holding both a `ghp_` and a `github_pat_` token, reported `builtin-3` once.

    I ran these cases by hand against the current `operator/bin/sanitise`, and each gave the result the criteria expect, so the new rows should pass with no code change:
    - every row of finding 2 gave the expected output with status 0;
    - the 9-character and 10-character third-part JWTs were left unchanged and replaced, respectively;
    - `\10` gave the full group-10 message with status 2;
    - `check` reported `alpha alpha` once as rule 1, and the line with both tokens once as `builtin-3`.

    What the journal changed: entries 15 and 23 changed the meaning of the task, and the reviewer has already written that change into the Interface and the criteria. I did not rewrite the Description, because the work item is outside my write paths.

    Noticed but not touched: the reviewer's side note in entry 12 is still open. The precedents I cited earlier, `status.sh` and `job.sh`, run `python3 -c` without `-I`.
26. factory: started tests as vm.
