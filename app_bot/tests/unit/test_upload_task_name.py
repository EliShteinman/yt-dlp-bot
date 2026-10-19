import pytest
from pytest_mock import MockerFixture
from yt_shared.enums import MediaFileType

from bot.core.handlers.success import SuccessDownloadHandler
from tests.unit.constants import CHAT_ID, MESSAGE_ID


class VideoUploadTaskStub:
    def __init__(self, **_: object) -> None:
        pass

    def run(self) -> None:
        pass


@pytest.fixture
def handler(
    mocker: MockerFixture, context: object, bot: object
) -> SuccessDownloadHandler:
    mocker.patch('bot.core.handlers.success.RmqPublisher')
    bot.conf.telegram.max_upload_tasks = 2
    mocker.patch.dict(
        SuccessDownloadHandler._UPLOAD_TASK_MAP,
        {MediaFileType.VIDEO: VideoUploadTaskStub},
    )
    body = mocker.Mock(
        task_id='task-1', message_id=MESSAGE_ID, from_chat_id=CHAT_ID, context=context
    )
    return SuccessDownloadHandler(body=body, bot=bot)


async def test_upload_task_is_named_after_its_class(
    mocker: MockerFixture, handler: SuccessDownloadHandler
) -> None:
    create_task = mocker.patch(
        'bot.core.handlers.success.create_task', mocker.AsyncMock()
    )
    await handler._create_upload_task(mocker.Mock(file_type=MediaFileType.VIDEO))

    assert create_task.await_args.kwargs['task_name'] == 'VideoUploadTaskStub'
