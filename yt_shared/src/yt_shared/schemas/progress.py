from typing import Literal

from pydantic import NonNegativeFloat, NonNegativeInt, PositiveInt

from yt_shared.enums import ProgressStage, RabbitPayloadType
from yt_shared.schemas.base import StrictBaseRabbitPayloadModel


class DownloadProgressPayload(StrictBaseRabbitPayloadModel):
    """Short-lived progress report from the worker for the chat that asked."""

    type: Literal[RabbitPayloadType.PROGRESS] = RabbitPayloadType.PROGRESS
    stage: ProgressStage
    from_chat_id: int
    message_id: int | None
    url: str
    title: str | None = None
    downloaded_bytes: NonNegativeInt | None = None
    total_bytes: NonNegativeInt | None = None
    speed: NonNegativeFloat | None = None
    eta: NonNegativeInt | None = None
    entry_count: PositiveInt | None = None
