# Design: the TypeScript/npm template

Status: design, 2026-10-19, for the human's review; not stories. Read offline against the same inputs as `java-gradle.md` (its header names them) and `C:/Dev/Projects/factory-timeline/docs/plan.md`. Versions marked *to be checked* could not be confirmed offline; the first story that pins one reads the current release. The generic stories G1 to G4 and the questions on the image and the work network are shared with the Java design and are only referred to here.

First use: the Factory Timeline (`pkrahmer/factory-timeline`), a static HTML page whose reading code is pure functions with unit tests; the human decided on 2026-10-19 that its real build waits for this template and is the factory's first project outside Python.

## 0. The shape in short

- The engine stays as it is: a thin `Makefile` over npm scripts and `npx` keeps `make check`/`lint`/`test` and the contract's lines; `MakeProjectCommands` (R11) suffices.
- TypeScript in strict mode on Node 24 LTS, ES modules; `tsc --noEmit` plus typed ESLint rules are the type check (`types`), Prettier and the untyped ESLint rules the `lint`; Vitest with V8 coverage and a JUnit reporter the `test`; dependency-cruiser the `layers`; semgrep the `sast`; detect-secrets the `secrets`; license-checker the `licenses`; jscpd and knip the `duplicates`; StrykerJS with its Vitest runner and incremental mode the `mutants`.
- Write paths: tester `tests/*`, coder `src/*` (plus a page file for the timeline); every config file at the root stays outside them. `node_modules/` is a tool path; the gate installs from `package-lock.json` with `npm ci --ignore-scripts`.
- The image: Node 24 from the official tarball replaces Debian's Node 18 in every target (Claude Code gains from it too), plus semgrep and detect-secrets as image tools; a target `typescript` adds nothing else.
- For a browser page (the timeline) the template adds an optional `build` target (`tsc` to `dist/`); whether the page keeps "no build step" is the human's question T1.

## 1. The project commands and their output contract

The contract is the Python template's (see `java-gradle.md`, section 1, "What the factory expects"): each target's last line `<target>: green (<seconds> s)`, `check: green`, a JUnit report, the duplicates and mutants lines, judged by exit status.

The mapping: one `Makefile` with the Python template's skeleton (`SHELL`, `.ONESHELL`, `$(start)`, `$(green)`), calling the tools through `npx --no-install` (never a download at run time) so the Makefile names every flag and the factory's records keep per-target times. npm scripts in `package.json` mirror the targets for a human at a terminal (`npm run check` calls `make check`), not the other way round: one place holds the recipes.

```make
NPX ?= npx --no-install
# node_modules from package-lock.json alone; no install scripts (a dependency's postinstall is code
# nobody reviewed). The stamp is npm's own hidden lockfile, newer than package-lock.json after `npm ci`.
node_modules/.package-lock.json: package-lock.json
	npm ci --ignore-scripts --no-audit --no-fund --prefer-offline --loglevel=error

check: lint types layers sast secrets licenses test
	echo "check: green"

lint: node_modules/.package-lock.json          # no type information: the tests stage runs it on red tests
	$(start)
	$(NPX) prettier --check --log-level warn .
	$(NPX) eslint --config eslint.config.js --max-warnings 0 --cache --cache-location .reports/eslintcache .
	$(green)

types: node_modules/.package-lock.json
	$(start)
	$(NPX) tsc --noEmit -p tsconfig.json
	$(NPX) eslint --config eslint.typed.config.js --max-warnings 0 src tests
	$(green)

layers: node_modules/.package-lock.json
	$(start)
	$(NPX) depcruise src --config .dependency-cruiser.cjs --output-type err
	$(green)

sast:
	$(start)
	SEMGREP_SEND_METRICS=off semgrep scan --config security/semgrep --metrics=off \
	  --disable-version-check --quiet --error src
	$(green)

secrets:   # the Python template's recipe; package-lock.json left out (its sha512 integrity values)
	...    # grep -vE '^(package-lock\.json|\.secrets\.baseline|.*\.costs\.jsonl)$$'
	$(green)

licenses: node_modules/.package-lock.json
	$(start)
	$(NPX) license-checker-rseidelsohn --production --excludePrivatePackages \
	  --onlyAllow "$(ALLOWED_LICENSES)" > /dev/null
	$(green)

test: node_modules/.package-lock.json   # every core (Vitest's threads), coverage thresholds from vitest.config.ts
	$(start)
	$(NPX) vitest run --coverage --passWithNoTests --reporter=dot --reporter=junit \
	  --outputFile.junit=.reports/junit.xml
	$(green)

duplicates: node_modules/.package-lock.json   # never fails for its findings
	$(NPX) jscpd src --silent --reporters json --output .reports/jscpd > /dev/null || true
	$(NPX) knip --reporter json > .reports/dead-code.json || true
	similar=$$(node -e '...count of duplicates in .reports/jscpd/jscpd-report.json...')
	dead=$$(node -e '...count of issues in .reports/dead-code.json...')
	echo "duplicates: $$similar similar code, $$dead dead code, in .reports/"
```

