# One instance, one project, one checkout

## Assignment (as of log entry 1)

Build the settings and the loop of one factory instance. An instance is told its project and its name by two environment variables, may be told the identity of its commits by two more, keeps its checkout at one fixed path, reclones that checkout when it is missing, and ticks in a loop whose pause is 15 seconds after activity and doubles while idle, up to 120 seconds. Nothing in the loop or the settings can name a second project. This covers ST7.1, ST7.2 and ST7.3, implements R2 and R25, and keeps kept thing 15 (one instance, one project) and kept thing 16 (the pause follows activity). The console scripts `factory-run` and `factory-health` are already declared in `pyproject.toml`. This story builds the pure parts: the settings, the scheduler and the checkout preparer. The next story builds the boundaries from the settings, and the story after it the process that runs them (`main`, `run_instance`). Later stories of this feature add fields to `InstanceSettings` and wrap the checkout preparation; the first tick of a run happens at once, so a restart with the same instance name reaches its first look without waiting out any pause. The commit identity (`GIT_USER_NAME`, `GIT_USER_EMAIL`) overrides `GitIdentity`'s default `factory <factory@noreply.invalid>` through the settings (questionnaire 1, Q18; F0001 decision 10); no preflight item checks it. The settings also hold the identity of the image the instance runs on, which the human decided on 2026-10-14 is read from a file that the image build generates (`/opt/factory/image-id`, written by the image story), so that a rebuild with the same build argument cannot keep an old preflight stamp valid (ST4.3); a missing or empty file is refused. The reader of that file is a parameter, so that the domain does no I/O.

## Interface

`src/factory/domain/errors.py` gains one type:

```python
class SettingsInvalid(FactoryError):
    variable: str
    fault: str
    def __init__(self, variable: str, fault: str) -> None: ...   # the message is "<variable>: <fault>"
```

`src/factory/domain/settings.py`

```python
CHECKOUT_PATH = Path("/work/checkout")
STATE_DIRECTORY = Path("/state")
REPOSITORY_URL_VARIABLE = "FACTORY_REPOSITORY_URL"
INSTANCE_VARIABLE = "FACTORY_INSTANCE"
GIT_USER_NAME_VARIABLE = "GIT_USER_NAME"
GIT_USER_EMAIL_VARIABLE = "GIT_USER_EMAIL"
DEFAULT_GIT_IDENTITY = GitIdentity(name="factory", email="factory@noreply.invalid")
IMAGE_ID_FILE = Path("/opt/factory/image-id")
IMAGE_ID_FILE_VARIABLE = "FACTORY_IMAGE_ID_FILE"

class InstanceSettings(BaseModel):            # frozen, extra="forbid", like every DTO
    repository_url: str
    instance: Name                            # factory.domain.identifiers.Name
    git_identity: GitIdentity = DEFAULT_GIT_IDENTITY     # factory.domain.git.GitIdentity
    image: str | None = None                  # the image identity; None outside an image
    checkout: Path = CHECKOUT_PATH
    state_directory: Path = STATE_DIRECTORY

def read_settings(
    environ: Mapping[str, str], read_file: Callable[[Path], str] | None = None
) -> InstanceSettings: ...
```

`src/factory/application/scheduler.py`

```python
FIRST_PAUSE = timedelta(seconds=15)
MAX_PAUSE = timedelta(seconds=120)

def pause_after(idle_ticks: int) -> timedelta: ...      # min(FIRST_PAUSE * 2 ** idle_ticks, MAX_PAUSE)

class Scheduler:
    def __init__(
        self,
        prepare: Callable[[], bool],
        tick: Callable[[], bool],
        sleep: Callable[[float], None],
        should_stop: Callable[[], bool],
        log: FactoryLog,
    ) -> None: ...
    def run(self) -> None: ...

class CheckoutPreparer:
    def __init__(self, git: Git, settings: InstanceSettings) -> None: ...
    def prepare(self) -> bool: ...
```

Rules:

