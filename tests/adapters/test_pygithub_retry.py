"""The PyGithub client retries with a backoff, writes included."""

from urllib3.util.retry import Retry

from factory.adapters.pygithub_hosting import pygithub_service


def test_the_hosting_client_retries_five_times_with_a_backoff_and_covers_patch() -> None:
    service = pygithub_service("owner/name", "example-value")

    repository = vars(service)["_repository"]
    retry = vars(repository.requester)["_Requester__retry"]

    assert isinstance(retry, Retry)
    assert retry.total == 5
    assert retry.backoff_factor == 2
    assert retry.allowed_methods is not None
    assert set(retry.allowed_methods) >= {*Retry.DEFAULT_ALLOWED_METHODS, "PATCH"}
