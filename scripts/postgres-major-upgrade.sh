#!/usr/bin/env bash
# Move the yt database to the Postgres major version now set in docker-compose.yml.
# The old data volume is left untouched, so rolling back is just reverting the
# compose change and recreating yt_postgres.
#
# Usage: scripts/postgres-major-upgrade.sh <dump-file> [docker compose options...]
#   e.g. scripts/postgres-major-upgrade.sh ~/db-backups/yt-pre-pg18.sql -p yt
set -euo pipefail

readonly DB_CONTAINER='yt_postgres'
readonly APP_SERVICES=(yt_bot yt_worker yt_api)
readonly ENV_FILE='envs/common.env'
readonly READY_TIMEOUT_SECONDS=60

dump_file="${1:?usage: $0 <dump-file> [docker compose options...]}"
shift
compose_options=("$@")

compose() { docker compose "${compose_options[@]}" "$@"; }
psql_in_db() { docker exec -i "$DB_CONTAINER" psql -v ON_ERROR_STOP=1 -qtA -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"; }
server_version() { psql_in_db -c 'SHOW server_version'; }
row_counts() {
    psql_in_db <<'SQL'
SELECT string_agg(t || '=' || c, ' ' ORDER BY t) FROM (
  SELECT 'cache' t, count(*) c FROM cache UNION ALL
  SELECT 'file', count(*) FROM file UNION ALL
  SELECT 'task', count(*) FROM task UNION ALL
  SELECT 'yt_dlp', count(*) FROM yt_dlp
) counts;
SQL
}

wait_until_ready() {
    for _ in $(seq "$READY_TIMEOUT_SECONDS"); do
        docker exec "$DB_CONTAINER" pg_isready -q -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" && return 0
        sleep 1
    done
    echo "Postgres did not become ready within ${READY_TIMEOUT_SECONDS}s" >&2
    return 1
}

set -a
# shellcheck source=/dev/null
. "$ENV_FILE"
set +a

echo "Stopping apps so nothing writes during the dump: ${APP_SERVICES[*]}"
compose stop "${APP_SERVICES[@]}"

echo "Old server: $(server_version)"
before="$(row_counts)"
echo "Rows before: $before"
docker exec "$DB_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner > "$dump_file"
echo "Dump written to $dump_file ($(wc -c < "$dump_file") bytes)"

echo "Recreating $DB_CONTAINER on the new image and volume"
compose up -d --no-deps --force-recreate yt_postgres
wait_until_ready
echo "New server: $(server_version)"

psql_in_db < "$dump_file" >/dev/null
after="$(row_counts)"
echo "Rows after:  $after"
if [[ "$before" != "$after" ]]; then
    echo "Row counts differ - apps left stopped. Old data is still in the old volume." >&2
    exit 1
fi

echo "Row counts match. Starting apps."
compose up -d --no-deps "${APP_SERVICES[@]}"
