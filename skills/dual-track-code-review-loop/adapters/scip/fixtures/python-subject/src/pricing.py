"""Real Python, indexed for real by scip-python.

This file is the subject of the SCIP adapter's live lane. It is small on
purpose and it is not a stub: every construct here exists so one decoded fact
has something to be checked against.

    format_total        a module-level function, defined and then referenced
                        from inside another definition's range -- the only
                        shape from which this adapter derives an edge, and the
                        reason that edge is a lower bound rather than a call
                        graph.
    Pricing.apply       calls a method on a value whose type the indexer has to
                        resolve across a file boundary.
    json.dumps          a symbol defined outside this project. Whether the
                        indexer resolves it is the indexer's property, not this
                        file's, and either way it belongs in the denominator.
    _widen              never called from anywhere in this subject, so the
                        absence of an edge into it is a fact about this subject
                        rather than about the indexer.
"""
import json

from client import Client


def format_total(amount):
    return json.dumps({"total": amount})


def _widen(rows):
    return [row * 2 for row in rows]


class Pricing:
    def __init__(self, client: Client):
        self.client = client

    def apply(self, amount):
        rows = self.client.query(amount)
        return format_total(sum(rows))
