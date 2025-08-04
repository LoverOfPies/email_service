#!/usr/bin/env bash
exec /app/.venv/bin/python -m alembic upgrade head &
exec /app/.venv/bin/python -m src.main
