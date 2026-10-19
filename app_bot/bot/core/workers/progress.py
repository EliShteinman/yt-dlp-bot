from yt_shared.rabbit.rabbit_config import PROGRESS_QUEUE
from yt_shared.schemas.progress import DownloadProgressPayload

from bot.core.handlers.progress import DownloadProgressHandler
from bot.core.workers.abstract import AbstractDownloadResultWorker, RabbitWorkerType


class DownloadProgressWorker(AbstractDownloadResultWorker):
    """Apply progress reports in arrival order (awaited, not spawned)."""

    TYPE = RabbitWorkerType.PROGRESS
    QUEUE_TYPE = PROGRESS_QUEUE
    SCHEMA_CLS = (DownloadProgressPayload,)

    async def _process_body(self, body: DownloadProgressPayload) -> None:
        await DownloadProgressHandler(body=body, bot=self._bot).handle()
