"""Environment needed to import modules that build `CommonSettings` at import time."""

import os

_ENV_DEFAULTS: dict[str, str] = {
    'APPLICATION_NAME': 'yt_shared_test',
    'POSTGRES_USER': 'yt',
    'POSTGRES_PASSWORD': 'yt',
    'POSTGRES_HOST': 'localhost',
    'POSTGRES_PORT': '5432',
    'POSTGRES_DB': 'yt',
    'SQLALCHEMY_ECHO': 'False',
    'SQLALCHEMY_EXPIRE_ON_COMMIT': 'False',
    'RABBITMQ_USER': 'guest',
    'RABBITMQ_PASSWORD': 'guest',
    'RABBITMQ_HOST': 'localhost',
    'RABBITMQ_PORT': '5672',
    'RABBITMQ_CONSUMER_TIMEOUT_MS': '21600000',
    'RABBITMQ_PROGRESS_TTL_MS': '60000',
    'LOG_LEVEL': 'INFO',
    'REDIS_HOST': 'localhost',
    'TMP_DOWNLOAD_ROOT_PATH': '.',
    'TMP_DOWNLOAD_DIR': 'downloading',
    'TMP_DOWNLOADED_DIR': 'downloaded',
}

for _key, _value in _ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)
