# Design: the Java/Gradle template

Status: design, 2026-10-19, for the human's review. These are not stories. They say enough that the stories of section 7 can be drafted without new research. Read offline against v1.1 at the state of 2026-10-19: `template/`, `demo/todo-service/`, `factory/pipeline.yml`, `Makefile`, `pyproject.toml`, `CLAUDE.md`, `docs/project-guide/`, `docs/operator-guide.md`, `image/Dockerfile`, the drafts of F0022, F0023 and F0024, and the Podman note. Every version below is the one I would pin. Where it says *to be checked*, I could not confirm the version offline, and the first story that pins it reads the current release.

The use: the human's work projects. They are Java built with Gradle, run under rootless Podman on Windows and Mac at work, on a corporate network (a Maven mirror, maybe a proxy, maybe TLS interception).

## 0. The shape in short

- The factory's engine stays as it is. It still calls `make check`, `make lint` and `make test`, and the Python template's `MakeProjectCommands` (R11) is enough. A thin `Makefile` wraps the Gradle wrapper (`./gradlew`), times each target and prints the contract's lines.
- Gradle does the work: Spotless and Checkstyle (`lint`), javac with `-Werror`, Error Prone and NullAway (`types`), ArchUnit in a source set the agents cannot write (`layers`), SpotBugs with FindSecBugs plus semgrep (`sast`), detect-secrets (`secrets`), a licence report (`licenses`), JUnit with JaCoCo (`test`), CPD (`duplicates`) and PIT (`mutants`).
- Write paths follow Maven's layout: the tester writes `src/test/*`, the coder `src/main/*`. Build files at the root stay outside every write path.
- The image gets a Dockerfile target `java`: the factory's image plus a pinned Temurin JDK and the shared tools (semgrep, detect-secrets). Gradle itself comes from each project's wrapper, cached per user on a volume.
- At work, three things are not part of the template but must be settled first. Proxy variables and a corporate CA must reach the agent runs. Today `ALLOWED_ENVIRONMENT_NAMES` passes only `PATH`, `HOME`, `LANG`, `LC_ALL`, `TERM` and `TZ`, so even Claude Code cannot pass through a proxy. And the Maven mirror is named in a Gradle init script in each user's home, never in the project.

## 1. The project commands and their output contract

### What the factory expects (unchanged)

Read from `template/Makefile`, `template/factory/pipeline.yml`, `src/factory/adapters/make_commands.py` and `src/factory/domain/checks.py`:

- `make <command>` runs in the checkout's root. It is judged by its exit status alone. The factory keeps the last line that is not a `make:` message, the last 30 lines, and every line `<target>: green (<seconds> s)` (`target_times`, for the records).
- `check` runs `lint types layers sast secrets licenses test` and ends with `check: green`. The tests stage runs `lint` as a check and `test` as a report. `doing` and `docs` run `check`. `duplicates` and `mutants` are reports.
- `make test` writes a JUnit report. The acceptance reviewer reads it for the slowest tests ("the `--junit-xml` file its `Makefile` names").
- `make duplicates` ends with one counting line, `duplicates: <n> similar code, <k> dead code, in .reports/`. factory-rf's own form, which compares against a baseline, is its own.
- `make mutants FEATURE=<id>` ends with a summary line. F0024 makes it a per-story report in factory-rf only (its decision 12); the template keeps the feature-level form until that real check has passed.

### The mapping onto Gradle

One `Makefile` over the wrapper. It keeps the Python template's skeleton: `SHELL := /bin/bash`, `.SHELLFLAGS := -eu -o pipefail -c`, `.ONESHELL:`, `.SILENT:`, and `$(start)` / `$(green)` as they are. `GRADLE ?= ./gradlew` stays a variable so that the template's tests can put a stand-in in its place, as `tests/test_template_makefile.py` does for `uv`.

```make
GRADLE ?= ./gradlew
# No daemon: a daemon an agent run starts would outlive the run and keep its Landlock rules (section 3).
# Plain console, only warnings and errors, no welcome text.
G = $(GRADLE) --no-daemon --console=plain --quiet --warning-mode=summary

check: lint types layers sast secrets licenses test
	echo "check: green"

lint:          # needs no compilation: the tests stage runs it while the classes under test do not exist
	$(start)
	$(G) spotlessCheck checkstyleMain checkstyleTest
	$(green)

types:         # the compiler is the type check: -Xlint:all -Werror, Error Prone, NullAway
	$(start)
	$(G) compileJava compileTestJava
	$(green)

layers:
	$(start)
	$(G) archTest
	$(green)

sast:
	$(start)
	$(G) spotbugsMain
	SEMGREP_SEND_METRICS=off semgrep scan --config security/semgrep --metrics=off \
	  --disable-version-check --quiet --error src/main/java
	$(green)

secrets:       # as the Python template's, with the Gradle lock and verification files left out
	...        # grep -vE '^(gradle\.lockfile|.*/gradle\.lockfile|gradle/verification-metadata\.xml|\.secrets\.baseline|.*\.costs\.jsonl)$$'
	$(green)

licenses:
	$(start)
	$(G) checkLicense
	$(green)

test:          # every core; the JUnit reports in .reports/junit/; coverage verified at the threshold
	$(start)
	$(G) test jacocoTestCoverageVerification
	$(green)

duplicates:    # never fails for its findings
	$(G) cpdCheck --continue || true
	similar=$$(grep -c '<duplication ' .reports/cpd/cpd.xml || true)
	dead=$$(grep -c '<violation ' .reports/pmd/dead-code.xml || true)
	echo "duplicates: $$similar similar code, $$dead dead code, in .reports/"

mutants:       # feature-level, as the Python template's; section 2 has the per-story form
	...
```

