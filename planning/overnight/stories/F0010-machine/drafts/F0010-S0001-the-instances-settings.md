# The instance's settings

## Assignment (as of log entry 1)

Build the settings of one factory instance. An instance is told its project and its name by two environment variables, may be told the identity of its commits by two more, and keeps its checkout and its state at two fixed paths. Nothing in the settings can name a second project. This covers ST7.2, implements R2 and R25, and keeps kept thing 15 (one instance, one project). The console scripts `factory-run` and `factory-health` are already declared in `pyproject.toml`. This story builds the pure part: the settings and the error that refuses them. The next story builds the loop that ticks with them (the scheduler and the checkout preparer), the story after it the boundaries from the settings, and the one after that the process that runs them (`main`, `run_instance`). Later stories of this feature add fields to `InstanceSettings`. The commit identity (`GIT_USER_NAME`, `GIT_USER_EMAIL`) overrides `GitIdentity`'s default `factory <factory@noreply.invalid>` through the settings (questionnaire 1, Q18; F0001 decision 10); no preflight item checks it. The settings also hold the identity of the image the instance runs on, which the human decided on 2026-10-14 is read from a file that the image build generates (`/opt/factory/image-id`, written by the image story), so that a rebuild with the same build argument cannot keep an old preflight stamp valid (ST4.3); a missing or empty file is refused. The reader of that file is a parameter, so that the domain does no I/O.

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

Rules:

- `read_settings` requires exactly two variables, `FACTORY_REPOSITORY_URL` and `FACTORY_INSTANCE`, and reads two optional ones, `GIT_USER_NAME` and `GIT_USER_EMAIL`. `checkout` and `state_directory` are never read from the environment: they are always the two constants unless a test builds the settings directly.
- A required variable that is missing, empty or only whitespace raises `SettingsInvalid` whose `variable` is that variable's name. `read_settings` reports the first fault in the order `FACTORY_REPOSITORY_URL`, `FACTORY_INSTANCE`, `FACTORY_IMAGE_ID_FILE`.
- `repository_url` must contain no whitespace and no comma (one repository, R2), else `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"`.
- `repository_url` must hold no password: a URL with `://` whose part up to the next `/` holds an `@` with a `:` before it raises `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"`, because git would keep the password in the shared checkout's `.git/config`, which the agent can read; a user name alone (`ssh://git@github.com/owner/project.git`) and the form `git@github.com:owner/project.git` are accepted (the human, 2026-10-14).
- `instance` must match `Name` (`^[a-z][a-z0-9-]*$`), else `SettingsInvalid` with `variable == "FACTORY_INSTANCE"`.
- `git_identity` is `GitIdentity(name=<GIT_USER_NAME>, email=<GIT_USER_EMAIL>)`, each half taken from its variable when that is set and not blank (the value stripped), else from `DEFAULT_GIT_IDENTITY`; the two halves are decided one by one.
- `image` is `None` when `read_file` is `None` (no file is read). With `read_file` set, `image` is the text of the file named by `FACTORY_IMAGE_ID_FILE` (default `IMAGE_ID_FILE`), stripped; a file that does not exist, cannot be read (the reader raises `OSError`) or holds only whitespace raises `SettingsInvalid` with `variable == "FACTORY_IMAGE_ID_FILE"`. The variable `FACTORY_IMAGE` is never read as an identity: it is only a label of the build.

Tests: `tests/domain/test_settings.py` (the image criteria use a `read_file` stub backed by a dictionary), `tests/test_single_project.py` (the search). The closed-model test builds the model through a variable typed `type[BaseModel]` and assigns with `setattr`, the field's name in a variable (`CLAUDE.md`, Tests).

## Acceptance criteria

