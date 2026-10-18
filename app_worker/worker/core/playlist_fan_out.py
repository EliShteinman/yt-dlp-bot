import asyncio
import logging

from yt_shared.rabbit.publisher import RmqPublisher
from yt_shared.schemas.media import InbMediaPayload

from worker.core.playlist_expander import PlaylistExpander


class PlaylistFanOut:
    """Re-queue every playlist entry as its own single-media download task."""

    def __init__(self, expander: PlaylistExpander, publisher: RmqPublisher) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._expander = expander
        self._publisher = publisher

    async def try_fan_out(self, media_payload: InbMediaPayload) -> bool:
        entry_urls = await asyncio.get_running_loop().run_in_executor(
            None, self._expander.expand, media_payload.url
        )
        if not entry_urls:
            return False

        for entry_url in entry_urls:
            await self._publish_entry(media_payload, entry_url)
        return True

    async def _publish_entry(self, media_payload: InbMediaPayload, url: str) -> None:
        entry_payload = media_payload.model_copy(
            update={
                'id': None,
                'url': url,
                'original_url': url,
                'custom_filename': None,
            }
        )
        if not await self._publisher.send_for_download(entry_payload):
            self._log.error('Failed to queue playlist entry "%s"', url)
