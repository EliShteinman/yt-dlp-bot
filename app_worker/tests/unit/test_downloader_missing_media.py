from pathlib import Path

import pytest

from worker.core.downloader import MediaDownloader
from worker.core.exceptions import MediaDownloaderError

VIDEO_NAME = 'lesson.mp4'


@pytest.fixture
def downloader() -> MediaDownloader:
    return MediaDownloader()


@pytest.fixture
def video_meta(tmp_path: Path) -> dict:
    return {
        '_type': 'video',
        'title': 'lesson',
        'requested_downloads': [
            {
                'ext': 'mp4',
                'filepath': str(tmp_path / VIDEO_NAME),
                '_filename': str(tmp_path / VIDEO_NAME),
            },
        ],
    }


def test_missing_video_raises_download_error(
    downloader: MediaDownloader, video_meta: dict, tmp_path: Path
) -> None:
    with pytest.raises(MediaDownloaderError, match=f'"{VIDEO_NAME}" was not created'):
        downloader._create_video_dto(video_meta, tmp_path, tmp_path / 'dest')


def test_missing_audio_raises_download_error(
    downloader: MediaDownloader, video_meta: dict, tmp_path: Path
) -> None:
    with pytest.raises(MediaDownloaderError, match='"audio" was not created'):
        downloader._create_audio_dto(video_meta, tmp_path, tmp_path / 'dest')


def test_existing_video_passes_check(
    downloader: MediaDownloader, tmp_path: Path
) -> None:
    video_path = tmp_path / VIDEO_NAME
    video_path.write_bytes(b'video')

    downloader._ensure_media_file_exists(video_path)


def test_missing_video_is_logged(
    downloader: MediaDownloader,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with pytest.raises(MediaDownloaderError):
        downloader._ensure_media_file_exists(tmp_path / VIDEO_NAME)

    assert 'was not created' in caplog.text
