"""Application-level providers for Composition Root examples.

This module intentionally keeps function names and behavior minimal. Use get_container() from bootstrap to obtain providers.
"""

from bootstrap import get_container


def get_application_provider():
    c = get_container()
    return c.applications
