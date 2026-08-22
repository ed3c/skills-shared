"""Fixture package indexed by scip-python so the adapter has real provider bytes.

This package exists to be indexed, not to be imported by anything in this
repository. It is deliberately small enough that every symbol scip-python emits
can be read by hand, and it deliberately contains one construct the indexer
cannot resolve, so the unresolved denominator this adapter reports is a measured
number rather than a zero nobody tested.
"""
