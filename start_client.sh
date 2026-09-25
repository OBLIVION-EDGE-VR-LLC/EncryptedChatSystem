#!/bin/bash
# ═══════════════════════════════════════════
# RiddlerChat Client Launcher
# Connects to a remote RiddlerChat backend
# 1337_TECH DBA, Austin Texas - 2026
# ═══════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔═══════════════════════════════════════════╗"
echo "║      RIDDLERCHAT — CLIENT LAUNCH          ║"
echo "║  Post-Quantum Encrypted Messenger v2.0    ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ─── Server config ───
export RIDDLER_SERVER="${RIDDLER_SERVER:-127.0.0.1}"
export RIDDLER_PORT="${RIDDLER_PORT:-7576}"

echo "[*] Backend target: ${RIDDLER_SERVER}:${RIDDLER_PORT}"

# ─── Check backend reachability ───
echo "[*] Checking backend connectivity..."
if curl -s --connect-timeout 5 "http://${RIDDLER_SERVER}:${RIDDLER_PORT}/api/status" > /dev/null 2>&1; then
  echo "[*] Backend is reachable"
else
  echo "[WARN] Backend at ${RIDDLER_SERVER}:${RIDDLER_PORT} is not responding"
  echo "       Make sure the server container is running:"
  echo "         docker compose up -d"
  echo ""
  echo "       Or set RIDDLER_SERVER to point to your server:"
  echo "         RIDDLER_SERVER=192.168.1.100 ./start_client.sh"
  echo ""
  read -p "       Launch anyway? [y/N] " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# ─── Setup Electron if needed ───
if [ ! -d "electron/node_modules" ]; then
  echo "[*] Installing Electron dependencies..."
  cd electron
  npm install
  cd ..
fi

# ─── Launch Electron ───
echo "[*] Launching RiddlerChat..."
cd electron
npx electron . --no-sandbox
