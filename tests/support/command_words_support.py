"""Reading the words of a command line that tests take apart."""


def value_after(words: list[str], option: str) -> str:
    """The word that follows `option` in `words`: the option's value."""
    return words[words.index(option) + 1]
