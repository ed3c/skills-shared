#!/usr/bin/env python3
"""Credential-free Git remote URL parsing shared by private-lineage tools."""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

GITHUB_HOSTS = {
    "github.com",
    "api.github.com",
    "raw.githubusercontent.com",
    "objects.githubusercontent.com",
}


@dataclass(frozen=True)
class RemoteURL:
    raw: str
    host: str
    has_http_credentials: bool
    relative: bool


def parse(value: str) -> RemoteURL:
    raw = value.strip()
    if not raw:
        return RemoteURL(raw, "", False, False)
    if raw.startswith(("./", "../", "/")):
        return RemoteURL(raw, "", False, True)
    if "://" in raw:
        parsed = urlsplit(raw)
        return RemoteURL(
            raw,
            (parsed.hostname or "").lower(),
            parsed.scheme in {"http", "https"} and (parsed.username is not None or parsed.password is not None),
            False,
        )
    match = re.match(r"^(?:[^@/\s]+@)?([^:/\s]+):.+$", raw)
    return RemoteURL(raw, (match.group(1) if match else "").lower(), False, False)


def is_github(host: str) -> bool:
    lowered = host.lower()
    return lowered in GITHUB_HOSTS or lowered.endswith(".github.com") or lowered.endswith(
        ".githubusercontent.com"
    )
