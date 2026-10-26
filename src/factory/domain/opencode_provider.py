"""The opencode provider file: one OpenAI-compatible provider, its rules and its configuration."""

import re
from typing import Self
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeFloat,
    PositiveInt,
    ValidationError,
    field_validator,
    model_validator,
)

PROVIDER_PACKAGE = "@ai-sdk/openai-compatible"

_ID = re.compile(r"[a-z][a-z0-9-]*")
_ENVIRONMENT_NAME = re.compile(r"[A-Z_][A-Z0-9_]*")
_URL_SCHEMES = ("http", "https")


class OpencodeModel(BaseModel):
    """One model of the provider: its limits and its prices, all optional."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str | None = None
    context: PositiveInt | None = None
    output: PositiveInt | None = None
    # Dollars per million tokens.
    input_cost: NonNegativeFloat | None = None
    output_cost: NonNegativeFloat | None = None

    @model_validator(mode="after")
    def _pairs_whole(self) -> Self:
        if (self.context is None) != (self.output is None):
            raise ValueError("context and output are given together or not at all")
        if (self.input_cost is None) != (self.output_cost is None):
            raise ValueError("input_cost and output_cost are given together or not at all")
        return self


class OpencodeProvider(BaseModel):
    """The provider file: one OpenAI-compatible provider and the small model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    base_url: str
    api_key_env: str
    models: dict[str, OpencodeModel]
    small_model: str

    @field_validator("id")
    @classmethod
    def _id_named(cls, value: str) -> str:
        if _ID.fullmatch(value) is None:
            raise ValueError("is not a provider id of the form [a-z][a-z0-9-]*")
        return value

    @field_validator("base_url")
    @classmethod
    def _url_with_host(cls, value: str) -> str:
        parts = urlsplit(value)
        if parts.scheme not in _URL_SCHEMES or not parts.hostname:
            raise ValueError("is not an http:// or https:// URL with a host")
        return value

    @field_validator("api_key_env")
    @classmethod
    def _environment_name(cls, value: str) -> str:
        if _ENVIRONMENT_NAME.fullmatch(value) is None:
            raise ValueError("is not an environment variable name")
        return value

    @field_validator("models")
    @classmethod
    def _models_named(cls, value: dict[str, OpencodeModel]) -> dict[str, OpencodeModel]:
        if not value:
            raise ValueError("holds no model")
        if any(not key.strip() for key in value):
            raise ValueError("holds a blank model name")
        return value

    @model_validator(mode="after")
    def _small_model_known(self) -> Self:
        provider, _, model = self.small_model.partition("/")
        if provider != self.id or model not in self.models:
            raise ValueError(f"small_model {self.small_model} is not {self.id}/<one of models>")
        return self


def read_provider(text: str) -> OpencodeProvider:
    """The provider of the JSON `text`; a fault is a `ValueError` that names the first one."""
    try:
        return OpencodeProvider.model_validate_json(text)
    except ValidationError as exc:
        first = exc.errors()[0]
        place = ".".join(str(part) for part in first["loc"]) or "the file"
        raise ValueError(f"{place}: {first['msg']}") from exc


def provider_configuration(provider: OpencodeProvider) -> dict[str, object]:
    """The `provider` and `small_model` keys of opencode's configuration for `provider`."""
    return {
        "provider": {
            provider.id: {
                "npm": PROVIDER_PACKAGE,
                "options": {
                    "baseURL": provider.base_url,
                    "apiKey": f"{{env:{provider.api_key_env}}}",
                },
                "models": {key: _model_entry(model) for key, model in provider.models.items()},
            }
        },
        "small_model": provider.small_model,
    }


def _model_entry(model: OpencodeModel) -> dict[str, object]:
    entry: dict[str, object] = {}
    if model.name is not None:
        entry["name"] = model.name
    if model.context is not None and model.output is not None:
        entry["limit"] = {"context": model.context, "output": model.output}
    if model.input_cost is not None and model.output_cost is not None:
        entry["cost"] = {"input": model.input_cost, "output": model.output_cost}
    return entry
