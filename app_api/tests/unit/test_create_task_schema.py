import pytest
from pydantic import ValidationError

from api.apps.video.v1.tasks.schemas.task import CreateTaskIn

VIDEO_URL = 'https://www.youtube.com/watch?v=aaaaaaaaaaa'


def _create_task(**overrides: object) -> CreateTaskIn:
    fields: dict[str, object] = {
        'url': VIDEO_URL,
        'download_media_type': 'VIDEO',
        'save_to_storage': False,
        'automatic_extension': False,
    }
    return CreateTaskIn(**(fields | overrides))


def test_custom_filename_is_optional() -> None:
    assert _create_task().custom_filename is None


def test_explicit_null_custom_filename_is_accepted() -> None:
    assert _create_task(custom_filename=None).custom_filename is None


def test_safe_custom_filename_is_kept() -> None:
    assert _create_task(custom_filename='lesson.mp4').custom_filename == 'lesson.mp4'


@pytest.mark.parametrize('filename', ['', '..', '../etc/passwd', 'a/b.mp4'])
def test_unsafe_custom_filename_is_rejected(filename: str) -> None:
    with pytest.raises(ValidationError):
        _create_task(custom_filename=filename)
