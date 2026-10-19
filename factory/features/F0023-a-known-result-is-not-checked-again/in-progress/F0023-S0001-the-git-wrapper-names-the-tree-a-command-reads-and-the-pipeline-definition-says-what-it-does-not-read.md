---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 267
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T14:24:48.220000Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T14:24:48.227452Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T14:25:06.019383Z'
  stage: intake
  run: 3e4cc65b172b460691dec86d99fb6a73
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T14:25:26.681339Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T14:28:34.739919Z'
  stage: tests
  run: a2fe8bf5b0744716ac8312611cf8741d
---

# The git wrapper names the tree a command reads, and the pipeline definition says what it does not read

## Description

The factory cannot yet tell whether a project command would read the same input as an earlier run. The checks run on the work tree before the stage's result commit, so `HEAD` names the stage-start commit. Every commit also carries a new journal entry that the command may never read. This story gives S0002 the two things its key needs. First, the git wrapper gets a twenty-fourth operation, `work_tree_id(left_out)`: the id of the tree that a commit of the work tree would record right now, without the paths matching `left_out`. It is computed in a temporary index, so the checkout's index, `HEAD`, refs and work tree stay as they are. Second, each project command in the pipeline definition may say which paths it does not read, `not_read`, a list of patterns matched as write paths are; the default leaves nothing out. A pattern that cannot name a path inside the checkout is refused when the definition loads, with a fault that names the command and the pattern. The records contract's schema of the pipeline definition is regenerated, and its minor version raised. Nothing uses either yet: S0002 keys the known results on them.

## Interface

`factory.domain.git` (`domain`):

```python
TreeId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
```

- The pattern of `CommitId`: 40 lower-case hex characters.

`factory.application.git` (`application`):

```python
class Git(ABC):
    ...
    @abstractmethod
    def work_tree_id(self, left_out: Sequence[str] = ()) -> TreeId:
        """The tree a commit of the work tree would record now, less the paths matching `left_out`.

        Tracked files count with their content in the work tree, untracked files that are
        not ignored count, deleted and ignored files do not. A path is left out when
        `matches_any(path, left_out)`. The index, `HEAD`, the refs and the work tree stay
        as they are.
        """
```

`factory.adapters.git_cli` (`adapters`):

- `GitCli.work_tree_id(left_out=())` works in a temporary index: a file in a `tempfile.TemporaryDirectory()` outside the checkout, removed when the call returns and when it raises. The index starts as a copy of the checkout's own index when there is one, and empty otherwise: so git rehashes only changed files, and a tracked file that `.gitignore` matches stays in the tree, as it stays in the commit. It runs `git add --all` against the temporary index (`GIT_INDEX_FILE`), removes from it every listed path that `matches_any(path, left_out)` accepts, and returns `git write-tree`. Removed paths are passed as literal paths, never as pathspecs, so a name with `*`, `:` or `[` in it is removed exactly.
- The checkout's `.git/index` keeps its bytes, and `status()` and `resolve("HEAD")` give the same before and after the call.
- A failing git call raises `GitError` as every other operation does; a checkout without a commit is no error (its tree is that of the files it holds).

`factory.domain.pipeline_definition` (`domain`):

```python
class ProjectCommandDefinition(BaseModel):
    time_limit: PositiveInt = 10
    not_read: list[WritePath] = []
```

- `not_read` holds the patterns of the paths the command does not read, in the order written; `[]` when the key is absent. The strict model refuses a value that is not a list of strings, and `WritePath` refuses an empty or blank string.
- A new load rule, last in `_RULES`, gives for every command and every pattern of its `not_read` that starts with `/` or `~`, has a segment `..` (split at `/`), or holds `{` or `}`, the fault `project command <name>: not_read <pattern> must be a path pattern inside the checkout`. The faults come in the order of `project_commands`, then of each command's `not_read`, and are joined with the other rules' faults as today.
 The rule uses `is_inside_checkout`, which moves from `factory.domain.write_paths` into `factory.domain.pipeline_definition` (`write_paths` imports `pipeline_definition`, so the reverse import would be a cycle); `write_paths` and `confinement` import it from there (`mypy --strict` allows no implicit re-export, and ruff refuses `import ... as` the same name).

`factory.domain.contract` and `src/factory/contract/` (F0021-S0006's):

- `RECORDS_CONTRACT`'s minor is raised by one from the value it holds when this story starts (an optional field added, F0021's decision 15); the major stays.
- The five schemas are regenerated with `uv run python -m factory.entry.contract`, never by hand. The pipeline definition's `contract` stays `"1.0"` in every pipeline definition of the repository.
- F0021-S0006 is on `main` (archived in `done/`); after F0020-S0001 and S0005 the contract is `"1.2"`, so this story makes it `"1.3"`.

