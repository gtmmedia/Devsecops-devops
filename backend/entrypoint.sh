#!/bin/sh
# Optionally migrate, then hand over to the real command (uvicorn).
# Kubernetes runs migrations in an initContainer instead (RUN_MIGRATIONS=false).
set -e
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  python -m app.wait_for_db
  alembic upgrade head
fi
exec "$@"
