## Release 1.8.0

Release date: October 19, 2026

## New Features

- Playlists: a playlist link downloads every video (up to `MAX_PLAYLIST_ITEMS`,
  default 50), each one as a separate task. A video link that merely carries a
  `list=` parameter still downloads just that video.
- Live status: one message per video that updates itself with download
  progress (percent, size, speed, time left), then upload progress, and is
  removed when the video arrives. Playlists get a "N videos queued" message.
  Users with `silent: true` get no status messages.
- Best quality that fits: `MAX_VIDEO_FILESIZE` (default `1900M`) picks the best
  format whose size, known before downloading, fits Telegram's 2 GB bot upload
  limit, and fails immediately when none does. Optional `MAX_VIDEO_HEIGHT` caps
  the resolution (off by default).
- Failed and interrupted jobs are no longer lost: messages are acknowledged only
  after they are handled, survive a broker restart, are retried a limited number
  of times and then kept in a `dead.q` dead-letter queue.

## Important (upgrading from 1.7.x)

Back up your database first, then, in this order:

1. `git pull`, then create `envs/secrets.env` (Postgres and RabbitMQ no longer use
   the defaults from git) with random passwords, or by hand from
   `envs/secrets.env.example`:
   ```bash
   scripts/generate-secrets.sh
   ```
2. Rebuild everything on the new base image:
   ```bash
   docker compose build --pull base-image && docker compose build
   ```
3. Stop the apps **before** replacing RabbitMQ (old apps would recreate the old
   queues and the new apps would fail with `PRECONDITION_FAILED`), then start
   RabbitMQ, Redis and the PO token provider on fresh volumes:
   ```bash
   docker compose stop yt_bot yt_worker yt_api
   docker compose up -d -V --no-deps --force-recreate yt_rabbitmq yt_redis yt_pot_provider
   ```
4. Move the database to Postgres 18 (dumps it, starts Postgres 18 on a new
   `pgdata18` volume, restores, checks row counts, starts the apps):
   ```bash
   scripts/postgres-major-upgrade.sh ~/yt-pre-pg18.sql
   ```
   The old `pgdata` volume is left untouched for rollback; remove it once
   everything works.
5. The bot, worker and API now run as UID 1000. If you use `save_to_storage`,
   make the host storage directory writable for it, e.g.
   `sudo chown 1000:1000 /data/downloads`.

Other changes you may notice:

- `app_bot/config.yml` is mounted into the container at runtime instead of
  being copied into the image; the bot refuses to start if it is missing.
- New environment variables: `MAX_PLAYLIST_ITEMS`, `MAX_VIDEO_FILESIZE`,
  `MAX_VIDEO_HEIGHT`, `PROGRESS_REPORT_INTERVAL_SECONDS` (worker);
  `TG_STATUS_EDIT_INTERVAL_SECONDS`, `TG_STATUS_RETENTION_SECONDS` (bot);
  `CONSUMER_NUMBER_OF_RETRY`, `RABBITMQ_CONSUMER_TIMEOUT_MS`,
  `RABBITMQ_PROGRESS_TTL_MS` (common).
- API: `custom_filename` is optional when creating a task.
- Postgres and RabbitMQ ports are published on `127.0.0.1` only.

## Security

- Remote code execution through crafted URLs/filenames passed to ffmpeg fixed
  (commands run without a shell); download URLs and custom filenames are
  validated.
- PO token provider upgraded to 2.0.2 (fixes an RCE in the provider server).
- Containers run as an unprivileged user with all capabilities dropped; the API,
  Postgres and RabbitMQ listen on localhost only; generated passwords instead of
  `yt/yt` and `guest/guest`; the Telegram config is no longer baked into images.

## Platform

- Python 3.14, Alpine 3.24 (ffmpeg 8.1, Node.js 24), Postgres 18, RabbitMQ 4.3,
  Redis 8, all Python dependencies upgraded.
- The Telegram library moved from the archived `pyrofork` to `kurigram`.
- The bundled `yt-dlp-ejs` solver is installed, so YouTube no longer hides
  higher-quality formats.

## Fixes

- `MAX_SIMULTANEOUS_DOWNLOADS` and `max_upload_tasks` were never enforced.
- Tasks interrupted by a worker restart stayed `PROCESSING` forever.
- The bot deleted the history of API tasks every minute.
- Clearer errors when a download produced no file; error messages are logged and
  no longer leave the "processing" message behind.

## Development

- pre-commit hooks (Ruff, shellcheck, gitleaks) and a GitHub Actions workflow
  running lint and the test suites of all four components.

---

## Release 1.7.3

Release date: July 24, 2026

## New Features

- Provide YouTube PO Tokens via the `bgutil-ytdlp-pot-provider` HTTP sidecar to
  avoid throttling and missing formats.