Unchanged: every other git operation, `matches_any`, the other load rules and their faults, `PipelineDefinitionReader`, the stop `pipeline_definition_invalid`.

Tests (the tester writes them): `tests/domain/test_tree_id.py`, `tests/adapters/test_git_cli_work_tree.py` (the `checkout` fixture of `tests/conftest.py`, `run_git` and `write_files` of `tests/git_support.py`), `tests/domain/test_pipeline_not_read.py` (texts built on `PIPELINE_YAML` of `tests/git_support.py`, read with `RuamelPipelineDefinitionReader`, as `tests/domain/test_tool_paths.py` does), `tests/entry/test_contract_not_read.py`.

Changed under the feature's decision 15, by the tester only, nothing else in those modules: `tests/application/test_git_interface.py`, whose `OPERATIONS` gains `"work_tree_id"` and whose test `test_git_has_exactly_the_twenty_three_operations_and_git_cli_has_each` is renamed `test_git_has_exactly_the_twenty_four_operations_and_git_cli_has_each`; `tests/application/test_interfaces.py`, the test `test_git_abstract_methods_are_exactly_its_twenty_three_operations` renamed `test_git_abstract_methods_are_exactly_its_twenty_four_operations`; in `tests/domain/test_contract.py` (one `"1.2"`) and `tests/domain/test_contract_provider_limit.py` (two `"1.2"`), and any later test module that pins the records contract's version as a literal, that literal becomes `"1.3"`; the test names and module docstrings that say `1.2` stay, as they name the version that brought `provider_limit`. Each test keeps what it checks.

## Acceptance criteria

1. `TreeId` (through a `TypeAdapter`) accepts `"a" * 40` and `"0" * 40` and refuses `"a" * 39`, `"a" * 41`, `"A" * 40` and `"g" * 40` (rows of one parametrized test).
2. `work_tree_id()` is the tree a commit records (rows of one parametrized test): on a clean checkout it equals `git rev-parse HEAD^{tree}`. After an edit of a tracked file, a new untracked file `notes/new.txt` and a deleted tracked file, it equals the `HEAD^{tree}` of the commit that `GitCli.commit` makes right after the call. With `.gitignore` holding `*.log`, a file `build.log` in the work tree gives the same id as without it. A tracked `kept.log`, committed before `.gitignore` holds `*.log`, counts: after an edit of it the id equals the `HEAD^{tree}` of the commit `GitCli.commit` makes right after the call. In a folder with `git init` and two files but no commit and no index, it equals the `HEAD^{tree}` of the first commit of those files.
3. `left_out` (rows of one parametrized test, on a work tree with `src/a.py`, `docs/guide.md`, `docs/sub/deep.md`, `docsx/a.md`, `docs/:x.md` and `docs/a*b.md`): `work_tree_id(["docs/*"])` equals `work_tree_id()` of the same checkout after `docs/` is removed from the work tree. An edit of `docs/sub/deep.md` leaves `work_tree_id(["docs/*"])` unchanged and changes `work_tree_id()`. An edit of `docsx/a.md` changes `work_tree_id(["docs/*"])`. `work_tree_id(["Docs/*"])` equals `work_tree_id()`. `work_tree_id(["*"])` equals `git hash-object -t tree /dev/null`, the empty tree.
 On a work tree whose root holds `a*b.md`, `aXb.md`, `:x.md` and `x.md`, `work_tree_id(["a[*]b.md", ":x.md"])` equals `work_tree_id()` after only `a*b.md` and `:x.md` are removed from the work tree (a pathspec would also remove `aXb.md` and `x.md`, and keep `:x.md`).
