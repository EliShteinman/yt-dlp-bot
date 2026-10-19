import logging
from typing import TYPE_CHECKING

from pyrogram.enums import ParseMode
from pyrogram.errors import RPCError
from pyrogram.types import ReplyParameters
from yt_shared.enums import ProgressStage
from yt_shared.schemas.progress import DownloadProgressPayload

from bot.core.status.formatter import StatusTextFormatter

if TYPE_CHECKING:
    from bot.bot.client import VideoBotClient


class DownloadProgressHandler:
    """Reflect a worker progress report in the requesting chat."""

    def __init__(self, body: DownloadProgressPayload, bot: VideoBotClient) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._body = body
        self._bot = bot

    async def handle(self) -> None:
        if not self._wants_status_messages():
            return
        match self._body.stage:
            case ProgressStage.PLAYLIST_QUEUED:
                await self._announce_playlist()
            case ProgressStage.DOWNLOADING:
                await self._show_download_progress()

    def _wants_status_messages(self) -> bool:
        user = self._bot.allowed_users.get(self._body.from_chat_id)
        return user is not None and not user.upload.silent

    async def _announce_playlist(self) -> None:
        kwargs: dict = {
            'chat_id': self._body.from_chat_id,
            'text': StatusTextFormatter.playlist_queued(self._body.entry_count or 0),
            'parse_mode': ParseMode.HTML,
        }
        if self._body.message_id:
            kwargs['reply_parameters'] = ReplyParameters(
                message_id=self._body.message_id
            )
        try:
            await self._bot.send_message(**kwargs)
        except RPCError as err:
            self._log.warning('Could not announce playlist: %s', err)

    async def _show_download_progress(self) -> None:
        body = self._body
        await self._bot.status.show(
            key=(body.from_chat_id, body.message_id, body.url),
            text=StatusTextFormatter.downloading(
                title=body.title,
                downloaded_bytes=body.downloaded_bytes,
                total_bytes=body.total_bytes,
                speed=body.speed,
                eta=body.eta,
            ),
        )
