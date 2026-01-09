#!/bin/sh

echo "Waiting for database migrations..."
alembic upgrade head
if [ $? -ne 0 ]; then
  echo "Alembic migration failed"
  exit 1
fi

echo "Starting Gunicorn..."

exec gunicorn -k uvicorn.workers.UvicornWorker \
     -w 4 \
     -b 0.0.0.0:8000 \
     --access-logfile - \
     --error-logfile - \
     src.main:app \
     --worker-tmp-dir /dev/shm \
     --log-level info \
     --access-logfile - \
     --error-logfile - \
     --capture-output \
     --enable-stdio-inheritance