Notes on the mapping:

- **One Gradle call per make target.** This keeps the per-target lines that the records read. The cost is one JVM start and one configuration per target, seven per `check`. With the configuration cache (`org.gradle.configuration-cache=true` in the project's `gradle.properties`) I expect 3 to 6 s per call (*to be checked* in the first story). That is 20 to 40 s of overhead on `check`. The alternative is a single `$(G) check` with a single green line: faster, but `project-commands.jsonl` then loses the target times that F0012's telemetry reads. Recommendation: separate calls, and measure in the template story. Open question J4.
- **`lint` must not compile.** The tests stage runs `lint` while the tester's tests name classes that do not exist yet. Spotless (google-java-format) and Checkstyle work on the source text. Error Prone runs inside javac, so it belongs to `types`, not to `lint`, just as the Python template leaves `mypy` out of the tests stage.
- **Red tests in Java are compile errors.** In Python a missing module fails one test module. In Java a missing class fails `compileTestJava`, so every test of the source set is red, the earlier stories' tests included. That is still "red for the right reason". The tester's entry names the missing symbols instead of "the modules the test runner could not import" (section 5).
- **The JUnit report is a folder.** Gradle writes one `TEST-<class>.xml` per test class. `reports.junitXml.outputLocation` points it at `.reports/junit/`. Merging the files would need a tool the project does not otherwise have. Instead the acceptance reviewer's text is generalized: "the JUnit report its `Makefile` names, a file or a folder" (section 5).
- **No tests is green.** For an empty project, Gradle's `test` is `NO-SOURCE`, which is green. Gradle 9 fails a test task that has sources but finds no test (`failOnNoDiscoveredTests`, *to be checked* that it is on by default in 9.x). That is the equivalent of pytest's exit status 5 after the first test exists, so the Makefile needs no `|| [ $? -eq 5 ]`.
- **Tests always run in `check`.** `tasks.test { outputs.upToDateWhen { false } }` in the build script. Gradle would otherwise mark `test` up to date from state in `build/` and `.gradle/`, which are tool paths an agent writes (section 3). Compilation stays incremental. The local build cache is off (`org.gradle.caching=false`), so no output comes from a cache that an agent run could have filled.
- **The lines Gradle prints.** `--quiet` leaves errors and warnings only, so the recipe's own `<target>: green (...)` stays the last line on success, and a failure's tail is Gradle's `* What went wrong:` block, which an agent can read. `--warning-mode=summary` keeps deprecation lists short.

### The pipeline definition (`factory/pipeline.yml`)

```yaml
contract: "1.0"
attempts_cap: 2
crash_cap: 2
acceptance_stage: acceptance
project_commands:
  check: {time_limit: 15}      # a cold first run resolves every dependency through the mirror
  lint: {time_limit: 5}
  test: {time_limit: 10}
  duplicates: {time_limit: 5}
tool_paths: ["build/*", ".gradle/*", ".reports/*", "~/.gradle/*", "~/.java/*"]
roles:
  intake: {write_paths: ["{work_item}"]}
  tester: {write_paths: ["src/test/*"]}
  coder: {write_paths: ["src/main/*"]}
  reviewer: {write_paths: ["{work_item}"]}
  documenter: {write_paths: ["README.md", "docs/*"]}
  smoke-tester: {write_paths: ["{work_item}"]}
  acceptance-reviewer: {write_paths: ["{work_item}", "{feature}/backlog/*"]}
stages: # as the Python template's, `duplicates` as a report of `doing`
```

The leases with the defaults: doing is 40 + 15 + 5 = 60, inside 60. Docs is 40 + 15 = 55. A project that adds `mutants` as a report (section 2) lowers `check` to 8, as F0024 does, or raises the lease.

## 2. The checks

| Check | Python template | Java/Gradle | Pin (to be checked unless stated) |
|---|---|---|---|
| Build | uv | Gradle wrapper, Kotlin DSL (`build.gradle.kts`, `settings.gradle.kts`), version catalog `gradle/libs.versions.toml` | Gradle 9.x, the latest 9 minor at the story (9.1.0 was current in Sept 2025) |
| JDK | Python 3.12 | Eclipse Temurin 21 LTS through a Gradle toolchain (`languageVersion = 21`); toolchain auto-download off | 21.0.x, latest patch (open question J2: 21 or 25) |
| Format | ruff format | Spotless with google-java-format | Spotless plugin `com.diffplug.spotless` 7.x/8.x; google-java-format 1.2x |
| Lint | ruff check | Checkstyle (Gradle's `checkstyle` plugin) with a vendored config under `config/checkstyle/` | Checkstyle 11.x (10.x if 11 needs a newer JDK than the project's) |
| Types | mypy --strict | javac `-Xlint:all -Werror`, Error Prone, NullAway (`@NullMarked` packages, JSpecify annotations) | plugin `net.ltgt.errorprone` 4.x; Error Prone 2.4x; NullAway 0.12.x; JSpecify 1.0.0 (confirmed: 1.0.0 is final) |
| Layers (R8) | import-linter, contracts in `pyproject.toml` | ArchUnit tests in their own source set `src/archTest/java`, a task `archTest`; the project declares its layers there with `layeredArchitecture()` | ArchUnit 1.4.x |
| SAST | semgrep + bandit | SpotBugs with the FindSecBugs plugin, plus semgrep's vendored Java rules under `security/semgrep/` | plugin `com.github.spotbugs` 6.x; SpotBugs 4.9.x; FindSecBugs 1.14.0; semgrep at the version the Python projects pin (1.180.0 in the todo demo) |
| Secrets | detect-secrets | detect-secrets, the same recipe and baseline format, from the image (section 4) | 1.5.0 (as pinned today) |
| Licences | pip-licenses against an allow list | `com.github.jk1.dependency-license-report` with `allowed-licenses.json` and its `checkLicense` task, runtime classpath only | 2.9 or later 2.x |
| Tests | pytest, xdist, branch coverage ≥ 90 % | JUnit Jupiter with AssertJ; `maxParallelForks` = cores / 2 and JUnit's own parallel mode off (simpler failures); JaCoCo `jacocoTestCoverageVerification` with LINE and BRANCH ≥ 0.90 | JUnit 6.0.x (5.13.x if the PIT plugin below does not support 6); AssertJ 3.27.x; JaCoCo 0.8.13 (0.8.14 for Java 25) |
| Duplicates | pylint duplicate-code | PMD's CPD through `de.aaschmid.cpd`, XML to `.reports/cpd/` | plugin 3.x; PMD 7.x |
| Dead code | vulture | PMD's unused rules only (`UnusedPrivateMethod`, `UnusedPrivateField`, `UnusedLocalVariable`, `UnusedFormalParameter`), XML to `.reports/pmd/dead-code.xml`. No Java tool finds dead public code reliably. That gap is accepted and named in the CLAUDE.md. | PMD 7.x |
| Mutation | mutmut | PIT with the JUnit 5 plugin, through `info.solidsoft.pitest` | PIT 1.2x; plugin 1.15.x/1.19.x; pitest-junit5-plugin 1.2.x |

Notes:

- **Layers belong to the project (R8), and the agents must not move them.** In Python the contracts live in `pyproject.toml`, an engine-protected file. An ArchUnit test under `src/test/` would sit in the tester's write path, so a tester could weaken the rule its own story breaks. So the layer tests get a source set of their own, `src/archTest/java`, outside both write paths. The kernel refuses writes there, and the hook and the undo judge the write paths. They are the human's, like the build files. `check`'s `layers` target runs them. A new layer is a change the human makes, as with import-linter. The engine's `PROTECTED_PATHS` (ten fixed patterns) need not change for this: they matter only where a write path would reach a file, and no Java write path reaches the root or `src/archTest/` (open question J6).
- **Strict types.** `options.compilerArgs.addAll(listOf("-Xlint:all", "-Werror"))`, Error Prone with `NullAway:AnnotatedPackages=<the project's root package>` at ERROR. JSpecify's `@NullMarked` goes in each `package-info.java`. This is the closest thing to `mypy --strict`: a nullable value that is not checked fails the build.
- **Coverage.** `jacocoTestReport` runs after `test`, and the verification fails `make test` below 0.90 line or branch coverage, as `fail_under` does in Python. The threshold is a project value in `build.gradle.kts`, the human's file.
- **Mutation testing and the structural tests.** PIT mutates bytecode in memory, not the source on disk. So the Python rule "mutmut rewrites the source, so the structural tests that read it are deselected" mostly disappears. ArchUnit tests that read class files would still pass, but they kill no mutant and cost time. They are in their own source set, which `pitest` does not run (`testSourceSets` = `test` only). A test under `src/test/` that reads a source file by path still reads the unmutated file, which is harmless. The rule in the CLAUDE.md becomes "PIT runs only the tests in `src/test`; layer tests stay in `src/archTest`".
- **Mutation testing per story (F0024's form).** PIT gets its classes from the Makefile, as mutmut gets its modules:
  - On a story's branch: the changed files under `src/main/java`, `git diff --name-only $(git merge-base origin/main HEAD)` plus the untracked ones. Each path `src/main/java/a/b/C.java` becomes the class glob `a.b.C*` (inner classes included), passed as `-Ppit.targetClasses=...`, which the build script reads into `pitest { targetClasses = ... }`.
  - With `FEATURE`: the files of the feature's story commits, as today.
  - The recipe stops PIT with `timeout $(MUTANTS_SECONDS)` (540), as F0024's recipe does.
  - PIT has what mutmut 3.8 lacks: **incremental analysis**. With `historyInputLocation` / `historyOutputLocation` (or `withHistory = true`) it reuses the result of every mutant whose class and tests did not change. That fixes F0024's measured fault, where a stopped run reached the same mutants every time, for every unchanged mutant. The history file goes to `.reports/pit-history.bin`. **Risk:** PIT writes the history at the end of a run, so a run that `timeout` stops leaves none (*to be checked*). Until that is checked, the per-story run must fit in 540 s by its size, and PIT's `threads` = cores.
  - The last line: PIT prints `>> Generated <n> mutations Killed <k> (<p>%)` and `>> Ran <t> tests` in its statistics. The recipe greps those into `mutants: <k> killed of <n> mutant(s) in <c> class(es)`, or `mutants: partial, ... (stopped after 540 s)` when `timeout` returned 124, and then exits 1, as F0024 decision 3 has it.
  - The survivors are in `build/reports/pitest/mutations.xml` (`status="SURVIVED"`, `NO_COVERAGE`, `TIMED_OUT`). The reviewer reads them with `grep`, the way F0024's reviewer reads `mutmut results`. A parser like factory-rf's `check_mutants` is not needed for the template; the grep line is enough.
- **What `check` leaves out on purpose.** OWASP dependency-check and Gradle's `dependencyCheckAnalyze` need the NVD over the network, and their result changes with the day. A check whose result depends on the date breaks F0023's reuse and the offline rule. Recommendation: not in `check`. It can be a weekly job of the human's, outside the factory.

## 3. The factory's interfaces it touches

- **Project commands (R11).** `MakeProjectCommands` is enough. A `GradleProjectCommands` would have to learn task names (`spotlessCheck`, `archTest`) and the green-line format. That is exactly what R8 and R6 keep out of the engine. The Makefile is the adapter, and it lives in the project. Nothing in `src/factory` changes for the commands.
- **Write paths.** Tester `src/test/*`, coder `src/main/*` (Java and resources). Documenter `README.md` and `docs/*`. The build files at the root (`build.gradle.kts`, `settings.gradle.kts`, `gradle.properties`, `gradle/libs.versions.toml`, `gradle/wrapper/*`, `gradlew`, `gradle.lockfile`, `gradle/verification-metadata.xml`, `config/*`), `src/archTest/*` and `security/*` are in no write path. So the kernel refuses them, and "new dependency" is still a question to the human, as `pyproject.toml` is today. A project that generates a file the coder must commit (the todo demo's `docs/openapi.json`) adds that one path to the coder's write paths, as the Python demo does.
- **Protected paths.** The engine's list holds `Makefile`, `pyproject.toml` and `uv.lock` (Python names) among its ten. For Java, nothing needs adding while no write path covers the root. Not building a `protected_paths` key is the solid choice. Open question J6.
- **Tool paths** (`tool_paths`, F0019's kernel guard). An agent run's `make test` writes all of these, and each must be listed or the kernel refuses it:
  - `build/*`: the compiled classes, the test results, the reports Gradle writes under `build/reports`.
  - `.gradle/*`: the project cache directory (file hashes, the configuration cache).
  - `.reports/*`: JUnit, CPD, PMD, the PIT history.
  - `~/.gradle/*`: the wrapper's distribution, the dependency cache, native libraries, the init scripts it reads.
  - `~/.java/*`: Java's user preferences. Gradle touches them on some JDKs (*to be checked*; drop it if the probe shows no write).
  - `~/.m2/*` only if a project resolves from `mavenLocal()`, which the template does not do. Its CLAUDE.md says why not: a local Maven repository is state outside the lockfile.
- **Temporary files (a hard trap).** The JVM ignores `TMPDIR`: `java.io.tmpdir` is `/tmp` on Linux whatever the environment says. The kernel refuses `/tmp` and allows only the run's own `$TMPDIR`. So JUnit's `@TempDir`, `Files.createTempFile` and Gradle's own temporary files fail with `AccessDeniedException` inside an agent run. HotSpot's `hsperfdata_<user>` folder also goes to `/tmp`; it fails quietly but noisily. The template's Makefile therefore exports
  `JAVA_TOOL_OPTIONS = -Djava.io.tmpdir=$${TMPDIR:-/tmp} -XX:-UsePerfData`.
  That reaches the Gradle client, its single-use daemon and the test workers, which inherit the environment. Every JVM then prints `Picked up JAVA_TOOL_OPTIONS: ...` on standard error at its start. That line is never the last line, so the contract holds. This is the first thing the probe (section 7, J0) must confirm under `factory-confine`.
- **No Gradle daemon.** An agent's daemon would outlive the agent run (it detaches) and keep that run's Landlock rules. The next run's client would connect to it, and builds would run under the previous run's write paths and `$TMPDIR`: wrong refusals that are hard to read. Daemons are per user (the registry is in `~/.gradle/daemon`), so the factory's own runs never meet an agent's daemon, but two agent runs do. Hence `--no-daemon` in the Makefile and `org.gradle.daemon=false` in `gradle.properties`. Gradle still forks a single-use daemon when the client's JVM arguments differ from `org.gradle.jvmargs`, and that one ends with the build.
- **Two users.** The factory's `make check` runs as `factory`, the agents' runs as `agent`. Each has its own `~/.gradle`, so each user downloads the distribution and the dependencies once. `build/` and `.gradle/` in the checkout are written by both, the same two-user situation F0024 decision 13 meets in `mutants/`. With `umask 002` on both sides (sudoers and entrypoint), what one writes the other can rewrite. Gradle's lock files under `.gradle/` are created by whoever comes first. Risk: a lock file created without group write blocks the other user (*to be checked* in the probe). The fallback is `rm -rf build .gradle` as the first line of the factory's `check`, at the cost of a cold compile.
- **F0023's `not_read` and known results.** The key is the tree that `check` reads, plus the pipeline definition and the image. For a Gradle project, reuse is safe when every input of the build is in the tree or the image:
  - **Dependency locking** for every configuration, the build script classpath included (`dependencyLocking { lockAllConfigurations() }` and `buildscript { configurations.classpath { resolutionStrategy.activateDependencyLocking() } }`), so `gradle.lockfile` is in the tree.
  - **Dependency verification** (`gradle/verification-metadata.xml` with SHA-256), so a mirror cannot hand over different bytes for the same version.
  - **The wrapper's `distributionSha256Sum`** in `gradle/wrapper/gradle-wrapper.properties`.
  - **No dynamic versions** (`1.+`, `latest.release`). Locking with `--write-locks` is the human's step, like `uv lock`.
  - What is outside the tree: `~/.gradle/` (the caches, the downloaded distribution, the mirror's init script). With locking and verification, the init script changes only where the bytes come from, not which bytes. So reuse stays safe.
  - `not_read` for `check` would be as factory-rf's: `README.md`, `docs/*.md`, `factory/features/*.md`, `factory/features/*.jsonl`, `factory/stops.jsonl`, `planning/*`. Java resources such as `src/main/resources/*.md` stay read; the patterns are anchored.
  - The caveat F0023 decision 3 already accepts for `.venv` applies to `build/` and `.gradle/`: an agent could forge state there. The tests' `upToDateWhen { false }` and the build cache off make the factory's own run compute the tests' result itself.
  - With `secrets` inside `check`, the Java template takes F0023 decision 12 as it is: `secrets` runs as its own docs-stage check when `not_read` is used.
- **Records contract.** Nothing changes; the template only produces project commands.

## 4. The image

What it must add, as one more Dockerfile target. Recommendation: one Dockerfile with targets `python` (today's image), `java` and `typescript`, sharing every layer up to the factory. Compose picks the target per instance (`build.target: ${FACTORY_STACK:-python}`). Open question J1.

- **A JDK.** Debian 12 ships OpenJDK 17 only. Recommendation: `COPY --from=eclipse-temurin:21.0.<x>_<y>-jdk-noble@sha256:<digest> /opt/java/openjdk /opt/java/openjdk`. That is the official image named by digest, like `BASE_IMAGE`, and `tests/test_image.py`'s check that every base image is pinned by digest extends to it. Symlink `java`, `javac` and `keytool` into `/usr/local/bin`. **The agent run's `PATH` is fixed** (`/usr/local/bin:/usr/bin:/bin` plus the factory's scripts) and `JAVA_HOME` is not among the allowed names. The wrapper finds `java` on the `PATH`, and the Gradle toolchain finds the JDK through `org.gradle.java.installations.paths=/opt/java/openjdk` in the user's `~/.gradle/gradle.properties`, which the entrypoint writes for both users. Size: about 320 MB unpacked for the JDK (*to be checked*; a `jlink`ed runtime is not enough, because Gradle needs `javac`).
- **Gradle.** Not in the image. Each project's wrapper names its version and the SHA-256 of the distribution. The distribution, about 135 MB unpacked, is downloaded once per user into `~/.gradle/wrapper/dists`. Two named volumes keep both homes' `.gradle` across rebuilds: `gradle-agent` and `gradle-factory`, like `claude-home`. Putting a fixed Gradle into the image would tie the image to one project's version.
- **semgrep and detect-secrets** for the non-Python stacks. In a Python project they are project dependencies under `uv`. A Java project has no Python environment, so the image installs them as tools: `uv tool install semgrep==<the Python projects' pin> detect-secrets==1.5.0`, with `UV_TOOL_BIN_DIR=/usr/local/bin`. About 150 MB, most of it semgrep. Their versions are then the image's, not the project's, and a change of them changes the image identity in F0023's key, which is correct.
- **Node 24 LTS.** The image's Node is Debian's 18.20.4, which is past its end of life (April 2025), and Claude Code runs on it. The TypeScript design (its section 4) replaces it with the official Node 24 tarball for every target. Java gains nothing from it but loses nothing either.
- **Total.** About +500 MB over today's image for the `java` target (JDK plus tools), plus about 135 MB per user on the volumes. All pinned (R29): the Temurin digest, the tool versions, the wrapper's checksum in the project.

**Offline and corporate network (the Podman note: work uses rootless Podman on Windows and Mac).**

- **The Maven mirror.** The project keeps `mavenCentral()` and `gradlePluginPortal()`. At work, an init script `~/.gradle/init.d/mirror.gradle.kts` replaces every repository with the mirror (`settingsEvaluated { pluginManagement.repositories ... }` and `allprojects { repositories ... }`). No init script reaches the wrapper's distribution: the wrapper reads only the project's `gradle-wrapper.properties`. So either the mirror's distribution URL is written into the project, or the distribution is pre-seeded on the volumes. Recommendation: pre-seed. The operator copies the zip into each volume once (an operator-guide step), and the project keeps the public URL and checksum. Open question J3.
  The init script and `gradle.properties` are files the operator mounts read-only (Compose `configs` or a bind mount into `/home/agent/.gradle/init.d` and `/home/factory/.gradle/init.d`), never committed to the project.
- **A proxy.** The JVM ignores `HTTPS_PROXY`. Gradle needs `systemProp.https.proxyHost`, `systemProp.https.proxyPort` and `systemProp.http.nonProxyHosts` in the user's `~/.gradle/gradle.properties`, in the same mounted file. Claude Code itself needs `HTTPS_PROXY` in its environment, and the agent run's environment is scrubbed to six names. **That is a factory gap independent of Java:** at work behind a proxy, no agent run reaches the API today. A generic story (section 7, G1) lets the operator name proxy and CA variables that pass to the agent runs: `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` (and their lower-case forms) and `NODE_EXTRA_CA_CERTS`.
- **TLS interception.** A corporate root CA must be trusted by Debian (`update-ca-certificates`, used by git, curl and uv), by the JDK (`keytool -importcert` into `/opt/java/openjdk/lib/security/cacerts`) and by Node (`NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt`). Recommendation: an optional folder `image/ca-certificates/*.crt`, empty in the repository and git-ignored, read by one `RUN` step of every target. The build stays reproducible for a given set of files.
- **Podman specifics.** None beyond today's. Named volumes belong to sub-ids. Compose uses the docker-compose v2 provider. Nothing here needs root in the container.

## 5. The agents

What the shipped texts assume of Python, read in `claude/agents/*.md`:

| Text | Python assumption | Change |
|---|---|---|
| tester, Role: "No sleeps, no network, no real files outside `tmp_path`" | pytest's fixture | "outside the test framework's temporary folder (`CLAUDE.md` names it)". The Java CLAUDE.md names JUnit's `@TempDir`. |
| tester, Role: "named after the behaviour it checks (`test_blank_title_is_rejected`)" | pytest naming | Keep the rule and drop the example's form, or say "(for example `blank title is rejected`)". The project's CLAUDE.md gives its naming (`@Test void blankTitleIsRejected()`). |
| tester, stage 2 and 5: "collection errors because the modules under test do not exist yet", "the modules the test runner could not import" | Python import errors | "or a compile error that names the missing classes; your entry names them" |
| tester, stage 3: "Skip the type check in this stage" | mypy is separate from the tests | Holds for Java as well, because `lint` does not compile. No change. |
| coder, documenter, smoke tester, acceptance reviewer, Lessons: "`tempfile.TemporaryDirectory()` in Python, or `d=$(mktemp -d)`..." | Python first | "`mktemp -d` in the shell, or your language's temporary folder under `$TMPDIR` (`CLAUDE.md` says how)". The Java trap of `java.io.tmpdir` is handled by the Makefile, not by the agent. |
| reviewer, stage 1: "Do not read the Makefile, `pyproject.toml` or tool configuration" | Python file name | "the Makefile, the build files or tool configuration" |
| acceptance reviewer, step 3: "`uv run mutmut show <id>`" | mutmut | "read the survivors the way `CLAUDE.md` names (for mutmut `uv run mutmut show <id>`)". F0024's S0003 rewrites this paragraph anyway: one sentence to merge there. |
| acceptance reviewer, Lessons: "the `--junit-xml` file its `Makefile` names" | pytest flag | "the JUnit report its `Makefile` names, a file or a folder of files" |

Everything else (R1 to R14, the stage protocol, the journal, the write guard) is language-free. These eight edits are one generic story (G3). They change texts that `tests/test_claude_agent_texts.py` and `tests/shipped_agents.py` pin, so the story names those tests and the human's leave.

What moves into the project rather than into the agents:

- **The project's `CLAUDE.md`** (the template's `templates/java-gradle/CLAUDE.md`). It has the Python template's chapters, with Java's content:
  - *Architecture*: packages as layers, declared in `src/archTest`; records for values; interfaces nominal, so a repository `implements` its interface (the todo demo's "no inheritance of the protocol" reverses); no `null` across a boundary (NullAway); wiring in one place.
  - *Tests*: JUnit Jupiter, AssertJ, `@TempDir`, `@ParameterizedTest` with `@CsvSource` or `@MethodSource` for both sides of a limit; one test class per production class under the same package; no mocking of the code under test; Mockito is not a dependency of the template (a fake through the interface instead).
  - *Checks*: the targets above with their lines; PIT's per-story or feature form; the `JAVA_TOOL_OPTIONS` line and why.
  - *Not without asking*: a new dependency (a change to `libs.versions.toml` or `gradle.lockfile`), a `@SuppressWarnings` or `@SuppressFBWarnings`, a `// NOPMD` or `// CHECKSTYLE:OFF`, a Checkstyle or SpotBugs exclusion, a change under `src/archTest`.
- **Skills (F0022).** Know-how too long for CLAUDE.md goes in `.claude/skills/`, for example "reading a Gradle failure" (where `* What went wrong:` and the test report are, how to run one test class with `--tests`) or "reading PIT's mutations.xml". They are optional. F0022 lets a project add them later without a factory change.
- **Project agents (F0022).** Not needed. No role's text is Python-bound beyond the eight sentences above, and replacing a whole agent would freeze it against later fixes of the shipped one.

## 6. A demo for the stack

Recommendation: the todo service again, as `demo/todo-service-java/`. It has the same three features and eight stories, so that a run is comparable with the Python baseline run in time, cost, send-backs and questions. The stack: Spring Boot 3.5.x or 4.0.x (*to be checked*; the work projects decide which), Spring MVC, `JdbcClient` over SQLite (`org.xerial:sqlite-jdbc` 3.50.x, Apache-2.0) or the in-memory repository, and springdoc-openapi for `docs/openapi.json`. Spring Boot is chosen over a micro-framework (Javalin) because the work projects are Spring. The demo should show the template's checks against a realistic dependency tree: the licence report, SpotBugs and PIT's speed on it. Open question J5.

How its stories would read. The Interface shows Java signatures, with the same rules expressed as Java expresses them:

```java
// src/main/java/app/domain/Todo.java
public record Todo(UUID id, String title, boolean done, Instant createdAt) {
  public static final int MAX_TITLE_LENGTH = 200;
  public Todo { /* strips the title; InvalidTitle outside 1..200; null id, title or createdAt is an NPE */ }
  public static Todo create(String title, Clock clock) { ... }
  public Todo withTitle(String title) { ... }
  public Todo withDone(boolean done) { ... }
}
```

What changes against the Python stories:

- Decision 2 (UTC; a naive time is an error) shrinks to "an `Instant`". The type carries the rule, so its criterion disappears.
- Decision 15 (no repository inherits the protocol) becomes "every repository `implements TodoRepository`; one abstract contract test class `TodoRepositoryContract` with a subclass per repository". That is JUnit's form of the parametrized contract test.
- Decision 6 (one error shape) becomes a `@RestControllerAdvice`, and decision 7's 422 needs a `@Valid` record with a cross-field check. Spring returns 400 by default, so the story states 422 explicitly.
- `TODO_DB` becomes `todo.db` as a Spring property with the environment variable `TODO_DB` as its source.
- The tests name test classes and methods (`criterion 3: src/test/java/app/domain/TodoTest.java::blankTitleIsRejected`).
- HTTP through `MockMvc` or `WebTestClient` against the application context, no server port (the Python "TestClient, no server process" rule).

## 7. The order of the stories, and the open questions

### Before any story: a probe (no story, the human's or a design agent's half hour)

**J0.** In a throwaway container of the current image, with a Temurin JDK copied in, run a minimal Gradle 9 project with JUnit, `@TempDir` and one PIT run under `factory-confine` as the agent user. Use the tool paths of section 3 and the Makefile's `JAVA_TOOL_OPTIONS`. Write it up as `planning/overnight/probe-java-<date>.md`, as F0019 had its probe. It answers:

- Does every write land in a tool path or `$TMPDIR`?
- Do `~/.java` and the lock files under `.gradle/` behave with two users?
- What does one Gradle call per target cost?
- Is PIT's history written when `timeout` stops PIT?

### Generic stories (both stacks need them; build once)

- **G1. Proxy and CA variables reach the agent runs.** `ALLOWED_ENVIRONMENT_NAMES` gains `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, their lower-case forms and `NODE_EXTRA_CA_CERTS`, passed only when set. It is a domain constant, its test and one line of the operator guide. Needed at work for any stack, Python included, if work has a proxy (open question J3).
- **G2. Node 24 LTS in the image** (the TypeScript design's story T1): it replaces Debian's Node 18, pins the tarball's SHA-256, and adds the optional corporate CA folder for every target. `tests/test_image.py`'s pinned Debian set loses `nodejs` and `npm`; that needs the human's leave.
- **G3. The shipped agents' texts are stack-neutral**: the eight edits of section 5, with the leave for the tests that pin those texts.
- **G4. The templates' folder.** `template/` becomes `templates/python-uv/`, beside `templates/java-gradle/` and `templates/typescript-npm/`. It includes the Dockerfile's `COPY`, the tests that read `template/`, and the docs. It is optional but cheap now and dearer with every template (open question J7).

### The Java stories (each small, each inside factory-rf's write paths: `template*/`, `image/*`, `claude/*`)

1. **J1. The image's `java` target**: the Temurin JDK by digest, the symlinks, `uv tool install` of semgrep and detect-secrets, the two Gradle volumes and the entrypoint's `~/.gradle/gradle.properties` for both users. The tests in `tests/test_image.py`'s style: every base image by digest, every tool pinned, the target set.
2. **J2. The template's build and its three contract targets**: `settings.gradle.kts`, `build.gradle.kts`, `libs.versions.toml`, the wrapper with its checksum, `gradle.properties` (no daemon, no build cache, configuration cache), the `Makefile`'s `check`, `lint`, `types` and `test` with `JAVA_TOOL_OPTIONS`, `factory/pipeline.yml` with its `tool_paths`, and `CLAUDE.md`. The tests use a stand-in `gradlew` (`GRADLE=<stand-in>`), as the Python template's tests stand in `uv`: the targets' lines, the timing, a first failing line that stops the recipe, the `JAVA_TOOL_OPTIONS` export.
3. **J3. The other gate targets**: `layers` (the `archTest` source set), `sast` (SpotBugs, FindSecBugs, semgrep's Java rules vendored under `security/semgrep/`), `secrets` (with the lock and verification files left out), `licenses` (the allow list). Tested with the same stand-in, plus `secrets` against real files, as `tests/test_template_makefile.py` does.
4. **J4. The reports**: `duplicates` (CPD, PMD's unused rules, the counting line) and `mutants` (the feature form; the per-story form once F0024's real check has passed on factory-rf).
5. **J5. The demo**: `demo/todo-service-java/` with its project, its eight stories rewritten as section 6 says, and its README.

Then the human's real check: one run of the Java demo on an instance of the `java` target. First at home, then at work behind the mirror.

### Open questions for the human (independent ones first, each with a recommendation)

- **J1. One image or one per stack?** (a) One Dockerfile with targets `python`, `java` and `typescript`, chosen per instance. (b) One image holding all stacks, about 1.2 GB, simpler to operate. (c) Separate Dockerfiles. **Recommendation: (a).** Each instance builds one project, the layers are shared, and F0023's image key changes only for the stack that changed.
- **J2. Which JDK?** (a) 21 LTS. (b) 25 LTS (Sept 2025). (c) The work projects' own version (17?). **Recommendation: 21**, unless the work projects are on 17. The Gradle toolchain lets a project ask for 17 while Gradle runs on 21, but the image carries one JDK, and a second costs another 300 MB.
- **J3. What is the work network?** Is there a forced proxy, a TLS-intercepting CA, a Maven and npm mirror (Artifactory or Nexus), and may the container reach `services.gradle.org`? **Recommendation:** find out before J1. G1 and the CA folder only matter if the answer is yes. The mirror is in any case configured in the users' Gradle homes, never in the project.
- **J4. One Gradle call per target, or one for all of `check`?** **Recommendation: one per target**, measured in the probe J0. Switch only if the overhead is above about a third of `check`.
- **J5. The demo's stack.** (a) Spring Boot, as at work. (b) Javalin or the JDK's own HTTP server, smaller and faster. **Recommendation: (a)**, because the demo is to show the work case.
- **J6. Project-declared protected paths?** A key `protected_paths` in the pipeline definition that adds to the engine's ten. **Recommendation: not now.** No Java or TypeScript write path reaches a build file; the kernel already refuses them. Build it when a project needs a write path that covers one.
- **J7. Rename `template/` to `templates/python-uv/` (G4)?** **Recommendation: yes, before the first second template**, in one story of its own.
- **J8. Per-story mutation testing in the template?** **Recommendation:** start the Java template with the feature-level form, as F0024 decision 12 keeps it for Python. Move to the per-story form when F0024's change 3 has shown it on factory-rf and the probe J0 has shown that PIT's history survives a stopped run.

### The biggest risk

The JVM and Gradle under the write guard and on the corporate network. Neither has been probed. `java.io.tmpdir`, `hsperfdata`, `~/.java`, the lock files of two users and a lingering daemon each fail as an unexplained `Permission denied`, the stall the agents read worst. And the first run at work goes through a mirror, a proxy and a CA that no test here can see. The probe J0 and question J3 come before any story for that reason.
