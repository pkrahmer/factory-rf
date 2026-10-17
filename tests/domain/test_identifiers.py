"""Work item ids, file and directory names, their order and their branch names."""

from collections.abc import Callable

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from factory.domain.identifiers import (
    ACCEPTANCE_ID,
    FEATURE_ID,
    STORY_ID,
    FeatureDirectoryName,
    FeatureId,
    Name,
    WorkItemFileName,
    WorkItemId,
    branch_name,
    feature_of,
    is_acceptance,
    parse_feature_directory_name,
    parse_work_item_file_name,
    work_item_of_branch,
    work_item_order,
)

WORK_ITEM_ID = TypeAdapter(WorkItemId)
FEATURE = TypeAdapter(FeatureId)
NAME = TypeAdapter(Name)


@pytest.mark.parametrize(
    ("adapter", "text", "accepted"),
    [
        (WORK_ITEM_ID, "F0001-S0001", True),
        (WORK_ITEM_ID, "F0012-A0003", True),
        (WORK_ITEM_ID, "F001-S0001", False),
        (WORK_ITEM_ID, "F0001-X0001", False),
        (WORK_ITEM_ID, "f0001-s0001", False),
        (WORK_ITEM_ID, "F0001-S00001", False),
        (WORK_ITEM_ID, "F0001-S0001-slug", False),
        (WORK_ITEM_ID, "", False),
        (FEATURE, "F0001", True),
        (FEATURE, "F001", False),
        (FEATURE, "F00001", False),
        (FEATURE, "F0001-x", False),
        (NAME, "intake", True),
        (NAME, "smoke-test", True),
        (NAME, "a1", True),
        (NAME, "", False),
        (NAME, "1a", False),
        (NAME, "Intake", False),
        (NAME, "-a", False),
        (NAME, "a_b", False),
    ],
)
def test_id_and_name_types_accept_only_their_pattern(
    adapter: TypeAdapter[str], text: str, accepted: bool
) -> None:
    if accepted:
        assert adapter.validate_python(text) == text
    else:
        with pytest.raises(ValidationError):
            adapter.validate_python(text)


def test_id_patterns_are_the_stated_regular_expressions() -> None:
    assert FEATURE_ID == r"F\d{4}"
    assert STORY_ID == r"F\d{4}-S\d{4}"
    assert ACCEPTANCE_ID == r"F\d{4}-A\d{4}"


def _name_model(
    model: type[BaseModel], slug: str | None
) -> WorkItemFileName | FeatureDirectoryName:
    if model is WorkItemFileName:
        return WorkItemFileName(id="F0001-S0001", slug=slug)
    return FeatureDirectoryName(id="F0001", slug=slug)


@pytest.mark.parametrize("model", [WorkItemFileName, FeatureDirectoryName])
@pytest.mark.parametrize(
    ("slug", "accepted"),
    [
        (None, True),
        ("x", True),
        ("2fa", True),
        ("a-b", True),
        ("Bad", False),
        ("", False),
        ("a-", False),
        ("-a", False),
        ("a--b", False),
    ],
)
def test_name_models_accept_only_hyphen_joined_lower_case_slugs(
    model: type[BaseModel], slug: str | None, accepted: bool
) -> None:
    if accepted:
        assert _name_model(model, slug).slug == slug
    else:
        with pytest.raises(ValidationError):
            _name_model(model, slug)


@pytest.mark.parametrize(
    ("name", "work_item", "slug"),
    [
        ("F0001-S0001-domain-model.md", "F0001-S0001", "domain-model"),
        ("F0001-S0001.md", "F0001-S0001", None),
        ("F0002-S0001-2fa.md", "F0002-S0001", "2fa"),
        ("F0001-A0001-acceptance.md", "F0001-A0001", "acceptance"),
    ],
)
def test_work_item_file_name_parses_into_id_and_slug(
    name: str, work_item: str, slug: str | None
) -> None:
    parsed = parse_work_item_file_name(name)

    assert parsed == WorkItemFileName(id=work_item, slug=slug)


