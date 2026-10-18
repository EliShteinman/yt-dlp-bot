from pydantic import DirectoryPath, Field, field_validator
from yt_shared.config import CommonSettings


class WorkerSettings(CommonSettings):
    APPLICATION_NAME: str
    MAX_SIMULTANEOUS_DOWNLOADS: int
    STORAGE_PATH: DirectoryPath
    THUMBNAIL_FRAME_SECOND: float
    INSTAGRAM_ENCODE_TO_H264: bool
    FACEBOOK_ENCODE_TO_H264: bool
    MAX_DOWNLOAD_THREADS: str
    POT_PROVIDER_BASE_URL: str
    MAX_PLAYLIST_ITEMS: int = Field(gt=0)
    MAX_VIDEO_HEIGHT: int | None = Field(default=None, gt=0)

    @field_validator('MAX_DOWNLOAD_THREADS')
    @classmethod
    def validate_max_download_threads(cls, value: str) -> str:
        """Value must be integer enclosed as string."""
        if not value.isdigit():
            raise ValueError('Value must be integer enclosed as string.')
        return value


settings = WorkerSettings()