Notes:

- **Typed lint belongs to `types`, not `lint`.** typescript-eslint's `strictTypeChecked` rules (`no-unsafe-*`, `no-floating-promises`) read types; on a tester's red tests whose imports do not resolve, every use of the missing module is `any` and `lint` would go red for the wrong reason. So `eslint.config.js` holds the syntax-only rules, `eslint.typed.config.js` extends it with the typed ones, run in `types`, as Error Prone sits in `types` for Java and mypy is left out of the tests stage for Python.
- **Red tests are import errors, as in Python.** Vitest transforms TypeScript without type checking (esbuild), so a test file whose module does not exist fails alone with "Failed to resolve import", the others run: the tester's entry stays "the modules the test runner could not import".
- **No tests is green**: `--passWithNoTests` is the equivalent of pytest's exit 5; once a test exists Vitest fails a run that finds none only if the filter is wrong, which the Makefile never sets.
- **Coverage**: `coverage.thresholds` `{lines: 90, branches: 90, functions: 90, statements: 90}` and `include: ["src/**"]` in `vitest.config.ts`, provider `v8`, report to `.reports/coverage/`; below the threshold `vitest run` exits 1.
- **`npm ci` as the first step, by make's own rule.** The stamp keeps it to one install per lockfile change; a `check` on a fresh checkout installs first. Should the gate distrust an agent-written `node_modules` (section 3) it can delete the stamp first; recommended not, consistently with F0023's decision 3 for `.venv`.
- **`npm audit` is not in `check`**: its result depends on the day's advisories and the network (offline rule, F0023 reuse); a weekly job of the human's.
- **The JUnit report is one file** (`.reports/junit.xml`), exactly as the Python template's.
- **`build`, optional** (for a page): `$(NPX) tsc -p tsconfig.build.json` emits ES modules to `dist/` (git-ignored); not part of `check` unless the page is. For the timeline: question T1.

The pipeline definition:

```yaml
project_commands:
  check: {time_limit: 10}
  lint: {time_limit: 5}
  test: {time_limit: 10}
  duplicates: {time_limit: 5}
tool_paths: ["node_modules/*", ".reports/*", ".stryker-tmp/*", "dist/*", "~/.npm/*", "~/.cache/*"]
roles:
  tester: {write_paths: ["tests/*"]}
  coder: {write_paths: ["src/*"]}          # the timeline adds its page: ["src/*", "index.html"]
  # intake, reviewer, documenter, smoke-tester, acceptance-reviewer as in the Python template
stages:  # as the Python template's, `duplicates` as a report of `doing`
```

## 2. The checks

