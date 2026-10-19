#!/usr/bin/env bash
# Create envs/secrets.env with random Postgres and RabbitMQ passwords.
# Never overwrites an existing file: the passwords are baked into the data
# volumes on their first start, so regenerating them would lock the apps out.
#
# Usage: scripts/generate-secrets.sh
set -euo pipefail

readonly SECRETS_FILE='envs/secrets.env'
readonly PASSWORD_BYTES=24

if [[ -e "$SECRETS_FILE" ]]; then
    echo "$SECRETS_FILE already exists - leaving it untouched."
    exit 0
fi

random_password() { openssl rand -hex "$PASSWORD_BYTES"; }

postgres_password="$(random_password)"
rabbitmq_password="$(random_password)"

umask 077
cat > "$SECRETS_FILE" <<EOF
POSTGRES_PASSWORD=$postgres_password
RABBITMQ_PASSWORD=$rabbitmq_password
RABBITMQ_DEFAULT_PASS=$rabbitmq_password
EOF

echo "Created $SECRETS_FILE (readable by $(id -un) only)."
