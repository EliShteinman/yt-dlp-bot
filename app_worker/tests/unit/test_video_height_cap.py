import pytest
from yt_shared.enums import DownMediaType

from worker.utils import build_resolution_sort_key
from ytdl_opts.per_host._default import DefaultHost
from ytdl_opts.per_host.twitter import TwitterHost


@pytest.mark.parametrize(
    ('max_height', 'expected'),
    [(None, 'res'), (1080, 'res:1080'), (2160, 'res:2160')],
)
def test_resolution_sort_key(max_height: int | None, expected: str) -> None:
    assert build_resolution_sort_key(max_height) == expected


@pytest.mark.parametrize(
    ('host_cls', 'url'),
    [
        (DefaultHost, 'https://www.youtube.com/watch?v=aaaaaaaaaaa'),
        (TwitterHost, 'https://x.com/user/status/1'),
    ],
)
def test_resolution_is_uncapped_by_default(host_cls: type, url: str, tmp_path) -> None:
    ytdl_opts = (
        host_cls(url=url)
        .build_config(media_type=DownMediaType.VIDEO, curr_tmp_dir=tmp_path)
        .ytdl_opts
    )

    assert ytdl_opts['format_sort'][0] == 'res'
