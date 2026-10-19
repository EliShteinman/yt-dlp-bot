import pytest
from pytest_mock import MockerFixture
from sqlalchemy.dialects import postgresql
from yt_shared.enums import TaskStatus
from yt_shared.repositories.task import TaskRepository


@pytest.fixture
def db(mocker: MockerFixture) -> object:
    return mocker.Mock(
        execute=mocker.AsyncMock(return_value=mocker.Mock(rowcount=4)),
        commit=mocker.AsyncMock(),
    )


@pytest.fixture
def repository(db: object) -> TaskRepository:
    return TaskRepository(db=db)


def _executed_sql(db: object) -> str:
    statement = db.execute.await_args.args[0]
    return str(
        statement.compile(
            dialect=postgresql.dialect(), compile_kwargs={'literal_binds': True}
        )
    )


async def test_purge_without_users_deletes_nothing(
    repository: TaskRepository, db: object
) -> None:
    await repository.purge_user_tasks(user_ids=())

    db.execute.assert_not_awaited()


async def test_purge_targets_only_listed_users(
    repository: TaskRepository, db: object
) -> None:
    await repository.purge_user_tasks(user_ids=(111,))

    assert 'from_user_id IN (111)' in _executed_sql(db)


async def test_purge_keeps_tasks_without_user(
    repository: TaskRepository, db: object
) -> None:
    await repository.purge_user_tasks(user_ids=(111,))

    assert 'IS NULL' not in _executed_sql(db)


async def test_fail_interrupted_targets_processing_tasks(
    repository: TaskRepository, db: object
) -> None:
    await repository.fail_interrupted_tasks()

    assert f"status = '{TaskStatus.PROCESSING.value}'" in _executed_sql(db)


async def test_fail_interrupted_marks_tasks_failed(
    repository: TaskRepository, db: object
) -> None:
    await repository.fail_interrupted_tasks()

    assert f"status='{TaskStatus.FAILED.value}'" in _executed_sql(db)


async def test_fail_interrupted_returns_affected_count(
    repository: TaskRepository,
) -> None:
    assert await repository.fail_interrupted_tasks() == 4
