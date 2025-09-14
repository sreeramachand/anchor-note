"""anchor_note package root"""

__version__ = "0.1.0"

# Expose key top-level conveniences for consumers
from .core import scheduler as scheduler  # noqa: E402,F401
from .core import checklist as checklist  # noqa: E402,F401
from .core import alerts as alerts        # noqa: E402,F401
from .core import calendar_sync as calendar_sync  # noqa: E402,F401
