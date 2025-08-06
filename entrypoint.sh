#!/usr/bin/env bash
echo "Starting migrations..."
/app/.venv/bin/python -m alembic upgrade head
if [ $? -ne 0 ]; then
    echo "Migration failed, exiting..."
    exit 1
fi
echo "Starting service..."
exec /app/.venv/bin/python -m src.main
