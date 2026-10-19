from yt_shared.utils.common import format_bytes

from bot.core.utils import bold

_SECONDS_PER_MINUTE = 60


class StatusTextFormatter:
    """Texts of the live status messages."""

    @staticmethod
    def playlist_queued(entry_count: int) -> str:
        return f'📋 {bold(f"Playlist: {entry_count} videos queued for download")}'

    @classmethod
    def downloading(
        cls,
        title: str | None,
        downloaded_bytes: int | None,
        total_bytes: int | None,
        speed: float | None,
        eta: int | None,
    ) -> str:
        details = [cls._progress(downloaded_bytes, total_bytes)]
        if speed:
            details.append(f'{format_bytes(int(speed))}/s')
        if eta is not None:
            details.append(f'{cls._duration(eta)} left')
        return cls._compose('⬇️', 'Downloading', title, details)

    @classmethod
    def uploading(cls, title: str | None, sent_bytes: int, total_bytes: int) -> str:
        return cls._compose(
            '⬆️', 'Uploading', title, [cls._progress(sent_bytes, total_bytes)]
        )

    @staticmethod
    def _compose(icon: str, action: str, title: str | None, details: list[str]) -> str:
        header = f'{icon} {bold(action)}'
        if title:
            header = f'{header} {title}'
        return f'{header}\n{" · ".join(item for item in details if item)}'

    @staticmethod
    def _progress(done_bytes: int | None, total_bytes: int | None) -> str:
        if not total_bytes:
            return format_bytes(done_bytes) if done_bytes else ''
        percent = min(100, int((done_bytes or 0) * 100 / total_bytes))
        return f'{percent}% · {format_bytes(done_bytes or 0)} / {format_bytes(total_bytes)}'

    @staticmethod
    def _duration(seconds: int) -> str:
        minutes, seconds = divmod(seconds, _SECONDS_PER_MINUTE)
        return f'{minutes}:{seconds:02d}'
