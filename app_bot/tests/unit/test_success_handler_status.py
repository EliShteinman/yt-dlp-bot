import pytest
from pyrogram.errors import RPCError
from pytest_mock import MockerFixture
from yt_shared.enums import TaskSource

from bot.core.handlers.success import SuccessDownloadHandler
from tests.unit.constants import ACK_MESSAGE_ID, CHAT_ID, MESSAGE_ID

STATUS_KEY = (CHAT_ID, MESSAGE_ID, 'https://www.youtube.com/watch?v=aaa')


@pytest.fixture
def media_object(mocker: MockerFixture) -> object:
    return mocker.Mock(
        title='Lesson 1', current_file_size=mocker.Mock(return_value=2048)
    )


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
def handler(mocker: MockerFixture, body: object, bot: object) -> SuccessDownloadHandler:
    mocker.patch('bot.core.handlers.success.RmqPublisher')
    mocker.patch('bot.core.handlers.success.is_user_upload_silent', return_value=False)
    handler = SuccessDownloadHandler(body=body, bot=bot)
    mocker.patch.object(handler, '_create_upload_task', mocker.AsyncMock())
    return handler


async def test_upload_starts_by_showing_upload_status(
    handler: SuccessDownloadHandler, bot: object, media_object: object
) -> None:
    await handler._upload_with_status(media_object)

    key, text = bot.status.show.await_args_list[0].args
    assert (key, 'Uploading' in text, bot.status.show.await_args_list[0].kwargs) == (
        STATUS_KEY,
        True,
        {'force': True},
    )


async def test_status_is_finished_after_upload(
    handler: SuccessDownloadHandler, bot: object, media_object: object
) -> None:
    await handler._upload_with_status(media_object)

    bot.status.finish.assert_awaited_once_with(STATUS_KEY)


async def test_status_is_finished_when_upload_fails(
    handler: SuccessDownloadHandler, bot: object, media_object: object
) -> None:
    handler._create_upload_task.side_effect = RuntimeError('upload failed')
    with pytest.raises(RuntimeError):
        await handler._upload_with_status(media_object)

    bot.status.finish.assert_awaited_once_with(STATUS_KEY)


async def test_upload_progress_updates_status(
    handler: SuccessDownloadHandler, bot: object, media_object: object
) -> None:
    await handler._upload_with_status(media_object)
    progress = handler._create_upload_task.await_args.kwargs['progress']
    await progress(1024, 2048)

    assert '50%' in bot.status.show.await_args.args[1]


async def test_no_status_without_chat(
    handler: SuccessDownloadHandler, body: object, bot: object, media_object: object
) -> None:
    body.from_chat_id = None
    await handler._upload_with_status(media_object)

    bot.status.show.assert_not_awaited()


async def test_upload_without_status_still_happens(
    handler: SuccessDownloadHandler, body: object, media_object: object
) -> None:
    body.from_chat_id = None
    await handler._upload_with_status(media_object)

    assert handler._create_upload_task.await_args.kwargs['progress'] is None


async def test_no_status_for_api_tasks(
    handler: SuccessDownloadHandler, context: object, bot: object, media_object: object
) -> None:
    context.source = TaskSource.API
    await handler._upload_with_status(media_object)

    bot.status.show.assert_not_awaited()


async def test_no_status_for_silent_user(
    mocker: MockerFixture,
    handler: SuccessDownloadHandler,
    bot: object,
    media_object: object,
) -> None:
    mocker.patch('bot.core.handlers.success.is_user_upload_silent', return_value=True)
    await handler._upload_with_status(media_object)

    bot.status.show.assert_not_awaited()


async def test_success_text_is_skipped_when_uploading(
    mocker: MockerFixture, handler: SuccessDownloadHandler, media_object: object
) -> None:
    mocker.patch.object(handler, '_upload_is_enabled', return_value=True)
    mocker.patch.object(handler, '_validate_file_size_for_upload')
    send_success_text = mocker.patch.object(handler, '_send_success_text')
    await handler._handle_media_object(media_object)

    send_success_text.assert_not_called()


async def test_success_text_is_sent_when_not_uploading(
    mocker: MockerFixture, handler: SuccessDownloadHandler, media_object: object
) -> None:
    mocker.patch.object(handler, '_upload_is_enabled', return_value=False)
    send_success_text = mocker.patch.object(
        handler, '_send_success_text', mocker.AsyncMock()
    )
    await handler._handle_media_object(media_object)

    send_success_text.assert_awaited_once_with(media_object)


async def test_acknowledgment_is_removed_before_media_handling(
    mocker: MockerFixture, handler: SuccessDownloadHandler, bot: object
) -> None:
    mocker.patch.object(handler, '_handle_media_object', mocker.AsyncMock())
    await handler._handle()

    bot.delete_messages.assert_awaited_once_with(
        chat_id=CHAT_ID, message_ids=ACK_MESSAGE_ID
    )


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
