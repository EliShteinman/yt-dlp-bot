import pytest
from yt_shared.enums import DownMediaType

from ytdl_opts.per_host._default import DefaultHost
from ytdl_opts.per_host.twitter import TwitterHost


@pytest.mark.parametrize(
    ('host_cls', 'url'),
    [
        (DefaultHost, 'https://www.youtube.com/watch?v=aaaaaaaaaaa'),
        (TwitterHost, 'https://x.com/user/status/1'),
    ],
)
def test_video_resolution_is_capped(host_cls: type, url: str, tmp_path) -> None:
    ytdl_opts = (
        host_cls(url=url)
        .build_config(media_type=DownMediaType.VIDEO, curr_tmp_dir=tmp_path)
        .ytdl_opts
    )

    assert 'res:1080' in ytdl_opts['format_sort']
