import pytest
from pydantic import ValidationError

from worker.core.config import WorkerSettings
from worker.utils import build_video_format

UNLIMITED_FORMAT = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4'


def test_unlimited_format_matches_original() -> None:
    assert build_video_format(None) == UNLIMITED_FORMAT


def test_limit_filters_video_stream() -> None:
    assert 'bestvideo[ext=mp4][filesize_approx<=1900M]' in build_video_format('1900M')


def test_limit_filters_fallback_format() -> None:
    assert build_video_format('1900M').endswith('/mp4[filesize_approx<=1900M]')


@pytest.mark.parametrize('value', ['1900M', '2G', '1.5G', '500000'])
def test_valid_filesize_setting_is_accepted(value: str) -> None:
    worker_settings = WorkerSettings(MAX_VIDEO_FILESIZE=value)

    assert value == worker_settings.MAX_VIDEO_FILESIZE


@pytest.mark.parametrize('value', ['2GB', 'big', '-1G', '1900M]+x'])
def test_invalid_filesize_setting_is_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        WorkerSettings(MAX_VIDEO_FILESIZE=value)
