"""The list of folders that must have a README leaves out the operator's template."""

from factory.shared.domain.folder_readmes import FOLDER_READMES

LISTED = 22
TEMPLATE_README = "operator/template/README.md"


def test_the_folder_readme_list_leaves_out_the_template_folder() -> None:
    assert (len(FOLDER_READMES), TEMPLATE_README in FOLDER_READMES) == (LISTED, False)
