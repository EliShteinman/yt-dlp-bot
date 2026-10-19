"""Calls the bot makes into the Telegram library must match its real signatures.

Mocks accept any keyword, so a library upgrade that removes a parameter (as
kurigram did with Message.reply(reply_to_message_id=...)) would otherwise only
fail in production.
"""

import inspect

import pytest
from pyrogram import Client
from pyrogram.types import Message
from pytest_mock import MockerFixture
from yt_shared.enums import ProgressStage
from yt_shared.schemas.progress import DownloadProgressPayload

from bot.core.callbacks import TelegramCallback
from bot.core.handlers.error import ErrorDownloadHandler
from bot.core.handlers.progress import DownloadProgressHandler
from bot.core.status.registry import StatusMessageRegistry
from bot.core.status.updater import StatusMessageUpdater
from bot.core.tasks.upload import AudioUploadTask, VideoUploadTask
from tests.unit.constants import CHAT_ID, MESSAGE_ID


def _assert_accepted(method: object, call: object) -> None:
    inspect.signature(method).bind(None, *call.args, **call.kwargs)


@pytest.fixture
def message(mocker: MockerFixture) -> object:
    return mocker.Mock(id=MESSAGE_ID, reply=mocker.AsyncMock())


async def test_start_reply_matches_message_reply(message: object) -> None:
    await TelegramCallback.on_start(client=None, message=message)

    _assert_accepted(Message.reply, message.reply.await_args)


async def test_acknowledgment_matches_message_reply(
    mocker: MockerFixture, message: object
) -> None:
    mocker.patch('bot.core.callbacks.UrlService')
    await TelegramCallback()._send_acknowledge_message(message=message, url_count=2)

    _assert_accepted(Message.reply, message.reply.await_args)


async def test_error_message_matches_send_message(
    mocker: MockerFixture, bot: object, context: object
) -> None:
    body = mocker.Mock(
        type='DOWNLOAD_ERROR',
        task_id='task-1',
        message_id=MESSAGE_ID,
        from_chat_id=CHAT_ID,
        message='Download error',
        url=context.url,
        context=context,
        yt_dlp_version='x',
        exception_msg='boom',
        exception_type='DownloadError',
    )
    mocker.patch.dict(
        ErrorDownloadHandler._ERR_MSG_HEADER_MAP, {'DOWNLOAD_ERROR': 'Download error'}
    )
    await ErrorDownloadHandler(body=body, bot=bot)._send_error_text()

    _assert_accepted(Client.send_message, bot.send_message.await_args)


@pytest.fixture
def status_updater(mocker: MockerFixture) -> StatusMessageUpdater:
    bot = mocker.Mock(
        send_message=mocker.AsyncMock(return_value=mocker.Mock(id=99)),
        edit_message_text=mocker.AsyncMock(),
    )
    return StatusMessageUpdater(
        bot=bot,
        registry=StatusMessageRegistry(retention_seconds=600),
        edit_interval_seconds=0.0001,
    )


async def test_status_send_matches_send_message(
    status_updater: StatusMessageUpdater,
) -> None:
    await status_updater.show((CHAT_ID, MESSAGE_ID, 'url'), 'downloading')

    _assert_accepted(Client.send_message, status_updater._bot.send_message.await_args)


async def test_status_edit_matches_edit_message_text(
    status_updater: StatusMessageUpdater,
) -> None:
    key = (CHAT_ID, MESSAGE_ID, 'url')
    await status_updater.show(key, 'downloading')
    await status_updater.show(key, 'uploading', force=True)

    _assert_accepted(
        Client.edit_message_text, status_updater._bot.edit_message_text.await_args
    )


async def test_playlist_announcement_matches_send_message(bot: object) -> None:
    payload = DownloadProgressPayload(
        stage=ProgressStage.PLAYLIST_QUEUED,
        from_chat_id=CHAT_ID,
        message_id=MESSAGE_ID,
        url='url',
        entry_count=3,
    )
    await DownloadProgressHandler(body=payload, bot=bot).handle()

    _assert_accepted(Client.send_message, bot.send_message.await_args)


@pytest.mark.parametrize(
    ('task_cls', 'method'),
    [(VideoUploadTask, Client.send_video), (AudioUploadTask, Client.send_audio)],
)
def test_upload_with_progress_matches_send_media(
    mocker: MockerFixture, task_cls: type, method: object
) -> None:
    task = object.__new__(task_cls)
    task._bot = mocker.Mock()
    task._progress = mocker.AsyncMock()
    task._media_ctx = mocker.Mock(
        caption='c',
        filename='f.mp4',
        filepath='f.mp4',
        duration=1.0,
        height=1,
        width=1,
        thumb=None,
        is_cached=False,
        type=None,
    )
    task._generate_send_media_coroutine(chat_id=CHAT_ID)

    sent = getattr(task._bot, method.__name__).call_args
    _assert_accepted(method, sent)