## Important

- YouTube extraction now requires a JavaScript runtime. The worker image ships
  Node.js 22 (Alpine 3.22) and enables it via `--js-runtimes node`. Deno was
  dropped: its Alpine package is too old and it does not run on musl.
- A new `yt_pot_provider` service was added to `docker-compose.yml`. Rebuild the
  base image and worker, then `docker compose up -d`.
- A new `POT_PROVIDER_BASE_URL` variable was added to `envs/worker.env`
  (defaults to `http://yt_pot_provider:4416`).
- If you previously copied `app_worker/ytdl_opts/default.py` to `user.py`,
  re-copy or merge these changes, otherwise the JS-runtime, PO-token and
  format-sort fixes will not apply to your downloads.

## Misc

- Removed the deprecated `h264` field from `--format-sort`.

---

## Release 1.7

Release date: May 30, 2024

## New Features

- Choose `yt-dlp` release channel between `NIGHTLY`, `STABLE` or `MASTER`. Default is `NIGHTLY`.

## Important

- Update your `app_bot/config.yaml` with new `release_channel: "NIGHTLY"` line in `ytdlp` section
- `app_worker/requirements.txt` includes `NIGHTLY` `yt-dlp` package to install.

## Misc

N/A

---

## Release 1.6

Release date: April 25, 2024

## New Features

 - Ability to set custom video name in `POST` API request:
   ```json
    {
        "url": "<VIDEO_URL>",
        "download_media_type": "VIDEO",
        "save_to_storage": true,
        "custom_filename": "your cool custom name and extension.mp4",
        "automatic_extension": false
    }
   ```
 - Saving into storage with the same name won't overwrite the file but append timestamp to the filename.

## Important

N/A

## Misc

N/A

---

## Release 1.5

Release date: March 20, 2024

## New Features

N/A

## Important

N/A

## Misc

- Migrated from Pyrogram to Pyrofork
- Migrated from Python 3.11 to 3.12

---

## Release 1.4.5

Release date: November 23, 2023

## New Features

N/A

## Important

N/A

## Misc

- Improved error handling

---

## Release 1.4.4

Release date: November 11, 2023

## New Features

- New boolean config variable per user `is_admin`. Currently, admin users will receive update message when `yt-dlp` needs update.
  ```yaml
  allowed_users:
    - id: 11111111111
      is_admin: !!bool True
      ***
  ```

## Important

- Every user in the config must include this new config variable whether it's `True` or `False`

## Misc

N/A

---

## Release 1.4.3

Release date: September 20, 2023

## New Features

- Encode Instagram VP9 videos to H264 (not played in Telegram on iOS)
- New environment variable in `envs/.env_worker`: `INSTAGRAM_ENCODE_TO_H264=True`

## Important

N/A

## Misc

- Maintenance and refactor

---

## Release 1.4.2

Release date: July 06, 2023

## New Features

- Use cookies for website auth for download by putting them into the `app_worker/cookies/cookies.txt` file in Netscape
  format.

## Important

- If you are using the customized yt-dlp options in the `app_worker/ytdl_opts/user.py` you must reconfigure them from
  the updated `app_worker/ytdl_opts/default.py`.

## Misc

N/A

---

## Release 1.4.1

Release date: March 29, 2023

## New Features

N/A

## Important

N/A

## Misc

 - Maintenance release: added `uvloop`.

---

## Release 1.4

Release date: March 29, 2023

## New Features

- Enable or disable URL match against the regex. If you use the bot in the group with
  other people and don't want the bot to try to download any text message sent to the
  group, you can enable `use_url_regex_match: !!bool True` in the `app_bot/config.yml`
  so the bot will skip messages not matching URL regexes. You can add your own if
  needed.

## Important

1. Two new variables introduced in the `app_bot/config-example.yml`
    1. ```yaml
       url_validation_regexes:
         - "^http(s)?:\\/\\/.+$"
       ```
    2. ```yaml
       use_url_regex_match: !!bool True
       ```

## Misc

N/A

---

## Release 1.3

Release date: March 28, 2023

## New Features

- Now any user which is in the configured group with the bot can send the link

## Important

N/A

## Misc

N/A

---

## Release 1.2.1

Release date: March 22, 2023

## New Features

N/A (Maintenance release)

## Important

1. Disabled SQL logs by default: `SQLALCHEMY_ECHO=False` in `envs/.env_common`

## Misc

1. Improved upload log messages - now include file size and whether upload of the file is cached

---

## Release 1.2

Release date: March 13, 2023

## New Features

- Show message when media was saved to storage.

## Important

N/A

## Misc

N/A

---

## Release 1.1

Release date: March 11, 2023

