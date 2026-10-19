"""Environment and config file needed to import bot modules.

`BotSettings` and the bot `config.yml` are both loaded at import time, so the
environment and a config file must exist before any bot module is imported.
The example config is copied in when no real one is present and removed again
when the test process exits.
"""

import atexit
import os
import shutil
import tempfile
from pathlib import Path

_APP_ROOT = Path(__file__).parent.parent
_CONFIG_PATH = _APP_ROOT / 'config.yml'
_EXAMPLE_CONFIG_PATH = _APP_ROOT / 'config-example.yml'
_CREATED_CONFIG = not _CONFIG_PATH.exists()

if _CREATED_CONFIG:
    shutil.copyfile(_EXAMPLE_CONFIG_PATH, _CONFIG_PATH)
    atexit.register(_CONFIG_PATH.unlink, missing_ok=True)

_ENV_DEFAULTS: dict[str, str] = {
    'APPLICATION_NAME': 'yt_bot_test',
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
    'LOG_LEVEL': 'INFO',
    'REDIS_HOST': 'localhost',
    'TMP_DOWNLOAD_ROOT_PATH': tempfile.gettempdir(),
    'TMP_DOWNLOAD_DIR': 'downloading',
    'TMP_DOWNLOADED_DIR': 'downloaded',
    'TG_MAX_MSG_SIZE': '4096',
    'TG_MAX_CAPTION_SIZE': '1024',
}

for _key, _value in _ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)
