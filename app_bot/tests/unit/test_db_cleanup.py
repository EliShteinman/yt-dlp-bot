from pytest_mock import MockerFixture

from bot.core.tasks.db_cleanup import DbCleanupTask


async def test_cleanup_is_skipped_without_opted_out_users(
    mocker: MockerFixture,
) -> None:
    delete_data = mocker.patch.object(DbCleanupTask, '_delete_data')
    await DbCleanupTask(user_ids=()).run()

    delete_data.assert_not_called()
