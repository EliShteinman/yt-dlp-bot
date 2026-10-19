"""Security regression tests for the ffmpeg/ffprobe tasks (RCE hardening).

The tasks must never build a shell string from untrusted filenames. Every
interpolated value has to reach the process as a single, isolated argv element
so shell metacharacters (``$(...)``, backticks, ``;``) cannot be expanded.
"""

from pathlib import Path

import pytest
from yt_shared.enums import DownMediaType
from yt_shared.schemas.media import DownMedia, Video

from worker.core.tasks.abstract import AbstractFfBinaryTask
from worker.core.tasks.encode import EncodeToH264Task
from worker.core.tasks.ffprobe_context import GetFfprobeContextTask
from worker.core.tasks.thumbnail import MakeThumbnailTask

# Valid filename on disk, but a shell-injection payload if ever passed to a shell.
_INJECTION_NAME = '$(id).mp4'


class _ConcreteFfTask(AbstractFfBinaryTask):
    async def run(self) -> None:
        return None


@pytest.fixture
def evil_file(tmp_path: Path) -> Path:
    path = tmp_path / _INJECTION_NAME
    path.write_bytes(b'')
    return path


async def test_run_proc_uses_exec_not_shell(mocker, tmp_path: Path) -> None:
    task = _ConcreteFfTask(file_path=tmp_path / 'x')
    proc = mocker.AsyncMock()
    proc.wait = mocker.AsyncMock(return_value=0)
    exec_mock = mocker.patch(
        'asyncio.create_subprocess_exec', new=mocker.AsyncMock(return_value=proc)
    )
    shell_mock = mocker.patch('asyncio.create_subprocess_shell', new=mocker.AsyncMock())

    await task._run_proc(['ffprobe', '-of', 'json', str(tmp_path / 'x')])

    exec_mock.assert_awaited_once()
    shell_mock.assert_not_called()
    assert exec_mock.await_args.args[0] == 'ffprobe'


async def test_thumbnail_isolates_filename(mocker, evil_file: Path) -> None:
    task = MakeThumbnailTask(
        thumbnail_path=Path('/tmp/out.jpg'),  # noqa: S108
        file_path=evil_file,
        duration=5.0,
        video_ctx=mocker.Mock(),
    )
    run_proc = mocker.patch.object(
        task, '_run_proc', new=mocker.AsyncMock(return_value=None)
    )

    await task._make_thumbnail()

    cmd = run_proc.await_args.args[0]
    assert isinstance(cmd, list)
    assert cmd[0] == 'ffmpeg'
    assert str(evil_file) in cmd


async def test_ffprobe_isolates_filename(mocker, evil_file: Path) -> None:
    task = GetFfprobeContextTask(file_path=evil_file)
    run_proc = mocker.patch.object(
        task, '_run_proc', new=mocker.AsyncMock(return_value=None)
    )

    await task._get_context()

    cmd = run_proc.await_args.args[0]
    assert isinstance(cmd, list)
    assert cmd[0] == 'ffprobe'
    assert cmd[-1] == str(evil_file)


async def test_encode_isolates_filename_and_preserves_opts(
    mocker, tmp_path: Path
) -> None:
    video = Video(
        title='t',
        original_filename=_INJECTION_NAME,
        directory_path=tmp_path,
        file_size=1,
    )
    media = DownMedia(
        audio=None,
        video=video,
        media_type=DownMediaType.VIDEO,
        root_path=tmp_path,
        meta={},
    )
    encode_opts = ('-c:v', 'libx264', '-crf', '22', '-c:a', 'copy')
    task = EncodeToH264Task(
        media=media, encode_opts=encode_opts, check_if_in_final_format=False
    )
    run_proc = mocker.patch.object(
        task, '_run_proc', new=mocker.AsyncMock(return_value=None)
    )

    await task._encode_video()

    cmd = run_proc.await_args.args[0]
    assert isinstance(cmd, list)
    assert cmd[0] == 'ffmpeg'
    assert str(media.video.current_filepath) in cmd
    # Per-host encode options are forwarded verbatim, in order, as separate args.
    assert [*encode_opts] == cmd[
        cmd.index('-c:v') : cmd.index('-c:v') + len(encode_opts)
    ]
