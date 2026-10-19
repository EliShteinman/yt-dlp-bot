import asyncio
import traceback
from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from pyrogram.enums import ParseMode
from pyrogram.types import ReplyParameters
from yt_shared.emoji import SUCCESS_EMOJI
from yt_shared.enums import MediaFileType, TaskSource
from yt_shared.rabbit.publisher import RmqPublisher
from yt_shared.schemas.error import ErrorDownloadGeneralPayload
from yt_shared.schemas.media import BaseMedia
from yt_shared.schemas.success import SuccessDownloadPayload
from yt_shared.utils.file import list_files_human, remove_dir
from yt_shared.utils.tasks.tasks import create_task

from bot.core.handlers.abstract import AbstractDownloadHandler
from bot.core.status.formatter import StatusTextFormatter
from bot.core.status.registry import StatusKey
from bot.core.tasks.upload import AbstractUploadTask, AudioUploadTask, VideoUploadTask
from bot.core.utils import bold, is_user_upload_silent


class SuccessDownloadHandler(AbstractDownloadHandler):
    """Handle successfully downloaded media context."""

    _body: SuccessDownloadPayload
    _UPLOAD_TASK_MAP: ClassVar[dict[MediaFileType, AbstractUploadTask]] = {
        MediaFileType.AUDIO: AudioUploadTask,
        MediaFileType.VIDEO: VideoUploadTask,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._rmq_publisher = RmqPublisher()

    async def handle(self) -> None:
        try:
            await self._handle()
        finally:
            self._cleanup()

    async def _handle(self) -> None:
        await self._delete_acknowledgment_message()
        coro_tasks = [
            self._handle_media_object(media_object)
            for media_object in self._body.media.get_media_objects()
        ]
        await asyncio.gather(*coro_tasks)

    async def _upload_with_status(self, media_object: BaseMedia) -> None:
        if not self._shows_status():
            await self._create_upload_task(media_object, progress=None)
            return
        key = self._status_key()
        size = media_object.current_file_size()
        await self._bot.status.show(
            key, StatusTextFormatter.uploading(media_object.title, 0, size), force=True
        )
        try:
            await self._create_upload_task(
                media_object, progress=self._upload_progress(key, media_object.title)
            )
        finally:
            await self._bot.status.finish(key)

    def _upload_progress(
        self, key: StatusKey, title: str | None
    ) -> Callable[[int, int], Awaitable[None]]:
        async def report(sent_bytes: int, total_bytes: int) -> None:
            await self._bot.status.show(
                key, StatusTextFormatter.uploading(title, sent_bytes, total_bytes)
            )

        return report

    def _shows_status(self) -> bool:
        if not self._body.from_chat_id or self._body.context.source is TaskSource.API:
            return False
        return not is_user_upload_silent(
            user=self._receiving_users[0], conf=self._bot.conf
        )

    async def _publish_error_message(self, err: Exception) -> None:
        err_payload = ErrorDownloadGeneralPayload(
            task_id=self._body.task_id,
            message_id=self._body.message_id,
            from_chat_id=self._body.from_chat_id,
            from_chat_type=self._body.from_chat_type,
            from_user_id=self._body.from_user_id,
            message='Upload error',
            url=self._body.context.url,
            context=self._body.context,
            yt_dlp_version=self._body.yt_dlp_version,
            exception_msg=traceback.format_exc(),
            exception_type=err.__class__.__name__,
        )
        await self._rmq_publisher.send_download_error(err_payload)

    async def _handle_media_object(self, media_object: BaseMedia) -> None:
        try:
            if self._upload_is_enabled():
                self._validate_file_size_for_upload(media_object)
                await self._upload_with_status(media_object)
            else:
                await self._send_success_text(media_object)
                self._log.warning(
                    'File "%s" will not be uploaded due to upload configuration',
                    media_object.current_filepath,
                )
        except Exception as err:
            self._log.exception('Upload of "%s" failed', media_object.current_filepath)
            await self._publish_error_message(err)

    def _cleanup(self) -> None:
        root_path = self._body.media.root_path
        self._log.info(
            'Cleaning up task "%s": removing download content directory "%s" with files %s',
            self._body.task_id,
            root_path,
            list_files_human(root_path),
        )
        remove_dir(root_path)

    async def _create_upload_task(
        self,
        media_object: BaseMedia,
        progress: Callable[[int, int], Awaitable[None]] | None,
    ) -> None:
        """Upload video to Telegram chat."""
        upload_task_cls = self._UPLOAD_TASK_MAP[media_object.file_type]
        task_name = upload_task_cls.__name__
        await create_task(
            upload_task_cls(
                media_object=media_object,
                users=self._receiving_users,
                bot=self._bot,
                semaphore=self._bot.upload_slots,
                context=self._body,
                progress=progress,
            ).run(),
            task_name=task_name,
            logger=self._log,
            exception_message='Task "%s" raised an exception',
            exception_message_args=(task_name,),
        )

    @staticmethod
    def _create_success_text(media_object: BaseMedia) -> str:
        text = f'{SUCCESS_EMOJI} {bold("Downloaded")} {media_object.current_filename}'
        if media_object.saved_to_storage:
            text = f'{text}\n💾 {bold("Saved to media storage")}'
        return f'{text}\n📏 {bold("Size")} {media_object.file_size_human()}'

    async def _send_success_text(self, media_object: BaseMedia) -> None:
        text = self._create_success_text(media_object)
        for user in self._receiving_users:
            if not is_user_upload_silent(user=user, conf=self._bot.conf):
                kwargs: dict[str, Any] = {
                    'chat_id': user.id,
                    'text': text,
                    'parse_mode': ParseMode.HTML,
                }
                if self._body.message_id:
                    kwargs['reply_parameters'] = ReplyParameters(
                        message_id=self._body.message_id
                    )
                await self._bot.send_message(**kwargs)

    def _upload_is_enabled(self) -> bool:
        """Check whether upload is allowed for particular user configuration."""
        if self._body.context.source is TaskSource.API:
            return self._bot.conf.telegram.api.upload_video_file

        user = self._bot.allowed_users[self._get_sender_id()]
        return user.upload.upload_video_file

    def _validate_file_size_for_upload(self, media_obj: BaseMedia) -> None:
        if self._body.context.source is TaskSource.API:
            max_file_size = self._bot.conf.telegram.api.upload_video_max_file_size
        else:
            user = self._bot.allowed_users[self._get_sender_id()]
            max_file_size = user.upload.upload_video_max_file_size

        if not media_obj.current_filepath.exists():
            raise ValueError(
                f'{media_obj.file_type} {media_obj.current_filepath} not found'
            )

        _file_size = media_obj.current_file_size()
        if _file_size > max_file_size:
            err_msg = (
                f'{media_obj.file_type} file size of {_file_size} bytes bigger than '
                f'allowed {max_file_size} bytes. Will not upload'
            )
            self._log.warning(err_msg)
            raise ValueError(err_msg) from None
