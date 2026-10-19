import asyncio

import pytest
from pytest_mock import MockerFixture

from worker.core.callbacks import RMQCallbacks

VALID_BODY = (
    b'{"id":null,"from_chat_id":1,"from_chat_type":"private","from_user_id":1,'
    b'"message_id":1,"ack_message_id":2,'
    b'"url":"https://www.youtube.com/watch?v=aaa",'
    b'"original_url":"https://www.youtube.com/watch?v=aaa","source":"BOT",'
    b'"save_to_storage":false,"download_media_type":"VIDEO",'
    b'"custom_filename":null,"automatic_extension":false,'
    b'"added_at":"2026-10-18T00:00:00Z"}'
)


class ConcurrencyProbe:
    def __init__(self) -> None:
        self.running = 0
        self.max_running = 0

    async def handle(self, media_payload: object) -> None:  # noqa: ARG002
        self.running += 1
        self.max_running = max(self.max_running, self.running)
        await asyncio.sleep(0.01)
        self.running -= 1


def _message(mocker: MockerFixture, body: bytes = VALID_BODY) -> object:
    return mocker.Mock(
        body=body,
        processed=False,
        ack=mocker.AsyncMock(),
        reject=mocker.AsyncMock(),
    )


@pytest.fixture
def probe() -> ConcurrencyProbe:
    return ConcurrencyProbe()


@pytest.mark.parametrize('limit', [1, 2])
async def test_downloads_never_exceed_limit(
    mocker: MockerFixture, probe: ConcurrencyProbe, limit: int
) -> None:
    callbacks = RMQCallbacks(payload_handler=probe, max_simultaneous_downloads=limit)
    messages = [_message(mocker) for _ in range(5)]
    await asyncio.gather(*(callbacks.on_input_message(m) for m in messages))

    assert probe.max_running == limit


async def test_waiting_message_is_not_acked(
    mocker: MockerFixture, probe: ConcurrencyProbe
) -> None:
    callbacks = RMQCallbacks(payload_handler=probe, max_simultaneous_downloads=1)
    first, second = _message(mocker), _message(mocker)
    first_task = asyncio.create_task(callbacks.on_input_message(first))
    await asyncio.sleep(0)
    second_task = asyncio.create_task(callbacks.on_input_message(second))
    await asyncio.sleep(0)

    assert second.ack.await_count == 0
    await asyncio.gather(first_task, second_task)


async def test_invalid_message_is_rejected(
    mocker: MockerFixture, probe: ConcurrencyProbe
) -> None:
    callbacks = RMQCallbacks(payload_handler=probe, max_simultaneous_downloads=1)
    message = _message(mocker, body=b'not json')
    await callbacks.on_input_message(message)

    message.reject.assert_awaited_once_with(requeue=False)


class FailingHandler:
    async def handle(self, media_payload: object) -> None:  # noqa: ARG002
        raise RuntimeError('worker crashed mid-task')


async def test_message_is_acked_only_after_handling(
    mocker: MockerFixture, probe: ConcurrencyProbe
) -> None:
    events: list[str] = []
    message = _message(mocker)
    message.ack.side_effect = lambda: events.append('ack')
    original_handle = probe.handle

    async def recording_handle(media_payload: object) -> None:
        await original_handle(media_payload)
        events.append('handled')

    probe.handle = recording_handle
    callbacks = RMQCallbacks(payload_handler=probe, max_simultaneous_downloads=1)
    await callbacks.on_input_message(message)

    assert events == ['handled', 'ack']


async def test_crashed_handling_is_not_acked(mocker: MockerFixture) -> None:
    callbacks = RMQCallbacks(
        payload_handler=FailingHandler(), max_simultaneous_downloads=1
    )
    message = _message(mocker)
    await callbacks.on_input_message(message)

    message.ack.assert_not_awaited()


async def test_crashed_handling_is_dead_lettered(mocker: MockerFixture) -> None:
    callbacks = RMQCallbacks(
        payload_handler=FailingHandler(), max_simultaneous_downloads=1
    )
    message = _message(mocker)
    await callbacks.on_input_message(message)

    message.reject.assert_awaited_once_with(requeue=False)
