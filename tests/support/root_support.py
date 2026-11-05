"""The mark for tests that need a folder root could still write in."""

import os

import pytest

AS_ROOT = pytest.mark.skipif(
    os.geteuid() == 0, reason="root removes files in unwritable directories"
)
