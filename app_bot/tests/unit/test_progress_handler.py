import pytest
from yt_shared.enums import ProgressStage
from yt_shared.schemas.progress import DownloadProgressPayload

from bot.core.handlers.progress import DownloadProgressHandler
from tests.unit.constants import CHAT_ID, MESSAGE_ID

VIDEO_URL = 'https://www.youtube.com/watch?v=aaaaaaaaaaa'


def _payload(**overrides: object) -> DownloadProgressPayload:
    fields: dict[str, object] = {
        'stage': ProgressStage.DOWNLOADING,
        'from_chat_id': CHAT_ID,
        'message_id': MESSAGE_ID,
        'url': VIDEO_URL,
        'title': 'Lesson 1',
        'downloaded_bytes': 512,
        'total_bytes': 2048,
    }
    return DownloadProgressPayload(**(fields | overrides))


async def test_download_progress_updates_status(bot: object) -> None:
    await DownloadProgressHandler(body=_payload(), bot=bot).handle()

    key, text = bot.status.show.await_args.kwargs.values()
    assert (key, '25%' in text) == ((CHAT_ID, MESSAGE_ID, VIDEO_URL), True)


async def test_playlist_is_announced_once(bot: object) -> None:
    payload = _payload(stage=ProgressStage.PLAYLIST_QUEUED, entry_count=4)
    await DownloadProgressHandler(body=payload, bot=bot).handle()

    assert '4 videos' in bot.send_message.await_args.kwargs['text']


async def test_silent_user_gets_no_status(bot: object, receiving_user: object) -> None:
    receiving_user.upload.silent = True
    await DownloadProgressHandler(body=_payload(), bot=bot).handle()

    bot.status.show.assert_not_awaited()


async def test_unknown_chat_gets_no_status(bot: object) -> None:
    await DownloadProgressHandler(body=_payload(from_chat_id=999), bot=bot).handle()

    bot.status.show.assert_not_awaited()


@pytest.mark.usefixtures('bot')
async def test_progress_payload_round_trips_through_json() -> None:
    payload = _payload(speed=1.5, eta=3)

    assert DownloadProgressPayload.model_validate_json(payload.model_dump_json()) == (
        payload
    )
