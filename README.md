## yt-dlp-bot - Video Download Telegram Bot 🇺🇦

Simple and reliable self-hosted Video Download Telegram Bot.

Version: 1.8.0. [Release details](RELEASES.md) (read the upgrade steps when coming from 1.7.x).

![frames](.assets/download_success.png)


## Support the development

- [Buy me a coffee](https://www.buymeacoffee.com/terletsky)
- PayPal [![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=MA6RKYAZH9DSA)
- Bitcoin wallet `14kMRS8SvfD2ydMSMEyAmefHV3Yynf9kAd`

## 😂 Features

* Download audio and free videos with Creative Commons (CC) License from [yt-dlp](https://github.com/yt-dlp/yt-dlp) sites to your storage.
* Upload downloaded media to Telegram, picking the best quality that fits the upload limit.
* Download whole playlists: every video is downloaded and sent separately.
* Live status: one message per video shows download and upload progress.
* Interact with the bot in private or group chats.
* Trigger video downloads via link to the API.
* Track download tasks using the API.

## Disclaimer

- Intended to use only with videos that are under Creative Commons (CC) License

## ⚙ Quick Setup

1. Create Telegram bot using [BotFather](https://t.me/BotFather) and get your `token`
2. [Get your Telegram API Keys](https://my.telegram.org/apps) (`api_id` and `api_hash`)
3. [Find your Telegram User ID](https://stackoverflow.com/questions/32683992/find-out-my-own-user-id-for-sending-a-message-with-telegram-api)
4. Copy `app_bot/config-example.yml` to `app_bot/config.yml` (it is mounted into the
   bot container at runtime; restart the bot after editing it)
5. Write `token`, `api_id`, `api_hash` to `app_bot/config.yml` by changing respective
   placeholders
6. Write your Telegram user or group ID to the `allowed_users` -> `id` by replacing dummy
   value and change `forward_group_id` value if you want to forward the video to
   some group/channel when upload is enabled. Bot should be added to the group/channel to be able to send messages.
7. Change download media type for the user/group: `AUDIO`, `VIDEO` or `AUDIO_VIDEO`
   in `app_bot/config.yml`'s variable `download_media_type`. Default `VIDEO`
8. If you want your downloaded audio/video to be uploaded back to the Telegram, set `upload_video_file` config variable 
   for your user/group in the `app_bot/config.yml` to `True`
9. Media `STORAGE_PATH` environment variable is located in
   the `envs/worker.env` file. By default, it's `/filestorage` path inside the
   container. What you want is to map the real path to this inside
   the `docker-compose.yml` file for the `yt_worker` service, e.g. if you're on Windows, next
   strings mean container path `/filestorage` is mapped to real `D:/Videos` so your
   videos will be saved to your `Videos` folder.
   ```yml
     yt_worker:
       volumes:
         - "D:/Videos:/filestorage"
   ```
   The worker runs as UID 1000, so the host directory must be writable by it
   (e.g. `sudo chown 1000:1000 /data/downloads`).
10. Change application's `LOG_LEVEL` in `envs/common.env` to `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` if needed
11. Create `envs/secrets.env` with the database and message broker passwords, either by
    generating random ones (an existing file is never overwritten):
    ```bash
    scripts/generate-secrets.sh
    ```
    or by hand from `envs/secrets.env.example` (keep `RABBITMQ_DEFAULT_PASS` equal to
    `RABBITMQ_PASSWORD`). Postgres and RabbitMQ store the password on their first start, so
    changing the file later also requires changing the password inside them.

## 🏃 Run

```bash
# Build base image
docker compose build base-image

# Build and run all services in detached mode
docker compose up --build -d -t 0 && docker compose logs --tail 100 -f

# Stop all services
docker compose stop -t 0
```

For development, install the git hooks once (Ruff, shellcheck, secret scanning run before every commit):

```bash
uvx pre-commit install
```

Run a component's tests the way CI does (`yt_shared`, `app_worker`, `app_bot`, `app_api`):

```bash
export UV_PROJECT_ENVIRONMENT=$PWD/.venv-test
(cd yt_shared && uv sync --frozen --no-install-project)
(cd app_worker && uv sync --frozen --no-install-project --inexact)
uv pip install --python .venv-test/bin/python -e ./yt_shared pytest pytest-asyncio pytest-mock pytest-cov
cd app_worker && ../.venv-test/bin/python -m pytest -m "not network"
```

Your Telegram Bot should send you a startup message:
`✨ <YOUR_BOT_NAME> started, paste a video URL(s) to start download` and that's it. After
pasting video URL(s) the bot keeps one status message per video up to date while it
downloads and uploads, and removes it when the video arrives. For a playlist it first
tells you how many videos were queued. If something goes wrong you get an error message.

## 💻 Advanced setup

1. If you want to change `yt-dlp` download options, go to the `app_worker/ytdl_opts`
   directory, copy content from `default.py` to `user.py` and modify as you wish by
   checking [available options](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L180).
2. Default max simultaneous video downloads by worker service is 2. Change
   the `MAX_SIMULTANEOUS_DOWNLOADS` variable in `envs/worker.env` to desired value but
   keep in mind that downloads are stored in the `shared-tmpfs` volume, a tmpfs that lives in
   RAM. Its maximum size is the `size=` option in `docker-compose.yml` (27168m by default);
   it is not reserved up front, but filling it uses memory, so set it below your free RAM and
   large enough for the videos downloaded at once.
   A playlist is split into at most `MAX_PLAYLIST_ITEMS` videos (default 50).
3. `yt-dlp` will try to download video thumbnail if it exists. In other case Worker
   service (particularly the FFmpeg process) will make a JPEG thumbnail from the
   video. It's needed when you choose to upload the video to the Telegram chat. By
   default, it will try to make it on the 10th second of the video, but if the video is
   shorter, it will make it on `video length / 2` time point because the FFmpeg process
   will error out. Change the `THUMBNAIL_FRAME_SECOND` variable if needed in
   the `envs/worker.env` file.
4. Telegram limits uploads by the account that uploads, which here is the bot: 2GB
   (2147483648 bytes), reflected in `upload_video_max_file_size` in the example config.
   The 4GB Telegram Premium limit belongs to user accounts, so a Premium recipient does
   not raise it. The worker picks the
   best format whose size fits `MAX_VIDEO_FILESIZE` in `envs/worker.env` (default `1900M`,
   leaving room for audio and size estimates); remove it for no limit. Uncomment
   `MAX_VIDEO_HEIGHT` there to also cap the resolution (e.g. `1080`).
5. If the website you want to download from requires authentication you can use your cookies by putting them into
   the `app_worker/cookies/cookies.txt` file in the Netscape format.
6. Live status updates: the worker reports download progress every
   `PROGRESS_REPORT_INTERVAL_SECONDS` (`envs/worker.env`), and the bot edits a status
   message at most every `TG_STATUS_EDIT_INTERVAL_SECONDS` (`envs/bot.env`) to stay within
   Telegram's rate limits.
7. A job that keeps failing is retried `CONSUMER_NUMBER_OF_RETRY` times and then moved to
   the `dead.q` RabbitMQ queue. Long downloads and uploads may stay unacknowledged for up
   to `RABBITMQ_CONSUMER_TIMEOUT_MS` (`envs/common.env`, default 6 hours).

## 🛑 Failed download

If your URL can't be downloaded for some reason, you will see a message with error
details

![frames](.assets/download_failed.png)

## Access

- **API**: `127.0.0.1:1984` on the host, no auth, so it is not reachable from the
  network. Port and binding can be changed in `docker-compose.yml`.
- **RabbitMQ**: user `yt` (`RABBITMQ_USER` in `envs/common.env`), password in `envs/secrets.env`; AMQP on `127.0.0.1:25672`,
  management UI on `127.0.0.1:15672`.
- **PostgreSQL**: user `yt` (`POSTGRES_USER` in `envs/common.env`), password in `envs/secrets.env`; `127.0.0.1:5435`.

Use an SSH tunnel to reach them from another machine.

## API

By default, API service will run on your `localhost` and `1984` port. API endpoint
documentations lives at `http://127.0.0.1:1984/docs`. A playlist URL sent to the API is
split into one task per video; the id returned for the playlist itself is not tracked.

| Endpoint                                                           | Method   | Description                                                                                                                                |
|--------------------------------------------------------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `/status`                                                          | `GET`    | Get API healthcheck status, usually response is `{"status": "OK"}`                                                                         |
| `/api/v1/yt-dlp/?release_channel=NIGHTLY`                          | `GET`    | Get latest (`NIGHTLY`, `STABLE` or `MASTER`) and currently installed `yt-dlp` version                                                      |
| `/api/v1/tasks/?include_meta=False&status=DONE`                    | `GET`    | Get all tasks with filtering options like to include large file metadata and by task status: `PENDING`, `PROCESSING`, `FAILED` and `DONE`. |
| `/api/v1/tasks/f828714a-5c50-45de-87c0-3b51b7e04039?include_meta=True` | `GET`    | Get info about task by ID                                                                                                                  |
| `/api/v1/tasks/latest?include_meta=True`                           | `GET`    | Get info about latest task                                                                                                                 |
| `/api/v1/tasks/f828714a-5c50-45de-87c0-3b51b7e04039`               | `DELETE` | Delete task by ID                                                                                                                          |
| `/api/v1/tasks/`                                                   | `POST`   | Create a download task (see example below; `custom_filename` is optional)                                                                 |
| `/api/v1/tasks/stats`                                              | `GET`    | Get overall tasks stats                                                                                                                    |

### API examples

1. `GET http://localhost:1984/api/v1/tasks/?include_meta=False&status=DONE&limit=2&offset=0`

   Response
   ```json
   [
       {
           "id": "7ab91ef7-461c-4ef6-a35b-d3704fe28e6c",
           "added_at": "2026-10-19T19:07:43.308683",
           "created": "2026-10-19T19:10:21.968421",
           "updated": "2026-10-19T19:10:51.681729",
           "status": "DONE",
           "url": "https://www.youtube.com/watch?v=PavYAOpVpJI",
           "source": "BOT",
           "from_user_id": 123456789,
           "message_id": 621,
           "yt_dlp_version": "2026.10.10.233141",
           "error": null,
           "files": [
               {
                   "id": "4b1c63ed-3e32-43e6-a0b7-c7fc8713b268",
                   "created": "2026-10-19T19:10:51.675802",
                   "updated": "2026-10-19T19:10:51.675810",
                   "title": "[Drone Freestyle] Mountain Landscape With Snow | Free Stock Footage | Creative Common Video",
                   "name": "[Drone Freestyle] Mountain Landscape With Snow | Free Stock Footage | Creative Common Video.mp4",
                   "thumb_name": "[Drone Freestyle] Mountain Landscape With Snow | Free Stock Footage | Creative Common Video.jpg",
                   "duration": 300,
                   "width": 1920,
                   "height": 1080,
                   "cache": null
               }
           ]
       }
   ]
   ```
2. `POST http://localhost:1984/api/v1/tasks/`

   Request
   ```json
   {
       "url": "https://www.youtube.com/watch?v=PavYAOpVpJI",
       "download_media_type": "AUDIO_VIDEO",
       "save_to_storage": false,
       "custom_filename": "cool.mp4",
       "automatic_extension": false
   }
   ```
   Response
   ```json
   {
       "id": "5ac05808-b29c-40d6-b250-07e3e769d8a6",
       "url": "https://www.youtube.com/watch?v=PavYAOpVpJI",
       "source": "API",
       "added_at": "2022-02-14T00:35:25.419962+00:00"
   }
   ```
3. `GET http://localhost:1984/api/v1/tasks/stats`

   Response
   ```json
   {
       "total": 39,
       "unique_urls": 5,
       "pending": 0,
       "processing": 0,
       "failed": 26,
       "done": 13
   }
   ```
