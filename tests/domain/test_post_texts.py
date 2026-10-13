"""The texts the factory writes on the hosting service."""

from factory.domain.post_texts import opened_for_stop_description


def test_the_description_of_a_pull_request_opened_for_a_stop_names_the_work_item() -> None:
    assert opened_for_stop_description("F0001-S0001") == (
        "The factory opened this draft pull request to report a stop on F0001-S0001."
        " The stop is the comment below."
    )
