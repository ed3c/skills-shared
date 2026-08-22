"""The other half of the subject: a definition referenced from pricing.py.

A cross-file reference is what makes the index worth decoding. A single-file
subject would let a nesting heuristic look like resolution, because everything
it needed would already be in one document.
"""


class Client:
    def query(self, amount):
        return [amount, amount * 2]