1. `read_settings({"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "factory-1"})` returns settings with that repository URL and that instance name, `git_identity == GitIdentity(name="factory", email="factory@noreply.invalid")`, `checkout == Path("/work/checkout")` and `state_directory == Path("/state")`.
2. Each of the two required variables, when missing, empty or only spaces (six cases), raises `SettingsInvalid` whose `variable` is that variable's name.
3. A repository URL that contains a comma (`a/b,c/d`) or a space (`a b`) raises `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"`; `https://github.com/owner/project.git` is accepted.
4. An instance name is accepted when it matches `^[a-z][a-z0-9-]*$` (`factory-1`, `a`) and raises `SettingsInvalid` with `variable == "FACTORY_INSTANCE"` for `Factory-1`, `1st`, `factory_1` and `-x`.
5. `FACTORY_CHECKOUT`, `FACTORY_STATE_DIRECTORY` and any other variable in the mapping change nothing: `checkout` and `state_directory` stay the two constants.
6. A search of every `.py` file under `src/factory` finds no match of the regular expression `\bREPOS\b` (v1's list of repositories is gone, ST7.2; `FACTORY_REPOSITORY_URL` is not a match).
7. With `GIT_USER_NAME=Ann` and `GIT_USER_EMAIL=ann@example.invalid` in the mapping, `git_identity == GitIdentity(name="Ann", email="ann@example.invalid")`.
8. Each half of the identity falls back to its own default: with only `GIT_USER_NAME` set the email is `factory@noreply.invalid`; with only `GIT_USER_EMAIL` set the name is `factory`; a value of only spaces counts as unset; `GIT_USER_NAME=" Ann "` gives the name `Ann` (five cases).
9. `read_settings` with a `read_file` that answers `build-7` and a newline for the path in `FACTORY_IMAGE_ID_FILE` gives `image == "build-7"`; the default path is `/opt/factory/image-id`; without `read_file`, `image is None`.
10. `read_settings` with a `read_file` raises `SettingsInvalid` with `variable == "FACTORY_IMAGE_ID_FILE"` when the file does not exist (the reader raises `FileNotFoundError`), when it cannot be read (the reader raises `PermissionError`), when it is empty and when it holds only spaces (four cases).
11. `FACTORY_IMAGE=other` in the mapping changes nothing: the identity is the file's, and `None` without a reader.
12. `InstanceSettings` refuses an unknown key and an assignment to a field with `ValidationError`; `instance="Factory-1"` is refused and `instance="factory-1"` is accepted when the model is built directly.
13. `read_settings` reports the first fault in the order `FACTORY_REPOSITORY_URL`, `FACTORY_INSTANCE`, `FACTORY_IMAGE_ID_FILE`: an empty mapping with a `read_file` that raises `FileNotFoundError` raises `SettingsInvalid` naming `FACTORY_REPOSITORY_URL`, and a valid URL with the instance `Factory-1` and the same reader raises it naming `FACTORY_INSTANCE`.
14. `SettingsInvalid("FACTORY_INSTANCE", "missing")` has `variable == "FACTORY_INSTANCE"`, `fault == "missing"` and the message `FACTORY_INSTANCE: missing`.
15. A repository URL with a password raises `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"`: the test joins `https://user:`, `example-value` and `@github.com/owner/project.git` into one URL, and `ssh://git:`, `example-value` and `@github.com/owner/project.git` into another, so that no line of the story or the test holds a URL with credentials (`make secrets` flags one); `ssh://git@github.com/owner/project.git`, `git@github.com:owner/project.git` and `https://user@github.com/owner/project.git` are accepted.
16. make check stays green.
17. docs: `docs/operator-guide.md` lists the variables (`FACTORY_REPOSITORY_URL` and `FACTORY_INSTANCE`, and the optional `GIT_USER_NAME` and `GIT_USER_EMAIL` with their default `factory <factory@noreply.invalid>`, and `FACTORY_IMAGE_ID_FILE`, the file that holds the image identity, `/opt/factory/image-id` by default) and the fixed checkout path `/work/checkout` and state directory `/state`; `docs/decisions.md` records why one instance runs one project (R2), why the commit identity has a default and no preflight item (questionnaire 1, Q18), and why the image identity is read from a file (the human, 2026-10-14); `docs/operator-guide.md` says that a repository URL with a password is refused and that the token belongs in the token file.

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

## Log (append only)

1. 2026-10-12 human: created.
