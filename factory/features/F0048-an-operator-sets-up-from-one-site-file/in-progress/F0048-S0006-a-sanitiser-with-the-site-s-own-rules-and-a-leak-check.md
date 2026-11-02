# A sanitiser with the site's own rules and a leak check

## Description

A log, a result or a note that leaves the operator's machine for a repository must not carry the site's names: its domain, its project, its repository, a token. The session of 2026-11-02 did this by a Python snippet pasted into every command, with the rules in the snippet. This story makes it one command, `operator/bin/sanitise`, with two uses: as a filter (`sanitise < raw > clean`) it applies the built-in rules (tokens, bearer JWTs, terminal escape codes) and then the site's own rules from a rules file, and `sanitise check FILE...` proves a file clean: it names every file and line where a rule's pattern still matches, never the text itself, so that a leak report is not a leak. The rules file is a value of the site (the patterns are the company's names), so it lies beside the site file, outside every repository; the repository holds the mechanism only. The story adds no use of the sanitiser (S0007 uses it for the job's log).

## Interface

`operator/bin/sanitise` (`sh` with `python3`; loads the site for `SITE_SANITISE_RULES` and the path of the site file)

```sh
sanitise                    # standard input to standard output, rules applied
sanitise check FILE...      # exit 0 and "sanitise: clean", or 1 naming file:line, or 3
```

- The rules file is `$SITE_SANITISE_RULES`, else `sanitise.rules` in the folder of the site file. Its lines are blank, a comment (`#`), `PATTERN => REPLACEMENT` (the pattern a Python regular expression, applied with `re.sub`, case sensitive; the replacement literal text with `\1`-style groups allowed), `drop: PATTERN` (a line that matches is removed), or `leak: PATTERN` (a pattern that the check reports and the filter leaves alone). The first ` => ` of a line splits it; leading and trailing whitespace of both parts is removed. A line of another kind, or a pattern that is not a valid regular expression, stops the command with `sanitise: <path>:<line>: <reason>` and status 2.
- The built-in rules, applied before the site's, in this order: remove ANSI escape sequences (`\x1b\[[0-9;]*[A-Za-z]`); replace `eyJ` followed by two further dot-separated base64url parts (each at least 10 characters) with `***JWT***`; replace `gh[pousr]_[A-Za-z0-9]{20,}` and `github_pat_[A-Za-z0-9_]{20,}` with `***TOKEN***`.
- A filter without a rules file prints `sanitise: no rules file at <path>; only the built-in rules apply` to standard error once and goes on. `check` without one prints `sanitise: no rules file at <path>; nothing to check against` and returns 3.
- `check` reads each file and, for every line, tests the built-in token patterns (before replacement) and every site pattern (each rule's left side and each `leak:` pattern). For each line that matches it prints `<file>:<line>: <n>` to standard output, `<n>` the number of the rule in the order of the file (a built-in is `builtin-1`, `builtin-2`, `builtin-3`), once per line and rule. It never prints a matched text. When nothing matched it prints `sanitise: clean` and returns 0; else 1. A missing file returns 2 with `sanitise: <file>: no such file`.
- The filter keeps the order of the lines, applies the rules line by line, and ends every line with a newline.

Tests: `tests/test_operator_sanitise.py`, running the command as a child process with a site file and a rules file in `tmp_path`.

## Acceptance criteria

1. The built-in rules, as rows of one parametrized test over one input line each: a line with an escape sequence `\x1b[31mred\x1b[0m` becomes `red`; a line holding a three-part JWT (made of `eyJabcdefghij.abcdefghij1.abcdefghij2`) has it replaced by `***JWT***`; `ghp_` followed by 30 letters and `github_pat_` followed by 30 letters each become `***TOKEN***`; a text that only starts like a token (`ghp_short`, `eyJabc.def`) is unchanged.
2. A site rule `corp\.example\.invalid => <company-host>` replaces every occurrence in a line; a rule with a group (`(\d+)-secret => \1-x`) keeps the group.
3. `drop:` removes the matching line from the output and keeps the other lines in their order; a `leak:` pattern does not change the filter's output.
4. The order: the built-ins are applied first, then the site's rules in the file's order, so that a site rule sees the text the built-ins left.
5. Faults of the rules file stop the filter with status 2 and nothing on standard output, as rows of one parametrized test: a line `no arrow here`, a pattern `[unclosed`, a `drop:` with an empty pattern; each message names the path and the line number.
6. A missing rules file: the filter prints its warning to standard error once, applies the built-ins, and exits 0; `check` prints its message, runs no check and exits 3.
7. `SITE_SANITISE_RULES` in the site file (or the environment) names another rules file and wins over the default; a relative path is relative to the site file's folder.
8. `check` on a file with the line `host corp.example.invalid` (the rule of criterion 2) at line 3 prints `<file>:3: 1` and exits 1; on a file with a token at line 2 prints `<file>:2: builtin-3`; the printed lines contain neither the matched host nor the token.
9. `check` on a clean file prints `sanitise: clean` and exits 0; on two files, one clean and one not, it reports the one and exits 1; on a missing file it exits 2 with its message and does not read the others.
10. A line that matches two rules is reported once for each rule; a rule that matches two lines is reported for both lines.
11. A sanitised output passes `check` against the same rules whenever the replacements do not themselves match a pattern (a test: a mixed input filtered, then checked: `sanitise: clean`).
12. `make check` stays green.
13. docs: `docs/operator-guide.md`, in the site file's part: a section *Sanitising what leaves the machine* (the rules file's place and format, the built-in rules, `check`, and that the rules file is the site's and never goes into a repository); `README.md` and the other documents: none.

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