4. The call changes nothing (rows of one parametrized test): after a call on a checkout with staged, unstaged and untracked changes, `status()`, `resolve("HEAD")` and the bytes of `.git/index` are what they were before. On a `GitCli` of a folder that is not a repository, the call raises `GitError`. In both rows the temporary folder (`tempfile.tempdir` set to `tmp_path / "tmp"` with `monkeypatch`) is empty afterwards.
5. `Git.__abstractmethods__` and the public callables of `Git` are the twenty-three operations and `work_tree_id`, and `GitCli` has each (the two renamed tests of decision 15).
6. `not_read` loads (rows of one parametrized test): a definition whose `check` is `{time_limit: 10}` gives `not_read == []`; `{time_limit: 10, not_read: ["README.md", "docs/*"]}` gives `["README.md", "docs/*"]`, in that order, and the other commands keep `[]`.
7. The load rule (rows of one parametrized test, each a `check: {time_limit: 10, not_read: [<pattern>]}`): `docs/*`, `*.md`, `.github/*` and `factory/features/*` load. `/etc/*`, `~/notes/*`, `../docs/*`, `docs/../src/*`, `{work_item}`, `docs/{x` and `docs/x}` raise `PipelineDefinitionInvalid` whose fault is exactly `project command check: not_read <pattern> must be a path pattern inside the checkout`. With `check` and `lint` both holding `/a/*`, the fault is `project command check: not_read /a/* must be a path pattern inside the checkout; project command lint: not_read /a/* must be a path pattern inside the checkout`. `not_read: ["/b/*", "/a/*"]` gives the two faults in that order, joined by `; `. With `tool_paths: ["x"]` beside `not_read: ["/a/*"]`, the fault is `tool path x: must be <folder>/* or ~/<folder>/*; project command check: not_read /a/* must be a path pattern inside the checkout`. `not_read: "docs/*"`, `not_read: [1]`, `not_read: [""]` and `not_read: [" "]` raise `PipelineDefinitionInvalid` whose fault names `not_read`.
8. The committed `src/factory/contract/pipeline-definition.schema.json` holds `not_read` among the `properties` of `ProjectCommandDefinition` under `$defs`, not among its `required`, and its `x-records-contract` equals `RECORDS_CONTRACT`. F0021-S0006's comparison of the committed schemas with the generated ones passes.
9. `make check` stays green.
10. docs: `docs/project-guide/git-and-hosting.md`, *The git wrapper*: `work_tree_id(left_out)`, what counts in the tree, the temporary index and that nothing in the checkout changes; *Which feature uses which operation*: `work_tree_id`, F0023. `docs/project-guide/stages.md`, *The pipeline definition*, where the guide describes the pipeline definition's model: `ProjectCommandDefinition.not_read`, its default and its load rule with the fault. `docs/operator-guide.md`, *The pipeline definition*: the key `not_read` of a project command, its form (patterns as in `write_paths`, `*` crossing `/`), the refused forms with the fault, and that it does nothing yet. `docs/decisions.md`: none, the entry comes with S0002.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git init -q --initial-branch=main "$d/w"
mkdir -p "$d/w/src" "$d/w/docs"
printf 'a\n' > "$d/w/src/a.py"
printf 'guide\n' > "$d/w/docs/guide.md"
uv run -q python - "$d/w" <<'EOF'
import subprocess
import sys
from pathlib import Path
from factory.adapters.git_cli import GitCli

