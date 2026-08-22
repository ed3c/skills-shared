"""Definitions the indexer resolves: a module function, a class, a method."""


def surcharge(amount):
    """A module-level function referenced from another module in this package."""
    return amount + 1


class Pricing:
    """A class whose method calls a module-level function in the same file."""

    def __init__(self, base):
        self.base = base

    def apply(self, amount):
        return surcharge(self.base + amount)
