from typing import Any

from aio_pika import ExchangeType

from yt_shared.config import settings

INPUT_QUEUE = 'input.q'
ERROR_QUEUE = 'error.q'
SUCCESS_QUEUE = 'success.q'

INPUT_EXCHANGE = 'input.dx'
SUCCESS_EXCHANGE = 'success.dx'
ERROR_EXCHANGE = 'error.dx'

DEAD_LETTER_QUEUE = 'dead.q'
DEAD_LETTER_EXCHANGE = 'dead.fx'


def _work_queue(name: str) -> dict[str, Any]:
    return {
        'name': name,
        'auto_delete': False,
        'durable': True,
        'arguments': {
            'x-queue-type': 'quorum',
            'x-delivery-limit': settings.CONSUMER_NUMBER_OF_RETRY,
            'x-dead-letter-exchange': DEAD_LETTER_EXCHANGE,
            'x-consumer-timeout': settings.RABBITMQ_CONSUMER_TIMEOUT_MS,
        },
    }


def get_rabbit_config() -> dict[str, list[dict[str, Any]]]:
    return {
        'queues': [
            _work_queue(INPUT_QUEUE),
            _work_queue(ERROR_QUEUE),
            _work_queue(SUCCESS_QUEUE),
            {
                'name': DEAD_LETTER_QUEUE,
                'auto_delete': False,
                'durable': True,
                'arguments': {'x-queue-type': 'quorum'},
            },
        ],
        'exchanges': [
            {
                'name': INPUT_EXCHANGE,
                'auto_delete': False,
                'durable': True,
                'type': ExchangeType.DIRECT.value,
            },
            {
                'name': ERROR_EXCHANGE,
                'auto_delete': False,
                'durable': True,
                'type': ExchangeType.DIRECT.value,
            },
            {
                'name': SUCCESS_EXCHANGE,
                'auto_delete': False,
                'durable': True,
                'type': ExchangeType.DIRECT.value,
            },
            {
                'name': DEAD_LETTER_EXCHANGE,
                'auto_delete': False,
                'durable': True,
                'type': ExchangeType.FANOUT.value,
            },
        ],
        'queue_bindings': {
            INPUT_QUEUE: [{'exchange_name': INPUT_EXCHANGE}],
            ERROR_QUEUE: [{'exchange_name': ERROR_EXCHANGE}],
            SUCCESS_QUEUE: [{'exchange_name': SUCCESS_EXCHANGE}],
            DEAD_LETTER_QUEUE: [{'exchange_name': DEAD_LETTER_EXCHANGE}],
        },
    }
