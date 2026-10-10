"""MessWise - AI food-operations intelligence for institutional kitchens.

Predict -> Plan -> Cook -> Measure -> Learn
"""

from messwise.db import get_data_environment_summary

__version__ = "0.1.0"

__all__ = [
    "get_data_environment_summary",
    "__version__",
]
