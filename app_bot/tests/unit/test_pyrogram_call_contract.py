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

from bot.core.callbacks import TelegramCallback
from bot.core.handlers.error import ErrorDownloadHandler
from bot.core.handlers.success import SuccessDownloadHandler
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


async def test_upload_status_matches_send_message(
    mocker: MockerFixture, bot: object, context: object
) -> None:
    mocker.patch('bot.core.handlers.success.RmqPublisher')
    body = mocker.Mock(message_id=MESSAGE_ID, from_chat_id=CHAT_ID, context=context)
    media_object = mocker.Mock(file_size_human=mocker.Mock(return_value='1MiB'))
    handler = SuccessDownloadHandler(body=body, bot=bot)
    await handler._send_upload_status(media_object)

    _assert_accepted(Client.send_message, bot.send_message.await_args)