## New Features

- Show uploaded file size in human-readable format.

## Important

* Added new config variable `include_size: !!bool True` for displaying uploaded file
  size.

## Misc

N/A

---

## Release 1.0

Release date: February 25, 2023

## New Features

1. Now bot can download audio (mp3), video (default), or both. Just configure the
   preferred mode for the particular user/group.

## Important

1. Changed content yt-dlp options in `app_worker/ytdl_opts/default.py`
2. Added two new user config options in `app_bot/config-example.yml`:
    1. `download_media_type`: What to download - audio (mp3), video or both. Values can
       be `AUDIO`, `VIDEO`, `AUDIO_VIDEO`.
    2. `save_to_storage`: Moved from `envs/.env_worker`
3. Creating task on API now requires previously mentioned two fields in payload to be
   sent.

## Misc

N/A


---

## Release 0.9

Release date: February 16, 2023

## New Features

N/A

## Important

1. Changed format of `YTDL_OPTS` in `app_worker/ytdl_opts/default.py` from `dict`
   to `list` for proper parsing on `yt_dlp` side:
   ```python
   # Old format
   YTDL_OPTS = {
       'outtmpl': '%(title).200B.%(ext)s',
       'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
       'noplaylist': True,
       'playlist_items': '1:1',
       'writethumbnail': True,
       'concurrent_fragment_downloads': 5,
   }
   
   # New format
   YTDL_OPTS = [
       '--output',
       '%(title).200B.%(ext)s',
       '--format',
       'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
       '--no-playlist',
       '--playlist-items',
       '1:1',
       '--write-thumbnail',
       '--convert-thumbnails',
       'jpg',
       '--concurrent-fragments',
       '5',
       '--verbose',
   ]
   ```
   This means only `yt-dlp` CLI options can be added (`yt-dlp --help` to list all of
   them).

## Misc

N/A

---

## Release 0.8

Release date: February 15, 2023

## New Features

1. yt-dlp will now try to download video thumbnail if it exists. This is done by
   setting `'writethumbnail': True` in `app_worker/ytdl_opts/default.py`. If thumbnail
   wasn't downloaded, `ffmpeg` task will create it as previously.

## Important

N/A

## Misc

N/A

---

## Release 0.7

Release date: February 5, 2023

## New Features

N/A

## Important

1. Configuration variable `TMP_DOWNLOAD_PATH` renamed to `TMP_DOWNLOAD_ROOT_PATH`
   in `envs/.env_common`.
2. Added 2 new configuration variables `TMP_DOWNLOAD_DIR` and `TMP_DOWNLOADED_DIR`
   to `envs/.env_common`.
3. Fixed bug [#52](https://github.com/tropicoo/yt-dlp-bot/issues/52).

## Misc

N/A


---

## Release 0.6

Release date: January 31, 2023

## New Features

N/A

## Important

N/A

## Misc

1. API bugfixes
2. Renamed microservices directories, e.g. `api` -> `app_api`

---

## Release 0.5

Release date: January 21, 2023

## New Features

1. Updated handling failed video download logic. In case of failed post-processing by
   yt-dlp, the (broken) video file could still remain in the temporary directory.
   This update handles this potential issue.

## Important

N/A

## Misc

N/A

---

## Release 0.4

Release date: November 13, 2022

## New Features

N/A

## Important

1. Changed default yt-dlp options in `worker/ytdl_opts/default.py`.
   Replaced `'max_downloads': 1` with `'playlist_items': '1:1'`
   to properly handle the result.
2. It's important to know that the worker backend does not handle downloading more than
   one video from the playlist even if you change yt-dlp options. Only the first video
   will be downloaded and processed.

## Misc

N/A

---

## Release 0.3.1

Release date: November 11, 2022

## New Features

* This is maintenance release. No New Features. Bumped `fastapi` and `SQLAlchemy`
  versions, updated README.

## Important

N/A

## Misc

N/A

---

## Release 0.3

Release date: November 7, 2022

## New Features

1. New or changed config variables in `bot/config-template.yml`:
    1. `send_startup_message` - send startup messages (per user in config) or not
    2. Fixed typo in `upload_vide_file` -> `upload_video_file`
    3. `ytdlp_version_check_interval` variable replaced with a new `ytdlp` config
       section:
        1. `version_check_enabled` - check for the new `yt-dlp` version or not
        2. `version_check_interval` - check interval in seconds when enabled,
           default `86400` (24 hours)
        3. `notify_users_on_new_version` - send a notification to Telegram chats about
           the new `yt-dlp` version or not (only log records will contain the message
           about the new version) for every user in the config

## Important

1. Default config template `bot/config-template.yml` was changed, reconfiguration needed

## Misc

1. Updated README
