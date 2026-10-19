import pytest
from pytest_mock import MockerFixture

from worker.core.launcher import WorkerLauncher


@pytest.fixture
def launcher(mocker: MockerFixture) -> WorkerLauncher:
    mocker.patch('worker.core.launcher.get_rabbitmq')
    return WorkerLauncher()


@pytest.fixture
def setup_calls(mocker: MockerFixture, launcher: WorkerLauncher) -> list[str]:
    calls: list[str] = []
    for step in (
        '_fail_interrupted_tasks',
        '_setup_rabbit',
        '_set_yt_dlp_version',
        '_create_intermediate_directories',
    ):
        mocker.patch.object(
            launcher,
            step,
            mocker.AsyncMock(side_effect=lambda name=step: calls.append(name)),
        )
    mocker.patch.object(launcher, '_register_shutdown')
    return calls


async def test_interrupted_tasks_are_failed_before_consuming(
    launcher: WorkerLauncher, setup_calls: list[str]
) -> None:
    await launcher._perform_setup()

    assert setup_calls.index('_fail_interrupted_tasks') < setup_calls.index(
        '_setup_rabbit'
    )


async def test_failed_interrupted_tasks_are_logged(
    mocker: MockerFixture,
    launcher: WorkerLauncher,
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def fake_get_db():  # noqa: ANN202
        yield mocker.Mock()

    mocker.patch('worker.core.launcher.get_db', fake_get_db)
    mocker.patch(
        'worker.core.launcher.TaskRepository',
        return_value=mocker.Mock(
            fail_interrupted_tasks=mocker.AsyncMock(return_value=3)
        ),
    )
    await launcher._fail_interrupted_tasks()

    assert 'Marked 3 task(s) interrupted' in caplog.text
