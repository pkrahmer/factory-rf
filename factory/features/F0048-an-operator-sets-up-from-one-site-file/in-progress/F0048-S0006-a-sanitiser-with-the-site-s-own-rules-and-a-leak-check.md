---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 504
comments_read: [6587261348]
handed_over: null
claim: null
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

- The rules file is `$SITE_SANITISE_RULES`, else `sanitise.rules` in the folder of the site file. Its lines are blank, a comment (`#`), `PATTERN => REPLACEMENT` (the pattern a Python regular expression, applied with `re.sub`, case sensitive; the replacement literal text with `\1`-style groups allowed), `drop: PATTERN` (a line that matches is removed), or `leak: PATTERN` (a pattern that the check reports and the filter leaves alone). The first ` => ` of a line splits it; leading and trailing whitespace of both parts is removed. A line of another kind, a pattern that is empty (on any of the three kinds), or a pattern that is not a valid regular expression, stops the command with `sanitise: <path>:<line>: <reason>` and status 2; `check` stops the same way, with the same message and status, before it reads any file. The rules are numbered 1-based in file order, counting only rule lines (`=>`, `drop:`, `leak:`), never blank or comment lines.
- The built-in rules, applied before the site's, in this order: remove ANSI escape sequences (`\x1b\[[0-9;]*[A-Za-z]`); replace `eyJ` followed by two further dot-separated base64url parts (each at least 10 characters) with `***JWT***`; replace `gh[pousr]_[A-Za-z0-9]{20,}` and `github_pat_[A-Za-z0-9_]{20,}` with `***TOKEN***`.
- A filter without a rules file prints `sanitise: no rules file at <path>; only the built-in rules apply` to standard error once and goes on. `check` without one prints `sanitise: no rules file at <path>; nothing to check against` and returns 3.
- `check` reads each file and, for every line, tests the built-in token patterns (before replacement) and every site pattern (each rule's left side, each `drop:` pattern and each `leak:` pattern; all three built-ins, `builtin-3` for both the `gh[pousr]_` and the `github_pat_` form). For each line that matches it prints `<file>:<line>: <n>` to standard output, `<n>` the number of the rule in the order of the file (a built-in is `builtin-1`, `builtin-2`, `builtin-3`), once per line and rule. It never prints a matched text. When nothing matched it prints `sanitise: clean` and returns 0; else 1. `check` makes sure every named file exists before it reads any: a missing file returns 2 with `sanitise: <file>: no such file` and nothing else on standard output.
- The filter keeps the order of the lines, applies the rules line by line, and ends every line with a newline (a last line without one gets one; an empty input gives an empty output).

Tests: `tests/test_operator_sanitise.py`, running the command as a child process with a site file and a rules file in `tmp_path`.

## Acceptance criteria

1. The built-in rules, as rows of one parametrized test over one input line each: a line with an escape sequence `\x1b[31mred\x1b[0m` becomes `red`; a line holding a three-part JWT (made of `eyJabcdefghij.abcdefghij1.abcdefghij2`) has it replaced by `***JWT***`; `ghp_` followed by 30 letters and `github_pat_` followed by 30 letters each become `***TOKEN***`; a text that only starts like a token (`ghp_short`, `eyJabc.def`) is unchanged.
2. A site rule `corp\.example\.invalid => <company-host>` replaces every occurrence in a line; a rule with a group (`(\d+)-secret => \1-x`) keeps the group.
3. `drop:` removes the matching line from the output and keeps the other lines in their order; a `leak:` pattern does not change the filter's output.
4. The order: the built-ins are applied first, then the site's rules in the file's order, so that a site rule sees the text the built-ins left.
5. Faults of the rules file stop the filter with status 2 and nothing on standard output, as rows of one parametrized test: a line `no arrow here`, a pattern `[unclosed`, an empty pattern in each kind (`=> x`, `drop:`, `leak:`); each message names the path and the line number.
6. A missing rules file: the filter prints its warning to standard error once, applies the built-ins, and exits 0; `check` prints its message, runs no check and exits 3.
7. `SITE_SANITISE_RULES` in the site file (or the environment) names another rules file and wins over the default; a relative path is relative to the site file's folder.
8. `check` on a file with the line `host corp.example.invalid` (the rule of criterion 2) at line 3 prints `<file>:3: 1` and exits 1; on a file with a token at line 2 prints `<file>:2: builtin-3`; the printed lines contain neither the matched host nor the token.
9. `check` on a clean file prints `sanitise: clean` and exits 0; on two files, one clean and one not, it reports the one and exits 1; on a leaking file followed by a missing one it prints only `sanitise: <file>: no such file` (no report of the first) and exits 2.
10. A line that matches two rules is reported once for each rule; a rule that matches two lines is reported for both lines.
11. A sanitised output passes `check` against the same rules whenever the replacements do not themselves match a pattern (a test: a mixed input filtered, then checked: `sanitise: clean`).
12. `check` tests every built-in, as rows of one parametrized test: a line with an escape sequence is reported `builtin-1`, a JWT `builtin-2`, a `ghp_` token and a `github_pat_` token each `builtin-3`.
13. Rule numbers in `check` count only rule lines: a rules file of a comment, a blank line, a `=>` rule, a comment, a blank line and a `drop:` rule reports a line matching the `drop:` pattern as `<file>:<line>: 2`; a `leak:` pattern is reported by number too.
14. A last line without a newline gets one in the output; an empty input gives an empty output.
15. A rules-file fault stops `check` with status 2, the same message as the filter's (path and line number), and no report of any file.
16. `SITE_SANITISE_RULES` in the environment wins over the one in the site file; a relative path in it is relative to the site file's folder.
17. `make check` stays green.
18. docs: `docs/operator-guide.md`, in the site file's part: a section *Sanitising what leaves the machine* (the rules file's place and format, the built-in rules, `check`, and that the rules file is the site's and never goes into a repository); `README.md` and the other documents: none.

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
