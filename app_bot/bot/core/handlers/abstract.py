import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pyrogram.errors import RPCError
from yt_shared.enums import TaskSource, TelegramChatType
from yt_shared.schemas.base_rabbit import BaseRabbitDownloadPayload

from bot.core.schemas import AnonymousUserSchema, UserSchema
from bot.core.status.registry import StatusKey

if TYPE_CHECKING:
    from bot.bot import VideoBotClient


class AbstractDownloadHandler(ABC):
    def __init__(self, body: BaseRabbitDownloadPayload, bot: VideoBotClient) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._body = body
        self._bot = bot
        self._receiving_users = self._get_receiving_users()

    @abstractmethod
    async def handle(self) -> None:
        pass

    def _status_key(self) -> StatusKey:
        return (
            self._body.from_chat_id,
            self._body.message_id,
            self._body.context.url,
        )

    async def _delete_acknowledgment_message(self) -> None:
        chat_id = self._body.from_chat_id
        ack_message_id = self._body.context.ack_message_id
        if not (chat_id and ack_message_id):
            return
        try:
            await self._bot.delete_messages(chat_id=chat_id, message_ids=ack_message_id)
        except RPCError as err:
            self._log.warning(
                'Could not delete acknowledgment message "%s": %s', ack_message_id, err
            )

    def _get_sender_id(self) -> int | None:
        if self._body.context.source is TaskSource.API:
            return None
        if self._body.context.from_chat_type is TelegramChatType.PRIVATE:
            return self._body.context.from_user_id
        return self._body.context.from_chat_id

    def _get_receiving_users(self) -> list[AnonymousUserSchema | UserSchema]:
        if self._body.context.source is TaskSource.API:
            return self._bot.conf.telegram.api.upload_to_chat_ids.copy()
        return [self._bot.allowed_users[self._get_sender_id()]]
