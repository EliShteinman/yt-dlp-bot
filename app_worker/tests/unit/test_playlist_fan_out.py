import pytest
from pytest_mock import MockerFixture
from yt_shared.enums import DownMediaType, TaskSource, TelegramChatType
from yt_shared.schemas.media import InbMediaPayload

from worker.core.playlist_fan_out import PlaylistFanOut

PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PL123'
ENTRY_URLS = [
    'https://www.youtube.com/watch?v=aaa',
    'https://www.youtube.com/watch?v=bbb',
]


@pytest.fixture
def media_payload() -> InbMediaPayload:
    return InbMediaPayload(
        from_chat_id=1,
        from_chat_type=TelegramChatType.PRIVATE,
        from_user_id=1,
        message_id=10,
        ack_message_id=11,
        url=PLAYLIST_URL,
        original_url=PLAYLIST_URL,
        source=TaskSource.BOT,
        save_to_storage=False,
        download_media_type=DownMediaType.VIDEO,
        custom_filename='custom.mp4',
        automatic_extension=False,
    )


@pytest.fixture
def expander(mocker: MockerFixture) -> object:
    return mocker.Mock(expand=mocker.Mock(return_value=ENTRY_URLS))


@pytest.fixture
def publisher(mocker: MockerFixture) -> object:
    return mocker.Mock(send_for_download=mocker.AsyncMock(return_value=True))


@pytest.fixture
def fan_out(expander: object, publisher: object) -> PlaylistFanOut:
    return PlaylistFanOut(expander=expander, publisher=publisher)


def _published_payloads(publisher: object) -> list[InbMediaPayload]:
    return [call.args[0] for call in publisher.send_for_download.await_args_list]


async def test_playlist_is_fanned_out(
    fan_out: PlaylistFanOut, media_payload: InbMediaPayload
) -> None:
    assert await fan_out.try_fan_out(media_payload) is True


async def test_publishes_one_task_per_entry(
    fan_out: PlaylistFanOut, media_payload: InbMediaPayload, publisher: object
) -> None:
    await fan_out.try_fan_out(media_payload)

    assert [p.url for p in _published_payloads(publisher)] == ENTRY_URLS


async def test_entry_original_url_is_entry_url(
    fan_out: PlaylistFanOut, media_payload: InbMediaPayload, publisher: object
) -> None:
    await fan_out.try_fan_out(media_payload)

    assert [p.original_url for p in _published_payloads(publisher)] == ENTRY_URLS


async def test_entry_drops_custom_filename(
    fan_out: PlaylistFanOut, media_payload: InbMediaPayload, publisher: object
) -> None:
    await fan_out.try_fan_out(media_payload)

    assert {p.custom_filename for p in _published_payloads(publisher)} == {None}


async def test_entry_keeps_chat_context(
    fan_out: PlaylistFanOut, media_payload: InbMediaPayload, publisher: object
) -> None:
    await fan_out.try_fan_out(media_payload)

    assert {p.ack_message_id for p in _published_payloads(publisher)} == {11}


async def test_non_playlist_is_not_fanned_out(
    fan_out: PlaylistFanOut,
    media_payload: InbMediaPayload,
    expander: object,
) -> None:
    expander.expand.return_value = []

    assert await fan_out.try_fan_out(media_payload) is False


async def test_non_playlist_publishes_nothing(
    fan_out: PlaylistFanOut,
    media_payload: InbMediaPayload,
    expander: object,
    publisher: object,
) -> None:
    expander.expand.return_value = []
    await fan_out.try_fan_out(media_payload)

    publisher.send_for_download.assert_not_awaited()


async def test_unsent_entry_is_logged_as_error(
    fan_out: PlaylistFanOut,
    media_payload: InbMediaPayload,
    publisher: object,
    caplog: pytest.LogCaptureFixture,
) -> None:
    publisher.send_for_download.return_value = False
    await fan_out.try_fan_out(media_payload)

    assert 'Failed to queue playlist entry' in caplog.text
