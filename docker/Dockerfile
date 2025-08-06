FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/

ENV APP_USER=email-sender
ENV APP_HOME=/app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY uv.lock pyproject.toml /
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_USER=email-sender
ENV APP_HOME=/app

RUN useradd -ms /bin/bash $APP_USER
RUN mkdir -p $APP_HOME && chown $APP_USER:$APP_USER -R $APP_HOME

WORKDIR $APP_HOME
COPY --link --chown=$APP_USER:$APP_USER --from=builder . $APP_HOME
COPY --chown=$APP_USER:$APP_USER alembic/ $APP_HOME/alembic
COPY --chown=$APP_USER:$APP_USER entrypoint.sh alembic.ini  $APP_HOME
COPY --chown=$APP_USER:$APP_USER src/ $APP_HOME/src

USER $APP_USER
EXPOSE 8080/TCP

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]