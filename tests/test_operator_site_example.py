"""The operator's example site file: its comments name the required keys and the true defaults."""

import re
import shutil
from pathlib import Path

import pytest

from factory.agents.domain.opencode_provider import read_provider
from operator_job_support import INSTANCE, TAG, job_runner, make_job_repository, provider_text
from operator_support import (
    INTERFACE_KEYS,
    SITE_EXAMPLE,
    example_keys,
    example_values,
    operator_environment,
    run_library,
    run_site,
)
from recording_stand_in_support import read_records

HOSTING_KEYS = ("SITE_REPOSITORY", "SITE_CHECKOUT")
OPTIONAL_DEFAULT = re.compile(r"\. Optional; the default is (.+)\.$")


def comment_of(key: str) -> str:
    """The text of the comment line directly above the key's line, without its `# `."""
    lines = SITE_EXAMPLE.read_text(encoding="utf-8").splitlines()
    index = next(number for number, line in enumerate(lines) if line.startswith(f"{key}="))
    assert index > 0
    assert lines[index - 1].startswith("# "), lines[index - 1]
    return lines[index - 1].removeprefix("# ")


def default_of(key: str) -> str:
    """The default the key's comment names."""
    match = OPTIONAL_DEFAULT.search(comment_of(key))
    assert match is not None, comment_of(key)
    return match.group(1)


@pytest.fixture(scope="module")
def job_keys(tmp_path_factory: pytest.TempPathFactory) -> set[str]:
    """The keys of `site_job_keys`, read by sourcing the site library."""
    folder = tmp_path_factory.mktemp("keys")
    result = run_library('printf "%s\\n" $site_job_keys\n', folder, operator_environment(folder))
    assert result.exit_status == 0, result.stderr
    return set(result.stdout.split())


@pytest.mark.parametrize("key", example_keys())
def test_each_comment_says_whether_its_key_is_required_and_otherwise_names_a_default(
    job_keys: set[str], key: str
) -> None:
    comment = comment_of(key)

    if key in HOSTING_KEYS:
        assert comment.endswith(". Required."), comment
    elif key in job_keys:
        assert comment.endswith(". Required for a job."), comment
    else:
        assert OPTIONAL_DEFAULT.search(comment) is not None, comment


@pytest.fixture
def job_run(tmp_path: Path) -> tuple[Path, Path]:
    """A tagged repository of the operator's scripts and the gcloud stand-in's record."""
    return make_job_repository(tmp_path / "repo"), tmp_path / "gcloud.jsonl"


def without(key: str) -> dict[str, str]:
    """The example's values with the key's line left out."""
    return {name: value for name, value in example_values().items() if name != key}


@pytest.mark.parametrize(
    ("key", "prefix"),
    [
        pytest.param("SITE_CPU", "--cpu=", id="cpu"),
        pytest.param("SITE_MEMORY", "--memory=", id="memory"),
        pytest.param("SITE_TIMEOUT", "--task-timeout=", id="timeout"),
        pytest.param("SITE_IDLE_MINUTES", "FACTORY_IDLE_SHUTDOWN_MINUTES=", id="idle-minutes"),
    ],
)
def test_the_named_size_defaults_are_those_the_job_takes_without_the_key(
    tmp_path: Path, job_run: tuple[Path, Path], key: str, prefix: str
) -> None:
    repository, records = job_run
    run = job_runner(tmp_path, repository, records)

    result = run(["create", "--dry-run"], without(key), SITE_CODE_REF=TAG)

    assert result.exit_status == 0, result.stderr
    arguments = result.stdout.splitlines()
    env_flag = [word for word in arguments if word.startswith("--set-env-vars=")]
    assert len(env_flag) == 1
    words = [*arguments, *env_flag[0].split("@")]
    assert f"{prefix}{default_of(key)}" in words


@pytest.mark.parametrize(
    ("key", "price"),
    [
        pytest.param("SITE_MODEL_INPUT_COST", "input_cost", id="input"),
        pytest.param("SITE_MODEL_OUTPUT_COST", "output_cost", id="output"),
    ],
)
def test_the_named_price_default_is_the_price_the_provider_file_holds_without_the_key(
    tmp_path: Path, job_run: tuple[Path, Path], key: str, price: str
) -> None:
    repository, records = job_run
    run = job_runner(tmp_path, repository, records)

    result = run(["create"], without(key), SITE_CODE_REF=TAG, SITE_INSTANCE=INSTANCE)

    assert result.exit_status == 0, result.stderr
    provider = read_provider(provider_text(tmp_path, read_records(records)[-1]))
    model = example_values()["SITE_MODEL"]
    assert getattr(provider.models[model], price) == float(default_of(key))


def test_the_sanitise_rules_default_is_the_file_beside_the_site_file() -> None:
    assert default_of("SITE_SANITISE_RULES") == "sanitise.rules beside the site file"


def test_show_on_a_copy_of_the_example_says_set_for_every_key_in_order(tmp_path: Path) -> None:
    folder = tmp_path / "site"
    folder.mkdir()
    site_file = folder / "site.env"
    shutil.copyfile(SITE_EXAMPLE, site_file)

    result = run_site(
        ["show"], tmp_path, operator_environment(tmp_path, FACTORY_SITE=str(site_file))
    )

    assert result.exit_status == 0, result.stderr
    assert result.stdout.splitlines() == [f"{key}=set" for key in INTERFACE_KEYS]
