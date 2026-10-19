FROM python:3.14-alpine3.24

ARG APP_UID=1000
ARG APP_GID=1000

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV UV_PYTHON_DOWNLOADS=never

RUN apk add --no-cache \
        tzdata \
        htop \
        bash

WORKDIR /app

RUN addgroup -g "$APP_GID" app \
    && adduser -D -u "$APP_UID" -G app app \
    && chown app:app /app

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./yt_shared/uv.lock,target=uv.lock \
    --mount=type=bind,source=./yt_shared/pyproject.toml,target=pyproject.toml \
    uv venv /opt/venv && uv sync --frozen --no-install-project
