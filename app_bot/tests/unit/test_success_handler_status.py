import pytest
from pyrogram.errors import RPCError
from pytest_mock import MockerFixture

from bot.core.handlers.success import SuccessDownloadHandler
from tests.unit.constants import ACK_MESSAGE_ID, CHAT_ID, MESSAGE_ID


@pytest.fixture
def media_object(mocker: MockerFixture) -> object:
    return mocker.Mock(file_size_human=mocker.Mock(return_value='44.3MiB'))


@pytest.fixture
def body(mocker: MockerFixture, context: object, media_object: object) -> object:
    media = mocker.Mock(get_media_objects=mocker.Mock(return_value=[media_object]))
    return mocker.Mock(
        task_id='task-1',
        message_id=MESSAGE_ID,
        from_chat_id=CHAT_ID,
        context=context,
        media=media,
    )


@pytest.fixture
def status_message(mocker: MockerFixture) -> object:
    return mocker.Mock(id=99, delete=mocker.AsyncMock())


@pytest.fixture
def handler(
    mocker: MockerFixture, body: object, bot: object, status_message: object
) -> SuccessDownloadHandler:
    mocker.patch('bot.core.handlers.success.RmqPublisher')
    bot.send_message.return_value = status_message
    handler = SuccessDownloadHandler(body=body, bot=bot)
    mocker.patch.object(handler, '_create_upload_task', mocker.AsyncMock())
    return handler


async def test_upload_status_is_its_own_message(
    handler: SuccessDownloadHandler, bot: object, media_object: object
) -> None:
    await handler._upload_with_status(media_object)

    assert 'Uploading 44.3MiB' in bot.send_message.await_args.kwargs['text']


async def test_upload_status_replies_to_original_message(
    handler: SuccessDownloadHandler, bot: object, media_object: object
) -> None:
    await handler._upload_with_status(media_object)

    assert bot.send_message.await_args.kwargs['reply_to_message_id'] == MESSAGE_ID


async def test_upload_status_is_removed_after_upload(
    handler: SuccessDownloadHandler, media_object: object, status_message: object
) -> None:
    await handler._upload_with_status(media_object)

    status_message.delete.assert_awaited_once()


async def test_upload_status_is_removed_when_upload_fails(
    handler: SuccessDownloadHandler, media_object: object, status_message: object
) -> None:
    handler._create_upload_task.side_effect = RuntimeError('upload failed')
    with pytest.raises(RuntimeError):
        await handler._upload_with_status(media_object)

    status_message.delete.assert_awaited_once()


async def test_status_delete_failure_is_tolerated(
    handler: SuccessDownloadHandler,
    media_object: object,
    status_message: object,
    caplog: pytest.LogCaptureFixture,
) -> None:
    status_message.delete.side_effect = RPCError('gone')
    await handler._upload_with_status(media_object)

    assert 'Could not delete upload status message "99"' in caplog.text


async def test_acknowledgment_is_removed_before_media_handling(
    mocker: MockerFixture, handler: SuccessDownloadHandler, bot: object
) -> None:
    mocker.patch.object(handler, '_handle_media_object', mocker.AsyncMock())
    await handler._handle()

    bot.delete_messages.assert_awaited_once_with(
        chat_id=CHAT_ID, message_ids=ACK_MESSAGE_ID
    )


async def test_no_status_without_chat(
    handler: SuccessDownloadHandler, body: object, bot: object, media_object: object
) -> None:
    body.from_chat_id = None
    await handler._upload_with_status(media_object)

    bot.send_message.assert_not_awaited()


async def test_no_acknowledgment_removal_without_ack(
    mocker: MockerFixture, handler: SuccessDownloadHandler, context: object, bot: object
) -> None:
    context.ack_message_id = None
    mocker.patch.object(handler, '_handle_media_object', mocker.AsyncMock())
    await handler._handle()

    bot.delete_messages.assert_not_awaited()


async def test_acknowledgment_removal_failure_is_logged(
    mocker: MockerFixture,
    handler: SuccessDownloadHandler,
    bot: object,
    caplog: pytest.LogCaptureFixture,
) -> None:
    bot.delete_messages.side_effect = RPCError('gone')
    mocker.patch.object(handler, '_handle_media_object', mocker.AsyncMock())
    await handler._handle()

    assert f'Could not delete acknowledgment message "{ACK_MESSAGE_ID}"' in caplog.text
