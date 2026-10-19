import asyncio
import logging
import time
from collections.abc import Callable

from yt_shared.enums import ProgressStage
from yt_shared.rabbit.publisher import RmqPublisher
from yt_shared.schemas.media import InbMediaPayload
from yt_shared.schemas.progress import DownloadProgressPayload


class DownloadProgressReporter:
    """Turn yt-dlp progress hooks into throttled progress messages for the bot.

    yt-dlp calls the hook from the download thread, so publishing is handed
    over to the event loop that owns the RabbitMQ connection.
    """

    _DOWNLOADING_STATUS = 'downloading'

    def __init__(
        self,
        media_payload: InbMediaPayload,
        publisher: RmqPublisher,
        loop: asyncio.AbstractEventLoop,
        interval_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._media_payload = media_payload
        self._publisher = publisher
        self._loop = loop
        self._interval_seconds = interval_seconds
        self._clock = clock
        self._last_report_at: float | None = None

    def hook(self, status: dict) -> None:
        if status.get('status') != self._DOWNLOADING_STATUS or not self._is_due():
            return
        self._last_report_at = self._clock()
        asyncio.run_coroutine_threadsafe(
            self._publisher.send_progress(self._build_payload(status)), self._loop
        )

    def _is_due(self) -> bool:
        if self._last_report_at is None:
            return True
        return self._clock() - self._last_report_at >= self._interval_seconds

    def _build_payload(self, status: dict) -> DownloadProgressPayload:
        info: dict = status.get('info_dict') or {}
        total = status.get('total_bytes') or status.get('total_bytes_estimate')
        return DownloadProgressPayload(
            stage=ProgressStage.DOWNLOADING,
            from_chat_id=self._media_payload.from_chat_id,
            message_id=self._media_payload.message_id,
            url=self._media_payload.url,
            title=info.get('title'),
            downloaded_bytes=_as_int(status.get('downloaded_bytes')),
            total_bytes=_as_int(total),
            speed=_as_float(status.get('speed')),
            eta=_as_int(status.get('eta')),
        )


def _as_int(value: float | None) -> int | None:
    return None if value is None else int(value)


def _as_float(value: float | None) -> float | None:
    return None if value is None else float(value)
