#!/bin/bash
# Rebuild frontend & backend and run with Docker.
# Run from Terminal: ./rebuild-and-run.sh
# Or double-click (if allowed to execute).

set -e
cd "$(dirname "$0")"

echo "Rebuilding backend and frontend..."
docker compose build --no-cache

echo "Starting containers..."
docker compose up -d

echo "Done. Frontend: http://localhost:3000  |  Backend docs: http://localhost:8000/docs"