| Check | Python template | TypeScript/npm | Pin (*to be checked* unless stated) |
|---|---|---|---|
| Runtime | Python 3.12, uv | Node 24 LTS, npm 11 (bundled), `"type": "module"`, `"engines": {"node": "24.x"}` | Node 24.x latest patch; npm as bundled |
| Language | — | TypeScript, `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`, `erasableSyntaxOnly` (so Node's type stripping could run the sources too), `module`/`moduleResolution` `nodenext` | typescript 5.9.x (6.0 if released and typescript-eslint supports it) |
| Format | ruff format | Prettier | prettier 3.6.x |
| Lint | ruff check | ESLint flat config, `@eslint/js` recommended + typescript-eslint `strict` (no type info) | eslint 9.x; typescript-eslint 8.x |
| Types | mypy --strict | `tsc --noEmit` + typescript-eslint `strictTypeChecked` | as above |
| Layers (R8) | import-linter in `pyproject.toml` | dependency-cruiser, the project's layers as `forbidden` rules in `.dependency-cruiser.cjs` at the root (the human's file: outside every write path) | dependency-cruiser 17.x |
| SAST | semgrep + bandit | semgrep with vendored TypeScript/JavaScript rules under `security/semgrep/`; no second tool (eslint-plugin-security mostly duplicates semgrep's rules and is noisy) | semgrep as the Python projects pin it (1.180.0 in the todo demo), from the image |
| Secrets | detect-secrets | detect-secrets from the image, same recipe and baseline | 1.5.0 |
| Licences | pip-licenses | license-checker-rseidelsohn `--production --onlyAllow` | 4.4.x |
| Tests | pytest + xdist + coverage | Vitest, `node` environment, V8 coverage, JUnit reporter | vitest 3.2.x or 4.x; @vitest/coverage-v8 the same version |
| Duplicates | pylint duplicate-code | jscpd | jscpd 4.0.x |
| Dead code | vulture | knip (unused files, exports, dependencies) | knip 5.x |
| Mutation | mutmut | StrykerJS with `@stryker-mutator/vitest-runner`, `coverageAnalysis: "perTest"`, `incremental: true` | @stryker-mutator/core 9.x and vitest-runner the same |

Notes:

- **Why Vitest and not Node's built-in runner** (the timeline plan named `node --test` when it was plain JavaScript with no build step): Vitest runs TypeScript as it is, has coverage thresholds, a JUnit reporter and parallel workers built in, and above all has a Stryker runner with per-test coverage analysis. Stryker has no `node:test` runner; its `command` runner re-runs the whole suite for every mutant, hundreds of times slower on a real suite. Question T2.
- **Mutation testing per story (F0024's form).** The recipe computes the changed `src/**/*.ts` files exactly as F0024's Makefile computes modules (`git diff --name-only <merge base>` plus untracked on `work-item/<story id>`, the feature's story commits with `FEATURE`) and passes them as `--mutate <file>,<file>`; it stops Stryker with `timeout $(MUTANTS_SECONDS)` (540).
  Stryker's **incremental mode** (`incrementalFile: .reports/stryker-incremental.json`) reuses the result of every mutant whose code and covering tests did not change, which mutmut 3.8 does not; so a story's second run, and an acceptance's re-run, check only what changed. **Risk:** Stryker writes the incremental file when the run ends; a run that `timeout` kills leaves none (*to be checked*). So, as for PIT, a per-story run must fit 540 s by size until a probe shows otherwise, and `concurrency` is left at Stryker's default (cores − 1).
  The last line: a small project script `scripts/mutants-line.mjs` (the template's, ~30 lines, no dependency) reads `.reports/mutation/mutation.json` (the mutation-testing-report schema) and prints `mutants: <k> killed, <s> survived, <t> timed out, <n> no coverage of <total> mutant(s) in <f> file(s)`, or `mutants: partial, ...` with exit 1 when `timeout` returned 124 (no report then, so "partial" with the counts unknown). The reviewer lists survivors from the same JSON (`status: "Survived"`), with a `jq`-free `node -e` one-liner the CLAUDE.md gives.
- **Structural tests under mutation.** Stryker mutates a copy of the project in `.stryker-tmp/` and instruments the source; a test that reads a source file by path reads the instrumented copy and fails or kills nothing, as with mutmut. dependency-cruiser is not a test, so the template has no structural test; a project that adds one puts it under `tests/structure/`, and `vitest.stryker.config.ts` (used by Stryker's runner, `vitest.configFile`) excludes that folder. The CLAUDE.md says so, in the place of `[tool.mutmut]`'s deselect list.
- **No build step for the tests.** Vitest reads `.ts`; `tsc` only checks. The sources carry erasable syntax only (no `enum`, no `namespace`, no parameter properties), so the same files could run under Node 24's type stripping without any tool, which keeps the door open for a no-build page (T1).

## 3. The factory's interfaces it touches

- **Project commands (R11)**: the make-based class suffices; an `NpmProjectCommands` would learn script names and the green-line format, which R6 and R8 keep out of the engine.
- **Write paths**: tester `tests/*`, coder `src/*`; documenter `README.md` and `docs/*`. At the root and outside every write path: `package.json`, `package-lock.json`, `tsconfig*.json`, `eslint*.config.js`, `.prettierrc.json`, `.prettierignore`, `vitest*.config.ts`, `stryker.config.mjs`, `.dependency-cruiser.cjs`, `knip.json`, `.npmrc`, `scripts/*`, `security/*`. A new dependency stays a question to the human (`package.json` is refused by the kernel as `pyproject.toml` is protected). The engine's `PROTECTED_PATHS` need nothing added (Java design, question J6).
  For the timeline the coder also writes the page (`index.html`, and its stylesheet if split); `tools/snapshot.py` stays the human's.
- **Tool paths**: `node_modules/*` (installed packages; Vitest's and Prettier's caches in `node_modules/.vite` and `node_modules/.cache`), `.reports/*` (JUnit, coverage, ESLint's cache, jscpd, knip, Stryker's report and incremental file), `.stryker-tmp/*` (Stryker's sandbox; its `tempDirName` default), `dist/*` (the optional build), `~/.npm/*` (npm's cache; `_cacache` and `_logs`), `~/.cache/*` (semgrep's and others'). Node honours `TMPDIR` (`os.tmpdir()`), so the run's `$TMPDIR` works without the Java trap; the template's CLAUDE.md still says "temporary files under `os.tmpdir()`, never `/tmp` by name".
- **Two users**: `node_modules/` is written by `factory` (the gate's `npm ci`) and by `agent` (an agent's `make test`); with `umask 002` both can replace the other's files, and `npm ci` removes the whole folder first, which needs write on the folders only. Risk: a file that a package's tarball carries without group write (`0644`) cannot be rewritten in place by the other user. It can still be removed, because removal needs only the folder's write bit, which `umask 002` gives, and removing and remaking is what `npm ci` does. *To be checked* in the probe T0: an agent's `npm ci` after the factory's, and the reverse.
- **F0023's `not_read` and known results**: the tree holds `package.json` and `package-lock.json` (exact versions with `integrity` sha512), so the dependencies are pinned by the tree; `node_modules/` is ignored and not in the key, the same accepted caveat as `.venv` (F0023 decision 3). `npm ci` installs exactly the lockfile, so a reuse is safe as long as `.npmrc` sets `save-exact=true` and nobody commits a lockfile with `resolved` URLs of another registry (a mirror's URLs in the lockfile tie it to the network it was made on; npm 9+ replaces the default registry host with the configured one, *to be checked* for npm 11, so lockfiles keep `registry.npmjs.org`). `not_read` for `check` as factory-rf's: `README.md`, `docs/*.md`, `factory/features/*.md`, `factory/features/*.jsonl`, `factory/stops.jsonl`, `planning/*`, and with it `secrets` as its own docs-stage check (F0023 decision 12). Prettier formats Markdown, so a project whose `lint` runs `prettier --check .` reads `docs/*.md`: either `.prettierignore` leaves out `docs/` and `README.md` (recommended: the documenter's prose is not Prettier's), or they may not be in `not_read`.
- **The records contract**: unchanged; the timeline itself reads it (the plan: "a release of the map names the contract versions it reads").

## 4. The image

- **Node 24 LTS for every target** (the generic story G2): the official `node-v24.<x>.<y>-linux-x64.tar.xz` from nodejs.org, its SHA-256 from that release's `SHASUMS256.txt` pinned in the Dockerfile (R29), unpacked into `/usr/local` (so `node`, `npm` and `npx` are on the agent run's fixed `PATH`, `/usr/local/bin` first). Debian's `nodejs` 18.20.4 and `npm` 9.2.0 leave the apt line: Node 18 is past its end of life (April 2025), and Claude Code is installed with the new npm. About 30 MB compressed, 190 MB unpacked, against about 70 MB for Debian's two packages (*to be checked*). For arm64 hosts (a Mac at work) the tarball's architecture is a build argument with its own pinned checksum.
- **semgrep and detect-secrets as image tools** for the non-Python stacks, as in the Java design (`uv tool install` with pinned versions, about 150 MB).
- **The `typescript` target** is then the `python` target plus those tools: no further layer. One Dockerfile with targets (Java design, question J1).
- **Offline and corporate network** (work uses rootless Podman, Windows and Mac):
  - The npm mirror is named in the users' `~/.npmrc` (`registry=https://<mirror>/api/npm/npm/`), a file the operator mounts read-only into `/home/agent/.npmrc` and `/home/factory/.npmrc`, never in the project's `.npmrc`. The agent's environment is scrubbed, so `NPM_CONFIG_REGISTRY` would not reach it; a file in the home does.
  - A proxy: npm reads `https-proxy` from `~/.npmrc` and Node's `fetch` does not read `HTTPS_PROXY` at all (Node 24 has `NODE_USE_ENV_PROXY`, *to be checked*), so the project's own code never goes out in tests (no network rule) and npm gets its proxy from the file. Claude Code needs `HTTPS_PROXY` in the agent's environment: the generic story G1.
  - A corporate CA: the image's optional `image/ca-certificates/` folder (Java design), and `NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt` set in the image and passed to agent runs (G1); npm reads `cafile` from `~/.npmrc` too.
  - The first `npm ci` of each user fills `~/.npm`; two named volumes (`npm-agent`, `npm-factory`) keep the caches across rebuilds, so `--prefer-offline` rarely reaches the mirror.

## 5. The agents

The shipped texts' Python assumptions and their stack-neutral wording are listed once, in `java-gradle.md`, section 5 (generic story G3). For TypeScript they read: the temporary folder is `os.tmpdir()` under `$TMPDIR`; red tests are "Failed to resolve import" lines, as in Python; the JUnit report is one file; the survivors come from Stryker's JSON report.

What the template's `CLAUDE.md` says for this stack (its chapters as the Python template's):

- *Architecture*: modules as layers, declared in `.dependency-cruiser.cjs`; the pure core imports no I/O module (`node:fs`, `fetch`, the DOM) and nothing from the outer layers; `readonly` types and `Readonly<>` for values; `unknown`, never `any`, at a boundary, narrowed by a validator (zod 4.x if the project takes a dependency, a hand-written guard otherwise); no `enum` (erasable syntax only); wiring in one module.
- *Tests*: Vitest, `describe`/`it` named after the behaviour; `it.each` tables for both sides of a limit; one test file per module under `tests/` mirroring `src/`; fakes through the interface, `vi.mock` never on the code under test; no network (`fetch` faked at the boundary), no timers but `vi.useFakeTimers`, files only under a `mkdtemp(join(tmpdir(), ...))` folder removed in `afterEach`.
- *Checks*: the targets above with their lines; typed lint in `types`; Stryker's form and how to read a survivor.
- *Not without asking*: a new dependency (a change to `package.json` or `package-lock.json`), an `eslint-disable`, a `@ts-expect-error` or `@ts-ignore`, a `nosemgrep`, a `.secrets.baseline` entry, a licence outside the allow list, a change to a config file at the root.

Skills (F0022) are optional: "reading a Vitest failure and its coverage table", "reading Stryker's report". No project agent is needed.

## 6. A demo, and the first use

- **The first real project is the Factory Timeline** (the human's decision of 2026-10-19). Its features, from its plan: (1) the reading module, pure functions from raw file texts to records (front matter via js-yaml 4.1.x, MIT; the sidecars line by line), validated against the records contract's JSON Schemas copied from factory-rf as test fixtures; (2) the derived values (visits, waits, the approval wait, send-backs, the factory's own wait); (3) the loader with its two sources (the GitHub API with `If-None-Match`, at most 8 requests at a time, IndexedDB by blob sha; the embedded snapshot); (4) the page. Features 1 and 2 are pure and fit the template exactly; 3 is tested against a fake `fetch`; 4 is the coder's `index.html` plus `src/page/*`, checked by the smoke tester in a browser only if the factory gets one (today it has none: the page's own behaviour is the human's check at the approval).
  How its stories read: the Interface in TypeScript signatures, for example

  ```ts
  // src/records/journal.ts
  export type JournalRecord = Readonly<{
    number: number; speaker: string; kind: RecordKind; at: Date; stage: string; run?: string;
  }>;
  export function parseFrontMatter(text: string): Result<WorkItemFront, ReadFault>;
  export function stageVisits(records: readonly JournalRecord[], costs: readonly CostLine[]): readonly StageVisit[];
  ```

  with criteria such as "a `started` record followed by a `result` of the same stage is one visit from the first `at` to the second", each a Vitest case, and decisions like the plan's ("no state, time, cost or outcome is ever taken from prose").
- **A demo of the template** before that: recommendation, the todo service's first feature only (S0001 to S0004: domain, service, HTTP, SQLite) as `demo/todo-service-ts/`, so that one feature is comparable with the Python baseline run; Fastify 5.x (`app.inject()` as the test client, the Python "no server process" rule) and `node:sqlite` (`DatabaseSync`, built into Node 24, no native build behind a proxy; still flagged experimental, *to be checked*) or better-sqlite3 12.x if `node:sqlite` warns on every run. What changes in the stories: a todo's id is a `string` (a UUID from `crypto.randomUUID()`), its time a `Date` normalised with `toISOString()`; decision 15 (no repository inherits the protocol) holds as it is, TypeScript being structural; decision 6's error shape is Fastify's `setErrorHandler`. Alternatively go straight to the timeline and skip the demo (question T3).

## 7. The order of the stories, and the open questions

**T0, a probe before any story** (no story): in a throwaway container of the current image with Node 24 unpacked, run a minimal project from the template's files (`npm ci`, `make check`, one Stryker run on two files) under `factory-confine` as the agent user, with the tool paths of section 3; written up as `planning/overnight/probe-typescript-<date>.md`. It answers: every write inside a tool path or `$TMPDIR` (npm's `~/.npm/_logs`, Vitest's and Stryker's temporary folders, esbuild's binary in `node_modules/@esbuild/`); `npm ci` by one user after the other; the incremental file of a Stryker run that `timeout` stops; `check`'s time on the empty project.

The generic stories G1 (proxy and CA names reach agent runs), G2 (Node 24 in the image), G3 (stack-neutral agent texts) and G4 (`templates/`) are described in `java-gradle.md`, section 7; G2 is this stack's own prerequisite.

Then, each small and inside factory-rf's write paths:

1. **T1. The image's tools and target**: semgrep and detect-secrets as image tools (shared with J1, whichever comes first builds it), the `typescript` target, the npm volumes in the compose file.
2. **T2. The template's three contract targets**: `package.json` (dev dependencies exact), `package-lock.json`, `tsconfig.json`, the two ESLint configs, Prettier's, `vitest.config.ts`, `.npmrc`, the `Makefile`'s `check`, `lint`, `types`, `test` and the install stamp, `factory/pipeline.yml` with `tool_paths`, `CLAUDE.md`. Tested as `tests/test_template_makefile.py` tests the Python one, with a stand-in `npx` and `npm` (`NPX=<stand-in>`).
3. **T3. The other gate targets**: `layers` (dependency-cruiser with a placeholder layer rule), `sast` (vendored semgrep rules for TypeScript), `secrets` (with `package-lock.json` left out), `licenses`.
4. **T4. The reports**: `duplicates` (jscpd, knip, the counting line) and `mutants` with `scripts/mutants-line.mjs` (the feature form; the per-story form after F0024's real check and T0).
5. **T5. The demo** (if T3 is answered "demo first"): `demo/todo-service-ts/` with the first feature's four stories.
6. Then the timeline: a repository seeded from the template (its `index.html` and `tools/snapshot.py` kept), its plan turned into features by the human with the drafter, built on an instance of the `typescript` target.

**Open questions for the human** (independent ones first, each with a recommendation):

- **T1. The page and the build step.** (a) TypeScript sources; `make build` (`tsc` to `dist/`, git-ignored) before opening the page; (b) the same but `dist/` committed so the page opens from a clone without Node; (c) JavaScript sources with JSDoc types checked by `tsc --checkJs` (no build step at all, as the plan first said; "TypeScript" then means the checker, not the syntax); (d) TypeScript sources loaded by the browser through an import map and a runtime transpiler (no). **Recommendation: (a)**: one tool chain, no generated files in the diff the reviewer reads, and the human's "opened from disk" holds after one `make build`. (c) is the fallback if a build step proves a burden.
- **T2. Vitest or Node's test runner?** **Recommendation: Vitest**, for Stryker's per-test runner, TypeScript without a build, coverage thresholds and a JUnit reporter in one tool; `node --test` would need the command runner (every mutant runs the whole suite) and a separate coverage gate.
- **T3. A todo demo first, or the timeline straight away?** **Recommendation: the todo service's first feature** (four stories) as the template's proof against the Python baseline, then the timeline; the timeline alone would mix the template's faults with a new product's.
- **T4. ESLint + Prettier, or Biome?** Biome 2.x is one fast tool for format and lint with some type-aware rules, but fewer typed rules than typescript-eslint and no dependency-cruiser equivalent. **Recommendation: ESLint + Prettier**, the more common pair and the stricter type-aware lint.
- **T5. `node:sqlite` or better-sqlite3 for the demo?** **Recommendation: `node:sqlite`** if Node 24's warning can be silenced per call site; a native module behind a corporate proxy means a prebuilt binary download from GitHub that the mirror may not serve.
- The shared ones from `java-gradle.md`: J1 (one image with targets), J3 (the work network), J6 (no project-declared protected paths now), J7 (`templates/`), J8 (per-story mutants after F0024's check).

**The biggest risk**: the mutation report. StrykerJS is the one tool here whose time grows with the code, and like mutmut it loses a run stopped at 540 s if its incremental file is written only at the end; the per-story form then repeats F0024's fault (the same mutants reached every time) in a new tool. T0 measures it before T4 is drafted; the fallback is the feature-level form with a smaller `mutate` set per acceptance run.
