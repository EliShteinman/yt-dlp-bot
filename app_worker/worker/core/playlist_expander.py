import logging
from itertools import islice

import yt_dlp
from yt_dlp.utils import DownloadError

from worker.core.config import settings
from worker.utils import cli_to_api

try:
    from ytdl_opts.user import PLAYLIST_EXPAND_YTDL_OPTS
except ImportError:
    from ytdl_opts.default import PLAYLIST_EXPAND_YTDL_OPTS


class PlaylistExpander:
    """Resolve a playlist URL into the URLs of its entries without downloading."""

    _PLAYLIST_TYPE = 'playlist'

    def __init__(
        self,
        cli_opts: tuple[str, ...] = PLAYLIST_EXPAND_YTDL_OPTS,
        max_items: int = settings.MAX_PLAYLIST_ITEMS,
    ) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._ytdl_opts: dict = cli_to_api(list(cli_opts))
        self._max_items = max_items

    def expand(self, url: str) -> list[str]:
        try:
            meta = self._extract_unprocessed_info(url)
        except DownloadError:
            self._log.warning('Could not inspect "%s" for playlist entries', url)
            return []

        if not meta or meta.get('_type') != self._PLAYLIST_TYPE:
            self._log.debug('"%s" is not a playlist', url)
            return []

        entry_urls = self._collect_entry_urls(meta)
        self._log.info('Expanded playlist "%s" into %d entries', url, len(entry_urls))
        return entry_urls

    def _extract_unprocessed_info(self, url: str) -> dict | None:
        with yt_dlp.YoutubeDL(self._ytdl_opts) as ytdl:
            return ytdl.extract_info(url, download=False, process=False)

    def _collect_entry_urls(self, meta: dict) -> list[str]:
        entries = (entry for entry in meta.get('entries') or [] if entry)
        entry_urls = (entry['url'] for entry in entries if entry.get('url'))
        return list(islice(entry_urls, self._max_items))
