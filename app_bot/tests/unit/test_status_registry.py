import pytest

from bot.core.status.registry import StatusMessageRegistry

KEY = (1, 10, 'https://www.youtube.com/watch?v=aaaaaaaaaaa')


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def registry(clock: FakeClock) -> StatusMessageRegistry:
    return StatusMessageRegistry(retention_seconds=600, clock=clock)


def test_stored_message_is_returned(registry: StatusMessageRegistry) -> None:
    message = object()
    registry.store(KEY, message)

    assert registry.get(KEY) is message


def test_popped_message_is_forgotten(registry: StatusMessageRegistry) -> None:
    registry.store(KEY, object())
    registry.pop(KEY)

    assert registry.get(KEY) is None


def test_finished_key_is_remembered(registry: StatusMessageRegistry) -> None:
    registry.mark_finished(KEY)

    assert registry.is_finished(KEY) is True


def test_finished_key_expires_after_retention(
    registry: StatusMessageRegistry, clock: FakeClock
) -> None:
    registry.mark_finished(KEY)
    clock.now += 601

    assert registry.is_finished(KEY) is False
