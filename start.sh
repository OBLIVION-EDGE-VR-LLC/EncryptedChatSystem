#!/bin/bash
# ═══════════════════════════════════════════════
# RiddlerChat Launcher
# Starts the Python backend then launches Electron
# 1337_TECH DBA, Austin Texas - 2026
# ═══════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔═══════════════════════════════════════════╗"
echo "║        RIDDLERCHAT — SYSTEM BOOT          ║"
echo "║  Post-Quantum Encrypted Messenger v2.0    ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ─── Check Python ───
PYTHON=""
if command -v python3 &>/dev/null; then
  PYTHON="python3"
elif command -v python &>/dev/null; then
  PYTHON="python"
else
  echo "[ERROR] Python 3 not found. Install Python 3.10+"
  exit 1
fi

echo "[*] Python: $($PYTHON --version)"

# ─── Check OpenSSL ───
if command -v openssl &>/dev/null; then
  echo "[*] $(openssl version)"
else
  echo "[WARN] OpenSSL not found in PATH"
fi

# ─── Install Python dependencies ───
echo "[*] Checking Python dependencies..."
PIP_FLAGS="--break-system-packages"
$PYTHON -m pip install $PIP_FLAGS -q \
  fastapi uvicorn[standard] websockets pydantic \
  cryptography argon2-cffi python-jose[cryptography] aiofiles 2>/dev/null || \
$PYTHON -m pip install -q \
  fastapi uvicorn[standard] websockets pydantic \
  cryptography argon2-cffi python-jose[cryptography] aiofiles 2>/dev/null || \
echo "[WARN] Some pip installs may have failed — continuing anyway"

echo "[*] Dependencies ready"

# ─── Setup Electron if needed ───
if [ ! -d "electron/node_modules" ]; then
  echo "[*] Installing Electron dependencies..."
  cd electron
  npm install
  cd ..
fi

# ─── Kill any stale processes on port 7576 ───
if lsof -ti:7576 &>/dev/null; then
  echo "[*] Killing stale process on port 7576..."
  lsof -ti:7576 | xargs kill -9 2>/dev/null || true
  sleep 1
fi

# ─── Start Backend ───
echo "[*] Starting RiddlerChat backend on :7576..."
$PYTHON -m uvicorn backend.server:app --host 127.0.0.1 --port 7576 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "[*] Waiting for backend..."
for i in $(seq 1 15); do
  if curl -s http://127.0.0.1:7576/api/status > /dev/null 2>&1; then
    echo "[*] Backend ready"
    break
  fi
  sleep 1
done

# ─── Start Electron ───
# Use --no-sandbox to avoid SUID sandbox permission issues on Linux
echo "[*] Launching RiddlerChat UI..."
cd electron
npx electron . --no-sandbox &
ELECTRON_PID=$!
cd ..

echo ""
echo "[*] RiddlerChat is running"
echo "    Backend PID: $BACKEND_PID"
echo "    Electron PID: $ELECTRON_PID"
echo ""
echo "    Press Ctrl+C to shutdown"

# Cleanup on exit
trap "kill $BACKEND_PID $ELECTRON_PID 2>/dev/null; exit" INT TERM

wait $ELECTRON_PID
kill $BACKEND_PID 2>/dev/null
