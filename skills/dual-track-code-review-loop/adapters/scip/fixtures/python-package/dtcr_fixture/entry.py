"""Cross-file references: an import, a constructor call, two method calls."""

from dtcr_fixture.core import Pricing, surcharge


def quote(base, amount):
    return Pricing(base).apply(amount)


def flat(amount):
    return surcharge(amount)