w = Path(sys.argv[1])
git = GitCli(w)
whole = git.work_tree_id()
code = git.work_tree_id(["docs/*"])
(w / "docs" / "guide.md").write_text("changed\n", encoding="utf-8")
print(git.work_tree_id() == whole, git.work_tree_id(["docs/*"]) == code)
(w / "src" / "a.py").write_text("b\n", encoding="utf-8")
print(git.work_tree_id(["docs/*"]) == code)
expected = git.work_tree_id()
git.commit("all")
tree = subprocess.run(["git", "-C", str(w), "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, check=True).stdout.strip()
print(expected == tree, git.status().changes == [])
EOF
```
Expect: three lines, `False True`, `False`, `True True`

```bash
uv run -q python - <<'EOF'
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid

text = 'contract: "1.0"\nproject_commands:\n  check: {time_limit: 10, not_read: [%s]}\nroles:\n  coder: {write_paths: ["src/*"]}\nstages:\n  doing: {role: coder, next: [done], checks: [check]}\n  done: {}\n'
reader = RuamelPipelineDefinitionReader()
print(reader.parse(text % '"README.md", "docs/*"').project_commands["check"].not_read)
try:
    reader.parse(text % '"../docs/*"')
except PipelineDefinitionInvalid as error:
    print(error.fault)
EOF
```
Expect: two lines, `['README.md', 'docs/*']` and `project command check: not_read ../docs/* must be a path pattern inside the checkout`

```bash
uv run -q python -c '
import json

with open("src/factory/contract/pipeline-definition.schema.json", encoding="utf-8") as file:
    schema = json.load(file)
command = schema["$defs"]["ProjectCommandDefinition"]
print("not_read" in command["properties"], "not_read" in command.get("required", []))
'
```
Expect: `True False`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures (`factory.domain.git.TreeId`, `Git.work_tree_id(left_out)`, `GitCli.work_tree_id`, `ProjectCommandDefinition.not_read`, the load rule with its exact fault text, the move of `is_inside_checkout`, the contract minor 1.2 to 1.3). Every comment-stated behaviour has a criterion: the tree contents (2), the literal-path removal (3), the unchanged index, status and HEAD (4), the temporary folder removed also on error (4), the no-commit case (2), the default `[]` (6).
   Criteria: each is testable by one parametrized test and the rows are concrete. Each rule has its failing side: `TreeId` refusals (1), the refused patterns `/`, `~`, `..`, `{`, `}` and the faults' order and joining (7), a non-list, non-string, empty or blank `not_read` (7), `GitError` on a non-repository (4), `Docs/*` case-sensitivity and `docsx` (3). The renamed and literal-pinned tests have the feature's decision 15 as the human's word.
   Smoke test: three runnable blocks. Each `Expect:` line is checkable: the printed booleans, the list and the exact fault text, `True False`.
   Architecture: matches CLAUDE.md. `TreeId` lives in domain; `Git` is the abstract class, `GitCli` its only implementation and the only git caller; DTOs are Pydantic; the layer direction holds (`write_paths` and `confinement` import from `pipeline_definition`).
   Scope: inside F0023's scope list (S0001 items) and not in its Out of scope; nothing uses `not_read` or `work_tree_id` yet, which is S0002's.
   Open: none. One note, not a question: criterion 8 pins the contract version only through `x-records-contract` equal to `RECORDS_CONTRACT`; the `"1.3"` literal itself is pinned by the changed existing tests.
4. factory: started tests as self.
5. tester: Wrote the tests for every criterion. `make lint` is green, and one `make test` run is red for the expected reasons: `TreeId` and `work_tree_id` don't exist yet, `not_read` is still an unknown key the strict model refuses, and the schema has no `not_read` yet.
   criterion 1: tests/domain/test_tree_id.py::test_a_tree_id_is_forty_lower_case_hex_characters
   criterion 2: tests/adapters/test_git_cli_work_tree.py::test_the_work_tree_id_is_the_tree_a_commit_records
   criterion 3: tests/adapters/test_git_cli_work_tree.py::test_the_left_out_paths_are_not_in_the_work_tree_id
   criterion 4: tests/adapters/test_git_cli_work_tree.py::test_the_work_tree_id_changes_nothing_and_leaves_no_temporary_file
   criterion 5: tests/application/test_git_interface.py::test_git_has_exactly_the_twenty_four_operations_and_git_cli_has_each, tests/application/test_interfaces.py::test_git_abstract_methods_are_exactly_its_twenty_four_operations
   criterion 6: tests/domain/test_pipeline_not_read.py::test_not_read_loads_in_order_and_defaults_to_nothing
   criterion 7: tests/domain/test_pipeline_not_read.py::test_a_not_read_pattern_outside_the_checkout_is_refused (the accepted patterns, the refused patterns, two commands, two patterns, after tool_paths), tests/domain/test_pipeline_not_read.py::test_a_not_read_that_is_not_a_list_of_patterns_is_refused (a plain string, `[1]`, `[""]`, `[" "]`)
   criterion 8: tests/entry/test_contract_not_read.py::test_the_committed_pipeline_schema_holds_an_optional_not_read, and the existing tests/entry/test_contract.py::test_the_committed_schemas_are_the_generated_ones (F0021-S0006's comparison)
   criteria 9 (`make check`) and 10 (docs): no test, these are the coder's and the documenter's.

   Files created: tests/domain/test_tree_id.py, tests/adapters/test_git_cli_work_tree.py, tests/domain/test_pipeline_not_read.py, tests/entry/test_contract_not_read.py.
   Earlier test files changed, as the feature's decision 15 allows and nothing else in them:
   - tests/application/test_git_interface.py: `"work_tree_id"` added to `OPERATIONS`, and the test renamed to `..._twenty_four_...`.
   - tests/application/test_interfaces.py: the git test renamed to `..._twenty_four_...`.
   - tests/domain/test_contract.py: the `"1.2"` literal on line 54 is now `"1.3"`.
   - tests/domain/test_contract_provider_limit.py: the two `"1.2"` literals are now `"1.3"`. The test name and the module docstring still say 1.2, as the story asks.
   No other test module pins the contract version as a literal.

   Could not import: `factory.domain.git.TreeId`, so tests/domain/test_tree_id.py stops at collection with an ImportError. The other new tests fail on missing behaviour: `GitCli.work_tree_id`, `ProjectCommandDefinition.not_read` with its load rule, and the regenerated schema at contract 1.3.

   Choices made inside the criteria:
   - In criterion 3, the files are committed before each row runs.
   - In criterion 4, the checkout has a staged new file, an unstaged edit of a tracked file and an untracked file.
   - For criterion 7's type rows, the test checks only that the fault names `not_read`, since the criterion says nothing more.

   Open: none.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/domain/test_tree_id.py - ImportError while importing test module ...
