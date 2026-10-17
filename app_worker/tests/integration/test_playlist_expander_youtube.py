import pytest

from worker.core.playlist_expander import PlaylistExpander

pytestmark = pytest.mark.network

NO_COOKIES_EXPAND_OPTS = ('--flat-playlist', '--no-playlist', '--quiet')
PLAIN_VIDEO_URL = 'https://www.youtube.com/watch?v=V1bFr2SWP1I'
YOUTUBE_PLAYLIST_URL = (
    'https://www.youtube.com/playlist?list=PL05afllilgWXXWuZA-Bmcz2OXcsef-Xoy'
)
YOUTUBE_VIDEO_IN_PLAYLIST_URL = 'https://www.youtube.com/watch?v=V1bFr2SWP1I&list=PL05afllilgWXXWuZA-Bmcz2OXcsef-Xoy'


@pytest.fixture(scope='module')
def expander() -> PlaylistExpander:
    return PlaylistExpander(cli_opts=NO_COOKIES_EXPAND_OPTS, max_items=3)


def test_real_playlist_expands_to_watch_urls(expander: PlaylistExpander) -> None:
    entry_urls = expander.expand(YOUTUBE_PLAYLIST_URL)

    assert len(entry_urls) == 3
    assert all('watch?v=' in url for url in entry_urls)


def test_video_inside_playlist_is_not_expanded(expander: PlaylistExpander) -> None:
    assert expander.expand(YOUTUBE_VIDEO_IN_PLAYLIST_URL) == []


def test_plain_video_is_not_expanded(expander: PlaylistExpander) -> None:
    assert expander.expand(PLAIN_VIDEO_URL) == []
