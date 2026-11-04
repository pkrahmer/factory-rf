---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 296
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T22:45:09.178149Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T22:48:45.853511Z'
  stage: acceptance
  run: 715f68b6be614e04bccdce6faed3b6a2
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-19T22:50:04.430287Z'
  stage: done
stories: [F0025-S0001, F0025-S0002, F0025-S0003, F0025-S0004, F0025-S0005]
outcome: accepted
---

# Acceptance of The project guide split by domain

## Recommendation

**Accepted.** S0005 closed the one finding of A0003: `factory.application.project_agents` and `factory.application.provider_limits` are now on the index lines of the files that describe them. The feature smoke test is green in every part: the move, the references, the file sizes, the index's sections and modules, and the document check over all twelve files. `make check` is green. No story is proposed. One question stays open for the human under 6 (B, how the index stays complete), unchanged from A0003.

## 1 Scope

The five archived stories, against `feature.md`:

- **S0001 to S0004** are as A0003 found them: S0001 built every scope bullet (the constants and `is_guide_file` in `src/factory/domain/documents.py`, the loop in `src/factory/entry/check_documents.py`, the move, the references in `README.md`, `docs/operator-guide.md` and `docs/decisions.md`); S0002 and S0004 completed the index; S0003 pinned the line-edge behaviour of the wording check.
- **S0005** (A0003's proposal) was documents only. Its diff (`22db1047`) changes two lines of `docs/project-guide/README.md`, *The files*: the `agents.md` line gains `factory.application.project_agents` and the `stages.md` line gains `factory.application.provider_limits`, each in the order the criterion names. Its tester (entry 5), coder (entry 7) and smoke tester (entry 13) confirm that nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed.

No story went outside the scope, and every out-of-scope item still holds (single template and demo guide, single operator guide and decision log, code tree not moved, no lasting layout or length test, documenter's lesson untouched, no paid call).

The human's changes:
- **Change 1** is on `main` (smoke part 1).
- **Change 2:** outside `done/`, only two `feature.md` files name `docs/project-guide.md`: F0025's own and F0019's (fully archived). Both are history.
- **Change 3:** `wc -l docs/project-guide/*.md` gives README 144, agents 325, costs 89, git-and-hosting 199, processes-and-checks 208, stages 307, watching 276, work-items 377, write-guard 184 (2,109 in all). The largest is 377 lines, so no file is near 600. Since A0003 only S0005 changed the guide (`git log -- docs/project-guide/`).

The goal is reached.

## 2 Feature smoke test

What a user of the feature does, end to end:
1. An agent follows `CLAUDE.md` to the index.
2. From the index it finds the file for its module or section.
3. It finds the moved text unchanged.
4. The docs stage's check reads the whole guide and finds a v1 word anywhere in it.

The script is A0003's, with two changes:
- part 3 drops a subsection named in parentheses ("(with *The report of a mutation run*)") before comparing the `## ` sections. A0003 showed `False` there only because of that form;
- part 10 checks all five modules added to the index after the move (S0004's three and S0005's two).

The move is still compared between the guide before the split (`61077acb:docs/project-guide.md`) and the folder at the end of S0001's docs stage (`10b669bf`).

Command, from the root of the checkout: `uv run -q python -I "$d/feature_smoke.py"; echo "exit $?"`, with `$d` a `mktemp -d` folder removed on exit. The script:

```python
"""F0025 end to end: an agent goes from CLAUDE.md to the guide's index to its domain file; the docs stage checks every file."""
import re
import subprocess
from pathlib import Path

from factory.domain.documents import DOCUMENT_PATHS, check_documents, is_guide_file
from factory.domain.sections import sections, split_lines


def git_show(spec):
    return subprocess.run(["git", "show", spec], capture_output=True, encoding="utf-8", check=True).stdout


def parts(text):
    lines = split_lines(text)
    return {s.heading: "\n".join(lines[s.start : s.end]).rstrip() for s in sections(text)}


def heads(text, level):
    return {l[level + 1 :].strip() for l in text.splitlines() if l.startswith("#" * level + " ")}


found = {}
problems = []
# 1. The first instruction an agent reads leads to the index, and the index exists.
claude = Path("CLAUDE.md").read_text(encoding="utf-8")
form = Path("factory/story-form.md").read_text(encoding="utf-8")
print("1. CLAUDE.md names the index:", "`docs/project-guide/README.md` is the guide for agents" in claude,
      "| names the old file:", "docs/project-guide.md" in claude, "| story form names the folder:", "docs/project-guide/" in form,
      "| old file exists:", Path("docs/project-guide.md").exists())
files = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path("docs/project-guide").glob("*.md"))}
index = files["README.md"]
the_files = parts(index)["The files"]
listed = {m.group(1): line for line in the_files.splitlines() if (m := re.match(r"- `([^` ]+)`", line))}
print("2. files and lines:", {n: len(split_lines(t)) for n, t in files.items()}, "| index lists every file:", set(listed) == set(files),
      "| none over 600:", max(len(split_lines(t)) for t in files.values()) <= 600)
for name, text in files.items():
    seg = listed.get(name, "").split("Sections:")[-1].split("Subsections other files refer to:")[0]
    seg = re.sub(r"\(with [^)]*\)", "", seg)  # a subsection named in parentheses, as on the processes-and-checks.md line
    named = re.findall(r"\*([^*]+)\*", seg)
    if named != list(parts(text)):
        problems.append(f"{name}: the index lists {named}, the file has {list(parts(text))}")
print("3. the index lists each file's ## sections, in order:", not problems)
found["3"] = problems; problems = []
# 4. The move, against the guide before the merge and the folder at the end of S0001's docs stage.
old = parts(git_show("61077acb:docs/project-guide.md").replace("`docs/project-guide.md`", "`docs/project-guide/`"))
moved_parts = {n: parts(git_show(f"10b669bf:docs/project-guide/{n}")) for n in files}
for h, text in old.items():
    holders = [n for n, p in moved_parts.items() if h in p]
    if len(holders) != 1 or (h != "The document check" and moved_parts[holders[0]][h] != text):
        problems.append(f"moved wrongly: {h} {holders}")
print(f"4. {len(old)} old sections, each in one file and byte for byte unchanged at the move (but the named exceptions):", not problems)
changed_since = sorted(f"{n}: {h}" for n, t in files.items() for h, body in parts(t).items() if moved_parts[n].get(h) != body)
new_sections = sorted(f"{n}: {h}" for n, t in files.items() for h in parts(t) if h not in moved_parts[n])
print("   ## sections changed since the move:", len(changed_since), "| ## sections new since the move:", new_sections)
found["4"] = problems; problems = []
for doc in ("README.md", "docs/operator-guide.md", "CLAUDE.md"):
    t = Path(doc).read_text(encoding="utf-8")
    for f in re.findall(r"`(docs/project-guide[^`]*)`", t):
        problems += [f"{doc} names {f}, which is gone"] if not Path(f).exists() else []
    for f, sec in re.findall(r"`(docs/project-guide/[a-z-]+\.md)`, [\"*]([^\"*]+)[\"*]", t):
        if sec not in heads(Path(f).read_text(), 2) | heads(Path(f).read_text(), 3):
            problems.append(f"{doc}: {f} has no heading {sec!r}")
print("5. README.md, the operator guide and CLAUDE.md name guide files that hold what they name:", not problems)
found["5"] = problems; problems = []
# 6. From a module to its file: every module a domain file names is on that file's index line.
mods = {str(p.relative_to("src"))[:-3].replace("/", ".").removesuffix(".__init__") for p in Path("src/factory").rglob("*.py")}
named_by = {}
for n, t in files.items():
    if n == "README.md":
        continue
    for m in set(re.findall(r"factory\.(?:domain|application|adapters|entry)(?:\.[a-z_]+)+", t)):
        while m not in mods and m.count(".") > 2:
            m = m.rsplit(".", 1)[0]
        if m in mods:
            named_by.setdefault(m, set()).add(n)
gap = sorted(m for m, ns in named_by.items() if not any(f"`{m}`" in listed.get(n, "") for n in ns))
unguided = sorted(m for m in mods if not any(f"`{m}`" in line for line in listed.values()) and m not in named_by)
print(f"6. modules a domain file names: {len(named_by)}; on no index line of a file that names them: {gap}")
print(f"   modules under src/factory the guide names nowhere: {len(unguided)}: {unguided}")
# 7. Every '### ' heading another file refers to ("see *X*") is named in the index.
h2 = {n: heads(t, 2) for n, t in files.items()}
h3 = {n: heads(t, 3) for n, t in files.items()}
unresolved = []
for n, t in files.items():
    for ref in re.findall(r"see \*([^*]+)\*", t):
        home = [f for f in files if ref in h2[f] | h3[f]]
        if home and n not in home and not any(ref in h2[f] for f in home) and f"*{ref}*" not in the_files and "`" + home[0] + "`" not in t:
            unresolved.append(f"{n} -> {ref} ({home})")
print("7. cross-file references to a ### the index does not name:", unresolved)
# 8. The docs stage's check reads the whole guide.
texts = {p: Path(p).read_text(encoding="utf-8") for p in DOCUMENT_PATHS} | {f"docs/project-guide/{n}": t for n, t in files.items()}
print("8. the document check reads", sum(p in DOCUMENT_PATHS or is_guide_file(p) for p in texts), "files; findings:", check_documents(texts))
for edge in ("x\n\nEach ticket\nmoves.\n", "x\n\nThe run\nticket moves.\n", "x\n\nThe last ticket", "x\n\nThe last ticketed"):
    print("9. a v1 word at an edge in costs.md:", repr(edge), [f.message for f in check_documents(texts | {"docs/project-guide/costs.md": edge}) if "costs" in f.document])
# 10. S0004 and S0005: the five modules added after the move are on the lines of their files.
for f, m in (("watching.md", "factory.adapters.preflight_stamp_file"), ("watching.md", "factory.application.dispatcher"),
             ("watching.md", "factory.domain.tick_status"), ("agents.md", "factory.application.project_agents"),
             ("stages.md", "factory.application.provider_limits")):
    print(f"10. {f} line names {m}:", f"`{m}`" in listed[f].split("Sections:")[0])
print("problems by part:", found)
```

Output:

```
1. CLAUDE.md names the index: True | names the old file: False | story form names the folder: True | old file exists: False
2. files and lines: {'README.md': 144, 'agents.md': 325, 'costs.md': 89, 'git-and-hosting.md': 199, 'processes-and-checks.md': 208, 'stages.md': 307, 'watching.md': 276, 'work-items.md': 377, 'write-guard.md': 184} | index lists every file: True | none over 600: True
3. the index lists each file's ## sections, in order: True
4. 41 old sections, each in one file and byte for byte unchanged at the move (but the named exceptions): True
   ## sections changed since the move: 20 | ## sections new since the move: []
5. README.md, the operator guide and CLAUDE.md name guide files that hold what they name: True
6. modules a domain file names: 122; on no index line of a file that names them: []
   modules under src/factory the guide names nowhere: 9: ['factory', 'factory.adapters', 'factory.application', 'factory.domain', 'factory.domain.fault_paths', 'factory.domain.kill_point_cases', 'factory.domain.kill_points', 'factory.entry', 'factory.entry.health']
7. cross-file references to a ### the index does not name: []
8. the document check reads 12 files; findings: []
9. a v1 word at an edge in costs.md: 'x\n\nEach ticket\nmoves.\n' ["uses the v1 word 'ticket'"]
9. a v1 word at an edge in costs.md: 'x\n\nThe run\nticket moves.\n' ["uses the v1 word 'ticket'"]
9. a v1 word at an edge in costs.md: 'x\n\nThe last ticket' ["uses the v1 word 'ticket'"]
9. a v1 word at an edge in costs.md: 'x\n\nThe last ticketed' []
10. watching.md line names factory.adapters.preflight_stamp_file: True
10. watching.md line names factory.application.dispatcher: True
10. watching.md line names factory.domain.tick_status: True
10. agents.md line names factory.application.project_agents: True
10. stages.md line names factory.application.provider_limits: True
problems by part: {'3': [], '4': [], '5': []}
exit 0
```

`uv run -q python -m factory.entry.check_documents` prints `documents ok`.

The feature smoke test is **green** in every part:
- **Part 3** is now `True`. The index's `## ` lists match every file's sections and their order.
- **Part 4:** 20 sections have changed since the move, the same 20 as at A0003. Each was changed in the file of its domain, and no file has a `## ` section the move did not put there.
- **Part 6:** no module a domain file names is missing from that file's index line. A0003's two gaps are closed. The nine modules the guide names nowhere are expected: the five package roots, the three that the index describes in its own sections (*Kill points*, *Fault-injection paths*), and `factory.entry.health`, which only the operator guide describes (section 5).
- **Part 9:** a v1 word at the end of a line, at the start of a line, and at the end of the file is found, and a longer word that contains it is not.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **S0005** noticed nothing:
  - the coder's entry 7 reads "Noticed and not touched: nothing";
  - the documenter's entry 11 reads "Stale text noticed and not touched: nothing";
  - the reviewer's entry 9 had no remarks beyond the criteria. It notes that the coder's `duplicates: 5 new` cannot come from this branch.
- **`make duplicates`: 5 new, 33 known, 3 gone** (S0005 entry 7, and again today). As at A0003: four similar-code findings between `factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime`, and `unused class 'ManualWaiter'` in `src/factory/adapters/clock.py`. All are F0020's code and for F0020's acceptance. None is F0025's.
- **From A0003's items:** the two module gaps are closed by S0005. The index named a subsection in two forms, which was judged no defect and is unchanged. `factory.entry.health` is still described only in the operator guide.

## 5 The documentation as a whole

I read:
- `README.md`'s pointers to the guide;
- the index, in full;
- S0005's two changed lines;
- the operator guide's references to guide files (smoke part 5);
- the decision log's F0025 entries.

I found no contradiction between documentation and behaviour:
- every guide file that `README.md`, the operator guide and `CLAUDE.md` name holds the heading they name;
- *The document check* describes the command as built, and the command prints `documents ok`;
- every module a domain file names can now be found from the index.

Smaller points, unchanged from A0003 and with no story proposed:
1. On the `processes-and-checks.md` line, the index names a subsection as "(with *The report of a mutation run*)". The other lines use "Subsections other files refer to: …". These are two forms, not a contradiction.
2. `factory.entry.health` is described only in the operator guide. Describing it in the project guide would be new content, which is outside F0025's move-only scope. It belongs to a story that changes the module.

## 6 Decisions taken for the human

From `feature.md`, decisions 1 to 12, to accept or revisit:
1. one story;
2. the index and eight domain files;
3. about 600 lines a file, with no lasting length or layout test;
4. a byte-for-byte move with two exceptions and no links;
5. the move by script;
6. the check reads the index as the guide and the folder's other files for words only;
7. the template and the demo keep a single guide;
8. the other documents follow in the same story;
9. the leave for `tests/entry/test_check_documents.py`;
10. independence from F0020 to F0024;
11. testing in `tmp_path` plus the smoke test against `origin/main`;
12. building F0025 before F0020-S0005.

From the stories:
- the choices A0002 and A0003 listed for S0001 to S0004:
  - S0001's `a.md.bak` row;
  - S0003's reviewer-added criterion 3;
  - S0002's documenter choosing the index line for a module that several files name, and the wording "It also names …";
  - S0004's coder leaving both edits to the documenter;
- **S0005, coder entry 7:** the coder left the two-line edit to the documenter, by `CLAUDE.md` *Docs*. This is no decision of weight.

Open for the human, carried from A0003:
- **B. Keeping the index complete.** A0003's question has no answer on `main`: `claude/agents/documenter.md` is unchanged, and its line 74 still says only that the guide is an index plus one file per domain. The drift did not recur this time, because since A0003 no story of another feature has changed the guide; S0005 is the only commit there. The options, as before:
  1. keep things as they are, and let each acceptance catch a gap;
  2. add one line to the documenter's lesson: a module newly named in a domain file goes on that file's index line (a coder write path, which the feature put out of scope);
  3. make `make documents` check this, which revisits decision 3 and adds code.

  I would still choose option 2. I propose no story for it, because it is a change to a shipped agent's lesson and so the human's call.

Earlier tests changed:
- only `tests/entry/test_check_documents.py`, in S0001, under decision 9;
- S0002, S0004 and S0005 changed no test (S0005's reviewer, entry 9: "No test file is changed, renamed or deleted");
- S0003 only added test modules.

No earlier test was changed without leave.

## 7 The slow checks

The project offers nothing beyond the make targets: `make check`, `make duplicates` (a record) and `make documents` (a check of the docs stage). There is no image scan and no SBOM. `make mutants` is a sweep and was not run (check 3).

- `make check` is **green** as I found it: `test: green (46.9 s)`, total coverage 99.12 %.
- `.reports/junit.xml` holds 6,008 tests, 438.8 s summed. The slowest are F0020's time-limit rows and one fault path:
  - `tests.adapters.test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`: 5.0 s;
  - `tests.adapters.test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s;
  - two rows of `tests.adapters.test_opencode_sudo_time_limit`: 4.5 s each;
  - `tests.test_fault_paths_7_to_13::test_acceptance_container_lost_in_review_reruns_once_and_books_result[refused]`: 3.4 s.
- The 263 rows whose names hold `document` take at most 0.33 s each.
- `make duplicates`: 5 new, 33 known, 3 gone, all F0020's (section 4).

**Disk:** the Disk now line (acceptance) and the Disk at the previous record line (start) are identical: `/work` 970.4 GB free with 0.5 GB used, and `/state` and `/tmp` at 0.0 GB used. There is no growth, which fits S0005's two changed lines.

## 8 Cost

The five stories cost 38 runs, 24.6 min, 206 turns, 699,723 tokens in (3,241,792 more from cache), 66,483 out and $6.34:

| Story | Runs | Minutes | Dollars |
|---|---|---|---|
| S0001 (the move, code and tests) | 10 | 9.7 | 2.74 |
| S0002 (the index) | 6 | 3.2 | 0.78 |
| S0003 (the line-edge tests) | 10 | 5.9 | 1.30 |
| S0004 (three modules, one sentence) | 6 | 3.4 | 0.76 |
| S0005 (two modules) | 6 | 2.4 | 0.76 |

- **S0001 still stands out**, at 43 % of the cost. It is the only story with code, tests and the scripted move of 1,900 lines.
- **S0005** went through each stage once, as A0003 predicted, at the same $0.76 as S0004. Its tester and coder runs did nothing and say so, at $0.26 together ($0.139 and $0.124 in its cost records). That is again the cost of a documents-only story going through the whole pipeline.
- The three acceptances before this one cost $5.92 (A0001 $2.69, A0002 $2.09, A0003 $1.15, from their cost records), more than S0002 to S0005 together ($3.60). A0003 alone cost $1.15 to find two index lines that S0005 then wrote for $0.76. That is one more reason for option B2 under 6.

**Human interventions:** 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

None. Nothing found is worth a story. The one open point (B under 6) is a change to a shipped agent's lesson, which the feature put out of scope, so it is left to the human.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed

   1. Scope: met. S0005 added `factory.application.project_agents` and `factory.application.provider_limits` to the index lines of the files that describe them, which closes A0003's only finding. Its diff (`22db1047`) changes two lines of `docs/project-guide/README.md` and nothing else. Nothing was built outside the scope, and the human's changes 1 to 3 hold: no file is near 600 lines, the largest has 377.
   2. Feature smoke test: green in every part.
      - All 41 sections moved byte for byte.
      - The index's `## ` lists match every file.
      - Every module a domain file names is on that file's index line.
      - The references in `README.md`, the operator guide and `CLAUDE.md` all point to headings that exist.
      - The document check reads 12 files with no findings and prints `documents ok`.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: nothing new from S0005. `make duplicates` reports 5 new, 33 known, 3 gone, all in F0020's runtimes and clock, so they belong to F0020's acceptance.
   5. Documentation: no contradiction between documentation and behaviour. Two small points are unchanged and need no story: the index names subsections in two different forms, and `factory.entry.health` is described only in the operator guide.
   6. Decisions: the feature's decisions 1 to 12 and the stories' choices stand. No earlier test was changed without leave. Question B from A0003 is still open: how should the index stay complete? I would still choose one line in the documenter's lesson. That is the human's call, since the feature put the lesson out of scope.
   7. Slow checks: nothing beyond the make targets.
      - `make check` is green: test 46.9 s, coverage 99.12 %, 6,008 tests.
      - The slowest tests are F0020's time-limit rows at 5.0 s; the document-check tests take at most 0.33 s.
      - Disk is unchanged since the previous record.
   8. Cost: 38 runs, 24.6 min, $6.34.
      - S0001 is $2.74 of that: the move, the code and the tests.
      - S0005 cost $0.76, of which $0.26 went to tester and coder runs that did nothing.
      - The three earlier acceptances cost $5.92 together.
      - 0 questions answered, 0.0 h waited.
3. factory: done (pull request merged); cost: 1 runs, 3.6 min, 13 turns, 53199 tokens in (536766 more from cache), 14614 out, $0.83
