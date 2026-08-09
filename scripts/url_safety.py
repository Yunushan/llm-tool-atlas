#!/usr/bin/env python3
"""Shared static safety checks for catalog HTTPS source URLs."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit


SPECIAL_HOST_SUFFIXES = (
    ".localhost",
    ".local",
    ".internal",
    ".home.arpa",
    ".test",
    ".invalid",
)


def static_https_url_error(value: str) -> str | None:
    """Return a stable explanation when an HTTPS URL is statically unsafe."""

    if (
        not value
        or value != value.strip()
        or any(
            character.isspace()
            or ord(character) < 32
            or character in "<>\\"
            for character in value
        )
    ):
        return (
            "source URL must not contain whitespace, control characters, "
            "backslashes, or angle brackets"
        )

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        return f"invalid source URL: {exc}"

    if (
        parsed.scheme != "https"
        or not value.startswith("https://")
        or not parsed.netloc
        or hostname is None
    ):
        return "source URL must be absolute HTTPS"
    if parsed.username is not None or parsed.password is not None:
        return "source URL must not contain credentials"
    if port not in {None, 443}:
        return "source URL may only use the default HTTPS port 443"

    host = hostname.casefold().rstrip(".")
    if not host or "%" in host:
        return "source URL hostname is invalid"
    if host == "localhost" or host.endswith(SPECIAL_HOST_SUFFIXES):
        return (
            "source URL must not target localhost or another local or "
            "special-use hostname"
        )

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # Some clients interpret these legacy numeric forms as IP literals.
        if re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|[0-9.]+)", host):
            return "source URL contains a non-canonical IP literal"
        try:
            ascii_host = host.encode("idna").decode("ascii")
        except UnicodeError:
            return "source URL hostname is not valid IDNA"
        if "." not in ascii_host or any(not label for label in ascii_host.split(".")):
            return "source URL hostname must be fully qualified"
        if len(ascii_host) > 253 or any(
            len(label) > 63 for label in ascii_host.split(".")
        ):
            return "source URL hostname is too long"
    else:
        if (
            not address.is_global
            or address.is_private
            or address.is_reserved
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_unspecified
        ):
            return "source URL must not target a private or reserved IP literal"

    return None
