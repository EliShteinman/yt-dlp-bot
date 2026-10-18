import logging

import pytest
from pyrogram.errors import RPCError
from pytest_mock import MockerFixture
from yt_shared.enums import RabbitPayloadType

from bot.core.handlers.error import ErrorDownloadHandler
from tests.unit.constants import ACK_MESSAGE_ID, CHAT_ID, MESSAGE_ID


@pytest.fixture
def body(mocker: MockerFixture, context: object) -> object:
    return mocker.Mock(
        type=RabbitPayloadType.DOWNLOAD_ERROR,
        task_id='task-1',
        message_id=MESSAGE_ID,
        from_chat_id=CHAT_ID,
        message='Download error',
        url=context.url,
        context=context,
        yt_dlp_version='2026.10.10',
        exception_msg='boom',
        exception_type='DownloadError',
    )


@pytest.fixture
def handler(body: object, bot: object) -> ErrorDownloadHandler:
    return ErrorDownloadHandler(body=body, bot=bot)


async def test_error_is_sent_to_user(
    handler: ErrorDownloadHandler, bot: object
) -> None:
    await handler.handle()

    assert bot.send_message.await_args.kwargs['chat_id'] == CHAT_ID


async def test_error_replies_to_original_message(
    handler: ErrorDownloadHandler, bot: object
) -> None:
    await handler.handle()

    assert bot.send_message.await_args.kwargs['reply_to_message_id'] == MESSAGE_ID


async def test_error_removes_acknowledgment_message(
    handler: ErrorDownloadHandler, bot: object
) -> None:
    await handler.handle()

    bot.delete_messages.assert_awaited_once_with(
        chat_id=CHAT_ID, message_ids=ACK_MESSAGE_ID
    )


async def test_delivered_error_is_logged(
    handler: ErrorDownloadHandler, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO):
        await handler.handle()

    assert 'Delivered error of task "task-1"' in caplog.text


async def test_undelivered_error_is_logged(
    handler: ErrorDownloadHandler, bot: object, caplog: pytest.LogCaptureFixture
) -> None:
    bot.send_message.side_effect = RPCError('nope')
    await handler.handle()

    assert 'Failed to deliver error of task "task-1"' in caplog.text


async def test_missing_ack_message_does_not_break_error(
    handler: ErrorDownloadHandler, bot: object
) -> None:
    bot.delete_messages.side_effect = RPCError('gone')
    await handler.handle()

    bot.send_message.assert_awaited_once()
