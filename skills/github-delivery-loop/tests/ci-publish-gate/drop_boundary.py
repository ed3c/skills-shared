#!/usr/bin/env python3
"""Remove the independently observed branch ref from a snapshot.

This is what every snapshot looked like before #70: an absent pull request read
as an absent branch, so a repeated or orphaned remote branch was byte-identical
to a genuinely unpublished one.
"""
from __future__ import annotations

import json
import pathlib
import sys

source, target = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
snapshot = json.loads(source.read_text(encoding="utf-8"))
snapshot.pop("initial_boundary", None)
target.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