- `read_settings` requires exactly two variables, `FACTORY_REPOSITORY_URL` and `FACTORY_INSTANCE`, and reads two optional ones, `GIT_USER_NAME` and `GIT_USER_EMAIL`. `checkout` and `state_directory` are never read from the environment: they are always the two constants unless a test builds the settings directly.
- A required variable that is missing, empty or only whitespace raises `SettingsInvalid` whose `variable` is that variable's name. `read_settings` reports the first fault in the order `FACTORY_REPOSITORY_URL`, `FACTORY_INSTANCE`, `FACTORY_IMAGE_ID_FILE`.
- `repository_url` must contain no whitespace and no comma (one repository, R2), else `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"`.
- `instance` must match `Name` (`^[a-z][a-z0-9-]*$`), else `SettingsInvalid` with `variable == "FACTORY_INSTANCE"`.
- `git_identity` is `GitIdentity(name=<GIT_USER_NAME>, email=<GIT_USER_EMAIL>)`, each half taken from its variable when that is set and not blank (the value stripped), else from `DEFAULT_GIT_IDENTITY`; the two halves are decided one by one.
- `image` is `None` when `read_file` is `None` (no file is read). With `read_file` set, `image` is the text of the file named by `FACTORY_IMAGE_ID_FILE` (default `IMAGE_ID_FILE`), stripped; a file that does not exist, cannot be read (the reader raises `OSError`) or holds only whitespace raises `SettingsInvalid` with `variable == "FACTORY_IMAGE_ID_FILE"`. The variable `FACTORY_IMAGE` is never read as an identity: it is only a label of the build.
- `pause_after(n)` is the pause after an iteration that left `n` consecutive idle ticks since the last activity (0 right after activity). A negative `n` raises `ValueError`.
- `Scheduler.run` repeats iterations until `should_stop()` is true. It asks `should_stop()` before every iteration and again after every iteration, before the sleep. The first iteration runs before any sleep.
- One iteration calls `prepare()`. When that returns `False` the tick is not called and the iteration counts as idle. Otherwise it calls `tick()`; `True` means activity, `False` idle. After the iteration it calls `sleep(pause_after(idle_ticks).total_seconds())`.
- An `Exception` raised by `prepare` or `tick` is caught, written as one line `iteration failed: <exception type name>: <message>` through `log.line`, and counts as idle. A `BaseException` (such as `InjectedKill`) is not caught.
- `CheckoutPreparer.prepare` returns `True` without calling git when `settings.checkout / ".git"` exists. Otherwise it calls `git.clone(settings.repository_url)` and returns `True`. A `GitError` from the clone is not caught. A checkout whose clone was killed half-way is not recognised: the operator guide tells the operator to delete the directory, because R18 calls the checkout disposable and a clone killed half-way is rare.

Tests: `tests/domain/test_settings.py` (the image criteria use a `read_file` stub backed by a dictionary), `tests/application/test_scheduler.py`, `tests/test_single_project.py` (the search). The scheduler tests pass recording callables for `prepare`, `tick`, `sleep` and `should_stop`, and a `FactoryLog` that collects lines; the preparer tests use `GitCli` on a real bare remote in `tmp_path`. The closed-model test builds the model through a variable typed `type[BaseModel]` and assigns with `setattr`, the field's name in a variable (`CLAUDE.md`, Tests).

## Acceptance criteria

