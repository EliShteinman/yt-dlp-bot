import aio_pika
import pytest
from pytest_mock import MockerFixture
from yt_shared.rabbit.publisher import RmqPublisher
from yt_shared.rabbit.rabbit_config import (
    DEAD_LETTER_EXCHANGE,
    DEAD_LETTER_QUEUE,
    ERROR_QUEUE,
    INPUT_QUEUE,
    SUCCESS_QUEUE,
    get_rabbit_config,
)
from yt_shared.utils.common import Singleton

WORK_QUEUES = (INPUT_QUEUE, ERROR_QUEUE, SUCCESS_QUEUE)


def _queue_arguments(name: str) -> dict:
    queues = {queue['name']: queue for queue in get_rabbit_config()['queues']}
    return queues[name]['arguments']


@pytest.mark.parametrize('queue', WORK_QUEUES)
def test_work_queue_is_quorum(queue: str) -> None:
    assert _queue_arguments(queue)['x-queue-type'] == 'quorum'


@pytest.mark.parametrize('queue', WORK_QUEUES)
def test_work_queue_limits_redeliveries(queue: str) -> None:
    assert _queue_arguments(queue)['x-delivery-limit'] == 2


@pytest.mark.parametrize('queue', WORK_QUEUES)
def test_work_queue_dead_letters_to_dead_exchange(queue: str) -> None:
    assert _queue_arguments(queue)['x-dead-letter-exchange'] == DEAD_LETTER_EXCHANGE


@pytest.mark.parametrize('queue', WORK_QUEUES)
def test_work_queue_allows_long_jobs(queue: str) -> None:
    assert _queue_arguments(queue)['x-consumer-timeout'] == 21600000


def test_dead_letter_queue_is_bound_to_dead_exchange() -> None:
    bindings = get_rabbit_config()['queue_bindings'][DEAD_LETTER_QUEUE]

    assert bindings == [{'exchange_name': DEAD_LETTER_EXCHANGE}]


@pytest.fixture
def exchange(mocker: MockerFixture) -> object:
    return mocker.Mock(publish=mocker.AsyncMock())


@pytest.fixture
def publisher(mocker: MockerFixture, exchange: object) -> RmqPublisher:
    Singleton._instances.pop(RmqPublisher, None)
    rabbit = mocker.Mock(exchanges=mocker.MagicMock())
    rabbit.exchanges.__getitem__.return_value = exchange
    mocker.patch('yt_shared.rabbit.publisher.get_rabbitmq', return_value=rabbit)
    yield RmqPublisher()
    Singleton._instances.pop(RmqPublisher, None)


@pytest.mark.parametrize(
    'method', ['send_for_download', 'send_download_error', 'send_download_finished']
)
async def test_published_messages_are_persistent(
    mocker: MockerFixture, publisher: RmqPublisher, exchange: object, method: str
) -> None:
    payload = mocker.Mock(model_dump_json=mocker.Mock(return_value='{}'))
    await getattr(publisher, method)(payload)

    message = exchange.publish.await_args.args[0]
    assert message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
