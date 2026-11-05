"""Time limits for tests whose child must act before the limit ends it."""

from datetime import timedelta
from typing import Final

# Under `make check` pytest runs on every core; on 2026-10-19 a stand-in started through
# `factory-confine` needed more than three seconds to write its first record.
ROOMY_LIMIT: Final[timedelta] = timedelta(seconds=10)
# An upper bound on a run that ROOMY_LIMIT ends, with room above it; a stand-in the limit must
# end waits longer, so a missed kill fails.
ROOMY_BOUND_SECONDS: Final[int] = 25
