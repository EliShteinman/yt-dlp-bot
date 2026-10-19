import pytest
from pytest_mock import MockerFixture
from yt_shared.enums import DownMediaType, ProgressStage, TaskSource, TelegramChatType
from yt_shared.schemas.media import InbMediaPayload

from worker.core.progress_reporter import DownloadProgressReporter

VIDEO_URL = 'https://www.youtube.com/watch?v=aaaaaaaaaaa'
DOWNLOADING = {
    'status': 'downloading',
    'downloaded_bytes': 512,
    'total_bytes_estimate': 2048.0,
    'speed': 256,
    'eta': 6.0,
    'info_dict': {'title': 'Lesson 1'},
}


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def media_payload() -> InbMediaPayload:
    return InbMediaPayload(
        from_chat_id=1,
        from_chat_type=TelegramChatType.PRIVATE,
        from_user_id=1,
        message_id=10,
        ack_message_id=11,
        url=VIDEO_URL,
        original_url=VIDEO_URL,
        source=TaskSource.BOT,
        save_to_storage=False,
        download_media_type=DownMediaType.VIDEO,
        custom_filename=None,
        automatic_extension=False,
    )


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def scheduled(mocker: MockerFixture) -> object:
    return mocker.patch(
        'worker.core.progress_reporter.asyncio.run_coroutine_threadsafe',
        side_effect=lambda coro, _loop: coro.close(),
    )


@pytest.fixture
def publisher(mocker: MockerFixture) -> object:
    return mocker.Mock(send_progress=mocker.AsyncMock())


@pytest.fixture
def reporter(
    media_payload: InbMediaPayload, publisher: object, clock: FakeClock
) -> DownloadProgressReporter:
    return DownloadProgressReporter(
        media_payload=media_payload,
        publisher=publisher,
        loop=object(),
        interval_seconds=5,
        clock=clock,
    )


def _reported(publisher: object) -> object:
    return publisher.send_progress.call_args.args[0]


def test_first_progress_is_reported(
    reporter: DownloadProgressReporter, scheduled: object
) -> None:
    reporter.hook(DOWNLOADING)

    assert scheduled.call_count == 1


def test_progress_within_interval_is_throttled(
    reporter: DownloadProgressReporter, scheduled: object, clock: FakeClock
) -> None:
    reporter.hook(DOWNLOADING)
    clock.now += 4.9
    reporter.hook(DOWNLOADING)

    assert scheduled.call_count == 1


def test_progress_after_interval_is_reported(
    reporter: DownloadProgressReporter, scheduled: object, clock: FakeClock
) -> None:
    reporter.hook(DOWNLOADING)
    clock.now += 5
    reporter.hook(DOWNLOADING)

    assert scheduled.call_count == 2


@pytest.mark.parametrize('status', ['finished', 'error'])
def test_non_downloading_status_is_ignored(
    reporter: DownloadProgressReporter, scheduled: object, status: str
) -> None:
    reporter.hook({**DOWNLOADING, 'status': status})

    scheduled.assert_not_called()


@pytest.mark.usefixtures('scheduled')
def test_report_targets_the_requesting_chat(
    reporter: DownloadProgressReporter, publisher: object
) -> None:
    reporter.hook(DOWNLOADING)
    payload = _reported(publisher)

    assert (payload.from_chat_id, payload.message_id, payload.url) == (
        1,
        10,
        VIDEO_URL,
    )


@pytest.mark.usefixtures('scheduled')
def test_report_carries_download_figures(
    reporter: DownloadProgressReporter, publisher: object
) -> None:
    reporter.hook(DOWNLOADING)
    payload = _reported(publisher)

    assert (
        payload.stage,
        payload.title,
        payload.downloaded_bytes,
        payload.total_bytes,
        payload.speed,
        payload.eta,
    ) == (ProgressStage.DOWNLOADING, 'Lesson 1', 512, 2048, 256.0, 6)