1. `read_settings({"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "factory-1"})` returns settings with that repository URL and that instance name, `git_identity == GitIdentity(name="factory", email="factory@noreply.invalid")`, `checkout == Path("/work/checkout")` and `state_directory == Path("/state")`.
2. Each of the two required variables, when missing, empty or only spaces (six cases), raises `SettingsInvalid` whose `variable` is that variable's name.
3. A repository URL that contains a comma (`a/b,c/d`) or a space (`a b`) raises `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"`; `https://github.com/owner/project.git` is accepted.
4. An instance name is accepted when it matches `^[a-z][a-z0-9-]*$` (`factory-1`, `a`) and raises `SettingsInvalid` with `variable == "FACTORY_INSTANCE"` for `Factory-1`, `1st`, `factory_1` and `-x`.
5. `FACTORY_CHECKOUT`, `FACTORY_STATE_DIRECTORY` and any other variable in the mapping change nothing: `checkout` and `state_directory` stay the two constants.
6. A search of every `.py` file under `src/factory` finds no match of the regular expression `\bREPOS\b` (v1's list of repositories is gone, ST7.2; `FACTORY_REPOSITORY_URL` is not a match).
7. With `GIT_USER_NAME=Ann` and `GIT_USER_EMAIL=ann@example.invalid` in the mapping, `git_identity == GitIdentity(name="Ann", email="ann@example.invalid")`.
8. Each half of the identity falls back to its own default: with only `GIT_USER_NAME` set the email is `factory@noreply.invalid`; with only `GIT_USER_EMAIL` set the name is `factory`; a value of only spaces counts as unset (four cases).
9. `read_settings` with a `read_file` that answers `build-7` and a newline for the path in `FACTORY_IMAGE_ID_FILE` gives `image == "build-7"`; the default path is `/opt/factory/image-id`; without `read_file`, `image is None`.
10. `read_settings` with a `read_file` raises `SettingsInvalid` with `variable == "FACTORY_IMAGE_ID_FILE"` when the file does not exist (the reader raises `FileNotFoundError`), when it is empty and when it holds only spaces (three cases).
11. `FACTORY_IMAGE=other` in the mapping changes nothing: the identity is the file's, and `None` without a reader.
12. `InstanceSettings` refuses an unknown key and an assignment to a field with `ValidationError`; `instance="Factory-1"` is refused and `instance="factory-1"` is accepted when the model is built directly.
13. `pause_after(n)` for `n` in 0, 1, 2, 3, 4 and 10 is 15, 30, 60, 120, 120 and 120 seconds.
14. `pause_after(-1)` raises `ValueError`.
15. `Scheduler.run` calls `prepare` and `tick` once per iteration, in that order, and the first call it makes is `prepare`, before any `sleep`: with `should_stop` true after the third `tick`, `tick` was called exactly 3 times and `sleep` exactly 2 times (ST7.1: the one `tick` callable is the whole loop).
16. The sleeps follow the idle count since the last activity: ticks returning `True, False, False, False, False, False` give sleeps of 15.0, 30.0, 60.0, 120.0 and 120.0 seconds, and ticks returning `False, False, True, False` give 30.0, 60.0 and 15.0 seconds.
17. When `prepare` returns `False` the tick is not called and the iteration counts as idle: `prepare` results `False, True, True` with a `tick` that always returns `True` and `should_stop` true after the third `prepare` give two tick calls and sleeps of 30.0 and 15.0 seconds.
18. A `ValueError("boom")` raised by `tick` writes the line `iteration failed: ValueError: boom` through the log, the loop goes on with the next iteration, and the sleep that follows is the idle pause of 30.0 seconds.
19. An `InjectedKill` raised by `tick` leaves `Scheduler.run` and is not logged.
20. `CheckoutPreparer.prepare` on a missing checkout directory clones the settings' repository into it and returns `True`: `origin/main` then resolves in the new checkout; after `shutil.rmtree` of the whole checkout, a second `prepare` clones again (ST7.3).
21. `CheckoutPreparer.prepare` on a checkout that already holds a clone returns `True` and leaves it as it is: a file the test added to the work tree is still there.
22. `CheckoutPreparer.prepare` on a directory that holds files but no `.git` raises `GitError` and changes nothing in the directory.
23. make check stays green.
24. docs: `docs/operator-guide.md` lists the variables (`FACTORY_REPOSITORY_URL` and `FACTORY_INSTANCE`, and the optional `GIT_USER_NAME` and `GIT_USER_EMAIL` with their default `factory <factory@noreply.invalid>`, and `FACTORY_IMAGE_ID_FILE`, the file that holds the image identity, `/opt/factory/image-id` by default), the fixed checkout path `/work/checkout` and state directory `/state`, the pauses (15 seconds after activity, doubling to 120 seconds while idle), and that only a missing checkout is recloned, so the operator deletes a checkout whose clone was killed half-way; `docs/decisions.md` records why one instance runs one project (R2) why the commit identity has a default and no preflight item (questionnaire 1, Q18), and why the image identity is read from a file (the human, 2026-10-14).

## Demo

```bash
uv run python -c "
from factory.domain.settings import read_settings
s = read_settings({'FACTORY_REPOSITORY_URL': '/srv/project.git', 'FACTORY_INSTANCE': 'factory-1'})
print(s.instance, s.repository_url, s.checkout, s.state_directory)
"
```
Expect: one line, `factory-1 /srv/project.git /work/checkout /state`.

```bash
uv run python -c "
from factory.domain.settings import read_settings
base = {'FACTORY_REPOSITORY_URL': '/srv/project.git', 'FACTORY_INSTANCE': 'factory-1'}
print(read_settings(base).git_identity.name, read_settings({**base, 'GIT_USER_NAME': 'Ann'}).git_identity.name)
"
```
Expect: one line, `factory Ann`.

```bash
uv run python -c "
from factory.application.scheduler import pause_after
print([int(pause_after(n).total_seconds()) for n in range(6)])
"
```
Expect: `[15, 30, 60, 120, 120, 120]`.

```bash
uv run python -c "
from factory.application.scheduler import Scheduler
results = iter([True, False, False])
sleeps = []
class Log:
    def line(self, text):
        print('log:', text)
Scheduler(prepare=lambda: True, tick=lambda: next(results), sleep=sleeps.append, should_stop=lambda: len(sleeps) >= 3, log=Log()).run()
print(sleeps)
"
```
Expect: one line, `[15.0, 30.0, 60.0]`: the first tick ran at once, activity gave 15 seconds and each idle tick doubled the pause.

## Log (append only)

1. 2026-10-12 human: created.
