"""Reusable Pydantic validators for untrusted external input.

Shared by the API (`CreateTaskIn`) and the bot/worker payload
(`InbMediaPayload`) so both entry points enforce the same rules.
"""

import ipaddress
from pathlib import PurePosixPath
from typing import Annotated
from urllib.parse import urlparse

from pydantic import AfterValidator

_ALLOWED_URL_SCHEMES: frozenset[str] = frozenset({'http', 'https'})
_BLOCKED_HOSTNAMES: frozenset[str] = frozenset(
    {'localhost', 'localhost.localdomain', 'ip6-localhost', 'ip6-loopback'}
)
_INVALID_FILENAMES: frozenset[str] = frozenset({'', '.', '..'})


def validate_public_http_url(value: str) -> str:
    """Allow only http(s) URLs whose host is not an internal/private address.

    Mitigates SSRF via the download URL. Literal internal IPs and known
    loopback hostnames are rejected; a public hostname that later resolves to
    a private IP is not caught here (would require resolution at fetch time).
    """
    parsed = urlparse(value)
    if parsed.scheme not in _ALLOWED_URL_SCHEMES:
        raise ValueError(f'URL scheme must be http or https, got "{parsed.scheme}"')

    host = parsed.hostname
    if not host:
        raise ValueError('URL must contain a host')
    if host.lower() in _BLOCKED_HOSTNAMES:
        raise ValueError('URL host is not allowed')

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return value

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    ):
        raise ValueError('URL host must be a public address')
    return value


def validate_safe_filename(value: str) -> str:
    """Reject filenames that could traverse out of their target directory."""
    if '\x00' in value:
        raise ValueError('Filename must not contain a NUL byte')
    if value in _INVALID_FILENAMES:
        raise ValueError('Filename is invalid')
    if value != PurePosixPath(value).name or '\\' in value:
        raise ValueError('Filename must not contain path separators')
    return value


PublicHttpUrl = Annotated[str, AfterValidator(validate_public_http_url)]
SafeFilename = Annotated[str, AfterValidator(validate_safe_filename)]
