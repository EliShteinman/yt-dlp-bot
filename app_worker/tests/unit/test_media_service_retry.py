import pytest
from pytest_mock import MockerFixture
from yt_shared.enums import TaskStatus
from yt_shared.repositories.task import TaskRepository

from worker.core.media_service import MediaService


@pytest.mark.parametrize(
    ('status', 'error', 'runnable'),
    [
        (TaskStatus.PENDING, None, True),
        (TaskStatus.FAILED, TaskRepository.INTERRUPTED_TASK_ERROR, True),
        (TaskStatus.FAILED, 'Download error', False),
        (TaskStatus.PROCESSING, None, False),
        (TaskStatus.DONE, None, False),
    ],
)
def test_only_new_or_interrupted_tasks_run(
    mocker: MockerFixture, status: TaskStatus, error: str | None, runnable: bool
) -> None:
    task = mocker.Mock(status=status.value, error=error)

    assert MediaService._is_runnable(task) is runnable
