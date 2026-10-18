import pytest
from pytest_mock import MockerFixture
from yt_dlp.utils import DownloadError

from worker.core.playlist_expander import PlaylistExpander

PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PL123'
FIRST_VIDEO_URL = 'https://www.youtube.com/watch?v=aaaaaaaaaaa'
SECOND_VIDEO_URL = 'https://www.youtube.com/watch?v=bbbbbbbbbbb'


@pytest.fixture
def expander() -> PlaylistExpander:
    return PlaylistExpander()


def _stub_flat_info(
    mocker: MockerFixture, expander: PlaylistExpander, meta: dict | None
) -> None:
    mocker.patch.object(expander, '_extract_unprocessed_info', return_value=meta)


def test_playlist_returns_entry_urls(
    mocker: MockerFixture, expander: PlaylistExpander
) -> None:
    meta = {
        '_type': 'playlist',
        'entries': [{'url': FIRST_VIDEO_URL}, {'url': SECOND_VIDEO_URL}],
    }
    _stub_flat_info(mocker, expander, meta)

    assert expander.expand(PLAYLIST_URL) == [FIRST_VIDEO_URL, SECOND_VIDEO_URL]


def test_entries_without_url_are_skipped(
    mocker: MockerFixture, expander: PlaylistExpander
) -> None:
    meta = {'_type': 'playlist', 'entries': [None, {}, {'url': FIRST_VIDEO_URL}]}
    _stub_flat_info(mocker, expander, meta)

    assert expander.expand(PLAYLIST_URL) == [FIRST_VIDEO_URL]


@pytest.mark.parametrize(
    'meta',
    [None, {'_type': 'video', 'url': FIRST_VIDEO_URL}, {'title': 'no type'}],
)
def test_non_playlist_returns_empty(
    mocker: MockerFixture, expander: PlaylistExpander, meta: dict | None
) -> None:
    _stub_flat_info(mocker, expander, meta)

    assert expander.expand(PLAYLIST_URL) == []


def test_extraction_error_returns_empty(
    mocker: MockerFixture, expander: PlaylistExpander
) -> None:
    mocker.patch.object(
        expander, '_extract_unprocessed_info', side_effect=DownloadError('boom')
    )

    assert expander.expand(PLAYLIST_URL) == []


def test_options_use_flat_extraction(expander: PlaylistExpander) -> None:
    assert expander._ytdl_opts['extract_flat'] == 'in_playlist'


def test_entries_are_capped_at_max_items(mocker: MockerFixture) -> None:
    expander = PlaylistExpander(max_items=1)
    meta = {
        '_type': 'playlist',
        'entries': iter([{'url': FIRST_VIDEO_URL}, {'url': SECOND_VIDEO_URL}]),
    }
    _stub_flat_info(mocker, expander, meta)

    assert expander.expand(PLAYLIST_URL) == [FIRST_VIDEO_URL]


def test_options_skip_ambiguous_playlist_links(expander: PlaylistExpander) -> None:
    assert expander._ytdl_opts['noplaylist'] is True


def test_single_video_url_returns_empty(
    mocker: MockerFixture, expander: PlaylistExpander
) -> None:
    mocker.patch.object(expander, '_extract_unprocessed_info')

    assert expander.expand(FIRST_VIDEO_URL) == []


def test_single_video_url_skips_extraction(
    mocker: MockerFixture, expander: PlaylistExpander
) -> None:
    extract = mocker.patch.object(expander, '_extract_unprocessed_info')
    expander.expand(FIRST_VIDEO_URL)

    extract.assert_not_called()


@pytest.mark.parametrize(
    'url',
    [
        PLAYLIST_URL,
        'https://www.youtube.com/@somechannel',
        'https://www.youtube.com/watch?v=aaaaaaaaaaa&list=PL123',
    ],
)
def test_possible_playlist_url_is_inspected(
    mocker: MockerFixture, expander: PlaylistExpander, url: str
) -> None:
    extract = mocker.patch.object(
        expander, '_extract_unprocessed_info', return_value=None
    )
    expander.expand(url)

    extract.assert_called_once_with(url)


def test_options_enable_node_runtime(expander: PlaylistExpander) -> None:
    assert 'node' in expander._ytdl_opts['js_runtimes']
