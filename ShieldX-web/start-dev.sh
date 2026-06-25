#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

cleanup() {
  echo ""
  echo "🛑 Shutting down services..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null && echo "Backend stopped"
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && echo "Frontend stopped"
  exit 0
}
trap cleanup SIGINT SIGTERM

echo "=============================="
echo "  ShieldX Dev Environment"
echo "=============================="

# --- PostgreSQL ---
echo ""
echo "[1/3] Starting PostgreSQL..."
docker compose -f "$BACKEND_DIR/docker-compose.yml" up -d
echo "  ✅ PostgreSQL is running"

# --- .env ---
if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  echo "  ⚠️  Created .env from .env.example — edit it if needed"
fi

# --- Backend ---
echo ""
echo "[2/3] Starting backend (FastAPI) on port 8000..."
source "$BACKEND_DIR/.venv/bin/activate"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --app-dir "$BACKEND_DIR" &
BACKEND_PID=$!
echo "  ✅ Backend PID: $BACKEND_PID"

sleep 2

# --- Frontend ---
echo ""
echo "[3/3] Starting frontend (React + Vite) on port 5173..."
npm --prefix "$FRONTEND_DIR" run dev &
FRONTEND_PID=$!
echo "  ✅ Frontend PID: $FRONTEND_PID"

echo ""
echo "=============================="
echo "  All services are running!"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Press Ctrl+C to stop all"
echo "=============================="

wait
