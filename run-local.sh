#!/bin/bash
# Run backend and frontend locally (no Docker).
# Usage: ./run-local.sh
# Or run in two terminals: terminal 1 = backend, terminal 2 = frontend.

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

# --- Backend ---
echo ">>> Backend: starting on http://localhost:8000"
cd "$ROOT/backend"
if [ ! -d "venv" ]; then
  echo "Creating venv..."
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# --- Frontend ---
echo ">>> Frontend: installing deps and starting on http://localhost:3000"
cd "$ROOT/frontend"
npm install
npm run dev &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "Backend:  http://localhost:8000  (docs: http://localhost:8000/api/v1/docs)"
echo "Frontend: http://localhost:3000"
echo ""
echo "To stop: kill $BACKEND_PID $FRONTEND_PID"
wait
