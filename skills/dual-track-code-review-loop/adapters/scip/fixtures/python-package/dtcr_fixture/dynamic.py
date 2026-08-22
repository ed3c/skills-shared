"""The ceiling, written as code.

`getattr` dispatch is a call at runtime and nothing at index time: no static
indexer emits an edge from `dispatch` to `Pricing.apply`, and an importer that
reported this file as fully covered would be reporting the absence of an edge as
the absence of a call. The adapter counts this file in its denominator and names
the construct in its omissions rather than leaving the gap invisible.
"""

from dtcr_fixture.core import Pricing


def dispatch(name, base, amount):
    return getattr(Pricing(base), name)(amount)