@pytest.mark.parametrize(
    "name",
    [
        "F0001-S0001",
        "F0001-S0001-Domain.md",
        "F0001-S0001-.md",
        "F0001-S0001-a-.md",
        "F0001-S0001-a--b.md",
        "F0001-S0001-a_b.md",
        "F0001-S001-x.md",
        "F0001-S0001-x.md.bak",
        "F0001-S0001-x.costs.jsonl",
        ".gitkeep",
    ],
)
def test_malformed_work_item_file_name_parses_to_none(name: str) -> None:
    assert parse_work_item_file_name(name) is None


@pytest.mark.parametrize(
    ("name", "feature", "slug"),
    [
        ("F0002-work-item-data", "F0002", "work-item-data"),
        ("F0002", "F0002", None),
        ("F0002-2fa", "F0002", "2fa"),
    ],
)
def test_feature_directory_name_parses_into_id_and_slug(
    name: str, feature: str, slug: str | None
) -> None:
    parsed = parse_feature_directory_name(name)

    assert parsed == FeatureDirectoryName(id=feature, slug=slug)


@pytest.mark.parametrize(
    "name", ["f0002-x", "F002-x", "F0002-Upper", "F0002-", "F0002-a-", "F0002-a--b", "F0002-x/y"]
)
def test_malformed_feature_directory_name_parses_to_none(name: str) -> None:
    assert parse_feature_directory_name(name) is None


def test_kind_and_feature_of_a_work_item_come_from_its_id() -> None:
    assert is_acceptance("F0001-A0001")
    assert not is_acceptance("F0001-S0001")
    assert feature_of("F0002-S0003") == "F0002"
    assert feature_of("F0002-A0001") == "F0002"


@pytest.mark.parametrize("function", [is_acceptance, feature_of, work_item_order, branch_name])
@pytest.mark.parametrize("text", ["F0001", "F0001-X0001", ""])
def test_functions_on_a_work_item_id_refuse_a_malformed_id(
    function: Callable[[str], object], text: str
) -> None:
    with pytest.raises(ValueError, match=r"."):
        function(text)


def test_acceptance_sorts_after_the_stories_of_its_feature_whatever_the_slug() -> None:
    names = ["F0002-A0001.md", "F0002-S0002-2fa.md", "F0002-S0001.md", "F0001-S0010-x.md"]
    parsed = [parse_work_item_file_name(name) for name in names]
    ids = [item.id for item in parsed if item is not None]

    assert sorted(ids) == ["F0001-S0010", "F0002-A0001", "F0002-S0001", "F0002-S0002"]
    assert sorted(ids, key=work_item_order) == [
        "F0001-S0010",
        "F0002-S0001",
        "F0002-S0002",
        "F0002-A0001",
    ]


@pytest.mark.parametrize(
    ("earlier", "later"),
    [
        ("F0001-S0009", "F0001-S0010"),
        ("F0001-S0010", "F0002-S0001"),
        ("F0001-A0001", "F0002-S0001"),
    ],
)
def test_work_item_order_keeps_string_order_within_a_kind_and_across_features(
    earlier: str, later: str
) -> None:
    assert work_item_order(earlier) < work_item_order(later)
    assert sorted([later, earlier], key=work_item_order) == [earlier, later]


def test_branch_name_is_the_prefix_and_the_id() -> None:
    assert branch_name("F0002-S0001") == "work-item/F0002-S0001"
    assert work_item_of_branch("work-item/F0002-S0001") == "F0002-S0001"


@pytest.mark.parametrize(
    "branch",
    ["main", "work-item/", "work-item/F0002", "work-item/F0002-S0001-slug", "ticket/F0002-S0001"],
)
def test_branch_that_is_not_a_work_item_branch_has_no_work_item(branch: str) -> None:
    assert work_item_of_branch(branch) is None
