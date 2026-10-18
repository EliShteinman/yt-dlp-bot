"""Tests for the shared input validators (SSRF + path-traversal guards)."""

import pytest
from pydantic import TypeAdapter, ValidationError
from yt_shared.schemas.validators import PublicHttpUrl, SafeFilename

_url_adapter = TypeAdapter(PublicHttpUrl)
_filename_adapter = TypeAdapter(SafeFilename)


@pytest.mark.parametrize(
    'url',
    [
        'https://www.youtube.com/watch?v=abc',
        'http://vimeo.com/12345',
        'https://sub.example.co.uk/path?a=1&b=2',
    ],
)
def test_public_url_accepts_public_http(url: str) -> None:
    assert _url_adapter.validate_python(url) == url


@pytest.mark.parametrize(
    'url',
    [
        'ftp://example.com/x',            # non-http scheme
        'file:///etc/passwd',             # file scheme
        'http://localhost/admin',         # loopback hostname
        'http://127.0.0.1:5432/',         # loopback IP
        'http://169.254.169.254/latest',  # link-local (cloud metadata)
        'http://10.0.0.5/internal',       # private range
        'http://[::1]/',                  # ipv6 loopback
        'not-a-url',                      # no scheme/host
    ],
)
def test_public_url_rejects_non_public(url: str) -> None:
    with pytest.raises(ValidationError):
        _url_adapter.validate_python(url)


@pytest.mark.parametrize(
    'name',
    ['video.mp4', 'My Cool Clip.mkv', '$(id).mp4', 'a b; c.mp4'],
)
def test_safe_filename_accepts_plain_names(name: str) -> None:
    # Shell metachars are allowed as a *name* (exec makes them inert); only
    # path separators / traversal are rejected here.
    assert _filename_adapter.validate_python(name) == name


@pytest.mark.parametrize(
    'name',
    ['../../etc/passwd', 'a/b.mp4', '..', '.', '', 'x\\y.mp4', 'null\x00.mp4'],
)
def test_safe_filename_rejects_traversal(name: str) -> None:
    with pytest.raises(ValidationError):
        _filename_adapter.validate_python(name)
