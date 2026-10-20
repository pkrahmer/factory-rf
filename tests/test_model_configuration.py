"""Every Pydantic model under src/factory is frozen and refuses unknown keys."""

import importlib
import inspect
import pkgutil

import pytest
from pydantic import BaseModel, ConfigDict

import factory

EXCEPTIONS = [
    "factory.adapters.claude_runtime._Usage",
    "factory.adapters.claude_runtime._Denial",
    "factory.adapters.claude_runtime._StructuredOutput",
    "factory.adapters.claude_runtime._Reply",
    "factory.adapters.opencode_runtime._Event",
    "factory.adapters.opencode_runtime._Part",
    "factory.adapters.opencode_runtime._Tokens",
    "factory.adapters.opencode_runtime._CacheTokens",
    "factory.adapters.opencode_runtime._ToolState",
    "factory.adapters.opencode_runtime._Span",
    "factory.adapters.opencode_runtime._Error",
    "factory.adapters.opencode_runtime._ErrorData",
]


def _collect() -> dict[str, type[BaseModel]]:
    models: dict[str, type[BaseModel]] = {}
    for module_info in pkgutil.walk_packages(factory.__path__, prefix="factory."):
        module = importlib.import_module(module_info.name)
        for name, value in inspect.getmembers(module, inspect.isclass):
            if issubclass(value, BaseModel) and value.__module__ == module.__name__:
                models[f"{module.__name__}.{name}"] = value
    return models


MODELS = _collect()


def closed_fault(model: type[BaseModel]) -> str | None:
    """Return None for a frozen model that forbids unknown keys, else what it lacks."""
    missing = [
        setting
        for setting, wanted in (("frozen", True), ("extra", "forbid"))
        if model.model_config.get(setting) != wanted
    ]
    if not missing:
        return None
    return f"{model.__qualname__} lacks {' and '.join(missing)}"


class _Closed(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class _FrozenOnly(BaseModel):
    model_config = ConfigDict(frozen=True)


class _ForbidOnly(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _FrozenIgnoring(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")


class _ThawedForbidding(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")


class _Unconfigured(BaseModel):
    pass


@pytest.mark.parametrize(
    ("model", "missing"),
    [
        pytest.param(_Closed, [], id="closed"),
        pytest.param(_FrozenOnly, ["extra"], id="frozen-only"),
        pytest.param(_ForbidOnly, ["frozen"], id="forbid-only"),
        pytest.param(_FrozenIgnoring, ["extra"], id="frozen-ignore"),
        pytest.param(_ThawedForbidding, ["frozen"], id="not-frozen-forbid"),
        pytest.param(_Unconfigured, ["frozen", "extra"], id="no-config"),
    ],
)
def test_the_rule_names_the_model_and_each_missing_setting(
    model: type[BaseModel], missing: list[str]
) -> None:
    fault = closed_fault(model)

    if not missing:
        assert fault is None
    else:
        assert fault is not None
        assert model.__name__ in fault
        for setting in missing:
            assert setting in fault


@pytest.mark.parametrize("name", [name for name in MODELS if name not in EXCEPTIONS], ids=str)
def test_every_model_is_frozen_and_forbids_unknown_keys(name: str) -> None:
    assert closed_fault(MODELS[name]) is None


def test_the_collection_finds_every_model_and_nothing_else() -> None:
    assert len(MODELS) > 90
    assert "factory.domain.work_item.WorkItemState" in MODELS
    assert "factory.application.stage.StartedStage" in MODELS
    assert "factory.adapters.claude_runtime._Reply" in MODELS
    assert "factory.application.boundaries.Boundaries" not in MODELS
    assert all(issubclass(model, BaseModel) for model in MODELS.values())


@pytest.mark.parametrize("name", EXCEPTIONS)
def test_each_exception_is_a_model_that_ignores_unknown_keys(name: str) -> None:
    assert name in MODELS
    assert MODELS[name].model_config.get("extra") == "ignore"
