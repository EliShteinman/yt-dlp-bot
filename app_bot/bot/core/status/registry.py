import time
from collections.abc import Callable

from pyrogram.types import Message

type StatusKey = tuple[int, int | None, str]


class StatusMessageRegistry:
    """Track the live status message of every media being processed.

    A key is (chat id, id of the message that sent the link, media URL). Keys of
    finished media are remembered for a while so that a late progress report
    does not bring a deleted status message back.
    """

    def __init__(
        self, retention_seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._retention_seconds = retention_seconds
        self._clock = clock
        self._messages: dict[StatusKey, Message] = {}
        self._finished_at: dict[StatusKey, float] = {}

    def get(self, key: StatusKey) -> Message | None:
        return self._messages.get(key)

    def store(self, key: StatusKey, message: Message) -> None:
        self._messages[key] = message

    def pop(self, key: StatusKey) -> Message | None:
        return self._messages.pop(key, None)

    def mark_finished(self, key: StatusKey) -> None:
        self._forget_expired()
        self._finished_at[key] = self._clock()

    def is_finished(self, key: StatusKey) -> bool:
        self._forget_expired()
        return key in self._finished_at

    def _forget_expired(self) -> None:
        oldest_kept = self._clock() - self._retention_seconds
        for key in [k for k, at in self._finished_at.items() if at < oldest_kept]:
            del self._finished_at[key]
