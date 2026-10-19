import pytest
from pyrogram.errors import MessageNotModified, RPCError
from pytest_mock import MockerFixture

from bot.core.status.registry import StatusMessageRegistry
from bot.core.status.updater import StatusMessageUpdater

KEY = (1, 10, 'https://www.youtube.com/watch?v=aaaaaaaaaaa')


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def status_message(mocker: MockerFixture) -> object:
    return mocker.Mock(id=99, delete=mocker.AsyncMock())


@pytest.fixture
def bot(mocker: MockerFixture, status_message: object) -> object:
    return mocker.Mock(
        send_message=mocker.AsyncMock(return_value=status_message),
        edit_message_text=mocker.AsyncMock(),
    )


@pytest.fixture
def updater(bot: object, clock: FakeClock) -> StatusMessageUpdater:
    registry = StatusMessageRegistry(retention_seconds=600, clock=clock)
    return StatusMessageUpdater(
        bot=bot, registry=registry, edit_interval_seconds=5, clock=clock
    )


async def test_first_status_is_sent_as_reply(
    updater: StatusMessageUpdater, bot: object
) -> None:
    await updater.show(KEY, 'downloading')

    assert bot.send_message.await_args.kwargs['reply_parameters'].message_id == 10


async def test_next_status_edits_the_same_message(
    updater: StatusMessageUpdater, bot: object, clock: FakeClock
) -> None:
    await updater.show(KEY, 'downloading 10%')
    clock.now += 5
    await updater.show(KEY, 'downloading 20%')

    assert bot.edit_message_text.await_args.kwargs['message_id'] == 99


async def test_status_within_interval_is_throttled(
    updater: StatusMessageUpdater, bot: object, clock: FakeClock
) -> None:
    await updater.show(KEY, 'downloading 10%')
    clock.now += 4
    await updater.show(KEY, 'downloading 20%')

    bot.edit_message_text.assert_not_awaited()


async def test_forced_status_skips_throttle(
    updater: StatusMessageUpdater, bot: object
) -> None:
    await updater.show(KEY, 'downloading')
    await updater.show(KEY, 'uploading', force=True)

    assert bot.edit_message_text.await_args.kwargs['text'] == 'uploading'


async def test_finish_deletes_the_status_message(
    updater: StatusMessageUpdater, status_message: object
) -> None:
    await updater.show(KEY, 'downloading')
    await updater.finish(KEY)

    status_message.delete.assert_awaited_once()


async def test_late_progress_after_finish_is_ignored(
    updater: StatusMessageUpdater, bot: object, clock: FakeClock
) -> None:
    await updater.finish(KEY)
    clock.now += 10
    await updater.show(KEY, 'downloading')

    bot.send_message.assert_not_awaited()


async def test_unchanged_text_is_tolerated(
    updater: StatusMessageUpdater, bot: object, clock: FakeClock
) -> None:
    bot.edit_message_text.side_effect = MessageNotModified()
    await updater.show(KEY, 'same')
    clock.now += 5
    await updater.show(KEY, 'same')

    bot.edit_message_text.assert_awaited_once()


async def test_failed_send_is_logged(
    updater: StatusMessageUpdater, bot: object, caplog: pytest.LogCaptureFixture
) -> None:
    bot.send_message.side_effect = RPCError('flood')
    await updater.show(KEY, 'downloading')

    assert 'Could not send status message' in caplog.text
