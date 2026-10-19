import pytest

from bot.core.status.formatter import StatusTextFormatter


def test_playlist_announcement_counts_videos() -> None:
    assert 'Playlist: 4 videos queued' in StatusTextFormatter.playlist_queued(4)


@pytest.mark.parametrize(
    ('expected', 'kwargs'),
    [
        ('25%', {'downloaded_bytes': 512, 'total_bytes': 2048}),
        ('512.0B / 2.0KiB', {'downloaded_bytes': 512, 'total_bytes': 2048}),
        ('256.0B/s', {'speed': 256.0}),
        ('5:04 left', {'eta': 304}),
        ('Lesson 1', {'title': 'Lesson 1'}),
    ],
)
def test_download_text_contains(expected: str, kwargs: dict) -> None:
    fields = {
        'title': None,
        'downloaded_bytes': None,
        'total_bytes': None,
        'speed': None,
        'eta': None,
    }
    assert expected in StatusTextFormatter.downloading(**(fields | kwargs))


def test_download_percent_never_exceeds_100() -> None:
    text = StatusTextFormatter.downloading(
        title=None, downloaded_bytes=3000, total_bytes=2048, speed=None, eta=None
    )

    assert '100%' in text


def test_upload_text_shows_percent() -> None:
    assert '50%' in StatusTextFormatter.uploading('Lesson 1', 1024, 2048)
