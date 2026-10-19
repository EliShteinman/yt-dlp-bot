import asyncio
import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified, RPCError
from pyrogram.types import ReplyParameters

from bot.core.status.registry import StatusKey, StatusMessageRegistry

if TYPE_CHECKING:
    from pyrogram import Client


class StatusMessageUpdater:
    """Show one status message per media and keep editing it in place.

    Edits of the same message are throttled to one per `edit_interval_seconds`
    to stay well inside Telegram's flood limits; `force` bypasses the throttle
    for stage changes (e.g. downloading -> uploading).
    """

    def __init__(
        self,
        bot: Client,
        registry: StatusMessageRegistry,
        edit_interval_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._bot = bot
        self._registry = registry
        self._edit_interval_seconds = edit_interval_seconds
        self._clock = clock
        self._last_shown_at: dict[StatusKey, float] = {}
        self._lock = asyncio.Lock()

    async def show(self, key: StatusKey, text: str, force: bool = False) -> None:
        async with self._lock:
            if self._registry.is_finished(key) or not (force or self._is_due(key)):
                return
            self._last_shown_at[key] = self._clock()
            message = self._registry.get(key)
            if message:
                await self._edit(key, message.id, text)
            else:
                await self._send(key, text)

    async def finish(self, key: StatusKey) -> None:
        async with self._lock:
            self._registry.mark_finished(key)
            self._last_shown_at.pop(key, None)
            message = self._registry.pop(key)
        if not message:
            return
        try:
            await message.delete()
        except RPCError as err:
            self._log.warning(
                'Could not delete status message "%s": %s', message.id, err
            )

    def _is_due(self, key: StatusKey) -> bool:
        last_shown_at = self._last_shown_at.get(key)
        if last_shown_at is None:
            return True
        return self._clock() - last_shown_at >= self._edit_interval_seconds

    async def _send(self, key: StatusKey, text: str) -> None:
        chat_id, reply_to_message_id, _ = key
        kwargs: dict = {'chat_id': chat_id, 'text': text, 'parse_mode': ParseMode.HTML}
        if reply_to_message_id:
            kwargs['reply_parameters'] = ReplyParameters(message_id=reply_to_message_id)
        try:
            self._registry.store(key, await self._bot.send_message(**kwargs))
        except RPCError as err:
            self._log.warning('Could not send status message: %s', err)

    async def _edit(self, key: StatusKey, message_id: int, text: str) -> None:
        try:
            await self._bot.edit_message_text(
                chat_id=key[0],
                message_id=message_id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
        except MessageNotModified:
            pass
        except RPCError as err:
            self._log.warning('Could not edit status message "%s": %s', message_id, err)
