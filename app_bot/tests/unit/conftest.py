import pytest
from pytest_mock import MockerFixture
from yt_shared.enums import TaskSource, TelegramChatType

from tests.unit.constants import ACK_MESSAGE_ID, CHAT_ID


@pytest.fixture
def receiving_user(mocker: MockerFixture) -> object:
    user = mocker.Mock(id=CHAT_ID)
    user.upload.silent = False
    return user


@pytest.fixture
def bot(mocker: MockerFixture, receiving_user: object) -> object:
    bot = mocker.Mock()
    bot.allowed_users = {CHAT_ID: receiving_user}
    bot.delete_messages = mocker.AsyncMock()
    bot.send_message = mocker.AsyncMock()
    bot.status = mocker.Mock(show=mocker.AsyncMock(), finish=mocker.AsyncMock())
    return bot


@pytest.fixture
def context(mocker: MockerFixture) -> object:
    return mocker.Mock(
        source=TaskSource.BOT,
        from_chat_type=TelegramChatType.PRIVATE,
        from_user_id=CHAT_ID,
        ack_message_id=ACK_MESSAGE_ID,
        url='https://www.youtube.com/watch?v=aaa',
    )
