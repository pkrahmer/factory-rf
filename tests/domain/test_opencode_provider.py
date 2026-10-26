"""The opencode provider file: its rules and the configuration keys it gives."""

import json

import pytest

from factory.domain.opencode_provider import (
    OpencodeModel,
    OpencodeProvider,
    provider_configuration,
    read_provider,
)
from opencode_provider_support import CONFIGURATION, KEY_ENV, PROVIDER

LOWER_KEY_ENV = "lower"
DIGIT_FIRST_KEY_ENV = "1KEY"

MINIMAL: dict[str, object] = {
    "id": "corp",
    "base_url": "https://example.invalid/v1",
    "api_key_env": KEY_ENV,
    "models": {"m": {}},
    "small_model": "corp/m",
}


def _text(**changes: object) -> str:
    return json.dumps({**MINIMAL, **changes})


def _model(**fields: object) -> str:
    return _text(models={"m": fields})


@pytest.mark.parametrize(
    ("text", "fault"),
    [
        pytest.param(json.dumps(PROVIDER), None, id="complete"),
        pytest.param(_text(), None, id="minimal"),
        pytest.param(_text(id="Corp", small_model="Corp/m"), "id", id="id-upper"),
        pytest.param(_text(id="1corp", small_model="1corp/m"), "id", id="id-digit-first"),
        pytest.param(_text(id="corp-1", small_model="corp-1/m"), None, id="id-dash-digit"),
        pytest.param(_text(models={}), "models", id="models-empty"),
        pytest.param(_text(models={"m": {}, " ": {}}), "models", id="model-key-blank"),
        pytest.param(_text(base_url="ftp://x"), "base_url", id="base-url-ftp"),
        pytest.param(_text(base_url="https://"), "base_url", id="base-url-no-host"),
        pytest.param(_text(base_url="example.invalid"), "base_url", id="base-url-no-scheme"),
        pytest.param(_text(base_url="https://example.invalid/v1/"), None, id="base-url-slash"),
        pytest.param(_text(base_url="http://example.invalid"), None, id="base-url-http"),
        pytest.param(_text(api_key_env=LOWER_KEY_ENV), "api_key_env", id="key-env-lower"),
        pytest.param(
            _text(api_key_env=DIGIT_FIRST_KEY_ENV), "api_key_env", id="key-env-digit-first"
        ),
        pytest.param(_text(small_model="other/m"), "small_model", id="small-other-provider"),
        pytest.param(_text(small_model="corp"), "small_model", id="small-no-model"),
        pytest.param(_text(small_model="corp/missing"), "small_model", id="small-missing-model"),
        pytest.param(_model(input_cost=1.0), "input_cost", id="input-cost-alone"),
        pytest.param(_model(output_cost=1.0), "output_cost", id="output-cost-alone"),
        pytest.param(_model(context=10), "context", id="context-alone"),
        pytest.param(_model(output=10), "output", id="output-alone"),
        pytest.param(_model(input_cost=-0.01, output_cost=1.0), "input_cost", id="cost-negative"),
        pytest.param(_model(input_cost=0, output_cost=0), None, id="cost-zero"),
        pytest.param(
            _model(input_cost=1.0, output_cost=-0.01), "output_cost", id="output-cost-negative"
        ),
        pytest.param(_model(context=0, output=1), "context", id="context-zero"),
        pytest.param(_model(context=1, output=1), None, id="context-one"),
        pytest.param(_model(context=1, output=0), "output", id="output-zero"),
        pytest.param(_text(extra=1), "extra", id="unknown-top-key"),
        pytest.param(_model(extra=1), "extra", id="unknown-model-key"),
        pytest.param("[]", "", id="not-an-object"),
    ],
)
def test_the_provider_file_is_accepted_only_when_it_keeps_every_rule(
    text: str, fault: str | None
) -> None:
    if fault is None:
        provider = read_provider(text)
        assert isinstance(provider, OpencodeProvider)
    else:
        # The word boundaries keep "output" from matching inside "output_cost".
        with pytest.raises(ValueError, match=rf"\b{fault}\b" if fault else r"."):
            read_provider(text)


def test_a_complete_provider_gives_the_provider_and_the_small_model() -> None:
    assert provider_configuration(read_provider(json.dumps(PROVIDER))) == CONFIGURATION


@pytest.mark.parametrize(
    ("model", "base_url", "entry"),
    [
        pytest.param(OpencodeModel(), "https://example.invalid/v1", {}, id="none"),
        pytest.param(
            OpencodeModel(name="M"), "https://example.invalid/v1", {"name": "M"}, id="name-only"
        ),
        pytest.param(
            OpencodeModel(context=1000, output=100),
            "https://example.invalid/v1",
            {"limit": {"context": 1000, "output": 100}},
            id="limits-only",
        ),
        pytest.param(
            OpencodeModel(input_cost=3.0, output_cost=15.0),
            "https://example.invalid/v1",
            {"cost": {"input": 3.0, "output": 15.0}},
            id="prices-only",
        ),
        pytest.param(OpencodeModel(), "https://example.invalid/v1/", {}, id="trailing-slash"),
    ],
)
def test_each_model_holds_only_the_groups_it_was_given(
    model: OpencodeModel, base_url: str, entry: dict[str, object]
) -> None:
    provider = OpencodeProvider(
        id="corp",
        base_url=base_url,
        api_key_env=KEY_ENV,
        models={"m": model},
        small_model="corp/m",
    )

    assert provider_configuration(provider) == {
        "provider": {
            "corp": {
                "npm": "@ai-sdk/openai-compatible",
                "options": {"baseURL": base_url, "apiKey": "{env:PROXY_KEY}"},
                "models": {"m": entry},
            }
        },
        "small_model": "corp/m",
    }
