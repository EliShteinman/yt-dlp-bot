"""Shared test fixtures and the environment needed to import worker modules.

`WorkerSettings`/`CommonSettings` are instantiated at import time with required
fields, so the environment must be populated before any worker module is
imported. This runs at conftest import, which precedes test-module collection.
"""

import os
import tempfile
from pathlib import Path

_TMP_ROOT = Path(tempfile.mkdtemp(prefix='ytbot-test-'))
(_TMP_ROOT / 'downloading').mkdir(exist_ok=True)
(_TMP_ROOT / 'downloaded').mkdir(exist_ok=True)

_ENV_DEFAULTS: dict[str, str] = {
    'APPLICATION_NAME': 'yt_worker_test',
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
    'LOG_LEVEL': 'INFO',
    'REDIS_HOST': 'localhost',
    'TMP_DOWNLOAD_ROOT_PATH': str(_TMP_ROOT),
    'TMP_DOWNLOAD_DIR': str(_TMP_ROOT / 'downloading'),
    'TMP_DOWNLOADED_DIR': str(_TMP_ROOT / 'downloaded'),
    'MAX_SIMULTANEOUS_DOWNLOADS': '2',
    'MAX_DOWNLOAD_THREADS': '10',
    'MAX_PLAYLIST_ITEMS': '50',
    'MAX_VIDEO_HEIGHT': '1080',
    'STORAGE_PATH': str(_TMP_ROOT),
    'THUMBNAIL_FRAME_SECOND': '10.0',
    'INSTAGRAM_ENCODE_TO_H264': 'True',
    'FACEBOOK_ENCODE_TO_H264': 'True',
    'POT_PROVIDER_BASE_URL': 'http://localhost:4416',
}

for _key, _value in _ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)
